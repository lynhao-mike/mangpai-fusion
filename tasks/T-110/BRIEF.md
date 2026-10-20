# T-110 BRIEF · `as_of_contract_gate` 的 locator 校验缺口修复

**结论：缺陷已修复，存量体检发现 5 个失效 locator（4 个格式不可解析 + 1 个文件缺失），
因此按任务卡 Step 2 走「报警优先、不阻断」模式。43 个冻结 case 实跑零回归，
`python -m pytest -q` 229 passed（与基线一致）。**

---

## 1. 改动文件

| # | 文件 | 动作 | 说明 |
|---|---|---|---|
| 1 | `tools/as_of_contract_gate.py` | 修改 | 新增 locator 可达性校验，接进 `check_theory_evidence` / `run_contract_gate`；既有字段与语义未删未改 |
| 2 | `tests/tools/test_locator_reachability.py` | 新建 | 22 个回归测试，锁定可达/失效/报警不阻断三条契约 |
| 3 | `tasks/T-110/STATUS.md` | 修改 | 执行记录 |

未触碰 `cases/`、`theory/`、`engine/` 下任何文件（见 §5 git status 佐证）。

---

## 2. 存量体检（T-110 核心产出，Step 1 实测数字）

扫描范围：`cases/**/asof-blind-freeze.json` 共 **43 个冻结包**。口径限定在
`theory_evidence[].locator`（**不是**全文的 `locator` 键 —— 后者在
`natal_capacity_graph` / `frozen_event_candidates` 等字段里表示图内节点路径，
与理论库文件无关，误把那些算进去会得到上百个假「失效」）。

| 指标 | 数值 |
|---|---|
| 冻结包总数 | **43** |
| 其中含 `theory_evidence` 列表的 | **19** |
| 不含（字段缺失/为空，由既有硬门控负责） | 24 |
| `theory_evidence` dict 条目总数 | **59** |
| 每条都带字符串 `locator` | 59（0 条缺 key，0 条类型非字符串） |
| **locator 字符串总数** | **59** |
| 展开后 `path:line` 目标数（按 `;` 拆分） | **60** |
| ✅ 健康（文件存在 + 行号在范围内） | **55** |
| ❌ 文件缺失 | **1** |
| ❌ 行号越界 | **0** |
| ❌ 格式不可解析（无行号等） | **4** |
| **失效合计** | **5** |

### 2.1 格式分布（59 条字符串）

| 形态 | 条数 | 例 |
|---|---|---|
| `path:start-end` | 31 | `theory/ziping/index-new.yaml:794-831` |
| `path:line` | 23 | `theory/yang/index.yaml:794` |
| `;` 串起的多目标 | 1 | `theory/gao/index.yaml:2379-2380; theory/gao/index.yaml:2679-2680` |
| 其它（不可解析） | 4 | 见 §2.2 |

### 2.2 失效条目明细（共 5 条，涉及 3 个 case）

| case | rule_id | locator | 失效类型 | 原因 |
|---|---|---|---|---|
| `C-2026-RF000900` | 普通格局论边界 | `theory/_ir/unified_rule_ir.yaml:46449-46478` | **文件缺失** | `theory/_ir/` 下只有 `graph_metrics.yaml`、`rule_graph.yaml`、`theory_alignment_report.yaml`、`ziping_alignment_report.yaml`、`ziping_rule_ir.yaml` 五个文件，无 `unified_rule_ir.yaml` |
| `C-2026-RF000421-坤-甲申丙寅己巳己巳` | `M2-Y-003` | `theory/yang/index.yaml` | 格式不可解析 | 只有路径没有行号；文件本身存在（4901 行） |
| `C-2026-RF000421-坤-甲申丙寅己巳己巳` | `ZP-PROD-20260622-032` | `theory/ziping/index.yaml` | 格式不可解析 | 同上；文件存在（38302 行） |
| `NEW-P-2026-001` | (无) | `theory/yang/index.yaml` | 格式不可解析 | 同上 |
| `NEW-P-2026-001` | (无) | `theory/duan/index.yaml` | 格式不可解析 | 同上；文件存在（5006 行） |

**未修这些条目**——按任务卡要求交中枢决策。它们是历史数据问题，不是本次代码缺陷；
修 case 属于篡改冻结证据，明确禁止。

### 2.3 存量对 `theory/ziping/index-new.yaml` 的引用（T-107 关联）

T-107 BRIEF §3 记录 `index-new.yaml` 被 5 个冻结 case 引用。本次体检确认这些引用
**全部可达**（文件 8930 行，`:794-831`、`:832-868`、`:1630-1668`、`:1669-1708`、`:794`
均未越界），即 T-107「不得删除」的结论有可机检的新支撑。

### 2.4 体检工具

体检脚本写在会话临时目录（不入库），只读打开 JSON 与理论库文件、只计行数，
不写入任何路径。核心两个函数（`classify` / `iter_locations`）与实现版
`check_locator_reachability` 口径一致。

---

## 3. 实现策略（Step 2 结论）

**存量有 5 个失效 → 报警优先，不阻断。** 具体落成：

1. 新增 `check_locator_reachability(locator, repo_root=None) -> tuple[LocatorReachabilityFinding, ...]`：
   解析 `path:start-end` / `path:line`，支持 `;` 多目标；只读校验文件存在与行号范围，
   **无任何写操作、不抛异常**，无法解析的目标返回 `reachable=False` + 原因。
2. `TheoryEvidenceFinding` **只加不删**：新增 `locator_findings`、`locator_blocks_freeze`
   两个带默认值的字段；既有 `evidence_count` / `placeholder_only` / `blocks_freeze` / `note`
   四个字段与全部取值语义不变（既有的 209 行测试全绿佐证）。
3. `ContractGateResult` 新增 `locator_findings`、`locator_blocks_freeze`，现有字段不变。
4. **默认 `LOCATOR_REACHABILITY_BLOCKS_FREEZE = False`**：locator 不可达时
   `any_issue_found=True`、`summary` 明确列出失效目标与原因，但
   `blocking_reasons` 保持 `()`、`passes_gate` 保持 `True`。存量清零后可改 True 升级为硬门控。
5. 模块 docstring 原文写「本模块不读写任何文件」，与新行为矛盾，已改写为如实描述
   （除 locator 可达性校验外不读写；该校验只读行数）。

---

## 4. 实证：缺陷确已修复

对 `theory/ziping/index-new.yaml:794-831` 用临时空仓库根模拟「文件已删除」：

```
simulated deleted index-new.yaml ->
   reachable = False | reason = 文件不存在：theory/ziping/index-new.yaml
```

修复前该引用无论指向何处都一律通过（`check_theory_evidence` 只查非空+非占位）。
T-107 记录的「删掉 index-new.yaml 后 pytest 依然全绿、审计溯源静默断掉」这一盲区
现在有机器可检的出口。

---

## 5. 验证原始输出

### 5.1 体检（§2 数字来源）

```
freeze files scanned                : 43
cases with theory_evidence list    : 19
theory_evidence dict entries       : 59
total locator strings              : 59
total path:line targets            : 60
  OK        = 55
  MISSING   = 1
  OVERFLOW  = 0
  UNPARSED  = 4
VERDICT: 存量有失败 → 报警优先，不阻断
```

### 5.2 交叉验证（用真实冻结包数据驱动门禁）

```
cases with theory_evidence evaluated : 19
cases the hard gate BLOCKS          : 0 -> []
cases with locator alarm (advisory) : 3
    C-2026-RF000421-坤-甲申丙寅己巳己巳: 2/2 unreachable
    C-2026-RF000900: 1/4 unreachable
    NEW-P-2026-001: 2/9 unreachable
cases fully clean                   : 16
```

**0 个 case 被阻断** —— 报警模式没有误伤任何既有冻结包。报警的 3 个 case
与 §2.2 失效条目一一对应（第 4、5 条同属 NEW-P-2026-001）。

### 5.3 测试

```
$ python -m pytest -q
........................................................................ [ 31%]
........................................................................ [ 62%]
........................................................................ [ 94%]
.............                                                            [100%]
229 passed in 14.13s
```

229 passed，与 T-107 记录的基线（229 passed）完全一致 —— 新增校验未造成任何回归。

```
$ python -m pytest tests/tools -q -o addopts=""
........................................................................ [ 24%]
........................................................................ [ 48%]
........................................................................ [ 73%]
........................................................................ [ 97%]
......                                                                  [100%]
294 passed in 81.26s
```

```
$ python -m pytest tests/tools/test_locator_reachability.py -q -o addopts=""
......................                                                   [100%]
22 passed in 0.19s
```

22 个新测试覆盖：真实 YAML 可达 / 单行号 / 末行边界 / 多目标拆分、文件缺失 / 行号越界 /
无行号 / 逆序区间 / 0 行号、报警不阻断（`passes_gate` True + `blocking_reasons` 空）、
无 locator 证据行为不变、占位分支阻断语义不受影响、`repo_root` 显式与缺省一致、
只读性（不创建目录或文件）、`TheoryEvidenceFinding` 旧字段可读。

### 5.4 `git status --porcelain`

本任务触及 3 个路径：

```
 M tools/as_of_contract_gate.py
?? tasks/T-110/
?? tests/tools/test_locator_reachability.py
```

其余条目均为其它任务遗留（与 T-107 BRIEF §2.3 记录一致），本任务未触碰：

- ` M cases/C-2026-035-*/manifest.json`、` M cases/C-2026-036-*/manifest.json`：
  mtime `2026-10-19 22:16`，本任务 00:02 才开始，且 diff 内容是 pytest 临时目录路径
  （`pytest-of-Administrator/pytest-697/test_preprod_builds_r10_run_fr0`），属 r10 预生产流程产生。
  **本任务对 `cases/` 零写入**（体检脚本只 `read_text`）。
- ` M .gitignore`、`D  plans/...crx`、`D  theory/_light_index.json`、
  `D  theory/*/_extracted_rules.json`、` M engine/v5/preprod.py`、` M tools/render_report_v6.py`、
  ` M tests/v5/*`、` M tests/r10/*`、`?? tests/v5/test_manifest_isolation.py`、
  `?? tasks/T-106..T-109/`：T-104 / T-106 / T-107 等任务既有改动。

`theory/` 与 `cases/` 下没有任何由本任务产生的改动。

---

## 6. 未完成与风险

### 6.1 5 个失效 locator 待中枢决策（不阻断交付的理由）

见 §2.2。建议后续动作（**本任务未执行**）：

- `C-2026-RF000900` 的 `theory/_ir/unified_rule_ir.yaml:46449-46478`：
  文件确已不在 `theory/_ir/`。需确认是改名（`ziping_rule_ir.yaml`？）还是该文件被
  T-107 清理流程误删，再决定补文件还是改 case 引用。
- 4 个「只有路径没有行号」：写这些 case 时可能只记录了文件级出处。补行号即可，
  但属修改冻结证据，须中枢授权。
- **存量清零后**把 `LOCATOR_REACHABILITY_BLOCKS_FREEZE` 改 `True`，并在
  `tests/tools/test_locator_reachability.py` 补一个阻断模式的测试。

### 6.2 范围说明

locator 校验只覆盖 `theory_evidence[].locator`。冻结包里其它 `locator` 键
（`natal_capacity_graph.*`、`frozen_event_candidates.*.annual_trace.*` 等）语义是
**包内图节点路径**而非仓库文件路径，刻意不纳入校验；本文 §2 开头已说明为何
不能用全文扫描口径统计。

### 6.3 性能

`check_locator_reachability` 每次调用都对目标文件做一次全量行数统计
（读整个文件）。`index.yaml` 38302 行，59 个 locator 实测 `tests/tools`
294 passed in 81.26s，未成为瓶颈；若未来 locator 数量级上升，
可加按 `(path, mtime, size)` 的行数缓存。
