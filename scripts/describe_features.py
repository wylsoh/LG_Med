"""Descriptive statistics for the exported caption feature CSVs.

Reads logs/caption_features_{train,test}.csv and prints a full descriptive
report: sizes, sentence distributions, parsed attribute distributions, lung
zone frequencies, parsing success rates, quantity<->num_regions consistency
and text-length stats. Also writes a Markdown report to logs/desc_stats.md.
"""
import os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

ZONES = ["UL", "ML", "LL", "UR", "MR", "LR"]
L = []


def log(s=""):
    print(s)
    L.append(s)


def block(title):
    log(f"\n## {title}")
    log("-" * 60)


def dist_str(series, pct=True):
    """{value: count (pct%)} sorted by count desc."""
    vc = series.value_counts(dropna=False)
    parts = []
    for k, v in vc.items():
        key = 'None' if pd.isna(k) else k
        s = f"  {key}: {v}"
        if pct:
            s += f" ({100*v/len(series):.1f}%)"
        parts.append(s)
    return "\n".join(parts)


def main():
    for split in ['train', 'test']:
        df = pd.read_csv(f'logs/caption_features_{split}.csv')
        log(f"\n{'#'*72}\n# SPLIT: {split.upper()}  (n={len(df)})\n{'#'*72}")

        # ---- 规模 ----
        block("1. 规模与缺失")
        log(f"行数: {len(df)}")
        log(f"唯一图片: {df['Image'].nunique()}")
        na = df.isna().sum()
        na = na[na > 0]
        log(f"缺失值列: {na.to_dict() if len(na) else '无'}")

        # ---- 句子特征分布 ----
        block("2. 第1句·性质 (sentence_1_nature)")
        log(dist_str(df['sentence_1_nature']))
        log("(解析 nature: 0=单侧 1=双侧)")
        log(dist_str(df['nature']))

        block("3. 第2句·数量 (sentence_2_quantity)")
        log(dist_str(df['sentence_2_quantity']))
        log("(解析 quantity: 文本词 one=1..four=4)")
        log(dist_str(df['quantity']))
        log(f"quantity 解析失败数: {(~df['quantity_ok']).sum()}")

        block("4. 第3句·位置 (sentence_3_location) Top15")
        log("--- 最常用的前15个位置句 ---")
        top = df['sentence_3_location'].value_counts().head(15)
        for k, v in top.items():
            log(f"  [{v} ({100*v/len(df):.1f}%)] {k}")

        block("5. 位置句提到区域数 (num_regions)")
        log(dist_str(df['num_regions']))
        log(f"location 解析失败数: {(~df['location_ok']).sum()}")

        block("6. 肺区 Zone 出现频次 (每图含该区比例)")
        zone_count = collections.Counter()
        for locs in df['locations']:
            if pd.isna(locs) or locs == '':
                continue
            for z in str(locs).split('/'):
                zone_count[z] += 1
        for z in ZONES:
            log(f"  {z}: {zone_count[z]} ({100*zone_count[z]/len(df):.1f}%)")

        # ---- 关联: quantity vs num_regions ----
        block("7. 数量词 vs 区域数一致性")
        mask = df['quantity_ok'] & df['location_ok']
        sub = df[mask]
        consistent = (sub['quantity'] == sub['num_regions']).sum()
        log(f"可比样本: {len(sub)}")
        log(f"一致: {consistent} ({100*consistent/len(sub):.1f}%)")
        log(f"不一致: {len(sub)-consistent} ({100*(len(sub)-consistent)/len(sub):.1f}%)")
        # 交叉表
        log("交叉表 (行=quantity 文本词, 列=num_regions):")
        ct = pd.crosstab(sub['quantity'], sub['num_regions'])
        log(ct.to_string())

        # ---- 文本长度 ----
        block("8. 文本长度统计 (字符数)")
        for col, nm in [('raw_description', '完整描述'), ('sentence_1_nature', '性质句'),
                        ('sentence_2_quantity', '数量句'), ('sentence_3_location', '位置句')]:
            ln = df[col].str.len()
            log(f"  {nm}: 均值={ln.mean():.1f} 中位={ln.median():.0f} 最大={ln.max()}")

    # ---- 汇总 train vs test ----
    log(f"\n{'#'*72}\n# SUMMARY train vs test\n{'#'*72}")
    for split in ['train', 'test']:
        df = pd.read_csv(f'logs/caption_features_{split}.csv')
        q = df['quantity'].value_counts(dropna=False).sort_index()
        log(f"{split:5s} n={len(df):5d} | quantity分布=" +
            ", ".join(f"{int(k) if not pd.isna(k) else 'None'}:{v}" for k, v in q.items()))

    out = '\n'.join(L)
    with open('logs/desc_stats.md', 'w') as f:
        f.write("# 描述性统计报告\n\n" + out)
    print(f"\n[报告已保存: logs/desc_stats.md]")


if __name__ == '__main__':
    main()
