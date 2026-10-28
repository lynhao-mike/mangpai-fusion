# T-150 STATUS

- 状态：✅ **已验收**（2026-10-28，中枢亲自跑命令）
- 执行者：子代理 A
- 任务卡：`tasks/T-150/PROMPT.md`
- 简报：`tasks/T-150/BRIEF.md`
- 验收：中枢亲自跑命令，Worker 自报不算数

## 改动概览

| 文件 | 性质 |
|---|---|
| `engine/claims/condition_ir/ir.py` | `evaluate_claim` 先 `preconditions` 后 `invalidators`；新增 `triggered` / `outcome`；旧字段语义不变 |
| `engine/contracts/23-claim-condition-protocol-v1.md` | 升 v1.4；§5.1 判定表 9 行 + 硬规则；补登记 v1.3（T-149 漏记）与 v1.4 |
| `engine/claims/metrics.py` | 新建：纯函数 `score()` / `validate_protocol()` / `wilson_ci_95()` |
| `tools/claim_metric.py` | 新建：CLI `--protocol/--cases/--json` + `--self-check`，fail-closed 退出码 2 |
| `META/eval-protocol-v1.md` | 新建：预注册格式说明（不是具体协议） |
| `META/claim-instrument-map-v1.yaml` | 新建：`PREDICTION_MAP` / `NO_MAP_REASON` 原样搬出 |
| `tools/tiekoulu_eval.py` | 仅改映射读取（`load_instrument_map()`）；逻辑/阈值/题未动 |
| `tests/claims/test_claim_contract.py` | 新建 23 条测试 |

未改：`atoms.py`（0 字节）、既有测试与断言、`theory/_ir/`、`sources/`、`theory/raw/`、`theory/claims/`、
`pyproject.toml`。无 `git commit / push / checkout / stash / reset / clean`。

## 自测（实测，中枢请重跑）

```text
.venv\Scripts\python.exe -m pytest -q
→ 1066 passed, 1 skipped, 1 warning in 94.26s   EXIT=0
  （动工前基线 1043 passed / 1 skipped；skip = T-114 过渡措施，非本卡引入；
   收尾前共跑两次全量：86.36s / 94.26s，两次计数一致）

.venv\Scripts\python.exe -m pytest tests/claims/test_claim_contract.py -q -o addopts="-ra --tb=short"
→ 23 passed in 0.37s   EXIT=0

.venv\Scripts\python.exe -m tools.claim_metric --self-check
→ self-check PASSED：全部手算断言一致   EXIT=0

.venv\Scripts\python.exe -m tools.tiekoulu_eval
→ EXIT=0；产物 SHA256 = 8381BBF6…（搬家前备份同为此值），逐字段比对差异 0
```

## Blockers

无。

## Execution Log

| 时间 | 动作 |
|---|---|
| 21:35 | 中枢建卡并派发；File Scope 与 T-151/T-148 无重叠 |
| 21:36 | Worker 读 `AGENTS.md`、`PROMPT.md`、`ir.py`、`atoms.py`（只读）、`rule_loader.py`、`tiekoulu_eval.py`、契约 23；跑基线 `pytest -q` = 1043 passed / 1 skipped |
| 21:38 | 备份 `META/tiekoulu-eval-v1.json` 到 `%TEMP%`；基线 `tiekoulu_eval` 退出码 0，哈希 `8381BBF6…` |
| 21:40 | §2 `ir.py`：求值顺序重排 + `triggered`/`outcome`；`pytest tests/claims` = 273 passed（既有断言未动） |
| 21:41 | §2.3 契约 23 升 `v1.4`：§5.1 判定表 9 行、硬规则 5 条、`state` 判定顺序重写；§九补登记 v1.3/v1.4 |
| 21:42 | §3 新建 `engine/claims/metrics.py`（纯函数计分）与 `tools/claim_metric.py`（CLI + self-check） |
| 21:43 | §3 新建 `META/eval-protocol-v1.md`（预注册格式）；`--self-check` 退出码 0、手算值全中 |
| 21:44 | §4 映射搬家到 `META/claim-instrument-map-v1.yaml`；`tiekoulu_eval` 前后逐字节一致、逐字段差异 0、连跑两次 stdout 哈希一致 |
| 21:45 | §5 新建 `tests/claims/test_claim_contract.py`（23 条：判定表 9 行 / 负对照 / 计分手算 / fail-closed / 0 分母 / 映射护栏） |
| 21:46 | 全量 `pytest -q` = 1066 passed / 1 skipped；现场负对照：未知前置 → `triggered=None`（不是 False） |
| 21:50 | 写 `tasks/T-150/BRIEF.md` 四字段 + 本执行日志；回报中枢 |
| 21:52 | 中枢独立验收：`test_claim_contract.py` 23 passed EXIT=0；`claim_metric --self-check` PASSED EXIT=0；负对照 7 passed；`tiekoulu_eval` EXIT=0 且 `META/tiekoulu-eval-v1.json` 无 diff |
| 21:54 | 中枢独立跑全量：`pytest -q` → **1066 passed, 1 skipped, 0 failed, EXIT=0**（1043 基线 + 23 新测试） |
| 21:55 | 中枢裁决两条口径：缺答案不入分母、单列 `n_missing_answer`；state 顺序变更接受（实测影响 0 期）。写入 `PROMPT.md` §10 |
| 21:58 | 中枢提交（仅暂存 T-150 相关文件） |
