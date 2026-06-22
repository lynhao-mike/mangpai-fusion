# 2041 条生产规则库统一审计与修复方案

**基线确认（2026-06-22）**  
- 子平生产规则：**933** 条，来源 [`theory/ziping/index.yaml`](theory/ziping/index.yaml)  
- 滴天髓调候派生产规则：**1108** 条，来源 [`theory/tiaohou_ditiansui/index.yaml`](theory/tiaohou_ditiansui/index.yaml)  
- 默认生产规则总数：**2041** 条  
- 上次校准基线：**312** 条（Phase-300，2026-06-12）

---

## 一、事实汇总之绝对判断

| 文件 | 关键数字 | 影响 |
|---|---|---|
| [`theory/ziping/index.yaml`](theory/ziping/index.yaml) | 933 条 | 自旧基线 57 条 **×16** 扩容 |
| [`theory/tiaohou_ditiansui/index.yaml`](theory/tiaohou_ditiansui/index.yaml) | 1108 条 | 自旧基线 255 条 **×4.3** 扩容 |
| [`META/mapping-recovery-audit.md`](META/mapping-recovery-audit.md:11) | `rule_id → statement_index` 覆盖率 **0%** | 2041 条规则 **无一** 能挂到现有反馈 |
| [`META/mapping-recovery-audit.md`](META/mapping-recovery-audit.md:19) | 554 反馈行中 **534 行** `rule_id=UNMAPPED` | 规则与反馈之间的链路完全断裂 |
| [`META/mapping-recovery-audit.md`](META/mapping-recovery-audit.md:279) | 4797 条 statement 中 `rule_id` 字段覆盖率 **0.00%** | statement_index 无法作为规则桥 |
| [`META/feedback-governance-remediation-plan.md`](META/feedback-governance-remediation-plan.md:13) | 100% fallback_yaml_trigger | 旧校准数据不可用 |
| [`META/feedback-governance-remediation-plan.md`](META/feedback-governance-remediation-plan.md:57) | 27/100 案例有反馈信号 | 有效反馈覆盖严重不足 |
| [`theory/ziping/_extracted_rules_summary.md`](theory/ziping/_extracted_rules_summary.md:5) | 933 条均 `confidence=0.72/★4/sample_n=1` | 无任何规则级校准数据 |
| [`theory/tiaohou_ditiansui/_extracted_rules_summary.md`](theory/tiaohou_ditiansui/_extracted_rules_summary.md:5) | 1108 条均 `confidence=0.72/★4/sample_n=1` | 无任何规则级校准数据 |
| 两文件均缺 | `quantifiable` 字段 = 全部缺失 | 无法区分可量化规则 vs 解释性规则 |

### 核心判断

**2041 条生产规则库 = 已生产化，未反馈化。**

- 规则数量已经从 312 扩容到 2041（×6.5）
- 但反馈映射链还停留在旧基线时代
- 没有任何一条新规则被真实反馈验证过置信度

---

## 二、需要先处理的根本性缺陷（Ponytail：只提必须修的）

### 2.1 反馈桥完全断裂（阻塞级）

**问题**：新规则库的 ID 格式全部为 `ZP-PROD-20260622-001` / `DTS-PROD-20260622-001`，但现有反馈映射仍然只有旧 `M*` 和 `UNMAPPED`。见 [`META/mapping-recovery-audit.md`](META/mapping-recovery-audit.md:19)。

**为什么阻塞**：如果无法回答“这条反馈对应哪条规则”，任何命中率计算都不成立。

**修复前提**：必须先修 [`statement_index.json`](cases:1) 的规则字段覆盖率，否则 feedback 无法对接 rules。

### 2.2 量化开关缺失（结构级）

**问题**：2041 条规则全部没有 `quantifiable` 字段。

**后果**：
- 总纲类规则（“天地之间，一气而已”）与细断类规则（“财旺克印，贪玩误学”）被同等对待
- 前者只应作为解释性证据，不应计入 hit/miss 学习

**已知社区共识**：任派 [`M3-R-003`](META/arbitration-log.md:412) 已在仲裁中被标记为 `quantifiable: false`，证明这个方向已经被需要了。现在 2041 条规则里同样需要区分。

### 2.3 层统一预设为“互补”（结构级）

**问题**：2041 条规则的 `layer` 全部为 `互补`。

**后果**：冲突仲裁时无法区分：
- 某条规则是 consensus 级（多派同向）
- 还是 complementary 级（一家之言）

**修复方向**：layer 不应在抽取阶段就统一赋死值，应根据 rule_type、topic、cross-school 关系动态设定。

### 2.4 默认置信度全部相同（校准级）

**问题**：2041 条规则全部 `star: 4, percent: 0.72, sample_n: 1`。

**后果**：任何 hit/miss 统计都会因初始值一致而失去区分度。这不是规则本身的问题，而是需要一张空表来填反馈数据，但填之前应该至少在抽取阶段区分：
- 从古籍直接引用的原文 → 默认置信可低一档
- 从命例反向归纳的规则 → 默认置信可高一档

### 2.5 旧校准文件全部过期（文档级）

以下文件已事实过期（基线是 57/255 规则，实际是 933/1108）：

| 文件 | 旧基线 | 当前基线 | 影响 |
|---|---|---|---|
| [`META/phase-300-calibration.md`](META/phase-300-calibration.md:4) | 312 条 | 2041 条 | school vote/canon vote 数据不可沿用 |
| [`META/theory-validation-sprint-01.md`](META/theory-validation-sprint-01.md:12) | 57+255 | 933+1108 | 覆盖分析已过时 |
| [`META/canon-school-governance-design.md`](META/canon-school-governance-design.md:45) | 57:255 | 933:1108 | school lane 设计需重算 |
| [`META/progress-report-2026-06-09.md`](META/progress-report-2026-06-09.md:42) | 57 / 255 | 933 / 1108 | progress 状态应更新 |

---

## 三、修复优先级（按阻塞级别）

### P0 级（不修则后续全无意义）

#### P0-1：修 feedback → rule 映射桥

**目标**：`statement_index.json` 中每一条 statement 真正挂上 `rule_id / family_id / school / rule_type` 字段。

**怎么做**：

1. 改 [`tools/render_report.py`](tools/render_report.py:1) 或 [`engine/statement_runtime.py`](engine/statement_runtime.py:1) 的写回逻辑：当 report 渲染中引用了一条 production rule 时，把 rule 的元数据写入 `statement_index.json`。
2. 对于已存的 case，统一补写 `statement_index.json` 的元数据字段。
3. 验收：随机抽 5 个 case，检查 `statement_index.json` 中 `rule_id` 覆盖率 > 0。

#### P0-2：禁止把 `UNMAPPED` / fallback 数据用于规则学习

**怎么做**：

1. [`tools/feedback_loop.py`](tools/feedback_loop.py:1) 或 [`tools/feedback_ingest.py`](tools/feedback_ingest.py:1) 入口处过滤：`rule_id == "UNMAPPED"` 的行不进 posterior 更新。
2. `needs_mapping_repair=true` 的行不进 learnable 样本。
3. 验收：learnable 样本量从当前 12 降到 0（说明之前 12 条也是假的），才算打通。

---

### P1 级（规则结构治理）

#### P1-1：为 2041 条规则补 `quantifiable` 字段

**怎么做**：

1. 在 [`theory/SCHEMA.md`](theory/SCHEMA.md:1) 中明确定义：`quantifiable: true` = 允许进入 hit/miss 学习；`false` = 只做解释性引用。
2. 运行一次批量修改：[`theory/ziping/index.yaml`](theory/ziping/index.yaml) + [`theory/tiaohou_ditiansui/index.yaml`](theory/tiaohou_ditiansui/index.yaml)：
   - `trigger=always` 且 `topic` 不在细断类（非 wealth_structure, non-official_career 等）→ `quantifiable: false`
   - `layer=互补` 且 `domains` 覆盖超过 5 个 → `quantifiable: false`（泛化规则）
   - 其余 → `quantifiable: true`
3. 验收：`quantifiable: true` 的比例从 100% 降到 50-65%（可量化规则不应超过总数的 2/3）。

#### P1-2：重新分层

**怎么做**：

1. 去掉当前全量 `layer: 互补` 的统一预设。
2. 按以下条件自动分层：
   - `topic in (wealth_structure, official_career, marriage_family, food_injury, seal_resource)` → `layer: consensus`（结构类规则默认共识）
   - `topic in (cold_warm_dry_wet, source_flow, zhonghe_pianku, qi_momentum)` → `layer: 互补`（气势调候类默认补充层）
   - `domains` 覆盖 ≤ 2、且有明确 `trigger` 的 → `layer: 独门`（专精补强层）
3. 验收：`layer: 共识` 不应超过规则总量的 40%。

---

### P2 级（校准基础设施）

#### P2-1：选定首批 20 个可用的 calibration case

**怎么做**：

1. 从 [`META/feedback-governance-remediation-plan.md`](META/feedback-governance-remediation-plan.md:74) 的 27 案中，选出：
   - 非 fallback 运行能通过的 case
   - 反馈信号清晰的（`y` / `n` 明确，[`feedback.md`](META/feedback-governance-remediation-plan.md:25) 格式达标）
   - 有 [`statement_index.json`](cases:1) 的 case
2. 为这 20 个案补写 `statement_index` 的规则元数据（P0-1 的输出）。
3. 目标是这 20 个案成为首批可验证的 calibration 白名单。

#### P2-2：建立 rule_type 分 lane 学习基础设施

**怎么做**：

1. 在 [`engine/feedback/`](engine:0)（或合适位置）新建设计文档，定义：

```text
STRUCTURE → 结构主票 lane：参与主命中率计算
EVENT → 事件主票 lane：参与主命中率计算
TIMING → 单独应期 lane：不参与结构命中率
GENERAL_PRINCIPLE → 解释票 lane：不进 hit/miss
ANTI_PATTERN → veto/风险 lane：不进正向主票
```

2. 在 [`tools/feedback_loop.py`](tools/feedback_loop.py:1) 中增加 lane 过滤器。
3. 验收：`GENERAL_PRINCIPLE` 和 `ANTI_PATTERN` 的 hit/miss 不计入 rule posterior。

---

### P3 级（文档同步）

#### P3-1：更新以下过期文件

| 文件 | 更新内容 |
|---|---|
| [`META/theory-validation-sprint-01.md`](META/theory-validation-sprint-01.md:12) | 规则总数从 312 改为 2041 |
| [`META/progress-report-2026-06-09.md`](META/progress-report-2026-06-09.md:42) | 子平/滴天髓条数从 57/255 改为 933/1108 |
| [`META/phase-300-calibration.md`](META/phase-300-calibration.md:1) | 标注“基线过期，不可用于当前规则库” |
| [`META/canon-school-governance-design.md`](META/canon-school-governance-design.md:45) | school lane 按新比例重算 |

---

## 四、不可做的三件事（Ponytail 约束）

1. **不要在 P0 未完成前重跑 Phase-300 校准**：旧校准是瓶颈入口问题，不是新规则库问题。先修桥，再校准。
2. **不要手动给 2041 条规则单独设置信度**：当前统一 0.72 没有问题，问题是没有反馈数据。等 P0/P1 完成后自然产生差异。
3. **不要在旧过时文件上修修补补**：如果重新校准，考虑新建校准文件（如 `META/calibration-v2/`），不与旧口径混在一起。

---

## 五、当前正确的结论

> 子平 933 条、滴天髓 1108 条，都已是大规模生产规则库。
> 最大问题不是哪条规则对或错，而是**这 2041 条规则与现有反馈数据之间没有可工作的映射桥**。
> 修复顺序：先修桥，再分类，再校准确认，再谈实战有效性。

---

## 六、修复时间线（保守估计）

| 阶段 | 步骤 | 预期工作 |
|---|---|---|
| 1. 修桥 | P0-1 + P0-2 | 改 2-3 个文件 + 补写 statement_index |
| 2. 分类 | P1-1 + P1-2 | 改 2 个 YAML 文件 + 跑批量脚本 |
| 3. 校准 | P2-1 + P2-2 | 20 个白名单 case + 设计文档 |
| 4. 文档 | P3-1 | 更新 4 个 META 文件 |
