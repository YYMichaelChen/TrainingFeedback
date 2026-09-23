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
- The project is in development: new/revised exercises, guidance and intended
  illustrations belong in owned source and the built-in catalog under current
  rules. Reconcile deliberate development content before retiring old roots.
  The user explicitly authorizes the later personal-data transition; never promote
  synthetic approvals/training to personal facts.

## Local And Public Release Boundaries

- Follow `docs/development-plan.md` Sections 9–10 (user decision 2026-09-23).
- Local release requires content closeout, repaired/budgeted regression, complete
  reproducible source and a verified installer with local installed checks.
- 070-H3 / 8-B2 independent Windows acceptance and public-distribution requirements
  are deferred until the user explicitly requests a public release. Do not make
  them local-release blockers or mark deferred checks as passed.
- W4 and external content review are separate unfinished follow-ups, not local
  release gates. Local release does not establish a personal-data transition,
  expert approval, plan activation or genuine training facts.

## Engineering Boundaries

- Keep UI, domain workflow, and SQLite access in separate layers.
- UI code must not contain SQL.
- A session controller owns training execution state.
- Database writes that complete one user action must be transactional.
- User data and application binaries must remain in separate directories.
- Tests use temporary databases and must never access real user data.
- Use PowerShell 7 for project commands on Windows.
- Use `apply_patch` for manual file edits.

## Version And Retention Rules

- Follow `docs/development-plan.md` section 13. Retain complete development
  documents, schema/contract baselines and migration entry support for the current
  application version plus two predecessors. Same-version commits use one slot.
- Current window: 0.7.0/schema22, 0.6.1/schema16, 0.6.0/schema14. Every subsequent
  schema revision requires at least an application patch bump in the same change;
  do not append more schemas under 0.7.0. Existing intermediate numbers are historical.
- Preserve applied migrations while supported endpoints need them; prune expired
  entry paths together with fixtures and consolidate fresh initialization without
  breaking retained upgrades. Three-version enforcement is implemented (070-R2,
  2026-09-21): roots below schema14 are refused read-only before writes, with
  reinstall/new-empty-root guidance; retained endpoints upgrade via the normal
  migration chain.
- Expired development roots must be rejected before writes, with reinstall/new-empty-
  root guidance. Preserve old data; program reinstall alone does not reset a root.
- Archive completed material by application version, then remove expired complete
  records at rotation. Archives are subject to the same window; Git history stays.

## Test Budgets

- Follow the verification policy in `docs/development-plan.md` section 9.4.
- Hard caps on parameter-expanded pytest cases: development step 30, patch
  release 50, minor release 100, major release 300. The resident suite is at most 300.
- Use `--test-tier dev|patch|minor|major` and a stable `--test-scope TASK-ID`.
  All commands for one step/release share that scope; their unique cases count
  together. Never split commands, reset ledgers, or change scopes/tiers to evade a cap.
- For a small change, explicitly select affected test nodes/files or `-k` cases.
  Bare pytest selects the small dev smoke profile, not a full regression.
- `--collect-only` inventories cases without running tests or consuming budget.
  Parameter combinations count separately. Do not hide cases with skip/collection
  exclusions or move independent scenarios into loops to lower the count.
- Add a test only for a meaningful new risk or reproduced bug; first check existing
  coverage. Remove redundant coverage when adding cases near the resident cap.
- After relevant tests pass, stop. Following a fix, rerun only failed/affected
  cases; do not automatically append a full-suite run.

## Project Layout

- `domain/` — pure rules and value objects (no Qt, no SQL).
- `application/` — use-case services (`LibraryWorkflowService`,
  `GroupPlanService`, `GroupSessionService`, `LibraryLifecycleService`)
  coordinating domain rules and repositories; write operations open their
  transaction here or inside one repository method.
- `data/` — repositories per table family (`library_repository`,
  `catalog_repository`, `group_plan_repository`, `group_session_repository`,
  `library_lifecycle_repository`, `conversion_repository`), `migrations.py`
  (versioned migrations retained for supported endpoints), `database.py` (connection +
  `transaction()` boundary), `data_root.py`, `locator.py`, `backup.py`,
  `upgrade_recovery.py` + `catalog_conversion.py` (one-time schema-16 root
  conversion), `group_plan_handoff.py` / `group_session_handoff.py` (v2
  export/import incl. Markdown rendering), `seed/` (bundled catalog source for
  the catalog builder).
- `ui/` — PySide6 pages and dialogs; Chinese display labels live in
  `ui/labels.py` (including `make_unit_combo`); no SQL, no business rules.
- Entry chain: `main.py` → `bootstrap.py` → `app.py` (`LibraryContext`,
  `DataRootSwitcher`) → `ui/main_window.py`.

## Documentation

- `docs/development-plan.md` is the authoritative product scope, domain model,
  and delivery plan.
- `docs/initial-exercises-and-plan.md` is the authoritative seed catalog and
  initial-plan proposal until real use or an external AI expert revises it.
- Avoid duplicating those specifications in the README or source comments.
- `docs/release-readiness-0.7.0.md` records the current review, ordered closeout and
  workspace cleanup tasks. `docs/history/README.md` indexes retained version history;
  expired versions move from the tracked `docs/history/<version>/` to the untracked
  local `docs/archive/` holding area.

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
  `.planning/archive/<application-version>/` before new content is added. Apply
  the same three-version window; do not accumulate an unlimited second archive.
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
