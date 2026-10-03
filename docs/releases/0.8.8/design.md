# 0.8.8 Update Exit Hardening Design

## Identity

- Application version: `0.8.8`
- Database schema: `24`
- Catalog: `070-illustrated-3`
- Plan and evidence wire contracts: `4`
- Previous distributed version: `0.8.7` / schema `24` / contract `4`

The implementation and clean local candidate are recorded in the
[0.8.8 development record](../../history/0.8.8/development.md), and the Setup is
distributed through [GitHub Release v0.8.8](../../history/0.8.8/github-release-2026-10-03.md).

GitHub Release distribution is part of this update, but remains separate from a
formal compatibility baseline, public-support commitment, external content
review, personal-data transition or W4.

## Scope And Safety Boundary

User feedback on the in-app update from 0.8.6 to 0.8.7: the verified download
reached 100% but the application never exited and Setup never opened; closing
the application manually immediately released the waiting launcher and Setup
appeared. The detached launcher and its wait were therefore working, but the
application's own exit depended on a single zero-interval `quit` timer that
was scheduled only after the handoff notification emit. Any exception in that
emit chain — silent in the windowed client — skipped the quit entirely, and
even a scheduled normal quit had no fallback.

- Schedule the normal quit and a hard-exit watchdog BEFORE emitting the
  handoff notification, and contain the emit: notification failure can no
  longer affect the arranged exit.
- The watchdog hard-exits the process after 10 seconds if the normal quit did
  not end it. It arms only after the verified download is complete and no user
  data write is in flight; the normal quit path still closes the context
  cleanly first, and SQLite WAL tolerates the hard exit.
- The handoff instruction now states that if the application does not exit,
  closing it manually still opens the installer automatically — the launcher
  already supports this, as the user demonstrated.
- Download, verification, temporary-directory and launcher behavior are
  unchanged. Rotate application and implementation-history identity to 0.8.8.
  Do not change schema 24, catalog `070-illustrated-3`, contract 4, user text
  semantics, user data or import compatibility.

## Verification And Delivery Boundary

`release_updates.py` is imported and the coordinator is constructed on the
startup path; an import or construction error in this change would prevent the
application from opening. Select exactly one existing startup scenario
(synthetic roots, construct the coordinator and the main window without
network) and stop when it passes. Download, handoff, exit, launcher and
installed-client behavior receive no functional or GUI-automated scenarios
under the current policy; the next in-app update attempt is the feedback
channel.

Ruff, documentation consistency and diff checks may be run without counting as
functional coverage. Manual checks are zero. Do not inspect or modify real user
data, operate an installed client, launch Setup or claim unobserved client
behavior passed.

Build a clean 0.8.8 Setup and publish stable GitHub Release `v0.8.8` with
exactly one `TrainingFeedback-0.8.8-Setup.exe`. Record the exact source,
toolchain, asset size, SHA-256, GitHub digest and evidence limits in
`docs/history/0.8.8/`.

The active execution plan is `.planning/releases/v0.8.8/PLAN.md`. Product
policy remains governed by [`development-plan.md`](../../development-plan.md),
and the event-specific procedure by
[`development-workflow.md`](../../development-workflow.md).
