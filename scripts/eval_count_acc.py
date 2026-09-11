"""Evaluate region-count accuracy (connected components, area-filtered).

Usage:
    python scripts/eval_count_acc.py config/exp/<name>.yaml [min_area]

Counts 8-connected components of the thresholded prediction (out > 0.5) and of
the ground truth, filters components smaller than `min_area` (default 200 px),
then reports the fraction of test images whose predicted region count matches
the GT region count (overall + per true-count breakdown).

Checkpoint is read from the config (model_save_path / model_save_filename).
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import numpy as np
import torch
from PIL import Image

from utils.count_loss import _neighbors_min


def ccm_min_area(mask, min_area, connectivity=8, max_iter=512):
    """Exact connected components (label propagation) with area filtering."""
    B, H, W = mask.shape
    sentinel = float(H * W)
    ids = torch.arange(H * W, device=mask.device).view(1, H, W).expand(B, H, W).clone()
    sentinel_t = torch.full_like(ids, sentinel)
    ids = torch.where(mask, ids, sentinel_t)
    for _ in range(max_iter):
        prev = ids
        ids = torch.minimum(ids, _neighbors_min(ids, sentinel, connectivity))
        ids = torch.where(mask, ids, sentinel_t)
        if torch.equal(ids, prev):
            break
    counts = torch.zeros(B, device=mask.device)
    for b in range(B):
        fg = mask[b]
        if not fg.any():
            counts[b] = 0
            continue
        comp = ids[b][fg]
        area = torch.unique(comp, return_counts=True)[1]
        counts[b] = (area >= min_area).sum().item()
    return counts


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
    MIN = int(sys.argv[2]) if len(sys.argv) > 2 else 200

    import utils.config as config
    from utils.dataset import QaTa
    from torch.utils.data import DataLoader
    from engine.wrapper import LanGuideMedSegWrapper

    gpu = pick_gpu()
    if gpu is None:
        print('[eval_count_acc] no GPU with >=3G free, abort', flush=True)
        sys.exit(1)
    os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu)

    cfg = config.load_cfg_from_cfg_file(cfg_file)
    cfg.valid_batch_size = 8
    model = LanGuideMedSegWrapper(cfg)

    ckpt_path = os.path.join(cfg.model_save_path, cfg.model_save_filename + '.ckpt')
    model.load_state_dict(torch.load(ckpt_path, map_location='cpu')['state_dict'],
                          strict=True)
    model.cuda().eval()

    ds = QaTa(csv_path=cfg.test_csv_path, root_path=cfg.test_root_path,
              tokenizer=cfg.bert_type, image_size=cfg.image_size, mode='test',
              return_attrs=False)
    text_mode = getattr(cfg, 'text_mode', 'full')
    if text_mode != 'full':
        from utils.text_process import process_caption
        ds.caption_list = [process_caption(c, text_mode) for c in ds.caption_list]

    dl = DataLoader(ds, batch_size=8, shuffle=False, num_workers=4)

    pred = []
    with torch.no_grad():
        for b in dl:
            x, _ = b
            img, text = x
            tc = {'input_ids': text['input_ids'].cuda(),
                  'attention_mask': text['attention_mask'].cuda()}
            out = model([img.cuda(), tc])
            out = out[0] if isinstance(out, (tuple, list)) else out
            # NOTE: model output is ALREADY sigmoid probability -> single threshold
            pred.append((out > 0.5).bool().cpu()[:, 0])
    pred = torch.cat(pred)

    gts = []
    for im in ds.image_list:
        gts.append(np.array(Image.open(os.path.join('data/QaTa-COV19-v2/Test/GTs', im))
                            .convert('L')) > 0)
    gt = torch.from_numpy(np.stack(gts))

    pc, gc = [], []
    with torch.no_grad():
        for i in range(0, len(pred), 128):
            pc.append(ccm_min_area(pred[i:i + 128].to('cuda'), MIN).cpu())
            gc.append(ccm_min_area(gt[i:i + 128].to('cuda'), MIN).cpu())
    pc = torch.cat(pc).numpy()
    gc = torch.cat(gc).numpy()

    print(f'model={os.path.basename(ckpt_path)} min_area={MIN} '
          f'overall_count_acc={100 * (pc == gc).mean():.1f}%')
    for k in sorted(set(gc)):
        m = gc == k
        print(f'  true={k}: n={int(m.sum())} acc={100 * (pc[m] == gc[m]).mean():.1f}%')


if __name__ == '__main__':
    main()
