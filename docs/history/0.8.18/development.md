# 0.8.18 计划编辑布局交付记录

日期：2026-10-10（Asia/Shanghai）。用户明确要求“提交推送并release”，承接
[计划编辑列宽源码跟进](../../designs/plan-interface-scaling.md#2026-10-09-编辑区宽度源码跟进)。

## 身份与修改

应用 `0.8.18`；schema `24`、catalog `070-illustrated-3`、contract `4` 不变。

- `src/training_feedback/ui/relative_widgets.py`：按各列自身的表头、控件和相对下限
  分配宽度，短列保持紧凑，备注接收余宽；表格内横向滚动、预留高度并保护重入。
- `src/training_feedback/ui/group_plan_page.py`：指定短列、保持上方表单换行，剂量和
  成员操作使用自动换行按钮栏；引用统一文案。
- `src/training_feedback/ui/theme.py`、`src/training_feedback/ui/labels.py`：水平滚动条
  对比度和可拖动区域，明确组序和动作结束后休息的文案。
- `pyproject.toml`、`src/training_feedback/__init__.py`：应用补丁版本；
  `src/training_feedback/data/migrations.py` 只扩展 schema 24 的应用实现编号映射。
- README、文档索引、版本历史、产品规范和[设计](../../releases/0.8.18/design.md)：
  当前身份、布局规则和交付证据。

轮换审阅保留的候选记录、schema 23/24 与合同 v4 入口；没有删除历史材料、
新增迁移、退休开发根或访问用户数据，旧数据库未发现、打开或修改。

## 验证与交付范围

源码修复、轮换、构建和分发共用同一次更新范围。无具体应用打不开风险：
**应用测试 0 项；人工测试 0 项；功能检查重跑 0 次**。不新增测试账本。
仅进行受影响源码 Ruff、文档链接／身份与 Git 差异静态检查；实际结果随交付记录。
编辑、保存、滚动、缩放、安装和更新未运行或观察，不记通过，不形成待补验收。

使用 `packaging/build.ps1` 的 `-Installer` 参数从已提交的干净源码构建，记录精确身份，
再上传唯一 Setup 至稳定 v0.8.18，并核对公开 latest API 的附件 digest。
准备不等于构建或发布成功；实际结果在完成后追加。

Planscope `v0.8.18` 跟踪构建、分发和收尾。GitHub 分发不声明正式兼容支持、
公共验收、外部内容审核、W4、个人数据转移或个人使用就绪。
