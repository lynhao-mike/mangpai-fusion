# P6-1 First Live Sample Simulation

生成时间：2026-06-13（Asia/Shanghai）

## 1. 目的

只读模拟最近 10 个新案例在“statement_record -> feedback -> learning sample”链路下的可学习样本统计。

不更新权重；不执行学习；不修改生产规则；不写盘。

## 2. 选样口径

按 [`cases/`](../cases/) 目录名 `C-YYYY-NNN-...` 排序，取最大的 10 个正式 case 目录：

```text
排序键：case 目录名字典序
范围：cases/ 下所有以 C- 开头且不属于 _TEMPLATE/raw_feedback 的正式 case
数量：10
```

本次 10 个 case 如下（按字典序）：

| # | case_id | report 归档 | statement_index | statement_records | record_count | feedback_rows | learnable | mapped | unmapped | pending |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | C-2026-RF000963-乾-… | 0 | 1 | 1 | 12 | 0 | 0 | 0 | 0 | 0 |
| 2 | C-2026-RF000965-坤-… | 1 | 1 | 1 | 15 | 0 | 0 | 0 | 0 | 0 |
| 3 | C-2026-RF000968-乾-… | 0 | 1 | 1 | 11 | 0 | 0 | 0 | 0 | 0 |
| 4 | C-2026-RF000970-乾-… | 0 | 1 | 1 | 12 | 0 | 0 | 0 | 0 | 0 |
| 5 | C-2026-RF000975-乾-… | 0 | 1 | 1 | 9 | 0 | 0 | 0 | 0 | 0 |
| 6 | C-2026-RF000977-坤-… | 0 | 1 | 1 | 8 | 0 | 0 | 0 | 0 | 0 |
| 7 | C-2026-RF000980-坤-… | 0 | 1 | 1 | 11 | 0 | 0 | 0 | 0 | 0 |
| 8 | C-2026-RF000986-乾-… | 0 | 1 | 1 | 10 | 0 | 0 | 0 | 0 | 0 |
| 9 | C-2026-RF000989-乾-… | 1 | 1 | 1 | 13 | 0 | 0 | 0 | 0 | 0 |
| 10 | C-2026-RF000990-乾-… | 1 | 1 | 1 | 14 | 0 | 0 | 0 | 0 | 0 |

> 上述 case_id 中含不可显示字符；实际目录名见 [`cases/`](../cases/) 下排序末 10 个 `C-2026-RF000963` 至 `C-2026-RF000990`。

## 3. 汇总

| 指标 | 数量 |
|---|---:|
| case 总数 | 10 |
| 含 report 归档的 case | 3 |
| 含 statement_records.json 的 case | 10 |
| statement_records 记录数 | 115 |
| record 缺字段总数 | 0 |
| 结构化 feedback_rows | 0 |
| learnable samples | 0 |
| mapped feedback_rows | 0 |
| unmapped feedback_rows | 0 |
| pending/no_data rows | 0 |

## 4. 理论可学习样本数

按以下假设进行理论推演，**不是**实际 ingest 落盘结果：

1. 假设所有 10 个新案都获得人工重标反馈（`[S-...] [y/n]` 至少 1 条）。
2. 假设 `statement_records.json` 中每条 record 都完整携带 `rule_id/family_id/school/canon/rule_type`。
3. 假设每案至少 5 条 y/n 反馈（每案 5 条来自 statement_records 内的可见断语）。
4. 假设无额外 unmapped 缺失。

```text
理论可学习样本上限 = 10 case × 5 feedback/case = 50
```

按 [`META/dynamic-confidence-readiness.md`](dynamic-confidence-readiness.md) 阈值：

| 指标 | 理论上限 | 阈值 | 是否达到 |
|---|---:|---:|---|
| learnable_samples | 50 | >= 50 | BORDERLINE |
| y + n | 50 | >= 30 | PASS |
| pending_ratio | 0% | < 50% | PASS |

注意：

- “理论可学习样本上限”是上界，不等于 P6-1 当前的真实样本数。
- 真实状态仍是 0 / 0 / 0，因为没有 case 完成 feedback 重标。
- 50 也只是达到 learnable_samples 阈值的下限；正式 Dynamic Confidence 仍需要更稳定的样本分布。

## 5. 阻断点

1. **feedback 缺失**：10 个新案均无 `feedback.md` 中的 `[S-...] [y/n]` 标注。
2. **builder 未实现**：尚未实现 `learning_sample_builder` 落盘 `learning_samples.json`。
3. **readiness checker 未实现**：未自动化 `not_learnable` 分类与 reason。
4. **无 live y/n 闭环**：无法产生 learning sample → 无法验证 builder 与 checker 行为。

## 6. 与历史 case 区分

- 10 个新 case 均为 RF 系列，由 [`tools/promote_wenzhen_*`](../tools/) 从 [`cases/raw_feedback/`](../cases/raw_feedback/) 转入。
- 它们的 statement_records 来源于 [`tools/render_report.py`](../tools/render_report.py) 同源 render，schema 完整，缺字段数为 0。
- 因此一旦补齐 feedback 行，本批 10 案即可作为“首批可学习样本源”。

## 7. P6-1 阶段判定

`learnable_samples = 0`；`y + n = 0`；`pending_ratio = NaN`（无 feedback rows）。

`ready_for_learning` = `BLOCKED_MULTIPLE`。

P6-2 启动条件：

- 在本批 10 案（或新生成案例）上至少补齐 1 个 case 的 `[S-...] [y/n]` 反馈；
- 实现 `learning_sample_builder` 落盘 `learning_samples.json`；
- 实现 `feedback_readiness_check.py` 输出 not_learnable 分类；
- 重新跑 [`META/dynamic-confidence-readiness.md`](dynamic-confidence-readiness.md) 评估。
