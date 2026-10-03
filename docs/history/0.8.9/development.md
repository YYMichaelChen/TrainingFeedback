# 0.8.9 Development And Candidate Record

## Identity and event classification

- Application: `0.8.9`
- Database schema: `24`
- Catalog: `070-illustrated-3`
- Plan/evidence contract: `4`
- Events: action-library construction fix, application-version rotation, local
  installer candidate and GitHub Release distribution.

## Scope and diagnosis

User feedback on the installed 0.8.8 client showed that selecting 动作库 reached
the contained error page with `KeyError: 'images_tab'`. The action-library page
constructs two tabs using `LIBRARY_TEXT["images_tab"]`, while the 0.8.2 change
that introduced those reads placed the label only in `GROUP_PLAN_TEXT`.
Construction therefore failed before catalog or user-data access.

`LIBRARY_TEXT` now contains `images_tab: 动作示意图`, matching both consumers.
No loading, image, persistence or business rule changed. Schema 24, catalog
`070-illustrated-3`, contract 4, user text semantics and import compatibility
are unchanged.

## Verification

The change adds one dictionary entry and has no concrete causal path to failure
of the application itself to open. Under the current startup-only policy,
application tests were **0** and manual checks were **0**. The two exact
action-library consumers and their label definition were inspected. Ruff passed
for the changed Python file, `packaging/check_docs.py` passed, and
`git diff --check` reported no whitespace errors beyond checkout line-ending
notices.

Action-library navigation, dialog construction, catalog loading and
installed-client behavior were not run and are not passes. No GUI automation,
scripted client interaction or real user root was used. The user's next normal
use remains the feedback channel.

## Candidate

The clean implementation commit `eec23905bdb70240fc904335531fea44623a9e7c`
was built on 2026-10-03 with Python 3.12.14 AMD64, PySide6 6.11.2,
PyInstaller 6.22.2, hooks 2026.7 and Inno Setup 6.7.3.

- Setup: `dist/installer/TrainingFeedback-0.8.9-Setup.exe`
- Bytes: `85,670,039`
- SHA-256: `e0030b4c15be767b46fafb7e0da652bd27ce647207779eb2e5163a873accd722`
- Signature: unsigned (`NotSigned`); payload EXE also `NotSigned`
- Payload files: `298`
- Payload executable SHA-256:
  `0bcecd5d9aefce0f53798cb4b339aa02c66eb638b3adf040147d73ca6eea78e4`
- Source dirty: `false`
- Icon SHA-256: `3db199c1a7b7289fc4dbea91653952486431fe7072f7eb16ea7d90e51b99a65c`
  for the packaged runtime copy
- Manifests: [installer](installer-build-manifest.json) and
  [payload](payload-build-manifest.json)

The build verified the catalog and required packaged schema, contract and icon
resources, and found no user data in the payload. Building and manifest
inspection do not certify action-library navigation, dialog construction,
catalog loading or installed behavior.

GitHub distribution remains separate from formal compatibility, public support,
external content review, personal-data transition or W4.
