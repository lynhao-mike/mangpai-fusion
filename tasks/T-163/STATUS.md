# T-163 STATUS

- 状态：✅ **已验收**（2026-10-29 00:50，中枢亲自复跑）
- 执行者：子代理 O
- 任务卡：`tasks/T-163/PROMPT.md`
- 简报：`tasks/T-163/BRIEF.md`（Worker 写）
- 验收：中枢亲自跑；v1 不得被覆盖

## Execution Log

| 时间 | 动作 |
|---|---|
| 00:55 | 中枢建卡并派发；与 T-161/T-162 并行，File Scope 无重叠 |
| 00:48 | 子代理 O：`--out-prefix` + 路径处理完成；新测试 `6 passed`；tmp 前缀实跑 exit 0；v1 `git status` 空、SHA256 未变；全量 pytest `1260 passed, 1 skipped`。⚠️ 卡 §5「与 v1 数值一致」不成立：当前 YAML 重跑 = v2 数值（2219/965/379/185），v1 为 T-156 修复前（2219/965/1818/641），详见 BRIEF §3.1。 |
| 00:50 | 中枢验收：`--out-prefix $env:TEMP\t163-verify` 实跑 exit 0；与 v2 **逐条数值一致**（same_numbers=True，totals 965/965/379/185）；v1 JSON 哈希仍 `E3ED1318…`、`git status` 空；6 tests passed。裁决：卡 §5 改为对照 v2，写入卡 §6。提交 |

## Blockers / 风险

- **已裁决**：卡 §5「与 v1 数值一致」不成立——v1 是 T-156 之前的产物，当前 YAML 重跑得到 v2 数值。
  验收改为「与 v2 逐条一致 + v1 零改动 + 两次运行一致」；已写入卡 §6。
- **默认无参数仍写 v1**（兼容行为）：调用方必须显式 `--out-prefix`；建议下一版加「目标已存在则拒绝，
  除非 `--force`」，本卡不改默认。
