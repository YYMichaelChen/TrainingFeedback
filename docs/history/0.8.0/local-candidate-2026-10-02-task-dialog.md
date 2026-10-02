# 2026-10-02 标准卸载选择对话框本地候选

替换 [两次尺寸复测失败的自定义窗口](uninstall-task-dialog-2026-10-02.md)，改用
Inno维护的TaskDialog，默认仅卸载并保留数据；有效当前根的删除为独立明确操作，
再次确认默认“否”，拒绝直接取消。归属拒绝时只显示仅卸载和取消。
手动窗口、安装/取消/删除和客户端检查全部not run，不把编译当作尺寸通过。
下一步按 [中文重试步骤](../../releases/0.8.0/uninstall-task-dialog-recheck.md) 仅检查显示与取消。

## 精确身份与实际验证

| 项目 | 值 |
| --- | --- |
| 应用/schema/catalog/contract | 0.8.0/23/070-illustrated-3/3，未变 |
| 干净源码 | 1bef967968e8959530ea8097499d7ca66122a63e |
| 构建UTC/耗时 | 2026-10-02T06:00:00Z / 59.57秒 |
| 程序目录 | 296文件，176,808,893 bytes |
| Setup | 85,602,115 bytes，NotSigned |
| 工具 | Python3.12.14 AMD64/PySide6 6.11.2/PyInstaller6.22.2/hooks2026.7/Inno6.7.3 |
| Setup SHA-256 | 69a5c0f04ac189a6ced6bc52087402c62d5a06b29dcd4ff5f18c3f6c26dac756 |
| EXE SHA-256 | 3057fff5928d99efadd3f41d68edf8dda349334a3f7cbe4645eb77ac4876eadd |
| 程序构建清单SHA-256 | b7a85ad8416a955b723e09d23d734f41534d3084749386f7783b0b1ab5100b2b |
| 安装包构建清单SHA-256 | 4084c7caeeb392637db3ddfd61118aa2cc4ed501f052b30c3fc4688c0b75b8cf |
| 归属清单SHA-256 | 963fe94b581acebeba79d1ae05a49131f4c71a869525c16732978a89d12da7ef |

原release-0.8.0 minor scope既有3项清理边界复测通过（0.17s），累计仍100/100
unique，不增加scope、不重跑无关全部选集。其它后端结果明确复用。Inno完整编译
与干净源码完整构建通过，296文件的路径/大小/hash、归属清单、Setup与嵌入清单
逐项核对通过。构建验证catalog及36资源、schema/contract/运行库和不夹带用户数据库。
新候选没有任何自动客户端、安装或卸载验证。证据：[审计](candidate-audit-2026-10-02-task-dialog.json)、
[程序清单](payload-build-manifest-2026-10-02-task-dialog.json)、
[安装包清单](installer-build-manifest-2026-10-02-task-dialog.json)。

当前输出仍为dist/installer/TrainingFeedback-0.8.0-Setup.exe及完整程序目录。
上一份04a943dd候选另存本地.tmp/candidates/2026-10-02-uninstall-dialog/。
原候选的A/B、重装、搬迁结果不认证新构建；现有A/B和locator的Administrators
所有权保持原样，不能用它们认证可删除场景。未修复ACL或放宽归属边界。
性能、训练、其它视觉与故障项仍有未完成内容。Planscope仍v0.8.0/P5/T-014。
这是未签名本地候选，不建立正式/公开发布、个人使用、专家审核或W4资格。
