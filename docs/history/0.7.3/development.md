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

Candidate identity, test results and installed acceptance are recorded below
after the clean-source build. Public distribution, external content review,
personal-data transition and W4 remain separate events.
