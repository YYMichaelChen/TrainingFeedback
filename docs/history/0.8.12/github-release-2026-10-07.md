# GitHub Release v0.8.12

用户于 2026-10-07（Asia/Shanghai）明确授权“提交推送并 release 新版程序”。
本次已发布稳定版 [v0.8.12](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.12)，
包括独立更新启动器的退出兜底和临时文件占用修正。

## 分发身份

| 项目 | 实际值 |
| --- | --- |
| 唯一附件 | `TrainingFeedback-0.8.12-Setup.exe` |
| SHA-256 | `22fc750d5773fd9442ee1e29e7644747544786639101c72d0e9d0800d33235f6` |
| 大小 | 85,693,750 bytes |
| 签名 | NotSigned |
| 干净构建源码 | `8a3ae604bc93dcff9b42798036a4a39d924f8158` |
| Release 标签目标 | `03e957cf8a9176fe4a163f991967c7bcc269b969` |
| 应用 / schema / 目录 / contract | 0.8.12 / 24 / 070-illustrated-3 / 4 |
| 发布时间 UTC | `2026-10-07T10:37:03Z` |
| 发布时间 Asia/Shanghai | 2026-10-07 18:37:03 |
| GitHub release ID | `405648379` |
| GitHub asset ID | `618368952` |

源码修复及身份提交 `ad82e87` 和日志清理修正 `8a3ae60` 已推送 main。
最终 Setup 从后者的干净源码构建；候选记录提交 `03e957c` 保留
[开发和候选记录](development.md)、[载荷清单](payload-build-manifest.json)
与[安装包清单](installer-build-manifest.json)，并作为 v0.8.12 标签目标。
候选证据提交不改变已构建载荷。

先创建草稿并上传唯一 Setup，按 release ID 核对 uploaded 状态、附件名称、
大小和 GitHub digest，再公开并设为 latest。草稿按标签读取返回 404，随后
通过已授权的草稿列表和 release ID 读取完成核对；没有重复上传附件。
公开后以未携带 Authorization 的请求读取 public latest API，确认
`tag_name=v0.8.12`、`draft=false`、`prerelease=false`，且恰有上述唯一
uploaded Setup；GitHub 返回的
`sha256:22fc750d5773fd9442ee1e29e7644747544786639101c72d0e9d0800d33235f6`
与本地文件相同。远程标签指向上述候选记录提交。

[下载已发布安装包](https://github.com/YYMichaelChen/TrainingFeedback/releases/download/v0.8.12/TrainingFeedback-0.8.12-Setup.exe)。

## 实际验证与限制

- 沿用 `2026-10-06-external-update-exit`；本次更新累计 1 项隔离启动检查通过，
  1 次执行、无重跑。追加构建/分发/收尾自动应用检查 0 项，人工检查 0 项。
- 改动文件的静态源码、PowerShell 语法、文档和身份检查通过；构建核对资源
  清单、大小与哈希，静态打包模块清单包含新启动器，未执行它。
- 下载、更新交接、退出、外部终止、Setup 启动、覆盖安装和已安装客户端
  行为未运行，不记通过，也不作为待补任务。
- 旧进程更新到本版时仍执行旧更新器，因此本次升级仍可能需要手动关闭。
  安装并打开 0.8.12 后，后续更新才使用新机制；Setup 仍是交互式安装。
- 数据 schema、动作目录和外部 contract 未改；未读取真实用户数据或旧数据库。
  安装包未签名；分发不声明正式兼容支持、公共验收、内容审核、个人数据转移
  或 W4。
- Planscope v0.8.12 按实际分发身份收尾关闭；未来继续依据使用反馈修复。
