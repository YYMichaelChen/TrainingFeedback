# v0.7.8 Documentation And Knowledge Governance

Date: 2026-09-30

## Scope

This application-only patch reorganizes documentation authority and fixes known
factual drift. It does not change product behavior, database schema, catalog
content or external wire contracts.

The change:

- adds `docs/README.md` as the durable documentation router and exposes current
  implementation/target status in the root README;
- relocates the v0.8.0 design, image-production prompts and contract reference
  artifacts according to their lifecycle;
- keeps current runtime schemas canonical under
  `src/training_feedback/contracts/` and removes documentation mirrors;
- corrects stale source references and current plan/evidence contract wording;
- moves the full one-time v0.7.5 schema-22 reset design into version history;
- narrows procedure and agent documents to links where the product specification
  owns policy;
- adds `packaging/check_docs.py` and a pytest entry point for documentation links,
  repository paths, identity consistency and contract ownership.

## Identity impact

| Identity | v0.7.8 |
| --- | --- |
| Application | 0.7.8 |
| Database schema | 23 (unchanged) |
| Catalog | 070-illustrated-3 (unchanged) |
| Plan/evidence contract | 3 (unchanged) |

## Verification

This task directly forms the v0.7.8 update, so automated pytest uses patch tier
and the single stable scope `release-0.7.8`. Before execution, collection selected
15 unique cases covering the new documentation checker, moved contract examples
and frozen baselines, the canonical current schema, and the root-switch fixture
that consumes the moved v3 example. Unchanged product workflows and the rest of
the resident regression suite are lower-risk exclusions because no runtime
behavior, schema, catalog or wire contract changed; exclusions are not passes.

Results:

- `15 passed in 1.15s` under patch tier and scope `release-0.7.8`.
- `python packaging/check_docs.py`: passed for 25 tracked/new Markdown files.
- Ruff on changed Python/source/test files: passed.
- `git diff --check`: passed; Git reported only the repository's normal Windows
  line-ending conversion notices.
- Planscope `compact` and `doctor`: passed with no failures or warnings.

No installer candidate was built. Installer, packaged acceptance, manual client,
public acceptance, external content review, W4 and personal-use checks were
`not run`; this update does not claim them.
