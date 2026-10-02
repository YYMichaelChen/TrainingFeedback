# 2026-10-02 标准卸载对话框交付候选

本包替换 [两次尺寸失败的自定义窗口](uninstall-task-dialog-2026-10-02.md)，使用
Inno维护的TaskDialog布局。首项仅卸载保留数据，删除是独立操作且二次默认“否”；
拒绝直接取消，预检不通过时只提供仅卸载和取消。删除归属和范围不变。
窗口、安装、取消、删除及客户端手动检查全部not run，不能凭编译宣称尺寸通过。
下一步执行 [显示与取消重试](../../releases/0.8.0/uninstall-task-dialog-recheck.md)。

| 项目 | 精确值 |
| --- | --- |
| 应用/schema/catalog/contract | 0.8.0/23/070-illustrated-3/3，未变 |
| 干净源码 | b5bf5c8d09472bdda13d01aa4f00f6bda54a8b31 |
| 构建UTC/耗时 | 2026-10-02T06:05:13Z / 60.17秒 |
| 程序目录 | 296文件，176,808,893 bytes |
| Setup | 85,596,151 bytes，NotSigned |
| 工具 | Python3.12.14 AMD64/PySide6 6.11.2/PyInstaller6.22.2/hooks2026.7/Inno6.7.3 |
| Setup SHA-256 | 408df0767146fcaf6d8324da88e15928d07da86969da1026fc4e6b426976fb28 |
| EXE SHA-256 | 20a06f04af9b42ff828b7e5285ce2167d87b4796c23b1df7e154e0b9a5291e1d |
| 程序构建清单SHA-256 | 8cb84d49d08f68ff06f7058390f8bdf812414e9117c6e4ae9589ba99e5743433 |
| 安装包构建清单SHA-256 | f4d96f0d3a1e6acf294664b69079a434d91d655e669a656a99e9c58a53d17cd2 |
| 归属清单SHA-256 | 0170aa02eea3fcc702851844bf847aa8a341b838a1f45a141c33950378adc809 |

输出仍为dist/installer/TrainingFeedback-0.8.0-Setup.exe与完整程序目录。
[静态审计](candidate-audit-2026-10-02-task-dialog-final.json)、
[程序清单](payload-build-manifest-2026-10-02-task-dialog-final.json)、
[安装包清单](installer-build-manifest-2026-10-02-task-dialog-final.json) 逐项核对
程序路径、长度、hash、归属、Setup和嵌入清单均通过；构建验证catalog的36资源、
schema/契约/运行库与不夹带用户数据库。完整Inno编译和干净源码构建通过。

同一release-0.8.0 minor scope既有3项边界测试通过0.17s，累计仍100/100 unique，
其它后端结果复用，没有额外测试scope。交互层变化不以这些后端测试代替手动结果。
没有执行客户端/安装器/卸载器做自动验收。现有A/B和locator的Administrators
所有权保持原样，不能认证可删除场景；旧候选的部分结果不转移认证本包。

同轮 [初始TaskDialog构建](local-candidate-2026-10-02-task-dialog.md) 的精确记录
保留，最终产品说明移除了测试验收文字后重新完整构建；无开发者操作初始构建结果。
其它响应/故障/视觉项目仍未完成。Planscope保持v0.8.0/P5/T-014，不关闭版本。
未签名本地候选不建立正式/公开发布、个人使用、专家内容审核或W4资格。

## 2026-10-02 开发者标准对话框截图结果

开发者按本轮重试步骤提供 [新窗口截图](evidence/uninstall-task-dialog-visible-2026-10-02.png)。
截图显示紧凑标准对话框，主要中文文字正常换行，“仅卸载程序”和“取消”均完整
可见，不再出现此前大面积空白与底部裁切。**此归属拒绝场景的窗口内容和按钮
可见性 pass**。Windows所有者不符的解释清楚，删除入口未提供，符合该场景预期。
截图裁切到对话框，不能单独认证屏幕居中位置或其它DPI/多屏环境；没有完整安装
过程或运行hash的新终端记录，不据此新增payload或目录页认证。

开发者同时贴了三条Test-Path命令文本，但没有True/False输出，不能把取消后的
EXE/B/locator存在检查登记为通过，继续保持未确认。重新打开B及标记保留亦未
提供结果。下一步只补取消后的三行输出与重新打开B，不重复安装或此前M02/M03。
本轮仅截图与文档/计划状态更新，不改代码、候选或任何数据格式，也不重新打包。
