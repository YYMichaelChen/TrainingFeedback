# 2026-10-02 旧程序清理

用户明确要求清理旧版本。此前只修错误提示，未移除阻塞安装的旧程序，未解决
安装环境问题。本次执行的是授权的程序维护，不是安装或卸载功能验收。

## 实际处理

- 通过各自原有卸载器，移除
  `E:\Github\TrainingFeedback\.tmp\acceptance-075\c2\program` 的 0.7.7，及
  `C:\Users\41315\AppData\Local\Programs\TrainingFeedback` 的 0.7.5。
  原路径中的 `acceptance-075` 名字不代表其中实际程序版本。
- 调用前核对程序路径没有链接、卸载器的产品/版本和 SHA-256，并检查旧安装
  脚本没有数据删除卸载步骤。调用参数为
  `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /KEEPDATA`，没有打开训练客户端。
- 两个卸载器退出码均为 0；两个程序目录中的 EXE 和卸载器均不存在。
  默认程序目录已移除，截图路径剩余空程序目录经空目录检查后非递归移除。
- 本应用 AppId 对应的当前用户 32/64 位卸载登记均不存在，三个固定桌面/
  开始菜单快捷方式路径均不存在。没有扫描其它应用的登记或快捷方式。
- 核对卸载日志的 670 条文件/目录删除记录，全部在这两个程序目录及本应用
  快捷方式范围内，没有范围外删除记录。没有打开或扫描训练数据根、locator
  或备份；不声称做过数据根字节级前后比对。
- 从 `dist/installer` 删除 0.6.1、0.7.0～0.7.5、0.7.7 的 8 个过期安装包及
  各自清单，共 16 文件、633,523,378 bytes（604.17 MiB）。删除前逐一核对
  清单版本、安装包 hash 和精确输出目录。版本事实与既有 Git 历史保留，
  没有新建无限归档或删除历史证据。

清理后 `dist/installer` 只有 0.8.0 安装包和其构建清单。现有新候选的安装包
SHA-256 仍是 `8b5fd69ac7babe7da6ebbf9a5eea2e3926e779b93d6bdf5ee52b655b2cb59575`，
应用/schema/catalog/contract 仍为 0.8.0 / 23 / 070-illustrated-3 / 3。
详细文件、hash 和维护结果在 [维护记录](legacy-program-cleanup-2026-10-02.json)。
原始卸载日志保存在本地 `.tmp/legacy-program-cleanup-2026-10-02/`。

## 第二张截图与下一步

[第二张截图](evidence/installation-chinese-message-2026-10-02.png) 已观察到完整
中文说明，没有原来的英文 Errno；安装仍停在“Preparing to Install”。截图
没有安装包 hash，所以只记录该屏幕观察，不认证精确候选或整个安装通过。

已打开的安装器可能缓存清理前的旧目录，开发者需点击 `Cancel` 退出，再从
`dist/installer/TrainingFeedback-0.8.0-Setup.exe` 重新打开，按
[中文步骤](../../releases/0.8.0/manual-acceptance.md) 安装到新的空程序目录。
不再要求用户自己卸载已清理的两份旧程序。

本次未修改代码或候选，无新增 pytest 执行，原 release-0.8.0 minor scope
累计仍为 100/100。文档和 diff 检查通过，Planscope 保持 P5/T-014。
清理后的实际安装、客户端、卸载和响应检查仍未运行；维护结果不代替这些验收。
