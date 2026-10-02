# 卸载窗口修复包：先检查显示和取消

本次只重新安装程序、查看卸载窗口并取消，不删除A/B，也不修改它们的权限。
此前程序已卸载，但A/B和测试目录记录保留。此清单对应
[新的精确候选](../../history/0.8.0/local-candidate-2026-10-02-uninstall-dialog.md)。

1. 关闭仍开着的安装器或程序。在原PowerShell窗口复制下面命令。
   命令只绑定已存在的测试路径并检查新安装包，不重新创建测试环境。

   ```powershell
   $tf080Setup = 'E:\Github\TrainingFeedback\dist\installer\TrainingFeedback-0.8.0-Setup.exe'
   $tf080Program = 'E:\TrainingFeedback-080-PathFix\程序 乙'
   $tf080RootA = 'E:\TrainingFeedback-080-PathFix\测试数据 A'
   $tf080RootB = 'E:\TrainingFeedback-080-PathFix\测试数据 B'
   $env:LOCALAPPDATA = 'E:\TrainingFeedback-080-PathFix\测试配置'
   $tf080Pointer = Join-Path $env:LOCALAPPDATA 'TrainingFeedback/locator.json'
   if ((Get-FileHash -LiteralPath $tf080Setup -Algorithm SHA256).Hash -ne '04a943dd3d3a88cc341dbe8ed1b7b646ef1194917ad5d4a0d710852613f6d90e') { throw '安装包不是本次卸载窗口修复包，请停止。' }
   Start-Process -FilePath $tf080Setup -ArgumentList ('/DIR="' + $tf080Program + '"') -Wait
   ```

2. 确认目录页是“程序 乙”，继续安装；完成页取消勾选自动启动程序。
   出现路径错误或安装错误就停下，反馈完整提示，不清理A/B。
3. 从同一PowerShell运行：

   ```powershell
   Start-Process -FilePath (Join-Path $tf080Program 'unins000.exe') -Wait
   ```

4. 检查应是居中的普通对话框，有正常标题栏和关闭按钮，控件完整可见，
   不再铺满工作区。标题应为“卸载 TrainingFeedback”，说明和按钮为中文。
   此前A/B与locator属于管理员组，因此删除选项仍应不可用；文字应解释Windows
   所有者与当前账号不一致，按钮应是“仅卸载程序”和“取消”。这项拒绝是预期，
   不能记成允许删除的场景通过。保留一张窗口截图供记录。
5. 点击“取消”，不要点“仅卸载程序”。窗口应退出，然后运行：

   ```powershell
   Test-Path -LiteralPath (Join-Path $tf080Program 'TrainingFeedback.exe')
   Test-Path -LiteralPath $tf080RootB
   Test-Path -LiteralPath $tf080Pointer
   ```

   三行都应为True。若窗口仍全屏、说明不清、取消后程序或数据消失，都算失败。
   反馈窗口截图和命令输出，保留现场，不继续删除验收。
6. 再从同一PowerShell启动程序，确认能重新打开B并看到B标记，随后关闭。

   ```powershell
   Start-Process -FilePath (Join-Path $tf080Program 'TrainingFeedback.exe') -Wait
   ```

反馈：窗口大小是否正常、是否中文、是否解释归属原因、取消后的三行结果、
B能否重新打开且标记保留。新普通测试账号的可删除场景另行准备，不让你修改
现有A/B的所有权。未实际执行的步骤保持“未运行”。
