# 命局裁决入口改造状态（2026-10-07）

## 当前交付

本轮将命盘事实接入现有 L2 结构命题 runner，并保留完整候选集合：

```text
ChartFactLedger
  → cfv-v1
  → 已登记的 structure.overview runner
  → ClaimCandidateSet
  → ChartAdjudication
```

`ChartAdjudication` 只表示原局结构命题的工程裁决状态，不是现实结果，也不代表理论已经验证。它保留：

- 原局事实账本；
- 每个学派和任务的完整 Claim 集合；
- 规则证据、适用条件和 falsifier；
- 按 `target_id` 分组后的 L6 裁决；
- `primary`、`partial`、`unresolved`、`abstain`、`unsupported` 状态。

不同目标的结构 Claim 可以在同一命局中并存为主断；只有同一目标存在未解决竞争时才输出 `unresolved`，若其他目标已有主断则输出 `partial`。系统不按 claim ID、置信度、规则数量或学派数量选优。

## 阶段边界

| 阶段 | 状态 | 说明 |
|---|---|---|
| P0 命盘事实 → 命局候选 | 完成 | `generate_chart_adjudication()` 已提供 chart-only 入口 |
| P1 候选保留与弃断 | 完成 | `generate_claim_candidates()` 保留全部候选；旧盲测适配遇到竞争时 abstain |
| P2 学业有成测量草案 | Draft | 候选对象为 `education.academic_achievement`；映射未解决、未冻结 |
| P3 现实测量冻结/揭示/评分 | 暂不接入 | 现有通用基础契约可用，但没有获批的 Measurement Spec，不启动现实 pilot |
| P4 报告/反馈分层 | 暂不改生产报告 | 现有报告管线含已知事实输入，不能冒充 chart-only 盲断产物 |

## 不得越过的闸门

在 `academic-achievement-v0.1-proposal.md` 仍为 Draft、Mapping Status 为 `UNRESOLVED` 时：

1. 不把成果字段直接定义为“学业有成”；
2. 不冻结 Measurement Spec；
3. 不生成现实 outcome 标签；
4. 不启动 blind pilot；
5. 不把现实结果、反馈或报告输入 chart-only 入口。

后续只有在 Measurement Spec 另行获批并冻结后，才可以把对应的观察、揭示和评分接到现有通用评估契约。该步骤不改变已经冻结的理论或结构命题。
