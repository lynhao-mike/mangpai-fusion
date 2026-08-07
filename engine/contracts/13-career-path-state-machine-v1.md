# 职业路径状态机契约 v1

> 代码事实源：`engine/asof/career_path_state.py`
>
> 适用范围：as-of 职业路径 staged 原型。该契约不切换生产默认入口，不授权从反馈、occupation 或 known facts 反推命盘分类结果。

## 一、目标与分层

职业路径必须拆成四层，禁止把任何一层当作另一层：

1. `NatalCareerInclination`：原局结构给出的职业路径先验；
2. `DayunCareerContext`：当前大运对两类路径的开放与抑制；
3. `RealityCareerStatus`：截至求测日由已核验事件建立的现实位置；
4. `CareerPathState.abstain_reason`：当结构不足、信号冲突或现实未知时的显式弃权原因。

核心不变量：**倾向不等于发生，大运开放不等于兑现，财富活动不等于经营所有权。**

## 二、状态定义

### 2.1 原局倾向

| 字段组合 | 语义 |
|---|---|
| `employment_inclined=true`，`entrepreneurship_inclined=false` | 原局优先支持组织内任职 |
| `employment_inclined=false`，`entrepreneurship_inclined=true` | 原局优先支持自主经营 |
| 两者均为 `true` | 双路径先验；不是现实 mixed 的充分条件 |
| 两者均为 `false` | 原局证据不足，不代表命主不会工作 |

`evidence_refs` 只引用命盘结构证据，如官印链、食伤财链或制化关系；不得引用工资、单位、经商反馈等现实答案。

### 2.2 大运上下文

`DayunCareerContext` 对任职与经营分别记录 `opens_*` 与 `suppresses_*`。同一路径可以同时开放和受抑，表示大运内部信号或与原局关系复杂；调用方必须保留冲突，不得静默归一。

`mechanism` 是人类可读的命理机制说明，例如“官杀当令且印绶承接，开放组织路径并抑制经营”。它必须描述结构关系，不得写入职业真值。

大运资料缺失或截止日期无法定位大运时，`dayun_context` 为 `None`，不得创建猜测上下文。

### 2.3 现实状态

| `current` | 正式语义 | 最低证据 |
|---|---|---|
| `employed` | 截止日处于受雇、体制或明确组织任职关系 | 已核验的入职、工资、单位、职务或在岗事件 |
| `entrepreneurial` | 截止日自主承担经营决策和盈亏 | 已核验的创业、经商、开店、合伙经营或企业所有权事件 |
| `mixed` | 同期存在任职与经营双轨，或当前状态必须结合明确转换历史解释 | 至少两条跨路径事件，且能证明双轨或转换后仍有路径重叠 |
| `transitioning` | 已发生离职、筹备、停业、转型等转换动作，但新稳定位置尚未确认 | 至少一条已核验转换事件及未闭合目标状态 |
| `unknown` | 截止日没有足够的已核验职业事实 | 无满足上述状态的证据 |

### 2.4 mixed 的正式语义

`mixed` 不是脏数据、标注失败或必须被压成弃权。它包含两种合法情况：

1. **双轨状态**：同一时期既有稳定任职，又实际经营副业或企业；
2. **转换状态的历史表达**：先任职后经营或先经营后任职，当前判断离不开已核验的转换历史。

若转换动作正在发生而目标位置尚未稳定，优先使用 `transitioning`。若只有命盘双链信号、没有现实事件，不得填写现实 `mixed`；应保持 `unknown`，并可使用 `abstain_reason="mixed_signal"`。

## 三、状态转换条件

状态转换只由已核验现实事件触发；原局和大运只能改变先验或上下文。

| 起始状态 | 目标状态 | 必要条件 |
|---|---|---|
| `unknown` | `employed` | 截止日前出现有效入职/在岗事件，且未被离职或失业事件关闭 |
| `unknown` | `entrepreneurial` | 截止日前出现实际经营及承担盈亏事件，且未被停业事件关闭 |
| `employed` | `transitioning` | 已核验辞职、裁员或创业筹备，但新经营状态尚未确认 |
| `employed` | `entrepreneurial` | 任职关闭事件 + 实际经营开启事件均已核验 |
| `employed` | `mixed` | 任职仍有效，同时实际经营已开启 |
| `entrepreneurial` | `transitioning` | 停业、退出合伙或求职转型已发生，新任职尚未确认 |
| `entrepreneurial` | `employed` | 经营关闭事件 + 有效入职事件均已核验 |
| `entrepreneurial` | `mixed` | 经营仍有效，同时有效任职已开启 |
| `mixed` | `employed` | 经营关闭，任职继续有效 |
| `mixed` | `entrepreneurial` | 任职关闭，经营继续有效 |
| 任意已知状态 | `unknown` | 仅在证据撤回、截止日早于所有有效事件或现有证据无法确定当前状态时使用；不得用来抹除不方便的 mixed |

每次转换必须在 `transition_history` 中保留来源事件、时间窗口、起点和终点。v1 骨架保留 `dict` 以兼容不同事件账本，但调用方至少应提供 `from`、`to`、`window` 与 `event_refs`。

## 四、证据要求

### 4.1 原局证据

- 只允许来自四柱结构、十神关系、透藏根气、制化与做功；
- 官杀印绶组织链可支持任职倾向；
- 食伤生财且比劫/主体参与做功可支持经营倾向；
- 仅财星多、财富分高或流动性强，不足以单独支持经营；
- 每个倾向至少保留一个可追溯 `evidence_ref`；证据不足时两个布尔值可均为 `false`。

### 4.2 大运证据

- 必须能把截止日期定位到大运阶段；
- 必须说明大运干支与原局承载结构的关系；
- 官杀当令且有印承接，可以开放任职并抑制经营；
- 大运与原局方向相悖时应保留冲突并弃权，不得测试后降低门槛。

### 4.3 现实证据

- 只接受截至求测日已发生且已核验的事件；
- 预测文本、命理判断和未来计划不构成现实证据；
- “做财务”“有业务能力”“收入高”“财运好”不自动等于经营；
- 经营证据必须涉及自主决策或承担盈亏；
- 所有 `verified_events` 应可映射回现实事件账本。

## 五、与既有 as-of 接口对齐

### 5.1 对齐 `daiyun_context.py`

`engine/asof/daiyun_context.py` 的 `DaiyunStage` 是通用阶段路径容器：

- `opened_paths` / `amplified_paths` 可显式适配为 `opens_employment` 或 `opens_entrepreneurship`；
- `closed_paths` / `suppressed_paths` 可显式适配为对应 `suppresses_*`；
- `natal_relations` 和路径变化的 evidence 用于形成 `mechanism`；
- `unresolved_signal_refs` 绝不能自动映射成职业开放/抑制；
- `PathTendencySuggestion` 仍只是启发式信号，不能直接构造已裁决的 `DayunCareerContext`。

本契约不修改 `DaiyunStage`，也不要求它依赖职业专用类型。适配方向是通用阶段对象 → 职业专用上下文，避免反向耦合。

### 5.2 对齐 `reality_track.py`

`engine/asof/reality_track.py` 的 `RealityTrack` 是已核验现实状态事实源：

- `active_states` 中职业域状态用于确定 `RealityCareerStatus.current`；
- `verified_event_ids` 映射为 `verified_events`；
- `path_states` 与有效期变化生成 `transition_history`；
- `RealityCareerStatus` 不得包含命理触发强度；
- 没有可用职业状态时必须返回 `unknown`，不得从 `NatalCareerInclination` 补写现实状态。

适配必须以 `RealityTrack.as_of_date` 为截止日，禁止纳入截止日后的事件。

## 六、弃权语义

推荐的稳定原因码：

| 原因 | 含义 |
|---|---|
| `insufficient_information` | 四柱或必要结构信息不足 |
| `insufficient_dayun_information` | 需要大运裁决但无法定位或资料缺失 |
| `score_margin_below_threshold` | 任职与经营分差小于冻结阈值 |
| `mixed_signal` | 原局与大运方向相悖或双链冲突 |
| `reality_not_verified` | 现实状态没有已核验事件 |

`abstain_reason` 描述分类器为何不作唯一方向判断，不会把 `RealityCareerStatus.current` 自动改成 `unknown`；反之，现实未知也不抹除原局倾向。

## 七、非目标

v1 数据契约不包含：

- 十神计算、格局推理或评分逻辑；
- 从 known facts、occupation、人工标签或反馈文本预测职业路径；
- 经营质量、财富层级、升迁概率或具体应期；
- 生产默认入口切换；
- 将 mixed 强制二分类。
