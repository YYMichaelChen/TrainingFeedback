# 2026-10-02 卸载对话框修复本地候选

本包修复 [开发者截图暴露的窗口与说明问题](uninstall-dialog-fix-2026-10-02.md)。
新包未实际安装或操作客户端，手动验收全部not run。原路径修复候选的创建、重启、
重装、搬迁和卸载存在检查保留在 [原证据](local-candidate-2026-10-02-path-fix.md)，
不转移认证新构建。下一步只做 [安装、查看和取消重试](../../releases/0.8.0/uninstall-dialog-recheck.md)。

## 精确身份

| 项目 | 值 |
| --- | --- |
| 应用/schema/catalog/contract | 0.8.0/23/070-illustrated-3/3，未变 |
| 干净源码 | 8ac2c8975be34a04751ba81308242dafbaffb999 |
| 构建UTC | 2026-10-02T05:07:48Z |
| 构建耗时 | 66.01秒，含PyInstaller、Inno和构建检查 |
| 完整程序目录 | 296文件，176,808,893 bytes |
| Setup | 85,596,677 bytes；NotSigned |
| 工具 | Python3.12.14 AMD64/PySide6 6.11.2/PyInstaller6.22.2/hooks2026.7/Inno6.7.3 |

| 文件 | SHA-256 |
| --- | --- |
| Setup | 04a943dd3d3a88cc341dbe8ed1b7b646ef1194917ad5d4a0d710852613f6d90e |
| EXE | 6d9eb51970cdf7fec09c7f84ac99e329cae62df1be2f0c8d304d8080894cf77d |
| 程序构建清单 | 0388cbba6ef972e0dac3beb0acaffa9b2cb310473c42589c0224d1cfa5db03a3 |
| 安装包构建清单 | e9bca24fb346c8fa5cdd16da90226b188b3574a41a21290e9793462b2a594a6a |
| 程序归属清单 | 54d97e07992fa371cd71d114709767dd0ecefb8f6ba7c3fea07a415cda664274 |

输出仍是`dist/installer/TrainingFeedback-0.8.0-Setup.exe`及完整程序目录。
证据：[静态审计](candidate-audit-2026-10-02-uninstall-dialog.json)、
[程序清单](payload-build-manifest-2026-10-02-uninstall-dialog.json)、
[安装包清单](installer-build-manifest-2026-10-02-uninstall-dialog.json)。

## 实际验证与限制

原release-0.8.0 minor scope既有3项清理边界测试通过（0.35s），累计仍100/100
unique；未受影响后端结果复用。Inno完整编译、完整干净源码构建通过。程序路径、
大小、SHA-256、归属清单、安装包及嵌入清单逐项一致；构建还验证catalog的36资源、
schema、契约、运行库及不夹带用户数据库。未启动程序、安装器或卸载器做客户端验收。

Windows组所有权不等于当前用户所有权，现有A/B和测试locator不满足删除归属
要求。此包保持拒绝，不提权、不改ACL，不删除现有数据。窗口实际大小、中文、
取消保留、可删除场景、其它安装/卸载/训练/响应都待开发者实际检查。
冷图片目标与其它原未完成项没有因本修复消失。Planscope仍v0.8.0/P5/T-014。
这是未签名本地候选，不建立正式/公开发布、个人使用、专家内容审核或W4资格。

## 2026-10-02 第二次尺寸复测失败

开发者提供 [新截图](evidence/uninstall-dialog-still-oversized-2026-10-02.png)，
中文说明和标题已显示，但窗口仍覆盖整个工作区，底部选项和按钮被挤出可见范围。
**尺寸/控件可见性 fail**，不能因中文生效而记为界面通过。没有取消后的终端输出，
不登记取消保留通过。截图本身不包含运行hash；它是开发者按上一轮精确包步骤
复测时的反馈，保留此来源限制。

限制尺寸与控件相对布局未解决本机现象；该窗口实现停止继续投入验收，后续改用
Inno维护的TaskDialog。旧包和两次截图保留，后续构建的身份与结果独立记录。
