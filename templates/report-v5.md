# 报告模板 v5 · 五派命理推理操作系统统一版

> 适用范围：基于 ZiPing Fusion Engine v5 并行核心生成《命理师内容报告（统一版）》。  
> 五派：子平类 / 滴天髓类 / 高德臣 / 段建业 / 杨清娟。  
> 模板原则：五派独立命题 → 结构图统一 → 三段式仲裁 → 受限概率提示 → 性格行为模式单列 → 结果分类等级映射 → 反馈闭环。
> 结果分类事实源：`engine/contracts/11-outcome-taxonomy-v1.md` + `mapping/outcome-taxonomy-v1.yaml`。本模板只引用，不定义训练标签。
> 展示层禁显：禁止暴露 claim_id、prediction_id、statement_id、statement_index、内部结构图 ID、仲裁索引、学习信号编号、Agent 工作记录。

---

## 一、使用说明

1. 用户要求“分析八字 / 看这个八字 / 断这个八字 / 生成报告 / 形成报告 / 出报告 / 输出报告”时，默认使用本模板生成单份《命理师内容报告（统一版）》。
2. 本模板是命理师内容报告，不是命主可读精简报告；除非用户明确要求“用户报告 / 客户报告 / 对外报告”，不得另行生成第二份可读报告。
3. 五派结论必须先经过角色化仲裁，不得把五派原始命题直接堆叠成报告。
4. 性格、格局层次、总体气质默认不概率化；只有事业、财富、婚姻、健康、学业等可反馈事件可进入受限概率提示。
5. 性格与行为模式单独成章，置于主要事项表之前；学业、事业、财富、婚姻、健康等主要事项必须引用结果分类事实源，输出领域等级、二级指标等级、候选范围、现实映射、五派支持摘要、证据链、置信度、应期和反馈字段。
6. 报告只展示结果分类的命理师可读摘要，不展示机器字段全集、内部编号或裸概率矩阵。
7. 报告结尾必须记录统一报告归档路径、case 目录与反馈入口，但不得展示内部编号。

---

## 二、统一报告骨架

```markdown
# 命理师内容报告（统一版）· {{ case_id }} · {{ qian_kun }}

> {{ qian_kun }}造 · {{ year_pillar }}年 {{ month_pillar }}月 {{ day_pillar }}日 {{ hour_pillar }}时  
> 命理师内部版 · 五派命理推理操作系统 v5 分析  
> 生成日期：{{ generated_date }} · mangpai-fusion 产品 {{ product_version }} · ZiPing Fusion Engine v5 并行核心

---

## 基本盘面

| 区域 | 内容 |
|---|---|
| 案例编号 | {{ case_id }} |
| 命式 | {{ qian_kun }}造 |
| 出生信息 | {{ solar_birth }}；{{ lunar_birth }}；{{ source_note }} |
| 四柱 | {{ year_pillar }}年 · {{ month_pillar }}月 · {{ day_pillar }}日 · {{ hour_pillar }}时 |
| 日主 | {{ day_master }} |
| 司令 / 月令 | {{ commander_and_month_order }} |
| 胎元 / 命宫 / 身宫 | {{ taiyuan }}；{{ minggong }}；{{ shengong }} |
| 空亡 | {{ kongwang }} |
| 起运 | {{ luck_start }} |
| 大运 | {{ luck_sequence }} |
| 当前大运 | {{ current_luck }}，{{ current_luck_years }}，{{ current_luck_summary }} |
| 反馈状态 | {{ feedback_status }} |

四柱竖排：

|  | 年柱 | 月柱 | 日柱 | 时柱 |
|---|---|---|---|---|
| 天干 | {{ year_gan }} | {{ month_gan }} | {{ day_gan }} | {{ hour_gan }} |
| 地支 | {{ year_zhi }} | {{ month_zhi }} | {{ day_zhi }} | {{ hour_zhi }} |
| 十神主象 | {{ year_ten_god }} | {{ month_ten_god }} | {{ day_ten_god }} | {{ hour_ten_god }} |
| 主体取象 | {{ year_image }} | {{ month_image }} | {{ day_image }} | {{ hour_image }} |

---

## v5 五派裁决总论

本次分析采用“子平类 / 滴天髓类 / 高德臣 / 段建业 / 杨清娟”五派命题图框架。报告只展示命理师可读结论，不展示内部命题编号、结构图编号、预测账本编号或学习信号编号。

| 流派角色 | 对本命局的核心判断 | 裁决权重 |
|---|---|---|
| 子平类 | {{ ziping_core_judgment }} | 结构合法性主权重 |
| 滴天髓类 | {{ ditiansui_core_judgment }} | 气势、病药、反证主权重 |
| 高德臣 | {{ gao_core_judgment }} | 做功转化与事业财富主权重 |
| 段建业 | {{ duan_core_judgment }} | 事件框架与宫位落地主权重 |
| 杨清娟 | {{ yang_core_judgment }} | 细节象、婚恋健康生活事件主权重 |

### 五派统一主结论

{{ five_school_integrated_thesis }}

{{ current_luck_integrated_thesis }}

---

## 三段式仲裁摘要

| 仲裁阶段 | 裁决结果 | 说明 |
|---|---|---|
| 结构合法性 | {{ structure_legality_result }} | {{ structure_legality_reason }} |
| 事件落地 | {{ event_realization_result }} | {{ event_realization_reason }} |
| 受限概率 | {{ probability_timing_result }} | {{ probability_timing_reason }} |

### 主要冲突与裁决

| 冲突类型 | 分歧点 | 裁决口径 | 报告处理 |
|---|---|---|---|
| 结构冲突 | {{ structure_conflict }} | {{ structure_resolution }} | {{ structure_report_policy }} |
| 事件冲突 | {{ event_conflict }} | {{ event_resolution }} | {{ event_report_policy }} |
| 时间冲突 | {{ timing_conflict }} | {{ timing_resolution }} | {{ timing_report_policy }} |
| 程度冲突 | {{ degree_conflict }} | {{ degree_resolution }} | {{ degree_report_policy }} |

---

## 受限概率提示

> 概率仅用于可反馈事件；当前无充分反馈时只给区间，不作伪精确。性格、格局高低、总体气质不进入概率层。无反馈时，置信度不是“算出来的准确度”，而是“结构 + 一致性 + 约束”的稳定性评分；允许展示“高证据 / 结构稳定倾向”，但不得写成已验证命中率或单点概率。

| 事件域 | 时间窗 | 概率范围 | 置信边界 |
|---|---|---:|---|
| {{ probability_event_1_domain }} | {{ probability_event_1_window }} | {{ probability_event_1_range }} | {{ probability_event_1_boundary }} |
| {{ probability_event_2_domain }} | {{ probability_event_2_window }} | {{ probability_event_2_range }} | {{ probability_event_2_boundary }} |
| {{ probability_event_3_domain }} | {{ probability_event_3_window }} | {{ probability_event_3_range }} | {{ probability_event_3_boundary }} |

---

## 性格与行为模式

### 判断结果

{{ personality_full_judgment }}

### 五派证据链

| 流派 | 有效证据 | 对性格判断的作用 |
|---|---|---|
| 子平类 | {{ personality_ziping_evidence }} | {{ personality_ziping_effect }} |
| 滴天髓类 | {{ personality_ditiansui_evidence }} | {{ personality_ditiansui_effect }} |
| 高德臣 | {{ personality_gao_evidence }} | {{ personality_gao_effect }} |
| 段建业 | {{ personality_duan_evidence }} | {{ personality_duan_effect }} |
| 杨清娟 | {{ personality_yang_evidence }} | {{ personality_yang_effect }} |

### 行为建议

{{ personality_action_advice }}

### 应期与证伪

- 应期：长期结构；{{ personality_timing_detail }}
- 证伪条件：{{ personality_falsifier }}

---

## 主要事项结果分类判断表

> 本表引用 `engine/contracts/11-outcome-taxonomy-v1.md` 与 `mapping/outcome-taxonomy-v1.yaml`。训练标签的事实源不在本模板；报告只展示领域等级、二级指标等级、现实映射、证据链、置信度、应期、证伪条件与反馈字段。反馈不足时允许输出 2-3 个候选等级并标注“待反馈校准”。

### 领域总览

| 领域 | 领域等级 | 候选范围 | 现实映射说明 | 五派支持摘要 | 置信度 | 应期 / 反馈窗口 |
|---|---|---|---|---|---|---|
| 学业 | {{ education_domain_level }} | {{ education_level_range }} | {{ education_display_mapping }} | {{ education_school_support_summary }} | {{ education_confidence }} | {{ education_timing }} |
| 事业 | {{ career_domain_level }} | {{ career_level_range }} | {{ career_display_mapping }} | {{ career_school_support_summary }} | {{ career_confidence }} | {{ career_timing }} |
| 财富 | {{ wealth_domain_level }} | {{ wealth_level_range }} | {{ wealth_display_mapping }} | {{ wealth_school_support_summary }} | {{ wealth_confidence }} | {{ wealth_timing }} |
| 婚姻 | {{ marriage_domain_level }} | {{ marriage_level_range }} | {{ marriage_display_mapping }} | {{ marriage_school_support_summary }} | {{ marriage_confidence }} | {{ marriage_timing }} |
| 健康 | {{ health_domain_level }} | {{ health_level_range }} | {{ health_display_mapping }} | {{ health_school_support_summary }} | {{ health_confidence }} | {{ health_timing }} |

### 学业

| 指标 | 等级 | 候选范围 | 展示描述 / 案例映射 | 证据链 | 置信度 | 应期 | 反馈字段 / 证伪条件 |
|---|---|---|---|---|---|---|---|
| 学历层次 | {{ education_degree_level }} | {{ education_degree_range }} | {{ education_degree_mapping }} | {{ education_degree_evidence_chain }} | {{ education_degree_confidence }} | {{ education_degree_timing }} | {{ education_degree_feedback_fields }}；{{ education_degree_falsifier }} |
| 学校 / 平台层次 | {{ education_institution_level }} | {{ education_institution_range }} | {{ education_institution_mapping }} | {{ education_institution_evidence_chain }} | {{ education_institution_confidence }} | {{ education_institution_timing }} | {{ education_institution_feedback_fields }}；{{ education_institution_falsifier }} |
| 学习能力 | {{ education_learning_level }} | {{ education_learning_range }} | {{ education_learning_mapping }} | {{ education_learning_evidence_chain }} | {{ education_learning_confidence }} | {{ education_learning_timing }} | {{ education_learning_feedback_fields }}；{{ education_learning_falsifier }} |
| 考试能力 | {{ education_exam_level }} | {{ education_exam_range }} | {{ education_exam_mapping }} | {{ education_exam_evidence_chain }} | {{ education_exam_confidence }} | {{ education_exam_timing }} | {{ education_exam_feedback_fields }}；{{ education_exam_falsifier }} |
| 学业成就 | {{ education_academic_level }} | {{ education_academic_range }} | {{ education_academic_mapping }} | {{ education_academic_evidence_chain }} | {{ education_academic_confidence }} | {{ education_academic_timing }} | {{ education_academic_feedback_fields }}；{{ education_academic_falsifier }} |
| 专业 / 方向类型 | {{ education_field_type }} | — | {{ education_field_mapping }} | {{ education_field_evidence_chain }} | {{ education_field_confidence }} | {{ education_field_timing }} | {{ education_field_feedback_fields }}；{{ education_field_falsifier }} |

### 事业

| 指标 | 等级 | 候选范围 | 展示描述 / 案例映射 | 证据链 | 置信度 | 应期 | 反馈字段 / 证伪条件 |
|---|---|---|---|---|---|---|---|
| 职业层次 | {{ career_occupation_level }} | {{ career_occupation_range }} | {{ career_occupation_mapping }} | {{ career_occupation_evidence_chain }} | {{ career_occupation_confidence }} | {{ career_occupation_timing }} | {{ career_occupation_feedback_fields }}；{{ career_occupation_falsifier }} |
| 组织 / 平台层次 | {{ career_organization_level }} | {{ career_organization_range }} | {{ career_organization_mapping }} | {{ career_organization_evidence_chain }} | {{ career_organization_confidence }} | {{ career_organization_timing }} | {{ career_organization_feedback_fields }}；{{ career_organization_falsifier }} |
| 管理层级 | {{ career_management_level }} | {{ career_management_range }} | {{ career_management_mapping }} | {{ career_management_evidence_chain }} | {{ career_management_confidence }} | {{ career_management_timing }} | {{ career_management_feedback_fields }}；{{ career_management_falsifier }} |
| 权责 / 权威层级 | {{ career_authority_level }} | {{ career_authority_range }} | {{ career_authority_mapping }} | {{ career_authority_evidence_chain }} | {{ career_authority_confidence }} | {{ career_authority_timing }} | {{ career_authority_feedback_fields }}；{{ career_authority_falsifier }} |
| 职业成就 | {{ career_achievement_level }} | {{ career_achievement_range }} | {{ career_achievement_mapping }} | {{ career_achievement_evidence_chain }} | {{ career_achievement_confidence }} | {{ career_achievement_timing }} | {{ career_achievement_feedback_fields }}；{{ career_achievement_falsifier }} |
| 社会影响力 | {{ career_social_influence_level }} | {{ career_social_influence_range }} | {{ career_social_influence_mapping }} | {{ career_social_influence_evidence_chain }} | {{ career_social_influence_confidence }} | {{ career_social_influence_timing }} | {{ career_social_influence_feedback_fields }}；{{ career_social_influence_falsifier }} |

### 财富

| 指标 | 等级 | 候选范围 | 展示描述 / 案例映射 | 证据链 | 置信度 | 应期 | 反馈字段 / 证伪条件 |
|---|---|---|---|---|---|---|---|
| 财富层级 | {{ wealth_overall_level }} | {{ wealth_overall_range }} | {{ wealth_overall_mapping }} | {{ wealth_overall_evidence_chain }} | {{ wealth_overall_confidence }} | {{ wealth_overall_timing }} | {{ wealth_overall_feedback_fields }}；{{ wealth_overall_falsifier }} |
| 收入层级 | {{ wealth_income_level }} | {{ wealth_income_range }} | {{ wealth_income_mapping }} | {{ wealth_income_evidence_chain }} | {{ wealth_income_confidence }} | {{ wealth_income_timing }} | {{ wealth_income_feedback_fields }}；{{ wealth_income_falsifier }} |
| 资产层级 | {{ wealth_asset_level }} | {{ wealth_asset_range }} | {{ wealth_asset_mapping }} | {{ wealth_asset_evidence_chain }} | {{ wealth_asset_confidence }} | {{ wealth_asset_timing }} | {{ wealth_asset_feedback_fields }}；{{ wealth_asset_falsifier }} |
| 财富来源类型 | {{ wealth_source_type }} | — | {{ wealth_source_mapping }} | {{ wealth_source_evidence_chain }} | {{ wealth_source_confidence }} | {{ wealth_source_timing }} | {{ wealth_source_feedback_fields }}；{{ wealth_source_falsifier }} |
| 财富稳定度 | {{ wealth_stability_level }} | {{ wealth_stability_range }} | {{ wealth_stability_mapping }} | {{ wealth_stability_evidence_chain }} | {{ wealth_stability_confidence }} | {{ wealth_stability_timing }} | {{ wealth_stability_feedback_fields }}；{{ wealth_stability_falsifier }} |

### 婚姻

| 指标 | 等级 | 候选范围 | 展示描述 / 案例映射 | 证据链 | 置信度 | 应期 | 反馈字段 / 证伪条件 |
|---|---|---|---|---|---|---|---|
| 恋爱画像 | {{ marriage_romance_level }} | {{ marriage_romance_range }} | {{ marriage_romance_mapping }} | {{ marriage_romance_evidence_chain }} | {{ marriage_romance_confidence }} | {{ marriage_romance_timing }} | {{ marriage_romance_feedback_fields }}；{{ marriage_romance_falsifier }} |
| 关系状态 | {{ marriage_relationship_level }} | {{ marriage_relationship_range }} | {{ marriage_relationship_mapping }} | {{ marriage_relationship_evidence_chain }} | {{ marriage_relationship_confidence }} | {{ marriage_relationship_timing }} | {{ marriage_relationship_feedback_fields }}；{{ marriage_relationship_falsifier }} |
| 婚姻稳定度 | {{ marriage_stability_level }} | {{ marriage_stability_range }} | {{ marriage_stability_mapping }} | {{ marriage_stability_evidence_chain }} | {{ marriage_stability_confidence }} | {{ marriage_stability_timing }} | {{ marriage_stability_feedback_fields }}；{{ marriage_stability_falsifier }} |
| 婚姻质量 | {{ marriage_quality_level }} | {{ marriage_quality_range }} | {{ marriage_quality_mapping }} | {{ marriage_quality_evidence_chain }} | {{ marriage_quality_confidence }} | {{ marriage_quality_timing }} | {{ marriage_quality_feedback_fields }}；{{ marriage_quality_falsifier }} |
| 配偶条件 | {{ marriage_spouse_level }} | {{ marriage_spouse_range }} | {{ marriage_spouse_mapping }} | {{ marriage_spouse_evidence_chain }} | {{ marriage_spouse_confidence }} | {{ marriage_spouse_timing }} | {{ marriage_spouse_feedback_fields }}；{{ marriage_spouse_falsifier }} |
| 家庭结构 | {{ marriage_family_structure }} | — | {{ marriage_family_mapping }} | {{ marriage_family_evidence_chain }} | {{ marriage_family_confidence }} | {{ marriage_family_timing }} | {{ marriage_family_feedback_fields }}；{{ marriage_family_falsifier }} |

### 健康

> 健康章禁止预测具体死亡年龄；长寿风险只表达风险等级、风险窗口或长寿倾向。

| 指标 | 等级 | 候选范围 | 展示描述 / 案例映射 | 证据链 | 置信度 | 应期 | 反馈字段 / 证伪条件 |
|---|---|---|---|---|---|---|---|
| 身体底盘 | {{ health_physical_level }} | {{ health_physical_range }} | {{ health_physical_mapping }} | {{ health_physical_evidence_chain }} | {{ health_physical_confidence }} | {{ health_physical_timing }} | {{ health_physical_feedback_fields }}；{{ health_physical_falsifier }} |
| 重大疾病风险 | {{ health_major_disease_level }} | {{ health_major_disease_range }} | {{ health_major_disease_mapping }} | {{ health_major_disease_evidence_chain }} | {{ health_major_disease_confidence }} | {{ health_major_disease_timing }} | {{ health_major_disease_feedback_fields }}；{{ health_major_disease_falsifier }} |
| 慢性风险 | {{ health_chronic_level }} | {{ health_chronic_range }} | {{ health_chronic_mapping }} | {{ health_chronic_evidence_chain }} | {{ health_chronic_confidence }} | {{ health_chronic_timing }} | {{ health_chronic_feedback_fields }}；{{ health_chronic_falsifier }} |
| 心理 / 压力状态 | {{ health_mental_level }} | {{ health_mental_range }} | {{ health_mental_mapping }} | {{ health_mental_evidence_chain }} | {{ health_mental_confidence }} | {{ health_mental_timing }} | {{ health_mental_feedback_fields }}；{{ health_mental_falsifier }} |
| 意外风险 | {{ health_accident_level }} | {{ health_accident_range }} | {{ health_accident_mapping }} | {{ health_accident_evidence_chain }} | {{ health_accident_confidence }} | {{ health_accident_timing }} | {{ health_accident_feedback_fields }}；{{ health_accident_falsifier }} |
| 长寿 / 衰弱风险 | {{ health_longevity_level }} | {{ health_longevity_range }} | {{ health_longevity_mapping }} | {{ health_longevity_evidence_chain }} | {{ health_longevity_confidence }} | {{ health_longevity_timing }} | {{ health_longevity_feedback_fields }}；{{ health_longevity_falsifier }} |

### 细节展开策略

> 本表只决定首轮报告可展开到多细，不改变案例验证置信度；当证据强度高而反馈置信低时，细节必须按“理论推断”展示，并保留不确定性说明。无反馈下的“高置信初始化模型”可初始化理论证据强度与结构稳定性评分，但不得初始化反馈验证命中率。

| 领域 | 展开等级 | 证据强度 | 反馈置信 | 输出口径 | 理论来源 | 不确定性说明 |
|---|---|---|---|---|---|---|
{% for r in detail_expansion_rows %}
| {{ r.label }} | {{ r.level_label }} | {{ r.evidence_score_value }} | {{ r.confidence_score_value }} | {{ r.inference_type }} | {{ r.theory_sources }} | {{ r.uncertainty }} |
{% endfor %}

---

## 学业与学习能力

### 判断结果

{{ study_full_judgment }}

### 五派证据链

| 流派 | 有效证据 | 对学业判断的作用 |
|---|---|---|
| 子平类 | {{ study_ziping_evidence }} | {{ study_ziping_effect }} |
| 滴天髓类 | {{ study_ditiansui_evidence }} | {{ study_ditiansui_effect }} |
| 高德臣 | {{ study_gao_evidence }} | {{ study_gao_effect }} |
| 段建业 | {{ study_duan_evidence }} | {{ study_duan_effect }} |
| 杨清娟 | {{ study_yang_evidence }} | {{ study_yang_effect }} |

### 应期与证伪

- 应期：{{ study_timing_detail }}
- 证伪条件：{{ study_falsifier }}

---

## 事业与职业路径

### 判断结果

{{ career_full_judgment }}

### 五派证据链

| 流派 | 有效证据 | 对事业判断的作用 |
|---|---|---|
| 子平类 | {{ career_ziping_evidence }} | {{ career_ziping_effect }} |
| 滴天髓类 | {{ career_ditiansui_evidence }} | {{ career_ditiansui_effect }} |
| 高德臣 | {{ career_gao_evidence }} | {{ career_gao_effect }} |
| 段建业 | {{ career_duan_evidence }} | {{ career_duan_effect }} |
| 杨清娟 | {{ career_yang_evidence }} | {{ career_yang_effect }} |

### 适合方向

{{ career_suitable_paths }}

### 应期与证伪

- 应期：{{ career_timing_detail }}
- 证伪条件：{{ career_falsifier }}

---

## 财富与资产

### 判断结果

{{ wealth_full_judgment }}

### 五派证据链

| 流派 | 有效证据 | 对财富判断的作用 |
|---|---|---|
| 子平类 | {{ wealth_ziping_evidence }} | {{ wealth_ziping_effect }} |
| 滴天髓类 | {{ wealth_ditiansui_evidence }} | {{ wealth_ditiansui_effect }} |
| 高德臣 | {{ wealth_gao_evidence }} | {{ wealth_gao_effect }} |
| 段建业 | {{ wealth_duan_evidence }} | {{ wealth_duan_effect }} |
| 杨清娟 | {{ wealth_yang_evidence }} | {{ wealth_yang_effect }} |

### 资产与风险边界

{{ wealth_risk_boundary }}

### 应期与证伪

- 应期：{{ wealth_timing_detail }}
- 证伪条件：{{ wealth_falsifier }}

---

## 婚姻与家庭

### 判断结果

{{ marriage_full_judgment }}

### 五派证据链

| 流派 | 有效证据 | 对婚姻判断的作用 |
|---|---|---|
| 子平类 | {{ marriage_ziping_evidence }} | {{ marriage_ziping_effect }} |
| 滴天髓类 | {{ marriage_ditiansui_evidence }} | {{ marriage_ditiansui_effect }} |
| 高德臣 | {{ marriage_gao_evidence }} | {{ marriage_gao_effect }} |
| 段建业 | {{ marriage_duan_evidence }} | {{ marriage_duan_effect }} |
| 杨清娟 | {{ marriage_yang_evidence }} | {{ marriage_yang_effect }} |

### 关系稳定关键

{{ marriage_stability_key }}

### 应期与证伪

- 应期：{{ marriage_timing_detail }}
- 证伪条件：{{ marriage_falsifier }}

---

## 健康与风险

### 判断结果

{{ health_full_judgment }}

### 五派证据链

| 流派 | 有效证据 | 对健康判断的作用 |
|---|---|---|
| 子平类 | {{ health_ziping_evidence }} | {{ health_ziping_effect }} |
| 滴天髓类 | {{ health_ditiansui_evidence }} | {{ health_ditiansui_effect }} |
| 高德臣 | {{ health_gao_evidence }} | {{ health_gao_effect }} |
| 段建业 | {{ health_duan_evidence }} | {{ health_duan_effect }} |
| 杨清娟 | {{ health_yang_evidence }} | {{ health_yang_effect }} |

### 健康管理建议

{{ health_management_advice }}

### 应期与证伪

- 应期：{{ health_timing_detail }}
- 证伪条件：{{ health_falsifier }}

---

## 关键年份提示

| 年份 | 主题 | 判断 |
|---|---|---|
| {{ key_year_1 }} | {{ key_year_1_theme }} | {{ key_year_1_judgment }} |
| {{ key_year_2 }} | {{ key_year_2_theme }} | {{ key_year_2_judgment }} |
| {{ key_year_3 }} | {{ key_year_3_theme }} | {{ key_year_3_judgment }} |
| {{ key_year_4 }} | {{ key_year_4_theme }} | {{ key_year_4_judgment }} |
| {{ key_year_5 }} | {{ key_year_5_theme }} | {{ key_year_5_judgment }} |

---

## 风险提示与校准清单

- 本报告基于用户提供排盘；若出生地真太阳时、历法口径或时柱变化，应重新排盘。
- 当前反馈状态：{{ feedback_status }}。无反馈时，婚姻状态、学历层级、职业行业、收入规模、健康史、父母兄弟、重大年份只能按命局结构判断，不能当作既成事实。
- 无反馈时不要求所有判断“普遍偏低”：置信度应理解为“结构 + 一致性 + 约束”的稳定性评分，理论证据强度和结构稳定性可以高，但反馈验证命中率必须保守，并明确标注“理论推断 / 需反馈验证”。
- 概率仅用于可反馈事件，并且只输出区间；性格、格局高低、气质描述不作概率化。
- 优先回访事实：{{ priority_feedback_questions }}。
- 凡涉及疾病、投资、婚姻决策，本报告只作命理风险提示，不替代医学、法律、金融与心理专业意见。

---

## 总评

{{ final_integrated_summary }}

{{ final_strategy_summary }}

---

## 归档信息

- 统一报告归档路径：reports/{{ report_filename }}
- case 目录：cases/{{ case_dir }}/
- v5 内部制品目录：cases/{{ case_dir }}/findings/v5/
- 反馈入口：cases/{{ case_dir }}/feedback.md
```

---

## 三、生成前检查清单

| 检查项 | 要求 |
|---|---|
| 五派齐备 | 子平类、滴天髓类、高德臣、段建业、杨清娟均有结论或明确 abstain 原因 |
| 三段仲裁 | 每个主要领域至少覆盖结构合法性、事件落地、概率应期三段 |
| 六大事项 | 性格与行为模式单列，学业、事业、财富、婚姻、健康必须进入主要事项分域表 |
| 分域枚举判断 | 学业拆学历层次、学校 / 平台层次、学业成就、专业 / 方向类型；事业拆职业层次、组织 / 平台层次、权责 / 权威层级、职业成就；财富拆收入层级、资产层级、财富稳定度；婚姻拆关系状态、婚姻质量、配偶条件、家庭结构；健康拆身体底盘、重大疾病风险、心理 / 压力状态、长寿 / 衰弱风险 |
| 证据链 | 每个主要事项必须写明五派或有效主派证据链 |
| 置信度 | 使用“★★★★ / 80%”等双轨样式；概率另用区间；无反馈时区分“理论证据强度 / 结构稳定性评分 / 反馈验证命中率” |
| 应期 | 必须给年份、阶段或长期结构说明；不得只写“未来” |
| 概率边界 | 只对可反馈事件给概率范围；不对性格和格局层次给概率 |
| 禁显内部 ID | 不得出现 claim_id、prediction_id、statement_id、statement_index、内部结构图 ID |
| 归档路径 | 报告末尾必须给 report、case、feedback 路径 |

---

## 四、出口禁用词与替代表达

| 禁用 / 慎用 | 原因 | 替代表达 |
|---|---|---|
| 铁口必然 | 过度确定 | 高证据倾向、结构稳定、需反馈验证 |
| 百分百 | 伪精确 | 区间概率、待校准 |
| 一定离婚 / 一定破财 / 一定患病 | 高风险绝对断语 | 关系压力增大、财务风险升高、健康管理重点 |
| 格局定终身 | 忽略反馈与岁运 | 原局提供结构边界，岁运与现实选择决定落地 |
| 内部编号 | 展示层泄密 | 改写为自然语言证据链 |

---

## 五、建议文件命名

- 报告：reports/{{ case_id }}-{{ qian_kun }}-{{ pillars_compact }}-content-report.md
- case：cases/{{ case_id }}-{{ qian_kun }}-{{ pillars_compact }}/
- 输入：cases/{{ case_dir }}/input.md
- 反馈：cases/{{ case_dir }}/feedback.md
- 内部制品：cases/{{ case_dir }}/findings/v5/
