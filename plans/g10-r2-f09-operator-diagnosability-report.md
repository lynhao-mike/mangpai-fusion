# G10-R2 · F09 Operator Diagnosability Readiness Report

- 记录日期：2026-07-27（Asia/Shanghai）
- Gate：G10-R2-A 至 G10-R2-D
- 本地状态：**LOCAL ONLY / NOT PUSHED**
- 远端边界：本受控会话未执行 Git/GitHub 命令；本报告不证明 GitHub 服务端整体状态
- F10 边界：**HOLD F10 保持；F10 未授权且未启动**
- 冻结合同：[`g10-r2-a2-f09-phase-observation-persistence-contract.md`](g10-r2-a2-f09-phase-observation-persistence-contract.md)
- Operator 手册：[`../docs/f09-operator-diagnosability-runbook.md`](../docs/f09-operator-diagnosability-runbook.md)

## 1. 历史授权与 STOP 保留

原 G10-R2-A 在当时明确禁止修改 `engine/f09/` 与既有 `tests/f09/` 的授权边界内完成盘点，发现 `F09Observation` 只存在于内存 `F09RunResult`，artifact attempt ledger 又只覆盖 ARTIFACT phase，无法独立闭合早期 phase 的 operator diagnosability。原合同因此按冻结 STOP 条件记录：

```text
AUTHORIZATION_REQUIRED — 需要新的独立 CONTRACT 授权才能修改 engine/f09
```

该历史事实保留在 [`g10-r2-f09-operator-diagnosability-contract.md`](g10-r2-f09-operator-diagnosability-contract.md)，未倒写、未改判。

用户后续分别授予：

1. 新开独立合同并最小修改 `engine/f09/`；
2. 必要时同步调整精确 ABI/fixture 断言；
3. 允许把真实执行新 I/O 的相关 fixture 改为 `tmp_path`，实现所有具有合法 artifact root 的受控 phase result 持久化。

新授权不继承为公开 ABI 修改、Git/GitHub、部署、F10 或合同写集外修改权限。

## 2. A2 冻结合同

[`g10-r2-a2-f09-phase-observation-persistence-contract.md`](g10-r2-a2-f09-phase-observation-persistence-contract.md) 的 CONTRACT verdict 为 `PASS`，冻结：

- 私有模块 `engine/f09/operator_diagnostics.py`；
- `application._result()` 单点接入；
- 不改变公开 DTO、函数签名、`engine.f09.__all__` 或 artifact role；
- bounded JCS observation schema；
- digest-based locator；
- 同目录临时文件、flush、fsync、atomic replace、readback byte equality；
- typed fail-closed `APPLICATION.OBSERVATION_PERSISTENCE_FAILED`；
- `artifact_root=None` 为唯一物理持久化例外，禁止任何 fallback；
- 精确本地写集与三层验证 selector；
- `LOCAL ONLY / NOT PUSHED` 与 `HOLD F10`。

## 3. TDD RED

在 production persistence 尚不存在时运行：

```text
python -m pytest tests/f09/test_operator_diagnosability_readiness.py -q
```

静态预期与动态 collection 均为 9 个实例，结果：

```text
7 failed, 2 passed in 0.53s
```

失败直接证明：

- 6 个合法 artifact root 场景没有诊断文件，表现为 `FileNotFoundError`；
- 1 个 persistence failure 注入场景没有私有模块，表现为 `ModuleNotFoundError`。

两个通过实例只证明：

- `artifact_root=None` 没有 fallback 文件；
- 既有真实 artifact attempt ledger 已满足 D3–D5 的目标材料。

该 RED collection 正常，不是 collection error；未被误记为 behavior PASS。

## 4. 最小实现

### 4.1 私有 persistence module

新增 [`../engine/f09/operator_diagnostics.py`](../engine/f09/operator_diagnostics.py)，实现：

1. schema 与 terminal closure 检查；
2. observation identity closure；
3. bounded JCS canonicalization；
4. locator identity 的 bounded JCS SHA-256；
5. `<artifact_root>/operator-diagnostics/<digest>.json` 固定路径；
6. 同目录唯一临时文件；
7. write、flush、`os.fsync()`、`os.replace()`；
8. readback bytes 与 canonical payload 精确相等；
9. 未提交临时文件 best-effort 清理；
10. 所有 persistence failure 统一转换为 typed `F09WriteError`。

### 4.2 单点接入

[`../engine/f09/application.py`](../engine/f09/application.py) 只增加私有 helper import，并在 `_result()` 中：

1. 先构造原 `F09RunResult`；
2. `artifact_root` 是 `Path` 时持久化完整 observations；
3. 返回原 DTO。

未修改公开 DTO 字段、公开 entrypoint 签名、导出、artifact role 或 owner 调用顺序。

### 4.3 fixture 最小修复

静态复核发现 [`../tests/f09/test_application_opt_in.py`](../tests/f09/test_application_opt_in.py) 的真实受控返回测试沿用字面 `Path("artifacts")`，会把新增诊断副作用写入仓库工作区。该轮 STATIC_REVIEW 裁决为 `REVISE`，随后只把实际执行新 I/O 的 5 个测试函数改为 `tmp_path / "artifacts"`，保持 `artifact_root=None` 精确用例。

[`../tests/f09/test_current_run_authority.py`](../tests/f09/test_current_run_authority.py) 虽获条件授权，但没有真实 `run_f09_slice()` 调用，未修改。`tests/f09/conftest.py` 已使用临时 artifact root，未修改。

## 5. 报告前验证与失败账本

### 5.1 首轮 GREEN 与回归

| selector | 结果 | 说明 |
|---|---:|---|
| `python -m pytest tests/f09/test_operator_diagnosability_readiness.py -q` | 9 passed | 首轮专用 GREEN |
| `python -m pytest tests/f09/test_application_opt_in.py -q` | 26 passed | fixture 修复后直接受影响测试 |
| `python -m pytest tests/f09 -q` | 1181 passed | 首轮完整 F09 回归 |
| `python -m pytest -q` | 3130 passed, 7 skipped, 1 warning | 100%，1416.30s |

首个全仓运行曾推进到 98% 后丢失最终摘要与退出码，因此被登记为 `environment/tool evidence incomplete`，不得用于 PASS。等待残余测试进程自然结束后，使用系统临时日志重新运行，取得 100% 完整汇总。临时日志不作为仓库交付物。

一次用于日志重定向的 PowerShell `Start-Process` 包装器因 stdout/stderr 指向同一文件而在启动 pytest 前失败；该事件分类为命令层 environment/tool failure，提供零测试行为证据。

### 5.2 逻辑新鲜 EVIDENCE_REVIEW 的 REVISE

独立重读冻结合同、实现与专用测试后发现：合同要求 write/readback failure 均有 typed fail-closed 机械证据，首轮专用测试只注入了 `os.replace()` failure。实现已处理 readback mismatch，但没有独立动态实例。

该缺口分类为 test evidence gap，不是已观察到的 production defect。EVIDENCE_REVIEW 裁决 `REVISE`，并使此前 STATIC_REVIEW/VERIFY 对最终冻结失效。

最小修复只修改已授权的 [`../tests/f09/test_operator_diagnosability_readiness.py`](../tests/f09/test_operator_diagnosability_readiness.py)，新增 1 个 `Path.read_bytes()` mismatch 实例，断言：

- 抛出 `F09WriteError`；
- issue code 为 `APPLICATION.OBSERVATION_PERSISTENCE_FAILED`；
- field path 为 `/artifact_root/operator-diagnostics`；
- atomic replace 后目标可能存在，但不得被当作已验证材料；
- 不残留 `.tmp` 文件。

### 5.3 REVISE 后新鲜验证

| selector | 预期/实际 collection | 结果 | exit | 耗时 |
|---|---:|---:|---:|---:|
| `python -m pytest tests/f09/test_operator_diagnosability_readiness.py -q` | 10 / 10 | 10 passed | 0 | 0.22s |
| `python -m pytest tests/f09 -q` | 1182 / 1182 | 1182 passed | 0 | 118.06s |
| `python -m pytest -q` | 3138 total outcomes | 3131 passed, 7 skipped, 1 warning | 0（pytest 100% 成功汇总） | 1283.76s |

全仓 skip 数与既有基线一致，未出现新增未知 skip；唯一 warning 是既有 `engine.application.dual_engine_adapter` deprecation warning。

## 6. D1–D5 证据裁决

| 标准 | 裁决 | 直接证据 |
|---|---|---|
| D1 | `PASS`（有界） | 五个 terminal phase 参数实例、成功五 phase、canonical bytes、确定性 locator、replace failure、readback mismatch、`artifact_root=None` 无 fallback；合法 root 下所有受控 `_result()` 通过单点持久化 |
| D2 | `PASS` | terminal observation 恰一项、位于末尾、phase/status 与 `stopped_at` 一致，`issue_codes` 非空且成员为非空字符串 |
| D3 | `PASS` | 真实 artifact coordinator 的 FAILED attempt 具有 `finished_at`、`error_class`、`error_message_digest`，且 `observed_digest is None` |
| D4 | `PASS` | FAILED attempt 可关联所属 `artifact_id`、request `input_snapshot_refs` 与 canonical `idempotency_key` |
| D5 | `PASS` | retry 后 attempt number 为 `(1, 2)`，第二项 predecessor 精确指向第一项，公共 manifest validator 通过 |

D1 的适用域严格限制为：`artifact_root` 是合法 `Path` 且 `run_f09_slice()` 经 `_result()` 形成受控结果的 run。`APPLICATION.ARTIFACT_ROOT_REQUIRED` rejection 与未形成 `_result()` 的非受控异常不在物理持久化声明内。

## 7. Falsifier Review

| falsifier | 检查结果 | 影响 |
|---|---|---|
| 空或不完整 scan | 五 terminal phase + success + 两种 persistence failure + missing root 均有实例 | 无阻断 |
| early return 绕过 | 所有受控返回集中经过 `_result()`；五个 terminal phase 动态覆盖 | 无阻断 |
| swallowed exception | persistence failure 转 typed `F09WriteError`；非受控 owner exception 不扩大捕获 | 无阻断 |
| wrong fixture/root | 专用与 vertical fixture 使用 `tmp_path`；字面工作区 root 已最小修复 | 无阻断 |
| 测试复制 production | locator test 以冻结合同 material 独立构造；未调用 production 私有 locator helper | 无阻断 |
| selector drift | 修复后静态预期 10 与动态 10 一致；F09 与全仓完整 collection 闭合 | 无阻断 |
| stale evidence | readback 测试加入后旧 GREEN 明确失效，三层均新鲜重跑 | 无阻断 |
| failure history omitted | 原 A STOP、RED、STATIC_REVIEW REVISE、工具证据不完整、EVIDENCE_REVIEW REVISE 均保留 | 无阻断 |
| 局部证据外推 | 明确列出 non-inference boundaries | 无阻断 |

## 8. 报告前 EVIDENCE_REVIEW 裁决

```text
Verdict: PASS
Current valid evidence: 修复后专用 10 passed、F09 1182 passed、全仓 3131 passed / 7 skipped / 1 warning
Invalid or historical evidence: 首次 RED；首轮 GREEN；输出尾部缺失的全仓运行；未启动 pytest 的包装器错误；readback 测试前的旧验证
Static/dynamic reconciliation: YES
Directly proven boundary: D1–D5 在冻结适用域内成立
Not-proven boundary: 完全生产就绪、外部环境、性能、安全基准、跨平台、部署、Git/GitHub、F10
Freeze eligible before report mutation: NO
Minimum next legal action: 写入 runbook、报告与十二域第 7 行，然后执行报告后三层新鲜验证
```

## 9. 十二域有限更新规则

只允许把 [`g10-r1-readiness-and-sanity-closeout.md`](g10-r1-readiness-and-sanity-closeout.md) 十二域表第 7 行从：

```text
观测性 | REQUIRES_LOCAL_GATE | 已有 audit/error surface，operator readiness 未单独验收
```

有界更新为：

```text
观测性 | PROVEN（有界） | G10-R2 D1–D5 ...
```

该更新只表示 operator diagnosability local Gate 在冻结适用域内完成，不改变其他十一行，不改写 G10.9/G10.10 历史裁决，不解除 `HOLD F10`。

## 10. 报告后新鲜验证

写入 runbook、报告和十二域第 7 行后，按冻结顺序新鲜运行：

| # | selector | collection | 结果 | exit | 耗时 |
|---|---|---:|---:|---:|---:|
| 1 | `python -m pytest tests/f09/test_operator_diagnosability_readiness.py -q` | 10 | 10 passed | 0 | 0.23s |
| 2 | `python -m pytest tests/f09 -q` | 1182 | 1182 passed | 0 | 99.91s |
| 3 | `python -m pytest -q` | 3138 total outcomes | 3131 passed, 7 skipped, 1 warning | 0（pytest 100% 成功汇总） | 1234.11s |

三层均无 failure、error 或 collection error；全仓 skip 数与既有基线一致，warning 仍为既有 deprecation。全仓输出通过系统临时日志取得完整 100% 汇总，临时日志不作为仓库交付物。

### 10.1 最终逻辑新鲜 EVIDENCE_REVIEW

最终 reviewer 只接受冻结合同、当前文件、报告后新鲜三层结果和完整失败历史，不把报告前结果冒充最终证据。复核结论：

```text
Verdict: PASS
Current valid evidence: 报告后专用 10 passed、F09 1182 passed、全仓 3131 passed / 7 skipped / 1 warning
Invalid or historical evidence: 原 A STOP；首次 RED；首轮 GREEN；尾部缺失全仓运行；未启动 pytest 的包装器错误；readback 实例前旧验证；报告前验证
Static/dynamic reconciliation: YES（10/10；1182/1182；全仓 3131 passed + 7 skipped）
Directly proven boundary: D1–D5 在 A2 冻结适用域内成立，runbook/报告/第 7 行与当前实现和测试相容
Not-proven boundary: 完全生产就绪、外部环境、性能、安全基准、跨平台、部署、Git/GitHub、F10
Freeze eligible: YES
Minimum next legal action: 有界冻结 G10-R2，保持 LOCAL ONLY 与 HOLD F10
```

### 10.2 最终 Gate 裁决

**G10-R2：`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`。**

冻结对象仅为 F09 operator diagnosability readiness 的 D1–D5 本地证据域；十二域第 7 行的 `PROVEN（有界）` 只在该边界内成立。该裁决不改变其他十一域状态，不改写 G10.9/G10.10 历史，不构成 F10 授权。

## 11. Directly Proven / Not Proven

### 11.1 Directly Proven

- 合法 root 下受控 F09 run 会在固定 operator diagnostics 目录生成 canonical、确定性寻址、readback 验证的 phase observation log；
- 受控 stopped run 的 terminal phase/status/issue identity 唯一闭合；
- success run 持久化五个 SUCCEEDED phase；
- persistence replace 与 readback mismatch 均 typed fail-closed；
- missing root 不产生 fallback；
- artifact attempt ledger 支持 D3–D5；
- 公开 F09 ABI、导出和 artifact role 未因本轮设计而要求改变；
- 修复后的专用、F09 与全仓测试在报告前均为 0 failed。

### 11.2 Not Proven / Do Not Infer

- 不证明 F09 完全生产就绪；
- 不证明外部密钥、权限、服务、运行环境或部署发布就绪；
- 不证明性能、安全基准、跨平台兼容或全仓测试未覆盖的行为；
- 不证明 Git provenance、GitHub 同步、PR、merge、发布或远端状态；
- 不证明 F10 已获授权，不允许启动 F10，不解除 `HOLD F10`；
- 不重开 F01–F12、Task 9-P 或 G10-R1 已冻结的其他语义。

## 12. 文件账本

### 新增

- [`../engine/f09/operator_diagnostics.py`](../engine/f09/operator_diagnostics.py)
- [`../tests/f09/test_operator_diagnosability_readiness.py`](../tests/f09/test_operator_diagnosability_readiness.py)
- [`g10-r2-a2-f09-phase-observation-persistence-contract.md`](g10-r2-a2-f09-phase-observation-persistence-contract.md)
- [`../docs/f09-operator-diagnosability-runbook.md`](../docs/f09-operator-diagnosability-runbook.md)
- 本报告

### 修改

- [`../engine/f09/application.py`](../engine/f09/application.py)：私有 helper import 与 `_result()` 单点调用
- [`../tests/f09/test_application_opt_in.py`](../tests/f09/test_application_opt_in.py)：真实新 I/O fixture 使用 `tmp_path`
- [`../tests/f09/test_operator_diagnosability_readiness.py`](../tests/f09/test_operator_diagnosability_readiness.py)：EVIDENCE_REVIEW REVISE 后增加 readback mismatch 实例
- [`g10-r1-readiness-and-sanity-closeout.md`](g10-r1-readiness-and-sanity-closeout.md)：仅十二域第 7 行，待本报告写入后执行

### 明确未修改

- [`g10-r2-f09-operator-diagnosability-contract.md`](g10-r2-f09-operator-diagnosability-contract.md) 历史 STOP 合同
- [`../tests/f09/test_current_run_authority.py`](../tests/f09/test_current_run_authority.py)
- `tests/f09/conftest.py`
- 九份 Task 9-P 冻结文件
- `handoff.md`
- `tools/README.md`

**LOCAL ONLY / NOT PUSHED。HOLD F10 保持。**
