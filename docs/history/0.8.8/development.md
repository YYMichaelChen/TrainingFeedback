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

The clean implementation commit and candidate identity will be recorded here
after the build, together with the installer and payload manifests.

GitHub distribution remains a separate event and does not declare formal
compatibility, public support, external content review, personal-data
transition or W4.
