from utils.model import LanGuideMedSeg
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
        
        self.model = LanGuideMedSeg(args.bert_type, args.vision_type, args.project_dim,
                                    use_aux=self.use_aux)
        self.lr = args.lr
        self.history = {}
        
        self.loss_fn = DiceCELoss()
        if self.use_aux:
            self.aux_ce = nn.CrossEntropyLoss(ignore_index=-100)

        metrics_dict = {"acc":Accuracy(task='binary'),"dice":Dice(),"MIoU":BinaryJaccardIndex()}
        self.train_metrics = nn.ModuleDict(metrics_dict)
        self.val_metrics = deepcopy(self.train_metrics)
        self.test_metrics = deepcopy(self.train_metrics)
        
        self.save_hyperparameters()

    def configure_optimizers(self):

        optimizer = torch.optim.AdamW(self.model.parameters(),lr = self.lr) # 修改这里的参数
        lr_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max =200, eta_min=1e-6)

        return {"optimizer":optimizer,"lr_scheduler":lr_scheduler}
        
    def forward(self,x):
       
       return self.model.forward(x)


    def shared_step(self,batch,batch_idx):
        x, y = batch
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
        return {'loss': loss, 'preds': preds.detach(), 'y': y.detach()}

    def _aux_loss(self, logits, attrs):
        """Combined auxiliary attribute loss (masked BCE / CE with ignore)."""
        device = logits['nature'].device
        losses = []

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
        
    def training_step_end(self, outputs):
        return {'loss':self.shared_step_end(outputs,"train")}
            
    def validation_step_end(self, outputs):
        return {'val_loss':self.shared_step_end(outputs,"val")}
            
    def test_step_end(self, outputs):
        return {'test_loss':self.shared_step_end(outputs,"test")}
            
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