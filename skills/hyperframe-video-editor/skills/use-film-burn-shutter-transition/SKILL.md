---
name: use-film-burn-shutter-transition
description: Apply the approved Film Burn Overlay Transition with its soft camera-shutter click inside a video's opening. Use when the editor freely chooses an analog exposure-wash transition between two opening beats; never use it as the boundary from opening into body content.
---

# Film Burn + Soft Shutter

这是一个已验收、可以自由选择的开头内部转场。

## 使用位置

- 只连接开头内部的两个 opening beat。
- 不放在“开头结束 → 正文开始”的边界。
- 不要求用户逐次点名；由主剪辑 Agent 根据开头节奏决定。
- 不连续重复使用。

## 事实源

- 从项目素材注册表读取 `transition.film-burn-screen-composite.v1`；素材路径、许可、审核和当前版本都以该条目为准。
- 制作时按需读取该条目的 `recipe`。不要从聊天历史重建参数，也不要把注册表信息复制进分镜。

## 执行

1. 使用注册表中的 `file` 与 `audio`，不得换成其他快门、`clack` 或重复音效。
2. 将 Film Burn 以 RGB `Screen` 或经验证的克制加法合成；黑底靠混合模式透明，不做预黑。
3. A 镜头在红橙色前导中持续可见；在最高亮度曝光峰切到 B；保留覆盖 B 的暖色尾部，再恢复自然画面。
4. 只重定时特效板，不再次变速 A/B。按画面事件定节奏，不把样片时长写成常量。
5. 将注册的轻快门瞬态对齐曝光峰。它是这个已确认组合的一部分，可以直接使用；根据对白压低音量，不要让它盖住人声。

## 验收

- 峰前无黑帧，A 可见；曝光峰完整遮住切点；B 在尾部下可见并自然恢复。
- 只有一次轻微快门声，瞬态与曝光峰误差不超过 1 帧，不盖对白。
- 注册条目状态为 `approved`，素材、许可和审核路径均可解析。
