# T-130: 案例排盘口径普查（A1 收口） — Status

**Status:** ✅ Done（数字自洽，退出码 0，待中枢裁定 4 处分歧）
**Current Step:** Step 5 验收已跑
**Last Updated:** 2026-10-27
**Iteration:** 1
**Size:** M
**Executor:** 子代理（Worker）

> 任务卡由中枢写好，Worker 只读卡执行，**未改 PROMPT.md**。
> 本轮为只读普查，`cases/` 零改动，未碰 `theory/`、`sources/`、`engine/`。

---

### Step 1: 读卡与口径消化
**Status:** ✅ Done

- [x] 读 `tasks/T-130/PROMPT.md` 与 `docs/adr/ADR-005-case-time-basis.md`
- [x] 确认判定只允许三值 `true_solar` / `clock_beijing` / `unknown`，证据只允许四值 `longitude_calc` / `explicit_time` / `label_only` / `none`
- [x] 确认两条硬规则：沉默一律 `unknown`（不得默认 `clock_beijing`）；矛盾一律 `unknown`
- [x] 确认「引擎零改动」是 ADR-005 §1 的既定结论，本任务不碰 `engine/`

### Step 2: 全量摸底三种（实为四种）元数据写法
**Status:** ✅ Done

- [x] 目录数核对：`cases/` 共 527 个目录，其中含 `input.md` 的 **485** 个，与 PROMPT 声明一致
- [x] 全量行频次普查（48438 行，2552 条时间相关行），归一化后梳理出全部写法，含 56 种只出现一次的写法
- [x] 三种 ADR 列举写法实测命中：表格注记 7、结构化字段 119、导入器字段 345
- [x] 发现 ADR 未列举的**第四种**：`$BASE` 文本段 `Solar:` / `Sun:`（`Sun` = 真太阳时，语义经 `cases/C-2026-017/lessons.md:78` 证实）+ 手写 `- 太阳时：` 行，共 14 例
- [x] 经度类证据全库仅 **1** 例（`C-2026-010`，`116°E`）

### Step 3: 实现 `tools/case_time_basis_audit.py`
**Status:** ✅ Done

- [x] 只依赖标准库，不 import 引擎，不做任何换算
- [x] 判定链：无出生时刻 → 矛盾 → 明示钟表 → 明示校正 → 仅太阳时字段值 → 明示未知 → 沉默
- [x] 内置自校验：覆盖集逐一对齐、`case_id` 不重复、取值合法、三档之和 == 覆盖数；不满足则退出码 1
- [x] 每例输出 `evidence` 数组，写明命中的是哪条规则，可逐例复查

### Step 4: 分桶逐条核对 + 修缺陷
**Status:** ✅ Done

- [x] 分桶明细逐条目视：`unknown` 11 / `longitude_calc` 1 / `label_only` 3 / `table_note` 7 / `other` 14
- [x] 导入器内部一致性：`真太阳时字段优先` 与 `时间来源` 345 例全部自洽，0 处不匹配
- [x] **修掉真实缺陷**：初版只检查首条出生行，漏掉 `C-2026-016` 第二条出生行的 `（真太阳时）` 标注，误判为 `label_only`；改为扫描全部出生行后修正为 `explicit_time`（`label_only` 4→3）。全库仅此 1 例
- [x] 抽核 5 例并读原文件核对（`C-2026-010`、`C-2026-016`、`C-2026-017`、`C-2026-RF000001`、`C-2026-032`）

### Step 5: 验收
**Status:** ✅ Done

- [x] `.venv\Scripts\python.exe -m tools.case_time_basis_audit --json` → **退出码 0**，stderr 空
- [x] 三档计数之和 330+144+11 = **485** == 覆盖数
- [x] `basis_evidence` 四值之和 1+326+3+155 = 485
- [x] `--summary` 打印分档计数表 ✓
- [x] `git status --porcelain cases/` 输出为空 ✓
- [x] 回归子集 `238 passed`，退出码 0

---

## Execution Log

| Timestamp | Action | Outcome |
|---|---|---|
| 2026-10-27 | 读 PROMPT.md + ADR-005 | 口径与硬规则确认 |
| 2026-10-27 | 统计 `cases/*/input.md` 目录数 | 527 目录 / 485 含 input.md |
| 2026-10-27 | 全量行频次普查 | 梳理出 3 种 ADR 写法 + 第四种 `$BASE`/`Solar:`/`Sun:` |
| 2026-10-27 | 经度证据扫描 | 全库仅 `C-2026-010` 1 例 |
| 2026-10-27 | 新建 `tools/case_time_basis_audit.py` | 只读普查器，含自校验 |
| 2026-10-27 | 首跑 `--summary` | 330/144/11；`label_only` 误为 4 |
| 2026-10-27 | 分桶核对发现 `C-2026-016` 漏检 | 修正为扫描全部出生行 |
| 2026-10-27 | 重跑 `--summary` | 330/144/11；证据 1/326/3/155 |
| 2026-10-27 | 验收命令 `--json` | 退出码 0，产物写入 `META/case-time-basis-v1.json` |
| 2026-10-27 | 回归子集 | 238 passed |
| 2026-10-27 | 写 BRIEF.md、本 STATUS.md | 本轮收口 |

---

## Blockers

无阻塞项。以下 4 处需中枢裁定，已写入 `BRIEF.md` §3.1，均不阻塞本任务交付：

**1. `_TEMPLATE` 计入 485**
`cases/_TEMPLATE/input.md` 存在，按 PROMPT §4 第 1 条「覆盖数 == `cases/*/input.md` 的目录数」必须计入（实测正好 485）。但它是模板不是案例，被判 `unknown`/`none`/`no_birth_time`。若认定不计入，真实案例 484，`unknown` 11→10。

**2. `C-2026-032`、`C-2026-033` 判 `unknown`**
两例同时有 `是否真太阳时：未知` 与 `真太阳时校正: false`，按 ADR-005 §2「证据互相矛盾无法判定」取 `unknown`。若以结构化字段 `false` 为准，则 `unknown` 11→9、`clock_beijing` 144→146。

**3. 4 例仅凭「太阳时 / `Sun:` 字段值」判 `true_solar`**
`C-2026-014`、`C-2026-018`、`P-2026-001`、`P-GO-2026-001`。依据 ADR-005 §4 `explicit_time` 定义 + 仓库内 `Sun:` = 真太阳时的文档。若要求必须有独立「校正: true」声明，这 4 例降为 `unknown`，`true_solar` 330→326。

**4. ADR-005 列举的「三种写法」已不完备**
实测存在第四种（`$BASE` 段 `Solar:`/`Sun:`、手写 `太阳时` 行）。我按字段语义处理，仍落 ADR 的三值四证据，未发明新口径；但建议下一版 ADR 补一句。属 ADR 修订，不在本卡 File Scope，未动 `docs/adr/`。

另记一处**既有**红灯（非本任务引入）：`tools/tool_registry.py --check` 在本轮改动前即退出码 1，已有 14 个工具未登记在 `tools/README.md`（`engine_audit.py`、`relations_audit.py`、`human_touch_linter.py`、`verify_baseline.py` 等）；新增的 `case_time_basis_audit.py` 让该清单多 1 项。未改 `tools/README.md`（不在 File Scope），需授权后补登记。

---

## Amendments

无需修订 PROMPT.md。任务卡规则（三值判定、四值证据、沉默→unknown、矛盾→unknown、覆盖必须全量）自洽且可执行，实测 485 例全部可判，无「无法判定」的死角 —— 4 处分歧均是**规则边界的选择**而非**规则缺失**，已按 ADR-005 字面取最保守侧，并给出改判后的数字供中枢一句话翻转。
