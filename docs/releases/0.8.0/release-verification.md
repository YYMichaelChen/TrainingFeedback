# 0.8.0 发布回归风险选集

在首次发布 scope 执行前锁定（2026-09-30）。minor，唯一 scope
**release-0.8.0**，上限 100 parameter-expanded unique cases；同版本修复复用
这个 scope，不清账本。全 resident collect-only 为 264，不作为全套通过。

选中风险：

| 风险 | 明确选集 |
| --- | --- |
| 程序路径、安全归属、stale payload 删除、Qt-free 分派 | tests/test_installation.py 全部 24 |
| 精确根删除、所有权、链接/锁、换根/新增对象、进程崩溃和恢复 | tests/test_root_cleanup.py 全部 26 |
| 旧通道退役且 pending/未知/过期状态不变拒绝 | tests/test_one_time_reset.py 全部 5 |
| 当前初始化与事务、schema 边界 | tests/test_database.py 全部 3 |
| 当前根、错 marker、未来 config/schema、损坏 DB | test_data_root.py 中 5 项列入节点清单 |
| catalog 重建、hash/资源安全、跨根与失败回滚 | tests/test_070_catalog_storage.py 全部 11 |
| 缓存失效、100 草稿、名字/家族竞态、审核/图片资格与回滚 | tests/test_070_library_workflow.py 非 UI 17 |
| 测量库存不扫描未跟踪根 | test_inventory_never_enumerates_untracked_roots |
| 冻结计划、失败 pin 回滚、完成事实不可改、备份/恢复 | group plans/execution 中 4 节点 |
| 新根名称原文/路径预览与创建失败回滚 | test_new_root.py 中 2 节点 |

完整参数展开节点在 [release-nodeids.json](release-nodeids.json)。预期 98 unique
cases；以 collection 与 budget ledger 的实际结果核对，超限则不执行。

排除：客户端交互测试由 AGENTS.md 要求开发者手动操作，不能用自动点击/键盘
替代；其状态为 not run。未改变的 wire 格式、完整领域组合、调整建议 UI、
历史版本兼容专属场景不纳入本候选选集；保留仍有当前功能覆盖职责的 resident
用例，排除不等于通过。路径探测/空图算法的低风险重叠用例已有对应 dev 证据，
不把全部 resident 作为发布门槛。没有正式旧版本支持端点。

静态 checks、目录/安装包构建和 hash 核对单独记录，不占 pytest scope，
也不替代开发者手动客户端/安装/响应验收。

结果：唯一 release-0.8.0 minor scope **98/100 unique cases，98 passed**，
28.37 s。完整结果在本地 .tmp/pytest-release-0.8.0.log，budget ledger 保留。
Ruff、文档一致性与 diff 检查通过。精确候选身份在构建后进入版本历史；
安装和客户端手动检查仍 not run。

最终句柄安全复查收紧目录写共享，并在现有目录替换用例加入实际 Windows
写句柄拒绝检查。原 scope 内重跑受影响的 26 清理 + 2 程序清理 cases：
**28 passed，2.48 s**，累计仍为 98。其余未受该句柄改动影响的先前结果明确复用，
未重跑不冒充重复执行；最终候选从修复后的干净 source 构建。

## 2026-10-02 安装目录错误提示修复选集

开发者截图显示 0.8.0 安装目录页面预填旧测试程序目录，缺少程序归属清单时
直接显示英文 `FileNotFoundError`。这是错误提示失败，不能算安装通过。
截图未提供安装包 hash，不能据标题把它绑定到某个精确候选。

本次在执行前追加两个风险节点：缺少程序归属清单、缺少安装记录，分别验证
中文恢复步骤和检查前后程序文件不变。完整节点清单因此从 98 增至 100。
原有程序目录校验、归属、清理与 helper 分派受到影响，重跑
`tests/test_installation.py` 全部 26 项；同一 `release-0.8.0` minor scope
和原 ledger 继续使用，累计预期 100/100，不重建或拆分账本。
未受改动影响的旧结果明确复用。新候选的实际安装和完整中文弹窗由开发者
手动复验，代码测试与 Inno 编译不能代替。

实际执行：安装目录选集 **26 passed，0.52 s**；原 scope 累计 **100/100 unique
cases**。此前 98 个节点通过，本次追加的两个节点通过，其余未受影响结果复用。
