# GitHub Release v0.8.20

用户授权“提交推送并 release”。稳定
[v0.8.20](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.20)
已公开并设为 latest，包含添加动作与保存计划分离，以及先另存后自行编辑的计划文件
模板。实现及实际验证见[开发记录](development.md)，范围见
[版本设计](../../releases/0.8.20/design.md)。

## 分发身份

| 项目 | 实际值 |
| --- | --- |
| 唯一附件 | `TrainingFeedback-0.8.20-Setup.exe` |
| SHA-256 | `daed4069ce5cf45327c5880a4a556933af7871038a4562c48af8eeceb5e4064c` |
| 大小 | 85,845,146 bytes |
| 签名 | NotSigned |
| 干净构建源码 | `f71bee5bde3d92f487177ccd5dcf9bde4cf141e3` |
| 稳定标签目标 | `62bb6a61fa3345af7d4281e79439e3bc4cc683e7` |
| 应用 / schema / catalog / contract | 0.8.20 / 25 / 070-illustrated-3 / 4 |
| 发布时间 UTC | `2026-10-17T18:38:29Z` |
| 发布时间 Asia/Shanghai | 2026-10-18 02:38:29 |
| GitHub release ID | `415992562` |
| GitHub asset ID | `651266502` |

[载荷清单](payload-build-manifest.json)与[安装包清单](installer-build-manifest.json)
保留完整候选身份。源码、候选证据及标签已推送；后续文档提交不改变程序、附件或标签。

先创建草稿并上传唯一 Setup 一次，核对非 prerelease、附件 uploaded 状态、大小和
digest 后公开并设为 latest。不携带 Authorization 的公开 latest API 返回
`tag_name=v0.8.20`、`draft=false`、`prerelease=false`，唯一附件 digest 为
`sha256:daed4069ce5cf45327c5880a4a556933af7871038a4562c48af8eeceb5e4064c`，
与本地实际文件及构建清单一致。远端标签指向上表提交。

[下载安装包](https://github.com/YYMichaelChen/TrainingFeedback/releases/download/v0.8.20/TrainingFeedback-0.8.20-Setup.exe)。

## 验证与候选边界

- 无具体启动失败风险，应用测试 0 项、人工测试 0 项；Ruff、文档链接／身份及 Git
  差异静态检查通过。干净构建一次成功，核对受控工具链、必需资源、程序所有权载荷
  以及实际 Setup 哈希、大小、源码状态和签名状态。
- 未运行客户端或 Setup，添加、保存、另存、导入、安装与更新功能均未观察，不记
  通过，不形成待补验收；未使用 GUI 自动化或脚本操作客户端。
- schema 25、内部编辑格式 1、catalog 和外部 contract 不变。schema23/24 的现有
  入口和数据根拒绝规则未改；不新增正式兼容承诺。未访问个人根或旧项目数据库。
- GitHub 分发不声明公共验收、内容审核、W4、个人数据转移或个人使用就绪。证据仅
  对应本表源码和安装包，旧候选结果不自动转移。
- 本次交付使用本地 Planscope v0.8.20；持久要求和候选证据已归入 tracked docs，
  旧规划归档未改写。
