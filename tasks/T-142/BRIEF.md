# T-142 BRIEF · 原子层修复包（原局/岁运隔离、he_at、binzhu、lu_at、needs_judgment、_label）

- 任务卡：`tasks/T-142/PROMPT.md`
- 决策依据：`docs/adr/ADR-007-refactor-direction-adjudication.md` D3 / D5 / D12
- 前置：T-140、T-141 已完成并合入（已核对：`facade.py:102` keep 含 `tiyong`；`structure_check._crosses` 已排除 `双属`）
- 状态：**已完成**，两条验收命令均绿（`994 passed, 1 skipped` / `verify_baseline` 四项不降，EXIT=0）

## 0. 一句话结论

`he_at(D.b)` 在 481 盘上从 **412 盘（85.7%）降到 182 盘（37.8%）**——被砍掉的 230 盘全是「半三合/半三会/日柱自合」被误当成「被合」。同一批盘上 `M1-D-298`（夫妻宫安静）的 `candidate` 从 **6** 升到 **39**，`rejected` 从 **467** 降到 **364**：这条断语此前几乎被前置条件自动枪毙，现在真正开始筛人。

---

## 1. 六个子项各自改了什么

| # | 子项 | 改动 | 位置 |
|---|---|---|---|
| ① | 原局原子隔离岁运边 | 新增 `_edges(ctx, scope="natal")`；`edge` / `edge_touches` / `chong_at` / `he_at` / `chuan_at` / `xing_at` / `po_at` / `group_complete` / `muku_open` 一律经它取边。`edge` 增 `scope?`（`natal`/`dayun`/`liunian`/`dayun+liunian`/`any`） | `atoms.py` `_edges()`、各关系原子 |
| ② | `he_at` 收窄 | `HE_KINDS` 由 6 种改为 `("liuhe","zhi_anhe")`；新增 `_is_he_edge()` 统一判定；新增 `exclude_god?`（默认不启用）。排除半局/拱局、完整三合三会、`ganzhi_zihe`、`wuhe` | `atoms.py` `HE_KINDS` / `he_at()` / `_is_he_edge()` |
| ③ | `binzhu` 落地 | 不再恒 `unknown`。参数 `layer`（必填 1–4）、`side?`（主/宾）、`at?`；先读做功候选自带的 `binzhu` 读数（`layer/sides/direction`），候选未覆盖的地址回落到事实层纯位置函数 `chart_facts.binzhu_side`（同一 SSOT）。第 4 层「岁运为宾」需岁运节点，无岁运时 `side="宾"` 判 `false` 并注明原因 | `atoms.py` `binzhu()` / `_binzhu_from_facts()` / `_suiyun_addrs()` |
| ④ | 新增 `lu_at` | 参数 `gan?`（默认日主）、`at?`（限定地支地址）。禄表 `from engine.facts.chart_facts import _LU`（不另造表，与 `structure_check.py:21` 同源导入）。命中返回 `addr` + `zhi` 绑定；`at` 给天干地址时返回 `unknown`（禄只看地支） | `atoms.py` `lu_at()` |
| ⑤ | 新增 `needs_judgment` | 恒 `unknown`，`reason` 必填（`SIGNATURES` 里为必填参数，`validate_claim` 会拦缺参）；缺 `reason` 时仍返回 `unknown` 但附说明 | `atoms.py` `needs_judgment()` |
| ⑥ | `_label` 可读 | 支持 `all[...]` / `any[...]` / `not(...)` 递归展开，带 `as=` 时一并输出；无 `atom` 时输出 `<无原子:键名>` 而不是 `?()` | `ir.py` `_label()` |

未改：`engine/api/facade.py`、`engine/facts/**`、`theory/claims/**`、`theory/_ir/`、`sources/`、`pyproject.toml`（`git status` 只有本卡 3 个源文件 + 1 个测试文件 + 本卡测量脚本）。

**关于「读事实」与「不自造表」的边界**：`lu_at` 与 `binzhu` 都从 `engine.facts` 拿定义（`_LU` / `binzhu_side`），没有在原子层复制表；这符合契约 23 §四「全部原子只能读 engine.facts 已产出的字段」。`binzhu` 优先用事实输出（候选里的 `binzhu` 读数），仅在候选未覆盖该地址时才调用纯位置函数。

---

## 2. `he_at(D.b)` 改前 / 改后（481 盘，同进程 A/B）

脚本：`tasks/T-142/_measure_he_at.py`（改前口径不靠 git 回退，而是在同一进程内把 `ATOMS["he_at"]` 临时替换为旧实现）。

### 2.1 命中盘数

| 口径 | 命中盘数 | 占比 |
|---|---:|---:|
| 改前（`liuhe/wuhe/zhi_anhe/sanhe/sanhui/ganzhi_zihe` 全认） | **412** | 85.7% |
| 改后（只认 `liuhe` + `zhi_anhe`） | **182** | 37.8% |

### 2.2 改前明细（首条命中边的 kind，与任务卡给的数字完全一致）

```text
改前（首条命中边 kind）: {'liuhe': 70, 'zhi_anhe': 48, 'sanhe': 155, 'sanhui': 134, 'ganzhi_zihe': 5}
```

### 2.3 改后明细

```text
改后（首条命中边 kind）: {'liuhe': 109, 'zhi_anhe': 73}          # 合计 182
改后 kind 组合         : {'liuhe': 101, 'zhi_anhe': 69, 'liuhe+zhi_anhe': 12}
```

> **为什么不是 70+48=118**：卡里的 70/48/155/134/5 是「首条命中边」的归属（`ctx["edges"]` 的顺序），一张盘只记一次。收窄后，原先被第一条半三合「占位」的盘会继续往后找，落到它自己的六合/暗合边上，于是单 kind 计数升到 109/73；盘级唯一数仍是 182。

### 2.4 盘级并集（一张盘可同时挂多种 kind，用于核对 412 的来源）

```text
盘级并集（一张盘可多 kind）: {'liuhe': 113, 'sanhe': 207, 'sanhui': 220, 'zhi_anhe': 81, 'ganzhi_zihe': 63}
```

即：220 盘有半三会、207 盘有半三合、63 盘有日柱自合——这些以前都算「夫妻宫被合」。

### 2.5 对真实断语的影响（`M1-D-298`「夫妻宫安静」，481 盘）

脚本：`tasks/T-142/_measure_claim_298.py`

```text
改后 he_at（六合/暗合）  : {'rejected': 364, 'evidence_only': 78, 'candidate': 39}
改前 he_at（全 HE_KINDS）: {'rejected': 467, 'candidate': 6, 'evidence_only': 8}
```

开火率 1.2% → 8.1%，落在契约 23 §八「开火率 5%–95%」区间内；改前 1.2% 属于「几乎不筛人」。

### 2.6 完整三合/三会（`full`）算不算「被合」——查原文结论

**结论：原文无据，保持排除，标注「待中枢裁定」。**

- 段派《婚姻专辑》:48 原文：「夫妻宫位要安静，如有用，不能被刑坏，**冲破**，**穿倒**，或**六合**，**暗合他星**（配偶星以外的星），也不宜杂透，多现。」——枚举只有六合与暗合他星，没有三合三会。
- 任派「婚姻好坏 3 条件」第 1 条（`theory/raw/ren/r05-r07-theory.md:490`）转述同一条判据，同样只写「不六合暗合他星」。
- `theory/raw/ren/r01-r04-theory.md:161`「三合局要义」讲的是**成局条件**（中神双现不成局、忌冲中神），不是「宫被合则不安静」。
- 段派原书里三合出现在婚姻语境时是**应期/事件**（`:388`「癸酉年巳酉丑三合局，结婚」），不是「宫位不安静」的判据。
- 因此 `full` 暂排除；需要完整局的断语请用 `group_complete`（本卡已保留它并在测试里锁住「完整局不算被合、`group_complete` 仍为真」）。

---

## 3. `ATOMS` 42 → 44 与契约改动

### 3.1 顺序（先契约、后断言，没有先改断言让红变绿）

1. 先改 `engine/contracts/23-claim-condition-protocol-v1.md`：
   - §四 标题 42 → 44，版本 `v1-draft` → `v1.1`，加「岁运隔离」总则；
   - §4.2 表逐行补 `scope` / `exclude_god` 语义，新增 **§4.2.1 `he_at` 的合口径**（逐 kind 判据 + 原文行号 + 「`full` 待裁定」）；
   - §4.4 `binzhu` 参数改 `layer, side?, at?`，加「v1.1 起读事实」说明（两处事实来源）；
   - 新增 **§4.7 禄与显式未知（2）**：`lu_at` / `needs_judgment` 的签名、返回值与新增理由（含 `False∧Unknown=False`、`True∧Unknown=Unknown` 的动机与 ADR-007 D12 出处）；
   - §6.2「42 个基础原子」→ 44；
   - §九 版本 `v1.1`，新增 **§9.1 变更登记**（5 行，逐条写依据）。
2. 再改 `atoms.py`：`ATOMS` 增 `lu_at`、`needs_judgment`，`SIGNATURES` 同步（`lu_at: ((), ("gan","at"))`、`needs_judgment: (("reason",), ())`、`edge` optional 加 `scope`、`he_at` optional 加 `exclude_god`、`binzhu` optional 加 `side`/`at`）。
3. 最后才改断言：`assert len(ATOMS) == 44`，并加注释指向契约 §4.7 与 §九。

### 3.2 结果

```text
44 44          # len(ATOMS), len(SIGNATURES)
```

测试 `test_registry_has_44_atoms_and_new_signatures` 同时锁住「原子表 = 签名表」和两个新原子的参数形状，避免以后只改一边。

---

## 4. 五条自证的真实输出

复跑：`.venv\Scripts\python.exe -X utf8 tasks/T-142\_proofs.py` + `...\_measure_he_at.py`

### 证 1 · `he_at(D.b)` 481 盘改前后

见 §2.1–§2.4：**412（85.7%）→ 182（37.8%）**；改前 kind 明细 `liuhe 70 / zhi_anhe 48 / sanhe 155 / sanhui 134 / ganzhi_zihe 5`，改后 `liuhe 109 / zhi_anhe 73`。

### 证 2 · 岁运边不污染原局原子，`edge(scope=...)` 能查到岁运边

```text
【证2】原局原子不被岁运边点燃
  chong_at(D.b) 原局        : False
  chong_at(D.b) 带 2026 流年: False
  edge(chong, scope=liunian): {'edge_id': 'e020'}
  edge(chong) 默认 natal    : {'edge_id': 'e013'}
```

盘 `庚申 戊寅 壬子 辛丑` + `liunian_year=2026`（丙午）：关系图共 21 条边，其中 9 条 `scope=liunian`；`chong(D.b, LN2026.b)` 确实存在（e020），但 `chong_at(D.b)` 在带与不带流年两种输入下都是 `False`，未被点燃。

### 证 3 · `lu_at` 与 `chart_facts._LU` 一致

```text
【证3】lu_at 与 chart_facts._LU 一致
  壬子日默认(壬禄亥)      : False 壬禄在亥，盘中四支未见
  甲禄落在 M.b(寅)        : {'addr': 'M.b', 'zhi': '寅'}
  癸禄落在 Y.b(子)        : {'addr': 'Y.b', 'zhi': '子'}
```

另有一条参数化测试对 `_LU` 全部 10 个天干与盘中四支做一致性核对（`test_lu_at_consistent_with_fact_table_for_all_stems`）。

### 证 4 · `needs_judgment` 的三值行为

```text
【证4】needs_judgment 的三值行为
  True AND Unknown = None  | claim state = needs_fact
  False AND Unknown = False | claim state = rejected
```

测试 `test_false_and_unknown_is_false` 还验证了**两种顺序**（未知在前 / 假在前）都必须判假，证明「假优先」不是靠 `all` 的遍历顺序碰出来的。

### 证 5 · `_label` 对 `{"not": ...}` 输出可读字符串

```text
【证5】_label 不再输出 ?()
  not : not(kongwang(at=D.b))
  any : any[edge(type=chong, between=['Y.b', 'D.b']), not(kongwang(at=D.b))]
  all : all[any[day_master(gan=壬)]]
```

### 附 · `binzhu` 读事实

```text
  L1 D.s : D.s 第1层为主（正向）
  L4 LN  : LN2026.s 第4层为宾（正向）
  L4 无岁运 side=宾: 本次输入未提供岁运节点，第 4 层只有原局主位，无宾可命中
```

---

## 5. 验收命令（数字与退出码）

```text
.venv\Scripts\python.exe -m pytest -q
→ 994 passed, 1 skipped, 1 warning   EXIT=0
  （改动前同命令 959 passed, 1 skipped；+35 全部是本卡新增 tests/claims/test_condition_ir_atoms.py）
  注：T-144 已把 testpaths 从 226 档扩到 994 档，故与 T-140/T-141 简报里的 226/227 不可直接比。

.venv\Scripts\python.exe -m tools.verify_baseline
→ pytest_passed 994 / pytest_failed 0 / pytest_rc 0 / audit_errors 0 / audit_rc 0 /
  relations_ok true / relations_rc 0 / zuogong_charts 477 / zuogong_day_branch 346 / zuogong_rc 0
  EXIT=0

.venv\Scripts\python.exe -m tools.verify_baseline --compare
→ 【基线未退步】 EXIT=0
```

`zuogong_charts 477` / `zuogong_day_branch 346` 与 T-141 收尾数字一致，未因本卡变化（本卡不碰 `engine/facts/`）。

---

## 6. 未完成、风险与待中枢裁定

1. **完整三合/三会（`full`）是否算「被合」——待裁定**（见 §2.6）。当前排除；若中枢判定算，只改 `_is_he_edge()` 一行 + 契约 §4.2.1 一行，`he_at(D.b)` 命中数会从 182 上升（481 盘中「D.b 参与完整三合/三会」的盘数可用同脚本扩展统计）。
2. **`ir.py` 的失败/未知列表会重复同一标签**（`evaluate` 的 `all` 分支：`failed + out.failed + [_label(child)]`，而 `out.failed` 已含该标签），所以自证输出里能见到 `['day_master(gan=甲)', 'day_master(gan=甲)']`。这是**既有缺陷**，不是本卡引入；本卡对 `ir.py` 只有「仅 `_label`」的授权，故未改，仅在此登记。修法是一行去重，请中枢授权。
3. **`engine/claims/condition_ir/__init__.py:6` 仍写「42 个」**（包文档字符串）。该文件不在本卡 File Scope，未改；建议授权一行文档同步（`docs/analysis-pipeline-explained.md:401` 同）。
4. **`liunian_present` 与岁运边不同步**（既有）：传 `liunian_year=2026` 时关系图已产出 `LN2026.*` 边，但 `chart.cycles` 里没有 `liunian` 字段，`ctx["liunian"]` 为 `None` → `liunian_present` 返回 `false`。实测两种入口都如此：`birth_dt` 入口（LN 边 7 条）与 `pillars` 入口（LN 边 9 条）都得到 `ctx.liunian=None` / `liunian_present=false`。本卡未动（属 `engine/facts`），但 T-145 做岁运原子时会撞上，先记账。
5. **`he_at` 口径变化会影响既有断语的命中率**：卡内 `unmapped_prose` 提到「未区分合的是否配偶星」，现在 `exclude_god` 已具备，但把 `exclude_god: 配偶星` 写进 `pilot-20.yaml` 属 T-143 的范围（`theory/claims/**` 本卡禁止改）。
6. **`_iter_atoms`（`count` / `exists`）对 `binzhu` / `lu_at` 的语义**：`binzhu` 的 `at` 现为可选，`count(atom=binzhu, layer=1, side=主)` 会数出 1（只有 `D.s`）；`lu_at` 在 8 个地址上迭代时天干地址返回 `unknown`、不计入。两者都已在契约 §4.7 / §4.4 说明，但若中枢希望 `count` 只扫地支，需要另开一卡。
7. **`binzhu` 第 4 层在无岁运输入时返回 `false`（不是 `unknown`）**：理由与 D3「未提供是客观输入事实」一致（同 `dayun_present`）。若中枢认为应返回 `unknown`（未知而非不存在），改一行即可。

---

## 7. 下游须知

- **T-143（`theory/claims/**`）**：`he_at` 现在只认六合/暗合。原先用 `he_at` 表达「宫被半合」或「日柱自合」的断语会被判 `false`，请改用 `group_complete`（完整局）或显式 `edge(type=sanhe, between=...)`。把「不会算的条件」从 `unmapped_prose` 搬进条件树时，用 `needs_judgment(reason=...)` 而不是删条件。
- **T-145（岁运原子）**：`edge(scope="dayun"|"liunian"|"dayun+liunian"|"any")` 已可直接查岁运边，不必另建查询路径；另外注意 §6.4 的 `liunian_present` 不同步问题。
- **报告层**：`failed_atoms` / `unknown_facts` 现在对组合节点也给出可读标签（`not(...)` / `any[...]` / `all[...]`），可以直接进人话报告；但同一标签可能重复出现（§6.2），展示前去重。
- **契约**：原子表现在是 44 个、版本 `v1.1`；`validate_claim` 会按新签名校验，旧断语若给 `binzhu` 只传 `layer` 仍合法。
