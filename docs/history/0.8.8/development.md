# 0.8.8 Development And Candidate Record

## Identity and event classification

- Application: `0.8.8`
- Database schema: `24`
- Catalog: `070-illustrated-3`
- Plan/evidence contract: `4`
- Events: updater-exit development update, application-version rotation, local
  installer candidate and GitHub Release distribution.

## Scope and diagnosis

User feedback on the in-app update from 0.8.6 to 0.8.7: the verified download
reached 100% but the application never exited and Setup never opened; closing
the application manually immediately released the waiting launcher and Setup
appeared. The detached launcher and its wait were therefore working. The
application's own exit depended on one zero-interval `quit` timer scheduled
after the handoff notification emit; any exception in that emit chain — silent
in the windowed client — skipped the quit, and even a scheduled normal quit
had no fallback. The exact reason the normal quit did not take effect on the
user's machine is not observable from code, so the exit is made structurally
redundant instead of dependent on one mechanism.

The normal quit and a 10-second hard-exit watchdog are now scheduled BEFORE
the handoff emit, and the emit is contained so notification failure cannot
affect the arranged exit. The watchdog arms only after the verified download
is complete and no user data write is in flight; the normal quit still closes
the context first, and SQLite WAL tolerates the hard exit. The handoff
instruction states that closing the application manually also opens the
installer — the launcher already supports that path. Schema 24, catalog
`070-illustrated-3`, contract 4, user text semantics and import compatibility
are unchanged.

## Verification

Concrete startup risk: `release_updates.py` is imported and the coordinator is
constructed on the startup path; an import, name or construction error in this
change could prevent the application from opening. Exactly one existing
isolated scenario was selected under scope `v0.8.8-update-exit`:

- `test_update_coordinator_does_not_block_main_window_startup` created a
  synthetic data root and update temporary root, constructed the coordinator
  without network and opened the main window. Result: **1 passed in 0.34 s**,
  with no rerun.

Ruff passed for the changed Python files, `packaging/check_docs.py` passed,
and `git diff --check` reported no whitespace errors beyond checkout
line-ending notices.

Download, handoff, exit, watchdog, launcher and installed-client behavior were
not run and are not passes. No other pytest node, script scenario, GUI
automation or real user root was used. Manual checks: **0**. The next in-app
update attempt remains the feedback channel.

## Candidate

The clean implementation commit `13e99547f4995b64ea18463a0c2a5491d76d461f`
was built on 2026-10-03 with Python 3.12.14 AMD64, PySide6 6.11.2,
PyInstaller 6.22.2, hooks 2026.7 and Inno Setup 6.7.3.

- Setup: `dist/installer/TrainingFeedback-0.8.8-Setup.exe`
- Bytes: `85,672,877`
- SHA-256: `bfbf1789b53d10f6aada0875c7395dcaf0493868a8a8f03b89b5119632c17207`
- Signature: unsigned (`NotSigned`); payload EXE also `NotSigned`
- Payload files: `298`
- Payload executable SHA-256:
  `9228a4dbcd608214a78b1f8b845955ef5c6b4597f4df3eb809ef55fe64606ad8`
- Source dirty: `false`
- Icon SHA-256: `3db199c1a7b7289fc4dbea91653952486431fe7072f7eb16ea7d90e51b99a65c`
  for `icon/`, source runtime and packaged runtime copies
- Manifests: [installer](installer-build-manifest.json) and
  [payload](payload-build-manifest.json)

The build verified the catalog and required packaged schema, contract and icon
resources, and found no user data in the payload. Building and manifest
inspection do not certify download, handoff, exit, watchdog, launcher or
installed behavior. GitHub distribution remains a separate event and does not
declare formal compatibility, public support, external content review,
personal-data transition or W4.
