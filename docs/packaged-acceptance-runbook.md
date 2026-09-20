# Packaged Acceptance Runbook — 0.7.0

Updated: 2026-09-21. Status: local directory candidate exists; formal installer
and independent acceptance **not run**. Product scope and supported versions live
in [development-plan.md](development-plan.md), §§7–9, 12–13. The
[release review](release-readiness-0.7.0.md) records findings and execution order.
Historical procedures are in the [version history](history/README.md).

All changing/destructive checks use isolated synthetic roots. Development content
belongs in the built-in catalog; these fixtures do not establish personal facts.

## 1. Candidate And Installer Preparation — Build Machine

1. Close 070-R1/R2 and content prerequisites from the active plan. Record application,
   database schema, catalog and wire-contract versions separately. Capture the exact
   source commit/snapshot; dirty-source manifests require a matching source snapshot.
2. With the pinned toolchain, build the complete PyInstaller directory plus installer:

   ```powershell
   pwsh -File packaging/build.ps1 -Installer -ISCC 'C:\Users\41315\AppData\Local\Programs\Inno Setup 6\ISCC.exe'
   ```

   The inspected compiler exists; actual compilation is still required. Substitute
   the verified compiler path on another build machine. Output:
   `dist/TrainingFeedback/`, its adjacent manifest, and
   `dist/installer/TrainingFeedback-<version>-Setup.exe` plus installer manifest.
3. Verify all payload paths, counts, sizes and hashes, including unexpected files.
   Catalog verification must cover actual illustration bytes and readiness for every
   entry. A filename or prompt is not an asset. Include v2 contracts and sqlite3.dll.
4. Record build time, version, source revision/dirty flag, source snapshot identity,
   architecture, Python/PySide6/PyInstaller versions, installer/manifest/executable
   hashes and Authenticode status. Unsigned builds may support development testing;
   the existing broad-distribution signing requirement still applies.
5. Verify the installed executable and complete payload. Program replacement must
   not touch locator/root files; first application launch may perform the declared
   supported migration. Validate these as separate boundaries.

Directory-only builds are supporting checks, not installer/upgrade acceptance.
Archive a changed candidate separately and rerun affected checks; never relabel an
older candidate's evidence. Retain artifacts within the three-version window.

## 2. Isolated Input And Transfer Preparation

- Prepare a clean first-launch profile and new empty Chinese/space-containing root
  path; cancellation must create nothing. Keep program and data paths separate.
- The source fixture helper copies the frozen synthetic schema16 baseline:

  ```powershell
  pwsh -File packaging/prepare-acceptance-data.ps1 D:\TF-Preparation\functional
  ```

  Use a new/empty base. Its generated locator contains an absolute build-machine
  path; do not reuse it after transfer. The frozen source fixture is not evidence
  of actual old-binary use. 070-R1 must make its DB and byte hashes reproducible.
- Prepare actual **0.6.0/schema14** and **0.6.1/schema16** baselines with matching
  retained binaries. Open/close normally before capturing logical facts, original
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
| 1366×768 | 100% | not run | |
| 1366×768 | 125% | not run | |
| 1366×768 | 150% | not run | |
| 1920×1080 | 100% | not run | |
| 1920×1080 | 125% | not run | |
| 1920×1080 | 150% | not run | |

Check startup/errors/root selection, families, full guidance/image/review forms,
group/member editors, long Chinese content, removal impact, feedback/history and
many actual-set rows. Save/cancel and pause/abort/finish must stay reachable.
Record actual alternatives where a resolution is unavailable; required scaling
coverage remains open until evidenced. Execute invalid-input retention, cancelled
save/retraction, stale preview and explicit confirmation, not just visual inspection.

## 5. Current Candidate Acceptance

### 5.1 Preparation Status

The 0.7.0 directory candidate has 257 verified files, schema22 runtime, v2 contracts
and catalog070-baseline-1 (36 entries, zero illustrations). Its dirty source is based
on `072c931`. Local offscreen schema16 conversion/restart/first-launch checks passed
7/7; see `.tmp/070-h-package/verification.json` and `rehearsal-result.json`.
These checks are not repeated here as independent results. The
[delivery history](history/0.7.0/development.md) records completed A–G and local H.

Before formal execution: finish reproducible frozen inputs, three-version runtime
support, actual current content/images, release regression, installer and actual
retained-binary baselines. The Inno compiler is present; no 0.7.0 installer result
has yet been recorded. Refresh transfer inputs for the final candidate.

### 5.2 Independent Candidate Scenarios

| ID | Operation | Required result | Status |
| --- | --- | --- | --- |
| 070-01 | Install; cancel first launch; create Chinese/space root as ordinary user; try invalid/occupied paths. | Current built-in catalog works without old data/import or full seed copy; no program writes or partial roots; cancel creates nothing. | not run |
| 070-02 | Install over retained 0.6.1/schema16 and oldest retained 0.6.0/schema14; start with their selected roots. | Program replacement preserves data; launch separately snapshots/converts automatically, preserving locator/settings/facts with no re-import or compatibility selector. | not run |
| 070-03 | Compare converted facts; restart twice, restart Windows and switch roots. | Verbatim originals and unknowns preserved; no duplicate conversion/assets or repeated approval of unchanged eligible plans; isolation and paused position survive. | not run |
| 070-04 | Open interrupted roots; exercise disk/access/backup failures; try expired and future roots. | Recover a consistent supported root; actionable errors, retained recovery copy. Unsupported roots unchanged; expired development root explains reinstall plus explicit new directory. | not run |
| 070-05 | Exercise text/image gate through library/review/plan/start. | Missing/corrupt/escaping/mismatched images block use; unreviewed valid images invent no approval; original review survives invalidation. | not run |
| 070-06 | Browse families; edit/activate A→B groups, rounds/sides and repeated members. | Distinct identities/units, exact side/rest/transition order, immutable pins, stale/invalid input rejected without loss. | not run |
| 070-07 | Individual/round results; partial work, retraction/cancel, pause/restart, abort/finish. | Correct member/round/side position; atomic batches; no duplicate/defaulted facts; terminal guards and history/export agreement. | not run |
| 070-08 | Request/review/approve/reject/cancel/restore removal and publisher withdrawal. | Root-local decisions, no evidence/variant cascade loss, new use blocked, frozen unfinished/history usable; restoration not automatic enablement. | not run |
| 070-09 | Export portable evidence/images; import v2; try new v1 file. | JSON/Markdown/current schema and hashes agree; original file preserved; draft only; v1 clearly rejected with current-format guidance. | not run |
| 070-10 | Online backup with paused work/reviews/retractions; try bad destinations; reopen with newer catalog and resume/re-export. | Complete custom/review/snapshot assets survive; source isolated, errors leave no misleading partial backup; old installed catalog unnecessary. | not run |
| 070-11 | Inspect settings/library/import; upgrade/uninstall/reinstall program. | No old-settings/export-all/bundled-acceptance controls; locator/root untouched by installer/uninstaller; new root reads latest built-ins. | not run |
| 070-12 | Execute real-desktop scaling/small-window/long-content matrix. | Readable family/group/image/removal/training states; fixed save/cancel/session controls accessible. | not run |

### 5.3 Exit

Every required row needs candidate-specific passing evidence. A missing-image
supported plan remains viewable with exact remediation; frozen paused sessions
remain usable. No supported-upgrade pass may rely on resetting a root. Deliberate
new-root handling is the declared behavior only for expired development versions.

Recovery snapshots must not recursively include backups or masquerade as complete
ordinary roots. Unsupported future roots stay untouched. The old binary must
reject an upgraded schema, not corrupt it; there is no in-app downgrade mode.

Keep independent technical acceptance, real content review and user-authorized
personal/W4 evidence distinct. Apply the three-version retention inventory after
evidence dependencies are accounted for; do not reset active test-budget ledgers.
