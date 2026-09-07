# Phase 0 And Phase 1 Implementation Design

> Note: file names in this document reflect the design-time layout. The current layout is documented in README.md and AGENTS.md (e.g. data/repositories.py is now data/exercise_repositories.py; ui/placeholders.py was removed).
Status: implementation baseline
Last updated: 2026-09-04

This document records the implementation details for Phase 0 and Phase 1 of
`docs/development-plan.md`. The development plan remains authoritative for
product scope, domain meaning, and acceptance criteria. This document defines
the first engineering shape used to implement that scope.

## 1. Delivery Objective

Phase 0 establishes a runnable, testable application foundation. Phase 1 adds
the first-launch data-root workflow and an empty desktop shell. Together they
must produce an application that can:

- create a new, independent TrainingFeedback data set;
- reopen a valid existing data set;
- reject invalid or unsafe data directories with readable errors;
- initialize and migrate a new SQLite database;
- start a native PySide6 window with explicit page navigation;
- close safely without losing committed data;
- create an immediate backup from the settings workflow;
- keep application files separate from user data.

Neither phase implements the exercise catalog, plans, training execution, or
next-day feedback UI. Those features consume the contracts established here.

## 2. Repository Layout

The first implementation uses a `src` layout:

```text
pyproject.toml
src/
  training_feedback/
    __init__.py
    main.py
    app.py
    domain/
      __init__.py
      enums.py
      models.py
      clock.py
      training.py
    data/
      __init__.py
      database.py
      migrations.py
      repositories.py
      data_root.py
    ui/
      __init__.py
      main_window.py
      home_page.py
      settings_page.py
      placeholders.py
    resources/
      styles/
tests/
  conftest.py
  test_data_root.py
  test_database.py
  test_migrations.py
  test_domain_models.py
  test_training_state.py
  test_app_lifecycle.py
```

Responsibilities are deliberately narrow:

- `main.py` creates the Qt application and invokes the application bootstrap.
- `app.py` coordinates configuration, data-root opening, repositories, and the
  main window. It does not contain SQL.
- `domain/` contains values, enums, validation, and state transitions. It does
  not know about Qt or SQLite.
- `data/database.py` owns SQLite connection setup and transaction boundaries.
- `data/migrations.py` owns schema versions and migration execution.
- `data/data_root.py` owns filesystem validation and data-set initialization.
- `data/repositories.py` owns SQL and maps rows to domain-facing records.
- `ui/` renders state and emits user commands. UI modules do not execute SQL or
  manipulate database connections directly.

## 3. Project Configuration

`pyproject.toml` must define:

- package name and version;
- Python version requirement, initially Python 3.12 or newer within the
  supported Windows environment;
- runtime dependency on PySide6;
- development dependencies for pytest and Ruff;
- the `training-feedback` application entry point;
- pytest test discovery and source path configuration;
- Ruff formatting and linting configuration.

The project must install without the old `Exercises@home` repository. No old
repository path, package name, database filename, or import is permitted in
runtime dependencies or application startup code.

## 4. Data-Root Contract

### 4.1 Directory shape

Every valid data set has this shape:

```text
<selected-root>/
  training_feedback.marker.json
  app_config.json
  training_feedback.sqlite3
  backups/
  exercise-images/
  exports/
  imports/
```

The marker is separate from application configuration. It identifies the
directory format before the database is opened. The marker is written only
after the root has passed safety checks and is created as part of a new data
set transaction at the filesystem-operation level.

The exact marker payload is:

```json
{
  "application": "TrainingFeedback",
  "data_format_version": 1
}
```

`app_config.json` is the authoritative configuration for this data set. Its
initial payload is:

```json
{
  "application": "TrainingFeedback",
  "config_version": 1,
  "data_format_version": 1
}
```

The configuration may later gain user preferences, but it must not become a
second source for schema state or a store for training facts.

### 4.2 Initialization rules

The data-root service exposes two operations conceptually:

```text
create_new(root_path) -> DataRoot
open_existing(root_path) -> DataRoot
```

`create_new` may operate only when the selected directory is empty, or when it
does not yet exist and its parent permits creation. It must reject a non-empty
unknown directory rather than deleting, merging, or overwriting its contents.

`open_existing` must validate, in order:

1. the path exists and is a directory;
2. the marker exists and contains the expected application identifier;
3. the data format version is supported;
4. `app_config.json` exists and is valid JSON with the expected application;
5. the database exists and can be opened;
6. the database schema version is supported and migrations can be applied.

The service must not scan sibling directories, search the workspace, infer a
database path from the old application, or silently create a replacement when
validation fails.

### 4.3 Filesystem errors

Domain-facing errors should distinguish at least:

- `DataRootNotEmptyError`: creation would risk existing data;
- `InvalidDataRootError`: marker or configuration is missing or malformed;
- `UnsupportedDataFormatError`: the data set is newer than this application;
- `DataRootAccessError`: permissions or filesystem access prevent the action;
- `DatabaseOpenError`: the database cannot be opened or validated;
- `BackupError`: backup creation failed.

The UI converts these errors to readable messages and does not expose stack
traces in normal operation. The original exception should remain available to
the application log and tests.

## 5. SQLite Contract

### 5.1 Connection setup

Each connection must configure:

```sql
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;
```

The database service must verify the foreign-key pragma after setting it. SQL
is allowed only in the data layer. Repositories receive an already configured
connection and never create ad-hoc connections with different settings.

The first schema migration creates an application metadata table:

```sql
schema_migration (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL
)
```

The database schema version is the greatest applied migration version. A
database with a greater version than the application supports is read as
incompatible and must not be modified.

### 5.2 Transaction rules

The database layer provides a transaction context used for every write that
represents one user action:

- begin transaction;
- execute all related repository writes;
- commit on success;
- rollback on any exception.

Migration execution also uses transactions, one migration at a time. A failed
migration leaves the database at its previous version. Phase 1 backup creation
must first flush and close the active application database connection, copy the
complete data root to a new empty destination, and then reopen the connection
if the application remains running.

### 5.3 Initial schema scope

The first migration creates the minimum relational shape from the development
plan:

```text
exercise
exercise_alias
exercise_guidance_revision
body_area
exercise_body_area
training_plan
training_plan_revision
training_plan_day
training_plan_action
training_plan_set
training_session
training_session_action
training_session_set
session_event
next_day_feedback
next_day_feedback_area
ai_export
plan_import
```

Phase 0 need not seed catalog or plan records. It must establish primary keys,
foreign keys, uniqueness rules, nullable actual-dose columns, ordering columns,
and immutable-history fields sufficiently for later phases. Detailed guidance
and dose content comes from `docs/initial-exercises-and-plan.md` in Phase 2 and
Phase 3.

## 6. Domain Contracts

Controlled values live in `domain/enums.py`, not as UI-only constants. The
initial enums are:

```text
DoseUnit: reps, seconds, minutes, breaths, free
ExerciseResult: exceeded, completed, partial, not_completed
SessionStatus: open, paused, completed, partial, aborted
AbortReason: discomfort, pain_or_injury, urgent_interruption,
             insufficient_time, other
FeedbackValue: significant_soreness, some_soreness,
               no_obvious_sensation, discomfort_or_injury
```

The domain model must preserve these invariants:

- `training_date` is assigned at session start and never rewritten;
- only one `open` or `paused` session may exist;
- only `open` and `paused` sessions accept execution changes;
- `completed` confirms planned dose but does not assert technique, pain, or
  fatigue facts;
- `exceeded` and `partial` require actual dose rows where work is known;
- `not_completed` does not fabricate actual dose;
- `NULL` means unknown and `0` means explicitly recorded zero;
- user notes are stored verbatim;
- final session status is `completed` only when every performed action is
  `completed` or `exceeded`; otherwise it is `partial`;
- terminal sessions cannot transition back to an active state.

The controller or domain service owns mutable training execution state. A
global dictionary or UI widget state must not act as the session controller.

## 7. Injectable Clock And 02:00 Rule

`domain/clock.py` defines a small clock protocol with `now()` and `today()`.
Production uses the system clock; tests use a fixed clock. All unfinished-
session labeling decisions receive the clock explicitly.

The rule is:

- before 02:00, an unfinished session retains normal resumable presentation;
- at or after 02:00, an unfinished session with an earlier stored
  `training_date` is labeled as previous-day training not finished;
- the stored date is never changed;
- if no unfinished previous-day session exists, starting a new current-day
  session is allowed.

Tests must cover 01:59, 02:00, and 02:01, including restart-like re-opening of
the same database.

## 8. Phase 1 Application Lifecycle

### 8.1 Startup sequence

The startup sequence is explicit:

1. create `QApplication`;
2. load the small locator under `%LOCALAPPDATA%\TrainingFeedback\`, if valid;
3. if no valid locator exists, show the data-root selection flow;
4. create or open the selected data root;
5. open the configured database and run supported migrations;
6. create application services and repositories;
7. construct `MainWindow` with explicit dependencies;
8. show the home page.

The locator contains only the last selected root path and no training data. An
invalid locator is ignored and replaced after a successful selection. The
application never scans for candidate roots.

### 8.2 First-launch selection

The first-launch dialog offers two explicit actions:

- create a new data root;
- open an existing TrainingFeedback data root.

The dialog must not treat an arbitrary existing directory as valid. Creation
and opening use the data-root service, so the UI only displays the result or a
mapped error. Cancellation exits cleanly without creating a database.

### 8.3 Main window

Phase 1 provides a minimal native shell with navigation entries for:

- Home;
- Exercise library;
- Plans;
- History;
- Settings.

Only Home and Settings need functional Phase 1 content. The other entries may
show clearly labeled placeholders, but navigation must be real and must not
pretend that later features are implemented.

The Home page displays:

- the selected data-root location;
- database/application readiness;
- a later-workflow placeholder for today's plan;
- a clear path to Settings.

The Settings page displays:

- current data-root path;
- open-location action;
- create immediate backup action;
- switch data-root action;
- safe application close remains available through the normal window control.

### 8.4 Shutdown sequence

On close, the application:

1. asks active pages to finish or cancel transient UI operations;
2. refuses shutdown only for a real unsaved write operation, with a readable
   prompt;
3. commits or rolls back the current transaction;
4. closes repositories and the SQLite connection;
5. persists the locator only after a valid root is open;
6. allows Qt shutdown.

Shutdown must not create a session, alter training facts, or silently discard a
database transaction.

## 9. Backup Contract

Phase 1 backup is a complete data-root copy, not a database-only export. The
destination must be selected explicitly and must be empty or newly created.

The backup service must:

- prevent the destination from being inside the source root;
- prevent copying onto an existing non-empty directory;
- close or safely checkpoint the database before copying;
- copy the marker, configuration, database, and all managed subdirectories;
- report failure without deleting the source;
- never overwrite an existing backup silently.

The source data set remains unchanged after a successful backup. A backup
timestamp may be shown in the UI, but timestamps must not be used as training
facts.

## 10. Test Strategy

All tests use `tmp_path` or an equivalent temporary directory. No test may
read `%LOCALAPPDATA%`, the repository root as a data source, or any real user
database.

Required Phase 0 tests:

- new-root creation and valid-root reopening;
- invalid marker, invalid config, unsupported format, and occupied-directory
  rejection;
- schema creation, migration idempotence, and migration rollback;
- foreign-key enforcement on every connection;
- transaction commit and rollback;
- enum validation and session state transitions;
- actual-dose and note invariants;
- 02:00 boundary behavior;
- proof that no old-project path is consulted.

Required Phase 1 tests:

- application bootstrap with a temporary locator and data root;
- first launch with no locator;
- invalid locator fallback;
- cancellation without data-root creation;
- main-window construction without SQL in UI modules;
- backup to an empty destination;
- rejection of occupied or nested backup destinations;
- clean shutdown and database reopen after shutdown.

Headless Qt tests may use `QT_QPA_PLATFORM=offscreen`. UI tests should verify
signals and service calls rather than pixel layout. Repository tests should
verify persisted results by reopening the temporary database.

## 11. Implementation Order

The work should be delivered in these increments:

1. Add project metadata, package layout, and test configuration.
2. Add domain enums, immutable value records, and injectable clock.
3. Add data-root marker/config validation and safe initialization.
4. Add SQLite connection, transaction context, and migration runner.
5. Add the first schema migration and schema tests.
6. Add session transition contracts and invariant tests.
7. Add application bootstrap and locator handling.
8. Add the main window, home/settings pages, and explicit placeholders.
9. Add backup service and settings integration.
10. Run formatting, linting, tests, and a minimal installed-package startup
    check.

Each increment should remain runnable. No Phase 1 UI should bypass an
unfinished Phase 0 service by implementing temporary SQL or filesystem logic
inside widgets.

## 12. Phase Gate

Phase 0 is complete when a temporary data root can be created, reopened, and
validated; migrations and domain invariants are covered by automated tests; and
the package installs without the old project.

Phase 1 is complete when the empty PySide6 application starts, supports first
launch and reopening through the selected root, displays the main navigation,
creates a safe complete backup, and closes/restarts without losing committed
data. Invalid and occupied directories must produce readable errors, and
application files must remain separate from user data.
