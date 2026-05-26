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



---

## 九、Flagged-for-Review 规律批量审查（2026-05-26 · 架构师 Review）

> 触发来源：v1.3 历史回补（10 案）+ C-2026-015 反馈摄入 → 累计 7 条规律降级至 flagged_for_review。
> 审查目标：逐条决定保留观察 / 收紧条件 / 退役。

---

### REV-001 · M3-R-005 · 富贵八字两要素（任派）

| 项目 | 值 |
|---|---|
| 当前状态 | **deprecated**（已由自动降级从 flagged → deprecated） |
| 统计 | 0 hit / 4 miss / posterior=0.17 |
| 失验案 | C-001, C-002, C-014, C-015 |
| 规律内容 | "要素 ① 有势力有党 + 要素 ② 做功有效 → 富贵命" |

**审查结论：✅ 维持 deprecated（确认退役）**

**理由**：
- 4 案全 miss，posterior=0.17，远低于 candidate 门槛 0.40
- 该规律要求"势+功"双具备才定义为"富贵命"，标准过严——C-001 路桥正科 L3 算中产（该规律预判为"打七折"偏低估）、C-015 正厅 L12 也被判为"做功不够"
- 实质问题：这是一条**过于理想化的总纲式规律**，现实案例中几乎不存在"势+功"完美配合的八字
- 替代方案：M1-D-122（段派势/党三档）+ M1-D-014（复合做功）+ EXC-D-LIFA-CAP-001（体制路径例外条款）三者联合已覆盖本规律的功能

**动作**：无需操作（系统已自动完成 deprecated）

---

### REV-002 · M2-Y-091 · 承载财官本质论（杨派）

| 项目 | 值 |
|---|---|
| 当前状态 | flagged_for_review |
| 统计 | 0 hit / 3 miss / posterior=0.20 |
| 失验案 | C-001（婚姻域）, C-002（婚姻域）, C-014（承载/做功域） |
| 规律内容 | "真正福=禄；真正财官=印和禄(非字面财官)；用哪字取财官该字必须旺" |

**审查结论：⬇️ 退役（deprecated）**

**理由**：
- 3 案全 miss，0 hit，posterior=0.20
- 规律本身过度抽象（"真正福=禄"），在具体预测中缺乏可操作的判定边界
- C-001/C-002 中被用于婚姻域判断"承载有余/旺极无依"，实际婚姻均稳定→方向性错误
- C-014 中被用于"承载本质"学业判断，未能贡献准确预测
- 这属于**哲学层面的心法**而非可验证的预测规律，不应进入引擎的量化判定流程

**动作**：降级为 deprecated

---

### REV-003 · M3-R-031 · 六合婚姻应期（任派）

| 项目 | 值 |
|---|---|
| 当前状态 | flagged_for_review |
| 统计 | 5 hit / 3 miss / posterior=0.60 |
| 失验案 | C-001（婚姻）, C-002（婚姻）, C-014（学业域误用） |
| 命中案 | C-008, C-009, C-010, C-011, C-015（应期域） |
| 规律内容 | "六合婚姻应期"（6 触发应期：流年合化/冲/伏吟/破刑/原局动/藏干透出） |

**审查结论：⬆️ 恢复 confirmed + 收紧适用域**

**理由**：
- **5/8=62.5% 命中率**，posterior=0.60，recent_5=[T,T,T,F,T]——近期 4/5 命中
- 3 次 miss 全在**婚姻应期域**（C-001/002 预测晚婚但实际早婚）和**学业域误用**（C-014）
- 在**应期触发域**本身（哪一年发生事件）命中率极高：C-008/009/010/011/015 全部铁命中
- 问题不在规律本身，而在于**被错误引用到婚期预测**——"六合=应期触发"≠"六合年=结婚年"
- C-015 中 M3-R-031 对应"2004 寅申冲发升职"铁命中（年-月级精度）

**收紧条件**：
- 该规律仅适用于**应期触发域**（判断某年是否有重大事件触发）
- **不得**单独用于婚期预测——婚期须走联检路径（MR-005 坤造三项联检 / 画像窗口 + 三层 gate）
- 在 analysis.md 中引用 M3-R-031 时必须标注具体触发类型，禁止笼统标注"婚姻"

**动作**：恢复 confirmed，在 theory/ren/index.yaml 对应条目添加 `domain_restriction: ["应期"]` 注释

---

### REV-004 · M1-D-122 · 富贵贫贱三档判定 — 势+功/有功无势/无功（段派）

| 项目 | 值 |
|---|---|
| 当前状态 | flagged_for_review |
| 统计 | 1 hit / 3 miss / posterior=0.33 |
| 命中案 | C-001（L2-L3 正确） |
| 失验案 | C-002（坤造靠家庭资源）, C-014（学业域）, C-015（体制内正厅低估） |
| 规律内容 | "富贵贫贱三档判定：势+功→富贵 / 有功无势→小康 / 无功→普通" |

**审查结论：🟡 保留观察 + 新增适用域限制**

**理由**：
- C-001 准确命中（L2-L3 正确），说明规律在**乾造 + 非体制路径**下有效
- 3 次 miss 均有**系统性偏差场景**：
  - C-002：坤造（女命财富路径靠配偶/父亲家庭资源，非本人做功）
  - C-015：纯体制路径（做功 2 层但正厅 L12，已由 CFL-C015-001 新增例外条款覆盖）
  - C-014：18 岁少年案（学业域误用，该规律本为富贵层级定性，非学业预测）
- 规律本身在原定适用场景（乾造+非体制+成年案）仍有效
- 样本量不足（仅 4 案）下判退役过于激进

**收紧条件**：
- 明确适用约束：乾造优先 / 坤造需额外评估配偶资源路径
- 体制内路径需叠加 EXC-D-LIFA-CAP-001 例外条款
- 学业域不引用本规律（本规律仅适用于事业/富贵定性）

**动作**：保留 flagged_for_review，待再累积 3+ 案合格样本后重新评估

---

### REV-005 · M3-R-022 · 禄刃不可坏原则（任派）

| 项目 | 值 |
|---|---|
| 当前状态 | flagged_for_review |
| 统计 | 2 hit / 3 miss / posterior=0.43 |
| 命中案 | C-008, C-010 |
| 失验案 | C-001（婚姻域）, C-002（婚姻域）, C-015（不适用） |
| 规律内容 | "禄刃为日主根气所在，被冲/被合/被克 = 重大灾/变动信号" |

**审查结论：🟡 保留观察 + 收紧适用条件**

**理由**：
- C-008/010 命中说明规律在**应期灾变判断**中有效（禄刃被冲 = 重大变动）
- C-001/002 miss 原因：被错误引用到"婚姻凶"判断——禄刃被冲 ≠ 婚姻坎坷
- C-015 miss 原因：analysis.md 明确写"禄刃律不直接适用"（丙日主无午/丁禄），ingest 仍计为 miss 属信号噪音
- 规律本质正确（禄刃被冲确实是重大变动信号），问题在于**引用时的域定位错误**

**收紧条件**：
- 仅适用于**灾变/重大变动**应期判断
- 禁止单独引用为"婚凶"信号（婚姻须走联检路径）
- 命局中无禄无刃时标注"不适用"，不应强行引用

**动作**：保留 flagged_for_review，后续案例正确使用后可自动恢复 confirmed

---

### REV-006 · M3-R-027 · 五合四用法（任派）

| 项目 | 值 |
|---|---|
| 当前状态 | flagged_for_review |
| 统计 | 0 hit / 3 miss / posterior=0.20 |
| 失验案 | C-001（婚姻域）, C-002（婚姻域）, C-015（整体任派域） |
| 规律内容 | "天干五合四种用法：合化/合绊/合制/合留 → 对应不同吉凶走向" |

**审查结论：⬇️ 退役（deprecated）**

**理由**：
- 3 案全 miss，0 hit，posterior=0.20
- C-001/002 中被用于婚姻预测"五合=婚姻走向"→实际婚姻稳定，完全失验
- C-015 中被引用但未产出有效命中（丙辛合化水 → "得妻得财"待回测但未计 hit）
- 该规律表述过于笼统（"五合四种用法"），缺乏明确的**触发条件 → 产出断语**映射
- 与 M3-R-031（6 触发应期）功能重叠但缺乏后者的精确性
- 实质问题：这是**教学层面的方法论总结**，不是可验证的预测规律

**动作**：降级为 deprecated

---

### REV-007 · M3-R-003 · 原局定层次，大运定吉凶，流年定应期（任派）

| 项目 | 值 |
|---|---|
| 当前状态 | flagged_for_review |
| 统计 | 0 hit / 3 miss / posterior=0.20 |
| 失验案 | C-001（婚姻域）, C-002（婚姻域）, C-015（整体任派域） |
| 规律内容 | "原局定层次，大运定吉凶，流年定应期"（核心心法三层叠加） |

**审查结论：🟡 保留观察（不退役）+ 标注为"框架性心法，不参与量化评分"**

**理由**：
- 这是任派的**方法论总纲**（"三层叠加"心法），不是具体可证伪的预测规律
- 3 次 miss 均源于 v1.0 启发式 ingest 的**信号噪音**——启发式解析器把该规律 ID 挂在了婚姻域的具体预测上（"六合年=婚年"等），但 M3-R-003 本身并没有做具体预测
- 该规律指导的是**分析方法论**（先看原局定方向，再看大运定时段，最后看流年定年份），每一层的具体判断由 M3-R-022/027/031 等子规律负责
- 退役框架性心法对理论库完整性有损害

**处置**：
- 不退役，保留 flagged_for_review
- 在 theory/ren/index.yaml 对应条目标注 `quantifiable: false`（框架性心法不参与 hit/miss 计数）
- 后续 ingest 遇到 M3-R-003 时应跳过计分（abstain），仅当有明确的"三层叠加方法论使用错误"场景才计 miss

---

## 十、审查汇总

| 规律 | 派别 | 审查结论 | 动作 |
|---|---|---|---|
| **M3-R-005** | 任 | ✅ 维持 deprecated | 无需操作（已退役） |
| **M2-Y-091** | 杨 | ⬇️ 退役 deprecated | 需执行 |
| **M3-R-031** | 任 | ⬆️ 恢复 confirmed | 需执行 + 域限制 |
| **M1-D-122** | 段 | 🟡 保留观察 flagged | 待累积样本 |
| **M3-R-022** | 任 | 🟡 保留观察 flagged | 待正确使用后恢复 |
| **M3-R-027** | 任 | ⬇️ 退役 deprecated | 需执行 |
| **M3-R-003** | 任 | 🟡 保留观察 flagged | 标注 quantifiable=false |

### 关键发现

1. **婚姻域集体失验**：M2-Y-091 / M3-R-022 / M3-R-027 / M3-R-031 在 C-001/002 婚姻域全 miss → 根因不在单条规律，而在**婚姻应期模型**整体有偏（预测晚婚/多婚实际早婚/稳定）。建议 v1.4 优先强化婚期联检机制（MR-005 + 画像窗口 + 三层 gate）。

2. **框架性心法不应参与量化评分**：M3-R-003 / M3-R-005 等"总纲"级规律被启发式解析器强行计入 hit/miss 导致失真。建议在 theory yaml 中增加 `quantifiable: true/false` 字段，false 的规律 ingest 时自动跳过。

3. **域定位错误放大 miss 计数**：多条规律的 miss 来自被错误引用到不适用的域（婚姻/学业），而非规律本身错误。建议 v1.4 在 ingest 时增加 `domain_restriction` 校验，域不匹配时跳过计分。
