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
python -m pytest --basetemp .tmp/pytest
python -m ruff check src tests
```

## Project layout

- `src/training_feedback/domain/` — pure business rules and value objects (no
  Qt, no SQL).
- `src/training_feedback/application/` — use-case services coordinating domain
  workflows and repositories.
- `src/training_feedback/data/` — SQLite repositories, schema migrations, data
  root lifecycle, backup and handoff facades, seed catalog, and export/import
  file handling. SQL is only allowed here.
- `src/training_feedback/ui/` — PySide6 pages and dialogs (no SQL).
- `src/training_feedback/app.py` / `bootstrap.py` / `main.py` — composition
  root, startup coordination, and the Qt entry point.
- `tests/` — pytest suite; always uses temporary databases.

## Package

The Windows build produces a portable directory layout. The verified build
environment and pinned toolchain are recorded in
`packaging/requirements-build.txt`; with those installed, run:

```powershell
pwsh -File packaging/build.ps1
```

The entry point is `dist/TrainingFeedback/TrainingFeedback.exe`; move or copy
the whole `dist/TrainingFeedback/` directory together. User data always lives
in the separately chosen data root, never in the program directory.
Independent-machine acceptance of the packaged build remains Phase 8 work.

## Documentation

- [Authoritative development plan](docs/development-plan.md)
- [Initial exercise catalog and plan proposal](docs/initial-exercises-and-plan.md)
