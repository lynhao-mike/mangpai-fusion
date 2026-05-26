# 规律生命周期契约 · 05-rule-lifecycle

> **本文规定 v1.2 自迭代闭环的核心：规律的状态机、Beta 更新、降级保险丝。**
> 这是"系统能自我迭代"的具体实现规范。

最后更新：2026-05-26（v1.4 W1 · 增 V1/V2 字段：quantifiable + domain_restriction）
版本：v1.3.0-current
依赖：决策 E（Beta 分布）+ F（全自动）+ G（3 次降级缓冲）+ K（每 10 案扫描）+ V1/V2/V3（v1.4 W1 ingest 跳过）

---

## 一、设计原则

1. **数据驱动**：所有状态变更由案例反馈触发，不靠人工"觉得"
2. **慢启动**：早期 hits/misses 少时不允许虚高置信度（变异度惩罚）
3. **降级带保险丝**：单次失验不动 status，3 次累计才降级
4. **diff 落盘**：每次状态变更都写 META/iteration-log.md，可回滚
5. **跨派比较**：每 10 案扫描一次，识别系统性偏差
6. **测量字段就位**（v1.4 W1）：`quantifiable=False` 框架性心法不参与 hit/miss 计分；`domain_restriction` 限定规律仅在指定域内 ingest 时计分。这是修复"D8 误降级"的关键——见 § 六·1。

---

## 二、规律状态机

```
       ┌──────────────────────────────────────────────────┐
       │                                                  │
       ▼                                                  │
   ┌─────────┐                                            │
   │proposed │  ← 新规律首次入库（n=0）                   │
   └────┬────┘                                            │
        │ 第 1 次案例应用 + 命中                          │
        ▼                                                 │
   ┌─────────┐                                            │
   │candidate│  ← 1-4 案，hit_rate≥50%                    │
   └────┬────┘                                            │
        │ n≥5 + hit_rate≥70%                              │
        ▼                                                 │
   ┌──────────┐                                           │
   │confirmed │  ← 主力规律，被 D1/D2/D3/D4 引擎引用      │
   └────┬─────┘                                           │
        │ 累计 3 次失验（决策 G）                         │
        ▼                                                 │
   ┌─────────────────┐                                    │
   │flagged_for_review│ ← 自动降级，触发 META 审计       │
   └────┬─────────────┘                                   │
        │ 再 1 次失验（n失≥4）                            │
        ▼                                                 │
   ┌──────────┐                                           │
   │deprecated│ ← 完全停用，保留历史                      │
   └──────────┘                                           │
                                                          │
   特殊：drift detect 触发的状态变更                      │
        confirmed → flagged_for_review                    │
        （滑动窗 5 案 hit_rate < 50% 且总 n ≥ 8）         │
```


---

## 三、状态枚举与含义

```python
RuleStatus = Literal[
    "proposed",            # 新规律，从未被应用 (n=0)
    "candidate",           # 候选 (1≤n≤4)
    "confirmed",           # 已确认主力 (n≥5)
    "flagged_for_review",  # 自动标记需检视
    "deprecated",          # 已停用
]
```

**状态对引擎行为的影响**：

| 状态 | D1/D2/D3/D4 是否可用 | 置信度处理 | 出现在报告 |
|---|---|---|---|
| proposed | ✅ 可用 | confidence.star ≤ ★★★（变异度强惩罚）| 标"试用" |
| candidate | ✅ 可用 | confidence.star ≤ ★★★★ | 标"候选" |
| confirmed | ✅ 可用 | 无额外限制 | 正常 |
| flagged_for_review | ⚠️ 仍用但 -1★ | confidence.star -1，且加 "审查中" 标签 | 标"审查中" |
| deprecated | ❌ 不用 | 不参与计算 | 不出现 |

---

## 四、Beta 分布置信度（决策 E）

### 4.1 数学定义

```python
import math

def beta_posterior(hits: int, misses: int) -> tuple[float, float]:
    """
    返回 (posterior_mean, variance)
    
    posterior_mean = (α) / (α + β) where α=hits+1, β=misses+1
    variance = αβ / ((α+β)² (α+β+1))
    """
    α = hits + 1
    β = misses + 1
    mean = α / (α + β)
    variance = (α * β) / ((α + β) ** 2 * (α + β + 1))
    return mean, variance
```

### 4.2 置信度计算

```python
def compute_rule_confidence(hits: int, misses: int) -> Confidence:
    posterior, variance = beta_posterior(hits, misses)
    n = hits + misses

    # 基础 ★ 映射 (0-1 → 1-5)
    if posterior < 0.40: base_star = 1
    elif posterior < 0.55: base_star = 2
    elif posterior < 0.70: base_star = 3
    elif posterior < 0.85: base_star = 4
    else: base_star = 5

    # 变异度惩罚（决策 E 的硬约束）
    if variance > 0.15:
        base_star = max(1, base_star - 1)

    return Confidence(
        star=base_star,
        percent=posterior,
        posterior=posterior,
        variance=variance,
        sample_n=n,
    )
```

### 4.3 数据示例

| hits | misses | n | posterior | variance | base★ | 变异度惩罚 | 最终★ |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 0.500 | 0.083 | 2 | 否 | ★★ |
| 1 | 0 | 1 | 0.667 | 0.056 | 3 | 否 | ★★★ |
| 2 | 0 | 2 | 0.750 | 0.038 | 4 | 否 | ★★★★ |
| 3 | 1 | 4 | 0.667 | 0.040 | 3 | 否 | ★★★ |
| 5 | 0 | 5 | 0.857 | 0.018 | 5 | 否 | ★★★★★ |
| 7 | 1 | 8 | 0.800 | 0.016 | 4 | 否 | ★★★★ |
| 7 | 3 | 10 | 0.667 | 0.020 | 3 | 否 | ★★★ |
| 1 | 1 | 2 | 0.500 | 0.083 | 2 | 否 | ★★ |
| 0 | 2 | 2 | 0.250 | 0.038 | 1 | 否 | ★ |

> **解读**：单次命中（n=1 hits=1）只能给 ★★★ ——这就是"数据少不允许虚高"。

---

## 五、状态转换规则（自动机）

### 5.1 升级规则（auto，决策 F）

```python
def maybe_upgrade(rule: Rule) -> Optional[RuleStatus]:
    n = rule.hits + rule.misses
    rate = rule.hits / n if n > 0 else 0.0

    if rule.status == "proposed" and n >= 1 and rate >= 0.50:
        return "candidate"
    if rule.status == "candidate" and n >= 5 and rate >= 0.70:
        return "confirmed"
    return None
```

### 5.2 降级规则（auto + 3 次缓冲，决策 G）

```python
def maybe_downgrade(rule: Rule, recent_miss: bool) -> Optional[RuleStatus]:
    """
    单次失验不动 status，仅累计 misses。
    3 次累计失验 = confirmed → flagged_for_review。
    """
    if rule.status == "confirmed":
        # 必须连续累计——只统计"自从晋级 confirmed 以来的 misses"
        misses_since_confirmed = rule.misses - rule.misses_at_confirmed
        if misses_since_confirmed >= 3:
            return "flagged_for_review"

    if rule.status == "flagged_for_review":
        misses_since_flagged = rule.misses - rule.misses_at_flagged
        if misses_since_flagged >= 1:  # 再失验 1 次直接 deprecated
            return "deprecated"

    return None
```

### 5.3 漂移检测（drift_detect.py）

```python
def detect_drift(rule: Rule) -> Optional[RuleStatus]:
    """
    confirmed 规律的 last 5 案滑动窗 hit_rate < 50% 且 n ≥ 8 → flagged_for_review
    """
    if rule.status != "confirmed":
        return None
    if len(rule.recent_5) < 5 or rule.hits + rule.misses < 8:
        return None
    recent_hit_rate = sum(rule.recent_5) / 5  # recent_5 是 list[bool]
    if recent_hit_rate < 0.50:
        return "flagged_for_review"
    return None
```


---

## 六、theory/{school}/index.yaml schema（v1.2 → v1.4 W1 升级）

每个规律在 `theory/{school}/index.yaml` 中的字段：

```yaml
- id: M1-D-142
  school: 段
  topic: 婚姻
  description: "辰戌冲夫宫=婚姻坎坷"
  
  # 生命周期
  status: confirmed              # 状态
  status_changed_at: 2026-05-15
  status_history:                # 完整 diff 历史
    - {date: 2026-04-01, from: proposed, to: candidate, case_id: C-2026-001}
    - {date: 2026-05-15, from: candidate, to: confirmed, case_id: C-2026-008}

  # 命中数据
  hits: 5
  misses: 1
  abstained: 2                   # 案例适用但未应用（D2 主动放弃）
  
  # 状态分水岭（用于 maybe_downgrade）
  misses_at_confirmed: 0         # 晋级 confirmed 时累计 misses
  misses_at_flagged: null        # 未触发 flagged 时为 null

  # 滑动窗（用于 drift_detect）
  recent_5: [true, true, true, false, true]   # 最近 5 案命中情况

  # 案例 trace
  applied_cases:
    - {case_id: C-2026-001-庚申戊寅壬子辛丑, year: 2005, hit: false, evidence_chain: [M1-D-142]}
    - {case_id: C-2026-007-乙丑庚辰己丑庚午, year: 2010, hit: true, evidence_chain: [M1-D-142]}
    - ...

  # 置信度
  confidence_cache:
    posterior: 0.857
    variance: 0.018
    star: 5
    percent: 85.7
    last_updated: 2026-05-23

  # ── v1.4 W1 新增字段（V1/V2，可选；省略时按默认行为） ──
  quantifiable: true             # bool，默认 true。
                                 # = false 表示框架性心法（如 M3-R-003 "原局定层次,大运定吉凶,流年定应期"）
                                 # ingest 时整体跳过 hit/miss 计分（见 § 六·1）
  domain_restriction: []         # list[str]，默认空。
                                 # 非空表示规律仅在列出的域内 ingest 时计 hit/miss
                                 # 例：M3-R-031 "六合婚姻应期" 收紧到 [应期]
                                 # 当 ingest 的 conclusion.domain ∉ domain_restriction 时跳过该规律本次计分

  # 黑名单标记
  blacklisted: false
  blacklist_reason: null

  # 元信息
  source: "段建业《盲派命理》§4.2"
  version: 1.2.0
```

### 6.1 V1/V2 ingest 跳过策略（v1.4 决策 V3）

`tools/feedback_loop._apply_rule_verdicts` 在调用 `rule.hits +=1 / misses += 1` 之前先做两层守门（`tools/feedback_loop.py` 实现）：

```python
# v1.4 V1：quantifiable=False → 框架性心法不参与 hit/miss 计分
if not rule.quantifiable:
    diff.notes.append(f"[v1.4-V1] 跳过 {rid}: quantifiable=False"
                      f"（框架性心法不参与 hit/miss 计分）")
    continue

# v1.4 V2：domain_restriction 非空且当前 domain 不在列表中 → 跳过该规律的本次计分
# 注意：vctx.domain 为空时不强制（无法判定域）→ 仍计分，由上层决断力合并兜底
if (rule.domain_restriction
    and vctx.domain
    and vctx.domain not in rule.domain_restriction):
    diff.notes.append(f"[v1.4-V2] 跳过 {rid}: domain={vctx.domain!r} ∉ "
                      f"domain_restriction={rule.domain_restriction}")
    continue
```

**为什么必须有这两个字段（决策动机）**

v1.3 D5/D8 把规律命中率推到"自动升降级"位（§ 五·2 的 maybe_downgrade）。首次 D8 触发就把 3 条 confirmed 规律降为 flagged_for_review（[`META/iteration-report-001.md`](../../META/iteration-report-001.md)）。其中：

- **M3-R-003**（原局定层次,大运定吉凶,流年定应期）= **方法论总纲**，无可量化的 hit/miss——它是"框架性心法"。被错误纳入计分 → 每次 ingest 都被算成 miss → D8 误降级。**V1 quantifiable=False 关闭此误算路径**。
- **M3-R-031**（六合婚姻应期）= **应期域专用规律**，被命理师在"婚姻"域 ingest 时错误引用 → 每个婚姻案件都算 miss → 看起来规律失效，**实则是域定位错位**。**V2 domain_restriction=[应期] 关闭此误算路径**。

不解决 V1/V2，自迭代闭环越跑偏差越大——这是 v1.4 启动的核心动因（[`../../plans/architecture-v1.4.md`](../../plans/architecture-v1.4.md) § 二 决策 V1/V2/V3）。

### 6.2 默认值与向后兼容

| 字段 | 默认值 | 旧 yaml（无字段时）行为 |
|---|---|---|
| `quantifiable` | `True` | 视同 `True`，所有规律默认参与计分 |
| `domain_restriction` | `[]` | 视同空列表，所有域均参与计分 |

`Rule.from_dict` / `_entry_to_rule` 已处理这两个字段的 fallback（见 [`tools/rule_lifecycle.py`](../../tools/rule_lifecycle.py)）。**旧 yaml 不需要回填**——只有显式标注的规律（如 M3-R-003 / M3-R-031）才会写入 yaml；其余规律保持简洁。

---

## 七、feedback_loop.py 主循环

```python
# tools/feedback_loop.py
def ingest_feedback(case_id: str) -> IterationDiff:
    """
    新案归档或反馈到位时调用。返回所有发生的变更。
    """
    case_dir = find_case_dir(case_id)
    feedback = parse_feedback_md(case_dir / "feedback.md")
    analysis = parse_analysis_md(case_dir / "analysis.md")  # 含 trace_id

    diff = IterationDiff(case_id=case_id, ts=datetime.now())

    # 1. 解析每条结论的应验/失验标签
    for conclusion in analysis.final_conclusions:
        verdict = match_verdict(conclusion, feedback)  # hit/miss/abstain/no_data

        # 2. 顺 trace_id 找到所有支撑规律
        for rule_id in conclusion.evidence_chain:
            rule = load_rule(rule_id)
            if verdict == "hit":
                rule.hits += 1
                rule.applied_cases.append({"case_id": case_id, "hit": True, ...})
            elif verdict == "miss":
                rule.misses += 1
                rule.applied_cases.append({"case_id": case_id, "hit": False, ...})
            elif verdict == "abstain":
                rule.abstained += 1
                continue  # abstain 不动 hits/misses
            else:
                continue  # no_data 跳过

            # 3. 更新滑动窗
            update_recent_5(rule, hit=(verdict == "hit"))

            # 4. Beta 重算
            rule.confidence_cache = compute_rule_confidence(rule.hits, rule.misses)

            # 5. 检查升降级 + 漂移
            old_status = rule.status
            new_status = maybe_upgrade(rule) or maybe_downgrade(rule, recent_miss=(verdict=="miss")) \
                          or detect_drift(rule)
            if new_status:
                rule.status = new_status
                rule.status_changed_at = today()
                rule.status_history.append({
                    "date": today(), "from": old_status, "to": new_status,
                    "case_id": case_id})
                if new_status == "confirmed":
                    rule.misses_at_confirmed = rule.misses
                if new_status == "flagged_for_review":
                    rule.misses_at_flagged = rule.misses
                diff.status_changes.append((rule_id, old_status, new_status))

            save_rule(rule)
            diff.rule_updates.append(rule_id)

    # 6. 写 META/iteration-log.md
    append_iteration_log(diff)

    # 7. case_count % 10 == 0 触发跨派扫描
    if total_case_count() % 10 == 0:
        run_cross_school_scan()

    return diff
```

---

## 八、META/iteration-log.md 格式

每次 ingest_feedback 追加一段：

```markdown
## 2026-05-23 14:32 · ingest C-2026-014-丙戌庚子乙亥辛巳

case_count: 14 → 15
trigger: 命主反馈到位

### Rule Updates (8 条)

| rule_id | 派 | hits 旧→新 | misses 旧→新 | conf ★ 旧→新 | status 旧→新 |
|---|---|---|---|---|---|
| G-XX-词馆学堂 | 高 | 1→1 | 0→1 | ★★★★→★★★ | confirmed→confirmed |
| M2-Y-035 财富7等 | 杨 | 4→5 | 1→1 | ★★★★→★★★★ | confirmed→confirmed |
| ...

### Status Changes
- G-XX-词馆学堂: confirmed → confirmed (3 次失验缓冲: 1/3)
- M3-R-XXX 婚期触发: candidate → confirmed (n=5, rate=80%)

### Cross-School Scan
- 触发：case_count = 20（每 10 案）
- 输出：META/conflict-trends.md 已更新

### Rollback Hint
若需回滚到本次 ingest 前：
  git revert <commit-hash>
  并恢复 META/calibration/2026-05-23-after-C-2026-014.snapshot.yaml
```

每次 ingest 同时写一份**快照**到 `META/calibration/{date}-after-{case_id}.snapshot.yaml`，用于一键回滚。

---

## 九、紧急回滚开关（engine/calibration.yaml）

```yaml
# engine/calibration.yaml
freeze_iteration: false   # 紧急时设 true，所有 hits/misses/status 更新都拒绝执行

# 升级阈值（可调）
candidate_min_hits: 1
candidate_min_rate: 0.50
confirmed_min_n: 5
confirmed_min_rate: 0.70

# 降级阈值（决策 G）
confirmed_demote_misses: 3       # 累计失验数
flagged_demote_misses: 1
drift_window_size: 5
drift_min_n: 8
drift_min_rate: 0.50

# 变异度惩罚（决策 E）
variance_threshold: 0.15

# Cross-school 扫描
cross_school_every_n_cases: 10
```

任何阈值修改都需要 PR + 影响评估。


---

## 十、应验/失验/弃用的判定规则（match_verdict）

```python
def match_verdict(conclusion: FinalConclusion, feedback: Feedback) -> Literal["hit","miss","abstain","no_data"]:
    """
    比对结论与反馈，返回应验情况。
    """
    # 优先匹配 known_facts（input.md 中已记录的事实）
    fact = find_matching_fact(conclusion, feedback.known_facts)
    if fact:
        return verdict_from_fact_match(conclusion, fact)

    # 次级匹配：feedback.md 中显式标记
    explicit = parse_explicit_verdict(feedback, conclusion.conclusion_id)
    if explicit:
        return explicit  # "应验" / "失验" / "部分应验" → hit/miss/abstain

    # 时间型应期未到达
    if conclusion.yingqi_year and conclusion.yingqi_year > current_year():
        return "no_data"  # 等待时间触发

    return "no_data"  # 反馈数据不足以判断
```

**部分应验** 的处理（如 C-2026-001 婚姻应了"配偶富贵"但失了"婚期"）：
- 在 feedback.md 中显式分拆为多条 verdict
- 每条 conclusion 独立处理 hit/miss
- 引擎不允许"部分应验"做整体性推断（避免黑箱）

---

## 十一、跨派扫描（cross_school_scan.py）

每 10 案触发，对**同一领域**的不同派别规律做系统性比较：

```python
def cross_school_scan() -> ConflictTrendsReport:
    """
    对每个领域（婚姻/财运/...）：
      统计最近 N 案中各派的 hit_rate
      若派 A 的 hit_rate - 派 B 的 hit_rate > 0.30 持续 ≥ 5 案
      → 标记为系统性偏差，写入 META/conflict-trends.md
    """
    report = ConflictTrendsReport(date=today())
    for domain in ["婚姻","事业","财运","健康","学业","六亲"]:
        rates = compute_school_rates_in_domain(domain, last_n=10)
        # rates = {"段": 0.85, "杨": 0.55, "高": 0.80, "任": 0.78}
        max_school, max_rate = max(rates.items(), key=lambda x: x[1])
        min_school, min_rate = min(rates.items(), key=lambda x: x[1])
        if max_rate - min_rate > 0.30:
            report.add_systematic_bias(
                domain=domain,
                strong=max_school, weak=min_school,
                gap=max_rate - min_rate,
                recommendation=f"调整 dimension-weights.yaml 在 {domain} 上 {max_school} 权重↑, {min_school}↓"
            )
    save_to(report, "META/conflict-trends.md")
    return report
```

**人工 PR 触发**：cross_school_scan 不自动调权重，只生成报告。架构师人工 review 后开 PR 修 `dimension-weights.yaml`。

---

## 十二、可观测性

`tools/lifecycle_dashboard.py`（不强制 W2 交付，可后期）输出实时面板：

```
=== mangpai-fusion v1.2 · Rule Lifecycle Dashboard ===
案例总数: 15  |  最近一案: C-2026-014 (2026-05-23)

按状态分布：
  proposed:           24 (13%)
  candidate:          51 (28%)
  confirmed:          92 (51%)
  flagged_for_review: 11 (6%)
  deprecated:          5 (2%)
  ─────────────────────────
  total: 183 active rules

近 7 天变更：
  ↑ 4 condid → confirmed
  ↑ 8 proposed → candidate  
  ↓ 1 confirmed → flagged (M2-Y-073, 婚凶五凶煞)
  ✗ 0 deprecated

漂移监控：
  M2-Y-073 婚凶五凶煞: recent_5=[F,T,F,F,F], hit_rate=20% → flagged
  ...
```

---

## 十三、版本演进

| 版本 | 变更 |
|---|---|
| 1.2.0 | 初版 5 状态自动机 + Beta + 3 次降级 + drift detect |
| 1.3.0 | feedback_loop 重构出 `_apply_rule_verdicts` 共用核心；新增 v1.3 D5 结构化反馈入口（feedback_ingest）；增加 D7 应期延迟反馈（半年外 hit=0.5）独立隔离 |
| **1.3.0-current** | **v1.4 W1 增字段：`quantifiable: bool`（V1）+ `domain_restriction: list[str]`（V2）；ingest 跳过策略 V3 落地（见 § 六·1）。修复 D8 误降级（M3-R-003 框架性心法 / M3-R-031 域错位）** |

---

**契约结束。下一份请阅读 `06-confidence-model.md`（W1.3 第 3 份）。**
