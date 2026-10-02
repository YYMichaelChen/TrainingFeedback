# 卸载补验：删除前点“否”，程序打开时拒绝删除

使用已安装的 [49de95af候选](../../history/0.8.0/installer-directory-progress-2026-10-02.md)，
程序文件校验值以1d2f09f7开头。安装目录页复测已通过，不重新安装。
**2026-10-03本清单两项均已通过，不重复运行。** 开发者确认第二次点了“否”，
程序/E/目录记录保留且全部文件校验未变；使用中拒绝截图及取消后核对通过。
第4步没留截图如实记录，结果见上述候选记录末尾。以下步骤保留作追溯，
不要重新创建测试目录、删除E或重复卸载；下一步转响应及其它剩余验收材料。

本轮新建数据称为E，名称采用程序默认的TrainingFeedbackData，命令会打印完整
路径。E只含合成测试内容，使用全新独立配置。原A/B、原配置和根外文件保留，
已删除的D不重建。**本轮预期不删除数据，也不卸载程序；第二次确认必须点“否”，
不要点“是”。** 若误点“是”，立即反馈实际选择和输出，不重装、不补建来掩盖结果。

命令在普通权限PowerShell 7中运行，所有步骤使用同一个窗口。只复制代码块内部
完整命令，包括最外层的点和花括号，不复制三个反引号。任何报错都停止后续步骤，
反馈完整输出和窗口截图，不自行修改路径、权限或清理文件。

## 1. 关闭程序，准备全新的测试目录

先关闭TrainingFeedback和卸载窗口。在普通PowerShell运行下方完整命令。
命令先核对程序和普通权限，再创建新测试父目录、配置及根外检查文件；
它不创建数据E。只修改当前PowerShell的配置位置，不修改系统环境变量。

```powershell
. {
    $ErrorActionPreference = 'Stop'
    $tf080CancelPrepared = $false
    $tf080CancelReady = $false
    $tf080CancelPassed = $false
    $tf080CancelIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    if ([Security.Principal.WindowsPrincipal]::new($tf080CancelIdentity).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw '当前是管理员权限，请停止。' }
    $tf080CancelProgram = 'E:\TrainingFeedback-080-PathFix\程序 乙'
    $tf080CancelExe = Join-Path $tf080CancelProgram 'TrainingFeedback.exe'
    $tf080CancelExeHash = '1d2f09f781a8a2217921946f48ffc187c9cdb94e716cafa124880dd2cc9a8961'
    if ((Get-FileHash -LiteralPath $tf080CancelExe -Algorithm SHA256).Hash -ne $tf080CancelExeHash) { throw '已安装程序不是本次目录页候选，请停止。' }
    if (-not (Test-Path -LiteralPath (Join-Path $tf080CancelProgram 'unins000.exe') -PathType Leaf)) { throw '卸载器不存在，请停止。' }
    $tf080CancelBase = Join-Path $env:USERPROFILE ('TrainingFeedback-080-Cancel-' + [guid]::NewGuid().ToString('N'))
    if (Test-Path -LiteralPath $tf080CancelBase) { throw '新测试父目录已存在，请停止。' }
    $tf080CancelConfig = Join-Path $tf080CancelBase '独立测试配置'
    $tf080CancelRoot = Join-Path $tf080CancelBase 'TrainingFeedbackData'
    $tf080CancelPointer = Join-Path $tf080CancelConfig 'TrainingFeedback\locator.json'
    $tf080CancelOutside = Join-Path $tf080CancelBase '根外保留文件'
    $tf080CancelOldBase = 'C:\Users\41315\TrainingFeedback-080-Delete-20261002-153609'
    $tf080CancelProtected = @('E:\TrainingFeedback-080-PathFix\测试数据 A', 'E:\TrainingFeedback-080-PathFix\测试数据 B', 'E:\TrainingFeedback-080-PathFix\测试配置', (Join-Path $tf080CancelOldBase '根外保留文件'), $tf080CancelOutside)
    New-Item -ItemType Directory -Path $tf080CancelConfig, $tf080CancelOutside | Out-Null
    Set-Content -LiteralPath (Join-Path $tf080CancelOutside '保留检查.txt') -Value '取消卸载后这份测试文件必须保留' -Encoding utf8
    $tf080CancelSid = $tf080CancelIdentity.User.Value
    foreach ($tf080CancelOwnedPath in @($tf080CancelBase, $tf080CancelConfig, $tf080CancelOutside)) {
        if ((Get-Acl -LiteralPath $tf080CancelOwnedPath).GetOwner([Security.Principal.SecurityIdentifier]).Value -ne $tf080CancelSid) { throw ('测试目录归属不符，请停止：' + $tf080CancelOwnedPath) }
    }
    function Get-Tf080CancelFileState {
        param([string[]]$Directories, [string]$Locator = '')
        foreach ($tf080CancelDirectory in $Directories) {
            if (-not (Test-Path -LiteralPath $tf080CancelDirectory -PathType Container)) { throw ('应保留目录不存在：' + $tf080CancelDirectory) }
            Get-ChildItem -LiteralPath $tf080CancelDirectory -Recurse -Force -File | ForEach-Object {
                $_.FullName + '|' + (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
            }
        }
        if ($Locator) { $Locator + '|' + (Get-FileHash -LiteralPath $Locator -Algorithm SHA256).Hash }
    }
    $tf080CancelProtectedBefore = @(Get-Tf080CancelFileState -Directories $tf080CancelProtected | Sort-Object)
    if ($tf080CancelProtectedBefore.Count -eq 0) { throw '未取得保留文件校验值，请停止。' }
    $env:LOCALAPPDATA = $tf080CancelConfig
    $tf080CancelPrepared = $true
    Write-Output ('新测试父目录：' + $tf080CancelBase)
    Write-Output ('本轮数据E完整路径：' + $tf080CancelRoot)
    Write-Output ('新独立配置：' + $tf080CancelConfig)
    Write-Output '准备通过。下一步手动创建E，不打开原A/B。'
}
```

预期打印三个新路径和“准备通过”。任何归属或文件校验报错都停止；不要取得
原A/B所有权。如果出现Windows权限确认，先取消，反馈是哪一步出现。

## 2. 手动创建E，保留默认名称，然后关闭程序

在同一PowerShell运行：

```powershell
. {
    $ErrorActionPreference = 'Stop'
    if (-not $tf080CancelPrepared -or $env:LOCALAPPDATA -ne $tf080CancelConfig) { throw '第1步未成功或配置已变化，请停止。' }
    if ((Test-Path -LiteralPath $tf080CancelRoot) -or (Test-Path -LiteralPath $tf080CancelPointer)) { throw '本轮E或目录记录已存在，请停止。' }
    if ((Get-FileHash -LiteralPath $tf080CancelExe -Algorithm SHA256).Hash -ne $tf080CancelExeHash) { throw '程序已变化，请停止。' }
    Start-Process -FilePath $tf080CancelExe -Wait
}
```

应出现“选择训练反馈数据目录”。选择“创建新的数据目录”，在“父目录”填第1步
打印的新测试父目录；“新目录名称”保持TrainingFeedbackData，不另填“数据E”。
确认“将创建”后的完整路径等于第1步的数据E路径，再点“确定”。进入程序后打开
“设置”，再次核对当前数据目录；无需写训练或审核记录。核对后关闭整个主程序。
没有出现选择窗口、路径不一致或打不开都停止，反馈截图，不打开原A/B来替代E。

## 3. 核对E归属和文件，打开卸载器

主程序已关闭后运行下方完整命令。它记录E、目录记录和根外文件的校验值，
再打开卸载器。只有最后出现“E归属和文件核对通过”才能继续第4步。

```powershell
. {
    $ErrorActionPreference = 'Stop'
    $tf080CancelReady = $false
    $tf080CancelPassed = $false
    function Assert-Tf080CancelContext {
        if (-not $tf080CancelPrepared) { throw '第1步未成功，请停止。' }
        if ([Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw '当前是管理员权限，请停止。' }
        if ($env:LOCALAPPDATA -ne $tf080CancelConfig) { throw '新独立配置已变化，请停止。' }
        if ((Get-FileHash -LiteralPath $tf080CancelExe -Algorithm SHA256).Hash -ne $tf080CancelExeHash) { throw '程序已变化，请停止。' }
        if (-not (Test-Path -LiteralPath $tf080CancelRoot -PathType Container) -or -not (Test-Path -LiteralPath $tf080CancelPointer -PathType Leaf)) { throw 'E或目录记录不存在，请停止。' }
        $tf080CancelRecordedRoot = (Get-Content -LiteralPath $tf080CancelPointer -Raw | ConvertFrom-Json).data_root
        if (-not $tf080CancelRecordedRoot -or [IO.Path]::GetFullPath($tf080CancelRecordedRoot) -ne [IO.Path]::GetFullPath($tf080CancelRoot)) { throw '目录记录未指向本轮E，请停止。' }
        if ((Test-Path -LiteralPath (Join-Path $tf080CancelOldBase 'TrainingFeedbackData')) -or (Test-Path -LiteralPath (Join-Path $tf080CancelOldBase '独立测试配置\TrainingFeedback\locator.json'))) { throw '已删除的D或旧记录被重建，请停止。' }
    }
    Assert-Tf080CancelContext
    $tf080CancelOwnedItems = @($tf080CancelRoot, $tf080CancelPointer) + @(Get-ChildItem -LiteralPath $tf080CancelRoot -Recurse -Force | ForEach-Object FullName)
    foreach ($tf080CancelOwnedPath in $tf080CancelOwnedItems) {
        if ((Get-Acl -LiteralPath $tf080CancelOwnedPath).GetOwner([Security.Principal.SecurityIdentifier]).Value -ne $tf080CancelSid) { throw ('E归属不符，请停止：' + $tf080CancelOwnedPath) }
    }
    $tf080CancelDifference = @(Compare-Object $tf080CancelProtectedBefore @(Get-Tf080CancelFileState -Directories $tf080CancelProtected | Sort-Object))
    if ($tf080CancelDifference.Count -ne 0) { $tf080CancelDifference; throw '创建E时原文件有变化，请停止。' }
    $tf080CancelAllBefore = @(Get-Tf080CancelFileState -Directories ($tf080CancelProtected + @($tf080CancelRoot)) -Locator $tf080CancelPointer | Sort-Object)
    $tf080CancelReady = $true
    Write-Output ('E归属和文件核对通过：' + $tf080CancelRoot)
    Start-Process -FilePath (Join-Path $tf080CancelProgram 'unins000.exe') -Wait
}
```

卸载器应显示第1步的E完整路径，提供“同时永久删除当前数据…”。没有此选项、
显示其它路径或文字按钮看不全，就点“取消”并反馈截图，不改权限绕过检查。

## 4. 进入第二次确认，明确点“否”，再核对文件

先核对卸载器显示的是E，然后点“同时永久删除当前数据…”。第二个确认窗口
也应显示E，默认选择应为“否”。**本步点No（否），不要点Yes（是）。**
点“否”后应取消整个卸载，程序和E均保留；不要再选择“仅卸载程序”。
保留第二次确认截图，记下实际点击的按钮。回到PowerShell运行：

```powershell
. {
    $ErrorActionPreference = 'Stop'
    $tf080CancelPassed = $false
    if (-not $tf080CancelReady) { throw '第3步未成功，请停止。' }
    Test-Path -LiteralPath $tf080CancelExe
    Test-Path -LiteralPath $tf080CancelRoot
    Test-Path -LiteralPath $tf080CancelPointer
    Assert-Tf080CancelContext
    $tf080CancelDifference = @(Compare-Object $tf080CancelAllBefore @(Get-Tf080CancelFileState -Directories ($tf080CancelProtected + @($tf080CancelRoot)) -Locator $tf080CancelPointer | Sort-Object))
    if ($tf080CancelDifference.Count -ne 0) { $tf080CancelDifference; throw '点否后测试文件有变化，请停止。' }
    $tf080CancelPassed = $true
    Write-Output '点否后程序、E和目录记录保留，全部测试文件校验值未变。'
}
```

预期三个True，随后打印文件未变。False、差异或报错都停止后续检查，反馈实际
按钮、截图和完整输出。若误点“是”，应据实记录，不能把三项False解释成取消通过。

## 5. 保持E打开，再检查卸载器拒绝删除

第4步通过后，在同一PowerShell运行下面命令。此处不等待程序关闭，方便保持
主程序打开后启动卸载器。

```powershell
. {
    $ErrorActionPreference = 'Stop'
    if (-not $tf080CancelPassed) { throw '第4步文件检查未通过，请停止。' }
    Assert-Tf080CancelContext
    $tf080CancelClientProcess = Start-Process -FilePath $tf080CancelExe -PassThru
}
```

等主程序完全打开，在“设置”确认当前数据目录仍为E，**保持主程序打开**。
再回到同一PowerShell运行：

```powershell
. {
    $ErrorActionPreference = 'Stop'
    if (-not $tf080CancelPassed -or -not $tf080CancelClientProcess -or $tf080CancelClientProcess.HasExited) { throw '第4步未通过或主程序已关闭，请停止。' }
    Assert-Tf080CancelContext
    Start-Process -FilePath (Join-Path $tf080CancelProgram 'unins000.exe') -Wait
}
```

预期卸载器说明数据正在使用或当前不能安全删除，并且不提供可选的永久删除
入口。保留截图，点“取消”，不要点“仅卸载程序”。回到仍打开的主程序，确认
E的动作列表仍能查看，然后关闭主程序。若仍能选择永久删除、点击取消后程序
消失或主程序异常，停止并反馈；不要尝试确认删除。

## 6. 最后核对存在状态，反馈两项结果

主程序已关闭，卸载器也已取消后运行：

```powershell
. {
    $ErrorActionPreference = 'Stop'
    if (-not $tf080CancelPassed) { throw '第4步文件检查未通过，请停止。' }
    Test-Path -LiteralPath $tf080CancelExe
    Test-Path -LiteralPath $tf080CancelRoot
    Test-Path -LiteralPath $tf080CancelPointer
    Assert-Tf080CancelContext
    $tf080CancelDifference = @(Compare-Object $tf080CancelProtectedBefore @(Get-Tf080CancelFileState -Directories $tf080CancelProtected | Sort-Object))
    if ($tf080CancelDifference.Count -ne 0) { $tf080CancelDifference; throw '原A/B、原配置或根外文件有变化，请停止。' }
    Write-Output '程序、E和目录记录存在，原A/B、原配置和根外文件未变。'
}
```

预期三个True，随后打印保留核对结果。主程序正常启动可能更新E的数据库，
因此本步只比较原A/B、原配置和根外文件，不拿E与启动前校验值比较。
窗口表现必须由你确认，命令成功不能单独证明“使用中拒绝”通过。

反馈可直接写：

- 第4步：第二次确认默认是否为“否”；实际点了什么；三个True及文件未变是否通过；截图。
- 第5步：主程序打开E时，是否无永久删除入口；点取消后E能否继续查看；截图。
- 第6步：完整输出。若任何一步失败，补充步骤号、实际路径和完整错误。

完成后保留E和新配置，不删除、不重装。当前仍只认证本机精确候选的这两项，
不建立公开验收、个人使用或W4资格。
