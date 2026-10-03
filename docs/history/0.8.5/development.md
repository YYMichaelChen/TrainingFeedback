# 0.8.5 Development And Candidate Record

## Identity and event classification

- Application: `0.8.5`
- Database schema: `24`
- Catalog: `070-illustrated-3`
- Plan/evidence contract: `4`
- Events: emergency development update, application-version rotation, local
  installer candidate and GitHub Release distribution.

## Scope and diagnosis

The [user screenshot](evidence/user-update-feedback-2026-10-03.png) shows the
download progress percentage clipped by the shared eight-pixel progress-bar
maximum. The updater now gives only `updateDownloadProgress` a 22-pixel height,
leaving other progress bars unchanged.

The prior updater started Setup before asking Qt to quit. Setup could therefore
attempt an overwrite while the client still owned installed files. After exact
size and SHA-256 validation, v0.8.5 instead starts a detached system PowerShell
handoff with the current PID and verified temporary Setup path in environment
variables. The handoff waits until the current process disappears and only then
starts Setup. The normal shutdown closes the selected data-root context before
process exit. Failure to locate or start the handoff keeps the client open and
preserves retry and browser-download choices.

No schema, catalog, wire contract, user text or user data changes. The screenshot
and report are defect input only and do not certify the corrected behavior.

## Verification

Concrete startup risk: `main.py` imports the changed updater module before it
can construct the main window, and that module now requires
`QProcessEnvironment`. A missing Qt symbol, invalid import or syntax error could
prevent the application from opening. Exactly one existing isolated scenario
was selected under scope `v085-updater-handoff`:

- `test_required_application_icon_is_loaded_and_assigned_to_main_window`
  imported the startup UI path, created a synthetic root and constructed a main
  window. Result: **1 passed in 0.34 s**, with no rerun.

Ruff passed for the changed Python files and `git diff --check` reported no
whitespace errors beyond checkout line-ending notices. The first documentation
check failed only because this required `docs/history/0.8.5/` destination did
not yet exist; it was created before rerunning that same check.

No other pytest node, script scenario, GUI automation, real user root or client
operation was used. Download progress rendering, verified-download handoff,
client exit, installer start, overwrite installation and installed-client
behavior were not run and are not passes. Manual checks: **0**.

## Candidate

The clean implementation commit `749b6a306572eed191d268ca1cfa54169842a60e`
was built on 2026-10-03 with Python 3.12.14 AMD64, PySide6 6.11.2,
PyInstaller 6.22.2, hooks 2026.7 and Inno Setup 6.7.3.

- Setup: `dist/installer/TrainingFeedback-0.8.5-Setup.exe`
- Bytes: `85,665,376`
- SHA-256: `37658f63ce49535f73ac56fef7d186495982aeecd38e5d559afe3b26cd5dc9e0`
- Signature: unsigned (`NotSigned`); payload EXE also `NotSigned`
- Payload files: `298`
- Payload executable SHA-256:
  `ccc7c7e1cad8b7bd0f4348dde6dd2e695b3e81e08f3d1926b6c34c361102593d`
- Source dirty: `false`
- Manifests: [installer](installer-build-manifest.json) and
  [payload](payload-build-manifest.json)

The build verified the catalog and required packaged schema, contract and icon
resources, and found no user data in the payload. Building and manifest
inspection do not certify visible progress, updater handoff, process exit,
installer launch or installed behavior. GitHub distribution remains a separate
event and does not declare a formal compatibility baseline, public support,
external content review, personal-data transition or W4.
