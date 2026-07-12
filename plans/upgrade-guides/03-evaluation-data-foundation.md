# 升级指导 03 · 评估数据地基与真实标注回流

> 日期：2026-07-12
> 文档类型：实施指导（供强模型执行）
> 服从：[`docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md`](../../docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md)
> 路线阶段：对应 Phase 0（最小证明与数据盘点）
> 依赖：无前置代码依赖；本指导是整个升级飞轮的**燃料**，应最先或与指导 01 并行启动
> 被依赖：指导 04（L1 回流飞轮）无本指导产出的真实标注数据则完全空转

---

## 1. 为什么这是最高优先级的非架构任务

已合并的 [`engine/evaluation/`](../../engine/evaluation/) 盲测评估框架是全仓库工程质量最高的资产（7 任务 + 3 轮整体验收 + 147 测试），但它现在**称的是空气**：

- 绝大多数 [`cases/*/feedback.md`](../../cases/) 的标注表是空的 `[ ]`；
- 没有一份 reviewed manifest（含 `expected_schools` 与六维 `eligible_routes`）；
- 没有 frozen blind run，没有 revealed labels，没有真实 `CapabilityPosterior`。

**没有真实标注数据，后面所有"变准了没"都无法验证。** 这个指导的产物是：一批经过污染审计、结构化标注、可冻结盲测的评估数据包，让评估框架第一次产出非空的六维能力后验基线。

这是把"秤"校准好，然后才能称"厨师"。

---

## 2. 目标与验收总纲

### 2.1 目标

1. 盘点全部 [`cases/`](../../cases/) 案例的出生信息完整度、反馈完整度、标签可信度、是否参与过规则开发（污染）；
2. 产出机器可读的案例分级清单（开发污染 / 历史盲测可用 / 前瞻可用 / 不可量化）；
3. 对 ≥30 个可用案例，把 [`feedback.md`](../../cases/) 的自由文本反馈转成结构化任务标签（对齐 [`mapping/school-capability-task-catalog-v1.yaml`](../../mapping/school-capability-task-catalog-v1.yaml) 的 18 项任务）；
4. 为这批案例产出 reviewed manifest（`school-capability-case-manifest/v1`），补齐 `expected_schools`、六维 `eligible_routes`、`reviewed_by`；
5. 跑通 `audit → freeze → score → report` 全链，产出第一份真实六维能力后验基线报告。

### 2.2 硬验收门槛（对齐路线 Phase 0 GO）

- ≥30 个案例有完整结构化标注，且每条标签记录 6 字段：`source / observed_at / confidence_grade / quantifiable / conflict_state / reviewer`；
- 污染案例被明确标为 `development_only`，绝不进入盲测评分；
- 评估框架产出**非空** posterior，报告不再是 HOLD-because-empty；
- 至少一个任务能从 Fact 追溯到 Claim、ArbitrationResult、Prediction；
- 报告不泄露内部 ID。

---

## 3. 现状事实（as-built，动手前先确认）

| 事实 | 位置 | 影响 |
|---|---|---|
| 反馈表大量为空 `[ ]` | [`cases/*/feedback.md`](../../cases/) | 需人工/半自动补标注，这是本指导主要工作量 |
| 标注协议已定义 y/n/?/skip | [`templates/feedback.md`](../../templates/feedback.md) | 复用，不要另造标注符号 |
| 案例 school-claims 为人工手写 | `cases/*/*.v5.json` | 这些**不能**作为盲测输出；盲测输出必须由引擎冻结生成（见指导 02） |
| 评估框架要求 reviewed manifest | [`engine/evaluation/case_audit.py`](../../engine/evaluation/case_audit.py)、[`tools/school_capability_baseline.py`](../../tools/school_capability_baseline.py) | audit 产出 `school-capability-case-audit/v1`，需人工提升为 reviewed manifest |
| 已有反馈摄入工具 | [`tools/feedback_ingest.py`](../../tools/feedback_ingest.py)、[`tools/case_feedback_intake.py`](../../tools/case_feedback_intake.py) | 复用其解析能力，不要重写 |
| 六维身份定义 | 见核心宪法 §5.13 CapabilityPosterior | 标注时必须能映射到 chart_prototype / time_horizon / evidence_band |

**关键约束**：本指导只做数据与标注，**不改引擎推理代码**。标注产物是数据文件，不是逻辑。

---

## 4. 工作分解

### Task 03-A：案例污染与可用性盘点

产出机器可读清单 `META/school-capability-case-inventory.json`，每个案例记录：

```text
case_id
birth_info_complete: bool        # 四柱/性别/历法/大运是否齐全
feedback_present: bool           # feedback.md 是否有真实标注（非空 [ ]）
feedback_grade: high|medium|low  # 标签可信度
development_contaminated: bool   # 是否参与过规则开发/调参
contamination_evidence: [str]    # 污染证据（如 reports 含反馈校准段、rule-changelog 引用）
classification: development_only | historical_blind | prospective | not_scorable
notes: str
```

污染判定必须保守：**只要无法证明清洁，默认 `development_only`**。污染证据来源：
- [`META/rule-changelog.md`](../../META/rule-changelog.md) 中引用过该 case；
- 报告中含"反馈校准""已验""既有反馈"字样（对齐 [`engine/evaluation/case_audit.py`](../../engine/evaluation/case_audit.py) 的 `feedback_calibrated_report` 标记）；
- [`META/calibration/`](../../META/) 快照涉及该 case。

### Task 03-B：结构化任务标注

对 `historical_blind` 与 `prospective` 案例，把 [`feedback.md`](../../cases/) 自由文本转成对齐 18 项任务目录的结构化标签。

单条标签结构（写入 `cases/<case_id>/school-capability-labels.json`，对齐 [`templates/school-capability-labels.json`](../../templates/school-capability-labels.json)）：

```text
case_id
task_id                    # 对齐 task-catalog-v1
observed_value             # 按 task 的 label_schema：occurred/not_observed、类别、年份、rank
source                     # 命主自述 / 第三方 / 档案
observed_at
confidence_grade           # high/medium/low
quantifiable: bool
conflict_state             # none / conflicting_sources
reviewer                   # 标注人（非空，硬要求）
```

标注纪律：
- 无法可靠映射的任务 → 不产出标签（不要猜），对应任务在该案例记 no_data；
- 性格/画像任务只做双盲一致度，不编造事件概率；
- 高风险任务（灾病/离婚/重大损失）标注需 `confidence_grade` 佐证来源，宁缺毋滥。

### Task 03-C：reviewed manifest 生成

先跑 audit 生成审计草稿：

```bash
python -m tools.school_capability_baseline audit --cases cases/ --out <audit-manifest.json>
```

再人工提升为 reviewed manifest（`school-capability-case-manifest/v1`），补齐：
- `reviewed_by`（非空）；
- `expected_schools`（本批次预期参评的流派全集，非空唯一）；
- 六维 `eligible_routes`：每个 `(case_id, task_id)` 标注其 `chart_prototype_id`、`claim_type`、`time_horizon`、`evidence_completeness_band`。

`chart_prototype_id` 来源：指导 01 的命局特征向量层产出。若指导 01 未就绪，本批次可先用粗粒度原型（身强/身弱/从格候选三分类）占位，并在 manifest 标注 `prototype_provisional: true`。

### Task 03-D：跑通全链并产出基线报告

```bash
# 冻结盲测输出（输出由引擎生成，见指导 02；Phase 0 若引擎未就绪，可用受限 binary 任务子集）
python -m tools.school_capability_baseline freeze --outputs <blind-outputs.json> --task <task-doc> --rule-snapshot <snapshot> --out <frozen.json>

# 揭示标签并评分
python -m tools.school_capability_baseline score --manifest <reviewed-manifest.json> --frozen <frozen.json> --labels <labels.json> --config <eval-config.json> --out <scores.json>

# 生成基线报告
python -m tools.school_capability_baseline report --scores <scores.json> --out META/school-capability-baseline-<date>.md
```

---

## 5. 与"什么八字用什么法"的关系

本指导产出的六维能力后验基线，是指导 04（L1 回流飞轮）的**唯一合法输入**。没有它：
- L1 无法学习"什么命局该信哪派"；
- 所有"变准了"的断言都无法证伪；
- 评估框架的门禁永远停在 HOLD-because-empty。

标注质量直接决定飞轮质量。**宁可 30 个高质量标注，不要 100 个低质量猜测**——低质量标签会把飞轮训歪，比没有更糟。

---

## 6. 风险与红线

| 风险 | 处理 |
|---|---|
| 污染案例混入盲测 | 保守分级，无法证明清洁即 `development_only`；这是不可协商红线 |
| 标注者主观倾向 | 标签必须记 `reviewer` 和 `source`；高风险任务要求第二人复核 |
| 反馈文本与报告结论循环污染 | 标注只依据命主真实经历，禁止从系统旧报告反向抄结论 |
| 样本不足硬凑 | 不足 30 个高质量案例 → 进入 HOLD，不得用污染案例凑数（对齐路线 §7.1） |
| 标签泄漏进 runner | 标注文件与 runner 输入物理隔离；发现泄漏则整批作废（对齐宪法 §3.6） |

---

## 7. 交付物清单

1. `META/school-capability-case-inventory.json` — 全案例分级清单；
2. `cases/<case_id>/school-capability-labels.json` — ≥30 份结构化标签；
3. reviewed manifest（≥1 份，覆盖标注案例）；
4. `META/school-capability-baseline-<date>.md` — 第一份真实六维能力后验基线报告；
5. 一份简短盘点说明：可用案例数、污染案例数、各任务标签覆盖、HOLD/GO 判定。

交付后，Phase 0 GO/HOLD 由基线报告与本清单共同判定，写回 [`plans/bazi-intelligence-platform-roadmap.md`](../bazi-intelligence-platform-roadmap.md) §16 阶段状态。
