# TrainingFeedback Development Plan

Status: implementation through Phase 6 plus the data-root lifecycle (validation, switching, backup restore); Phase 7 refinement in progress; release acceptance pending\
Last updated: 2026-09-09

This is the authoritative product scope, domain model, and delivery plan.
The [initial catalog and plan proposal](initial-exercises-and-plan.md) defines
seed content and proposed doses. Current implementation status is summarized in
Section 9; requirements elsewhere are not claims that every release gate has
passed. Completed task history belongs in `.planning/archive/`.

## 1. Product Goal

Build a desktop-first personal training application that opens directly into a
clear training workflow, minimizes input during exercise, and preserves enough
structured facts and original user feedback for an external AI expert to create
high-quality future plans.

The application records and exports facts. It does not attempt to embed a
high-level AI coach in the first version.

```text
Open application
-> review today's plan or resume an unfinished session
-> start training
-> complete each exercise
-> record exceptions or extra work only when needed
-> pause, abort, or finish the session
-> provide short next-day feedback by trained body area
-> export complete evidence for an external AI expert
-> import or manually enter a confirmed revised plan
```

## 2. Repository And Runtime Boundary

This project starts in a separate repository. The previous `Exercises@home`
project remains an archive and optional human reference.

The new application must not:

- import modules from the old project;
- open, scan for, migrate, or modify the old database;
- inherit the old schema or Streamlit session state;
- include wardrobe management;
- include LAN, browser, mobile, authentication, or synchronization features;
- claim compatibility with old submission packages.

Old exercise names and guidance may be reviewed manually. Any selected content
must be deliberately rewritten or copied into the new application's own seed
data and thereafter owned by the new application.

## 3. First-Version Scope

The first usable version includes:

- a native PySide6 Windows application;
- a user-selected data root and a new SQLite database;
- an exercise catalog, initially focused on glutes, legs, and core;
- comprehensive exercise guidance suitable for human use and AI export;
- versioned training plans with per-set prescriptions;
- today's plan and an obvious start or resume action;
- exercise-level `exceeded`, `completed`, `partial`, and `not_completed` results;
- actual dose entry for exceeded and partial results;
- optional verbatim notes for every exercise result;
- session-level pause, abort, and finish operations;
- short next-day feedback generated from the main trained body areas;
- training history;
- JSON and Markdown exports for an external AI expert;
- confirmed plan revision import or manual entry;
- data backup and data-directory management;
- directory-based Windows packaging.

The first version excludes:

- embedded AI inference or automatic plan decisions;
- a pre-training light-mode choice;
- fixed sleep, energy, fatigue, pain, or RPE questionnaires;
- detailed subjective scoring during training;
- wardrobe data and clothing questions;
- trend dashboards and advanced analytics;
- cloud backup, accounts, network access, and mobile access;
- an installer or automatic updater;
- old data migration.

## 4. Core Product Decisions

### 4.1 Plans Drive Training

An exercise describes how a movement is performed. A plan describes what to do
on a specific training day. Dose, set sequence, rest, and plan-specific notes
belong to the plan, not the exercise catalog.

A plan action contains one or more ordered set prescriptions. This must support
both equal and unequal sets:

```text
Glute bridge: 2 x 15 reps
Glute bridge: 12 / 10 / 10 / 8 reps
Isometric glute bridge: 30 / 30 / 20 seconds
Dead bug: 8 reps per side
```

Each planned set stores a numeric value, a controlled unit, and whether the
value applies per side. Free-form display text may be generated or retained as
an additional note, but it is not the only dose representation.

Supported initial units:

- `reps`
- `seconds`
- `minutes`
- `breaths`
- `free`

All sets of one action use the same unit. `per_side` is stored separately from
the value and unit. Numeric doses and rest seconds must be finite and
non-negative; a `free` dose may omit its numeric value only with a non-empty
explanatory note. Day, action, and set orders are positive and unique within
their parent. Action phases are `preparation`, `main`, and `cooldown`.

Plan revisions move from `draft` to `active` to `superseded`. Editing an active
revision creates a new draft. A saved draft has a name, at least one day, an
action in each day, and sets in every action; it may reference guidance awaiting
approval. Activation additionally requires active exercises with complete,
reviewed, explicitly user-approved active guidance. The complete prescription
and differences from the current revision are shown before confirmation.
Saving a draft does not activate it. Superseding the previous revision and
updating the active revision pointer form one transaction.

The editor supports equal-set and individual-set entry; switching modes must
not silently discard unsaved values. Revision diffs cover action additions,
removals and ordering, phase, rest, notes, set values, units, per-side flags,
and plan purpose without mutating either revision.

### 4.2 Exercise Results Stay Simple

Each exercise presents four result actions:

```text
Exceeded | Completed as planned | Partially completed | Not completed
```

Behavior:

- `completed`: one click confirms that the prescribed sets and dose were done;
- `exceeded`: actual sets and values are required so the excess is measurable;
- `partial`: actual completed sets and values are required;
- `not_completed`: no fabricated actual dose is stored;
- all four states allow an optional free-text note;
- the original note is preserved verbatim.

Clicking `completed` confirms dose completion only. It must not silently record
good technique, absence of pain, absence of fatigue, or any other subjective
fact.

### 4.3 Session Controls

The fixed session controls are:

```text
Pause training | Abort training | Finish training
```

`Pause training`:

- persists all current progress;
- changes the session to `paused`;
- records the pause time;
- requires no reason;
- can survive application restart;
- returns to the home page as a resumable session.

`Abort training`:

- ends the session permanently;
- requires a reason category and allows a free-text explanation;
- never forces the user through another long questionnaire.

Initial abort reasons:

- physical discomfort;
- pain or injury;
- urgent interruption;
- insufficient time;
- other.

`Finish training` requires a recorded result for every planned action, then
derives a proposed final result:

- all actions completed or exceeded -> `completed`;
- any action partial or not completed -> `partial`.

The user confirms the final save but does not repeat exercise feedback.
An unanswered action must not be silently converted into `not_completed`.
Terminal sessions cannot resume; narrowly scoped note corrections are audited
without rewriting execution results.

Session statuses are:

- `open`
- `paused`
- `completed`
- `partial`
- `aborted`

Only one `open` or `paused` session may exist at a time.

### 4.4 The 02:00 Boundary

`training_date` is assigned when a session starts and never changes afterward.
The 02:00 boundary controls recovery and labeling of unfinished sessions; it
does not rewrite dates and does not make the entire day belong to yesterday.

- Before 02:00, an unfinished late-night session remains resumable with its
  original `training_date`.
- At or after 02:00, an unfinished session whose `training_date` is earlier than
  the current calendar date is explicitly shown as "previous-day training not
  finished".
- Such a session must never be relabeled as today's training.
- If no unfinished previous-day session exists, the user may start a new
  session for the current calendar date immediately.
- The home page always displays the session's stored training date.

All date-boundary behavior must be implemented by one injectable clock/domain
function so it can be tested deterministically.

### 4.5 Next-Day Feedback

Next-day feedback is not a general body questionnaire. It is generated from the
primary body-area snapshots of exercises that were actually performed in the
previous session.

Warm-up, mobility, breathing, and cooldown exercises do not create soreness
questions unless explicitly configured to do so. `not_completed` exercises do
not contribute body areas. `completed`, `exceeded`, and `partial` exercises do.

For each distinct main area, display exactly one choice:

```text
Significant soreness affecting activity
Some soreness
No obvious sensation
Discomfort or injury
```

The page also contains one optional overall note. Unanswered areas remain
unknown; the application must not select a default answer.

Initial display labels are expected to include:

- glutes;
- front thigh;
- back thigh;
- core.

The stored feedback uses body-area snapshots captured for the session so later
exercise-catalog edits cannot change historical meaning.

### 4.6 External AI Handoff

The application exports evidence but does not make an AI decision.

Each handoff provides JSON for machine processing and Markdown for direct human
review. The export must identify provenance and distinguish:

- stable exercise guidance;
- the exact plan revision used;
- planned set doses;
- actual exercise and set results;
- verbatim user notes;
- pause or abort events and reasons;
- next-day body-area feedback;
- relevant earlier plan revisions and training summaries;
- prior externally supplied adjustment reasons.

Guidance such as "avoid lumbar compensation" must never appear as though the
user reported lumbar compensation.

An external AI expert may return a revised plan. The application must validate
it, show a human-readable diff, and require user confirmation before activation.
Applying it creates a new immutable plan revision and records:

- the previous revision;
- the source training session or export;
- the external rationale;
- the confirmed new revision;
- the confirmation time.

No active plan is silently overwritten.

The application owns the versioned contract; it is not tied to a particular AI
provider. `domain/handoff.py` defines the external response schema
(`training_feedback.plan`, version 1) and validation. `data/handoff.py` produces
the evidence JSON, Markdown, and response schema. The current UI imports JSON
files into drafts and retains the source in the managed imports directory.
Clipboard import is not part of the current workflow. Validating and saving an
import never imply activation or user approval.

## 5. Exercise Guidance Model

Exercise guidance must be sufficiently complete for safe execution and
high-quality external analysis. Each exercise supports:

- canonical name and aliases;
- category and equipment;
- purpose;
- primary and secondary body areas;
- starting position;
- ordered execution steps;
- breathing;
- tempo or pacing;
- intended sensations;
- common compensations and errors;
- stop criteria;
- regressions;
- progressions;
- applicability and cautions;
- image references;
- active state.

The guidance model and training evidence are separate. Session history freezes
the exercise name, primary body areas, guidance revision identifier, and plan
prescription needed to interpret that session.

`Glute bridge` is the canonical object. `Standard glute bridge` is an alias,
not a second exercise.

Canonical names and aliases must not collide across exercises. Lookup may
normalize whitespace, Unicode, and case for matching; stored names, guidance,
and user text remain verbatim. Exercise identities and body-area relationships
are relational; guidance content is validated JSON in immutable content
revisions. Plan prescriptions remain normalized day/action/set records.

### 5.1 Guidance Review And Activation

Guidance review uses `draft -> pending_review -> approved -> active`, with
`rejected` available during review. Incomplete guidance can be saved as a draft
but cannot be approved or activated. Missing images are explicit and do not
hide text or stop criteria; equipment may be an empty list when none is needed.
Field-level completeness is not proof of exercise-specific content quality.

External review evidence records reviewer type, source, review note, and review
time. Approval requires an explicit user action and approval time; seed values
must not supply either. The review form records external review evidence; the
application performs no expert reasoning. Only approved guidance can activate.
Editing guidance creates a new content revision, and rejecting a review leaves
the previous active guidance unchanged. Related review/activation writes are
transactional, and previous content remains available for historical sessions.

## 6. Minimum Domain Model

Names below describe responsibilities; final SQL naming may vary while keeping
the relationships and invariants.

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

Important invariants:

- plan revisions are immutable after activation;
- session actions snapshot their plan prescription;
- completed history is never rewritten by catalog or plan edits;
- actual dose remains `NULL` when unknown;
- `0` means an explicitly recorded zero, not unknown;
- user notes are preserved verbatim;
- one session action maps to ordered planned and actual set rows;
- one session can have at most one next-day feedback record;
- foreign keys are enabled for every connection;
- final session save and its action results commit transactionally.

## 7. User Data Directory

The user chooses a data root, for example:

```text
D:\TrainingFeedbackData\
|- training_feedback.marker.json
|- training_feedback.sqlite3
|- app_config.json
|- backups\
|- exercise-images\
|- exports\
`- imports\
```

`app_config.json` inside the selected root is the authoritative configuration
for that data set. A tiny locator under `%LOCALAPPDATA%\TrainingFeedback\` may
remember the last selected root so the application can find it at next launch;
the locator contains no training data and is not an alternate configuration
source. If it is absent or invalid, the application asks the user to select a
data root.

First launch supports:

- create a new data root in an empty directory;
- open an existing valid TrainingFeedback data root.

Settings later support:

- show and open the current data root;
- create an immediate backup;
- copy the complete current data root to a new empty directory;
- switch to another valid data root.

The application must validate an application marker and schema version before
opening a directory. It must refuse silent overwrite, partial copy, old-project
database import, and automatic directory scanning.

`training_feedback.marker.json` identifies `application: TrainingFeedback` and
`data_format_version: 1`. Configuration uses the same application/format and
`config_version: 1`; database migration state belongs in SQLite, not in the
configuration. Opening validates the marker and configuration before accessing
the database. Unsupported newer database schemas must not be modified.

A backup copies the complete data root, including marker, configuration, images,
exports, and imports, to an explicitly selected empty destination outside the
source root. The running application uses SQLite's online backup API for a
consistent database copy, rather than copying an open database file directly.
Failures are reported, never delete the source, and clean up the incomplete
copy so a partial backup is never presented as successful. Recovery uses the
normal open/switch flow: select the backup copy as the data root. There is no
overwrite-style restore.

Current settings provide location display/open, complete backup, evidence
export, and switching to another valid data root. Switching validates and
prepares the target, rebuilds the main window and services in-process, and
commits the locator only after preparation succeeds; any failure keeps the
previous root, window, and database usable. An `open` training session blocks
switching until paused; a paused session stays in its original root and can be
resumed after switching back.

Application upgrades must not overwrite the database, images, exports, or
backups.

## 8. Application Architecture

```text
src/training_feedback/
|- main.py            # Qt entry point
|- bootstrap.py       # startup coordination (data-root location/selection)
|- app.py             # ApplicationContext composition root
|- ui/                # PySide6 pages and dialogs (no SQL)
|- domain/            # pure rules and value objects (no Qt, no SQL)
|- application/       # use-case services coordinating domain and repositories
`- data/              # SQLite repositories, migrations, data root, backup, seed, handoff
```

`packaging/` lives at the repository root, alongside `src/` and `tests/`.
See `AGENTS.md` for concrete layer responsibilities and `pyproject.toml` for
runtime and tooling dependencies. The layering rules below apply.

Architecture rules:

- UI never executes SQL;
- repositories own SQLite statements and row mapping;
- domain services own session transitions and validation;
- a session controller owns mutable execution state;
- pages communicate through explicit models, commands, and signals;
- filesystem operations such as backup, import, and export have dedicated
  services;
- tests inject a clock and temporary data root;
- no global Streamlit-like session dictionary is introduced.

SQLite connections enable and verify foreign keys and configure a busy timeout.
One user action commits or rolls back as a unit. Schema migrations are
append-only, versioned, and transactional per migration; later changes must not
edit an already applied migration. Failed migrations preserve the prior version.
UI tests may use offscreen Qt; all tests use temporary databases and locators,
never real user data. Date-boundary checks cover 01:59, 02:00, and 02:01.

## 9. Delivery Phases

### Current Status (2026-09-09)

| Phase | Current status | Remaining acceptance or release work |
| --- | --- | --- |
| 0–1 | Foundation, data-root shell, root validation/switching, and backup restore implemented and regression-verified | Visual acceptance of the startup error and switch dialogs on a real desktop session. |
| 2–3 | Catalog review and versioned-plan workflows implemented and tested | Seed guidance is still generic draft content; review and explicit plan confirmation are required before real activation. |
| 4–6 | Execution, feedback/history, and external handoff implemented and regression-verified | Continue preserving their acceptance criteria during refinement. |
| 7 | First workflow refinement slice implemented and tested | Multiple real sessions and an external expert's explainable revision based on actual feedback. |
| 8 | Pending; current packaging spec produces a single-file development smoke build | Directory-based release, independent runtime, and upgrade/data isolation. Backup restore is regression-verified with synthetic data and documented in Section 7. |

Automated and synthetic-data checks establish implementation behavior. They do
not complete real-use, content-review, or release acceptance. Phase requirements
below remain the acceptance checklist; dated test runs belong in task records.

### Phase 0: Repository And Contracts

- establish the independent repository and package layout;
- select Python, PySide6, packaging, formatting, and test tooling versions;
- write the new schema and migration runner;
- define controlled enums and state-transition rules;
- add temporary-database tests for schema and session invariants.

Acceptance:

- the project installs without the old repository;
- a synthetic data root can be created and reopened;
- tests prove the old database path is never consulted.

### Phase 1: Data Root And Application Skeleton

- implement first-launch data-root selection;
- create and validate `app_config.json` and SQLite;
- implement the main window and navigation;
- implement backup creation and safe shutdown.

Acceptance:

- the empty application starts, closes, and restarts using the selected root;
- invalid or occupied directories produce readable errors;
- application files and user data remain separate.

### Phase 2: Exercise Catalog And Guidance

- seed the approved first exercise set;
- implement list, search, detail, add, edit, activate, and deactivate;
- implement comprehensive versioned guidance and image placeholders;
- treat `Standard glute bridge` as an alias of `Glute bridge`.

Acceptance:

- every seeded exercise has complete text guidance or an explicit incomplete
  status;
- missing images do not hide stop criteria or text guidance;
- catalog edits do not modify historical snapshots.

### Phase 3: Versioned Plans

- implement plans, immutable revisions, days, actions, and per-set doses;
- support equal and unequal set prescriptions;
- implement plan maintenance and readable revision diffs;
- seed the initial proposal after explicit dose review.

Acceptance:

- the UI represents `2 x 15`, `12/10/10/8`, per-side doses, timed holds, and
  breaths without relying only on free text;
- activating a revision preserves all earlier revisions.

### Phase 4: Training Execution

- implement start, resume, action selection, and fixed session controls;
- implement exceeded, completed, partial, and not-completed action results;
- require actual dose only where needed;
- implement transactional finish and abort flows;
- implement the 02:00 unfinished-session labeling rule.

Acceptance:

- normal completion requires one action per exercise and no long form;
- core controls never require scrolling;
- pause survives process restart;
- an unfinished prior-day session is never presented as today's session;
- unknown subjective facts remain unknown.

### Phase 5: Next-Day Feedback And History

- derive prompts from performed primary training-area snapshots;
- implement four-state area feedback and one optional note;
- implement session and action history;
- allow narrowly scoped note correction with an audit record.

Acceptance:

- only relevant main areas are shown;
- unanswered values are not defaulted;
- old sessions remain readable after exercise and plan edits.

### Phase 6: External AI Handoff

- define versioned JSON schema and Markdown rendering;
- export guidance, plans, actual execution, original notes, and next-day data;
- validate external plan input;
- show plan diffs and require confirmation before activation.

Acceptance:

- exports clearly identify provenance and unknown values;
- a round trip creates a new plan revision without changing the old one;
- malformed or partial imports cannot leave half-written plans.

### Phase 7: Real-Use Refinement

- use the application over multiple sessions;
- measure unnecessary clicks and unclear states;
- revise workflow before adding features;
- let an external AI expert review exported evidence and the initial plan;
- remove controls that real use shows are unnecessary.

Acceptance:

- the training workflow remains usable without developer intervention;
- actual feedback can support an explainable plan revision.

### Phase 8: Windows Packaging

- produce a directory-based Windows build;
- use `icon/TrainingFeedback.ico` as the packaged Windows executable icon;
- verify operation without a development environment;
- verify upgrades against an existing copied user data root;
- document backup and recovery.

Acceptance:

- the packaged application runs independently;
- upgrading application files does not modify user data;
- backup restore is tested before release.

## 10. First Usable Release Definition

The first usable release is complete when a user can:

- choose a data directory;
- back up the complete data root and switch to another valid root;
- inspect the initial exercise guidance;
- inspect and activate a plan with per-set doses;
- start or resume training;
- record every exercise with one of four result states;
- record exact excess or partial work;
- pause, abort with a reason, or finish;
- restart without losing a paused session;
- submit relevant next-day area feedback;
- review history;
- export complete JSON and Markdown evidence for an external AI expert;
- confirm a revised plan without losing the previous plan;
- run the packaged Windows application without Streamlit or the old project.

The release also requires reviewed exercise-specific seed guidance and the
Phase 7 real-use and Phase 8 packaging/recovery acceptance above. A package
version number alone does not establish release readiness.

## 11. Deferred Decisions

The following remain intentionally open until implementation evidence or real
use resolves them:

- the final prescribed dose for the initial plan;
- additional exercise images and later exercise batches.

Clipboard import, provider-specific adapters, advanced trend analysis,
installers, and automatic updates are optional later scope, not unresolved
first-version requirements. The current application-owned JSON/file contract
is defined in Section 4.6.
