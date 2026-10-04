# GitHub Release v0.8.11

2026-10-04（Asia/Shanghai）在用户明确授权“提交推送并 release”后，
发布稳定版 [v0.8.11](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.11)。

## 分发身份

| 项目 | 实际值 |
| --- | --- |
| 唯一附件 | `TrainingFeedback-0.8.11-Setup.exe` |
| SHA-256 | `baa1e40c153c4ae69ca99e5f53b5d6019cd31481db5515777d511f4911549519` |
| 大小 | 85,689,267 bytes |
| 签名 | NotSigned |
| 构建源码 | `52c9fcef2594c03ee552fa060bb9c3cfda351bb3` |
| Release 标签目标 | `4bc971f8dfbf344b3238ebe825aad894defacc0d` |
| 应用 / schema / 目录 / contract | 0.8.11 / 24 / 070-illustrated-3 / 4 |
| 公开发布时间 | `2026-10-04T08:35:05Z`（北京时间 16:35:05） |
| GitHub asset ID | `609452105` |

Setup 从干净应用源码提交构建；标签目标追加了候选构建记录及清单，
没有改变应用载荷。[开发与候选记录](development.md)、
[载荷清单](payload-build-manifest.json)与
[安装包清单](installer-build-manifest.json)保留完整构建身份。

先上传草稿的唯一 Setup 并确认其 uploaded 状态、大小和摘要，随后发布。
发布后通过**未登录**的 public latest-Release API 读取并确认：
`tag_name=v0.8.11`、`draft=false`、`prerelease=false`，且仅有上述 uploaded
附件，GitHub 返回的
`sha256:baa1e40c153c4ae69ca99e5f53b5d6019cd31481db5515777d511f4911549519`
与本地文件相同。拉取标签确认其目标为上表中的候选记录提交。
这些是分发身份核对，不是客户端更新功能验证。

[下载已发布安装包](https://github.com/YYMichaelChen/TrainingFeedback/releases/download/v0.8.11/TrainingFeedback-0.8.11-Setup.exe)。

## 实际验证与限制

- 本次更新累计 1 项隔离启动检查通过，1 次执行、无重跑；本次打包分发没有追加应用测试。
- 人工测试 0 项；未运行客户端、Setup、自动下载、更新交接、安装或界面功能检查。
- 指导原文、训练执行、schema、目录内容和外部 contract 不变，未读取真实用户数据。
- 安装包未签名。分发不声明正式兼容、公共验收、外部内容审核、个人数据转移或 W4 完成。
- Planscope 的开发计划已关闭归档，此追加交付仅更新本地路线图；没有新的活动发布。
