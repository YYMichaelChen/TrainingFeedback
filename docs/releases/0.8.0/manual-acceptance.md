# 0.8.0 手动验收：按顺序操作

这份清单用于检查 0.8.0 安装包是否能正常安装、使用和卸载。
**当前先不继续M04/M05：** 最新卸载窗口截图存在布局与说明问题，程序乙已卸载，
B和目录记录仍存在，但取消卸载并未通过。A/B与目录记录归属为Windows管理员组，
当前删除选项按规则不可用。不要改这些目录的权限或删除它们；先执行
[修复包安装、显示和取消重试](uninstall-dialog-recheck.md)。此前A/B、重装和搬迁
结果保留在原候选记录中。新的可删除场景需普通测试账号下的新测试数据。
清理旧程序后的完整安装、使用和卸载检查尚未全部完成，已执行项目见下面的
最新进度；其它项目实际操作后才能记录为“通过”或“失败”。第一张截图的英文错误提示记为失败；第二张截图
已看到完整中文说明，但安装仍被旧程序阻塞。两张截图未提供安装包 hash，
详见 [问题记录](../../history/0.8.0/installation-error-2026-10-02.md) 和
[旧程序清理记录](../../history/0.8.0/legacy-program-cleanup-2026-10-02.md)。
先完成 M01～M05，再做后面的检查。某一步失败就记录现象，不必硬做后续步骤。

最新进度：准备与安装后的两项文件存在检查通过，安装后的296个程序文件也与
候选清单一致。首次启动退出后，目录记录和数据 A 的两项检查均为 `False`，
这两项检查通过。开发者已确认数据 A 创建、36个动作、两张图片、标记保存及
两次重启保留均通过。B创建、保存和A/B来回切换、标记互不混入也已通过。
同目录重装后的文件比较没有输出，A/B与目录记录的文件内容不变，这项已通过。
搬迁后比较同样无输出，旧程序EXE为False、新程序EXE为True，标记保留，
这些检查已通过；启动变量已更新为程序乙。之后卸载截图显示窗口和说明问题，
程序已卸载，B与目录记录仍存在，不能把取消卸载记为通过。先按顶部的修复包
重试链接检查新窗口和取消，不重复准备或M02检查。首次选择窗口和取消操作、
安装目录页、快捷方式目标与搬迁后初始当前B等还缺明确反馈；M01/M03整体不补填通过。
新目录训练/审核记录检查未单独反馈，卸载及后续检查尚未运行。

本次安装包和校验记录见 [10 月 2 日卸载窗口修复候选记录](../../history/0.8.0/local-candidate-2026-10-02-uninstall-dialog.md)。
安装包已重建；不要继续运行之前打开的旧安装器。新包 SHA-256
（用于确认文件没有换过）是：

`04a943dd3d3a88cc341dbe8ed1b7b646ef1194917ad5d4a0d710852613f6d90e`

## 旧程序已清理，先退出并重新打开安装器

1. 如果截图中的安装器还开着，点击右下角 `Cancel`（取消），退出这次安装。
   如果还有错误框，先点“确定”。本次安装包修复了旧路径选择逻辑，要使用本次新包。
2. 两份旧程序、安装登记及快捷方式已按你的要求清理。不需要再去找旧卸载器，
   也不要删除测试父目录、训练数据或备份。
3. 重新复制下面“一、先准备测试环境”的本次命令。新命令使用以 `tf080` 开头的
   变量和新的 `E:\TrainingFeedback-080-PathFix` 父目录，不使用旧验收窗口留下的
   `$program` 等变量。旧测试目录保持原样，不要删除。然后从同一个 PowerShell
   窗口执行 M01；命令会明确指定“程序 甲”，无需靠安装器猜上次的位置。

**应该看到：** 重新打开后，安装器能对新的空程序目录继续安装，不再因截图中的
旧程序路径阻塞。之后按 M01 核对程序和安装记录是否存在。

**失败判断与反馈：** 已退出并重新打开后仍出现截图里的旧路径错误，或安装不能
完成，都记为失败。请反馈本次选的完整安装目录、错误页截图，以及是否重新打开
过安装器。没有实际做的步骤记“未运行”，不要直接删除目录继续测试。

## 一、先准备测试环境

1. 登录一个专门用于测试的普通 Windows 账户，不要用已有个人训练数据的账户
   做删除测试。如果没有这样的账户，先告诉我，暂不进行安装、卸载删除测试。
2. 打开 **PowerShell 7**。下面的命令都在这个窗口运行，先不要关闭它。
3. 选一个全新的测试父目录。下面以 `E:\TrainingFeedback-080-PathFix` 为例。
   如果这个目录已经存在，只改下面第一行，换成一个新的目录名。
4. 复制下面整段命令到 PowerShell，按回车。它只创建测试目录，不启动程序。

```powershell
. {
$tf080Setup = $null
$tf080Program = $null
$tf080AcceptanceDirectory = 'E:\TrainingFeedback-080-PathFix'
if (Test-Path -LiteralPath $tf080AcceptanceDirectory) { throw '测试目录已存在，请换一个新目录名。' }
$tf080Setup = 'E:\Github\TrainingFeedback\dist\installer\TrainingFeedback-0.8.0-Setup.exe'
if (-not (Test-Path -LiteralPath $tf080Setup)) { throw '找不到安装包，请先确认安装包路径。' }
if ((Get-FileHash -LiteralPath $tf080Setup -Algorithm SHA256).Hash -ne '04a943dd3d3a88cc341dbe8ed1b7b646ef1194917ad5d4a0d710852613f6d90e') { throw '安装包不是本次卸载窗口修复包，请使用更新后的文件。' }
$env:LOCALAPPDATA = Join-Path $tf080AcceptanceDirectory '测试配置'
$tf080Program = Join-Path $tf080AcceptanceDirectory '程序 甲'
$tf080ProgramNext = Join-Path $tf080AcceptanceDirectory '程序 乙'
$tf080RootA = Join-Path $tf080AcceptanceDirectory '测试数据 A'
$tf080RootB = Join-Path $tf080AcceptanceDirectory '测试数据 B'
$tf080Outside = Join-Path $tf080AcceptanceDirectory '根外备份'
$tf080Pointer = Join-Path $env:LOCALAPPDATA 'TrainingFeedback/locator.json'
New-Item -ItemType Directory -Path $env:LOCALAPPDATA, $tf080Outside -Force | Out-Null
Set-Content -LiteralPath (Join-Path $tf080Outside '保留检查.txt') -Value '这份测试文件必须保留' -Encoding utf8
Write-Output "程序安装位置：$tf080Program"
Write-Output "数据 A：$tf080RootA"
Write-Output "数据 B：$tf080RootB"
Write-Output "独立测试配置：$env:LOCALAPPDATA"
}
```

**应该看到：** 输出四个测试路径，没有红色错误。记下这些路径。
“测试配置”保存程序上次打开哪个数据目录的记录；不会复制你的个人记录。
程序文件、数据 A、数据 B、根外备份是四个不同的目录。

后续安装器、程序和卸载器都从这个 PowerShell 窗口启动，才能使用同一份测试
配置。此轮不要通过桌面快捷方式或控制面板启动卸载器来做数据删除测试。
如果窗口关闭了，先告诉我，恢复测试环境后再继续，别直接重做第一段命令。

## 二、M01：安装到中文、带空格的目录，再取消首次启动

1. 在 PowerShell 运行：

   ```powershell
   & {
       if (-not $tf080Setup -or -not $tf080Program) { throw '请先完整运行本次准备命令。' }
       Write-Output "本次安装位置：$tf080Program"
       Start-Process -FilePath $tf080Setup -ArgumentList ('/DIR="' + $tf080Program + '"') -Wait
   }
   ```

2. 按安装向导前进。到安装目录页面时，应已经填好准备阶段输出的“程序安装位置”，
   也就是“程序 甲”的完整路径。核对它与 PowerShell 输出相同；若仍是旧测试地址，
   点击取消并反馈。不要选数据 A、数据 B 或测试父目录本身。目录页仍应允许修改位置。
3. 勾选创建桌面快捷方式，以便后面检查它的目标。安装前的汇总页面应显示你选的路径。
4. 完成安装。最后一页如果有 `Launch TrainingFeedback`（启动程序），取消勾选，
   再点击 `Finish`（完成）。
5. 回到 PowerShell，运行：

   ```powershell
   Test-Path -LiteralPath (Join-Path $tf080Program 'TrainingFeedback.exe')
   Test-Path -LiteralPath (Join-Path $tf080Program '.training-feedback-install.json')
   Start-Process -FilePath (Join-Path $tf080Program 'TrainingFeedback.exe') -Wait
   ```

6. 前两行应该各输出一个 `True`，表示程序和安装归属记录都存在。
   程序打开后，应出现“选择训练反馈数据目录”窗口。点击“取消”。
7. 程序关闭后，在 PowerShell 检查：

   ```powershell
   Test-Path -LiteralPath $tf080Pointer
   Test-Path -LiteralPath $tf080RootA
   ```

**通过要求：** 安装目录可修改，程序从“程序 甲”启动；取消首次选择后，最后两行
都输出 `False`，没有偷偷创建数据 A 或上次打开目录的记录。

**失败例子：** 没有目录页、仍装到其它位置、程序打不开、取消后已经创建数据。
反馈 M01 的结果；出现错误时附上完整提示。

## 三、M02：创建两份测试数据，检查保存、重启和切换

1. 运行上面的程序启动命令。
2. 选择“创建新的数据目录”。“父目录”填写测试父目录的完整路径；“新目录名称”
   填 `测试数据 A`。确认预览路径与准备阶段输出的数据 A 相同，再创建。
3. 打开左侧“动作库”。检查显示共 36 个动作；分别点击“臀桥”和“蚌式开合”的卡片。
   在详情上方的图片页签查看图片；本候选该页签的文字是“替换为本地示意图…”，
   选择上方页签即可，不点下方同名按钮。图片应正常显示，没有图片丢失提示。
   新目录不应有已经完成的训练或专家审核记录。
4. 打开“臀桥”详情，点击“编辑动作内容…”。找到“训练目的”文字框，在原文字末尾
   另起一行，加入 `【合成验收】仅在 A`，点击“保存”。不要改其它字段，也不要点击
   “记录外部审核…”。关闭编辑窗口后，确认“完整指导”中能看到刚加入的文字。
5. 关闭程序，再从同一个 PowerShell 启动。确认“设置”中的当前数据目录还是 A，
   刚保存的标记文字仍在。再关闭、重启一次，检查结果相同。
6. 打开“设置”→“切换到其他数据目录…”，选择创建新目录，父目录仍填测试父目录，
   新目录名称填 `测试数据 B`。确认当前目录变为 B。
7. 在 B 中打开“臀桥”，不应出现 `【合成验收】仅在 A`。按第 4 步的同样方法，
   在“训练目的”末尾加入 `【合成验收】仅在 B` 并保存。
8. 从“设置”切换回 A。这次选“打开已有数据目录”，选数据 A 的完整路径。
   A 应有 A 的标记，没有 B 的标记。再切到 B，确认结果相反，最后停在 B。

**通过要求：** 创建和两次重启正常，图片可见，草稿保存成功，A/B 的修改互不混入。
记录程序中的当前数据目录路径。没有做完的步骤记“未运行”，不要算作全部通过。

## 四、M03：重装和更换程序位置，检查数据不被改动

**开始前：** 当前数据目录是 B，程序已经关闭。不要关闭 PowerShell。

1. 复制运行下面这段只读检查命令。它记录 A、B 和上次打开目录记录的文件校验值，
   供重装后比较；不会修改这些文件。

   ```powershell
   function Get-Tf080TestFileState {
       foreach ($directory in @($tf080RootA, $tf080RootB)) {
           Get-ChildItem -LiteralPath $directory -Recurse -File | ForEach-Object {
               $_.FullName + '|' + (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
           }
       }
       if (Test-Path -LiteralPath $tf080Pointer) {
           $tf080Pointer + '|' + (Get-FileHash -LiteralPath $tf080Pointer -Algorithm SHA256).Hash
       }
   }
   $tf080BeforeReinstall = @(Get-Tf080TestFileState | Sort-Object)
   ```

2. 运行下面命令，在同一个“程序 甲”目录重装：

   ```powershell
   Start-Process -FilePath $tf080Setup -ArgumentList ('/DIR="' + $tf080Program + '"') -Wait
   ```
   完成页仍取消自动启动程序。
3. 程序还没有启动时，运行：

   ```powershell
   Compare-Object $tf080BeforeReinstall @(Get-Tf080TestFileState | Sort-Object)
   ```

   **应该没有任何输出。** 如果出现路径或校验值，说明有文件变化，记录下来。
4. 保持程序关闭，在原PowerShell运行下面的命令，明确指定新位置“程序 乙”：

   ```powershell
   Start-Process -FilePath $tf080Setup -ArgumentList ('/DIR="' + $tf080ProgramNext + '"') -Wait
   ```

   目录页应为 `E:\TrainingFeedback-080-PathFix\程序 乙`。出现更换位置提示时，
   确认显示的是从“程序 甲”到“程序 乙”，再继续。完成页取消勾选自动启动。
5. 再运行第 3 步的比较命令，仍应没有输出。然后运行：

   ```powershell
   Test-Path -LiteralPath (Join-Path $tf080Program 'TrainingFeedback.exe')
   Test-Path -LiteralPath (Join-Path $tf080ProgramNext 'TrainingFeedback.exe')
   ```

   应依次输出 `False`、`True`，表示旧位置的程序已移除、新位置存在程序。
   比较有输出或这两项不符合预期，就停止并反馈，不运行后续命令。
   全部符合后再运行下面一行，把后续启动路径更新为“程序 乙”：

   ```powershell
   $tf080Program = $tf080ProgramNext
   ```
6. 右键桌面快捷方式，打开“属性”，检查“目标”指向“程序 乙”的
   `TrainingFeedback.exe`，不能指向“程序 甲”。这一项只查看，不从快捷方式启动。
7. 从 PowerShell 启动新位置的程序，检查仍打开 B，A/B 的草稿标记仍各自保留，随后关闭。

**通过要求：** 两次重装后关闭状态的数据文件都没变化，换位置后只有新程序入口，
原测试数据仍能打开。任何安装错误、旧入口残留或数据变化都记为失败。

## 五、M04：取消卸载，以及默认保留数据卸载

1. 确认程序关闭，运行下面的命令。正常安装的卸载器名称应为 `unins000.exe`；
   如果这个文件不存在，先报告，不要自行猜其它程序文件。

   ```powershell
   Start-Process -FilePath (Join-Path $tf080Program 'unins000.exe') -Wait
   ```

2. 修复包的卸载窗口中，“同时永久删除上方数据目录内的全部数据（默认保留）”
   应默认**不勾选**。可删除时显示的数据路径应为 B；归属不符时应明确说明
   不能删除，并显示“仅卸载程序”。后者不能算作可删除场景通过。
3. 点击“取消”。程序文件和数据应仍在。再次启动程序，确认 B 的草稿标记
   还在，然后关闭程序。
4. 只有归属检查通过且删除选项可用时才做本步。再打开卸载器，勾选删除数据，
   点击“继续卸载…”。出现再次确认永久删除
   的窗口时，核对路径为测试数据 B，选择 `No`（否）。如果后面还有普通卸载确认，
   也选 `No`（否），保留程序。这一步不要选择任何确认删除或卸载的“是”。
   然后运行下面命令，三行都应为 `True`：

   ```powershell
   Test-Path -LiteralPath (Join-Path $tf080Program 'TrainingFeedback.exe')
   Test-Path -LiteralPath $tf080RootB
   Test-Path -LiteralPath $tf080Pointer
   ```

   再从原PowerShell启动程序，确认B标记保留，随后关闭。如果路径不符、
   没有再次确认就开始删除，或程序/数据消失，停止并反馈窗口提示与命令输出。
5. 第三次打开卸载器：保持删除数据选项**不勾选**，继续并确认卸载程序。
6. 卸载完成后运行：

   ```powershell
   Test-Path -LiteralPath (Join-Path $tf080Program 'TrainingFeedback.exe')
   Test-Path -LiteralPath $tf080RootB
   Test-Path -LiteralPath $tf080Pointer
   ```

   应依次输出 `False`、`True`、`True`：程序删掉了，B 和上次打开目录的记录保留。
7. 用同一个安装包重新安装到刚才的程序位置。安装后从 PowerShell 启动程序，确认
   可以重新打开 B、看到原标记，再关闭程序。

**通过要求：** 取消卸载、拒绝再次删除确认都不删数据；默认卸载只移除程序；
重装后原测试数据可以继续打开。反馈这三种操作各自的结果。

## 六、M05：明确选择删除，只删除当前测试数据 B

**这一步会删除 B 内的全部测试文件，以及上次打开目录的记录。**
数据 A 和“根外备份”必须保留。只对本清单刚创建的测试目录操作。

1. 先打开程序，在“设置”确认当前数据目录的完整路径确实是 B，再关闭程序。
2. 在文件资源管理器确认数据 A、数据 B 和“根外备份”中的 `保留检查.txt` 都存在。
3. 从同一个 PowerShell 启动卸载器。
4. 核对窗口显示的待删除路径：必须完整等于准备阶段的数据 B 路径。
   如果显示其它路径，点击取消，记录为失败，不继续删除。
5. 勾选删除数据，点击“继续卸载…”。在永久删除的再次确认窗口检查路径仍为 B，
   再选择 `Yes`（是）。如果还有普通卸载确认，确认继续。
6. 卸载完成后运行：

   ```powershell
   Test-Path -LiteralPath $tf080RootB
   Test-Path -LiteralPath $tf080Pointer
   Test-Path -LiteralPath $tf080RootA
   Get-Content -LiteralPath (Join-Path $tf080Outside '保留检查.txt')
   ```

**通过要求：** 前三行依次输出 `False`、`False`、`True`；最后一行仍显示
`这份测试文件必须保留`。表示 B 和上次打开目录的记录已删除，A 和根外文件没被删除。

**失败例子：** B 残留却显示删除完成、删掉 A 或根外文件、显示路径与实际删除路径不符。
有错误时保留剩余文件和错误信息，不自行删除恢复记录。

## 七、M06：程序正在使用数据时，不允许删除数据

完成 M05 后，需要重新安装程序才能做这一项。

1. 用同一个安装包安装到 `$tf080Program` 指定的位置，不自动启动。
2. 在 PowerShell 运行 `Start-Process -FilePath (Join-Path $tf080Program 'TrainingFeedback.exe')`，
   本次不加 `-Wait`，这样程序打开后还能继续在 PowerShell 输入命令。
   选择“打开已有数据目录”，打开保留下来的 A。
3. 保持程序窗口打开，回到 PowerShell，运行
   `Start-Process -FilePath (Join-Path $tf080Program 'unins000.exe') -Wait` 启动卸载器。
4. 删除数据选项应无法勾选，窗口应说明数据正在使用或不能安全删除。
5. 点击取消卸载，回到程序检查 A 的标记文字仍在，然后关闭程序。

**通过要求：** 使用中的数据不能删除，取消后程序和 A 仍可用。
如果能勾选删除、没有原因说明，或 A 被改动，记录为失败。

## 八、M07：特殊故障测试，暂不执行

这一项包括损坏或未来版本数据、目录连接、权限不足、删除中断和恢复重试。
目前尚未交付专门的测试材料及可安全重复的手动制造故障步骤，因此这项保留为
**未运行**，不要求你自行改数据库、设置连接或强行结束删除进程。

后续由我先准备隔离材料，再给出每个案例的具体操作、预期提示、应保留的文件
以及如何重试。没有完整步骤之前，不把代码测试结果当作这一项手动验收通过。

## 九、M08：训练和响应检查

可以先反馈前面已做完的项目。这部分需要另一份专用合成计划、较多历史记录和
备份文件；材料及完整录入步骤未提供的场景，继续记为**未运行**，不用自行编训练计划。

你已经完成安装、重启、切换目录、打开动作图片和保存草稿时，可以顺便记录：

1. 从点击启动到主窗口可以操作，是否明显等很久。
2. 切换 A/B、打开动作库和图片时，是否出现点击无反应的停顿；有没有等待提示。
3. 在动作库搜索框输入 `臀`，结果是否及时变化；保存草稿后是否及时反馈保存结果。
4. 发生明显停顿时，记录正在做哪一步、大约等了几秒；方便时提供屏幕录制。
   不要求你凭肉眼判断 0.2 秒，也不要求自行计算统计值。

正式响应验收仍需要每个关键操作 20 次原始计时，以及最长无反馈停顿的记录。
我会提供记录方法并计算“典型耗时”和“较慢情况耗时”；现在的主观观察只是问题线索，
不能单凭“感觉流畅”认定 0.2 秒停顿要求已经通过。
首次完整图片检查目前仍较慢，约 0.85 秒，要特别记录窗口是否有反馈、还能否操作。

## 十、按这个格式反馈

复制下面模板，把实际做过的项目填好。没做的写“未运行”，失败的写清是哪一步。

```text
测试日期：
Windows 测试账户：
程序安装路径：
测试数据 A 路径：
测试数据 B 路径：
独立测试配置路径：

M01：通过 / 失败 / 未运行
M02：通过 / 失败 / 未运行
M03：通过 / 失败 / 未运行
M04：通过 / 失败 / 未运行
M05：通过 / 失败 / 未运行
M06：通过 / 失败 / 未运行
M07：未运行（等待专门测试材料）
M08：未运行 / 已提供部分观察

出问题的项目和步骤：
本来应该看到什么：
实际看到什么：
错误提示原文或截图：
是否有残留文件、明显停顿：
```

“通过、失败、未运行”分别对应证据里的 `pass`、`fail`、`not run`。
实际操作结果只适用于本次安装包；不会自动认定正式发布、专家审核或个人使用准备完成。
