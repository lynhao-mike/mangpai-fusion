# 升级指导 04 · L1 可学习流派适用性路由与能力回流飞轮

> 文档类型：实施指导（供强模型执行）
> 服从：[`docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md`](../../docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md)
> 上游依赖：[`01-chart-feature-vector.md`](01-chart-feature-vector.md)、[`02-l2-claim-engine.md`](02-l2-claim-engine.md)、[`03-evaluation-data-foundation.md`](03-evaluation-data-foundation.md)
> 定位：**这是整个升级路线的胜负手**。本单元第一次让系统用数据证明"学会了什么八字该用什么法"。

---

## 1. 为什么这是胜负手

核心设计宪法 §2.2 把平台目标定义为：

> 在某类命盘、某类任务、某种时间尺度、证据完整度达到某水平时，识别哪些方法能够提供经过校准且具有增量价值的判断，并让不适用的方法主动退出决策。

这句话的工程实现就落在 L1。前三个升级单元（特征向量、命题引擎、评估数据）都是**为本单元准备的燃料**：

- 01 提供 `命局特征向量` → 分型的钥匙
- 02 提供 `引擎生成的命题` → 可信的评估对象
- 03 提供 `真实标注 + 能力后验` → 学习信号来源

本单元把这三者接成**闭环飞轮**：

```text
评估框架产出六维能力后验（03 已建成）
  → L9 转成"命局特征 → 流派权重"更新（本单元 + 06）
  → L1 下次分型时消费更新后的权重（本单元核心）
  → 产生新预测 → 新反馈 → 新能力后验
  → 飞轮转动，系统越来越懂"什么八字用什么法"
```

**目前这条回流通道完全断开**：[`engine/decision/l1_school_router.py`](../../engine/decision/l1_school_router.py) 的 `SCHOOL_PROFILES` 是硬编码字符串表，`_apply_learned_prior()` 只消费一个全局命中率标量，与评估框架产出的六维 `CapabilityPosterior` 没有任何连接。

---

## 2. As-Built 现状（必须先读）

先阅读并确认以下现状，不要假设：

1. [`engine/decision/l1_school_router.py`](../../engine/decision/l1_school_router.py)
   - `SCHOOL_PROFILES: dict` 是硬编码"流派 → {领域列表, 理由文字}"。
   - `_apply_learned_prior(school, role, score, learned_prior)` 只接收 `dict[str, tuple[float, int]]`（全局命中率 + 样本数），阈值 `_PRIOR_MIN_SAMPLE=5`、`_PRIOR_LOW_HIT_RATE=0.35`、`_PRIOR_SCORE_PENALTY=0.2`。
   - `_ROLE_LADDER = ("lead", "co_lead", "evidence_only", "abstain")` 降级阶梯已存在，可复用。
   - `_chart_signals()` 已从四柱派生 `complete/skewed/missing_count/has_chong` — 这是 L1 现有的"准特征"，本单元要把它替换为 01 的完整特征向量。

2. [`engine/evaluation/capability.py`](../../engine/evaluation/capability.py)
   - `build_capability_posteriors()` 已产出六维 `CapabilityPosterior`，身份维度为 `(school_id, task_id, chart_prototype_id, claim_type, time_horizon, evidence_completeness_band)`。
   - 字段含 `posterior_mean / credible_interval / n_eff / incremental_gain / evidence_grade`。

3. [`engine/evaluation/models.py`](../../engine/evaluation/models.py)
   - `CapabilityPosterior` 是冻结 dataclass，已有 JSON 往返。**本单元只读它，不改它**。

4. 现状缺口：`chart_prototype_id` 目前只在评估框架内部作为字符串标签存在；01 单元产出的命局特征向量与它没有映射函数。**本单元必须建立 `特征向量 → chart_prototype_id` 的稳定映射**，否则能力后验查不回来。

---

## 3. 本单元目标与非目标

### 3.1 目标

1. 建立 `命局特征向量 → chart_prototype_id` 的确定性映射（10–20 个稳定原型，宪法附录与路线 §8.1 已限定规模）。
2. 建立 `CapabilityRegistry`：从评估框架产出的能力后验加载，供 L1 查询。
3. 重构 L1 路由：从"静态领域表 + 全局命中率降级"改为"条件化能力后验 + 不确定性惩罚"驱动的路由计划。
4. 打通回流：L1 消费 03 单元产出的真实能力后验，并留出 06 单元写入更新的接口。
5. **用留出盲测集证明**：学过之后 L1 分型命中率 > 静态表基线（这是本单元唯一的 GO 硬门槛）。

### 3.2 非目标（明确不做）

- 不做在线学习服务；能力后验以离线快照文件形式加载。
- 不改 `CapabilityPosterior` 契约。
- 不实现 L6/L9 的完整重构（各自独立单元）。
- 不切换生产入口；新路由与旧 `SCHOOL_PROFILES` 并行，通过开关选择。
- 不创建数百个专家文本原型；原型必须由 Fact/特征向量定义。

---

## 4. 接口契约

### 4.1 命盘原型映射

新增 `engine/decision/chart_prototype.py`：

```python
def classify_prototype(feature_vector: ChartFeatureVector) -> PrototypeAssignment:
    """把命局特征向量映射到稳定原型 ID。

    - 返回主原型 ID + 置信度 + 命中的判定条件列表。
    - 原型集合固定为 10–20 个，全部由可计算特征定义。
    - 无法归入任何原型时返回 prototype_id="prototype-unclassified"，
      不得强行塞入最近原型（那会污染能力后验分母）。
    - 纯函数，确定性：同一 feature_vector 必得同一结果。
    """
```

`PrototypeAssignment` 冻结 dataclass 最小字段：

```text
prototype_id: str
confidence: float          # 0-1，多原型边界时的归属确定度
matched_conditions: tuple[str, ...]
alternative_ids: tuple[str, ...]   # 边界情况下的次选原型，供不确定性传播
```

原型定义应外置为 `mapping/chart-prototype-registry-v1.yaml`（数据，不是硬编码），每个原型至少含：

```text
prototype_id
label
required_features        # 特征向量上的可计算判定条件
excluded_features
priority                 # 多原型命中时的裁决顺序
notes
```

候选原型维度（路线 §8.1，起步 10–20 个）：身强/身弱/从格候选、气势集中/多方混战、做功链清晰/不清晰、宫位冲合明显/弱、官杀混杂、财官印食关键组合、寒暖燥湿极端/中和、原局信号强/依赖岁运、神煞与结构同向/冲突。

### 4.2 能力注册表

新增 `engine/decision/capability_registry.py`：

```python
class CapabilityRegistry:
    """只读能力后验查询层。从评估框架产出的快照加载。"""

    @classmethod
    def from_snapshot(cls, path: str | Path) -> "CapabilityRegistry":
        """加载 03 单元产出的 CapabilityPosterior 快照 JSON。"""

    def query(
        self,
        *,
        school_id: str,
        task_id: str,
        chart_prototype_id: str,
        claim_type: str,
        time_horizon: str,
        evidence_completeness_band: str,
    ) -> CapabilityQuery:
        """六维精确查询；查不到时按层级 Bayesian 收缩向上回退。"""
```

`CapabilityQuery` 返回：

```text
posterior_mean: float
credible_interval: tuple[float, float]
n_eff: float
incremental_gain: float
evidence_grade: str
shrink_level: str          # "exact" | "prototype_backoff" | "task_backoff" | "domain_prior"
resolved_identity: dict    # 实际命中的维度，供审计
```

**层级收缩（宪法 §6.5、路线 §8.2）**：精确六维查不到（或 `n_eff` 过低）时，依次向上回退：
`六维 → 流派×任务×原型 → 流派×任务 → 流派×领域 → 全局先验`。每次回退必须在 `shrink_level` 标注，并让可信区间变宽。禁止小样本格子直接独立掌权。

### 4.3 路由决策

重构后的 L1 入口（保留旧函数名兼容，新增路由路径）：

```python
def build_route_plan(
    *,
    feature_vector: ChartFeatureVector,
    tasks: list[Task],
    evidence_completeness_band: str,
    registry: CapabilityRegistry,
    risk_config: RoutingRiskConfig,
) -> RoutePlan:
    """基于条件化能力后验产出路由计划。"""
```

`RoutePlan` 必须满足宪法 §7.2：

```text
primary_schools: list[str]        # 1-2 个主力
counter_school: str | None        # 至多 1 个反证流派
abstain_candidates: list[str]
unsupported_schools: list[str]
route_rationale: str
capability_snapshot_id: str
per_task_routes: dict[str, TaskRoute]   # 每个 task 独立路由
```

路由打分（路线 §8.3）：

```text
route_score
  = expected_utility
  - risk_factor × posterior_uncertainty
  + complementarity_gain
```

其中 `posterior_uncertainty` 来自可信区间宽度，`complementarity_gain` 来自反证流派与主力流派的能力互补。**必须惩罚不确定性，不得只比 `posterior_mean`**（宪法 §6.5）。

**关键护栏**：若所有流派在某 task 上均达不到最低证据要求，`per_task_routes[task]` 必须输出"证据不足"，不得依赖静态权重强行选赢家（宪法 §7.2）。

---

## 5. 任务分解

按 TDD，每步先写测试再实现。

### T1：命盘原型映射
- 建 `mapping/chart-prototype-registry-v1.yaml`（10–20 原型，全部特征可计算）。
- 建 `classify_prototype()` + `PrototypeAssignment`。
- 测试：每个原型至少 1 个正例命中、1 个反例不命中；边界盘产出 `alternative_ids`；无法分类返回 `prototype-unclassified`；确定性（同输入同输出）。

### T2：能力注册表 + 层级收缩
- 建 `CapabilityRegistry.from_snapshot()` + `query()`。
- 实现五级收缩回退。
- 测试：精确命中；低 `n_eff` 触发收缩且区间变宽；查不到回退到领域先验；`shrink_level` 标注正确；快照缺失字段时明确报错不静默。

### T3：路由决策核心
- 建 `build_route_plan()` + `RoutePlan` + `TaskRoute`。
- 实现 `route_score` 三项打分 + 不确定性惩罚 + 证据不足护栏。
- 测试：高能力低不确定性流派入选 primary；高均值但宽区间流派被惩罚降位；反证流派按互补性入选 counter；全员证据不足时输出"证据不足"而非强选。

### T4：与旧路由并行 + 开关
- 保留 `SCHOOL_PROFILES` 路径；新增 `routing_mode` 开关（`static` | `learned`）。
- 默认仍 `static`，`learned` 显式开启。
- 测试：开关切换不影响旧路径行为；`learned` 路径产出合法 `RoutePlan`。

### T5：回流验证（GO 门槛）
- 建留出盲测集：一部分标注案例**不参与**能力后验训练，仅用于验证。
- 指标：`learned` 路由在留出集上的分型命中率 / 决策效用 vs `static` 基线。
- 产出对照报告：`reports/l1-routing-holdout-comparison.md`。

---

## 6. GO / HOLD / STOP 门槛

对应路线 §8.5 与 H2 假设。

### GO（全部满足）
1. `learned` 路由在**留出盲测集**上决策效用 ≥ `static` 基线。
2. 校准误差不恶化。
3. 高风险任务假阳性不增加。
4. 至少部分"任务 × 原型"格子显示稳定增量。
5. 路由理由可解释、可复现（`capability_snapshot_id` 可追溯）。

### HOLD
- 留出集样本不足、可信区间过宽，方向未被证伪但证据不足。
- 原型分类大量落入 `prototype-unclassified`（说明原型集需迭代）。

### STOP / REFRAME（对应 H2 证伪）
- 条件化路由相对固定权重**无稳定增益**，或增益小于复杂度和方差成本。
- 只在训练集提升、留出集不提升 → 过拟合，回退固定先验并简化路由模型（路线 §12）。

**红线**：只提高训练集表现必须 STOP 查过拟合（路线 §8.5）。不得删除留出集异常样本来凑 GO。

---

## 7. 泄漏与治理红线

- 训练能力后验的案例与留出验证案例**严格隔离**，同一命主/多版本报告/衍生案例不得跨集（路线 §11.1）。
- L1 路由在预测冻结前不得读取真实反馈或能力后验中混入的答案信息（宪法 §3.6）。
- 能力快照必须带 `evidence_grade`；E0/E1 只能作冷启动弱先验，不能单独支撑生产路由权重（宪法 §6.3、§3.7）。
- 路由权重大幅变化进入人工裁决（宪法 §8.4）。

---

## 8. 交付物清单

```text
mapping/chart-prototype-registry-v1.yaml
engine/decision/chart_prototype.py
engine/decision/capability_registry.py
engine/decision/l1_school_router.py           # 重构，保留旧路径
tests/decision/test_chart_prototype.py
tests/decision/test_capability_registry.py
tests/decision/test_learnable_routing.py
tests/decision/test_routing_holdout.py
reports/l1-routing-holdout-comparison.md       # GO 证据
```

## 9. 完成定义

- 全部测试通过，`learned` 路由产出合法可追溯 `RoutePlan`。
- 留出集对照报告给出明确 GO / HOLD / STOP 判定与证据。
- 未改 `CapabilityPosterior` 契约，未切换生产入口，未污染训练/验证隔离。
- 若判定 GO：本单元证明"系统学会了分型"，升级路线核心假设 H2 成立，可进入 L6/L9 内核重构。
