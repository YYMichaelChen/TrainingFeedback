# 0.6.1 Development Record And Superseded Rules

Archived: 2026-09-20. Database baseline: schema 16; plan/evidence contract: v1.
Current requirements: [development plan](../../development-plan.md).
These rules explain the old baseline and must not be offered as a current mode.

## Completed scope

- Review, selected guidance and enablement became independent facts. Schema 15
  removed only `review.status`, preserving other review evidence. Schema 16 froze
  `guidance_reviewed_snapshot`; old sessions stayed NULL rather than acquiring review.
- Enabled actions with complete but unreviewed guidance could train with disclosure.
  Required images were not yet a use gate; missing images remained explicit.
- Managed image association created a new unreviewed revision. User images lived
  in `exercise-images/` with root-relative paths and containment/decoding checks.
- Bundled updates explicitly previewed and created selected drafts/new exercises.
  Stable bundled keys prevented duplicates; ambiguous aliases failed. Cancellation
  wrote nothing and batches rolled back. Startup did not overwrite local edits.
- External review source, actual date/time precision, separate confirmation time,
  original text and optional managed answer files were preserved. Review withdrawal
  cleared old current review evidence, retained selection/enablement, and was blocked
  for revisions referenced by history. Current 0.7.0 uses appended events instead.
- Per-user Inno Setup delivery used stable application identity, separate data,
  normal shortcuts, in-place program replacement and uninstall data retention.

## Retired architecture and workflow

`ApplicationContext` composed the old services/repositories. Domain/data handoff
used plan/evidence v1, and Settings included export-all. The old live model used
`exercise`, aliases/guidance/body-area relations; `training_plan` revisions/days/
actions/sets; `training_session` actions/sets/events; next-day feedback; `ai_export`
and `plan_import`. These are conversion inputs, not current runtime alternatives.

The selected root held marker/database/config, backups, exercise images, exports,
imports and reviews; the locator remained separate. The 0.7.0 catalog split adds
program-owned content plus custom/snapshot assets and removes startup seeding.

The [archived guidance/W4 procedure](guidance-review-runbook.md) preserves the old
operation sequence. It is not executable guidance for the current UI.

## Candidate-specific evidence and limitations

- The 2026-09-16 working-tree directory candidate passed manifest, module collection,
  data isolation and isolated startup checks; its dirty-source manifest uses base
  `072c931`. It does not inherit 0.6.0 Phase C or establish independent acceptance.
- Installer task records report 279 tests, Ruff/PowerShell/build checks and sandbox
  install/upgrade/uninstall checks, 211 payload files, plus an isolated installed
  startup with locator unchanged. These are historical results for that candidate.
- The unsigned installer and adjacent manifest are under `dist/installer/` pending
  versioned artifact organization. Hash verification passed in the 0.7.0 review.
- The old local baseline was recorded as 20 enabled actions, no recorded review,
  and a draft plan. Earlier approvals/activation preceded a local reset; they do
  not approve all 36 guides or establish the current personal-data stage.
- Inno Setup exists in the current user's standard program directory. The later
  070-H note claiming it was unavailable was corrected by direct file inspection.

Raw candidate hashes/source provenance stay in local evidence. Full content review,
W4 and independent Windows acceptance remained open. Preserve this version's
synthetic baseline for supported upgrading until it leaves the retention window.
