# 新D已关闭但卸载仍拒绝：只读诊断

**诊断与后续普通权限重装均已通过，本文仅保留排查记录，不再执行。** 当前从
[删除清单第4步](uninstall-delete-acceptance.md#4-拒绝永久删除确认程序和数据应保留) 继续。

对应 [408df076候选](../../history/0.8.0/local-candidate-2026-10-02-task-dialog-final.md)。
开发者已确认实际D存在、目录记录指向D、归属检查通过，主程序未打开，且没有
出现Windows权限确认。卸载窗口仍提示“数据文件正在使用，或当前账号没有所需
权限”，不能记为使用中拒绝通过。当时原因未确定，曾暂停删除验收第4～7步。

本次只检查下面这套新合成配置。不要读取、切换到或删除其它数据目录。
原A/B、原配置和实际D保持不变；不会启动Qt客户端，也不会执行删除提交。
诊断结果写在新父目录下的独立“只读诊断-…”目录，位于D之外。

1. 在截图中的卸载窗口点击“取消”，不要点击“仅卸载程序”。确保主程序关闭，
   保留刚才创建D和执行恢复检查的普通PowerShell窗口。
2. 在同一个窗口只复制下面代码块内部的完整命令。它重新核对普通权限、固定
   隔离配置、目录记录和已安装EXE的候选hash，再运行内部只读预检。
   若意外出现权限确认框，选择取消并反馈，不继续。

   ```powershell
   . {
       $ErrorActionPreference = 'Stop'
       $tf080DeleteDiagnosticIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
       if ([Security.Principal.WindowsPrincipal]::new($tf080DeleteDiagnosticIdentity).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw '当前不是普通权限，请停止。' }
       $tf080DeleteBase = 'C:\Users\41315\TrainingFeedback-080-Delete-20261002-153609'
       $tf080DeleteRoot = Join-Path $tf080DeleteBase 'TrainingFeedbackData'
       $tf080DeleteConfig = Join-Path $tf080DeleteBase '独立测试配置'
       $tf080DeletePointer = Join-Path $tf080DeleteConfig 'TrainingFeedback\locator.json'
       $tf080DeleteProgram = 'E:\TrainingFeedback-080-PathFix\程序 乙'
       if ($env:LOCALAPPDATA -ne $tf080DeleteConfig) { throw '当前不是这套独立配置，请停止。' }
       if (-not (Test-Path -LiteralPath $tf080DeleteRoot -PathType Container)) { throw '实际D不存在，请停止。' }
       $tf080DeleteDiagnosticRecordedRoot = (Get-Content -LiteralPath $tf080DeletePointer -Raw | ConvertFrom-Json).data_root
       if ([IO.Path]::GetFullPath($tf080DeleteDiagnosticRecordedRoot) -ne [IO.Path]::GetFullPath($tf080DeleteRoot)) { throw '目录记录未指向本轮实际D，请停止。' }
       $tf080DeleteDiagnosticExe = Join-Path $tf080DeleteProgram 'TrainingFeedback.exe'
       if ((Get-FileHash -LiteralPath $tf080DeleteDiagnosticExe -Algorithm SHA256).Hash -ne '20a06f04af9b42ff828b7e5285ce2167d87b4796c23b1df7e154e0b9a5291e1d') { throw '已安装程序不是本次候选，请停止。' }
       $tf080DeleteDiagnosticDirectory = Join-Path $tf080DeleteBase ('只读诊断-' + [guid]::NewGuid().ToString('N'))
       New-Item -ItemType Directory -Path $tf080DeleteDiagnosticDirectory | Out-Null
       $tf080DeleteDiagnosticOffer = Join-Path $tf080DeleteDiagnosticDirectory 'offer.json'
       $tf080DeleteDiagnosticResult = Join-Path $tf080DeleteDiagnosticDirectory 'result.txt'
       $tf080DeleteDiagnosticArguments = '--uninstall-helper probe --offer "' + $tf080DeleteDiagnosticOffer + '" --result "' + $tf080DeleteDiagnosticResult + '"'
       $tf080DeleteDiagnosticProcess = Start-Process -FilePath $tf080DeleteDiagnosticExe -ArgumentList $tf080DeleteDiagnosticArguments -Wait -PassThru
       Write-Output ('预检退出码：' + $tf080DeleteDiagnosticProcess.ExitCode)
       Write-Output ('诊断结果目录：' + $tf080DeleteDiagnosticDirectory)
       Get-Content -LiteralPath $tf080DeleteDiagnosticResult
   }
   ```

3. 反馈整个输出。正常可用时退出码为0，结果第一行为READY，下一行必须完整
   等于`C:\Users\41315\TrainingFeedback-080-Delete-20261002-153609\TrainingFeedbackData`。
   这只证明直接预检可用，不代表卸载窗口或删除通过。REFUSED、其它路径、没有
   结果文件或运行报错都反馈原文，保留日志，不修改权限或继续删除。

本段已由开发者运行通过：退出码0、READY、上述确切D、Files: 4; bytes: 475345。
结果目录为`C:\Users\41315\TrainingFeedback-080-Delete-20261002-153609\只读诊断-8edb15c565df400aba33ae7411a2dce9`。
不要重复预检。只读检查现有程序乙的Inno卸载记录确认其仍有管理员安装标记，
[保留数据重置程序安装](uninstall-install-context-reset.md) 也已执行通过：新管理员
标记False，正确D的删除入口出现，首屏取消后文件未变。现在从
[删除清单第4步](uninstall-delete-acceptance.md#4-拒绝永久删除确认程序和数据应保留) 继续，
不重复本段。没有认证此前管理员卸载器实际配置或根路径。
