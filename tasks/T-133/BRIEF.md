# T-133 · BRIEF — 段派婚姻判据原文锚点（B1 前置）

- 任务卡：`tasks/T-133/PROMPT.md`
- 状态：✅ 完成（16 条锚点记录 / 6 组判据：4 组 anchored、1 组 not_found、1 组 unmodeled）
- 产物：`theory/claims/drafts/duan-marriage-anchors.yaml`

## 1. 改动文件

| 类型 | 路径 |
|---|---|
| 新建 | `theory/claims/drafts/duan-marriage-anchors.yaml`（16 条记录，6 组判据） |
| 新建 | `tasks/T-133/BRIEF.md`、`tasks/T-133/STATUS.md` |

**未改动**：`theory/_ir/`、`sources/`、`engine/`、`tests/`、任何语料原文、任何 YAML 之外的产物。
本任务未跑 `git commit/push/checkout/stash/reset`。

生成方式：一次性脚本调用 `python -m tools.query_theory`（唯一入口），从返回 JSON 的 `statement` 字段
按 id 取值写入 YAML，`quote` 是工具返回串的逐字切片（脚本内断言 `quote in statement`，否则中止）。
没有手抄、没有补字、没有补页码。

## 2. 原始输出（query_theory 真实返回）

统一调用参数：`--schools duan --top-k 10 --per-school-cap 0 --json`。
（`--per-school-cap` 默认为 2，会让段派命中被截断；取证时已显式设 0，任务卡示例命令的默认值也记录在 §2.1。）

### 2.1 任务卡指定命令（原样执行）

```
.venv\Scripts\python.exe -m tools.query_theory --query "克者被合绊 制用" --schools duan --top-k 5 --json
```

[exit 0] 命中 2 条（该命令未指定 per-school-cap，取默认值 2）：

```json
[{"id":"M1-D-009","school":"duan","classic_name":"段建业盲派","title":"做功 1 — 制用结构（80%）","domain":"做功","tags":["做功","lifa"],"statement":"段建业原文：「八字通过体用与宾主之间制的关系，得到命主所用的东西。因为这种结构非常常见，又占八字的大多数」 - 段派的 5 类制局通辨子项（D-01 §5.2，对应 module-1-duan §6.1-6.5）： 1. 比劫与财的配置（比肩制财局 / 财制比劫局） 2. 比劫与官杀的配置（比劫制官杀局 / 官杀制比劫局） 3. 伤食与官杀的配置（伤食制官杀局 / 官杀制伤食局） 4. 印星与伤…","source_ref":{"path":"theory/raw/duan/d01-deep-read.md","anchor":"line:126"},"score":14.0},{"id":"M1-D-116","school":"duan","classic_name":"段建业盲派","title":"制用结构做功工程化","domain":"做功","tags":["做功","lifa"],"statement":"体（日主/印/禄）+ 宾位之用（财/官/伤食）发生 刑/冲/克/穿 prerequisites=制神在主位或主党中 被制神在宾位（财/官等） 制法不被解（无合化救应） conclusion: - 制法占段派 60%+ 案例（\"非常常见，又占八字的大多数\"） - 制法成立 → 命主主动获取所追求之物 - 制力来自主位 ＞ 制力来自宾位（后者效率较低） falsifiable_by: - 若制神被合…","source_ref":{"path":"theory/raw/duan/d10-theory.md","anchor":"line:263"},"score":14.0}]
```

同一 query 放开 `--per-school-cap 0`、`--top-k 10` 后为 4 条：

```json
[{"id":"M1-D-009","title":"做功 1 — 制用结构（80%）","domain":"做功","source_ref":{"path":"theory/raw/duan/d01-deep-read.md","anchor":"line:126"},"score":14.0},{"id":"M1-D-116","title":"制用结构做功工程化","domain":"做功","source_ref":{"path":"theory/raw/duan/d10-theory.md","anchor":"line:263"},"score":14.0},{"id":"M1-D-343","title":"穿与被穿看势","domain":"lifa","source_ref":{"path":"sources/duan/MinerU_markdown_体用_2056043694349017088.md","anchor":"line:161"},"score":10.0},{"id":"M1-D-173","title":"做功层次计量（1层百万~4层百亿）","domain":"过河拆桥","source_ref":{"path":"theory/raw/duan/d15-d18-theory.md","anchor":"line:281"},"score":2.0}]
```

### 2.2 not_found 的直接依据：「旺透」在段派索引中零命中

```
.venv\Scripts\python.exe -m tools.query_theory --query "旺透" --schools duan --top-k 10 --per-school-cap 0 --json
```

[exit 0] []

对照：「得长生 旺透」同样返回 `[]`。即「旺透」是任务卡的措辞，不是原文用语。

### 2.3 被引用命中的原始对象（逐字）

**M1-D-316**（首次由 Q02 返回，score=36.0）

```json
{"id":"M1-D-316","school":"duan","classic_name":"段建业盲派","title":"卯合戌制与戌绊卯不制的级别差","domain":"geju","tags":["过河拆桥","卯戌","合制","绊","级别","geju"],"statement":"同为卯戌关系，级别大不相同：前造是戌绊卯不制，本造是卯合戌还制；合而制之者级别远大","source_ref":{"path":"sources/duan/MinerU_markdown_命格组合_2056043853946478592.md","anchor":"line:31"},"score":36.0}
```

**M1-D-108**（首次由 Q02 返回，score=2.0）

```json
{"id":"M1-D-108","school":"duan","classic_name":"段建业盲派","title":"干合贪合而忘抗","domain":"签字+案例","tags":["签字+案例","geju"],"statement":"大运/流年与日主之忌神相合 conclusion: 忌神被合住 → 当年忌作用减弱 → 反成喜 falsifiable_by: 若合而不能化，仅减弱不消除","source_ref":{"path":"theory/raw/duan/d03-theory.md","anchor":"line:556"},"score":2.0}
```

**M1-D-364**（首次由 Q02 返回，score=10.0）

```json
{"id":"M1-D-364","school":"duan","classic_name":"段建业盲派","title":"强弱角度与做功角度的分别","domain":"lifa","tags":["合绊","做功角度","强弱角度","寅亥","身强财旺","lifa"],"statement":"合财看身强弱是从强弱角度讲；寅亥合绊、寅与亥不发挥作用，是这两字的做功角度看，而不是强弱角度看——两个角度不可混淆","source_ref":{"path":"sources/duan/MinerU_markdown_宾主作用_2056044174571667456.md","anchor":"line:173"},"score":10.0}
```

**M1-D-194**（首次由 Q03 返回，score=4.0）

```json
{"id":"M1-D-194","school":"duan","classic_name":"段建业盲派","title":"婚外情桃花 3 类","domain":"婚姻判定","tags":["婚姻判定","unmapped"],"statement":"判定命主是否有婚外情 prerequisites=配偶星宫+桃花星分布 conclusion: 女命禄入主合他星=桃花；男命劫财合别人财=外遇；暗合(寅丑/亥午等)=暗中关系；伤官坐花宫/门户=明桃花；配偶宫被穿倒+他星趁虚=第三者 falsifiable_by: 有桃花象但被合绊锁死不应","source_ref":{"path":"theory/raw/duan/d19-d24-theory.md","anchor":"line:303"},"score":4.0}
```

**M1-D-152**（首次由 Q04 返回，score=18.0）

```json
{"id":"M1-D-152","school":"duan","classic_name":"段建业盲派","title":"比劫去财格 — 财弱被制反主富","domain":"实战签字","tags":["实战签字","geju"],"statement":"命局以财作忌神 + 比劫制财 → 反主富 prerequisites=财星弱（虚透 / 被制 / 入墓） 比劫有力（旺 / 紧贴财 / 盖头） 4 类成立条件之一： 1. 财多身弱无印扶身（用比劫扶身 + 制财） 2. 官杀多身弱（财弱反主富，财旺主贫） 3. 任何类型 + 财弱被制 4. 比劫为\"主\"财为\"客\"（自己劫得他人之财） conclusion: - 反向铁律：\"财者凡人俱喜，命中忌财…","source_ref":{"path":"theory/raw/duan/d06-d09-theory.md","anchor":"line:740"},"score":18.0}
```

**M1-D-183**（首次由 Q05 返回，score=4.0）

```json
{"id":"M1-D-183","school":"duan","classic_name":"段建业盲派","title":"干支虚实 — 虚透=弱化气化","domain":"干支虚实 + 互通 + 冲换象","tags":["干支虚实 + 互通 + 冲换象","unmapped"],"statement":"判定某天干在八字中的虚实状态 prerequisites=以坐支定虚实：有根有力=实，无根虚浮=虚 conclusion: 虚用（财虚/杀虚）论吉：财虚=才华不贪财/杀虚=名气无权；实用论实力；应期中虚透=该字要跑了/弱化了 falsifiable_by: 虚透之神被合实则不论虚","source_ref":{"path":"theory/raw/duan/d15-d18-theory.md","anchor":"line:566"},"score":4.0}
```

**M1-D-149**（首次由 Q06 返回，score=6.0）

```json
{"id":"M1-D-149","school":"duan","classic_name":"段建业盲派","title":"忌神三种强弱策略（不预设与制法关系构成全组合矩阵）","domain":"制法","tags":["制法","lifa"],"statement":"命局有忌神（含官杀作忌） + 需识别该忌神的强弱状态 → 选取制法 prerequisites=完成忌神识别（M1-D-115 贼神理论 + M1-D-122 富贵贫贱档） 完成忌神强弱判定（弱 / 略偏旺 / 旺） conclusion: - 忌神 3 种制法（D-09 §十一 line 706 \"若是弱的官杀要旺制（贼神捕神）；若是官杀略偏旺要平衡制（用印化杀为用化敌为友）；若是旺的官杀要弱…","source_ref":{"path":"theory/raw/duan/d06-d09-theory.md","anchor":"line:583"},"score":6.0}
```

**M1-D-343**（首次由 Q01 返回，score=10.0）

```json
{"id":"M1-D-343","school":"duan","classic_name":"段建业盲派","title":"穿与被穿看势","domain":"lifa","tags":["穿","势","得势","制用结构","lifa"],"statement":"在原局中确定穿与被穿：相克之穿看势在哪里，哪方得势即能穿了对方","source_ref":{"path":"sources/duan/MinerU_markdown_体用_2056043694349017088.md","anchor":"line:161"},"score":10.0}
```

**M1-D-185**（首次由 Q07 返回，score=4.0）

```json
{"id":"M1-D-185","school":"duan","classic_name":"段建业盲派","title":"冲的远近与换象","domain":"干支虚实 + 互通 + 冲换象","tags":["干支虚实 + 互通 + 冲换象","unmapped"],"statement":"命局/大运/流年出现六冲 prerequisites=区分远近强弱 conclusion: 近冲库=坏库中之物；远冲库=开库；旺冲衰=冲去/取代；流年冲八字=动；大运冲八字力量相当=破；强方取代弱方信息(换象) falsifiable_by: 远冲库但库中无有用之物则开库无益","source_ref":{"path":"theory/raw/duan/d15-d18-theory.md","anchor":"line:622"},"score":4.0}
```

**M1-D-220**（首次由 Q08 返回，score=14.0）

```json
{"id":"M1-D-220","school":"duan","classic_name":"段建业盲派","title":"反用 vs 弱制辨析","domain":"体用","tags":["体用","lifa"],"statement":"命局中弱方制强方（如辛制群丙、金制火势） prerequisites=存在力量悬殊的制克关系 conclusion: 反用=我方弱但借对方之力为己用（撒切尔辛合制群杀、徐向前丑金库集团军被火制）； 弱制=以弱力真正制住强方（需要特殊条件）； 阎锡山：非反用非弱制，是金多入墓丑+丁丑同象完成做功 falsifiable_by: 辛制群杀命局中辛确实克掉了火（则为强制非反用）","source_ref":{"path":"theory/raw/duan/d25-d29-theory.md","anchor":"line:291"},"score":14.0}
```

**M1-D-024**（首次由 Q03 返回，score=2.0）

```json
{"id":"M1-D-024","school":"duan","classic_name":"段建业盲派","title":"制法 4 — 条件性穿制（来源冲突）+ 夹制/远制","domain":"制法","tags":["制法","lifa"],"statement":"> 初级讲义：「**六穿中，只有酉戌穿、卯辰穿、子未穿、丑午穿都可以相制**。**申亥穿、寅巳穿相生不能制**，但有个坏的象，可以坏了六亲或宫位。丑午之间也是相生，但因丑能晦午火，所以也有相克的意思。」 > > 同一合集另一节又说「穿制不了对方……唯有穿制不了」（`sources/duan/MinerU_markdown_21.大连段建业-面授讲义（合集）134页_205604522200262…","source_ref":{"path":"theory/raw/duan/d01-deep-read.md","anchor":"line:251"},"score":2.0}
```

**M1-D-178**（首次由 Q09 返回，score=2.0）

```json
{"id":"M1-D-178","school":"duan","classic_name":"段建业盲派","title":"六穿性质与功能边界（损害分层；“穿制”原文有冲突）","domain":"制法","tags":["制法","lifa"],"statement":"命局出现穿的组合 prerequisites=子未/丑午/卯辰/酉戌(克泄穿) vs 寅巳/申亥(生穿) conclusion: D-15将六穿分为克泄穿与生穿，并说明仇恨、不和、损坏、穿倒等含义；但“穿不能制”与D-21同合集后文及D-02初级讲义中的条件性穿制说法直接冲突。D-29另有穿后仍可作功但费力/不净的问答案例，证明“穿”不等于关系链必然失效，却不能单独解决其是否属于制的术语争议。M…","source_ref":{"path":"theory/raw/duan/d15-d18-theory.md","anchor":"line:435"},"score":2.0}
```

**M1-D-047**（首次由 Q10 返回，score=4.0）

```json
{"id":"M1-D-047","school":"duan","classic_name":"段建业盲派","title":"夹制常见未尽；“远制/留余烟”原文定位待核","domain":"财运判定","tags":["财运判定","unmapped"],"statement":"项：5；交接文档主题：制净 / 制尽；状态：已核对；核对结论 / 下一步：原文确有“制干净/制净/制尽/不尽”等定性用词，但未找到净与尽之间稳定的术语分级或数值阈值。初级/中级讲义支持夹制/夹冲常不尽；面授讲义也有夹住制净的具体案例，故不能作绝对状态。同一命局不同 occurrence 可分别判为未净/制净，双向做功也会改变“制尽”判断。完成度不等于效率或吉凶。“夹制远制制不尽，留余烟”整句仅见…","source_ref":{"path":"theory/raw/duan/promoted/handoff-review-2026-10-05.md","anchor":"line:13"},"score":4.0}
```

**M1-D-075**（首次由 Q07 返回，score=0.6666666666666666）

```json
{"id":"M1-D-075","school":"duan","classic_name":"段建业盲派","title":"制象原则 — 制后转象","domain":"象法体系","tags":["象法体系","xiangfa"],"statement":"字被制（合制 / 冲制 / 克制 / 穿制） prerequisites=制方与被制方力量比较已完成 conclusion: 制后该字本象消失或转为相反象（如官被制 = 没工作 / 印被制 = 没文凭 / 财被制 = 破财或得财，看制方为体或为用） falsifiable_by: 制不尽 = 留余烟，本象部分保留","source_ref":{"path":"theory/raw/duan/d02-theory.md","anchor":"line:697"},"score":0.6666666666666666}
```

**M1-D-085**（首次由 Q03 返回，score=2.0）

```json
{"id":"M1-D-085","school":"duan","classic_name":"段建业盲派","title":"杀刃格完整 5 项模板","domain":"正格12格局","tags":["正格12格局","geju"],"statement":"日主有刃 + 独杀清透 + 刃合杀 prerequisites=杀刃贴近 不见伤食过制 conclusion: 武职 / 兵权 / 实权统帅 falsifiable_by: 若杀被伤官克尽 / 刃被合化，格破","source_ref":{"path":"theory/raw/duan/d03-theory.md","anchor":"line:132"},"score":2.0}
```

### 2.4 仅在 notes 中被提及、未作为锚点入 YAML 的两条（供对照）

**M1-D-133**（Q13，score=14.0）

```json
{"id":"M1-D-133","school":"duan","classic_name":"段建业盲派","title":"夫星临长生拱局不入墓","domain":"暗合","tags":["暗合","xiangfa"],"statement":"女命 + 命局有官星 / 杀星 + 该字坐长生地或形成三合局 prerequisites=已确定夫星（按段派\"用神 = 命主追求\"标准选定） 夫星位置已识别 conclusion: 原则: 夫星临长生 + 拱局 = 不可入墓 反例展示: 宋先生主张\"丙戌年夫星入墓\"被卜文反驳 - 实情：丁火杀星非夫，时上寅中丙火正官才是夫 - 寅木为夫之原神，临长生地（寅是丙的长生） - 行壬子癸丑运不会伤克寅…","source_ref":{"path":"theory/raw/duan/d05-theory.md","anchor":"line:407"},"score":14.0}
```

**M1-D-345**（Q16，score=22.0）

```json
{"id":"M1-D-345","school":"duan","classic_name":"段建业盲派","title":"不能穿旺禄与禄穿牢狱","domain":"jiankang","tags":["穿旺禄","牢狱","车祸","官星穿禄","jiankang"],"statement":"不能穿旺禄，犯此忌者有灾（官星生寅穿禄主牢狱之灾）；类似的破禄之命有车祸应期","source_ref":{"path":"sources/duan/MinerU_markdown_体用_2056043694349017088.md","anchor":"line:251"},"score":22.0}
```

### 2.5 全部检索索引（16 条）

| tag | query | 命中数 | 命中 id |
|---|---|---|---|
| Q01 | 克者被合绊 制用 | 4 | M1-D-009, M1-D-116, M1-D-343, M1-D-173 |
| Q02 | 绊 合住 不制 | 10 | M1-D-316, M1-D-154, M1-D-405, M1-D-311, M1-D-364, M1-D-235, M1-D-021, M1-D-012, M1-D-055, M1-D-108 |
| Q03 | 合绊 不能制 被合 | 10 | M1-D-405, M1-D-364, M1-D-176, M1-D-189, M1-D-194, M1-D-021, M1-D-024, M1-D-074, M1-D-083, M1-D-085 |
| Q04 | 比劫有力 制财 财弱 | 10 | M1-D-152, M1-D-009, M1-D-012, M1-D-079, M1-D-081, M1-D-093, M1-D-170, M1-D-181, M1-D-214, M1-D-274 |
| Q05 | 无根 虚浮 不制 | 6 | M1-D-316, M1-D-183, M1-D-021, M1-D-089, M1-D-150, M1-D-235 |
| Q06 | 官杀略偏旺 用印化杀 化敌为友 | 2 | M1-D-149, M1-D-089 |
| Q07 | 力量相当 | 10 | M1-D-106, M1-D-185, M1-D-010, M1-D-022, M1-D-024, M1-D-056, M1-D-059, M1-D-061, M1-D-075, M1-D-101 |
| Q08 | 旺制 弱制 平衡制 官杀 | 10 | M1-D-311, M1-D-318, M1-D-408, M1-D-420, M1-D-006, M1-D-032, M1-D-033, M1-D-090, M1-D-091, M1-D-220 |
| Q09 | 穿中带生 不能制 | 3 | M1-D-024, M1-D-153, M1-D-178 |
| Q10 | 制净 制尽 | 2 | M1-D-023, M1-D-047 |
| Q11 | 制干净 制不尽 不尽 留余烟 | 4 | M1-D-047, M1-D-075, M1-D-189, M1-D-204 |
| Q12 | 旺透 | 0 | （空） |
| Q13 | 长生 | 5 | M1-D-133, M1-D-013, M1-D-022, M1-D-139, M1-D-237 |
| Q14 | 临长生 长生地 制 不惧 | 10 | M1-D-021, M1-D-022, M1-D-023, M1-D-024, M1-D-143, M1-D-149, M1-D-178, M1-D-299, M1-D-305, M1-D-315 |
| Q15 | 谁也制不了谁 相持 势 | 10 | M1-D-017, M1-D-018, M1-D-122, M1-D-123, M1-D-343, M1-D-352, M1-D-359, M1-D-013, M1-D-019, M1-D-020 |
| Q16 | 被制之神 旺 长生 制不住 | 10 | M1-D-345, M1-D-362, M1-D-407, M1-D-408, M1-D-409, M1-D-133, M1-D-017, M1-D-040, M1-D-098, M1-D-131 |

## 3. 五条判据 + 1 条阈值的结论

| 判据 | status | 锚点数 | 主要依据（工具 id） |
|---|---|---|---|
| 克者被合绊 | anchored | 4 | M1-D-316（戌绊卯不制）、M1-D-108（忌神被合住→作用减弱）、M1-D-364（合绊=不发挥作用）、M1-D-194（婚姻域：合绊使象锁死不应） |
| 克者无根 | anchored | 2 | M1-D-152（制方须「比劫有力」）、M1-D-183（无根虚浮=虚） |
| 力量相当 | anchored | 4 | M1-D-149（弱/略偏旺/旺三档制法）、M1-D-343（得势即能穿）、M1-D-185（力量相当=破，冲语境）、M1-D-220（弱制需特殊条件） |
| 穿中带生不能制 | anchored | 2 | M1-D-024（申亥穿、寅巳穿相生不能制）、M1-D-178（来源冲突边界） |
| 目标旺透得长生 | **not_found** | 0 | 原文无该组合判据；部分证据见 §3.1 |
| 制净 / 制尽 | **unmodeled** | 3 | M1-D-047（无稳定分级、无数值阈值）、M1-D-075（制不尽=留余烟）、M1-D-085（「克尽」是定性措辞，无刻度） |

### 3.1 唯一 not_found 的原因

「目标旺透得长生」在原文里没有单一句子，三个组成部分分散且结论各不相同：

- M1-D-149：旺的官杀要**弱制**——不是「不能制」，而是换手法（化/软制）。
- M1-D-133：夫星**临长生**+拱局 = **不可入墓**——谓词是「入墓」，不是「制」。
- M1-D-345：**不能穿旺禄**——是一条禁忌（犯此忌者有灾），不是制局的成败判据。

把这三条拼成「旺+透+得长生 → 制不住」属于自造判据，任务卡明令不许用相近段落顶替，故标 `not_found`。
若要救，须回原文语料补读婚姻专辑相关章节（本任务只许用 query_theory，无法进一步定位）。

## 4. 「制净 / 制尽」查证结论：**无阈值**

结论：**原文只有定性用词，没有量化标准 → 标 unmodeled，B1 不得自造阈值。**

依据 M1-D-047（交接文档的自查结论，工具原文）：

> 原文确有“制干净/制净/制尽/不尽”等定性用词，但未找到净与尽之间稳定的术语分级或数值阈值……
> 初级/中级讲义支持夹制/夹冲常不尽；面授讲义也有夹住制净的具体案例，故不能作绝对状态。

另有两点加重「不可量化」：

1. M1-D-047 明说同一命局的不同 occurrence 可分别判为未净/制净，双向做功也会改变「制尽」判断——
   即「净」不是盘面静态属性，不能用一次性条件求值。
2. M1-D-075 的对应表述只有「制不尽 = 留余烟，本象部分保留」，仍是定性；
   原文另有「制不尽当财」（M1-D-189、M1-D-204 的 prerequisites）这类用法，同样只有定性区分。

## 5. 未完成与风险

1. **两条判据是「合成锚点」，不是单句直述**：「克者无根」由 M1-D-152（正述必要条件）+ M1-D-183（根的判定口径）
   合起来才成立；原文没有「克者无根则不能制」这样的句子。YAML 的 notes 已写明。中枢若坚持「单句原则」，
   这两条应降级为 not_found——请中枢裁定，我没有替中枢做这个决定。
2. **「力量相当」的语义偏离**：原文用「势」（得势即能穿）与「略偏旺要平衡制」来描述强弱对比，
   并把「力量相当」一词用在六冲（力量相当=破）。用它支撑「力量相当→不能制」是**同一机制的合理延伸，但不是原句**。
   三档分级本身无量化刻度，B1 若要把「相当」求值，仍然没有原文阈值可用（同 §4 的问题）。
3. **工具返回在 200 字处截断**：`statement` 超长时以「…」结尾。凡我引用处均已切在完整句上，
   未引被截断的尾巴；M1-D-149 的第三档（「旺的官杀要弱…」）因此未取，YAML notes 已注明。
4. **场景边界**：五条判据的主要锚点取自段派「制局成败」的通论（制法、过河拆桥、干支虚实、势与党等章），
   **没有一条出现在婚姻专辑**（`sources/duan/MinerU_markdown_婚姻专辑_*.md`）。婚姻专辑里命中的是
   M1-D-291/297/298/299/304/305/309 这类「宫为主星为辅」「正星不可制」的规则，与本五条不是同一套判据。
   唯一带婚姻域、又出现「合绊」的命中是 M1-D-194（婚姻判定域），但它讲的是桃花之象被合绊锁死，
   不是「克者被绊」。这一层错位必须让 B1 知道：锚点支撑的是机制，不是「段派婚姻原文这么说」。
5. **未做的事**：没写编译、没改引擎、没动语料、没建索引、没跑 `--rebuild-index`。

## 6. 下游须知（B1 编译时）

- 可直接当硬条件用的只有 1 条：**穿中带生不能制**（M1-D-024 逐字有「相生不能制」）。但它自带来源冲突
  （M1-D-178 记录「穿不能制」与同一合集的条件性穿制说法直接冲突），编译时必须把冲突保留成
  `boundary_warnings` 或候选分支，不能挑一边写成定论。
- **克者被合绊** 是全组里机制最清楚的一条，但要注意 M1-D-108 的反例面：
  「若合而不能化，仅减弱不消除」——合绊是**削弱**，不是必然归零。别把它编译成「被合 → 制力=0」。
- **力量相当 / 克者无根** 都需要「力量比较」这个前置判断，而引擎当前没有可求值的力量刻度；
  按 §3/§5 的分析，这两条大概率只能落到 `needs_human` 或证据候选，不能直接出断语。
- **目标旺透得长生** 是 `not_found`：**不要编译**。若 B1 的模板必须六条齐全，请显式留空并标注原因，
  不要拿 M1-D-149/M1-D-133/M1-D-345 去凑。
- **制净 / 制尽** 是 `unmodeled`：任何形如「制力度 ≥ 0.8 即为制净」的阈值都是自造，违反任务卡硬要求。
  可行做法是把它留成人工裁决项，或只出「制不尽 = 留余烟，本象部分保留」这种定性旁注。
- 每条 `source_ref` 都是 query_theory 的返回值（`path` + `anchor`），没有页码；引用时照抄，不要换算成页码。

## 7. 验收（本机实跑）

```
.venv\Scripts\python.exe -m pytest -q
220 passed, 1 skipped in 12.19s          # 与基线一致，未碰代码

git status --porcelain theory/_ir sources
# （空）                                 # 未碰原文语料
```

`git status --porcelain` 全量输出（含**他人**改动）：

```
 M docs/adr/README.md
 M tasks/T-128/PROMPT.md
 M theory/claims/conditions-v2/pilot-20.yaml
?? META/case-time-basis-v1.json
?? docs/adr/ADR-006-v5-retirement-strategy.md
?? tasks/T-130/
?? tasks/T-131/
?? tasks/T-132/
?? tasks/T-133/
?? tasks/T-134/
?? theory/claims/drafts/
?? tools/case_time_basis_audit.py
```

**本任务新增的只有** `theory/claims/drafts/duan-marriage-anchors.yaml` 与 `tasks/T-133/`。
其余 `M`/`??` 在我开始前就已存在于工作区，属其他任务；`pilot-20.yaml` 的改动（M1-D-242 compile_note 复算）
经 `git diff` 确认与 T-133 无关，我未编辑它。

