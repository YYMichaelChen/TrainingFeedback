# GitHub Release v0.8.17

用户于 2026-10-09（Asia/Shanghai）明确要求提交推送并 release。稳定
[v0.8.17](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.17)
已公开并设为 latest，包含计划拖动排序修复、默认右侧编辑及按需指导加载。
修改文件与规则见[设计](../../releases/0.8.17/design.md)、[开发记录](development.md)
和[源码跟进](../0.8.16/plan-editor-follow-up-2026-10-09.md)。

## 分发身份

| 项目 | 实际值 |
| --- | --- |
| 唯一附件 | `TrainingFeedback-0.8.17-Setup.exe` |
| SHA-256 | `c83b8dc41c0efcf8f79ef75e9d616c73ec6856bf19cd4d22d27ccacbfafda233` |
| 大小 | 85,740,355 bytes |
| 签名 | NotSigned |
| 干净构建源码 | `943bf42cd8b609ce710619cea28590438fbe3b8f` |
| Release 标签目标 | `c6604c1e6fdf4f132c06dbf20be1d2474534e5f4` |
| 应用 / schema / catalog / contract | 0.8.17 / 24 / 070-illustrated-3 / 4 |
| 发布时间 UTC | `2026-10-09T13:10:25Z` |
| 发布时间 Asia/Shanghai | 2026-10-09 21:10:25 |
| GitHub release ID | `407927451` |
| GitHub asset ID | `625008907` |

源码及候选证据已推送 main；[载荷清单](payload-build-manifest.json)与
[安装包清单](installer-build-manifest.json)保存精确构建身份。后续文档提交不改变
程序、附件或稳定标签。

先创建草稿并上传唯一 Setup 一次；通过 Releases 列表定位同名草稿，核对 draft、
prerelease、目标提交、唯一 uploaded 附件、大小及 digest 后公开并设为 latest。
不携带 Authorization 的 public latest API 返回 `tag_name=v0.8.17`、`draft=false`、
`prerelease=false`；唯一 Setup 的
`sha256:c83b8dc41c0efcf8f79ef75e9d616c73ec6856bf19cd4d22d27ccacbfafda233`
与实际本地文件及清单一致。`git ls-remote` 确认标签指向候选证据提交。

[下载安装包](https://github.com/YYMichaelChen/TrainingFeedback/releases/download/v0.8.17/TrainingFeedback-0.8.17-Setup.exe)。

## 验证与限制

- 源码修复、版本轮换、构建、分发与收尾共用同一次更新：应用测试 0 项、人工测试
  0 项、功能检查重跑 0 次，无具体启动风险，不新增测试账本。
- 受影响源码 Ruff、文档链接／身份及 Git 差异静态检查通过。构建一次成功，工具链、
  必需资源和程序所有权清单核对完成；实际 Setup 哈希、大小及签名状态已核对。
- 拖动、导航、保存、动作组、客户端流畅度、安装与更新未运行或观察，不记通过，
  不形成待补验收；没有使用 GUI 自动化、脚本点击或按键。
- 应用补丁版本变更；schema、catalog 和 contract 不变。没有访问用户数据或旧数据库，
  没有启动客户端或 Setup。安装包未签名。
- GitHub 分发不声明正式兼容支持、公共验收、外部内容审核、W4、个人数据转移或
  个人使用就绪；候选证据仅对应本次精确构建。
- Planscope `v0.8.17` 完成后关闭并归档，INDEX 无活动版本；旧归档保持只读。
