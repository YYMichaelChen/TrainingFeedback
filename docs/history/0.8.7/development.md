# 0.8.7 Development And Candidate Record

## Identity and event classification

- Application: `0.8.7`
- Database schema: `24`
- Catalog: `070-illustrated-3`
- Plan/evidence contract: `4`
- Events: navigation reliability development update, application-version
  rotation, local installer candidate and GitHub Release distribution.

## Scope and diagnosis

User feedback on a clean-installed 0.8.6: selecting 动作库 in the navigation
highlights the entry, but the previously visible page remains on screen with no
message. The stacked-widget switch happens only after the target page is
constructed inside the navigation slot, so any exception raised during page
construction — including the first lazy import of the page module — escapes
the slot silently in the windowed client and permanently diverges the
navigation selection from the visible page. The 0.8.4 progressive loading
change contained only refresh-time failures, not construction-time ones. The
exact construction-time trigger on the user's machine is not observable from
code; the contained error page is the feedback channel for it.

`MainWindow._show_page` now contains page creation: a factory exception
substitutes a visible error page carrying the page name and the error text
(selectable for feedback), the stack still switches so the visible page always
matches the navigation selection, and the index stays unbuilt so the next
entry retries creation. The containment path reads and writes no user data.
The library page schedules its first progressive refresh from its first
`paintEvent` instead of a zero-interval timer, so the loading state paints
before heavy reading begins. Normal creation, per-card progressive loading,
refresh and cancellation are unchanged. Schema 24, catalog
`070-illustrated-3`, contract 4, user text semantics and import compatibility
are unchanged.

## Verification

Concrete startup risk: `main_window.py` and `labels.py` are imported and the
main window is constructed on the startup path; an import, name or
construction error in this change could prevent the application from opening.
Exactly one existing isolated scenario was selected under scope
`v0.8.7-navigation-containment`:

- `test_required_application_icon_is_loaded_and_assigned_to_main_window`
  created a synthetic root and constructed the main window. The first attempt
  used the system Python 3.13 interpreter, which lacks the project's
  `jsonschema` dependency and failed during collection-phase import before
  reaching the change; the same node rerun with the repository interpreter
  (Python 3.12.14) gave **1 passed in 0.35 s**. No other rerun occurred.

Ruff passed for the changed Python files, `packaging/check_docs.py` passed,
and `git diff --check` reported no whitespace errors beyond checkout
line-ending notices.

Navigation switching, the substituted error page, library loading behavior and
installed-client behavior were not run and are not passes. No other pytest
node, script scenario, GUI automation or real user root was used. Manual
checks: **0**. The next user report through the contained error message
remains the feedback channel.

## Candidate

The clean implementation commit `5bf3f694780b425cb3b6ea0407aad9304b637b89`
was built on 2026-10-03 with Python 3.12.14 AMD64, PySide6 6.11.2,
PyInstaller 6.22.2, hooks 2026.7 and Inno Setup 6.7.3.

- Setup: `dist/installer/TrainingFeedback-0.8.7-Setup.exe`
- Bytes: `85,672,077`
- SHA-256: `48c4dae577a17428760c135c5713f1e87608cbc9e0b89b0ff5b4e2f955a62ee0`
- Signature: unsigned (`NotSigned`); payload EXE also `NotSigned`
- Payload files: `298`
- Payload executable SHA-256:
  `8778fdde7f0a4c2fa389549844b834f312a424e8f08bf9bac7d482accda5b2d8`
- Source dirty: `false`
- Icon SHA-256: `3db199c1a7b7289fc4dbea91653952486431fe7072f7eb16ea7d90e51b99a65c`
  for `icon/`, source runtime and packaged runtime copies
- Manifests: [installer](installer-build-manifest.json) and
  [payload](payload-build-manifest.json)

The build verified the catalog and required packaged schema, contract and icon
resources, and found no user data in the payload. Building and manifest
inspection do not certify navigation behavior, the contained error page or
installed behavior. GitHub distribution remains a separate event and does not
declare formal compatibility, public support, external content review,
personal-data transition or W4.
