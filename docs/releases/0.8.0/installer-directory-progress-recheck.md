# 安装目录页等待复测：先看反馈，再安装程序乙

本次使用 [49de95af新候选](../../history/0.8.0/installer-directory-progress-2026-10-02.md)。
旧408df076包的删除范围及删除后重装已反馈无问题，不重复。原A/B、原配置、
根外文件必须保留，已删除的D和它的目录记录不得被重建。本次不创建训练数据，
不卸载程序、不选择删除，只有第3步在原程序乙位置安装新二进制。
所有步骤尚未手动运行；每步报错都停止，反馈完整输出，不自行清理或改权限。

## 1. 保留普通PowerShell，记录测试文件并启动新包

关闭主程序。使用刚才删除后重装检查的普通PowerShell窗口，配置仍为本轮
独立测试配置。只复制下方代码块内部的完整命令，不复制三个反引号。
命令新建一个独立的安装页测试文件夹，记录已有测试文件，然后打开安装器。
安装器会先选中这个新建的“误选目录”，用于检查错误返回；不要直接安装到那里。

```powershell
. {
    $ErrorActionPreference = 'Stop'
    $tf080ProgressPrepared = $false
    if ([Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw '当前是管理员权限，请停止。' }
    $tf080ProgressBase = 'C:\Users\41315\TrainingFeedback-080-Delete-20261002-153609'
    $tf080ProgressConfig = Join-Path $tf080ProgressBase '独立测试配置'
    if ($env:LOCALAPPDATA -ne $tf080ProgressConfig) { throw '当前不是原独立配置，请停止。' }
    $tf080ProgressRoot = Join-Path $tf080ProgressBase 'TrainingFeedbackData'
    $tf080ProgressPointer = Join-Path $tf080ProgressConfig 'TrainingFeedback\locator.json'
    if ((Test-Path -LiteralPath $tf080ProgressRoot) -or (Test-Path -LiteralPath $tf080ProgressPointer)) { throw 'D或目录记录已出现，请停止并反馈。' }
    $tf080ProgressSetup = 'E:\Github\TrainingFeedback\dist\installer\TrainingFeedback-0.8.0-Setup.exe'
    $tf080ProgressProgram = 'E:\TrainingFeedback-080-PathFix\程序 乙'
    if ((Get-FileHash -LiteralPath $tf080ProgressSetup -Algorithm SHA256).Hash -ne '49de95af46f2ae0f20f36a7bbb1f4e6318a418cf9b117370ee130ced1b1dcdad') { throw '安装包不是本次目录页修复包，请停止。' }
    if ((Get-FileHash -LiteralPath (Join-Path $tf080ProgressProgram 'TrainingFeedback.exe') -Algorithm SHA256).Hash -ne '20a06f04af9b42ff828b7e5285ce2167d87b4796c23b1df7e154e0b9a5291e1d') { throw '程序乙不是刚才重装的旧候选，请停止。' }
    $tf080ProgressProtected = @('E:\TrainingFeedback-080-PathFix\测试数据 A', 'E:\TrainingFeedback-080-PathFix\测试数据 B', 'E:\TrainingFeedback-080-PathFix\测试配置', (Join-Path $tf080ProgressBase '根外保留文件'))
    function Get-Tf080ProgressFileState {
        foreach ($tf080ProgressDirectory in $tf080ProgressProtected) {
            if (-not (Test-Path -LiteralPath $tf080ProgressDirectory -PathType Container)) { throw ('应保留目录不存在：' + $tf080ProgressDirectory) }
            Get-ChildItem -LiteralPath $tf080ProgressDirectory -Recurse -Force -File -ErrorAction Stop | ForEach-Object {
                $_.FullName + '|' + (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256 -ErrorAction Stop).Hash
            }
        }
    }
    $tf080ProgressBefore = @(Get-Tf080ProgressFileState | Sort-Object)
    if ($tf080ProgressBefore.Count -eq 0) { throw '未取得保留文件校验值，请停止。' }
    $tf080ProgressTestDirectory = Join-Path $tf080ProgressBase ('安装页复测-' + [guid]::NewGuid().ToString('N'))
    $tf080ProgressOccupied = Join-Path $tf080ProgressTestDirectory '误选目录'
    New-Item -ItemType Directory -Path $tf080ProgressOccupied | Out-Null
    $tf080ProgressSentinel = Join-Path $tf080ProgressOccupied '保留检查.txt'
    Set-Content -LiteralPath $tf080ProgressSentinel -Value '误选此目录时不得覆盖或删除这个测试文件' -Encoding utf8
    $tf080ProgressSentinelBefore = (Get-FileHash -LiteralPath $tf080ProgressSentinel -Algorithm SHA256).Hash
    $tf080ProgressLog = Join-Path $tf080ProgressTestDirectory '安装日志.log'
    $tf080ProgressPrepared = $true
    Write-Output ('实际安装位置：' + $tf080ProgressProgram)
    Write-Output ('只用于检查错误返回的目录：' + $tf080ProgressOccupied)
    Write-Output ('日志位置：' + $tf080ProgressLog)
    Start-Process -FilePath $tf080ProgressSetup -ArgumentList ('/DIR="' + $tf080ProgressOccupied + '" /LOG="' + $tf080ProgressLog + '"') -Wait
}
```

## 2. 在“误选目录”点击Next，确认有反馈且能返回

安装器停在Select Destination Location（选择安装位置）时，路径应是刚才打印
的误选目录。点击Next（下一步）一次。应立即显示“正在检查安装目录”、当前
路径和等待说明；检查耗时很短时可能一闪而过。若等待仍有几秒，应能明确看到
正在检查，不反复点击Next。记录大约等了几秒以及是否仍像无反馈卡死，不用精确计时。

检查应拒绝这个含其它文件的目录并显示错误。点击OK（确定）后，进度页应消失，
回到目录选择页，Browse（浏览）、Next和Cancel（取消）应能正常使用。
截图保留错误提示和等待页（等待足够长时）。错误后停在进度页、无法操作、
或允许直接安装到误选目录，都停止，取消安装并反馈。

## 3. 改回程序乙，观察等待并完成同路径安装

在同一个安装器窗口把路径改为第1步打印的实际安装位置
`E:\TrainingFeedback-080-PathFix\程序 乙`，再点击Next一次。
记录是否出现检查说明、约等待几秒、检查后是否正常进入下一页。
然后按Next/Install（安装）完成安装。最后取消勾选Launch TrainingFeedback
（启动程序），再点Finish（完成）。不要选择其它安装位置，也不自动启动客户端。
出现权限确认、不能继续、仍无反馈卡顿或错误提示都记录并反馈；不要改测试权限。

## 4. 回到原PowerShell核对文件并输出检查日志

第1步命令等待安装器关闭后会返回提示符，再运行下面完整代码块：

```powershell
. {
    $ErrorActionPreference = 'Stop'
    if (-not $tf080ProgressPrepared) { throw '第1步未成功，请停止。' }
    if ((Get-FileHash -LiteralPath (Join-Path $tf080ProgressProgram 'TrainingFeedback.exe') -Algorithm SHA256).Hash -ne '1d2f09f781a8a2217921946f48ffc187c9cdb94e716cafa124880dd2cc9a8961') { throw '未安装本次完整新程序，请停止并反馈。' }
    if ((Test-Path -LiteralPath $tf080ProgressRoot) -or (Test-Path -LiteralPath $tf080ProgressPointer)) { throw '安装后D或目录记录被重建，请停止。' }
    if ((Get-FileHash -LiteralPath $tf080ProgressSentinel -Algorithm SHA256).Hash -ne $tf080ProgressSentinelBefore) { throw '误选目录的检查文件有变化，请停止。' }
    if (@(Get-ChildItem -LiteralPath $tf080ProgressOccupied -Force).Count -ne 1) { throw '误选目录出现其它文件，请停止。' }
    $tf080ProgressDifference = @(Compare-Object $tf080ProgressBefore @(Get-Tf080ProgressFileState | Sort-Object))
    if ($tf080ProgressDifference.Count -ne 0) { $tf080ProgressDifference; throw '根外保留文件有变化，请停止。' }
    Write-Output '安装文件核对通过：新程序hash匹配，测试文件未变，D和目录记录未重建。'
    Select-String -LiteralPath $tf080ProgressLog -SimpleMatch -Pattern 'directory-page check', 'selected target already checked' | ForEach-Object Line
}
```

预期先打印文件核对通过，再输出目录页检查开始/结束以及同路径目标已检查
的日志行。没有去重行不自动判失败，先反馈日志，由代理核对当时的旧程序登记。
任何校验报错都反馈原文，不自己修复目录。不要删除复测目录或日志。

反馈模板：误选目录是否显示等待、约几秒、是否拒绝及正常返回；程序乙约几秒、
是否有清楚反馈并顺利安装；完整命令输出；等待或错误截图。
本次不认证冷启动全部耗时、其它DPI/多屏或剩余卸载取消/使用中拒绝检查。
