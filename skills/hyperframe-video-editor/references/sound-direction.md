# 音效方向

音效不是气氛贴纸。先找到画面中真实发生的动作或编辑事件，再选择方向、包络和落点。

## 已确认方向：0813 片头拉远呼声

| 字段 | 记录 |
| --- | --- |
| 方向 ID | `sfx.opening-pullback-whoosh.direction.v1` |
| 分发状态 | 只登记方向；开源仓库不包含原始音频母文件 |
| 用户叫法 | 这个片子的呼声、片头拉远的“呼” |
| 声学形态 | 1.100 秒，AAC 双声道，48 kHz；空气质感跟随快起慢收的拉远运动，不额外叠低频“咚” |
| 镜头绑定 | `counterclaim-subject-reveal-open`；与极近人物拉回完整构图同时启动，声音尾部与镜头落稳共同完成真正判断的揭示 |
| 已确认案例 | `0813-yujun-boss-content-memory` 正式母版；工程中 `0.05s` 启动，播放 `1.10s` |
| 选材要求 | 每期从有明确商业使用许可的来源另选 outward air whoosh，并保留来源与许可证 |

这条是该开头的默认声音方向，不是所有推拉镜头的通用音效。案例中的 `0.70` 只是当期混音；新项目仍需重新选材、按人声定电平，并逐帧对齐包络。

## 历史声学参考：02 吸入唰（非默认资产）

| 字段 | 记录 |
| --- | --- |
| 专业检索名 | `Reverse-Suction Snap-Zoom Whoosh` / `Reverse Air Sweep` |
| 用户叫法 | 02、短促吸入呼、开头放大聚焦的“唰” |
| 声学形态 | 0.662 秒；能量由弱到强，约 `+0.469s` 达峰；没有低频“咚”作为主体 |
| 镜头绑定 | 音效与推拉/由虚到实同时启动；峰值对齐摄影机主要位移与聚焦落稳处，不对齐动作起点 |
| 已确认案例 | `0816-raw-talking-head-20s-sample` v14：0 秒启动，镜头 0.48 秒落稳 |
| 内容身份 | SHA-256 `5d973eafec96434d7b89b30eed32a3c5264997f24522538081c6e1fd5128b753`；个人缓存复用键 `5d973eafec96434d` |
| 权利边界 | 原始作者与授权未核验；只作用户确认的声学参考和内部预览，不能直接进入商业母版 |

这条只保留“声音包络如何跟镜头对齐”的历史判断，不再代表仓库默认片头声音，也不能直接进入商业母版。

## 2026 创作者常用家族

Uppbeat 在 2026 年发布的统计基于其 300 万创作者上一年度的下载行为。它支持“哪些音效家族常用”，不证明任何外站母带本身爆火。

| 家族 | 流行证据 | 适用 | 不要用于 |
| --- | --- | --- | --- |
| `Smooth Swish / Whoosh` | `Whoosh - Smooth swish` 为其上一年度下载量第一 | 标题滑入、轻转场、连续运动 | 没有位移的静态大字；重大冲击 |
| `Quick Swipe / Swoosh` | 榜单第 10；用于快切与快速转场 | 横甩、卡片快速移入、照片切换 | 缓慢推镜；需要吸向目标的镜头 |
| `Small Bubble Pop` | 榜单第 5，且为其下载量最高的 premium SFX | 单个图标、标签、数字或 UI 出现 | 整屏大标题、严肃结论、连续每个字 |
| `Camera Shutter` | 榜单第 12 | 照片定格、闪白拍照、证据快照 | 普通换场；没有摄影语义的白闪 |
| `Heartbeat Tension` | 榜单第 14 | 明确倒计时、危险临近、悬念积累 | 普通解释段；用来假造紧张感 |

来源：[Uppbeat 2026 YouTuber SFX 下载统计](https://uppbeat.io/blog/sound-effects/sound-effects-youtubers-use)、[Whoosh - smooth swoosh](https://uppbeat.io/sfx/whoosh-smooth-swoosh/11761/30556)、[Swoosh - quick swipe](https://uppbeat.io/sfx/swoosh-quick-swipe/4214/17803)。Uppbeat 素材按下载时账户与方案授权，不能把下载文件作为通用库存转售或在订阅失效后继续“囤货待用”；正式项目逐次确认其当前授权。

## 已找到并缓存的可商用候选

以下文件来自 Mixkit 官方下载地址，按 Mixkit Sound Effects Free License 可用于个人与商业视频；不可原样转售或做素材库再分发。文件保存在个人 `~/.media` 内容寻址缓存，不进入 Git。新项目先运行 `media-use --candidates`，再用复用键导入。

| 用途 | 官方条目 | 时长 | 复用键 | 使用判断 |
| --- | --- | ---: | --- | --- |
| Zoom 空气吸入替代 | [Air zoom vacuum · 2608](https://mixkit.co/free-sound-effects/transition/) | 1.275s | `62d46c7faeaa2860` | 推近/拉远候选；先试听包络，再决定是否反转或裁短。不是 02 的同母带 |
| 轻横甩 | [Fast small sweep transition · 166](https://mixkit.co/free-sound-effects/transition/) | 0.781s | `ca5a0206a7e6b128` | 快速横移、照片切换；不承担冲击 |
| 重转场 whoosh | [Cinematic whoosh fast transition · 1492](https://mixkit.co/free-sound-effects/transition/) | 1.334s | `02b8cd40b3761288` | 可见的大幅换场；普通小元素会显得过重 |
| 图形微弹出 | [Explainer video pops whoosh light pop · 3005](https://mixkit.co/free-sound-effects/whoosh/) | 0.180s | `2ae8c9395cb02fec` | 单个 UI/标签落点；避免连续铺满 |
| 数字故障 | [Cinematic sci-fi glitch · 1022](https://mixkit.co/free-sound-effects/glitch/) | 0.825s | `5a4e8db3640e3da9` | 仅与可见 glitch、信号断裂或数字故障绑定 |
| Zoom + impact | [Quick zoom impact · 772](https://mixkit.co/free-sound-effects/impact/) | 1.222s | `a9acddce67b0ad80` | 推镜同时落到重大揭示；不能替代纯空气吸入 |
| 章节级长尾冲击 | [Big cinematic impact · 788](https://mixkit.co/free-sound-effects/impact/) | 7.941s | `772e4afc9e793228` | 只给章节级事件；普通句子禁用 |

Mixkit 授权依据：[Sound Effects 页面与 FAQ](https://mixkit.co/free-sound-effects/)、[Mixkit License](https://mixkit.co/license/)、[User Terms](https://mixkit.co/terms/)。

## 落点判断

- `Reverse / suction / riser`：能量向后聚拢，峰值对齐镜头落稳或目标清晰的时刻。
- `Swipe / quick swoosh`：瞬态贴动作启动或通过画面中心的时刻，尾巴可以跨切点。
- `Impact / boom`：瞬态贴揭示、闪白峰值或构图完成；不要提前砸在预备动作上。
- `Pop / click / shutter`：必须与单一可见事件逐帧同步；没有对应动作就留白。
- 一个动作优先一颗主音效。只有画面确有“预备 → 落地”两阶段时，才组合 riser + impact。

## 混音边界

- 先保证口播清楚，再让音效明确可闻；不能因“高级感”把音效压到听感上不存在。
- 不把 `0.35`、`0.90` 等单期电平当全局常数。比较同一时段的人声与音效，检查 true peak 和遮蔽。
- 反向吸入 whoosh 的主要任务是方向感，不要额外叠低频“咚”改变语义。
- 流行只决定候选池，不决定使用。声音必须由文案情绪和可见动作共同触发。
