# G6 收口 + G7/G8/G9 执行方案（供 terra 模型执行）

> 目的：给出可直接执行、证据优先、低 token 的操作指令。每个 Gate 只认一件事——**指定命令的真实退出码与计数**。不写逐 Task 合同散文。
>
> 工作目录固定：`f:/多流派新思路`。所有 pytest 从仓库根执行。Windows `cmd.exe`，禁用 `tail`/`grep`/`sed`。
>
> 事实源：[`plans/production-implementation-control.md`](production-implementation-control.md)、[`plans/production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md)。

---

## 0. 当前已验证事实（2026-07-25）

- [`engine/f09/`](../engine/f09/) 12 个模块存在。
- [`tests/f09/`](../tests/f09/) 存在 13 个测试文件，全绿：
  - `python -m pytest tests/f09 -q` → **1037 passed**，exit 0。
  - 隔离/回归 6 节点 → **6 passed**，exit 0。
- **未完成**：Task 10 的 T01–T104 vertical matrix 三文件缺失：
  - `tests/f09/test_f09_vertical_matrix.py`
  - `tests/f09/test_f09_adapter_reachability.py`
  - `tests/f09/data/f09_vertical_scenarios.py`

结论：Task 1–9 + P-1/P-2 + feedback 有直接行为证据；**Task 10 未落地**，构成 G7 的前置阻塞。G6 尚不能整体收口。

---

## 阶段 P0（前置）：补齐 Task 10 — Tests-Only 垂直矩阵

**唯一 owner 写集（严格闭合，禁止越界）：**
- 新建 `tests/f09/test_f09_vertical_matrix.py`
- 新建 `tests/f09/test_f09_adapter_reachability.py`
- 新建 `tests/f09/data/f09_vertical_scenarios.py`
- 可改 `tests/f09/conftest.py`（仅追加 Task 10 fixture/scenario 图，不得改动既有 Task 1–9 fixture 语义）

**硬边界：** 不得修改 `engine/f09/`、validators、生产代码、默认配置、frozen sources。若某场景暴露实现缺陷 → **停止 Task 10**，把缺陷退回对应 Task（1–9）的 owner，不得在 Task 10 内改实现，也不得弱化断言。

**唯一 copy 事实源**（禁止自创结构）：
- 104 个 `VerticalScenario` 字面量 + 104 个 `mutate_tNN` + `SCENARIOS` 元组：见 PI-500 计划 [`Task 10`](production-implementation-pi-500-r1-f09-implementation-plan.md:3086) 及其 T01–T104 字面清单（计划文件约 5145–5248 行）。
- 矩阵测试模块与 5 个断言 helper：见计划 “Literal vertical-matrix test module” 段（约 5255 行起）。
- 每个 `VerticalScenario` 九列必须完整：`test_id / pi300_purpose / mutation / mutate / expected_action / expected_gate_or_state / expected_issue_code / expected_issue_path / basis_assertions / binding_assertions / side_effect_assertion / pytest_node`。

**执行步骤：**
1. 按计划字面清单创建 `tests/f09/data/f09_vertical_scenarios.py`（104 行 `VerticalScenario` + `SCENARIOS` 元组）。
2. 在 `conftest.py` 追加 `VerticalScenario`、`ScenarioExecution`、`execute_scenario` 与 104 个 `mutate_tNN` 及 baseline 图。
3. 创建 `tests/f09/test_f09_vertical_matrix.py`（参数化 `test_f09_vertical_matrix` + 5 helper）与 `tests/f09/test_f09_adapter_reachability.py`。
4. 静态自检（先于 pytest）：
   ```
   python -m pytest --collect-only tests/f09/test_f09_vertical_matrix.py -q
   ```
   要求恰好 104 个 `T01`–`T104` 节点 + 连续性测试，无重复/缺失。
5. 运行矩阵：
   ```
   python -m pytest tests/f09/test_f09_vertical_matrix.py tests/f09/test_f09_adapter_reachability.py -q
   ```
   期望全绿；任何红灯若指向 `engine/f09/` 行为缺陷 → 停止并退回 owner Task。
6. 全套回归：
   ```
   python -m pytest tests/f09 -q
   ```
   期望计数 = 现有 1037 + 新增矩阵用例数，exit 0。

**P0 完成判据：** 上述 collect-only 计数正确 + 两条 pytest exit 0 + `git diff --name-only` 仅含 `tests/f09/` 路径。

---

## 阶段 G7：F09 集成验证

**目标：** 证明 opt-in 集成路径端到端可用且被隔离。**不改实现**，只运行既有集成/矩阵证据并记录。

**入口约定（来自计划 line 7150）：** caller `enable_f09=True`、`mode="STAGED_AUDIT"`、独立 `artifact_root`；执行入口 [`run_f09_slice_with_execution_authority_v1()`](../engine/f09/application.py:249)。

**G7 命令集（全部从仓库根，记录退出码与计数）：**
```
python -m pytest tests/f09/test_application_opt_in.py -q
python -m pytest tests/f09/test_f09_vertical_matrix.py -q
python -m pytest tests/f09/test_current_run_authority.py -q
python -m pytest tests/f09 -q
```

**G7 PASS 判据：**
- 四条命令 exit 0，无 failed/error/skipped 混入；
- 矩阵 T01–T104 全绿；
- 全套 `tests/f09` 计数与 P0 收口计数一致；
- 记录：命令、工作目录、Python/pytest 版本、collected/passed 计数、exit code。

**STOP：** 任一命令非 0、任何 collection error、任何需要改 `engine/f09/` 才能通过的用例。

---

## 阶段 G8：回归与隔离验证

**目标：** 证明 production-default 行为不变、`engine.f09` 不被默认入口加载、staged/preprod 分账。**不改任何代码。**

**默认生产入口（不得 import f09）：**
- [`engine/application/pipeline_runner.py`](../engine/application/pipeline_runner.py)
- [`engine/claims/runner_registry.py`](../engine/claims/runner_registry.py)
- [`engine/infrastructure/weight_repository.py`](../engine/infrastructure/weight_repository.py)

**G8 命令集：**
```
python -m pytest tests/f09/test_production_isolation.py -q
python -m pytest tests/application/test_staged_parallel_runner.py::test_parallel_and_comparison_modules_have_no_forbidden_imports tests/ziping_career/test_production_isolation.py::test_staged_modules_do_not_import_default_registry_pipeline_reports_or_timing -q
python -m pytest tests/test_production_entrypoints_unchanged.py tests/test_performance_and_ports.py -q
python -m pytest tests/test_error_policy.py::test_ep004_production_service_strict_render_failure_marks_job_failed -q
```

**G8 PASS 判据：**
- 四条命令全部 exit 0；
- 隔离测试确认三个默认入口的 `sys.modules` 无 `engine.f09*`；
- production entrypoint 签名/默认值/registry digest 未变；
- 记录每条命令的 passed 计数与 exit code。

**STOP：** 任一隔离/回归红灯，或发现默认入口引入 `engine.f09` import。

---

## 阶段 G9：F09 实现收口终验

**目标：** 汇总 G6(含 P0)/G7/G8 的真实证据，形成有界收口结论。**只读汇总 + 一次全域 sanity。**

**G9 命令集：**
```
python -m pytest tests/f09 -q
python -m pytest -q
```
（第二条为全仓 sanity；若历史上存在与 F09 无关的既有失败，需单独标注为 pre-existing，不得据此阻塞 F09 收口，也不得据此声称全仓绿。）

**G9 收口记录必须包含（写入 [`production-implementation-control.md`](production-implementation-control.md) 第 8 节 + 阶段表）：**
- G6 = COMPLETED（含 Task 10 P0 证据）；
- G7 = COMPLETED（集成命令证据）；
- G8 = COMPLETED（隔离/回归证据）；
- G9 = COMPLETED（终验汇总）；
- 明确“未证明”边界：全仓 100% 绿、部署、GitHub 同步、生产就绪均不因本收口成立。

**G9 PASS 判据：** G7 与 G8 全部 PASS，且 `tests/f09 -q` 复跑仍 exit 0、计数一致。

---

## 通用纪律（terra 必须遵守）

1. **证据优先**：每个 Gate 只认真实命令输出（命令 + cwd + 计数 + exit code）。不得用散文替代运行证据。
2. **不改实现闯 Gate**：G7/G8/G9 均为验证阶段。任何“要改 `engine/f09/` 才能过”的情况，退回对应实现 Task，不在验证阶段改。
3. **写集闭合**：P0 只碰 `tests/f09/`；G7/G8/G9 除收口写 `production-implementation-control.md` 外不改文件。
4. **Windows 命令**：不用 `tail`/`grep`/`sed`；pytest `-q` 的末行 summary 即结论。
5. **失败即停**：collection error = 零行为证据，立即停并归类（实现缺陷/测试缺陷/环境问题），不反复微调。
6. **GitHub 永久禁止**：不 push、不建 PR/Issue/Release，不做任何服务端写操作。

---

## 一页速查（命令清单）

```
:: P0 Task 10
python -m pytest --collect-only tests/f09/test_f09_vertical_matrix.py -q
python -m pytest tests/f09/test_f09_vertical_matrix.py tests/f09/test_f09_adapter_reachability.py -q
python -m pytest tests/f09 -q

:: G7 集成
python -m pytest tests/f09/test_application_opt_in.py -q
python -m pytest tests/f09/test_f09_vertical_matrix.py -q
python -m pytest tests/f09/test_current_run_authority.py -q
python -m pytest tests/f09 -q

:: G8 隔离/回归
python -m pytest tests/f09/test_production_isolation.py -q
python -m pytest tests/application/test_staged_parallel_runner.py::test_parallel_and_comparison_modules_have_no_forbidden_imports tests/ziping_career/test_production_isolation.py::test_staged_modules_do_not_import_default_registry_pipeline_reports_or_timing -q
python -m pytest tests/test_production_entrypoints_unchanged.py tests/test_performance_and_ports.py -q
python -m pytest tests/test_error_policy.py::test_ep004_production_service_strict_render_failure_marks_job_failed -q

:: G9 终验
python -m pytest tests/f09 -q
python -m pytest -q
```
