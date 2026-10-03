# GitHub Release v0.8.10

On 2026-10-04 (Asia/Shanghai) the identified personal-use Setup was published as
[`v0.8.10`](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.10).

## Distributed artifact

| Item | Value |
| --- | --- |
| Asset | `TrainingFeedback-0.8.10-Setup.exe` |
| SHA-256 | `9846aedc52073b9c85e9f52c7f3cafe2450e60a6c38a103368bb8c34c2b1580d` |
| Size | 85,669,719 bytes |
| Signature | Not signed |
| Application source used by the build | `5f37d83ab8292d4d62652a2e0a3e01f51052bb3f` |
| Release tag target | `48bf157f75544a22fece98c7a8e084bfe815e056` |
| Application/schema/catalog/contract | 0.8.10 / 24 / 070-illustrated-3 / 4 |

The tag target includes the candidate-evidence commit; the Setup was built from
the clean application-source commit above. The tracked payload and installer
manifests in this directory preserve the exact candidate identity.

The unauthenticated public latest-Release API was inspected after upload. It
returned stable, non-draft, non-prerelease `v0.8.10`, published at
`2026-10-03T16:38:27Z`, with exactly the asset above in `uploaded` state. Its
reported size and
`sha256:9846aedc52073b9c85e9f52c7f3cafe2450e60a6c38a103368bb8c34c2b1580d`
digest matched the local candidate. This is a distribution-identity check only.

## Scope and limits

- One isolated startup-construction scenario passed once; manual checks were
  zero.
- Illustration rendering, card alignment, application-managed download,
  client-exit handoff, installer launch, overwrite installation and
  installed-client behavior were not run and are not passes.
- The unsigned Setup may trigger normal Windows trust warnings.
- GitHub distribution does not declare formal compatibility or public support,
  external content review, personal-data transition or W4 completion.
