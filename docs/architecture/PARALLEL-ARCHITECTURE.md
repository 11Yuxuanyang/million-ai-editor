# 百万AI剪辑师 V3 并行架构

V3 的目标不是让更多 Agent 各剪一版，而是让一个导演判断可以被多个执行者同时实现。

```text
完整内容理解
    ↓
主控导演：cut plan + A-roll + Creative Brief + 完整分镜
    ↓
按连续语义段落拆成 TASK.json
    ↓
多个 Sequence Worker 并行写独占目录
    ↓
确定性检查与自动装配
    ↓
主控统一跨段节奏、字幕、声音与连续预览
    ↓
一次快速独立审核 → 用户观看 → 正式母版
```

## 为什么这样拆

单 Agent 的瓶颈是素材检索、VOX、生图、复杂动画和长时间线实现依次排队。把这些已经有清楚上下文边界的段落并行，能减少等待；让总时间线保持单写者，又避免合并时丢节奏、字幕漂移或互相覆盖。

V3 不追求 Agent 数量。简单人物段落留给主控，复杂且独立的段落才派发。速度来自同时工作、缓存和清晰接口，不来自降低画面质量。

## 三份契约

1. `work/creative-brief.json`：全片共同的创意事实。
2. `work/sequence-plan.json`：每个连续语义段落的时间、任务、素材关系和首尾状态。
3. `sequences/<ID>/TASK.json`：可独立执行的不可歧义任务包。

Worker 交付 `sequence.json` 和可选的 `scene.html`、`styles.css`、`timeline.js`、局部资产。它不读取主 Session，并且必须在隔离工作区运行；主控只回收该 Worker 的段落目录，不合并其他改动。

任务包会记录 `BRIEF.md`、`SCRIPT.md`、`SOURCES.md`、`DESIGN.md`、共享分镜、素材清单、字幕、A-roll、核心配置与审美入口的内容指纹，并对本段指定的真实素材和成熟能力建立契约；任何一项改变，旧段落结果都会自动失效。

Worker 返回的落稳构图、实际入出口、已用素材、已用能力和备注会全部进入装配计划；未声明资源和断裂的相邻边界会被拒绝。

## 单写者边界

主控唯一负责：内容顺序、统一时钟、A-roll、正文字幕、共享样式、跨段转场、全片声音、最终装配与审美连贯性。

Worker 只负责：当前 TASK 描述的可见画面及其局部资产。它可以挑战模板和设计新画面，但不能改变全片事实与边界。

## 命令

```bash
python3 system/scripts/editctl.py pack-sequences <episode>
python3 system/scripts/editctl.py check-sequences <episode>
python3 system/scripts/editctl.py assemble-sequences <episode>
python3 system/scripts/editctl.py render <episode> --quality preview
```

已有视频工程先运行一次 `upgrade-v3`。命令会备份旧构建器与模板，再补入 V3 装配入口；新建工程无需迁移。

构建器读取 `work/assembly-plan.json`，按段落顺序合并 Worker 的 HTML、作用域 CSS 与 GSAP 语句。没有 V3 分镜计划时仍兼容原来的单 Agent 工程；一旦分镜计划非空，装配文件必须存在、覆盖全部段落，并与当前创意简报和分镜文件一致。
