# 置信度模型契约 · 06-confidence-model

> **本文规定 v1.2 双轨置信度（★+%）的精确数学公式与聚合规则。**
> 这是引擎所有"× ★X (X%)"输出的"宪法"。

最后更新：2026-05-26（v1.4 W1 · 增 § 二·1 决策 E Beta 切换计数公式）
版本：v1.3.0-current
依赖：05-rule-lifecycle（Beta 计算的源头）+ 04-gate-protocol（三层 gate 上限）+ decisions-locked.md 决策 E

---

## 一、设计原则

1. **双轨**：★（命理师好读）+ %（数据精确）必须**双向一致**——不允许 ★★★(85%) 这种矛盾搭配
2. **诚实**：数据少时不允许虚高；变异度大时强制 -1★
3. **保守聚合**：多规律联立时，倾向于"最强单条" + 边际加权，**不做天真平均**
4. **gate 限顶**：再高的规律置信度，三层 gate 不通过也不能 ★★★★★
5. **不可篡改**：引擎自动算出，AI 不能直接修改 confidence 字段
6. **切换条件明确**（v1.4 W1 补）：决策 E 从"线性加权"切到"Beta 后验"的阈值口径必须是单一公式（§ 二·1），不允许文档间分歧。

---

## 二、单规律置信度（详见 05-rule-lifecycle § 四）

```python
# 见 05-rule-lifecycle.md
# Beta(α=hits+1, β=misses+1)
# posterior = α/(α+β); variance = αβ/((α+β)²(α+β+1))
# star ∈ {1,2,3,4,5} from posterior bins
# variance > 0.15 → star -= 1
```

5 个 ★ 的 % 区间映射（**双向唯一**）：

| ★ | posterior 区间 | 显示 % |
|---|---|---|
| ★ | [0.00, 0.40) | 0%-39% |
| ★★ | [0.40, 0.55) | 40%-54% |
| ★★★ | [0.55, 0.70) | 55%-69% |
| ★★★★ | [0.70, 0.85) | 70%-84% |
| ★★★★★ | [0.85, 1.00] | 85%-100% |

**显示规则**：
- 引擎一律输出 `★N (XX%)`，其中 % 是 `round(posterior * 100)`
- 报告中 `★X` 与 `XX%` 的区间必须一致；output_linter 校验

### 2.1 决策 E Beta 切换计数公式（v1.4 W1 锁定）

> **背景**：决策 E（[`decisions-locked.md`](decisions-locked.md) E 行）规定"≥30 反馈样本切 Beta 后验"。但"30 是怎么数的"在 v1.3 各文档中未明确，造成 STATUS.md 当前显示"11/30"或"10/30"或"12/30"的口径分歧。本节锁定唯一公式。

**Beta 切换计数公式**

```
N_eff = N_y + N_n + 0.5 · (N_late_hit + N_late_miss)

其中：
  N_y          = master 反馈中 [y] 标注总数（D5 直接命中）
  N_n          = master 反馈中 [n] 标注总数（D5 直接失验）
  N_late_hit   = late_feedback.py 在半年窗外回填的 hit 总数（D7，权重 0.5）
  N_late_miss  = late_feedback.py 在半年窗外回填的 miss 总数（D7，权重 0.5）

  [?] / [skip] 标注（D5 不计数 verdict）→ 不进入分母
  abstain（部分应验）→ 不进入分母（不是 hit 也不是 miss）
  no_data → 不进入分母
  V1 quantifiable=False 跳过的规律级 verdict → 不进入分母（已被 ingest 层过滤）
  V2 domain 不匹配跳过的规律级 verdict → 不进入分母（已被 ingest 层过滤）

切换条件：N_eff ≥ 30 时，feedback_loop._apply_rule_verdicts 改用
         Confidence(posterior=Beta_mean, variance=Beta_variance) 输出，
         不再走线性加权（4:6 静态:动态）的 v1.0 fallback。
```

**公式锚点**：

- `N_y` / `N_n` 来源：[`tools/feedback_ingest.py`](../../tools/feedback_ingest.py) `parse_statement_feedback` 解析 `[y]` / `[n]` 标注，再经 `fanout_to_rules` 决断力优先合并到 rule-level（miss > hit > abstain > no_data）。**注意**：分母统计的是 **case-level 完成反馈数 × 规律平均覆盖**，不是 statement-level；细节由 [`META/iteration-state.json`](../../META/iteration-state.json) `feedback_completed_count` 字段维护。
- `N_late_hit` / `N_late_miss` 来源：[`tools/late_feedback.py`](../../tools/late_feedback.py) 当反馈在应期年 ±0.5 年外到达时，hit/miss 各自打 0.5 折扣（D7 决策）。
- 不进入分母的标注：`[?]` 命主当场不知道（D5 决策"入库不计数等待 D7 兑现"）；`[skip]` 解释时未讲到。

**仪表盘口径**：[`STATUS.md`](../../STATUS.md) "决策 E Beta 切换" 行写 **`N_eff / 30`**，其中 N_eff 由本公式计算。**任何文档若与本公式分歧，以本公式为准**。

**当前 N_eff（截至 2026-05-26）**：见 [`STATUS.md`](../../STATUS.md) → § "决策 E Beta 切换"。本契约不硬编码当前值。

---

## 三、多规律联立聚合（同一结论由 N 条规律共同支撑）

```python
def aggregate_confidence(evidences: list[Evidence]) -> Confidence:
    """
    保守聚合：max + 边际加权。
    例：3 条规律 ★★★★(82%) / ★★★★(80%) / ★★★(65%)
        → 不是平均 (82+80+65)/3 = 75.7%
        → 而是 max + 边际：
          base = 82
          margin = (80-50)*0.15 + (65-50)*0.15 = 4.5 + 2.25 = 6.75
          posterior = min(82 + 6.75, 95) = 88.75%
        → ★★★★★ (89%)
    """
    if not evidences:
        return Confidence(star=1, percent=0.0, posterior=0.0, variance=0.5, sample_n=0)

    sorted_ev = sorted(evidences, key=lambda e: e.confidence.posterior, reverse=True)
    base = sorted_ev[0].confidence.posterior

    # 边际加权（历史 v1.0 报告模板来源；当前唯一报告模板为 templates/report-v1.3.md）
    margin = sum(
        max(0, e.confidence.posterior - 0.50) * 0.15  # 0.15 = 单条边际系数
        for e in sorted_ev[1:]
    )

    posterior = min(base + margin, 0.95)  # 顶 95% 防止过拟合

    # 同质规律惩罚：若所有规律都来自同一派，扣 5%（信息冗余）
    schools = {e.school for e in evidences}
    if len(schools) == 1:
        posterior *= 0.95

    # 派别多样性奖励：≥3 派同向 +3%
    if len(schools) >= 3:
        posterior = min(posterior + 0.03, 0.95)

    # 总样本数（用于变异度）
    total_n = sum(e.confidence.sample_n for e in evidences)
    variance = compute_aggregate_variance(evidences)

    star = posterior_to_star(posterior)
    if variance > 0.15:
        star = max(1, star - 1)

    return Confidence(
        star=star, percent=posterior, posterior=posterior,
        variance=variance, sample_n=total_n
    )
```

### 3.1 边际系数 0.15 的来源

边际系数来自 v1.0 历史报告模板中的互补层加权公式；该历史模板已作废，当前报告出口统一为 `templates/report-v1.3.md` 的 C-2026-025 标准：

```
联立加权 = max(scores) + Σ(其余 × 0.15)
```

v1.2 起保留此系数，但加上**派别多样性**修正。

### 3.2 同质 vs 异质示例

| 场景 | 规律来源 | 边际加权 | 派别修正 | 最终 % |
|---|---|---|---|---|
| 4 派同支持，max=85 | 段+杨+任+高 | +6 | +3% | 0.91+0.03 → cap 95% |
| 同派 3 条，max=85 | 段+段+段 | +6 | -5% (同质惩罚) | 0.91 × 0.95 = 86.5% |
| 2 派对立，max=70 | 段(+) vs 杨(-) | 见 § 五 仲裁 | — | — |

---

## 四、应期 GateResult 的置信度

```python
def compute_yingqi_confidence(
    passed_layers: int,
    triggers: list[TriggerEvent],
    l2_via_transition: bool,
    upstream_consistent: bool,
) -> Confidence:
    """
    应期置信度专用计算（与单规律不同）。
    """
    # 1. 三层 gate 上限（决策硬约束）
    gate_ceiling = {0: 0, 1: 3, 2: 4, 3: 5}[passed_layers]
    if gate_ceiling == 0:
        # passed_layers == 0 → 不输出此候选事件
        return Confidence(star=0, percent=0.0, posterior=0.0, variance=1.0, sample_n=0)

    # 2. 触发器信号强度（多触发 = 多信号）
    n_triggers = len(triggers)
    primary_strength = trigger_strength(triggers[0]) if triggers else 0.5

    # 多触发奖励（最多 +0.10）
    trigger_bonus = min(0.10, (n_triggers - 1) * 0.04)

    # 触发类型加权（倒象成立=必凶 +0.05；伏吟+0.03 等）
    type_bonus = sum(trigger_type_bonus(t.type) for t in triggers)

    # 基础 posterior
    posterior = primary_strength + trigger_bonus + type_bonus

    # 3. 过渡期惩罚
    if l2_via_transition:
        posterior -= 0.08
        gate_ceiling = max(1, gate_ceiling - 1)

    # 4. 上游不一致 → 强降级
    if not upstream_consistent:
        posterior -= 0.20
        gate_ceiling = min(gate_ceiling, 2)

    posterior = max(0.0, min(0.95, posterior))
    star = posterior_to_star(posterior)
    star = min(star, gate_ceiling)

    return Confidence(
        star=star, percent=posterior, posterior=posterior,
        variance=0.05,  # gate 路径无 variance 概念，固定低值
        sample_n=n_triggers
    )
```

### 4.1 trigger 强度表（trigger_strength + trigger_type_bonus）

```yaml
触发类型基础强度:
  本字到:        0.65
  伏吟:          0.78
  合冲引动:      0.62
  墓库开闭:      0.60
  藏干透出:      0.58
  倒象成立:      0.85  # 必凶强信号

触发类型加成:
  倒象成立: +0.05
  伏吟:    +0.03
  其他:    +0.00
```


---

## 五、跨派冲突仲裁后的置信度

当某结论由多派给出**对立判断**时（CrossSchoolConflict），按 `engine/arbitration.md` 仲裁。胜方继承自己规律的置信度，但需要应用以下惩罚：

```python
def conflict_resolved_confidence(
    winner_evidences: list[Evidence],
    loser_evidences: list[Evidence],
) -> Confidence:
    base = aggregate_confidence(winner_evidences)
    
    # 冲突存在的事实本身就降低确信度（最少 -0.05）
    base.posterior = max(0, base.posterior - 0.05)
    
    # 失败方信号强度也参与（强反对 = 多减）
    loser_max = max((e.confidence.posterior for e in loser_evidences), default=0)
    if loser_max >= 0.70:  # 反对方 ≥★★★★
        base.posterior -= 0.10
    
    base.star = posterior_to_star(base.posterior)
    return base
```

**输出策略**（决定如何在报告中显示）：

| winner 置信度 - loser 置信度 | output_strategy |
|---|---|
| > 0.30 | "显示主胜方"（loser 不出现） |
| 0.10-0.30 | "并列显示"（同时显示两派立场，winner 主） |
| < 0.10 | "降级输出"（标注"两派持平待回测"，confidence 强制 ≤★★★） |

---

## 六、置信度的全链路血源

```
案例反馈
   ↓ feedback_loop.py
hits/misses (per rule)
   ↓ Beta(α, β)
posterior + variance
   ↓ posterior_to_star + variance penalty
Rule.confidence ★N (X%)            ← 单规律
   ↓ 引擎引用
Findings.evidence[].confidence
   ↓ aggregate_confidence
FinalConclusion.confidence ★N (X%)  ← 报告级别
   ↓ + gate ceiling (for 应期)
GateResult.confidence ★N (X%)
   ↓ + arbitration penalty (for 冲突)
最终展示
```

每一层都**不允许跳过**——这是 trace_id 链的基础。

---

## 七、output_linter 的置信度校验

```python
def lint_confidence(conf_str: str) -> list[str]:
    """
    检查 ★N (XX%) 字符串的合法性。
    返回错误列表（空=合法）。
    """
    errors = []
    m = re.match(r"★(\d) \((\d+)%\)", conf_str)
    if not m:
        errors.append(f"格式错误：{conf_str}")
        return errors
    
    star = int(m.group(1))
    pct = int(m.group(2))
    
    # 区间一致性
    valid_ranges = {1: (0, 39), 2: (40, 54), 3: (55, 69), 4: (70, 84), 5: (85, 100)}
    lo, hi = valid_ranges[star]
    if not (lo <= pct <= hi):
        errors.append(f"★{star} 与 {pct}% 不匹配，应在 [{lo}, {hi}]")
    
    return errors
```

---

## 八、整体报告置信度（overall_confidence）

```python
def compute_overall_confidence(output: AnalysisOutput) -> Confidence:
    """
    报告整体置信度 = 各层加权均值。
    """
    layers = {
        "共识": (sum_conf("共识", output.final_conclusions), 0.40),
        "互补": (sum_conf("互补", output.final_conclusions), 0.30),
        "独门": (sum_conf("独门", output.final_conclusions), 0.20),
        "冲突仲裁": (sum_conf("冲突仲裁", output.final_conclusions), 0.10),
    }
    weighted = sum(c * w for (c, w) in layers.values())
    
    return Confidence(
        star=posterior_to_star(weighted),
        percent=weighted,
        posterior=weighted,
        variance=0.05,
        sample_n=len(output.final_conclusions),
    )
```

报告"画像版"末尾的总置信度即来自此函数。

---

## 九、placeholder 行为（数据缺失时）

新规律首次入库 / 新案首次输出 时：

```python
DEFAULT_PROPOSED = Confidence(
    star=2, percent=0.50, posterior=0.50,
    variance=0.083, sample_n=0
)  # 等价于 hits=0, misses=0 时的 Beta
```

报告中显示为 `★★ (50%) [新规律]` 或 `[试用]` 标签。

### 9.1 无反馈情况下的高置信初始化边界

没有反馈时，报告中的“置信度”不是“算出来的准确度”，而是“结构 + 一致性 + 约束”的稳定性评分。为避免“无反馈时所有输出普遍偏低”与“无反馈也可高置信初始化”两种口径混淆，v5 起将三个概念强制拆轨：

| 轨道 | 含义 | 可无反馈高值 | 报告展示口径 | 禁止事项 |
|---|---|---:|---|---|
| 理论证据强度 `evidence_score` | 命局结构、规则覆盖、多派同向、应期 gate 等内部证据是否足够 | 是，可 ≥0.75 并展开细节 | “证据强 / 理论推断 / 待反馈校准” | 不得直接写成已验证命中率 |
| 结构稳定性置信 `structural_confidence` / report-facing `confidence` | 在当前命盘证据、跨派一致性、冲突裁决和 gate 约束下，结论是否稳定 | 是，可高置信初始化 | “高证据倾向 / 结构稳定 / 需反馈验证” | 不得解释为现实准确率或历史命中率 |
| 反馈验证置信 `validation_confidence` | 该断语或规则是否已被案例反馈验证 | 否，`sample_n=0` 默认 ★★(50%) | “反馈不足 / 需反馈验证” | 不得用无反馈样本输出 ★★★ 以上的验证命中率 |
| 事件概率 `probability_range` | 可反馈事件在时间窗中的受限概率 | 只允许区间，不允许单点伪精确 | “区间概率 / 待校准” | 不得把结构倾向写成确定发生 |

**高置信初始化模型**允许初始化“理论证据强度”和“结构稳定性置信”，但不允许初始化“反馈验证置信”。因此：

1. 无反馈但五派同向、结构强、gate 通过时，可以输出“高证据倾向 / 结构稳定，需反馈验证”。
2. 同一断语若 `sample_n=0`，其“反馈验证置信”仍必须保持 `★★ (50%) [试用]` 或同等保守口径。
3. 若报告需要保留高细节，可通过 `detail_expansion` 的 `evidence_score` 展开，并在不确定性中说明“理论推断，不等同于已被案例验证”。
4. “高置信倾向”在自然语言中容易被理解为“已验证高命中率”，模板推荐改写为“高证据倾向”或“结构稳定倾向”。
5. “普遍偏低”不是目标；目标是“结构稳定性可以高、反馈验证置信必须诚实、二者分轨展示”。

---

## 十、置信度禁忌清单（output_linter 黑名单）

| 禁忌输出 | 原因 | 拦截动作 |
|---|---|---|
| `★N` 不带 % | 双轨缺一 | 拒绝输出 |
| `XX%` 不带 ★ | 双轨缺一 | 拒绝输出 |
| `★5 (50%)` 等区间不符 | 数学错 | 拒绝输出 |
| 应期断语无三层 gate 标记 | 违背 v1.2 灵魂 | 拒绝输出 |
| confidence 没有 evidence 链 | 不可追溯 | 拒绝输出 |
| `sample_n=0` 的反馈验证置信写成 ★≥3 | 把结构稳定性误写成已验证命中率 | 强制标注为结构稳定性评分，或将反馈验证置信降级为 ★★ |

---

## 十一、置信度可视化建议（render_report）

报告中的置信度统一用以下样式：

```
[共识 · 4 派一致] 命主从公门入仕 ★★★★★ (88%)
├─ 来源：M1-D-001(段) / M2-Y-091(杨) / G-XX-005(高) / M3-R-018(任)
├─ 路径：4 派同向 + 大运到位
└─ 证伪：若 65 岁前未在公门体制内 → 失验
```

`output_linter` 校验：
1. 派别标签 `[XX]` 必须出现
2. ★ + (%) 都在
3. 来源（evidence chain）至少 1 条
4. 应期断语额外要求"应期 + 证伪"

---

## 十二、版本演进

| 版本 | 变更 |
|---|---|
| 1.2.0 | 初版 Beta + 5 ★ 映射 + 联立聚合 + gate 限顶 + 仲裁惩罚 |
| **1.3.0-current** | **v1.4 W1：增 § 二·1 决策 E Beta 切换计数公式（N_eff = N_y + N_n + 0.5·(N_late_hit + N_late_miss)），统一 STATUS.md / handoff.md / 03-findings 的"30/30"口径** |

---

**契约结束。W1.3 三份契约（04/05/06）全部交付。**
**W1.4 待写：07 流水线流程 + 08 agent 边界。然后契约冻结，启动 8 agent。**
