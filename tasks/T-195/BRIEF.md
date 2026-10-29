# T-195 · R-tool 一次运行（fixed-20 + routing）· BRIEF

- 执行者：子代理（未污染 runner，按任务卡）
- 运行时间：2026-10-29 23:5x（Asia/Shanghai）
- 解释器：`.venv\Scripts\python.exe`
- 规格：`docs/specs/fact-evidence-pack-v1.md`、`docs/specs/actor-rules-v1.md`

## 1. 改动文件

| 文件 | 动作 | 说明 |
|---|---|---|
| `META/r-tool-run-v1.json` | 新建 | 产物：fixed-20 固定类事实 20 条 + routing 证据包 15 个 |
| `tasks/T-195/run_r_tool.py` | 新建 | 确定性 runner；JSON 由它生成，可由干净会话重跑复现 |
| `tasks/T-195/BRIEF.md` | 新建 | 本文件 |
| `tasks/T-195/STATUS.md` | 更新 | 追加 Execution Log |

未改：`engine/**`、答案/阈值、`tests/**`、`sources/**`、`theory/**`、`META/project-state.json`、`tasks/T-195/PROMPT.md`。无 git 写。

## 2. 原始输出

```powershell
.venv\Scripts\python.exe tasks\T-195\run_r_tool.py
# wrote E:\Git hub\mangpai-fusion\META\r-tool-run-v1.json
# fixed 20/20  out_of_class=0
# breakdown={'engine_candidate': 17, 'engine_element_rule': 2, 'engine_pair_fallback': 1}
# routing packs=15 evidence=116
```

结构自检（stdlib 脚本，逐条核 `source_ref` 可解析 + `quote` 逐字命中 + 端点/类/方向约束）：

```
ERRORS: 0
```

证据项计数（`routing.evidence_breakdown`）：palaces 37 / edges 49 / source_refs 30 = **116**。
（题库预注册计数为 palaces 35 / edges 32 / source_refs 30；本包按「宫位集合×支级边」全量取，边多取 17 条，见 §3。）

### fixed-20 明细（class · actor→target · 来源）

| case | class | actor→target | matched_by | engine 规则 |
|---|---|---|---|---|
| F20-001 | 克 | M.b(戌)→Y.b(亥) | engine_candidate | 制用/zhi_ke |
| F20-002 | 克 | Y.b(午)→D.b(酉) | engine_candidate | 制用/zhi_ke |
| F20-003 | 克 | M.b(午)→D.b(酉) | engine_candidate | 制用/zhi_ke |
| F20-004 | 克 | Y.b(戌)→M.b(亥) | engine_candidate | 制用/zhi_ke |
| F20-005 | 克 | Y.b(卯)→D.b(未) | engine_candidate | 制用/zhi_ke |
| F20-006 | 生 | M.b(亥)←D.b(酉) | engine_candidate | sheng/sheng |
| F20-007 | 生 | Y.b(卯)→M.b(巳) | engine_candidate | 生泄用/sheng(main_qi) |
| F20-008 | 生 | D.b(午)→Y.b(辰) | engine_candidate | 生泄用/sheng(main_qi) |
| F20-009 | 生 | Y.b(申)→D.b(子) | **engine_element_rule** | 五行表（engine 无该对 生 候选） |
| F20-010 | 生 | D.b(卯)→Y.b(巳) | engine_candidate | 生泄用/sheng(main_qi) |
| F20-011 | 化 | Y.b(亥)→M.b(酉) | engine_candidate | 化用/sheng(main_qi) |
| F20-012 | 化 | H.b(子)→D.b(申) | engine_candidate | 化用/sheng(main_qi) |
| F20-013 | 化 | Y.b(未)→M.b(亥) | **engine_pair_fallback** | 沿用同对 制用 力向（类不符，已标） |
| F20-014 | 化 | H.b(子)→Y.b(申) | **engine_element_rule** | 五行表 + §4.8 化者=受生端 |
| F20-015 | 化 | M.b(寅)→H.b(子) | engine_candidate | 化用/sheng(main_qi) |
| F20-016 | 墓 | Y.b(未)→D.b(寅) | engine_candidate | 墓用/muku |
| F20-017 | 墓 | M.b(丑)→D.b(酉) | engine_candidate | 墓用/muku |
| F20-018 | 墓 | H.b(辰)→M.b(亥) | engine_candidate | 墓用/muku |
| F20-019 | 墓 | D.b(丑)→Y.b(申) | engine_candidate | 墓用/muku |
| F20-020 | 墓 | D.b(丑)→Y.b(酉) | engine_candidate | 墓用/muku |

F20-006 表中「M.b(亥)←D.b(酉)」即 actor=D.b（酉生亥），JSON 内为 `actor=D.b / target=M.b`。

### routing 15 题（每题证据项数）

| 题 | 域 | palaces | edges | theory | 合计 |
|---|---|---:|---:|---:|---:|
| RQ-01 | 婚姻 | 2 | 3 | 2 | 7 |
| RQ-02 | 婚姻 | 2 | 1 | 2 | 5 |
| RQ-03 | 婚姻 | 1 | 2 | 2 | 5 |
| RQ-04 | 婚姻 | 2 | 3 | 2 | 7 |
| RQ-05 | 事业 | 2 | 2 | 2 | 6 |
| RQ-06 | 事业 | 2 | 4 | 2 | 8 |
| RQ-07 | 事业 | 2 | 2 | 2 | 6 |
| RQ-08 | 事业 | 2 | 3 | 2 | 7 |
| RQ-09 | 健康 | 3 | 4 | 2 | 9 |
| RQ-10 | 健康 | 3 | 5 | 2 | 10 |
| RQ-11 | 健康 | 3 | 6 | 2 | 11 |
| RQ-12 | 财运 | 3 | 5 | 2 | 10 |
| RQ-13 | 财运 | 3 | 3 | 2 | 8 |
| RQ-14 | 财运 | 3 | 2 | 2 | 7 |
| RQ-15 | 财运 | 4 | 4 | 2 | 10 |

## 3. 未完成与风险

1. **routing 非盲（最重要）**：任务卡指定的 `META/routing-questions-v1.json` 自称「runner 视图」，但文件实际包含
   `expected_evidence`（`access.restricted_fields`）。整文件读取后该字段进入 runner 上下文，**routing 已不是盲跑**。
   `META/r-tool-run-v1.json.routing.blind_valid = false`，并写了原因。**该 routing 数据不可作为盲测入账**。
   同一事实也记在 `isolation.restricted_field_exposure`（occurred=true）。
   fixed-20 未受影响（未读任何 answers / B 卷 / prereg）。
   → 补救：先产出仅含 `runner_visible_fields` 的脱敏文件，再由干净会话跑 `tasks/T-195/run_r_tool.py`（脚本本身不读 expected_evidence）。

2. **fixed-20 有 3 条「类与 engine 固定候选不一致」**（`class_rule_mismatch_cases = F20-009/013/014`）：
   - F20-009（生，申/子）：engine 只发 `化用`（子化申），无 `生` 候选；按 engine 五行表推 申→子。
   - F20-014（化，申/子）：engine 只发 `生泄用`（申→子）；按 §4.8「化者=受生端」取 子→申。
   - F20-013（化，未/亥）：engine 只发 `制用`（未克亥）；五行无生向，**只能沿用同端点对的制用力向**（未→亥），
     `basis = engine_pair_direction_with_target_class`，是最弱的一条。
   这 3 条不属类外发射（仍是克/生/化/墓），但属「engine 未给出该类的固定事实」。

3. **覆盖 20/20 是构造性结果**：`target_relation.mechanism`已在盲卷内给出，runner 只负责定位该类事实。
   真正的信息量在 `class_source_breakdown`：**engine_candidate 17 / engine_element_rule 2 / engine_pair_fallback 1**。

4. **edge_id 全为 null**：engine 不建支-支克边（G3），生/化/墓类候选多为 `derived`（无 edge_id）。
   为满足「edge/source_ref」要求，每条 fixed fact 附 `class_source_ref`（类级原文锚点，逐字校验通过）+ `rule_ref`（engine 代码行/actor-rules 行）。

5. **F20-012 性别「未注明」**：engine 仅接受 乾/坤，脚本回退 `乾` 并记录 `gender_input/gender_used`。
   固定类事实与十神不依赖性别；该盘未用于 routing。

6. **routing 边多取**：按「宫位集合 × 支级边」全量取，49 条 > 预注册 32 条。R 规格只测召回（§3.3），
   多取不影响召回，但**精度会偏低**；若中枢要精度，需另立卡收窄规则（例如只取与「主位/配偶星/财星」直接相连的边）。

7. 未跑 `pytest`（本卡只产事实包，不改 engine）；未跑评分器；未自评；未做 git 写。

## 4. 下游须知

- **中枢评分口径**：fixed gate 只数 (a) `out_of_class_emissions == 0`、(b) 20/20 目标类覆盖；
  actor 对错不计门（卡 §1）。routing recall **先解决盲性**再算，否则数字不可用。
- **证据包字段**（每题）：
  `palaces[{addr, role, ten_god, mapping_rule, mapping_rules, basis_source_ref}]`、
  `edges[{edge_id, kind, members, scope, direction="undetermined", actor=null, target=null}]`、
  `theory[{entry_id, source_ref, quote, quote_verified, basis}]`、
  `evidence_items[{type: palace|edge|source, ref}]`、`gaps[]`、`non_claims[]`。
- **mapping_rule 登记**：M-01 夫妻宫/日支、M-02 配偶星（男财/女官杀）、M-03 月令事业宫、M-04 日主、
  M-05 日支身体宫、M-06 月令气候、M-07 财星、M-08 主位取财之身；每条带 `basis_source_ref`（原文行区间）。
- **理论锚点**：婚姻 → 婚姻专辑 L15-L17 / L37-L44；事业 → 盲派中级命理学 L2819-L2827 / L2829-L2831；
  健康 → 疾病 L3-L11 + 日支象法行；财运 → 求财 L3-L5 / 命格组合 L3-L7。全部 `quote` 已在范围内逐字命中。
  `entry_id` 仅婚姻命中 query_theory 原子（M1-D-291 / M1-D-295），其余域 `entry_id=null`（检索未返回该行锚点），
  但 quote 仍逐字可复核。
- **重跑**：`.venv\Scripts\python.exe tasks\T-195\run_r_tool.py`（约 20 次 engine.cli 调用 + 4 次 query_theory）。
