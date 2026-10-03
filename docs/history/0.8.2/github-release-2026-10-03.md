# GitHub Release v0.8.2

On 2026-10-03 the identified personal-use Setup was published as
[`v0.8.2`](https://github.com/YYMichaelChen/TrainingFeedback/releases/tag/v0.8.2).

## Distributed artifact

| Item | Value |
| --- | --- |
| Asset | `TrainingFeedback-0.8.2-Setup.exe` |
| SHA-256 | `c04ba484d6d6cbf9a7c3347a0728ad4859e11a51cb131641465b5c18ab568d97` |
| Size | 85,660,884 bytes |
| Signature | Not signed |
| Application source used by the build | `75b34bb45e1179df8f93b2cbe7656982272a7421` |
| Release tag target | `3e93becdc6473c6bdd1b547f38a99df678133a8d` |
| Application/schema/catalog/contract | 0.8.2 / 24 / 070-illustrated-3 / 4 |

The tag includes the candidate evidence commit; the Setup was built from the
clean application-source commit above. The tracked payload and installer build
manifests in this directory preserve the exact candidate identity.

The public latest-Release API was inspected after upload. It returned stable,
non-draft `v0.8.2`, published at `2026-10-03T04:24:25Z`, with exactly the asset
above in `uploaded` state. Its reported size, `sha256:` digest and browser URL
matched the local candidate. This is a distribution-identity check only.

## Scope and limits

- The two selected schema 23→24 startup-risk scenarios passed; manual checks
  were zero.
- UI rendering, complete plan/training workflows, import/export, installation
  and overwrite-update behavior were not run and are not recorded as passes.
- The unsigned Setup may trigger normal Windows trust warnings.
- GitHub distribution does not declare formal compatibility or public support,
  external content review, personal-data transition or W4 completion.
