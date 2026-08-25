# 百万AI剪辑师索引

- 当前任务：用户指令 + 单期 `episode.json` / `SCRIPT.md` / `SOURCES.md`
- 部署与贡献：`docs/CONTRIBUTOR-GUIDE.md`
- 审美母原则：`docs/EDITORIAL-MOTHER.md`
- 稳定技术参数：`config/editorial-defaults.json`
- 镜头语言：`references/SHOT-LANGUAGE.md`
- 可复用资产：`references/asset-library/registry.json`
- 剪辑 Skill：`skills/hyperframe-video-editor/`
- 当前运行结构：`docs/architecture/OVERVIEW.md`
- V3 并行架构：`docs/architecture/PARALLEL-ARCHITECTURE.md`
- 段落执行 Skill：`skills/hyperframe-sequence-worker/`
- 封面 Skill：`skills/auto-cover-imagegen/`
- 成功案例：`episodes/reference/0813-yujun-boss-content-memory/`
- 开源发布文稿：`docs/OPEN-SOURCE-LAUNCH-SCRIPT.md`

复杂镜头按需读取对应小型 Skill；历史文档、旧门控和旧审核记录不再参与当前剪辑判断。
本机可以保留未跟踪的 `NOW.md` 作状态便签，但它不会随 Git 交接，也不能覆盖单期事实。
