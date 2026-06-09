# 八字分析报告 · {{ case_id }} · {{ qian_kun }}

> {{ qian_kun }}造 · {{ bazi_str }}
> 多流派功能域并行直出 · 命理师内部版
> 生成日期：{{ analysis_date }} · mangpai-fusion 产品 v1.3.0 · pipeline/schema v1.4.0

---

## 0. 基本盘面

| 项目 | 内容 |
|---|---|
| case_id | {{ case_id }} |
| 性别命式 | {{ qian_kun }} |
| 出生信息 | {{ birth_date }} |
| 四柱 | {{ bazi_str }} |
| 大运 | {{ dayun_str }} |

{% if dayun_full_table %}
### 大运排布

| 序 | 干支 | 起讫年龄 | 起讫年份 | 标记 |
|---|---|---|---|---|
{% for d in dayun_full_table %}
| {{ d.seq }} | {{ d.ganzhi }} | {{ d.age_range }} | {{ d.year_range }} | {{ d.marker }} |
{% endfor %}
{% endif %}

---

## 一、总裁决摘要

- **总体命局等级**：{{ energy_ordinal }}（{{ energy_score_pct }}%），做功 {{ layer_count }} 层，财富天花板参考为 {{ wealth_ceiling }}。
- **主导结构**：日主 {{ sz_day_master }}，月令 {{ sz_yueling }}；体为 {{ sz_body_str }}，用为 {{ sz_purpose_str }}。
- **最强一致结论**：财富等级 {{ caifu_type }}（第 {{ caifu_rank }} 等），官命取法 {{ guanming_type }}（第 {{ guanming_rank }} 取），行业方向 {{ industry_pointers_str }}。
- **最大冲突结论**：{% if parallel_domain_consistency_notes %}见“四、跨域一致性检查”的冲突 / 仲裁提示。{% endif %}{% if not parallel_domain_consistency_notes %}本案暂未形成可量化跨域冲突。{% endif %}
- **最需反馈验证**：优先回访三派逐域裁判中的 ★4+ 断语、关键应期与婚恋 / 财富 / 健康高风险命题。

---

## 二、三派共同命局底盘

### 2.1 盲派底盘

#### 段派 · 能量 / 做功 / 体用

{% for path in zuogong_paths %}
- {{ path.description }}（强度：{{ path.strength_ordinal }}，层数：{{ path.layer_count }}；置信：★{{ path.star }}/{{ path.pct }}%）。
{% endfor %}

**体用判断**：{{ tiyong_summary }}

#### 杨派 · 画像 / 五步法 / 婚财官取象

{% for step in wubu_steps %}
- **第 {{ step.step }} 步 · {{ step.name }}**：{{ step.finding }}
{% endfor %}

- 财富等级：{{ caifu_type }}（第 {{ caifu_rank }} 等）。
- 官命取法：{{ guanming_type }}（第 {{ guanming_rank }} 取）。
- 行业方向：{{ industry_pointers_str }}。

{% if marriage_picture %}
- 婚恋画像：初婚最佳窗口 {{ marriage_window_str }}；{{ marriage_picture_extra }}
{% if marriage_age_warning %}
- 婚恋提醒：{{ marriage_age_warning }}
{% endif %}
{% endif %}
{% if not marriage_picture %}
- 婚恋画像：待结合反馈补充。
{% endif %}

#### 任派 · 应期三层门

{% if gate_results %}
| 年份 | 流年 | 大运 | 领域 | 候选事件 | 置信 | 触发 |
|---|---|---|---|---|---|---|
{% for g in gate_results %}
| {{ g.year }} | {{ g.liunian }} | {{ g.dayun_str }} | {{ g.domain }} | {{ g.candidate_event }} | ★{{ g.star }}/{{ g.pct }}% | {{ g.primary_trigger_type }} |
{% endfor %}
{% endif %}
{% if not gate_results %}
> 本案暂无可输出应期表。
{% endif %}

#### 高派 · 神煞 / 健康 / 灾厄 / 旁证

{% if support_marriage_boosts %}
**婚恋旁证**：
{% for s in support_marriage_boosts %}
- {{ s.name }}：{{ s.contribution }}。
{% endfor %}
{% endif %}

{% if support_health %}
**健康旁证**：
{% for h in support_health %}
- {{ h.organ }}：{{ h.rationale }}（风险：{{ h.risk_ordinal }}）。
{% endfor %}
{% endif %}
{% if not support_health %}
- 健康风险需结合实际体检、作息和反馈继续校准。
{% endif %}

### 2.2 子平格局底盘

{% if production_rule_conclusions %}
{% for c in production_rule_conclusions %}
- {{ c.statement }}（{{ c.schools_str }}；置信：★{{ c.star }}/{{ c.pct }}%；证据：{{ c.evidence_str }}）。
{% endfor %}
{% endif %}
{% if not production_rule_conclusions %}
> 本案暂无可单列输出的子平 / 滴天髓生产规则断语；若理论库存在但未触发，按 `abstain` 进入三派逐域裁判。
{% endif %}

### 2.3 滴天髓 / 调候底盘

> 调候派底盘在第一版报告中优先通过“子平 / 滴天髓生产规则断语”与“三派逐域分析过程”呈现；未接线领域必须显式标记 `abstain`，不得强行补断。

### 2.4 底盘一致性裁判

{% if consensus_conclusions %}
**共识结论**：
{% for c in consensus_conclusions %}
- {{ c.statement }}（{{ c.schools_str }}；置信：★{{ c.star }}/{{ c.pct }}%；证据：{{ c.evidence_str }}）。
{% endfor %}
{% endif %}
{% if complementary_conclusions %}
**互补结论**：
{% for c in complementary_conclusions %}
- {{ c.statement }}（{{ c.schools_str }}；置信：★{{ c.star }}/{{ c.pct }}%；证据：{{ c.evidence_str }}）。
{% endfor %}
{% endif %}
{% if not consensus_conclusions %}
> 本案暂未形成 ★4+ 多派共识断语，优先以逐域裁判和反馈校准为准。
{% endif %}

---

## 三、功能域逐项裁判

{% if parallel_domain_conclusions %}
### 3.0 裁判总表

> 盲派专家组、子平格局派、调候派（滴天髓）围绕同一功能域分别输出 reading，经裁判层合并为可反馈结论。下表保留结构化证据，供命理师复核与后续反馈校准。

| domain | consensus_layer | 主结论 | reading_ids | adjudication_id | expert_systems | supporting_experts | dissenting_experts | abstained_experts | feedback_state | 冲突解释 |
|---|---|---|---|---|---|---|---|---|---|---|
{% for c in parallel_domain_conclusions %}
| {{ c.domain }} | {{ c.consensus_layer }} | {{ c.statement }} | {{ c.reading_ids_str }} | {{ c.adjudication_id }} | {{ c.expert_systems_str }} | {{ c.supporting_experts_str }} | {{ c.dissenting_experts_str }} | {{ c.abstained_experts_str }} | {{ c.feedback_state }} | {{ c.conflict_summary }} |
{% endfor %}
{% endif %}
{% if not parallel_domain_conclusions %}
> 本案尚未生成多专家功能域裁判总表；当前只能输出盲派底盘与生产规则断语，不能宣称三派完整裁判已完成。
{% endif %}

{% if parallel_domain_sections %}
### 3.1 三派逐域分析过程（方案 A）

> 本节按功能域分章，每个功能域固定输出盲派、子平、滴天髓三段。即使某一派未触发正式规则，也会以 `abstain` 形式明确记录“未生成读数 / 规则未接线”，避免报告只展示强势流派而遗漏空白域。每段均保留取法过程、证据链、适用边界、证伪条件与置信度，后续可逐条进入 `statement_index.json` 反馈校准。每个主要事项必须在 3.2 或 5.1 中落入 15 层判断；缺项时本报告不得视为完成。

{% for d in parallel_domain_sections %}
#### {{ d.domain }}域 · {{ d.layer }} · ★{{ d.star }}/{{ d.pct }}%

- 裁判摘要：{{ d.statement }}
- 决策状态：{{ d.decision }}
- adjudication_id：{{ d.adjudication_id }}
- expert_systems：{{ d.expert_systems_str }}
- feedback_state：{{ d.feedback_state }}
- 冲突解释：{{ d.conflict_summary }}

| 盲派专家组 | 子平格局派 | 滴天髓调候派 |
|---|---|---|
| {{ d.blind_block }} | {{ d.ziping_block }} | {{ d.ditiansui_block }} |

{% endfor %}
{% endif %}

### 3.2 主要事项 15 层判断完成性检查

> 学业 / 事业 / 财富 / 婚姻 / 健康 / 性格等主要事项必须逐项输出 15 层判断。每项至少包含“层级｜现实释义｜起止界限｜证伪条件”，并挂入 `statement_index.json`。若下表缺任一事项，必须人工补齐后才能归档为正式完成报告。

| 事项 | 15 层落点 | 现实释义 | 起止界限 | 证伪条件 | statement_id / adjudication_id |
|---|---|---|---|---|---|
| 学业 | {{ education_15tier_layer }} | {{ education_15tier_meaning }} | {{ education_15tier_boundary }} | {{ education_15tier_falsifier }} | {{ education_15tier_statement_id }} |
| 事业 | {{ career_15tier_layer }} | {{ career_15tier_meaning }} | {{ career_15tier_boundary }} | {{ career_15tier_falsifier }} | {{ career_15tier_statement_id }} |
| 财富 | {{ wealth_15tier_layer }} | {{ wealth_15tier_meaning }} | {{ wealth_15tier_boundary }} | {{ wealth_15tier_falsifier }} | {{ wealth_15tier_statement_id }} |
| 婚姻 | {{ marriage_15tier_layer }} | {{ marriage_15tier_meaning }} | {{ marriage_15tier_boundary }} | {{ marriage_15tier_falsifier }} | {{ marriage_15tier_statement_id }} |
| 健康 | {{ health_15tier_layer }} | {{ health_15tier_meaning }} | {{ health_15tier_boundary }} | {{ health_15tier_falsifier }} | {{ health_15tier_statement_id }} |
| 性格 | {{ personality_15tier_layer }} | {{ personality_15tier_meaning }} | {{ personality_15tier_boundary }} | {{ personality_15tier_falsifier }} | {{ personality_15tier_statement_id }} |

---

## 四、跨域一致性检查

{% if parallel_domain_consistency_notes %}
| 涉及领域 | 等级 | 一致性提示 | 仲裁备注 | 关联裁判 |
|---|---|---|---|---|
{% for n in parallel_domain_consistency_notes %}
| {{ n.domain }} | {{ n.severity }} | {{ n.statement }} | {{ n.arbitration_note }} | {{ n.related_adjudication_ids }} |
{% endfor %}
{% endif %}
{% if not parallel_domain_consistency_notes %}
> 本案暂未生成跨域一致性告警。
{% endif %}

---

## 五、高风险铁断与禁断边界

### 5.1 ★4+ 可验证断语

{% if has_15tier %}
| 维度 | 区间 | 中位 | 社会对应 | 年入参考 | 推断依据 |
|---|---|---|---|---|---|
{% for d in tier_domains %}
| {{ d.domain_label }} | L{{ d.low }}-L{{ d.high }} | L{{ d.mid }}（{{ d.label }}） | {{ d.society }} | {{ d.income_cny }} | {{ d.rationale }} |
{% endfor %}

> {{ tier_disclaimer }}
{% endif %}
{% if not has_15tier %}
> 缺失：本案暂未生成五维 15 层定位；正式报告必须补齐学业 / 事业 / 财富 / 婚姻 / 健康 / 性格等主要事项的“层级｜现实释义｜起止界限｜证伪条件”，否则不得视为报告完成。
{% endif %}

### 5.2 关键应期

{% if gate_results %}
| 年份 | 流年 | 大运 | 领域 | 候选事件 | 置信 | 触发 |
|---|---|---|---|---|---|---|
{% for g in gate_results %}
| {{ g.year }} | {{ g.liunian }} | {{ g.dayun_str }} | {{ g.domain }} | {{ g.candidate_event }} | ★{{ g.star }}/{{ g.pct }}% | {{ g.primary_trigger_type }} |
{% endfor %}
{% endif %}
{% if not gate_results %}
> 本案暂无可输出应期表。
{% endif %}

### 5.3 禁断边界

1. 未接线的子平 / 滴天髓功能域只能标记 `abstain`，不得强行补断。
2. 应期年份只作风险管理和复盘线索，不替代医疗、法律、投资等专业决策。
3. 重大财务、合作、婚恋承诺事项，优先做书面规则和风险隔离。

---

## 六、statement_index / feedback 映射

- `statement_index`：cases/{{ case_id }}/statement_index.json
- `feedback`：cases/{{ case_id }}/feedback.md
- `report_path`：reports/{{ case_id }}-analyst-report.md
- 第一版报告已预留 `reading_id` / `adjudication_id` / `expert_system` 字段；方案 C 拆分 `expert-audit.md` 后继续沿用同一追踪链。

---

## 七、总评

本报告为命理师内部报告，采用方案 A 第一版结构：总裁决摘要、三派共同命局底盘、功能域逐项裁判、跨域一致性、高风险铁断与反馈映射。学业 / 事业 / 财富 / 婚姻 / 健康 / 性格等主要事项必须逐项给出 15 层判断，并写明现实释义、起止界限与证伪条件。长期终局为方案 C：命理师实战报告与专家审计报告双层化。除非收到明确“用户报告 / 客户报告 / 命主可读报告 / 对外报告”命令，否则不得据此生成用户报告。

---

## 归档信息

| 字段 | 内容 |
|---|---|
| case_id | {{ case_id }} |
| 报告类型 | 命理师内部版 |
| product_version | v1.3.0 |
| pipeline_version | v1.4.0 |
| report_path | reports/{{ case_id }}-analyst-report.md |
| case_analysis | cases/{{ case_id }}/analysis.md |
| case_feedback | cases/{{ case_id }}/feedback.md |
| statement_index | cases/{{ case_id }}/statement_index.json |
| energy_hash | {{ energy_hash }} |
| picture_hash | {{ picture_hash }} |
| generated_at | {{ generated_at }} |
