# Versioned Development History

Retention authority: [development plan §13](../development-plan.md#13-version-retention-and-development-data-policy).
This table is the single human-readable current application/schema support map;
the [development workflow](../development-workflow.md) owns future rotation steps.
Keep complete development documents for the current application version and its
two predecessors, not the last three Git commits or schema numbers.

This directory is **tracked in Git**. Each subdirectory is labeled with the exact
application version it documents. Any file that must be retained for the window
lives here under its version; when a version rotates out of the three-version
window, its complete subdirectory moves to the untracked local `docs/archive/`
holding area in the same action — archiving into another unlimited location is
not policy compliance.

| Application version | Database baseline | History | Status |
| --- | --- | --- | --- |
| 0.7.2 | 22 | [Version update](0.7.2/development.md) | Current source and local installer candidate; public distribution remains deferred. |
| 0.7.1 | 22 | [Interface development](0.7.1/development.md) | Local development builds from an uncommitted source state; no public release or personal-data transition. |
| 0.7.0 | 22 | [Development deliveries](0.7.0/development.md), [release closeout](0.7.0/release-readiness.md), [installed candidate checks](0.7.0/packaged-acceptance.md), [test maintenance](0.7.0/test-maintenance.md), [contract integration history](0.7.0/contract-integration-history.md) | Retained local release; public H3 remains deferred. |

History records explain completed work and dated evidence; they do not override
current requirements or certify a later build. Multiple schemas already created
during 0.6.1/0.7.0 are historical exceptions, not a future numbering pattern.

At the next version bump, rotate the window, merge still-valid requirements into
current specifications, and move the expired version's complete history
subdirectory plus its exclusive fixtures/migration support to `docs/archive/`.
The 0.6.0 and 0.6.1 directories and schema16-only fixture rotated out in 0.7.2;
their committed bytes remain in Git history.
Git history is not rewritten. Historical references inside a retained version's
own evidence do not create another supported version or a requirement to retain
that older program.

Pre-0.6.0 task artifacts in `.planning/` and `.tmp/` were trimmed on 2026-09-21
per the [completed cleanup record](0.7.0/development.md#workspace-cleanup-completed-2026-09-21);
retained-version evidence (including `070-e/f/h` verification) was preserved
under `.tmp/releases/0.7.0/` and the kept visual/rehearsal directories.

The [2026-09-23 release-boundary record](0.7.0/development.md#local-release-policy-2026-09-23)
explains the current local/public distinction. Historical pending statements below
older dates do not reopen completed R1/R2 or supersede that decision. Current
requirements remain in the main plan and current manuals; historical candidate
results certify only their identified build.
