# T-150 · 度量契约 v1：触发器/结果分离 + 预注册 + 尺子自检

- 状态：🔵 Ready for Execution
- 优先级：**P0（最高，阻塞后续一切测量）**
- 创建：2026-10-28（中枢）
- 依据：`docs/reviews/verdict-chatgpt6.md` §4.1、§5 第一步；`docs/reviews/direction-decisions-v1.md` §3.1①
- 前置：无。本卡不依赖 T-151。

## 0. 一句话

把「结构不存在」和「结构存在但失败」分开，输出 `triggered`（触发与否）与 `outcome`（结果成败）两个字段；所有评测只在 `triggered=True` 的集合内计分；口径先写进预注册文件，跑分工具缺预注册即拒绝运行（fail-closed，失败即关闭）。

## 1. 已核实现状（不要重复验证，直接改）

- `evaluate_claim` 现在返回 `state ∈ {candidate, rejected, needs_fact, evidence_only}`。
- 它先算 `invalidators`（反证条件，`ir.py:162-167`），再算 `preconditions`（前置条件）；「反证成立」与「前置不成立」都压成 `rejected`，**这是要修的核心**。
- 三值逻辑：`True / False / None(unknown)`，`unknown` 不得折叠成 `False` 或 `True`（`ir.py:3`）。
- `condition_ir` 在 `engine/` 内零调用，只被测试与 4 个工具 import。**本卡不改变这一点**。
- 原子共 46 个；**本卡不改任何原子语义**。

## 2. 契约字段（改 `engine/claims/condition_ir/ir.py`）

在 `evaluate_claim` 返回值中新增：

- `triggered`: `bool | None` —— 结构是否触发。
- `outcome`: `"success" | "fail" | "unknown"` —— 结构触发后，断语结论成立与否。

保留 `state`、`value`、`reason`、`bindings`、`failed_atoms`、`unknown_facts`、`near_miss`、`framework`，语义不变（向后兼容）。

### 2.1 判定表（必须逐行覆盖测试）

| # | 情形 | triggered | outcome | state（保持旧值） |
|---|---|---|---|---|
| 1 | `preconditions=False` | `False` | `unknown` | `rejected` |
| 2 | `preconditions=None` | `None` | `unknown` | `needs_fact` |
| 3 | `requires_pair`，配对命题=False | `False` | `unknown` | `rejected` |
| 4 | `requires_pair`，配对命题=None 或缺失 | `None` | `unknown` | `evidence_only` |
| 5 | `requires_school_frame`，`frame_atom` 缺失或求值=None | `None` | `unknown` | `evidence_only` |
| 6 | `requires_school_frame`，`frame_atom` 求值=False | `False` | `unknown` | `evidence_only` |
| 7 | 前置+框架成立，`invalidator=True` | `True` | `fail` | `rejected` |
| 8 | 前置+框架成立，`invalidator=False` | `True` | `success` | `candidate` |
| 9 | 前置+框架成立，`invalidator=None` | `True` | `unknown` | `candidate` |

### 2.2 硬规则

1. **先算 `preconditions` 再算 `invalidators`**（否则拿不到 `triggered`）；但 `state` 按旧优先级合成，**既有测试断言一条都不许改**。
2. `triggered` 不是 `True` 时，`outcome` 必须是 `unknown`。禁止出现 `triggered=False` + `outcome=fail` 这种组合。
3. `preconditions=None` → `triggered=None`，不许当 `False`。
4. `invalidator=None` → `outcome="unknown"`，不许当 `success`。
5. 情形 1/2 保持旧短路行为：前置不成立时**不**再求值 `invalidators`。

### 2.3 更新契约文档

`engine/contracts/23-claim-condition-protocol-v1.md` 增加本节判定表与字段说明，版本号升一位（v1.3 → v1.4，以文件当前版本为准）。

## 3. 评测器（`engine/claims/metrics.py` + `tools/claim_metric.py`）

新增纯函数（无 I/O、无全局状态）：

```text
score(cases: list[dict], protocol: dict) -> dict
```

`cases` 每例至少含：

```json
{"case_id": "...", "claim_id": "...", "branch": "self_controls",
 "triggered": true, "outcome": "success",
 "prediction_letters": ["B"], "answer_letter": "B"}
```

计分口径（写死，不许中途改）：

- **scored 集** = `triggered is True` 且 `prediction_letters` 非空。
- `correct` = `answer_letter ∈ prediction_letters`。
- 必须报告：`n_total` / `n_scored` / `n_correct` / `n_abstain`（触发但预测为空）/ `n_not_triggered` / `n_missing_answer`。
- `accuracy = n_correct / n_scored`；**`n_scored == 0` 必须抛错**（CLI 退出码 2），禁止 0/0 静默出分。
- `baseline_single`：同一 scored 集上出现最多的**单个字母**的命中率（含该字母名）。这是**判定基线**。
- `baseline_same_k`：每例按预测字母数 `k`，取 scored 集上频率最高的 `k` 个字母（并列按字母序）作为常量预测，算命中率。这是**乐观上界，只作参考，不参与判定**（防止「预测 2 个字母占便宜」）。
- `wilson_ci_95`：[下界, 上界]，保留 4 位小数。
- `by_branch`：按 `branch` 字段分组，各报 `n / correct / accuracy`。
- 确定性：按 `case_id` 排序；浮点保留 4 位；输出不含当前时间。同一输入两次运行必须逐字节一致。
- 输出附带 `input_sha256`（cases 规范化 JSON 的 SHA-256）。

预注册文件（YAML 或 JSON 均可，建议 `META/eval-protocols/<id>.yaml`）必填字段：

```text
protocol_id, claim_id, frozen_at, commit,
trigger_definition, direction_rule,
label_map（标签 -> 字母集）, prediction_rule（分支 -> 标签）,
scored_set_rule, baseline, decision_rule
```

`tools/claim_metric.py`：

- `--protocol <file> --cases <file> [--json]` → 缺文件、缺字段、scored 集为空均退出码 2；正常退出码 0。
- `--self-check` → 内置玩具集，手算断言精确值，退出码 0/1。玩具集必须覆盖：单字母预测、多字母预测、弃权、未触发、缺答案、0 分母报错。

## 4. 尺子与映射分离（便宜且必须做）

把 `tools/tiekoulu_eval.py` 里的 `PREDICTION_MAP` 与 `NO_MAP_REASON` 移到 **`META/claim-instrument-map-v1.yaml`**，工具改为读该文件。

- **只搬家，不改评测逻辑、不改阈值、不改题**。
- 回归：搬家前后 `python -m tools.tiekoulu_eval` 输出数字一致（时间戳字段除外）。先备份已提交的 `META/tiekoulu-eval-v1.json` 到 `%TEMP%`，跑完逐字段比对，把比对结果写进 BRIEF。
- 若时间不够：**优先保 §2 + §3 + §5**，本节可降级为下一张卡，但必须在 BRIEF 的「未完成与风险」写明。

## 5. 测试（新建 `tests/claims/test_claim_contract.py`）

只许新建，**不许修改任何既有测试文件或断言**。至少覆盖：

1. §2.1 判定表 9 行，逐行断言 `triggered / outcome / state`；
2. 负对照：构造 `preconditions` 含未知原子 → `triggered=None`，且断言它不是 `False`；
3. 计分器玩具集：3 例手算（含一例多字母预测），断言 `n_scored / n_correct / accuracy / baseline_single / baseline_same_k`;
4. 预注册缺失或字段缺失 → 退出码 2（用 subprocess 或直接调 CLI 函数）；
5. `n_scored==0` → 抛错。

## 6. File Scope

**允许修改**

- `engine/claims/condition_ir/ir.py`
- `engine/claims/condition_ir/__init__.py`（仅导出，如需要）
- `engine/contracts/23-claim-condition-protocol-v1.md`
- `tools/tiekoulu_eval.py`（仅改 `PREDICTION_MAP` / `NO_MAP_REASON` 的读取）

**允许新建**

- `engine/claims/metrics.py`
- `tools/claim_metric.py`
- `META/eval-protocol-v1.md`（预注册格式说明，不是具体协议）
- `META/claim-instrument-map-v1.yaml`
- `tests/claims/test_claim_contract.py`

**只读**

- `engine/claims/condition_ir/atoms.py`（一个字节都不许改）
- `theory/claims/conditions-v2/pilot-20.yaml`
- `META/tiekoulu-eval-v1.json`（对照用）
- `tiekoulu_1507_to_1428.json`

**禁止**

- `theory/_ir/`、`sources/`、`theory/raw/`、`theory/yang/` 等原文语料
- 其他 `engine/` 文件、`pyproject.toml`、`requirements*.txt`
- 修改既有测试断言来变绿
- `git commit / push / checkout / stash / reset / clean`

## 7. 验收（中枢亲自跑，Worker 自报不算数）

```bash
.venv\Scripts\python.exe -m pytest -q
# 要求：0 failed；passed >= 1043；skipped 仍为 1（T-114 过渡 skip）

.venv\Scripts\python.exe -m tools.claim_metric --self-check
# 退出码 0，打印手算值

.venv\Scripts\python.exe -m pytest tests/claims/test_claim_contract.py -q -o addopts="-ra --tb=short"
# 全绿

.venv\Scripts\python.exe -m tools.tiekoulu_eval
# 退出码 0；数字与已提交 META/tiekoulu-eval-v1.json 一致（时间戳除外）
```

中枢还会额外检查：

- 同一命令跑两次，输出逐字节一致（`Get-FileHash`）。
- 负对照现场演示：未知事实 → `triggered=None`，不是 `False`。
- `PREDICTION_MAP` 已不在 `tools/tiekoulu_eval.py` 中（grep）。
- 读 diff：没有为了让测试变绿而放宽任何断言。

## 8. 回报格式（写 `tasks/T-150/BRIEF.md` + `tasks/T-150/STATUS.md`）

四个字段，缺一不可：

1. **改动文件**（逐个列出，说明性质）
2. **原始输出**（上面四条命令的完整输出，含退出码）
3. **未完成与风险**（含 §4 是否降级）
4. **下游须知**（`triggered`/`outcome` 的准确语义；哪些组合不可能出现）

`STATUS.md` 追加 Execution Log 一行一步。

## 9. 发现卡有问题时

写进 `BRIEF.md` 的 Blockers，并在 `STATUS.md` 记录。**不许自行扩大 File Scope**。判据若确实错了，先证明它错了（原文锚点或代码依据），再改，并在 BRIEF 写清证据。

## 10. Amendments（中枢裁决，2026-10-28 21:55）

1. **§3 scored 集补一条「且有 `answer_letter`」**。缺答案的案例记 `n_missing_answer`，单列、**不进分母**；四桶互斥可加：
   `n_total = n_scored + n_abstain + n_not_triggered + n_missing_answer`。
   理由：数据缺陷不是断语错误，计入分母会系统性压低准确率且无法归因。实现已在 `engine/claims/metrics.py` 与 `META/eval-protocol-v1.md` 落定。
2. **§2.2 硬规则 1 的语义后果中枢确认接受**：`invalidators` 成立 + `preconditions` 未知，v1.3 判 `rejected`、v1.4 判 `needs_fact`。
   理由是「未知不得被失效条件折叠成否定」。实测 36 期 × 12 条断语的 `state` 分布与提交版逐字节一致（`META/tiekoulu-eval-v1.json` 无 diff），影响 0 期。
3. **T-151 集成接口**：78 例的 `triggered` 一律 `true`（`no_ke` 是触发后弃权，不是未触发），`branch=direction`，`outcome=unknown`（本条未建模 invalidator）。中枢已另行通知 T-151。
4. 契约 23 版本升到 **v1.4**，原子表仍 v1.2；本次不新增、不改动任何原子。
