# Development Workflow

This is the version-independent procedure for TrainingFeedback development and
delivery. Classify work by **event**, not by the version number in a task title.
Every current personal-use update follows the startup-only policy in
[product specification §9.1](development-plan.md#91-release-and-follow-up-boundaries).
Combining events does not add checks or increase the three-scenario cap.

## Authority and current state

- The [documentation index](README.md) routes durable authority and document
  lifecycle. It is distinct from local Planscope execution routing.
- [Development plan](development-plan.md) owns product behavior, the local/public
  release boundary, and the formal-release compatibility policy. The
  [initial catalog specification](initial-exercises-and-plan.md) owns proposed
  built-in content until deliberately revised.
- This document owns the procedure. [Packaged acceptance](packaged-acceptance-runbook.md)
  owns installation and machine-level checks; [test instructions](../tests/README.md)
  explain commands. Completed candidate results belong to dated version history
  and candidate-specific evidence, not to these procedures.
- [Guidance review](guidance-review-runbook.md) owns external content review,
  personal transition and W4 procedures. The release gates in the development
  plan determine when each is in scope.
- [Version history index](history/README.md) is the one human-readable current
  application/schema support map. The running values live in `pyproject.toml`,
  `src/training_feedback/__init__.py`, `src/training_feedback/data/migrations.py`, the catalog manifest,
  and the bundled wire contracts. Check these separately at a version change;
  a catalog or contract revision is not a database schema revision.
- Local Planscope is execution context: `.planning/INDEX.md` routes to the active
  release `PLAN.md`, which owns its phase, task, blockers and next action. It does
  not replace tracked requirements or candidate evidence.

## Events and minimum gates

| Event | Current procedure |
| --- | --- |
| Development update | Identify a concrete startup failure risk. Run 0 checks without one; otherwise select at most 3 independent scenarios, normally 0–1. |
| Local package or installed delivery | Build only if part of the agreed deliverable; record source/build identity. No added regression or installed checklist. |
| Application version change | Update application/schema/catalog/contract identities and support mapping; the same startup-only limit applies. |
| Formal release declaration | Only the user can declare it. Identify the support baseline under product policy; do not automatically add compatibility tests. |
| GitHub Release distribution | Upload the identified installer and concise notes to the matching version Release. This adds no tests and does not declare a formal compatibility baseline. |
| Formal public-support commitment | Only an explicit user declaration opens a new discussion of support scope; do not execute stored public scenarios automatically. |

Personal-data transition remains the user's explicit decision. Content review,
personal use and W4 do not add software checks or revive cancelled acceptance.
Synthetic facts never become personal facts.

### Start and record one task

Before implementation, inspect the working tree; classify the event(s) and
micro, normal or complex scope; identify affected risks and the expected result.
Use the installed `planscope` skill when work needs durable context. Read
`.planning/INDEX.md` first, then only the active PLAN current/affected phase.
Search KNOWLEDGE for relevant findings, read PROJECT for cross-release decisions,
and consult recent LOG only for recovery. Micro edits may skip planning. If
`.planning/` is absent, use tracked docs and Git state; initialize it only for
work needing durable planning, without inventing a release from old records.

Load the affected tracked product rules after routing context. Implement and
verify the change, then update PLAN when task/phase state changes and run
`plan.py sync` after changing current phase, task, blockers or next action.
Record only non-recoverable reusable findings in KNOWLEDGE and recent recovery
context in LOG. Use `plan.py doctor` and `compact` after structural planning
changes. Historical planning records remain read-only context; product rules
and formal release evidence stay in tracked docs.

### Verify a development task

1. Read the diff and state the specific causal link, if any, from this change to
   failure to open the application. A module name or general quality/data-safety
   concern is not sufficient. Documentation-only work runs 0 application tests.
2. Without such a risk, run 0 application tests. With one, select only existing
   relevant code-level checks, at most 3 independent scenarios for the whole
   update, normally 0–1. There is no mandatory three-check bundle.
3. Use PowerShell 7, the repository interpreter and isolated synthetic inputs.
   Select explicit pytest node IDs under a single stable update scope; never run
   bare pytest, a whole file containing unrelated cases or a version profile.
4. Stop when the selected checks pass. After a fix, rerun only failed or directly
   affected original checks; record repeat executions. Do not add unrelated
   cases, performance samples or speculative fault scenarios.
5. Deliver a short statement of check count, actual results and known issues.
   Handle other problems when the user reports them in normal use. Do not append
   a list of functional checks for the user to complete.

[Tests README](../tests/README.md) owns counting and CLI details. Independent
script scenarios and parameterized cases consume the same three-scenario cap;
bundling, task splitting, alternate commands or new scope names cannot evade it.
One genuine update keeps one scope across fixes and commands. A version bump,
installer or release closeout does not create another verification allowance.
Preserve historical ledgers; do not clear them or manufacture a new update to
continue cancelled testing. Record the current policy beside older tool budgets.

Static diff/link/identity inspection is distinct from application tests. Keep it
limited to the change: Ruff for changed Python files where applicable,
`git diff --check`, and `python packaging/check_docs.py` for documentation,
source-reference or identity edits. Do not disguise functional scenarios as
static checks. No routine benchmarks, full test discovery or build is needed.

### Verification by affected risk

The only selection criterion is a concrete application-startup failure caused
by this update. Possible qualifying checks concern a changed startup import or
required resource, initialization/opening of a synthetic current root, or
startup object construction. Select only the relevant risk; these are examples,
not a checklist. Do not exercise navigation or other client functionality.

UI layout, search, saved content, training state, import/export, backup and
performance have no automatic regression obligation. Their implementation
requirements still apply; user feedback drives subsequent fixes.

### Prepare a local candidate

1. Build only when an installer is requested or part of the agreed deliverable.
   Identify the source snapshot and application/schema/catalog/contract values.
   Reconcile owned development content before retiring its root; never inspect
   personal roots automatically.
2. Apply the same startup-only limit for this update. Candidate preparation
   adds no release suite, manual matrix or larger tier allowance.
3. When building, retain the generated manifests and exact installer/executable
   identity. Review relevant startup payload issues without adding broad
   runtime scenarios. Use reproducible complete source; a dirty snapshot remains
   an informal preview and carries no complete-acceptance claim.
4. Manual checks default to 0. Only if a concrete startup risk cannot be resolved
   by code-level checks, ask for at most one observation on the user's next
   normal opening of the application. No dedicated acceptance session,
   recording, timing, repeated installation/uninstallation or simulated training.
5. The default distribution destination is this repository's GitHub Releases.
   Attach the identified Setup executable to the matching version tag and state
   its SHA-256, signature status, build source revision and evidence limits.

Record only what was actually observed for the exact candidate. Existing
results retain their identities; changing a candidate does not require repeating
cancelled checks. An unrun check is not a pass, and a check cancelled by current
policy is not an outstanding gate. A known startup failure remains actionable.
Local delivery never itself declares public acceptance or personal-data transition.

### Close a release

Review the implementation and its acceptance criteria under current §9.1,
recording actual results and cancelled requirements in `docs/history/<version>/`.
Do not retain superseded manual or functional verification as closeout blockers.
Do not claim a cancelled check passed or close unrelated unfinished work. Create the Planscope
`SUMMARY.md`, promote only durable non-recoverable project knowledge, update
ROADMAP, mark every PLAN phase and its status complete, then run `plan.py doctor`
and `plan.py close <version>`. The close command archives execution context;
its archive does not replace tracked release evidence. Compact planning
archives under the audited retention rules in Section 13 of the development plan.

### Rotate a version

An application-only fix may retain its schema. Every new database schema revision
or external wire-schema change requires an application patch-or-greater bump in
the same change. On every distinct application version bump, update the version
history index, source version values, implemented application/schema mapping and
relevant contract/catalog identities. Apply the compatibility and retention
boundary owned by the product release policy; several commits of one version do
not create distinct version identities.
A version bump does not select a larger test profile. Use the same update scope
and three-scenario limit whether the update includes a package or not.

Inventory completed documents, planning archives, contract/schema baselines,
synthetic fixtures and migration entry support. Before removing a path, inspect its current references and startup role.
Any executable check must qualify under §9.1; no broad regression is implied. Git history remains available; the local archive is not an unlimited
second retention system. Reject unsupported or future roots before writes with
actionable new-empty-root guidance, without deleting or importing their data.
Program reinstall alone does not reset a data root. Any adopted exception must
follow the product's explicit path-verification and confirmation rules.

## Three walkthroughs

- **Documentation or ordinary UI wording change:** 0 application tests and
  0 manual checks; inspect the diff and relevant document links.
- **Startup dependency or root-opening change:** explain the startup failure
  risk, select the minimum matching code-level scenarios, at most 3, and stop
  when they pass. No navigation, simulated training or fault matrix.
- **Local installer update:** same cap; retain the build identity if packaging
  is in scope. No repeated install/uninstall acceptance. Public distribution
  remains dormant until explicitly requested and scoped.
