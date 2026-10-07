# GitHub Release v0.8.13

用户于 2026-10-08（Asia/Shanghai）明确授权“提交推送并 release 更新”。
已发布稳定版 [v0.8.13](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.13)，
包括连续计划交互、精确内容指导阅读和处方数字输入修复。

## 分发身份

| 项目 | 实际值 |
| --- | --- |
| 唯一附件 | `TrainingFeedback-0.8.13-Setup.exe` |
| SHA-256 | `66ec6977bc87af5ef805b35f48b3a28cc46e407051bbc1649571ca9bc66e0b5b` |
| 大小 | 85,690,958 bytes |
| 签名 | NotSigned |
| 干净构建源码 | `531a3178bd1babf15c4e9c7c722b32060b131a66` |
| Release 标签目标 | `8dd1f6d8f2e63df339cdde84822fd250bf73c4ad` |
| 应用 / schema / 目录 / contract | 0.8.13 / 24 / 070-illustrated-3 / 4 |
| 发布时间 UTC | `2026-10-07T23:46:37Z` |
| 发布时间 Asia/Shanghai | 2026-10-08 07:46:37 |
| GitHub release ID | `406254353` |
| GitHub asset ID | `620138622` |

源码及候选证据提交均已推送 main。保存[开发记录](development.md)、
[载荷清单](payload-build-manifest.json)与[安装包清单](installer-build-manifest.json)。
候选证据提交不改变已构建程序；Release 标签固定在该提交。

创建草稿时首次使用远端无法解析的 `HEAD` 参数被 GitHub 422 拒绝，没有创建
Release 或上传附件。改用已推送的完整提交 SHA 后创建成功，只上传一次唯一 Setup。
公开前按草稿记录核对 uploaded 状态、名称、大小和 GitHub digest，再公开设为 latest。
公开后用未携带 Authorization 的请求读取 public latest API，确认
`tag_name=v0.8.13`、`draft=false`、`prerelease=false`，且恰有上述唯一 uploaded
Setup。GitHub 返回的
`sha256:66ec6977bc87af5ef805b35f48b3a28cc46e407051bbc1649571ca9bc66e0b5b`
与本地一致；远端标签通过 `git ls-remote` 核对为上表候选证据提交。

[下载已发布安装包](https://github.com/YYMichaelChen/TrainingFeedback/releases/download/v0.8.13/TrainingFeedback-0.8.13-Setup.exe)。

## 实际验证与限制

- 同一次更新累计应用自动测试 0 项、人工测试 0 项、重跑 0 次。
  追加构建、分发和收尾没有扩大验证范围。
- 相关源码 Ruff、文档链接/身份及差异静态检查通过。构建一次成功；
  核对工具链、资源文件、程序所有权清单及 Setup 的哈希/大小和签名状态。
- 保存处方、界面阅读、训练执行、应用下载/更新交接、Setup 启动、安装覆盖及
  已安装客户端行为未运行，不记通过，也不形成待补验收。
- schema、动作目录及外部协议未改。未访问真实用户数据或旧训练数据库，
  未执行 GUI 自动化。安装包未签名；GitHub 分发不声明正式兼容支持、公共验收、
  外部内容审核、个人数据转移或 W4。
- 本地 Planscope 的源码工作已归档；追加分发使用 Git 状态和本记录承接，
  未重新打开历史计划，INDEX 无活动发布；ROADMAP 更新为本次实际分发状态。
