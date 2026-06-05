# 子平 / 滴天髓候选规则 YAML Schema 扩展草案（旁路审查态）

> 目标：为子平格局派与滴天髓调候派提供候选规则 YAML 的字段约定。
>
> 状态：schema 草案；不修改 [`theory/SCHEMA.md`](../../SCHEMA.md)；不接入生产引擎。

## 1. 设计原则

1. 所有规则初始状态必须为 `candidate`。
2. 规则来源必须可追溯到原文摘录或样板提取稿。
3. 子平与滴天髓使用同一外壳字段，但 `expert_system` 必须隔离。
4. 不允许直接写 `active`、`confirmed`、`promoted`。
5. 不允许把裁判层字段回写为流派内部规则。

## 2. 顶层结构

```yaml
schema_version: review-draft-2026-06-05
status: review_draft
source_scope: bypass_candidate_rules
expert_system: ziping | tiaohou_ditiansui
rules:
  - id: ZP-CAND-20260605-001
    status: candidate
```

## 3. 单条规则字段

| 字段 | 必填 | 类型 | 说明 |
|---|---|---|---|
| id | 是 | string | 规则 ID，子平用 `ZP-CAND-*`，滴天髓用 `DTS-CAND-*` |
| status | 是 | enum | 必须为 `candidate` |
| expert_system | 是 | enum | `ziping` 或 `tiaohou_ditiansui` |
| title | 是 | string | 候选规则标题 |
| topic | 是 | string | 主题，如 `yongshen`、`tiaohou`、`geju` |
| domains | 是 | list | 功能域，如 财富、事业、健康 |
| axis_refs | 是 | list | 对应统一判断轴 |
| claim | 是 | string | 规则提炼断语 |
| conditions.required | 是 | list | 必要条件 |
| conditions.optional | 否 | list | 辅助条件 |
| conditions.exclusions | 否 | list | 排除条件 |
| output.statement | 是 | string | 可输出结论模板 |
| output.falsifiable | 是 | string | 可证伪表达 |
| source.path | 是 | string | 来源文件 |
| source.excerpt | 是 | string | 原文摘录 |
| review.notes | 否 | string | 人工审查备注 |

## 4. 状态机限制

当前旁路 YAML 只允许：

```text
candidate
```

禁止：

```text
active
confirmed
promoted
deprecated
```

其中 `deprecated` 暂不用于新候选规则，避免与生产规则生命周期混用。

## 5. ID 约定

| 系统 | ID 前缀 | 示例 |
|---|---|---|
| 子平 | ZP-CAND | ZP-CAND-20260605-001 |
| 滴天髓 | DTS-CAND | DTS-CAND-20260605-001 |

## 6. 与裁判模型的关系

候选规则只提供专家内部输出的理论依据。裁判模型只读取专家输出后的外壳字段，不直接读取或修改这些候选规则。

## 7. 进入正式 schema 前的审查项

1. 字段是否过多或过少；
2. `axis_refs` 是否足以连接裁判模型；
3. `source.excerpt` 是否足以满足证据链；
4. 是否需要引入 `confidence_seed`；
5. 是否需要为每条候选规则增加 `review_decision`。
