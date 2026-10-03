# 0.8.1 Development Record

On 2026-10-03, TrainingFeedback added process-scoped discovery of the latest
stable GitHub Release. The application version changed from 0.8.0 to 0.8.1;
database schema 23, catalog `070-illustrated-3` and plan/evidence contract 3 did
not change.

## Implementation

- The main window starts one asynchronous public latest-Release request after it
  is visible. A root switch reuses the same coordinator and result.
- Strict application-layer parsing accepts only stable `vX.Y.Z` tags and trusted
  repository URLs. A direct Setup action additionally requires one exact uploaded
  asset and a GitHub SHA-256 digest.
- A newer version shows the sidebar hollow-circle exclamation mark. Settings owns
  checking, current, ahead and failure text plus manual retry.
- Release details remain plain text. Release and Setup actions open the system
  browser; the application does not download, verify, execute or install files.

## Verification

Concrete startup risk: the main window now imports the QtNetwork-backed update
coordinator and production creates that coordinator before the window opens.

- Scope: `update-0.8.1-github-update`, dev tier.
- Selected scenario: file `tests/test_update_startup.py`, node
  `test_update_coordinator_does_not_block_main_window_startup`.
- Result: **1 passed in 1.12 s** using an isolated synthetic root and a production
  coordinator subclass that prevents any network request. No rerun.
- Ruff for changed Python files, `git diff --check` and `packaging/check_docs.py`
  passed before the clean source commit.
- Manual tests: **0**. No GUI automation or client operation was performed.

Release parsing, sidebar interaction, browser download, Setup execution and
overwrite installation were not run. Under the current startup-only policy they
are neither passes nor outstanding gates; actual-use feedback governs follow-up.

## Candidate

| Item | Value |
| --- | --- |
| Application source | `2be4651a0325d2ead04db2de40d52f6ef42df5b0` |
| Source dirty | no |
| Application/schema/catalog/contract | 0.8.1 / 23 / 070-illustrated-3 / 3 |
| Payload files | 296 |
| Python / PySide6 / PyInstaller | 3.12.14 / 6.11.2 / 6.22.2 |
| Setup | `TrainingFeedback-0.8.1-Setup.exe` |
| Setup bytes | 85,611,215 |
| Setup SHA-256 | `5e9299066ad13c6ef78a2e6e8fb07b013595b57f240c64be54f388c8a219b0cf` |
| Signature | not signed |

The build succeeded and the generated manifest contains QtNetwork and Windows
TLS payloads. Building and identity inspection do not establish installed client
behavior. This candidate does not declare a formal compatibility baseline,
public support, external content review, personal-data transition or W4.
