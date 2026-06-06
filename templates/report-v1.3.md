# 八字命理师分析报告 · {{ case_id }} · {{ qian_kun }}

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

## 一、命局核心结论

- **整体能量**：{{ energy_ordinal }}（{{ energy_score_pct }}%），做功 {{ layer_count }} 层，财富天花板参考为 {{ wealth_ceiling }}。
- **核心结构**：日主 {{ sz_day_master }}，月令 {{ sz_yueling }}；体为 {{ sz_body_str }}，用为 {{ sz_purpose_str }}。
- **画面补充**：财富等级 {{ caifu_type }}（第 {{ caifu_rank }} 等），官命取法 {{ guanming_type }}（第 {{ guanming_rank }} 取）。
- **行业方向**：{{ industry_pointers_str }}。

---

## 二、体用、病药与人生主线

### 2.1 做功路径

{% for path in zuogong_paths %}
- {{ path.description }}（强度：{{ path.strength_ordinal }}，层数：{{ path.layer_count }}；置信：★{{ path.star }}/{{ path.pct }}%）。
{% endfor %}

### 2.2 体用判断

{{ tiyong_summary }}

### 2.3 五步法旁证

{% for step in wubu_steps %}
- **第 {{ step.step }} 步 · {{ step.name }}**：{{ step.finding }}
{% endfor %}

---

## 三、五维定位

{% if has_15tier %}
| 维度 | 区间 | 中位 | 社会对应 | 年入参考 | 推断依据 |
|---|---|---|---|---|---|
{% for d in tier_domains %}
| {{ d.domain_label }} | L{{ d.low }}-L{{ d.high }} | L{{ d.mid }}（{{ d.label }}） | {{ d.society }} | {{ d.income_cny }} | {{ d.rationale }} |
{% endfor %}

> {{ tier_disclaimer }}
{% endif %}
{% if not has_15tier %}
> 本案暂未生成五维 15 层定位。
{% endif %}

---

## 四、婚恋与家庭

{% if marriage_picture %}
- 初婚最佳窗口：{{ marriage_window_str }}。
- {{ marriage_picture_extra }}
{% if marriage_age_warning %}
- 提醒：{{ marriage_age_warning }}
{% endif %}
{% endif %}
{% if not marriage_picture %}
- 婚恋画像待结合反馈补充。
{% endif %}

{% if support_marriage_boosts %}
### 婚恋旁证

{% for s in support_marriage_boosts %}
- {{ s.name }}：{{ s.contribution }}。
{% endfor %}
{% endif %}

---

## 五、事业与财富

- 事业与财富主线以做功层数、财富天花板、行业方向和五维定位综合判断。
- 适合方向：{{ industry_pointers_str }}。
- 财富参考：{{ wealth_ceiling }}；需以稳定现金流、资产沉淀和风险隔离为优先。

{% if production_rule_conclusions %}
### 子平 / 滴天髓生产规则参与

{% for c in production_rule_conclusions %}
- {{ c.statement }}（{{ c.schools_str }}；置信：★{{ c.star }}/{{ c.pct }}%；证据：{{ c.evidence_str }}）。
{% endfor %}
{% endif %}

{% if parallel_domain_conclusions %}
### 多流派功能域并行直出（v1.5-A，暂不自动裁判）

> 当前阶段不做自动裁判与机械投票；要求盲派专家组、子平格局派、调候派（滴天髓）围绕同一功能域分别输出可反馈结论。下表保留结构化证据，供命理师人工复核与后续反馈校准。

| 功能域 | 当前层级 | 流派/专家 | 结论 | 置信 | 证据 |
|---|---|---|---|---|---|
{% for c in parallel_domain_conclusions %}
| {{ c.domain }} | {{ c.layer }} | {{ c.experts_str }} | {{ c.statement }} | ★{{ c.star }}/{{ c.pct }}% | {{ c.evidence_str }} |
{% endfor %}
{% endif %}

{% if consensus_conclusions %}
### 共识结论

{% for c in consensus_conclusions %}
- {{ c.statement }}（{{ c.schools_str }}；置信：★{{ c.star }}/{{ c.pct }}%；证据：{{ c.evidence_str }}）。
{% endfor %}
{% endif %}

{% if complementary_conclusions %}
### 互补结论

{% for c in complementary_conclusions %}
- {{ c.statement }}（{{ c.schools_str }}；置信：★{{ c.star }}/{{ c.pct }}%；证据：{{ c.evidence_str }}）。
{% endfor %}
{% endif %}

---

## 六、关键应期

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

---

## 七、健康与生活风险

{% if support_health %}
{% for h in support_health %}
- {{ h.organ }}：{{ h.rationale }}（风险：{{ h.risk_ordinal }}）。
{% endfor %}
{% endif %}
{% if not support_health %}
- 健康风险需结合实际体检、作息和反馈继续校准。
{% endif %}

---

## 八、行动建议

1. 重大财务、合作、婚恋承诺事项，优先做书面规则和风险隔离。
2. 把命局优势落到可持续技能、稳定现金流和长期资产，不宜因短期机会透支健康与关系。
3. 应期年份只作风险管理和复盘线索，不替代医疗、法律、投资等专业决策。

---

## 九、总评

本报告为命理师内部报告，采用四派融合盲派框架，并承接 v1.5-A“多流派功能域并行直出阶段”：盲派专家组、子平格局派、调候派（滴天髓）分别对功能域输出结论，暂不启用自动裁判模型。后续以 `feedback.md` 与 `statement_index.json` 逐条回测校准；除非收到明确“用户报告 / 客户报告 / 命主可读报告 / 对外报告”命令，否则不得据此生成用户报告。

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
