# TrainingFeedback Documentation

This is the durable documentation entry point. Local `.planning/INDEX.md`
routes current execution work; this file routes tracked project authority.

## Current state

- Current application: `0.8.0`
- Current database schema: `23`
- Current plan/evidence contract: `3`
- Current catalog: `070-illustrated-3`
- Current planned release: [`0.8.0`](releases/0.8.0/design.md)
- Formal release declared: no

## Read this for...

| Need | Authoritative document |
| --- | --- |
| Product, domain, data-root and release rules | [Product specification](development-plan.md) |
| Catalog content and initial-plan proposal | [Catalog and plan specification](initial-exercises-and-plan.md) |
| Current release design | [v0.8.0 design](releases/0.8.0/design.md) |
| Development, verification, version rotation and release close | [Development workflow](development-workflow.md) |
| Pytest tiers, scopes and budget accounting | [Test instructions](../tests/README.md) |
| Installed and public acceptance | [Packaged acceptance runbook](packaged-acceptance-runbook.md) |
| Content review, personal transition and W4 | [Guidance review runbook](guidance-review-runbook.md) |
| Current application/schema/catalog/contract identity and candidate status | [Version history](history/README.md) |
| Runtime plan-contract schemas | [`src/training_feedback/contracts/`](../src/training_feedback/contracts/) |
| Historical contract examples and frozen baselines | [Contract reference artifacts](reference/contracts/README.md) |
| Image-production prompts | [Image prompt assets](../content/image-prompts/README.md) |
| Agent routing and hard invariants | [`AGENTS.md`](../AGENTS.md) |

## Document classes

- **Specification** states what the product must mean now.
- **Procedure** states how maintainers perform and record work.
- **Release design** describes intended changes and is not current product truth.
- **Evidence** records what happened for an exact version or candidate.
- **Historical reference** preserves superseded context without governing current behavior.
- **Reference/content artifact** supports implementation or content production without owning policy.

## Authority rule

One durable rule has one authoritative home. If another document needs the
rule, it links to the authority and keeps only the local context needed to carry
out its own procedure. Planscope owns execution state, not product policy,
public procedures or release evidence.
