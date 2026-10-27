# T-130 · 案例排盘口径普查 — BRIEF

**执行人**：子代理（Worker）
**完成时间**：2026-10-27
**依据**：`tasks/T-130/PROMPT.md` + `docs/adr/ADR-005-case-time-basis.md`
**结论**：485 例全部落三值之一，`--json` 退出码 0，`cases/` 零改动。

---

## 1. 改动文件

| 文件 | 类型 | 说明 |
|---|---|---|
| `tools/case_time_basis_audit.py` | 新建 | 普查器。仅依赖标准库（`argparse/json/re/sys/pathlib`），不 import 引擎，不做任何真太阳时换算 |
| `META/case-time-basis-v1.json` | 新建（产物） | 485 例逐例清单 + 分档计数 + 每例判定依据（`evidence` 数组可逐例复查） |
| `tasks/T-130/BRIEF.md` | 新建 | 本文件 |
| `tasks/T-130/STATUS.md` | 新建 | 执行状态 |

**未改动**（硬约束已核）：`cases/` 下所有文件、`theory/`、`sources/`、`engine/`、`tools/README.md`、`pyproject.toml`。

`git status --porcelain cases/` 输出为空（见 §2.4）。

### 判定规则的实现映射（全部来自 ADR-005，未发明第四种口径）

| 元数据写法 | 信号 | `time_basis` | `basis_evidence` |
|---|---|---|---|
| 表格注记 `（真太阳时）`/`（已校真太阳时）`/`（真太阳时·辰时）` | 出生行内标注 + 该行有具体时刻 | `true_solar` | `explicit_time` |
| 表格注记 + 出生地经度 | `江西九江（116°E）` + `校正约 16:37` | `true_solar` | `longitude_calc` |
| 结构化字段 `真太阳时校正: true` + `太阳时:` 值 | 有校正后时刻 | `true_solar` | `explicit_time` |
| 结构化字段 `真太阳时校正: true`，无 `太阳时` 值 | 只有标记 | `true_solar` | `label_only` |
| 结构化字段 `真太阳时校正: false` | 明示未校正 | `clock_beijing` | `none` |
| 结构化字段 `真太阳时校正: 未知` / `是否真太阳时：未知` | 明示未知 | `unknown` | `none` |
| 导入器 `时间来源: true_solar_time_raw` + `真太阳时字段优先: true` | 来源字段即真太阳时 | `true_solar` | `explicit_time` |
| 导入器 `时间来源: birth_datetime_raw` + `真太阳时字段优先: false` | 明示只取原始钟表时间 | `clock_beijing` | `none` |
| 导入器 `时间来源: none` | 无出生时刻 | `unknown` | `none` |
| 第四种（ADR 未列举）：`$BASE` 段 `Solar:`/`Sun:` | `Sun:` = 真太阳时 | `true_solar` | `explicit_time` |
| 第四种：手写 `- 太阳时：<时刻>` / `| 太阳时 | <时刻> |` | 直接给出太阳时 | `true_solar` | `explicit_time` |
| 太阳时字段自我否定 `（与公历同，未做地理校正）`/`未校正` | 写了字段但明示没校正 | `clock_beijing` | `none` |
| **沉默**（有公历时刻，无一字提及口径） | — | `unknown` | `none` |

两条硬规则已落实：
- **沉默一律 `unknown`**，绝不默认 `clock_beijing`（C-2026-002、C-2026-007 即此类）。
- **矛盾一律 `unknown`**（ADR-005 §2「证据互相矛盾无法判定」）。

---

## 2. 原始输出

### 2.1 验收命令（PROMPT §4）

```powershell
PS> .venv\Scripts\python.exe -m tools.case_time_basis_audit --json
```

**退出码 0**，stderr 为空。stdout 前 34 行（元数据块，其后是 `cases` 数组，共 5218 行）：

```json
{
  "schema": "case-time-basis-v1",
  "adr": "docs/adr/ADR-005-case-time-basis.md",
  "task": "T-130",
  "cases_dir": "cases",
  "coverage": 485,
  "counts": {
    "true_solar": 330,
    "clock_beijing": 144,
    "unknown": 11
  },
  "counts_sum": 485,
  "basis_evidence_counts": {
    "longitude_calc": 1,
    "explicit_time": 326,
    "label_only": 3,
    "none": 155
  },
  "notation_counts": {
    "other": 14,
    "table_note": 7,
    "structured_field": 119,
    "importer_field": 345
  },
  "unknown_breakdown": {
    "no_birth_time": 5,
    "has_time_undecidable": 6
  },
  "duplicate_case_numbers": [
    "C-2026-015",
    "C-2026-038"
  ],
  "cases": [
    {
```

### 2.2 `--summary`（PROMPT §4 第 4 条）

```powershell
PS> .venv\Scripts\python.exe -m tools.case_time_basis_audit --summary
```

```text
T-130 案例排盘口径普查（依据 ADR-005）
覆盖数：485

time_basis 分档：
+----------------+--------+---------+
| 档位           | 例数   | 占比    |
+----------------+--------+---------+
| true_solar     |    330 |  68.0% |
| clock_beijing  |    144 |  29.7% |
| unknown        |     11 |   2.3% |
+----------------+--------+---------+
| 合计           |    485 |         |
+----------------+--------+---------+

basis_evidence 分布：
  longitude_calc        1
  explicit_time       326
  label_only            3
  none                155

元数据写法分布：
  importer_field      345
  structured_field    119
  other                14
  table_note            7

unknown 细分：
  确实无出生时刻             5
  有时刻但判不了             6

同一案例号多目录：C-2026-015、C-2026-038
```

退出码 0。

### 2.3 覆盖数与产物自校验

```powershell
PS> (Get-ChildItem cases -Directory | ? { Test-Path (Join-Path $_.FullName 'input.md') }).Count
485
```

产物复核（读 `META/case-time-basis-v1.json`）：

```text
artifact cases: 485
counts sum   : 485 / coverage 485
evidence sum : 485
notation sum : 485
unique ids   : 485
illegal rows : 0
```

### 2.4 案例零改动证明（PROMPT §4 第 5 条）

```powershell
PS> git status --porcelain cases/
PS> echo $LASTEXITCODE
0
```

输出为空。整个仓库的 `git status --porcelain` 中与本任务相关的只有两行新增：

```text
?? META/case-time-basis-v1.json
?? tools/case_time_basis_audit.py
```

（其余 `M`/`??` 项属其他任务的既有改动，非本 Worker 所为。）

### 2.5 回归

```powershell
PS> .venv\Scripts\python.exe -m pytest -q -o addopts="-ra --tb=short" tests/facts tests/api tests/predicates `
     tests/tools/test_query_theory.py tests/tools/test_human_touch_linter.py tests/tools/test_blind_ledger.py `
     tests/tools/test_anchor_span.py tests/tools/test_blind_toolchain.py tests/tools/test_gao_split.py `
     tests/test_project_metadata.py
238 passed in 12.34s
```

退出码 0。本任务纯新增文件，未触碰既有实现。

---

## 3. 未完成与风险

### 3.1 需中枢裁定的 4 处（按影响从大到小）

**(1) `_TEMPLATE` 被计入 485。**
`cases/_TEMPLATE/input.md` 存在，按 PROMPT §4 第 1 条「覆盖数 == `cases/*/input.md` 的目录数」必须计入，实测目录数正好 485。但它是模板不是案例（内容为 `Case C-YYYY-NNN` 占位），因此被判 `unknown` / `none` / `no_birth_time`。
→ 若中枢认定不应计入，真实案例数为 **484**，`unknown` 11→10、`no_birth_time` 5→4，且 PROMPT 的「当前为 485」需改成 484。

**(2) `C-2026-032`、`C-2026-033` 判 `unknown`（矛盾），可一句话改判。**
这两例同时有手写 `是否真太阳时：未知，按用户提供问真八字排盘结果执行` 与结构化 `真太阳时校正: false`。按 ADR-005 §2「证据互相矛盾无法判定」取 `unknown`（也是「宁可标低」方向）。
→ 若以结构化字段 `false` 为准，则 `unknown` 11→9、`clock_beijing` 144→146，其余不变。

**(3) 4 例仅凭「太阳时 / `Sun:` 字段值」判 `true_solar`，无独立「校正: true」声明。**
`C-2026-014`、`C-2026-018`、`P-2026-001`、`P-GO-2026-001`。判 `true_solar` + `explicit_time` 的理由：ADR-005 §4 定义 `explicit_time` = 「案例内直接给出校正后的具体时刻」，这四例都直接给出了一行 `太阳时`/`Sun:` 具体时刻；`Sun:` 的语义已由仓库内文档确认（`cases/C-2026-017/lessons.md:78`：`| \`Sun:...\` | 真太阳时 | \`solar_true\` |`）。
→ 若中枢要求「必须有独立的校正声明才算」，这 4 例降为 `unknown` / `none`，则 `true_solar` 330→326、`explicit_time` 326→322、`unknown` 11→15。

**(4) ADR-005 只列举了三种元数据写法，实测存在第四种。**
`$BASE` 文本段的 `Solar:` / `Sun:` 字段（`P-2026-001`、`P-GO-2026-001` 等 12 例）+ 手写 `- 太阳时：` 行（`C-2026-014`、`C-2026-018`、`C-2026-034` 等）。我按字段语义处理，**没有发明新的 `time_basis` 值**，仍落 ADR 的三值四证据；但 ADR 背景第 2 条「三种互不兼容写法」的表述已不完备，建议下一版 ADR 补一句。这属于 ADR 修订，不在本卡 File Scope 内，未动 `docs/adr/`。

### 3.2 已知不完美

**(5) `tool_registry --check` 在我改动前已是红的。**
`tools/tool_registry.py` 会 `glob("*.py")` 并把未登记在 `tools/README.md` 的工具报为 `UNINDEXED`。实测改动前已有 14 个既有工具在列（`engine_audit.py`、`relations_audit.py`、`human_touch_linter.py`、`verify_baseline.py`、`zuogong_probe.py` 等），退出码 1。新增的 `case_time_basis_audit.py` 让该清单多 1 项。
→ 未改 `tools/README.md`，因为它不在本卡 File Scope（卡内只授权新建 `tools/case_time_basis_audit.py`）。需中枢授权后补登记。

**(6) 未逐例人工复核全部 485 例。**
判定是规则驱动的，靠三层证据兜底：① 全量关键词频次普查（覆盖所有出现过的写法，含 56 种只出现一次的写法）；② 分桶明细逐条目视（`unknown` 11 / `longitude_calc` 1 / `label_only` 3 / `table_note` 7 / `other` 14 全部人工过目）；③ 5 例精抽（见 §4.4）。每例的 `evidence` 数组已把命中的规则写进 JSON，可逐例复查。
已修掉一个真实缺陷：初版只检查第一条出生行，漏掉 `C-2026-016` 第二行的 `公历：1984-12-18 00:50（真太阳时）`，把它误判为 `label_only`；修正后为 `explicit_time`（`label_only` 4→3）。全库仅此 1 例存在「标注不在首条出生行」。

**(7) 导入器 215 例的 `经度校正: false` 不是矛盾，已在语义上说清。**
这些案例同时有 `经度校正: false` + `经度校正说明: "本模块未做…换算"` + `时间来源: true_solar_time_raw`。读法：**本模块没换算，但来源字段本身就是真太阳时**，故判 `true_solar` / `explicit_time`，不判 `label_only`（因为它给得出具体校正后时刻）。若中枢认为「上游声称」不足为凭、必须本仓库可复现，这 215 例需整体降级 —— 但这会让 `true_solar` 只剩 115 例，与 ADR-005 背景的 104+ 量级也不再吻合，故未采用。

**(8) 同一案例号存在多目录。**
`C-2026-015` 有 `C-2026-015-乾-甲寅乙亥丙辰辛卯` 与 `C-2026-015-甲寅乙亥丙辰辛卯` 两个目录（内容近似，均 `label_only`）；`C-2026-038` 有 `C-2026-038-乾-庚辰己卯壬午丙午`（`unknown`）与 `C-2026-038-乾-辛卯壬辰己未庚午`（`clock_beijing`）两个目录，八字不同。故 485 个目录只对应 483 个独立案例号。清单以**目录名**作 `case_id` 以保证 485 条唯一。

---

## 4. 下游须知

### 4.1 怎么消费产物

`META/case-time-basis-v1.json` 顶层即分档计数，`cases[]` 逐例：

```json
{ "case_id": "C-2026-010-坤-甲子丁卯癸卯庚申",
  "time_basis": "true_solar",
  "basis_evidence": "longitude_calc",
  "notation": "table_note",
  "unknown_kind": null,
  "evidence": ["出生行标注 （北京时间 · 真太阳时校正约 16:37 → 申时）", "有出生地经度 + 可复现换算"] }
```

- `time_basis` 直接喂 B4 分层验证，**不要另建口径**（ADR-005 §后果）。
- `basis_evidence=label_only` 的 3 例（`C-2026-015`×2、`C-2026-022`）**保留在 `true_solar` 层但标低可信度**，不丢弃（ADR-005 §4）。

### 4.2 分层红线的具体数字

- 时柱敏感断语（宫位、穿、合、时支藏干、时柱十神、时柱长生）**只允许在 330 例 `true_solar` 层验证**。
- `clock_beijing` **144 例**只验证与时辰无关的断语（日主强弱、日支、年月柱、十神结构）。
- `unknown` **11 例**不得用于任何时柱相关断语。
- 跨层合并统计必须写明两层的样本数与混合比例（330 : 144）。
- 其中 `longitude_calc` 仅 **1 例**（`C-2026-010`）——若 B4 想要「最强证据子集」，就是它。

### 4.3 重跑与改判

```powershell
.venv\Scripts\python.exe -m tools.case_time_basis_audit            # 摘要并刷新产物
.venv\Scripts\python.exe -m tools.case_time_basis_audit --summary  # 分档计数表
.venv\Scripts\python.exe -m tools.case_time_basis_audit --json     # 机器可读（验收命令）
.venv\Scripts\python.exe -m tools.case_time_basis_audit --case C-2026-010   # 单例明细
.venv\Scripts\python.exe -m tools.case_time_basis_audit --out X.json        # 换产物路径
.venv\Scripts\python.exe -m tools.case_time_basis_audit --no-write          # 只看不写
```

内部自校验：覆盖集必须与 `cases/*/input.md` 目录集合逐一相等、`case_id` 不得重复、取值必须在允许集合内、三档之和必须等于覆盖数；任一不满足即**退出码 1** 并在 stderr 打 `[FAIL]`。

**改判只改 `classify()` 里对应的那条规则，不要手改 JSON** —— 手改会在下次重跑时被覆盖。

### 4.4 抽核的 5 例（含判定理由）

| # | 案例 | 判定 | 理由（已读原文件核对） |
|---|---|---|---|
| 1 | `C-2026-010-坤-甲子丁卯癸卯庚申` | `true_solar` / `longitude_calc` | 全库唯一给出出生地经度的一例：`\| **出生地** \| 江西九江（116°E）\|`；出生行 `1984-03-10 17:03（北京时间 · 真太阳时校正约 16:37 → 申时）` 同时给出钟表时刻与校正后时刻，方向一致（校正后更早），换算可复现 → 四项证据里最强档 |
| 2 | `C-2026-016-坤-甲子丙子丙戌戊子` | `true_solar` / `explicit_time` | `真太阳时校正: true`，且第二条出生行 `公历：1984-12-18 00:50（真太阳时）` 直接把该时刻标为真太阳时 → 属「案例内直接给出校正后的具体时刻」，不是 `label_only`。**此例正是初版工具漏检、修正后才对的** |
| 3 | `C-2026-017-乾-庚申辛巳辛丑丁酉` | `clock_beijing` / `none` | 最容易误判的一例：表里有 `\| 真太阳时 \| 1980-05-28 17:15（与公历同，未做地理校正） \|`，字面像已校正，但括注**自我否定**（与公历同、未做地理校正）→ 只有钟表时间。故不因「有真太阳时字样」就标高 |
| 4 | `C-2026-RF000001-坤-己卯辛未丙寅乙未` | `true_solar` / `explicit_time` | 导入器写法代表：`时间来源: true_solar_time_raw` + `真太阳时字段优先: true`，同时 `经度校正: false` + `经度校正说明: "本模块未做…换算"`。读法为「本模块没换算，取的是来源里本就是真太阳时的那个字段」→ 不是矛盾，判 `true_solar` |
| 5 | `C-2026-032-乾-癸酉乙卯戊戌甲寅` | `unknown` / `none` | 矛盾代表：L8 `是否真太阳时：未知，按用户提供问真八字排盘结果执行` 与 L70 `真太阳时校正: false` 对同一问题给了不同答案 → 按 ADR-005 §2 落 `unknown`（`unknown_kind=has_time_undecidable`）。**此判定可由中枢一句话改判为 `clock_beijing`**，见 §3.1(2) |

补充抽核（非计数入表，但已核对）：`C-2026-021`（无出生时刻，只有「约 1986 年寅月」→ `unknown`/`no_birth_time`）、`C-2026-022`（`真太阳时校正: true` 但全文无 `太阳时` 值、无经度 → `label_only` 的标准样本）。

### 4.5 回答 PROMPT §5 要求的全部数字

- 三档计数：`true_solar` **330** / `clock_beijing` **144** / `unknown` **11**，合计 **485** = 覆盖数。
- `basis_evidence` 四值：`longitude_calc` **1** / `explicit_time` **326** / `label_only` **3** / `none` **155**，合计 485。
- `unknown` 细分：确实无出生时刻 **5**（`_TEMPLATE`、`C-2026-021`、`C-2026-RF000009/29/668`）；有时刻但判不了 **6**（`C-2026-002`、`C-2026-007`、`C-2026-031`、`C-2026-032`、`C-2026-033`、`C-2026-038-乾-庚辰己卯壬午丙午`）。
- 三种写法命中数：表格注记 **7**、结构化字段 **119**、导入器字段 **345**；ADR 未列举的其余写法 **14**（含 `$BASE` `Solar:`/`Sun:`、手写 `太阳时` 行、无出生时刻案例）。合计 485。
