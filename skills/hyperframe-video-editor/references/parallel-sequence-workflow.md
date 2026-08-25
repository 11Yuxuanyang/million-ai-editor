# V3 并行段落制作

V3 把全片导演判断和段落实现分开。主控先理解完整内容并锁定一条视觉主线，再把可以独立实现的连续语义段落交给多个 Sol；不是让多个 Agent 各自重新导演一遍视频。

## 何时拆分

满足以下条件后才拆：A-roll 与统一时钟已确定、完整分镜已写、全片创意简报已明确、相邻段落的入口与出口可描述。

按叙事段落和实现依赖切分，而不是按每句字幕或每个小动作切分。通常一个任务覆盖能独立表达完整意思的连续片段；复杂片头、VOX、证据段、系统动画和片尾适合独立，连续的简单人物节拍可以合并。段落数量由内容和复杂度决定。

不适合并行的工作由主控保留：内容顺序、统一时钟、字幕、跨段转场、全片声音、共享 CSS、总时间线和最终节奏。

## 主控写两份事实

`work/creative-brief.json` 只保存全片共同创意基线：观众承诺、视觉论点、前五秒、视觉主线、色彩角色、展示字层级、声音方向、共享素材和本期例外。

`work/sequence-plan.json` 保存每段局部事实：

- 变速后起止时间和准确口播；
- 观众任务、情绪节拍和主视觉角色；
- 本地或网络素材与当前句子的关系；
- 入口状态、可见动作、落稳构图和出口状态；
- 已选 technique / asset / reference；
- 只属于这一段的说明。

完整可见分镜仍保留在 `MOTION-STORYBOARD.md`，方便人审片；JSON 用于可靠拆包。

## 生成任务包

```bash
python3 system/scripts/editctl.py pack-sequences <episode>
```

命令会为每段写 `sequences/<ID>/TASK.json`，嵌入完整创意简报、当前段落和相邻边界，并对当期文档、指定素材和已选能力建立带哈希的可用契约。子 Agent 不需要读取主 Session，也不能声称使用任务包外的证据或能力。

任务、共享分镜、A-roll、核心配置或审美入口改变时，旧 Worker 产物会因内容指纹不一致失效。主控确认重做后才使用 `--force` 更新任务包。

## 并行派发

每个子 Agent 只收到：

```text
使用 hyperframe-sequence-worker，实现 <episode>/sequences/<ID>/TASK.json。
只写该 TASK 指定的 exclusiveWriteRoot；完成后返回 sequence.json 路径和一句落稳结果。
```

多个任务可以并行，但必须运行在各自的 forked worktree 或等价隔离工作区。主控只回收任务声明的 `exclusiveWriteRoot`，拒绝 Worker 对共享工程或其他段落的任何改动。封面仍使用独立封面 Agent，不混入段落任务。

## 合并

```bash
python3 system/scripts/editctl.py check-sequences <episode>
python3 system/scripts/editctl.py assemble-sequences <episode>
npm run build
```

旧工程在第一次并行前运行 `python3 system/scripts/editctl.py upgrade-v3 <episode>`；它会先备份旧模板和构建器，再补齐 V3 入口。

检查会拒绝过期任务、越界文件、未声明素材或能力、断裂的入出口、重复或未加前缀的 DOM ID、未限定作用域的 CSS 和缺失产物。装配命令保留每段的落稳结果、入出口、实际素材、实际能力和备注；构建器随后按分镜顺序合并片段、样式和 GSAP 语句。

主控最后统一处理跨段交接、正文字幕、声音和节奏，输出一条连续预览。独立审核仍然只在连续预览完成后快速做一次。
