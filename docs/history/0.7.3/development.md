# 0.7.3 Plan Page and Local Candidate

Application 0.7.3 retains database schema22, catalog `070-illustrated-3`, and
plan and evidence wire contract v2. The retained application window is
0.7.3/0.7.2/0.7.1. These versions share schema22; the runtime can reject
pre-schema22 roots unchanged but cannot distinguish an older schema22 root by
the application version that first created it. No schema or contract migration
is introduced by this patch.

The Training Plan page now has a compact revision navigator and structured
day, action, group, member and set detail. The saved adjustment text appears
once. Technical import and migration evidence remains stored but is omitted
from the plan view and activation preview. The local development checks are
recorded in the v0.7.3 Planscope log.

The clean source snapshot is `acadd9dc594bee58ef74f26e3ba167b83c3bfe13`.
Patch scope `release-0.7.3` passed 32 unique cases, comprising the
27-case baseline and five affected plan/schema cases. Ruff and diff checks
passed. The local directory payload contained 294 files and matched its
manifest in full; all 38 catalog files matched source. Setup SHA-256 is
`529311f885d6ff694619fc6e31dc05f283c0fed11b045476d376f85b242640bf`.

Installed LOCAL-01 through LOCAL-06 passed in a non-elevated account with
isolated synthetic roots, including first-use cancel/invalid paths, new-root
catalog, plan-page UI, restart, retained 0.7.1/0.7.2 schema22 roots and
unchanged expired/future-root refusal. The ordinary per-user program install
and Start Menu shortcut now point to the 0.7.3 payload. Candidate-specific
manifest, source archive, Setup, hashes, input baseline and screenshots are in
`.tmp/releases/0.7.3/20260927-085133-acadd9d/LOCAL-ACCEPTANCE.md` on the
build machine. The binaries are unsigned. Public distribution, independent
Windows acceptance, external content review, personal-data transition and W4
remain separate events.
