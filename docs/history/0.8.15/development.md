# 0.8.15 紧凑界面交付开发记录

日期：2026-10-09（Asia/Shanghai）。用户明确要求“提交推送并release”，
将[紧凑界面源码跟进](../0.8.14/compact-interface-2026-10-08.md)交付为补丁版本。

## 身份与改动文件

应用 `0.8.15`；schema `24`、catalog `070-illustrated-3`、contract `4` 不变。
源码改动文件和最终窗口/字号规则在上述源码记录与
[发布设计](../../releases/0.8.15/design.md)中列明。本次额外更新：

- `pyproject.toml`、`src/training_feedback/__init__.py`：应用版本。
- `src/training_feedback/data/migrations.py`：仅扩展 schema 24 的应用实现版本
  映射，不新增迁移、不改变拒绝未来或不支持根的边界。
- `README.md`、`docs/README.md`、`docs/history/README.md`：当前身份及路由。
- `docs/releases/0.8.15/design.md`、本记录：发布设计及候选/分发证据。
- 原界面设计与源码记录追加承接版本路由，旧安装包证据保持原样。

版本轮换审阅当前文档路由、已引用历史版本材料、schema 23/24 与 v4 合同；
仍被引用的候选记录、schema 入口、合同和测试账本保留，未删除历史材料，
未扩大旧版本兼容义务或访问用户数据。

## 验证

沿用更新 scope `compact-interface-20261008`。源码开发及用户澄清后累计
**1 个独立启动构造场景通过，执行 2 次（原检查重跑 1 次），人工测试 0 项**。
版本元数据及实现映射调整、构建和发布新增应用检查 0 项；通过后不再重跑。
相关 Python Ruff、文档链接/身份和差异静态检查通过。

客户端布局、悬停、跨屏/DPI、动作编辑保存、训练、更新交接、安装及卸载未
操作或观察，不记通过，也不形成必须补测的收尾工作。

## 提交与分发准备

用户授权提交并推送 main；从干净源码构建 Windows Setup，保留载荷和安装包
清单，将唯一 `TrainingFeedback-0.8.15-Setup.exe` 上传稳定 `v0.8.15`，
核对 GitHub digest 和不携带 Authorization 的公开 latest 响应。
实际构建、提交、附件与公开身份将在完成后记录；准备不等于发布成功。

本地 Planscope `v0.8.15` 记录交付阶段；旧跟进归档保持只读。GitHub 分发不
声明正式兼容支持、公共验收、外部内容审核、W4 或个人数据转移。

## 干净安装包候选

源码提交 `22acd710a5a89da216f50da550722ed99e795ec0` 已推送 main。
工作树干净后使用 `packaging/build.ps1` 的 `-Installer` 参数构建一次成功，未启动程序或 Setup。

| 项目 | 实际值 |
| --- | --- |
| Setup | `dist/installer/TrainingFeedback-0.8.15-Setup.exe` |
| SHA-256 | `4aa81c4c6e517a8e1958ef36c4ce59fb96da520d558d707cae47025b6e1484bf` |
| 大小 | 85,739,870 bytes |
| 签名 | NotSigned |
| 干净构建源码 | `22acd710a5a89da216f50da550722ed99e795ec0` |
| 构建时间 UTC | `2026-10-08T16:11:29Z` |
| 构建时间 Asia/Shanghai | 2026-10-09 00:11:29 |
| Python / PySide6 | 3.12.14 / 6.11.2 |
| 载荷文件数 | 298 |
| 源码状态 | `source_dirty=false` |

保存[载荷清单](payload-build-manifest.json)与[安装包清单](installer-build-manifest.json)。
本地实际 Setup 哈希、大小、应用版本与清单一致。构建流程核对受控工具链、
必需资源、只读内置目录和程序所有权清单，不混入用户数据库或 locator。
这些构建检查不证明界面、安装或更新行为，新增应用/人工测试均为 0 项。
