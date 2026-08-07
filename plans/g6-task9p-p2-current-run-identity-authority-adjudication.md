# Task 9-P/P-2 current-run identity authority 独立裁决

> **裁决日期：** 2026-07-23  
> **裁决角色：** 独立 authority adjudicator；只读分析与本文档记录，不是 implementer，也不是后续 fresh reviewer。  
> **Gate：`BLOCKED`。** 本 Gate 未闭合 producer-owned current-execution identity；不得解释为 `PASS`、implementation 授权、P-1 实现授权、Task 9 主合同关闭或 Task 9-P 总 Gate 解锁。

## 1. 当前状态与裁决边界

当前总控状态以本轮任务给出的现行状态为准：

- P-1 authority contract 已获得第六轮 fresh independent `PASS`；该结果只关闭 P-1 合同 Gate，不授权 P-1 implementation。
- P-2 在本裁决前为 `BLOCKED`；Task 9-P 总 Gate 为 `BLOCKED`；Task 9 主合同为 `STILL_OPEN`。
- 已 PASS 的 P-1 合同及其 artifact filesystem/failure authority 不因本文而修改。P-1/P-2 边界见 [`g6-task9p-prerequisite-authority-contract.md`](g6-task9p-prerequisite-authority-contract.md)。
- 本文只裁决 Task 9 current execution identity 是否已有可机械证明的 producer owner，以及能否据此冻结 P-2 public authority surface。
- 本文不是 implementation plan，不授权修改 production、tests 或既有合同。
- 本轮没有运行 Python、pytest、Git 命令，也没有执行 GitHub service-side mutation。

## 2. 裁决问题

P-2 只有在以下事项能够同时机械闭合时才可能 `PASS`：

1. current Task 9 execution identity 的唯一 producer owner；
2. `run_id` 的 producer 来源、exact identity 与禁止 caller 重标规则；
3. manifest、`RUN_SNAPSHOT` graph 与同一 current execution 的不可伪造同一性证明；
4. feedback binding protocol 与 canonical track authority，包括 `STAGED_L6` 是否获准使用 run-target protocol；
5. public DTO/read port/builder 的必要性及 exact module、runtime shape、signature、construction order、validation precedence；
6. exact closed future write set；
7. typed failures、fail-closed precedence、negative falsifiers 与 failure ledger；
8. 禁止 caller 预构造、借用、跨 run 复用或重标 identity；
9. 与 P-1、Task 9 主合同及 feedback consumer 的边界；
10. authority Gate 与 implementation 授权严格分离。

本裁决发现第 1、3、4 项没有现行上游权威闭合，因此不得通过下游设计推定其余项目已经闭合。

## 3. Observed facts

### 3.1 当前 F09 artifact owner 只生产 statement-set graph

1. [`ArtifactSetManifest`](../engine/f09/artifacts.py:112) 的 records 可以表达 run roles，但当前 lifecycle writer 的 required roles 只有 `REPORT`、`STATEMENT_RECORDS`、`STATEMENT_INDEX`。
2. [`_record()`](../engine/f09/artifacts.py:330) 为当前 writer 生成的每条 record 固定写入 statement-set identity，并固定 `run_id=None`。
3. [`write_artifact_set()`](../engine/f09/artifacts.py:369) 与 [`coordinate_artifact_operation()`](../engine/f09/artifacts.py:1005) 因而生产的是 statement artifact manifest，不是由非空 `run_id` 约束的 run-only graph。
4. 当前 F09 production 路径中没有发现构造 [`PreprodRunAuthority`](../engine/f09/feedback.py:190) 的 producer；检索到的直接构造位于测试 fixture，测试可构造性不能证明 production current-execution provenance。

### 3.2 feedback runtime 是 consumer，不是 current-run identity producer

1. [`PreprodRunAuthority`](../engine/f09/feedback.py:190) 包含 `case_id`、`track`、`run_id`、manifest、target refs 与 content digest。
2. [`_preprod_authority_self_excluded_material()`](../engine/f09/feedback.py:1146) 验证传入 authority 的内部结构、digest、role cardinality 与排序；其 canonical track 硬编码为 `RunTrack.V5_V6_PREPROD`。
3. [`_preprod_target()`](../engine/f09/feedback.py:1715) 要求 `RUN_SNAPSHOT` 存在，并核对 submission、refs 与 manifest records 的 case、track、run、schema、digest 和 `VERIFIED` state。
4. [`validate_feedback_binding_record()`](../engine/f09/feedback.py:1908) 对 `PREPROD_RUN_TARGET` 同样把 expected target track 固定为 `RunTrack.V5_V6_PREPROD`；没有 `STAGED_L6` run-target protocol branch。
5. [`bind_feedback_operation()`](../engine/f09/feedback.py:1857) 消费 [`RawFeedbackAuthority`](../engine/f09/feedback.py:226)，并不生产 current Task 9 execution identity。
6. 上述校验能证明 caller 所持 graph 的内部一致性，但不能证明该 graph 就是调用当下 Task 9 current execution 的 producer output。

### 3.3 V5 存在独立 run snapshot 候选，但不是已闭合的 P-2 authority

1. [`V5RunSnapshot.from_output()`](../engine/v5/domain.py:389) 以 `case_id`、output schema version 与 output hash 派生 deterministic `run_id`。
2. [`run_v5_snapshot()`](../engine/v5/runner.py:1222) 运行 V5 后返回该 snapshot，因此它是一个真实 producer-owned V5 output snapshot 候选。
3. [`V5CaseManifest.from_run_snapshot()`](../engine/v5/domain.py:493) 和 [`V5FeedbackAttachment.from_run_snapshot()`](../engine/v5/domain.py:579) 从 snapshot 复制 `case_id` 与 `run_id`。
4. [`V5CaseManifest`](../engine/v5/domain.py:481) 不是 F09 [`ArtifactSetManifest`](../engine/f09/artifacts.py:112)：它没有 F09 `ArtifactRecord` graph、record state、observed digest、target refs 或 F09 manifest digest closure。
5. [`render_v6_preprod_case()`](../engine/v5/preprod.py:215) 先从 V5 output 构造 snapshot，再从同一 output 另行调用 [`build_ziping_career_decision_run()`](../engine/decision/r10_ziping_career.py:85)。它没有从 snapshot 原子构造 F09 run manifest/authority，也没有返回 immutable execution envelope。
6. [`build_ziping_career_decision_run()`](../engine/decision/r10_ziping_career.py:85) 的 decision `run_id` 来源是 raw input hash；[`V5RunSnapshot.from_output()`](../engine/v5/domain.py:389) 的 snapshot `run_id` 来源是 output hash。两者是不同 identity scheme，当前没有显式 same-execution bridge。
7. [`decision_run_from_snapshot()`](../engine/decision/v5_adapter.py:323) 虽然从 snapshot 恢复 output 后派生 decision run，但仍生成 decision 自己的 `drun` identity，并未建立 F09 所需的单一 run identity graph。
8. [`ProductionService._run_existing_job()`](../engine/application/production_service.py:141) 可调用 V6 preprod renderer，但它拥有另一项 `analysis_id`/job lifecycle；当前没有 observed public contract 将该 job identity、V5 snapshot identity、decision identity 与 Task 9 execution identity原子绑定。

### 3.4 Task 9 current execution owner 尚不存在

1. 旧 Task 9 合同指定的 [`engine/f09/application.py`](../engine/f09/application.py) 当前不存在。
2. 当前 [`engine/f09/`](../engine/f09/) 下没有 Task 9 application orchestrator，也没有 current-execution envelope/read port/builder。
3. PI-500-A1 冻结的是同一个 normalized evidence port instance 的复用，不生产 `run_id`、`RUN_SNAPSHOT` 或 run manifest；相关上游计划见 [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md)。
4. 旧 Task 9 application contract 把 feedback 调用保持为零，且依赖 caller-supplied artifact inputs；它不能证明 producer-owned current-run identity。该历史合同见 [`g6-task9-application-orchestrator-contract.md`](g6-task9-application-orchestrator-contract.md)。

### 3.5 track authority 未闭合

1. [`RunTrack`](../engine/f09/contracts.py:21) 的 closed enum 同时包含 `STAGED_L6` 与 `V5_V6_PREPROD`。
2. enum 成员存在只证明 canonical token 存在，不证明某一 feedback binding protocol 获准消费该 track。
3. 现行 [`PreprodRunAuthority`](../engine/f09/feedback.py:190) 与 `PREPROD_RUN_TARGET` validator 只接受 `V5_V6_PREPROD`。
4. 历史 Task 9 authority 要求 `STAGED_AUDIT` 映射到 `STAGED_L6` 并进入 feedback phase，但没有现行 runtime protocol authority 将 `STAGED_L6` 绑定为合法 run target。
5. 因此不能在 Task 9 application 层通过扩 enum、兼容分支或把 `STAGED_L6` 伪装成 production statement feedback 来填补该上游缺口。

### 3.6 typed failure owner 的现状

1. [`F09Error`](../engine/f09/errors.py:4) 及其 [`F09IntegrityError`](../engine/f09/errors.py:21)、[`F09SourceError`](../engine/f09/errors.py:25)、[`F09ContractError`](../engine/f09/errors.py:29)、[`F09WriteError`](../engine/f09/errors.py:33) 是现行 typed failure family。
2. feedback validator 通过 [`_error()`](../engine/f09/feedback.py:326) 将形状/合同错误映射为 `F09ContractError`，将 digest/integrity 错误映射为 `F09IntegrityError`。
3. 由于 current-execution producer 与 public authority constructor 尚不存在，当前没有 owner 可冻结 producer-side provenance failures、construction precedence 或 current-run mismatch failure ledger。

## 4. Inferences

以下为从 observed facts 得出的受限推论，不冒充直接事实：

1. V5 snapshot 可以成为未来 authority 设计的输入或上游候选，但不能原样充当 F09 [`PreprodRunAuthority`](../engine/f09/feedback.py:190)。
2. 仅比较 `case_id`、track、字符串 `run_id` 或 digest closure，仍允许 caller 借用一个内部一致但属于旧执行或另一执行的 graph。
3. 两个 deterministic identity scheme 即使都由 producer 生成，也不会自动成为同一 current execution identity；必须有一个 owner 原子建立并验证桥接关系。
4. 当前存在至少三类 materially different 设计路径：扩展 V5 producer、建立新的 F09 execution envelope producer、或定义只读 execution authority port。现有上游权威不能唯一选择其中之一。
5. 因为 owner 选择会决定 public schema、identity preimage、construction order、failure precedence 和 future write set，本裁决不能以“最小实现”为由擅自冻结其中任一方案。

## 5. Unknowns

1. Task 9 current execution 的规范 owner 应是 V5 runtime、未来 F09 application boundary，还是独立 execution authority service/port。
2. current execution identity 是否应复用 V5 output-derived `run_id`、decision `run_id`、production job `analysis_id`，或由新 owner 产生新的 identity。
3. F09 run manifest 是否应由现有 [`ArtifactSetManifest`](../engine/f09/artifacts.py:112) 的专用 producer 构造，或通过一个不同的 immutable envelope 引用现有 artifact owners。
4. `STAGED_L6` 是否应加入 `PREPROD_RUN_TARGET`，还是需要独立 protocol/tag/authority type。
5. `RUN_SNAPSHOT`、`DECISION_RUN`、`FEEDBACK_ATTACHMENT`、`MANIFEST` 的 exact schema versions、digest preimages、required/optional cardinality与原子 commit boundary。
6. producer-side current-run mismatch、cross-run reuse、stale manifest、identity relabel 与 partial construction 的 exact issue codes 和 precedence。
7. 哪个模块拥有 public DTO/builder/read port，以及它和 Task 9 orchestrator 的依赖方向。

这些 unknowns 会改变公共 API/schema，不能由本轮只读裁决自行消除。

## 6. Adjudicated clauses

### 6.1 Gate

P-2 authority Gate 裁决为 **`BLOCKED`**。

理由不是“尚未实现”本身，而是现行权威无法唯一识别并证明 Task 9 current execution 的 producer owner，也没有为 `STAGED_L6` 提供 run-target protocol authority。缺少这两项前置权威时，任何下游 DTO/builder 都会把 caller-held material 包装成伪 authority。

### 6.2 `run_id` 与 identity 禁令

在本 Gate 解阻前：

- caller、Task 9 application 与 feedback consumer 均不得生成、覆盖、重标或“确认” current-execution `run_id`；
- 不得从 raw feedback 的 `target_run_id` 反向签发 authority；
- 不得把 V5 snapshot `run_id`、decision `run_id` 或 production `analysis_id` 按字符串相等、case 相等或时间接近解释为同一 execution；
- 不得借用旧 manifest、其他 run 的 graph、测试 fixture 或 caller 重建 records；
- 不得把 statement artifact record 补写 `run_id` 后重标为 run graph；
- 不得把 statement role 重标为 `RUN_SNAPSHOT`。

### 6.3 manifest 与 `RUN_SNAPSHOT` 同一性

future authority 必须由同一个 producer owner 原子产出或通过不可变 read port 原子读取以下闭包：

- current execution identity；
- exact canonical track；
- case identity；
- producer-issued `run_id`；
- `RUN_SNAPSHOT` identity与digest；
- run manifest identity与digest；
- manifest records/refs 中全部 run roles；
- 可机械验证的 same-execution relation。

任何由 caller 分别提供上述字段，再由 builder 只做相等比较的方案均不合格。

### 6.4 feedback protocol/track

- 当前唯一 observed run-target protocol authority是 `V5_V6_PREPROD -> PREPROD_RUN_TARGET`。
- `STAGED_L6` 当前**未获裁决允许**使用 `PREPROD_RUN_TARGET`，也不得使用 `PRODUCTION_STATEMENT`。
- future upstream authority 必须明确选择：扩展现有 protocol、建立独立 staged protocol，或声明 `STAGED_L6` 无 feedback target；该选择必须先于 Task 9 application 合同修订。

### 6.5 public DTO/builder/read port

本轮不冻结新 public DTO、builder 或 read port，也不复活旧 [`NonProductionRunFeedbackInput`](g6-task9-authority-adjudication.md) / historical builder 草案。

原因：现有 owner 不充分，且存在 materially different 公共 schema 方案。此时冻结 exact module、runtime shape、signature 或 construction order 会越权选择架构，并可能把 caller 预构造 material 洗成 authority。

### 6.6 exact closed future write set

**当前获准 implementation future write set：空集 `∅`。**

- 不授权修改 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py)、[`engine/f09/feedback.py`](../engine/f09/feedback.py)、[`engine/v5/domain.py`](../engine/v5/domain.py)、未来 [`engine/f09/application.py`](../engine/f09/application.py) 或任何 tests。
- P-1 已冻结的 future implementation write set 仍属于 P-1，不能继承给 P-2，也不因 P-1 PASS 自动激活。
- 只有新的 upstream producer-ownership authority 合同获得 fresh independent `PASS` 后，才可在 Task 9 主合同中另行冻结一个非空、exact、closed implementation write set。

### 6.7 typed failures 与 fail-closed precedence

由于 producer API 未获权威选择，本轮只冻结下列最低限度 failure 要求，不冻结新 issue-code 字面量：

1. authority wrapper/type/closed-schema failure 必须先于任何 identity 使用而 fail closed；
2. producer provenance 缺失或不可验证必须阻止 authority construction，不能降级为 warning；
3. cross-run reuse、borrowed graph、relabel、manifest/snapshot execution mismatch 必须阻止 feedback binding；
4. digest/integrity mismatch 必须使用 integrity-class typed failure，不能被后续 not-found 或 track mismatch 覆盖；
5. `STAGED_L6` protocol 未获授权时必须在进入 feedback consumer 前停止；
6. producer failure 不得被 Task 9 application 改写成成功、空反馈或可学习结果；
7. P-2 不得调用 [`evaluate_learning_eligibility()`](../engine/f09/feedback.py:2031)。

future authority 必须另行冻结 exact issue codes 和完整 precedence；在此之前不得实现猜测性的错误映射。

### 6.8 P-1、Task 9 与 feedback consumer 边界

- P-1：只拥有 artifact filesystem authority/failure precedence；不拥有 current-run identity，不生产 feedback authority。
- P-2：只负责 producer-owned current-execution identity 与 run-feedback authority；不得修改 P-1 artifact semantics 来偷渡 run graph。
- Task 9 application：未来只能消费已获权威的 producer output，并按 phase order传递；不能生产或重签 authority。
- feedback consumer：[`bind_feedback_operation()`](../engine/f09/feedback.py:1857) 只验证和消费已建立的 authority；不能作为 current execution owner。
- learning owner：不在 P-2/Task 9 授权范围内。

## 7. Negative falsifier ledger

命中任一项即维持或恢复 `BLOCKED`，不得以局部测试通过替代 authority proof：

| ID | Negative falsifier | 必须结果 |
|---|---|---|
| P2-F01 | caller 直接传 `case_id`、track、`run_id`、manifest、refs，builder 只做相等检查 | `BLOCKED` |
| P2-F02 | 从 raw feedback `target_run_id` 产生或选择 current-run authority | `BLOCKED` |
| P2-F03 | 复用三角色 statement manifest，或给 statement records 补写 `run_id` | `BLOCKED` |
| P2-F04 | 把任意 artifact 重标为 `RUN_SNAPSHOT` | `BLOCKED` |
| P2-F05 | 从 tests/fixture 手工构造 [`PreprodRunAuthority`](../engine/f09/feedback.py:190) 并据此声称 producer 存在 | `BLOCKED` |
| P2-F06 | 把 [`V5CaseManifest`](../engine/v5/domain.py:481) 当作 F09 [`ArtifactSetManifest`](../engine/f09/artifacts.py:112) | `BLOCKED` |
| P2-F07 | 仅因 V5 snapshot 与 decision run 同 case 或来自同一函数调用就宣称同一 execution | `BLOCKED` |
| P2-F08 | 跨 run 借用旧 snapshot/manifest graph，或 caller 重建 records 后重新计算 digest | `BLOCKED` |
| P2-F09 | 将 `STAGED_L6` 伪装为 `V5_V6_PREPROD` 或 `PRODUCTION_DEFAULT` | `BLOCKED` |
| P2-F10 | 只扩 hard-coded enum/branch，不新增上游 protocol authority | `BLOCKED` |
| P2-F11 | Task 9 application 生成 `run_id`、authority digest 或 producer provenance | `BLOCKED` |
| P2-F12 | P-2 调用 learning eligibility 或产生 learning target refs | `BLOCKED` |
| P2-F13 | authority PASS 被解释为 implementation、Task 9 主合同或总 Gate 自动授权 | `BLOCKED` |
| P2-F14 | 未经上游裁决擅选 V5 extension、F09 envelope 或 read-port 三类公共方案之一 | `BLOCKED` |

## 8. STOP conditions

出现以下任一情况必须立即 STOP：

1. 要求修改已 PASS 的 P-1 authority contract；
2. 要求在 owner 未冻结前实现 DTO/builder/adapter；
3. 要求修改 production/tests 或运行验证以“发现”规范；
4. 要求以 caller assertion、fixture 或 digest self-consistency替代 producer provenance；
5. 要求无上游协议裁决地支持 `STAGED_L6` feedback；
6. 要求扩大到 learning execution；
7. 要求执行 Git mutation 或任何 GitHub service-side mutation；
8. 发现新的 materially different public API/schema 方案但没有唯一上游选择；
9. 试图把本作者自检称为 fresh independent review。

## 9. 候选解阻路径，不构成方案选择

以下仅是候选，不是 adjudicated API：

- **候选 A：V5 producer extension。** 由 [`run_v5_snapshot()`](../engine/v5/runner.py:1222) 或更上层 owner 原子生产 F09-compatible execution envelope 和 run graph。
- **候选 B：F09 execution owner。** 由新的独立 producer 在 Task 9 application 之前生产 immutable current-execution authority；application 只能消费。
- **候选 C：read-only authority port。** 由已有 runtime owner 持久化 execution graph，再由 exact read port 按不可由 caller 指定/重标的 current execution handle 返回闭包。

三者会产生不同依赖方向、schema、construction order、failure precedence 与 write set。现有证据无法唯一选择，因此本文不冻结任一方案。

## 10. 唯一下一合法动作

由总控启动一个新的、只读的 **upstream producer-ownership authority adjudication**，且只解决一个决策面：

1. 从候选 owner 中唯一选定 Task 9 current execution producer；
2. 冻结 producer-issued execution identity 与 `run_id` preimage；
3. 冻结同一 producer 原子提供的 immutable snapshot/manifest graph 或 exact read port；
4. 明确 `STAGED_L6` 的 run-feedback protocol authority；
5. 冻结 exact public module、DTO/port/builder surface、construction order、typed failure precedence和 closed future write set；
6. 明确禁止 caller preconstruction、borrowing、cross-run reuse 和 relabeling；
7. 完成后交由 fresh independent reviewer 审查。

在该上游 authority 获得 fresh independent `PASS` 前：P-2 保持 `BLOCKED`，Task 9-P 总 Gate 保持 `BLOCKED`，Task 9 主合同保持 `STILL_OPEN`，implementation write set 保持 `∅`。

## 11. 作者自检边界

本文作者仅执行一致性自检，确认：

- observed facts、inferences、unknowns、adjudicated clauses、falsifiers 与 STOP conditions 已分栏；
- 没有把 [`PreprodRunAuthority`](../engine/f09/feedback.py:190) 可构造性冒充 current-run provenance；
- 没有复活旧 P-2 DTO/builder 草案；
- 没有修改 P-1 合同；
- 没有冻结未经权威选择的公共 API/schema；
- exact current implementation write set 为 `∅`；
- Gate 明确为 `BLOCKED`；
- authority adjudication 与 implementation 授权严格分离。

该自检不是 fresh independent review。若 future upstream authority 合同完成，仍必须由新的 fresh independent reviewer 审查；本文的 `BLOCKED` 不可由作者自检升级为 `PASS`。

---

# 附录 A：第二轮上游 producer-ownership authority 裁决

> **裁决日期：** 2026-07-23
> **裁决范围：** 只裁决 P-2 上游 current-execution producer ownership；第 1–11 节保留为首轮 `BLOCKED` 历史，不被重写、不被解释为已获 implementation 授权。
> **本轮 verdict：** `PASS-READY FOR FRESH INDEPENDENT REVIEW`。这不是 fresh independent review 的 `PASS`，不授权 implementation，不改变 P-1、Task 9-P 总 Gate `BLOCKED` 或 Task 9 主合同 `STILL_OPEN`。

## A.1 本轮事实、推论与裁决输入

### Observed facts

1. [`V5RunSnapshot`](../engine/v5/domain.py:366) 与 [`DecisionRun`](../engine/decision/r10_ziping_career.py:114) 各自是 producer output，但其 `run_id` 方案不同，故均不能自动成为 F09 current-execution authority。
2. 现有 [`ArtifactSetManifest`](../engine/f09/artifacts.py:112)、[`ArtifactRecord`](../engine/f09/artifacts.py:87)、[`DigestRef`](../engine/f09/contracts.py:78)、[`PreprodRunAuthority`](../engine/f09/feedback.py:190) 与 F09 typed error family 已提供本裁决可复用的运行时形状。
3. 现有 statement artifact writer 固定生产三条 statement roles 且 `run_id=None`，其 P-1 语义、filesystem authority 与 failure precedence 不可被 P-2 改写。
4. [`RunTrack`](../engine/f09/contracts.py:21) 已有 `STAGED_L6` 与 `V5_V6_PREPROD`；现有 feedback consumer 对后者硬编码，尚未实现本轮授权的两 track 闭集。

### Inferences

1. 唯一能同时持有 Task 9 调用边界、P-1 操作结果、V5/decision 输入证据与 feedback authority 的最小 owner 是未来 F09 Task 9 application orchestrator；V5 extension 或独立 read port 都会另引入跨 owner 桥接或可借用 handle。
2. 因此该 orchestrator 必须是 authority 的 producer，而不能是仅消费上游 authority 的 wrapper；其 producer 行为限于该调用内的纯内存 binding construction，不能越过 P-1 写入边界。

### Adjudicated selection

**唯一选择：** 新建 [`engine/f09/application.py`](../engine/f09/application.py) 的 [`run_f09_slice()`](../engine/f09/application.py:1) 是唯一 public current-execution producer。它在同一次成功的 Task 9 调用中，取得 P-1 artifact operation 的已验证结果后，原子构造并返回 execution envelope。V5 snapshot、decision run 与其兼容 artifacts 仅是此 producer 已获得的输入证据；它们不是 authority issuer，caller、feedback consumer 和任何 future adapter 都不是 issuer。

## A.2 不可变 producer-owned runtime shape 与 public surface

唯一新增 public DTO 及字段顺序冻结如下；所有类均为 `@dataclass(frozen=True)`，不得增加 setter、registry、global state、I/O read port 或 alternate constructor：

```python
@dataclass(frozen=True)
class F09ExecutionAuthority:
    case_id: str
    track: RunTrack
    run_id: str
    artifact_authority: ArtifactOperationAuthority
    run_manifest: ArtifactSetManifest
    run_snapshot_ref: VersionedObjectRef
    decision_run_ref: VersionedObjectRef
    feedback_attachment_ref: VersionedObjectRef | None
    preprod_feedback_authority: PreprodRunAuthority
```

冻结的 public producer signature 为：

```python
def run_f09_slice(
    request: F09RunRequest,
    *,
    gate_inputs: tuple[GateEvaluationInput, ...],
    competition_input: CompetitionInput,
    root_input: RootInput,
    timing_input: TimingInput,
) -> F09RunResult: ...
```

[`F09RunResult`](../engine/f09/application.py) 必须以公开、不可变字段 `execution_authority: F09ExecutionAuthority` 持有唯一 envelope；其既有 result/findings 字段不在 P-2 重定义。不得暴露 `build_*authority()`、`from_caller_*()`、可传入 `run_id`/manifest/ref/authority 的 builder，亦不得以 export alias 提供等价旁门。

**输入与传播规则：**

- `F09RunRequest` 不得接受 `run_id`、run manifest、run graph refs、[`PreprodRunAuthority`](../engine/f09/feedback.py:190)、readiness boolean 或 caller 的 execution-authority object。
- `artifact_authority` 是 P-1 的 [`ArtifactOperationAuthority`](../engine/f09/artifacts.py) 原对象，producer 只保留并传递，不复制、不重签、不重验 statement projection semantic truth。
- `run_manifest` 只表达 run graph；它不得包含 `REPORT`、`STATEMENT_RECORDS` 或 `STATEMENT_INDEX`，也不得取得 P-1 statement records 的 ownership。
- `preprod_feedback_authority` 仅由同一 producer 内部 private adapter 从前八个 envelope fields 派生；该 adapter 不是 public surface，不能被 caller、consumer 或测试 fixture 当作 authority issuer。

## A.3 `run_id` identity、canonicalization 与 digest

producer 必须先完成 P-1 authority 及 run-graph structural/integrity validation，再对以下 **完整、固定字段顺序、bounded JCS** preimage 编码 UTF-8 并计算 SHA-256：

```json
{
  "domain":"f09.task9.execution.v1",
  "case_id":"<producer case_id>",
  "track":"<RunTrack.value>",
  "artifact_manifest_id":"<artifact_authority.manifest.manifest_id>",
  "artifact_manifest_digest":{"algorithm":"...","canonicalization":"...","value":"..."},
  "run_snapshot_ref":{"object_id":"...","schema_version":"...","digest":{}},
  "decision_run_ref":{"object_id":"...","schema_version":"...","digest":{}},
  "feedback_attachment_ref":null
}
```

其中 `feedback_attachment_ref` 存在时必须使用相同的完整 ref material 取代 `null`。`run_id` 精确为 `run-` 加该 digest 的前 32 个小写十六进制字符；完整 digest 同时以 [`DigestRef`](../engine/f09/contracts.py:78) 形式保留在 run graph 的 `RUN_SNAPSHOT` record metadata/material 中。实现必须复用仓库已采用的 bounded RFC 8785 JCS 与 lowercase SHA-256，不得使用 `json.dumps` 替代 canonicalization。

以下值**禁止**进入 preimage 或作为 identity 替代物：时间、时钟、随机 UUID、文件路径、`attempt_id`、`request_id`、caller label、raw feedback `target_run_id`、测试 fixture 值及外部可覆写 manifest。相同 canonical 输入重放必须给出相同 `run_id`；任一 snapshot/decision/feedback ref、P-1 manifest id/digest、case 或 track 改变必须给出不同 `run_id`。单独声称同一 `run_id` 不能授权 graph 复用：producer 仍须完整验证所有 binding。

## A.4 独立 `RUN_SNAPSHOT` graph 与 manifest 关系

1. producer 只在 P-1 operation 已成功、其 authority 原对象可用之后构造一个新的内存 [`ArtifactSetManifest`](../engine/f09/artifacts.py:112)。这不是调用 [`write_artifact_set()`](../engine/f09/artifacts.py:369)，不会产生额外 I/O，也不会修改 P-1 filesystem 生命周期。
2. run manifest 的 records 为唯一角色集合：必有 `RUN_SNAPSHOT`、`DECISION_RUN`、`MANIFEST`，可有一次 `FEEDBACK_ATTACHMENT`；所有 records 皆为 `VERIFIED`、同一非空 `case_id`、同一 canonical track、同一 producer-issued `run_id`、`statement_set_id=None`，且无重复 artifact id/role。
3. `RUN_SNAPSHOT`、`DECISION_RUN`、`FEEDBACK_ATTACHMENT` 的 expected/observed digest 必须相等并与其相应 [`VersionedObjectRef`](../engine/f09/trace.py) digest 相等。ref 顺序固定为 `RUN_SNAPSHOT`、`DECISION_RUN`、`FEEDBACK_ATTACHMENT`、`MANIFEST`。
4. 为避免把 hash 自引用伪装为可实现机制，`MANIFEST` record 的 expected/observed digest 是单独的 `f09.task9.run-manifest.document.v1` bounded-JCS document digest：该 document 固定包含 manifest id、key material 与除该 `MANIFEST` record 外的 ordered records；它不等于 outer [`ArtifactSetManifest.digest`](../engine/f09/artifacts.py:241)。outer manifest digest 仍完全按现有 artifact-record canonicalization 计算。两种 digest 必须各自被验证，不能互相替代。
5. run manifest 的 key 必须由 producer 内部产生，且其 `case_id`、track、source/contract digest 都来自同一 successful invocation 的已验证 inputs；不得接受 caller key。若现有 `IdempotencyKey.operation` 无适用 literal，P-2 不授权修改其 closed literal：实现必须在 fresh review 后确认复用的现有 operation 是否与 P-1 contract 一致；不能确认即 STOP，而非扩展 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py)。
6. 由 envelope 内部 adapter 构造 [`PreprodRunAuthority`](../engine/f09/feedback.py:190) 时，`target_refs` 采用上述固定顺序且包含四角色；其 `content_digest` 必须由现有 feedback owner canonical material 计算。任何 caller-built authority、manifest 或 refs 均不得进入该 adapter。

## A.5 `STAGED_L6` feedback protocol 裁决

`BindingProtocol` 不新增 literal。`PREPROD_RUN_TARGET` 的精确、closed target-track set 裁决为：

```python
frozenset({RunTrack.STAGED_L6, RunTrack.V5_V6_PREPROD})
```

未来 [`engine/f09/feedback.py`](../engine/f09/feedback.py) 必须将 [`PreprodRunAuthority`](../engine/f09/feedback.py:190)、[`_preprod_target()`](../engine/f09/feedback.py:1715) 与 [`validate_feedback_binding_record()`](../engine/f09/feedback.py:1908) 的既有单值硬编码一致替换为该同一 closed set；不得只修改其中一个 seam，不得新增 staged masquerade、production fallback 或 caller adapter。`PRODUCTION_STATEMENT` 仍只对应 `PRODUCTION_DEFAULT`；`STAGED_L6` 与 `V5_V6_PREPROD` 共同属于 non-production run target，且不得进入 [`evaluate_learning_eligibility()`](../engine/f09/feedback.py:2031) 或获得 production/learning authority。

## A.6 validation precedence、typed failure 与 side-effect boundary

producer 和内部 adapter 的 fail-closed 顺序固定如下：

1. exact type、frozen DTO shape、nonblank scalar、enum/role cardinality；失败为 [`F09ContractError`](../engine/f09/errors.py:29)；
2. P-1 `ArtifactOperationAuthority` 原对象、manifest identity 和 operation success；缺失/错误 shape 为 `F09ContractError`，swap/不一致为 [`F09IntegrityError`](../engine/f09/errors.py:21)；
3. run graph 的 roles、same case/track/run、`statement_set_id=None`、refs、verified states 与各 digest closure；任何 mismatch 为 `F09IntegrityError`；
4. exact bounded-JCS material、canonical digest、`run_id` recomputation；bypass、drift 或 collision-material mismatch 为 `F09IntegrityError`；
5. `PREPROD_RUN_TARGET` target-track closed-set/protocol validation；不在集合或 protocol mismatch 为 `F09ContractError`；
6. 仅全部通过后构造 immutable envelope 和内部 [`PreprodRunAuthority`](../engine/f09/feedback.py:190)。

任一步失败立即 STOP：不得调用 feedback binder、learning eligibility、额外 artifact I/O、mutable registry 或 global state；不得把错误转换为空 authority、warning 或 success result。P-2 不重新判定 P-1 statement projection 的语义真实性，也不得覆盖 P-1 已有 write/failure precedence。

## A.7 Closed future implementation/test write set

本裁决为未来经 fresh review 与另行 implementation authorization 后的唯一 closed write set；除下列文件外一律无权修改：

| 路径 | 唯一目的 |
|---|---|
| [`engine/f09/application.py`](../engine/f09/application.py) | 定义 Task 9 producer、不可变 envelope、private authority adapter 与原子 result return。 |
| [`engine/f09/feedback.py`](../engine/f09/feedback.py) | 将 preprod run-target 的 hard-coded track 校验收束为已裁决二元闭集。 |
| [`engine/f09/__init__.py`](../engine/f09/__init__.py) | 仅导出已冻结的 public application surface。 |
| [`tests/f09/test_application_opt_in.py`](../tests/f09/test_application_opt_in.py) | 覆盖 opt-in producer 调用及 result authority presence。 |
| [`tests/f09/test_production_isolation.py`](../tests/f09/test_production_isolation.py) | 证明 production 路径、P-1 ownership 和 learning 保持隔离。 |
| [`tests/f09/test_current_run_authority.py`](../tests/f09/test_current_run_authority.py) | 覆盖 identity preimage、same-invocation graph、swap、canonicalization 与 no-side-effect ledger。 |
| [`tests/f09/test_feedback_binding.py`](../tests/f09/test_feedback_binding.py) | 覆盖两 track 的 `PREPROD_RUN_TARGET` 正反例和 consumer anti-laundering。 |

明确不在 write set：[`engine/f09/artifacts.py`](../engine/f09/artifacts.py)、[`engine/f09/contracts.py`](../engine/f09/contracts.py)、任何 V5/decision 模块、P-1 合同、其他 production/tests。若实现发现上述 closed `IdempotencyKey` literal 无法合规复用，或任一必要改动超出本表，必须 STOP 并返回新的 authority adjudication；不得悄然扩大 write set。

## A.8 Negative falsifier ledger

| ID | seam | 负向输入/现象 | owner / 必须结果 | STOP |
|---|---|---|---|---|
| P2R-F01 | application request | caller 提供 `run_id`、manifest、snapshot ref 或 `PreprodRunAuthority` | producer 拒绝；`F09ContractError` | 不构造 envelope |
| P2R-F02 | envelope graph | snapshot/manifest 来自不同 invocation 或 cross-run swap | producer；`F09IntegrityError` | 不调用 feedback |
| P2R-F03 | identity | 相同 `run_id` 配不同 graph 或不同 preimage | producer；重算不匹配即 `F09IntegrityError` | 不返回 result authority |
| P2R-F04 | feedback protocol | track 不在 `{STAGED_L6, V5_V6_PREPROD}` 或 protocol 不匹配 | feedback consumer；`F09ContractError` | 不绑定 |
| P2R-F05 | run graph | 缺失或重复 `RUN_SNAPSHOT` | producer；`F09ContractError` | 不派生 feedback authority |
| P2R-F06 | manifest closure | outer 或 self-excluded manifest document digest drift | producer；`F09IntegrityError` | 不构造 envelope |
| P2R-F07 | P-1 seam | P-1 authority/manifest 原对象被替换，或 operation 未成功 | producer；`F09IntegrityError` | 不写额外 artifact、不绑定 |
| P2R-F08 | consumer boundary | consumer 用 caller-built authority 或 raw `target_run_id` 洗成 current authority | consumer 拒绝；`F09ContractError` | 不产生 binding success |
| P2R-F09 | side effects | 任一 validation failure 后发生 artifact I/O、registry mutation、feedback 或 learning 调用 | producer test failure；实现不合格 | 保持 fail-closed |
| P2R-F10 | canonicalization | 非 bounded-JCS、非 lowercase SHA-256、加入 clock/random/caller label | producer；`F09IntegrityError` | 不签发 run_id |
| P2R-F11 | semantic boundary | 用 statement artifact records 充当 run graph 或重验 P-1 statement truth | producer；`F09ContractError` | 不改写 P-1 |
| P2R-F12 | track isolation | `STAGED_L6` 伪装为 production 或送入 learning eligibility | application/consumer 拒绝；`F09ContractError` | 无 production/learning side effect |

## A.9 Materially different alternatives 与拒绝理由

| 方案 | 裁决 | 拒绝理由 |
|---|---|---|
| 扩展 [`run_v5_snapshot()`](../engine/v5/runner.py:1222) 为 authority issuer | 拒绝 | V5 output identity 与 decision identity 不同，仍需跨 owner 绑定 P-1 result/feedback graph，且扩大 V5 write surface。 |
| 独立 execution authority read port/service | 拒绝 | 要增加持久化 owner、可借用 handle 与新的 read boundary；现有证据不要求，违背最小无 registry/I/O 设计。 |
| F09 Task 9 application producer envelope | 选择 | 唯一已有调用边界能原子持有 P-1 result、execution inputs 与 feedback derivation，最小闭合 producer ownership。 |

## A.10 剩余 unknowns、权限边界与 reviewer handoff

剩余 unknown 仅限 implementation-level、不得由实现自行裁决：

1. [`IdempotencyKey`](../engine/f09/artifacts.py:48) 的既有 operation literal 是否可在不触碰 P-1 语义的条件下用于 run manifest key；若否即 STOP。
2. 未来 [`F09RunRequest`](../engine/f09/application.py) 与 [`F09RunResult`](../engine/f09/application.py) 的既有非 P-2 fields 的精确兼容迁移，必须服从 Task 9 主合同的单独裁决。
3. run-ref artifact payload 的具体 serializer/path locator 可在不改变本附录 shape、preimage、write set 与 side-effect boundary下，由 implementation contract 补足；若会改变任一冻结项即 STOP。

**权限状态：** 本附录仅令 P-2 authority document 有资格交 fresh independent reviewer。它不授权 implementation、不将 P-2 记为 fresh-review `PASS`、不解锁 Task 9-P 总 Gate、也不关闭 Task 9 主合同。fresh reviewer 必须独立检查本附录与首轮历史是否一致、write set 是否 closed、所有 falsifier 是否可机械证伪，并独立作出结论。

## A.11 本轮作者自检

作者自检确认：

- 首轮 `BLOCKED` 历史仍原样保留在第 1–11 节；
- 本轮明确区分 observed facts、inferences、adjudicated clauses、remaining unknowns、falsifiers 与 STOP；
- 唯一 producer 是 Task 9 F09 application，不将 V5/decision/consumer/caller 提升为 issuer；
- DTO、run identity preimage、manifest self-reference 的可实现 digest 分层、两-track protocol、错误优先级与闭集 write set 已冻结；
- 未触碰 P-1 authority contract、production、tests、Git、Python/pytest 或 GitHub service-side state；
- 未把作者自检称为 fresh independent review，也未授予 implementation 权限。

**作者 verdict：** `PASS-READY FOR FRESH INDEPENDENT REVIEW`。仅可移交 fresh independent reviewer；在其独立结论以及后续单独 implementation authorization 前，所有 implementation write set 均保持未授权。

---

# 附录 B：现行 P-2 admission 覆盖裁决

> **现行效力：** 附录 A 仅保留为历史记录；其 `PASS-READY`、API、owner、identity、manifest、feedback protocol、write set 与 falsifier 不再具有现行规范效力。[`g6-task9p-p2-upstream-contract-reconcile-adjudication.md`](g6-task9p-p2-upstream-contract-reconcile-adjudication.md:232) 第 10–16 节是唯一候选上游规范文本，仅以该 reconcile 自身取得的 fresh independent read-only review `PASS` 为 P-2 可消费的生效条件；P-2 作者自检或本附录 review 均不得替代、追认或推导该上游 `PASS`。当前控制证据链已记录该 reconcile fresh `PASS` 与 P-1 authority contract fresh `PASS`，但二者都只解锁下一串行合同 Gate，不授权 implementation。本轮唯一 write 是本文档；不修改 production、tests 或其他合同，不运行 Python、pytest、Git，不执行任何 GitHub mutation。

## B.1 明确废止的附录 A 条款

以下旧设计全部废止，不得作为 implementation 或 test 依据：

1. `run_f09_slice()` 作为 authority issuer，以及 `F09ExecutionAuthority` public DTO；
2. 向 legacy `F09RunResult` 添加 `execution_authority`，或改变 legacy callable、constructor、字段与 STOP semantics；
3. 读取不存在的 `ArtifactOperationAuthority.manifest`，以及 application/P-2 自行签发 `run_id`；
4. application/P-2 在内存构造、重建或重签 run manifest、root、records、refs 或 authority；
5. writable/self-referential `MANIFEST` record 及其 self-excluded record digest；
6. 扩展、复用、别名、隐式转换或实现期任选 legacy `IdempotencyKey` operation；
7. 由 P-2/Task 9 扩展 `STAGED_L6` feedback consumer；
8. 基于上述旧 graph 的 validation order、混合 implementation/test write set 与相关 falsifiers。

附录 A 中 anti-borrow、anti-swap、anti-relabel 与 validation failure 后零未授权副作用原则仅作为历史原则保留；其旧 API、字段、owner 或 graph 不是现行 proof surface。

## B.2 上游 Gate 生效后唯一可消费的 surface

P-2 只可消费、不得重定义下列经各自 owner Gate 交付的 surface：

1. P-1 的 exact `RunArtifactSetKeyV1`；`PROJECT_RUN_ARTIFACT_SET` 仅属于该 carrier，legacy `IdempotencyKey` 与 statement semantics byte-for-byte 不变，见 [`g6-task9p-p2-upstream-contract-reconcile-adjudication.md`](g6-task9p-p2-upstream-contract-reconcile-adjudication.md:778)。
2. P-1 的 `coordinate_run_artifact_set_v1()` 及其实际返回的 run `ArtifactSetManifest`；无 returned lifecycle result 即 STOP，见 [`g6-task9p-p2-upstream-contract-reconcile-adjudication.md`](g6-task9p-p2-upstream-contract-reconcile-adjudication.md:252)。
3. P-1 public `validate_run_artifact_manifest_v1(manifest: ArtifactSetManifest) -> DigestRef`；feedback/P-2 不导入 artifact private serializer/helper，也不复制 digest 算法，见 [`g6-task9p-p2-upstream-contract-reconcile-adjudication.md`](g6-task9p-p2-upstream-contract-reconcile-adjudication.md:744)。
4. Task 9 versioned `run_f09_slice_with_execution_authority_v1()` 与 exact immutable `F09RunExecutionResultV1(run_result, preprod_authority, unsupported_reason)`；legacy result 与 callable 均不变，见 [`g6-task9p-p2-upstream-contract-reconcile-adjudication.md`](g6-task9p-p2-upstream-contract-reconcile-adjudication.md:304)。
5. Feedback adapter 的 exact module-private validated-state carrier、其 `RunArtifactSetKeyV1` key 字段、verifier-returned records digest 与 helper 重验接口，以 R39 合同第 4.2 节为准，见 [`g6-task8-r39-feedback-adapter-contract.md`](g6-task8-r39-feedback-adapter-contract.md:101)；upstream 第 15.1 节中 carrier 的 legacy `IdempotencyKey` 字段与第 16.1 节冻结的 run-key isolation 不一致，故仅作历史接口提案保留，不得作为现行 proof surface。跨 owner 只允许调用第 14.3 节冻结的 public verifier，见 [`g6-task9p-p2-upstream-contract-reconcile-adjudication.md`](g6-task9p-p2-upstream-contract-reconcile-adjudication.md:632)；outer `MANIFEST` target-ref 只走第 13.4 节专用分支，见 [`g6-task9p-p2-upstream-contract-reconcile-adjudication.md`](g6-task9p-p2-upstream-contract-reconcile-adjudication.md:558)，且必须与第 16.1 节的 exact run-key/verifier closure 一致，见 [`g6-task9p-p2-upstream-contract-reconcile-adjudication.md`](g6-task9p-p2-upstream-contract-reconcile-adjudication.md:776)。`MANIFEST` 不是 projection、payload 或 record。
6. `V5_V6_PREPROD` 仅在全部前置 Gate 完成时可产生可空 `PreprodRunAuthority`；`STAGED_L6` 固定为 `preprod_authority=None`、`unsupported_reason="STAGED_L6_UNSUPPORTED"`，不得进入 binder、eligibility 或 learning。

## B.3 P-2 admission 边界

P-2 只验证已经由上述 public surface 交付的 mapping/admission、anti-borrow、anti-swap、anti-relabel 与 zero-side-effect 约束。P-2：

- 不生成 `run_id`，不构造 run key、root、manifest、records、refs 或 authority；
- 不修改、包装或扩展 legacy result/callable；
- 不读取 `ArtifactOperationAuthority.manifest`；
- 不调用 binder、eligibility evaluator 或 learning validator；
- 不拥有或修改 artifacts、application、exports、feedback producer/consumer implementation；
- adapter Gate 前不公开 producer-internal candidate authority；
- 任一 prerequisite surface 不存在、未 frozen、identity 不一致或 authority absent 时均 fail closed/STOP，不以 caller material补足。

## B.4 串行 Gate 与 closed scope

唯一顺序为：

1. upstream reconcile 第 10–16 节必须先由其自身 fresh independent read-only review 明确取得 `PASS`；缺少可独立核验的该项证据即 STOP，P-2 review 不得替代；
2. P-1 run-artifact public surface 独立 implementation/verification/freeze；
3. feedback adapter contract fresh `PASS` 后，独立 implementation/verification/freeze；
4. Task 9 versioned callable/envelope contract fresh `PASS` 后，独立 implementation/verification/freeze；
5. producer、verifier、adapter 与 versioned envelope 全部完成后，P-2 admission 才可 fresh review；
6. P-2 admission `PASS` 仍不自动解锁 Task 9 主合同、Task 9-P 总 Gate或任何 implementation。

任一 Gate 非 `PASS`、实现未获单独授权或 owner 需要越过 closed set，后续全部 STOP。当前控制证据链中的 upstream reconcile fresh `PASS` 只满足第 1 项，不自动满足第 2–6 项。

- 本次 document-only write set：仅 [`g6-task9p-p2-current-run-identity-authority-adjudication.md`](g6-task9p-p2-current-run-identity-authority-adjudication.md)。
- Future P-2 conditional candidate write set：仅本文档与 [`tests/f09/test_current_run_authority.py`](../tests/f09/test_current_run_authority.py)；该 test 只验证已交付 public surface，不拥有 producer implementation。
- 明确排除 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py)、[`engine/f09/feedback.py`](../engine/f09/feedback.py)、[`engine/f09/application.py`](../engine/f09/application.py)、[`engine/f09/__init__.py`](../engine/f09/__init__.py)、legacy result、所有上游 owner tests 与其他路径。

## B.5 现行 negative ledger 与 finding coverage

### B.5.1 原子 negative ledger

| ID | 唯一 proof seam | 原子负向 case / 参数化 case set | 必须结果 |
|---|---|---|---|
| P2B-F01 | authority manifest source | 读取不存在的 `ArtifactOperationAuthority.manifest` | STOP；不得推断或重建 manifest |
| P2B-F02 | lifecycle result provenance | application/P-2 内存构造或重签 manifest/root/records/refs/authority | STOP；只接受 P-1 lifecycle returned result |
| P2B-F03 | legacy ABI shape | 扩 legacy `F09RunResult`、constructor 或 callable signature | contract failure；legacy ABI 原样保留 |
| P2B-F04 | restricted-context helper ingress | 任一 helper 未分别重验 exact private carrier type、authority/manifest object identity 或 immutable comparison material | typed fail closed；不得进入 restricted branch |
| P2B-F05 | run-key type ownership | 扩展、复用、别名或隐式转换 legacy `IdempotencyKey` | STOP；只接受 exact `RunArtifactSetKeyV1` |
| P2B-F06 | public verifier run-key closure | 参数化逐项注入且一次只改变一个 case：carrier type、refs graph digest、role closure、per-role payload digest map 任一不 exact | 每个 case 均在同一 public verifier seam typed fail closed；零后续副作用 |
| P2B-F07 | manifest representation | writable/self-referential `MANIFEST` record | STOP；只能使用 outer target ref |
| P2B-F08 | run identity issuer | application/P-2/caller 自行签发或覆写 `run_id` | STOP；不得接受 caller identity 或另建 issuer |
| P2B-F09 | adapter publication Gate | adapter Gate 前公开 candidate `PreprodRunAuthority` | authority 保持 `None`；不得传给 consumer |
| P2B-F10 | verifier owner boundary | feedback 跨 owner 导入 private serializer/helper、复制 digest 算法或绕过 public verifier | STOP；只允许 exact public-verifier call |
| P2B-F11 | staged feedback protocol | `STAGED_L6` 产生 `PreprodRunAuthority`、扩 consumer protocol 或进入 binding/learning | unsupported branch；零 binder/learning calls |
| P2B-F12 | graph provenance | 非 exact producer-returned graph，包括 caller-built 或 cross-run borrowed graph，被 admission | typed fail closed；不得 repair、borrow 或重签 |
| P2B-F13 | ref role binding | snapshot/decision/feedback refs 被 swapped 或 relabeled | typed fail closed；不得按 caller label 修复 |
| P2B-F14 | owner/write-set closure | P-2 修改任一上游 owner path、owner test 或扩大 candidate write set | STOP；保持 closed owner/write set |
| P2B-F15 | outer manifest ref classification | outer `MANIFEST` ref 被当作 projection、payload、record、retry/root/key input | STOP；仅走 outer-ref 专用分支 |
| P2B-F16 | failure short-circuit | legacy 或 versioned validation 任一失败后仍构造 authority，或发生 filesystem、binder、eligibility、learning 副作用 | 保持原 failure/STOP；零未授权副作用，admission 维持 BLOCKED |

### B.5.2 前次 `6 Critical / 5 High / 4 Medium / 1 Low` finding 机械重建矩阵

前次 reviewer 的逐字 finding 清单未持久化到本文档；下表不冒充 reviewer 原文，而是依据其已记录的等级计数与冲突摘要建立的原子重建索引。fresh reviewer 必须同时核验：ID 数量精确为 `6/5/4/1`，16 行须映射 `P2B-F01`–`P2B-F16` 各一次且仅一次，每行只绑定一个 proof seam，B 条款与 falsifier 均可机械定位。F06 的四个参数化 case 只验证同一个 public-verifier closure seam，执行时必须一次只改变一个 case 并分别断言 fail closed；它们不是四个 finding，也不得用一个 case 的结果替代另一个。任一 ID 重复、遗漏、case 未逐项执行或把两个 proof seam 合并，本文档继续 `REVISE` 并 STOP。

| 重建 finding ID | 等级 | 原子条件 | 覆盖条款 | 对应 falsifier | 未命中时 |
|---|---|---|---|---|---|
| C-01 | Critical | 读取不存在的 authority manifest 属性 | B.1.3、B.3 | P2B-F01 | STOP |
| C-02 | Critical | application/P-2 内存构造 run manifest graph | B.1.4、B.3 | P2B-F02 | STOP |
| C-03 | Critical | legacy result/callable ABI 被扩展 | B.1.1–B.1.2、B.2.4 | P2B-F03 | STOP |
| C-04 | Critical | legacy `IdempotencyKey` 被扩展或复用为 run key | B.1.6、B.2.1 | P2B-F05 | STOP |
| C-05 | Critical | `MANIFEST` 被建模为 writable/self-referential record | B.1.5、B.2.5 | P2B-F07 | STOP |
| C-06 | Critical | P-2/Task 9 扩展 `STAGED_L6` feedback consumer | B.1.7、B.2.6 | P2B-F11 | STOP |
| H-01 | High | application/P-2/caller 成为独立 `run_id` issuer | B.1.3、B.3 | P2B-F08 | STOP |
| H-02 | High | adapter Gate 被绕过并提前公开 candidate authority | B.3、B.4 | P2B-F09 | STOP |
| H-03 | High | feedback 跨 owner 调 private seam、复制 digest 或绕过 public verifier | B.2.3、B.2.5 | P2B-F10 | STOP |
| H-04 | High | producer、adapter、P-2 owner/write set 混合 | B.3、B.4 | P2B-F14 | STOP |
| H-05 | High | validation failure 未短路，改变 legacy STOP 或产生后续副作用 | B.1.8、B.3 | P2B-F16 | STOP |
| M-01 | Medium | private carrier/helper exact type、object identity 与 material 未重验 | B.2.5、B.3 | P2B-F04 | STOP |
| M-02 | Medium | caller-built/cross-run borrowed graph 被接受 | B.3 | P2B-F12 | STOP |
| M-03 | Medium | graph refs 可 swap 或 relabel | B.3 | P2B-F13 | STOP |
| M-04 | Medium | exact run-key refs graph/role/payload closure 未验证 | B.2.1、B.2.5 | P2B-F06 | STOP |
| L-01 | Low | outer `MANIFEST` ref 被误归类为 projection/payload/record | B.2.5、B.3 | P2B-F15 | STOP |

## B.6 当前 Gate 与 reviewer handoff

当前控制证据链已分别取得 upstream reconcile 与 P-1 authority contract 的 fresh independent `PASS`；本附录只消费这些前置 verdict，不重新作出、替代或追认它们。其 implementation、feedback adapter、Task 9 versioned surface 与 P-2 admission implementation 均未因此授权。本附录作者状态为 **`REVISE — ready for fresh independent review`**；P-2 在 fresh review 前仍非 `PASS`，Task 9-P 总 Gate保持 `BLOCKED`，Task 9 amendment保持 `STILL_OPEN`。

**唯一下一动作：** 对附录 B 执行一次 fresh independent read-only review，核对其完整废止附录 A 冲突 surface、以 upstream 自身 fresh `PASS` 为生效前置、准确转引第 10–16 节、保持 owner/Gate/write-set 隔离，并机械核对 `6C/5H/4M/1L` 重建矩阵与 16 项原子 negative ledger。该 P-2 review 不替代 upstream review，也不授权 production/tests、Python、pytest、Git 或 GitHub mutation。

---

## B.7 Fresh independent read-only review record（2026-07-24）

- **审查角色与证据边界：** 独立逻辑审查；重新静态读取本附录 B、[`G6 Task 9-P Prerequisite Authority Contract`](g6-task9p-prerequisite-authority-contract.md:15)、[`P-2 upstream reconcile`](g6-task9p-p2-upstream-contract-reconcile-adjudication.md:772)、[`R39 feedback adapter contract`](g6-task8-r39-feedback-adapter-contract.md:1)、[`engine/f09/artifacts.py`](../engine/f09/artifacts.py:63) 与 [`engine/f09/application.py`](../engine/f09/application.py:34)。未将作者自检或历史 review 视为本次审查证据；未运行 Python、pytest、Git 或任何 GitHub-mutating operation。
- **已核验事实：** legacy [`IdempotencyKey`](../engine/f09/artifacts.py:63) 与 versioned [`RunArtifactSetKeyV1`](../engine/f09/artifacts.py:88) 彼此分离；P-1 public [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1683) 与 [`coordinate_run_artifact_set_v1()`](../engine/f09/artifacts.py:1745) 已是独立 surface；R39 仅冻结 feedback consumer admission；当前只观察到 legacy [`run_f09_slice()`](../engine/f09/application.py:135)，未观察到 versioned producer callable 或 immutable execution-result envelope。
- **B.1/B.2 disposition：** 附录 A 已被明确撤回，且 B.2 不再允许 application、P-2、feedback 或 caller 生成、重签、借用、swap 或 relabel run identity、manifest、records、refs 或 authority。`STAGED_L6` 保持不支持并不得进入 binder、eligibility 或 learning。
- **B.3/B.4 disposition：** owner、ABI 与 write-set 隔离保持完整。P-2 admission 只可消费 producer-owned surface；在 versioned Task 9 callable/envelope 尚未独立合同化、实施、验证和冻结前，B.4 的串行 Gate正确要求 fail-closed STOP，未把 P-1/R39 的结论转换为 Task 9 或 P-2 implementation authorization。
- **negative ledger disposition：** B.5 的 16 项原子 negative cases覆盖 authority manifest 臆造、caller issuer、legacy ABI 扩展、legacy/run-key 混用、self-referential manifest、跨 owner private serializer、`STAGED_L6` consumer 扩展、borrow/swap/relabel、outer-ref 误分类以及失败后的副作用；其 `6C/5H/4M/1L` 重建索引未发现遗漏或重复。

**Review verdict：`PASS`（仅附录 B 的 fresh independent read-only document review）。** 本 PASS 只关闭该文档审查 Gate；不表示 P-2 admission 已 PASS，绝不授权 P-1、P-2、Task 9、production 或 tests implementation，也不关闭 Task 9 amendment。

**现行状态与唯一下一合法动作：** P-1 prerequisite authority contract 为 `PASS`（仅该合同 Gate）；P-2 admission 为 `BLOCKED`；Task 9-P 总 Gate 为 `BLOCKED`；Task 9 amendment 为 `STILL_OPEN`。唯一下一合法动作是由总控在独立、精确授权下建立并审查 Task 9 versioned producer/envelope contract；在该合同、独立 implementation/verification/freeze 与后续 P-2 admission Gate全部完成前，停止所有 implementation、tests、Python、pytest、Git 和 GitHub service-side mutation。

---

# 附录 C：R41/R40/Task 9 durable freeze 后的现行 P-2 CONTRACT

> **规范效力：** 本附录完整保留附录 B 及其历史 verdict，仅覆盖附录 B 中已经被后续 durable freeze 改变的“现行状态、public surface 与唯一下一动作”。附录 B 仍是历史 admission/falsifier 来源，不得被倒写为当时已经存在后续实现。

## C.1 Gate 输入、目标与非目标

### C.1.1 当前 Gate 输入

现行控制链已分别取得以下 durable、evidence-bounded 前置结果：

1. R41 returned-carrier provisioning seam：`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`；
2. R40 public authority constructor：`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`；
3. Task 9 versioned producer/envelope：`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`；
4. 在上述三项 freeze 后执行的 fresh independent P-2 ADMISSION：`PASS`；其 durable Gate record 见 C.13。

这些 verdict 只构成 P-2 CONTRACT 的准入输入；不得推断本合同、P-2 tests、behavior、VERIFY、FREEZE、Task 9-P 或 G6 已 PASS。

### C.1.2 唯一目标

以 characterization-only unit 证明现行 public execution chain 已成为 P-2 的唯一 current-run identity authority surface：

```text
public caller
→ run_f09_slice_with_execution_authority_v1(...)
→ exact immutable F09RunExecutionResultV1
   ├─ legacy stop: exact legacy result + no authority + no owner call
   ├─ STAGED_L6: exact legacy result + explicit unsupported + no owner call
   └─ V5_V6_PREPROD success
      → R41 public producer exactly once
      → actual RunArtifactSetResultV1 object by identity
      → R40 public constructor exactly once
      → actual PreprodRunAuthority object unchanged in envelope
```

### C.1.3 非目标

P-2 不重新证明或实现：

- R41 的签名、registry、canonical serializer、manifest graph closure 或 filesystem lifecycle；
- R40 的 issuance verification、restricted manifest context、records digest reconciliation 或 feedback-owned digest；
- Task 9 的 production logic、legacy pipeline behavior 或新 track；
- feedback binding、eligibility、learning、deployment、Git、GitHub 或任何 remote mutation；
- 第二套 manifest、run identity、authority、serializer、verifier、issuer 或 compatibility adapter。

## C.2 冻结 public chain 与 owner boundary

### C.2.1 Task 9 application owner

唯一 versioned entrypoint 是 [`run_f09_slice_with_execution_authority_v1()`](../engine/f09/application.py:249)，唯一 public envelope 是 [`F09RunExecutionResultV1`](../engine/f09/application.py:111)。legacy [`run_f09_slice()`](../engine/f09/application.py:152) 与 [`F09RunResult`](../engine/f09/application.py:93) 必须原样保留，不得因 P-2 扩字段、扩参数或改变 identity。

### C.2.2 R41 artifact owner

Task 9 只能调用 R41 public [`coordinate_run_artifact_set_with_target_refs_v1()`](../engine/f09/artifacts.py:2041)，并接收 exact [`RunArtifactSetResultV1`](../engine/f09/artifacts.py:149)。P-2 只观察该 returned carrier 被按 object identity 向下传递；不得读取其私有构造材料、复制 issuance serializer，或自行重建 manifest/refs/proof。

characterization test 可以使用 `object.__new__(RunArtifactSetResultV1)` 生成 **exact-class opaque sentinel**，但只能在 patched owner boundary 中验证“R41 返回的同一对象被原样交给 R40”；不得读取、填充或声称验证 sentinel 内部字段。该 sentinel 不是合法 production carrier，也不得作为 R41/R40 correctness 证据。

### C.2.3 R40 feedback owner

Task 9 只能把实际 R41 result 交给 public [`construct_preprod_run_authority_v1()`](../engine/f09/feedback.py:1430)。P-2 只观察：调用一次、参数名与 object identity exact、R40 返回对象在 envelope 中 identity unchanged。P-2 不得调用 private restricted-context helper，不得构造或签发 [`PreprodRunAuthority`](../engine/f09/feedback.py:194)，不得进入 binder、eligibility 或 learning。

### C.2.4 package surface

package 只能继续公开冻结的 DTO 与 entrypoint；P-2 不新增 export。legacy `IdempotencyKey` 与 versioned [`RunArtifactSetKeyV1`](../engine/f09/artifacts.py:89) 保持 exact 分离，禁止 alias、subclass、implicit conversion 或 cross-use。

## C.3 禁止能力与失败不变量

以下任一观察均使当前 Gate `REVISE` 并 STOP：

1. application/P-2/caller 自建、重签、替换或修复 manifest、refs、proof、run identity 或 authority；
2. P-2 导入或调用 R41/R40 private serializer、digest、registry、signer、restricted-context helper；
3. legacy stop 或 `STAGED_L6` 分支调用 R41/R40；
4. identity/key admission 失败后仍调用 R41/R40；
5. R41 或 R40 failure 被重试、包裹、替换，或失败后返回 envelope；
6. P-2 调用 filesystem、binder、eligibility 或 learning；
7. 扩 legacy ABI、支持 `STAGED_L6` feedback，或创建第二 owner；
8. write set、测试实例、ledger disposition 或 selector 与本合同不一致。

所有 owner exception 必须按原 object identity 向 caller 传播；不得 retry，且不得执行后续 owner。

## C.4 exact closed write set

CONTRACT 通过后，唯一 runtime implementation write 是：

```text
tests/f09/test_current_run_authority.py
```

明确禁止修改：

```text
engine/f09/application.py
engine/f09/artifacts.py
engine/f09/feedback.py
engine/f09/__init__.py
任何既有 test/fixture
依赖、配置或其他路径
```

本 adjudication 文档只允许追加 Gate ledger；不得改写附录 A/B 历史。若首次 executable characterization 暴露 production defect，必须保留失败证据并返回 CONTRACT `REVISE`，不得在当前授权下修改 production。

## C.5 test contract 与静态实例 accounting

唯一新测试模块必须精确包含以下 8 个 top-level `test_` declarations，不得增加隐藏 helper test、dynamic generation 或 collection hook：

```python
def test_p2_public_abi_legacy_isolation_and_key_types_are_exact(): ...

def test_p2_legacy_stop_returns_exact_envelope_and_calls_no_authority_owner(...): ...

def test_p2_staged_l6_is_exactly_unsupported_before_authority_owners(...): ...

def test_p2_v5_v6_returns_actual_public_chain_without_copy_or_substitute(...): ...

def test_p2_identity_or_key_cross_use_fails_before_authority_owners(...): ...

def test_p2_owner_failure_short_circuits_without_retry_or_envelope(...): ...

def test_p2_static_public_only_boundary_has_no_private_or_downstream_calls(): ...

def test_p2_static_accounting_is_exactly_8_declarations_16_instances_and_16_dispositions(): ...
```

静态实例 accounting 必须为：

```text
public ABI/key isolation                1
legacy stop variants                    5
STAGED_L6 unsupported                   1
V5_V6 public identity chain             1
identity/key cross-use                  4
owner failure short-circuit             2
static owner/downstream boundary        1
static accounting/ledger closure        1
TOTAL declarations                      8
TOTAL collected instances              16
```

五个 legacy stop 参数必须对应现行五个 `stopped_at` phase；四个 identity/key failure 必须逐项覆盖 case、run、track 与 legacy-key cross-use；两个 owner failure 必须分别覆盖 R41 与 R40。每个参数实例都必须独立执行并断言自己的 fail-closed seam。

测试可复用现行 public DTO 或同模块内最小 local fixture，但不得导入既有 test module、复制 owner canonicalization/digest/signature算法，或以 private fields 作为 oracle。现有 [`test_application_opt_in.py`](../tests/f09/test_application_opt_in.py:320) 是前置 Task 9 证据，不替代 P-2 的独立 ledger closure，也不得被修改。

## C.6 `P2B-F01`–`P2B-F16` 机械 disposition

16 项 ledger 必须各出现一次且仅一次，分类总数必须精确为 `Direct 8 + Hybrid 5 + Prerequisite 3 = 16`：

| ID | 类别 | P-2 direct proof | durable prerequisite boundary |
|---|---|---|---|
| P2B-F01 | Direct | static/public ABI：不得从 authority 臆造 manifest | — |
| P2B-F02 | Hybrid | actual R41 returned sentinel 按 identity 进入 R40，无 P-2 substitute | R41 issuance/result correctness |
| P2B-F03 | Direct | legacy DTO、signature 与 return identity保持 exact | — |
| P2B-F04 | Prerequisite | P-2 不调用 private helper | R40 exact private-carrier revalidation |
| P2B-F05 | Direct | legacy key 与 versioned key exact 分离及 cross-use fail closed | — |
| P2B-F06 | Prerequisite | P-2 不复制 closure verifier | R41 public verifier的 type/graph/role/payload closure |
| P2B-F07 | Hybrid | P-2 不构造 writable/self-referential manifest | R41 outer-ref representation correctness |
| P2B-F08 | Direct | application/P-2/caller 无第二 run issuer | — |
| P2B-F09 | Direct | legacy/staged/failure 分支 authority均不公开 | — |
| P2B-F10 | Hybrid | static boundary只允许 R41/R40 public calls | R40 verifier/serializer owner correctness |
| P2B-F11 | Direct | `STAGED_L6` exact unsupported且零 owner/downstream call | — |
| P2B-F12 | Hybrid | actual returned carrier不可替换、借用或复制 | R41 issuance与R40重验 |
| P2B-F13 | Prerequisite | P-2 不修复/swap/relabel refs | R41 role binding与R40 reconciliation |
| P2B-F14 | Direct | exact single-test-file write set和owner边界 | — |
| P2B-F15 | Hybrid | P-2 不读取或重分类 outer manifest ref | R41/R40 outer-ref处理 |
| P2B-F16 | Direct | legacy、admission、R41、R40 failure均短路且零后续调用 | — |

`Hybrid` 只表示 P-2 直接证明 integration boundary，并消费 owner freeze证明 owner内部性质；不得把二者合并为 P-2 自己已重证 crypto/graph correctness。`Prerequisite` 不进入 P-2 动态重演；其 durable ledger 必须在 EVIDENCE_REVIEW 中被明确引用，不能由 P-2 test count替代。

## C.7 RED、characterization-only 与 production-change 语义

当前 [`test_current_run_authority.py`](../tests/f09/test_current_run_authority.py) 不存在，只能记录：

```text
missing-test structural RED
```

这不是已执行 behavioral RED。CONTRACT `PASS` 后创建测试并首次运行时：

- 若 16 个实例全部 GREEN，记录 `characterization-only GREEN / no production implementation required`；不得伪造 production `RED → GREEN`；
- 若 collection error，行为证据为零，分类为 selector/test defect或环境失败；
- 若 assertion failure，保留 exact failure，分类 product defect/test defect/contract gap并返回 CONTRACT `REVISE`；
- 任一失败均不得自动扩大 write set或修改 production。

## C.8 STATIC_REVIEW 与 VERIFY

### C.8.1 fresh STATIC_REVIEW

实现后由逻辑新鲜、只读 reviewer 至少核验：

- 只修改唯一新测试文件；
- 8 declarations、16 instances 与参数矩阵 exact；
- 只依赖 public surface，opaque sentinel 不读取内部字段；
- 无 private import、owner算法复制、filesystem/binder/eligibility/learning call；
- legacy/staged/failure short-circuit及 exception identity oracle完整；
- 16 ledger disposition无遗漏、重复或错误升级；
- 未执行 GitHub-mutating operation。

STATIC_REVIEW `PASS` 只授权 exact VERIFY，不证明行为正确。

### C.8.2 exact VERIFY selectors

fresh STATIC_REVIEW `PASS` 后才允许从仓库根目录依次执行：

```text
python -m pytest tests/f09/test_current_run_authority.py -q
python -m pytest tests/f09/test_application_opt_in.py tests/f09/test_current_run_authority.py -q
python -m pytest tests/f09 -q
```

预期 collection accounting（以 Task 9 freeze 的现行 `1019` baseline 为前提）：

```text
P-2 module                         16
Task 9 application + P-2          26 + 16 = 42
F09 regression                    1019 + 16 = 1035
```

中间 selector 有意只选择 `test_application_opt_in.py` 与 P-2 模块，因此消费 Task 9 application 的 `26` 项基线；Task 9 的 `30` 项总基线还包含 `test_production_isolation.py` 的 `4` 项，只在完整 F09 regression 中消费，不得错误计入中间 selector。

执行前必须重新核验 baseline 未被其他合法 unit 改变；若改变，不得硬套 `1035`，必须记录 observed collection并重新 reconciliation。每次命令记录 cwd、环境、完整 selector、collection、pass/fail/error、exit code与 rerun history。

## C.9 EVIDENCE_REVIEW 与 FREEZE

fresh EVIDENCE_REVIEW 必须独立核对：

1. CONTRACT fresh verdict 与实际 write set；
2. STATIC_REVIEW fresh verdict；
3. 三条 exact VERIFY evidence及计数 reconciliation；
4. 8 declarations / 16 instances / 16 dispositions 的静态与动态闭合；
5. 所有失败、collection error、repair和 rerun历史；
6. R41、R40、Task 9 durable prerequisite ledgers；
7. 直接证明、消费前置证明与未证明边界；
8. 本 controlled session 未执行 GitHub-mutating operation的直接记录。

只有上述全部成立，P-2 才可获得：

```text
PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE
```

该 freeze 只证明现行 P-2 public integration authority boundary；不证明 R41/R40 内部算法被 P-2 重验，不代表 Task 9-P、G6、deployment、publication或 GitHub同步完成。

## C.10 STOP、failure routing 与永久禁止

- CONTRACT、STATIC_REVIEW、VERIFY 或 EVIDENCE_REVIEW 任一 `REVISE`：停止后续 Gate，仅允许最小只读诊断和冻结范围内修复；修复后旧 STATIC_REVIEW失效。
- write-set扩大、production change需求、owner contract冲突或 baseline不可解释：返回 CONTRACT `REVISE`。
- 保护冲突或不可授权安全冲突：`BLOCKED`。
- 仅真正缺失且无法从权威证据推导的用户决策/外部能力：`AUTHORIZATION_REQUIRED`。
- 永久禁止 push、PR、Issue、Release、workflow dispatch及任何 GitHub service-side mutation；该能力不存在，不得请求授权。

## C.11 fresh independent CONTRACT reviewer checklist

reviewer 必须重新读取本附录及必要的冻结 public surface，逐项给出 observed facts、inferences、unknowns与唯一 verdict，并回答：

1. R41 → R40 → Task 9 public chain是否精确且唯一？
2. 是否确实可由 test-only characterization完成，无 production change？
3. opaque exact-class sentinel是否只验证 identity handoff而未冒充合法 carrier？
4. closed write set是否唯一且足够？
5. 8 declarations / 16 instances是否机械可收集、无隐藏重复？
6. `Direct 8 + Hybrid 5 + Prerequisite 3` 是否覆盖全部16项且各一次？
7. RED/GREEN、collection failure及首次失败路由是否诚实？
8. STATIC_REVIEW、VERIFY、reconciliation与 EVIDENCE_REVIEW是否可执行且可证伪？
9. STOP、owner boundary、legacy/STAGED compatibility和GitHub永久禁止是否闭合？

任一答案不成立，verdict 为 `REVISE`；不得给部分 PASS。

## C.12 作者状态与唯一下一动作

**作者状态：`REVISE — ready for fresh independent CONTRACT review`。** 本附录由合同作者重建，不是 fresh review，也不授权创建 [`test_current_run_authority.py`](../tests/f09/test_current_run_authority.py)、运行 Python/pytest或修改 production。

**唯一下一合法动作：** 由逻辑新鲜、独立、只读 CONTRACT reviewer重新读取附录 C、R41/R40/Task 9 durable freeze与附录 B 16项 ledger，使用 C.11 checklist作出唯一 verdict。只有 fresh CONTRACT `PASS` 才授权在 C.4 单文件 write set内创建 characterization oracle。

## C.13 Fresh independent P-2 ADMISSION durable Gate record（2026-07-25）

| 字段 | durable record |
|---|---|
| Gate | P-2 ADMISSION after R41/R40/Task 9 durable freeze |
| Owner role | G6 controller；只负责重建准入输入与计算唯一候选，不作 CONTRACT 或 behavior verdict |
| Fresh reviewer role | 逻辑新鲜、独立、只读 ADMISSION reviewer |
| Authorization envelope | 只读 R41、R40、Task 9 freeze ledger、P-2附录B及必要 public surface；禁止修改文件、Python、pytest、Git与GitHub mutation |
| Required inputs | upstream reconcile document PASS；P-1 authority contract PASS；R41、R40、Task 9 durable evidence-bounded freeze；附录B prerequisite chain与16项 ledger |
| Observed facts | R41 已冻结 signed `RunArtifactSetResultV1` returned-carrier surface；R40 已冻结只接收 actual returned carrier 的 public constructor；Task 9 已冻结 versioned immutable execution-result envelope与legacy/STAGED short-circuit；附录B旧 manifest-only surface已被后续实现改变；candidate test文件不存在 |
| Inferences | 唯一 active candidate 是 Task 9 versioned producer/envelope → R41 signed result → R40 public authority constructor → envelope returned authority；附录B staleness必须在 CONTRACT reconstruction修订，不构成循环式 ADMISSION blocker |
| Unknowns | P-2 CONTRACT、测试、STATIC_REVIEW、VERIFY与behavior尚未产生；未来 baseline可能改变 |
| Required outputs | 唯一候选、prerequisite disposition、owner/non-goal/compatibility boundary、minimum candidate write set、STOP与唯一 verdict |
| Falsifiers | 任一 prerequisite未 durable freeze；存在第二合法issuer/authority constructor；候选需要修改production或legacy ABI；`STAGED_L6`必须进入feedback consumer；owner/write set无法闭合 |
| STOP conditions | prerequisite缺失；候选不唯一；需要caller-built manifest/authority；扩legacy ABI或STAGED consumer；owner boundary冲突；GitHub mutation |
| Verdict | **PASS** |
| Direct evidence boundary | 仅证明P-2已具备进入CONTRACT reconstruction的准入资格及候选唯一性 |
| Forbidden inference boundary | 不证明CONTRACT PASS、测试存在、behavior correctness、implementation authorization、VERIFY/FREEZE、Task 9-P或G6完成 |
| Minimum next authorization | 仅授权document-only重建现行P-2 CONTRACT并进行fresh independent CONTRACT review |

**ADMISSION verdict：`PASS`。** 本 PASS 已由后续附录 C reconstruction消费；它不追认附录B历史状态，也不授权创建测试、运行pytest或修改production。

## C.14 Fresh independent CONTRACT review #1 与 bounded document repair（2026-07-25）

### C.14.1 review #1 evidence 与 verdict

逻辑新鲜、独立、只读 reviewer重新读取附录 C、附录B ledger、R41/R40/Task 9 durable freeze及必要 public/test surface；未编辑文件，未运行Python、pytest、Git或GitHub-mutating operation。

reviewer确认以下合同设计成立：public chain唯一；test-only characterization原则上足够；exact-class opaque sentinel只可证明identity handoff；单一未来测试文件write set足够；`8 declarations / 16 instances`静态算术闭合；`Direct 8 + Hybrid 5 + Prerequisite 3`无重复遗漏；structural RED与failure routing诚实；legacy/STAGED/owner/GitHub边界闭合。

发现两个document-only缺口：

1. C.8.2第二条selector只选取Task 9 application模块的`26`项与未来P-2的`16`项，却错误写成`30 + 16 = 46`；
2. C.1.1声明fresh P-2 ADMISSION `PASS`，但当时未在限定证据中提供可独立定位的durable Gate record。

**Review #1 verdict：`REVISE`。** 该 verdict禁止创建测试、运行pytest或修改production，只授权最小document repair与再次fresh CONTRACT review。

### C.14.2 bounded repair disposition

本次作者修订仅：

- 将中间selector accounting更正为`26 + 16 = 42`，并明确Task 9其余`4`项只由完整F09 regression消费；
- 追加C.13 fresh P-2 ADMISSION durable Gate record，并从C.1.1建立可定位引用；
- 持久化本次`REVISE`失败历史，未删除或改写review finding。

未改变public chain、opaque sentinel边界、closed write set、8/16 accounting、8/5/3 disposition、structural RED、STOP或永久GitHub禁止；未创建/修改tests或production，未运行Python/pytest/Git/GitHub operation。

**修订后作者状态：`REVISE — ready for fresh independent CONTRACT re-review`。** 唯一下一合法动作是fresh independent、只读CONTRACT re-review；只有新 verdict为`PASS`才授权进入单文件test-only IMPLEMENT。

## C.15 Fresh independent CONTRACT re-review #2（2026-07-25）

| 字段 | durable record |
|---|---|
| Gate | P-2 CONTRACT fresh independent re-review |
| Owner role | P-2 CONTRACT owner；维护characterization contract、ledger disposition、Gate routing与授权边界，不拥有R41/R40/Task 9 production surface |
| Fresh reviewer role | 第二次逻辑新鲜、独立、只读CONTRACT reviewer；重新读取权威材料，不把review #1结论当事实 |
| Authorization envelope | 只允许静态读取附录B/C、三项freeze ledger及必要public/test surface；禁止编辑、Python、pytest、Git与GitHub mutation |
| Required inputs | 附录B 16项ledger；修订后的附录C；C.13 ADMISSION record；R41、R40、Task 9 durable freeze；必要public/test surface |
| Observed facts | C.13提供完整且边界正确的fresh ADMISSION `PASS` durable record；中间selector精确为application `26`加future P-2 `16`等于`42`，Task 9其余`4`项只进入完整F09 regression；public chain、source refs与opaque sentinel先例可定位；single future test-file write set、8 declarations/16 instances与8/5/3 disposition闭合；C.14保留review #1 `REVISE`及bounded repair历史 |
| Inferences | 现行合同已把characterization目标、实例数、ledger唯一覆盖、owner handoff、negative space、执行顺序与failure routing冻结到足以安全进入test-only IMPLEMENT |
| Unknowns | future test尚不存在；16 instances尚未collection或执行；42项selector与完整F09 regression尚无动态证据；behavior、STATIC_REVIEW、VERIFY、EVIDENCE_REVIEW与FREEZE均未产生 |
| Required outputs | 唯一CONTRACT verdict、直接证据边界、禁止推断边界与最小下一授权 |
| Falsifiers | 实现需要production change；测试必须读取opaque carrier字段或调用private seam；8 declarations不能形成16 instances；16 ledger未唯一覆盖；selector不能收集26+16；legacy/STAGED触达R41/R40；owner exception被包裹/吞没；C.14失败历史被删除或改写 |
| STOP conditions | production write；第二测试文件；private/downstream调用；P-2自建manifest/refs/proof/run identity/authority；legacy ABI变化；实例或ledger漂移；未经授权运行pytest；Git/GitHub mutation |
| Verdict | **PASS** |
| Direct evidence boundary | 仅证明现行P-2 characterization CONTRACT内部闭合、与冻结public seams对齐、单文件test-only IMPLEMENT可执行 |
| Forbidden inference boundary | 不证明测试存在或通过、R41/R40内部算法被P-2重验、合法production carrier、STATIC_REVIEW/VERIFY/EVIDENCE_REVIEW/FREEZE、Task 9-P或G6完成 |
| Minimum next authorization | 仅授权IMPLEMENT：创建`tests/f09/test_current_run_authority.py`作为16-instance characterization oracle；不授权pytest、production修改、Git或GitHub mutation |

### C.15.1 C.11 checklist disposition

1. public caller → Task 9 → R41 returned carrier → R40 authority → Task 9 envelope的surface与identity handoff精确且唯一；
2. test-only characterization足够；若暴露product defect则返回CONTRACT `REVISE`，不改production；
3. exact-class opaque sentinel只在patched owner boundary验证identity，不读取字段、不冒充合法carrier；
4. write set唯一闭合为future `tests/f09/test_current_run_authority.py`；
5. 8个top-level declarations按`1+5+1+1+4+2+1+1`机械形成16 instances；
6. Direct 8、Hybrid 5、Prerequisite 3覆盖P2B-F01–F16各一次；
7. missing-test structural RED、首次characterization GREEN、collection/error/failure routing诚实；
8. STATIC_REVIEW、三条VERIFY selector、计数reconciliation与EVIDENCE_REVIEW可执行、可证伪；
9. STOP、legacy/STAGED、owner boundary与永久GitHub禁止闭合。

**CONTRACT re-review #2 verdict：`PASS`。** 该PASS仅关闭P-2 CONTRACT Gate并授权C.4单文件test-only IMPLEMENT；不授权运行pytest，不授权修改production，不证明behavior、STATIC_REVIEW、VERIFY或FREEZE。

**唯一下一合法动作：** 创建`tests/f09/test_current_run_authority.py`，精确实现C.5冻结的8 declarations/16 instances characterization oracle；完成写入后立即STOP并进入fresh independent STATIC_REVIEW，不得先运行pytest。

## C.16 P-2 IMPLEMENT 与 fresh independent STATIC_REVIEW ledger（2026-07-25）

### C.16.1 IMPLEMENT record

在C.15 CONTRACT `PASS`授权后，Implementer仅创建`tests/f09/test_current_run_authority.py`，未修改production或既有测试。该文件建立8个top-level test declarations，并以静态参数化算术表达`1 + 5 + 1 + 1 + 4 + 2 + 1 + 1 = 16`个characterization instances；覆盖public ABI/key isolation、五个legacy stop、`STAGED_L6` unsupported short-circuit、V5/V6 public owner chain identity/order、四个pre-owner admission failure、两个owner failure、public-only static boundary与P2B ledger closure。

opaque sentinel仅以`object.__new__(RunArtifactSetResultV1)`在patched owner boundary中验证exact-class object identity handoff；测试不读取或填充其字段，不调用真实R40处理该对象，也不把它当作合法production carrier。IMPLEMENT阶段未运行Python或pytest，未声明behavior PASS，未执行Git或GitHub-mutating operation。

**IMPLEMENT disposition：`COMPLETE — test-only candidate ready for STATIC_REVIEW`。** 该记录仅证明冻结write set内的候选文件已建立，不证明collection、执行或正确性。

### C.16.2 Fresh independent STATIC_REVIEW #1

逻辑新鲜、独立、只读Static Reviewer重新读取C.5/C.6/C.8冻结合同、唯一候选测试文件及必要public owner surface；未编辑文件，未运行Python、pytest、Git或GitHub-mutating operation。

reviewer确认8 declarations与16-instance静态算术、legacy/STAGED/owner chain、identity handoff、admission/owner failure、public-only negative space及ABI/key isolation的总体结构成立，但发现三项test-only机械闭合缺口：

1. `P2B_DISPOSITIONS`虽然保持`Direct 8 + Hybrid 5 + Prerequisite 3`总数，却没有实现C.6逐ID exact mapping；
2. accounting oracle只校验category cardinality和ID顺序，错误mapping仍可通过，未冻结完整16-tuple semantic disposition；
3. accounting oracle只校验8个声明数量，未冻结exact ordered declaration names，也未排除module-level dynamic collection hooks。

**STATIC_REVIEW #1 verdict：`REVISE`。** 该失败使任何VERIFY资格失效；只授权在唯一文件`tests/f09/test_current_run_authority.py`内进行上述三项bounded test-only repair，并要求修复后重新取得fresh STATIC_REVIEW。production、第二测试文件、pytest、Git与GitHub mutation仍不授权。

### C.16.3 Bounded test-only repair

Implementer仅修改`tests/f09/test_current_run_authority.py`：

- 将`P2B_DISPOSITIONS`修正为C.6冻结的完整逐ID mapping；
- 在accounting test中加入完整`expected_dispositions`并断言tuple exact equality；
- 加入8个exact ordered declaration names断言；
- 显式禁止`pytest_collect_file`、`pytest_collection_modifyitems`、`pytest_generate_tests`与`pytest_pycollect_makeitem`四个module-level dynamic collection hooks。

修复未改变8个测试声明、静态16-instance算术、owner/behavior范围或write set；未修改production或第二文件，未运行Python/pytest/Git/GitHub operation。因候选文件发生修改，STATIC_REVIEW #1保持历史`REVISE`且不可复用，必须重新fresh review。

### C.16.4 Fresh independent STATIC_REVIEW #2 durable Gate record

| 字段 | durable record |
|---|---|
| Gate | P-2 fresh independent STATIC_REVIEW after bounded repair |
| Owner role | P-2 test-only Implementer；只拥有冻结单文件候选，不拥有production或review verdict |
| Fresh reviewer role | 第二次逻辑新鲜、独立、只读Static Reviewer；重新读取合同和修复后候选，不把review #1判断或作者自评当事实 |
| Authorization envelope | 只读附录C、`tests/f09/test_current_run_authority.py`及必要public owner surface；禁止编辑、Python、pytest、Git与GitHub mutation |
| Required inputs | C.15 CONTRACT `PASS`；C.5/C.6/C.8冻结合同；C.16.2失败历史；C.16.3 bounded repair；修复后唯一候选文件 |
| Observed facts | 候选仍为单一test file；8个top-level declarations名称与顺序exact；静态参数化算术为16；五legacy stop与STAGED short-circuit均在authority owners前结束；V5/V6测试冻结legacy→R41→R40顺序及actual object identity；四admission failures与两owner failures闭合；public-only boundary、ABI/key isolation、完整16-item disposition mapping与dynamic-hook negative space均被机械断言 |
| Inferences | 当前候选在静态结构上满足P-2 CONTRACT，未发现明显collection/runtime defect；exact VERIFY selectors可安全执行 |
| Unknowns | pytest尚未collection或执行；16、42及完整F09动态计数尚未观察；behavior correctness、EVIDENCE_REVIEW与FREEZE尚未产生 |
| Falsifiers | collection不是16；任一selector失败或报错；application selector不是42且无法合法reconcile；完整F09 baseline异常；测试触达private/downstream seam；owner call/order/identity动态断言失败 |
| STOP conditions | 任一collection error、failure、count mismatch或环境异常；需要修改production、扩大selector/write set或执行Git/GitHub mutation |
| Verdict | **PASS** |
| Direct evidence boundary | 仅证明当前单文件候选静态符合合同：8 exact ordered declarations、16静态实例、五legacy stop、STAGED短路、成功identity/order/opaque handoff、四admission failure、两owner failure、public-only边界、ABI/key isolation及16项ledger closure；且未发现明显collection/runtime defect |
| Forbidden inference boundary | 不证明测试已collection或通过，不重验R41/R40内部算法，不证明behavior correctness、EVIDENCE_REVIEW/FREEZE、Task 9-P或G6完成 |
| Minimum next authorization | 仅授权VERIFY，并严格从仓库根目录依次运行C.8.2三条exact pytest selectors；不授权修复、production修改、Git或GitHub mutation |

**STATIC_REVIEW #2 verdict：`PASS`。** 该PASS只解锁以下串行VERIFY子授权：

1. `python -m pytest tests/f09/test_current_run_authority.py -q`；
2. 仅当第1条valid PASS且collection为16时，运行`python -m pytest tests/f09/test_application_opt_in.py tests/f09/test_current_run_authority.py -q`；
3. 仅当第2条valid PASS且collection为42时，运行`python -m pytest tests/f09 -q`，并在执行前后观察完整F09 baseline、对任何合法变化做reconciliation。

任一命令出现collection error、failure、unexpected count或environment/tool failure，立即STOP并按failure routing分类；不得自动修改production。三条均valid PASS也只产生VERIFY evidence，必须再经fresh independent EVIDENCE_REVIEW，不能直接FREEZE。

**唯一下一合法动作：** 从仓库根目录执行第1条exact selector；当前behavior仍为unknown。

## C.17 P-2 VERIFY 与 fresh independent EVIDENCE_REVIEW（2026-07-25）

### C.17.1 Dynamic execution ledger

执行环境：仓库根目录`f:/多流派新思路`；Python `3.14.5`；pytest `8.4.2`。三条命令均已预检为本地只读测试执行，不包含Git、GitHub、网络发布或远端mutation；输出均完整、未截断，未使用后台任务或超时继续。

| Run | Exact command | Expected | Observed | Exit code | Duration | Disposition |
|---:|---|---:|---:|---:|---:|---|
| 1 | `python -m pytest tests/f09/test_current_run_authority.py -q` | 16 | 16 passed | 0 | 0.21s | valid focused PASS |
| 2 | `python -m pytest tests/f09/test_application_opt_in.py tests/f09/test_current_run_authority.py -q` | 42 | 42 passed | 0 | 0.35s | valid combined PASS |
| 3 | `python -m pytest tests/f09 -q` | 1035 | 1035 passed | 0 | 69.56s | valid F09 regression PASS |

运行严格串行：第2条只在第1条valid PASS后执行，第3条只在第2条valid PASS后执行。最后一次候选修复发生在三次运行之前，且修复后已有C.16.4 fresh STATIC_REVIEW `PASS`；不存在post-run change、rerun、collection error、partial run、scope drift、environment failure或unknown exit code。

### C.17.2 Static/dynamic reconciliation

| Surface | Static source | Static expected | Dynamic observed | Difference | Reconciled |
|---|---|---:|---:|---:|---|
| P-2 module | 8 exact declarations，参数化算术`1+5+1+1+4+2+1+1` | 16 | 16 | 0 | YES |
| Task 9 application + P-2 | 既有application 26 + P-2 16 | 42 | 42 | 0 | YES |
| Full F09 | 冻结pre-P-2 baseline 1019 + P-2 16 | 1035 | 1035 | 0 | YES |

Task 9其余4项production-isolation tests不在第2条selector内，但已由第3条完整F09 selector消费；因此不存在把Task 9历史总数30错误套入第2条selector的计数漂移。

### C.17.3 Failure and invalid-evidence accounting

- CONTRACT review #1 `REVISE`及两项document repair保留于C.14；
- STATIC_REVIEW #1 `REVISE`及三项test-only repair保留于C.16.2–C.16.3；
- 修复前未运行pytest，因此不存在需要冒充fresh behavior evidence的旧RED/GREEN输出；
- 本轮三次VERIFY均为首次授权执行且valid PASS；invalid evidence ledger为空；
- characterization-only结果为GREEN，表示现行production public chain已满足新增characterization oracle，不构造虚假的production RED→GREEN历史。

### C.17.4 Fresh independent EVIDENCE_REVIEW durable Gate record

逻辑新鲜、独立、只读Evidence Reviewer仅以C.15合同、C.16 STATIC_REVIEW ledger、三次完整命令输出及运行环境查询作为当前证据；不把作者自评、旧摘要或旧测试结果当作fresh evidence，未编辑候选或production，未重跑测试，未执行Git或GitHub-mutating operation。

| 字段 | durable record |
|---|---|
| Gate | P-2 fresh independent EVIDENCE_REVIEW |
| Evidence identity | current-run identity/authority characterization；C.15 contract；C.16.4 post-repair static candidate |
| Freshness | 三次运行均发生于最后修复和fresh STATIC_REVIEW `PASS`之后，且审查前无后续代码变化 |
| Authorization | exact C.16.4三条串行selector；路径、顺序与working directory均匹配 |
| Completeness | 三条输出完整，含passed count、duration与exit code；无截断、后台或timeout |
| Static/dynamic reconciliation | `16=16`、`26+16=42`、`1019+16=1035`，差值均为0 |
| Failure history | CONTRACT `REVISE`与STATIC_REVIEW `REVISE`均保留；无失败运行、无效证据或未披露rerun |
| Falsifier review | selector drift、count mismatch、stale/unauthorized evidence、partial/collection failure、failed-history omission及局部证据系统化外推均未成立 |
| Verdict | **PASS** |
| Freeze eligible | **YES** |
| Direct evidence boundary | P-2单文件16-instance characterization在Python 3.14.5/pytest 8.4.2环境下通过；与Task 9 application联合42项通过；完整F09 1035项通过；静态/动态accounting精确闭合 |
| Forbidden inference boundary | 不独立重验R41签名/crypto/graph或R40内部restricted-context算法；opaque sentinel不是合法production carrier；不证明仓库全套测试、性能、安全、部署、Task 9-P或G6完成；不证明GitHub整体状态 |
| Minimum next authorization | 仅授权P-2 evidence-bounded FREEZE与本地durable state更新；不授权production change、Git或GitHub mutation |

**EVIDENCE_REVIEW verdict：`PASS`。** 当前证据满足P-2单元冻结条件，但只能在上述直接证明边界内冻结。

## C.18 P-2 PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE（2026-07-25）

### C.18.1 Frozen unit

P-2 current-run identity/authority characterization单元现冻结为：

```text
PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE
```

冻结产物：

- 唯一characterization oracle：`tests/f09/test_current_run_authority.py`；
- 现行合同与完整Gate/失败/验证ledger：本附录C；
- production change：无。

### C.18.2 Directly proven

当前新鲜有效证据直接证明：

1. public caller通过Task 9 versioned entrypoint时，五个legacy stop保持exact legacy result identity，且不触达R41/R40；
2. `STAGED_L6`精确返回unsupported envelope并在authority owners前短路；
3. V5/V6 path按legacy→R41→R40顺序各调用一次，并把actual ingress identities交给R41、把R41 actual exact-class returned object按identity交给R40、把R40 actual authority按identity放入immutable envelope；
4. case/run/track mismatch与legacy-key cross-use均在authority owners前fail closed；
5. R41/R40 owner exception按对象identity传播，无retry、无下游调用或伪造envelope；
6. P-2 public-only static boundary、legacy/versioned ABI separation、key type isolation、8 declarations/16 instances与P2B-F01–F16 exact disposition closure成立；
7. focused 16、combined 42及完整F09 1035项均fresh valid PASS。

### C.18.3 Not proven / forbidden inference

本冻结不证明且不得推断：

- opaque sentinel拥有合法字段、issuance proof或production carrier语义；
- P-2重新证明R41 cryptographic issuance、manifest/ref graph correctness或R40 restricted-context内部算法；
- legacy ABI支持authority，或`STAGED_L6`进入feedback consumer；
- caller/application可自建manifest、refs、proof、run identity或authority；
- 完整仓库test suite、性能、安全、可移植性、部署或发布状态；
- Task 9-P、后续Task 4–Task 10、P-1、feedback、G6 phase或整个program完成；
- GitHub整体未变化、已同步、已创建PR、已合并或已发布。

受控会话未执行任何Git或GitHub-mutating operation；该局部观察不得扩展为对GitHub整体状态的断言。

### C.18.4 Freeze protections and next boundary

- 冻结文件与合同不得被后续单元静默改写；任何影响本单元surface或oracle的变化都必须重新ADMISSION并重建后续Gate；
- P-2 FREEZE不继承为相邻单元的CONTRACT、IMPLEMENT或VERIFY授权；
- production仍不在本单元write set内；永久禁止GitHub service-side mutation；
- 本冻结只关闭P-2单元，不关闭Task 9-P或G6。

**唯一下一合法动作：** 返回G6控制状态，依据权威任务依赖为尚未冻结的后续Task 4–Task 10、P-1、feedback或Task 9-P总冻结计算唯一下一候选并重新进入INVENTORY/ADMISSION；不得把本P-2 FREEZE当作相邻单元授权。
