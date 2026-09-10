# Packaged Acceptance Runbook

Scope and requirements live in
[development-plan.md](development-plan.md) Sections 8–9 (Phase 8-B2). This
runbook only lists steps, expected results, and the evidence table. Run every
step in an independent Windows x64 environment: no Python, no Conda, no source
checkout, and no access to the build machine. A clean VM or separate machine is
required; a new account on the build machine is not sufficient.

## 1. Candidate Identification

1. Build on the build machine: `pwsh -File packaging/build.ps1`.
2. Record from `dist/TrainingFeedback.build-manifest.json`: build time,
   application version, Python/PySide6/PyInstaller versions, architecture,
   source revision, and file count.
3. Copy the complete `dist/TrainingFeedback/` directory and the manifest to the
   acceptance environment. Record the transfer hash of
   `TrainingFeedback.exe` against the manifest.

## 2. Synthetic Fixture

On any machine with the repository toolchain (or on the build machine before
transfer):

```powershell
pwsh -File packaging/prepare-acceptance-data.ps1 D:\TF-Acceptance
```

This creates an isolated data root with synthetic completed/partial/paused
sessions, plan revisions, verbatim notes, next-day feedback, images, exports,
and an imported draft, plus `D:\TF-Acceptance\localappdata\` with a locator.
The image assets are decodable synthetic PNG fixtures, not exercise guidance.
All fixture content is marked `【合成验收数据】`. The locator records the
fixture's absolute path; generate it at its final location. If the fixture is
moved, re-create it or select its data root through the normal UI. To start the
packaged application directly into the fixture:

```powershell
$env:LOCALAPPDATA = "D:\TF-Acceptance\localappdata"
& D:\TrainingFeedback\TrainingFeedback.exe
```

Use a separate empty directory (no preset `LOCALAPPDATA`) for the first-launch
scenarios so the application asks for a data root.

## 3. Scenarios

### 3.1 First launch and data-root lifecycle

- Launch without a locator: the data-root dialog appears; cancel leaves no data.
- Create a new root in an empty directory whose path contains Chinese
  characters and spaces; close and relaunch: the same root opens without
  re-asking.
- Opening an occupied directory (contains unrelated files) and an invalid root
  (missing marker) produces readable errors; nothing is modified.
- Run as an ordinary (non-administrator) user throughout.

### 3.2 Upgrade on a copied real-class root

- Prepare a root with the fixture script, preferably opened once by an actual
  previous-version build; record both application versions.
- Close the application. Baseline: export evidence, and hash the database,
  marker, configuration, images, exports, and imports.
- Replace only the program directory with the candidate; launch.
- Expected: only declared schema migrations run; logical records, historical
  snapshots, and resource-file hashes are unchanged. Same-version relocation is
  not cross-version upgrade evidence.

### 3.3 Packaged backup and restore drill

- With the fixture root open (paused session present), create a backup through
  the settings page into an explicitly selected empty directory outside the
  source root.
- Close the application; relaunch and select the backup copy as the data root.
- Resume the paused session, inspect history and next-day feedback, and export
  evidence again.
- Expected: source root untouched; verbatim notes and images byte-identical;
  an invalid or occupied backup destination is rejected readably without
  partial copies.

### 3.4 Real-desktop display checks

- At 100%, 125%, and 150% scaling, at recorded resolutions including 1366x768
  and 1920x1080 where available: check startup errors, root switching dialogs,
  long Chinese text, and an action with many actual-set rows.
- Expected: Pause / Abort / Finish remain accessible without scrolling the
  training content in every checked configuration.

## 4. Evidence Table

| # | Scenario | Result (pass/fail/not run) | Evidence |
| --- | --- | --- | --- |
| 1 | Candidate identified (manifest fields recorded) | | |
| 2 | First launch, cancel, create root (Chinese + space path) | | |
| 3 | Reopen via locator; restart keeps root | | |
| 4 | Invalid root and occupied directory rejected readably | | |
| 5 | Ordinary non-administrator operation | | |
| 6 | Upgrade replaces only program files; data unchanged | | |
| 7 | Packaged backup while open; invalid destination rejected | | |
| 8 | Open backup copy; resume paused session; export again | | |
| 9 | Display 100% / 125% / 150%, 1366x768 and 1920x1080 | | |
| 10 | Session controls accessible without scrolling | | |

Leave unavailable scenarios "not run" with a note; Phase 8 acceptance stays
pending until every row has evidence. Offscreen tests and process-survival
smoke checks are supporting evidence only.
