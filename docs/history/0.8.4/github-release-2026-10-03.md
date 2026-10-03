# GitHub Release v0.8.4

On 2026-10-03 the identified personal-use Setup was published as
[`v0.8.4`](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.4).

## Distributed artifact

| Item | Value |
| --- | --- |
| Asset | `TrainingFeedback-0.8.4-Setup.exe` |
| SHA-256 | `832e958df99c3707d85065f715787d4035d69f85fe1830ec8f4116c47c8497b7` |
| Size | 85,662,349 bytes |
| Signature | Not signed |
| Application source used by the build | `768ef9e614cac1022ed09807bcd2fae65ec5b2b2` |
| Release tag target | `1c5e2edd110de0f3c6d87518c6ddddc18d56527f` |
| Application/schema/catalog/contract | 0.8.4 / 24 / 070-illustrated-3 / 4 |

The tag target includes the candidate-evidence commit; the Setup was built from
the clean application-source commit above. The tracked payload and installer
manifests in this directory preserve the exact candidate identity.

The public latest-Release API was inspected after upload. It returned stable,
non-draft, non-prerelease `v0.8.4`, published at `2026-10-03T07:27:09Z`, with
exactly the asset above in `uploaded` state. Its reported size,
`sha256:832e958df99c3707d85065f715787d4035d69f85fe1830ec8f4116c47c8497b7`
digest and browser URL matched the local candidate. This is a distribution-
identity check only.

## Scope and limits

- One isolated icon-resource/main-window startup scenario passed once; manual
  checks were zero.
- Visible title-bar and dialog icons, action-library navigation/loading, plan
  import/export, Setup launch, installation and overwrite behavior were not run
  and are not passes.
- The unsigned Setup may trigger normal Windows trust warnings.
- GitHub distribution does not declare formal compatibility or public support,
  external content review, personal-data transition or W4 completion.
