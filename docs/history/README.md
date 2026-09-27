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
| 0.7.3 | 22 | [Plan page and local candidate](0.7.3/development.md) | Current local candidate accepted; public distribution remains deferred. |
| 0.7.2 | 22 | [Version update](0.7.2/development.md) | Retained local candidate. |
| 0.7.1 | 22 | [Interface development](0.7.1/development.md) | Retained development version; no public release or personal-data transition. |

History records explain completed work and dated evidence; they do not override
current requirements or certify a later build. Multiple schemas already created
during 0.6.1/0.7.0 are historical exceptions, not a future numbering pattern.

At the next version bump, rotate the window, merge still-valid requirements into
current specifications, and move the expired version's complete history
subdirectory plus its exclusive fixtures/migration support to `docs/archive/`.
The 0.6.0 and 0.6.1 directories and schema16-only fixture rotated out in 0.7.2;
their committed bytes remain in Git history.
The complete 0.7.0 history, local planning records and candidate evidence rotated to the ignored
`docs/archive/0.7.0/` holding area in 0.7.3. The last tracked snapshot is
[`f2e0700`](https://github.com/YYMichaelChen/TrainingFeedback/tree/f2e0700362bc1413a19af86739ffef50f5ac5cf5/docs/history/0.7.0).
Git history is not rewritten. Historical references inside a retained version's
own evidence do not create another supported version or a requirement to retain
that older program.

Historical candidate results certify only their identified build. Current
requirements remain in the main plan and current manuals.
