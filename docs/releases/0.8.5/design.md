# 0.8.5 Emergency Updater Correction Design

## Identity

- Application version: `0.8.5`
- Database schema: `24`
- Catalog: `070-illustrated-3`
- Plan and evidence wire contracts: `4`
- Previous distributed version: `0.8.4` / schema `24` / contract `4`

The implementation and clean local candidate are recorded in the
[0.8.5 development record](../../history/0.8.5/development.md), and the Setup is
distributed through [GitHub Release v0.8.5](../../history/0.8.5/github-release-2026-10-03.md).

GitHub Release distribution is part of this update, but remains separate from a
formal compatibility baseline, public-support commitment, external content
review, personal-data transition or W4.

## User Feedback And Cause

The [user-provided 2026-10-03 screenshot](../../history/0.8.5/evidence/user-update-feedback-2026-10-03.png)
shows the update download bar rendered at the theme's eight-pixel maximum height
while its percentage text requires the normal font height. The text is therefore
clipped rather than providing a complete progress indication.

The 0.8.4 updater starts Setup with `QProcess.startDetached()` before requesting
Qt application shutdown. Setup can begin its overwrite while the running client
still owns installed files, so the installer's close-app option does not prevent
an immediate in-use failure. The screenshot and report are defect input only;
they do not certify this correction.

## Scope

- Give only the updater's download progress bar enough fixed height for its
  percentage text, while retaining the compact shared progress style elsewhere.
- After exact size and SHA-256 validation, start a detached system PowerShell
  handoff that waits for the current process ID to disappear and then launches
  the verified Setup from its unique temporary directory.
- Exit only after that handoff starts successfully. If the system launcher is
  absent or cannot start, preserve the existing retry and browser-download
  choices and do not execute Setup.
- Update user-facing text so it accurately states the order: download, verify,
  exit the current client, then open Setup.
- Rotate application and implementation-history identity to 0.8.5. Do not
  change schema 24, catalog `070-illustrated-3`, contract 4, user data or import
  compatibility.

The selected data root is not read or written by this flow. The normal main
shutdown closes the current context before the process exits; the detached
launcher waits for full process exit before allowing Setup to begin.

## Verification And Delivery Boundary

The startup entry imports the changed updater module before constructing the
main window. Select exactly one existing isolated startup scenario to catch an
invalid required Qt import or module-load failure, then stop when it passes.
Progress rendering and installer sequencing are UI/update behavior and receive
no functional or GUI-automated scenarios under the current policy.

Ruff, documentation consistency and diff checks may be run without counting as
functional coverage. Manual checks are zero. Do not operate an installed client,
launch Setup, use real user data or claim unobserved Windows behavior passed.

Build a clean 0.8.5 Setup and publish stable GitHub Release `v0.8.5` with exactly
one `TrainingFeedback-0.8.5-Setup.exe`. Record the exact source, toolchain, asset
size, SHA-256, GitHub digest and evidence limits in `docs/history/0.8.5/`.

The active execution plan is `.planning/releases/v0.8.5/PLAN.md`. Product policy
remains governed by [`development-plan.md`](../../development-plan.md), and the
event-specific procedure by [`development-workflow.md`](../../development-workflow.md).
