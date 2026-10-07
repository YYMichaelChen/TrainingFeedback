# 0.8.12 External Updater Exit Design

## Identity and authorization

- Application: `0.8.12`
- Database schema: `24`
- Catalog: `070-illustrated-3`
- Plan/evidence contract: `4`
- Events: updater development follow-up, application-version rotation,
  clean installer build and GitHub Release distribution.

The user's 2026-10-07 instruction authorizes commit, push and a new Release.
Carry the [2026-10-06 source correction](../../history/0.8.11/updater-follow-up-2026-10-06.md)
into a uniquely versioned installer. Product installation behavior is owned by
[development plan §9.1](../../development-plan.md#91-release-and-follow-up-boundaries).

## Scope

Move the shutdown watchdog out of Python/Qt into a hidden Windows launcher.
Pass an inherited wait/terminate handle to the exact running application process;
wait for launcher readiness before requesting normal application exit. After a
10-second grace period, the launcher may terminate only that bound process and
must confirm actual exit before starting the verified Setup. Preparation failure
keeps the application open, and failure diagnostics remain in the strictly owned
temporary directory. Setup retains the existing interactive installation flow.

Update version identities and the implemented schema/application mapping only.
No schema, catalog, external contract, personal fact, text or data-root changes.
Do not inspect real data, legacy databases or run the client/installer.

## Verification and distribution

Keep scope `2026-10-06-external-update-exit` across source repair and distribution.
Exactly one isolated no-network startup scenario already passed once, in 1.62s;
no rerun or additional application/manual check is selected. Static source,
PowerShell syntax, documentation and identity checks do not certify update exit.

Build from clean committed source, retain installer and payload manifests, then
publish stable `v0.8.12` with exactly one `TrainingFeedback-0.8.12-Setup.exe`.
Confirm uploaded size and GitHub digest and the unauthenticated latest-Release
response. Record exact source, tag and asset identities in
[development evidence](../../history/0.8.12/development.md).
Distribution does not declare formal compatibility, public acceptance or W4.

An already running older application uses its own old updater during this
upgrade; downloading 0.8.12 cannot replace the updater in that running process.
The external watchdog becomes available after installing and opening 0.8.12.
