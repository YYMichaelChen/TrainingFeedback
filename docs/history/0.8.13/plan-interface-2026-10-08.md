# 0.8.13 计划界面与缩放源码后续改动

日期：2026-10-08（Asia/Shanghai）。本次用户要求更新计划弹窗尺寸、三栏响应布局
及应用内缩放。属于新的开发更新；不自动追加打包、版本升级或 GitHub 分发事件。

应用仍为 `0.8.13`，数据库 schema `24`、catalog `070-illustrated-3`、
plan/evidence contract `4` 不变。没有数据库迁移、外部合同修改、目录内容修改
或个人数据转移。[设计映射](../../designs/plan-interface-scaling.md)和
[产品规则](../../development-plan.md#411-plan-editor-sizing-and-interface-scale)承接规格。

## 改动文件

| 文件 | 改动 |
| --- | --- |
| `src/training_feedback/data/ui_preferences.py` | 独立本机界面配置，不读写训练数据库 |
| `src/training_feedback/ui/sizing.py`、`theme.py` | 单一字体逻辑单位、缩放管理、快捷键、默认原生 metrics 和 QSS 边界转换 |
| `src/training_feedback/ui/relative_widgets.py` | 独立滚动区、自适应参数格、竖向文本手柄、相对列宽和表格限高 |
| `src/training_feedback/ui/plan_layout.py` | 三栏、指导抽屉、动作胶囊和同级拖拽请求 |
| `src/training_feedback/ui/group_plan_page.py` | 折叠基本信息、固定底栏、逐组操作、保留备注、复用原保存/编辑流程 |
| `src/training_feedback/ui/exercise_reading.py` | 常驻指导锚点、图文单区滚动、比例图片和完整图注 |
| `src/training_feedback/ui/settings_page.py` | 缩放滑杆、模式、实时预览；设置正文滚动 |
| `src/training_feedback/ui/main_window.py`、`catalog_library_page.py`、`guidance_widgets.py`、`illustrations.py` | 现有显式尺寸改为共享相对单位 |
| `src/training_feedback/ui/group_training_page.py`、`group_session_page.py`、`library_lifecycle_page.py`、`release_updates.py` | 同步既有窗口/输入区的相对尺寸；不变更功能规则 |
| `tests/test_window_icon.py` | 原有启动构造场景加入真实主题初始化；界面配置重定向到临时合成路径 |
| `docs/development-plan.md`、`docs/README.md`、`docs/history/README.md`、本文与设计文档 | 产品规格与源码后续证据路由 |

没有打开、查找或操作真实训练根或旧训练数据库。未启动客户端或安装器，
未使用 GUI 自动化、脚本点击/按键或远程控制。

## 实际验证

具体启动风险：主窗口及设置页现在导入共享尺寸组件；入口主题初始化新增
`InterfaceScale`、原生 `UnitStyle` 与尺寸绑定。导入/API/对象初始化错误可能
在窗口创建前阻止打开应用。因此只选原有隔离主窗口启动构造节点，并把该节点
补入真实主题初始化；没有把设置操作或计划编辑操作并入场景。

```powershell
.venv/python.exe -m pytest tests/test_window_icon.py::test_required_application_icon_is_loaded_and_assigned_to_main_window --test-tier dev --test-scope plan-interface-20261008 --basetemp .tmp/pytest-plan-interface-20261008
```

结果：独立场景 **1 项，通过 1 项，执行 1 次，重跑 0 次；人工测试 0 项**。
使用隔离合成根、临时界面配置及 offscreen Qt，不操作客户端。
插件显示的 dev 1/30 是旧工具容量，本次许可仍受产品规范 §9.1 的启动上限约束。
该结果仅说明这条主题/主窗口启动构造路径通过，不证明客户端视觉或功能行为。

静态审阅和变更文件 Ruff、`git diff --check`、文档链接与身份检查通过。
未运行 DPI/缩放矩阵、布局/拖拽/滚轮/保存功能回归、全套 pytest 或安装验收；
未运行不记通过，也不形成必须补做的任务。其它问题随正常使用反馈修复。

## 交付与 Planscope

此次交付是工作树源码，没有新候选、安装包、提交、推送或 Release。
[既有 v0.8.13 Setup](github-release-2026-10-08.md) 不含此次改动，其构建身份和
旧证据保持原样；此处的启动结果不转移给该 Setup，也不建立公共验收、
内容审核、W4、正式兼容支持或个人使用就绪结论。

Planscope 本地 `v0.8.13` 记录本次源码后续任务，完成实现、有限验证与文档收尾。
旧同版本归档保持不变；本次后续上下文使用带日期的独立归档目录，清空活动状态。
可从源码与本文恢复的内容未重复存入 KNOWLEDGE 或 PROJECT。

## 后续发布授权

用户随后于 2026-10-08 明确要求“提交推送并release”。应用承接为补丁版本
`0.8.14`，schema、catalog 和 contract 不变。上述无安装包事实保留为最初源码
交付时点的记录；实际构建与 GitHub 分发身份转由
[0.8.14 开发记录](../0.8.14/development.md)承接。沿用本次更新累计 1 项启动
构造检查，不因版本轮换、构建或发布增加测试、人工观察或正式兼容承诺。
