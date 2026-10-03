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

The clean implementation commit `ccb47bd09e33807807ed28eedc863bbf4b172b2f`
was built on 2026-10-03 with Python 3.12.14 AMD64, PySide6 6.11.2,
PyInstaller 6.22.2, hooks 2026.7 and Inno Setup 6.7.3.

- Setup: `dist/installer/TrainingFeedback-0.8.6-Setup.exe`
- Bytes: `85,664,463`
- SHA-256: `06120b97244ab24a745a429617e04abdbe50f7b0057086cf050f64158b89e61c`
- Signature: unsigned (`NotSigned`); payload EXE also `NotSigned`
- Payload files: `298`
- Payload executable SHA-256:
  `e3ebc0f84d0ea4443cf3699dadefef17e9ca3cc449e5da13a7a023adc3d8afd0`
- Source dirty: `false`
- Manifests: [installer](installer-build-manifest.json) and
  [payload](payload-build-manifest.json)

The build verified the catalog and required packaged schema, contract and icon
resources, and found no user data in the payload. Building and manifest
inspection do not certify stale-directory selection, deletion, Setup waiting,
post-install cleanup or installed behavior. GitHub distribution remains a
separate event and does not declare formal compatibility, public support,
external content review, personal-data transition or W4.
