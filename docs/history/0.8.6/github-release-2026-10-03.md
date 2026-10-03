# GitHub Release v0.8.6

On 2026-10-03 the identified personal-use Setup was published as
[`v0.8.6`](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.6).

## Distributed artifact

| Item | Value |
| --- | --- |
| Asset | `TrainingFeedback-0.8.6-Setup.exe` |
| SHA-256 | `06120b97244ab24a745a429617e04abdbe50f7b0057086cf050f64158b89e61c` |
| Size | 85,664,463 bytes |
| Signature | Not signed |
| Application source used by the build | `ccb47bd09e33807807ed28eedc863bbf4b172b2f` |
| Release tag target | `58f3c215fca3ec63b22e384f2fd46be27fe9cdc0` |
| Application/schema/catalog/contract | 0.8.6 / 24 / 070-illustrated-3 / 4 |

The tag target includes the candidate-evidence commit; the Setup was built from
the clean application-source commit above. The tracked payload and installer
manifests in this directory preserve the exact candidate identity.

The unauthenticated public latest-Release API was inspected after upload. It
returned stable, non-draft, non-prerelease `v0.8.6`, published at
`2026-10-03T07:54:34Z`, with exactly the asset above in `uploaded` state. Its
reported size,
`sha256:06120b97244ab24a745a429617e04abdbe50f7b0057086cf050f64158b89e61c`
digest and browser URL matched the local candidate. This is a distribution-
identity check only.

## Scope and limits

- One isolated coordinator/main-window startup scenario passed once; manual
  checks were zero.
- Stale-directory selection/deletion, launcher waiting, Setup execution,
  post-install cleanup and installed-client behavior were not run and are not
  passes.
- The unsigned Setup may trigger normal Windows trust warnings.
- GitHub distribution does not declare formal compatibility or public support,
  external content review, personal-data transition or W4 completion.
