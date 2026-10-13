# as-of 真实盲断闭环 First Proof Point 冻结合同

> **修订记录（Amendment R1）**：本合同 R0 版本第一次执行因把"整份 `input.md`
> 含命主已知信息小节"误判为"污染"而过早 STOP，产出 `BLOCKED` 结论。geju 格局
> 审计发现该小节是仓库 `templates/input-from-wenzhen.md` 第57行起定义的
> input.md 标准第三/四节，是模板结构，不是异常污染。审计结论：应把阶段一
> 盲态输入粒度从"整份文件"降级为"排盘小节截断"。本次修订（R1）新增 §2.1
> 截断规则与 §3.3 R1 执行记录，其余章节原样保留作为历史留痕；R0 的执行叙述
> 见 §3.3。

## 1. 合同状态与目标

- Gate：`Gate A · CONTRACT`。
- 工作性质：探索性验证，不是新功能开发。
- 唯一目标：产出项目历史上第一份“as-of 推理在不知道答案的情况下能否盲断准确”的真实单案例证据；证明两阶段协议在本地可执行、可留痕、可产出可比较的盲断/事实对照。
- 禁止推断：本任务不得声称已证明 as-of 推理系统整体的盲断准确率、命理学有效性或任何统计显著性。单案例结果只是一个数据点。
- 既有编排对照：`reports/as-of-life-state-unit8-real-case-blind-verification-report.md` 只证明 session runner 编排，不证明预测准确率；不得继承其中已知答案 fixture 作为本任务预测。

## 2. 权威输入与只读依赖

1. `AGENTS.md`。
2. `plans/as-of-life-state-reasoning-design-2026-07-18.md` §6，尤其 §6.6。
3. `engine/asof/consultation_freeze.py`。
4. `engine/asof/event_candidate.py`。
5. `engine/asof/natal_capacity.py`。
6. `engine/asof/daiyun_context.py`。
7. `engine/asof/session_runner.py`。
8. `reports/as-of-life-state-unit8-real-case-blind-verification-report.md`。
9. 候选案例在阶段一只允许读取 `input.md`（经 §2.1 截断规则处理后的视图）；选定案例冻结落盘后，阶段二才允许读取该案 `feedback.md`。

### 2.1 阶段一盲态输入截断规则（R1 新增）

`input.md` 不是原子的盲态单位。仓库两种模板变体均把命主已知信息/反馈内容作为
`input.md` 自身的标准小节，而不是独立文件：

- Markdown 表格模板固定用二级标题 `## 三/四、命主已知信息` 引入该小节（见
  `templates/input-from-wenzhen.md` 第57行起）；
- 结构化 YAML 模板用顶层键 `known_facts:` 引入同一类信息（无 Markdown 标题）。

阶段一必须使用 [`tools/as_of_blind_judgment_probe.py`](../tools/as_of_blind_judgment_probe.py) 的
`truncate_blind_section()` 函数，把 `input.md` 截断到第一个匹配上述两种边界标记
之前，只读取截断后的纯排盘视图（四柱、藏干、十神、大运、神煞等）。若截断函数
返回 `boundary_type is None`（未匹配到任何边界标记），必须视为"无法确认该文件
是否纯排盘"，不得默认当作安全,该案例不得选用。

即使检索/grep 操作本身也可能因为返回结果的上下文片段而泄露反馈内容（R1 执行
中实测发生：对候选 015 的 grep 搜索直接在结果中显示了具体职业年表内容）。因此
阶段一严禁对候选案例目录使用会在结果里展示正文片段的搜索；如需批量筛选候选，
只能使用只输出布尔值/行号/边界类型的内容盲扫描脚本。

## 3. 候选案例池与排除清单

### 3.1 当前候选 inventory 与计划尝试池（R1 修订）

只读路径存在性机械枚举得到：`cases/` 下同时具备 `input.md` 与 `feedback.md` 的目录共 133 个；排除 `_TEMPLATE` 与下列 8 个已用案例后，合格目录 inventory 共 124 个。该计数只证明文件存在，不证明命盘字段完整，也未读取任何反馈正文。

R0 执行把两个连续编号案例（013、014）作为计划尝试池，但阶段一实测发现两案的
`input.md` 全文均在标准"命主已知信息"小节前有完整排盘信息，只是 R0 把整份文件
（含该小节）判定为污染，未按 §2.1 截断规则处理。R1 不复用 013/014（已被 R0 会话
完整读取全文，对本会话已知情污染，不可能再恢复盲态），改为从 124 个目录中按
§2.1 截断规则重新筛选：

1. 排除 R0 已知情污染的 `C-2026-013-坤-壬申甲辰丙辰己丑`、`C-2026-014-乾-丙戌庚子乙亥辛巳`；
2. 排除本轮内容盲扫描发现的合成测试数据 `C-2026-029-坤-乙亥戊寅辛酉癸巳`（其 `input.md` 头部 `case_meta.来源` 字段明确写有"随机生成（用于系统报告流程 smoke）"，该字段属于排盘头部信息而非反馈内容，判定过程未读取任何反馈）；
3. 排除本轮 grep 搜索意外显示职业年表内容的 `C-2026-015-乾-甲寅乙亥丙辰辛卯`（真实污染事件，见 §3.3）；
4. 剩余目录用只输出布尔值/行号/边界类型的内容盲扫描脚本核对 §2.1 截断可行性，选定第一个可用真实案例。

实际选定：`C-2026-002-坤-壬戌庚戌戊辰丙辰`（截断行号第60行，边界类型 `heading`，
`case_meta`/来源头部信息未显示合成标记）。选定过程只依据截断行号、边界类型和
排盘完整性这三个内容盲指标，未读取任何反馈正文。

### 3.2 已用案例排除清单

以下案例不得选用：

- `C-2026-028-乾-壬戌癸卯壬子乙巳`（G0-G5）
- `C-2026-024-坤-己巳壬申辛亥壬辰`（G6、Unit8、Unit9）
- `C-2026-022-坤-癸亥庚申戊寅己未`（G6，跳过）
- `C-2026-016-坤-甲子丙子丙戌戊子`（G7）
- `C-2026-026-坤-癸未甲寅壬戌丙午`（G7）
- `C-2026-027-乾-丁卯壬寅甲午乙丑`（G7）
- `C-2026-RF000118-乾-己巳癸酉辛丑己丑`（Unit10、Unit11）
- `C-2026-RF000475-坤-戊辰辛酉己巳乙丑`（Unit9）

### 3.3 R0/R1 执行记录

**R0（BLOCKED，历史留痕）**：只读 013、014 的 `input.md` 全文后发现"命主已知
信息"小节，误判为污染，STOP。未构造任何候选、未冻结、未打开任何 `feedback.md`。

**R1（本次修订执行）**：
- 013、014 因 R0 已读全文，标记为"本会话已知情污染"，不再使用。
- 015（`C-2026-015-乾-甲寅乙亥丙辰辛卯`）：R1 初次用截断函数处理时，因该案例
  用 YAML `known_facts:` 键而非 Markdown 标题引入已知信息，第一版截断函数只
  检测标题格式，未命中该边界，原样返回全文（含反馈内容）。随后为确认"截断为
  何失败"，对该案例目录执行了 grep 搜索，搜索结果的上下文片段直接显示了具体
  职业年表内容（1996-2025 共 11 条职业事件）。**这是真实污染事件**：不是靠读
  取 `feedback.md` 造成，而是靠读取 `input.md` 全文 + grep 结果上下文共同造成。
  立即停止使用该案例，并将截断函数升级为同时检测 `heading` 与 `yaml_key` 两种
  边界（见 §2.1）。
- 029（`C-2026-029-坤-乙亥戊寅辛酉癸巳`）：升级后的截断函数在该案例上正确截断
  （第93行，`yaml_key` 边界）。读取截断后视图时发现头部 `case_meta.来源` 字段
  写明"随机生成（用于系统报告流程 smoke）"——该字段属于排盘头部信息而非反馈，
  读取过程未看到任何反馈内容。据此排除该案例（合成测试数据，不是真实案主）。
- 002（`C-2026-002-坤-壬戌庚戌戊辰丙辰`）：批量内容盲扫描（只输出布尔值/行号/
  边界类型，不展示正文片段）确认排除已用与已污染案例后的候选目录里，该案例
  截断在第60行（`heading` 边界），排盘信息完整（四柱/藏干/十神/大运/关键结构）。
  选定为本次 First Proof Point 唯一使用案例。

## 4. 案例选择协议（原样冻结）

1. 用 `list_files` 或等价方式列出 `cases/` 目录，排除上述已用案例，筛出同时具备 `input.md`、`feedback.md` 两个文件的候选。
2. 对候选案例，**只读取 `input.md`**（排盘信息），确认四柱、藏干、十神、起运信息完整，足以构造原局承载图和大运阶段（判据与 G0 冻结规格一致）。**此步骤严禁打开该案例的 `feedback.md` 或任何其他包含反馈内容的文件**。
3. 基于 `input.md` 信息选定唯一候选案例和唯一 `as_of_date`（建议选择大运中段某个流年末，确保该命主此刻大概率已经历过至少一次成年后的事业级事件，但你在阶段一无法验证这一点，只能基于命盘结构合理猜测）。
4. 若阶段二揭示后发现该案例反馈里没有任何可评分的事业事件（证据不足），如实记录该案例为“无效样本”，**最多再尝试一次**新的、同样未被触碰过的案例，重复阶段一→阶段二；仍不足则停止并如实报告，不得尝试第三个案例。

## 5. 两个不可逆阶段

### 5.1 阶段一（冻结盲断）

只读该案例的 `input.md`（排盘事实），绝对不打开 `feedback.md` 或该案例目录下任何反馈类文件。基于命盘事实（四柱、藏干、十神、大运）用既有 `engine.asof.natal_capacity.build_natal_capacity_graph()`、`engine.asof.daiyun_context` 构造函数和 `engine.asof.event_candidate.evaluate_event_candidate()`，独立判断该命主截至某个 `as_of_date` 之前最可能发生的事业事件候选（根源性 × 完成方式，只能使用设计文档 §6.6 白名单内组合），构造 `CareerBlindDraft`，调用既有 `engine.asof.consultation_freeze.freeze_career_draft()` 生成 `CareerFreezePackage` 并计算冻结哈希。把该冻结包连同一份显式声明“截至此刻本会话尚未打开 feedback.md”的时间戳记录写入磁盘（新建文件，不修改任何既有文件）。

阶段一报告草稿必须在打开反馈前写死每个候选事件的领域、方向、大致时间窗、置信程度；阶段二不得润色、替换或重写该原始预测。

### 5.2 阶段二（揭示核验）

只有阶段一冻结包已经落盘之后，才允许打开该案例的 `feedback.md`，读取真实反馈事实，构造 `VerificationInput`，调用既有 `session_runner.run_career_session()` 完成完整核验→状态构建流程，得到 `SessionRunResult`。

阶段二完成后，对阶段一冻结的每一个候选事件，逐条判定：命中（预测方向/领域/大致时间窗与真实反馈一致）、部分命中、失验、或证据不足无法判定。分类措辞参照仓库常见 ✅/🟡/❌ 惯例，但判定理由必须根据冻结预测与新揭示事实独立写作，不得照抄任何案例已有判定文字。

## 6. §6.6 根源性 × 完成方式白名单

阶段一主事件只允许以下组合：

- `STRONG_ROOT + ACTIVATE_EXISTING`
- `STRONG_ROOT + REPAIR_DEFECT`
- `WEAK_ROOT + COMPLETE_LATENT`
- `WEAK_ROOT + TEMPORARY_SUBSTITUTE`
- `NO_ROOT + TEMPORARY_SUBSTITUTE`
- 任意根源 + `INVALID_COMPLETION` 仅进入反证审计，不得生成目标主事件或进入冻结包。

以下逻辑约束必须保持：

- `NO_ROOT + ACTIVATE_EXISTING` 必须拒绝。
- `NO_ROOT + COMPLETE_LATENT` 不得宣称完成潜在结构。
- 任意根源与 `INVALID_COMPLETION` 配对时不得生成目标主事件。
- `WEAK_ROOT + TEMPORARY_SUBSTITUTE` 只支持阶段性候选。
- `STRONG_ROOT + REPAIR_DEFECT` 的跨运延续必须由现实成果固化核验。
- 不得仅因岁运凑齐表面字形升级根源等级。

## 7. 硬边界（原样冻结）

- 只允许新增文件：
  1. `plans/as-of-life-state-blind-judgment-first-proof-point-contract.md`
  2. `tools/as_of_blind_judgment_probe.py`（历史/手动 side path，仅供本任务使用，不注册为默认工具、不切换任何生产入口）
  3. 每次尝试写一个冻结产物文件：`cases/<case_id>/asof-blind-judgment-first-proof-point-frozen-draft.json`
  4. 每次尝试写一个揭示后核验产物文件：`cases/<case_id>/asof-blind-judgment-first-proof-point-verified-result.json`
  5. `reports/as-of-life-state-blind-judgment-first-proof-point-report.md`
- 禁止修改 `engine/asof/` 下任何文件、任何既有测试、任何案例已有的 `input.md`/`feedback.md`/`statement_index.json`、任何既有 as-of 报告或合同。
- 禁止任何 Git 或 GitHub 操作（本地与远端均不可）。
- 禁止在阶段一完成冻结落盘之前，以任何方式打开、grep、搜索或读取候选案例的 `feedback.md`、`analysis.md`、`lessons.md`、`statement_records.json`，或任何可能泄露该案例已知结果的文件。
- 若在阶段一执行过程中发现自己已经（哪怕不小心）看到了候选案例的反馈内容，必须立即停止该案例，如实记录“污染事件”，换一个新案例重新开始阶段一，不得假装没看到继续往下走。
- 本任务不得声称已证明 as-of 推理系统整体的盲断准确率、命理学有效性或任何统计显著性——单案例结果只是一个数据点，仅用于证明“两阶段协议在本地可执行、可留痕、可产出可比较的盲断/事实对照”。

## 8. Gate 执行顺序

### Gate A · CONTRACT

1. 只读 `AGENTS.md`、`plans/as-of-life-state-reasoning-design-2026-07-18.md` §6（事件影响模型，尤其 §6.6 白名单）、`engine/asof/consultation_freeze.py`、`engine/asof/event_candidate.py`、`engine/asof/natal_capacity.py`、`engine/asof/daiyun_context.py`、`engine/asof/session_runner.py`、`reports/as-of-life-state-unit8-real-case-blind-verification-report.md`（理解既有编排模式，但注意它的“盲断”不是真盲断）。
2. 把上述“案例选择协议”和“硬边界”原样冻结进本合同，并明确写出计划选用的候选案例池（此刻只列案例 ID，不读取其反馈内容）。
3. 对本合同做一次逻辑新鲜的独立自审，只有 `PASS` 才能进入 Gate B。

### Gate B · 阶段一：冻结盲断

1. 严格按案例选择协议第 1-3 步选定案例和 `as_of_date`。
2. 在 `tools/as_of_blind_judgment_probe.py` 中实现一个纯粹委托既有 `engine.asof` 公共 API 的最小编排函数：读取命盘 JSON 输入 → 构造 `NatalCapacityGraph`/`DaiyunStage` → 生成候选事件候选并做根源×完成方式判定 → 构造 `CareerBlindDraft` → 调用 `freeze_career_draft()` → 把冻结包和一个显式 `"feedback_opened": false` 字段、当前 UTC 时间戳一起写入 `cases/<case_id>/asof-blind-judgment-first-proof-point-frozen-draft.json`。
3. 运行该脚本，确认产物落盘、哈希可重复读回。记录真实命令输出。
4. 在报告草稿里写下此刻对每个候选事件的**预测**（领域、方向、大致时间窗、置信程度），这是后续评分的基准，必须在打开 `feedback.md` 之前写死，不得事后补写或润色。

### Gate C · 阶段二：揭示核验

1. 只有 Gate B 的冻结产物已经落盘之后，才打开该案例的 `feedback.md`。
2. 构造 `VerificationInput`，调用 `session_runner.run_career_session()` 完成完整核验流程，产物写入 `cases/<case_id>/asof-blind-judgment-first-proof-point-verified-result.json`。
3. 逐条对照 Gate B 写死的预测与真实反馈，给出命中/部分命中/失验/证据不足四选一判定和理由。

### Gate D · REPORT + FREEZE

1. 创建 `reports/as-of-life-state-blind-judgment-first-proof-point-report.md`：选用案例与理由、Gate B 冻结时刻的原始预测全文（逐字保留，不事后修饰）、Gate C 真实反馈摘录与逐条判定、命中率汇总、“已知的方法论局限”章节原样保留、`LOCAL ONLY / NOT PUSHED` 声明。
2. 报告创建后重新运行一次 Gate B/C 涉及的脚本命令，确认幂等（同输入产生同哈希），把新鲜结果回填报告。
3. 最终裁决只能是以下之一：
   - `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`（协议可执行、产出可比较结果，不论命中率高低）；
   - `BLOCKED — 案例池耗尽或污染事件导致无法产出有效样本`（附具体原因）。

## 9. STOP 条件

命中任一条件立即停止并汇报：

- 阶段一执行中发现自己已经看到候选案例反馈内容（污染事件）且已用完第二次案例尝试机会；
- 需要修改 `engine/asof/` 任何文件才能完成编排；
- 需要执行任何 Git/GitHub 操作；
- 案例池中排除已用案例后找不到任何同时具备完整命盘信息的候选。

## 10. 已知的方法论局限（最终报告必须原样声明）

单会话自我执行的“先冻结后揭示”协议，**无法被加密学证明**该会话在阶段一真的没有获得任何案例结果信息——唯一的证据是文件写入时间戳和你对自己工具调用顺序的如实记录。如果未来有独立审查者怀疑纪律是否被遵守，本次结果不能自证清白；更严格的证明需要引入项目里已有的、面向多方隔离的 `tools/school_capability_prospective.py` blind-bundle 协议（本任务不做这件事，只做最小可行的单会话验证）。

## 11. 验收与非推断边界

合同 PASS 只表示协议边界闭合、可进入阶段一，不证明实现正确、冻结真实、核验命中或系统有效。最终只有在新增文件写集合规、阶段顺序有时间戳与命令记录、冻结哈希可复验、完整 runner 产出存在、报告后新鲜幂等验证和证据审查均通过时，才能裁决 `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`。

本任务全部成果保持 `LOCAL ONLY / NOT PUSHED`；受控会话不得执行 Git 命令或 GitHub-mutating operation。
