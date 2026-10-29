# T-178 BRIEF · 墓用 actor 审计 + actor 规则表（只读规格）

- 状态：✅ 交付（只读审计 / 规格；未改 answers、hold-out、engine、规则、测试；无 git 写操作）
- 任务卡：`tasks/T-178/PROMPT.md`
- 产物：`META/p1-muku-actor-audit-v1.json`（四条逐条 + 总判定 + 分母裁决）、`META/p1-muku-actor-audit-v1.md`、
  `docs/specs/actor-rules-v1.md`（九类规则表 + 原文例子 + 引擎映射）
- 一句话：**四条墓用 4/4 `engine_wrong`，0 `label_wrong`，0 `convention_conflict`；标注 `a=库、actor=库` 与原文力向
  （「辰墓了丑」「未墓寅」「被辰所控制」「丑也有墓酉之象」、任派「墓库…表示制」）一致，引擎墓用候选
  `members=(入库方,库)、actor=入库方` 反了；因此方向主分母 16 只在冻结时成立，审计后应回到 20（16 降为 sensitivity），
  四条不改不剔，只建议补 quote。**

---

## 1. 改动文件

**新建**

| 文件 | 说明 |
|---|---|
| `META/p1-muku-actor-audit-v1.json` | 四条墓用逐条（clauses/roles/verdict/证据等级/引擎现状/修复）、总判定、分母裁决、规则表摘要、下游清单 |
| `META/p1-muku-actor-audit-v1.md` | 同内容人读版：证据链、四条判定、两个「为什么不」、引擎修复规格、分母裁决、风险 |
| `docs/specs/actor-rules-v1.md` | 九类 actor 规则表（合/冲/刑/穿/破/克/生/化/墓），每类 `source_ref` + 正例 + 反例 + 引擎映射 + 未知时 `null`；三条硬规则、T-174 三条教训、证据分级、实现纪律、表外 kind、与 P1 评分的关系 |
| `tasks/T-178/BRIEF.md` | 本文件 |

**修改**

| 文件 | 改动 |
|---|---|
| `tasks/T-178/STATUS.md` | 追加 Execution Log 一行 |

**未改**：`META/p1-holdout-answers-v1.json`、`META/p1-holdout-v1.json`、`META/p1-holdout-freeze-v2.json`、
`META/p1-holdout-baseline-v1.json`、`engine/**`、`docs/specs/single-chart-analysis-v1.md`、`sources/**`、`tests/**`、`tools/**`。
**未做**：任何 git 写操作（无 commit/push/checkout/stash/reset/clean）；未跑评分器（会覆盖基线产物）。

```text
$ git status --porcelain          # 收尾时
?? META/p1-muku-actor-audit-v1.json      ← 本卡
?? META/p1-muku-actor-audit-v1.md        ← 本卡
?? docs/specs/actor-rules-v1.md          ← 本卡
?? tasks/T-178/BRIEF.md                  ← 本卡
 M tasks/T-178/STATUS.md                 ← 本卡（追加一行）
?? mangpai-fusion-offline-04677d2c.zip   ← 既有未跟踪，未碰
```

## 2. 原始输出

### 2.1 引擎现场复核（四条墓用的墓用候选）

```text
$ .venv\Scripts\python.exe -m engine.cli all --pillars "<四柱>" --gender <乾|坤> --json   （过滤 relation_kind=muku）

== 壬辰 壬寅 己丑 戊辰 ==            # P1-H13
  members=M.s,Y.b actor=M.s          # 壬→辰（财入墓）
  members=Y.s,H.b actor=Y.s          # 壬→辰
  members=M.s,H.b actor=M.s          # 壬→辰
  # 无一条跨答案端点 a=辰/b=丑；丑→辰 被 _crosses 过滤（两端皆体）

== 壬寅 己酉 丁丑 己酉 ==            # P1-H14
  members=M.b,D.b actor=M.b          # 酉→丑
  members=H.b,D.b actor=H.b          # 酉→丑

== 壬午 辛亥 庚辰 丁亥 ==            # P1-H15
  members=Y.s,D.b actor=Y.s          # 壬→辰（不跨端点）
  members=M.b,D.b actor=M.b          # 亥→辰
  members=H.b,D.b actor=H.b          # 亥→辰

== 戊申 甲寅 己未 辛未 ==            # P1-H16
  members=M.s,D.b actor=M.s          # 甲→未（不跨端点）
  members=M.b,D.b actor=M.b          # 寅→未
  members=M.s,H.b actor=M.s          # 甲→未（不跨端点）
  members=M.b,H.b actor=M.b          # 寅→未
```

结论：**所有墓用候选一律 `members=(入库方,库)`、`actor=members[0]=入库方`**，与 `structure_check.py:505` 一致；
基线行的 `candidates` 是评测器按答案端点过滤后的视图（`tools/p1_holdout_eval.py:276-279`），不是引擎全部候选。

### 2.2 原文 quote 逐字校验（44 条）

```text
checked=44 miss=0
  （九类正例/反例 34 条 + 墓用定向句 8 条 + 定义句 2 条；全部 path:line 行内命中）
json-quotes checked=22 miss=0          # 审计 JSON 的 basis 9 条 + clauses 13 条
```

两次修正记录（已改）：

- `sources/duan/MinerU_markdown_33…:L942` 是繁体「卯破午主破**財**」，不是「财」；
- 「庚金生坐下子水和年干壬水」在 `sources/duan/MinerU_markdown_墓__穿…:L125`，不是 L124。

### 2.3 回归（未改代码，确认现状 0 failed）

```text
$ .venv\Scripts\python.exe -m pytest -q
1420 passed, 1 skipped, 1 warning in 133.44s (0:02:13)     exit 0
SKIPPED [1] tests\tools\test_bundle_pii.py:34: 脱敏脚本缺失（T-114 已知项）
```

与 `docs/reviews/p1-baseline-verdict-v1.md` 记录的 1420/1 一致；本卡未新增代码，skip 非本卡引入。

### 2.4 两次运行 JSON 一致

```text
run1 canonical sha256 = run2 canonical sha256 = 66a39037f5c517fcd05142888b5acd7a495ffb6f21ccef89ad516f0788b4d3fe
file sha256 = 0ac2c7fef47ae6d76f22ab5d7195f4f1cb2501edb8c0da6f0671ccc419a36bc3
md   sha256 = f51027f09a0fb559ee102c71fa9f93235d2252dae964e6a166989e7ea50a69d2
spec sha256 = 00d48c16ff4c5d400b466f74dd20e707c555c4b93812a323776d54e7e4de9023
```

JSON 无时间戳/随机序；两次独立进程按 `json.dumps(sort_keys=True, ensure_ascii=False)` 重序列化，哈希相同。
输入产物哈希（写进审计 JSON `inputs`）：answers `b1075a39…`、freeze v2 `f2750a73…`、baseline `7086c461…`（与裁决书一致）、
blind `593f4dbe…`、verdict `9a287f8a…`、`structure_check.py` `9298cbfc…`。

## 3. 未完成与风险

1. **H14/H16 有证据缺口**：H14 的定向句在同页另一造（`L2338`「丑也有墓酉之象」），H16 没有「未墓寅」逐字句，
   依据是定义句 `L2274` + 收藏/释放语义（`L4105`）+ 同页通用句式「被墓之神」（`L4099`）。判定不变（力向仍是库→入库方），
   但若中枢采用「所引句逐字明示」最严口径，这两条应转 sensitivity（18 例分母），不是改 verdict。
2. **H13 是另一个缺口**：即使 actor 修好，H13 仍 `no_candidate`（丑→辰 两端皆体被过滤），要等 T-179 的体-体/双属过滤。
   别把 H13 的 `no_edge` 当成 actor 修复失败。
3. **未改 answers 的 quote**：本卡只读，H13/H15/H14/H16 的 quote 仍是入墓句；建议中枢在后续卡里补成定向句或加 `quote_force`，
   否则 answer 的字段语义（actor＝原文明确指出的施力方）在文字上仍缺一环。
4. **评测器文档与引擎实现自洽但与本审计相反**：`tools/p1_holdout_eval.py:41-46` 写「引擎 actor 是入库方 … 这是口径对立，不是 bug」。
   引擎一改，这句必须同步，否则工具文档说谎。
5. **未跑评分器**：`tools/p1_holdout_eval.py` 默认写 `META/p1-holdout-baseline-v1.json`，会覆盖基线产物，按卡不跑；
   本卡的引擎结论来自 `engine.cli` 现场 + 基线 JSON 行对照。
6. **无 Blocker**：审计可交付、规格可实施；剩余是中枢决策（是否重冻 v3）与 T-179 的代码落地。

## 4. 下游须知

1. **判定**：四条墓用 4/4 `engine_wrong`；`label_wrong`=0、`convention_conflict`=0；a/b/actor 全部维持，不更正、不剔除。
2. **分母**：16 只作冻结时的临时口径；审计后应回到 **20**（目标 80%＝16/20，kill 60%＝12/20），16 作 sensitivity。
   必须在**修复前**重冻 v3（freeze v2 discipline 允许基于 pre-fix 定义冲突修订；post-fix 不得再改）。
3. **修复按哪条规则**：`docs/specs/actor-rules-v1.md` §3 第 9 行（墓）＋§5.2：
   `structure_check.py:498-506` 改为 `emit("墓用","muku",None,(m.addr,c.addr),m.addr,...)`；`relations.muku` 事实层不动；
   `:72` 注释同步；评测器说明与 `test_p1_holdout_eval.py:173-184` 的旧约定 fixture 同步重写（不得放宽断言）。
4. **对称关系不动**：合/冲/刑/穿/破 现状 `actor=null` 已符合规则表，别在修 actor 时顺手给它们赋向。
5. **顺序**：先冻结规则（本 spec）→ 再改引擎 → 再跑 post-fix；不得用 hold-out 结果回头调规则。
