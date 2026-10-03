# GitHub Release v0.8.7

On 2026-10-03 the identified personal-use Setup was published as
[`v0.8.7`](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.7).

## Distributed artifact

| Item | Value |
| --- | --- |
| Asset | `TrainingFeedback-0.8.7-Setup.exe` |
| SHA-256 | `48c4dae577a17428760c135c5713f1e87608cbc9e0b89b0ff5b4e2f955a62ee0` |
| Size | 85,672,077 bytes |
| Signature | Not signed |
| Application source used by the build | `5bf3f694780b425cb3b6ea0407aad9304b637b89` |
| Release tag target | `9e9e7cc54e363c7ae5670ee218975f048e32613b` |
| Application/schema/catalog/contract | 0.8.7 / 24 / 070-illustrated-3 / 4 |

The tag target includes the candidate-evidence commit; the Setup was built from
the clean application-source commit above. The tracked payload and installer
manifests in this directory preserve the exact candidate identity.

The unauthenticated public latest-Release API was inspected after upload. It
returned stable, non-draft, non-prerelease `v0.8.7`, published at
`2026-10-03T08:36:48Z`, with exactly the asset above in `uploaded` state. Its
reported size,
`sha256:48c4dae577a17428760c135c5713f1e87608cbc9e0b89b0ff5b4e2f955a62ee0`
digest and browser URL matched the local candidate. This is a distribution-
identity check only.

## Scope and limits

- One isolated startup construction scenario passed once on the repository
  interpreter (a prior attempt with the system interpreter lacking the project
  dependency failed before reaching the change and was rerun as the same
  node); manual checks were zero.
- Navigation switching, the substituted error page, library loading behavior
  and installed-client behavior were not run and are not passes.
- The unsigned Setup may trigger normal Windows trust warnings.
- GitHub distribution does not declare formal compatibility or public support,
  external content review, personal-data transition or W4 completion.
