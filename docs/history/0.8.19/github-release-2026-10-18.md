# GitHub Release v0.8.19

用户授权开发后直接提交、推送和 release。稳定
[v0.8.19](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.19)
已公开并设为 latest，包含未完成计划草稿、严格计划文件预览导入、中文问题定位和 Qt
中文资源，也携带先前未提交的计划编辑和中文报错改动。修改及验证详见
[开发记录](development.md)，要求见[版本设计](../../releases/0.8.19/design.md)。

## 分发身份

| 项目 | 实际值 |
| --- | --- |
| 唯一附件 | `TrainingFeedback-0.8.19-Setup.exe` |
| SHA-256 | `b379a509025db8d011a0697eda90c3ace4f343f3180c90d527cb29d8c09791ec` |
| 大小 | 85,845,925 bytes |
| 签名 | NotSigned |
| 干净构建源码 | `2d0e78793719d61953eaa985ecb3d7a7469ec048` |
| 稳定标签目标 | `d516cb63bfd7178adfa68483bbc118651e277765` |
| 应用 / schema / catalog / contract | 0.8.19 / 25 / 070-illustrated-3 / 4 |
| 发布时间 UTC | `2026-10-17T16:41:43Z` |
| 发布时间 Asia/Shanghai | 2026-10-18 00:41:43 |
| GitHub release ID | `415933649` |
| GitHub asset ID | `650990292` |

[载荷清单](payload-build-manifest.json)和[安装包清单](installer-build-manifest.json)
保留完整候选身份。源码及候选证据已推送 main；后续文档提交不改变程序、附件或标签。

先创建草稿并上传唯一 Setup 一次。按 release ID 核对非 prerelease、唯一 uploaded
附件、大小和 digest 后公开并设为 latest。不携带 Authorization 的公开 latest API
返回 `tag_name=v0.8.19`、`draft=false`、`prerelease=false`，附件 digest 为
`sha256:b379a509025db8d011a0697eda90c3ace4f343f3180c90d527cb29d8c09791ec`，
与本地实际文件及清单一致；远端标签指向上表提交。

[下载安装包](https://github.com/YYMichaelChen/TrainingFeedback/releases/download/v0.8.19/TrainingFeedback-0.8.19-Setup.exe)。

## 验证与候选边界

- 2 个隔离合成根启动场景通过：新根初始化和 schema24 升级；因存储列改动各重跑
  一次，最终 2 passed，累计 4 次场景执行。人工测试 0 项，功能检查 0 项。
- Ruff、文档链接／身份及差异静态检查通过，干净构建一次成功；构建核对受控工具链、
  必需资源及程序所有权载荷。哈希、大小、源码状态和未签名状态已核对。
- 客户端、Setup 均未运行；保存、导入、启用、训练、显示、备份、安装与更新未观察，
  不记通过，不形成待补验收；未使用 GUI 自动化或脚本操作客户端。
- 新增 schema25 和内部编辑格式1，支持映射保留23/24升级入口；外部合同和目录版本
  未变。未访问个人数据或旧项目数据库，未改写活动计划和冻结训练事实。
- GitHub 分发不声明正式兼容支持、公共验收、内容审核、W4、个人数据转移或个人使用
  就绪。证据只对应本表精确源码及安装包，旧候选结果不自动转移。
- Planscope `v0.8.19` 已关闭归档，INDEX 无活动版本，旧归档未改写。
