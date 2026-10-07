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
检查通过。版本身份与文档静态检查在提交前执行。构建只核对目录资源清单、
大小、哈希和必要打包资源，不运行旧功能检查或客户端。

下载、交接、进程退出、外部终止、Setup 启动、覆盖安装与已安装客户端行为
均未运行，不记通过，也不是待补验收。当前机器具体退出阻塞位置没有日志证据。

## 候选与分发

安装包将从干净源码提交构建；实际源提交、大小、摘要、签名、清单与 GitHub
asset 身份在完成后追加。本地 Planscope v0.8.12 记录版本准备、构建、发布和
收尾阶段；执行状态不替代上述权威规范或候选证据。
