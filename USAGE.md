# LanGuideMedSeg 项目使用说明书

> 基于 MICCAI 2023 论文 *Ariadne’s Thread: Using Text Prompts to Improve Segmentation of Infected Areas from Chest X-ray images*  
> 本仓库当前环境：本机 AutoDL（基线复现）+ 他服实验归档（`experiments/`）

---

## 1. 项目是做什么的

用**文本提示**引导胸部 X 光图上的 COVID-19 感染区域分割。  
每张图对应一句三属性描述（性质 / 数量 / 方位），模型用视觉编码器 + 文本编码器，经 GuideDecoder 交叉注意力融合后输出分割 mask。

**后续研究主线**（见 `experiments/docs/`）：论文消融曾报告「单独方位句优于完整三句」——我们在同一数据上系统复现、解释，并尝试辅助监督 / 结构改动以提升分割与区域计数。

---

## 2. 目录架构

```
LG_Med/
├── train.py / evaluate.py     # 训练与测试入口（当前 main = 原始可跑基线）
├── config/training.yaml       # 超参与数据路径
├── engine/wrapper.py          # Lightning 封装（损失、指标、训练循环）
├── utils/
│   ├── model.py               # LanGuideMedSeg（视觉+文本+解码）
│   ├── layers.py              # GuideDecoder / 位置编码
│   ├── dataset.py             # QaTa 数据集
│   └── config.py              # YAML 配置加载
├── lib/                       # 本地预训练权重（CXR-BERT / ConvNeXt）
├── save_model/                # 本机训练得到的 checkpoint
├── lightning_logs/            # 本机 Lightning 日志（同步副本见 experiments）
├── log_file/                  # 本机运行时间记录
├── experiments/               # ★ 全部实验数据与汇报文档（已整理）
│   ├── README.md              # 实验归档说明与阅读顺序
│   ├── docs/                  # 实验记录 / 汇总 / 导师汇报
│   ├── remote_server/         # 他服实验原始产物
│   └── local_autodl/          # 本机 AutoDL 基线跑分
├── misc/                      # 论文框架图
├── USAGE.md                   # 本说明书
└── requirements.txt
```

### 数据流（训练）

```
train.csv + 图像
    → QaTa Dataset（tokenize + 图像增强）
    → DataLoader
    → LanGuideMedSegWrapper
         ├─ Vision: ConvNeXt-tiny（多尺度特征）
         ├─ Text: CXR-BERT（冻结）→ 投影
         └─ GuideDecoder ×3 + 上采样 → mask
    → DiceCELoss + Acc/Dice/Jaccard
    → checkpoint → save_model/
```

---

## 3. 环境准备

### 3.1 依赖

```bash
# 建议 Python 3.8
pip install -r requirements.txt
# 主要版本见 README：torch 1.12 / lightning 1.9 / transformers 4.24 / monai 1.0.1
```

他服实验环境曾使用：`torch 2.4.1` + 同系列 lightning/transformers，扩展分支代码见 `experiments/remote_server/code_snapshot/`（**不是**当前 `main` 源码）。

### 3.2 预训练模型

放到本地（或改 YAML 为 HuggingFace 在线名）：

| 模型 | 路径 |
|------|------|
| CXR-BERT-specialized | `./lib/BiomedVLP-CXR-BERT-specialized/` |
| ConvNeXt-tiny-224 | `./lib/convnext-tiny-224/` |

需含 `pytorch_model.bin` 与对应 config。

### 3.3 数据集 QaTa-COV19-v2

本机路径（见 `config/training.yaml`）：

```yaml
DATA:
  train_csv_path: ../autodl-tmp/data/QaTa-COV19-v2/prompt/train.csv
  train_root_path: ../autodl-tmp/data/QaTa-COV19-v2/Train
  test_csv_path:  ../autodl-tmp/data/QaTa-COV19-v2/prompt/test.csv
  test_root_path: ../autodl-tmp/data/QaTa-COV19-v2/Test
```

- 图像与 mask：Kaggle QaTa-COV19  
- 文本标注：参考 LViT 仓库第三方标注  
- 规模：train 7145 / test 2113；图像 224×224

文本格式示例：

```text
Bilateral pulmonary infection, two infected areas, all left lung and middle lower right lung.
```

---

## 4. 快速开始（本机基线）

### 训练

```bash
cd /root/LG_Med
python train.py --config ./config/training.yaml
```

关键配置项：

| 项 | 含义 | 当前值 |
|----|------|--------|
| `train_batch_size` | 训练 batch | 16 |
| `lr` | AdamW 学习率 | 3e-4 |
| `device` | **GPU 数量**（非卡号） | 1 |
| `patience` | early stopping | 20 |
| `model_save_path` | 权重目录 | `./save_model` |

选点规则：按 **val_loss** 最小保存；patience=20 早停。

### 评估（必须用 test 集）

```bash
python evaluate.py --config ./config/training.yaml
```

会加载 `./save_model/medseg.ckpt`，在 **test** 上报 Acc / Dice / Jaccard（即 MIoU）。

> 训练过程中屏幕打印的是 **验证集** 指标，与论文 Table 1 的 **测试集** 不可混用。

### 本机已有一次完整基线

| 项 | 值 |
|----|-----|
| 时间 | 2026-11-12 19:28–20:13（约 45 min，epoch≈31 早停） |
| GPU | RTX 2080 Ti；内存约 4.9 GB |
| 最佳大致 | val_dice ≈ 0.872 / val_MIoU ≈ 0.773（`lightning_logs/version_2`） |
| 权重 | `save_model/medseg.ckpt`（约 979 MB） |

详情：`experiments/local_autodl/NOTES.md`

---

## 5. 实验归档怎么读

| 文档 | 用途 |
|------|------|
| [`experiments/README.md`](experiments/README.md) | 归档目录说明 + 阅读顺序 |
| [`experiments/docs/PROGRESS_REPORT.md`](experiments/docs/PROGRESS_REPORT.md) | **导师汇报用进度总结（推荐）** |
| [`experiments/docs/EXPERIMENT_SUMMARY.md`](experiments/docs/EXPERIMENT_SUMMARY.md) | 结论速览与总表 |
| [`experiments/docs/EXPERIMENTS.md`](experiments/docs/EXPERIMENTS.md) | 逐实验完整记录 |
| [`experiments/docs/REPORT.md`](experiments/docs/REPORT.md) | 较早一版汇报稿 |

原始日志：`experiments/remote_server/logs/`、`lightning_logs/version_*`。

---

## 6. 常见问题

1. **OOM**：先降 `train_batch_size`；基线无 aux 时 batch=16 峰值约 4 GB 量级。  
2. **`device` 写错**：YAML 里是 GPU **个数**；指定物理卡用 `CUDA_VISIBLE_DEVICES=0`。  
3. **论文数字对不上**：用 `evaluate.py` 看 test，不要用训练时的 val。  
4. **连通域 count_acc**：评估前需面积过滤（&lt;200px）；且模型输出已是 sigmoid 概率，脚本勿再套一层 sigmoid。  
5. **扩展实验代码不在 main**：他服消融/辅助头等在扩展分支；本仓库 `main` 保持原版可跑，代码快照仅作参考。

---

## 7. 引用

```
@inproceedings{zhong2023ariadne,
  title={Ariadne’s Thread: Using Text Prompts to Improve Segmentation of Infected Areas from Chest X-ray Images},
  author={Zhong, Yi and Xu, Mengqiu and Liang, Kongming and Chen, Kaixin and Wu, Ming},
  booktitle={MICCAI},
  year={2023}
}
```
