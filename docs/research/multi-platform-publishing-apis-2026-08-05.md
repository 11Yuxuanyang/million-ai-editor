# 抖音、微信视频号、小红书内容发布 API 核验

核验日期：2026-08-05（北京时间）

## 结论

截至核验日，三个平台都没有一套面向个人/普通创作者、可公开申请并完整覆盖本项目需求的官方 API。

| 平台 | 官方能力能否完整覆盖 | 关键判断 |
| --- | --- | --- |
| 抖音 | 否；但有可用的服务端发布主链路 | 官方 Open API 可上传、立即创建视频、设置自定义封面或指定视频帧、写标题与 `#话题`，并查询审核状态和公开分享链接；但开放平台暂不接受个人开发者入驻，且公开接口资料未证明支持定时发布。 |
| 微信视频号 | 否 | 未找到微信官方对普通创作者公开的内容投稿 API。官方可见入口是视频号创作者后台/产品能力；不能据此推导存在可申请的服务端发布 API。 |
| 小红书 | 否 | 官方“分享开放平台”是客户端分享 SDK，会唤起小红书 App 的发布流程，不是无人值守服务端投稿 API；新接入目前暂停，且标题/文案自动填充受限。公开资料未证明支持定时发布、审核状态轮询或返回笔记公开链接。 |

所以，若目标是“一键直接发布/排期并在到点后复查”，API-first 的现实路线是：抖音先申请机构开发者与 `video.create` 等权限；微信视频号和小红书必须把浏览器/客户端自动化或人工确认作为降级路径。抖音自定义封面已有官方字段；平台内定时发布仍不能在设计阶段假定 API 已覆盖。

## 证据口径

- 只采纳平台自有开放平台、开发者文档或第一方产品页面。
- “未发现/未证明支持”表示公开第一方资料不足以支持该能力，不等于断言平台内部、定向合作接口或未公开接口绝对不存在。
- 网页创作者后台能做某件事，不等于开放 API 也有对应字段。

## 抖音

### 可以确认的能力

1. **上传视频：支持。** 官方 `POST /video/upload/` 接口使用 `video.create` Scope，要求先申请权限并取得用户授权；文件可直接或分片上传，返回 `video_id`。[上传视频](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/create/upload/)
2. **立即创建/发布：支持。** 官方 `POST /video/create/` 使用同一 Scope；创建后进入审核，审核期间仅本人可见。代用户发布时，除 OAuth 授权外，每次调用还必须让用户明确感知该操作。[创建视频](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/create/create-video)
3. **标题和 `#话题`：支持。** 官方发布接入方案说明，可在视频标题 `text` 字段中加入 `#话题1 #话题2`；不相关话题可能影响分发。[抖音内容发布接入方案](https://open.douyin.com/platform/resource/docs/ability/content-management/douyin-publish-solution/)
4. **自定义封面：支持。** `POST /video/create/` 的官方 page-data 接口 schema 包含 `custom_cover_image_url`，说明虽然字段名叫 URL，参数实际为 `/image/upload/` 返回的 `image_id`；同一 schema 还包含 `cover_tsp`，可将指定秒数对应的视频帧设为封面。[创建视频](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/create/create-video)、[创建视频官方 page-data schema](https://open.douyin.com/platform/resource/page-data/docs/openapi/video-management/douyin/create/create-video/page-data.json)、[上传图片](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/publish-img/upload/)
5. **审核/发布状态和公开链接：支持查询。** `video.list`/`video.data` 相关官方接口返回 `video_status`、`is_reviewed`、`share_url`、封面 URL 和作品标识；特定视频数据接口只返回已公开作品，未公开作品不返回。[查询授权账号视频列表](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/search-video/account-video-list)、[查询特定视频数据](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/search-video/video-data)
6. **账号授权：需要 OAuth。** 应用先获得相应 Scope，随后展示官方授权页面让用户授权，以 code 换取用户 `access_token`；服务端应安全保存 token。[获取授权码](https://open.douyin.com/platform/resource/docs/openapi/account-permission/douyin-get-permission-code)、[获取 access token](https://open.douyin.com/platform/resource/docs/openapi/account-permission/get-access-token)

### 门槛与限制

- `video.create` 属于普通权限、默认关闭，需要在管理中心申请；`video.list`、`video.data` 也分别需要申请。[用户类型及权限说明](https://open.douyin.com/platform/resource/docs/accession-guide/type-and-permission)
- 开放平台当前要求机构入驻，官方明确写明“暂时尚未开放至个人开发者的申请入驻”，并要求营业执照、认证公函和单位盖章。因此“普通抖音用户可授权使用已获批第三方应用”不等于“个人创作者能自己注册并获批发布应用”。[平台入驻](https://open.douyin.com/platform/resource/docs/accession-guide/platform-accession)
- 自研开发者和系统服务商均属于正式开发者类型；基础视频能力并非只给服务商，但应用和权限仍须审核。[用户类型及权限说明](https://open.douyin.com/platform/resource/docs/accession-guide/type-and-permission)

### 本需求中未被公开资料证明的能力

- **定时发布：未证明支持。** 公开 `video/create` 文档描述的是创建后进入审核，公开发布方案和接口目录未给出预约时间或调度字段。故不能将创作者后台的定时功能视为 Open API 能力。[创建视频](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/create/create-video)、[抖音内容发布接入方案](https://open.douyin.com/platform/resource/docs/ability/content-management/douyin-publish-solution/)

可行性判断：若有可入驻的机构主体并获批权限，抖音适合优先做官方 API；服务端创建接口可直接设置独立图片封面或视频帧封面。定时节奏可由本地/Codex 调度“到点调用立即发布接口”，但这与平台提前预约发布不同，且到点时必须保证 token、网络和运行环境有效。

## 微信视频号

### 公开资料能支持的结论

截至核验日，没有找到微信官方开发者文档中面向个人/普通视频号创作者的“上传并发布视频号内容”开放 API，也没有找到可公开申请的 OAuth Scope、投稿接口、封面字段、定时字段、审核状态查询接口或作品链接返回定义。

腾讯官方产品介绍只确认视频号是供用户、企业和品牌创作与记录视频的产品，并不能证明存在第三方投稿 API。[腾讯产品介绍：视频号](https://www.tencent.net.cn/zh-cn/products/channels/)

因此以下能力均不能按“官方公开 API 已支持”设计：上传视频、自定义封面、标题/话题、立即或定时发布、审核/发布状态轮询、获取公开作品链接。若后续通过微信商务或服务商渠道取得定向接口，必须以对方提供的正式接口定义和授权条款重新核验；当前不能用非官方抓包接口或网页内部接口冒充开放 API。

可行性判断：API-first 路线目前没有可落地的公开入口；需要把视频号创作者后台的浏览器自动化或人工发布作为降级方案，并在真实账号中验证定时发布、封面和状态可见性。

## 小红书

### 官方实际开放的是客户端分享 SDK

小红书第一方“分享开放平台”提供 Android、iOS、HarmonyOS 客户端 SDK，让第三方 App 把素材交给小红书 App 的发布流程；它不是服务端、无人值守的内容投稿 API。[分享开放平台文档](https://agora.xiaohongshu.com/doc)

- **视频和自定义视频封面：SDK 支持。** Android/iOS 接口文档均描述单视频分享及视频封面参数。[Android SDK](https://agora.xiaohongshu.com/doc/android)、[iOS SDK](https://agora.xiaohongshu.com/doc/ios)
- **标题、正文和 `#话题`：不能作为调用方稳定预填能力。** 官方 Q&A 明确说明已接入与新接入方都受自动填充标题和文案的限制。平台页面提到的标题/话题推荐或自动挂载属于小红书 App 内发布工具，不应解释成第三方可以自由指定发布文案。[官方 Q&A](https://agora.xiaohongshu.com/doc/qa)
- **立即发布：只能表述为“唤起发布流程”。** SDK 有分享成功、失败和用户取消等回调，但用户仍在小红书 App 内完成流程，不能等同于后台直接投稿。[Android SDK](https://agora.xiaohongshu.com/doc/android)、[iOS SDK](https://agora.xiaohongshu.com/doc/ios)
- **定时发布、审核/发布状态轮询、公开链接：公开 SDK 文档未证明支持。** 回调围绕单次分享 `sessionId` 和错误状态；未见预约时间参数、笔记 ID、审核状态查询或公开 URL 返回定义。[分享开放平台文档](https://agora.xiaohongshu.com/doc)

### 接入门槛

- iOS 需要登记开发者应用、申请 AppKey 与分享权限并经审核；Android 文档要求与小红书商务沟通获取 AppKey；HarmonyOS 登记要求面向企业和应用。[iOS SDK](https://agora.xiaohongshu.com/doc/ios)、[Android SDK](https://agora.xiaohongshu.com/doc/android)、[HarmonyOS SDK](https://agora.xiaohongshu.com/doc/harmony)
- 分享开放平台首页当前明确显示“暂停接入”，所以不能假设新项目现在能拿到 AppKey。[分享开放平台首页](https://agora.xiaohongshu.com/)

可行性判断：若已经是获批合作方，可用官方 SDK 做“客户端唤起发布”，但它仍不能完整覆盖本项目的一键无人值守、统一文案、定时排期、发布后复查与链接回收。对于新做的个人 Skill，官方 API/SDK 不能作为完整主链路。

## 封面与开通手续深挖

### 1. 抖音封面：服务端 API 确实支持，且有两种方式

第一次阅读普通网页文本时，页面中的动态参数表没有被正文抓取器渲染出来，容易得出“没有封面字段”的错误结论。直接读取同一官方站点的 Gatsby `page-data.json` 后，可以看到完整请求 schema：

- `custom_cover_image_url: string`：描述为“自定义封面图片”，实际传值是 `/image/upload/` 返回的 `image_id`。因此流程是先用 `video.create` Scope 调用官方图片上传接口，再把 `image_id` 填入创建视频请求。
- `cover_tsp: double`：把指定秒数对应的视频帧设为视频封面，例如 `2.3`。
- 两者均为 `POST /video/create/` 的可选 Body 字段；`video_id` 才是必填字段。

证据：[创建视频普通文档页](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/create/create-video)、[同页官方 page-data 完整 schema](https://open.douyin.com/platform/resource/page-data/docs/openapi/video-management/douyin/create/create-video/page-data.json)、[上传图片](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/publish-img/upload/)

结论修正：抖音服务端创建 API **支持独立自定义封面，也支持选择视频帧作为封面**。本文件前一版“未证明支持自定义封面”的判断已撤回。

### 2. 抖音移动分享 SDK 不是同一条链路

官方 Android/iOS SDK 是把本地视频交给抖音 App：可进入编辑页，也可直接进入发布页；它不等于服务端 `/video/create/`。

- Android 最新公开 `Share.Request`/`ShareParam` 参数表包括媒体、标题、话题、POI、音乐、贴纸、可见范围、下载权限等，但没有独立投稿封面字段。公开视频示例的 `VideoObject` 只接收视频路径。[Android 发布](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/sdk/mobile-app/share/android)
- iOS 公开请求字段同样以相册素材、目标页面、标题、Hashtag、贴纸和小程序为主，未列出投稿封面参数。[iOS 分享](https://open.douyin.com/platform/resource/docs/develop/share/ios)
- SDK 会调起抖音编辑页或发布页，用户可能在抖音界面内使用原生封面功能；这属于 App 交互，不是调用方可依赖的 SDK 封面参数。官方文档里“获取视频封面图”是发布后读取封面，不是发布前设置封面。[拍抖音能力](https://developer.open-douyin.com/docs/resource/zh-CN/mini-app/open-capacity/operation/douyin-video/douyin-task)
- “分享给抖音好友/群”的 HTML `thumbUrl` 是私信链接卡片缩略图，不是视频投稿封面，不能混用。[Android 分享给好友或群](https://open.douyin.com/platform/resource/docs/develop/share/android-share-with-douyin)

因此，本项目若要无人值守并明确指定封面，应优先用服务端 `/image/upload/` + `/video/create/`；移动分享 SDK 更接近“把素材送到发布页让用户完成发布”。

### 3. 抖音开通：自动化能做什么，用户必须做什么

| 环节 | 可由 Skill/程序协助或自动完成 | 必须由用户/机构提供或亲自确认 |
| --- | --- | --- |
| 机构入驻 | 校验材料清单、生成填写草稿；在用户明确授权后辅助录入和上传 | 真实机构主体；营业执照彩色扫描件；认证公函；单位盖章；真实住所、经营范围等法定信息。官方暂不接受个人开发者入驻。 |
| 创建应用 | 生成应用说明、权限用途、技术回调和隐私材料草稿；检查表单完整性 | 对应用名称、图标、业务用途和隐私承诺负责；提供真实 App/网站信息。 |
| 申请 `video.create`、`video.list`、`video.data` | 按需求生成权限申请理由、跟踪状态、读取驳回原因 | 机构管理员授权提交；平台审核结果无法被自动化替代或保证。权限默认关闭，需要管理中心审批。 |
| OAuth 绑定发布账号 | 构造官方授权 URL、接收 code、换取并安全保存 token、自动刷新未过期的 token | 抖音账号本人在官方页面扫码/登录并同意 Scope；refresh token 失效后重新授权。不能静默代替用户同意。 |
| 每次发布 | 在已有授权和明确发布指令下自动上传视频/封面、创建作品、轮询状态和链接 | 用户必须明确感知每次代发操作。官方明确警告，未经用户感知代用户创建视频会被回收权限并处罚。 |

第一方依据：[平台入驻与法定材料](https://open.douyin.com/platform/resource/docs/accession-guide/platform-accession)、[权限类型与申请方式](https://open.douyin.com/platform/resource/docs/accession-guide/type-and-permission)、[OAuth 获取授权码](https://open.douyin.com/platform/resource/docs/openapi/account-permission/douyin-get-permission-code)、[获取 access token](https://open.douyin.com/platform/resource/docs/openapi/account-permission/get-access-token)、[刷新 token 与重新授权边界](https://open.douyin.com/platform/resource/docs/openapi/account-permission/refresh-access-token)、[创建视频的逐次用户感知要求](https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/create/create-video)

补充边界：官方把“自研开发者”和“系统服务商”都列为开发者类型。系统服务商可以开发第三方应用服务创作者，但基础 `video.create` 仍是需要应用审批和账号 OAuth 的普通权限；“服务商身份”不构成绕过材料、权限审核或用户授权的通道。[用户类型及权限说明](https://open.douyin.com/platform/resource/docs/accession-guide/type-and-permission)

### 4. 视频号与小红书的服务商/定向能力边界

#### 微信视频号

- 本轮仍未找到微信官方开发者文档中面向普通创作者，或公开提供给 MCN/服务商申请的内容投稿接口定义与申请入口。
- 能找到的腾讯第一方产品资料只证明视频号提供内容创作产品，不能证明第三方可通过公开 API 上传、设封面、排期或查询公开作品链接。[腾讯产品介绍：视频号](https://www.tencent.net.cn/zh-cn/products/channels/)
- 证据边界：这不否认微信可能向定向合作机构提供未公开能力；只是截至核验日，没有可供本项目据以实现和申请的第一方公开接口合同。若用户已有微信商务/MCN/服务商合同，应要求对方提供正式接口文档、Scope、调用域名和授权条款后单独复核。

#### 小红书

- 官方“分享开放平台”是移动 App 分享 SDK。Android/iOS 文档支持把单个视频和独立视频封面交给小红书 App，因此**客户端分享链路有封面参数**。[Android SDK](https://agora.xiaohongshu.com/doc/android)、[iOS SDK](https://agora.xiaohongshu.com/doc/ios)
- Android 文档要求与小红书商务沟通取得 AppKey；iOS 需要登记应用、申请 AppKey/分享权限并审核；HarmonyOS 登记面向企业与应用。这说明存在合作/审核门槛，但并不能推出一个服务端 MCN 投稿 API。[Android SDK](https://agora.xiaohongshu.com/doc/android)、[iOS SDK](https://agora.xiaohongshu.com/doc/ios)、[HarmonyOS SDK](https://agora.xiaohongshu.com/doc/harmony)
- 分享开放平台首页当前显示“暂停接入”，新项目不能把获得 AppKey 当作确定前提。[分享开放平台首页](https://agora.xiaohongshu.com/)
- 官方 Q&A 限制自动填充标题和文案；SDK 也未公开预约时间、笔记审核轮询和公开链接返回接口。因此即使已有合作 AppKey，也只证明可唤起 App 发布并携带素材/封面，不证明可无人值守完整投稿。[官方 Q&A](https://agora.xiaohongshu.com/doc/qa)
- 证据边界：未找到小红书面向普通创作者或 MCN 公开申请的服务端笔记投稿 API。若有定向商务能力，需要以小红书提供的非公开正式合同和接口定义另行核验。

### 5. 定时发布再核验

- **抖音服务端创建 API：未找到官方定时字段。** 完整 page-data Body schema 中有封面、标题、视频、锚点等字段，但没有 `publish_time`、`schedule_time` 或同义调度字段。[创建视频官方 page-data schema](https://open.douyin.com/platform/resource/page-data/docs/openapi/video-management/douyin/create/create-video/page-data.json)
- **抖音移动分享 SDK：未找到定时参数。** Android `ShareParam` 公布的参数表没有调度时间；流程进入抖音编辑/发布页。[Android 发布](https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/sdk/mobile-app/share/android)
- **微信视频号：未找到面向普通创作者的公开投稿 API，因此也没有可据以实现的官方 API 定时字段。**
- **小红书分享 SDK：未找到调度时间参数；它是即时唤起 App 的分享动作，不是平台预约任务。**[分享开放平台文档](https://agora.xiaohongshu.com/doc)

工程结论：当前能由官方接口明确落地的“定时”方案，是由本地/Codex 队列在目标时刻调用立即发布链路；它是本地调度，不应对用户宣称为平台原生预约。对于只能走 App/网页后台的平台，本地调度还依赖设备在线、登录有效与界面可用。

## 对 Skill 设计的直接影响

1. 采用“平台适配器 + 能力探测”，不要把三个平台抽象成同一套必然可用的 API。
2. 抖音适配器分成 `official_api` 和 `creator_backend_fallback`；只有拿到机构资质、应用审核结果和真实 Scope 后才启用 API。
3. 微信视频号暂设 `creator_backend_fallback`，不要实现或保存非公开网页接口。
4. 小红书暂设 `app_share_sdk`（仅已有 AppKey 时）与 `creator_backend_fallback`；SDK 路线不得标成无人值守发布。
5. 统一排期由本地队列负责：有平台定时 API 才提前预约；没有则到点执行立即发布。后者必须在用户可理解的结果中标明“本地调度”，并处理机器离线、登录失效和审核延迟。
6. 发布完成标准不能只看“上传成功”：应分别记录 `已上传`、`已提交`、`审核中`、`已公开`、`失败`。只有拿到公开页面或经官方状态接口确认，才记为 `已公开`。
