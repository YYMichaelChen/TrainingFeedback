# Project Agent Rules

TrainingFeedback is a native PySide6 Windows application with its own SQLite
data root. The old `Exercises@home` repository is reference material only.

## Hard invariants

- Never discover, open, migrate or modify the old training database. Do not add
  Streamlit, wardrobe management, LAN/mobile access or old submission-package
  compatibility.
- Keep user data separate from application binaries. Tests and acceptance use
  isolated synthetic roots, never real user data.
- Preserve user text verbatim. Defaults are not user facts; unknown is not zero.
  Freeze facts needed to interpret completed sessions. Synthetic training and
  approvals never become personal facts.
- UI contains no SQL or business rules. A session controller owns training
  execution state. Writes completing one user action are transactional.
- `not run` is not `pass`. Candidate evidence certifies only its exact build.
  A local candidate does not establish public acceptance, external content
  review, W4 or personal-use readiness.

## Authority

| Question | Authoritative source |
| --- | --- |
| Product behavior, release gates, retention and personal transition | `docs/development-plan.md` |
| Proposed seed catalog | `docs/initial-exercises-and-plan.md` |
| Current application/schema implementation map and release history | `docs/history/README.md` and `docs/history/<version>/` |
| Development, local release, version rotation and release close procedure | `docs/development-workflow.md` |
| Pytest commands, tiers, scope and budget accounting | `tests/README.md` |
| Installed and public acceptance | `docs/packaged-acceptance-runbook.md` |
| Content review, personal transition and W4 procedure | `docs/guidance-review-runbook.md` |
| Active release execution state | `.planning/releases/<version>/PLAN.md`, projected into `.planning/INDEX.md` |

Tracked `docs/` owns requirements and formal evidence. Local Planscope owns
execution context. A PLAN task cannot change product policy; planning archives
are historical context and never override tracked requirements.

## Context routing and Planscope usage

- Micro edit: read the affected file; use `.planning/INDEX.md` only if release
  context might matter. Do not create planning noise.
- Normal development: read `INDEX.md`, the relevant active PLAN section and
  affected tracked requirements. Search `KNOWLEDGE.md` only for a relevant
  existing finding.
- Complex feature, migration or release: read `INDEX.md`, active PLAN current
  state and phase, relevant KNOWLEDGE sections and tracked requirements. Read
  `PROJECT.md` for a relevant cross-release decision only.
- Recovery: `INDEX.md` → PLAN current state → Git state → search KNOWLEDGE →
  recent LOG only if needed. Do not load archives or all planning files by default.
- `PLAN.md` owns the active phase, task, blockers and next action. After changing
  these, run the installed Planscope `plan.py sync`; do not hand-edit their INDEX
  projection. Keep one active release. Use KNOWLEDGE only for findings future
  work cannot reliably recover, and LOG only for recent recovery context.
- If `.planning/INDEX.md` is absent, the clone remains valid: use tracked docs
  and Git state. Initialize Planscope only when work warrants durable planning;
  never infer an active release from stale historical files. Keep `.planning/`
  local and its archives within the product's retention window.

## Engineering boundaries

- `src/training_feedback/domain/` contains pure rules; `application/` owns use
  cases; `data/` owns SQLite and root lifecycle; `ui/` owns PySide6. Startup is
  `main.py` → `bootstrap.py` → `app.py` → `ui/main_window.py`.
- Deliberate development exercises, guidance and illustrations belong in owned
  source and the built-in catalog before a development root is retired. Only
  the user can authorize the personal-data transition.
- Use PowerShell 7 for project commands and `apply_patch` for manual edits.

## Verification entry points

Do not use computer use, GUI automation, remote-control tools, scripted clicks
or keystrokes, or similar capabilities to directly test client functionality.
The developer must manually operate the client and record the results of client
checks, including installed acceptance. Automated code-level tests may still
run, but they do not substitute for manual client verification; report client
checks as `not run` until the developer provides their results.

Classify development, local installed acceptance, user-declared formal release,
explicit public release and application-version rotation by event. Follow `docs/development-workflow.md`
and `tests/README.md`; do not evade test-scope accounting. A normal code change
does not require an installer. A schema or external wire-schema revision requires
an application patch-or-greater bump in the same change. Before the user's
explicit formal-release declaration, old-version compatibility tests and
support promises are disabled. Afterwards, support the user-selected one or
two predecessor formal versions and verify their upgrade paths. Reject
unsupported/future roots unchanged before writes. Reinstall does not reset a
data root; v0.8.0's explicitly confirmed uninstall deletion follows the
narrow path rules in the development plan.

## Task completion report

Report changed files, actual verification and unrun checks, application/schema/
catalog/contract impact, candidate limits, and Planscope state changes when used.
