# 0.8.21 开发记录

日期：2026-10-18（Asia/Shanghai）。事件：开发更新与应用／schema／合同版本升级。
本次按[左右交替设计](../../designs/alternating-side-prescriptions.md)交付源码，
同时保留工作区原有的未发布问题提示修复。没有构建、提交或发布新安装包。

- 应用 `0.8.21`，schema `26`，内部编辑格式 `2`，plan/evidence contract `5`。
- catalog `070-illustrated-3` 不变，90/90 原有指导及图片不变，不按名称改写计划。
- 已有 GitHub `v0.8.20` 安装包不包含本次源码，不能覆盖本次功能证据。

## 文件与行为

- `domain/execution_modes.py`、`group_plans.py`、`action_groups.py`、`plan_editing.py`：
  整体／分侧／交替、总量／每侧、每组起始规则、整数次校验、具体问题位置、组侧序约束；
  旧格式映射不造成虚假 AA，执行模式变化进入结构修订。缓存不参与有效处方。
- `contracts/plan-v5.schema.json`、`data/plan_contract.py`、`group_plan_handoff.py`、
  `application/group_plan_service.py`：v5 模板和帮助，v4 严格校验后转换为新草稿，预览说明
  转换并保留原字节；拒绝其它旧版和未来版。v5 证据明确携带冻结语义版本与对应 plan schema。
- `data/migrations.py`、`draft_documents.sql`、`group_plan_repository.py`、应用版本文件：
  新根和已有支持根同为 schema26；旧可编辑输入升级，原始文字／空白／缓存保留；活动
  版本、原件及冻结会话不改写。计划仓储使用实际格式标识，不再统一重建为 v4。
- `domain/group_execution.py`、`application/group_session_service.py`、
  `data/group_session_repository.py`：交替动作连续执行，每组实际记录关联原计划组号，
  总量和左右分别记录互斥，不推算未知侧。批量确认复用相同规则，撤回保留前像，暂停
  继续读取冻结步骤。新增会话携带精确指导引用及语义标识。
- `ui/group_plan_page.py`、`group_training_page.py`、`plan_presentation.py`、`labels.py`、
  `error_messages.py`、`data/group_session_handoff.py`：中文模式和口径选择，立即解释每组
  计划左右／合计，休息不适用时保留输入缓存；训练录入关联组号并明确总量或左右，历史
  和 Markdown 区分计划推算、用户确认处方、实填以及未记录。
- README、文档入口、产品规范、版本历史与本设计同步身份和行为；保留旧合同／schema
  基线，它们仍被严格 v4 导入、支持根升级或历史证据引用，未引入正式兼容承诺。

## 验证与边界

本次稳定 scope：`update-0821-alternating`。仅检查两个具体启动风险：新根初始化 DDL
及 schema25 旧编辑表迁移若失败会阻止打开。所选代码级节点：

1. `tests/test_startup_0819.py` 中的
   `test_new_root_initialization_has_required_edit_storage`。
2. `tests/test_startup_0821.py` 中的 `test_schema25_root_open_upgrades_edit_storage`。

实际执行 2 个独立场景，均通过，各执行 1 次、重跑 0 次（pytest 2 passed）。
未执行 schema23/24 场景或功能回归；不为额度增加场景。
人工测试 0 项，没有 GUI 自动化、计时或安装卸载检查。
未运行的功能检查不记通过，也不是待补验收。静态检查限于修改文件的 Ruff、文档链接／
身份一致性和 Git 差异；Ruff、文档检查和 `git diff --check` 通过。
所有根均为隔离合成根，不读取真实或旧项目数据库。

本次无候选构建；源码检查不证明客户端功能通过，不建立公共验收、外部内容审核、W4、
正式支持或个人数据转移结论。本地 Planscope 记录唯一活动 v0.8.21，收尾按实际完成状态
同步和归档，执行上下文不替代本文件或产品要求。

## 用户授权的构建与分发跟进

用户随后要求“提交推送并release”。源码已提交推送，干净构建一次成功；
本段为候选事实，公开后的 Release 身份另行记录。

| 项目 | 实际值 |
| --- | --- |
| 构建源码 | `bd8f1e71fa0629be683974984de9c34a1b34727e`，source_dirty=false |
| 安装包 | `TrainingFeedback-0.8.21-Setup.exe` |
| SHA-256 | `cb9f2af8997563c2a755bd05089bbff567b6204e871935771ee8c8b48759a605` |
| 大小 | 85,861,616 bytes |
| 签名 | NotSigned |
| 构建时间 UTC | `2026-10-18T06:39:21Z` |
| 构建时间 Asia/Shanghai | 2026-10-18 14:39:21 |

[载荷清单](payload-build-manifest.json)与[安装包清单](installer-build-manifest.json)
保存完整身份。已核对工具链、必需 SQL／中文资源／v5 合同载荷、目录文件哈希和
实际 Setup 的大小、SHA-256、签名及来源状态；没有运行 Setup 或客户端。
本次分发跟进新增应用测试 0 项、人工测试 0 项；整次更新仍仅有前述 2 项启动检查，
不能将其视为安装包或客户端功能已通过。没有新增正式兼容或公共支持承诺。
