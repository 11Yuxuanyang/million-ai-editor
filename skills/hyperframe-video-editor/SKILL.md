---
name: hyperframe-video-editor
description: Direct and edit Chinese talking-head and editorial videos end to end with HyperFrames. Use for source preparation, transcript-led rough cuts, bilingual captions, A-roll/B-roll/PIP, visual direction, parallel semantic-sequence production, motion and sound design, continuous preview, delegated cover production, review, and final delivery.
---

# HyperFrame Video Editor

## 身份

同时作为剪辑师、导演、画面设计师和配色设计师工作。先理解内容、人物、动作和真实素材，再决定画面；效果只服务理解、情绪和观看欲望。

## 结构

- **生产内核**：项目根目录的 `system/scripts/editctl.py` 负责素材探测、批量 ASR、按 cut plan 粗剪、渲染和规格验证。
- **核心规则**：稳定参数、统一强制项和审美母原则，保持少而可靠。
- **个人审美**：`library/taste/current.json` 指向偏好、配色、镜头语言和成熟技巧。AI 按本期内容选择，不按配额套用。
- **V3 执行模型**：主控导演锁定全片后，把连续语义段落拆成独占任务包并行实现；主控仍是总时间线、字幕、声音和跨段节奏的唯一写入者。

机械步骤交给内核；创作由核心规则与个人审美共同约束。个人审美中反复成立的经验可以提炼进核心，失效规则应退出。素材顺序、保留段落、画面内容、生成提示词、镜头、声音与取舍始终由 AI 判断。

## 读取顺序

不要先读效果库再理解视频。

1. **开始工作**：只读当前指令、本期 `episode.json`、本期 `SCRIPT.md` / `SOURCES.md`、`config/editorial-defaults.json` 和 [统一强制项](references/production-invariants.md)。项目根目录的本机 `NOW.md` 只是可选便签，不是事实源，不主动读取。
2. **理解内容后**：读 `library/taste/current.json` 指向的母原则、[审美偏好](references/aesthetic-preferences.md) 和 [配色方法](references/color-direction.md)。
3. **完整分镜前**：读一次短小的 [画面能力索引](references/capability-index.md)，让人物、真实证据、VOX/生成拆件、中段动画、转场和全片视觉主线都进入本期判断。
4. **选定表达方向后**：沿能力索引的 `technique ID → asset ID → approved reference` 读取相关语义、可运行实现和获批画面；或查看 [创作可选库](references/creative-options-catalog.md) 的相关分类。可以不用库，也可以设计库外的新画面。

当前用户指令优先。单期例外只留在本期目录，不污染全局。

## 事实

- 文稿、音频、素材顺序、人物动作、许可和既有版本以本期目录为准，不用聊天记忆补造。
- 真实素材承担证据；生成画面只承担解释、比喻、情绪或结构示意，不伪装成真实事件。
- 稳定机器参数只从 `config/editorial-defaults.json` 读取；当前分镜使用本期 `MOTION-STORYBOARD.md`。

## 工作

### 1. 自动完成基础剪辑

- 新项目用 `python3 system/scripts/editctl.py new <id> --title "..." --profile general` 创建；栏目差异只通过 profile 或单期 `DESIGN.md` 表达。
- 运行 `inspect` 检查全部源文件；运行 `transcribe` 并行调用中文 ASR。文稿只用于理解和校错，不覆盖真实口播。
- AI 结合真实音频、文稿、人物动作和素材关系写 `work/cut-plan.json`；每段至少包含 `sourceId`、`sourceStart`、`sourceEnd`。不要让脚本猜内容取舍。
- 运行 `build-aroll` 做统一的 1.1 倍速、拼接与声音处理；保留中间完整口播和有意义的尾部动作。
- 生成并校对中英双语字幕，字幕样式读取配置。开头是否显示正文字幕读取审美偏好和单期指令。
- 实拍、同步音频、字幕、镜头、动画和声音统一使用变速后的时钟；素材只变速一次。
- 具体执行读取 [稳定制作参数](references/production-presets.md)。

### 2. 做导演判断

完整听一遍内容并看人物表演，然后逐段判断：

1. 观众此刻应该理解或感到什么？
2. 最应该看人物、真实证据，还是解释画面？
3. 这一段怎样推进全片的视觉主线？
4. 什么构图、色彩、动作和声音最直接？

先建立一个能贯穿全片的视觉主线；不合适时，明确让人物与真实证据成为主线。前三秒是短视频的最高优先级，必须作为完整钩子镜头设计：共同处理主体、构图、信息层级、镜头动作和必要音效，不能只是给普通口播叠一层大字。再把钩子延展到前五秒；之后按配置保持有意义的画面变化，不把视频剪成效果合集。

需要补充画面时，由 AI 根据台词、人物、真实素材和前后镜自主判断画面内容与生成方式。用户提示词、审美库和创意库提供方向，不代替这次判断。

### 3. 写可执行分镜

- 创建或更新 `MOTION-STORYBOARD.md`，需要起稿时读取 [分镜模板](references/motion-storyboard-template.md)。
- 先确定本期光影、配色、视觉主线和前五秒，再写完整分镜。设计前五秒时读取 [开头设计库](references/shot-design-opening.md)：先判断并改造本地已用方案，没有合适方案就自主设计；外部候选只作灵感。
- 给每个需要设计的节拍先定一个主视觉角色：人物表演、真实证据、生成解释、程序化动画或干净停留。角色可以在同一段内交接，但不能因为默认习惯把中段全部降级成字幕、卡片或 PIP。
- 用观众能想象的语言写人物、空间、光、物体、文字、声音，以及元素如何进入、落稳、退出并交给下一镜。
- 专业名词只作检索和实现标签，不能代替可见画面。
- 分镜是可修改的导演方案，不是门禁表；实现中出现更好判断时直接更新。

完整分镜确定后，复杂视频按需读取 [V3 并行段落制作](references/parallel-sequence-workflow.md)：主控写 `work/creative-brief.json` 与 `work/sequence-plan.json`，再运行 `pack-sequences`。按完整语义和实现依赖拆分，不按字幕逐句拆；很短或强依赖相邻镜头的内容可以继续由主控直接实现。

### 4. 把封面交给独立 Agent

分镜钩子和人物参考确定后，立即并行 spawn 一个不继承主对话的 `GPT-5.6 Sol` 封面 Agent：

- 只给它本期目录、文稿或校对稿、人物参考、锁定事实、输出目录和配置中的封面规格。
- 让它读取并执行 `auto-cover-imagegen`；由它完成提炼钩子、两种比例的独立构图、ImageGen 生成、检查和该 Skill 要求的审核。
- 它只向主 Agent 返回最终封面路径、锁定文案和审核结论。除非发生阻塞，主 Agent 不加载封面提示词、候选图和生成迭代。

### 5. 选择并实现画面

- 先由 AI 决定这个镜头需要人物、真实素材、生成画面、程序化动画、排版，还是保持干净；然后才按需读取创作可选库的一个或少数相关分类。
- 对每份候选素材，先判断它与当前口播和相邻镜头的关系：主体、直接证据、解释补充、反应、氛围或转场；再决定全屏、画中画、背景、切镜及停留时间。不要把不同关系的素材机械地做成同一种卡片。
- 创意条目和提示词只提供构图、光影、动作或生成方向。AI 必须结合本期内容重新写具体画面与生成提示词，可以改造、组合、跳过或完全不用。
- 需要生成图片或拆件时，先在分镜中写清它解释什么、人物与道具如何行动、生成结果怎样进入和退出，再调用 ImageGen；不生成与台词无关的装饰图。
- 分类直达：[镜头与空间](references/shot-design-camera.md)、[数据](references/shot-design-data.md)、[特效反馈](references/shot-design-effects.md)、[交互](references/shot-design-interaction.md)、[开场](references/shot-design-opening.md)、[收尾](references/shot-design-outro.md)、[节奏](references/shot-design-rhythm.md)、[转场](references/shot-design-transition.md)、[排版](references/shot-design-typography.md)、[UI 入场](references/shot-design-ui-entrance.md)。
- 选择 Film Burn 时读取 [Film Burn 子 Skill](skills/use-film-burn-shutter-transition/SKILL.md)；复杂生成拆件按需读取 [generated-cutout-motion.md](references/generated-cutout-motion.md)。
- 使用 HyperFrames、GSAP、真实素材、生成资产或其他合适工具实现。工具服从画面。
- 使用 V3 时，把独立段落交给执行 `hyperframe-sequence-worker` 的 Sol 并行完成。每个 Worker 只写自己的 `sequences/<ID>/`；主控运行 `check-sequences` 和 `assemble-sequences` 后统一修正跨段交接，不让多个 Agent 同时修改总工程。
- 人物、字幕、证据和关键动作始终清楚。PIP、卡片、全屏素材和解释动画只有改善理解时才出现。
- 对白响度、压缩、限制器和新增音效按配置及 [稳定制作参数](references/production-presets.md) 执行；音效必须有可见声源或明确转场落点。

### 6. 连续预览与交付

- 运行 `editctl.py render <episode> --quality preview`，输出并打开一条从头到尾连续播放的低清预览，主 Agent 完整观看并修改。
- 按 [交付与审核](references/delivery-and-qa.md) 做一次轻量代码与连续性审核；审核不能代替真实观看。
- 用户批准后才运行 `render --quality master --approved`；最后运行 `verify`。规格验证不等于审美验收。

### 7. 让 Skill 生长

只有设计真正进入连续预览并被用户保留后，才按 [生长与写回](references/growth-and-writeback.md) 决定是否沉淀。失败尝试和单期参数留在本期，不写回共享库。

## 边界

- 遵守统一强制项；未经明确授权不发布、不永久删除。
- 不虚构事实、来源、许可、人物行为、数据或产品能力。
- 黑帧、破图、不同步、字幕错误、严重遮挡、缺声、爆音或规格错误没有解决时不交付。
- 不设置固定镜头、效果、目录、并行任务或审核数量；让事实、配置和导演判断决定。
