# GitHub Release v0.8.3

On 2026-10-03 the identified personal-use Setup was published as
[`v0.8.3`](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.3).

## Distributed artifact

| Item | Value |
| --- | --- |
| Asset | `TrainingFeedback-0.8.3-Setup.exe` |
| SHA-256 | `a7dcb23536c43422355d6113df926fef2f05cbeaaea383310e9630f50a381009` |
| Size | 85,661,990 bytes |
| Signature | Not signed |
| Application source used by the build | `d157174e5bd3246c084b96410b986be356dc8bc3` |
| Release tag target | `d3ee241a3c9c118950cdd9f3b02743428992fb14` |
| Application/schema/catalog/contract | 0.8.3 / 24 / 070-illustrated-3 / 4 |

The tag includes the candidate-evidence commit; the Setup was built from the
clean application-source commit above. The tracked payload and installer build
manifests in this directory preserve the exact candidate identity.

The public latest-Release API was inspected after upload. It returned stable,
non-draft `v0.8.3`, published at `2026-10-03T07:01:30Z`, with exactly the asset
above in `uploaded` state. Its reported size, `sha256:` digest and browser URL
matched the local candidate. This is a distribution-identity check only.

## Scope and limits

- The one selected updater/main-window startup-risk scenario passed after one
  environment-only failed execution; manual checks were zero.
- Application-managed download, Setup launch, directory selection, overwrite
  installation and broader client behavior were not run and are not passes.
- The unsigned Setup may trigger normal Windows trust warnings.
- GitHub distribution does not declare formal compatibility or public support,
  external content review, personal-data transition or W4 completion.
