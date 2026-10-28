# T-155 STATUS

- 状态：✅ **已验收**（2026-10-28，中枢独立复算；判定：样本不足）
- 执行者：子代理 H
- 任务卡：`tasks/T-155/PROMPT.md`（卡内 §1 即预注册）
- 简报：`tasks/T-155/BRIEF.md`（Worker 写）
- 验收：中枢亲自跑；342 / **336** 两套敏感性都已报

## Blockers

1. **卡内「7 例 → 335」与现场不符，实际为 336（须中枢裁决，Worker 未改卡）**
   T-153 §9 名单中的 `RF-2026-000947` 冻结标签是 `unknown`（`unknown_reason=neutral`），本就不在 342 分母内；按名单剔除，342 内实际命中 **6** 例 → 敏感性集 **336** 例。要凑 335 必须额外挑一例名单外样本，违反「不许按标签挑案例」，故未凑。已按「名单优先」执行并在报告 §4 如实标注。
   → 建议中枢在卡内 Amendments 说明以 336 为准，或给出第 8 例的 case_id。
2. **敏感性集对计分无影响**：名单命中的 6 例全部 `triggered=false`（无日支冲），两套 n_scored / accuracy / Wilson 完全相同。该敏感性只能证明「判定不依赖这 6 例」，不能检验 scored 集内的标签噪声。
3. 其余无阻塞：建盘失败 0、skipped_edges 0、pytest 1099 passed 1 skipped。

## Execution Log

| 时间 | 动作 |
|---|---|
| 22:55 | 中枢建卡并派发；与 T-154 并行，File Scope 无重叠 |
| 22:31 | 子代理 H：读卡 + AGENTS.md + `tools/m2y395_direction.py` + 标签/评测集结构 + `engine/predicates/types.py`；确认 342 分母 = usable 382 中 label ∈ {negative,positive} |
| 22:33 | 新建 `tools/m2y395_real_direction.py`（import `direction_of`，未复制规则）：382 例全部建盘成功，日支有冲 67 人（17.54%）= self 20 / other 28 / no_ke 19 / ambiguous 0；grep `negative|label|marriage-quality` = 0 命中 |
| 22:34 | 写 `META/eval-protocols/m2y395-v2.yaml`（11 字段，冻结 2026-10-28T22:34+08:00 @ 3c49d91d），再新建 `tools/m2y395_real_score.py` 并入标签计分 |
| 22:36 | 342 全集：n_triggered 60、n_scored 43、n_correct 23、n_abstain 17、accuracy 0.5349、baseline N 0.5814、Wilson [0.3892, 0.6749] → **样本不足**（n_scored<50 硬门槛） |
| 22:37 | 敏感性集：卡写 335，实际命中 6 例 → 336；scored 集不变（命中的 6 例均未触发）→ 同样 **样本不足**；两套不翻转 → 不判「标签不足以裁决」 |
| 22:40 | 自测 4 条命令全部 EXIT=0（direction / score / claim_metric / pytest 1099 passed 1 skipped）；三产物两次运行 SHA-256 一致；抽查 3 人（130/081/034）方向与标签逐项核对一致 |
| 22:42 | 写 `tasks/T-155/BRIEF.md`（四字段），记录 335→336 的口径差异与「点估计低于基线但不满足否证条件」 |
| 23:20 | 中枢验收：direction / score 连跑两次哈希一致；`grep negative|label|marriage-quality` = 0；342/60/43/23、branch 20/23/17、Wilson [0.3892, 0.6749] 逐项复算一致 |
| 23:22 | 中枢裁决 335→**336**：卡 §1.1 已改；6 例全部未触发，敏感性对计分无影响，只能证明「判定不依赖这 6 例」，不能检验 scored 内标签噪声 |
| 23:24 | 最终判定 **样本不足**（n_scored=43 < 50）；未达否证（Wilson 上界 0.6749 > 基线 0.5814）；点估计 0.5349 低于基线；写入 `docs/reviews/m2y395-verdict-v1.md` §8 |

