# 0.8.4 Development And Candidate Record

## Identity and event classification

- Application: `0.8.4`
- Database schema: `24`
- Catalog: `070-illustrated-3`
- Plan/evidence contract: `4`
- Events: development update, application-version rotation and requested local
  installer candidate. GitHub Release distribution is recorded separately.

## Scope and diagnosis

This update applies the owned dumbbell icon explicitly to QApplication, the
main window and the parentless data-root chooser. The executable icon and the
runtime icon remain separate required copies of the same source bytes.

The prior action-library page was constructed and synchronously refreshed
inside the navigation signal before it was inserted into the stacked widget.
During a slow or failed first browse, navigation could therefore select 动作库
while the prior page remained visible; an exception raised through the Qt slot
also had no page-local feedback. The progressive page now schedules its first
refresh after construction, immediately becomes the selected page, and contains
read failures in a visible message without writing or repairing user data.

Ordinary plan-page labels now say `导入计划文件`, `导出计划资料` and
`计划资料已导出到：`. The contract number appears only in actionable format
errors. `training_feedback.plan` and `training_feedback.evidence` remain format
version 4; database, catalog, import compatibility and user text are unchanged.

The original [user screenshot](evidence/user-ui-feedback-2026-10-03.png) is
retained as defect input. It demonstrates the generic title-bar icon, exposed
v4 wording and old-page retention, but does not establish the cause or certify
this candidate.

## Verification

Concrete startup risk: the startup entry now imports a new icon helper and
MainWindow requires the runtime ICO during construction. A missing module,
invalid resource path or null icon could prevent the application from opening.
Exactly one isolated scenario was selected under scope
`v0.8.4-ui-reliability`:

- `test_required_application_icon_is_loaded_and_assigned_to_main_window`
  created a synthetic root, loaded the application icon and constructed the
  main window. Result: **1 passed in 0.36 s**, with no rerun.

Ruff passed for the changed Python files, `packaging/check_docs.py` passed for
66 Markdown files, and `git diff --check` reported no whitespace errors beyond
checkout line-ending notices. No other pytest node, script scenario, GUI
automation or real user root was used.

Action-library navigation/loading, plan wording, visible Windows title bars,
dialogs, imports/exports, installation and overwrite behavior were not run and
are not passes. Manual checks: **0**. These unrun checks are not outstanding
bulk-test requirements under the current personal-use policy.

## Candidate

The clean implementation commit `768ef9e614cac1022ed09807bcd2fae65ec5b2b2`
was built on 2026-10-03 with Python 3.12.14 AMD64, PySide6 6.11.2,
PyInstaller 6.22.2, hooks 2026.7 and Inno Setup 6.7.3.

- Setup: `dist/installer/TrainingFeedback-0.8.4-Setup.exe`
- Bytes: `85,662,349`
- SHA-256: `832e958df99c3707d85065f715787d4035d69f85fe1830ec8f4116c47c8497b7`
- Signature: unsigned (`NotSigned`); payload EXE also `NotSigned`
- Payload files: `298`
- Payload executable SHA-256:
  `a6e94653b69415b352e5045c378840c0c9f42853dc29536ef1bcb674ad35a7c6`
- Source dirty: `false`
- Icon SHA-256: `3db199c1a7b7289fc4dbea91653952486431fe7072f7eb16ea7d90e51b99a65c`
  for `icon/`, source runtime and packaged runtime copies
- Manifests: [installer](installer-build-manifest.json) and
  [payload](payload-build-manifest.json)

The build verified the catalog and required packaged schema, contract and icon
resources, and found no user data in the payload. Building and manifest
inspection do not certify installed or visible client behavior. Subsequent
GitHub distribution does not declare a formal compatibility baseline, public
support, external content review, personal-data transition or W4.
