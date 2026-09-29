# 0.7.7 Development And Candidate Record

## Identities and event

- Event: new-root development, application-version rotation, and requested local
  candidate/installed acceptance.
- Application `0.7.7`; database schema `23`; bundled catalog
  `070-illustrated-3`; plan and evidence contracts v3.
- Retained application versions: `0.7.7`, `0.7.6`, `0.7.5`, all schema 23.
  Schema 22 opening is expired and read-only; schema 23 cleanup recovery remains.

## Verification selection before first execution

One `patch` scope, `release-0.7.7`, at most 50 unique parameter-expanded pytest
cases. Material risks: Windows child-name validation, redirected Documents,
mode/preview/cancel behavior, child states, creation rollback, locator/window
commit, retained direct open, expired/future refusal, and committed journal
recovery. Collection inventory: exactly 48 parameter-expanded node IDs across
`tests/test_new_root.py` (25), `tests/test_one_time_reset.py` (2),
`tests/test_bootstrap.py` (5), `tests/test_root_switch.py` (8), and
`tests/test_data_root.py` (8). All nodes in those five files were selected for
the single `release-0.7.7` patch execution. Two further material failure-stage
nodes in `test_new_root.py` were reserved after adding library and context
construction rollback injection, for 50 unique cases total. Collection with the default dev
tier reported its 30-case ceiling and reserved no cases; the patch scope is the
first execution scope.
Broader plan authoring, training, import/export, and content cases are excluded
because their behavior and contracts are unchanged. Excluded cases are not passes.

## Results

- Source verification: 50 unique selected cases reserved; initial run 45 pass,
  3 fail; the 3 failed cases passed after fixture corrections. The two added
  failure-stage cases passed; affected root-switch cases passed after path
  handling adjustment, and affected creation cases passed after error handling
  correction. All 50 selected cases have a pass for the final source.
  Ruff changed Python areas and `git diff --check` passed.
- Candidate build and manifest: clean candidate `831f7ed`; see
  [local candidate](local-candidate.md). An earlier build from `154fce4`
  preceded the access-error correction and had no installed client checks; it
  is superseded and carries no acceptance result.
- Developer-operated installed client checks: `not run`.
- Independent public acceptance: `not run` (not requested).
- External content review, W4, and personal-use readiness: `not run`.
