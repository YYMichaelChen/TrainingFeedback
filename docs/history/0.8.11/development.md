# 0.8.11 动作阅读界面开发记录

## 身份与范围

- 日期：2026-10-04。
- 应用：`0.8.11`；数据库 schema：`24`；目录：`070-illustrated-3`；
  plan/evidence contract：`4`。
- 事件：用户授权的开发更新及应用版本轮换；源码开发完成后，用户于同日追加授权
  提交、推送、构建安装包和 GitHub Release 分发。
- 依据：[确认的阅读设计](../../designs/exercise-reading-redesign.md)与
  [本版本设计](../../releases/0.8.11/design.md)。
- 初次源码开发交付没有构建或分发。追加交付沿用同一验证范围；
  没有正式发布声明或个人数据状态变更。

## 实现与改动文件

| 文件 | 改动 |
| --- | --- |
| `src/training_feedback/ui/exercise_reading.py` | 新增独立阅读组件：单滚动区分组指导、双向适配图片、多图翻页、两行说明及完整原文弹窗、原图缩放查看器；760 逻辑像素宽度切换布局 |
| `src/training_feedback/ui/catalog_library_page.py` | 动作详情及外部审核阅读区接入新组件；管理按钮合并为分组菜单；新增内容信息及当前版本审核事件只读弹窗 |
| `src/training_feedback/ui/group_training_page.py` | 仅冻结指导弹窗接入新阅读区；训练执行页继续使用旧 GuidanceView、IllustrationLabel 及其原有记录操作 |
| `pyproject.toml`、`src/training_feedback/__init__.py` | 应用版本更新为 0.8.11 |
| `src/training_feedback/data/migrations.py` | 已实现 schema/application 映射延伸到 0.8.11；没有迁移步骤、schema 或支持政策变化 |
| `README.md`、`docs/README.md`、`docs/history/README.md` | 当前开发身份及文档路由；保留 v0.8.10 分发身份 |
| `docs/development-plan.md` | §12.12 归入已实现阅读行为及既有数据/服务边界 |
| `docs/designs/exercise-reading-redesign.md` | 保留已有确认方案并关联实施版本，区分原落档授权与后续开发授权 |
| `docs/releases/0.8.11/design.md`、本文 | 本次范围、启动风险、实际验证及证据限制 |
| `packaging/build.ps1`、`packaging/build_catalog.py` | 打包时仅比较目录资源清单、大小与哈希；保留原完整目录检查入口但不自动执行 |

指导保留字段原文、换行、步骤顺序与编号；安全字段默认展开，空字段显示
“未填写”。宽窄切换复用同一指导和图片区实例，保留阅读位置、折叠状态及图片页码。
图片绘制不使用原图尺寸决定页面高度；说明及翻页占用布局高度后，图片适应剩余区域。
长说明可以查看和复制完整原文。放大查看支持适应窗口、实际逻辑大小、10%～400%
手动缩放、滚轮、拖动及 Esc；适应窗口可以低于 10%。

菜单打开时刷新状态并捕获精确 LibraryTarget，执行前核对显示目标及内容存在性。
使用、启用、审核和内容维护保留各自服务与确认，未合并事务含义；失败后重新读取状态。
启用/停用只显示当前适用的一项。审核事件按记录时间倒序，仅使用当前内容的事件，
显示未知时间、原始备注及原件路径/摘要；无事件明确显示“当前内容版本暂无审核事件”。
内容信息展示来源、动作族/变体、显示与已选内容身份、目录版本和各图片资格。

动作库与审核图片通过现有服务校验及读取；冻结阅读仅调用会话图片服务，
没有最新目录回退。没有改写指导、替换图片、变更审核资格、触碰真实用户数据，
也没有访问旧训练数据库。动作卡片与训练执行布局不在改动范围内。

## 实际验证

具体启动风险：训练首页在主窗口创建时导入 `group_session_page.py`，继而导入
`group_training_page.py`；后者新增 `exercise_reading.py` 导入。新增 Qt 导入或模块
定义如果无效，可能阻止主窗口打开。因此仅选择已有的隔离启动场景：

```powershell
.\.venv\python.exe -m pytest tests/test_update_startup.py::test_update_coordinator_does_not_block_main_window_startup --test-tier dev --test-scope 2026-10-04-exercise-reading --basetemp .tmp/pytest-2026-10-04-exercise-reading
```

- 自动应用测试：**1 项，1 次执行，1 passed in 1.24 s，无重跑**。
  仅使用隔离合成根与无网络更新协调器，未操作导航、点击或按键。
  此检查覆盖启动导入与主窗口打开，不证明新阅读组件构造或界面功能通过。
- 人工测试：**0 项**。
- 改动 Python 文件 Ruff、Python 编译检查通过；文档链接/身份检查及
  `git diff --check` 通过。文档检查首次把行内 pytest 节点误识别为文件路径，
  分开标注文件与用例名称后重跑通过；没有重跑应用测试。
- 界面布局、宽窄切换、高 DPI、多图翻页、放大查看、菜单功能及安装行为均未运行，
  不记通过；按 §9.1 不安排额外检查，也不作为待补任务。

版本轮换仅审阅相关身份、文档引用及已有历史路由。原分发候选证据仍被引用，
没有删除历史记录、兼容入口、测试账本或任何数据根；版本号不产生新的兼容承诺。

## 候选与执行状态

首次源码交付没有 0.8.11 候选；后续安装包身份另行记录，
0.8.10 的候选结果不适用于这些源码变更。
不声明客户端效果、公共验收、外部内容审核、个人使用就绪或 W4 通过。

本次建立本地 v0.8.11 Planscope 发布，P1 完成阅读组件和接入，P2 完成身份与开发记录。
当前阶段、任务和下一步均通过已安装的 `plan.py sync` 投影到 INDEX。
开发范围完成后按流程生成 SUMMARY 并关闭归档；无不可从源码或文档恢复的新 finding。
本地计划不替代本记录，也不建立打包/分发义务。

## 追加授权后的候选构建

用户随后要求“提交推送并 release”。应用源码提交
`52c9fcef2594c03ee552fa060bb9c3cfda351bb3` 已推送到 main，安装包于
2026-10-04 从该干净提交构建（manifest 的 `source_dirty: false`）。

| 项目 | 实际值 |
| --- | --- |
| 安装包 | `TrainingFeedback-0.8.11-Setup.exe` |
| SHA-256 | `baa1e40c153c4ae69ca99e5f53b5d6019cd31481db5515777d511f4911549519` |
| 大小 | 85,689,267 bytes |
| 签名 | NotSigned |
| 构建时间 | `2026-10-04T08:32:04Z`（北京时间 16:32:04） |
| Python / 架构 | 3.12.14 / AMD64 |
| PySide6 | 6.11.2 |
| PyInstaller / hooks | 6.22.2 / 2026.7 |
| Inno Setup 编译器 | 用户安装的 Inno Setup 6 / ISCC.exe |
| 载荷文件数 | 298 |

构建命令：`pwsh -NoProfile -File packaging/build.ps1 -Installer`。
精确输出由[载荷构建清单](payload-build-manifest.json)及
[安装包构建清单](installer-build-manifest.json)保留。
安装包未运行，客户端未操作。构建过程只核对源目录与打包目录的 37 个资源文件
清单、字节数和 SHA-256，并生成载荷所有权/构建清单；没有执行完整目录图片解码
或领域规则验证。打包脚本改动的 Ruff、编译及文档检查通过。
本次更新仍累计为 1 项启动场景、1 次执行、无重跑；追加阶段应用测试 0 项，
人工测试 0 项。构建成功不表示安装行为或新阅读界面功能通过。
