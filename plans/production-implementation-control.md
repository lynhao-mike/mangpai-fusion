# 事业功能证据卡生产实现设计 · 总控状态表

> 建立日期：2026-07-19（Asia/Shanghai）
>
> 当前阶段：生产实现设计
>
> 本文件是 F01–F12 生产实现设计阶段的唯一总控状态表。它记录任务拆分、依赖、产物、验收证据与下一动作，但不是冻结业务语义的事实源。

## 1. 事实源与职责边界

| 信息类型 | 事实源 | 职责 |
|---|---|---|
| F01–F12 正式业务语义 | [`engine/contracts/12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md) | 冻结定义、证据门、竞争边界、根源、时序、现实落点及变更纪律 |
| F01–F12 机器可读数据 | [`mapping/real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml) | 声明性枚举、字段、来源与竞争关系；禁止可执行逻辑 |
| 契约体系总览 | [`engine/contracts/00-OVERVIEW.md`](../engine/contracts/00-OVERVIEW.md) | 契约分层、变更和评审入口 |
| 当前项目状态 | [`META/project-state.json`](../META/project-state.json) | 项目阶段与稳定入口 |
| 当前会话交接 | [`handoff.md`](../handoff.md) | 当前阶段、硬边界、总控入口与新会话提示词 |
| 本阶段任务状态 | 本文件 | 生产实现设计的任务、依赖、验收与阻断状态 |

优先级规则：正式业务语义冲突时，以正式契约正文为准；机器结构冲突时，以机器附录及其 schema 为准；本文件不得重定义或改写冻结裁决。

## 2. 阶段目标与非目标

### 2.1 目标

设计一套可审计、可测试、可弃权的生产实现方案，将冻结证据卡接入现有引擎，同时保持以下边界：

```text
冻结声明性证据卡
→ 运行时输入契约
→ 证据归一化
→ 必要门检查
→ 竞争候选与反证
→ 根源／时序约束
→ OUTPUT / CONDITIONAL / ASK / ABSTAIN / HUMAN_REVIEW
→ 可追溯结果
```

设计必须回答：

1. 运行时读取哪些冻结字段；
2. 哪些字段只用于审计，不能直接执行；
3. 如何表达现实事实、命理结构、时间层与来源；
4. 如何执行必要门而不把声明性 YAML 当脚本；
5. 如何处理竞争功能、冲突、缺证与弃权；
6. 如何与现有 pipeline、findings、报告和反馈链集成；
7. 如何测试不回归既有生产入口。

### 2.2 非目标

本阶段不做：

- 不重开 F01–F12 冻结定义；
- 不把机器附录改造成可执行 if/else；
- 不直接实现十二张卡的全部生产规则；
- 不修改现有生产默认行为；
- 不以职位名、行业名、十神标签或材料命中数替代必要门；
- 不在设计完成和批准前进入编码；
- 不把历史案例命中率冒充统计概率。

## 3. 阶段门

| 阶段 | 目标 | 进入条件 | 完成条件 | 状态 |
|---|---|---|---|---|
| G0 冻结基线 | 确认 F01–F12 正式输入稳定 | 正式契约与机器附录存在 | 最终独立验收 PASS | `COMPLETED` |
| G1 架构盘点 | 找到现有 pipeline、findings、决策状态、报告和反馈接点 | G0 完成 | 形成现状图、可复用组件、缺口和不可触碰边界，且持久化交付物与独立验收证据齐全 | `COMPLETED` |
| G2 运行时契约设计 | 设计输入、输出、证据、门、竞争与弃权接口 | G1 完成 | 契约草案无业务语义扩张，字段可追溯 | `COMPLETED` |
| G3 最小垂直切片设计 | 选择一张代表卡验证端到端架构 | G2 完成 | 切片范围、适配器、测试和回滚边界明确，并通过分离实例独立验收 | `COMPLETED` |
| G4 独立评审 | 审查语义保真、架构适配、失败模式与测试充分性 | G3 完成 | High/Medium 问题清零并获得用户批准 | `COMPLETED` |
| G5 实现计划 | 将批准设计拆成可执行编码步骤 | G4 完成 | 形成逐文件、逐测试、可回滚计划，并通过分离实例独立验收 | `COMPLETED` |
| G6 F09 最小生产切片实现 | 按批准计划逐个实现、静态审查、精确验证并作证据有界冻结 | G5 完成且每个 Task 获得独立非继承授权 | Task 1–Task 10 + P-1/P-2 + feedback 实现与测试落地；Task 10 T01–T104 collect 104、vertical + adapter 136 passed、`tests/f09` 1172 passed，退出码均为 0 | `COMPLETED` |
| G7 F09 集成验证 | 验证批准的 F09 最小切片集成行为 | G6 完成及独立命令授权 | application opt-in 26 passed、vertical matrix 104 passed、current-run authority 16 passed、`tests/f09` 1172 passed，退出码均为 0 | `COMPLETED` |
| G8 F09 回归与隔离验证 | 验证 production-default 不变、F08 不可执行及 staged/preprod 分账 | G7 完成及独立命令授权 | 四组精确回归/隔离命令分别 4／2／11／1 passed，退出码均为 0；仅既有 deprecated adapter warning | `COMPLETED` |
| G9 F09 实现收口 | 汇总 G6–G8 证据并形成有界实现结论 | G6–G8 完成 | 2026-07-26 新鲜 `tests/f09` 复跑 1172 passed、退出码 0，与 G6/G7 计数一致；全仓 sanity 有 2 个非 F09 失败，按计划单独记录，不据此声称全仓绿 | `COMPLETED` |

状态枚举：`BLOCKED`、`READY`、`IN_PROGRESS`、`REVIEW`、`COMPLETED`、`CANCELLED`。

## 4. 总控任务表

| 任务 ID | 父任务 | 任务 | 状态 | 依赖 | 输入事实源 | 产物 | 验收证据 | 阻断项 | 下一动作 |
|---|---|---|---|---|---|---|---|---|---|
| PI-000 | — | 建立生产实现设计治理入口 | `COMPLETED` | G0 | 正式契约、机器附录 | 本总控表、精简 handoff | 链接和边界校验 | 无 | 已收口 |
| PI-100 | — | 现有运行架构盘点 | `COMPLETED` | PI-000 | pipeline、findings 契约、decision/domain、报告与反馈入口 | PI-110／120／130 三份持久化审计 | PI-190-R2 与 PI-195-R2 均为 `PASS` | 无 | 已收口 |
| PI-110 | PI-100 | 盘点输入与 pipeline 接点 | `COMPLETED` | PI-100 启动 | 引擎入口与输入契约 | [`production-implementation-pi-110-input-pipeline-audit.md`](production-implementation-pi-110-input-pipeline-audit.md) | 文件、符号、调用链齐全；PI-190-R2 验收通过 | 无 | 已收口 |
| PI-120 | PI-100 | 盘点 findings、决策状态与冲突机制 | `COMPLETED` | PI-100 启动 | findings、decision、domain 模型 | [`production-implementation-pi-120-findings-decision-conflict-audit.md`](production-implementation-pi-120-findings-decision-conflict-audit.md) | production/staged 分账及可复用/缺口明确；PI-190-R2 验收通过 | 无 | 已收口 |
| PI-130 | PI-100 | 盘点报告、statement index 与反馈回路 | `COMPLETED` | PI-100 启动 | report、linter、feedback 工具 | [`production-implementation-pi-130-report-statement-feedback-audit.md`](production-implementation-pi-130-report-statement-feedback-audit.md) | 追溯链、失败模式和兼容边界明确；PI-190-R2 验收通过 | 无 | 已收口 |
| PI-190 | PI-100 | 汇总架构盘点并通过 G1 | `COMPLETED` | PI-110/120/130 | 三份持久化盘点报告 | [`production-implementation-pi-190-r2-g1-acceptance.md`](production-implementation-pi-190-r2-g1-acceptance.md) | 独立实例 PI-190-R2 裁决 `PASS` | 无 | 已收口 |
| PI-195 | PI-100 | 独立校准 handoff 所载 G1 PASS | `COMPLETED` | handoff 历史声明、三份审计、PI-190-R2 与总控治理规则 | 当前事实源与调用链 | 原 [`production-implementation-g1-calibration-blocker.md`](production-implementation-g1-calibration-blocker.md) 与新 [`production-implementation-pi-195-r2-g1-calibration.md`](production-implementation-pi-195-r2-g1-calibration.md) | PI-195-R2 独立校准 `PASS` | 原 Option A 阻断已解除；F01–F12 implementation 仍为 `false` | 已收口 |
| PI-200 | — | 运行时契约设计 | `COMPLETED` | PI-190、PI-195 PASS | G1 三份审计、PI-190-R2、PI-195-R2、正式契约 | PI-210／220／230 设计稿及 PI-290-R1／R2／R3 独立验收记录 | 输入输出、错误和追溯闭合 | PI-290-R3 十二项矩阵 `12 PASS / 0 BLOCKED`，独立裁决 G2 `PASS` | 已收口；进入 G3 |
| PI-210 | PI-200 | 设计规范化证据模型 | `COMPLETED` | PI-200 启动 | 卡字段、现有模型 | [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md) | 三轨、来源、时间、空值、不变量与适配边界齐全 | 无 | 已收口，交由 PI-290 独立验收 |
| PI-220 | PI-200 | 设计门、竞争、反证与弃权接口 | `COMPLETED` | PI-210 | 冻结门与决策状态、PI-210 规范化模型 | [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md) | 五动作、缺证/冲突/未知与失败安全接口齐全；不含新增业务规则 | 无 | 已收口，交由 PI-290 独立验收 |
| PI-230 | PI-200 | 设计审计轨迹和来源绑定 | `COMPLETED` | PI-210 | source refs、findings、PI-210 规范化模型 | [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md) | 端到端身份、版本、artifact 失败与反馈安全绑定齐全 | 无 | 已收口，交由 PI-290 独立验收 |
| PI-290 | PI-200 | 汇总运行时契约并通过 G2 | `COMPLETED` | PI-210/220/230 | 三份 G2 设计文档与冻结契约 | [`production-implementation-pi-290-r1-g2-acceptance.md`](production-implementation-pi-290-r1-g2-acceptance.md)、[`production-implementation-pi-290-r2-g2-reacceptance.md`](production-implementation-pi-290-r2-g2-reacceptance.md)、[`production-implementation-pi-290-r3-g2-reacceptance.md`](production-implementation-pi-290-r3-g2-reacceptance.md) | PI-290-R3 独立裁决 `PASS`：H-03-R 已解除，七项无回归，十二项矩阵全通过 | 无 | 已收口；该 PASS 仅证明 G2 设计，不证明实现 |
| PI-300 | — | 最小垂直切片设计 | `COMPLETED` | PI-290-R3 PASS | 批准的运行时契约 | [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md)；独立验收 [`production-implementation-pi-390-r1-g3-acceptance.md`](production-implementation-pi-390-r1-g3-acceptance.md)；PI-360-R1／R2／R3 有界整改；独立复验 [`production-implementation-pi-390-r2-g3-reacceptance.md`](production-implementation-pi-390-r2-g3-reacceptance.md)、[`production-implementation-pi-390-r3-g3-reacceptance.md`](production-implementation-pi-390-r3-g3-reacceptance.md)、[`production-implementation-pi-390-r4-g3-reacceptance.md`](production-implementation-pi-390-r4-g3-reacceptance.md) | PI-390-R4 独立裁决 `PASS`：0 High、0 Medium、0 critical ambiguity、0 类关键证据缺失、0 新回归；五个互斥 gate 场景 5 PASS／0 BLOCKED；G3 回归域 18 PASS／0 BLOCKED | 无；该 PASS 仅证明 F09 单卡设计可进入 G4，不证明实现、测试执行、runtime 接线或投产 | 已收口；进入 PI-400 独立技术评审 |
| PI-400 | — | 独立设计评审 | `COMPLETED` | PI-390-R4 PASS | 完整 G2 契约、PI-300 设计、两次用户 Option A 授权、PI-210/PI-220 amendments 及独立验收 | [`production-implementation-pi-400-r3-g4-technical-rereview.md`](production-implementation-pi-400-r3-g4-technical-rereview.md)、[`production-implementation-pi-285-r3-pi210-locator-amendment-reacceptance.md`](production-implementation-pi-285-r3-pi210-locator-amendment-reacceptance.md)、PI-470-R3 有界整改、实际 fixture [`production-implementation-pi-300-f09-source-snapshots-v1.json`](production-implementation-pi-300-f09-source-snapshots-v1.json)、[`production-implementation-pi-400-r4-g4-technical-rereview.md`](production-implementation-pi-400-r4-g4-technical-rereview.md) | PI-400-R4 分离实例独立裁决 `PASS`；父实例重算 Markdown/JSON 摘要并核验测试编号、legacy path 与 reason-code；用户于 2026-07-20 明确指令“以子任务完成G5”，解除用户批准硬门 | 无；该完成只批准进入 G5 编写并验收计划，不授权生产实现、测试执行、mapping/YAML 执行或 production-default 变更 | 已收口；G5 按独立计划验收循环推进 |
| PI-500 | — | 编写实现计划 | `COMPLETED` | PI-400-R4 PASS、用户于 2026-07-20 明确指令“以子任务完成G5” | 批准的 F09 单卡设计与 PI-210/220/230 canonical 契约 | [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) 及 PI-570/PI-590 历次整改复验记录 | PI-590-R25 独立静态裁决 `PASS`，父实例直接重读并接受：High=0、Medium=0、critical ambiguity=0、material evidence gap=0、mechanical-copyability gap=0、authority conflict=0、regression=0 | 无 G5 plan-text 阻断；parseability、typing、collection、runtime、implementation conformance、生产就绪与 GitHub 同步均未证明 | 已收口；不得推断生产实现、测试执行或 production-default 变更授权 |
| PI-600-T1 | PI-500 | F09 Task 1 基础契约与错误类型实现 | `COMPLETED` | G5 完成；Task 1 修改、命令与状态写入均获逐次独立授权 | 修复后的 Task 1 literal-copy 与 Step 1；精确五路径 | [`../engine/f09/errors.py`](../engine/f09/errors.py)、[`../engine/f09/contracts.py`](../engine/f09/contracts.py)、[`../tests/f09/__init__.py`](../tests/f09/__init__.py)、[`../tests/f09/conftest.py`](../tests/f09/conftest.py)、[`../tests/f09/test_evidence_contract.py`](../tests/f09/test_evidence_contract.py) | 父实例直接检查；新鲜独立静态实现审查 `PASS`（High=0、Medium=0）；focused `47 passed in 0.13s`；两个指定 production-default 回归 selector `2 passed, 1 warning in 1.04s`；两次 exit 0；新鲜独立证据审查 `PASS`（High=0、Medium=0）；父实例接受 Task 1 evidence-bounded freeze | 全套测试、全仓正确性、Git provenance、YAML/mapping、F08 runtime、完整 production-default 动态不变性、G6 完成、G7–G9、部署、GitHub 同步与生产就绪均未证明 | Task 1 已有界收口 |
| PI-600-T2 | PI-500 | F09 Task 2 受限 RFC 8785 canonical JSON 实现 | `COMPLETED` | PI-600-T1 evidence-bounded freeze；Task 2 合同范围内的实现、独立静态审查与两条精确验证命令 | [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) Task 2；[`../engine/f09/canonical_json.py`](../engine/f09/canonical_json.py)；[`../tests/f09/test_canonical_json.py`](../tests/f09/test_canonical_json.py) | 有界 number-free RFC 8785/JCS parser、canonicalizer 与 SHA-256 digest；46-instance focused ledger | 新鲜独立静态审查 `PASS`（High=0、Medium=0、Low=0）；独立 VERIFY：focused `46 passed in 0.37s`、exit 0；指定回归 `6 passed, 1 warning in 2.18s`、exit 0；无 failed/errors/skipped/xfail/xpass；新鲜独立 EVIDENCE_REVIEW `PASS`，父实例复核后接受 Task 2 evidence-bounded freeze | 全套测试、全仓正确性、完整 RFC 8785 数字支持、Git provenance、YAML/mapping、F08 runtime、完整 production-default 动态不变性、G6 完成、G7–G9、部署、GitHub 同步与生产就绪均未证明 | Task 2 已有界收口；Task 3 必须按冻结合同重新准入，权限不可继承 |

| PI-570-R12 | PI-500 | 有界 plan-only typed-output oracle 整改 | `BLOCKED` | 父实例以一个 High 拒绝 PI-570-R11 | R11 实际计划文本、Task 10 phase observations 与 matrix oracle | [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) R12 remediation record | 删除 matrix-side fixture/baseline issue reconstruction；三个 adapter 从实际 typed validator/coordinator rejection 产出同-surface code/path；T102 与 no-issue closure 保持 | 父实例后续发现 returned-output issue transport 与 `errors.py` literal scaffold 两个 High；R12 未获接受 | 已由 PI-570-R13 有界整改接续 |
| PI-570-R13 | PI-500 | 有界 plan-only returned-output transport 与 errors scaffold 整改 | `BLOCKED` | 父实例以两个 High 拒绝 PI-570-R12 | R12 实际计划文本、Task 1、Tasks 6–8 canonical returns、Task 10 adapters 与 matrix oracle | [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) R13 remediation record | 增加完整 literal-copy `engine/f09/errors.py`；增加唯一 production-owned `DetectedIssue` pair；adapters 同时转发 returned records 与 typed exceptions；same-surface/no-issue/五 helper 保持 | 父实例以 producer literal closure、exact leading-slash path closure 与 constructor/import closure 不足拒绝 R13；该裁决固定，不得重判 PASS | 已由 PI-570-R14 有界整改接续 |
| PI-570-R14 | PI-500 | 有界 plan-only producer literal、exact-path 与 constructor/import closure 整改 | `BLOCKED` | `PI-570-R13=BLOCKED` 的固定父裁决 | R13 实际计划、Task 1、Tasks 6–8、Task 10 adapters、PI-210/220/230 与 PI-300 phase-owned rows | [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) R14 remediation record 与 parent static adjudication | leading-slash exact inventory、显式 success/no-issue empty tuple、cross-phase reset 规则及 feedback consistency 非 issue-oracle 边界获得父实例静态确认 | 父实例以 3 High + 1 Medium 拒绝：Task 6 在 shape guard 前解引用 nullable/未守卫结构；多数 non-returnable exception 仍是含省略号的未来指令；Tasks 6–8 依赖未定义 predicate/helper/local，无法机械复制并验证 branch reachability；Task 7 raw illegal-state Enum membership 未静态闭合 | `PI-500=BLOCKED`、`G5=IN_PROGRESS`；由全新分离 writer 执行有界 `PI-570-R15`；不得启动 `PI-590-R14` |
| PI-570-R15 | PI-500 | 有界 plan-only fail-closed producer mechanical closure 整改 | `BLOCKED` | `PI-570-R14=BLOCKED` 的固定 3 High + 1 Medium 父裁决 | R14 实际计划与父裁决、Tasks 6–8 producers、Task 10 adapters、PI-210/220/230、PI-300 phase-owned rows 与 immutable source snapshot fixture | [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) R15 remediation record 与 parent static adjudication | 父实例接受 guard-before-dereference、canonical `action_envelope`、多处 literal pair、八 predicate 文本计数及 raw-value-safe state guard 为局部静态改进 | 父实例以 4 High + 1 Medium fail-closed 拒绝：T27/T28 未比较 incoming key 且仅比较 payload 子集；T58 错把 source digest 与 submission digest 等同且无 prior operation；Task 8 validators 未展开并将 evidence/snapshot refs 冒充 canonical binding/learning targets；T96 与 accepted fixture identity 冲突且 T101 自身场景不可达；REPORT issue pair 的冻结 authority 不明 | `PI-500=BLOCKED`、`G5=IN_PROGRESS`；由全新分离 writer 执行有界 `PI-570-R16`；不得启动 `PI-590-R15` |
| PI-570-R16 | PI-500 | 有界 plan-only R15 固定 4 High + 1 Medium 整改 | `BLOCKED` | `PI-570-R15=BLOCKED` 的固定父裁决 | R15 实际计划与父裁决、PI-230 幂等/反馈 authority、PI-300 T21/T22/T27/T28/T58/T96/T101、immutable source snapshot fixture | [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) R16 remediation record 与 parent static adjudication | 父实例接受 exact T96 identity、literal T101 reachability、incoming artifact key、已展开 validator 以及移除 REPORT semantic issue pair为局部静态改进 | 父实例以 4 High + 1 Medium fail-closed 拒绝：retry 拒绝 partial manifest 且新 control type 无 canonical authority/caller transition；T58 无 prior/current canonical key/receipt 并把 changed-source new identity重命名为 same operation；`source_track_binding_ref` 错指 source evidence；statement/set/records/anchor refs 使用无关 digest、字段错位与 evidence 首项猜测；raw REPORT `OSError` 未留下 canonical attempt/audit evidence | `PI-500=BLOCKED`、`G5=IN_PROGRESS`；R16 保持拒绝；`PI-590-R16` 永久不得启动 |
| PI-570-R17 | PI-500 | 有界 plan-only R16 固定 4 High + 1 Medium 整改 | `BLOCKED` | `PI-570-R16=BLOCKED` 的固定父裁决 | R16 实际计划与父裁决、PI-230 artifact retry/attempt、feedback identity/binding/anchor authority、PI-300 T21/T22/T27/T28/T53/T54/T58 | [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) R17 remediation record 与 parent static adjudication | 父实例接受 partial manifest 可进入 retry、移除本地 new-operation exception、REPORT failed attempt audit、TrackSourceBinding 自身引用为局部静态改进 | 父实例以 5 High + 2 Medium fail-closed 拒绝：Task 10 仍调用旧 binder 签名且未构造 canonical keys/refs/anchor selections；RULE 与 CARD_FIELD validator 条件互斥导致 T53/T54 不可达；PREPROD run-only BOUND 与 production triple validator 冲突；T58 changed-input/new-identity 无 producer-owned observable outcome 且旧 prose 冲突；changed-key 复用固定 role 路径覆盖旧 operation；canonical refs/selection 校验不足；missing-role retry 未保全 schema/revision/frozen input identity | `PI-500=BLOCKED`、`G5=IN_PROGRESS`；R17 保持拒绝；`PI-590-R17` 永久不得启动；由 R18 有界整改接续 |
| PI-570-R18 | PI-500 | 有界 plan-only R17 固定 5 High + 2 Medium 整改 | `BLOCKED` | `PI-570-R17=BLOCKED` 的固定父裁决 | R17 实际 Task 7/8/10 文本与父裁决、PI-230 operation/retry/binding authority、PI-300 T53/T54/T58 与 canonical RULE anchor | [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) R18 remediation record 与 parent static adjudication | 父实例接受当前 binder 签名接线、统一 RULE anchor、producer-owned changed-source receipt、changed-key operation-directory 隔离为局部静态改进 | 父实例以 5 High + 2 Medium fail-closed 拒绝：canonical key digest 遗漏 item/revision/policy/top-level/schema-contract 输入；target digest 复用未重算 manifest digest；PREPROD 仍依赖 production statement/anchor 且 exact triple authority 不足；shape-invalid 后继续解引用；retry 将 superseded 历史强制匹配当前 identity；contract/revision/policy/order/uniqueness 校验不足；key 路径组件未做 containment preflight | `PI-500=BLOCKED`、`G5=IN_PROGRESS`；R18 保持拒绝；`PI-590-R18` 永久不得启动；由 R19 有界整改接续 |
| PI-570-R19 | PI-500 | 有界 plan-only R18 固定 5 High + 2 Medium 整改 | `BLOCKED` | `PI-570-R18=BLOCKED` 的固定父裁决 | R18 实际 Task 7/8/10 与 parent adjudication、PI-230 ArtifactRecord/Attempt/FeedbackBinding/PREPROD/INVALID/VersionedObjectRef authority、PI-300 T53–T58/T72/12.1 | [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) R19 controlling amendments、remediation record 与 parent static adjudication | 父实例接受 record-local attempt-chain、superseded/current 分账意图、命名 path preflight 及 canonical helper call 为局部静态改进 | 父实例以 5 High + 2 Medium fail-closed 拒绝：Task 8 连续代码仍未守卫解引用并保留 exact PREPROD triple；Task 10 仍无条件构造 production 材料；canonical-key helpers 未定义且 T55–T57 无 prior/current 单输入 stimulus；target-digest helpers 未定义且 prior/current graph 相同；retry 无显式 current refs/schema/contract authority；完整 validation 仅在 prose；path helper 未定义且 policy identity 前后冲突 | `PI-570-R19=BLOCKED`、`PI-500=BLOCKED`、`G5=IN_PROGRESS`；`PI-590-R19` 永久不得启动；由全新分离 writer 执行有界 `PI-570-R20` |
| PI-570-R20 | PI-500 | 有界 plan-only R19 固定 5 High + 2 Medium 整改 | `BLOCKED` | `PI-570-R19=BLOCKED` 的固定父裁决 | R19 实际 Task 7/8/10 连续代码与 parent adjudication、PI-230 ArtifactRecord/Attempt/VersionedObjectRef/FeedbackBinding/PREPROD/INVALID authority、PI-300 canonical feedback key、T53–T58、T72 与 approved policy identity | [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) R20 物理替换后的 Task 7/8/10 连续块、remediation record 与 parent static adjudication | 父实例接受 literal helper presence、物理 protocol branch、binder tagged dereference、显式 current retry 参数及 active positive RULE/policy literal 为局部静态改进 | 父实例以 3 High + 2 Medium fail-closed 拒绝：Task 10 PREPROD 从任意首记录改写出 run authority 且空 manifest 可异常；Task 7 初写与 retry 的 manifest digest 语义不一致；policy-v2 仍是 active key/eligibility 路径；production contract 仅非空不做 authority identity 等值；T55–T57 leaf tests 不直接观察 canonical-key/receipt/no-overwrite | `PI-570-R20=BLOCKED`、`PI-500=BLOCKED`、`G5=IN_PROGRESS`；`PI-590-R20` 永久不得启动；唯一下一动作=全新角色分离 writer 执行有界 `PI-570-R21` |
| PI-570-R21 | PI-500 | 有界 plan-only R20 固定 3 High + 2 Medium 整改 | `BLOCKED` | `PI-570-R20=BLOCKED` 的固定父裁决 | R20 实际 Task 7/8/10 连续代码与 parent adjudication、PI-230 ArtifactRecord/Attempt/PREPROD/VersionedObjectRef/FeedbackBinding authority、PI-300 T53–T58/T72/canonical feedback identity/approved policy identity | [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) R21 物理替换后的 Task 7/8/10 连续块、remediation record 与 parent static adjudication | 父实例接受初写/重试四个 materialized return 分支统一 exact-record digest helper、四类 production contract authority 显式等值、active current key/anchor/eligibility 固定 policy-v1 且 policy-v2 仅进入 prior key | 父实例以固定 2 High + 1 Medium fail-closed 拒绝：PREPROD authority 仍由 adapter 内部固定制造，非 caller-owned 可变图，故 empty/malformed/extensible 守卫不可被输入证伪；operation_result 错加在 ArtifactPhaseObservation 且 FeedbackPhaseObservation 未声明/未返回，T55–T57 receipt assertions 机械不可达；fixture-field translation prose 仍称 active policy_version 送入 evaluator，与 hard-coded current policy-v1 冲突 | `PI-570-R21=BLOCKED`、`PI-500=BLOCKED`、`G5=IN_PROGRESS`；`PI-590-R21` 永久不得启动；唯一下一动作=全新角色分离 writer 执行有界 `PI-570-R22` |
| PI-570-R22 | PI-500 | 有界 plan-only R21 固定 2 High + 1 Medium 整改 | `BLOCKED` | `PI-570-R21=BLOCKED` 的固定父裁决 | R21 parent static adjudication、Task 10 fixture/adapter/PREPROD 连续块、`FeedbackPhaseObservation` 与所有返回、fixture-field translation contract、T55–T57 leaf assertions、PI-230 ArtifactWriteAttempt authority | [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) R22 Task 10 bounded amendments、remediation record 与 parent static adjudication | 父实例接受 receipt 已移至并返回自 FeedbackPhaseObservation、T55–T57 直接观察 producer receipt、fixture policy prior/current 语义对齐为局部静态改进 | 父实例以固定 3 High fail-closed 拒绝：sole-copy imports 缺 ArtifactWriteAttempt 与 FeedbackOperationResult；PREPROD case/run 仍由 adapter 常量拥有且 baseline attempt 的 input_snapshot_refs 为空、完整 attempt-chain 未校验；PREPROD validate_versioned_ref 在后续 F09Error try 边界之前执行，malformed ref 可逸出而非形成 coherent observation | `PI-570-R22=BLOCKED`、`PI-500=BLOCKED`、`G5=IN_PROGRESS`；`PI-590-R22` 永久不得启动；唯一下一动作=全新角色分离 writer 执行有界 `PI-570-R23` |
| PI-570-R23 | PI-500 | 有界 plan-only R22 固定 3 High 整改 | `BLOCKED` | `PI-570-R22=BLOCKED` 的固定父裁决 | R22 parent static adjudication、Task 10 sole-copy imports、FeedbackFixture、`exercise_feedback_binding_phase()` PREPROD 连续块与 baseline PREPROD authority、PI-230 ArtifactRecord / ArtifactWriteAttempt 12.1 authority | [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) R23 Task 10 bounded amendments、remediation record 与 parent static adjudication | 父实例接受缺失 imports 补齐、PREPROD case/run 从 caller authority 全图推导、baseline attempt 携带非空 input ref，以及 typed `F09Error` observation routing 为局部静态改进 | 父实例以固定 2 High + 1 Medium fail-closed 拒绝：ArtifactRecord role 闭合集合、issue_ids 与 DigestRef 标量面未闭合；malformed-but-truthy nested scalar 可穿过 truthiness validator 并在 JSON serialization 引发未捕获 TypeError；attempt_number 可接受 bool 且 attempt scalar/coherence 未完整闭合 | `PI-570-R23=BLOCKED`、`PI-500=BLOCKED`、`G5=IN_PROGRESS`；`PI-590-R23` 永久不得启动；唯一下一动作=全新角色分离 writer 执行有界 `PI-570-R24` |
| PI-570-R24 | PI-500 | 有界 plan-only R23 固定 2 High + 1 Medium 整改 | `ACCEPTED_FOR_INDEPENDENT_REVIEW` | `PI-570-R23=BLOCKED` 的固定父裁决 | R23 parent static adjudication、Task 10 sole-copy PREPROD authority/attempt/ref validation 与 serialization boundaries、PI-230 7.1 VersionedObjectRef/DigestBinding/DigestRef 及 12.1 ArtifactRecord/ArtifactWriteAttempt authority | [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) R24 Task 10 sole-copy physical amendments、remediation record 与 parent static adjudication | 父实例直接接受闭合八类 role/八类 state、record/attempt/ref/digest 标量面、PREPROD-only malformed caller-material observation boundary、排除 bool 的连续 attempt/retry 链为有界 plan-text 完整性修复 | parseability、typing、runtime、serialization execution、implementation conformance、PI-500/G5 完成仍未证明；该接受不构成行为 PASS 或实施授权 | 已进入 PI-590-R24 独立静态复验；其 `BLOCKED` 裁决不撤销既有有界父接受历史 |
| PI-590-R24 | PI-500 | R24 独立怀疑式静态复验 | `BLOCKED` | `PI-570-R24=ACCEPTED_FOR_INDEPENDENT_REVIEW` | R23 parent adjudication、R24 实际 sole-copy imports/helpers/PREPROD preflight/record-ref-attempt coherence/两处 exception boundaries/target digest path、R24 remediation 与 parent adjudication、PI-230 7.1/12.1 authority、控制账本 | [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) `PI-590-R24 independent static review` | 独立确认 R24 的 role/state/scalar/nullability、开放 object_type、PREPROD caller-material boundary、排除 bool 的连续 attempt/retry 链未见新增语义回归 | `PI590-R24-H-01`：声明为完整 sole-copy 的 Task 10 模块缺少 `Mapping`、`DetectedIssue` 及四个跨 Task helper 的 import/local definition，且 canonical-key helper 依赖未声明 `_digest_ref_material`；存在隐藏 symbol 与 mechanical-copyability gap | `PI-590-R24=BLOCKED`、`PI-500=BLOCKED`、`G5=IN_PROGRESS`；已由全新角色分离 `PI-570-R25` 有界 writer 接续，仅修复该固定 High |
| PI-570-R25 | PI-500 | 有界 plan-only R24 固定 1 High + 0 Medium 整改 | `COMPLETED` | `PI-590-R24=BLOCKED` 的固定独立裁决 | R24 sole-copy import block、固定缺失符号使用点、Task 1/7/8 对应权威 public module imports/definitions、R24/R25 records 与控制账本 | [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) Task 10 sole-copy import/helper amendments、R25 remediation、parent static adjudication 与最终 parent acceptance | 父实例直接接受显式 `Mapping`、canonical `DetectedIssue`、四个 public-owner helpers 和本地 nullable `_digest_ref_material` 已闭合固定 mechanical-copyability High；PI-590-R25 独立 PASS 后由父实例直接复核接受 | 无 G5 plan-text 阻断；parseability、annotation/import resolution、typing、AST/accounting、collection、runtime、serialization execution与 implementation conformance 仍未证明 | 已收口；不得推断生产实现或测试执行授权 |
| PI-590-R25 | PI-500 | R25 独立怀疑式静态复验 | `COMPLETED` | `PI-570-R25=ACCEPTED_FOR_INDEPENDENT_REVIEW` | Task 10 完整连续 sole-copy、`PI590-R24-H-01` 全部使用点、R25 actual imports/local helper、Task 1/7/8 public owners、R24/R25 records、PI-230 authority 与控制账本 | [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) `PI-590-R25 independent static review` 与 `PI-590-R25 parent acceptance and G5 closeout` | 独立裁决及父实例直接接受均为 `PASS`：High=0、Medium=0、critical ambiguity=0、material evidence gap=0、mechanical-copyability gap=0、authority conflict=0、regression=0 | 动态执行面、实现符合性、生产就绪与 GitHub 同步均未证明 | `PI-590-R25=COMPLETED`、`PI-500=COMPLETED`、`G5=COMPLETED`；实现计划治理收口 |

## 5. 递归子任务协议

### 5.1 角色分工

主会话只负责：

- 读取总控状态；
- 选择唯一可启动的下一任务；
- 拆分和派发子任务；
- 裁决跨子任务冲突；
- 汇总证据；
- 更新本总控表；
- 组织独立验收；
- 在阶段门通过后请求用户批准。

子任务只负责被授权的单一边界，不得擅自扩大范围或改写父任务目标。

### 5.2 递归深度与标识

- 最大递归深度为 3 层；主会话不计入深度；
- 一级任务示例：`PI-100`；
- 二级任务示例：`PI-110`；
- 三级调查可使用 `PI-110-A`、`PI-110-B`；
- 第三级子任务不得继续拆分；需要继续拆分时必须返回父任务重新规划。

### 5.3 默认权限

- 子任务默认只读；
- 只有明确标记为写任务并列出允许修改文件时，才能修改文件；
- 同一文件同一时刻只允许一个写任务；
- 未授权文件一律不得修改；
- 调查任务不得顺手修复；
- 验收任务不得自行修复；
- 失败或证据不足时必须返回父任务裁决。

### 5.4 子任务派发必填项

每个子任务消息必须包含：

1. `task_id` 与 `parent_task_id`；
2. 单一目标；
3. 任务模式：只读调查、设计、写入或验收；
4. 必读事实源；
5. 允许读取范围；
6. 允许修改文件，默认“无”；
7. 明确禁止事项；
8. 交付物格式；
9. 完成条件；
10. 失败返回条件；
11. 是否允许继续递归拆分及剩余深度。

### 5.5 标准派发模板

```text
task_id: PI-xxx
parent_task_id: PI-xxx 或 null
mode: readonly | design | write | acceptance
objective: 一句话单一目标
required_sources:
  - 相对路径与必要章节
read_scope:
  - 允许读取目录或文件
write_scope:
  - 无，或精确文件清单
constraints:
  - 不新增冻结业务规则
  - 不扩大任务范围
  - 不把声明性 YAML 当可执行脚本
  - 不修改生产默认行为
expected_output:
  - 证据
  - 结论
  - 产物或建议
  - 遗留风险
completion_criteria:
  - 可机械检查的完成条件
failure_return:
  - 证据不足、冲突或越界时返回父任务
recursion:
  allowed: true | false
  remaining_depth: 0..2
```

### 5.6 子任务标准回报

每个子任务必须按以下顺序回报：

1. 结论：`PASS`、`FAIL`、`BLOCKED` 或 `NEEDS_DECISION`；
2. 任务 ID 与实际范围；
3. 关键证据：文件、符号、行号、命令或哈希；
4. 已修改文件；没有则明确写“无”；
5. 验证动作和结果；
6. 未解决风险和不能推断的项；
7. 对父任务的唯一建议下一动作。

### 5.7 汇总与状态更新

- 父任务不得只凭子任务摘要宣称完成，必须核验关键证据；
- 多个子任务结论冲突时，父任务必须建立独立裁决任务；
- 任务只有在交付物和验收证据均存在时才能改为 `COMPLETED`；
- `BLOCKED` 必须写明阻断项和解除条件；
- 每次状态变化只更新本总控表，不在多个文档复制动态任务状态；
- 阶段门必须由独立验收任务确认，不能由实现任务自验后直接通过。

## 6. 设计硬边界

1. F01–F12 已冻结，不得以实现便利重开定义。
2. 声明性机器附录不承载运行算法；生产代码只能读取数据并执行另行批准的接口逻辑。
3. `null` 与 `unresolved_fields` 是信息，不得以默认值静默回填。
4. `validation_timepoints` 与 `output_precision` 必须分账。
5. 现实事实轨与命理结构轨必须分账；未核验事件不得污染事实状态。
6. 没有完整原局链、现实必要门、相应时序机制或可裁决竞争关系时，必须支持追问、条件输出、弃权或人工复核。
7. 输出必须可回溯到输入事实、冻结卡字段、来源和判定步骤。
8. 最小垂直切片不得自动扩展为十二卡全量实现。
9. 所有生产变更必须保留现有入口兼容性，并具有测试和回滚路径。
10. 新证据或业务变化只能走正式契约变更流程，不在实现代码中暗改语义。

## 7. G1 架构盘点验收清单

PI-100 完成前必须回答：

- 现有命盘、现实问题、时间范围和已核验事实从哪里进入；
- pipeline 如何产生和传递 findings；
- 现有模型是否已表达来源、置信度、冲突、状态和事件；
- `OUTPUT`、`CONDITIONAL`、`ASK`、`ABSTAIN`、`HUMAN_REVIEW` 是否已有可复用表达；
- 现有竞争、仲裁、跨域一致性和报告 linter 可复用到什么程度；
- statement index 和反馈摄入如何绑定功能判定；
- 哪些模块可以复用，哪些需要适配器，哪些必须新设计；
- 哪些生产入口明确不得改变；
- 最小垂直切片候选及选择依据；
- 所有判断是否有文件、符号和调用链证据。

## 8. G6–G9 有界收口记录

### 8.1 结论

2026-07-26 按 [`g6-g9-execution-plan-for-terra.md`](g6-g9-execution-plan-for-terra.md) 完成 tests-only Task 10 vertical matrix、G7 集成验证、G8 隔离／回归验证与 G9 终验。G6、G7、G8、G9 均标记为 `COMPLETED`；该结论只覆盖本节列明的 F09 行为与隔离证据。

### 8.2 G6（含 Task 10 P0）

工作目录均为 `f:/多流派新思路`：

- `python -m pytest --collect-only tests/f09/test_f09_vertical_matrix.py -q` → **104 tests collected**，退出码 0；
- `python -m pytest tests/f09/test_f09_vertical_matrix.py tests/f09/test_f09_adapter_reachability.py -q` → **136 passed**，退出码 0；
- `python -m pytest tests/f09 -q` → **1172 passed**，退出码 0。

Task 10 tests-only 产物为 [`../tests/f09/test_f09_vertical_matrix.py`](../tests/f09/test_f09_vertical_matrix.py)、[`../tests/f09/test_f09_adapter_reachability.py`](../tests/f09/test_f09_adapter_reachability.py) 与 [`../tests/f09/data/f09_vertical_scenarios.py`](../tests/f09/data/f09_vertical_scenarios.py)。Adapter reachability 对齐 production 实际 first boundary；未为越过边界而削弱 production validator 或制造 tests-only owner authority。

### 8.3 G7 集成验证

- `python -m pytest tests/f09/test_application_opt_in.py -q` → **26 passed**，退出码 0；
- `python -m pytest tests/f09/test_f09_vertical_matrix.py -q` → **104 passed**，退出码 0；
- `python -m pytest tests/f09/test_current_run_authority.py -q` → **16 passed**，退出码 0；
- `python -m pytest tests/f09 -q` → **1172 passed**，退出码 0。

### 8.4 G8 隔离与回归验证

- `python -m pytest tests/f09/test_production_isolation.py -q` → **4 passed**，退出码 0；
- 两个 staged／preprod import-isolation selectors → **2 passed**，退出码 0；
- `python -m pytest tests/test_production_entrypoints_unchanged.py tests/test_performance_and_ports.py -q` → **11 passed**，退出码 0；
- EP004 production strict-render selector → **1 passed**，退出码 0。

上述命令仅出现既有 `engine.application.dual_engine_adapter` deprecated warning，未作为本次 tests-only 范围的修改理由。

### 8.5 G9 终验与全仓 sanity

- 新鲜 `python -m pytest tests/f09 -q` → **1172 passed in 72.65s**，退出码 0，与 G6/G7 计数一致；
- 新鲜 `python -m pytest -q` → **2 failed, 3001 passed, 6 skipped, 1 warning in 1181.42s**，退出码 1。

全仓两个失败均位于 F09 之外：[`test_witness_trust_boundary_is_explicitly_documented()`](../tests/evaluation/test_dataset.py:256) 要求 [`../tools/README.md`](../tools/README.md) 存在 witness trust-boundary 文案；[`test_handoff_names_first_legal_case_action_and_all_independent_holds()`](../tests/evaluation/test_prospective_gate_workflow.py:343) 要求 [`../handoff.md`](../handoff.md) 存在 prospective 首案与 HOLD 文案。二者不修改、不归因于本次 F09 tests-only 工作；按 G9 计划将其单独记录，**不得据此声称全仓绿**。

### 8.6 明确未证明边界

本次有界收口不证明：

- 全仓 100% 绿或全仓正确性；
- 6 个 skipped 场景的行为；
- 部署、发布或运行环境生产可用性；
- Git provenance、提交完整性或远程仓库同步；
- GitHub 同步、PR、Issue、Release 或任何服务端状态；
- F08 runtime、十二卡全量实现、YAML/mapping 可执行性；
- 超出已执行命令与已观察 first boundary 的 production readiness。

### 8.7 Task 9-P 专项合同 total-Gate 治理追溯

2026-07-27 对九个 specialty contract units → Task 9-P total Gate → G6 governance roll-up 进行了 supersession-aware 专项审计，持久化裁决见 [`g6-task9p-total-gate-roll-up-adjudication.md`](g6-task9p-total-gate-roll-up-adjudication.md)。该记录包含九行 owner-aware 矩阵、历史 `BLOCKED`／`REVISE` 保留规则、六条 fresh pytest 命令账本，以及行为证据与治理证据的分账。

唯一裁决为 **`REVISE — TRACEABILITY RECORD REQUIRED`**：未发现新的材料性前置缺口，但审计开始时不存在九单元 → Task 9-P → G6 的 durable、机械可审计 roll-up。新增 adjudication 与本有限链接是对该 traceability gap 的补正，不得循环解释为审计开始时已有 PASS，也不改变本节既有 G6–G9 `COMPLETED` 仅覆盖 F09 行为与隔离证据的范围。

本轮 fresh ledger 为：feedback eligibility 117 passed；artifact lifecycle 217 passed；两者组合 334 passed；application opt-in + production isolation 30 passed；current-run authority 16 passed；`tests/f09` 1172 passed；六条命令退出码均为 0。该 ledger 不单独授权 Task 9-P total Gate，不证明全仓绿、部署、生产就绪、Git provenance 或 GitHub 同步。

最小下一合法动作是对 adjudication 与本链接进行新鲜独立复读；只有后续独立 evidence review 才能决定是否另行升级为 `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`，当前总控不得自我升级。

本地状态保持 **LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION**；本轮未执行任何 Git 命令，GitHub 服务端写操作永久禁止。

### 8.8 Task 9-P total-Gate 后续独立升级复核

2026-07-27 在 §8.7 的 durable adjudication 与有限链接落盘后，完成一轮逻辑新鲜、独立、只读的 EVIDENCE_REVIEW，持久化复核见 [`g6-task9p-total-gate-upgrade-review.md`](g6-task9p-total-gate-upgrade-review.md)。复核重新读取九份专项 owner 文件的最后有效章节，以非 Git 文件时间戳与 SHA-256 登记当前库存，并机械核对 §8.7 与 adjudication 的链接、九行矩阵、六行命令账本、唯一既有裁决、依赖链及 non-inference boundaries。

本轮唯一升级裁决为 **`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`**。该 PASS 的依据是 durable record 形成后的后续独立复核，不是 adjudication 自我升级；§8.7 的 `REVISE — TRACEABILITY RECORD REQUIRED` 继续保留为审计开始时缺少记录的历史裁决，不被删除或倒写。

本轮未重跑 pytest：用户定义的可选 VERIFY 仅在内部自洽门禁需要新行为证据时启用，而该门禁已由原始 owner 章节复读、当前文件库存与只读文本机械检查闭合。§8.7 记载的六条 pytest 结果仍是上一轮账本，不冒充本轮 fresh execution。

本升级只关闭 Task 9-P total-Gate governance traceability。它不改写 G6–G9 既有行为结论，不授权 runtime/tests 修改，不证明全仓绿、两个非 F09 sanity 失败已解决、部署、发布、生产就绪、Git provenance、远程同步或任何 GitHub 状态，也不启动 G10 实现。

阶段 B 仅获准形成纯计划 [`g10-next-governance-milestone-plan.md`](g10-next-governance-milestone-plan.md)；任何 G10 实现、测试执行或生产默认变更都必须另行经过其自身准入、合同与证据 Gate。

本地状态保持 **LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION**；本任务未执行任何 Git 命令或 GitHub 操作。

### 8.9 G10-R1 F09 Production-Readiness Admission 与 Sanity Failure Closeout

2026-07-27 按 [`g10-next-governance-milestone-plan.md`](g10-next-governance-milestone-plan.md) 完成 G10.0–G10.10 全部子 Gate，持久化记录见 [`g10-r1-readiness-and-sanity-closeout.md`](g10-r1-readiness-and-sanity-closeout.md)。§8.5 登记的两个非 F09 sanity 失败（[`test_witness_trust_boundary_is_explicitly_documented()`](../tests/evaluation/test_dataset.py:256)、[`test_handoff_names_first_legal_case_action_and_all_independent_holds()`](../tests/evaluation/test_prospective_gate_workflow.py:343)）已通过精确写集 [`../tools/README.md`](../tools/README.md)、[`../handoff.md`](../handoff.md) 的最小修复各自闭合；fresh `tests/f09 -q` 为 `1172 passed`，与 G6–G9 计数一致；fresh 全仓 `pytest -q` 为 `3121 passed, 7 skipped, 1 warning in 1344.94s`，退出码 0，零 failed。

唯一裁决：`G10.9 = PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`；`G10.10 = HOLD F10`（F10 业务目标、owner 与依赖尚未由现有冻结事实唯一确定）。本节不改写 §8.1–§8.8 既有历史裁决，也不构成 F10 实现、部署、性能、安全或 Git/GitHub 同步的证明。

本地状态保持 **LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION**；本任务未执行任何 Git 命令或 GitHub 操作。
