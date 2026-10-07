# 0.8.12 更新退出修复与候选记录

## 身份与范围

- 日期：2026-10-07（Asia/Shanghai）。
- 应用：`0.8.12`；数据库 schema：`24`；目录：`070-illustrated-3`；
  plan/evidence contract：`4`。
- 用户明确授权提交、推送、新版安装包和 GitHub Release 分发。
- 实现依据：[2026-10-06 源码修复记录](../0.8.11/updater-follow-up-2026-10-06.md)
  与 [0.8.12 交付设计](../../releases/0.8.12/design.md)。

## 改动与版本轮换

| 文件 | 改动 |
| --- | --- |
| `src/training_feedback/application/update_launcher.py` | 新增外部启动器、继承的精确进程句柄、10 秒退出等待与超时终止、实际退出确认、就绪标记与失败日志 |
| `src/training_feedback/ui/release_updates.py` | 后台启动器交接和就绪轮询；移除进程内 daemon 退出线程，保留正常窗口关闭与 Qt 退出 |
| `src/training_feedback/application/release_updates.py` | 临时目录清理精确识别新增标记和日志，必须具有有效的应用所有权标记 |
| `pyproject.toml`、`src/training_feedback/__init__.py` | 应用更新为 0.8.12 |
| `src/training_feedback/data/migrations.py` | schema/application 实现映射延伸到 0.8.12；无迁移步骤或兼容支持变化 |
| `README.md`、`docs/README.md`、`docs/history/README.md` | 当前版本、分发和证据路由 |
| `docs/development-plan.md` | §9.1 明确外部退出和精确进程边界 |
| `docs/history/0.8.11/updater-follow-up-2026-10-06.md` | 保留原源码交付事实并关联追加授权 |
| `docs/releases/0.8.12/design.md`、本文及本版本候选/分发证据 | 交付范围、构建身份、实际结果及限制 |

启动器只在安装包已通过大小及 SHA-256 校验后安排；就绪前不请求退出。
只持有当前应用的等待/结束句柄，不通过程序名或 PID 重新选进程。超时结束
请求是异步操作，启动器必须再等待实际退出才能启动 Setup。失败不启动 Setup，
准备失败不退出应用。安装仍采用已有交互式 Setup 和独立数据根边界。

保留应用/schema/catalog/contract 四种身份的独立性。版本轮换仅审阅现有
证据、目录和合同引用，不删除仍有引用的历史记录或兼容入口，不清除测试账本；
没有新增正式兼容承诺、个人数据转移或 W4。未访问真实用户根或旧训练数据库。

## 实际验证

沿用 scope `2026-10-06-external-update-exit`：新增 ctypes/subprocess 导入、
启动器模块与 QTimer 初始化存在具体启动失败风险。已有
`tests/test_update_startup.py` 中的
`test_update_coordinator_does_not_block_main_window_startup` 于源码修复阶段
**1 项、1 次执行，1 passed in 1.62s，无重跑**，仅使用隔离合成数据根和
更新临时目录，无网络和客户端点击/按键。本次版本轮换及打包分发追加自动
应用测试 **0 项**，人工测试 **0 项**。

源码修复阶段改动文件 Ruff、Python 编译、PowerShell AST 语法及文档/差异
检查通过。版本身份与文档静态检查在提交前通过。构建只核对目录资源清单、
大小、哈希和必要打包资源，不运行旧功能检查或客户端。

构建审阅发现启动器 stdout 持续持有日志文件句柄，且工作目录落在待清理目录，
可能阻止 Windows 删除自身更新临时目录。改为每条日志使用立即关闭的文件
追加，并在系统 PowerShell 目录启动。此变动只影响交接后的文件占用，不改
启动导入、协调器初始化或原检查路径，未重跑应用测试。初次构建不分发；
最终安装包从包含此修正的干净提交重新构建，静态语法检查重新执行。

下载、交接、进程退出、外部终止、Setup 启动、覆盖安装与已安装客户端行为
均未运行，不记通过，也不是待补验收。当前机器具体退出阻塞位置没有日志证据。

## 候选与分发

最终安装包从干净源码 `8a3ae604bc93dcff9b42798036a4a39d924f8158` 构建。
构建完成时间 `2026-10-07T10:34:18Z`（北京时间 18:34:18）。工具链为
Python 3.12.14 AMD64、PySide6 6.11.2、PyInstaller 6.22.2、hooks 2026.7
和 Inno Setup 6.7.3。

| 项目 | 实际值 |
| --- | --- |
| Setup | `dist/installer/TrainingFeedback-0.8.12-Setup.exe` |
| 大小 | 85,693,750 bytes |
| Setup SHA-256 | `22fc750d5773fd9442ee1e29e7644747544786639101c72d0e9d0800d33235f6` |
| 载荷 EXE SHA-256 | `bde36912794d11a9f6c2f5270c41b1df2dffb7b7498277cb98bb26c99df90d64` |
| Setup / EXE 签名 | NotSigned / NotSigned |
| 载荷文件数 | 298 |
| source_dirty | false |

[载荷清单](payload-build-manifest.json)和[安装包清单](installer-build-manifest.json)
保留完整来源及逐文件摘要。构建资源检查通过，静态 PyInstaller 清单包含
`training_feedback.application.update_launcher`；未运行任何客户端或 Setup。
原 v0.8.11 候选证据不适用于本次新安装包。

安装包和清单的构建身份是实测文件事实，不是更新退出、安装或客户端行为通过。
[GitHub 分发记录](github-release-2026-10-07.md)记录唯一附件与公开 latest 响应。
稳定版 v0.8.12 于北京时间 2026-10-07 18:37:03 公开，标签目标
`03e957cf8a9176fe4a163f991967c7bcc269b969` 仅在构建源之后追加候选记录和清单，
不改变应用载荷。GitHub 返回的附件大小和摘要与上述最终安装包完全相同。
不声明正式兼容基线、公共验收、外部内容审核、个人数据转移或 W4。

本地 Planscope v0.8.12 完成源码、构建及分发任务；收尾摘要将执行状态路由到
本记录和分发记录，并通过已安装 plan.py 同步、检查和关闭归档，无新 finding。
规划状态不替代规范或候选证据，不因未运行的客户端行为留下验收待办。
