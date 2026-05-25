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



---

## 七、CFL-C015 系列仲裁记录（2026-05-25 · 来自 C-2026-015 反馈）

### CFL-C015-001 · 段派做功层数封顶律 vs 杨派理论上限律

```yaml
- cfl_id: CFL-C015-001
  case_id: C-2026-015-甲寅乙亥丙辰辛卯
  date: 2026-05-25
  category: rule_arbitration            # 规则仲裁（非工程问题）
  severity: major                       # 重大 — 影响段派核心做功律
  conflicting_rules:
    - rule_id: M1-D-173
      school: duan
      claim: "做功 2 层 → 兑现 L9-L11（大富级 / 事业二等中等）"
    - rule_id: M2-Y-042
      school: yang
      claim: "化杀生枭 = 官命第 1 取 → 理论顶配 L13-L15（事业一等）"
  conflict_essence: |
    本案命主在纯体制内路径已升至 L12 正厅级，超过段派做功 2 层封顶 L11，
    但低于杨派化杀生枭理论上限 L13。两派映射律对兑现层级的预测不一致。

  resolution:
    direction: yang_party_amplified_with_duan_exception
    new_rule: EXC-D-LIFA-CAP-001        # 体制路径做功层数 +1 档例外条款
    new_rule_status: candidate
    detail: |
      杨派理论上限律权重提升（M2-Y-042 ★4 75% → ★4 82%）；
      段派做功层数封顶律保留作为民营/体制外案例的默认兑现律（M1-D-173 不变），
      但新增体制路径例外条款 EXC-D-LIFA-CAP-001：
      纯体制路径 + 化杀生枭/官印相生 + 驿马 ≥ 2 验证 → 兑现层级 +1 档。

  evidence_chain:
    - C-2026-015 反馈：1996 选优入省厅 → 2025.02 正厅 L12（30 年纯体制路径）
    - 4 次跨地市/跨部门调动验证驿马铁律
    - 化杀生枭 + 官印相生结构齐备（CON-GEJU-001/002）
    - 做功 2 层（按 M1-D-173 默认）+ 实际 L12 → 偏差 +1 档

  feedback_status: confirmed
  feedback_evidence: cases/C-2026-015-甲寅乙亥丙辰辛卯/feedback.md § 五 CFL-C015-001
  outcome:
    correct: true                       # 仲裁方向正确（候选规则首例命中）
    notes: |
      候选规则 EXC-D-LIFA-CAP-001 起始 ★3 (65%)。
      升 confirmed 需再有 1 例正厅及以上体制内命主复现"做功 2 层 → L12"映射。

  workflow_artifacts:
    - mapping/exclusive.md § 2.6 EXC-D-LIFA-CAP-001
    - engine/level-scales.md § 七（规则映射表新增行）
    - engine/level-scales.md § 九·四（完整触发逻辑伪代码）
```

### CFL-C015-002 · 跨维度输出耦合性 gate

```yaml
- cfl_id: CFL-C015-002
  case_id: C-2026-015-甲寅乙亥丙辰辛卯
  date: 2026-05-25
  category: engine_engineering          # ⚠️ 工程改进（非规则纠偏）
  severity: medium
  problem_essence: |
    报告同时输出 "公门首选 90%"（互补 4.1）+ "中富下 L9 85%"（互补 4.2）。
    二者隐含矛盾——体制内薪酬走公务员体系，与市场财富 7 等不直接映射。
    当前两条独立轨道并行输出，命主无从判断哪个该信。

  important_clarification: |
    1. 这不是"市场财富分级规则错"——本案命主从未走过非体制路径，规则本身没被证伪
    2. 这不是"维度错配命中失败"——立案时 known_facts 全空，引擎按 fallback 输出市场财富分级是合理的默认
    3. 这是"引擎输出层耦合 gate 缺失"——当其他维度已强暗示某条路径时，本维度应做条件输出而非独立输出

  resolution:
    direction: add_cross_domain_consistency_check
    detail: |
      在 tools/output_linter.py 新增 _lint_cross_domain_coupling 函数，
      扫描报告同时出现"高置信体制内信号 + 高置信市场财富分级 + 无耦合标注" → 触发 W9 警告。

      在 engine/level-scales.md § 十一 落定输出框架分流规则：
        P(体制内) > 0.7  → 主输出权力层级 + 公务员薪酬区间
        0.3 ≤ P ≤ 0.7    → 双框架并列
        P(体制内) < 0.3  → 默认市场财富 7 等

  feedback_status: confirmed
  feedback_evidence: cases/C-2026-015-甲寅乙亥丙辰辛卯/feedback.md § 五 CFL-C015-002
  outcome:
    correct: true
    notes: |
      工程改进已落地 v1.3 引擎（output_linter W9 检查）。
      v1.4 完整实现需补：
        - engine/contracts/03-findings-schema.md 新增 industry_path + wealth_level.framework 字段
        - templates/report.md 新增 § 八·零 行业路径耦合提示
        - 历史报告回溯扫描

  workflow_artifacts:
    - tools/output_linter.py（新增 _lint_cross_domain_coupling + W9 严重等级）
    - engine/level-scales.md § 十一（完整规范 + 实操检查清单）
```

### CFL-C015-003 · 应期"事件类型"vs"时间窗"分流

```yaml
- cfl_id: CFL-C015-003
  case_id: C-2026-015-甲寅乙亥丙辰辛卯
  date: 2026-05-25
  category: engine_engineering          # 工程改进 — 应期模型升级
  severity: medium
  problem_essence: |
    2010 庚寅应期"财源/置业"在时间上完美命中（命主 2010.12 升副处级），
    但实际事件类型是"职级升迁"而非"财源/置业"。
    当前应期模型把"庚透财"绑死为单一事件类型，未考虑体制内案例的解读差异。

  resolution:
    direction: split_event_type_from_time_window
    detail: |
      应期判定应分两层独立评估：
        time_window：流年 / 流月 / 流日触发的时间窗（保持现有铁律）
        event_type：事件类型候选列表（在体制内案例中扩展为"职级升迁/财源/置业"多解）

      v1.4 实现：
        engine/yingqi/threelayer.py 新增 event_type_hypotheses: list[str] 字段
        体制内案例的"财星显象"应期 → 输出多个候选事件类型而非单一类型

  feedback_status: pending                # 暂未落规则文件，等 v1.4 应期模型升级时一并处理
  feedback_evidence: cases/C-2026-015-甲寅乙亥丙辰辛卯/feedback.md § 五 CFL-C015-003
  outcome:
    correct: null                         # 待 v1.4 实施验证
    notes: |
      建议性仲裁。已在 META/rule-changelog.md 标记 v1.4 backlog。
      不立即落代码，避免污染 v1.3 应期模型。

  workflow_artifacts:
    - cases/C-2026-015-甲寅乙亥丙辰辛卯/feedback.md § 五 CFL-C015-003
    - 待 v1.4：engine/yingqi/threelayer.py
```

---

## 八、本批次仲裁统计

| CFL ID | 类别 | 严重度 | 状态 | 落代码 |
|---|---|---|---|---|
| CFL-C015-001 | rule_arbitration | major | confirmed | ✅ EXC-D-LIFA-CAP-001 候选 |
| CFL-C015-002 | engine_engineering | medium | confirmed | ✅ output_linter W9 |
| CFL-C015-003 | engine_engineering | medium | pending | ⏳ v1.4 backlog |
