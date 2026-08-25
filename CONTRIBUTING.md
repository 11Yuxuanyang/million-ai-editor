# 参与百万AI剪辑师

谢谢你愿意一起完善这套剪辑系统。这里更看重真实项目中的有效判断，而不是规则数量。

## 开始前

```bash
uv sync --extra dev
./system/scripts/install-local-skills.sh
python3 system/scripts/editctl.py doctor --mode runtime
```

请先阅读：

- `AGENTS.md`
- `docs/EDITORIAL-MOTHER.md`
- `docs/CONTRIBUTOR-GUIDE.md`
- `references/asset-library/README.md`

## 可以贡献什么

- 可复现的剪辑、转录、装配或渲染修复；
- 在连续预览或正式成片中被保留的镜头方法；
- 有明确来源、许可证和语义用途的素材；
- 更清楚的文档、测试和错误提示；
- 删除失效、重复或妨碍判断的规则。

请不要提交：

- 原始口播、客户资料、聊天记录、平台凭据或正式成片；
- 来源不明的音乐、音效、字体、图片、视频或模型输出；
- 只展示效果、没有使用条件和失败边界的模板；
- 把单期例外强行升级成全局规则的改动。

## 验证

提交前运行：

```bash
uv run pytest -q
python3 skills/hyperframe-video-editor/scripts/validate_skill_integrity.py
python3 system/scripts/editctl.py doctor --mode runtime
```

涉及视觉输出时，请同时提供一条连续低清预览或小体积联系表，并说明：

1. 它解决了什么内容问题；
2. 什么时候适用；
3. 什么时候不应使用；
4. 素材来源与许可证；
5. 它是否在真实成片中被保留。

## Pull Request

- 一次 PR 聚焦一个清楚的问题。
- 不重写无关文件，不清理他人的本地工作。
- 说明行为变化、验证结果和剩余风险。
- 如果改动了 Skill，同时更新对应参考或测试，但不要扩展成新的多层审核流程。

规则可以被挑战，Skill 可以成长。好的贡献让下一位创作者少做重复劳动，同时保留更多判断空间。
