# -*- coding: utf-8 -*-
"""Bilingual speaker notes for SpaCon PPT (~10 min oral + 3 min Q&A)."""

# Target: ~10:00 speaking @ ~125–130 wpm while pointing at slides (~1250–1350 EN words)

SLIDE_NOTES = [
    # Slide 1 — Title (~20s)  cumulative 0:20
    {
        "timing": "~20s",
        "cumulative": "0:20",
        "section": "Opening",
        "en": (
            "Good morning, everyone. My name is Shiqi Shi, from Wuhan University of Science and Technology. "
            "It's my pleasure to present our work, SpaCon: Spatial Complementary Consistency for "
            "Semi-Supervised Medical Image Segmentation. This work is co-authored with Zhengshi Chen "
            "and Juanjuan He. I'll keep the talk to about ten minutes, and then we can move to Q&A."
        ),
        "zh": (
            "各位老师、各位同学，早上好。我是武汉科技大学的石诗淇。"
            "今天很荣幸汇报我们的工作 SpaCon：面向半监督医学图像分割的空间互补一致性方法。"
            "本工作由我和陈郑石、何娟娟老师共同完成。讲解大约十分钟，随后进入答辩环节。"
        ),
    },
    # Slide 2 — TOC (~15s)  cumulative 0:35
    {
        "timing": "~15s",
        "cumulative": "0:35",
        "section": "Agenda",
        "en": (
            "Here is the roadmap for today. I'll briefly cover the research background, "
            "then our hypothesis and objectives, the SpaCon methodology, the main experimental results, "
            "and finally discussion with next steps."
        ),
        "zh": (
            "今天的路线如下：研究背景、假设与目标、SpaCon 方法、主要实验结果，以及讨论与下一步工作。"
        ),
    },
    # Slide 3 — Background (~65s)  cumulative 1:40
    {
        "timing": "~65s",
        "cumulative": "1:40",
        "section": "I · Background",
        "en": (
            "Let me start with the problem. Medical image segmentation is a fundamental task for clinical "
            "diagnosis, surgical planning, and quantitative analysis. Deep learning, especially U-Net style "
            "architectures, has significantly improved segmentation accuracy. However, dense pixel-level "
            "annotation remains prohibitively expensive and heavily relies on scarce domain expertise. "
            "Semi-supervised learning is therefore a natural solution: we jointly use a small labeled set "
            "and a large unlabeled set to reduce annotation cost.\n\n"
            "Among recent advances, two paradigms stand out. One is cross-image mixing, represented by "
            "methods such as BCP. The other is masked image modeling. Both improve overall performance, "
            "but they also reduce the integrity of the input. Conventional masking discards vital spatial "
            "regions. Cross-image region replacement, together with rigid grid boundaries, disrupts the "
            "semantic continuity of anatomical structures. So the open challenge is clear: can we exploit "
            "unlabeled data while preserving spatial completeness and continuous anatomical boundaries?"
        ),
        "zh": (
            "先从问题说起。医学图像分割是临床诊断、手术规划和定量分析的基础任务。深度学习，尤其是 U-Net，"
            "显著提升了精度，但像素级标注昂贵，且高度依赖稀缺专科经验。半监督因此很自然：少量有标签加大量无标签一起训练。\n\n"
            "近年两条路线很有代表性：跨图像混合（如 BCP）和掩码图像建模。它们提升了整体性能，却削弱了输入完整性——"
            "传统掩码丢掉关键空间区域；跨图像替换加上硬网格边界，会打断解剖结构的语义连续性。"
            "核心挑战是：利用无标签数据时，能否同时保住空间完整性与连续的解剖边界？"
        ),
    },
    # Slide 4 — Hypothesis (~35s)  cumulative 2:15
    {
        "timing": "~35s",
        "cumulative": "2:15",
        "section": "II · Hypothesis",
        "en": (
            "This leads to our testable claim. We hypothesize that by using complementary masks to retain "
            "complete information—instead of scrambling or discarding it—we can maximize spatial information "
            "utilization and achieve significantly more accurate and continuous anatomical segmentation. "
            "In one sentence: we split each unlabeled image into two complementary views that teach each other, "
            "yet together they still cover the full image with no pixel loss."
        ),
        "zh": (
            "由此提出可验证假设：用互补掩码保留完整信息，而不是打乱或丢弃信息，"
            "就能最大化空间信息利用，得到更准确、更连续的解剖分割。"
            "一句话：把无标签图分成两个互补视图互相教学，合起来仍覆盖整图、像素不丢。"
        ),
    },
    # Slide 5 — Core innovation (~50s)  cumulative 3:05
    {
        "timing": "~50s",
        "cumulative": "3:05",
        "section": "II · SpaCon / CMC",
        "en": (
            "Based on this idea, we propose SpaCon. Inspired by masked autoencoders, covering random regions "
            "can force the model to predict the masked area, produce higher-quality pseudo-labels, and help "
            "alleviate edge artifacts and under-used spatial context in mixing-based methods like BCP. "
            "But unlike conventional masking, we do not throw pixels away. We introduce spatial complementary masking.\n\n"
            "Through the CMC module—Complementary Mask Consistency—each unlabeled image is partitioned into "
            "two fully complementary spatial views and fed into the student for mutual pseudo-label supervision. "
            "To further improve boundary processing, we design Smooth Complementary Mask, or SCM, which creates "
            "a continuous transition zone so that boundary pixels receive weighted supervision from both views "
            "at the same time."
        ),
        "zh": (
            "据此提出 SpaCon。受 MAE 启发，随机遮挡可逼模型预测被盖区域、生成更高质量伪标签，"
            "也有助于缓解 BCP 一类方法的边缘伪影与空间利用不足。但与传统掩码不同，我们不丢像素，而是做空间互补掩码。\n\n"
            "CMC（互补掩码一致性）把每张无标签图分成两个完全互补的空间视图，送入学生做双向伪标签互监督。"
            "为进一步改善边界，我们设计 SCM（平滑互补掩码），在边缘形成连续过渡带，"
            "让边界像素同时接受来自两路视图的加权监督。"
        ),
    },
    # Slide 6 — Objectives (~40s)  cumulative 3:45
    {
        "timing": "~40s",
        "cumulative": "3:45",
        "section": "II · Objectives",
        "en": (
            "Concretely, we pursue three objectives. First, propose the SpaCon framework as a lightweight "
            "local refinement module that bridges the gap between macro-level cross-image mixing and "
            "micro-level structural integrity. Second, introduce the CMC branch with a bidirectional "
            "blind-spot mechanism, so all pixel features are retained and complementary regions teach "
            "each other without information loss. Third, design the SCM algorithm to replace hard binary "
            "grid partitions with continuous-valued transition zones, smoothing gradients and eliminating "
            "grid artifacts—without introducing any extra learnable parameters."
        ),
        "zh": (
            "具体有三个目标。第一，提出 SpaCon 框架：轻量局部精炼模块，桥接宏观跨图混合与微观结构完整性。"
            "第二，引入 CMC 分支：双向盲区机制保留全部像素特征，互补区域互教学、信息不丢。"
            "第三，设计 SCM：用连续取值过渡带替换硬二值网格，平滑梯度、消除网格伪影，且不增加任何可学习参数。"
        ),
    },
    # Slide 7 — Methodology (~85s)  cumulative 5:10
    {
        "timing": "~85s",
        "cumulative": "5:10",
        "section": "III · Methods",
        "en": (
            "Now let's look at the study design. As shown in the figure, SpaCon consists of two branches "
            "that share one student network and one EMA teacher network.\n\n"
            "On the left, the BCP branch performs macro-level distribution alignment through bidirectional "
            "cross-image mixing between labeled and unlabeled samples. On the right, the CMC branch performs "
            "micro-level intra-image refinement with complementary masked views. Within CMC, SCM further "
            "smooths mask boundaries to reduce grid artifacts. Both branches optimize through the same "
            "shared teacher and the same teacher pseudo-labels.\n\n"
            "For CMC specifically: unlabeled images are partitioned into a regular grid to create two "
            "spatially complementary views. Early in training, a shared block ratio provides overlapping "
            "context so each view still sees enough of the image; this ratio then decays linearly toward "
            "strict spatial orthogonality—from about 0.4 down to zero over the first five thousand steps. "
            "A bidirectional blind-spot mechanism then lets each view supervise the invisible pixels of "
            "its complement, fully exploiting global context. We apply a stop-gradient operator to avoid "
            "the trivial collapse of both views to identical predictions."
        ),
        "zh": (
            "接下来看方法设计。如图所示，SpaCon 包含两条分支，共用一个学生网络和一个 EMA 教师网络。\n\n"
            "左侧 BCP 分支通过有标签与无标签之间的双向跨图混合，做宏观分布对齐；"
            "右侧 CMC 分支用互补掩码视图做微观图内精炼；其中 SCM 进一步平滑掩码边界、削弱网格伪影。"
            "两条分支通过同一教师与同一伪标签联合优化。\n\n"
            "CMC 具体流程：无标签图按规则网格分成两个空间互补视图。"
            "训练早期用共享块比例保留重叠上下文，再线性衰减到严格正交——约从 0.4 降到 0，前五千步完成。"
            "双向盲区机制让每路监督互补区域中看不见的像素，充分利用全局上下文；"
            "并加 stop-gradient，避免两路塌缩成相同预测。"
        ),
    },
    # Slide 8 — SCM advanced (~55s)  cumulative 6:05
    {
        "timing": "~55s",
        "cumulative": "6:05",
        "section": "III · SCM",
        "en": (
            "Let me highlight the SCM design in three short phases.\n\n"
            "Phase one, motivation: hard binary masks create an abrupt jump from zero to one at every "
            "grid-block edge. Boundary pixels are assigned to only one view and systematically excluded "
            "from the other view's gradient—along a grid-aligned stripe that does not correspond to any "
            "anatomical boundary.\n\n"
            "Phase two, pipeline: SCM replaces nearest-neighbor upsampling with bilinear interpolation "
            "followed by average pooling. This produces a continuous-valued transition zone. With sigma "
            "equal to 0.3 and block size eight, the soft band is roughly one to two pixels wide.\n\n"
            "Phase three, outcome: boundary pixels receive soft supervision from both views simultaneously, "
            "which encourages highly consistent anatomical boundaries."
        ),
        "zh": (
            "SCM 设计分三步说明。\n\n"
            "动机：硬二值掩码在每个网格块边缘从 0 直接跳到 1，边界像素只分给一边，"
            "另一边系统性拿不到梯度——这条网格断裂线并不对应任何解剖边界。\n\n"
            "流程：SCM 用双线性插值加平均池化替代最近邻上采样，形成连续取值过渡带；"
            "σ=0.3、块大小 8 时，软边界大约一到两个像素宽。\n\n"
            "结果：边界像素同时接受两路软监督，解剖边界更一致、更连贯。"
        ),
    },
    # Slide 9 — ACDC SOTA (~50s)  cumulative 6:55
    {
        "timing": "~50s",
        "cumulative": "6:55",
        "section": "IV · ACDC",
        "en": (
            "Turning to results. On the ACDC cardiac MRI dataset with seven labeled cases—about ten percent "
            "annotation—SpaCon achieves a Dice score of 90.31 percent, an HD95 of 1.32 millimeters, and an "
            "ASD of 0.46 millimeters. Compared with our reproduced BCP baseline, this is roughly a 1.2-point "
            "Dice gain and a 1.73-millimeter improvement in HD95.\n\n"
            "With only three labeled cases, SpaCon still reaches 89.33 percent Dice and 1.37 millimeters HD95, "
            "outperforming the baseline by 2.83 points and nearly matching the seven-case accuracy. "
            "This suggests that intra-image complementary supervision is especially valuable when labels are scarce."
        ),
        "zh": (
            "看实验结果。ACDC 心脏 MRI、七例有标签（约 10% 标注）下，SpaCon 达到 Dice 90.31%、"
            "HD95 1.32 毫米、ASD 0.46 毫米；相对我们复现的 BCP 基线，约提升 1.2 个百分点 Dice，"
            "HD95 改善约 1.73 毫米。\n\n"
            "仅三例有标签时，仍达 Dice 89.33%、HD95 1.37 毫米，比基线高 2.83 个百分点，已接近七例水平。"
            "说明标注越稀缺，图内互补自监督越有价值。"
        ),
    },
    # Slide 10 — Qualitative / LA (~45s)  cumulative 7:40
    {
        "timing": "~45s",
        "cumulative": "7:40",
        "section": "IV · Qualitative",
        "en": (
            "Beyond the numbers, the qualitative comparisons tell the same story. On ACDC, SpaCon produces "
            "sharper and more complete segmentation boundaries than MT, MC-Net, UA-MT, and BCP, which is "
            "consistent with the 1.73-millimeter HD95 gain over the reproduced baseline.\n\n"
            "On the left-atrium LA dataset with eight labeled cases, SpaCon yields more continuous boundaries, "
            "aligning with about a 0.69-millimeter HD95 improvement, and reaches 90.30 percent Dice. "
            "So the benefit transfers from 2D cardiac MRI to 3D left-atrium segmentation."
        ),
        "zh": (
            "定性结果与数字一致。ACDC 上，SpaCon 的边界比 MT、MC-Net、UA-MT、BCP 更锐利、更完整，"
            "与相对复现基线 HD95 改善 1.73 毫米相符。\n\n"
            "左心房 LA 数据集、八例有标签设置下，SpaCon 边界更连续，对应 HD95 约改善 0.69 毫米，"
            "Dice 达到 90.30%。收益从二维心脏 MRI 迁移到三维左心房分割。"
        ),
    },
    # Slide 11 — Pancreas + ablation (~55s)  cumulative 8:35
    {
        "timing": "~55s",
        "cumulative": "8:35",
        "section": "IV · Ablation",
        "en": (
            "We further evaluate generalization on NIH Pancreas CT. Under the ten-percent labeled setting, "
            "SpaCon reaches 82.54 percent Dice—three percentage points above the reproduced baseline—"
            "with clear reductions in HD95 as well. The larger gain at ten percent than at twenty percent "
            "again indicates that intra-image self-supervision helps most when labeled data is limited.\n\n"
            "The component ablation on ACDC with seven cases makes the roles clear. BCP alone gives "
            "89.11 Dice and 3.05 HD95. CMC alone can raise Dice but worsens HD95, showing that mutual "
            "teaching needs a stable macro prior. BCP plus hard-mask CMC improves Dice, yet boundaries "
            "remain weak. Adding SCM finally reaches 90.31 Dice and 1.32 HD95. In short: BCP aligns "
            "distributions, CMC refines inside the image, and SCM removes boundary artifacts."
        ),
        "zh": (
            "我们在 NIH Pancreas CT 上进一步验证泛化。10% 标注下，SpaCon 达到 Dice 82.54%，"
            "相对复现基线提升 3 个百分点，HD95 同步下降。10% 设置的提升大于 20%，再次说明标注越少，图内自监督越有用。\n\n"
            "ACDC 七例组件消融角色清晰：仅 BCP 为 89.11 / 3.05；仅 CMC 可抬 Dice 但 HD95 变差，说明互教学需要宏观先验；"
            "BCP+硬掩码 CMC 改善 Dice，边界仍弱；加上 SCM 达到 90.31 / 1.32。"
            "简言之：BCP 对齐分布，CMC 做图内精炼，SCM 消除边界伪影。"
        ),
    },
    # Slide 12 — Discussion (~40s)  cumulative 9:15
    {
        "timing": "~40s",
        "cumulative": "9:15",
        "section": "V · Discussion",
        "en": (
            "What does this mean for the field? SpaCon shows that micro-level intra-image supervision "
            "complements macro-level cross-image distribution alignment. Together they produce sharper, "
            "more anatomically correct boundaries. It also works as a practical plug-and-play enhancement: "
            "we reuse the teacher network with minimal overhead and no additional learnable parameters.\n\n"
            "There are two main limitations. First, fixed grid orientations and uniform SCM transition widths "
            "may occasionally blur high-frequency anatomical details. Second, as a local refinement module, "
            "CMC currently relies on macro-level alignment from a baseline such as BCP to stay stable early in training."
        ),
        "zh": (
            "对领域的意义：SpaCon 说明微观图内监督可以很好地补上宏观跨图分布对齐；两者结合，边界更锐、更符合解剖。"
            "同时它是实用的即插即用增强：复用教师网络，几乎零额外开销，不增加可学习参数。\n\n"
            "两点主要局限：一是网格方向与 SCM 过渡宽度固定，复杂高频解剖细节偶尔会被抹平；"
            "二是作为局部精炼模块，CMC 早期仍依赖 BCP 一类宏观对齐基线来稳住训练。"
        ),
    },
    # Slide 13 — Future (~30s)  cumulative 9:45
    {
        "timing": "~30s",
        "cumulative": "9:45",
        "section": "V · Future",
        "en": (
            "For future work, we plan three directions. First, uncertainty-guided adaptive boundary sampling "
            "to strengthen standalone capability and reduce dependence on external baselines. Second, "
            "anatomy-aware transition widths tailored to local edge sharpness, so we do not blur fine details. "
            "Third, cross-slice continuity regularization to better adapt SpaCon to complex 3D volumetric scans."
        ),
        "zh": (
            "未来三个方向：一是不确定性引导的自适应边界采样，增强独立能力、降低对外部基线依赖；"
            "二是解剖感知过渡宽度，按局部边缘锐度调节，避免抹掉细结构；"
            "三是跨切片连续性约束，更好适配复杂三维体数据。"
        ),
    },
    # Slide 14 — Thank you (~15s)  cumulative 10:00
    {
        "timing": "~15s",
        "cumulative": "10:00",
        "section": "Closing",
        "en": (
            "That concludes my presentation. Thank you very much for your attention. "
            "Our code is available on GitHub, and I'd be happy to take your questions."
        ),
        "zh": (
            "以上是我今天的汇报。非常感谢各位聆听。代码已开源在 GitHub，欢迎提问。"
        ),
    },
]


def format_notes(item: dict) -> str:
    return (
        f"【时长 Timing】{item['timing']}  |  【累计 Cumulative】{item['cumulative']}  |  {item['section']}\n"
        f"{'=' * 56}\n"
        f"【English — speak this】\n"
        f"{item['en']}\n"
        f"\n"
        f"{'-' * 56}\n"
        f"【中文对照】\n"
        f"{item['zh']}\n"
    )
