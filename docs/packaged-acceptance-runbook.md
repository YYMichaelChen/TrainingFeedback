# Packaged Acceptance Runbook

This runbook applies to every application version. The
[development workflow](development-workflow.md) decides when a candidate is
needed and which verification tier applies. Current supported application/schema
versions are in the [version history index](history/README.md). Put dated results,
hashes and candidate status in candidate-specific evidence; this file is a
procedure, not a certificate for any build.

## 1. Build and identify a candidate

1. Finish the intended source and built-in catalog content. Record application,
   database schema, catalog and external wire-contract identities separately.
   Use a clean, complete source revision for a local-release or completed
   installed-acceptance claim. A dirty build is an informal preview with a
   complete source snapshot and no acceptance claim.
2. Use the pinned toolchain and PowerShell 7. Build the directory payload and
   installer with `pwsh -File packaging/build.ps1 -Installer`, supplying `-ISCC`
   when the Inno Setup compiler is not found automatically.
3. Preserve the directory payload, adjacent build manifest, Setup executable and
   installer manifest together. Compare every payload path, size and hash to the
   manifest, including unexpected files. Verify the bundled catalog and actual
   illustration bytes, required contracts/runtime files and absence of locator,
   personal roots or other user data in the program payload.
4. Record source revision/snapshot, source dirty flag, build time, toolchain and
   Windows architecture, manifest/EXE/Setup hashes and Authenticode status.
   Candidate identity changes when source or payload bytes change. Preserve prior
   candidate evidence under its own identity.

The installer replaces program files only. Compare closed isolated locator/root
bytes before launching a replacement program; application startup may then apply
only a declared supported migration. Never use a real personal root for fault
injection or synthetic training.

## 2. Local installed acceptance

Use the newly built Setup on the build machine with an ordinary-user context,
isolated `%LOCALAPPDATA%` locator and synthetic roots. Resolve the installed EXE
before changing `%LOCALAPPDATA%`; suppress automatic post-install launch until
the isolated profile is active. Keep one profile for restart checks and fresh
named profiles for independent inputs. Close the app before copying a root.

| Check | Required observation |
| --- | --- |
| Installed payload | Setup succeeds; installed files equal the complete payload manifest; program replacement leaves the closed isolated locator/root unchanged. |
| Fresh launch | Cancelling root choice creates no locator/root; invalid and occupied destinations fail cleanly. |
| New root | A Chinese or space-containing empty root receives the complete current built-in catalog and valid assets without an old root, manual import or invented review/plan/training facts. |
| Restart | The same isolated root reopens with its selected state and frozen facts; no duplicate migration or stray data in program files. |
| Affected workflow | Exercise the actual UI path changed by this candidate. For a release with no narrower workflow, use a representative plan, result, pause, restart and resume path with blank actuals preserved. |
| Compatibility, when changed | Open copies of each retained endpoint and verify declared upgrade preservation; reject expired/future roots unchanged before writes. Preserve untouched originals. |

For each applicable check, record candidate and installed identities, account,
paths, synthetic input baseline, operations, expected/observed result, evidence
path/hash and `pass`, `fail` or `not run`. Inspect interactive UI where the claim
depends on visible behavior; offscreen process survival alone is not that evidence.
If a candidate changes, rerun affected checks and explicitly cite earlier
unchanged checks that were not repeated. Do not relabel prior results as new
candidate passes. Unsigned local builds disclose their status; signing is a
public-distribution requirement.

## 3. Public release preparation — explicit request only

Do not start independent acceptance or public distribution without the user's
explicit public-release request. The local gate must first identify the exact
candidate. Prepare isolated synthetic roots from **actual** retained-version
programs and manifests named by the current version index. Preserve unopened
originals, closed transfer copies, logical facts, original text/unknown fields,
resource hashes and database hashes. A tag rebuilt later is a different binary
identity. Include one expired root for unchanged refusal and a future-schema
root; arbitrary intermediate schemas are not upgrade promises.

Transfer only identified programs/installers/manifests, synthetic fixture copies,
baseline descriptions/hashes, operator instructions and evidence forms. Use an
independent Windows x64 VM or machine with an ordinary non-administrator account,
without Python, Conda, source checkout or access to the build environment. A new
account on the build machine is insufficient. Isolate its locator and close apps
before copying roots. Never test an old binary on the sole upgraded copy.

## 4. Independent public acceptance — explicit request only

Execute the following against the exact candidate with actual UI interaction.
Each row needs input baseline, operations, expected/observed result, logical and
resource comparison, evidence path/hash and a `pass`, `fail` or `not run` status.

| ID | Scenario and required result |
| --- | --- |
| PUB-01 | Install as an ordinary user; cancel, create a fresh Chinese/space root and try invalid/occupied paths. Built-ins load without old data; cancel leaves nothing partial. |
| PUB-02 | Install over each actual retained-version program and open copies of its root. Installer preserves data; supported startup upgrade preserves locator, text, unknowns and frozen facts without re-import. |
| PUB-03 | Compare upgraded facts/resources, restart twice and restart Windows, then switch roots. No duplicate conversion, approval or assets; paused position and root isolation survive. |
| PUB-04 | Open interrupted supported roots; exercise access, space and backup failures, expired and future roots. Recovery is consistent; unsupported roots remain unchanged with actionable guidance. |
| PUB-05 | Exercise guidance/image eligibility through review, plan and start. Invalid/missing assets block new use; valid unreviewed assets invent no approval; originals remain. |
| PUB-06 | Browse families and edit/activate plans with groups, sides, repeated members and distinct units. Ordering and pinned prescriptions remain exact; invalid/stale input loses nothing. |
| PUB-07 | Record individual and round outcomes, partial work, retraction/cancel, pause/restart and abort/finish. Atomic actions preserve exact facts and agree with history/export. |
| PUB-08 | Exercise removal, restoration and publisher withdrawal. New use is blocked as declared; frozen work/history remain usable; restoration does not auto-enable. |
| PUB-09 | Export portable evidence/images and import the current contract. JSON/Markdown/hashes agree; originals remain; imports are drafts; unsupported formats fail clearly. |
| PUB-10 | Back up an active synthetic root, try bad destinations, reopen and resume with a newer catalog. Assets and facts survive; failures leave no misleading partial backup. |
| PUB-11 | Inspect settings/library/import, then upgrade, uninstall and reinstall. Program operations leave locator/root intact and fresh roots use current built-ins. |
| PUB-12 | Inspect real desktop scaling at 100%, 125% and 150% on 1366×768 and 1920×1080 where available. Long Chinese text and many actual-set rows keep core controls reachable. |

Record actual alternatives for unavailable display sizes; a required scenario
remains open until evidenced. The public Setup and EXE require valid trusted
Authenticode signatures; verify them and the intended distribution artifact.
Every required row must pass for the identified candidate
before public acceptance is claimed. Missing or deferred evidence remains `not
run`; local checks, expert content review, personal use and W4 cannot stand in
for independent technical acceptance.
