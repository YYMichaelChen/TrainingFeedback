# 0.7.2 Version Update

Application 0.7.2 uses database schema22, catalog `070-illustrated-3`, plan and
evidence wire contract v2. Its source identity is the `v0.7.2` Git tag once the
version commit is pushed. The build manifest beside the local installer records
the exact commit and `source_dirty: false`.

The release combines the 0.7.1 interface cleanup with an illustration-card
action library. A card opens guidance, illustrations, review history and normal
actions; an explicit multi-selection mode retains batch review/removal. The
library gallery shows latest content without changing the default browse
semantics used by planning and lifecycle operations.

The retained application window is 0.7.2/0.7.1/0.7.0, all at schema22. Existing
roots below schema22 are refused read-only before writes. The old schema16
conversion runtime entry, its exclusive synthetic fixtures and positive old-root
tests rotated out. Generic recovery and persisted migration provenance remain
where current schema22 roots can still contain their evidence. The 0.6.0/0.6.1
complete documents moved into the ignored local `docs/archive/` holding area;
Git history retains their tracked content.

This version does not claim public H3 acceptance, external content approval,
personal-data transition or genuine training facts.
