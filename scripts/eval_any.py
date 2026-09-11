"""Evaluate one experiment config on the test set -> Acc / Dice / Jaccard.

Usage:
    python scripts/eval_any.py config/exp/<name>.yaml

The checkpoint is read from the config itself (model_save_path /
model_save_filename). A GPU with >=3GB free memory is picked automatically.
Outputs the original paper's three metrics: Acc / Dice / Jaccard (test_acc /
test_dice / test_MIoU).
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)


def pick_gpu(min_free_mb=3000):
    out = subprocess.check_output(
        ['nvidia-smi', '--query-gpu=index,memory.free',
         '--format=csv,noheader,nounits'])
    for line in out.decode().strip().splitlines():
        idx, free = line.split(',')
        if int(free) >= min_free_mb:
            return int(idx)
    return None


def main():
    cfg_file = sys.argv[1]

    from engine.wrapper import LanGuideMedSegWrapper
    import torch
    from torch.utils.data import DataLoader
    import pytorch_lightning as pl
    from utils.dataset import QaTa
    import utils.config as config

    gpu = pick_gpu()
    if gpu is None:
        print('[eval_any] no GPU with >=3G free, abort', flush=True)
        sys.exit(1)
    os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu)

    cfg = config.load_cfg_from_cfg_file(cfg_file)
    cfg.valid_batch_size = 1
    model = LanGuideMedSegWrapper(cfg)

    ckpt_path = os.path.join(cfg.model_save_path, cfg.model_save_filename + '.ckpt')
    checkpoint = torch.load(ckpt_path, map_location='cpu')['state_dict']
    model.load_state_dict(checkpoint, strict=True)

    return_attrs = (getattr(cfg, 'use_aux', False)
                    or getattr(cfg, 'count_loss_weight', 0) > 0)
    ds_test = QaTa(csv_path=cfg.test_csv_path, root_path=cfg.test_root_path,
                   tokenizer=cfg.bert_type, image_size=cfg.image_size, mode='test',
                   return_attrs=return_attrs)

    text_mode = getattr(cfg, 'text_mode', 'full')
    if text_mode != 'full':
        from utils.text_process import process_caption
        ds_test.caption_list = [process_caption(c, text_mode)
                                for c in ds_test.caption_list]

    print(f'[eval_any] {cfg_file} text_mode={text_mode} '
          f'samples={len(ds_test.caption_list)} gpu={gpu}', flush=True)

    dl_test = DataLoader(ds_test, batch_size=1, shuffle=False, num_workers=8)
    trainer = pl.Trainer(accelerator='gpu', devices=1, logger=False)
    model.eval()
    trainer.test(model, dl_test)


if __name__ == '__main__':
    main()
