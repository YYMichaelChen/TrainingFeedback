# GitHub Release v0.8.25

用户授权“执行 v0.8.25 的开发，开发完成后，提交推送，release v0.8.25”。稳定
[v0.8.25](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.25)
已公开并设为 latest，包含历史摘要／详情读取、现有根单一打开协调、通用包图标资源、
当前 pytest 硬限制及规范身份整理。实现与源码验证见[开发记录](development.md)，行为
依据见[产品规范](../../development-plan.md)。

## 分发身份

| 项目 | 实际值 |
| --- | --- |
| 唯一附件 | `TrainingFeedback-0.8.25-Setup.exe` |
| SHA-256 | `7df906756e883eedd284d5285adbf972f70f58a0ec32331a597b66fb6d963aee` |
| 大小 | 85,905,339 bytes |
| 签名 | NotSigned |
| 干净构建源码 | `7a7d76e1e22cb0052009558b074c70a7b97b7bb6` |
| 稳定标签目标 | `7a7d76e1e22cb0052009558b074c70a7b97b7bb6` |
| 应用 / schema / 编辑格式 / catalog / contract | 0.8.25 / 26 / 2 / 070-illustrated-3 / 5 |
| 构建工具 | Python 3.12.14 AMD64 / PySide6 6.11.2 / PyInstaller 6.22.2 / Inno Setup 6.7.3 |
| 载荷文件数 | 301 |
| 发布时间 UTC | `2026-10-19T16:31:12Z` |
| 发布时间 Asia/Shanghai | 2026-10-20 00:31:12 |
| GitHub release ID | `417505253` |
| GitHub asset ID | `656795123` |

[载荷清单](payload-build-manifest.json)与[安装包清单](installer-build-manifest.json)
保留完整候选身份。构建前源码工作树干净且已推送；标签与远端 `main` 在发布时都解析到
上述构建提交。后续证据提交不改变标签、程序载荷或附件。

Release 创建为非草稿、非预发布并设为 latest，只上传唯一 Setup。未携带 Authorization
的公共 latest API 返回 `tag_name=v0.8.25`、`draft=false`、`prerelease=false`，唯一
附件名称、85,905,339 字节、下载地址和 digest
`sha256:7df906756e883eedd284d5285adbf972f70f58a0ec32331a597b66fb6d963aee`
与本地文件及安装包清单一致。

[下载安装包](https://github.com/YYMichaelChen/TrainingFeedback/releases/download/v0.8.25/TrainingFeedback-0.8.25-Setup.exe)。

## 验证与候选边界

- 干净构建一次成功，固定工具链、catalog 身份、必需资源、载荷文件清单及 Setup 哈希、
  大小、签名和构建来源已由构建流程核对；包内包含运行时使用的
  `training_feedback/ui/TrainingFeedback.ico`。未运行 Setup 或客户端。
- 同一开发更新累计应用测试 1 项：locator/current-root 合成启动场景首次通过，无失败或
  重跑；人工测试 0 项。构建和分发新增应用／人工测试 0 项。此源码级结果不认证安装包
  启动、历史／反馈/UI、安装、更新或其它客户端行为；未观察行为不记通过或待补验收。
- 修改范围 Ruff、134 份 Markdown 的文档／身份检查和 Git 差异检查在源码提交前通过；
  发布证据写入后，文档／身份检查通过 135 份 Markdown，Git 差异检查通过。收尾没有
  重复运行应用测试。
- 未访问个人数据根或旧项目数据库。发布没有改变 schema、编辑格式、外部合同或 catalog，
  也不建立正式兼容基线、公共验收、外部内容审核、W4、个人数据转移或个人使用就绪结论。
