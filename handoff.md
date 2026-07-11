# HANDOFF · 分层命理决策学习系统重构

> 写给完全没有上下文的新会话。读完这份你就能接手。
> 最后更新：2026-07-10。
> 本文件是**短期交接**，不是长期事实源。长期架构事实源是 [`plans/layered-decision-system.md`](plans/layered-decision-system.md)。

---

## 0. 一句话现状

我们在把一个八字分析系统从"多派融合大杂烩"重构成"分层决策学习系统（L0-L9）"。核心病灶已诊断清楚、R1-R9 九个重构阶段已全部落地并通过验证。**排期（用户 2026-07-10 定）：先做完 R 系列——即 R10 北极星（v5 runner 下沉 L2、删除 v5_adapter 事后转录）——再启动 K 系列命理建模；真实反馈样本收集全程并行。** R10 是要动代码的硬骨头；跨案学习与 K 系列校准则卡在真实反馈样本积累。

---

## 1. 我们在做什么任务

把 [`engine/`](engine/) 里的八字分析系统，从"五派各自算完、加权融合出报告"，改造成一条分层决策链：

```
L0 输入事实 → L1 流派适用性路由 → L2 各派独立命题 → L3 结构合法性审查
→ L4 事件落地 → L5 应期概率 → L6 冲突仲裁 → L7 报告表达
→ L8 反馈归因 → L9 校准治理
```

核心理念：**没有万能流派，只有适用场景**。系统要学会"什么八字该用什么法"，而不是让所有流派都发言再平均。

完整架构设计见 [`plans/layered-decision-system.md`](plans/layered-decision-system.md)（§0 格局判断 + L0-L9 逐层契约 + §18 R1-R9 分阶段路线）。

---

## 2. 事实源层级（重要，先搞清楚以哪个为准）

| 文档 | 定位 | 是否事实源 |
|---|---|---|
| [`plans/layered-decision-system.md`](plans/layered-decision-system.md) | **主架构文档**，L0-L9 契约 + R1-R9 路线 | ✅ 唯一架构事实源 |
| [`AGENTS.md`](AGENTS.md) | 仓库 AI 调用规则、事实源矩阵 | ✅ 操作规则事实源 |
| [`plans/l0-l9-refactor-geju-judgment-2026-07-10.md`](plans/l0-l9-refactor-geju-judgment-2026-07-10.md) | 重构格局判断（为什么这么做） | 支撑材料 |
| [`META/l0-l9-architecture-gap-investigation-2026-07-10.md`](META/l0-l9-architecture-gap-investigation-2026-07-10.md) | 四缺口调查（代码级根因） | 支撑材料 |
| [`docs/superpowers/plans/2026-07-10-*.md`](docs/superpowers/plans/) | R6-R9 执行计划（怎么做） | 已执行，历史留档 |
| [`META/layered-decision-system-run-flow-report-2026-07-10.md`](META/layered-decision-system-run-flow-report-2026-07-10.md) | 系统运行流程说明 | 支撑材料 |
| `HANDOFF.md`（本文件） | 短期交接 | ❌ 不作长期事实源 |
| `handoff.md`（小写，旧文件） | 历史短期交接 | ❌ 已过时，以本文件为准 |

**结论：改动架构方向时更新 [`plans/layered-decision-system.md`](plans/layered-decision-system.md)；它已与代码同步，无需额外维护第二份。** 支撑材料是历史留档，不要反过来当事实源去推断当前状态。

---

## 3. 已经完成了什么

### 3.1 架构诊断（核心洞察，务必理解）

真实案例 C-2026-035 跑通后发现根本倒置：**当前 v5 引擎在推理，L0-L9 分层链在抄写**。

- 命主看的报告 Markdown 从 `V5Output` 直渲染（[`engine/v5/report_view.py`](engine/v5/report_view.py)）。
- `DecisionRun`（L0-L9 账本）是旁路派生物，两条路互不消费。
- 所以分层裁判链**曾经从未真正决定过报告里的任何一句话**。

这与最早 R1 发现的"先让流派发言、再反推谁适用"是同一种倒置的不同部位。

### 3.2 R1-R9 全部落地（已验证）

主文档 §18 的状态标记已与代码核实一致。逐阶段：

| 阶段 | 做了什么 | 状态 | 关键测试 |
|---|---|---|---|
| R1 | 生产路由前置：`route_schools` 前置于命题层，删除 `_school_applicability` 命题反推 | ✅ 已完成 | tests/test_decision_v5_adapter.py |
| R2 | 路由接盘面结构信号：五行偏枯提 ditiansui、地支冲提 duan/ren | ✅ 已完成 | tests/test_l1_structural_signals.py |
| R3 | 反馈回打责任流派：单 run 内 miss → router 校准动作 | ✅ 部分完成（单run） | tests/test_l9_router_calibration.py |
| R4 | 分层准确率看板：按 verdict/层/域/事件类型聚合 | ✅ 聚合渲染完成 | tests/test_accuracy_report.py |
| R5 | 学习先验注入端：`route_schools(learned_prior=...)`，缺省零回归 | ✅ 注入端完成 | tests/test_l1_learned_prior.py |
| R6 | 报告改读 L7：五域裁决结论全部改读 `ReportViewItem` | ✅ 全域落地 | tests/v5/test_report_reads_l7.py |
| R7 | 加厚 L7：`_report_items` 聚合各派依据进 display_text | ✅ 已落地（并入 R6 节点） | tests/v5/test_report_reads_l7.py |
| R8 | L4 事件类型分类器：`classify_event_type` 从 event_label 派生类型 | ✅ 已落地 | tests/test_l4_event_type.py |
| R9 | L3 格局一致性审查：消费 v5 格局用忌神方向，依赖忌神命题降级 | ✅ 已落地 | tests/test_l3_geju_review.py |

### 3.3 R9 最新落地细节（本会话刚做）

- [`engine/decision/models.py`](engine/decision/models.py)：`SchoolClaim` 加 `metadata` 字段。
- [`engine/decision/v5_adapter.py`](engine/decision/v5_adapter.py)：`_claims` 透传 metadata；新增 `_extract_geju_profile`（提取格局用忌神）、`_shishen_in_statement`；`_verdicts` 叠加格局一致性审查。
- 实测效果：C-2026-035 的 L3 verdict 从"pass 287 / weaken 41 / reject 0"变为"pass 277 / weaken 51 / unknown 2"——**10 条依赖格局忌神的命题被正确降级**，L3 首次从"通道"变成有区分力的"关口"。

### 3.4 R10 第一证明物已完成（子平 × 事业原生 L2-L7 纵切片）

- 已完成 R10 第一证明物：子平 × 事业原生 L2-L4 纵切片 + L7 事业域单源渲染。
- 已证明目标路径不调用 adapter 的 L2 反推、L3 或 L4 判断；`validate_trace()` 返回空；报告事业域全部占位符（五派列 + 裁决 + 共识 + 冲突）仅从 L7 `ReportViewItem` 的结构化 `school_evidence` 派生，不存在 V5 claims 直读旁路；decision-run JSON 无损序列化同一 L7 内容；信息量 ≥ R6 基线（270 claims / 5 schools / 270 evidence，逐派逐域守住下限）。
- L3/L4 判断（`_extract_geju_profile` / `classify_event_type`）已从 adapter 归位到 `l3_structure.py` / `l4_events.py`；adapter 仅保留非目标流派/领域的迁移期桥。
- 这只证明第一条纵切片可行，**不表示 R10 全完成**：其他流派 / 领域迁移、adapter 全删、生产默认切换均未完成。
- K 系列尚未启动；当前 L3 / L4 只消费上游命题，不发明命理判断。
- **已知架构债（PRE_EXISTING_DEBT，来自 R9，非本分支引入）**：
  - L3 格局 profile 以全局 scope 应用于全体 claims（含非目标流派/域）；
  - L3 对 `event_claim` 无条件发 `weaken`，使无结构依据的事件命题获得 L4 进入资格。
  - 两项均为 R9 既有行为（本分支只做了位置迁移，行为等价），待 K 系列或后续迁移时收窄 scope。

### 3.5 真实案例闭环已跑通

C-2026-035（1988-11-15 男，甲戌日）已建立标准 case：
- 输入：[`cases/C-2026-035-乾-戊辰癸亥甲戌庚午/input.md`](cases/C-2026-035-乾-戊辰癸亥甲戌庚午/input.md)
- 报告：[`reports/C-2026-035-乾-戊辰癸亥甲戌庚午-v6-preprod-content-report.md`](reports/)
- 反馈入口：[`cases/C-2026-035-乾-戊辰癸亥甲戌庚午/feedback.md`](cases/C-2026-035-乾-戊辰癸亥甲戌庚午/feedback.md)（**等命主反馈填入**）

---

## 4. 当前卡在哪

**R1-R9 已全部落地；R10 已完成第一证明物，但尚未完成全部迁移。剩下 R10 后续迁移、K 系列（命理建模）两个大工程，外加一个数据瓶颈。**

R1-R9 都是"配管 + 消费 v5 已有结论"的重构。R10 第一证明物已证明子平 × 事业纵切片可行；往后按**先完成 R 系列后续迁移、再启动 K 系列**的排期推进（用户 2026-07-10 定）：

1. **R10 北极星（第一证明物已完成，后续迁移待做）**：子平 × 事业目标路径已经由原生 L2-L4 分层链产出，不调用 adapter 的 L2 反推、L3 或 L4 判断；但其他流派 / 领域尚未迁移，`v5_adapter` 尚未全删，生产默认入口尚未切换。下一步应沿已验证纵切片逐派逐域迁移，最终删除 adapter 的事后转录定位并切换生产默认报告入口。详见 [`plans/layered-decision-system.md`](plans/layered-decision-system.md) §R10（含 thesis / kill / options / 证明物 / 证伪）。

2. **K 系列命理建模（未启动）**：L3/L4 目前仍只消费上游已有命题，不自行发明命理判断。真正的原生命局判断（多域格局裁决 / 旺衰独立校验 / 五派结构交叉验证）是独立命理知识建模，见 plan §18bis K1-K3；须等 R10 后续迁移完成后再启动。

3. **数据瓶颈（贯穿始终、可并行积累）**：跨案学习（R5-B）与 K 系列校准都需真实反馈样本。R5 只做了注入端（learned_prior 能改路由），"从真实反馈聚合出 learned_prior"依赖足够有效反馈——按 `school×domain×role` 分桶、每桶 5-20 条起步、全域生产级需 1500+ 条。当前真实样本 = C-2026-035 一份（还没填）。

---

## 5. 下一步计划（按排期）

> 排期总纲（用户 2026-07-10 定）：**R10 第一证明物之后继续完成其他流派 / 领域迁移、adapter 全删与生产默认切换 → 再启动 K 系列**；真实反馈样本收集全程并行。

### 5.1 并行·立即可做（不需要新代码）
- **收集真实反馈**：让命主填 [`cases/C-2026-035-.../feedback.md`](cases/)，用 `python -m tools.feedback_ingest C-2026-035-乾-戊辰癸亥甲戌庚午` 摄入。多跑几个真实命盘，积累样本。这是 R5-B 与 K 系列校准的共同前置，越早开始越好。

### 5.2 R 系列收尾·继续做（R10 北极星）
- 子平派 × 事业域第一证明物已经完成：该目标路径原生产出 L2 `SchoolClaim`，不经 `v5_adapter` 做 L2 反推、L3 或 L4 判断；报告与 decision-run JSON 同源，`validate_trace()` 返回空，信息量不低于 R6 基线。
- 继续逐派逐域迁移，最后删除 `v5_adapter` 转录定位、切生产默认报告入口；在这些工作完成前，不得写成 R10 或 R 系列全完成。
- L3 / L4 继续遵守"只消费、不发明"；K 系列未启动，不得与 R10 配管迁移混做。

### 5.3 R 完成后启动（K 系列命理建模 + R5-B）
- **R5-B 跨案学习**（数据够了即可做）：从真实反馈聚合 `learned_prior`（`school×domain×role` 命中率）持久化回灌 `route_schools`。方向文档：[`docs/superpowers/plans/2026-07-09-r5-cross-run-routing-learning-direction.md`](docs/superpowers/plans/2026-07-09-r5-cross-run-routing-learning-direction.md)。**复用 `tools/feedback_loop.py` + `DomainRoleStats` 的 Beta 生命周期，不要新建平行学习系统。**
- **K 系列**（R10 下沉后启动）：K1 多域格局裁决 → K2 旺衰独立校验 → K3 五派结构交叉验证。每项独立用 geju 立项，不与 R10 配管混做。铁律：产出可被 L3/L4 消费的独立判断，但不得让 adapter 或报告层凭空发明命理。
- **同步更新 handoff**：只有 R10 其他流派 / 领域迁移、adapter 全删与生产默认切换全部落地后，才能把本文件 §3/§4/§5 推进到"R 系列全完成"；K 系列须实际启动后才能写"K 系列进行中"。

---

## 6. 踩过的坑，绝对不要再踩

### 6.1 工具与环境坑
- **`read_file` 工具在长会话里会频繁报 `missing nativeArgs` 失败**。绕过办法：用 `search_files` 定位，或用 `python -c "print(open(...).read())"` 读文件。
- **Windows 终端 stdout 中文/emoji 会乱码或 `UnicodeEncodeError`**。绕过：用 `sys.stdout.buffer.write(s.encode('utf-8','replace'))`；或写文件再 `type`。文件名里的中文在终端显示成乱码是正常的，路径本身没错。
- **cmd 的 `;` 链式 + 重定向会给 pytest 塞进 `;` 当参数导致 exit 4**。用 `&&` 串联，或分开跑。
- **`tests/v5` 跑得慢（60-70 秒）**，含真实报告渲染。别以为卡住了。

### 6.2 架构与判断坑
- **不要把 `plans/layered-decision-system.md` 当"感想文档"**。它是唯一架构事实源，改方向必须同步它，且它已与代码同步。
- **不要用四缺口的"逐个补占位符"思路**。R6-R9 看着像四个独立修补，但它们是同一个病灶（v5 推理/L0-L9 抄写）的四个部位。补占位符不改倒置。真正的解是让报告读 L7（已做 R6）+ 最终 v5 下沉 L2（未做）。
- **不要让 L3/L4 凭空发明命理判断**。R8/R9 的铁律是"只消费 v5 已算出的结论，不自行判旺衰/用神/事件"。给便宜模型写"发明命局规则"的计划会导致它瞎编命理。
- **L3 reject 要极度克制**：只在"依赖忌神 + 无 favor + 低置信"三条件同时满足才 reject，有疑问一律 weaken。**漏放好过错砍**。
- **不要让 `route_schools` 读文件或 import tools**。它必须保持纯函数，学习结果只能作为入参注入（R5 的 learned_prior 就是这么做的）。engine 层不做 IO。
- **不要新建平行学习系统**。仓库已有 `tools/feedback_loop.py` + `DomainRoleStats` + Beta 生命周期。跨案学习要复用它，不要另起炉灶。
- **真实反馈样本闭环必须"系统先分析→再反馈"**。不要直接注入"案例+结果"，那样没有系统当时的判断链，无法归因到层、无法学习。

### 6.3 展示层坑
- **报告 Markdown 禁止出现内部 ID**（claim_id/decision_id/statement_id 等）。见 [`AGENTS.md`](AGENTS.md) §5.2 展示层禁显约束。R7 加厚 L7 时特意只聚合可读文本。

### 6.4 流程坑
- **完成前必须真跑验证命令**，不许说"应该可以"。本仓库用 verification-before-completion 纪律：跑测试、读输出、确认 exit 0，再下结论。
- **临时文件记得删**。本会话残留了一个 `_r9res.txt`（失败命令产物），可以删掉：`del _r9res.txt`。

---

## 7. 什么时候用哪个模型（成本优化）

用户在不同节点切换模型控制成本。经验规则：

### 用 claude-fable-5（贵，判断力强）——重要节点
- 写**方向决策 / 格局判断 / geju 分析**（如 R5 方向文档、L0-L9 重构判断）。
- 写**交接文档、最终结论、架构总结**（如本文件）。
- **调查根因、需要判断命理边界**的任务（如 R9 的 L3 审查设计——涉及命理对错）。
- 遇到"两条路怎么选"的架构岔路口。

### 用 chatgpt codex 5.5（便宜）——机械执行
- 执行**已写好的 bite-sized TDD 执行计划**（R6/R7/R8 那种，每步都有完整可粘贴代码 + 验证命令）。
- 纯**配管代码替换、跑测试、改文案**。
- 前提：计划里已经把命理判断都锁死成"只消费不发明"，codex 只做搬运，不做判断。

### 用 claude-sonnet-4-6（当前默认，便宜档）——日常
- 读代码、跑验证命令、查事实、小改动。
- 调查阶段（收集事实，还没到下结论）。

### 切换信号（我会主动提示）
- 到"输出最终结论 / 写重要文档 / 做架构判断"节点时，我会停下说**"请切到 claude-fable-5"**。
- 到"执行已定稿的机械计划"时，我会说**"这步可以交 codex 5.5"**。
- 调查/读代码阶段，用当前便宜模型即可，我不会打断。

---

## 8. 新会话快速上手命令

```bash
# 确认系统能跑 + 核心链路测试
python tools/tool_registry.py --check
python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q

# 跑一个真实案例看完整闭环产物
python tools/render_report_v6.py cases/C-2026-035-乾-戊辰癸亥甲戌庚午/input.md --output-dir reports

# 看 R9 L3 审查是否生效（应看到非零 weaken）
python -c "import json,pathlib,sys; from collections import Counter; d=json.loads(pathlib.Path('reports/C-2026-035-乾-戊辰癸亥甲戌庚午-v6-preprod-content-report.decision-run.json').read_text(encoding='utf-8')); c=Counter(v['verdict'] for v in d['structural_verdicts']); sys.stdout.buffer.write(str(dict(c)).encode('utf-8'))"

# R1-R9 全部相关测试
python -m pytest tests/test_l3_geju_review.py tests/test_l4_event_type.py tests/test_l1_structural_signals.py tests/test_l1_learned_prior.py tests/test_l9_router_calibration.py tests/test_accuracy_report.py tests/v5/test_report_reads_l7.py -q
```
