# 单盘五元组断语卡 v1 · C1 / C2 / C3（三张真实盘）

> **当前能力展示，不是 P1 验证。** 这三张卡只证明「用现有事实层能把一条断语写到什么程度、哪些字段写不出来」，不构成对 `docs/specs/single-chart-analysis-v1.md` 的验收，也不构成任何预测。
>
> - `pre_p1: true`（三张卡逐卡标注）
> - 任务卡：`tasks/T-176/PROMPT.md`；规格：`docs/specs/single-chart-analysis-v1.md`（五元组 §2、Linter §4、缺口 §7.3）
> - 案例事实：`META/single-chart-cases-v1.json`；本文件与 `META/single-chart-cards-v1.json` 同源
> - 盘面事实唯一来源：`python -m engine.cli`；原文唯一来源：`theory/duan/index.yaml` 的 `entry_id` + `raw_file` + `raw_anchor`
> - 三张卡都是**原局快照**（`dayun_index=null`、`liunian_year=null`）；`edge_id` 只对该快照有效，跨快照引用即错（规格 §1.3）
> - 一盘一卡：C1/C2/C3 各 1 张，共 3 张

---

## 0 · 三张卡一览

| 卡 | case_id | 四柱 / 性别 | ① 宫位·地址 | 边 | ② direction | direction_known | ③ 三态 | 救应 | confidence |
|---|---|---|---|---|---|---|---|---|---|
| C1-01 | RF-2026-000125 | 丁卯 壬子 辛丑 乙未 / 乾 | 日 D.b=丑 偏印 + 时 H.b=未 偏印 | e015 chong · e016 xing | 冲 | **false**（actor/target=null） | 破局 | 未判 | 中 |
| C2-01 | RF-2026-000438 | 庚午 戊寅 己未 乙丑 / 坤 | 日 D.b=未 比肩 + 时 H.b=丑 比肩 | e013 chong · e014 xing | 冲 | **false**（actor/target=null） | 破局 | 未判 | 中 |
| C3-01 | RF-2026-000894 | 壬戌 己酉 庚子 戊子 / 乾 | 月 M.b=酉 劫财 + 日 D.b=子 伤官 | e009 po | 破 | **false**（actor/target=null） | 破局 | 未判 | 低 |

**计数：`direction_known=false` 3/3，`true` 0/3；`rescue_judged=未判` 3/3；用到的边 5 条（e015/e016/e013/e014/e009）。**

这不是写作偏好，是事实层现状：冲/刑/穿/破这类地支边在引擎里 `actor=None`（缺口 G2；规格 §1.1 引 failure-ledger A-01 记为 523/3179，`structure_check.py:475-478`），所以三张卡都只能写「方向未定」。**当前能力的天花板就写在 `direction_known` 这一列上。**

---

## 1 · 三张卡

### [C1-01] 夫妻宫 D.b=丑 同时受 H.b=未 的冲边与刑边（方向未定）

- ① 原局象：`day`（日支）/ `D.b`=丑 偏印 + `H.b`=未 偏印 / `e015 chong[D.b,H.b]` group=null completeness=null；`e016 xing[D.b,H.b]` group=丑戌未 completeness=partial
- ② 体用宾主：体=`D.b`、体=`H.b`；第 3 层（主=日柱、时柱；宾=年柱、月柱），`D.b`/`H.b` 同在主侧；方向=冲（**方向未定**，actor/target=null，G2）
- ③ 三态：**破局**；依据=`edge` `e015`「目标受冲」evidence=[`D.b`,`H.b`]、`edge` `e016`「目标受刑」evidence=[`D.b`,`H.b`]；救应=**未判**
- ④ 落事：日支 D.b（夫妻宫，偏印）与时支 H.b（偏印）之间同时挂着冲边 e015 与刑边 e016，两股作用落在同一宫位上。方向未定（G2），只能写「同一对地址上的双重牵连」，不能写成谁冲谁、谁刑谁。　引动=none_observed @ D.b（原局快照 16 条边全部 scope=natal，DY/LN 边 0 条）
- ⑤ 锚点：地址=`e015`/`e016` + `D.b`/`H.b`；原文=`M1-D-298` `sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:48`
- statement：D.b=丑 与 H.b=未 之间有冲边 e015、刑边 e016（方向未定，G2）；按 M1-D-298「夫妻宫位要安静，如有用，不能被刑坏，冲破，穿倒」，本盘夫妻宫同时落在「冲破」与「刑坏」两类上，故记破局；救应未判（G5），不写化解。
- 边界：成立=以 D.b=丑 为夫妻宫；e015/e016 在该原局快照（dayun_index=null, liunian_year=null）内成立，且 D.b 十神为偏印、体用为「体」。不成立=换成岁运快照后 edge_id 全量重编号（实测加 --dayun-index 5 --liunian 2026 后边数 16→39，同一对夫妻宫冲/刑边变为 e031/e032）；或夫妻宫改取其他柱；或 M1-D-298 的「如有用」前提不成立（同段 :124 另按破坏程度分级，本卡不判程度）。
- confidence：**中**；unknowns：`G2` / `G5` / `muku_open_close` / `suiyun_ten_god`
- 快照：`chart_id=cf-5735e1472538ad92664b` `dayun_index=null` `liunian_year=null`

### [C2-01] 夫妻宫 D.b=未 同时受 H.b=丑 的冲边与刑边（方向未定）

- ① 原局象：`day`（日支）/ `D.b`=未 比肩 + `H.b`=丑 比肩 / `e013 chong[D.b,H.b]` group=null completeness=null；`e014 xing[D.b,H.b]` group=丑戌未 completeness=partial
- ② 体用宾主：体=`D.b`、体=`H.b`；第 3 层（主=日柱、时柱；宾=年柱、月柱）；方向=冲（**方向未定**，actor/target=null，G2）
- ③ 三态：**破局**；依据=`edge` `e013`「目标受冲」evidence=[`D.b`,`H.b`]、`edge` `e014`「目标受刑」evidence=[`D.b`,`H.b`]；救应=**未判**
- ④ 落事：日支 D.b（夫妻宫，比肩）与时支 H.b（比肩）之间同时挂着冲边 e013 与刑边 e014，同一宫位被同一对方以两种方式连着。方向未定（G2），只能描述为「本位被同一处外力顶住」，不能说成丑冲未、丑刑未。　引动=none_observed @ D.b（原局快照 14 条边全部 scope=natal，DY/LN 边 0 条）
- ⑤ 锚点：地址=`e013`/`e014` + `D.b`/`H.b`；原文=`M1-D-298` `sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:48`
- statement：D.b=未 与 H.b=丑 之间有冲边 e013、刑边 e014（方向未定，G2）；按 M1-D-298「夫妻宫位要安静，如有用，不能被刑坏，冲破，穿倒」，本盘夫妻宫属被冲破、刑坏的一类，故记破局；救应未判（G5）。
- 边界：成立=以 D.b=未 为夫妻宫；e013/e014 在该原局快照（dayun_index=null, liunian_year=null）内成立，且 D.b 十神为比肩、体用为「体」。不成立=换成岁运快照后 edge_id 全量重编号（实测加 --dayun-index 4 --liunian 2026 后边数 14→39，同一对夫妻宫冲/刑边变为 e028/e029）；或夫妻宫改取其他柱；或 M1-D-298 的「如有用」前提不成立（同段 :124 另按破坏程度分级，本卡不判程度）。
- confidence：**中**；unknowns：`G2` / `G5` / `muku_open_close` / `suiyun_ten_god`
- 快照：`chart_id=cf-f10b5515f2019638f42f` `dayun_index=null` `liunian_year=null`

### [C3-01] 夫妻宫 D.b=子 只有一条破边 e009（方向未定；本盘无配偶星地址）

- ① 原局象：`day`（日支）/ `M.b`=酉 劫财 + `D.b`=子 伤官 / `e009 po[M.b,D.b]` group=null completeness=null（**全盘落在夫妻宫上的唯一关系边**）
- ② 体用宾主：体=`M.b`、双属=`D.b`；第 3 层（主=日柱；宾=月柱），`D.b` 为主、`M.b` 为宾；方向=破（**方向未定**，actor/target=null，G2）
- ③ 三态：**破局**；依据=`edge` `e009`「目标受破」evidence=[`M.b`,`D.b`]；救应=**未判**
- ④ 落事：日支 D.b（夫妻宫，伤官）与月支 M.b（劫财）之间只有一条破边 e009，是全盘落在夫妻宫上的唯一关系边。方向未定（G2），且本盘无配偶星地址（no_spouse_star），只能描述这条宫位上的结构，不能补出配偶星的作用。　引动=none_observed @ D.b（原局快照 12 条边全部 scope=natal，DY/LN 边 0 条）
- ⑤ 锚点：地址=`e009` + `M.b`/`D.b`；原文=`M1-D-300` `sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:122`
- statement：D.b=子 与 M.b=酉 之间只有一条破边 e009（方向未定，G2）；按 M1-D-300「夫妻宫位有用，却被刑、冲、破、穿」，本盘夫妻宫与月支构成相破的一类，故记破局；救应未判（G5），且本盘无配偶星地址（no_spouse_star），该句只落在宫位结构上。
- 边界：成立=以 D.b=子 为夫妻宫；e009 在该原局快照内成立；口径取 engine profile zi_shi=late_zi_split（日柱 庚子，日主 庚）。不成立=换 zi_shi=rollover_23 口径后日柱变辛丑（alt_chart_id=cf-62995823c069f1deacba），日主/十神/体用/边全变；或换岁运快照后 e009 变为 e022（实测 --dayun-index 4 --liunian 2026 边数 12→34）；或 M1-D-300 的「夫妻宫有用」前提不成立（该条只讲宫被刑冲破穿，破坏程度本卡不判）；或把 po 当第 5 种制法（M1-D-143 明确不并入四类制法，对应规格 §9.5）。
- confidence：**低**；unknowns：`G2` / `G5` / `no_spouse_star` / `boundary_zi_shi` / `suiyun_ten_god`
- 快照：`chart_id=cf-8b541a506fc413884431` `dayun_index=null` `liunian_year=null`

---

## 2 · 盘面事实（不产卡；规格 §5.1「① 排盘」段）

三盘各 8 个物理地址，十神取 `stem.ten_god` / `branch.main_ten_god`，藏干只能写 `addr⊕char`（G4）。以下全部现场跑 `engine.cli all` 得到。

### C1 `RF-2026-000125` · 丁卯 壬子 辛丑 乙未 · 乾 · `cf-5735e1472538ad92664b`

| 柱 | 干·十神 | 支·本气十神 | 藏干（`addr⊕char`） |
|---|---|---|---|
| year | `Y.s` 丁 七杀 | `Y.b` 卯 偏财 | `Y.b⊕乙` 偏财 |
| month | `M.s` 壬 伤官 | `M.b` 子 食神 | `M.b⊕癸` 食神 |
| day | `D.s` 辛 日主 | `D.b` 丑 偏印 | `D.b⊕己` 偏印 / `D.b⊕癸` 食神 / `D.b⊕辛` 比肩 |
| hour | `H.s` 乙 偏财 | `H.b` 未 偏印 | `H.b⊕己` 偏印 / `H.b⊕丁` 七杀 / `H.b⊕乙` 偏财 |

- 体用：体=`D.s`/`D.b`/`H.b`；用=`Y.s`/`Y.b`/`H.s`；双属=`M.s`/`M.b`
- 边 16 条；做功候选 17 个，`actor` 非空 12 个
- 夫妻宫 `D.b` 的 4 条边：`e012 liuhe[M.b,D.b]`、`e013 sanhui[M.b,D.b]`、`e015 chong[D.b,H.b]`、`e016 xing[D.b,H.b]`；其中 `e013`/`e015`/`e016` **不在 candidates 内**（`sanhui` 不在 kind 清单；`chong`/`xing` 两端皆体）
- 墓库：`D.b`=丑 为金库，openers=`e015,e016`、binders=`e012`（**开边与合边并存，孰胜不判**）；`H.b`=未 为木库，openers=`e015,e016`、chuan_po=`e014`
- 空亡：日旬空辰巳、年旬空戌亥，`hits` 为空（全盘无命中）
- `gaps_present`：G2 / G3 / G4 / G5 / muku_open_close

### C2 `RF-2026-000438` · 庚午 戊寅 己未 乙丑 · 坤 · `cf-f10b5515f2019638f42f`

| 柱 | 干·十神 | 支·本气十神 | 藏干（`addr⊕char`） |
|---|---|---|---|
| year | `Y.s` 庚 伤官 | `Y.b` 午 偏印 | `Y.b⊕丁` 偏印 / `Y.b⊕己` 比肩 |
| month | `M.s` 戊 劫财 | `M.b` 寅 正官 | `M.b⊕甲` 正官 / `M.b⊕丙` 正印 / `M.b⊕戊` 劫财 |
| day | `D.s` 己 日主 | `D.b` 未 比肩 | `D.b⊕己` 比肩 / `D.b⊕丁` 偏印 / `D.b⊕乙` 七杀 |
| hour | `H.s` 乙 七杀 | `H.b` 丑 比肩 | `H.b⊕己` 比肩 / `H.b⊕癸` 偏财 / `H.b⊕辛` 食神 |

- 体用：体=`Y.b`/`M.s`/`D.s`/`D.b`/`H.b`；用=`M.b`/`H.s`；双属=`Y.s`
- 边 14 条；做功候选 13 个，`actor` 非空 11 个
- 夫妻宫 `D.b` 的 4 条边：`e009 liuhe[Y.b,D.b]`、`e010 sanhui[Y.b,D.b]`、`e013 chong[D.b,H.b]`、`e014 xing[D.b,H.b]`；**4 条全部不在 candidates 内**（只读 candidates 会得出「夫妻宫无作用」）
- 墓库：`D.b`=未 为木库，openers=`e013,e014`、binders=`e009`；`H.b`=丑 为金库，openers=`e013,e014`、binders=`e012`、chuan_po=`e011`
- 空亡：日旬空子丑，命中 `H.b`（`[["H.b","day"]]`）——**空亡只是地址，不是吉凶结论**
- 配偶星地址（官杀，坤）：`M.b` 正官 / `M.b⊕甲` 正官 / `H.s` 七杀 / `D.b⊕乙` 七杀
- `gaps_present`：G2 / G3 / G4 / G5 / muku_open_close

### C3 `RF-2026-000894` · 壬戌 己酉 庚子 戊子 · 乾 · `cf-8b541a506fc413884431`

| 柱 | 干·十神 | 支·本气十神 | 藏干（`addr⊕char`） |
|---|---|---|---|
| year | `Y.s` 壬 食神 | `Y.b` 戌 偏印 | `Y.b⊕戊` 偏印 / `Y.b⊕辛` 劫财 / `Y.b⊕丁` 正官 |
| month | `M.s` 己 正印 | `M.b` 酉 劫财 | `M.b⊕辛` 劫财 |
| day | `D.s` 庚 日主 | `D.b` 子 伤官 | `D.b⊕癸` 伤官 |
| hour | `H.s` 戊 偏印 | `H.b` 子 伤官 | `H.b⊕癸` 伤官 |

- 体用：体=`Y.b`/`M.s`/`M.b`/`D.s`/`H.s`；用=**空**；双属=`Y.s`/`D.b`/`H.b`（全盘无「用」）
- 边 12 条（**无冲边、无六合边**）；做功候选 8 个，`actor` 非空 6 个
- 夫妻宫 `D.b` 的关系边只有 1 条：`e009 po[M.b,D.b]`（`po` 不在候选 kind 清单内 → 做功候选里没有它）
- 墓库：`Y.b`=戌 为火/土空库，`openers`/`binders` 皆无、`chuan_po=e007`（空库，不写「库冲开」）
- 空亡：日旬空辰巳、年旬空子丑；命中 `D.b`（夫妻宫）与 `H.b`，均为年旬
- 边界：`late_zi` 警告；`variants[axis=zi_shi].alt_chart_id=cf-62995823c069f1deacba`（该口径日柱为 辛丑）
- 配偶星：**无**（乾造无财；四柱与全部藏干皆无正财/偏财）
- `gaps_present`：no_spouse_star / boundary_zi_shi / G2 / G3 / G4 / G5 / muku_open_close

---

## 3 · 这套卡不能说什么（覆盖 `gaps_present`）

| 缺口 | 在三张卡上的具体落点 | 本文件怎么处理 |
|---|---|---|
| **G2** | 三张卡的边都是冲/刑/破，引擎 `actor=None`；连做功候选里也没有 actor 的有：C1 `e001/e007/e010/e012/e014`、C2 `e003/e012`、C3 `e011/e012` | 三张卡一律 `direction_known=false` + `actor/target=null`；不写「A 冲 B」，也不用原文克向去补（规格 §9.12） |
| **G3** | 支vs支不建克边（如 C1 `Y.b`=卯 与 `D.b`=丑、C2 `M.b`=寅 与 `D.b`=未、C3 `Y.b`=戌 与 `D.b`=子） | 卡里不出现「支上相克」的做功结论 |
| **G4** | 藏干无独立地址 | 只写 `D.b⊕己` 这类复合串，不声称藏干有独立地址 |
| **G5** | C1 有 3 条 `rescuer.met`、C2 有 3 条、C3 为 0 条，但都属子平八格，不是夫妻宫救应 | 三张卡 `rescue_judged=未判`，不写「化解」；C3 的 0 条不等于「无救应」 |
| **muku_open_close** | C1 `D.b`=丑 的 openers(`e015,e016`) 与 binders(`e012`) 并存；C2 `D.b`=未 的 openers(`e013,e014`) 与 binder(`e009`) 并存 | 只列开边/合边清单，不写「库被冲开/合住」；C1/C2 的 `unknowns` 带 `muku_open_close` |
| **no_spouse_star** | C3 无财星（乾造） | C3 只写「本盘无配偶星地址」，不写「配偶星受制」；M1-D-296（配偶宫×配偶星）因此**不能用**在 C3 上 |
| **boundary_zi_shi** | C3 晚子时，`rollover_23` 口径日柱变辛丑 | C3 的 `boundary.holds_when` 声明口径；`unknowns` 带 `boundary_zi_shi` |
| **suiyun_ten_god** | 三张卡的 ④ 都含引动字段，但 DY/LN 字的十神/体用取不到 | 只写边种 + 地址；`unknowns` 带 `suiyun_ten_god`；不对岁运字下十神判断 |

另外三条**没写**的判断（不是漏写，是写不出来）：

1. C1/C2 的「库开/库闭」——开边合边并存，无事实（`muku_open_close`）；
2. C1 的 `Y.b`=卯 入 `H.b`=未 墓带 `requires_judgment`（四正支一般作拱局）——只能写「入墓候选 + 需判断」；
3. C3 的 `po` 是否算一种做功——`M1-D-143` 明确不把「破」并入四类制法（规格 §9.5 待审）。

---

## 4 · 五元组自检表（中枢可直接核对）

| 检查 | C1-01 | C2-01 | C3-01 |
|---|---|---|---|
| ① 宫位 + ≥1 物理地址 + 十神等长 | day；`D.b`/`H.b`；偏印/偏印 | day；`D.b`/`H.b`；比肩/比肩 | day；`M.b`/`D.b`；劫财/伤官 |
| ① 边号在快照内存在 + kind/members 一致 | `e015` `e016` ✔ | `e013` `e014` ✔ | `e009` ✔ |
| ② 方向未定即置空（actor/target=null） | ✔ | ✔ | ✔ |
| ② `direction` 与边种相容（§3.3） | 冲 → false | 冲 → false | 破 → false |
| ③ 三态之一（非布尔） | 破局 | 破局 | 破局 |
| ③ `basis.kind` ∈ {structure_item, edge} | edge×2 | edge×2 | edge×1 |
| ③ `rescue_judged` | 未判 | 未判 | 未判 |
| ④ `scene` 1–2 句、无年份/年龄/概率/事件 | 2 句 ✔ | 2 句 ✔ | 2 句 ✔ |
| ④ `scene` 含本卡地址 | `D.b`/`H.b` | `D.b`/`H.b` | `D.b`/`M.b` |
| ④ `activation` 引动（none_observed + 边数证据） | 16 条全 natal | 14 条全 natal | 12 条全 natal |
| ⑤ 地址锚点覆盖 ① 的全部边与地址 | ✔ | ✔ | ✔ |
| ⑤ 原文 `path:line` 可解析且支持「结构」 | `M1-D-298:48` | `M1-D-298:48` | `M1-D-300:122` |
| `statement` 含 ① 的地址 + 边号 | ✔ | ✔ | ✔ |
| 边界双向具体 | ✔ | ✔ | ✔ |
| `unknowns` 全部是 §7.3 ID | 4 个 | 4 个 | 5 个 |
| `snapshot` 三字段齐（null 也写） | ✔ | ✔ | ✔ |
| `pre_p1: true` | ✔ | ✔ | ✔ |

机器校验（脚本临时跑、已删）：逐卡比对 `chart_id`/四柱/十神/`tiyong`/`edge kind+members+group+completeness`/`basis`/`statement` 地址/锚点原文行/`scene` 禁词表 → **ALL CHECKS PASS**。

---

## 5 · 已知偏差与待审项（写卡人必须自曝）

1. **`scene_refs` 为空，且这是硬伤。** 规格 §2.4 要求 `scene_refs` 引用 ≥2 张**同 `case_id`** 的卡；本任务是一盘一卡，同盘没有第 2 张卡可引，所以三张卡都是 `[]`。按 §2.4 字面，这三张卡**不合格**；`L20/L21` 不会命中（空数组不引用不存在的卡），但「≥2」门槛没达。补卡可解，但补卡超出 T-176 的「3 张卡」范围。
2. **一盘一卡 ⇒ 单盘报告过不了 §5.3。** 报告级门槛要求一份报告里 ≥3 张通过 Linter 的关系型卡；本交付是「3 张卡分属 3 张盘」，任何一张盘单独成报告都只有 1 张卡。若 P1 走「一盘一卡」，§5.3 必须先改口径。
3. **`activation` 用了 `none_observed`，与 §3.4 示例写法不同。** §2.4 说「该快照未见引动边 → 写 `none_observed` + 边数证据」，§3.4 的合格卡示例却用 `kind=chong` + 通配 `LN{year}.b`。原局快照 DY/LN 边恒为 0 条，本文件从 §2.4（更具体的规则），并把「换快照后什么条件算引动」写进 `condition`。
4. **C3 的「目标受破」踩在判据与枚举的缝上。** §2.3 的破局判据文字只列「冲/刑/穿」，但同段 `basis.assert` 枚举含「目标受破」、§3.3 的 `direction` 枚举也含「破」。本卡从枚举；需外部审计确认（§9.5 同一处）。
5. **C1/C2 的破局只有 `edge` 依据，没有 `structure_item`。** 婚姻域无结构项（G5），这正是规格 §9.13 的待审项：若外部审计否掉「原文判据 + edge」这条路径，C1/C2 只能降级为假设（三态里没有第四种）。**这是本交付最大的未决风险。**
6. **C1/C2 共用同一原文锚点 `M1-D-298:48`。** 两盘结构同为夫妻宫冲+刑，锚点相同是事实；这**不构成锚点独立性的证明**。
7. **C3 的 `M1-D-300` 结构句在 `:122`，而 entry 的 `raw_anchor` 记 `:124`。** `:124` 讲的是「破坏程度 → 是否离异」（吉凶/事件半句，按 L13 不引用）。本卡引 `:122` 的结构句，并在 `statement` 里只保留「夫妻宫位有用，却被刑、冲、破、穿」。
8. **C3 的 `confidence=低` 是三条原因叠加**：四柱不唯一（`boundary_zi_shi`）、夫妻宫只有一条 `po` 边、`po` 是否算做功待审（§9.5）。C1/C2 给「中」而不给「高」，因为 ③ 的破局只靠 `edge`（§9.13 未决）。
9. **`chart_id` 随输入形态变。** 用 `--birth` 得到卡里登记的 `cf-5735e1472538ad92664b` / `cf-f10b5515f2019638f42f` / `cf-8b541a506fc413884431`；用 `--pillars` 会得到另一串 id（`cf-ada5459163b88f49505e` / `cf-f835f14ca5091eec536d` / `cf-48de88b1324fbde0476f`），但**边号、kind/members、tiyong 完全一致**（三盘逐项比对过）。核对边号用哪种输入都可以，核对 `chart_id` 必须用 `--birth`。

---

## 6 · 复现命令（三盘逐条可回查）

```powershell
# 原局快照（三张卡的快照）
.venv\Scripts\python.exe -m engine.cli all --birth "1987-12-18 13:15:00" --gender 乾 --json   # C1
.venv\Scripts\python.exe -m engine.cli all --birth "1990-02-23 01:48:00" --gender 坤 --json   # C2
.venv\Scripts\python.exe -m engine.cli all --birth "1982-09-14 23:55:00" --gender 乾 --json   # C3

# 四柱口径（边号一致，chart_id 不同）
.venv\Scripts\python.exe -m engine.cli all --pillars "丁卯 壬子 辛丑 乙未" --gender 乾 --json
.venv\Scripts\python.exe -m engine.cli all --pillars "庚午 戊寅 己未 乙丑" --gender 坤 --json
.venv\Scripts\python.exe -m engine.cli all --pillars "壬戌 己酉 庚子 戊子" --gender 乾 --json

# 边界（all 删空值，必须用 chart）
.venv\Scripts\python.exe -m engine.cli chart --birth "1982-09-14 23:55:00" --gender 乾 --json

# 岁运快照（只在 boundary.fails_when 里引用，不产卡）
.venv\Scripts\python.exe -m engine.cli all --birth "1987-12-18 13:15:00" --gender 乾 --dayun-index 5 --liunian 2026 --json  # 16→39，e031/e032
.venv\Scripts\python.exe -m engine.cli all --birth "1990-02-23 01:48:00" --gender 坤 --dayun-index 4 --liunian 2026 --json  # 14→39，e028/e029
.venv\Scripts\python.exe -m engine.cli all --birth "1982-09-14 23:55:00" --gender 乾 --dayun-index 4 --liunian 2026 --json  # 12→34，e022
```

- 回归现状：`.venv\Scripts\python.exe -m pytest -q` → **1374 passed, 1 skipped**（0 failed；skip 为 `tests/tools/test_bundle_pii.py` 的 T-114 过渡 skip）。
- 本任务未新增代码、未改 engine/规则/测试/案例 JSON，故不改任何门禁。
