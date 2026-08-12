import argparse
import os
from engine.wrapper import LanGuideMedSegWrapper

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

import pytorch_lightning as pl  

from utils.dataset import QaTa
import utils.config as config


def get_parser():
    parser = argparse.ArgumentParser(
        description='Language-guide Medical Image Segmentation')
    parser.add_argument('--config',
                        default='./config/training.yaml',
                        type=str,
                        help='config file')

    args = parser.parse_args()
    assert args.config is not None
    cfg = config.load_cfg_from_cfg_file(args.config)

    return cfg

if __name__ == '__main__':

    args = get_parser()

    # load model
    model = LanGuideMedSegWrapper(args)

    ckpt_path = os.path.join(args.model_save_path,
                             args.model_save_filename + '.ckpt')
    checkpoint = torch.load(ckpt_path, map_location='cpu')["state_dict"]
    model.load_state_dict(checkpoint, strict=True)

    # dataloader
    return_attrs = getattr(args, 'use_aux', False)
    ds_test = QaTa(csv_path=args.test_csv_path,
                    root_path=args.test_root_path,
                    tokenizer=args.bert_type,
                    image_size=args.image_size,
                    mode='test',
                    return_attrs=return_attrs)

    # ---- experiment: reduced text variants (no-op unless text_mode != 'full') ----
    text_mode = getattr(args, 'text_mode', 'full')
    if text_mode != 'full':
        from utils.text_process import process_caption
        ds_test.caption_list = [process_caption(c, text_mode) for c in ds_test.caption_list]
        print(f'[EXP] text_mode={text_mode}: test={len(ds_test.caption_list)}')

    dl_test = DataLoader(ds_test, batch_size=args.valid_batch_size, shuffle=False, num_workers=8)

    trainer = pl.Trainer(accelerator='gpu',devices=1) 
    model.eval()
    trainer.test(model, dl_test) 
