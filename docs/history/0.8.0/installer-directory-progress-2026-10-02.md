# 安装目录检查的等待反馈与重复检查修复

开发者在408df076候选的安装目录页点击Next后报告卡顿几秒。首次辅助检查
同步解压完整payload，同路径重装还会在旧程序完整验证之后再次完整验证同一
目标，期间目录页没有等待反馈。未测量精确耗时，不能把代码路径计数当秒数。

`packaging/training_feedback.iss` 现在使用
[Inno标准等待进度页](https://jrsoftware.org/ishelp/topic_isxfunc_createoutputmarqueeprogresspage.htm)：
点击Next进入“正在检查安装目录”，显示当前路径与“请稍候”，检查后在finally
隐藏进度页，回到原页面再显示错误或继续。静默安装不显示该页。
同一次Next中，刚完成的旧程序及卸载器检查已覆盖完全相同的目标时，省略
额外的目标validate调用。选择不同路径仍检查重叠/边界/归属，真正安装前
PrepareToInstall和prepare阶段仍保留原检查；没有跨操作缓存、跳过校验或触碰数据。
开始/结束记录写入Inno日志，后续开发者可提供日志作实际等待证据。

同一release-0.8.0 minor范围的26个既有安装案例通过/0.52s，仍100/100 unique；
合成payload Inno6.7.3编译通过/1.140s。这些不认证窗口显示、进度动画、响应性、
实际耗时或完整新候选安装；客户端检查尚未运行，等待干净源码完整构建。
应用0.8.0/schema23/catalog070-illustrated-3/contract3均不变，Python程序行为及
数据策略不变。旧408df076候选的手动通过只属于旧包，新包需检查受影响目录页。
构建前Ruff、50份Markdown文档检查及git diff --check均通过。新目录页逻辑未
执行自动客户端操作，进度显示与同路径去重的安装调用仍需开发者手动复测。

## 完整交付候选

| 项目 | 值 |
| --- | --- |
| 干净构建源码 | 89f7981c8e1eaf4d7ca821528c7b452529917fe3 |
| 构建UTC / 耗时 | 2026-10-02T15:46:53Z / 66.30秒 |
| 应用/schema/catalog/contract | 0.8.0 / 23 / 070-illustrated-3 / 3 |
| payload | 296文件 / 176808893 bytes |
| Setup | 85600545 bytes / NotSigned |
| Setup SHA-256 | 49de95af46f2ae0f20f36a7bbb1f4e6318a418cf9b117370ee130ced1b1dcdad |
| EXE SHA-256 | 1d2f09f781a8a2217921946f48ffc187c9cdb94e716cafa124880dd2cc9a8961 |
| 程序构建清单SHA-256 | 0c728983b6f184b0529e38b40cd680089b947e8b52f16165fb8258eb877ce41b |
| 安装包清单SHA-256 | d676e1dbe4803e5e9bd6f8d8a4a06c987bb9d970a086569231e86cbfffab5841 |
| 程序归属清单SHA-256 | 67b6319318a6797246caa9de6e2e117aa06637ee453d302169bf3e51f4878d5e |

标准完整PyInstaller/Inno构建成功，工具链仍Python3.12.14 AMD64/PySide6 6.11.2/
PyInstaller6.22.2/hooks2026.7/Inno6.7.3。静态审计核对全部路径、长度、hash、
程序归属、Setup及嵌入构建清单，catalog36资源/schema/契约/运行库与不夹带
用户数据库检查通过。见 [审计](candidate-audit-2026-10-02-directory-progress.json)、
[程序清单](payload-build-manifest-2026-10-02-directory-progress.json) 和
[安装包清单](installer-build-manifest-2026-10-02-directory-progress.json)。
与408df076比较文件集合相同，仅EXE、base_library.zip和归属清单hash不同；
不能因为Python源码没改而宣称新二进制已安装通过。旧候选实测保留历史。

当前交付位置为`dist/installer/TrainingFeedback-0.8.0-Setup.exe`，替换同名旧包。
按 [目录页等待复测](../../releases/0.8.0/installer-directory-progress-recheck.md)
由开发者检查新进度、错误返回、同路径安装及合成文件保留。实际显示、消息响应
与耗时改善全部not run；不声明几秒等待已消失。未签名本地候选不建立正式/公开
发布、个人使用、内容审核或W4资格。Planscope保持v0.8.0/P5/T-014。
交付材料检查：51份Markdown文档检查、复测清单2段PowerShell语法解析及
git diff --check通过，Planscope sync/doctor为0错误/0警告。未运行复测命令或
自动客户端检查，等待页的实际显示和效果必须由开发者提供结果。

## 2026-10-03 开发者手动复测结果

开发者在原普通PowerShell窗口按目录页复测清单操作，提供了
[完整终端记录](evidence/installer-directory-progress-terminal-2026-10-03.txt)。
原始文件SHA-256为
`b2450b0ace9477773ead434984cf5e9511b40f3b1ec2f08dffafad39d2e0f5d9`。
准备检查绑定Setup49de95af、旧安装EXE20a06f04、原独立配置以及已不存在的D。
完成后EXE1d2f09f7匹配，误选目录仍只有原检查文件且hash未变，原A/B、原配置、
根外保留文件hash全部未变，D和目录记录未重建。这组新候选安装及边界检查pass。

日志显示误选目录检查00:01:15.818至00:01:17.223，用时1.405秒；程序乙检查
00:01:43.114至00:01:44.359，用时1.245秒，同一次操作的目标去重日志已出现。
每个路径仅一次样本；这是日志覆盖的目录检查区间，不是全部安装或冷启动耗时，
没有可比较的旧包计时，不能宣称加速百分比、p95或所有等待已消失。

开发者进一步确认：“提示和返回都正常，等待能接受”。新等待说明、误选目录
错误返回和本轮主观等待体验pass；没有新界面截图、其它DPI/多屏或消息响应
时间测量，不扩展结论。复测由开发者操作，代理只核对记录，没有自动客户端检查。

二次确认选择No取消、数据正在使用时拒绝删除仍not run，改用
[全新合成根的两项补验](../../releases/0.8.0/uninstall-cancel-and-in-use-recheck.md)。
408df076旧候选的删除范围/重装通过仍是历史证据，不转成49de95af的新包通过。
应用/schema/catalog/contract身份和构建产物不变；本次仅补记证据和准备清单，
不重新构建或重复pytest。Planscope保持v0.8.0/P5/T-014，响应验收等缺项仍开放。
本次材料验证：52份Markdown文档检查、新补验清单7段PowerShell语法解析、
git diff --check通过；Planscope sync/doctor为0错误/0警告，LOG压缩到软预算内。
这些命令仅检查材料，没有替开发者执行新E清单或启动客户端。
