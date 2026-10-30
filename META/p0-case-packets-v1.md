# P0 案例包 v1（T-197）· 4 例 · A / B1 / B2 / C

- 生成：`2026-10-30T08:26:26+08:00`；任务：`T-197`；JSON：`META/p0-cards-v1.json`
- 用途：给中枢/人类看的**证据包**。每例一页：盘面事实 → 原文锚点 → 方向候选 → 状态/救应候选 → 锚点题 → 引擎校验 → 缺口。
- **本包不做选定**：`selected_option=null`、`anchor_a=[]`、`pending=anchor_q`。人只答**已发生事实**的是非题，不替 Agent 选方向。

## 0. 一句话

4 例真实盘（婚/事业/健康/财各 1），每例 3 个方向候选、1–2 个锚点事实题；全部候选过 engine 地址/边/十神/引文校验（含 20 个植入错误 fixture 全部被拦）。方向候选 12 条：A 3（固定克/生/化/墓）、B1 8、C 1；B2 触发 0，6 个待答单元（6 个事实题）全部留空。

## 1. 读取边界（自证）

- 读答案：**否**；读 restricted：**否**；git 写：无；engine/保护区：未改；评分器：未跑。
- 盲卷只取四柱查重：`F20` 20、`PF` 40、`A60` 60、`P1-H` 20、`OLD3` 3，归一化后 133 个四柱集合，与本包 4 盘重叠 **0**。
- 理论引文不经过检索器摘要，直接回 `sources/` 原文逐字核对（每条 quote 带 `path:Ln`，构建时做子串校验）。

## 2. 档位口径（中枢 2026-10-30 追加后）

| 档 | 含义 | 本包处置 |
|---|---|---|
| **A** | 只许固定**克/生/化/墓**；engine 固定规则与原文同向、无竞争候选 | `agent_auto`，无需人 |
| **B1** | 锚点消歧（默认）：候选分歧可由「命主已发生事实」的是非题区分 | 只问事实，不问「你选哪个」 |
| **B2** | 没有任何可观测事实可区分时：专家单选 / 转 needs_anchor，必须带 source+quote | 本包 0 项（见 §3 说明） |
| **C** | 无源（原文未给该方向）或与已冻结规则冲突 | `needs_anchor`，不写断语 |

> 冲/合/穿/刑/破**一律不得 A**；「原文没写冲突」也不自动升 A。

## 3. 统计

| 指标 | 值 |
|---|---|
| 例数 / 覆盖域 | 4 / 事业、健康、婚、财 |
| 方向候选 | 12（A 3 · B1 8 · B2 0 · C 1） |
| A 档占比 | 25.00%（P0 gate ≥50% → **未达**） |
| 锚点题（B1） | 6 题 |
| B2 专家单选 | 0 项（未触发）；B2 / 全部 B 单元 = 0.00% |
| 状态候选 / 救应候选 | 10 / 4 |
| 引擎校验失败 | 0（候选作废 0） |
| 原文/宫位引文逐字校验 | 24/24 通过 |
| 植入错误（逐卡 4 类） | 16/16 全部拦截 |
| 植入错误 self_test（20 fixture） | 20/20 → pass |

**A 档未达 gate 的原因（留给中枢判）**：本题 4 例的 material edge 是夫妻宫冲/合、财印克、丑午穿/戌刑、官入辰墓+印克伤官。冲/合/穿不得 A（中枢追加），固定类只剩 3 条（C4 的墓/克/生）；C2 的财制印虽为克，但有年干戊/时干己两组财争同一印，需锚点消歧。

---

# P0-01 · 婚 · 辛巳 庚寅 甲申 庚午（乾）

| 项 | 值 |
|---|---|
| 卡档位 | **B1** / `decision_by=anchor_fact` / `direction_tier=B1` / `pending=anchor_q` |
| tier_reason | ['direction:anchor_conflict', 'state:not_claimed', 'rescue:candidate_only'] |
| chart_id / 日主 | `cf-daef938eab28eb49e1b8` / 甲 |
| 快照 | dayun_index=null，liunian_year=null（原局；四柱输入不起运） |
| 问题 | 我婚姻一直不顺，离过几次，现在一个人过；想知道这段命里的婚姻还能不能稳定下来。 |
| 问题域 | marriage |
| 原文出处 | `sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md` L21-L33（案例）；L15-L17、L44-L50（同章判据） |
| 后续事实（备查，不作预测） | 原文后续事实：五次婚姻、配偶带子女离开、无子女留在身边（P0 仅备查，不作预测依据）。 |

## 0.5) 宫位映射与 material edge

| addr | 角色 | 十神 | 映射 | 依据引文 |
|---|---|---|---|---|
| `D.b` | 夫妻宫（配偶宫） | 七杀 | M-01 | `sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:L15`「看婚姻的好坏，应以配偶宫为主，配偶星为辅。」 |
| `Y.b` | 配偶星（男命财星）藏戊偏财 | 食神 | M-02 | `sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:L17`「配偶宫为日主的坐支，配偶星则男命以财星为妻，女命以官杀星当夫，如无则另看：男命再无遁藏，基本可能确定无婚，或克配偶。」 |
| `H.b` | 配偶星（男命财星）藏己正财 | 伤官 | M-02 | `sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:L17`「配偶宫为日主的坐支，配偶星则男命以财星为妻，女命以官杀星当夫，如无则另看：男命再无遁藏，基本可能确定无婚，或克配偶。」 |

- material edge（问题命中的边）：
  - `e015`：夫妻宫(M.b寅↔D.b申)相冲——问题直接问婚姻稳定
  - `e011`：年支巳与夫妻宫申六合——配偶星来源侧，与冲争主线

## 1) engine 事实（`engine.cli all/relations`）

| 柱 | 干支 | 干(addr/十神) | 支(addr/十神) | 藏干 |
|---|---|---|---|---|
| year | 辛巳 | 辛 `Y.s` 正官 | 巳 `Y.b` 食神 | 丙本气(食神)、庚中气(七杀)、戊余气(偏财) |
| month | 庚寅 | 庚 `M.s` 七杀 | 寅 `M.b` 比肩 | 甲本气(比肩)、丙中气(食神)、戊余气(偏财) |
| day | 甲申 | 甲 `D.s` 日主 | 申 `D.b` 七杀 | 庚本气(七杀)、壬中气(偏印)、戊余气(偏财) |
| hour | 庚午 | 庚 `H.s` 七杀 | 午 `H.b` 伤官 | 丁本气(伤官)、己中气(正财) |

- 旬空：日旬 ['午', '未']；年旬 ['申', '酉']；命中 [['D.b', 'year'], ['H.b', 'day']]
- 体用（duan_zuogong.tiyong）：{'Y.s': '用', 'Y.b': '双属', 'M.s': '用', 'M.b': '体', 'D.s': '体', 'D.b': '用', 'H.s': '用', 'H.b': '双属'}
- 墓库（relations.muku）：（无）

### 关系边（原样引用 edge_id）

| edge_id | kind | members | chars | 距离 | 组/完整度 |
|---|---|---|---|---|---|
| e001 | same_qi | ['Y.s', 'M.s'] | ['辛', '庚'] | 1 | / |
| e002 | ke | ['Y.s', 'D.s'] | ['辛', '甲'] | 2 | / |
| e003 | same_qi | ['Y.s', 'H.s'] | ['辛', '庚'] | 3 | / |
| e004 | stem_chong | ['M.s', 'D.s'] | ['庚', '甲'] | 1 | / |
| e005 | ke | ['M.s', 'D.s'] | ['庚', '甲'] | 1 | / |
| e006 | same_qi | ['M.s', 'H.s'] | ['庚', '庚'] | 2 | / |
| e007 | stem_chong | ['D.s', 'H.s'] | ['甲', '庚'] | 1 | / |
| e008 | ke | ['H.s', 'D.s'] | ['庚', '甲'] | 1 | / |
| e009 | chuan | ['Y.b', 'M.b'] | ['巳', '寅'] | 1 | / |
| e010 | xing | ['Y.b', 'M.b'] | ['巳', '寅'] | 1 | 寅巳申/partial |
| e011 | liuhe | ['Y.b', 'D.b'] | ['巳', '申'] | 2 | / |
| e012 | po | ['Y.b', 'D.b'] | ['巳', '申'] | 2 | / |
| e013 | xing | ['Y.b', 'D.b'] | ['巳', '申'] | 2 | 寅巳申/partial |
| e014 | sanhui | ['Y.b', 'H.b'] | ['巳', '午'] | 3 | 巳午未/partial |
| e015 | chong | ['M.b', 'D.b'] | ['寅', '申'] | 1 | / |
| e016 | xing | ['M.b', 'D.b'] | ['寅', '申'] | 1 | 寅巳申/partial |
| e017 | sanhe | ['M.b', 'H.b'] | ['寅', '午'] | 2 | 寅午戌/half_sheng |
| e018 | xing | ['M.b', 'Y.b', 'D.b'] | ['寅', '巳', '申'] | 2 | 寅巳申/full |
| e019 | ganzhi_zihe | ['Y.s', 'Y.b'] | ['辛', '巳'] | 0 | / |

- 段派做功候选（`duan_zuogong.candidates`，共 29 条；下表只列本卡引用到的）：

| mode | members | actor | edge_id |
|---|---|---|---|
| 合用 | ['Y.b', 'D.b'] | None | e011 |
| 制用 | ['M.b', 'D.b'] | None | e015 |

## 2) 原文锚点

- 命例四柱：`sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:L21`「辛   庚    甲    庚」
- 命例四柱：`sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:L23`「巳   寅    申    午」
- 后续事实：`sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:L25`「这个例子记载他有五次婚姻，老婆带子女全跑了，最后还是孤家寡人。」

## 3) 方向候选（2–3 条，均不自动选定）

| id | 档 | 类/kind | 方向 | 边 | decisive | conflict_with | 校验 |
|---|---|---|---|---|---|---|---|
| dc1 | B1 | 冲/chong | actor→target M.b→D.b | `e015` | False | ['dc2', 'dc3'] | valid |
| dc2 | B1 | 冲/chong | mutual（对称，不赋向）  | `e015` | False | ['dc1', 'dc3'] | valid |
| dc3 | B1 | 合/liuhe | needs_anchor（方向未定）  | `e011` | False | ['dc1', 'dc2'] | valid |

### dc1（B1 / `human_anchor`）

- 方向：actor→target，`M.b`(寅) → `D.b`(申)，evidence_gap=same_page（同段/邻行，未同句）
- 依据：『夫宫被冲克』是被动句：受方=夫妻宫申；紧接一句『寅申之冲，寅多作用一次』把反复作用的一方指向月支寅（比肩＝月柱父母兄弟宫）。engine 边 e015 为 chong(M.b,D.b)、actor=null，方向由本候选补出。
- 规则：`docs/specs/actor-rules-v1.md:L86-L93`
- 引文（direction_support）：`sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:L29`「为何偏偏要离婚，而不是二奶三奶呢？因夫宫被冲克，处于不稳定状态。」
- 引文（actor_support）：`sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:L31`「巳、寅、午，三个老婆，巳申合，巳用了两次，多数一个，而寅申之冲，寅多作用一次，所以总算五个。」
- 校验：address=pass · edge=pass · ten_god=pass · quote=pass（边存在且 kind/members 一致；动态边 actor 由 engine 保持 null）

### dc2（B1 / `human_anchor`）

- 方向：mutual（对称，不赋向），evidence_gap=same_line（同句）
- 依据：冲为对称关系，actor=null；『寅申之冲』是并列句，『寅多作用一次』是次数统计（计老婆个数），不是及物施受句法，不得据以单向赋向。
- 规则：`docs/specs/actor-rules-v1.md:L34-L42,L86-L93`
- 引文（direction_support）：`sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:L31`「巳、寅、午，三个老婆，巳申合，巳用了两次，多数一个，而寅申之冲，寅多作用一次，所以总算五个。」
- 校验：address=pass · edge=pass · ten_god=pass · quote=pass（边存在且 kind/members 一致；动态边 actor 由 engine 保持 null）

### dc3（B1 / `human_anchor`）

- 方向：needs_anchor（方向未定），evidence_gap=same_line（同句）
- 依据：同一夫妻宫另有『巳申合』（engine e011 liuhe 巳申）与『巳申破』（e012）。合不赋向；若婚姻主线是年支合夫妻宫而非冲，则施力方不可判（方向留空）。
- 规则：`docs/specs/actor-rules-v1.md:L72-L84`
- 引文（relation_support）：`sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:L31`「巳、寅、午，三个老婆，巳申合，巳用了两次，多数一个，而寅申之冲，寅多作用一次，所以总算五个。」
- 校验：address=pass · edge=pass · ten_god=pass · quote=pass（边存在且 kind/members 一致；动态边 actor 由 engine 保持 null）

## 4) 状态候选 / 救应候选

| id | 层 | 档 | 结果 | 主张 | anchored_by |
|---|---|---|---|---|---|
| st1 | state | B1 | 败 | 夫宫被冲克 → 婚姻不稳、多婚 | ['AQ1'] |
| st2 | state | B1 | 多现 | 副宫多现 → 有婚姻关系的女性多（配偶星伏于副宫之下） | ['AQ1'] |
| st3 | state | C | needs_anchor | 『夫妻宫为所忌之神，被夫星制之吉者婚姻较好』——本造不满足（反条件） | [] |
| rs1 | rescue | C | needs_anchor | 夫妻宫安静条件：不能被刑坏、冲破、穿倒，或六合/暗合他星 | — |

- **st1**（B1，败）：原文把多婚直接归因于『夫宫被冲克』；且『寅申之冲，寅多作用一次』给出次数层面的解释。
  - 引文：`sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:L29`「为何偏偏要离婚，而不是二奶三奶呢？因夫宫被冲克，处于不稳定状态。」
  - 引文：`sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:L25`「这个例子记载他有五次婚姻，老婆带子女全跑了，最后还是孤家寡人。」
- **st2**（B1，多现）：『申是妻宫，透出庚辛副宫，而副宫下边压着是伤食及财星』——配偶星不在夫妻宫本身而在副宫之下，故主关系多。
  - 引文：`sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:L27`「申是妻宫，透出庚辛副宫，而副宫下边压着是伤食及财星，都是配偶星，表示跟他有婚姻关系的女人多。」
- **st3**（C，needs_anchor）：该句给出的是好婚姻条件；本造夫宫七杀为忌且被冲，条件不成立。是否另有救应，原文未给。
  - 引文：`sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:L50`「原局夫妻宫为所忌之神，被夫星制之吉者婚姻较好。」
- **rs1**（C，needs_anchor）：该句是『好婚姻的组合』条件式，本造夫妻宫同时被 e015 冲、e011 六合、e012 破，无一满足；原文未给任何救应事实。
  - 引文：`sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:L48`「夫妻宫位要安静，如有用，不能被刑坏，冲破，穿倒，或六合，暗合他星（配偶星以外的星），也不宜杂透，多现。」

## 5) 锚点题（只问已发生事实）

### AQ1 · direction · discriminates=['dc1', 'dc2']

> 你的婚姻破裂过程中，是否出现过『你的父母、兄弟或原生家庭出面介入、施压或替你做主』的具体事实？

- 能区分的原因：dc1 把施力方定在月支寅＝父母兄弟宫（家人在前推）；dc2 说两侧同损、没有单一推手。若确有原生家庭反复介入，则单侧施力读法成立；若没有，则对称读法保留。
- 规则：`sources/duan/MinerU_markdown_16.《盲派批命案例集》（263例，74页）段建业_2056045601255776256.md:L39`；`source_mentions_answer=False`；proxy=medium
- 答「是」：keep ['dc1']；eliminate ['dc2']
- 答「否」：keep ['dc2']；eliminate ['dc1']
- 答不出：`needs_anchor`，影响 ['dc1', 'dc2']
- **答案（留空，待人类/命主）**：`anchor_a: []`

### AQ2 · direction · discriminates=['dc1', 'dc3']

> 你与已经分开的配偶，是否至今仍有联系或经济往来（即分开后并没有彻底断干净）？

- 能区分的原因：dc3 认为主线是年支巳与夫妻宫申『合』（合而未断）；dc1 认为是冲（推走、断离）。若分开后仍长期有联系/往来，合读法保留；若彻底断绝，冲读法保留。
- 规则：`docs/specs/actor-rules-v1.md:L72-L84`；`source_mentions_answer=False`；proxy=medium
- 答「是」：keep ['dc3']；eliminate ['dc1', 'dc2']
- 答「否」：keep ['dc1', 'dc2']；eliminate ['dc3']
- 答不出：`needs_anchor`，影响 ['dc1', 'dc2', 'dc3']
- **答案（留空，待人类/命主）**：`anchor_a: []`

## 6) 引擎校验

| 校验 | 通过/总数 |
|---|---|
| address | 7/7 |
| edge | 3/3 |
| ten_god | 7/7 |
| quote | 7/7 |
| 原文/宫位引文 | 6/6 |

植入错误自检：4/4 拦截（`pass`）

- fake_address:Q.b → 拦截（engine 未输出该地址）
- fake_edge:e999 → 拦截（engine relations 无此 edge_id）
- wrong_ten_god:D.b=正印 → 拦截（十神不符）
- tampered_quote:HY:L15 → 拦截（该行未找到逐字文本）

## 7) 缺口与非断言

- gaps：G2, G3, G4, G5, no_spouse_star_on_stem, muku_open_close, suiyun_ten_god
- 非断言：不判冲/合的方向，不判吉凶、成败、离婚与否、应期
- 非断言：不把固定边（如 e002 ke）写成结论
- 非断言：不据原文『五次婚姻』反推本盘断语（仅作后续事实备查）
- 非断言：不判救应、不判岁运引动、不判党势

---

# P0-02 · 事业 · 戊戌 癸亥 乙巳 己卯（乾）

| 项 | 值 |
|---|---|
| 卡档位 | **B1** / `decision_by=anchor_fact` / `direction_tier=B1` / `pending=anchor_q` |
| tier_reason | ['direction:anchor_conflict', 'state:not_claimed', 'rescue:candidate_only'] |
| chart_id / 日主 | `cf-1627557db9bf35baf387` / 乙 |
| 快照 | dayun_index=null，liunian_year=null（原局；四柱输入不起运） |
| 问题 | 我在部队/单位里干了多年，想知道还能不能往上走、能走到哪一步。 |
| 问题域 | career |
| 原文出处 | `sources/duan/MinerU_markdown_如何看军官_2056043755153842176.md` L17-L27（案例）；L1-L3（军官判据） |
| 后续事实（备查，不作预测） | 原文后续事实：正师级干部、07 年转戊辰运提副军长（P0 仅备查，不作预测依据）。 |

## 0.5) 宫位映射与 material edge

| addr | 角色 | 十神 | 映射 | 依据引文 |
|---|---|---|---|---|
| `M.s` | 印星（偏印）＝权/印 | 偏印 | M-03 | `sources/duan/MinerU_markdown_16.《盲派批命案例集》（263例，74页）段建业_2056045601255776256.md:L39`「月——一父母、兄弟」 |
| `Y.s` | 财星（正财）＝制印之力 | 正财 | M-04 | `sources/duan/MinerU_markdown_如何看军官_2056043755153842176.md:L27`「解析：八字是财制印得权的官命」 |
| `M.b` | 月支（父母兄弟宫） | 正印 | M-03 | `sources/duan/MinerU_markdown_16.《盲派批命案例集》（263例，74页）段建业_2056045601255776256.md:L39`「月——一父母、兄弟」 |

- material edge（问题命中的边）：
  - `e002`：财制印(戊克癸)：原文判官命的核心机制
  - `e006`：第二组财制印(己克癸)：同一受印癸的竞争候选

## 1) engine 事实（`engine.cli all/relations`）

| 柱 | 干支 | 干(addr/十神) | 支(addr/十神) | 藏干 |
|---|---|---|---|---|
| year | 戊戌 | 戊 `Y.s` 正财 | 戌 `Y.b` 正财 | 戊本气(正财)、辛中气(七杀)、丁余气(食神) |
| month | 癸亥 | 癸 `M.s` 偏印 | 亥 `M.b` 正印 | 壬本气(正印)、甲中气(劫财) |
| day | 乙巳 | 乙 `D.s` 日主 | 巳 `D.b` 伤官 | 丙本气(伤官)、庚中气(正官)、戊余气(正财) |
| hour | 己卯 | 己 `H.s` 偏财 | 卯 `H.b` 比肩 | 乙本气(比肩) |

- 旬空：日旬 ['寅', '卯']；年旬 ['辰', '巳']；命中 [['D.b', 'year'], ['H.b', 'day']]
- 体用（duan_zuogong.tiyong）：{'Y.s': '用', 'Y.b': '用', 'M.s': '体', 'M.b': '体', 'D.s': '体', 'D.b': '双属', 'H.s': '用', 'H.b': '体'}
- 墓库（relations.muku）：[{'addr': 'Y.b', 'branch': '戌', 'ku_of': ['火', '土'], 'openers': [], 'chuan_po': [], 'binders': ['e008'], 'candidates': [{'addr': 'D.b', 'char': '巳', 'effect': '入墓', 'excluded': False, 'requires_judgment': []}, {'addr': 'Y.s', 'char': '戊', 'effect': '不论入墓', 'excluded': True, 'requires_judgment': []}]}]

### 关系边（原样引用 edge_id）

| edge_id | kind | members | chars | 距离 | 组/完整度 |
|---|---|---|---|---|---|
| e001 | wuhe | ['Y.s', 'M.s'] | ['戊', '癸'] | 1 | / |
| e002 | ke | ['Y.s', 'M.s'] | ['戊', '癸'] | 1 | / |
| e003 | ke | ['D.s', 'Y.s'] | ['乙', '戊'] | 2 | / |
| e004 | same_qi | ['Y.s', 'H.s'] | ['戊', '己'] | 3 | / |
| e005 | sheng | ['M.s', 'D.s'] | ['癸', '乙'] | 1 | / |
| e006 | ke | ['H.s', 'M.s'] | ['己', '癸'] | 2 | / |
| e007 | ke | ['D.s', 'H.s'] | ['乙', '己'] | 1 | / |
| e008 | liuhe | ['Y.b', 'H.b'] | ['戌', '卯'] | 3 | / |
| e009 | chong | ['M.b', 'D.b'] | ['亥', '巳'] | 1 | / |
| e010 | sanhe | ['M.b', 'H.b'] | ['亥', '卯'] | 2 | 亥卯未/half_sheng |

- 段派做功候选（`duan_zuogong.candidates`，共 31 条；下表只列本卡引用到的）：

| mode | members | actor | edge_id |
|---|---|---|---|
| 制用 | ['Y.s', 'M.s'] | Y.s | e002 |
| 制用 | ['H.s', 'M.s'] | H.s | e006 |
| 制用 | ['M.b', 'D.b'] | None | e009 |

## 2) 原文锚点

- 命例四柱：`sources/duan/MinerU_markdown_如何看军官_2056043755153842176.md:L17`「戊 癸 乙 己」
- 命例四柱：`sources/duan/MinerU_markdown_如何看军官_2056043755153842176.md:L19`「戌 亥 巳 卯」
- 后续事实：`sources/duan/MinerU_markdown_如何看军官_2056043755153842176.md:L25`「此人婚姻非常好，一生2个孩子，一儿一女。」

## 3) 方向候选（2–3 条，均不自动选定）

| id | 档 | 类/kind | 方向 | 边 | decisive | conflict_with | 校验 |
|---|---|---|---|---|---|---|---|
| dc1 | B1 | 克/ke | actor→target Y.s→M.s | `e002` | True | ['dc2'] | valid |
| dc2 | B1 | 克/ke | actor→target H.s→M.s | `e006` | False | ['dc1'] | valid |
| dc3 | C | 冲/chong | needs_anchor（方向未定）  | `e009` | False | [] | valid |

### dc1（B1 / `human_anchor`）

- 方向：actor→target，`Y.s`(戊) → `M.s`(癸)，evidence_gap=same_line（同句）
- 依据：engine 固定规则：e002 ke(戊,癸)、actor=Y.s。原文把戊点为『做工的重要的字』并说『见到戊…或印被制』——即戊(正财)制癸(偏印)。
- 规则：`docs/specs/actor-rules-v1.md:L120-L127`
- 引文（direction_support）：`sources/duan/MinerU_markdown_如何看军官_2056043755153842176.md:L27`「解析：八字是财制印得权的官命」
- 引文（actor_support）：`sources/duan/MinerU_markdown_如何看军官_2056043755153842176.md:L27`「戊就是做工的重要的字，见到戊他出现或印被制，或印库出现，官杀被制之年都是提升的应期。」
- 校验：address=pass · edge=pass · ten_god=pass · quote=pass（边存在且 kind/members 一致；动态边 actor 由 engine 保持 null）

### dc2（B1 / `human_anchor`）

- 方向：actor→target，`H.s`(己) → `M.s`(癸)，evidence_gap=doctrine_only（只有定义/通用句）
- 依据：同盘第二组财克印：e006 ke(己,癸)、actor=H.s。原文只说『财制印』未点名哪一个财；时干己(偏财)同样满足该机制，与 dc1 争同一个受印癸。
- 规则：`docs/specs/actor-rules-v1.md:L120-L127`
- 引文（direction_support）：`sources/duan/MinerU_markdown_如何看军官_2056043755153842176.md:L27`「解析：八字是财制印得权的官命」
- 校验：address=pass · edge=pass · ten_god=pass · quote=pass（边存在且 kind/members 一致；动态边 actor 由 engine 保持 null）

### dc3（C / `needs_anchor`）

- 方向：needs_anchor（方向未定），evidence_gap=gap（无定向线索）
- 依据：原局亥(正印)与巳(伤官)相冲（e009），但原文对升迁只给岁运叙述（如『壬申92年是印化官杀生身』），未给本造原局亥巳冲的施动方；同书他造『寅申冲了印换了地方』属于另一造，不能移植。
- 规则：`docs/specs/actor-rules-v1.md:L86-L93`
- 引文（absence_evidence）：`sources/duan/MinerU_markdown_如何看军官_2056043755153842176.md:L27`「壬申92年是印化官杀生身」
- 校验：address=pass · edge=pass · ten_god=pass · quote=pass（边存在且 kind/members 一致；动态边 actor 由 engine 保持 null）

## 4) 状态候选 / 救应候选

| id | 层 | 档 | 结果 | 主张 | anchored_by |
|---|---|---|---|---|---|
| st1 | state | B1 | 成 | 财制印得权 → 官命 | ['AQ1'] |
| st2 | state | B1 | 疑 | 无伤官制官杀、无比劫羊刃做工 → 仅凭『戌为火药库』补象法才成军官 | ['AQ1'] |
| rs1 | rescue | C | needs_anchor | 引擎 structures 救应要件命中：rsc_cai_zhi_xiao / rsc_yin_or_cai（met） | — |

- **st1**（B1，成）：原文直断『八字是财制印得权的官命』，并以戊为工神；engine 亦有 e002 ke(戊,癸)。
  - 引文：`sources/duan/MinerU_markdown_如何看军官_2056043755153842176.md:L27`「解析：八字是财制印得权的官命」
- **st2**（B1，疑）：原文自陈『很难理解是部队的军官，因为八字无伤官制官杀，也无比劫羊刃做工』，改由戌土火库（火药、枪炮）取象成立。此路与 st1 的财制印并不同源。
  - 引文：`sources/duan/MinerU_markdown_如何看军官_2056043755153842176.md:L27`「但很难理解是部队的军官，因为八字无伤官制官杀，也无比劫羊刃做工，但是八字见了戌土火库，又是伤官库做工了」
  - 引文：`sources/duan/MinerU_markdown_如何看军官_2056043755153842176.md:L27`「戌本来就是火药、枪炮、炮弹的意思，所以能带火药的字做工了，肯定是军队部队的官了。」
- **rs1**（C，needs_anchor）：engine.structures 只报『救应要件命中』（ziping_shishen.rsc_cai_zhi_xiao、ziping_shangguan.rsc_yin_or_cai），按规格 §4.2 G5 救应未判，不构成救应结论；原文无对应救应句。

## 5) 锚点题（只问已发生事实）

### AQ1 · direction · discriminates=['dc1', 'dc2']

> 你过去十年里，收入的主要来源是否以『体制外的项目、投资或兼职』为主，而不是固定级别的工资？

- 能区分的原因：dc1 的施力财是年干戊(正财)、dc2 是时干己(偏财)。『正财↔固定收入、偏财↔外部项目』是十神通则，本包未找到逐字原文，因此只作区分假设，不写成断语；题目问的是收入结构这一已发生事实，据此决定哪一个财在命主身上是活的。
- 规则：`sources/duan/MinerU_markdown_如何看军官_2056043755153842176.md:L27，docs/specs/fact-evidence-pack-v1.md:L60-L62`；`source_mentions_answer=False`；proxy=medium
- 答「是」：keep ['dc2']；eliminate ['dc1']
- 答「否」：keep ['dc1']；eliminate ['dc2']
- 答不出：`needs_anchor`，影响 ['dc1', 'dc2']
- **答案（留空，待人类/命主）**：`anchor_a: []`

## 6) 引擎校验

| 校验 | 通过/总数 |
|---|---|
| address | 6/6 |
| edge | 3/3 |
| ten_god | 6/6 |
| quote | 6/6 |
| 原文/宫位引文 | 6/6 |

植入错误自检：4/4 拦截（`pass`）

- fake_address:Q.b → 拦截（engine 未输出该地址）
- fake_edge:e999 → 拦截（engine relations 无此 edge_id）
- wrong_ten_god:D.b=正印 → 拦截（十神不符）
- tampered_quote:HY:L15 → 拦截（该行未找到逐字文本）

## 7) 缺口与非断言

- gaps：G2, G3, G4, G5, muku_open_close, suiyun_ten_god, binzhu_direction
- 非断言：不判官职高低、升迁年份、吉凶
- 非断言：不把『财制印』写成必然结论；engine 候选不等于做功成功
- 非断言：不判救应（G5）；不判岁运引动

---

# P0-03 · 健康 · 壬寅 庚戌 己丑 庚午（坤）

| 项 | 值 |
|---|---|
| 卡档位 | **B1** / `decision_by=anchor_fact` / `direction_tier=B1` / `pending=anchor_q` |
| tier_reason | ['direction:anchor_conflict', 'state:conflict', 'rescue:candidate_only'] |
| chart_id / 日主 | `cf-0075a9941ae6f079f4b9` / 己 |
| 快照 | dayun_index=null，liunian_year=null（原局；四柱输入不起运） |
| 问题 | 我这些年身体一直出问题，最担心妇科和大病，想知道根子在哪。 |
| 问题域 | health |
| 原文出处 | `sources/duan/MinerU_markdown_疾病_2056043976378220544.md` L135-L141（案例）；L9、L17、L27、L123（同章象法与病性） |
| 后续事实（备查，不作预测） | 原文后续事实：子宫癌、午运手术，后经中医治疗未转移（P0 仅备查，不作预测依据）。 |

## 0.5) 宫位映射与 material edge

| addr | 角色 | 十神 | 映射 | 依据引文 |
|---|---|---|---|---|
| `D.b` | 日支（夫妻宫/自身坐支）丑：阴土、伤食之墓 | 比肩 | M-01 | `sources/duan/MinerU_markdown_16.《盲派批命案例集》（263例，74页）段建业_2056045601255776256.md:L41`「日——一自己、配偶」 |
| `H.b` | 时支午：己土之禄、女体 | 偏印 | M-05 | `sources/duan/MinerU_markdown_疾病_2056043976378220544.md:L139`「丑午穿，伤了时上禄，午代表女人的身体，丑是伤食的墓，又是阴的象，表示妇科方面的疾病了。实际得了子宫癌，午运丑午穿的应期，得病手术。」 |
| `M.b` | 月支戌：火土库、劫财 | 劫财 | M-03 | `sources/duan/MinerU_markdown_16.《盲派批命案例集》（263例，74页）段建业_2056045601255776256.md:L39`「月——一父母、兄弟」 |

- material edge（问题命中的边）：
  - `e012`：丑午穿：原文指定的病源
  - `e010`：丑戌刑：原文用作救应(戌坏丑)

## 1) engine 事实（`engine.cli all/relations`）

| 柱 | 干支 | 干(addr/十神) | 支(addr/十神) | 藏干 |
|---|---|---|---|---|
| year | 壬寅 | 壬 `Y.s` 正财 | 寅 `Y.b` 正官 | 甲本气(正官)、丙中气(正印)、戊余气(劫财) |
| month | 庚戌 | 庚 `M.s` 伤官 | 戌 `M.b` 劫财 | 戊本气(劫财)、辛中气(食神)、丁余气(偏印) |
| day | 己丑 | 己 `D.s` 日主 | 丑 `D.b` 比肩 | 己本气(比肩)、癸中气(偏财)、辛余气(食神) |
| hour | 庚午 | 庚 `H.s` 伤官 | 午 `H.b` 偏印 | 丁本气(偏印)、己中气(比肩) |

- 旬空：日旬 ['午', '未']；年旬 ['辰', '巳']；命中 [['H.b', 'day']]
- 体用（duan_zuogong.tiyong）：{'Y.s': '用', 'Y.b': '用', 'M.s': '双属', 'M.b': '体', 'D.s': '体', 'D.b': '体', 'H.s': '双属', 'H.b': '体'}
- 墓库（relations.muku）：[{'addr': 'M.b', 'branch': '戌', 'ku_of': ['火', '土'], 'openers': ['e010'], 'chuan_po': [], 'binders': ['e013'], 'candidates': [{'addr': 'H.b', 'char': '午', 'effect': '一般作拱局', 'excluded': False, 'requires_judgment': ['四正支见墓一般作拱局，极弱（被制受伤）才入墓，需判断（:63、:71）']}]}, {'addr': 'D.b', 'branch': '丑', 'ku_of': ['金'], 'openers': ['e010'], 'chuan_po': ['e012'], 'binders': ['e008'], 'candidates': [{'addr': 'M.s', 'char': '庚', 'effect': '入墓', 'excluded': False, 'requires_judgment': []}, {'addr': 'H.s', 'char': '庚', 'effect': '入墓', 'excluded': False, 'requires_judgment': []}]}]

### 关系边（原样引用 edge_id）

| edge_id | kind | members | chars | 距离 | 组/完整度 |
|---|---|---|---|---|---|
| e001 | sheng | ['M.s', 'Y.s'] | ['庚', '壬'] | 1 | / |
| e002 | ke | ['D.s', 'Y.s'] | ['己', '壬'] | 2 | / |
| e003 | sheng | ['H.s', 'Y.s'] | ['庚', '壬'] | 3 | / |
| e004 | sheng | ['D.s', 'M.s'] | ['己', '庚'] | 1 | / |
| e005 | same_qi | ['M.s', 'H.s'] | ['庚', '庚'] | 2 | / |
| e006 | sheng | ['D.s', 'H.s'] | ['己', '庚'] | 1 | / |
| e007 | sanhe | ['Y.b', 'M.b'] | ['寅', '戌'] | 1 | 寅午戌/gong |
| e008 | zhi_anhe | ['Y.b', 'D.b'] | ['寅', '丑'] | 2 | / |
| e009 | sanhe | ['Y.b', 'H.b'] | ['寅', '午'] | 3 | 寅午戌/half_sheng |
| e010 | xing | ['M.b', 'D.b'] | ['戌', '丑'] | 1 | 丑戌未/partial |
| e011 | sanhe | ['M.b', 'H.b'] | ['戌', '午'] | 2 | 寅午戌/half_mu |
| e012 | chuan | ['D.b', 'H.b'] | ['丑', '午'] | 1 | / |
| e013 | sanhe | ['Y.b', 'H.b', 'M.b'] | ['寅', '午', '戌'] | 3 | 寅午戌/full |

- 段派做功候选（`duan_zuogong.candidates`，共 38 条；下表只列本卡引用到的）：

| mode | members | actor | edge_id |
|---|---|---|---|
| 制用 | ['M.b', 'D.b'] | None | e010 |
| 制用 | ['D.b', 'H.b'] | None | e012 |

## 2) 原文锚点

- 命例四柱：`sources/duan/MinerU_markdown_疾病_2056043976378220544.md:L135`「壬  庚   己   庚」
- 命例四柱：`sources/duan/MinerU_markdown_疾病_2056043976378220544.md:L137`「寅  戌   丑   午」
- 后续事实：`sources/duan/MinerU_markdown_疾病_2056043976378220544.md:L139`「丑午穿，伤了时上禄，午代表女人的身体，丑是伤食的墓，又是阴的象，表示妇科方面的疾病了。实际得了子宫癌，午运丑午穿的应期，得病手术。」

## 3) 方向候选（2–3 条，均不自动选定）

| id | 档 | 类/kind | 方向 | 边 | decisive | conflict_with | 校验 |
|---|---|---|---|---|---|---|---|
| dc1 | B1 | 穿/chuan | actor→target D.b→H.b | `e012` | False | ['dc2'] | valid |
| dc2 | B1 | 穿/chuan | mutual（对称，不赋向）  | `e012` | False | ['dc1'] | valid |
| dc3 | B1 | 刑/xing | actor→target M.b→D.b | `e010` | True | ['dc1', 'dc2'] | valid |

### dc1（B1 / `human_anchor`）

- 方向：actor→target，`D.b`(丑) → `H.b`(午)，evidence_gap=same_page（同段/邻行，未同句）
- 依据：『丑午穿，伤了时上禄』先把受方定在时支午（己土之禄、女体），穿的另一端丑（日支/夫妻宫）即施力方。engine e012 chuan actor=null，方向由本候选补出。
- 规则：`docs/specs/actor-rules-v1.md:L104-L110`
- 引文（direction_support）：`sources/duan/MinerU_markdown_疾病_2056043976378220544.md:L139`「丑午穿，伤了时上禄，午代表女人的身体，丑是伤食的墓，又是阴的象，表示妇科方面的疾病了。实际得了子宫癌，午运丑午穿的应期，得病手术。」
- 引文（method_support）：`sources/duan/MinerU_markdown_疾病_2056043976378220544.md:L9`「三：关注八字的穿、刑、破，被坏了的字要看代表什么，是不是身体的一部分。」
- 校验：address=pass · edge=pass · ten_god=pass · quote=pass（边存在且 kind/members 一致；动态边 actor 由 engine 保持 null）

### dc2（B1 / `human_anchor`）

- 方向：mutual（对称，不赋向），evidence_gap=same_line（同句）
- 依据：『丑午穿』是并列列举（原文另有『酉戌穿,丑午穿』式并列），对称不赋向；『伤了时上禄』是结果句，只说明受损方，没有给出施动主语。
- 规则：`docs/specs/actor-rules-v1.md:L104-L110`
- 引文（direction_support）：`sources/duan/MinerU_markdown_疾病_2056043976378220544.md:L139`「丑午穿，伤了时上禄，午代表女人的身体，丑是伤食的墓，又是阴的象，表示妇科方面的疾病了。实际得了子宫癌，午运丑午穿的应期，得病手术。」
- 校验：address=pass · edge=pass · ten_god=pass · quote=pass（边存在且 kind/members 一致；动态边 actor 由 engine 保持 null）

### dc3（B1 / `human_anchor`）

- 方向：actor→target，`M.b`(戌) → `D.b`(丑)，evidence_gap=same_line（同句）
- 依据：原文『命中因有戌坏丑』是主谓宾句：戌为施动主语、丑为受事；engine e010 为 xing(丑戌未 partial)、actor=null。原文用『坏』字，本卡按 engine 既有边 kind=xing 记录，不另造边。
- 规则：`docs/specs/actor-rules-v1.md:L95-L102`
- 引文（direction_support）：`sources/duan/MinerU_markdown_疾病_2056043976378220544.md:L141`「后经中医治疗，没有转移，治好了，命中因有戌坏丑，否则将过不去午运。」
- 校验：address=pass · edge=pass · ten_god=pass · quote=pass（边存在且 kind/members 一致；动态边 actor 由 engine 保持 null）

## 4) 状态候选 / 救应候选

| id | 层 | 档 | 结果 | 主张 | anchored_by |
|---|---|---|---|---|---|
| st1 | state | B1 | 病 | 妇科（子宫癌）：丑＝阴、伤食之墓，午＝女体/禄 | ['AQ2'] |
| st2 | state | B1 | 病 | 心脏/心慌（同章病性：丑午穿主心被伤） | ['AQ2'] |
| rs1 | rescue | B1 | 救 | 戌坏丑 → 病源被制，未转移、治好 | ['AQ1'] |

- **st1**（B1，病）：原文以丑午穿＋丑为阴/伤食之墓＋午为女体，直指妇科；并记子宫癌、午运手术。
  - 引文：`sources/duan/MinerU_markdown_疾病_2056043976378220544.md:L139`「丑午穿，伤了时上禄，午代表女人的身体，丑是伤食的墓，又是阴的象，表示妇科方面的疾病了。实际得了子宫癌，午运丑午穿的应期，得病手术。」
  - 引文：`sources/duan/MinerU_markdown_疾病_2056043976378220544.md:L17`「丑：生殖器、妇科、肛门」
- **st2**（B1，病）：同章病性条把丑午穿读作心脏：『丑午穿--------心是被伤，心慌惊悸』；该读法与本造『午得寅生，旺，所以不得心脏病』的判据互斥，须以事实定夺。
  - 引文：`sources/duan/MinerU_markdown_疾病_2056043976378220544.md:L123`「丑午穿--------心是被伤，心慌惊悸。」
  - 引文：`sources/duan/MinerU_markdown_疾病_2056043976378220544.md:L27`「午：心脏、阳亢、血压、神经」
  - 引文：`sources/duan/MinerU_markdown_疾病_2056043976378220544.md:L131`「原局的毛病是丑午穿，午得寅生，旺，所以不得心脏病。」
- **rs1**（B1，救）：原文『命中因有戌坏丑，否则将过不去午运』——戌坏丑被当作能过关的原因（救应），与 dc3 同源但用途相反：dc3 是方向，rs1 是救应效果。
  - 引文：`sources/duan/MinerU_markdown_疾病_2056043976378220544.md:L141`「后经中医治疗，没有转移，治好了，命中因有戌坏丑，否则将过不去午运。」

## 5) 锚点题（只问已发生事实）

### AQ1 · direction · discriminates=['dc1', 'dc2']

> 你的妇科病（或相关手术）确诊之前，是否先发生过『婚姻或家庭重大变故』（分居、离婚、丧偶、家人重病）？

- 能区分的原因：dc1 把施力方定在日支丑（夫妻宫）→ 家庭侧先动、病随后；dc2 说两侧同损、无先后。若确有『变故在前、发病在后』的时间顺序，单侧施力读法保留；否则对称读法保留。
- 规则：`docs/specs/actor-rules-v1.md:L104-L110`；`source_mentions_answer=False`；proxy=medium
- 答「是」：keep ['dc1']；eliminate ['dc2']
- 答「否」：keep ['dc2']；eliminate ['dc1']
- 答不出：`needs_anchor`，影响 ['dc1', 'dc2']
- **答案（留空，待人类/命主）**：`anchor_a: []`

### AQ2 · state · discriminates=['st1', 'st2']

> 在那次发病期间，你是否同时出现过心脏、血压或心慌惊悸方面的症状（并被医生记录）？

- 能区分的原因：st2 的读法要求心脏侧确有受病记录；st1 的读法要求妇科侧为主。两者在原文中互斥（『午得寅生，旺，所以不得心脏病』），只能由事实定夺。
- 规则：`sources/duan/MinerU_markdown_疾病_2056043976378220544.md:L9`；`source_mentions_answer=False`；proxy=high
- 答「是」：keep ['st2']；eliminate []；downgrade ['st1']
- 答「否」：keep ['st1']；eliminate ['st2']
- 答不出：`needs_anchor`，影响 ['st1', 'st2']
- **答案（留空，待人类/命主）**：`anchor_a: []`

## 6) 引擎校验

| 校验 | 通过/总数 |
|---|---|
| address | 6/6 |
| edge | 3/3 |
| ten_god | 6/6 |
| quote | 6/6 |
| 原文/宫位引文 | 6/6 |

植入错误自检：4/4 拦截（`pass`）

- fake_address:Q.b → 拦截（engine 未输出该地址）
- fake_edge:e999 → 拦截（engine relations 无此 edge_id）
- wrong_ten_god:D.b=正印 → 拦截（十神不符）
- tampered_quote:HY:L15 → 拦截（该行未找到逐字文本）

## 7) 缺口与非断言

- gaps：G2, G3, G4, G5, muku_open_close, suiyun_ten_god, disease_severity_not_scored
- 非断言：不判疾病名称、严重程度、生死、应期
- 非断言：不把『丑午穿』直接写成断语；象法条目只是检索依据
- 非断言：不判救应成立（rs1 仅候选）；不判岁运（午运）引动

---

# P0-04 · 财 · 乙巳 己丑 壬辰 辛丑（乾）

| 项 | 值 |
|---|---|
| 卡档位 | **B1** / `decision_by=anchor_fact` / `direction_tier=A` / `pending=anchor_q` |
| tier_reason | ['direction:engine_fixed', 'state:conflict', 'rescue:candidate_only', 'pending:state_anchor'] |
| chart_id / 日主 | `cf-4d8fe4fe1b354d973a7b` / 壬 |
| 快照 | dayun_index=null，liunian_year=null（原局；四柱输入不起运） |
| 问题 | 我的生意和资产做得不小，最担心守不住；我的财到底是从哪来的、能不能守住？ |
| 问题域 | wealth |
| 原文出处 | `sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md` L384-L398（案例） |
| 后续事实（备查，不作预测） | 原文后续事实：戌运发财五年、资产4亿；乙运坐牢、没收财产、判刑十年（P0 仅备查，不作预测依据）。 |

## 0.5) 宫位映射与 material edge

| addr | 角色 | 十神 | 映射 | 依据引文 |
|---|---|---|---|---|
| `M.b` | 月支丑：官星（正官）—财生官、官当财看 | 正官 | M-06 | `sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md:L392`「原局：月时丑官都入辰墓，为官入辰墓，年上巳生合丑官，财生官，财弱官旺，官当财看。所以是个富命，辰是主要功神。」 |
| `D.b` | 日支辰：水库/土库，本造『主要功神』 | 七杀 | M-07 | `sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md:L392`「原局：月时丑官都入辰墓，为官入辰墓，年上巳生合丑官，财生官，财弱官旺，官当财看。所以是个富命，辰是主要功神。」 |
| `Y.b` | 年支巳：偏财（财源） | 偏财 | M-02 | `sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md:L392`「原局：月时丑官都入辰墓，为官入辰墓，年上巳生合丑官，财生官，财弱官旺，官当财看。所以是个富命，辰是主要功神。」 |

- material edge（问题命中的边）：
  - `e008`：巳丑三合拱(财生官的载体)
  - `e004`：辛克乙：破坏辰(功神)的克向
  - `e010`：丑辰破：库被动摇

## 1) engine 事实（`engine.cli all/relations`）

| 柱 | 干支 | 干(addr/十神) | 支(addr/十神) | 藏干 |
|---|---|---|---|---|
| year | 乙巳 | 乙 `Y.s` 伤官 | 巳 `Y.b` 偏财 | 丙本气(偏财)、庚中气(偏印)、戊余气(七杀) |
| month | 己丑 | 己 `M.s` 正官 | 丑 `M.b` 正官 | 己本气(正官)、癸中气(劫财)、辛余气(正印) |
| day | 壬辰 | 壬 `D.s` 日主 | 辰 `D.b` 七杀 | 戊本气(七杀)、乙中气(伤官)、癸余气(劫财) |
| hour | 辛丑 | 辛 `H.s` 正印 | 丑 `H.b` 正官 | 己本气(正官)、癸中气(劫财)、辛余气(正印) |

- 旬空：日旬 ['午', '未']；年旬 ['寅', '卯']；命中 None
- 体用（duan_zuogong.tiyong）：{'Y.s': '双属', 'Y.b': '用', 'M.s': '用', 'M.b': '用', 'D.s': '体', 'D.b': '用', 'H.s': '体', 'H.b': '用'}
- 墓库（relations.muku）：[{'addr': 'M.b', 'branch': '丑', 'ku_of': ['金'], 'openers': [], 'chuan_po': ['e010'], 'binders': [], 'candidates': []}, {'addr': 'D.b', 'branch': '辰', 'ku_of': ['水', '土'], 'openers': [], 'chuan_po': ['e010', 'e011'], 'binders': [], 'candidates': [{'addr': 'D.s', 'char': '壬', 'effect': '不论入墓', 'excluded': True, 'requires_judgment': []}, {'addr': 'M.b', 'char': '丑', 'effect': '入墓', 'excluded': False, 'requires_judgment': []}, {'addr': 'H.b', 'char': '丑', 'effect': '入墓', 'excluded': False, 'requires_judgment': []}]}, {'addr': 'H.b', 'branch': '丑', 'ku_of': ['金'], 'openers': [], 'chuan_po': ['e011'], 'binders': [], 'candidates': [{'addr': 'H.s', 'char': '辛', 'effect': '不论入墓', 'excluded': True, 'requires_judgment': []}]}]

### 关系边（原样引用 edge_id）

| edge_id | kind | members | chars | 距离 | 组/完整度 |
|---|---|---|---|---|---|
| e001 | ke | ['Y.s', 'M.s'] | ['乙', '己'] | 1 | / |
| e002 | sheng | ['D.s', 'Y.s'] | ['壬', '乙'] | 2 | / |
| e003 | stem_chong | ['Y.s', 'H.s'] | ['乙', '辛'] | 3 | / |
| e004 | ke | ['H.s', 'Y.s'] | ['辛', '乙'] | 3 | / |
| e005 | ke | ['M.s', 'D.s'] | ['己', '壬'] | 1 | / |
| e006 | sheng | ['M.s', 'H.s'] | ['己', '辛'] | 2 | / |
| e007 | sheng | ['H.s', 'D.s'] | ['辛', '壬'] | 1 | / |
| e008 | sanhe | ['Y.b', 'M.b'] | ['巳', '丑'] | 1 | 巳酉丑/gong |
| e009 | sanhe | ['Y.b', 'H.b'] | ['巳', '丑'] | 3 | 巳酉丑/gong |
| e010 | po | ['M.b', 'D.b'] | ['丑', '辰'] | 1 | / |
| e011 | po | ['D.b', 'H.b'] | ['辰', '丑'] | 1 | / |

- 段派做功候选（`duan_zuogong.candidates`，共 31 条；下表只列本卡引用到的）：

| mode | members | actor | edge_id |
|---|---|---|---|
| 制用 | ['H.s', 'Y.s'] | H.s | e004 |
| 生泄用 | ['Y.b', 'M.b'] | Y.b | None |
| 墓用 | ['D.b', 'M.b'] | D.b | None |

## 2) 原文锚点

- 命例四柱：`sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md:L384`「乙己壬辛」
- 命例四柱：`sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md:L386`「巳丑辰丑」
- 后续事实：`sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md:L394`「行戌运，财库冲入自己发财五年，资产4亿。」

## 3) 方向候选（2–3 条，均不自动选定）

| id | 档 | 类/kind | 方向 | 边 | decisive | conflict_with | 校验 |
|---|---|---|---|---|---|---|---|
| dc1 | A | 墓/muku | actor→target D.b→M.b | `墓用(['D.b', 'M.b'])` | True | [] | valid |
| dc2 | A | 克/ke | actor→target H.s→Y.s | `e004` | True | [] | valid |
| dc3 | A | 生/sheng | actor→target Y.b→M.b | `生泄用(['Y.b', 'M.b'])` | True | [] | valid |

### dc1（A / `agent_auto`）

- 方向：actor→target，`D.b`(辰) → `M.b`(丑)，evidence_gap=doctrine_only（只有定义/通用句）
- 依据：engine 墓用候选 (D.b,M.b)、actor=D.b（库收，符合 actor-rules §4.9）。原文『月时丑官都入辰墓』是位移句（按 §4.9 只给位移不给向），但紧接『辰是主要功神』把辰标为主功方；两据合并取库→入库方。
- 规则：`docs/specs/actor-rules-v1.md:L150-L166`
- 引文（direction_support）：`sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md:L392`「原局：月时丑官都入辰墓，为官入辰墓，年上巳生合丑官，财生官，财弱官旺，官当财看。所以是个富命，辰是主要功神。」
- 校验：address=pass · edge=pass · ten_god=pass · quote=pass（engine 做功候选命中（固定类））

### dc2（A / `agent_auto`）

- 方向：actor→target，`H.s`(辛) → `Y.s`(乙)，evidence_gap=same_line（同句）
- 依据：原文『辛克乙等于破坏了辰』是主动句，辛为句法主语；engine e004 ke(辛,乙)、actor=H.s 与之一致。此向用于『守不住』一侧（印克伤官、破坏功神辰）。
- 规则：`docs/specs/actor-rules-v1.md:L120-L127`
- 引文（direction_support）：`sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md:L396`「乙酉运之乙运，这里的乙不仅代表年上的乙，也代表辰，乙透干有克无生，辛克乙等于破坏了辰。主凶。」
- 校验：address=pass · edge=pass · ten_god=pass · quote=pass（边存在且 kind/members 一致；动态边 actor 由 engine 保持 null）

### dc3（A / `agent_auto`）

- 方向：actor→target，`Y.b`(巳) → `M.b`(丑)，evidence_gap=same_line（同句）
- 依据：原文『年上巳生合丑官，财生官』：巳为句法主语、生合为谓语；engine 生泄用候选 (Y.b,M.b)、actor=Y.b 一致。财源=年支巳(偏财)生月支丑(官)。
- 规则：`docs/specs/actor-rules-v1.md:L129-L137`
- 引文（direction_support）：`sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md:L392`「原局：月时丑官都入辰墓，为官入辰墓，年上巳生合丑官，财生官，财弱官旺，官当财看。所以是个富命，辰是主要功神。」
- 校验：address=pass · edge=pass · ten_god=pass · quote=pass（engine 做功候选命中（固定类））

## 4) 状态候选 / 救应候选

| id | 层 | 档 | 结果 | 主张 | anchored_by |
|---|---|---|---|---|---|
| st1 | state | B1 | 成 | 官入辰墓＋财库冲入 → 富命 | ['ED1'] |
| st2 | state | B1 | 败 | 辛克乙破坏辰 → 主凶；乙运坐牢、没收财产 | ['ED1'] |
| st3 | state | C | needs_anchor | 财弱官旺、官当财看（财的定义口径） | [] |
| rs1 | rescue | C | 应 | 行戌运，财库冲入自己 → 岁运层面的『开库得财』 | — |

- **st1**（B1，成）：原局：月时丑官入辰墓、巳生丑官，官当财看，故断富命；岁运戌运冲开财库，五年发财、资产4亿。
  - 引文：`sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md:L392`「原局：月时丑官都入辰墓，为官入辰墓，年上巳生合丑官，财生官，财弱官旺，官当财看。所以是个富命，辰是主要功神。」
  - 引文：`sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md:L394`「行戌运，财库冲入自己发财五年，资产4亿。」
- **st2**（B1，败）：岁运乙透（代表辰）被辛克、辰被破坏，原文判『主凶』；同运癸未年坐牢、没收财产、判刑十年。
  - 引文：`sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md:L396`「乙酉运之乙运，这里的乙不仅代表年上的乙，也代表辰，乙透干有克无生，辛克乙等于破坏了辰。主凶。」
  - 引文：`sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md:L398`「癸未年刚入乙运坐牢，因非法集资而没收产财。判刑十年。现已出狱。」
- **st3**（C，needs_anchor）：『官当财看』是本造把官星当财的口径说明；它决定『财』指什么，不回答能否守住，故不单独成断。
  - 引文：`sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md:L392`「原局：月时丑官都入辰墓，为官入辰墓，年上巳生合丑官，财生官，财弱官旺，官当财看。所以是个富命，辰是主要功神。」
- **rs1**（C，应）：『财库冲入自己』是岁运引动（戌运）而非原局救应；本卡快照 dayun_index=null，按规格 §4.1 不跨快照引用，故只记录为岁运候选、不判。
  - 引文：`sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md:L394`「行戌运，财库冲入自己发财五年，资产4亿。」

## 5) 锚点题（只问已发生事实）

### AQ1 · state · discriminates=['st1', 'st2']

> 你过去是否经历过资产被一次性清空（罚没、没收、强制清算或巨额赔付）？

- 能区分的原因：st2 的破局读法要求『资产被一次性打掉』这一已发生事实；st1 的富命读法只要求财富曾经形成。若确已清空，破局读法优先；若从未清空，保留富命读法。
- 规则：`sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md:L396-L398`；`source_mentions_answer=True`；proxy=high
- 答「是」：keep ['st2']；eliminate ['st1']
- 答「否」：keep ['st1']；eliminate ['st2']
- 答不出：`needs_anchor`，影响 ['st1', 'st2']
- **答案（留空，待人类/命主）**：`anchor_a: []`

## 6) 引擎校验

| 校验 | 通过/总数 |
|---|---|
| address | 7/7 |
| edge | 3/3 |
| ten_god | 7/7 |
| quote | 7/7 |
| 原文/宫位引文 | 6/6 |

植入错误自检：4/4 拦截（`pass`）

- fake_address:Q.b → 拦截（engine 未输出该地址）
- fake_edge:e999 → 拦截（engine relations 无此 edge_id）
- wrong_ten_god:D.b=正印 → 拦截（十神不符）
- tampered_quote:HY:L15 → 拦截（该行未找到逐字文本）

## 7) 缺口与非断言

- gaps：G2, G3, G4, G5, muku_open_close, suiyun_ten_god, snapshot_dayun_null
- 非断言：不判财运高低、破财年份、牢狱、生死
- 非断言：不把『富命』或『主凶』择一写成结论（本条交 ED1 专家裁决）
- 非断言：不判岁运引动；不跨快照引用 edge_id

---

# 关键选择清单（交中枢/人类）

> 只答事实，不选方向。答完由后续卡（T-197b）按每题 `elimination`（yes/no/unknown）机械淘汰候选；答不出→该候选转 `needs_anchor`。

| 序号 | 卡 | 题号 | 层 | 题目（是/否） | 区分候选 | 答「是」 | 答「否」 |
|---|---|---|---|---|---|---|---|
| 1 | P0-01 | AQ1 | direction | 你的婚姻破裂过程中，是否出现过『你的父母、兄弟或原生家庭出面介入、施压或替你做主』的具体事实？ | ['dc1', 'dc2'] | keep ['dc1'] / elim ['dc2'] | keep ['dc2'] / elim ['dc1'] |
| 2 | P0-01 | AQ2 | direction | 你与已经分开的配偶，是否至今仍有联系或经济往来（即分开后并没有彻底断干净）？ | ['dc1', 'dc3'] | keep ['dc3'] / elim ['dc1', 'dc2'] | keep ['dc1', 'dc2'] / elim ['dc3'] |
| 3 | P0-02 | AQ1 | direction | 你过去十年里，收入的主要来源是否以『体制外的项目、投资或兼职』为主，而不是固定级别的工资？ | ['dc1', 'dc2'] | keep ['dc2'] / elim ['dc1'] | keep ['dc1'] / elim ['dc2'] |
| 4 | P0-03 | AQ1 | direction | 你的妇科病（或相关手术）确诊之前，是否先发生过『婚姻或家庭重大变故』（分居、离婚、丧偶、家人重病）？ | ['dc1', 'dc2'] | keep ['dc1'] / elim ['dc2'] | keep ['dc2'] / elim ['dc1'] |
| 5 | P0-03 | AQ2 | state | 在那次发病期间，你是否同时出现过心脏、血压或心慌惊悸方面的症状（并被医生记录）？ | ['st1', 'st2'] | keep ['st2'] / elim [] | keep ['st1'] / elim ['st2'] |
| 6 | P0-04 | AQ1 | state | 你过去是否经历过资产被一次性清空（罚没、没收、强制清算或巨额赔付）？ | ['st1', 'st2'] | keep ['st2'] / elim ['st1'] | keep ['st1'] / elim ['st2'] |

## 答案回收表（留空）

| 卡 | 题号 | 答案（是/否/不知道） | 回答人 | 时间 | 备注 |
|---|---|---|---|---|---|
| P0-01 | AQ1 |  |  |  |  |
| P0-01 | AQ2 |  |  |  |  |
| P0-02 | AQ1 |  |  |  |  |
| P0-03 | AQ1 |  |  |  |  |
| P0-03 | AQ2 |  |  |  |  |
| P0-04 | AQ1 |  |  |  |  |

# 第三方重推指引

1. 盘面事实：按每卡 `provenance.engine_cmd` 重跑，比对 `chart_id`、四柱、十神、edge_id/kind/members。
2. 引文：按 `source_ref`（`path:Ln`）打开原文，逐字比对；本包构建脚本对全部引文做了子串校验（24 条原文/宫位引文 + 每候选引文）。
3. 候选：只看 `basis + quote + decisive + conflict_with + evidence_gap`；冲/合/穿/刑不得 A；无源即 C。
4. 复现构建：`.venv\Scripts\python.exe tasks/T-197/build_p0_cards.py`（幂等，仅读 `tasks/T-197/_engine/*.json` 与 `sources/`）。

# 与 T-196 规格的对齐（analysis-card-v2 / agent-candidate-set/v1）

- 目标 schema：agent-candidate-set/v1（生成器 §7）；选定后装配为 analysis-card/v2
- 已映射字段：
  - option_id / claim{relation,direction,members,actor,target} / basis[{kind,ref,note}] / source_ref / quote / decisive / conflict_with / conflict_class / engine_note
  - direction_tier / state_tier / rescue_tier / tier / decision_by / card_status / pending
  - anchor_q{qid,text,fact_window,fact_domain,answer_type=yes_no,discriminates,elimination[yes/no/unknown]} / anchor_a
  - engine_validation{snapshot,address,edge,ten_god,quote,seeded_error,overall}
- 扩展（v2 未定义，本包保留）：
  - claim.direction='undetermined'：v2 枚举只有 actor_to_target|mutual，本包为『合/冲但方向不可判』的候选保留第三值
  - basis_text：中文依据散文（v2 的 basis 只允许结构项）
  - state_label：成败候选的原文词（成/败/疑/多现/病/救/应），state 三态另存
  - facts / palaces / material_edges / material_edge_reasons：证据包层（供第三方重推）
- 未实现（需选定后装配，或按 T-197 禁止代选）：
  - `selected_option/selected_state/selected_rescue`：T-197 明令不自动选定；pending=anchor_q 前不得填
  - `t1–t5 与 statement/statement_claims`：analysis-card/v2 在选定后才装配；本包是候选集不是成品卡
  - `anchor_a 实体答案`：待人类/命主回答；Agent 不代答
  - `agent_top1`：生成器 §8.2 的 B1 lift 基线，本包未冻结（避免锚定）
- 已知口径冲突：
  - v2 的 A 档要求 selected_option 已填且 pending=none；T-197 禁止代选 → direction_tier=A 的卡仍保持 selected_option=null
  - v2 的 C 档也用 selected_option=null + selection_source=needs_anchor；因此『待自动确认的 A』与『无源 C』在本包只能靠 direction_tier/pending 区分

# 未完成与风险

- T-196 三份规格在本卡生成途中落盘（analysis-card-v2 / agent-candidate-generator-v1 / first-principle-agent-first-v1）；本包已按 agent-candidate-set/v1 改名与补字段，但仍是 pending candidate set（pending=anchor_q），不是可交付的 analysis-card/v2（T-197 明令不选定）。
- 与 v2 的两处口径冲突：①v2 的 A 档要求 selected_option 已填、pending=none，而 T-197 禁止 Agent 代选 → 本包 direction_tier=A 的卡仍 selected_option=null；②v2 的 C 档要求 selected_option=null 且 selection_source=needs_anchor，与 A 未选状态同形，故本包用 tier/pending 区分『待自动确认的 A』与『无源的 C』。
- 四柱输入无出生时刻：engine input_limitations 明确不起运/不给大运公历年份；本包全部 dayun_index=null、liunian_year=null。
- G5 救应未判：engine.structures 的 rescuer 命中只作要件，不作救应结论。
- 『寅申之冲，寅多作用一次』的『作用一次』是计数用语，本卡按 same_page 缺口记为方向依据，是否够格由中枢裁。
- P0-04 的原局富/岁运破属成败层，按 analysis-card-v2 §5.3 不适用方向层 B2；已改为 state 锚点题（原文已写结局 → source_mentions_answer=true），expert_decision 置 null，本包 B2 = 0。
- 本包 4 例的方向候选里，P0-01/P0-03 的『单侧施力』读法都依赖结果句/计数句（evidence_gap=same_page），是否够格作方向依据，需中枢裁。
- 锚点题答案与原文后续事实存在部分可推测性（例：P0-01 原文已写五次婚姻）；本包题目刻意选原文**未写**的事实（原生家庭是否介入、分开后是否仍有往来、收入结构、发病前家庭变故、心脏症状）以降低泄漏。
- P0-04 的『原局富 vs 岁运破』属**成败层**，按 analysis-card-v2 §5.3 不适用方向层 B2，已改为 state 锚点题（AQ1，`source_mentions_answer=true`）；本包 B2=0。
- 本包是 `agent-candidate-set/v1` 的 **pending** 形态（`pending=anchor_q`），不是可交付的 `analysis-card/v2`：v2 的 `t1–t5` / `statement_claims` 须在选定后装配，而 T-197 禁止代选。
