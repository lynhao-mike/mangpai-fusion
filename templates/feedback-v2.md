# 案例反馈模板（v2）

## 字段约定

- `case_id` 必填，对应 `cases/<case_id>/` 目录名。
- `命主性别` 必填，填写 `M` 或 `F`。
- `命主出生` 必填，格式 `YYYY-MM-DD HH:MM`。
- 每条 statement 反馈行格式：

```
- [<statement_id>] <statement_text>
  - 反馈 (y/n/skip/pending)：<y|n|skip|pending>
  - 备注（可选）：<free text, 不要重复 verdict>
```

## verdict 含义

| verdict | 含义 | 是否进入学习通道 |
|---|---|---|
| `y` | 该 statement 与实际事件一致 | 是 |
| `n` | 该 statement 与实际事件不一致 | 是 |
| `skip` | 命主无可核验信息 / 不愿披露 | 否 |
| `pending` | 尚未收集到反馈 | 否 |

## 校验

- 反馈中出现的 `[S-xxxx]` 必须存在于对应 `cases/<case_id>/statement_records.json::records`。- 不存在的 `statement_id` 在 normalized 副本中标记为 `INVALID_STATEMENT_ID`，并整体从学习通道中剔除。
- verdict 字段只接受 `y` / `n` / `skip` / `pending`，其他值在摄入阶段被拒绝。
