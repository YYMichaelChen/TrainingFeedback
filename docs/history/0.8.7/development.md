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

The clean implementation commit and candidate identity will be recorded here
after the build, together with the installer and payload manifests.

GitHub distribution remains a separate event and does not declare formal
compatibility, public support, external content review, personal-data
transition or W4.
