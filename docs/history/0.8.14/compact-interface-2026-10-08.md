# QHD 基准与独立动作框源码跟进

日期：2026-10-08（Asia/Shanghai）。用户反馈默认字号偏大，并提供训练、计划、
编辑、设置及动作条目悬停遮挡截图。用户随后明确：在其 3840×2160 屏幕上，
应用默认窗口应是 2560×1440、16:9；其他屏幕按相同的 2/3 窗口比例适配。
这不是随分辨率放大字号的要求。本次事件为普通源码开发更新，未请求新安装包、
版本轮换、提交推送或 GitHub 分发。

## 实现与改动文件

产品规则由[产品规范 §4.1.1](../../development-plan.md#411-plan-editor-sizing-and-interface-scale)
拥有；原生实现映射由[界面设计](../../designs/plan-interface-scaling.md)路由。

- `src/training_feedback/ui/sizing.py`：正文基准从约 16 降为 14 逻辑像素，
  Qt 处理系统 DPI，保留本机 80%–200% 自定义字号偏好。澄清后删除第一轮的
  分辨率字号倍率和换屏信号；`initial_window_size` 使用屏幕逻辑宽高的 2/3，
  保持 16:9，在物理 4K 屏幕上对应物理 2560×1440 客户区。其他比例按较小轴
  容纳，并以可用屏幕 96% 为上限。默认窗口尺寸不受字号百分比影响。
  编辑弹窗按默认窗口区域的 85%/88% 初始化，且不超过该区域。
- `src/training_feedback/ui/theme.py`、`main_window.py`：减少标题、按钮、侧栏及
  页边距；主窗口初始大小澄清后改为上述 16:9 屏幕比例，替代第一轮 104u×64u。
- 新增 `src/training_feedback/ui/compact_widgets.py`：原生自动换行操作栏，及按
  当前字体/宽度测量的独立圆角条目；文字不省略，悬停、选中和键盘焦点各有
  明确状态。图库列宽和高度随窗口、字体和文字变化重算。
- `catalog_library_page.py`：动作图库使用独立框，批量栏自动换行；移除旧固定
  grid 对每个条目的尺寸快照。
- `group_plan_page.py`、`plan_layout.py`：计划版本、动作多选、组成员和动作
  下拉复用独立框；计划工具栏换行；编辑三栏按实际栏区 96u/64u 断点响应，
  指导栏为 22u–30u，减少狭窄栏区挤压。
- `group_session_page.py`：开始/恢复与历史分成两卡，宽度不足 66u 时上下堆叠。
- `group_training_page.py`：结果、实做、保存及训练结束操作栏使用自然按钮宽度
  并自动换行。
- `settings_page.py`：内容限宽、数据目录按钮紧凑排列，说明新的分辨率基准。
- `docs/development-plan.md`、`docs/designs/plan-interface-scaling.md`、
  `docs/README.md`、`docs/history/README.md` 和本记录：同步规则、实现与证据路由。

## 实际验证

第一轮具体启动风险：`InterfaceScale` 在主题初始化中新增屏幕信号连接；主窗口首次
构造训练页时会创建新操作栏及布局。这些 Python/Qt 构造错误可能阻止应用打开。
仅选择现有的一项隔离主题/主窗口构造场景：

```powershell
./.venv/python.exe -m pytest tests/test_window_icon.py::test_required_application_icon_is_loaded_and_assigned_to_main_window --test-tier dev --test-scope compact-interface-20261008 --basetemp .tmp/pytest-compact-interface-20261008
```

第一轮实际 **1 项通过，执行 1 次，重跑 0 次；人工测试 0 项**。用例使用临时
`QSettings` 文件和独立合成训练根，不读取真实数据或机器界面偏好。通过后停止。
改动 Python 文件 Ruff、差异检查和文档链接/身份静态检查通过。

用户澄清后，新增 `initial_window_size` 会在主窗口启动构造时调用 Qt 屏幕几何
及 `resize(QSize)`；这里的 API 或返回值错误可能阻止打开。沿用同一 scope，
只重跑直接受影响的原节点一次并通过。本次更新累计仍为 **1 个独立场景，
共执行 2 次，重跑 1 次；人工测试 0 项**，没有扩大场景或另建测试额度。
第二次结果只说明澄清后源码的启动构造，不证明窗口像素、DPI 或客户端布局。

未执行客户端操作、界面绘制、悬停、跨屏、各分辨率、编辑保存或训练功能检查，
不记通过，也不形成待补任务。没有 GUI 自动化或追加用户验收清单。

## 身份与交付限制

应用仍为 `0.8.14`，schema `24`、catalog `070-illustrated-3`、contract `4`
均未改动。没有修改业务规则、用户原文、处方、数据根或数据写入路径。
现有 Setup 与 GitHub Release 仍来自旧的精确构建 `b09b611`，不包含本次源码
改动；既有候选证据不转移。本次不建立公共验收、正式兼容支持、内容审核、W4
或个人数据转移状态。

本地 Planscope 使用独立的 `v0.8.14-compact-interface-2026-10-08` 执行目录，
避免覆盖旧 `v0.8.14` 归档；实现和记录完成后关闭并归档，INDEX 恢复无活动版本。
`plan.py doctor` 确认两阶段、摘要与全部收尾项完成；`close` 命令仅接受
`vX.Y[.Z]`，拒绝本次跟进目录名称。因此核对新源/目标均位于本项目 `.planning/`
且目标不存在后，仅移动本次目录；使用已安装 helper 的 `clear_active_release`
清除活动投影并再次运行 doctor。未覆盖或改写既有发布归档。
这次局部澄清直接同步源码和上述权威文档，不重开或改写已归档规划；INDEX
继续无活动版本，取消的客户端检查不成为收尾阻塞。

用户随后于 2026-10-09 明确要求“提交推送并release”，本源码跟进由
[0.8.15 开发记录](../0.8.15/development.md)承接；不修改旧 Setup 的身份或证据。
