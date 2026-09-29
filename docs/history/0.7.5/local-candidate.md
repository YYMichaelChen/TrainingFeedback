# 0.7.5 Local Candidate

Candidate status: **user-approved to continue development; installed acceptance
not run for the corrected clean candidate**. The earlier installed candidate
failed the schema 22 check. Results below identify each candidate separately
and do not certify a public release or personal-use readiness.

## First installed candidate: source and artifacts

- Source revision: `acce64846feb6c6090331bc17acd31d1377f5ef4` (`main`, pushed to
  `origin`); the build manifest records `source_dirty: false`.
- Application/schema/catalog: `0.7.5` / `23` / `070-illustrated-3`.
- Build manifest: `dist/TrainingFeedback.build-manifest.json`, SHA-256
  `e1f87b0b564903ff27e7516e1c8c40ce39119fa8c0bdb0e5da1b8deac89cb277`.
- Installer: `TrainingFeedback-0.7.5-Setup.exe`, 85,546,891 bytes, SHA-256
  `607e5d8c1c0af694f964caea6711e0863feb1c73d3aed5d93116f233c292f1ca`.
- Installer manifest:
  `TrainingFeedback-0.7.5-Setup.build-manifest.json`, SHA-256
  `8a4ae73c16abdf41e26ef972f27034186c98c1de79cb47ea64e5b89ec77802e5`.
- Payload: 295 files; `TrainingFeedback.exe` is 3,104,576 bytes with SHA-256
  `a500c30d00e33dc820a2344a841f567d27cfb9ffc06446941ef9c7b5cd9e380f`.
- The setup executable is unsigned (`NotSigned`).

## First candidate checks

- 48 unique affected cases passed under the single `release-0.7.5` patch scope.
  The 30-case configured patch regression profile would make a 65-case union,
  exceeding the patch cap of 50, so that profile was not run. The scope was not
  reset or split.
- Ruff, `git diff --check`, Python bytecode compilation, and catalog source
  verification passed.
- The clean candidate was installed first into an isolated synthetic profile.
  All 295 payload files matched the build manifest; its first-run data-root
  chooser was started and responsive. Visual confirmation of the chooser and
  cancellation behavior was unavailable because the desktop bridge exposed no
  native application windows.
- Installer exit code was 0 when updating the standard per-user program
  directory `C:\Users\41315\AppData\Local\Programs\TrainingFeedback`.
  All 295 installed payload files match the build manifest, with no missing or
  hash-mismatched files. The installed executable has the expected size and
  SHA-256 above. Schema 23 and the v3 contract are present in the installed
  payload.
- The installed application was not launched under the real user profile. No
  real data root was opened. Root creation, schema 22 reset in a real installed
  run, restart/recovery, and end-to-end authoring workflows were not run.
- Windows visual acceptance, independent Windows acceptance, external content
  review, W4, and public-distribution checks were not run.

## Acceptance state

The source checks and local installation completed. Local release acceptance
remains incomplete because the configured regression profile exceeded the
single-scope patch limit and the installed UI/root workflows were not visually
verified. The installation is the identified local candidate only.

## 2026-09-28 acceptance continuation

The installed candidate above was opened with isolated `%LOCALAPPDATA%` profiles
and synthetic roots under `.tmp/acceptance-075/`. Its root chooser cancelled
without creating a locator or root. A Chinese/space-containing new root opened
at schema 23, and the UI showed the bundled `070-illustrated-3` catalog with 36
illustrated exercises. A blank plan save was rejected; cancelling the editor
left zero plans. Restart through the same isolated locator opened the root.

The candidate **failed** the retained-root installed check: a valid schema 22
synthetic copy produced “数据目录中的数据库无效或已损坏。” The untouched original and failed
copy both retained schema 22, one old group plan and session, one legacy plan
and session, and the same database SHA-256
`9273dbea8630f3740063f13714702fdf7a7552bf63b1af4dbddc2a5f96007695`.
The installed payload omitted `training_feedback/data/schema22.sql`, which
`one_time_reset.py` reads before migration. The original installed candidate
therefore cannot be accepted for schema 22 upgrades.

The packaging spec and build gate now include both SQL schemas. A **dirty-source
directory preview**, not an accepted candidate, was built and inspected:

- Manifest SHA-256 `4e2c1c2eb79e5727a9d29fedc6345bc8d671a015410f8ccbd62087ce22f06308`;
  EXE SHA-256 `9606033e101bfed74e4884f171ffe398b9d70e9f1e1dfb0a7e1f3ca98ecf3286`.
- All 296 payload paths, sizes and hashes matched the manifest. Bundled
  `schema22.sql` matched source bytes; its SHA-256 is
  `614a34ac9c4e3fc6e894049f8e3421769090d83ad910a7ee83a1a04a6893c721`.
- The preview EXE opened a closed schema 22 synthetic copy from an isolated
  locator and displayed the main window. After closing, its database was schema
  23; group/legacy plans and sessions were empty, retained `body_area` and
  `library_reference` rows remained, managed backup/export/import directories
  were empty, and the cleanup journal was empty. The unopened original stayed
  at the SHA-256 above with its old rows and managed files intact.
- The preview manifest says `source_dirty: true`. No Setup was built or installed
  from it. These results do not transfer to a later clean candidate.

The single `release-0.7.5` patch ledger now contains 50 unique cases. Two
additional risk-selected cases passed; one needed a stale test assertion updated
for the new `plan_code` field before its rerun. The configured 30-case profile
was still not run, and its 17 distinct unselected cases remain unrun. Selection
and reasons are in [acceptance test design](acceptance-test-design.md). Installed
invalid/occupied destinations, complete plan-to-training workflow, and other
applicable candidate checks remain `not run` for the corrected build. Local
acceptance remains incomplete.

## 2026-09-29 corrected clean candidate: package inspection

This is a new candidate. The previous installed and dirty-preview results above
do not count as installed results for it.

- Source revision: `afabe02794f6ebba50d97f380d8c17b10ef1bfc0` (`main`,
  pushed to `origin`); the payload manifest records `source_dirty: false` at
  build time. A later local `AGENTS.md` edit is outside this source snapshot.
- Built 2026-09-28 16:24 UTC on Windows AMD64 with Python 3.12.14, PySide6
  6.11.2, PyInstaller 6.22.2 and Inno Setup 6.
- Application/schema/catalog: `0.7.5` / `23` / `070-illustrated-3`.
- Payload: `dist/TrainingFeedback/`, 296 files. Manifest:
  `dist/TrainingFeedback.build-manifest.json`, SHA-256
  `24b6698683c04145c175618b34b43b2a9ab867bb3cdba8040d86a67e0c4b6280`.
  All paths, byte lengths and SHA-256 hashes matched; there were no extra files.
- EXE SHA-256:
  `76b36ddd2a16261e884e0bb55b2fabb61f7e0c1cc86ca8d05fee6204b0e4fe47`;
  it is unsigned (`NotSigned`).
- Installer: `dist/installer/TrainingFeedback-0.7.5-Setup.exe`, 85,547,966
  bytes, SHA-256
  `1d5843c4958cb3d540ab94af2a7dd5c2c24697b641213d555d1d522be57ffb3d`.
  Its adjacent build manifest has SHA-256
  `1d7e572d6fa09dfb16c75e94764d65a28eb88b11820d92e0780f24cfdcb93f35`;
  its embedded payload manifest equals the adjacent payload manifest. The Setup
  is unsigned (`NotSigned`).
- Both bundled `schema22.sql` and `schema23.sql` match source bytes. Their
  respective SHA-256 hashes are
  `614a34ac9c4e3fc6e894049f8e3421769090d83ad910a7ee83a1a04a6893c721`
  and `d71e904a211c04da7b3d947cb2eb773d3cb1aadde3b38aafebe2a74610171f8e`.
  The packaged catalog verification passed with 36 illustrated exercises. No
  locator or user-data SQLite file was found in the payload.
- The `release-0.7.5` ledger is still one `patch` scope with 50 distinct cases.
  No new pytest case was executed for this package inspection. The configured
  profile and its 17 unselected cases remain `not run`.

### Installed checks awaiting developer operation

All rows below are **not run** for this corrected candidate. The developer must
operate the installed client manually and record the observed result, synthetic
profile/root paths, closed-input baseline and evidence path/hash for each row.
Use fresh copies of synthetic roots and keep unopened originals. Do not launch
the program under a real user locator or open a real schema 22 root.

| Check | Manual operation and expected observation | Status |
| --- | --- | --- |
| Install and replacement | Suppress automatic launch, install this exact Setup, compare every installed file to the 296-file manifest, and confirm the closed isolated locator/root bytes did not change during installation. | `not run` |
| Fresh choice and bad destinations | With a fresh isolated `%LOCALAPPDATA%`, cancel the chooser; confirm no locator/root. Retry with an invalid and an occupied destination; confirm clean rejection and no partial root. | `not run` |
| New root and restart | Create a Chinese/space-containing synthetic root; inspect schema 23 and all 36 bundled illustrated exercises without invented plans or reviews. Close and reopen through the same isolated profile; confirm selection and facts persist without duplicate migration. | `not run` |
| Schema 22 reset | Open separate closed copies from the retained 0.7.3 and 0.7.4 endpoints. Confirm exactly the declared plan/training rows, associated managed files and in-root backups are removed, independent library/review/image facts remain, and schema becomes 23. Reopen each copy; confirm cleanup is complete and originals remain byte-identical. This is an intentional reset, not plan preservation. | `not run` |
| Rejection before writes | Open synthetic expired, future and invalid-root copies. Confirm actionable refusal, unchanged database/managed-file hashes and no cleanup. | `not run` |
| Changed plan and training UI | In a new synthetic root, use the unified editor to create days, actions and a group with distinct set doses. Check incomplete/invalid input stays visible and cannot save; save a valid plan, reopen exact text/doses, clone/upgrade and inspect codes/diff, then activate and start. Leave actuals blank, pause, restart and resume; check frozen prescription and position. | `not run` |
| Current wire contract | Through the installed UI, export/import a v3 plan or evidence sample and compare displayed code, text and exported facts; verify v2 import receives the current-format error and creates no draft or managed file. | `not run` |

Local acceptance remains incomplete until the applicable installed rows have
candidate-specific manual results. The source and package checks above do not
replace those observations. Independent public acceptance, external content
review, W4 and personal-use readiness remain outside this local candidate.

## 2026-09-29 user release decision

The user directed: “放行0.7.5，标记批准继续开发。” This approves progression beyond
0.7.5 with the recorded evidence gaps. The user also confirmed that the model
must not use any computer-control plugin during acceptance. The corrected Setup
was not installed or operated in this continuation; every corrected-candidate
installed row above remains `not run`. The configured patch regression profile
was not run and its 17 unselected cases remain `not run`. Neither omission is
recorded as a pass. The technical local acceptance state remains incomplete.

The 50-case `release-0.7.5` ledger and its 17 unselected cases refer only to
pytest node IDs. None of the client or installed checks above is included in
that version-update test quantity; each has its own candidate-specific status.

This decision authorizes continued development only. It does not authorize a
personal-data transition or establish independent public acceptance, content
review or W4 readiness. If installed acceptance is requested later, it must use
candidate-specific developer-operated evidence under the project rules.
