# GitHub Release v0.8.18

用户于 2026-10-10（Asia/Shanghai）授权提交、推送和 release。稳定
[v0.8.18](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.18)
已公开并设为 latest，包含紧凑列宽、表内横向滚动、明显的水平滚动条、
自动换行按钮和计划编辑字段文案。修改文件见[开发记录](development.md)，
需求与边界见[设计](../../releases/0.8.18/design.md)。

## 分发身份

| 项目 | 实际值 |
| --- | --- |
| 唯一附件 | `TrainingFeedback-0.8.18-Setup.exe` |
| SHA-256 | `774751f0392362cf200d19cb58aab6ae9b039407903997734944711a9533b6d7` |
| 大小 | 85,734,511 bytes |
| 签名 | NotSigned |
| 干净构建源码 | `905b5342e4917932d26889984c0e892887c10737` |
| 稳定标签目标 | `ddfe218d4c5cec8881df8eaf80927e8dbe177a45` |
| 应用 / schema / catalog / contract | 0.8.18 / 24 / 070-illustrated-3 / 4 |
| 发布时间 UTC | `2026-10-09T16:32:52Z` |
| 发布时间 Asia/Shanghai | 2026-10-10 00:32:52 |
| GitHub release ID | `408113958` |
| GitHub asset ID | `625529094` |

[载荷清单](payload-build-manifest.json)与[安装包清单](installer-build-manifest.json)
保留精确候选身份。源码和候选证据已推送 main；后续文档提交不改变程序、附件或标签。

先创建草稿并上传唯一 Setup 一次；核对草稿非 prerelease、唯一 uploaded 附件、
大小与 digest 后公开并设为 latest。不携带 Authorization 的公开 latest API 返回
`tag_name=v0.8.18`、`draft=false`、`prerelease=false`；附件 digest 为
`sha256:774751f0392362cf200d19cb58aab6ae9b039407903997734944711a9533b6d7`，
与本地实际文件和清单一致。`git ls-remote` 确认稳定标签目标一致。

[下载安装包](https://github.com/YYMichaelChen/TrainingFeedback/releases/download/v0.8.18/TrainingFeedback-0.8.18-Setup.exe)。

## 实际验证和限制

- 本次更新无具体启动失败风险，累计应用测试 0 项、人工测试 0 项、功能检查重跑
  0 次；未新增测试账本或额外验收。
- 受影响源码 Ruff、文档链接／身份与 Git 差异静态检查通过；构建一次成功。
  构建核对工具链、必需资源和程序所有权载荷。哈希、大小及未签名状态已核对。
- 没有启动客户端或 Setup；布局、滚动、编辑、保存、安装和更新未运行或观察，
  不记通过，不形成待补验收；未使用 GUI 自动化或脚本操作客户端。
- 应用补丁版本变化，schema、catalog、contract 不变；没有访问用户数据或旧数据库。
- 分发不声明正式兼容支持、公共验收、外部内容审核、W4、个人数据转移或个人使用
  就绪。候选证据只适用于上述精确源码和 Setup。
- Planscope `v0.8.18` 完成后关闭并归档，INDEX 无活动版本；旧归档保持只读。
