import json
import os
import random
import torch
import pandas as pd
from monai.transforms import (AddChanneld, Compose, Lambdad, NormalizeIntensityd,RandCoarseShuffled,RandRotated,RandZoomd,
                              Resized, ToTensord, LoadImaged, EnsureChannelFirstd)
from torch.utils.data import DataLoader, Dataset
from transformers import AutoTokenizer
from utils.text_process import parse_caption, to_labels, build_variant

class QaTa(Dataset):

    def __init__(self, csv_path=None, root_path=None, tokenizer=None, mode='train',image_size=[224,224], return_attrs=False, tanda=False):

        super(QaTa, self).__init__()

        self.mode = mode
        self.tanda = tanda

        with open(csv_path, 'r') as f:
            self.data = pd.read_csv(f)
        self.image_list = list(self.data['Image'])
        self.caption_list = list(self.data['Description'])

        if mode == 'train':
            self.image_list = self.image_list[:int(0.8*len(self.image_list))]
            self.caption_list = self.caption_list[:int(0.8*len(self.caption_list))]
        elif mode == 'valid':
            self.image_list = self.image_list[int(0.8*len(self.image_list)):]
            self.caption_list = self.caption_list[int(0.8*len(self.caption_list)):]
        else:
            pass   # for mode is 'test'

        self.root_path = root_path
        self.image_size = image_size

        self.return_attrs = return_attrs
        if return_attrs:
            # pre-parse attribute labels (nature / quantity / location zones)
            self.attr_list = [to_labels(parse_caption(c)) for c in self.caption_list]

        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer, trust_remote_code=True)

    def __len__(self):

        return len(self.image_list)

    def __getitem__(self, idx):

        trans = self.transform(self.image_size)

        image = os.path.join(self.root_path,'Images',self.image_list[idx].replace('mask_',''))
        gt = os.path.join(self.root_path,'GTs', self.image_list[idx])
        caption = self.caption_list[idx]
        if self.tanda and self.mode == 'train' and random.random() < 0.5:
            # TANDA: 用结构化等价变体做文本增强 (抗错字/句法噪声)
            caption = build_variant(parse_caption(caption), 'keyword')

        token_output = self.tokenizer.encode_plus(caption, padding='max_length',
                                                        max_length=24, 
                                                        truncation=True,
                                                        return_attention_mask=True,
                                                        return_tensors='pt')
        token,mask = token_output['input_ids'],token_output['attention_mask']

        data = {'image':image, 'gt':gt, 'token':token, 'mask':mask}
        data = trans(data)

        image,gt,token,mask = data['image'],data['gt'],data['token'],data['mask']
        gt = torch.where(gt==255,1,0)
        text = {'input_ids':token.squeeze(dim=0), 'attention_mask':mask.squeeze(dim=0)} 

        if self.return_attrs:
            a = self.attr_list[idx]
            text['attrs'] = {
                'nature': torch.tensor(0 if a['nature'] is None else a['nature'], dtype=torch.long),
                'nature_ok': torch.tensor(bool(a['nature_ok']), dtype=torch.bool),
                'quantity': torch.tensor(0 if a['quantity'] is None else a['quantity'], dtype=torch.long),
                'quantity_ok': torch.tensor(bool(a['quantity_ok']), dtype=torch.bool),
                'location': torch.tensor(a['location'], dtype=torch.float),
                'location_ok': torch.tensor(bool(a['location_ok']), dtype=torch.bool),
                'side_L': torch.tensor(bool(sum(a['location'][0:3])), dtype=torch.bool),
                'side_R': torch.tensor(bool(sum(a['location'][3:6])), dtype=torch.bool),
            }

        return ([image, text], gt)

    def transform(self,image_size=[224,224]):

        if self.mode == 'train':  # for training mode
            trans = Compose([
                LoadImaged(["image","gt"], reader='PILReader'),
                EnsureChannelFirstd(["image","gt"]),
                RandZoomd(['image','gt'],min_zoom=0.95,max_zoom=1.2,mode=["bicubic","nearest"],prob=0.1),
                Resized(["image"],spatial_size=image_size,mode='bicubic'),
                Resized(["gt"],spatial_size=image_size,mode='nearest'),
                NormalizeIntensityd(['image'], channel_wise=True),
                ToTensord(["image","gt","token","mask"]),
            ])
        
        else:  # for valid and test mode: remove random zoom
            trans = Compose([
                LoadImaged(["image","gt"], reader='PILReader'),
                EnsureChannelFirstd(["image","gt"]),
                Resized(["image"],spatial_size=image_size,mode='bicubic'),
                Resized(["gt"],spatial_size=image_size,mode='nearest'),
                NormalizeIntensityd(['image'], channel_wise=True),
                ToTensord(["image","gt","token","mask"]),

            ])

        return trans


