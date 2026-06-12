# P2-3 Production Governance Design Audit

审计性质：只读治理设计。本报告根据既有 P1/P2 审计结果设计未来 100 案例校准所需治理契约；不修改 `theory/*`、`engine/*`、`tests/*`、权重或 Schema，不创建新规则，不自动修复。

## 1. 输入事实源

- `META/rule-family-audit-final.md`
- `META/rule-type-audit.md`
- `META/rule-source-audit.md`
- `META/ziping-coverage-report.md`
- `META/duplicate-vote-leaderboard.md`
- `META/theory-validation-sprint-01.md`

## 2. 关键事实摘要

| 指标 | 数值 |
|---|---:|
| 生产规则总数 | 312 |
| 子平规则数 | 57 |
| 滴天髓规则数 | 255 |
| P2-1 总触发次数 | 8811 |
| P2-1 重复投票压缩率 | 94.5% |
| DTS raw votes | 7163 |
| ZIPING raw votes | 1648 |
| Raw 压制倍数 DTS/ZIPING | 4.35x |
| Dedup 压制倍数 DTS/ZIPING | 5.67x |
| 子平章节覆盖率 | 14.5% |
| rule_type=GENERAL_PRINCIPLE 规则数 | 55 |
| rule_type=STRUCTURE 规则数 | 147 |
| rule_type=EVENT 规则数 | 73 |
| rule_type=TIMING 规则数 | 19 |
| rule_type=ANTI_PATTERN 规则数 | 18 |

## 3. Family Cap 设计

治理口径：Family Cap 是校准统计层契约，不等于修改规则权重；同一 case 内同一 family 的多条命中规则先压缩为 family vote，再进入 school vote 与最终学习口径。

| risk | 建议 cap | family | 原因 |
|---|---:|---|---|
| CRITICAL | 1 | FAM-004(调候 / 寒暖 / 燥湿 / 季令气候)、FAM-011(从格 / 从象 / 从势 / 从旺 / 从强 / 从财杀儿) | 同源理论拆分最严重；P2-2 显示 FAM-004 最高 23票→1票，若不 cap 会直接污染主票。 |
| HIGH | 2 | FAM-001(用神 / 取用 / 喜忌 / 成败救应)、FAM-002(扶抑 / 旺衰 / 身强身弱 / 太过不及)、FAM-003(中和 / 偏枯 / 有病有药 / 补偏却余)、FAM-005(顺逆 / 顺势 / 流通 / 通关 / 源流)、FAM-006(合冲刑害 / 冲动 / 冲开 / 发用)、FAM-007(格局成败 / 层级 / 纯杂 / 有情 / 护卫)、FAM-008(清浊 / 清气 / 清枯 / 澄浊求清)、FAM-012(化格 / 合化 / 真化 / 假化 / 合而不化)、FAM-013(月令 / 时令 / 旺相休囚 / 四时进退)、FAM-018(金木震兑 / 水火坎离 / 对待制化调济) | 高频结构/总纲 family 在 30 案例中普遍 100% 触发，建议最多保留 2 张主/辅混合票以保留细分差异。 |
| MEDIUM | 3 | FAM-009(财官承载 / 财官相生 / 财官取用)、FAM-010(官杀 / 伤官 / 制化 / 杀印相生)、FAM-014(六亲 / 婚姻 / 子息 / 家庭落点)、FAM-015(运岁 / 动态成败 / 触发转化)、FAM-016(性情 / 行为风格 / 中和偏枯外化)、FAM-017(健康 / 寿元 / 元神 / 体用风险)、FAM-019(真假神 / 假神得局 / 真神失势)、FAM-020(透藏 / 隐显 / 根气 / 得地) | 仍有重复风险，但更多属于事件落点或解释细分；允许最多 3 票用于保留不同域的可解释性。 |

### 3.1 Family Cap 明细

| family_id | family_name | source_risk | audit_raw_votes | audit_dedup_votes | compression_ratio | 建议 cap |
|---|---|---|---:|---:|---:|---:|
| FAM-001 | 用神 / 取用 / 喜忌 / 成败救应 | HIGH | 490 | 30 | 93.9% | 2 |
| FAM-002 | 扶抑 / 旺衰 / 身强身弱 / 太过不及 | HIGH | 351 | 30 | 91.5% | 2 |
| FAM-003 | 中和 / 偏枯 / 有病有药 / 补偏却余 | HIGH | 270 | 30 | 88.9% | 2 |
| FAM-004 | 调候 / 寒暖 / 燥湿 / 季令气候 | CRITICAL | 671 | 30 | 95.5% | 1 |
| FAM-005 | 顺逆 / 顺势 / 流通 / 通关 / 源流 | HIGH | 411 | 30 | 92.7% | 2 |
| FAM-006 | 合冲刑害 / 冲动 / 冲开 / 发用 | HIGH | 305 | 30 | 90.2% | 2 |
| FAM-007 | 格局成败 / 层级 / 纯杂 / 有情 / 护卫 | HIGH | 341 | 30 | 91.2% | 2 |
| FAM-008 | 清浊 / 清气 / 清枯 / 澄浊求清 | HIGH | 220 | 30 | 86.4% | 2 |
| FAM-009 | 财官承载 / 财官相生 / 财官取用 | MEDIUM | 324 | 30 | 90.7% | 3 |
| FAM-010 | 官杀 / 伤官 / 制化 / 杀印相生 | MEDIUM | 278 | 30 | 89.2% | 3 |
| FAM-011 | 从格 / 从象 / 从势 / 从旺 / 从强 / 从财杀儿 | CRITICAL | 396 | 30 | 92.4% | 1 |
| FAM-012 | 化格 / 合化 / 真化 / 假化 / 合而不化 | HIGH | 321 | 30 | 90.7% | 2 |
| FAM-013 | 月令 / 时令 / 旺相休囚 / 四时进退 | HIGH | 360 | 30 | 91.7% | 2 |
| FAM-014 | 六亲 / 婚姻 / 子息 / 家庭落点 | MEDIUM | 191 | 30 | 84.3% | 3 |
| FAM-015 | 运岁 / 动态成败 / 触发转化 | MEDIUM | 190 | 30 | 84.2% | 3 |
| FAM-016 | 性情 / 行为风格 / 中和偏枯外化 | MEDIUM | 131 | 30 | 77.1% | 3 |
| FAM-017 | 健康 / 寿元 / 元神 / 体用风险 | MEDIUM | 112 | 30 | 73.2% | 3 |
| FAM-018 | 金木震兑 / 水火坎离 / 对待制化调济 | HIGH | 360 | 30 | 91.7% | 2 |
| FAM-019 | 真假神 / 假神得局 / 真神失势 | MEDIUM | 209 | 30 | 85.6% | 3 |
| FAM-020 | 透藏 / 隐显 / 根气 / 得地 | MEDIUM | 239 | 30 | 87.4% | 3 |

## 4. Rule Type 投票策略

| rule_type | 参与主票 | 参与辅助票 | 参与解释层 | 参与动态权重学习 | 策略说明 |
|---|---|---|---|---|---|
| GENERAL_PRINCIPLE | 否 | 是 | 是 | 有限 | 总纲类规则多为上游背景，不应直接加主票；可作为 shared evidence 与解释框架，动态学习只学习其辅助增益。 |
| STRUCTURE | 有条件 | 是 | 是 | 是，但必须 family-capped | 结构规则可形成主判断，但重复率最高；必须先做 family cap，再参与权重学习。 |
| EVENT | 是 | 是 | 是 | 是 | 事件规则直接对应事业、财富、健康、婚姻等落点，是主票核心，但同 family 内仍需 cap。 |
| TIMING | 有条件 | 是 | 是 | 是，按应期准确率单独学习 | 应期规则应作为时间触发票，不与结构主票混加；需按年份/大运/流年命中单独校准。 |
| ANTI_PATTERN | 否 | 是 | 是 | 有限 | 反机械/禁用孤证类规则不应正向加主票，应作为 veto、降权或风险提示证据。 |

## 5. Shared Evidence 模型

模型定义：Shared Evidence Key 是 family 内或跨 family 的共享特征，不直接等于独立投票。命中 shared evidence 时，先生成 evidence feature，再由 family vote 消化，避免同一证据被多条规则重复计票。

| rank | evidence_key | 关联family | 关联rule数估计 | 说明 |
|---:|---|---|---:|---|
| 1 | 月令 | FAM-001, FAM-002, FAM-004, FAM-013, FAM-018, FAM-020 | 134 | 归一化汇总 key |
| 2 | 旺衰 | FAM-002, FAM-003, FAM-013 | 74 | 归一化汇总 key |
| 3 | 调候 | FAM-004, FAM-017 | 125 | 归一化汇总 key |
| 4 | 坎离升降 | FAM-004, FAM-018 | 36 | 原始 shared evidence key |
| 5 | 有情无情 | FAM-001, FAM-007 | 29 | 原始 shared evidence key |
| 6 | 旺相休囚 | FAM-002, FAM-013 | 25 | 原始 shared evidence key |
| 7 | 从格条件 | FAM-011 | 98 | 归一化汇总 key |
| 8 | 通关条件 | FAM-005 | 45 | 归一化汇总 key |
| 9 | 震兑调济 | FAM-004 | 24 | 原始 shared evidence key |
| 10 | 燥湿状态 | FAM-004 | 24 | 原始 shared evidence key |
| 11 | 火暖需求 | FAM-004 | 24 | 原始 shared evidence key |
| 12 | 水润需求 | FAM-004 | 24 | 原始 shared evidence key |
| 13 | 月令季节 | FAM-004 | 24 | 原始 shared evidence key |
| 14 | 寒暖状态 | FAM-004 | 24 | 原始 shared evidence key |
| 15 | 土燥土湿 | FAM-004 | 24 | 原始 shared evidence key |
| 16 | 十干调候用神 | FAM-004 | 24 | 原始 shared evidence key |
| 17 | 跨类别取用 | FAM-001 | 17 | 原始 shared evidence key |
| 18 | 相神护卫 | FAM-001 | 17 | 原始 shared evidence key |
| 19 | 喜忌取裁 | FAM-001 | 17 | 原始 shared evidence key |
| 20 | yongshen来源_月令透藏 | FAM-001 | 17 | 原始 shared evidence key |

## 6. DTS vs ZIPING 平衡机制

### 6.1 三级统计模型

| 层级 | 定义 | 用途 | 防压制机制 |
|---|---|---|---|
| raw vote | 每条 triggered rule 计 1 票 | 保留原始触发体量与规则活跃度 | 只作为诊断，不直接进入最终校准权重 |
| family vote | 同一 case × family 内按 cap 压缩 | 主校准口径，消解同源规则拆分 | CRITICAL cap=1，HIGH cap=2，MEDIUM cap=3 |
| school vote | 同一 case × school 内对 family vote 再归一化 | 比较 DTS 与 ZIPING 体系贡献 | 每派先归一到 0-1 或固定上限，再进入融合层 |

### 6.2 防止 255 条 DTS 压制 57 条 ZIPING

1. raw vote 不进入最终权重，只作为规则库活跃度监控。
2. family vote 是 100 案例主统计口径，先消除一理论拆成 N 规则的问题。
3. school vote 对每派 family vote 做派别内归一化，避免 DTS 因规则数量 255:57 获得天然票数优势。
4. 输出必须同时展示 raw / family / school 三轨，若三轨结论不一致，进入人工仲裁而非自动调权。
5. ZIPING 的章节覆盖率仅 14.5%，不得用低覆盖导致的低 raw vote 反向削弱子平体系权重。

## 7. 100案例准入门槛

### 7.1 必须完成

- 冻结 family cap 统计口径：CRITICAL=1、HIGH=2、MEDIUM=3。
- 在 100 案例统计中同时输出 raw vote、family vote、school vote。
- 把 duplicate-vote Top50 规则标记为 family cap 观察对象。
- 把 STRUCTURE / GENERAL_PRINCIPLE / ANTI_PATTERN 高重复规则纳入 shared evidence 观察口径。
- 补齐 UNMAPPED 或跨多 family 规则的治理解释，避免绕过 cap。

### 7.2 建议完成

- 对 FAM-004、FAM-001、FAM-005、FAM-011 做人工抽检，确认 cap 后解释不丢失。
- 为 TIMING 规则建立独立应期准确率表，不与结构票混合学习。
- 对子平未覆盖章节建立 source trace backlog，避免 coverage 缺口影响派别评价。
- 为 DTS 与 ZIPING 建立派别内归一化 dashboard。

### 7.3 可延期

- 正式把 cap 字段写入 Schema。当前阶段只需统计契约，不改 Schema。
- 自动修复或拆并生产规则。当前阶段禁止自动修复。
- 细化每个 shared evidence key 的机器字段名。可在 100 案例后根据稳定性再定。

## 8. 最终结论：是否允许进入 Phase-100 Calibration

结论：YES-WITH-GUARDRAILS

依据：

- 允许进入：P2-1 已完成 30 案例触发统计，P2-2 已量化重复投票、DTS/ZIPING 压制与 N票→1票放大链路，具备扩大样本的最低观测条件。
- 必须带护栏：重复投票压缩率高达 94.5%，FAM-004 最高 23票→1票，若不先执行 family cap，100 案例权重学习会被重复证据污染。
- 不允许裸奔校准：DTS raw votes 为 7163，ZIPING raw votes 为 1648，DTS/ZIPING raw 压制倍数为 4.35x；若不做 school vote 归一化，会把规则库规模误当作理论有效性。
- 子平章节覆盖率仍为 14.5%，100 案例阶段只能校准现有 production coverage，不能据此否定未抽取章节的理论价值。

## 9. 机器可读摘要

```json
{
  "decision": "YES-WITH-GUARDRAILS",
  "family_cap": {
    "CRITICAL": 1,
    "HIGH": 2,
    "MEDIUM": 3
  },
  "rule_type_strategy": {
    "GENERAL_PRINCIPLE": {
      "main_vote": "否",
      "aux_vote": "是",
      "explanation": "是",
      "dynamic_learning": "有限"
    },
    "STRUCTURE": {
      "main_vote": "有条件",
      "aux_vote": "是",
      "explanation": "是",
      "dynamic_learning": "是，但必须 family-capped"
    },
    "EVENT": {
      "main_vote": "是",
      "aux_vote": "是",
      "explanation": "是",
      "dynamic_learning": "是"
    },
    "TIMING": {
      "main_vote": "有条件",
      "aux_vote": "是",
      "explanation": "是",
      "dynamic_learning": "是，按应期准确率单独学习"
    },
    "ANTI_PATTERN": {
      "main_vote": "否",
      "aux_vote": "是",
      "explanation": "是",
      "dynamic_learning": "有限"
    }
  },
  "top_shared_evidence": [
    {
      "evidence_key": "月令",
      "families": [
        "FAM-001",
        "FAM-002",
        "FAM-004",
        "FAM-013",
        "FAM-018",
        "FAM-020"
      ],
      "rule_count": 134
    },
    {
      "evidence_key": "旺衰",
      "families": [
        "FAM-002",
        "FAM-003",
        "FAM-013"
      ],
      "rule_count": 74
    },
    {
      "evidence_key": "调候",
      "families": [
        "FAM-004",
        "FAM-017"
      ],
      "rule_count": 125
    },
    {
      "evidence_key": "坎离升降",
      "families": [
        "FAM-004",
        "FAM-018"
      ],
      "rule_count": 36
    },
    {
      "evidence_key": "有情无情",
      "families": [
        "FAM-001",
        "FAM-007"
      ],
      "rule_count": 29
    },
    {
      "evidence_key": "旺相休囚",
      "families": [
        "FAM-002",
        "FAM-013"
      ],
      "rule_count": 25
    },
    {
      "evidence_key": "从格条件",
      "families": [
        "FAM-011"
      ],
      "rule_count": 98
    },
    {
      "evidence_key": "通关条件",
      "families": [
        "FAM-005"
      ],
      "rule_count": 45
    },
    {
      "evidence_key": "震兑调济",
      "families": [
        "FAM-004"
      ],
      "rule_count": 24
    },
    {
      "evidence_key": "燥湿状态",
      "families": [
        "FAM-004"
      ],
      "rule_count": 24
    },
    {
      "evidence_key": "火暖需求",
      "families": [
        "FAM-004"
      ],
      "rule_count": 24
    },
    {
      "evidence_key": "水润需求",
      "families": [
        "FAM-004"
      ],
      "rule_count": 24
    },
    {
      "evidence_key": "月令季节",
      "families": [
        "FAM-004"
      ],
      "rule_count": 24
    },
    {
      "evidence_key": "寒暖状态",
      "families": [
        "FAM-004"
      ],
      "rule_count": 24
    },
    {
      "evidence_key": "土燥土湿",
      "families": [
        "FAM-004"
      ],
      "rule_count": 24
    },
    {
      "evidence_key": "十干调候用神",
      "families": [
        "FAM-004"
      ],
      "rule_count": 24
    },
    {
      "evidence_key": "跨类别取用",
      "families": [
        "FAM-001"
      ],
      "rule_count": 17
    },
    {
      "evidence_key": "相神护卫",
      "families": [
        "FAM-001"
      ],
      "rule_count": 17
    },
    {
      "evidence_key": "喜忌取裁",
      "families": [
        "FAM-001"
      ],
      "rule_count": 17
    },
    {
      "evidence_key": "yongshen来源_月令透藏",
      "families": [
        "FAM-001"
      ],
      "rule_count": 17
    }
  ],
  "three_tier_vote_model": [
    "raw vote",
    "family vote",
    "school vote"
  ],
  "must_complete_before_100": [
    "冻结 family cap 统计口径：CRITICAL=1、HIGH=2、MEDIUM=3。",
    "在 100 案例统计中同时输出 raw vote、family vote、school vote。",
    "把 duplicate-vote Top50 规则标记为 family cap 观察对象。",
    "把 STRUCTURE / GENERAL_PRINCIPLE / ANTI_PATTERN 高重复规则纳入 shared evidence 观察口径。",
    "补齐 UNMAPPED 或跨多 family 规则的治理解释，避免绕过 cap。"
  ]
}
```
