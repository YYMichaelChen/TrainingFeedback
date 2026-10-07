# 2026-10-06 更新退出修复（源码）

## 用户反馈与判断边界

用户再次报告：应用内下载更新后无法自动关闭，手动关闭应用才会弹出安装程序。
本次反馈没有提供运行版本或退出现场日志。该现象表明等待旧进程结束后启动
Setup 的路径能够工作，但不能确定旧进程的具体阻塞位置。

0.8.8 和 0.8.10 的历史修复分别使用 Qt 定时器及进程内 daemon 线程兜底。
后者虽然不依赖 Qt 事件循环，仍依赖 Python 线程得到执行；不能覆盖整个解释器
退出阶段。[Python 线程文档](https://docs.python.org/3/library/threading.html)
说明 daemon 线程会在关闭时被停止。此处是源码确认的机制缺口，不是对用户
机器上具体阻塞位置的已证实诊断。此前隔离启动检查未验证更新退出。

## 本次实现

- 新增 `src/training_feedback/application/update_launcher.py`：后台 PowerShell
  接收当前进程的继承句柄，只有等待和结束权限。使用句柄绑定本次进程，
  不按程序名或 PID 重新搜索，不结束其它实例或进程树。
- `src/training_feedback/ui/release_updates.py`：删除进程内退出线程，改用
  `subprocess.Popen` 启动隐藏启动器；异步等待其完成原生 API 准备并写出
  就绪标记后，才关闭窗口并请求正常退出。启动失败、准备失败或超时保持
  应用打开；未确认停止的启动器禁止再次交接。
- 外部启动器给正常退出 10 秒；超时调用 Windows `TerminateProcess`，随后
  再等待进程句柄变成已退出状态。结束请求成功不等于进程已退出，等待失败
  不启动 Setup。正常结束与超时结束都只能在确认退出后启动安装程序。
- `src/training_feedback/application/release_updates.py`：精确识别新增就绪标记
  和日志；这些文件必须与有效的本应用目录标记共同存在才可清理。
  启动器失败时保留日志和已验证 Setup，后续启动按既有边界尽力清理。
- `docs/development-plan.md`：在 §9.1 更新安装条款中明确外部退出责任。

使用 [DuplicateHandle](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-duplicatehandle)
及 Python 显式继承句柄列表传递目标；等待与异步终止遵循
[WaitForSingleObject](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject)
和 [TerminateProcess](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-terminateprocess)
的语义。Setup 仍使用既有交互式安装流程。

## 身份、验证与交付

本次是源码开发修复，没有应用版本轮换、打包、GitHub 上传或正式发布声明。
应用版本保留 `0.8.11`，schema `24`、catalog `070-illustrated-3`、contract `4`
未改变；不修改用户文本、个人事实或数据根，不访问真实或旧训练数据库。
已发布的 v0.8.11 安装包不包含本次修改；旧进程更新时也仍执行旧的更新器。

具体启动风险：原启动导入链新增 ctypes/subprocess 模块和更新启动器模块，
协调器初始化新增 QTimer 及槽连接；名称、导入或构造错误可能阻止主窗口打开。
仅选择已有的隔离无网络启动场景，使用 scope
`2026-10-06-external-update-exit`，合成数据根和更新临时目录。

实际结果：已有 `tests/test_update_startup.py` 中的
`test_update_coordinator_does_not_block_main_window_startup` 场景
**1 项、1 次执行，1 passed in 1.62s，无重跑**。仅构造协调器和合成根主窗口，
没有网络请求、客户端点击、键盘操作或更新器执行。

改动 Python 文件 Ruff、Python 编译、文档链接/路径/身份与差异空白检查通过。
从源码提取 PowerShell 字符串进行 AST 语法检查，未执行启动器或原生 API。
更新下载、就绪交接、外部终止、安装程序启动及安装行为未运行，不记通过，
也不列为待补验收。人工测试 **0 项**。

本地 INDEX 无活动发布。本次范围是局部源码修复，没有新建发布计划或修改
Planscope 执行状态；该记录拥有本次事实，不改写旧候选证据。

## 2026-10-07 追加交付授权

用户随后明确要求提交、推送并 release 新版程序。本次修复归入应用
[0.8.12](../0.8.12/development.md)，沿用同一启动检查 scope 和已执行结果；
版本轮换、构建和 GitHub 分发不追加应用或人工测试。上述 2026-10-06
源码交付状态保留为当时事实，后续候选与分发身份由 0.8.12 记录拥有。
