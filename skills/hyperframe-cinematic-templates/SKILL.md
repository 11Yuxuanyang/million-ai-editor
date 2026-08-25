---
name: hyperframe-cinematic-templates
description: Choose and adapt reusable HyperFrame motion grammars after a storyboard beat has a clear semantic job and actual geometry. Covers long-tail camera moves, layered type, evidence handoffs, presenter-centered cards, generated cutouts, visual systems, and optical transitions.
---

# HyperFrame Cinematic Templates

这些是参数化镜头骨架，不是固定画面。

## 选择

- 长尾推近、拉远或重点回推，落位后保持：`longTailScale`
- 人物前后景展示字：`layeredDisplayType`
- 真实证据按口播交接、全屏缩入小窗：`cueLockedEvidenceHandoff`、`fullFrameToPipHandoff`
- 多个概念或页面围绕人物：`presenterCardOrbit`、`sharedPivotPageFan`
- 一组真实证据快闪：`quickFlashMontage`
- 散落资料变成可调用系统：`scatterIndexRetrieve`
- 生成拆件完成 setup → action → result：`generatedCutoutSequence`
- 容器变形或焦点交接：`containerMorph`、`rackFocus`
- 真实笔画或曝光峰值：`brushAccent`、`exposureFlash`

不适配就不用。卡片内容、数量、位置、倾角、颜色和声音都根据台词、人物构图和素材重新设计。

## 使用

复制 `assets/cinematic-templates.js` 到当前 HyperFrame 项目，在主 GSAP timeline 中调用对应函数。先设置人物和卡片的真实几何，再传入时间；不要直接沿用示例数值。

人物中心卡片的核心关系：

- 人物保持主视觉平面。
- 2–5 张卡片围绕人物形成浅弧或扇形，不平铺。
- 每张卡片有独立 `x/y/z/rotateY/rotateZ`。
- 卡片随台词或字幕节拍逐张出现；只允许一个主要动作。
- 可以有一张前移成为当前焦点，其余退后。
- 没有可靠人物抠像时，卡片放在人物两侧或下方，不伪造穿插。

声音是独立的剪辑判断，只能和同一可见动作或转场峰值共用落点。
