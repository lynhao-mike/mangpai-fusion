# T-145 BRIEF · 岁运 4 原子 + `can_control`

- 执行：子代理（T-145）
- 完成时间：2026-10-27
- 决策依据：ADR-007 D3 / D4；任务卡 `tasks/T-145/PROMPT.md`
- 前置：T-142 已完成（`needs_judgment` 原子与 `_edges()` 的 natal 隔离均在），未补做 T-142 的活

## 1. 改动文件

| 文件 | 改动 |
|---|---|
| `engine/claims/condition_ir/atoms.py` | 原子表 44 → 46。实装 3 个空壳岁运原子；新增 `suiyun_arrives`、`can_control`；`liunian_present` 改为从岁运节点反推年份；`build_context` 增 `nodes` 字段（读 `relations.nodes`）；新增 `engine.predicates.types` 的 `GAN_TO_WUXING` / `ZHI_TO_WUXING` / `KE_MAP` 只读导入 |
| `engine/contracts/23-claim-condition-protocol-v1.md` | §4 标题 44 → 46（`v1.2`）；§4.5 岁运 5 → 6 并补实装说明与原文边界；新增 §4.8 力量比较（`can_control`）；§八 Pass 0 计数 44 → 46；§九 版本号与 3 条变更登记 |
| `tests/claims/test_condition_ir_atoms.py` | 原子计数与签名断言 44 → 46；新增 ⑦ 岁运 4 原子（10 条）与 ⑧ `can_control`（6 条）共 16 条新测试 |

**未改动**：`engine/facts/**`、`engine/api/facade.py`、`theory/claims/**`、`theory/_ir/**`、`sources/**`、`pyproject.toml`。无 git 破坏性操作。

## 2. 五个原子的签名与语义

### 2.1 `suiyun_edge(type, at, scope?)`

- 必填 `type`、`at`；可选 `scope ∈ {dayun, liunian, dayun+liunian}`（原契约的 `layer?` 已废弃）。
- 只扫 `scope != "natal"` 的边；`kind == type` 且 `at ∈ members` 即命中，绑定 `edge_id` + `scope`。
- 未提供岁运 → `unknown`，note「未提供大运/流年上下文」。

### 2.2 `sanhe_with_suiyun(zhi_set?)`

- `kind ∈ {sanhe, sanhui}` 且 `completeness == "full"` 且 `scope != natal`。
- `zhi_set` 由必填改可选：给定时要求这些支都被该边包含（字符串 `"亥子丑"` 或列表均可）。
- 完整局由事实层判定，本层不自补第三支。未提供岁运 → `unknown`。

### 2.3 `chong_kai_muku(zhi?, year?)`

- 取 `ctx["muku"]`（按 `zhi` 过滤 `branch`），看其 `addr` 是否被 `scope ∈ {dayun, liunian}` 且 `kind ∈ {chong, xing}` 的边触及。
- `year` 给定时要求该边涉及 `LN{year}.s/b`；该年不在本次上下文里 → `unknown`（不是 false）。
- 盘无该墓库 → `false`（客观事实），note 说明「原局无 X 墓库，无从冲开」。

### 2.4 `suiyun_arrives(at, via?)`

- `at`：原局地址（`"Y.s"`）或单字干支（`"癸"`）；`via ∈ {通禄, 原身}`，缺省按地址层级自动选（天干→通禄，地支→原身）。
- **通禄**：原局天干 G 的禄支 `_LU[G]` 出现在本次岁运的**地支**节点上。
- **原身**：原局地支 Z 的原身干出现在本次岁运的**天干**节点上。原身表 = 禄表逆映射（`YUANSHEN`，由 `chart_facts._LU` 反推，不另造表）：甲↔寅 / 乙↔卯 / 丙戊↔巳 / 丁己↔午 / 庚↔申 / 辛↔酉 / 壬↔亥 / 癸↔子。
- 辰戌丑未无原身 → `false` + note 引 M1-D-058 `falsifiable_by`，**不补造土支原身**。
- `via` 与地址层级不符、或 `at` 定位不到 → `unknown`。未提供岁运 → `unknown`。

### 2.5 `can_control(actor, target)`

- 参数均可写地址（`"M.b"`）或单字干支（`"亥"`）；命中绑定 `actor_addr` / `target_addr`。
- 三值：`True` 制得住 / `False` 制不住 / `None` 力量相当不可裁。**没有第四值**。
- 旺项 = {得令, 多, 合局会局}；衰项 = {失令, 寡, 孤立受克}。
- 判定：`True` ⇔ actor 旺项 ≥2 且 target 旺项 = 0 且 target 衰项 ≥1；`False` ⇔ 镜像；其余 `None`。
- `note` 恒附双方「旺项/衰项」明细（含地址、字数、受克来源），供 Agent 追问而非黑盒。

## 3. 原文依据（行号为当前语料文件实测）

| 论点 | 出处 | 引文 |
|---|---|---|
| 「到位」两法 | `theory/raw/duan/d01-deep-read.md:287`（M1-D-042） | 「如运中出现八字中的字就为八字中的字到了，反客为主了。有两种方式：一为通禄，二为现原身。」 |
| 禄与原身互到 | `theory/raw/duan/d02-theory.md:272-287`（M1-D-058） | `:276`「大运/流年的支是命中天干的禄；或大运/流年的干是命中地支的原身」；`:287` `related_table: 甲↔寅 / 乙↔卯 / 丙戊↔巳 / 丁己↔午 / 庚↔申 / 辛↔酉 / 壬↔亥 / 癸↔子`；`:284` `falsifiable_by: 辰戌丑未无原身，此 4 支不适用本规则` |
| 旺衰对句 | `sources/duan/MinerU_markdown_22.盲派初级命理学_2056045493286002688.md:1762` | 「冲神之旺衰判断，以多则为旺，寡则为衰；以合局会局为旺，以孤立受克为衰；以得令为旺，以失令为衰。冲之力强弱判断，以冲中带克为强，以冲而不克为弱；以大运冲之为强，以太岁冲之为弱。」 |
| 冲开墓库 | 同书 `:1764` | 「运冲则冲破冲坏 岁冲则冲动冲开……动则为发动，开则为开墓。」 |
| 力量相当不可裁 | 同书 `:1812` / `:1824` | `:1812`「戌辰力量相当，互相制不了」；`:1824`「原局金水党和火土党对抗，谁也制不了谁」（另见 `:560`、`:774`、`:830`） |
| 六党对 | 同书 `:426` / `:428` | `:426`「木火可以一党，金水可以一党，水木可以一党；火与燥土可以为一党，金与湿土可以为一党，水与湿土也可以为一党。」`:428` 党→所制（木火制金 / 火与燥土制水 / 金水制火 / 金与湿土制木火 / 水与湿土制燥土或火 / 水木制土） |
| 代码铁律 | `engine/facts/structure_check.py:255`（`strength_judgment`） | 「力量对比不由代码裁决：恒为 needs_judgment，附日主与相关角色的地址及其通根地址。」 |

### 3.1 任务卡引文与实测行号的偏差（须回报中枢）

| 任务卡引 | 实测 | 说明 |
|---|---|---|
| `MinerU_22:1759`（旺衰对句） | `:1762` | 偏差 3 行；语义完全一致 |
| `MinerU_22:1844`（戌辰力量相当） | `:1812` | 偏差 32 行 |
| `MinerU_22:1850`（谁也制不了谁） | `:1824` | 偏差 26 行 |
| `d01-deep-read.md:191-196`（12 种党势） | **不存在**；六党对在 `MinerU_22:426` | 该区间实际内容是「党的主神/中神/辅神」，与党势清单无关 |

代码与契约里的行号已改为实测值；`d01-deep-read.md:287`（到位）与 `d02-theory.md:271-287` 经核实无误。

## 4. 原始输出（自证四条）

环境：`.venv\Scripts\python.exe`，`analyze_facts(pillars=…, gender="坤")`。

### 4.1 标杆盘 A（制得住）：坤造 癸丑 癸亥 辛亥 癸巳

```
ATOMS = 46

can_control(亥,巳) = True  bind={'actor_addr': 'M.b', 'target_addr': 'H.b'}
  制者 水（Y.s/M.s/H.s/M.b/D.b）旺项[得令(亥月)、多(5字)]衰项[无]；
  被制 火（H.b）旺项[无]衰项[失令(亥月)、寡(1字)、受克(M.b(水)克火)] → 制得住（MinerU_22:1762 旺衰对句）

can_control(巳,亥) = False
  制者 火（H.b）旺项[无]衰项[失令(亥月)、寡(1字)、受克(M.b(水)克火)]；
  被制 水（Y.s/M.s/H.s/M.b/D.b）旺项[得令(亥月)、多(5字)]衰项[无] → 制不住（MinerU_22:1762 旺衰对句）
```

判定理由：水三透（癸癸癸）+ 双亥，显性 5 字 ≥3 且亥月水得令，两项达 `STRONG_MIN`；
火仅巳一支，亥月失令、孤寡、被双亥冲且水克火（「冲中带克为强」，`:1762`），旺项 0、衰项 3。
即段派「伤官亥冲巳，冲去夫星忌神」的力量前提成立。反向（火制水）落 `False`，方向不乱。

### 4.2 标杆盘 B（制不住）：壬子 乙巳 庚子 壬午

```
can_control(子,巳) = None
  制者 水（Y.s/H.s/Y.b/D.b）旺项[多(4字)]衰项[失令(巳月)]；
  被制 火（M.b/H.b）旺项[得令(巳月)]衰项[受克(Y.b(水)克火)] → 力量相当，不可裁（MinerU_22:1812/:1824）
can_control(子,午) = None   （同上明细）
can_control(Y.b,M.b) = None （同上明细）
```

判定理由：水以「多(4字)」得 1 旺项但失令；火以「得令(巳月)」得 1 旺项但受子冲。
双方各 1 旺项 → 不满足 `True`（actor 需 ≥2 且 target 旺项 0）也不满足 `False`，判 `unknown`，
与原文「水火力量相当，制不住夫星」一致。**未调任何阈值去凑**：A/B 的差异来自结构本身
（A 是 2 旺项 vs 0，B 是 1 旺项 vs 1），不是阈值选边。

### 4.3 岁运原子（同一盘，`liunian_year=2027` = 丁未，`dayun_index=1` = 甲子）

不传岁运：

```
suiyun_edge          -> None | 未提供大运/流年上下文
sanhe_with_suiyun    -> None | 未提供大运/流年上下文
chong_kai_muku       -> None | 未提供大运/流年上下文
suiyun_arrives       -> None | 未提供大运/流年上下文
liunian_present      -> False
```

传 2027 + 甲子运：

```
suiyun_edge{type:chong, at:Y.b}        -> True  bind={'edge_id': 'e024', 'scope': 'liunian'} | chong 边 e024（liunian）
suiyun_edge{type:liuhe, at:Y.b}        -> True  bind={'edge_id': 'e022', 'scope': 'dayun'}   | liuhe 边 e022（dayun）
sanhe_with_suiyun{}                    -> True  bind={'edge_id': 'e036', 'scope': 'dayun'}   | 亥子丑 成局（dayun）边 e036
chong_kai_muku{}                       -> True  bind={'edge_id': 'e024', 'addr': 'Y.b'}       | 丑库（Y.b）被 chong 边 e024（liunian）冲开
suiyun_arrives{at:Y.s}                 -> True  bind={'addr': 'Y.s', 'sui_addr': 'DY1.b'}     | 原局天干癸（Y.s）的禄子落到 DY1.b
suiyun_arrives{at:H.b}                 -> False | 原局地支巳原身丙戊，本次岁运天干未见
suiyun_arrives{at:Y.b}                 -> False | 丑为墓库支，无原身（D-02 M1-D-058：辰戌丑未无原身）
liunian_present{year:2027}             -> True
```

### 4.4 原局原子隔离仍在（T-142 成果未破坏）

```
chong_at(Y.b) natal       = False      # 冲丑只有岁运边 e024
group_complete(sanhui)    = False      # 完整三会只在岁运层
edge(sanhui) 默认         = e019       # 命中的是 natal 半会
edge(sanhui, scope=dayun) = e023       # 显式查岁运边才拿到
```

## 5. 工程取值 vs 原文数值（区分清单）

| 取值 | 位置 | 性质 | 说明 |
|---|---|---|---|
| `DUO_MIN = 3`（同五行显性字数 ≥3 为「多」） | `atoms.py` 常量 | **工程取值** | 原文只说「以多则为旺，寡则为衰」（`:1762`），未给数 |
| `GUA_MAX = 1`（≤1 为「寡」） | 同上 | **工程取值** | 同上 |
| `STRONG_MIN = 2`（判真/假所需旺项数） | 同上 | **工程取值**（设计值来自 ADR-007 D4） | 原文无此门槛，是「极端清晰盘才判」的实现手段 |
| 「显性字数」= 天干数 + 地支本气数 | `_side_profile` | **工程取值** | 中气/余气不计入「多」，避免藏干把字面撑大；取自 facts 的 `wuxing_layered.stems + main_qi` |
| 「受克」边种 = {chong, ke, stem_chong, chuan} | `SIDE_KE_KINDS` | **工程取值** | 原文只说「孤立受克」（`:1762`）与「冲中带克为强」，未穷举边种 |
| 「成局」= 原局 `sanhe/sanhui` 且 `completeness == full` | `_side_ju` | 原文有据（「以合局会局为旺」）+ 工程限定（只认原局、只认完整局） | 半局/拱局不计 |
| 得令 = `wuxing_layered[wx].month_main_qi` | `_side_profile` | 原文有据（「以得令为旺，以失令为衰」）+ 事实层口径（月支**本气**） | 未用「人元司令」细分 |
| 墓库冲开边种 = {chong, xing}、scope ∈ {dayun, liunian} | `chong_kai_muku` | 原文有据（「开则为开墓」，`:1764`）+ 任务卡限定 | `dayun+liunian` scope 的边不计入（见 §6） |

上述恒定值均集中在 `atoms.py` 常量区，改动必须同步本清单。

## 6. 未完成与风险

1. **「遁藏透干」（M1-D-059）未实现**。`suiyun_arrives` 只答 M1-D-042 的两法（通禄 / 现原身）。
   更宽的口径「原局地支任一藏干透于运年天干」（`theory/raw/duan/d02-theory.md:294-303`）会让
   寅、申等支的中气也算到位（如寅透丙戊），与 `原身` 表不一致；原文另立条目且有独立
   `falsifiable_by`，**未擅自并入**，留待中枢裁定是否作为第三个 `via`。
2. **六党对（木火/金水/水木/火与燥土/金与湿土/水与湿土）未做跨五行聚合**，党势只以「同五行字数
   入『多』」体现。风险点：若按 `MinerU_22:426/:428` 把金并入水党、燥土并入火党，标杆盘 B 的
   水党会显著大于火党，可能把原文「力量相当」判成「制得住」——与原文冲突。**这是一个真实的
   口径分歧，须中枢裁决**，不要为了让 `can_control` 更「敢判」而放宽。
3. **`chong_kai_muku` 不计 `scope == "dayun+liunian"` 的边**（按任务卡限定）。若出现「大运地支
   与流年地支互冲且同时触及墓库」的三元边，当前会漏；实测该盘无此类边（`e035` 是 chuan）。
4. **`dayun_present` 与「有大运上下文」不是同一问题**：前者读 `chart.cycles.dayun`（只要出生
   数据可排就为真），后者以是否真的建出 DY 边为准（需 `dayun_index`）。已按契约保留原语义，
   `suiyun_*` 一律用后者。**下游别再拿 `dayun_present` 判断「能不能算岁运」。**
5. **`can_control` 只做二元对抗**：`actor`/`target` 各解析为「同五行的全部字」，不区分具体是
   哪一柱、哪一字在制（如 A 盘的 M.b 亥 vs D.b 亥）。位置/远近/夹冲的差异（原文 `:1764`
   「近冲则克破 隔冲则伤损」）未纳入，属下一层。
6. 岁运原子的 `at` 仍只认**原局地址**与**单字干支**；不认 `DY1.b` / `LN2027.b` 这类节点地址作
   为 `at`（`suiyun_edge` 的 `at` 就是原局地址，节点在 `members` 的对侧）。

## 7. 下游须知

- 原子表 **46 个**（v1.2）。`engine/claims/condition_ir/__init__.py:6` 的模块 docstring 与
  `docs/analysis-pipeline-explained.md:401` 仍写「42 个」——**不在本卡 File Scope，未改**，请中枢
  一并修掉。
- `build_context` 新增 `"nodes"` 键（来自 `relations.nodes`）。裁掉 `nodes` 的旧快照仍可用
  （`_suiyun_nodes` 会回退到从边 `members`/`chars` 对齐反推），但若连 `chars` 也裁掉，
  `suiyun_arrives` 会因无法定位干支而给 `unknown`。
- `liunian_present` 已修：旧实现读 `chart.cycles.liunian`（事实层恒为 `null`），因此永远返回
  false。现改为从 `LN{year}` 节点反推。**这是行为变更**，依赖「有流年必为 true」的调用方需复看。
- 岁运原子的三值语义：未提供上下文一律 `unknown`（`state = needs_fact`），**不要**在编译层
  把它们当 false 处理，否则又会退化成「过滤掉所有需要追问的盘」。

## 8. 验收命令

```text
.venv\Scripts\python.exe -m pytest -q
→ 1011 passed, 1 skipped, 1 warning in 99.85s   EXIT=0   （本卡改动完成时）
→ 1040 passed, 1 skipped, 1 warning in 94.48s   EXIT=0   （并发会话 T-143 补 29 条后复跑）
  （skip 为 AGENTS.md 记录的 tests/tools/test_bundle_pii.py，T-114 过渡措施，非本卡引入）

.venv\Scripts\python.exe -m tools.verify_baseline
→ {"pytest_passed": 1040, "pytest_failed": 0, "pytest_rc": 0,
   "audit_errors": 0, "audit_rc": 0, "relations_ok": true, "relations_rc": 0,
   "zuogong_charts": 477, "zuogong_day_branch": 346, "zuogong_rc": 0}   EXIT=0

.venv\Scripts\python.exe -m tools.verify_baseline --compare
→ 【基线未退步】   EXIT=0

.venv\Scripts\python.exe -m pytest tests/claims/test_condition_ir_atoms.py -q -o addopts="-ra --tb=short"
→ 52 passed   EXIT=0
```

> ⚠ `--compare` 必须**前台**跑。两次以后台任务启动时，内部 pytest 子进程返回
> `pytest_rc=1 / pytest_passed=0`（收集阶段失败，无 `N passed` 汇总行），`regressions()` 据此
> 误报「pytest 通过数 220 → 0」。同一命令前台复跑两次均 1040 passed / 【基线未退步】。
> 并发会话 T-143 正在高频改写 `theory/claims/conditions-v2/pilot-20.yaml` 并跑 pytest，
> 判定为该窗口的收集竞态，与本卡无关（本卡只动 `atoms.py` / 契约 23 / 本卡测试三个文件）。

## 9. 工作区并发提示（非本卡改动）

`git status` 里另有 4 个本卡**未触碰**的文件处于 modified / untracked，时间戳晚于本卡编辑
（21:56、22:01），来自并发会话 **T-143（断语层：pilot-20 编译 + invalidators）**：

```
 M META/claim-condition-corpus-v1.json
 M META/claim-condition-pilot-v1.json
 M META/claim-condition-pilot-v1.md
 M theory/claims/conditions-v2/pilot-20.yaml
?? tests/claims/test_pilot20_conditions.py
```

其中 `META/claim-condition-pilot-v1.md` 的「原子表规模」已记为 46、未知率由 0.0 变为 0.2，
说明该并行流程是在本卡改动之后跑的。**本卡未编辑这些文件**，提交时请勿混入。
