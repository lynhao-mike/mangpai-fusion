# A+ 裁决规格 v1.3（Opus/WB/Gemini 三方收敛，草案待冻结）

> **DISPOSITION: KILLED**（2026-10-29，T-191 按 §8 判定；方向产品 kill，事实层 + 分流/检索保留）。本文件仅作研究归档，不再执行。

> 依据：`docs/reviews/t187-gemini4-verdict-v1.md`、`t187-wb-v4-verdict-v1.md`、Gemini v5、Opus v6（2026-10-29）。
> 状态：阈值已收敛；采三方更严线；待最终确认后 hash 冻结。
> 杀的只是“自动方向产品”；事实 + 分流层保留。

## 1. 三层

| 层 | 条数 | 计分 |
|---|---:|---|
| fixed gate | 10 | 克/生/化/墓；**10/10**（Opus v6；不过先修 bug）；新策展；不进动态主分母 |
| decidable dynamic | 40 | 冲/合/穿/刑；必须 actor→target 或 mutual；nj=miss；主分母 |
| ambiguous | 10 | 真歧义；允许 nj，但必须 conflict_quotes[2]；单列 |

anchor-60：≥30 盘、≤2/盘；与 golden-20 / holdout-20 / fresh-40 三重零重叠；标注/运行/裁判分离；双人复核；engine.cli 预检；无 locator；答案先 hash。

## 2. 引擎 / Agent

- 引擎只发射：克 / 生 / 化（印为 actor）/ 墓（库为 actor）四个固定类。
- 冲 / 合 / 穿 / 破：`actor=None`；A+ 机制枚举不含破，不得逼 Agent 为破编单向 actor。
- 刑（未戌/子卯/三刑）：只保留 `mutual` **候选**；PF-025 证明可单向未→戌，PF-027 证明键可 mutual；双向可表达。
- 自刑边（辰辰/午午/酉酉/亥亥）：保留 `RelationGraph.edges`（completeness="zixing"，保 481/0 与关系图测试），
  但在 `build_duan_zuogong_candidates` 中逐条 logged 剔除（不静默丢弃；`excluded` 原则）。
- 党数回执只作披露事实，永不作方向判据；引擎不发射任何党势方向（R1/R2/R3/R5b 全死）。
- Agent：读 `engine.cli` + `query_theory` + 原文；给 actor→target / mutual；带 edge_id、source_ref、逐字 quote、主宾/连体/库位依据。
- decidable 上 nj=miss；ambiguous 上 nj 必须 `conflict_quotes[2]`（正反两条逐字冲突/无功条件原文）。

## 3. 阈值（Gemini v5 严格版；WB v4 的 24–27 红、nj 5–6 灰已并入更严线）

| 项 | Pass | Gray | Kill |
|---|---|---|---|
| fixed 10 | **10/10** | 不设 | <10 先修 bug；修后仍 <10 |
| dynamic 40 | ≥32/40 且 Wilson LB>65% 且 chart 聚类 ≥78% | 28–31（只作带引文候选；换新盲集复测一次；复测 ≤31 kill） | **≤27；或复测 ≤31（方向产品 kill；事实+分流层保留）** |
| 基线增量 | correct − max(B1,B2) ≥ +8 | +6～+7 | ≤+5 |
| decidable nj | ≤4/40 | 不设 | ≥5/40 |
| ambiguous | ≥7/10 且双引文 100% 行内可检出 | 5–6/10 | ≤4/10 |
| 引文 | 伪造/失配 ≤2/40 | 不设 | ≥3/40 |
| 一致性 | 3 次方向一致 ≥90% | 不设 | <90% |
| E2 选边 | 本轮只披露（T-187 12/40 基线） | — | P1 通过后 P2 top-3 ≥70%；P1 未过 E2 一并停 |

## 4. B2 笨基线必须写死 fallback

B2 = ① 本气相克取克方 → ② 本气相生取生方 → ③ 本气同五行（含全部四墓库冲刑：辰戌/丑未/丑戌/未戌）
一律取**主位端**（D/H 优先于 Y/M；同主或同宾取柱序靠后者）。否则 B2 在四库冲刑上弃权得 0，
系统会白捡“高出基线 +8”的假象。

B1 = T-184 整数 delta 符号（delta=0 按柱序左端）。评分器 v2 必须自动计 B1/B2 的较高者。

## 5. 3 张真实盘卡（四个硬补丁）

1. **L09 死锁**：`single-chart-analysis-v1.md` §2.3 / L09 硬拦 `rescue_judged=已判`；必须放行，并新增
   `rescue_evidence`：无救应时列出已扫描原局/岁运候选字及为何不构成救应（虚透/被合绊/隔柱），禁止只改两个字。
2. **C3 po 边**：C3（RF-2026-000894）夫妻宫唯一边是 e009 po（酉/子）；段派 M1-D-143 不把破并入四类制法，
   A+ 枚举不含 po。允许 C3 改锚全盘有向主功边，或把有据 mutual 计入 direction_known=true；
   严禁逼 Agent 为子酉破编单向施力方。
3. **双快照隔离**：t1 原局边与 t4 岁运引动边分别绑定 `snapshot{chart_id,dayun_index,liunian_year}`；
   加岁运会使 edge_id 重编号（C1 16→39），禁止跨快照混用 edge_id。
4. **反事实实跑**：替换的 1 个非目标端点字必须构成合法六十甲子柱（防 PF-040 甲日甲寅时）；
   必须附替换后 `engine.cli` 实跑的新 chart_id 与翻转输出。

3 卡门槛：direction_known 3/3、rescue 3/3 且挂源、随机异盘移植拒绝 ≥95%、同构异盘 ≥80%、
单字反事实翻转（跑前预注册翻哪个字/翻到什么）、第三人凭 CLI+锚点可重推。旧卡只演示。

## 6. 预注册顺序（严禁倒置）

1. 冻结 D-05 勘误 + 本规格 SHA-256；
2. scorer v2 + 合成 fixture，锁 hash；**先用 T-187 fixture 复算 12/40、2/20、28/40**；
3. 双人隔离策展 anchor-60；engine.cli 预检；无 locator；锁盲卷与答案 hash；
4. 未污染 Agent 盲跑 3 次 + 中枢一次性开盒评分。

## 7. 4 步

1. Day1–2：冻结规格；`structure_check.py` 过滤 `completeness=="zixing"` 的自刑候选；1489/1、481/0 全绿。
2. Day3–5：`tools/p1_assertion_eval_v2.py`：地址/字双向、三层、nj=miss、conflict_quotes、B1/B2、聚类 CI、3 次一致；合成 fixture 锁 hash。
3. Day6–9：双人策展 anchor-60（10+40+10）；四柱/原文行区间三重零重叠；十神库位复核；engine.cli 合法；无 locator；hash。
4. Day10–14：未污染 Agent 跑 3 次 + 一次性评分 + 3 卡门禁。

## 8. Kill（方向产品）

- dynamic ≤27/40；或复测 ≤31；或 Wilson LB≤65%；或 chart 聚类 <78%；
- 基线净胜 ≤+5；或 decidable nj ≥5/40；或引文伪造 ≥3/40；或 3 次一致 <90%；
- **双人复核一致率 <75%**（>10 条分歧）：原书判不出方向，“裁决器”定位不成立；
- 3 卡移植拒绝 <95%/同构 <80%，或反事实实跑不翻转；
- 策展失败：剔除已烧 85 例后，连 40 条双人复核一致、方向明确的冲/合/穿/刑原局断言都策不出来 → 语料底座证伪，产品停。

命中任一：关方向产品，保留 engine.cli + query_theory 事实/检索层。

## 9. 禁止

- 不复活引擎党势；不写 party-direction-v2；不为 PF-008/PF-018/寅申巳亥/刑/穿打引擎规则补丁；
- 不在 dev-20/holdout-20/fresh-40 上重跑宣称；不把 fixed 混进 40；不留 locator；
- decidable 不给 nj；不事后移阈值；不扩岁运/P2；不把旧卡当证明；看过答案的人不当裁判。
