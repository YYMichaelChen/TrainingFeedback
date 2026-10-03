# 0.8.9 Action-Library Construction Fix Design

## Identity

- Application version: `0.8.9`
- Database schema: `24`
- Catalog: `070-illustrated-3`
- Plan and evidence wire contracts: `4`
- Previous distributed version: `0.8.8` / schema `24` / contract `4`

Implementation and candidate facts are recorded in the
[0.8.9 development record](../../history/0.8.9/development.md), and the Setup is
distributed through [GitHub Release v0.8.9](../../history/0.8.9/github-release-2026-10-03.md).
GitHub Release distribution remains separate from a formal
compatibility baseline, public-support commitment, external content review,
personal-data transition or W4.

## Scope And Safety Boundary

User feedback on the installed 0.8.8 client showed that selecting 动作库 reached
the 0.8.7 containment page with `KeyError: 'images_tab'`. Both the action-library
detail view and review dialog read `LIBRARY_TEXT["images_tab"]`, but the 0.8.2
illustration update added that label only to `GROUP_PLAN_TEXT`. Action-library
construction therefore failed deterministically before any catalog or user-data
read.

- Add the missing `images_tab` entry to `LIBRARY_TEXT`, preserving the intended
  Chinese label “动作示意图”.
- Keep page construction, catalog loading, image checking and all data behavior
  unchanged.
- Rotate application identity to 0.8.9. Do not change schema 24, catalog
  `070-illustrated-3`, contract 4, user text, user facts or import compatibility.

## Verification And Delivery Boundary

The change adds one constant dictionary entry and does not alter a startup
execution path or create a specific application-open failure risk. Run zero
application scenarios and zero manual checks under the current policy. Inspect
the exact references, run Ruff, documentation consistency and diff checks, and
do not use GUI automation or real user data. Action-library navigation and
installed-client behavior remain unobserved and are not passes.

Build a clean 0.8.9 Setup and publish stable GitHub Release `v0.8.9` with
exactly one `TrainingFeedback-0.8.9-Setup.exe`. Record the exact source,
toolchain, asset size, SHA-256, GitHub digest and evidence limits in
`docs/history/0.8.9/`.

The active execution plan is `.planning/releases/v0.8.9/PLAN.md`. Product
policy remains governed by [`development-plan.md`](../../development-plan.md),
and the event-specific procedure by
[`development-workflow.md`](../../development-workflow.md).
