# 📁 归档信息（可点击导航）

- case_id：{{ case_id }}
- 报告路径：[#reports/{{ case_id }}](#reports)
- case目录：[#cases/{{ case_dir }}](#cases)
- 反馈入口：[#feedback/{{ case_dir }}](#feedback)
- v6分析模块：[#analysis/{{ case_dir }}](#analysis)

---

# 命理师内容报告（统一版）· {{ case_id }} · {{ qian_kun }}

> {{ qian_kun }}造 · {{ bazi_str }}  
> 命理师内部版 · 五派融合推理操作系统 · v6.2 增强报告模板
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

## v6.2 五派裁决总论

本报告采用“子平类 / 滴天髓类 / 高德臣 / 段建业 / 杨清娟”五派融合口径。展示层只输出命理师可读结论，不展示内部命题编号、结构图编号、预测账本编号或学习信号编号。

| 裁决面向 | 当前引擎结论 | 证据链 / 取法 | 置信度 |
|---|---|---|---|
| 原局承载 | 总体命局等级 {{ energy_ordinal }}（{{ energy_score_pct }}%） | 日主 {{ sz_day_master }}，月令 {{ sz_yueling }}；体为 {{ sz_body_str }}，用为 {{ sz_purpose_str }} | ★{{ energy_star }}/{{ energy_pct }}% |
| 财富事业 | 财富等级 {{ caifu_type }}（第 {{ caifu_rank }} 等）；官命取法 {{ guanming_type }}（第 {{ guanming_rank }} 取） | 财富天花板 {{ wealth_ceiling }}；行业方向 {{ industry_pointers_str }} | ★{{ picture_star }}/{{ picture_pct }}% |
| 做功路径 | 以坐宫路径、五步法、财官出处和大运承接共同判断 | {{ tiyong_summary }} | 以可反馈事件校准 |
| 婚恋健康 | 婚恋画像与健康旁证仅作结构风险和反馈入口 | 婚恋窗口、神煞旁证、健康风险项共同参考 | 以事实反馈校准 |

### 五派统一主结论

- 原局核心不是单纯旺衰，而是“体用结构、财官做功、运势承接、现实反馈”四层共同裁决。
- 事业、财富、婚姻、健康必须进入反馈闭环；没有反馈前只输出可证伪判断，不把理论推断当作既成事实。
- 当前大运与未来三年优先验证事业变化、财富变化、关系状态和健康风险。

---

## 三段式仲裁摘要

| 仲裁阶段 | 裁决结果 | 说明 |
|---|---|---|
| 结构合法性 | 原局结构可进入当前标准分析 | 以 {{ energy_ordinal }} 级承载、体用关系与坐宫路径为主，不单凭某一五行旺衰定论 |
| 事件落地 | 优先落在事业、财富、婚恋、健康四类反馈事件 | 事件判断必须由大运、流年、做功路径与现实反馈共同确认 |
| 受限概率 | 只对可反馈事件给出概率区间 | baseline 不低于 55%，主候选按 65%–85% 区间或 prior boost 展示 |

### 主要冲突与裁决

| 冲突类型 | 分歧点 | 裁决口径 | 报告处理 |
|---|---|---|---|
| 结构冲突 | 旺衰、体用、财官取法可给出不同侧重 | 以可落地事件与证据链完整度优先 | 保留结构说明，不输出内部编号 |
| 事件冲突 | 同一结构可落在职业、财富或婚恋不同事项 | 以大运承接和反馈事实优先 | 写入待反馈关键事件 |
| 时间冲突 | 大运、流年与原局触发点可存在差异 | 以时间窗口表达，不做单点断语 | 使用“窗口 + 事实确认” |
| 程度冲突 | 理论强度与现实层级可不一致 | 原局潜势不等于现实达成 | 明确要求现实反馈校准 |

---

# 📊 受限概率提示（校准增强版）

> 概率仅用于可反馈事件，统一按 0%–100% 区间展示；初始概率 baseline 不低于 55%，主候选默认进入 65%–85% 区间。五派一致时触发 prior boost，禁止全局低置信压缩策略。性格、格局高低、总体气质不进入概率层。

| 事件领域 | 时间窗口 | 概率（0–100%） | 置信状态 | 星级 | 说明 |
|---|---|---|---|---|---|
| {{ probability_event_1_domain }} | {{ probability_event_1_window }} | {{ probability_event_1_range }} | {{ probability_event_1_confidence_state }} | {{ probability_event_1_star }} | {{ probability_event_1_explanation }} |
| {{ probability_event_2_domain }} | {{ probability_event_2_window }} | {{ probability_event_2_range }} | {{ probability_event_2_confidence_state }} | {{ probability_event_2_star }} | {{ probability_event_2_explanation }} |
| {{ probability_event_3_domain }} | {{ probability_event_3_window }} | {{ probability_event_3_range }} | {{ probability_event_3_confidence_state }} | {{ probability_event_3_star }} | {{ probability_event_3_explanation }} |

---

## 命局做功与人生主线

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

---

## 性格与行为模式

| 指标 | 判断结果 | 证据链 | 置信度 | 应期 | 反馈校准 |
|---|---|---|---|---|---|
| 行为模式 | {{ personality_15tier_layer }}；{{ personality_15tier_meaning }} | {{ personality_15tier_evidence }} | {{ personality_15tier_confidence }} | {{ personality_15tier_timing }} | 长期行为模式、关键决策、压力反应 |

> 性格只作为结构解释变量，不进入主要事项概率层，也不作为 outcome taxonomy 主标签。

---

## 主要事项结果分类判断表

> 本区按 outcome taxonomy 拆成五大现实事项与可反馈二级指标。报告只展示中文字段；机器标签仅保留在契约、映射与内部结构中，不在报告正文显示。

### 学业

| 概率 | 置信状态 | 星级 | 总体说明 |
|---|---|---|---|
| {{ education_probability_range }} | {{ education_confidence_state }} | {{ education_star_display }} | {{ education_15tier_meaning }}；候选边界：{{ education_15tier_boundary }}，{{ education_15tier_boundary_explain }} |

| 指标 | 判断结果 | 候选范围 | 证据链 | 置信度 | 应期 | 反馈校准 |
|---|---|---|---|---|---|---|
| 学历层次 | {{ education_degree_result }} | {{ education_degree_range }} | {{ education_15tier_evidence }} | {{ education_15tier_confidence }} | {{ education_15tier_timing }} | 最高学历、毕业时间、证照、升学节点 |
| 学校层次 | {{ education_institution_result }} | {{ education_institution_range }} | {{ education_domain_process }} | {{ education_15tier_confidence }} | {{ education_15tier_timing }} | 学校名称、学校层级、录取方式、转学或深造记录 |
| 成绩水平 | {{ education_performance_result }} | {{ education_performance_range }} | {{ education_domain_process }} | {{ education_15tier_confidence }} | {{ education_15tier_timing }} | 分数、排名、竞赛、证书、长期学习反馈 |
| 专业/方向类型 | {{ education_field_result }} | {{ education_field_range }} | {{ education_domain_process }} | {{ education_15tier_confidence }} | {{ education_15tier_timing }} | 专业方向、职业关联、后续技能迁移 |

### 事业

| 概率 | 置信状态 | 星级 | 总体说明 |
|---|---|---|---|
| {{ career_probability_range }} | {{ career_confidence_state }} | {{ career_star_display }} | {{ career_15tier_meaning }}；候选边界：{{ career_15tier_boundary }}，{{ career_15tier_boundary_explain }} |

| 指标 | 判断结果 | 候选范围 | 证据链 | 置信度 | 应期 | 反馈校准 |
|---|---|---|---|---|---|---|
| 职业层级 | {{ career_occupation_result }} | {{ career_occupation_range }} | {{ career_15tier_evidence }} | {{ career_15tier_confidence }} | {{ career_15tier_timing }} | 职业、岗位、头衔、经营规模、转岗记录 |
| 单位层级 | {{ career_organization_result }} | {{ career_organization_range }} | {{ career_domain_process }} | {{ career_15tier_confidence }} | {{ career_15tier_timing }} | 单位性质、平台规模、组织层级、行业地位 |
| 权力层级 | {{ career_authority_result }} | {{ career_authority_range }} | 官命取法 {{ guanming_type }}；{{ career_domain_process }} | {{ career_15tier_confidence }} | {{ career_15tier_timing }} | 正式任命、管理半径、预算权、资源调度权 |
| 成就层级 | {{ career_achievement_result }} | {{ career_achievement_range }} | 行业方向 {{ industry_pointers_str }}；{{ career_domain_process }} | {{ career_15tier_confidence }} | {{ career_15tier_timing }} | 项目成果、业绩、奖项、客户或行业影响 |

### 财富

| 概率 | 置信状态 | 星级 | 总体说明 |
|---|---|---|---|
| {{ wealth_probability_range }} | {{ wealth_confidence_state }} | {{ wealth_star_display }} | {{ wealth_15tier_meaning }}；候选边界：{{ wealth_15tier_boundary }}，{{ wealth_15tier_boundary_explain }} |

| 指标 | 判断结果 | 候选范围 | 证据链 | 置信度 | 应期 | 反馈校准 |
|---|---|---|---|---|---|---|
| 年收入 | {{ wealth_income_result }} | {{ wealth_income_range }} | {{ wealth_15tier_evidence }} | {{ wealth_15tier_confidence }} | {{ wealth_15tier_timing }} | 年收入区间、收入来源、经营流水、薪酬变化 |
| 资产等级 | {{ wealth_asset_result }} | {{ wealth_asset_range }} | 财富天花板 {{ wealth_ceiling }}；{{ wealth_domain_process }} | {{ wealth_15tier_confidence }} | {{ wealth_15tier_timing }} | 净资产、房产、投资、负债、现金储备 |
| 财富稳定性 | {{ wealth_stability_result }} | {{ wealth_stability_range }} | 财富等级 {{ caifu_type }}（第 {{ caifu_rank }} 等）；{{ wealth_domain_process }} | {{ wealth_15tier_confidence }} | {{ wealth_15tier_timing }} | 现金流波动、负债压力、收入周期、风险事件 |

### 婚姻

| 概率 | 置信状态 | 星级 | 总体说明 |
|---|---|---|---|
| {{ marriage_probability_range }} | {{ marriage_confidence_state }} | {{ marriage_star_display }} | {{ marriage_15tier_meaning }}；候选边界：{{ marriage_15tier_boundary }}，{{ marriage_15tier_boundary_explain }} |

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

{% if marriage_age_warning %}
- 婚恋提醒：{{ marriage_age_warning }}
{% endif %}
{% if support_marriage_boosts %}
**婚恋旁证**：
{% for s in support_marriage_boosts %}
- {{ s.name }}：{{ s.contribution }}。
{% endfor %}
{% endif %}

### 健康

| 概率 | 置信状态 | 星级 | 总体说明 |
|---|---|---|---|
| {{ health_probability_range }} | {{ health_confidence_state }} | {{ health_star_display }} | {{ health_15tier_meaning }}；候选边界：{{ health_15tier_boundary }}，{{ health_15tier_boundary_explain }} |

> 健康章禁止预测具体死亡年龄；寿元只表达风险等级、健康管理窗口或长寿倾向。

| 指标 | 判断结果 | 候选范围 | 证据链 | 置信度 | 应期 | 反馈校准 |
|---|---|---|---|---|---|---|
| 体质 | {{ health_physical_result }} | {{ health_physical_range }} | {{ health_15tier_evidence }} | {{ health_15tier_confidence }} | {{ health_15tier_timing }} | 体检、病史、运动水平、恢复力 |
| 疾病风险 | {{ health_disease_result }} | {{ health_disease_range }} | {% if support_health %}见健康旁证{% endif %}{% if not support_health %}需结合体检继续校准{% endif %}；{{ health_domain_process }} | {{ health_15tier_confidence }} | {{ health_15tier_timing }} | 体检异常、家族史、慢病、意外伤病 |
| 心理健康 | {{ health_mental_result }} | {{ health_mental_range }} | {{ health_domain_process }} | {{ health_15tier_confidence }} | {{ health_15tier_timing }} | 压力、睡眠、情绪、心理诊疗或长期状态 |
| 寿元风险/长寿倾向 | {{ health_longevity_result }} | {{ health_longevity_range }} | {{ health_domain_process }} | {{ health_15tier_confidence }} | {{ health_15tier_timing }} | 重大健康事件、生活方式、家族长寿反馈；禁止反推死亡年龄 |

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
- {{ d.ganzhi }}运：{{ d.age_range }}，{{ d.year_range }} {{ d.marker }}
{% endfor %}
{% endif %}
{% if not dayun_full_table %}
- {{ dayun_str }}
{% endif %}

---

# 📌 待反馈关键流年与事件（重点校准区）

## 一、重点流年（必须回访）

| 反馈主题 | 时间窗口 | 概率（0–100%） | 置信状态 | 星级 | 回访要点 |
|---|---|---|---|---|---|
| {{ probability_event_1_domain }} | {{ probability_event_1_window }} | {{ probability_event_1_range }} | {{ probability_event_1_confidence_state }} | {{ probability_event_1_star }} | 是否出现职位、平台、职责、行业或工作模式明显变化 |
| {{ probability_event_2_domain }} | {{ probability_event_2_window }} | {{ probability_event_2_range }} | {{ probability_event_2_confidence_state }} | {{ probability_event_2_star }} | 是否出现收入结构、资产配置、现金流或负债变化 |
| {{ probability_event_3_domain }} | {{ probability_event_3_window }} | {{ probability_event_3_range }} | {{ probability_event_3_confidence_state }} | {{ probability_event_3_star }} | 是否出现恋爱、婚姻、分合、家庭结构或关系压力事件 |
| 健康变化 | 当前大运及未来三年 | {{ health_probability_range }} | {{ health_confidence_state }} | {{ health_star_display }} | 是否有体检异常、慢性风险、意外伤病或长期压力问题 |

## 二、关键事件验证点

| 事件领域 | 需要确认的事实 | 校准用途 |
|---|---|---|
| 事业变化 | 职位、平台、职责、行业或工作模式是否明显变化 | 校准事业主线、做功落地与官命取法 |
| 财富变化 | 收入结构、资产配置、现金流或负债是否变化 | 校准财富天花板、财源类型与运势承接 |
| 婚姻变化 | 恋爱、婚姻、分合、家庭结构或关系压力是否出现 | 校准夫妻宫、婚恋窗口与关系稳定度 |
| 健康变化 | 体检异常、慢性风险、意外伤病或长期压力是否存在 | 校准健康旁证、风险等级与应期边界 |

## 三、反馈优先级

- ⭐⭐⭐⭐⭐ 高优先：事业 / 财富 / 婚姻变化
- ⭐⭐⭐⭐ 中优先：健康变化
- ⭐⭐⭐ 学业（仅历史校验）

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
