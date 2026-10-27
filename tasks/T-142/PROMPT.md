# T-142 · 原子层修复包：原局/岁运隔离、he_at、binzhu、lu_at、needs_judgment、_label

- 状态：🔵 Ready for Execution
- 优先级：**P0**
- 创建：2026-10-27（中枢）
- 决策依据：ADR-007 D3 / D5 / D12
- **前置：T-140 与 T-141 必须已完成并合入**（本卡不依赖它们的代码，但同一批验证要一起看）

## 1. 本卡要修六件事（全部在 `engine/claims/condition_ir/atoms.py`）

### ① 原局原子必须隔离岁运边（否则污染）

`engine/facts/relation_graph.py:85` 的 `_nodes(chart, dayun_index, liunian_year)` 已经能建 `DY{n}.s/b`、`LN{year}.s/b` 节点与边，并给边打 `scope ∈ {natal, dayun, liunian, dayun+liunian}`。

但 `atoms.py` 里所有关系原子**都没有过滤 scope**。一旦有人给 `analyze_facts` 传了岁运参数，原局静态断语会被流年干支错误点燃。

**要求**：以下原子默认只扫 `e.get("scope", "natal") == "natal"` 的边：
`edge`、`edge_touches`、`chong_at`、`he_at`、`chuan_at`、`xing_at`、`po_at`、`group_complete`、`muku_open`。

`edge` 若显式传 `scope` 参数则按参数匹配（保留岁运查询能力）。

### ② `he_at` 定义过宽（这是重大 bug）

现在 `HE_KINDS = ("liuhe", "wuhe", "zhi_anhe", "sanhe", "sanhui", "ganzhi_zihe")`。

实测后果：`he_at(D.b)` 在 481 盘命中 **412 盘（85.7%）**。其中真正的合只有 `liuhe` 70、`zhi_anhe` 48；其余全是
`sanhui:partial` 134、`sanhe:half_sheng/half_mu/gong` 155、`ganzhi_zihe` 5。

原文（`sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:48`）说的是：
「不能被刑坏，冲破，穿倒，**或六合，暗合他星**」——只提六合与暗合（且是合**他星**）。

**要求**：
- 默认只认 `liuhe`（六合）与 `zhi_anhe`（地支暗合）。
- **排除** `sanhe`/`sanhui` 中 `completeness ∈ {partial, half_sheng, half_mu, gong}` 的**半局/拱局**。
- **排除** `ganzhi_zihe`（日柱自合，不涉他星）。
- `sanhe`/`sanhui` 的 **full（完整三合/三会）**是否算「被合」：**你必须查原文给出结论并写进 BRIEF**。若原文无据，保持排除，并在卡里标注「待中枢裁定」。
- 允许传 `exclude_god`（例如排除配偶星本星相合），默认不启用。

### ③ `binzhu` 原子目前是空壳

`atoms.py:517` 现在恒返回 `_u("facts 未提供宾主层级")`。但宾主**早已实现**于
`engine/facts/chart_facts.py:125 binzhu_side()` 与 `structure_check.py:395-406 _binzhu()`。

**要求**：让 `binzhu` 原子真正读事实（T-140 会把它透出到 facade），不再恒返回未知。

### ④ 新增 `lu_at` 原子（禄）

「禄」**早已在事实层**：`engine/facts/chart_facts.py:67 _LU`（甲禄寅、乙禄卯、丙戊禄巳、丁己禄午、庚禄申、辛禄酉、壬禄亥、癸禄子）。

**要求**：新增 `lu_at(ctx, args)`，参数 `gan`（可选，默认日主）、`at`（可选，限定某个地支地址）。语义：该天干的禄支是否落在指定/任一地支上，命中返回 `_t` 并绑定地址。

这一段让 `M2-Y-017`（人生三宝印食禄）脱离 `needs_human` 成为可能。

### ⑤ 新增 `needs_judgment` 原子（显式未知占位）

恒返回 `_u(reason)`，参数 `reason`（必填，说明缺什么判断）。

**为什么需要它**：现在 `pilot-20.yaml` 有断语把「不会算的条件」直接删进 `unmapped_prose` 再标 compiled，导致未知率恒为 0（ADR-007 D12 判定的设计失效）。有了这个原子，就能把「不会算的部分」显式挂在条件树里：

- 前置客观条件为 `False` → `False AND Unknown = False` → `rejected`（过滤不相关盘）
- 前置为 `True` → `True AND Unknown = Unknown` → `needs_fact`（推给 Agent）

### ⑥ `_label()` 输出不可读（`?()`）

`ir.py:30-35` 的 `_label()` 只认 `node.get("atom")`，遇到 `{"not": {...}}` / `{"any": [...]}` 就输出 `?()`。
实测 `M1-D-298` 失败时给出 `failed=['?()']`，**人无法追责到具体哪个子条件**。

**要求**：`_label()` 支持 `all` / `any` / `not` 组合节点，递归输出可读标签。

## 2. 关于 `assert len(ATOMS) == 42`

`atoms.py:684` 有 `assert len(ATOMS) == 42`。新增 `lu_at`、`needs_judgment` 后数量会变。

**正确做法**：
1. 先改契约 `engine/contracts/23-claim-condition-protocol-v1.md` 的原子表，写明新增两个原子的理由与签名；
2. 再改断言，并在提交信息里说明「契约新增原子的依据」。

**禁止**为了让测试变绿而直接把 42 改成 44 而不改契约。那是改断言让红变绿。

## 3. File Scope

- `engine/claims/condition_ir/atoms.py`（主）
- `engine/claims/condition_ir/ir.py`（仅 `_label`）
- `engine/contracts/23-claim-condition-protocol-v1.md`（原子表）
- 对应测试（`tests/claims/`）

**禁止**：改 `engine/api/facade.py`（T-140 的活）、`engine/facts/`（T-141 的活）、`theory/claims/**`（T-143 的活）、`theory/_ir/`、`sources/`、`pyproject.toml`；git 破坏性操作。

## 4. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m tools.verify_baseline
```

**必须自证**：
1. `he_at(D.b)` 在 481 盘上的命中数从 412 降到多少（给出具体数字与各 kind 明细）。
2. 构造一例：传入 `liunian_year` 后，`chong_at(H.b)` 等**原局原子仍返回原局结果**（未被岁运边污染）；同时 `edge(scope=...)` 能查到岁运边。
3. `lu_at` 对 3 个不同日主给出正确禄支（与 `chart_facts._LU` 一致）。
4. 构造一条含 `needs_judgment` 的条件，验证 `True AND Unknown = Unknown`、`False AND Unknown = False`。
5. `_label` 对 `{"not": {...}}` 输出可读字符串，不再出现 `?()`。

## 5. 回报格式

六个子项各自改了什么；`he_at` 改前改后的 481 盘命中数与 kind 明细；ATOMS 从 42 变成几、契约怎么改的；五个自证项的原始输出；两条验收命令的数字与退出码。

**若发现本卡任一条与代码事实不符，停下报告，不要自行扩大范围。**
