# 标准卸载对话框包：只查看并取消

本次对应 [408df076候选](../../history/0.8.0/local-candidate-2026-10-02-task-dialog-final.md)。
不用重新创建或修改A/B；只更新程序乙，再查看标准卸载选择对话框并取消。
取消保留、显示和恢复打开都还未运行，需要你实际操作反馈。

1. 点击当前尺寸异常的卸载窗口右上角的“×”关闭它。如果出现其它卸载确认，选择
   `No`（否），不要确认卸载。程序若开着也关闭，保留原PowerShell窗口。
2. 在原PowerShell复制运行以下命令，它仅绑定既有路径、检查新安装包并打开安装器。

   ```powershell
   $tf080Setup = 'E:\Github\TrainingFeedback\dist\installer\TrainingFeedback-0.8.0-Setup.exe'
   $tf080Program = 'E:\TrainingFeedback-080-PathFix\程序 乙'
   $tf080RootB = 'E:\TrainingFeedback-080-PathFix\测试数据 B'
   $env:LOCALAPPDATA = 'E:\TrainingFeedback-080-PathFix\测试配置'
   $tf080Pointer = Join-Path $env:LOCALAPPDATA 'TrainingFeedback/locator.json'
   if ((Get-FileHash -LiteralPath $tf080Setup -Algorithm SHA256).Hash -ne '408df0767146fcaf6d8324da88e15928d07da86969da1026fc4e6b426976fb28') { throw '不是本次标准对话框包，请停止。' }
   Start-Process -FilePath $tf080Setup -ArgumentList ('/DIR="' + $tf080Program + '"') -Wait
   ```

3. 目录页应为“程序 乙”，继续安装。完成页取消勾选自动启动程序。
   安装报错就停下并反馈，不删除数据或程序目录来绕过检查。
4. 从同一PowerShell运行：

   ```powershell
   Start-Process -FilePath (Join-Path $tf080Program 'unins000.exe') -Wait
   ```

5. 应显示标准确认对话框而不是大面积文本框。窗口和全部按钮应在屏幕内，文字
   自动换行，主要说明和选项为中文。现有测试数据的归属仍不符，因此只提供
   “仅卸载程序”和“取消”，说明为什么不能删除，不出现删除操作。保留窗口截图。
6. 点击“取消”，不要点击“仅卸载程序”。退出后运行：

   ```powershell
   Test-Path -LiteralPath (Join-Path $tf080Program 'TrainingFeedback.exe')
   Test-Path -LiteralPath $tf080RootB
   Test-Path -LiteralPath $tf080Pointer
   ```

   三行应全部True。若仍铺满屏幕、按钮被裁掉或取消后文件消失，算失败，
   反馈截图和命令输出，停下保留现场。
7. 从同一PowerShell重新打开程序，确认能打开B且B标记保留，再关闭：

   ```powershell
   Start-Process -FilePath (Join-Path $tf080Program 'TrainingFeedback.exe') -Wait
   ```

反馈窗口截图、按钮是否完整可见、三行True结果和B标记是否保留。没有做的步骤
记“未运行”。删除数据的其它场景另行安排，不修改现有A/B的Windows所有权。
