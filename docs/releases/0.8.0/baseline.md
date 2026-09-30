# v0.8.0 开发基线与引用审计

2026-09-30，T-003。原始样本、环境、逐次计时、分位数和调用分布在
[baseline.json](baseline.json)。此记录是开发测量，不是 0.8.0 候选/客户端验收。
测量时应用源码来自 `d0dd44f37afe7ed57db2f52ac7412320d5b11cfa`，工作区新增
测量工具、其测试与实施文档，应用源码没有改变；故记录 `source_dirty=true`。
工具 SHA-256 为 `242d0f651a01284fbca0c1549387008ab19d133972adc476bbd3a8ba46ecb8b0`。

## 可重复方法与边界

PowerShell 7，仓库 `.venv/python.exe`，Windows 11 x64 build 26200，
Intel Core i7-12700KF，Python 3.12.14，PySide6 6.11.2，jsonschema 4.26.0。
工具为 [measure_baseline.py](../../../packaging/measure_baseline.py)。重跑命令：

```powershell
& .venv/python.exe packaging/measure_baseline.py --samples 20 --custom-counts 0 100 > .tmp/baseline-v080.json
```

工具只盘点 `git ls-files` 列出的工作区文件，不枚举 `.git`、`.venv`、
`.planning`、`user_data` 或历史根；禁止读取跟踪文件中的链接/目录连接目标。
性能样本由工具在 `.tmp/measurements/baseline-*` 新分配的临时目录内创建，
只读使用本程序自有 catalog；关闭上下文后只回收工具刚创建的合成目录。
不接受用户根参数、不读取默认 locator、不创建 QApplication/窗口、不运行
点击/按键等客户端自动化。结果只包含类别、耗时、规模和源码函数名称。

每条路径 2 次预热、20 次计时，串行 wall clock，p50/p95 用 nearest-rank。
初轮定位后，在最终工具版本上重新测量；本记录仅使用最终轮，不混合挑选样本。
OS 文件缓存未清空；“冷”只表示清空服务层图片检查缓存，不能称磁盘冷启动。
fresh process 包含解释器/模块加载、打开上下文、关闭和进程退出；不等同于
启动到可操作窗口。cProfile 另采一轮定位，带测量开销，不代替无 profiler 的计时。

两组初始数据：36 个内置动作，以及 36 内置 + 100 个无图片合成自定义动作。
后者另建 20 个合成草稿计划；两组均没有训练历史、审批或个人事实。
浏览/搜索/计划列表计时先执行；保存路径先建立一个无图片合成 override，
再反复保存同一内容，数据库规模不随计时次数增长。备份/重开在此之后执行；
最终根大小分别为 483,537 / 1,011,921 bytes。保存和备份未复制内置目录图片。
新建根计时包括关闭上下文，每次是不同的空目标。

## 仓库与 payload 体积

以下是基线提交已有的 216 个跟踪文件，不包含本任务新增工具/证据。
字节按工作区实际内容计；没有删除文件，后续清理必须比较同一口径。

| 区域 | 文件数 | bytes |
| --- | ---: | ---: |
| docs | 23 | 272,115 |
| src（含目录/种子图片） | 149 | 101,616,840 |
| tests | 27 | 192,852 |
| packaging | 8 | 39,610 |
| content | 3 | 173,593 |
| icon | 1 | 44,695 |
| 根级配置/说明 | 5 | 16,226 |
| 合计 | 216 | 102,355,931（97.61 MiB） |

36 组完全相同的图片分别在 catalog/images 和 data/seed/images 中，
每组保留一个副本可减少 50,380,696 bytes（48.05 MiB）。原始 JSON 保存
每组路径与大小；该数字只表示潜在仓库重复体积，不是已实现的节省。

现有 `dist/TrainingFeedback.build-manifest.json` 属于历史 0.7.7、源码
`831f7edf2f80a062f5919223b10cada4037f577b`，其记录的 payload 为 295 文件、
176,740,757 bytes（168.55 MiB）。本次只读取 manifest，未复核当前 payload
或安装包 hash，不能用于 0.7.8/0.8.0 验收。新构建耗时和当前 payload 基线
均 `not run`；在实际打包批次再测量。当前 spec 仅显式收集 catalog 图片，
因此消除种子图片副本不会自动让 installer 减少 48.05 MiB。

## 依赖与保留/删除候选

运行时声明依赖为 PySide6 和 jsonschema；开发依赖 pytest/Ruff，构建固定
PyInstaller 6.22.2、hooks-contrib 2026.7。当前使用 QtCore/QtGui/QtWidgets，
历史 manifest 含 QtQuick/Qml/Pdf/opengl32sw 等大文件。其可能由 hook 或
DLL 传递引用收集，未证明可删；P3 必须结合实际分析 TOC/manifest 和构建回归。

| 候选 | 已找到的引用/责任 | 本轮决定与下一证据 |
| --- | --- | --- |
| 36 组种子/目录图片 | `seed/images.py` → `catalog_builder.py` → `packaging/build_catalog.py`；catalog manifest/读者需要目录资源 | 全部保留；T-008 先设计唯一源和可重复构建，再验证内容/hash 不变 |
| `upgrade_recovery.py` | 当前生产源码无 `UpgradeRecovery` 导入；`test_070_upgrade_recovery.py` 使用 | 退役候选；T-007 审计未完成升级拒绝与锁职责后决定，不凭无导入删除安全覆盖 |
| `one_time_reset.py` | `data_root.open_existing` 调用，schema23 journal 仍有当前残留清理职责 | 保留至 T-007 明确边界；不可把 current journal 安全当作旧版承诺直接删 |
| `conversion_repository.py` | 当前 `group_plan_repository.py` 和 `group_plan_handoff.py` 读取转换登记 | 保留；仍有当前计划来源事实/导出引用 |
| plan-v2/v3 contracts、group execution fixture | contracts 为自有运行资源，v3 当前；fixture 验证当前展开语义 | T-007 分开审计旧版通道与当前安全；不整体删历史命名文件 |
| 历史 docs | 当前仅 23 个 docs 文件，权威文档/近版本证据已有路由 | 按 retention 审计；体积收益小于图片，不能删除仍有效规则/未运行事实 |
| Qt payload 大文件 | 历史 manifest、PyInstaller hooks/二进制传递引用 | 保留；构建和依赖证据不足，当前不设置猜测性 exclude |

这张表是首次审计，尚无任何删除批准或完整无引用证明。后续批次需记录
逐文件删除清单、引用审计、前后 bytes、当前功能回归和实际打包结果。

## 服务层响应结果

单位 ms，以下为 p50 / p95；完整 raw/max 见 JSON。

| 路径 | 36 内置，0 草稿 | 36 内置 + 100 自定义，20 草稿 |
| --- | ---: | ---: |
| 目录 browse，延后图片检查 | 6.86 / 7.13 | 18.24 / 20.48 |
| 目录 browse，热显示检查 | 73.92 / 76.76 | 844.06 / 853.58 |
| 目录 browse，冷图片检查缓存 | 824.23 / 831.65 | 840.27 / 853.81 |
| 搜索“臀”，显示检查 | 21.64 / 22.41 | 32.86 / 33.70 |
| 草稿计划列表 | 0.01 / 0.02 | 0.04 / 0.04 |
| 空训练历史列表 | 0.01 / 0.01 | 0.01 / 0.01 |
| 同一 override 事务保存 | 47.93 / 50.06 | 97.92 / 101.96 |
| 在线备份（小根） | 14.00 / 14.07 | 14.03 / 14.12 |
| 同进程重开上下文 | 116.52 / 122.78 | 121.69 / 125.35 |
| 新进程打开/关闭上下文 | 347.99 / 367.64 | 349.75 / 367.03 |

新建上下文并关闭 p50/p95 = 124.75 / 127.05 ms。
空历史/小备份结果不能外推有长期记录、大图片或大备份的根。

## 热点、待验证原因与优化目标

1. **图片检查缓存容量**：`LibraryWorkflowService._display_image_checks` 在
   128 项时清空整个缓存。136 项目录热浏览 p95 = 853.58 ms，几乎与冷检查
   相同。独立 profile 一次显示调用触发 128 次 `inspect_images`，其中 28 次
   解码占 497.41 ms 累计时间；源码机制与计时共同支持缓存反复清空的判断。
   T-010 优先验证有限 LRU/不缓存空图等方案，保持文件修改、删除、损坏和切根
   时及时失效；不能为了速度让陈旧图片通过动作级资格校验。
2. **重开目录校验**：一次 reopen profile 中 CatalogRepository 初始化
   102.05 ms，`checked_bytes` 73 次、累计 89.02 ms。需审计重复清单/内容图片
   校验，优化只能在明确的资源身份/有效期内复用，不能取消完整性校验。
3. **保存重复枚举**：大样本一次 save profile 调用 `LibraryService.list`
   6 次（累计 114.48 ms）、`get` 817 次。锁内名字/家族复核仍有正确性职责；
   T-010 先识别一次动作内可共享的读取，保持事务和第二写入者检查。

锁定这一协议作为同机比较基线：20 样本、2 预热、相同内容/数据规模和计时边界。
确认的热点目标至少下降 30%：大样本热 browse p95 ≤ 597.51 ms，
冷图片检查 p95 ≤ 597.67 ms；若定位后不能改善，应报告原因而非改口径。
这不是 UI 合格线；常用交互无反馈主线程停顿超过 200 ms 的约束仍需独立
测量和开发者手测，不能用 597 ms 服务目标宣称交互达标。

启动到可操作窗口、实际切根窗口、页面渲染、搜索输入到刷新、非空历史和
最大 UI 停顿均 **not run**。T-009 应在开发者手动操作流上补齐测量与样本；
P4 以此结果决定线程/分页/反馈策略，不运行 GUI 自动化。客户端基线未齐
不妨碍先进行 P2 的代码实现，但不允许声称响应验收完成。

## 本任务验证与身份影响

- `tests/test_baseline_measurement.py`：T-003 dev scope，4 个 unique cases，4 passed。
  覆盖越界路径、目录连接前置拒绝和不读取/枚举未跟踪数据根。目录连接用元数据
  故障注入，不构成实际 Windows 卸载后端的 junction 验收。
- major collect-only 清点原 resident suite 为 213 cases，不执行/不预留预算；
  新增本工具 4 cases 后为 217。测量迭代仅是性能采样，不是额外正确性测试或
  release scope 验收；没有把循环场景记为 pytest 覆盖。
- 改动 Python 的 Ruff、文档路径/身份检查、diff check 通过。
- 应用保持 **0.7.8**，schema **23**，catalog **070-illustrated-3**，wire contract **3**。
  本轮新增开发工具和证据，不改产品行为、schema 或外部契约，不构建安装候选。
- 客户端、安装/卸载、当前打包及公开验收均 **not run**。T-004 的
  [卸载助手设计](uninstall-design.md) 尚未实现；本轮不会产生个人数据转换、
  外部内容审核或 W4 证据。
