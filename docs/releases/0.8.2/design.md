# 0.8.2 Development Design

## Identity

- Application version: `0.8.2`
- Database schema: `24`
- Catalog: `070-illustrated-3`
- Plan and evidence wire contracts: `4`
- Previous distributed version: `0.8.1` / schema `23` / contract `3`

This is the active development target. No 0.8.2 package, acceptance result,
formal compatibility claim, or public release is recorded here.

## Scope

- Remove user-defined training-day names from plans, wire imports, database
  storage, execution snapshots and visible plan/session pages. Days display by
  order; a one-day plan uses the plan name in the start selector.
- Upgrade schema 23 roots in place to schema 24 transactionally. Preserve
  plans, training history, feedback and review records while dropping only the
  obsolete name columns.
- Correct the exercise-library illustration tab label, make card thumbnails
  sharp on high-DPI screens and fit detail illustrations to their visible area
  while keeping original-image viewing.
- Set the TrainingFeedback window icon.

The approved release execution plan is `.planning/releases/v0.8.2/PLAN.md`.
Product behavior and release gates remain governed by
[`development-plan.md`](../../development-plan.md), and development procedure
by [`development-workflow.md`](../../development-workflow.md).

