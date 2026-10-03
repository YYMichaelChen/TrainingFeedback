# 0.8.10 Illustration Layout And Update Exit Design

## Identity

- Application version: `0.8.10`
- Database schema: `24`
- Catalog: `070-illustrated-3`
- Plan and evidence wire contracts: `4`
- Previous distributed version: `0.8.9` / schema `24` / contract `4`

Implementation and candidate facts are recorded in the
[0.8.10 development record](../../history/0.8.10/development.md). GitHub Release
distribution is part of this update, but remains separate from a formal
compatibility baseline, public-support commitment, external content review,
personal-data transition or W4.

## Scope And Safety Boundary

User screenshots of the installed 0.8.9 client show uneven action-card placement
and a small centered illustration whose caption is detached at the left edge.
The preview scaled the label rectangle rather than the source image dimensions;
on a wide, relatively short label that manufactured a shallow intermediate
rectangle and unnecessarily constrained a square source. The icon view also did
not declare equal item sizes even though every card uses one grid.

The user also reported that the verified in-app update still did not close the
client automatically, while manually closing it immediately opened Setup. That
observation confirms the detached launcher is waiting correctly and isolates the
remaining failure to application exit. The 0.8.8 watchdog used `QTimer`, so it
depended on the same Qt event loop whose lack of progress could prevent the
normal quit request from completing.

- Scale illustration previews from the source's device-independent dimensions,
  preserve height-for-width sizing, and center each image with its caption.
- Give every action card the same explicit grid size and uniform-size contract.
- After a verified detached handoff, close visible windows and quit the
  application directly. Arm a daemon-thread watchdog that does not depend on
  Qt event processing before sending the final visible notification.
- Rotate application identity to 0.8.10. Do not change schema 24, catalog
  `070-illustrated-3`, contract 4, user data or import compatibility.

## Verification And Delivery Boundary

The updater module is imported on the application startup path and now imports
and annotates `threading.Timer`; an import, syntax or construction failure could
prevent the main window from opening. Exactly one existing isolated startup
construction scenario was selected under the stable update scope
`2026-10-03-image-updater-feedback` and passed once. The UI layout changes do not
create an application-open risk and receive no functional test.

Ruff, Python compilation, documentation consistency and diff checks may run
without counting as functional scenarios. Manual checks are zero. Do not use GUI
automation, operate an installed client, launch Setup or claim unobserved image
layout, updater exit or installer behavior passed.

Build a clean 0.8.10 Setup and publish stable GitHub Release `v0.8.10` with
exactly one `TrainingFeedback-0.8.10-Setup.exe`. Record the exact source,
toolchain, asset size, SHA-256, signature status, GitHub digest and evidence
limits in `docs/history/0.8.10/`.

The active execution plan is `.planning/releases/v0.8.10/PLAN.md`. Product
policy remains governed by [`development-plan.md`](../../development-plan.md),
and the event-specific procedure by
[`development-workflow.md`](../../development-workflow.md).
