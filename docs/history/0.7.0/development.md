# 0.7.0 Completed Development Deliveries

Archived from the active development plan on 2026-09-20. Source delivery is not
formal release acceptance. Current product rules and open tasks live in the
[development plan](../../development-plan.md); the
[release review](release-readiness.md) owns the dated closeout sequence.
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
070-R2 (pending at this milestone; completed on 2026-09-21, recorded below).
Unknown historical facts must continue to remain unknown.

### G3

Normal startup and data-root switching run conversion and pending recovery, with
actionable Chinese errors. Locator saves only after successful open. `LibraryContext`
is the only desktop context, composing group sessions, library, plans and settings.
`ApplicationContext`, old services/repositories, v1 runtime handoff, startup seeding,
old pages/controllers and dual-runtime fallbacks are removed. Windows-native path
separators resolve for original registrations without modifying recorded strings.
The schema-16 fixture was frozen from the pre-retirement working-tree runtime;
helpers copy/verify it instead of depending on deleted modules. The review later
found the DB ignored by Git and newline protection absent. Those dated delivery
gaps were resolved by R1 on 2026-09-21, recorded below.

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
At that 2026-09-20 milestone, actual artwork, content review, supported actual-binary
upgrades, installer and independent desktop evidence remained open. Subsequent
source delivery and the 2026-09-23 gate decision are recorded below; they do not
alter this old binary's evidence.

## Release Review Snapshot — 2026-09-20

The review was consolidated on 2026-09-21. Source for that candidate was dirty
`072c931` / tag `v0.6.0`; the then-observed status was 39 modified, 41 deleted,
77 untracked, nothing staged. These are historical counts, not the current tree.

All 257 files in `dist/TrainingFeedback/` matched the adjacent manifest by path,
count, size and SHA-256. Exact hashes remain with the candidate. The installer
inventory contained only 0.6.1 Setup and its matching manifest, whose original
hash was verified. A complete candidate requires both directory and manifest;
`.tmp/070-h-package/` alone holds supporting evidence, not the entire payload.

At this review, Ruff for src/tests/packaging, diff whitespace checks and AST parsing
of 95 Python files passed. Resident inventory was 184; minor selection 61 plus
recovery/conversion 16 with overlap 2 gave proposed union 75/100. These were selection
counts, not passing release regression. Later changes supersede the counts.

No independent 070-01–070-12 scenario had run. The compiler existed at
`C:\Users\41315\AppData\Local\Programs\Inno Setup 6\ISCC.exe`; the earlier
“Inno Setup unavailable” diagnosis was incorrect. Compilation was still pending.

## R1 And R2 Completed — 2026-09-21

- R1 commit `2bbd179`: track the synthetic schema16 DB and protect the entire
  frozen baseline from newline conversion with path-specific Git attributes.
  Fourteen files survived both clean clone and ZIP archive byte-for-byte.
  Focused recovery/conversion tests passed 16/16 under dev scope 070-R1.
  Windows tar extraction had a Chinese-path tooling limitation; ZIP was used.
- R2 commit `a274b70`: enforce the application/schema window 0.7.0/22, 0.6.1/16,
  0.6.0/14; refuse expired roots before writes with reinstall/new-directory guidance.
  Fresh initialization and retained upgrade dependencies remain available.
  Rejection cases cover schema1/9/13, and schema14 has positive conversion coverage.
  Dev scope 070-R2 passed 27/27. The then-existing package was not rebuilt.
- R1's synthetic fixture provenance remains the prior working-tree runtime,
  not an actual preserved old packaged executable. Later public acceptance must
  establish old-binary evidence separately.

The local Planscope route is `.planning/archive/v0.7.0/SUMMARY.md`.
Detailed earlier task records remain under `.planning/archive/0.7.0/`.
Complete current source identity and candidate-level regression remain later tasks.

## Workspace Cleanup Completed 2026-09-21

The review estimates before cleanup were: pytest roots ~3.44 GiB, planning scratch
~216 MiB, build ~11 MiB, 070-b–f intermediate payloads ~0.60 GiB and the two expired
September12 delivery trees ~1.74 GiB; `.tmp` was estimated ~5.85 GiB and the verified
toolchain `.venv` ~0.82 GiB was to be retained. These are dated estimates.

Executed inventory recorded `.tmp` shrinking from 5.90 GiB to ~4 MiB:
136 pytest roots 3,571 MiB; development-updates-20260912 1,324 MiB;
release-readiness-20260912 456 MiB; 070-b–f payloads ~619 MiB; and 27 stale loose
scripts/logs. Planning records were trimmed by 50 pre-0.6.0 entries.
The two cleanup-task summaries reported ~6.3 GiB total recovery across their scopes.

Preserved 070-e/f verification files moved to
`.tmp/releases/0.7.0/070-e-package/` and `070-f-package/`.
Kept `test-budgets/`, `070-h-package/`, 070-e/f visual evidence,
`catalog-070-b-regenerated/`, `three-exercises-20260915/`, `releases/`,
the verified environment, dist and all in-window records.
User roots, original answers/exports and real backups were not cleanup targets.
The subsequent tracked history layout was committed as `cafe5b1`.

These removals are completed history, not a current deletion queue. Later builds
and tests may increase local disk usage again.

## Guidance And Illustrations Delivered — 2026-09-22

The user confirmed video-informed definitions for entries 29/31/34/35. Guidance
and the authoritative content document were synchronized with new content versions.
All 36 owned source PNGs were explicitly mapped, with the sixth duplicate extension
corrected. Image integration advanced each content version once; final catalog
`070-illustrated-1` contains 36 entries and 36 required 1254×1254 PNGs.
Manifest hashes cover SQLite and all images. Current versions span v2–v5;
entry 29 is v4, entries 31/34/35 are v3. Both remaining bridge targets are v3.

Qt decoding/dimensions/reference/hash checks passed 36/36. The catalog reproducibility
test passed 1/1 under dev scope `GUIDANCE-SYNC-20260922`; target Ruff and whitespace
checks passed. Deterministic SQLite bytes require the pinned project runtime.
The user chose direct image association without another per-image content review.
No external expert review, plan approval or training facts were created.

The old `070-baseline-1` evidence was retained unchanged. No new program/installer
was built. Local summary:
`.planning/archive/0.7.0/2026-09-22-guidance-and-illustrations-summary.md`.

## Local Release Policy 2026-09-23

The user explicitly limited local-release blockers to four tasks: remaining content,
test repair/final regression, complete reproducible source, and new package/local
installed verification. Independent Windows H3/8-B2 is deferred until the user
explicitly requests public release. External content review and W4 remain separate
unfinished follow-ups, not local blockers; deferred work is not passed work.

Read-only planning found 188 resident cases, a stale minor-profile function and an
old missing-image generator invoked by the contract test. Replacing the stale
function with existing rejection/schema14 cases yields estimated minor 63 plus 18
recovery/conversion cases with 4 overlaps: 77/100. This is selection analysis,
not a new passing regression result. Current source remains `070-illustrated-1`;
target `070-illustrated-2`, tests, source freeze and installation are pending.

The documentation-only follow-up updates current plans/manuals and archives dated
status. It does not modify product code, configuration, databases, images or
packaging scripts, run product tests/builds, or publish/commit the application.

## 070-H1-CONTENT Completed — 2026-09-23

The regular bridge gained the `基础臀桥` alias and an explicit lift, three-second
top hold and controlled lowering cycle. `蛙式臀桥` became an alias of the existing
butterfly bridge identity. Only those two entries advanced from v3 to v4; stable
keys/content IDs, the other 34 entries, all 36 image bytes, schema22 and v2 wire
contracts stayed unchanged. The current source catalog is `070-illustrated-2`.

The catalog was built and verified first in a new empty staging directory, then
copied into the source tree. SQLite and manifest SHA-256 values are
`a551721131cd1b78050049b664bd943d5db044dbb9097ebd233df4dc904df3eb`
and `7de2db1d617e3c6243294079680886bf21ff3e6a31a3d971d7104ea597107489`.
The frozen baseline remained byte-identical. Dev scope `070-H1-CONTENT` used
3/30 unique cases and passed catalog reproducibility/image integrity, alias search
identity, and retained local-content behavior. No review, activation, personal
data transition or training fact was created. H2 tests/source/package work remains.

## 070-H2-TESTS Completed — 2026-09-23

The minor profile's removed schema-chain node was replaced by the three expanded
out-of-window refusal cases and the oldest retained schema14 conversion case. The
historical catalog inventory test now freezes its inventory and v1 schema bytes
directly while validating current source, manifest, payload bytes and SQLite content
separately. `packaging/prepare_contract_baseline.py` and its executable test
dependency were retired; the dated historical command and every frozen fixture were
preserved.

Default collection succeeded with 188 resident cases and a 12-case dev selection.
Dev scope `070-H2-TESTS` passed 5/30 unique affected cases. Final-source minor
regression used the shared `release-0.7.0` ledger: the 63-case profile and 18
conversion/recovery cases overlapped by 4, producing 77/100 unique cases; both runs
passed. Target Ruff passed, and frozen inventory/schema16 hashes stayed unchanged.
H2 source identity and packaging remain; public H3, external review, W4 and the
personal-data transition were not performed.

## 070-H2-SOURCE Completed — 2026-09-24

Reviewed and committed the complete 0.7.0 candidate: new runtime layers, v2 contracts,
36 seed and 36 payload illustrations, reproducible catalog, retained fixtures,
packaging inputs, documentation and intentional G3 deletions. The commit contains
218 tracked files; its post-commit worktree was clean and excluded planning files,
budget ledgers, `dist/`, `.tmp/`, local acceptance roots and user data.

Before any later build can replace `dist/`, the complete 2026-09-20 directory
candidate, adjacent manifest and 41 associated rehearsal files were copied to
`.tmp/releases/0.7.0/20260920-142327-072c931-dirty/`. All 257 manifest payload paths,
sizes and hashes matched, and the copied evidence had zero differences. The old
manifest remains explicitly bound to dirty source revision `072c931`; it is not
current release evidence.

A clean Git ZIP of the complete source identity contained the same 218 files. From
the extracted archive, all 67 package modules imported, all 14 frozen baseline files
remained unchanged, 36 seed/payload image pairs were byte-identical 1254×1254 PNGs,
and rebuilding the catalog reproduced all 38 files byte-for-byte. Ruff, compileall,
PowerShell parsing, relative-link, layering and diff checks passed. No source defect
was found after the 77/100 minor regression, so no additional release-budget cases
ran. Packaging and local installed checks remain; public H3, external review, W4 and
the personal-data transition were not performed.

## 070-H2-PACKAGE Completed — 2026-09-24

Built the final 0.7.0 directory payload and Setup from clean source revision
`736223e8b5258a914b106f04da90efd98ab215f7`. An earlier rebuilt candidate exposed a
real installed startup failure: PyInstaller had collected incompatible ICU and other
DLLs from a Codex Poppler runtime. The final spec rejects external binary provenance,
uses interpreter-owned alternatives where required and leaves Qt to use compatible
Windows system ICU. Isolated Qt Core/Gui/Widgets loading and the real installed UI passed.

The final manifest contains 293 files and matches the installed program path-for-path,
size-for-size and hash-for-hash; only the two Inno uninstaller files are additional.
The payload includes all 36 illustrations, catalog `070-illustrated-2`, schema22/v2
resources, ffi and sqlite DLLs, with no user database or locator. Payload manifest,
EXE and Setup SHA-256 values are `e72dfdb7...9aa9`, `dc7f24dd...e7e` and
`4fdf7f83...e889`. EXE and Setup are unsigned, which is disclosed for local release.

Installed LOCAL-01—06 passed through actual UI interaction with isolated profiles and
the synthetic Chinese/space root `中文 空格 根 070`. The alias checks resolved
`基础臀桥` and `蛙式臀桥` to the existing v4 identities. A synthetic two-member group
session stored a user-entered partial result of 4 reps, paused at member 2, restarted,
and resumed at the exact position with member 2 still unrecorded rather than zero;
frozen guidance/image and the unreviewed status remained intact. Evidence is indexed
under `.tmp/releases/0.7.0/20260924-010017-736223e/LOCAL-ACCEPTANCE.md`.

The local-release gate is therefore satisfied. Public H3/8-B2, actual old-binary
installed upgrades, signing/scaling, external content review, W4 and the personal-data
transition remain deferred or unfinished and were not marked passed.
