# Goal Document: 第一性原则快车道 v1

## Go / No-Go
- **Judgment**: **Go**
- **Reason**: P1 方向召回已被 41.2% 的预注册测量证实为事实层阻塞；修复点窄（三处）、hold-out 可冻结、3 张真实盘卡片可立即产出。先证明「能分析一张盘」，再谈预测。

## Target Outcome

在 2 周内，系统对一张真实八字能输出**可复核的五元组结构分析卡**，并且事实层能标出正确施力方：

1. **P1**：hold-out 20 例上，方向召回 ≥80%、边召回 ≥90%；<60% 则 kill/降级。
2. **3 份真实盘卡**：每条带宫位/十神/关系边地址 + 原文锚点 + 成败三态；不给年份/概率/事件。
3. **P2**（P1 通过后）：主功盲测，前两条命中 ≥70% 且高出随机基线 30pp，三态一致 ≥70%，事实错误 0。
4. 全程 481 盘 0 错、全量测试不降；不写确定性 analyzer、不补 880 支克边、不跑 golden-20 盲推。

## Goal Definition
- **Type**: product / technical
- **Boundary**:
  - 含：结构断语卡（五元组）、事实层方向修复、hold-out 评测、P2 主功盲测、3 份真实盘卡。
  - 不含：事件年份/吉凶预测、财富/健康/事业标签、应期模型、物理删除旧层、跨派融合结论。
- **Non-goals**:
  - 不写 `engine/analyzer.py`；判断留给 Agent，校验留给机器。
  - 不补 880 条地支克边（原书断语 0/23 需要它）。
  - 不用 golden-20 盲推代替 P1；不再刷 p 值。
- **Deferred work**:
  - 跨派 natal-only 集、事实层完整原语、Kill List 清场、Linter 代码化。
- **Verification rule**:
  - P1 用独立 hold-out 的机械评分；3 张卡用 T-169 §6 判定表；每步跑 `pytest -q` + `verify_baseline`。
- **Evidence source**: hold-out 评分 JSON、卡片文件、`engine.cli` 地址、`pytest`/`verify_baseline` 退出码。
- **Pass criteria**:
  - P1：方向 ≥80%、边 ≥90%；<60% kill；60–80% 只做局部修。
  - 卡片：五元组齐全、地址可回查、无年份/概率/事件、无编造；3 份里 ≥2 份「真分析」。
  - 工程：481/0；全量测试 0 failed。
- **Confidence note**: 41.2% 是 33 条一人标注，±2 条仍 <60%；hold-out 由第二人独立策展，避免同一人既当运动员又当裁判。
- **Judgment owner**: 中枢 + 独立复核人；P2 最终由人类/领域专家盲审。

## Current State
- 主仓 `main` @ `8bb767d2`；独立分支 `rethink/2026-10-29` @ `6a40bcb5`（worktree `..\mangpai-fusion-rethink`）。
- 33 条标注 → 23 可判 / 17 有施力方 / **7 正确 = 41.2%**；edge 82.6%、candidate 73.9%；`facts_blocking`。
- 失败分解：`actor_none` 3 / `no_candidate` 5 / `reversed` 2。
- 事实层：481/0、关系图通过；但合/冲/刑/穿无施力方（范围比文档更宽，合类也空）、藏干无地址、体-体被滤。
- 测试：main 1374/1；worktree 1380/1。
- T-169 五元组卡规格、T-170 golden-20（duan-only，现为 dev 集）、T-171 依赖审计已就绪。

## Priority Rationale
1. **先 P1 后 P2**：方向召回不修，P2 的主功选择会被事实层残缺污染。
2. **先复核/ hold-out 后改代码**：避免用同一批 33 条调规则再在同一批上验收。
3. **3 张卡并行**：让用户尽快看到「当前能力 + 缺口」，不必等 P1 全绿。
4. **不写 analyzer**：过去三次把判断写进代码都失败；这次把判断留给 Agent，机器只做校验。

## Assumptions and Open Decisions
| Item | Status | Impact | Owner / Next step |
|---|---|---|---|
| hold-out 能凑 20 例非名人段派命例 | assumed | 不足 15 例则停在解释工作台 | T-175 策展；不足如实报 |
| 33 条第二人复核后仍 <60% | assumed | 结论方向不变；若翻到 ≥60%，P1 线需重议 | T-174 复核 |
| 三处修复足以把方向拉到 ≥60% | assumed | 若 <60% 直接 kill；60–80 只做局部修 | 独立 Agent 分支；P1 评分 |
| 名人盘污染 P2 | confirmed（≥4 例） | P2 必须剔除名人盘 | T-175/P2 策展 |
| 预测暂不可检验 | confirmed | 产品只承诺结构分析 | 人类签字 |

## Progress Management
- **Update rule**: 每个 todo 的 proof 通过才勾；phase 的 exit proof 通过才勾 phase。
- **Reprioritization rule**: 若 hold-out 不足或复核翻转，先记录再改顺序；不静默换目标。
- **Phase checklist**:
  - [ ] Phase 1: 并行证据（第二复核 / hold-out / 3 张卡）
  - [ ] Phase 2: P1 三处修复（分支）
  - [ ] Phase 3: P1 hold-out 评分（kill/pass）
  - [ ] Phase 4: P2 主功盲测（仅 P1 通过）
  - [ ] Phase 5: 交付 3 份卡 + 报告 + 基线/交接书

## Phases

### Phase 1: 并行证据（0–2 天）
- **Purpose**: 在改代码前把尺子、hold-out、当前能力三件事同时推进。
- **Entry condition**: 独立 Agent 的 33 条标注与 41.2% 已确认。
- **Phase rules**:
  - 只读/只写新文件；不改 `engine/**`、不合并分支、不动 main 工作区。
  - 第二复核与 hold-out 策展必须是**不同 Agent**；hold-out 不见 33 条标注。
  - 3 张卡标 `pre-P1`，只展示当前能力与缺口。
- **Todos**:
  - [ ] T-174 第二人复核 33 条 → `META/p1-second-review-v1.*`
    - **Proof**: 33 条逐条复核、重算 7/17、分歧清单。
  - [ ] T-175 独立策展 20 例 hold-out → `META/p1-holdout-v1.*`
    - **Proof**: 20 例、非名人、非 dev、四类、原文锚点、盲测/答案分离。
  - [ ] T-176 3 张真实盘五元组卡 → `docs/demo/single-chart-cards-v1.md`
    - **Proof**: 3 卡、地址/边可回查、无年份/概率/事件。
- **Exit proof**: 复核/ hold-out 文件通过中枢检查并冻结哈希；3 张卡可读。
- **Stop condition**: hold-out 不足 15 例，或复核把 41.2% 翻到 ≥60%。

### Phase 2: P1 三处修复（2–4 天）
- **Purpose**: 只修「事实层表达不出谁对谁」的三处，不动排盘。
- **Entry condition**: hold-out 冻结；第二复核完成。
- **Phase rules**:
  - 只在 `rethink/2026-10-29` 分支/worktree；不 push main。
  - 方向规则必须带 `source_ref`；原文没明说的保留 `actor=None`。
  - 不补 880 支克边；不改排盘；不改测试断言。
- **Todos**:
  - [ ] 合/冲/刑/穿施力方（带出处，未知留空）
  - [ ] 去体-体/双属-双属过滤
  - [ ] 柱内/邻柱生进入候选
  - [ ] 跑 481/0 + 全量 + 33 条 dev 复算
- **Exit proof**: 分支上 481/0、测试 0 failed、dev 方向召回提升且可解释。
- **Stop condition**: 需要动排盘或改断言；或修完 dev 仍 <60%。

### Phase 3: P1 hold-out 评分（1 天）
- **Purpose**: 用没参与调参的 20 例判 P1。
- **Entry condition**: Phase 2 exit proof 通过。
- **Phase rules**:
  - 一次性评分；不调规则、不换 hold-out、不换阈值。
  - 方向 ≥80/边 ≥90 才进 P2；<60 kill；60–80 只做局部修。
- **Todos**:
  - [ ] 跑 hold-out 评分 → `META/p1-holdout-result-v1.*`
  - [ ] 敏感性：剔除名人/边界/无配偶星
- **Exit proof**: 结果 JSON + 判定词（pass/between/kill）。
- **Stop condition**: <60% 直接 kill，不再调。

### Phase 4: P2 主功盲测（3–4 天，仅 P1 通过）
- **Purpose**: 验证 Agent 能否从 `engine.cli` + `query_theory` 选出原书主功。
- **Entry condition**: P1 pass。
- **Phase rules**:
  - 剔除名人盘；Agent 不看原书；机械判 + 随机基线；事实错误 0。
- **Todos**:
  - [ ] 去名人 hold-out；随机基线；三态一致；报告。
- **Exit proof**: 前两条 ≥70%、高出随机 30pp、三态 ≥70%、事实错误 0。
- **Stop condition**: 不到随机 +15pp 或事实错误 >0。

### Phase 5: 交付（1 天）
- **Purpose**: 把「能分析一张盘」变成用户可见的产物。
- **Todos**:
  - [ ] 3 份卡定稿（P1 后重跑，替换 pre-P1）
  - [ ] 报告、基线、交接书、队列更新
- **Exit proof**: 用户能读 3 份卡并指出每条断语的地址/原文；`verify_baseline` 绿。
- **Stop condition**: 卡仍被判定「模板」——先修事实层，不靠文案。

## Dry-Run Findings
- hold-out 可能凑不到 20 例非名人段派命例 → 若 <15，产品停在解释工作台，不硬跑 P1。
- 33 条一人标注，复核可能把 7/17 翻到 9/17 或 10/17，仍 <60%；若翻到 11/17，P1 线要重议。
- `reversed` 2 条可能是 `ke` 的 members 顺序问题，不是缺方向；修复要区分「方向错」与「无方向」。
- 3 张 pre-P1 卡可能大部分 `direction_known=false`；这是诚实展示缺口，不是失败。

## Final Validation
- `python -m pytest -q` 0 failed；`python -m tools.verify_baseline` 全绿；481/0。
- hold-out 评分 JSON 的判定词；3 份卡按 T-169 §6 判定表 ≥2 份「真分析」。
- 人类/领域专家能逐条回查地址与原文。

## First Execution Step
并行派 T-174（第二复核）、T-175（hold-out 策展）、T-176（3 张 pre-P1 卡）；
中枢验收并冻结 hold-out 后，独立 Agent 在 `rethink/2026-10-29` 做三处修复。
