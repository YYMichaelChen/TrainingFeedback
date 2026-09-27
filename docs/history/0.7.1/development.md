# 0.7.1 Interface Development

Application 0.7.1 used database schema22 and catalog `070-illustrated-3`.
On 2026-09-25, local development builds simplified the interface: the action
library stopped exposing content-version pickers and comparison tabs, internal
IDs and hashes were removed from user-facing views, remaining enum values were
localized, and migrated history events became readable. Exact immutable content
and frozen session facts remained in the data layer.

The source changes were left uncommitted at the time. Two local 0.7.1 installers
were built from a dirty working tree and installed for review. They are local
development evidence, not a reproducible clean source release. Those changes
were subsequently included in the 0.7.2 source commit. The local Planscope
route is `.planning/archive/v0.7.1/SUMMARY.md`; earlier task records remain under
`.planning/archive/0.7.1/` while this version stays in the three-version window.

No local build established expert approval, plan activation, personal training
facts or a personal-data transition.
