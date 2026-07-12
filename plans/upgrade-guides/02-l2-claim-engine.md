# 升级指导 02 · L2 命题引擎化（消除手写命题）

> 日期：2026-07-12
> 文档类型：升级方向详细实施指导
> 服从文档：[`docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md`](../../docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md)
> 上游依赖：[`plans/upgrade-guides/01-chart-feature-vector.md`](01-chart-feature-vector.md)
> 主索引：[`plans/upgrade-guides/00-overview-and-sequencing.md`](00-overview-and-sequencing.md)

## 0. 给执行模型的定向说明

你将实现整个升级计划里**最能决定成败真实性**的一项：让每派命题由引擎从命局事实推导，而不是人工写进 JSON。

在动手前必须理解一个陷阱：**如果命题仍由人写，那么后续所有准确率评估、能力后验、路由学习，评估的都是"写命题的人"的水平，不是"系统"的水平。** 这会让整个学习闭环在一个虚假基线上运转。因此本单元的验收核心不是"命题写得好不好"，而是"命题是不是引擎生成的、是否带可追溯证据链、是否能在同一命盘上稳定复现"。

不要试图一次实现五派完整命理。按本文的范围约束，先做**两派 × 各自最擅长的少量任务**，把"引擎生成 + 证据链 + 三态 + 盲测隔离"这条管道打通并锁死。

## 1. 目标与非目标

### 1.1 目标

1. 定义统一的 `Claim` 生成契约：每派 runner 接收 `Chart` + `ChartFeatureVector` + `Task`，输出 `list[Claim]`，每条 `Claim` 必须挂 `evidence`（引用具体 Fact / feature）与 `falsifier`。
2. 至少两派 runner 从"原文触发 / 人工 JSON"改为"特征推导"：
   - **子平**：扩展现有 [`engine/v5/ziping_runner.py`](../../engine/v5/ziping_runner.py) 的旺衰 + 格局两层，产出结构类命题（structure_claim）。
   - **任派**：以应期任务为切口，从大运流年触发 Fact 推导事件时间窗命题（event_claim + timing）。
3. 每条生产命题具备可执行判别测试：正例触发、反例不触发、边界 `abstain`。
4. 命题生成全程不接触反馈、真实经历、旧报告结论（盲测隔离）。

### 1.2 非目标

- ❌ 不实现五派全量命理断语。
- ❌ 不改报告模板与出口（L7 保持不动）。
- ❌ 不实现仲裁改造（L6 属指导 05）。
- ❌ 不做规则自动抽取工具链（原文→规则的批量抽取是独立后续工作）。
- ❌ 不触碰 `engine/evaluation/`（它是验收基座，只被调用不被改动）。

## 2. 现状（as-built 证据）

| 现象 | 位置 | 问题 |
|---|---|---|
| 学派命题人工手写 | `cases/*/…school-claims.json`、`reports/*.v5.json` 中 `claim_id: "v5-034-ziping-structure-001"` | 命题是人写的整段话术，非引擎推导 |
| 子平 runner 仅两层 | [`engine/v5/ziping_runner.py`](../../engine/v5/ziping_runner.py) | 只有月令旺衰 + 主要格局，注释自述"最小推导" |
| 三盲派靠原文触发 | [`engine/v5/runner.py`](../../engine/v5/runner.py) `BLIND_SCHOOL_INDEX_FILES` | 从 `theory/*/index.yaml` 触发原文规则，claim 字段为整段古籍 |
| 命题无 falsifier | v5.json `falsifiable` 字段偶有，但非强制、非结构化 | 无法进入盲测评分 |

## 3. 接口契约（必须遵守）

### 3.1 Claim 生成函数签名

每派 runner 必须暴露一个纯函数（无 IO、无反馈访问）：

```python
def generate_claims(
    chart: Chart,
    features: ChartFeatureVector,   # 来自指导 01
    task: Task,                     # 来自 mapping/school-capability-task-catalog-v1.yaml
) -> list[Claim]:
    """从命局事实与特征推导本派对该任务的命题。

    契约：
    - 纯函数：相同 (chart, features, task) 必产生相同 claims（含稳定 claim_id）。
    - 三态：无法形成命题时返回 []（abstain）或抛出 TaskUnsupported（unsupported）。
    - 禁止读取：反馈、真实经历、旧报告结论、其他派中间命题。
    - 每条 claim 必须带非空 evidence 且 evidence 只引用 chart/features 中真实存在的节点。
    """
```

### 3.2 Claim 对象最小字段

复用核心宪法 §5.7 的 `Claim` 定义，落地为：

```python
@dataclass(frozen=True)
class Claim:
    claim_id: str            # 稳定哈希：hash(school|task|chart_signature|rule_id)
    school_id: str
    task_id: str
    claim_type: str          # structure_claim | event_claim | timing_claim | portrait_claim
    stance: str              # support | oppose
    statement: str           # 结构化生成，非自由手写
    evidence: list[Evidence] # 非空；每项引用 fact_ref / feature_ref
    falsifier: str           # 什么现实结果能证伪本命题
    time_window: Optional[TimeWindow]  # event/timing 类必填
    confidence_basis: str    # 证据强度来源说明，非拍脑袋分数
    applicability_snapshot: dict  # 生成时的 feature 快照，供事后追溯
```

### 3.3 Evidence 引用约束

```python
@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    fact_refs: list[str]     # 必须能在 Chart/Fact 中解析到
    feature_refs: list[str]  # 必须能在 ChartFeatureVector 中解析到
    rule_id: str             # 触发本命题的 ExecutableRule
    text: str                # 人类可读依据（可含原文引用）
```

**硬约束**：`fact_refs` 和 `feature_refs` 至少一个非空，且引用的键必须真实存在——生成后要有一个 validator 校验"证据不能指向不存在的事实"。这是防止"编证据"的关键门禁。

## 4. 任务分解（TDD 逐步）

### Task 2.1：Claim / Evidence 领域对象与校验器

- 在 `engine/v5/domain.py` 或新建 `engine/claims/` 定义上述 dataclass。
- 实现 `validate_claim_evidence(claim, chart, features)`：证据引用必须可解析，否则抛错。
- 实现 `stable_claim_id(...)`：同输入同 ID。
- 测试：证据指向不存在节点被拒绝；claim_id 稳定；三态合法性。

### Task 2.2：子平结构命题生成

- 扩展 [`engine/v5/ziping_runner.py`](../../engine/v5/ziping_runner.py)：基于指导 01 的 feature（旺衰带、格局、十神分布）生成 structure_claim。
- 每条命题挂 feature_ref（如 `strength.band`、`geju.primary`）。
- 覆盖至少：身强/身弱结构主线、格局成立/破格、食伤/官杀结构关系。
- 无法判定时 `abstain`（返回空），不硬凑。
- 测试：正例（清晰身弱盘出身弱结构命题）、反例（中和盘不出极端命题）、边界（残缺盘 abstain）。

### Task 2.3：任派应期事件命题生成

- 新建 `engine/v5/ren_runner.py`（或等价）：从大运流年触发 Fact + feature 推导 event_claim + timing。
- 时间窗必须来自可计算触发（岁运引动冲合），不得来自固定文案。
- `falsifier` 必须写明"该时间窗内未发生该类事件即证伪"。
- 测试：触发年产出时间窗命题；无触发则 abstain；时间窗可复现。

### Task 2.4：盲测隔离审计

- 加一个静态测试/审计：扫描两派 runner 的调用图，断言不 import 任何反馈/报告读取模块。
- 断言 `generate_claims` 的输入 DTO 不含反馈字段。
- 与 `engine/evaluation/freeze.py` 的冻结契约对接：生成的 claim 能被冻结为 `BlindSchoolOutput`。

### Task 2.5：与评估框架对接验证

- 写一个 fixture 案例，跑通"两派 generate_claims → 冻结 → 揭示标签 → 评分"。
- 证明引擎命题能进入 `engine/evaluation/` 的盲测评分链，产出非空 score。

## 5. 验收标准

| 门禁 | 判定 |
|---|---|
| 引擎生成率 | 两派目标任务的命题 100% 由 `generate_claims` 产出，零人工 JSON |
| 证据完整性 | 每条命题 evidence 非空且引用全部可解析（validator 通过） |
| 三态合法 | claim / abstain / unsupported 三态均有测试覆盖 |
| 可复现 | 同一 (chart, features, task) 两次运行 claim_id 与内容完全一致 |
| 盲测隔离 | 静态审计证明 runner 不接触反馈/报告结论 |
| 评估对接 | 引擎命题能进入 evaluation 盲测链并得到评分 |
| 判别测试 | 每条生产命题有正例/反例/边界例 |

## 6. STOP / REFRAME 条件

- 若大量关键命理判断无法从 feature 形式化推导（只能靠自由文本），**收缩范围**：先只做子平结构类命题，任派应期降级为下一单元。
- 若引擎命题在评估集上系统性劣于人工命题且差距无法通过 feature 扩展弥补，回到指导 01 补特征，不要在 L2 硬堆规则。

## 7. 对下游的交付物

- 稳定的 `generate_claims` 契约 → 指导 04 的 L1 路由按此调度各派。
- 带证据链的 Claim → 指导 05 的 L6 分段仲裁消费。
- 引擎命题进入评估链 → 指导 03 的真实标注得以评估"系统"而非"人"。

## 8. 风险

| 风险 | 缓解 |
|---|---|
| 把手写话术挪进代码字符串模板，伪装成"引擎生成" | validator 强制 evidence 引用真实 feature；审查生成逻辑是否真的读了 feature 分支 |
| 时间窗命题用固定文案冒充推导 | timing 必须来自岁运触发 Fact，测试要求换命盘时间窗随之改变 |
| 命题爆炸（每盘上百条） | 每派每任务设命题数上限；低证据命题 abstain 而非输出 |
