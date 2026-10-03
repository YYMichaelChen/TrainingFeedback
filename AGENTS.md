# Project Agent Rules

TrainingFeedback is a native PySide6 Windows application with its own SQLite
data root. The old `Exercises@home` repository is reference material only.

## Hard invariants

- Never discover, open, migrate or modify the old training database. Do not add
  Streamlit, wardrobe management, LAN/mobile access or old submission-package
  compatibility.
- Keep user data separate from application binaries. Tests and acceptance use
  isolated synthetic roots, never real user data.
- Preserve user text verbatim. Defaults are not user facts; unknown is not zero.
  Freeze facts needed to interpret completed sessions. Synthetic training and
  approvals never become personal facts.
- UI contains no SQL or business rules. A session controller owns training
  execution state. Writes completing one user action are transactional.
- `not run` is not `pass`. Candidate evidence certifies only its exact build.
  A local candidate does not establish public acceptance, external content
  review, W4 or personal-use readiness.

## Authority

| Question | Authoritative source |
| --- | --- |
| Documentation routing and authority ownership | `docs/README.md` |
| Product behavior, release gates, retention and personal transition | `docs/development-plan.md` |
| Proposed catalog content and initial plan | `docs/initial-exercises-and-plan.md` |
| Current application/schema implementation map and release history | `docs/history/README.md` and `docs/history/<version>/` |
| Development, local release, version rotation and release close procedure | `docs/development-workflow.md` |
| Pytest commands, tiers, scope and budget accounting | `tests/README.md` |
| Installed and public acceptance | `docs/packaged-acceptance-runbook.md` |
| Content review, personal transition and W4 procedure | `docs/guidance-review-runbook.md` |
| Active release execution state | `.planning/releases/<version>/PLAN.md`, projected into `.planning/INDEX.md` |

Tracked `docs/` owns requirements and formal evidence. Local Planscope owns
execution context. A PLAN task cannot change product policy; planning archives
are historical context and never override tracked requirements.

## Context routing and Planscope usage

- Micro edit: read the affected file; use `.planning/INDEX.md` only if release
  context might matter. Do not create planning noise.
- Normal development: read `INDEX.md`, the relevant active PLAN section and
  affected tracked requirements. Search `KNOWLEDGE.md` only for a relevant
  existing finding.
- Complex feature, migration or release: read `INDEX.md`, active PLAN current
  state and phase, relevant KNOWLEDGE sections and tracked requirements. Read
  `PROJECT.md` for a relevant cross-release decision only.
- Recovery: `INDEX.md` → PLAN current state → Git state → search KNOWLEDGE →
  recent LOG only if needed. Do not load archives or all planning files by default.
- `PLAN.md` owns the active phase, task, blockers and next action. After changing
  these, run the installed Planscope `plan.py sync`; do not hand-edit their INDEX
  projection. Keep one active release. Use KNOWLEDGE only for findings future
  work cannot reliably recover, and LOG only for recent recovery context.
- If `.planning/INDEX.md` is absent, the clone remains valid: use tracked docs
  and Git state. Initialize Planscope only when work warrants durable planning;
  never infer an active release from stale historical files. Keep `.planning/`
  local and its archives within the product's retention window.

## Engineering boundaries

- `src/training_feedback/domain/` contains pure rules; `application/` owns use
  cases; `data/` owns SQLite and root lifecycle; `ui/` owns PySide6. Startup is
  `main.py` → `bootstrap.py` → `app.py` → `ui/main_window.py`.
- Deliberate development exercises, guidance and illustrations belong in owned
  source and the built-in catalog before a development root is retired. Only
  the user can authorize the personal-data transition.
- Use PowerShell 7 for project commands and `apply_patch` for manual edits.

## Verification entry points

当前长期个人使用阶段，严格遵循 `docs/development-plan.md` 第 9.1 节：
每次开发更新自动测试最多 3 项，通常 0～1 项；仅限本次改动有具体因果关系的
“应用打不开”风险，无此风险及纯文档更新均为 0 项。参数化、独立场景和脚本
功能验证均计数，不拆任务／scope 或合并场景绕限；通过即停止，修复后只重跑
失败或直接受影响的原检查并记录次数。旧测试库和工具容量不构成运行许可。
人工测试默认 0 项；仅在代码无法确认具体启动风险时，最多在下次正常使用观察
一次能否打开。不得要求批量手测、录屏、计时、重复安装卸载或完整模拟流程。
其它问题随使用反馈修复；打包、版本升级、个人使用和收尾均不扩大测试范围。
取消的检查不记通过，也不作为待补任务或收尾阻塞。GitHub Releases 是安装包和
后续更新的默认分发渠道；发布附件不自动增加测试量，也不自动声明正式兼容支持。


Do not use computer use, GUI automation, remote-control tools, scripted clicks
or keystrokes, or similar capabilities to directly test client functionality.
If the one permitted startup observation is needed, the developer operates the
client and supplies the result. Code-level checks do not certify client behavior.
Unobserved behavior is not a pass; cancelled checks are not outstanding work.
Do not use this client-operation boundary to require additional manual checks.

手动验收清单必须用简单易懂的中文，按实际操作顺序分步写清楚要求。
遵循 `docs/packaged-acceptance-runbook.md` 的“手动验收清单写法”：交代准备、
具体操作、预期结果、失败判断和反馈内容；不能只给编号、术语或概括表格。

Classify development, GitHub Release distribution, user-declared formal release,
explicit public support commitments and application-version rotation by event. Follow
`docs/development-workflow.md`, the release policy in `docs/development-plan.md`
and `tests/README.md`; the current startup-only cap applies to every development
update regardless of event, and test-scope accounting must not evade it. Do not infer
compatibility, formal-release, public-release or personal-data status from a
version number or installer build. A normal code change does not require an
installer. A schema or external wire-schema revision requires an application
patch-or-greater bump in the same change. Reject unsupported or future roots
unchanged before writes.

## Task completion report

Report changed files, actual verification and unrun checks, application/schema/
catalog/contract impact, candidate limits, and Planscope state changes when used.
