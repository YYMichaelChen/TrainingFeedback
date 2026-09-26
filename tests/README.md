# Regression maintenance

The authoritative budget policy is development-plan.md §9.4. Test databases,
locators, synthetic images and fixtures always live in temporary directories.

Current 0.7.2 resident inventory is 175 parameter-expanded cases. The retained
application window is 0.7.0–0.7.2, all at schema22. Expired schema16 fixtures and
their positive conversion tests rotated out; current tests cover read-only refusal
of older roots, schema22 reopen, UI behavior and frozen history.

## Selecting and accounting

- `--test-tier dev` (default): at most 30 cases; explicit affected cases are
  preferred. Without a selector, use the small smoke profile.
- `--test-tier patch|minor`: nested baseline profiles plus release-specific
  cases selected by subsequent commands in the same scope, capped at 50/100.
- `--test-tier major`: the full resident suite, capped at 300.
- Names in `pyproject.toml` select all parameter combinations of that function.
  Paths/node IDs, `-k` and `-m` instead select exactly the requested cases.
- `--test-scope TASK-ID` is required for execution, not collection. The ledger
  in `.tmp/test-budgets/TASK-ID.json` records unique **reserved node IDs**, not a
  claim that they passed. A failed/interrupted run does not refund reservations.
  Reusing a node ID after a repair does not consume another slot.
- A scope lock prevents simultaneous commands from racing. After a crashed
  process, confirm that it exited before removing its stale `.lock`; keep the
  JSON ledger. Malformed ledgers and tier changes fail rather than reset counts.
- Default collection also checks the resident cap and stale profile names.
  `--test-tier major --collect-only -q` inventories everything without executing.

For a patch release, run the patch baseline under its release scope, then the
affected tests under the same scope and tier. Do not run the dev, patch, minor
and major profiles successively. Select a new scope only for a genuinely new
development step or release. Budget metadata is local developer state, not an
application database or a security boundary.

## Historical 0.7.0 Release Preparation — 2026-09-23

The resident inventory is 188 expanded cases. 070-H2-TESTS replaced the removed
minor-profile function with `test_out_of_window_root_refused_before_any_write` and
`test_oldest_retained_schema14_root_converts_unknown_facts`; default collection now
succeeds and selects 12 dev cases.

Actual final-source selection is minor 63 plus recovery/conversion 18, overlap 4,
for a 77/100 unique-case union. The 63-case profile and all 18 added cases passed
under the shared `--test-tier minor --test-scope release-0.7.0` ledger.

The contract inventory test now validates the frozen historical inventory and v1
schema directly, then checks today's catalog against current source, manifest,
payload bytes and SQLite content. The old missing-image generator and its executable
test dependency are retired; frozen hashes were not regenerated.

R1's frozen-input repair and R2's support-window implementation are complete.
Independent public acceptance, W4 and external content review are separate from the
local regression gate under development-plan §9.1. The detailed next steps and
budgets live in [the closeout plan](../docs/release-readiness-0.7.0.md).

## September 2026 consolidation

The 479-case suite was reviewed down to at most 300 expanded cases. This is an
actual reduction in resident test code and input combinations. No legacy file
is globally excluded. ApplicationContext coverage retired with the old runtime
in 070-G3; LibraryContext is now the only desktop context under test.

| Removed/reduced overlap | Retained representative coverage |
| --- | --- |
| Navigation, page classes and labels in separate windows | `test_main_window_navigation_and_chinese_labels` |
| Normal domain result/state transitions repeated in service tests | `test_training_state.py`, `test_070_group_execution.py` outcomes/finish/pause |
| Repeated seed lists and historical per-catalog expansion matrices | `test_070_contracts.py` catalog inventory, `test_070_catalog_storage.py` replacement and retained content |
| Multiple basic clone/activation cases | Catalog-to-plan revision chain, import activation preservation, failed activation/draft replacement |
| Enum-value and schema errors repeated at several layers | Representative schema/service failures, exact three side sequences, zero/unknown/free-dose behavior |
| Basic online backup and root round-trip checks | Whole-root backup/reopen, execution/retraction recovery, lifecycle decision isolation |
| Small UI-only review assertions | Actual checked-row submission, invalid occurrence repair/reuse, source/target selection and explicit confirmation |
| Standalone display/scroll checks | Frozen session/history/Markdown display, actual-entry UI and themed small-window controls |
| Trivial root/config/locator variants | Unknown/occupied root, application identity, unreadable metadata, future versions, corrupt DB and switch rollback |

This trades exhaustive minor input/label permutations for workflow and
data-preservation coverage; it does not claim unchanged line/branch coverage.
Keep distinct transactional failure points and history/migration tests. A
passing larger scenario can replace its trivial subchecks; unrelated failures
must not be bundled solely to reduce the displayed case count.

## 070-G1 coverage exchange

Eight recovery cases replace eight lower-risk cases, keeping the resident count at
300. Three independently parameterized cases interrupt staging, DB publication and
cleanup; separate cases cover failed snapshot copy, corrupt snapshot, process locks
free-space preflight and committed WAL preservation. The existing schema-chain case runs through
the recovery boundary and verifies the original schema-16 snapshot and idempotency.

- Occupied-root rejection remains in the bootstrap retry scenario.
- Metadata error translation retains the malformed-metadata case; missing-field
  message permutations are no longer individually covered.
- Manifest path escaping remains; the three lower-level path-literal permutations
  were removed. Managed image containment also retains workflow coverage.
- Old library row labels and first-launch suggestion text are no longer individually
  checked; state-axis behavior, real selection dialogs and navigation remain covered.
- Old unique-action reorder display is reduced; same-position identity replacement
  and new-model member reordering/diff remain covered.

This is an explicit coverage tradeoff for upgrade data preservation, not an assertion
that UI-label or path-literal coverage is unchanged.

## 070-G2 coverage exchange

Eight expanded conversion cases replace eight lower-risk/overlapping cases; the
schema16 contract fixture additionally checks actual conversion, all archived facts,
resource bytes and evidence output. Separate cases cover pause/aggregate continuation,
SQL/publication failures, schema1/9 chains, migrated-plan editing/new starts, changed
destination validation, and nonempty schema21 result/feedback migration.

Removed short cases: old reviewed=true snapshot (covered in the full migration
fixture), empty-root migration idempotency (conversion/recovery reopen), preparation
phase area exclusion (performed-primary feedback cases), empty old custom form, old
long-title layout, catalog builder invalid-destination cleanup, future marker variant
(future config/schema remain), and acceptance-fixture occupied-directory rejection
(production bootstrap occupied-directory coverage remains). The last five reduce
detail/tooling coverage; they are a deliberate tradeoff for data-conversion risks.
No collection exclusions/skips or independent-scenario loops were added.

## 070-G3 coverage exchange

The retired-runtime suite (20 files exercising ApplicationContext, the old
services/repositories, handoff, seeding and old UI pages) is removed with the old
desktop runtime. At G3 completion on 2026-09-20, the resident suite collected
184 expanded cases, below the 300 cap. G3 cases cover bootstrap create/open/recovery-error routing, data-root
switching through conversion, and main-window navigation composition on
LibraryContext.

The schema-16 acceptance fixture is no longer generated by test code: it is frozen
as checked-in baseline bytes under `docs/contracts/baseline/` (`schema16-root/` plus
preservation/fixture metadata) and materialized by `tests/migration_070_fixtures.py`.
`test_acceptance_fixtures.py` verifies the frozen root's preserved facts and that
conversion registers every archived import/export file as available, including
Windows-native separator paths, instead of regenerating content with the retired
generator. Stale `pyproject.toml` profile entries pointing at removed test nodes
were replaced with equivalent current-model cases in the same risk areas.

## Historical Version-window Follow-up — Completed 2026-09-21

The supported window is 0.7.0/schema22, 0.6.1/schema16 and 0.6.0/schema14;
same-version commits do not add slots. R2 implemented pre-write lower-bound refusal,
replaced schema1/9 positive-upgrade scenarios with unchanged rejection including
schema13, and added the oldest-retained schema14 conversion case. Its dev scope
passed 27/27; candidate-specific release regression is still pending.

R1 separately tracked the frozen schema16 DB and protected evidence from Git newline
filters, with clone/ZIP byte comparisons passing 14/14. Keep supported fixture and
internal migration dependencies, future-root rejection and fresh initialization.
The historical G1–G3 coverage exchanges above describe their original dates;
the current resident inventory and known selection defect are recorded above.
Never delete the synthetic DB as generated user data or clear active budget ledgers.

Completed test-delivery notes belong to their application version and rotate with
the document window. The current release selection/union and evidence gaps are in
[the release plan](../docs/release-readiness-0.7.0.md#3-verification-plan).
