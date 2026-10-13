# 职业路径分类器 v2 一次性冻结评估

> 结论：**FAIL，不晋级**。本报告仅复述已经冻结的一次性评估；评分后未修改分类器、未重写预测、未在同一批次刷分。

## 1. 评估边界与冻结纪律

- 同一 P 系列 40 案 cohort：37 个严格二分类样本 + 3 个 mixed holdout。
- 预测阶段只消费四柱、大运序列与 as-of 日期；现实职业状态仅在预测冻结后由评分阶段读取。
- 冻结预测：[`predictions/p-series-career-path-classifier-v2.jsonl`](../predictions/p-series-career-path-classifier-v2.jsonl)。
- 冻结元数据：[`META/as-of-evaluation/p-series-career-path-classifier-freeze-v2.json`](../META/as-of-evaluation/p-series-career-path-classifier-freeze-v2.json)。
- 评分结果：[`META/as-of-evaluation/p-series-career-path-classifier-score-v2.json`](../META/as-of-evaluation/p-series-career-path-classifier-score-v2.json)。
- `one_shot_freeze=true`，`post_score_tuning_permitted=false`。
- 冻结预测 SHA256：`5ae87eb2f1004be5119e58348ea3825ab0f79b73434432a17e290834632a9223`。

## 2. 判别器与 error-analysis 机制映射

| 机制 | 报告定义 | v2 编码落点 | 审计证据标记 |
|---|---|---|---|
| 判别器 1：官杀印绶组织链 | 官杀有根且印承接时任职 +2.0；官杀透干且官印相生时任职 +1.5；官杀混杂无制化不加稳定分；强食伤破官且无印救应时任职 -1.0 | [`engine/asof/career_path_classifier_v2.py`](../engine/asof/career_path_classifier_v2.py) 的原局结构与任职计分 | `detector_1:*` |
| 判别器 2：食伤生财做功闭环 | 可用食伤直接生财 +2.0；财有根且链条连续 +1.0；比劫/日主参与做功 +1.0；孤财最多 +0.5 且不得单独触发经营 | 同文件的食伤、财、比劫/日支参与结构与经营计分 | `detector_2:*` |
| 判别器 3：官杀大运压制 | 官杀大运当令且原局有印承接：任职 +1.5、经营 -1.5；无承接只记录压力；若与原局经营方向相反则 abstain | 同文件的大运上下文与冲突判定 | `detector_3:*`、`mixed_signal` |
| 对称大运门控 | 食伤/财大运在原局具备主体做功能力时，打开经营方向并压制任职方向 | 同文件的大运上下文 | `dayun:*` |
| 判别器 4：固定弃权边界 | 两方向分差小于 1.5 时弃权；原局与大运强方向冲突时返回 `mixed_signal` | `SCORE_MARGIN = 1.5` 与最终方向决策 | `score_margin_below_threshold`、`mixed_signal` |

## 3. v1 / v2 指标对比

| 指标 | v1 | v2 | 变化 | v2 门槛 | 结果 |
|---|---:|---:|---:|---:|---|
| 平衡准确率 | 36.25% | 46.25% | +10.00 pp | 60.00% | 失败 |
| 任职召回率 | 12.50% | 12.50% | +0.00 pp | 55.00% | 失败 |
| 经营召回率 | 60.00% | 80.00% | +20.00 pp | 55.00% | 通过 |
| 覆盖率 | 51.35% | 89.19% | +37.84 pp | 70.00% | 通过 |
| 准确率 | 18.92% | 21.62% | +2.70 pp | — | 观察项 |

v2 混淆矩阵（严格二分类 37 案）：任职真值 32 案中预测任职 4、预测经营 25、弃权 3；经营真值 5 案中预测任职 0、预测经营 4、弃权 1。预测分布为任职 5、经营 31、弃权 4。

## 4. 门禁结论与精确差距

- Promotion gate 实际退出码：`1`。
- `eligible=false`；失败检查：`min_balanced_accuracy`、`min_employment_recall`、`beats_majority_baseline`。
- 平衡准确率 46.25%，距 60.00% 门槛差 **13.75 个百分点**（0.1375）。
- 任职召回率 12.50%，距 55.00% 门槛差 **42.50 个百分点**（0.4250）。
- 经营召回率 80.00%，超过 55.00% 门槛 25.00 个百分点。
- 覆盖率 89.19%，超过 70.00% 门槛 19.19 个百分点。
- 平衡准确率超过冻结基线 42.50%，但准确率 21.62% 未超过多数类基线 86.49%，相差 **64.86 个百分点**（按未四舍五入值为 0.64865）。
- 因此 v2 不得晋级。主要冻结失败模式是判别器 2 过宽：隐藏食伤、财与隐藏比劫/日支参与组合使 40 案中 31 案落到经营预测，严重牺牲任职召回。该诊断只用于后续新版本设计，不能用于回改本批 v2。

## 5. 40 案逐案审计

| case_id | 预测 | 真值 | 命中 | 判别器触发原因 |
|---|---|---|---|---|
| P-2026-001 | entrepreneurship | entrepreneurship | 是 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-004 | entrepreneurship | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-007 | entrepreneurship | employment | 否 | detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=0.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-008 | entrepreneurship | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-009 | entrepreneurship | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-011 | entrepreneurship | employment | 否 | detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=0.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-013 | entrepreneurship | employment | 否 | detector_1:strong_output_breaks_official_without_resource_rescue<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=-1.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-017 | entrepreneurship | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-018 | entrepreneurship | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-019 | entrepreneurship | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-021 | entrepreneurship | employment | 否 | detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=0.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-023 | entrepreneurship | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-025 | entrepreneurship | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-027 | abstain | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_1:visible_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=3.5<br>entrepreneurship_score=4.0<br>reason=score_margin_below_threshold |
| P-2026-030 | entrepreneurship | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-031 | entrepreneurship | employment | 否 | detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=0.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-034 | employment | employment | 是 | detector_1:rooted_official_resource_chain<br>detector_2:wealth_only_cap<br>employment_score=2.0<br>entrepreneurship_score=0.5<br>reason=natal_score_advantage |
| P-2026-035 | entrepreneurship | entrepreneurship | 是 | detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=0.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-037 | abstain | entrepreneurship | 否 | detector_1:rooted_official_resource_chain<br>detector_1:visible_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=3.5<br>entrepreneurship_score=4.0<br>reason=score_margin_below_threshold |
| P-2026-038 | entrepreneurship | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-039 | employment | employment | 是 | detector_1:rooted_official_resource_chain<br>detector_2:wealth_only_cap<br>employment_score=2.0<br>entrepreneurship_score=0.5<br>reason=natal_score_advantage |
| P-2026-041 | entrepreneurship | employment | 否 | detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=0.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-045 | abstain | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_1:visible_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=3.5<br>entrepreneurship_score=4.0<br>reason=score_margin_below_threshold |
| P-2026-046 | abstain | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_1:visible_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=3.5<br>entrepreneurship_score=4.0<br>reason=score_margin_below_threshold |
| P-2026-047 | employment | mixed | 否 | detector_1:rooted_official_resource_chain<br>detector_2:wealth_only_cap<br>employment_score=2.0<br>entrepreneurship_score=0.5<br>reason=natal_score_advantage |
| P-2026-048 | entrepreneurship | entrepreneurship | 是 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-049 | employment | employment | 是 | detector_1:rooted_official_resource_chain<br>detector_2:wealth_only_cap<br>employment_score=2.0<br>entrepreneurship_score=0.5<br>reason=natal_score_advantage |
| P-2026-051 | entrepreneurship | mixed | 否 | detector_1:visible_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=1.5<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-055 | entrepreneurship | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-056 | entrepreneurship | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-058 | entrepreneurship | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-060 | entrepreneurship | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-062 | employment | employment | 是 | detector_1:rooted_official_resource_chain<br>detector_1:visible_official_resource_chain<br>employment_score=3.5<br>entrepreneurship_score=0.0<br>reason=natal_score_advantage |
| P-2026-063 | entrepreneurship | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-067 | entrepreneurship | mixed | 否 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-071 | entrepreneurship | employment | 否 | detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=0.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-072 | entrepreneurship | employment | 否 | detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=0.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-073 | entrepreneurship | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-074 | entrepreneurship | employment | 否 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |
| P-2026-075 | entrepreneurship | entrepreneurship | 是 | detector_1:rooted_official_resource_chain<br>detector_2:usable_output_directly_generates_wealth<br>detector_2:rooted_continuous_output_wealth_chain<br>detector_2:peer_or_subject_participation<br>employment_score=2.0<br>entrepreneurship_score=4.0<br>reason=natal_score_advantage |

## 6. 复现证据与不可变性

- 新鲜目标测试：`14 passed, 1 warning in 0.58s`；覆盖 v2 的 9 个判别器测试与 promotion gate 测试，退出码为 0。warning 是既有 deprecated adapter 导入提示。
- 独立重算预测 SHA256 为 `5ae87eb2f1004be5119e58348ea3825ab0f79b73434432a17e290834632a9223`，与冻结记录完全一致。
- 冻结与评分元数据均确认 `post_score_tuning_permitted=false`，冻结记录确认 `one_shot_freeze=true`；评分 JSON 与本报告均含 40 条审计记录。
- 版本控制定向检查显示 [`cases/fankui-feedback.md`](../cases/fankui-feedback.md) 与 [`cases/shuru-input.md`](../cases/shuru-input.md) 无 tracked diff；两个 JSONL 真值文件在当前仓库基线中为 untracked，因此 Git 无法提供相对提交的差异证明，但本任务未写入它们，最终状态仍明确记录这一限制。

## 7. 最终裁决

**FAIL / 不晋级 / 禁止评分后调参。** v2 相比 v1 提升了平衡准确率、经营召回和覆盖率，但任职召回仍停留在 12.50%，且准确率远低于多数类基线。冻结产物保留为失败基线，后续改进必须创建新版本并使用新的预注册、冻结和盲评流程。
