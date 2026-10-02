# Version History

This is the single human-readable implementation identity map and index of
candidate-specific evidence. Product retention and compatibility rules are
owned by [development plan §13](../development-plan.md#13-version-retention-and-development-data-policy);
the [development workflow](../development-workflow.md) owns version rotation.

## Current implementation

- Application: **0.8.0**
- Database schema: **23**
- Catalog: **070-illustrated-3**
- Current plan/evidence contract: **3**
- Formal release declared: **no**
- Current development target: [0.8.0](../releases/0.8.0/design.md)

The user has suspended old-version compatibility obligations until an explicit
formal-release declaration. Older rows below are historical records, not a
current support promise.

## Version map

| Application | Database schema | Role | Candidate status |
| --- | ---: | --- | --- |
| 0.8.0 | 23 | Current development version: [installation, cleanup and response work](0.8.0/development.md) | [October 2 task-dialog candidate; manual retest not run](0.8.0/local-candidate-2026-10-02-task-dialog.md) |
| 0.7.8 | 23 | Historical development version: [documentation and knowledge governance](0.7.8/development.md) | No installer candidate; documentation/identity verification only |
| 0.7.7 | 23 | Historical development version: [new-root creation](0.7.7/development.md) | [User-approved partial closeout; full installed acceptance incomplete](0.7.7/local-candidate.md#2026-09-29-部分验收收尾) |
| 0.7.6 | 23 | Historical development version: [documentation ownership and routing](0.7.6/development.md) | No installer candidate; development verification only |
| 0.7.5 | 23 | Historical development version: [plan/reset development](0.7.5/development.md) | [User-approved closeout; installed acceptance incomplete](0.7.5/local-candidate.md#2026-09-29-final-version-closeout) |

Intermediate schemas and retired development versions retain their original
identities in Git history; they do not imply application releases or support.

## Candidate status

The [October 2 task-dialog candidate](0.8.0/local-candidate-2026-10-02-task-dialog.md)
is built and statically verified; its installed and client checks remain not run.
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
