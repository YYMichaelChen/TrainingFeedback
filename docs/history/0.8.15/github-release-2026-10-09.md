# GitHub Release v0.8.15

用户于 2026-10-09（Asia/Shanghai）明确要求“提交推送并release”。
稳定 [v0.8.15](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.15)
已公开并设为 latest，包含 4K 上默认 2560×1440 窗口、紧凑字号、响应页面结构
与独立动作框；[设计](../../releases/0.8.15/design.md)和
[开发记录](development.md)说明改动文件与证据。

## 分发身份

| 项目 | 实际值 |
| --- | --- |
| 唯一附件 | `TrainingFeedback-0.8.15-Setup.exe` |
| SHA-256 | `4aa81c4c6e517a8e1958ef36c4ce59fb96da520d558d707cae47025b6e1484bf` |
| 大小 | 85,739,870 bytes |
| 签名 | NotSigned |
| 干净构建源码 | `22acd710a5a89da216f50da550722ed99e795ec0` |
| Release 标签目标 | `4f9eb3ad59d3315ceb0362503cc69f65a848f7c9` |
| 应用 / schema / catalog / contract | 0.8.15 / 24 / 070-illustrated-3 / 4 |
| 发布时间 UTC | `2026-10-08T16:14:21Z` |
| 发布时间 Asia/Shanghai | 2026-10-09 00:14:21 |
| GitHub release ID | `407030428` |
| GitHub asset ID | `622332783` |

源码和候选证据已推送 main；[载荷清单](payload-build-manifest.json)与
[安装包清单](installer-build-manifest.json)保留精确构建信息。后续文档证据提交
不改变已构建程序或稳定标签。

Release 先建草稿，唯一 Setup 上传一次。通过 Releases 列表定位同名草稿，
核对 draft、prerelease、目标提交、唯一 uploaded 附件、大小和 digest 后公开。
随后使用不携带 Authorization 的 public latest API 确认
`tag_name=v0.8.15`、`draft=false`、`prerelease=false`，唯一 Setup 返回
`sha256:4aa81c4c6e517a8e1958ef36c4ce59fb96da520d558d707cae47025b6e1484bf`，
与本地实际文件和清单一致。`git ls-remote` 确认标签指向上表候选证据提交。

[下载安装包](https://github.com/YYMichaelChen/TrainingFeedback/releases/download/v0.8.15/TrainingFeedback-0.8.15-Setup.exe)。

## 实际验证与限制

- 更新 scope `compact-interface-20261008` 累计 1 个隔离启动构造场景通过、
  执行 2 次（重跑 1 次），人工测试 0 项。版本轮换、构建、分发和收尾新增
  应用检查 0 项；原账本保留，不扩大或重置额度。
- 源码 Ruff、文档链接/身份与差异静态检查通过，构建一次成功。工具链、
  必需资源、程序所有权清单及 Setup 哈希/大小/签名状态已核对。
- 客户端布局、悬停、系统/应用 DPI、跨屏、动作编辑保存、训练、更新交接、
  安装覆盖和卸载未运行或观察，不记通过，也不形成待补验收任务。
- 应用补丁版本变更；schema、catalog、contract 不变。未访问真实数据或旧训练
  数据库，未操作客户端/安装器或使用 GUI 自动化、脚本点击、按键。
- 安装包未签名。GitHub 分发不声明正式兼容支持、公共验收、外部内容审核、
  个人数据转移、个人使用就绪或 W4；历史候选结果不转移。
- Planscope `v0.8.15` 已完成并归档，INDEX 无活动版本；ROADMAP 路由本次
  实际交付记录，旧归档保持只读。
