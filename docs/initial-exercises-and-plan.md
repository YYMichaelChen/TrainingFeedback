# Initial Exercises And Plan Proposal

Status: approved catalog scope; proposed doses require user or external-expert
confirmation before activation\
Last updated: 2026-09-04

This document defines the first catalog candidates and the initial plan used to
develop and validate the application. It is not a medical assessment and its
example doses are not automatically treated as a confirmed prescription.

## 1. Canonical Naming

`臀桥` is the canonical exercise. `常规臀桥` is an alias of the same object.
They must not produce duplicate catalog entries, split history, or separate AI
statistics.

## 2. Approved Launch Catalog

### Main Training Exercises

| Canonical name | Aliases | Role | Primary next-day areas | Initial dose unit |
| --- | --- | --- | --- | --- |
| 臀桥 | 常规臀桥 | Glute strength | 臀部 | reps |
| 蚌式开合 |  | Hip-abduction strength | 臀部 | reps per side |
| 椅子深蹲 |  | Squat pattern | 大腿前侧、臀部 | reps |
| 死虫式 |  | Anterior core control | 核心 | reps per side |
| 蝴蝶臀桥 |  | Glute bridge variation | 臀部 | reps |
| 跪姿臀冲 |  | Hip-extension strength | 臀部、核心 | reps |
| 静态臀桥 |  | Isometric hip extension | 臀部、核心 | seconds |

### Supporting Exercises

| Canonical name | Role | Training phase | Creates soreness prompt by default |
| --- | --- | --- | --- |
| 仰卧360°膈肌呼吸 | Breathing and trunk preparation/recovery | preparation or cooldown | no |
| 小幅猫牛式 | Spinal mobility and trunk control | preparation | no |
| 坐姿90/90髋转换 | Hip rotation mobility | preparation | no |
| 蝴蝶式 | Inner-thigh and hip cooldown | cooldown | no |
| 仰卧4字臀部拉伸 | Glute stretch | cooldown | no |
| 半跪髋屈肌拉伸 | Front-hip stretch | cooldown | no |
| 站立体前屈 | Posterior-chain cooldown | cooldown | no |

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

## 4. Initial Plan Proposal

Plan name: `臀腿与核心基础`\
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

Only performed main-training exercises contribute prompts:

- 臀桥 -> 臀部;
- 蚌式开合 -> 臀部;
- 椅子深蹲 -> 大腿前侧、臀部;
- 死虫式 -> 核心;
- 静态臀桥 -> 臀部、核心.

The resulting deduplicated prompts are:

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
