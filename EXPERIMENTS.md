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

> 发现:**约 8.6% 训练样本的数量词与位置句区域数不一致**(如 `two infected areas, all left lung and middle lower right lung` 位置句区域实为 2 个)。
> ⚠️ 注意:这不代表数量词是"语义噪声"——相关性分析(Part B)显示**数量词与真实 GT 连通域一致率高达 97.2%**(见下文相关性分析章节)。

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

> 记录 val/test 的 loss/acc/dice/MIoU。模型按 val_loss 选最优(early stopping patience=20)。

| 实验 | 分支 | 配置 | 最佳val_loss(epoch) | val_dice | val_MIoU | test_dice | test_MIoU | 备注 |
|---|---|---|---|---|---|---|---|---|
| E1 full | text-ablation | config/exp/full.yaml | 0.2126 (30) | 0.8613 | 0.7564 | **0.8947** | **0.8094** | 基线,epoch50 早停 |
| E2 location | text-ablation | config/exp/location.yaml | 0.2194 (33) | 0.8586 | 0.7522 | 0.8897 | 0.8014 | epoch53 早停 |
| E3 nature | text-ablation | config/exp/nature.yaml | 0.2812 (39) | 0.7991 | 0.6655 | 0.8273 | — | epoch59 早停 |
| E4 quantity | text-ablation | config/exp/quantity.yaml | 0.2846 (50) | 0.7964 | 0.6616 | 0.8308 | — | epoch70 早停 |
| E5 keyword | text-ablation | config/exp/keyword.yaml | 0.2161 (39) | 0.8579 | 0.7512 | 0.8881 | — | epoch59 早停 |
| E8 kw_nature | text-ablation | config/exp/kw_nature.yaml | 0.2873 (49) | 0.7931 | 0.6571 | 0.8328 | — | epoch69 早停,仅性质词 |
| E9 kw_quantity | text-ablation | config/exp/kw_quantity.yaml | 0.2919 (57) | 0.7951 | 0.6600 | 0.8340 | — | 仅数量词 |
| E10 kw_location | text-ablation | config/exp/kw_location.yaml | 0.2408 (44) | 0.8550 | 0.7468 | 0.8842 | — | 仅方位短语 |
| E6 aux_full | aux-supervision | config/exp/aux_full.yaml | 0.2243 (40) | 0.8596 | 0.7538 | 0.8919 | — | aux 监督未提升 |
| E7 aux_location | aux-supervision | config/exp/aux_location.yaml | 0.2894 (34) | 0.8480 | 0.7360 | 0.8792 | 0.7844 | aux 监督未提升(真实 test,已评估) |
| C1 count_full | aux-supervision | config/exp/count_full.yaml | ~1.37 (16) | 0.301 | 0.177 | 0.3641 | 0.2226 | 计数监督致分割崩溃;test count_acc=0.386 |
| C2 count_location | aux-supervision | config/exp/count_location.yaml | ~0.89 (34) | 0.192 | 0.106 | 0.2441 | 0.1390 | 同上;test count_acc=0.755 虚高 |
| C3 count_weighted | aux-supervision | config/exp/count_weighted.yaml | ~0.82 (0) | 0.211 | 0.118 | 0.3356 | 0.2017 | 类加权+只监督多区域仍崩;连通域回归损失不可行 |
| C4 aux_quantity_weighted | aux-supervision | config/exp/aux_quantity_weighted.yaml | ~0.18 (34) | — | — | **0.8904** | **0.8025** | 数量分类头监督成功:test_count_acc(面积过滤后)=**91.3%** |
| E11 aux_nature | aux-supervision | config/exp/aux_nature.yaml | ~0.22 (—) | 0.859 | 0.754 | 0.8896 | 0.8011 | 性质分类头:dice 持平,count_acc(面积过滤后)=**91.2%**(≈C4) |
| E12 clip_full | aux-supervision | config/exp/clip_full.yaml | ~0.48 (34) | 0.856 | 0.749 | 0.8825 | 0.7897 | CLIP 对比对齐损失:未提升,面积过滤 count_acc=**87.8%**(低于基线) |
| E13 unfreeze_full | aux-supervision | config/exp/unfreeze_full.yaml | ~0.31 (43) | 0.860 | 0.752 | 0.8914 | 0.8040 | 解冻 BERT 末2层:略低于基线,count_acc=90.1% |
| E14 multitext_full | aux-supervision | config/exp/multitext_full.yaml | ~0.32 (33) | 0.861 | 0.753 | 0.8907 | 0.8029 | 多层文本特征:略低于基线,count_acc=89.7% |
| E15 clip_clean | aux-supervision | config/exp/clip_clean_full.yaml | ~0.36 (0) | 0.746 | 0.595 | 0.8922 | 0.8054 | 去碎片对齐:修复CLIP碎片化,count_acc=**90.5%** |
| E16 film_full | aux-supervision | config/exp/film_full.yaml | ~0.30 (—) | 0.857 | 0.751 | 0.8913 | 0.8039 | **FiLM调制:count_acc=91.0%** |
| E17 tanda_full | aux-supervision | config/exp/tanda_full.yaml | ~0.31 (—) | 0.857 | 0.750 | 0.8874 | 0.7976 | TANDA文本增强:无提升,count_acc=89.7% |
| E18 aux_quantity_location | aux-supervision | config/exp/aux_quantity_location.yaml | ~0.31 (—) | 0.841 | 0.729 | 0.8613 | 0.7564 | 数量头+方位句:坏组合,count_acc=**70.8%**(文本缺数量词,最差) |
| E19 aux_quantity_w10 | aux-supervision | config/exp/aux_quantity_w10.yaml | ~0.30 (—) | 0.857 | 0.750 | 0.8874 | 0.7976 | 数量头 weight1.0:count_acc=90.3% |
| E20 aux_quantity_unfreeze | aux-supervision | config/exp/aux_quantity_unfreeze.yaml | ~0.30 (—) | 0.856 | 0.749 | 0.8869 | 0.7968 | 数量头+解冻:count_acc=89.4% |
| E21 aux_quantity_multitext | aux-supervision | config/exp/aux_quantity_multitext.yaml | ~0.31 (—) | 0.859 | 0.753 | 0.8888 | 0.7999 | 数量头+多层文本:count_acc=**90.8%** |
| E22 side_gate | aux-supervision | config/exp/side_gate_full.yaml | ~0.31 (—) | 0.857 | 0.750 | 0.8486 | 0.7370 | 侧别门控(中线拆分+性质句):dice 明显下降,count_acc=87.8% |

> ⚠️ **评估方法修正(重要)**:模型输出 `out` 已是 sigmoid 概率,早期分析脚本重复套 sigmoid 造成假碎片化。修正阈值(`out>0.5`)后,所有 count_acc 数值已重评(见 §3 更新)。修正后基线 count_acc(200px)=**90.7%**(原 87.3%),各模型提升幅度整体缩小。

> ⚠️ **关键发现(全部实验)**:
> 1. **完整三句(full)在 val/test 上均优于任何单句**——与论文「stage3 单独最优」不一致。
> 2. **分割性能主要由「方位」信息驱动**:
>    - 单个方位关键词 E10(0.8842)已接近完整文本 E1(0.8947)与方位句 E2(0.8897);
>    - 而性质/数量关键词 E8/E9(≈0.833)与对应句子 E3/E4(≈0.83)均明显更差。
> 3. **单关键词 vs 对应句子**:kw_nature(0.8328)> nature 句(0.8273)、kw_quantity(0.8340)> quantity 句(0.8308)
>    ——更精简的单关键词反而略优,提示句子中的冗余/噪声有轻微负作用;但方位句(0.8897)> 方位关键词(0.8842)。
> 4. **关键词监督辅助损失无益**:E6(0.8919)< E1(0.8947)、E7(0.8792)< E2(0.8897)。
> 5. 即:「更少文本反而更好」的现象在本数据集**未复现**;完整三句仍最优。
> 6. **连通域计数监督(C1/C2)是失败的**:`count_loss_weight=1.0` 加入后,模型学会**投机输出两个连通域**(文本数量词 "two infected areas" 占 ~74%,C2 count_acc 0.755 ≈ two 比例),count_acc 虚高但 dice 从 0.85+ 崩至 0.24~0.36。
>    原因:数量标签严重不平衡(two 占 ~74%),计数损失被多数类主导,压过 DiceCE,导致模型牺牲分割质量换取计数"正确"。
> 7. **类别不平衡修复(C 选项)结论**:
>    - **C3 类加权连通域回归仍失败**(dice 0.336):即使逆频率加权 + 只监督多区域 + 降权 0.3,连通域计数回归损失与像素级分割本质冲突 → **连通域回归监督这条路不可行**。
>    - **C4 数量分类头监督**:在深层特征上直接分类数量(加权 CE,aux_weight=0.3),test_dice 0.8904 ≈ 基线 0.8947,count_acc(面积过滤后)=**91.3%**(基线 90.7%,+0.6pp);少数类 true3 50%(基线 45%)、true4 50%(基线 25%)。增益有限但方向正确。
> 8. **连通域作为评估指标必须先做面积过滤**:未经后处理时,分割图因噪声小碎片,连通域数从正确值暴涨,count_acc 失真;过滤 <200px 组件后才有意义(修正后基线 90.7%,C4 91.3%)。
> 9. **修正后「数量头 vs 性质头」增益均有限(原结论被推翻)**:修正评估后,数量头 C4 count_acc=91.3%、性质头 E11=91.2%、基线=90.7%——三者几乎持平(±0.6pp)。
>    原「性质头损害区域计数(81.7%)」是双重 sigmoid 评估 bug 的假象。→ 辅助分类头监督本身**增益有限**(+0.5~0.6pp),远小于此前估计。
> 10. **CLIP 式图文对比对齐(E12)略有害**:test_dice 0.8825(<基线 0.8947),面积过滤后 count_acc=87.8%(<基线 90.7%)。
>    全局池化图像特征与文本嵌入的 InfoNCE 对齐轻微破坏分割(dice 与区域计数均略降),简单的全局对齐损失不适配本任务。
> 11. **unfreeze / multitext(文本利用增强)也无提升**:解冻 BERT 末 2 层(count_acc 90.1%)、多层文本特征融合(89.7%),均略低于基线(90.7%)。
>     → 在交叉注意力框架下,增强文本编码/表示都无法超越基线。
> 12. **clip_clean(去碎片后对齐)小幅修复 CLIP**:clip_full 87.8% → clip_clean 90.5%(去碎片 +2.7pp),dice 0.8825→0.8922。
>    → 去碎片确实缓解了对齐对区域结构的扰动,但修复后与基线(90.7%)基本持平,增益有限。
> 13. **FiLM 文本条件调制(E16)**:count_acc=91.0%(≈C4 91.3%、≈基线 90.7%),test_dice 0.8913 接近基线。显式文本调制与基线持平,无明显增益。
> 14. **TANDA 文本增强(E17)无提升**:count_acc=89.7%(≈基线),dice 0.8874 略低。
> 15. **数量头组合实验(E18-E21,修正后)**:
>    - E18 数量头+方位句:count_acc=**70.8%**(仍最差)→ **数量头必须从文本读到数量词**;
>    - E19/E20(weight1.0/解冻):90.3%/89.4%;E21 数量头+多层文本:**90.8%**——均与基线(90.7%)/C4(91.3%)相当,无显著增益。
> 16. **侧别门控(E22 side_gate)是负结果**:按左右肺中线拆分 + 性质句门控(训练时未声明侧强制背景)导致 test_dice 0.8486(<基线 0.8947)、count_acc 87.8%(<基线 90.7%)。
>    中线拆分不精确 + bilateral 学习受损,强制侧别门控反而损害分割。
> 可能原因:数据/标注版本差异、按 val_loss 选点 vs 论文选点方式、或现象在本数据不复现。
> 待 E4/E5/E6/E7 完成以补全曲线。

---

## 4. 机制假设(待验证)

1. **长度/截断**:full 文本更长,`max_length=24` 截断风险高,信息被挤压 → 已获 token 统计支持(17.45 vs 9.38)
2. **注意力聚焦**:方位句使交叉注意力更聚焦空间位置,引导更精准
3. ~~**语义噪声**~~(已修正):数量词与真实 GT 连通域一致率 97.2%(train)/98.3%(test),Spearman 0.95+,**并非噪声**;
   真正的轻微不一致来自位置句区域数(89.3%/93.2%)。见 §5 相关性分析。
4. **信息冗余**:nature 与 quantity 近乎确定性冗余(Cramer's V=0.979),两者携带几乎相同信息,削弱单独监督价值。

---

## 5. 相关性分析(文本特征 × 真实 GT 连通域)

> 两个脚本:Part A = `scripts/correlation_text.py`(文本特征内部相关性),Part B = `scripts/correlation_gt.py`(文本特征 vs 真实 mask 连通域数,GPU 精确计数)。报告:`logs/corr_text.md`、`logs/corr_gt.md`,GT 连通域数:`logs/gt_count_{train,test}.csv`。

### 5.1 真实连通域分布(GT,8-连通)
| gt_count | train | test |
|---|---|---|
| 1 区 | 20.4% | 20.1% |
| **2 区** | **72.2%** | **74.4%** |
| 3 区 | 6.2% | 5.1% |
| 4 区 | 1.0% | 0.4% |

### 5.2 文本特征 vs GT 连通域(关键)
| 特征 | 一致率 train | 一致率 test | Spearman(train) | Spearman(test) |
|---|---|---|---|---|
| **quantity(数量词)** | **97.2%** | **98.3%** | **0.951** | **0.970** |
| num_regions(位置句区域数) | 89.3% | 93.2% | 0.800 | 0.872 |

> **核心结论**:数量词几乎完美对应真实感染区域数(Spearman 0.95+),是**高度可靠的监督信号**。
> 之前观察到的 8.6% 不一致是**位置句少写/多写区域**造成的(num_regions 一致率仅 89-93%),而非数量词噪声。

### 5.3 文本特征内部相关性
- **nature × quantity:Cramer's V = 0.979**(近乎确定性冗余):双侧↔两个区域、单侧↔一个区域几乎一一对应(quantity=2 的 5226/5268 为 bilateral)。
- **nature × num_regions:V = 0.938**;quantity × num_regions:V = 0.649。
- **Zone 共现**:左右对称区共现高(UR-MR 0.72、UL-ML 0.67、UL-UR 0.67);LL-LR 仅 0.25(单侧下叶感染常见)。
- 数值特征 Spearman(quantity vs num_regions)= 0.832。

### 5.4 对实验的再解释
1. **E3/E4、E8/E9(性质/数量)分割差 ≈0.83**,不是因为文本带噪——数量词其实很准;而是因为**性质与数量相互冗余且均不含空间位置信息**,无法指导"在哪里分割"。
2. **count 实验(C1/C2)失败**不是标签噪声问题,而是**类别极不平衡(two 占 74%)+ 计数代理损失的优化投机**(模型输出 2 个连通域即可命中多数类)。
3. **位置句是唯一携带空间定位的特征**,与 E2/E10 表现最优(≈0.89)一致。

---

## 6. 运行方法

```bash
# 单实验(指定 GPU 与配置)
PYTHON=/home/hjj/anaconda3/envs/languided/bin/python \
  bash scripts/run_exp.sh <gpu> config/exp/<mode>.yaml

# 全部消融并行
bash scripts/run_ablation.sh
```

环境:`languided`(numpy 1.24.4 / torch 2.4.1)。注意:`device` 是 GPU **数量**(应为 1),物理卡由 `CUDA_VISIBLE_DEVICES` 指定。
