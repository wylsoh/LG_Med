from utils.model import LanGuideMedSeg
from utils.count_loss import soft_euler_count, count_components
from monai.losses import DiceCELoss
from torchmetrics import Accuracy,Dice
from torchmetrics.classification import BinaryJaccardIndex
import torch
import torch.nn as nn
import pytorch_lightning as pl
from copy import deepcopy
import pandas as pd
import sys
import numpy as np
import datetime

class LanGuideMedSegWrapper(pl.LightningModule):

    def __init__(self, args):
        
        super(LanGuideMedSegWrapper, self).__init__()

        self.use_aux = getattr(args, 'use_aux', False)
        self.aux_weight = getattr(args, 'aux_weight', 1.0)
        self.count_loss_weight = getattr(args, 'count_loss_weight', 0.0)
        self.clip_weight = getattr(args, 'clip_weight', 0.0)
        self.clip_clean = getattr(args, 'clip_clean', False)
        self.side_gate = getattr(args, 'side_gate', False)
        if self.clip_clean:
            # 对齐前先对分割图做形态学去碎片, 再用投影头提取对齐特征
            self.seg_align = nn.Sequential(
                nn.Conv2d(1, 32, 3, padding=1), nn.GELU(),
                nn.AdaptiveAvgPool2d(1), nn.Flatten(),
                nn.Linear(32, args.project_dim))
        self.count_weighted = getattr(args, 'count_weighted', False)
        self.count_min_q = getattr(args, 'count_min_q', 1)
        if self.count_weighted:
            # 逆频率权重(固定自训练集数量分布): one/two/three/four
            freq = torch.tensor([1442., 5268., 365., 59.])
            self.register_buffer('_count_w', (freq.sum() / (4 * freq)).float())
        
        self.model = LanGuideMedSeg(
            args.bert_type, args.vision_type, args.project_dim,
            use_aux=self.use_aux,
            text_unfreeze_layers=getattr(args, 'text_unfreeze_layers', 0),
            multi_text=getattr(args, 'multi_text', False),
            film=getattr(args, 'film', False))
        self._unfrozen_ids = {id(p) for p in self.model.text_encoder.unfrozen}
        self.lr = args.lr
        self.history = {}
        
        self.loss_fn = DiceCELoss()
        self.aux_quantity_only = getattr(args, 'aux_quantity_only', False)
        self.aux_nature_only = getattr(args, 'aux_nature_only', False)
        if self.use_aux:
            if self.aux_quantity_only:
                # 只监督 quantity 分类头, CE 用逆频率类权重(one/two/three/four)
                freq = torch.tensor([1442., 5268., 365., 59.])
                self.aux_ce = nn.CrossEntropyLoss(
                    weight=(freq.sum() / (4 * freq)).float(), ignore_index=-100)
            else:
                self.aux_ce = nn.CrossEntropyLoss(ignore_index=-100)

        metrics_dict = {"acc":Accuracy(task='binary'),"dice":Dice(),"MIoU":BinaryJaccardIndex()}
        self.train_metrics = nn.ModuleDict(metrics_dict)
        self.val_metrics = deepcopy(self.train_metrics)
        self.test_metrics = deepcopy(self.train_metrics)
        
        self.save_hyperparameters()

    def configure_optimizers(self):

        if self._unfrozen_ids:
            # unfrozen BERT layers get a 10x smaller learning rate
            base, small = [], []
            for name, p in self.model.named_parameters():
                if not p.requires_grad:
                    continue
                (small if id(p) in self._unfrozen_ids else base).append(p)
            optimizer = torch.optim.AdamW(
                [{'params': base, 'lr': self.lr},
                 {'params': small, 'lr': self.lr / 10.0}],
                lr=self.lr)
        else:
            optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.lr)
        lr_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=200, eta_min=1e-6)

        return {"optimizer": optimizer, "lr_scheduler": lr_scheduler}
        
    def forward(self,x):
       
       return self.model.forward(x)


    def shared_step(self,batch,batch_idx):
        x, y = batch
        if self.side_gate and self.training:
            # 训练时: 未声明侧(文本 nature/location)强制背景, 实现侧别门控
            y = self._gate_side(y, x[1]['attrs'])
        out = self(x)
        if self.use_aux:
            preds, aux_logits = out
            loss = self.loss_fn(preds, y)
            aux_loss = self._aux_loss(aux_logits, x[1]['attrs'])
            self.log('aux_loss', aux_loss, prog_bar=True, batch_size=y.size(0))
            loss = loss + self.aux_weight * aux_loss
        else:
            preds = out
            loss = self.loss_fn(preds, y)

        # ---- connected-component count supervision (quantity keyword) ----
        ret = {'loss': loss, 'preds': preds.detach(), 'y': y.detach()}
        # ---- CLIP-style image-text alignment (training only) ----
        if self.clip_weight > 0 and self.training:
            if hasattr(self.model, 'last_img_proj'):
                if self.clip_clean:
                    clip_loss = self._clip_clean_loss(preds, self.model.last_txt_proj)
                else:
                    clip_loss = self._clip_loss(self.model.last_img_proj,
                                                self.model.last_txt_proj)
                self.log('clip_loss', clip_loss, prog_bar=True, batch_size=y.size(0))
                ret['loss'] = ret['loss'] + self.clip_weight * clip_loss
        if self.count_loss_weight > 0:
            count_loss = self._count_loss(preds, x[1]['attrs'])
            self.log('count_loss', count_loss, prog_bar=True, batch_size=y.size(0))
            ret['loss'] = loss + self.count_loss_weight * count_loss
            if not self.training:
                self._collect_count_stats(preds, x[1]['attrs'], ret)
        return ret

    def _gate_side(self, y, attrs):
        """Zero-out the non-declared lung side(s) in the GT mask (side gating).

        The text (nature + location) declares which side(s) have infection;
        the other side is forced to background so the model learns to segment
        ONLY the declared side(s). Applied at training time only; evaluation
        uses the full GT.
        """
        y = y.clone()
        side_L = attrs['side_L'].to(y.device)
        side_R = attrs['side_R'].to(y.device)
        W2 = y.shape[-1] // 2
        for b in range(y.shape[0]):
            if not side_L[b].item():
                y[b, :, :, :W2] = 0
            if not side_R[b].item():
                y[b, :, :, W2:] = 0
        return y

    def _clip_loss(self, img, txt, temperature=0.07):
        """Symmetric InfoNCE (CLIP-style) aligning image & text projections.

        img/txt: (B, project_dim) pooled global features. Pulls the image
        representation of each sample close to its own caption embedding and
        away from other captions in the batch. Needs B >= 2 (returns 0 else).
        """
        if img.shape[0] < 2:
            return torch.zeros((), device=img.device)
        img = nn.functional.normalize(img, dim=-1)
        txt = nn.functional.normalize(txt, dim=-1)
        logits = img @ txt.t() / temperature          # (B, B)
        labels = torch.arange(logits.shape[0], device=logits.device)
        return 0.5 * (nn.functional.cross_entropy(logits, labels)
                      + nn.functional.cross_entropy(logits.t(), labels))

    def _clip_clean_loss(self, preds, txt, temperature=0.07, kernel=5):
        """CLIP alignment on speckle-removed segmentation (clip_clean).

        Applies a differentiable morphological opening (erode = min-pool then
        dilate = max-pool) to the soft segmentation to drop small fragments
        BEFORE pooling + projecting for the global alignment - mirrors the
        min_area filtering used in evaluation, so the model cannot align to
        (or be rewarded for) tiny speckle regions.
        """
        x = preds                                   # (B,1,H,W) sigmoid
        x_erode = -nn.functional.max_pool2d(-x, kernel_size=kernel,
                                            stride=1, padding=kernel // 2)
        x_open = nn.functional.max_pool2d(x_erode, kernel_size=kernel,
                                          stride=1, padding=kernel // 2)
        img = self.seg_align(x_open)                # (B, project_dim)
        return self._clip_loss(img, txt, temperature)

    def _count_loss(self, preds, attrs):
        """Bounded differentiable count loss: Euler proxy vs quantity.

        `soft_euler_count` can be large for soft probability maps (e.g. an
        almost-uniform map has a large Euler number). The loss is therefore
        bounded via z/(z+1): it stays ~1 (inert, weak gradient) while the map
        is far from binary, and becomes active once the segmentation is
        near-binary and the count mismatch is small.

        If `count_weighted=True`:
          - only samples with quantity >= count_min_q are supervised
            (one-area samples are handled by DiceCE; avoids majority-class
            cheating by always emitting 2 components);
          - each sample's loss is scaled by the inverse class frequency so
            the minority classes (three/four) are not dominated by `two`.
        """
        device = preds.device
        counts = soft_euler_count(preds)  # (B,) differentiable proxy
        target = attrs['quantity'].to(device).float() + 1.0  # 1..4
        m = attrs['quantity_ok'].to(device)
        if not m.any():
            return torch.zeros((), device=device)
        diff = torch.abs(counts - target)
        loss = diff / (diff + 1.0)  # bounded in [0, 1)
        if self.count_weighted:
            q = attrs['quantity'].to(device).long()
            m = m & (q >= self.count_min_q)
            if not m.any():
                return torch.zeros((), device=device)
            wgt = self._count_w[q.clamp(0, 3)] * m
            return (loss * wgt).sum() / wgt.sum()
        return (loss * m).sum() / m.sum()

    def _collect_count_stats(self, preds, attrs, ret):
        """Exact connected-component count metrics (no grad, on GPU)."""
        with torch.no_grad():
            mask = preds.detach() > 0.5             # (B,1,H,W) bool
            counts = count_components(mask[:, 0])   # (B,) exact
        q = attrs['quantity'].detach() + 1          # 1..4
        ok = attrs['quantity_ok'].detach()
        correct = total = 0
        mae = 0.0
        for b in range(preds.shape[0]):
            if ok[b].item():
                c = int(counts[b].item())
                t = int(q[b].item())
                total += 1
                correct += int(c == t)
                mae += abs(c - t)
        ret['count_correct'] = correct
        ret['count_total'] = total
        ret['count_mae'] = mae

    def _aux_loss(self, logits, attrs):
        """Combined auxiliary attribute loss (masked BCE / CE with ignore)."""
        device = logits['nature'].device
        losses = []

        # quantity-only mode: single weighted 4-class CE on the quantity head
        if self.aux_quantity_only:
            m = attrs['quantity_ok'].to(device)
            if not m.any():
                return torch.zeros((), device=device)
            t = attrs['quantity'].to(device).long()
            t = torch.where(m, t, torch.full_like(t, -100))
            return self.aux_ce(logits['quantity'], t)

        # nature-only mode: single weighted 2-class CE on the nature head
        # (inverse-frequency: unilateral=1482, bilateral=5663 in train)
        if self.aux_nature_only:
            m = attrs['nature_ok'].to(device)
            if not m.any():
                return torch.zeros((), device=device)
            freq = torch.tensor([1482., 5663.])   # 0=unilateral, 1=bilateral
            w = (freq.sum() / (2 * freq)).to(device)
            t = attrs['nature'].to(device).long()
            loss = nn.functional.cross_entropy(
                logits['nature'], t, weight=w, reduction='none')
            return (loss * m).sum() / m.sum()

        # nature: 2-class, per-sample masked BCE
        m = attrs['nature_ok'].to(device)
        if m.any():
            t = torch.nn.functional.one_hot(
                attrs['nature'].to(device), num_classes=2).float()
            l = torch.nn.functional.binary_cross_entropy_with_logits(
                logits['nature'], t, reduction='none').mean(-1)
            losses.append((l * m).sum() / m.sum())

        # quantity: 4-class CE with ignore_index
        m = attrs['quantity_ok'].to(device)
        if m.any():
            t = attrs['quantity'].to(device).long()
            t = torch.where(m, t, torch.full_like(t, -100))
            losses.append(self.aux_ce(logits['quantity'], t))

        # location: 6-dim multi-hot, per-sample masked BCE
        m = attrs['location_ok'].to(device)
        if m.any():
            l = torch.nn.functional.binary_cross_entropy_with_logits(
                logits['location'], attrs['location'].to(device),
                reduction='none').mean(-1)
            losses.append((l * m).sum() / m.sum())

        if not losses:
            return torch.zeros((), device=device)
        return torch.stack(losses).mean()
    
    def training_step(self, batch, batch_idx):
        return self.shared_step(batch,batch_idx)
    
    def validation_step(self, batch, batch_idx):
        return self.shared_step(batch,batch_idx)
    
    def test_step(self, batch, batch_idx):
        return self.shared_step(batch,batch_idx)
    
    def predict_step(self, batch, batch_idx):
        if isinstance(batch,list) and len(batch)==2:
            return self(batch[0])
        else:
            return self(batch)
        
    def shared_step_end(self,outputs,stage):
        metrics = self.train_metrics if stage=="train" else (
            self.val_metrics if stage=="val" else self.test_metrics)
        for name in metrics:
            step_metric = metrics[name](outputs['preds'], outputs['y']).item()
            if stage=="train":
                self.log(name,step_metric,prog_bar=True)
        return outputs["loss"].mean()
        
    def _pass_count_stats(self, outputs, ret):
        if self.count_loss_weight > 0:
            for k in ('count_correct', 'count_total', 'count_mae'):
                if k in outputs:
                    ret[k] = outputs[k]

    def training_step_end(self, outputs):
        ret = {'loss': self.shared_step_end(outputs, "train")}
        self._pass_count_stats(outputs, ret)
        return ret

    def validation_step_end(self, outputs):
        ret = {'val_loss': self.shared_step_end(outputs, "val")}
        self._pass_count_stats(outputs, ret)
        return ret

    def test_step_end(self, outputs):
        ret = {'test_loss': self.shared_step_end(outputs, "test")}
        self._pass_count_stats(outputs, ret)
        return ret
            
    def shared_epoch_end(self,outputs,stage="train"):
        metrics = self.train_metrics if stage=="train" else (
            self.val_metrics if stage=="val" else self.test_metrics)
        
        epoch = self.trainer.current_epoch
        stage_loss = torch.mean(torch.tensor([t[(stage+"_loss").replace('train_','')] for t in outputs])).item()
        dic = {"epoch":epoch,stage+"_loss":stage_loss}
        
        for name in metrics:
            epoch_metric = metrics[name].compute().item() 
            metrics[name].reset()
            dic[stage+"_"+name] = epoch_metric 

        # aggregate exact connected-component count metrics (count_loss exp.)
        if self.count_loss_weight > 0:
            c_c = sum(t.get('count_correct', 0) for t in outputs)
            c_t = sum(t.get('count_total', 0) for t in outputs)
            c_m = sum(t.get('count_mae', 0.0) for t in outputs)
            if c_t > 0:
                dic[stage + '_count_acc'] = c_c / c_t
                dic[stage + '_count_mae'] = c_m / c_t

        if stage!='test':
            self.history[epoch] = dict(self.history.get(epoch,{}),**dic)    
        return dic 
    
    def training_epoch_end(self, outputs):
        dic = self.shared_epoch_end(outputs,stage="train")
        self.print(dic)
        dic.pop("epoch",None)
        self.log_dict(dic, logger=True)

    def validation_epoch_end(self, outputs):
        dic = self.shared_epoch_end(outputs,stage="val")
        self.print_bar()
        self.print(dic)
        dic.pop("epoch",None)
        self.log_dict(dic, logger=True)
        
        #log when reach best score
        ckpt_cb = self.trainer.checkpoint_callback
        monitor = ckpt_cb.monitor 
        mode = ckpt_cb.mode 
        arr_scores = self.get_history()[monitor]
        best_score_idx = np.argmax(arr_scores) if mode=="max" else np.argmin(arr_scores)
        if best_score_idx==len(arr_scores)-1:   
            self.print("<<<<<< reach best {0} : {1} >>>>>>".format(
                monitor,arr_scores[best_score_idx]),file = sys.stderr)
    
    def test_epoch_end(self, outputs):
        dic = self.shared_epoch_end(outputs,stage="test")
        dic.pop("epoch",None)
        self.print(dic)
        self.log_dict(dic, logger=True)
        
    def get_history(self):
        return pd.DataFrame(self.history.values()) 
    
    def print_bar(self): 
        nowtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.print("\n"+"="*80 + "%s"%nowtime)