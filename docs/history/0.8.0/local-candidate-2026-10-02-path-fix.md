# 0.8.0 路径修复候选 — 2026-10-02

本候选修复未经校验的旧默认目录继承和不存在旧目录的搬迁检查，并更新
[中文操作命令](../../releases/0.8.0/manual-acceptance.md) 为专用变量和明确的
`/DIR` 路径。背景与旧日志观察见 [问题记录](installation-path-fix-2026-10-02.md)。
**新候选的实际默认路径、安装、卸载、客户端和响应检查未运行。**
这是未签名本地候选，不建立正式/公开发布、个人使用、专家内容审核或 W4 资格。

## 精确身份

| 项目 | 值 |
| --- | --- |
| 应用 / schema / catalog / contract | 0.8.0 / 23 / 070-illustrated-3 / 3，未变 |
| 干净源码 | 1abf07daedd87272773dd1cce0fbaaa93d806945 |
| 构建 UTC | 2026-10-01T17:39:59Z（北京时间10月2日） |
| 构建耗时 | 61.30 秒，含 PyInstaller、Inno 和构建检查 |
| 完整程序目录 | 296 文件，176,808,893 bytes |
| 安装包 | 85,602,077 bytes，NotSigned |
| 工具 | Python3.12.14 AMD64 / PySide6 6.11.2 / PyInstaller6.22.2 / hooks2026.7 / Inno6.7.3 |

| 文件 | SHA-256 |
| --- | --- |
| TrainingFeedback.exe | f0d92afa6dc15595210bf67cfa696a52f4d08df0516697fa9fadbc68ba87a025 |
| TrainingFeedback-0.8.0-Setup.exe | 7b708a7cb19a75b0478ffc1cd8c7d56e3b4d45eb90f8773e76b0a39de1665a36 |
| 程序构建清单 | ee6119b89d536407cd0c561708ab427270b08b435702ad7c38aa09481eba348d |
| 安装包构建清单 | 11b0c2ac57241989d6a23c48b0e892ef053debf06f70e7d01466ac962bd35ca0 |
| 程序归属清单 | d4c93fa787971f30572720efb7fd3f2305fbdefa0fe5f4080f24a7cd1592b6d2 |

当前交付位于 `dist/installer/TrainingFeedback-0.8.0-Setup.exe` 和完整
`dist/TrainingFeedback/`。证据为 [程序清单](payload-build-manifest-2026-10-02-path-fix.json)、
[安装包清单](installer-build-manifest-2026-10-02-path-fix.json)、
[审计](candidate-audit-2026-10-02-path-fix.json)。前一提示修复候选的记录和 hash
不改写，其本地安装包另存 `.tmp/candidates/2026-10-02-message-fix/`。

## 实际验证与未运行项

既有安装helper选集26项通过（0.39s）；仍在唯一release-0.8.0 minor scope，
累计100/100 unique cases，未受影响结果明确复用，没有重跑全部100项。
Inno 完整编译、干净源码构建及程序路径/大小/hash/归属清单逐项核对通过；
安装包hash与嵌入的程序构建清单一致，catalog及36资源验证通过。构建脚本
核对schema/契约/运行库及不夹带用户数据库。文档和diff检查通过；MD的11段
PowerShell用原生解析器检查语法，**没有执行这些启动/卸载命令**。

关闭 `UsePreviousAppDir`，由脚本返回普通Windows默认或经过helper校验的当前
安装目录；缺失旧程序路径只清除进程内旧安装变量，不删除旧登记或任何目录。
仍存在且归属未知的目录继续拒绝。准备搬迁时复核校验，保留受控迁移流程。
脚本新增登记、默认、选中及准备搬迁来源日志，不读取训练内容。
早期临时helper提取时机核对了 [Inno 官方说明](https://jrsoftware.org/ishelp/topic_isxfunc_extracttemporaryfiles.htm)。

上述代码级检查不证明实际默认目录和 `/DIR` 页面预填正确，更不代替实际安装/
快捷方式/搬迁/卸载。旧日志证明此前确实重新启动仍失败，不能说是用户没重开。
新候选相关实际检查全部未运行，开发者按更新清单操作后再记录。
冷解码853.28ms目标、客户端停顿和非空历史/大备份仍未解决或未运行。
Planscope保持v0.8.0/P5/T-014进行中，不关闭版本。

## 2026-10-02 开发者准备步骤结果

开发者粘贴的实际终端记录显示 PowerShell 7.6.6，完整执行新版准备代码后
没有报错，并输出四个路径。安装包存在与 SHA-256 检查均已走过，匹配本候选
`7b708a7cb19a75b0478ffc1cd8c7d56e3b4d45eb90f8773e76b0a39de1665a36`。
**准备步骤 pass**，不把准备通过记成安装或客户端通过。

- 程序：`E:\TrainingFeedback-080-PathFix\程序 甲`。
- 数据A/B：`E:\TrainingFeedback-080-PathFix\测试数据 A`、
  `E:\TrainingFeedback-080-PathFix\测试数据 B`，目前是已赋值的目标路径。
- 隔离配置：`E:\TrainingFeedback-080-PathFix\测试配置`。
- 配置与根外备份目录创建、根外检查文件写入命令无错误；未单独读回文件。
  没有创建或打开训练数据根，没有客户端训练、审核或个人事实。

终端提示符为 `C:\Users\41315`；是否为专用普通测试账户尚未提供，不据此
认证删除验收环境。此输出尚未执行 M01 启动命令，因此 `/DIR` 预填、安装、
EXE/receipt、首次启动取消、卸载和响应仍 not run。
下一步使用当前 PowerShell 的 `tf080` 变量执行 M01，不重复准备命令。

## 2026-10-02 开发者安装与静态文件检查结果

开发者在同一窗口执行带 `/DIR` 的新版启动命令，随后对
`E:\TrainingFeedback-080-PathFix\程序 甲\TrainingFeedback.exe` 和
`.training-feedback-install.json` 的两项 `Test-Path` 均输出 `True`。
**M01 自定义目录安装后的两项存在检查 pass**。未提供安装器退出码、目录页
视觉、桌面快捷方式或完成页取消自动启动的单独结果，不补填这些检查为通过。

随后 agent 仅静态检查该已知合成程序目录：完整296个候选payload文件的路径、
大小、SHA-256与构建清单一致；总299个归属文件包含精确安装记录以及
`unins000.exe`/`unins000.dat`。归属、receipt绑定目录和卸载器hash校验通过，
无无关文件。结果见 [安装后静态审计](installed-payload-audit-2026-10-02-path-fix.json)。
没有执行程序或卸载器，没有读取locator、训练数据根或训练数据库。

这证明本次指定新目录已安装匹配的程序文件，不证明无参数默认目录或整个M01
通过。首次启动选择数据目录后取消、locator/数据A不创建，以及M02后续客户端、
搬迁、卸载和响应尚无开发者结果，保持not run。下一步在原PowerShell窗口启动
该EXE，取消数据目录选择，确认pointer和rootA两项均为False。
