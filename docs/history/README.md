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

Current development application version: **0.7.6** (database schema **23**).
Latest locally accepted candidate: **0.7.3**; that version is now outside the
retained window, and its acceptance is historical. The 0.7.4 and 0.7.5
candidates have incomplete installed/local acceptance recorded below. The user
closed 0.7.5 for continued development with its unrun checks recorded; this is
not a technical acceptance pass or evidence for 0.7.6.

| Application version | Database schema | Role | Local candidate |
| --- | --- | --- | --- |
| 0.7.6 | 23 | Current development version: [documentation ownership and routing](0.7.6/development.md) | No installer candidate; development verification only |
| 0.7.5 | 23 | Closed development version: [plan and reset development](0.7.5/development.md) | [User-approved closeout; installed acceptance incomplete](0.7.5/local-candidate.md#2026-09-29-final-version-closeout) |
| 0.7.4 | 22 | Retained predecessor: [performance development](0.7.4/development.md) | [Installed acceptance incomplete](0.7.4/local-candidate.md) |

History records explain completed work and dated evidence; they do not override
current requirements or certify a later build. Multiple schemas already created
during 0.6.1/0.7.0 are historical exceptions, not a future numbering pattern.

On each distinct application-version change, rotate the window, merge
still-valid requirements into current specifications, and move the expired
version's complete history subdirectory plus its exclusive fixtures/migration
support to `docs/archive/`.
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
history. Schema 22 remains supported through the retained 0.7.4 root lifecycle.
Git history is not rewritten. Historical references inside a retained version's
own evidence do not create another supported version or a requirement to retain
that older program.

Historical candidate results certify only their identified build. Current
requirements remain in the main plan and current manuals.
