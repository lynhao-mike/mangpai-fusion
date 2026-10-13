# as-of 真实盲断闭环 · 多轮持续扩样 · Terra 无人值守提示词

> 本文件交付一份可在多个独立受控会话中反复使用的执行提示词，用于持续扩大 as-of 真实盲断闭环的样本量。**每次使用本提示词只完成一轮"力所能及"的真实扩样，不承诺凑到任何预设的 N 值**。
>
> 已完成的历史轮次（只读继承，不重开）：
> - First Proof Point：[`reports/as-of-life-state-blind-judgment-first-proof-point-report.md`](../reports/as-of-life-state-blind-judgment-first-proof-point-report.md)（N=1）。
> - 批次 B：[`reports/as-of-life-state-blind-judgment-batch-report.md`](../reports/as-of-life-state-blind-judgment-batch-report.md)（N=3）。
> - N5 扩样：[`reports/as-of-life-state-blind-judgment-n5-extension-report.md`](../reports/as-of-life-state-blind-judgment-n5-extension-report.md)（累计 N=5）。
> - N50-R2：[`reports/as-of-life-state-blind-judgment-n50-extension-report-r2.md`](../reports/as-of-life-state-blind-judgment-n50-extension-report-r2.md)（累计 N=8，命中率 5/8）。

---

## 提示词正文

````text
你正在 mangpai-fusion 仓库承接"as-of 真实盲断闭环"任务的第 N+1 轮持续扩样。这不是一次性任务,
是可重复执行多轮的长期证据积累工作。每一轮的目标是：在你的上下文预算内，尽可能多地完成新增
真实盲断案例，不设固定样本量目标，完成后诚实报告实际数量并停止。

## 核心原则（贯穿全部轮次，不可协商）

1. **真实瓶颈是命理学判读产能，不是执行工具。** 历史 N50-R2 轮已证实：把冻结管线写成独立
   .py 脚本文件（而非塞进单条 shell 内嵌命令）可以完全解决执行工具层面的问题；但每案独立的
   排盘阅读、原局承载图构造、大运阶段适配、根源×完成方式判定——这部分不能压缩、不能模板化、
   不能用上一案的判读结构套用到新案。若发现自己在"复制粘贴上一案的判读理由，只换掉几个字"，
   立即停止，这已经不是盲断，是伪造证据。
2. **禁止使用"真实准确率""引擎准确性""证明有效性"这类措辞描述任何单轮或累计结果。** 每一轮
   新增的样本只是"多一个独立数据点"，不是向着某个可信区间收敛的统计过程。样本选择方式（固定
   队列顺序、字典序）不是随机抽样，存在系统性选择偏差，永远不能用频率学派的"准确率估计"框架
   去解读这些数字。累计命中率只能报告为"截至目前观察到的分数"，并且必须在同一句话里附上样本
   量过小、非随机抽样的免责声明。
3. **不设固定样本量目标。** 本提示词的"多轮"是指跨会话累积，不是单轮内硬凑数字。每轮完成后
   如实报告本轮新增数量（可能是 3 个，可能是 10 个，取决于当轮上下文预算与案例证据密度），
   不得因为"离目标还差很多"而降低判读质量、压缩阅读排盘的时间、或编造判定理由。
4. **无效样本必须诚实记录，不得为凑数字牵强判定。** 若反馈揭示后窗口内无可评分事业事件，记
   为无效样本，不生成 verified-result，不计入命中率分母。历史轮次显示无效样本率可能高达
   30-50%（尤其当候选命主截止 as_of_date 时仍是学生），这是真实情况的一部分，不是失败。
5. **只允许本地只读/本地新增文件；禁止任何 Git 或 GitHub 操作。**

## 必读事实源（每轮开始时按顺序读取，不全文复述）

1. `AGENTS.md`（禁止事项一节）
2. `META/project-state.json`
3. 历史全部 as-of 盲断闭环报告（按时间顺序）：
   - `reports/as-of-life-state-blind-judgment-first-proof-point-report.md`
   - `reports/as-of-life-state-blind-judgment-batch-report.md`
   - `reports/as-of-life-state-blind-judgment-n5-extension-report.md`
   - `reports/as-of-life-state-blind-judgment-n50-extension-report-r2.md`
   - 以及本轮开始前已存在的任何后续轮次报告（按文件名日期/轮次编号排序，全部读取）
4. `tools/as_of_blind_judgment_probe.py`（`truncate_blind_section()` 与
   `detect_table_embedded_annotation()` 的签名与用法）
5. `engine/asof/` 下 `natal_capacity.py`、`daiyun_context.py`、`event_candidate.py`、
   `consultation_freeze.py`、`reality_translation.py`、`session_contract.py`、
   `session_runner.py`、`career_state_builder.py`、`state_ledger.py` 的公共 API 签名
   （只读依赖，不修改；若某轮编排库文件仍保留在工作区，可直接复用其函数签名参考）

## 候选池管理（每轮必做，不得跳过）

1. **新鲜机械枚举**：不得假设候选池数量与任何历史报告记录的数字相同,必须重新枚举
   `cases/` 下 `C-2026-RF*` 前缀、同时具备 `input.md` 与 `feedback.md` 的目录。
2. **排除清单**：从历史全部报告中提取已触碰案例 ID 列表（含有效样本、无效样本、污染案例），
   排除后才是本轮候选池。
3. **双重安全审计**：对候选池逐个调用 `truncate_blind_section()`（`cut` 必须非 None）与
   `detect_table_embedded_annotation()`（必须零命中），并用历史报告记录的校正后真实事实词表
   做布尔扫描。只输出布尔值/行号/边界类型，不展示正文片段。
4. **候选选择**：按案例 ID 字典序选取（延续历史轮次的客观、可复现选择规则），不得凭案例名称
   或任何先验信息挑选"看起来容易命中"的候选。

## 执行纪律（每案独立执行，不可协商）

沿用历史轮次已冻结的两阶段不可逆协议：

1. 只读取该案 `input.md`，调用 `truncate_blind_section()` 得到截断视图。
2. 只基于截断视图做真实命理学判读：日主根气（十二长生）、十神结构（透干/藏干/主气中气余气）、
   竞争解释、大运阶段适配。选定根源×完成方式组合，只能是以下白名单之一：
   - STRONG_ROOT + ACTIVATE_EXISTING
   - STRONG_ROOT + REPAIR_DEFECT
   - WEAK_ROOT + COMPLETE_LATENT
   - WEAK_ROOT + TEMPORARY_SUBSTITUTE
   - NO_ROOT + TEMPORARY_SUBSTITUTE
3. 选定 as_of_date 时优先考虑命主年龄与事业阶段匹配度（历史 N50-R2 轮教训：候选命主截止
   as_of_date 时仍是学生会导致高比例无效样本；应优先选择大运中后段、命主已过 25 岁的窗口，
   除非命盘本身的大运结构只允许更早窗口）。
4. 通过真实 `engine.asof` API 构造 `NatalCapacityGraph`/`DaiyunStage`/事件候选/落点集合，调用
   `freeze_career_draft()`、`compute_freeze_package_sha256()`，create-only 落盘 frozen-draft.json
   （文件名与 schema_version 延续历史轮次约定，或在本轮报告中明确记录本轮使用的文件名约定）。
5. 冻结落盘并验证幂等哈希后，才允许读取该案 `feedback.md`。
6. 反馈揭示后独立判定四选一（CONFIRMED/PARTIAL_HIT/REJECTED/无效样本），判定理由必须基于
   反馈具体内容独立写作，不得照抄历史轮次任何案例的判定模板。
7. PARTIAL_HIT/CONFIRMED 的 `actual_landing_name` 必须与冻结包内预先注册的中心或替代落点
   名称字符串完全一致（历史教训：自由文本描述会触发引擎校验拒绝）。
8. 非 REJECTED 的核验需要提供对应的 `CareerImpactSuggestion`/`CareerImpactAdjudication`/
   `CareerFundamentalAdjudication`，调用 `run_career_session()` 完成完整核验。

## 效率工具（可选，不强制）

若发现执行工具层面出现新的技术障碍（不是判读产能问题），可参考历史 N50-R2 轮的修复方式：
把冻结/核验逻辑写成独立 `.py` 脚本文件（用 `write_to_file` 创建），通过 `python script.py`
执行,避免把整条调用链塞进 shell 内嵌命令。若需要跨脚本复用对象（如先冻结、后核验），可用
`importlib.util.spec_from_file_location()` 动态加载，但必须记得把加载的模块注册进
`sys.modules`（Python 3.14 的 dataclass 类型解析依赖这一步，否则会抛出
`AttributeError: 'NoneType' object has no attribute '__dict__'`）。所有临时脚本必须在
本轮完成后立即删除，不得作为案例专属产物保留在案例目录内。

## 写集白名单

只允许新增：

1. 每个新案例目录内的 frozen-draft.json（若产生 verified-result 则一并新增）。
2. 一份本轮独立的增量报告 `reports/as-of-life-state-blind-judgment-<轮次标识>-report.md`
   （轮次标识需与历史轮次区分，如日期或序号）。
3. 执行期间使用的临时脚本/临时截断视图文件（`.tmp.py`/`.tmp.md`/`.tmp.txt`），使用后立即删除。

禁止修改任何既有文件，包括但不限于：`engine/asof/` 任何文件、`tools/as_of_blind_judgment_probe.py`、
历史全部 as-of 报告与合同正文、任何案例既有的 `input.md`/`feedback.md`/`statement_index.json`、
任何既有测试、`handoff.md`。

禁止任何 Git 或 GitHub 操作（本地与远端均不可）。

## 污染处理

沿用历史轮次协议：同一会话累计污染 3 次触发硬停止。若阶段一读取截断视图时发现现实履历泄露
（包括但不限于头部来源描述、命主代号注释、大运表格内嵌括号注释——后者已有
`detect_table_embedded_annotation()` 检测，但该检测不保证覆盖所有变体），立即停止该案，
记录污染事件，换用候选池中下一个候选。

## 本轮报告必须包含的内容

1. 候选池新鲜枚举结果（真实数字，不沿用历史假设）。
2. 本轮逐案摘要表（案例ID / as_of_date / root_level+completion_mode / 四选一判定）。
3. 无效样本与污染事件的诚实记录。
4. 技术失败记录（如有），含根因分类（执行工具问题 vs 判读产能问题 vs 脚本参数错误）。
5. 哈希与写集核验的真实命令输出。
6. **累计命中率汇总表**：列出本轮新增与历史全部轮次的合并累计（有效样本数、命中数、部分命中
   数、失验数、命中率分数）。命中率必须以分数形式呈现（如"7/12"），禁止简化为单一百分比后
   丢弃分母，禁止使用"准确率"这个词汇描述该分数。
7. **已知的方法论局限**章节，原样声明历史全部轮次已记录的局限，并追加本轮新发现的局限
   （如果有）。
8. 直接证明与禁止推断两个清单，明确写出"不得推断 as-of 引擎存在某个'真实准确率'，本轮及
   历史累计的所有分数都只是特定选择方式下的观察值，不构成对总体的无偏估计"。
9. 新增文件完整清单。
10. 最终裁决：
    - `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`（本轮完成至少 1 个新增有效或无效样本，
      且全部证据核实一致）；
    - `BLOCKED — <具体原因>`（如遇到污染预算耗尽、候选池耗尽、或无法在本轮完成任何新案例）。
11. `LOCAL ONLY / NOT PUSHED` 声明。
12. 遗留问题：明确写出"若要继续扩样，应在下一轮独立受控会话中使用同一份提示词继续执行"。

## 硬边界

- 不得在任何时候声称已经"证明"或"证伪"了 as-of 引擎的命理学有效性。
- 不得因为追求样本量而牺牲判读的独立性——如果发现自己在无意识地让新案例的判读结构趋同于
  历史案例（例如连续多案都选 WEAK_ROOT+COMPLETE_LATENT 且判读理由高度相似），应停下来
  重新审视是否真的在做独立判读，还是在套模板。
- 不得执行任何 Git 或 GitHub 操作。
- 不得把多轮累计的命中率数字用于任何生产决策、规则调整或路由权重变更——这仍然只是认识论
  探索阶段的证据积累，不是可以直接消费的置信度输入。
````

---

## 交付边界

本文件本身不执行任何扩样轮次,也不预先决定某一轮应该完成多少个案例——这些都留给持续
使用本提示词的每一次受控会话根据当时的真实上下文预算自主判断。是否需要在积累到某个样本
量后触发进一步的方法论审视（例如是否需要引入随机抽样而非固定队列顺序），需要用户在看到
多轮累计结果后另行决定，不属于本提示词范围。
