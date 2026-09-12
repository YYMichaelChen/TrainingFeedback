# Packaged Acceptance Runbook

Requirements live in [development-plan.md](development-plan.md), Sections 7–9.
This runbook covers the 0.4.0 candidate, with 0.3.1 retained as a separate
correction release. Test v0.2.2 → 0.4.0 migration and 0.3.1 → 0.4.0 adjacent
opening. For the 0.3.1 candidate, test 0.3.0 → 0.3.1 separately.
Use only isolated synthetic roots belonging to this application.

Preparation and build-machine startup checks are supporting evidence. Execute
8-B2 in an independent Windows x64 environment with no Python, Conda,
application source checkout, or access to the build environment. Use a clean VM
or separate machine and an ordinary non-administrator account. A new account
on the build machine does not establish runtime independence.

## 1. Candidate And Transfer Preparation — Build Machine

Use the identified candidate directory and its manifest. The previous 0.3.0
candidate is from commit `ec611f0464e579e6bc5ea2adf335278df0ac3d1c`; its checks
remain historical evidence. Build changed candidates with `packaging/build.ps1`
and the pinned toolchain. A rebuild gets its own acceptance identity. If
`source_dirty=true`, retain the exact source ZIP, file hashes and base commit on
the build machine; the base commit alone does not identify those source changes.

The local preparation delivery contains these transfer inputs:

| Input | Purpose |
| --- | --- |
| `programs/0.4.0/TrainingFeedback/` and adjacent build manifest | Complete candidate directory; copy the executable and `_internal` together. |
| `programs/0.3.1/TrainingFeedback/` and adjacent build manifest | Previous candidate for the adjacent-version scenario. |
| `programs/0.2.2/TrainingFeedback/`, manifest, and source-provenance record | Previous-version build recreated from this repository's tag. |
| `inputs/functional/data-root/` | Current synthetic training, feedback, imported draft, and recovery fixture. |
| `inputs/upgrade-original/data-root/` | Closed schema-12 baseline; never open with the new application. |
| `inputs/upgrade-copy/data-root/` | Unmodified copy for the independent upgrade scenario. |
| `inputs/adjacent-original/data-root/` and `inputs/adjacent-copy/data-root/` | 0.3.1-generated, normally opened/closed baseline and unopened copy. |
| `baselines/upgrade-original.json` | Logical records, schema version, resource hashes, and original database hash. |
| `candidate-verification.json`, `START-HERE.md`, `acceptance-evidence.md` | Local preparation evidence, operator instructions, and unfilled independent acceptance results. |

Keep source archives, Python helpers, build logs, and development environments
on the build machine. Transfer only the package above to the independent
environment. Keep program and data directories separate after unpacking.

Record build time, app version, source revision, source-dirty flag, architecture,
Python/PySide6/PyInstaller versions, and file count. Verify every file, including
unexpected extra files, on the build machine and after transfer. With PowerShell 7,
set the path to the version directory and run:

```powershell
$candidateDir = 'D:\TF 验收\programs\0.4.0'
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

Expect the selected version (normally `0.4.0`) and use its actual source identity,
dirty flag and manifest file count. Record the manifest hash and entry executable
hash in the environment record; never substitute the previous candidate's values.

## 2. Prepare Three Separate Inputs — Build Machine

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
[guidance review runbook](guidance-review-runbook.md) for normal seed drafts.

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

Do not create the upgrade fixture with current code and then open it in 0.2.2.
For adjacent-version coverage, generate a second fixture using the preserved
0.3.1 source snapshot, open/close it with the corresponding 0.3.1 executable,
and create original/copy baselines in the same way. Expect schema 13 → 13 and
no changes to existing records/resources. Keep source helpers on the build machine.
That produces schema 13 before the upgrade test has started.

## 3. Execute On Independent Windows

### Isolated launch

Unpack under a path containing Chinese characters and spaces, for example
`D:\TF 验收\`. Use a new locator directory for first launch. In PowerShell 7:

```powershell
$acceptanceBase = 'D:\TF 验收'
$previousLocalAppData = $env:LOCALAPPDATA
try {
    $env:LOCALAPPDATA = Join-Path $acceptanceBase 'operator-localappdata'
    & (Join-Path $acceptanceBase 'programs\0.4.0\TrainingFeedback\TrainingFeedback.exe')
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
2. **First launch/cancel/create.** Launch with an empty locator. Cancel directory
   selection: the process exits and no root is created. Relaunch and create a
   root in a separate empty Chinese-and-space path. Program files stay separate.
3. **Reopen/restart.** Close and relaunch with the same locator. The selected root
   opens without asking again; repeat after a Windows restart.
4. **Invalid/occupied roots.** Through startup selection, try an unrelated
   nonempty directory and a copy missing its marker. Expect readable errors,
   no partial root, and no changes to unrelated files. Do not damage originals.
5. **Ordinary user.** Perform the sequence without elevation; record account
   privilege and any request for administrator access. A required elevation fails.
6. **Upgrade.** Open only `upgrade-copy` with the 0.4.0 candidate, then close normally before
   exporting or changing any content. Preserve the closed upgraded copy for
   comparison on the build machine. Expect schema 12 → 13, identical old fields
   and business rows, unchanged historical snapshots and resources. New bundled
   identity fields stay null; startup creates no new guidance drafts. Keep
   `upgrade-original` unopened and byte-identical. After this capture, inspect
   history and feedback on a working copy and export evidence through the UI.
   Repeat on `adjacent-copy` for 0.3.1 → 0.4.0; expect schema 13 → 13. Record both
   outcomes in row 6 and preserve both originals. Candidate 0.3.1 uses a separate
   0.3.0 → 0.3.1 baseline and evidence form.
7. **Online backup/errors.** Open a working copy of the functional fixture. In
   Settings, back up while the paused session exists to an explicitly selected
   empty directory outside the source. Try occupied, nested, and unavailable
   destinations separately: errors must be readable, without partial copies.
8. **Recovery.** Close the program; with a fresh locator select the backup root.
   Resume the paused session, inspect history and feedback, and export evidence.
   Check original notes and images; subsequent edits in the backup must not
   modify the closed source. Compare the source against the baseline taken
   immediately after it was closed, before opening the backup.
9. **Display.** On the actual desktop, record resolution and Windows scaling.
   Run the matrix below, checking long Chinese text and all listed dialogs.
10. **Training controls.** Open an action with many actual-set rows. At every
    tested display combination, Pause / Abort / Finish stay reachable without
    scrolling training content. Record evidence before interacting with controls.

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
| 6 | v0.2.2 → 0.4.0 migration and 0.3.1 → 0.4.0 opening; originals isolated | not run | Pending independent environment | |
| 7 | Online backup and destination failures | not run | Pending independent environment | |
| 8 | Open backup, resume, inspect, export | not run | Pending independent environment | |
| 9 | Actual-desktop display matrix | not run | Pending real desktop | |
| 10 | Fixed session controls | not run | Pending real desktop | |

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

For 0.4.0, create two drafts and deliberately select the older one. Check that
editing, guidance review and activation target it, while a published selection
is read-only and can be cloned. Importing opens the new draft; original rationale
and managed source remain unchanged after local edits. Confirming a changed
preview must ask for a fresh review. In guidance review, occurrence starts empty;
test a date-only value and a timezone-aware value, separate approval time, invalid
or empty input, unchecked approval, cancellation and clearing inputs on revision
switch. Test approvals must retain explicit synthetic labels.

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
