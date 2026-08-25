# 画面能力索引

在理解本期内容、人物表演和素材关系之后，写完整分镜之前读一次。本页只让新任务知道系统已经会什么，不是效果菜单、镜头配额或固定流程。

先判断这一拍的主要任务，再选择一种主视觉角色；没有合适能力时直接设计新画面。

| 表达任务 | 可以怎样看见 | 可执行指针 | 深入读取 |
| --- | --- | --- | --- |
| 人物本身最有力量 | 保留完整表演；在重音处做长尾推近、拉远或回推，落位后保持；镜头、展示字和声音共同强调一个重点。 | `technique.camera.long-tail-scale-hold` → `motion.camera.long-tail-scale.v1` | [剪辑与镜头](creative-options-catalog.md#剪辑与表演-editing--performance)、[镜头语言](../../../references/SHOT-LANGUAGE.md) |
| 前三秒需要反常识揭示 | 人物一直在场；先让惯性答案出现并退后，再用长尾拉远和人物前后景大字揭示真正主题。 | `technique.opening.counterclaim-subject-reveal` | [获批开头参考](../../../library/references/reference.opening.boss-content-memory.v1/reference.yaml) |
| 用真实材料证明台词 | 证据在对应名词响起时接管画面；可全屏成立后缩入安全 PIP、逐词交接或短促快闪。 | `technique.evidence.cue-locked-handoff`、`technique.evidence.fullframe-to-pip-handoff` | [证据剪辑](creative-options-catalog.md#证据剪辑与蒙太奇-evidence-editing--montage)、[获批参考](../../../library/references/reference.person-evidence.scatter-to-proof.v1/reference.yaml) |
| 多份材料围绕人物建立关系 | 页面从人物身后共轴扇开，或以人物为中心形成带倾角、深度和遮挡关系的卡片弧；不平铺。 | `technique.composition.shared-pivot-page-fan` → `motion.composition.shared-pivot-page-fan.v1` | [空间合成](creative-options-catalog.md#构图与空间合成-composition--spatial-compositing) |
| 口播需要具象比喻、人物互动或幽默解释 | 用 ImageGen 生成本句专属人物、物体和场景拆件，再抠图、补全并做 setup → action → result；VOX 不是静态生图。 | `technique.generated.vox-cutout-motion` → `motion.generated.cutout-sequence.v1` | [生成拆件与 VOX](generated-cutout-motion.md)、[获批人物示例](../../../library/references/reference.generated.vox-two-presenter.v1/reference.yaml) |
| 中段需要解释系统、流程、产品或代码 | 使用遮罩揭示、容器变形、焦点交接、微交互、数字变化或持续演化的母图；人物和真实证据仍可作空间锚点。 | `transition.container-morph.v1`、`motion.composition.presenter-card-orbit.v1` | [UI 与解释动画](creative-options-catalog.md#ui-与解释动画-ui--explainer-motion) |
| 资料从散乱变成可调用资产 | 让同一批真实材料经历“散落 → 归档 → 调用”，每次变化对应口播中的一步，而不是另起 PPT。 | `technique.system.scatter-index-retrieve` → `motion.system.scatter-index-retrieve.v1` | [视觉结构](creative-options-catalog.md#全片视觉结构-visual-system) |
| 章节需要黑场中的结构化过渡 | 可选缓慢完整的动态等高线，或只在转场存在的动态点线场；文字在结构形成后出现。 | `technique.transition.contour-flow-bridge`、`technique.transition.dynamic-line-dot-blackout` | [程序化动效](creative-options-catalog.md#程序化抽象动效-procedural-motion-graphics) |
| 两镜需要短促的电影化接缝 | 可用像素重组、曝光闪切、漏光或 Film Burn；根据前后镜形状、亮度、动作和语义选择。 | `technique.transition.pixel-resolve`、`transition.exposure-flash.v1`、`transition.film-burn-screen-composite.v1` | [转场](creative-options-catalog.md#转场-transitions)、[转场镜头库](shot-design-transition.md) |
| 全片容易散 | 先建立会随章节演化的视觉主线，例如同一套资料、路径、组织系统或母图；到对应台词只改变焦点和结构。 | 可从 `technique.system.scatter-index-retrieve` 改造，也可新设计 | [视觉结构](creative-options-catalog.md#全片视觉结构-visual-system) |

## 选择原则

- 事实优先使用真实证据；生成画面只解释、比喻、营造情绪或展示结构。
- 一拍只保留一个主要动作，但同一段可以让人物、证据和动画依次交接。
- 先决定画面要说明什么，再决定使用已沉淀能力、改造它，还是创造新方法。
- 选中能力后按 `technique ID → asset ID → reference` 只读取相关实现和获批画面；未选中的分支不加载。
- 音效只和可见动作、镜头落点或转场峰值绑定；没有明确落点就保持干净。
