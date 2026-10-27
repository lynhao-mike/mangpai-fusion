# T-132: 墓库扫描扩全部十神（A4） — Status

**Status:** ❌ 前提不成立，已撤销
**Current Step:** Closed（无代码改动）
**Last Updated:** 2026-10-27
**Iteration:** 1
**Size:** S（原估 M，因前提不成立降级）
**Executor:** 子代理（Worker）

> 任务卡由中枢写好，Worker 只读卡执行，**不要自己写 PROMPT.md**。
> 本轮为只读勘察 + 复现，未动业务代码。

---

### Step 1: 定位墓库扫描
**Status:** ✅ Done

- [x] `engine/facts/` 全目录搜 墓/库/入墓/tomb/store → 命中 `relation_graph.py::_muku`（事实层）、`structure_check.py` 墓用分支、`types.py` MukuFact/MukuCandidate、`profiles.yaml` tu_jigong
- [x] 判定：**墓库扫描所在模块 = `engine/facts/relation_graph.py`（`_muku`, L341-413）**
- [x] 读清「为什么只出财官」→ **不成立**：`_muku` 按五行（`_MU_BRANCH = {辰:水, 戌:火, 丑:金, 未:木}`）扫描，五行为该库的字全进候选，本来就是全十神

### Step 2: 先复现 fire=0
**Status:** ✅ Done

- [x] `pilot-20.yaml` M3-R-166（L325-343）：`conditions_v2 = {framework_dependency: requires_pair, pair_with: [M2-Y-017], preconditions.all: [ru_mu(star=食神)]}`；文件中**未绑定四柱**
- [x] probe 1（481 盘）：`ru_mu(食神)` 为真 **41 盘**，十类十神全部有命中；`muku_candidates_total=818`
- [x] probe 2（481 盘）：facts 层墓用候选 507 条 / 226 盘，十类十神全覆盖
- [x] 定位真实成因：`compile_state: partial` → `compile_claim` 返回 `partial` → 两个报告工具跳过 → `fire_rate` 无此条；且 `requires_pair` + `ctx["cited"]` 恒为 `{}` → 最多 `evidence_only`
- [x] 中枢独立复算，确认结论成立，任务卡前提作废

### Step 3: 扩到全部十神
**Status:** ⛔ Cancelled

- [x] **未执行**。前提不成立，中枢已撤回修改授权；在链路 A 无对应缺口，在链路 B 动手不会改变任何观测值

### Step 4: 补「扩前 0 / 扩后非 0」测试
**Status:** ⛔ Cancelled

- [x] **未执行**。无可断言的真实变化，编造该测试即为假修复

### Step 5: 验收
**Status:** ⛔ Not Run（按中枢指示不跑）

- [x] 未跑 `pytest -q` / `verify_baseline`：本轮无代码改动，门禁不受影响

---

## Execution Log

| Timestamp | Action | Outcome |
|---|---|---|
| 2026-10-27 | 读卡、定位墓库扫描 | `engine/facts/relation_graph.py::_muku`，按五行扫描 |
| 2026-10-27 | probe 1：481 盘十神覆盖 + `ru_mu` 逐神命中 | `ru_mu(食神)=41 盘`；十类全有覆盖；候选 818 条 |
| 2026-10-27 | probe 2：facts 层墓用候选分布 | 507 条 / 226 盘，十类全有覆盖 |
| 2026-10-27 | 定位 `fire=0` 真实成因 | `partial` 跳过求值 + `requires_pair` 未裁决 |
| 2026-10-27 | 上报中枢 | 中枢独立复算确认，任务卡前提作废 |
| 2026-10-27 | 中枢撤回修改授权 | 不做代码改动，只产出证据文档 |
| 2026-10-27 | 写 BRIEF.md、更新 STATUS.md | 本轮收口 |

---

## Blockers

**1. 任务卡前提不成立（决定性）**

任务卡 §1 称「墓库扫描当前只覆盖财、官两类十神」。核实结果：

- `ru_mu` 读取的是 `engine/facts/relation_graph.py::_muku`（经 `facts["relations"]["muku"]`）。该函数按五行扫描，`_MU_BRANCH = {"辰":"水","戌":"火","丑":"金","未":"木"}`，凡五行为该库的原局字全部进候选，再按任付红五条细则标注 —— 本来就是全十神。481 盘实测：候选 818 条，十类十神全有覆盖；`ru_mu(食神)` 为真 41 盘。
- 财官限定**只存在于另一条链路**：`engine/energy/zuogong.py::detect_mu_paths`（**:472**，函数内 `_yongshen_in_zhi_canggan` 把用神限定为 财/官杀；文件 L27 自述「墓 = 简化实现（只检测财官入辰戌丑未）」）。
- 该遗留函数经 `engine/energy/evaluator.py:220`（`zuogong_paths = evaluate_zuogong(bazi, tiyong)`）与 `engine/v5/duan_runner.py:60`（`paths = evaluate_zuogong(bazi, tiyong)`）被调用，并在 `engine/energy/zuogong.py:535` 由 `evaluate_zuogong` 汇入。
- 它**不在** `ru_mu` 读取的 `engine/facts/relation_graph.py::_muku` 路径上：`engine/facts/` 全目录不含 `engine.energy` 的任何 import（grep 0 命中）。

即任务卡把链路 B 的自述当成了链路 A 的行为。

**2. `fire=0` 的真实成因与墓库扫描无关（双重不可达）**

- 第一层：`M3-R-166` 的 `compile_state: partial` → `engine/claims/condition_ir/ir.py::compile_claim`（L271-273）返回 `partial` → `tools/claim_condition_report.py:96` 与 `tools/claim_condition_corpus.py:55` 都只收 `compiled` → 该断语根本没被求值（`META/claim-condition-pilot-v1.json` 的 `compiled_claims` 与 `fire_rate` 里都没有它）。
- 第二层：即使改成 `compiled`，其 `framework_dependency: requires_pair` + `pair_with: [M2-Y-017]`（对方自身 `needs_human`），而 `build_context` 里 `"cited": {}` 恒空 → `evaluate_claim`（ir.py L167-179）只会给 `evidence_only`，而开火判定是 `state == "candidate"`。**改 `compile_state` 也救不回来。**

**3. `pilot-20.yaml` 的 `compile_note` 曾是错误陈述 —— 已由中枢更正**

旧 note 的「只覆盖财官」「481 张盘命中 0」两句均已被证伪。按分工由**中枢亲自更正**（避免两人同时写同一文件），Worker 未改；`git diff -- theory/claims/conditions-v2/pilot-20.yaml` 可见中枢已于 2026-10-27 改写该 note，并把后续指向 M2-Y-017 而非扩墓库。更正后需重跑 `claim_condition_report` / `claim_condition_corpus` 才能刷新 `META/` 下的旧产物。

---

## Amendments

中枢已在 `tasks/T-132/PROMPT.md` 顶部加入 ⛔ 裁定横幅（前提不成立、本卡撤销、保留仅作追溯、**不得据本卡修改 `engine/facts/`**），本 Worker 无需再提更正建议。裁定要点：

- 病灶描述溯源：`tasks/T-117/PROMPT.md:88` 指向的是遗留链 `engine/energy/zuogong.py::detect_mu_paths:472`（经 `engine/energy/evaluator.py:220`、`engine/v5/duan_runner.py:60` 调用），**不在** `ru_mu` 读取路径上。
- `M3-R-166` 真正原因：`compile_state: partial` 使两个报告工具跳过 + `requires_pair` 的 `M2-Y-017` 为 `needs_human`，配对永不裁决 → 只能 `evidence_only`。
- 后续拆分：① 补「禄」原子解锁 M2-Y-017 → **T-135**；② 遗留链 `detect_mu_paths` 的财官限定若要修，单独立项（P1，与断语求值链无关）。
