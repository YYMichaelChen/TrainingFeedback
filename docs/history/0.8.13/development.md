# 0.8.13 连续计划与指导阅读开发记录

日期：2026-10-08（Asia/Shanghai）。本次用户授权修复数字转换报错、取消训练日
交互及更正动作详情内容。应用 `0.8.13`、schema `24`、目录 `070-illustrated-3`、
plan/evidence contract `4`。[设计范围](../../releases/0.8.13/design.md)与
[产品规范](../../development-plan.md)承接持久规则。

## 改动文件

| 文件 | 改动 |
| --- | --- |
| `src/training_feedback/domain/group_plans.py` | 旧容器的连续动作投影；处方休息适用性规则 |
| `src/training_feedback/application/group_plan_service.py` | 精确内容及校验图片的只读服务 |
| `src/training_feedback/application/group_session_service.py`、`src/training_feedback/domain/session_controller.py` | UI 可预览、确认并开始整个计划，冻结完整顺序及原版本 |
| `src/training_feedback/ui/group_plan_page.py` | 平面动作树、指导图文阅读、字段中文错误、不适用休息、编辑中保存保护 |
| `src/training_feedback/ui/group_session_page.py`、`src/training_feedback/ui/plan_presentation.py` | 按计划选择和展示连续动作 |
| `src/training_feedback/ui/labels.py`、`src/training_feedback/ui/library_lifecycle_page.py` | 移除训练日交互和展示文案 |
| `src/training_feedback/data/group_plan_handoff.py` | Markdown 正文直接显示连续动作；JSON 结构和原事实保留 |
| `pyproject.toml`、`src/training_feedback/__init__.py`、`src/training_feedback/data/migrations.py` | 应用版本及实现映射；无新增 schema、迁移或兼容承诺 |
| `README.md`、`docs/README.md`、`docs/history/README.md` | 当前身份及证据路由 |
| `docs/development-plan.md`、`docs/initial-exercises-and-plan.md` | 连续计划规则、指导阅读与输入含义；移除提案中的训练日名称 |
| 本文及设计文档 | 源码交付范围和实际证据 |

动作/member ID、内容引用、指导、剂量和备注保留；仅待保存的编辑副本重排容器和
顶层顺序。已启用版本、历史和原始导入文件不改写。单次保存及开始训练继续由
服务事务提交，训练状态仍归 controller。未读取真实用户数据或旧训练数据库。

## 验证与交付限制

本次修改的是交互、数字解析与训练开始用例，复用已有阅读组件；不添加启动依赖、
必需资源、根初始化或启动对象。没有具体启动失败因果链，按产品规范 §9.1：
**应用自动测试 0 项，人工测试 0 项，重跑 0 次**。

变更 Python 文件 Ruff 通过；文档路径、链接和版本身份检查通过（96 个 Markdown
文件）；`git diff --check` 通过。初次 Ruff 发现导入顺序和一行过长，已修正；
后续相关输入/展示边界调整后只复查改动文件并通过。静态检查不代表客户端行为。
未运行处方保存、界面操作、训练模拟或旧版本功能回归；
这些不是通过，也不形成待补验收。没有客户端自动化或额外用户手测任务。

源码交付时未构建安装包、提交、推送或发布 GitHub Release，当时最新分发为 `v0.8.12`；
既有候选证据只属于其精确构建，不证明当前源码的客户端行为、公共验收、
外部内容审核、W4、正式兼容支持或个人数据转移。版本轮换保留仍有引用的历史、
合同、schema 入口及测试账本；没有进行旧数据发现、迁移或清理。

本地 Planscope `v0.8.13` 用于此次源码工作，阶段完成后归档并清空活动发布；
没有将可从源码和本文恢复的内容重复存为知识结论。

## 追加分发授权

用户于 2026-10-08 明确授权“提交推送并 release 更新”。此次追加提交、推送、
构建干净源码的 Setup 及 GitHub Release 分发。构建和发布不扩大同一次更新的
测试范围：应用自动测试累计 0 项、人工测试累计 0 项。实际候选与公开附件身份
将在完成后记录；当前尚不把准备动作记为分发成功。
