# T-104 · 修 `recording_builder` 签名，接住 `run_id` 参数

## Review Level: 2

> 定级理由：改动落在 `tests/` 保护区内。虽然是单函数签名改动，但它决定
> 一条断言链（`calls == [input_text]`）是否仍然成立，需中枢核对断言未松动后放行。
> 不升至 3：File Scope 单文件单函数、不触碰验收标准本身、不改变产品行为。

## Context（中枢只读勘察已确证，Worker 无需重复勘察）

**失败现象：**

```
TypeError: test_preprod_builds_r10_run_from_exact_input_text.<locals>.recording_builder()
           got an unexpected keyword argument 'run_id'
```

**根因链（已核实 2026-10-19）：**

1. commit `1eb20968`（2026-10-15，refactor(phase1-3): complete service decoupling,
   v5 identity chain, statement v2, and dual-line interop）给
   `engine/decision/r10_ziping_career.py:build_ziping_career_decision_run` 加了
   关键字参数 `run_id: str | None = None`：

   ```python
   +    *,
   +    run_id: str | None = None,
   -    run_id=v5_adapter._stable_id("drun", case_id, raw_hash),
   +    run_id=run_id or v5_adapter._stable_id("drun", case_id, raw_hash),
   ```

2. 同提交让 `engine/v5/preprod.py` 传入该参数：

   ```python
   -    decision_run = build_ziping_career_decision_run(output, raw_text=input_text)
   +    decision_run = build_ziping_career_decision_run(output, raw_text=input_text, run_id=snapshot.run_id)
   ```

3. `tests/r10/test_r10_ziping_career_acceptance.py` 里的 fake builder 签名仍写死为
   `recording_builder(output, raw_text="")`，不接 `run_id`，于是 TypeError。

**方向已定：改测试，不改实现。** 反证：同一提交的 3 份测试已固定 run_id 身份链，
改回实现会破坏它们：

- `tests/v5/test_render_report_v6.py:114` —— 断言 `decision_payload["run_id"] == run_snapshot.run_id`（实测 5 passed）
- `tests/evaluation/test_dual_line_interop.py:178` —— 身份链绑定
- `tests/evaluation/test_dual_line_interop.py:189` —— 身份漂移必须被拒绝

## Objective

让 `recording_builder` 接受并透传 `run_id`（以及未来可能新增的关键字参数），
使该用例通过，同时**不改变它原本要断言的东西**（`calls == [input_text]`）。

## 授权范围

**你被授权修改且仅修改：**

```
tests/r10/test_r10_ziping_career_acceptance.py
```

且仅限 `test_preprod_builds_r10_run_from_exact_input_text` 内部定义的
`recording_builder` 函数签名与参数转发逻辑。

## Steps

### Step 0: Preflight

- [ ] 读 `test_preprod_builds_r10_run_from_exact_input_text` 全文，确认 `recording_builder`
      的当前签名与它在测试中的用法
- [ ] 确认该测试的断言是 `calls == [input_text]`（与 run_id 无关）

### Step 1: 改签名

- [ ] 把 `def recording_builder(output, raw_text="")` 改为接收 `**kwargs` 并转发
- [ ] **不要硬编码 `run_id`**，用 `**kwargs` 兜住，避免下次新增参数又断
- [ ] 保持 `raw_text` 的记录行为不变（它才是断言的对象）

### Step 2: 验证

- [ ] 该测试单跑通过
- [ ] `tests/r10` 整目录失败数从 5 降到 4
- [ ] 默认门禁 `python -m pytest -q` 仍 229 passed

## Completion Criteria（可执行命令 + 期望退出码，全部需粘贴原始输出）

| # | 命令 | 期望 |
|---|---|---|
| 1 | `python -m pytest tests/r10/test_r10_ziping_career_acceptance.py::test_preprod_builds_r10_run_from_exact_input_text -q -o addopts=""` | **exit 0**，1 passed |
| 2 | `python -m pytest tests/r10 -q -o addopts=""` | **4 failed**（不是 5） |
| 3 | `python -m pytest -q` | **exit 0**，`229 passed`（默认门禁不回归） |
| 4 | `git diff --stat -- tests/` | **仅 1 个文件**，且只增删几行 |

## Do NOT

- **禁止修改任何断言**（含放宽、删除、改成 `assert True`）
- **禁止 `pytest.skip` / `xfail` / `try-except` 吞掉 TypeError**
- **禁止修改 `engine/v5/preprod.py` 或 `engine/decision/r10_ziping_career.py`**——方向已定是改测试
- **禁止读取 File Scope 之外的文件**（除上面 Context 里点名的几个只读文件）
- **禁止执行 `git commit` / `checkout` / `stash` / `reset` / `clean`**
- 禁止顺手去修另外 4 个失败（另立卡）

## Deliverables

- 改后的 `tests/r10/test_r10_ziping_career_acceptance.py`
- `tasks/T-104/BRIEF.md`：改动前后 diff、4 项验收原始输出、未完成与风险
- 更新 `tasks/T-104/STATUS.md`
