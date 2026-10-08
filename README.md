# TrainingFeedback

TrainingFeedback is a new local-first PySide6 training desktop application. It
is intentionally independent from the existing `Exercises@home` application,
database, Streamlit UI, wardrobe data, and submission format.

## Current status

- Application: `0.8.14`
- Database schema: `24`
- Current development release: [`0.8.14`](docs/releases/0.8.14/design.md)
- Latest GitHub distribution: [`v0.8.14`](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.14)
- Version and candidate status: [`docs/history/README.md`](docs/history/README.md)

## Run

```powershell
python -m venv .venv
.venv\Scripts\pip install -e .
training-feedback
```

## Develop

当前开发遵循 [最小验证政策](docs/development-plan.md#91-release-and-follow-up-boundaries)：
每次更新仅检查可能导致应用打不开的具体风险，最多 3 项，通常 0～1 项；
无此风险时为 0 项。人工测试默认 0 项，其它问题随使用反馈解决。

Install development dependencies as needed:

```powershell
.venv\Scripts\pip install -e .[dev]
```

Do not run bare pytest, default regression profiles or full version suites.
When a concrete startup risk exists, select only the relevant node IDs under
one stable update scope, following [test instructions](tests/README.md).
The existing larger tool budgets are not permission to execute more cases.
Documentation-only work uses link/consistency and diff checks, with no app tests.

See the [development workflow](docs/development-workflow.md) for the short
decision, verification and delivery procedure.

## Project layout

- `src/training_feedback/domain/` — pure business rules and value objects (no
  Qt, no SQL).
- `src/training_feedback/application/` — use-case services coordinating domain
  workflows and repositories.
- `src/training_feedback/data/` — SQLite repositories, supported migrations,
  data-root lifecycle, backup/recovery, bundled catalog source and current
  export/import file handling. SQL is only allowed here.
- `src/training_feedback/ui/` — PySide6 pages and dialogs (no SQL).
- `src/training_feedback/app.py` / `bootstrap.py` / `main.py` — composition
  root, startup coordination, and the Qt entry point.
- `tests/` — pytest suite; always uses temporary databases.

## Package and install

Windows installation packages are distributed through this repository's
[GitHub Releases](https://github.com/YYMichaelChen/TrainingFeedback/releases).
Download the Setup executable for the required version and run it to install or
update. The application also checks the latest stable Release after opening and
can download, verify and hand its Setup to the installer after the client exits.

The Windows build first produces a PyInstaller directory layout. The verified
build environment and pinned toolchain are recorded in
`packaging/requirements-build.txt`; with those installed, run:

```powershell
pwsh -File packaging/build.ps1
```

For a normal Windows installation package, install Inno Setup 6 on the build
machine and run:

```powershell
pwsh -File packaging/build.ps1 -Installer
```

The optional `-ISCC 'C:\Path\to\ISCC.exe'` parameter selects an explicit Inno
Setup compiler. The result is
`dist/installer/TrainingFeedback-<version>-Setup.exe`. Distribute that single
Setup.exe to users; they do not need Python, the repository, or PyInstaller. An
adjacent `*.build-manifest.json` records the Setup.exe hash and the complete
payload manifest for release verification.

Record the actual Authenticode status of each Setup.exe. An unsigned local build
may show an unknown-publisher warning; public distribution requires a trusted
signature under the packaged-acceptance runbook.

The build interpreter resolves to `-Python <path>` when given, then
`.venv\Scripts\python.exe` (standard venv), then `.venv\python.exe` (Conda
layout). The build verifies both pinned packaging dependencies and the
declared Python/PySide6 baseline, isolates binary discovery from unrelated
developer-tool `PATH` entries, and writes
`dist/TrainingFeedback.build-manifest.json` with versions, source revision,
and artifact hashes.

The entry point is `dist/TrainingFeedback/TrainingFeedback.exe`; move or copy
the whole `dist/TrainingFeedback/` directory together. User data always lives
in the separately chosen data root, never in the program directory.

The Setup.exe uses a stable application identity and installs per-user by
default to `%LocalAppData%\Programs\TrainingFeedback`. Running a newer Setup.exe
over the existing installation performs a standard in-place upgrade: it closes
the running app when needed, replaces only the program payload, and keeps the
Start Menu shortcut. Uninstall removes the installed program and shortcuts, but
does not remove the locator or the selected data root. The data root therefore
survives upgrades and uninstalls and can be selected again after reinstalling.

The installer is intentionally not a source-code updater. The release flow is:
build a new Setup.exe, attach it to the matching GitHub Release, then run it on
the user's machine.

Building an installer does not trigger a manual acceptance checklist. Any
permitted startup check uses an isolated temporary profile and synthetic root;
see the [packaged acceptance runbook](docs/packaged-acceptance-runbook.md).
Build manifests identify the exact source revision and payload. Independent
Windows acceptance begins only on an explicit public-release request; external
content review, W4 and personal-data transition have separate gates in the
[product specification](docs/development-plan.md#9-delivery-gates).

## Documentation

Use the [documentation index](docs/README.md) to find the authoritative product
specification, procedures, release design, current identity map and historical
evidence. Active release tasks, when Planscope is initialized locally, are in
`.planning/INDEX.md` and its linked PLAN. A fresh clone does not need
`.planning/` to use the tracked project documentation.
