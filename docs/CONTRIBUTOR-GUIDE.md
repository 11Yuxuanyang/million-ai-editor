# 百万AI剪辑师贡献与部署指南

## 先建立同一套环境

1. 克隆仓库。
2. 运行 `uv sync --extra dev`，建立锁定的 Python 环境和测试依赖。
3. 运行 `./system/scripts/install-local-skills.sh`。旧 Skill 会被备份，活动 Skill 必须指向本仓库，不能静默沿用本机旧版。
4. 运行 `npm install -g hyperframes@0.8.12`，然后重启 Codex 或新建任务，让新的 Skill 与版本绑定生效。
5. 安装并登录 Codex、Node.js、Python 与 FFmpeg，然后运行 `python3 system/scripts/editctl.py doctor --mode full-edit --verify-asr`；该命令会用极短静音片段真实验证 ASR 凭据，状态降级时先处理报告的缺口。
6. ASR、ImageGen 和平台账号凭据只放本机环境变量或系统钥匙串，不写入仓库。

## 系统如何分工

- `system/scripts/editctl.py` 是确定性生产入口；`system/editing/` 分别承载 JSON/进程、媒体探测、ASR 与运行时诊断，新增机械能力时优先进入对应模块，不继续堆进入口脚本。
- `hyperframe-video-editor` 负责理解台词、判断素材关系、写 cut plan、导演分镜和实现画面。
- V3 中，主控可以将锁定分镜拆成语义段落任务包，多个 `hyperframe-sequence-worker` 只实现各自目录；主控统一装配和处理跨段节奏。
- 创作判断是“核心规则 + 个人审美”：核心读统一强制项与审美母原则，个人审美从 `library/taste/current.json` 按镜头读取。反复成立的经验提炼进核心，失效规则退出活跃层。
- 已沉淀画面通过 `capability index → technique ID → asset ID → approved reference` 调用。先按本期语义选能力，再只展开相关实现和参考；不要只抄名字，也不要一次加载整个库。

这意味着基础工作可以复用，画面不会被固定成同一套模板。

## 每期素材如何交付

用生产入口创建单期：

```bash
python3 system/scripts/editctl.py new <日期或主题> --title "标题" --profile general
```

然后在该目录至少放入：

- 原始视频与补充素材；
- 原文或文稿；
- 已知的事实、更正与平台要求；
- 用户指定参考；
- 授权与素材来源说明。

媒体默认不进 Git。需要协作传大文件时使用共享硬盘或云盘，并保持原文件名不变。

## 工作入口

1. 首次安装或更换凭据后运行 `editctl.py doctor --mode full-edit --verify-asr`；若报 `doubao-asr`，先在本机配置 `DOUBAO_APP_KEY` 和 `DOUBAO_ACCESS_KEY`。然后对本期运行 `inspect` 与 `transcribe`。
2. 调用 `hyperframe-video-editor`，结合音频、文稿和动作确定素材顺序，写 `work/cut-plan.json`。
3. 运行 `build-aroll`；AI 同时确定本期视觉母题、配色、真实素材与完整 `MOTION-STORYBOARD.md`。
4. 旧工程先运行一次 `upgrade-v3`；复杂视频由主控写 `work/creative-brief.json` 与 `work/sequence-plan.json`，运行 `pack-sequences` 后在隔离工作区并行派发段落，只回收对应的 `sequences/<ID>/`；简单视频可以直接实现。
5. Worker 完成后运行 `check-sequences` 与 `assemble-sequences`；主控统一跨段转场、字幕、声音和总节奏。封面由独立上下文执行 `auto-cover-imagegen`。
6. 运行 `style-check` 与 `render --quality preview`，先阻止字幕黑框、描边和字体漂移，再完整观看连续低清成片并修正。
7. 用户批准后运行 `render --quality master --approved` 和 `verify`。

cut plan 的最小格式：

```json
{
  "rate": 1.1,
  "clips": [
    {"sourceId": "inventory 中的 id", "sourceStart": 0.42, "sourceEnd": 8.73}
  ],
  "tailHoldSeconds": 0.3
}
```

## 真正需要继承的判断

- 前三秒是最高优先级，但不是固定模板；主体、构图、展示字、镜头运动和必要声音必须作为一个完整镜头设计。
- 每十秒内应有一次有意义的画面变化，变化服务内容，不为凑数。
- 真实素材负责证明；生成画面负责解释、比喻和情绪，不能冒充事实。
- 人物、字幕、证据和关键动作优先于效果。避免无意义渐变、光晕、装饰线和 PPT 式信息卡。
- 同一期建立一条视觉主线，章节只改变焦点和尺度，不每段重建一套风格。
- 低清连续预览由人完整观看；最后只做一次独立快速审核，不设置多层门禁。

## 获批视觉参考快照

`episodes/reference/0813-yujun-boss-content-memory/` 是近期获批案例的视觉与代码快照，不是脱离本期资料即可重建的工程。它缺少未入库的原始媒体和字幕工作文件，保留的历史 HyperFrames 版本也只用于理解当时实现。它用于校准信息密度、节奏和实现质量，不要求复制其画面。可直接复用的素材必须在共享注册表中拥有明确实现路径和许可；只登记方向的声音需要在单期另选有许可音源。

新任务需要人物长尾推拉、前后景展示字、真实证据交接、人物中心 3D 卡片、VOX 拆件、散落到调用的视觉主线或章节转场时，先读 `skills/hyperframe-video-editor/references/capability-index.md`。选中后由 `library/techniques/registry.json` 的 `assetRefs` 直接落到 `references/asset-library/registry.json` 中的实现。

## Skill 维护

- `skills/hyperframe-video-editor/SKILL.md` 只保留入口与判断顺序，细节放在 `references/`。
- 新技巧只有在连续预览中真实使用且被保留后，才写回共享 Skill。
- 单期例外留在本期目录，不升级成全局规则。
- 修改仓库内 Skill 后，符号链接安装方式会立即生效；提交前运行：

```bash
python3 skills/hyperframe-video-editor/scripts/validate_skill_integrity.py
```
