# 0.7.4 Local Candidate

Candidate status: **built; installed acceptance incomplete**. This record does
not certify a completed local release. Public release checks were not requested
and were not run.

## Identity

- Built: `2026-09-27T15:01:20Z`
- Source revision: `d6cc67a2302274558a060249c879b2d9ddde3fbb`
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
| Payload manifest | `dist/TrainingFeedback.build-manifest.json` | 56,442 | `dfcf06bde4ec768475ac9f23a0289baa502798ed367abedab148b465b5718b38` |
| Application EXE | `dist/TrainingFeedback/TrainingFeedback.exe` | 3,081,060 | `f2b6abba96b87fa3eb05aebb23ff70dad10a075d6ea7c14de175fb6ea44d7a99` |
| Setup EXE | `dist/installer/TrainingFeedback-0.7.4-Setup.exe` | 85,534,020 | `f40c6224c5196e0a3595f71f543936633cd465fd950b8c47cb554cb7f54e8c1c` |
| Setup manifest | `dist/installer/TrainingFeedback-0.7.4-Setup.build-manifest.json` | recorded locally | `04832332612d09dabb017a520b5f38f11a287b0d864de382cd080f47d2a1ac0b` |

The payload contains 294 files. Both executable signatures report `NotSigned`,
which is acceptable for this local candidate. Signing and public distribution
are separate gates.

## Verification

| Check | Status | Evidence |
| --- | --- | --- |
| Release regression | pass | Scope `release-0.7.4`, patch tier: 27 unique cases passed; 151 deselected. |
| Ruff | pass | `python -m ruff check src tests packaging` |
| Diff check and source identity | pass | `git diff --check`; source tree clean at build revision. |
| Catalog and payload build | pass | Catalog manifest verified at source and packaged path; pinned build baseline passed; build script found no missing runtime files or user data. |
| Setup compile | pass | Inno Setup 6.7.3 compiled `TrainingFeedback-0.7.4-Setup.exe`. |
| Installed payload | pass | Installed under `.tmp/local-installed-0.7.4`; all 294 manifest files matched path, size and SHA-256. Only standard Inno uninstaller files `unins000.exe` and `unins000.dat` were additional. |
| Fresh launch and cancel | pass | Installed chooser appeared. Cancel closed the app; isolated profile `.tmp/local-profile-0.7.4` contains no `TrainingFeedback/locator.json`. |
| New synthetic root and bundled catalog | not run | Interactive acceptance was stopped before root creation. |
| Restart/reopen and changed library workflow | not run | Interactive acceptance was stopped before these checks. |
| Supported-root upgrade and expired-root refusal | not applicable | This patch retains schema 22 and makes no database, catalog or wire-contract revision. Source regression covers retained-root opening and expired-root refusal. |
| Independent Windows/public checks | not run | Not requested; remain deferred to an explicit public-release request. |

## Evidence limits

The installed copy matches the candidate payload, and the first-launch chooser
and cancellation path were observed. The interactive UI tool reported that it
was stopped with the physical Escape key before new-root, restart and action-
library checks completed. Do not treat those checks as passes. The Setup and
payload are local build artifacts under `dist/`; this record does not certify
public distribution, external content review, personal-use readiness or W4.
