# As-of Blind Bundle First Proof Point · Evidence-Bounded Freeze Report

> 日期：2026-08-07（Asia/Shanghai）  
> Active unit：合成单事件 blind-bundle → freeze → release → verify 纵切  
> 最终裁决：**FREEZE — PASS（evidence-bounded）**

## 1. 冻结结论

本 active unit 已依次完成 CONTRACT、IMPLEMENT、STATIC_REVIEW、VERIFY 与 logically fresh EVIDENCE_REVIEW。冻结范围仅为：测试内显式合成、位于 trusted workspace root 下临时根中的单事件链，能够通过既有 typed as-of API 完成 bundle 验证、冻结、release gate、custody 开启与 verified-result 封存。

本冻结不是产品发布，不改变 production routing，不证明命理判断有效性、真实案例可用性、全仓正确性或全部隐藏 consumer 无回归。

## 2. 冻结实现范围

本单元实现与验证涉及：

- `engine/evaluation/prospective_asof.py`
- `tools/as_of_prospective.py`
- `tests/evaluation/test_prospective_asof.py`

权威合同：

- `plans/as-of-blind-bundle-first-proof-point-contract-2026-08-07.md`

冻结 public API 保持七个 exact keyword-only signatures：

- `prepare_asof_blind_bundle()`
- `verify_asof_blind_bundle()`
- `build_career_blind_draft()`
- `build_asof_frozen_artifact()`
- `build_asof_feedback_release()`
- `verify_asof_feedback_release()`
- `collect_asof_verification()`

## 3. 关键冻结语义

### 3.1 Trusted root 与路径身份

- trusted workspace root 在模块首次 import 时固定。
- API 与 CLI 共享同一模块对象及 trusted-root binding。
- 新 as-of artifact 中保存的路径是 trusted-root 相对 POSIX path。
- 旧 `prospective_single_case` parent bundle 内部 manifest identity 仍按旧 verifier 要求保存并核验绝对 path。
- 两层路径身份分账，不互相替代：旧 parent 内部 absolute identity；新 as-of stored parent reference 为相对 canonical identity。

### 3.2 单事件状态链

冻结状态链为：

```text
BUNDLE_VERIFIED
  → FROZEN_SEALED
  → RELEASED
  → VERIFIED_RESULT_SEALED
```

正式 cardinality：

```text
fundamentals = exactly 1
events = exactly 1
```

verification 只为唯一 event 生成 record，不为 fundamental 生成 verification record。record state 为 `VERIFICATION_OPEN`，并绑定同一 freeze hash、session identity 与唯一 event item ID。

### 3.3 Release-before-custody

- release 无效、漂移或发生异常时，custody reader 调用次数为 0。
- 合法单事件 release 验证完成后，custody reader 调用次数恰好为 1。
- 单事件核验分别调用既有 `open_verification()`、`verification_input_from_mapping()` 与 `record_career_verification()` 恰好一次。

### 3.4 CLI 与错误边界

冻结 CLI grammar：

```text
python -m tools.as_of_prospective freeze --bundle-root <dir> --out <path>
python -m tools.as_of_prospective release --frozen <path> --created-at <UTC-Z> --out <path>
python -m tools.as_of_prospective verify --release <path> --custody <released-json> --collected-at <UTC-Z> --out <path>
```

UTC-Z 接受整秒或可选小数秒。CLI 单故障路径中，link-like output 映射为 `ASOF_LINK_ERROR`，普通已存在 output 映射为 `ASOF_CONFLICT_ERROR`，malformed stored input path 映射为 `ASOF_PATH_ERROR`。

本冻结不声称 parser/filesystem/schema 多故障并存时的全局错误优先级已证明。

## 4. STATIC_REVIEW 证据

最后一次修改只修正测试中 stale parent-ref assertion，使其与生产 `_canonical_path()` 的 trusted-root 相对 POSIX 语义一致。随后 logically fresh STATIC_REVIEW 返回 **PASS**，确认：

- 旧 parent manifest 的 absolute identity 与新 as-of stored parent-ref 的 relative identity 已正确分账；
- parent-ref 数据流未复用旧 manifest 的绝对 `artifact_path`；
- 测试 fixture 与 assertion 分别验证各自层级语义。

静态审查 PASS 仅表示合同与源码静态闭合，不替代动态行为证据。

## 5. VERIFY 原始证据

合同 §11 冻结的 exact commands 均退出码 0：

| 证据组 | 结果 |
|---|---:|
| `tests/evaluation/test_prospective_asof.py -q` | 31 passed in 7.77s |
| 同文件 `-k "asof_bundle_first_proof"` | 31 passed in 13.17s |
| 三个 exact as-of compatibility nodes | 3 passed in 0.56s |
| 六个 exact prospective consumer compatibility nodes | 6 passed in 2.17s |

两个 31-instance selectors 均收集并通过 31 个实例；未收集 two-event、locator 或 real-case smoke。

### 5.1 历史失败留痕

VERIFY 调试历史未抹除：

1. 首次运行：24 failed / 7 passed。
2. 第二次运行：1 failed / 30 passed。
3. 最终在根因确认、最小修复和 fresh STATIC_REVIEW 后，同一冻结 selector：31 passed。

历史失败根因包括测试 parent fixture 的旧 verifier path identity 不匹配、CLI oracle 遗留 output 造成非单故障、以及新 as-of parent-ref stale absolute assertion。后续 PASS 取代其当前 Gate 结论，但不删除历史证据。

## 6. EVIDENCE_REVIEW

Logically fresh EVIDENCE_REVIEW verdict：**PASS**。

审查确认：

- 四组命令与合同 §11 exact selectors 一致；
- collection 数符合 31 + 3 + 6；
- deferred selectors 未被收集；
- 历史失败已由同 selector 的后续 PASS 取代并保留留痕；
- selected compatibility nodes 未被夸大为 full-system correctness。

## 7. 明确未冻结与 deferred units

以下内容未进入本 active unit，保持 inactive：

- deferred A：two-event 动态核算；
- deferred B：真实案例 closed request provenance、locator 与 real-case full smoke；
- deferred C：parser/filesystem/schema 多故障组合的全局错误优先级；
- 真实案例、feedback、known facts、analysis、lessons、reports 的业务读取；
- 命理准确率、事业预测有效性或真实命主结论；
- 全套测试、全仓正确性及全部隐藏 consumer 行为；
- production pipeline、render、routing、deployment、release 或 production switch；
- 本地 Git 与任何 GitHub 服务端变更。

GitHub 服务端变更继续永久禁止。

## 8. Freeze verdict 与下一边界

```text
Gate: FREEZE
Verdict: PASS
Scope: synthetic, single-event, evidence-bounded First Proof Point only
Direct evidence: exact 31 + 3 + 6 frozen selectors PASS after fresh STATIC_REVIEW
Forbidden inference: full-system correctness, real-case proof, two-event behavior,
                     global multi-fault precedence, prediction validity,
                     deployment/release/production readiness
```

本报告完成 evidence-bounded freeze 持久化。后续只能进行 HANDOFF 状态交接；任何 deferred unit、真实案例读取、额外实现、额外测试、Git/GitHub、部署、发布、routing 或 production switch 均需新的独立明确授权。
