# 0.8.0 Local Candidate — 2026-09-30

Historical exact candidate. The current deliverable is the
[October 2 rebuilt candidate](local-candidate-2026-10-02.md); this record's hashes
and unrun checks remain attached only to the September 30 build.

**Prepared for manual acceptance; installed and client checks are not run.**
This is an unsigned local candidate, not a completed local/public release,
formal-release declaration, external content review, W4 or personal-use baseline.

## Exact identity

| Item | Value |
| --- | --- |
| Application / schema / catalog / wire | 0.8.0 / 23 / 070-illustrated-3 / 3 |
| Build source | cdb0972022efa833179172ba423684a0369d6b06 |
| Source dirty at build | false |
| Build completed UTC | 2026-09-30T09:20:56Z |
| Build duration | 60.62 seconds (PyInstaller, verification, Inno and manifests) |
| Payload | 296 files, 176,808,298 bytes (168.62 MiB) |
| Setup | 85,603,202 bytes (81.64 MiB) |
| Signing | NotSigned |
| Toolchain | Python 3.12.14 AMD64, PySide6 6.11.2, PyInstaller 6.22.2, hooks 2026.7, Inno 6.7.3 |

The source commit follows the implementation snapshot `17c3887` and includes the
directory-write sharing safety fix. Later evidence-only commits do not replace
this build's source identity or installer bytes. No installer/client was executed
by the agent. No public artifact was uploaded or release declared.

| File | SHA-256 |
| --- | --- |
| TrainingFeedback.exe | 2ad35abd0daf49ffff6eea76aee7ee8b6d5434a2a0fd03960af3c55a24a9eb5c |
| TrainingFeedback-0.8.0-Setup.exe | b5b67479dfd0bdca1ae763908ead7651bbf9b2dfbfc8111d8fadd4f455186cf4 |
| Payload build manifest | 82306950df306869eb04121e57ce3bfe5c2e9b1d51b16796c81a4eb639ef62f4 |
| Setup build manifest | e97707f5173115743376c3798bd0d016f3e9aa7b0f6e60cd6df32b7742bded9b |
| Program ownership manifest | 09ff6e3988f52a71e384a8b4a93f306d59c7020f4a30467427ea1a6bf23d0023 |

Deliverable paths in this checkout:

- `dist/TrainingFeedback/TrainingFeedback.exe` and its complete directory payload.
- `dist/TrainingFeedback.build-manifest.json`.
- `dist/installer/TrainingFeedback-0.8.0-Setup.exe`.
- `dist/installer/TrainingFeedback-0.8.0-Setup.build-manifest.json`.

Tracked evidence copies: [payload manifest](payload-build-manifest.json),
[installer manifest](installer-build-manifest.json), [audit](candidate-audit.json).
The complete payload is required; the EXE alone is not a portable application.

## Actual verification

The single `release-0.8.0` minor scope passed **98 unique cases out of a 100 cap**
in 28.37 s. After the directory-handle sharing fix, its affected 28 existing cases
passed again in 2.48 s under the same scope (still 98 unique). Unaffected earlier
checks are explicitly reused. [Risk selection and expanded nodes](../../releases/0.8.0/release-verification.md)
were recorded before first execution. No GUI clicks/keys were automated.

Ruff, documentation consistency, diff checks and Planscope doctor passed.
The final PyInstaller and Inno build succeeded with a clean source revision.
Static inspection compared every payload path, size and SHA-256, rejected
unexpected/missing files, compared the installer hash and embedded payload
manifest, and verified all program-ownership manifest entries. The packaged
catalog and 36 image assets verified; required runtime/schema/contract files and
absence of user databases/locators were checked by the build script.

The historical payload baseline was 176,740,757 bytes; final payload is 67,541
bytes larger, mostly helper code/ownership metadata. Source illustration
deduplication removed 48.05 MiB from the checkout, **not** from the payload; do not
combine these two inventories into a misleading installer-slimming claim.

Service measurements show the large synthetic library hot browse p95 improved
853.58→117.80 ms and save 101.96→43.90 ms. Cold decode remains 853.28 ms, its
30% improvement target is unmet; no client 200 ms pause certificate is claimed.
See [measurement evidence](../../releases/0.8.0/slimming-and-performance.md).

## Open acceptance

| Gate | Status |
| --- | --- |
| Installer pages, actual helper orchestration, directory/shortcut behavior | not run |
| Default retention, cancel, confirmed current-root deletion and reinstall | not run |
| Installed new root, restart, switch, current/future safety and representative training | not run |
| Startup/render/search, populated history, large backups, 200 ms client response | not run |
| Public independent-machine acceptance | not run; no public request |
| Expert review, personal transition and W4 | not established |

The developer must follow [manual acceptance](../../releases/0.8.0/manual-acceptance.md)
with isolated profiles and synthetic roots. Record actual observations against
these exact hashes. Remaining response/cold-decode work and manual gates keep
Planscope v0.8.0 active; no completed-release claim or closeout is made.
