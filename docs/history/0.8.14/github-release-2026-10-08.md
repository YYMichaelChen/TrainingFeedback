# GitHub Release v0.8.14

用户于 2026-10-08（Asia/Shanghai）明确要求“提交推送并release”。已发布稳定版
[v0.8.14](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.14)，
包含计划界面相对尺寸、三栏响应布局、指导抽屉和本机界面缩放。

## 分发身份

| 项目 | 实际值 |
| --- | --- |
| 唯一附件 | `TrainingFeedback-0.8.14-Setup.exe` |
| SHA-256 | `26a5a403975e2dab7ce769e048abae04fb33faba7171579357e84e6ebca4169e` |
| 大小 | 85,727,665 bytes |
| 签名 | NotSigned |
| 干净构建源码 | `b09b611a790f0647feecc8e3813351c45eaaa44c` |
| Release 标签目标 | `6b701968e12e889888a74f3b178d3bdbb72b927e` |
| 应用 / schema / catalog / contract | 0.8.14 / 24 / 070-illustrated-3 / 4 |
| 发布时间 UTC | `2026-10-08T11:00:47Z` |
| 发布时间 Asia/Shanghai | 2026-10-08 19:00:47 |
| GitHub release ID | `406727664` |
| GitHub asset ID | `621561931` |

源码与候选证据提交已推送 main。保存[开发记录](development.md)、
[载荷清单](payload-build-manifest.json)和[安装包清单](installer-build-manifest.json)。
候选与分发记录提交不改变已构建程序；标签固定在上述候选证据提交。

Release 先创建草稿，Setup 上传一次。草稿尚未创建 Git tag 时，按标签 API 查询
返回 404；通过已授权 Release 列表找到唯一同名草稿，未重复创建或上传。
核对 draft、prerelease、目标提交、唯一 uploaded 附件、大小与 GitHub digest 后
公开并设为 latest。随后用不携带 Authorization 的请求读取 public latest API：
`tag_name=v0.8.14`、`draft=false`、`prerelease=false`，恰有上述唯一 uploaded Setup，
返回 `sha256:26a5a403975e2dab7ce769e048abae04fb33faba7171579357e84e6ebca4169e`，
与本地实际文件及构建清单一致。`git ls-remote` 确认标签指向上表提交。

[下载安装包](https://github.com/YYMichaelChen/TrainingFeedback/releases/download/v0.8.14/TrainingFeedback-0.8.14-Setup.exe)。

## 实际验证与限制

- 同一次更新 scope `plan-interface-20261008` 累计 1 项隔离启动构造通过、执行 1 次、
  重跑 0 次、人工测试 0 项。追加版本轮换、构建、分发及收尾新增应用测试 0 项。
- 相关源码 Ruff、文档链接/身份及差异静态检查通过；构建一次成功。工具链、必需
  资源、程序所有权清单及 Setup 哈希/大小/签名状态已核对。
- 客户端布局、系统/应用 DPI 缩放、拖拽、文本拉高、保存、更新下载/交接、安装覆盖
  及已安装客户端行为未运行或观察，不记通过，也不形成必须补做的验收任务。
- Schema、catalog、外部协议未改。未访问真实用户训练数据或旧训练数据库；
  未操作客户端或安装器，未使用 GUI 自动化、脚本点击/按键或远程控制。
- 安装包未签名。分发不声明正式兼容支持、公共验收、外部内容审核、个人数据
  转移、个人使用就绪或 W4。历史候选证据不转移给此构建。
- Planscope `v0.8.14` 完成并归档，INDEX 无活动发布；ROADMAP 仅路由实际分发状态。
