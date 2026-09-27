# Development Workflow

This is the version-independent procedure for TrainingFeedback development and
delivery. Classify work by **event**, not by the version number in a task title.
Several events may apply to one task; perform each applicable gate once. A task
that directly produces a release uses its release verification scope and does not
also run a separate development profile.

## Authority and current state

- [Development plan](development-plan.md) owns product behavior, the local/public
  release boundary, and the three-application-version retention policy. The
  [initial catalog specification](initial-exercises-and-plan.md) owns proposed
  built-in content until deliberately revised.
- This document owns the procedure. [Packaged acceptance](packaged-acceptance-runbook.md)
  owns installation and machine-level checks; [test instructions](../tests/README.md)
  explain commands. Completed candidate results belong to dated version history
  and candidate-specific evidence, not to these procedures.
- [Version history index](history/README.md) is the one human-readable current
  application/schema support map. The running values live in `pyproject.toml`,
  `src/training_feedback/__init__.py`, `data/migrations.py`, the catalog manifest,
  and the bundled wire contracts. Check these separately at a version change;
  a catalog or contract revision is not a database schema revision.

## Events and minimum gates

| Event | Required work | Exit |
| --- | --- | --- |
| Development task | State the intended behavior and affected risks; inspect existing coverage, make the change, run focused verification and applicable static checks. | Relevant checks pass and their actual results are recorded. No automatic installer build. |
| Local release or user-requested installed acceptance | Close intended candidate content; verify final source and release regression; build and inspect the installer; exercise the installed app with isolated synthetic roots. | Candidate identity, manifests, installed checks and evidence limits are recorded. |
| Public release | Start only on the user's explicit request; run the independent Windows and public-distribution gate in the packaged-acceptance runbook. | Every required public scenario has candidate-specific evidence; `not run` is never `pass`. |
| Application version change | Update application version and distinct schema/catalog/contract mappings; rotate the three-version window and support paths. | Retained roots work, expired roots are refused unchanged before writes, and old data remains intact. |

External content review, personal-data transition and W4 have their own product
triggers in the development plan. None follows automatically from packaging,
testing or a version bump. Synthetic facts never become personal facts.

### Start and record one task

Before implementation, inspect the working tree and identify the event(s), scope,
affected behaviors, expected result and verification tier. For work needing
durable context, use the installed `planscope` skill and start at
`.planning/INDEX.md`. It routes to the single active release's `PLAN.md`,
`KNOWLEDGE.md` and recent `LOG.md`. Read only relevant sections. A small local
change may skip planning unless it changes release state or stable constraints.

`PLAN.md` owns current release work; after editing its current state, run
`plan.py sync` to update `INDEX.md`. Record only reusable discoveries in
`KNOWLEDGE.md` and recent recovery context in `LOG.md`. Use the skill's
`doctor` and `compact` checks when changing planning structure. Close a release
only after its acceptance work is complete; keep archives inside the
three-application-version retention window. The pre-Planscope local task records
remain read-only historical evidence; use the `archive/v<version>/SUMMARY.md`
route for past work and do not load archives as active context. Keep product rules
and decisions in the development plan, not in planning summaries.

### Verify a development task

Use PowerShell 7 and the repository interpreter. Reuse meaningful existing tests
before adding a case. For code, content or contract changes, select only affected
pytest nodes/files (or `-k`) with `--test-tier dev --test-scope TASK-ID`; use
`--collect-only` to inventory when necessary. Run Ruff for changed Python areas
and `git diff --check`. A documentation-only change needs link, status and diff
checks, not routine pytest. Stop after relevant checks pass; after a fix, rerun
only failed or affected checks.

Budgets count parameter-expanded unique cases across commands in one immutable
scope: dev 30, patch 50, minor 100, major 300, with at most 300 resident cases.
These are ceilings, not targets. Never split or reset a scope to evade a cap,
hide cases at collection, or move independent regression scenarios into loops.
The pytest plugin enforces selection and accounting; this procedure does not
change its CLI. A release task uses the matching patch/minor/major scope from
its first execution and includes affected cases within that scope. Do not run
all tier profiles in sequence.

### Prepare a local candidate

1. Confirm the intended source/content is complete and internally consistent.
   Reconcile deliberate development content into owned source before retiring a
   development root; do not inspect or promote personal roots automatically.
2. Identify the final reproducible source snapshot and the separate application,
   schema, catalog and wire-contract versions. Use a stable `release-<version>`
   test scope and the appropriate release tier; run its baseline plus affected
   integration cases within the one tier budget, then applicable Ruff and diff
   checks. A same-version commit uses the same version slot and release scope.
3. Build the installer from the identified complete source with the pinned
   toolchain. Verify source identity/dirty status, complete payload and installer
   manifests, hashes, bundled catalog and assets, required runtime files and
   absence of user data. A clean source revision is required to claim a local
   release or completed installed acceptance; a dirty build is only an informal
   preview with its exact source snapshot and limit disclosed.
4. Install that candidate under an isolated locator/profile and synthetic roots.
   Verify the installed payload, fresh launch and cancel, new-root catalog,
   restart/reopen, and the affected user workflow. Include supported-root upgrade
   and out-of-window read-only refusal when compatibility changes. Record the
   account, paths, inputs, expected/actual result and evidence for each check.

Candidate evidence is immutable and identified by source revision/snapshot,
manifest and installer/executable hashes. If source or payload changes after a
pass, keep the earlier candidate's results historical; rerun only affected tests
in the same release scope and affected installed checks for the new candidate.
Reference earlier unchanged checks explicitly rather than silently claiming they
were repeated. A local result never implies public acceptance, expert review or
personal-use readiness.

### Rotate a version

An application-only fix may retain its schema. Every new database schema revision
or external wire-schema change requires an application patch-or-greater bump in
the same change. On every distinct application version bump, update the version
history index, source version values, supported application/schema mapping and
relevant contract/catalog identities. Retain the current application version plus
two immediate predecessors; several commits of one version consume one slot.
If the bump is still a development step, use its dev scope; a task that directly
forms a release uses the release scope instead.

Inventory completed documents, planning archives, contract/schema baselines,
synthetic fixtures and migration entry support. Move expired complete records to
the local `docs/archive/` holding area and remove exclusive runtime/test entry
paths only after verifying retained upgrades and fresh initialization. Git history
remains available; the local archive is not an unlimited second retention system.
Reject expired or future roots before writes with actionable new-empty-root
guidance, without deleting or importing their data. Program reinstall alone does
not reset a data root.

## Three walkthroughs

- **Small UI change:** one dev task and scope; affected UI cases, Ruff and diff
  check; no installer unless the user asks for installed acceptance.
- **Schema-changing patch release:** one patch release scope, including affected
  upgrade/preservation/refusal cases; application patch bump and window rotation;
  clean source, verified installer and isolated installed compatibility checks.
- **Requested public release:** complete the local candidate gate, then use the
  explicit public gate on an independent Windows environment with actual retained
  binaries and distribution evidence. Mark unavailable checks `not run` and do
  not publish as accepted while required public checks remain open.
