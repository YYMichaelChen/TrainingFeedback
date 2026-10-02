# 0.8.0 删除验收：使用全新的测试数据D

对应 [408df076标准对话框候选](../../history/0.8.0/local-candidate-2026-10-02-task-dialog-final.md)。
这份材料已准备，所有新步骤均未运行。先只做第1步确认环境，再继续后面的步骤。
原A/B和原测试配置保留，不改权限。删除目标只有本清单新建的“待删除数据 D”
及新配置中的目录记录；最后确认删除时程序乙也会卸载。根外检查文件、原A/B
与原目录记录必须保留。不要选择任何其它数据目录。

命令在PowerShell 7运行。只复制代码块里的命令，不复制开头或结尾的三个反引号。
每步出现报错就停下反馈完整输出，不自己清理、修改权限或重做全部步骤。

## 1. 先确认PowerShell不是以管理员身份运行

关闭TrainingFeedback，保留原PowerShell窗口。在开始菜单找到PowerShell 7，
普通点击打开一个新窗口，不选择“以管理员身份运行”。在新窗口运行：

```powershell
$tf080DeleteIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
$tf080DeletePrincipal = [Security.Principal.WindowsPrincipal]::new($tf080DeleteIdentity)
$tf080DeletePrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
```

预期输出False。先反馈这一行结果。True表示当前仍是管理员权限，不做后面的
准备和删除；反馈结果即可，不取得原A/B的所有权。False仅确认权限环境，不能
单独认证新数据归属或删除功能。

## 2. 在同一个新窗口准备独立测试路径

第1步为False后，在同一个新窗口运行。路径由命令生成，不需要修改：

```powershell
if ($tf080DeletePrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw '当前仍是管理员权限，请停止。' }
$tf080DeleteSetup = 'E:\Github\TrainingFeedback\dist\installer\TrainingFeedback-0.8.0-Setup.exe'
$tf080DeleteProgram = 'E:\TrainingFeedback-080-PathFix\程序 乙'
if ((Get-FileHash -LiteralPath $tf080DeleteSetup -Algorithm SHA256).Hash -ne '408df0767146fcaf6d8324da88e15928d07da86969da1026fc4e6b426976fb28') { throw '安装包不是本次候选，请停止。' }
if (-not (Test-Path -LiteralPath (Join-Path $tf080DeleteProgram 'TrainingFeedback.exe'))) { throw '程序乙不存在，请停止并反馈。' }
$tf080DeleteBase = Join-Path $env:USERPROFILE ('TrainingFeedback-080-Delete-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
if (Test-Path -LiteralPath $tf080DeleteBase) { throw '新测试父目录已存在，请停止。' }
$tf080DeleteConfig = Join-Path $tf080DeleteBase '独立测试配置'
$tf080DeleteRoot = Join-Path $tf080DeleteBase '待删除数据 D'
$tf080DeleteOutside = Join-Path $tf080DeleteBase '根外保留文件'
$tf080DeletePointer = Join-Path $tf080DeleteConfig 'TrainingFeedback\locator.json'
$tf080DeleteOriginalA = 'E:\TrainingFeedback-080-PathFix\测试数据 A'
$tf080DeleteOriginalB = 'E:\TrainingFeedback-080-PathFix\测试数据 B'
$tf080DeleteOriginalConfig = 'E:\TrainingFeedback-080-PathFix\测试配置'
$tf080DeleteSid = $tf080DeleteIdentity.User.Value
New-Item -ItemType Directory -Path $tf080DeleteConfig, $tf080DeleteOutside -ErrorAction Stop | Out-Null
Set-Content -LiteralPath (Join-Path $tf080DeleteOutside '保留检查.txt') -Value '删除D后这份文件仍应保留' -Encoding utf8 -ErrorAction Stop
foreach ($tf080DeleteOwnedPath in @($tf080DeleteBase, $tf080DeleteConfig, $tf080DeleteOutside)) {
    if ((Get-Acl -LiteralPath $tf080DeleteOwnedPath -ErrorAction Stop).GetOwner([Security.Principal.SecurityIdentifier]).Value -ne $tf080DeleteSid) { throw ('新测试目录归属不符，请停止：' + $tf080DeleteOwnedPath) }
}
$env:LOCALAPPDATA = $tf080DeleteConfig
Write-Output ('新测试父目录：' + $tf080DeleteBase)
Write-Output ('唯一待删除数据目录：' + $tf080DeleteRoot)
Write-Output ('独立目录记录：' + $tf080DeletePointer)
```

预期打印三个新路径，D和新的目录记录此时还不存在。命令只设置当前新窗口的
配置路径，不改变原PowerShell的测试配置。出现归属不符就保留现场并反馈，
不修改ACL或改用原A/B。

## 3. 手动创建新数据D，再检查文件归属

从这个新PowerShell启动程序：

```powershell
Start-Process -FilePath (Join-Path $tf080DeleteProgram 'TrainingFeedback.exe') -Wait
```

应进入数据目录选择。选择创建新目录，父目录填第2步打印的新测试父目录，
名称填“待删除数据 D”。不要打开原A/B。进入后在“设置”确认当前完整路径
与第2步的唯一待删除目录一致，然后关闭程序。不创建个人训练或审核记录。
回到同一PowerShell运行：

```powershell
if (-not (Test-Path -LiteralPath $tf080DeleteRoot) -or -not (Test-Path -LiteralPath $tf080DeletePointer)) { throw '新数据D或目录记录未创建，请停止。' }
$tf080DeleteOwnedItems = @($tf080DeleteRoot, $tf080DeletePointer) + @(Get-ChildItem -LiteralPath $tf080DeleteRoot -Recurse -Force -ErrorAction Stop | ForEach-Object FullName)
foreach ($tf080DeleteOwnedPath in $tf080DeleteOwnedItems) {
    if ((Get-Acl -LiteralPath $tf080DeleteOwnedPath -ErrorAction Stop).GetOwner([Security.Principal.SecurityIdentifier]).Value -ne $tf080DeleteSid) { throw ('新数据归属不符，请停止：' + $tf080DeleteOwnedPath) }
}
Write-Output '新数据D及目录记录归属检查通过'
```

预期输出归属检查通过。目录错误、打不开或归属报错算异常，反馈路径和提示，
不继续删除。这是只读文件检查，不能代替卸载器自己的安全检查。

## 4. 拒绝永久删除确认，程序和数据应保留

程序已关闭后，运行以下命令记录文件校验值并打开卸载器：

```powershell
function Get-Tf080DeleteFileState {
    param([string[]]$Directories, [string]$Locator = '')
    foreach ($tf080DeleteDirectory in $Directories) {
        Get-ChildItem -LiteralPath $tf080DeleteDirectory -Recurse -Force -File -ErrorAction Stop | ForEach-Object {
            $_.FullName + '|' + (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256 -ErrorAction Stop).Hash
        }
    }
    if ($Locator) { $Locator + '|' + (Get-FileHash -LiteralPath $Locator -Algorithm SHA256 -ErrorAction Stop).Hash }
}
$tf080DeleteProtected = @($tf080DeleteOriginalA, $tf080DeleteOriginalB, $tf080DeleteOriginalConfig, $tf080DeleteOutside)
$tf080DeleteProtectedBefore = @(Get-Tf080DeleteFileState -Directories $tf080DeleteProtected | Sort-Object)
$tf080DeleteAllBefore = @(Get-Tf080DeleteFileState -Directories ($tf080DeleteProtected + @($tf080DeleteRoot)) -Locator $tf080DeletePointer | Sort-Object)
Start-Process -FilePath (Join-Path $tf080DeleteProgram 'unins000.exe') -Wait
```

窗口应提供“同时永久删除当前数据…”，显示的确切目录必须是新D。如果仍不能
删除、显示其它路径或布局不正常，点击取消，反馈截图和新D路径，不绕过检查。
正常时点击删除选项；再次确认窗口仍应显示D，默认是“否”。选择No（否），
整个卸载应取消，不确认任何删除或卸载。回到PowerShell运行：

```powershell
Test-Path -LiteralPath (Join-Path $tf080DeleteProgram 'TrainingFeedback.exe')
Test-Path -LiteralPath $tf080DeleteRoot
Test-Path -LiteralPath $tf080DeletePointer
Compare-Object $tf080DeleteAllBefore @(Get-Tf080DeleteFileState -Directories ($tf080DeleteProtected + @($tf080DeleteRoot)) -Locator $tf080DeletePointer | Sort-Object)
```

预期三项True，比较没有输出。文件消失、比较有差异或未经确认就删除，记失败，
停下反馈输出和窗口提示，保留剩余文件。

## 5. D正在使用时，不能删除

从同一PowerShell运行下面两条命令。第一条不加Wait，先等程序完全打开D，
在“设置”确认确实是新D，再运行第二条：

```powershell
Start-Process -FilePath (Join-Path $tf080DeleteProgram 'TrainingFeedback.exe')
```

```powershell
Start-Process -FilePath (Join-Path $tf080DeleteProgram 'unins000.exe') -Wait
```

卸载窗口应不提供删除选项，说明数据正在使用或不能安全删除。点击“取消”，
不要仅卸载程序。回到客户端确认仍可查看D，然后关闭程序。反馈卸载窗口截图，
说明是否无删除入口、取消后D能否继续查看。如果能选删除或客户端异常就停止。
此时程序曾打开，不能与第4步数据库文件校验值直接比较。

## 6. 明确确认删除，只删除D和新目录记录

客户端已关闭，再从同一窗口启动卸载器：

```powershell
Start-Process -FilePath (Join-Path $tf080DeleteProgram 'unins000.exe') -Wait
```

这一步会删除新D内全部合成测试文件、新配置中的目录记录，并卸载程序乙。
核对显示的待删除路径完整等于第2步的D，再点击“同时永久删除当前数据…”。
二次确认仍为D时选择Yes（是）；随后普通卸载确认也确认继续。任一窗口显示
其它数据路径就取消，反馈，不继续。退出后运行：

```powershell
Test-Path -LiteralPath $tf080DeleteRoot
Test-Path -LiteralPath $tf080DeletePointer
Test-Path -LiteralPath (Join-Path $tf080DeleteProgram 'TrainingFeedback.exe')
Test-Path -LiteralPath $tf080DeleteOriginalA
Test-Path -LiteralPath $tf080DeleteOriginalB
Get-Content -LiteralPath (Join-Path $tf080DeleteOutside '保留检查.txt')
Compare-Object $tf080DeleteProtectedBefore @(Get-Tf080DeleteFileState -Directories $tf080DeleteProtected | Sort-Object)
```

预期前五项False、False、False、True、True；检查文件内容仍为
“删除D后这份文件仍应保留”；最后比较没有输出，原A/B、原配置和根外文件
内容未变。D残留却显示完成、其它文件消失或比较有变化都记失败，停下反馈，
不自行删除残留或恢复记录。

## 7. 重装后不会偷偷重建D

在同一新PowerShell用同一候选重新安装程序乙，完成页取消勾选自动启动：

```powershell
if ((Get-FileHash -LiteralPath $tf080DeleteSetup -Algorithm SHA256).Hash -ne '408df0767146fcaf6d8324da88e15928d07da86969da1026fc4e6b426976fb28') { throw '安装包不是本次候选，请停止。' }
Start-Process -FilePath $tf080DeleteSetup -ArgumentList ('/DIR="' + $tf080DeleteProgram + '"') -Wait
Start-Process -FilePath (Join-Path $tf080DeleteProgram 'TrainingFeedback.exe') -Wait
```

启动后应回到数据目录选择，因为新配置的目录记录已删除。只点击取消，退出
程序，不创建新目录，也不在这个新窗口打开原A/B。然后运行：

```powershell
Test-Path -LiteralPath (Join-Path $tf080DeleteProgram 'TrainingFeedback.exe')
Test-Path -LiteralPath $tf080DeleteRoot
Test-Path -LiteralPath $tf080DeletePointer
Compare-Object $tf080DeleteProtectedBefore @(Get-Tf080DeleteFileState -Directories $tf080DeleteProtected | Sort-Object)
```

预期True、False、False，比较没有输出。自动打开或重建D、取消后新建目录记录
算失败，反馈提示和输出。全部检查后关闭这个新PowerShell；原PowerShell仍用
原隔离配置，原A/B可以继续使用。不要删除新测试父目录，它留作证据。

反馈模板：第1步False/True；第3步归属通过/报错；第4步窗口、三行输出和比较；
第5步截图及D能否继续查看；第6、7步完整输出及启动现象。没有执行的步骤写
“未运行”。准备成功不等于删除通过，实际结果只认证这个精确本地候选。
