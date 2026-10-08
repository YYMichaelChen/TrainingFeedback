# 0.8.14 计划界面发布开发记录

日期：2026-10-08（Asia/Shanghai）。用户明确授权“提交推送并release”，
将[计划界面源码更新](../0.8.13/plan-interface-2026-10-08.md)承接为 `0.8.14`。
功能改动文件和源开发时的启动风险及结果保留在该记录，不覆盖已有 v0.8.13 候选。

## 身份与轮换

- 应用：`0.8.14`，更新 `pyproject.toml`、`src/training_feedback/__init__.py`。
- 数据库 schema：`24`，仅扩展 `src/training_feedback/data/migrations.py` 的实现版本映射，
  不新增或改变数据库迁移。
- Catalog：`070-illustrated-3`；plan/evidence contract：`4`，均无修改。
- 当前身份与设计路由：`README.md`、`docs/README.md`、`docs/history/README.md`、
  `docs/releases/0.8.14/design.md` 和 `docs/designs/plan-interface-scaling.md`。
- 产品规范 §12.12 同步共享相对单位断点和完整图注，不继续保留与源码冲突的旧表述。

版本轮换盘点既有版本文档、schema 23/24 入口、v2/v3/v4 合同及本地规划归档。
仍被现行文档或历史证据引用的材料保持原样；没有删除合同、测试账本或历史候选，
没有扩大旧版本兼容义务。没有查找、打开或修改真实训练根或旧训练数据库。

## 验证范围

本次更新稳定 scope 为 `plan-interface-20261008`。源开发已执行的独立启动构造
场景累计 **1 项通过，执行 1 次，重跑 0 次；人工测试 0 项**。
应用版本元数据与实现映射修改、构建和 GitHub 分发不增加启动或功能检查。
源码相关 Ruff、文档链接/身份及差异静态检查通过。安装包、客户端布局、DPI、
拖拽、输入保存、更新交接及安装行为均未操作或观察，不记通过，不形成补测任务。

## 提交和分发准备

用户授权提交源码并推送 main，然后从干净提交构建 Windows Setup、保留载荷和
安装包清单、上传稳定 `v0.8.14` 的唯一 Setup 并核对公开 latest API。
构建身份和公开附件身份在实际完成后追加；准备不等于发布成功。

本地 Planscope `v0.8.14` 只记录这次追加交付，沿用原验证范围；不重开旧归档。
GitHub 分发不声明正式兼容基线、公共验收、外部内容审核、W4 或个人数据转移。

## 干净安装包候选

源码提交 `b09b611a790f0647feecc8e3813351c45eaaa44c` 已推送 main。
工作树干净后使用 `packaging/build.ps1` 的 `-Installer` 参数构建一次成功；未启动客户端或 Setup。

| 项目 | 实际值 |
| --- | --- |
| Setup | `dist/installer/TrainingFeedback-0.8.14-Setup.exe` |
| SHA-256 | `26a5a403975e2dab7ce769e048abae04fb33faba7171579357e84e6ebca4169e` |
| 大小 | 85,727,665 bytes |
| 签名 | NotSigned |
| 干净构建源码 | `b09b611a790f0647feecc8e3813351c45eaaa44c` |
| 构建时间 UTC | `2026-10-08T10:57:52Z` |
| 构建时间 Asia/Shanghai | 2026-10-08 18:57:52 |
| Python / PySide6 | 3.12.14 / 6.11.2 |
| 载荷文件数 | 298 |
| 源码状态 | `source_dirty=false` |

保留[载荷清单](payload-build-manifest.json)和[安装包清单](installer-build-manifest.json)。
实际文件 SHA-256、大小、版本与清单一致；构建流程核对受控工具链、必需资源、
程序所有权文件及不混入用户数据库/locator，不运行应用功能场景。
沿用源开发累计 1 项启动构造通过、执行 1 次、人工测试 0 项；此次构建新增应用
测试 0 项、重跑 0 次。清单与构建事实不证明安装、缩放或已安装客户端行为。
