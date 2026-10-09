# TrainingFeedback Development Plan

Current application/schema baseline: [version history index](history/README.md).
Public-release acceptance, external review and W4 have separate gates below.
Last updated: 2026-10-08

This is the authoritative product scope, domain model, and delivery plan.
The [initial catalog and plan proposal](initial-exercises-and-plan.md) defines
seed content and proposed doses. Use these entry points:

- [Product rules and current baseline](#1-product-goal): Sections 1–8.
- [Delivery gates](#9-delivery-gates): stable release and follow-up boundaries.
- [First usable release](#10-first-usable-release-definition): product capability and release boundaries.
- [Current catalog/group contract](#12-current-catalog-and-group-contract):
  ownership, eligibility, execution, removal and supported-root conversion.
- [Version and development-data policy](#13-version-retention-and-development-data-policy):
  application/schema identity, formal-release support policy, unsupported-root
  safety and the user-directed personal-data transition.
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

An exercise describes how a movement is performed. A plan describes one complete
ordered training sequence. There is no user-facing training-day concept or
day selection. Dose, set sequence, rest, and plan-specific notes
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
explanatory note. Action and set orders are positive and unique within
their parent. Action phases are `preparation`, `main`, and `cooldown`.

Plan revisions move from `draft` to `active` to `superseded`. Editing an active
revision creates a new draft. A saved draft has a name, at least one action or
group, and sets in every action; it may reference guidance that has
not been reviewed. Activation additionally requires enabled exercises whose
guidance in use has complete text and valid required images under Section 12.4.
Review state does not gate activation: unreviewed
guidance is reported before confirmation and recorded in training evidence, but
it does not block activation or training. The complete prescription
and differences from the current revision are shown before confirmation.
Saving a draft does not activate it. Superseding the previous revision and
updating the active revision pointer form one transaction.
Section 12.11 owns the distinction between editing a draft, cloning an
independent plan and explicitly upgrading an active plan.

The editor places an action list beside the selected action's editable prescription
and per-set table by default, without a separate read-only summary or an edit-entry
button. Existing prescriptions use the dialog's single save/cancel footer; switching
between independent actions retains unfinished input in the unsaved editor.
Moving between a group and its members first validates and stages related edits in
the unsaved document so their copies cannot overwrite one another. Equal-set entry
is an optional collapsible batch-fill tool, with explicit confirmation before
replacing current values and notes. Opening or closing that tool does not change
the table. Invalid values block saving or switching between a group and its members
without losing the input. Ordering updates the document once and moves existing
navigation rows without recreating the selected editor or reloading its guidance.
Revision diffs cover action additions,
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
plan as a readable hierarchy of ordered actions or groups, members and
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

### 4.1.1 Plan Editor Sizing And Interface Scale

The native interface uses one font-relative logical unit `u`, with a readable
system-font baseline equivalent to 14 logical pixels at normal Qt DPI. Qt owns
system DPI scaling; application dimensions must not multiply devicePixelRatio
again. Font scale is independent of screen resolution and window size.
On the user's physical 3840×2160 display, the main window defaults to a physical
2560×1440 client area (16:9). Use two thirds of full screen width and height in
Qt logical coordinates, preserving 16:9 within the smaller axis for other aspect
ratios. Thus a 2560×1440 screen defaults to about 1707×960 and a 1920×1080 screen
to 1280×720. Clamp to 96% of available screen space if necessary. This window
size policy is independent of custom font percentages; window resizing remains
free and triggers the existing responsive layout. Owned font sizes, spacing,
icons and explicit dimensions are expressed
as unit multiples, compiled into logical dimensions at the Qt boundary. A
one-pixel separator is permitted. Native layout defaults also derive from `u`.

Settings offer follow-system and custom scaling from 80% to 200%, in 10% steps,
with text/button/input previews. Changes apply immediately and persist in local
interface configuration, independently of training roots. Percentages multiply
the compact font baseline; existing custom preferences are preserved. Ctrl/Cmd plus/minus
adjusts custom scale; Ctrl/Cmd 0 restores follow-system. Scaling never changes
training facts, catalog content or root/schema compatibility.

The plan dialog sizes itself within the default main-window canvas: width
`min(canvasWidth, max(60u, 85% of canvasWidth))`, height
`min(canvasHeight, max(36u, 88% of canvasHeight))`; screen bounds take precedence
over the minimums on small displays. Header and save/cancel footer stay
outside scroll regions. Plan name remains visible; expandable basic information
uses at most two columns (20u minimum per column) and an internal scroll region
bounded by 30% of dialog height. Multi-line edits initially show at least three
lines and can be enlarged with a vertical grip without moving the footer offscreen.

At pane viewport width >=96u, display action navigation, prescription and guidance
beside one another. Navigation uses 17% within 13u–18u, guidance uses 28% within
22u–30u, and the center consumes the remainder. At 64u–96u, guidance becomes a
drawer with an entry at the center's upper right. Below 64u, action navigation
becomes horizontally scrollable name capsules. Selected action/member and
unsaved edits survive layout changes. Sibling drag ordering and context-menu
commands use the same document operations as existing move buttons.

Parameter fields use an adaptive grid with 14u minimum fields. The per-set table
uses base-size text and relative widths: # 2, set order 4, value 5, unit 4,
per-side 3, rest 6, operations 4. Keep the existing verbatim per-set note column
(weight 4). The table's minimum is 28u, increased if embedded controls require
more width; a narrower center scrolls horizontally rather than crushing columns.
Rows grow from a 2.5u minimum. Up to eight rows use content height; more rows
scroll internally within half of the center viewport. Deleting a set and
confirmed equal-set filling retain the existing validation and rest semantics.

Guidance combines full-width proportional images and selectable wrapping text
with 1.6 line height; sticky section anchors remain outside the scroll region.
Captions wrap fully. Images open in a viewer bounded by 90% of the smaller
available screen dimension. Wheel events stay in the hovered explicit scroll
region, including at its boundary. User text is neither elided nor rewritten to
make the layout fit; explicit edit/read regions may scroll.

The main training page presents start/resume and history in separate cards,
side by side from 66u of usable content width only when both cards' measured
minimum widths fit, and stacked otherwise. The start card reserves at least
18u and the natural width needed by its longest button and card margins.
Action toolbars wrap using full button labels and never shrink buttons below
their natural width. The library gallery, multi-action picker, group member
list and plan revision navigator use independent rounded frames. Text height is
measured at current font/viewport width, with wrapped names and distinct hover,
selection and keyboard-focus states. Gallery columns and card heights recalculate
on font, content and viewport changes; no stale per-item fixed size is retained.
Gallery images and their wrapped captions are centered. Gallery columns divide
the available viewport width, with native item padding disabled so the final
column is not pushed to the next row by duplicate insets.

The requested scale/DPI/layout criteria describe intended behavior. Current
verification remains governed by Section 9.1: unobserved client layout is not a
pass and does not create a bulk manual acceptance obligation. Native mapping and
source-follow-up evidence: [plan interface design](designs/plan-interface-scaling.md)
and [development record](history/0.8.13/plan-interface-2026-10-08.md).

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
provider. New imports use `training_feedback.plan` v4 and new evidence uses
`training_feedback.evidence` v4. The canonical runtime schema is
`src/training_feedback/contracts/plan-v4.schema.json`;
`src/training_feedback/data/plan_contract.py` loads it, domain/application code
validates it, and the handoff repositories produce portable evidence.
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
the database. Future schemas and development schemas outside the applicable
support boundary are rejected unchanged; the historical schema 22 exception is in
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
The historical 0.7.5 first-open reset was the one-time exception summarized in
Section 13.4; installing program files alone does not perform it.

Windows distribution uses a directory payload with `icon/TrainingFeedback.ico`
and a per-user Inno Setup installer with stable application identity, normal
shortcuts and an uninstaller. The default installation directory is
`%LocalAppData%\Programs\TrainingFeedback`. When the stable application identity
has an existing installation, Setup selects that previous program directory
before considering the default. The selected old or new directory is still
validated before any write. Installation and upgrade never own the locator or
data root. Normal uninstall removes program files only; the optional data-removal
path requires the separate path and ownership checks defined by the
[v0.8.0 design](releases/0.8.0/design.md).

### 7.1 New-Root Directory Creation

**Create a new data root** asks the user to select a *parent*
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

**Open an existing data root** selects the root directory itself, including
roots created by earlier application versions and copied backups; opening must not append
another directory layer. Use the same create behavior from first launch and
Settings when creating and switching to a new root. The separate backup and
root-copy destination flows retain their own complete-root semantics.

Acceptance covers a redirected Documents suggestion, create-path
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
Failed ordinary migrations preserve the prior version; the historical exception
is recorded in Section 13.4.
UI tests may use offscreen Qt; all tests use temporary databases and locators,
never real user data. One QApplication is shared for a whole run, so a UI test
must let Qt destroy the windows it created; widget graphs abandoned to Python
garbage collection crash the interpreter later in the run. Existing date-boundary
cases cover 01:59, 02:00, and 02:01; this inventory does not require execution.
All test selection is limited by Section 9.1.

## 9. Delivery Gates

### 9.1 Release And Follow-Up Boundaries

#### 当前个人使用阶段的验证政策（2026-10-03）

本项目将在相当长时间内仅供用户本人使用，通过开发和实际使用反馈逐步改进。
GitHub Releases 是安装包和后续更新的默认分发渠道。普通更新、安装包上传、
版本提升和开发收尾均遵循本节，
不自动触发完整回归、安装验收、内容审核或 W4。

- 每次开发更新自动测试最多 **3 项**，通常 **0～1 项**；没有具体启动失败风险时
  为 **0 项**，纯文档修改不运行应用测试。
- 唯一允许的测试范围是本次改动可能导致应用打不开：启动报错退出、启动必需资源
  无法加载、数据初始化或打开失败导致无法进入应用。选择检查前必须写明具体改动与
  启动失败的因果关系；不能按模块名或“保障质量／数据安全”泛化选取。
- 界面、搜索、训练流程、保存内容、导入导出、备份、性能等问题，等用户使用反馈后
  逐步修复；不预先安排全面回归。收到反馈也不自动增加其它功能回归。
- 不因版本级别、打包或收尾增加额度。独立场景、参数化场景和脚本中的功能验证
  均计数；不打包大量场景进一个用例，不拆任务或换 scope 绕过上限。
  修复后只重跑失败或直接受影响的原检查，记录重复执行，不循环采样。
- 人工测试默认 **0 项**。仅在有具体启动风险且代码检查无法确认时，最多请用户
  在下一次正常使用中观察一次能否打开；不专门组织验收，不要求录屏、计时、
  填表、重复安装卸载、切根、逐页检查、完整模拟训练或批量故障操作。
- 160 次计时、预热、60fps 录屏、性能统计及 200 ms、p50/p95、改善百分比等门槛
  已取消。既有测量仍是事实记录，未达旧指标不再阻止当前开发交付。
- 原范围外的未运行检查记为“按新政策取消要求”，不是通过，也不是以后必须补齐
  的待办。未运行本身不构成开发收尾障碍；实际已知启动失败仍须修复。

以上只收缩验证义务。数据隔离、事务、历史冻结、用户原文、未知不等于零、
未知／不支持根在写入前拒绝等产品实现要求继续有效。任何自动检查均使用隔离
合成根，不接触真实数据。旧测试库保留，其存在及工具的较大容量不构成执行许可。
具体步骤和计数由 [开发流程](development-workflow.md) 与
[测试说明](../tests/README.md) 承接。

Local delivery records the actual source/build identity and known issues. Build an
installer only when that deliverable is in scope; packaging does not add a test
gate. A candidate certifies only checks actually performed on that exact build.
The [version history index](history/README.md) owns current identities and routes
dated evidence. Historical failures, passes and unrun results are not rewritten.

Publishing an installer to GitHub Releases is an authorized distribution event
and does not activate a larger verification matrix. A future formal compatibility
or wider public-support commitment must be declared separately; do not silently
replace the current three-check policy with a stored public checklist.
External content review concerns exact content/image
versions and actual sources. Personal-data transition remains the user's decision
under Section 13.3; no test result transfers synthetic facts or activates a plan.

Before a user-declared formal release, old-application-version compatibility
tests and support promises remain disabled. The first formal release establishes
a baseline; later formal releases select one or two predecessor formal versions
under Section 13. A formal declaration alone does not authorize bulk testing.
Future formal/public verification scope must be explicitly settled at that time.

#### GitHub update discovery and installation

Starting with application 0.8.1, each process that successfully opens a main
window checks this repository's latest stable GitHub Release once, after the
window is visible. The request is asynchronous and unauthenticated and must not
read or write the selected data root. Switching roots reuses the process result;
it does not start another automatic request. A manual Settings action may retry.

Only an exact `vMAJOR.MINOR.PATCH` stable Release participates. Drafts,
prereleases, malformed responses and network or rate-limit failures never block
startup. Failures remain quiet outside Settings and are not retried automatically.
An equal or older published version does not display an update notice.

A newer version displays a clickable hollow-circle exclamation mark in the main
sidebar. Release text is shown as untrusted plain text. An installable update
requires exactly one uploaded `TrainingFeedback-<version>-Setup.exe`, a valid
GitHub repository download URL, a positive byte size and a SHA-256 digest.
Otherwise the notice remains available but only the Release page can be opened.

After the user chooses **download and install**, the application streams the
Setup into a unique temporary directory without touching the selected data root.
It must match both the declared byte size and SHA-256 before execution. A
download, write, size, digest or launch failure never executes the file and
keeps retry and browser-download choices available. On successful validation,
the application hands Setup to a detached Windows launcher, exits completely,
and only then starts Setup. The launcher must be ready before the application
requests normal exit. It holds an inherited wait/terminate handle to that exact
application process; after a 10-second normal-exit grace period it can terminate
that process independently of Qt, Python threads or interpreter shutdown. It
must confirm process termination before starting Setup, and must not terminate
other instances or select targets by executable name. Launcher preparation
failure leaves the application open. The launcher waits for Setup to finish and removes
that exact application-owned temporary update directory. On later startup, the
application also makes a best-effort cleanup of direct, non-link temporary
directories whose names and complete contents strictly match its updater
artifacts; it never treats this as permission to sweep other temporary content
or any data root. A handoff failure does not exit and keeps the retry and
browser-download choices available. Opening the GitHub Release or downloading
through the system browser remains an explicit secondary choice, not the default
path. The installer is still interactive: existing installer ownership,
directory validation and data-root separation govern the overwrite update.

The 0.8.1 discovery feature was itself bootstrapped by one final manual
installation from 0.8.0. Likewise, an existing 0.8.2 process still uses its
browser path to obtain 0.8.3; application-managed download begins after 0.8.3 is
installed. GitHub distribution remains distinct from a formal compatibility or
public-support declaration, external content review, personal-data transition
and W4.

### 9.2 W4 Real-Use Gate

W4 begins only after the user authorizes the personal-data transition in Section
13.3. Required actions must have complete text and valid images, be explicitly
enabled, and belong to a fully confirmed active plan. Personal use and W4 do not
add software checks beyond Section 9.1 or require the cancelled acceptance work.
Unreviewed guidance is disclosed and frozen in session evidence.
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

This gate is dormant in the current personal-use stage. GitHub Release
distribution of an identified installer does not activate it. Only an explicit
formal compatibility or wider public-support declaration can open a discussion
of its scope and verification policy; required evidence must then complete
before making that support claim. Local packaging or installation does not
trigger it automatically.
The [packaged acceptance runbook](packaged-acceptance-runbook.md) owns the
candidate-specific scenarios and evidence form.

Required public-release coverage:

- An independent Windows x64 environment without the build checkout or Python,
  using an ordinary non-administrator account.
- For later formal releases, actual binaries of the selected one or two
  predecessor formal versions, with isolated representative roots for upgrade
  preservation. The first formal release establishes the baseline and has no
  predecessor-formal-version upgrade to test. Development candidates are not
  automatically supported baselines; same-version relocation is not upgrade
  evidence.
- Installed backup/recovery, root isolation, session/history/export agreement,
  uninstall/reinstall boundaries and real-desktop scaling at 100%, 125% and 150%.

Identify each candidate by its original manifest, hashes and source snapshot.
Offscreen checks cannot replace independent runtime or desktop evidence;
unavailable scenarios stay `not run`.

### 9.4 Verification And Record Ownership

Data preservation, frozen history, verbatim text and transactional rollback
remain implementation requirements. They do not independently authorize tests:
Section 9.1 exclusively limits current verification to concrete startup risks.
Tests use synthetic temporary roots and locators, never personal data. The version-independent
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

Each local update follows the minimal verification policy in Section 9.1 and
records actual delivery under the [workflow](development-workflow.md).
An installer is built only when requested or part of the agreed deliverable;
no full installed checklist is required. The initial plan remains a proposal;
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

Clipboard import, provider-specific adapters and advanced trend analysis are
optional later scope, not unresolved first-version requirements. The current
application-owned JSON/file contract is defined in Section 4.6.

<a id="12-070-development-contract-planned"></a>

## 12. Current Catalog And Group Contract

This catalog and group contract remains the product rule until deliberately
revised. Historical source delivery is discoverable through Git history;
Section 9 owns delivery gates and Section 13 governs version changes.

The application provides an application-owned bundled catalog, exercise families
and variants, continuous plan action groups, mandatory illustration checks,
and reviewed exercise removal. Current behavior uses one runtime model; Section
13.4 records the historical 0.7.5 exception. Native Windows/PySide6, local-only use,
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

The logical structure is plan → ordered items (single action or action
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

Plan editing must support creating plans, adding/removing/reordering single
actions and groups, moving members, rounds, side order, per-round doses and rest.
Removing the penultimate group member must explicitly dissolve the group or
cancel, not leave an invalid one-member group. Invalid input stays on screen.
One save commits all children and ordering or nothing. Activated revisions are
immutable and are copied to edit; Section 12.11 distinguishes the planned
`Clone` and `Upgrade` operations. Diffs use stable item identities plus readable
item/group/member paths, and include membership, ordering, side sequence, rounds,
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
completed history. The historical 0.7.5 first-open reset deleted the plan/training
scope in Section 13.4. Opening or switching to a supported root validates the
marker, configuration, schema and current library model before use. No directory
scanning or old Exercises@home database access is allowed.

Historical conversions and retired fixtures do not expand the current support
boundary; their dated design is in version history. Roots outside the applicable
boundary are rejected read-only with the reinstall/new-empty-root guidance of
Section 13.2; schema 22 roots were the explicit 0.7.5 exception. Do not offer a
migration wizard, compatibility setting, legacy library, fallback reader or
implicit import for an expired root.

After formal release, supported schema changes use a version bump, pre-write
validation, recoverable snapshots and transactional migrations. They preserve
frozen facts without inventing approval, images, physical results or user
decisions. Before formal release, an old root has no upgrade promise, but a
refused root remains unchanged. The 0.7.5 schema 22 reset in Section 13.4
discarded its specified plan/training facts without a backup. Normal root
backup and restore remain separate user actions outside that one-time reset.

### 12.8 External Handoff Contract

Use `training_feedback.plan` version 4 for new imports and
`training_feedback.evidence` version 4 for new exports; define their version
constants independently. Only the current plan-import contract is accepted. A
newly supplied older-format file gets a clear current-format error and the
current schema, not a compatibility converter or version selector. Plans
already stored in a usable current root retain their frozen facts; their
original imported files and original exports are not rewritten or re-imported.

V4 carries namespaced action keys, exact content references, family/variant
identity, ordered standalone/group items, rounds, side order, per-round sets,
all rest boundaries and source rationale. Training days have order and items;
they have no user-defined name. Imports create drafts only and cannot
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

Section 9.1 exclusively determines current verification scope. The
[contract annex](reference/contracts/0.7.0-contracts.md) preserves the historical
serialization/mapping baseline. Existing functional, failure, UI, backup,
image, session and export cases remain available as reference; they are not an
execution backlog or mandatory regression matrix.

Preserve current initialization, refusal before writes, frozen facts and the
other specified behaviors in implementation. Run a check only when this update
has a concrete application-startup failure risk, within the same three-scenario
limit. Other issues are handled from actual use feedback.

Old-version compatibility and independent public acceptance stay dormant under
Section 9.1. Their stored scenarios neither block personal development nor add
work before personal use. The [workflow](development-workflow.md) and
[packaged runbook](packaged-acceptance-runbook.md) record only applicable, actual
checks and their exact candidate identity.

### 12.10 Release Exit And Documentation Ownership

Usable actions meet Section 12.4 and the bundled content/image inventory must
report truthful readiness. A technically valid illustration does not establish
expert review. Dated release exits and candidate checks belong to version
history and Git history, not to this current specification.

Keep local-release, external-review, personal-use and W4 results distinct.
Independent 8-B2 is deferred/not run and is activated only by an explicit public
release request. It is not a prerequisite for local packaging or local release.

After formal release, no supported-upgrade success claim may rely on a reset
root, manual re-import, compatibility settings, changed historical doses or an
earlier build's acceptance. The 0.7.5 reset is historical deletion evidence,
not preservation evidence. Current verification follows Section 9.1; neither
formal-release wording nor a version number expands its scope automatically.
Any actual local observation and later explicitly scoped public acceptance
retain their own results and candidate identity.

This document owns product/architecture/migration contracts. The content
document owns family membership, aliases, technique and proposed doses.
Candidate evidence and task records document actual work without duplicating
these specifications.

### 12.11 Plan Authoring And Identity

New-plan entry and editing use one page: an ordered action/group list beside the
selected action's exact-version guidance and illustrations, with a concise
prescription summary and per-set table. Technical classification and identity
fields do not appear as guidance. The new page starts with an empty action list;
adding an action or group requires no parent selection. Searchable, multiple exercise selection adds
unsaved actions; groups and members use the same detail area. The user supplies
set values, count, unit, per-side choice and applicable rest, including an
explicit zero for no prescribed rest. The final set has no additional set rest:
its cell says 不适用 and the boundary rest is entered separately. Bilateral
actions have no side-switch rest. These structural zeros are not user-entered
rest facts. Blank applicable fields stay unknown on screen and saving identifies
the required field in Chinese; numeric conversion errors do not leak to users.
Legacy aggregate unknown fields remain unknown. No catalog proposal or UI placeholder is
silently saved as a user dose. An explicit equal-set fill may replace existing
values or notes only after confirmation. It copies rest only when both the
source and target set have applicable set rest; selecting a terminal set does
not erase other sets' prescribed rest. Incomplete or invalid input remains
visible, blocks switching or saving as applicable, and identifies the field to
repair. A valid draft still requires a name, a nonempty action list and complete action
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
Changes to item/group structure, action identity or content, item/member order,
phase, first side or side sequence increment `AA` and reset `DD` to `00`.
Changes confined to dose, rest or other plan text increment `DD`; combined
changes use the structural rule. A rationale alone does not create an upgrade.
Before every draft save, show the changed fields and resulting code, recheck
uniqueness transactionally and recompute after later edits; activation fixes the
code. Both suffixes have a two-digit minimum and may grow past 99. Base numbers
are `001`–`999`, are unique within the root and never wrap or silently reuse.
Internal revision IDs/ordinals remain for associations, but the plan page shows
the code rather than automatic `v1`/`v2` labels.

Database schema 24 uses the current plan/evidence wire contracts v4.
The existing `days` wire/storage envelope remains an internal representation;
there is no new schema or wire shape. New manual drafts use one container.
Reading and whole-plan execution concatenate existing containers by their order
and each item's order. Editing projects this sequence into one unsaved container,
retaining item/member identities, all prescriptions and original text; saving
shows the resulting structural diff. Cancelling does not modify stored revisions.
Starting from the UI executes the complete selected plan, with a preview and
freshness token covering every action. New sessions freeze that sequence and the
original source revision; existing sessions resume their original frozen scope.
There is no automatic root migration or rewrite of active revisions or history.
The plan-import rationale may be empty. A new import receives a root-local base
number; an upgrade import identifies the target by base code and follows the
same difference classification. Only v4 is accepted; v2/v3 imports receive
the current-format error. JSON/Markdown evidence and new training snapshots
show the complete code consistently. Saving a draft never activates it, and
activation retains the existing eligibility and explicit confirmation gates.

The historical schema 23 roots upgrade in place to schema 24 in one transaction. The upgrade
removes only the plan-day name columns and historical session name snapshot;
plans, training history, feedback and review records remain. A failed upgrade
rolls back the complete change.

### 12.12 Action Detail And Guidance Reading

Action-library details, external-review reading regions and frozen-guidance
dialogs share read-only reading components. At 47.5u of available
body width, illustrations and guidance appear side by side with an initial
45/55 split and adjustable divider; narrower bodies show guidance/illustration
tabs with guidance selected initially. Resizing preserves guidance position and
group state. Training execution and library card layouts retain their existing
components.

Illustrations fit both available dimensions without cropping or stretching.
Declared images retain order, caption and position even when unavailable;
multiple images are paged rather than stacked. Captions wrap to display the full
original text rather than being limited to two lines. Clicking a valid image opens
a resizable viewer with fit, actual logical size, wheel zoom, pan and Esc close.
Manual zoom ranges from 10% to 400%; fit may go below 10%. Rendering always
uses the original pixels and refreshes for display DPI changes, without changing
files, hashes, eligibility or review status.

Guidance has one vertical scroll container. How-to and safety groups default
open; understanding and progression/regression groups default closed. User
folding persists during resizing and resets on action/content change. Original
field text, line breaks, step order and numbering remain accessible and
selectable; empty fields explicitly say 未填写. No image-derived instruction or
generated summary becomes guidance.

Details put management in a grouped More actions menu bound to the exact
displayed target on opening and execution. Selection, enablement, editing,
copying, image replacement, review and lifecycle operations keep their existing
service, confirmation and transaction boundaries. Enable/disable shows only the
applicable entry. Content information and current-version review events are
read-only dialogs, separate from reading and write operations. Events appear
newest first with recorded/actual times, source, original notes and attachment
information; unknown time, absent attachment and no events are explicit.
Frozen reading uses session content and session image services only, never a
fallback to the latest catalog. No reading action writes personal facts.

The detailed layout design is in
[动作详情与指导阅读重新设计](designs/exercise-reading-redesign.md);
implementation evidence belongs to [v0.8.11](history/0.8.11/development.md).

## 13. Version Retention And Development Data Policy

The 2026-09-20 three-version development policy is superseded by the user's
2026-09-29 decision: old-version compatibility testing is closed until the user
declares a formal release. This is not permission to alter or delete an old
data root. The current application/schema implementation map is in the
[version history index](history/README.md); dated implementation evidence is in
version history. Rotation procedure is in the [workflow](development-workflow.md).

### 13.1 Application Versions And Schema Changes

- Before formal release, keep an accurate current application/schema map but do
  not promise that a new application opens any older application version's root.
  Existing development paths may remain during an audit, but do not create
  new compatibility obligations. The first formal release establishes a
  baseline. For later formal releases, select one or two available predecessor
  **formal** versions, record their exact source/build identity and support
  paths. Any future endpoint verification must first be explicitly scoped under
  Section 9.1; a formal declaration does not automatically increase current tests.
  Development candidate numbers do not automatically fill those slots.
- Every subsequent database schema revision must bump the application version
  at least by one patch in the same change. A minor/major bump may accompany
  a schema change; an application-only fix may keep the existing schema.
- Historical intermediate schemas retain their original numbers; do not
  fabricate released application versions for them. Required internal steps
  may remain while a current or formally supported endpoint depends on them,
  but are not additional supported releases. Decide intermediate-root handling
  explicitly in the version/schema mapping; never equate a numeric range with
  release support.
- Maintain application version, database schema, catalog/content version and
  external wire-contract version separately. Changing a wire schema requires an
  application bump too, but need not change the database schema without a storage
  change. Retaining an old contract as evidence does not enable its import.

### 13.2 Retention And Supported Database Upgrades

Current specifications keep valid rules and open work. Completed version facts
are tracked under `docs/history/<version>/`; local `.planning/archive/` is
historical execution context, not a substitute for tracked release evidence.
Before formal release, slimming may remove duplicate or obsolete development
records, fixtures and compatibility entries after reference and data-safety
audit; preserve any still-current product rule and candidate fact in an
appropriate tracked document or Git history. After formal release, keep the
selected one-or-two-version support material and required upgrade paths.
Archiving is not permanent retention.

At version rotation or slimming, inventory references, merge still-valid rules
into current documents, then remove proven obsolete records and exclusive
fixtures/helpers. Keep schema definitions and steps needed to create the current
database or upgrade a formally supported version. Consolidate new-database
initialization without rewriting already-applied migration semantics in the
selected support range. Git/GitHub commit history stays intact; do not create
an unbounded second archive.

Except for the historical one-time rule in Section 13.4, the current root
reopens without changing frozen facts; formally supported upgrades may use
declared automatic recovery/conversion. Roots outside the applicable boundary
are detected read-only and refused before migration or other writes, with an actionable
message such as:

> 此开发数据版本已超出支持范围，请重新安装当前版本并新建数据目录。
> 原数据目录已保留，不会自动删除或重置。

Reinstalling program files does not recreate the independent root. The user must
explicitly choose a new empty directory for a new root. Ordinary uninstall
preserves the root and locator. Starting with 0.8.0, an interactive uninstaller
may offer a separate, default-unselected deletion of only the locator's exact
current root, after ownership, version, path, exclusive-handle and confirmation
checks. Silent uninstall retains data. Historical roots and external backups
are excluded. Interrupted deletion retains a recovery record and prevents opening
the partially deleted root; retry requires the same verified objects. The
[uninstall design](releases/0.8.0/uninstall-design.md) specifies the boundary.
Do not auto-import an unsupported database or offer a
legacy runtime mode. Unsupported future roots remain unchanged. New
roots load the complete current bundled catalog without relying on an older root.

Artifact cleanup is not general permission to purge personal data, original
answers/exports or historical evidence within any root. Section 13.4 records
the historical 0.7.5 reset decision. Active test-budget
ledgers must not be reset during cleanup. Unclassified local files require
inventory before disposal.

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

### 13.4 Historical 0.7.5 Reset Exception

The 0.7.5 schema-22 reset was a historical one-time exception and does not
define current upgrade behavior. Its full design, deletion scope and recovery
semantics are retained with the [0.7.5 historical record](history/0.7.5/reset-design.md).
Current and future behavior follows Sections 13.1–13.3 unless a new rule is
deliberately adopted in this specification.

From 0.8.0 onward, unfinished historical reset or upgrade journals are refused
read-only. No historical reset deletion or migration is resumed. The original
root remains unchanged and the developer must choose a new empty root.
