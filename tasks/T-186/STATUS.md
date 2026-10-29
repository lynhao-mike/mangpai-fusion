# T-186 STATUS

- 状态：🟡 **交付待验收**（2026-10-29 15:30，子代理；中枢亲自跑）
- 执行者：子代理 AI（评分器）
- 任务卡：`tasks/T-186/PROMPT.md`
- 分支：`p1/assertion-eval`（worktree `..\mangpai-fusion-assertion`，基线 `f158014d`，含 `f003d216`）
- 验收：中枢亲自跑 `pytest tests/tools/test_p1_assertion_eval.py -q`；不跑真实 fresh-40
- Blockers：**routing 输入缺失**（见下）

## 交付物

| 文件 | 类型 | 规模 |
|---|---|---:|
| `tools/p1_assertion_eval.py` | 新建 | 713 行 / 33,332 B |
| `tests/tools/test_p1_assertion_eval.py` | 新建 | 574 行 / 26,882 B（30 测试函数 / 33 用例） |
| `tasks/T-186/BRIEF.md` | 新建 | 四字段简报 |
| `tasks/T-186/STATUS.md` | 更新（本文件） | 状态 + 日志 + Blockers |

## 口径要点（验收先看这五条）

1. **六桶记账**：`total == correct + wrong + abstain_expected + abstain_unexpected + missing + routing_claims`
   （routing 例被硬给方向记 `routing_claims`，**不进 precision 分母**）；`run()` 内部自检，不平即退出码 2。
2. **一等指标照抄卡 §2**：`precision = correct/(correct+wrong)`、`coverage = (correct+wrong)/total`（total=45）、
   `needs_judgment_rate = 实际 needs_judgment/total`、`confident_error = wrong/(correct+wrong)`；
   precision / coverage 各一个 Wilson 95% CI；分类型小表按 克/生/化/墓/冲/合/穿/刑。
3. **abstain 不记 ok/wrong**：main 上 `needs_judgment` → `abstain_unexpected`；routing 上 → `abstain_expected`。
4. **阈值只读**：`PREREG_THRESHOLDS`（40/5/32/0.50/0.75/0.10/24/[24,31]/0.50）写死 + 测试逐值钉死；
     `dev-20 否决/不变量` 用 `--dev20-veto passed` 外证，默认 `unknown` 不判 pass。
5. **分母护栏**：main 或 routing 条数不等于 40/5 → `verdict=not_evaluated`，合成 fixture 永远不会被判 pass/kill。

## Execution Log

| 时间 | 动作 |
|---|---|
| 15:10 | 中枢建卡并派发；与 T-183/T-185 并行 |
| 15:13 | 读卡 + 规格 §2/§4/§5.2 + prereg + T-184 BRIEF + T-185 答案；确认 `META/p1-fresh-40-routing-v1.json` 不存在 |
| 15:14 | 建 worktree `..\mangpai-fusion-assertion` + 分支 `p1/assertion-eval`（从 `f158014d`，含 `f003d216`） |
| 15:15–15:24 | 写 `tools/p1_assertion_eval.py`：六桶、一等指标、Wilson、分类型表、只读阈值判定、`not_evaluated` 护栏、CLI |
| 15:24–15:27 | 写 `tests/tools/test_p1_assertion_eval.py`：30 函数 / 33 用例（全对/全错/abstain/missing/neutral/mutual/routing/边界/CLI） |
| 15:27 | `pytest tests/tools/test_p1_assertion_eval.py -q` → **33 passed** |
| 15:28 | `pytest tests/tools -q` → 624 passed, 1 skipped（T-114 既有 skip） |
| 15:29 | `pytest -q` → **1469 passed, 1 skipped, 1 warning**，退出码 0 |
| 15:29 | 只读装载真实 answers（无 system output、未算分）：40 cases / mutual 1 / actor==a 40 / 8 类 mechanism 全覆盖 |
| 15:30 | 合成场景 A–E 跑通（BRIEF §2.4）；写 BRIEF + 本 STATUS |
| 15:31 | commit `c8fe7fc7`（4 files / +1626 −3）；分支 `p1/assertion-eval`（基线 `f158014d`）；未 push |

## Blockers

**BLOCKER-1（输入缺失，需中枢拍板）**：`META/p1-fresh-40-routing-v1.json` 不存在。
卡 §1 写「T-185 将补」，但 T-185 的 `PROMPT.md` / `BRIEF.md` 都没有 routing 任务，其交付 40 条答案不含 routing。
未代写真实 5 条：那属于标注层（选例 + 逐字 quote + 与 40 条不重叠 + 先 hash 后跑），代写会破坏标注/运行分离。
工具行为：缺文件 → 退出码 2；routing 条数 ≠5 → `verdict=not_evaluated`。

**待拍板的口径（不影响本工具可跑，但影响真实运行的解释）**：

1. **coverage 分母**：按卡 §2.4 字面取 total=45，满分运行 coverage=40/45=88.9%；`correct=32` 且零错时
   coverage=71.1%<75%，仍不 pass（32 分要 pass 至少还要 2 条 wrong）。若本意是 40 分母，须改卡。
2. **routing 未进 pass 门槛**：卡 §3 的 pass 条件不含 routing 正确率，故「40/40 + routing 全硬给方向」仍 pass
   （只在 `routing_claims` 单列）。已按字面实现并用测试钉住；要设门槛须改卡。
3. **系统输出方向语义**：约定 `a` = 系统自报施力端，`direction=actor→target` = a 端施力于 b 端（同 prereg §4.2）；
   未来 runner 必须按此输出，否则整卷会被读成 reversed。此条须写进 runner 任务卡。

## 未做

- **未跑真实 fresh-40**（无 system output，也不伪造）；BRIEF 内所有分数均来自合成 fixture。
- 未改 `engine/**`、规则、`META/**`（answers / hold-out / prereg）、`docs/specs/party-direction-v1.md`、既有测试、阈值、分母。
- 未 push main、未碰其他 worktree；`dev-20` 门槛未自证（外部门槛）。
