# P6-1 Feedback Readiness Gate

生成时间：2026-06-13（Asia/Shanghai）

## 1. 目的

定义 feedback readiness checker，明确一条 feedback row 能否成为 Dynamic Confidence 可学习样本的最小门禁。

不更新权重；不执行学习；不修改生产规则。

## 2. 必填字段门禁

每一条 feedback row 必须满足以下条件，否则判定为 `not learnable`：

| 字段 | 来源 | 缺失处理 |
|---|---|---|
| `statement_id` | feedback 文本 | 缺失 → `not learnable` |
| `rule_id` | statement_records[statement_id] | 缺失 / UNMAPPED → `not learnable` |
| `family_id` | statement_records[statement_id] | 缺失 / UNMAPPED → `not learnable` |
| `school` | statement_records[statement_id] | 缺失 / UNMAPPED → `not learnable` |
| `canon` | statement_records[statement_id] | 缺失 / UNMAPPED → `not learnable` |
| `rule_type` | statement_records[statement_id] | 缺失 / UNMAPPED → `not learnable` |
| `verdict` | parser（`hit` / `miss` / `no_data`） | `no_data` → `not learnable` |

注意：

- 字段名 `verdict` 在本设计中指 learning verdict（`hit` / `miss`）。
- `pending` 不存在；`?` 与 `skip` 直接映射为 `no_data`。
- `UNMAPPED` 字面开头的字段值一律视为 not learnable。

## 3. 判定函数

```python
def is_learnable(feedback_row, statement_record) -> tuple[bool, str | None]:
    if not feedback_row.statement_id:
        return False, "statement_id_missing"
    if not statement_record:
        return False, "statement_id_not_found"
    for field in ("rule_id", "family_id", "school", "canon", "rule_type"):
        value = str(statement_record.get(field) or "").strip()
        if not value or value.upper().startswith("UNMAPPED"):
            return False, f"{field}_missing_or_unmapped"
    if feedback_row.verdict not in ("hit", "miss"):
        return False, "pending_or_no_data"
    return True, None
```

## 4. 检查器形态

`feedback_readiness_check.py` 接受单 case 或批量 case，并对每条 feedback row 输出：

```json
{
  "case_id": "C-2026-XXX-乾-四柱",
  "statement_id": "S-...",
  "verdict": "hit",
  "learnable": true,
  "reason": null,
  "missing_fields": []
}
```

不可学习示例：

```json
{
  "case_id": "C-2026-XXX-乾-四柱",
  "statement_id": "S-...",
  "verdict": "no_data",
  "learnable": false,
  "reason": "pending_or_no_data",
  "missing_fields": []
}
```

## 5. reason 取值

| reason | 含义 |
|---|---|
| `statement_id_missing` | feedback 行无 `statement_id` 标注。 |
| `statement_id_not_found` | feedback 标注存在，但 statement_records 找不到。 |
| `rule_id_missing_or_unmapped` | record 缺 rule_id 或为 UNMAPPED。 |
| `family_id_missing_or_unmapped` | record 缺 family_id 或为 UNMAPPED。 |
| `school_missing_or_unmapped` | record 缺 school 或为 UNMAPPED。 |
| `canon_missing_or_unmapped` | record 缺 canon 或为 UNMAPPED。 |
| `rule_type_missing_or_unmapped` | record 缺 rule_type 或为 UNMAPPED。 |
| `pending_or_no_data` | verdict 不是 hit/miss。 |
| `invalid_verdict` | 标注无法识别。 |

## 6. 行为约束

- checker 不写任何 case 目录、theory 目录或 META 索引文件。
- checker 输出可直接供 [`META/dynamic-confidence-readiness.md`](dynamic-confidence-readiness.md) 消费。
- checker 必须支持 `--dry-run` 与 `--format json`。
- checker 不得使用 [`tools/feedback_loop._apply_rule_verdicts()`](../tools/feedback_loop.py) 任何副作用函数。

## 7. 与 `learning_sample_builder` 的关系

| 维度 | builder | readiness checker |
|---|---|---|
| 写入 | `learning_samples.json` | 不写 |
| 修改 statement_records | 不修改 | 不修改 |
| 修改 feedback | 不修改 | 不修改 |
| 累计学习样本数 | 是 | 否（仅分类） |
| 可触发 Dynamic Confidence | 否 | 否 |
| 主要输出 | 学习样本 envelope | 分类与缺失字段统计 |

checker 是 builder 的前置审计工具，可独立运行，也可与 builder 串联：

```text
feedback_readiness_check
  -> 输出 not_learnable 分类
  -> builder 仅消费 learnable=true 的行
```

## 8. P6-1 阶段目标

- 文档已定义。
- 实际工具运行尚未实现，仍需 P6-2 阶段落实。
- 当前判定：**CONTRACT_READY / RUNTIME_PENDING**。
