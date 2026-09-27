# 0.7.4 Performance Development

Application 0.7.4 retains database schema22, catalog `070-illustrated-3`, and
plan and evidence wire contract v2. The retained application window is
0.7.4/0.7.3/0.7.2. These versions share schema22; the runtime cannot infer which
application version first created an existing schema22 root. Roots below schema22
are still refused unchanged before writes. This patch introduces no database,
catalog or wire-contract migration.

The main window creates inactive pages when first opened. The action library
shows cards promptly, checks and renders images in small event-loop steps, and
reuses validated image results and thumbnails while the source bytes remain
unchanged. Runtime actions continue to validate the exact image bytes. Exercise
and frozen-session guidance display a wider preview that opens the original
illustration on click; the 1254×1254 bundled source images are unchanged.

Development scope `perf-image-ui-20260927` passed 14 unique affected cases,
including image invalidation, navigation, root compatibility and export.
Ruff and `git diff --check` passed. In a local offscreen measurement with a
synthetic root, main-window construction fell from about 3.1 seconds to 0.02
seconds; entering the action library now returns in about 0.02 seconds while
its 36 cards load incrementally. These are source-level measurements, not
installed-app acceptance.

This is a development source update. No installer or installed-app acceptance
has been run for 0.7.4, and the 0.7.3 candidate's acceptance does not certify
this source. Public release, external content review, personal-data transition
and W4 remain separate work.
