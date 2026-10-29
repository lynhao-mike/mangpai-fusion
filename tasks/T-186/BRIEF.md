# T-186 BRIEF · P1′ 系统级断言评分器（一等指标）

- 状态：✅ **交付待验收**（只写评分器与合成测试；未跑真实 fresh-40、未改 engine / 规则 / hold-out / answers / 阈值 / 分母 / 其他 worktree；未 push main）
- 分支：`p1/assertion-eval`（worktree `..\mangpai-fusion-assertion`）
- 交付 commit：`c8fe7fc7`（评分器 + 测试 + BRIEF/STATUS 首版，4 files / +1626 −3）；
  其后只有一个 doc 补记提交（写这个 hash），HEAD 以 `git log -1` 为准。
- 基线：从 `f158014d`（= 当前 main tip，已含 `f003d216`）起
  —— 卡面写 `f003d216` 是写卡时的 main；按字面从 `f003d216` 起会缺 T-184 规格与 T-186 卡本身，故取其后继提交，`f003d216` 仍是祖先。
- 一句话：把「40 条方向断言 + 5 条 routing」逐条比对成**六个记账桶**，输出
  `total / correct / wrong / abstain_expected / abstain_unexpected / missing / routing_claims`、
  `precision / coverage / needs_judgment_rate / confident_error`、precision 与 coverage 的 Wilson 95% CI、
  分类型小表；判定只读预注册阈值（32/40、Wilson 下界>50、coverage≥75、confident_error≤10；kill<24；24–31 灰区），
  阈值在代码里是只读常量并由测试逐值钉死。

---

## 1 · 改动文件

| 文件 | 类型 | 规模 | 内容 |
|---|---|---:|---|
| `tools/p1_assertion_eval.py` | **新建** | 713 行 / 33,332 B | 独立评分器：`--answers --routing --system-output [--json] [--dev20-veto]`；六桶记账、一等指标、Wilson、分类型小表、预注册判定、`not_evaluated` 分母护栏 |
| `tests/tools/test_p1_assertion_eval.py` | **新建** | 574 行 / 26,882 B | 30 个测试函数（33 个用例）全合成 fixture：全对 / 全错 / abstain / missing / neutral / mutual / routing / 判定边界 / Wilson / 输入契约 / CLI / 可复现 |
| `tasks/T-186/BRIEF.md` | **新建** | 本文件 | 四字段简报 |
| `tasks/T-186/STATUS.md` | 更新 | — | 状态 + Execution Log + Blockers |

**未改**：`engine/**`、规则、`META/**`（answers / hold-out / prereg / baseline 一个字节都没动）、`docs/specs/party-direction-v1.md`、
`tests/` 既有文件、`pyproject.toml`、其他 worktree；未 `push`。

**刻意未写** `META/p1-fresh-40-routing-v1.json`：卡面 §1 说「T-185 将补」，但 T-185 的卡与 BRIEF 都没有 routing 这一项，
仓库里也没有这份文件。5 条真实 routing 例属于**标注层输入**（要从 `sources/` 选例 + 逐字 quote + 与 40 条不重叠），
代写等于替 T-185 临时补标注，会破坏「标注人/运行人分离 + 先 hash 后跑」的冻结纪律。详见 §3.1（**Blocker**）。

---

## 2 · 原始输出

### 2.1 目标门禁（卡面 §7）

```text
$ E:\Git hub\mangpai-fusion\.venv\Scripts\python.exe -m pytest tests/tools/test_p1_assertion_eval.py -q
.................................                                        [100%]
33 passed in 0.30s
```

### 2.2 无回归

```text
$ python -m pytest tests/tools -q
624 passed, 1 skipped in 112.77s        # skip 是 AGENTS.md 记录的 T-114 既有 skip

$ python -m pytest -q
1469 passed, 1 skipped, 1 warning in 135.20s
[exit code: 0]
```

### 2.3 真实 answers 的**只读装载检查**（不是跑分）

没有 system output、没有算任何分数；只验证评分器能解析 T-185 已交付的答案文件：

```text
loaded 40 cases; sha256 478d1a5959016b5c
mutual 1
actor!=a 0
mechanisms {'冲': 8, '合': 7, '穿': 6, '刑': 5, '墓': 5, '生': 4, '克': 3, '化': 2}
kinds {'制': 16, '合': 5, '墓': 5, '生': 4, '克': 3, '穿': 3, '化': 2, '冲': 1, '刑': 1}
missing source_ref 0
```

（分布与 T-185 `META/p1-fresh-40-v1.md` 一致；`mutual` 1 条 = PF-027；40 条 `actor == a`。）

### 2.4 合成场景（脚本在 `%TEMP%`，fixture 在 `%TEMP%\dsh-t186-synth\`，**非任何真实盘**）

**A. 全对（40/40，routing 全分流）**

```text
[P1′ 断言评分 T-186] total=45（main 40 + routing 5）
  buckets: correct=40 wrong=0 abstain_expected=5 abstain_unexpected=0 missing=0 routing_claims=0
  precision 40/40 = 100.0%  Wilson95 [91.2%, 100.0%]
  coverage  40/45 = 88.9%  Wilson95 [76.5%, 95.2%]
  needs_judgment_rate 5/45 = 11.1%  confident_error = 0.0%
  verdict: pass（全部门槛满足（correct≥32、Wilson 下界>50%、coverage≥75%、confident_error≤10%、dev-20 通过））；claim: direction_engine
  分类型 precision：克 5/5 | 生 5/5 | 化 5/5 | 墓 5/5 | 冲 5/5 | 合 5/5 | 穿 5/5 | 刑 5/5
  routing: abstain_expected=5 routing_claims=0 missing=0
```

**B. 32/40（confident_error=20%）**

```text
  buckets: correct=32 wrong=8 abstain_expected=5 abstain_unexpected=0 missing=0 routing_claims=0
  precision 32/40 = 80.0%  Wilson95 [65.2%, 89.5%]
  coverage  40/45 = 88.9%  Wilson95 [76.5%, 95.2%]
  needs_judgment_rate 5/45 = 11.1%  confident_error = 20.0%
  verdict: fail_secondary_gate（correct≥32 但次级门槛未满足：confident_error_at_most_10）；claim: direction_engine
```

**C. 全错（0/40，全部写反）**

```text
  buckets: correct=0 wrong=40 abstain_expected=5 abstain_unexpected=0 missing=0 routing_claims=0
  precision 0/40 = 0.0%  Wilson95 [0.0%, 8.8%]
  coverage  40/45 = 88.9%  Wilson95 [76.5%, 95.2%]
  needs_judgment_rate 5/45 = 11.1%  confident_error = 100.0%
  verdict: kill（correct=0 < 24（卡 §3：kill））；claim: direction_engine
```

**D. 全对 + routing 5 条全部硬给方向（routing 单列）**

```text
  buckets: correct=40 wrong=0 abstain_expected=0 abstain_unexpected=0 missing=0 routing_claims=5
  precision 40/40 = 100.0%  Wilson95 [91.2%, 100.0%]
  coverage  40/45 = 88.9%  Wilson95 [76.5%, 95.2%]
  needs_judgment_rate 0/45 = 0.0%  confident_error = 0.0%
  verdict: pass（…）；claim: direction_engine
  routing: abstain_expected=0 routing_claims=5 missing=0
```

→ routing 的错**不进 precision 分母**（卡 §4），但也**不在卡 §3 的 pass 门槛内**，所以 D 仍 pass。
这是卡片字面口径，已写进 `verdict.notes` 并用测试钉住（`test_routing_claims_do_not_change_verdict_per_card`）；
要把分流正确率设成门槛，须改卡（见 §3.3）。

**E. 缺 routing 文件**

```text
[p1_assertion_eval] 输入不合口径：routing 文件不存在：…\no-routing.json
exit_code = 2
```

### 2.5 一等字段清单（`--json` 的 `metrics`）

`total`、`correct`、`wrong`、`abstain_expected`、`abstain_unexpected`、`missing`、`routing_claims`、
`precision{numerator,denominator,value,percent,wilson95{lower,upper}}`、`coverage{…}`、
`needs_judgment_rate{…}`、`confident_error{…}`；另有 `by_kind[]`（分类型小表）、`routing{}`（routing 单列）、
`verdict{gates,reasons,claim,notes}`、`prereg_thresholds`（本次实际使用的只读阈值）。

### 2.6 记账恒等式（工具内自检 + 测试复核）

```text
total == correct + wrong + abstain_expected + abstain_unexpected + missing + routing_claims
```

`run()` 内部 `_check_accounting` 不成立即抛 `ValueError`（退出码 2），不会静默出分。

### 2.7 git

```text
$ git branch --show-current
p1/assertion-eval
$ git log --oneline -2
c8fe7fc7 feat(tools): P1′ 系统级断言评分器（T-186）+ 合成测试
f158014d feat(spec): 党势方向预注册 v1（T-184）；派 T-186 系统级评分器
```

---

## 3 · 未完成与风险

### 3.1 Blocker：routing 输入缺失（需要中枢拍板）

| 项 | 现状 |
|---|---|
| 卡面 §1 | `META/p1-fresh-40-routing-v1.json`（**T-185 将补**）：5 条 `expected_direction=needs_judgment` |
| 实际 | 文件不存在；`tasks/T-185/PROMPT.md` 与 `BRIEF.md` 都没有 routing 任务；T-185 已交付 40 条答案，不含 routing |
| 我的处理 | 不代写真实标注；工具在缺文件时 **退出码 2** 并报明确原因；routing 条数 ≠5 时 `verdict=not_evaluated`（不给 pass/kill） |
| 需要中枢 | ①派新卡或扩 T-185 补 5 条（schema 见 §4.2，测试 fixture 可直接照抄格式）并给 hash；②或明确「本轮只跑 40 条」——那必须改卡改分母，本工具不擅自改 |

### 3.2 风险：coverage 分母按卡面字面取 45（算术后果，不是 bug）

`coverage = (correct + wrong) / total`，`total = 40 + 5 = 45`（卡 §2.1 + §2.4）。
所以 routing 的正确 abstain 永远不进分子 → **满分运行 coverage = 40/45 = 88.9%**；pass 要求 ≥75% → 已判 ≥34 条。
推论：`correct = 32` 且 `wrong = 0` 时 coverage = 32/45 = 71.1% < 75%，**仍然不 pass**；
32 分要 pass 至少还要 2 条 wrong（34/45 = 75.6%）。若中枢本意是「40 分母」，须改卡，代码不改。

### 3.3 风险：routing 正确率不在 pass 门槛内（卡面字面）

见 §2.4 D：40/40 全对 + routing 5 条全部硬给方向仍判 `pass`，只单列 `routing_claims=5`。
我没有自创「routing 必须 ≥4/5」之类的门槛（那是发明阈值）。**这可能是卡面缺口**，需要中枢决定是否补预注册门槛（改卡，不改代码）。

### 3.4 契约风险：系统输出的方向语义

评分器约定：系统输出每条 `a` = **它自报的施力端**，`direction="actor→target"` 意为「我的 a 端施力于 b 端」，
与 `docs/specs/party-direction-v1.md` §4.2 的 `palace.actor 端施力于 palace.target 端` 同义。
未来 runner（T-183 之后）必须按此约定输出；若 runner 把答案顺序原样抄进 a/b、却用 `direction` 表达别的意思，
整卷会被读成 `reversed`。**这一条要写进 runner 的任务卡。**

### 3.5 判分边界（已写进模块 docstring，避免事后争议）

1. 端点不是答案那一对 → `wrong / endpoint_mismatch`（不静默 drop，也不当 missing）；
2. 答案 `mutual` 与系统单向互串 → `wrong`（两种理由分开记）；
3. `needs_judgment` 一律 `abstain_*`，**不记 ok/wrong**（卡 §2.2 + 规格 §5.2）；
4. `kind` 只回显、不参与判分（本卷判方向；kind 映射是另一张尺子）；
5. 系统输出多出未登记 case、重复 case、未登记 `direction` → 一律 `ValueError`（退出码 2），不静默兜底。

### 3.6 未做

- **未跑真实 fresh-40**（无 system output；也不会去造）。本 BRIEF 的所有数字都来自合成 fixture 或只读装载检查。
- **未实现引擎侧**党势/断言输出——那是 T-183/T-187 之后的事。
- **未碰 dev-20**：`dev-20 否决/不变量全过` 无法由本工具自证，作为外部门槛用 `--dev20-veto passed` 传进来；默认 `unknown` → 最多判 `fail_secondary_gate`，不会误判 pass。

### 3.7 需要中枢拍板（汇总）

1. routing 5 条由谁写、何时 hash（§3.1）；
2. coverage 分母 45 还是 40（§3.2）；
3. 是否给 routing 正确率加 pass 门槛（§3.3，须改卡）；
4. 系统输出方向语义确认（§3.4）。

---

## 4 · 下游须知

### 4.1 中枢怎么跑（真实运行）

```bash
python -m tools.p1_assertion_eval \
  --answers META/p1-fresh-40-answers-v1.json \
  --routing META/p1-fresh-40-routing-v1.json \
  --system-output <runner 产出的 run.json> \
  --dev20-veto passed \
  --json
```

- `--dev20-veto` 不传 = `unknown` → 最高只能 `fail_secondary_gate`；`passed` 才会出 `pass`；
- 退出码 0 = 评完（**kill 也是 0**）；2 = 输入不合口径（缺文件 / schema 错 / case 对不上 / 记账不平）；
- 产物不含时间戳，同一输入两次运行逐字节一致。

### 4.2 routing 文件 schema（缺这份就退出 2）

```json
{
  "schema_version": "p1-fresh-40-routing/v1",
  "case_count": 5,
  "cases": [
    {"case_id": "PR-01", "a": "酉", "b": "戌", "kind": "制", "mechanism": "穿",
     "expected_direction": "needs_judgment", "source_ref": "<path>:L<n>", "quote": "<逐字>"}
  ]
}
```

硬约束：`expected_direction` **只能** `needs_judgment`（别的值直接报错）；`case_id` 不得与 40 条答案重叠；
条数必须 5（否则 `verdict=not_evaluated`）；建议 `a`/`b`/`kind`/`mechanism`/`source_ref`/`quote` 与 40 条同格式。

### 4.3 系统输出 schema

```json
{"cases": [
  {"case_id": "PF-001", "a": "巳", "b": "亥", "kind": "制",
   "direction": "actor→target", "edge_id": "e012", "source_ref": "<path>:L<n>"}
]}
```

- `direction ∈ {actor→target, mutual, needs_judgment}`；`a` = 系统自报施力端（见 §3.4）；
- 一条断言一条输出；case 集合必须与 answers∪routing 一致（多出即报错，缺的记 `missing`）。

### 4.4 读结果的顺序

1. `verdict.prereg_denominators_met`（false 说明分母不是 40+5，**不得**引用 pass/kill）；
2. 六桶 + 恒等式；
3. `precision`（分子/分母 + Wilson 95%）、`coverage`（分母是 total）、`confident_error`；
4. `by_kind` 找是哪一类拉低；
5. `routing` 看分流是否退化成「乱给方向」；
6. `verdict.claim`：`needs_judgment_rate > 50%` 只准宣称「分流引擎」。

### 4.5 阈值只读

`PREREG_THRESHOLDS`（40 / 5 / 32 / 0.50 / 0.75 / 0.10 / 24 / [24,31] / 0.50）全部写死在模块常量里，
`test_prereg_thresholds_pinned_to_card` 逐值钉死：**改阈值 = 测试红**。判定只读这份常量，不读答案分布。

### 4.6 别做

- 不要把本 BRIEF §2.4 的合成数字当 P1 结果引用（fixture 不是真实盘）；
- 不要为了 `pass` 去改 `coverage` 分母 / 把 routing 计入 precision / 把 abstain 记 ok；
- 不要把 `missing` 当作 `wrong` 或从分母里剔掉（卡面要求单列）。

---

## 5 · 中枢可直接核

| 卡面验收项 | 命令 / 判据 |
|---|---|
| 只写评分器 + 合成测试 | `git show --stat`：只有 `tools/p1_assertion_eval.py` + `tests/tools/test_p1_assertion_eval.py`（+ 本 BRIEF/STATUS） |
| 0 failed | `python -m pytest tests/tools/test_p1_assertion_eval.py -q` → 33 passed |
| 一等字段齐全 | `--json` 的 `metrics` 键 + `by_kind` + `routing`（见 §2.5） |
| routing 单列、abstain 不记 ok/wrong、missing 单列 | §2.4 A/B/C/D + `test_routing_claims_do_not_enter_precision` / `test_abstain_on_main_is_unexpected_not_ok_or_wrong` / `test_missing_is_counted_separately` |
| 不改阈值/分母 | `PREREG_THRESHOLDS` + `test_prereg_thresholds_pinned_to_card`；`git diff` 无 `META/**` |
| 不跑真实数据 | `git show --stat` 无 `META/**`；工具不 import engine、不读 `sources/`；测试全用 tmp_path fixture |
| 判定边界 | `test_verdict_boundaries`（23 kill / 24、31 灰区 / 32 次级门槛）+ `test_pass_requires_dev20_attestation` |
