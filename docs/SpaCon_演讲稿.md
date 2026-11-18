# SpaCon Oral Script（中英双语 · 精简版）· PRICAI-2026

> **会议时长**：13 min presentation + 3 min Q&A  
> **本口播目标**：**约 8:20**（略短于 10 分钟，便于控时）  
> **PPT**：`presentations/SpaCon_Presentation.pptx`（备注已同步）  
> **读法约定**：英文主稿；方括号 `[...]` 为生僻词发音；数字旁括号为英文读法  
> **已删除**：开场预计时长说明；“即插即用 / plug-and-play”；“零参数 / no learnable parameters”类表述

---

## 时长分配总表

| 页 | 内容 | 本页 | 累计 |
|----|------|------|------|
| 1 | Title / 封面 | ~15s | 0:15 |
| 2 | Agenda / 目录 | ~12s | 0:27 |
| 3 | Background / 背景 | ~55s | 1:22 |
| 4 | Hypothesis / 假设 | ~30s | 1:52 |
| 5 | SpaCon & CMC | ~45s | 2:37 |
| 6 | Objectives / 目标 | ~30s | 3:07 |
| 7 | Methods / 方法总览 | ~70s | 4:17 |
| 8 | SCM design | ~45s | 5:02 |
| 9 | ACDC results | ~45s | 5:47 |
| 10 | Qualitative / LA | ~35s | 6:22 |
| 11 | Pancreas + ablation | ~50s | 7:12 |
| 12 | Discussion | ~30s | 7:42 |
| 13 | Future | ~25s | 8:07 |
| 14 | Thank you | ~13s | 8:20 |
| — | Q&A / 答辩 | **3:00** | 13:00 slot |

---

## 发音速查（按出现顺序）

| Word | Pronunciation |
|------|---------------|
| complementary | `kom-pluh-MEN-tuh-ree` |
| consistency | `kuhn-SIS-tuhn-see` |
| quantitative | `KWON-tuh-tay-tiv` |
| prohibitively | `pro-HIB-ih-tiv-lee` |
| paradigms | `PAIR-uh-dymz` |
| integrity | `in-TEG-rih-tee` |
| semantic | `sih-MAN-tik` |
| continuity | `kon-tih-NOO-ih-tee` |
| anatomy / anatomical | `uh-NAT-uh-mee / an-uh-TOM-ih-kuhl` |
| hypothesis | `hy-POTH-uh-sis` |
| autoencoders | `AW-toh-en-koh-derz` |
| pseudo-labels | `SOO-doh-lay-buhlz` |
| artifacts | `AR-tih-fakts` |
| orthogonality | `or-thog-uh-NAL-ih-tee` |
| bilinear | `by-LIN-ee-er` |
| interpolation | `in-tur-puh-LAY-shun` |
| sigma | `SIG-muh` |
| qualitatively | `KWOL-ih-tay-tiv-lee` |
| atrium | `AY-tree-uhm` |
| pancreas | `PAN-kree-us` |
| ablation | `uh-BLAY-shun` |
| regularization | `REG-yuh-luh-ri-ZAY-shun` |
| volumetric | `vol-yuh-MET-rik` |

---

## Slide 1 · Opening（~15s｜累计 0:15）

**English**  
Good morning, everyone. My name is Shiqi Shi, from Wuhan University of Science and Technology. Today I'll present SpaCon: Spatial Complementary Consistency [kom-pluh-MEN-tuh-ree / kuhn-SIS-tuhn-see] for Semi-Supervised Medical Image Segmentation. This work is co-authored with Zhengshi Chen and Juanjuan He.

**中文**  
各位老师、各位同学，早上好。我是武汉科技大学的石诗淇。今天汇报 SpaCon：面向半监督医学图像分割的空间互补一致性方法。本工作由我和陈郑石、何娟娟老师共同完成。

---

## Slide 2 · Agenda（~12s｜累计 0:27）

**English**  
Here is today's roadmap: research background, hypothesis and objectives, methodology, main results, then discussion and next steps.

**中文**  
今天的路线：研究背景、假设与目标、方法、主要结果，以及讨论与下一步。

---

## Slide 3 · I · Background（~55s｜累计 1:22）

**English**  
Medical image segmentation is fundamental for diagnosis, surgical planning, and quantitative [KWON-tuh-tay-tiv] analysis. Deep learning has improved accuracy, but dense pixel-level annotation remains prohibitively [pro-HIB-ih-tiv-lee] expensive and depends on scarce clinical expertise. Semi-supervised learning is a natural choice: train with few labeled cases plus many unlabeled ones.

Two recent paradigms [PAIR-uh-dymz] work well: cross-image mixing, such as BCP, and masked image modeling. But both reduce input integrity [in-TEG-rih-tee]. Conventional masking discards spatial regions. Cross-image replacement and rigid grid boundaries disrupt the semantic [sih-MAN-tik] continuity [kon-tih-NOO-ih-tee] of anatomy [uh-NAT-uh-mee]. The open question: can we use unlabeled data while keeping spatial completeness and continuous anatomical [an-uh-TOM-ih-kuhl] boundaries?

**中文**  
医学图像分割对诊断、手术规划与定量分析很关键。深度学习提升了精度，但像素级标注昂贵，且依赖稀缺专科经验。半监督因此很自然：少量有标签加大量无标签一起训练。

近年两条路线效果好：跨图像混合（如 BCP）和掩码建模。但都会削弱输入完整性——传统掩码丢掉空间区域；跨图像替换和硬网格边界打断解剖语义连续性。核心问题是：利用无标签时，能否同时保住空间完整性与连续解剖边界？

---

## Slide 4 · II · Hypothesis（~30s｜累计 1:52）

**English**  
Our hypothesis [hy-POTH-uh-sis]: if we use complementary masks to retain complete information—instead of scrambling or discarding it—we can maximize spatial utilization and get more accurate, continuous anatomical segmentation. In short: two complementary views teach each other, yet together they still cover the full image.

**中文**  
我们的假设：用互补掩码保留完整信息，而不是打乱或丢弃，就能更好利用空间信息，得到更准确、更连续的解剖分割。一句话：两路互补视图互相教学，合起来仍覆盖整图。

---

## Slide 5 · II · SpaCon / CMC（~45s｜累计 2:37）

**English**  
This leads to SpaCon. Inspired by masked autoencoders [AW-toh-en-koh-derz], random masks can force the model to predict covered regions and produce better pseudo-labels [SOO-doh-lay-buhlz], also helping reduce edge artifacts [AR-tih-fakts] in mixing methods like BCP. But we do not throw pixels away—we use spatial complementary masking.

In CMC—Complementary Mask Consistency—each unlabeled image is split into two fully complementary spatial views for mutual pseudo-label supervision. For boundaries, Smooth Complementary Mask, or SCM, creates a transition zone so boundary pixels get weighted supervision from both views.

**中文**  
由此提出 SpaCon。受掩码自编码器启发，随机遮挡可逼模型预测被盖区域、提高伪标签质量，也有助于缓解 BCP 类边缘伪影。但我们不丢像素，而是做空间互补掩码。

CMC（互补掩码一致性）把无标签图分成两个完全互补的空间视图，做双向伪标签互监督。边界方面，SCM（平滑互补掩码）形成过渡带，让边界像素同时接受两路加权监督。

---

## Slide 6 · II · Objectives（~30s｜累计 3:07）

**English**  
We set three objectives. First, propose SpaCon as a lightweight local refinement module bridging macro-level cross-image mixing and micro-level structural integrity. Second, introduce CMC with bidirectional blind-spot mutual teaching, retaining all pixels. Third, design SCM to replace hard binary grids with continuous transition zones, smoothing gradients and removing grid artifacts.

**中文**  
三个目标：一，提出 SpaCon，桥接宏观跨图混合与微观结构完整性；二，引入 CMC，双向盲区互教学、保留全部像素；三，设计 SCM，用连续过渡带替换硬二值网格，平滑梯度、消除网格伪影。

---

## Slide 7 · III · Methods（~70s｜累计 4:17）

**English**  
As shown here, SpaCon has two branches sharing one student and one EMA [EE-em-AY, Exponential Moving Average] teacher.

The BCP branch handles macro-level distribution alignment via cross-image mixing. The CMC branch handles micro-level intra-image refinement with complementary masks. SCM smooths mask boundaries to cut grid artifacts.

For CMC: unlabeled images are partitioned into a regular grid to form two complementary views. Early on, a shared block ratio keeps overlapping context; it then decays linearly to strict spatial orthogonality [or-thog-uh-NAL-ih-tee]—from about zero point four (0.4) down to zero (0) over the first five thousand (5,000) steps. A bidirectional blind-spot mechanism lets each view supervise the invisible pixels of its complement. We apply stop-gradient to avoid collapse.

**中文**  
如图，SpaCon 两条分支共用学生网络与 EMA（指数滑动平均）教师。

BCP 做宏观跨图分布对齐；CMC 做图内互补精炼；SCM 平滑掩码边界。

CMC：无标签图按网格分成两个互补视图。训练早期共享块比例保留重叠上下文，再线性衰减到严格正交——从约 zero point four（0.4）降到 zero（0），前 five thousand（5,000）步完成。双向盲区互监督，并加 stop-gradient 防塌缩。

---

## Slide 8 · III · SCM（~45s｜累计 5:02）

**English**  
SCM in three steps. Motivation: hard binary masks jump from zero (0) to one (1) at grid edges, so boundary pixels belong to only one view—along a stripe that is not an anatomical boundary.

Pipeline: we replace nearest-neighbor upsampling with bilinear [by-LIN-ee-er] interpolation [in-tur-puh-LAY-shun] plus average pooling, forming a continuous transition zone. With sigma [SIG-muh] equal to zero point three (0.3) and block size eight (8), the soft band is about one to two (1–2) pixels wide.

Outcome: boundary pixels receive soft supervision from both views, encouraging consistent anatomy.

**中文**  
SCM 分三步。动机：硬掩码在网格边从 zero（0）跳到 one（1），边界像素只属一边——这条断裂线并不对应解剖边界。

流程：双线性插值加平均池化，形成连续过渡带；sigma 取 zero point three（0.3）、块大小 eight（8）时，约 one to two（1–2）像素宽。

结果：边界同时接受两路软监督，解剖边界更一致。

---

## Slide 9 · IV · ACDC（~45s｜累计 5:47）

**English**  
On ACDC [AY-see-dee-see] with seven (7) labeled cases—about ten percent (10%) annotation—SpaCon reaches Dice ninety point three one percent (90.31%), HD95 [aitch-dee-ninety-five] one point three two millimeters (1.32 mm), and ASD [AY-ess-dee] zero point four six millimeters (0.46 mm). Versus our reproduced BCP baseline: about plus one point two (1.2) Dice points, and minus one point seven three millimeters (1.73 mm) in HD95.

With only three (3) labeled cases, we still get Dice eighty-nine point three three percent (89.33%) and HD95 one point three seven millimeters (1.37 mm)—a two point eight three (2.83) point gain, nearly matching the seven-case setting. So when labels are scarce, intra-image complementary supervision helps even more.

**中文**  
ACDC、seven（7）例有标签（约 ten percent / 10%）下，SpaCon 达到 Dice ninety point three one percent（90.31%）、HD95 one point three two millimeters（1.32 mm）、ASD zero point four six millimeters（0.46 mm）；相对复现 BCP 约 +one point two（1.2）个百分点，HD95 −one point seven three mm（1.73 mm）。

仅 three（3）例时仍达 eighty-nine point three three percent（89.33%）/one point three seven mm（1.37 mm），提升 two point eight three（2.83）个百分点，接近七例水平。

---

## Slide 10 · IV · Qualitative（~35s｜累计 6:22）

**English**  
Qualitatively [KWOL-ih-tay-tiv-lee], on ACDC SpaCon yields sharper boundaries than MT, MC-Net, UA-MT, and BCP—consistent with the one point seven three millimeter (1.73 mm) HD95 gain.

On the left-atrium [AY-tree-uhm] LA dataset with eight (8) labeled cases, boundaries are more continuous: about zero point six nine millimeters (0.69 mm) better HD95, and Dice ninety point three zero percent (90.30%). Gains transfer from two-D (2D) cardiac MRI to three-D (3D) left-atrium segmentation.

**中文**  
定性上，ACDC 中 SpaCon 边界更锐，对应 HD95 改善 one point seven three mm（1.73 mm）。

左心房 LA、eight（8）例标注下边界更连续：HD95 约改善 zero point six nine mm（0.69 mm），Dice ninety point three zero percent（90.30%）。收益从 2D 心脏 MRI 迁移到 3D 左心房分割。

---

## Slide 11 · IV · Ablation（~50s｜累计 7:12）

**English**  
On NIH Pancreas [PAN-kree-us] CT with ten percent (10%) labels, Dice reaches eighty-two point five four percent (82.54%)—three (3) points above the reproduced baseline. The larger gain at ten percent (10%) than at twenty percent (20%) again shows intra-image self-supervision helps most when labels are limited.

Ablation [uh-BLAY-shun] on ACDC with seven (7) cases: BCP alone gives Dice eighty-nine point one one (89.11) and HD95 three point zero five (3.05). CMC alone can raise Dice but worsen HD95. BCP plus hard-mask CMC helps Dice, yet boundaries stay weak. Adding SCM reaches Dice ninety point three one (90.31) and HD95 one point three two (1.32). So: BCP aligns distributions, CMC refines inside the image, SCM cleans boundary artifacts.

**中文**  
Pancreas CT、ten percent（10%）标注下 Dice eighty-two point five four percent（82.54%），相对复现基线 +three（3）个百分点；ten percent（10%）收益大于 twenty percent（20%）。

ACDC seven（7）例消融：仅 BCP 为 eighty-nine point one one（89.11）/three point zero five（3.05）；仅 CMC 可抬 Dice 但 HD95 变差；BCP+硬掩码改善 Dice、边界仍弱；加 SCM 达 ninety point three one（90.31）/one point three two（1.32）。结论：BCP 对齐分布，CMC 图内精炼，SCM 清边界伪影。

---

## Slide 12 · V · Discussion（~30s｜累计 7:42）

**English**  
SpaCon shows that micro-level intra-image supervision complements macro-level cross-image distribution alignment, yielding sharper, more anatomical boundaries. It reuses the shared teacher network with little extra cost.

Limitations: fixed grid orientation and uniform SCM width may blur high-frequency details; and as a local refinement module, CMC still relies on a macro baseline like BCP early in training.

**中文**  
SpaCon 说明：微观图内监督可补上宏观跨图对齐，边界更锐、更符合解剖；并复用共享教师网络，额外开销很小。

局限：网格方向与过渡宽度固定，高频细节可能被抹平；CMC 作为局部精炼，早期仍依赖 BCP 类宏观基线。

---

## Slide 13 · V · Future（~25s｜累计 8:07）

**English**  
Next: uncertainty-guided adaptive boundary sampling to reduce baseline dependence; anatomy-aware transition widths matched to local edge sharpness; and cross-slice continuity regularization [REG-yuh-luh-ri-ZAY-shun] for fuller three-D (3D) volumetric [vol-yuh-MET-rik] scans.

**中文**  
下一步：不确定性引导的自适应边界采样；解剖感知过渡宽度；以及跨切片连续性约束，更好适配 3D 体数据。

---

## Slide 14 · Closing（~13s｜累计 8:20）

**English**  
Thank you for your attention. Our code is on GitHub, and I'm happy to take questions.

**中文**  
感谢聆听。代码已开源在 GitHub，欢迎提问。

---

## 答辩预案（约 3 分钟 · 英文）

**Q1: Difference from standard masked consistency?**  
We do not discard pixels. Complementary masks cover the full image together; each view teaches the other's blind spot, with stop-gradient to prevent collapse.

**Q2: Why couple CMC with BCP?**  
Ablation [uh-BLAY-shun]: CMC alone can raise Dice but hurt HD95. BCP gives the macro prior; CMC refines locally.

**Q3: Why sigma = zero point three (0.3)?**  
Too small ≈ hard boundary; too large dilutes complementarity. σ=0.3 / s=8 gave best HD95 one point three two millimeters (1.32 mm) on ACDC.

**Q4: 3D setting?**  
LA / Pancreas use V-Net; masks extend to depth with eight-by-eight-by-eight (8×8×8) tiles; SCM uses trilinear upsampling.

---

## 关键数字读法卡

| 数字 | English |
|------|----------|
| 0.4 → 0 | zero point four → zero |
| 5,000 | five thousand |
| 0.3 / 8 / 1–2 | zero point three / eight / one to two |
| 7 / 10% | seven / ten percent |
| 90.31% / 1.32 mm / 0.46 mm | ninety point three one percent / one point three two millimeters / zero point four six millimeters |
| +1.2 / −1.73 mm | plus one point two / minus one point seven three millimeters |
| 3 / 89.33% / 1.37 mm / +2.83 | three / eighty-nine point three three percent / one point three seven millimeters / plus two point eight three |
| 8 / 0.69 mm / 90.30% | eight / zero point six nine millimeters / ninety point three zero percent |
| 10% / 82.54% / +3 | ten percent / eighty-two point five four percent / plus three |
| 89.11 / 3.05 → 90.31 / 1.32 | eighty-nine point one one / three point zero five → ninety point three one / one point three two |
