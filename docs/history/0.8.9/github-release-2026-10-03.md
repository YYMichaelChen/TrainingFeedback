# GitHub Release v0.8.9

On 2026-10-03 the identified personal-use Setup was published as
[`v0.8.9`](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.9).

## Distributed artifact

| Item | Value |
| --- | --- |
| Asset | `TrainingFeedback-0.8.9-Setup.exe` |
| SHA-256 | `e0030b4c15be767b46fafb7e0da652bd27ce647207779eb2e5163a873accd722` |
| Size | 85,670,039 bytes |
| Signature | Not signed |
| Application source used by the build | `eec23905bdb70240fc904335531fea44623a9e7c` |
| Release tag target | `4401c00926b2ee64cbef7db9857e791ae6e36f76` |
| Application/schema/catalog/contract | 0.8.9 / 24 / 070-illustrated-3 / 4 |

The tag target includes the candidate-evidence commit; the Setup was built from
the clean application-source commit above. The tracked payload and installer
manifests in this directory preserve the exact candidate identity.

The unauthenticated public latest-Release API was inspected after upload. It
returned stable, non-draft, non-prerelease `v0.8.9`, published at
`2026-10-03T14:53:52Z`, with exactly the asset above in `uploaded` state. Its
reported size,
`sha256:e0030b4c15be767b46fafb7e0da652bd27ce647207779eb2e5163a873accd722`
digest and browser URL matched the local candidate. This is a distribution-
identity check only.

## Scope and limits

- Application tests and manual checks were zero under the current startup-only
  policy.
- Action-library navigation, dialog construction, catalog loading and
  installed-client behavior were not run and are not passes.
- The unsigned Setup may trigger normal Windows trust warnings.
- GitHub distribution does not declare formal compatibility or public support,
  external content review, personal-data transition or W4 completion.
