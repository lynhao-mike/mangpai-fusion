# 八字智能推理平台六个月执行 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在六个月内先完成多知识来源标准 Claim 的中等覆盖，再以真实隔离数据验证条件化路由，并从第 4 个月开始以新旧并跑方式积累可切换证据。

**Architecture:** 保持现有生产入口为 fallback，以 `ChartFactLedger → cfv-v1 → task-specific runners → Claim → staged arbitration → run/decision snapshots → report view` 建立旁路主干。能力评估、L1 路由与 L9 学习只通过冻结制品和内容寻址快照连接；任何阶段未达到 GO 门禁时停在旁路，不用兼容成本换取虚假上线。

**Tech Stack:** Python 3、pytest、dataclass/frozen contracts、YAML task/rule registries、JSON frozen artifacts、现有 `engine/evaluation` 盲评框架、stdlib CLI。

## Global Constraints

- 目标架构服从 [`docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md`](../../docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md)，当前运行事实服从 [`engine/contracts/00-OVERVIEW.md`](../../engine/contracts/00-OVERVIEW.md)。
- 产品版本只从 [`VERSION`](../../VERSION) 读取；阶段名不等于产品版本。
- 不在本文硬编码 git HEAD、规则数量、N_eff 当前值、flagged/deprecated 清单；易变状态由运行时扫描或阶段证据制品承载。
- 预测冻结前禁止读取反馈、真实经历、旧报告结论或其他流派中间输出；发现标签泄漏时整批作废。
- L2 命题必须由事实与 `cfv-v1` 推导；人工 `school-claims.json` 不得成为能力评分输入。
- runner 必须支持 `claim / abstain / unsupported`；不得为覆盖率强制发言。
- 可证伪事件才可概率化；结构、画像与宽泛倾向不得伪装成精确概率。
- 健康、离婚、重大财务损失等高风险任务使用更高假阳性成本，并保留人工审批门。
- learned 路由在门禁 GO 前不得成为默认入口；L1 当前 HOLD 期间保持 `static` 默认。
- L9 只写独立、不可变、可回滚的 capability snapshot；不得回写静态生产权重、生产规则或历史 run snapshot。
- 新报告字段必须先进入 run/decision 结构，再由报告视图渲染；报告不得泄露内部 ID 或学习索引。
- 实施采用 TDD，小步提交；每个任务先运行失败测试，再写最小实现，再运行相关测试和全局护栏。

---

## 1. 已批准执行边界

### 1.1 路径与覆盖深度

1. 优先顺序固定为：**标准 Claim 覆盖 → 数据补齐与评分 → 知识重铸 → 路由验证 → 新旧并跑**。
2. 不先纵深重写单一领域；第一轮采用中等覆盖，每个知识来源承担 2—3 个强项任务，并覆盖结构、事件、应期三类 Claim。
3. 减少画像任务投入，把有限实现预算优先给财富、事业和可验证时间窗。
4. 时间窗 runner 采用**任派 + 段派双主力**；高派“流年有根论”作为第二批增强，不替代双主力。
5. 六个月内不承诺正式切换或删除旧引擎；第 4 月起开始新旧并跑，切换由证据门禁决定而非日历决定。

### 1.2 名词边界

本计划同时涉及子平、滴天髓、段、任、高、杨六个知识来源。它们按任务角色参与，不把“流派数量”固化为新的生产契约；子平与滴天髓在结构任务上组成主/副结构席，任派在应期任务上作为独立专业 runner。后续若要改变 [`engine/contracts/00-OVERVIEW.md`](../../engine/contracts/00-OVERVIEW.md) 中正式 runner 枚举，必须另行修改契约并经过架构 review。

### 1.3 能力矩阵

| 知识来源 | 核心擅长 | 独有武器 | 六个月角色 |
|---|---|---|---|
| 子平 | 格局成败定性、旺衰多口径、调候用神 | 八格取运体系 | 结构主判、事业结构与路径 |
| 滴天髓 | 寒暖燥湿、真假用神、五行颠倒、从化格 | 寒暖燥湿轴 | 结构副判、反证与调候约束 |
| 段派 | 做功体系、宾主论、应期四类、职业与重大事件 | 宾主体用、反客为主应期 | 事业/财富事件主力、应期双主力之一 |
| 任派 | 十八道法门、应期直定、穿、疾病与六亲 | 合留婚期法、直定应期法 | 四域应期双主力之一、健康事件辅助 |
| 高派 | 神煞实战、串宫压运、流年有根、财运应期 | 命宫长生诀、流年有根论 | 财富/健康事件与反证；第二批 timing 增强 |
| 杨派 | 婚姻规程、调候改运、禄、气数 | 婚姻操作规程、转象换象 | 婚姻事件主力、关系结构落地 |

### 1.4 已批准任务分配

| 任务 | 主力/协作 | Claim 类型 | 首轮验收重点 |
|---|---|---|---|
| `structure.overview` | 子平主 + 滴天髓副 | structure | 独立结构复核一致度，不概率化 |
| `career.role_change` | 子平 + 段派 | event | 二元事件判别、正负例与 abstain |
| `marriage.divorce_or_remarriage` | 杨派 + 段派 | event | 高风险假阳性、离婚与压力严格区分 |
| `wealth.debt` | 段派 + 高派 | event | 债务事件定义、反证条件、假阳性成本 |
| `career.path_type` | 段派 + 子平 | event/categorical | employment/entrepreneurship/mixed 分类 |
| `health.system_risk` | 高派 + 任派 | event/categorical | 风险分层、医学免责声明、高风险门禁 |
| `career.change_window` | 任派 + 段派；高派第二批 | timing | 年窗来源可计算、中心偏差与越界惩罚 |
| `marriage.event_window` | 任派 + 段派；高派第二批 | timing | 婚恋变化窗口，不自动等同离婚 |
| `health.event_window` | 任派 + 段派；高派第二批 | timing | 已记录显著事件窗口、高风险保守输出 |
| `wealth.major_loss_window` | 任派 + 段派；高派第二批 | timing | 重大损失白名单事件、假阳性成本 |

现有任务 ID 以 [`mapping/school-capability-task-catalog-v1.yaml`](../../mapping/school-capability-task-catalog-v1.yaml) 为准；实现不得另造近义任务 ID。

## 2. 六个月阶段总览

| 月份 | 阶段 | 主要交付 | 退出条件 |
|---|---|---|---|
| 月 1 | 数据与契约锁定 | 任务/事件语义冻结、runner 覆盖清单、prospective intake 常态化 | 任务无歧义；输入、输出、泄漏边界有测试 |
| 月 2 | Claim 中等覆盖 | 六来源强项任务 runner；任+段 timing 双主力最小闭环 | 各目标任务至少有主力实现；三态、证据、稳定 ID 测试通过 |
| 月 3 | 知识重铸与评分 | executable rules、正反边界例、历史隔离评分与失败分类 | 规则有判别力；新命题可进入 evaluation；不低于可比基线或 HOLD |
| 月 4 | L1 路由验证 + 并跑启动 | learned/static 留出对照；新旧结构化 diff | 有真实竞争样本才判 GO；否则维持 HOLD 并继续采集 |
| 月 5 | 并跑扩大 + L6/L9 接线 | 六域并跑、分段仲裁、反馈归因、capability snapshot | 高风险指标不退化；历史快照不可变；回滚通过 |
| 月 6 | 生产候选验收 | E3/E4 前瞻证据、切换建议、旧引擎处置建议 | 满足正式切换门禁才提案；否则保持 staged fallback |

## 3. 通用 GO / HOLD / STOP 与回退

### GO

每个阶段全部满足：预测冻结无泄漏；推理轨迹可追溯；与旧流程或静态基线同案比较；误差、校准与高风险假阳性被评估；失败样本完整保留并分类；产物可按版本和快照复现。

### HOLD

样本不足、竞争覆盖不足、可信区间过宽、标签质量不足、原型大量未分类或工程证据不完整时进入 HOLD。HOLD 不等于失败：继续旁路、继续采集、缩小结论范围，但不得把等价重放宣称为学习增益。

### STOP / REFRAME

出现以下任一情况：独立集持续低于旧流程；只在训练集提升；标签泄漏；高风险假阳性恶化；关键知识无法形成可判别规则；条件化路由增益小于复杂度与方差成本。

### 回退策略

1. Claim runner 退化：禁用对应 school/task 注册项，保留其 `unsupported` 状态，不影响其他 runner。
2. learned 路由退化：切回 `routing_mode="static"`，冻结失败的 capability snapshot，不删除审计制品。
3. staged arbitration 退化：使用旧仲裁对照路径，保留新旧 decision diff。
4. L9 更新异常：回滚到父 capability snapshot；历史 run snapshot 保持字节不变。
5. 报告覆盖退化：不切 [`tools/render_report_v6.py`](../../tools/render_report_v6.py) 默认入口，定位上游 run/decision 缺失，不在 Markdown 补造结论。
6. 发现泄漏：作废整批 freeze/score/report 制品，从最后一个可信规则快照重新冻结。

---

### Task 1: 冻结六个月任务与事件语义（月 1）

**Files:**
- Modify: `mapping/school-capability-task-catalog-v1.yaml`
- Create: `mapping/school-capability-runner-coverage-v1.yaml`
- Test: `tests/evaluation/test_six_month_task_contract.py`

**Interfaces:**
- Consumes: `BlindTask` 及现有 task catalog loader。
- Produces: 唯一任务 ID、事件定义、主/副 runner、首批/第二批标记，供后续 orchestrator 和评估使用。

- [ ] **Step 1: 写失败的契约测试**

测试必须断言上表十个任务 ID 全部存在；`marriage.divorce_or_remarriage`、`wealth.debt`、`health.system_risk` 与两个高风险 timing 任务保持 `high_risk=true`；coverage registry 中 `ren` 与 `duan` 同时覆盖四个 timing 任务，`gao` 标记为 `batch_2`。

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m pytest tests/evaluation/test_six_month_task_contract.py -q`

Expected: FAIL，原因是 `school-capability-runner-coverage-v1.yaml` 尚不存在或 coverage 字段未满足契约。

- [ ] **Step 3: 写最小 coverage registry**

每条记录固定字段：`task_id`、`claim_type`、`primary_schools`、`supporting_schools`、`delivery_batch`、`high_risk`。只登记本计划十个任务，不增加画像任务。

- [ ] **Step 4: 运行契约测试**

Run: `python -m pytest tests/evaluation/test_six_month_task_contract.py -q`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add mapping/school-capability-task-catalog-v1.yaml mapping/school-capability-runner-coverage-v1.yaml tests/evaluation/test_six_month_task_contract.py
git commit -m "docs: freeze six month task coverage contract"
```

### Task 2: 建立 runner 注册与任务级调度边界（月 1）

**Files:**
- Modify: `engine/claims/orchestrator.py`
- Create: `engine/claims/runner_registry.py`
- Test: `tests/claims/test_runner_registry.py`

**Interfaces:**
- Consumes: `ClaimGenerator = Callable[[ChartFactLedger, ChartFeatureVector, BlindTask], list[Claim]]`。
- Produces: `RunnerRegistry.resolve(school_id, task_id) -> ClaimGenerator | None`；orchestrator 使用显式注入 registry，不再扩大全局硬编码字典。

- [ ] **Step 1: 写失败测试**

覆盖：已注册 school/task 返回 generator；未覆盖任务返回 `None` 并映射为 `unsupported`；同一 school/task 重复注册抛 `ValueError`；默认 registry 保持现有 `ziping` 与 `ren` 行为。

- [ ] **Step 2: 确认测试失败**

Run: `python -m pytest tests/claims/test_runner_registry.py -q`

Expected: FAIL with import error for `engine.claims.runner_registry`。

- [ ] **Step 3: 实现最小只读注册表并接入 orchestrator**

注册表只负责调度，不读取 YAML、不做 IO、不计算能力权重。`generate_blind_outputs()` 新增可选 `registry` 参数；缺省使用冻结默认注册表，保持现有调用兼容。

- [ ] **Step 4: 运行 claim 回归**

Run: `python -m pytest tests/claims/test_runner_registry.py tests/claims/test_claim_engine.py tests/claims/test_ren_binary_career.py -q`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add engine/claims/runner_registry.py engine/claims/orchestrator.py tests/claims/test_runner_registry.py
git commit -m "refactor: add task scoped claim runner registry"
```

### Task 3: 实现段派事件 runner（月 1—2）

**Files:**
- Create: `engine/v5/duan_runner.py`
- Modify: `engine/claims/runner_registry.py`
- Test: `tests/claims/test_duan_runner.py`

**Interfaces:**
- Consumes: `ChartFactLedger`、`ChartFeatureVector`、`BlindTask`。
- Produces: `generate_claims(chart, features, task) -> list[Claim]`，首批支持 `career.role_change`、`career.path_type`、`wealth.debt`、`marriage.divorce_or_remarriage` 以及四个 timing 任务。

- [ ] **Step 1: 为每个首批事件任务写正例、反例与边界测试**

事件命题至少引用宾主/做功可计算代理特征；离婚任务必须证明“关系压力”不会自动触发离婚；债务任务必须有明确负债事件 falsifier；残缺证据返回 abstain。

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/claims/test_duan_runner.py -q`

Expected: FAIL with import error for `engine.v5.duan_runner`。

- [ ] **Step 3: 实现事件 Claim 的最小判别规则**

每条 Claim 使用 `stable_claim_id()`，evidence 至少含一个可解析 `fact_ref` 或 `feature_ref`，并通过 `validate_claim_evidence()`；不把教材原文整段作为触发器。

- [ ] **Step 4: 运行段派 runner 与证据验证测试**

Run: `python -m pytest tests/claims/test_duan_runner.py tests/claims/test_claim_engine.py -q`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add engine/v5/duan_runner.py engine/claims/runner_registry.py tests/claims/test_duan_runner.py
git commit -m "feat: add duan task specific event claims"
```

### Task 4: 实现段派 timing runner，与任派形成双主力（月 2）

**Files:**
- Create: `engine/v5/duan_timing.py`
- Modify: `engine/v5/duan_runner.py`
- Test: `tests/claims/test_duan_timing.py`

**Interfaces:**
- Consumes: 原局四柱、`dayun_steps`、`liunian_steps` 与段派事件候选。
- Produces: 四个白名单任务的 `timing_claim`，时间窗必须来自可计算岁运触发；无触发返回空列表。

- [ ] **Step 1: 写双主力独立性失败测试**

同一命盘分别运行任派与段派，断言两者独立生成、claim ID 不同、均不读取对方输出；换流年后段派时间窗随输入变化；无岁运触发时 abstain。

- [ ] **Step 2: 运行失败测试**

Run: `python -m pytest tests/claims/test_duan_timing.py -q`

Expected: FAIL because `engine.v5.duan_timing` is missing。

- [ ] **Step 3: 实现段派 timing 最小闭环**

将反客为主、宾主体用与岁运触发实现为小型纯函数；输出限制为每任务最多一条最强时间窗命题；高风险任务保守降低 confidence 上限。

- [ ] **Step 4: 运行任+段 timing 测试**

Run: `python -m pytest tests/claims/test_duan_timing.py tests/claims/test_claim_engine.py -q`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add engine/v5/duan_timing.py engine/v5/duan_runner.py tests/claims/test_duan_timing.py
git commit -m "feat: add duan timing runner beside ren"
```

### Task 5: 补齐滴天髓、高派、杨派强项 Claim（月 2）

**Files:**
- Modify: `engine/v5/ditiansui_runner.py`
- Create: `engine/v5/gao_runner.py`
- Create: `engine/v5/yang_runner.py`
- Modify: `engine/claims/runner_registry.py`
- Test: `tests/claims/test_school_strength_runners.py`

**Interfaces:**
- Consumes: 统一 Chart/CFV/Task，不消费其他 runner 输出。
- Produces: 滴天髓 `structure.overview`；高派 `wealth.debt` 与 `health.system_risk`；杨派 `marriage.divorce_or_remarriage` 的 task-specific Claim。

- [ ] **Step 1: 写三派强项任务失败测试**

每派至少一正例、一反例、一 abstain；高派健康和杨派离婚按高风险规则限制；滴天髓仅输出结构命题且无时间窗。

- [ ] **Step 2: 运行失败测试**

Run: `python -m pytest tests/claims/test_school_strength_runners.py -q`

Expected: FAIL，缺少高/杨 runner 或现有滴天髓 runner 未满足统一 Claim 契约。

- [ ] **Step 3: 实现最小规则与注册**

高派首批只做事件/风险分层，不提前实现 timing；杨派严格区分婚姻压力与离婚事件；滴天髓复用 `cfv-v1` 寒暖燥湿与结构信号。

- [ ] **Step 4: 运行全部 Claim 子集**

Run: `python -m pytest tests/claims -q`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add engine/v5/ditiansui_runner.py engine/v5/gao_runner.py engine/v5/yang_runner.py engine/claims/runner_registry.py tests/claims/test_school_strength_runners.py
git commit -m "feat: add school strength claim coverage"
```

### Task 6: 把 runner 输出接入冻结评估链（月 2—3）

**Files:**
- Modify: `engine/claims/blind_adapter.py`
- Modify: `engine/claims/orchestrator.py`
- Test: `tests/claims/test_multi_school_freeze.py`

**Interfaces:**
- Consumes: 六来源 task-specific Claim 与三态结果。
- Produces: `FrozenBlindRun`，包含稳定输出、规则快照引用和 task catalog 版本；不包含反馈或旧报告字段。

- [ ] **Step 1: 写端到端失败测试**

用固定 Chart 和十任务目录运行所有已注册 runner，冻结后检查稳定哈希、三态保留、证据映射完整、重复运行字节等价；静态扫描禁止 import feedback/report modules。

- [ ] **Step 2: 运行失败测试**

Run: `python -m pytest tests/claims/test_multi_school_freeze.py -q`

Expected: FAIL，直到新增 runner 能被默认或显式 registry 调度并冻结。

- [ ] **Step 3: 最小适配 frozen output**

不改变 [`engine/evaluation`](../../engine/evaluation/) 契约；只在 claims adapter 处理 Claim 类型映射和三态输出。

- [ ] **Step 4: 运行冻结与 evaluation 回归**

Run: `python -m pytest tests/claims tests/evaluation -q`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add engine/claims/blind_adapter.py engine/claims/orchestrator.py tests/claims/test_multi_school_freeze.py
git commit -m "feat: freeze multi school task claims"
```

### Task 7: 重铸首批 ExecutableRule 与判别测试（月 3）

**Files:**
- Create: `theory/production/claim-rules-v1.yaml`
- Create: `engine/claims/rule_loader.py`
- Modify: `engine/v5/duan_runner.py`
- Modify: `engine/v5/gao_runner.py`
- Modify: `engine/v5/yang_runner.py`
- Test: `tests/claims/test_executable_claim_rules.py`

**Interfaces:**
- Consumes: 结构化规则字段 `rule_id/school_id/task_scope/required_facts/exclusions/counter_conditions/falsifier/source_refs`。
- Produces: 只读、版本化规则对象；runner 通过稳定谓词执行，不把新增命理经验硬编码进通用执行器。

- [ ] **Step 1: 写规则 schema 与判别失败测试**

每条生产规则必须通过字段校验，并有正例触发、反例不触发、排除条件、边界 abstain、反证条件、跨案例稳定性六类测试。

- [ ] **Step 2: 运行失败测试**

Run: `python -m pytest tests/claims/test_executable_claim_rules.py -q`

Expected: FAIL because rule registry/loader does not exist。

- [ ] **Step 3: 迁移首批强项规则**

只迁移 Tasks 3—5 已证明需要的规则；原文保留为 `source_refs`，不得把原文转录当可执行触发器。

- [ ] **Step 4: 运行规则与 Claim 回归**

Run: `python -m pytest tests/claims -q`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add theory/production/claim-rules-v1.yaml engine/claims/rule_loader.py engine/v5/duan_runner.py engine/v5/gao_runner.py engine/v5/yang_runner.py tests/claims/test_executable_claim_rules.py
git commit -m "feat: externalize first executable claim rules"
```

### Task 8: 运行历史隔离评分并维护前瞻采集（月 1—6 持续）

**Files:**
- Modify: `META/school-capability-tasks.json` only when task catalog synchronization requires it
- Create: `META/six-month-capability-baseline-YYYY-MM-DD.json`
- Create: `META/six-month-capability-baseline-YYYY-MM-DD.md`
- Test: existing `tests/evaluation/`

**Interfaces:**
- Consumes: 已审核 manifest、冻结 runner 输出、冻结后揭示的 labels。
- Produces: 六维 `CapabilityPosterior` 与基线报告；历史隔离证据保持其真实 evidence grade，不冒充 prospective。

- [ ] **Step 1: 审计输入与污染分级**

Run: `python -m tools.school_capability_baseline audit --help`

Expected: exit 0 and CLI usage。按 CLI 当前参数生成审计制品，人工 review 后才进入 freeze/score。

- [ ] **Step 2: 对新案执行 prediction-first 隔离**

先用 [`tools/school_capability_dataset.py`](../../tools/school_capability_dataset.py) 的 `prospective-intake` 和 `prepare-blind`，确认 bundle 只含白名单输入、tasks、rule snapshot 和 manifest；反馈不得进入 bundle。

- [ ] **Step 3: 冻结、揭示、评分和报告**

按 [`tools/README.md`](../../tools/README.md) 当前 CLI 契约运行 audit→freeze→score→report 链；输出文件使用实际日期替换 `YYYY-MM-DD`，但本文不复制易漂移样本数与 N_eff。

- [ ] **Step 4: 分类失败案例**

每个失败归入：coverage、trigger boundary、label quality、input completeness、calibration、high-risk false positive、leakage。禁止删除异常样本改善分数。

- [ ] **Step 5: 提交只读证据制品**

```bash
git add META/six-month-capability-baseline-*.json META/six-month-capability-baseline-*.md
git commit -m "eval: record multi school capability baseline"
```

### Task 9: 重跑 L1 learned/static 留出门禁（月 4）

**Files:**
- Modify: `reports/l1-routing-holdout-comparison.md`
- Test: `tests/decision/test_routing_holdout_comparison.py`
- Test: `tests/decision/test_real_routing_evaluator.py`

**Interfaces:**
- Consumes: 训练集能力快照、严格隔离留出集、`CapabilityRegistry`。
- Produces: GO/HOLD/STOP 对照报告；不自动切换默认路由。

- [ ] **Step 1: 验证竞争覆盖，不足则直接 HOLD**

Run: `python -m tools.l1_routing_holdout_audit --help`

Expected: exit 0 and CLI usage。使用当前 CLI 参数生成对照；同案同任务至少两派可评分才计竞争样本。

- [ ] **Step 2: 运行路由测试**

Run: `python -m pytest tests/decision/test_routing_holdout_comparison.py tests/decision/test_real_routing_evaluator.py tests/decision/test_routing_holdout_artifacts.py -q`

Expected: PASS。

- [ ] **Step 3: 应用硬门禁**

只有 learned 至少改变一个选择、留出效用不低于 static、校准不恶化、高风险假阳性不增加，才写 GO。选择完全相同、真实竞争样本不足或仅有正例时写 HOLD。

- [ ] **Step 4: 提交证据，不切默认入口**

```bash
git add reports/l1-routing-holdout-comparison.md
git commit -m "eval: refresh learned routing holdout gate"
```

### Task 10: 启动新旧并跑与结构化差异审计（月 4—5）

**Files:**
- Create: `engine/application/staged_parallel_runner.py`
- Create: `engine/application/run_comparison.py`
- Test: `tests/application/test_staged_parallel_runner.py`
- Test: `tests/application/test_run_comparison.py`

**Interfaces:**
- Consumes: legacy pipeline 输出、新 Claim/L6 run snapshot、同一标准 Chart。
- Produces: `RunComparison`，按 task/domain 记录 coverage、结论方向、时间窗、证据完整度与高风险差异；不得比较自然语言表面相似度代替结构比较。

- [ ] **Step 1: 写并跑隔离失败测试**

断言两条路径读取同一输入但互不读取对方中间态；任一路径失败不改写另一条快照；comparison 不含反馈字段。

- [ ] **Step 2: 运行失败测试**

Run: `python -m pytest tests/application/test_staged_parallel_runner.py tests/application/test_run_comparison.py -q`

Expected: FAIL with missing staged parallel modules。

- [ ] **Step 3: 实现最小并跑与结构化 diff**

不修改 legacy 默认入口；新入口显式调用。差异维度固定为 task coverage、claim state、event label、polarity、time window、risk flag、evidence completeness。

- [ ] **Step 4: 运行 application 与核心回归**

Run: `python -m pytest tests/application/test_staged_parallel_runner.py tests/application/test_run_comparison.py tests/claims tests/decision -q`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add engine/application/staged_parallel_runner.py engine/application/run_comparison.py tests/application/test_staged_parallel_runner.py tests/application/test_run_comparison.py
git commit -m "feat: add structured legacy and claim pipeline comparison"
```

### Task 11: 接入 staged L6 与 L9 治理（月 5）

**Files:**
- Modify: `engine/application/staged_parallel_runner.py`
- Modify: `engine/decision/l6_staged_arbitration.py`
- Modify: `engine/learning/service.py`
- Test: `tests/decision/test_staged_arbitration.py`
- Test: `tests/learning/test_service.py`
- Test: `tests/application/test_staged_learning_integration.py`

**Interfaces:**
- Consumes: task-specific Claims、显式 L1 route plan、冻结反馈观察。
- Produces: 三段 decision run、条件化 LearningDecision、内容寻址 capability snapshot；learned route 仅显式注入。

- [ ] **Step 1: 写集成失败测试**

覆盖：structure/event/timing 分段；高风险冲突 unresolved；L1 缺失显式 uniform fallback；不可归因反馈 no_data；低样本 record_only；回滚恢复父快照；历史 run 字节不变。

- [ ] **Step 2: 运行失败测试**

Run: `python -m pytest tests/application/test_staged_learning_integration.py -q`

Expected: FAIL，直到 application 旁路完成 L6/L9 接线。

- [ ] **Step 3: 实现最小接线**

复用现有 L6/L9 模块，不重写评估框架，不向静态权重文件回灌，不自动应用高风险更新。

- [ ] **Step 4: 运行 decision/learning/application 回归**

Run: `python -m pytest tests/decision tests/learning tests/application/test_staged_learning_integration.py -q`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add engine/application/staged_parallel_runner.py engine/decision/l6_staged_arbitration.py engine/learning/service.py tests/application/test_staged_learning_integration.py tests/decision/test_staged_arbitration.py tests/learning/test_service.py
git commit -m "feat: connect staged arbitration and governed learning"
```

### Task 12: 高派第二批 timing 增强（月 5）

**Files:**
- Create: `engine/v5/gao_timing.py`
- Modify: `engine/v5/gao_runner.py`
- Modify: `engine/claims/runner_registry.py`
- Test: `tests/claims/test_gao_timing.py`

**Interfaces:**
- Consumes: 流年/大运事实、流年有根与串宫压运的可计算谓词。
- Produces: 四域 timing 的第二批独立 Claim；它是任+段双主力的增强/反证，不替代主力。

- [ ] **Step 1: 写第二批门禁失败测试**

测试必须证明高派输出独立于任/段；无流年有根或可计算触发时 abstain；高风险时间窗不升格为铁断。

- [ ] **Step 2: 运行失败测试**

Run: `python -m pytest tests/claims/test_gao_timing.py -q`

Expected: FAIL because `engine.v5.gao_timing` is missing。

- [ ] **Step 3: 实现高派 timing enhancer**

只实现可由输入事实验证的流年有根/串宫触发，不以神煞名称单独构造事件概率。

- [ ] **Step 4: 运行全部 Claim 回归**

Run: `python -m pytest tests/claims -q`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add engine/v5/gao_timing.py engine/v5/gao_runner.py engine/claims/runner_registry.py tests/claims/test_gao_timing.py
git commit -m "feat: add second batch gao timing enhancer"
```

### Task 13: 从 run/decision 结构渲染并跑报告（月 5—6）

**Files:**
- Modify: `engine/v5/report_view.py`
- Modify: `tools/render_report_v6.py`
- Modify: `tools/output_linter.py`
- Test: `tests/v5/test_report_view.py`
- Test: `tests/test_output_linter.py`

**Interfaces:**
- Consumes: frozen run、decision run、prediction ledger、结构化 comparison。
- Produces: 命理师统一报告 ViewModel；不泄露 claim/statement/学习内部 ID，不从 Markdown 反推状态。

- [ ] **Step 1: 写报告出口失败测试**

覆盖六域主要事项、来源于结构化上游的判断、少数派/风险提示、时间窗；负向断言报告不含内部 ID、capability snapshot 索引、Agent 工作记录。

- [ ] **Step 2: 运行失败测试**

Run: `python -m pytest tests/v5/test_report_view.py tests/test_output_linter.py -q`

Expected: FAIL，直到新增结构化字段进入 ViewModel 和 linter。

- [ ] **Step 3: 最小渲染与 lint**

只渲染已有结构化字段；若某任务无证据，显示“证据不足/本派克制”，不得由模板补写命理结论。

- [ ] **Step 4: 运行报告回归**

Run: `python -m pytest tests/v5/test_report_view.py tests/test_output_linter.py tests/test_render_report_v6.py -q`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add engine/v5/report_view.py tools/render_report_v6.py tools/output_linter.py tests/v5/test_report_view.py tests/test_output_linter.py
git commit -m "feat: render staged decisions without internal ids"
```

### Task 14: 六个月生产候选验收（月 6）

**Files:**
- Create: `META/six-month-platform-gate-YYYY-MM-DD.md`
- Create: `META/six-month-platform-gate-YYYY-MM-DD.json`
- Modify: `META/project-state.json` only if the evidence-backed phase status changes
- Modify: `STATUS.md` only for stable route links, without volatile counts

**Interfaces:**
- Consumes: Claim 覆盖报告、能力基线、L1 留出报告、并跑 diff、L6/L9 审计、高风险指标、E3/E4 前瞻证据。
- Produces: 最终 GO/HOLD/STOP 判定与下一不可逆决策；GO 也只形成切换提案，不在验收文档中偷偷切入口。

- [ ] **Step 1: 运行完整验证**

Run: `python -m pytest tests -q`

Expected: PASS；允许项目既有显式 skip，但不得有 failure/error。

- [ ] **Step 2: 运行工具与规则状态检查**

Run: `python tools/tool_registry.py --check && python tools/rule_status_scan.py --check`

Expected: 两个命令 exit 0。

- [ ] **Step 3: 运行仓库文本与 diff 检查**

Run: `git diff --check`

Expected: no output, exit 0。

- [ ] **Step 4: 写门禁制品**

JSON 固定字段：`phase`、`status`、`evidence_artifacts`、`accepted_hypotheses`、`rejected_hypotheses`、`known_risks`、`next_irreversible_decision`、`updated_at`。Markdown 必须明确：是否满足六域覆盖、独立效用、校准、高风险、审计链、复现、反馈归因和前瞻证据。

- [ ] **Step 5: 根据证据选择结果**

GO：提出将新流程设为默认、旧流程保留显式 fallback 的独立契约变更；HOLD：保持 staged 并指定缺失证据；STOP：冻结新路由更新并回退静态先验。不得因已到第 6 月自动判 GO。

- [ ] **Step 6: 提交验收制品**

```bash
git add META/six-month-platform-gate-*.md META/six-month-platform-gate-*.json META/project-state.json STATUS.md
git commit -m "eval: record six month platform gate"
```

## 4. 阶段证明物与证伪路径

### 第一证明点

月 2 结束时，同一冻结命盘与同一任务目录能由至少两个目标知识来源独立生成 task-specific Claim，且每条 Claim 具有稳定 ID、可解析证据、结构化 falsifier 和合法三态；任派与段派可独立生成四域 timing 候选。这个证明点成立，才说明后续能力评估测的是系统而不是人工写命题者。

### 首要证伪器

月 4 的严格留出对照。如果在真实竞争样本达到门槛后，learned 路由仍未改变选择、独立效用没有改善、校准或高风险假阳性恶化，则 H2 条件化路由增益假设被证伪或需重构。此时回退 static，保留 Claim/L6/L9 中已独立证明有价值的部分，不为保住“大平台”叙事强行切换。

## 5. 自检清单

- [ ] 本计划覆盖路径、覆盖深度、财富/事业优先、任+段 timing 双主力和高派第二批。
- [ ] 能力矩阵与已批准任务分配均有对应实施任务。
- [ ] 每个月都有可审查交付物、GO/HOLD/STOP 与回退。
- [ ] 每个代码任务都有精确文件、接口、失败测试、验证命令和提交边界。
- [ ] 未把历史 feedback-first 案例冒充 prospective。
- [ ] 未硬编码当前 N_eff、规则数量、git HEAD 或 review 清单。
- [ ] 未安排默认切换、旧引擎删除或静态权重回灌。
- [ ] 报告层只消费结构化 run/decision，且禁显内部 ID。
