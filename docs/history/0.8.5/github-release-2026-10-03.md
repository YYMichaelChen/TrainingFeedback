# GitHub Release v0.8.5

On 2026-10-03 the identified personal-use Setup was published as
[`v0.8.5`](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.5).

## Distributed artifact

| Item | Value |
| --- | --- |
| Asset | `TrainingFeedback-0.8.5-Setup.exe` |
| SHA-256 | `37658f63ce49535f73ac56fef7d186495982aeecd38e5d559afe3b26cd5dc9e0` |
| Size | 85,665,376 bytes |
| Signature | Not signed |
| Application source used by the build | `749b6a306572eed191d268ca1cfa54169842a60e` |
| Release tag target | `bdab54318ba90bd43a96fc84ee2c98d8771a6240` |
| Application/schema/catalog/contract | 0.8.5 / 24 / 070-illustrated-3 / 4 |

The tag target includes the candidate-evidence commit; the Setup was built from
the clean application-source commit above. The tracked payload and installer
manifests in this directory preserve the exact candidate identity.

The unauthenticated public latest-Release API was inspected after upload. It
returned stable, non-draft, non-prerelease `v0.8.5`, published at
`2026-10-03T07:37:40Z`, with exactly the asset above in `uploaded` state. Its
reported size,
`sha256:37658f63ce49535f73ac56fef7d186495982aeecd38e5d559afe3b26cd5dc9e0`
digest and browser URL matched the local candidate. This is a distribution-
identity check only.

## Scope and limits

- One isolated startup-construction scenario passed once; manual checks were zero.
- Visible download progress, application-managed download, client-exit handoff,
  installer launch, overwrite installation and installed-client behavior were
  not run and are not passes.
- The unsigned Setup may trigger normal Windows trust warnings.
- GitHub distribution does not declare formal compatibility or public support,
  external content review, personal-data transition or W4 completion.
