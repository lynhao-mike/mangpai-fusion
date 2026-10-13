# 职业路径状态机 v2：关系图双层时序裁决

> 状态：staged contract
>
> v2 是对 [`13-career-path-state-machine-v1.md`](13-career-path-state-machine-v1.md) 的向后兼容解释与实现契约，不改写、不废除 v1 已冻结的四层字段及现实状态语义。

## 1. 适用范围

本契约约束 [`career_relation_reasoner.py`](../asof/career_relation_reasoner.py) 的三个独立入口：

1. 原局职业倾向裁决；
2. 截止日所在大运的阶段上下文裁决；
3. 已核验现实轨到职业现实状态的单向适配。

本能力保持 staged，不注册到默认 pipeline、runner、服务或 HTTP API。

## 2. 不变量

- 原局倾向不是现实职业结果。
- 大运上下文不是现实职业结果。
- 现实职业状态只能来自已核验事件或 `RealityTrack`。
- 命理倾向和大运关系不得补写、覆盖或消解现实状态。
- `mixed` 与 `transitioning` 是一等状态，不得压缩为二分类。
- 不读取 occupation、known facts、职业标签或反馈。
- 不使用浮点总分、概率、经验权重或关系强度加总。
- 无证据、关系冲突和时间定位失败必须显式返回，不得猜测。

## 3. 原局层

### 3.1 唯一输入

原局层只接受已经构建的 `CareerRelationGraphResult`。职业柱必须由关系图中的五步选择结果唯一确定，左柱必须是该职业柱的明确左邻柱。

### 3.2 离散链规则

| 路径 | 必要条件 | 输出 |
|---|---|---|
| 任职链 | 职业柱含官杀，且左柱含印星 | `employment_inclined=True` |
| 经营链 | 职业柱含财星，且左柱含食伤 | `entrepreneurship_inclined=True` |
| 双链 | 上述两条链分别完整成立 | 两个布尔均为 `True` |
| 无完整链 | 任一完整链均不成立 | 双 `False`，`insufficient_natal_relation_evidence` |
| 职业柱冲突 | 无唯一职业柱且顶级候选冲突 | 双 `False`，`career_relation_conflict` |

财星单独出现、食伤单独出现，均不得推出经营倾向。两条链独立成立，不做互斥归一化。

### 3.3 审计信息

`NatalCareerDecision` 在 v1 的 `NatalCareerInclination` 外承载：

- `applicability_conditions`：必要条件；
- `counter_evidence`：反证或缺链原因；
- `unresolved_refs`：关系图未能可靠计算的主题；
- `abstain_reason`：显式弃权。

这些字段不扩展 v1 顶层 `CareerPathState`，从而保持既有字段集合兼容。

## 4. 大运层

### 4.1 时间门禁

只有同时满足以下条件时才生成 `DayunCareerContext`：

1. `as_of_date` 非空且为明确日期；
2. 每个大运有合法干支；
3. 每个大运有明确的闭区间 `start_date`、`end_date`；
4. 所有区间均非反向且彼此不重叠；
5. 截止日落入且仅落入一个大运区间；
6. 原局职业柱与左柱均已唯一确定。

以下情况统一返回 `context=None` 和 `insufficient_dayun_information`：

- `as_of_date=None`；
- 阶段集合为空；
- 边界缺失或类型错误；
- 起止日期反向；
- 干支错误；
- 大运区间重叠；
- 截止日无法定位到唯一阶段。

### 4.2 离散关系

只考察当前大运干支与原局职业柱、左柱之间由仓库确定性谓词支持的关系：

- 天干五合或地支六合：开放原局已经成立的路径；
- 地支冲、刑、害、破：抑制原局已经成立的路径；
- 无契约支持关系：对应开放/抑制布尔保持 `False`。

大运不能凭空创造原局未成立的任职链或经营链。

若同一路径同时开放和抑制，两个轴均保留为 `True`，并返回 `mixed_signal`；不得通过分数或优先级静默消解。

## 5. 现实层

`adapt_reality_career_status(track)` 只消费 `RealityTrack.active_states` 中：

- `domain == "career"`；
- 已由 `RealityTrack` 保证核验且在截止日有效；
- 值为 `employed`、`entrepreneurial`、`mixed` 或 `transitioning`。

适配规则：

- 明确 `transitioning` 保留为 `transitioning`；
- 明确 `mixed`，或任职与经营状态同时有效，返回 `mixed`；
- 单一任职或经营状态原样返回；
- 无可用已核验职业状态返回 `unknown`。

该适配入口不接受原局倾向或大运上下文参数，因此命理轨无法污染现实轨。

## 6. 兼容性与生产边界

- v1 的 `CareerPathState` 四个顶层字段保持不变。
- v1 的 `NatalCareerInclination`、`DayunCareerContext`、`RealityCareerStatus` 构造方式保持不变。
- v2 不采用 v1 文档中可能出现的评分边界作为本 reasoner 的裁决依据。
- v2 当前仅是模块级 staged 能力；任何生产入口切换必须另行评审、验证和授权。
