# 0.8.10 Development And Candidate Record

## Identity and event classification

- Application: `0.8.10`
- Database schema: `24`
- Catalog: `070-illustrated-3`
- Plan/evidence contract: `4`
- Events: user-feedback development update, application-version rotation,
  local installer candidate and GitHub Release distribution.

## Scope and diagnosis

The user supplied screenshots from the installed 0.8.9 client showing rows of
action cards without stable alignment and a small illustration centered far
away from its left-aligned caption. `IllustrationLabel` incorrectly scaled its
own rectangular area into the target before scaling the square source, which
made the available height unnecessarily constrain the result. It now calculates
from the source image's device-independent size, advertises height-for-width
sizing and retains a useful minimum. The image/caption pair is top-centered.
Action cards now declare uniform sizes and each item uses the view's exact grid
size.

The same feedback reports that update download and handoff still wait until the
user manually closes the application, after which Setup opens automatically.
The detached launcher is therefore functioning. The prior hard-exit fallback
was a Qt timer, so it could fail together with a stalled or prematurely
unwinding Qt event loop. The verified handoff now actively closes all visible
windows and requests application quit, while a daemon `threading.Timer` arms a
10-second `os._exit` fallback independent of Qt event processing.

No schema, catalog, wire contract, user text, user fact or data-root behavior
changed.

## Verification

Concrete startup risk: `release_updates.py` is imported and the coordinator is
constructed on the startup path; the new standard-library import, type annotation
or helper definition could prevent application opening if invalid. Exactly one
existing isolated scenario was selected under scope
`2026-10-03-image-updater-feedback`:

- `test_update_coordinator_does_not_block_main_window_startup` created an
  isolated synthetic data root and update temporary root, constructed the
  coordinator without network and opened the main window. Result: **1 passed in
  1.11 s**, with no rerun.

Ruff and Python compilation passed for the three changed UI files, and
`git diff --check` reported no whitespace errors beyond checkout line-ending
notices. Documentation consistency will be recorded with the candidate.

No other pytest node, script scenario, GUI automation, real user root or client
operation was used. Illustration layout, update download, handoff, application
exit, watchdog, installer launch, overwrite installation and installed-client
behavior were not run and are not passes. Manual checks: **0**.

## Candidate

Candidate build and exact artifact identity are pending.

GitHub distribution does not declare a formal compatibility baseline, public
support, external content review, personal-data transition or W4.
