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

To create the current Windows smoke-test executable after installing PyInstaller, run:

```powershell
pyinstaller --clean --noconfirm packaging/training_feedback.spec
```

The executable is written to `dist/TrainingFeedback.exe`. The directory-based
release layout remains Phase 8 work.

## Documentation

- [Authoritative development plan](docs/development-plan.md)
- [Initial exercise catalog and plan proposal](docs/initial-exercises-and-plan.md)
- [Phase 0 and Phase 1 implementation design](docs/phase-0-and-1-implementation.md)
- [Phase 2 and Phase 3 implementation design](docs/phase-2-and-3-implementation.md)
