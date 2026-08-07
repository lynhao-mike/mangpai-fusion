# G10-R3 · F09 性能与资源观测基线 Gate 合同

## 1. Common Gate Record

| 字段 | 冻结值 |
|---|---|
| Gate | G10-R3 · F09 性能与资源观测基线 |
| Owner role | Analyst → Implementer → Static Reviewer → Verification Role → Evidence Reviewer → Controller |
| Fresh reviewer role | CONTRACT / STATIC_REVIEW / EVIDENCE_REVIEW 均采用逻辑新鲜角色；每次重置先前结论并只读取本合同、授权边界、必要原文件和当前证据 |
| Authorization envelope | 仅限本地读取、下述精确写集、本地 Python/pytest 验证和系统临时目录日志；不含任何 Git、GitHub、远端、部署或 F10 操作 |
| Activation condition | RECOVER 已确认权威状态、保护边界、现有 F09 调用路径和临时目录 fixture，且未触发 STOP |
| Remaining inactive grants | CONTRACT PASS 后方可 IMPLEMENT；IMPLEMENT 完成后方可 STATIC_REVIEW；STATIC_REVIEW PASS 后方可 VERIFY；VERIFY 完整后方可 EVIDENCE_REVIEW；EVIDENCE_REVIEW PASS 后方可 REPORT/FREEZE |
| Required inputs | `engine/f09/application.py`、`engine/f09/artifacts.py`、`tests/f09/conftest.py`、G10-R1 十二域表、G10-R2 合同与报告、仓库状态事实源 |
| Observed facts | `run_f09_slice()` 成功路径产生五个 phase observation；普通首次成功写三个业务 artifact；合法 artifact root 会持久化一次 observation log；同 key 且传入首次 manifest 时进入 retry/reuse 路径 |
| Inferences | 测量可完全在测试侧通过标准库计时、`tracemalloc` 和 callable 包裹实现，不需要公开 hook、第三方依赖或 production ABI 修改 |
| Unknowns | 本机实际耗时与峰值内存；冷启动与重复调用的实际 I/O 数；两次采样的自然波动 |
| Falsifiers | 任一场景未完成五阶段成功路径；测量污染仓库；计数边界与真实写入边界不一致；输出含 SLO/阈值或性能达标判定；必须修改公开行为或新增依赖 |
| STOP conditions | 见第 10 节 |
| Verdict | PASS（2026-07-27 逻辑新鲜合同审查；仅表示合同可实施，不证明实现正确） |
| Direct evidence boundary | 仅证明当前本地环境、当前代码与固定 fixture 下具备测量能力并取得有限快照 |
| Forbidden inference boundary | 不证明性能达标、稳定性、容量、生产负载、跨平台、部署、外部服务或 F10 readiness |
| Minimum next authorization | 合同 PASS 后，仅修改第 4 节精确写集以实现测量能力 |

## 2. 唯一目标

建立一个可重复执行的本地 F09 性能与资源观测测试能力，并取得至少两轮真实快照。每轮必须同时覆盖：

1. 一个冷启动成功调用；
2. 一个重复调用成功调用；
3. `SOURCE_PREFLIGHT`、`EVIDENCE`、`DECISION`、`TRACE`、`ARTIFACT` 五阶段墙钟耗时；
4. 整次 `run_f09_slice()` 调用的墙钟耗时与 `tracemalloc` 峰值内存；
5. 业务 artifact 原子写入次数；
6. phase observation 持久化写入次数。

本 Gate 只建立测量能力和数据快照，不制定 SLO、阈值、预算、增长上限或性能 PASS/FAIL 规则。

## 3. 明确非目标

- 不优化或重构 F09 production 代码。
- 不修改 `engine/f09/` 的公开 DTO、函数签名、字段或 `__all__`。
- 不修改九份 Task 9-P 冻结文件、F01–F12 契约、`handoff.md` 或 `tools/README.md`。
- 不启动、推进或解除 `HOLD F10`。
- 不修改 G10-R1 的 G10.9、G10.10 或十二域表中第 8 行以外的内容。
- 不新增第三方依赖。
- 不执行任何 Git 命令、GitHub 操作、远端操作、部署或发布。
- 不用两个样本推断统计稳定性、趋势、泄漏、容量或生产表现。

## 4. 精确本地写集

只允许创建或修改以下四个文件：

1. `plans/g10-r3-f09-performance-resource-observation-contract.md`：本合同；
2. `tests/f09/test_performance_resource_observation.py`：自解释测量能力与 pytest 验证；
3. `plans/g10-r3-f09-performance-resource-observation-report.md`：最终证据报告；
4. `plans/g10-r1-readiness-and-sanity-closeout.md`：只允许替换十二证据域表第 8 行。

禁止通配写集。测量运行时产生的 artifact、observation 和快照输出只能位于 pytest `tmp_path` 或操作系统临时目录，不得写入仓库。

## 5. 场景冻结

### 5.1 冷启动场景

- 使用 `baseline_scenario_bundle(tmp_path)` 构造固定合法输入；
- 使用现有 canonical artifact authority 绑定逻辑准备 projections 与 key；
- `existing_manifest=None`；
- artifact root 是该测试独占的 `tmp_path / "cold" / "f09-artifacts"`；
- 预期结果是五阶段均 `SUCCEEDED`、`stopped_at is None`、manifest 为 `COMPLETE_VERIFIED`；
- 不冻结任何耗时、内存或 I/O 数值阈值。

### 5.2 重复调用场景

- 逻辑输入、artifact key、projections 与冷启动保持相同；
- 使用独立的 `tmp_path / "repeat" / "f09-artifacts"` 完成该场景的首次准备调用；
- 第二次被测调用使用相同 artifact root，并把准备调用返回的 manifest 作为 `existing_manifest`；
- 第二次被测调用使用新的 `attempt_id`，避免把尝试身份混同为同一次执行；
- 预期结果仍是五阶段均 `SUCCEEDED`、`stopped_at is None`、manifest 为 `COMPLETE_VERIFIED`；
- 该场景仅观察幂等复用路径的资源快照，不设“增长明显/不明显”的数值判据。

准备调用不计入被测调用的耗时、峰值内存或 I/O 快照；其作用只是在临时目录内建立合法 existing manifest。

## 6. 测量方法与归属规则

### 6.1 墙钟时间

- 使用标准库 `time.perf_counter_ns()`；单位固定为整数纳秒 `ns`。
- 整次调用在进入 `run_f09_slice()` 前开始，在函数返回后结束。
- 阶段通过包裹 `engine.f09.application` 已导入的 callable 计时，不修改 production：
  - `SOURCE_PREFLIGHT`：`build_f09_evidence_package` 第一次调用开始前的入口检查区间；由于入口检查没有独立 callable，定义为整次调用起点至 `build_f09_evidence_package` 开始；
  - `EVIDENCE`：`build_f09_evidence_package` 调用区间；
  - `DECISION`：`evaluate_f09` 调用区间；
  - `TRACE`：从 `build_trace` 开始，覆盖 `build_trace`、`build_statement_set`、`validate_statement_projection` 的连续区间；
  - `ARTIFACT`：`coordinate_artifact_operation` 调用区间。
- observation log 持久化发生在结果收口阶段，不伪装成 `ARTIFACT` 业务阶段；它包含在整次调用时间中，并以独立 I/O 计数呈现。
- 阶段和不要求等于整次调用时间；未归属的框架开销必须通过 `unattributed_ns = total_ns - sum(phase_ns)` 显式呈现。若因计时边界导致负值，测试失败。

### 6.2 峰值内存

- 使用标准库 `tracemalloc`；
- 每个被测调用前启动，调用结束后读取 `get_traced_memory()` 并在 `finally` 中停止；
- 输出 `peak_traced_bytes` 整数；
- 该数值仅代表 Python `tracemalloc` 可追踪分配峰值，不代表进程 RSS、系统总内存或生产峰值。

### 6.3 I/O 计数

- 业务 artifact 写入次数：包裹 `engine.f09.artifacts._atomic_write_verified`，每次真实进入该函数计一次；
- observation 持久化写入次数：包裹 `engine.f09.application.persist_phase_observation_log`，每次真实进入该函数计一次；
- 不把读操作、临时文件内部步骤、`fsync`、`os.replace` 分别展开为额外业务写入；
- 计数只描述调用边界，不规定期望阈值。场景成功性与计数值均写入快照。

## 7. 输出 schema

测试模块必须提供可 JSON 序列化的场景结果，至少包含：

```text
scenario
run_status
stopped_at
artifact_set_state
phase_statuses
phase_wall_ns.SOURCE_PREFLIGHT
phase_wall_ns.EVIDENCE
phase_wall_ns.DECISION
phase_wall_ns.TRACE
phase_wall_ns.ARTIFACT
total_wall_ns
unattributed_ns
peak_traced_bytes
artifact_atomic_write_calls
observation_persist_calls
```

pytest 测量测试必须以稳定标记前缀输出一行 JSON，例如 `F09_PERF_RESOURCE_SNAPSHOT=`；键排序固定，便于完整日志提取。动态数值不要求跨运行相等。

## 8. 行为与结构不变量

- 两个场景都必须走真实 `run_f09_slice()` 成功路径，不复制 production 逻辑计算结果。
- 五个 phase key 必须恰好各出现一次且状态均为 `SUCCEEDED`。
- `total_wall_ns`、各阶段时间、峰值内存和两类计数必须是非负整数。
- `unattributed_ns` 必须是非负整数。
- 测量包装必须在测试结束后自动恢复，不得泄漏 monkeypatch。
- 所有 artifact root 必须位于 `tmp_path` 下。
- 不允许写入仓库根目录的 `artifacts/`、`operator-diagnostics/` 或任何快照文件。
- 不允许硬编码 SLO、阈值、预算或“性能达标”断言。
- 不允许修改 production 代码或公开 ABI。

## 9. 精确验证选择器与静态计数

### 9.1 静态计数

- 新增文件数：3；既有文件修改数：1。
- production 文件修改数：0。
- 新增第三方依赖数：0。
- 测量场景数：恰好 2（cold、repeat）。
- 每场景 phase key 数：恰好 5。
- 每轮快照场景记录数：恰好 2。
- 至少执行完整测量 selector 两次，形成两轮独立动态快照。

### 9.2 验证选择器

最低必须执行：

```text
python -m pytest tests/f09/test_performance_resource_observation.py -q -s
```

并至少重复一次同一 selector。随后执行必要 F09 回归 selector；如执行全仓 `pytest -q`，必须将完整 stdout/stderr 与 exit code 保存至操作系统临时目录，只有存在 100% 汇总和明确 exit code 才可计作有效证据。

所有命令工作目录固定为仓库根目录。命令不得包含 Git、GitHub、网络、部署、发布或远端副作用。

## 10. STOP 条件

立即停止并如实记录以下任一情况：

1. 测量必须修改 F09 公开行为、公开 DTO、函数签名、字段、`__all__` 或新增公开 hook；
2. 需要新增第三方依赖；
3. 现有测试基线耗时过长，无法取得两次可比较测量；
4. 需要任何 Git/GitHub、远端、部署、发布或解除 `HOLD F10` 的操作；
5. 必须写出第 4 节精确写集以外的仓库文件；
6. 临时目录隔离无法成立或测试产生仓库残留；
7. 两个场景任一不能完成五阶段成功路径；
8. 验证输出被截断、缺失 exit code、collection error 或无法取得完整证据；
9. 为获得结论必须创造 SLO、阈值、预算或性能 PASS/FAIL 判据。

## 11. Fresh-review questions

逻辑新鲜合同审查必须逐项回答：

1. 目标是否唯一，是否只建立测量能力与快照？
2. 写集是否精确到四个文件，是否保护 production、冻结文件和 G10.9/G10.10？
3. 冷启动和重复调用是否具有可执行、互不污染的定义？
4. 五阶段归属是否完整且没有把 observation persistence 冒充业务 artifact 阶段？
5. I/O 计数边界是否绑定真实 callable，而不是复制实现逻辑？
6. 输出 schema 与静态数量是否可核对？
7. 是否存在隐含 SLO、阈值、预算、增长判据或性能达标声明？
8. 是否明确 `tracemalloc` 和本机快照的证据边界？
9. 是否无需第三方依赖、公开 hook、Git/GitHub、远端、部署或 F10 操作？
10. 验证 selector 是否精确且失败闭合？

## 12. 直接证明与禁止外推

若后续全部 Gate PASS，本轮最多直接证明：

- 当前代码存在可重复执行的本地测量能力；
- 固定合法 fixture 下，冷启动和重复调用各取得五阶段墙钟、整次墙钟、`tracemalloc` 峰值和两类 I/O 调用计数；
- 测量运行使用临时目录，没有按合同授权写入 production 或其他仓库路径；
- 十二证据域第 8 行可从 `UNKNOWN` 有界更新为“测量能力已证明、无 SLO 判据”。

严禁推断：

- F09 性能达标或不达标；
- 不存在内存泄漏、非幂等增长或资源风险；
- 两次运行具有统计稳定性或代表长期趋势；
- 当前机器数据可外推至其他机器、操作系统、部署环境、生产负载或外部服务；
- F10 已就绪、`HOLD F10` 可解除；
- 本地结果已推送、同步、合并、部署或发布。

## 13. CONTRACT 逻辑新鲜审查记录

审查角色已重置，不采信起草者自评；审查输入限定为本合同、用户授权/保护边界，以及 `application.py`、`artifacts.py`、`tests/f09/conftest.py` 中已直接观察的必要事实。

| 审查问题 | 结论 | 直接依据 |
|---|---|---|
| 目标唯一 | PASS | 第 2 节只要求测量能力与两轮快照 |
| 写集精确且保护冻结边界 | PASS | 第 4 节恰好四个文件；第 3 节保护 production、Task 9-P、G10.9/G10.10 与 F10 |
| 两场景可执行且隔离 | PASS | 第 5 节为 cold/repeat 分配独立 `tmp_path` 子树，repeat 使用准备 manifest |
| 五阶段归属完整 | PASS | 第 6.1 节覆盖五个 phase，observation persistence 单独计数 |
| I/O 边界真实 | PASS | 第 6.3 节包裹真实 `_atomic_write_verified` 与 `persist_phase_observation_log` callable |
| 输出与数量可核对 | PASS | 第 7、9 节冻结 schema、2 场景、每场景 5 phase、至少 2 轮 |
| 无隐含性能判据 | PASS | 数值只要求类型与非负；明确禁止 SLO、阈值、预算和达标声明 |
| 内存证据边界明确 | PASS | 第 6.2、12 节限定为当前调用的 Python 可追踪分配峰值 |
| 无额外依赖或外部能力 | PASS | 只用标准库与既有 pytest；禁止 Git/GitHub、远端、部署、F10 |
| selector 精确且失败闭合 | PASS | 第 9.2、10 节冻结命令、完整输出、exit code 与 STOP |

实现约束补充：测试模块必须直接复用 `tests/f09/conftest.py` 已有的 `baseline_scenario_bundle()`、`materialize_f09_decision_inputs()` 和 canonical artifact authority 绑定 helper，不复制 fixture 或 production 构造逻辑。

**CONTRACT verdict：PASS。** 该 PASS 仅证明合同唯一、完整、可证伪且可实施；不证明实现、行为或性能。
