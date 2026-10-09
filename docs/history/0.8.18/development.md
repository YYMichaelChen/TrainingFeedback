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

## 干净候选构建

源码 `905b5342e4917932d26889984c0e892887c10737` 已推送 main；干净工作树
构建一次成功。受影响源码 Ruff、文档链接／身份与 Git 差异静态检查通过。
文档检查曾因将命令参数识别为文件路径失败一次，修正文案后通过；这不是应用测试。

| 项目 | 实际值 |
| --- | --- |
| Setup | `dist/installer/TrainingFeedback-0.8.18-Setup.exe` |
| SHA-256 | `774751f0392362cf200d19cb58aab6ae9b039407903997734944711a9533b6d7` |
| 大小 | 85,734,511 bytes |
| 签名 | NotSigned |
| 干净源码 | `905b5342e4917932d26889984c0e892887c10737` |
| 载荷构建时间 UTC | `2026-10-09T16:30:20Z` |
| Setup 构建时间 UTC | `2026-10-09T16:30:51Z` |
| Setup 构建时间 Asia/Shanghai | 2026-10-10 00:30:51 |
| Python / PySide6 | 3.12.14 / 6.11.2 |
| 载荷文件数 | 298 |
| 源码状态 | `source_dirty=false` |

[载荷清单](payload-build-manifest.json)与[安装包清单](installer-build-manifest.json)
保存完整候选身份，实际 Setup 哈希、大小及源码身份与清单一致。构建核对受控工具链、
程序资源和程序所有权载荷；没有启动客户端或 Setup。应用／人工测试仍各 0 项。
构建成功和候选身份不证明客户端显示、编辑或安装行为。

## GitHub 分发完成

候选证据 `ddfe218d4c5cec8881df8eaf80927e8dbe177a45` 已推送 main，稳定标签
`v0.8.18` 指向该提交。唯一 Setup 上传一次，草稿核对唯一附件、uploaded 状态、
大小与 digest 后，于 2026-10-10 00:32:52（Asia/Shanghai）公开并设为 latest。
不携带 Authorization 的公开 latest API 核对上述身份与本地一致；远端标签一致。
完整身份与下载入口见[发布记录](github-release-2026-10-10.md)。

累计应用测试 0 项、人工测试 0 项、功能检查重跑 0 次；构建一次成功。
Planscope `v0.8.18` 完成关闭并归档，INDEX 无活动版本；ROADMAP 路由实际证据，
旧归档保持只读。后续文档提交不改变 Setup 或稳定标签。
