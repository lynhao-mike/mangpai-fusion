# G6 Task 9-P 总 Gate 专项合同 Roll-up 裁决

- 裁决日期：2026-07-27
- 审计对象：九个 specialty contract units → Task 9-P total Gate → G6 governance roll-up
- 审计方式：supersession-aware contract review + fresh ordered behavior verification + logical independent evidence review
- 唯一裁决：**`REVISE — TRACEABILITY RECORD REQUIRED`**
- 状态：**`LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION`**

## 1. 裁决摘要

九个专项单元的最后明确有效章节、owner 职责、历史失败与后续 supersession 已可组成一条非循环依赖链。R40、R41、R42、Task 9 versioned producer/envelope 与 P-2 current-run identity/authority 均已有各自范围内的 evidence-bounded freeze；P-1 prerequisite authority 与 legacy Task 9 application contract 仅有 document-only PASS；Task 9 authority adjudication 的历史 `BLOCKED` 与 upstream reconcile 的历史 `REVISE` 必须保留，但不得覆盖后续 owner 文件中更晚且更具体的 PASS/freeze。

本轮六条精确 pytest 命令全部退出 0，且 F09 全量为 1172 passed。该行为账本支持已测 F09 行为、production-entry isolation 和 current-run authority 路径，但不单独授权 Task 9-P total Gate。

现有 [`production-implementation-control.md`](production-implementation-control.md) 的 G6–G9 记录明确只覆盖已列明的 F09 行为与隔离证据，审计开始时没有一份持久化记录机械映射“九个专项单元 → Task 9-P total Gate → G6 governance roll-up”。因此：

1. 未发现仍未满足的材料性前置依赖，不裁决为 `BLOCKED`；
2. 审计开始时缺少 durable traceability record，不裁决为 `PASS`；
3. 唯一合法裁决为 **`REVISE — TRACEABILITY RECORD REQUIRED`**；
4. 本文件是对缺失追溯记录的有界补正，不得循环地作为审计开始时已经存在的 PASS 证据；
5. 完成本文件和总控的有限链接更新后，Task 9-P 仍须由新鲜独立复核决定是否可升级为 `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`。

## 2. 权威性与 supersession 规则

本裁决按以下规则读取证据：

1. 每个专项单元只采用其 owner 文件最后明确有效的 fresh review、adjudication 或 freeze 章节作为当前状态；
2. 所有历史 RED、失败、`BLOCKED` 与 `REVISE` 均保留为审计轨迹；
3. 后续明确 PASS/freeze 可以 supersede 同一 owner 链上的旧状态，但不得删除旧证据；
4. 局部 PASS/freeze 不得外推为 Task 9-P total Gate 或 G6 governance roll-up；
5. document-only PASS 不得外推为 implementation authorization、runtime conformance 或 production readiness；
6. 行为/测试证据与合同/治理证据分账；两者均不能替代另一方；
7. 非继承授权：任何 unit 的授权不得自动传递给下游 unit 或 total Gate。

## 3. 九单元机械可审计矩阵

| # | 专项单元 | 权威文件与最后有效章节 | 最终状态 | 直接证明 | 明确未证明 | 前置依赖 | Task 9-P 职责 | 足以进入 total Gate | 证据链接 |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | R40 preprod authority construction seam | §11 | `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE` | issuance-first；manifest verifier exactly once；restricted-context digest reconciliation；零 binder/learning | Task 9、P-2、Task 9-P、G6；部署与生产就绪 | R41 返回的实际 signed result carrier | 从实际 run artifact result 构造实际 preprod authority | **是，作为有界 prerequisite；否，不能单独关闭 total Gate** | [`g6-task8-r40-preprod-authority-construction-seam-contract.md`](g6-task8-r40-preprod-authority-construction-seam-contract.md) |
| 2 | R41 run target-ref capture/provisioning seam | §21 | `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE` | signed result carrier；key/manifest/ref closure；registry/signer fail closed；add-only rotation | Task 9、P-2、Task 9-P、G6；R40 内部语义 | versioned request 与 target refs authority | 产出交给 R40 的实际、签名、可验证 current-run carrier | **是，作为有界 prerequisite；否，不能单独关闭 total Gate** | [`g6-task8-r41-run-target-ref-capture-provisioning-seam-contract.md`](g6-task8-r41-run-target-ref-capture-provisioning-seam-contract.md) |
| 3 | R42 feedback-owner revalidation/call-count amendment | §10 | `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE` | feedback restricted-context revalidation；exact exception propagation；downstream zero-call；历史动态 113 passed | R40、R41、Task 9、P-2、Task 9-P、G6 | 既有 feedback owner 与 authority/manifest context | 固定 feedback-owner revalidation 和调用次数边界 | **是，作为 feedback-side 有界 prerequisite；否，不能单独关闭 total Gate** | [`g6-task8-r42-feedback-owner-revalidation-call-count-contract.md`](g6-task8-r42-feedback-owner-revalidation-call-count-contract.md) |
| 4 | Legacy Task 9 application orchestrator contract | §12 | document-only CONTRACT `PASS`；implementation authorization=`NO` | legacy result、STOP、closed write set、legacy isolation 的合同边界 | versioned producer runtime、current-run authority、Task 9-P、G6 | 冻结 legacy application contract | 提供 versioned producer 必须保持的 legacy-first 与 compatibility baseline | **条件性是：仅作合同基线；不是 runtime admission 或 total closure** | [`g6-task9-application-orchestrator-contract.md`](g6-task9-application-orchestrator-contract.md) |
| 5 | Task 9 authority adjudication | §11 | 历史 `BLOCKED` prerequisite finding；保留，不作当前 owner-final verdict | 记录当时缺失 statement-set-dependent projection/key owner 与 current-run feedback authority owner | 后续 owner 工作是否实现、P-2 是否冻结、Task 9-P 是否关闭 | 当时的 P-1/P-2 authority gaps | 提供必须由后续 R40/R41/Task 9/P-1/P-2 证据逐项解除的历史 blocker ledger | **是，作为历史反证与解除检查；否，不能以自身 `BLOCKED` 覆盖后续 owner freeze，也不能授权 total Gate** | [`g6-task9-authority-adjudication.md`](g6-task9-authority-adjudication.md) |
| 6 | Task 9 versioned producer/envelope | §9.9 | `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`；supersede 早期多轮 `REVISE` | legacy-first；legacy result identity；STAGED pre-R41 exit；V5/V6 R41→R40 actual-object handoff；owner failure propagation；零 binder/eligibility/learning | P-2、Task 9-P、G6；R41 crypto/graph 与 R40 内部语义 | R40 + R41 + legacy Task 9 baseline | 把 versioned producer 的实际 result/authority 放入 immutable execution envelope | **是，作为直接 producer prerequisite；否，§9.9 明确不关闭 P-2/Task 9-P/G6** | [`g6-task9-versioned-producer-envelope-contract.md`](g6-task9-versioned-producer-envelope-contract.md) |
| 7 | P-1 prerequisite artifact-operation authority | §8 | document-only `PASS`；P-2 与 Task 9-P 的历史状态不作当前最终状态 | artifact projections + `IdempotencyKey` 的 authority contract；fresh logical rereview 已通过 | P-1 implementation、run-artifact authority、P-2、Task 9-P、Task 9 implementation、G6 | normalized package、decision、trace、statement set 与两类 contract refs | 固定 artifact construction authority，防止与 current-run authority/key 混用 | **条件性是：合同 prerequisite 已满足；否，不能冒充实现或 total closure** | [`g6-task9p-prerequisite-authority-contract.md`](g6-task9p-prerequisite-authority-contract.md) |
| 8 | P-2 current-run identity/authority | Appendix C §C.18 | `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`；supersede §§1–11、Appendix A/B 的旧 blocker | Task 9 → R41 actual carrier identity → R40 actual authority identity → immutable envelope；legacy stops；STAGED short-circuit；mismatch/cross-key rejection；owner exception identity | R41 crypto/graph、R40 internals、Task 9-P、G6、生产就绪 | R41 + R40 + Task 9 versioned producer；P-1 类型/authority separation | 完成 current-run identity/authority admission 与实际对象 identity handoff | **是，作为 Task 9-P 的直接 runtime prerequisite；否，C.18 明确不关闭 Task 9-P/G6** | [`g6-task9p-p2-current-run-identity-authority-adjudication.md`](g6-task9p-p2-current-run-identity-authority-adjudication.md) |
| 9 | P-2 upstream contract reconcile | §18.3 | 第十轮 document-only fresh review `PASS`；早期 `REVISE` 保留 | canonical role order 修正为 `RUN_SNAPSHOT, DECISION_RUN[, FEEDBACK_ATTACHMENT]`；局部 upstream 文本一致性 | P-1 当前 owner-final 状态、任何 implementation、feedback admission、Task 9-P、G6、全仓正确性 | P-1/Task 9/P-2 文档链 | 消除 upstream contract 文本冲突并记录局部 reconcile | **条件性是：作为文本一致性证据；否，不能覆盖各 owner 最新状态或关闭 total Gate** | [`g6-task9p-p2-upstream-contract-reconcile-adjudication.md`](g6-task9p-p2-upstream-contract-reconcile-adjudication.md) |

### 3.1 矩阵结论

- 九行均可进入 total-Gate 审计，但进入含义分别是“有界 prerequisite”“合同基线”“历史反证”或“局部 reconcile”，不是九个独立 PASS 的简单相加。
- 五个行为/实现冻结单元：R40、R41、R42、Task 9 versioned producer/envelope、P-2 current-run identity/authority。
- 两个 document-only PASS 单元：legacy Task 9 application contract、P-1 prerequisite authority。
- 一个历史 blocker ledger：Task 9 authority adjudication。
- 一个局部 document-only reconcile PASS：P-2 upstream contract reconcile。
- 不存在任何单行可以独立推出 Task 9-P total Gate 或 G6 governance roll-up。

## 4. 依赖链复核

本轮验证的依赖链为：

```text
R40 + R41 + R42
  → Task 9 versioned producer/envelope
    → P-2 current-run identity/authority
      → Task 9-P total Gate
        → G6 governance roll-up
```

补充的横向约束为：

```text
legacy Task 9 application contract
  → legacy-first / compatibility baseline

P-1 prerequisite authority contract
  → artifact-operation authority 与 current-run authority/key 分离

Task 9 authority adjudication
  → 历史缺口 ledger 与解除检查

P-2 upstream reconcile
  → 文本 role-order 与 owner-state reconcile
```

依赖复核结果：

1. **R41 → R40**：R41 产出 actual signed result carrier；R40 消费 actual result 构造 actual preprod authority。
2. **R40/R41 → Task 9**：Task 9 versioned producer 在 V5/V6 分支按 R41 后 R40 顺序执行 actual-object handoff；STAGED 在 R41 前 fail closed。
3. **Task 9 → P-2**：P-2 Appendix C 以 actual carrier identity 与 actual authority identity 进入 immutable envelope，并覆盖 mismatch、cross-key 与 owner exception identity。
4. **R42 横向进入 Task 9-P**：R42 关闭 feedback-owner revalidation/call-count 边界，但不替代 P-2 current-run authority。
5. **P-1 横向进入 Task 9-P**：P-1 只关闭 artifact-operation authority 的 document contract，且必须与 `RunArtifactSetKeyV1`、current-run authority 分离。
6. **Task 9-P → G6**：审计开始时缺少机械可审计的 durable roll-up；这是本裁决的唯一 traceability gap。
7. 未发现循环依赖；未发现仍需实现或修复代码才能解除的材料性 prerequisite。

## 5. Fresh VERIFY 命令账本

执行顺序固定如下；无 rerun、无自动修复、无 collection error。工作目录均为 `f:/多流派新思路`。

| # | 精确命令 | Exit | passed | failed | errors | skipped | 耗时 | 证据含义 |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | `python -m pytest tests/f09/test_feedback_eligibility.py -q` | 0 | 117 | 0 | 0 | 0 | 12.64s | feedback eligibility/revalidation 当前行为 |
| 2 | `python -m pytest tests/f09/test_artifact_lifecycle.py -q` | 0 | 217 | 0 | 0 | 0 | 7.17s | artifact lifecycle 当前行为 |
| 3 | `python -m pytest tests/f09/test_feedback_eligibility.py tests/f09/test_artifact_lifecycle.py -q` | 0 | 334 | 0 | 0 | 0 | 18.88s | 精确闭合：117 + 217 = 334 |
| 4 | `python -m pytest tests/f09/test_application_opt_in.py tests/f09/test_production_isolation.py -q` | 0 | 30 | 0 | 0 | 0 | 1.23s | application opt-in 与 production-entry isolation |
| 5 | `python -m pytest tests/f09/test_current_run_authority.py -q` | 0 | 16 | 0 | 0 | 0 | 0.11s | P-2 current-run authority focused behavior |
| 6 | `python -m pytest tests/f09 -q` | 0 | 1172 | 0 | 0 | 0 | 76.70s | F09 当前全量 regression |

### 5.1 VERIFY 直接证明

上述 fresh ledger 直接证明：

- 六条指定命令均正常 collection、正常执行并退出 0；
- 当前 F09 全量为 1172 passed；
- feedback eligibility 与 artifact lifecycle 单独计数及组合计数机械闭合；
- application opt-in、production isolation 与 current-run authority 的指定 selector 当前通过；
- 没有因失败而触发停止闭合写入条件。

### 5.2 VERIFY 不得推导

上述 fresh ledger不证明：

- 九份专项文件的 governance authority 自动合并；
- Task 9-P total Gate 已有 durable authorization record；
- G6 governance roll-up 已在审计开始时闭合；
- 全仓 100% 绿或全仓正确性；
- 未执行测试、skipped 场景或环境外行为；
- 部署、发布、生产可用性或 production readiness；
- Git provenance、提交完整性、远程同步或任何 GitHub 状态。

## 6. 六项 EVIDENCE REVIEW 门禁

| 门禁 | 独立结论 | 理由 |
|---|---|---|
| 1. 九单元最后有效状态是否可机械确定 | `PASS` | 每个 owner 文件均有可识别的最后有效章节；历史状态按 supersession 保留 |
| 2. 依赖链是否非循环且 owner 职责闭合 | `PASS` | R41→R40→Task 9→P-2 为 actual-object handoff；R42/P-1/legacy/reconcile 为横向约束 |
| 3. 历史 material blockers 是否有后续 owner 证据解除 | `PASS WITH BOUNDARIES` | 旧 Task 9/P-2 blockers 已由更晚 owner freezes 或 contract PASS 逐项覆盖；document-only 部分仍不得解释为实现 |
| 4. Fresh behavior evidence 是否通过且与治理证据分账 | `PASS` | 六条命令 exit 0；1172 F09 passed；不以测试代替治理授权 |
| 5. 审计开始时是否已有 Task 9-P total-Gate durable roll-up | `FAIL — TRACEABILITY ONLY` | 总控 §8.1 明确只覆盖 F09 行为与隔离；无九单元机械映射与 total-Gate authorization record |
| 6. 缺口是否达到 material block | `NO` | 未发现新的代码、测试、authority owner、identity handoff 或前置实现缺失；最小补正是持久化 adjudication 与有限总控链接后进行 fresh review |

## 7. Task 9-P 直接证明

本轮证据组合可以直接证明：

1. 九个专项单元均已被纳入同一份 owner-aware、supersession-aware 的矩阵；
2. R40/R41/R42、Task 9 versioned producer/envelope、P-2 current-run identity/authority 的各自 evidence-bounded freeze 可被追溯；
3. legacy Task 9 与 P-1 的 document-only 性质已显式隔离，不再被误标为 runtime freeze；
4. Task 9 authority adjudication 的历史 `BLOCKED` 和 upstream reconcile 的历史 `REVISE` 均被保留；
5. `IdempotencyKey` 与 `RunArtifactSetKeyV1`、artifact-operation authority 与 current-run authority 的职责没有被合并；
6. actual R41 carrier → actual R40 authority → immutable Task 9 envelope → P-2 identity admission 的路径可追溯；
7. fresh behavior ledger 与治理矩阵已分账；
8. 审计时点唯一缺口被准确界定为 total-Gate durable traceability record，而非材料性实现缺口。

## 8. 明确 non-inference boundaries

本裁决不得用于推导：

- `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`；
- Task 9-P 已在审计开始时完成；
- G6 的既有 `COMPLETED` 自动包含本次九单元 governance roll-up；
- 任一 unit freeze 自动继承给另一 unit、Task 9-P 或 G6；
- document-only CONTRACT PASS 等于 implementation authorization 或 runtime conformance；
- F09 1172 passed 等于九合同 total-Gate PASS；
- F09 行为/隔离收口等于全仓正确性或生产就绪；
- P-1 artifact-operation authority 等于 P-2 current-run authority；
- `IdempotencyKey` 等于 `RunArtifactSetKeyV1`；
- `PROJECT_ARTIFACT_SET` 与 `PROJECT_RUN_ARTIFACT_SET` 可以混用；
- opaque sentinel identity 等于合法 production carrier；
- R41 crypto/graph、R40 internals 或 R42 之外的 feedback semantics 被 P-2 重验；
- F08 runtime、十二卡全量实现、YAML/mapping 可执行性已被证明；
- 全仓 100% 绿、部署、发布、生产可用性、Git provenance 或 GitHub 同步。

## 9. 唯一裁决与最小下一合法动作

### 9.1 唯一裁决

**`REVISE — TRACEABILITY RECORD REQUIRED`**

该裁决属于 governance traceability revision，不是 runtime/code revision，也不是 material prerequisite block。

### 9.2 最小下一合法动作

1. 在 [`production-implementation-control.md`](production-implementation-control.md) 的 G6–G9 有界收口区追加一个精确、有限的 Task 9-P governance roll-up 小节；
2. 只链接本文件、记录本轮六条命令和 `REVISE` 边界，不改写既有 G6–G9 行为结论，不声称全仓绿；
3. 完成链接后进行新鲜独立复读，确认九行矩阵、supersession、命令账本、唯一 verdict 与 non-inference boundaries 一致；
4. 只有后续独立 evidence review 才能决定是否另行升级为 `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`；本文件不得自我升级。

## 10. 写集与操作边界

本轮允许写集仅为：

- 新建本文件；
- 有限更新 [`production-implementation-control.md`](production-implementation-control.md)。

本轮未授权且不得修改：

- [`../engine/f09/`](../engine/f09/)；
- [`../tests/f09/`](../tests/f09/)；
- 上表九份冻结专项文件；
- 任何其他 runtime、tests、contracts、metadata 或 handoff 文件。

操作状态：**`LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION`**。
