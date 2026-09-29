# 0.7.7 Local Candidate And Installed Acceptance

## Candidate identity

- Source commit: `831f7edf2f80a062f5919223b10cada4037f577b`; clean at build.
- Application `0.7.7`, schema `23`, catalog `070-illustrated-3`, plan/evidence
  wire contracts v3. Python `3.12.14` AMD64, PySide6 `6.11.2`, PyInstaller
  `6.22.2`, Inno Setup `6.7.3` on Windows 11.
- Directory payload: `dist/TrainingFeedback/`; 295 files. The complete file
  inventory, sizes and SHA-256 values match the adjacent build manifest; no
  missing, extra or mismatched files. The bundled catalog verified with 36
  illustrations. `schema23.sql` and `plan-v3.schema.json` are present;
  retired `schema22.sql` is absent. The build script found no locator or user
  database in the payload.
- Build manifest SHA-256:
  `9d7deb4651547ecf217618c3c914a4e2564d179935e633f47a2b500fb990271b`.
- EXE SHA-256:
  `9da31103b7e103a8bca18506e60cca1f227bddfd72627b5cd3e8cc18bf5a3b08`.
- Setup: `dist/installer/TrainingFeedback-0.7.7-Setup.exe`; SHA-256
  `b3b8573274bb95b0b71056a0504dd3e5a5de5493a21f58484906e425ae093279`.
  Its installer manifest records the same hash and includes the payload build
  manifest. Installer manifest SHA-256:
  `bc34c6958d91dd04ca53f9972ee1bd0eaeff72daa4f1868bc61295621bc3e512`.
- Authenticode: `NotSigned` (local candidate; no public release claim).

An earlier clean build from commit `154fce4` passed static manifest inspection,
then was superseded before any installed client check by the error-handling
correction in `831f7ed`. Its checks do not certify this candidate.

## Developer-operated installed checks

The developer must manually install and operate the client using an isolated
`%LOCALAPPDATA%` profile/locator and synthetic roots. Record account, actual
paths, input, observed result and evidence for each row against the Setup hash
above. No automated UI operation substitutes for these checks.

| Check | Expected result | Status | Actual evidence |
| --- | --- | --- | --- |
| Install and payload | Ordinary-user install succeeds; installed payload matches manifest and prior isolated root/locator is unchanged | not run | Awaiting developer record |
| Fresh cancel | Cancel creates no locator or child | not run | Awaiting developer record |
| Create form | Redirected Documents suggestion, parent/name/path preview, invalid names; no pre-confirmation writes | not run | Awaiting developer record |
| Child states | Missing and empty child succeed; valid root requires explicit open; occupied/incomplete/future/expired refuse unchanged | not run | Awaiting developer record |
| New root | Chinese/space name; complete built-in catalog and assets; no invented personal facts | not run | Awaiting developer record |
| Settings and direct open | Create from Settings, open supported existing and copied-backup roots directly; backup destination remains a complete-root selection | not run | Awaiting developer record |
| Restart and compatibility | Isolated locator/restart persists; 0.7.5/0.7.6 schema-23 roots reopen, pending cleanup completes, schema-22 root refuses read-only | not run | Awaiting developer record |

Local installed acceptance remains incomplete while any required row is
`not run`. Independent public acceptance, content review, W4 and personal-use
readiness are separate and have no result from this candidate.
