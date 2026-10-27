# T-132 · 墓库扫描扩全部十神（A4）

> ## ⛔ 2026-10-27 中枢裁定：**前提不成立，本任务撤销**
>
> 复算证据（481 盘，中枢亲跑）：`ru_mu` 读的是 `engine/facts/relation_graph.py::_muku`，该扫描**按五行**建候选（`_MU_BRANCH = {"辰":"水","戌":"火","丑":"金","未":"木"}`），本就覆盖全部十神——818 条候选，食神 54、伤官 73、比肩 109、正财 84、偏财 75、七杀 66、正官 56、劫财 53、偏印 65、正印 51、日主 86。`ru_mu(食神)` 实际命中 **41/481 盘**，`compile_note` 所称「481 张盘命中 0」是错误陈述（已更正）。
>
> 本卡原先的病灶描述来自 `tasks/T-117/PROMPT.md:88`，那句指向的是遗留链 `engine/energy/zuogong.py::detect_mu_paths:472`（经 `engine/energy/evaluator.py:220`、`engine/v5/duan_runner.py:60` 调用），**不在** `ru_mu` 的读取路径上。
>
> `M3-R-166` 真正的 fire=0 原因：`compile_state: partial` 使它被两个报告工具直接跳过；且 `requires_pair` 的配对命题 `M2-Y-017` 为 `needs_human`（缺「禄」原子），配对永不裁决 → 只能落 `evidence_only`。**即使把 compile_state 改成 compiled 也不会 fire。**
>
> 后续拆为两件事：① 补「禄」原子以解锁 M2-Y-017（见 T-135）；② 遗留链 `detect_mu_paths` 的财官限定若要修，单独立项（P1，与断语求值链无关）。
>
> 本卡保留仅作追溯，**不得据本卡修改 `engine/facts/`**。


- 状态：🔵 Ready for Execution
- 优先级：P0（直接导致断语算出 0）
- 创建：2026-10-27（中枢）
- 决策依据：ADR-001（引擎=确定性事实）

## 1. 背景

墓库扫描当前只覆盖财、官两类十神，导致断语 `M3-R-166` 的 `fire=0`。这是「断语算不出来」的直接原因之一，属 A 组必修项。

## 2. 要做的事

1. **先定位**：找到墓库扫描的实现（`engine/facts/` 下，自行搜索墓库/入库/藏库相关函数），读清它现在为什么只出财官。
2. **先复现**：从 `theory/claims/conditions-v2/pilot-20.yaml` 取 `M3-R-166` 的 `conditions_v2` 与其绑定的四柱，用 `engine.cli` 跑出 `fire=0` 的现场证据，把原始输出贴进 BRIEF。**没有复现证据不许动手改。**
3. **再修**：把扫描范围扩到全部十神（比肩/劫财/食神/伤官/偏财/正财/七杀/正官/偏印/正印）。判断「某十神是否入墓」的规则必须来自既有代码或 `tools.query_theory` 的原文，**不得自己发明规则、不得自己定阈值**。
4. **补测试**：新增测试必须断言「扩前为 0、扩后非 0」这一具体变化，不许只断言不抛异常。

## 3. File Scope

- 墓库扫描所在模块（`engine/facts/` 下，由你定位后写进 STATUS.md）
- 对应测试文件（`tests/facts/` 或就近）
- **禁止**改 `theory/_ir/`、`sources/`、`pyproject.toml`

## 4. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m pytest -q                    # 不得出现 failed，passed 数不得减少
.venv\Scripts\python.exe -m tools.verify_baseline        # pytest≥220 / audit_errors=0 / relations 通 / zuogong_charts≥477
```

外加：M3-R-166 那盘的 `fire` 候选由 0 变为非 0（把命令与输出贴进 BRIEF）。

## 5. 回报格式

必须写清：改了哪个函数、原规则是什么、扩到全部十神后新增哪些候选、「某十神入墓」的规则依据来自哪段原文或哪段既有代码、以及扩前的 `fire=0` 原始输出。
