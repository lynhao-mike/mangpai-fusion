# 原局—大运—流年—截止状态推理系统 · 设计与实现落差审计（修订版）

> 审计日期：2026-07-26（Asia/Shanghai）
> 原始版本由 GPT-5.6 产出；本版由 Claude Opus 独立核验、补充并修订
> 审计对象：[`plans/as-of-life-state-reasoning-design-2026-07-18.md`](../plans/as-of-life-state-reasoning-design-2026-07-18.md)
> 审计方法：代码检索（全仓关键类名精确搜索 + 既有模块字段枚举）+ 案例目录抽样读取 + 全仓 sanity 结果交叉核对
> 结论性质：状态审计，不是实现验收，不构成任何 G-gate PASS
>
> ⚠️ 检索方法论局限：本次只对设计文档 §5 的七个精确类名进行了全仓搜索，未穷举语义等价的变体命名（如 `life_event`、`life_state`、`natal_chart`、`career_track`）。若存在同义不同名的实现，可能被遗漏。在 G1 启动前建议 terra 对新建的 `engine/asof/` 目录做额外的宽泛搜索以排除潜在命名冲突。

---

## 1. 结论摘要

设计文档状态仍为文档头部自述的 **"设计已确认，待用户审阅书面规格"**（[行 3](../plans/as-of-life-state-reasoning-design-2026-07-18.md:3)），本次审计未发现任何证据推翻这一自述。

**核心发现：该设计的关键数据对象在代码库中精确检索为零命中。** 全仓库搜索 `NatalCapacityGraph`、`DaiyunContext`、`AnnualInteractionTrace`、`LifeEventCandidate`、`EventImpactAssessment`、`VerifiedState`、`HypothesisState`（设计文档 [§5](../plans/as-of-life-state-reasoning-design-2026-07-18.md:131) 定义的全部七个关键数据对象）均为 0 结果。`as_of_date` 输入参数同样 0 结果。

**F09 收口 ≠ as-of 状态机进度推进。** 两者共享同一批原始设计动机，但目前零代码耦合、零共用数据模型——这是本次审计最关键的去歧义结论，避免后续工作基于错误进度预判做出错误估算。

---

## 2. 逐项证据核验

### 2.1 关键数据对象检索结果

| 设计对象 | 定义位置 | 精确检索命中数 | 备注 |
|---|---|---|---|
| `NatalCapacityGraph` | [§5.1](../plans/as-of-life-state-reasoning-design-2026-07-18.md:133) | 0 | — |
| `DaiyunContext` | [§5.2](../plans/as-of-life-state-reasoning-design-2026-07-18.md:146) | 0 | ⚠️ `engine/yingqi/retrospective.py:76` 存在同义类 `DaiyunSegment`，含义高度相似，实现时须注意命名冲突 |
| `AnnualInteractionTrace` | [§5.3](../plans/as-of-life-state-reasoning-design-2026-07-18.md:158) | 0 | — |
| `LifeEventCandidate` | [§5.4](../plans/as-of-life-state-reasoning-design-2026-07-18.md:173) | 0 | — |
| `EventImpactAssessment` | [§5.5](../plans/as-of-life-state-reasoning-design-2026-07-18.md:201) | 0 | — |
| `VerifiedState` | [§5.6](../plans/as-of-life-state-reasoning-design-2026-07-18.md:219) | 0 | — |
| `HypothesisState` | [§5.7](../plans/as-of-life-state-reasoning-design-2026-07-18.md:230) | 0 | — |
| `as_of_date` | [§9](../plans/as-of-life-state-reasoning-design-2026-07-18.md:484) | 0 | — |

### 2.2 既有 `engine/yingqi/retrospective.py` 可复用字段 vs. 设计需求缺口

设计文档 [§13](../plans/as-of-life-state-reasoning-design-2026-07-18.md:616) 明确列出四个既有对象可作为"候选生成层基础"。本次对其实际字段做了枚举，发现以下重要缺口，将影响 G1 的具体实施方式：

| 既有对象 | 实际字段（已核实） | 设计 §5 要求的字段 | 缺口 |
|---|---|---|---|
| `FlowYearEnergy`（行 42-61） | `year`, `age`, `liunian`, `dayun`, `relations`, `main_energy`, `strength`, `domains` | 流年与大运/原局的作用关系、被发动节点、命理触发强度、是否越过证据门 | `domains` 是无结构的中文字符串列表；`relations` 是自由文本描述，无法直接映射为"作用对象"或"发动节点"的结构化字段 |
| `DaiyunSegment`（行 76-106） | `seq`, `ganzhi`, `age_range`, `year_range`, `feature`, `typical_domains`, `flow_years` | 开放/关闭/放大/抑制/修复/改道的路径集合、领域阶段倾向、适用条件与反证 | `feature` 是自由文本字符串；无路径集合数据模型；无适用条件/反证字段 |
| `RetrospectiveReport`（行 109-144） | `case_id`, `birth_year`, `current_year`, `current_age`, `current_dayun`, `segments`, `note` | 截止状态的上游输入 | 无显式 `as_of_date`（当前用 `current_year` 代替）；无状态机所需的事件账本字段 |

**影响**：G1 不能直接将这三个对象"转化"为 `NatalCapacityGraph` / `DaiyunContext`——字段语义存在根本差异。正确做法是在 `engine/asof/` 内新建适配函数，以这三个对象作为**信号来源**，输出完全由设计文档 §5 冻结条款定义的新数据结构。禁止直接继承或 monkey-patch 既有类。

### 2.3 F09 的真实性质与边界

`tests/f09` 1172 passed 证明的是 F09「资本配置与风险承担」一张功能证据卡，在 `tests-only` 环境下走完"evidence package → real-world hard gate → competition → root/timing → 五动作 → StandardStatement → artifacts → feedback"的技术架子。关键边界：

1. **F09 默认禁用**：[`engine/f09/application.py:64`](../engine/f09/application.py:64) `enable_f09: bool = False` + 行 161-163 显式拒绝 `PRODUCTION_DEFAULT` 模式。
2. **F09 是单次静态判定**，不含跨大运/跨流年的动态状态转移语义——这正是 as-of 设计新增的核心能力。
3. **同名术语陷阱**：F09 卡片契约（[§3.3-3.4](../engine/contracts/12-real-world-function-evidence-cards-v1.md:117)）与 as-of 设计（[§6.4-6.5](../plans/as-of-life-state-reasoning-design-2026-07-18.md:273)）均使用"强根源/弱根源/无根源"+ 五种完成方式，但前者是**单次静态字段**，后者要求**跨运动态判定+延伸边界约束**。实现 G1-G2 时若直接从 F09 复制字段结构，会静默丢失"延伸边界"和"跨运复核"语义。

### 2.4 事业 + 财富现有实现现状

已有两条 staged 切片可复用其判别层素材，均未进入 G6：

| 切片 | 状态 | 可复用什么 | 不能代替什么 |
|---|---|---|---|
| 子平职业路径结构切片（[验证报告](ziping-career-structure-slice-g0-g5-verification.md:1)） | G0-G5 `staged_verified_production_unchanged` | 粗官杀+食伤必要门的结构判别信号 | 无事件账本、无状态转移、无双快照 |
| 任派职业变化应期切片（[验证报告](ren-career-timing-slice-g0-g5-verification.md:1)） | G0-G5 `staged_verified_production_unchanged` | 流年岁运触发的应期窗口信号 | 明确声明"不重新判断事件是否成立"，即假设上游事件已成立 |

另存在权重打分驱动的六域裁判（`parallel_domain_orchestrator`），其横截面打分范式与 as-of 要求的纵向时序状态机**架构不兼容**。

### 2.5 预先已知的全仓失败测试（重要：G5 STOP 条件参考）

G9 sanity 已证实全仓存在 2 个与本计划无关的 **pre-existing failures**：

| 失败测试 | 位置 | 失败原因 | 与 as-of 工作的关系 |
|---|---|---|---|
| `test_witness_trust_boundary_is_explicitly_documented` | [`tests/evaluation/test_dataset.py:256`](../tests/evaluation/test_dataset.py:256) | `tools/README.md` 缺少 witness trust-boundary 文案 | 无关 |
| `test_handoff_names_first_legal_case_action_and_all_independent_holds` | [`tests/evaluation/test_prospective_gate_workflow.py:343`](../tests/evaluation/test_prospective_gate_workflow.py:343) | `handoff.md` 缺少 prospective 首案及 HOLD 文案 | 无关 |

G5 运行全仓 sanity 时看到这 2 个失败**不应触发 STOP**——它们是既有失败，不是 as-of 新代码引入。若出现第 3 个及以上失败，才触发 G5 STOP 条件。

### 2.6 案例池预审结果（G0 参考）

本次对 `cases/` 目录下有 `feedback.md` 的案例进行了宽泛扫描，以下 3 个案例已通过 G0 三条前置条件的初步核验，建议 terra 在 G0 阶段优先考虑：

| 案例 | 文件完整性 | 已核验事业事件 | 可设置多个 as_of_date 的历史截止点 |
|---|---|---|---|
| `C-2026-028-乾-壬戌癸卯壬子乙巳` | `input.md`、`feedback.md`、`statement_index.json` 均存在 | 2020 年校分拆兼任两校校长、2022 年晋升正股级、2025 年调任较大初中 | 2019年前（无职务）/ 2021年（兼任双校）/ 2025年后（调任）三个不同截止点 |
| `C-2026-024-坤-己巳壬申辛亥壬辰` | 完整 | 2014-2015 入职小学教师、2024-2025 升职为校长 | 2014年前（在校）/ 2020年（在职教师）/ 2025年（校长）三个截止点 |
| `C-2026-022-坤-癸亥庚申戊寅己未` | 完整 | 2020 年调回初中物理并入编、2025 年晋升中级职称 | 2019年（编外）/ 2021年（在编）/ 2025年（职称晋升）三个截止点 |

**建议首选 C-2026-028**：事件横跨 2020-2025 年的五年视窗，包含"职业身份变化+层级提升+地域调动"三种不同类型的事业事件，适合验证设计 §11.1 中多类事件的状态转移差异；且 input.md 存在（排盘完整可用），无财富事件（G4 将用合成传播边，符合设计预期）。

---

## 3. 能否用事业 + 财富立即做验证？

**不能——因为待验证的系统本体尚未存在。**

正确做法是：以事业+财富为**首个实现原型**，从零实现最小状态机骨架，再用历史截止点回放（设计 [§12.1](../plans/as-of-life-state-reasoning-design-2026-07-18.md:582)）做验证。

---

## 4. 建议裁决

| 问题 | 裁决 |
|---|---|
| as-of 设计当前实现进度 | **0%**（精确类名全仓 0 命中；语义等价变体未穷举，理论上存在极低概率遗漏） |
| F09 收口是否等于 as-of 设计推进 | **不等于**；零代码耦合，F09 是静态功能证据卡，as-of 是动态状态机 |
| `DaiyunContext` 命名冲突风险 | **有风险**：已存在 `DaiyunSegment`，建议 G0 确认最终命名方案（如改为 `DaiyunStage`） |
| `retrospective.py` 字段能否直接复用 | **不能直接复用**：字段类型/语义存在结构性缺口，只能作为信号来源在适配层消费 |
| 全仓 2 个 pre-existing failures | **G5 正常现象**，不触发 STOP，不代表 as-of 工作引入新失败 |
| G4 财富传播边的数据来源 | **大概率需要合成测试**：推荐案例 C-2026-028 无财富事件反馈，G4 应预期使用合成边界用例 |
| 下一步 | 见配套执行计划 [`plans/as-of-life-state-g0-g5-execution-plan-for-terra.md`](../plans/as-of-life-state-g0-g5-execution-plan-for-terra.md) |

本审计不构成任何实现授权；后续代码写入仍需按仓库既有纪律逐步获得独立授权。
