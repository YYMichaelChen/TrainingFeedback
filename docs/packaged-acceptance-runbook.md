# Packaged Acceptance Runbook

This runbook applies to every application version. The
[development workflow](development-workflow.md) decides when a candidate is
needed and which verification tier applies. The [product release policy](development-plan.md#13-version-retention-and-development-data-policy)
owns compatibility and retention boundaries; current implementation identities
are in the [version history index](history/README.md). Put dated results,
hashes and candidate status in candidate-specific evidence; this file is a
procedure, not a certificate for any build.

## 1. Build and identify a candidate

1. Finish the intended source and built-in catalog content. Record application,
   database schema, catalog and external wire-contract identities separately.
   Use a clean, complete source revision for a local-release or completed
   installed-acceptance claim. A dirty build is an informal preview with a
   complete source snapshot and no acceptance claim.
2. Use the pinned toolchain and PowerShell 7. Build the directory payload and
   installer with `pwsh -File packaging/build.ps1 -Installer`, supplying `-ISCC`
   when the Inno Setup compiler is not found automatically.
3. Preserve the directory payload, adjacent build manifest, Setup executable and
   installer manifest together. Compare every payload path, size and hash to the
   manifest, including unexpected files. Verify the bundled catalog and actual
   illustration bytes, required contracts/runtime files and absence of locator,
   personal roots or other user data in the program payload.
4. Record source revision/snapshot, source dirty flag, build time, toolchain and
   Windows architecture, manifest/EXE/Setup hashes and Authenticode status.
   Candidate identity changes when source or payload bytes change. Preserve prior
   candidate evidence under its own identity.

Installation and upgrade replace program files only. Compare closed isolated
locator/root bytes before launching a replacement program; application startup
may then apply only a migration allowed by the product release policy. Ordinary
uninstall retains the root unless the candidate implements a separately adopted,
explicitly confirmed and path-verified exception. Never use a real personal root for fault
injection or synthetic training.

## 2. Local installed acceptance

### 手动验收清单写法

交给开发者实际操作的手动验收清单必须使用简单易懂的中文，按执行顺序编号。
每一项都要写清：开始前需要什么、操作哪个程序或测试目录、具体怎么做、应该
看到什么、什么情况算失败，以及做完后要反馈什么。不要只写“验收切根”“确认
receipt”“检查回滚”等概括或术语，让开发者自行猜测步骤。

首次出现的技术词先用中文解释；界面只有英文按钮时，同时给出按钮原文和中文
含义。命令必须可以直接复制，注明需要改的路径、运行位置和预期输出。涉及
删除时，必须先指出具体测试目录、哪些文件会被删除、哪些应保留。
复杂故障案例应先提供隔离的合成测试材料和操作步骤；尚未准备好的案例明确写
“暂不执行／未运行”，不得让开发者自行修改真实数据库或猜测如何制造故障。

结果用“通过、失败、未运行”表示，并对应证据中的 `pass`、`fail`、`not run`。
未运行的项目不得打勾为通过。给出简短的中文反馈模板；技术统计由代理根据
原始记录计算，不能要求开发者自行理解或计算 p50/p95。

Use the newly built Setup on the build machine with an ordinary-user context,
isolated `%LOCALAPPDATA%` locator and synthetic roots. Resolve the installed EXE
before changing `%LOCALAPPDATA%`; suppress automatic post-install launch until
the isolated profile is active. Keep one profile for restart checks and fresh
named profiles for independent inputs. Close the app before copying a root.

普通权限要求同时适用于安装程序和创建测试数据。不要仅用新PowerShell的False
结果认证借用的旧程序安装：Inno即使设置`PrivilegesRequired=lowest`，安装时
已有管理员权限也会留下需要管理员权限卸载的记录，同目录覆盖安装可能沿用
该记录。遇到此情况先用`/KEEPDATA`仅卸载程序、记录测试数据未变，再在普通权限
窗口重新安装并检查新记录；不要靠修改数据所有权或读取真实默认配置解决。
详见 [Inno安装权限说明](https://jrsoftware.org/ishelp/topic_admininstallmode.htm)。

| Check | Required observation |
| --- | --- |
| Installed payload | Setup succeeds; installed files equal the complete payload manifest; program replacement leaves the closed isolated locator/root unchanged. |
| Fresh launch | Cancelling root choice creates no locator/root; invalid and occupied destinations fail cleanly. |
| New root | A Chinese or space-containing empty root receives the complete current built-in catalog and valid assets without an old root, manual import or invented review/plan/training facts. |
| Restart | The same isolated root reopens with its selected state and frozen facts; no duplicate migration or stray data in program files. |
| Affected workflow | Exercise the actual UI path changed by this candidate. For a release with no narrower workflow, use a representative plan, result, pause, restart and resume path with blank actuals preserved. |
| Current-root safety | Check current-root restart/reinstall and affected malformed/future-root refusal unchanged before writes. This remains required when the candidate affects root safety. |
| Compatibility boundary | Apply the product release policy. Where predecessor endpoints are in scope, open copies and verify declared preservation; reject unsupported roots unchanged. Preserve untouched originals. |
| Affected installer/uninstaller behavior | Exercise every installer or uninstaller option changed by the candidate, including defaults, cancellation, invalid paths, program identity and the exact synthetic-data boundary. |

For each applicable check, record candidate and installed identities, account,
paths, synthetic input baseline, operations, expected/observed result, evidence
path/hash and `pass`, `fail` or `not run`. Inspect interactive UI where the claim
depends on visible behavior; offscreen process survival alone is not that evidence.
These client checks are recorded separately and do not count toward the
version-update pytest case limit in [test instructions](../tests/README.md).
If a candidate changes, rerun affected checks and explicitly cite earlier
unchanged checks that were not repeated. Do not relabel prior results as new
candidate passes. Unsigned local builds disclose their status; signing is a
public-distribution requirement.

## 3. Public release preparation — explicit request only

Do not start independent acceptance or public distribution without the user's
explicit public-release request. Apply the formal-release and compatibility
boundary from the product release policy. The local gate must first identify
the exact candidate. When predecessor endpoints are in scope, prepare isolated
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

## 4. Independent public acceptance — explicit request only

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
