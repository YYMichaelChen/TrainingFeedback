# 0.8.16 默认窗口排版修复交付记录

日期：2026-10-09（Asia/Shanghai）。用户明确要求“提交推送并release”，将
[默认窗口排版源码跟进](../0.8.15/layout-follow-up-2026-10-09.md)交付为补丁版本。

## 身份与文件

应用 `0.8.16`；schema `24`、catalog `070-illustrated-3`、contract `4` 不变。

- `src/training_feedback/ui/compact_widgets.py`、`group_session_page.py`：
  完整按钮宽度、训练卡片响应排列、图库文字居中和列宽均分；详细实现见源码记录。
- `pyproject.toml`、`src/training_feedback/__init__.py`：应用版本。
- `src/training_feedback/data/migrations.py`：仅扩展 schema 24 应用实现版本映射，
  不新增迁移或修改不支持/未来根拒绝规则。
- `README.md`、`docs/README.md`、`docs/history/README.md`：身份与交付路由。
- `docs/development-plan.md`、源码记录、本记录及[发布设计](../../releases/0.8.16/design.md)：
  产品规则、实现及候选证据；旧候选身份保持不变。

版本轮换审阅当前文档路由、保留版本与 schema 23/24、合同 v4 入口；仍被引用的
候选记录、合同、迁移和历史测试账本保留。未删除历史文件、退休开发根或访问用户数据。

## 验证

本次更新无具体应用打不开风险，源码开发、版本轮换、构建、分发和收尾共用同一次
更新范围：**应用测试 0 项；人工测试 0 项；重跑 0 次。** 不新增测试 scope/账本。
客户端排版、DPI、训练、更新交接及安装卸载未运行，不记通过，也不形成待补验收。
仅执行受影响 Python 文件 Ruff、文档链接/身份及差异静态检查。

## 交付准备

提交并推送 main 后，从干净源码使用 `packaging/build.ps1` 的 `-Installer` 参数构建，保留
载荷和安装包清单，再上传唯一 Setup 到稳定 v0.8.16 并设为 latest。实际成功结果
与精确身份在完成后追加；准备不等于构建或发布成功。

Planscope `v0.8.16` 记录交付和收尾；旧归档保持只读。GitHub 分发不建立正式兼容
支持、公共验收、外部内容审核、W4、个人数据转移或个人使用就绪状态。
