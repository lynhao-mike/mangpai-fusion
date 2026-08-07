# as-of 盲断闭环 · 大规模扩样（50+）与后续候选 geju 裁决 · Terra 无人值守提示词

> 本文件交付一份可直接粘贴给下一会话的执行提示词。任务分两段，必须在同一受控会话内顺序完成：
> 1. 用剩余候选池把 as-of 真实盲断闭环样本量扩大到 **50+**（从当前累计 N=5 继续）。
> 2. 扩样任务收口后，用 geju skill 对候选 A（接入 blind-bundle 协议）、候选 C（G6 Task 9-P P-2 BLOCKED）、
>    候选 D（F10 业务目标 HOLD）做一次格局裁决，判断哪个更值得推进（不要求当场执行，只裁决优先级）。
>
> 已完成部分（只读继承，不重开）：
> - 候选 B 首轮：[`reports/as-of-life-state-blind-judgment-batch-report.md`](../reports/as-of-life-state-blind-judgment-batch-report.md)（N=3，命中率 2/3）。
> - 候选 B 扩样：[`reports/as-of-life-state-blind-judgment-n5-extension-report.md`](../reports/as-of-life-state-blind-judgment-n5-extension-report.md)（累计 N=5，命中率 4/5）。
> - 候选 E：[`plans/as-of-life-state-blind-judgment-probe-table-annotation-detection-contract.md`](as-of-life-state-blind-judgment-probe-table-annotation-detection-contract.md)（`detect_table_embedded_annotation()` 已上线，可选调用）。

---

## 提示词正文

````text
你正在 mangpai-fusion 仓库承接一个长任务续接，分两段执行，必须在同一受控会话内完成：

第一段：把 as-of 真实盲断闭环样本量从当前累计 N=5 扩大到 N≥50。
第二段：用 geju skill 对候选 A/C/D 做一次格局裁决，判断优先级（不要求执行，只裁决）。

## 第一段：大规模扩样至 50+

### 必读事实源（按顺序，恢复上下文用，不全文复述）

1. AGENTS.md（尤其禁止事项一节）
2. META/project-state.json
3. reports/as-of-life-state-blind-judgment-batch-report.md（首轮N=3，只读不重开）
4. reports/as-of-life-state-blind-judgment-n5-extension-report.md（扩样N=5，只读不重开）
5. plans/as-of-life-state-blind-judgment-n5-extension-contract.md（N5合同，理解已冻结的写集/排除规则）
6. plans/as-of-life-state-blind-judgment-probe-table-annotation-detection-contract.md（E的产物，含新增
   detect_table_embedded_annotation() 函数说明，本轮应实际使用该函数辅助安全审计，而不是重新发明检测逻辑）
7. tools/as_of_blind_judgment_probe.py（截断+检测函数实现，只读依赖，不修改）

### 候选池现状核实（不得凭旧结论假设数字）

上一轮记录候选池约有93个安全的C-2026-RF*候选未使用，但这是上一轮某个时刻的观察，本轮必须重新
执行一次新鲜的机械枚举来确认当前真实剩余候选数量（cases/目录内容可能已变化）。核实步骤：

1. 列出cases/下同时具备input.md与feedback.md、且案例ID为C-2026-RF*前缀的全部目录；
2. 排除首轮（3个）与扩样轮（3个，含1个无效样本）已触碰的全部6个案例ID（从上述两份报告的
   §3/§4提取，不得凭记忆或猜测）；
3. 排除Mang.pai旧格式池全部已触碰的7个案例（007/008/009/010/011/012/017，来自
   reports/as-of-life-state-blind-judgment-batch-report.md §2.2/§2.3）；
4. 对剩余候选，用truncate_blind_section()确认yaml_key或heading边界存在（cut不为None）；
5. 用已有的真实事实词表 + detect_table_embedded_annotation() 做双重内容盲审计，只输出布尔值，
   不展示正文；
6. 只有通过全部审计的候选才能进入执行池。

如果新鲜核实后发现候选池不足50个安全候选，如实报告实际可用数量并在该数量上尽力执行，不得
编造候选或强行降低安全审计标准来凑够50个。

### 执行纪律（与B/E一致，不可协商）

- 沿用candidat B合同的两阶段不可逆协议：阶段一（截断→冻结盲断→落盘，feedback_opened=false）
  必须完全早于阶段二（打开feedback.md→核验→落盘）。
- §6.6根源×完成方式白名单原样沿用（STRONG_ROOT+ACTIVATE_EXISTING /
  STRONG_ROOT+REPAIR_DEFECT / WEAK_ROOT+COMPLETE_LATENT / WEAK_ROOT+TEMPORARY_SUBSTITUTE /
  NO_ROOT+TEMPORARY_SUBSTITUTE；INVALID_COMPLETION仅反证审计不入冻结包）。
- 反馈揭示后若发现某案例窗口内无可评分事业事件，如实记录为"无效样本"，不计入命中率分母，
  不得为凑数字牵强判定。
- 只允许新增：每案两个JSON制品（frozen-draft.json / verified-result.json，沿用与N5轮相同的
  schema_version与文件命名）、一份新的独立增量报告（不得修改任何既有报告正文）、截断/审计
  临时文件（用后立即删除）。
- 禁止修改：engine/asof/ 任何文件、tools/as_of_blind_judgment_probe.py、任何既有报告正文、
  任何既有测试、任何案例既有文件、handoff.md。
- 禁止任何 Git 或 GitHub 操作。
- 污染处理：延用"累计3次触发硬停止、换池或BLOCKED"规则；若在扩样过程中再次发现类似候选10
  的表格内嵌注释污染，必须使用已上线的detect_table_embedded_annotation()先行拦截，若仍发生
  真实污染，按协议立即停止该案、如实记录，不得静默跳过。

### 效率要求（50+样本量的必要调整）

- 允许批量化：可以先批量完成全部候选的阶段一冻结（每案落盘后立即验证幂等哈希），再批量进入
  阶段二核验，只要严格保证"该案例阶段一冻结完成之后才打开该案feedback.md"这一顺序对每案
  独立成立即可，不要求全局串行。
- 判定理由可以简化篇幅（不需要每案都写长段落），但必须保留：候选ID、as_of_date选定依据、
  冻结候选事件的根源×完成方式组合、冻结哈希、反馈揭示后的四选一判定与关键证据引用。
- 最终报告允许用汇总表格呈现逐案结果，不要求每案单独展开成小节（但仍应保留可追溯的哈希与
  candidate_id）。

### 第一段验证与裁决

- VERIFY：对全部新增案例做冻结哈希幂等复跑，记录真实结果。
- 最终裁决只能是：
  - PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE（累计有效案例达到或接近50，命中率以分数呈现）；
  - BLOCKED — <具体原因>（候选池不足或污染预算耗尽导致未达50）。
- 产出独立报告 reports/as-of-life-state-blind-judgment-n50-extension-report.md，
  合并累计所有轮次（首轮N=3 + N5轮N=2 + 本轮）的命中率汇总表。

## 第二段：候选 A/C/D 的 geju 格局裁决

第一段收口（PASS或BLOCKED均可）后，调用本仓库.roo/skills/geju/SKILL.md定义的geju skill，
对以下三个候选做一次格局裁决：

- 候选A：把as-of引擎接到tools/school_capability_prospective.py的blind-bundle隔离协议上
- 候选C：解决G6 Task 9-P P-2 producer-owned current-run identity authority的BLOCKED
- 候选D：F10业务目标裁决（G10.10=HOLD）

裁决前必须先读取：
- plans/as-of-life-state-next-task-geju-adjudication-2026-07-28.md（候选A的历史裁决上下文）
- handoff.md 第8-9节（候选C的BLOCKED历史）
- plans/production-implementation-control.md 最后60-100行（候选D的HOLD历史）
- 第一段刚产出的50+样本量报告（作为"as-of盲断闭环价值是否已经充分证明"的新证据输入）

geju裁决必须产出：
1. 一句尖锐的thesis：结合第一段50+样本的真实命中率数据，判断"继续加深as-of盲断闭环深度"
   （即候选A）与"转向F09生产切片遗留问题"（候选C）与"F10业务目标裁决"（候选D）三者的
   相对杠杆，是否因为样本量已经足够大而发生变化；
2. kill-list：该候选清单中是否有候选因为第一段证据的出现而变得明显不值得做；
3. 保守/干净/分阶段三选项对比，并明确推荐一个；
4. 一条可验证路径：如果推荐的候选被采纳，First Proof Point是什么、什么证据会推翻这个方向；
5. 收益账单：讲清推荐方向为什么值得它的代价。

裁决产物写入 plans/as-of-life-state-next-task-geju-adjudication-<当前日期>.md
（延续既有命名惯例），不得执行该裁决推荐的候选本身——第二段只裁决优先级，不动手实现。

## 硬边界（覆盖两段，不可协商）

- 只允许新增本任务自己创建的文件（案例JSON制品、增量报告、geju裁决文档）；不得修改任何
  既有文件（包括所有历史报告、合同、handoff.md、engine/、tools/as_of_blind_judgment_probe.py）。
- 禁止任何 Git 或 GitHub 操作。
- 第二段的geju裁决只产出判断文档，不得据此自动启动候选A/C/D的实现；若裁决后想继续做，
  需要用户看到裁决结果后另行明确指令。
- 全程保持 LOCAL ONLY / NOT PUSHED。

## 完成后的汇报格式

最终回复必须包含：第一段候选池新鲜核实结果（真实剩余数量）、全部执行案例的逐案摘要表
（案例ID/root_level/completion_mode/四选一判定）、累计命中率（含历次轮次合并计算）、
第一段最终裁决、第二段geju裁决全文摘要（thesis/kill-list/三选项/推荐/验证路径）、
新增文件完整清单、唯一下一动作。不得省略任何一项，也不得用推测替代真实文件内容或
真实命令输出。
````

---

## 交付边界

本文件不预先判断候选池是否真的能凑够50个安全案例，也不预判geju裁决会推荐A/C/D中的哪一个——两者都留给续接会话在受控执行中用真实证据得出结论。
