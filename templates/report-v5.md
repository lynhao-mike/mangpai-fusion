# 📁 归档信息（可点击导航）

- case_id：{{ case_id }}
- 报告路径：[#reports/{{ case_id }}](#reports)
- case目录：[#cases/{{ case_dir }}](#cases)
- 反馈入口：[#feedback/{{ case_dir }}](#feedback)
- v6分析模块：[#analysis/{{ case_dir }}](#analysis)

---

# 命理师内容报告（统一版）· {{ case_id }} · {{ qian_kun }}

> {{ qian_kun }}造 · {{ bazi_str }}  
> 命理师内部版 · 当前引擎标准产物 · v6 展示规范  
> 生成日期：{{ generated_date }} · mangpai-fusion 产品 {{ product_version }} · 报告规范 {{ report_schema_version }}

---

## 基本盘面

| 区域 | 内容 |
|---|---|
| 案例编号 | {{ case_id }} |
| 命式 | {{ qian_kun }}造 |
| 出生信息 | {{ birth_date }} |
| 案例状态 | {{ case_status }} |
| 四柱 | {{ bazi_str }} |
| 大运 | {{ dayun_str }} |
| 已知反馈事实 | {{ known_facts_br }} |
| 展示口径 | {{ display_policy }} |

四柱竖排：

|  | 年柱 | 月柱 | 日柱 | 时柱 |
|---|---|---|---|---|
| 天干 | {{ year_gan }} | {{ month_gan }} | {{ day_gan }} | {{ hour_gan }} |
| 地支 | {{ year_zhi }} | {{ month_zhi }} | {{ day_zhi }} | {{ hour_zhi }} |

---

## 命局核心结论

- **总体命局等级**：{{ energy_ordinal }}（{{ energy_score_pct }}%）。本项表示原局结构承载度、清晰度与可训练性，不直接等同现实社会层级。
- **主导结构**：日主 {{ sz_day_master }}，月令 {{ sz_yueling }}；体为 {{ sz_body_str }}，用为 {{ sz_purpose_str }}。
- **财富与事业主线**：财富天花板参考 {{ wealth_ceiling }}；现实层级须按“原局潜势 → 大运承接 → 现实反馈”校准。
- **格局取象摘要**：财富等级 {{ caifu_type }}（第 {{ caifu_rank }} 等），官命取法 {{ guanming_type }}（第 {{ guanming_rank }} 取），行业方向 {{ industry_pointers_str }}。
- **核心反馈方向**：优先回访事业变化、财富变化、婚恋状态、健康风险与关键年份事件。

---

## 体用、做功与人生主线

### 盲派底盘

{% if zuogong_paths %}
{% for path in zuogong_paths %}
- {{ path.description }}（强度：{{ path.strength_ordinal }}，层数：{{ path.layer_count }}；置信：★{{ path.star }}/{{ path.pct }}%）。
{% endfor %}
{% endif %}
{% if not zuogong_paths %}
- 当前引擎未输出可单列坐宫路径，按体用、五步法与共识断语综合判断。
{% endif %}

**体用判断**：{{ tiyong_summary }}

### 五步法

{% if wubu_steps %}
{% for step in wubu_steps %}
- **{{ step.name }}**：{{ step.finding }}
{% endfor %}
{% endif %}
{% if not wubu_steps %}
- 当前引擎未输出五步法明细，按核心结论与逐域判断呈现。
{% endif %}

### 婚恋与健康旁证

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

---

## 性格与行为模式

| 指标 | 判断结果 | 证据链 | 置信度 | 应期 | 反馈校准 |
|---|---|---|---|---|---|
| 行为模式 | {{ personality_15tier_layer }}；{{ personality_15tier_meaning }} | {{ personality_15tier_evidence }} | {{ personality_15tier_confidence }} | {{ personality_15tier_timing }} | 长期行为模式、关键决策、压力反应 |

> 性格只作为结构解释变量，不进入主要事项概率层，也不作为 outcome taxonomy 主标签。

---

# 📊 受限概率提示（校准增强版）

> 概率仅用于可反馈事件，统一按 0%–100% 区间展示；初始概率 baseline 不低于 45%，无反馈主候选默认进入 55%–75% 区间。五派一致时触发 prior boost，禁止全局低置信压缩策略。性格、格局高低、总体气质不进入概率层。

| 事件领域 | 时间窗口 | 概率（0–100%） | 置信状态 | 星级 | 说明 |
|---|---|---|---|---|---|
| {{ probability_event_1_domain }} | {{ probability_event_1_window }} | {{ probability_event_1_range }} | {{ probability_event_1_confidence_state }} | {{ probability_event_1_star }} | {{ probability_event_1_explanation }} |
| {{ probability_event_2_domain }} | {{ probability_event_2_window }} | {{ probability_event_2_range }} | {{ probability_event_2_confidence_state }} | {{ probability_event_2_star }} | {{ probability_event_2_explanation }} |
| {{ probability_event_3_domain }} | {{ probability_event_3_window }} | {{ probability_event_3_range }} | {{ probability_event_3_confidence_state }} | {{ probability_event_3_star }} | {{ probability_event_3_explanation }} |

---

## 主要事项结果分类判断表

> 本表按 outcome taxonomy 拆成五大现实事项与可反馈二级指标。报告只展示中文字段；机器标签仅保留在契约、映射与内部结构中，不在报告正文显示。

### 学业

| 指标 | 判断结果 | 候选范围 | 证据链 | 置信度 | 应期 | 反馈校准 |
|---|---|---|---|---|---|---|
| 学历层次 | {{ education_degree_result }} | {{ education_degree_range }} | {{ education_15tier_evidence }} | {{ education_15tier_confidence }} | {{ education_15tier_timing }} | 最高学历、毕业时间、证照、升学节点 |
| 学校层次 | {{ education_institution_result }} | {{ education_institution_range }} | {{ education_domain_process }} | {{ education_15tier_confidence }} | {{ education_15tier_timing }} | 学校名称、学校层级、录取方式、转学或深造记录 |
| 成绩水平 | {{ education_performance_result }} | {{ education_performance_range }} | {{ education_domain_process }} | {{ education_15tier_confidence }} | {{ education_15tier_timing }} | 分数、排名、竞赛、证书、长期学习反馈 |
| 专业/方向类型 | {{ education_field_result }} | {{ education_field_range }} | {{ education_domain_process }} | {{ education_15tier_confidence }} | {{ education_15tier_timing }} | 专业方向、职业关联、后续技能迁移 |

### 事业

| 指标 | 判断结果 | 候选范围 | 证据链 | 置信度 | 应期 | 反馈校准 |
|---|---|---|---|---|---|---|
| 职业层级 | {{ career_occupation_result }} | {{ career_occupation_range }} | {{ career_15tier_evidence }} | {{ career_15tier_confidence }} | {{ career_15tier_timing }} | 职业、岗位、头衔、经营规模、转岗记录 |
| 单位层级 | {{ career_organization_result }} | {{ career_organization_range }} | {{ career_domain_process }} | {{ career_15tier_confidence }} | {{ career_15tier_timing }} | 单位性质、平台规模、组织层级、行业地位 |
| 权力层级 | {{ career_authority_result }} | {{ career_authority_range }} | 官命取法 {{ guanming_type }}；{{ career_domain_process }} | {{ career_15tier_confidence }} | {{ career_15tier_timing }} | 正式任命、管理半径、预算权、资源调度权 |
| 成就层级 | {{ career_achievement_result }} | {{ career_achievement_range }} | 行业方向 {{ industry_pointers_str }}；{{ career_domain_process }} | {{ career_15tier_confidence }} | {{ career_15tier_timing }} | 项目成果、业绩、奖项、客户或行业影响 |

### 财富

| 指标 | 判断结果 | 候选范围 | 证据链 | 置信度 | 应期 | 反馈校准 |
|---|---|---|---|---|---|---|
| 年收入 | {{ wealth_income_result }} | {{ wealth_income_range }} | {{ wealth_15tier_evidence }} | {{ wealth_15tier_confidence }} | {{ wealth_15tier_timing }} | 年收入区间、收入来源、经营流水、薪酬变化 |
| 资产等级 | {{ wealth_asset_result }} | {{ wealth_asset_range }} | 财富天花板 {{ wealth_ceiling }}；{{ wealth_domain_process }} | {{ wealth_15tier_confidence }} | {{ wealth_15tier_timing }} | 净资产、房产、投资、负债、现金储备 |
| 财富稳定性 | {{ wealth_stability_result }} | {{ wealth_stability_range }} | 财富等级 {{ caifu_type }}（第 {{ caifu_rank }} 等）；{{ wealth_domain_process }} | {{ wealth_15tier_confidence }} | {{ wealth_15tier_timing }} | 现金流波动、负债压力、收入周期、风险事件 |

### 婚姻

| 指标 | 判断结果 | 候选范围 | 证据链 | 置信度 | 应期 | 反馈校准 |
|---|---|---|---|---|---|---|
| 感情状态 | {{ marriage_relationship_result }} | {{ marriage_relationship_range }} | {{ marriage_15tier_evidence }} | {{ marriage_15tier_confidence }} | {{ marriage_15tier_timing }} | 恋爱次数、结婚时间、分合、离异、再婚 |
| 婚姻质量 | {{ marriage_quality_result }} | {{ marriage_quality_range }} | {{ marriage_domain_process }} | {{ marriage_15tier_confidence }} | {{ marriage_15tier_timing }} | 满意度、冲突频率、支持度、长期稳定性 |
| 配偶教育 | {{ marriage_spouse_education_result }} | 参考学业层次映射 | {{ marriage_domain_process }} | {{ marriage_15tier_confidence }} | {{ marriage_15tier_timing }} | 配偶学历、毕业院校、证照与学习背景 |
| 配偶事业 | {{ marriage_spouse_career_result }} | 参考事业层级映射 | {{ marriage_domain_process }} | {{ marriage_15tier_confidence }} | {{ marriage_15tier_timing }} | 配偶职业、单位、权责、事业稳定性 |
| 配偶财富 | {{ marriage_spouse_wealth_result }} | 参考财富层级映射 | {{ marriage_domain_process }} | {{ marriage_15tier_confidence }} | {{ marriage_15tier_timing }} | 配偶收入、资产、家庭资源与负债状态 |
| 配偶外貌 | {{ marriage_spouse_appearance_result }} | {{ marriage_spouse_appearance_range }} | {{ marriage_domain_process }} | {{ marriage_15tier_confidence }} | {{ marriage_15tier_timing }} | 外貌吸引力、身形气质、现实反馈 |
| 配偶气质 | {{ marriage_spouse_temperament_result }} | 温和、强势、稳重、活跃、敏感等中文画像 | {{ marriage_domain_process }} | {{ marriage_15tier_confidence }} | {{ marriage_15tier_timing }} | 性情、沟通方式、压力反应、相处模式 |
| 家庭结构 | {{ marriage_family_result }} | {{ marriage_family_range }} | {% if marriage_picture %}初婚窗口 {{ marriage_window_str }}；{{ marriage_picture_extra }}{% endif %}{% if not marriage_picture %}待结合反馈补充{% endif %} | {{ marriage_15tier_confidence }} | {{ marriage_15tier_timing }} | 子女、居住结构、双方家庭牵连、再婚或同居状态 |

### 健康

> 健康章禁止预测具体死亡年龄；寿元只表达风险等级、健康管理窗口或长寿倾向。

| 指标 | 判断结果 | 候选范围 | 证据链 | 置信度 | 应期 | 反馈校准 |
|---|---|---|---|---|---|---|
| 体质 | {{ health_physical_result }} | {{ health_physical_range }} | {{ health_15tier_evidence }} | {{ health_15tier_confidence }} | {{ health_15tier_timing }} | 体检、病史、运动水平、恢复力 |
| 疾病风险 | {{ health_disease_result }} | {{ health_disease_range }} | {% if support_health %}见健康旁证{% endif %}{% if not support_health %}需结合体检继续校准{% endif %}；{{ health_domain_process }} | {{ health_15tier_confidence }} | {{ health_15tier_timing }} | 体检异常、家族史、慢病、意外伤病 |
| 心理健康 | {{ health_mental_result }} | {{ health_mental_range }} | {{ health_domain_process }} | {{ health_15tier_confidence }} | {{ health_15tier_timing }} | 压力、睡眠、情绪、心理诊疗或长期状态 |
| 寿元风险/长寿倾向 | {{ health_longevity_result }} | {{ health_longevity_range }} | {{ health_domain_process }} | {{ health_15tier_confidence }} | {{ health_15tier_timing }} | 重大健康事件、生活方式、家族长寿反馈；禁止反推死亡年龄 |

---

## 多派共识与互补结论

{% if consensus_conclusions %}
### 共识结论
{% for c in consensus_conclusions %}
- {{ c.statement }}（{{ c.schools_str }}；置信：★{{ c.star }}/{{ c.pct }}%；证据：{{ c.evidence_str }}）。
{% endfor %}
{% endif %}
{% if not consensus_conclusions %}
- 本案暂未形成高置信多派共识断语，优先以逐域判断和反馈校准为准。
{% endif %}

{% if complementary_conclusions %}
### 互补观点
{% for c in complementary_conclusions %}
- {{ c.statement }}（{{ c.schools_str }}；置信：★{{ c.star }}/{{ c.pct }}%；证据：{{ c.evidence_str }}）。
{% endfor %}
{% endif %}
{% if not complementary_conclusions %}
- 暂无可单列的互补观点。
{% endif %}

{% if production_rule_conclusions %}
### 生产规则参与
{% for c in production_rule_conclusions %}
- {{ c.statement }}（{{ c.schools_str }}；证据：{{ c.evidence_str }}；置信：★{{ c.star }}/{{ c.pct }}%）。
{% endfor %}
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

# 📌 待反馈关键流年与事件（重点校准区）

| 优先级 | 反馈主题 | 时间窗口 | 需要确认的事实 | 校准用途 |
|---|---|---|---|---|
| 1 | {{ probability_event_1_domain }} | {{ probability_event_1_window }} | 是否出现职位、平台、职责、行业或工作模式明显变化 | 校准事业主线、做功落地与官命取法 |
| 2 | {{ probability_event_2_domain }} | {{ probability_event_2_window }} | 是否出现收入结构、资产配置、现金流或负债变化 | 校准财富天花板、财源类型与运势承接 |
| 3 | {{ probability_event_3_domain }} | {{ probability_event_3_window }} | 是否出现恋爱、婚姻、分合、家庭结构或关系压力事件 | 校准夫妻宫、婚恋窗口与关系稳定度 |
| 4 | 健康变化 | 当前大运及未来三年 | 是否有体检异常、慢性风险、意外伤病或长期压力问题 | 校准健康旁证、风险等级与应期边界 |

---

## 报告边界与风险提示

- 本报告为命理师内容报告统一版，结论用于结构推演、事件回访和规则校准，不替代医疗、法律、投资或心理咨询。
- 健康章禁止预测具体死亡年龄；只表达风险等级、风险窗口和需反馈校准的生活事实。
- 未被反馈验证的判断均按“理论推断 + 可证伪条件”处理，后续应通过 `cases/{{ case_dir }}/feedback.md` 回填。

---

## 归档与反馈入口

- 报告文件：`reports/{{ report_filename }}`
- 案例目录：`cases/{{ case_dir }}/`
- 反馈文件：`cases/{{ case_dir }}/feedback.md`
