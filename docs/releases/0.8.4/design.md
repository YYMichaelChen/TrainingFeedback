# 0.8.4 UI Reliability Update Design

## Identity

- Application version: `0.8.4`
- Database schema: `24`
- Catalog: `070-illustrated-3`
- Plan and evidence wire contracts: `4`
- Previous distributed version: `0.8.3` / schema `24` / contract `4`

The implementation and clean local candidate are recorded in the
[0.8.4 development record](../../history/0.8.4/development.md).

GitHub Release distribution is part of this update, but remains a separate event
from development and does not declare a formal compatibility baseline, public
support, external content review, personal-data transition or W4.

## User Feedback And Evidence Boundary

The [2026-10-03 user screenshot](../../history/0.8.4/evidence/user-ui-feedback-2026-10-03.png)
shows the installed application using a generic title-bar icon. It also shows
the action-library navigation item selected while the prior training-plan page
remains visible, and exposes the unexplained labels `v4 计划` and `v4 证据`.
The screenshot is defect input only: it does not identify the cause and cannot
certify the later fix.

The icon was originally in the 0.8.2 scope, not 0.8.3. The 0.8.2 development
record verified matching source/runtime bytes and packaged resources while
explicitly leaving visible title-bar behavior unobserved. v0.8.4 preserves that
historical evidence instead of rewriting it as a pass.

In the current UI, “v4 plan” means a JSON handoff file using
`training_feedback.plan` format version 4. It is not the fourth user plan or a
plan revision label. v0.8.4 keeps the contract and its validation unchanged.

## Scope

- Load the owned runtime `TrainingFeedback.ico` through one UI helper, reject a
  null icon, and apply the same icon to QApplication, MainWindow and the
  parentless first-run data-root dialog. Application-owned child dialogs inherit
  from the application or parent; native Windows file dialogs remain OS-owned.
- Make the progressive action-library page visible before its first browse. The
  initial browse runs on the next event-loop turn, preserves progressive card
  checks, and reports a load failure inside the selected page instead of leaving
  the previous page visible with an unhandled Qt-slot exception.
- Replace ordinary plan-page wording with `导入计划文件`, `导出计划资料`,
  `计划资料已导出到：` and an empty-state reference to `计划文件`. Only validation
  errors mention `格式版本 4` and tell the user to use a file exported by the
  current application.
- Rotate application and implementation-history identity to 0.8.4. Do not change
  schema 24, catalog `070-illustrated-3`, contract 4, user text, user data or
  import compatibility.

## Verification And Delivery Boundary

The icon helper is imported by the startup entry and its resource is required
before a usable main window can be constructed. Select exactly one isolated
code-level startup scenario that loads the icon and constructs a MainWindow,
then stop when it passes. The action-library and plan wording are UI behavior and
receive no additional functional scenarios under the current policy.

Ruff, documentation consistency and diff checks may be run without using them as
functional coverage. Manual checks are zero. No GUI automation, real user root,
installed-client operation, plan import/export regression or dedicated title-bar
observation is permitted. Candidate construction may verify exact package/resource
identity but does not certify visible Windows chrome.

Build a clean 0.8.4 Setup and publish a non-draft, non-prerelease GitHub Release
`v0.8.4` with exactly one `TrainingFeedback-0.8.4-Setup.exe`. Record the exact
source, toolchain, asset size, SHA-256, GitHub digest and evidence limits in
`docs/history/0.8.4/`.

The active execution plan is `.planning/releases/v0.8.4/PLAN.md`. Product policy
remains governed by [`development-plan.md`](../../development-plan.md), and the
event-specific procedure by [`development-workflow.md`](../../development-workflow.md).
