# GitHub Release v0.8.16

用户于 2026-10-09（Asia/Shanghai）明确要求提交推送并 release。稳定
[v0.8.16](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.16)
已公开并设为 latest，包含完整训练按钮宽度、居中图库文字和均分图库列宽。
修改文件和规则见[设计](../../releases/0.8.16/design.md)、[开发记录](development.md)
与[源码记录](../0.8.15/layout-follow-up-2026-10-09.md)。

## 分发身份

| 项目 | 实际值 |
| --- | --- |
| 唯一附件 | `TrainingFeedback-0.8.16-Setup.exe` |
| SHA-256 | `c26ff9d174bc1de6677feb293d52954339c63db21f889cbe1bccc27ba53b149c` |
| 大小 | 85,732,682 bytes |
| 签名 | NotSigned |
| 干净构建源码 | `e12b5db3a04b2febb068de9d46aeb114debbdb91` |
| Release 标签目标 | `bf11339284182a610f995fed766395084d6c3604` |
| 应用 / schema / catalog / contract | 0.8.16 / 24 / 070-illustrated-3 / 4 |
| 发布时间 UTC | `2026-10-08T16:44:00Z` |
| 发布时间 Asia/Shanghai | 2026-10-09 00:44:00 |
| GitHub release ID | `407056561` |
| GitHub asset ID | `622403058` |

源码和候选证据已推送 main；[载荷清单](payload-build-manifest.json)与
[安装包清单](installer-build-manifest.json)保留精确构建身份。后续文档证据提交
不改变程序、附件或稳定标签。

Release 先建草稿，唯一 Setup 上传一次。通过 Releases 列表定位同名草稿，
核对 draft、prerelease、目标提交、唯一 uploaded 附件、大小与 digest 后公开并
设为 latest。不携带 Authorization 的 public latest API 确认 `tag_name=v0.8.16`、
`draft=false`、`prerelease=false`，唯一 Setup 的
`sha256:c26ff9d174bc1de6677feb293d52954339c63db21f889cbe1bccc27ba53b149c`
与本地文件及清单相同。`git ls-remote` 确认标签指向上表候选证据提交。

[下载安装包](https://github.com/YYMichaelChen/TrainingFeedback/releases/download/v0.8.16/TrainingFeedback-0.8.16-Setup.exe)。

## 验证与限制

- 源码修复、版本轮换、构建、分发及收尾累计**应用测试 0 项、人工测试 0 项、
  重跑 0 次**。无具体启动风险，不新增应用检查或测试账本。
- 受影响 Python 文件 Ruff、文档链接/身份和 Git 差异静态检查通过。构建一次
  成功，工具链、必需资源、程序所有权清单及实际 Setup 哈希/大小/签名状态已核对。
- 客户端排版、225%/跨屏 DPI、训练、更新交接、安装覆盖和卸载未运行或观察，
  不记通过，也不是待补验收任务。未使用 GUI 自动化、脚本点击或按键。
- 应用补丁版本变更；schema、catalog、contract 不变。未访问真实用户数据或
  旧训练数据库，未启动客户端或安装器。
- 安装包未签名。GitHub 分发不声明正式兼容支持、公共验收、外部内容审核、
  W4、个人数据转移或个人使用就绪；候选证据仅对应本次精确构建。
- Planscope `v0.8.16` 已完成并归档，INDEX 无活动版本；旧归档保持只读。
