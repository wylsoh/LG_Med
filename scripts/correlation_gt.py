"""Part B: correlation of text features with GROUND-TRUTH connected-component count.

For every sample, compute the exact number of connected components in the real
GT mask (8-connectivity, pure torch), then analyse:
  - gt_count distribution
  - quantity(text word) vs gt_count consistency + confusion matrix
  - num_regions(location) vs gt_count consistency
  - Spearman correlation between text numeric features and gt_count
Saves gt counts to logs/gt_count_{train,test}.csv and report to logs/corr_gt.md.
"""
import os, sys, subprocess, time, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import torch
from PIL import Image
from utils.count_loss import count_components

L = []


def log(s=""):
    print(s)
    L.append(s)


def pick_gpu():
    try:
        out = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=index,memory.free', '--format=csv,noheader,nounits'])
        for line in out.decode().strip().splitlines():
            idx, free = line.split(',')
            if int(free) >= 2000:
                return int(idx)
    except Exception:
        pass
    return None


def load_gt_masks(images, root):
    """Load GT masks as a single (N,H,W) uint8 tensor (0/255)."""
    arrs = []
    for img in images:
        a = np.array(Image.open(os.path.join(root, 'GTs', img)).convert('L'))
        arrs.append(a)
    return torch.from_numpy(np.stack(arrs)).byte()


def main():
    gpu = pick_gpu()
    if gpu is not None:
        os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu)
        dev = torch.device('cuda')
        log(f"[gt] using GPU {gpu}")
    else:
        dev = torch.device('cpu')
        log("[gt] no free GPU -> CPU (slower)")

    for split in ['train', 'test']:
        df = pd.read_csv(f'logs/caption_features_{split}.csv')
        root = f'data/QaTa-COV19-v2/{"Train" if split=="train" else "Test"}'
        images = df['Image'].tolist()

        # reuse precomputed gt counts if available (avoids re-counting)
        gt_csv = f'logs/gt_count_{split}.csv'
        if os.path.exists(gt_csv):
            prev = pd.read_csv(gt_csv)
            if len(prev) == len(df) and 'gt_count' in prev.columns:
                df['gt_count'] = prev['gt_count'].values
                log(f"[gt] {split}: reuse precomputed gt_count from {gt_csv}")
                gt_count = df['gt_count'].values
        if 'gt_count' not in df.columns:
            t0 = time.time()
            masks = load_gt_masks(images, root)              # (N,H,W) 0/255
            log(f"[gt] {split}: loaded {len(images)} masks in {time.time()-t0:.0f}s")
            # batch compute component counts
            counts = []
            bs = 64
            with torch.no_grad():
                for i in range(0, len(masks), bs):
                    chunk = (masks[i:i+bs] > 0).to(dev)
                    counts.append(count_components(chunk, connectivity=8))
            gt_count = torch.cat(counts).cpu().numpy()
            log(f"[gt] {split}: counted in {time.time()-t0:.0f}s total")
            df['gt_count'] = gt_count
            df.to_csv(gt_csv, index=False)

        # ---- analysis ----
        log(f"\n{'#'*68}\n# PART B — GT 连通域 vs 文本特征 ({split.upper()}, n={len(df)})\n{'#'*68}")

        block = lambda t: (log(f"\n## {t}"), log("-"*64))
        block("1. 真实连通域数 (gt_count) 分布")
        vc = df['gt_count'].value_counts().sort_index()
        for k, v in vc.items():
            log(f"  {k} 个连通域: {v} ({100*v/len(df):.1f}%)")

        # consistency with quantity
        block("2. quantity(文本数量词) vs gt_count 一致性")
        m = df['quantity_ok']
        sub = df[m]
        acc = (sub['quantity'] == sub['gt_count']).mean()
        log(f"可比样本 {len(sub)}, 完全一致率 = {100*acc:.1f}%")
        log("混淆矩阵 (行=quantity, 列=gt_count):")
        log(pd.crosstab(sub['quantity'], sub['gt_count']).to_string())

        # consistency with num_regions
        block("3. num_regions(位置区域数) vs gt_count 一致性")
        m2 = df['location_ok']
        sub2 = df[m2]
        acc2 = (sub2['num_regions'] == sub2['gt_count']).mean()
        log(f"可比样本 {len(sub2)}, 完全一致率 = {100*acc2:.1f}%")
        log("混淆矩阵 (行=num_regions, 列=gt_count):")
        log(pd.crosstab(sub2['num_regions'], sub2['gt_count']).to_string())

        # spearman correlations (pure pandas: rank then pearson, no scipy)
        block("4. 文本数值特征 vs gt_count 相关性 (Spearman)")
        corr_df = df[['quantity', 'num_regions', 'gt_count']].astype(float)
        log(corr_df.rank().corr(method='pearson').round(3).to_string())

    out = '\n'.join(L)
    with open('logs/corr_gt.md', 'w') as f:
        f.write("# GT 连通域与文本特征相关性分析报告 (Part B)\n\n" + out)
    print(f"\n[报告已保存: logs/corr_gt.md]")


if __name__ == '__main__':
    main()
