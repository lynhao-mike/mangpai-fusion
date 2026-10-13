# 原局—大运—流年—截止状态推理系统 · 事业+财富首个原型规格

> 状态：G0 冻结规格
> 范围：事业主域 + 财富显式传播域；仅供 G0-G5 staged 原型
> 唯一业务语义事实源：[`as-of-life-state-reasoning-design-2026-07-18.md`](as-of-life-state-reasoning-design-2026-07-18.md)
> 执行手册：[`as-of-life-state-g0-g5-execution-plan-for-terra.md`](as-of-life-state-g0-g5-execution-plan-for-terra.md)
> 隔离边界：仅新增 `engine/asof/`、`tests/asof/` 与本计划指定的规格/验证报告；不接入生产 loader、registry、pipeline 或报告入口

## 1. G0 冻结结论

本原型直接采用设计文档的推理宪法、事件影响模型、双快照归并规则与架构不变量，不重新解释、不简化。原局、大运、流年之间采用阶段约束与证据门，不使用分数加权求和。命理结构轨和现实状态轨必须由独立 dataclass 表达。未核验候选不得进入事实快照。财富变化只允许通过显式传播边发生。

## 2. 案例冻结

选定案例：`C-2026-028-乾-壬戌癸卯壬子乙巳`。

### 2.1 三项准入条件复核

| 条件 | 复核结果 | 证据 |
|---|---|---|
| 文件完整性 | 通过 | `input.md`、`feedback.md`、`statement_index.json` 均存在。 |
| 至少一个已核验事业事件 | 通过 | 2020 年校分拆后兼任两校校长；2022 年晋升正股级；2025 年调任较大初中并经历兼任归并，均由用户反馈给出明确年份和现实结果。 |
| 可设置多个历史 `as_of_date` | 通过 | 冻结 2019-12-31、2021-12-31、2025-12-31 三个回放点，分别位于 2020 事件之前、之后以及 2025 调任之后。 |

### 2.2 排盘充分性

`input.md` 明确提供出生时间、乾坤、四柱、藏干、十神、起运年、顺逆与九步大运排布，足以构造事业域最小原局承载图和大运阶段上下文。因此不切换备选案例。

### 2.3 防泄底边界

案例履历仅用于 G5 历史回放夹具和已核验事件账本，不得反向参与原局根源等级判定。G1 原局承载图只消费排盘事实；G2 根源判定只消费命盘结构证据与可定位原始语料证据。现实履历、事件后果、完成方式和置信度不得回填或抬升原局根源性。

### 2.4 原型启用的事业事件类型

设计 §11.1 的七类事业事件逐项裁定如下：

| 事件类型 | 本次状态 | 理由 |
|---|---|---|
| 首次进入稳定职业 | 不启用 | 当前案例缺少精确首次入编年份，不用于首切片主事件。 |
| 升迁或职责层级显著变化 | 启用 | 2020 兼任双校与 2022 正股级均可核验。 |
| 主动或被动离职 | 不启用 | 案例无对应反馈。 |
| 跨行业转职 | 不启用 | 案例始终处于教育系统。 |
| 创业或结束经营 | 不启用 | 案例无对应反馈。 |
| 长期职业中断 | 不启用 | 案例无对应反馈。 |
| 工作地点迁移并改变职业路径 | 启用 | 2025 调任较大初中并最终专任，可核验现实路径变化。 |

财富不是主事件生成域，只作为事业事件经显式传播边到达的状态域。案例没有财富事实反馈，因此 G4 财富传播测试必须标记为“合成边界用例，非该案例真实历史”。

## 3. `NatalCapacityGraph` 最小字段冻结

对象职责保持设计 §5.1：只表达稳定原局承载，绝不表达求测截止日现实结果。

| 设计要求 | 字段 | 类型/形态 | 本次状态 | 来源与约束 |
|---|---|---|---|---|
| 领域能力与容量 | `domain` | `str` | 启用 | 固定为 `career`；仅声明原型领域，不由履历推导。 |
| 领域能力与容量 | `capacity_nodes` | `tuple[CapacityNode, ...]` | 启用 | 每个节点含稳定 `node_id`、领域功能、命盘事实引用；来自四柱、藏干、十神等排盘事实。 |
| 主要结构与脆弱点 | `structural_features` | `tuple[EvidenceRef, ...]` | 启用 | 结构方向及命盘证据；不得含现实事件。 |
| 主要结构与脆弱点 | `vulnerabilities` | `tuple[EvidenceRef, ...]` | 启用 | 受阻或脆弱结构及命盘证据。 |
| 可行路径与限制条件 | `feasible_paths` | `tuple[PathRef, ...]` | 启用 | 原局可承载的事业功能路径，不等于实际职业履历。 |
| 可行路径与限制条件 | `constraints` | `tuple[EvidenceRef, ...]` | 启用 | 对路径成立的原局限制。 |
| 命理事实证据 | `chart_evidence` | `tuple[EvidenceRef, ...]` | 启用 | 必须定位到输入中的四柱/藏干/十神事实。 |
| 原始语料依据 | `source_citations` | `tuple[SourceCitation, ...]` | 启用 | 必须包含可定位文件路径与行号；二手规则不得单独通过语料门。 |
| 竞争解释与反证 | `competing_explanations` | `tuple[str, ...]` | 启用 | 保存同一结构的竞争解释。 |
| 竞争解释与反证 | `counter_evidence` | `tuple[EvidenceRef, ...]` | 启用 | 保存结构反证，不允许仅输出支持证据。 |
| 对象身份与可审计性 | `case_id` | `str` | 启用（工程辅助） | 只作来源追踪，不改变设计语义。 |
| 对象身份与可审计性 | `schema_version` | `str` | 启用（工程辅助） | 固定原型序列化契约。 |
| 其他基本面容量 | — | — | 不启用 | 不扩展到原生家庭、学业、婚姻、健康等领域。 |
| 数值综合分 | — | — | 禁止 | 不设置 natal score、总分或加权结果。 |

所有集合使用不可变 tuple；构造函数为纯函数，相同输入逐字段相等。

## 4. 大运阶段对象命名与字段冻结

### 4.1 命名裁定

新对象定名为 `DaiyunStage`，实现文件仍为 `engine/asof/daiyun_context.py`。

它与既有 `engine.yingqi.retrospective.DaiyunSegment` 的区别：

- `DaiyunSegment` 是逐年回溯的基础时间容器，包含自由文本 `feature`、`typical_domains` 与流年列表；
- `DaiyunStage` 是 as-of 推理中的结构化阶段上下文，表达路径被开放、关闭、放大、抑制、修复或改道，并携带适用条件与反证；
- `DaiyunStage` 不继承、不修改、不 monkey-patch `DaiyunSegment`；适配器只把既有对象当信号来源，不能把自由文本直接映射成结构化路径裁决。

### 4.2 最小字段

| 设计要求 | 字段 | 类型/形态 | 本次状态 | 来源与约束 |
|---|---|---|---|---|
| 时间范围 | `sequence` | `int` | 启用 | 来自排盘大运序号。 |
| 时间范围 | `ganzhi` | `str` | 启用 | 来自排盘大运干支。 |
| 时间范围 | `start_date` / `end_date` | `date` | 启用 | 由明确起讫年构造闭区间；不读取系统当前日期。 |
| 开放路径 | `opened_paths` | `tuple[PathChange, ...]` | 启用 | 必须有结构化信号与证据。 |
| 关闭路径 | `closed_paths` | `tuple[PathChange, ...]` | 启用 | 必须有结构化信号与证据。 |
| 放大路径 | `amplified_paths` | `tuple[PathChange, ...]` | 启用 | 必须有结构化信号与证据。 |
| 抑制路径 | `suppressed_paths` | `tuple[PathChange, ...]` | 启用 | 必须有结构化信号与证据。 |
| 修复路径 | `repaired_paths` | `tuple[PathChange, ...]` | 启用 | 必须有结构化信号与证据。 |
| 改道路径 | `redirected_paths` | `tuple[PathChange, ...]` | 启用 | 必须有结构化信号与证据。 |
| 与原局节点有效关系 | `natal_relations` | `tuple[NatalRelation, ...]` | 启用 | 明确引用 `NatalCapacityGraph` 节点；自由文本不能直接充当关系。 |
| 领域阶段倾向 | `domain_tendency` | `str` | 启用 | 仅事业域枚举式倾向，不是数值评分。 |
| 适用条件 | `applicability_conditions` | `tuple[str, ...]` | 启用 | 所有路径变化须声明成立条件。 |
| 反证 | `counter_evidence` | `tuple[EvidenceRef, ...]` | 启用 | 阶段解释的反证。 |
| 信号来源 | `signal_refs` | `tuple[EvidenceRef, ...]` | 启用（工程辅助） | 追踪排盘事实或既有模块产出；自由文本信号只能登记为待判别输入。 |
| 流年列表 | — | — | 不启用 | 流年轨迹属于 `AnnualInteractionTrace`，不嵌入阶段对象。 |
| 现实事件后果 | — | — | 禁止 | 阶段上下文不承担事件或现实状态判定。 |
| 数值阶段总分 | — | — | 禁止 | 不允许大运分与原局分相加。 |

## 5. `as_of_date` 输入契约

采用新建、不可变的 request dataclass：

```python
@dataclass(frozen=True)
class AsOfRequest:
    case_id: str
    as_of_date: date
```

冻结规则：

1. `as_of_date` 是必填构造参数，无默认值；
2. 禁止读取 `date.today()`、`datetime.now()`、系统时钟或环境变量作为隐式替代；
3. 输入必须是 `datetime.date`，不得接受无时区语义的自由文本并静默猜测；
4. 所有历史事件必须满足 `event_date <= as_of_date` 才能进入本次归并；
5. 截止日后的事实不得被读取、不得参与候选裁决、不得出现在 `VerifiedState`；
6. 同一请求和同一冻结输入必须产生逐字段相同结果；
7. 正式后运主线只能从该截止日的 `VerifiedState` 出发，不能从出生原局重新开始。

## 6. 根源 × 完成方式白名单

直接采用设计 §6.6，仅登记以下六类，不新增：

| 根源性 | 完成方式 | 原型裁决 |
|---|---|---|
| `STRONG_ROOT` | `ACTIVATE_EXISTING` | 可进入双证据门并生成强事件候选。 |
| `STRONG_ROOT` | `REPAIR_DEFECT` | 可形成显著改善；跨运延续必须检查现实成果是否固化。 |
| `WEAK_ROOT` | `COMPLETE_LATENT` | 可生成候选；延伸范围受原局缺失程度约束。 |
| `WEAK_ROOT` | `TEMPORARY_SUBSTITUTE` | 只支持阶段性候选，不自动升级为长期层级变化。 |
| `NO_ROOT` | `TEMPORARY_SUBSTITUTE` | 原则上只支持短期机会或波动，不推导永久路径。 |
| `STRONG_ROOT` / `WEAK_ROOT` / `NO_ROOT` | `INVALID_COMPLETION` | 本次岁运不得生成目标主事件，进入反证、降级或弃权。 |

逻辑拒绝与未登记边界：

- `NO_ROOT + ACTIVATE_EXISTING`：逻辑矛盾，拒绝且不生成候选；
- `NO_ROOT + COMPLETE_LATENT`：不得宣称完成潜在结构；本原型不登记为候选组合；
- 除上表之外的组合保持未登记；不得因案例需要自行扩展；
- 任意根源与 `INVALID_COMPLETION` 配对时均不生成目标主事件；
- 多流派数量、现实履历、事件后果或置信度均不得自动升级根源等级。

## 7. 后续 Gate 冻结接口

G1 只构造 `NatalCapacityGraph` 与 `DaiyunStage`，零事件判定。G2 新增 `AnnualInteractionTrace` 与 `LifeEventCandidate`，并执行命盘结构证据 + 原始语料证据双门。G3 实现独立命理结构轨、现实状态轨、`VerifiedState`、`HypothesisState` 与事件影响账本。G4 只通过显式边传播到财富，并实现冻结落点与 `TAXONOMY_GAP`。G5 以 2019-12-31、2021-12-31、2025-12-31 做历史回放并证明生产隔离。

## 8. 非目标与冻结边界

- 不做 G6、生产 promotion、样本外后验校准或 Beta 切换；
- 不修改任何既有生产文件、F01-F12 契约、默认 loader/registry/pipeline/schema/report 入口；
- 不复用 `engine/f09/` 的字段或命名，只可参考隔离架构模式；
- 不建立跨卡统一五动作 dispatcher；
- 不扩展到六大基本面全量；
- 不做 GitHub 服务端操作；全部产物为 `LOCAL ONLY / NOT PUSHED`。
