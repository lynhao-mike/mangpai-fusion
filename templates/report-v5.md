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

# 📊 受限概率提示（校准增强版）

> 概率仅用于可反馈事件，统一按 0%–100% 区间展示；初始概率 baseline 不低于 45%，无反馈主候选默认进入 55%–75% 区间。五派一致时触发 prior boost，禁止全局低置信压缩策略。性格、格局高低、总体气质不进入概率层。

| 事件领域 | 时间窗口 | 概率（0–100%） | 置信状态 | 星级 | 说明 |
|---|---|---|---|---|---|
| {{ probability_event_1_domain }} | {{ probability_event_1_window }} | {{ probability_event_1_range }} | {{ probability_event_1_confidence_state }} | {{ probability_event_1_star }} | {{ probability_event_1_explanation }} |
| {{ probability_event_2_domain }} | {{ probability_event_2_window }} | {{ probability_event_2_range }} | {{ probability_event_2_confidence_state }} | {{ probability_event_2_star }} | {{ probability_event_2_explanation }} |
| {{ probability_event_3_domain }} | {{ probability_event_3_window }} | {{ probability_event_3_range }} | {{ probability_event_3_confidence_state }} | {{ probability_event_3_star }} | {{ probability_event_3_explanation }} |

---

## 主要事项结果分类判断表

> 本表采用当前引擎已稳定产出的 15 层判断字段，并按 v6 要求使用中文主字段；每个事项同时展示判断结果、证据链、置信度与应期。

| 事项 | 判断结果 | 概率 | 置信状态 | 星级 | 证据链 | 应期 | 证伪 / 反馈 |
|---|---|---|---|---|---|---|---|
| 学业 | {{ education_15tier_layer }}；{{ education_15tier_meaning }}；界限：{{ education_15tier_boundary }}，{{ education_15tier_boundary_explain }} | {{ education_probability_range }} | {{ education_confidence_state }} | {{ education_star_display }} | {{ education_15tier_evidence }} | {{ education_15tier_timing }} | 以学历层次、考试节点、专业路径与学习反馈校准 |
| 事业 | {{ career_15tier_layer }}；{{ career_15tier_meaning }}；界限：{{ career_15tier_boundary }}，{{ career_15tier_boundary_explain }} | {{ career_probability_range }} | {{ career_confidence_state }} | {{ career_star_display }} | {{ career_15tier_evidence }} | {{ career_15tier_timing }} | 以职业平台、权责变化、收入结构与岗位变化校准 |
| 财富 | {{ wealth_15tier_layer }}；{{ wealth_15tier_meaning }}；界限：{{ wealth_15tier_boundary }}，{{ wealth_15tier_boundary_explain }} | {{ wealth_probability_range }} | {{ wealth_confidence_state }} | {{ wealth_star_display }} | {{ wealth_15tier_evidence }} | {{ wealth_15tier_timing }} | 以收入、资产、现金流与负债状态校准 |
| 婚姻 | {{ marriage_15tier_layer }}；{{ marriage_15tier_meaning }}；界限：{{ marriage_15tier_boundary }}，{{ marriage_15tier_boundary_explain }} | {{ marriage_probability_range }} | {{ marriage_confidence_state }} | {{ marriage_star_display }} | {{ marriage_15tier_evidence }} | {{ marriage_15tier_timing }} | 以恋爱、结婚、分合、家庭结构反馈校准 |
| 健康 | {{ health_15tier_layer }}；{{ health_15tier_meaning }}；界限：{{ health_15tier_boundary }}，{{ health_15tier_boundary_explain }} | {{ health_probability_range }} | {{ health_confidence_state }} | {{ health_star_display }} | {{ health_15tier_evidence }} | {{ health_15tier_timing }} | 以体检、慢病、意外、作息与压力反馈校准 |
| 性格 | {{ personality_15tier_layer }}；{{ personality_15tier_meaning }}；界限：{{ personality_15tier_boundary }}，{{ personality_15tier_boundary_explain }} | 不进入概率层 | {{ personality_15tier_confidence }} | {{ energy_star }} | {{ personality_15tier_evidence }} | {{ personality_15tier_timing }} | 以长期行为模式与关键决策反馈校准 |

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
