# as-of盲断协议
## 目的
反馈揭示前冻结可证伪判断，防止答案污染；仅作人工旁路。

## 新鲜度
[`scan_feedback_current_state()`](../tools/as_of_current_state_scanner.py:100)：最新年≥2024且该年含状态词；结果须人工复核。

## 八步
1. [`truncate_blind_section()`](../tools/as_of_blind_judgment_probe.py:98)+[`detect_table_embedded_annotation()`](../tools/as_of_blind_judgment_probe.py:77)：盲文、截点、污染行。
2. [`compute_age_at()`](../tools/as_of_admission_age_gate.py:54)：截止周岁。
3. [`run_freeze_preflight()`](../tools/as_of_freeze_preflight.py:50)：触发年分层。
4. 理论库查阅（强制）：判定者必须实际调用 [`search_theory()`](../tools/as_of_theory_lookup.py:110)，用候选事件涉及的十神名称与关键动作词组成关键词（例如“食神”+“夺食”、“正官”+“印化”），并审阅返回的命中结果。采纳的至少一条命中必须以 [`TheoryHit.as_citation_line()`](../tools/as_of_theory_lookup.py:62) 的输出写入冻结记录 `theory_evidence`。若尝试相关关键词组合后仍无命中，`theory_evidence` 必须如实记录“已检索关键词X/Y，无命中”；不得留空，也不得为通过门控伪造引用。
5. [`build_freeze_scaffold()`](../tools/as_of_freeze_scaffold.py:78)：基本面、事件草稿。
6. [`run_contract_gate()`](../tools/as_of_contract_gate.py:214)：红线结果；`theory_evidence` 缺失、为空或仅含占位文本时不得冻结。
7. 写冻结包及SHA-256，揭示前后验散列。
8. 独立裁决三评分单元；[`compute_running_stats()`](../tools/as_of_running_stats.py:105)汇总分母、命中。

## 红线
中心“或”少于3；窗口≤14个月；须有“能力存在但兑现不稳”备选；`theory_evidence` 必须包含经审阅采纳的真实检索命中，或包含实际尝试过的关键词及“无命中”结果，禁止缺失、空值和占位文本。

## 揭示裁决
散列通过才读反馈。ABSTAIN=缺证/冲突/窗口未完，不进分母；MISS=充分直接反证，进分母。

## 快照
`stats=compute_running_stats(Path("cases"))`；[`append_stats_snapshot()`](../tools/as_of_running_stats.py:41)：`append_stats_snapshot(stats,Path("META/as-of-stats-history.jsonl"))`。

## 排序
[`rank_remaining_candidates()`](../tools/as_of_candidate_prioritizer.py:57)：`rows=rank_remaining_candidates(Path("cases"))`，按§9.4与scaffold排序后人工复核。