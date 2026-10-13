# W2-C1 杨派婚姻 typed governance adapter 实施计划

**计划状态：** plan-pass；fresh adversarial review R2 `PASS`
**前置 Gate：** CONTRACT R5 `PASS`
**冻结契约：** `.omo/drafts/multi-school-governance-wave2-yang-marriage-2026-08-06.md`  
**当前授权边界：** 本文件只描述未来本地实施；计划 PASS 前不得激活 Boulder/ledger，不得创建实现文件，不得运行实现验证，不得执行 Git 操作或任何 GitHub 服务端写操作。

## TL;DR（给人看的）

**你会得到：** 一个独立、确定性的杨派婚姻治理适配边界：只有证据完整的事件态能形成一条保守的治理支持 claim；压力态和弃权态始终保留为可审计 non-claim。

**为什么这样做：** 保留既有三态判别作为唯一语义源，不把新结果伪装成旧 claim，也不放宽通用 adapter。规则锚、内容版本、证据等级和置信度全部冻结，避免 shadow 结果被误当成发布或生产权限。

**不会做：** 不改 registry，不接入 runner/pipeline，不做冻结、评分、晋升、发布或生产切换，也不重构既有杨派实现。

**工作量：** Short  
**风险：** High —— 婚姻事件是高风险二元 claim，错误的分支顺序或 source identity 会把 `pressure` 膨胀成事件，或把 non-claim 错计入评分。

**已裁决关键选择：** `pressure` / `abstain` 优先终止为 `INSUFFICIENT_EVIDENCE`；只有 `event` 校验 exact source refs 与 catalog。

下一步：先对本计划做 fresh adversarial review；只有计划 PASS 后才允许激活 W2-C1 的 Boulder/ledger 和受限实施阶段。

---

> TL;DR（机器）：Short/high-risk；新增一个 typed adapter 和聚焦测试，条件性更新 application lazy export；shadow-only，禁止 registry/runner/production 变化。

## 目标

实现以下唯一公共 typed boundary：

```python
adapt_yang_marriage_discrimination(
    result: YangMarriageDiscrimination,
    catalog: GovernanceReferenceCatalog,
) -> AdaptationResult
```

它必须满足：

1. concrete `event` + exact source anchors + exact catalog registrations → exactly one `GovernanceClaim`，issues 为空；
2. `pressure` / `abstain` → exactly one `INSUFFICIENT_EVIDENCE`，claim 为空；
3. wrong concrete type、altered event refs、catalog rejection 或 governance constructor rejection → 契约规定的单一 typed loss；
4. 完整 discriminator payload、固定 identity/version/ref material 被稳定绑定到 provenance 和 derivation digest；
5. 不改变任何当前 pipeline、registry、runner、legacy Yang slice 或生产行为。

## 范围与风险

### Must have

- 新建 `engine/application/governance_yang_marriage_adapter.py`。
- 新建 `tests/application/test_governance_yang_marriage_adapter.py`。
- 仅当 package public-export convention 在实施时仍要求时，条件性修改 `engine/application/__init__.py` 的 `TYPE_CHECKING` import、`_LAZY_EXPORTS` 和 `__all__`；否则保持不变并记录理由。
- 使用既有 `AdaptationResult`、`loss()`、`GovernanceClaimSpec`、`build_governance_claim()`、`stable_object_id()` 和 `derivation_chain_digest()`。
- 先写聚焦失败测试，再实现最小代码；每次产品修改后都需要 fresh STATIC_REVIEW。
- 精确核算 pytest collection 与 execution，包括 passed/failed/error/skipped/xfail/deselected。

### Must NOT have

- 不修改 `engine/decision/yang_marriage.py`、`engine/decision/yang_marriage_claims.py` 或任何既有 Yang slice。
- 不修改 `engine/application/governance_claim_adapters.py`、`engine/application/governance_claim_adapter_values.py`、`SCHOOL_METADATA_KEYS` 或 `ClaimIssueCode`。
- 不修改 `theory/multi-school-governance-v1.yaml`，不增加 capability/certification。
- 不接入 `run_governance_shadow()`、pipeline、composition、arbitration、trigger 或生产路由。
- 不创建 freeze、score、promotion、publication 或 production receipt artifact。
- 不读取 filesystem、环境变量、网络、系统时钟、labels、feedback、reports、scores 或 learned metrics。
- 不捕获 `Exception`、`ValueError` 或其他非 `GovernanceClaimContractError` 异常。
- 不运行全仓无界修复；既有 Wave 1 Exact Gate D 的 `tests/test_application_candidates.py:21` collection `SyntaxError` 继续作为历史红态保留，不得掩盖或归因于 W2-C1。
- 不执行 reset、clean、checkout、restore、stash、rebase、commit 或任何 GitHub 服务端写操作。

## 架构与强制顺序

```text
concrete type check
  → state branch（必须先于 refs/catalog）
      pressure → INSUFFICIENT_EVIDENCE
      abstain  → INSUFFICIENT_EVIDENCE + blocking_reason_codes
      event    → exact source-anchor equality
                 → typed ClaimReference tuple with frozen content SHA
                 → stable source_claim_ref from complete result.to_dict()
                 → stable AdapterProvenance + derivation digest
                 → GovernanceClaimSpec
                 → build_governance_claim(spec, catalog)
                 → claim or mapped GovernanceClaimContractError loss
```

不可调整的顺序依赖：

1. non-event 必须在任何 `ClaimReference` 构造和 catalog validation 前终止；
2. event altered refs 必须在 catalog validation 前返回 `LEGACY_REFERENCE_INVALID`；
3. exact event refs 才能构造 versioned `SOURCE_RULE` references；
4. provenance/digest 必须在 claim spec 构造前完成；
5. 只有 `build_governance_claim()` 抛出的 `GovernanceClaimContractError` 可被映射；其他异常保持可见；
6. adapter tests 与实现形成一个 TDD 交付单元，不把测试与实现分成可独立完成的并行任务。

## 冻结常量与数据契约

实现模块内仅允许以下语义常量，名称可按项目风格调整，但值和用途不可改变：

| 语义 | 冻结值 |
|---|---|
| school | `yang_qingjuan` |
| task | `marriage.divorce_or_remarriage` |
| claim kind | `ClaimKind.EVENT` |
| stance | `ClaimStance.SUPPORT` |
| temporal scope | `TemporalScope(layer=TemporalLayer.NATAL)` |
| evidence grade | `ClaimEvidenceGrade.INFERENTIAL` |
| confidence | `0.60` |
| adapter version | `yang-marriage-discrimination/v1` |
| source version | `sha256:e8be77f67246ff056770a35d618b4b3fc5694ba5fdec2f65c8d674708355e768` |
| exact source anchors | `theory/yang/index.yaml#M2-Y-068`、`theory/yang/index.yaml#M2-Y-088`，canonical tuple 顺序 |
| conclusion | 沿用既有杨派保守风险措辞，不宣称必然、次数、婚姻质量或时间 |

### Provenance 与 derivation 设计

- 使用 `result.to_dict()` 作为完整 canonical discriminator payload；该 payload 已含 schema、case、state、sex basis、spouse palace、完整 families、A/B gates、blockers、falsifier 和 source refs。
- 通过 `stable_object_id("yang_marriage_discrimination", result.to_dict())`（namespace 若需符合现有命名风格可使用同义的固定 lowercase namespace，但必须由测试冻结）生成 deterministic `source_claim_ref`；禁止 `id()`、`hash()`、`repr(object)` 或随机 UUID。
- 构造 `AdapterProvenance`，adapter ID 必须 Yang-specific 且稳定；adapter version 必须直接使用模块冻结常量 `yang-marriage-discrimination/v1`，不得从 `result.schema_version` 动态复制，也不得由调用方覆盖。
- `result.schema_version` 仍作为完整 discriminator payload 的字段参与 source ref 与 derivation binding。领域构造器允许任意非空 schema 字符串，而 CONTRACT 未定义 schema-mismatch loss，因此 W2-C1 不擅自增加 schema rejection 分支；不同实例 schema 必须改变 source ref/digest，但不得改变冻结 adapter version。若实施前权威 discriminator 的生产 schema 已漂移，则按 Wave 0 STOP 返回 CONTRACT，而不是在 adapter 内兼容漂移。
- 调用 `derivation_chain_digest()`；其 source refs 至少包含 stable source claim ref，metadata 必须显式绑定 school、task、kind、stance、temporal layer、evidence grade、confidence、adapter version、source version 和 ordered exact source refs。
- metadata tuple 顺序在实现中显式固定；测试只能断言稳定性和敏感性，不能复制生产 digest 算法计算“期望 PASS 值”。

### Claim spec 设计

`GovernanceClaimSpec` 应使用：

- `public_fact_refs=()`；
- `certified_fact_refs=()`；
- `school_reason_refs=()`；
- `source_rule_refs=` 两个 exact `ClaimReference(SOURCE_RULE, anchor, frozen_sha)`；
- `blockers=()`、`counterevidence=()`；
- `falsifier=result.falsifier`；
- 其他 identity、scope、confidence、grade、digest、provenance 使用冻结值。

Family facts/features/reason codes 不伪装成 governance refs；它们通过完整 canonical payload 进入 provenance 与 derivation binding。

### Typed loss 映射

| 条件 | 结果 |
|---|---|
| concrete type 不是 `YangMarriageDiscrimination` | `ADAPTER_INPUT_INVALID` |
| `pressure`，不论 refs/catalog | `INSUFFICIENT_EVIDENCE`，detail 标识 pressure，不做负面事件断言 |
| `abstain`，不论 refs/catalog | `INSUFFICIENT_EVIDENCE`，detail 标识 abstain 并稳定保留所有 blocking reason codes |
| event refs 非 exact tuple | `LEGACY_REFERENCE_INVALID` |
| caught issue code 以 `CLAIM.REFERENCE_` 开头 | `LEGACY_REFERENCE_REJECTED` |
| 其他 caught `GovernanceClaimContractError` | `LEGACY_CLAIM_REJECTED` |
| 其他异常 | 不捕获、不转换 |

每个 loss 均为 `AdaptationResult(claim=None, issues=(one_issue,))`。

## 执行策略

### Wave 0：激活与基线保护（计划 PASS 后才允许）

- 在 `.omo/boulder.json` 中仅激活 W2-C1 对应工作记录，并在 `.omo/start-work/ledger.jsonl` 追加唯一 `work-started`；该激活是控制状态，不是产品实现证据。
- 激活前再次核验 source YAML SHA、discriminator schema/anchors、目标实现文件不存在或未被他人创建、共享工作区保护仍成立。
- 任一漂移均停止并回到 CONTRACT；不得通过修改契约常量“适配”漂移。

### Wave 1：TDD RED → 最小实现 → focused GREEN

该 wave 强顺序执行，不并行：

1. 在新测试文件写完整 contract fixtures 和失败测试；只构造 typed domain objects/catalog，不复用 adapter 内部常量作为 expected identity。
2. 运行新测试文件并记录 RED：必须是缺少目标模块/函数或明确未实现行为导致的预期失败；collection error、fixture defect 或无关错误不算有效 RED。
3. 新建 adapter 模块，以最小分支实现全部冻结行为。
4. 仅在公共 package convention 确实要求时更新 application lazy export；若更新，添加针对 `__all__`、`__dir__()` 和 lazy attribute resolution 的断言；否则测试直接从 dedicated module import。
5. 对 constructor catch 边界的不可自然到达分支，测试仅可用 `monkeypatch` 临时替换 adapter 模块局部绑定的 `build_governance_claim`：分别抛出一个 `CLAIM.REFERENCE_*` contract error、一个其他 `GovernanceClaimContractError` 和一个非-contract sentinel exception，断言前两者精确映射而 sentinel 原样传播。不得修改 governance 源模块全局绑定，不得新增生产依赖注入参数、测试 hook 或 public API；pytest fixture 负责自动恢复替换。
6. 运行新测试文件到 GREEN；失败进入最小诊断/修复，不扩大 whitelist。

### Wave 2：fresh STATIC_REVIEW

独立 reviewer 只接收冻结 CONTRACT、完整计划、精确实现 diff 和原始权威文件，检查：

- 只修改 whitelist 文件；
- branch order 是 type → state → event refs → catalog/claim；
- non-event 没有 source/catalog 路径；
- event exact refs 与 frozen SHA 都是不可覆盖常量；
- provenance 绑定完整 `result.to_dict()`；
- adapter version 直接来自冻结模块常量而非 `result.schema_version`，同时 payload schema 变化仍改变 source ref/digest；
- digest metadata 覆盖冻结 identity/version/ref material；
- 只捕获 `GovernanceClaimContractError`；异常分类测试仅 patch adapter 模块局部 constructor binding，未引入生产测试 seam；
- 没有 forbidden imports/tokens、registry/runner/pipeline side effects；
- 测试 expected values 独立于实现常量；
- package export 修改（若有）符合现有 lazy convention且无 eager import cycle。

任何修复都会使原 STATIC_REVIEW PASS 失效，必须重新 fresh review。

### Wave 3：精确 VERIFY 与 evidence accounting

仅在 STATIC_REVIEW fresh PASS 后激活 exact test sub-envelope。按以下顺序执行；不将历史运行当作 fresh evidence：

1. collection-only：
   ```text
   python -B -m pytest --collect-only -q -p no:cacheprovider tests/application/test_governance_yang_marriage_adapter.py
   ```
2. focused new tests：
   ```text
   python -B -m pytest -q -p no:cacheprovider tests/application/test_governance_yang_marriage_adapter.py
   ```
3. Yang regression selectors：
   ```text
   python -B -m pytest -q -p no:cacheprovider tests/yang_marriage/test_domain_model.py tests/yang_marriage/test_signal_families.py tests/yang_marriage/test_school_claim_adapter.py
   ```
4. governance adapter regression selectors：
   ```text
   python -B -m pytest -q -p no:cacheprovider tests/application/test_governance_claim_adapter_boundaries.py tests/application/test_governance_claim_adapter_derivation.py
   ```
5. fresh-process digest stability 必须由新测试中的 `subprocess.run([sys.executable, "-c", ...])` 覆盖，并断言 return code/stderr；不得依赖当前 Python process。
6. 静态 isolation 检查由测试通过 Python AST/源码 token 完成，至少拒绝 filesystem、environment、network、clock、labels、feedback、reports、scores、registry loader、runner/pipeline imports；不得用容易误报注释的无界字符串匹配作为唯一证据。

每条命令记录：完整命令、cwd、开始时间、结束时间、exit code、collected/executed/deselected/skipped/xfailed/failed/errored/passed。collection error 等于零行为证据。不得把 focused PASS 扩大解释为全仓 PASS。

### Wave 4：EVIDENCE_REVIEW → bounded FREEZE → HANDOFF

- 独立 Evidence Reviewer 核对 CONTRACT PASS、最新 STATIC_REVIEW PASS、所有 fresh VERIFY 证据、失败/修复/rerun 历史和 collection accounting。
- 只有证据完整一致时，W2-C1 才可得到 `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`。
- Freeze 仅证明 typed adapter 在所列 selector 和边界内成立；不证明 Wave 2 全体完成、capability eligibility、预测准确率、proposal readiness、publication 或 production readiness。
- Freeze 后再单独持久化 HANDOFF；未成功持久化时状态只能是 `FROZEN / HANDOFF PENDING`。

## 任务清单与依赖矩阵

| Task | Depends on | Blocks | 可并行 |
|---|---|---|---|
| T0 控制激活与基线复核 | 计划 fresh PASS | T1 | 否 |
| T1 typed adapter TDD 交付 | T0 | T2 | 否，同一文件强顺序 |
| T2 fresh STATIC_REVIEW | T1 | T3 | 否 |
| T3 focused VERIFY/accounting | T2 PASS | T4 | 命令可按独立终端并行，但默认顺序执行以简化失败归因 |
| T4 EVIDENCE_REVIEW/FREEZE/HANDOFF | T3 完整有效证据 | 后续单元 ADMISSION | 否 |

### T0：激活 W2-C1 并保护基线

- **文件：** 条件性修改 `.omo/boulder.json`；append-only 修改 `.omo/start-work/ledger.jsonl`。
- **边界：** 仅在本计划 fresh PASS 后；不得激活 W2-C2～W2-C5；不得将 work-started 解释成 IMPLEMENT 或 PASS。
- **实施：** 记录 exact contract/plan refs、local-only scope、implementation whitelist、禁止操作和 source SHA witness。
- **验证：** 读取写入结果，确认 JSON 可解析、ledger 新增恰好一行、没有覆盖既有记录；确认 source SHA/schema/anchors 未漂移。
- **完成：** 控制状态唯一指向 W2-C1 IMPLEMENT/TDD_RED，且产品文件未变化。

### T1：新增 typed adapter 与 contract tests

- **文件：** 新增 `engine/application/governance_yang_marriage_adapter.py`；新增 `tests/application/test_governance_yang_marriage_adapter.py`；条件性修改 `engine/application/__init__.py`。
- **边界：** 实现本计划全部冻结 contract；不得修改其他产品或测试文件。
- **实施：** 按 Wave 1 的 RED→GREEN 顺序，覆盖 concrete type、三态优先级、exact event refs、catalog error mapping、conservative claim、provenance/digest determinism、异常不吞、isolation 和 side-effect absence。
- **验证：** 新测试先出现有效 RED，再 focused GREEN；测试收集实例数与执行实例数一致。
- **完成：** 新模块可以独立 import；所有新行为 partitions 有独立断言；non-event 永不触发 catalog；event claim exact identity/content/provenance 可审计。

### T2：fresh STATIC_REVIEW

- **文件：** 只读 CONTRACT、计划、实现 diff 和权威接口；若 REVISE，修复仍限 T1 whitelist。
- **边界：** reviewer 不继承 implementer 自评；修复后重新 review。
- **验证：** 输出逐条 contract/whitelist/dependency/import/exception/test-independence verdict。
- **完成：** fresh `PASS`，并明确 directly proven 与 forbidden inference boundary。

### T3：运行 exact verification selectors并核算证据

- **文件：** 不改产品；证据写入仓库既有 `.omo/evidence/` 命名约定下的 W2-C1 evidence 文件，具体文件名在激活 envelope 中冻结。
- **边界：** 只运行 Wave 3 的 exact selectors；不自动扩展到 full suite，不绕过历史 Gate D 红态。
- **验证：** collection-only + 三组 focused runs；fresh-process digest 与 static isolation 包含在新测试实例中；所有 exit code 和实例状态完整记录。
- **完成：** 每个 selector 均有 fresh、有效、可重放证据，且静态/动态计数一致。

### T4：证据审查、冻结和交接

- **文件：** 条件性更新控制状态与 append-only ledger/handoff；不修改产品代码。
- **边界：** 只有 EVIDENCE_REVIEW PASS 才能 FREEZE；FREEZE 不授权发布或下一单元实现。
- **验证：** 核对失败历史、最新 rerun、selector count、source/version witness、shared-worktree protection 和 remote-side-effect boundary。
- **完成：** W2-C1 为 evidence-bounded frozen 且 HANDOFF 已持久化，或精确记录阻塞原因；W2-C2 仍需独立 ADMISSION。

## 新测试文件的最低行为分区

1. male event 和 female event 各生成 exactly one claim；
2. claim exact school/task/kind/stance/scope/grade/confidence/conclusion/falsifier；
3. source refs exactly two、category exact、SHA version exact、canonical order；
4. pressure × exact/altered refs × valid/empty/wrong catalog 均为 `INSUFFICIENT_EVIDENCE`；
5. abstain × exact/altered refs × valid/empty/wrong catalog 均为 `INSUFFICIENT_EVIDENCE`，blockers 稳定保留；
6. wrong concrete type → `ADAPTER_INPUT_INVALID`；
7. event missing/additional/substituted refs → `LEGACY_REFERENCE_INVALID`，且证明 catalog validation 未先行；
8. event unknown anchor registration / missing one registration / wrong version → `LEGACY_REFERENCE_REJECTED`；
9. 通过 monkeypatch adapter 模块局部 `build_governance_claim` binding 抛出 non-reference contract error，验证 → `LEGACY_CLAIM_REJECTED` 且 detail 含原 issue code/diagnostic；同一 seam 抛 `CLAIM.REFERENCE_*` 时验证 `LEGACY_REFERENCE_REJECTED`；
10. 同一局部 seam 抛出测试专用非-contract sentinel exception，验证异常原样传播且未被捕获；测试不得 patch governance 源模块、不得要求生产注入参数；
11. 同一 payload 同进程与 fresh process 的 source ref、derivation digest、claim ID/content digest 稳定；
12. case、schema、family payload或 falsifier 变化会改变 payload-derived source ref/digest；冻结 identity/adapter version/source version/ordered refs 通过独立 derivation helper 输入敏感性测试验证，不能要求 public adapter 暴露覆盖参数；public adapter 对 altered exact refs fail closed，且 adapter provenance version 始终为冻结常量；
13. family/pair 输入排序的 canonical equivalent 不改变输出；
14. conclusion 无 `100%`、`必离`、`多婚命`、时间或婚姻质量扩张；
15. AST/isolation 与 package import side-effect 检查；
16. 若更新 application facade，lazy export/`__all__`/`__dir__()` 行为回归。

## 风险与回退

- **最大语义风险：** source validation 提前于 state branch。回退方式不是调整 loss expectation，而是恢复冻结的 non-event-first 顺序并 fresh review/rerun。
- **身份风险：** 使用部分 payload 或 runtime hash 造成跨进程漂移。修复必须回到完整 `to_dict()` + canonical primitive，不得引入缓存、随机 ID 或 filesystem lookup。
- **错误分类风险：** broad exception handling 掩盖编程错误。发现 `except Exception`、`except ValueError` 或等价 broad catch 即 STATIC_REVIEW REVISE。
- **导出风险：** eager facade import 可能形成循环。仅使用现有 lazy export convention；若 dedicated-module public import 已符合仓库习惯，则不修改 facade。
- **共享工作区风险：** 任何 pre-existing tracked/untracked 内容冲突都 STOP；禁止 reset/restore/stash/commit 混合处理。
- **历史红态：** Wave 1 Exact Gate D 的既有 collection `SyntaxError` 保持显式隔离；W2-C1 focused PASS 不覆盖它。
- **治理越权风险：** registry `published`、artifact creation、offline GO 或 `proposal_allowed=true` 都不是生产许可；W2-C1 不产生这些状态。

## Final verification wave

以下四个 review lane 必须基于同一最终实现和同一 fresh evidence ledger 全部 PASS：

- **F1 Plan compliance audit：** whitelist、任务顺序、loss map、exact identities、证据计数。
- **F2 Code quality review：** typed/immutable boundary、determinism、exception discipline、dependency direction、无无关抽象。
- **F3 Behavioral QA：** 三态交叉矩阵、event ref/catalog 矩阵、fresh-process replay、canonical permutation。
- **F4 Scope fidelity：** 无 registry/runner/pipeline/freeze/scoring/promotion/publication/production 变化，无 Git/GitHub 写操作。

任一 lane 非 PASS，不能宣称完成或 freeze。

## Commit 策略

本计划不授权任何 Git 操作。实施期间也默认不 stage、不 commit；若未来另有精确 local-Git envelope，必须先检查 exact diff、排除用户既有修改，并标记 `LOCAL ONLY / NOT PUSHED`。GitHub 服务端写操作永久禁止。

## Plan review history

- **R1 verdict：** `REVISE`。
- **R1 finding A：** adapter version 表述可能从任意实例 schema 动态复制，与冻结 non-overridable version 冲突。
- **R1 finding B：** constructor contract/non-contract exception tests 没有指定可执行且不扩张生产 API 的 seam。
- **R1 bounded revision：** 固定模块 adapter version；实例 schema 仅进入 payload binding；异常测试只 monkeypatch adapter 模块局部 `build_governance_claim` binding，并禁止新增生产测试 seam。
- **R1 forbidden inference：** 本次修订不构成计划 PASS，不激活 Boulder/ledger，也不证明实现或测试存在。
- **R2 verdict：** `PASS`。
- **R2 directly proven：** 修订后计划与 CONTRACT R5、真实 canonical/derivation/claim 接口、三态优先级、exact whitelist、shadow-only 边界和受控证据顺序一致，且具备可执行的 TDD 与异常边界测试 seam。
- **R2 forbidden inference：** 该 PASS 只证明计划可实施；不证明 Boulder/ledger 已激活、实现存在、测试通过、capability 已发布、proposal 可用或生产已授权。
- **R2 unique next legal action：** 由 Controller 在最小 local-only scope 下激活 W2-C1 的 Boulder/append-only ledger，并在任何产品修改前复核冻结 SHA、schema/anchors、目标路径与共享工作区保护。

## 成功标准

1. CONTRACT R5 PASS 保持有效且 source/schema 未漂移；
2. 实际修改严格限定为实现 whitelist；
3. typed adapter 满足完整三态、identity、source、catalog、provenance、digest、loss 和 isolation contract；
4. fresh STATIC_REVIEW PASS；
5. 所有 exact selectors fresh PASS，collection/execution accounting 完整，失败历史未省略；
6. fresh EVIDENCE_REVIEW PASS 后才进行 evidence-bounded freeze；
7. HANDOFF 成功持久化；
8. 明确不推断 capability publication、预测准确率、proposal readiness、production readiness 或 production authorization。
