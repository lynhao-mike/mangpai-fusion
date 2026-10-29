# T-187 BRIEF · 系统级盲测运行（fresh-40 + routing）

- 运行人：子代理（未污染，未读答案）
- 时间：2026-10-29
- 输入只读了：`tasks/T-187/PROMPT.md`、`docs/specs/party-direction-v1.md`、
  `META/p1-fresh-40-v1.json`、`META/p1-fresh-40-routing-blind-v1.json`。
- **答案文件读取：否。** 未打开 `META/p1-fresh-40-answers-v1.json`、`META/p1-fresh-40-routing-v1.json`、
  任何 `META/p1-holdout-*`、`META/golden-20-*`、`META/p1-dev20-*`；未打开 `sources/` 中与本批 case
  对应的原书分析段（只读了 `party-direction-v1.md` 明确引用的通用规则行）。

## 1. 改动文件

| 文件 | 性质 |
|---|---|
| `META/p1-system-run-v1.json` | 新增。45 条断言（40 fresh + 5 routing），object 形状 `{"schema_version","task","generated_at","case_count","cases":[45]}` |
| `tasks/T-187/BRIEF.md` | 新增（本文件） |
| `tasks/T-187/STATUS.md` | 追加 Execution Log |

- 未改 `engine/`、规则、`tests/`、hold-out、answers；未做任何 git 写操作。
- 一次性只读取数脚本只写在 `%TEMP%\T187\`（`run_all.py` / `analyze.py` / `decide.py` / `lines.py` / `build.py` / `check.py`），不在仓库内、不提交；脚本只读盲测输入与引擎输出，不读答案。

## 2. 原始输出

生成与自检命令（一次性脚本，均在 `%TEMP%`）：

```text
> python %TEMP%\T187\build.py
wrote E:\Git hub\mangpai-fusion\META\p1-system-run-v1.json 45
all quotes verified

> python %TEMP%\T187\check.py
count 45 expected 45 match True
errors: 0
nj: 25 mutual: 4 dir: 16
```

`check.py` 逐条校验并通过（0 错误）：

1. 45 个 `case_id` 与两份盲测输入**顺序与集合完全一致**；
2. `direction` ∈ `actor→target` / `mutual` / `needs_judgment`；`basis` / `state` 枚举合法；
3. `mutual == (direction=="mutual")`；
4. routing 5 条（PF-R01..R05）全部 `needs_judgment`；
5. 每条 `edge_id` 都能在对应盘的 `relations.edges` 中找到，且 `a`/`b` 是该边成员；
6. 每条 `verbatim_quote` 都能在 `source_ref` 指向行的行内逐字检索到；
7. `party` 回执自洽：`fire == items 中 F 计数`、`water == items 中 W 计数`、`delta == fire - water`；
8. 全对象无浮点数（正则 `\d+\.\d+` 无命中）。

方向分布：`actor→target` 16 条、`mutual` 4 条、`needs_judgment` 25 条（其中 routing 5 条）。
党势由 T-184 §2 的整数口径现算（A/B/C/D 四类、八位同权、藏干同字透干才计、D 只加月支本气党）。

## 3. 未完成与风险

- **无 missing**：45/45 全部产出。唯一取不到「原盘」事实的是 `PF-040`（见下）。
- **PF-040 时柱非法**：`戊申 甲子 甲寅 甲寅` 在甲日无 `甲寅` 时（引擎报「应为 丙寅」并退出 1）。
  处理：按引擎提示改用 `丙寅` 取**支级**事实（`甲`/`丙` 同属火党，`delta` 与两支冲/刑关系不变），
  `edge_id` 取 `e008`（申寅冲），`notes` 已标注替代。若中枢要求严格原盘，本条应改记 `missing`。
- **关系选取是最大风险（本卡固有）**：盲测输入不含 `relation/kind/mechanism`，同盘常有多条候选。
  本运行的确定性选法：优先 `duan_zuogong` 的「制用」大关系（冲/合/穿/刑），同盘多候选按
  `冲 > 合 > 穿 > 刑`、优先月支/日支；无「制用」大关系时取「合用」（按合绊处理）。三张双例盘
  （CH03=PF-003/023、CH07=PF-007/012、CH32=PF-034/038）按先冲后穿/先合后穿分配。
  若策展人锚定的是同盘另一条边，本条方向可能对不上而记 `no_candidate`；同一 R1/R2/R3 跨党对内
  方向只由盘级 `delta` 决定，故只要不在「合 ↔ 穿/刑」之间错配，方向仍可一致。
- **`state` 全为 `needs_judgment`**：所引均为通用规则句，没有逐案结果句，按 T-184 §4.5 不得填
  `成/败/救应`；`state_evidence` 因此为 `null`。
- **表外类**：`PF-001`（巳亥冲）、`PF-005`（寅申冲）、`PF-028`（巳亥冲）、`PF-040`（寅申冲）
  按 R8/G2 判 `needs_judgment`，未赋向。
- **`PF-012` 的边是戌酉穿**（年支戌·日支酉），不是卯酉穿；同盘另一例 PF-007 取卯酉冲。
- 未自评、未宣称通过；评分以中枢跑 T-186 为准。

## 4. 下游须知

- **输出形状**：顶层是 object，断言在 `cases` 数组（与 `p1-fresh-40-v1.json` / routing 盲测同构）。
  若 T-186 评分器只接受裸数组，请用 `doc["cases"]`。
- **`a`/`b` 是引擎地址**（`Y.s/M.s/D.s/H.s/Y.b/M.b/D.b/H.b`），与 `tasks/T-187/PROMPT.md` §2 的示例一致；
  按字比对前需用 `edge_id` 的 members 归一（同一字可能多现，如 `甲` 多透，不能直接字→地址）。
- **`party` 回执**只在 R1/R2/R3 与 Δ=0 的冲类给出；R4/R5/R7/R8 不带 `party`（规格 §4.1「其余 null」）。
- **`edge_id`** 全部取引擎真实边；`PF-009/014/016/029` 的合用边、`PF-R04` 的 `戊癸` 五合边也都在边表内。
- **引用**：`source_ref` 用相对路径 `sources/duan/<file>:L\u4f4d`，`verbatim_quote` 含 OCR 空格逐字复制；
  重算党势时请以 `party.items` 为准（A/B/C/D 四类可逐项指认）。
- 复现：对每盘跑 `python -m engine.cli all --pillars "<四柱>" --gender <性别> --json`，
  再按 T-184 §2.2–2.7 整数口径重算；`PF-040` 需用 `丙寅` 时柱替代。
