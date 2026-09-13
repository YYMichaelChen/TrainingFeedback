# TrainingFeedback Development Plan

Status: implementation through Phase 6 plus the data-root lifecycle (validation, switching, backup restore); Phase 7 refinement in progress; Phase 8-B1 candidate preparation implemented and smoke-verified on the build machine; release acceptance pending\
Last updated: 2026-09-13

Current implementation: 0.4.0, following the separately preserved 0.3.1 correction
candidate. Both are tagged releases (v0.3.1, v0.4.0) and passed a contract-by-contract
implementation acceptance review on 2026-09-13 (full test suite, Ruff, and source
review against the acceptance contracts below). Independent runtime/desktop
acceptance, actual content review and W4 remain pending.

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

### Current Status (2026-09-13)

| Phase | Current status | Remaining acceptance or release work |
| --- | --- | --- |
| 0–1 | Foundation, data-root shell, root validation/switching, and backup restore implemented and regression-verified | Visual acceptance of the startup error and switch dialogs on a real desktop session. |
| 2–3 | W1–W3 implemented and independently code-reviewed for 0.3.0: transactional exercise editing, fresh drafts, complete Chinese guidance views/forms, revision selection, 14 exercise-specific bundled drafts, and explicit delivery to existing roots | Real external guidance review and explicit user approval; separate confirmation of the complete initial plan. Include the updated guidance windows in packaged desktop acceptance. |
| 4–6 | Execution, feedback/history, and external handoff implemented and regression-verified | Continue preserving their acceptance criteria during refinement. |
| 7 | First workflow refinement slice implemented and tested | Multiple real sessions and an external expert's explainable revision based on actual feedback. |
| 8 | Directory-based build plus repeatable 8-B1 candidate preparation implemented and smoke-verified on the build machine; the build isolates binary discovery, records a manifest, and the synthetic fixture covers the required data classes | Execute 8-B2: independent Windows runtime acceptance, upgrade/data isolation on a copied real-class root, packaged backup/restore drills, and real-desktop scaling checks. Backup restore is regression-verified with synthetic data and documented in Section 7. |

Automated and synthetic-data checks establish implementation behavior. They do
not complete real-use, content-review, or release acceptance. Phase requirements
below remain the acceptance checklist; dated test runs belong in task records.

### Delivery Status For 0.3.0 And Remaining Work

Version **0.3.0 delivered W1–W3** and their acceptance-review fixes. Follow-up
0.3.1/0.4.0 implementation is specified below; both are now tagged releases whose
implementation passed the 2026-09-13 contract-by-contract acceptance review. The
next packaging acceptance gate is **8-B2**, using the identified 0.4.0 candidate
with separate evidence for the preserved 0.3.1 candidate. Guidance
content review, explicit user approval, and initial-plan confirmation remain
separate participant actions. This implementation delivery does not complete
the first usable release defined in Section 10. An unavailable independent
Windows environment must not block implementation delivery or be reported as a
passed acceptance check.

| Work item | Status and dependency | Reviewable result |
| --- | --- | --- |
| W1 — Exercise-edit correctness | Complete; 0.3.0 | One transactional save, honest new-draft state, and working alias/body-area edits. |
| W2 — Readable guidance editing and review | Complete; 0.3.0 | Complete Chinese guidance forms/views with explicit revision selection and approval; original untouched text and usable small-window controls. |
| W3 — Exercise-specific content and existing-root delivery | Implementation complete; 0.3.0; actual content review remains pending | All 14 launch guides, including the initial plan's 11, are available as drafts; existing users can explicitly receive selected drafts. |
| Local personal go-live | In progress; 0.4.1 installed outside the repository with a separate data root | Verified installed program files, real data root, approved guidance for the plan's exercises, an activated plan revision, and a local self-check that is not 8-B2. |
| 8-B2 — Packaged acceptance | P0 release gate; run the identified current candidate when an independent environment is available | Candidate-specific independent-runtime, upgrade, recovery, and display evidence. |
| W4 — Real use and expert revision | After packaged acceptance and guidance/plan confirmation | Multiple real sessions plus one evidence-based plan-revision cycle. |

#### Completed Preparation: Acceptance And Review Materials

Executable acceptance materials and external review inputs have been prepared
using the 0.3.0 candidate. An independent Windows environment
is currently unavailable; actual external review and user approval are also
pending. Preparation alone does not require a version bump, a new application
interface, or a schema migration.

| Remaining work | Work that can proceed now | Completion evidence |
| --- | --- | --- |
| Packaged acceptance preparation | The 0.3.0 materials are prepared; refresh candidate files, baselines and forms for each follow-up build. | An operator can execute the ten scenarios without reading application source. |
| Guidance and plan review preparation | All 14 seed drafts and the complete initial plan are exported with review request, checklist and validated example; actual review is pending. | Complete, version-identified materials; no invented review facts or personal training records. |
| 8-B2 independent Windows acceptance | Keep environment-dependent scenarios not run; execute when the environment is available and turn failures into reproducible repair tasks. | Candidate-specific passing evidence for runtime independence, upgrade, recovery, and desktop checks. |
| W4 real-use revision cycle | Prepare the observation procedure; begin after technical acceptance, guidance approval, and full plan confirmation. | At least three real sessions as the initial verification sample, next-day feedback workflow, and one justified revision cycle. |

The [packaged acceptance runbook](packaged-acceptance-runbook.md) owns technical
sample preparation and execution. The [guidance review runbook](guidance-review-runbook.md)
owns review inputs, return requirements, and applying actual responses. Guidance
content and proposed doses remain owned by
[initial-exercises-and-plan.md](initial-exercises-and-plan.md) and the seed.
Generated packages, synthetic roots, candidate hashes, and dated verification
results stay in local task artifacts; personal evidence stays in the user's
data root. The three root task records track only the current development task.

Review all 14 launch guides, prioritizing the initial plan's 11 references.
Content review and acceptance-environment preparation can proceed concurrently.
The user explicitly approves the required guidance and separately confirms the
entire plan. Once 8-B2 also passes, conduct W4. Record unanswered feedback as
unknown; the session sample is a software-verification starting point, not a
training frequency or dose prescription. Complete the actual evidence export,
external rationale, imported draft, reviewed diff, and explicit activation
cycle before closing that gate.

Prioritize reproduced data/history errors, workflow blockers, then redundant
operations and unclear messages. Each repair needs reproduction steps,
expected behavior, and a focused acceptance case. Identify any changed candidate
and rerun affected packaged checks; retain earlier results as historical.

W1–W3 are implementation work; completion does not assert an external expert
review, user approval, or real training. Those events require their actual
participants and evidence. If a candidate changes during this work, identify
the new build and rerun affected packaged scenarios before release. Assign
subsequent application versions when their delivered scope is known.

#### Follow-Up Releases: 0.3.1 Corrections And 0.4.0 Review Workflow

Status (2026-09-13): both delivered as tagged releases (v0.3.1, v0.4.0) with
source identity, manifest, regression results, and packaged evidence preserved
per candidate. Their implementations passed a contract-by-contract acceptance
review against the requirements below (full suite, Ruff, source review).
Runtime-independent acceptance and actual content review remain open gates;
neither is implied by an implementation version.

0.3.1 implements prescription display and feedback/history window corrections;
its candidate and source snapshot are preserved separately. The acceptance
contracts are:

- Show each set's order, value, unit, per-side flag and original note in plan
  details/activation, training and history. Free doses without a numeric value
  display their explanation. Numeric doses must not hide their accompanying note.
- Training/history use frozen action and set prescription notes, phase and rest.
  Markdown session exports include these existing snapshots alongside the same
  JSON facts. Rendering does not update storage or infer missing actual doses.
- Open next-day feedback as a separate window bounded by the available screen;
  scroll its content while keeping submission state and action fixed. History
  details scroll independently of the export action. Unknown responses and audited
  note correction retain their existing meaning.

0.4.0 implements explicit plan revision and review targets:

- Select one plan revision. Default to the active revision, or the newest draft
  if no active revision exists; import/clone selects the newly created revision.
  Editing, guidance review, diff and activation target that displayed revision.
  Published revisions are read-only and can be cloned; a stale target is rejected
  and refreshed without performing the action on a different revision.
- Show the original import rationale, source references and managed original
  file for the selected imported revision. Subsequent draft editing does not
  rewrite that original evidence. Importing still creates only a draft.
- Record the external review occurrence separately from approval. The occurrence
  input starts empty and accepts a calendar date or a timezone-aware datetime,
  retaining the supplied precision. An application use case validates the review
  and explicit confirmation, then generates approval time from an injectable clock
  and performs transactional approval/activation. Changing guidance selection
  clears the current input and confirmation; saved evidence remains read-only.
- Existing review times remain unchanged; earlier UI versions may have stored the
  submission time. Never infer or backfill their actual external occurrence.

The plan repository exposes a read-only import lookup by plan/revision and an
optional expected-revision argument for activation. The latter compares the
displayed draft in the same write transaction, rejecting changed content.
Existing repository callers remain compatible. ExerciseService's confirmation
use case owns approval time through Clock; lower-level review APIs remain usable.

0.4.1 implements first-launch data-root selection corrections found during the
local personal go-live:

- Data-root metadata failures report fixed, translatable messages. They never
  interpolate a filename or a full path into user-visible text, so a Chinese
  interface cannot fall back to raw English. Selecting an empty directory in open
  mode states that the directory is empty and points at the create flow.
- First launch prefills a documents-folder default data root and preselects
  create for a nonexistent or empty path, open for a path that already holds a
  marker file. An occupied path is not prefilled. The suggestion is a suggestion
  only: confirmation is still explicit, nothing is created or opened without it,
  and switching data roots later prefills nothing.
- The suggestion checks that single path through a read-only data-layer helper.
  It never scans directories for candidate roots and never opens a database, so
  no migration can run before the user confirms.

All three releases reuse database schema 13, evidence v1 and plan v1. Exercise/plan
content and dose proposals do not change. Add focused regressions before each
fix, run the full suite and lint, build and preserve each candidate separately.
Test v0.2.2 copied-root migration as well as adjacent-version opening, backup and
restore. Actual independent-desktop checks must identify the tested candidate.

#### 1. Prepare The Acceptance Candidate (8-B1)

Status (2026-09-10): complete on the build machine. This status covers the
repeatable toolchain, manifest, synthetic fixture, local regressions, and a
packaged startup smoke check; it does not claim any 8-B2 independent-machine
or real-desktop result.

Reuse `packaging/build.ps1`, the pinned toolchain, the build manifest, and
`packaging/prepare-acceptance-data.ps1`. The existing
[packaged-acceptance runbook](packaged-acceptance-runbook.md) owns execution
steps and its ten-row evidence table. Keep fixture data and its synthetic
approval metadata isolated from production seed content. Further build-tool
changes should address a reproduced acceptance failure or a changed candidate
requirement.

#### 2. Execute Packaged Acceptance (8-B2)

Status (2026-09-13): transfer preflight was rerun for the preserved 0.2.2,
0.3.1, and 0.4.0 programs. All 630 manifest entries, the upgrade/adjacent
original-copy pairs, and the refreshed 689-file transfer archive passed local
integrity and archive round-trip checks. The refreshed package adds the
runbook-required candidate verification record without changing any program
candidate. No independent Windows environment or real-desktop evidence was
available, so all ten 8-B2 scenarios remain not run. The sole current user has
explicitly deferred this gate: local build-machine operation is sufficient for
current personal use. The deferral does not mark 8-B2 as passed, but it does
remove it as a blocker for ordinary local use and continued non-release work.
Execute it before broader distribution, adding users, or claiming formal release
acceptance.

- Run the complete program directory in an independent Windows x64 environment
  with no Python, Conda, source checkout, or access to the build environment.
  A clean VM or separate machine is suitable; a new account on the build
  machine alone is insufficient evidence of runtime independence.
- Exercise first launch, new-root creation, reopening, invalid/occupied-root
  errors, cancellation, and restart. Include Chinese and space-containing
  program/data paths and ordinary non-administrator operation.
- On an isolated representative root, replace only application files with the
  candidate. For the migration gate, generate the sample from this repository's
  v0.2.2 source and open/close it with the corresponding previous-version build
  before capturing the baseline. Preserve an original never opened by the candidate,
  and upgrade a separate copy. Record both versions;
  same-version relocation is not cross-version upgrade evidence. Close the
  application before taking baselines. Compare logical records and historical
  snapshots after launch, and resource-file hashes; allow only declared schema
  migrations, without rewriting prior facts.
- Also test adjacent-version opening: use the exact preserved 0.3.1 source and
  executable to prepare a schema-13 baseline for 0.4.0. The separate 0.3.1
  candidate uses a 0.3.0 baseline. Preserve originals and compare copies as above.
- Through the packaged UI, back up the complete root while open, close the
  application, open the backup copy through the normal flow, resume the paused
  session, inspect history/feedback, and export evidence again. Verify source
  isolation and readable rejection of an invalid or occupied destination.
- On a real desktop, check 100%, 125%, and 150% scaling at recorded screen
  resolutions, including 1366x768 and 1920x1080 where available. Cover startup
  errors, root switching, long Chinese text, and many actual-set rows; pause,
  abort, and finish must remain accessible without scrolling the content.

Exit: record candidate/environment identity and evidence for every scenario;
reproduce and fix blocking failures, then rerun affected checks. Offscreen
tests and process-survival smoke checks are supporting evidence only. If the
independent environment or desktop checks are unavailable, leave those rows
not run and Phase 8 acceptance pending.

#### 3. Complete Guidance And Confirm The Initial Plan (Phases 2–3)

##### W1. Make Exercise Editing Atomic And Preserve Review Meaning

Status: implemented and reviewed for 0.3.0. The pre-W1 editor committed
metadata separately from the guidance revision, copied prior approval facts
into new drafts, and omitted editable aliases and primary areas. The following
requirements and acceptance cases remain regression contracts.

- Add one exercise-edit application use case covering metadata, aliases,
  editable body-area assignments, and a new guidance draft in one transaction.
  Detect duplicate names/aliases and invalid input before committing; a failed
  later write rolls back the complete user action.
- Save the fields the editor offers. Editing primary areas must preserve
  secondary-area assignments that the user has not edited. Existing session
  names, body-area participation, prescriptions, and guidance references remain
  frozen; reopening a renamed seeded exercise must not duplicate or replace it.
- Enforce fresh-draft review state in the application/domain path for both
  creation and editing, including a copied active or approved guide. Do not
  inherit reviewer, review date, or user-approval facts as approval of the new
  text. Keep the prior revision and active pointer until explicit approval.
- Audit other draft-creation callers so the same invariant applies to future
  bundled updates. Preserve free-text content verbatim.

Primary scope: `application/exercise_service.py`, `domain/exercises.py`,
`data/exercise_repositories.py`, `ui/exercise_editor.py`, and focused exercise/UI
tests; inspect seeding only as needed for rename/reopen behavior. Keep SQL in
repositories and write orchestration in the application layer.

Acceptance: injected failure leaves no metadata, alias, area, or revision
changes after reopening; valid edits persist every editable field; duplicate
aliases cause a full rollback; editing an approved guide creates an unapproved
draft; old approval records, active pointers, and historical exports retain
their meaning. Cover both new and existing exercises with temporary roots.

##### W2. Make The Complete Guidance Readable And Reviewable

Status: implemented and reviewed for 0.3.0. Acceptance fixes preserve untouched
line separators, keep step numbering consistent after structural edits, carry
the displayed revision into editing, prevent long revision identities from
forcing horizontal scrolling, and keep detail-window actions reachable.

- Replace the normal workflow's raw guidance JSON/dictionary display with
  labeled Chinese fields and ordered lists. Cover every guidance requirement
  in `docs/initial-exercises-and-plan.md`, including intended sensations,
  compensations, regressions/progressions, equipment, applicability, cautions,
  and explicit image availability.
- Show the current active revision separately from drafts. Let the user select
  the revision being edited/reviewed, read its full content and changes, and see
  the actual review source and state. Do not silently review a different
  revision from the one displayed.
- Reuse the existing approval transaction and explicit checkbox. Saving a
  draft, cancelling review, or merely installing content never approves it.
  User-authored text must survive form loading and saving without rewriting.
- Check long Chinese content and small-window layouts, with readable errors
  and reachable save/cancel/approval controls.

Primary scope: exercise detail/editor/review UI and shared Chinese labels;
reuse application services from W1. A reusable guidance view/form is justified
by these three consumers; a general UI framework is outside this slice.

Acceptance: all required content is accessible without reading JSON; revision
identity and draft/active states are unambiguous; cancellation makes no writes;
activation requires deliberate approval; form round trips preserve verbatim
text. Add focused Qt checks and include changed dialogs in 8-B2 desktop checks.

##### W3. Deliver Exercise-Specific Drafts To New And Existing Roots

Status: implementation reviewed for 0.3.0. All 14 bundled guides remain
unreviewed drafts until actual external review and explicit user approval.

- Write exercise-specific guidance owned by
  `docs/initial-exercises-and-plan.md` and the seed catalog. Prepare the initial
  proposal's 11 referenced exercises first; complete the other three launch
  exercises before release. Required-field validation checks structure, while
  actual external review checks content. Missing images may remain explicit.
- Separate custom-exercise draft defaults from bundled launch content. A new
  root receives the new content as drafts, with no invented review or approval.
  Neither generic defaults nor proposed doses become user facts.
- Provide an explicit local action to preview available bundled guidance and
  create selected new drafts for existing exercises. Reuse the current revision
  and review model; startup seeding must not overwrite existing guidance, user
  edits, active pointers, or plans.
- Track a stable bundled content identity/version and enough provenance to
  avoid duplicate drafts on repeat acceptance or restart. Existing roots may
  lack that identity: make ambiguous or renamed matches explicit instead of
  guessing from a mutable name, overwriting edits, or creating duplicates.
  Add a schema migration only if persisted identity requires one; migrations
  remain append-only and must not fabricate historical provenance.
- Allow skipping or cancelling an update with no writes. Accepting selected
  drafts is one transaction; a failure must not leave a partial batch. Record
  actual external review evidence and obtain explicit user approval through W2.
  Confirm the complete initial plan separately before activation.

Primary scope: the authoritative initial-content document, `data/seed/`, the
exercise application/repository boundary, and a small update-preview UI using
W2. This is delivery of application-owned local content, not an application
auto-updater or an external-provider integration.

Acceptance: a new root has 14 exercise-specific drafts; a pre-update temporary
root can receive selected new versions without losing custom text or approvals;
repeating the update creates no duplicates; ambiguous matches and cancellations
do not modify data; injected failure rolls back the batch. Paused/completed
session snapshots and prior exports remain interpretable after update, reopen,
and backup/restore. Real review and plan confirmation are recorded separately
from synthetic test approvals.

Exit: all launch guidance meets the documented content/review requirements,
and the user has a deliberately confirmed usable plan. Missing images may
remain explicit; adding image assets or more exercises is not a prerequisite.

#### 4. Validate Real Use And Close The Release Gates (Phase 7)

This is W4. It requires real training and external expert participation;
automated tests or synthetic fixtures cannot complete it.

- After technical acceptance and guidance/plan confirmation, use the packaged
  application for at least three real sessions as the initial verification
  sample and cover the next-day feedback workflow, leaving unanswered facts
  unknown. Record friction
  such as unnecessary clicks, unclear save states, or inaccessible controls;
  keep personal training evidence in the user's data root, outside Git.
- Complete one genuine evidence-export -> external expert rationale -> imported
  draft -> reviewed diff -> explicitly activated revision cycle, and verify
  that earlier history remains readable and unchanged.
- Address reproducible workflow defects, rerun the relevant regressions and
  packaged scenarios, then update the release-gate evidence and choose the
  version number appropriate to the delivered change.

Exit: the Phase 7 criteria and Section 10 release definition are supported by
actual evidence. No installer, automatic updater, dashboard, embedded AI,
cloud/mobile access, or speculative refactor is included in this sequence.

#### Verification And Completion For Each Work Item

- Begin W1 with regression cases for the reproduced failures, then implement
  the smallest complete save operation. W2 and W3 follow as separately
  reviewable changes with the acceptance cases stated above.
- Use PowerShell 7, the repository interpreter, temporary roots/locators, and
  an injectable clock where needed. Run focused tests during implementation;
  before delivering a code change run the full pytest suite, Ruff for `src`
  and `tests`, and `git diff --check`. Include packaging tests when its fixtures
  or tooling change. Test results belong in `progress.md`, not release claims.
- Attach packaged evidence to the exact candidate manifest and environment.
  Use a real previous-version build for cross-version upgrade evidence. When a
  candidate changes, retain earlier evidence as historical and rerun affected
  checks; mark unavailable scenarios not run.
- Review the three root task records for stale/duplicate entries at completion.
  Keep personal training data outside Git; record only the minimum nonpersonal
  acceptance summary needed to assess the release gates.

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
