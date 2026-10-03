# 0.8.3 Development Record

## Identity and event classification

- Application: `0.8.3`
- Database schema: `24`
- Catalog: `070-illustrated-3`
- Plan/evidence contract: `4`
- Events: development update, application-version rotation and requested local
  installer candidate. GitHub Release distribution is not yet performed.

## Scope

This emergency update replaces the browser-first updater action with an
application-managed background download. The application accepts only the exact
stable GitHub Setup asset already validated during release discovery, writes it
outside the data root, checks its declared size and SHA-256, then starts Setup
and exits. Browser download remains available as a fallback.

The installer now uses Inno Setup's stable-AppId previous-directory selection
before the default per-user path. Existing helper checks still gate every
selected path and overwrite. No locator, database, catalog content or wire
contract changes are included.

## Diagnosis

The 0.8.2 behavior matched its then-current browser-only product contract. The
installer already recorded the old location under the stable AppId, but disabled
Inno's built-in previous-directory selection and depended on a code-derived
default. The observed machine has the prior location registered as
`D:\Program Files\TrainingFeedback`; this diagnosis inspected only the known
program registration and install receipt, not any training data root.

## Verification and candidate

The concrete startup risk was that the required `ui.release_updates` module now
imports additional Qt network/process APIs and constructs new coordinator
state during main-window startup. Exactly one existing isolated scenario was
selected under scope `v083-emergency-update`:

- First execution with the ambient Python 3.13 interpreter failed before the
  changed path because that environment lacked the required `jsonschema`
  package. This was not an application result.
- The same node was rerun once with the repository environment (Python 3.12.14)
  and passed: [startup test](../../../tests/test_update_startup.py), node
  `test_update_coordinator_does_not_block_main_window_startup` (`1 passed` in
  0.36 s). No additional application scenario was run.

Static verification passed for the changed Python files with Ruff,
`packaging/check_docs.py` passed for 64 Markdown files, and `git diff --check`
reported no whitespace errors (only checkout line-ending notices). PySide6's
type stub was inspected to confirm that `QProcess.startDetached()` returns a
`(bool, pid)` tuple; the launch result is unpacked before deciding whether to
exit the application.

The release candidate was rebuilt from clean implementation commit `d157174`
on 2026-10-03 with Python 3.12.14,
PySide6 6.11.2, PyInstaller 6.22.2 and Inno Setup 6.7.3. Inno compilation
succeeded after one earlier compile failure exposed and removed an unsupported
Pascal Script `HKEY` annotation. A subsequent successful build was discarded
after static review found the `startDetached()` return-value issue; the identity
below belongs only to the clean rebuilt candidate:

- Setup: `dist/installer/TrainingFeedback-0.8.3-Setup.exe`
- Bytes: `85,661,990`
- SHA-256: `a7dcb23536c43422355d6113df926fef2f05cbeaaea383310e9630f50a381009`
- Signature: unsigned (`NotSigned`)
- Payload files: `298`
- Payload executable SHA-256: `3e8c66147310fd9455fea512e5a87fd24de9b07cc20e1577717b2f2c87c2f5b0`
- Source revision recorded by the builder:
  `d157174e5bd3246c084b96410b986be356dc8bc3`
- Source dirty: `false`.
- Manifests: [installer](installer-build-manifest.json) and
  [payload](payload-build-manifest.json).

Download, digest-failure handling, Setup launch, directory-page selection,
overwrite installation and all other client behavior were not run. No GUI
automation or scripted client operation was used. Those unobserved behaviors
are not passes and are not outstanding bulk-test requirements under the current
personal-use policy. Subsequent GitHub distribution is recorded separately in
[the public release record](github-release-2026-10-03.md) and does not change
these verification limits.
