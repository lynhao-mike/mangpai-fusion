# as-of blind-bundle First Proof Point 合同（2026-08-07）

> 状态：CONTRACT REVISION R3-ANCHOR-A / LOCAL ONLY / NOT PUSHED
>
> 本合同只冻结一个可证伪的最薄纵切；不授予 IMPLEMENT、测试执行、Git、GitHub、部署、发布、routing 或 production switch 权限。

## 1. 权威输入与证据边界

1. 优先级裁决：`plans/as-of-life-state-next-task-geju-adjudication-2026-07-29.md` §7、§10。
2. 现有 blind-bundle：`engine/evaluation/prospective_single_case.py` 的单案 bundle 构造与复验。
3. 现有 artifact path/create-only 语义：`engine/evaluation/prospective_artifacts.py`。
4. 现有 custody/release：`engine/evaluation/prospective_evidence.py` 的 feedback release 与 release 后读取边界。
5. 现有 as-of identity、输入、冻结与 event verification：`engine/asof/session_contract.py`、`engine/asof/consultation_freeze.py`。
6. 真实失败证据：`reports/as-of-life-state-blind-judgment-n50-extension-report.md`。

直接已证明：现有单案 bundle 可 create-only 落盘并机械复验文件白名单、父链与摘要；现有 as-of API 可生成带 `SessionIdentity`、blind-input SHA-256 与 canonical SHA-256 的 `CareerFreezePackage`；`record_career_verification()` 只能核验 frozen event candidate；现有 prospective evidence 层可在 release 验证前不调用 feedback reader。

不得推导：以上事实不证明现有 bundle schema 已承载完整 as-of 输入，不证明现有 release v1/v2 已接受 as-of frozen parent，不证明仓库已有生产级 `CareerBlindDraft` builder，也不证明 First Proof Point 已实现、可运行、命中、可批量或生产就绪。

## 2. 唯一目标

建立且只建立一个隔离的单案纵切：

```text
一个正式 as-of blind-bundle
  → verify bundle-only input
  → 固定 side-path draft builder 生成 CareerBlindDraft
  → 真实 as-of freeze API 生成 CareerFreezePackage，fundamentals=1、events=1
  → create-only 写入只含一个 event 的原生 as-of frozen artifact
  → 独立重读并复验 canonical hash
  → 由实际 frozen artifact identity 创建只接受一个 event 的 typed release
  → release 重读验证成功后才调用 custody reader
  → 以既有 event verification API 生成绑定同一 freeze hash、只含一个 event record 的 verified-result artifact
```

First Proof Point 必须用自动化测试证明 custody 在合法 release 之前接口不可达。当前单元只使用测试内显式合成的单事件输入与临时链，不选择真实案例，不读取案例、feedback、known facts、analysis、lessons 或 reports，也不从环境变量取得任何业务事实。真实案例 closed request provenance 与 real-case full smoke 整体登记到后续独立合同，不是当前实现或 VERIFY selector。

## 3. 明确非目标

- 不恢复 N50，不实现批量 runner。
- 不扩展婚姻、健康、家庭、教育等 as-of 领域。
- 不修改或替代静态多派 `FrozenBlindRun`。
- 不把 `CareerFreezePackage` 伪装成 `school-capability-single-case-staged-run/v1`。
- 不改变现有 future-question 二元三个月窗口语义。
- 不切换 `tools/production_as_of_cli.py`、报告 pipeline 或任何默认生产入口。
- 不修改 `engine/asof/` 已冻结公共 API。
- 不修改 `engine/evaluation/prospective_evidence.py`；as-of release 使用独立 typed schema，既有 v1/v2、immediate custody、future observation 与 completion consumers 必须 byte-for-byte 保持原实现。
- “不核验 `CareerFreezePackage.fundamentals`”只表示“不生成 fundamental verification record”：本纵切的正式 schema cardinality 仍冻结为 fundamentals=1、events=1，并仍须验证 fundamental 的存在、唯一性及 frozen package canonical binding；verification 阶段只为唯一 frozen event 生成既有 record，因为现有 `record_career_verification()` 不接受 fundamental ID。该澄清不新增 selector，不改变 record schema，也不把 fundamental 扩大成 verification record。
- 不打开、grep、搜索或读取任何案例的 `feedback.md`、`analysis.md`、`lessons.md`、`statement_records.json`、reports 或 `known_facts:` 后内容；当前单元没有真实案例 release 后读取例外。
- 不证明 two-event 或任意多事件动态核算；不证明真实案例 closed request provenance 或 real-case full smoke；不证明 parser/filesystem/schema 多故障同时存在时的全局组合错误优先级。
- 不证明命理学有效性、统计显著性、总体盲断准确率、N50 readiness、F10 GO 或 production readiness。

## 4. Anchor Ledger（R1 前一次性冻结）

Anchor Ledger — Unit：`ASOF-BLIND-BUNDLE-FPP-2026-08-07`

### 4.1 冻结 public API surface（精确签名）

新模块 `engine.evaluation.prospective_asof` 的 module-owned public callables 必须恰好为以下七个，全部参数 keyword-only；不得增加位置参数、`*args` 或 `**kwargs`：

```python
def prepare_asof_blind_bundle(
    *,
    parent_bundle_root: Path,
    asof_request: Mapping[str, object],
    target_dir: Path,
    dry_run: bool,
) -> dict[str, object]: ...

def verify_asof_blind_bundle(
    *,
    bundle_root: Path,
) -> dict[str, object]: ...

def build_career_blind_draft(
    *,
    blind_input: BlindChartInput,
    identity: SessionIdentity,
) -> CareerBlindDraft: ...

def build_asof_frozen_artifact(
    *,
    bundle_root: Path,
) -> dict[str, object]: ...

def build_asof_feedback_release(
    *,
    frozen_artifact: Mapping[str, object],
    created_at: str,
) -> dict[str, object]: ...

def verify_asof_feedback_release(
    *,
    release: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]: ...

def collect_asof_verification(
    *,
    release: Mapping[str, object],
    custody_reader: Callable[[], Mapping[str, object]],
    collected_at: str,
) -> dict[str, object]: ...
```

方案 A：保持上述七个 public API 签名不变。trusted workspace root 的唯一 locator/initialization/cache 算法为：`engine.evaluation.prospective_asof` 首次 import 时恰好执行一次 `_TRUSTED_WORKSPACE_ROOT = Path.cwd().resolve(strict=True)`，并把结果保存在该模块不可重绑定的 private module-level constant 中；该 import-time 初始化就是本合同所称“进程启动时固定”，失败必须 fail-closed。CLI 必须通过 import 该模块使用同一常量，direct API 与 CLI 在同一进程内必须共享同一对象值；不得为传递 root 新增参数、selector 或 public callable，也不得从 artifact path、caller mapping、环境变量或其他模块反推、注入、替换或重解析可信根。初始化后的当前工作目录变化不得改变该值。

`build_career_blind_draft()` 是 First Proof Point 唯一 concrete draft source。它只接收 bundle 解析出的 `BlindChartInput` 与 `SessionIdentity`，并且必须恰好返回一个 fundamental 和一个 event；不得接收路径、feedback、labels、report、known facts、系统日期或任意 repository context。CLI `freeze` 必须经 `build_asof_frozen_artifact()` 委托该 exact symbol，不允许 CLI 注入 builder、fixture 或 callable。其逐字段 deterministic oracle 冻结在 §8.1；这只是验证原生 freeze/release/verification 链可闭合的结构探针，不得解释成命理有效性或准确率证据。

### 4.2 冻结 CLI grammar（精确 subcommands/flags）

```text
python -m tools.as_of_prospective freeze --bundle-root <dir> --out <path>
python -m tools.as_of_prospective release --frozen <path> --created-at <UTC-Z> --out <path>
python -m tools.as_of_prospective verify --release <path> --custody <released-json> --collected-at <UTC-Z> --out <path>
```

每个 subcommand 只允许上列 flags；不提供 `--feedback-path`、`--case-dir`、`--report`、builder 参数或通配路径参数。`freeze` 只能读取 bundle root；`release` 只能读取实际 sealed frozen artifact；`verify` 只能读取实际 sealed release 与 release 后由 outcome custodian 提供的 closed custody JSON。所有 `--out` 必须等于第 6 节的唯一 canonical path。正式写入均 create-only；已存在、symlink、junction 或其他 link-like 目标必须 fail-closed。

`--created-at` 与 `--collected-at` 的唯一 UTC-Z grammar 为 `YYYY-MM-DDTHH:MM:SS(?:\.[0-9]+)?Z`：接受整秒或一位以上小数秒，合法输入文本原样保留进入 artifact，先按该 grammar 解析后再以 UTC instant 做时间比较；不得规范化后替换 artifact 中的合法输入文本，不得做 locale 或 system-time inference。任何偏移写法、缺失 `Z`、逗号小数、空小数或 grammar 外文本均 fail-closed 为 `ASOF_TIME_ERROR`。

### 4.3 冻结状态机、status 与 error set

```text
BUNDLE_VERIFIED → FROZEN_SEALED → RELEASED → VERIFIED_RESULT_SEALED
```

只允许逐步前进；不得跳步、回退或覆盖。`FROZEN_SEALED` 之前 custody reader 不存在于 API；实际 sealed release 被重读验证之前 custody reader 调用次数必须为 0。

新 artifact 的 closed status 值恰好为：

```text
bundle_status: BUNDLE_VERIFIED
freeze_status: FROZEN_SEALED
release_status: RELEASED
verification_status: VERIFIED_RESULT_SEALED
```

CLI 成功 exit code 为 `0`；任何失败统一 exit code `2`，stderr 必须恰好为下列一个稳定类名加单个换行，不得输出异常文本、payload、custody 内容或路径：

```text
ASOF_SCHEMA_ERROR
ASOF_IDENTITY_ERROR
ASOF_PATH_ERROR
ASOF_PARENT_ERROR
ASOF_HASH_ERROR
ASOF_TIME_ERROR
ASOF_STATE_ERROR
ASOF_LINK_ERROR
ASOF_CONFLICT_ERROR
ASOF_CUSTODY_ERROR
ASOF_DOMAIN_ERROR
ASOF_IO_ERROR
```

错误类名集合仍恰好为上述十二个。当前单元只要求每个 parser、filesystem、schema、identity、parent、hash、time、state、custody 与 domain 验证点沿其实际单路径稳定映射到集合内恰好一个类名；CLI 统一保持 exit code `2`、单类名 stderr、不泄漏内容。当前单元不构造多故障组合，不定义或声称跨 parser/filesystem/schema 验证点的全局排序已被证明；该全局组合错误优先级整体移入后续独立合同。未知单路径异常归 `ASOF_DOMAIN_ERROR`，但仍不得回显原异常。`ORPHANED_SEALED_PREREQUISITE` 不是 artifact status、schema field、返回值或新增 stderr 类名；它只是在异常对象内部不可持久化的诊断 reason，并且对 CLI 唯一映射为 `ASOF_IO_ERROR`。实现不得新增其他错误类名或状态值，也不得把失败表示为成功 artifact。

### 4.4 冻结幂等、冲突与失败语义

- 相同 bundle bytes 必须产生相同 `BlindChartInput`、`CareerBlindDraft`、`blind_input_sha256`、`freeze_package_sha256` 与 frozen artifact canonical digest；wall-clock 时间不得进入 draft/freeze 计算。
- `frozen_at` 等于 sealed request 的 `created_at`；不是运行时当前时间。
- 相同目标已存在时返回 conflict，不覆写；调用者可独立重读并验证既有 artifact，但第二次调用不得报告为新创建。
- 任一 parent、文件集合、文件 bytes、identity、时间顺序或摘要漂移均 fail-closed。
- 单 JSON artifact 的失败不得留下目标正式文件或可被误认成正式 artifact 的临时文件。request + directory bundle 是明确的两阶段 create-only publication，不承诺跨文件系统事务：
  1. `prepare_asof_blind_bundle()` 是 request 与 bundle 的唯一创建者；先在内存完成 parent 重验、closed request 校验、canonical paths、四个 bundle bytes 与全部 digest 计算。
  2. `dry_run=True` 时返回同一 canonical request document 与 manifest plan，写入次数恰好为 0，目标存在与 link-like 冲突仍须在返回前检查。
  3. `dry_run=False` 时先 create-only 发布 `request_path`；立即从该实际路径重读 bytes，验证 closed schema、`artifact_path` 和 `artifact_sha256`，后续不得再信 caller mapping 或预写内存 request。
  4. 只有 request 重读成功后，才在 sibling 临时目录中按固定顺序写入 `parent-bundle-ref.json`、`asof-request.json`、`chart.json`、`bundle-manifest.json` 四个文件并逐字节复验；最后以 create-only directory rename 发布 `asof_bundle_root`，随后重读 `bundle-manifest.json` 和全部 manifest-listed bytes。
  5. request 发布前失败，正式 request/bundle 均不得存在；request 已 sealed 而 bundle 发布失败时，request 必须原样保留；异常内部 reason 固定为 `ORPHANED_SEALED_PREREQUISITE`，CLI 固定输出 `ASOF_IO_ERROR`。不得把该 reason 写入任何 closed artifact/status/返回值，不得删除、覆盖、续写、自动重用 request 或报告 `BUNDLE_VERIFIED`。调用立即 STOP，后续只能在 fresh diagnosis 后另行裁决。
  6. 任一 bundle 临时目录必须位于 `selected_case_root`，名称含不可预测随机后缀且不匹配任何正式 artifact basename；失败时只清理本次拥有的临时目录。不得删除或更改任何 sealed prerequisite。
  7. `verify_asof_blind_bundle()` 只信实际 `asof-request.json` bytes、其 manifest digest、实际 request parent ref 与 sealed standalone request；调用者内存 mapping 不具有证据资格。

### 4.5 冻结文件白名单

CONTRACT R1 唯一可修改文件：

```text
plans/as-of-blind-bundle-first-proof-point-contract-2026-08-07.md
```

只有 CONTRACT fresh PASS 后才可派生 IMPLEMENT scope；本合同本身不激活该 scope。拟议 IMPLEMENT whitelist 仅为：

```text
engine/evaluation/prospective_asof.py                         NEW
tools/as_of_prospective.py                                  NEW
tests/evaluation/test_prospective_asof.py                    NEW
reports/as-of-blind-bundle-first-proof-point-report-2026-08-07.md NEW
handoff.md                                                   APPEND ONLY after all Gates PASS
```

当前单元不实例化任何真实案例动态路径；测试内 request、bundle、frozen、release 与 verified-result 只允许位于测试框架提供的临时目录，测试结束后不得作为正式仓库 artifact 保留。禁止修改 `engine/asof/**`、`engine/evaluation/prospective_evidence.py`、`engine/evaluation/prospective_single_case.py`、`tools/school_capability_prospective.py`、既有测试、既有案例原文件、既有 prospective artifact、默认生产入口及本白名单外全部文件。

### 4.6 Anchor authority source

| Anchor | Authority source |
|---|---|
| 唯一正式 blind-bundle → as-of freeze → release → verify 纵切 | `plans/as-of-life-state-next-task-geju-adjudication-2026-07-29.md`，PROJECT ADJUDICATION |
| `BlindChartInput` / `SessionIdentity` / `CareerFreezePackage` / event verification 语义 | 既有受保护 API，PROJECT STATE |
| public API、CLI、typed artifacts、exact paths | admitted target 的最小 side-path 设计；R1 中一次性冻结，CONTRACT 通过后仅用户决定可改变 |
| 状态、错误、幂等、冲突、closed schemas | 既有 create-only/canonical/fail-closed 语义与本单元可证伪要求 |
| 文件白名单、非目标、GitHub/生产禁令 | 用户边界、仓库规则、controller permanent protections |

Anchor provenance：用户在 R2 repeated-defect stop 后曾明确裁决“以当前合同中冻结的 Anchor Ledger 作为权威 baseline”，并授权 R2-LP1 literal-only 修订与 fresh review。其后用户再次明确授权拆分当前单元：当前正式链冻结为 fundamentals=1、events=1，并把 two-event 动态核算、真实案例 closed request provenance + real-case full smoke、全局组合错误优先级分别移入后续独立合同。R3-SPLIT1 只按该用户裁决修改受影响的 schema cardinality、accounting、selectors、错误证明边界、白名单与 Gate 记录。最新用户 Anchor adjudication 明确批准方案 A，并把 fresh review 的七项意见分类为 `B/B/A/C/C/B/A`：本轮 literal patch 仅修 `A/C/A` 项；`B` 类 REVIEWER_ANCHOR_DRIFT 一律拒绝且不得实施，包括删除或改变 §4.5 既有五项拟议 whitelist、把 fundamental verification 扩大为 fundamental record、改变 11 names/31 instances 或新增动态 selector。七个 public signatures、三条 CLI grammar、四步状态机、十二个 CLI error names、two-stage publication/orphan、canonical path/parent/hash/time、chart 原 bytes、actual sealed release before custody、single-event event-only record、consumer baseline 兼容性、deferred A/B/C 及禁止生产/反馈/GitHub边界保持冻结。该裁决不构成 IMPLEMENT、测试执行或 deferred unit 激活权。

## 5. Identity 映射（唯一规则）

prospective identity 与 as-of identity 不得混用：

1. artifact/bundle `case_id` 必须保持 parent manifest 的 `P-GO-YYYY-NNN-{乾|坤}-{四柱}`，称 `prospective_case_id`。
2. `SessionIdentity.case_id` 必须由纯字符串转换唯一生成：去掉 prospective ID 的 `P-GO-` 前缀并加 `C-`，即 `P-GO-2026-001-坤-...` → `C-2026-001-坤-...`，称 `session_case_id`；禁止 caller 自由提供另一个值。
3. `subject_id_hash` 必须逐值继承 verified parent manifest；它与两个 case ID 同时交叉绑定，不能替代任何 case ID。
4. `as_of_date` 与 `session_id` 逐值来自 sealed request。`session_id` 必须符合现有 `S-YYYYMMDDTHHMMSSZ-xxxxxxxx`；其日期前八位必须等于 `as_of_date` 的无连字符日期。
5. `SessionIdentity` 必须恰好构造为 `(SESSION_SCHEMA_VERSION, session_case_id, as_of_date, session_id)`；frozen、release、verified-result 必须同时保存 `prospective_case_id` 与 `session_case_id`。
6. 任一转换、性别、四柱、subject hash、日期或 session binding 不一致立即 fail-closed。

## 6. Canonical roots、paths 与 parent identity

给定测试内显式合成并通过既有 verifier 的 parent bundle root：

```text
<dataset-root>/<prospective_case_id>/<prospective_case_id>--blind-bundle--vNNN
```

唯一推导为：

```text
dataset_root       = parent_bundle_root.parent.parent
selected_case_root = dataset_root / prospective_case_id  # 当前单元中必须位于测试独占临时根
parent_identity    = parent_bundle_root / bundle-manifest.json
request_path       = selected_case_root / <case_id>--asof-request--v001.json
asof_bundle_root   = selected_case_root / <case_id>--asof-blind-bundle--v001
asof_bundle_id     = asof_bundle_root / bundle-manifest.json
frozen_path        = selected_case_root / <case_id>--asof-frozen-run--v001.json
release_path       = selected_case_root / <case_id>--asof-feedback-release--v001.json
verified_path      = selected_case_root / <case_id>--asof-verified-result--v001.json
```

目录型 bundle 的唯一 parent identity 是其 canonical `bundle-manifest.json` 的 `{artifact_path, artifact_sha256}`；目录路径或目录摘要不得充当 parent ref。所有 JSON parent refs 必须是 closed object，字段恰好为 `artifact_path`、`artifact_sha256`。

trusted workspace root 必须严格按 §4.1 的唯一算法，在 `engine.evaluation.prospective_asof` 首次 import 时由 `Path.cwd().resolve(strict=True)` 恰好解析一次并缓存于不可重绑定的 private module-level `_TRUSTED_WORKSPACE_ROOT`；所有七个 API 与 CLI 必须只读取该同一固定值。所有 stored `artifact_path` 必须是该 root 下的相对 POSIX path。必须拒绝 absolute path、Windows drive path、UNC path、`.`、`..`、解析后越出 trusted root，以及 trusted root 本身或从 trusted root 到目标的任一 link-like component（包括 symlink、junction 或同类重解析链接）。不得从 artifact path、caller mapping、环境变量、其他模块、当前 cwd 或后续 cwd 变化反推、注入、替换或重解析 trusted root。该规则只在 trusted root 下的测试独占临时根中验证，不授予仓库 artifact 写入权。v001 之外版本、替代 root 或自由 `--out` 一律拒绝。

所有接收 artifact mapping 的 mapping-only API——包括 `build_asof_feedback_release()`、`verify_asof_feedback_release()` 与 `collect_asof_verification()`——必须从 mapping 的 `artifact_path` 在固定 trusted root 下完成上述路径验证、定位并重读 actual sealed bytes；caller mapping 必须与重读 document 完全一致，且其 canonical digest 必须与重读 document 的 canonical digest 及 stored `artifact_sha256` 一致，否则 fail-closed。caller mapping、摘要字符串或路径存在本身均不具有证据资格。

## 7. Closed schemas

所有 object 均拒绝 unknown/missing fields；所有 digest 为小写 64 位 SHA-256；所有 timestamp 必须匹配 `YYYY-MM-DDTHH:MM:SS(?:\.[0-9]+)?Z`，合法原文本保留、比较使用解析后的 UTC instant；所有数组保持输入顺序且 identity 不重复。

所有 closed JSON artifact 的 canonical artifact digest 沿用 `engine/evaluation/prospective_artifacts.py` 的既有语义且不改变任何 schema 字段集合：从完整 document 移除 `artifact_sha256` self-field，以 JSON UTF-8、`ensure_ascii=False`、`sort_keys=True`、`separators=(",", ":")` 序列化，然后计算 SHA-256 并以小写 64 位十六进制保存。closed object 中出现任何非 JSON-safe 值、NaN、Infinity 或无法按该投影无歧义序列化的值必须 fail-closed；不得字符串化、丢弃或替换该值。

### 7.1 `prospective-asof-request/v1`

顶层字段恰好为：

```text
schema_version
case_id
session_case_id
subject_id_hash
as_of_date
session_id
chart_source
hidden_stems_by_pillar
changsheng_by_pillar
daiyun
created_at
artifact_path
parents
artifact_sha256
```

`parents` 恰好一个 verified parent `bundle-manifest.json` ref。`hidden_stems_by_pillar` 与 `changsheng_by_pillar` 均是字段恰好为 `year/month/day/hour` 的 closed object；前者每值为 1–3 个无重复天干，后者每值为现有十二长生枚举值。`daiyun` 为 1–20 个 closed object，每项字段恰好为 `sequence/stem/branch/start_date/end_date`，sequence 从 1 连续，日期区间首尾合法且相邻连续。四柱 stem/branch 与 gender 只从 verified parent bundle 的 `chart.json` 获取；request 不重复定义。

### 7.2 `prospective-asof-blind-bundle/v1`

bundle 目录精确四文件：

```text
parent-bundle-ref.json
asof-request.json
chart.json
bundle-manifest.json
```

前三个文件逐字节分别为：canonical parent ref、sealed request、parent bundle 的 canonical chart。manifest 顶层字段恰好为：

```text
schema_version
case_id
session_case_id
subject_id_hash
as_of_date
session_id
created_at
artifact_path
parents
files
bundle_status
artifact_sha256
```

`artifact_path` 等于 `asof_bundle_id`；`parents` 按固定顺序恰好为 parent bundle manifest ref、request ref；`files` 是字段恰好为前三个文件名的 closed object，值为实际 file-byte SHA-256；不得把 manifest 自身放入 `files`。

### 7.3 `prospective-asof-frozen-run/v1`

字段恰好为：

```text
schema_version
case_id
session_case_id
subject_id_hash
as_of_date
session_id
frozen_at
artifact_path
parents
freeze_status
blind_input_sha256
freeze_package_sha256
freeze_package
artifact_sha256
```

`parents` 恰好一个 `asof_bundle_id` ref。`freeze_package` 必须是 `freeze_package_to_canonical_bytes()` 所定义 canonical projection 解码后的完整 object；其 `identity.case_id` 必须等于 `session_case_id`，正式 schema cardinality 冻结为 fundamentals=1、events=1；正式 frozen artifact 必须拒绝零个或多个 event。`freeze_package_sha256` 必须由重建后的 `CareerFreezePackage` 调用现有 canonical API 复验，不得只 hash 外层 mapping。

### 7.4 `prospective-asof-feedback-release/v1`

字段恰好为：

```text
schema_version
case_id
session_case_id
subject_id_hash
as_of_date
session_id
created_at
artifact_path
parents
release_status
blind_input_sha256
freeze_package_sha256
artifact_sha256
```

`parents` 恰好一个实际 frozen artifact ref；`created_at >= frozen_at`；所有 identity/hash 必须逐值等于实际重读 frozen parent。release 只能由 events=1 的实际 frozen parent 签发，零个或多个 event 均拒绝。此 schema 与既有 `prospective-feedback-release/v1|v2` 不互认。

### 7.5 released custody input：`prospective-asof-custody/v1`

custody 是 release 后外部输入，不是正式输出 artifact；顶层字段恰好为：

```text
schema_version
case_id
session_case_id
subject_id_hash
session_id
freeze_package_sha256
verifications
```

`verifications` 必须恰好一项，并绑定 frozen package 的唯一 event candidate；每项字段恰好等于现有 `verification_input_from_mapping()` 的 closed fields：`schema_version/freeze_package_sha256/item_id/verdict/actual_landing/reality_constraint/taxonomy_evidence`。禁止字段及递归别名：`prediction/report/analysis/lesson/score/runner/reviewer/known_fact/feedback_path`。

### 7.6 `prospective-asof-verified-result/v1`

字段恰好为：

```text
schema_version
case_id
session_case_id
subject_id_hash
as_of_date
session_id
collected_at
artifact_path
parents
verification_status
blind_input_sha256
freeze_package_sha256
records
artifact_sha256
```

`parents` 按固定顺序恰好为 release ref、frozen ref。`records` 必须恰好保存一个由 `record_career_verification()` 返回的 `CareerVerificationRecord` JSON-safe projection，并绑定 frozen parent 的唯一 event candidate。fundamentals 不得出现在 `records`；不得手写或扩义 fundamental verdict。正式 verified-result 必须拒绝零个或多个 event record。

每个 record 顶层字段恰好为：

```text
envelope
freeze_package_sha256
item_id
verdict
actual_landing
reality_constraint
taxonomy_evidence
landing_verdict
frozen_landing_name
reason_code
```

`envelope` 字段恰好为 `identity/blind_input_sha256/state`；其中 `identity` 字段恰好为 `schema_version/case_id/as_of_date/session_id`。`actual_landing` 为 `null` 或字段恰好为 `name/domain/direction`；`reality_constraint` 为 `null` 或字段恰好为 `state_id/description/closed_landing_names/reachable_landing_names/verified`。所有 enum 存 `.value`，date 存 ISO `YYYY-MM-DD`，tuple 存保持原顺序的 JSON array，Python `None` 存 JSON `null`。`state` 必须为 `VERIFICATION_OPEN`；record 的 identity、blind-input hash、freeze hash 与 item ID 必须逐值绑定实际 frozen parent。任何 unknown/missing field、非 JSON-safe 值或顺序漂移均拒绝。

## 8. Bundle、draft、freeze、release 与读取不变量

1. 新 as-of bundle 只接受一个通过 `verify_single_case_bundle()` 的 parent bundle 与一个 sealed request；runner 所有领域输入只来自重验后的新 bundle。
2. bundle 构造/验证不得遍历 parent case 目录，不得接受任意 source path，不得复制 `input.md`、feedback 或报告。
3. `verify_asof_blind_bundle()` 是 identity/input/initial-envelope 的唯一所有者：它必须由 request 与 chart 组装 mapping，调用 `blind_chart_input_from_mapping()`，构造 `SessionIdentity`，显式检查 session ID 日期前缀等于 `as_of_date`，并调用 `create_initial_envelope()`；返回 closed verified context `manifest/request/chart/blind_input/identity/initial_envelope`。不得复制领域 validator 逻辑替代调用。
4. `build_asof_frozen_artifact()` 必须依次：调用 verify、使用其返回的 `initial_envelope`、transition 到 `BLIND_DRAFTED`、调用 concrete builder、调用 `freeze_career_draft()`、canonical hash、构造 closed frozen artifact。它不得直接或间接再次调用 `create_initial_envelope()`，不得调用完整 `run_career_session()`。
5. `build_asof_feedback_release()` 只接受 exact as-of frozen schema，必须按 §6 从固定 trusted root 重读 mapping 的 `artifact_path` 所指 actual sealed frozen bytes，要求 caller mapping 与重读 document/canonical digest 一致，并复验 parent tree、package canonical bytes、events=1 与全部 identity/hash binding。
6. `collect_asof_verification()` 必须先调用 `verify_asof_feedback_release()`；后者同样必须按 §6 从固定 trusted root 重读 actual sealed release bytes并核对 caller mapping/document/canonical digest。验证失败或异常时 reader 调用为 0。合法单事件 release 后 reader exactly once，再解析 custody。
7. 当前单元 event_count 固定为 1；必须对唯一 event 分别调用 `open_verification()`、`verification_input_from_mapping()` 与 `record_career_verification()` 恰好一次，取得 `VERIFICATION_OPEN` envelope 并生成唯一 record；所有 input 均绑定同一 `freeze_package_sha256`。two-event 动态核算属于后续独立合同，不是当前实现或 VERIFY selector。
8. request/frozen/release/verified 时间必须满足 `request.created_at = frozen_at <= release.created_at <= collected_at`。
9. 禁止读取仓库其他路径、环境变量中的业务事实或系统当前日期。

### 8.1 Concrete draft deterministic behavior oracle

该 builder 不执行完整命理推演，只生成一个显式标记为 structural proof probe 的最小合法 draft；输入之外只有下列冻结字符串常量，禁止自由文案、随机数、locale、clock 或 repository lookup：

1. 选取 `eligible_daiyun = [item for item in blind_input.daiyun if item.end_date <= identity.as_of_date]`；必须恰好非空，否则 `ASOF_DOMAIN_ERROR`。选取 sequence 最大的 `probe_daiyun`。
2. `pillar_token` 恰好为 year/month/day/hour 四柱 stem+branch 依次连接；`probe_token = f"{identity.case_id}|{identity.as_of_date.isoformat()}|{pillar_token}|{probe_daiyun.sequence}|{probe_daiyun.stem}{probe_daiyun.branch}|{probe_daiyun.start_date.isoformat()}|{probe_daiyun.end_date.isoformat()}"`；`probe_digest` 为该 UTF-8 bytes 的小写 SHA-256。
3. 唯一 fundamental 逐字段为：
   - `fundamental_id = "career-fundamental-" + probe_digest[:16]`；
   - window start/end 等于 `probe_daiyun.start_date/end_date`，center 等于两端 ordinal 整数平均向下取整对应日期；
   - `center = "STRUCTURAL_PROBE_ONLY"`；
   - `reasonable_range = ("STRUCTURAL_PROBE_ONLY",)`；
   - `strongest_alternative = "NO_CAREER_INFERENCE"`；
   - `falsifiers = ("PROOF_SEAM_IS_NOT_A_CAREER_PREDICTION",)`。
4. 唯一 event 的 candidate：
   - `candidate_id = "career-event-" + probe_digest[:16]`，`domain="career"`，`event_type="STRUCTURAL_PROBE_ONLY"`，window 等于 probe 大运窗口；
   - 唯一 natal evidence 为 `EvidenceRef("blind-input", "pillars", pillar_token)`；唯一 daiyun evidence 为 `EvidenceRef("blind-input", f"daiyun[{sequence}]", "<stem><branch>|<start>|<end>")`；root evidence 与 supporting evidence 均等于 natal evidence，counter evidence 为空；
   - annual trace：`year=probe_daiyun.end_date.year`，`liunian="STRUCTURAL_PROBE_ONLY"`，`dayun_ganzhi=<stem><branch>`，relations 等于唯一 daiyun evidence，activated node IDs 为 `(f"daiyun-{sequence}",)`，domains 为 `("career",)`，supporting evidence 等于 natal evidence+daiyun evidence，counter evidence 为空，`trigger_strength="low"`，`crossed_candidate_gate=True`；
   - `root_level=WEAK_ROOT`，`completion_mode=COMPLETE_LATENT`，`alternative_hypotheses=("NO_CAREER_INFERENCE",)`，`frozen_version="prospective-asof-structural-probe/v1"`，`verification_status=FROZEN`，`extension_boundary=REMAINDER_ONLY_RECHECK_CROSS_DAIYUN`，`is_primary_event=True`；
   - 唯一 source citation 是固定 governing-contract locator `SourceCitation("plans/as-of-blind-bundle-first-proof-point-contract-2026-08-07.md", 1, "# as-of blind-bundle First Proof Point 合同（2026-08-07）")`；excerpt 必须逐字等于实际第 1 行。它只标识 probe 的治理合同，不说明命理依据，也不充当命理来源证据。
5. 唯一 landing set：`function_candidate="STRUCTURAL_PROBE_ONLY"`；center 为 `LandingPoint("STRUCTURAL_PROBE_ONLY", "career", "structural-probe")`；alternatives 为空；`weak_hit_boundary="EXACT_PROBE_LABEL_ONLY"`；`falsifiers=("ANY_REAL_CAREER_CLAIM",)`；`exclusions=("ACCURACY_INFERENCE",)`；`frozen_version="prospective-asof-structural-probe/v1"`。
6. builder 必须通过上述 dataclass constructors 返回对象；不得用 `object.__new__` 绕过 validation。测试 oracle 独立逐字段断言、重算 token/digest，并证明相同输入跨进程 canonical bytes 相同。

该 oracle 直接证明的上限只是“测试内显式合成且经既有 verifier 验证的 bundle-only input 能穿过原生 typed freeze/release/event-verification 链”；由于 event 明确是结构探针，当前临时链的 custody 只能针对该 probe label 做接口核验，不得记录、推断或宣称任何真实案例 provenance、smoke 或命主事业事实命中。

## 9. Static/API instance accounting

### 9.1 Fully-qualified symbol binding

`engine/evaluation/prospective_asof.py` 必须用以下 exact direct imports，禁止 alias、module import 后 attribute 调用、rebind、wrapper shadow 或动态 import：

```text
engine.asof.session_contract.blind_chart_input_from_mapping
engine.asof.session_contract.create_initial_envelope
engine.asof.session_contract.transition_session
engine.asof.consultation_freeze.freeze_career_draft
engine.asof.consultation_freeze.freeze_package_to_canonical_bytes
engine.asof.consultation_freeze.compute_freeze_package_sha256
engine.asof.consultation_freeze.open_verification
engine.asof.consultation_freeze.verification_input_from_mapping
engine.asof.consultation_freeze.record_career_verification
engine.evaluation.prospective_single_case.verify_single_case_bundle
```

AST 先建立 `ImportFrom(module, original_name → local_name)` 表并断言 `local_name == original_name`；再只统计解析到该 binding 的 `ast.Name` calls。attribute basename 或未解析名称不得计入。

### 9.2 Exact static/dynamic counts

1. `build_asof_frozen_artifact()`：`verify_asof_blind_bundle` 1、`transition_session` 1、`build_career_blind_draft` 1、`freeze_career_draft` 1、`freeze_package_to_canonical_bytes` 1、`compute_freeze_package_sha256` 1、`create_initial_envelope` 0、`run_career_session` 0。
2. `verify_asof_blind_bundle()`：`verify_single_case_bundle` 1、`blind_chart_input_from_mapping` 1、`create_initial_envelope` 1。
3. `collect_asof_verification()`：当前 event_count=1；`verify_asof_feedback_release` 1、`open_verification` 1、`verification_input_from_mapping` 1、`record_career_verification` 1。two-event 或任意多事件的动态次数不属于当前 accounting、实现要求或 VERIFY selector。
4. custody reader：合法单事件 release exactly 1；任何非法/异常 release exactly 0。
5. 新模块中 `FrozenBlindRun`、`freeze_outputs`、`generate_blind_outputs`、`run_career_session` 的 import/call 各 0。
6. 新模块与 CLI 中 `glob/rglob/walk` 调用各 0；案例路径枚举与业务事实环境变量读取各 0；`feedback.md`、`analysis.md`、`lessons.md`、`known_facts`、`reports/`、生产 pipeline/render/routing/Git/GitHub 字面量或 import 各 0。
7. `engine/evaluation/prospective_evidence.py` 的冻结 baseline byte SHA-256 恰好为 `a503adc310c97e59cdc411b021f127e4687824e73b3004fb34fda2ecb468d416`；IMPLEMENT 后必须对实际 bytes 重算并恰好相等。仅当相等且 §11 的六个 compatibility nodes 全部通过，才能声称本任务未修改该文件且未观察到所选 consumer regression；不得据此声称所有隐藏 consumer 行为不可能变化。

## 10. 当前单元的合成输入与临时链边界

1. 当前单元不含真实案例 locator，不枚举或选择 `cases/`、`META/prospective-go/single-cases`、reports 或其他案例根。
2. 所有 VERIFY 输入必须由测试代码内的 closed、blind-safe、单事件 fixture 显式合成；不得从环境变量、repository case、feedback、known facts、analysis、lessons 或 report 补字段。
3. request、bundle、frozen、release、custody 与 verified-result 链只能写入测试框架提供且由当前测试独占的临时根；该临时根必须创建在 §4.1 已固定的 trusted workspace root 下，并且在 `resolve(strict=True)` 后是该 root 的真实、非 link-like 后代。测试临时根不得替换或重绑定 `_TRUSTED_WORKSPACE_ROOT`；正式 canonical path 规则仍须在该临时根内逐字验证，测试结束只清理当前测试拥有的临时根。
4. 当前单元不得生成仓库 artifact、不得宣称真实 request provenance、真实案例隔离或 real-case full smoke 已证明。
5. 真实案例 closed request provenance + real-case full smoke 的 locator、动态白名单、授权读取根、freshness 与 smoke oracle 由后续独立合同重新冻结；不得从旧 §10 历史文本恢复或隐式继承。

## 11. Exact verification selectors 与实例账本

新增测试文件必须定义以下 11 个 exact test names；参数值按下表冻结，共 31 instances。该表是当前单元唯一可机械收集账本；不得沿用旧 34-instance 声明：

| Test function | Params | Instances |
|---|---:|---:|
| `test_asof_bundle_first_proof_exact_bundle_and_parent_binding` | — | 1 |
| `test_asof_bundle_first_proof_bundle_tamper_fails_closed` | `extra,missing,symlink,parent,hash,marker` | 6 |
| `test_asof_bundle_first_proof_request_closed_validation` | `unknown,identity,daiyun,date` | 4 |
| `test_asof_bundle_first_proof_freeze_delegates_exactly_once` | — | 1 |
| `test_asof_bundle_first_proof_hash_is_process_stable` | — | 1 |
| `test_asof_bundle_first_proof_create_only_paths` | `request,bundle,frozen` | 3 |
| `test_asof_bundle_first_proof_release_parent_is_exact` | `mapping,wrong-schema,tampered` | 3 |
| `test_asof_bundle_first_proof_invalid_release_never_reads_custody` | `hold,tampered,exception` | 3 |
| `test_asof_bundle_first_proof_valid_release_reads_custody_once` | — | 1 |
| `test_asof_bundle_first_proof_event_only_verified_result` | `one-event` | 1 |
| `test_asof_bundle_first_proof_ast_accounting` | `api,imports,calls,paths,cli,evidence-byte,forbidden-static` | 7 |
| **Total** |  | **31** |

移出当前账本且不得被当前 selector 收集：`test_asof_bundle_first_proof_event_only_verified_result[two-events]`、`test_asof_bundle_first_proof_locator_is_single_and_bounded`、`test_asof_bundle_first_proof_real_case_smoke`。前者属于 deferred unit A，后两者整体属于 deferred unit B。

正式 VERIFY commands 与预期 collection：

```text
pytest tests/evaluation/test_prospective_asof.py -q
# collected 31, selected 31, deselected 0

pytest tests/evaluation/test_prospective_asof.py -q -k "asof_bundle_first_proof"
# collected 31, selected 31, deselected 0

pytest \
  tests/asof/test_session_contract.py::test_canonical_bytes_and_sha256_match_literal_oracle \
  tests/asof/test_session_runner.py::test_public_signature_return_contract_and_immutability \
  tests/asof/test_archive_integration.py::test_public_surface_is_exactly_two_module_owned_callables_and_has_no_cli \
  -q
# collected 3, selected 3, deselected 0

pytest \
  tests/evaluation/test_prospective_frozen_run.py::test_single_case_frozen_run_is_complete_unique_parent_bound_grid \
  tests/evaluation/test_prospective_evidence.py::test_release_gate_reads_feedback_only_after_verified \
  tests/evaluation/test_prospective_evidence.py::test_invalid_or_drifted_release_never_invokes_custody_reader \
  tests/evaluation/test_prospective_evidence.py::test_v2_release_collects_immediate_retrospective_from_mixed_frozen_parents \
  tests/evaluation/test_prospective_evidence.py::test_future_observation_reloads_and_binds_actual_question_and_frozen_parent \
  tests/evaluation/test_prospective_evidence.py::test_v2_release_can_anchor_immediate_case_completion \
  -q
# collected 6, selected 6, deselected 0
```

任何 collection 与 31-instance 账本不一致，或收集到 two-event、locator、real-case smoke，均为 selector/collection failure，提供零行为证据并 STOP；不得扩大 selector。测试 oracle 必须从测试临时根中的 actual sealed bytes、独立 canonical projection 与原生领域 API 重建验证，不得复制实现算法。一个现有 instance 可以包含多个相互独立的 oracle；这仍只计一个测试实例，不得把 oracle 数伪增为 instance count。

### 11.1 冻结行为 → selector traceability matrix

下表只把既有冻结行为映射到上述既有 11 names/31 instances及既有 3+6 compatibility nodes；它不新增 selector、参数或实例，也不改变总数。`STATIC_REVIEW` 表示合同/源码静态闭合上限，不是新增动态 selector；`contract unknown` 表示当前账本没有动态证据，禁止编造覆盖。

| 冻结行为 | 既有承担节点 | 直接证据边界 |
|---|---|---|
| 七个 public API 精确签名；fully-qualified AST binding/import/call accounting | `test_asof_bundle_first_proof_ast_accounting[api]`、`[imports]`、`[calls]` | 三个既有 instance 内分别使用多个独立 AST oracle；不增加 instance。只证明目标模块静态 surface/binding/count。 |
| 三条 CLI grammar、exact flags、UTC-Z 整秒/小数秒 grammar | `test_asof_bundle_first_proof_ast_accounting[cli]`；时间行为由 `test_asof_bundle_first_proof_request_closed_validation[date]` 与既有 release/verification 单事件实例内独立 oracle 承担 | `[cli]` 静态闭合三条 grammar；`[date]` 及链路实例只承担其现有可表达的合法文本保留与 UTC instant 比较。不得声称 locale/system-time 的所有平台组合均动态穷举。 |
| 四个 closed status 与单向状态链 | bundle status：`test_asof_bundle_first_proof_exact_bundle_and_parent_binding`；freeze status：`test_asof_bundle_first_proof_freeze_delegates_exactly_once`；release status：`test_asof_bundle_first_proof_release_parent_is_exact[mapping]`；verification status：`test_asof_bundle_first_proof_event_only_verified_result[one-event]` | 四个既有实例各含独立 status oracle；不伪增实例。 |
| trusted root 固定一次、相对 POSIX `artifact_path`、拒绝 absolute/drive/UNC/dot/dotdot/越界/link-like；mapping-only 重读 actual sealed bytes并核对 mapping/document/digest | `test_asof_bundle_first_proof_ast_accounting[paths]`、`test_asof_bundle_first_proof_bundle_tamper_fails_closed[symlink]`、`[parent]`、`[hash]`、`test_asof_bundle_first_proof_release_parent_is_exact[mapping]`、`[tampered]`、`test_asof_bundle_first_proof_invalid_release_never_reads_custody[tampered]` | 只在这些既有 instance 内放多个独立路径/重读 oracle；不得新增路径参数矩阵。未被既有参数逐值枚举的平台路径变体以 STATIC_REVIEW 闭合，不得声称逐变体动态全覆盖。 |
| canonical artifact digest：移除 self-field、指定 JSON 投影、UTF-8 SHA-256、非 JSON-safe/NaN fail-closed | `test_asof_bundle_first_proof_hash_is_process_stable`、`test_asof_bundle_first_proof_bundle_tamper_fails_closed[hash]`、`test_asof_bundle_first_proof_release_parent_is_exact[tampered]`、`test_asof_bundle_first_proof_event_only_verified_result[one-event]` | 现有实例内独立重算各链路 digest；closed JSON 非安全值拒绝仅能在既有 schema/tamper oracle 可承担处验证，其余为 STATIC_REVIEW，不新增参数。 |
| 十二个单路径 error set 的有限性、exit `2`、单类名 stderr 与不泄漏 | `test_asof_bundle_first_proof_ast_accounting[cli]` 加现有 `bundle_tamper` 6、`request_closed_validation` 4、`release_parent_is_exact` 3、`invalid_release_never_reads_custody` 3 的实际失败路径 | `[cli]` 静态断言集合恰好十二个和统一出口；失败实例只证明其实际单路径映射与不泄漏。当前 31-instance 账本不覆盖十二类逐类动态全覆盖；直接证据上限是静态有限闭合加已列单路径，组合优先级仍 deferred C。 |
| 五类 create-only artifact（request/bundle/frozen/release/verified-result）与 orphan | request/bundle/frozen：`test_asof_bundle_first_proof_create_only_paths[request]`、`[bundle]`、`[frozen]`；bundle publication failure seam：`test_asof_bundle_first_proof_bundle_tamper_fails_closed[marker]` 仅在其现有 oracle 真正触发该 seam 时承担 | 当前动态账本只明确证明前三类 create-only。release、verified-result 的 create-only 冲突及 `ORPHANED_SEALED_PREREQUISITE` 保留为后续 STATIC_REVIEW 检查或 contract unknown；若 `[marker]` 未实际触发 orphan seam，也必须记为 contract unknown，不得编造动态证据。 |
| fundamentals=1、events=1 正式 cardinality；不生成 fundamental verification record；event-only record | `test_asof_bundle_first_proof_freeze_delegates_exactly_once`、`test_asof_bundle_first_proof_event_only_verified_result[one-event]` | 前者承担 draft/freeze cardinality，后者承担唯一 event record 且无 fundamental record；不改变 schema、不增加 fundamental selector。 |
| release-before-custody；非法/异常 release reader=0；合法 release reader=1 | `test_asof_bundle_first_proof_invalid_release_never_reads_custody[hold]`、`[tampered]`、`[exception]`；`test_asof_bundle_first_proof_valid_release_reads_custody_once` | 既有四个实例直接承担调用次数和顺序 oracle。 |
| verified record state `VERIFICATION_OPEN`、同一 freeze hash、唯一 event binding | `test_asof_bundle_first_proof_event_only_verified_result[one-event]` | 一个实例内多个独立 oracle，仍计一个 instance。 |
| consumer literal digest与六个 compatibility nodes | `test_asof_bundle_first_proof_ast_accounting[evidence-byte]`；§11 最后一组命令列出的六个既有 compatibility nodes | digest instance 只证明 literal baseline bytes；六 nodes 只证明被选择 consumers，不能推出 hidden consumers 全部不变。另三 compatibility nodes 是 §11 中现有 as-of 3-node 命令，保持原 selector 与计数。 |
| forbidden-static：禁用旧 runner、遍历、业务事实路径/字面量、生产/routing/Git/GitHub | `test_asof_bundle_first_proof_ast_accounting[forbidden-static]` | 只证明既有目标文件静态禁项；不构成 repository-wide 或运行时外部行为证明。 |

上述映射中的 3+6 compatibility nodes 均保持 §11 已冻结的 exact node names：三项 as-of compatibility 与六项 prospective consumer compatibility；它们不计入新增文件的 11 names/31 instances，也不得被改写为动态 selector。

## 12. Falsifiers

以下任一观察推翻 CONTRACT PASS 或后续实现成功声明：

- 新 bundle 仍需 runner 读取 bundle 外命盘、案例、反馈、known facts、analysis、lessons、报告、业务事实环境变量或系统日期；
- identity 映射存在 caller choice 或无法无损构造 `BlindChartInput` / `SessionIdentity`；
- CLI 可注入 draft builder，或 concrete builder 读取 repository context；
- frozen artifact 不含可独立复验的完整 `CareerFreezePackage` projection；
- release 可由摘要字符串、任意 mapping、既有 v1/v2 schema 或非实际 sealed as-of artifact 签发；
- release 验证失败时 custody reader 被调用；
- frozen/release/verified-result 接受零个或多个 event，verified-result 核验 fundamental、漏核验唯一 event、record state 不是 `VERIFICATION_OPEN`，或不绑定同一 freeze hash；
- 相同输入得到不同 freeze hash；
- canonical path 漂移、冲突时覆盖既有 artifact，或 request→bundle 两阶段失败被误报为成功；
- 当前单元枚举或选择真实案例、读取案例业务事实、从环境变量取得业务事实，或写入测试临时根之外的动态 artifact；
- `prospective_evidence.py` bytes 改变，或既有 v1/v2/future/completion consumer 行为改变；
- 必须修改现有静态 bundle schema、静态 `FrozenBlindRun`、`engine/asof/` 或默认生产路径；
- AST count 未解析 fully-qualified binding，或测试只复制实现逻辑；
- 当前 selector 收集 two-event、真实案例 locator 或 real-case full smoke；
- 当前单元声称已证明跨 parser/filesystem/schema 多故障的全局组合错误优先级。

## 13. STOP conditions

命中任一立即停止当前 Gate，不扩大范围：

1. 当前单元需要读取或枚举真实案例、feedback、known facts、analysis、lessons、reports，或需要从环境变量取得业务事实。
2. 当前链需要 event_count 不等于 1，或要求 two-event 动态核算才能闭合。
3. 需要修改用户最新裁决未授权的 Anchor 语义、禁止文件或新增白名单外文件。
4. 需要任意 feedback path 参数、生产默认切换、Git/GitHub、Boulder、部署、发布或 routing。
5. API/schema/path/31-instance selector 不唯一，收集到已 deferred selectors，或同名 artifact 已存在且身份不一致。
6. fresh review 发现隐藏消费者、无法机械核算的单事件调用或 release 保护冲突。
7. 当前证明需要多故障全局优先级；停止并转交 deferred unit C，不在本单元扩张。
8. 任何获授权 VERIFY 命令或测试出现未被合同预期的失败；停止并进入最小诊断，不继续盲修或扩大 selector。当前 CONTRACT 阶段仍禁止运行命令或测试。

## 14. 拆分后的 deferred units

以下三个单元只登记边界，不自动激活其 CONTRACT、IMPLEMENT、测试、案例读取或任何外部操作权限；每个单元都必须另立合同并取得独立授权与 fresh CONTRACT review。

### 14.1 Deferred unit A — two-event 动态核算

- 目标：冻结 event_count=2 时 `open_verification()`、`verification_input_from_mapping()`、`record_career_verification()` 的逐事件动态次数、顺序、失败原子性与 records cardinality oracle。
- 非目标：不重新证明当前单事件链，不引入真实案例，不扩展事业之外领域，不改变原生 API。
- 前置条件：当前单事件 First Proof Point 的 CONTRACT 与必要后续 Gates 独立闭合；另立 exact two-event schema/selector/instance ledger。
- 不得由当前单元推导：不得声称任意多事件受支持、two-event 调用次数正确、部分事件失败语义已证明或批量 readiness 已建立。

### 14.2 Deferred unit B — 真实案例 closed request provenance + real-case full smoke

- 目标：重新冻结真实案例 locator、授权读取根、closed request 的 blind-safe provenance、freshness、动态实例化白名单，以及 actual sealed freeze→release→custody→verified-result full smoke 的证据链。
- 非目标：不读取未获授权 feedback/known facts/analysis/lessons/reports，不把结构 probe 当作事业准确率证据，不切换生产或反馈闭环。
- 前置条件：当前合成单事件链已独立证明；有明确案例读取授权、freshness 标准、closed request 字段来源、唯一机械 locator 与独立 selector ledger。
- 不得由当前单元推导：不得声称任何真实案例可用、request provenance 已闭合、反馈从未被历史流程触碰、real-case smoke 通过或真实事业事实命中。

### 14.3 Deferred unit C — 全局组合错误优先级

- 目标：对 parser/filesystem/schema 及其他验证阶段的多故障组合冻结全局分类排序、组合矩阵、CLI oracle 与非泄漏证明。
- 非目标：不改变十二个错误类名，不改变每个单路径验证阶段与 CLI 出口的稳定映射，不借此扩展 artifact schema。
- 前置条件：当前单路径错误映射已独立闭合；另立可机械收集的多故障矩阵并明确故障注入边界。
- 不得由当前单元推导：不得声称多故障同时存在时输出哪一类、跨阶段排序已证明、所有未知异常均有全局确定顺序。

## 15. Revision State Table

| Revision | Author role reset? | Reviewer role reset? | Verdict | Defect classes found | Repeated? | Anchor drift? |
|---|---|---|---|---|---|---|
| Initial draft | n/a | yes | REVISE | identity、path、draft source、closed schemas、verification scope、locator、selectors/accounting、AST binding、consumer compatibility、signature consistency | no | n/a |
| R1 | yes | yes | REVISE | D1 two-artifact publication lifecycle；D2 envelope ownership/count；D3 literal consumer digest；D4 exact error names；D5 deterministic draft oracle；D6 record projection | no：均为残余闭合缺口，未裁定为已修复类别重现 | semantic conflict：§8 与 §9 的 envelope ownership 不一致；Anchor Ledger 文本未改 |
| R2 | yes | yes | REVISE | D1 manifest publication + orphan representation；D4 orphan error mapping；D5 citation locator；ACCOUNT transition/canonical-byte counts；ANCHOR provenance | yes：D1/D4/D5/accounting | ambiguous：缺独立 baseline provenance；未观察到具体集合漂移 |
| R2-LP1 | yes（用户明确 literal-only 授权） | yes | PASS | literal-only 缺口闭合；随后进入 IMPLEMENT，并在三轮 fresh STATIC_REVIEW 后仍为 REVISE | no | no |
| R3-SPLIT1 | yes（重置 CONTRACT ANALYST；用户明确拆分授权） | yes（fresh reset） | REVISE | fresh review 七项意见；Anchor adjudication 分类 `B/B/A/C/C/B/A` | pending | 含 REVIEWER_ANCHOR_DRIFT；交由用户裁决 |
| R3-ANCHOR-A | yes（freshly reset literal-patch author；用户批准方案 A） | yes（fresh reset） | REVISE | trusted-root locator/初始化/缓存及测试临时根后代关系未机械闭合；UTC-Z regex 的小数点未转义 | yes：trusted-root 同类路径缺陷修复后重现，触发 literal-only repair | no：未改变用户方案 A 或其他 Anchor |
| R3-ANCHOR-A-LP1 | yes（freshly reset literal-patch author） | yes（logically fresh reset） | PASS | trusted-root 唯一 import-time 初始化/private cache/API-CLI 共用/测试临时根后代规则与 normative UTC-Z escaped literal dot 均机械闭合；§16 十问全部通过 | no | no：七 API、五项拟议 whitelist、fundamental record 边界、11 names/31 instances 均未改变 |

R2 fresh review 触发 repeated-defect/ambiguous-anchor stop，失败历史保留。用户随后授权 R2-LP1 literal patch；R2-LP1 logically fresh CONTRACT review 获得 PASS，继而完成 IMPLEMENT，并在三轮 fresh STATIC_REVIEW 后仍为 REVISE，命中默认修订上限。用户此后明确批准拆分：当前单元只保留单事件正式链，三个 deferred concerns 分立合同。R3-SPLIT1 fresh review 的 verdict 为 REVISE；用户随后以 `B/B/A/C/C/B/A` 完成 Anchor adjudication并批准方案 A。R3-ANCHOR-A 只修 `A/C/A` 项并拒绝 B 类 drift；其 logically fresh review 仍为 REVISE，唯一发现 trusted-root 机械定义/测试临时根关系缺口与 UTC-Z regex 未转义，其中 trusted-root 同类缺陷修复后重现，故进入 literal-only repair。R3-ANCHOR-A-LP1 只闭合这两项文本缺口，不删除或改变既有五项拟议 whitelist，不把 fundamental verification 扩大为 fundamental record，不改变 11 names/31 instances，不新增动态 selector。R3-ANCHOR-A-LP1 logically fresh CONTRACT review 获得 PASS；该 PASS 仅允许后续另行派生最窄 IMPLEMENT scope，不证明实现或测试。它不撤销 R2-LP1 历史 CONTRACT PASS，也不抹除其后 IMPLEMENT、三轮 STATIC_REVIEW REVISE、Initial/R1/R2/R3-SPLIT1/R3-ANCHOR-A REVISE 与 repeated-defect 历史。deferred A/B/C、永久 GitHub 禁令及其他 Anchor 保持不变。按本轮明确边界，当前停止于 CONTRACT PASS，不进入 IMPLEMENT。

## 16. Fresh CONTRACT review 问题

fresh reviewer 必须重置角色，只使用完整 R3-ANCHOR-A-LP1、用户最新 Anchor adjudication与方案 A、保留的历史 verdict、Anchor baseline 与必要原始事实，独立回答：

1. 当前正式 schema 与 frozen/release/verified-result 是否始终冻结 fundamentals=1、events=1，并拒绝零个或多个 event；“不核验 fundamentals”是否只澄清为不生成 fundamental verification record而未扩大 record schema？
2. `collect_asof_verification()` 在 event_count=1 时是否对 `open_verification()`、`verification_input_from_mapping()`、`record_career_verification()` 各恰好调用一次，record state 是否唯一为 `VERIFICATION_OPEN`？
3. request JSON 与 directory bundle 的两阶段 create-only lifecycle、orphan STOP、canonical path/parent/hash/time、chart 原 bytes 是否仍机械闭合？
4. 七个 public APIs 是否保持签名不变；trusted root 是否唯一由 `engine.evaluation.prospective_asof` 首次 import 时的 `Path.cwd().resolve(strict=True)` 初始化并缓存于不可重绑定的 private module-level constant，API/CLI 是否共享该值且后续 cwd 不影响它；测试临时根是否必须是该 root 下 resolve 后真实、非 link-like 后代；stored path 与 mapping-only actual sealed bytes重读是否 fail-closed；UTC-Z grammar 是否使用转义后的 literal dot，合法原文本保留与 UTC instant 比较是否闭合且不依赖 locale/system time？
5. 31-instance exact ledger 是否唯一可机械收集，traceability matrix 是否只映射现有 11 names/31 instances及3+6 nodes，并彻底排除新增 selector、two-event、locator 与 real-case full smoke selectors？
6. 当前输入是否只来自测试内合成 fixture 与临时链，且不枚举真实案例、不依赖环境变量业务事实、不创建仓库 artifact？
7. 十二个 error names 是否保持 finite；每个验证阶段与 CLI 单路径出口是否稳定、不泄漏，同时没有虚称全局组合优先级已证明？
8. consumer literal SHA-256 baseline 与六个 compatibility nodes 是否保留，且没有夸大 hidden consumer 结论？
9. deferred units A/B/C 是否各自说明目标、非目标、前置条件和禁止推导，并明确不会自动激活？
10. 是否仍有条款要求当前单元 two-event、真实案例 full smoke、环境变量 request、全局组合错误优先级，或暗中授予 IMPLEMENT、测试、反馈读取、Git/GitHub、部署、发布、routing、production switch 权限？

## 17. 当前 Gate record

```text
Gate: CONTRACT
Owner role: freshly reset CONTRACT literal-patch author（R3-ANCHOR-A-LP1 authoring complete；停止）
Fresh reviewer role: logically fresh CONTRACT reviewer（complete；停止）
Authorization envelope: 用户明确授权仅修改本合同；R3-ANCHOR-A fresh REVISE 后只允许机械化 trusted-root 初始化/缓存/测试临时根关系并转义 UTC-Z regex 的 literal dot；B drift 与其他改动明确拒绝
Activation condition: R3-ANCHOR-A fresh REVISE 已锁定并完成两项 literal-only repair，且 logically fresh CONTRACT review 已完成（已满足）
Remaining inactive grants: IMPLEMENT/test/CLI/locator/build/case-read/feedback-read/artifact/Git/GitHub/deploy/release/routing/production switch 均未由本轮激活；GitHub 服务端变更永久禁止
Required inputs: Initial/R1/R2/R2-LP1/R3-SPLIT1/R3-ANCHOR-A 历史、R3-ANCHOR-A fresh review REVISE、Anchor adjudication `B/B/A/C/C/B/A`、用户批准方案 A、冻结 Anchor、R3-ANCHOR-A-LP1 全文与 logically fresh reviewer verdict
Observed facts: logically fresh reviewer 对 §16 十问逐项审查并返回 PASS；确认 R3-ANCHOR-A-LP1 保持七 API 签名、五项拟议 whitelist、fundamentals=1/events=1 与 11 names/31 instances，trusted root 的唯一 import-time 初始化/private cache/API-CLI 共用/测试临时根后代关系及 normative UTC-Z escaped literal dot 均机械闭合；mapping actual sealed bytes重读、canonical artifact digest、行为→selector traceability与 deferred A/B/C 保持；未修改实现/测试/其他文件；未运行测试、CLI或 build；未读取案例、feedback、known facts、analysis、lessons、reports；未创建 artifact；未执行 Git/GitHub/部署/发布/routing
Inferences: R3-ANCHOR-A-LP1 CONTRACT Gate PASS，仅允许另行派生最窄 IMPLEMENT scope；不代表实现正确或测试通过
Unknowns: 后续 IMPLEMENT 可行性与实际差距；STATIC_REVIEW/VERIFY 结论；deferred units 各自未来合同结论
Required output: CONTRACT PASS ledger persistence
Falsifiers: §12
STOP conditions: §13
Verdict: PASS
Direct evidence boundary: 只证明 R3-ANCHOR-A-LP1 合同文本经 logically fresh reviewer 按 §16 十问及 CONTRACT Gate 审查通过
Forbidden inference boundary: 不证明 CONTRACT PASS、实现可行、测试通过、create-only/orphan 未覆盖项、十二错误逐类动态全覆盖、two-event、真实案例 provenance/full smoke、全局组合错误优先级、案例可用或事业预测有效
Minimum next authorization: 本轮停止于 CONTRACT PASS；后续仅可另行派生最窄 IMPLEMENT alignment scope
```

唯一下一合法动作：停止 CONTRACT author/reviewer roles并保留 PASS ledger；按本轮明确边界不得进入 IMPLEMENT。后续只有在重新激活 IMPLEMENT 时，才可从本合同派生最窄 alignment scope；仍不得提前运行测试/CLI/locator/build、读取案例或受保护事实、创建正式 artifact，或执行 Git/GitHub/部署/发布/routing/production switch。
