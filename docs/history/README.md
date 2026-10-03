# Version History

This is the single human-readable implementation identity map and index of
candidate-specific evidence. Product retention and compatibility rules are
owned by [development plan §13](../development-plan.md#13-version-retention-and-development-data-policy);
the [development workflow](../development-workflow.md) owns version rotation.

## Current implementation

- Application: **0.8.1**
- Database schema: **23**
- Catalog: **070-illustrated-3**
- Current plan/evidence contract: **3**
- GitHub distribution: **v0.8.0**; v0.8.1 pending
- Formal compatibility baseline declared: **no**
- Current development version: [0.8.1](../releases/0.8.1/design.md)

The user has suspended old-version compatibility obligations until an explicit
formal-release declaration. Older rows below are historical records, not a
current support promise.

## Version map

| Application | Database schema | Role | Candidate status |
| --- | ---: | --- | --- |
| 0.8.1 | 23 | Current update: [GitHub update discovery](../releases/0.8.1/design.md) | Implementation in progress; no candidate or GitHub Release yet |
| 0.8.0 | 23 | Current personal-use update: [installation, cleanup and response work](0.8.0/development.md) | GitHub Release `v0.8.0`; Setup SHA-256 `49de95af46f2ae0f20f36a7bbb1f4e6318a418cf9b117370ee130ced1b1dcdad`; unsigned |
| 0.7.8 | 23 | Historical development version: [documentation and knowledge governance](0.7.8/development.md) | No installer candidate; documentation/identity verification only |
| 0.7.7 | 23 | Historical development version: [new-root creation](0.7.7/development.md) | [User-approved partial closeout; full installed acceptance incomplete](0.7.7/local-candidate.md#2026-09-29-部分验收收尾) |
| 0.7.6 | 23 | Historical development version: [documentation ownership and routing](0.7.6/development.md) | No installer candidate; development verification only |
| 0.7.5 | 23 | Historical development version: [plan/reset development](0.7.5/development.md) | [User-approved closeout; installed acceptance incomplete](0.7.5/local-candidate.md#2026-09-29-final-version-closeout) |

Intermediate schemas and retired development versions retain their original
identities in Git history; they do not imply application releases or support.

## Candidate status

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
