# 上层故障只读盘点 v1（T-131 · A2 前置）

- 生成：2026-10-27（子代理执行 T-131）
- 依据：`tasks/T-131/PROMPT.md`、ADR-001（引擎=事实+候选）
- 性质：**只读盘点，未修任何代码**。本文件是本任务唯一新增文件。
- 解释器：`.venv\Scripts\python.exe`，所有命令均在仓库根 `E:\Git hub\mangpai-fusion` 下执行。

## 0. 只读基线（先证明没动过代码）

```powershell
.venv\Scripts\python.exe -m pytest -q
```

```
220 passed, 1 skipped in 11.63s
```

```powershell
git status --porcelain
```

```
 M docs/adr/README.md
 M tasks/T-128/PROMPT.md
?? docs/adr/ADR-006-v5-retirement-strategy.md
?? tasks/T-130/
?? tasks/T-131/
?? tasks/T-132/
?? tasks/T-133/
?? tasks/T-134/
```

> 以上 `docs/adr/README.md`、`tasks/T-128/PROMPT.md`、`ADR-006` 与 `tasks/T-13x/` **均非本任务改动**，是同一时间其他子代理/中枢的产出。本任务未改任何 `.py`、未改任何测试、未新建除本文件外的文件。

### ⚠️ 并发干扰声明

盘点过程中检测到同仓库其他子代理在**实时写文件**（本任务未参与）：

```powershell
git status --porcelain tools/ engine/ tests/
```

```
?? tools/case_time_basis_audit.py
```

```powershell
Get-Item tools\case_time_basis_audit.py | Select-Object Name,LastWriteTime,Length
```

```
Name                      LastWriteTime          Length
----                      -------------          ------
case_time_basis_audit.py  2026/10/27 10:01:09     16525
```

该文件在盘点开始（约 09:56）时尚不存在，10:01 出现，导致 `except Exception` 计数从 **110** 变为 **111**。**本报告所有数字均钉在「110」这个快照上**，复现命令现在跑出来会是 111（多出的 1 处即 `tools/case_time_basis_audit.py:378` 的 `except Exception: pass`，属并发新增，不在本清单评级范围内）。

同时期间被其他代理改动的还有：`theory/claims/conditions-v2/pilot-20.yaml`(M)、`META/case-time-basis-v1.json`(新)、`theory/claims/drafts/`(新)、`tasks/T-135/`(新)。

## 1. 总表

| 项 | 数 |
|---|---|
| 清单条数（故障项） | **19** |
| 其中 P0 | **9** |
| 其中 P1 | **10** |
| 反证记录（非故障，用于纠正任务卡假设） | 1（A-07） |
| `except Exception` 在 `engine/`+`tools/`+`tests/` 总数 | **110**（engine 46 / tools 54 / tests 10） |
| 其中「静默吞错」（`pass` / `continue` / `return None`，无任何日志） | **20**（SILENT_PASS 7 + SILENT_CONTINUE 5 + RETURN_NONE 8） |
| 「只断言不抛异常」的测试 | **20**（NO_VERIFY 14 + ONLY_NOT_NONE 6，全 `tests/` 口径） |
| 其中落在 `pyproject.toml` `testpaths` 门禁内的 | **2** |

### 关于任务卡三个「已知嫌疑」的裁决

| 任务卡假设 | 实跑结论 |
|---|---|
| `tiyong` / `binzhu` 序列化成 `None` | **不成立**。`duan_zuogong.tiyong` 实跑是完整 8 字字典（A-07）；`binzhu` 从不出现 `null`。真实故障是**字段被整键删除**（A-01），不是置 `None`。 |
| 冲/刑/穿边 `actor` 为 `None` | **成立，且比描述更严重**：`actor` 不是 `None`，而是**键根本不存在**，调用方 `cand["actor"]` 会 `KeyError`（A-02/A-03/A-04）。 |
| `engine/v5` 与现行实现双轨 | **成立，但形态与预期不同**。ADR-006 已用 import 闸门管住 v5；真正的活体冲突是 `engine/energy` 与 `engine/facts` **两套体用表**，两者都在「现行」侧，闸门管不到（B-01）。 |

## 2. A 组 · 序列化层：字段被静默删除

### A-01 | `engine/api/facade.py:93-94` | 做功候选的 `tiyong` / `binzhu` / `distance` 被 keep 白名单整键删除 | **P0** | 段派做功（体用、宾主、层距）

**现象**：`ZuogongCandidate` 在 `engine/facts/structure_check.py:64-77` 声明了 12 个字段，但 `_compact_zuogong` 只保留 `("mode","relation_kind","edge_id","members","ten_gods","actor")` 六个。`tiyong`、`binzhu`、`distance` 从不出现在 CLI 输出里，也不会是 `null`——**键直接消失**。即使补进白名单，`_compact`（`facade.py:67` 的 `if compact in (None, [], {}): continue`）还会再删一次 `None`。

**复现命令**

```powershell
.venv\Scripts\python.exe -m engine.cli all --pillars "庚申 戊寅 壬子 辛丑" --gender 乾 --json | .venv\Scripts\python.exe -c "import sys,json;d=json.load(sys.stdin);print(sorted(d['duan_zuogong']['candidates'][0].keys()))"
```

**实测输出**

```
['actor', 'edge_id', 'members', 'mode', 'relation_kind', 'ten_gods']
```

**影响断语**：段派「谁做谁」「体用相交」「宾主方位」「层距远近」只能靠 Agent 从 `members` 反推。但 `binzhu` 的 `direction`（正向/反向/同在主位/同在宾位/需判断）**无法从 `members` 反推**——它依赖 `_ti_yong_ends`（`structure_check.py:385`）的双属补位规则。任何「用神在宾位所以费力」这类断语目前没有事实支撑。

---

### A-02 | `engine/facts/structure_check.py:476`（+ `facade.py:94`） | 冲边产生的候选 `actor` 为 `None` 且键被删 | **P0** | 做功方向（主/客、谁克谁）

**现象**：`actor = e.members[0] if e.kind == "ke" else None`。`_ZHI_KINDS` 含 `chong`/`xing`/`chuan`/`stem_chong`，但它们一律落到 `else None`。`facade.py:94` 的 `if cand.get(k) not in (None, [], ())` 又把 `None` 的键删掉，于是「没有 actor」和「字段没算」在输出上不可区分。

**复现命令**

```powershell
.venv\Scripts\python.exe -m engine.cli all --pillars "庚申 戊寅 壬子 辛丑" --gender 乾 --json | .venv\Scripts\python.exe -c "import sys,json;d=json.load(sys.stdin);[print(c['mode'],c['relation_kind'],'actor' in c,c.get('actor')) for c in d['duan_zuogong']['candidates'] if c['relation_kind'] in ('chong','xing','ke','sheng')]"
```

**实测输出**

```
化用 sheng True M.s
制用 ke True M.s
化用 sheng True M.s
制用 chong False None
制用 xing False None
```

对比可见：`ke`/`sheng` 有 actor，`chong` 没有。

**影响断语**：冲是「体用相交」里最常见的做功方式之一。没有 actor，只能说「这里有个冲」，说不出「谁冲谁、谁被迫动」——而盲派断语恰恰靠方向定主客。

---

### A-03 | `engine/facts/structure_check.py:476` | 刑边候选同样 `actor=None` | **P0** | 刑的做功方向

**复现命令**

```powershell
.venv\Scripts\python.exe -m engine.cli all --pillars "庚申 戊寅 壬子 辛丑" --gender 乾 --json | .venv\Scripts\python.exe -c "import sys,json;d=json.load(sys.stdin);[print(c['mode'],c['relation_kind'],'actor' in c,c.get('actor')) for c in d['duan_zuogong']['candidates'] if c['relation_kind']=='xing']"
```

**实测输出**

```
制用 xing False None
```

**影响断语**：同 A-02，刑的「谁刑谁」不可判定。

---

### A-04 | `engine/facts/structure_check.py:476` | 穿边候选同样 `actor=None` | **P0** | 穿（害）的做功方向

**复现命令**（换一张含穿的盘）

```powershell
.venv\Scripts\python.exe -m engine.cli all --pillars "甲子 辛未 丙寅 戊戌" --gender 坤 --json | .venv\Scripts\python.exe -c "import sys,json;d=json.load(sys.stdin);[print(c['mode'],c['relation_kind'],'actor' in c,c.get('actor')) for c in d['duan_zuogong']['candidates'] if c['relation_kind'] in ('chuan','xing')]"
```

**实测输出**

```
制用 chuan False None
制用 xing False None
```

**影响断语**：穿是「暗中受损」的主要依据，缺 actor 就无法指认受损方。

---

### A-05 | `engine/facts/structure_check.py:482` | 合类候选 `actor` 恒为 `None`（合无方向） | **P1** | 合化/合绊的主从

**现象**：`emit("合用", e.kind, e.id, members, None, ...)` 写死 `None`。这可能是**有意设计**（合本就无向），但序列化层把 `None` 删键，导致下游无法区分「合没有方向」与「actor 没算」。

**复现命令**

```powershell
.venv\Scripts\python.exe -m engine.cli all --pillars "庚申 戊寅 壬子 辛丑" --gender 乾 --json | .venv\Scripts\python.exe -c "import sys,json;d=json.load(sys.stdin);[print(c['mode'],c['relation_kind'],c['edge_id'],'actor' in c) for c in d['duan_zuogong']['candidates'] if c['mode']=='合用']"
```

**实测输出**

```
合用 zhi_anhe e010 False
合用 liuhe e011 False
```

**影响断语**：合绊断语目前只能给出「有合」，不能给出合的方向语义。

---

### A-06 | `engine/facts/structure_check.py:363` | 破（`po`）边永远不产生做功候选 | **P1** | 破的做功

**现象**：`_ZHI_KINDS = {"ke","stem_chong","chong","xing","chuan"}` —— **没有 `po`**。而 `engine/facts/relation_graph.py:234` 是会建 `po` 边的（`_CHUAN_PO_KINDS` 也含它）。于是破边被 `if e.kind in _ZHI_KINDS` 与 `elif e.kind in _HE_KINDS` 双双漏掉，**静默丢弃**。

**复现命令**

```powershell
.venv\Scripts\python.exe -m engine.cli all --pillars "甲子 辛未 丙寅 戊戌" --gender 坤 --json | .venv\Scripts\python.exe -c "import sys,json;d=json.load(sys.stdin);po=[e for e in d['relations']['edges'] if e['kind']=='po'];print('po edges:',[(e['id'],e['chars']) for e in po]);ids={c.get('edge_id') for c in d['duan_zuogong']['candidates']};print('po in candidates?',[(e['id'],e['id'] in ids) for e in po]);print('kinds:',sorted({c['relation_kind'] for c in d['duan_zuogong']['candidates']}))"
```

**实测输出**

```
po edges: [('e009', ['未', '戌'])]
po edge in candidates? [('e009', False)]
kinds: ['canggan_ke', 'chuan', 'ke', 'muku', 'sheng', 'sheng(main_qi)', 'wuhe', 'xing']
```

**影响断语**：破是「破损、反复、耗损」类断语的边。现在这条边**排盘有、做功候选无**——事实层和候选层不一致，Agent 会漏断。

---

### A-07 | `engine/api/facade.py:165` | **反证**：`duan_zuogong.tiyong` 序列化正常，不是 `None` | 记录（纠正任务卡） | —

**现象**：任务卡假设「`tiyong` 序列化成 `None`」。实跑否证：`tiyong_view(chart)` 返回完整 8 字字典。

**复现命令**

```powershell
.venv\Scripts\python.exe -m engine.cli all --pillars "庚申 戊寅 壬子 辛丑" --gender 乾 --json | .venv\Scripts\python.exe -c "import sys,json;d=json.load(sys.stdin);print(json.dumps(d['duan_zuogong']['tiyong'],ensure_ascii=False))"
```

**实测输出**

```
{"Y.s": "体", "Y.b": "体", "M.s": "用", "M.b": "双属", "D.s": "体", "D.b": "体", "H.s": "体", "H.b": "用"}
```

**结论**：这条嫌疑**应当撤销**，改记为 A-01（候选内 `tiyong` 被删键）。**不要按「修 None」的思路去动 `tiyong_view`，它是对的。**

## 3. B 组 · 双轨 / SSOT 冲突

### B-01 | `engine/energy/tiyong.py:140-141` vs `engine/facts/structure_check.py:91-94` | 两套互斥的体用表，同一张盘给出不同答案 | **P0** | 段派体用、用神选取、母星取法

**现象**：
- `engine/energy/tiyong.py`（v1.2 D1，经 `engine/energy/evaluator.py:213` 与 `engine/v5/duan_runner.py:59` 可达）：食伤 → **一律归体**（`body.append(TiyongItem(char=gan, role="食伤", ...))`），全表**没有「双属」这一档**。
- `engine/facts/structure_check.py:91-94`（`engine.cli` 唯一路径）：食神/伤官 → **`双属`**。

同一张 `庚申 戊寅 壬子 辛丑`，月支 `寅`（食神）在两套里一个是「体」、一个是「双属」。这不是措辞差异：`_crosses()`（`structure_check.py:381`）用体用是否相交来决定哪些关系边算做功，`双属` 会改变相交结果，从而改变**候选集合本身**。

**复现命令**

```powershell
.venv\Scripts\python.exe -c "from engine.predicates.types import Bazi,GanZhi; from engine.energy.tiyong import evaluate_tiyong; b=Bazi(年柱=GanZhi.parse('庚申'),月柱=GanZhi.parse('戊寅'),日柱=GanZhi.parse('壬子'),时柱=GanZhi.parse('辛丑')); t=evaluate_tiyong(b); print('ENERGY body=',[(i.char,i.role) for i in t.body]); print('ENERGY purpose=',[(i.char,i.role) for i in t.purpose])"
```

**实测输出**

```
ENERGY body= [('壬', '体'), ('庚', '印'), ('辛', '印'), ('申', '印'), ('寅', '食伤'), ('子', '比劫')]
ENERGY purpose= [('戊', '官杀'), ('丑', '官杀')]
```

对照 A-07 的 facts 输出：`M.b`（寅）= **双属**，而 ENERGY 把 `寅` 放进 `body`。

**影响断语**：段派「体用」是整套做功断语的地基。两套表并存意味着「同一个命主，走 CLI 得一个用神，走 v5/energy 得另一个」。**ADR-006 的 import 闸门挡不住这条**——它只拦 `engine.v5` 的 import，而 `engine/energy` 是独立包，两边都算「现行侧」。这是本次盘点里最该先定性的架构冲突。

---

### B-02 | `engine/v5/runner.py:918` | 路由权重异常 → 静默 `0.5`，与「无匹配」不可区分 | **P1** | 流派权重、置信度折算

**现象**：`_route_weight()` 的 `except Exception: return 0.5`，而正常「无匹配」分支也是 `return 0.5`（`runner.py:917` 的 `matched[0] if matched else 0.5`）。异常被降级成一个看起来合法的中性值。

**复现命令**

```powershell
.venv\Scripts\python.exe -c "from engine.v5.runner import _route_weight; print('good chart ->',_route_weight('blind',{'pillars':{'year':'庚申'}})); print('bad chart ->',_route_weight('blind',{'pillars':123}))"
```

**实测输出**

```
good chart -> 0.5
bad chart -> 0.5
```

**影响断语**：流派权重直接参与置信度折算。异常时静默取中性值，等于「算错了但看起来没算错」。

## 4. C 组 · `except Exception` 吞错

### C-01 | 全局 | 110 处 `except Exception`，其中 20 处完全静默 | **P0**（系统性） | 全部（错误被降级成正常值）

**扫描口径**：`engine/` 46 处（26 文件）、`tools/` 54 处（28 文件）、`tests/` 10 处（4 文件），合计 **110**。按 catch 体分类：`SILENT_PASS` 7、`SILENT_CONTINUE` 5、`RETURN_NONE` 8、`LOGGED` 10、`RERAISE` 9、`OTHER` 71。

**复现命令**（打印静默点 file:line 与 catch 体首行）

```powershell
.venv\Scripts\python.exe -c "import pathlib,re;
out=[]
for d in ('engine','tools','tests'):
    for p in pathlib.Path(d).rglob('*.py'):
        L=p.read_text(encoding='utf-8',errors='replace').splitlines()
        for i,l in enumerate(L):
            if re.search(r'except\s+Exception',l):
                ind=len(l)-len(l.lstrip()); body=[]
                for j in range(i+1,len(L)):
                    s=L[j]
                    if not s.strip(): continue
                    if len(s)-len(s.lstrip())<=ind: break
                    body.append(s.strip())
                    if len(body)>=3: break
                t=' '.join(body)
                k='SILENT_PASS' if body==['pass'] else ('RETURN_NONE' if 'return None' in t else ('SILENT_CONTINUE' if t.startswith('continue') else None))
                if k: out.append((k,str(p),i+1,t[:60]))
print(len(out));
[print(k,f'{f}:{n}',t) for k,f,n,t in out]"
```

**实测输出**（10:0x 快照，含并发新增的 1 条，故为 21）

```
21
RETURN_NONE engine\domain\analysis.py:143 return None
RETURN_NONE engine\domain\analysis.py:154 return None
RETURN_NONE engine\domain\analysis.py:165 return None
RETURN_NONE engine\domain\analysis.py:176 return None
RETURN_NONE engine\domain\analysis.py:187 return None
RETURN_NONE engine\domain\dual_engine.py:168 return None
SILENT_CONTINUE engine\predicates\palace.py:256 continue
SILENT_CONTINUE engine\predicates\palace.py:276 continue
SILENT_PASS engine\predicates\types.py:453 pass
SILENT_CONTINUE engine\v5\preprod.py:139 continue
SILENT_PASS engine\yingqi\retrospective.py:318 pass
SILENT_PASS tools\case_time_basis_audit.py:378 pass
SILENT_CONTINUE tools\claim_condition_corpus.py:61 continue
SILENT_CONTINUE tools\education_label_sheet.py:88 continue
SILENT_PASS tools\extraction_validator.py:200 pass
RETURN_NONE tools\feedback_statement_trace_audit.py:48 return None
RETURN_NONE tools\historical_mapping_recovery.py:38 return None
SILENT_PASS tools\render_report.py:384 pass
SILENT_PASS tools\render_report.py:465 pass
SILENT_PASS tools\_audit_p6a1.py:69 pass
SILENT_PASS tests\v1_3_acceptance\test_h1_statement_id_stable.py:89 pass
```

**说明**：`tools/case_time_basis_audit.py:378` 是并发新增（10:01 出现），不计入本报告 20 条基线。其余 20 条即清单基线。

**影响断语**：静默吞错的共同形态是「把异常降级成一个合法值」，下游无法区分「算出来是这样」和「算挂了走兜底」。下面 C-02～C-07 是其中影响断语的 6 组。

---

### C-02 | `engine/domain/analysis.py:143,154,165,176,187` | 5 个反序列化器失败即 `return None`，整层结论静默消失 | **P0** | 应期回溯、并行分析、四派 findings、融合结论

**现象**：`_load_retrospective` / `_load_parallel_analysis` / `_load_theory_findings` / `_load_blind_findings` / `_load_fusion_findings` 五个函数结构完全一致：`try: X.from_dict(d) except Exception: return None`。而 `from_dict` 对坏数据是会抛的（下面实测三种都抛）。于是「这份 payload 根本没有」和「这份 payload 坏了」在调用方看来一模一样。

**复现命令**

```powershell
.venv\Scripts\python.exe -c "from engine.yingqi.retrospective import RetrospectiveReport; from engine.domain.analysis import _load_retrospective
try: RetrospectiveReport.from_dict({'segments':123})
except Exception as e: print('direct from_dict -> RAISES',type(e).__name__,e)
print('via _load_retrospective ->',repr(_load_retrospective({'segments':123})))"
```

**实测输出**

```
direct from_dict -> RAISES TypeError 'int' object is not iterable
via _load_retrospective -> None
```

**影响断语**：五层里任意一层反序列化失败，`AnalysisOutput` 就少一层结论，而输出看起来「正常」——Agent 会以为「这盘没算应期」，而不是「应期算挂了」。

---

### C-03 | `engine/infrastructure/weight_repository.py:24,45` | 权重文件读失败 → 静默回落到硬编码默认值 | **P0** | 四派权重、综合裁决配比

**现象**：`load_expert_weights()` 读 YAML 失败 `return {}`；`load_school_weights()` 再失败 `return dict(_DEFAULT_SCHOOL_WEIGHTS)`（`ziping 0.42 / tiaohou_ditiansui 0.32 / blind 0.26`）。配置文件损坏、路径搬家、YAML 语法错——全都变成「用默认权重继续算」。

**复现命令**

```powershell
.venv\Scripts\python.exe -c "import engine.infrastructure.weight_repository as w; from pathlib import Path; w._WEIGHTS_PATH=Path('NOPE.yaml'); print('load_expert_weights ->', w.load_expert_weights()); print('load_school_weights ->', w.load_school_weights())"
```

**实测输出**

```
load_expert_weights -> {}
load_school_weights -> {'ziping': 0.42, 'tiaohou_ditiansui': 0.32, 'blind': 0.26}
```

**影响断语**：四派权重直接决定「谁的话更算数」。静默回落意味着**裁决配比可能在无人知情的情况下变成出厂默认**，而报告上看不出任何异常。

---

### C-04 | `engine/predicates/palace.py:256,276` | 十神计算异常 → `continue`，宫位静默漏字 | **P0** | 十神定位、宫位断语

**现象**：`find_shishen_in_bazi` 扫天干/藏干时，`get_shishen` 抛异常就 `continue`。结果里少一个字，调用方拿到的是一个**看起来完整但少了成员**的列表。

**复现命令**（注入 `get_shishen` 故障，观察返回值从 2 项变 0 项）

```powershell
.venv\Scripts\python.exe -c "import engine.predicates.palace as p; from engine.predicates.types import Bazi,GanZhi,_default_canggan_for
b=Bazi(年柱=GanZhi.parse('庚申'),月柱=GanZhi.parse('戊寅'),日柱=GanZhi.parse('壬子'),时柱=GanZhi.parse('辛丑'))
b.藏干=_default_canggan_for(b)
print('normal ->',p.find_shishen_in_bazi('偏印',b))
p.get_shishen=lambda *a,**k:(_ for _ in ()).throw(RuntimeError('boom'))
print('injected ->',p.find_shishen_in_bazi('偏印',b))"
```

**实测输出**

```
normal -> [('年柱', '庚'), ('年支', '庚')]
injected -> []
```

**影响断语**：十神是几乎所有断语的前置。静默漏字会让「某宫有偏印」变成「某宫没有偏印」，属于**结论方向性错误**而非缺字段。

---

### C-05 | `engine/yingqi/retrospective.py:318` | 大运定位失败 → `current_dayun` 变成 `"—"` | **P1** | 应期、流年大运落点

**现象**：`get_dayun_at_year` 抛异常被 `pass` 吞掉，`current_step` 保持 `None`，下一行 `current_dayun = str(current_step.干支) if current_step else "—"` 输出破折号。破折号在报告里会被读成「这一步没有大运」，而不是「大运定位失败」。

**复现命令**

```powershell
.venv\Scripts\python.exe -c "import engine.yingqi.retrospective as r; print('src has bare except-pass:', 'except Exception:' in open(r.__file__,encoding='utf-8').read())"
```

**实测输出**

```
src has bare except-pass: True
```

**影响断语**：应期断语依赖「当前在哪步大运」。定位失败退化成 `—` 后，任何「今年交运/脱运」类断语都失去锚点，且报告看不出这是故障。

> 备注：本条的复现是「确认吞错构造存在」，未构造出真实的 `get_dayun_at_year` 失败盘面（该函数对合法输入不抛）。评级保守取 P1。

---

### C-06 | `engine/predicates/types.py:453` | `_smoke()` 用 `except Exception` 吞掉自己抛的 `AssertionError`，frozen 检查**永远不会失败** | **P1** | 引擎自检可信度

**现象**：

```python
try:
    gz.gan = "甲"          # 若 frozen 失效，这句会成功
    raise AssertionError("frozen 失败：本应 raise")
except Exception:          # ← AssertionError 是 Exception 的子类，被自己吞了
    pass
```

frozen 生效时抛 `FrozenInstanceError`（被吞，正确）；frozen 失效时抛 `AssertionError`（**也被吞**）。两条路径都 `pass`，这个自检恒绿。

**复现命令**

```powershell
.venv\Scripts\python.exe -c "from engine.predicates.types import _smoke; _smoke(); print('_smoke() 返回正常，无异常')"
```

**实测输出**

```
[OK] Bazi 构造: 庚申戊寅壬子辛丑
     寅藏干 = [('甲', '主气', 1.0), ('丙', '中气', 0.3), ('戊', '余气', 0.2)]
[OK] 长生表抽查 3 条全过
_smoke() 返回正常，无异常
```

**影响断语**：不直接影响断语，但让「引擎自检通过」这个信号失效——属于**验证可信度**问题，故 P1。

---

### C-07 | `tools/render_report.py:410,793,801,810` | 缺失区间被渲染成看似合法的中文兜底串 | **P1** | 大运区间、应期年份、年龄区间

**现象**：`_format_year_range` / `_format_age_range` / `_dayun_slice_for_year_range` 解包失败时返回 `"待反馈校准"`，`_format_dayun_span`（`:410`）返回 `"—"`。这些字符串在报告里**读起来像正常内容**，不像错误。

**复现命令**

```powershell
.venv\Scripts\python.exe -c "from tools.render_report import _format_year_range,_format_age_range,_dayun_slice_for_year_range
print('_format_year_range((1998,2008)) ->',_format_year_range((1998,2008)))
print('_format_year_range(None)        ->',_format_year_range(None))
print('_format_age_range(None)         ->',_format_age_range(None))
print('_dayun_slice_for_year_range({},None) ->',_dayun_slice_for_year_range({},None))"
```

**实测输出**

```
_format_year_range((1998,2008)) -> 1998–2008年
_format_year_range(None)        -> 待反馈校准
_format_age_range(None)         -> 待反馈校准
_dayun_slice_for_year_range({},None) -> 待反馈校准
```

**影响断语**：应期断语必须落到具体年份区间。兜底串会让 Agent 把「区间缺失」写成「待反馈校准」交给用户，或更糟——被下游当成「已标注不确定」而放弃追问。

## 5. D 组 · 测试不能失败

### D-01 | `tests/track_e_smoke/test_e_negatives.py:170-268`（`_Reporter.add` 在 `:50-51`） | 8 个负向用例只 `rep.add()` 记录、从不断言；且该文件在 pytest 下根本跑不起来 | **P0**（测试完整性） | E-001～E-008 全部防线

**现象**（两处独立缺陷）：
1. `_Reporter.add(tid, ok, msg)` 只是 `self.results.append(...)`，**全文件零 `assert`**。断言 `ok=False` 时 pytest 依旧绿——失败只被记进 `results`，靠 `main()` 的 `summary()` 返回码体现。也就是说 **pytest 视角下这 8 条测试永不失败**。
2. 该文件的 8 个函数签名是 `(rep: _Reporter, tmp: Path)`，但 `rep` 不是 pytest fixture，直接跑 pytest 得到 8 个 setup ERROR。

**复现命令**

```powershell
.venv\Scripts\python.exe -m pytest tests/track_e_smoke/test_e_negatives.py -q -o addopts="-ra --tb=line" 2>&1 | Select-String -Pattern 'fixture|error' | Select-Object -First 3
```

**实测输出**

```
=================================== ERRORS ====================================
_____________ ERROR at setup of test_E001_missing_schema_version ______________
E       fixture 'rep' not found
```

**复现命令**（改走它自己的 `main()`，看它其实「能报 FAIL」）

```powershell
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'.'); from tests.track_e_smoke.test_e_negatives import main; sys.exit(main())"
```

**实测输出**

```
✓ E-001  [PASS]  step=1 field=schema_version detail=缺失，必须为 '1.2.0'
...
✓ E-008  [PASS]  step=5 field=fingerprint
======================================================================
PASS=8  FAIL=0  SKIP=0  TOTAL=8
main() exit=0
```

**影响断语**：E 组是「防止编造/防越界」的负向防线。它们现在是**只记录不拦截**：即使某天真的放过了一个非法输入，pytest 门禁也不会红。这是「测试存在但防线不存在」。

---

### D-02 | `tests/facts/test_chart_facts.py:212` | `test_graph_is_json_serializable` 只调用不校验 | **P1** | 关系图可序列化

**现象**：函数体只有 `json.dumps(g.to_dict(), ensure_ascii=False)`，没有 assert。它只能证明「不抛异常」——序列化结果对不对（字段有没有丢，例如 A-01 那种）完全测不到。

**复现命令**

```powershell
.venv\Scripts\python.exe -m pytest tests/facts/test_chart_facts.py::test_graph_is_json_serializable -q
```

**实测输出**

```
1 passed
```

**影响断语**：间接。这条测试是「关系图 JSON 契约」的唯一守门人，而它连「键还在不在」都不检查。

---

### D-03 | `tests/facts/test_strength_facts.py:189` | `test_json_serializable` 只调用不校验 | **P1** | 力量事实可序列化

**现象**：同上，`json.dumps(_sf(pillars).to_dict(), ...)` 无 assert。

**复现命令**

```powershell
.venv\Scripts\python.exe -m pytest tests/facts/test_strength_facts.py::test_json_serializable -q
```

**实测输出**

```
3 passed
```

**影响断语**：间接。与 D-02 同构。

---

### D-04 | 6 处 | 只有 `assert x is not None` 的「弱断言」 | **P1** | 取决于被测模块

**现象**：AST 扫描（只统计 `ast.Assert` 且全部为 `X is not None`）命中 6 处。这类断言在「返回了非 None 的空对象」时照样绿。

| 位置 | 用例 |
|---|---|
| `tests/evaluation/test_dual_line_interop.py:12` | `test_controlled_dual_line_interop_module_is_available` |
| `tests/test_accuracy_report.py:126` | `test_exports_from_decision_package` |
| `tests/test_error_policy.py:90` | `test_ep001_tolerant_renderer_failure_only_warns` |
| `tests/test_error_policy.py:167` | `test_ep002_tolerant_findings_failure_only_warns` |
| `tests/test_error_policy.py:236` | `test_ep003_tolerant_self_iter_failure_only_warns` |
| `tests/v1_3_acceptance/test_cfl_c016_fixes.py:292` | `test_run_pipeline_accepts_preflight_parsed_input` |

**复现命令**

```powershell
.venv\Scripts\python.exe -c "import ast,pathlib
def nn(a):
    t=a.test
    return isinstance(t,ast.Compare) and len(t.ops)==1 and isinstance(t.ops[0],ast.IsNot) and isinstance(t.comparators[0],ast.Constant) and t.comparators[0].value is None
for f in sorted(pathlib.Path('tests').rglob('*.py')):
    try: tree=ast.parse(f.read_text(encoding='utf-8'))
    except Exception: continue
    for n in ast.walk(tree):
        if isinstance(n,ast.FunctionDef) and n.name.startswith('test_'):
            A=[x for x in ast.walk(n) if isinstance(x,ast.Assert)]
            if A and all(nn(a) for a in A): print(f'{f}:{n.lineno}',n.name)"
```

**实测输出**

```
tests\evaluation\test_dual_line_interop.py:12 test_controlled_dual_line_interop_module_is_available
tests\test_accuracy_report.py:126 test_exports_from_decision_package
tests\test_error_policy.py:90 test_ep001_tolerant_renderer_failure_only_warns
tests\test_error_policy.py:167 test_ep002_tolerant_findings_failure_only_warns
tests\test_error_policy.py:236 test_ep003_tolerant_self_iter_failure_only_warns
tests\v1_3_acceptance\test_cfl_c016_fixes.py:292 test_run_pipeline_accepts_preflight_parsed_input
```

**影响断语**：`test_error_policy.py` 那三条尤其值得注意——它们测的是「容错路径只 warn 不抛」，而断言只有 `is not None`，等于**没有验证 warn 内容**。这与 C 组的静默吞错正好互补：吞错没有测试盯着。

---

### D-05 | 14 处 | 完全无断言/无 `pytest.raises` 的测试函数 | **P1** | 取决于被测模块

**现象**：AST 扫描命中 17 处，其中 3 处（`tests/test_prediction_yaml_migration.py:31,46,56`）是 `@pytest.fixture` 装饰的 `test_context_*` 夹具、被误计入，**剔除后真值为 14 处**。这些函数体内既无 `assert`、无 `self.assertX`、无 `pytest.raises/fail`，也没调用同文件内带断言的 helper。

**复现命令**

```powershell
.venv\Scripts\python.exe -c "import ast,pathlib
def ver(fn):
    for x in ast.walk(fn):
        if isinstance(x,ast.Assert): return True
        if isinstance(x,ast.Attribute) and (x.attr.startswith('assert') or x.attr in ('raises','fail','xfail')): return True
    return False
for f in sorted(pathlib.Path('tests').rglob('*.py')):
    try: tree=ast.parse(f.read_text(encoding='utf-8'))
    except Exception: continue
    helpers={n.name for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and not n.name.startswith('test_') and ver(n)}
    for n in ast.walk(tree):
        if not isinstance(n,ast.FunctionDef) or not n.name.startswith('test_'): continue
        if any(isinstance(d,ast.Attribute) and d.attr=='fixture' for d in n.decorator_list): continue
        if any(isinstance(x,ast.Attribute) and x.attr in ('raises','fail','xfail') for x in ast.walk(n)): continue
        A=[x for x in ast.walk(n) if isinstance(x,ast.Assert)]
        U=[x for x in ast.walk(n) if isinstance(x,ast.Attribute) and x.attr.startswith('assert')]
        if A or U: continue
        calls={c.func.id for c in ast.walk(n) if isinstance(c,ast.Call) and isinstance(c.func,ast.Name)}
        if calls & helpers: continue
        print(f'{f}:{n.lineno}',n.name)"
```

**实测输出**

```
tests\asof\test_case_2022_out_of_sample.py:31 test_case_2022_out_of_sample_replay_is_skipped_without_deriving_ten_gods
tests\f09\test_artifact_lifecycle.py:4097 test_r41_public_verifier_accepts_actual_ed25519_proof
tests\f09\test_artifact_lifecycle.py:5053 test_r41_old_active_key_proof_remains_valid_under_add_only_rotation
tests\facts\test_chart_facts.py:212 test_graph_is_json_serializable
tests\facts\test_strength_facts.py:189 test_json_serializable
tests\track_e_smoke\test_e_negatives.py:170 test_E001_missing_schema_version
tests\track_e_smoke\test_e_negatives.py:183 test_E002_invalid_pillar
tests\track_e_smoke\test_e_negatives.py:201 test_E003_star_pct_range
tests\track_e_smoke\test_e_negatives.py:210 test_E004_yingqi_no_year
tests\track_e_smoke\test_e_negatives.py:234 test_E005_blacklisted_rule
tests\track_e_smoke\test_e_negatives.py:246 test_E006_three_layer_mismatch
tests\track_e_smoke\test_e_negatives.py:254 test_E007_forbidden_phrase
tests\track_e_smoke\test_e_negatives.py:264 test_E008_duplicate_fingerprint
tests\v5\test_domain_feedback.py:103 test_feedback_status_taxonomy_is_closed
```

其中 `tests/facts/*` 2 条已单列为 D-02/D-03，`tests/track_e_smoke/*` 8 条已单列为 D-01。**本项实际新增 4 条**：`tests/asof/test_case_2022_out_of_sample.py:31`、`tests/f09/test_artifact_lifecycle.py:4097`、`:5053`、`tests/v5/test_domain_feedback.py:103`。

**影响断语**：`test_feedback_status_taxonomy_is_closed`（`tests/v5/`）名不副实——它声称验证「状态分类封闭」，却没有任何断言。

## 6. 未完成与风险

1. **计数会随并发漂移。** 盘点期间 `tools/case_time_basis_audit.py` 在 10:01 被其他代理新建，使 `except Exception` 从 110 变 111。本报告所有数字钉在 110 快照；复现时若看到 111，属正常。
2. **C-05 未构造出真实失败盘面。** `get_dayun_at_year` 对合法输入不抛，我只验证了「吞错构造存在」。评级保守取 P1，未升 P0。
3. **`po` 边是否该做功未定性。** A-06 只证明「破边不产生候选」这个事实，**没有**判断这是漏实现还是有意排除（段派文献里破的做功地位需理论侧确认）。中枢定性前不要直接补 `"po"` 进 `_ZHI_KINDS`。
4. **B-01 的裁决方向未定。** 我只证明两套表冲突，未判断哪套是权威。注意 `engine/energy/tiyong.py` 的模块 docstring 引用 M1-D-005..008 等条目，看起来是「有出处」的一套；`structure_check.py` 的 `双属` 更像为候选层做的工程折中。**需要理论侧裁决**，不要按「哪边代码少改哪边」来选。
5. **未盘点的区域。** `tests/` 下 `tests/f09`、`tests/asof`、`tests/evaluation` 等被 `addopts --ignore` 排除的目录，只在 D 组按 AST 扫了「有无断言」，**没有逐条判断断言强度是否足够**。若要 A2 全覆盖，这是下一轮的口子。
6. **未验证运行时影响面。** 本报告未统计「哪些断语模板/规则实际读 `cand['actor']`」。若下游全是 `.get('actor')`，A-02 的实际危害是「方向缺失」；若有 `cand['actor']` 硬取键，则是运行时 `KeyError`。这两种严重度不同，建议 A2 修之前先 grep 一遍消费方。

## 7. 下游须知

1. **A-07 是反证，别按任务卡原话去修。** `tiyong_view` 是对的，不要动。要修的是 `facade.py:93-94` 的 keep 白名单和 `facade.py:67` 的「删 None」。
2. **A-02/A-03/A-04 的修法不止一处。** 只改 `structure_check.py:476` 让冲/刑/穿有 actor 还不够——`facade.py:94` 仍会把 `None` 删键。**两处必须同时改**，否则「无 actor」依旧不可见。建议把 `actor` 从「可删键」改成「恒输出，无方向时输出 `null`」，让 `null` 承载「算了但没有」的语义。
3. **B-01 优先级高于所有 A 组。** A 组是「字段看不见」，B-01 是「字段看见了但两个数不一样」。后者会让 Agent 拿到自相矛盾的事实，比缺字段更危险。建议 A2 第一件事是让中枢裁决 `engine/energy` 与 `engine/facts` 谁是体用 SSOT。
4. **ADR-006 的闸门不覆盖 B-01。** `tools/v5_boundary_check.py`（ADR-006 第 2 条）只拦 `import engine.v5`。若 A2 决定「`engine/energy` 也退役」，闸门规则需扩展；若决定「`engine/energy` 是权威」，则 `engine/facts/structure_check.py` 的 `_TIYONG` 要改成调用它。**不要两边都留。**
5. **D-01 修的时候注意：** 那 8 条现在 pytest 下是 ERROR（`fixture 'rep' not found`），说明它们从来没被 `testpaths` 门禁跑过（`tests/track_e_smoke` 不在 `testpaths`）。修法是加 `assert` 或加 `rep` fixture，**但不要**把它们移进 `testpaths` 除非同时把 8 条改真能断言——否则等于给门禁加 8 条永绿测试。
6. **验收口径未变。** 本任务只读，`python -m pytest -q` 仍是 `220 passed, 1 skipped`；`git status` 中与本任务相关的只有 `?? META/upper-layer-faults-v1.md`。
