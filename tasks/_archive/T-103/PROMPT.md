# T-103 · `testpaths` 收口为 `["tests"]`，黑名单显式化，登记 4 个保留 ignore

> **Review Level 3** —— 本卡改动的是**验收标准本身**。合并后所有后续任务的
> 完成标准都会变，必须独立评审，不可"自测自过"。

## Context（中枢只读勘察已确证，Worker 无需重复勘察）

**根因**：`testpaths` 是**白名单**（L12-23 共 10 项），新测试目录默认静默掉落。
叠加 `addopts` 的 5 个 `--ignore`，形成双重收窄。结果：**90 个测试文件、2000+ 用例
从未进入默认门禁**。

**已确证证据（2026-10-19）：**

| 观测 | 命令 | 结果 |
|---|---|---|
| 现状收集 | `pytest --collect-only -q` | `229 tests collected` |
| 合并运行（除 5 个 ignore 目录外全部） | `pytest tests -q -o addopts="... 5 个 --ignore"` | **`1 failed, 3110 passed, 4 skipped`，rc=1** |
| 该 1 failed | — | `tests/test_preflight_prospective.py`（**T-101 修**） |
| `tests/v5` | `pytest tests/v5 -q` | `128 passed`，**rc=0**，268.22s |
| `tests/track_e_smoke` | `pytest tests/track_e_smoke -q` | **rc=5，no tests ran**（纯 stdlib 脚本，设计如此） |
| 未收集的 11 个包 | 逐个单跑 | 全 green（f09 1183 / claims 189 / governance 178 / yang_marriage 145 / application 104 …） |

## Objective

1. `testpaths` 由 10 项白名单收口为单根 `["tests"]`，使新测试目录**默认被收集**。
2. 把「确实不该跑」的目录由白名单副作用改为**显式黑名单**，并全部附**关闭条件**。
3. 将 4 个保留 ignore 及其关闭条件写入 `AGENTS.md` §5，防止变成永久沉默区。

**本卡不解禁 `tests/v5`**（按运营决策延后至独立卡）。

## 指定改动 1：`pyproject.toml`

```toml
testpaths = ["tests"]
addopts = [
    "-ra",
    "--strict-markers",
    "--tb=short",
    "--ignore=tests/evaluation",
    "--ignore=tests/asof",
    "--ignore=tests/r10",
    "--ignore=tests/v1_3_acceptance",
    "--ignore=tests/v5",
    "--ignore=tests/track_e_smoke",
]
```

| 改动 | 理由 |
|---|---|
| `testpaths` 10 项 → `["tests"]` | 消除"新增目录静默不跑"的机制性缺口 |
| **新增** `--ignore=tests/track_e_smoke` | 纯 stdlib 自跑脚本，pytest 收集恒 `rc=5`；**若不显式 ignore，`pytest -q` 退出码恒非 0** |
| 保留 4 个 `--ignore` | 见下表，每项附关闭条件 |
| 保留 `--ignore=tests/v5` | 268s，按决策延后；由 v5 解禁卡（用 T-102 的 slow marker）处理 |

**注意**：T-102 已在 `markers` 注册 `slow`，本卡**不得**改动该段。

## 指定改动 2：`AGENTS.md` §5

在「验证命令」小节内，「核心回归测试」命令之后插入登记块，模板如下（措辞可润色，
但**必须**包含：目录、当前状态、用例数、关闭条件、负责人待定）：

```markdown
#### 门禁技术债登记（4 项，勿删）

以下目录以 `--ignore` 显式排除，均为**已登记的技术债**而非"已弃置"。
每项附关闭条件；满足后应从 `addopts` 移除并重新纳入门禁。

| 目录 | 排除原因（实测） | 规模 | 关闭条件 |
|---|---|---|---|
| `tests/evaluation` | 8 个文件依赖已丢失的 `.omo/drafts/...-2026-08-08.md` 草稿 | 26 failed + 294 error；其余 498 passed | 8 个文件改指向 `cases/` 或 `META/` 下的稳定产物 |
| `tests/asof` | 2 个架构门禁红灯 | 609 passed / 2 failed | ① 移除 `engine/asof/career_event_prediction.py` 对 `engine.decision.ren_career_timing` 的越界导入；② 刷新 `tests/asof/test_session_contract.py` 的 `PROTECTED_BASELINE` 哈希 |
| `tests/r10` | 5 个实现漂移 | 59 passed / 5 failed | 修 `engine/v5/preprod.py` 的 `run_id` 参数 + 4 个信息量/纪律断言 |
| `tests/v1_3_acceptance` | 15 个失败集中在 `test_cfl_c016_fixes.py` | 120 passed / 15 failed / 5 skipped | 修非法 fixture `case_id`、`TriggerEvent(target=)` 接口、`_extract_candidates` 返回契约、缺失的 `templates/report-v1.3.md` |
```

同时补充一条快速门禁说明（依赖 T-102 的 marker）：

```markdown
# 快速门禁（排除 slow 用例）
python -m pytest -q -m "not slow"
```

## File Scope

**必须且只能是：**

```
pyproject.toml
AGENTS.md
```

（`pyproject.toml` 只允许动 `testpaths` 与 `addopts` 的 `--ignore` 行；**禁止**动
`markers`、`filterwarnings`、`minversion`、`python_files` 等。）

## Do NOT

- **禁止修改测试或验收脚本使其通过。**
- **禁止读取 File Scope 之外的文件**（勘察结论已在上面给全，无需再看 `tests/`）。
- **禁止解禁 `tests/v5`**（独立卡处理）。
- **禁止解禁或"顺手修复"那 4 个保留 ignore**——本次只登记，不修。
- **禁止用 `--ignore` 掩盖 T-101 的编码失败**（该失败必须已由 T-101 消除）。
- 禁止改动 `markers` 段（T-102 的产物）。
- 禁止执行 `git commit` / `checkout` / `stash` / `reset` / `clean`。

## Completion Criteria（可执行 + 期望退出码，全部需粘贴原始输出）

| # | 命令 | 期望 |
|---|---|---|
| 1 | `python -m pytest --collect-only -q 2>&1 \| tail -1` | **exit 0**，收集数 ≈ **3110–3250**（须远大于 229，并记录确切值） |
| 2 | `python -m pytest -q` | **exit 0**，`~3110 passed, 4 skipped`，**0 failed** |
| 3 | `python -m pytest -q -m "not slow"` | **exit 0**（T-102 机制可用；当前与 #2 等价） |
| 4 | `python -m pytest tests/evaluation -q -o addopts="--tb=no" --ignore=tests/evaluation 2>&1; echo $?` | 确认**不在**默认收集内：`pytest --collect-only -q \| grep -c "tests/evaluation"` → **0** |
| 5 | 同理核对 asof / r10 / v1_3_acceptance / v5 / track_e_smoke | 各自 `grep -c` 均为 **0** |
| 6 | `python -m pytest tests/track_e_smoke -q; echo $?` | 单独跑仍 `rc=5`，但**不影响**默认门禁（#2 已证） |
| 7 | `python -m pytest -q --ignore=tests/evaluation --ignore=tests/asof --ignore=tests/r10 --ignore=tests/v1_3_acceptance --ignore=tests/v5 --ignore=tests/track_e_smoke 2>&1 \| tail -1` | 与 #2 一致（验证 `addopts` 与显式 `--ignore` 不冲突） |
| 8 | `grep -c "tests/evaluation\|tests/asof\|tests/r10\|tests/v1_3_acceptance" AGENTS.md` | **exit 0**，计数 ≥ 4（登记块存在） |
| 9 | `git diff --stat` | 仅 `pyproject.toml`、`AGENTS.md`（及 `tasks/T-103/`） |
| 10 | `git diff pyproject.toml \| grep -E "^[-+].*(markers\|filterwarnings\|minversion)"` | **空输出 + exit 1**（证明未动 T-102 产物） |

### before / after 对照（必须写入 BRIEF.md）

| 指标 | before | after |
|---|---|---|
| `pytest --collect-only` 用例数 | 229 | `____`（预期 ~3110+） |
| `pytest -q` 耗时 | 11.73s | `____`（预期 ~14–16 分钟） |
| 门禁覆盖的测试文件数 | ~10+18 | `____`（预期 ~200+） |
| 仍被排除的目录 | 5 | 6（含 track_e_smoke） |

## 已知风险（评审必看）

1. **门禁从 12s 涨到 ~15 分钟**。这是有意的取舍（覆盖 90 个文件的静默缺口），
   但必须确认团队接受该频率；快速子集依赖 T-102 的 `slow` marker + 后续 v5 卡。
2. **`tests/track_e_smoke` 的 ignore 是新增的必要项**：遗漏会让 `pytest -q` 退出码
   恒非 0，是最容易踩的坑。
3. **`tests/conftest.py` 至今从未在门禁中生效**（根级测试未被收集）。本次收口后它
   首次真正加载，若其中 session fixture 有副作用，可能在 #2 暴露——属于**预期收益**，
   不是回归。

## Deliverables

- 改后的 `pyproject.toml`、`AGENTS.md`
- `tasks/T-103/BRIEF.md`：before/after 对照、10 项验收原始输出、风险评估
- 更新 `tasks/T-103/STATUS.md`
- **提交评审**：Review Level 3，需单独评审记录，不得自签自过
