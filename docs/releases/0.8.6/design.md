# 0.8.6 Updater Artifact Cleanup Design

## Identity

- Application version: `0.8.6`
- Database schema: `24`
- Catalog: `070-illustrated-3`
- Plan and evidence wire contracts: `4`
- Previous distributed version: `0.8.5` / schema `24` / contract `4`

The implementation and clean local candidate are recorded in the
[0.8.6 development record](../../history/0.8.6/development.md), and the Setup is
distributed through [GitHub Release v0.8.6](../../history/0.8.6/github-release-2026-10-03.md).

The user requested this as an additional “v0.8.5b” update. The updater accepts
only stable `vMAJOR.MINOR.PATCH` tags and application identities, so the
updater-compatible patch identity is v0.8.6 rather than a suffix that existing
clients would ignore.

GitHub Release distribution is part of this update, but remains separate from a
formal compatibility baseline, public-support commitment, external content
review, personal-data transition or W4.

## Scope And Safety Boundary

- Mark every newly created updater temporary directory as application-owned.
- After the current client exits, start the verified Setup with the detached
  Windows launcher, wait for Setup and its process tree to finish, and then
  remove that exact temporary directory in a `finally` cleanup.
- When the update coordinator is constructed, best-effort remove stale direct
  children of the selected system update-temporary root. A candidate qualifies
  only when its directory has the exact `TrainingFeedback-update-` random-name
  shape, is neither a symbolic link nor junction, resolves directly beneath the
  expected root, and contains only the owned marker and/or an exact semantic-
  version TrainingFeedback Setup `.exe` or `.part` file.
- Recognize the strict legacy directory contents written by v0.8.3–v0.8.5 so
  the first v0.8.6 startup can remove the package that installed it. Empty,
  foreign, nested, linked or extra-content directories are left unchanged.
- Keep all cleanup outside the selected data root. A cleanup refusal or failure
  is non-blocking and does not prevent startup or update discovery.
- Rotate application and implementation-history identity to 0.8.6. Do not
  change schema 24, catalog `070-illustrated-3`, contract 4, user text, user
  data or import compatibility.

## Verification And Delivery Boundary

The update coordinator now performs non-blocking stale-artifact cleanup during
its construction on the startup path. Select exactly one existing isolated
startup scenario with an injected synthetic temporary root to catch an import,
constructor or unexpected-cleanup exception that could prevent the main window
from opening, then stop when it passes. Deletion selection, Setup waiting and
post-install cleanup receive no extra functional or GUI-automated scenarios
under the current policy.

Ruff, documentation consistency and diff checks may be run without counting as
functional coverage. Manual checks are zero. Do not inspect or modify real user
data, operate an installed client, launch Setup or claim unobserved cleanup and
Windows process behavior passed.

Build a clean 0.8.6 Setup and publish stable GitHub Release `v0.8.6` with exactly
one `TrainingFeedback-0.8.6-Setup.exe`. Record the exact source, toolchain, asset
size, SHA-256, GitHub digest and evidence limits in `docs/history/0.8.6/`.

The active execution plan is `.planning/releases/v0.8.6/PLAN.md`. Product policy
remains governed by [`development-plan.md`](../../development-plan.md), and the
event-specific procedure by [`development-workflow.md`](../../development-workflow.md).
