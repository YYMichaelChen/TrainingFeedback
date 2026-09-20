# TrainingFeedback

TrainingFeedback is a new local-first PySide6 training desktop application. It
is intentionally independent from the existing `Exercises@home` application,
database, Streamlit UI, wardrobe data, and submission format.

## Run

```powershell
python -m venv .venv
.venv\Scripts\pip install -e .
training-feedback
```

## Develop

```powershell
.venv\Scripts\pip install -e .[dev]
python -m pytest --test-scope my-task --basetemp .tmp/pytest
python -m ruff check src tests
```

Pytest defaults to a small smoke profile. For focused development, select the
affected file or node IDs with the same scope, for example:

```powershell
python -m pytest tests/test_database.py --test-scope my-task --basetemp .tmp/pytest
```

For releases, use `--test-tier patch`, `minor`, or `major` and a release scope
such as `--test-scope release-0.7.0`. Stage caps are **30 / 50 / 100 / 300** cases;
parameter combinations and the union of selections across commands count.
Explicit paths or `-k` replace the baseline profile. Keep one scope for a task
or release; do not clear `.tmp/test-budgets/` while it is in progress.
To inspect all cases without running them:

```powershell
python -m pytest --test-tier major --collect-only -q
```

See [verification policy](docs/development-plan.md#94-verification-and-record-ownership)
and [test maintenance notes](tests/README.md).

## Project layout

- `src/training_feedback/domain/` — pure business rules and value objects (no
  Qt, no SQL).
- `src/training_feedback/application/` — use-case services coordinating domain
  workflows and repositories.
- `src/training_feedback/data/` — SQLite repositories, schema migrations, data
  root lifecycle, backup, one-time schema-16 catalog conversion with upgrade
  recovery, bundled catalog source, and v2 plan/session export-import file
  handling. SQL is only allowed here.
- `src/training_feedback/ui/` — PySide6 pages and dialogs (no SQL).
- `src/training_feedback/app.py` / `bootstrap.py` / `main.py` — composition
  root, startup coordination, and the Qt entry point.
- `tests/` — pytest suite; always uses temporary databases.

## Package and install

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

The locally produced Setup.exe is currently unsigned. Windows may therefore
show an unknown-publisher warning; a trusted Authenticode certificate and
release signing step are still required before broad public distribution.

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
build a new Setup.exe, distribute it, then run it on the user's machine.

Packaged acceptance uses a synthetic fixture and a step-by-step runbook:

```powershell
pwsh -File packaging/prepare-acceptance-data.ps1 D:\TF-Acceptance
```

See [docs/packaged-acceptance-runbook.md](docs/packaged-acceptance-runbook.md).
The 0.7.0 directory build is a development candidate; content and independent
installer/upgrade/desktop acceptance remain open. See the
[release review and cleanup plan](docs/release-readiness-0.7.0.md).

## Documentation

- [Authoritative development plan](docs/development-plan.md)
- [Initial exercise catalog and plan proposal](docs/initial-exercises-and-plan.md)
- [Version retention and development-data policy](docs/development-plan.md#13-version-retention-and-development-data-policy)
- [Retained version history](docs/history/README.md)
