# 创作可选库

只在已经理解内容、并遇到具体表达问题后打开本页。它是一组供 AI 参考的提示词方向，不是现成画面菜单、开工必读清单或固定配额。

AI 先自主判断当前镜头应该生成或组织什么画面，再看本地已验证的表达方法；仍缺启发时才进入外部分类。所有名称只帮助提示构图、光影、空间和动作，不能直接成为结果。可以改变、组合、跳过，也可以设计库外的新画面。

## 剪辑与表演 Editing & Performance

| 选项 | 最简单的描述 | 适合哪里 | 过去用在哪里 |
| --- | --- | --- | --- |
| **Clean Performance Hold（完整表演停留）** | 清掉额外效果，让人物的一句台词、动作或反应完整成立。 | 玩笑、情绪、互动和有价值的动作尾巴。 | 百万计划第三期 Round 04 `24.20–31.07`。 |
| **J-Cut / L-Cut（声音先行 / 延后）** | 下一镜声音先来，或上一镜声音继续留在新画面上。 | 让场景自然衔接、提前建立下一段信息。 | 暂无单独登记的案例。 |
| **Motivated Hard Cut（有动机硬切）** | 在台词重音、动作落点或观点变化处直接切镜。 | 不需要转场、直接切更有力量时。 | 多期人物与真实素材交接。 |

## 动态排版 Kinetic Typography

| 画面 | 最简单的描述 | 适合哪里 | 过去用在哪里 |
| --- | --- | --- | --- |
| **Semantic Rise（语义上升）** | 几组词随着语气从下方升起，最后组成一句完整主张。 | 开头钩子、压力逐步增加的一句话。 | `hf-0728-ai-news-opening-sample@v24-r2` 开场。 |
| **Side Fade（侧向淡入）** | 一个短词从侧边滑入并变清楚。 | 补充名词、工具名、人物旁边的短标签。 | `hf-0728-ai-news-opening-sample@v24-r2`。 |
| **Quiet Fade（安静淡入）** | 文字几乎不移动，只轻轻出现并停住。 | 反思、结论、情绪变安静的句子。 | `hf-0728-ai-news-opening-sample@v24-r2`。 |
| **Brush-Accent Display Type（画笔强调字）** | 画笔线划过关键词，带出改写或转折。 | “从 A 变成 B”、划重点、纠正旧概念。 | 百万计划第三期 Round 04 `46.38–49.65`，“运营 → 公司架构师”。 |
| **Impact Word（冲击重音字）** | 一个词快速变大落位，马上稳定。 | 开头重音、数字、否定词、短促结论。 | 已有 GSAP 实现原语；暂无单独登记的成片案例。 |

实现入口：`assets/opening-display-type/approved-style-v1.json` 保存已认可但可调整的字形基准；`assets/opening-display-type/gsap-patterns.js` 保存参数化运动原语；每期按 `assets/opening-display-type/display-events.example.json` 在视频目录另建 `display-type.json`，重新决定文案分组、布局、时点、运动参数和声音。不要复制旧期完整时间线。也可使用 `hyperframe-cinematic-templates`。

## 证据剪辑与蒙太奇 Evidence Editing & Montage

| 画面 | 最简单的描述 | 适合哪里 | 过去用在哪里 |
| --- | --- | --- | --- |
| **Symmetric Evidence Tableau（对称证据阵列）** | 真实素材从左右聚到人物周围，人物保持中心。 | 多个工具或案例共同证明一件事。 | `hf-0728-ai-news-opening-sample@v24-r2`。 |
| **Three-Card Spread（三卡展开）** | 三张真实证据从中间展开，最后并排落住。 | 三个例子共同导向一个结果。 | `hf-0728-ai-news-opening-sample@v24-r2`。 |
| **Quick-Flash Evidence Montage（证据快闪蒙太奇）** | 多张真实素材短促快速切换，压缩成一组证据。 | 新闻、产品、案例、人物或网页的密集列举。 | `hf-0728-ai-news-opening-sample` 的证据快闪段。 |
| **Cue-Locked Evidence Handoff（逐词证据交接）** | 真实素材只在旁白说到对应人物、载体或动作时接管画面，再把注意力交还人物或下一份证据。 | 语音、聊天、团队工作、产品页面等需要建立可信度的具体陈述。 | 与君 AI《老板内容记忆》正式获批版。 |
| **Full-Frame to PIP Handoff（全屏证据缩入画中画）** | 先让真实素材全屏成立；叙事转回人物时，同一素材缩入人脸安全区的小窗继续承接上下文。 | 既要看清真实动作，又要恢复讲述者连续性的段落。 | 与君 AI《老板内容记忆》“内容团队 → 等老板解释”。 |

实现入口：项目 `library/techniques/registry.json`、`hyperframe-cinematic-templates`。

## 构图与空间合成 Composition & Spatial Compositing

| 画面 | 最简单的描述 | 适合哪里 | 过去用在哪里 |
| --- | --- | --- | --- |
| **Presenter-Centered 3D Card Orbit（人物中心卡片环绕）** | 2–5 张卡片在人物周围形成有纵深的浅弧。 | 围绕一个人讲多个并列选项、产品或角色。 | 百万计划第三期 Round 04 `37.08s` 附近。 |
| **Shared-Pivot 3D Page Fan（共轴页面扇开）** | 多张真实页面从人物身后沿同一个底部轴展开。 | 展示资源、案例、文档或作品积累。 | 百万计划第三期 Round 04 `32.12–36.98` 的真实素材纸片。 |
| **Radial 3D Card Wall（放射式卡片墙）** | 卡片从人物或中心主题向两侧放射，前后错开。 | 数量较多但仍需要围绕一个中心关系时。 | 已进入项目镜头语言；暂无登记的正式案例。 |

实现入口：`hyperframe-cinematic-templates`、项目 `references/SHOT-LANGUAGE.md`。

## 镜头运动与焦点 Camera & Focus

| 画面 | 最简单的描述 | 适合哪里 | 过去用在哪里 |
| --- | --- | --- | --- |
| **Evidence Push（证据推进）** | 先看完整证据，再轻推到真正要看的位置。 | 网页、文章、产品图、文件中的关键细节。 | `hf-0728-ai-news-opening-sample@v24-r2`。 |
| **Snap Pull-back（快速拉远）** | 镜头快速拉开并慢慢落稳，露出更完整的关系。 | 从人物重音扩展到环境、数字或全局结构。 | 百万计划第三期 Round 04 开头 `00.00–01.55`。 |
| **Pull-back to Rebound Push-in（拉远后回推）** | 先拉远落稳建立空间，再在后续重点词上快起慢收地推回人物或目标；展示字与第二个 whoosh 同拍落下。 | 一个镜头内先扩展关系、再把注意力收回关键结论；回推后保持，不自动弹回。 | 用户确认的可选组合，等待正式成片案例。 |
| **Focus Flash Cuts（聚焦快切）** | 多个真实整页快速切换，浅景深只让目标原文清楚。 | 多个网页反复证明同一个问题；使用权限读取审美偏好。 | `hf-0728-ai-news-opening-sample` v8–v10 证据段。 |

实现入口：项目 `library/techniques/registry.json`、`hyperframe-editorial-explainer/references/focus-flash-cuts.md`。

## UI 与解释动画 UI & Explainer Motion

| 画面 | 最简单的描述 | 适合哪里 | 过去用在哪里 |
| --- | --- | --- | --- |
| **Masked Code Reveal（遮罩代码揭示）** | 代码窗口沿一个方向打开，内容按顺序出现。 | 从真人进入代码、产品界面或可执行系统。 | `hf-0728-ai-news-opening-sample@v24-r2`。 |

实现入口：项目 `library/techniques/registry.json`、`assets/opening-display-type/gsap-patterns.js`。

## 程序化抽象动效 Procedural Motion Graphics

| 选项 | 最简单的描述 | 适合哪里 | 过去用在哪里 |
| --- | --- | --- | --- |
| **Dynamic Point-Line Field（动态点线场）** | 纯黑转场里，点先漂入，必要时连接线依次亮起，文字在关系形成后出现；换章完成后点场退出。 | 网络、协作、系统或 AI 节点主题的章节接缝；不作为正文人物画面的常驻装饰。 | 百万计划第三期 `assets/transition-native/dot-grid-blackout.js`。 |
| **Animated Contour Field（动态等高线 / 地形线）** | 纯黑空间里的完整等高线由确定性场生成，在画框外闭合并缓慢漂移；路径显影完成后保持连续，避免边缘裁切和虚线截断。 | 压力、复杂度、地形隐喻、成长路径、层级变化或章节过渡。 | 百万计划第三期 `assets/transition-native/contour-flow.js`。 |

实现入口：项目 `library/techniques/transition-native/`；过去用法留在案例字段，不让共享库依赖旧视频目录。

## 配色与光影 Color & Lighting

| 选项 | 最简单的描述 | 适合哪里 | 过去用在哪里 |
| --- | --- | --- | --- |
| **Four-Role Palette（四色彩角色）** | 先分地色、内容色、结构色和语义强调色，再决定具体颜色。 | 需要整片统一但不想套固定色值时。 | 当前 HyperFrame 配色方法。 |
| **Moving Focus Accent（移动强调色）** | 同一个强调色跟着叙事重点在不同元素间移动。 | 关键词、数字、路径和当前步骤。 | 百万计划第三期 Round 04 的黄色重点。 |
| **Warm–Cool Handoff（冷暖交接）** | 用冷暖关系把注意力或章节从一边交到另一边。 | 人物与证据、问题与结果、现实与解释之间。 | 暂无单独登记的案例。 |
| **Directional Light Handoff（方向光交接）** | 一束看得见方向的光扫过主体，把注意力交给下一元素。 | 素材揭示、标题进入、段落内的视觉接力。 | 开头光学转场研究。 |

## 转场 Transitions

| 画面 | 最简单的描述 | 适合哪里 | 过去用在哪里 |
| --- | --- | --- | --- |
| **Exposure Flash（曝光闪切）** | 画面短暂过曝，在亮度峰值换到下一镜。 | 两个画面需要快速、干净、偏电影感的连接。 | 已有可执行模板；暂无登记的正式案例。 |
| **Film Burn + 轻快门（胶片烧片转场）** | 红橙胶片曝光盖住切点，下一镜从暖色尾光里恢复。 | 需要模拟胶片曝光洗过切点时；具体范围与实现读取子 Skill。 | `youtube-R_tuS9sWJEk-opening-study` `05.36–06.00`。 |

实现入口：`hyperframe-cinematic-templates`、`skills/use-film-burn-shutter-transition/SKILL.md`。

## 声音设计 Sound Design

| 选项 | 最简单的描述 | 适合哪里 | 过去用在哪里 |
| --- | --- | --- | --- |
| **Dry Cut / No SFX（干切 / 无音效）** | 不加音效，让对白、动作和剪切本身成立。 | 人物表演、安静结论、音效会显得多余时。 | 百万计划第三期 Round 04。 |
| **Opening Pull-back Whoosh（片头长尾拉远呼声）** | 一条约 1.1 秒的空气拉远声，与极近人物退回完整构图同起同落。 | `counterclaim-subject-reveal-open` 的反常识判断片头；不用于推近或普通换场。 | `0813-yujun-boss-content-memory` 正式母版；仓库保留方向 `sfx.opening-pullback-whoosh.direction.v1`，单期另选有许可音源。 |
| **Soft Air Whoosh（轻空气划过）** | 用很轻的空气声跟随一个看得见的推拉或滑动。 | 镜头推拉、卡片进入、方向明确的移动。 | 暂无单独登记的案例。 |
| **Soft Shutter Click（轻快门）** | 在可见曝光峰值放一次轻快门。 | 已确认的 Film Burn 组合。 | Film Burn 轻快门样片。 |
| **UI Click（界面点击）** | 只在按钮、选择或输入真的发生时给一次短点击。 | 产品界面、代码和操作演示。 | 暂无单独登记的案例。 |
| **Short Impact Hit（短冲击音）** | 在一个真正的画面落点给一次短促重音。 | 大字、数字、结果或章节重音。 | 暂无单独登记的案例。 |

## 全片视觉结构 Visual System

| 画面 | 最简单的描述 | 适合哪里 | 过去用在哪里 |
| --- | --- | --- | --- |
| **Visual Narrative Spine / Master Diagram（视觉主线 / 母图）** | 用一个图形或空间系统贯穿全片，每章只改变它的重点和结构。 | 流程、时间线、成长路线、因果系统或章节型内容。 | 百万计划第三期 Round 04 的“12 个月成长系统”。 |
| **Scatter → Index → Retrieve（散落 → 归档 → 调用）** | 同一组真实材料先分散在不同载体，再汇入统一索引，最后按旁白顺序被调回；形态变化本身就是叙事。 | 企业记忆、知识管理、资料复用、内容生产链等系统型主题。 | 与君 AI《老板内容记忆》全片主线。 |

实现入口：项目 `references/SHOT-LANGUAGE.md`。

## 镜头设计分类 Shot Design

以下分类是外部镜头语言检索库。只有本地方法不足时才进入相关文件，不预读全部条目；来源不等于用户偏好，也不构成第四层。

| 分类 | 主要解决什么 | 读取 |
| --- | --- | --- |
| 镜头运动与空间 | 推拉、环绕、俯冲、景深、空间关系和观看位置。 | [打开](shot-design-camera.md) |
| 数据与信息图 | 数字、图表、时间线、比较、变化和信息结构。 | [打开](shot-design-data.md) |
| 视觉特效与物理反馈 | 冲击、光、材质、粒子、形变和可感知的力量。 | [打开](shot-design-effects.md) |
| 交互表演 | 输入、点击、筛选、协作、生成和系统响应。 | [打开](shot-design-interaction.md) |
| 开场设计 | 第一印象、品牌显影、主体登场和世界建立。 | [打开](shot-design-opening.md) |
| 收尾设计 | 结论、合影、品牌落点、行动号召和能量收束。 | [打开](shot-design-outro.md) |
| 节奏与蒙太奇 | 卡点、加速、停顿、重复、断裂和镜头密度。 | [打开](shot-design-rhythm.md) |
| 转场与接缝 | 遮挡、匹配、擦除、推进和镜头之间的视觉接力。 | [打开](shot-design-transition.md) |
| 动态排版 | 文字显影、拼装、接力、强调、节拍和版式变化。 | [打开](shot-design-typography.md) |
| UI 入场与组装 | 页面、卡片、列表、面板和模块如何进入、落位与建立关系。 | [打开](shot-design-ui-entrance.md) |

先选与当前内容相关的分类，再读取对应文件。卡名只帮助检索；来源、参数、时长、次数和案例不自动成为当前视频的规则。采用时按当前内容、人物、素材、配色和前后镜重新设计。来源与许可见 [来源说明](shot-design-source-and-license.md)。

## 使用方式

- 允许组合，例如“人物中心卡片环绕 + Quiet Fade”，但每一刻只保留一个主动作。
- 允许改变配色、数量、方向、速度、构图和素材；复用的是表达方法，不是旧画面。
- 允许设计目录外的新画面。新画面先服务当前视频，不要求先注册或先证明。
- 本页与链接的分类文件共同构成创作可选库。只有实际进入获批版本的设计才按 [growth-and-writeback.md](growth-and-writeback.md) 写回；允许增加、合并、改名或移除条目。
