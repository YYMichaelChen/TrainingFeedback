# v0.7.5 One-Time Plan And Training Reset

This is the historical design for the schema-22 reset accepted on 2026-09-28.
It records what v0.7.5 did and does not define current upgrade behavior.

After 0.7.4 source work closed, v0.7.5 first opening any valid schema 22
TrainingFeedback root automatically deleted its existing plan and dependent
training data without a confirmation prompt or recovery backup. Schema 22 roots
created by 0.7.2, 0.7.3 and 0.7.4 did not record enough application-version
information to distinguish their origin reliably; all were subject to this
same reset. This was an explicit exception to ordinary preservation rules, not
evidence that prior plan or training facts were preserved.

The reset removed current and retained legacy plan revisions, actions, doses,
activation pins, sessions and their results, retractions, next-day feedback,
plan/session import-export registrations and associated managed files. It also
deleted existing backups inside that selected root, including backups that may
contain other root data. It retained the root's library selections, custom
actions, guidance, images, review and removal decisions that were independent
of the deleted plans. No previous synthetic training or approval became a new
personal fact. Files copied outside the selected root were not discovered or
deleted. The old `Exercises@home` repository and database remained untouched.

Before any write, the application validated the exact selected root's marker,
configuration, schema, SQLite integrity and references, acquired its exclusive
lease and inventoried managed deletion paths. It applied the database reset and
schema 23 migration transactionally. A metadata-only cleanup journal allowed an
interrupted run to finish pending file deletions before the root became usable;
the transition did not create or retain a data snapshot or report partial
cleanup as success. Failure before the database commit left old rows unchanged;
failure afterward resumed the irreversible cleanup on next open. Installation
alone and root discovery did not trigger the reset.

Fresh v0.7.5 roots started at schema 23 with no old plan data. Roots with a
schema earlier than 22, a future schema or invalid metadata remained unchanged
and were rejected before cleanup. Verification used isolated synthetic roots,
interrupted cleanup, repeat opening and installed checks. Ordinary preservation
and backup policy resumed after this one-time transition.
