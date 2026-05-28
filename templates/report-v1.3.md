# 八字分析报告 v1.3 · {{ case_id }} · {{ qian_kun }}

**命主**：{{ gender }}命 · {{ birth_date }}  
**四柱**：{{ bazi_str }}  
**大运**：{{ dayun_str }}  
**分析日期**：{{ analysis_date }}  
**引擎**：mangpai-fusion v1.3 · 四派融合 · {{ variant }} 版  

{% if dayun_full_table %}
**全运表**（F9）：
| 序 | 干支 | 起讫年龄 | 起讫年份 | 标记 |
|----|------|----------|----------|------|
{% for d in dayun_full_table %}
| {{ d.seq }} | {{ d.ganzhi }} | {{ d.age_range }} | {{ d.year_range }} | {{ d.marker }} |
{% endfor %}
{% endif %}

<!--
  ╔══════════════════════════════════════════════════════════╗
  ║          AI 润色边界声明（决策 D · 永久锁定）             ║
  ╠══════════════════════════════════════════════════════════╣
  ║  §A ~ §G  铁断段 / 应期段：引擎自动生成，禁止 AI 修改。  ║
  ║           ★N (X%)、evidence 编号、证伪条件不可更改。      ║
  ║  §H       画像段：唯一允许 AI 润色的区段，须标 [AI-polish]║
  ╚══════════════════════════════════════════════════════════╝

  v1.3 D1+D2 改动：
   · 每条断语挂 statement_id（S-NNN-xxxxxx）
   · master 版每条断语带 `反馈：[S-...] [ ]` 行，命理师事后填 [y]/[n]/[?]/[skip]
   · client 版隐藏 statement_id 锚点，仅展示 ★4+ 主线断语
-->

{% if is_master %}<!-- 此报告为 MASTER 版（命理师内部用）：含 statement_id 锚点 + 反馈位 -->{% endif %}{% if is_client %}<!-- 此报告为 CLIENT 版（命主可读）：仅 ★4+ 主线，无反馈位 -->{% endif %}

---

<!-- ██ 铁断区开始 ██  §A–§G  禁止 AI 修改 ██ -->

{% if section_zero %}
## 〇、命局核心结构（§0 · F8）

<!-- §0-START: 由 D1+D2 数据综合产出，禁止 AI 修改 -->

| 柱 | 干 | 支 |
|----|----|----|
{% for p in sz_pillars %}
| {{ p.name }} | {{ p.gan }} | {{ p.zhi }} |
{% endfor %}

- **日主**：{{ sz_day_master }}
- **月令**：{{ sz_yueling }}
- **体**：{{ sz_body_str }}
- **用**：{{ sz_purpose_str }}
- **做功层数**：{{ sz_layer_count }} 层 · **财富天花板**：{{ sz_wealth_ceiling }}
- **十神暗引（杨派）**：{{ sz_anyin_brief }}
- **神煞分布**：{{ sz_shensha_brief }}

<!-- §0-END -->

---
{% endif %}

## 一、能量层级（§A · D1 段派）

<!-- §A-START: 铁断段，禁止 AI 修改 -->

**做功层数**：{{ layer_count }} 层  
**财富天花板**：{{ wealth_ceiling }}  
**整体能量**：{{ energy_ordinal }} ({{ energy_score_pct }}%)  
<!-- 段派 D1 置信度：{{ energy_star }}星 / {{ energy_pct }}% -->

### 做功路径

{% for path in zuogong_paths %}
**[段派]** {{ path.description }}（强度：{{ path.strength_ordinal }}，层数：{{ path.layer_count }}）  ★{{ path.star }} ({{ path.pct }}%)  
来源：{{ path.evidence_str }}  
证伪：{{ path.falsifiable }}  
{% if is_master %}反馈：[{{ path.statement_id }}] [ ]  {% endif %}

{% endfor %}

### 体用结构

{{ tiyong_summary }}

<!-- §A-END -->

---

## 二、画面细节（§B · D2 杨派）

<!-- §B-START: 铁断段，禁止 AI 修改 -->

**财富等级**：{{ caifu_type }}（第 {{ caifu_rank }} 等）  
**官命取法**：{{ guanming_type }}（第 {{ guanming_rank }} 取）  
**行业方向**：{{ industry_pointers_str }}  
<!-- 杨派 D2 置信度：{{ picture_star }}星 / {{ picture_pct }}% -->

### 五步法结果

{% for step in wubu_steps %}
**第 {{ step.step }} 步 · {{ step.name }}**：{{ step.finding }}  
来源：{{ step.evidence_str }}

{% endfor %}

### 婚姻画像

{% if marriage_picture %}
- 初婚最佳窗口：{{ marriage_window_str }}  
- {{ marriage_picture_extra }}  
{% if marriage_age_warning %}
- ⚠️ {{ marriage_age_warning }}  
{% endif %}
{% endif %}
{% if not marriage_picture %}
- 婚姻画像待补充  
{% endif %}

{% if has_15tier %}
### 五维 15 层定位（§B.6 · F5）

| 域 | 区间 | 中位 | 社会对应 | 年入参考 | 推断依据 |
|----|------|------|----------|----------|----------|
{% for d in tier_domains %}
| {{ d.domain_label }} | L{{ d.low }}-L{{ d.high }} | **L{{ d.mid }} ({{ d.label }})** | {{ d.society }} | {{ d.income_cny }} | {{ d.rationale }} |
{% endfor %}

> {{ tier_disclaimer }}  
> 来源：D1 段派 + D2 杨派合成（MR-501）
{% endif %}

<!-- §B-END -->

---

## 三、应期总表（§C · D3 任派）

<!-- §C-START: 铁断段，禁止 AI 修改 -->
<!-- 三层惩罚规则（04 § 七 · 不可违反）：
     passed_layers=3 → ★ 上限 5（铁口断）
     passed_layers=2 → ★ 上限 4
     passed_layers=1 → ★ 上限 3
     passed_layers=0 → 不输出 -->

{% if has_retrospective %}
### 流年回溯（§C.0 · F6 · 起运 → {{ retro_current_year }}）

> {{ retro_note }}  
> 当前：{{ retro_current_age }} 岁 · {{ retro_current_dayun }} 大运 · 来源 MR-601

{% for seg in retro_segments %}
**大运 #{{ seg.seq }} {{ seg.ganzhi }}**（年龄 {{ seg.age_range }} · 年份 {{ seg.year_range }}）— {{ seg.feature }} ｜ 典型域：{{ seg.typical_domains_str }}

| 流年 | 干支 | 岁 | 强弱 | 主能量 | 推测域 | 与原局/大运作用 |
|------|------|----|------|--------|--------|-----------------|
{{ seg.flow_years_md }}

{% endfor %}
{% endif %}

{% if gate_results %}
| 年份 | 流年 | 大运 | 候选事件 | 领域 | 三层 | 道门 | 置信度 | 主触发 | 来源 |
|------|------|------|----------|------|------|------|--------|--------|------|
{% for g in gate_results %}
| {{ g.year }} | {{ g.liunian }} | {{ g.dayun_str }} | {{ g.candidate_event }} | {{ g.domain }} | {{ g.layers_icon }} | {{ g.door }} | {{ g.star }}星/{{ g.pct }}% | {{ g.primary_trigger_type }} | {{ g.evidence_str }} |
{% endfor %}

### 铁口断语（passed_layers = 3 · 三层齐备）

{% for g in iron_gates %}
**[任派]** {{ g.year }}年 {{ g.domain }}·{{ g.candidate_event }}（三层齐备）  ★{{ g.star }} ({{ g.pct }}%)  
来源：{{ g.evidence_str }}  
应期：{{ g.year }} 年（passed_layers={{ g.passed_layers }}/3）  
证伪：若 {{ g.year }} 年上述事件未发生 → 失验，反馈至 feedback.md  
三层：{{ g.l1_icon }}原局有 / {{ g.l2_icon }}大运到位 / {{ g.l3_icon }}流年引爆  
主触发：{{ g.primary_trigger_type }} · 道门：{{ g.door_str }}  
{% if is_master %}反馈：[{{ g.statement_id }}] [ ]  {% endif %}

{% endfor %}

{% if not iron_gates %}
> 当前扫描年份内无三层齐备的铁口断语。建议扩展扫描范围或补充候选事件。
{% endif %}

{% endif %}
{% if not gate_results %}
> 本次未运行应期扫描（gate_results 为空）。
{% endif %}

<!-- §C-END -->

---

## 四、旁证补强（§D · D4 高派）

<!-- §D-START: 铁断段，禁止 AI 修改 -->

{% if support %}
**[高派] 旁证置信度**：★{{ support_star }} ({{ support_pct }}%)  来源：D4 高派神煞合成层（MR-401）  

{% if support_marriage_boosts %}
**婚姻旁证**：
{% for s in support_marriage_boosts %}
- [高派 {{ s.rule_id }}] {{ s.name }}（挂 {{ s.palaces_str }}）：{{ s.contribution }}（boost +{{ s.boost_pct }}%）  
{% if is_master %}  反馈：[{{ s.statement_id }}] [ ]  {% endif %}
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
  来源：{{ h.evidence_str }}  
{% if is_master %}  反馈：[{{ h.statement_id }}] [ ]  {% endif %}
{% endfor %}
{% endif %}

{% endif %}
{% if not support %}
> D4 高派旁证未运行（Track-D 未合入或 shensha 为空）。
{% endif %}

<!-- §D-END -->

---

## 五、立体合并（§E）

<!-- §E-START: 铁断段，禁止 AI 修改 -->

### 5.1 共识层断语

{% for c in consensus_conclusions %}
**[共识·{{ c.schools_str }}]** {{ c.statement }} ★{{ c.star }} ({{ c.pct }}%)  
来源：{{ c.evidence_str }}  
证伪：{{ c.falsifiable }}  
{% if is_master %}反馈：[{{ c.statement_id }}] [ ]  {% endif %}

{% endfor %}
{% if not consensus_conclusions %}
> 当前无四派全一致的共识断语。
{% endif %}

### 5.2 互补层断语

{% for c in complementary_conclusions %}
**[互补·{{ c.schools_str }}]** {{ c.statement }} ★{{ c.star }} ({{ c.pct }}%)  
来源：{{ c.evidence_str }}  
证伪：{{ c.falsifiable }}  
{% if is_master %}反馈：[{{ c.statement_id }}] [ ]  {% endif %}

{% endfor %}

<!-- §E-END -->

---

## 六、风险提示（§G）

<!-- §G-START: 铁断段，禁止 AI 修改 -->

- ⚠️ 应期误差 ±3 个月（流年精度），大运过渡期（前后 1 年）置信度降 ★  
- ⚠️ 三层 gate 是铁口断的**必要条件**：passed_layers < 3 的应期仅供参考  
{% if has_xiong_gate %}
- ⚠️ **倒象凶应年份**：{{ xiong_years_str }}——这些年份用神被多重矛盾作用，须重点预警  
{% endif %}
- ⚠️ 本系统不替代命主决策；涉医疗/法律/婚姻重大决策请咨询专业人士  

<!-- §G-END -->

<!-- ██ 铁断区结束 ██  §A–§G  以上内容禁止 AI 修改 ██ -->

---

## 七、命主画像版（§H · AI 润色允许段）

<!-- §H-START: AI 润色段 [AI-polish] 开始 -->
<!-- [AI-polish] 本段允许 AI 润色文字表达。
     约束：
       1. 不得修改任何 ★N (X%) 数值
       2. 不得修改 evidence 编号（MR-*/M1-*/M2-*/M3-*/GP-*）
       3. 不得修改证伪条件
       4. 不得添加 §A–§G 中不存在的结论
       5. 润色后的段落开头必须保留 [AI-polish] 标记 -->

{{ portrait_block }}

<!-- §H-END: AI 润色段结束 -->
<!-- [AI-polish] §H 润色区间已结束，以下内容禁止修改 -->

---

{% if is_master %}
## 八、反馈采集说明（master 版独有）

> 命理师向命主解释完毕后，**另存本文件为** `cases/{{ case_id }}/feedback.md`，
> 把每条 `反馈：[S-...] [ ]` 中的 `[ ]` 填为：
>
> - `[y]`  应验
> - `[n]`  失验
> - `[?]`  命主当场不知道（入库不计数，等待延迟反馈兑现）
> - `[skip]` 解释时未讲到 / 不适用
>
> 然后运行：`python3 -m tools.feedback_ingest {{ case_id }}`
>
> 系统会自动按 statement_id 查 `cases/{{ case_id }}/statement_index.json` 反查规律，
> 调用 feedback_loop 重算置信度。每完成 10 案反馈 → 自动触发迭代报告。

---
{% endif %}

## 归档信息

- **case_id**：{{ case_id }}  
- **report_path**：reports/{{ case_id }}-{{ variant }}.md  
- **pipeline_version**：v1.3.0  
- **statement_index**：cases/{{ case_id }}/statement_index.json  
- **energy_hash**：`{{ energy_hash }}`  
- **picture_hash**：`{{ picture_hash }}`  
- **generated_at**：{{ generated_at }}  
- **feedback_path**：cases/{{ case_id }}/feedback.md  

---

```
报告由 mangpai-fusion v1.3 自动生成
四派融合：段建业盲派 · 杨清娟盲派 · 任付红盲派 · 高德臣盲派
双轨置信度（★+%）· 三层 gate 铁口断 · 断语级反馈
```
