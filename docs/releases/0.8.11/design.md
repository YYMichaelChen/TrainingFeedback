# 0.8.11 Action Reading Design

## Identity and scope

- Application: `0.8.11`
- Database schema: `24`
- Catalog: `070-illustrated-3`
- Plan/evidence contract: `4`
- Latest distributed application: `0.8.10`
- Events: development update and application-version rotation; the user's
  2026-10-04 follow-up additionally authorizes commit/push, Setup and GitHub Release.

Implement the confirmed
[动作详情与指导阅读重新设计](../../designs/exercise-reading-redesign.md).
The user authorized implementation on 2026-10-04. Durable reading behavior is
owned by [product specification §12.12](../../development-plan.md#1212-action-detail-and-guidance-reading),
and actual results by the [development record](../../history/0.8.11/development.md).

## Implementation

Add independent UI reading components for grouped verbatim guidance, bounded
image paging and an original-pixel zoom viewer. Library details replace the
three top-level tabs and bottom management rows with responsive reading and a
grouped exact-target menu. Move review history and content identity/qualification
into read-only dialogs. External-review forms and frozen-guidance dialogs share
the reading region while retaining their existing surrounding controls.

Library and review images come from the existing checked-image service. Frozen
guidance and images remain tied to session snapshots. Keep the old training-page
guidance and image components, card layout, business rules and write services.
No catalog text, illustration assets, schema or wire contract changes.

## Verification and delivery limits

`group_session_page.py` imports `group_training_page.py` on main-window startup;
that module now imports `exercise_reading.py`. An invalid new Qt import or module
definition could prevent startup. Select only the existing isolated
`test_update_coordinator_does_not_block_main_window_startup` in
`tests/test_update_startup.py`
under stable scope `2026-10-04-exercise-reading` (dev tier), with no navigation,
real data or network. This verifies startup imports, not the new reading behavior.
Keep static checks confined to changed source, identities and documentation.

Manual checks are zero. No client operation, GUI automation, functional
regression or personal-data transition is in scope.
Unobserved layout, resizing, image viewing and menu behavior are not passes or
deferred acceptance obligations. Candidate evidence from v0.8.10 does not apply.
Execution state is local and routed through `.planning/INDEX.md`.

## Authorized delivery follow-up

The source-only development scope was completed first. The user then explicitly
requested commit, push and release. Build from a clean source commit, retain the
payload/installer manifests and publish stable `v0.8.11` with exactly one
`TrainingFeedback-0.8.11-Setup.exe`. Packaging compares the catalog resource
manifest, sizes and hashes via `--verify-files`; it does not run the dormant
full-catalog decoding/rule check. This adds no application tests or manual checks.
Record the exact candidate and public GitHub asset identity in version history.
