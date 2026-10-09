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

## 干净安装包候选

源码提交 `943bf42cd8b609ce710619cea28590438fbe3b8f` 已推送 main，工作树干净后
构建一次成功；没有启动应用或 Setup。受影响源码 Ruff、文档链接／身份和 Git 差异
静态检查通过。构建核对受控工具链、必需资源、目录和程序所有权载荷清单。

| 项目 | 实际值 |
| --- | --- |
| Setup | `dist/installer/TrainingFeedback-0.8.17-Setup.exe` |
| SHA-256 | `c83b8dc41c0efcf8f79ef75e9d616c73ec6856bf19cd4d22d27ccacbfafda233` |
| 大小 | 85,740,355 bytes |
| 签名 | NotSigned |
| 干净构建源码 | `943bf42cd8b609ce710619cea28590438fbe3b8f` |
| 构建时间 UTC | `2026-10-09T13:08:37Z` |
| 构建时间 Asia/Shanghai | 2026-10-09 21:08:37 |
| Python / PySide6 | 3.12.14 / 6.11.2 |
| 载荷文件数 | 298 |
| 源码状态 | `source_dirty=false` |

[载荷清单](payload-build-manifest.json)和[安装包清单](installer-build-manifest.json)
保留精确候选身份；实际 Setup 哈希、大小、版本与源码提交和清单相符。载荷只含
程序拥有的资源，不含用户数据库或 locator。应用／人工测试仍各 0 项；候选身份
和构建成功不证明客户端拖动、保存、流畅度或安装行为。

## GitHub 分发完成

候选证据提交 `c6604c1e6fdf4f132c06dbf20be1d2474534e5f4` 已推送 main，稳定
标签 `v0.8.17` 指向该提交。Release 于 2026-10-09 21:10:25（Asia/Shanghai）
公开并设为 latest；唯一 Setup 上传一次。草稿及不携带 Authorization 的公开
latest API 核对附件名、uploaded 状态、大小、digest 与本地清单一致；远端标签
目标一致。精确身份见[发布记录](github-release-2026-10-09.md)。

源码修复至发布收尾累计应用测试 0 项、人工测试 0 项；未运行项不记通过。
Planscope `v0.8.17` 完成后关闭并归档，INDEX 无活动版本；ROADMAP 路由本次
实际交付证据，旧归档保持只读。后续文档提交不改变安装包和稳定标签。
