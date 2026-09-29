# TrainingFeedback Development Plan

Current application/schema baseline: [version history index](history/README.md).
Public-release acceptance, external review and W4 have separate gates below.
Last updated: 2026-09-28

This is the authoritative product scope, domain model, and delivery plan.
The [initial catalog and plan proposal](initial-exercises-and-plan.md) defines
seed content and proposed doses. Use these entry points:

- [Product rules and current baseline](#1-product-goal): Sections 1–8.
- [Delivery gates](#9-delivery-gates): stable release and follow-up boundaries.
- [First usable release](#10-first-usable-release-definition): product capability and release boundaries.
- [Current catalog/group contract](#12-current-catalog-and-group-contract):
  ownership, eligibility, execution, removal and supported-root conversion.
- [Version and development-data policy](#13-version-retention-and-development-data-policy):
  three application versions, schema bumps and the user-directed personal-data transition.
- [Versioned delivery history](history/README.md): completed work and superseded rules.
- [Version-independent workflow](development-workflow.md): task, verification,
  release and rotation procedures.
- [0.7.0 release review](https://github.com/YYMichaelChen/TrainingFeedback/blob/f2e0700362bc1413a19af86739ffef50f5ac5cf5/docs/history/0.7.0/release-readiness.md): dated findings and
  candidate evidence, not current release instructions.

This document contains product requirements and stable delivery gates. Active
tasks belong in the local Planscope PLAN when present. Completed delivery facts
belong in versioned history; process steps belong in the workflow and runbooks.
Historical candidate checks do not certify a later build.

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
- directory-based Windows packaging and a conventional per-user installer.

The first version excludes:

- embedded AI inference or automatic plan decisions;
- a pre-training light-mode choice;
- fixed sleep, energy, fatigue, pain, or RPE questionnaires;
- detailed subjective scoring during training;
- wardrobe data and clothing questions;
- trend dashboards and advanced analytics;
- cloud backup, accounts, network access, and mobile access;
- an automatic updater or background network update service;
- migration from the unrelated old project; development-version support for this
  application's own databases follows Section 13.

## 4. Core Product Decisions

### 4.1 Plans Drive Training

Section 12.3 extends this model with ordered action groups and rounds;
Section 12.5 pins content and images before catalog updates can change a plan.

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
action in each day, and sets in every action; it may reference guidance that has
not been reviewed. Activation additionally requires enabled exercises whose
guidance in use has complete text and valid required images under Section 12.4.
Review state does not gate activation: unreviewed
guidance is reported before confirmation and recorded in training evidence, but
it does not block activation or training. The complete prescription
and differences from the current revision are shown before confirmation.
Saving a draft does not activate it. Superseding the previous revision and
updating the active revision pointer form one transaction.
Section 12.11 owns the planned 0.7.5 distinction between editing a draft,
cloning an independent plan and explicitly upgrading an active plan.

The editor places an action list beside a single per-set table. Equal-set entry
is an optional collapsible batch-fill tool, with explicit confirmation before
replacing current values and notes. Opening or closing that tool does not change
the table. Invalid values block saving or switching actions without losing the
input. Revision diffs cover action additions,
removals and ordering, phase, rest, notes, set values, units, per-side flags,
and plan purpose without mutating either revision.

All editing, review, diff and activation operations target the displayed
revision: default to the active revision or newest draft, and select a newly
imported/cloned draft. Reject stale targets rather than acting on another revision.
Show every set's order, value, unit, per-side flag and original note in plan,
training, history and exports; free doses retain their explanation. Imported
rationale, source references and the managed original file remain unchanged by
later draft edits.

The training-plan page presents revisions in compact navigation and the selected
plan as a readable hierarchy of days, ordered actions or groups, members and
per-round sets. Its first view emphasizes plan identity, status, purpose,
prescription and execution order instead of raw stored fields. Show side order,
rest at its applicable boundary, original notes and content issues without
inventing defaults; zero and unknown remain distinct. A plan may show one concise
adjustment description explaining a deliberate prescription change, using the
saved rationale verbatim. It must not present inferred symptoms as user feedback.
Import paths, source IDs, migration registrations and other technical provenance
do not appear in the plan page or its activation preview; they remain preserved
in storage and appropriate machine-readable evidence. The page does not alter
revision targeting, activation checks or stored facts.

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

Actual-dose entry and not-completed confirmation hide the other result actions
and provide dedicated save/cancel controls. A saved result stays visible until
the user chooses the next unfinished action; repeated clicks cannot spill into
the next action. Before the session ends, an explicit confirmed retraction can
return a result to unrecorded. It atomically archives the prior action result,
actual sets and original note, then clears the recorded fields. Prescription
and guidance snapshots never change. Retractions appear in history and exports.
Finished or aborted sessions cannot retract results. Unsaved input requires an
explicit discard before leaving or pausing; it is never counted as saved work.

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
- the external rationale when supplied, without inventing one when absent;
- the confirmed new revision;
- the confirmation time.

No active plan is silently overwritten.

The application owns the versioned contract; it is not tied to a particular AI
provider. Through 0.7.4, new imports use `training_feedback.plan` v2 and new
evidence uses `training_feedback.evidence` v2. `contracts/plan-v2.schema.json`
ships with that application; `data/plan_contract.py` loads it, domain/services
validate it, and `group_plan_handoff.py` / `group_session_handoff.py` produce
portable evidence. Section 12.11 owns the planned 0.7.5 v3 contract change.
The UI imports JSON files into drafts and retains original bytes in managed
imports. Clipboard import is outside current scope. Validation and saving never
imply activation or approval. Section 12.8 owns the detailed wire contract.

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
- an enabled state, which decides whether the exercise may be used in plans and
  training and is independent of guidance review.

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

### 5.1 Guidance Review, Use, And The Enabled State

Section 12.4 owns one eligibility matrix for text, images, review and enablement.
Selection and enablement are explicit root-local facts; neither supplies review.
Complete text and valid required images may be used without external review,
with disclosure. Missing/invalid images leave readable drafts ineligible for use.

Actual review binds the exact content/image hashes and records source, actual
occurrence and separate explicit confirmation. Withdrawal appends an event and
retains original evidence; it never erases historical review observations.
Changing text or images creates new unreviewed content, retaining the selected
revision until an explicit change. Batch targets are explicit and transactional.

Bundled images belong to the program catalog; custom images and frozen assets
belong to the selected root (Section 12.1). All image references are managed,
portable and validated. Field completeness and technical image validity do not
establish content quality. Equipment may be empty when none is needed.

Chinese forms show complete current guidance,
preserve original text and unedited secondary body areas, and keep controls
reachable with long text and small windows.

External review occurrence starts empty, accepts a date or timezone-aware time,
and retains the supplied precision; explicit fill shortcuts do not become defaults.
The application generates confirmation time separately through its clock. Batch
review requires explicit selection of every target and commits atomically.
Optional answer files are copied into `reviews/` with relative path, SHA-256 and
original filename; failed writes clean up the copy. Old times and missing evidence
are never inferred or backfilled.

Bundled updates travel with the application; no manual bundled-draft import is
required. Development content delivery follows Section 13.3. Superseded review
and manual-delivery rules remain in Git history.

## 6. Minimum Domain Model

Names below describe responsibilities; final SQL naming may vary while keeping
the relationships and invariants.

| Responsibility | Current model |
| --- | --- |
| Bundled content | Read-only catalog identities, families, guidance and image manifest. |
| Root-local library | Stable references, custom/override content, selection/enablement, immutable review and lifecycle events. |
| Plans | `group_plan` revisions/days/items/sets, member/round/side rules and immutable activation pins. |
| Execution | `group_session`, frozen occurrences, actual sets, batch membership, saved controller position and audited events. |
| Feedback and handoff | Performed-area feedback, preserved original imports, portable plan/session exports and provenance. |
| Retention and conversion | Immutable content/assets, supported-version mappings, original facts and recovery journal. |

Important invariants:

- plan revisions are immutable after activation;
- session actions snapshot their plan prescription;
- completed history is never rewritten by catalog or plan edits;
- actual dose remains `NULL` when unknown;
- `0` means an explicitly recorded zero, not unknown;
- user notes are preserved verbatim;
- one execution occurrence maps to ordered planned and actual set rows;
- one session can have at most one next-day feedback record;
- foreign keys are enabled for every connection;
- final session save and its action results commit transactionally.

## 7. User Data Directory

Section 12.1 separates bundled resources from root-local state; Section 12.7
owns supported-root conversion and recovery. During development these roots are
development/test data until the user authorizes the transition in Section 13.3.

The user chooses a data root, for example:

```text
D:\TrainingFeedbackData\
|- training_feedback.marker.json
|- training_feedback.sqlite3
|- app_config.json
|- backups\
|- exercise-images\
|- custom-exercise-images\
|- snapshot-assets\
|- exports\
|- imports\
`- reviews\
```

`exercise-images/` can retain original supported-version resources; new custom
assets use `custom-exercise-images/`. The installed `catalog/` is outside this root.

`app_config.json` inside the selected root is the authoritative configuration
for that data set. A tiny locator under `%LOCALAPPDATA%\TrainingFeedback\` may
remember the last selected root so the application can find it at next launch;
the locator contains no training data and is not an alternate configuration
source. If it is absent or invalid, the application asks the user to select a
data root.

Through 0.7.6, first launch supports:

- create a new data root in an empty directory;
- open an existing valid TrainingFeedback data root.

Settings support:

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
the database. Future schemas and development schemas outside the applicable
support boundary are rejected unchanged; the planned schema 22 exception is in
Section 13.4. The current application/schema map is in the version history index.

A backup copies the complete data root, including marker, configuration, images,
exports, and imports, to an explicitly selected empty destination outside the
source root. The running application uses SQLite's online backup API for a
consistent database copy, rather than copying an open database file directly.
Failures are reported, never delete the source, and clean up the incomplete
copy so a partial backup is never presented as successful. Recovery uses the
normal open/switch flow: select the backup copy as the data root. There is no
overwrite-style restore.

Current settings provide catalog information, location display/open, complete
backup and root switching; evidence export belongs to plan/session pages.
Switching validates and prepares the target, rebuilds the main window and services
in-process, and
commits the locator only after preparation succeeds; any failure keeps the
previous root, window, and database usable. An `open` training session blocks
switching until paused; a paused session stays in its original root and can be
resumed after switching back.

Installer replacement must not write the database, images, exports or backups.
Normal application startup may apply the declared supported-version migration.
The planned 0.7.5 first-open reset of a selected schema 22 root is the explicit
exception in Section 13.4; installing program files alone does not perform it.

Windows distribution uses a directory payload with `icon/TrainingFeedback.ico`
and a per-user Inno Setup installer with stable application identity, normal
shortcuts and an uninstaller. The default installation directory is
`%LocalAppData%\Programs\TrainingFeedback`; upgrades replace program files in
place. Install, upgrade and uninstall own no locator or user-root files.

### 7.1 0.7.7 New-Root Directory Creation

For 0.7.7, **create a new data root** asks the user to select a *parent*
directory and a name for the new data directory. The name defaults to
`TrainingFeedbackData`. Before confirmation, show the resulting full path, for
example selecting `Documents` with the default name previews
`Documents\TrainingFeedbackData`. Create the marker, database, configuration and
managed subdirectories only inside that child directory; selecting `Documents`
must never place those items directly in `Documents`.

The suggested first-launch parent is the user's Windows Documents location,
resolved through the system location API so redirected Documents folders work.
The suggestion is only a proposal and creates nothing until the user confirms.
The directory name must be a single valid Windows directory name, not a path.
Do not silently choose a numbered or different name. If the child does not
exist, create it; an already existing empty child may be used. If it contains a
valid TrainingFeedback root, explain that the user can explicitly open that
root. If it contains unrelated or incomplete content, refuse creation without
modifying it. A cancelled or failed attempt must not update the last-root
locator. Failed creation must not leave an incomplete child presented as a
usable root.

**Open an existing data root** continues to select the root directory itself,
including roots created before 0.7.7 and copied backups; opening must not append
another directory layer. Use the same create behavior from first launch and
Settings when creating and switching to a new root. The separate backup and
root-copy destination flows retain their own complete-root semantics.

Acceptance for 0.7.7 covers a redirected Documents suggestion, create-path
preview, successful parent-to-child creation, existing empty/valid/occupied
children, invalid names, cancellation and failure cleanup, locator persistence,
and direct opening of existing or backup roots. Use temporary roots for these
checks, never a personal data directory.

## 8. Application Architecture

```text
src/training_feedback/
|- main.py            # Qt entry point
|- bootstrap.py       # startup coordination (data-root location/selection)
|- app.py             # LibraryContext and DataRootSwitcher composition
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
One user action commits or rolls back as a unit. Migrations within the supported
window are versioned, append-only and transactional; never rewrite an applied
migration. When a version leaves the window, retire its entry path and consolidate
fresh-database initialization under Section 13.2, preserving the remaining paths.
Every subsequent schema change also bumps the application version (Section 13.1).
Failed ordinary migrations preserve the prior version; Section 13.4 defines the
planned 0.7.5 reset's post-commit cleanup behavior.
UI tests may use offscreen Qt; all tests use temporary databases and locators,
never real user data. One QApplication is shared for a whole run, so a UI test
must let Qt destroy the windows it created; widget graphs abandoned to Python
garbage collection crash the interpreter later in the run. Date-boundary checks
cover 01:59, 02:00, and 02:01.

## 9. Delivery Gates

### 9.1 Release And Follow-Up Boundaries

A local release requires candidate content closeout, budgeted regression,
complete reproducible source and verified installer/local installed checks.
Independent Windows acceptance (H3/8-B2) and public-distribution requirements
become gates only on an explicit public-release request. External content review
is a separate review of exact content/image versions with original answers and
actual source/time; valid images alone are not review. The personal-data
transition requires the user's explicit decision under Section 13.3. W4 follows
that transition and the real-use gate below. No local release automatically
authorizes either transition, creates review facts or activates a plan.

Deferred or unrun checks are not passed checks. The [version history index](history/README.md)
owns the current application/schema and candidate baseline; version history
owns dated evidence. The [workflow](development-workflow.md) owns execution
order and verification selection.

For future candidate acceptance, choose pytest cases from the candidate's
affected and material risks before execution. Low-risk, unaffected cases are
not part of a default release run; keep them available for changes that make
their risks relevant. A case excluded after review is not a pass. Preserve
one release scope and its count, and record selected coverage, exclusions and
unrun required checks with the exact candidate. Installed client checks remain
separate and must be completed when applicable. A required risk left unverified
prevents technical acceptance even when the selected pytest count meets its cap.

### 9.2 W4 Real-Use Gate

W4 begins only after the user authorizes the personal-data transition in Section
13.3. Required actions must have complete text and valid images, be explicitly
enabled, and belong to a fully confirmed active plan; applicable local program
checks must pass. Unreviewed guidance is disclosed and frozen in session evidence.
W4 and external content review are independent follow-ups, not local-release gates.
H3 starts only on an explicit public-release request; starting personal
observation does not pass H3. No personal-use readiness is assumed.

Use the [guidance review runbook](guidance-review-runbook.md) for review and W4
templates. Record binary identity, plan/guidance versions, real session IDs and
excluded simulated IDs. Keep original exports intact even when they include
earlier simulated history; personal evidence stays in the data root.

Three sessions are a verification sample, not a frequency or dose prescription.
Unanswered feedback remains unknown. Complete a genuine evidence export →
external expert rationale → imported draft → reviewed diff → explicitly
activated revision, preserving prior history. Templates, simulated sessions and
local software checks cannot close this gate or establish full content review.

### 9.3 Independent Windows Gate (8-B2)

This gate begins only when the user explicitly requests a public release and
must complete before public publication. Local packaging or installation does
not trigger it automatically.
The [packaged acceptance runbook](packaged-acceptance-runbook.md) owns the
candidate-specific scenarios and evidence form.

Required public-release coverage:

- An independent Windows x64 environment without the build checkout or Python,
  using an ordinary non-administrator account.
- Actual retained-version binaries and isolated representative roots for upgrade
  behavior; verify preservation normally and the explicit 0.7.5 reset under
  Section 13.4. Same-version relocation is not upgrade evidence.
- Installed backup/recovery, root isolation, session/history/export agreement,
  uninstall/reinstall boundaries and real-desktop scaling at 100%, 125% and 150%.

Identify each candidate by its original manifest, hashes and source snapshot.
Offscreen checks cannot replace independent runtime or desktop evidence;
unavailable scenarios stay `not run`.

### 9.4 Verification And Record Ownership

Verification must protect data preservation and, for the 0.7.5
exception, the exact reset scope; it also covers frozen history, verbatim text,
transactional rollback and supported upgrades. Tests use synthetic temporary
roots and locators, never personal data. The version-independent
[workflow](development-workflow.md) owns test selection, static checks and
candidate procedure. [Test instructions](../tests/README.md)
give the executable commands; [packaged acceptance](packaged-acceptance-runbook.md)
owns installed and independent-machine procedures. Candidate hashes and dated
results are evidence for their identified build only.

## 10. First Usable Release Definition

The first usable **local release** established these continuing capabilities,
demonstrated with isolated synthetic inputs where appropriate:

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

Each new local release closes its intended content, verifies final source and
builds a reproducible installer with local installed checks under the
[workflow](development-workflow.md). The initial plan remains a proposal;
unreviewed guidance is disclosed and all selection/activation rules remain in
force.

External content review and W4 remain separate unfinished follow-ups. Neither blocks
local release. Independent 8-B2 and public-distribution requirements apply only after
the user's explicit public-release request. A local-release result must identify the
exact build and these evidence limits; it does not claim public acceptance, expert
approval or a personal-data launch.

## 11. Deferred Decisions

The following remain intentionally open until implementation evidence or real
use resolves them:

- the final prescribed dose for the initial plan;
- later exercise batches. Illustration availability is a mandatory enablement
  condition under Section 12.4; missing illustrations are not deferred for
  actions offered as usable.

Clipboard import, provider-specific adapters, advanced trend analysis, and
automatic updates are optional later scope, not unresolved
first-version requirements. The current application-owned JSON/file contract
is defined in Section 4.6.

<a id="12-070-development-contract-planned"></a>

## 12. Current Catalog And Group Contract

This catalog and group contract originated in the 0.7.0 work and remains the
product rule until deliberately revised. Source delivery is recorded in the
[version history](https://github.com/YYMichaelChen/TrainingFeedback/blob/f2e0700362bc1413a19af86739ffef50f5ac5cf5/docs/history/0.7.0/development.md); Section 9 owns delivery gates and
Section 13 governs supported upgrades and future version changes.

The release delivers an application-owned bundled catalog, exercise families
and variants, continuous plan action groups, mandatory illustration checks,
and reviewed exercise removal. Upgrades through 0.7.4 preserve user work while
leaving one current runtime model; Section 13.4 records the planned 0.7.5
exception. Native Windows/PySide6, local-only use,
verbatim user text, transactional actions and frozen training history remain
the product and engineering boundaries.

### 12.1 Catalog Ownership And Stable Identity

**Bundled content travels with the application.** Ship a read-only
`catalog/catalog.sqlite3`, `catalog/catalog-manifest.json`, and `catalog/images/`
under the program's resource directory. The resource resolver must work both
from source and in the installed directory payload, independently of the
working directory. The build manifest covers every catalog file; the catalog
manifest identifies its format/version, content versions and asset hashes.
Never write user state, SQLite journals or overlays into the program directory.

The selected user root owns plans, execution, feedback, reviews and original
answers, custom exercises, user content overrides, enablement/selection/removal
decisions, imports, exports and immutable evidence snapshots. New custom images
live under `custom-exercise-images/`; retained plan/session assets live under
`snapshot-assets/`. These are user-owned evidence, not another editable copy of
the bundled library. Creating a new root must not seed the full bundled catalog
into the user database. Switching roots changes user facts while the installed
bundled library remains the same.

Use namespaced stable references: `bundled` plus the existing
`bundled_exercise_key`, or `custom` plus an application-owned stable custom ID.
Persist content identity/version and hash alongside a reference. Database-local
integer IDs may remain internal keys but are not cross-root/catalog identities.
Names and aliases are display and lookup aids, never identity migration keys.
Reject ambiguous lookups; reject an imported key/name conflict instead of
choosing a different movement. IDs are never reused after removal.

Read-only bundled content and user state are combined by an application service.
The user may copy a bundled action to a custom action or create a local content
override with explicit provenance. Neither edits the package. A copy gets a new
identity, no review evidence and no enablement; an override gets a new content
revision and must pass the same current eligibility rules. A package update
must not overwrite custom text, overrides or user decisions. Bundled metadata
cannot assert a personal review, approval, activation or performed dose.

The unified library shows source, family, variant, selected content identity,
image readiness, effective review and enablement, plus removal state where
applicable. Search/filter must expose incomplete drafts as well as usable
actions. Show program catalog version in library details/settings, with the
selected user root remaining a separate setting.

Minimum new-model persistence responsibilities (final SQL names may vary):

| Store | Entities / responsibility |
| --- | --- |
| Read-only program catalog | Exercise identities, aliases, body areas, families, versioned guidance, image manifest and publisher withdrawal metadata. |
| User SQLite | Namespaced exercise references, per-root selection/enablement, custom/override revisions, review events, removal requests/decisions and migration provenance. |
| User SQLite | Plan items/groups/members/sets, immutable content snapshots and asset references, execution occurrences and actual sets, result batch/retraction identity and controller position. |
| User managed files | Custom images, hash-addressed snapshot assets, original review/import files, portable exports and recovery snapshots. |

Foreign keys join local reference/snapshot rows within the user database;
catalog references are validated by key/version/hash at the application boundary.
All state changes for one user action commit in that one writable database.
Store asset bytes before making them visible through committed references, with
staging/journal cleanup for failures. Asset retention follows all plan, session,
review and selected-override references, not just the latest library selection.

### 12.2 Exercise Families And Variants

A family is a browsing/planning relationship, not a trainable prescription or
an alias. Each movement variant keeps an independent stable key, complete
guidance, illustrations, body areas and counting convention. Basic glute bridge
remains a trainable member as well as the base of the bridge family. Membership
does not imply difficulty, progression, interchangeability or inherited review.

Conceptual catalog fields are `family_key`, `variant_role` (`base`, `variant`,
`standalone`), `variant_order`, an optional `parent_exercise_key`, and
`starting_position_class`. A family has its own stable key, display name and
description. An action has at most one primary family; optional parent
links remain within that family and cannot self-reference or form a cycle.
Standalone actions need no artificial family. Family metadata is versioned;
moving/renaming a member does not merge its history or change pinned plans.

Controlled starting-position classes are `supine`, `prone`, `side_lying`, `quadruped`,
`seated`, `kneeling`, `standing`, `mixed`, and `unknown`. Keep the full starting
position verbatim beside the classification. Equal classes support a convenient
filter, not an automatic assertion that hand placement, equipment or support
points match. Missing classification remains unknown until actually supplied.

The content document owns the initial 36-action mapping, bridge naming, the
basic bridge's three-second top hold, and the existing static-bridge definition.
Changing those instructions creates a new content version. Do not turn a
family restructure into a new user dose or a silent rewrite of an old guide.

Library UI supports family expansion, individual variants, starting-position
filters and a base/variant comparison. Copying to a custom action and changing
family membership are explicit operations; shared content is not silently
inherited by child movements.

### 12.3 Plan Action Groups And Dose Semantics

The new logical structure is day → ordered items (single action or action
group) → ordered member actions → per-round dose sets. Preserve standalone
action behavior. A group has a stable plan-item identity, display name, phase,
order, positive integer `round_count`, finite non-negative
`rest_between_rounds`, side sequence, transition instruction and original note.
Every member has its own stable item identity, order, exercise reference,
per-round sets and `rest_after_member`. A group requires at least two members;
there is no nested group. All members share the group's phase. The same exercise
may appear more than once, so exercise ID is not a plan-item identity.

The execution rule is fixed and unambiguous: perform the first member's listed
sets, then the next member's sets; repeat that ordered sequence for the stated
number of rounds. The sets are **per round**, not totals for the whole group.
Standalone sets keep their previous meaning. Members may use different units;
all sets within one member use the same unit and per-side convention. Rep counts and seconds are never
added into one meaningless group total. A group with `A: 1 rep → B: 1 rep`,
repeated N times, prescribes N A reps and N B reps for each indicated side.
All numbers in UI examples are format demonstrations, not a default dose.

For unilateral groups explicitly choose and preview side sequencing:

- `member_each_side`: each member completes its prescribed left/right work
  before moving to the next member; applicable mixed-side groups can use this.
- `same_side_then_switch`: complete the member sequence on the selected first
  side, then mirror it on the other side within each round.
- `all_rounds_then_switch`: complete all rounds on the selected first side,
  then all rounds on the other side.

The last two require compatible per-side members and an explicit first side;
otherwise use member-by-member execution or split the group. Store explicit
side labels for asymmetric actual work; `per_side=true` must not invent work
on the unperformed side. Display the expanded order before activation.

Keep member-internal set rest, between-member rest, side-switch rest and
between-round rest distinct. Zero means no prescribed rest, not an unknown
value. At a boundary apply only its designated rest, not two accumulated rest
fields; the final member transitions to the side/round boundary and the final
round has no implied extra round rest. Undefined transition duration is not
recorded as measured time. Group-level exit rest, if prescribed, is explicit.

The same-position example uses **直腿后踢 → 消防栓**, both quadruped under the
current content definitions. **俯卧直腿抬腿 → 消防栓** requires a prone-to-quadruped
transition; never present it as identical starting position. The editor lists
class/support differences and requires a transition description for mixed or
unknown positions before activation; it does not claim to assess movement safety.

Plan editing must support creating plans/days, adding/removing/reordering single
actions and groups, moving members, rounds, side order, per-round doses and rest.
Removing the penultimate group member must explicitly dissolve the group or
cancel, not leave an invalid one-member group. Invalid input stays on screen.
One save commits all children and ordering or nothing. Activated revisions are
immutable and are copied to edit; Section 12.11 distinguishes the planned
`Clone` and `Upgrade` operations. Diffs use stable item identities plus readable
day/group/member paths, and include membership, ordering, side sequence, rounds,
rest, dose, notes and pinned content changes.

### 12.4 Illustration, Review And Enablement

**No usable illustration means an unreviewed draft, ineligible for enablement.**
At least one illustration is required for the selected content revision, with
all assets declared required by that revision available. Text remains readable
even when an image fails. Validate a managed relative reference, containment,
file existence, supported decoding, nonzero dimensions and SHA-256. An absolute
or escaping path, remote link, placeholder, corrupt file or `status: missing`
does not pass. Image resolution/decoding belongs outside the pure domain layer;
domain eligibility consumes its explicit validation result. A successful file
check is not expert review of anatomical or technical correctness.

Keep four distinguishable facts: text completeness, image readiness, actual
external review evidence for that exact content/image set, and user's enablement.
Review evidence binds a content hash and the reviewed image-set hashes. A new
or edited text/image version starts unreviewed. The reviewer must inspect support
points, moving side, direction, sequence and agreement between illustration and
text; a picture's mere presence never produces approval.

| Selected revision | Select for use / enable | Plan activation / new-session start |
| --- | --- | --- |
| Incomplete text or no valid required illustration | Block; show draft and exact reason | Block and name affected items |
| Complete text and valid images, no external review | Allowed only through the explicit normal actions | Allow when enabled, disclose unreviewed content |
| Complete text/images and matching real review evidence | Allowed through the same actions | Allow when enabled |
| Removed/archived for future use | Block | Block for new sessions |

This is the accepted illustration gate with the retained distinction between
external review and enablement. It is not permission to bypass the image gate.
Review never enables automatically; enabling never manufactures review. Selecting
a revision cannot evade validation through an already-enabled action. Check the
same eligibility rule in services for selection, enablement, plan activation and
starting a new session, including imports and batch operations, not only buttons.

For an edited draft, the previous selected revision remains selected until an
explicit change. If a selected image disappears or is corrupted, effective
eligibility and effective review immediately fail; do not erase the original
review event or rewrite historical review snapshots. Repairing the exact hashed
asset restores file validity, not a new approval. Different bytes require a new
unreviewed content revision. Old review evidence lacking image coverage remains
historical evidence and cannot be inferred to certify a new image set.

Check images at build/catalog validation and again before the relevant runtime
actions. A missing optional illustration is visible; it must not be relabelled
as checked. Withdrawing current review uses an appended event instead of erasing
evidence used by history. A current unreviewed version with valid text/images
remains governed by the table above. Batch actions revalidate exact targets and
commit all selected changes or roll back all of them.

### 12.5 Training, Snapshots And History

At plan activation pin each member's content revision, name, guidance, body areas,
family/variant identity, image hashes and required assets. Retain a deduplicated
immutable snapshot in the user root; it is evidence for that plan, not a second
live catalog. Review evidence remains separately time-stamped. Later bundled
updates become visible in the library automatically but adopting changed content
for an activated plan requires a new draft and the normal plan confirmation.
Unchanged content needs no reconfirmation after upgrade.

At session creation freeze the full prescription, guidance/asset reference and
review/eligibility facts observed then. Expand group rounds and side order into
uniquely positioned execution occurrences with group, round, member and side
snapshots. Do not rely on the old unique `(session, day, plan_action_order)` key
for several rounds of the same member. Freeze group name, total rounds,
transition/rest semantics and original notes. Later catalog deletion, renaming
or program replacement cannot make session interpretation depend on live files.

Each occurrence supports the existing four outcomes, actual work for partial or
exceeded results, and verbatim notes. To keep one-rep combinations practical,
offer an explicit “complete this round as prescribed” batch operation for its
unrecorded members. Show exactly what that command confirms, commit it atomically,
and reject stale/repeated requests. It never overwrites recorded exceptions or
marks a later round completed. Individual outcomes remain available. Retracting
a batch result archives the prior member facts transactionally before resetting
them; terminal sessions remain immutable.

For `all_rounds_then_switch`, the batch target is the displayed side and round,
not the opposite-side occurrences that will be performed later. For a round
containing both sides, the preview explicitly includes both before confirmation.
Persist the batch membership so retraction never clears an unrelated individual
result. UI navigation cannot change the target while a save is in flight.

SessionController owns position/round/side and unfinished state. Navigation is
not evidence of performance; only saved results count. Pause/restart resumes the
last saved position and unfinished work, without inferring unsaved reps. Show
group name, round, current side, current/next member and boundary-specific rest;
pause/abort/finish controls stay outside scrolling. Finish requires an outcome
for every occurrence. Next-day feedback is deduplicated from actually performed
member snapshots, never from all catalog-family members or unanswered work.

Already open/paused sessions remain finishable from their original snapshots
after upgrade or removal. This is a current-model execution rule for frozen work,
not an old-settings switch. New sessions recheck removals, enabled state and
asset readiness against the pinned prescription. Unanswered older facts stay
unknown; never synthesize historical image validity, side counts or review times.

### 12.6 Reviewed Removal And Restoration

Removal is a reviewed lifecycle operation with retention of referenced evidence.
A user removal of a bundled action records a root-local decision; it cannot edit
the read-only package or claim to change the publisher's catalog. Publisher-wide
withdrawal is delivered in a later bundled manifest. Custom actions are archived
in the user's root. Both disappear from new-plan selection once removal applies.

A request stores source/key, exact content hash, original reason, request time
and reference impact (draft/active plans, groups, unfinished/terminal sessions,
reviews, dependent variants and exports). Append decisions and their source,
actual occurrence, explicit confirmation time and note. The lifecycle is
`requested → under_review → approved → applied`, with `rejected` and `cancelled`
exits; a separate approved restoration event can restore future availability.
Request, content identity, decision and application are auditable, not a single
unexplained deleted Boolean. A content change requires renewed review. Applying
an approval rechecks references in the transaction; if impacts changed since
preview, refresh the impact before applying.

One person may explicitly request and confirm removal; no account system or
multi-role approval infrastructure is introduced. Do not invent an external
reviewer. Approval/application may share one transaction when that is the
explicit user action. Batch removal must show every target and roll back as a
whole on failure. Show rejected/cancelled outcomes without hiding the action.

Applied removal disables future use and adds a minimal stable-key tombstone;
it does not physically delete referenced guidance/images, mutate plan revisions,
rewrite exports or recursively remove family members. Affected plans remain
viewable; new sessions are blocked until a newly confirmed plan replaces the
action. Open/paused work uses the rule in Section 12.5. Proposed substitutes are
suggestions requiring explicit plan editing. Parent/family links must remain
resolvable or be explicitly reassigned without deleting the variants.

The tombstone contains identity and disposition metadata, not a trainable legacy
library or compatibility entry point. History reads its own snapshots. Restore
requires a new explicit decision and current image/content validation; it does
not restore enablement, plans or invalid review evidence automatically. No
unreviewed physical purge is offered.

### 12.7 Supported Root Opening And Historical Upgrade Evidence

An installed update replaces only application files. Ordinary root opening
retains the locator, selected root, meaningful settings, frozen plans and
completed history. The planned 0.7.5 first-open reset deletes the plan/training
scope in Section 13.4. Opening or switching to a supported root validates the
marker, configuration, schema and current library model before use. No directory
scanning or old Exercises@home database access is allowed.

Historical conversions and retired fixtures do not expand the current support
window; their dated design is in version history. Roots outside the applicable
boundary are rejected read-only with the reinstall/new-empty-root guidance of
Section 13.2; schema 22 roots are the explicit 0.7.5 exception. Do not offer a
migration wizard, compatibility setting, legacy library, fallback reader or
implicit import for an expired root.

Future in-window schema changes normally use a version bump, pre-write
validation, recoverable snapshots and transactional migrations. They preserve
frozen facts without inventing approval, images, physical results or user
decisions. The planned 0.7.5 schema 22 reset in Section 13.4 instead discards
the specified plan/training facts without a backup. Normal root backup and
restore remain separate user actions outside that one-time reset.

### 12.8 External Handoff Contract

Through 0.7.4, use `training_feedback.plan` version 2 for new imports and
`training_feedback.evidence` version 2 for new exports; define their version
constants independently. Only the current plan-import contract is accepted. A
newly supplied older-format file gets a clear current-format error and the
current schema, not a compatibility converter or version selector. Through
0.7.4, plans already stored in a supported root retain their frozen facts;
their original imported files and original exports are not rewritten or
re-imported. Sections 12.11 and 13.4 own the planned 0.7.5 changes.

V2 carries namespaced action keys, exact content references, family/variant
identity, ordered standalone/group items, rounds, side order, per-round sets,
all rest boundaries and source rationale. Imports create drafts only and cannot
create approval, enablement, deletion decisions or plan activation. Schema and
domain validation enforce identical invariants and reject unknown identities
without silent substitutions. An identity for removed content resolves to
“removed”, not to a new similarly named exercise.

Evidence JSON and Markdown show the same frozen plan/group/occurrence facts,
actual work, review state at execution, unknown legacy facts, verbatim notes and
audited retractions. Record application version, catalog version, database schema
and content hashes separately. Group totals are derived displays, not additional
performed work. Relevant removal events and snapshot provenance are labelled as
catalog/user-management facts rather than user physical feedback.

References alone do not let an external reviewer inspect a local image. Export
the needed illustration files as an adjacent portable asset set with relative
paths and hashes (deduplicated by content), or include them in the explicit
review package. Mark unavailable historical assets honestly. Never depend on an
absolute installation path. Backup/copy/restore includes custom content, reviews
and retained snapshot assets; it does not require a previous installed catalog
to render recorded history.

### 12.9 Remaining Delivery And Verification

Section 9.1 is the open work list. The [contract annex](contracts/0.7.0-contracts.md)
owns the retained detailed serialization/mapping baseline. Regression protects
the risks below; actual retained-binary and independent Windows acceptance
belongs to H3 only after a public-release request.

- For a later public release: supported baselines generated/opened by identified
  retained-version programs, using
  isolated synthetic data with renamed/missing-key actions,
  custom text, overrides, images, review attachments, active/draft plans,
  terminal and paused sessions, next-day feedback, retractions and original files.
  Compare logical facts/resource hashes for ordinary preservation upgrades;
  verify the declared 0.7.5 deletion scope instead for its one-time reset.
- Reject out-of-window development roots before writes, except the planned 0.7.5
  schema 22 reset; preserve future-schema rejection and fresh initialization coverage.
- Missing image vs corrupt image vs changed hash, no-image drafts with prior
  review evidence, enabled-but-ineligible state, bundled and custom images,
  renamed families, repeated exercises in groups, asymmetric sides and mixed units.
- Failure at backup, staging, SQL conversion, asset publication and cleanup for
  ordinary upgrades; for the 0.7.5 reset, cover transactional database deletion
  and resumable file cleanup without a snapshot. Include disk/access errors,
  competing opens, repeat startup and root switching. No partial success or
  fabricated approval.
- Catalog withdrawal after plan activation; new-start blocking; resumed frozen
  work; history/export/backup restore with a newer catalog lacking that movement.
- UI inventory and source review proving removal of manual bundled acceptance,
  old-settings/legacy mode controls, old-format import selectors and fallback
  runtime branches. Read-only provenance and recovery artifacts are labelled
  as evidence, not selectable settings.

The [development workflow](development-workflow.md) owns selection and verification
steps. The [packaged runbook](packaged-acceptance-runbook.md) owns installed and
independent-machine checks, each tied to an exact candidate.

### 12.10 Release Exit And Documentation Ownership

Usable actions meet Section 12.4 and the bundled content/image inventory must
report truthful readiness. A technically valid illustration does not establish
expert review. The dated 0.7.0 local-release exit and checks are recorded in its
[version history](https://github.com/YYMichaelChen/TrainingFeedback/blob/f2e0700362bc1413a19af86739ffef50f5ac5cf5/docs/history/0.7.0/release-readiness.md).

Keep local-release, external-review, personal-use and W4 results distinct.
Independent 8-B2 is deferred/not run and is activated only by an explicit public
release request. It is not a prerequisite for local packaging or local release.

No ordinary supported-upgrade success claim may rely on a reset root, manual
re-import, compatibility settings, changed historical doses or an earlier build's
acceptance. The planned 0.7.5 reset is successful only when its exact deletion
and retained-library scope is verified; it is not preservation evidence. Source
regression covers supported synthetic upgrades and unchanged rejection of roots
outside the applicable boundary. Local installed checks and later public
acceptance record their own actual scope and candidate identity.

This document owns product/architecture/migration contracts. The content
document owns family membership, aliases, technique and proposed doses.
Candidate evidence and task records document actual work without duplicating
these specifications.

### 12.11 0.7.5 Plan Authoring And Identity

Decision accepted: 2026-09-28. This defines 0.7.5 behavior; it is not a claim
about the 0.7.4 application or candidate.

New-plan entry and editing use one page: a plan/day/item hierarchy beside the
selected item's fields and per-set table. The new page starts with an unfinished
day whose name is entered in place. Searchable, multiple exercise selection adds
unsaved actions; groups and members use the same detail area. The user supplies
set values, count, unit, per-side choice and applicable rest, including an
explicit zero for no prescribed rest. No catalog proposal or UI placeholder is
silently saved as a user dose. An explicit equal-set fill may replace existing
values or notes only after confirmation. Incomplete or invalid input remains
visible, blocks switching or saving as applicable, and identifies the field to
repair. A valid draft still requires a name, a nonempty day and complete action
sets; one save commits the complete prescription transactionally.

Each root uses a visible code `plan-NNN.AA.DD`. A new plan takes the next free
three-digit `NNN` on save and begins at `.01.00`. `Clone` copies the complete
selected revision into an independent plan; on save the user supplies an unused
three-digit base number and a distinct plan name, beginning at `.01.00`.
`Upgrade` copies the latest active revision within the same plan; an existing
upgrade draft reopens for editing, and an unchanged copy cannot be saved as a
new upgrade. Draft edits keep their identity and do not create an extra version.
Both operations ask for a change description when opened but allow it to remain
empty. Copied prescription and user text remain verbatim until explicitly edited.

The upgrade code is calculated from the actual difference against its source.
Changes to day/group structure, action identity or content, item/member order,
phase, first side or side sequence increment `AA` and reset `DD` to `00`.
Changes confined to dose, rest or other plan text increment `DD`; combined
changes use the structural rule. A rationale alone does not create an upgrade.
Before every draft save, show the changed fields and resulting code, recheck
uniqueness transactionally and recompute after later edits; activation fixes the
code. Both suffixes have a two-digit minimum and may grow past 99. Base numbers
are `001`–`999`, are unique within the root and never wrap or silently reuse.
Internal revision IDs/ordinals remain for associations, but the plan page shows
the code rather than automatic `v1`/`v2` labels.

0.7.5 introduces database schema 23 and current plan/evidence wire contracts v3.
The plan-import rationale may be empty. A new import receives a root-local base
number; an upgrade import identifies the target by base code and follows the
same difference classification. Only v3 is newly accepted; v2 imports receive
the current-format error. JSON/Markdown evidence and new training snapshots
show the complete code consistently. Saving a draft never activates it, and
activation retains the existing eligibility and explicit confirmation gates.

## 13. Version Retention And Development Data Policy

Decision accepted: 2026-09-20. The project remains in development. This policy
supersedes unlimited historical-document retention and unbounded migration-chain
support. The current application/schema support map is in the
[version history index](history/README.md); dated implementation evidence is in
version history. Rotation procedure is in the [workflow](development-workflow.md).

### 13.1 Application Versions And Schema Changes

- Keep the current application version plus its two immediate predecessors.
  Count distinct version numbers, including patch versions, not GitHub commits.
  Several commits with the same version consume one slot. Record the actual
  commit/source snapshot/build identity for each retained version.
- Every subsequent database schema revision must bump the application version
  at least by one patch in the same change. A minor/major bump may accompany
  a schema change; an application-only fix may keep the existing schema.
- Historical intermediate schemas retain their original numbers; do not
  fabricate released application versions for them. Required internal steps
  may remain while a supported endpoint depends on them, but are not additional
  supported releases. Decide intermediate-root handling explicitly in the
  version/schema mapping; never equate a numeric range with release support.
- Maintain application version, database schema, catalog/content version and
  external wire-contract version separately. Changing a wire schema requires an
  application bump too, but need not change the database schema without a storage
  change. Retaining an old contract as evidence does not enable its import.

### 13.2 Retention And Supported Database Upgrades

Complete development plans, task records, acceptance evidence, schema documents,
contract snapshots, synthetic baselines and runtime migration entry support share
the three-application-version window. Current specifications keep valid rules and
open work; completed work of a retained version is tracked under
`docs/history/<version>/`, and moves to
the untracked local `docs/archive/` holding area when the version expires.
Local `.planning/archive/` contains historical execution context only; it is
not a substitute for tracked release evidence. Archiving is not permanent
retention.

At rotation, inventory references, merge still-valid rules into current documents,
then remove the expired version's full records and exclusive fixtures/helpers.
Keep only schema definitions and migration steps needed to create the current
database or upgrade a retained version. Consolidate new-database initialization
without rewriting already-applied migration semantics in the supported window.
Git/GitHub commit history stays intact; do not create an unbounded second archive.

Except for the explicit one-time rule in Section 13.4, supported roots reopen
without changing frozen facts and a retained upgrade may use normal automatic
recovery/conversion. Roots outside the applicable support boundary are detected
read-only and refused before migration or other writes, with an actionable
message such as:

> 此开发数据版本已超出支持范围，请重新安装当前版本并新建数据目录。
> 原数据目录已保留，不会自动删除或重置。

Reinstalling program files does not recreate the independent root. The user must
explicitly choose a new empty directory; installation/uninstallation never deletes
the old root or locator. Section 13.4 applies only when 0.7.5 first opens a
selected valid schema 22 root. Do not auto-import an unsupported database or
offer a legacy runtime mode. Unsupported future roots remain unchanged. New
roots load the complete current bundled catalog without relying on an older root.

Retention is for development artifacts and compatibility code, not general
permission to purge personal data, original answers/exports or historical
evidence within a retained root. Section 13.4 records the user's specific
0.7.5 deletion decision. Active test-budget ledgers must not be reset during
cleanup. Unclassified local files require inventory before disposal.

### 13.3 Development Content And Personal-Data Transition

All development additions/revisions to exercises, guidance, aliases, families,
classification and intended bundled illustrations belong in application-owned
source content and the packaged catalog. They must satisfy the latest version's
format, identity, content and image rules. A useful change saved only in a local
development root is not delivered: deliberately reconcile it into owned source
before retiring that root. Never scan personal roots or publish personal assets
as an automatic part of this reconciliation.

A clean install plus new root must show the latest full built-in library without
old-database migration or manual import. Missing-image items remain visible drafts
and cannot be described as ready to train. Package updates do not invent personal
reviews, activation, results or feedback. Simulated approvals/training stay synthetic.

The user explicitly decides when development is ready to become personal use.
Until that decision, do not designate a development root as the personal baseline
or automatically transfer its facts. At the transition, identify the exact program/
catalog/schema, establish a deliberate personal root, select which actual content
is to become personal data, and confirm the complete plan. The concrete transfer
scope and mechanism are deferred to that decision; existing custom/override
features do not authorize a bulk copy of development records. Preserve real
original facts if any are deliberately retained, and exclude synthetic facts from
personal review, training and W4 evidence. Revisit long-term support policy then.

### 13.4 0.7.5 One-Time Plan And Training Reset

Decision accepted: 2026-09-28. After 0.7.4 source work closes, 0.7.5 first opening
any valid schema 22 TrainingFeedback root automatically deletes its existing
plan and dependent training data without a confirmation prompt or recovery
backup. Schema 22 roots created by 0.7.2, 0.7.3 and 0.7.4 do not record enough
application-version information to distinguish their origin reliably; all are
subject to this same reset. This is an explicit exception to Sections 12.7 and
13.2, not evidence that prior plan or training facts were preserved.

The reset removes current and retained legacy plan revisions, actions, doses,
activation pins, sessions and their results, retractions, next-day feedback,
plan/session import-export registrations and associated managed files. It also
deletes existing backups inside that selected root, including backups that may
contain other root data. It retains the root's library selections, custom
actions, guidance, images, review and removal decisions that are independent of
the deleted plans. No previous synthetic training or approval becomes a new
personal fact. Files copied outside the selected root are not discovered or
deleted. The old `Exercises@home` repository and database remain untouched.

Before any write, validate the exact selected root's marker, configuration,
schema, SQLite integrity and references, acquire its exclusive lease and
inventory managed deletion paths. Apply the database reset and schema 23
migration transactionally. Use only a metadata-only cleanup journal so an
interrupted run finishes pending file deletions before the root becomes usable;
do not create or retain a data snapshot, and do not report partial cleanup as
success. Failure before the database commit leaves its old rows unchanged;
failure afterward resumes the irreversible cleanup on next open. Installation
alone and root discovery never trigger the reset.

Fresh 0.7.5 roots start at schema 23 with no old plan data. Roots with a schema
earlier than 22, a future schema or invalid metadata remain unchanged and are
rejected before cleanup. Verify the exact deletion and retained-library scope
with isolated synthetic roots, interrupted cleanup, repeat opening and installed
checks; identify each candidate and never present the reset as a preserved-root
upgrade. Ordinary preservation and backup policy resumes after this one-time
transition.
