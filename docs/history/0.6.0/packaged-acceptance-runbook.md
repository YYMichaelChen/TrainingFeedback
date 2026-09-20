# 0.6.0 Packaged Acceptance Procedure — Historical

Archived 2026-09-21. This preserves the earlier 0.6.0 procedure and its staged
0.7.0 planning addendum, including unexecuted rows and subsequently corrected
observations. It is not the current workflow, compatibility window or candidate
status. Use the [current runbook](../../packaged-acceptance-runbook.md) and
[version policy](../../development-plan.md#13-version-retention-and-development-data-policy).
The old missing-Inno claim in the addendum was disproved by direct file inspection;
see the [0.7.0 delivery record](../0.7.0/development.md). References to programs
before 0.6.0 describe historical proposals, not retained support obligations.

Requirements live in [development-plan.md](../../development-plan.md), Sections 7–9.
This runbook targets 0.6.0: test v0.2.2 → 0.6.0 (schema 12 → 14) and
v0.5.1 → 0.6.0 (schema 13 → 14). Earlier 0.3.0/0.3.1/0.4.0 candidates and their
results remain historical; never relabel their evidence as a 0.6.0 result.
Use only isolated synthetic roots belonging to this application.

Status (2026-09-14): the instructions are updated; the 0.6.0 transfer package
has not been assembled. All independent scenarios remain `not run` (未执行).
Personal W4 may proceed after local Phase C and required guidance/plan
confirmation. Refresh transfer inputs when 8-B2 starts, and complete this gate
before broader distribution, adding users, or formal release acceptance.

**0.7.0 planning addendum (2026-09-17):** Section 5 defines the future
candidate's seamless-upgrade and new-model acceptance. Sections 1–4 retain
their named 0.6.x baseline; they are not an optional old-settings workflow in
0.7.0. No 0.7.0 build, migration or acceptance run is created by this document
update. The preserved candidate remains 0.6.1 / 16; development schemas 17–22 with
the new-model desktop cutover (070-G3) are complete in source, pending the real
0.7.0 build and independent acceptance.

Preparation and build-machine startup checks are supporting evidence. Execute
8-B2 in an independent Windows x64 environment with no Python, Conda,
application source checkout, or access to the build environment. Use a clean VM
or separate machine and an ordinary non-administrator account. A new account
on the build machine does not establish runtime independence.

## 1. Candidate And Transfer Preparation — Build Machine

### Formal Windows installer

The supported user-facing distribution is the Inno Setup package produced by:

```powershell
pwsh -File packaging/build.ps1 -Installer
```

This requires Inno Setup 6 (`ISCC.exe`) on the build machine; use
`-ISCC <path>` when it is not on PATH or in a standard installation directory.
The output is `dist/installer/TrainingFeedback-<version>-Setup.exe`. The
installer has a stable application identity and uses the per-user default
directory `%LocalAppData%\Programs\TrainingFeedback`, so running a newer setup
file over an existing installation is an in-place application upgrade rather
than a source checkout replacement.

For every release candidate, verify that the installer contains the complete
PyInstaller onedir payload (`TrainingFeedback.exe` and `_internal/`), that the
installed executable starts, and that the old selected data root and its
database/resources are unchanged after an upgrade. Uninstall the program as a
separate check and confirm that the locator and data root remain. The setup
package owns only the program directory and shortcuts; it must never be used to
delete or move user data.

If Inno Setup is unavailable on the build machine, the directory build and its
manifest can still be verified, but that does not count as formal installer or
upgrade acceptance.

Record the Setup.exe Authenticode status as part of candidate identity. Local
unsigned builds can support personal installation testing, but broad public
distribution remains blocked until the release is signed with a trusted code-
signing certificate and the signature is verified after transfer.

Use the identified candidate directory and its original manifest. The existing
0.6.0 program is a precommit build: its manifest records `source_dirty=true`
and base commit `fb593ef`, whereas source tag `v0.6.0` points to `072c931`.
Keep the manifest, executable hash, complete file hashes and actual source facts;
do not substitute the tag for the recorded build identity. Exact candidate hashes
and local checks belong in local task artifacts, not this reusable runbook.

No rebuild is required for the current documentation/W4 preparation task.
Before independent acceptance, retain an exact source snapshot and its hash for
any dirty candidate. If that snapshot cannot be established, build a separately
identified candidate from a known clean source state with `packaging/build.ps1`
and the pinned toolchain, then rerun affected local checks before transfer.
Do not recreate a missing precommit snapshot from the tag and claim equivalence.
A rebuild receives its own identity; keep the earlier program and results.

When 8-B2 starts, assemble these transfer inputs in a new directory; this table
is a preparation checklist, not a claim that the current package exists:

| Input | Purpose |
| --- | --- |
| `programs/0.6.0/TrainingFeedback/` and adjacent build manifest | Complete candidate directory; copy the executable and `_internal` together. |
| `programs/0.5.1/TrainingFeedback/`, manifest, and source-provenance record | Previous build for the schema-13 adjacent upgrade. |
| `programs/0.2.2/TrainingFeedback/`, manifest, and source-provenance record | Previous-version build recreated from this repository's tag. |
| `inputs/functional/data-root/` | Current synthetic training, feedback, imported draft, and recovery fixture. |
| `inputs/workflow/data-root/` and synthetic answer file | Supplemental synthetic review/catalog fixture described below; use copies for destructive or state-changing checks. |
| `inputs/upgrade-original/data-root/` | Closed schema-12 baseline; never open with the new application. |
| `inputs/upgrade-copy/data-root/` | Unmodified copy for the independent upgrade scenario. |
| `inputs/adjacent-original/data-root/` and `inputs/adjacent-copy/data-root/` | 0.5.1-generated, normally opened/closed schema-13 baseline and unopened copy. |
| `baselines/upgrade-original.json` and `baselines/adjacent-original.json` | Logical records, schema version, resource hashes, and original database hash for both upgrade paths. |
| `candidate-verification.json`, `START-HERE.md`, `acceptance-evidence.md` | Local preparation evidence, operator instructions, and unfilled independent acceptance results. |

Keep source archives, Python helpers, build logs, and development environments
on the build machine. Transfer only the package above to the independent
environment. Keep program and data directories separate after unpacking.

Record build time, app version, source revision, source-dirty flag, architecture,
Python/PySide6/PyInstaller versions, and file count. Verify every file, including
unexpected extra files, on the build machine and after transfer. With PowerShell 7,
set the path to the version directory and run:

```powershell
$candidateDir = 'D:\TF 验收\programs\0.6.0'
$programDir = Join-Path $candidateDir 'TrainingFeedback'
$manifest = Get-Content -LiteralPath (Join-Path $candidateDir 'TrainingFeedback.build-manifest.json') -Raw | ConvertFrom-Json
$files = @(Get-ChildItem -LiteralPath $programDir -Recurse -File)
if ($files.Count -ne $manifest.file_count -or $manifest.artifact_hashes.Count -ne $manifest.file_count) {
    throw 'Candidate file count mismatch'
}
foreach ($entry in $manifest.artifact_hashes) {
    $file = Get-Item -LiteralPath (Join-Path $programDir $entry.path) -ErrorAction Stop
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    if ($file.Length -ne $entry.bytes -or $hash -ne $entry.sha256) {
        throw "Candidate mismatch: $($entry.path)"
    }
}
```

Expect the selected version (`0.6.0` for this runbook) and use its actual source identity,
dirty flag and manifest file count. Record the manifest hash and entry executable
hash in the environment record; never substitute the previous candidate's values.

## 2. Prepare Isolated Inputs — Build Machine

### First launch

Use an absent/empty locator directory and an empty data destination. Never
reuse a developer's default locator. The operator launch procedure below sets
an explicit isolated `LOCALAPPDATA` even for first launch.

### Functional and recovery fixture

Run from the current repository using PowerShell 7:

```powershell
pwsh -File packaging/prepare-acceptance-data.ps1 D:\TF-Preparation\functional
```

The base directory must be empty or absent. The result contains synthetic
completed, partial, and paused sessions, revisions, original notes, next-day
feedback, PNG images, exports, and an imported draft. The content and approval
metadata are explicitly synthetic. Copy only `data-root/` into the transfer
package; after moving it, select it through the normal UI. Its original locator
contains an absolute build-machine path and must not be reused after transfer.

This fixture must never be used for actual exercise-content review. Follow the
[guidance review runbook](../0.6.1/guidance-review-runbook.md) for the historical seed procedure.

Before transfer, prepare a separate supplemental synthetic workflow root with
two reviewable guidance drafts, one missing and unreferenced bundled exercise,
and a synthetic external-answer file. The standard fixture command does not
prepare these extra conditions. Record the prepared IDs/names and baseline in
START-HERE so the independent operator can use only the packaged UI; never
delete real user content to create a missing-catalog case. Label all test review
facts and attachments synthetic. Keep fresh copies for repeatable checks.

### Cross-version upgrade fixture

1. Export **this repository's** `v0.2.2` source to a new staging directory.
   Record the peeled commit and SHA-256 of the archive. Do not change the main
   checkout or consult another project's database.
2. In the extracted source, run its `packaging/build.ps1` and
   `packaging/prepare-acceptance-data.ps1`, passing the build interpreter
   explicitly. Its fixture script imports its own source, which creates schema 12.
3. Open that fixture with the resulting **0.2.2 executable** using an isolated
   locator; close the application normally before taking the baseline. Record
   the executable identity and actual startup/close result. A hidden-desktop
   check supports preparation only; desktop acceptance remains pending.
4. Preserve that closed root as `upgrade-original/data-root`. Capture all
   business-table records, schema version, and resource-file hashes. Preserve
   the original database hash for source-isolation checks.
5. Copy the original into `upgrade-copy/data-root`. Confirm its files match the
   original. Do not open this transfer copy with the candidate during preparation;
   use a separate local rehearsal copy for build-machine checks.

For source extraction, run from the current repository:

```powershell
$staging = 'D:\TF-Preparation'
New-Item -ItemType Directory -Path $staging -ErrorAction Stop | Out-Null
git rev-parse 'v0.2.2^{commit}'
git archive --format=zip --output="$staging\v0.2.2-source.zip" v0.2.2
Get-FileHash -LiteralPath "$staging\v0.2.2-source.zip" -Algorithm SHA256
Expand-Archive -LiteralPath "$staging\v0.2.2-source.zip" -DestinationPath "$staging\previous-source"
pwsh -File "$staging\previous-source\packaging\build.ps1" -Python 'E:\Github\TrainingFeedback\.venv\python.exe'
pwsh -File "$staging\previous-source\packaging\prepare-acceptance-data.ps1" "$staging\previous-fixture" -Python 'E:\Github\TrainingFeedback\.venv\python.exe'
```

Choose an unused staging location and replace the interpreter path with the
verified build interpreter. When staging inside another Git checkout, prevent
Git from discovering that enclosing checkout (set `GIT_CEILING_DIRECTORIES` to
the enclosing repository root for the child build). An archive has no `.git`:
its manifest can legitimately have null source fields. Keep the archive hash,
tag commit, build log, and manifest hash in a separate provenance record;
do not replace null fields with a fabricated clean-checkout claim.

Do not create either older-version fixture with current code. For adjacent
coverage, repeat the five steps using this repository's `v0.5.1` tag in a separate
unused staging directory: extract its source, build and generate its fixture
using its own scripts, then open/close it with the matching 0.5.1 executable.
Capture schema 13 as `adjacent-original`, then create an unopened `adjacent-copy`.
The 0.6.0 candidate will migrate this copy to schema 14. Keep source helpers on
the build machine; both originals must remain byte-identical throughout testing.

| Previous program | Before opening with 0.6.0 | Expected automatic changes |
| --- | --- | --- |
| 0.2.2 | schema 12 | Migrations 13 and 14: nullable bundled identity fields and indexes, an empty `session_result_retraction` table, and migration metadata. Existing field values, business records, snapshots and resources stay unchanged. |
| 0.5.1 | schema 13 | Migration 14: an empty `session_result_retraction` table and migration metadata. Existing bundled identities and all old records/resources stay unchanged. |

Capture upgraded copies immediately after normal open/close, before exports,
training, approvals or catalog delivery. Migration must not create new guidance
drafts, approvals, retraction facts or user feedback. Never open schema 14 with
0.5.1; a rollback uses a preserved schema-13 root in a separate directory.

## 3. Execute On Independent Windows

### Isolated launch

Unpack under a path containing Chinese characters and spaces, for example
`D:\TF 验收\`. Use a new locator directory for first launch. In PowerShell 7:

```powershell
$acceptanceBase = 'D:\TF 验收'
$previousLocalAppData = $env:LOCALAPPDATA
try {
    $env:LOCALAPPDATA = Join-Path $acceptanceBase 'operator-localappdata'
    & (Join-Path $acceptanceBase 'programs\0.6.0\TrainingFeedback\TrainingFeedback.exe')
} finally {
    $env:LOCALAPPDATA = $previousLocalAppData
}
```

Use the same locator for restart tests. Use a new, explicitly named locator
directory to select another fixture at startup. Do not use the source-root
switch action while the fixture has a paused session: open the backup or
upgrade copy through a fresh startup locator instead. Close all application
processes before copying roots.

### Scenarios And Expected Results

1. **Candidate identity.** Record environment details and recheck the transferred
   manifest and all program files. A mismatch fails this scenario; obtain a
   correct complete copy before continuing.
2. **First launch/cancel/create.** Launch with an empty locator. From 0.4.1 the
   dialog prefills the documents-folder default and preselects create for a new or
   empty path, open for a path that already has a marker; an occupied path is not
   prefilled. Confirm the suggestion is only a suggestion: cancel directory
   selection and the process exits with no root created, including no root at the
   suggested default. Relaunch, replace the suggestion, and create a root in a
   separate empty Chinese-and-space path. Program files stay separate.
3. **Reopen/restart.** Close and relaunch with the same locator. The selected root
   opens without asking again; repeat after a Windows restart.
4. **Invalid/occupied roots.** Through startup selection, try an unrelated
   nonempty directory and a copy missing its marker. Expect readable errors,
   no partial root, and no changes to unrelated files. Do not damage originals.
5. **Ordinary user.** Perform the sequence without elevation; record account
   privilege and any request for administrator access. A required elevation fails.
6. **Upgrade.** Open only `upgrade-copy` with the 0.6.0 candidate, then close normally before
   exporting or changing any content. Preserve the closed upgraded copy for
   comparison on the build machine. Expect schema 12 → 14, identical old fields
   and business rows, unchanged historical snapshots and resources. New bundled
   identity fields stay null, the retraction table is empty, and startup creates
   no new guidance drafts. Check integrity and foreign keys on the build machine. Keep
   `upgrade-original` unopened and byte-identical. After this capture, inspect
   history and feedback on a working copy and export evidence through the UI.
   Repeat on `adjacent-copy` for 0.5.1 → 0.6.0; expect schema 13 → 14 with the
   existing identity values preserved and an empty retraction table. Record both
   outcomes in row 6 and preserve both originals. Use only preserved schema-13
   copies for an old-program rollback check.
7. **Online backup/errors.** Open a working copy of the functional fixture. In
   Settings, back up while the paused session exists to an explicitly selected
   empty directory outside the source. Try occupied, nested, and unavailable
   destinations separately: errors must be readable, without partial copies.
   Also back up the workflow copy after a synthetic review attachment has been
   stored and the training copy after a result retraction has been recorded.
8. **Recovery.** Close the program; with a fresh locator select the backup root.
   Resume the paused session, inspect history and feedback, and export evidence.
   Check original notes and images; subsequent edits in the backup must not
   modify the closed source. Compare the source against the baseline taken
   immediately after it was closed, before opening the backup. Verify managed
   answer-file hashes and retraction history in those additional backups as well.
9. **Display.** On the actual desktop, record resolution and Windows scaling.
   Run the matrix below, checking long Chinese text and all listed dialogs,
   including the review/catalog checks through 0.5.1 below.
10. **Training controls.** Open an action with many actual-set rows. At every
    tested display combination, Pause / Abort / Finish stay reachable without
    scrolling training content. Actual-dose Save / Cancel must also stay reachable.
    Execute the 0.6.0 plan/training checks below. Record evidence before
    interacting with controls.

Schema migration can change the database file hash; compare logical data and
resources for the upgraded copy. The original's database hash must stay fixed.
Separate automatic-upgrade comparison from later exports, training, or content
acceptance, which intentionally create new records. Build-machine comparison
of returned closed copies does not change the independent-runtime environment.

If a check fails, record reproduction, expected/actual behavior, candidate,
environment, and evidence before repair. A changed candidate receives a new
identity and reruns affected checks; retain prior results as historical.

## 4. Evidence Forms

Copy these forms per candidate/environment. Use `pass`, `fail`, or `not run`;
unavailable scenarios remain `not run` with the reason. Do not prefill a pass
from a build-machine check.

Environment: date/operator; Windows edition/build/x64; clean VM or machine;
absence of Python/Conda/source/build access; ordinary-user status; program/data
paths; candidate version/commit/build time; manifest and executable SHA-256;
previous version and source-provenance record; monitor/resolution/scaling.

| # | Scenario | Result | Actual steps and expected/actual result | Evidence / blocker |
| --- | --- | --- | --- | --- |
| 1 | Candidate identity and transferred hashes | not run | Pending independent environment | |
| 2 | First launch, cancel, create Chinese + space root | not run | Pending independent environment | |
| 3 | Locator reopen and restart | not run | Pending independent environment | |
| 4 | Invalid root and occupied directory | not run | Pending independent environment | |
| 5 | Non-administrator operation | not run | Pending independent environment | |
| 6 | v0.2.2 → 0.6.0 and v0.5.1 → 0.6.0 migrations; originals isolated | not run | Pending independent environment | |
| 7 | Online backup and destination failures | not run | Pending independent environment | |
| 8 | Open backup, resume, inspect, export | not run | Pending independent environment | |
| 9 | Actual-desktop display matrix and review/catalog workflows through 0.5.1 | not run | Pending real desktop | |
| 10 | 0.6.0 plan editing, result retraction, and fixed session/entry controls | not run | Pending real desktop | |

For every display row check startup errors, root selection/switching, training
with many actual sets, exercise detail, complete editor, revision review, and
bundled-update preview. Select an older guidance revision and edit it, inspect
long Chinese text, reorder steps, and check save/cancel/approval controls.
If the functional fixture has only one guidance revision, first save a new
draft on a working copy, then select the older revision for this check.
Use fixture copies for edits and synthetic approvals; never treat these as
actual content review.

For 0.3.1 and later, include numeric-set notes, per-side prescriptions and a
free-dose explanation in training/history/exports; edit the catalog on a working
copy and confirm history still uses frozen text. Open next-day feedback from
Home with four primary areas and eleven performed actions. Scroll all content
and confirm submission state/button remain accessible; unanswered choices stay
unknown after submission. Long history details must not displace Export.

Retain the 0.4.0 revision-selection checks: create two drafts and deliberately
select the older one. Check that
editing, guidance review and activation target it, while a published selection
is read-only and can be cloned. Importing opens the new draft; original rationale
and managed source remain unchanged after local edits. Confirming a changed
preview must ask for a fresh review. In guidance review, occurrence starts empty;
test a date-only value and a timezone-aware value, separate approval time, invalid
or empty input, unchecked approval, cancellation and clearing inputs on revision
switch. Test approvals must retain explicit synthetic labels.

For review/catalog behavior through 0.5.1, use the supplemental workflow copy.
Record these outcomes with scenario 9; every item needs an actual result:

- Batch guidance approval starts with nothing checked. Inspect the selected
  revision and its difference, check two intended drafts, and record one synthetic
  review's source, occurrence, note and answer file. Cancel first and verify no
  approval; then explicitly approve the checked revisions and verify only those
  revisions received the shared review facts.
- Verify the answer is a managed copy in `reviews/` with its original name and
  SHA-256 recorded. Preserve a baseline for the backup/recovery scenarios;
  older reviews without an attachment still display normally.
- Occurrence begins empty. Check date-only, timezone-aware time, Today, Now and
  Reuse Last, plus manual editing. Reuse Last remembers a successful approval in
  this run, not a cancelled or failed one. Switching revisions clears the current
  input and explicit confirmation; opening the form invents no occurrence.
- Explicitly import the prepared missing bundled exercise. Verify its catalog
  fields and one unreviewed guidance draft, no approval or activation, and no
  duplicate on repeat. Edit its catalog text on a working copy and verify later
  bundled delivery does not overwrite that text.

For 0.6.0, record the following with scenario 10 using functional working copies:

- Plan editing uses a list and one group table. Enter an invalid dose, attempt
  to switch the selected action or save, and verify the error blocks the change
  while preserving input. Correct it, save, reopen and compare values and original
  notes. Exercise the collapsible batch panel with many rows; Save / Cancel remain
  accessible at every required display combination.
- Record a result and verify it stays visible. Select another unrecorded action
  and choose Partial or Exceeded to open actual-dose entry. Edit and cancel, then
  reopen and explicitly save; verify cancelled input is not persisted and the
  saved result contains exactly the entered sets. Unsaved entry must not be
  silently discarded by navigation or session controls.
- Cancel a retraction confirmation and verify no change. Confirm it for a recorded
  result in a nonterminal session: the result clears, its former facts are audited,
  and the frozen prescription stays unchanged. Close/reopen, record a replacement,
  and verify history and JSON/Markdown retain the prior retraction facts.
- Exercise all four actual result choices, extra/partial sets, pause/resume,
  abort with a reason and finish on synthetic copies. Finish must not bypass a
  result cleared by retraction. After finish or abort, result retraction is unavailable.
- Check home, dark navigation, plan/history views, training and actual-dose entry
  for readable Chinese text, visible errors, disabled states and clear save state.

Use actual per-item observations in scenarios 9–10; a screenshot of the window
alone does not prove its state-changing behavior. Use separate copies where a
completed action would prevent checking cancellation or an earlier state.

| Resolution | Scaling | Result | Checked windows and control visibility | Evidence / unavailable reason |
| --- | --- | --- | --- | --- |
| 1366×768 | 100% | not run | | |
| 1366×768 | 125% | not run | | |
| 1366×768 | 150% | not run | | |
| 1920×1080 | 100% | not run | | |
| 1920×1080 | 125% | not run | | |
| 1920×1080 | 150% | not run | | |

Use these resolutions where available and document actual alternatives and
unavailable combinations. The 100%/125%/150% checks are required; unavailable
required coverage keeps the display gate pending. Phase 8 closes only when all
ten scenario rows have the required passing evidence. Offscreen, hidden-desktop,
and process-survival checks remain supporting evidence only.

## 5. 0.7.0 Seamless-Upgrade Acceptance (Planned; Not Run)

The [development contract, Section 12](../../development-plan.md#12-070-development-contract-planned)
owns scope and invariants. Identify the actual candidate application version,
source snapshot, installer/build manifest, catalog version and manifest hash,
and assigned target schema before executing these scenarios. Do not copy a
0.6.0/0.6.1 result or schema number into the new candidate's evidence.

### 5.1 Candidate And Input Preparation

- 070-B supplies `training_feedback/catalog/catalog.sqlite3`, its manifest and
  resource resolver. `packaging/build.ps1` verifies both source and collected
  catalogs and exempts only that exact database from its user-data leak check.
  Wheel and isolated PyInstaller collection are locally verified; the source
  catalog still has no delivered illustrations. New-model `LibraryContext` uses
  schema 17 with empty user reference/snapshot tables until explicit actions.
  Existing-root conversion and UI routing are 070-G work, not an operator choice.
- 070-C adds decode/dimension checks to catalog build verification and runtime
  qualification, plus schema 18 exact-version review events. Collect the new
  catalog page, review/editor dialogs and `LibraryWorkflowService`; exercise
  family/position filters, unreviewed valid-image use, corrupted retained images,
  stale targets and batch rollback on temporary new-model roots. Full desktop
  activation/session flows integrate these services in D/E before G cutover.
- 070-D adds schema 19 group-plan storage and packaged `contracts/plan-v2.schema.json`;
  `jsonschema` is a runtime dependency. Include the new plan/editor/activation page
  and verify explicit per-round/side/rest displays, invalid-input retention,
  stale-preview rejection and transactional activation pins. Portable plan-scope
  evidence includes JSON/Markdown/current schema and image assets; session-scope
  v2 results are supplied by E. Importing a v1 file through the new page must fail.
- 070-E adds schema 20, `GroupSessionController`, session service/repository/handoff
  and the training, start/resume/history and feedback pages. Verify these modules
  are present in the collected payload. Temporary-root source tests cover exact
  side doses, round batch membership, stale requests, rollback, pause/restart,
  terminal guards, unknown feedback and JSON/Markdown agreement. Backup/reopen
  with an empty replacement catalog must retain session text/assets and position.
  The program's desktop route remains unchanged until G; a startup smoke does
  not establish packaged end-to-end grouped execution or independent acceptance.
  Local E verification on 2026-09-20: 445 source tests pass, Ruff/diff checks pass,
  and the isolated PyInstaller payload at `.tmp/070-e-package` (retired 2026-09-21)
  includes all new
  modules, schema 20 and the matching v2 schema resource. The packaged 36-entry
  catalog verifies. An isolated profile/system-PATH offscreen start remained alive
  for five seconds and created no locator/database before confirmation. Local
  hashes and source inventory are preserved at
  `.tmp/releases/0.7.0/070-e-package/verification.json`;
  themed synthetic UI renders are in `.tmp/070-e-visual`. These are build-machine
  checks only; Section 5.2 independent/real-desktop rows remain not run.
- 070-F adds schema 21 and `LibraryLifecycleService`, its repository/domain module,
  and `LibraryLifecyclePage`. The catalog page opens batch removal/restoration and
  reference review; `LibraryContext.create_removal_page()` supports direct composition.
  Verify root-local decisions, publisher withdrawal/missing entries, stale content
  and impacts, transactional rollback, explicit restoration and separate enablement.
  Previously affected activation pins remain blocked for new starts until a newly
  confirmed revision; frozen unfinished sessions and historical export stay usable.
  Source verification on 2026-09-20: 479 tests pass (34 new F cases), including
  backup/root isolation and missing-parent identity retention. The isolated payload
  was `.tmp/070-f-package` (retired 2026-09-21), schema 21; new modules and the
  packaged 36-entry catalog
  are checked. Its isolated-profile/system-PATH offscreen smoke stays alive for
  five seconds without creating a locator/database before confirmation.
  Hashes/source inventory preserved at
  `.tmp/releases/0.7.0/070-f-package/verification.json`; themed synthetic
  request/review/library images and 800×600/1040×780 control bounds:
  `.tmp/070-f-visual`. These are build-machine checks; no personal candidate was
  replaced, and G conversion/full routing and independent Windows acceptance remain pending.
- 070-G completes the end-to-end conversion path: G1 recovery protocol, G2 schema 22
  `convert_catalog_root`, and G3 desktop wiring. Normal launch and data-root
  switching convert a schema-16 root automatically with pending-journal recovery
  and actionable failure messages; `LibraryContext` is the only desktop context and
  the retired runtime, startup seeding, old handoff and old UI pages are removed
  with their dual-runtime fallbacks. The packaged acceptance fixture is now copied
  and hash-verified from the frozen `docs/contracts/baseline/schema16-root/` bytes;
  the generator that depended on the retired runtime is gone. Source verification
  on 2026-09-20: the resident suite collects 184 cases with the 070-G3 dev-scope
  selection (29 unique cases) passing and Ruff clean on source and tests. These are
  build-machine checks only; the Section 5.2 rows remain not run, and the real
  0.6.1 binary adjacent upgrade is a 070-H gate.
- 070-H build-machine preparation (2026-09-20): the directory build
  (`dist/TrainingFeedback/`, 257 files, application version **0.7.0**,
  source_dirty=true at base 072c931) verifies against its manifest, and the
  payload contains the 070-baseline-1 catalog (36 entries, still no delivered
  illustrations), the v2 plan contract and `sqlite3.dll`. A rehearsal drove the
  packaged binary offscreen against a Chinese-and-space-path copy of the frozen
  schema-16 fixture: the journaled conversion completed to schema 22 with exactly
  one conversion run, all three original import/export registrations available,
  integrity/foreign-key checks clean and the recovery snapshot retained; a
  relaunch did not repeat the conversion; a first-launch smoke with an empty
  isolated profile stayed alive five seconds without creating a locator or data
  files. Evidence: `.tmp/070-h-package/verification.json` and
  `rehearsal-result.json`. No installer was built (Inno Setup 6 unavailable on
  the build machine), so formal installer/upgrade acceptance stays open, and the
  Section 5.2 rows remain not run.
- The [070-A contract annex](../../contracts/0.7.0-contracts.md) supplies the source
  inventory, v1 schema snapshot, v2 structural example and schema-16 preservation
  fixture. Its source-only copy/reopen checks are preparation evidence; retain
  the actual 0.6.1 binary identity when opening the baseline for packaged upgrade.
- Include the read-only catalog database, manifest and actual illustration
  assets in the program payload. Validate catalog and build manifests before
  transfer. An image filename mapping or generation prompt is not an asset.
- Prepare a synthetic **0.6.1/schema-16** baseline using the matching previous
  program, with a separately preserved closed original and upgrade copy.
  Include user overrides/custom movements, a missing bundled key, renamed
  actions, actual image files, missing/corrupt images, review attachments,
  enabled/disabled actions, draft/active plans, paused/terminal sessions,
  next-day feedback, retraction audits, original exports/imports and settings.
  Mark every synthetic review/training fact as synthetic. Never use real data
  for destructive or fault-injection preparation.
- Capture logical facts, original text bytes, resource hashes and unknown fields.
  Expected changes list the new references/structures and eligibility effects,
  not blanket permission to rewrite business rows. Add earlier supported-schema
  chain fixtures and future-schema rejection coverage on the build machine.
- Prepare current-model group fixtures with distinct units, repeated movement
  instances, same-side and alternating-side order, exception outcomes and
  removal references. Include stale-target cases and a subsequent catalog
  missing/withdrawing a formerly available movement.
- Plan migration-failure injections for backup, asset staging, SQL commit,
  resource publication and cleanup. Run them on isolated copies before desktop
  transfer; supply packaged interrupted-state fixtures where feasible, rather
  than asking an operator to edit SQL in the independent environment.

### 5.2 Independent Candidate Scenarios

Use the independent Windows and ordinary-user requirements at the top of this
runbook. After preparation, every row starts `not run`; fill it only with the
identified candidate's actual evidence.

| ID | Operation | Required result | Status |
| --- | --- | --- | --- |
| 070-01 | Install and create a fresh root in Chinese/space-containing paths. | Program reads its bundled catalog outside the user root; no full bundled seed copy or program-directory writes; drafts and source labels are truthful. | not run |
| 070-02 | Install over 0.6.1; start normally with its selected root/locator. | Automatic verified recovery snapshot and conversion, same selected root and meaningful settings; no wizard, re-import, mapping, bundled acceptance or old/new selector. | not run |
| 070-03 | Compare upgraded data, restart twice and switch roots. | Original user facts/files and unknowns preserved; current references/settings only; no duplicate conversion/assets or repeated confirmation for unchanged eligible plans. | not run |
| 070-04 | Open prepared interrupted roots and exercise backup/access/disk failure. | Either complete conversion or recover the prior consistent root; exact error reported, no half-success or obsolete-settings fallback; recovery copy retained. | not run |
| 070-05 | Exercise text/image gate through library, review, plan and new-session actions. | Missing/corrupt/escaping/mismatched images block; valid unreviewed images do not fabricate review; prior review evidence survives current invalidation. | not run |
| 070-06 | Browse families; edit and activate an A→B group with rounds/sides. | Distinct variant identities and per-round units; explicit side/rest/transition order; immutable activation pins; stale/invalid edits rejected without lost input. | not run |
| 070-07 | Record individual and whole-round results; partial work, retraction, pause/restart, abort/finish. | Correct member/round/side position and quantities; batch atomicity; no duplicate result or defaulted unknown; history/export agree. | not run |
| 070-08 | Request/approve/reject/cancel/restore removal; update to catalog withdrawal. | Root-local user decisions do not write the package; no cascade loss; new starts blocked for removed content, frozen unfinished work/history remain usable. | not run |
| 070-09 | Export evidence/images and import a v2 plan; attempt a newly supplied v1 file. | Portable current schema and image bytes/hashes; draft-only import; v1 clearly rejected with current schema guidance, no compatibility selector/converter. | not run |
| 070-10 | Back up while open, reopen the copy with a newer catalog, resume and re-export. | Customizations, reviews, snapshot text/assets and paused state survive; historical display does not need an old installed catalog. Source root remains isolated. | not run |
| 070-11 | Inspect all settings/library/import menus, then upgrade/uninstall program files. | No old-settings switches, legacy library, bundled-acceptance control or data-reset requirement; installer/uninstaller preserve locator and user root. | not run |
| 070-12 | Real-desktop 100/125/150% scaling, small-window and long-Chinese-content checks. | Family/group editor, image review, removal impact and training state are readable; fixed save/cancel/pause/abort/finish reachable at recorded resolutions. | not run |

The installer-file replacement itself must not write user data. First application
launch may perform exactly the declared automatic data migration; verify these
two boundaries separately. An upgraded missing-image plan stays visible with
specific remediation in the normal plan detail page; no old-rule switch exists.
Already paused sessions use converted frozen evidence. A complete unchanged
eligible plan requires no repeated approval. Show updated catalog content
automatically while preserving pinned active prescriptions and user overrides.

### 5.3 Evidence And Exit

For each row record candidate/catalog/schema and environment identity, input
baseline, exact operation, expected/observed result, resource/fact comparison,
evidence path/hash, and any unavailable reason. Verify no old-format runtime
fallback remains through source inspection as well as the visible-menu check;
automatic one-time migration readers and immutable original files are evidence
retention, not selectable legacy settings.

Restart/failure tests must account for files as well as SQLite transactions.
Recovery snapshots must not recursively duplicate backups or be mistaken for
ordinary new user data roots. Unsupported newer roots remain untouched. The
older binary must reject the upgraded schema rather than corrupting it; there
is no in-app downgrade/settings mode. Normal backup/open remains available.

Every required row needs actual passing evidence for formal 0.7.0 acceptance.
Record unavailable environments as not run; build-machine checks do not close
independent acceptance. Refresh the transfer instructions for the exact build
when implementation completes. Real content review, W4 training and technical
packaged acceptance remain separately evidenced under the development plan.
