# GitHub Release v0.8.21

用户授权“提交推送并release”。稳定
[v0.8.21](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.21)
已公开并设为 latest，包含左右交替动作的编辑、计次解释、连续执行、按组实际记录及
历史导出，并包含此前未发布的问题提示修复。文件范围及实际源码检查见
[开发记录](development.md)，行为依据见[产品规范](../../development-plan.md)。

## 分发身份

| 项目 | 实际值 |
| --- | --- |
| 唯一附件 | `TrainingFeedback-0.8.21-Setup.exe` |
| SHA-256 | `cb9f2af8997563c2a755bd05089bbff567b6204e871935771ee8c8b48759a605` |
| 大小 | 85,861,616 bytes |
| 签名 | NotSigned |
| 干净构建源码 | `bd8f1e71fa0629be683974984de9c34a1b34727e` |
| 稳定标签目标 | `e013ae360ead3a7842aeab2d568a7a2ccec42289` |
| 应用 / schema / 编辑格式 / catalog / contract | 0.8.21 / 26 / 2 / 070-illustrated-3 / 5 |
| 发布时间 UTC | `2026-10-18T06:40:45Z` |
| 发布时间 Asia/Shanghai | 2026-10-18 14:40:45 |
| GitHub release ID | `416279212` |
| GitHub asset ID | `652707841` |

[载荷清单](payload-build-manifest.json)与[安装包清单](installer-build-manifest.json)
保留完整候选身份。构建源码与候选证据已推送，远端附注标签解析到上表提交；后续文档
提交不改变该标签、程序载荷或附件。

先创建草稿并上传唯一 Setup 一次，按 Release ID 核对 uploaded 状态、名称、大小和
digest 后公开并设为 latest。未携带 Authorization 的公开 latest API 返回
`tag_name=v0.8.21`、`draft=false`、`prerelease=false`，唯一附件 digest 为
`sha256:cb9f2af8997563c2a755bd05089bbff567b6204e871935771ee8c8b48759a605`，
与本地文件和安装包清单一致。

[下载安装包](https://github.com/YYMichaelChen/TrainingFeedback/releases/download/v0.8.21/TrainingFeedback-0.8.21-Setup.exe)。

## 验证与候选边界

- 干净构建一次成功，核对固定工具链、必需资源（含 v5 合同、SQL、中文资源）、目录
  文件身份及实际 Setup 的哈希、大小、签名和构建来源；未运行 Setup 或客户端。
- 本次分发新增应用测试 0 项、人工测试 0 项。同一开发更新累计 2 项隔离合成根启动
  检查通过，各执行 1 次，无重跑；不追加功能回归或安装验收。原结果只说明其源码级
  启动范围，不能视为精确安装包或客户端功能通过。未观察的行为不记通过或待补验收。
- README、文档入口、版本历史、设计状态和本记录同步分发身份；静态文档／身份和差异
  检查通过，源码阶段 Ruff 已通过。应用、schema、合同、编辑格式和 catalog 与上表一致。
- 保留原计划、原始导入文件及冻结训练语义；没有访问个人根或旧项目数据库。本次分发
  不建立正式兼容、公共验收、外部内容审核、W4、个人数据转移或个人使用就绪结论。
- 本地 Planscope 的源码阶段已经归档，未改写归档内容；仅更新当前 ROADMAP 分发路由，
  无活动开发 release。候选与发布事实以 tracked docs 为准。
