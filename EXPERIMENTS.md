# 实验记录:为什么更少的文本信息反而更好?

> 目标:复现并解释 LanGuideMedSeg 论文消融现象——**单独使用第 3 句(方位句,stage3)的分割效果优于完整三句**。
>
> 方法:用正则提取文本中的「性质 / 数量 / 方位」关键词,通过 **前端文本替换消融** 与 **关键词监督辅助多任务损失** 两条路线设计实验。

---

## 1. 数据与文本格式

QaTa-COV19 的每条描述为单字符串,由三句逗号分隔:

| 句 | 属性 | 示例 |
|---|---|---|
| 第 1 句 | 性质 nature | `Bilateral pulmonary infection` |
| 第 2 句 | 数量 quantity | `two infected areas` |
| 第 3 句 | 方位 location | `all left lung and middle lower right lung.` |

**解析统计(utils/text_process.py)**:

| 数据集 | 条数 | nature ok | quantity ok | location ok | 全部 ok | 数量句与区域数矛盾 |
|---|---|---|---|---|---|---|
| train.csv | 7145 | 100% | 99.85% | 99.90% | 99.75% | **612 (8.6%)** |
| test.csv | 2113 | 100% | 99.95% | 99.95% | 99.90% | 134 (6.3%) |

> 发现:**约 8.6% 训练样本的数量句与实际方位区域数不一致**(如 `two infected areas, all left lung and middle lower right lung` 区域实为 2 个)。这支持「数量句含语义噪声」假设。

**各变体在 CXR-BERT 下的真实 token 长度**:

| 模式 | 平均 token | 最大 token |
|---|---|---|
| full(三句) | **17.45** | 24(贴近截断上限) |
| nature | 5.00 | 5 |
| quantity | 8.02 | 22(个别回退) |
| location | **9.38** | 17 |
| keyword | 13.36 | 18 |

> 支持「长度/注意力」假设:完整文本的 token 数约为方位句的 2 倍。

---

## 2. 实验设计

### 2.1 前端文本替换消融(exp/text-ablation 分支)
通过 `TEXT.text_mode` 把输入文本替换为不同信息量的变体,其余不变:
- E1 `full` — 完整三句(基线,复现论文)
- E2 `location` — 仅方位句(期望最优,复现论文 stage3 现象)
- E3 `nature` — 仅性质句
- E4 `quantity` — 仅数量句
- E5 `keyword` — 极简结构化关键词(`bilateral, 2, all left lung and middle lower right lung.`)

### 2.2 关键词监督辅助损失(exp/aux-supervision 分支)
新增 `utils/aux_head.py`:从分割解码器 os4 特征(全局池化)接 3 个小头,用正则解析出的关键词做监督:
- nature:2 类 BCE;quantity:4 类 CE;location:6 维 multi-hot BCE
- 总损失 `L = DiceCE + aux_weight × (L_nature + L_quantity + L_location)`
- 实验:
  - E6 `aux_full` — full 文本 + 辅助损失
  - E7 `aux_location` — location 文本 + 辅助损失

> 所有扩展由 config 开关(`use_aux` / `text_mode`)保护,**默认关闭**,与原始行为完全一致;`main` 分支保持原版可运行。

---

## 3. 结果

> 训练进行中…(记录 val/test 的 loss/acc/dice/MIoU)

| 实验 | 分支 | 配置 | val_dice | val_MIoU | test_dice | test_MIoU | 备注 |
|---|---|---|---|---|---|---|---|
| E1 full | text-ablation | config/exp/full.yaml | 训练中… | | | | 基线 |
| E2 location | text-ablation | config/exp/location.yaml | 训练中… | | | | 期望最优 |

**早期信号(epoch 3)**:
- E1(full):val_dice **0.811** / val_MIoU 0.682
- E2(location):val_dice **0.820** / val_MIoU 0.695

---

## 4. 机制假设(待验证)

1. **长度/截断**:full 文本更长,`max_length=24` 截断风险高,信息被挤压 → 已获 token 统计支持(17.45 vs 9.38)
2. **注意力聚焦**:方位句使交叉注意力更聚焦空间位置,引导更精准
3. **语义噪声**:数量句与 mask 连通域数量不一致(约 8.6%)→ 已获解析统计支持
4. **信息冗余**:性质/数量与分割任务弱相关,甚至引入歧义

---

## 5. 运行方法

```bash
# 单实验(指定 GPU 与配置)
PYTHON=/home/hjj/anaconda3/envs/languided/bin/python \
  bash scripts/run_exp.sh <gpu> config/exp/<mode>.yaml

# 全部消融并行
bash scripts/run_ablation.sh
```

环境:`languided`(numpy 1.24.4 / torch 2.4.1)。注意:`device` 是 GPU **数量**(应为 1),物理卡由 `CUDA_VISIBLE_DEVICES` 指定。
