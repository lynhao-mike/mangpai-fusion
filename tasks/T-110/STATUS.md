# T-110: 修 locator 校验缺口 — Status

**Status:** ✅ Complete
**Current Step:** Step 3 完成（实施 + 测试 + 验证）
**Last Updated:** 2026-10-20
**Iteration:** 1
**Size:** M

> 任务卡由中枢写好，Worker 只读卡执行，**不要自己写 PROMPT.md**。
> Step 1 的存量体检数字是本任务最重要的产出——见 `BRIEF.md` §2。

---

## 核心结论

**缺陷已修复；存量体检发现 5 个失效 locator（1 文件缺失 + 4 格式不可解析），
据此走「报警优先、不阻断」。229 passed，零回归。**

存量总账：43 个冻结包 / 19 个有 `theory_evidence` / 59 个 locator 字符串
/ 60 个目标 → **OK 55、缺失 1、越界 0、不可解析 4**。明细与策略推导见 `BRIEF.md` §2。

---

### Step 0: 读现有实现
**Status:** ✅ Done

- [x] check_theory_evidence 全文（原 :259-293）
- [x] `_evidence_texts`（原 :246-258）——确认只做文本叶节点提取，与 locator 无关
- [x] `TheoryEvidenceFinding`（原 :110-119）——四字段：count / placeholder_only / blocks_freeze / note
- [x] run_contract_gate 调用方式（原 :294+）——`blocks_freeze` 是 `blocking_reasons` 的唯一来源；
      `any_issue_found` 另有 advisory 通道，locator 报警走这条，实现为不翻转 passes_gate

### Step 1: 存量体检（先做，不改代码）
**Status:** ✅ Done

- [x] 扫描所有 asof-blind-freeze.json（43 个）
- [x] 统计 总 locator / 文件缺失 / 行号越界 / 健康
- [x] 列出失效具体条目

**关键口径修正**：只统计 `theory_evidence[].locator`。全文 `locator` 键扫出来上百个
「失效」几乎全是假阳性——`natal_capacity_graph` / `frozen_event_candidates` 里的
`locator` 表示包内图节点路径（如 `career.domain_nodes`、`year[2026].relations[0]`），
不是仓库文件路径。数字以 `theory_evidence` 口径为准。

### Step 2: 定实现策略
**Status:** ✅ Done

- [x] ~~存量 0 失败 → 阻断式~~
- [x] **存量有失败 → 报警优先，不阻断**（实测 5 个失效，走这条）

### Step 3: 实施
**Status:** ✅ Done

- [x] 新增校验，旧字段不删（`TheoryEvidenceFinding` 只加 `locator_findings` /
      `locator_blocks_freeze`，两者都有默认值，构造顺序不变）
- [x] 新增 test_locator_reachability.py（22 tests，全绿）
- [x] 模块 docstring「不读写任何文件」改写为如实描述（该校验只读行数）

---

## Execution Log

| Timestamp | Action | Outcome |
|---|---|---|
| 2026-10-19 | Task staged | 中枢写卡 |
| 2026-10-20 | Step 0 读实现 | 确认 `check_theory_evidence` 无任何文件可达性检查 |
| 2026-10-20 | Step 1 存量体检 | 59 locator / 60 target：OK 55、MISSING 1、OVERFLOW 0、UNPARSED 4 |
| 2026-10-20 | Step 2 定策略 | 存量有失败 → 报警优先，不阻断 |
| 2026-10-20 | Step 3 实施 | `check_locator_reachability` + 接入两函数；新测试 22 passed |
| 2026-10-20 | 交叉验证 | 19 个真实 case 驱动门禁，0 个被阻断、3 个报警（与失效条目一致） |
| 2026-10-20 | 缺陷场景复现 | 模拟删除 `index-new.yaml` → `reachable=False`，盲区已封 |

---

## Blockers

*None*

## 待中枢决策（不在本任务范围）

1. **5 个失效 locator 的处置**（`BRIEF.md` §2.2 / §6.1）：
   `C-2026-RF000900` 指向的 `theory/_ir/unified_rule_ir.yaml` 确已不存在；
   另 4 个是「只有路径没行号」。修 case 属改冻结证据，需授权。
2. **存量清零后**将 `LOCATOR_REACHABILITY_BLOCKS_FREEZE` 改 `True` 升级为硬门控，
   并补阻断模式测试。
