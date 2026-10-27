# T-143 BRIEF · 断语层：修 M1-D-298 编译 + 补 invalidators + 挂 needs_judgment

- 任务卡：`tasks/T-143/PROMPT.md`
- 决策依据：`docs/adr/ADR-007-refactor-direction-adjudication.md` D10 / D11 / D12
- 前置：T-142 已完成（已核对：`atoms.py` 有 `needs_judgment`；`he_at` 只认 `HE_KINDS=("liuhe","zhi_anhe")`，`ganzhi_zihe` / 半局 / 拱局已排除）
- 状态：**已完成**，三条验收命令全绿，`verify_baseline --compare` 未退步

## 0. 一句话结论

`M1-D-298` 在 481 盘上的 `candidate` 从 **39 升到 75**（T-142 之前是 6），标杆盘 坤造 癸丑 癸亥 辛亥 癸巳 从 **rejected 变成 needs_fact**（不再是「系统对这张盘零输出」）；试点未知率 **0.0 → 0.2**，未知显性率 **1.0**；20 条断语的 `invalidators` 从 **0/20 非空** 变为 **4/20 非空**，每条都带逐字锚点并已被机器校验（0 MISS）。

---

## 1. 前置检查（先做的，结论：通过）

| 检查项 | 结果 |
|---|---|
| `engine/claims/condition_ir/atoms.py` 含 `needs_judgment` 原子 | ✅ 有，且 `SIGNATURES` 里 `reason` 为必填 |
| `he_at` 已收窄（只认六合与暗合） | ✅ `HE_KINDS = ("liuhe","zhi_anhe")`，`_is_he_edge()` 排除 `wuhe`/`sanhe`/`sanhui` 半局与拱局/`ganzhi_zihe`，并有 `exclude_god?` |

未替 T-142 补任何活。

---

## 2. ① `M1-D-298` 的 `frame_atom` 新形式与原文依据

### 2.1 改前 / 改后

```yaml
# 改前（错）：要求日支本气必须是财官
frame_atom: {atom: tiyong, args: {role: 用, at: D.b}}

# 改后：日支「有用」= 体用为 用 或 双属（只有 体 不算）
frame_atom:
  any:
    - {atom: tiyong, args: {role: 用, at: D.b}}
    - {atom: tiyong, args: {role: 双属, at: D.b}}
```

### 2.2 为什么是「用/双属」而不是「日支参与做功候选」

原文把「夫妻宫有用」与「夫妻宫制去夫妻星」分成两层：**「有用」是资格（frame），「制去/制不住」是成败（precondition + invalidator）**。若把「参与做功」直接当 frame，等于把成败塞进准入条件，会重犯「候选取代结论」。故 frame 只判资格。

**依据链（全部逐字，已被机器校验能在声明行命中）**：

| 锚点 | 引文 | 用来定什么 |
|---|---|---|
| `婚姻专辑:48` | 「夫妻宫位要安静，如有用，不能被刑坏，冲破，穿倒，或六合，暗合他星（配偶星以外的星）」 | 主句：「如有用」是资格判断 |
| `大连面授讲义:4109` ⑨ | 「坐下为用（财官食伤）就不好」 | **夫妻宫语境下「用」的取值域含食伤**——这就是收进 `双属` 的直接依据 |
| `婚姻专辑:58` | 「伤官亥冲巳，夫宫为喜，冲去夫星忌神」 | 标杆盘实证：日支亥是**伤官（双属）**，原文仍判「夫宫为喜」⇒ 双属必须算「有用」 |
| `婚姻专辑:70` | 「寅丑暗合，夫星合到夫宫」 | 合他星要排除配偶星本星（见 §3） |
| `大连面授讲义:701` | 「如果制不死，就是坏婚姻。」 | 「制死才算好」⇒ 成败必须单列，不能当 frame |

事实层配套：`engine/facts/structure_check.py:373` 的 `tiyong_view` 明确「食神偏体、伤官偏用，统一标双属，不替调用方强择」，`tiyong_of` 把食伤映射为 `双属`。本条 frame 就是把这个「不替调用方强择」的判断交给断语层做，并给出派别依据。

### 2.3 口径分歧（必须上报，不擅自抹平）

`4109` 同一条里还有 ①「男命财官食伤为用，女命财官为用」，字面上**女命的「用」不含食伤**，与 ⑨「坐下为用（财官食伤）」冲突。

- 本条取 **⑨**。理由：①自身紧接着承认「只有伤官制官、比劫去财」也是好婚姻机制（伤官属食伤）；②标杆盘坤造日支是伤官，原文判婚姻好；③若取①，坤造日支为食伤一律出局，与原文实例直接矛盾。
- 该分歧已写入 `synthesis_note`，**请中枢裁定是否作为契约 23 的 `tiyong` 口径附注**。

---

## 3. ② `he_at` 的限定参数与依据

```yaml
- not:
    atom: he_at
    args: {at: D.b, exclude_god: 配偶星}
```

- **「合他星」中的「他星」= 配偶星以外的星**：`婚姻专辑:48` 括号自注逐字写了「（配偶星以外的星）」。所以 `exclude_god: 配偶星` 不是我的发挥，是原文自注。
- **为什么配偶星本星相合不算坏**：`婚姻专辑:70`「此造丑为夫宫，寅为夫星，寅丑暗合，夫星合到夫宫，表示丈夫只跟自已好，一生好婚姻」——夫星合到夫宫是好事。
- 半三合 / 拱局 / 自合**不进** `he_at`：由 T-142 的 `_is_he_edge()` 在原子层挡掉（原文只举六合、暗合）。
- 原 `unmapped_prose`「未区分合的是否配偶星」**已删除**——这个缺口现在被编译了，留着就是假账。

---

## 4. ③ `invalidators`：补了 4 条（原 20/20 全空）

| 断语 | 失效条件（什么情况下不成立） | 生效方式 | 原文锚点（行号+逐字引文） |
|---|---|---|---|
| **M1-D-298** | 配偶星**既不透也不藏** → 无婚或克配偶，「婚姻较好」不成立 | **机械可判**（`not visible_god` + `not hidden_god`），实测在 481 盘上会真实拒绝 | `婚姻专辑:17`「如无则另看：男命再无遁藏，基本可能确定无婚，或克配偶。」 |
| **M1-D-298** | 夫妻宫虽有用且安静，但夫妻星**「制不死」** → 坏婚姻 | `needs_judgment`（力量比较无原子，不编阈值） | `大连面授讲义:701`「如果制不死，就是坏婚姻。如果此造改为申年，制不住官杀，婚姻就不好了。」 |
| **G-SP-130** | 夫妻宫落了夫妻星仍被**非配偶星**六合/暗合 → 一合就合走，不离不弃不成立 | **机械可判**（`he_at(at=D.b, exclude_god=配偶星)`），实测把本条 fired 从 231 压到 154 | `婚姻专辑:160`「夫妻宫落夫妻星时，不喜他合，包括六合，暗合，一合就容易合走了，离婚者居多。」（段派同构原文，跨流派交叉验证，已在 `invalidator_school_note` 声明未用段派结论替换高派前提） |
| **M1-D-009** | 有制用结构但**制不住**（力量相当）→ 不作功 | `needs_judgment` | `婚姻专辑:64`「此造坐支夫宫之伤官也欲制官星，但原局水火之力量相当…这样夫宫就制不住夫星了」 |
| **M2-Y-395** | 「我制了对方」仍可能坏婚：日主**身弱承载不住**；且刑坏≠离婚 | `needs_judgment`（本条 `needs_human`，机械层不参与求值，仅留档） | `杨清娟广州班:1529`「夫妻感情好不等于不离婚，她承载不了，身太弱了」；`:1697`「刑坏戌中辛金不等于离婚」 |

**4 条断语、5 个失效条件**（其中 **2 条机械生效**、3 条为 `needs_judgment` 占位）。之所以不硬造机械判据：契约 23 §6.3 已把 `compare(相对力量)` 列为未实现缺口，硬写阈值就是 M2-Y-251 那种「设计取值冒充原文数值」。

### 4.1 锚点机器校验

新增字段 `invalidator_evidence` / `source_refs`（D11 多锚点），每条带 `path`+`line`+`quote`。校验方式：`quote` 必须是 `path` 第 `line` 行的**连续子串**。

```text
11 条锚点全部 OK，MISS 总数 = 0
（含 M1-D-298 的 5 条 source_refs + 2 条 invalidator_evidence、G-SP-130 1 条、
  M1-D-009 1 条、M2-Y-395 2 条）
```

该校验已固化为测试 `tests/claims/test_pilot20_conditions.py::test_declared_quotes_are_verbatim_on_declared_line`（20 条参数化），原文语料变动导致行号漂移会直接红。

### 4.2 `not_found`（明确没补的）

| 断语 | 想补的失效条件 | 为什么没补 |
|---|---|---|
| M1-D-242 | 「印虚透不做功→有文化但非高学历」 | 只有库内摘要 `theory/raw/duan/promoted/m1-practice.md:16` 的 rule 名「印星做功=有学历/不做功=懒笨」，在 `sources/duan/` 原文里没找到逐字对应句。已写入 `invalidator_pending` 标 `not_found` |
| M3-R-166 | 「食神入墓但寿元正常」反例 | `墓__穿:11`「父酉入墓，有一个重要的前提，是本酉很弱了」只是**入墓作凶的前提**（收窄前置），不是失效判据，硬挂会变成前置误置。已标 `not_found` |
| M2-Y-014 / M3-R-013 / G-SP-071 | 未补 | 本卡只要求 3–5 条，这 3 条不在优先名单 |
| **M1-D-299** | —— | **`pilot-20.yaml` 里根本没有这条断语**（20 条中无此 id）。任务卡把它列为优先项，但目标文件里不存在；补它等于新增断语、改变 `claims_total`，超出本卡范围。**请中枢裁决是否单开一卡** |

---

## 5. ④ 给 4 条 partial 挂 `needs_judgment`（partial → compiled）

四条都把原先塞在 `unmapped_prose` 的未量化条件搬进 `preconditions.all` 的 `needs_judgment`，**不删除、不折算**：

| 断语 | `needs_judgment(reason=…)` 记的是什么 | `unmapped_prose` | 状态 |
|---|---|---|---|
| M1-D-009 | 「有制用结构」到「做功成立」之间缺：制得住否 / 功神还是废神 / 功的层数（`zuogong_layers`、`zuogong_success` 均不存在） | 已清空 | partial → **compiled** |
| M1-D-013 | 入墓是否等于「得到/控制」：宾主方位 + 库是否被冲开（冲为库活、不冲为墓死） | 已清空 | partial → **compiled** |
| M1-D-242 | 印与它星有制/合/冲的边 ≠ 印做功成功；还需得根得令、是否被合解 | 已清空 | partial → **compiled** |
| M3-R-166 | 食神入墓是否等于寿元受损，还缺「印星被坏」「枭夺食」「本字弱/旺」分支 | 已清空 | partial → **compiled** |

### 5.1 判定标准（481 盘实测，全部出现 `needs_fact`，无恒真恒假）

```text
claim        domain  fired  labelled  unknown  verdict
M1-D-009     事业        0         0      480   样本不足
M1-D-013     财富        0         0      225   样本不足
M1-D-242     学历        0         0      371   样本不足
M3-R-166     健康        0         0       41   样本不足
```

`fired=0` 是**设计结果**：`needs_judgment` 恒 unknown，所以这些断语永远不返回 `candidate`，只返回 `needs_fact`——正是 D12 要的「不能删掉子条件当 compiled 跑」。481 盘上 480/225/371/41 盘走到 `needs_fact`，说明它们既非恒真也非恒假。

> **副作用（需中枢知情的指标口径）**：报告里这 4 条会进 `outlier_claims`（开火率 0 ＝「过严/绑定失效」）。对它们，`fire_rate` 已不是有效指标，**应改看 `needs_fact` 数**。本卡未改工具（`tools/` 不在 File Scope）。

---

## 6. ⑤ M3-R-166 能否解锁 / M2-Y-017 是否可编译

**结论：`M2-Y-017` 现在可编译（`lu_at` 已够用），但本卡不动它的 `compile_state`，交中枢裁决。**

依据（我试编了结构并在 481 盘上实跑，脚本未留档，结构如下）：

```yaml
all:
  - {atom: visible_god, args: {god: 印}, as: Y1}
  - any: [edge_touches(ke,$Y1), chong_at($Y1), chuan_at($Y1), po_at($Y1)]
  - {atom: visible_god, args: {god: 食伤}, as: S1}
  - any: [edge_touches(ke,$S1), chong_at($S1), chuan_at($S1), po_at($S1)]
  - {atom: lu_at, args: {}}          # 禄 = 日主之禄，T-142 已提供
```

- 481 盘结果：**True 27 / False 454 / None 0** —— 可求值、有区分度、无 unknown，说明「缺禄原子」这个阻塞点已被 T-142 消掉。
- 因此 `M3-R-166` 的 `requires_pair → M2-Y-017` **不再必然空转**，一旦中枢把 M2-Y-017 判 compiled，配对即可参与裁决。
- 但 `M3-R-166` 现在**不依赖**这个配对结论：它的 `preconditions` 已含 `needs_judgment`，求值在配对检查之前就落 `needs_fact`（41 盘）。所以本条我现在就敢从 partial 转 compiled。
- 仍需中枢定的三件事：①「三宝被坏」的「坏」到底认哪几种关系（chong / chuan / po / ke / 被合算不算）；②「全坏」是三件各自被坏，还是允许「两坏一休」；③ `visible_god` 只认透干，地支本气算不算「有」——这三个都影响 27 这个数。

---

## 7. 验收（中枢请亲自重跑；以下是我本机实际输出）

```text
.venv\Scripts\python.exe -m pytest -q
→ 1040 passed, 1 skipped, 1 warning in 104.86s, EXIT=0
   skip 仍是 T-114 的 test_bundle_pii.py（已知红灯，非本卡引入）
   本卡新增 29 条：tests/claims/test_pilot20_conditions.py

.venv\Scripts\python.exe -m tools.claim_condition_corpus
→ cases=481，M1-D-298 fired=75 / labelled=34 / unknown=49 → 可做自然对照

.venv\Scripts\python.exe -m tools.claim_condition_report
→ compile_states {compiled:12, needs_human:5, uncompilable:2, reference_only:1}
  unknown_rate 0.2 / unknown_explicit_rate 1.0 / evaluable_rate 0.8
  state_distribution {rejected:152, candidate:35, evidence_only:5, needs_fact:48}
  unmapped_rate 0.25（改前 0.5）/ anchor_ok_rate 0.85 / anchor_exact_rate 0.75

.venv\Scripts\python.exe -m tools.verify_baseline --compare
→ pytest_passed 1040 / failed 0 / audit_errors 0 / relations_ok true /
  zuogong_charts 477 / zuogong_day_branch 346 → 【基线未退步】EXIT=0
```

### 7.1 四条自证

**① M1-D-298 命中数 6 → ≥30：达标，实际 75。**
`6`（ADR-007 记录的原始值）→ T-142 修 `he_at` 后 `39` → 本卡修 `frame_atom` 后 **`75`**（481 盘，占 15.6%）。`rejected` 从 442 降到 357。

**② 标杆盘不再是 rejected：是 `needs_fact`。为什么：**
坤造 癸丑 癸亥 辛亥 癸巳，日支亥＝伤官→`tiyong=双属`，新 frame 通过（改前 frame 只认 `用`，这一步就死）。此后：

- 「安静」分支**为假**：`chong_at(D.b)` 成立（e012 亥冲巳）、`xing_at(D.b)` 成立（e010 亥亥自刑）；
- 第二条分支成立：`zuogong(kind=制用, involves=配偶星)` 命中（e012「伤官—正官」制用候选，正是原文「伤官亥冲巳」）；
- 该分支内的 `needs_judgment` 恒 unknown ⇒ `True AND Unknown = Unknown` ⇒ `needs_fact`，`unknown_facts` 非空（带原因），交给 Agent 判「夫妻宫被坏」还是「夫妻宫制去夫妻星、且制死」。

**这里没有硬凑成 candidate**：这条盘原局确实有冲有刑，「安静」字面不成立；硬判 candidate 等于把「制得住」当既成事实，正是 D12 反对的做法。

**③ 未知率 0.0 → 0.2，未知显性率 1.0：达标。**
`unknown_rate` 0.0 → **0.2**（48/240）；`unknown_explicit_rate` **1.0**（48 个 unknown 全部带 `needs_judgment` 原因文本）。
**为什么 `evaluable_rate` 从 1.0 掉到 0.8（红线三要求写明）**：这不是能力退步，是 D12 认定的「设计失效」被修掉了——改前 8 条 compiled 里 4 条把未量化条件删掉当 compiled 跑，数学上不可能产生 unknown，于是「可求值率 100%」是假账。现在 12 条 compiled 里有 48/240 对诚实落 unknown。**用一个真 0.2 的未知率换掉一个假 1.0 的可求值率，这是本卡的核心产出，不是副作用。**

**④ 新补 invalidators 每条都有可核对锚点：达标，0 MISS。**
5 个失效条件、6 条 `invalidator_evidence`，`quote` 全部是声明行号的连续子串（机器校验 + 固化测试）。行号与原文对应：`婚姻专辑:17/160`、`大连面授讲义:701`、`婚姻专辑:64`、`杨清娟:1529/1697`。

---

## 8. 需要中枢裁决的项

1. **`M1-D-299` 不在 `pilot-20.yaml`**：任务卡把它列为优先补 invalidators 的对象，但 20 条里没有这个 id。是否单开一卡、或先把 `M1-D-299` 加进库（会改 `claims_total`，需授权）？
2. **`4109` 内部口径冲突**：①「女命财官为用」vs ⑨「坐下为用（财官食伤）」。本卡取 ⑨（依据见 §2.3）。是否把这条写进契约 23 的 `tiyong` 口径附注？
3. **`M2-Y-017` 是否判 compiled**：试编在 481 盘上 True 27 / False 454 / None 0，可求值。判定前需先定「坏」认哪几种关系、「全坏」的合成规则（见 §6）。本卡**未改**它的 `compile_state`。
4. **`can_control` 落地后应回填 M1-D-298**：并发任务 T-145 正在 `atoms.py` 加 `can_control(actor, target)`（未验收、在途）。我用它试跑：
   - 标杆盘 `can_control(D.b → H.b)` = **True**（制者水得令且多5字，被制火无旺项）——与原文「冲去夫星忌神」吻合；
   - 对照盘 壬子 乙巳 庚子 壬午 = **None**（水火力量相当）——与原文「力量相当…夫宫就制不住夫星了」吻合。

   ⇒ 这正是 ADR-007「证明点 B」要的判别力。T-145 验收后，建议把本条 `preconditions` 里那个 `needs_judgment` 分支换成 `can_control(actor: D.b, target: <配偶星地址>)`，`M1-D-299` / `M2-Y-395` 同理。**本卡没这么做**：T-145 未合入、`atoms.py` 正在被改，依赖它会让我这条断语随对方回滚而变 `uncompilable`。
5. **`G-SP-071` 的岁运条件仍未挂 `needs_judgment`**：`unmapped_prose`「行运不走财运或食伤运」正是 D12 举的第二个例子（诚实写入岁运原子必 unknown）。任务卡只点了 4 条 partial，我没扩范围。建议随 T-145 一起收口。
6. **`outlier_claims` 现在 5 条**（M1-D-298 + 4 条原 partial）：4 条是「开火率 0 但 needs_fact 41–480」的设计结果，`fire_rate` 对它们失效（见 §5.1）。是否改 `tools/claim_condition_report.py` 的判读口径？（`tools/` 不在本卡 File Scope）

---

## 9. 改动文件（只这些是我改的）

| 文件 | 性质 |
|---|---|
| `theory/claims/conditions-v2/pilot-20.yaml` | ① `M1-D-298` frame_atom 改 `any[用,双属]` + `he_at` 加 `exclude_god:配偶星` + 冲刑改走分支 + `source_refs`(5) + `synthesis_note` + `invalidators`(2) + `invalidator_evidence`(2) + 删 `unmapped_prose`；② `G-SP-130` 加 `invalidators`(1)+`invalidator_evidence`(1)+`invalidator_school_note`；③ `M1-D-009` partial→compiled + `needs_judgment` + `invalidators`(1)+`invalidator_evidence`(1)；④ `M1-D-013` partial→compiled + `needs_judgment`；⑤ `M1-D-242` partial→compiled + `needs_judgment` + `invalidator_pending`(not_found)；⑥ `M2-Y-395` 加 `invalidators`(1)+`invalidator_evidence`(2)（`compile_state` 保持 `needs_human`）；⑦ `M3-R-166` partial→compiled + `needs_judgment` + `invalidator_pending`(not_found) |
| `tests/claims/test_pilot20_conditions.py` | **新增**，29 条：锚点逐字校验（20 参数化）/ 高价值断语 invalidators 非空 / 原 partial 必挂 `needs_judgment` / frame 必含 `双属` / 标杆盘不得 rejected / needs_fact 必带原因 |
| `META/claim-condition-pilot-v1.{json,md}`、`META/claim-condition-corpus-v1.json` | **验收命令自动重写**（工件，非手工编辑） |

**没改**：`engine/`（任何文件）、`theory/_ir/`、`sources/`、`pyproject.toml`、`tools/`。无任何 git 写操作（未 commit / push / checkout / stash / reset）。

> ⚠️ **`git status` 里 `engine/claims/condition_ir/atoms.py`、`engine/contracts/23-*.md`、`tests/claims/test_condition_ir_atoms.py` 的改动不是我的**：那是并发任务 **T-145**（岁运 4 原子 + 力量比较原子）正在写的，我开工期间（21:54）该文件被改过，`ATOMS` 从 44 变成 46（新增 `suiyun_arrives` / `can_control`）。报告里的 `atom_count: 46` 因此不是 44。**中枢验收时请注意这两份工作在同一工作区并行，`atoms.py` 的 mtime 会在我的测试运行期间变化。**

## 10. 未完成与风险

- **风险 1（并发）**：`atoms.py` 正在被 T-145 修改。我的 `pytest` 结果（1040 passed）是 2026-10-27 21:57 左右快照，若 T-145 随后又改，重跑会变数字。本卡的 YAML **不依赖**任何 T-145 新原子，最坏情况是报告里原子数与我记录的不同。
- **风险 2（指标）**：`evaluable_rate` 1.0→0.8、`outlier_claims` 1→5 都是 D12 的直接后果，已在 §7.1③/§5.1 写明归因，不是退步。
- **风险 3（口径）**：`M1-D-298` 冲刑分支目前只判到「有制用候选涉及配偶星」，粒度偏粗（`zuogong` 原子无法限定「日支必须是该候选的成员」）。所以「夫妻宫有冲」+「局中任何制用涉及官杀」都会被推成 `needs_fact`。这是**偏保守**的错（把可判的交给人判），不是把不可判的说成可判。`can_control` 落地后可显著收窄（见 §8.4）。
