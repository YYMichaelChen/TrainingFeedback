# GitHub Release v0.8.8

On 2026-10-03 the identified personal-use Setup was published as
[`v0.8.8`](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.8).

## Distributed artifact

| Item | Value |
| --- | --- |
| Asset | `TrainingFeedback-0.8.8-Setup.exe` |
| SHA-256 | `bfbf1789b53d10f6aada0875c7395dcaf0493868a8a8f03b89b5119632c17207` |
| Size | 85,672,877 bytes |
| Signature | Not signed |
| Application source used by the build | `13e99547f4995b64ea18463a0c2a5491d76d461f` |
| Release tag target | `29fa9d3538ff85ef03ef85ab8b021ddaebce6ddf` |
| Application/schema/catalog/contract | 0.8.8 / 24 / 070-illustrated-3 / 4 |

The tag target includes the candidate-evidence commit; the Setup was built from
the clean application-source commit above. The tracked payload and installer
manifests in this directory preserve the exact candidate identity.

The unauthenticated public latest-Release API was inspected after upload. It
returned stable, non-draft, non-prerelease `v0.8.8`, published at
`2026-10-03T09:01:08Z`, with exactly the asset above in `uploaded` state. Its
reported size,
`sha256:bfbf1789b53d10f6aada0875c7395dcaf0493868a8a8f03b89b5119632c17207`
digest and browser URL matched the local candidate. This is a distribution-
identity check only.

## Scope and limits

- One isolated coordinator/main-window startup scenario passed once with no
  rerun; manual checks were zero.
- Download, handoff, exit, watchdog, launcher and installed-client behavior
  were not run and are not passes.
- The unsigned Setup may trigger normal Windows trust warnings.
- GitHub distribution does not declare formal compatibility or public support,
  external content review, personal-data transition or W4 completion.
