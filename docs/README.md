# TrainingFeedback Documentation

This is the durable documentation entry point. Local `.planning/INDEX.md`
routes current execution work; this file routes tracked project authority.

## Current state

- Current application: `0.8.25`
- Current database schema: `26`
- Current plan/evidence contract: `5`
- Current catalog: `070-illustrated-3`
- Current development release: [`0.8.25`](designs/project-review-roadmap-2026-10.md)
- GitHub distribution: `v0.8.21`
- Formal compatibility baseline declared: no

## 后续版本安排

`0.8.25` 按[全项目审视与版本安排](designs/project-review-roadmap-2026-10.md)
处理历史摘要读取、根打开协调、包资源声明、当前测试硬限制和规范一致性。
实际交付事实归版本历史；规划文档不代替实现与候选证据。

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
| Review findings and assigned future versions 0.8.22–0.8.25 | [全项目审视与版本安排](designs/project-review-roadmap-2026-10.md) |
| Catalog content and initial-plan proposal | [Catalog and plan specification](initial-exercises-and-plan.md) |
| Current release design | [v0.8.25 long-term reading and maintenance scope](designs/project-review-roadmap-2026-10.md) |
| Separate action addition and plan saving; Save As plan-file templates | [0.8.20 开发记录](history/0.8.20/development.md) |
| Action-detail and guidance reading design implemented in v0.8.11 source | [动作详情与指导阅读重新设计](designs/exercise-reading-redesign.md) |
| Plan editor sizing and local scale source follow-up | [计划界面相对尺寸与缩放](designs/plan-interface-scaling.md) |
| Compact default window and independent action frames | [源码跟进](history/0.8.14/compact-interface-2026-10-08.md), [0.8.15 交付记录](history/0.8.15/development.md) |
| Default training-button widths and centered gallery captions | [0.8.16 交付记录](history/0.8.16/development.md) |
| Plan drag ordering and default inline editing source follow-up | [计划编辑源码跟进](history/0.8.16/plan-editor-follow-up-2026-10-09.md) |
| Published plan-editor fix and candidate identity | [0.8.17 交付记录](history/0.8.17/development.md) |
| Compact plan-editor columns and scrollbars | [0.8.18 交付记录](history/0.8.18/development.md) |
| Long names, switch overhead, drag insertion, group doses and bounded save confirmation | [计划编辑源码跟进](history/0.8.18/plan-editor-follow-up-2026-10-17.md) |
| Chinese client errors, validation locations and system-error presentation | [报错中文映射源码跟进](history/0.8.18/error-localization-2026-10-17.md) |
| Incomplete drafts, strict plan-file import and Chinese client text | [功能设计](designs/plan-drafts-import-and-chinese.md), [0.8.19 开发记录](history/0.8.19/development.md) |
| Alternating actions: counting, execution order and actual records | [左右交替动作设计](designs/alternating-side-prescriptions.md)、[0.8.21 开发记录](history/0.8.21/development.md) |
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
