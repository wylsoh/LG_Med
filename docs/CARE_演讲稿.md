# CARE Oral Script（中英双语）· PRICAI-2026

> **论文/PPT**：Continuous Anchor-based Recalibration for Unsupervised VLM Adaptation  
> **会议时长**：约 13 min presentation + 3 min Q&A  
> **口播目标**：约 **11:15**（原 PPT 备注时长合计；备份页不计时）  
> **PPT**：`presentations/CARE_Conference_Presentation.pptx`（备注已写入双语稿）  
> **读法**：上台主读 English；`/IPA/` 音标；括号内为数字英文读法

---

## 时长分配总表（口播页）

| 页 | 内容 | 本页 | 累计 |
|----|------|------|------|
| 1 | Title | ~20s | 0:20 |
| 2 | Why label-free VLM adaptation drifts | ~50s | 1:10 |
| 3 | Keep the semantic reference fixed | ~45s | 1:55 |
| 4 | What information is available | ~40s | 2:35 |
| 5 | Frozen multi-view prototype bank | ~55s | 3:30 |
| 6 | Representation anchoring | ~60s | 4:30 |
| 7 | Decision recalibration | ~65s | 5:35 |
| 8 | Stable anchor channel; efficient final model | ~55s | 6:30 |
| 9 | Six benchmarks, one protocol | ~40s | 7:10 |
| 10 | CARE wins on all six datasets (LLM) | ~70s | 8:20 |
| 11 | Each component contributes | ~60s | 9:20 |
| 12 | Less data; cleaner clusters | ~55s | 10:15 |
| 13 | Takeaways and outlook | ~50s | 11:05 |
| 14 | Thank you | ~10s | 11:15 |
| 15–17 | Backup（答辩备用） | — | — |
| — | Q&A | **~3:00** | 13:00 slot |

---

## 音标速查（IPA）

| Word | IPA |
|------|-----|
| recalibration | `/ˌriːˌkæləˈbreɪʃən/` |
| semantic | `/sɪˈmæntɪk/` |
| misalignment | `/ˌmɪsəˈlaɪnmənt/` |
| pseudo-labels | `/ˈsuːdoʊ ˈleɪbəlz/` |
| prototypes | `/ˈproʊtətaɪps/` |
| complementary | `/ˌkɑːmpləˈmentəri/` |
| Gemini | `/ˈdʒemɪni/` |
| LogSumExp | `/lɔːɡ sʌm ɪkˈsp/` |
| EMA | `/ˌiː em ˈeɪ/` |
| entropy | `/ˈentrəpi/` |
| Polyak–Łojasiewicz | `/ˈpɔːliæk wəˈjɑːʃɛvɪtʃ/` |
| MPA | `/ˌem piː ˈeɪ/` |
| ablation | `/əˈbleɪʃən/` |
| t-SNE | `/ˌtiː ˈsniː/` |

---

## Slide 1 · Opening — Title（~20s｜累计 0:20）

**English**  
Good afternoon. I'm Shiqi Shi. I'm presenting today on behalf of Yujie Wang, who couldn't join us due to a scheduling conflict. This work introduces Continuous Anchor-based Recalibration /ˌriːˌkæləˈbreɪʃən/, or CARE, a framework for adapting vision-language models using unlabeled target-domain images. The central idea is simple: rather than trusting the model's changing predictions alone, we continuously refer to a fixed semantic /sɪˈmæntɪk/ coordinate system.

**中文**  
下午好。我是石诗淇。今天我代表王宇杰作报告，他因行程冲突未能到场。这项工作提出 Continuous Anchor-based Recalibration，简称 CARE：用无标签目标域图像适配视觉–语言模型。核心很简单：不只依赖模型不断变化的预测，而是持续对照一套固定的语义坐标系。

---

## Slide 2 · Motivation — Why label-free VLM adaptation drifts（~50s｜累计 1:10）

**English**  
Pretrained CLIP provides strong zero-shot recognition by matching images with text. However, specialized target domains introduce visual-semantic misalignment /ˌmɪsəˈlaɪnmənt/, especially for fine-grained classes. Standard self-training generates pseudo-labels /ˈsuːdoʊ ˈleɪbəlz/ and then optimizes on those same predictions. If an early prediction is confidently wrong, future updates may amplify it. This is the semantic drift problem. CARE attacks this feedback loop by using class semantics as an external reference that stays fixed throughout optimization. The reference both guides visual features and helps stabilize training decisions.

**中文**  
预训练 CLIP 通过图文匹配提供很强的零样本识别。但专用目标域会出现视觉–语义错位，细粒度类别尤其明显。标准自训练会生成伪标签，再在这些预测上优化；若早期高置信预测错了，后续更新可能放大错误——这就是语义漂移。CARE 打破这一反馈环：用类别语义作外部参考，并在整个优化过程中保持固定；它既引导视觉特征，也帮助稳定训练决策。

---

## Slide 3 · Key Idea — Keep the semantic reference fixed（~45s｜累计 1:55）

**English**  
The distinction from ordinary self-training is that our semantic prototypes /ˈproʊtətaɪps/ do not co-evolve with the image encoder. They are frozen throughout adaptation. CARE uses this reference in two complementary /ˌkɑːmpləˈmentəri/ ways: a representation channel explicitly aligns visual embeddings to the anchors, and a decision channel stabilizes pseudo-label learning using teacher-student consistency and class-balanced sample selection. Finally, the framework is parameter-efficient. We train visual prompt tokens, and discard the teacher, buffer, and training losses after adaptation.

**中文**  
与普通自训练的区别是：语义原型不与图像编码器共同演化，适配全程冻结。CARE 从两方面使用该参考：表征通道把视觉嵌入显式对齐到锚点；决策通道用师生一致性与类别均衡采样稳定伪标签学习。框架也参数高效：只训练视觉 prompt，适配结束后丢掉教师、缓冲与训练损失模块。

---

## Slide 4 · Problem Setting — What information is available（~40s｜累计 2:35）

**English**  
The task is closed-set classification on an unlabeled target-domain adaptation split. We know the candidate class names, but use neither image labels nor a labeled validation set. Three semantic protocols are evaluated. Base uses class names. The LLM protocol generates multiple complementary textual descriptions per category. Where structured class-level metadata exists, the attribute protocol uses those weights to define more informative anchors. This last protocol is side-information-assisted label-free adaptation, and it is important not to confuse class attributes with target image labels.

**中文**  
任务是无标签目标域适配划分上的闭集分类。我们知道候选类名，但不用图像标签，也不用有标签验证集。评估三种语义协议：Base 只用类名；LLM 协议为每类生成多条互补文本描述；若有结构化类级元数据，Attribute 协议用其权重定义更信息丰富的锚点。后者是旁路信息辅助的无标签适配——切勿把类属性与目标图像标签混淆。

---

## Slide 5 · Method 1/3 — Frozen multi-view prototype bank（~55s｜累计 3:30）

**English**  
We first build a bank of frozen semantic prototypes. In the LLM protocol, Gemini two point five Flash /ˈdʒemɪni/ generates ten (10) textual descriptions for each class, covering visual attributes, shape, and contextual information. We encode the descriptions with the frozen CLIP text encoder and normalize the embeddings. During classification, the score for a class is the maximum image-text similarity across that class's views, instead of a plain average. When a dataset supplies class attributes, we encode class-conditioned attribute descriptions and combine them using their given weights into a single anchor per class. Crucially, none of these anchors is updated during training.

**中文**  
首先构建冻结的语义原型库。LLM 协议下，Gemini 2.5 Flash 为每类生成 ten（10）条文本描述，覆盖外观、形状与上下文。用冻结的 CLIP 文本编码器编码并归一化。分类时，类分数取该类各视图上图文相似度的最大值，而非简单平均。若数据集提供类属性，则编码条件化属性描述，按给定权重合成为每类一个锚点。关键：这些锚点在训练中一律不更新。

---

## Slide 6 · Method 2/3 — Representation anchoring（~60s｜累计 4:30）

**English**  
The representation channel directly constrains the geometry of image features. For a high-confidence image, the teacher supplies a pseudo-label. We compute its similarity to each frozen class prototype, using a differentiable LogSumExp /lɔːɡ sʌm ɪkˈsp/ aggregation across semantic views. The representation loss then increases the score of its predicted class while contrasting against negative classes. In geometric terms, the visual feature is pulled toward a fixed semantic region rather than following a moving, jointly learned class center. Importantly, this is not immune to incorrect pseudo-labels; confidence gating and balanced selection are essential to limit that bias.

**中文**  
表征通道直接约束图像特征几何。对高置信样本，教师给出伪标签；我们计算其与各类冻结原型的相似度，并用可微 LogSumExp 聚合多语义视图。表征损失抬高预测类分数，同时与负类对比——几何上是把视觉特征拉向固定语义区域，而不是跟着共同学习、不断移动的类中心走。但该方法并不免疫错误伪标签；置信门控与均衡选择对限制偏差至关重要。

---

## Slide 7 · Method 3/3 — Decision recalibration（~65s｜累计 5:35）

**English**  
This figure illustrates the overall CARE framework. On the left, the teacher and student process weakly and strongly augmented images, respectively. The teacher is updated through EMA /ˌiː em ˈeɪ/. In the middle, frozen semantic prototypes provide a stable external reference. On the right, confidence gating filters unreliable predictions, while class-balanced sampling prevents dominant classes from overwhelming training. Together with teacher-student consistency, these mechanisms stabilize pseudo-label learning and reduce semantic drift.

**中文**  
这张图展示 CARE 整体框架。左侧：教师与学生分别处理弱增强与强增强图像，教师经 EMA 更新。中间：冻结语义原型提供稳定的外部参考。右侧：置信门控过滤不可靠预测，类别均衡采样避免优势类主导训练。再配合师生一致性，这些机制稳定伪标签学习并减轻语义漂移。

---

## Slide 8 · Optimization & Theory — Stable anchor channel; efficient final model（~55s｜累计 6:30）

**English**  
The total objective combines the representation anchor loss with the decision consistency and entropy /ˈentrəpi/ losses. The paper also provides a stability argument for the representation anchoring channel. Under local smoothness, a Polyak–Łojasiewicz /ˈpɔːliæk wəˈjɑːʃɛvɪtʃ/ condition, bounded pseudo-label bias and bounded stochastic variance, the expected loss gap contracts toward a bounded neighborhood. The key is that the bias and variance terms control the residual error. We do not claim that this theorem covers the entire EMA and buffer dynamics. At inference time, we remove the teacher, class buffers and loss modules, retaining just the prompted student and the frozen text classifier.

**中文**  
总目标把表征锚点损失与决策一致性、熵损失结合。论文还给出表征锚定通道的稳定性论证：在局部光滑、Polyak–Łojasiewicz 条件、伪标签偏差与随机方差有界时，期望损失间隙收缩到有界邻域；残差由偏差与方差项控制。我们不声称该定理覆盖全部 EMA 与缓冲动态。推理时去掉教师、类缓冲与损失模块，只保留带 prompt 的学生与冻结文本分类器。

---

## Slide 9 · Experiments — Six benchmarks, one protocol（~40s｜累计 7:10）

**English**  
We evaluate on six (6) classification datasets covering fine-grained birds, pets, flowers, general objects, scenes and animals. The backbone is CLIP ViT-B/sixteen (ViT-B/16) with visual prompt tuning. Both pretrained encoders stay frozen, and only visual prompt parameters are learned. We compare against zero-shot CLIP, pseudo-label linear probing, UPL, MUST and ReCLIP under compatible offline protocols. We report both overall accuracy and mean per-class accuracy, or MPA /ˌem piː ˈeɪ/. The evaluation uses the same semantic source for all compatible methods within each anchor protocol.

**中文**  
我们在 six（6）个分类数据集上评估，覆盖细粒度鸟类、宠物、花卉、通用物体、场景与动物。骨干为 CLIP ViT-B/16，配合视觉 prompt tuning；预训练编码器冻结，只学视觉 prompt。对比零样本 CLIP、伪标签线性探测、UPL、MUST、ReCLIP，协议匹配。报告 overall accuracy 与 mean per-class accuracy（MPA）。同一锚点协议内，各可比方法使用相同语义来源。

---

## Slide 10 · Main Results — CARE wins on all six datasets (LLM)（~70s｜累计 8:20）

**English**  
The main table shows CARE achieving the highest accuracy on every dataset in all applicable anchor protocols. Here I visualize the LLM setting, where each bar is CARE's gain over the strongest competing method on that particular dataset. The margin ranges from zero point four (0.4) percentage points on AWA2 to one point five (1.5) points on Flowers-102. On CUB, CARE reaches fifty-two point seven percent (52.7%). On SUN397 it reaches sixty-six point nine percent (66.9%), and on IIIT-Pets ninety point two percent (90.2%). The result is not dependent on just one dataset: it holds for all six (6). The same ranking pattern holds in the Base and three-dataset attribute protocols.

**中文**  
主表显示：在所有适用锚点协议下，CARE 在每个数据集上都取得最高准确率。这里展示 LLM 设定，每根柱是 CARE 相对该数据集最强对照方法的增益：从 AWA2 的 zero point four（0.4）个百分点，到 Flowers-102 的 one point five（1.5）。CUB 达 fifty-two point seven percent（52.7%）；SUN397 达 sixty-six point nine percent（66.9%）；IIIT-Pets 达 ninety point two percent（90.2%）。不是单数据集偶然：六个数据集都成立；Base 协议与三数据集 Attribute 协议也呈同样排名模式。

---

## Slide 11 · Ablation — Each component contributes（~60s｜累计 9:20）

**English**  
The ablation /əˈbleɪʃən/ study clarifies why performance improves. On CUB with attribute anchors, full CARE achieves fifty-eight point eight four percent (58.84%) accuracy. Removing the representation anchor loss reduces accuracy to fifty-seven point zero one percent (57.01%), a drop of one point eight three (1.83) points. Removing the decision loss reduces it to fifty-seven point two zero (57.20), a drop of one point six four (1.64). Replacing class-balanced selection with plain confidence thresholding reduces it to fifty-seven point five three (57.53). These results show that feature anchoring, decision recalibration and balanced sample selection are complementary rather than redundant. The same table reports VPT outperforming both full fine-tuning and LoRA for this setting.

**中文**  
消融说明提升来源。CUB + 属性锚点下，完整 CARE 达 fifty-eight point eight four percent（58.84%）。去掉表征锚点损失降至 fifty-seven point zero one percent（57.01%），降 one point eight three（1.83）；去掉决策损失降至 fifty-seven point two zero（57.20），降 one point six four（1.64）；用纯置信阈值替代类别均衡降至 fifty-seven point five three（57.53）。说明特征锚定、决策再校准与均衡采样是互补而非冗余；同表也显示该设定下 VPT 优于全量微调与 LoRA。

---

## Slide 12 · Further Evidence — Less data; cleaner clusters（~55s｜累计 10:15）

**English**  
Beyond the main result table, CARE is effective when unlabeled adaptation data is scarce. The left plot shows accuracy and mean per-class accuracy on CUB as the training split shrinks from one hundred percent (100%) to twenty percent (20%). CARE stays above the comparison methods over the tested sizes. On the right, the original t-SNE /ˌtiː ˈsniː/ visualizations compare learned embeddings from zero-shot CLIP and several adaptation baselines. CARE exhibits more compact and more clearly separated class clusters. These qualitative plots support the intended feature-geometry effect, although t-SNE is descriptive rather than a proof of class separability.

**中文**  
除主表外，无标签适配数据稀缺时 CARE 仍然有效。左图：CUB 上训练划分从 one hundred percent（100%）缩到 twenty percent（20%），准确率与 MPA 在测试规模上均高于对照。右图：原文 t-SNE 对比零样本 CLIP 与多种适配基线的嵌入；CARE 的类簇更紧、分离更清晰。这些定性图支持预期的特征几何效应，但 t-SNE 是描述性可视化，并非可分性证明。

---

## Slide 13 · Conclusions — Takeaways and outlook（~50s｜累计 11:05）

**English**  
To conclude, CARE contributes a simple but useful principle: use external semantics as a continuous reference, not merely as an initialization. Frozen prototypes help constrain the visual representation, while the EMA teacher, confidence selection and class-balanced buffer stabilize the decisions. This combination consistently improves offline label-free adaptation, with efficient post-training inference. There are also clear limits. The stability result applies locally to the anchor channel; it does not prove convergence of all training dynamics. Performance also depends on semantic anchor quality and sometimes on available class-level attributes. Natural next directions include verifying anchor reliability and extending the method to open-set or online adaptation.

**中文**  
总结：CARE 贡献一个简单但有用的原则——把外部语义当作持续参考，而不只是初始化。冻结原型约束视觉表征；EMA 教师、置信选择与类别均衡缓冲稳定决策。组合一致提升离线无标签适配，且推理轻量。局限也很清楚：稳定性结果局部作用于锚点通道，不证明全部训练动态收敛；性能也依赖语义锚点质量，有时依赖类级属性。自然下一步：校验锚点可靠性，并扩展到开放集或在线适配。

---

## Slide 14 · Closing — Thank you（~10s｜累计 11:15）

**English**  
Thank you for your attention. Because I am not the author of this paper, if you have further questions, you are welcome to email this address: yujiew@mail.ustc.edu.cn.

**中文**  
感谢聆听。我并非本文作者；若有进一步问题，欢迎发邮件至 yujiew@mail.ustc.edu.cn。

---

## Slide 15 · BACKUP — Full LLM-anchor results（backup｜累计 —）

**English**  
Backup slide. Full LLM-anchor accuracy and MPA table from the paper. Not part of the timed oral presentation. Use only if asked for detailed numbers.

**中文**  
备份页：论文 LLM 锚点协议完整 Accuracy / MPA 表。不属于计时口播，仅在被问到细节时使用。

---

## Slide 16 · BACKUP — Attribute protocol & components（backup｜累计 —）

**English**  
Backup slide. Attribute-anchor protocol results and CUB component comparisons, including ablation and VPT versus full fine-tune and LoRA. Not part of the timed talk.

**中文**  
备份页：属性锚点协议结果与 CUB 组件对比（含消融、VPT 相对全量微调与 LoRA）。不计入口播时长。

---

## Slide 17 · BACKUP — Local stability assumptions（backup｜累计 —）

**English**  
Backup slide. Theorem one analyzes the representation loss channel under smoothness, a local Polyak–Łojasiewicz condition, and bounded bias and variance. It does not cover the full teacher-buffer dynamics.

**中文**  
备份页：定理 1 分析表征损失通道（光滑、局部 PL、偏差与方差有界），不覆盖完整师生–缓冲动态。

---

## 关键数字读法卡

| Item | Say |
|------|-----|
| LLM descriptions / class | ten (10) textual descriptions |
| Datasets | six (6) classification datasets |
| LLM gains | zero point four (0.4) pp on AWA2 → one point five (1.5) on Flowers-102 |
| CUB / SUN / Pets (LLM) | fifty-two point seven percent (52.7%) / sixty-six point nine percent (66.9%) / ninety point two percent (90.2%) |
| CUB attr full CARE | fifty-eight point eight four percent (58.84%) |
| w/o L_rep / L_dec / balance | 57.01 (−1.83) / 57.20 (−1.64) / 57.53 (−1.31) |
| Data efficiency | one hundred percent (100%) → twenty percent (20%) |
