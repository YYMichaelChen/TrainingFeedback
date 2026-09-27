# 0.7.5 Local Candidate

Candidate status: **installed; local acceptance incomplete**. These results
identify the local candidate and distinguish completed checks from checks that
could not be completed in this environment. They do not certify a public
release or personal-use readiness.

## Source and artifacts

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

## Checks

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
