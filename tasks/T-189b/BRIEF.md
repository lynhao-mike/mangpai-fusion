# T-189b BRIEF · scorer v2 增量（B1/B2、四库、margin、聚类、3 次、T-187 回归、source loader）

- 状态：✅ **交付待验收**（只做增量；未跑真实 anchor-60；未改 engine / 答案 / 阈值 / 分母；
  未重写 T-189a 三层；未 push main）
- 分支：`p1/assertion-v2b`（worktree `..\mangpai-fusion-av2b`）
- 代码提交：`9a0b90f9`（2 files；后续只有一个 BRIEF/STATUS 文档提交，HEAD 以 `git log -1` 为准）
- 基线：卡面写 `e6e4add5`。实际从其后继 `0512463c` 起：该提交只加 T-189b 派活日志，
  避免本 worktree 的 `STATUS.md` 与中枢 add/add；`e6e4add5` 仍是祖先，代码差异只有下列 2 个文件。
- 一句话：三层逻辑一行没改；在核心里加 B1/B2（四库 B2 不弃权）、margin、chart 聚类 bootstrap、
  3 次方向一致、T-187 三数回归、ambiguous 只读 source loader；另把地址表改为 per-case，
  否则真实 anchor 的 `Y.b/M.b` 在不同盘指向不同字会冲突。

---

## 1 · 改动文件

| 文件 | 类型 | 规模 | 内容 |
|---|---|---:|---|
| `tools/p1_assertion_eval_v2.py` | 增量 | 610 → 1282 行 | B1/B2、margin、chart 聚类 bootstrap、3 次一致、T-187 回归、source loader、per-case 地址表 |
| `tests/tools/test_p1_assertion_eval_v2.py` | 增量 | 493 → 961 行 | T-189a 24 用例保留；新增 49 个用例（共 **73**）覆盖上述增量 |
| `tasks/T-189b/BRIEF.md` | 新建 | 本文件 | 四字段简报 |
| `tasks/T-189b/STATUS.md` | 更新 | — | 状态 + Execution Log + Blockers |

**未改**：`engine/**`、`META/**`（答案 / 阈值 / 分母零字节）、`docs/**`、既有 `tests/`、
`pyproject.toml`；未 `push`。

### 1.1 B1 = T-184 delta 符号（平局柱序左）

- delta 来源（二者都给必须一致，否则退出 2）：
  - `party_delta`：显式整数；
  - `four_pillars`：`"己卯 己巳 辛亥 甲午"` → `compute_party_delta()` 按 T-184 §2.2–2.7
    现算（A 四天干、B 四地支本气、C 非本气藏干同字透干、D 月支本气；戊己/藏干土中立）。
- 判定：
  - `delta > 0` → 火党端 → 金水党端；
  - `delta < 0` → 金水党端 → 火党端；
  - `delta == 0` → **柱序左端 → 右端**（`Y < M < D < H`）。
- 同类端（未戌，两端皆燥土 F）无法用符号定向：B1 记 `basis="delta_party_ambiguous"`、`actor=null`，
  **不发明方向**；该 case 由 B2 四库 fallback 兜住（见 1.2）。这不是缺数据：
  `data_missing=0`，`margin_comparable` 仍为 true。
- 无 delta / delta=0 但无柱位：`basis="no_delta"` / `"delta_zero_no_pillar"`，记入 `data_missing`。

### 1.2 B2 = 本气笨基线（四库不弃权）

- 本气五行：地支取本气（子水/丑土/…）；天干取自身五行。
- 本气**克** → 克方为 actor；本气**生** → 生方为 actor。
- 本气**同五行**（四库冲刑：辰戌 / 丑未 / 丑戌 / 未戌）→ **主位端**：
  - D/H 优先于 Y/M；
  - 同为 D/H 或同为 Y/M → **柱序靠后者**（D 后于 M、H 后于 D）。
- 只要两端柱位可得（`addr_a/addr_b` 为 `Y.b/M.b/...`，或显式 `pillar_a/pillar_b`），
  四库题**一定给方向，不弃权 0**。缺柱位才记 `same_element_no_pillar`（`data_missing+1`）。

### 1.3 margin = dynamic.correct − max(B1, B2)

- 两条基线都按 **dynamic 40 全分母**计；弃权按不中计（对系统保守）。
- `margin = correct − best_correct`，`best ∈ {b1,b2}`；输出还带各自的 `available/abstain/data_missing`。
- `margin_comparable=false` 只在**缺数据**时出现（缺 delta、缺柱位），不因为 B1 对未戌的合法弃权而 false。
- 合成 smoke（非真实盘）：correct 32、B1 12、B2 0 → **margin 32−12=+20**。

### 1.4 chart_id 聚类 CI

- 按 `chart_id` 聚合；缺省 `chart_id = case_id`（逐条当独立盘）。
- 输出：`charts / cases / correct`、`case_weighted_accuracy`、`chart_macro_accuracy`（每盘等权）、
  `all_correct_chart_rate`（整盘全对率）、`per_chart`、`chart_sizes`。
- `bootstrap95`：按盘有放回重抽 **2000** 次、固定 seed **20261029**，算 case 加权准确率的百分位区间；
  同一输入两次运行逐字节一致。
- 合成 smoke（20 盘、每盘 2 条、32/40、误差集中在 4 盘）：macro 80.0%、全对盘 16/20=80.0%、
  bootstrap95 **[0.6, 0.95]**。
- A+ §3 只写「chart 聚类 ≥78%」，未定义是全对盘率还是 macro；本工具**两个都报，不判 pass/kill**。

### 1.5 3 次方向一致率

- `--system-output` 可重复 1–3 次；逐 case 比较方向签名：
  - 定向：`(actor→target, observed_a, observed_b)`，**交换端点算不一致**；
  - mutual / needs_judgment：比较类型；
  - 任一运行缺该 case → 记不一致。
- 报 `dynamic`（主口径）与 `all`（含 fixed/ambiguous）的 `consistent/cases`、Wilson、`three_runs`。
- 合成 smoke：第 3 次翻 4 条定向 → **36/40 = 90.0%**。

### 1.6 T-187 回归（只复算，不宣称新结果）

- 纯函数 `t187_regression(run_doc, answers_doc)`：读已解析的
  `META/p1-system-run-v1.json` + `META/p1-fresh-40-answers-v1.json`；
  用答案 `four_pillars` 把 `Y.s/M.b/...` 地址归一到字。
- 复算口径：
  - **edge**：系统端点字集合 == 答案端点字集合（无序）→ **12/40**；
  - **direction**：只在系统交付 `actor→target` / `mutual` 时计分母；要求边对得上，
    且定向取向与答案 actor 一致，或 mutual 与答案 `mutual=true` 一致 → **2/20**；
  - **edge mismatch**：40 − 12 → **28/40**。
- 写在测试里：`test_t187_regression_three_numbers` 钉 12/40、2/20、28/40；
  `test_t187_regression_recomputes_instead_of_hardcoding` 改一条定向后 direction 减 1，
  证明不是写死常量。
- 旁证：`compute_party_delta()` 与 T-187 运行人现算的 `party.delta` **17/17 逐条相等**；
  T-184 §2.8 的 V1a/V1b 向量 **−1 / 0** 复现。

### 1.7 ambiguous 只读 source loader

- `SourceLoader(root)`：按 `<path>.md:L<行号>` 只读取一行；默认 root 为仓库 `sources/`。
- CLI：`--source-loader`（默认关）+ `--source-root <sources/>`。
- 仅当 ambiguous **缺 `source_texts`** 时启用；定位符来自 `source_ref` / `source_refs`
  （`conflict_quotes` 若是对象也读其 `source_ref`）。有 `source_texts` 时 loader 一行也不读。
- 引文口径**不变**：两条仍须逐字落在所加载的某一行；loader 只补「行文本」，不放宽匹配。
- 安全：拒绝绝对路径、`..` 越界、缺文件、行号越界；只读，不写。
- 多行正反引文请给 `source_refs: ["...:L1", "...:L2"]`；只给单条 `source_ref` 时只加载那一行。

### 1.8 地址表改为 per-case（真实 anchor 兼容补丁）

- T-189a 的全局 `address_book` 会把所有 case 的 addr↔char 合并；真实 anchor 的 `Y.b/M.b`
  在不同盘指向不同的字，必然冲突退出 2。
- T-189b 起：全局 `address_book` 只放跨 case 稳定地址（如 `D1/H3`）；每个 case 另有
  `Case.book`（本 case 的 addr↔char + 全局表），评分只在本 case 内归一。
- 三层判分逻辑未动；T-189a 的 24 个用例全过。

---

## 2 · 原始输出

### 2.1 目标门禁（卡面验证）

```text
$ E:\Git hub\mangpai-fusion\.venv\Scripts\python.exe -m pytest tests/tools/test_p1_assertion_eval_v2.py -q
........................................................................ [ 98%]
.                                                                        [100%]
73 passed in 1.44s
```

### 2.2 全仓回归（worktree 内）

```text
$ python -m pytest -q
1569 passed, 1 skipped, 1 warning in 131.92s (0:02:11)
[exit code: 0]        # skip = AGENTS.md 记录的 T-114 既有 skip
```

### 2.3 合成 CLI smoke（`%TEMP%\t189b-smoke\`，**非任何真实盘**）

命令：3 次 `--system-output` + T-187 回归；40 条 dynamic 合成 case（无 fixed/ambiguous，
所以分母不齐，仅看增量字段）。

```text
[P1 断言评分 v2] 三层分录：fixed 0 / dynamic 40 / ambiguous 0（预注册 10/40/10；分母不齐（不得引用 pass/kill））
  fixed：correct=0 wrong=0 nj=0 missing=0 | precision n/a（无交付） | correct/total 0/0
  dynamic：correct=32 wrong=8 nj=0（nj=miss） missing=0 | precision 32/40 = 80.0% Wilson95 [0.6524, 0.895] | correct/total 32/40
  ambiguous：correct=0 wrong=0 quote_fail=0 missing=0 | 双引文 0/0 | 引文违规 0/0 | precision n/a（无交付）
  分类型：dynamic:冲 32/40
  基线：B1 12/40 | B2 0/40 | best b1 12 | margin 32−12=+20
  chart 聚类：20 盘 | 全对盘 16/20 = 80.0% | macro 80.0% | bootstrap95 [0.6, 0.95]
  3 次方向一致：dynamic 36/40 = 90.0%
  T-187 回归：edge 12/40、direction 2/20、edge mismatch 28/40
```

### 2.4 T-187 回归三数（测试里断言，不是新结果）

```text
cases=40  edge_match=12/40  direction_correct=2/20  edge_mismatch=28/40
edge_match_rate=0.3  direction_rate=0.1
```

### 2.5 T-184 delta 旁证

```text
V1a 甲子 戊午 辛辰 壬戌 → -1   （规格 §2.8 期望 -1）
V1b 甲子 戊午 庚辰 壬戌 →  0   （规格 §2.8 期望  0）
T-187 party 回执 17/17 与现算相等
```

---

## 3 · 未完成与风险

### 3.1 Blockers（真实 anchor-60 前必须拍板）

1. **fixed 10 的天干端点会被 T-189a 契约拒收**：`char_a/char_b` / `address_book` 目前只接受
   **单个地支字**；真实 fixed 10（克/生/化/墓）很可能出现 `庚`/`乙` 等天干端点，会退出 2。
   本卡范围只写 B1/B2/margin/聚类/3 次/T-187/loader，**没有擅自放宽**。
   两条合法出路：① T-190 的 fixed 10 全选地支端点；② 中枢授权把端点字集扩到「天干或地支」
   （`_is_zhi` → `_is_zhi or _is_gan`，并同步 address_book 的提示文案）。B2 的五行/主位算法已能处理天干。
2. **T-190 当前答案格式缺 B1/聚类所需字段**：`tasks/T-190/PROMPT.md` §2 的答案只有
   `relation{actor/mutual/expected_direction}`、`quote`、`source_ref`。要跑 B1/margin 需要
   `four_pillars`（或 `party_delta`）与 `chart_id`；聚类需要 `chart_id`；多行 ambiguous 需要
   `source_refs`（或 `source_texts`）。请在 T-190 冻结 hash **之前**补齐，或在评分时把盲卷的
   `chart_id/four_pillars` 只读合并进答案。否则：`margin_comparable=false`、`chart_id` 退化为
   `case_id`（60 盘、聚类意义变弱）。
3. **A+「chart 聚类 ≥78%」的口径未定义**：全对盘率与每盘等权 macro 是不同数（误差集中时会分开）。
   本工具两个都报，不判 pass/kill；请中枢在规格里钉死用哪一个。

### 3.2 风险 / 需要知道

1. **mutual 答案会压低基线**：B1/B2 只给定向；dynamic 里的 `mutual` 答案对两条基线都记不中，
   系统判对即计 correct，margin 会因此结构性偏高（最多 = mutual 条数）。T-187 只有 1 条 mutual；
   anchor-60 若 mutual 多，读 margin 时要扣掉这部分解释。
2. **B1 在未戌同类端合法弃权**：`max(B1,B2)` 依赖 B2 的四库 fallback；若某条四库又缺柱位，
   会同时丢 B1/B2，`margin_comparable=false`。真实 anchor 的 `addr_a/addr_b` 是柱位编码即可避免。
3. **T-187 答案是 fresh-40，含已知 PF-003/023/025 错标**：本回归只复算冻结的 12/40、2/20、28/40，
   证明量具能复现 T-187 读数；**不得**把这几个数当新 P1 结果或答案正确性证明。
4. **source loader 的多行边界**：只给单条 `source_ref` 时只加载一行；正反引文在不同行时必须
   给 `source_refs`，否则第二条 `quote_fail` 是口径正确、不是 loader bug。
5. **chart bootstrap 是固定 seed 的百分位法**：2000 次、seed 20261029；不同 seed 会得到略不同的
   区间（点估计不变）。测试钉了当前值，改 seed 需要同步改测试。
6. **per-case 地址表**：同一 `chart_id` 内若两个 case 对同一地址给了不同的字，不再跨 case 报冲突
   （各 case 自洽即可）；这是为真实多盘地址做的取舍。

### 3.3 未做

- 未跑真实 anchor-60 / 未读/改 anchor 答案；未跑 fresh-40 新评分；
- 未改 engine / 规则 / 阈值 / 分母；未改 T-189a 三层判分；
- 未出 pass/kill（只给原始读数与 margin，不判 32/40、不判 Wilson LB、不判 cluster ≥78%）；
- 未 push main；未合并回 main。

---

## 4 · 下游须知

### 4.1 怎么跑

```bash
python -m tools.p1_assertion_eval_v2 \
  --answers <answers.json> \
  --system-output <run1.json> [--system-output <run2.json> --system-output <run3.json>] \
  [--json] \
  [--source-loader --source-root sources/] \
  [--t187-run META/p1-system-run-v1.json --t187-answers META/p1-fresh-40-answers-v1.json]
```

- 退出码 0 = 评完；2 = 输入不合口径（缺文件 / schema 错 / 层与 kind 不符 / 重复或未登记 case /
  记账不平 / ambiguous 缺 source_texts 且未开 loader / delta 与 four_pillars 不一致）。
- 产物无时间戳；同一输入两次运行逐字节一致（bootstrap 固定 seed）。
- `run()` 仍兼容单次调用；`evaluate_runs()` / `run_many()` 才有多运行。
- 不 import engine；不自动读 META；只有显式 `--source-loader` 才读 `sources/`。

### 4.2 真实 anchor-60 的答案字段（B1/聚类）

dynamic 每条至少给：

```json
{"case_id": "...", "chart_id": "CH-..", "layer": "dynamic", "kind": "冲",
 "addr_a": "M.b", "char_a": "午", "addr_b": "D.b", "char_b": "子",
 "four_pillars": "己卯 己巳 辛亥 甲午",   // 或 party_delta: -1
 "expected_direction": "actor→target"}
```

- `addr_a/addr_b` 用柱位编码（`Y.s/M.b/...`）时自动得到 `pillar_a/pillar_b`；
  否则显式给 `pillar_a/pillar_b ∈ {Y,M,D,H}`。
- ambiguous：给 `source_texts`，或开 `--source-loader` 并给 `source_ref` / `source_refs`。
- fixed：当前仍只收单个**地支**字（见 3.1 Blocker 1）。

### 4.3 读结果顺序

1. `counts.denominators_met`（false 就**不得**引用任何 pass/kill）；
2. 三层 `correct / wrong / nj / quote_fail / missing` 与恒等式；
3. `baselines.dynamic`：先看 `margin_comparable`，再看 `b1/b2/available/data_missing` 与 `margin`；
4. `chart_cluster.dynamic`：`chart_macro_accuracy` 与 `all_correct_chart_rate` 两个口径都看，
   `bootstrap95` 是按盘聚类的区间；
5. `consistency.dynamic`：`three_runs` 为 true 才引用；`rate` 是方向一致率；
6. `t187_regression`：只作量具回归，不作新结果。

### 4.4 别做

- 不要把本 BRIEF §2.3 的合成 smoke 数字当 P1 结果引用；
- 不要在 `margin_comparable=false` 时引用 margin；
- 不要把 T-187 的 12/40、2/20、28/40 当成本轮新跑出来的成绩；
- 不要为了好看把 B1 的合法弃权改成「猜一个方向」，也不要把 mutual 答案算作基线命中。
