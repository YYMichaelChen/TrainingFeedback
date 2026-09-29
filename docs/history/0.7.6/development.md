# 0.7.6 Development

## Objective

Clarify documentation ownership and Planscope routing without changing
application behavior, schema, bundled catalog content or wire contracts.

## Version identity

- Application version: `0.7.6`.
- Database schema: `23` (unchanged).
- Schema 22 remains the retained 0.7.4 root baseline; the existing guarded
  schema 22 reset behavior from 0.7.5 is unchanged.
- Catalog: `070-illustrated-3` (unchanged).
- Plan and evidence wire contracts: version 3 (unchanged).
- Supported window: application 0.7.6 / schema 23, 0.7.5 / schema 23, and
  0.7.4 / schema 22.

## Delivered

- Routed product requirements, seed content, development and release procedure,
  pytest accounting, installed acceptance, content-review gates, version
  history, and local Planscope execution context to their authoritative files.
- Moved the former 0.7.3 tracked history and local planning records to the
  ignored local `docs/archive/0.7.3/` holding area as the three-version window
  rotated. Their Git history remains intact.
- Kept the 0.7.7 new-root directory creation change deferred; opening an
  existing valid root remains a direct selection.

## Verification

- Documentation local-link and heading checks: pass for the changed workflow,
  history index and 0.7.6 development record; version-window/status assertions
  also pass.
- Planscope compact and doctor: pass; all planning files are within budget,
  INDEX pointers match, and doctor reports 0 failures and 0 warnings.
- Pytest version-boundary checks: 12/12 passed from `tests/test_data_root.py`
  and `tests/test_one_time_reset.py` under the single `dev` scope
  `v076-update` (12/30 unique cases).
- Ruff: pass for `src/training_feedback/__init__.py` and
  `src/training_feedback/data/migrations.py`.
- `git diff --check`: pass.
- Version identity assertions: pass for application `0.7.6`, schema 23 and
  supported map; plan and evidence wire contracts remain version 3.
- Installed client acceptance: not run; no installer candidate was created.

This is a development record, not public-release acceptance, external content
review, W4 evidence or personal-use readiness.
