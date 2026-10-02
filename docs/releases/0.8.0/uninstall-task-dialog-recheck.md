# 标准卸载对话框包：取消结果与保留数据复测

本次对应 [408df076候选](../../history/0.8.0/local-candidate-2026-10-02-task-dialog-final.md)。
不用重新创建或修改A/B。原显示与取消步骤的结果已记录，下面继续保留数据复测。
最新截图已确认此归属拒绝场景下的文字换行与两个按钮完整可见，显示检查通过。
取消后三条存在检查已收到，均为True，这三项通过。重新启动已执行，A标记仍可见，
开发者已明确确认B没有写过标记，B标记保留检查不适用，不需要补写。
最新反馈“A保留，B没有。正确”确认内容观察符合预期，不要求重复标记检查。
最新完整终端记录已确认下方第1～5步完成：仅卸载后EXE/A/B/目录记录为
False/True/True/True；两次文件比较没有输出；408df076同包重装后EXE为True。
这些文件检查均通过，开发者已补充第6步重装后内容检查“没有问题”。
**这组保留数据卸载、同包重装和恢复使用检查通过，不要重复本清单。**
原A/B归属不符，不用于删除；[新的删除验收清单](uninstall-delete-acceptance.md)
第1步普通权限检查、第2步新隔离配置准备已通过。
实际新D的恢复归属检查、[直接只读预检](uninstall-preflight-diagnostic.md) 已通过，
主程序关闭时卸载仍拒绝。现有程序乙的卸载记录仍有管理员安装标记，删除相关
检查暂停，先按 [保留数据重置程序安装](uninstall-install-context-reset.md) 继续。

复制命令时只复制代码块内的命令行，不要复制开头的三个反引号及powershell
文字，也不要复制结尾的三个反引号。误复制标记报“术语不被识别”不代表程序
出错；本次后续检查已完成，不需要重做。

## 保留数据复测步骤（第1～6步已完成，保留供追溯）

1. 关闭程序，保留原PowerShell。本次继续使用程序乙、测试数据A/B和独立测试配置。
   先确认原来的文件检查函数仍存在，再记录现在的文件校验值：

   ```powershell
   if (-not (Get-Command Get-Tf080TestFileState -CommandType Function -ErrorAction SilentlyContinue)) { throw '原文件检查函数不存在，请停止并反馈，不继续卸载。' }
   $tf080BeforeKeepUninstall = @(& { $ErrorActionPreference = 'Stop'; Get-Tf080TestFileState | Sort-Object })
   if ($tf080BeforeKeepUninstall.Count -eq 0) { throw '没有取得测试文件校验值，请停止并反馈。' }
   ```

2. 运行下面命令。在卸载窗口点击“仅卸载程序”，然后在普通卸载确认窗口确认
   移除程序。不能选择删除数据；如果意外显示待删除数据的确认，点击取消并反馈。

   ```powershell
   Start-Process -FilePath (Join-Path $tf080Program 'unins000.exe') -Wait
   ```

3. 卸载退出后、重新启动任何程序前运行：

   ```powershell
   Test-Path -LiteralPath (Join-Path $tf080Program 'TrainingFeedback.exe')
   Test-Path -LiteralPath $tf080RootA
   Test-Path -LiteralPath $tf080RootB
   Test-Path -LiteralPath $tf080Pointer
   Compare-Object $tf080BeforeKeepUninstall @(& { $ErrorActionPreference = 'Stop'; Get-Tf080TestFileState | Sort-Object })
   ```

   前四行应依次为False、True、True、True，最后比较应没有输出，表示程序移除，
   A/B和目录记录的文件内容保留。结果不符或有读取报错就停下，反馈完整输出，
   不删除剩余文件。
4. 在原PowerShell重新安装同一个标准对话框包到程序乙：

   ```powershell
   if ((Get-FileHash -LiteralPath $tf080Setup -Algorithm SHA256).Hash -ne '408df0767146fcaf6d8324da88e15928d07da86969da1026fc4e6b426976fb28') { throw '不是本次标准对话框包，请停止。' }
   Start-Process -FilePath $tf080Setup -ArgumentList ('/DIR="' + $tf080Program + '"') -Wait
   ```

   目录页应为“程序 乙”。完成页取消勾选自动启动，安装报错就停下反馈。
5. 仍保持程序关闭，运行下面命令。第一项应True，文件比较应没有输出：

   ```powershell
   Test-Path -LiteralPath (Join-Path $tf080Program 'TrainingFeedback.exe')
   Compare-Object $tf080BeforeKeepUninstall @(& { $ErrorActionPreference = 'Stop'; Get-Tf080TestFileState | Sort-Object })
   ```

6. 从原PowerShell启动程序：

   ```powershell
   Start-Process -FilePath (Join-Path $tf080Program 'TrainingFeedback.exe') -Wait
   ```

   先记下“设置”显示的当前数据目录完整路径。选择“切换到其他数据目录…”→
   “打开已有数据目录”，打开 `E:\TrainingFeedback-080-PathFix\测试数据 A`，
   确认“臀桥”的“完整指导”中A标记还在。再打开已有的
   `E:\TrainingFeedback-080-PathFix\测试数据 B`，确认能正常打开；B未写过标记，
   不要求出现B标记，也不要编辑保存。打不开、A标记消失或B中出现A标记，
   反馈提示和截图，保留现场。查看后关闭程序。

第3、5步完整输出与第6步操作无问题的反馈均已收到，不重复操作。
本次通过要求是仅移除程序、两次文件比较无变化、重装后既有数据仍可打开。
删除数据验收继续未运行，不修改现有数据的Windows所有权。

## 原显示与取消步骤（已完成部分不要重复）

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
7. 从同一PowerShell重新打开程序，确认当前目录与已有内容，再关闭。
   A现有标记应保留；B未写过标记，不要求存在B标记：

   ```powershell
   Start-Process -FilePath (Join-Path $tf080Program 'TrainingFeedback.exe') -Wait
   ```

反馈窗口截图、按钮是否完整可见、三行True结果和当前目录及已有标记。没有做的步骤
记“未运行”。删除数据的其它场景另行安排，不修改现有A/B的Windows所有权。
