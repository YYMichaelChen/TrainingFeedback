# 0.8.6 Development And Candidate Record

## Identity and event classification

- Application: `0.8.6`
- Database schema: `24`
- Catalog: `070-illustrated-3`
- Plan/evidence contract: `4`
- Events: updater cleanup development update, application-version rotation,
  local installer candidate and GitHub Release distribution.

## Scope and diagnosis

Before v0.8.6, a successful handoff intentionally retained its unique temporary
directory so Setup would still exist after the client exited. The PowerShell
launcher did not wait for Setup completion and therefore had no safe point at
which to remove the package. This also meant that the package used to install a
new version remained after that version first opened.

The launcher now uses PowerShell's process-tree wait and removes its exact
download directory in `finally`. New directories carry an ownership marker.
Startup recovery recognizes only direct, non-link `TrainingFeedback-update-`
directories with the exact random-name shape and complete contents limited to
the marker and semantic-version Setup `.exe`/`.part` names. This permits strict
legacy cleanup without treating a name prefix as authority to delete arbitrary
temporary content. Cleanup is best-effort and never reaches a data root.

## Verification

Concrete startup risk: coordinator construction now performs stale-artifact
cleanup before the main window opens; an uncaught import, path or filesystem
error could prevent the application from opening. Exactly one existing isolated
scenario was selected under scope `v086-update-cleanup`:

- `test_update_coordinator_does_not_block_main_window_startup` injected an empty
  synthetic update temporary root, constructed the coordinator and synthetic
  data root, then created the main window without network access. Result:
  **1 passed in 0.35 s**, with no rerun.

Ruff passed for the changed Python files, `packaging/check_docs.py` passed for
73 Markdown files, and `git diff --check` reported no whitespace errors beyond
checkout line-ending notices.

Updater selection/deletion behavior, launcher waiting, Setup execution,
post-install cleanup and installed-client behavior will not be run and will not
be recorded as passes. No other pytest node, script scenario, GUI automation,
real update directory or real user root was used. Manual checks: **0**.

## Candidate

No candidate has been built yet. This section will identify the exact clean
source commit, toolchain, payload and Setup after construction.
