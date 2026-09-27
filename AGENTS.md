# Project Rules

TrainingFeedback is a native PySide6 desktop application for Windows, with its
own SQLite data root. The old `Exercises@home` repository is reference material,
never a runtime dependency or a database source.

## Authority and workflow

- `docs/development-plan.md` owns product behavior, release boundaries and
  retention policy; `docs/initial-exercises-and-plan.md` owns the proposed seed
  catalog. Do not duplicate their specifications in README or source comments.
- `docs/development-workflow.md` is the single version-independent development
  and delivery procedure. `docs/packaged-acceptance-runbook.md` supplies installed
  and public-release checks; `tests/README.md` supplies pytest command details.
- `docs/history/README.md` is the current human-readable application/schema
  support map. Version-specific completed work and candidate evidence belong in
  version history or candidate-specific local artifacts, not in this file.
- Classify work by event: development, local release/installed acceptance,
  explicit public release, and application-version rotation. A normal code change
  does not require an installer. Do not mark deferred or unrun checks as passed.

## Product and data boundaries

- Never discover, open, migrate or modify the old training database. Do not add
  Streamlit, wardrobe management, LAN/mobile access or old submission-package
  compatibility.
- Preserve user text verbatim; defaults are not user facts. Freeze plan and
  exercise facts needed to interpret completed sessions so later catalog edits
  cannot rewrite history.
- New or revised development exercises, guidance and illustrations belong in
  owned source and the built-in catalog. Reconcile deliberate development content
  before retiring a development root. Never promote synthetic approvals/training
  to personal facts. Only the user can authorize the later personal-data transition.
- A local release requires complete candidate content, bounded regression,
  reproducible source and verified installer/installed checks. Independent
  Windows acceptance and public-distribution gates start only on an explicit
  public-release request. External content review and W4 are separate follow-ups;
  local release establishes neither of them nor personal-use readiness.

## Engineering boundaries

- Keep UI, domain workflow and SQLite access separate. UI contains no SQL or
  business rules; a session controller owns training execution state. Writes
  completing one user action are transactional.
- Keep user data separate from application binaries. Tests use temporary roots,
  never real user data.
- Use PowerShell 7 for project commands on Windows and `apply_patch` for manual
  file edits.
- Layout: `src/training_feedback/domain/` for pure rules,
  `application/` for use cases, `data/` for SQLite and root lifecycle, `ui/` for
  PySide6. Startup follows `main.py` → `bootstrap.py` → `app.py` →
  `ui/main_window.py`.

## Version and verification invariants

- Retain complete development material and migration entry support for the
  current application version plus two predecessors. Same-version commits take
  one slot. A schema or external wire-schema revision requires an application
  patch-or-greater bump in the same change. Preserve retained upgrades and reject
  expired roots unchanged before writes; reinstall does not reset a data root.
- Pytest limits on parameter-expanded cases are dev 30, patch 50, minor 100,
  major 300; resident suite at most 300. Use one stable `--test-scope` and tier for
  a task or release, counting unique cases across commands. Never reset/split
  scopes, hide cases or loop independent scenarios to evade a cap. `--collect-only`
  does not execute or reserve cases. Run affected cases, then stop once relevant
  checks pass; rerun failed/affected cases after a fix.

## Planning context

- Use the installed `planscope` skill for work that needs durable planning context.
  Its entry point is `.planning/INDEX.md`; load only the relevant active release
  sections. Small local changes may skip planning unless they change release state
  or stable project constraints.
- Keep one active release at most. `PLAN.md` owns its current state; run the
  planscope `sync` command after changing that state. Use `KNOWLEDGE.md` only for
  findings future work cannot reliably recover from source, and `LOG.md` only
  for recent recovery context. Product decisions and release policy remain under
  `docs/`.
- Keep planning archives within the three-application-version window in the
  development plan. Historical legacy task records are read-only evidence; do
  not load them as active context or duplicate them in new plans.
