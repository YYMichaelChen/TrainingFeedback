# 0.8.17 计划排序与默认编辑交付记录

日期：2026-10-09（Asia/Shanghai）。用户明确要求“提交推送并release”，将
[计划编辑源码跟进](../0.8.16/plan-editor-follow-up-2026-10-09.md)交付为补丁版本。

## 身份与文件

应用 `0.8.17`；schema `24`、catalog `070-illustrated-3`、contract `4` 不变。

- `src/training_feedback/ui/plan_layout.py`、`group_plan_page.py` 和
  `src/training_feedback/domain/group_plans.py`：自有拖动、单次排序、默认编辑、
  输入保留、统一保存及按需加载指导；具体实现见源码记录。
- `pyproject.toml`、`src/training_feedback/__init__.py`：应用版本。
- `src/training_feedback/data/migrations.py`：仅扩展 schema 24 应用实现版本映射，
  不新增迁移或改变不支持／未来根拒绝路径。
- `README.md`、`docs/README.md`、`docs/history/README.md`：当前身份和交付路由。
- `docs/development-plan.md`、源码记录、本记录和[设计](../../releases/0.8.17/design.md)：
  产品规则、改动与本次候选证据。历史候选保持原身份。

版本轮换审阅文档路由、schema 23/24 和合同 v4 入口；保留仍被引用的历史候选、
合同和迁移，Git 历史保留其原编号。没有删除历史文件、退休开发根或访问用户数据。

## 验证

从源码修复到版本轮换、打包、分发和收尾共用本次更新范围。无具体启动失败风险：
**应用测试 0 项；人工测试 0 项；功能检查重跑 0 次**。未新增测试 scope 或账本。
只执行受影响 Python 文件 Ruff、文档链接／身份和 Git 差异静态检查。
拖动、导航、保存、动作组、客户端性能、安装与更新未运行，不记通过，也不形成待补验收。

## 交付准备

提交并推送 main 后，从干净源码使用 `packaging/build.ps1` 的 `-Installer` 参数构建，记录
完整候选身份，再将唯一 Setup 上传至稳定 v0.8.17 并设为 latest。准备不等于构建或
分发成功；实际身份和结果将在完成后追加。

Planscope `v0.8.17` 跟踪交付与收尾；旧归档保持只读。分发不建立正式兼容支持、
公共验收、外部内容审核、W4、个人数据转移或个人使用就绪状态。
