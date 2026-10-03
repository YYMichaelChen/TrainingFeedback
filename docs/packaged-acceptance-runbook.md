# Packaged Acceptance Runbook

当前长期个人使用阶段遵循
[产品规范第 9.1 节](development-plan.md#91-release-and-follow-up-boundaries)。
本手册不能因为制作安装包、更新版本、个人使用或收尾而增加测试：
自动验证仅针对具体启动失败风险，每次更新最多 3 项、通常 0～1 项；
无此风险为 0 项，人工测试默认 0 项。旧批量本机验收要求已取消。
安装包及后续更新默认通过本仓库 GitHub Releases 分发。上传 Release 不增加测试，
不自动声明正式兼容支持；说明中记录版本、SHA-256、签名状态和构建来源。

## 1. Build and identify a candidate

Only build when requested or included in the agreed deliverable. Follow the
[development workflow](development-workflow.md) for source identity and the
[test instructions](../tests/README.md) for the unchanged startup-only cap.

Use the pinned toolchain and PowerShell 7. The build command, when needed, is
`pwsh -File packaging/build.ps1 -Installer`, with `-ISCC` for a non-default
Inno Setup compiler. Preserve the generated payload, installer and adjacent
manifests; identify the source revision/snapshot and application/schema/catalog/
contract versions. A dirty source snapshot is an informal preview, not a claim
of complete installed acceptance. Review relevant startup packaging risks only.

Program files stay separate from data. Building does not authorize installation,
root migration, deletion or discovery of personal data. Any allowed code-level
root check uses isolated synthetic inputs and an isolated locator. Never use
personal roots for fault injection or synthetic training.

## 2. Local installed acceptance

### 当前最小观察

默认不交付手动验收清单。只有本次改动有具体启动失败风险、且代码检查无法确认时，
最多请用户在下一次正常使用时观察一次能否打开：

1. **准备：**说明本次程序版本／位置、具体启动风险和预期正常入口；不要求重装、
   卸载、重建或切换数据目录，不要求准备大批合成材料。
2. **操作：**用户按正常方式打开一次应用。代理不点击、按键或自动操作客户端。
3. **预期：**应用进入正常主窗口；尚未配置数据目录时能显示正常选择入口。
   启动报错退出、无法进入正常入口或启动一直无响应时，反馈原始现象。
4. **反馈：**一句“能打开”或具体错误／现象即可；需要定位时再补错误原文或截图。
   不要求录屏、帧率、耗时、重复次数、统计表、页面巡检或完整训练。

普通反馈无需填写候选 hash、路径清单或证据矩阵。代理在已有材料能确定的范围内
记录构建身份；身份未知时如实说明，不把反馈自动认证为所有版本通过。
代码检查不能代替实际界面观察；没有观察不写通过。政策已取消的检查不再待补，
不阻止开发交付。已知启动失败应修复。

### 手动验收清单写法

如果确有上述一次启动观察，说明必须用简单中文写清准备、具体操作、预期、
失败判断和反馈内容。不要只给编号或术语，不给用户自行准备故障材料的任务。
命令仅在必要时给出，必须可复制并说明需要改的路径。

通过、失败、未运行仍分别对应 pass、fail、not run；取消要求不等于通过。
更换候选不触发批量重测。原安装、卸载、训练、故障、性能等完整矩阵已退出
当前本机交付门槛；历史材料只供追溯，不是待办。

## 3. Formal public-support preparation — explicit declaration only

Uploading the identified personal-use installer to GitHub Releases is authorized
and does not invoke this section. The following scenarios are dormant reference
material for a future formal compatibility or wider public-support commitment,
not current work or personal-use prerequisites. Such a declaration must first
settle its scope and any change to verification policy with the user.

Do not start independent acceptance without that declaration. Apply the formal
compatibility boundary from the product release policy. The local gate must
first identify the exact candidate. When predecessor endpoints are in scope,
prepare isolated
synthetic roots from their **actual** programs and manifests named by the
current version index. Preserve unopened originals, closed transfer copies,
logical facts, original text/unknown fields,
resource hashes and database hashes. A tag rebuilt later is a different binary
identity. Include one expired root for unchanged refusal and a future-schema
root; arbitrary intermediate schemas are not upgrade promises.

Transfer only identified programs/installers/manifests, synthetic fixture copies,
baseline descriptions/hashes, operator instructions and evidence forms. Use an
independent Windows x64 VM or machine with an ordinary non-administrator account,
without Python, Conda, source checkout or access to the build environment. A new
account on the build machine is insufficient. Isolate its locator and close apps
before copying roots. Never test an old binary on the sole upgraded copy.

## 4. Independent public-support acceptance — explicit declaration only

Execute the following against the exact candidate with actual UI interaction.
Each row needs input baseline, operations, expected/observed result, logical and
resource comparison, evidence path/hash and a `pass`, `fail` or `not run` status.

| ID | Scenario and required result |
| --- | --- |
| PUB-01 | Install as an ordinary user; cancel, create a fresh Chinese/space root and try invalid/occupied paths. Built-ins load without old data; cancel leaves nothing partial. |
| PUB-02 | When required by the product compatibility boundary, install over each selected predecessor program and open copies of its root. Installer preserves data; supported startup upgrade preserves locator, text, unknowns and frozen facts without re-import. Otherwise record the row as not applicable with the governing policy state. |
| PUB-03 | Compare upgraded facts/resources, restart twice and restart Windows, then switch roots. No duplicate conversion, approval or assets; paused position and root isolation survive. |
| PUB-04 | Open interrupted supported roots; exercise access, space and backup failures, expired and future roots. Recovery is consistent; unsupported roots remain unchanged with actionable guidance. |
| PUB-05 | Exercise guidance/image eligibility through review, plan and start. Invalid/missing assets block new use; valid unreviewed assets invent no approval; originals remain. |
| PUB-06 | Browse families and edit/activate plans with groups, sides, repeated members and distinct units. Ordering and pinned prescriptions remain exact; invalid/stale input loses nothing. |
| PUB-07 | Record individual and round outcomes, partial work, retraction/cancel, pause/restart and abort/finish. Atomic actions preserve exact facts and agree with history/export. |
| PUB-08 | Exercise removal, restoration and publisher withdrawal. New use is blocked as declared; frozen work/history remain usable; restoration does not auto-enable. |
| PUB-09 | Export portable evidence/images and import the current contract. JSON/Markdown/hashes agree; originals remain; imports are drafts; unsupported formats fail clearly. |
| PUB-10 | Back up an active synthetic root, try bad destinations, reopen and resume with a newer catalog. Assets and facts survive; failures leave no misleading partial backup. |
| PUB-11 | Inspect settings/library/import, then upgrade, default uninstall and reinstall. Program operations leave locator/root intact and fresh roots use current built-ins. Exercise any candidate-specific deletion option only with an isolated synthetic root, including cancel and invalid-path refusal. |
| PUB-12 | Inspect real desktop scaling at 100%, 125% and 150% on 1366×768 and 1920×1080 where available. Long Chinese text and many actual-set rows keep core controls reachable. |

Record actual alternatives for unavailable display sizes; a required scenario
remains open until evidenced. The public Setup and EXE require valid trusted
Authenticode signatures; verify them and the intended distribution artifact.
Every required row must pass for the identified candidate
before public acceptance is claimed. Missing or deferred evidence remains `not
run`; local checks, expert content review, personal use and W4 cannot stand in
for independent technical acceptance.
