# T-140 BRIEF · 事实出口保留 tiyong / binzhu / distance / actor

- 任务卡：`tasks/T-140/PROMPT.md`（含 4.0 追加约束：中枢两次裁决，第二次为「事实视图与 Agent 视图分离」）
- 决策依据：`docs/adr/ADR-007-refactor-direction-adjudication.md` D5
- 状态：**已完成**，两条验收命令均绿

## 0. 一句话结论

`analyze_facts()` 现在是**完整事实视图**（候选含 `tiyong`/`binzhu`/`distance`/`actor`，`actor` 无方向时是 `"actor": null` 而非键消失）；新增 `facade.compact_for_agent()` 负责 **Agent 视图**，`engine.cli all` 默认走它、`--full` 出完整事实。`tests/api/test_engine_reset_regression.py` **一个字未改**（`git diff` 为空），15KB 断言照旧通过。

---

## 1. 改动文件与行号

### 1.1 `engine/api/facade.py`（+62 / −12）

| 行 | 改动 |
|---|---|
| `45-53` | `_compact()` 新增参数 `keep_null_keys: frozenset[str] = frozenset()`，docstring 说明「这些键值为 None 也保留」 |
| `74` | 递归调用透传 `keep_null_keys` |
| `75` | 删除条件由 `if compact in (None, [], {}):` 改为 `if compact in (None, [], {}) and key not in keep_null_keys:` |
| `80` | list 递归同样透传 |
| `99-107` | `_compact_zuogong()`：`keep` 扩为 `("mode","relation_kind","edge_id","members","ten_gods","tiyong","actor","binzhu","distance")`；取值改 `cand.get(k)`，并让 `actor` **无条件进入**（`k == "actor"` 分支），保证 null 不丢键 |
| `111-113` | 新增三个投影白名单常量 `_AGENT_OMIT_CANDIDATE_KEYS` / `_AGENT_OMIT_EDGE_KEYS` / `_AGENT_OMIT_RELATION_KEYS` |
| `116-148` | 新增 `compact_for_agent(payload)`：纯函数投影，不修改入参 |
| `231` | `analyze_facts()` 返回改为 `_compact(payload, keep_null_keys=frozenset({"actor"}))`（即完整事实） |

### 1.2 `engine/cli.py`（+8 / −2）

| 行 | 改动 |
|---|---|
| `9` | import 增加 `compact_for_agent` |
| `18` | 注释更正：预算是 CLI 的（`保证 CLI 默认输出 < 15KB（完整事实见 --full）`） |
| `50-52` | `_run()`：`if command == "all" and not args.full: payload = compact_for_agent(payload)` |
| `83` | `--full` 开关（挂在 shared parser，所有子命令可解析，仅 `all` 生效） |

### 1.3 `tests/api/test_facade_zuogong_fields.py`（新增，6 条）

`test_candidates_carry_tiyong_binzhu_distance_and_actor`、`test_actor_null_is_null_not_missing_key`、`test_compact_for_agent_drops_only_restorable_fields`、`test_compact_for_agent_does_not_mutate_input`、`test_cli_full_keeps_facts_default_stays_compact`、`test_zuogong_atom_target_not_always_tail_member`。

---

## 2. `_compact` 的改法（追问链结论）

任务卡要求「自己追一遍调用链」。实际链路是**两级**：

1. `_compact_zuogong(candidates)` → 只留白名单键，`actor=None` 在**这一级**就被 `if cand.get(k) not in (None,[],())` 丢掉；
2. 整个 payload 再走 `analyze_facts` 末尾的 `_compact(payload)`，其 `:75` 的 `continue` 会**第二次**删掉任何空值键。

所以只改第 1 级无效，必须两级同时改。选法是给 `_compact` 加 `keep_null_keys` 参数并在递归/list 分支透传，顶层调用传 `frozenset({"actor"})`；**没有**用哨兵字符串，也没有为 `actor` 单独开特例分支。`"actor"` 这个键名在本仓库只出现在做功候选上（全仓 grep 确认），不会误伤其他段落。

---

## 3. `actor` 为 null 时的真实 JSON（原始片段）

盘：`癸丑 癸亥 辛亥 癸巳`（坤）。

① **默认 Agent 视图**（`python -m engine.cli all`，13 951 B）：

```json
{"mode":"制用","relation_kind":"xing","edge_id":"e010","members":["M.b","D.b"],"ten_gods":["伤官","伤官"],"tiyong":["双属","双属"],"actor":null}
```

② **完整事实**（`--full`，17 266 B）：

```json
{"mode":"制用","relation_kind":"xing","edge_id":"e010","members":["M.b","D.b"],"ten_gods":["伤官","伤官"],"tiyong":["双属","双属"],"actor":null,"binzhu":[{"layer":1,"sides":["宾","宾"],"direction":"需判断"},{"layer":2,"sides":["宾","主"],"direction":"需判断"},{"layer":3,"sides":["宾","主"],"direction":"需判断"}],"distance":1}
```

③ 带具体地址的候选（自证第 1 条：同一候选同时含 `tiyong` 与 `actor`）：

```json
{"mode":"生泄用","relation_kind":"sheng","edge_id":"e002","members":["D.s","Y.s"],"ten_gods":["日主","食神"],"tiyong":["体","双属"],"actor":"D.s","binzhu":[{"layer":1,"sides":["主","宾"],"direction":"正向"},{"layer":2,"sides":["主","宾"],"direction":"正向"},{"layer":3,"sides":["主","宾"],"direction":"正向"}],"distance":2}
```

④ 分档差异：默认视图 `relations` 键 = `['edges','muku']`，边键 = `['distance','id','kind','layer','members','scope']`；`--full` 的 `relations` 键 = `['edges','muku','nodes']`，边键多 `chars`。

---

## 4. target 判定修复前后对比（自证第 2 条）

用 `atoms.build_context()` 把每条候选**单独**喂给 `zuogong` 原子（`ctx["zuogong"] = [cand]`），取 `bindings["T"]`。盘：`癸丑 癸亥 辛亥 癸巳`（坤），14 条候选。

| id | mode | members | actor | 修前 T | 修后 T |
|---|---|---|---|---|---|
| 7 | 化用 | `["H.b","Y.b"]` | `H.b` | `Y.b` | **`H.b`** |
| 11 | 制用 | `["H.b","D.s"]` | `H.b` | `D.s` | **`H.b`** |
| 12 | 制用 | `["H.b","Y.s"]` | `H.b` | `Y.s` | **`H.b`** |
| 13 | 制用 | `["H.b","M.s"]` | `H.b` | `M.s` | **`H.b`** |

- 修前：`target == members[-1]` 命中 **14 / 14**（100% 回退，与卡 §1 描述一致）。
- 修后：**4 / 14** 不再等于 `members[-1]`，其余 10 条因「用」本就在末位而不变。
- 决定性对照（已写成测试）：同一条候选 `["H.b","Y.s"]`（正官克食神）把 `tiyong` 削掉后，`T` 立刻回退成 `"Y.s"`；带 `tiyong` 时 `T == "H.b"`。证明确实是 `tiyong` 在驱动判定，不是别的巧合。

自证第 3 条：`binzhu` / `distance` 出现在候选里 —— 见 §3 ②③（`--full`）。

---

## 5. 原始输出（两条验收命令）

```text
> .venv\Scripts\python.exe -m pytest -q
........................................................................ [ 31%]
........................................................................ [ 63%]
........................................................................ [ 95%]
..........                                                               [100%]
=========================== short test summary info ===========================
SKIPPED [1] tests\tools\test_bundle_pii.py:34: （脚本缺失，T-114，未变）
226 passed, 1 skipped in 13.16s
EXIT=0
```

```text
> .venv\Scripts\python.exe -m tools.verify_baseline
{
  "pytest_passed": 226,
  "pytest_failed": 0,
  "pytest_rc": 0,
  "audit_errors": 0,
  "audit_rc": 0,
  "relations_ok": true,
  "relations_rc": 0,
  "zuogong_charts": 477,
  "zuogong_day_branch": 350,
  "zuogong_rc": 0
}
EXIT=0
```

对照 `META/baseline-v1.json`（220 passed / 0 failed / audit 0 / relations ok / zuogong 477）：**四项不降**——通过数 220→226（新增 6 条），失败数 0→0，底层体检 0→0，关系图校验 true→true，宫制星覆盖 477→477。

15KB 断言的证明（测试文件零改动）：

```text
> git diff -- tests/api/test_engine_reset_regression.py
(无输出，DIFF_EXIT=0)
```

体积实测（`len(stdout.encode("utf-8"))`）：

| 盘 | 改动前默认 | 现在默认（Agent 视图） | 现在 `--full` | 上限 |
|---|---|---|---|---|
| 庚申 戊寅 壬子 辛丑（15KB 断言用盘，16 条候选） | 14 904 | **14 864** | 18 556 | < 15 000 |
| 癸丑 癸亥 辛亥 癸巳（14 条候选） | — | 13 951 | 17 266 | — |

## 6. 正交性复核（卡 §2.3）

四项全部由位置/五行生克决定，**不含吉凶**，已放行：

- `tiyong`：`structure_check._TIYONG` 十神→体/用/双属，纯映射（食伤标「双属」，正是 ADR-007 D1 的忠实实现）。
- `binzhu`：`chart_facts.binzhu_side(addr, layer)` 纯位置函数；`direction` 五值（正向/反向/同在主位/同在宾位/需判断）全是主宾方位关系，`需判断` 是「双属对双属」的缺省标记，不是吉凶档。
- `distance`：柱序下标差的绝对值。
- `actor`：关系边上生克/入墓的发出方，无方向时为 `null`。

---

## 7. 未完成与风险（**必须由中枢裁决的三条**）

1. **Agent 视图余量只剩 136 B**（14 864 / 15 000）。这已经是把 binzhu + distance + `relations.nodes` + `edges.chars` + `edges.between` 全部投影掉之后的结果；其中只有 `binzhu` 是中枢点名的，另四项是我按「纯函数可还原」同一标准加的（见下条）。任何再往候选/关系里加字段的卡都会重新撞线。建议：单开一张卡，把 CLI 预算与投影白名单一起收口（我未改断言，按你的红线一办）。
2. **投影清单是我扩的，请复核**：中枢只点名 `binzhu`。但不砍 `distance`(208B)+`edges.chars`(169B)+`edges.between`(82B)+`nodes`(113B) 就压不进 15 000（只砍 binzhu 是 15 554，超 554）。四项都能从保留字段唯一还原，理由已写进 `compact_for_agent` docstring。若你认为 `distance` 必须留在默认视图，那就只能再削 208 B 别的东西，请给口径。
3. **`atoms.py:487` 的 target 语义仍不对**（超出本卡 File Scope，未改）：修好 `tiyong` 后，上表这 4 条之所以变，是因为「用」正好是**官杀**、也正是发出制的 `actor`，于是 `T == Z`。换句话说，原子把「用＝被制者」当成了恒等式，遇到「官杀克食伤」会把 target 判成制者本身。D5 的管线已通（不再是恒等于 `members[-1]` 的静默错），但「谁制谁」的语义要下一张卡修 `atoms.py`：target 应取 `actor` 之外的被作用方，或显式引入 `target` 字段由 facts 给出。

---

## 8. 下游须知

- **`analyze_facts()` 返回值变大**：18.5KB 量级（原 14.9KB）。`claim_condition_corpus` / `claim_condition_report` / `education_label_sheet` / `engine_audit` / `relations_audit` / `zuogong_probe` 都直调它，拿到的是**完整事实**，字段只增不减，无需改动。
- **`engine.cli all` 默认输出形态变了**：不再含 `relations.nodes`、`edges[].chars`、`edges[].between`、`candidates[].binzhu`、`candidates[].distance`。任何**解析 CLI stdout** 的下游要么按文档还原，要么加 `--full`。已知受影响：`tools/rf_facts_hydrate.py:109,114`（它把 `all.json` 当「全量事实」落盘），建议那张卡加 `--full`——本卡未改 `tools/`。
- `engine.cli` 其他子命令（chart/relations/strength/shensha/structures）输出**未变**。
- 新增测试文件 `tests/api/test_facade_zuogong_fields.py` 纳入默认门禁（`tests/api` 在 testpaths 内），默认基数 220 → 226。
