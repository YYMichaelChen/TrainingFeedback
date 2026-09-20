# 0.6.0 Development Record

Archived: 2026-09-20. Database baseline: schema 14; plan/evidence contract: v1.
Current requirements: [development plan](../../development-plan.md).

## Completed scope

- Native workflow/palette refinement, focused home/history, safer per-set editing
  and fixed result/session controls.
- Schema 14 adds audited `session_result_retraction`; original result, actual
  sets and note survive retraction, with additive evidence-v1 fields and no backfill.
- Runtime and packaging application versions were aligned. Older exports identify
  their schema rather than a binary version and are not rewritten retrospectively.

## Candidate-specific checks

- Phase C (2026-09-14) on isolated copies covered schema 13 → 14, preserved rows,
  cross-process pause/resume, all four results, retraction, finish/abort, unanswered
  feedback, JSON/Markdown agreement and equal backup/reopened history.
- Local Windows rendering used DPR 2.25 at 1707×960 logical pixels. Offscreen Qt
  lacked Chinese glyphs; this did not establish real-desktop acceptance.
- The separately approved local-root upgrade preserved old rows/resources through
  before/after/restart checks, passed integrity/FK checks and left the retraction
  table empty. The exercised session was simulated, not W4 evidence.
- The preserved precommit manifest has `source_dirty=true`, base `fb593ef`;
  source tag `v0.6.0` points to `072c931`. Tag identity must not replace the actual
  manifest/source snapshot identity.

The [archived packaged procedure](packaged-acceptance-runbook.md) contains its
original, unexecuted independent matrix. References there to earlier programs
explain that candidate's proposed checks; they are not the current compatibility
window. W4, content review and independent acceptance were not closed by these
local checks. Full details for pre-0.6.0 development no longer belong in the
active plan or this three-version archive; tracked history remains in Git.
