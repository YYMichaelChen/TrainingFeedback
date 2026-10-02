# 第4步中程序与D已移除：先核对保留文件

本轮仍对应 [408df076候选](../../history/0.8.0/local-candidate-2026-10-02-task-dialog-final.md)。
开发者第4步检查得到程序、D、目录记录三个False，随后因EXE不存在而报错，
原文件比较未执行。开发者已确认点击永久删除选项，并在二次确认选择“是”。
本次提前执行删除分支，取消检查未完成；没有证据表明保留数据选项误删。
不能把这次记录为二次确认取消通过，也不能只凭三个False认证删除范围通过。

## 1. 保留现场

保留刚才的普通PowerShell窗口，里面仍有卸载前的文件校验值。暂不执行旧清单
第4～7步，不重装、不重建D，也不重新记录覆盖原校验值。新D是本轮合成测试
数据；原A/B、原配置和根外保留文件仍应存在且内容完全未变。

实际按钮已确认，不必重复回答。本轮只认证程序、D、新目录记录被移除这一
存在结果，根外文件校验尚未完成；先运行下一段，不把整个删除范围记为通过。

## 2. 在同一个PowerShell运行完整的只读检查

只复制代码块内部的命令，不复制三个反引号。它只读取指定测试文件、比较
已有校验值，不启动程序、安装器或卸载器，不创建或删除任何文件。

```powershell
. {
    $ErrorActionPreference = 'Stop'
    $tf080AccidentOutsideChecked = $false
    if (-not (Get-Command Get-Tf080DeleteFileState -CommandType Function -ErrorAction SilentlyContinue)) { throw '卸载前的文件检查函数不存在，请停止。' }
    if ($null -eq $tf080DeleteProtectedBefore -or @($tf080DeleteProtectedBefore).Count -eq 0) { throw '卸载前的校验值不存在，请停止，不补写新基线。' }
    foreach ($tf080AccidentBaselineRow in $tf080DeleteProtectedBefore) {
        if ($tf080AccidentBaselineRow -isnot [string] -or $tf080AccidentBaselineRow -notmatch '\|[a-fA-F0-9]{64}$') { throw '卸载前的校验值不完整，请停止。' }
    }
    $tf080AccidentProtected = @(
        'E:\TrainingFeedback-080-PathFix\测试数据 A',
        'E:\TrainingFeedback-080-PathFix\测试数据 B',
        'E:\TrainingFeedback-080-PathFix\测试配置',
        'C:\Users\41315\TrainingFeedback-080-Delete-20261002-153609\根外保留文件'
    )
    if (@(Compare-Object @($tf080DeleteProtected | Sort-Object) @($tf080AccidentProtected | Sort-Object)).Count -ne 0) { throw '卸载前的保留目录范围不符，请停止。' }
    foreach ($tf080AccidentDirectory in $tf080AccidentProtected) {
        if (-not (Test-Path -LiteralPath $tf080AccidentDirectory -PathType Container)) { throw ('应保留的目录不存在，请停止：' + $tf080AccidentDirectory) }
    }
    Write-Output ('程序存在：' + (Test-Path -LiteralPath 'E:\TrainingFeedback-080-PathFix\程序 乙\TrainingFeedback.exe'))
    Write-Output ('D存在：' + (Test-Path -LiteralPath 'C:\Users\41315\TrainingFeedback-080-Delete-20261002-153609\TrainingFeedbackData'))
    Write-Output ('新目录记录存在：' + (Test-Path -LiteralPath 'C:\Users\41315\TrainingFeedback-080-Delete-20261002-153609\独立测试配置\TrainingFeedback\locator.json'))
    $tf080AccidentDifference = @(Compare-Object $tf080DeleteProtectedBefore @(Get-Tf080DeleteFileState -Directories $tf080AccidentProtected | Sort-Object))
    if ($tf080AccidentDifference.Count -ne 0) { $tf080AccidentDifference; throw '根外保留文件有变化，请停止并反馈，不重装或清理。' }
    $tf080AccidentOutsideChecked = $true
    Write-Output '保留文件核对通过：A/B、原配置和根外文件校验值全部未变。'
}
```

## 3. 核对通过后，重装并检查取消不会重建D

预期前三项False，最后打印保留文件核对通过；这只证明已记录的根外保留文件
未变，不证明按钮操作正确或二次确认取消通过。任何报错、比较差异或缺失文件
都保留原文反馈，不自行清理或修改权限。只有上一步完整通过才运行下面代码。

安装目录仍为`E:\TrainingFeedback-080-PathFix\程序 乙`。在安装完成页取消勾选
Launch TrainingFeedback（启动程序），再点Finish（完成）。命令会核对程序
hash与D没有被安装器重建，再启动程序。应出现数据目录选择窗口，**只点击取消**，
不创建目录、不打开A/B。出现权限确认就取消并反馈。此步骤仍保留原测试文件。

```powershell
. {
    $ErrorActionPreference = 'Stop'
    $tf080AccidentReinstallChecked = $false
    if (-not $tf080AccidentOutsideChecked) { throw '保留文件核对尚未通过，请停止。' }
    if ([Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw '当前是管理员权限，请停止。' }
    if ($env:LOCALAPPDATA -ne 'C:\Users\41315\TrainingFeedback-080-Delete-20261002-153609\独立测试配置') { throw '独立配置已变化，请停止。' }
    $tf080DeleteRoot = 'C:\Users\41315\TrainingFeedback-080-Delete-20261002-153609\TrainingFeedbackData'
    $tf080DeletePointer = Join-Path $env:LOCALAPPDATA 'TrainingFeedback\locator.json'
    $tf080DeleteProgram = 'E:\TrainingFeedback-080-PathFix\程序 乙'
    $tf080DeleteSetup = 'E:\Github\TrainingFeedback\dist\installer\TrainingFeedback-0.8.0-Setup.exe'
    if ((Test-Path -LiteralPath $tf080DeleteRoot) -or (Test-Path -LiteralPath $tf080DeletePointer) -or (Test-Path -LiteralPath (Join-Path $tf080DeleteProgram 'TrainingFeedback.exe')) -or (Test-Path -LiteralPath (Join-Path $tf080DeleteProgram 'unins000.dat'))) { throw '删除后的现场不符，请停止。' }
    if ((Get-FileHash -LiteralPath $tf080DeleteSetup -Algorithm SHA256).Hash -ne '408df0767146fcaf6d8324da88e15928d07da86969da1026fc4e6b426976fb28') { throw '安装包不是本次候选，请停止。' }
    Start-Process -FilePath $tf080DeleteSetup -ArgumentList ('/DIR="' + $tf080DeleteProgram + '"') -Wait
    if ((Get-FileHash -LiteralPath (Join-Path $tf080DeleteProgram 'TrainingFeedback.exe') -Algorithm SHA256).Hash -ne '20a06f04af9b42ff828b7e5285ce2167d87b4796c23b1df7e154e0b9a5291e1d') { throw '重装程序不是本次候选，请停止。' }
    if ((Test-Path -LiteralPath $tf080DeleteRoot) -or (Test-Path -LiteralPath $tf080DeletePointer)) { throw '安装器重建了D或目录记录，请停止。' }
    Start-Process -FilePath (Join-Path $tf080DeleteProgram 'TrainingFeedback.exe') -Wait
    Write-Output ('程序存在：' + (Test-Path -LiteralPath (Join-Path $tf080DeleteProgram 'TrainingFeedback.exe')))
    Write-Output ('D存在：' + (Test-Path -LiteralPath $tf080DeleteRoot))
    Write-Output ('新目录记录存在：' + (Test-Path -LiteralPath $tf080DeletePointer))
    if (-not (Test-Path -LiteralPath (Join-Path $tf080DeleteProgram 'TrainingFeedback.exe')) -or (Test-Path -LiteralPath $tf080DeleteRoot) -or (Test-Path -LiteralPath $tf080DeletePointer)) { throw '重装取消后的存在检查不符，请停止。' }
    $tf080AccidentDifference = @(Compare-Object $tf080DeleteProtectedBefore @(Get-Tf080DeleteFileState -Directories $tf080AccidentProtected | Sort-Object))
    if ($tf080AccidentDifference.Count -ne 0) { $tf080AccidentDifference; throw '重装后根外保留文件有变化，请停止。' }
    $tf080AccidentReinstallChecked = $true
    Write-Output '重装取消检查通过：D和目录记录未重建，根外保留文件校验值未变。'
}
```

预期程序True、D和目录记录False，随后打印重装取消检查通过，无报错或差异。
反馈两段完整输出，以及是否确实出现目录选择窗口、是否只点击取消。
本清单尚未运行；二次确认取消和使用中拒绝仍需之后用新合成根补验。
保留这个PowerShell和原校验值，不继续旧清单或自行新建根。
