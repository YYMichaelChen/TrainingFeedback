# 客户端报错中文映射源码跟进

日期：2026-10-17 至 2026-10-18（Asia/Shanghai）。用户要求将可扫描到的报错在客户端映射成中文，
承接同次工作树中的[计划编辑修复](plan-editor-follow-up-2026-10-17.md)。

## 范围与修改文件

- `src/training_feedback/error_messages.py`：集中原有中文映射，补齐扫描发现的 221 条
  英文异常字面量和 11 条 SQL 触发器报错。模块仅依赖标准库，不导入 Qt、不访问数据。
  增加顺序、训练状态、枚举、数字、图片清单等动态文案，以及 JSON、字符编码、系统权限、
  文件路径和数据库错误的中文表达。未知错误提供中文说明并保留技术详情，不记成功。
- `src/training_feedback/ui/labels.py`：重新导出公共映射和展示函数，保持原调用入口；
  文案与规则分离，不更改用户输入或已保存的事实。
- `src/training_feedback/domain/group_plans.py`：格式校验失败时保留原异常作为原因；
  不改变校验内容、异常文本或计划格式。客户端据此显示中文字段位置和具体格式要求，
  不再直接展示英文验证器输出或整份错误实例。
- `src/training_feedback/main.py`、`src/training_feedback/ui/data_root_dialog.py`、
  `src/training_feedback/ui/main_window.py`、`src/training_feedback/ui/settings_page.py`、
  `src/training_feedback/ui/exercise_reading.py`：错误出口传递异常对象，保留错误类别和系统码；
  数据目录预览补上原来绕过映射的入口。
- `src/training_feedback/ui/catalog_library_page.py`、
  `src/training_feedback/ui/group_plan_page.py`、
  `src/training_feedback/ui/group_session_page.py`、
  `src/training_feedback/ui/group_training_page.py`、
  `src/training_feedback/ui/library_lifecycle_page.py`：现有操作错误出口使用统一映射，
  同时接住数据库操作异常；不添加吞掉所有程序异常的全局处理器。
- `src/training_feedback/ui/release_updates.py`：更新临时文件创建、下载落盘和安装启动失败
  使用中文原因，路径和错误码保留。
- `src/training_feedback/application/installer_cli.py`、
  `src/training_feedback/application/uninstall_cli.py`、`packaging/training_feedback.iss`：
  安装和卸载辅助程序输出中文失败原因，安装器自身的英文错误出口改成中文。
  机器状态、判断分支和清理授权保持原义，持久化恢复记录不改写。
- `tests/test_installation.py`：仅将原有辅助程序断言中的英文预期改为中文，未执行该用例。
- `docs/development-plan.md`、`docs/README.md` 与本记录：记录中文错误展示要求和证据入口。

## 实际验证

对应用 Python 源码做 AST 文本清点，并读取受控 SQL 源码中的触发器错误；
清点不导入、不执行应用，不访问数据库。发现的固定英文异常及触发器文案均有中文映射，
剩余未映射固定文案为 0。动态表达式逐项审阅，区分已中文化文案、系统错误、字段校验、
原样转交异常以及退出状态；没有把用户原文或技术标识误当成需全文翻译的错误。

受影响 Python 文件 Ruff 通过。文案补充时发现的长行和导入顺序已修正；
扫描脚本及源文件检查属于静态检查，未调用映射函数逐例执行功能验证。
文档链接／身份检查通过（119 个 Markdown 文件），Git 差异空白检查通过。

映射抽取只增加独立标准库模块，原入口保留重导出；静态审阅未发现循环导入或缺失依赖，
未识别需要运行应用检查的具体启动失败风险。**应用测试 0 项；人工测试 0 项；
功能检查重跑 0 次**。未启动客户端、安装器、卸载器或触发错误场景，未运行旧测试库，
未构建安装包。客户端实际显示未观察，不记为通过，也不形成待补验收。

应用 `0.8.18`、schema `24`、catalog `070-illustrated-3`、contract `4` 不变。
SQL 只读用于清点，没有迁移或外部格式变更；未访问个人数据根或旧训练数据库。
本次没有提交、推送或发布，已有 Setup 及其证据不包含此次源码修改。
不建立正式兼容、公共验收、外部内容审核、W4 或个人使用就绪结论。
Planscope INDEX 仍无活动版本，计划、知识和日志未变；没有重开已归档版本。
