# 保留测试数据，清除程序乙的旧安装权限记录

对应 [408df076候选](../../history/0.8.0/local-candidate-2026-10-02-task-dialog-final.md)。
**本清单第1～3步已由开发者执行通过，不要重复。** 仅卸载和普通权限重装前后
全部测试文件校验值未变，新管理员标记False；正确D的删除入口已显示，首屏
取消后程序及文件保留。下一步从 [删除验收清单第4步](uninstall-delete-acceptance.md#4-拒绝永久删除确认程序和数据应保留)
继续二次确认取消、使用中拒绝、实际删除和重装检查。以下内容仅保留追溯。
直接只读预检已通过：退出码0、READY、确切D、4个文件/475345字节。
重置前程序乙的Inno卸载记录有“安装时具有管理员权限”标记；它会使卸载器要求管理员
权限。普通PowerShell本身不能清除这个历史标记，同目录覆盖安装也可能保留它。
卸载器当时实际使用哪套配置仍未确定，本次先移除这一已确认的环境差异。

下面只卸载并重新安装程序乙，不删除任何训练数据。原A/B、原配置、新D、
新目录记录和根外检查文件全部保留；只移除程序乙的二进制与旧安装记录。
不用创建新数据、改名或修改权限。所有步骤已由开发者手动执行并反馈通过。

## 1. 在刚才的普通PowerShell记下文件校验值

关闭TrainingFeedback和卸载窗口，保留刚才打印READY的普通PowerShell窗口。
只复制代码块内部的完整命令，不复制三个反引号。任何报错都停止并反馈原文，
不继续下一步。路径已填写，不需要修改。

```powershell
. {
    $ErrorActionPreference = 'Stop'
    $tf080ContextPrepared = $false
    $tf080ContextInstalled = $false
    $tf080ContextIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    if ([Security.Principal.WindowsPrincipal]::new($tf080ContextIdentity).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw '当前是管理员权限，请停止。' }
    $tf080DeleteBase = 'C:\Users\41315\TrainingFeedback-080-Delete-20261002-153609'
    $tf080DeleteRoot = Join-Path $tf080DeleteBase 'TrainingFeedbackData'
    $tf080DeleteConfig = Join-Path $tf080DeleteBase '独立测试配置'
    $tf080DeletePointer = Join-Path $tf080DeleteConfig 'TrainingFeedback\locator.json'
    $tf080DeleteOutside = Join-Path $tf080DeleteBase '根外保留文件'
    $tf080DeleteOriginalA = 'E:\TrainingFeedback-080-PathFix\测试数据 A'
    $tf080DeleteOriginalB = 'E:\TrainingFeedback-080-PathFix\测试数据 B'
    $tf080DeleteOriginalConfig = 'E:\TrainingFeedback-080-PathFix\测试配置'
    $tf080DeleteProgram = 'E:\TrainingFeedback-080-PathFix\程序 乙'
    $tf080DeleteSetup = 'E:\Github\TrainingFeedback\dist\installer\TrainingFeedback-0.8.0-Setup.exe'
    if ($env:LOCALAPPDATA -ne $tf080DeleteConfig) { throw '当前窗口不是刚才的独立配置，请停止。' }
    if ((Get-FileHash -LiteralPath $tf080DeleteSetup -Algorithm SHA256).Hash -ne '408df0767146fcaf6d8324da88e15928d07da86969da1026fc4e6b426976fb28') { throw '安装包不是本次候选，请停止。' }
    if ((Get-FileHash -LiteralPath (Join-Path $tf080DeleteProgram 'TrainingFeedback.exe') -Algorithm SHA256).Hash -ne '20a06f04af9b42ff828b7e5285ce2167d87b4796c23b1df7e154e0b9a5291e1d') { throw '已安装程序不是本次候选，请停止。' }
    $tf080ContextRecordedRoot = (Get-Content -LiteralPath $tf080DeletePointer -Raw | ConvertFrom-Json).data_root
    if ([IO.Path]::GetFullPath($tf080ContextRecordedRoot) -ne [IO.Path]::GetFullPath($tf080DeleteRoot)) { throw '目录记录不是实际D，请停止。' }
    $tf080ContextDirectories = @($tf080DeleteOriginalA, $tf080DeleteOriginalB, $tf080DeleteOriginalConfig, $tf080DeleteOutside, $tf080DeleteRoot)
    foreach ($tf080ContextDirectory in $tf080ContextDirectories) {
        if (-not (Test-Path -LiteralPath $tf080ContextDirectory -PathType Container)) { throw ('应保留的目录不存在，请停止：' + $tf080ContextDirectory) }
    }
    function Get-Tf080ContextFileState {
        foreach ($tf080ContextDirectory in $tf080ContextDirectories) {
            Get-ChildItem -LiteralPath $tf080ContextDirectory -Recurse -Force -File -ErrorAction Stop | ForEach-Object {
                $_.FullName + '|' + (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256 -ErrorAction Stop).Hash
            }
        }
        $tf080DeletePointer + '|' + (Get-FileHash -LiteralPath $tf080DeletePointer -Algorithm SHA256 -ErrorAction Stop).Hash
    }
    $tf080ContextBefore = @(Get-Tf080ContextFileState | Sort-Object)
    if ($tf080ContextBefore.Count -eq 0) { throw '没有取得文件校验值，请停止。' }
    $tf080ContextPrepared = $true
    Write-Output '准备通过：已记录A/B、两套配置中的训练记录、D和根外文件校验值。'
}
```

预期只有准备通过提示，无报错。它只读取已知测试文件并保存校验值，还未卸载。

## 2. 仅卸载程序，再用同一个窗口重新安装

第1步成功后，运行下面整个代码块。卸载器可能出现权限确认，此次仅卸载程序
可按提示允许；普通卸载确认选择Yes（是）。`/KEEPDATA`使它直接保留数据，
不会运行数据预检或删除提交，不需要在旧窗口选择删除。

卸载完成后命令会检查程序和旧卸载记录已移除、所有测试文件校验值未变，
然后自动打开同一个安装包。安装目录必须是`E:\TrainingFeedback-080-PathFix\程序 乙`。
按Next（下一步）完成安装，最后**取消勾选Launch TrainingFeedback（启动程序）**，
再点击Finish（完成）。重新安装时若出现权限确认，取消并反馈，不继续。

```powershell
. {
    $ErrorActionPreference = 'Stop'
    $tf080ContextInstalled = $false
    if (-not $tf080ContextPrepared) { throw '第1步未成功，请停止。' }
    if ([Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw '当前是管理员权限，请停止。' }
    if ($env:LOCALAPPDATA -ne $tf080DeleteConfig) { throw '独立配置已变化，请停止。' }
    if ((Get-FileHash -LiteralPath $tf080DeleteSetup -Algorithm SHA256).Hash -ne '408df0767146fcaf6d8324da88e15928d07da86969da1026fc4e6b426976fb28') { throw '安装包已变化，请停止。' }
    Start-Process -FilePath (Join-Path $tf080DeleteProgram 'unins000.exe') -ArgumentList '/KEEPDATA' -Wait
    foreach ($tf080ContextProgramFile in @('TrainingFeedback.exe', 'unins000.exe', 'unins000.dat')) {
        if (Test-Path -LiteralPath (Join-Path $tf080DeleteProgram $tf080ContextProgramFile)) { throw ('仅卸载尚未完成，请停止：' + $tf080ContextProgramFile) }
    }
    $tf080ContextDifference = @(Compare-Object $tf080ContextBefore @(Get-Tf080ContextFileState | Sort-Object))
    if ($tf080ContextDifference.Count -ne 0) { $tf080ContextDifference; throw '测试文件有变化，请停止，不重装。' }
    Write-Output '仅卸载通过：旧安装记录已移除，测试文件校验值全部未变。'
    Start-Process -FilePath $tf080DeleteSetup -ArgumentList ('/DIR="' + $tf080DeleteProgram + '"') -Wait
    if ((Get-FileHash -LiteralPath (Join-Path $tf080DeleteProgram 'TrainingFeedback.exe') -Algorithm SHA256).Hash -ne '20a06f04af9b42ff828b7e5285ce2167d87b4796c23b1df7e154e0b9a5291e1d') { throw '重装后的程序不是本次候选，请停止。' }
    $tf080ContextDifference = @(Compare-Object $tf080ContextBefore @(Get-Tf080ContextFileState | Sort-Object))
    if ($tf080ContextDifference.Count -ne 0) { $tf080ContextDifference; throw '重装后测试文件有变化，请停止。' }
    $tf080ContextLogStream = [IO.File]::OpenRead((Join-Path $tf080DeleteProgram 'unins000.dat'))
    try {
        $tf080ContextHeader = [byte[]]::new(448)
        if ($tf080ContextLogStream.Read($tf080ContextHeader, 0, 448) -ne 448) { throw '卸载记录头不完整，请停止。' }
    } finally { $tf080ContextLogStream.Dispose() }
    if ([Text.Encoding]::ASCII.GetString($tf080ContextHeader, 0, 64).TrimEnd([char]0) -ne 'Inno Setup Uninstall Log (b) 64-bit' -or [BitConverter]::ToInt32($tf080ContextHeader, 320) -ne 1054) { throw '卸载记录格式不符，请停止。' }
    $tf080ContextFlags = [BitConverter]::ToInt32($tf080ContextHeader, 332)
    Write-Output ('新卸载记录的管理员标记：' + (($tf080ContextFlags -band 1) -ne 0))
    if (($tf080ContextFlags -band 193) -ne 0) { throw '新安装仍有管理员或高权限标记，请停止。' }
    $tf080ContextInstalled = $true
    Write-Output '普通权限重装检查通过，所有测试文件校验值未变。'
}
```

预期输出“仅卸载通过”、管理员标记False、“普通权限重装检查通过”。标记检查
仅查看本候选的Inno记录头，不替代程序归属和数据删除预检。报错、校验值差异、
管理员标记True或安装目录不符，都停止并反馈完整输出。

## 3. 只看删除入口，然后取消

前两步都成功，且没有自动打开主程序后，在同一窗口运行：

```powershell
. {
    $ErrorActionPreference = 'Stop'
    if (-not $tf080ContextInstalled) { throw '普通权限重装尚未通过，请停止。' }
    if ($env:LOCALAPPDATA -ne $tf080DeleteConfig) { throw '独立配置已变化，请停止。' }
    Start-Process -FilePath (Join-Path $tf080DeleteProgram 'unins000.exe') -Wait
    $tf080ContextDifference = @(Compare-Object $tf080ContextBefore @(Get-Tf080ContextFileState | Sort-Object))
    if ($tf080ContextDifference.Count -ne 0) { $tf080ContextDifference; throw '取消后测试文件有变化，请停止。' }
    if (-not (Test-Path -LiteralPath (Join-Path $tf080DeleteProgram 'TrainingFeedback.exe'))) { throw '取消后程序被卸载，请停止。' }
    Write-Output '取消后程序保留，全部测试文件校验值未变。'
}
```

预期对话框显示“同时永久删除当前数据…”和完整路径
`C:\Users\41315\TrainingFeedback-080-Delete-20261002-153609\TrainingFeedbackData`。
这次只截图，点击“取消”，**不选择删除，也不选择仅卸载**。
如果还在拒绝、显示其它路径或出现权限确认，也取消并反馈。
回到PowerShell应看到取消后检查通过。反馈第2～3步完整输出和卸载窗口截图。

反馈模板：仅卸载检查通过／失败；新管理员标记False／True；重装文件比较通过／失败；
显示的D路径；是否出现删除选项；取消后检查结果。本组反馈已收到，当前从原删除清单第4步继续。
