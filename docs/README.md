# TrainingFeedback Documentation

This is the durable documentation entry point. Local `.planning/INDEX.md`
routes current execution work; this file routes tracked project authority.

## Current state

- Current application: `0.8.12`
- Current database schema: `24`
- Current plan/evidence contract: `4`
- Current catalog: `070-illustrated-3`
- Current development release: [`0.8.12`](releases/0.8.12/design.md)
- GitHub distribution: `v0.8.12`
- Formal compatibility baseline declared: no

## 当前验证政策

本项目长期供用户本人使用。安装和更新统一通过 GitHub Releases 分发；
该渠道不自动建立正式兼容支持承诺，也不扩大测试范围。
[产品规范第 9.1 节](development-plan.md#91-release-and-follow-up-boundaries)
规定：每次更新只允许检查具体启动失败风险，最多 3 项，通常 0～1 项；
无此风险为 0 项。人工测试默认 0 项，其它问题随使用反馈逐步修复。
安装包、版本升级、个人使用和收尾不自动增加验收；已取消的检查不再是待办。

## Read this for...

| Need | Authoritative document |
| --- | --- |
| Product, domain, data-root and release rules | [Product specification](development-plan.md) |
| Catalog content and initial-plan proposal | [Catalog and plan specification](initial-exercises-and-plan.md) |
| Current release design | [v0.8.12 design](releases/0.8.12/design.md) |
| Action-detail and guidance reading design implemented in v0.8.11 source | [动作详情与指导阅读重新设计](designs/exercise-reading-redesign.md) |
| Development, verification, version rotation and release close | [Development workflow](development-workflow.md) |
| Pytest tiers, scopes and budget accounting | [Test instructions](../tests/README.md) |
| Minimal startup observation; dormant public acceptance | [Packaged acceptance runbook](packaged-acceptance-runbook.md) |
| Content review, personal transition and W4 | [Guidance review runbook](guidance-review-runbook.md) |
| Current application/schema/catalog/contract identity and candidate status | [Version history](history/README.md) |
| Runtime plan-contract schemas | [`src/training_feedback/contracts/`](../src/training_feedback/contracts/) |
| Historical contract examples and frozen baselines | [Contract reference artifacts](reference/contracts/README.md) |
| Image-production prompts | [Image prompt assets](../content/image-prompts/README.md) |
| Agent routing and hard invariants | [`AGENTS.md`](../AGENTS.md) |

## Document classes

- **Specification** states what the product must mean now.
- **Procedure** states how maintainers perform and record work.
- **Design / release design** describes intended changes and is not current product truth.
  An unassigned design does not open a release or change application identity.
- **Evidence** records what happened for an exact version or candidate.
- **Historical reference** preserves superseded context without governing current behavior.
- **Reference/content artifact** supports implementation or content production without owning policy.

## Authority rule

One durable rule has one authoritative home. If another document needs the
rule, it links to the authority and keeps only the local context needed to carry
out its own procedure. Planscope owns execution state, not product policy,
public procedures or release evidence.
