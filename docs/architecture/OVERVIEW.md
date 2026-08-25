# 百万AI剪辑师：运行结构

Status: `V3 current`

本文件只记录当前运行结构。完整并行协议见 [PARALLEL-ARCHITECTURE.md](PARALLEL-ARCHITECTURE.md)。旧实验不作为新任务的事实源。

## 一个导演，多段执行

主控 Sol 负责完整内容理解、素材关系、cut plan、A-roll、全片创意简报、分镜、总时间线、字幕、声音和最终节奏。它可以把已经具有清楚首尾状态的连续语义段落交给多个 Sequence Worker 并行实现，但不会把全片导演权拆散。

```text
事实与素材
  → 主控导演判断
  → Creative Brief + 完整分镜 + Sequence Plan
  → TASK.json × N
  → 独占目录并行实现
  → 自动检查与装配
  → 连续预览
  → 一次快速独立审核 + 用户观看
  → 正式母版
```

## 当前事实源

| 内容 | 位置 |
| --- | --- |
| 项目母规则 | `AGENTS.md` |
| 稳定制作参数 | `config/editorial-defaults.json` |
| 剪辑核心审美 | `docs/EDITORIAL-MOTHER.md` |
| 当前个人审美入口 | `library/taste/current.json` |
| 创意能力路由 | `skills/hyperframe-video-editor/references/capability-index.md` |
| 单期事实 | 单期 `episode.json`、`SCRIPT.md`、`SOURCES.md` |
| 全片创意基线 | 单期 `work/creative-brief.json` |
| 人类可读完整分镜 | 单期 `MOTION-STORYBOARD.md` |
| 并行段落计划 | 单期 `work/sequence-plan.json` |
| Worker 任务与产物 | 单期 `sequences/<ID>/` |
| 自动装配顺序 | 单期 `work/assembly-plan.json` |

## 单写者边界

只能由主控修改：内容顺序、统一时钟、A-roll、正文字幕、共享样式、跨段转场、全片声音、总时间线和最终装配。

Worker 在独立 worktree 或等价隔离环境中只写自己的 `sequences/<ID>/`，主控只回收这个目录。任务包改变后，旧产物因指纹不一致而失效；不同 Worker 的 DOM、CSS 与时间线选择器通过段落命名空间隔离。

## 创意边界

创意记忆继续使用：`画面任务 → technique → asset → approved reference`。V3 没有增加镜头配额，也不要求复杂视频必须拆成固定数量的 Agent。简单人物段可以保持干净；复杂片头、真实证据、VOX、系统动画和片尾在边界清楚时适合并行。

速度来自并行、缓存和确定性装配，不来自降低审美、素材质量或预览质量。

## 交付

主控装配后输出一条从头到尾连续的低清预览，亲自观看并修正。随后仅由一个未参与制作的 Sol 快速检查分镜、实现和连续性；用户批准后才输出正式母版。
