# 0.8.2 Development And Candidate Record

On 2026-10-03, TrainingFeedback removed user-defined training-day names,
introduced plan/evidence contract v4 and database schema 24, improved exercise
illustration presentation, and set the application window icon. Catalog
`070-illustrated-3` did not change.

## Implementation

- Plan models, persisted plan/session snapshots, UI presentation and new
  plan/evidence files no longer contain a training-day name. A one-day active
  plan is shown by its plan name; multi-day choices use `训练日 N`.
- New plan imports and evidence use contract v4. V2/v3 runtime schemas remain
  packaged as historical files, but only v4 is accepted for a new import.
- Schema 23 roots upgrade transactionally to schema 24. The upgrade removes the
  three obsolete name columns while retaining plans, sessions, feedback, review
  events and original evidence bytes; a failed upgrade rolls back.
- The action-library image tab now says `动作示意图`. Card thumbnails use the
  display device-pixel ratio, and detail images scale to the available area while
  retaining the original-image dialog.
- The runtime icon is the same byte identity as `icon/TrainingFeedback.ico` and
  is included in the packaged resources.

## Verification

Concrete startup risk: opening a supported schema 23 root now performs the new
23→24 migration. A failure could prevent the application from entering its main
window, and a partial failure must not leave the root half-upgraded.

- Scope: `v0.8.2-release`, dev tier.
- Selected scenarios:
  - `test_schema23_upgrade_drops_only_training_day_name_columns_and_preserves_rows`
  - `test_schema23_upgrade_rolls_back_all_column_changes_when_version_write_fails`
- Result: **2 passed in 0.08 s** against in-memory synthetic schema 23 data; no
  rerun and no real user root was opened.
- Ruff for changed Python files, `git diff --check` and
  `python packaging/check_docs.py` passed before the application-source commit.
- The runtime/source icon hashes matched. The clean package build verified the
  catalog and required packaged schema, contract and icon resources.
- Manual tests: **0**. No GUI automation or client operation was performed.

The existing main-window test was not run because it also navigates pages and
checks image rendering beyond the permitted startup-risk scope. DPI sharpness,
detail-image fitting, visible title-bar icons, complete plan workflows,
import/export behavior and installed overwrite behavior were not observed and
are not recorded as passes. Under the current personal-use policy they are not
outstanding release blockers; normal-use feedback governs follow-up.

## Candidate

| Item | Value |
| --- | --- |
| Application source | `75b34bb45e1179df8f93b2cbe7656982272a7421` |
| Source dirty | no |
| Application/schema/catalog/contract | 0.8.2 / 24 / 070-illustrated-3 / 4 |
| Payload files | 298 |
| Python / PySide6 / PyInstaller | 3.12.14 / 6.11.2 / 6.22.2 |
| Inno Setup | 6.7.3 |
| Setup | `TrainingFeedback-0.8.2-Setup.exe` |
| Setup bytes | 85,660,884 |
| Setup SHA-256 | `c04ba484d6d6cbf9a7c3347a0728ad4859e11a51cb131641465b5c18ab568d97` |
| Setup signature | not signed |
| EXE signature | not signed |

The generated [payload manifest](payload-build-manifest.json) and
[installer manifest](installer-build-manifest.json) preserve the exact candidate
identity. Building and manifest inspection do not establish installed client
behavior. This candidate does not declare a formal compatibility baseline,
public support, external content review, personal-data transition or W4.
