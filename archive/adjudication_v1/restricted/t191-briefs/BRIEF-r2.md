# T-191 BRIEF · runner r2（未污染盲跑）

- 任务卡：`tasks/T-191/PROMPT.md`
- 输入：`META/p1-anchor-60-blind-final-v2.json`（60 条）、`docs/specs/adjudication-a-plus-v1.md`、`adjudication-a-plus-v1-notes.md`、`python -m engine.cli all/relations`、`python -m tools.query_theory`、`sources/duan/` 理论原文
- 产物：`META/p1-system-run-r2.json`（60 条全量）
- 执行时间：2026-10-29

## 1. 改动文件

| 文件 | 动作 |
|---|---|
| `META/p1-system-run-r2.json` | 新增（唯一交付数据） |
| `tasks/T-191/BRIEF-r2.md` | 新增（本文件） |
| `tasks/T-191/STATUS-r2.md` | 新增 |

未改：盲卷、答案、`engine/`、阈值、测试；未做任何 git 写操作。

## 2. 原始输出

### 2.1 生成与自检（本地脚本，仅标准库）

```
$ python build.py
wrote E:\Git hub\mangpai-fusion\META\p1-system-run-r2.json cases 60
missing []
null_edges 10 ['A60-001', ..., 'A60-010']
nj 10
conflict ok 10

$ python verify.py
case_count: 60 actual: 60
layer counts: {'fixed': 10, 'dynamic': 40, 'ambiguous': 10}
quotes checked: 70
errors: 0
null edge ids: ['A60-001','A60-002','A60-003','A60-004','A60-005','A60-006','A60-007','A60-008','A60-009','A60-010']
nj: 10
directed: 50
mutual: 0
```

统计：`basis` = source_text 35 / fixed_wuxing 13 / party_dominance 12；`direction` = actor→target 50 / needs_judgment 10；`state` = 成 50 / needs_judgment 10；`edge_id` 非空 50、空 10；`source_ref` 14 个不同原文行；70 条引文全部逐字命中 `source_ref` 指定行（脚本按 `文件:行号` 回读校验）。

### 2.2 方向判定所用的引擎事实（例）

fixed 10（`engine.cli relations` / `duan_zuogong`；全部 a→b）：

| case | 关系 | 引擎依据 |
|---|---|---|
| A60-001/002/003 | 克 | `duan_zuogong.zhi_ke` actor=Y.b / D.b / M.b（克方） |
| A60-004/005/006 | 生 | `duan_zuogong.sheng(main_qi)` actor=D.b / H.b / Y.b（生方） |
| A60-007 | 化 | `duan_zuogong` 化用 actor=H.b 子（印化杀，印为 actor） |
| A60-008 | 化 | 化用 actor=D.b 辰（印化官，印为 actor） |
| A60-009 | 墓 | `muku` 未（木库）→ 寅，rule=(一)寅申巳亥见各自墓库为入墓 |
| A60-010 | 墓 | `muku` 辰（水库/土库）→ 未，rule=(五)丑入辰墓、未也入辰墓 |

dynamic 40：关系图 `chong/liuhe/sanhe/chuan/xing` 边 actor 恒为 null（A+ §2），方向由「五行生克 → 得势方 → 库位/主宾」按段派原文裁：

- 穿：`体用:161`「相克之穿看势在哪里，哪方得势即能穿了对方」——得势方为 actor（如 034 申子辰水势，子→未；035/039 土势，戌→酉）。
- 冲：`21.大连:2852`「成势的冲才可能冲伤冲去」+ `21.大连:2850`「冲库……制的干净」——库冲（011/012/016/020）按冲库取，成势者（017 水势子→午、018 火势巳→亥）按旺冲衰取。
- 合：`宾主:202`「旺合动来衰合伤」、`23.中级:589`「合者主到」、`墓__穿:127`「制之之字为作功」——六合/半合按五行生克与旺衰取（辰酉 026/028 均辰→酉，子丑 025/030 均丑→子）。
- 刑：`体用:184`「未刑戌，制戌中辛」、`21.大连:2852`「未刑戌……丑戌刑戌把丑制干净」、`宾主:225`「开库要借刑力量」、`16.案例集:429`「子卯刑、寅巳申刑、丑戌未刑类似于冲」。

### 2.3 ambiguous 10

全部 `direction=needs_judgment`、`state=needs_judgment`，每条 `conflict_quotes` 两条逐字原文（正/反或正/无功条件）：

| case | 冲突对（ref） |
|---|---|
| 051 墓 戌/午 | 墓__穿:4「入墓有二：多而墓之，寅申巳亥见墓入之」 vs 同行「午戌论拱不是入墓」 |
| 052 穿 酉/戌 | 体用:161 得势方穿 vs 象法:158「酉戌穿，穿为速度……」（取象，非做功） |
| 053 合 寅/亥 | 23.中级:589「合者主到」 vs 宾主:202「旺合动来衰合伤」 |
| 054 穿 未/子 | 体用:161 vs 15.断句集:75 力序「…三刑>刑、害、破」 |
| 055 冲 未/丑 | 32.瑰宝:2250「两字互冲」 vs 21.大连:2852「一对一的冲…只是动和消耗」 |
| 056 合 卯/戌 | 23.中级:589 vs 宾主:202 |
| 057 穿 丑/午 | 体用:161 vs 15.断句集:75 力序 |
| 058 刑 未/戌 | 体用:184「未刑戌，制戌中辛」 vs 16.案例集:429「丑戌未刑类似于冲，当冲看」 |
| 059 冲 戌/辰 | 32.瑰宝:2250 vs 21.大连:2850「制财官临库不冲不发」 |
| 060 穿 寅/巳 | 体用:161 vs 15.断句集:75 力序 |

## 3. 未完成与风险

1. **edge_id 缺 10 条（全部 fixed 10）**。原因：关系图不建地支「克/生」边（G3），`duan_zuogong` 的 `zhi_ke` / `sheng(main_qi)` / `muku` 候选 `edge_id=null`；`化`（子/申、辰/午）在图中亦无对应 `sheng` 边。未用异类边（如把未/子的 `chuan e008` 冒充克边）填充，故留 null 待中枢评分器口径处理。
2. **dynamic 40 全部给 actor→target，0 条 mutual**。`adjudication-a-plus-v1-notes.md` §4 记载答案侧有「3 条 mutual」；本轮按盲卷端点顺序 + 五行/势/库原文逐条可证为有向（fixed 10/10 端点均为 actor 在前，dynamic 亦同序），未能从原文结构上确证哪 3 条为 mutual，故不主动标 mutual。若中枢评分显示 mutual 误判，集中风险在 011（戌辰）、016（丑未）、020（辰戌）三组同五行库冲——这三条方向证据最弱（仅库冲规则，无生克/势差）。
3. **state 统一取「成」**（fixed/dynamic 共 50 条）。判据：关系边/候选成立且方向可依原文落地即记成；未对「败/救应」程度另做裁决（A+ v1.3 阈值表未把 state 列为计分项）。ambiguous 10 条为 needs_judgment。
4. **引文复用**：14 个原文行覆盖 60 条，同一机制共用同一规则句；均逐字回读校验（脚本 70/70 命中），未伪造。
5. **A60-051 的两条 conflict_quotes 同出 `墓__穿:4` 同一行**（拱/墓两说本就在同一答句内），非跨文件冲突。

## 4. 下游须知

- 评分合并按 `case_id`；本文件不含 `chart_id/four_pillars`，请按 notes §2 从盲卷合并。
- ambiguous 条目结构：`conflict_quotes` 为 2 条字符串，另附 `conflict_quote_refs`（同序 2 条 `path:line`）；顶层 `source_ref/verbatim_quote` 取第 1 条。
- 方向一律 `actor→target` 字符串（U+2192），nj 为 `needs_judgment`；`kind` 用盲卷 mechanism 原字（克/生/化/墓/冲/合/穿/刑）。
- 未读 `META/p1-anchor-60-*-answers*`、`META/p1-anchor-60-B-v1.md`、任何 fresh/holdout/golden answers、`META/p1-system-run*`（r1/v1 仅列文件名与大小，未读内容）、dev-20 答案；未跑 T-189b 或任何评分器；未宣称通过、未自评。
