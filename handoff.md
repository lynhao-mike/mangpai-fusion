# HANDOFF · F01–F12 生产实现设计

## 0. 2026-08-07 · As-of Blind Bundle First Proof Point 收口

As-of blind-bundle First Proof Point active unit 已完成 CONTRACT → IMPLEMENT → STATIC_REVIEW → VERIFY → EVIDENCE_REVIEW → FREEZE，最终为 **evidence-bounded PASS**。冻结报告见 [`reports/as-of-blind-bundle-first-proof-point-report-2026-08-07.md`](reports/as-of-blind-bundle-first-proof-point-report-2026-08-07.md)，权威合同见 [`plans/as-of-blind-bundle-first-proof-point-contract-2026-08-07.md`](plans/as-of-blind-bundle-first-proof-point-contract-2026-08-07.md)。

冻结动态证据：两个 exact 31-instance selectors 均为 `31 passed`；三个 exact as-of compatibility nodes 为 `3 passed`；六个 exact prospective consumer compatibility nodes 为 `6 passed`。历史 `24 failed / 7 passed` 与 `1 failed / 30 passed` 已保留在冻结报告中，最终由根因修复后的同 selector PASS 取代当前 Gate 结论。

本结论只覆盖测试内合成、trusted-root 临时根、fundamentals=1/events=1 的单事件 bundle→freeze→release→verify 纵切。它不证明真实案例、two-event、全局多故障优先级、命理准确率、全套测试、全仓正确性、全部隐藏 consumer、部署、发布、routing 或 production switch。

Deferred A（two-event）、Deferred B（真实案例 closed request provenance/locator/full smoke）与 Deferred C（多故障组合优先级）继续 inactive，不能自动继承当前授权。任何后续实现、读取受保护事实、额外测试、本地 Git 或远端动作都需要新的独立明确授权；GitHub 服务端变更永久禁止。

当前唯一合法状态是 **HANDOFF complete / STOP**；不得从本交接自动启动 deferred unit 或生产切换。

---

> 更新时间：2026-07-21（Asia/Shanghai）
>
> 本文件是新会话的短期入口，只保留当前阶段、事实源、硬边界、总控入口和启动提示词。动态任务状态统一维护在 [`plans/production-implementation-control.md`](plans/production-implementation-control.md)，不得在本文件重复维护。

## 1. 当前结论

F01–F12“事业功能—现实落点词典”的理论冻结与正式归档已经结束：

- 正式 Markdown 契约：[`engine/contracts/12-real-world-function-evidence-cards-v1.md`](engine/contracts/12-real-world-function-evidence-cards-v1.md)；
- 机器可读附录：[`mapping/real-world-function-evidence-cards-v1.yaml`](mapping/real-world-function-evidence-cards-v1.yaml)，仍是声明性附录，不得作为可执行逻辑；
- F01–F12 冻结定义不得重开；新证据或业务变化必须走正式契约变更流程。

历史 handoff 的 G1 PASS 声明曾因治理证据不足被 PI-195 fail closed；用户选择阻断包 Option A 后，G1 已通过独立验收并 `COMPLETED`。G2 经 PI-290-R3 独立复验 **PASS**；G3 的 F09 一卡切片经 PI-390-R4 独立复验 **PASS**；G4 经 PI-400-R4 技术复评 **PASS** 且用户于 2026-07-20 明确指令“以子任务完成G5”后 `COMPLETED`。G5 经 PI-570-R1 至 R25 的有界计划整改、角色分离复验及父实例直接证据核验收口；最终 PI-590-R25 独立静态裁决 **PASS**，High=0、Medium=0、critical ambiguity=0、material evidence gap=0、mechanical-copyability gap=0、authority conflict=0、regression=0，父实例已直接接受。`PI-500=COMPLETED`、`G5=COMPLETED`，证据见 [`plans/production-implementation-pi-500-r1-f09-implementation-plan.md`](plans/production-implementation-pi-500-r1-f09-implementation-plan.md) 的 PI-590-R25 review/parent closeout 与 [`plans/production-implementation-control.md`](plans/production-implementation-control.md)。

G6 已在独立授权下启动，但尚未完成。F09 Task 1 已严格创建 [`engine/f09/errors.py`](engine/f09/errors.py)、[`engine/f09/contracts.py`](engine/f09/contracts.py)、[`tests/f09/__init__.py`](tests/f09/__init__.py)、[`tests/f09/conftest.py`](tests/f09/conftest.py) 与 [`tests/f09/test_evidence_contract.py`](tests/f09/test_evidence_contract.py)；父实例已直接检查实际内容，新鲜独立静态实现审查 **PASS**（High=0、Medium=0）。精确动态验证结果为 focused selector `47 passed in 0.13s`，两个指定 production-default 回归 selector `2 passed, 1 warning in 1.04s`，两次退出码均为 0；新鲜独立证据审查 **PASS**（High=0、Medium=0），父实例接受 **Task 1 evidence-bounded freeze**。

F09 Task 2 已按冻结合同创建 [`engine/f09/canonical_json.py`](engine/f09/canonical_json.py) 与 [`tests/f09/test_canonical_json.py`](tests/f09/test_canonical_json.py)。新鲜独立 STATIC_REVIEW 为 **PASS**（High=0、Medium=0、Low=0），确认 exact two-path scope、continuous literal implementation block 与静态 46-instance ledger。随后独立 VERIFY 在仓库根目录各执行一次获授权命令：focused [`tests/f09/test_canonical_json.py`](tests/f09/test_canonical_json.py) 为 `46 passed in 0.27s`、退出码 0；指定 regression selectors 合计 `6 passed, 1 warning in 1.84s`、退出码 0。无失败、collection error、重跑或修复。Task 2 当前唯一 Gate 状态是 **VERIFY PASS — EVIDENCE_REVIEW AUTHORIZATION REQUIRED**；尚未进行独立 EVIDENCE_REVIEW 或父级 evidence-bounded freeze。

Task 1 freeze 只覆盖其五路径的静态机械一致性和已记录 selector；Task 2 VERIFY PASS 只覆盖本次获授权的 46 个 focused instances 与 6 个 regression instances。二者均不证明全套测试、全仓正确性、Git provenance、YAML/mapping 或 F08 运行行为、production entrypoint 的完整动态不变性、G6 完成、G7–G9、部署、GitHub 同步或生产就绪。本受控流程没有执行本地 Git 或 GitHub 服务端操作。

## 2. 当前阶段

总控状态、阶段门、任务依赖和递归子任务协议仍以 [`plans/production-implementation-control.md`](plans/production-implementation-control.md) 为准；本文件只交接 G1–G5 已完成的治理结论、G6 Task 1 的 evidence-bounded freeze、Task 2 的 VERIFY PASS，以及后续非继承授权边界。当前“大长任务”是完整 **G6 — F09 最小生产切片实现**：按批准的 [`PI-500 Task 1–Task 10`](plans/production-implementation-pi-500-r1-f09-implementation-plan.md) 逐个完成角色分离的 IMPLEMENT、STATIC_REVIEW、VERIFY、EVIDENCE_REVIEW 与父级 evidence-bounded freeze，而不是把单个 Task 内的某个 Gate 当作大长任务。

G1 核心发现：

- `questions` 可摄入，但未证明被 staged 分析消费；系统没有统一外部时间范围；
- `known_facts` 仅有带年份事件子集进入 D3；
- 五动作没有统一运行时协议，且 `ASK` 缺失；F01–F12 尚无运行时模型；
- statement / feedback 基础设施只能部分复用；
- 生产默认链与 staged / preprod 链必须分账。

用户已经授权并完成第二轮 Option A：PI-210 正式定义 `mdff:v1` Markdown frozen-field locator/resolver 与 discriminated `SourceBinding`，实际 immutable source snapshot fixture 已在 `plans/` 下建立并被 PI-400-R4 独立机械验证。用户随后明确授权以子任务完成 G5；PI-590-R25 独立 PASS 已由父实例直接接受，G5 实现计划治理已经收口。此后 Task 1 经逐次独立授权完成实现、父级检查、独立静态审查、精确动态验证、独立证据审查与 evidence-bounded freeze；Task 2 已完成获授权的 IMPLEMENT、独立 STATIC_REVIEW 与独立 VERIFY。当前必须停止自动推进：Task 2 的 EVIDENCE_REVIEW 与父级 freeze 尚未授权，Task 3–Task 10 的任何权限也不得继承；后续读取、修改、测试、production-default 变更、local Git 或远端动作均需新的精确授权。

## 3. 必读事实源

新会话按以下顺序读取：

1. [`README.md`](README.md)
2. [`AGENTS.md`](AGENTS.md)
3. [`META/project-state.json`](META/project-state.json)
4. [`STATUS.md`](STATUS.md)
5. [`tools/README.md`](tools/README.md)
6. [`engine/README.md`](engine/README.md)
7. [`engine/contracts/00-OVERVIEW.md`](engine/contracts/00-OVERVIEW.md)
8. [`engine/contracts/12-real-world-function-evidence-cards-v1.md`](engine/contracts/12-real-world-function-evidence-cards-v1.md)
9. [`mapping/real-world-function-evidence-cards-v1.yaml`](mapping/real-world-function-evidence-cards-v1.yaml)
10. [`plans/production-implementation-control.md`](plans/production-implementation-control.md)
11. [`handoff.md`](handoff.md)

事实源职责：

- 产品版本以 [`VERSION`](VERSION) 为准；
- 当前项目状态以 [`META/project-state.json`](META/project-state.json) 为准；
- F01–F12 冻结业务语义以正式契约为准；
- 机器结构以机器附录及其 schema 为准；
- 生产实现设计任务状态只以总控表为准；
- 本文件不作为产品版本、规则数量、运行状态或冻结业务字段的事实源。

## 4. 生产实现设计硬边界

1. 不重开 F01–F12 定义、必要门、竞争边界、根源、时序和有限现实落点。
2. 不把 [`mapping/real-world-function-evidence-cards-v1.yaml`](mapping/real-world-function-evidence-cards-v1.yaml) 改成可执行 if/else、表达式或优先级算法。
3. `null` 和 `unresolved_fields` 必须原样保留语义，不得静默套用默认值。
4. `validation_timepoints` 与 `output_precision` 分账。
5. 命理结构轨、现实事实轨和未核验假设轨分账；未核验事件不得污染事实快照。
6. 五动作 `OUTPUT`、`CONDITIONAL`、`ASK`、`ABSTAIN`、`HUMAN_REVIEW` 必须失败安全；证据链不完整时不得为目录完整强行输出。
7. 用户已授权并完成 G2 → G3 → G4 → G5 计划治理，并以独立授权完成 G6 Task 1 的 evidence-bounded freeze；Task 2 当前仅到 VERIFY PASS。这不授权 Task 2 的 EVIDENCE_REVIEW/freeze、Task 3–Task 10、冻结语义变更、生产默认行为变更、额外测试或远端操作，最小切片不得扩成十二卡。
8. 每个设计判断必须有现有文件、符号或调用链证据；普通证据缺口自动追加只读调查，不得从文件名和旧摘要推断系统能力。
9. 不涉及冻结语义、生产代码和生产默认行为的设计分歧可由自动化裁决；若必须修改冻结语义、生产代码或无法保持默认行为，必须 fail closed，输出阻断／决策包并停止。
10. 生产默认链与 staged / preprod 链必须分账；本轮不得修改生产或数据文件。
11. G2、G3、G4、G5 均已按各自门禁完成；历史用户批准硬门与角色分离验收不可被后续会话重判或省略。
12. G5 完成只证明实现计划通过独立静态验收及父实例接受；Task 1 freeze 与 Task 2 VERIFY PASS 各自只证明其精确边界内的有界证据，不得据此自动启动后续 Gate、Task 3、部署或任何 Git/GitHub 操作。

## 5. 递归子任务纪律

详细协议见 [`plans/production-implementation-control.md`](plans/production-implementation-control.md)。新会话必须遵守以下最小纪律：

- 主会话负责拆分、派发、汇总、裁决、更新总控和组织独立阶段验收；
- 子任务默认只读；写任务必须精确列出允许修改文件；
- 最大递归深度为 3 层；第三级不得继续拆分；
- 同一文件同一时刻只允许一个写任务；
- 调查任务不得顺手修复，验收任务不得自行修复；
- 子任务必须继承父任务 ID、事实源、禁止事项、完成条件和回报格式；
- 证据不足、任务冲突或需要扩大范围时，返回父任务裁决；普通证据缺口优先派发只读调查；
- 父任务必须抽查并核验关键证据，不得只凭子任务摘要宣布完成；
- 阶段门只能由独立验收节点 PASS，不得由设计／整改任务自验通过；
- G6 的每次写范围必须来自当前 Task 的独立、精确、非继承授权；没有该授权时禁止修改任何路径。fixture、mapping/YAML、状态文件与 handoff 默认只读或禁止写，除非用户另行明确授权 exact path 与用途。

## 6. 新会话启动提示词

```text
你正在 mangpai-fusion 仓库承接“大长任务：G6 — F09 最小生产切片实现”。先按仓库规定顺序读取事实源，并以 plans/production-implementation-control.md 为动态任务状态唯一事实源，以 plans/production-implementation-pi-500-r1-f09-implementation-plan.md 为 Task 1–Task 10 的冻结实施合同。

G1、G2、G3、G4、G5 均已完成治理收口。G5 的最终证据是 PI-590-R25 角色分离独立静态 PASS 及父实例直接接受；PI-500=COMPLETED、G5=COMPLETED。不要重复或重判既有 Gate，也不要从旧计划或历史 BLOCKED 记录推断当前状态。

G6 已启动但未完成。Task 1 已完成角色分离的实现、静态审查、精确验证、证据审查，并被父实例接受为 evidence-bounded freeze。

Task 2 已创建 engine/f09/canonical_json.py 与 tests/f09/test_canonical_json.py；新鲜独立 STATIC_REVIEW PASS（High=0、Medium=0、Low=0）。独立 VERIFY 各执行一次冻结命令：focused 46 passed in 0.27s、exit 0；regression 6 passed, 1 warning in 1.84s、exit 0；无失败、collection error、修复或重跑。Task 2 当前唯一状态是 VERIFY PASS — EVIDENCE_REVIEW AUTHORIZATION REQUIRED，尚未进行 EVIDENCE_REVIEW 或父级 evidence-bounded freeze。

你的编排对象是完整 G6：Task 2 收口后继续 Task 3–Task 10，直至每个 Task 都完成独立 IMPLEMENT、STATIC_REVIEW、VERIFY、EVIDENCE_REVIEW 与父级 evidence-bounded freeze。但长期任务授权不等于跨 Gate 授权；每个角色、读取、exact-path 修改、完整命令、测试、状态写入和 local Git 权限均默认拒绝、独立且不可继承。

唯一下一合法动作：请求并取得 Task 2 独立 EVIDENCE_REVIEW 的精确只读授权。EVIDENCE_REVIEW PASS 后仍须单独取得父级 freeze 授权；不得自动进入 Task 3。随后对 Task 3–Task 10 逐个按冻结合同与角色分离流程推进。

完成边界：Task 1 freeze 与 Task 2 VERIFY PASS 均不证明全套测试、全仓正确性、Git provenance、YAML/mapping、F08 runtime、G6 完成、G7–G9、生产就绪、部署或 GitHub 同步。

停止边界：没有新的明确授权时，不得读取新 Task 正文、继续 Gate、实现、验证、修复或重跑；不得执行声明性 mapping/YAML；不得改变 production-default；不得扩展 F09 范围；F08 仅 identity/reference-only。任何本地 Git 操作都需独立 exact authorization；GitHub 服务端写操作永久禁止。
```

---

## 7. 2026-07-23 · G6 Task 9-P 第 16 节只读审查交接

> **持久化范围：** 本条仅交接本会话对 [`plans/g6-task9p-p2-upstream-contract-reconcile-adjudication.md`](plans/g6-task9p-p2-upstream-contract-reconcile-adjudication.md) 第 16 节的只读独立审查。动态项目状态仍以 [`plans/production-implementation-control.md`](plans/production-implementation-control.md) 与相关 prerequisite/reconcile 合同为准；本条不覆盖既有 G6 Task 1/Task 2 交接结论。

### 当前状态与直接证据

- 已完成：RECOVER、INVENTORY、ADMISSION、CONTRACT，以及第 16 节逻辑新鲜的只读 STATIC_REVIEW。
- 审查 verdict：`REVISE`。P-1 保持 `REVISE`；P-2 与 Task 9-P 保持 `BLOCKED`；Task 9 amendment 保持 `STILL_OPEN`；implementation 未获授权。
- 直接观察：第 15.2 将 future run key 表述为扩展 legacy [`IdempotencyKey`](engine/f09/artifacts.py) 的 `PROJECT_RUN_ARTIFACT_SET` shape；第 16.1 则规定独立 versioned `RunArtifactSetKeyV1`，并要求 legacy `IdempotencyKey` 的 statement semantics byte-for-byte 不变且禁止两类 key 互换或隐式转换。
- 审查发现：第 16 节仅覆盖第 15.2 中不一致或不完整的 run-key preimage 表述，未明确撤销第 15.2 对 legacy key 类型/字段的扩展方案；故 future implementer 仍可能选择两种互斥 schema carrier，H-02 不能冻结。
- 交叉核对：当前 [`engine/f09/artifacts.py`](engine/f09/artifacts.py) 的 `IdempotencyKey` 不含 `PROJECT_RUN_ARTIFACT_SET`、`run_id` 或 refs-graph fields；当前 statement writer 为 records 固定 `run_id=None`。这只证明第 16 节是 future contract，不证明 runtime support。
- 未执行：未修改 production/tests；未运行 Python、pytest、Git 或 GitHub 操作；本受控会话未执行 GitHub-mutating operation。

### 唯一下一合法动作

仅对 [`plans/g6-task9p-p2-upstream-contract-reconcile-adjudication.md`](plans/g6-task9p-p2-upstream-contract-reconcile-adjudication.md) 进行最小 document-only reconcile，明确第 15.2 关于扩展 legacy `IdempotencyKey`、legacy-field preimage 及同 carrier 方案的条款，全部由第 16 节的独立 `RunArtifactSetKeyV1` carrier 方案替代；同时明确 future run-verifier path 的 [`ArtifactSetManifest`](engine/f09/artifacts.py) key-carrier typing/validation boundary。修订后必须由新鲜独立 reviewer 只读复审。

### 禁止推导与非扩张边界

- 本交接不授权修改 [`engine/f09/artifacts.py`](engine/f09/artifacts.py)、[`engine/f09/feedback.py`](engine/f09/feedback.py) 或任何测试。
- 不得将 `RunArtifactSetKeyV1`、`validate_run_artifact_manifest_v1()` 或 `coordinate_run_artifact_set_v1()` 视为现有 runtime API。
- 不得启动 P-1 implementation、feedback adapter、P-2 upstream producer authority、Task 9 application/versioned envelope、Python、pytest、Git 或 GitHub 操作。
- document-only revision 或 subsequent review PASS 不等于 P-1/P-2/Task 9 implementation authorization。

### 新会话启动提示词

```text
继续 G6 / Task 9-P 长任务。先遵循 AGENTS.md 的事实源顺序，并读取 handoff.md 第 7 节及 plans/g6-task9p-p2-upstream-contract-reconcile-adjudication.md 第 15.2、16.1–16.2。

已完成第 16 节只读独立 STATIC_REVIEW，verdict 为 REVISE。唯一发现是 schema-carrier conflict：第 15.2 仍将 PROJECT_RUN_ARTIFACT_SET 描述为扩展 legacy IdempotencyKey 的方案，而第 16.1 规定独立 RunArtifactSetKeyV1 并冻结 legacy IdempotencyKey byte-for-byte 不变；第 16 节尚未明确完整覆盖第 15.2 的 legacy key type/field extension。

本轮唯一授权：仅修改 plans/g6-task9p-p2-upstream-contract-reconcile-adjudication.md，进行最小 document-only reconcile，明确第 15.2 的 legacy IdempotencyKey extension / legacy-field preimage / same-carrier run-key 表述均由第 16 节独立 RunArtifactSetKeyV1 carrier 完整替代，并明确 ArtifactSetManifest 在 future run-verifier path 的 key-carrier typing/validation boundary。禁止修改任何 production/tests/状态文件；禁止运行 Python、pytest、Git 或 GitHub；禁止启动任何 implementation。

修订完成后停止 implementation，并启动新的逻辑新鲜、只读独立审查。P-1 必须保持 REVISE；P-2 与 Task 9-P 必须保持 BLOCKED；Task 9 amendment 必须保持 STILL_OPEN。任何 document revision 或 review PASS 都不构成 implementation authorization。
```

---

## 8. 2026-07-24 · G6 Task 9-P P-2 current-run identity adjudication 交接

> **持久化范围：** 本条追加记录 P-2 producer-owned current-run identity authority 的只读裁决；历史第 7 节仅表示其当时的工作点，不覆盖本条。当前项目/任务状态仍以 [`META/project-state.json`](META/project-state.json)、[`plans/g6-task9p-prerequisite-authority-contract.md`](plans/g6-task9p-prerequisite-authority-contract.md) 与 P-2 现行附录为准。本条是恢复快照，不是 Gate 事实源或 implementation 授权。

### 当前状态与直接证据

- P-1 prerequisite authority contract：`PASS`，仅关闭 P-1 authority-contract Gate；不构成 P-1 implementation correctness、Task 9 amendment `PASS`、Task 9-P total Gate `PASS` 或 P-2 admission。
- R39 feedback adapter：已完成其独立 evidence-bounded freeze；仅证明已记录的 R39 范围，不产生 current Task 9 execution identity issuer。
- P-2 producer-owned current-run identity authority adjudication：`BLOCKED`；Task 9-P total Gate 继续 `BLOCKED`，Task 9 amendment 继续 `STILL_OPEN`。
- 直接观察：公开执行入口 [`run_f09_slice()`](engine/f09/application.py:135) 接收 caller-supplied [`F09RunRequest`](engine/f09/application.py:35)，并调用 legacy [`coordinate_artifact_operation()`](engine/f09/application.py:215)；当前未观察到 P-2 所要求的 versioned [`run_f09_slice_with_execution_authority_v1()`](engine/f09/application.py:135) 或 immutable `F09RunExecutionResultV1`。
- P-1 [`RunArtifactSetKeyV1`](engine/f09/artifacts.py:87)、[`coordinate_run_artifact_set_v1()`](engine/f09/artifacts.py:1745) 与 [`validate_run_artifact_manifest_v1()`](engine/f09/artifacts.py:1683) 可验证 supplied run graph 的 key/manifest/record integrity closure；其 request 仍接收 `run_id`、refs 与 projections，不能独立证明 graph 属于 current Task 9 invocation。
- R39 [`_validated_preprod_restricted_manifest_context()`](engine/f09/feedback.py:970) 会严格验证 [`PreprodRunAuthority`](engine/f09/feedback.py:191) 的 manifest、role 和 digest closure，但该 adapter 属 consumer admission，不能充当 current execution 的唯一 producer-owned identity issuer。
- 现行 P-2 范围与前置条件见 [`plans/g6-task9p-p2-current-run-identity-authority-adjudication.md`](plans/g6-task9p-p2-current-run-identity-authority-adjudication.md:461) 第 B.2–B.4 节：Task 9 versioned callable/envelope 与其 implementation/verification/freeze 未完成，P-2 admission 不得进入 `PASS`。

### 裁决边界与停止点

- 已完成的唯一合法动作：P-2 的只读 adjudication；未修改 production、tests 或任何 Task 9 主合同；未运行 Python、pytest、Git；本受控会话未执行 GitHub-mutating operation。
- 不得推导：P-1 `PASS`、R39 freeze、run-artifact manifest verifier 或 feedback adapter integrity check 均不等于 producer-owned current-run identity、P-2 admission `PASS`、Task 9-P total Gate `PASS`、全仓正确性或 GitHub 同步。
- 当前 blocker：缺少由当前 Task 9 execution 的唯一 owner 签发、以 P-1 lifecycle returned manifest 为来源、以 immutable versioned envelope 输出的 current-run identity authority；caller-held graph closure 不可替代该 provenance seam。
- P-2 继续 fail-closed：不得由 application、P-2 或 caller 签发/覆写 `run_id`，不得内存构造、重签、borrow、swap 或 relabel manifest/records/refs/authority，也不得以 consumer validation 反推 producer provenance。

### 唯一下一合法动作

在新会话进行最小只读 RECOVER：读取 [`AGENTS.md`](AGENTS.md)、[`META/project-state.json`](META/project-state.json)、[`plans/g6-task9p-prerequisite-authority-contract.md`](plans/g6-task9p-prerequisite-authority-contract.md)、[`plans/g6-task9p-p2-current-run-identity-authority-adjudication.md`](plans/g6-task9p-p2-current-run-identity-authority-adjudication.md) 的附录 B，以及本节；确认 P-2 `BLOCKED` 与上述 blocker 后停止。除非后续获得独立、精确的 Task 9 versioned producer/envelope contract authorization，否则不得启动 implementation、tests、Git 或任何 GitHub 服务端操作。

### 新会话启动提示词

```text
继续 G6 / Task 9-P 长任务，但首先只做 RECOVER，不启动 implementation、tests、Git 或 GitHub 操作。

按仓库事实源顺序读取 AGENTS.md、META/project-state.json；随后读取 plans/g6-task9p-prerequisite-authority-contract.md、plans/g6-task9p-p2-current-run-identity-authority-adjudication.md 的 Appendix B，以及 handoff.md 第 8 节。handoff 仅为恢复快照，不是 Gate 事实源。

已完成的最新裁决：P-1 prerequisite authority contract = PASS（只关闭 P-1 contract Gate）；R39 已 evidence-bounded freeze；P-2 producer-owned current-run identity authority = BLOCKED；Task 9-P total Gate = BLOCKED；Task 9 amendment = STILL_OPEN。

BLOCKED 的直接理由：当前公开 application 仅有 legacy run_f09_slice()/F09RunResult；不存在现行 P-2 所要求的 versioned run_f09_slice_with_execution_authority_v1() 与 immutable F09RunExecutionResultV1。P-1 RunArtifactSetKeyV1 / coordinate_run_artifact_set_v1 / validate_run_artifact_manifest_v1 只能验证 supplied graph integrity closure；它们不证明 graph 源于 current Task 9 invocation。R39 feedback adapter 是 consumer admission，不是 current-run identity issuer。

当前唯一合法动作：完成最小只读 RECOVER，确认上述 authoritative current state 与 blocker，然后停止。不要重开 P-1 或 R39；不得将 P-1 PASS、R39 freeze、manifest verifier 或 adapter validation 推导为 P-2 PASS。没有新的独立、精确 authorization 时，不得修改 production、tests、Task 9 主合同、状态文件或 handoff；不得运行 Python、pytest、Git；不得执行任何 GitHub 服务端 mutation。
```

---

## 9. 2026-07-24 · R42 single-verifier 完成与 G6 整体 RECOVER 交接

> **持久化范围：** 本节记录已获明确 implementation Gate 的 R42 最小修订及其验证证据，并把后续工作收束为一次只读 G6 全局恢复/阻塞盘点。本节不是 G6 完成声明、P-2 admission、Task 9-P total Gate 或任何后续实现授权；动态任务状态仍须以现行控制合同和各任务契约为准。

### 已完成的 R42 事实与验证证据

- R42 的唯一授权 write set 为 [`engine/f09/feedback.py`](engine/f09/feedback.py) 与 [`tests/f09/test_feedback_eligibility.py`](tests/f09/test_feedback_eligibility.py)。除此之外未在 R42 implementation Gate 下授权修改其他生产或测试路径。
- [`_revalidate_preprod_restricted_manifest_context()`](engine/f09/feedback.py) 已改为消费 builder 已保存的 `context.verifier_returned_records_digest`，不再重复调用 P-1 公共 [`validate_run_artifact_manifest_v1()`](engine/f09/artifacts.py)。其 exact type、authority/manifest object identity、key/track/case/run/roles、前三项 record join 和 `MANIFEST` outer-ref digest 的结构复验均保留。
- 新增聚焦回归 [`test_restricted_authority_material_invokes_public_manifest_verifier_once()`](tests/f09/test_feedback_eligibility.py)：先在旧实现下 RED，观察到有效 restricted self-excluded-material 路径调用 verifier 共 4 次；最小修订后 GREEN，断言该路径恰好 1 次。
- 最终工作区验证：`python -m pytest tests/f09/test_feedback_eligibility.py -q` → `111 passed in 13.13s`、exit 0。该证据仅覆盖此测试文件与 R42 目标行为，不证明全仓正确性、G6 完成、P-2 PASS、Task 9-P total Gate PASS、部署或 GitHub 同步。
- 当前仓库 Git 索引将上述两个 R42 目标文件显示为未跟踪，因此 `git diff` 不会展示其内容；这仅是本地索引观察，不构成 provenance、提交或同步结论。

### G6 整体问题的当前处理方向

G6 不能通过继续局部修补来声明收口。已知工作同时横跨早期 Task 1/Task 2 Gate 状态、R39/R42 feedback-owner consumer authority 路径、R40/R41 returned carrier 与 issuance provenance 契约、以及仍 `BLOCKED` 的 P-2 producer-owned current-run identity / Task 9-P 链路。下一会话必须先建立一份只读、证据绑定的 **G6 阻塞图**：逐项区分已冻结证据、合同已通过但未实施项、已实施但未完成 evidence/freeze 的项、以及必须获得产品/API 裁决或独立授权的项。

该阻塞图的唯一目的，是派生一份**唯一下一授权包**：准确说明单一下一 Gate/任务、角色、允许读取的事实源、精确写集（如有）、允许执行的验证命令（如有）、完成条件和禁止扩张边界。不得因做了 RECOVER 而自动启动实现、测试、Git 或任何 GitHub 服务端动作。

### 新会话的唯一下一合法动作

仅做 G6 整体只读 RECOVER 与阻塞图/授权包草案：

1. 按 [`AGENTS.md`](AGENTS.md) 规定读取事实源，并读取 [`plans/production-implementation-control.md`](plans/production-implementation-control.md)、[`plans/production-implementation-pi-500-r1-f09-implementation-plan.md`](plans/production-implementation-pi-500-r1-f09-implementation-plan.md)、[`plans/g6-task8-r40-preprod-authority-construction-seam-contract.md`](plans/g6-task8-r40-preprod-authority-construction-seam-contract.md)、[`plans/g6-task8-r41-run-target-ref-capture-provisioning-seam-contract.md`](plans/g6-task8-r41-run-target-ref-capture-provisioning-seam-contract.md)、[`plans/g6-task8-r42-feedback-owner-revalidation-call-count-contract.md`](plans/g6-task8-r42-feedback-owner-revalidation-call-count-contract.md)、[`plans/g6-task9p-prerequisite-authority-contract.md`](plans/g6-task9p-prerequisite-authority-contract.md) 和 [`plans/g6-task9p-p2-current-run-identity-authority-adjudication.md`](plans/g6-task9p-p2-current-run-identity-authority-adjudication.md)。
2. 只读核验最新 Gate/实现状态与依赖；不得以本 handoff 或历史摘要替代各合同和控制表。
3. 产出 G6 阻塞图和唯一下一授权包草案，列明证据、状态、依赖、风险、最小下一步及其 exact scope；完成后停止并等待用户对该授权包的明确批准。

### 新会话启动提示词

```text
继续 mangpai-fusion 的整体 G6 问题，但本轮只获授权执行 G6 全局 RECOVER，不启动任何 implementation、test execution、Git 或 GitHub 操作。

先严格按 AGENTS.md 的事实源顺序读取；再读取 handoff.md 第 9 节，以及以下当前控制/合同：
- plans/production-implementation-control.md
- plans/production-implementation-pi-500-r1-f09-implementation-plan.md
- plans/g6-task8-r40-preprod-authority-construction-seam-contract.md
- plans/g6-task8-r41-run-target-ref-capture-provisioning-seam-contract.md
- plans/g6-task8-r42-feedback-owner-revalidation-call-count-contract.md
- plans/g6-task9p-prerequisite-authority-contract.md
- plans/g6-task9p-p2-current-run-identity-authority-adjudication.md

已知最新 R42 事实：在唯一授权的 engine/f09/feedback.py 与 tests/f09/test_feedback_eligibility.py 中，restricted self-excluded-material 路径已由旧的 4 次 public manifest verifier 调用修订为恰好 1 次；目标测试文件最终为 111 passed。这不是 G6、P-2、Task 9-P 或全仓完成证明。

本轮交付物只能是只读、证据绑定的《G6 阻塞图与唯一下一授权包草案》：
1) 对每一相关 G6 任务/契约列出 authoritative status、直接证据、依赖与阻塞原因；
2) 明确区分：已 evidence-bounded freeze、contract-only PASS、已实现待 evidence/freeze、REVISE、BLOCKED、STILL_OPEN；
3) 提出且只提出一个最小下一授权包，包含目的、角色、允许读取项、精确 write set（若需要）、允许命令（若需要）、验证标准、停止边界；
4) 标明该建议为何先于其他候选工作项，且不得把 RECOVER 结论当作实现授权。

硬禁止：不得修改任何文件（包括 handoff、状态文件、plans、production、tests）；不得运行 Python、pytest、Git 或 GitHub 操作；不得重开已冻结的 F01–F12 语义；不得把 R42、P-1 contract PASS、R39 freeze 或 manifest verifier 推导为 P-2 PASS、Task 9-P total Gate PASS 或 G6 完成。完成阻塞图和唯一授权包草案后停止，等待用户明确批准。
```

---

## 10. Prospective 首案短期交接

> 本节只交接当前下一动作；机器状态仍以 [`META/project-state.json`](META/project-state.json) 和既有不可变制品为准，不在本文件建立竞争事实源。

- 首案 v004 的 immutable frozen result 已正式存在，feedback release 也已落盘；当前唯一业务动作是直接完成该案已释放的即时回顾，不重新 intake、freeze 或生成空制品。正式反馈链以对应 `--frozen-run` 为父制品；可选 witness / verification 不是反馈前置条件。
- `prediction_capability_candidate_gate_v1 = HOLD`：即时回顾尚未完成。
- `future_empirical_gate_v1 = HOLD`：未来观察尚未完成。
- `historical_platform_baseline_2026_07_15 = HOLD`：保持只读独立门禁，不得由即时或未来样本冲抵。
- 默认 routing 保持 static，`production_switch=false`；离线 GO 不代表平台 GO 或生产 GO，只能形成不可变结果与升级提案。

---

## 11. 2026-07-28 · Unit11 as-of 会话制品化 evidence-gated 交接

> **持久化范围：** 本节仅追加记录 Unit11 的本地 evidence-bounded freeze。权威契约为 [`plans/as-of-life-state-unit11-real-case-session-productization-contract.md`](plans/as-of-life-state-unit11-real-case-session-productization-contract.md)，完整证据账本为 [`reports/as-of-life-state-unit11-second-case-session-productization-report.md`](reports/as-of-life-state-unit11-second-case-session-productization-report.md)；本节是恢复快照，不替代上述事实源，也不改变第 1–10 节所记录的其他项目状态。

### 冻结状态与交付物

- Unit11 已完成 Gate 0–Gate 6；冻结 verdict 为 `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`。
- 新增 [`tools/as_of_session_cli.py`](tools/as_of_session_cli.py)，提供历史/手动 as-of 事业会话 side path；它是**手动 opt-in 旁路，不切换任何生产默认入口**。
- 第二真实案例冻结为 `C-2026-RF000118-乾-己巳癸酉辛丑己丑`，输入 fixture 为 [`cases/C-2026-RF000118-乾-己巳癸酉辛丑己丑/asof_session_input.json`](cases/C-2026-RF000118-乾-己巳癸酉辛丑己丑/asof_session_input.json)。案例来源包含多个明确事业事件，但本单元仅冻结 feedback 第 34 行的 2020 年跳槽事件；唯一 confirmed ID 为 `career-2020-job-change`。
- 专项测试为 [`tests/asof/test_unit11_second_case_session_productization.py`](tests/asof/test_unit11_second_case_session_productization.py)，证明 runner 与 archive 各委托一次、`CREATED`→`UNCHANGED`、artifact 读回 digest、未核验语义隔离、结构化错误及 AST 生产隔离。
- 未修改既有 `engine/asof/*.py` 行为或签名，未修改既有 as-of 测试，未切换生产 pipeline、报告、反馈、服务或公开 schema。

### 新鲜证据与失败历史

- smoke：`CREATED PROJECTED 1 1`；CLI：exit 0、`status=CREATED`、`session_state=PROJECTED`、`projection_created=true`。
- Unit11 专项：`6 passed in 0.57s`；as-of 全量：`467 passed, 1 skipped, 1 warning in 3.03s`；production isolation：`4 passed, 1 warning in 0.59s`。
- 既有 `tests/asof/test_*.py` 排除 Unit11 文件后共 24 个，实施前后 ledger SHA-256 均为 `7827c645aa20d4744202719b38492e5422bb5b165b60c5a5392d68d96fb1bc5e`，`changed=0`；AST 扫描为 `forbidden=[]`。
- 首轮专项曾为 `1 failed, 5 passed`：测试把裸字符串 `2026` 用于整份 artifact 搜索，误命中合法 metadata；分类为 test defect，修正为仅检查 ledger/state/projection 的具体未核验语义后，专项 6/6 通过。
- Gate 5 fresh evidence review 曾判 `REVISE`：契约误述 fixture 冻结五个事件；分类为 contract gap，现已修正为“多个事件证明案例适合遴选，但 Unit11 仅冻结 2020 事件”，复核后 contract、fixture、测试与报告一致。

### 证据边界、保护与停止点

- 直接证明：显式磁盘 JSON 可通过既有 [`run_career_session()`](engine/asof/session_runner.py:53) 与 [`archive_asof_state()`](engine/asof/archive_integration.py:163) 完成手动会话、投影、归档和读回；选定第二真实案例可走同一编排链；已核验与未核验语义保持隔离。
- 不得推导：任意案例自动泛化、自动候选抽取、命理或未来预测准确率、生产 promotion、服务化、全仓正确性、部署或 GitHub 同步。
- 本受控 Unit11 会话未执行本地 Git、GitHub 服务端 mutation、网络、外部服务或生产入口操作。该陈述只覆盖本受控会话直接执行的操作，不证明 GitHub 整体状态。
- 当前停止点：Unit11 技术冻结与 append-only handoff 均已完成。唯一下一合法动作是停止 Unit11 自动推进；未来若有新任务，必须从上述契约与证据报告重新 RECOVER，并另行冻结其精确范围，不得继承 Unit11 写集、测试或生产权限。

---

## 12. 2026-08-06 · W2-C1 杨派婚姻 typed governance adapter evidence-gated 交接

> **持久化范围：** 本节仅追加记录 W2-C1 的本地 evidence-bounded freeze。权威契约为 [`.omo/drafts/multi-school-governance-wave2-yang-marriage-2026-08-06.md`](.omo/drafts/multi-school-governance-wave2-yang-marriage-2026-08-06.md)，实施计划为 [`.omo/plans/multi-school-governance-wave2-yang-marriage-2026-08-06.md`](.omo/plans/multi-school-governance-wave2-yang-marriage-2026-08-06.md)，动态证据与审查结论分别见 [`.omo/evidence/w2-c1-yang-marriage-typed-adapter-verify-2026-08-06.md`](.omo/evidence/w2-c1-yang-marriage-typed-adapter-verify-2026-08-06.md) 和 [`.omo/evidence/w2-c1-yang-marriage-typed-adapter-evidence-review-2026-08-06.md`](.omo/evidence/w2-c1-yang-marriage-typed-adapter-evidence-review-2026-08-06.md)。本节是恢复快照，不替代上述事实源，也不改变第 1–11 节记录的其他项目状态。

### 冻结状态与交付物

- W2-C1 已依序完成 CONTRACT、IMPLEMENT、STATIC_REVIEW、VERIFY、EVIDENCE_REVIEW；最终 verdict 为 `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`。
- 新增 [`adapt_yang_marriage_discrimination()`](engine/application/governance_yang_marriage_adapter.py:47)，将杨派婚姻三态领域结果保守映射为 typed governance claim 或 typed loss；专项契约测试位于 [`tests/application/test_governance_yang_marriage_adapter.py`](tests/application/test_governance_yang_marriage_adapter.py)。
- 冻结绑定为 school `yang_qingjuan`、task `marriage.divorce_or_remarriage`、event/support/natal/inferential、confidence `0.60`、adapter version `yang-marriage-discrimination/v1`，并精确绑定 `M2-Y-068` 与 `M2-Y-088` 两个 source refs。
- 该 adapter 保持 shadow-only：未登记 capability，未接入 registry、runner 或 pipeline，未发布 artifact，未设置 proposal/production switch。

### 新鲜证据与失败历史

- 最终 collect-only 为 39 collected；focused 为 39 passed；Yang regressions 为 81 passed；governance adapter regressions 为 7 passed。合计执行 127 项，0 failed、0 errors、0 skipped、0 xfailed、0 deselected。
- 首轮最终 focused VERIFY 曾为 38 passed / 1 failed：first-import isolation 测试把允许依赖 [`engine.governance`](engine/governance/__init__.py) facade 的既有 transitive loader 误归因给目标 adapter；经 fresh-process 边界探针确认目标模块在允许依赖 baseline 后没有新增 registry-loader 模块，分类为 test defect，仅修订测试归因边界。
- STATIC_REVIEW R4–R6 均为 REVISE，依次补齐动态导入/依赖漂移门禁并收窄误伤合法 source tuple 下标的规则；最终 R7 PASS。旧 review 与失败运行保留为历史，不作为最终 PASS 证据。
- Wave 1 的 [`tests/test_application_candidates.py`](tests/test_application_candidates.py:21) `SyntaxError` 仍是独立历史 Gate D 红态；W2-C1 focused PASS 不覆盖、不修复也不重分类该红态。

### 证据边界、保护与停止点

- 直接证明：冻结 source SHA-256 与 exact refs 下，杨派婚姻 concrete result 的 event/pressure/abstain 和指定异常 seam 满足 W2-C1 typed adapter 契约；目标模块的静态依赖与允许依赖 baseline 后 first-import 增量满足冻结 isolation 边界。
- 不得推导：W2-C2 或 Wave 2 整体完成、capability/registry publication、预测准确率、proposal readiness、生产发布、部署、全仓正确性或 GitHub 同步。
- W2-C2 必须重新经过独立 ADMISSION；W2-C1 的写集、测试权限、Gate PASS 与冻结结论均不可继承。生产发布继续保持独立人工授权。
- 保护继续有效：保留既有 tracked/untracked 修改；禁止 reset、clean、checkout、restore、stash、rebase、commit；禁止 GitHub 服务端写操作。
- 当前停止点：W2-C1 技术冻结与 append-only handoff 已完成。唯一下一合法动作是停止 W2-C1 自动推进；未来若要启动 W2-C2，必须从独立 RECOVER/ADMISSION 开始，且不得由本交接自动激活。

---

## 13. 2026-08-07 · W2-C2 governance shadow → blind output adapter evidence-gated 交接

> **持久化范围：** 本节仅追加记录 W2-C2 的本地 evidence-bounded freeze。权威契约为 [`.omo/drafts/multi-school-governance-wave2-shadow-blind-adapter-2026-08-07.md`](.omo/drafts/multi-school-governance-wave2-shadow-blind-adapter-2026-08-07.md)。本节是恢复快照，不替代契约、Boulder、completion ledger 或项目事实源，也不激活后续单元。

### 冻结状态与交付面

- W2-C2 已依次完成 CONTRACT、IMPLEMENT、STATIC_REVIEW、VERIFY、EVIDENCE_REVIEW 与 FREEZE；最终 verdict 为 `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`。
- 本地交付文件仅为 [`engine/evaluation/governance_shadow_adapter.py`](engine/evaluation/governance_shadow_adapter.py) 与 [`tests/evaluation/test_governance_shadow_adapter.py`](tests/evaluation/test_governance_shadow_adapter.py)。
- 适配入口为 [`adapt_governance_shadow_to_blind_outputs()`](engine/evaluation/governance_shadow_adapter.py:285)，把受约束的 `GovernanceShadowResult`、`BlindTask` 与显式 reviewed projection 映射为确定性的 `tuple[BlindSchoolOutput, ...]`。
- 三态边界冻结为 `unsupported`、`abstain`、`claim`；projection 是显式 attestation，不得解释为 shadow result 已独立认证的事实。
- claim 仅在事件 token `yang.divorce_or_remarriage_event_risk/v1` 与 typed claim conclusion 逐字节同时匹配时成立；关系压力、近义表达、截断文本、关键词或 claim kind/stance 均不得替代该联合谓词。

### Revision、review 与验证证据

- CONTRACT R1：REVISE；修复 projection attestation 边界、typed claim binding、non-claim rationale、exact task/ref/accounting predicates。
- CONTRACT R2：REVISE；唯一缺口为 relationship-pressure conclusion 仍可能错误映射为事件标签。
- CONTRACT R3：引入 exact event token 与 exact typed conclusion 联合谓词；独立 fresh review PASS。
- STATIC_REVIEW：PASS；30 个 unique test functions，其中 17 个参数化函数；静态预期为 123 pytest items。
- focused VERIFY：`123 passed in 12.38s`。
- narrow VERIFY：`76 passed in 2.10s`。
- broader VERIFY：`378 passed in 151.76s`。
- 三层动态验证均为 0 failed、0 errors、0 skipped、0 xfailed、0 deselected；focused 静态/动态核算为 `123 = 123`。
- 独立 EVIDENCE_REVIEW：PASS；Freeze eligible：YES。

### 直接证明、禁止推导与保护边界

- 直接证明：在冻结的 exact task、projection schema、result identity、typed claim ownership、event predicate、probability/window/ref grammar 与排序规则下，adapter 满足 focused contract，并通过本次记录的 narrow 与 broader regression selectors。
- 不证明：projection attestation 真实或具有外部 custody；prediction accuracy 或 calibration；W2-C3 完成；capability publication、registry publication、routing、production readiness、deployment、Wave 2 完成或全仓库正确性。
- 本受控会话未执行 Git 或 GitHub mutation 操作；这不推导 GitHub 整体状态、同步状态或远端未发生其他变化。
- 继续保护全部 tracked/untracked 修改；禁止 reset、clean、checkout、restore、stash、rebase、commit；永久禁止 GitHub 服务端 mutation。
- [`.omo/boulder.json`](.omo/boulder.json) 已记录 W2-C2 为 `completed`，且 `active_work_id` 保持 `null`；[`.omo/start-work/ledger.jsonl`](.omo/start-work/ledger.jsonl) 已 append completion 事件。

### 唯一下一合法动作

- 当前停止点：W2-C2 技术冻结与 append-only handoff 均已完成。停止 W2-C2 自动推进。
- W2-C3 未授权、未激活；任何 successor unit 必须从独立 RECOVER 与 ADMISSION 开始，不继承 W2-C2 的 contract、写权限、测试权限、Gate PASS、publication 或 production 权限。

---

## 14. 2026-08-08 · W2-C3 reconciliation-only Gate 交接

> **纠正性追加而非历史改写：** 上一节保留了当时 durable controller state 中“W2-C3 未授权、未激活”的原始记录。后续只读调查发现 W2-C3 源码与测试已经落盘，且 W2-C3 草案包含 PASS 自述，但 Boulder、append-only ledger 与本交接未同步。本节不删除该冲突、不回填历史 start/completion，也不认证草案中的旧测试自述；它仅记录 2026-08-08 当前时间重新执行的 reconciliation evidence。权威当前证据为 [`.omo/evidence/w2-c3-prospective-staging-reconciliation-2026-08-08.md`](.omo/evidence/w2-c3-prospective-staging-reconciliation-2026-08-08.md)。

### 当前 reconciliation verdict

- 初始 verdict 为 `REVISE`：历史 `20/20` 与 `123/123` 自述缺少独立 durable evidence，不能补写成历史 PASS。
- 当前 fresh static review 与两个草案精确 selectors 均成功后，最终 verdict 为 `PASS / CURRENT RECONCILIATION COMPLETE — EVIDENCE-BOUNDED FREEZE`。
- 此 PASS 只认证当前被检查状态，不认证历史运行；[`.omo/start-work/ledger.jsonl`](.omo/start-work/ledger.jsonl) 追加的是当前 `work-reconciled` 事实，不是伪造的历史 `work-started` 或 `work-completed` 事件。

### Fresh evidence 与准确核算

- W2-C3 精确 selector：44 collected，20 selected / 20 passed，24 deselected，0 failed / errors / skipped，exit code `0`，用时 `3.10s`。
- W2-C2 read-only adapter selector：123 collected / selected / passed，0 deselected / failed / errors / skipped，exit code `0`，用时 `1.80s`。
- Fresh static review：exit code `0`；确认 [`build_single_case_staged_frozen_run()`](engine/evaluation/prospective_single_case.py:972) 的 keyword-only governance API、`evaluation_note` task binding、唯一 adapter call、required/forbidden import 边界，以及 source-line 顺序 merge → timing → grid → freeze → verify；staged artifact payload 未加入 governance result/projection/custody/metadata 字段。
- 聚合 selected execution 为 143 passed、24 deselected；该数字不是全仓测试结论，也未执行草案中的 broader 两文件 selector。

### 证明边界与生产状态

- 直接证明：当前 W2-C3 implementation/test surface 满足上述静态边界与精确 selectors；W2-C2 adapter regression 在其完整单文件 selector 下保持 123 passed。
- 不证明：历史测试自述、全仓正确性、预测准确率、校准、外部 custody、real cohort readiness、publication、deployment、远端状态或生产授权。
- [`META/project-state.json`](META/project-state.json:70) 已只读核对且未修改：`real_cohort="not_ready"`、`production_ready=false`、`production_switch_permitted=false`。
- 本次只修改 W2-C3 evidence、Boulder、append-only ledger 与本 handoff；未修改源码、测试、production、router、weights、reports、feedback 或 registry；未执行 Git、GitHub、网络或远端 mutation。

### 唯一下一合法动作

- 当前停止点：W2-C3 当前时间 reconciliation 与 durable-state 同步完成，停止 W2-C3 自动推进。
- 不创建、不激活 W2-C4；任何 successor unit 必须重新经过独立 RECOVER 与 ADMISSION，不继承 W2-C3 的 contract、写权限、测试权限、Gate PASS、publication 或 production 权限。

---

## 15. 2026-08-08 · W2-C4 governance promotion REVISE / STOP 交接

> **纠正性 STOP persistence，不是成功交接：** 本节只追加记录 W2-C4 在关键实现假设被两轮独立核验推翻后的真实停止状态。权威证据为 [`.omo/evidence/w2-c4-governance-promotion-stop-2026-08-08.md`](.omo/evidence/w2-c4-governance-promotion-stop-2026-08-08.md)，合同为 [`.omo/drafts/w2-c4-governance-promotion-admission-contract-2026-08-08.md`](.omo/drafts/w2-c4-governance-promotion-admission-contract-2026-08-08.md)。本节不覆盖旧历史、不回填历史 start/PASS/completion，不构成 `HANDOFF complete / success`。

### Durable verdict 与 Gate 边界

- W2-C4 当前 durable verdict：`REVISE / BLOCKED / STOPPED`。
- CONTRACT 曾为 `PASS / CLOSED / FROZEN`，但只冻结合同；不等于实现可行、当前 Gate PASS 或技术 FREEZE。
- IMPLEMENT 曾产生 `32 focused PASS`，仅保留为旧实现证据；fresh STATIC_REVIEW 为 `REVISE`，所以 32 focused PASS 不是当前 Gate PASS。
- VERIFY 未运行；二次独立技术核验为 `confirmed`。未伪造 HOLD artifact、VERIFY PASS、EVIDENCE_REVIEW PASS 或 FREEZE PASS。
- W2-C4 **未 FREEZE**，也未形成成功完成的 HANDOFF；本节仅证明 STOP 已 durable persistence。W2-C5 未授权、未激活、不得自动进入。

### 关键假设推翻与实现缺陷

- 合同要求 promotion snapshot 从真实磁盘 lineage 认证五维身份：`school_id × task_id × claim_kind × evidence_grade × capability_version`。
- 当前 sealed prospective lineage 的 [`ArtifactRef`](engine/evaluation/prospective_artifacts.py:23) 只有 path/digest；[`GateEvidence`](engine/evaluation/prospective_gates.py:64) 也不携带 `claim_kind`、`evidence_grade`、`capability_version`。因此在当前白名单内不能诚实地从真实 lineage 构建合同要求的 W2-C4 snapshot。
- 当前新增 [`build_and_publish_metric_snapshot()`](engine/evaluation/governance_promotion.py:499) 仍依赖自造扁平 observation/gate parents，而非真实 cohort/gate lineage 重建；audit 状态由聚合 GO 推断；另有路径安全、typed/closed taxonomy 与 evidence parent accounting 缺陷。
- 当前专项测试 [`tests/evaluation/test_governance_promotion.py`](tests/evaluation/test_governance_promotion.py) 使用嵌入五维身份的合成 JSON fixture；它不能认证现有真实 sealed lineage 已携带这些字段。
- 遵照关键假设推翻即停止的硬边界，本轮未修复 [`engine/evaluation/governance_promotion.py`](engine/evaluation/governance_promotion.py) 或任何测试、contract、artifact primitive、gate owner。

### 项目状态、保护与证据边界

- [`META/project-state.json`](META/project-state.json:70) 只读且保持 `real_cohort="not_ready"`、`production_ready=false`、`production_switch_permitted=false`。
- 本轮仅修改 W2-C4 STOP evidence、[`.omo/boulder.json`](.omo/boulder.json)、append-only [`.omo/start-work/ledger.jsonl`](.omo/start-work/ledger.jsonl) 和本 handoff；未修改 Python、tests、contract 或 project state。
- 未运行测试、Python 验证、Ruff、compileall、Git、GitHub、网络、部署、发布或远端 mutation。
- 不得从 CONTRACT PASS、旧 32 focused PASS、fixture 分支或 STOP persistence 推导真实 HOLD artifact、candidate、accuracy、calibration、incremental value、proposal readiness、production readiness、W2-C4 FREEZE、Wave2 completion 或 W2-C5 authority。

### 唯一下一合法动作

由用户决定是否修订 W2-C4 合同，或明确扩展 sealed lineage owner / implementation whitelist，使真实 lineage owner 可认证携带五维 promotion identity。在该决定与新的精确授权之前，必须保持 W2-C4 STOP；不得修源码、运行测试、制造 artifact、标 completed/PASS/frozen、形成成功 HANDOFF，或启动 W2-C5。

---

