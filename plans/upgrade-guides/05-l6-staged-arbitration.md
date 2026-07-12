# 升级指导 05 · L6 分段仲裁与矛盾对撞

> 日期：2026-07-12
> 文档类型：实施指导（供强模型逐项执行）
> 服从：[`docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md`](../../docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md)
> 路线：[`plans/bazi-intelligence-platform-roadmap.md`](../bazi-intelligence-platform-roadmap.md)
> 总览：[`plans/upgrade-guides/00-overview-and-sequencing.md`](00-overview-and-sequencing.md)
> 依赖：本指导消费 02（L2 命题引擎）产出的结构化 Claim；建议在 02 有至少两派引擎化命题后启动。

---

## 1. 目标

把冲突仲裁层从"按置信度数字比大小"升级为**分段裁决 + 显式矛盾对撞**：

1. 结构合法性、事件落地、应期概率三段各自独立裁决；
2. 对直接对立命题（旺 vs 弱、吉 vs 凶、发生 vs 不发生）引入显式冲突消解规则，而非取中庸话术或平均分；
3. 裁决消费 L1 适用性权重（谁在这盘更该被信），而不是无差别平权；
4. 保留少数派观点与冲突理由，不强行制造唯一结论。

**一句话**：L6 从"数字比较器"变成"分段法庭"。

---

## 2. As-Built 现状与差距

### 2.1 当前实现

主实现见 [`engine/decision/l6_arbitration.py`](../../engine/decision/l6_arbitration.py) 的 `build_arbitration_decisions()`：

- 按 domain 分组事件；
- 裁决逻辑仅有四分支：全部 `confidence <= 0.1` → `reject_all`；单条 → `winner`；置信差 `<= 0.05` → `coexist`；否则 → `unresolved`；
- `arbitration_rule` 字段存的是**说明性文字**（"MVP：按同一领域内事件置信差距选择…"），不是可执行逻辑；
- 不区分结构/事件/应期三段；
- 不消费 L1 适用性权重；
- 不处理"A派说旺、B派说弱"这类直接语义对立——它只看数字，不看命题是否互相否定。

v5 侧 [`engine/v5/runner.py`](../../engine/v5/runner.py) 有 `V5ArbitrationResult` 分 stage（structure/event_realization/probability_timing），比 decision 层更接近目标，但融合仍是 support/oppose 计数 + 固定档位打分，没有对立命题的显式消解。

### 2.2 差距定级

| 目标 | 现状 | 差距 |
|---|---|---|
| 三段独立裁决 | v5 有 stage 骨架，decision 层无 | 🟡 |
| 矛盾对撞消解 | 只比数字，不识别语义对立 | 🔴 |
| 消费 L1 适用性权重 | 未消费 | 🔴 |
| 保留少数派 + 冲突理由 | 部分保留（unresolved/coexist） | 🟡 |

---

## 3. 接口契约

### 3.1 输入

```text
arbitrate_staged(
    case_id: str,
    claims: list[Claim],              # 来自 L2 命题引擎（指导 02）
    applicability: ApplicabilityPlan, # 来自 L1（指导 04），含各派权重
    *,
    conflict_rules: ConflictRuleSet,  # 显式对立消解规则集
) -> StagedArbitrationResult
```

- `Claim` 必须已带 `claim_type`（structure_claim / event_claim / timing_claim）、`polarity`、`stance`、`evidence`、`school_id`。
- `ApplicabilityPlan` 提供 `school_weight(school_id, task_id) -> float`，权重来自 L1 条件化能力后验；L1 未就绪时退化为均匀权重并在结果标注 `weight_source="uniform_fallback"`。

### 3.2 输出

```text
StagedArbitrationResult:
  case_id: str
  stages: list[StageDecision]        # 恰好三段：structure / event / timing
  weight_source: str                 # "l1_capability" | "uniform_fallback"

StageDecision:
  stage: "structure" | "event" | "timing"
  domain: str
  result: "winner" | "coexist" | "unresolved" | "reject_all" | "conflict_resolved"
  winner_claim_ids: list[str]
  minority_claim_ids: list[str]
  rejected_claim_ids: list[str]
  conflict_type: "none" | "polarity_opposition" | "magnitude_opposition" | "occurrence_opposition"
  resolution_rule_id: str | None     # 触发的显式消解规则；无则 None
  weighted_support: float
  weighted_oppose: float
  rationale: str
```

**硬约束**：
- 每段裁决独立，不得跨段混合命题（结构命题不与应期命题同台裁决）；
- `conflict_resolved` 只能由显式 `conflict_rules` 命中产生，且必须写 `resolution_rule_id`；
- 禁止取平均置信度当作最终结论；对立命题要么一方胜出（带规则依据），要么 `unresolved`（保留双方）；
- 输出必须可 JSON 往返（复用 evaluation 的 `PersistedContract` 风格）。

---

## 4. 显式冲突消解规则集

### 4.1 三类对立

| 冲突类型 | 定义 | 示例 |
|---|---|---|
| `polarity_opposition` | 同一命题对象，stance/polarity 直接相反 | A派"身旺" vs B派"身弱" |
| `magnitude_opposition` | 同向但程度对立 | A派"轻微破财" vs B派"重大损失" |
| `occurrence_opposition` | 事件发生 vs 不发生 | A派"必离婚" vs B派"婚姻稳定" |

### 4.2 消解规则结构

```yaml
conflict_rule:
  rule_id: CR-STRUCT-旺衰-001
  applies_to_stage: structure
  conflict_type: polarity_opposition
  target_claim_type: structure_claim
  resolution_strategy: capability_weighted   # 见下表
  min_weight_gap: 0.15                        # 权重差小于此值则判 unresolved
  falsifier: 若加权更高一方在盲测集持续劣于对立方，则该规则作废
```

### 4.3 消解策略

| 策略 | 逻辑 |
|---|---|
| `capability_weighted` | 用 L1 权重加权支持度；权重差 ≥ `min_weight_gap` 时高权重方胜，否则 unresolved |
| `evidence_completeness` | 证据完整度高的一方胜；持平则 unresolved |
| `structure_precedence` | 结构层结论优先于事件层（结构不成立则事件命题降级） |
| `conservative_high_risk` | 高风险域（健康灾厄/离婚/重大损失）对立时，强制 unresolved + 风险声明，不允许单方铁断 |

**关键原则**：`conservative_high_risk` 对高风险域是**默认兜底**——任何高风险对立在证据不压倒时必须保留双方，宁可 unresolved 不可武断。这与核心宪法 §8.3 和 evaluation 框架的高风险假阳性双倍成本一致。

---

## 5. 任务分解（TDD）

### Task 5.1 数据契约
- 定义 `StageDecision` / `StagedArbitrationResult` dataclass，JSON 往返。
- 测试：往返一致、三段结构强校验、非法 stage 拒绝。

### Task 5.2 命题分段
- 按 `claim_type` 把 claims 分入 structure/event/timing 三段。
- 测试：混合命题正确分段；无对应段命题时该段产出空裁决而非报错。

### Task 5.3 对立检测器
- 实现 `detect_opposition(claims) -> conflict_type`，识别三类对立。
- 测试：旺/弱→polarity；轻/重→magnitude；发生/不发生→occurrence；无对立→none。

### Task 5.4 消解规则引擎
- 加载 `conflict_rules` YAML，实现四种 `resolution_strategy`。
- 测试：capability_weighted 权重差达标/不达标两路径；conservative_high_risk 强制 unresolved；规则命中写 resolution_rule_id。

### Task 5.5 分段裁决主流程
- 组合 5.2–5.4，产出 `StagedArbitrationResult`。
- 测试：三段独立；L1 权重消费；uniform_fallback 标注；少数派保留。

### Task 5.6 结构优先级传播
- structure 段 `reject_all` 时，event/timing 段对应命题自动降级（不得高于结构上限）。
- 测试：结构不成立 → 下游事件置信被压上限。

### Task 5.7 与旧 L6 并行对照
- 保留旧 `build_arbitration_decisions()` 为对照；新函数独立入口，不改生产编排。
- 测试：同一批 claims 两条路径都能跑，输出可并排比较。

---

## 6. 验收标准

- 三段裁决完全独立，无跨段命题混合；
- 三类对立均能检测并按显式规则消解，`conflict_resolved` 必带 `resolution_rule_id`；
- 高风险域对立在证据不压倒时强制 unresolved；
- 裁决消费 L1 权重，L1 缺失时正确 fallback 并标注；
- 少数派与冲突理由完整保留；
- 不产生任何"平均置信度"式中庸结论；
- 新旧 L6 可并行对照，不动生产入口；
- 全部新增测试通过，`git diff --check` 干净。

---

## 7. 范围边界

**本单元做**：分段裁决、对立消解、L1 权重消费、结构优先级传播、旧路径对照。

**本单元不做**：
- 不切换生产仲裁入口（对照验证通过后由后续单元决定）；
- 不实现 L1 学习本身（消费其输出，学习见指导 04）；
- 不改报告层（L7 消费新结果由后续单元处理）；
- 不新增在线服务。

---

## 8. 风险

| 风险 | 缓解 |
|---|---|
| 对立检测误判（把非对立判成对立） | 对立检测器需正反例测试；不确定时归 none，不强行消解 |
| L1 权重未就绪导致退化 | uniform_fallback 明确标注，不静默 |
| 高风险域被误消解为单方铁断 | conservative_high_risk 为高风险默认兜底，测试强制覆盖 |
| 与 v5 stage 仲裁重复 | 明确本指导针对 decision 层；若统一到 v5，需在 00 总览记录合并决策 |
