# Version History

This is the single human-readable implementation identity map and index of
candidate-specific evidence. Product retention and compatibility rules are
owned by [development plan §13](../development-plan.md#13-version-retention-and-development-data-policy);
the [development workflow](../development-workflow.md) owns version rotation.

## Current implementation

- Application: **0.8.18**
- Database schema: **24**
- Catalog: **070-illustrated-3**
- Current plan/evidence contract: **4**
- GitHub distribution: **v0.8.18**
- Formal compatibility baseline declared: **no**
- Current development version: [0.8.18](../releases/0.8.18/design.md)

The [QHD compact-interface source follow-up](0.8.14/compact-interface-2026-10-08.md)
adds a 16:9 default window (2560×1440 on 4K) and independent action frames without changing these
data identities. It has one isolated startup scenario executed twice and no client
observation. The [0.8.15 development record](0.8.15/development.md) carries it into
the newly authorized patch delivery; the existing v0.8.14 Setup does not contain it.

The [225% scaling layout source follow-up](0.8.15/layout-follow-up-2026-10-09.md)
reserves full training-button widths and centers gallery captions while filling
the gallery width. Application/data identities remain unchanged; no application
or manual tests were run. The published v0.8.15 Setup does not contain this follow-up.
The user authorized submission and distribution; [0.8.16 development](0.8.16/development.md)
carries this fix into a patch version with unchanged data identities.

The [plan-editor width follow-up](../designs/plan-interface-scaling.md#2026-10-09-编辑区宽度源码跟进)
keeps short columns compact and horizontal overflow inside the table, improves
scrollbar visibility and clarifies group-order/rest labels. The user authorized
GitHub distribution; [0.8.18 development](0.8.18/development.md) and its
[release record](0.8.18/github-release-2026-10-10.md) identify the exact clean Setup.

The [plan-editor source follow-up](0.8.16/plan-editor-follow-up-2026-10-09.md)
addresses disappearing rows after drag ordering and opens editable prescriptions by
default. It retains application/data identities and has no application or manual
tests. The published v0.8.16 Setup does not contain this source follow-up.
The user authorized submission and distribution; [0.8.17 development](0.8.17/development.md)
carries this fix into a patch version with unchanged data identities.

The user has suspended old-version compatibility obligations until an explicit
formal-release declaration. Older rows below are historical records, not a
current support promise.

## Version map

| Application | Database schema | Role | Candidate status |
| --- | ---: | --- | --- |
| 0.8.18 | 24 | Compact prescription columns, table-local horizontal scrolling and clear plan-editor labels | GitHub Release `v0.8.18`; clean Setup from `905b534`; SHA-256 `774751f0392362cf200d19cb58aab6ae9b039407903997734944711a9533b6d7`; unsigned; application and manual tests 0 |
| 0.8.17 | 24 | Plan drag ordering and default inline prescription editing | GitHub Release `v0.8.17`; clean Setup from `943bf42`; SHA-256 `c83b8dc41c0efcf8f79ef75e9d616c73ec6856bf19cd4d22d27ccacbfafda233`; unsigned; application and manual tests 0 |
| 0.8.16 | 24 | Full training-button widths, centered gallery captions and evenly distributed gallery columns | GitHub Release `v0.8.16`; clean Setup from `e12b5db`; SHA-256 `c26ff9d174bc1de6677feb293d52954339c63db21f889cbe1bccc27ba53b149c`; unsigned; application and manual tests 0 |
| 0.8.15 | 24 | Compact 16:9 default window, responsive page structures and independent measured action frames | GitHub Release `v0.8.15`; clean Setup from `22acd71`; SHA-256 `4aa81c4c6e517a8e1958ef36c4ce59fb96da520d558d707cae47025b6e1484bf`; unsigned; no client observation |
| 0.8.14 | 24 | Font-relative interface scale and responsive plan/guidance editing | GitHub Release `v0.8.14`; clean Setup from `b09b611`; SHA-256 `26a5a403975e2dab7ce769e048abae04fb33faba7171579357e84e6ebca4169e`; unsigned; no client observation |
| 0.8.13 | 24 | Continuous plan editing/execution, exact-version guidance in plan details and field-specific numeric input handling | GitHub Release `v0.8.13`; clean Setup from `531a317`; SHA-256 `66ec6977bc87af5ef805b35f48b3a28cc46e407051bbc1649571ca9bc66e0b5b`; unsigned; no client observation |
| 0.8.12 | 24 | Updater exit follow-up: external watchdog bound to the exact application process, readiness acknowledgement and confirmed exit before Setup | GitHub Release `v0.8.12`; clean Setup from `8a3ae60`; SHA-256 `22fc750d5773fd9442ee1e29e7644747544786639101c72d0e9d0800d33235f6`; unsigned |
| 0.8.11 | 24 | Action reading redesign: responsive illustration/guidance panels, grouped guidance, zoom viewer and exact-content operations menu | GitHub Release `v0.8.11`; SHA-256 `baa1e40c153c4ae69ca99e5f53b5d6019cd31481db5515777d511f4911549519`; unsigned |
| 0.8.10 | 24 | Current illustration-layout and updater-exit correction: align stable cards and captions, scale previews from source proportions, and use an event-loop-independent exit fallback | GitHub Release `v0.8.10`; Setup SHA-256 `9846aedc52073b9c85e9f52c7f3cafe2450e60a6c38a103368bb8c34c2b1580d`; unsigned |
| 0.8.9 | 24 | Current action-library construction fix: restore the missing illustration-tab label used by the page and review dialog | GitHub Release `v0.8.9`; Setup SHA-256 `e0030b4c15be767b46fafb7e0da652bd27ce647207779eb2e5163a873accd722`; unsigned |
| 0.8.8 | 24 | Current updater exit-hardening update: make the post-handoff application exit unskippable with a contained emit and a hard-exit watchdog | GitHub Release `v0.8.8`; Setup SHA-256 `bfbf1789b53d10f6aada0875c7395dcaf0493868a8a8f03b89b5119632c17207`; unsigned |
| 0.8.7 | 24 | Current navigation reliability update: contain page-creation failure into a visible retryable message and paint the library loading state before its first read | GitHub Release `v0.8.7`; Setup SHA-256 `48c4dae577a17428760c135c5713f1e87608cbc9e0b89b0ff5b4e2f955a62ee0`; unsigned |
| 0.8.6 | 24 | Current updater cleanup follow-up: remove verified Setup temporaries after use and safely recover owned leftovers | GitHub Release `v0.8.6`; Setup SHA-256 `06120b97244ab24a745a429617e04abdbe50f7b0057086cf050f64158b89e61c`; unsigned |
| 0.8.5 | 24 | Current emergency updater correction: show complete download progress and exit before Setup starts | GitHub Release `v0.8.5`; Setup SHA-256 `37658f63ce49535f73ac56fef7d186495982aeecd38e5d559afe3b26cd5dc9e0`; unsigned |
| 0.8.4 | 24 | Current UI reliability update: restore owned window icons, make action-library loading visible and clarify plan-file wording | GitHub Release `v0.8.4`; Setup SHA-256 `832e958df99c3707d85065f715787d4035d69f85fe1830ec8f4116c47c8497b7`; unsigned |
| 0.8.3 | 24 | Current emergency update: verified in-app Setup download and previous-directory installer reuse | GitHub Release `v0.8.3`; Setup SHA-256 `a7dcb23536c43422355d6113df926fef2f05cbeaaea383310e9630f50a381009`; unsigned |
| 0.8.2 | 24 | Current personal-use update: remove training-day names, improve illustration views and set the application icon | GitHub Release `v0.8.2`; Setup SHA-256 `c04ba484d6d6cbf9a7c3347a0728ad4859e11a51cb131641465b5c18ab568d97`; unsigned |
| 0.8.1 | 23 | Previous personal-use update: [GitHub update discovery](../releases/0.8.1/design.md) | GitHub Release `v0.8.1`; Setup SHA-256 `5e9299066ad13c6ef78a2e6e8fb07b013595b57f240c64be54f388c8a219b0cf`; unsigned |
| 0.8.0 | 23 | Historical personal-use update: [installation, cleanup and response work](0.8.0/development.md) | GitHub Release `v0.8.0`; Setup SHA-256 `49de95af46f2ae0f20f36a7bbb1f4e6318a418cf9b117370ee130ced1b1dcdad`; unsigned |
| 0.7.8 | 23 | Historical development version: [documentation and knowledge governance](0.7.8/development.md) | No installer candidate; documentation/identity verification only |
| 0.7.7 | 23 | Historical development version: [new-root creation](0.7.7/development.md) | [User-approved partial closeout; full installed acceptance incomplete](0.7.7/local-candidate.md#2026-09-29-部分验收收尾) |
| 0.7.6 | 23 | Historical development version: [documentation ownership and routing](0.7.6/development.md) | No installer candidate; development verification only |
| 0.7.5 | 23 | Historical development version: [plan/reset development](0.7.5/development.md) | [User-approved closeout; installed acceptance incomplete](0.7.5/local-candidate.md#2026-09-29-final-version-closeout) |

Intermediate schemas and retired development versions retain their original
identities in Git history; they do not imply application releases or support.

## Candidate status

The [0.8.17 development record](0.8.17/development.md) records the requested plan-editor
delivery. No concrete startup risk is introduced; application and manual tests remain
zero. A clean Setup from `943bf42` has matching local hash and build manifests;
the [public release record](0.8.17/github-release-2026-10-09.md) records stable/latest
v0.8.17, its unique uploaded Setup, and matching unauthenticated public response.

The [0.8.16 development record](0.8.16/development.md) carries the default-window
layout follow-up into the user's explicitly requested GitHub delivery. Application
and manual tests remain zero; no client layout result is claimed. The published
v0.8.15 Setup does not contain this fix.
The [public release record](0.8.16/github-release-2026-10-09.md) identifies the
unique Setup built from `e12b5db` and its matching unauthenticated latest response.

The [0.8.15 development record](0.8.15/development.md) records the user's
2026-10-09 submission and GitHub distribution request. The source update has
one isolated startup construction scenario passed on two executions; packaging
and distribution add no application or manual checks. The clean Setup is built
from `22acd71`; candidate manifests retain its exact identity. Client layout
remains unobserved. The [public release record](0.8.15/github-release-2026-10-09.md)
identifies the unique uploaded Setup and matching unauthenticated latest response.

The [0.8.14 development record](0.8.14/development.md) carries the
[2026-10-08 plan-interface source follow-up](0.8.13/plan-interface-2026-10-08.md)
into a patch version after the user's explicit submission/distribution request.
The published v0.8.13 Setup does not include that change. One isolated
theme/main-window startup construction check passed during source development;
client layout and functional behavior remain unobserved. The clean Setup was built
from `b09b611`; retained manifests identify the candidate. The
[public release record](0.8.14/github-release-2026-10-08.md) preserves its unique
uploaded Setup, GitHub digest and matching public latest response. Version rotation,
packaging and distribution add no application/manual checks.

The [0.8.12 development record](0.8.12/development.md) carries the
[2026-10-06 updater follow-up](0.8.11/updater-follow-up-2026-10-06.md)
into a new application version. The distributed v0.8.11 asset below does not
include that fix. The clean 0.8.12 candidate was built from `8a3ae60`; its
installer/payload manifests are retained beside the development record.
The [public release record](0.8.12/github-release-2026-10-07.md) identifies the
matching uploaded asset for stable `v0.8.12` and its public latest response.
The prior single isolated startup result does not certify updater exit,
launcher or installer behavior.

The [0.8.11 development record](0.8.11/development.md) records the reading
redesign, limited source verification and the clean candidate built from
`52c9fce`. The [public release record](0.8.11/github-release-2026-10-04.md)
preserves the matching uploaded asset identity for stable `v0.8.11`.
Earlier candidate results do not
certify the new reading surfaces or their client behavior.

The [0.8.10 development record](0.8.10/development.md) identifies the clean
candidate built from application source `5f37d83`. Its payload and installer
manifests are tracked beside that record. The identified Setup was distributed
unchanged through GitHub Release `v0.8.10`; the
[public release record](0.8.10/github-release-2026-10-04.md) preserves its
GitHub-reported identity. One isolated startup construction scenario passed;
visual layout, update handoff, process exit, installer launch and
installed-client behavior remain unobserved and are not passes.

The [0.8.9 development record](0.8.9/development.md) identifies the clean
candidate built from application source `eec2390`. Its payload and installer
manifests are tracked beside that record. The identified Setup was distributed
unchanged through GitHub Release `v0.8.9`; the
[public release record](0.8.9/github-release-2026-10-03.md) preserves its
GitHub-reported identity. Application tests and manual checks were zero.
Action-library navigation, dialog construction, catalog loading and
installed-client behavior were not run and are not passes.

The [0.8.8 development record](0.8.8/development.md) identifies the clean
candidate built from application source `13e9954`. Its payload and installer
manifests are tracked beside that record. The identified Setup was distributed
unchanged through GitHub Release `v0.8.8`; the
[public release record](0.8.8/github-release-2026-10-03.md) preserves its
GitHub-reported identity. One isolated startup construction check passed.
Download, handoff, exit, watchdog, launcher and installed-client behavior were
not run and are not passes.

The [0.8.7 development record](0.8.7/development.md) identifies the clean
candidate built from application source `5bf3f69`. Its payload and installer
manifests are tracked beside that record. The identified Setup was distributed
unchanged through GitHub Release `v0.8.7`; the
[public release record](0.8.7/github-release-2026-10-03.md) preserves its
GitHub-reported identity. One isolated startup construction check passed.
Navigation switching, the substituted error page, library loading and
installed-client behavior were not run and are not passes.

The [0.8.6 development record](0.8.6/development.md) identifies the clean
candidate built from application source `ccb47bd`. Its payload and installer
manifests are tracked beside that record. The identified Setup was distributed
unchanged through GitHub Release `v0.8.6`; the
[public release record](0.8.6/github-release-2026-10-03.md) preserves its
GitHub-reported identity. One isolated startup construction check passed.
Stale-directory selection/deletion, launcher waiting, Setup execution,
post-install cleanup and installed-client behavior were not run and are not
passes.

The [0.8.5 development record](0.8.5/development.md) identifies the clean
candidate built from application source `749b6a3`. Its payload and installer
manifests are tracked beside that record. The identified Setup was distributed
unchanged through GitHub Release `v0.8.5`; the
[public release record](0.8.5/github-release-2026-10-03.md) preserves its
GitHub-reported identity. One isolated startup construction check passed.
Visible progress, application-managed download, client-exit handoff, installer
launch, overwrite installation and installed-client behavior were not run and
are not passes.

The [0.8.4 development record](0.8.4/development.md) identifies the clean
candidate built after the icon, action-library loading and plan-wording fixes.
The identified Setup was distributed unchanged through GitHub Release `v0.8.4`;
the [public release record](0.8.4/github-release-2026-10-03.md) preserves its
GitHub-reported identity. One isolated startup construction check passed.
Visible title-bar behavior, action-library navigation, plan import/export and
installed-client behavior were not run and are not passes.

The [0.8.3 development record](0.8.3/development.md) identifies the clean
candidate built after the updater and installer fixes. Its payload and installer
manifests are tracked beside that record. The identified Setup was distributed
unchanged through GitHub Release `v0.8.3`; the
[public release record](0.8.3/github-release-2026-10-03.md) preserves the
GitHub-reported asset identity. The build and one isolated startup check
succeeded, but application-managed download, installer launch, directory
selection and installed-client behavior were not run and are not passes.

The [0.8.2 development record](0.8.2/development.md) preserves the exact clean
candidate identity and the two selected startup-risk results. The identified
Setup was distributed unchanged through GitHub Release `v0.8.2`; the
[public release record](0.8.2/github-release-2026-10-03.md) preserves the
GitHub-reported asset identity. UI rendering and broader functional or installed
behavior were not run and are not claimed as passes.

The current [October 2 directory-progress candidate](0.8.0/installer-directory-progress-2026-10-02.md)
has candidate-specific directory-page, same-path installation, deletion-confirmation
cancellation and in-use refusal results. Other earlier installation/uninstallation
results retain their original candidate identities; they do not certify this build.
Its [P4 service diagnosis and prepared manual materials](0.8.0/p4-response-materials-2026-10-03.md)
preserve material-preparation and service-measurement facts only. On 2026-10-03,
the user cancelled bulk client response, training and fault verification under
[the personal-use policy](../development-plan.md#91-release-and-follow-up-boundaries).
Those unrun checks are not passes and are no longer pending acceptance blockers.
Historical results and identities stay unchanged. The user authorized GitHub
Release distribution on 2026-10-03. The distributed Setup remains the exact
`49de95af` candidate built from application source `89f7981`; subsequent
tracked changes are documentation, evidence and a local diagnostic-material
helper, with no application or installer input changes. GitHub distribution
does not declare a formal compatibility baseline.
The [October 2 final task-dialog candidate](0.8.0/local-candidate-2026-10-02-task-dialog-final.md)
retains its historical build and developer-operated results.
The [preceding dialog candidate](0.8.0/local-candidate-2026-10-02-uninstall-dialog.md)
received a second failed size retest: Chinese text was visible, but the form
remained oversized and bottom controls were clipped. It is replaced by Inno's
supported task-dialog layout, with the data-retention and confirmation boundaries retained.
The [path-fix candidate](0.8.0/local-candidate-2026-10-02-path-fix.md) retains
developer-confirmed creation, restart, data isolation, reinstall and relocation
checks. Its uninstall screenshot exposed poor layout and unclear ownership
refusal; program removal with root B and locator retained was observed, while
cancellation was not established. These results do not certify the new build.
The [earlier October 2 candidate](0.8.0/local-candidate-2026-10-02.md)
retains its exact identity and evidence.
The [September 30 candidate](0.8.0/local-candidate.md) retains its original evidence.
No 0.7.8 installer candidate was built or accepted. The latest historical
locally accepted candidate was 0.7.3 and is outside the current tracked history
set. The 0.7.5 and 0.7.7 records explicitly preserve incomplete or unrun client
checks. Candidate evidence certifies only its identified source and payload;
it never transfers to a later version.

## Historical records

- [0.8.18 GitHub Release record](0.8.18/github-release-2026-10-10.md)
- [0.8.18 development record](0.8.18/development.md)

- [0.8.17 GitHub Release record](0.8.17/github-release-2026-10-09.md)
- [0.8.17 development record](0.8.17/development.md)

- [0.8.16 GitHub Release record](0.8.16/github-release-2026-10-09.md)
- [0.8.16 development record](0.8.16/development.md)

- [0.8.15 GitHub Release record](0.8.15/github-release-2026-10-09.md)
- [0.8.15 development record](0.8.15/development.md)
- [0.8.14 GitHub Release record](0.8.14/github-release-2026-10-08.md)
- [0.8.14 development record](0.8.14/development.md)
- [0.8.13 GitHub Release record](0.8.13/github-release-2026-10-08.md)
- [0.8.13 development record](0.8.13/development.md)
- [0.8.12 GitHub Release record](0.8.12/github-release-2026-10-07.md)
- [0.8.12 development record](0.8.12/development.md)
- [0.8.11 GitHub Release record](0.8.11/github-release-2026-10-04.md)
- [0.8.11 development record](0.8.11/development.md)
- [0.8.10 GitHub Release record](0.8.10/github-release-2026-10-04.md)
- [0.8.10 development and candidate record](0.8.10/development.md)
- [0.8.9 GitHub Release record](0.8.9/github-release-2026-10-03.md)
- [0.8.9 development and local candidate record](0.8.9/development.md)
- [0.8.8 GitHub Release record](0.8.8/github-release-2026-10-03.md)
- [0.8.8 development and local candidate record](0.8.8/development.md)
- [0.8.7 GitHub Release record](0.8.7/github-release-2026-10-03.md)
- [0.8.7 development and local candidate record](0.8.7/development.md)
- [0.8.6 GitHub Release record](0.8.6/github-release-2026-10-03.md)
- [0.8.6 development and local candidate record](0.8.6/development.md)
- [0.8.5 GitHub Release record](0.8.5/github-release-2026-10-03.md)
- [0.8.5 development and local candidate record](0.8.5/development.md)
- [0.8.4 GitHub Release record](0.8.4/github-release-2026-10-03.md)
- [0.8.4 development and local candidate record](0.8.4/development.md)
- [0.8.3 GitHub Release record](0.8.3/github-release-2026-10-03.md)
- [0.8.3 development and local candidate record](0.8.3/development.md)
- [0.8.2 GitHub Release record](0.8.2/github-release-2026-10-03.md)
- [0.8.2 development and candidate record](0.8.2/development.md)
- [0.8.1 GitHub Release record](0.8.1/github-release-2026-10-03.md)
- [0.8.1 development record](0.8.1/development.md)
- [0.8.0 GitHub Release record](0.8.0/github-release-2026-10-03.md)
- [0.8.0 development record](0.8.0/development.md)
- [0.7.8 documentation-governance development record](0.7.8/development.md)
- [0.7.7 development and partial candidate evidence](0.7.7/)
- [0.7.6 development record](0.7.6/)
- [0.7.5 development, reset design and candidate evidence](0.7.5/)

Earlier tracked records remain discoverable through Git history. Local
`docs/archive/` and `.planning/archive/` content is historical holding context,
not current authority or a support promise.

## Retention policy

On a version change, update this map and the source identities together.
Retain or remove historical records, fixtures and migration entry points only
under [development plan §13](../development-plan.md#13-version-retention-and-development-data-policy).
Unsupported and future roots must be refused unchanged before writes.
