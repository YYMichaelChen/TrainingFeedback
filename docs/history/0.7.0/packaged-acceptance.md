# Packaged Acceptance Runbook — 0.7.0 (historical)

Updated: 2026-09-24. Status: current-source local installer/checks **passed**;
public independent acceptance **deferred / not run**. Product scope and supported versions live
in [development-plan.md](../../development-plan.md), §§7–9, 12–13. The
[release review](release-readiness.md) records findings and execution order.
Historical procedures are in the [version history](../README.md).

Per the user's 2026-09-23 decision, Section 1 is the current local-release procedure.
Sections 2–5 retain public-release preparation and independent acceptance, enabled
only by an explicit public-release request. They do not block local release.
External content review and W4 remain separate unfinished follow-ups.

All changing/destructive checks use isolated synthetic roots. Development content
belongs in the built-in catalog; these fixtures do not establish personal facts.

## 1. Candidate And Installer Preparation — Build Machine

### 1.1 Build And Payload Verification

1. R1/R2, 070-H1-CONTENT, 070-H2-TESTS and 070-H2-SOURCE are complete prerequisites.
   The previous directory candidate and its evidence are preserved before replacing
   `dist/`. Build from the exact complete source revision recorded by H2-SOURCE and
   require the payload manifest to report that revision with `source_dirty=false`.
   Record application, schema, catalog and wire-contract identities separately.
2. With the pinned toolchain, build the complete PyInstaller directory plus installer:

   ```powershell
   pwsh -File packaging/build.ps1 -Installer -ISCC 'C:\Users\41315\AppData\Local\Programs\Inno Setup 6\ISCC.exe'
   ```

   The completed local candidate used this compiler and the pinned toolchain.
   Substitute the verified compiler path on another build machine. Output:
   `dist/TrainingFeedback/`, its adjacent manifest, and
   `dist/installer/TrainingFeedback-<version>-Setup.exe` plus installer manifest.
3. Verify all payload paths, counts, sizes and hashes, including unexpected files.
   Catalog verification must cover actual illustration bytes and readiness for every
   entry. A filename or prompt is not an asset. Include v2 contracts and sqlite3.dll.
4. Record build time, version, source revision/dirty flag, source snapshot identity,
   architecture, Python/PySide6/PyInstaller versions, installer/manifest/executable
   hashes and Authenticode status. Unsigned local builds disclose that status;
   signing remains a public-distribution requirement after the explicit public trigger.
5. Verify the installed executable and complete payload. Program replacement must
   not touch locator/root files; first application launch may perform the declared
   supported migration. Validate these as separate boundaries.

Directory-only builds are supporting checks, not installer/upgrade acceptance.
Archive a changed candidate separately and rerun affected checks; never relabel an
older candidate's evidence. Retain artifacts within the three-version window.

### 1.2 Local Installed Checks

**Status: full LOCAL-01—06 pass for candidate `20260924-010017-736223e`;
image-only rebuild `20260924-142756-b88feba` passed affected LOCAL-01, 02, 03 and
05.** Use this machine and
isolated synthetic roots/locator. A separate machine or full resolution/scaling
matrix is not required for local release. Do not use a real root for failure or
synthetic training checks. Record the actual ordinary-user/account context.

Install the newly identified Setup, then resolve the installed executable before
isolating LOCALAPPDATA. Disable the installer's automatic post-install launch so
the first checked launch cannot read the ordinary locator. The installer owns the
program directory only; capture program and closed test-root/locator baselines
before replacing a program. Compare data bytes before launching the new application,
since an application launch can perform its declared supported conversion.

Example isolated launch after installation; choose the actual evidence base and
resolve a custom installed path when applicable:

```powershell
$localAcceptanceBase = Join-Path (Get-Location) '.tmp/local-package-070'
$installedProgram = Join-Path $env:LOCALAPPDATA 'Programs/TrainingFeedback/TrainingFeedback.exe'
$previousLocalAppData = $env:LOCALAPPDATA
try {
    $env:LOCALAPPDATA = Join-Path $localAcceptanceBase 'operator-localappdata'
    & $installedProgram
} finally {
    $env:LOCALAPPDATA = $previousLocalAppData
}
```

Keep the same isolated profile for restart checks and fresh named profiles for
independent inputs. Close the app before copying roots. Record evidence under the
candidate-specific release directory and include the actual scratch paths used.

| ID | Operation and expected result | Status |
| --- | --- | --- |
| LOCAL-01 | Install the candidate; compare installed files to the complete payload manifest, including unexpected files. Program replacement leaves the closed isolated locator/root bytes unchanged before application launch. | pass — `local-01-install-verification.json` |
| LOCAL-02 | Launch with a fresh isolated profile and cancel root selection. No data root or locator is created, and program files remain unchanged. | pass — `local-02-cancel-verification.json` |
| LOCAL-03 | Create an empty Chinese/space-containing root. All 36 current catalog entries/images are available without old roots or imports; no review, activation or training facts are invented. | pass — `local-03-catalog-verification.json` |
| LOCAL-04 | Browse the two revised bridge entries. 基础臀桥 and 蛙式臀桥 find the existing identities; guidance shows the three-second bridge hold. Catalog/content versions and images match the candidate manifest. | pass — `local-04-bridge-verification.json` |
| LOCAL-05 | Close/restart normally with the same isolated profile. The selected test root and saved state reopen without duplicate conversion or stray program-directory data. | pass — `local-05-restart-verification.json` |
| LOCAL-06 | In a clearly synthetic root, explicitly enable required valid content, save/activate a representative action-group plan, enter a result, pause, restart and resume. Exact position, saved result and frozen content survive; blank actuals are not defaults. | pass — `local-06-session-resume-verification.json` |

Each row records candidate/installer identity, Windows/account context, program and
data paths, input baseline, operations, expected/actual result, evidence path/hash
and pass/fail/pending. Retain failures before repair. Use actual UI interaction;
offscreen survival alone does not establish interactive behavior.

Local exit is satisfied: the four active tasks are closed and LOCAL-01–06 pass for the exact
candidate, with manifests and disclosed evidence limits. Public H3, actual old-binary
upgrade baselines, external review and W4 remain outside this exit. Changed binaries
get separate identities and rerun affected package checks.

The passing candidate is built from clean source revision `736223e8b5258a914b106f04da90efd98ab215f7`.
Its 293-file payload manifest SHA-256 is `e72dfdb787c08fc39c11a21bba873a819c7024cc561e9f8bd69e9283e8a89aa9`;
the installed executable and Setup SHA-256 values are `dc7f24dde919fd6ac485764928a180f14b8657339e12c44e7746aadb3c7ece7e`
and `4fdf7f835d8fe1a63b180db72282bd6f3ff0bbb6595f9b27830c96f7c34de889`.
Both are unsigned. Candidate-specific evidence is under
`.tmp/releases/0.7.0/20260924-010017-736223e/`; `LOCAL-ACCEPTANCE.md` is the index.

The `070-illustrated-3` caption rebuild from clean `b88feba` is now installed.
Its payload manifest, EXE and Setup SHA-256 values are respectively
`cedabf4c787d9c79edae51ac0c456e7a8eca2bb8f3fa5c9f29964647c73991cf`,
`d203a9dea1bdb6bf5409f2c9fa4a69bb2b23860c6c5f45dc840b00cab0b9391f`
and `d19eddceccb1bf8bdd3bf1d21466c3eb792477c508f6220ce1ea68452178279d`.
Affected checks LOCAL-01/02/03/05 passed in an isolated synthetic environment;
LOCAL-04/06 were not repeated for this image-only change. Evidence is under
`.tmp/releases/0.7.0/20260924-142756-b88feba/`; `LOCAL-ACCEPTANCE.md` is the index.

## 2. Isolated Input And Transfer Preparation

**Public release only; deferred until the user's explicit request.**

- Prepare a clean first-launch profile and new empty Chinese/space-containing root
  path; cancellation must create nothing. Keep program and data paths separate.
- Prepare isolated synthetic schema22 roots for the current 0.7.2 window. The
  retired schema16 preparation helper is retained only in Git history. Do not
  reuse locators across machines or use personal roots for fault injection.
- For a later public release, identify actual **0.7.0/schema22** and
  **0.7.1/schema22** binaries when available. Open/close normally before capturing logical facts, original
  text, unknown fields, resource hashes and original database hash. Preserve closed
  originals; create unopened transfer copies and separate local-rehearsal copies.
- Cover renamed/missing bundled keys, overrides/custom actions, complete/missing/
  corrupt images, review originals, selected/disabled content, draft/active plans,
  paused/terminal sessions, feedback, retractions and original imports/exports.
  Mark synthetic reviews and training explicitly. No real roots for fault injection.
- Prepare current-model groups with repeated actions, distinct units, side orders,
  partial/batch outcomes and removal references, plus a later catalog withdrawal.
- Supply interrupted-root fixtures for recovery/publication failures and an
  out-of-window root for unchanged rejection. Arbitrary earlier schemas are not
  upgrade promises; the accepted version/schema map is the authority. Future-schema
  rejection and free-space/access failures also require coverage.
- Expected conversion differences identify new structures/provenance/eligibility,
  not blanket permission to rewrite original facts. Compare before later training,
  exports or approvals intentionally add rows.

Transfer only versioned programs/installers/manifests, isolated fixture copies,
baseline descriptions/hashes, operator instructions and empty evidence forms.
Keep source archives, Python helpers and build environments on the build machine.
Record returned closed-copy comparisons there without changing the independent
machine's runtime environment. Original baselines must remain byte-identical.

## 3. Independent Environment And Launch

**Public release only; deferred / not run.** The clean-machine requirements in
this section do not apply to Section 1.2's local checks.

Use Windows x64 on a clean VM or separate machine, ordinary non-administrator
account, with no Python, Conda, source checkout or access to the build environment.
A new account on the build machine does not prove independence.

Install under the normal per-user location, or record the actual chosen path.
Use an isolated locator, including for first launch:

```powershell
$acceptanceBase = 'D:\TF 验收'
$program = 'C:\Users\Tester\AppData\Local\Programs\TrainingFeedback\TrainingFeedback.exe'
$previousLocalAppData = $env:LOCALAPPDATA
try {
    $env:LOCALAPPDATA = Join-Path $acceptanceBase 'operator-localappdata'
    & $program
} finally {
    $env:LOCALAPPDATA = $previousLocalAppData
}
```

Resolve the installed executable path before changing LOCALAPPDATA. Use the same
isolated profile for restart checks, fresh named profiles for independent fixtures,
and close applications before copying roots. Pause open sessions before normal
root switching; resumed work belongs to the selected root. Do not launch an old
program on the sole upgraded copy; rollback checks use preserved old roots.

## 4. Evidence Form And Display Matrix

**Public release matrix; deferred / not run.** Local evidence uses Section 1.2.

Record date/operator, Windows edition/build/x64, VM/machine identity, absence of
development dependencies, ordinary-user status, program/data paths, exact candidate
and catalog/schema identities, source provenance, installer/executable/manifest
SHA-256 and signature status, plus previous binary identities.

Each scenario needs input baseline, exact operations, expected/observed result,
logical/resource comparison, evidence path/hash and pass/fail/not run. Retain the
first failure reproduction before repair. Offscreen survival or an isolated image
of a window does not prove interactive behavior.

| Resolution | Scaling | Result | Checked windows / reachable controls / evidence |
| --- | --- | --- | --- |
| 1366×768 | 100% | deferred / not run | |
| 1366×768 | 125% | deferred / not run | |
| 1366×768 | 150% | deferred / not run | |
| 1920×1080 | 100% | deferred / not run | |
| 1920×1080 | 125% | deferred / not run | |
| 1920×1080 | 150% | deferred / not run | |

Check startup/errors/root selection, families, full guidance/image/review forms,
group/member editors, long Chinese content, removal impact, feedback/history and
many actual-set rows. Save/cancel and pause/abort/finish must stay reachable.
Record actual alternatives where a resolution is unavailable; required scaling
coverage remains open until evidenced. Execute invalid-input retention, cancelled
save/retraction, stale preview and explicit confirmation, not just visual inspection.

## 5. Public Release Acceptance — Deferred

### 5.1 Preparation Status

Public acceptance is deferred until an explicit public-release request. All rows
below remain not run; completion of local checks does not change their status.

The latest local candidate is `20260924-142756-b88feba`, with catalog
`070-illustrated-3`, 36 images and a 0.7.0 Setup. The previous fully exercised
candidate `20260924-010017-736223e` and the older 2026-09-20 candidate
remains dated history; see
[delivery history](development.md#070-h--completed-local-preparation-only-2026-09-20).

When H3 is enabled, choose the exact completed candidate, refresh manifests and
transfer inputs, and prepare actual retained-binary schema14/schema16 baselines.
Locate the matching old binary/manifest before using or deleting its evidence.
Document any missing original; a new tag rebuild has a different identity.
R1/R2 and the 36-image delivery are completed work, not open implementation tasks.

### 5.2 Independent Candidate Scenarios

| ID | Operation | Required result | Status |
| --- | --- | --- | --- |
| 070-01 | Install; cancel first launch; create Chinese/space root as ordinary user; try invalid/occupied paths. | Current built-in catalog works without old data/import or full seed copy; no program writes or partial roots; cancel creates nothing. | deferred / not run |
| 070-02 | Install over retained 0.6.1/schema16 and oldest retained 0.6.0/schema14; start with their selected roots. | Program replacement preserves data; launch separately snapshots/converts automatically, preserving locator/settings/facts with no re-import or compatibility selector. | deferred / not run |
| 070-03 | Compare converted facts; restart twice, restart Windows and switch roots. | Verbatim originals and unknowns preserved; no duplicate conversion/assets or repeated approval of unchanged eligible plans; isolation and paused position survive. | deferred / not run |
| 070-04 | Open interrupted roots; exercise disk/access/backup failures; try expired and future roots. | Recover a consistent supported root; actionable errors, retained recovery copy. Unsupported roots unchanged; expired development root explains reinstall plus explicit new directory. | deferred / not run |
| 070-05 | Exercise text/image gate through library/review/plan/start. | Missing/corrupt/escaping/mismatched images block use; unreviewed valid images invent no approval; original review survives invalidation. | deferred / not run |
| 070-06 | Browse families; edit/activate A→B groups, rounds/sides and repeated members. | Distinct identities/units, exact side/rest/transition order, immutable pins, stale/invalid input rejected without loss. | deferred / not run |
| 070-07 | Individual/round results; partial work, retraction/cancel, pause/restart, abort/finish. | Correct member/round/side position; atomic batches; no duplicate/defaulted facts; terminal guards and history/export agreement. | deferred / not run |
| 070-08 | Request/review/approve/reject/cancel/restore removal and publisher withdrawal. | Root-local decisions, no evidence/variant cascade loss, new use blocked, frozen unfinished/history usable; restoration not automatic enablement. | deferred / not run |
| 070-09 | Export portable evidence/images; import v2; try new v1 file. | JSON/Markdown/current schema and hashes agree; original file preserved; draft only; v1 clearly rejected with current-format guidance. | deferred / not run |
| 070-10 | Online backup with paused work/reviews/retractions; try bad destinations; reopen with newer catalog and resume/re-export. | Complete custom/review/snapshot assets survive; source isolated, errors leave no misleading partial backup; old installed catalog unnecessary. | deferred / not run |
| 070-11 | Inspect settings/library/import; upgrade/uninstall/reinstall program. | No old-settings/export-all/bundled-acceptance controls; locator/root untouched by installer/uninstaller; new root reads latest built-ins. | deferred / not run |
| 070-12 | Execute real-desktop scaling/small-window/long-content matrix. | Readable family/group/image/removal/training states; fixed save/cancel/session controls accessible. | deferred / not run |

### 5.3 Public Exit

This exit applies only after the explicit public-release trigger. Every required
public row needs candidate-specific passing evidence. A missing-image
supported plan remains viewable with exact remediation; frozen paused sessions
remain usable. No supported-upgrade pass may rely on resetting a root. Deliberate
new-root handling is the declared behavior only for expired development versions.

Recovery snapshots must not recursively include backups or masquerade as complete
ordinary roots. Unsupported future roots stay untouched. The old binary must
reject an upgraded schema, not corrupt it; there is no in-app downgrade mode.

Keep independent technical acceptance, real content review and user-authorized
personal/W4 evidence distinct. Apply the three-version retention inventory after
evidence dependencies are accounted for; do not reset active test-budget ledgers.
