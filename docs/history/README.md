# Versioned Development History

Retention authority: [development plan §13](../development-plan.md#13-version-retention-and-development-data-policy).
This table is the single human-readable current application/schema implementation map;
the [development workflow](../development-workflow.md) owns future rotation steps.
The user has suspended old-version compatibility obligations until an explicit
formal release. Rows for older development versions describe recorded behavior
and evidence, not a current support promise.

This directory is **tracked in Git**. Each subdirectory is labeled with the exact
application version it documents. Version history and local archive cleanup now
follow the audited retention rule in development plan §13; existing historical
rotations below are facts, not a continuing three-version obligation.

Current development application version: **0.7.7** (database schema **23**).
Latest locally accepted candidate: **0.7.3**; that version is now outside the
retained window, and its acceptance is historical. The 0.7.5 candidate has
incomplete installed/local acceptance recorded below. The user closed 0.7.5
for continued development with its unrun checks recorded; this is not a
technical acceptance pass or evidence for 0.7.7.

| Application version | Database schema | Role | Local candidate |
| --- | --- | --- | --- |
| 0.7.7 | 23 | Closed development version: [new-root creation](0.7.7/development.md) | [User-approved partial closeout; full local installed acceptance incomplete](0.7.7/local-candidate.md#2026-09-29-部分验收收尾) |
| 0.7.6 | 23 | Historical development version: [documentation ownership and routing](0.7.6/development.md) | No installer candidate; development verification only |
| 0.7.5 | 23 | Historical development version: [plan and reset development](0.7.5/development.md) | [User-approved closeout; installed acceptance incomplete](0.7.5/local-candidate.md#2026-09-29-final-version-closeout) |

History records explain completed work and dated evidence; they do not override
current requirements or certify a later build. Multiple schemas already created
during 0.6.1/0.7.0 are historical exceptions, not a future numbering pattern.

On future application-version changes, update this implementation map and merge
still-valid requirements into current specifications. Remove obsolete history,
fixtures and migration entry points only after the v0.8.0 audit; after formal
release, retain the user-selected one or two predecessor formal versions.
The 0.6.0 and 0.6.1 directories and schema16-only fixture rotated out in 0.7.2;
their committed bytes remain in Git history.
The complete 0.7.0 history, local planning records and candidate evidence rotated to the ignored
`docs/archive/0.7.0/` holding area in 0.7.3. The last tracked snapshot is
[`f2e0700`](https://github.com/YYMichaelChen/TrainingFeedback/tree/f2e0700362bc1413a19af86739ffef50f5ac5cf5/docs/history/0.7.0).
The 0.7.1 history and local planning records rotated into the ignored
`docs/archive/0.7.1/` holding area in 0.7.4; Git history retains the tracked
development record.
The 0.7.3 history and local planning records rotated into the ignored
`docs/archive/0.7.3/` holding area in 0.7.6; Git history retains their tracked
history. The 0.7.4 history and local planning records rotated in 0.7.7.
Schema 22 roots are expired and refused unchanged; committed cleanup journals
in retained schema 23 roots remain recoverable.
Git history is not rewritten. Historical references inside a retained version's
own evidence do not create another supported version or a requirement to retain
that older program.

Historical candidate results certify only their identified build. Current
requirements remain in the main plan and current manuals.
