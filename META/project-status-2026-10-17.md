# 项目状态与未完成任务清单 · 2026-10-17 收口

> 本文件是给人类决策者的核对表。所有数字均实测，非估计。
> 上一轮对手方简报有 1 处计算错误，已在 §五 标注。

## 一、已完成（本日）

### 1. WP-8 人话改造（v9 定稿，全部落地）

| 交付物 | 验证 |
|---|---|
| `docs/analysis_human_touch.md`（v7 契约版） | — |
| `templates/report-v7-human.md`（单报告 + 契约指纹） | — |
| `docs/agent_tools.md` Step 6（a–f 六条 + 两句声明） | — |
| `AGENTS.md` 导航图 +3 行、争议原则 +1 条 | — |
| `reports/README.md` v7 单报告默认架构 | — |
| `tools/human_touch_linter.py`（含 `_contract_health`） | 17 tests |
| 标杆报告 ×2 + 1984 修复 | linter 0 ERROR |

### 2. 盲测工具链（对接已有 `dual_core_blind`，未重造）

| 交付物 | 说明 |
|---|---|
| `tools/blind_predict_bridge.py` | predictions.json → `dual_core_blind` rounds/verification；含 `inspect` 预览 |
| `tools/rf_facts_hydrate.py` | 446 例 RF 案例落盘引擎事实（ok=446, error=0） |
| `tools/rf_pillar_intake.py` | 四柱口径案例（收 3 例 pillar-only） |
| `tools/extraction_validator.py` | 四项机械校验 + `--migrate` 真源回填 |
| `tools/blind_ledger.py` | L1 参考实现（24 tests），主线已改用 `dual_core_blind` |

### 3. RF 案例补全（收口）

- 992 条 jsonl → **446 个可展开案例**（443 birth + 3 pillar-only）
- 546 条无法展开且不可补救（缺四柱/缺性别）
- 结论见 [`META/rf-intake-conclusion-2026-10-17.md`](rf-intake-conclusion-2026-10-17.md)

### 4. 盲断首批（4 例完成并封存）

| 案例 | 断语数 | 事项封存 |
|---|---|---|
| RF000441 乾 | 9 | 6/6 |
| RF000864 乾 | 9 | 6/6 |
| RF000243 坤 | 8 | 6/6 |
| RF000524 坤 | 9 | 6/6 |

**共 24 个封存文件**（`META/blind_seals/.dual-core-blind-seals/`），
`seal_blind_run` 全部通过，`compute_rule_review_statistics` 口径就绪。

### 5. 杨派语料提取（+223 条，超预期）

- `theory/_light_index.json`：3471 → **3694 条**
- 杨派：163 → **386 条**（目标 400，**仅差 14**）
- 真源回填：223 条已写入 `theory/raw/yang/promoted/deep-extract-yang-b01..05.md`
- 机械校验：**PASS 222 / SUSPECT 1 / FORGE 0**（无编造锚点）

---

## 二、未完成任务（按优先级）

### P0 · 阻断首轮准确率的

| # | 任务 | 现状 | 阻塞点 |
|---|---|---|---|
| **1** | **历史回测任务包（v2）跑通** | v2 已生成 6 例（`.workbuddy-ai/blind-bundle-v2/`），**尚未派发给盲断 agent** | 盲断 agent 仍在用 v1（含 `known_facts` 污染） |
| **2** | **重新盲断 v2 的 6 例** | 未开始 | 需新会话/干净上下文，且要用 `blind-bundle-v2` 而非 v1 |
| **3** | **把 4 例已封存结果接入统计** | 封存完成，但 `compute_rule_review_statistics` 需要 `independent_rule_outcomes` | 该参数要求逐条规则独立核验，目前 verification_records 只有事项级结论 → **需扩展桥接层生成规则级核验** |

### P1 · 语料与结构

| # | 任务 | 现状 |
|---|---|---|
| 4 | 杨派补足 14 条 | 386/400 |
| 5 | 段派提取（110 条缺口） | 290/400，未启动 |
| 6 | 高派、任派 | **已达标**（261/200、200/200），无需再提 |
| 7 | `build_indexes.py` 支持新格式 | 回填稿进不了 `index.yaml`，**当前缓存不可 `--rebuild-index`** |
| 8 | `M2-Y-223` verify_fragment 空格问题 | SUSPECT 1 条，非编造 |
| 9 | StructureCheck 第一批 3–5 条 | 未开始（OPUS 建议首批只 3–5 条） |

### P2 · 评测设计

| # | 任务 | 现状 |
|---|---|---|
| 10 | 24 例 Dev 基线集 | **不可行**：年龄≥32 的合格案例仅 25 例（见 §四） |
| 11 | 标准化盲考题生成器（含负样本） | 未开始（Gemini 4 的核心建议） |
| 12 | 评分口径 `blind-scoring/v1` 冻结 | 草案在 `SCORING_CONTRACT.md`，未正式冻结 |

### P3 · 收尾

| # | 任务 | 现状 |
|---|---|---|
| 13 | **git 提交** | **481 项未提交**（5 修改 + 476 新增） |
| 14 | 仓库清理（.crx / 三个工具缓存） | 未做 |
| 15 | 打包给 Gemini 4 | 未做 |
| 16 | `.gitignore` 补 `.workbuddy-ai/` | 未做 |

---

## 三、关键技术风险（必须知道）

### 风险 1：`_light_index.json` 是缓存，不是真源

数据流：`theory/raw/{school}/` →（`build_indexes.py`）→ `index.yaml`
→（`query_theory.build_light_index`）→ `_light_index.json`

**223 条杨派新增已回填真源，但 `build_indexes.py` 还不认新格式。**
在它更新前，**任何人运行 `--rebuild-index` 都会冲掉这 223 条**。

→ 已在 `extraction_validator.py` 的 migrate 输出中警告。

### 风险 2：4 例已封存的是前瞻预测，不是历史回测

它们的 `time_scope` 全部在 2025 年后（因 input.md 含 known_facts 到 2024），
`verification_records` 全部为"反馈未提供"→ **全部 undetermined，不进分母**。

我们真正需要的历史回测，必须用 v2 任务包（已剥离 known_facts）重跑。

### 风险 3：`matter_category` 冲突

`dual_core_blind` 要求一次 seal 只覆盖一个事项，且 canonical path 无 matter 维度。
桥接层用 `case_id#matter` 复合 ID 解决。另外同一 round 内同规则双向引用
（实测 RF000243 的 MP-05）会被拒，已合并为 `mixed`。

---

## 四、年龄截断的硬事实（推翻 24 例方案）

实测 223 个合格案例：

- 年龄 ≥32：**25 例**（11.2%）
- 年龄 <32：**198 例**（88.8%）
- 性别：乾 150 / 坤 73

Gemini 4 要求"≥32 岁占 75%"，**但池子里只有 11%**。24 例 Dev 集无法满足
1:1 性别比 + events 两档 6:4 + 年龄约束。

→ 已在 `sampled/pilot.json`（6 例，全 ≥36 岁）与 `sampled/dev.json`（24 例，
但性别 21:3 失衡）留档。**dev.json 不可直接使用。**

---

## 五、需纠正对手方简报的 1 处错误

简报称"**杨派距 400 条目标还差 177 条**"。

实测：原 163 + 新增 223 = **386**，距 400 仅差 **14 条**。
177 = 400 − 223，漏算了原有 163 条基线。

另：简报称"高派 200 / 任派 200 未启动"——**两者本就已达标**（261/200、200/200），
无需提取。真正待提取的只有**段派（110 条）**与**杨派（14 条）**。

---

## 六、建议的下一步顺序

1. **立即**：`git add` + commit（481 项悬空太危险）
2. **今天**：把 `blind-bundle-v2` 派给盲断 agent，重跑 6 例历史回测
3. **随后**：扩展桥接层生成规则级 `independent_rule_outcomes`，让 4 例封存能出统计
4. **并行**：段派提取 110 条（派给另一 agent）
5. **收尾**：`build_indexes.py` 支持新格式，解除 rebuild 风险
