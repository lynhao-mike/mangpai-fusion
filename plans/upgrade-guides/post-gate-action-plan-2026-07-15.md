# HOLD 后门禁行动 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不降低任何 GO 门槛、不伪造前瞻证据且不切换生产入口的前提下，用真实 prediction-first 新案例补齐 timing 覆盖、binary 校准、高风险 A 级双审标签与 L1 差异化路由证据，使六个月平台门禁从 HOLD 达到可提交 GO 切换提案的条件。

**Architecture:** 保持现有生产链完全不动，建立一条独立的“真实新案登记 → 白名单盲包 → staged 多派冻结 → 冻结后观察与双审 → 标签绑定 → 能力评分 → learned/static 留出门禁”证据链。计划分为数据采集期、校准验证期、路由 GO 准备期；每一阶段只提升独立证据制品，不回写静态权重、生产规则或历史 run snapshot。

**Tech Stack:** Python 3、pytest、stdlib CLI、JSON/JSONL 冻结制品、YAML 任务目录、现有 `engine/evaluation` 评分框架、witness HMAC 外部见证链。

## Global Constraints

- 目标架构服从 [`2026-07-11-bazi-intelligence-platform-core-design.md`](../../docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md)，推进顺序服从 [`bazi-intelligence-platform-roadmap.md`](../bazi-intelligence-platform-roadmap.md)。
- 当前 HOLD 事实源为 [`six-month-platform-gate-2026-07-15.md`](../../META/six-month-platform-gate-2026-07-15.md)；本计划不得把任务完成数、Claim 数量或报告观感替代证据门禁。
- 不降低 GO 门槛：不得缩减十任务矩阵、竞争覆盖要求、binary 校准样本数、前瞻案例数或高风险 A 级双审要求。
- prospective 案例必须是规则/路由冻结后进入系统的真实新命主；既有 `P-2026-*` 历史隔离案例、990 反馈案例、Top30、同命主重复报告和复制命盘均不得计入 prospective/E3。
- 预测冻结前禁止读取真实经历、反馈、标签、旧报告结论或其他流派中间输出；发现任何泄漏时整批 STOP，不能删除个别记录后继续评分。
- HOLD 期间 [`run_pipeline()`](../../engine/application/pipeline_runner.py:1) 与 [`DEFAULT_RUNNER_REGISTRY`](../../engine/claims/runner_registry.py:1) 保持不变；learned 路由只能显式注入 staged/评估路径。
- 反馈入口只使用 [`feedback_ingest.py`](../../tools/feedback_ingest.py)；不得恢复或使用 deprecated `calibrate.py`。
- runner 的 `claim / abstain / unsupported` 都必须保留；缺逐年流年时正确 abstain，不得为提高 timing 覆盖补造流年。
- 高风险任务 `wealth.debt`、`marriage.divorce_or_remarriage`、`health.system_risk` 必须由两名相互独立的人类 reviewer 盲审；不一致时由第三名 adjudicator 裁决，不能降为单审或自动标签。
- 正负例均按真实连续入组产生；禁止为了平衡标签而复制、筛掉或改写案例。可在招募阶段按“尚未知道结果的风险暴露/观察窗口”分层，但不得按已知真实结果挑样本。
- L9 只写不可变 capability snapshot；不得回写 [`domain-weights.yaml`](../../engine/domain-weights.yaml)、`expert-weights.yaml`、生产规则或历史 run snapshot。
- 每次写证据前先 `--dry-run`；制品目录必须全新且不存在，输入/目标路径链不得包含 symlink。
- 所有易变计数以当次 JSON 制品为准；本文只保存门槛和执行方法，不把运行时 N_eff、规则数或 git HEAD 当长期事实。

---

## 1. 起点、目标差距与不可逆决策

### 1.1 2026-07-15 HOLD 基线

| 证据维度 | 当前事实 | GO 所需证据 | 本计划责任阶段 |
|---|---|---|---|
| timing Claim 覆盖 | 四个 timing 任务 Claim 为 0；历史输入缺逐年流年 | 至少形成可审计的 structure/event/timing 非空覆盖，且 timing 来自真实 `liunian_steps` | 数据采集期 |
| 独立效用 E2 | 竞争记录已有，但 learned/static 选择变化为 0 | 至少一个任务竞争样本 ≥ 5、选择变化 ≥ 1、learned 效用不低于 static | 校准验证期 + 路由 GO 准备期 |
| 校准 E3 | binary 概率校准样本为 0 | `career.role_change` 或 `marriage.divorce_or_remarriage` 可评分 binary 样本 ≥ 20 且 `calibration_error < 0.2` | 数据采集期 + 校准验证期 |
| 高风险 E4 | 可评估记录为 0 | 三个高风险任务有 A 级双审标签，可计算高风险假阳性且不退化 | 数据采集期 + 校准验证期 |
| 前瞻证据 E6 | prospective/E3 为 0 | ≥ 30 个真实新命主完成冻结、观察、标签绑定与校验 | 数据采集期 |

### 1.2 最短路径与范围

本计划严格执行门禁报告的四步最短路径：

1. 先取得 ≥ 30 个真实 prospective/E3 完成案；
2. 在同一批或追加批中取得目标 binary 任务 ≥ 20 条可评分正负例，并把校准误差压到 0.2 以下；
3. 在竞争任务中形成至少 5 条多派可评分记录，并让 learned 至少改变 1 个选择且效用不退化；
4. 仅在前三步满足后重跑 L1 留出与总门禁，GO 只产生切换提案。

### 1.3 下一不可逆决策

唯一允许的下一不可逆决策是：所有门禁证据达到 GO 后，另起契约变更提案，将 staged 路径设为默认并保留 legacy 显式 fallback。本计划本身不执行入口切换。

---

## 2. 文件结构与职责锁定

### 2.1 新增代码与模板

| 文件 | 职责 |
|---|---|
| [`prospective-go-task-catalog-v1.json`](../../META/prospective-go-task-catalog-v1.json) | 本阶段唯一 CLI 任务目录；从 YAML 事实源精确冻结十任务，覆盖 structure/event/timing、binary 与三项高风险任务 |
| [`prospective-observation-v1.json`](../../templates/prospective-observation-v1.json) | 冻结后观察模板；只记录 task outcome、来源、观察时间和证据等级，不含预测内容 |
| [`high-risk-review-v1.json`](../../templates/high-risk-review-v1.json) | 单个 reviewer 的盲审模板；固定 reviewer 身份、任务、结论、来源引用和签署时间 |
| [`high_risk_review.py`](../../engine/evaluation/high_risk_review.py) | 纯领域逻辑：验证两份独立审查、判定一致/冲突、生成可绑定的 A 级最终标签或要求仲裁 |
| [`school_capability_review.py`](../../tools/school_capability_review.py) | `prepare / submit / adjudicate / finalize / audit` CLI；只写评估制品，不写生产规则或权重 |
| [`prospective_routing_adapter.py`](../../engine/decision/prospective_routing_adapter.py) | 把 prospective frozen run + `school-capability-scores/v1` 显式适配为 L1 审计输入，保留 prospective classification 与父制品摘要 |
| [`test_high_risk_review.py`](../../tests/evaluation/test_high_risk_review.py) | 双审身份分离、冲突仲裁、A 级升级、泄漏和篡改负向测试 |
| [`test_prospective_gate_workflow.py`](../../tests/evaluation/test_prospective_gate_workflow.py) | ≥30 案、≥20 binary、正负例、timing 输入、witness、冻结先于揭示的端到端门禁测试 |
| [`test_prospective_routing_adapter.py`](../../tests/decision/test_prospective_routing_adapter.py) | prospective schema、classification、subject identity 与 score identity 无损适配测试 |

### 2.2 每批新生成制品

以下以首批固定批次 ID `prospective-go-b01` 展示；追加批依次使用 `prospective-go-b02`、`prospective-go-b03`，不得覆盖旧目录：

```text
META/prospective-go/
├── prospective-go-b01-intake.json
├── prospective-go-b01-tasks-by-case.json
├── prospective-go-b01-blind-bundle/
│   ├── bundle-manifest.json
│   ├── tasks.json
│   ├── rule-snapshot.json
│   └── cases/<case_id>/chart.json
├── prospective-go-b01-frozen-run.json
├── prospective-go-b01-witness-registry.json
├── prospective-go-b01-observations-unbound.json
├── prospective-go-b01-high-risk-reviews/
│   └── <case_id>/<task_id>/{reviewer-a,reviewer-b,adjudication}.json
├── prospective-go-b01-labels-unbound.json
├── prospective-go-b01-labels-bound.json
├── prospective-go-b01-reveal-provenance.json
├── prospective-go-b01-reviewed-manifest.json
├── prospective-go-b01-evaluation-config.json
├── prospective-go-b01-scores.json
├── prospective-go-b01-capability-report.md
└── prospective-go-b01-validation.json
```

### 2.3 不修改清单

本计划执行期间禁止修改：

- [`pipeline_runner.py`](../../engine/application/pipeline_runner.py)
- [`runner_registry.py`](../../engine/claims/runner_registry.py) 中的默认注册对象
- [`domain-weights.yaml`](../../engine/domain-weights.yaml)
- `engine/expert-weights.yaml`
- [`render_report.py`](../../tools/render_report.py)
- 已存在的 historical frozen run、labels、scores 和 capability snapshot

---

## 3. 阶段总览、时间估算与关键路径

| 阶段 | 建议周期 | 日历估算 | 退出条件 |
|---|---:|---|---|
| 数据采集期 | 8—12 周 | 第 1—12 周 | ≥30 真实新案完成冻结后观察；目标 binary ≥20；三项高风险有 A 级双审；timing 输入具有逐年流年 |
| 校准验证期 | 2—3 周 | 第 13—15 周 | 至少一个目标 binary 任务 `calibration_error < 0.2`；高风险可评估且不退化；竞争任务覆盖达标 |
| 路由 GO 准备期 | 1—2 周 | 第 16—17 周 | learned/static 选择变化 ≥1、效用不退化，八项总门禁重跑完成 |

### 3.1 关键路径

```text
真实新案招募
→ 脱敏 input.md + 完整逐年流年
→ prospective-intake
→ prepare-blind
→ staged runner 冻结
→ 外部 witness 签署冻结事件
→ 观察窗结束/事实发生
→ 两名 reviewer 独立标注高风险任务
→ 冲突仲裁并生成 A 级标签
→ bind-labels + validate
→ score/report
→ 校准门禁
→ learned/static 留出对照
→ 六个月总门禁重跑
```

外部瓶颈是“观察窗结束后得到真实正负 outcome”，不是代码实现。若 12 周时仍不足 30 个已观察新案，阶段必须 HOLD 并继续采集，不得进入路由 GO 判定。

### 3.2 并行工作

- Task 1—2 可在第 1 周并行完成：一个锁定采集协议，一个实现双审工具。
- Task 3 的招募、Task 4 的每周冻结和 Task 5 的观察跟踪滚动并行。
- Task 6 只能消费已到观察终点的案例；不得提前揭示。
- Task 8 校准与 Task 9 竞争覆盖审计可在同一冻结评分制品上并行，但 Task 10 必须等二者均 GO。

---

# 阶段一：数据采集期

## Task 1: 冻结 prospective 采集协议与任务配额（第 1 周）

**目标：** 把“真实新案”“完成案”“正负例”“逐年流年完整”和“高风险 A 级双审”转为可检查的入组协议，避免运营口径替代代码门禁。

**Files:**
- Create: [`prospective-intake-protocol-v1.md`](../../META/prospective-intake-protocol-v1.md)
- Create: [`prospective-go-task-catalog-v1.json`](../../META/prospective-go-task-catalog-v1.json)
- Create: [`prospective-observation-v1.json`](../../templates/prospective-observation-v1.json)
- Create: [`prospective-go-b01-tasks-by-case.json`](../../META/prospective-go/prospective-go-b01-tasks-by-case.json)
- Test: [`test_prospective_gate_workflow.py`](../../tests/evaluation/test_prospective_gate_workflow.py)

**Interfaces:**
- Consumes: [`school-capability-task-catalog-v1.yaml`](../../mapping/school-capability-task-catalog-v1.yaml) 中已批准十任务及 [`school-capability-runner-coverage-v1.yaml`](../../mapping/school-capability-runner-coverage-v1.yaml) 的六来源覆盖。
- Produces: `school-capability-cli-tasks/v1` 十任务 JSON 冻结目录、每案任务白名单、观察窗、招募/冻结/观察职责分离规则，供 [`prospective-intake`](../../tools/school_capability_dataset.py:973) 消费。现有 [`school-capability-prospective-tasks-v1.json`](../../META/school-capability-prospective-tasks-v1.json) 只有 structure + timing 五任务，只作旧 bundle 追溯，禁止用于本阶段 binary/high-risk 采集。

**配额设计：**

| 任务 | 最低完成标签 | 样本策略 | 目的 |
|---|---:|---|---|
| `career.role_change` | 20 | 全部 30 案都登记；观察窗内无显著岗位/职业角色变化计负例 | 校准主路径 |
| `marriage.divorce_or_remarriage` | 20 | 全部满足婚姻状态可观察条件的案例登记 | 备用校准 + 高风险 |
| `wealth.debt` | 12 | 连续入组，不按已知债务结果挑选 | 高风险 E4 |
| `health.system_risk` | 12 | 需要可核验健康资料或结构化访谈 | 高风险 E4 |
| `career.change_window` | 10 | 必须含逐年 `liunian_steps` | timing + L1 竞争 |
| `marriage.event_window` | 10 | 必须含逐年 `liunian_steps` | timing + L1 竞争 |
| `health.event_window` | 8 | 必须含逐年 `liunian_steps` | timing 覆盖 |
| `wealth.major_loss_window` | 8 | 必须含逐年 `liunian_steps` | timing 覆盖 |

上述为采集下限而非 GO 门槛替代；总完成案例仍须 ≥30，binary 校准仍须 ≥20，多派竞争仍须按评分制品核算。

- [ ] **Step 1: 写失败的工作流门禁测试**

测试固定断言：少于 30 个唯一 `subject_id_hash` 为 HOLD；目标 binary 少于 20 为 HOLD；只有正例或只有负例为 HOLD；分配 timing 任务但 `liunian_steps` 为空为 HOLD；高风险最终标签没有两个不同 reviewer 身份为 HOLD。

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m pytest tests/evaluation/test_prospective_gate_workflow.py -q`

Expected: FAIL，因为协议验证器和模板尚未存在。

- [ ] **Step 3: 冻结十任务 prospective CLI 目录**

从 YAML 事实源逐字段复制且只保留下列十个既有任务 ID：`structure.overview`、`career.role_change`、`marriage.divorce_or_remarriage`、`wealth.debt`、`career.path_type`、`health.system_risk`、`career.change_window`、`marriage.event_window`、`health.event_window`、`wealth.major_loss_window`。JSON 顶层固定为 `schema_version="school-capability-cli-tasks/v1"`、`task_catalog_version="prospective-go-tasks-v1"`、`tasks=[...]`；契约测试逐项比对 YAML 的 `claim_type/scoring_method/quantifiable/high_risk/allowed_time_horizons/required_input_fields/label_schema`，防止手工漂移。

- [ ] **Step 4: 写协议与模板**

协议必须定义：

1. 入组时间必须早于 freeze；
2. 运营人员只能接触输入，runner operator 只能接触 blind bundle；
3. outcome custodian 在 freeze witness 完成前不得释放观察；
4. `not_observed` 只表示预先定义观察窗内未发生，不等于终身不会发生；
5. 每个 timing case 的 `input.md` 使用可被 [`_canonical_chart()`](../../tools/school_capability_dataset.py:633) 解析的 `$DY_LOOP`，至少包含覆盖观察窗的逐年流年行；
6. 同一 `sex_marker + four_pillars` 只入组一次；
7. 已知结果仅可在 freeze 后进入 observation/label 文件，不能写入 `input.md`。

- [ ] **Step 5: 填首批任务分配**

为首批计划招募的 10 个 case ID 预留 `P-GO-2026-001` 至 `P-GO-2026-010`，每案至少分配 `career.role_change` 与一个 timing 任务；高风险配额按上表轮转。case 目录只在真实命主到达时创建，禁止提前复制命盘填充。

- [ ] **Step 6: 运行协议测试**

Run: `python -m pytest tests/evaluation/test_prospective_gate_workflow.py -q`

Expected: PASS。

- [ ] **Step 7: 提交**

```bash
git add META/prospective-intake-protocol-v1.md META/prospective-go-task-catalog-v1.json templates/prospective-observation-v1.json META/prospective-go/prospective-go-b01-tasks-by-case.json tests/evaluation/test_prospective_gate_workflow.py
git commit -m "docs: freeze prospective go intake protocol"
```

**验收门禁：**
- **GO：** 协议、模板、配额和负向测试齐全；timing 完整度可机械检查。
- **HOLD：** 观察窗、负例定义、职责分离或流年格式仍有歧义。
- **STOP：** 协议允许既有历史案例改名、预测前读取 outcome 或同命主重复计数。

**依赖：** 无。

---

## Task 2: 实现高风险 A 级双审与仲裁门（第 1—2 周）

**目标：** 为 `wealth.debt`、`marriage.divorce_or_remarriage`、`health.system_risk` 建立不可绕过的双人独立审查，不改变现有 [`RevealedLabel`](../../engine/evaluation/models.py:159) 持久化契约。

**Files:**
- Create: [`high_risk_review.py`](../../engine/evaluation/high_risk_review.py)
- Create: [`school_capability_review.py`](../../tools/school_capability_review.py)
- Create: [`high-risk-review-v1.json`](../../templates/high-risk-review-v1.json)
- Create: [`test_high_risk_review.py`](../../tests/evaluation/test_high_risk_review.py)
- Modify: [`tools/README.md`](../../tools/README.md)

**Interfaces:**
- Consumes: 两份 `school-capability-high-risk-review/v1`、可选一份 `school-capability-high-risk-adjudication/v1`、冻结后 observation。
- Produces: `finalize_reviews(case_id, task_id, review_a, review_b, adjudication=None) -> dict`；仅在审查者不同、输入摘要一致且结论一致，或第三方完成仲裁时产出 `confidence_grade="A"` 的标准 label record。

- [ ] **Step 1: 写失败测试**

必须覆盖：

- 同一 reviewer 提交两次被拒绝；
- reviewer 与 intake operator 相同被拒绝；
- 两审引用不同 observation hash 被拒绝；
- 两审一致时生成 A 级 label；
- 两审不一致时没有 adjudication 必须 HOLD；
- adjudicator 与任一 reviewer 相同被拒绝；
- 第三方仲裁后保留两份原始意见与裁决理由；
- 非三项高风险任务不能走该工具伪造 A 级；
- review 文件含预测概率、school 输出或报告文本时被泄漏扫描拒绝。

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m pytest tests/evaluation/test_high_risk_review.py -q`

Expected: FAIL with import error for `engine.evaluation.high_risk_review`。

- [ ] **Step 3: 实现纯领域验证器**

审查对象固定字段：`schema_version`、`case_id`、`task_id`、`observation_sha256`、`reviewer`、`decision`、`source_refs`、`rationale`、`signed_at`。`decision` 必须符合任务目录 label schema；健康任务只能为 `low/moderate/high`，离婚与债务只能为 `occurred/not_observed`。

- [ ] **Step 4: 实现 CLI**

CLI 子命令：

```text
prepare    observation → 两份空白、互相不可见的 review packet
submit     验证并内容寻址保存单份 review
adjudicate 只在两个 review 冲突时接受第三方裁决
finalize   生成标准 unbound label 或返回 HOLD 原因
audit      汇总每个高风险任务的一致率、冲突率、A 级数和不可评估数
```

所有写命令支持 `--dry-run`；目标文件已存在时拒绝覆盖。

- [ ] **Step 5: 更新工具索引**

将 [`school_capability_review.py`](../../tools/school_capability_review.py) 登记为 active 数据治理辅助工具，明确它不替代 [`feedback_ingest.py`](../../tools/feedback_ingest.py)，不写生产规则或权重。

- [ ] **Step 6: 运行测试与工具注册检查**

Run: `python -m pytest tests/evaluation/test_high_risk_review.py tests/evaluation/test_scoring.py tests/evaluation/test_freeze.py -q && python tools/tool_registry.py --check`

Expected: 全部 PASS，工具检查 exit 0。

- [ ] **Step 7: 提交**

```bash
git add engine/evaluation/high_risk_review.py tools/school_capability_review.py templates/high-risk-review-v1.json tests/evaluation/test_high_risk_review.py tools/README.md
git commit -m "feat: add independent high risk label review gate"
```

**验收门禁：**
- **GO：** 双审身份与证据 hash 可验证；冲突必须第三方裁决；最终 A 级 label 可被现有 freeze/score 链消费。
- **HOLD：** 工具只能记录两个 reviewer 名称但不能证明观察输入一致，或 conflict 无法保留。
- **STOP：** 自动模型可充当 reviewer、单审可产 A 级、工具直接修改 production 权重。

**依赖：** Task 1 的任务与观察定义。

---

## Task 3: 建立真实新案招募与完整输入流水线（第 1—12 周持续）

**目标：** 连续招募至少 36 个真实新命主，预留约 15% 因失访、输入不完整或泄漏作废的缓冲，最终保证 ≥30 个完成案。

**Files:**
- Create per real subject: `cases/P-GO-2026-NNN-{乾/坤}-{四柱}/input.md`
- Append-only: [`prospective-go-recruitment-log.jsonl`](../../META/prospective-go/prospective-go-recruitment-log.jsonl)
- Test: existing [`test_dataset.py`](../../tests/evaluation/test_dataset.py)

**Interfaces:**
- Consumes: 命主授权后的脱敏问真输入；不得消费 `feedback.md`、报告或经历字段。
- Produces: 可被 [`register_prospective_intake()`](../../tools/school_capability_dataset.py:686) 严格解析的 `input.md`。

**单案采集流程（Task 3—11 同步契约）：** 每案 dry-run 后当天正式 single-case intake，不等待 10 案；连续招募目标与 historical baseline 阈值保留，但不再用批量边界阻塞单案链。

1. 每周目标 4—6 个真实新命主；连续编号，不复用失败编号。
2. intake operator 只整理性别、四柱、公历时间、起运、大运和逐年流年；已知经历放在独立 custody 系统，禁止进入仓库 input。
3. 每案用 `$BASE/$FOUR/$DY_LOOP` 格式；四个 timing 任务的候选必须含覆盖观察窗的逐年流年。
4. 首次进入仓库即计算 `subject_id_hash`；重复命主拒绝，不以改 case ID 绕过。
5. 招募日志只记录 `case_id`、consent reference、received_at、input completeness、assigned_tasks、operator；不记录 outcome。

- [ ] **Step 1: 每个新案运行入口预检**

Run: `python -m tools.preflight cases/P-GO-2026-001-乾-甲子乙丑丙寅丁卯/input.md`

Expected: exit 0。命令中的四柱仅演示路径格式；执行时必须使用真实首案的实际 case ID，不得创建演示命盘计数。

- [ ] **Step 2: 每案运行 single-case intake dry-run**

Run:

```bash
python -m tools.school_capability_dataset prospective-intake --input cases/P-GO-2026-001-乾-实际四柱/input.md --input cases/P-GO-2026-002-坤-实际四柱/input.md --input cases/P-GO-2026-003-乾-实际四柱/input.md --input cases/P-GO-2026-004-坤-实际四柱/input.md --input cases/P-GO-2026-005-乾-实际四柱/input.md --tasks META/prospective-go-task-catalog-v1.json --school ziping --school ditiansui --school duan --school ren --school gao --school yang --operator human-intake-01 --tasks-by-case META/prospective-go/prospective-go-b01-tasks-by-case.json --out META/prospective-go/prospective-go-b01-intake.json --dry-run
```

执行者必须把每个 `实际四柱` 替换为招募日志中该真实命主的四柱；首案可先执行同参数的单输入 dry-run，之后每 5 案重跑。dry-run 输出必须显示与本次输入数相同的不同 `subject_id_hash`，且没有 forbidden marker。继续直接使用现有 [`prospective-go-b01-tasks-by-case.json`](../../META/prospective-go/prospective-go-b01-tasks-by-case.json:1) 的 `P-GO-2026-NNN` 十槽位冻结表：CLI 会在本次 `--input` 集合中唯一解析已到达槽位至完整 case ID；同批、严格格式、从 `001` 连续预注册且任务合法的未来槽位允许尚未到达，无需生成按真实四柱改写的任务文件。完整 case 键零匹配、短槽位格式错误、跨批、编号缺口、全部未命中、多匹配或短/完整键重复解析至同案都会拒绝。真实路径由招募日志唯一决定，禁止创建示例案例计数。

- [ ] **Step 3: 每案当天正式写 single-case intake**

确认单案 dry-run 后，使用真实 `single-case-intake` 参数去掉 `--dry-run`，当天创建该案全新的 intake 与 future-question registration；不得等待 cohort 满 10 案。目标已存在时拒绝覆盖，真实新案未到时保持 HOLD 且不创建空制品。

- [ ] **Step 4: 运行数据隔离回归**

Run: `python -m pytest tests/evaluation/test_dataset.py -q`

Expected: PASS。

- [ ] **Step 5: 提交每批 input 与 intake 制品**

```bash
git add cases/P-GO-2026-*/input.md META/prospective-go/prospective-go-recruitment-log.jsonl META/prospective-go/prospective-go-b*-intake.json
git commit -m "data: register prospective go intake batch"
```

**验收门禁：**
- **GO：** 招募 ≥36、唯一 subject、至少 30 案输入完整、每个 timing 候选有真实逐年流年。
- **HOLD：** 有效新案不足 30，或 binary/timing/high-risk 配额不足。
- **STOP：** 发现历史案例改名、复制命盘、输入含 outcome/feedback/report/known facts、无授权真实个人数据。

**依赖：** Task 1。该任务是全计划最长关键路径。

---

## Task 4: 每案准备盲包并在结果揭示前冻结与验证（第 2—12 周滚动）

**目标：** 每案独立 bundle / freeze / witness / verification；每案运行六来源 staged Claim，由独立人类见证人证明冻结早于 outcome 揭示，并以 verification=VERIFIED 作为反馈释放前的人工硬停点。10 案只用于父引用聚合。

**Files:**
- Create per batch: `META/prospective-go/prospective-go-bNN-blind-bundle/`
- Create per batch: `META/prospective-go/prospective-go-bNN-frozen-run.json`
- Create/append per batch: `META/prospective-go/prospective-go-bNN-witness-registry.json`

**Interfaces:**
- Consumes: intake、任务目录、冻结规则快照。
- Produces: bundle manifest、六来源三态输出、freeze hash、外部 witness 链。

- [ ] **Step 1: dry-run 准备盲包**

Run:

```bash
python -m tools.school_capability_dataset prepare-blind --intake META/prospective-go/prospective-go-b01-intake.json --tasks META/prospective-go-task-catalog-v1.json --rule-snapshot META/prospective-go-rule-snapshot-v1.json --target-dir META/prospective-go/prospective-go-b01-blind-bundle --dry-run
```

Expected: 输出 bundle JSON；目标目录不存在；安全文件白名单精确为 `intake.json`、`tasks.json`、`rule-snapshot.json`、`bundle-manifest.json`、`cases/<case_id>/chart.json`。不得包含原始 `input.md`、feedback、labels、report、known facts 或其他旁路文件。

- [ ] **Step 2: 正式创建全新盲包**

重复 Step 1 去掉 `--dry-run`。

Expected: 目标目录创建成功，bundle hash 与 dry-run 一致。

- [ ] **Step 3: 生成并冻结 staged outputs**

Run:

```bash
python -m tools.school_capability_prospective stage-frozen-run --bundle-root META/prospective-go/prospective-go-b01-blind-bundle --out META/prospective-go/prospective-go-b01-frozen-run.json --dry-run
```

[`stage-frozen-run`](../../tools/school_capability_prospective.py:342) 只消费已校验 blind bundle，保留六来源所有 `claim/abstain/unsupported`，并把 `task_catalog_version` 与 `rule_snapshot_id` 绑定到 bundle 中任务目录和 [`prospective-go-rule-snapshot-v1.json`](../../META/prospective-go-rule-snapshot-v1.json:1) 的内容 hash。核对 dry-run 后才去掉 `--dry-run` 写入全新且不存在的 frozen run 路径。

- [ ] **Step 4: witness 一次安全生成/追加 registered、prepared、freeze 三事件段**

首次生成 Run:

```bash
python -m tools.school_capability_prospective witness-freeze-chain --intake META/prospective-go/prospective-go-b01-intake.json --bundle-root META/prospective-go/prospective-go-b01-blind-bundle --staged-run META/prospective-go/prospective-go-b01-frozen-run.json --out META/prospective-go/prospective-go-b01-witness-registry.json --witness-key-env SCHOOL_CAPABILITY_WITNESS_KEY --dry-run
```

[`witness-freeze-chain`](../../tools/school_capability_prospective.py:346) 会校验正式 intake、盲包 manifest、staged artifact 及 case 集，一次为每案生成完整且严格递增的 `registered → prepared → freeze` 三事件段。追加既有链时增加 `--registry <既有-registry>`，同时把 `--out` 指向全新路径；不得覆盖既有 registry。见证方确认 dry-run 后才正式写入并外部备份 registry root。此步骤不生成 reveal，outcome 在 freeze witness 完成前继续封存。HMAC key 必须由独立见证方持有，且仅从 `--witness-key-env` 指定的环境变量读取，不得写入命令参数值、仓库或制品。

- [ ] **Step 5: 审计 timing 输出**

按任务统计 Claim/abstain/unsupported。任何 timing Claim 必须引用 `liunian_steps.*`；若仍全为 0，不能伪造 Claim，转入 HOLD 并检查真实输入格式是否被 parser 丢失。

- [ ] **Step 6: 运行冻结回归**

Run: `python -m pytest tests/claims/test_multi_school_freeze.py tests/evaluation/test_dataset.py tests/evaluation/test_prospective_frozen_run.py -q`

Expected: PASS。

- [ ] **Step 7: 提交冻结制品**

```bash
git add META/prospective-go/prospective-go-b01-blind-bundle META/prospective-go/prospective-go-b01-frozen-run.json META/prospective-go/prospective-go-b01-witness-registry.json
git commit -m "eval: freeze prospective go blind batch"
```

**验收门禁：**
- **GO：** 每批 freeze hash 可复算；witness 已形成完整 `registered → prepared → freeze` 链，且 freeze 早于后续独立 reveal；四类 timing 至少总体出现非空 Claim。
- **HOLD：** 真实数据尚未到达、timing 正确 abstain 但 Claim 仍为 0，或 witness 尚未完成。HOLD 时不创建空盲包、空 frozen run 或空 witness registry。
- **STOP：** runner 在冻结前读到结果；bundle 含白名单外文件；hash 不一致；冻结后改写历史输出。

**依赖：** Task 3 当前单案正式 intake；不依赖满 10 案。

---

## Task 5: verification 后即时回顾与独立未来观察（第 1—12 周滚动）

**目标：** 每案 freeze 前预注册恰好 1 个三个月内 binary future question；verification=VERIFIED 后才释放 freeze 前事实进入 `prediction_first_immediate_retrospective`，窗口成熟后另以 `future_observation` 形成真实正负 outcome。两类 evidence class、label identity 与完成数完全分账；评估标签不直接回灌生产规则。

**Files:**
- Create per completed case: `META/prospective-go/observations/<case_id>.json`
- Modify only after observation: `cases/<case_id>/feedback.md`
- Create per batch: `META/prospective-go/prospective-go-bNN-observations-unbound.json`

**Interfaces:**
- Consumes: 观察窗结束后的命主确认、可核验文档或结构化访谈。
- Produces: 不含预测内容的 outcome observation；case 反馈通过 [`ingest()`](../../tools/feedback_ingest.py:1176) 单独进入既有闭环。

- [ ] **Step 1: 按任务冻结观察窗**

建议首轮使用 8—12 周固定观察窗：`career.role_change` 记录是否发生显著岗位/职业角色变化；未发生必须明确记录 `not_observed` 和观察起止日期。离婚/再婚不得把关系压力算正例；债务不得把正常信用消费算显著债务；健康风险必须有结构化依据。

- [ ] **Step 2: outcome custodian 填 observation**

每条必须含 `case_id`、`task_id`、`label`、`observed_at`、`observation_window`、`source_refs`、`quantifiable`、`conflict_state`、`custodian`。禁止复制 runner rationale 或概率。

- [ ] **Step 3: 对正式 case feedback 先 dry-run**

Run: `python -m tools.feedback_ingest P-GO-2026-001-乾-实际四柱 --dry-run --json`

Expected: exit 0，输出 statement 反馈映射；评估专用 observation 不由该命令生成。

- [ ] **Step 4: 人工确认后正式摄入反馈**

Run: `python -m tools.feedback_ingest P-GO-2026-001-乾-实际四柱 --json`

Expected: exit 0。不得使用 `calibrate.py`。

- [ ] **Step 5: 形成批次 unbound observations**

只收录已到观察终点的案例。失访标记 `no_data`，不伪装负例；矛盾来源标记 conflict 并进入人工裁决。

- [ ] **Step 6: 每周统计完成度**

统计唯一完成 case、目标 binary 正/负例、三项高风险待审数、四项 timing 有标签数。计数来自 observation 文件，不从招募数推断。

**验收门禁：**
- **GO：** ≥30 案完成 observation；目标 binary ≥20 且同时有正负例；失访/no_data 不计完成标签。
- **HOLD：** 招募够但观察未结束、失访导致完成数不足、某 binary 只有一个类别。
- **STOP：** freeze 前创建 observation；把未知当负例；把关系压力当离婚；用生产反馈改写历史 blind output。

**依赖：** Task 4 对应批次 freeze + witness 完成。

---

## Task 6: 完成三项高风险双审并绑定标签（第 8—13 周）

**目标：** 让债务、离婚/再婚、健康系统风险从“0 可评估”变为有 A 级双审的可评分任务。

**Files:**
- Create: `META/prospective-go/prospective-go-bNN-high-risk-reviews/**`
- Create: `META/prospective-go/prospective-go-bNN-labels-unbound.json`
- Create: `META/prospective-go/prospective-go-bNN-labels-bound.json`
- Create: `META/prospective-go/prospective-go-bNN-reveal-provenance.json`

**Interfaces:**
- Consumes: Task 5 observations、Task 4 freeze hash。
- Produces: 现有 [`reveal_labels()`](../../engine/evaluation/freeze.py:68) 可消费的 `school-capability-labels/v1`。

**双审流程：**

1. review coordinator 为同一 observation 生成 A/B 两份 packet，packet 不含预测和对方意见；
2. reviewer A 与 reviewer B 独立判断，二者不得是 intake operator、runner operator 或 outcome custodian；
3. 一致则 finalizer 产 A 级 label；
4. 不一致则第三名 adjudicator 只看 observation 与两份理由，给出裁决；
5. 原始 review 永久保留；最终 label 的 `source` 指向 review bundle hash，`reviewer` 记录双审/仲裁 identity 摘要；
6. 任何审查资料不足则保持不可评估，不降为 B 级凑数。

- [ ] **Step 1: 为每个高风险 observation 生成双审 packet**

Run: `python -m tools.school_capability_review prepare --observation META/prospective-go/observations/P-GO-2026-001-乾-实际四柱.json --task-catalog mapping/school-capability-task-catalog-v1.yaml --out-dir META/prospective-go/prospective-go-b01-high-risk-reviews/P-GO-2026-001-乾-实际四柱/wealth.debt --dry-run`

Expected: 两份内容 hash 一致、reviewer 槽分离的 packet；正式执行时去掉 `--dry-run`。

- [ ] **Step 2: 两名 reviewer 分别提交**

Run: `python -m tools.school_capability_review submit --packet META/prospective-go/prospective-go-b01-high-risk-reviews/P-GO-2026-001-乾-实际四柱/wealth.debt/reviewer-a-packet.json --decision META/prospective-go/prospective-go-b01-high-risk-reviews/P-GO-2026-001-乾-实际四柱/wealth.debt/reviewer-a-decision.json --out META/prospective-go/prospective-go-b01-high-risk-reviews/P-GO-2026-001-乾-实际四柱/wealth.debt/reviewer-a-review.json --dry-run`

Expected: 校验通过；正式执行去掉 `--dry-run`。

- [ ] **Step 3: 冲突时第三方仲裁**

Run: `python -m tools.school_capability_review adjudicate --review-a META/prospective-go/prospective-go-b01-high-risk-reviews/P-GO-2026-001-乾-实际四柱/wealth.debt/reviewer-a-review.json --review-b META/prospective-go/prospective-go-b01-high-risk-reviews/P-GO-2026-001-乾-实际四柱/wealth.debt/reviewer-b-review.json --decision META/prospective-go/prospective-go-b01-high-risk-reviews/P-GO-2026-001-乾-实际四柱/wealth.debt/adjudication-decision.json --out META/prospective-go/prospective-go-b01-high-risk-reviews/P-GO-2026-001-乾-实际四柱/wealth.debt/adjudication.json --dry-run`

Expected: 仅冲突记录可执行；一致记录调用应被拒绝。

- [ ] **Step 4: finalize 全批标签**

Run: `python -m tools.school_capability_review finalize --reviews-dir META/prospective-go/prospective-go-b01-high-risk-reviews --observations META/prospective-go/prospective-go-b01-observations-unbound.json --out META/prospective-go/prospective-go-b01-labels-unbound.json --dry-run`

Expected: A 级高风险标签均有两个不同 reviewer；no_data 不升级。确认后去掉 `--dry-run`。

- [ ] **Step 5: 在 freeze 后绑定标签**

Run:

```bash
python -m tools.school_capability_dataset bind-labels --labels META/prospective-go/prospective-go-b01-labels-unbound.json --frozen-run META/prospective-go/prospective-go-b01-frozen-run.json --out META/prospective-go/prospective-go-b01-labels-bound.json --dry-run
```

确认 freeze hash 后去掉 `--dry-run`。

- [ ] **Step 6: 签署 reveal witness 事件并生成 provenance**

reveal event 的时间必须晚于 freeze event；`unbound_labels_sha256` 必须与实际 unbound labels 一致。

- [ ] **Step 7: 审计双审覆盖**

Run: `python -m tools.school_capability_review audit --reviews-dir META/prospective-go/prospective-go-b01-high-risk-reviews --labels META/prospective-go/prospective-go-b01-labels-bound.json`

Expected: 三项高风险任务均有 A 级记录；duplicate reviewer=0；unresolved conflict=0 才可 GO。

**验收门禁：**
- **GO：** 三项高风险任务均可评估，所有计分标签为 A 级双审，冲突全部有第三方裁决。
- **HOLD：** 任一任务 0 条可评估、存在 unresolved conflict、资料不足。
- **STOP：** reviewer 不独立、预测泄漏进审查包、单审升级 A、删掉冲突样本改善指标。

**依赖：** Task 2、Task 4、Task 5。

---

# 阶段二：校准验证期

## Task 7: 构建十案父引用 cohort 并运行分账数据门禁（第 13 周）

**目标：** 每 10 个即时回顾完成案仅聚合不可变父引用；分别为 `prediction_capability_candidate_gate_v1` 消费 `prediction_first_immediate_retrospective`，为 `future_empirical_gate_v1` 消费 `future_observation`，不得输出混合完成数。

**Files:**
- Create: [`prospective-go-reviewed-manifest.json`](../../META/prospective-go/prospective-go-reviewed-manifest.json)
- Create: [`prospective-go-evaluation-config.json`](../../META/prospective-go/prospective-go-evaluation-config.json)
- Create: [`prospective-go-validation.json`](../../META/prospective-go/prospective-go-validation.json)

**Interfaces:**
- Consumes: 三批 intake/bundle/frozen/labels/reveal/witness 制品。
- Produces: `blind_candidate` manifest、A 级 evaluation config、数据链 GO/HOLD。

- [ ] **Step 1: 生成人工 reviewed manifest**

每个 case 的 eligible routes 必须与实际 frozen outputs 精确一致；expected schools 为六来源。reviewed manifest 由未参与 runner 的 human data reviewer 签署。

- [ ] **Step 2: 生成 evaluation config**

Run:

```bash
python -m tools.school_capability_dataset evaluation-config --manifest META/prospective-go/prospective-go-reviewed-manifest.json --baseline META/prospective-go/prospective-go-baseline-prevalence.json --tasks META/prospective-go-task-catalog-v1.json --evidence-grade A --evaluated-at 2026-10-15T00:00:00Z --out META/prospective-go/prospective-go-evaluation-config.json --dry-run
```

`evaluated-at` 是计划目标日期；若实际执行日晚于该日期，必须使用真实 UTC 时间，不得回填伪造时间。baseline prevalence 必须覆盖 eligible tasks，来源与估计方法写入独立制品。

- [ ] **Step 3: 对每批运行 dataset validate**

Run:

```bash
python -m tools.school_capability_dataset validate --manifest META/prospective-go/prospective-go-reviewed-manifest.json --labels META/prospective-go/prospective-go-b01-labels-bound.json --frozen-run META/prospective-go/prospective-go-b01-frozen-run.json --prospective-intake META/prospective-go/prospective-go-b01-intake.json --blind-bundle-manifest META/prospective-go/prospective-go-b01-blind-bundle/bundle-manifest.json --blind-bundle-root META/prospective-go/prospective-go-b01-blind-bundle --reveal-provenance META/prospective-go/prospective-go-b01-reveal-provenance.json --witness-registry META/prospective-go/prospective-go-b01-witness-registry.json --witness-key-env SCHOOL_CAPABILITY_WITNESS_KEY
```

如果现有 validator 要求单一 run 与 manifest 精确覆盖，则先用既有 freeze contract 将三批 outputs 合并为一个新的、内容寻址的 aggregate frozen run，并保留三个父 freeze hash；不得覆盖父批次。

- [ ] **Step 4: 核对硬计数**

必须同时满足：唯一 blind eligible ≥30；labelled ≥30；目标 binary 可评分 ≥20；正例 >0、负例 >0；三项高风险 A 级可评分 >0；四个 timing 任务至少有 Claim 与标签。

- [ ] **Step 5: 运行数据/evaluation 回归**

Run: `python -m pytest tests/evaluation tests/claims/test_multi_school_freeze.py -q`

Expected: PASS。

**验收门禁：**
- **GO：** validator 返回 GO，所有硬计数满足，leakage=0。
- **HOLD：** 样本数、类别、timing、高风险或 witness 任一不足。
- **STOP：** 泄漏、hash 篡改、同命主跨批重复、标签时间早于 freeze。

**依赖：** Task 3—6 全部完成。

---

## Task 8: 分账评分、校准诊断与一次性冻结修正（第 13—14 周）

**目标：** `prediction_capability_candidate_gate_v1` 仅消费 `prediction_first_immediate_retrospective`，要求至少 20 个独立完成命主、至少一个任务 15 条有效正反例且 `calibration_error < 0.2`；`future_empirical_gate_v1` 仅消费 `future_observation`，要求至少 10 个到期完成命主、至少一个同类 future task 8 条有效正反例且误差严格小于 0.2。其余竞争、高风险、selection change、utility 与审计门槛保持严格。

**Files:**
- Create: [`prospective-go-scores-v1.json`](../../META/prospective-go/prospective-go-scores-v1.json)
- Create: [`prospective-go-capability-report-v1.md`](../../META/prospective-go/prospective-go-capability-report-v1.md)
- Create only if HOLD: [`prospective-go-calibration-diagnosis-v1.md`](../../META/prospective-go/prospective-go-calibration-diagnosis-v1.md)
- Create only after approved recalibration: `META/prospective-go/capability-snapshots/sha256-{实际内容摘要}.json`

**Interfaces:**
- Consumes: prospective aggregate frozen run、manifest、bound labels、tasks、rule snapshot、evaluation config。
- Produces: task/prototype 能力后验、calibration error、Brier、增量实验和高风险审计。

- [ ] **Step 1: 运行 score**

Run:

```bash
python -m tools.school_capability_baseline score --frozen-run META/prospective-go/prospective-go-aggregate-frozen-run.json --manifest META/prospective-go/prospective-go-reviewed-manifest.json --labels META/prospective-go/prospective-go-labels-bound.json --tasks META/prospective-go-task-catalog-v1.json --rule-snapshot META/school-capability-rule-snapshot-prospective-v1.json --evaluation-config META/prospective-go/prospective-go-evaluation-config.json --out META/prospective-go/prospective-go-scores-v1.json
```

Expected: exit 0；binary calibration sample count 不再为 0。

- [ ] **Step 2: 生成 capability report**

Run:

```bash
python -m tools.school_capability_baseline report --scores META/prospective-go/prospective-go-scores-v1.json --manifest META/prospective-go/prospective-go-reviewed-manifest.json --out META/prospective-go/prospective-go-capability-report-v1.md
```

Expected: exit 0；报告明确 evidence grade 为 prospective/E3，不与历史基线混写。

- [ ] **Step 3: 应用校准硬门**

至少一个目标任务必须同时满足：

- 可评分 binary 样本 ≥20；
- 正例和负例都存在；
- `calibration_error < 0.2`，严格小于而非小于等于；
- calibration slice 不是通过删除 abstain、异常或高风险假阳性得到；
- 95% CI 与 N_eff 如实展示，不以 posterior 数组非空判 GO。

- [ ] **Step 4: HOLD 时做诊断，不直接调生产**

按 `probability_bin × task × school × prototype × evidence_completeness` 输出 reliability table，分类为：概率档位偏置、触发边界、类别不平衡、输入完整度、标签质量、原型稀疏。禁止看到标签后修改历史 frozen prediction。

- [ ] **Step 5: 仅允许一次预注册 recalibration 迭代**

若样本 ≥20 但 error ≥0.2，可用训练子集拟合单调校准映射，并生成独立 capability snapshot；随后必须在未参与拟合的新追加批或预留 holdout 上复核。不得在同一批拟合并宣称同一批 GO。

- [ ] **Step 6: 高风险安全检查**

三项高风险任务 `unassessable_count=0`；learned/staged 高风险假阳性不得高于 static/legacy 对照；任何增加直接 HOLD，持续增加则 STOP/REFRAME。

- [ ] **Step 7: 提交评分证据**

```bash
git add META/prospective-go/prospective-go-scores-v1.json META/prospective-go/prospective-go-capability-report-v1.md META/prospective-go/prospective-go-calibration-diagnosis-v1.md META/prospective-go/capability-snapshots
git commit -m "eval: score prospective calibration gate"
```

**验收门禁：**
- **GO：** 至少一个目标 binary 任务 n≥20 且 calibration error<0.2，高风险安全不退化。
- **HOLD：** n<20、单一类别、error≥0.2、CI 过宽或预留复核集不足。
- **STOP / REFRAME：** 合理追加样本与预注册校准后仍显著失准，或高风险假阳性恶化。

**依赖：** Task 7 GO。

---

## Task 9: 为两个新门禁构造分账竞争与差异化路由证据（第 14—15 周）

**目标：** 不通过手改 route 结果，分别为 `prediction_capability_candidate_gate_v1` 的 `prediction_first_immediate_retrospective` 与 `future_empirical_gate_v1` 的 `future_observation` 提供真实竞争证据；未来账不得复用即时回顾审查或标签，learned 选择变化至少 1 且效用不低于 static。

**Files:**
- Create: [`prospective_routing_adapter.py`](../../engine/decision/prospective_routing_adapter.py)
- Create: [`test_prospective_routing_adapter.py`](../../tests/decision/test_prospective_routing_adapter.py)
- Create: [`prospective-routing-batch-v1.json`](../../META/prospective-go/prospective-routing-batch-v1.json)
- Create: [`prospective-routing-scores-v1.json`](../../META/prospective-go/prospective-routing-scores-v1.json)
- Create: [`prospective-routing-competition-audit-v1.json`](../../META/prospective-go/prospective-routing-competition-audit-v1.json)
- Create: [`prospective-routing-prototype-coverage-v1.md`](../../META/prospective-go/prospective-routing-prototype-coverage-v1.md)
- Test: existing [`test_routing_holdout_artifacts.py`](../../tests/decision/test_routing_holdout_artifacts.py)

**Interfaces:**
- Consumes: prospective `FrozenBlindRun`、`school-capability-scores/v1`、reviewed manifest、`cfv-v1` prototypes、静态 coverage mapping。
- Produces: 现有 [`build_audit_artifact()`](../../tools/l1_routing_holdout_audit.py:243) 可消费的 `school-capability-historical-batch/v1` / `school-capability-historical-scores/v1` 兼容接口制品，但 `classification` 必须保持 `prospective`，并用 `adapter_origin`、父 freeze hash、父 score digest 证明这是显式适配而非伪造历史身份；同时产出每任务多派可评分数、后验差异、route score 分解和预期选择变化候选。

- [ ] **Step 1: 写 prospective 适配失败测试**

覆盖：拒绝 historical classification；manifest case/route 与 frozen outputs 不精确相等时拒绝；score identity 缺失/重复时拒绝；适配后 subject 的性别+四柱、task/school/state/utility、freeze hash、artifact digest 不变；输出 `classification="prospective"`；不得从报告文本构造输入。

- [ ] **Step 2: 运行失败测试**

Run: `python -m pytest tests/decision/test_prospective_routing_adapter.py -q`

Expected: FAIL with import error for `engine.decision.prospective_routing_adapter`。

- [ ] **Step 3: 实现最小显式 adapter**

实现 `adapt_prospective_for_holdout(frozen_run, scores, manifest, canonical_charts) -> tuple[dict, dict]`。只做 schema 映射和完整性验证，不重算 utility、不改 classification、不生成缺失竞争记录；输出写入两个独立内容寻址制品，供现有 L1 CLI 的 `--batch/--scores` 参数使用。

- [ ] **Step 4: 运行适配测试**

Run: `python -m pytest tests/decision/test_prospective_routing_adapter.py tests/decision/test_routing_holdout_artifacts.py -q`

Expected: PASS。

- [ ] **Step 5: 只统计合法竞争记录**

同案同任务至少两个 school 有可评分 utility 才计竞争；unsupported 和 `utility=None` 不计；合法 abstain 按现有评分协议参与。

- [ ] **Step 6: 核对任务门槛**

优先检查 `career.change_window`、`career.role_change`、`marriage.event_window`；至少一个任务竞争数 ≥5。若只有一个 school 产生 Claim，不能用复制 prediction 或把 unsupported 当 miss 补齐。

- [ ] **Step 7: 分析 learned/static 无差异根因**

逐条记录：静态首选、learned 后验来源、expected utility、不确定性惩罚、互补增益、最终 route score。只接受数据导致的排序变化；不得修改 static mapping 以制造变化。

- [ ] **Step 8: 追加定向但结果未知的新案**

若竞争数不足，可按缺失的输入特征/原型招募追加新命主，但招募时不能知道 outcome；重复 Task 3—8 的完整 freeze/reveal 流程。追加批至少保留 25% subject-level holdout。

- [ ] **Step 9: 运行路由回归**

Run: `python -m pytest tests/decision/test_prospective_routing_adapter.py tests/decision/test_routing_holdout_comparison.py tests/decision/test_real_routing_evaluator.py tests/decision/test_routing_holdout_artifacts.py -q`

Expected: PASS。

**验收门禁：**
- **GO：** 至少一个任务竞争数 ≥5，真实后验预示选择变化 ≥1，且没有改静态基线或评分算法。
- **HOLD：** 竞争覆盖不足或后验完全收缩到静态选择。
- **STOP / REFRAME：** 达到竞争覆盖后，数据稳定表明 learned 没有差异化能力，或差异只来自高方差小样本。

**依赖：** Task 8 至少校准 GO；可与 Task 8 诊断并行。

---

# 阶段三：路由 GO 准备期

## Task 10: 分别重跑两个离线 learned/static 严格留出门禁（第 16 周）

**目标：** 对 `prediction_capability_candidate_gate_v1` / `prediction_first_immediate_retrospective` 与 `future_empirical_gate_v1` / `future_observation` 分别证明 selection change、utility、校准和高风险审查条件；两个离线 GO 均不代表平台 GO 或生产 GO，`production_switch=false`。

**Files:**
- Create: [`l1-routing-prospective-holdout-v1.json`](../../META/prospective-go/l1-routing-prospective-holdout-v1.json)
- Modify: [`l1-routing-holdout-comparison.md`](../../reports/l1-routing-holdout-comparison.md)
- Test: [`test_routing_holdout_comparison.py`](../../tests/decision/test_routing_holdout_comparison.py)
- Test: [`test_real_routing_evaluator.py`](../../tests/decision/test_real_routing_evaluator.py)

**Interfaces:**
- Consumes: aggregate prospective batch/scores、frozen inputs、static coverage。
- Produces: GO/HOLD/STOP 路由报告；不自动切默认入口。

- [ ] **Step 1: 预检门槛**

仅当 Task 7—9 全部 GO 才执行。检查唯一 subject ≥30、binary calibration GO、高风险 A 级可评估、竞争任务 ≥5。

- [ ] **Step 2: 运行 L1 审计**

Run:

```bash
python -m tools.l1_routing_holdout_audit --batch META/prospective-go/prospective-routing-batch-v1.json --scores META/prospective-go/prospective-routing-scores-v1.json --static-coverage mapping/school-capability-runner-coverage-v1.yaml --out META/prospective-go/l1-routing-prospective-holdout-v1.json --report reports/l1-routing-holdout-comparison.md --holdout-fraction 0.25 --salt prospective-go-l1-v1 --minimum-competitive-cases 5 --generated-at 2026-10-22T00:00:00Z
```

两个输入必须由 Task 9 的显式 adapter 生成并保持 `classification="prospective"`；禁止直接把 prospective frozen run 冒充 CLI 所要求的历史 batch schema。实际运行使用真实 UTC 时间。

- [ ] **Step 3: 应用硬门禁**

同时满足才为 GO：

- learned/static 可比较记录非空；
- 至少一个任务 competitive count ≥5；
- selection changes ≥1；
- learned mean utility ≥ static mean utility；
- calibration error 不恶化；
- 高风险 false positives 不增加；
- 至少一个 task×prototype slice 显示非负、可复现增量；
- 训练能力快照只由训练 subject 构造。

- [ ] **Step 4: 重跑路由测试**

Run: `python -m pytest tests/decision/test_routing_holdout_comparison.py tests/decision/test_real_routing_evaluator.py tests/decision/test_routing_holdout_artifacts.py -q`

Expected: PASS。

- [ ] **Step 5: 提交证据，不切入口**

```bash
git add META/prospective-go/l1-routing-prospective-holdout-v1.json reports/l1-routing-holdout-comparison.md
git commit -m "eval: rerun prospective learned routing holdout"
```

**验收门禁：**
- **GO：** 上述七项全部满足。
- **HOLD：** 选择仍相同、竞争不足、效用相同但无差异、校准样本不足。
- **STOP / REFRAME：** learned 效用低于 static、校准恶化、高风险假阳性增加，或只在训练集提升。

**依赖：** Task 7、8、9 GO。

---

## Task 11: 只读保留 historical baseline 并形成独立升级提案（第 17 周）

**目标：** 分别读取两个新离线门禁结果，并保持 `historical_platform_baseline_2026_07_15` 只读独立 HOLD；禁止用 `20 immediate + 10 future` 冲抵原 30 案 baseline。两个离线 GO 都不是平台 GO 或生产 GO，`production_switch=false`，任何 GO 仍只形成独立升级提案而不修改生产入口。

**Files:**
- Create: `META/post-gate-platform-gate-2026-10-29.md`
- Create: `META/post-gate-platform-gate-2026-10-29.json`
- Modify: [`project-state.json`](../../META/project-state.json) only if evidence-backed status changes
- Modify: [`STATUS.md`](../../STATUS.md) only for stable artifact links

**Interfaces:**
- Consumes: Claim coverage、prospective validation、capability score、L1 holdout、高风险 audit、witness/reproducibility、feedback attribution、出口 lint。
- Produces: 最终 GO/HOLD/STOP 与下一不可逆决策。

- [ ] **Step 1: 运行完整测试**

Run: `python -m pytest tests -q`

Expected: 无 failure/error；允许仓库已有显式 skip。

- [ ] **Step 2: 运行工具、规则与 diff 检查**

Run: `python tools/tool_registry.py --check && python tools/rule_status_scan.py --check && git diff --check`

Expected: 两个工具 exit 0；diff check 无输出。

- [ ] **Step 3: 逐项复核八项证据**

| # | 证据 | GO 条件 |
|---|---|---|
| 1 | 六域 Claim 覆盖 | structure/event/timing 非空；timing 来自真实流年，不以强制发言补齐 |
| 2 | 独立效用 | 竞争任务 ≥5、选择变化 ≥1、learned 效用不低于 static |
| 3 | 校准 | 目标 binary n≥20 且 error<0.2 |
| 4 | 高风险 | 债务/离婚/健康均有 A 级双审可评估；假阳性不增加 |
| 5 | 审计链 | freeze、bundle、规则、runner、witness hash 可复算 |
| 6 | 反馈归因 | Claim → evidence → fact_refs，评估标签与生产反馈边界清楚 |
| 7 | 前瞻证据 | ≥30 唯一真实新命主完成 freeze→observe→label→validate |
| 8 | 出口安全 | 报告无 Claim/statement/capability 内部 ID 泄漏 |

- [ ] **Step 4: 写 JSON 与 Markdown 门禁制品**

JSON 固定字段：`phase`、`status`、`evidence_artifacts`、`accepted_hypotheses`、`rejected_hypotheses`、`known_risks`、`next_irreversible_decision`、`updated_at`。每个证据维度额外保存 `status`、`measurement`、`threshold`、`source_digest`。

- [ ] **Step 5: 根据证据判定**

- **GO：** 仅提出独立契约变更，将 staged 路径设为默认、legacy 保留显式 fallback；本任务不改 [`run_pipeline()`](../../engine/application/pipeline_runner.py:1) 或 [`DEFAULT_RUNNER_REGISTRY`](../../engine/claims/runner_registry.py:1)。
- **HOLD：** 保持 staged，列出具体缺口和追加样本类型，不重置已有可信证据。
- **STOP / REFRAME：** 冻结 learned capability snapshot，回退 static，保留已独立证明有价值的 Claim/L6/L9 模块。

- [ ] **Step 6: 运行元数据测试**

Run: `python -m pytest tests/test_project_metadata.py tests/test_output_linter.py tests/v5/test_report_view.py -q`

Expected: PASS。

- [ ] **Step 7: 提交门禁制品**

```bash
git add META/post-gate-platform-gate-2026-10-29.md META/post-gate-platform-gate-2026-10-29.json META/project-state.json STATUS.md
git commit -m "eval: record post hold platform gate"
```

**验收门禁：**
- **GO：** 八项全部满足，完整验证通过，形成独立切换提案入口。
- **HOLD：** 任一证据不足但核心假设未证伪。
- **STOP / REFRAME：** learned 独立效用退化、校准持续失败、高风险安全退化或发生标签泄漏。

**依赖：** Task 10 GO。

---

## 4. Prospective 批量操作手册

### 4.1 每批十案标准顺序

```text
D0 真实命主到达、授权、脱敏
D0 intake operator 写 input.md（不含经历）
D0 prospective-intake --dry-run
D0 prospective-intake 正式写 intake
D0 prepare-blind --dry-run
D0 prepare-blind 正式建新目录
D0 staged runner 生成 outputs
D0 freeze outputs
D0 外部 witness 签署 freeze
D+56 至 D+84 outcome custodian 结束观察
D+56 至 D+84 两名 reviewer 独立审高风险标签
D+56 至 D+84 冲突由第三方仲裁
D+56 至 D+84 bind-labels
D+56 至 D+84 witness 签署 reveal
D+56 至 D+84 validate
全部三批完成后 aggregate → score → report → holdout
```

### 4.2 角色隔离矩阵

| 角色 | 可见 | 禁止可见/禁止行为 |
|---|---|---|
| intake operator | 出生事实、大运流年 | outcome、旧报告、预测 |
| runner operator | blind bundle、规则快照 | 身份、反馈、真实经历 |
| witness | 事件 hash、时间、registry | 不需要读取命理结论 |
| outcome custodian | 原始观察资料 | freeze 前不得向 runner/reviewer 揭示 |
| reviewer A/B | 同一 observation packet | 预测、概率、对方意见 |
| adjudicator | observation + 两份冲突理由 | 不得兼任 A/B/intake/runner |
| evaluation operator | bound labels、frozen run、manifest | 不得改写任一父制品 |

### 4.3 正负例与失访规则

- 正例：观察窗内发生且符合 task catalog 精确定义。
- 负例：完整观察窗结束、来源可核验、明确未发生；标签为 `not_observed`。
- no_data：失访、观察窗未结束、资料冲突或无法确认；不进入 binary 校准分母。
- 禁止把 no_data 当负例；禁止因缺负例从历史库补入 prospective 集。
- 若自然发生率太低，延长观察或扩大真实新案批次；不能降低事件定义。

### 4.4 Timing 输入要求

- `input.md` 必须包含真实大运和逐年流年；不能只列大运十年干支。
- parser 产出的 canonical `chart.json` 必须有非空 `liunian_steps`，每步有 `year` 与 `ganzhi`。
- timing Claim 必须引用 `liunian_steps.<index>`，涉及大运时同时引用 `dayun_steps.<index>`。
- 无流年或无触发时 abstain 是正确行为；该案不贡献 timing Claim 覆盖，但仍保留在失败分类中。

---

## 5. 阶段级 GO / HOLD / STOP 总表

### 数据采集期

- **GO：** ≥30 唯一真实 prospective 完成案；目标 binary ≥20 且正负皆有；四项 timing 有完整流年与非空 Claim；三项高风险均有 A 级双审标签。
- **HOLD：** 招募/观察/标签/流年任一不足；继续 staged 采集。
- **STOP：** 历史改名、重复命主、预测前泄漏、witness/hash 失效。

### 校准验证期

- **GO：** 至少一个目标 binary task n≥20 且 calibration error<0.2；高风险可评估且不退化；竞争任务 ≥5。
- **HOLD：** 样本不足、单一类别、误差未达标、后验区间过宽。
- **STOP / REFRAME：** 在独立追加集仍失准、高风险假阳性恶化、校准只对训练集有效。

### 路由 GO 准备期

- **GO：** learned 选择变化 ≥1、效用不低于 static、校准不恶化、高风险不退化、总门禁八项全过。
- **HOLD：** learned/static 仍相同或任一总门禁证据不足。
- **STOP / REFRAME：** learned 独立效用低于 static、只在训练集提升或引入安全退化。

---

## 6. 风险、缓冲与回退

| 风险 | 早期信号 | 处理 | 禁止处理 |
|---|---|---|---|
| 12 周完成案不足 30 | 第 6 周完成/在途总量低于 20 | 扩大真实招募渠道、增加批次、延长阶段 | 复制历史案或同命主 |
| binary 只有正例或只有负例 | 第 8 周类别单一 | 连续招募并延长观察；保持真实自然分布 | 按已知结果挑案或改标签 |
| timing 仍全 abstain | canonical chart 无 `liunian_steps` | 修复输入采集格式并对新批重冻 | 给旧 freeze 补写流年后覆盖 |
| 高风险审查冲突高 | 双审一致率低 | 收紧事件定义、增加证据、第三方仲裁 | 删除冲突或降为单审 |
| calibration error≥0.2 | reliability bins 系统偏置 | 预注册训练/holdout 校准，一次一快照 | 同批拟合并同批宣称 GO |
| learned/static 仍相同 | 后验差不足或收缩强 | 增加真实竞争原型和 outcome | 手改 static mapping 制造差异 |
| 高风险假阳性增加 | learned 对高风险更激进 | STOP learned，回退 static，审查风险惩罚 | 降低高风险门槛 |
| 泄漏或 witness 断链 | reveal 早于 freeze/hash 不符 | 整批作废，从可信快照重来 | 删除单条异常继续评分 |

---

## 7. 最终验证清单

- [ ] 核心设计与路线中的预测/反馈隔离、三态克制、条件化能力、前瞻验证原则均有任务承接。
- [ ] 五个 HOLD 根因分别由 timing、竞争路由、校准、双审高风险、prospective 任务覆盖。
- [ ] prospective 总数门槛保持 ≥30；没有把 40 个既有 `P-2026-*` 历史隔离目录计入。
- [ ] binary 校准保持 ≥20 且 `calibration_error < 0.2`；包含真实正负例。
- [ ] 竞争任务保持 ≥5 且 learned 选择变化 ≥1；没有缩减任务集或修改 static baseline 制造变化。
- [ ] 三项高风险任务均执行两名独立 reviewer + 冲突第三方仲裁；没有单审 A 级。
- [ ] timing runner 只消费真实 `liunian_steps`；无输入时保留 abstain。
- [ ] 所有批次先 intake/bundle/freeze/witness，再 observe/review/bind/reveal。
- [ ] [`feedback_ingest.py`](../../tools/feedback_ingest.py) 是唯一生产反馈入口；未使用 deprecated 工具。
- [ ] HOLD 期间未修改 [`run_pipeline()`](../../engine/application/pipeline_runner.py:1) 或 [`DEFAULT_RUNNER_REGISTRY`](../../engine/claims/runner_registry.py:1)。
- [ ] 每阶段均有 GO/HOLD/STOP、依赖、精确交付文件、验证命令和提交边界。
- [ ] 最终 GO 只形成独立切换提案，不在门禁任务中直接切生产入口。
