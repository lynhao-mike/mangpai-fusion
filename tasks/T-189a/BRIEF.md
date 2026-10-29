# T-189a BRIEF · scorer v2 核心（三层 + 地址/字 + nj=miss + 引文 + Wilson）

- 状态：✅ **交付待验收**（只写评分器与合成测试；未做 B1/B2、chart 聚类、3 次一致、T-187 回归、真实 anchor-60；未改 engine / 答案 / 阈值；未 push main）
- 分支：`p1/assertion-v2a`（worktree `..\mangpai-fusion-av2a`）
- 代码提交：`654b11e5`（2 files / +1103 −0）；随后只有一个 BRIEF/STATUS 文档提交，HEAD 以 `git log -1` 为准。
- 基线说明：卡面写 `46c00c3a`。分支先按要求从 `46c00c3a` 起，再 rebase 到其后继 `457c3cdc`（只加 T-189 卡与派活日志）：否则本 worktree 没有 `tasks/T-189a/PROMPT.md`，且我新建的 `STATUS.md` 会与中枢同名 add/add 冲突。`46c00c3a` 仍是祖先，代码差异只有下列 2 个新文件。
- 一句话：把 **fixed 10 / dynamic 40 / ambiguous 10** 三层逐条比对成 `correct / wrong / nj / quote_fail / missing`，
  地址与地支字双向归一，dynamic 上 `nj=miss`，ambiguous 要求 `needs_judgment` + `conflict_quotes[2]` 逐字行内，
  输出 `correct/total`、`precision`、`delivered`、Wilson 95% CI 与分类型小表；**不出 pass/kill**（阈值判定与 B1/B2/cluster/3-run 归 T-189b）。

---

## 1 · 改动文件

| 文件 | 类型 | 规模 | 内容 |
|---|---|---:|---|
| `tools/p1_assertion_eval_v2.py` | **新建** | 610 行 | 独立评分器：`--answers --system-output [--json]`；三层分录、地址/字归一、nj=miss、双引文逐字行内、指标 + Wilson、by_kind、输入契约护栏、记账自检 |
| `tests/tools/test_p1_assertion_eval_v2.py` | **新建** | 493 行 | 19 个测试函数（24 个用例）全合成 fixture：全对 / 32-8 / 全错 / nj=miss / ambiguous 引文 5 变体 / 地址字 6 参数 / 输入契约 5 项 / CLI |
| `tasks/T-189a/BRIEF.md` | **新建** | 本文件 | 四字段简报 |
| `tasks/T-189a/STATUS.md` | 更新 | — | 状态 + Execution Log + Blockers |

**未改**：`engine/**`、`META/**`（答案 / 阈值 / hold-out 零字节）、`docs/**`、既有 `tests/`、`pyproject.toml`；未 `push`。

### 1.1 三层字段（`--json`）

`layers.fixed` / `layers.dynamic`：`total / correct / wrong / nj / missing / miss（=nj+missing）/ miss_rate / delivered（=correct+wrong，nj 不算交付）/ delivered_rate / correct_over_total / precision / all_correct`；
`layers.ambiguous`：`total / correct / wrong / quote_fail / missing / delivered（=total−missing）/ delivered_rate / correct_over_total / both_quotes / precision / quotes_checked / quotes_verbatim / quote_violations / quote_violation_rate`；
顶层：`counts`（三层条数 + `prereg` 10/40/10 + `denominators_met` / `total_met`）、`layers`、`by_kind[]`（`layer+kind` 不混层）、`cases[]`（每条的 `status / reason / observed_direction / quotes[].found`）。
`precision = correct / delivered`；Wilson 95% 落在每条 metric 的 `wilson95`（n=0 时为 `None`，不编造区间）。

---

## 2 · 原始输出

### 2.1 目标门禁（卡面 §2）

```text
$ E:\Git hub\mangpai-fusion\.venv\Scripts\python.exe -m pytest tests/tools/test_p1_assertion_eval_v2.py -q
........................                                                 [100%]
24 passed in 0.19s
```

### 2.2 全仓回归（worktree 内）

```text
$ python -m pytest -q
1513 passed, 1 skipped, 1 warning in 145.20s
[exit code: 0]        # skip = AGENTS.md 记录的 T-114 既有 skip
```

### 2.3 合成场景（fixture 在 `%TEMP%\t189a-smoke\`，**非任何真实盘**）

**A. 全对（10/40/10，fixed 答案只给地址、系统用字回报；dynamic 系统 a 用字 b 用地址）**

```text
[P1 断言评分 v2] 三层分录：fixed 10 / dynamic 40 / ambiguous 10（预注册 10/40/10；分母齐）
  fixed：correct=10 wrong=0 nj=0 missing=0 | precision 10/10 = 100.0% Wilson95 [0.7225, 1.0] | correct/total 10/10
  dynamic：correct=40 wrong=0 nj=0（nj=miss） missing=0 | precision 40/40 = 100.0% Wilson95 [0.9124, 1.0] | correct/total 40/40
  ambiguous：correct=10 wrong=0 quote_fail=0 missing=0 | 双引文 10/10 | 引文违规 0/20 | precision 10/10 = 100.0% Wilson95 [0.7225, 1.0]
  分类型：fixed:克 3/3 | fixed:化 2/2 | fixed:墓 2/2 | fixed:生 3/3 | dynamic:冲 10/10 | dynamic:刑 10/10 | dynamic:合 10/10 | dynamic:穿 10/10 | ambiguous:刑 5/5 | ambiguous:墓 5/5
```

**B. 32/40（后 8 条写反）**

```text
  fixed：correct=10 wrong=0 nj=0 missing=0 | precision 10/10 = 100.0% Wilson95 [0.7225, 1.0] | correct/total 10/10
  dynamic：correct=32 wrong=8 nj=0（nj=miss） missing=0 | precision 32/40 = 80.0% Wilson95 [0.6524, 0.895] | correct/total 32/40
  ambiguous：correct=10 wrong=0 quote_fail=0 missing=0 | 双引文 10/10 | 引文违规 0/20
```

**C. 全错（全部写反）**

```text
  fixed：correct=0 wrong=10 nj=0 missing=0 | precision 0/10 = 0.0% Wilson95 [0.0, 0.2775] | correct/total 0/10
  dynamic：correct=0 wrong=40 nj=0（nj=miss） missing=0 | precision 0/40 = 0.0% Wilson95 [0.0, 0.0876] | correct/total 0/40
  ambiguous：correct=0 wrong=10 quote_fail=0 missing=0 | 双引文 0/10 | 引文违规 0/0
```

**D. nj=miss（dynamic 30 对 / 5 错 / 5 nj）**

```text
  dynamic：correct=30 wrong=5 nj=5（nj=miss） missing=0 | precision 30/35 = 85.7% Wilson95 [0.7062, 0.9374] | correct/total 30/40
```

测试 `test_dynamic_nj_is_miss` 另把同一批 5 条从输出里删掉：`correct/wrong/delivered/miss` 四个读数与 nj 版**逐项相同**（只有 `nj` vs `missing` 分开记）。

**E. ambiguous 引文变体（缺引文 / 只给一条 / 非逐字 / 重复 / 硬给方向 + 5 条合规）**

```text
  ambiguous：correct=5 wrong=1 quote_fail=4 missing=0 | 双引文 5/10 | 引文违规 1/12 | precision 5/10 = 50.0% Wilson95 [0.2366, 0.7634]
```

### 2.4 记账恒等式

`total == correct + wrong + nj + quote_fail + missing`（三层各自）；`evaluate()` 内自检，不成立即 `InputError`（退出码 2），不静默出分。

---

## 3 · 未完成与风险

### 3.1 Blockers

**无硬阻塞。** 卡面 §1 明确留给 T-189b 的项一个没碰（见 3.2）。

### 3.2 风险 / 契约缺口（需要中枢或 T-189b 拍板）

1. **schema 是本卡自定 v2**：`p1-adjudication-answers/v2`（`layer` + `char_*`/`addr_*` + `source_texts` + `conflict_quotes`）与 `p1-adjudication-system-output/v2`。若 T-189b 的真实 anchor-60 用别的字段名，要先改卡再改码；我没有为真实数据猜格式。
2. **层与 kind 强绑定**：fixed 只收 `克/生/化/墓`，dynamic 只收 `冲/合/穿/刑`，`破` 只能进 ambiguous（A+ 枚举不含破）。真实 anchor-60 若出现 dynamic 层的破边，会直接退出 2 —— 这是有意的护栏，不是 bug。
3. **地址归一要求能落到单个地支字**：`addr_a` 需在 `address_book` 里，或同 case 同时给 `char_a`；天干级/柱级编码（如 `甲子`）要先映射成地支字。大小写与首尾空白已归一。
4. **引文只认答案自带的 `source_texts` 行**，不读 `sources/` 真文件（卡面要求不跑真实数据，也不扩 I/O）。T-189b 接真实策展时，要么把被引行原文写进答案，要么另加 loader —— 后者需改卡。
5. **不出 pass/kill**：`counts.denominators_met=false` 时只在控制台标注「分母不齐（不得引用 pass/kill）」，不判 32/40、不判 Wilson LB>65%、不判 ambiguous ≥7。这些阈值判定与 B1/B2、cluster、3-run、T-187 回归全部留给 T-189b。
6. **fixed 的 10/10** 只暴露为 `all_correct` 布尔 + 计数，没有被写成 verdict；非 10/10 时照常出分，由下游判定。

### 3.3 未做

- 未跑真实 anchor-60 / 未读 T-187 产物 / 未读真实 answers；
- 未做 B1/B2（规格 §4 的笨基线）、未做 chart 聚类、未做 3 次一致、未做 T-187 复算 12/40、2/20、28/40；
- 未给 routing/split 层（T-186 已有独立工具）；
- 未改阈值、未改 engine、未改任何既有测试。

---

## 4 · 下游须知

### 4.1 中枢怎么跑（合成或真实都同一入口）

```bash
python -m tools.p1_assertion_eval_v2 \
  --answers <answers.json> \
  --system-output <run.json> \
  [--json]
```

- 退出码 0 = 评完（分数高低不影响退出码）；2 = 输入不合口径（缺文件 / schema 错 / 层与 kind 不符 / 重复或未登记 case / 记账不平）。
- 产物无时间戳，同一输入两次运行逐字节一致（`test_cli_json_repeatable_and_exit_codes` 已钉）。
- 不 import engine、不读 `META/**` 与 `sources/**`、不写文件。

### 4.2 读结果顺序

1. `counts.denominators_met`（false 就**不得**引用任何 pass/kill）；
2. 三层 `correct / wrong / nj / quote_fail / missing` 与恒等式；
3. `dynamic.precision`（分子分母 + Wilson）与 `dynamic.correct_over_total`；
4. `ambiguous.both_quotes` 与 `quote_violations`（引文伪造/失配看这一项）；
5. `by_kind` 找哪一类拉低；`cases[].reason` 定位单条（`reversed / endpoint_mismatch / expected_*_observed_* / conflict_quotes_* / quote_not_verbatim / directed_claim_on_ambiguous`）。

### 4.3 T-189b 要补的

B1/B2 自动计较高者、chart 聚类 ≥78%、3 次一致 ≥90%、T-187 fixture 复算（12/40、2/20、28/40）、真实 anchor-60 装载与 pass/kill——本工具只提供三层原始读数与 Wilson，判定逻辑一行没写。

### 4.4 别做

- 不要把本 BRIEF §2.3 的合成数字当 P1 结果引用（fixture 不是真实盘）；
- 不要为了好看把 `nj` 记成 correct、把 `quote_fail` 并入 wrong、或把 fixed 混进 dynamic 分母；
- 不要在 `denominators_met=false` 时引用 pass/kill。
