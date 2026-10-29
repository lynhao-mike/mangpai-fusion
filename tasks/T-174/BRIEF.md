# T-174 BRIEF · P1 33 条第二人复核（只读）

- 状态：✅ 交付（第二人复核 Agent，未参与标注）
- 任务卡：`tasks/T-174/PROMPT.md`
- 产物：`META/p1-second-review-v1.json`（33 条逐条复核 + 分歧 + 重算）、`META/p1-second-review-v1.md`
- 一句话：**33 条 quote 与地址 0 错，23/17/7 也复现得一模一样；但 6 条「施力方」的取法与原文句式不一致
  （1 条有反证、2 条是对称句、3 条依据在别的句子），按预注册字面口径应是 4–6/15–16（26.7%–37.5%）。
  41.2% 只是原标注口径的复现值、不是稳健中值；放宽口径最高 47.4%，全部 <60%，
  `facts_blocking` 维持，阈值不必改。**

---

## 1. 改动文件

**新建**

| 文件 | 说明 |
|---|---|
| `META/p1-second-review-v1.json` | 33 条逐条复核（quote/地址/actor/kind/scope + 结果行对照）、18 处 14 条分歧、5 个重算口径 |
| `META/p1-second-review-v1.md` | 计数、分歧清单、重算、41.2% 稳健性、阈值建议 |
| `tasks/T-174/BRIEF.md` | 本文件 |

**修改**

| 文件 | 改动 |
|---|---|
| `tasks/T-174/STATUS.md` | 追加 Execution Log 一行 |

**未改**：`..\mangpai-fusion-rethink`（`git status --porcelain` 为空）、33 条原文件 `META/golden-20-core-edges-v1.json`、
其结果 `META/golden-20-core-edge-recall-v1.json`、`META/golden-20-answers-v1.json`、`engine/**`、规则、`tests/**`、`sources/**`。

**未跑**：`tools/golden_core_edge_recall.py`（评分脚本，按卡禁止）；复算改用自己的实现。
**未做**：任何 git 写操作（无 commit/push/checkout/stash/reset/clean）。

```text
$ git status --porcelain          # main 工作区（12:20 快照）
 M tasks/T-175/STATUS.md                    ← 并行 T-175，未碰
?? META/p1-holdout-v1.json  ?? META/p1-holdout-v1.md
?? META/p1-holdout-answers-v1.json          ← 并行 T-175，未碰
?? tests/tools/test_p1_holdout_schema.py    ← 并行 T-175，未碰
?? tasks/T-175/BRIEF.md                     ← 并行 T-175，未碰
?? META/p1-second-review-v1.json            ← 本卡
?? META/p1-second-review-v1.md              ← 本卡
?? tasks/T-174/BRIEF.md                     ← 本卡
 M tasks/T-174/STATUS.md                    ← 本卡
?? mangpai-fusion-offline-04677d2c.zip      ← 既有未跟踪，未碰
?? .tmp-c1.json  ?? .tmp-c2.json  ?? .tmp-c3.json   ← 本卡之前就在，未碰
$ git -C ..\mangpai-fusion-rethink status --porcelain
（空）
```

main 在复核期间前进了一个提交：`7569c025` → `17095645`（T-176，只动 `META/`、`docs/`、`tasks/`）。
`engine/`、`sources/` 未变，故本次用 `engine.cli` 取的 20 盘事实不受影响（`git diff --name-status 7569c025..17095645` 已核）。

## 2. 原始输出

### 2.1 复现（独立实现，20 盘 `engine.cli all`）

```text
mine:   scored=23 edge=19 cand=17 directed=17 ok=7 {'actor_none': 3, 'ok': 7, 'reversed': 2, 'no_candidate': 5}
theirs:         23      19/23   17/23        17     7/17 {actor_none 3, no_candidate 5, ok 7, reversed 2}
逐行 diff（a/b 地址、status、edge_ids、candidates、muku_hits、edge_hit、candidate_hit、direction）：0
```

### 2.2 逐条复核三维检查

```text
quote 逐字：33/33（答案字段命中 且 source_refs[field] 的 path:line 原文行命中）
地址正确 ：33/33（chars/ten_gods/addrs 由 engine 表解析，逐条对原文宫位/十神）
与结果行对照：33/33 一致（含 6 条 endpoint_absent、3 条 suiyun、1 条 non_relational 的分类）
```

### 2.3 分歧（18 处 / 14 条）

```text
quote 不逐字      0
地址错            0
actor             6   n7  乙庚合（对称句赋向，无施力方）→ 出分母
                      n33 庚甲相冲（同上；因 endpoint_absent 无数字影响）
                      n16 只能靠甲木化杀为功（L2645「甲木化水」/L2647「甲为死木…」→ 施力方是甲，A/B 反了）
                      n10 泄官杀生自己（依据章首 L1605「杀生印、印生身」，非所引句）
                      n15 印化七杀（依据同段 L1461「七杀化印再生身」，非所引句）
                      n32 午禄紧贴劫财（「紧贴」非施力动词，依据 L211 通则）
kind              2   n5 合制群杀（应 wuhe，给 null 让 ganzhi_zihe 混入）、n12 克日主（预注册说 null，给了 ke）
kind 枚举缺口     2   n28 sanhe、n33 stem_chong（不在预注册枚举；均 endpoint_absent）
scope 标签错      6   n26 n27 n28 n29 n31 n33（缺端点是戌/辰/酉/丑/甲/庚＝岁运字，却写 natal）
其他              2   n19「两未」只命中 1 个（self_sit_excluded）；claims 无 path:line，只能经 answers 反查
```

三条「依据在别的句子」的 actor（n10 n15 n32）不算错，但也不是所引句明示——所以主口径不改它们，
只改有反证的 n16 与无施力方的 n7；从严口径才把它们按句法主语重算。

### 2.4 重算

```text
S0 原标注（复现）                      17 有施力方  7 正确  41.2%   CI95 [21.6, 64.0]
S4 最宽松 B（剔 n7 n32）               15          7       46.7%   CI95 [24.8, 69.9]
S3 最宽松 A（「入」也算施力方）         19          9       47.4%   CI95 [27.3, 68.3]
S1 复核主口径（n7 出分母、n16 反向）    16          6       37.5%   CI95 [18.5, 61.4]
S2 从严（+n10 n15 反向、n32 出分母）    15          4       26.7%   CI95 [10.9, 52.0]
±2 条（固定 17）                       5–9 条                29.4%–52.9%
唯一到线：S4 + 2 条假阴性（未发现假阴性） 9/15               60.0%（踩线，不过线）
```

### 2.5 自测

```text
$ .venv\Scripts\python.exe -m pytest -q
1381 passed, 1 skipped, 1 warning in 137.08s (0:02:17)     exit 0
SKIPPED [1] tests\tools\test_bundle_pii.py:34: 脱敏脚本缺失（T-114 已知项）
```

本次未新增任何代码，只确认现状 **0 failed**（skip 是 T-114 的已知项，非本卡引入）。

### 2.6 两次运行一致

```text
run1 sha256 = run2 sha256 = D44DF636CE9FFC119DE08049337E1AF86CB71CD4D54DC10FBACB4F266BFCC178
（p1-second-review-v1.json 字节一致；.md 亦一致，sha256 DDF982E4652BF68A7621E175BCE3BB3634CA6DFD4BEFB607FEFAC8E5446C6034）
生成过程无时间戳/随机序/未排序 dict，两次全量重跑逐字节相同。
```

## 3. 未完成与风险

1. **自测现状**：`pytest -q` = 1381 passed / 1 skipped / exit 0。比裁决书记录的 1374 多 7 条 =
   `tests/tools/test_p1_holdout_schema.py`（并行 T-175 新增，单独跑 `7 passed`）；不是本卡引入。
2. **无自建测试**：任务卡把 `tests/tools/test_p1_second_review.py` 列为可选；本次产物是数据 + 报告，不是代码，
   没有可断言的确定性契约可测（唯一可测的是「两次运行一致」，已用 sha256 手工确认）。
3. **6 条 actor 分歧分三档**：1 条有反证（n16「甲木化水/甲为死木化壬水杀」→ 施力方是甲）；2 条是对称句无施力方
   （n7「乙庚合」、n33「庚甲相冲」）；3 条有原文依据但不在所引句里（n10 靠 L1605、n15 靠 L1461、n32 靠 L211）。
   前两档进主口径，第三档只在从严口径里改，最终由中枢裁。
4. **点估计不等于统计结论**：n=17 的 Wilson 95% CI 上界到 64.0%，所以只能说「按预注册点估计判 blocking」，
   不能说「已证明事实层承载不了主功」。
5. **未跑评分脚本**：无法直接证明 `tools/golden_core_edge_recall.py` 两次运行一致；改用自己的实现复现，
   结果 0 行差异，等价性由此保证。

## 4. 下游须知

1. **别把 41.2% 当精确值**：它只是原标注口径的复现值。按所引句主语修正后是 37.5%（6/16）/ 26.7%（4/15）；
   把口径放宽（「入」也算施力方、只剔弱项）反而到 46.7% / 47.4%。要引用就报「26.7%–47.4%，全部 <60%」，别报单值。
2. **`facts_blocking` 维持**：±2（29.4%–52.9%）、两条最宽松口径（46.7% / 47.4%）全 <60%；
   连最宽松口径再取 ±2 上界也只有 60.0%（S4），是踩线不是过线。把 60% 线降到 30% 就能让今天这个结果「通过」——
   那是裁决书 §3.2 明令禁止的「用结果反推规则」。
3. **修 `structure_check.py` 之前先冻结 actor 规则**，建议三张表：对称动词（合/冲/穿/刑/自刑）→ `actor=null`；
   化/泄 → 取句法主语；入墓 → `actor=null`，除非原文是「库墓X」定向句。规则不冻结，hold-out 会重复同样的噪声。
4. **kind 枚举要补齐**（`sanhe`、`stem_chong`），或明确写「只认 合/刑/穿/冲/墓/生/克」。现在 n5 的 `kinds=null`
   把无关的 `ganzhi_zihe` 算进了候选，`candidate_recall 73.9%` 因此偏高，不宜直接对 70% 线用。
5. **scope 标签统一**：端点含岁运字的一律 `scope=suiyun`（现在 6 条写 `natal`，靠 `endpoint_absent` 兜住）。
   hold-out 的策展 Agent 会继承这个不一致。
6. **hold-out 规模要先定**：n≈17 时一条 = 6pp、±2 条 = 12pp，60% 与 80% 两条线在统计上分不开；
   要么加到能分开的样本量，要么改用区间判定，否则下一次的 go/kill 还是噪声。
7. **claims 建议带 `source_ref: path:line`**：现在 33 条只能经 `golden-20-answers-v1.json` 反查才能回原文，
   hold-out 若只交 claims 文件，第二人无法独立核验 quote。

## 5. 结论（给中枢的一句话）

**可以接受这份 33 条标注的「结构」，但不要接受它的「施力方」：quote 与地址都干净，7/17 也能复现，
可那 7 条里有 3 条是拿五行流向当施力方、其中 1 条与原文相反——真按预注册的字面规则，正确数是 4–6 条。
无论按哪个口径，方向召回都 <60%（26.7%–47.4%），`facts_blocking` 不变；下一步该做的是把 actor 规则写死再修 `structure_check.py`，
而不是重议阈值。**
