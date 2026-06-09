# 命理师内容报告（统一版）· {{ case_id }} · {{ qian_kun }}

> {{ qian_kun }}造 · {{ bazi_str }}  
> 多流派功能域并行直出 · V2 单报告模式  
> 生成日期：{{ analysis_date }} · mangpai-fusion 产品 v1.3.0 · pipeline/schema v1.4.0

---

## 案例概览与输入复核

| 区域 | 内容 |
|---|---|
| 案例编号 | {{ case_id }} |
| 命式 | {{ qian_kun }}造 |
| 出生信息 | {{ birth_date }} |
| 案例状态 | {{ case_status }} |
| 分析版本 | V2 命理师内容报告（统一版） |
| 使用口径 | 子平格局派、滴天髓调候派、盲派共同分析；未成年人案例不得作婚恋事实断，只保留结构风险与未来验证边界。 |
| 重要神煞 | {{ sz_shensha_brief }} |
| 空亡提示 | 以原始排盘与四柱标注为准；若 `input.md` 提供全局空亡或柱位空亡，报告应在本格补入。 |
| 已知反馈事实 | {{ known_facts_br }} |

四柱竖排：

|  | 年柱 | 月柱 | 日柱 | 时柱 |
|---|---|---|---|---|
| 天干 | {{ year_gan }} | {{ month_gan }} | {{ day_gan }} | {{ hour_gan }} |
| 地支 | {{ year_zhi }} | {{ month_zhi }} | {{ day_zhi }} | {{ hour_zhi }} |

---

## 总裁决摘要

- **总体命局等级**：{{ energy_ordinal }}（{{ energy_score_pct }}%）。这里的“命局等级”只表示原局结构的承载度、清晰度与可训练性，不等同于现实已经达到的社会阶层；现实层级必须结合学历、职业、家庭资源、反馈事实与大运落点再校准。
- **主导结构**：日主 {{ sz_day_master }}，月令 {{ sz_yueling }}；体为 {{ sz_body_str }}，用为 {{ sz_purpose_str }}。
- **财富与事业主线**：财富天花板参考 {{ wealth_ceiling }}；财富、事业、婚姻等层级均需按“原局潜势 → 大运承接 → 现实反馈”三步解释，不能只看单一五行旺衰。
- **最强一致结论**：财富等级 {{ caifu_type }}（第 {{ caifu_rank }} 等），官命取法 {{ guanming_type }}（第 {{ guanming_rank }} 取），行业方向 {{ industry_pointers_str }}。
- **最大冲突结论**：{% if parallel_domain_consistency_notes %}见“跨域一致性检查”的冲突与处理结果。{% endif %}{% if not parallel_domain_consistency_notes %}本案暂未形成可量化跨域冲突。{% endif %}
- **最需反馈验证**：优先回访三派逐域裁判中的高置信断语、关键应期与婚恋 / 财富 / 健康高风险命题。

---

## 三派共同命局底盘

### 盲派底盘

{% for path in zuogong_paths %}
- {{ path.description }}（强度：{{ path.strength_ordinal }}，层数：{{ path.layer_count }}；置信：★{{ path.star }}/{{ path.pct }}%）。
{% endfor %}

**体用判断**：{{ tiyong_summary }}

{% for step in wubu_steps %}
- **{{ step.name }}**：{{ step.finding }}
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

### 子平格局底盘

{% if production_rule_conclusions %}
{% for c in production_rule_conclusions %}
- {{ c.statement }}（{{ c.schools_str }}；置信：★{{ c.star }}/{{ c.pct }}%；证据：{{ c.evidence_str }}）。
{% endfor %}
{% endif %}
{% if not production_rule_conclusions %}
- 本案暂无可单列输出的子平生产规则断语；若理论库存在但未触发，按 abstain 进入三派逐域裁判。
{% endif %}

### 滴天髓调候底盘

- 调候派底盘优先通过生产规则断语与三派逐域分析过程呈现；未接线领域必须明确标记 abstain，不得强行补断。

### 命局核心矛盾

{% if consensus_conclusions %}
**共识结论**：
{% for c in consensus_conclusions %}
- {{ c.statement }}（{{ c.schools_str }}；置信：★{{ c.star }}/{{ c.pct }}%；证据：{{ c.evidence_str }}）。
{% endfor %}
{% endif %}
{% if complementary_conclusions %}
**互补观点**：
{% for c in complementary_conclusions %}
- {{ c.statement }}（{{ c.schools_str }}；置信：★{{ c.star }}/{{ c.pct }}%；证据：{{ c.evidence_str }}）。
{% endfor %}
{% endif %}
{% if not consensus_conclusions %}
- 本案暂未形成高置信多派共识断语，优先以逐域裁判和反馈校准为准。
{% endif %}

---

## 大运速览

{% if dayun_full_table %}
{% for d in dayun_full_table %}
- {% if d.marker %}**{{ d.ganzhi }}运：{{ d.age_range }}，{{ d.year_range }}，{{ d.marker }}**{% endif %}{% if not d.marker %}{{ d.ganzhi }}运：{{ d.age_range }}，{{ d.year_range }}{% endif %}
{% endfor %}
{% endif %}
{% if not dayun_full_table %}
- {{ dayun_str }}
{% endif %}

---

## 三派逐域分析与主要事项十五层判断

> 本节把“三派逐域分析过程”和“主要事项十五层判断”合并，避免先分析一次、后面再重复总结。每个事项同时给出三派依据、裁判结论、层级解释、界限解释、置信度与应期。

| 事项 | 三派依据与裁判过程 | 十五层判断与界限解释 | 证据链 | 置信度 | 应期 |
|---|---|---|---|---|---|
| 学业 | {{ education_domain_process }} | {{ education_15tier_layer }}；{{ education_15tier_meaning }}；界限：{{ education_15tier_boundary }}，{{ education_15tier_boundary_explain }} | {{ education_15tier_evidence }} | {{ education_15tier_confidence }} | {{ education_15tier_timing }} |
| 事业 | {{ career_domain_process }} | {{ career_15tier_layer }}；{{ career_15tier_meaning }}；界限：{{ career_15tier_boundary }}，{{ career_15tier_boundary_explain }} | {{ career_15tier_evidence }} | {{ career_15tier_confidence }} | {{ career_15tier_timing }} |
| 财富 | {{ wealth_domain_process }} | {{ wealth_15tier_layer }}；{{ wealth_15tier_meaning }}；界限：{{ wealth_15tier_boundary }}，{{ wealth_15tier_boundary_explain }} | {{ wealth_15tier_evidence }} | {{ wealth_15tier_confidence }} | {{ wealth_15tier_timing }} |
| 婚姻 | {{ marriage_domain_process }} | {{ marriage_15tier_layer }}；{{ marriage_15tier_meaning }}；界限：{{ marriage_15tier_boundary }}，{{ marriage_15tier_boundary_explain }} | {{ marriage_15tier_evidence }} | {{ marriage_15tier_confidence }} | {{ marriage_15tier_timing }} |
| 健康 | {{ health_domain_process }} | {{ health_15tier_layer }}；{{ health_15tier_meaning }}；界限：{{ health_15tier_boundary }}，{{ health_15tier_boundary_explain }} | {{ health_15tier_evidence }} | {{ health_15tier_confidence }} | {{ health_15tier_timing }} |
| 性格 | {{ personality_domain_process }} | {{ personality_15tier_layer }}；{{ personality_15tier_meaning }}；界限：{{ personality_15tier_boundary }}，{{ personality_15tier_boundary_explain }} | {{ personality_15tier_evidence }} | {{ personality_15tier_confidence }} | {{ personality_15tier_timing }} |

{% if parallel_domain_sections %}
### 逐域补充说明

{% for d in parallel_domain_sections %}
- **{{ d.domain }}域**：{{ d.statement }}；决策状态：{{ d.decision }}；冲突解释：{{ d.conflict_summary }}；置信度：★{{ d.star }}/{{ d.pct }}%。
{% endfor %}
{% endif %}
{% if not parallel_domain_sections %}
- 本案尚未生成完整多专家功能域裁判过程；当前以命局底盘、生产规则断语和 15 层定位为主，不宣称三派已完成每一域强裁判。
{% endif %}

---

## 共识层（Consensus）

{% if consensus_conclusions %}
{% for c in consensus_conclusions %}
- 共识结论：{{ c.statement }}
  - 证据来源：{{ c.schools_str }}
  - 推导逻辑：{{ c.evidence_str }}
  - 置信度：★{{ c.star }}/{{ c.pct }}%
{% endfor %}
{% endif %}
{% if not consensus_conclusions %}
- 暂无可单列的高置信共识结论。
{% endif %}

---

## 互补层（Complementary）

{% if complementary_conclusions %}
{% for c in complementary_conclusions %}
- 互补观点：{{ c.statement }}
  - 支撑依据：{{ c.schools_str }}；{{ c.evidence_str }}
  - 置信度：★{{ c.star }}/{{ c.pct }}%
{% endfor %}
{% endif %}
{% if not complementary_conclusions %}
- 暂无可单列的互补观点。
{% endif %}

---

## 独门层

{% if exclusive_conclusions %}
{% for c in exclusive_conclusions %}
- 独门判断：{{ c.statement }}
  - 理由：{{ c.evidence_str }}
  - 置信度：★{{ c.star }}/{{ c.pct }}%
{% endfor %}
{% endif %}
{% if not exclusive_conclusions %}
- 暂无可单列的独门判断。
{% endif %}

---

## 冲突层与仲裁

{% if parallel_domain_consistency_notes %}
{% for n in parallel_domain_consistency_notes %}
- 冲突内容：{{ n.statement }}
  - 涉及领域：{{ n.domain }}
  - 严重度：{{ n.severity }}
  - 仲裁理由：{{ n.arbitration_note }}
  - 最终裁决：以可反馈、可证伪且跨域一致性更高的一侧为主。
{% endfor %}
{% endif %}
{% if not parallel_domain_consistency_notes %}
- 本案暂未生成跨域冲突告警。
{% endif %}

---

## 应期总表

{% if gate_results %}
| 事项 | 时间窗口 | 触发条件 | 置信度 |
|---|---|---|---|
{% for g in gate_results %}
| {{ g.domain }} | {{ g.year }}（{{ g.liunian }}，{{ g.dayun_str }}） | {{ g.candidate_event }}；触发：{{ g.primary_trigger_type }} | ★{{ g.star }}/{{ g.pct }}% |
{% endfor %}
{% endif %}
{% if not gate_results %}
- 本案暂无可输出应期表。
{% endif %}

---

## 跨域一致性检查

{% if parallel_domain_consistency_notes %}
| 一致项 / 不一致项 | 处理结果 |
|---|---|
{% for n in parallel_domain_consistency_notes %}
| {{ n.domain }}：{{ n.statement }} | {{ n.arbitration_note }} |
{% endfor %}
{% endif %}
{% if not parallel_domain_consistency_notes %}
- 本案暂未生成跨域一致性告警。
{% endif %}

---

## 高风险铁断与禁断边界

### 高风险铁断

{% if has_15tier %}
{% for d in tier_domains %}
- {{ d.domain_label }}：L{{ d.low }}-L{{ d.high }}，中位 L{{ d.mid }}（{{ d.label }}）；社会对应：{{ d.society }}；依据：{{ d.rationale }}。这里的上下限分别表示“反馈不足或执行走偏时的保守落点”和“运势承接、教育/平台/资源配合良好时的可冲上界”。
{% endfor %}

> {{ tier_disclaimer }}
{% endif %}
{% if not has_15tier %}
- 十五层定位未完整生成，不输出高风险铁断。
{% endif %}

### 禁断边界

1. 未接线的子平 / 滴天髓功能域只能标记 abstain，不得强行补断。
2. 应期年份只作风险管理和复盘线索，不替代医疗、法律、投资等专业决策。
3. 重大财务、合作、婚恋承诺事项，优先做书面规则和风险隔离。
4. 未成年人案例不得作婚恋事实断，只能保留结构风险与未来验证边界。

---

## 总评

- **命局等级解释**：{{ energy_ordinal }}（{{ energy_score_pct }}%）代表原局结构的强弱、做功能力与可训练空间；若现实反馈不支持，不可直接等同于社会成就。
- **事业层级解释**：{{ guanming_type }}（第 {{ guanming_rank }} 取）表示事业更适合通过专业、规则、证照、项目责任和组织平台兑现；上升幅度取决于官杀运、平台机会与承担责任的程度。
- **财富层级解释**：{{ caifu_type }}（第 {{ caifu_rank }} 等）表示财富潜势与承财方式；必须结合平台、规则、证照、风控和家庭资产事实，不宜把“见财”直接解释成“已富”。
- **婚姻层级解释**：婚姻不单看配偶星旺衰，还要看合冲、边界、财务规则、家庭介入和年龄阶段；未成年人案例只保留结构风险，不作事实断。
- **健康层级解释**：健康风险以五行冲战、神煞旁证、作息、运动伤、体检结果与情绪压力共同校准；不能用单一神煞推出重病或灾祸。
- **性格层级解释**：性格层级反映行为模式、抗压方式、执行力与关系处理风格，不等同于道德评价；需要结合家庭教育、学校反馈与实际表现修正。
- **核心用神策略**：围绕体用结构、调候需求、规则平台与可验证反馈持续修正。

---

## 归档信息

| 字段 | 内容 |
|---|---|
| 案例编号 | {{ case_id }} |
| 报告类型 | 命理师内容报告（统一版） |
| product_version | v1.3.0 |
| pipeline_version | v1.4.0 |
| report_path | reports/{{ case_id }}-content-report.md |
| case_input | cases/{{ case_id }}/input.md |
| case_feedback | cases/{{ case_id }}/feedback.md |
| generated_at | {{ generated_at }} |

> 反馈入口：`python -m tools.feedback_ingest {{ case_id }}`
