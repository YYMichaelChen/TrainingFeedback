# Initial Exercises And Plan Proposal

Status: approved catalog scope; bundled guidance v1 and plan remain drafts pending review and confirmation\
Last updated: 2026-09-11

This document defines the first catalog candidates and the initial plan used to
develop and validate the application. It is not a medical assessment and its
example doses are not automatically treated as a confirmed prescription.

The [development plan](development-plan.md) defines review, activation, history,
and release requirements. This document owns seed names, body areas, and proposed
doses; it does not certify that bundled guidance has passed expert review.

## 1. Canonical Naming

`臀桥` is the canonical exercise. `常规臀桥` is an alias of the same object.
They must not produce duplicate catalog entries, split history, or separate AI
statistics.

## 2. Approved Launch Catalog

The current seed contains the 14 exercises below: seven main and seven
supporting exercises. Second-batch candidates are not seeded.

### Main Training Exercises

| Canonical name | Aliases | Role | Primary next-day areas | Secondary guidance areas | Initial dose unit |
| --- | --- | --- | --- | --- | --- |
| 臀桥 | 常规臀桥 | Glute strength | 臀部 | 大腿后侧、核心 | reps |
| 蚌式开合 |  | Hip-abduction strength | 臀部 | 髋部、核心 | reps per side |
| 椅子深蹲 |  | Squat pattern | 大腿前侧、臀部 | 核心 | reps |
| 死虫式 |  | Anterior core control | 核心 | 髋部 | reps per side |
| 蝴蝶臀桥 |  | Glute bridge variation | 臀部 | 大腿内侧、核心 | reps |
| 跪姿臀冲 |  | Hip-extension strength | 臀部、核心 | 大腿前侧 | reps |
| 静态臀桥 |  | Isometric hip extension | 臀部、核心 | 大腿后侧 | seconds |

### Supporting Exercises

| Canonical name | Role | Primary guidance areas | Secondary guidance areas | Training phase | Creates soreness prompt by default |
| --- | --- | --- | --- | --- | --- |
| 仰卧360°膈肌呼吸 | Breathing and trunk preparation/recovery | 核心 | 胸廓 | preparation or cooldown | no |
| 小幅猫牛式 | Spinal mobility and trunk control | 背部 | 核心、颈部 | preparation | no |
| 坐姿90/90髋转换 | Hip rotation mobility | 髋部 | 臀部、大腿内侧 | preparation | no |
| 蝴蝶式 | Inner-thigh and hip cooldown | 大腿内侧 | 髋部 | cooldown | no |
| 仰卧4字臀部拉伸 | Glute stretch | 臀部 | 髋部 | cooldown | no |
| 半跪髋屈肌拉伸 | Front-hip stretch | 髋前侧 | 大腿前侧、核心 | cooldown | no |
| 站立体前屈 | Posterior-chain cooldown | 大腿后侧 | 臀部、背部 | cooldown | no |

Second-batch supporting candidates:

- 扶墙小腿拉伸;
- 仰卧单膝抱胸.

They may be added after the first workflow is stable. They are not required for
the initial plan.

## 3. Guidance Completion Requirements

Every launch-catalog exercise must have the following content before the first
usable release:

- purpose;
- primary and secondary body areas;
- starting position;
- ordered movement steps;
- breathing;
- tempo or hold guidance;
- intended sensations;
- common compensations;
- stop criteria;
- regression;
- progression;
- equipment;
- applicability and cautions;
- image or explicit image-missing state.

The old project may be consulted manually, but the completed guidance belongs
to this repository's own seed data and must not be loaded from the old runtime.

Current implementation: `data/seed/catalog.py` owns exercise-specific bundled
guidance v1 for all 14 launch exercises. Each item has a stable bundled exercise
key and content identity/version, `review.status = draft`, blank review facts,
and an explicit missing-image state. New roots receive these drafts directly;
existing roots receive selected drafts only through the local preview and
acceptance action. Required-field validation still does not constitute content
review. Record real external review evidence and obtain explicit user approval
before activation. Bundled metadata must never represent an expert review,
user approval, or confirmed exercise dose.

## 4. Initial Plan Proposal

Plan name: `臀腿与核心基础`\
Day name: `基础训练日`\
Purpose: validate preparation, unequal/equal set models, repetitions, per-side
work, timed holds, exercise results, next-day prompts, and external AI export.

The proposed sequence is:

| Order | Phase | Exercise | Proposed sets | Rest proposal |
| --- | --- | --- | --- | --- |
| 1 | preparation | 仰卧360°膈肌呼吸 | 2 sets x 5 breaths | 30 s |
| 2 | preparation | 小幅猫牛式 | 1 set x 6 reps | 30 s |
| 3 | preparation | 坐姿90/90髋转换 | 2 sets x 6 reps per side | 30 s |
| 4 | main | 臀桥 | 12 / 12 / 10 reps | 60 s |
| 5 | main | 蚌式开合 | 2 sets x 12 reps per side | 45 s |
| 6 | main | 椅子深蹲 | 2 sets x 10 reps | 60 s |
| 7 | main | 死虫式 | 2 sets x 8 reps per side | 45 s |
| 8 | main | 静态臀桥 | 2 sets x 20 seconds | 45 s |
| 9 | cooldown | 蝴蝶式 | 2 sets x 30 seconds | 20 s |
| 10 | cooldown | 半跪髋屈肌拉伸 | 2 sets x 30 seconds per side | 20 s |
| 11 | cooldown | 站立体前屈 | 2 sets x 20 seconds | 20 s |

These values exist to exercise the software model. Before this plan becomes a
real active plan, the application must present it for explicit confirmation or
replace it with a plan returned by an external AI expert.

`data/seed/plans.py` creates this one-day proposal as a draft. Draft creation
may reference exercises whose guidance is still awaiting review. Activation
requires all referenced exercises to have approved active guidance and the user
to confirm the full prescription; an external expert's replacement also goes
through this confirmation flow. Reopening the application does not overwrite
existing seed entries or reset a user's plan to this proposal.

## 5. Launch Catalog Versus Initial Plan

The launch catalog intentionally includes `蝴蝶臀桥` and `跪姿臀冲`, while the
initial plan does not prescribe them. They are available for later replacement
or progression without forcing three similar hip-extension variants into the
same session.

Possible later substitutions include:

```text
臀桥 -> 蝴蝶臀桥
臀桥 -> 跪姿臀冲
静态臀桥 -> 跪姿臀冲
```

An external expert must give the actual reason for a substitution. These are
capability examples, not automatic progression rules.

## 6. Next-Day Prompt Derivation For This Plan

For this proposal, only performed main-training exercises contribute prompts.
`completed`, `exceeded`, and `partial` count as performed; `not_completed` does
not. The source is the session's frozen body-area and participation snapshots,
so later catalog edits cannot change the prompts:

- 臀桥 -> 臀部;
- 蚌式开合 -> 臀部;
- 椅子深蹲 -> 大腿前侧、臀部;
- 死虫式 -> 核心;
- 静态臀桥 -> 臀部、核心.

If all five main exercises were performed, the deduplicated prompts are:

```text
臀部
大腿前侧
核心
```

Each prompt offers:

```text
明显酸胀，影响活动
有点酸胀
没有明显感觉
不适/伤病
```

No choice is preselected. One optional overall note follows all body-area
questions.

If only some main exercises were performed, show only the corresponding subset
of these areas.

## 7. Revision Example

The system must be able to represent this evidence chain without overwriting
history:

```text
Plan revision 1: 臀桥 2 x 15 reps
Execution: completed as planned
Next day: 臀部没有明显感觉
External expert rationale: increase repeat dose based on completed work and feedback
Plan revision 2: 臀桥 2 x 20 reps
```

The application records and exports this chain. It does not infer by itself
that lack of soreness always means ineffective training, nor does it suppress a
confirmed increase merely because historical health context exists.
