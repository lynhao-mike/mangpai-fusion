# 项目架构与多流派引擎诊断报告

侦察日期：2026-10-14  
范围：只读。未改生产代码。临时扫描脚本已删除。  
安全约束：大于 500KB 的文件只取体积、键结构和前若干行样本，没有全文读入。

## 总判断

这不是「确定性排盘 + 向量 RAG + LLM 融合」系统。当前是 **纯规则引擎**，而且有两套并行主链：

1. **现行兼容主链**：问真排盘文本 → [`tools/preflight.py`](tools/preflight.py) `parse()` → [`engine/application/pipeline_runner.py`](engine/application/pipeline_runner.py) `run_pipeline()` → 段/杨/任/高四派硬编码 → [`integrate()`](engine/application/integration.py:171) 拼接断语 → [`tools/render_report.py`](tools/render_report.py) `render_from_output()`。
2. **目标主链**：chart dict → [`engine/v5/runner.py`](engine/v5/runner.py) `run_v5()` → 六源 `V5Claim` → 三段仲裁 → 预测账本。文档明确写它是方向，不是已经替换生产入口的主流程。见 [`engine/README.md`](engine/README.md)。

仓库约 **633.77 MB / 6589 个文件**。这 600MB 级体积主要不是古籍，而是案例运行产物 JSON。真正的理论语料只有约 36MB：`theory/` 22.63MB + `sources/` 13.03MB。

没有 OpenAI、Anthropic、LangChain、Chroma、FAISS、sentence-transformers 或 embedding 调用。所谓 Agent 是本地 Python 类，只把已有证据按极性分成正/负/中性句子。

---

## 1. 仓库全景目录树与体积分布

忽略 `.git`、`__pycache__`、`.pytest_cache` 后的目录体积：

| 目录 | MB | 文件数 | 内容 |
|---|---:|---:|---|
| [`cases/`](cases/) | 496.32 | 4707 | 案例输入、反馈、findings JSON |
| [`reports/`](reports/) | 73.17 | 166 | 渲染后的报告与审计产物 |
| [`theory/`](theory/) | 22.63 | 137 | 结构化规则 YAML / IR |
| [`sources/`](sources/) | 13.03 | 139 | 未清洗讲义 Markdown |
| [`META/`](META/) | 12.16 | 368 | 项目状态、变更、抽取记录 |
| [`plans/`](plans/) | 5.82 | 172 | 架构方案 |
| [`tests/`](tests/) | 3.57 | 321 | 测试 |
| [`engine/`](engine/) | 3.57 | 351 | 引擎源码 |
| [`tools/`](tools/) | 1.73 | 120 | CLI、API、渲染、反馈 |

核心源码树：

```text
engine/
  application/     pipeline_runner、integrate、fusion_engine_v2、production_service
  predicates/      干支、藏干、十二长生、刑冲合害、十神、神煞查询
  energy/          段派：体用、做功、势党、贼神捕神
  picture/         杨派：五步法、婚姻、财富官命、调候
  yingqi/          任派：三层门、触发器、应期
  pangzheng/       高派：神煞旁证、健康、学业
  v5/              六源命题、ziping/ditiansui runner、三段仲裁
  decision/        L1 路由、L6 对照仲裁（未替换生产入口）
  features/        ChartFeatureVector
  domain/          AnalysisOutput、并行协议
  v2/agents/       非 LLM 的领域分类器
tools/
  preflight.py
  production_api.py
  render_report.py
theory/
  {duan,gao,yang,ren,ziping,tiaohou_ditiansui}/index.yaml
  production/
  _ir/unified_rule_ir.yaml
sources/
  {duan,gao,yang,ren,ziping,tiaohou_ditiansui,ext1,ext2,qianliminggao}/
```

体积前 15：

| MB | 格式 | 相对路径 |
|---:|---|---|
| 47.50 | JSON | [`cases/C-2026-001-乾-庚申戊寅壬子辛丑/findings/analysis_output.json`](cases/C-2026-001-乾-庚申戊寅壬子辛丑/findings/analysis_output.json) |
| 42.57 | JSON | [`cases/C-2026-036-乾-辛巳壬辰甲寅乙丑/findings.after.json`](cases/C-2026-036-乾-辛巳壬辰甲寅乙丑/findings.after.json) |
| 42.57 | JSON | 同案 `findings/analysis_output.json` |
| 42.55 | JSON | [`cases/C-2026-034-乾-甲子甲戌癸卯壬戌/findings.after.json`](cases/C-2026-034-乾-甲子甲戌癸卯壬戌/findings.after.json) |
| 42.55 | JSON | 同案 `findings/analysis_output.json` |
| 18.73 | JSON | C-2026-036 `school_verdict_matrix.json` |
| 18.73 | JSON | C-2026-034 `school_verdict_matrix.json` |
| 8.38 | JSON | C-2026-036 `statement_records.json` |
| 8.38 | JSON | C-2026-034 `statement_records.json` |
| 7.75 | YAML | [`theory/_ir/unified_rule_ir.yaml`](theory/_ir/unified_rule_ir.yaml) |
| 5.44 | JSON | `cases/C-2026-RF000345-.../findings/analysis_output.json` |
| 5.43 | JSON | `cases/C-2026-RF000606-.../findings/analysis_output.json` |
| 5.40 | JSON | `cases/C-2026-RF000108-.../findings/analysis_output.json` |
| 5.40 | JSON | `cases/C-2026-RF000592-.../findings/analysis_output.json` |
| 5.40 | JSON | `cases/C-2026-RF000417-.../findings/analysis_output.json` |

C-2026-001 这份 47.50MB JSON 的膨胀点已经定位：顶层键是 `energy/picture/gate_results/support/final_conclusions/...`。其中 `fusion_findings` 7.92MB、`parallel_analysis` 7.87MB、`final_conclusions` 2048 条共 1.36MB、`theory_findings` 1.03MB。也就是说，一次分析把多套旁路结果、证据和断语重复嵌进同一个文件。前 15 名合计已超过 260MB，且多数是同一分析结果的副本。

## 2. 核心排盘与分析主链路

本仓库 **不排盘**。[`tools/preflight.py`](tools/preflight.py) 文件头写明：排盘靠问真 APP，本模块只校验并解析 `input.md`。

### 现行链路

```text
cases/*/input.md
  -> tools/preflight.py :: parse(input_md_path) -> ParsedInput
  -> engine/application/pipeline_runner.py :: run_pipeline_e2e()
       -> run_pipeline(parsed)
            -> engine/energy/evaluator.py :: evaluate_energy(parsed) -> EnergyFindings
            -> engine/picture/matcher.py :: match_picture(energy, parsed) -> PictureFindings
            -> engine/yingqi/gate.py :: gate_yingqi(...) -> list[GateResult]
            -> engine/pangzheng/pangzheng.py :: support_with_shensha(...) -> SupportFindings
            -> engine/application/integration.py :: integrate(...) -> AnalysisOutput
            -> engine/application/dual_engine_adapter.py :: analyze_dual_engine(...)
            -> engine/application/fusion_engine_v2.py :: build_final_prediction(...)
  -> tools/render_report.py :: render_from_output(AnalysisOutput) -> Markdown
```

HTTP 入口是 [`tools/production_api.py`](tools/production_api.py) `ProductionAPIHandler`，`POST /v1/analyses` 调 [`engine/application/production_service.py`](engine/application/production_service.py) `ProductionAnalysisService.submit()`。它仍包在上述 pipeline 外面，不是另一套命理算法。

[`engine/pipeline.py`](engine/pipeline.py) 只剩兼容外观：把 `run_pipeline`、`AnalysisOutput` 重新导出，并标注双引擎接口计划迁到 `engine.v5.runner.run_v5`。

### 目标链路

```text
chart: dict
  -> engine/v5/runner.py :: run_v5(chart, case_id, claims=None)
       -> build_default_claims()
            -> ziping_runner.run_ziping_independent()
            -> ditiansui_runner.run_ditiansui_independent()
            -> build_ziping_production_claims()
            -> build_ditiansui_production_claims()
            -> build_blind_school_rule_claims() × 高/段/杨
            -> build_abstain_claims() 给未接入流派
       -> build_structure_graph()
       -> arbitrate_claims()
       -> build_v5_adjudication_units()
       -> build_prediction_ledger()
  -> V5Output
  -> tools/render_report.py :: render_from_v5_output()
```

L1 适用范围路由在 [`engine/decision/l1_school_router.py`](engine/decision/l1_school_router.py) `route_schools()`。文档写明：在留出集门禁达到 GO 前，正式入口继续用 static，不自动覆盖生产权重。

### 主控制器片段

[`run_pipeline()`](engine/application/pipeline_runner.py:33) 的核心编排：

```python
ensure_parsed_chart_validated(parsed)
with timing.step("energy"):
    energy = evaluate_energy(parsed)
with timing.step("picture"):
    picture = match_picture(energy, parsed)
with timing.step("yingqi"):
    gate_results = []
    for year, event, domain in _extract_candidates(parsed):
        gr = gate_yingqi(year, event, domain, energy, picture, parsed)
        if gr.passed_layers >= 1:
            gate_results.append(gr)
with timing.step("pangzheng"):
    support = support_with_shensha(parsed, energy, picture, gate_results)
with timing.step("integrate"):
    output = integrate(energy, picture, gate_results, support, parsed)
theory_findings, blind_findings, fusion_findings = analyze_dual_engine(...)
output.theory_findings = theory_findings
output.blind_findings = blind_findings
output.fusion_findings = fusion_findings
```

双引擎、预测层、流年回溯都包在 `try/except` 里，失败只写 warning，不进入 D1–D4 hash 链。

## 3. 多流派理论模块的现有实现

### 基础排盘与干支关系：硬编码谓词表

| 能力 | 位置 | 方式 |
|---|---|---|
| 干支、五行、阴阳 | [`engine/predicates/ganzhi.py`](engine/predicates/ganzhi.py) `gan_to_wuxing()` / `zhi_to_wuxing()` | 常量表 |
| 藏干 | [`engine/predicates/types.py`](engine/predicates/types.py) `ZHI_CANGGAN_TABLE`、`Canggan`；[`get_canggan()`](engine/predicates/ganzhi.py:101) | 主气 1.0 / 中气 0.3 / 余气 0.2 |
| 十二长生 | [`engine/predicates/strength.py`](engine/predicates/strength.py) `get_changsheng()`、`is_dejin()` | 10×12 表 + 长生/临官/帝旺集合 |
| 刑冲合害穿破 | [`engine/predicates/relations.py`](engine/predicates/relations.py) `gan_he()`、`zhi_liuhe()`、`zhi_sanhe()`、`zhi_chong()`、`zhi_xing()`、`zhi_chuan()`、`zhi_po()` | 对表布尔判定 |
| 十神、宫位 | [`engine/predicates/palace.py`](engine/predicates/palace.py) `get_shishen()`、`find_shishen_in_bazi()` | 生克 + 阴阳 |
| 神煞 | [`engine/predicates/shensha.py`](engine/predicates/shensha.py) `has_shensha()` | 不自行起煞；读取输入里的神煞列表。缺失时 [`support_with_shensha()`](engine/pangzheng/pangzheng.py:330) 调 `attach_shensha()` |
| 墓库 | [`engine/energy/zuogong.py`](engine/energy/zuogong.py) `detect_mu_paths()`；[`engine/yingqi/chufa.py`](engine/yingqi/chufa.py) 墓库开闭 | 简化：财官入辰戌丑未，且有刑冲才算打开 |

### 盲派：部分硬编码，大量规则只是文本

段派 D1 入口 [`evaluate_energy()`](engine/energy/evaluator.py:199)：

- 体用：[`evaluate_tiyong()`](engine/energy/tiyong.py:99)。日干为我；印、比劫、禄为体；财、官杀为用。硬编码角色表。
- 做功：[`evaluate_zuogong()`](engine/energy/zuogong.py:522)。制、化、生泄、合、墓、复合六类扫描，层数上限启发式压缩。
- 贼神捕神：[`evaluate_zeishen()`](engine/energy/zeishen.py)。五行势力 ≥ 0.30 且克我 → 贼神；大运同五行 → 捕神。文件自己标注是启发式。
- 势党：[`evaluate_shidang()`](engine/energy/shidang.py)。

宾主、连体没有独立函数。全 `engine/` 搜不到 `宾主` 的计算实现；它只作为 [`theory/duan/index.yaml`](theory/duan/index.yaml) 的 `topic_label: 宾主` 被关键词打分后变成一句「规则参与：……」。段派 index 约 290 条，主题最多的是正格 28、婚姻 20、做功 19、象法 18、体用 11。象法同样没有几何/取象计算器，[`extract_mp_signal()`](engine/application/prediction_signals.py:99) 只是把应期门结果包装成 `MpPredictionSignal`。

杨派是 [`match_picture()`](engine/picture/matcher.py:235)：五步法、天干五合、暗引、财富官命、婚姻、调候，全部 if/表驱动。高派是神煞 boost，不是主审。任派是三层门：原局有、大运到位、流年引动。

### 传统旺衰 / 扶抑：两套互不统一的打分

1. [`calc_wuxing_strength()`](engine/predicates/strength.py:117)、[`calc_gan_strength()`](engine/predicates/strength.py:183)：天干 1.0，月令主气 1.5，其他主气 1.0，中气 0.3，余气 0.2，再归一化。
2. [`_assess_daymaster_strength()`](engine/v5/ziping_runner.py:69)：从 0.5 起步，得令 +0.20，月支同行 +0.15，克 −0.15，藏干 ±0.02/0.04。`>=0.62` 偏旺，`<=0.42` 偏弱，否则中和。

喜用神在 [`_identify_pattern_yongshen()`](engine/v5/ziping_runner.py:158)：月干十神当月令格，用神取「克格神或扶日主」的天干。这是简化映射，不是完整扶抑/调候/通关择用。

### 子平格局 / 穷通调候：轻量 if-else，不是成格引擎

子平独立 runner [`run_ziping_independent()`](engine/v5/ziping_runner.py:417) 只出两层：月令旺衰、格局用神。正格条件是「有根、有印比、月令格成立」；从格是 `score < 0.32` 且无印比无根。没有系统化的成格、破格、救应状态机。

滴天髓 [`_assess_tiaohou()`](engine/v5/ditiansui_runner.py:141) 用月支寒热燥湿标签：冬月火木且火少于 2 → 寒重需火；夏月水金且水少于 2 → 热重需水；燥而无水、湿而无火同理。这是四条阈值，不是《穷通宝鉴》逐日干逐月的调候表。

### 关键痛点：汇总是拼接、计数和加权，不是适用范围前置裁决

现行 [`integrate()`](engine/application/integration.py:171) 的做法：

- 应期门 `passed_layers >= 2` 且星级 ≥ 4 → 一条断语。
- D1 做功层数直接变一条「独门」断语。
- D2 婚姻窗口、行业方向再各加一条。
- D4 神煞 boost ≥ 0.04 再加旁证。
- 子平/滴天髓生产规则凡触发就 `_production_rule_to_conclusion()` 追加。
- `conflicts=[]`。代码注释写明：结构化冲突不在这里仲裁。

所以旧主链是 **结果追加**。后写的规则不会覆盖前面的断语，也不会先判断该派是否适用。

v4.2 [`build_final_prediction()`](engine/application/fusion_engine_v2.py:60) 把三派信号压成 0–1 概率，用 log-odds 加权。默认权重 ziping 0.42、调候 0.32、盲派 0.26。冲突定义是三者极值差 ≥ 0.35，冲突时只把子平权重乘 1.5。盲派在这里只贡献象法候选，不参与结构否决。

v5 [`arbitrate_claims()`](engine/v5/runner.py:909) 有角色顺序：结构（子平+滴天髓）→ 事件（盲派）→ 概率应期。但胜负主要按 support 条数加分：`0.45 + support * 0.08`。盲派规则默认 `stance="support"`，所以条数多的派会抬高分数。没有结构命题时，事件置信度先乘 0.4，这是唯一明显的前置门。

更严重的是盲派检索：[`build_blind_school_rule_claims()`](engine/v5/runner.py:462) 读取整份 `index.yaml`，用 [`score_blind_rule()`](engine/predicates/condition_evaluator.py:182) 做干支字符重合、冲刑词、应期词打分，然后 **每派只取前 15 条**。未知 trigger 在 [`evaluate_trigger()`](engine/predicates/condition_evaluator.py:129) 里保守返回 `True`。这会把「文本里碰巧出现命盘上的字」当成规则命中。

L1 [`_static_route_schools()`](engine/decision/l1_school_router.py:174) 确实有适用范围：五行偏枯给滴天髓加分，见冲给段/任加分，焦点不重叠则 abstain。但它没有接到 `run_pipeline()` 或 `run_v5()` 的默认路径上。

## 4. 核心数据结构

没有 Pydantic 主模型，核心都是 dataclass。盘面与结果不是同一个对象，而且 v1 与 v5 各有一套。

### 盘面：[`Bazi`](engine/predicates/types.py:180) + [`ParsedInput`](engine/predicates/types.py:266)

```python
@dataclass
class Bazi:
    年柱: GanZhi
    月柱: GanZhi
    日柱: GanZhi
    时柱: GanZhi
    藏干: dict[str, list[Canggan]] = field(default_factory=dict)

@dataclass
class ParsedInput:
    case_id: str
    bazi: Bazi
    dayun: Dayun
    birth: dict = field(default_factory=dict)
    shensha: dict[str, list[str]] = field(default_factory=dict)
    twelve_changsheng: dict[str, str] = field(default_factory=dict)
    known_facts: list[KnownFact] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
```

v5 不使用这个 dataclass。`run_v5(chart: dict)` 接受松散字典，字段如 `pillars/current_dayun/current_year/case_id`。[`ChartFactLedger`](engine/decision/models.py:43) 是决策层的另一份事实账本，[`ChartFeatureVector`](engine/features/types.py:20) 是派生特征。三套盘面模型并存。

### 旧结果：[`AnalysisOutput`](engine/domain/analysis.py:182)

字段包括 `energy`、`picture`、`gate_results`、`support`、`final_conclusions`、`conflicts`，以及后来追加的 `parallel_analysis`、`theory_findings`、`blind_findings`、`fusion_findings`、`prediction`。单条断语是 [`FinalConclusion`](engine/domain/analysis.py:20)：`statement/domain/layer/contributing_schools/confidence/evidence/yingqi_year`。

### 新结果：[`V5Claim`](engine/v5/domain.py:141)

```python
@dataclass(frozen=True)
class V5Claim:
    claim_id: str
    school: V5School          # ziping/ditiansui/gao/duan/yang/ren
    domain: str
    claim: str
    claim_type: V5ClaimType   # structure/event/timing/evidence/counter
    stance: V5Stance = "support"
    confidence: V5Confidence
    evidence: list[V5Evidence]
    probabilistic: bool = False
```

`run_v5()` 返回 `V5Output`：`claims + structure_graph + arbitration_results + prediction_ledger + adjudication_units`。这是重构时应保留的命题边界；不应继续把所有旁路嵌进一个 40MB 的 `AnalysisOutput`。

## 5. 语料库 / 规则库的形态与调用机制

没有 sqlite 向量库，也没有 embedding 索引。组织方式是四层：

| 层 | 路径 | 形态 | 是否被运行时检索 |
|---|---|---|---|
| 原始讲义 | [`sources/`](sources/) | 13.03MB，136 个 MinerU Markdown | 否。只作来源 |
| 派别规则 | `theory/{school}/index.yaml` | 结构化 YAML | 盲派三校会被 v5 全量加载 |
| 生产规则 | [`theory/production/`](theory/production/) | 小 YAML，带 trigger | 旧 pipeline 与 v5 都加载 |
| 统一 IR | [`theory/_ir/unified_rule_ir.yaml`](theory/_ir/unified_rule_ir.yaml) | 7.75MB，约 2955 条 | 未发现被 `run_pipeline` / `run_v5` 检索 |

规则条目数（按文件内 `- id:` / `- rule_id:` 计）：

| 文件 | MB | 条目约数 |
|---|---:|---:|
| [`theory/duan/index.yaml`](theory/duan/index.yaml) | 0.090 | 290 |
| [`theory/gao/index.yaml`](theory/gao/index.yaml) | 0.156 | 261 |
| [`theory/yang/index.yaml`](theory/yang/index.yaml) | 0.066 | 163 |
| [`theory/ren/index.yaml`](theory/ren/index.yaml) | 0.072 | 200 |
| [`theory/ziping/index.yaml`](theory/ziping/index.yaml) | 2.493 | 933 |
| [`theory/tiaohou_ditiansui/index.yaml`](theory/tiaohou_ditiansui/index.yaml) | 2.668 | 1108 |
| [`theory/_ir/unified_rule_ir.yaml`](theory/_ir/unified_rule_ir.yaml) | 7.749 | 2955 |

子平与滴天髓 index 很大，但 v5 默认不扫描这两份 index；它只跑独立打分器，再加载 `theory/production/` 里 `quantifiable=True` 的生产规则。因此 2000 多条传统规则大多停留在知识库。

### 样本

段派规则，[`theory/duan/index.yaml`](theory/duan/index.yaml)：

```yaml
- id: M1-D-001
  school: duan
  topic: lifa
  topic_label: 宾主
  title: 宾主第 1 层 — 日干 vs 其它 7 字
  status: confirmed
  layer: unmapped
  raw_anchor: §17.1 宾主
  raw_file: theory\raw\duan\promoted\m1-patterns.md
  candidate_score: 4.0
  hits: 2
  misses: 0
```

统一 IR 只是把同一条再包一层，[`theory/_ir/unified_rule_ir.yaml`](theory/_ir/unified_rule_ir.yaml)：

```yaml
schema_version: RuleIR-2026-06-13
rules:
- rule_id: M1-D-001
  theory_id: duan
  source_path: theory/duan/index.yaml
  statement: 宾主第 1 层 — 日干 vs 其它 7 字
  semantic_tags:
  - topic:lifa
  - topic_label:宾主
  element_vector: {wood: 0, fire: 0, earth: 0, metal: 0, water: 0}
  status: confirmed
```

生产规则是另一种更窄的 schema，[`theory/production/ziping-career-structure-rules-v1.yaml`](theory/production/ziping-career-structure-rules-v1.yaml)：

```yaml
schema_version: ziping-career-structure-rules/v1
school_id: ziping
task_id: career.role_change
domain: 事业
claim_type: structure_claim
required_facts:
  - ten_god_counts.正官
  - geju_profile.geju_type
required_gates:
  - complete_fact_closure
  - official_path_anchor
```

原始讲义样本，[`sources/duan/MinerU_markdown_体用_2056043694349017088.md`](sources/duan/MinerU_markdown_体用_2056043694349017088.md) 开头：

> 每一类术数学都讲体用……以宫位为体，星为用。婚姻看妻宫为体、妻星为用；父母之体用不能换。随后是乾造甲申、甲戌、丙寅、壬辰的课堂断例。

加载路径：

- 生产规则：[`load_default_production_library()`](engine/application/production_rule_loader.py:96) → `yaml.safe_load` → [`rule_triggered()`](engine/application/production_rule_triggers.py:25) 的 trigger 名字 if-else。
- 盲派：[`_load_blind_school_rules()`](engine/v5/runner.py:415) 一次读完 index，再 [`score_blind_rule()`](engine/predicates/condition_evaluator.py:182) 做字符袋打分，截断 15 条。
- 原始 Markdown：没有运行时检索器。
- 向量检索：不存在。

## 6. LLM / Prompt 接入情况

**当前是纯规则引擎。**

全仓库 `*.py/*.md/*.yaml` 检索 `openai`、`anthropic`、`langchain`、`chromadb`、`faiss`、`sentence_transformers`、`embeddings`，结果为 0。

名字像 Agent 的 [`engine/v2/agents/__init__.py`](engine/v2/agents/__init__.py) 不是模型调用。`BaseDomainAgent.analyze()` 只接收 `DomainEvidence`，`_reason()` 按 `polarity` 把 claim 分进 `main_claims/risk_claims/opportunity_claims`。`CareerAgent`、`WealthAgent` 等六个子类只有一个域名，没有提示词。

`feedback_prompt` 只是 [`engine/decision/models.py`](engine/decision/models.py) 和报告视图里的人工反馈说明文字，例如「请反馈该事件是否发生」，不是发给 LLM 的模板。

## 重构含义

如果目标是「确定性引擎 + 结构化语料 RAG + LLM 多流派融合」，现有代码应拆成三层，而不是在 `AnalysisOutput` 上再挂一个字段：

1. **确定性层只留可计算事实。** 保留 `predicates/`、藏干、长生、刑冲合害、十神、神煞、`ChartFeatureVector`。日主旺衰现在有两套分数，必须先合成一个版本化特征，不能让 v1 和 v5 各判一次。
2. **规则层改成带适用条件的检索，而不是前 15 条字符重合。** `index.yaml` 与 2955 条 IR 已有 `condition/topic/status/source`，但盲派匹配不执行 `condition`。未知 trigger 应弃权，不应返回 True。原始 `sources/*.md` 只能作为引用证据，不能直接当命中规则。
3. **融合层只消费同目标的支持与反对命题。** v5 的 `V5Claim + AdjudicationUnit` 比旧 `integrate()` 更适合当边界。L1 路由已经有适用范围雏形，但没有接入默认执行链；在它接入前，加权平均和条数投票都会把不适用流派算进结论。

不建议先引入向量库或 LLM。当前最先失真的位置是规则触发与流派适用门，不是文案生成。
