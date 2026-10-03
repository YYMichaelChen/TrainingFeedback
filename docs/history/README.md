# Version History

This is the single human-readable implementation identity map and index of
candidate-specific evidence. Product retention and compatibility rules are
owned by [development plan §13](../development-plan.md#13-version-retention-and-development-data-policy);
the [development workflow](../development-workflow.md) owns version rotation.

## Current implementation

- Application: **0.8.5**
- Database schema: **24**
- Catalog: **070-illustrated-3**
- Current plan/evidence contract: **4**
- GitHub distribution: **v0.8.5**
- Formal compatibility baseline declared: **no**
- Current development version: [0.8.5](../releases/0.8.5/design.md)

The user has suspended old-version compatibility obligations until an explicit
formal-release declaration. Older rows below are historical records, not a
current support promise.

## Version map

| Application | Database schema | Role | Candidate status |
| --- | ---: | --- | --- |
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
