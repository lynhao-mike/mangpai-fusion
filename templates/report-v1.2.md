# 八字分析报告 v1.2 · {{ case_id }}

**命主**：{{ gender }}命 · {{ birth_date }}  
**四柱**：{{ bazi_str }}  
**大运**：{{ dayun_str }}  
**分析日期**：{{ analysis_date }}  
**引擎**：mangpai-fusion v1.2 · 四派融合  

---

## 一、能量层级（§A · D1 段派）

<!-- 铁断段：引擎生成，不可 AI 修改 -->

**做功层数**：{{ layer_count }} 层  
**财富天花板**：{{ wealth_ceiling }}  
**整体能量**：{{ energy_ordinal }} ({{ energy_score_pct }}%)  
<!-- 段派 D1 整体置信度 {{ energy_star }}★ {{ energy_pct }}% -->  

### 做功路径
{% for path in zuogong_paths %}
**[段派]** {{ path.description }}（强度：{{ path.strength_ordinal }}，层数：{{ path.layer_count }}）  ★{{ path.star }} ({{ path.pct }}%)  
来源：{{ path.rule_id }}(段)  
证伪：{{ path.falsifiable }}  

{% endfor %}
### 体用结构
{{ tiyong_summary }}

---

## 二、画面细节（§B · D2 杨派）

<!-- 铁断段：引擎生成，不可 AI 修改 -->

**财富等级**：{{ caifu_type }}（第 {{ caifu_rank }} 等）  
**官命取法**：{{ guanming_type }}（第 {{ guanming_rank }} 取）  
**行业方向**：{{ industry_pointers_str }}  
<!-- 杨派 D2 整体置信度 {{ picture_star }}★ {{ picture_pct }}% -->  

### 五步法结果
{% for step in wubu_steps %}
**第 {{ step.step }} 步 · {{ step.name }}**：{{ step.finding }}  
来源：{% for e in step.evidence %}{{ e.rule_id }}({{ e.school }}) {% endfor %}

{% endfor %}

### 婚姻画像
{% if marriage_picture %}
- 初婚最佳窗口：{{ marriage_window_str }}  
- {{ marriage_picture_extra }}  
{% else %}
- 婚姻画像待补充  
{% endif %}

---

## 三、应期总表（§C · D3 任派）

<!-- 铁断段：引擎生成，不可 AI 修改 -->
<!-- 规则：passed_layers=3 → ★★★★★；=2 → ★★★★；=1 → ★★★ -->

{% if gate_results %}
| 年份 | 流年 | 大运 | 候选事件 | 领域 | 三层 | 道门 | 置信度 | 主触发 | 来源 |
|------|------|------|----------|------|------|------|--------|--------|------|
{% for g in gate_results %}
| {{ g.year }} | {{ g.liunian }} | {{ g.dayun_str }} | {{ g.candidate_event }} | {{ g.domain }} | {{ g.layers_icon }} | {{ g.door }} | {{ g.star }}星/{{ g.pct }}% | {{ g.primary_trigger_type }} | {{ g.evidence_str }} |
{% endfor %}

### 铁口断语（passed_layers = 3）

{% for g in iron_gates %}
**[任派]** {{ g.year }}年 {{ g.domain }}·{{ g.candidate_event }}（三层齐备）  ★{{ g.star }} ({{ g.pct }}%)  
来源：{{ g.evidence_str }}  
应期：{{ g.year }} 年（passed_layers={{ g.passed_layers }}/3）  
证伪：若 {{ g.year }} 年上述事件未发生 → 失验，反馈至 feedback.md  
三层：{{ g.l1_icon }}原局有 / {{ g.l2_icon }}大运到位 / {{ g.l3_icon }}流年引爆  
主触发：{{ g.primary_trigger_type }} · 道门：{{ g.door_str }}  

{% endfor %}

{% if not iron_gates %}
> 当前扫描年份内无三层齐备的铁口断语。建议扩展扫描范围或补充候选事件。
{% endif %}

{% else %}
> 本次未运行应期扫描（gate_results 为空）。
{% endif %}

---

## 四、旁证补强（§D · D4 高派）

<!-- 铁断段：引擎生成，不可 AI 修改 -->

{% if support %}
**高派旁证置信度**：★{{ support_star }} ({{ support_pct }}%)  

{% if support_marriage_boosts %}
**婚姻旁证**：
{% for s in support_marriage_boosts %}
- [高派 {{ s.rule_id }}] {{ s.name }}（挂 {{ s.palaces_str }}）：{{ s.contribution }}（boost +{{ s.boost_pct }}%）  
{% endfor %}
{% endif %}

{% if support_edu %}
**学业辅佐（词馆学堂）**：{{ support_edu_summary }}  
boost +{{ support_edu_boost_pct }}%  
{% endif %}

{% if support_health %}
**健康灾厄警示**：
{% for h in support_health %}
- {{ h.organ }}（{{ h.risk_ordinal }}风险）：{{ h.rationale }}  
  来源：{% for e in h.evidence %}{{ e.rule_id }} {% endfor %}
{% endfor %}
{% endif %}

{% else %}
> D4 高派旁证未运行（Track-D 未合入或 shensha 为空）。
{% endif %}

---

## 五、立体合并（§E）

<!-- 铁断段：引擎生成，不可 AI 修改 -->

### 5.1 共识层断语

{% for c in consensus_conclusions %}
**[共识·{{ c.schools_str }}]** {{ c.statement }} ★{{ c.star }} ({{ c.pct }}%)  
来源：{{ c.evidence_str }}  
证伪：{{ c.falsifiable }}  

{% endfor %}
{% if not consensus_conclusions %}
> 当前无四派全一致的共识断语。
{% endif %}

### 5.2 互补层断语

{% for c in complementary_conclusions %}
**[互补·{{ c.schools_str }}]** {{ c.statement }} ★{{ c.star }} ({{ c.pct }}%)  
来源：{{ c.evidence_str }}  
证伪：{{ c.falsifiable }}  

{% endfor %}

---

## 六、风险提示（§G）

<!-- 铁断段：引擎生成，不可 AI 修改 -->

- ⚠️ 应期误差 ±3 个月（流年精度），大运过渡期（前后 1 年）置信度降 ★  
- ⚠️ 三层 gate 是铁口断的**必要条件**：passed_layers < 3 的应期仅供参考  
{% if has_xiong_gate %}
- ⚠️ **倒象凶应年份**：{{ xiong_years_str }}——这些年份用神被多重矛盾作用，须重点预警  
{% endif %}
- ⚠️ 本系统不替代命主决策；涉医疗/法律/婚姻重大决策请咨询专业人士  

---

## 七、命主画像版（§H · AI 润色允许段）

<!-- [AI-polish] 此段允许 AI 润色（仅文字表达，不得改变 ★/% 数值和 evidence 链） -->

{{ portrait_block }}

<!-- [AI-polish] 以上 § H 段为 AI 润色区间结束 -->

---

## 归档信息

- **case_id**：{{ case_id }}  
- **report_path**：reports/{{ case_id }}-report.md  
- **pipeline_version**：v1.2.0  
- **energy_hash**：`{{ energy_hash }}`  
- **picture_hash**：`{{ picture_hash }}`  
- **generated_at**：{{ generated_at }}  
- **feedback_path**：cases/{{ case_id }}/feedback.md  

---

```
报告由 mangpai-fusion v1.2 自动生成
四派融合：段建业盲派 · 杨清娟盲派 · 任付红盲派 · 高德臣盲派
双轨置信度（★+%）· 三层 gate 铁口断
```
