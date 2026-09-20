# TrainingFeedback Development Plan

Status: development stage; 0.7.0 / schema 22 local candidate; 070-A–G complete;
070-H and release acceptance open; three-version policy implementation pending\
Last updated: 2026-09-21

This is the authoritative product scope, domain model, and delivery plan.
The [initial catalog and plan proposal](initial-exercises-and-plan.md) defines
seed content and proposed doses. Use these entry points:

- [Product rules and current baseline](#1-product-goal): Sections 1–8.
- [Open delivery work](#9-open-delivery-work): review, W4 and packaging gates.
- [First usable release](#10-first-usable-release-definition): completion criteria.
- [Current catalog/group contract](#12-current-catalog-and-group-contract):
  ownership, eligibility, execution, removal and supported-root conversion.
- [Version and development-data policy](#13-version-retention-and-development-data-policy):
  three application versions, schema bumps and the user-directed personal-data transition.
- [Versioned delivery archive](archive/README.md): completed work and superseded rules.
- [Release review and cleanup execution plan](release-readiness-0.7.0.md): findings,
  evidence, ordered tasks and acceptance criteria; no implied release approval.

This document contains current requirements and open work. Completed delivery
details belong in the versioned archive. Policy acceptance does not establish
implementation or candidate acceptance; Section 9.1 names the remaining gaps.

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

For 0.7.0, Section 12.3 extends this model with ordered action groups and rounds;
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
- the external rationale;
- the confirmed new revision;
- the confirmation time.

No active plan is silently overwritten.

The application owns the versioned contract; it is not tied to a particular AI
provider. New imports use `training_feedback.plan` v2 and new evidence uses
`training_feedback.evidence` v2. `contracts/plan-v2.schema.json` ships with the
application; `data/plan_contract.py` loads it, domain/services validate it, and
`group_plan_handoff.py` / `group_session_handoff.py` produce portable evidence.
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

Chinese forms show complete guidance, the selected version and differences,
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
and manual-delivery rules are in the [0.6.1 archive](archive/0.6.1/development.md).

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

First launch supports:

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
the database. Future schemas and development schemas outside the three-version
support mapping must be rejected unchanged. Section 13.2 defines the latter
policy; enforcing the lower bound is still open work in Section 9.1.

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

Windows distribution uses a directory payload with `icon/TrainingFeedback.ico`
and a per-user Inno Setup installer with stable application identity, normal
shortcuts and an uninstaller. The default installation directory is
`%LocalAppData%\Programs\TrainingFeedback`; upgrades replace program files in
place. Install, upgrade and uninstall own no locator or user-root files.

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
Failed migrations preserve the prior version.
UI tests may use offscreen Qt; all tests use temporary databases and locators,
never real user data. One QApplication is shared for a whole run, so a UI test
must let Qt destroy the windows it created; widget graphs abandoned to Python
garbage collection crash the interpreter later in the run. Date-boundary checks
cover 01:59, 02:00, and 02:01.

## 9. Open Delivery Work

### 9.1 Current Baseline

Current source and local directory candidate are **0.7.0 / schema 22**.
070-A–G implementation is complete; detailed deliveries live in the
[0.7.0 archive](archive/0.7.0/development.md). 070-H remains open. The catalog is
`070-baseline-1`: 36 unreviewed entries, no actual bundled illustrations, and a
13-action initial-plan proposal. This is development, not a personal-data launch.
The user decides when that transition occurs; old local approvals and simulations
do not establish approval of the current catalog or a personal baseline.

The [dated release review](release-readiness-0.7.0.md) records candidate evidence
and the cleanup sequence. Required open work:

| ID | Next action | Completion evidence |
| --- | --- | --- |
| 070-R1 — Reproducible source | Track the frozen synthetic DB explicitly and protect fixture bytes from Git newline filters; capture the complete source state. | Clean-checkout fixture/hash validation and a reproducible candidate identity. |
| 070-R2 — Version support window | Enforce Section 13: accepted version/schema map, too-old rejection, current fresh initialization and only necessary migration paths. Replace out-of-window positive fixtures with rejection coverage. | Fresh create; 0.6.0/schema14 and 0.6.1/schema16 supported upgrades; too-old/future roots unchanged; restart/failure preservation. **Implemented 2026-09-21**: schema-14 lower-bound guard at `inspect_existing`/`apply_migrations`, Section 13.2 refusal message, schema 1/9/13 rejection and schema14 conversion coverage (dev scope 070-R2, 27/27). Candidate-level re-verification remains with 070-H2. |
| 070-H1 — Built-in content | Deliver revised bridge definitions/aliases and real illustrations, prioritizing the initial 13 references; rebuild the catalog and classify all 36 entries. | Current content/image version/hash inventory; usable actions satisfy Section 12.4; actual review remains separately evidenced. |
| 070-H2 — Candidate and installer | Commit the reviewed source, run the minor release selection, build the installer with the pinned toolchain and retain manifests. | Candidate-specific regression, payload hashes and actual installation evidence. Inno Setup is present; installer execution is pending. |
| 070-H3 — Independent Windows | Execute the packaged runbook on an independent ordinary-user Windows machine/VM. | Passing supported upgrades, recovery, backup/reopen, uninstall isolation and 100/125/150% desktop checks. All 12 scenario rows currently not run. |
| DEV-CLEAN — Workspace retention | Apply the three-version inventory after preserving development content and required evidence; remove redundant generated files and expired material. | Version/file/hash inventory, no missing supported fixtures/evidence, reduced workspace and reviewed Git changes. |
| PERSONAL — User-directed transition | Await explicit user readiness, then establish a personal root/content baseline and confirm a complete plan. | User decision, deliberate content transfer and explicit plan activation; no synthetic facts promoted to personal evidence. |
| W4 — Real-use refinement | After PERSONAL and applicable checks, record at least three real sessions, feedback and one expert revision cycle. | Genuine IDs/feedback/rationale, imported draft, reviewed diff, activation and unchanged history. |

### 9.2 W4 Real-Use Gate

W4 begins only after the user authorizes the personal-data transition in Section
13.3. Required actions must have complete text and valid images, be explicitly
enabled, and belong to a fully confirmed active plan; applicable local program
checks must pass. Unreviewed guidance is disclosed and frozen in session evidence.
The independent gate remains mandatory for formal release even if the user elects
to start personal observation earlier. No current personal-use readiness is assumed.

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

Complete this gate before broader distribution, adding users or formal release
acceptance. The [packaged acceptance runbook](packaged-acceptance-runbook.md)
owns the current candidate's scenarios and evidence forms; superseded 0.6.x
procedures are versioned archive material, not current upgrade instructions.
Reuse the build tooling, manifests and synthetic fixtures, refreshing transfer
inputs when the gate starts.

Required coverage:

- Independent Windows x64 VM or machine without Python, Conda, source checkout
  or access to the build environment; a new build-machine account is insufficient.
- Ordinary non-administrator first launch, create/open/switch, invalid or
  occupied roots, cancellation and restart; Chinese and space-containing paths.
- Supported-window upgrades from actual previous-version programs using isolated
  representative roots. Preserve unopened originals; compare logical records,
  historical snapshots and resource hashes, allowing only declared migrations.
  Same-version relocation is not upgrade evidence.
- Packaged online whole-root backup and normal-flow reopening, paused-session
  resume, history/feedback/export agreement, source isolation and failed destinations.
- Real-desktop 100%, 125% and 150% scaling, including 1366×768 and 1920×1080
  where available: startup/switch dialogs, guidance, long Chinese text and many
  actual-set rows; core training controls remain outside scrolling.

Identify each candidate by its original manifest, hashes and source snapshot.
Keep previous results historical when a candidate changes and rerun affected
checks. Offscreen tests and startup smoke checks support acceptance but cannot
replace independent runtime or desktop evidence; unavailable scenarios stay
`not run`.

### 9.4 Verification And Record Ownership

Prioritize reproduced data/history errors, workflow blockers, then redundant
operations and unclear messages. Each repair needs reproduction steps, expected
behavior and a focused acceptance case. Use PowerShell 7, the repository
interpreter, temporary roots/locators and injectable clocks. Select meaningful
affected tests within the stage budget below; run Ruff for `src` and `tests`,
and `git diff --check` before implementation delivery. Include packaging checks
when payloads or fixtures change.

#### Regression Budgets

| Verification stage | Maximum parameter-expanded pytest cases |
| --- | ---: |
| Small development step (`dev`) | 30 |
| Patch release, x.y.z → x.y.(z+1) (`patch`) | 50 |
| Minor release, x.y.z → x.(y+1).0 (`minor`) | 100 |
| Major release, x.y.z → (x+1).0.0 (`major`) | 300 |

These are ceilings, not targets. Keep the resident suite at or below 300 cases.
Small edits use the affected cases, often fewer than ten. Patch/minor release
profiles cover core workflows plus stage-specific integration; add the actual
release's affected cases within the same budget. Major releases use the full
resident suite. Release budgets are inclusive, not added to each lower tier;
earlier development checks are historical, not a reason to rerun every case
during release verification.

`pyproject.toml` defines small, nested baseline profiles. Explicit pytest paths,
node IDs, `-k`, or `-m` replace that baseline selection for focused work; the cap
still applies. Every execution supplies a stable `--test-scope` task/release ID.
The pytest budget plugin checks expanded cases before execution and reserves
their union across commands in `.tmp/test-budgets/`. Repeated cases consume no
additional slots, but passing checks should not be repeated without new changes,
failures or unresolved concerns. Interrupted runs keep their reservations.
Collection-only commands neither execute tests nor reserve slots; use
`--test-tier major --collect-only` to inspect the entire resident suite.

Do not silently truncate a selection, bypass the cap by splitting commands or
changing a scope, or disguise independent cases as loops inside one test. If a
selection exceeds its budget, review duplicate/low-value coverage and choose
representative independent risks. Prefer transactional rollback, frozen history,
verbatim text, backup/reopen and upgrade preservation over repeated field/label
checks. UI tests should cover coherent user workflows. Add regression cases for
new behavior or reproduced defects only when existing cases cannot cover the risk.
Normal lint, inventory and packaging integrity checks are not pytest cases;
do not move regression scenarios into ad-hoc scripts to evade the budget.

Product/content requirements stay in this document and the seed specification;
execution procedures stay in the runbooks. Candidate hashes, generated fixtures
and dated checks stay in local task artifacts. Keep only the active task in the
three root records; archive completed work by application version under
`.planning/archive/<version>/`. Full documents, contracts, evidence and archives
obey the same three-version retention window in Section 13; moving material into
an archive does not exempt it from expiry.

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
W4 real-use and 8-B2 packaging/recovery acceptance in Section 9. A package
version number alone does not establish release readiness.

## 11. Deferred Decisions

The following remain intentionally open until implementation evidence or real
use resolves them:

- the final prescribed dose for the initial plan;
- later exercise batches. Illustration availability is a mandatory 0.7.0
  enablement condition under Section 12.4; missing illustrations are no longer
  deferred for actions offered as usable in that release.

Clipboard import, provider-specific adapters, advanced trend analysis, and
automatic updates are optional later scope, not unresolved
first-version requirements. The current application-owned JSON/file contract
is defined in Section 4.6.

<a id="12-070-development-contract-planned"></a>

## 12. Current Catalog And Group Contract

This is the current 0.7.0 product contract, not a completed-task log. The desktop
uses `LibraryContext` with schema 22. Source delivery is recorded in the
[version archive](archive/0.7.0/development.md); open acceptance is in Section 9.
Section 13 narrows supported upgrades and governs future schema/version changes.

The release delivers an application-owned bundled catalog, exercise families
and variants, continuous plan action groups, mandatory illustration checks,
and reviewed exercise removal. The upgrade must preserve user work while
leaving one current runtime model. Native Windows/PySide6, local-only use,
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
description. In 0.7.0 an action has at most one primary family; optional parent
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
immutable and are cloned to edit. Diffs use stable item identities plus readable
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
unreviewed physical purge is included in 0.7.0.

### 12.7 Seamless In-Place Upgrade; No Old-Settings Entry Point

For a root inside Section 13's support window, “seamless” means normal installer
replacement and normal launch, retaining the
locator, selected root, meaningful settings and user work. The installer owns
only application files. On first launch the application automatically prepares
and converts the explicitly selected TrainingFeedback root; it never scans other
directories or the old Exercises@home database. Do not introduce a migration
wizard, manual catalog import/mapping step, old/new settings selector, legacy
library tab, compatibility flag, reset requirement for supported roots or user-facing
rollback mode. Roots older than the window follow Section 13.2's explicit
reinstall/new-root requirement. Routine progress is allowed; actionable errors
must not be hidden. The lower-bound enforcement is implemented (070-R2,
2026-09-21): below-window roots are refused read-only before any write.

Implementation sequence:

1. Validate package/catalog manifests and the root marker/schema; acquire an
   exclusive migration lock and check access and free space before writes.
2. Automatically create and verify a pre-upgrade recovery snapshot using SQLite
   online backup plus copies of marker/configuration and all managed resource
   bytes, verified against a resource manifest. Use a versioned recovery location
   under `backups/` without recursively copying earlier backups into themselves.
   No destination-selection step is required. Failure stops the upgrade before
   business-data conversion. This recovery snapshot has its own internal format;
   it is not silently advertised as the ordinary complete-root backup.
3. Stage new managed assets and prepare deterministic stable references. Map
   existing bundled keys directly; a missing or unresolvable key becomes a
   preserved custom identity with origin metadata, not a guessed name match or
   a third `legacy` runtime branch. Preserve conflicts as distinct identities.
   Keep user overrides, original text, local illustrations and review attachments.
4. Materialize every referenced plan/session fact from its actual stored
   revision before detaching old catalog tables. Preserve schema-16 local IDs
   where externally referenced; map internal references consistently. Historical
   facts not recorded by the old schema remain explicitly unknown. A current
   name/image is not proof it applied at an earlier date. Mark migrated plan
   bindings as migration-time pins rather than fabricated activation snapshots.
5. Convert all persisted plans, actions, settings and registrations into the
   new model. Old ungrouped actions remain single items; never auto-group an
   existing plan or change its dose. Preserve previously valid intent, but
   invalidate effective enablement where required images are missing, retaining
   the former setting only as migration evidence. Active plan status is not
   rewritten to pretend confirmation of a replacement prescription.
6. In append-only schema migrations, commit new references, snapshots and format
   markers after validation. Remove obsolete live catalog duplicates/settings
   once their user content and evidence are accounted for. Never destructively
   clear an unknown user field: preserve its original value as read-only
    provenance rather than as a fallback runtime setting. Schema numbers and
    application versions are assigned together under Section 13.1.
7. Publish staged immutable assets and complete a recoverable journal protocol
   before exposing the root for normal use. File publication and SQLite commit
   cannot be treated as one filesystem transaction: test failure before/after
   each boundary and restart deterministically to finish or restore the prior
   complete root. Do not expose a half-converted root or delete the sole image
   copy. Clean old resource locations/staging only after committed references
   and hashes have been verified.
8. Subsequent starts use only current repositories, settings and asset resolvers;
   a completed conversion is idempotent and does not repeat seeding, copying,
   confirmation or image association. Remove old bundled-acceptance controls,
   obsolete review/plan controls and dual-read/dual-write fallback paths.

Migration code may read supported-window persisted formats once. There is no permanent
old-format execution or import mode after success. Historical exports, original
imports and backups remain immutable evidence, not alternative live settings.
Recovery from an interrupted upgrade is internal fault recovery; an unreadable
future schema is rejected unchanged. Whole-root backup/open remains the normal
current product feature. An old application must refuse an upgraded root.

Catalog updates require no “accept bundled drafts” action. User customizations
and pinned prescriptions are protected by ownership and snapshots rather than
by retaining the old delivery interface. Normal actions to review changed
guidance or activate a revised plan are still required: seamless upgrade cannot
invent illustrations, approval or user training facts. If a migrated active plan
contains an ineligible action, show the exact content issue in its ordinary
detail view and block only new starts, while keeping history and paused work
available. This is the new rule, with no switch to restore the missing-image
exemption. A complete, unchanged, eligible plan requires no new approval.

### 12.8 External Handoff Contract

Use `training_feedback.plan` version 2 for all new imports and
`training_feedback.evidence` version 2 for new exports; define their version
constants independently. Only the current plan-import contract is accepted in
0.7.0. A newly supplied v1 file gets a clear current-format error and the current
schema, not a compatibility converter or version selector. Plans already stored
in the root are converted internally under Section 12.7. Their original imported
files and original exports are not rewritten or re-imported.

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

Section 9.1 is the single active work list. Completed A–G milestones and the
local part of H are in the [0.7.0 delivery archive](archive/0.7.0/development.md),
not additional pending development plans. The [contract annex](contracts/0.7.0-contracts.md)
owns detailed current serialization/mapping. Changes to backup, root switching,
fixtures, resources and current imports must be covered in their implementing task.

Required verification covers:

- Supported baselines generated/opened by actual 0.6.0/schema-14 and
  0.6.1/schema-16 programs, using
  isolated synthetic data with renamed/missing-key actions,
  custom text, overrides, images, review attachments, active/draft plans,
  terminal and paused sessions, next-day feedback, retractions and original files.
  Preserve an untouched baseline and compare logical facts/resource hashes.
- Reject out-of-window development roots before writes, with the reinstall/new-root
  instruction; preserve future-schema rejection and fresh initialization coverage.
- Missing image vs corrupt image vs changed hash, no-image drafts with prior
  review evidence, enabled-but-ineligible state, bundled and custom images,
  renamed families, repeated exercises in groups, asymmetric sides and mixed units.
- Failure at backup, staging, SQL conversion, asset publication and cleanup;
  disk/access errors, stale previews, competing opens, repeat startup and
  root switching. No partial successful upgrade or fabricated approval.
- Catalog withdrawal after plan activation; new-start blocking; resumed frozen
  work; history/export/backup restore with a newer catalog lacking that movement.
- UI inventory and source review proving removal of manual bundled acceptance,
  old-settings/legacy mode controls, old-format import selectors and fallback
  runtime branches. Read-only provenance and recovery artifacts are labelled
  as evidence, not selectable settings.

Use PowerShell 7 and temporary roots/locators. Run meaningful affected tests
within Section 9.4's stage budget (each 070 work item is development, the 0.7.0
release is minor), Ruff and `git diff --check` for implementation delivery.
Run packaging checks when the payload/fixtures change. The packaged
runbook must identify the 0.7.0 candidate and actual target schema, including
ordinary-user in-place installation, auto-conversion, backup/reopen, uninstall
data isolation, Chinese/space-containing paths and 100/125/150% real-desktop
scaling. Existing independent-environment requirements still apply.

### 12.10 Release Exit And Documentation Ownership

0.7.0 is ready only when all 070 work items pass their acceptance, the current
image/content inventory is explicit, and the initial usable plan's referenced
actions have actual bundled illustrations and satisfy the new rules. All 36
catalog entries must retain their identity and classified readiness; items
without finished illustrations remain visible drafts and cannot be advertised
as usable. Source prompts, filename mappings and synthetic images are not
delivered artwork or real expert review. Actual content review and first-usable
release evidence remain subject to Section 10; do not reinterpret the retained
unreviewed-with-valid-images option as completed review coverage.

No supported-upgrade success claim may rely on a reset root, manual re-import,
compatibility settings, changed historic doses or a previous candidate's acceptance.
Verify clean first use, supported upgrades and unchanged rejection of expired roots.
Record application/catalog/schema identities and unresolved gates for the exact build.
Independent 8-B2 remains pending. The user's future decision to begin personal
observation does not establish technical acceptance of the candidate.

This document owns product/architecture/migration contracts. The content
document owns family membership, aliases, technique and proposed doses. The
guidance review runbook owns the version-specific review procedure, and the
packaged acceptance runbook owns candidate-specific execution evidence. Update
all four as implementation is delivered; keep completed procedures in their
version archives and never offer them as selectable runtime behavior. Root task
records capture development work and verification rather than duplicating these specifications.

## 13. Version Retention And Development Data Policy

Decision accepted: 2026-09-20; documented: 2026-09-21. The project remains in
development. This policy supersedes unlimited historical-document retention and
unbounded migration-chain support. Runtime enforcement was implemented as
070-R2 on 2026-09-21 (schema-14 lower bound, pre-write refusal); workspace
artifact rotation is DEV-CLEAN, not completed by documenting the policy.

### 13.1 Application Versions And Schema Changes

- Keep the current application version plus its two immediate predecessors.
  Count distinct version numbers, including patch versions, not GitHub commits.
  Several commits with the same version consume one slot. Record the actual
  commit/source snapshot/build identity for each retained version.
- The current window is **0.7.0 / 0.6.1 / 0.6.0**. Their database baselines are
  **22 / 16 / 14** respectively. A subsequent 0.7.1 rotates out 0.6.0; if it changes
  the database, its next schema is 23. This is an example, not a performed bump.
- Every subsequent database schema revision must bump the application version
  at least by one patch in the same change. Do not append several schema revisions
  while continuing to call the application 0.7.0. A minor/major bump may accompany
  a schema change; an application-only fix may keep the existing schema.
- Existing intermediate schemas 15 and 17–21 retain their historic numbers; do
  not fabricate released application versions for them. Required internal steps
  may remain while a supported endpoint depends on them, but are not additional
  independent supported releases. Decide intermediate-root handling explicitly
  in the version/schema mapping; never equate a numeric range with release support.
- Maintain application version, database schema, catalog/content version and
  external wire-contract version separately. Changing a wire schema requires an
  application bump too, but need not change the database schema without a storage
  change. Retaining an old contract as evidence does not enable its import.

### 13.2 Retention And Supported Database Upgrades

Complete development plans, task records, acceptance evidence, schema documents,
contract snapshots, synthetic baselines and runtime migration entry support share
the three-application-version window. Current specifications keep valid rules and
open work; completed work goes under `docs/archive/<version>/` or local
`.planning/archive/<version>/`. Archiving is not permanent retention.

At rotation, inventory references, merge still-valid rules into current documents,
then remove the expired version's full records and exclusive fixtures/helpers.
Keep only schema definitions and migration steps needed to create the current
database or upgrade a retained version. Consolidate new-database initialization
without rewriting already-applied migration semantics in the supported window.
Git/GitHub commit history stays intact; do not create an unbounded second archive.

Supported older roots receive normal automatic recovery/conversion with frozen
facts preserved. Roots older than the support window must be detected read-only
and refused before migration or other writes, with an actionable message such as:

> 此开发数据版本已超出支持范围，请重新安装当前版本并新建数据目录。
> 原数据目录已保留，不会自动删除或重置。

Reinstalling program files does not recreate the independent root. The user must
explicitly choose a new empty directory; installation/uninstallation never deletes
the old root or locator. Do not auto-import the unsupported database or offer a
legacy runtime mode. Unsupported future roots also remain unchanged. New roots
must load the complete current bundled catalog without relying on any older root.

Retention is for development artifacts and compatibility code, not permission to
purge personal data, original answers/exports or historical evidence within a
retained root. Active test-budget ledgers must not be reset during cleanup.
Unclassified local files require inventory before disposal.

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
