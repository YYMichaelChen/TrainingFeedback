# 0.7.0 Completed Development Deliveries

Archived from the active development plan on 2026-09-20. Source delivery is not
formal release acceptance. Current product rules and open tasks live in the
[development plan](../../development-plan.md); the
[release review](../../release-readiness-0.7.0.md) owns the closeout sequence.
Detailed original stage notes are in [contract integration history](contract-integration-history.md).

Application baseline: **0.7.0 / schema 22**. Schemas 17–22 were assigned during
this development cycle before the one-schema-change/one-version-bump policy.
Do not retroactively renumber them or use this exception for new schema work.

## Completed work sequence

| Work | Delivered responsibility | Verification emphasis |
| --- | --- | --- |
| 070-A | Identity/ownership, v2 shape, group/side/rest, image/removal and migration mappings for all 36 actions. | Reviewed structural examples and synthetic preservation fixtures. |
| 070-B | Read-only program catalog/manifest, user overlays, immutable snapshots/resources. | Reproducibility, package-relative reads, rollback, root isolation and no bundled seed copy. |
| 070-C | Families, variants, image gate and exact-version review. | Missing/corrupt/escaping/replaced images, stale targets, review independence and atomic batches. |
| 070-D | Group planning, activation pins and handoff v2. | Invalid-input retention, explicit confirmation, side/rest expansion, original imports and portable assets. |
| 070-E | Occurrence execution, feedback/history, batching and retractions. | Zero/unknown, asymmetric sides, stale/second writers, restart, terminal guards and export agreement. |
| 070-F | Reviewed removal, publisher withdrawal and restoration. | Changed targets/impacts, rollback, new-start blocking and frozen unfinished/history retention. |
| 070-G1/G2/G3 | Recovery, persisted conversion, normal desktop routing and old-runtime retirement. | Original facts/resources, journal boundaries, deterministic retry and supported UI continuation. |

## 070-A — Contracts (2026-09-17)

The [contract annex](../../contracts/0.7.0-contracts.md) supplies v2 schema/examples,
the frozen v1 contract, all 36 key/classification mappings, group/side/rest
expectations and schema-16 preservation fixtures. Pure checks cover identity,
hashing and ordering. The source-generated fixture is not an actual 0.6.1 binary
baseline; that identified-binary check remains a packaged acceptance requirement.

## 070-B — Catalog/storage (2026-09-17)

The 36-entry catalog and manifest declare missing images. Package-relative
resolution validates exact inventory/content hashes; user references, custom/
override drafts and retained bytes are transactional. `LibraryContext` creates
an empty user store without copying bundled content. Schema 17 was additive.
Backup/reopen, resource publication failure and root isolation were covered;
wheel and PyInstaller collection included the verified catalog. At this stage
the old desktop route remained until G; that staging restriction is now retired.

## 070-C — Eligibility/review (2026-09-17)

`LibraryWorkflowService` applies the same rule at selection, enablement, activation
and start boundaries. Managed paths, containment, hashes, decoding, dimensions
and placeholders are checked. Schema 18 appends review/withdrawal events bound to
content and image hashes, preserving original answers. Invalid images invalidate
effective review without rewriting earlier facts or saved intent. Native library
UI covers families/positions, variants, selected revisions, comparison, copy/
override, images and explicit review. Missing-image catalog drafts stay readable.

## 070-D — Plans and v2 handoff (2026-09-17)

The plan page supports days, single/group items, member reorder/move, rounds,
side order, dose/rest and explicit group dissolution. Invalid input is retained;
cancel writes nothing. Schema 19 normalizes prescriptions and immutable pins with
content/assets and activation-time review. Preview changes reject stale approval;
activation transactionally pins, supersedes and updates the active pointer.
V2 imports validate identity, classification, lineage, units/order and side/rest
semantics; only drafts and original bytes are saved. Plan exports include JSON,
Markdown, response schema and deduplicated portable images, with unavailable
historical resources explicit. Session-scope evidence followed in E.

## 070-E — Execution/evidence (2026-09-20)

Schema 20 stores full session prescriptions, ordered member/round/side occurrences,
actual sets, batch identity, controller position and append-only feedback/retraction/
note-correction facts. Standalone unilateral work also expands to explicit sides.
Start rechecks pins and discloses unreviewed content; start review is separate
from activation review. `GroupSessionController` persists navigation and does not
advance after saving. Round previews target only unrecorded members, both sides
where applicable, or the displayed side for all-rounds-then-switch. Stale/repeated
writes fail. Retraction resets only recorded batch membership. Finish requires
every result; abort leaves unanswered work unknown. Feedback uses performed main
areas without defaults. History/export retain original notes, results, review,
events, prior-plan context and images. Controls stay outside scrolling.

Historical source result: 445 tests passed before suite consolidation. Isolated
payload/catalog checks and a five-second empty-profile offscreen startup were
recorded in `.tmp/releases/0.7.0/070-e-package/verification.json` (payload retired
2026-09-21, evidence preserved); themed synthetic renders are
in `.tmp/070-e-visual`. This is not current release regression or desktop acceptance.

## 070-F — Lifecycle (2026-09-20)

Schema 21 adds immutable requests/decisions, root-local tombstones, publisher
observations and activation-pin invalidations. Exact content and reference impact
are previewed and rechecked transactionally; batches roll back as a unit. Impact
covers plans, groups, unfinished/terminal sessions, reviews, variants and exports;
unreadable exports remain unknown. Removal disables new use without deleting
evidence or dependent variants. Publisher withdrawal/missing keys independently
block new use; local observations do not invent publisher times. Missing parents
retain identity. Restoration validates current content/images but neither enables
the action nor clears old plan invalidations; a newly confirmed revision is needed.
Frozen work/history remain usable. Native request/review/history UI preserves input.

Historical source result: 479 tests (34 F additions) passed before consolidation.
Payload evidence is in `.tmp/releases/0.7.0/070-f-package/verification.json`
(payload retired 2026-09-21, evidence preserved); synthetic request/
library renders and 800×600 / 1040×780 bounds are in `.tmp/070-f-visual`.
Offscreen startup created no locator/database before confirmation. These local
checks did not replace an installed personal candidate or close independent acceptance.

## 070-G — Recovery, conversion and desktop cutover (2026-09-20)

### G1

`inspect_existing` validates metadata/schema/integrity/FKs without migration.
`UpgradeRecovery` verifies catalog and a versioned internal snapshot using online
SQLite backup and resource/config hashes. Existing backups are excluded, unknown
files retained and linked resources rejected. Conversion runs in a disposable root;
validation precedes publication. Shared OS-held database leases exclude the exclusive
upgrade lease and release on process exit. Pending journal phases block normal open.
Publication/cleanup failure restores the verified complete root before retry.
Recovery snapshots are retained evidence, not ordinary complete-root backups.

### G2

Schema 22 and `convert_catalog_root` implement deterministic fact conversion.
Original rows/configuration, identity mappings, registrations and managed bytes
remain immutable evidence; old live tables retire after mapping and validation.
Known bundled keys keep identity; unresolved keys become distinct custom IDs.
Guidance, selected overrides and attachments survive without fabricated image
approval. Plans preserve status/dose with migration-time pins. Sessions use recorded
snapshots, retain NULL/false/true review and zero/unknown actuals and verbatim audits.
`per_side_aggregate` preserves one old result as one occurrence without inventing
left/right work. Paused sessions resume/retract/finish in current services/UI.
Unchanged eligible plans need no new activation; missing content blocks new starts.
Destination facts, source archives and resource hashes are validated.

Earlier schema 1/9 fixtures and populated schema21 → 22 were historical test
coverage. The new three-application-version policy supersedes unlimited earlier
entry support; removing those entry paths and replacing old positive fixtures is
070-R2, still pending. Unknown historical facts must continue to remain unknown.

### G3

Normal startup and data-root switching run conversion and pending recovery, with
actionable Chinese errors. Locator saves only after successful open. `LibraryContext`
is the only desktop context, composing group sessions, library, plans and settings.
`ApplicationContext`, old services/repositories, v1 runtime handoff, startup seeding,
old pages/controllers and dual-runtime fallbacks are removed. Windows-native path
separators resolve for original registrations without modifying recorded strings.
The schema-16 fixture was frozen from the pre-retirement working-tree runtime;
helpers copy/verify it instead of depending on deleted modules. The review later
found the DB ignored by Git and newline protection absent: 070-R1 must fix those
delivery gaps before calling the baseline reproducible from a clean checkout.

G3's 29 unique dev-scope tests passed; resident collection was reduced to 184,
and Ruff passed. No complete current release regression is inferred from it.

## 070-H — Completed local preparation only (2026-09-20)

Built directory candidate 0.7.0, 257 files, dirty source based on `072c931`, catalog
070-baseline-1 with 36 entries and zero illustrations. Manifest hashes match;
payload includes v2 contract and sqlite3.dll. Offscreen packaged conversion of a
Chinese/space-path schema16 copy reached schema22, one conversion, all three
import/export registrations available, clean integrity/FKs and retained recovery
snapshot. Restart stayed idempotent; empty-profile startup wrote nothing. Seven
local checks passed. Evidence: `.tmp/070-h-package/`; complete candidate: `dist/`.

No 0.7.0 installer or independent scenario was executed. The claimed missing Inno
Setup was corrected: its compiler exists in the current user's standard directory.
Actual artwork, content review, supported actual-binary upgrades, installer and
independent desktop evidence remain open. A version bump is not release acceptance.
