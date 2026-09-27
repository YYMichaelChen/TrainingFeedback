# 0.7.5 Development

## Scope

This version rotates the supported window to application 0.7.5 and schema 23.
The accepted reset and authoring behavior remains defined by the
[development plan](../../development-plan.md#134-075-one-time-plan-and-training-reset)
and its [plan authoring section](../../development-plan.md#1211-075-plan-authoring-and-identity).

## Implemented

- Fresh roots initialize directly at schema 23. A valid schema 22 root is
  checked read-only, then reset under the exclusive root lease. Plan/training
  rows and the approved managed-file directories are removed; library rows are
  copied into the new schema transactionally. A metadata-only journal resumes
  file cleanup after a committed reset.
- Plan roots receive unique base numbers and visible revision codes. Clone
  creates an independent root-local plan; Upgrade ties one draft to the latest
  active revision and computes its code from the saved difference.
- Plan and evidence contracts are v3. Imports target a local base number,
  exports carry the full plan code, and v2 imports are rejected.
- Plan composition now has an in-place day hierarchy, searchable multi-action
  selection, shared details for actions/groups/members, explicit blank dose and
  rest fields, and a confirmed equal-set fill operation. Invalid entries stay
  editable and cannot be saved as a complete draft.

## Verification

- Patch scope `release-0.7.5`: 48 unique cases were selected and passed after
  rerunning affected failures. The ledger remains at the same scope and tier.
- Ruff, `git diff --check`, and Python bytecode compilation passed.
- Catalog source verification passed for `070-illustrated-3` (36 exercises).
- The configured patch regression profile selects 30 cases. Its union with the
  already reserved affected cases would be 65, above the patch cap of 50, so the
  profile was not executed. No cases were removed from or split out of the
  release scope.
- A clean build from pushed revision `acce64846feb6c6090331bc17acd31d1377f5ef4`
  and installation into the standard per-user program directory completed;
  all 295 installed payload hashes match. UI/root workflow acceptance remains
  incomplete. Candidate identity and check limits are recorded in
  [local candidate evidence](local-candidate.md).
