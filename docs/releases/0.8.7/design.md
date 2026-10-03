# 0.8.7 Navigation Failure Containment Design

## Identity

- Application version: `0.8.7`
- Database schema: `24`
- Catalog: `070-illustrated-3`
- Plan and evidence wire contracts: `4`
- Previous distributed version: `0.8.6` / schema `24` / contract `4`

The implementation and clean local candidate are recorded in the
[0.8.7 development record](../../history/0.8.7/development.md), and the Setup is
distributed through [GitHub Release v0.8.7](../../history/0.8.7/github-release-2026-10-03.md).

GitHub Release distribution is part of this update, but remains separate from a
formal compatibility baseline, public-support commitment, external content
review, personal-data transition or W4.

## Scope And Safety Boundary

User feedback on a clean-installed 0.8.6: selecting 动作库 in the navigation
highlights the entry but the previously visible page remains on screen with no
message. In current code the stacked-widget switch happens after the target
page is constructed inside the navigation slot; any exception raised by page
construction (including the first lazy import of its module) escapes the slot
silently in the windowed client, leaving the navigation selection and the
visible page permanently diverged with zero feedback. The 0.8.4 progressive
loading change contained only refresh-time failures, not construction-time
ones.

- Contain page creation in `MainWindow._show_page`: when a page factory
  raises, substitute a visible error page showing the page name and the error
  text (selectable for feedback), switch to it so the visible page always
  matches the navigation selection, and do not mark the index as built so the
  next entry retries creation. The containment path reads and writes no user
  data and adds no SQL or business rules to the UI layer.
- Schedule the library page's first progressive refresh only after the page
  has painted once (`paintEvent`), so the loading state becomes visible before
  heavy reading begins; a zero-interval timer can fire before the first paint,
  leaving the previous page's pixels on screen during a slow first load.
- Normal page creation, progressive per-card loading, refresh, cancellation
  and retry-after-leaving behavior are otherwise unchanged.
- Rotate application and implementation-history identity to 0.8.7. Do not
  change schema 24, catalog `070-illustrated-3`, contract 4, user text
  semantics, user data or import compatibility.

## Verification And Delivery Boundary

`main_window.py` and `labels.py` are imported and constructed on the startup
path; an import or construction error in this change would prevent the
application from opening. Select exactly one existing startup-construction
scenario (synthetic root, construct the main window) and stop when it passes.
Navigation behavior, the substituted error page and installed-client behavior
receive no functional or GUI-automated scenarios under the current policy; the
contained error message is the feedback channel for the next user report.

Ruff, documentation consistency and diff checks may be run without counting as
functional coverage. Manual checks are zero. Do not inspect or modify real user
data, operate an installed client, launch Setup or claim unobserved client
behavior passed.

Build a clean 0.8.7 Setup and publish stable GitHub Release `v0.8.7` with
exactly one `TrainingFeedback-0.8.7-Setup.exe`. Record the exact source,
toolchain, asset size, SHA-256, GitHub digest and evidence limits in
`docs/history/0.8.7/`.

The active execution plan is `.planning/releases/v0.8.7/PLAN.md`. Product
policy remains governed by [`development-plan.md`](../../development-plan.md),
and the event-specific procedure by
[`development-workflow.md`](../../development-workflow.md).
