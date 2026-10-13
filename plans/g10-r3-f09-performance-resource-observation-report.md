# G10-R3 · F09 性能与资源观测基线 Gate 最终报告

## 1. 最终裁决

**PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE**

本轮在当前本地环境、当前代码与固定 F09 fixture 下，建立并验证了冷启动与重复调用的性能/资源测量能力，并取得两轮真实数据快照。

**本报告不包含、也不支持任何性能达标或不达标声明。** 仓库仍无 F09 SLO、阈值、预算或性能 PASS/FAIL 判据；本轮没有创造这些指标。

## 2. 授权与保护边界

- 执行范围：本地文件、标准库测量、pytest 与系统临时目录。
- `LOCAL ONLY / NOT PUSHED`。
- 本受控会话未执行任何 Git 命令。
- 本受控会话未执行任何 GitHub-mutating operation，也未执行 GitHub 读取、远端、网络、部署、发布或同步操作。
- `HOLD F10` 保持，未启动、推进或解除。
- 未修改 `engine/f09/` production 代码、公开 DTO、函数签名、字段或 `__all__`。
- 未新增第三方依赖。
- 未修改九份 Task 9-P 冻结文件、F01–F12 契约、`handoff.md`、`tools/README.md`、G10.9 或 G10.10。

## 3. 交付物

| 文件 | 作用 |
|---|---|
| `plans/g10-r3-f09-performance-resource-observation-contract.md` | 冻结目标、非目标、四文件写集、场景、计时/I/O 方法、STOP 与 non-inference |
| `tests/f09/test_performance_resource_observation.py` | 以 `perf_counter_ns`、`tracemalloc` 和真实 callable 包裹建立自解释测量能力 |
| `plans/g10-r3-f09-performance-resource-observation-report.md` | 本地动态证据、审查与有界冻结记录 |
| `plans/g10-r1-readiness-and-sanity-closeout.md` | 只更新十二证据域表第 8 行 |

## 4. 测量定义

### 4.1 场景

- `cold`：合法固定 fixture，`existing_manifest=None`，独占 `tmp_path/cold/f09-artifacts`。
- `repeat`：在独占 `tmp_path/repeat/f09-artifacts` 中先完成一次合法准备调用；被测第二次调用复用相同 key/projections/root，并携带首次 manifest 与新 attempt ID。
- 准备调用不计入被测 repeat 快照。

### 4.2 五阶段墙钟

单位为 `ns`，时钟为标准库 `perf_counter_ns()`：

- `SOURCE_PREFLIGHT`：整次调用起点至 evidence callable 开始；
- `EVIDENCE`：`build_f09_evidence_package`；
- `DECISION`：`evaluate_f09`；
- `TRACE`：`build_trace` 至 `validate_statement_projection` 结束，覆盖 statement set 构建；
- `ARTIFACT`：`coordinate_artifact_operation`。

`unattributed_ns` 显式记录整次调用中未归入上述五阶段的框架和 observation persistence 收口时间。

### 4.3 内存与 I/O

- `peak_traced_bytes`：被测单次调用期间 `tracemalloc` 可追踪的 Python 分配峰值；不是 RSS 或系统总内存。
- `artifact_atomic_write_calls`：真实进入 `engine.f09.artifacts._atomic_write_verified` 的次数。
- `observation_persist_calls`：真实进入 `engine.f09.application.persist_phase_observation_log` 的次数。

## 5. 两轮真实快照

### 5.1 Run 1

命令：

```text
python -m pytest tests/f09/test_performance_resource_observation.py -q -s
```

结果：exit code `0`；`1 passed in 2.13s`；输出完整、未截断。

| 场景 | SOURCE_PREFLIGHT ns | EVIDENCE ns | DECISION ns | TRACE ns | ARTIFACT ns | total ns | unattributed ns | peak bytes | artifact writes | observation writes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| cold | 1,783,400 | 48,854,600 | 48,354,100 | 706,357,100 | 26,871,100 | 839,813,700 | 7,593,400 | 240,881 | 3 | 1 |
| repeat | 2,107,900 | 36,835,600 | 52,150,100 | 496,671,600 | 11,641,100 | 609,735,700 | 10,329,400 | 240,681 | 0 | 1 |

两个场景均直接输出：五个 phase `SUCCEEDED`、`stopped_at=null`、artifact set `COMPLETE_VERIFIED`。

### 5.2 Run 2

命令：

```text
python -m pytest tests/f09/test_performance_resource_observation.py -q -s
```

结果：exit code `0`；`1 passed in 3.64s`；输出完整、未截断。

| 场景 | SOURCE_PREFLIGHT ns | EVIDENCE ns | DECISION ns | TRACE ns | ARTIFACT ns | total ns | unattributed ns | peak bytes | artifact writes | observation writes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| cold | 41,200 | 53,733,300 | 68,741,400 | 894,583,200 | 682,273,400 | 1,713,994,700 | 14,622,200 | 240,881 | 3 | 1 |
| repeat | 29,000 | 53,339,400 | 64,448,500 | 923,369,200 | 15,857,200 | 1,068,579,800 | 11,536,500 | 240,681 | 0 | 1 |

两个场景均直接输出：五个 phase `SUCCEEDED`、`stopped_at=null`、artifact set `COMPLETE_VERIFIED`。

### 5.3 快照解释边界

- 两轮均实际取得 cold/repeat 数据，I/O 调用计数结构一致：cold 为 `3 + 1`，repeat 为 `0 + 1`。
- 两轮墙钟数据存在自然波动。
- 上述事实只描述本机两轮观察值；不判定速度、退化、稳定性、泄漏、容量、增长是否明显，亦不建立任何阈值。

## 6. 动态验证账本

| Run | 选择器 | 收集 | 通过 | 失败/错误/跳过 | Exit code | 完整性 |
|---:|---|---:|---:|---:|---:|---|
| 1 | 新增测量 selector | 1 | 1 | 0 / 0 / 0 | 0 | 完整 JSON + pytest 汇总 |
| 2 | 新增测量 selector | 1 | 1 | 0 / 0 / 0 | 0 | 完整 JSON + pytest 汇总 |
| 3 | application + artifact lifecycle + operator diagnosability 回归 | 253 | 253 | 0 / 0 / 0 | 0 | 100% 汇总；`253 passed in 11.93s` |

回归命令：

```text
python -m pytest tests/f09/test_application_opt_in.py tests/f09/test_artifact_lifecycle.py tests/f09/test_operator_diagnosability_readiness.py -q
```

本轮未运行全仓测试，因此不声明 full-suite PASS。

## 7. 静态/动态对账

| 合同静态预期 | 动态事实 | 对账 |
|---|---|---|
| 每轮 1 个 pytest check | 两轮各收集 1 项 | YES |
| 每轮恰好 2 个场景 | 两轮 JSON 均为 cold、repeat | YES |
| 每场景恰好 5 个 phase | 两轮四个场景记录均包含五个冻结 key | YES |
| 两场景五阶段成功 | 均为 `SUCCEEDED` 且无 stopped phase | YES |
| artifact set 完整 | 均为 `COMPLETE_VERIFIED` | YES |
| 至少两轮快照 | 已取得 Run 1、Run 2 | YES |
| production 修改 0 | 本轮实现未写 `engine/f09/` | YES |
| 第三方依赖新增 0 | 测量只用标准库与既有 pytest | YES |

## 8. 工作区隔离证据

- 新增测试的 cold root：`tmp_path / "cold" / "f09-artifacts"`。
- 新增测试的 repeat root：`tmp_path / "repeat" / "f09-artifacts"`。
- pytest 完成后，对仓库根顶层进行只读列举，未发现 `artifacts/` 或 `operator-diagnostics/`。
- 对仓库 JSON 文件搜索稳定快照标记，匹配数为 0。
- 新增测试源码不存在字面仓库 `Path("artifacts")`，也不调用仓库快照写入 API。

该证据仅支持“本轮新增测量运行未观察到上述仓库残留”，不外推所有历史文件或其他未运行代码路径。

## 9. Fresh review 与失败历史

### 9.1 CONTRACT fresh review

结论：PASS。合同目标唯一、四文件写集精确、场景和计数可执行、无 SLO/阈值，且不需要 production hook、第三方依赖、Git/GitHub、远端、部署或 F10 操作。

### 9.2 STATIC_REVIEW fresh review

结论：PASS。实现复用既有 fixture helper 与真实 production callable；使用 `monkeypatch.context()` 恢复包装；没有复制 production 逻辑、吞错、越权写入、ABI 修改或外部副作用。静态 PASS 不被当作行为 PASS。

### 9.3 EVIDENCE_REVIEW fresh review

结论：PASS；Freeze eligible：YES。两轮测量与一轮回归均 fresh、授权内、完整、scope-matched；静动态数量对账；隔离检查无合同禁止残留。

### 9.4 失败、诊断、修复与重跑历史

本轮无失败运行、collection error、截断输出、未知 exit code、超时、修复或无效证据。两次相同 selector 是合同要求的两个独立测量轮次，不是失败重跑。

## 10. 直接证明

- 当前本地代码具备可重复执行的 F09 cold/repeat 测量能力。
- 固定合法 fixture 下，两个场景均取得五阶段墙钟、整次墙钟、`tracemalloc` 峰值、artifact 原子写计数和 observation 持久化计数。
- 两轮被测调用均完成五阶段成功路径并返回 `COMPLETE_VERIFIED`。
- repeat 被测调用在两轮中均观察到业务 artifact 原子写计数为 0，同时 observation 持久化计数为 1；这证明该固定场景两轮的直接调用观测，不证明所有幂等路径。
- 相关 253 项 F09 application/artifact/diagnostics 回归通过。
- 本轮新增测量使用 pytest 临时目录，隔离检查未观察到合同禁止的仓库残留。
- 十二证据域第 8 行具备从 `UNKNOWN` 更新为有界 `PROVEN` 的证据基础：仅测量能力，不含 SLO 判据。

## 11. 明确没有证明 / 禁止推断

- **未做性能达标或不达标声明。**
- 未证明 F09 满足任何 SLO、延迟预算、吞吐目标、内存上限或资源预算。
- 未证明不存在内存泄漏、非幂等增长、性能退化或资源风险。
- 未证明两轮数据具有统计稳定性、代表长期趋势或可用于容量规划。
- 未证明 `tracemalloc` 峰值等于进程 RSS、系统总内存或生产峰值。
- 未证明其他机器、操作系统、部署环境、生产负载或外部服务表现。
- 未证明全仓测试通过、系统级正确性、安全基准或跨平台兼容性。
- 未证明 F10 readiness；`HOLD F10` 仍保持。
- 未证明 GitHub 整体状态未被其他主体改变；只确认本受控会话未执行 Git/GitHub 操作。
- 未发生推送、PR、合并、部署、发布或远端同步；`LOCAL ONLY / NOT PUSHED`。

## 12. 十二证据域第 8 行更新对比

更新前：

```text
| 8 | 性能与资源 | `UNKNOWN` | 无明确 F09 SLO/基准合同，不自行创造指标 |
```

更新后：

```text
| 8 | 性能与资源 | `PROVEN`（有界，仅测量能力，无 SLO 判据） | G10-R3 已由性能/资源观测合同、测量测试与两轮本地快照证明 cold/repeat 五阶段墙钟、`tracemalloc` 峰值及 artifact/observation I/O 计数能力；仅为当前本地固定 fixture 的数据快照，不构成性能达标、不达标、稳定性、容量、跨平台、部署环境或 F10 readiness 声明 |
```

## 13. Reopening conditions

出现以下任一情况时，应重新开启性能/资源证据域，而不是沿用本快照：

- F09 五阶段编排、artifact 写入或 observation persistence 边界发生行为变化；
- 新增正式 SLO、资源预算、容量目标或统计采样合同；
- 需要跨机器、跨平台、部署或生产负载结论；
- 测量 fixture、输出 schema 或计数边界改变；
- 后续证据发现仓库污染、不可复现或计时归属缺陷。
