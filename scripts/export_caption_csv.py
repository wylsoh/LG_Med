"""Export QaTa-COV19 caption texts into a feature-per-sentence CSV table.

Each raw Description = 3 comma-separated sentences:
    sentence_1_nature, sentence_2_quantity, sentence_3_location
Plus parsed structured features (nature/quantity/num_regions/zones + validity).

Output: logs/caption_features_{train,test}.csv

Note on quantity semantics:
  - `quantity` column uses the TEXT meaning: 1=one, 2=two, 3=three, 4=four.
  - (The aux-head label in to_labels() uses class index quantity-1; do NOT mix.)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from utils.text_process import parse_caption

SPLITS = [
    ('train', 'data/QaTa-COV19-v2/prompt/train.csv'),
    ('test',  'data/QaTa-COV19-v2/prompt/test.csv'),
]


def split_sentences(desc: str):
    """Split a description into its 3 sentences (strip, drop trailing dot)."""
    return [p.strip().rstrip('.') for p in str(desc).split(',')]


def main():
    for name, path in SPLITS:
        df = pd.read_csv(path)
        rows = []
        for _, r in df.iterrows():
            img = r['Image']
            desc = str(r['Description'])
            sents = split_sentences(desc)
            p = parse_caption(desc)
            rows.append({
                'Image': img,
                'raw_description': desc,
                'sentence_1_nature': sents[0] if len(sents) > 0 else '',
                'sentence_2_quantity': sents[1] if len(sents) > 1 else '',
                'sentence_3_location': sents[2] if len(sents) > 2 else '',
                'nature': p['nature'],              # 0=unilateral 1=bilateral, None=未解析
                'nature_ok': p['nature_ok'],
                'quantity': p['quantity'],          # 文本语义 1-4, None=未解析
                'quantity_ok': p['quantity_ok'],
                'num_regions': p['num_regions'],    # 位置句提到的区域个数
                'locations': '/'.join(p['locations']) if p['locations'] else '',
                'location_ok': p['location_ok'],
            })
        out = pd.DataFrame(rows)
        out_path = f'logs/caption_features_{name}.csv'
        out.to_csv(out_path, index=False)
        print(f'{name}: {len(out)} rows -> {out_path}')
        print(f'  列: {list(out.columns)}')
        print('  数量词(quantity)分布:',
              out['quantity'].value_counts().sort_index().to_dict())
        print()


if __name__ == '__main__':
    main()
