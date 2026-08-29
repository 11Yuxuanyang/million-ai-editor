# 镜头语言

这是词汇表，不是任务清单。先判断观众此刻该看什么，再选最简单有效的镜头。

| ID | 专业术语 | 作用 |
| --- | --- | --- |
| `SL-01` | **Snap Zoom / Snap Pull-back** | 快起慢收地推近或拉远，落位后保持；必须与语义重音、展示字或素材落点和 whoosh 同步。 |
| `SL-02` | **Punch-In / Double Punch-In** | 用硬切进入更紧的人物景别；二次强调可再切近一次，不自动退回。 |
| `SL-03` | **Subject Isolation / Selective Focus** | 人物保持清晰，环境可见但退后；不等于默认虚化背景。 |
| `SL-04` | **Full-Frame B-Roll** | 真实动作或证据占满画面，不在背后继续露 A-roll。 |
| `SL-05` | **Portrait / Letterboxed PIP** | 解释画面为主时保留人物；圆角，保持原比例，不拉伸、不糊底。 |
| `SL-06` | **2.5D Camera Projection** | 把可拆分的图片、UI 或证据建立前中后层，再做单一推进、平移或穿越。 |
| `SL-07` | **Container Morph / Scale Match Cut** | 当前容器自然变成下一镜，或用相近形状与位置完成匹配剪切。 |
| `SL-08` | **White Flash / Exposure Flash + Bloom** | 1–3 帧近白峰值完成闪白或过曝换场；不能变成持续光晕。 |
| `SL-09` | **Light Sweep / Light Wipe** | 一束有方向的光扫过并揭示下一镜。 |
| `SL-10` | **Light Leak / Film Burn** | 有许可的真实光学素材覆盖切点，尾部恢复下一镜自然颜色。 |
| `SL-11` | **Shared-Pivot 3D Page Fan** | 多张真实页面从人物身后共用下方枢轴展开，形成带倾角和纵深的扇面。 |
| `SL-12` | **Radial 3D Card Wall** | 卡片以人物组为中心向左右放射，角度、位置和深度错落，彼此部分遮挡。 |
| `SL-13` | **Presenter-Centered 3D Card Orbit** | 2–5 张卡片在人物周围形成浅弧，随台词逐张出现；选中卡片可前移，其他退后。 |
| `SL-14` | **Quick-Flash Evidence Montage** | 数张真实素材随短促节拍快速替换或叠出，用于压缩一组证据。 |
| `SL-15` | **Layered Display Type** | 展示字可在人物前后分层、持续或替换；全部横排，不套正文字幕。 |
| `SL-16` | **Visual Narrative Spine / Master Diagram** | 用一个母图形贯穿主题；随章节改变焦点、尺度和结构，让同一视觉系统持续生长。 |
| `SL-17` | **Animated Topographic Transition** | 一组连贯的等高线在黑色舞台上持续位移、缩放或聚焦，并揭示章节；不是随机手绘线。 |
| `SL-18` | **Editorial Contrast Tableau** | 用一张独立生成的编辑插画建立左右或前后对照，再以推镜、焦点切换或遮罩揭示讲清差异。 |
| `SL-19` | **Pull-back to Rebound Push-in** | 先快起慢收地拉远并落稳，建立人物与环境；随后在新的重点词上从当前景别推回人物或目标。两段运动各自落位后保持，展示字和独立 whoosh 与第二次推进同时击中。 |
| `SL-20` | **Cue-Locked Evidence Handoff** | 人物先提出事实，在对应名词或动作响起时让真实证据接管；证据读清后再交回人物或下一份证明。 |
| `SL-21` | **Full-Frame to PIP Handoff** | 真实素材先全屏建立，再以长尾缓动缩入避脸、避字幕的圆角小窗；缩小前后使用同一份未裁断素材。 |
| `SL-22` | **Dynamic Point-Line Blackout** | 黑场中点位先形成有意义关系，再点亮必要连线和章节字；整组只存在于转场，不能叠在口播画面上。 |
| `SL-23` | **Pixel Resolve** | 旧画面拆成受控像素单元，单元重组并解析为下一镜；适合数字系统或重建语义，不作为通用换场。 |
| `SL-24` | **Generated Cutout Sequence** | ImageGen 只生成可拆分素材，经过抠图、补全和组件化后，以 setup → action → result 完成解释；不是整图淡入。 |
| `SL-25` | **Scatter → Index → Retrieve** | 同一批真实材料从散落载体进入统一索引，并在对应口播处被检索出来成为下一步动作，形成全片视觉主线。 |
| `SL-26` | **Parallel Interface Swarm** | 六至九个真实界面以不同深度、倾角和时点组成不规则三维工作空间；镜头斜向穿过，内部运行状态持续，最后落在主界面。 |

## 判断

近景没空间就不用卡片；证据不足就不用卡片。效果必须建立清楚的空间或语义关系，声音只跟随看得见的动作。

实现骨架与正式资产见 `references/asset-library/registry.json`；音效方向、峰值落点与可复用候选见 `skills/hyperframe-video-editor/references/sound-direction.md`。
