# Project Rules

This repository contains the new TrainingFeedback desktop application. The old
`Exercises@home` repository is reference material only and is never a runtime
dependency.

## Product Boundaries

- Build a native PySide6 desktop application for Windows.
- Use a new SQLite database owned by this application.
- Never discover, open, migrate, or modify the old training database.
- Do not add Streamlit, wardrobe management, LAN access, mobile access, or old
  submission-package compatibility.
- Preserve user-entered text verbatim and never turn defaults into user facts.
- Freeze plan and exercise facts needed to interpret completed sessions; later
  catalog edits must not rewrite history.

## Engineering Boundaries

- Keep UI, domain workflow, and SQLite access in separate layers.
- UI code must not contain SQL.
- A session controller owns training execution state.
- Database writes that complete one user action must be transactional.
- User data and application binaries must remain in separate directories.
- Tests use temporary databases and must never access real user data.
- Use PowerShell 7 for project commands on Windows.
- Use `apply_patch` for manual file edits.

## Project Layout

- `domain/` — pure rules and value objects (no Qt, no SQL).
- `application/` — use-case services (`TrainingApplicationService`,
  `ExerciseService`) coordinating domain rules and repositories; write
  operations open their transaction here or inside one repository method.
- `data/` — repositories per table family (`exercise_repositories`,
  `plan_repositories`, `session_repositories`, `feedback_repositories`),
  `migrations.py` (append-only versioned migrations), `database.py`
  (connection + `transaction()` boundary), `data_root.py`, `locator.py`,
  `backup.py`, `handoff.py` (export/import facade incl. Markdown rendering),
  `seed/` (initial catalog and plan proposal).
- `ui/` — PySide6 pages and dialogs; Chinese display labels live in
  `ui/labels.py` (including `make_unit_combo`); no SQL, no business rules.
- Entry chain: `main.py` → `bootstrap.py` → `app.py` (`ApplicationContext`) →
  `ui/main_window.py`.

## Documentation

- `docs/development-plan.md` is the authoritative product scope, domain model,
  and delivery plan.
- `docs/initial-exercises-and-plan.md` is the authoritative seed catalog and
  initial-plan proposal until real use or an external AI expert revises it.
- Avoid duplicating those specifications in the README or source comments.

## Development Records

- Every development task must update `task_plan.md`, `findings.md`, and
  `progress.md` before the task is considered complete.
- `task_plan.md` records scope, status, decisions, and errors.
- `findings.md` records relevant discoveries, constraints, and implementation
  observations.
- `progress.md` records work performed, verification commands, and results.
- If any of these files is missing when development begins, create it before
  making implementation changes.
- These records are not product specifications; product decisions belong in the
  authoritative files under `docs/`.

### Record Hygiene

- The three root files represent the current task, not an unbounded project
  history.
- When a new task starts, completed task records must be summarized or moved to
  `.planning/archive/` before new content is added.
- `task_plan.md` must contain only the active task plan, current decisions,
  current risks, and relevant errors. It must not accumulate completed task
  plans.
- `findings.md` must contain deduplicated, currently valid findings. Each
  finding should state the fact, its evidence or source, and its implementation
  impact when those details matter.
- `progress.md` must contain concise session summaries, verification commands,
  results, blockers, and next steps. Do not paste complete tool output or
  repetitive command logs into it.
- Resolved errors must be condensed into a reusable constraint or removed when
  no longer useful. Repeated facts must be merged rather than appended.
- Keep the root records within these soft limits: `task_plan.md` 150 lines,
  `findings.md` 250 lines, and `progress.md` 200 lines. Reorganize or archive
  content before exceeding a limit.
- A development task is not complete until the three files have been reviewed
  for duplication, stale entries, and unnecessary history.
