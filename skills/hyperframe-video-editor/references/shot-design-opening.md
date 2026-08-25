# 开头设计库

前三秒先完成钩子，前五秒再完成交代。这里保存的是已经在本地视频或连续预览中用过并被保留的开头语言，不是要求照抄的模板。先理解本期的反常识、人物关系和证据，再选择、改造或重新设计。

使用顺序：先看“本地已用”，没有合适方案再看“可组合变体”和“外部候选”。展示字只保留钩子，不叠正文双语字幕；人物、文字、镜头动作和必要声音必须作为同一个镜头设计。

## 本地已用

| 检索标签 | 看见什么 | 适合哪里 | 过去用在哪里 |
| --- | --- | --- | --- |
| `selective-defocus-heavy-dialogue-open` | 人物或双人分屏先建立真实关系，Source Han Sans SC Heavy 大字按口播清晰切入；全段只挑一至两个语义锚点，让它们在最终位置稳定虚焦，再沿一条连续长尾曲线自然聚焦。普通词直接出现，镜头只用硬切或经过判断的静态裁切。 | 访谈、口播和观点型内容的冷开场；需要用“答案逐渐被看清”强化问题、结论或关键对象时。不是连续正文字幕，也不适合每句话都虚焦。 | `0816-doac-style-owned-footage-sample@v10`，用户认可的开头变体；参数基准见 [`approved-selective-defocus-v2.json`](../assets/opening-display-type/approved-selective-defocus-v2.json)。 |
| `semantic-rise-center-hero-open` | 人物始终是中心，钩子按语义组从画面下方依次升起，最后组成一条大主张；不同词组有明显字号级差，实心白字与本期强调色共同落稳。大字可以有意识地穿过身体或覆盖下半脸，但不能误伤眼睛和口型。 | 一句话里有两到三个递进重音，适合在三至五秒内把压力推到一个核心判断。 | `hf-0728-ai-news-opening-sample@v24-r2`，用户批准的中心 Hero Typography 开头。字体基准见 [`approved-style-v1.json`](../assets/opening-display-type/approved-style-v1.json)。 |
| `long-tail-pullback-depth-type` | 极近人物镜头以快起慢收的长尾运动拉回完整构图；主标题在人物身后穿过身体，次级结论落在前景，注释明显更小，成熟 whoosh 与拉镜同拍。 | 双人或单人口播需要在三秒内同时建立人物、主题与情绪时；不是普通口播叠大字，也不是把近景塞进小窗口。 | `0804-million-challenge-review` 低清预览 v9，用户确认方向。 |
| `counterclaim-subject-reveal-open` | 极近人物镜头长尾拉回；“文案、剪辑”这类惯性答案先以较小文字出现并退虚，真正结论从人物后方扩张为横向大字，人物从字前显形并保持前景。拉远与 `sound-direction.md` 定义的 outward whoosh 同起同落，单期必须另选有许可音源。 | 开场可以先否定一个常见答案，再在三秒内揭示真正昂贵、真正关键或真正被忽略的对象。 | `0813-yujun-boss-content-memory` 正式母版 `00:00–00:03.820`；已认可参考见 [`reference.opening.boss-content-memory.v1`](../../../library/references/reference.opening.boss-content-memory.v1/reference.yaml)。 |

这些方案共享一套展示字基础：系统重黑体、实心字、强字号层级、克制阴影或边缘辉光、无黑色文字容器。颜色、文案、位置和运动都按本期重新判断，不能继承案例的绝对坐标或强调色。

## 可组合变体

| 检索标签 | 看见什么 | 适合哪里 | 当前状态 |
| --- | --- | --- | --- |
| `pullback-rebound-pushin` | 先用长尾拉远建立完整构图并落稳；后续重点词出现时，从当前景别快速推回人物或目标，快起慢收后固定。第二次展示字与独立 whoosh 同时落点，不机械退回原位。 | 开头先交代人物与主题，随后仍需要一个重点词重新收紧注意力；也可用于正文关键结论。 | 用户确认的反向组合，尚缺一条获批正式成片，不视为默认开头。 |

## 可复用零件

这些是开头的组成语言，不单独算一种开头：

- `opening-display-heavy-v1`：展示字体、级差、阴影和人物遮挡基线。
- `semantic rise`：词组按语义压力从下方升起，而不是逐字乱跳。
- `symmetric evidence tableau`：真实证据从人物两侧进入，人物保持因果中心。
- `three-card spread`：三份真实证据从压缩中心展开，最后共同支撑一个结论。
- `impact word`：只让一个重音词迅速放大并稳定，不形成连续大字字幕。
- `selective focus`：一个语义锚点在原位由虚到实，不伴随位移或回弹。

实现与已用证据见 [`library/techniques/registry.json`](../../../library/techniques/registry.json) 和 [`assets/opening-display-type`](../assets/opening-display-type)。

## 外部候选

以下只用于找灵感，本地尚无获批成片；不能因为它们存在就强行套用。

| 检索标签 | 看见什么 | 适合哪里 |
| --- | --- | --- |
| [`brand-ink-open`](https://github.com/Vincentwei1021/video-shotcraft/blob/d4915443232e89527fdc9d7e79f132ba411fc440/references/shots/opening/brand-ink-open.md) | 墨线准星描画，字标逐字压印，副标打字出现，停稳后上浮消散。 | 先立品牌名号再进入产品。 |
| [`crane-rise-reveal`](https://github.com/Vincentwei1021/video-shotcraft/blob/d4915443232e89527fdc9d7e79f132ba411fc440/references/shots/opening/crane-rise-reveal.md) | 从一行数据特写减速升起后拉，逐步揭示完整界面。 | 从细节进入全局。 |
| [`dataviz-landscape-open`](https://github.com/Vincentwei1021/video-shotcraft/blob/d4915443232e89527fdc9d7e79f132ba411fc440/references/shots/opening/dataviz-landscape-open.md) | 暗场流线汇入主干，相机以重景深低速飞越数据地景。 | 数据、网络或系统世界观的抽象开场。 |
| [`icon-field-colorize`](https://github.com/Vincentwei1021/video-shotcraft/blob/d4915443232e89527fdc9d7e79f132ba411fc440/references/shots/opening/icon-field-colorize.md) | 灰阶图标场先铺满，再由一道品牌色波纹快速点亮。 | 产品能力、工具生态或集成规模。 |
| [`letterspace-materialize`](https://github.com/Vincentwei1021/video-shotcraft/blob/d4915443232e89527fdc9d7e79f132ba411fc440/references/shots/opening/letterspace-materialize.md) | 大字距字标的笔画同时生长，最后结晶成完整词。 | 安静、克制的品牌字标或章节题字。 |
| [`magician-card-flourish`](https://github.com/Vincentwei1021/video-shotcraft/blob/d4915443232e89527fdc9d7e79f132ba411fc440/references/shots/opening/magician-card-flourish.md) | 卡片从星芒中沿弧线飞向镜头，减速定住后掠过细光。 | 单张卡片、海报或封面被正式揭示。 |
| [`spotlight-hero-card`](https://github.com/Vincentwei1021/video-shotcraft/blob/d4915443232e89527fdc9d7e79f132ba411fc440/references/shots/opening/spotlight-hero-card.md) | 聚光扫过页面并锁定一张卡，卡片悬起、描边后归位。 | 把一个模块或条目立成主角。 |
| [`stroke-segment-build`](https://github.com/Vincentwei1021/video-shotcraft/blob/d4915443232e89527fdc9d7e79f132ba411fc440/references/shots/opening/stroke-segment-build.md) | 标题先碎成笔画，再逐段点亮，最后突然被读懂。 | 产品名、大数字或延迟揭晓的结论。 |
| [`text-as-mask`](https://github.com/Vincentwei1021/video-shotcraft/blob/d4915443232e89527fdc9d7e79f132ba411fc440/references/shots/opening/text-as-mask.md) | 超粗标题内部透出真实画面，字形放大溢出后让内部画面接管全屏。 | 品牌词、口号与产品画面合一的开场。 |

## 生长

新开头只有进入连续预览并被用户明确保留后，才进入“本地已用”。只验证方向的样片留在单期目录；失败画面不沉淀。新案例优先扩充已有方案的适用边界，确实形成新的叙事结构时才新增标签。
