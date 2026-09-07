# Phase 2 And Phase 3 Implementation Design

> Note: file names in this document reflect the design-time layout. The current layout is documented in README.md and AGENTS.md (e.g. data/repositories.py is now data/exercise_repositories.py; ui/placeholders.py was removed).
Status: Phase 2 and Phase 3 implementation complete
Last updated: 2026-09-05

This document records the approved implementation details for the exercise
catalog/guidance and versioned-plan phases. Product scope remains authoritative
in `docs/development-plan.md`; seed names and proposed doses remain
authoritative in `docs/initial-exercises-and-plan.md`.

## 1. Boundary

Phase 2 answers: what is this exercise and how is it performed?

Phase 3 answers: what does this plan prescribe on this training day?

The boundaries are strict:

- exercise guidance is not a plan prescription;
- a plan does not copy the complete guidance body;
- guidance identity and relationships remain SQL;
- guidance content starts as validated JSON;
- plan days, actions, and planned sets remain normalized SQL;
- no embedded AI inference is added;
- no exercise or plan data is silently activated.

## 2. Phase 2 Exercise Catalog

### 2.1 Seed scope

The first seed contains 14 exercises:

- Main: `臀桥`, `蚌式开合`, `椅子深蹲`, `死虫式`, `蝴蝶臀桥`, `跪姿臀冲`,
  `静态臀桥`.
- Supporting: `仰卧360°膈肌呼吸`, `小幅猫牛式`, `坐姿90/90髋转换`, `蝴蝶式`,
  `仰卧4字臀部拉伸`, `半跪髋屈肌拉伸`, `站立体前屈`.

`常规臀桥` is an alias of `臀桥`, never a second exercise. The second-batch
supporting candidates are not seeded in this phase.

Seed files belong to this repository and are loaded explicitly by a seed
service. Runtime code must not inspect or import the old project.

### 2.2 Exercise identity and relationships

The following remain relational:

```text
exercise
exercise_alias
body_area
exercise_body_area
exercise_guidance_revision
```

Required constraints:

- canonical exercise names are unique;
- aliases are unique;
- a canonical name cannot also be another exercise's alias;
- one exercise cannot have duplicate body-area links;
- body-area links identify primary versus secondary areas;
- an exercise is deactivated rather than physically deleted once referenced;
- guidance revisions are append-only.

Name lookup normalizes only the matching key: trim surrounding whitespace and
apply Unicode normalization. The stored canonical name, alias text, guidance,
and user notes are not rewritten. Exact canonical-name matches take precedence
over alias matches.

### 2.3 Guidance JSON contract

`exercise_guidance_revision.guidance_json` stores one validated JSON object:

```json
{
  "purpose": "...",
  "starting_position": "...",
  "steps": [{"order": 1, "text": "..."}],
  "breathing": "...",
  "tempo_or_pacing": "...",
  "intended_sensations": ["..."],
  "common_compensations": ["..."],
  "stop_criteria": ["..."],
  "regressions": ["..."],
  "progressions": ["..."],
  "equipment": ["..."],
  "applicability": "...",
  "cautions": "...",
  "images": [{"path": null, "caption": "...", "status": "missing"}],
  "review": {
    "status": "draft",
    "reviewer_type": null,
    "review_source": null,
    "review_note": "",
    "reviewed_at": null,
    "user_approved_at": null
  }
}
```

The domain validator owns this contract. UI code does not manipulate arbitrary
JSON paths.

Required guidance fields are `purpose`, `starting_position`, `steps`,
`breathing`, `tempo_or_pacing`, `intended_sensations`,
`common_compensations`, `stop_criteria`, `regressions`, `progressions`,
`equipment`, `applicability`, `cautions`, and `images`.

Validation rules:

- required scalar fields must contain non-whitespace text;
- required list fields must be arrays with meaningful entries;
- `steps` must contain at least one item and have unique positive order values;
- `stop_criteria` must not be empty;
- `images` must explicitly represent `missing` when no image exists;
- image absence alone does not make textual guidance unusable;
- unknown fields may be preserved for forward compatibility but are not trusted
  as required facts;
- malformed JSON cannot become a guidance revision.

### 2.4 Guidance review and approval gate

The approved state machine is:

```text
draft -> pending_review -> approved -> active
                    \-> rejected
```

The external AI expert review is evidence entered through import or a manual
review form. The application does not perform the expert reasoning itself.

Rules:

- incomplete guidance may be stored and edited;
- incomplete guidance cannot be marked `approved` or `active`;
- review metadata must identify reviewer type/source and review time;
- a user must explicitly approve reviewed content;
- default seed values are not user approval;
- only `approved` guidance can become `active`;
- only an exercise with active, user-approved guidance can be selected for an
  active plan;
- rejecting a review leaves the prior active guidance revision unchanged;
- editing active guidance creates a new revision and does not overwrite the
  previous revision.

The exact operation is transactional:

```text
validate JSON
-> create immutable guidance revision
-> attach external review evidence
-> user explicitly approves
-> mark revision active
-> keep prior revision readable
```

If a review or approval write fails, no partial revision state is committed.

### 2.5 Phase 2 services and UI

Domain services:

```text
ExerciseService
GuidanceValidator
GuidanceReviewService
```

Repository operations:

```text
list/search/get exercise
resolve canonical name or alias
create exercise and alias
add guidance revision
get guidance revision history
approve/reject/activate guidance revision
activate/deactivate exercise
```

UI pages:

```text
exercise_library_page.py
exercise_detail_page.py
exercise_editor.py
guidance_review_page.py
```

The list shows name, aliases, primary areas, guidance completeness, review
status, and active state. The detail page shows all guidance fields and a clear
image-missing state. The review page shows the full content, review evidence,
and an explicit approval action.

## 3. Phase 3 Versioned Plans

### 3.1 Plan model

Plan identity and plan content remain separate:

```text
training_plan
  training_plan_revision
    training_plan_day
      training_plan_action
        training_plan_set
```

The initial revision statuses are:

```text
draft
active
superseded
```

Rules:

- a plan has at most one active revision;
- an active revision cannot be edited in place;
- editing an active revision clones it into a new draft;
- activating a new revision supersedes the old active revision in one
  transaction;
- every earlier revision remains readable;
- a revision referenced by a session cannot be deleted or rewritten.

### 3.2 Set and unit definition

A set is one ordered planned prescription row. `unit` states what the numeric
value measures; it is not an optional display suffix.

Examples:

```text
set 1: value 12, unit reps, per_side false
set 2: value 10, unit reps, per_side false
set 1: value 30, unit seconds, per_side true
set 1: value 5, unit breaths, per_side false
```

The supported units are `reps`, `seconds`, `minutes`, `breaths`, and `free`.
`per_side` is a separate Boolean fact and must not be encoded only in display
text.

The first implementation requires all sets of one action to use the same unit.
This supports equal and unequal doses without accepting confusing mixed-unit
actions. The schema keeps unit on every set because each set is independently
ordered and must later support historical snapshots.

Representations:

```text
2 x 15 reps       -> 15, 15 as two set rows
12 / 10 / 10 / 8  -> 12, 10, 10, 8 as four set rows
30 seconds/side   -> value 30, unit seconds, per_side true
5 breaths         -> value 5, unit breaths
```

`free` may omit a numeric value only when a non-empty explanatory note/display
text is provided. Numeric units require a non-negative numeric value. Set,
action, and day order values are positive and unique within their parent.

### 3.3 Activation prerequisites

Drafts may be incomplete. Activation requires:

- a non-empty plan name;
- at least one day;
- every day has an action;
- every action references an existing exercise;
- every action has at least one set;
- every set has a legal unit, value rule, and order;
- rest seconds are non-negative;
- action phase is controlled and valid;
- referenced exercise is active;
- referenced guidance revision is complete, externally reviewed, user-approved,
  and active;
- all sets within one action use the same unit;
- no duplicate day/action/set order exists.

An incomplete or unapproved guidance revision cannot be used to activate a
plan, even if the exercise identity itself is active.

### 3.4 Plan repositories and transactions

The plan repository exposes operations conceptually equivalent to:

```text
list_plans
get_plan/revision
create_plan
create_draft_revision
clone_revision
add/update day
add/update action
replace action sets
validate revision
activate revision
list revision history
```

`activate_revision` is one transaction:

```text
validate complete revision
-> verify approved active exercise guidance
-> supersede current active revision
-> mark new revision active
-> update training_plan.active_revision_id
COMMIT
```

Any failure rolls back all three state changes. No state may exist where the old
revision is superseded but the new revision is not active.

### 3.5 Structured revision diff

`domain/plans.py` computes a structured diff. The UI only renders it.

Diff categories:

- added, removed, or reordered actions;
- phase changes;
- rest changes;
- action note changes;
- added or removed sets;
- set value changes;
- unit changes;
- per-side changes;
- plan purpose changes.

Diff computation never mutates either revision and must preserve the original
notes verbatim.

### 3.6 Initial proposed plan

The proposal in `docs/initial-exercises-and-plan.md` is imported as:

```text
Plan: 臀腿与核心基础
Revision 1: draft
```

It must not become active automatically. The UI must show that the doses are a
proposal and require explicit confirmation before activation. The plan seed may
only reference exercises whose guidance has passed the Phase 2 approval gate.

### 3.7 Phase 3 UI

Add:

```text
plan_page.py
plan_detail_page.py
plan_editor.py
plan_revision_diff.py
```

The editor supports two explicit set-entry modes:

- equal sets: count, value, unit, and per-side;
- individual sets: one value/unit/per-side row per set.

Switching modes with unsaved changes requires confirmation. It must not silently
discard set values.

The activation preview shows the complete ordered plan, every set, guidance
review status, and the structured diff against the current active revision.
The final activation action is explicit and separate from saving a draft.

### 3.8 Implementation Status

Completed:

- structured dose value objects and activation validation;
- schema migration for free-dose explanatory notes;
- normalized plan repository create/read operations;
- draft revision creation and active revision cloning;
- atomic activation with supersession and active revision pointer updates;
- temporary-database persistence, clone, activation, and rejection tests.

Completed additionally:

- plan list and read-only nested detail UI connected to main navigation;
- UI test coverage for the Plans navigation entry.
- draft replacement persistence and plan editor with equal/individual set modes;
- draft save protection for active and superseded revisions.
- read-only activation preview with complete structured prescription rendering,
  a diff against the active revision, and a separate confirmed activation action;
- combined catalog-to-plan acceptance coverage, including immutable prior
  revisions after a changed draft is activated.

## 4. Database Migrations

The implemented schema changes remain append-only in `data/migrations.py`.
Later work must add a new transactional, idempotent migration rather than edit
an applied version. Tests use temporary databases, and no migration may inspect
or import an old-project database.

## 5. Implementation Order

1. Define guidance JSON types and validator.
2. Implement Phase 2 repository operations and migration adjustments.
3. Add seed files and seed idempotence tests.
4. Implement alias resolution, review/approval state, and guidance revision tests.
5. Implement catalog list/detail/editor/review UI.
6. Define plan dose value objects and activation validator.
7. Implement plan repository, draft cloning, activation transaction, and diff.
8. Import the initial proposal as a draft only.
9. Implement plan list/detail/editor/diff/activation UI.
10. Run the combined catalog-to-plan acceptance suite.

## 6. Acceptance Gates

Phase 2 passes when:

- all 14 approved seed exercises are present;
- `常规臀桥` resolves to `臀桥` without duplicate identity;
- all seed guidance is complete or explicitly marked incomplete;
- missing images never hide text guidance or stop criteria;
- external review and user approval are required for active guidance;
- catalog edits create revisions and do not alter historical snapshots;
- catalog repository and UI tests pass without SQL in UI modules.

Phase 3 passes when:

- plans support equal and unequal structured sets;
- reps, seconds, minutes, breaths, and free units follow their validation rules;
- per-side values are structured facts;
- active revisions cannot be edited in place;
- activation preserves all earlier revisions;
- unapproved or incomplete guidance blocks activation;
- activation is atomic and rollback-tested;
- structured diffs cover action, set, dose, unit, per-side, rest, phase, and note
  changes;
- the initial proposal remains draft until explicit user confirmation.

## 7. Required End-To-End Test

The combined test must prove this chain:

```text
create exercise
-> add alias
-> create guidance JSON
-> reject incomplete guidance activation
-> record external AI review
-> user approves guidance
-> create plan draft
-> add day/action/sets
-> reject plan activation for unapproved guidance
-> activate after all prerequisites pass
-> clone active revision
-> change dose
-> diff revisions
-> activate new revision
-> verify old revision remains unchanged
```
