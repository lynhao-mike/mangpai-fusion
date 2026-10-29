# T-190 BRIEF · anchor-60 策展（annotator A）

- 日期：2026-10-29
- 角色：annotator A（只做 A 卷；B 复核由中枢另派，A 不宣称双人复核完成）
- 任务卡：`tasks/T-190/PROMPT.md`；规格：`docs/specs/adjudication-a-plus-v1.md` §1/§6

## 1. 改动文件

| 文件 | 说明 |
|---|---|
| `META/p1-anchor-60-blind-v1.json` | 盲卷 60 条；只含 case_id/chart_id/四柱/性别/层/target_relation；无 source_ref、无 locator、无答案 |
| `META/p1-anchor-60-answers-v1.json` | 答案 60 条；relation（actor/target/mutual/expected_direction）+ quote + source_ref；ambiguous 另带 conflict_quotes[2] 与 source_texts[2+] |
| `META/p1-anchor-60-v1.md` | 清单 / 盘数 / 类型 / 三重零校验 / engine.cli 预检表 / sha256 / 缺口 |
| `tasks/T-190/BRIEF.md` | 本文件 |
| `tasks/T-190/STATUS.md` | 追加 Execution Log |

未改任何 engine / 规则 / dev 答案 / 测试 / PROMPT.md；未做 git 写操作；未跑 engine 评分。

## 2. 原始输出

```text
$ python <verify>  # 独立校验脚本：读两份 JSON + 回读原文
cases 60 charts 53 layers {'fixed': 10, 'dynamic': 40, 'ambiguous': 10}
fails 0
sha256 blind   9c730d35ae1a1d8881ec55522ac114ee3d83bbbbd54802e7c87d55fca7217bc3
sha256 answers f3c06db547833e595b9174b43a1e9a1344ab3e10e79462b48673425a2acd49c8
mech dist: {'克': 3, '生': 3, '化': 2, '墓': 3, '冲': 12, '合': 12, '穿': 14, '刑': 11}
```

- 类型：fixed 10（克 3 / 生 3 / 化 2 / 墓 2）、dynamic 40（冲 10 / 合 10 / 穿 10 / 刑 10）、ambiguous 10
  （ambiguous 内部：墓 1 / 冲 2 / 合 2 / 穿 4 / 刑 1）；`破` 0 条。
- 方向：fixed 10/10 actor→target；dynamic 37 actor→target + 3 mutual（A60-046/047/050 两伤刑）；ambiguous 10 全 `needs_judgment`。
- 盘数：53 盘；7 盘各 2 条（辛卯 戊戌 己亥 癸酉 / 壬子 壬寅 庚辰 辛巳 / 癸卯 壬戌 癸巳 庚申 /
  丁亥 壬子 庚辰 壬午 / 甲寅 己巳 癸亥 戊午 / 乙未 壬午 甲子 甲戌 / 乙未 乙酉 丙戌 己丑），其余 46 盘各 1 条。
- 三重零：golden-20 / holdout-20 / fresh-40 / fresh-40-routing 四对照集，四柱重叠 0、case_id·chart_id 重叠 0、
  同文件原文行区间重叠 0；最近距离 4 行（A60-030、A60-040，不同案例）。
- engine.cli：53/53 盘 `python -m engine.cli all --pillars "<四柱>" --gender <乾|坤> --json` 退出码 0 且返回 chart_id。
- 另加静态校验：每盘过六十甲子配对 + 五虎遁（年→月）+ 五鼠遁（日→时）。淘汰 4 张原书排印/OCR 不合法的盘
  （癸卯 戊申 己酉 甲戌；己酉 辛丑 己亥 丙寅；壬子 庚戌 辛丑 己未；己酉 甲戌 乙丑 庚午），
  以及 2 张与 dev 四柱相撞的候选（己未 癸酉 壬寅 庚子＝G20-015；乙巳 乙酉 戊子 甲寅＝P1-H12）。
- 引文：60 条 quote 全部为原文原始行的逐字子串（含原始空格；未跨 `**` 记号边界）；
  ambiguous 的 conflict_quotes 两条互异且各自能在 source_texts 的某一行内逐字检出。

## 3. 未完成与风险

1. **未做双人复核**：只有 A 卷。B 由中枢另派；`p1-anchor-60-v1.md` 状态仍写“待 B 复核”。
2. **8 条性别未注明**：原书该盘以人名代替乾/坤（如 19 书「朱熔基：…」「奥那西斯：…」「克林顿：…」、
   30 书「梅加瓦蒂：…」、33 书无标注等），盲卷记 `未注明`；engine 预检按 `乾` 跑通，仅用于排盘合法性，不影响四柱事实。
3. **A60-015 含岁运重申**：引文「己卯冲酉夫妻宫」以 99 己卯年重申原局卯酉冲；如 B 要求纯原局引文，可整条替换。
4. **A60-057 自身引文是并列句**：「酉戌穿,丑午穿」只并列两条穿，方向由 conflict_quotes 承担；可换单句盘。
5. **行区间最近 4 行**：A60-030 与 23 书 L77-L81、A60-040 与 23 书 L3619-L3623 相距 4 行，无重叠；
   若上游要求 ≥10 行缓冲，这两条需换。
6. **未接评分器**：未跑 `tools/p1_assertion_eval*.py`，未做任何 engine 评分或 3 次盲跑。
7. **固定层 3 条是地支相克**：本卷 fixed 全部用地支-地支关系（符合中枢“地址落到单个地支字”的要求），
   因此 `克` 取的是地支相克（如 未克子、午克酉、戌克亥），不是天干克；`化` 取印化官杀（辰化午、子化申），
   `墓` 取库为 actor（未墓寅、辰墓未）。

## 4. 下游须知（给 B / 评分器）

- 盲卷字段：`case_id, chart_id, four_pillars, gender, layer, target_relation{addr_a, addr_b, char_a, char_b, mechanism}`。
  **不含** source_ref / locator / quote / relation / conflict_quotes / source_texts / actor / expected_direction。
- 答案字段：`relation{a,b,kind,mechanism,actor,target,mutual,expected_direction}`；`kind` 用引擎口径
  （ke/sheng/hua/muku/chong/he/chuan/xing）。ambiguous 用 `actor=null, expected_direction=needs_judgment`。
- 地址口径：`Y.b/M.b/D.b/H.b` ↔ 四柱第 1–4 柱地支；60 条全部为地支-地支，无天干/柱级编码。
- `source_ref` 形式：`sources/duan/<书名>.md:L起-L止`（chart 行 → quote 行），B 可直接按行区间逐字回读。
- 两文件已冻结 hash（见 §2）。若 B 要求改动任一条，需重算 hash 并同步 `p1-anchor-60-v1.md` §6；
  在 B 复核前不得据此卷宣称任何精度。
- 复核建议顺序：① 引文逐字（60 条）；② 方向/actor 是否被原文直接支持（重点 fixed 10 与 mutual 3 条）；
  ③ ambiguous 10 的正反引文是否真冲突而非互补；④ 是否与 dev 三套有任何四柱/行区间交集。
