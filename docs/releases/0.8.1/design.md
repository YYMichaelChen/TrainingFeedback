# 0.8.1 GitHub Update Discovery

Status: implemented and packaged for GitHub Release distribution on 2026-10-03.

## Goal

Add a non-blocking check of the repository's latest stable GitHub Release. A
newer version is disclosed through a hollow-circle exclamation mark; the user
may open the Release page or the exact Setup download in the system browser and
then decides whether to run the installer.

## Boundaries

- The check starts only after the first main window is visible and runs once per
  process. Root switching reuses the process-scoped result.
- Network, rate-limit and response failures never block startup and are visible
  only in Settings, where the user can retry.
- GitHub response text is untrusted plain text. Direct Setup access requires the
  unique uploaded asset, trusted repository URL and SHA-256 digest.
- The application does not download, verify, execute or install the Setup file.
- Application/schema/catalog/contract identity is
  `0.8.1 / 23 / 070-illustrated-3 / 3`.
- 0.8.0 must receive this bootstrap version through one final manual update.

## Verification policy

The new startup imports and coordinator construction create one concrete opening
risk. At most one isolated synthetic-root startup scenario is selected. Manual
testing remains zero; parsing, interaction, browser download and installer
behavior are not expanded into functional regression requirements.

Actual candidate identity and checks are recorded in the
[version history](../../history/0.8.1/development.md).
