# 原局—大运—流年—截止状态推理系统 · 事业+财富切片 G0-G5 验证

## 结论

状态：`staged_verified_production_unchanged`。

该结论仅表示 G0-G5 隔离原型在本地白名单范围内完成证据有界验证，且指定生产目录零 diff、默认 registry、正式 pipeline 签名、公共 schema 与既有隔离回归保持基线。它不表示全仓零失败、准确率提升、生产晋级、正式报告接线或 G6 获准。

## 控制边界

- 唯一业务语义事实源：`plans/as-of-life-state-reasoning-design-2026-07-18.md`。
- 唯一执行手册：`plans/as-of-life-state-g0-g5-execution-plan-for-terra.md`。
- 允许新增：`engine/asof/`、`tests/asof/`、`plans/as-of-life-state-prototype-spec.md`、本报告。
- 禁止修改任何既有文件，特别是 `engine/application/`、`engine/decision/`、`engine/domain/`、`engine/yingqi/`、`engine/v5/`、生产 loader、默认 registry 与 `theory/*/index.yaml`。
- GitHub 服务端操作永久禁止；本切片为 `LOCAL ONLY / NOT PUSHED`。
- 工作区在本任务开始前已存在多项修改和未跟踪文件；控制器将其视为用户/其他任务所有的受保护变更，不清理、不覆盖、不归因于本切片。

## G0 · 规格与案例冻结

### 产物

- `plans/as-of-life-state-prototype-spec.md`
- 选定案例：`C-2026-028-乾-壬戌癸卯壬子乙巳`
- 命名裁定：新阶段对象使用 `DaiyunStage`，与既有 `DaiyunSegment` 分离。
- 输入裁定：不可变 `AsOfRequest` 的 `as_of_date: date` 为无默认值必填字段；禁止隐式系统日期。
- 根源 × 完成方式：仅登记设计 §6.6 的六类组合，不扩展。

### 案例三条件证据

1. `input.md`、`feedback.md`、`statement_index.json` 均存在。
2. 已核验事业事件含 2020 年兼任两校校长、2022 年晋升正股级、2025 年调任较大初中并完成兼任归并。
3. 冻结历史回放点为 2019-12-31、2021-12-31、2025-12-31，可覆盖事件前后不同现实位置。

### 规格完整性审查

- `NatalCapacityGraph` 已对照设计 §5.1 逐项标注启用/不启用，并禁止数值综合分。
- `DaiyunStage` 已对照设计 §5.2 逐项标注启用/不启用，并明确不直接映射 `retrospective.py` 自由文本。
- 事业七类事件逐项标注启用/不启用；仅启用职责层级显著变化、工作地点迁移并改变职业路径。
- 财富仅作显式传播域；案例无财富反馈，G4 使用合成边界用例并须明确标注非真实历史。
- 现实履历不得参与根源等级判定，根源不可由事件结果反向回填。

### 真实验证证据

G0 执行手册未规定 focused pytest 命令，因此本 Gate 没有 pytest collection/passed/failed 计数；不得把静态规格审查伪装成行为测试。实际运行了每 Gate 强制的工作区与生产目录检查：

```text
git status --short
git diff --name-only -- engine/application engine/decision engine/domain engine/yingqi engine/v5
```

实际结果：

```text
git status --short: exit code 0；输出包含多项 pre-existing 用户/其他任务改动，以及本次新增 plans/as-of-life-state-prototype-spec.md。
git diff --name-only -- engine/application engine/decision engine/domain engine/yingqi engine/v5: 无输出；exit code 0。
pytest: NOT RUN（G0 无规定 pytest 命令）；passed=N/A，failed=N/A，errors=N/A。
```

### G0 证据裁决

`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`

直接证明：五项裁定齐备；首选案例满足三项条件；规格已落盘；生产目录 diff 为空。

未证明：任何 G1-G5 Python 行为、历史回放正确性、全仓测试状态、生产 promotion 或准确率提升。

## G1 · 纯判别层（原局承载图 + 大运上下文）

### 产物

- `engine/asof/__init__.py`
- `engine/asof/natal_capacity.py`
- `engine/asof/daiyun_context.py`
- `tests/asof/__init__.py`
- `tests/asof/test_natal_capacity.py`
- `tests/asof/test_daiyun_context.py`

### 实现与静态审查

- `NatalCapacityGraph`、嵌套证据、节点与路径均为 frozen dataclass；构造函数不接受履历、事件后果、置信度、score、weight 或完成方式。
- 每个业务节点和路径必须携带命盘事实定位；图对象必须携带可定位原始语料引用。
- `DaiyunStage` 与既有 `DaiyunSegment` 是不同类型，不继承、不修改、不 monkey-patch 既有类。
- 适配器只直接消费 `seq`、`ganzhi`、`year_range` 等基础时间信号；自由文本 `feature` 与 `typical_domains` 仅保存在 `unresolved_signal_refs`，不会自动映射为路径变化。
- 六类路径变化只能由调用方显式传入带证据的结构化 `PathChange`；G1 不生成事件或现实后果。
- 新模块不导入默认 registry、正式 pipeline 或报告入口。

### 真实验证证据

```text
python -m pytest tests/asof/test_natal_capacity.py tests/asof/test_daiyun_context.py -q
........                                                                 [100%]
8 passed in 0.30s
exit code: 0
```

计数：collected=8，passed=8，failed=0，errors=0，skipped=0。

每 Gate 强制隔离检查：

```text
git status --short
git diff --name-only -- engine/application engine/decision engine/domain engine/yingqi engine/v5
```

实际结果：`git status --short` exit code 0，显示 pre-existing 受保护改动及本切片新增目录；生产目录 diff 无输出，exit code 0。

### G1 证据裁决

`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`

直接证明：相同输入逐字段相等；对象不可变；启用字段具备来源；自由文本不直映；近义类物理隔离；G1 focused suite 全过；生产目录零 diff。

未证明：事件候选、状态转移、历史回放、财富传播、全仓测试状态或生产晋级。

## G2 · 事件候选与证据门

### 产物

- `engine/asof/event_candidate.py`
- `tests/asof/test_event_candidate.py`

### 实现与静态审查

- `AnnualInteractionTrace` 分离年度命理触发强度与现实影响度，只保存作用链、发动节点、领域、支持/反证和候选门状态。
- `LifeEventCandidate` 保存事件域、类型、时间窗、原局/大运/流年证据链、根源性、完成方式、替代假设、冻结版本与核验状态。
- 五类正常登记组合逐项通过；第六类“任意根源 + INVALID_COMPLETION”对三级根源逐项验证，均只能生成 `WITHHELD` 非主候选。
- `NO_ROOT + ACTIVATE_EXISTING`、`NO_ROOT + COMPLETE_LATENT` 与其他未登记组合逻辑拒绝，`candidate=None`。
- 双证据门要求命盘结构证据与可定位原始语料引用同时存在。
- 根源等级实际约束未来延伸边界：强根源可进入跨运复核资格，弱根源默认本运持续且跨运重审，无根源仅短期。
- 模块不导入 `engine.f09.*`，不读取反馈、报告或 pipeline，不允许现实履历回填根源等级。
- 组合矩阵与 INVALID_COMPLETION 覆盖均为“合成边界用例，非案例 C-2026-028 的真实历史归类”；案例真实事件的历史归并留至 G5。

### 真实验证证据

```text
python -m pytest tests/asof/test_event_candidate.py -q
..............                                                           [100%]
14 passed in 0.10s
exit code: 0
```

计数：collected=14，passed=14，failed=0，errors=0，skipped=0。

每 Gate 强制隔离检查：

```text
git status --short
git diff --name-only -- engine/application engine/decision engine/domain engine/yingqi engine/v5
```

实际结果：`git status --short` exit code 0；生产目录 diff 无输出，exit code 0。

### G2 证据裁决

`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`

直接证明：登记组合覆盖、逻辑拒绝、INVALID_COMPLETION 非主事件、双证据门、年度候选门、根源延伸边界及 F09 隔离均有自动测试证据；生产目录零 diff。

未证明：案例真实事件属于何种根源/完成组合、现实影响裁决、双快照、财富传播、历史回放或全仓状态。

## G3 · 双轨状态机、影响裁决与双快照

### 产物

- `engine/asof/structural_track.py`
- `engine/asof/reality_track.py`
- `engine/asof/state_ledger.py`
- `tests/asof/test_state_ledger.py`

### 实现与静态审查

- `StructuralTrack` 仅保存原局承载图、当前大运阶段与截止日前年度作用轨迹；不保存现实核验、事件影响或人生状态。
- `RealityTrack` 仅保存截止日仍有效的已核验现实状态和显式路径状态；不接收原局、大运或流年对象。两个轨道是不同 frozen dataclass 类型。
- `AsOfRequest.as_of_date` 是无默认值必填字段，不读取系统时间。
- `EventImpactAssessment` 使用四级影响、五种持续期和三种范围进行分类裁决，不使用加权求和；系统冻结建议与人工最终裁决字段同时保留，人工裁决不得覆盖或删除系统建议，且必须完整填写三个维度与调整理由。
- `VerifiedState` 与 `HypothesisState` 是不同 frozen dataclass 类型。事实快照没有候选、假设或未核验候选字段；只有截止日前 `CONFIRMED` 且仍有效的事件后果可进入事实主线。
- 短期状态必须有显式到期日；本运余期状态以运末为有效期；跨运和永久状态可继续有效；即时事件与轻微事件不形成稳定状态。
- 未核验重大或转折候选只有在至少持续本运余期、改变基本面、改变未来结论且有最小核验问题时，才能进入独立条件分支，不能污染事实快照。
- AST 结构测试直接检查 `state_ledger.py`：禁止 `sum(...)`，禁止包含 weight/weighted/score 的计算变量，禁止 `* weight` 和 `+ score` 模式。
- 持续期、状态门与假设门矩阵均明确标注为“合成边界用例，非案例 C-2026-028 的真实历史归类”。

### 失败历史与最小修复

首次运行：

```text
python -m pytest tests/asof/test_state_ledger.py -q
.....................F...                                                [100%]
1 failed, 24 passed in 0.28s
exit code: 1
```

计数：collected=25，passed=24，failed=1，errors=0，skipped=0。失败原因是测试夹具为 `SHORT_TERM` 构造影响裁决时未提供契约要求的显式到期日；产品实现按预期 fail-closed。最小修复仅在该测试参数为短期时补入 `short_term_until=2021-06-30`，没有修改实现或放宽规则。修复后重新进行了静态复核，并精确重跑原命令。

### 新鲜验证证据

```text
python -m pytest tests/asof/test_state_ledger.py -q
.........................                                                [100%]
25 passed in 0.41s
exit code: 0
```

计数：collected=25，passed=25，failed=0，errors=0，skipped=0。

每 Gate 强制隔离检查：

```text
git status --short
git diff --name-only -- engine/application engine/decision engine/domain engine/yingqi engine/v5
```

实际结果：`git status --short` exit code 0，继续显示 pre-existing 受保护改动和本切片新增目录；指定生产目录 diff 无输出，exit code 0。

### G3 证据裁决

`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`

直接证明：命理结构轨与现实状态轨物理分离；事实与假设为不同 dataclass；未核验/已拒绝候选不污染事实；截止日、持续期、换运失效、跨运延续、路径状态、人工裁决保留和假设准入均有自动测试证据；AST 禁加权断言通过；生产目录零 diff。

未证明：案例真实事件的完整历史回放、财富显式传播、现实落点冻结、全仓测试状态、生产晋级或准确率提升。

## G4 · 财富显式传播与现实落点转译

### 产物

- `engine/asof/wealth_propagation.py`
- `engine/asof/reality_translation.py`
- `tests/asof/test_wealth_propagation.py`
- `tests/asof/test_reality_translation.py`

### 实现与静态审查

- `WealthPropagationEdge` 逐项保存来源事件、目标财富状态、传播条件、时间延迟、持续期、反证条件与边核验状态。
- 事业事件不会默认改变财富：无显式边、传播条件不满足、反证激活、来源事件未核验或传播边未核验时，均返回无变化且不创建财富事实状态。
- 合成测试建立设计 §11.2 的两条显式边：“升迁 → 稳定收入能力提高”及“创业 → 收入结构变化与资产风险暴露”。案例没有财富反馈；这些边与传播结果均明确标注为“合成传播边，非案例 C-2026-028 的真实财富历史”。
- `FrozenLandingSet` 在结果揭晓前冻结一个中心落点、最多两个同域同方向替代落点、弱命中边界、反证、排除项和版本；跨域、反方向、重复或超过两个替代落点均 fail-closed。
- 现实转译只消费已核验现实约束，并且只能选择冻结集合内仍可达的同域同方向替代；无合法冻结替代时弃权，不创建新落点。
- 核验只把预冻结中心或替代落点计作命中。结果揭晓后新增落点即使同域同方向，也不计命中、不回写冻结记录；只有同时具备已核验现实约束和补充依据时才登记 `TAXONOMY_GAP`。
- 内部条件分支完整输入不被删除；生产输出按证据等级、影响等级和稳定标识裁剪到最多两个。

### 真实验证证据

```text
python -m pytest tests/asof/test_wealth_propagation.py tests/asof/test_reality_translation.py -q
.....................                                                    [100%]
21 passed in 0.16s
exit code: 0
```

计数：collected=21，passed=21，failed=0，errors=0，skipped=0。

每 Gate 强制隔离检查：

```text
git status --short
git diff --name-only -- engine/application engine/decision engine/domain engine/yingqi engine/v5
```

实际结果：`git status --short` exit code 0，继续显示 pre-existing 受保护改动和本切片新增目录；指定生产目录 diff 无输出，exit code 0。

### G4 证据裁决

`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`

直接证明：无边不传播、条件不满足不传播、来源事件与传播边双核验后才写财富事实、两条显式合成传播边、冻结中心与最多两个替代、受约束转译、核验后禁止新增命中、`TAXONOMY_GAP` 三门和输出分支上限均有自动测试证据；生产目录零 diff。

未证明：案例 C-2026-028 存在任何真实财富变化、这些合成边已具备生产规则资格、案例历史截止点回放、全仓测试状态、生产晋级或准确率提升。

## G5 · 历史截止点回放、生产隔离与终验

### 产物

- `tests/asof/test_historical_replay.py`
- `tests/asof/test_production_isolation.py`
- 本验证报告的最终证据账本与结论。

### 实现与静态审查

- 历史回放只在 G5 已核验事件账本夹具中使用案例反馈，不把现实履历反向写入原局图、根源等级或完成方式。
- 冻结回放点为 2019-12-31、2021-12-31、2025-12-31。三个 `AsOfRequest` 复用同一事件账本，分别得到零事件、仅 2020 事件、2020+2022+2025 事件的不同 `VerifiedState`。
- 2021 截止快照明确排除 2022 晋升与 2025 调任；2025 转折路径只在 2025 截止快照出现。
- 生产隔离测试固定默认 registry digest、正式 pipeline 签名、公共 `SchoolClaim`/`StructuralVerdict` schema 和生产 claim rules digest；同时 AST 双向检查 as-of 模块未导入生产 registry/pipeline/报告/时序/F09，生产 registry、pipeline 与报告入口也未导入 `engine.asof`。

### G5 首次 suite 失败历史与最小修复

首次运行完整 as-of suite：

```text
python -m pytest tests/asof -q
3 failed, 72 passed, 1 warning in 1.01s
exit code: 1
```

计数：collected=75，passed=72，failed=3，errors=0，skipped=0。三个失败来自同一历史夹具：`AnnualInteractionTrace.trigger_strength` 使用了未登记值 `historical-replay`，实现按冻结分类集合 fail-closed。最小修复仅将测试夹具改为合法分类 `high`，没有修改生产或 as-of 实现。该失败不是全仓 sanity 的第三个回归失败，不触发 STOP。

修复后新鲜重跑：

```text
python -m pytest tests/asof -q
........................................................................ [ 96%]
...                                                                      [100%]
75 passed, 1 warning in 0.64s
exit code: 0
```

计数：collected=75，passed=75，failed=0，errors=0，skipped=0。

### 规定终验命令

```text
python -m pytest tests/asof/test_production_isolation.py -q
4 passed, 1 warning in 0.50s
exit code: 0
```

计数：collected=4，passed=4，failed=0，errors=0，skipped=0。

```text
python -m pytest tests/test_production_entrypoints_unchanged.py tests/test_performance_and_ports.py -q
11 passed, 1 warning in 0.61s
exit code: 0
```

计数：collected=11，passed=11，failed=0，errors=0，skipped=0。

```text
python -m pytest tests/ziping_career/test_production_isolation.py tests/ren_timing -q
53 passed, 1 warning in 24.15s
exit code: 0
```

计数：collected=53，passed=53，failed=0，errors=0，skipped=0。

```text
git diff --name-only -- engine/application engine/decision engine/domain engine/yingqi engine/v5
```

实际结果：无输出，exit code 0。硬门禁通过。

```text
git status --short
```

实际结果：exit code 0。输出包含本切片新增 `engine/asof/`、`tests/asof/`、冻结规格与本报告，也继续包含任务开始前已有的大量修改和未跟踪文件；这些既有内容未被清理、覆盖、暂存或归因于本任务。

### 全仓 sanity

首次全仓命令被工具层中断，未返回 collection、结果计数或 exit code，因此作为零行为证据隔离，既不证明通过也不证明失败。随后精确重跑：

```text
python -m pytest -q
2 failed, 3076 passed, 6 skipped, 1 warning in 1118.20s (0:18:38)
exit code: 1
```

计数：collected=3078，passed=3076，failed=2，errors=0，skipped=6。两个失败与审计预登记项完全一致：

- `tests/evaluation/test_dataset.py::test_witness_trust_boundary_is_explicitly_documented`
- `tests/evaluation/test_prospective_gate_workflow.py::test_handoff_names_first_legal_case_action_and_all_independent_holds`

没有第 3 个失败，未触发 STOP。该结果证明全仓仍存在两个既有失败，不能表述为“全仓通过”。

### G5 证据裁决

`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`

直接证明：同一案例的三个历史截止点生成不同事实快照；截止日之后事件不会泄漏；as-of 全套 75 项通过；三组生产隔离/回归套件共 68 项通过；指定生产目录零 diff；全仓只有审计预登记的两个失败。

未证明：全仓零失败、样本外后验、置信度校准、生产 promotion、默认 pipeline 接线、正式报告可用、准确率提升或任何 GitHub 同步。

本切片全程为 `LOCAL ONLY / NOT PUSHED`；本受控会话未执行 GitHub 服务端写操作。

## G6

未进入。G5 完成不代表 G6 获准；需独立冻结样本后验和用户另行明确审批。G0-G5 的本地授权不可继承到 G6。
