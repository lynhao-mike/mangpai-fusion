# HANDOFF · 会话交接文档

> 写给一个完全没有上下文的新会话。读完这份文档 + [`AGENTS.md`](AGENTS.md) + 下面列出的两份主干文档，你就能无缝接手。
> 生成时间：2026-07-15
> 本文件只作短期交接，不是长期事实源。长期事实源见 [`AGENTS.md`](AGENTS.md) 第 3 节事实源矩阵。

---

## 1. 我们在做什么任务

本仓库 `mangpai-fusion` 是四派盲派融合八字分析系统。当前这一轮工作**不是日常出报告**，而是**架构升级规划**：把系统从"手工专家系统"演进为"可学习的八字智能推理平台"。

本轮会话的具体任务：**基于两份主干文档，制定未来 6 个月的分阶段实施路线**，并确认五派能力矩阵与任务分配。

两份主干文档（必读，优先级最高）：
1. [`docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md`](docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md) —— 目标架构核心设计（"宪法"，定义十层分权、核心对象、非谈判原则）
2. [`plans/bazi-intelligence-platform-roadmap.md`](plans/bazi-intelligence-platform-roadmap.md) —— 推进与验证路线（阶段门禁、H1-H6 假设、Phase 0-5）

配套升级指导文档在 [`plans/upgrade-guides/`](plans/upgrade-guides/)（00-06 共 7 份）。

---

## 2. 已经完成了什么

### 2.1 核验结论（本会话第一阶段）
核验了 [`plans/upgrade-guides/00-overview-and-sequencing.md`](plans/upgrade-guides/00-overview-and-sequencing.md) 清单，结论：
- 升级单元 **01（命局特征向量 cfv-v1）** ✅ 已落地：[`engine/features/`](engine/features/) + [`tests/features/test_chart_feature_vector.py`](tests/features/test_chart_feature_vector.py)
- 升级单元 **02（L2 命题引擎化）** ✅ 两派最小闭环已落地：[`engine/claims/`](engine/claims/) + [`engine/v5/ziping_runner.py`](engine/v5/ziping_runner.py) + [`engine/v5/ren_runner.py`](engine/v5/ren_runner.py)
- 升级单元 **03（评估数据地基）** ✅ 历史隔离基线 GO：[`META/school-capability-baseline-2026-07-14.md`](META/school-capability-baseline-2026-07-14.md)（64 冻结案、39 标注案、非空后验 N_eff=5.0）
- 升级单元 **04（L1 可学习路由）** ⚠️ HOLD：[`reports/l1-routing-holdout-comparison.md`](reports/l1-routing-holdout-comparison.md)（竞争样本 3<5，不足以判 GO）
- 升级单元 **05（L6 分段仲裁）** ✅ staged 已落地：[`engine/decision/l6_staged_arbitration.py`](engine/decision/l6_staged_arbitration.py)
- 升级单元 **06（L9 条件化学习）** ✅ offline staged 已落地：[`engine/learning/`](engine/learning/)
- 测试状态：升级相关子集 **391 passed**；tool registry check + rule status scan 均通过（曾运行全量 pytest，只见 skip 无 fail）。

### 2.2 六个月路线的关键决策（已获用户批准）
经多轮确认，用户最终选定的方案边界：
- **优先级路径**：先完成五派标准 Claim 覆盖，再集中补数据验证（不是先纵深单领域）。
- **覆盖深度**：中等覆盖 —— 每派完成 2-3 个强项任务，覆盖结构 / 事件 / 应期三类 Claim。
- **能力矩阵调整**：减少画像任务，增加财富和事业可量化任务。
- **应期 runner 决策**：**任派 + 段派同时实现 timing runner 作为双主力，高派放第二批。**
- **时间尺度**：6 个月，从数据 → 知识重铸 → 路由验证 → 第 4 个月起吸收"新旧并跑"。

### 2.3 五派能力矩阵（已获用户批准，基于原始资料第一手证据核实）
| 流派 | 核心擅长 | 独有武器 |
|---|---|---|
| 子平 | 格局成败定性 + 旺衰多口径 + 调候用神 | 八格取运体系 |
| 段派（段建业）| 做功体系 + 宾主论 + 应期4大类工程化 + 职业/牢狱/车祸 | 宾主体用、反客为主应期 |
| 任派（任付红）| 十八道法门 + 应期直定 + 穿的系统化 + 疾病/寿命/六亲 | 合留婚期法、直定应期法 |
| 高派（高德臣）| 神煞实战 + 串宫压运 + 流年有根论 + 财运应期6条 | 命宫长生诀、流年有根论 |
| 杨派（杨清娟）| 婚姻全套规程 + 调候改运 + 禄的多维应用 + 气数论 | 婚姻操作规程、转象换象 |
| 滴天髓 | 寒暖燥湿调候 + 真假用神 + 五行颠倒 + 从化格 | 寒暖燥湿轴（cfv-v1 已实现）|

任务分配（已批准）：
- 结构类 `structure.overview`：子平主 + 滴天髓副
- `career.role_change`：子平 + 段派
- `marriage.divorce`：杨派 + 段派
- `wealth.debt`：段派 + 高派
- `career.path_type`：段派 + 子平
- `health.system_risk`：高派 + 任派
- 时间窗（career/marriage/health/wealth）：**任派 + 段派双主力，高派第二批**

用户最后一条指令是"同意，执行"。

---

## 3. 当前卡在哪

**卡点 1：路线文档尚未落盘。**
用户已批准完整六个月方案（能力矩阵 + 任务分配 + 双主力 timing 决策），但**批准的方案还没有写入 `plans/` 下的正式规格文档**。TODO 第 6 项仍是 In Progress，第 7、8 项（写规格 + 编详细实施计划）仍 Pending。

原因：上一会话上下文窗口接近极限，搜索原始资料（sources/ 五派教材）消耗了大量 token，没来得及落盘就要交接。

**卡点 2：升级单元 04（L1 可学习路由）业务上 HOLD。**
不是代码问题，是**真实前瞻样本不足**——现有 133 案 blind eligible=0，990/Top30 都是 feedback-first（先有反馈后补排盘），不能冒充 prospective 盲测。这是外部数据采集门槛，无法用代码/并行 agent 绕过。

---

## 4. 下一步计划

按优先级：

1. **【立即做】把已批准的六个月路线写成正式规格文档**，建议路径 `plans/upgrade-guides/6-month-execution-plan-2026-07.md` 或 `docs/superpowers/specs/`。内容必须包含：
   - 第 2.2 节的路径 / 覆盖深度 / 应期双主力决策
   - 第 2.3 节的五派能力矩阵与任务分配表
   - 每月交付物、阶段门禁（GO/HOLD/STOP）、回退策略
   - 阶段①(月1-2) 数据+五派Claim覆盖 → 阶段②(月3) 知识重铸 → 阶段③(月4) 路由验证 → 阶段④(月4-6) 新旧并跑
2. 写完规格后跑自检（占位符扫描、内部一致性、范围检查），再请用户 review。
3. review 通过后用 writing-plans 编详细实施计划。
4. 实施第一步落在：**段派 timing runner**（`engine/v5/` 下新建，参照现有 `ren_runner.py` 结构）+ 对应任务目录扩展。

---

## 5. 踩过的坑，绝对不要再踩

1. **不要在长上下文里反复全文搜索 `sources/` 五派教材。** 每份教材几十万字，`search_files` 一次能吐 300+ 条截断结果，几次就把上下文烧光。要查某派应期理论，先定位到具体文件再 `read_file` 精确区间，或用 codebase_search 语义检索。

2. **不要把 feedback-first 历史案例当 prospective 盲测。** 990/Top30/wenzhen 全是"先有真实反馈、后补排盘生成报告"，逐案 provenance 已标 `feedback_predates_system_prediction`。把它们改名为 historical blind 会构成标签泄漏，整批作废。L1 路由 GO 必须靠真实前瞻新案。

3. **不要从阶段名推断产品版本。** [`META/project-state.json`](META/project-state.json) 的 `current_phase` 是工作阶段，产品版本永远以 [`VERSION`](VERSION) 为准。

4. **不要硬编码易漂移数据。** N_eff、规则数量、flagged/deprecated 清单、git HEAD 一律运行时扫描（`python tools/rule_status_scan.py`、`git rev-parse HEAD`），不要写进文档正文。

5. **命题引擎化必须先于/同步于 L1 学习化。** 若 L2 命题仍人工写入，能力后验只反映"写命题的人"的水平，飞轮学的是噪声（宪法附录 A.4.3）。这是整个升级的成败真实性红线。

6. **timing runner 决策已定为任派+段派双主力，不是只有任派。** 早期讨论里差点把应期任务只分给任派，但原始资料证明段派应期体系（应期4大类 + 三法则工程化 + 反客为主）与任派并列第一。高派的"流年有根论"放第二批。

7. **报告出口禁显内部 ID。** 统一报告禁止展示 statement_id、共识/互补/独门/冲突 ID、章节编号、关联裁判等（AGENTS.md 展示层禁显约束）。规格文档本身不受此限，但任何面向命主的产物受限。

8. **不要用 deprecated / missing 工具。** `calibrate.py` 已 deprecated；`seal_prediction.py`/`verify_evidence.py` 等从不存在。反馈入口用 [`tools/feedback_ingest.py`](tools/feedback_ingest.py)。

---

## 6. 快速上手命令

```bash
# 看当前项目机器状态
cat META/project-state.json

# 跑升级相关测试（应 391 passed 或更多）
python -m pytest tests -q

# 工具与规则状态自检
python tools/tool_registry.py --check
python tools/rule_status_scan.py --check

# 现有两派 claim runner 参考实现
#   engine/v5/ziping_runner.py  (子平结构命题)
#   engine/v5/ren_runner.py     (任派应期时间窗命题)
#   engine/claims/orchestrator.py (generate_blind_outputs / generate_frozen_claim_run)
```
