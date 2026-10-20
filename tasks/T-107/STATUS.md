# T-107: 仓库瘦身零风险项（误入库文件清理）— Status

**Status:** 🟡 部分完成 — 3 项已删并验证，第 4 项因前提不成立已停止
**Current Step:** Step 4 完成；等中枢裁决 `index-new.yaml` 去留
**Last Updated:** 2026-10-19
**Iteration:** 1
**Size:** S

---

### Step 0: 核实 4 项
**Status:** ✅ Completed

- [x] 确认 5 个文件存在及大小（1.6M crx / 7.0M light_index / 3.0M+2.7M extracted / 325K index-new）
- [x] `git ls-files` 确认 5 个文件全部被跟踪
- [x] grep 全仓库区分「写它的脚本」与「读它的代码」
      —— `_extracted_rules.json` 只有 `OUTPUT_JSON` 写入（`extract_*_production_rules.py:15/316/322`），
      **无任何 `.py` 读取**；`_light_index.json` 有 `query_theory.py:216/245` 自动重建，
      属缓存非真源；`.crx` 零引用
- [x] 缓存等价性验证：`build_light_index(rebuild=True)` 到临时文件 → 4215 条，id 集合完全相等
- [x] ⚠️ **`index-new.yaml` 核实不通过** —— 见下

---

### Step 1: `index-new.yaml` 前提证伪
**Status:** ⛔ Blocked（未删除，等中枢定夺）

任务称「废弃草稿，index.yaml 才是产物」，三条证据推翻：

- [x] **规则集零重叠**：index.yaml 933 条 vs index-new 236 条，按 id / title / claim 三重比对重叠均为 **0**
- [x] **155 条全仓库唯一**：按 id 交叉 `_ir/` 与 `_cleaned/` 后，236 条中 155 条
      （主要是 `ZP-PROD-20260623-*` 批次 144 条）**只存在于 index-new.yaml**，
      且无脚本会重新生成（`grep 20260623 --include=*.py` 零命中）
- [x] **被 5 个冻结 case 引用**：`asof-blind-freeze.json` 的 `theory_evidence[].locator` 指向
      `index-new.yaml:<行号>`，行号与内容精确对应（794/832/1630/1669 逐一核对无误）
- [x] 其中 `ZP-PROD-20260623-042`（RF000417 引用）在 index.yaml / _ir / _cleaned 中**均不存在**
- [x] 确认测试不会报警：`as_of_contract_gate.check_theory_evidence` 只查非空+非占位，
      **不校验 locator 文件是否存在** → 删除会造成静默证据链断裂

结论：**非零风险，按任务授权停止未删。**

---

### Step 2: 执行删除（3 项）
**Status:** ✅ Completed

- [x] `git rm --cached` 4 个文件（crx / light_index / 两个 _extracted_rules.json）
- [x] 工作区删除 `.crx` 与 `_light_index.json`（可再生 / 无引用）
- [x] 工作区**保留**两个 `_extracted_rules.json`（按任务建议，脚本 OUTPUT_JSON 指向它们）

---

### Step 3: 更新 .gitignore
**Status:** ✅ Completed

- [x] 新增 4 类规则（`.gitignore:79-86`）：`*.crx` 通配、`theory/_light_index.json`、两个 `_extracted_rules.json`
- [x] `git check-ignore -v` 验证生效（`:82`、`:85` 命中）

---

### Step 4: 验证
**Status:** ✅ Completed

- [x] `git status --porcelain`：4 个目标文件均为 `D `，无 untracked 残留
- [x] `python -m pytest -q`：**229 passed in 17.13s**（与删除前基线 229 passed 一致）
- [x] 缓存自愈：删后跑一次 CLI，`theory/_light_index.json` 自动重建且尺寸逐字节相同（7,267,962 B），
      重建文件被 gitignore 忽略，`git status` 仍只显示 `D `
- [x] 未触碰 `engine/`、`tests/`、`tools/`、`cases/`、任何 `.py`/`.md`/`index.yaml`
- [x] 未 commit、未动 `.git` 历史

---

### Step 5: 产出
**Status:** ✅ Completed

- [x] `tasks/T-107/BRIEF.md` 四字段齐备
- [ ] 等中枢对 `index-new.yaml` 的裁决（并入主索引 or 重写 case 引用后废弃）
