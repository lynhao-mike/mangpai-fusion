# 双核多轮盲测与规则统计契约 v1

> 本契约定义多轮盲测封存、复核/预测分离和规则统计。它不替代 [`20-domain-prospective-evaluation-v1.md`](20-domain-prospective-evaluation-v1.md) 的既有离线单次评估制品，也不授权生产规则、权重或路由自动变更。

## 1. 记录边界

每个盲测轮次和封存后的核验记录只使用以下结构化字段：

```yaml
record:
  case_id: "案例标识"
  round_index: 1
  matter_category: "career"
  time_scope: "natal"
  direction: "positive"
  conclusion: "本轮结论"
  rationale: "推理理由"
  applied_rules:
    - rule_id: "规则标识"
      school: "ziping"
      rule_direction: "positive"
      rule_statement: "所用断语"
```

- `matter_category`：`career`、`wealth`、`marriage`、`health`、`education`、`family`。
- `direction` 与 `rule_direction`：`positive`、`negative`、`mixed`。
- `time_scope`：`natal`、具体大运或流年区间。
- 不保存完整对话、检索过程或重复命盘事实。

规则修改标记分组键固定为：

```text
(rule_id, matter_category, rule_direction)
```

## 2. 轮次职责

- Round 1 必须通过 [`tools/as_of_theory_lookup.py`](../../tools/as_of_theory_lookup.py) 检索子平、滴天髓、段、任、杨、高的候选规则，并保留各规则独立初断。
- 后续轮次只对候选规则做适用域辩证、淘汰和收敛。
- 最后一轮形成该事项的唯一交付结论。
- 所有轮次在首次揭示核验资料时一并封存，之后不可修改。

## 3. 去重与仲裁

唯一统计单元：

```text
(case_id, matter_category, rule_id)
```

- 同一案例、同一事项中的重复触发只计一次。
- 同一规则在不同事项中分别计数。
- 规则曾在任一盲测轮次触发，但未进入该事项最后一轮，或其方向与最终 `direction` 相反，计一次仲裁推翻。

```text
仲裁错杀率 = 独立命中且被推翻次数 / 被推翻总次数
仲裁纠偏率 = 独立未命中且被推翻次数 / 被推翻总次数
```

分母为零时比率为空，不得记为 0。独立未命中进入“适用域需收窄”待审池；独立命中但被推翻进入“裁决优先级需复核”待审池。两类都只待命理师确认，不自动生效。

## 4. 触发器证据

未知 trigger 不得返回命中。[`trigger_evidence_status()`](../predicates/condition_evaluator.py:130) 对未知项返回 `insufficient_evidence`，[`evaluate_trigger()`](../predicates/condition_evaluator.py:153) 返回 `False`。仅有干支字面重合不能当作适用条件已满足。
