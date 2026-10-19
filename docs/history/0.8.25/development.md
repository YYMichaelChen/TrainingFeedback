# 0.8.25 开发记录

日期：2026-10-20（Asia/Shanghai）。事件：开发更新、应用补丁版本升级和用户明确授权的
GitHub Release 分发。本期按
[全项目审视与版本安排](../../designs/project-review-roadmap-2026-10.md)完成长期读取效率
与维护配置，不扩展正式兼容支持、外部内容审核、W4 或个人数据转移结论。

## 实现及身份

- 会话仓储新增轻量历史摘要读取，训练主页只用会话 ID、日期、状态和冻结计划名填充
  列表，保留仍存在的选中 ID；仅在显示选中项时读取完整会话。反馈按钮只读取该会话的
  终态／日期／是否已提交和推导部位所需的冻结 occurrence 字段，不再遍历并构造全部
  历史。完整历史显示、指导、备注更正和导出仍使用原详情读取，用户原文、实际记录、
  事件、批次、冻结解释和较早会话导出均未裁剪；未做性能改善百分比声明。
- 现有根打开改为一次协调准备：只读验证数据根、当前 library model 和历史恢复状态后，
  把唯一实际数据库连接交给 `LibraryContext`。数据库层在持有根租约时再次检查实时 schema
  并执行迁移；不复用“已检查”缓存，也不再先开一个迁移后立即关闭的临时连接。失败会
  释放已打开的数据库／catalog，future／unsupported 根仍在业务写入前拒绝。
- `pyproject.toml` 的通用 setuptools 包资源增加 `ui/*.ico`，与运行时
  `ui/TrainingFeedback.ico` 加载路径一致；PyInstaller 的显式资源和 Windows 支持范围
  没有扩大。
- pytest 预算插件保留旧 tier/profile 的解释容量和原账本，但当前执行必须显式提供
  `文件::测试` 节点，不论 tier 都以同一 scope 的最多 3 个唯一节点为硬上限。旧政策
  账本只能重跑既有节点，不能追加；插件无法识别的脚本场景仍须人工合并计数。
- 产品规范同步根打开、摘要／详情读取与反馈资格边界，并把 §12.11 残留的
  “version-1 edit document”修正为当前内部格式 2。应用版本为 `0.8.25`；schema `26`、
  内部编辑格式 `2`、plan/evidence contract `5`、catalog `070-illustrated-3` 均不变。
  没有 DDL、迁移步骤、外部 wire schema、内置动作／指导／图片或冻结训练事实变化。

## 实际验证与边界

本次稳定 scope：`update-0825-maintenance`。现有根启动协调从两次完整扫描和临时数据库
打开改为一次准备并转移实际连接所有权，若资源交接或异常映射有误会导致 locator 启动
无法进入应用。因此选择 [tests/test_bootstrap.py](../../../tests/test_bootstrap.py) 中唯一
直接相关合成根节点 `test_open_from_locator_reopens_current_root_and_is_idempotent`，首次执行
通过（1 passed，0.62s），没有失败或重跑；预算插件同时显示 1/3 个显式节点并写入同一
scope 账本。达到所选风险结果后停止。

应用测试 1 项；pytest 1 次；人工测试 0 项。没有使用 GUI 自动化、脚本点击／按键、
客户端操作、真实用户数据或旧项目数据库。历史摘要、反馈资格、选择保持、完整导出、
包安装资源和 UI 行为未作功能测试，不记通过；按当前 §9.1 政策也不是待补验收。

修改范围 Ruff 通过；文档／身份脚本通过 134 个 Markdown 文件；Git 差异检查通过。
候选构建结果在精确源码提交后补记；构建、上传和 release 收尾不增加应用或人工测试
额度。

## 候选与分发

源码提交 `7a7d76e1e22cb0052009558b074c70a7b97b7bb6` 先推送到 `origin/main`，工作树
干净后一次完成目录载荷与 Inno Setup 构建。候选含 301 个载荷文件；安装包为
`TrainingFeedback-0.8.25-Setup.exe`，85,905,339 字节，SHA-256
`7df906756e883eedd284d5285adbf972f70f58a0ec32331a597b66fb6d963aee`，Authenticode
状态 NotSigned。构建过程确认包内包含 `training_feedback/ui/TrainingFeedback.ico`，
未运行安装包或客户端。

用户授权的稳定 [GitHub Release v0.8.25](github-release-2026-10-20.md) 已发布为 latest，
tag 指向同一构建提交且只有一个 Setup 附件；公共未授权 API 返回的名称、大小和 digest
与本地清单一致。分发不改变本节验证数量，也不声明正式兼容或公共验收。
