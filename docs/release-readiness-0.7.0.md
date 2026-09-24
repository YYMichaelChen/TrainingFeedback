# 0.7.0 Local Release Closeout Plan

Updated: 2026-09-24. **070-H1-CONTENT, 070-H2-TESTS, 070-H2-SOURCE and
070-H2-PACKAGE are complete; the local-release gate is satisfied.** Product authority is [development-plan.md](development-plan.md),
especially Sections 9–10 and 12–13. This document owns execution details.

The user's 2026-09-23 decision makes content closeout, tests, source provenance and
local packaged checks the local-release gates. Independent Windows acceptance
070-H3/8-B2 is deferred until an explicit public-release request. External content
review and W4 are separate unfinished follow-ups, not local-release blockers.
Deferred work is not passed work; local release creates no personal approval,
plan activation or personal-data transition.

## 1. Observed Baseline

These observations identify current source separately from existing binaries.
The detailed old review, test counts and completed cleanup are in
[0.7.0 delivery history](history/0.7.0/development.md).

| Area | State as of 2026-09-24 |
| --- | --- |
| Application / schema / contracts | Working source 0.7.0 / schema22; plan and evidence v2. No schema change is planned. |
| Current candidate source identity | Clean `b88feba66cdd60891cc169568187420183590913`; complete 218-file Git ZIP SHA-256 `39ae52ba...0c5a5`, including the corrected catalog/image. |
| Completed R1 | `2bbd179`, 2026-09-21: frozen synthetic DB tracked, byte-preserving Git attributes, 14/14 files verified through clone and ZIP archive. |
| Completed R2 | `a274b70`, 2026-09-21: three-version support and pre-write refusal below schema14; focused dev verification 27/27. |
| Current source catalog | `070-illustrated-3`: 36 entries, 36 required 1254×1254 PNGs, content and file hashes. One image caption was corrected 2026-09-24; externally unreviewed. |
| Content closeout at 070-H1 | Both bridge entries reached v4, with the three-second hold and agreed aliases. At that task's completion the other 34 entries and all image bytes were unchanged. |
| Current directory candidate | 2026-09-24 293-file build from clean `b88feba`; payload manifest `cedabf4c...91cf`, EXE `d203a9de...391f`, catalog `070-illustrated-3`. |
| Current installer | 0.7.0 Setup `d19eddce...279d`, built with Inno Setup 6.7.3; Setup and EXE are unsigned, as disclosed for local release. |
| Current installed checks | The corrected candidate passed affected LOCAL-01, 02, 03 and 05 with an isolated synthetic root and actual UI. LOCAL-04/06 were not repeated because bridge and session code/content did not change; their complete results belong to the prior `736223e` candidate. |
| Previous complete candidate | `20260924-010017-736223e`, catalog `070-illustrated-2`, Setup `4fdf7f83...e889`, full LOCAL-01—06 pass; separately preserved. |
| Test selection | The pre-caption 0.7.0 source passed the 77/100 minor-release union. The image-only change passed the affected catalog reproducibility case under dev scope `070-CONTENT-CAPTION` (1/30); the full release suite was not repeated. |
| Historical/current contract check | Frozen inventory and v1 schema bytes are checked directly; current source, manifest, files and SQLite content are checked separately. The obsolete missing-image generator is retired. |
| Deferred / independent follow-ups | H3 scenarios not run; W4 and external content review not completed. None blocks local release. |

The synthetic schema16 fixture was frozen from the prior working-tree runtime,
not produced by an identified old packaged executable. Keep this provenance.
The entire previous candidate, adjacent manifest and associated rehearsal results
are preserved under the candidate-specific local release evidence directory;
rehearsal JSON alone is not a complete candidate.

The caption correction was repackaged as
`.tmp/releases/0.7.0/20260924-142756-b88feba/`. The complete candidate, source ZIP,
Setup log, affected local results (`LOCAL-ACCEPTANCE.md`)
and exact hashes are retained there. Source and installed catalog matched for all
38 files; the installed UI showed the corrected image caption and no review or
training facts were created.

## 2. Ordered Delivery Tasks

Order: content implementation → test repair and final-source regression → complete
source commit / clean-checkout verification → package and local installed checks.
Source review may proceed earlier, but its final identity must include all fixes.
If source changes after regression, rerun only affected cases in the same release
scope, record the final identity, then rebuild and repeat affected package checks.

### 070-H1-CONTENT — Two remaining content revisions

**Status:** complete 2026-09-23. Input: owned source `070-illustrated-1`, content
rules in [initial-exercises-and-plan.md §10.1](initial-exercises-and-plan.md#101-canonical-names-and-movement-definitions).
Development scope: `070-H1-CONTENT`, tier dev, maximum 30 unique expanded cases.

Implementation:

- Keep `launch.glute-bridge` / 臀桥 and 常规臀桥; add 基础臀桥 as an alias.
  Specify lift → hold at the top for three seconds → controlled lowering; the
  complete cycle is one rep. Do not turn the hold into a set duration or actual dose.
- Keep `launch.butterfly-glute-bridge` / 蝴蝶臀桥; add 蛙式臀桥 after the existing
  normalized-name collision check. Do not create a duplicate movement.
- Advance each affected illustrated entry from v3 to v4, accounting for the existing
  image-version increment. Preserve the other 34 entries and all 36 image bytes.
- Set the next catalog identity to `070-illustrated-2`; rebuild with the project
  `.venv/python.exe` in an empty staging directory and verify before replacing the
  in-tree payload. Keep application 0.7.0/schema22 and current v2 wire contracts.
- Preserve frozen baseline bytes, retained old content, selected versions,
  activation pins and session history. No review or plan activation is fabricated.

Outputs: updated owned content and current payload/manifest; version/hash inventory;
focused results; synchronized current-content documentation.

Acceptance: both aliases find the existing identity; new guidance expresses the
three-second hold without dose changes; all 36 images decode/hash correctly;
catalog reconstruction is deterministic; old references and snapshots remain
readable. Reuse catalog reproducibility, library search and retained-history tests.
Do not add another per-image content-acceptance round.

Result at 070-H1 completion: source/payload was `070-illustrated-2`; only the two bridge entries
advanced from v3 to v4. `launch.glute-bridge` is
`93e75191886da45e85b945047faf73c24ee4fbbacea8ed1ce46805a2d5cdb3e7` and
`launch.butterfly-glute-bridge` is
`8966e044ddc9193a665db84d97ac570d3c25e4ed980478df493e966dce68fac3`.
The other 34 manifest entries and all 36 image hashes match the prior payload;
the frozen baseline hash remains `d3555e076d4a553996d2a0917c53fa224632778a369d9e70c821981efd629521`.
The rebuilt SQLite/manifest hashes are respectively
`a551721131cd1b78050049b664bd943d5db044dbb9097ebd233df4dc904df3eb`
and `7de2db1d617e3c6243294079680886bf21ff3e6a31a3d971d7104ea597107489`.
Dev scope `070-H1-CONTENT` passed all 3 unique affected cases within the 30-case
budget. No review, plan activation or training fact was created.

### 070-H2-TESTS — Selection repair and final regression

**Status:** complete 2026-09-23. Final H1 content was included in regression.
Development fixes use `--test-tier dev --test-scope 070-H2-TESTS`, maximum 30.
Release execution uses only `--test-tier minor --test-scope release-0.7.0`, maximum
100 unique expanded cases across every command.

Implementation:

- In the minor profile, replace removed
  `test_earlier_schema_chain_keeps_pre_snapshot_facts_unknown` with existing
  `test_out_of_window_root_refused_before_any_write` and
  `test_oldest_retained_schema14_root_converts_unknown_facts`.
- Update `test_catalog_inventory_covers_all_source_identities_and_freezes_v1`:
  validate the frozen historical inventory directly; validate today's catalog
  against today's source and manifest. Compare stable identities where relevant,
  not current guidance/image hashes against old missing-image values.
- Retire `packaging/prepare_contract_baseline.py` and its executable test dependency
  after this adjustment. Its original generation command stays dated historical
  evidence. Preserve the frozen inventory, v1 schema, schema16 DB and preservation
  fixtures while supported endpoints require them.
- Inventory other assumptions exposed by the 36-image change and repair reproduced
  failures with focused cases; do not hide scenarios, rewrite frozen hashes, or
  restore retired runtime modules to make tests pass.
- Recollect after implementation. The 63 + 18 − 4 = 77 selection estimate is based
  on the current 188 cases and only the named profile replacement; final changes
  may alter it. Record the actual union before release execution.

Outputs: valid profiles and historical/current inventory checks; documented final
selection and shared budget ledger; focused and release results; static checks.

Acceptance: default collection succeeds without stale entries; frozen bytes stay
unchanged; required selected scenarios pass within budget; no unresolved reproduced
failures affecting release. Relevant tests passing ends verification unless further
changes or unresolved concerns justify additional affected checks.

Result: the resident inventory remains 188; default collection succeeds and selects
12 dev cases. The corrected minor profile selects 63 cases. The conversion/recovery
files select 18, overlap the profile by 4, and produce an actual 77/100 unique-case
union in the shared `release-0.7.0` ledger. The 63-case profile and all 18 added
scenarios passed. Dev scope `070-H2-TESTS` used 5/30 unique cases for the repaired
contract check and support-window selection. Target Ruff passed. The frozen catalog
inventory, v1 schema, schema16 metadata/database and preservation fixtures retained
their pre-task hashes. No public H3 acceptance, review, activation, personal-data
transition or training fact was created.

### 070-H2-SOURCE — Complete, reproducible source identity

**Status:** complete 2026-09-24.

- Reviewed all runtime, v2 contract, owned image, catalog, fixture, packaging,
  documentation and intentional-deletion changes. The complete source commit has
  218 tracked files; its post-commit worktree was clean.
- The source boundary contains 72 owned PNG paths (36 seed plus 36 payload copies)
  and the read-only catalog SQLite. No user data, budget ledger, local acceptance
  root, planning record or `dist/` artifact was staged.
- Preserved the verified 2026-09-20 directory candidate, adjacent manifest and all
  41 associated evidence files at
  `.tmp/releases/0.7.0/20260920-142327-072c931-dirty/`. Its 257 payload files and
  evidence copies have zero path, size or hash differences.
- Generated and extracted a clean Git ZIP from the complete source identity. All
  67 package modules imported; the 14 frozen baseline files were unchanged; all
  36 image pairs were identical 1254×1254 PNGs; Markdown links and three-version
  inventory were complete.
- Rebuilt the catalog with the pinned project interpreter outside the source tree.
  All 38 output files matched the committed payload byte-for-byte. Target Ruff,
  compileall, PowerShell parsing, catalog verification and diff checks passed.

No source defect was found after the final regression, so no additional pytest case
or release-budget use was needed. H2-PACKAGE subsequently built from that exact
revision and its payload manifest reports the same clean source identity.

### 070-H2-PACKAGE — Installer and local installed checks

**Status:** complete, 2026-09-24. All three preceding tasks were complete before the final build.

- Use project Python 3.12, PySide6 6.11.2 and the pins in
  `packaging/requirements-build.txt`; the last verified interpreter was 3.12.14,
  PyInstaller 6.22.2 and hooks 2026.7. Do not silently change the runtime.
- Built the full PyInstaller directory and Inno Setup installer with the pinned command:

  ```powershell
  pwsh -File packaging/build.ps1 -Installer -ISCC 'C:\Users\41315\AppData\Local\Programs\Inno Setup 6\ISCC.exe'
  ```

- The final manifest binds clean source `736223e8b5258a914b106f04da90efd98ab215f7` and
  contains 293 files. Every payload path/size/hash matched both the directory candidate
  and installed program; only the two expected Inno uninstaller files were additional.
- Application 0.7.0/schema22, catalog `070-illustrated-2`, v2 contract, all 36 images,
  Qt resources, ffi/sqlite DLLs and isolated Qt loading passed; no user DB/locator was
  present in the payload and no external Codex-runtime DLL remained.
- [LOCAL-01—06](packaged-acceptance-runbook.md#12-local-installed-checks) passed with
  actual installed UI interaction, isolated profiles and a Chinese/space synthetic root.
  The representative group session preserved position 1, a user-entered partial 4-rep
  result, a blank—not zero—second actual, frozen v4 guidance/image and unreviewed state.
- Candidate evidence is indexed by
  `.tmp/releases/0.7.0/20260924-010017-736223e/LOCAL-ACCEPTANCE.md`. Payload manifest,
  EXE and Setup hashes are `e72dfdb7...9aa9`, `dc7f24dd...e7e` and `4fdf7f83...e889`.
  EXE and Setup Authenticode are `NotSigned`; signing remains a public-release follow-up.
- Preserve old candidate results with the old candidate. Any rebuilt candidate gets
  its own identity and affected package checks; source changes return to H2-TESTS
  and H2-SOURCE as required.

Outputs: complete directory, Setup, both manifests, local evidence and local-release
status. Default evidence organization is `.tmp/releases/0.7.0/<candidate-id>/`,
where candidate-id includes build timestamp and source revision.

Acceptance is met: preceding tasks closed; all required local rows pass for this exact
candidate; program/data boundaries remain intact. H3's independent machine,
actual old-binary upgrade inputs and full scaling matrix do not block this exit.

## 3. Verification Plan

Future commands below are **not executed by the 2026-09-23 documentation task**.
First repair both known test issues; then recollect the corrected baseline and
additional recovery/conversion files:

```powershell
.venv\python.exe -m pytest --test-tier minor --collect-only -q
.venv\python.exe -m pytest tests/test_070_upgrade_recovery.py tests/test_070_conversion.py --test-tier minor --collect-only -q
```

Deduplicate node IDs and include any additional affected cases in the same release
union. Collection neither reserves budget nor establishes passing behavior.
Release commands, after final source and selection review:

```powershell
.venv\python.exe -m pytest --test-tier minor --test-scope release-0.7.0 --basetemp .tmp/pytest-release-0.7.0
.venv\python.exe -m pytest tests/test_070_upgrade_recovery.py tests/test_070_conversion.py --test-tier minor --test-scope release-0.7.0 --basetemp .tmp/pytest-release-0.7.0
.venv\python.exe -m ruff check src tests packaging
git diff --check
```

Never rename scopes, reset ledgers or split selections to evade the cap. If an
application version changes, choose the genuine release scope before its first
execution and preserve prior ledgers. Subsequent fixes rerun failed/affected cases,
not automatic full-suite passes. Packaging checks are separate artifact evidence,
not a substitute location for hidden regression scenarios.

## 4. Workspace Cleanup Plan

The retained window is **0.7.0 / 0.6.1 / 0.6.0**. The completed 2026-09-21 cleanup,
old space estimates and removed directories are recorded in
[history](history/0.7.0/development.md#workspace-cleanup-completed-2026-09-21);
they are not a fresh deletion queue.

Current document cleanup:

- Keep current requirements in authoritative documents and completed evidence in
  `docs/history/<version>/`; merge duplicate status descriptions rather than
  creating another independent specification.
- The retired single-file image-prompt entry is superseded by
  [the batch index](image_prompts/README.md). Keep both complete batch files and
  remove obsolete current links; do not delete current prompt content.
- Archive the completed 2026-09-22 root task records as a concise 0.7.0 summary.
  Maintain root record soft limits of 150/250/200 lines.
- Keep historical missing-image facts and hashes dated and immutable. Preserve
  retained contracts, fixtures, manuals and the deferred public runbook.
- This documentation task deletes no runtime code, generators, images, packages,
  user roots or test-budget ledgers. Code retirement is future H2-TESTS work.

Before any later artifact cleanup, preserve useful owned source and a verified
complete copy of every required retained candidate/evidence dependency. Keep
`.tmp/test-budgets/`, real backups, original answers/exports and personal roots.
Record exact retained/deleted locations and recovered space only after the action.

## 5. Deferred Public Release And Separate Follow-ups

**070-H3 / 8-B2: deferred, not run.** The sole reactivation trigger is an explicit
user request for public release. Then refresh the [public runbook](packaged-acceptance-runbook.md#5-public-release-acceptance--deferred)
and candidate evidence, locate identified 0.6.0/schema14 and 0.6.1/schema16 binaries,
and execute independent installation/upgrade/recovery/backup/uninstall and scaling
scenarios. A rebuilt old tag is not proof of a missing original dirty binary.
Keep public signing/distribution requirements for that stage.

External content review and W4 remain unfinished independent follow-ups under the
[guidance runbook](guidance-review-runbook.md). They do not block local release.
Personal-data transition requires its own explicit user decision; synthetic
approvals/training never become personal facts. Revisit public readiness against
the exact candidate when that stage is requested.
