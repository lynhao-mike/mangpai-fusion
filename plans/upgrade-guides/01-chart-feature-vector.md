# 升级指导 01 · 命局特征向量层（ChartFeatureVector）

> 文档类型：可执行实施指导（供强模型独立执行）
> 从属：[`docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md`](../../docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md)
> 路线：[`plans/bazi-intelligence-platform-roadmap.md`](../bazi-intelligence-platform-roadmap.md)
> 总览：[`plans/upgrade-guides/00-overview-and-sequencing.md`](00-overview-and-sequencing.md)
> 依赖：无（这是新架构的脊椎基础设施，必须最先落地）
> 被依赖：01 是 04（L1 路由）、05（L6 仲裁）、06（L9 学习）的前置条件；也是 ChartPrototype 的构造基础

---

## 1. 为什么先做这一层

核心设计宪法 §5.5 定义了 `ChartPrototype`（命盘结构原型），并明确要求"原型必须由可计算 Fact 组成，不得仅依赖专家自由文本标签"。路线 H5（局部专长假设）、Phase 3（方法适用性路由）都建立在"命盘可被结构化分型"之上。

但当前系统没有一个**共享的、可计算的、版本化的命局特征表示**。各处特征散落：

- [`engine/decision/l1_school_router.py`](../../engine/decision/l1_school_router.py) 里的 `_chart_signals()` 临时从四柱算 `complete / skewed / missing_count / has_chong`，只服务路由，不复用；
- [`engine/energy/`](../../engine/energy/) 内部有旺衰判断，但耦合在段派逻辑里；
- [`engine/v5/ziping_runner.py`](../../engine/v5/ziping_runner.py) 自己算月令旺衰和格局，与 energy 各算各的。

**结果**：L1 靠它分型、L6 靠它加权、L9 靠它做条件化学习——但这三层各自看到的"命盘特征"口径不一致，无法拼成飞轮。

**本层目标**：建立**唯一的、确定性的、版本化的** `ChartFeatureVector`，作为 L0 事实层的标准派生产物，供所有下游层共享。这是宪法 §4.1 输入事实层的直接扩展。

---

## 2. 范围边界（必须严格遵守）

**本层只做**：从 `Chart` 确定性计算结构化特征，输出不可变的 `ChartFeatureVector`。

**本层禁止**：
- 禁止产生任何解释性结论（不谈事业/财富/婚姻）——违反宪法 §4.1 边界；
- 禁止读取反馈、案例结论、报告文本；
- 禁止引入流派立场（这是中立事实层，不是任何一派的旺衰观点）；
- 禁止硬编码"某特征→某流派"的映射（那是 L1 的职责，见指导 04）。

**与旺衰争议的处理**：不同流派对"身强身弱"判法不同。本层**不裁定唯一旺衰**，而是输出**多口径的可计算信号**（例如：月令得令度、通根数、生扶/克泄抽干支计数、五行能量分布），把"如何据此判旺衰"留给各派 runner（指导 02）和结构审查层。本层只提供**中立的可计算底座**。

---

## 3. 接口契约

### 3.1 模块位置

```
engine/features/__init__.py
engine/features/chart_feature_vector.py      # 主实现
engine/features/types.py                      # ChartFeatureVector 数据类
tests/features/test_chart_feature_vector.py   # 测试
```

放在 `engine/features/` 而非 `engine/decision/` 或 `engine/v5/`，因为它是全系统共享的 L0 派生层，不属于任何单一决策路径。

### 3.2 输入

复用现有 `Chart` / `ParsedInput` 对象，不新建命盘解析。参考 [`engine/predicates/types.py`](../../engine/predicates/types.py) 的 `ParsedInput` 与 [`engine/decision/models.py`](../../engine/decision/models.py) 的 `ChartFactLedger`。

```python
def build_chart_feature_vector(
    chart: ChartFactLedger,   # 或复用 ParsedInput，二选一，保持与既有解析一致
    *,
    schema_version: str = "cfv-v1",
) -> ChartFeatureVector: ...
```

### 3.3 输出数据类（冻结 dataclass）

```python
@dataclass(frozen=True)
class ChartFeatureVector:
    # ── 身份与版本 ──
    schema_version: str            # "cfv-v1"
    chart_id: str                  # 稳定哈希（四柱+性别+历法派生）

    # ── 五行能量分布（中立口径）──
    element_counts: Mapping[str, int]      # {木,火,土,金,水} → 天干地支本气计数
    element_energy: Mapping[str, float]    # 含藏干加权的能量分布，和为 1.0
    dominant_element: str
    missing_elements: tuple[str, ...]
    element_concentration: float           # 最大元素占比（0..1，衡量偏枯）

    # ── 日主与月令（多口径，不裁定唯一旺衰）──
    day_master: str                        # 日干
    day_master_element: str
    month_branch: str
    month_lord: str                        # 月令司令主气天干
    rooted_count: int                      # 日主通根数（年月日时地支藏干含日主同类）
    supporting_count: int                  # 生扶日主的干支计数（印比）
    draining_count: int                    # 克泄耗日主的干支计数（食伤财官杀）
    monthly_command_favorable: bool        # 月令是否生扶日主（中立计算，非旺衰裁定）

    # ── 十神结构 ──
    ten_god_counts: Mapping[str, int]      # 十神在全局的出现计数
    has_official: bool                     # 正官/七杀出现
    has_wealth: bool
    has_output: bool                       # 食神/伤官
    has_resource: bool                     # 正印/偏印
    mixed_official_kill: bool              # 官杀混杂

    # ── 地支关系 ──
    chong_pairs: tuple[tuple[str, str], ...]   # 相冲对
    he_pairs: tuple[tuple[str, str], ...]      # 六合对
    xing_hai_pairs: tuple[tuple[str, str], ...]
    branch_conflict_intensity: float           # 冲刑害强度（0..1）

    # ── 寒暖燥湿（滴天髓/调候相关，中立计算）──
    cold_warm_axis: float                  # -1（极寒）..+1（极暖）
    dry_wet_axis: float                    # -1（极湿）..+1（极燥）
    climate_extreme: bool                  # 是否寒暖燥湿极端

    # ── 输入完整度 ──
    has_hour_pillar: bool
    evidence_completeness: str             # "full" | "no_hour" | "partial"
```

所有字段必须**确定性可计算**：同一 `Chart` + 同一 `schema_version` 必产生同一 `ChartFeatureVector`（含相同哈希）。禁止随机、时间依赖、外部 IO。

### 3.4 JSON 往返

必须提供 `to_dict()` / `from_dict()`，供冻结快照（宪法 §8.5）和评估框架消费。tuple 字段 JSON 化为 list，恢复时转回 tuple——参考 [`engine/evaluation/models.py`](../../engine/evaluation/models.py) 已建立的 `PersistedContract` 往返模式，保持全仓库一致。

---

## 4. 任务分解（TDD，逐步提交）

### Task 1：数据类与 JSON 往返
- 定义 `ChartFeatureVector` 冻结 dataclass；
- `__post_init__` 校验：`element_energy` 和约为 1.0（容差 1e-9）、`evidence_completeness` 三态枚举、轴值在 `[-1, 1]`；
- `to_dict()` / `from_dict()` 严格往返，非法状态构造与恢复均抛 `ValueError`；
- 测试：往返一致、非法值拒绝、哈希稳定。

### Task 2：五行能量与十神计算
- 复用 [`engine/predicates/wuxing.py`](../../engine/predicates/wuxing.py)、[`engine/predicates/ganzhi.py`](../../engine/predicates/ganzhi.py) 已有谓词，**不重新实现**干支→五行、藏干表；
- `element_counts` 用本气，`element_energy` 用含藏干加权（藏干权重沿用 [`engine/predicates/types.py`](../../engine/predicates/types.py) 的 `ZHI_CANGGAN_TABLE` 若已有权重，否则用主气 0.6/中气 0.3/余气 0.1 并在文档注明来源）；
- 十神计算复用 [`engine/v5/ziping_runner.py`](../../engine/v5/ziping_runner.py) 已有的 `_shishen()` 逻辑，抽取为共享函数避免两处漂移；
- 测试：已知命盘的元素分布、十神计数正确（取 2-3 个 `cases/` 真实盘做金标准）。

### Task 3：月令旺衰多口径信号
- `rooted_count / supporting_count / draining_count / monthly_command_favorable` 全部中立计算；
- **关键**：不输出"身强/身弱"单一结论，只输出计数与布尔；
- 测试：从格盘、身弱盘、中和盘的信号区分明显。

### Task 4：地支关系与寒暖燥湿
- 冲合刑害复用 [`engine/predicates/relations.py`](../../engine/predicates/relations.py)；
- 寒暖燥湿轴：按月令 + 五行分布计算（子丑亥极寒、巳午未极暖等），系数在模块常量中命名并注释来源；
- 测试：极端气候盘 `climate_extreme=True`，中和盘 `False`。

### Task 5：与既有路由信号对齐验证
- 写一个对照测试：`ChartFeatureVector` 的 `chong_pairs / element_concentration` 应能覆盖 [`engine/decision/l1_school_router.py`](../../engine/decision/l1_school_router.py) 现有 `_chart_signals()` 的 `has_chong / skewed`；
- 目的：证明新特征层是旧临时信号的超集，为指导 04 替换旧信号铺路；
- **本指导不修改 l1_school_router**，只证明可替代性。替换在指导 04 执行。

---

## 5. 验收标准

- [ ] `ChartFeatureVector` 所有字段确定性可计算，同盘同版本哈希稳定；
- [ ] JSON 往返无损，非法状态拒绝；
- [ ] 复用既有 predicates，无重复实现干支/五行/藏干/冲合表；
- [ ] `_shishen()` 抽取为共享函数，`ziping_runner` 与特征层共用同一实现；
- [ ] 不输出任何解释性结论，不裁定唯一旺衰，不含流派立场；
- [ ] 至少 3 个真实案例盘作为金标准测试；
- [ ] 证明可覆盖 `l1_school_router._chart_signals()` 现有信号；
- [ ] 全部新测试通过，且不破坏既有 `tests/` 回归。

---

## 6. 风险与克制

- **旺衰口径之争**：这是八字最大分歧点。本层的克制设计（只给计数、不给结论）是刻意的——一旦本层裁定唯一旺衰，就侵犯了各派 runner 的独立命题权（宪法 §4.3）。审查时如发现本层输出了"身强/身弱/从格"这类结论，必须打回。
- **藏干权重来源**：若 `ZHI_CANGGAN_TABLE` 没有权重，新引入的权重系数必须在文档明确标注是工程默认值（非某流派铁律），并留待 Phase 2 数据校准。
- **不要过度设计**：cfv-v1 只需覆盖 L1/L6/L9 当前需要的特征。不要一次性塞入几十个学术特征。宪法 §12 与 ponytail 原则都要求最小可用。新增特征应由下游真实需求驱动。

---

## 7. 完成后回填

完成后在路线 [`plans/bazi-intelligence-platform-roadmap.md`](../bazi-intelligence-platform-roadmap.md) §16 追加阶段状态，记录 `cfv-v1` schema 版本与覆盖特征清单，并更新总览 [`00-overview-and-sequencing.md`](00-overview-and-sequencing.md) 的依赖图状态。
