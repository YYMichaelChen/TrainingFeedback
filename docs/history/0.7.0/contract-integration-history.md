# 0.7.0 Contract Integration History

Archived: 2026-09-21. The dated stage notes below preserve how A–G were delivered;
statements that desktop cutover is still future apply only to their original stage.
Current serialization/mapping: [contract annex](../../contracts/0.7.0-contracts.md).
Current support window: [development plan §13](../../development-plan.md#13-version-retention-and-development-data-policy).
Historical schema1/9 checks do not promise continuing upgrade support.

Status: 070-A baseline complete, 2026-09-17. This is the wire-format and migration annex to
[development-plan.md, Section 12](../../development-plan.md#12-070-development-contract-planned).
It freezes the next model for implementation; the 0.6.1 UI still uses plan v1.

## Identity And Content

- An exercise reference is `{source: bundled|custom, key: stable-key}`. Bundled
  keys remain those in the current seed. New custom IDs are generated once and
  persisted; migration allocates one ID per old row and journals that mapping.
- Content is referenced by `{id, version, sha256}`. The hash is SHA-256 of UTF-8
  JSON with sorted keys, compact separators, unescaped Unicode and finite numbers.
  Arrays and text retain their original order/bytes; do not trim or normalize text.
  The reference serializer is `domain/catalog.py:content_sha256`; numeric JSON
  representation is part of the envelope (`1` and `1.0` need not hash identically).
- The hashed envelope contains exercise reference, name, aliases, category,
  equipment, body areas, family classification, guidance without `review`, and
  image declarations with relative path, required flag and byte hash. Review,
  enablement and local database IDs are separate user state, not publisher content.
- `data/seed/families.py` maps all 36 stable keys to four families or standalone
  positions. It does not modify the existing seed or imply illustration/review
  readiness. Technique and aliases remain owned by the
  [content specification](../../initial-exercises-and-plan.md#10-070-catalog-content-plan).

The checked [source inventory](../../contracts/baseline/catalog-070-baseline.json) includes the
current source content versions, not invented 0.7.0 guidance or artwork. Hashes
are computed for this baseline; they were not present in historical schema-16
rows. The [v1 schema snapshot](../../contracts/baseline/plan-v1-baseline.schema.json) freezes the
previous import contract for migration fixtures; it is not a future import option.

## Plan V2 Wire Format

The normative structural schema is [plan-v2.schema.json](../../contracts/plan-v2.schema.json), with
a [synthetic format example](../../contracts/plan-v2.example.json). The root contains
`schema`, `schema_version`, original `rationale`, optional `source` IDs and `plan`.
All object fields are declared; unexpected approval/enablement/status fields fail
validation. Source IDs refer to the target root. Only version 2 is accepted by the
new-model v2 import path; no v1 conversion or mode selection is exposed.
`PLAN_IMPORT_SCHEMA_VERSION = 2` and `EVIDENCE_SCHEMA_VERSION = 2` are independent
constants in `domain/group_plans.py`; old desktop routing retires at G.

Days contain ordered `items`: `kind: action` or `kind: group`. Each item/member
has a stable `item_id`, unique throughout a revision and retained across clones.
New externally added items get new IDs; matching an existing ID must match its
lineage. Orders are positive and unique within a parent. Members have no phase:
the group supplies it. No nested group exists. Each action/member carries an
exercise reference, display name, exact content, family/variant/position metadata,
sets, original note and explicit rest fields. The resolver must verify all these
metadata against the referenced content; name/key or hash conflicts are errors.

One member uses one unit and one `per_side` convention across its sets. Doses and
rest are finite and non-negative; absent numeric free doses require a nonblank
explanation. No numeric default is a user fact. `rest_after_set_seconds` applies
only between that member's sets; the final set uses the next boundary instead.

Groups explicitly provide rounds, side sequence, first side, transition note,
member/side/round/exit rest. `same_side_then_switch` and `all_rounds_then_switch`
require all members per-side. `member_each_side` permits bilateral and unilateral
members; first side is required whenever any member is unilateral, otherwise null.
Standalone actions use first side likewise. Mixed/unknown starting positions
require a nonblank transition at activation; identical classes do not imply equal
support or safety. Draft imports do not approve that transition or activate a plan.
No-side prescriptions require zero side-switch rest; a single round requires zero
between-round rest. The three fixed order/rest examples are stored in
`tests/fixtures/070/group-execution-expectations.json` and checked against the pure
`ActionGroup` expansion. This expansion is a prescription preview, not saved work.

Boundary priority (never sum rests): another set → set rest; another side of the
same member/sequence → side rest; another member → member rest; next round → round
rest; group exit → exit rest. For all-rounds-then-switch, the final first-side round
uses side rest instead of round rest. Set/member terminal rest fields must be zero
when inapplicable. Examples are format fixtures, not doses or reviewed guidance.

JSON Schema covers local shape/types; cross-row uniqueness, units, side
compatibility and resolver checks are additionally enforced by domain validation.
Neither layer can establish real review or physical image readiness from JSON.
070-D now enforces the schema plus cross-row identities/orders, finite doses,
uniform member units/per-side flags, terminal rest rules and exact content
resolution. The schema ships as package data and matches the checked contract.
New-model plan-page import accepts only v2; old desktop routing retires at G.

## Eligibility And Removal Contract

Selection, enablement, activation and new starts share Section 12.4 eligibility:
complete text, valid required images and not removed. Review is independently
bound to exact content/image hashes, never inferred from file validation. Missing
or changed bytes invalidate effective readiness without erasing earlier events.

Removal appends requested/under_review/approved/applied or rejected/cancelled
events. Application must compare the approved content hash and current reference
impact in the write transaction. Restoration appends a new decision and rechecks
content/images; it does not restore enablement or plans. Historical snapshots and
unfinished sessions retain their original facts. See Sections 12.5–12.6 for rules.

## Schema-16 Conversion Mapping

| Existing fact | New-model destination / required preservation |
| --- | --- |
| Known bundled key, even renamed | Same bundled identity; local name/aliases/content become explicit overrides, not edits to the package. |
| Missing or unresolvable bundled key | Distinct custom ID persisted in the migration journal; preserve original ID/key and all text as provenance. No name inference or merging. |
| Selected guidance and all referenced revisions | Immutable content snapshots/overrides; retain exact stored JSON, revision numbers and original review fields. Compute new hashes without fabricating old hashes. |
| User images/review originals | Preserve bytes and file hashes before detaching paths; stage assets and publish with a recovery journal. Missing files remain explicitly missing. |
| Active/draft/superseded plans and per-set doses | Single items with old action identity mapping, status and all original prescriptions preserved. Guidance bound now is labelled `migration_time`, not original activation evidence. |
| Session actions/sets, results, notes and events | Preserve IDs and frozen names/areas/phases/rest/notes, actual zero vs unknown and existing guidance reference. Ungrouped work stays ungrouped; unknown side counts remain unknown. |
| Review snapshot NULL/false/true | Keep each distinct value; never substitute current review evidence. No historical image-readiness inference. |
| Retraction and note-correction audit | Preserve original before-images, timestamps and references; no rewriting embedded historical JSON. |
| Feedback and import/export records | Preserve IDs, original files, rationale/source/confirmation and unanswered NULLs. Existing v1 files remain evidence, not re-imported settings. |
| Enablement, config and locator | Retain meaningful settings/selected root; image-ineligible intent becomes provenance and cannot enable new starts. Unknown fields remain read-only provenance. |

Fixture generation is isolated and schema-16-only. Reopen before capturing a
logical-table and resource-hash baseline; keep an untouched copy. Later converters
must compare facts through the mapping, not raw database file hashes. Recovery
tests cover backup failure, staging, SQL commit, asset publication and cleanup,
with restarts on both sides of each boundary. No partial root may be exposed.

The full acceptance baseline must also be opened by the identified **actual
0.6.1 binary**, with its manifest retained, before it is used as packaged upgrade
evidence. Source-generated fixtures alone do not satisfy that independent gate.

## Reproduce The Baselines

Use PowerShell 7 and the repository interpreter (standard venv users substitute
`.venv\Scripts\python.exe`). The output directory must be new or empty:

```powershell
.venv\python.exe packaging/prepare_contract_baseline.py .tmp/070-contract-baseline
.venv\python.exe -m pytest tests/test_070_contracts.py -q --test-scope 070-contracts --basetemp .tmp/070-contract-tests
```

`tests/migration_070_fixtures.py:create_schema16_baseline` uses only an explicit
empty synthetic base; the test retains `original/data-root` and its closed logical
baseline under pytest's temporary directory. `schema16-preservation.json` contains
the original records/resource hashes and expected identity/snapshot mapping.
The helper pins the unchanged migration chain through schema 16 within the test;
it does not label the current development binary as an original 0.6.1 candidate.
Preserve those closed inputs before upgrading a separate copy.

070-B now consumes the reference/hash/classification contracts in the read-only
catalog, manifest, user overlays and retained assets. Schema examples
contain placeholder hashes and are not resolver-valid plans or physical image
validation. No actual review, activation, migration or packaged release is claimed.

## 070-B Storage Integration

- `data/catalog_builder.py` produces the checked-in program payload from owned
  source content; `packaging/build_catalog.py <empty-directory>` regenerates it.
  Use `--verify <directory>` for source or packaged manifest/content validation.
  Startup never builds resources or writes to the program directory.
- `CatalogRepository` uses package-relative paths, read-only immutable SQLite and
  exact file inventory/hash verification. No journals, user state or overlays are
  permitted in the resource payload. The 36-entry baseline remains image-missing.
- Schema 17 adds local stable references, immutable content snapshots and asset
  bindings, versioned custom/override rows and per-root selection/enablement
  storage. New references default to unselected/disabled; B exposes draft and
  retention operations, while C provides validated selection/enablement workflows.
- `LibraryContext` composes the catalog, user repository, resource store and
  `LibraryService`. Creating a new-model root leaves catalog content out of user
  tables. Switching first prepares the target, retaining the old context on
  failure. No locator or user-facing mode choice is added.
- Retained bytes are hash-addressed under `snapshot-assets/`; new custom source
  files are under `custom-exercise-images/`. Under one SQLite write lock, publish
  bytes before committing references. Failed/restarted operations remove only
  unreferenced assets; immutable committed content survives catalog replacement.
- Existing desktop routes remain unconverted until D–G integrate their workflow.
  They reject a new-model root rather than silently seeding it. The final 0.7.0
  cutover removes that old route; this staging boundary is not a compatibility
  setting. Schema-16 business facts are preserved by additive schema 17 tests.

## 070-C Eligibility And Review Integration

- `LibraryWorkflowService` is composed by `LibraryContext`; its `LibraryTarget`
  pins both namespaced exercise and content id/version/hash. Selection and
  enablement, including batches, validate the displayed target inside the writer
  transaction. Activation and new-session use cases in D/E must invoke
  `require_for_activation` / `require_for_new_session` inside their transactions.
  These return exact unreviewed names for disclosure; they never approve content.
- `data/library_images.py` reads validated managed bytes, checks hashes, decodes
  and verifies positive dimensions. The pure domain consumes `ImageCheck` values.
  Required missing/invalid images block use; missing optional images stay visible.
  A broken optional supplied image invalidates effective review until restored.
  Explicit placeholders cannot qualify; file validity is not anatomical review.
- Schema 18 adds immutable `library_review_event` rows. Approval binds a retained
  content row/hash and ordered image-index/hash list, actual external source/type/
  occurrence, confirmation time and original note/optional answer-file metadata.
  Withdrawal appends a new event with an expected prior event ID. Prior facts and
  attachments remain readable; selection and enablement are independent.
- `CatalogLibraryPage`, `CatalogEditor` and `CatalogReviewDialog` provide family
  browsing, starting-position filters, explicit versions, comparisons, copied
  custom content, local override editing and image association. The page is
  composed via `LibraryContext.create_library_page()`; it adds no user-selectable
  legacy mode. Desktop routing and existing-root conversion remain G work.
- Parent relationships must remain within a known family, without cycles or
  self-parenting. Names/aliases cannot collide with other exercises. Edits create
  a fresh unreviewed content identity and preserve original text and older facts.

070-D now consumes these shared eligibility/review APIs. Runtime plan v1 remains
the old desktop baseline until the final cutover; it is not a selectable new-model mode.

## 070-D Plan And Handoff Integration

- `GroupPlanService` validates v2 drafts, resolves exact namespaced content and
  checks item lineage across revisions. Same-exercise repeated instances have
  distinct item IDs. Published revisions clone into drafts; edits never rewrite
  an original imported answer or its rationale/source record.
- Schema 19 adds `group_plan`, revision/day/item/set tables, immutable activation
  pins and immutable import/export registrations. A group member's item row has
  its own identity and order; per-set rows retain value, unit, side flag, note and
  internal rest. Group/side/transition metadata remains attached to its item.
- Activation uses a preview token bound to revision edit state, current active
  revision, review events and live image eligibility. One write transaction
  revalidates, retains content/resources, writes every action pin, supersedes the
  prior revision and updates the active pointer. Failure rolls back all changes.
  Plan pins record activation-time review, never future execution review.
- `GroupPlanEditor` and action/group dialogs provide explicit add/remove/reorder/
  move controls. Removing a group's penultimate member requires confirmed
  dissolution; explicitly reduce to one round first so no repetition is silently
  lost. Other invalid prescriptions remain editable and cannot be saved.
- `GroupPlanHandoff.import_file` rejects v1, duplicate JSON keys, nonfinite values,
  unexpected fields and unresolved/conflicting content. It copies the original
  UTF-8 bytes to managed imports inside the save action and creates only a draft.
  The new plan page selects imported/cloned revisions explicitly.
- `GroupPlanHandoff.export` writes a managed directory containing `plan.json`,
  `evidence.json`, `evidence.md`, `plan-response.schema.json` and hash-deduplicated
  `assets/` with decoded image suffixes. Plan-scope evidence identifies application,
  catalog/schema versions, frozen prescriptions/content and activation review.
  JSON and Markdown retain the same complete facts. Missing historical resources
  are unavailable, not fabricated. Staging or registration failures remove this
  action's incomplete files. Existing original imports/exports remain untouched.
- D exports use `scope: plan_revision`; they do not claim actual session results.
  E supplies grouped execution occurrences, results, controller position and session
  evidence. G replaces the old desktop entry routing after conversion is complete.

## 070-E Execution And Evidence Integration

- Schema 20 adds a session snapshot and ordered immutable occurrences, each with
  day/item/member/round/side, complete prescription, content reference and retained
  content ID, body areas, boundary rest and separate activation/start review facts.
  Standalone unilateral items expand first-side then opposite-side occurrences.
  Original `per_side` prescriptions are retained; actual sets carry explicit
  `side: left|right|null` and never claim the unperformed side.
- Completed results use `prescription_confirmed` doses; partial/exceeded use
  `user_entered` actual sets. Zero remains zero; not-completed and unanswered work
  have no actual sets. A free actual dose may omit a number only with its own
  nonblank original explanation. These states imply no technique or body sensation.
- Every state-changing execution command checks a session version under one
  SQLite writer transaction. A round token binds session/version/position and
  exact unrecorded members. All-rounds-then-switch limits the batch to the current
  side/round; other sequences preview both sides when present. No command advances
  position after saving. Navigation persists position without recording work.
- Batch identity/membership is immutable. Retraction archives complete prior
  occurrence/result/actual/note facts before clearing only that batch, or one
  individual result. A batch member cannot be retracted as an unrelated individual.
  Paused/terminal sessions reject result edits; resume never rechecks live catalog
  eligibility. New starts do, using exact pinned content and explicit disclosure.
- Feedback uses performed main-area snapshots; unanswered choices stay null.
  Terminal result/feedback note corrections append old/new text with a stale-value
  check and never overwrite original result or feedback rows.
- Session exports use `scope: training_session` under evidence v2. They contain the
  frozen revision, complete session, batch/event/feedback facts, earlier session
  summaries, earlier revisions and portable images. The Markdown embeds the exact
  JSON alongside readable execution summaries. Export registration/files publish
  atomically through the D exporter. Plan-scope exports keep their original scope.
- Current v2 `source.session_id` refers to `group_session`; `source.export_id`
  uses the shared `group_plan_export` identity namespace, with session exports
  additionally bound through `group_session_export`. Old v1 source IDs remain in
  original provenance; G must preserve/remap those facts explicitly during conversion.
- `LibraryContext.create_session_page()` composes native start/resume/history,
  frozen guidance/images, evidence export and feedback. `create_training_page()`
  takes a `GroupSessionController`; save/cancel/pause/abort/finish stay reachable
  outside scrolling. Desktop entry replacement and old-root conversion remain G.

## 070-F Removal And Restoration Integration

- Schema 21 stores immutable `library_lifecycle_request` and
  `library_lifecycle_event` rows. One request represents the exact displayed batch;
  its original reason, targets/content context and impact are retained. Decisions
  append source, actual occurrence, explicit confirmation time, original note and
  their reviewed impact snapshot. No account/role system or external reviewer is inferred.
- `LibraryLifecycleService` binds previews to target source/key/content hash,
  current catalog/local versions/selection, root disposition, enablement and all
  affected references. Content context changes require a new request. Reference
  changes require refreshed review, including when a prior approval exists.
  Event IDs reject competing decisions; applying rechecks inside the writer transaction.
- The lifecycle is requested → under_review → approved → applied, with rejection
  and cancellation exits. An explicit approve-and-apply action shares one transaction.
  Application retains available content/resources, writes minimal tombstones and
  disables all targets atomically. Broken-image drafts can be removed without
  inventing assets. No plan, review, session, original export or variant is deleted.
- Impact covers draft/active/superseded plans, group members, all session states,
  review events, dependent variants and saved exports. Export references are read
  from their managed evidence files, including prior-context identities; unreadable
  files are conservatively reported as unknown. File hashes participate in staleness checks.
- `library_publisher_event` records verified catalog disposition and manifest
  identity at the local observation time. Withdrawal and missing known references
  block use independently of local tombstones. They do not claim a publisher
  decision occurrence. A local restoration cannot override them; repeated opening
  of unchanged content/disposition does not duplicate observations.
- `library_plan_invalidation` links previously activated pins to the first removal
  event. Restoring and enabling an action do not clear these facts: a newly
  confirmed plan revision is required for new training. Open/paused sessions and
  terminal exports continue to use their immutable content/assets and prescriptions.
- Restoration validates text and illustrations and writes a separate approved
  decision. Enablement stays off, review evidence is unchanged, and variant/parent
  links remain explicit. Missing-parent identity can be resolved from retained
  child relationships; no missing guidance or ancestry is fabricated.
- The catalog page opens `LibraryLifecyclePage`, with batch request preview,
  review/approve/apply/reject/cancel, audit history, restore and publisher records.
  `LibraryContext.create_removal_page()` exposes the same page for G integration.
  Full desktop routing, old-root conversion and independent packaged acceptance
  remain later gates.

## 070-G1: Internal upgrade recovery protocol

- `UpgradeRecovery.run(operation, convert, validate)` owns an exclusive root lease.
  The converter receives only the disposable work root and verified program catalog;
  it must close database handles on return. Validation is read-only. G2 provides the
  actual fact mapping and current-model validation; G3 supplies normal startup routing.
- Internal format `training_feedback.upgrade-recovery`, version 1, consists of a
  root journal and `backups/upgrade-v1-<id>/manifest.json` plus `snapshot/`. Snapshot
  inventory covers configuration, database and all non-internal files/directories.
  Old backups, lock/journal files and SQLite transient sidecars are excluded. Online
  backup materializes committed SQLite/WAL state; manifest SHA-256 is bound to the
  journal. No old backup recursion or user-selected destination is involved.
- `prepared` → `publishing` → `complete` is the success path. Interrupted prepared,
  publishing or restoring work restores the verified snapshot, records `rolled_back`,
  and may retry the conversion. Restore itself is repeatable after interruption.
  No normal database open accepts pending/malformed journals. A corrupt recovery
  snapshot blocks restoration before changing live files; it is never silently used.
- A complete operation does not repeat conversion, copying or confirmation. The
  recovery snapshot remains retained; only disposable work is cleaned. A normal
  whole-root backup may include this evidence, but the internal snapshot alone is
  not advertised as a complete-root backup.
- Database connections hold shared leases; upgrade/recovery holds an exclusive
  OS lease. Current-process and cross-process contention are rejected without stale
  lock-file deletion. The older packaged binary does not participate in these leases;
  G2/G3 integration and candidate acceptance must enforce closed older application
  handles during replacement and validate the real adjacent-upgrade boundary.

## 070-G2: Persisted conversion and current-model facts

- Schema 22 appends immutable `conversion_run`, `conversion_original`,
  `conversion_mapping`, `conversion_registration` and plan migration provenance.
  Original schema rows, including guidance JSON strings, correction/retraction
  before-images and unknown configuration keys, retain original text/IDs. Only known
  application/format settings remain live; unknown settings are read-only evidence.
- `convert_catalog_root(path)` operates only on the supplied TrainingFeedback root.
  It recovers G1 pending publication before inspecting/configuring a conversion.
  The converter works in G1's disposable root, runs the historical schema chain,
  maps facts in one SQLite transaction, validates and drops accounted-for old live
  tables. A read-only validator checks original hashes, destination plans/results/
  feedback/audits, stable IDs, content and resource bytes before and after publication.
  No locator change, directory discovery, old import mode or user confirmation is added.
- Known bundled keys keep the namespace/key even after a local rename. Missing keys
  become distinct deterministic custom UUIDs derived from the preserved source facts;
  restart/retry keeps the same mapping. Reference, plan/revision/day, session and
  occurrence IDs retain their externally meaningful source IDs. Child identities and
  original import/export registrations have explicit mappings; new export IDs start
  above the old export namespace. Original files are never rewritten or re-imported.
- Each stored guidance revision retains technique text and original review metadata.
  Local image bytes become hash-addressed snapshots; missing references stay missing,
  corrupt bytes remain retained but fail eligibility. Original files remain as evidence.
  Old review records have no exact image-hash approval and therefore cannot supply new
  image-specific approval. Prior selected/enablement intent survives as provenance;
  effective enablement requires currently eligible content.
- Old ungrouped plan actions stay single items. Selected guidance is pinned at
  `migration_time`, not retrospectively at activation. No selected guidance yields an
  explicit unknown binding, never a guessed latest draft. Old per-set values/units,
  notes, per-side flags and action rest survive; absent side-order/set-rest facts are
  NULL. Active/superseded status does not imply new confirmation or known activation time.
- `dose_scope=per_side_aggregate` is a current stored-fact type: one occurrence retains
  the old per-side prescription/result without inventing left/right order or counts.
  Actual sets carry nullable `per_side`; unknown, false and true remain distinct.
  New actual-entry UI requires an explicit scope choice; no left/right completion is
  inferred. Existing results without actual dose remain unknown even when completed.
  Unknown result timestamps/notes are nullable. Resume uses only current session tables.
- Session content is built from its recorded guidance revision, name/area/phase/rest/
  note/set snapshots. Later catalog metadata is not historical proof: missing metadata,
  pre-snapshot-schema defaults, review time and image readiness remain unknown.
  Historical-only retained content does not appear as a selectable library revision.
  Imported events retain raw before-images under explicit imported-event kinds;
  later retractions/corrections use the normal current append-only workflow.
- Strict external v2 imports cannot claim internal migration provenance. Editing an
  already-stored migration item validates against its stored identity/scope and keeps
  untouched unknown values. V2 evidence contains those complete internal snapshots;
  an exported `plan.json` containing migration provenance is evidence, not a valid v2
  response proposal. The separately supplied response schema remains the authority
  for newly authored external prescriptions.
- Eligible unchanged active plans may start immediately, while missing content blocks
  only new starts and is shown in normal plan details. Source schema1/9/16 fixtures,
  populated schema21→22, before-commit/publication failures, restart/idempotency,
  temporary backup/reopen and current-controller continuation are verified. Real
  packaged-binary adjacency and independent acceptance remain H gates; G3 desktop
  wiring is recorded below.

## 070-G3: Desktop wiring and retired-runtime removal

- Normal launch and data-root switching route through `convert_catalog_root`:
  `bootstrap.open_root`/`create_root`/`open_from_locator` convert an inspected
  schema-16 root before opening it, recover G1 pending journals first, and save
  the locator only after a successful open. Conversion or recovery failures abort
  the open with an actionable Chinese message naming the root and cause; no
  half-upgraded root is presented as usable. `DataRootSwitcher` converts a
  candidate root, builds the replacement window, commits the locator and swaps
  windows; same-path switches are no-ops and an open (non-paused) session blocks
  switching.
- `LibraryContext` is the only desktop context. The main window composes the
  group training, catalog library, group plan and settings pages; the settings
  page keeps catalog information, open-location, root switching and backup, and
  drops the retired export-all control.
- `ApplicationContext`, the old application services/repositories, the old
  handoff export/import module, startup catalog/plan seeding, the old UI pages
  and the old session controller are removed. No old-format runtime fallback,
  old-settings switch or dual-runtime branch remains; read-only conversion
  provenance and recovery artifacts are evidence, not selectable settings.
- Registration lookups normalize Windows-native separators when resolving
  recorded import/export paths, while the recorded path text stays verbatim.
- The synthetic schema-16 acceptance baseline is frozen as checked-in bytes
  under `docs/contracts/baseline/` (root copy, preservation facts, fixture
  metadata). `packaging/prepare_acceptance_data.py` copies and hash/integrity
  verifies those bytes and no longer imports retired runtime modules.
- Verified with the 070-G3 dev scope (29 unique cases): bootstrap create/open/
  recovery-error paths, root switching with conversion, main-window navigation
  composition and the frozen-fixture conversion regression. Real packaged-binary
  adjacency and independent Windows acceptance remain 070-H gates.
