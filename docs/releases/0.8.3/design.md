# 0.8.3 Emergency Update Design

## Identity

- Application version: `0.8.3`
- Database schema: `24`
- Catalog: `070-illustrated-3`
- Plan and evidence wire contracts: `4`
- Previous distributed version: `0.8.2` / schema `24` / contract `4`

Implementation and candidate evidence belong in the
[0.8.3 development record](../../history/0.8.3/development.md). GitHub Release
distribution is a separate event and does not declare a formal compatibility
baseline or public-support scope.

## Scope

- Make verified application-managed Setup download the default action after the
  user accepts an available update. Stream into a unique temporary directory,
  require the exact Release byte size and SHA-256, then start Setup and exit the
  current application.
- Keep GitHub Release viewing and browser download as explicit secondary actions.
  Never execute a partial, oversized or digest-mismatched file.
- Let Inno Setup resolve the stable AppId's previous installation directory
  before its `%LocalAppData%\Programs\TrainingFeedback` fallback. Continue to
  validate the selected directory, payload ownership and uninstaller before any
  overwrite or relocation.
- Keep schema 24, catalog `070-illustrated-3`, contract 4 and all user data
  boundaries unchanged.

The release execution plan is `.planning/releases/v0.8.3/PLAN.md`. Product
behavior and release gates remain governed by
[`development-plan.md`](../../development-plan.md), and procedure by
[`development-workflow.md`](../../development-workflow.md).
