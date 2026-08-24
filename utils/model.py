import torch
import torch.nn as nn
import torch.nn.functional as F
from einops import rearrange, repeat
from .layers import GuideDecoder
from monai.networks.blocks.dynunet_block import UnetOutBlock
from monai.networks.blocks.upsample import SubpixelUpsample
from transformers import AutoTokenizer, AutoModel
from .aux_head import AuxHeads



class BERTModel(nn.Module):

    def __init__(self, bert_type, project_dim, unfreeze_layers=0):

        super(BERTModel, self).__init__()

        self.model = AutoModel.from_pretrained(bert_type,output_hidden_states=True,trust_remote_code=True)
        self.project_head = nn.Sequential(             
            nn.Linear(768, project_dim),
            nn.LayerNorm(project_dim),             
            nn.GELU(),             
            nn.Linear(project_dim, project_dim)
        )
        # freeze the parameters (except optionally the last encoder layers)
        for param in self.model.parameters():
            param.requires_grad = False
        self.unfrozen = []
        if unfreeze_layers > 0:
            bert = self.model.bert if hasattr(self.model, 'bert') else self.model
            for layer in bert.encoder.layer[-unfreeze_layers:]:
                for p in layer.parameters():
                    p.requires_grad = True
                    self.unfrozen.append(p)

    def forward(self, input_ids, attention_mask):

        output = self.model(input_ids=input_ids, attention_mask=attention_mask,output_hidden_states=True,return_dict=True)
        # get 1+2+last layer
        last_hidden_states = torch.stack([output['hidden_states'][1], output['hidden_states'][2], output['hidden_states'][-1]]) # n_layer, batch, seqlen, emb_dim
        embed = last_hidden_states.permute(1,0,2,3).mean(2).mean(1) # pooling
        embed = self.project_head(embed)

        return {'feature':output['hidden_states'],'project':embed}

class VisionModel(nn.Module):

    def __init__(self, vision_type, project_dim):
        super(VisionModel, self).__init__()

        self.model = AutoModel.from_pretrained(vision_type,output_hidden_states=True)   
        self.project_head = nn.Linear(768, project_dim)
        self.spatial_dim = 768

    def forward(self, x):

        output = self.model(x, output_hidden_states=True)
        embeds = output['pooler_output'].squeeze()
        project = self.project_head(embeds)

        return {"feature":output['hidden_states'], "project":project}


class LanGuideMedSeg(nn.Module):

    def __init__(self, bert_type, vision_type, project_dim=512, use_aux=False,
                 text_unfreeze_layers=0, multi_text=False, film=False):

        super(LanGuideMedSeg, self).__init__()

        self.use_aux = use_aux
        self.multi_text = multi_text
        self.film = film

        self.encoder = VisionModel(vision_type, project_dim)
        self.text_encoder = BERTModel(bert_type, project_dim,
                                      unfreeze_layers=text_unfreeze_layers)

        self.spatial_dim = [7,14,28,56]    # 224*224
        feature_dim = [768,384,192,96]

        self.decoder16 = GuideDecoder(feature_dim[0],feature_dim[1],self.spatial_dim[0],24)
        self.decoder8 = GuideDecoder(feature_dim[1],feature_dim[2],self.spatial_dim[1],12)
        self.decoder4 = GuideDecoder(feature_dim[2],feature_dim[3],self.spatial_dim[2],9)
        self.decoder1 = SubpixelUpsample(2,feature_dim[3],24,4)
        self.out = UnetOutBlock(2, in_channels=24, out_channels=1)

        if self.film:
            # FiLM: text-conditional per-channel scale/shift on each decoder stage
            self.film_mlp = nn.ModuleList([
                nn.Linear(project_dim, 2 * d)
                for d in (feature_dim[1], feature_dim[2], feature_dim[3])])

        if use_aux:
            # aux heads take the pooled decoder feature (feature_dim[-1] = 96)
            self.aux_head = AuxHeads(in_dim=feature_dim[3], hidden=128)

    def _film(self, x, proj, idx):
        """Text-conditional FiLM modulation: x*gamma + beta on channel dim."""
        gb = self.film_mlp[idx](proj)                 # (B, 2*dim)
        gamma, beta = gb.chunk(2, dim=-1)
        return x * gamma.unsqueeze(1) + beta.unsqueeze(1)

    def forward(self, data):

        image, text = data
        if image.shape[1] == 1:   
            image = repeat(image,'b 1 h w -> b c h w',c=3)

        image_output = self.encoder(image)
        image_features, image_project = image_output['feature'], image_output['project']
        text_output = self.text_encoder(text['input_ids'],text['attention_mask'])
        text_embeds, text_project = text_output['feature'],text_output['project']

        if len(image_features[0].shape) == 4: 
            image_features = image_features[1:]  # 4 8 16 32   convnext: Embedding + 4 layers feature map
            image_features = [rearrange(item,'b c h w -> b (h w) c') for item in image_features] 

        os32 = image_features[3]
        if self.multi_text:
            # fuse multiple text hidden layers (layers 1,2,last) instead of only last
            text_guide = sum(text_embeds[i] for i in (1, 2, -1)) / 3.0
        else:
            text_guide = text_embeds[-1]
        os16 = self.decoder16(os32,image_features[2], text_guide)
        if self.film:
            os16 = self._film(os16, text_project, 0)
        os8 = self.decoder8(os16,image_features[1], text_guide)
        if self.film:
            os8 = self._film(os8, text_project, 1)
        os4 = self.decoder4(os8,image_features[0], text_guide)
        if self.film:
            os4 = self._film(os4, text_project, 2)
        os4 = rearrange(os4, 'B (H W) C -> B C H W',H=self.spatial_dim[-1],W=self.spatial_dim[-1])

        aux_logits = None
        if self.use_aux:
            pooled = F.adaptive_avg_pool2d(os4, 1).flatten(1)  # B, 96
            aux_logits = self.aux_head(pooled)

        os1 = self.decoder1(os4)

        out = self.out(os1).sigmoid()

        # stash pooled image/text projections for optional CLIP-style alignment
        self.last_img_proj = image_project
        self.last_txt_proj = text_project

        if self.use_aux:
            return out, aux_logits
        return out
    
