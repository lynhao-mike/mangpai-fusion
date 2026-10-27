# ADR-007 · 重构方向外部评审的裁决记录

- **状态**：accepted（已接受）
- **日期**：2026-10-27
- **决策人**：中枢指挥官（依 [ADR-004](ADR-004-hub-commander-authority.md) 授权代决）
- **输入**：`docs/reviews/refactor-review-brief-v1.md`（中枢提交）+ 外部评审者的独立源码阅读与 481 盘实跑结论
- **影响**：D1–D12 全部裁决；推翻中枢简报 §6.2 的部分归因；撤销 T-135

## 0. 为什么要有这份记录

中枢提交的评审简报本身带着错误归因（§6.2 把 M1-D-298 低命中的原因判为「缺力量比较 + 缺岁运」）。外部评审用 481 盘逐原子拆解推翻了它。**中枢已逐条独立复现**，本 ADR 记录「哪些采纳、哪些否决、依据是什么」，避免结论再次失真。

---

## 1. 复现结论：谁对、谁错

### 1.1 外部评审纠正中枢的四处（中枢已实测确认）

| # | 中枢原判断 | 实测结果 | 影响 |
|---|---|---|---|
| 1 | M1-D-298 只命中 6 盘，是因为缺「力量比较」与「岁运应期」 | **错**。真因是 `he_at` 原子定义过宽 + `frame_atom` 误用 | 证明点需重设 |
| 2 | 「禄」只在 `engine/energy/tiyong.py:43`，事实层没有 | **错**。`engine/facts/chart_facts.py:67 _LU` 早已存在；`binzhu_side` 在 `:125` | **T-135 撤销** |
| 3 | `relation_graph` 只建原局四柱的边 | **错**。`relation_graph.py:85 _nodes(chart, dayun_index, liunian_year)` 已支持岁运建边并标注 `scope` | 岁运建模成本大幅下降 |
| 4 | `tests/track_e_smoke/test_e_negatives.py` 可能是假测试 | **错**。直接跑 `python tests/track_e_smoke/test_e_negatives.py` → `PASS=8 FAIL=0 EXIT=0`，八条都是真校验 | 门禁可低成本纳入 |

### 1.2 中枢实测到的新事实（外部评审指出，中枢确认）

- **`he_at` 过宽**：`HE_KINDS` 含 `sanhe` / `sanhui` / `ganzhi_zihe`，实测 `he_at(D.b)` 在 481 盘命中 **412 盘（85.7%）**，其中真正的合只有 `liuhe` 70、`zhi_anhe` 48；其余来自 `sanhui:partial` 134、`sanhe:half_sheng/half_mu/gong` 155、`ganzhi_zihe` 5。
- **`invalidators` 全域为空**：`pilot-20.yaml` 20 条断语的 `invalidators` **20/20 为空**。段派的「救应 / 反条件门」在编译层完全缺席。
- **两套权重实现并存**：`engine/application/weight_profile_service.py:70`（严格、读失败抛错）vs `engine/infrastructure/weight_repository.py:24,45`（两层 `except Exception` 静默回落到 `_DEFAULT_SCHOOL_WEIGHTS`）。

### 1.3 外部评审自身的三处错误（中枢已核实，不予采纳）

| 它说 | 实测 |
|---|---|
| `docs/adr/` 只有 ADR-001 至 ADR-004，ADR-005/006 未落地 | **错**。`ADR-005-case-time-basis.md`、`ADR-006-v5-retirement-strategy.md` 均在，对应提交 `e8cb4380`、`c4f10367` |
| `engine/decision/` 下 4 个 slice / 各文件行数（148/161/132/281） | 数量**错**：实测 3 个（`ren_career_timing_slice.py` 133 行、`yang_marriage_slice.py` 143 行、`ziping_career_structure_slice.py` 253 行）。但它指出的「中枢漏列 `ziping_career_structure_slice.py`」**成立** |
| `tools/render_report.py` 2281 行 | 口径差异：按换行切分 2282、按行统计 2041，两者都对，不作争议 |

**处理原则**：外部评审的错误不影响其核心结论的成立（核心结论均已由中枢独立复现）。但记录在此，提醒后续不要把它当作全知输入。

---

## 2. D1–D12 裁决

### D1 体用表冲突 —— 裁决：以 `structure_check.py` 为 SSOT，并修 `_crosses`

**采纳外部评审的 (b) 升级版**，依据是原文而非架构偏好。

原文（`sources/duan/MinerU_markdown_35.盲派命理开山之作_....md:1311-1313`）：「我们把日主、印星、禄神、比劫当体，财星、官杀星当用，**食神与伤官既可以是体，也可以是用**……如一定区分它们，则**食神更近于体，伤官则接近于用**。」

同书 `:1319`：「伤官与食神星为**中性之物**，食神略偏于体，伤官略偏于用。」

**结论**：`engine/facts/structure_check.py:94` 的 `双属` 是忠实实现；`engine/energy/tiyong.py:139-141` 无条件把食伤归体是**错的**——若食伤恒为体，段派核心的「枭印夺食」「印制食伤」会因两边都是体而被过滤掉。

**但 `_crosses` 有一处边界错**，采纳外部评审的修法：

```python
def _crosses(a: TiYong, b: TiYong) -> bool:
    return {a, b} not in ({"体"}, {"用"}, {"双属"})
```

原实现 `return {a, b} != {"体"} and {a, b} != {"用"}` 会让 `{"双属","双属"}` 返回 True，与 `_ti_yong_ends`（`:385-388` 已写 `if a == "双属" and b == "双属": return None`）自相矛盾。食伤内部互见不构成体用相交做功。

**处置**：`structure_check.py` 为唯一事实源；`energy/tiyong.py` 的硬编码归体标记为待废弃（不在本轮删除，避免动 v5 链）。

### D2 推理层单轨 —— 裁决：采纳，但不删 slice，冻结为回归基准

采纳「`condition_ir` 为唯一候选求值层、停止新增 slice」。**同时采纳外部评审的关键补充**：`engine/decision/` 三个 slice 里有三项机制是 IR 目前**没有**的，迁移前必须提取，否则会丢能力：

1. **`invalidators` 救应门**：`ziping_career_structure.py:182-189, 232-246` 的 `official_path_protection`（伤官见官但有财印救应 → CONTRADICTED）。而 `pilot-20.yaml` 的 `invalidators` **20/20 为空**。这是当前最大的能力缺口之一。
2. **事件 / 压力分级**：`yang_marriage.py:301-323` 的 `event` / `pressure` / `abstain` 三态。IR 现在只有 `candidate` / `rejected` / `needs_fact`，缺「轻度信号」档，容易把单条件开火当成事件。
3. **伏吟与岁运触发**：`ren_career_timing.py:114-126` 含伏吟（`left == right`）与「流年作用大运」（`target_kind == "dayun"`）。IR 无 `fuyin` 原子，岁运原子为空壳。

**处置**：三个 slice 冻结（不删、不新增），其状态被 `META/project-state.json` 与 `tests/test_production_entrypoints_unchanged.py` 锁定。上述三项以 IR 原子/字段表达后再议退役。

### D3 岁运建模 —— 裁决：复用已有建边能力，补 4 个原子，并强制原局隔离

采纳外部评审方案，核心两点：

1. **不另造建边**：`relation_graph.py:85` 已按 `dayun_index` / `liunian_year` 建好 `DY{i}.s/b`、`LN{year}.s/b` 节点与 `scope ∈ {natal, dayun, liunian, dayun+liunian}` 的边。
2. **必须先加原局隔离，否则污染**：所有关系原子（`edge` / `edge_touches` / `chong_at` / `he_at` / `chuan_at` / `xing_at` / `po_at` / `group_complete` / `muku_open`）默认只扫 `e.get("scope", "natal") == "natal"`。若先开岁运再补隔离，原局静态断语会被流年干支错误点燃。

**三值语义**（依契约 23 §四）：
- 探测存在性的 `dayun_present` / `liunian_present`：未提供时返回 **False**（「未提供」是客观输入事实）。
- 实质关系的 `suiyun_edge` / `sanhe_with_suiyun` / `chong_kai_muku`：未提供时返回 **unknown**，理由「待提供年份后可求值」，使 `state = needs_fact`，Agent 据此追问。
- **不引入第四种真值「不适用」**；只问原局时由 `time_window == "natal"` 在外层过滤断语集合。

### D4 力量比较原子 —— 裁决：采纳「三值 + 极端清晰盘才判」的混合架构

**否决**中枢原倾向里的「先做 heuristic_v1 能跑就行」——那会重蹈 v5 黑盒覆辙。

依据（原文，`sources/duan/MinerU_markdown_22.盲派初级命理学_....md:1759`）：「冲神之旺衰判断，**以多则为旺，寡则为衰；以合局会局为旺，以孤立受克为衰；以得令为旺，以失令为衰**。冲之力强弱判断，以冲中带克为强，以冲而不克为弱；以大运冲之为强，以太岁冲之为弱。」

依据（代码铁律，`engine/facts/structure_check.py:276`）：「力量对比不由代码裁决：恒为 `needs_judgment`，附日主与相关角色的地址及其通根地址。」

设计：
- 签名 `can_control(actor, target)`。
- **True**：actor 满足至少 2 项强势条件（得令 / 有本中气强根或三合三会成局 / 同党字数 ≥3），且 target 失令、无强根或根被坏、不成党。
- **False**：target 强旺成党得令有强根，而 actor 虚浮无根失令。
- **unknown**：双方均有根气，或两党对抗（段派「力量相当，互相制不了」，原文 `:1844`、`:1850`）。note 必须附双方根气与党势明细。

这一条让 `unknown` 第一次真正开火，是 ADR-003 立论的兑现点。

### D5 候选字段 —— 裁决：采纳 (a)+(c)，且升为 P0

外部评审指出一个中枢漏掉的**静默损坏**：`engine/api/facade.py:93` 的 `keep` 不含 `tiyong`，而 `engine/claims/condition_ir/atoms.py:495` 的 `zuogong` 原子直接 `c.get("tiyong")` → 恒得空元组 → `zip(members, ty)` 恒为空 → `target` 永远回退到 `members[-1]`。

**结论**：`zuogong` 原子的 target 识别目前处于静默失效状态。这是 P0。

处置：
- `keep` 扩为 `("mode","relation_kind","edge_id","members","ten_gods","tiyong","actor","binzhu","distance")`。
- `actor` 恒保留键，无方向时输出 `null`，不删键。
- **正交性说明**：`tiyong`（体/用/双属）、`binzhu`（主/宾层级）、`distance`、`actor` 全由位置与五行生克决定，不含吉凶结论，符合 ADR-001「引擎只发事实」。

### D6 破边不做功 —— 裁决：维持现状（不加 `po`）

原文（`sources/duan/MinerU_markdown_22.盲派初级命理学_....md:2010-2025`）：「**破不叫做功，他是破坏的意思**。破不叫做功，只表象，但午酉破也有做功的意思，因午克酉。」

原文（`MinerU_markdown_35.盲派命理开山之作_....md:1322`）列举做功方式：「体用、宾主之字进行**刑、冲、克、穿、合、墓**都是做功方式」——**不含破**。

**结论**：`relation_graph.py` 建 `po` 边是对的（象法用：破坏、漏洞、伤残），`structure_check.py:363` 的 `_ZHI_KINDS` 不含 `"po"` 也正确。唯一特例「午酉破」本质是火克金，应在克制中处理，**不得把全部 `po` 放进做功候选**，否则产生大量假候选。

### D7 权重静默回落 —— 裁决：采纳 Fail-Closed

- `engine/infrastructure/weight_repository.py:24,45` 的两层 `except Exception` 删除，改为抛错。
- 保留常量名 `_DEFAULT_SCHOOL_WEIGHTS`（`tests/test_production_entrypoints_unchanged.py` 有导入断言，不得破坏）。
- 生产读配置统一收口到已存在的严格实现 `engine/application/weight_profile_service.py:70`。

**实测佐证**：正常读配置 `{ziping:0.5, tiaohou_ditiansui:0.25, blind:0.25}`；路径指向不存在文件后静默变成 `{0.42, 0.32, 0.26}`——报告上看不出任何异常。

### D8 测试门禁 —— 裁决：分两阶段扩，先纠一个误判

**先纠正 T-131 子代理的错误报告**：`tests/track_e_smoke/test_e_negatives.py` **不是假测试**。该文件第 19 行自述「不依赖 pytest，纯 stdlib」，用 `_Reporter.add()` 计数并在 `main()` 里以退出码表达结果；直接跑实测 `PASS=8 FAIL=0 EXIT=0`。中介跑 pytest 得到 `no tests ran`（EXIT=5）是因为它被 `addopts --ignore` 排除，不是因为它无效。

**采纳两阶段方案**：
- 第一阶段纳入日常门禁：`tests/claims`、`tests/decision`、`tests/governance`、`tests/application`、`tests/tools` 全部、`tests/features`、根目录保护测试（`test_production_entrypoints_unchanged.py`、`test_project_metadata.py`、`test_error_policy.py`），以及包一层 `def test_track_e_negatives(): assert main() == 0` 的 `test_e_negatives.py`。
- 第二阶段：`tests/asof`、`tests/f09`、`tests/v5`、`tests/v1_3_acceptance` 归入独立的慢速门禁，不删、不阻塞日常迭代。`tests/r10` 的 4 个失败先查明是快照漂移还是逻辑回归。
- **禁止**一次性把 303 个塞进默认 `testpaths`。

### D9 ADR-006 —— 裁决：维持，但把「文档冻结」升级为「静态门禁测试」

外部评审支持 ADR-006，并给出更有力的实现方式：仓库已有范本 `tests/governance/static_isolation_scanner.py` 与 `tests/f09/test_production_isolation.py`，只需在门禁内加一个约 20 行的测试，扫描全仓 `.py` 的 `import engine.v5`，断言命中集合 ⊆ 冻结白名单，新增即红。

**采纳**：这比「写进 AGENTS.md」有效得多，也满足我方 T-134 卡的意图，但实现方式更好（AST 级、在门禁内）。T-134 按此改写。

**并确认**：`engine/cli.py` 与 `engine/api/facade.py` 零引用 `engine.v5`，Agent 侧不可见；唯一暴露点是 `tools/render_report.py:45-46`，属 T-128 的 P1。

### D10 婚姻 vs 岁运 —— 裁决：先打通岁运，再一次性编婚姻 60 条

**采纳外部评审的纵切顺序，否定我原来的「二选一」框架。**

理由：段派婚姻断语天然分两半——前半原局组合，后半紧接应期（「合处逢冲、冲处逢合为应期」）。若先编 60 条而不补岁运，凡带「逢冲之年」的条目只能标 `uncompilable` 或塞进 `unmapped_prose`，**编完还要返工第二遍**。

顺序：先 1 天接通岁运 4 原子 → 再一次完整编译婚姻 60 条（原局象 + 流年应期一体）。

### D11 多锚点合成 —— 裁决：维持不降级，但 schema 升级

维持中枢原裁定（「克者无根」「力量相当」保留 `anchored`；「目标旺透得长生」维持 `not_found`）。

**采纳外部评审的工具化补强**：把单锚点 `source_ref` 升级为 `source_refs: list` 并强制 `synthesis_note`，由锚点校验器逐一验证每个锚点真实存在，**防止借「合成」之名混入无据脑补**。

外部评审补充的证据（中枢采信其方向，但**未经中枢逐条复核**，编译时须再验）：「力量相当」原文有单句直述（`MinerU_markdown_22...md:1844`「戌辰力量相当，互相制不了」、`婚姻专辑:62`）。

### D12 未知率 0.0 —— 裁决：判定为 (b) 设计失效

采纳外部评审的 (b)，理由可代码验证，且中枢已实测确认其中一条：`pilot-20.yaml` 20 条断语的 `invalidators` **20/20 为空**，说明编译时把「救应 / 反条件」整体省略了。

归因三条：
1. **分母过滤**：`tools/claim_condition_report.py:68-73` 只对 `status == "compiled"` 的 8 条求值，把最可能产生 unknown 的 12 条（needs_human 5 / partial 4 / uncompilable 2 / reference_only 1）全部排除。
2. **半截编译**：8 条里 4 条（50%）把复杂条件塞进 `unmapped_prose`，例如 `G-SP-071` 的「行运不走财运或食伤运」被移出 `preconditions`。若诚实写入岁运原子，四柱输入下必然 unknown。
3. **原子值域**：剩余 8 条用到的 14 个原子，在「四柱 + 性别」输入下值域只有 `{True, False}`，**数学上不可能产生 unknown**。

**采纳其工程方案**：新增显式占位原子 `needs_judgment(reason)`（恒返回 unknown）。凡含未量化子条件的断语，**禁止把子条件删掉当 compiled 跑**，必须在 `preconditions.all` 里挂 `needs_judgment`。这样：前置客观条件为 False → `False AND Unknown = False` → rejected（过滤不相关盘）；前置为 True → `True AND Unknown = Unknown` → 推给 Agent 裁决。

---

## 3. 证明点的重新设定

**原定证明点 `M1-D-298` 作废**——它是纯原局静态判据（「夫妻宫要安静」），既不涉及「制得住」，也不是应期断语。把它当作「制得住 + 应期」的验证对象，是选错了对象。

**改为双证明点**：

- **证明点 A（静态层，半天）**：修 `he_at`（排除 `sanhui:partial` / `sanhe:half_*` / `ganzhi_zihe`，只认六合、暗合、且可排除配偶星本星）与 `frame_atom`（「夫妻宫有用」≠「日支本气是财官」）后，`M1-D-298` 在 481 盘的命中数须从 **6** 升至 **≥30**，状态由「样本不足」变「可做自然对照」。
- **证明点 B（动态层）**：编译 `M1-D-299` / `M2-Y-395`（夫妻宫冲制配偶星 + 制得住/制不住）并接婚姻应期规则，在原文标杆盘（癸丑 癸亥 辛亥 癸巳「冲制得住」vs 壬子 乙巳 庚子 壬午「力量相当制不住」）上区分成败并给出流年应期。

---

## 4. 处置清单

| 项 | 处置 |
|---|---|
| `tasks/T-135/PROMPT.md` | **撤销**（禄与宾主已在 `chart_facts.py`，前提不成立） |
| `tasks/T-134/PROMPT.md` | 改写为 AST 级静态门禁，纳入 `testpaths` |
| 中枢简报 §6.2 归因 | 已由本 ADR 更正 |
| `docs/reviews/refactor-review-brief-v1.md` | 保留原文不改（记录当时的判断），错误以本 ADR 为准 |

## 4.1 基线变动记录（红线三要求：任一指标下降须写明原因）

**`zuogong_probe` 的 `actor 在日支` 由 350 降至 346（−4）。中枢已逐盘核实，判定为修复，非回归。**

被删除的候选全部是 `制用` 且 `tiyong == ("双属","双属")`、`actor == "D.b"`，即「日支食伤 制 某干食伤」——正是 D1 要排除的「食伤内部互见」：

| 盘 | 删除的候选 |
|---|---|
| `C-2026-030-乾-己卯庚午丙辰戊子` | 制用 (D.b, Y.s) 双属×双属、(D.b, H.s) 双属×双属 |
| `C-2026-RF000668-乾-己卯庚午丙辰戊子` | 同上（同四柱，不同案例号） |
| `C-2026-RF000175-坤-乙亥己卯丁未乙巳` | 制用 (D.b, M.s) 双属×双属 |
| `C-2026-RF000487-乾-乙酉己丑丙辰庚寅` | 制用 (D.b, M.s) 双属×双属 |

依据原文：「食神与伤官既可以是体，也可以是用……在命中既可被制，也可制它」（`MinerU_markdown_35.盲派命理开山之作_....md:1319`）。食伤制食伤不构成体用相交做功，属假候选，删除正确。

**其余三项不变**：`pytest` 由 226 升至 959（T-144 扩门禁），`engine_audit` 0 错，`relations_audit` 通过，`zuogong_charts` 保持 477。

## 5. 未决

- 「同柱干支自合」（`ganzhi_zihe`）是否算「夫妻宫被合」——原文 M1-D-298 说的是「合他星」，而自合不涉他星。倾向**不算**，但需在编译 M1-D-298 时用原文逐句核定。
- 力量比较的「2 项强势条件」是中枢取的设计取值，非原文数值。原文只给定性指标（多寡、合局、得令）。**须在编译时标注为工程阈值，不冒充原文**。

## 来源

- 外部评审意见（2026-10-27，对 `docs/reviews/refactor-review-brief-v1.md` 的逐条回应）
- 中枢独立复现记录（481 盘；`he_at` 412/481、`invalidators` 20/20 空、`test_e_negatives` PASS=8）
- 相关：[ADR-001](ADR-001-engine-agent-boundary.md)、[ADR-003](ADR-003-claim-conditions-and-school-routing.md)、[ADR-006](ADR-006-v5-retirement-strategy.md)
