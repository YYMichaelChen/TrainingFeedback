# 0.7.4 Local Candidate

Candidate status: **built; installed acceptance incomplete**. This record does
not certify a completed local release. Public release checks were not requested
and were not run.

## Identity

- Built: `2026-09-27T16:40:32Z`
- Source revision: `0d3653f22443550d00d99fc7b3d6c994809523d0`
- Source dirty: `false`
- Application: `0.7.4`
- Database schema: `22`
- Catalog: `070-illustrated-3`
- Plan/evidence contracts: `v2`/`v2`
- Build host: Windows 11 x64, Python 3.12.14 AMD64, PySide6 6.11.2
- Packaging: PyInstaller 6.22.2, pyinstaller-hooks-contrib 2026.7,
  Inno Setup 6.7.3

| Artifact | Path | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Payload manifest | `dist/TrainingFeedback.build-manifest.json` | 56,441 | `ebcf14c7aaf1b3ab5ed02433a8660434f112130f4f624b1b5b839b1561436352` |
| Application EXE | `dist/TrainingFeedback/TrainingFeedback.exe` | 3,081,668 | `2f51b2d2667d03e70292b4fe830a5a737158eef97a36078a351282f5734e04c9` |
| Setup EXE | `dist/installer/TrainingFeedback-0.7.4-Setup.exe` | 85,528,061 | `253c5b069403fb5c8e61f9a0c2af33916cd945f76671944cc0c193ba43733a11` |
| Setup manifest | `dist/installer/TrainingFeedback-0.7.4-Setup.build-manifest.json` | 59,861 | `358790ae469435afa5140ac34f063462765c100b41259ae0544cf629e38488e2` |

The payload contains 294 files. Both executable signatures report `NotSigned`,
which is acceptable for this local candidate. Signing and public distribution
are separate gates.

## Verification

| Check | Status | Evidence |
| --- | --- | --- |
| Release regression | pass | Scope `release-0.7.4`, patch tier: 29 unique cases passed; 151 deselected. |
| Ruff | pass | `python -m ruff check src tests packaging` |
| Diff check and source identity | pass | `git diff --check`; source tree clean at build revision. |
| Catalog and payload build | pass | Catalog manifest verified at source and packaged path; pinned build baseline passed; build script found no missing runtime files or user data. |
| Setup compile | pass | Inno Setup 6.7.3 compiled `TrainingFeedback-0.7.4-Setup.exe`. |
| Installed payload | pass | Setup exit code 0; installed under `.tmp/candidate-acceptance-074-clean/program`; all 294 manifest files matched path, size and SHA-256. Only standard Inno uninstaller files `unins000.exe` and `unins000.dat` were additional. |
| Fresh launch and cancel | not run | The installed process opened the chooser (`选择训练反馈数据目录`) under isolated profile `.tmp/candidate-profile-074-clean`; the profile has no `TrainingFeedback/locator.json`. The desktop-control bridge returned no app windows, so the visible chooser and cancel behavior could not be inspected. |
| New synthetic root and bundled catalog | not run | Requires visible UI interaction; the desktop-control bridge returned no app windows. |
| Restart/reopen | not run | Depends on completing a new-root check through the unavailable visible UI. |
| Changed action-library workflow | not run | Requires visible interaction; focused source regression covers the plan-editor selection change only. |
| Supported-root upgrade and expired-root refusal | not applicable | This patch retains schema 22 and makes no database, catalog or wire-contract revision. Source regression covers retained-root opening and expired-root refusal. |
| Independent Windows/public checks | not run | Not requested; remain deferred to an explicit public-release request. |

## Evidence limits

The installed copy matches the candidate payload. A process-level chooser title
was detected in the isolated profile, but the desktop-control bridge exposed no
application windows, so visible launch/cancel, new-root/catalog, restart and
changed library workflow checks remain `not run`. Do not treat those checks as
passes. The Setup and payload are local build artifacts under `dist/`; this
record does not certify public distribution, external content review,
personal-use readiness or W4.
