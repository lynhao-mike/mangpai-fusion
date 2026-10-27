# T-132 · BRIEF（墓库扫描扩全部十神）

- 状态：❌ **前提不成立，已撤销**（未做任何业务代码改动）
- 完成日期：2026-10-27
- 执行者：子代理（Worker）
- 结论一句话：**事实层的墓库扫描本来就是全十神的**；「只扫财官」的是另一条遗留链 `engine/energy/zuogong.py`，而 `ru_mu` 根本不读它。M3-R-166 的 `fire=0` 与墓库扫描范围无关。

---

## 0. 明确声明

**任务卡前提不成立，未做代码改动。**

- 未改 `engine/facts/` 下任何文件
- 未改 `engine/energy/zuogong.py`
- 未改 `theory/claims/conditions-v2/pilot-20.yaml`（该条断语的 `compile_note` 由中枢亲自更正）
- 未改 `tests/`、未改 `pyproject.toml`、未动 `theory/_ir/` 与 `sources/`
- 未跑 pytest / verify_baseline（无代码改动，门禁不受影响）

任务卡 §1「墓库扫描当前只覆盖财、官两类十神」与 §2.1「读清它现在为什么只出财官」所预设的事实不存在，因此没有可执行的「扩到全部十神」改动，也没有可断言的「扩前 0 → 扩后非 0」变化。

---

## 1. 定位：墓库事实有两条互不相交的链

| # | 链路 | 入口函数 | 扫描粒度 | 是否被 `ru_mu` 读 | 是否只出财官 |
|---|---|---|---|---|---|
| A | **事实层**（M3-R-166 实际走这条） | `engine/facts/relation_graph.py::_muku`（L341-413），经 `engine/api/facade.py::analyze_facts` → `facts["relations"]["muku"]` → `atoms.py::build_context` → `atoms.py::ru_mu`（L356-368） | **按五行**：`_MU_BRANCH = {"辰":"水","戌":"火","丑":"金","未":"木"}`，五行为该库的所有原局字（天干/地支/藏干）都进候选，再按任派五条细则给 `rule_hits` / `excluded` | ✅ 是 | ❌ **否，全十神** |
| B | **遗留 v5 能量链** | `engine/energy/zuogong.py::detect_mu_paths`（L472-515） | **按用神**：`_yongshen_in_zhi_canggan()`，用神定义即 `role in ("财","官杀")` | ❌ 否 | ✅ 是（文件自述「墓 = 简化实现（只检测财官入辰戌丑未）」L27） |

两条链**没有任何 import 关系**：`engine/facts/` 全目录不含 `engine.energy` 引用（grep `engine\.energy|from engine import energy` → 0 命中）。

链路 B 的调用点（已逐一核实）：

- `engine/energy/zuogong.py:535` — `paths.extend(detect_mu_paths(bazi, day_master))`（在 `evaluate_zuogong` 内）
- `engine/energy/evaluator.py:220` — `zuogong_paths = evaluate_zuogong(bazi, tiyong)`
- `engine/v5/duan_runner.py:60` — `paths = evaluate_zuogong(bazi, tiyong)`

**即：财官限定只存在于链路 B，它不在 `ru_mu` 读取的链路 A 上。** 任务卡把 B 的自述当成了 A 的行为。

---

## 2. 复现证据

### 2.1 中枢独立复算（481 盘）——来源：中枢，非本人实测

> 以下数字由中枢亲自复算提供，本人未复跑该口径，**标注「中枢复算」**，不得当作我的实测结论引用。

- `relations.muku` 候选共 **818 条**，十神分布覆盖全部十类：食神 54 / 伤官 73 / 比肩 109 / 正印 51 / 偏财 75 / 七杀 66 / 正官 56 / 劫财 53 / 正财 84 / 偏印 65 / 日主 86。**不是「只扫财官」。**
- `ru_mu(食神)` 为真 **41 盘**（与我方 probe 一致），全部十神都有命中。
- `compile_note` 里「481 张盘命中 0」是**错误陈述**。
- M3-R-166：`compile_state: partial` → `compile_claim` 返回 `partial` → 两个报告工具直接跳过 → `fire_rate` 里没有这一条。

> 口径提示：中枢的十神分布把入墓字按其在盘中的十神归类（含日主），单字可计入多类；与我方 probe 的计数口径不同，两组数字**不可逐项对比**，但结论一致——十类全有覆盖。

### 2.2 我方 probe 原始输出

**probe 1 — 墓库候选的十神覆盖 + `ru_mu` 逐神命中（481 盘）**

命令：
```
.venv\Scripts\python.exe <probe1>.py
```

原始输出（逐字）：
```
charts=481 muku_empty_charts=98 muku_candidates_total=818
candidate chars 覆盖的十神计数：
  比肩: 88
  劫财: 62
  食神: 65
  伤官: 92
  偏财: 88
  正财: 90
  七杀: 76
  正官: 64
  偏印: 71
  正印: 65
ru_mu(star=g) == True 的盘数：
  比肩: 63
  劫财: 42
  食神: 41
  伤官: 45
  偏财: 54
  正财: 61
  七杀: 45
  正官: 44
  偏印: 43
  正印: 34
M3-R-166 preconditions True 盘数 = 41  Unknown = 0
```

要点：
- `muku_candidates_total=818`，与中枢的 818 条一致。
- 十类十神**全部**出现在墓库候选里，`ru_mu(食神)` 在 481 盘里为真 41 盘——**「ru_mu(食神) 永远为假」不成立**。
- 最后一行说明：M3-R-166 的 `preconditions`（`ru_mu(star=食神)`）本身就能成立 41 次；它没有开火，不是事实层不给事实。

**probe 2 — facts 层「墓用」做功候选的十神分布（481 盘）**

原始输出（逐字）：
```
charts=481 charts_with_墓用=226
每种做功模式候选数： {'化用': 450, '制用': 4210, '合用': 898, '生泄用': 1462, '墓用': 507}
墓用候选的十神分布（members 两个端点都计入）：
  比肩: 85
  劫财: 59
  食神: 164
  伤官: 150
  偏财: 111
  正财: 95
  七杀: 63
  正官: 84
  偏印: 92
  正印: 63
```

要点：`engine/facts/structure_check.py::build_duan_zuogong_candidates` 的墓用分支（L498-506）同样已经是全十神，`_crosses(ty[c.addr], ty[m.addr])` 的体用门并不把食伤/比劫/印挡在外面。

**复现片段（probe 1 的最小版，可直接粘贴运行）**

```python
import pathlib, re, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = pathlib.Path(r"E:\Git hub\mangpai-fusion"); sys.path.insert(0, str(ROOT))
from engine.api import analyze_facts, to_jsonable
from engine.claims.condition_ir import build_context
from engine.claims.condition_ir.atoms import ru_mu

CASE_RE = re.compile(r"^(C-\d{4}-[A-Za-z0-9]+)-(乾|坤)-((?:[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]){4})$")
GODS = ("比肩","劫财","食神","伤官","偏财","正财","七杀","正官","偏印","正印")
hits, n = {g: 0 for g in GODS}, 0
for p in sorted((ROOT / "cases").iterdir()):
    m = CASE_RE.match(p.name)
    if not m:
        continue
    pillars = [m.group(3)[i:i+2] for i in range(0, 8, 2)]
    ctx = build_context(to_jsonable(analyze_facts(pillars=pillars, gender=m.group(2))))
    n += 1
    for g in GODS:
        if ru_mu(ctx, {"star": g}).value is True:
            hits[g] += 1
print(f"charts={n}", hits)
```

### 2.3 `fire=0` 的真实成因（代码位置）

**成因一：`compile_state: partial` 使该断语根本不进求值。**

`engine/claims/condition_ir/ir.py::compile_claim`（L263-274）：

```python
    if declared == "partial":
        return {"claim_id": claim.get("id"), "status": "partial",
                "reason": claim.get("compile_note", "")}
```

而两个报告工具都只取 `compiled`：

- `tools/claim_condition_report.py:96` — `if r["status"] == "compiled": compiled.append(c)`
- `tools/claim_condition_corpus.py:55` — `if compile_claim(c)["status"] == "compiled"`

实证（现有产物 `META/claim-condition-pilot-v1.json` 的 `metrics`）：

```
"compile_states": {"compiled": 8, "needs_human": 5, "uncompilable": 2, "partial": 4, "reference_only": 1}
"compiled_claims": ["G-SP-165","G-SP-293","G-SP-071","G-SP-130","M1-D-298","M2-Y-251","M2-Y-014","M3-R-013"]
"fire_rate": {"G-SP-165":0.2,"G-SP-293":0.45,"G-SP-071":0.1,"G-SP-130":0.35,"M1-D-298":0.0,"M2-Y-251":0.4,"M2-Y-014":0.35,"M3-R-013":0.1}
```

`M3-R-166` **不在 `compiled_claims`，也不在 `fire_rate` 的键里**——它不是「算出 0」，是「根本没被求值」。`META/claim-condition-corpus-v1.json` 同理，8 条全量 481 盘，无 M3-R-166。

**成因二：即使改成 `compiled`，`requires_pair` 也让它永远到不了 `candidate`。**

`engine/claims/condition_ir/ir.py::evaluate_claim`（L167-179）：

```python
    if dep == "requires_pair":
        pair = (spec.get("pair_with") or [None])[0]
        cited = (ctx.get("cited") or {}).get(pair)
        if cited is None:
            out["framework"]["verdict"] = "unknown"
            out["state"] = "evidence_only"
            out["reason"] = f"配对命题 {pair} 未裁决"
            return out
```

M3-R-166 的 `pair_with: [M2-Y-017]`，而 M2-Y-017 自身是 `needs_human`（缺「禄」原子，见 `pilot-20.yaml` 的 `compile_note`），且 `ctx["cited"]` 在两个报告工具里始终是 `{}`（`atoms.py::build_context` 里写死 `"cited": {}`）。所以 `state` 只会是 `evidence_only`，而「开火」的判定是 `state == "candidate"`（`claim_condition_report.py:113`）——**换 `compile_state` 也救不回来**。

---

## 3. 「某十神是否入墓」的规则依据（原文，`sources/ren/…地支四墓库的使用方法…md`）

现有代码 `engine/facts/relation_graph.py::_muku` 逐条锚定任付红原文五条细则（常量 `REF_REN_MUKU`），行号与实际文件一致（已逐条核对）：

| 细则 | 原文（节录） | 原文行号 | 代码位置 | 代码效果 |
|---|---|---|---|---|
| （一） | 「寅、申、巳、亥见各自的墓库为入墓库，即寅见未、申见丑、巳见戍、亥见辰，见则入墓库。」 | :29 | `_muku` → `_rule("一","入墓",29,…)` | `四生支` 一律 `入墓`，不看字数 |
| （二） | 「子、午、卯、酉见各自墓一般不作入墓论……一般当拱局看，只有其极弱的情况下见墓才入。」 | :61 | `_rule("二","一般作拱局",61,…)` + `requires_judgment` | `四正支` 标 `一般作拱局`，是否入墓交调用方 |
| （三） | 「多而入墓库，即无论天干或地支，合在一起有两个或两个以上者见各自墓库则入……」 | :73 | `_rule("三","入墓",73,…)` | 同五行 `count >= 2` → `入墓`，不作拱看 |
| （四） | 「天干坐墓不以入墓论，如丙戍一柱，乙未一柱，丙乙不以入墓看。」 | :107 | `_rule("四","不论入墓",107,…)`，置 `excluded=True` | 同柱天干 `excluded`，`ru_mu` 跳过 |
| （五） | 「地支土之墓库比较特别，辰为土墓也为水墓，丑入辰墓未也入辰墓，但当丑未辰都出现时，丑未因为相冲的关系，不论入辰墓。」 | :111 | `_rule("五","入墓",111,…)` / `_rule("五","不论入墓",111,…)` | 仅 `tu_jigong` 口径下生效（`duan_split_earth` / `fire_earth`），丑未辰齐见则排除 |

**关键点：五条细则通篇只按五行与干支位置论入墓，全文没有出现任何十神限定，更没有「只有财官才论入墓」的说法。** 因此事实层按五行扫描、再把命中字映射回十神（`ru_mu` 用 `_chars_of_god` 做这一步），本来就是对原文的忠实实现；「扩到全部十神」在链路 A 上没有对应原文依据，也没有对应代码缺口。

---

## 4. 改动文件

**无。** 本轮只有两份文档产出：

| 文件 | 动作 |
|---|---|
| `tasks/T-132/BRIEF.md` | 新建（本文件） |
| `tasks/T-132/STATUS.md` | 新建 / 更新 |

两个临时 probe 脚本写在系统临时目录（`%TEMP%\t132_probe.py`、`%TEMP%\t132_probe2.py`），**不在仓库内**，未提交；其最小可复现版本已内嵌到本文件 §2.2。

---

## 5. 未完成与风险

1. **未完成（已撤销）**：任务卡要求的「扩到全部十神」代码改动与「扩前 0 → 扩后非 0」测试**均未执行**，因为前提不成立、且中枢已撤回授权。
2. ~~`pilot-20.yaml` 的 `compile_note` 仍是错误陈述~~ → **已由中枢于 2026-10-27 亲自更正**（`git diff` 可见：新 note 记录了本轮复算结论与真实双重成因，并指明后续应补 M2-Y-017 而非扩墓库）。本人未改该文件，符合「同一文件不双写」的分工。同时中枢已在 `tasks/T-132/PROMPT.md` 顶部加 ⛔ 裁定横幅，本卡保留仅作追溯。
3. **风险：`META/claim-condition-pilot-v1.json` / `-v1.md` 与 `META/claim-condition-corpus-v1.json` 仍是旧产物**，其中嵌着那句已被证伪的旧 `compile_note`。yaml 已更正，但需重跑 `python -m tools.claim_condition_report` 与 `python -m tools.claim_condition_corpus` 才会同步。
4. **风险：M3-R-166 目前是「双重不可达」**——第一层是 `partial` 不进求值，第二层是 `requires_pair` 让其最多到 `evidence_only`。只解开第一层不会让它开火；要开火还须等 `M2-Y-017` 的「禄」原子落地并进入 `ctx["cited"]`（当前 `build_context` 写死 `"cited": {}`）。
5. **风险：易误改点**。`engine/energy/zuogong.py` 的财官限定看起来像「同一个 bug」，但它是 v5 遗留链，与事实层无 import 关系；在此处动手不会改变 M3-R-166 的任何观测值，只会造成假的「修复」。

---

## 6. 下游须知

1. **别再按「facts 只扫财官」推断任何断语失效。** 判断某条 `ru_mu` 断语为什么不开火，先看 `compile_state`，再看 `framework_dependency`，最后才看事实层。
2. **两条墓库链要分开说**：
   - 断语原子 `ru_mu` / `muku_present` / `muku_open` / `zuogong(kind=墓用)` 走 `engine/facts/relation_graph.py::_muku`（全十神、任派五条细则、带 `source_ref` 锚点）。
   - `engine/energy/zuogong.py::detect_mu_paths` 只服务 v5 事件/报告链（`engine/v5/duan_runner.py`、`engine/energy/evaluator.py`），口径为「库藏用神（财/官杀）+ 刑冲开库」，**不是**断语原子的事实来源。
3. **想把 M3-R-166 变成可求值**，需要的是：① 中枢更正 `compile_note` 并调整 `compile_state`（**更正已由中枢完成**）；② `M2-Y-017` 的「禄」原子 + `ctx["cited"]` 填充机制 —— 该项已由中枢拆为 **T-135**（补「禄」原子），是 M3-R-166 的真正解锁路径。二者都不在 `engine/facts/`。
4. **`_muku` 的已知覆盖边界**（不是 bug，是待定口径）：`土支`（辰戌丑未）作为「入墓方」只在 `tu_jigong = duan_split_earth / fire_earth` 口径下产生候选（细则五），默认口径下不产生；`四正支` 只标「一般作拱局」并写 `requires_judgment`，不硬判入墓。这两处若要动，须先有原文或中枢口径裁决，不得自定阈值。
