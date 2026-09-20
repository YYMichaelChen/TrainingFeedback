# 0.7.0 Release Review And Workspace Plan

Reviewed: 2026-09-20; decisions consolidated: 2026-09-21.
**Verdict: local development candidate verified; formal release not accepted.**
Authority: [development plan](development-plan.md), especially §§9, 12–13.
This file records evidence and execution tasks; it does not duplicate product rules.
It belongs to the 0.7.0 retention slot, moving to that archive after closeout.

## 1. Observed Baseline

| Area | Observation / evidence |
| --- | --- |
| Application / schema | Source and directory manifest: 0.7.0; converted development root: schema22. |
| Source identity | HEAD `072c931` / tag `v0.6.0`; candidate is dirty-source. Review found 39 modified, 41 deleted, 77 untracked files and nothing staged. These counts precede this documentation task. |
| Directory candidate | `dist/TrainingFeedback/`, 257 files; actual count, sizes and all SHA-256 values match the adjacent manifest. |
| Catalog | Source and payload verify as 070-baseline-1, 36 entries, zero illustration files. |
| Local rehearsal | `.tmp/070-h-package/verification.json` and `rehearsal-result.json`: 7/7 checks for schema16 → 22, one conversion, original registrations available, integrity/FKs, retained recovery snapshot, idempotent restart and empty-profile startup. Offscreen/build-machine only. |
| Installer | Only 0.6.1 Setup.exe and matching manifest currently in `dist/installer/`; original installer hash verified. No 0.7.0 installer result. |
| Tooling correction | `C:\Users\41315\AppData\Local\Programs\Inno Setup 6\ISCC.exe` exists. Earlier “Inno Setup unavailable” records were inaccurate; actual 0.7.0 compilation remains pending. |
| Static checks | `ruff check --no-cache src tests packaging`, `git diff --check`, AST parsing of 95 Python files passed. |
| Test inventory | Resident 184; minor baseline 61; recovery/conversion files 16, with two overlapping baseline cases: proposed release union 75/100. Collection only, not passing regression evidence. |
| Independent acceptance | 070-01–070-12 all not run. W4 and real content review not established by synthetic checks. |

Exact binary/manifest hashes stay with the original candidate evidence. Preserve
the complete directory and adjacent manifest together; `.tmp/070-h-package/`
alone is not a complete copy of the candidate.

## 2. Ordered Delivery Tasks

### 070-R1 — Reproducible baseline (first)

- Add a precise `.gitignore` exception for the synthetic
  `docs/contracts/baseline/schema16-root/training_feedback.sqlite3`, then include
  it in reviewed source. It is currently ignored by `*.sqlite3`; both migration
  fixtures and `prepare_acceptance_data.py` require it.
- Protect frozen root bytes with path-specific Git attributes (for example `-text`
  for that root). Current `core.autocrlf=true` and absent `.gitattributes` allow
  clean filters to alter CRLF exports/imports/answers; mixed LF/CRLF files also
  risk checkout changes. Do not regenerate hashes to conceal changed originals.
- Verify all frozen files and resource hashes after a clean checkout/archive.
  Preserve the synthetic baseline's provenance; it was not produced by the actual
  preserved 0.6.1 packaged executable.
- Review all new/deleted modules and create a reproducible source commit/snapshot.
  The removed old runtime is intentional G3 work, not a reason to restore HEAD files.

### 070-R2 — Three-version runtime support

Status: implemented 2026-09-21 (dev tests 27/27 under scope 070-R2); candidate-level
re-verification stays with 070-H2/H3.

- Implement the application/schema support mapping and pre-write lower-bound guard
  in root inspection/startup/switching/conversion. Current endpoints: 0.6.0/14,
  0.6.1/16 and 0.7.0/22. Enumerate historical intermediate handling explicitly.
- Retire out-of-window upgrade entry paths, exclusive schemas/fixtures/helpers,
  and consolidate current fresh initialization. Keep dependency steps needed by
  retained endpoints; do not simply delete migrations 1–13 and break fresh create.
- Replace schema1/9 positive-upgrade coverage with too-old rejection where appropriate;
  add meaningful oldest-retained schema14 coverage and retain schema16 recovery.
- Verify refusal does not alter files/locator, supported conversion preserves facts,
  fresh roots use the bundled catalog, and the reinstall/new-empty-root instruction
  is clear. If this work changes schema22, bump application/schema together.

### 070-H1 — Complete built-in development content

- Reconcile intentional development additions/changes into the owned source catalog
  before any old development root is discarded. Track key, content version/hash,
  image source/path/hash and review/readiness; do not automatically harvest user data.
- Deliver the planned bridge three-second hold and aliases as new content versions;
  retain old facts/pins. Obtain actual illustrations for at least the initial plan's
  13 references, then continue the remaining entries with explicit readiness.
- Ensure catalog build input includes the real assets reproducibly. Current default
  source build represents missing images; copying files beside an unchanged manifest
  is not delivery. Preserve the frozen 070-A inventory as baseline evidence while
  creating the new current inventory and updating affected catalog checks.
- Verify a new root can browse the complete latest built-in library without old
  roots/imports. Valid assets do not fabricate review or activate a plan.

### 070-H2/H3 — Candidate, installation and acceptance

- Run the budgeted minor selection on final source; build a separately identified
  candidate/installer and retain source provenance and complete manifests.
- Use the existing Inno compiler explicitly if discovery is inconclusive:

  ```powershell
  pwsh -File packaging/build.ps1 -Installer -ISCC 'C:\Users\41315\AppData\Local\Programs\Inno Setup 6\ISCC.exe'
  ```

- Prepare isolated baselines opened/closed by actual retained old binaries, including
  schema14 and schema16. Complete install/upgrade/uninstall isolation, interrupted
  recovery, backup/reopen, grouped workflow and scaling evidence on independent Windows.
- Locate the exact retained 0.6.0 binary/manifest before deleting historical packages.
  If it is unavailable, document the gap and build a separately identified previous
  candidate from known source; never claim a tag rebuild equals a missing dirty build.
- Fill the [current runbook](packaged-acceptance-runbook.md) from observed results.
  Keep unavailable rows not run; a rebuilt candidate has its own evidence identity.
- PERSONAL/W4 begins only after the user's explicit transition decision. Content
  review and first-usable-release evidence follow development-plan §§9–10.

## 3. Verification Plan

Use one release scope/tier for all release pytest execution; collect again if the
implementation changes selection. Current proposed commands (not executed here):

```powershell
.venv\python.exe -m pytest --test-tier minor --test-scope release-0.7.0 --basetemp .tmp/pytest-release-0.7.0
.venv\python.exe -m pytest tests/test_070_upgrade_recovery.py tests/test_070_conversion.py --test-tier minor --test-scope release-0.7.0 --basetemp .tmp/pytest-release-0.7.0
.venv\python.exe -m ruff check src tests packaging
git diff --check
```

The current union is 75/100, not 61+16 independent slots. If the actual release
version changes, name its scope before the first execution; never rename/reset an
active scope to evade its budget. Development fixes have their own genuine task
scope and ≤30 cap. After affected tests pass, stop; packaging and independent checks
are separate required evidence, not disguised pytest cases.

## 4. Workspace Cleanup Plan

The version window is **0.7.0 / 0.6.1 / 0.6.0**. Complete development documents and
schema support obey that window, not an indefinite archive. Active requirements
are merged forward; the user-data transition has not been authorized.

### A. Inventory and preserve before deleting

1. Confirm useful development content is in owned current source, including actual
   assets; identify any uncommitted-only source/fixtures before staging or cleanup.
2. Inventory retained-version candidate manifests, program/installer files, source
   snapshots, results, screenshots, fixture dependencies and test-budget ledgers.
   Bind each to application version plus exact commit/build, not just a directory name.
3. Keep one verified copy of each required retained candidate and its evidence;
   remove duplicate ZIP/extracted copies after hash/restore verification. Organize
   local evidence under `.tmp/releases/<version>/` and task summaries under
   `.planning/archive/<version>/`; update references in the same action.
4. Review unclassified local artifacts before disposal. Personal roots, original
   answers/exports and real backups are not build garbage. Do not touch `user_data/`
   or real roots as part of this workspace cleanup.

### B. Rebuildable files

| Target | Review size | Action |
| --- | --- | --- |
| `.tmp/pytest*` | 134 directories, ~3.44 GiB | After test processes exit, preserve any required reproducer/evidence and remove disposable roots. Keep `.tmp/test-budgets/`. |
| `.planning/tmp/` | ~216 MiB | Preserve relevant retained-version evidence, then remove old test roots/screenshots not needed. |
| `build/`, caches, `__pycache__/` | build ~11 MiB, plus caches | Remove after processes finish; toolchain can rebuild them. |
| `.tmp/070-[b-f]-package/` | ~0.60 GiB | These are 0.7.0 intermediate candidates, not five application versions. Keep necessary evidence and avoid duplicate full payloads. |
| `.tmp/development-updates-20260912`, `.tmp/release-readiness-20260912` | ~1.74 GiB total | Mostly out-of-window deliveries; inventory untracked provenance/content, then remove expired complete packages and duplicates. |

`.tmp` totals ~5.85 GiB. The first rebuildable group can recover ~3.66 GiB before
candidate deduplication. These are planning estimates from the review, not deletion
results. Retain `.venv` (~0.82 GiB) for the verified build toolchain.

### C. Rotate documents, schemas and source together

- Completed plan material is now indexed under `docs/archive/` for the three versions.
  Still classify/trim historical local `.planning/archive/` and `.tmp/` material;
  moving it into another unlimited backup is not policy compliance.
- Retire old-version-exclusive contracts, schemas, fixtures and migration entry paths
  together with 070-R2, after dependency checks. The current synthetic schema16
  baseline remains necessary even though it is an older schema.
- Stage only reviewed source/docs/assets; check clean-checkout reproducibility and
  retain a known source identity before making the next formal candidate.
- Final inventory records retained versions, evidence locations, removed items and
  recovered space. Actual disk cleanup and migration-code changes remain pending.
