# 0.8.0 本地候选 — 2026-10-02

本候选修复安装目录缺少归属文件时直接显示英文异常的问题。
**新包安装及客户端检查未运行**，需要开发者按
[中文手动步骤](../../releases/0.8.0/manual-acceptance.md) 实际复验。
这是未签名的本地候选，不是正式或公开发布，也未建立个人使用、内容审核或 W4 资格。

## 精确身份

| 项目 | 值 |
| --- | --- |
| 应用 / schema / catalog / wire | 0.8.0 / 23 / 070-illustrated-3 / 3 |
| 干净构建源码 | b55e746793b2c20573167642ed1bb1e7affe1c1c |
| 构建时间 UTC | 2026-10-01T16:40:40Z（北京时间 10 月 2 日） |
| 构建耗时 | 101.92 秒，含 PyInstaller、验证、Inno 与清单 |
| 完整程序目录 | 296 文件，176,808,893 bytes |
| 安装包 | 85,602,404 bytes，NotSigned |
| 构建工具 | Python 3.12.14 AMD64 / PySide6 6.11.2 / PyInstaller 6.22.2 / hooks 2026.7 / Inno 6.7.3 |

| 文件 | SHA-256 |
| --- | --- |
| TrainingFeedback.exe | d44eec5eb56694bb513c65e31a4922832be2ee1d649c32068970db07e7ff4675 |
| TrainingFeedback-0.8.0-Setup.exe | 8b5fd69ac7babe7da6ebbf9a5eea2e3926e779b93d6bdf5ee52b655b2cb59575 |
| 程序构建清单 | c53e78a6d89feb03ff0fd6f29b8596ef272b514b95c5cd57235b9f94ca670323 |
| 安装包构建清单 | 4b806d40f3585ce4543074096adc3a131f88a518d8ece1e0b60f31f4467d032d |
| 程序归属清单 | 49990648cda99e9b7809efc43d229deb526f7c4a1a0fc98f233b191bd9f779c2 |

文件位于本仓库 `dist/installer/TrainingFeedback-0.8.0-Setup.exe`，以及
`dist/TrainingFeedback/` 完整程序目录。构建和核对结果分别保存在
[程序清单](payload-build-manifest-2026-10-02.json)、
[安装包清单](installer-build-manifest-2026-10-02.json) 和
[静态审计](candidate-audit-2026-10-02.json)。后续证据提交不改变本候选的源码或字节身份。
9 月 30 日的候选证据继续保留；其旧安装包另存本地 `.tmp/candidates/2026-09-30/`。

## 实际验证和限制

同一个 `release-0.8.0` minor scope 累计 **100/100 unique cases**。
本次受影响的安装相关 **26 项通过，0.52 秒**，含两个新增缺归属文件用例；
未受影响的原 98 节点结果复用，不声称本次又跑了全部 100 项。
[风险选集](../../releases/0.8.0/release-verification.md) 在追加执行前已记录。
Ruff、文档一致性、diff 检查通过。

PyInstaller 和 Inno 从干净源码构建成功。静态验证逐一核对程序所有路径、大小
和 hash，比较安装包 hash、嵌入的程序构建清单和程序归属清单；catalog 与
36 个动作资源验证通过。构建脚本检查当前 schema、契约和必要运行库，拒绝
夹带用户数据库或 locator。没有运行安装器、卸载器或客户端，没有自动点击或按键。

完整多行提示由 Inno 的 `LoadStringsFromFile` 读取 UTF-8 helper 结果，再逐行
拼接；其 UTF-8 支持已核对 [Inno 官方文档](https://jrsoftware.org/ishelp/topic_isxfunc_loadstringsfromfile.htm)。
编译通过不证明弹窗在实际屏幕上的显示效果通过。

[10 月 2 日截图](installation-error-2026-10-02.md) 的目录提示记为失败，截图
缺少精确安装包 hash，不能把该结果转移为本候选结论。本候选的完整中文弹窗、
旧程序仅卸载保留数据、新目录安装、覆盖/搬迁、卸载及客户端检查均 **未运行**。
冷解码 853.28 ms 的既有目标仍未达标，实际客户端停顿、非空历史及大备份
验收仍未运行。Planscope 保持 v0.8.0 / P5 / T-014 进行中，不关闭版本。
