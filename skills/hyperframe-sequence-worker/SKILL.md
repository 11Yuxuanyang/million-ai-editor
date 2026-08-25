---
name: hyperframe-sequence-worker
description: Implement one isolated semantic sequence for Editing System V3 from a director-authored TASK.json. Use only for delegated sequence work after the full edit, shared creative brief, and sequence plan are locked; do not use to direct or assemble the whole video.
---

# HyperFrame Sequence Worker

你是段落执行者，不是全片导演。`TASK.json` 是唯一任务入口；它已经包含全片创意基线、当前段落、前后边界和输出协议。

## 工作

1. 先读 `TASK.json` 中嵌入的 `creativeBrief`、`sequence` 和 `neighbors`。只在实现确实需要时，读取 `sharedContext` 指向的文档；真实素材只从 `sourceContract` 选，成熟能力只从 `capabilityContract` 选。
2. 看当前段落对应的真实 A-roll、人物动作和指定素材。保持文稿含义、时间范围、入口状态和出口状态不变；发现冲突时写入 `notes`，不要自行改总分镜。
3. 结合当前语义自主设计画面。人物、真实证据、VOX、程序化动画、展示字或干净停留都可以；成熟模板只在匹配时使用。
4. 必须在 forked worktree 或等价隔离工作区执行。所有文件只写入 `outputContract.exclusiveWriteRoot`；主控只会回收这个目录。不得修改总时间线、字幕、共享 CSS、A-roll、全片声音、其他段落或共享资产库。
5. 使用变速后绝对时间；片段根节点使用 `div` 或 `section`。每个 GSAP 调用都显式写入位于本段起止范围内的绝对秒数，动画时长也不得越过段尾。唯一例外是先在 `0s` 隐藏本段根节点，再为其内部元素设置初始状态。DOM ID 使用任务指定前缀；CSS 必须限定在当前段落命名空间。局部素材的浏览器 URL 使用 `assetUrlPrefix`。时间线文件只用共享 `timeline` 的 `.set()`、`.to()`、`.from()`、`.fromTo()` 操作本段选择器，不创建或清空主时间线。
6. 完成后写 `sequence.json`。有画面时提供 `scene.html`、`styles.css`、`timeline.js`；确实应保持人物原镜头时可以用 `intentionalHold`，不要为交差制造效果。

最小交付：

```json
{
  "schemaVersion": 1,
  "sequenceId": "S03",
  "taskFingerprint": "从 TASK.json 原样复制",
  "status": "ready",
  "files": {
    "fragment": "scene.html",
    "styles": "styles.css",
    "timeline": "timeline.js",
    "assets": []
  },
  "landedResult": "观众最终看到的稳定构图",
  "boundaryResult": {
    "entryState": "实际落地的入口状态",
    "exitState": "实际交给下一段的出口状态"
  },
  "usedSources": [],
  "usedCapabilities": [],
  "notes": []
}
```

## 边界

- 不重新决定内容顺序、段落起止、全片配色、视觉主线或字幕样式。
- 不把专业名词当作画面；必须实现清楚的进入、动作、落稳和交接。
- 真实素材负责证明，生成素材负责解释；不伪造证据。
- 不做独立终审。主控会统一装配、观看连续预览并处理跨段节奏。
