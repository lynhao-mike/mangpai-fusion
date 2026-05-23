# 仲裁日志 · arbitration-log.md

> 每次派别冲突仲裁的完整记录。用于回溯仲裁正确性 + 调整 CF 规则。

最后更新：2026-05-23  
版本：v1.0

---

## 一、记录格式

```yaml
- entry_id: ARB-YYYY-NNN
  date: YYYY-MM-DD
  case_id: C-YYYY-NNN
  conflict_id: CFL-{topic}-NNN
  cf_rule: CF-{topic}-NN
  
  domain: hunyin
  domain_lead: yang
  
  positions:
    - school: yang
      rule: M2-Y-XXX
      stance: 不破婚
      static_score: 85
      domain_weight: 1.0
    - school: gao
      rule: G-LF-XXX
      stance: 婚姻多变
      static_score: 78
      domain_weight: 0.4
  
  resolution:
    winner: yang
    winner_score: 61.6
    loser_score: 46.8
    output: |
      [杨派主导] 不破婚 ★★★ (62%)
      [高派持反对] 婚姻多变 ★ (47%)
  
  feedback_status: pending      # pending | confirmed | overturned
  feedback_evidence: ""         # 命主反馈应验细节
  outcome:                       # 仲裁是否正确
    correct: null                # null | true | false
    notes: ""
```

---

## 二、仲裁记录

> 暂无记录（等待第 1 案）

---

## 三、CF 规则调整建议

> 当某 CF 规则在 ≥ 3 个案例中被反馈"仲裁错误" → 触发 review。

| CF ID | 触发反对次数 | 当前规则 | 建议调整 | 备注 |
|---|---|---|---|---|
| _(暂无)_ | - | - | - | - |

---

## 四、领域权重调整建议

> 当某派在某领域累计失验 ≥ 5 例 → 触发 domain_weights 降级。

| 派别 | 领域 | 失验次数 | 当前 weight | 建议 weight |
|---|---|---|---|---|
| _(暂无)_ | - | - | - | - |

---

## 五、统计

| 指标 | 数值 |
|---|---|
| 总仲裁次数 | 0 |
| 仲裁正确次数 | 0 |
| 仲裁错误次数 | 0 |
| 仲裁正确率 | - |

---

## 六、维护规则

1. 每次主分析器遇到冲突 → 自动追加一条记录到本文件
2. 命主反馈应验后 → 回填 `feedback_status` + `outcome`
3. 月度 review：统计仲裁正确率，调整 `engine/arbitration.md` 中的 CF 规则
