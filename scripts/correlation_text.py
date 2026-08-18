"""Correlation analysis among caption text features (part A: text-only).

Computes for train/test:
  - Pearson & Spearman correlation matrix of numeric features
    (nature, quantity, num_regions, and the 6 lung zones)
  - Cramer's V for the key categorical pairs
  - zone co-occurrence (phi coefficient)
  - conditional distributions: quantity x nature, quantity x num_regions
Writes report to logs/corr_text.md and prints a summary.
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

ZONES = ["UL", "ML", "LL", "UR", "MR", "LR"]
L = []


def log(s=""):
    print(s)
    L.append(s)


def block(t):
    log(f"\n## {t}")
    log("-" * 64)


def cramers_v(x, y):
    """Cramer's V for two categorical series (NaN dropped)."""
    d = pd.DataFrame({'x': x, 'y': y}).dropna()
    ct = pd.crosstab(d['x'], d['y'])
    chi2 = 0.0
    total = ct.values.sum()
    for i in range(ct.shape[0]):
        for j in range(ct.shape[1]):
            exp = ct.iloc[i].sum() * ct.iloc[:, j].sum() / total
            obs = ct.iloc[i, j]
            if exp > 0:
                chi2 += (obs - exp) ** 2 / exp
    k = min(ct.shape) - 1
    if k <= 0 or total == 0:
        return float('nan')
    return float(math.sqrt(chi2 / (total * k)))


def phi(x, y):
    """Phi coefficient for two binary series."""
    d = pd.DataFrame({'x': x, 'y': y}).dropna()
    ct = pd.crosstab(d['x'], d['y'])
    if ct.shape != (2, 2):
        return float('nan')
    a, b = ct.iloc[0, 0], ct.iloc[0, 1]
    c, dd = ct.iloc[1, 0], ct.iloc[1, 1]
    den = (a + b) * (c + dd) * (a + c) * (b + dd)
    if den == 0:
        return float('nan')
    return float((a * dd - b * c) / math.sqrt(den))


def main():
    for split in ['train', 'test']:
        df = pd.read_csv(f'logs/caption_features_{split}.csv')
        log(f"\n{'#'*68}\n# CORRELATION (TEXT) — {split.upper()} (n={len(df)})\n{'#'*68}")

        # zone one-hot columns
        for z in ZONES:
            df[z] = df['locations'].apply(lambda s: 1 if (isinstance(s, str) and z in s.split('/')) else 0)

        # ---- numeric correlation matrix ----
        num = df[['nature', 'quantity', 'num_regions'] + ZONES].copy()
        block("1. Pearson 相关矩阵 (nature, quantity, num_regions, 6 zones)")
        log(num.corr().round(3).to_string())

        block("2. Spearman 相关矩阵")
        log(num.corr(method='spearman').round(3).to_string())

        # ---- Cramer's V ----
        block("3. Cramer's V (类别特征关联强度)")
        pairs = [('nature', 'quantity'), ('nature', 'num_regions'),
                 ('quantity', 'num_regions')]
        for a, b in pairs:
            v = cramers_v(df[a], df[b])
            log(f"  {a} vs {b}: V = {v:.3f}")

        # ---- zone co-occurrence phi ----
        block("4. Zone 两两共现 Phi 系数 (0=独立, ±1=完全相关)")
        phi_mat = pd.DataFrame(index=ZONES, columns=ZONES, dtype=float)
        for i, z1 in enumerate(ZONES):
            for j, z2 in enumerate(ZONES):
                if i == j:
                    phi_mat.loc[z1, z2] = 1.0
                elif i < j:
                    v = phi(df[z1], df[z2])
                    phi_mat.loc[z1, z2] = v
                    phi_mat.loc[z2, z1] = v
        log(phi_mat.round(3).to_string())

        # ---- conditional distributions ----
        block("5. quantity x nature 交叉 (行=数量词, 列=0单侧/1双侧)")
        log(pd.crosstab(df['quantity'], df['nature'], margins=True).to_string())

        block("6. quantity x num_regions 交叉 (行=数量词, 列=区域数)")
        log(pd.crosstab(df['quantity'], df['num_regions'], margins=True).to_string())

    out = '\n'.join(L)
    with open('logs/corr_text.md', 'w') as f:
        f.write("# 文本特征相关性分析报告 (Part A)\n\n" + out)
    print(f"\n[报告已保存: logs/corr_text.md]")


if __name__ == '__main__':
    main()
