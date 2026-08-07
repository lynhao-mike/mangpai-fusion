# as-of 真实盲断闭环 · First Proof Point · Terra 无人值守执行提示词

> 本文件只交付一份可直接粘贴给 ChatGPT 5.6 Terra 的执行提示词；不在本文件内实施该长任务。
>
> 来源：本提示词是对"婚姻域 as-of G0-G5"候选方案的 geju 格局判断结果。判断结论：加一个新领域只是第三次"历史回放证明内部一致性"，不产生新证据类型；`AGENTS.md` 第 6 节明确指出现有 as-of 报告（Unit8-11）"从未在'不知道答案'的条件下被测试过盲断准确率"，这才是当前最高杠杆的验证缺口。本任务就是解除这句免责声明的第一步：用一个此前从未被任何 as-of 工作触碰过的真实案例，严格执行"先读命盘冻结盲断、再读反馈核验"的两阶段协议，产出这个项目历史上第一份关于"as-of 推理本身是否真的能盲断准确"的证据。

## 使用说明

- 直接把"提示词正文"整段粘贴给 Terra 作为单次会话的完整任务说明。
- Terra 必须在**全新会话**中执行本任务，不得复用任何已经读过案例反馈内容的历史上下文。
- 本任务**不新增 `engine/asof/` 任何代码**，纯粹复用 Unit8-11 已冻结的公共 API（`session_contract`、`consultation_freeze`、`event_candidate`、`natal_capacity`、`daiyun_context`、`session_runner`），只是把它们用在一个从未被使用过的案例上，并首次严格执行"先冻结再揭示"的真实时间顺序。
- 允许 Terra 在提示词内部自行拆出子任务，但必须在同一对话内完成，不得请求切换会话。

---

## 提示词正文

```text
你正在 mangpai-fusion 仓库承接长任务：as-of 真实盲断闭环 First Proof Point。这是一次探索性验证，不是新功能开发。目标是产出项目历史上第一份"as-of 推理在不知道答案的情况下能否盲断准确"的真实证据，而不是再做一次已知答案的历史回放。

## 背景（已核实，无需重新调查）

1. `AGENTS.md` 第 6 节明确写着：现有生产 pipeline"从未在'不知道答案'的条件下被测试过盲断准确率"。这句话对 `engine/asof/` 同样成立——`reports/as-of-life-state-unit8-real-case-blind-verification-report.md`、Unit9、Unit10、Unit11 的报告都自我声明"不得推导：本轮不证明命理预测准确率"。
2. 这些报告里的"盲断"（`CareerBlindDraft`）都是由已经知道 `feedback.md` 内容的会话手写构造的 fixture——它们证明的是"会话制品化"（session_runner 能不能正确编排冻结→核验→状态构建→投影），不是"盲断准不准"。
3. 已被以下 as-of 单元使用过的案例（**本任务禁止选用，因为它们已经被历史工作的报告叙述"揭示"过结果**）：
   - `C-2026-028-乾-壬戌癸卯壬子乙巳`（G0-G5）
   - `C-2026-024-坤-己巳壬申辛亥壬辰`（G6、Unit8、Unit9）
   - `C-2026-022-坤-癸亥庚申戊寅己未`（G6，跳过）
   - `C-2026-016-坤-甲子丙子丙戌戊子`（G7）
   - `C-2026-026-坤-癸未甲寅壬戌丙午`（G7）
   - `C-2026-027-乾-丁卯壬寅甲午乙丑`（G7）
   - `C-2026-RF000118-乾-己巳癸酉辛丑己丑`（Unit10、Unit11）
   - `C-2026-RF000475-坤-戊辰辛酉己巳乙丑`（Unit9）

## 唯一目标

选一个不在上述排除列表内、此前从未被任何 as-of 工作触碰过的真实案例，在**同一个受控会话内**严格分两个不可逆转的阶段执行，并如实记录每一步的真实工具调用顺序：

- **阶段一（冻结盲断）**：只读该案例的 `input.md`（排盘事实），绝对不打开 `feedback.md` 或该案例目录下任何反馈类文件。基于命盘事实（四柱、藏干、十神、大运）用既有 `engine.asof.natal_capacity.build_natal_capacity_graph()`、`engine.asof.daiyun_context` 构造函数和 `engine.asof.event_candidate.evaluate_event_candidate()`，独立判断该命主截至某个 `as_of_date` 之前最可能发生的事业事件候选（根源性 × 完成方式，只能使用设计文档 §6.6 白名单内组合），构造 `CareerBlindDraft`，调用既有 `engine.asof.consultation_freeze.freeze_career_draft()` 生成 `CareerFreezePackage` 并计算冻结哈希。把该冻结包连同一份显式声明"截至此刻本会话尚未打开 feedback.md"的时间戳记录写入磁盘（新建文件，不修改任何既有文件）。
- **阶段二（揭示核验）**：只有阶段一冻结包已经落盘之后，才允许打开该案例的 `feedback.md`，读取真实反馈事实，构造 `VerificationInput`，调用既有 `session_runner.run_career_session()` 完成完整核验→状态构建流程，得到 `SessionRunResult`。

阶段二完成后，对阶段一冻结的每一个候选事件，逐条判定：命中（预测方向/领域/大致时间窗与真实反馈一致）、部分命中、失验、或证据不足无法判定——分类标准和措辞参照仓库既有 `feedback.md` 里常见的 ✅/🟡/❌ 惯例，但必须给出你自己的判定理由，不得照抄任何案例已有的判定文字。

## 案例选择协议（必须严格遵守顺序）

1. 用 `list_files` 或等价方式列出 `cases/` 目录，排除上述已用案例，筛出同时具备 `input.md`、`feedback.md` 两个文件的候选。
2. 对候选案例，**只读取 `input.md`**（排盘信息），确认四柱、藏干、十神、起运信息完整，足以构造原局承载图和大运阶段（判据与 G0 冻结规格一致）。**此步骤严禁打开该案例的 `feedback.md` 或任何其他包含反馈内容的文件**。
3. 基于 `input.md` 信息选定唯一候选案例和唯一 `as_of_date`（建议选择大运中段某个流年末，确保该命主此刻大概率已经历过至少一次成年后的事业级事件，但你在阶段一无法验证这一点，只能基于命盘结构合理猜测）。
4. 若阶段二揭示后发现该案例反馈里没有任何可评分的事业事件（证据不足），如实记录该案例为"无效样本"，**最多再尝试一次**新的、同样未被触碰过的案例，重复阶段一→阶段二；仍不足则停止并如实报告，不得尝试第三个案例。

## 硬边界（不可协商）

- 只允许新增文件：
  1. `plans/as-of-life-state-blind-judgment-first-proof-point-contract.md`
  2. `tools/as_of_blind_judgment_probe.py`（历史/手动 side path，仅供本任务使用，不注册为默认工具、不切换任何生产入口）
  3. 每次尝试写一个冻结产物文件：`cases/<case_id>/asof-blind-judgment-first-proof-point-frozen-draft.json`
  4. 每次尝试写一个揭示后核验产物文件：`cases/<case_id>/asof-blind-judgment-first-proof-point-verified-result.json`
  5. `reports/as-of-life-state-blind-judgment-first-proof-point-report.md`
- 禁止修改 `engine/asof/` 下任何文件、任何既有测试、任何案例已有的 `input.md`/`feedback.md`/`statement_index.json`、任何既有 as-of 报告或合同。
- 禁止任何 Git 或 GitHub 操作（本地与远端均不可）。
- 禁止在阶段一完成冻结落盘之前，以任何方式打开、grep、搜索或读取候选案例的 `feedback.md`、`analysis.md`、`lessons.md`、`statement_records.json`，或任何可能泄露该案例已知结果的文件。
- 若在阶段一执行过程中发现自己已经（哪怕不小心）看到了候选案例的反馈内容，必须立即停止该案例，如实记录"污染事件"，换一个新案例重新开始阶段一，不得假装没看到继续往下走。
- 本任务不得声称已证明 as-of 推理系统整体的盲断准确率、命理学有效性或任何统计显著性——单案例结果只是一个数据点，仅用于证明"两阶段协议在本地可执行、可留痕、可产出可比较的盲断/事实对照"。

## 已知的方法论局限（必须在最终报告中原样声明，不得省略或弱化）

单会话自我执行的"先冻结后揭示"协议，**无法被加密学证明**该会话在阶段一真的没有获得任何案例结果信息——唯一的证据是文件写入时间戳和你对自己工具调用顺序的如实记录。如果未来有独立审查者怀疑纪律是否被遵守，本次结果不能自证清白；更严格的证明需要引入项目里已有的、面向多方隔离的 `tools/school_capability_prospective.py` blind-bundle 协议（本任务不做这件事，只做最小可行的单会话验证）。

## Gate 执行顺序

### Gate A · CONTRACT
1. 只读 `AGENTS.md`、`plans/as-of-life-state-reasoning-design-2026-07-18.md` §6（事件影响模型，尤其 §6.6 白名单）、`engine/asof/consultation_freeze.py`、`engine/asof/event_candidate.py`、`engine/asof/natal_capacity.py`、`engine/asof/daiyun_context.py`、`engine/asof/session_runner.py`、`reports/as-of-life-state-unit8-real-case-blind-verification-report.md`（理解既有编排模式，但注意它的"盲断"不是真盲断）。
2. 把上述"案例选择协议"和"硬边界"原样冻结进 `plans/as-of-life-state-blind-judgment-first-proof-point-contract.md`，并明确写出你计划选用的候选案例池（此刻只列案例 ID，不读取其反馈内容）。
3. 对该合同做一次逻辑新鲜的独立自审，只有 `PASS` 才能进入 Gate B。

### Gate B · 阶段一：冻结盲断（对选定案例执行）
1. 严格按案例选择协议第 1-3 步选定案例和 `as_of_date`。
2. 在 `tools/as_of_blind_judgment_probe.py` 中实现一个纯粹委托既有 `engine.asof` 公共 API 的最小编排函数：读取命盘 JSON 输入 → 构造 `NatalCapacityGraph`/`DaiyunStage` → 生成候选事件候选并做根源×完成方式判定 → 构造 `CareerBlindDraft` → 调用 `freeze_career_draft()` → 把冻结包和一个显式 `"feedback_opened": false` 字段、当前 UTC 时间戳一起写入 `cases/<case_id>/asof-blind-judgment-first-proof-point-frozen-draft.json`。
3. 运行该脚本，确认产物落盘、哈希可重复读回。记录真实命令输出。
4. 在报告草稿里写下你此刻对每个候选事件的**预测**（领域、方向、大致时间窗、置信程度），这是后续评分的基准，必须在打开 feedback.md 之前写死，不得事后补写或润色。

### Gate C · 阶段二：揭示核验
1. 只有 Gate B 的冻结产物已经落盘之后，才打开该案例的 `feedback.md`。
2. 构造 `VerificationInput`，调用 `session_runner.run_career_session()` 完成完整核验流程，产物写入 `cases/<case_id>/asof-blind-judgment-first-proof-point-verified-result.json`。
3. 逐条对照 Gate B 写死的预测与真实反馈，给出命中/部分命中/失验/证据不足四选一判定和理由。

### Gate D · REPORT + FREEZE
1. 创建 `reports/as-of-life-state-blind-judgment-first-proof-point-report.md`：选用案例与理由、Gate B 冻结时刻的原始预测全文（逐字保留，不事后修饰）、Gate C 真实反馈摘录与逐条判定、命中率汇总、"已知的方法论局限"章节原样保留、`LOCAL ONLY / NOT PUSHED` 声明。
2. 报告创建后重新运行一次 Gate B/C 涉及的脚本命令，确认幂等（同输入产生同哈希），把新鲜结果回填报告。
3. 最终裁决只能是以下之一：
   - `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`（协议可执行、产出可比较结果，不论命中率高低）；
   - `BLOCKED — 案例池耗尽或污染事件导致无法产出有效样本`（附具体原因）。

## STOP 条件（命中任一立即停止并汇报）

- 阶段一执行中发现自己已经看到候选案例反馈内容（污染事件）且已用完第二次案例尝试机会；
- 需要修改 `engine/asof/` 任何文件才能完成编排；
- 需要执行任何 Git/GitHub 操作；
- 案例池中排除已用案例后找不到任何同时具备完整命盘信息的候选。

## 完成后的汇报格式

最终回复必须包含：选用案例 ID 与排除已用案例的核对清单、Gate B 冻结时刻写死的原始预测全文、Gate C 真实反馈对照与逐条判定、命中率汇总表、方法论局限声明、最终裁决（PASS/BLOCKED 及原因）。不得省略任何一项，也不得用推测替代真实文件内容。
```

---

## 交付边界

本文件本身不实施上述长任务，只交付这份提示词与使用说明。是否要在完成本次单案例验证后，进一步投入"把 as-of 接入既有 `school_capability_prospective` blind-bundle 隔离协议"这个更高工程量的干净目标，需要用户在看到本次单案例结果后另行明确授权，不属于本提示词范围。
