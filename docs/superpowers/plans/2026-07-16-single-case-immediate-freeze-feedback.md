# Single-Case Immediate Freeze and Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立每案当天独立完成正式 intake、短期未来问题预注册、盲包、六来源冻结、独立见证验证后即时回顾释放，并按每 10 个完成案只引用不可变父制品计算两个新门禁的完整 prediction-first 评估链。

**Architecture:** 将不可逆证明点下沉到单案：`engine.evaluation.prospective_artifacts` 负责内容摘要、不可覆盖和父链，`engine.evaluation.prospective_evidence` 负责两类证据分账与反馈释放，`engine.evaluation.prospective_gates` 负责 cohort 和门禁纯计算；现有 `tools.school_capability_dataset`、`tools.school_capability_prospective`、`tools.school_capability_review` 只作为文件/CLI adapter。工程与测试完成后再迁移首案；独立人类见证人在其临时 `cmd.exe` 中亲自签署和验证，验证成功处设置人工硬停点，agent 永不创建、读取、传递或知晓真实 witness key。

**Tech Stack:** Python 3、stdlib `dataclasses` / `datetime` / `hashlib` / `hmac` / `json` / `pathlib` / `tempfile`、现有 `engine.evaluation` / `engine.claims`、pytest、Windows 10 `cmd.exe`。

## Global Constraints

- 完整 case ID 固定为 `P-GO-YYYY-NNN-{乾|坤}-{四柱}`；编号在授权入组时分配，失败后不得复用，路径不得包含 PII。
- 单案根固定为 `META/prospective-go/single-cases/<case_id>/`；正式制品采用 `<case_id>--<artifact-kind>--vNNN.json`，已存在目标不得覆盖、追加或改名复用。
- 每个 JSON 制品必须含 `schema_version`、`case_id`、`subject_id_hash`、`created_at`、`artifact_sha256` 和直接父制品的 `artifact_path` / `artifact_sha256`；摘要计算排除自身 `artifact_sha256`。
- `v002+` 必须显式包含 `supersedes`、`supersedes_sha256`、`reason`、`approved_by`；旧版本永久保留。
- 所有写操作必须先 `--dry-run`；dry-run 不写盘；正式写使用不存在的目标并以同目录临时 sibling 原子发布。
- 正式 intake 恰好只含一个 record，并只消费脱敏预测输入；经历、当前现状、反馈、标签、旧报告和 known facts 在签名验证前不得进入 runner 边界。
- 单案 blind bundle 白名单精确为 `intake.json`、`tasks.json`、`rule-snapshot.json`、`future-question.json`、`bundle-manifest.json`、`cases/<case_id>/chart.json`；case 集恰为一，schools 恰为 `ziping`、`ditiansui`、`duan`、`ren`、`gao`、`yang`。
- 每案 freeze 前必须预注册恰好 1 个 binary 短期未来问题；`observation_window.start_at=freeze_at`，`end_at` 晚于 freeze 且不超过 freeze 后三个月。
- 六来源三态 `claim` / `abstain` / `unsupported` 全部保留；timing claim 必须引用真实 `liunian_steps`，不得补造。
- witness、intake operator、runner operator、outcome custodian、reviewer A/B、adjudicator 必须满足规格的角色隔离；签署与验证是两个独立门。
- 真实 witness key 只能由独立人类见证人在新开的本机临时 `cmd.exe` 会话中输入；agent 不得创建、索取、读取、接收、传递、记录、回显或知晓真实 key，也不得把 key 写入参数、仓库、日志、截图、聊天或 CI。
- 测试只能使用显式标记为 fixture 的假 key；任何生产/首案命令只引用环境变量名 `SCHOOL_CAPABILITY_WITNESS_KEY`，不得包含值。
- freeze verification 必须重新读取实际 intake、bundle manifest、frozen run、witness registry 和见证方仓库外保存的 registry root；只有新 verification 制品 `status=VERIFIED` 才允许生成反馈释放凭证。
- 验证前不得打开反馈文件、请求反馈正文、创建 `feedback.md`、即时回顾、observation、report 或 label；门禁失败不得创建空反馈制品。
- 即时回顾固定为 `evidence_class=prediction_first_immediate_retrospective`；未来观察固定为 `evidence_class=future_observation`；不确定、失访、冲突未决、窗口未结束固定为 `no_data`。
- 即时回顾与未来观察必须使用不同制品、不同全局唯一 `label_identity` 和不同完成计数；同一事实不得跨 evidence class 复制计数。
- 三项高风险任务固定为 `marriage.divorce_or_remarriage`、`wealth.debt`、`health.system_risk`；两名不同人类独立复核，冲突由第三方仲裁，未来账不得复用即时回顾审查。
- `prediction_capability_candidate_gate_v1` 仅消费即时回顾：20 独立完成命主、至少一个任务 15 条有效正反例、`calibration_error < 0.2`、高风险双审/仲裁、竞争记录不少于 5、`selection_change_count >= 1`、`learned_utility >= static_utility` 和全部审计同时满足才为 GO。
- `future_empirical_gate_v1` 仅消费未来观察：10 独立到期完成命主、至少一个同类 `future_task_id` 8 条有效正反例，其余校准、高风险、竞争、selection change、utility 和审计门槛不变且无 `not_applicable` 豁免。
- `historical_platform_baseline_2026_07_15` 与两个新门禁使用不同 `gate_id`、计数和证据；不得以 `20 immediate + 10 future = 30` 冲抵原 30 案 baseline。
- `META/six-month-platform-gate-2026-07-15.md` 与 `META/six-month-platform-gate-2026-07-15.json` 必须保持字节不变；实现前后复算 SHA-256。
- cohort 仅在 10 个唯一、未 STOP、`CASE_COMPLETE_FOR_RETROSPECTIVE` 单案满足时创建；manifest 对父制品只记录仓库相对路径与 SHA-256，不复制或改写父制品。
- 泄漏、identity 冲突、hash 失配、角色隔离破坏进入 `STOPPED_CONTAMINATED`；非污染环境/操作失败进入 `RECOVERABLE_HOLD`，只能从最后一个已验证不可变父制品向前派生。
- 任一 GO 只创建不可变门禁结果和升级提案；不得修改 `run_pipeline()`、`DEFAULT_RUNNER_REGISTRY`、默认 static routing、生产权重、生产规则、评分公式或历史 snapshot。
- `tools.feedback_ingest.py` 仍是生产反馈唯一入口；评估即时回顾/未来观察不得自动触发生产学习。
- 所有命令使用 Windows 10 默认 `cmd.exe` 语法；命令连接使用 `&&`，环境变量使用 `set "NAME=value"` / `set "NAME="`，不使用 Unix shell 命令。
- 本计划文件本身不提交；每个实施 Task 完成并通过 GREEN 后单独提交，首案真实数据制品是否提交仍服从当次人工批准和工作树范围审查。

---

## File Responsibility Map

| File | Action | Single responsibility |
|---|---|---|
| `engine/evaluation/prospective_artifacts.py` | Create | 单案命名、canonical SHA-256、父引用、不可覆盖版本和原子发布纯契约。 |
| `engine/evaluation/prospective_single_case.py` | Create | 单案 intake、future question、bundle/freeze 链的 schema 与状态验证。 |
| `engine/evaluation/prospective_evidence.py` | Create | verification、反馈释放凭证、即时回顾、未来观察、completion 的 evidence-class 分账。 |
| `engine/evaluation/prospective_gates.py` | Create | 10 案 cohort manifest、两个新门禁与 historical baseline 只读引用的纯计算。 |
| `tools/school_capability_dataset.py` | Modify | 将既有 intake/bundle adapter 接入单案契约，新增 future question、verification、release/evidence CLI。 |
| `tools/school_capability_prospective.py` | Modify | 强制单案 bundle、六来源完整网格、三段 witness 链和外部 root 验证。 |
| `engine/evaluation/high_risk_review.py` | Modify | 让 review identity 绑定 evidence class、label identity、packet SHA-256 和角色集合。 |
| `tools/school_capability_review.py` | Modify | 对即时/未来 packet 复用双审/仲裁 CLI，拒绝跨账复用。 |
| `tools/school_capability_cohort.py` | Create | cohort build/score/gate/report CLI，只展开父引用，不写生产入口。 |
| `templates/prospective-immediate-retrospective-v1.json` | Create | verification 后生成的即时回顾采集模板，不含预测文本。 |
| `templates/prospective-future-question-v1.json` | Create | 每案恰好一个三个月 binary future question 模板。 |
| `tests/evaluation/test_prospective_artifacts.py` | Create | 命名、hash、父链、不可覆盖、v002 和 STOP/HOLD 测试。 |
| `tests/evaluation/test_single_case_workflow.py` | Create | 单案 intake/bundle/freeze/witness verification/释放顺序测试。 |
| `tests/evaluation/test_prospective_evidence.py` | Create | 即时回顾、未来观察、no_data、完成计数和反馈不可预读测试。 |
| `tests/evaluation/test_prospective_cohort.py` | Create | 10 案父引用、分账 score、漂移 STOP、确定性测试。 |
| `tests/evaluation/test_prospective_gates.py` | Create | 20/15 与 10/8 两套 GO/HOLD 边界、baseline 隔离测试。 |
| `tests/evaluation/test_high_risk_review.py` | Modify | evidence class 双审、仲裁与禁止复用测试。 |
| `tests/evaluation/test_prospective_gate_workflow.py` | Modify | 新协议、模板、首案迁移和旧短槽位兼容测试。 |
| `tests/evaluation/test_prospective_frozen_run.py` | Modify | 单案六来源网格、三段 witness 与 verification 测试。 |
| `tests/test_production_entrypoints_unchanged.py` | Create | 锁定生产入口函数签名、runner registry 和历史门禁摘要。 |
| `META/prospective-intake-protocol-v1.md` | Modify | 将批量正式 intake 改为逐案当天链，定义两个新 gate identity。 |
| `plans/upgrade-guides/post-gate-action-plan-2026-07-15.md` | Modify | Task 3—11 改为单案节奏、future question 与双门禁消费。 |
| `tools/README.md` | Modify | 登记单案与 cohort 命令、见证人终端边界和硬停点。 |
| `handoff.md` | Modify | 下一步改为首案单案链，分别列三个门禁 HOLD 与首案人工硬停点。 |
| `META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/` | Create during approved execution | 首案不可变正式制品；先到 verification，硬停确认后才允许即时回顾。 |

## Phase 1: Immutable Single-Case Engineering

### Task 1: Immutable artifact identity and publication

**Files:**
- Create: `engine/evaluation/prospective_artifacts.py`
- Create: `tests/evaluation/test_prospective_artifacts.py`

**Interfaces:**
- Consumes: repository-relative `Path`, JSON-compatible `Mapping[str, Any]`.
- Produces: `ArtifactRef`, `canonical_artifact_sha256()`, `single_case_artifact_path()`, `validate_parent_ref()`, `publish_new_json()`.

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path
import pytest
from engine.evaluation.prospective_artifacts import (
    ArtifactRef, canonical_artifact_sha256, publish_new_json,
    single_case_artifact_path, validate_parent_ref,
)

CASE_ID = "P-GO-2026-001-坤-壬戌己酉乙卯丁亥"

def test_single_case_name_and_hash_exclude_self_digest(tmp_path: Path) -> None:
    path = single_case_artifact_path(tmp_path, CASE_ID, "intake", 1)
    assert path.name == f"{CASE_ID}--intake--v001.json"
    payload = {"schema_version": "x/v1", "case_id": CASE_ID,
               "artifact_sha256": "0" * 64}
    assert canonical_artifact_sha256(payload) == canonical_artifact_sha256(
        {**payload, "artifact_sha256": "f" * 64})

def test_publish_is_create_only_and_parent_hash_is_recomputed(tmp_path: Path) -> None:
    target = single_case_artifact_path(tmp_path, CASE_ID, "intake", 1)
    payload = {"schema_version": "x/v1", "case_id": CASE_ID,
               "subject_id_hash": "a" * 64, "created_at": "2026-07-16T00:00:00Z",
               "parents": []}
    ref = publish_new_json(target, payload, dry_run=False)
    assert ref.artifact_path == target.as_posix()
    with pytest.raises(ValueError, match="already exists"):
        publish_new_json(target, payload, dry_run=False)
    validate_parent_ref(ArtifactRef(ref.artifact_path, ref.artifact_sha256))
```

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/evaluation/test_prospective_artifacts.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'engine.evaluation.prospective_artifacts'`.

- [ ] **Step 3: Implement the minimal immutable primitives**

```python
@dataclass(frozen=True)
class ArtifactRef:
    artifact_path: str
    artifact_sha256: str


def canonical_artifact_sha256(payload: Mapping[str, Any]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "artifact_sha256"}
    encoded = json.dumps(unsigned, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def single_case_artifact_path(root: Path, case_id: str,
                              artifact_kind: str, version: int) -> Path:
    if not re.fullmatch(r"P-GO-\d{4}-\d{3}-[乾坤]-[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]{8}", case_id):
        raise ValueError("invalid prospective case_id")
    if version < 1 or not re.fullmatch(r"[a-z][a-z0-9-]*", artifact_kind):
        raise ValueError("invalid artifact identity")
    return Path(root) / case_id / f"{case_id}--{artifact_kind}--v{version:03d}.json"


def publish_new_json(path: Path, payload: Mapping[str, Any], *, dry_run: bool) -> ArtifactRef:
    digest = canonical_artifact_sha256(payload)
    document = {**payload, "artifact_sha256": digest}
    if dry_run:
        return ArtifactRef(path.as_posix(), digest)
    if path.exists() or path.is_symlink():
        raise ValueError(f"output already exists: {path}")
    if path.exists() or path.is_symlink():
        raise ValueError(f"output already exists: {path}")
    if dry_run:
        return ArtifactRef(path.as_posix(), digest)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            json.dump(document, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists() or path.is_symlink():
            raise ValueError(f"output already exists: {path}")
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise
    return ArtifactRef(path.as_posix(), digest)
```

Implement `validate_parent_ref(ref: ArtifactRef) -> dict[str, Any]` by reading the parent, checking its stored digest and recomputing the canonical digest. Implement `validate_revision_metadata(payload, version)` so `version > 1` requires exact `supersedes`, `supersedes_sha256`, `reason`, `approved_by` fields and a named human approver.

- [ ] **Step 4: Run GREEN and edge cases**

Run: `python -m pytest tests/evaluation/test_prospective_artifacts.py -q`

Expected: PASS, including dry-run writes nothing, symlink rejection, parent byte drift rejection, v002 metadata enforcement, and v001 preservation.

- [ ] **Step 5: Commit**

```bat
git add engine/evaluation/prospective_artifacts.py tests/evaluation/test_prospective_artifacts.py
git commit -m "feat: add immutable prospective artifact chain"
```

### Task 2: Single-record intake and exactly one future question

**Files:**
- Create: `engine/evaluation/prospective_single_case.py`
- Modify: `tools/school_capability_dataset.py:683-934`
- Create: `templates/prospective-future-question-v1.json`
- Create: `tests/evaluation/test_single_case_workflow.py`
- Modify: `tests/evaluation/test_prospective_gate_workflow.py:307-476`

**Interfaces:**
- Consumes: existing `register_prospective_intake(...) -> dict[str, Any]`, canonical chart parser, frozen task/rule hashes, one future-question draft.
- Produces: `build_single_case_intake(input_file, tasks, schools, operator, tasks_by_case, future_question, created_at) -> tuple[dict[str, Any], dict[str, Any]]`; `validate_future_question_registration(document, *, freeze_at=None) -> dict[str, Any]`.

- [ ] **Step 1: Write failing tests for one-record and future-question invariants**

```python
def test_single_intake_has_one_record_and_one_future_question(input_path, tasks) -> None:
    intake, question = build_single_case_intake(
        input_path, tasks, SIX_SCHOOLS, "human-intake-01",
        {"P-GO-2026-001": ["career.role_change", "career.change_window"]},
        {"future_task_id": "career.role_change.3m",
         "question_text_redacted": "未来三个月是否发生显著岗位角色变化？",
         "outcome_type": "binary", "positive_definition": "发生并有雇佣资料或本人确认",
         "negative_definition": "完整窗口结束且核验来源确认未发生",
         "verification_source_requirements": ["custody://structured-interview"],
         "observation_window": {"start_at": "2026-07-16T00:00:00Z",
                                "end_at": "2026-10-16T00:00:00Z"}},
        created_at="2026-07-16T00:00:00Z")
    assert len(intake["records"]) == 1
    assert intake["future_question"]["artifact_sha256"] == question["artifact_sha256"]

@pytest.mark.parametrize("questions", [[], [{"future_task_id": "a"}, {"future_task_id": "b"}]])
def test_single_intake_rejects_question_count_not_one(input_path, tasks, questions) -> None:
    with pytest.raises(ValueError, match="exactly one future question"):
        build_single_case_intake(
            input_path, tasks, SIX_SCHOOLS, "human-intake-01",
            {"P-GO-2026-001": ["career.role_change"]}, questions,
            created_at="2026-07-16T00:00:00Z")
```

Also assert duplicate `subject_id_hash` against an existing intake index rejects a changed case ID; forbidden feedback markers reject before publication; the existing ten short-slot table still uniquely maps the full case ID while future slots do not enter the single intake.

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/evaluation/test_single_case_workflow.py tests/evaluation/test_prospective_gate_workflow.py -q`

Expected: FAIL because `build_single_case_intake` and the future-question schema do not exist.

- [ ] **Step 3: Implement the minimal typed builders**

```python
SIX_SCHOOLS: tuple[str, ...] = ("ziping", "ditiansui", "duan", "ren", "gao", "yang")


def build_single_case_intake(
    input_file: Path,
    tasks: dict[str, Any],
    schools: Sequence[str],
    operator: str,
    tasks_by_case: dict[str, list[str]],
    future_question: Mapping[str, Any],
    *,
    created_at: str,
    existing_subject_hashes: AbstractSet[str] = frozenset(),
) -> tuple[dict[str, Any], dict[str, Any]]:
    batch = register_prospective_intake([input_file], tasks, list(schools), operator,
                                        tasks_by_case=tasks_by_case)
    if len(batch["records"]) != 1 or tuple(batch["schools"]) != SIX_SCHOOLS:
        raise ValueError("single-case intake requires one record and exactly six schools")
    row = batch["records"][0]
    if row["subject_id_hash"] in existing_subject_hashes:
        raise ValueError("duplicate subject_id_hash")
    question = build_future_question_registration(row, future_question, created_at=created_at)
    question_ref = ArtifactRef(question["artifact_path"], question["artifact_sha256"])
    intake_payload = {
        "schema_version": "prospective-single-case-intake/v1",
        "case_id": row["case_id"],
        "subject_id_hash": row["subject_id_hash"],
        "created_at": created_at,
        "operator": operator,
        "schools": list(SIX_SCHOOLS),
        "task_catalog_sha256": batch["task_catalog_sha256"],
        "records": [row],
        "future_question": asdict(question_ref),
        "parents": [asdict(question_ref)],
    }
    intake = {**intake_payload,
              "artifact_sha256": canonical_artifact_sha256(intake_payload)}
    return intake, question
```

Use an explicit schema `prospective-future-question/v1`, validate binary definitions and source requirements, parse UTC timestamps, and use calendar-month addition so `end_at <= freeze_at + 3 calendar months` is mechanical. Do not guess a future question from the chart.

- [ ] **Step 4: Add CLI wiring and run GREEN**

Add `single-case-intake` arguments `--input --tasks --school --operator --tasks-by-case --future-question --case-root --created-at --dry-run`; dry-run emits both documents and paths, formal mode publishes future question and intake into new paths without overwriting.

Run: `python -m pytest tests/evaluation/test_single_case_workflow.py tests/evaluation/test_prospective_gate_workflow.py tests/evaluation/test_dataset.py -q`

Expected: PASS; existing multi-input helper tests remain compatible, while the new formal CLI refuses more than one input.

- [ ] **Step 5: Commit**

```bat
git add engine/evaluation/prospective_single_case.py tools/school_capability_dataset.py templates/prospective-future-question-v1.json tests/evaluation/test_single_case_workflow.py tests/evaluation/test_prospective_gate_workflow.py
git commit -m "feat: register one prospective case and future question"
```

### Task 3: Single-case blind bundle

**Files:**
- Modify: `engine/evaluation/prospective_single_case.py`
- Modify: `tools/school_capability_dataset.py:806-934`
- Modify: `tests/evaluation/test_single_case_workflow.py`
- Modify: `tests/evaluation/test_dataset.py:353-445`

**Interfaces:**
- Consumes: `validate_single_case_intake()`, verified future-question parent, task catalog and rule snapshot.
- Produces: `prepare_single_case_blind_bundle(intake, future_question, tasks_path, rule_snapshot_path, target_dir, dry_run) -> dict[str, Any]`.

- [ ] **Step 1: Write failing whitelist and STOP tests**

```python
def test_bundle_has_exact_single_case_whitelist(single_case_intake, question, tmp_path) -> None:
    manifest = prepare_single_case_blind_bundle(single_case_intake, question, TASKS, RULES,
                                                tmp_path / "bundle", dry_run=False)
    case_id = single_case_intake["case_id"]
    assert set(manifest["files"]) == {
        "intake.json", "tasks.json", "rule-snapshot.json", "future-question.json",
        f"cases/{case_id}/chart.json",
    }
    assert manifest["case_count"] == 1
    assert manifest["future_question_count"] == 1

@pytest.mark.parametrize("extra", ["feedback.json", "report.md", "known-facts.json", "input.md"])
def test_bundle_extra_revealed_file_is_stop(bundle, extra) -> None:
    (bundle / extra).write_text("revealed", encoding="utf-8")
    with pytest.raises(ContaminationError):
        verify_single_case_bundle(bundle)
```

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/evaluation/test_single_case_workflow.py::test_bundle_has_exact_single_case_whitelist tests/evaluation/test_dataset.py -q`

Expected: FAIL because the current bundle lacks `future-question.json` and allows multiple records.

- [ ] **Step 3: Implement the minimal bundle adapter**

```python
def prepare_single_case_blind_bundle(
    intake: Mapping[str, Any], future_question: Mapping[str, Any],
    tasks_path: Path, rule_snapshot_path: Path, target_dir: Path,
    *, dry_run: bool,
) -> dict[str, Any]:
    row = validate_single_case_intake(intake)
    validate_future_question_parent(future_question, intake)
    prepare_blind_bundle(dict(intake), tasks_path, rule_snapshot_path,
                         target_dir, dry_run=True)
    files = materialize_safe_files(
        intake=intake, future_question=future_question,
        tasks_path=tasks_path, rule_snapshot_path=rule_snapshot_path)
    assert_exact_whitelist(files, row["case_id"])
    return publish_bundle_directory_create_only(target_dir, files, dry_run=dry_run)
```

Manifest includes `case_count=1`, `future_question_count=1`, sorted six schools, parent refs, per-file SHA-256 and bundle SHA-256. Any forbidden name/content, symlink, extra file, mismatched parent or changed intake becomes STOP rather than recoverable HOLD.

- [ ] **Step 4: Run GREEN**

Run: `python -m pytest tests/evaluation/test_single_case_workflow.py tests/evaluation/test_dataset.py -q`

Expected: PASS; dry-run writes no directory; a repeated formal call leaves the first bundle byte-identical.

- [ ] **Step 5: Commit**

```bat
git add engine/evaluation/prospective_single_case.py tools/school_capability_dataset.py tests/evaluation/test_single_case_workflow.py tests/evaluation/test_dataset.py
git commit -m "feat: build whitelist-only single case blind bundle"
```

### Task 4: Single-case staged frozen run

**Files:**
- Modify: `engine/evaluation/prospective_single_case.py`
- Modify: `tools/school_capability_prospective.py:41-213`
- Modify: `tests/evaluation/test_prospective_frozen_run.py`

**Interfaces:**
- Consumes: `verify_single_case_bundle(root) -> VerifiedSingleCaseBundle`, existing `generate_blind_outputs()` and `freeze_outputs()`.
- Produces: `build_single_case_staged_frozen_run(bundle_root: Path) -> dict[str, Any]` with a complete unique six-school × assigned-task grid.

- [ ] **Step 1: Write failing matrix and parent-binding tests**

```python
def test_single_case_frozen_run_is_complete_unique_grid(single_bundle: Path) -> None:
    artifact = build_single_case_staged_frozen_run(single_bundle)
    assignments = artifact["case_task_assignments"]
    task_count = len(assignments[0]["task_ids"])
    outputs = artifact["frozen_run"]["outputs"]
    assert len(outputs) == 6 * task_count
    assert len({(r["case_id"], r["school_id"], r["task_id"]) for r in outputs}) == len(outputs)
    assert {r["state"] for r in outputs} <= {"claim", "abstain", "unsupported"}
    assert artifact["future_question_registration_sha256"] == read_question_sha(single_bundle)
```

Add negative tests for two cases, duplicate output identity, missing school, future-question hash drift, timing claim without `liunian_steps` reference, and byte change in intake/bundle/rule/task parent.

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/evaluation/test_prospective_frozen_run.py -q`

Expected: FAIL because current `build_staged_frozen_run()` accepts multiple cases and does not bind the future question.

- [ ] **Step 3: Implement the single-case wrapper and strict grid check**

```python
def build_single_case_staged_frozen_run(bundle_root: Path) -> dict[str, Any]:
    verified = verify_single_case_bundle(bundle_root)
    artifact = build_staged_frozen_run(bundle_root)
    if len(artifact["case_task_assignments"]) != 1:
        raise ValueError("single-case frozen run requires exactly one case")
    assert_complete_six_source_grid(artifact, schools=SIX_SCHOOLS)
    assert_timing_claims_reference_liunian(artifact, verified.chart)
    return seal_child_artifact(artifact, parents=verified.parent_refs,
                               future_question_registration_sha256=verified.future_question_sha256)
```

Expose CLI `stage-single-case-frozen-run`; keep existing `stage-frozen-run` for read compatibility but update operational docs to use the single-case command.

- [ ] **Step 4: Run GREEN**

Run: `python -m pytest tests/evaluation/test_prospective_frozen_run.py tests/claims/test_multi_school_freeze.py -q`

Expected: PASS; deterministic rerun returns identical content before publication; formal output refuses overwrite.

- [ ] **Step 5: Commit**

```bat
git add engine/evaluation/prospective_single_case.py tools/school_capability_prospective.py tests/evaluation/test_prospective_frozen_run.py
git commit -m "feat: freeze one prospective case with six source grid"
```

### Task 5: Witness three-segment verification and feedback-release credential

**Files:**
- Create: `engine/evaluation/prospective_evidence.py`
- Modify: `tools/school_capability_prospective.py:216-374`
- Modify: `tools/school_capability_dataset.py:1017-1126`
- Modify: `tests/evaluation/test_prospective_frozen_run.py`
- Create: `tests/evaluation/test_prospective_evidence.py`

**Interfaces:**
- Consumes: actual intake path, bundle root, frozen run path, witness registry path, `witness_key: bytes` only inside witness-held process, `expected_external_root: str` supplied by witness.
- Produces: `verify_single_case_freeze_chain(...) -> dict[str, Any]`; `build_feedback_release_credential(verification, roles, leakage_scan) -> dict[str, Any]`.

- [ ] **Step 1: Write failing verification and no-pre-read tests**

```python
def test_release_gate_reads_feedback_only_after_verified(parents, monkeypatch) -> None:
    opened: list[Path] = []
    def forbidden_reader(path: Path) -> str:
        opened.append(path)
        raise AssertionError("feedback was opened before verification")
    result = evaluate_feedback_release(parents, roles=INDEPENDENT_ROLES,
                                       leakage_scan={"marker_count": 0},
                                       feedback_reader=forbidden_reader)
    assert result.status == "HOLD"
    assert opened == []

def test_verify_requires_actual_three_events_external_root_and_correct_fixture_key(parents) -> None:
    verification = verify_single_case_freeze_chain(
        **parents, witness_key=b"TEST-FIXTURE-KEY-NOT-REAL",
        expected_external_root=parents["registry"]["events"][-1]["event_hash"],
        verified_at="2026-07-16T01:00:00Z", verifier="human-witness-01")
    assert verification["status"] == "VERIFIED"
    assert "key" not in json.dumps(verification).lower()
```

Parameterize wrong/empty fixture key, missing/duplicate/out-of-order events, wrong case, changed actual parent, registry root mismatch, overlapping witness role and absent environment variable. Assert none creates release credential.

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/evaluation/test_prospective_evidence.py tests/evaluation/test_prospective_frozen_run.py -q`

Expected: FAIL because verification currently prints only `VALID` and creates no immutable verification artifact.

- [ ] **Step 3: Implement verification as a separate gate**

```python
def verify_single_case_freeze_chain(
    *, intake_path: Path, bundle_root: Path, frozen_run_path: Path,
    registry_path: Path, witness_key: bytes, expected_external_root: str,
    verified_at: str, verifier: str,
) -> dict[str, Any]:
    intake = read_and_verify_artifact(intake_path)
    bundle = verify_single_case_bundle(bundle_root)
    frozen = read_and_verify_frozen_run(frozen_run_path, bundle)
    registry = read_json(registry_path)
    verify_witness_registry(registry, witness_key)
    assert_exact_three_event_segment(registry, intake, bundle, frozen)
    if registry["events"][-1]["event_hash"] != expected_external_root:
        raise ContaminationError("external registry root mismatch")
    return seal_verification(
        status="VERIFIED",
        parents=(ref(intake_path), ref(bundle.manifest_path),
                 ref(frozen_run_path), ref(registry_path)),
        verified_at=verified_at,
        witness_identity_ref=verifier,
    )


def build_feedback_release_credential(
    verification: Mapping[str, Any], roles: Mapping[str, str],
    leakage_scan: Mapping[str, Any], *, created_at: str,
) -> dict[str, Any]:
    if verification["status"] != "VERIFIED":
        raise ValueError("feedback release requires VERIFIED freeze verification")
    assert_roles_are_pairwise_independent(roles)
    if leakage_scan != {"marker_count": 0, "status": "PASS"}:
        raise ContaminationError("feedback leakage scan failed")
    return seal_child_artifact(
        schema_version="prospective-feedback-release/v1",
        case_id=verification["case_id"],
        subject_id_hash=verification["subject_id_hash"],
        created_at=created_at,
        parents=[artifact_ref(verification)],
        release_status="RELEASED",
        freeze_at=verification["freeze_at"],
        roles=dict(roles),
        leakage_scan=dict(leakage_scan),
    )
```

CLI `witness-verify-single-case` reads key only through `--witness-key-env`; requires `--external-root` value (root is not secret), writes a new verification path, never logs environment values. CLI `issue-feedback-release` accepts only verification/roles/leakage artifacts and has no feedback-path argument.

- [ ] **Step 4: Run GREEN and key-redaction checks**

Run: `python -m pytest tests/evaluation/test_prospective_evidence.py tests/evaluation/test_prospective_frozen_run.py tests/evaluation/test_dataset.py -q`

Expected: PASS; captured stdout/stderr/artifacts contain neither fixture key nor environment value; missing variable fails closed.

- [ ] **Step 5: Commit**

```bat
git add engine/evaluation/prospective_evidence.py tools/school_capability_prospective.py tools/school_capability_dataset.py tests/evaluation/test_prospective_evidence.py tests/evaluation/test_prospective_frozen_run.py
git commit -m "feat: verify witness freeze before feedback release"
```

## Phase 2: Evidence, Review, Cohort, and Gates

### Task 6: Immediate retrospective collection and evidence classification

**Files:**
- Modify: `engine/evaluation/prospective_evidence.py`
- Modify: `tools/school_capability_dataset.py`
- Create: `templates/prospective-immediate-retrospective-v1.json`
- Modify: `tests/evaluation/test_prospective_evidence.py`

**Interfaces:**
- Consumes: VERIFIED release credential and a custody JSON path opened only after gate success.
- Produces: `collect_immediate_retrospective(release, custody_reader, *, collected_at, custodian) -> dict[str, Any]`; `bind_immediate_labels(...) -> dict[str, Any]`.

- [ ] **Step 1: Write failing classification tests**

```python
def test_immediate_retrospective_is_prediction_first_not_future(release, custody_file) -> None:
    result = collect_immediate_retrospective(
        release, lambda: json.loads(custody_file.read_text(encoding="utf-8")),
        collected_at="2026-07-16T02:00:00Z", custodian="human-custodian-01")
    assert result["evidence_class"] == "prediction_first_immediate_retrospective"
    assert result["fact_cutoff_at"] == release["freeze_at"]
    assert result["collected_after_verification"] is True
    assert all(fact["occurred_at"] <= result["fact_cutoff_at"] or
               fact["classification"] == "no_data" for fact in result["facts"])
    assert "probability" not in json.dumps(result).lower()
```

Add tests that a fact after freeze cannot enter immediate, unknown relative time becomes `no_data`, `future_outcome` evidence class is rejected, duplicate `label_identity` rejects, unbound artifact cannot contain rationale/report/prediction, and no release means custody lambda is never called.

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/evaluation/test_prospective_evidence.py -q`

Expected: FAIL because collection/template functions are absent.

- [ ] **Step 3: Implement minimal release-first collection**

```python
def collect_immediate_retrospective(
    release: Mapping[str, Any], custody_reader: Callable[[], Mapping[str, Any]],
    *, collected_at: str, custodian: str,
) -> dict[str, Any]:
    verified_release = validate_release_credential(release)  # before custody_reader()
    raw = custody_reader()
    facts = [classify_fact_time(row, cutoff=verified_release["freeze_at"])
             for row in validate_custody_payload(raw)]
    return seal_child_artifact(
        schema_version="prospective-immediate-retrospective-unbound/v1",
        evidence_class="prediction_first_immediate_retrospective",
        label_identity=canonical_artifact_sha256({
            "case_id": verified_release["case_id"],
            "evidence_class": "prediction_first_immediate_retrospective",
            "collected_at": collected_at,
        }),
        facts=facts,
        fact_cutoff_at=verified_release["freeze_at"],
        collected_after_verification=True, parents=[ref(release)])
```

CLI `release-immediate-retrospective-template` requires release credential and writes a new template copy only after validation. CLI `collect-immediate-retrospective` validates release before opening `--custody-input`; both support dry-run without output.

- [ ] **Step 4: Run GREEN**

Run: `python -m pytest tests/evaluation/test_prospective_evidence.py -q`

Expected: PASS, including mocked file-open order assertion.

- [ ] **Step 5: Commit**

```bat
git add engine/evaluation/prospective_evidence.py tools/school_capability_dataset.py templates/prospective-immediate-retrospective-v1.json tests/evaluation/test_prospective_evidence.py
git commit -m "feat: collect classified immediate retrospective evidence"
```

### Task 7: Matured future observation and separate completion ledger

**Files:**
- Modify: `engine/evaluation/prospective_evidence.py`
- Modify: `tools/school_capability_dataset.py`
- Modify: `tests/evaluation/test_prospective_evidence.py`

**Interfaces:**
- Consumes: future-question registration, frozen run parent, release-independent future custody input, current UTC time, evidence source refs.
- Produces: `collect_future_observation(registration, frozen_run, observation, *, collected_at) -> dict[str, Any]`; `build_case_completion(...) -> dict[str, Any]`.

- [ ] **Step 1: Write failing future ledger tests**

```python
@pytest.mark.parametrize("label", ["not_observed", "no_data"])
def test_future_observation_respects_window_and_no_data(registration, frozen, label) -> None:
    result = collect_future_observation(
        registration, frozen,
        {"future_task_id": registration["future_task_id"], "label": label,
         "observed_at": registration["observation_window"]["end_at"],
         "source_refs": ["custody://follow-up-001"], "conflict_state": "none"},
        collected_at=registration["observation_window"]["end_at"])
    assert result["evidence_class"] == "future_observation"
    assert result["label_identity"] != "immediate-label-identity"


def test_not_observed_before_window_end_is_rejected(registration, frozen) -> None:
    observation = {
        "future_task_id": registration["future_task_id"],
        "label": "not_observed",
        "observed_at": "2026-08-01T00:00:00Z",
        "source_refs": ["custody://follow-up-001"],
        "conflict_state": "none",
    }
    with pytest.raises(ValueError, match="window has not matured"):
        collect_future_observation(registration, frozen, observation,
                                   collected_at="2026-08-01T00:00:00Z")
```

Assert `occurred` must occur after freeze and inside window; `not_observed` requires full-window source coverage; lost contact/conflict/unknown time becomes `no_data`; completion has separate `retrospective_completion_status` and `future_completion_status`, never `completed: true`.

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/evaluation/test_prospective_evidence.py -q`

Expected: FAIL because future collection/completion functions are absent.

- [ ] **Step 3: Implement the future ledger**

```python
def collect_future_observation(
    registration: Mapping[str, Any], frozen_run: Mapping[str, Any],
    observation: Mapping[str, Any], *, collected_at: str,
) -> dict[str, Any]:
    question = validate_future_question_registration(registration,
                                                      freeze_at=frozen_run["freeze_at"])
    label = observation["label"]
    if label not in {"occurred", "not_observed", "no_data"}:
        raise ValueError("invalid future observation label")
    enforce_window_semantics(question, observation, collected_at=collected_at)
    label_identity = canonical_artifact_sha256({
        "case_id": question["case_id"],
        "evidence_class": "future_observation",
        "future_task_id": question["future_task_id"],
        "observed_at": observation["observed_at"],
    })
    return seal_child_artifact(
        schema_version="prospective-future-observation-unbound/v1",
        case_id=question["case_id"],
        subject_id_hash=question["subject_id_hash"],
        created_at=collected_at,
        evidence_class="future_observation",
        label_identity=label_identity,
        observation=dict(observation),
        parents=[artifact_ref(registration), artifact_ref(frozen_run)],
    )


def build_case_completion(
    *, freeze_verification: Mapping[str, Any],
    immediate_bound: Mapping[str, Any] | None,
    future_bound: Mapping[str, Any] | None,
    stopped_incident: Mapping[str, Any] | None,
    created_at: str,
) -> dict[str, Any]:
    if stopped_incident is not None:
        raise ContaminationError("STOP case cannot produce completion")
    retrospective_status = (
        "CASE_COMPLETE_FOR_RETROSPECTIVE" if immediate_bound is not None else "PENDING")
    future_status = "CASE_COMPLETE_FOR_FUTURE" if future_bound is not None else "PENDING"
    return seal_child_artifact(
        schema_version="prospective-case-completion/v1",
        case_id=freeze_verification["case_id"],
        subject_id_hash=freeze_verification["subject_id_hash"],
        created_at=created_at,
        retrospective_completion_status=retrospective_status,
        future_completion_status=future_status,
        parents=[artifact_ref(item) for item in
                 (freeze_verification, immediate_bound, future_bound) if item is not None],
    )
```

CLI `collect-future-observation` must not depend on immediate feedback; it validates maturity first. `build-case-completion` rejects STOP parents and scores `no_data` as incomplete.

- [ ] **Step 4: Run GREEN**

Run: `python -m pytest tests/evaluation/test_prospective_evidence.py -q`

Expected: PASS; immediate and future label identities/counts are disjoint.

- [ ] **Step 5: Commit**

```bat
git add engine/evaluation/prospective_evidence.py tools/school_capability_dataset.py tests/evaluation/test_prospective_evidence.py
git commit -m "feat: keep future observations in a separate ledger"
```

### Task 8: Reuse high-risk dual review without cross-ledger reuse

**Files:**
- Modify: `engine/evaluation/high_risk_review.py:11-334`
- Modify: `tools/school_capability_review.py:73-254`
- Modify: `tests/evaluation/test_high_risk_review.py`

**Interfaces:**
- Consumes: evidence-class-specific observation packet, role map, independent review decisions.
- Produces: `prepare_review_packets(observation, evidence_class, label_identity, reviewer_a, reviewer_b, disallowed_reviewers)`, `finalize_reviews(..., evidence_class, label_identity, adjudication=None)`.

- [ ] **Step 1: Write failing role and ledger tests**

```python
def test_future_review_cannot_reuse_immediate_reviews() -> None:
    immediate = _review("human-a", evidence_class="prediction_first_immediate_retrospective",
                        label_identity="label-immediate")
    future = _review("human-b", evidence_class="future_observation",
                     label_identity="label-future")
    with pytest.raises(ValueError, match="same evidence class and label identity"):
        finalize_reviews(CASE_ID, "wealth.debt", immediate, future)


def test_adjudicator_is_separate_from_all_operational_roles() -> None:
    with pytest.raises(ValueError, match="role separation"):
        finalize_reviews(
            CASE_ID, "wealth.debt", _review("human-reviewer-a"),
            _review("human-reviewer-b", decision="not_observed"),
            adjudication=_adjudication("human-custodian-01"),
            evidence_class="prediction_first_immediate_retrospective",
            label_identity="label-immediate",
            disallowed_adjudicators={"human-intake-01", "human-runner-01",
                                      "human-custodian-01", "human-witness-01"})
```

Assert packets contain facts/sources/time/task definition only; packet with prediction/probability/report/other reviewer opinion rejects; same reviewer, automated reviewer, single review, unresolved conflict cannot produce A grade.

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/evaluation/test_high_risk_review.py -q`

Expected: FAIL because review schema lacks evidence-class and label identity.

- [ ] **Step 3: Extend the schemas minimally**

```python
def prepare_review_packets(
    observation: Mapping[str, Any], *, evidence_class: str, label_identity: str,
    reviewer_a: str, reviewer_b: str,
    disallowed_reviewers: set[str] | None = None,
) -> dict[str, dict[str, Any]]:
    clean = validate_observation(observation)
    assert_evidence_identity(clean, evidence_class, label_identity)
    return build_isolated_packets(clean, reviewer_a, reviewer_b,
                                  disallowed_reviewers or set())


def finalize_reviews(
    case_id: str, task_id: str,
    review_a: Mapping[str, Any], review_b: Mapping[str, Any],
    adjudication: Mapping[str, Any] | None = None, *,
    evidence_class: str, label_identity: str,
    disallowed_adjudicators: set[str] | None = None,
) -> dict[str, Any]:
    first = validate_review(review_a)
    second = validate_review(review_b)
    assert_same_evidence_identity(first, second, evidence_class, label_identity)
    return resolve_dual_review(
        case_id, task_id, first, second, adjudication,
        disallowed_adjudicators=disallowed_adjudicators or set())
```

Bind `observation_sha256`, `evidence_class`, `label_identity`, and `review_packet_sha256` into every review/adjudication/final label. Keep original reviews forever and return HOLD on unresolved conflict.

- [ ] **Step 4: Run GREEN**

Run: `python -m pytest tests/evaluation/test_high_risk_review.py tests/evaluation/test_prospective_evidence.py -q`

Expected: PASS for both evidence classes and all three fixed high-risk tasks.

- [ ] **Step 5: Commit**

```bat
git add engine/evaluation/high_risk_review.py tools/school_capability_review.py tests/evaluation/test_high_risk_review.py
git commit -m "feat: bind high risk review to evidence ledger"
```

### Task 9: Ten-case parent-reference-only cohort

**Files:**
- Create: `engine/evaluation/prospective_gates.py`
- Create: `tools/school_capability_cohort.py`
- Create: `tests/evaluation/test_prospective_cohort.py`

**Interfaces:**
- Consumes: exactly 10 unique retrospective-complete parent chains, optional mature future parents, task/rule snapshots, immutable historical baseline refs.
- Produces: `build_cohort_manifest(member_completions, historical_refs, *, created_at) -> dict[str, Any]`; `verify_cohort_manifest(manifest) -> dict[str, Any]`.

- [ ] **Step 1: Write failing cohort tests**

```python
def test_cohort_manifest_contains_only_parent_refs(ten_completed_cases, historical_refs) -> None:
    manifest = build_cohort_manifest(ten_completed_cases, historical_refs,
                                     created_at="2026-08-01T00:00:00Z")
    assert len(manifest["members"]) == 10
    assert all(set(parent) == {"artifact_path", "artifact_sha256"}
               for member in manifest["members"] for parent in member["parents"].values()
               if parent is not None)
    assert "completed" not in json.dumps(manifest)
    assert manifest["gate_ids"] == [
        "prediction_capability_candidate_gate_v1",
        "future_empirical_gate_v1",
        "historical_platform_baseline_2026_07_15",
    ]
```

Add tests: 9 completion parents => HOLD/no score output; duplicate subject rejected; STOP member excluded but listed in stopped audit; stable member-set hash; parent drift => cohort STOP; no future labels => no future score file; same parent rerun verifies existing output rather than overwriting.

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/evaluation/test_prospective_cohort.py -q`

Expected: FAIL because cohort module/CLI does not exist.

- [ ] **Step 3: Implement manifest and create-only CLI**

```python
def build_cohort_manifest(
    member_completions: Sequence[Mapping[str, Any]],
    historical_refs: Sequence[ArtifactRef], *, created_at: str,
) -> dict[str, Any]:
    members = validate_ten_unique_retrospective_completions(member_completions)
    member_set_sha256 = canonical_artifact_sha256(
        {"members": sorted((m["case_id"], m["subject_id_hash"]) for m in members)})
    return seal_artifact(
        schema_version="prospective-cohort-manifest/v1",
        cohort_id=f"cohort-{members[0]['case_id']}-{members[-1]['case_id']}",
        created_at=created_at,
        member_set_sha256=member_set_sha256,
        members=[parent_refs_only(m) for m in members],
        gate_ids=["prediction_capability_candidate_gate_v1",
                  "future_empirical_gate_v1",
                  "historical_platform_baseline_2026_07_15"],
        historical_baseline_refs=[asdict(item) for item in historical_refs],
    )
```

CLI subcommands and exact argument contracts are: `build --completion <repeatable-path> --historical-md <path> --historical-json <path> --out-dir <path> [--dry-run]`, `verify --manifest <path>`, `score --manifest <path> --out-dir <path> [--dry-run]`, and `report --manifest <path> --immediate-gate <path> --future-gate <path> --out <path> [--dry-run]`. Output directory follows `META/prospective-go/cohorts/cohort-<first>-<last>--<sha-prefix>/` and must not exist for first publication.

- [ ] **Step 4: Run GREEN**

Run: `python -m pytest tests/evaluation/test_prospective_cohort.py -q`

Expected: PASS; no parent bytes are copied; future score absent when no valid future observation.

- [ ] **Step 5: Commit**

```bat
git add engine/evaluation/prospective_gates.py tools/school_capability_cohort.py tests/evaluation/test_prospective_cohort.py
git commit -m "feat: aggregate ten cases by immutable parent references"
```

### Task 10: Prediction-capability candidate gate

**Files:**
- Modify: `engine/evaluation/prospective_gates.py`
- Modify: `tools/school_capability_cohort.py`
- Create: `tests/evaluation/test_prospective_gates.py`

**Interfaces:**
- Consumes: immediate retrospective score rows, competition/holdout rows, audit statuses, multiple cohort manifests.
- Produces: `evaluate_prediction_capability_candidate(evidence: GateEvidence, *, evaluated_at: str) -> dict[str, Any]`.

- [ ] **Step 1: Write failing threshold-table tests**

```python
@pytest.mark.parametrize("mutation", [
    "subjects_19", "labels_14", "positive_zero", "negative_zero",
    "calibration_equal_0_2", "high_risk_unreviewed", "competitive_4",
    "selection_change_0", "learned_utility_lower", "hash_fail",
    "witness_fail", "leakage_fail",
])
def test_prediction_candidate_holds_on_each_missing_condition(go_immediate_evidence, mutation) -> None:
    evidence = mutate(go_immediate_evidence, mutation)
    result = evaluate_prediction_capability_candidate(evidence,
                                                       evaluated_at="2026-12-01T00:00:00Z")
    assert result["gate_id"] == "prediction_capability_candidate_gate_v1"
    assert result["status"] == "HOLD"
    assert result["unmet_conditions"]


def test_prediction_candidate_go_only_creates_proposal(go_immediate_evidence) -> None:
    result = evaluate_prediction_capability_candidate(go_immediate_evidence,
                                                       evaluated_at="2026-12-01T00:00:00Z")
    assert result["status"] == "GO"
    assert result["proposal_allowed"] is True
    assert result["production_switch"] is False
```

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/evaluation/test_prospective_gates.py -q`

Expected: FAIL because gate evaluator is absent.

- [ ] **Step 3: Implement exact typed gate evidence and predicate**

```python
@dataclass(frozen=True)
class GateEvidence:
    evidence_class: str
    unique_completed_subjects: int
    task_label_counts: Mapping[str, int]
    positive_counts: Mapping[str, int]
    negative_counts: Mapping[str, int]
    no_data_counts: Mapping[str, int]
    calibration_error_by_task: Mapping[str, float | None]
    competitive_count_by_task: Mapping[str, int]
    selection_change_count: int
    learned_utility: float
    static_utility: float
    high_risk_review_status: str
    hash_audit_status: str
    witness_audit_status: str
    leakage_audit_status: str


def evaluate_prediction_capability_candidate(
    evidence: GateEvidence, *, evaluated_at: str,
) -> dict[str, Any]:
    require_evidence_class(evidence, "prediction_first_immediate_retrospective")
    checks = {
        "completed_subjects_at_least_20": evidence.unique_completed_subjects >= 20,
        "one_task_has_15_positive_and_negative": any(
            count >= 15 and evidence.positive_counts.get(task, 0) > 0
            and evidence.negative_counts.get(task, 0) > 0
            for task, count in evidence.task_label_counts.items()),
        "one_eligible_task_calibration_below_0_2": any(
            evidence.task_label_counts.get(task, 0) >= 15
            and evidence.positive_counts.get(task, 0) > 0
            and evidence.negative_counts.get(task, 0) > 0
            and error is not None and error < 0.2
            for task, error in evidence.calibration_error_by_task.items()),
        "high_risk_reviews_pass": evidence.high_risk_review_status == "PASS",
        "one_competitive_task_at_least_5": max(evidence.competitive_count_by_task.values(), default=0) >= 5,
        "selection_changed": evidence.selection_change_count >= 1,
        "utility_not_degraded": evidence.learned_utility >= evidence.static_utility,
        "audits_pass": all(status == "PASS" for status in (
            evidence.hash_audit_status, evidence.witness_audit_status,
            evidence.leakage_audit_status)),
    }
    return build_gate_result("prediction_capability_candidate_gate_v1", checks, evidence,
                             evaluated_at=evaluated_at)
```

JSON must include every field required by spec and parent refs. `no_data` never enters valid task counts.

- [ ] **Step 4: Run GREEN**

Run: `python -m pytest tests/evaluation/test_prospective_gates.py -q`

Expected: PASS at every strict boundary, especially `0.2 => HOLD`.

- [ ] **Step 5: Commit**

```bat
git add engine/evaluation/prospective_gates.py tools/school_capability_cohort.py tests/evaluation/test_prospective_gates.py
git commit -m "feat: calculate prediction capability candidate gate"
```

### Task 11: Future empirical gate and historical baseline isolation

**Files:**
- Modify: `engine/evaluation/prospective_gates.py`
- Modify: `tools/school_capability_cohort.py`
- Modify: `tests/evaluation/test_prospective_gates.py`
- Create: `tests/test_production_entrypoints_unchanged.py`

**Interfaces:**
- Consumes: future observation gate evidence and immutable baseline paths/SHA-256.
- Produces: `evaluate_future_empirical(evidence, evaluated_at) -> dict[str, Any]`; `build_three_gate_report(...) -> str`.

- [ ] **Step 1: Write failing 10/8 and isolation tests**

```python
@pytest.mark.parametrize("mutation", [
    "subjects_9", "labels_7", "positive_zero", "negative_zero",
    "window_unmatured", "calibration_equal_0_2", "high_risk_reused",
    "competitive_4", "competition_not_applicable", "selection_change_0",
    "learned_utility_lower", "parent_hash_fail",
])
def test_future_gate_holds_on_each_missing_condition(go_future_evidence, mutation) -> None:
    result = evaluate_future_empirical(mutate(go_future_evidence, mutation),
                                       evaluated_at="2027-01-16T00:00:00Z")
    assert result["gate_id"] == "future_empirical_gate_v1"
    assert result["status"] == "HOLD"


def test_twenty_immediate_plus_ten_future_cannot_satisfy_historical_baseline(
    go_immediate_evidence, go_future_evidence, historical_result,
) -> None:
    immediate = evaluate_prediction_capability_candidate(
        go_immediate_evidence, evaluated_at="2027-01-16T00:00:00Z")
    future = evaluate_future_empirical(
        go_future_evidence, evaluated_at="2027-01-16T00:00:00Z")
    report = build_three_gate_report(immediate, future, historical_result)
    assert "预测能力候选 GO" in report
    assert "未来实证 GO" in report
    assert "historical baseline（只读引用）" in report
    assert historical_result["status"] == "HOLD"
```

Snapshot pre-change SHA-256 for both `META/six-month-platform-gate-2026-07-15.*`; assert post-test bytes unchanged. Assert report rejects a single mixed prospective total and the phrase `已自动切生产`.

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/evaluation/test_prospective_gates.py tests/test_production_entrypoints_unchanged.py -q`

Expected: FAIL because future gate/report and regression lock do not exist.

- [ ] **Step 3: Implement future predicate and read-only report**

```python
def evaluate_future_empirical(evidence: GateEvidence, *, evaluated_at: str) -> dict[str, Any]:
    require_evidence_class(evidence, "future_observation")
    checks = {
        "completed_subjects_at_least_10": evidence.unique_completed_subjects >= 10,
        "one_future_task_has_8_positive_and_negative": any(
            count >= 8 and evidence.positive_counts.get(task, 0) > 0
            and evidence.negative_counts.get(task, 0) > 0
            for task, count in evidence.task_label_counts.items()),
        "one_eligible_task_calibration_below_0_2": any(
            evidence.task_label_counts.get(task, 0) >= 8
            and evidence.positive_counts.get(task, 0) > 0
            and evidence.negative_counts.get(task, 0) > 0
            and error is not None and error < 0.2
            for task, error in evidence.calibration_error_by_task.items()),
        "fresh_high_risk_reviews_pass": evidence.high_risk_review_status == "PASS_FUTURE",
        "one_competitive_task_at_least_5": max(evidence.competitive_count_by_task.values(), default=0) >= 5,
        "selection_changed": evidence.selection_change_count >= 1,
        "utility_not_degraded": evidence.learned_utility >= evidence.static_utility,
        "audits_pass": all(status == "PASS" for status in (
            evidence.hash_audit_status, evidence.witness_audit_status,
            evidence.leakage_audit_status)),
    }
    return build_gate_result("future_empirical_gate_v1", checks, evidence,
                             evaluated_at=evaluated_at)
```

`build_three_gate_report()` renders three fixed sections and reads historical status from immutable baseline JSON; it never recalculates historical status from new evidence.

- [ ] **Step 4: Run GREEN and baseline digest check**

Run: `python -m pytest tests/evaluation/test_prospective_gates.py tests/test_production_entrypoints_unchanged.py -q`

Expected: PASS; `run_pipeline()` signature/default behavior and `DEFAULT_RUNNER_REGISTRY` registrations are unchanged; historical file digests equal their pre-implementation values.

- [ ] **Step 5: Commit**

```bat
git add engine/evaluation/prospective_gates.py tools/school_capability_cohort.py tests/evaluation/test_prospective_gates.py tests/test_production_entrypoints_unchanged.py
git commit -m "feat: calculate future gate without changing baseline"
```

## Phase 3: Protocol, Documentation, and Verification

### Task 12: Update protocol, action plan, tool index, and handoff

**Files:**
- Modify: `META/prospective-intake-protocol-v1.md`
- Modify: `plans/upgrade-guides/post-gate-action-plan-2026-07-15.md:314-908`
- Modify: `tools/README.md:39-49,154-175`
- Modify: `handoff.md`
- Modify: `tests/evaluation/test_prospective_gate_workflow.py`
- Modify: `tests/test_project_metadata.py`

**Interfaces:**
- Consumes: implemented CLI names and exact gate IDs from Tasks 1—11.
- Produces: one consistent operational contract: per-case intake/freeze/verify, post-verify immediate feedback, separate future observation, 10-case parent-reference aggregate.

- [ ] **Step 1: Write failing documentation contract tests**

```python
def test_protocol_documents_single_case_order_and_human_witness_stop() -> None:
    text = Path("META/prospective-intake-protocol-v1.md").read_text(encoding="utf-8")
    for required in (
        "每案当天正式 intake", "恰好 1 个", "prediction_first_immediate_retrospective",
        "future_observation", "prediction_capability_candidate_gate_v1",
        "future_empirical_gate_v1", "historical_platform_baseline_2026_07_15",
        "独立人类见证人", "人工硬停点", "不得自动切换生产入口",
    ):
        assert required in text
```

Assert action plan Task 3 is no longer “满 10 案正式 intake”; Task 4 is per-case; Task 5 has one future question; Tasks 7—10 consume separate gates; Task 11 preserves baseline. Assert tools README uses current command names and handoff states both new gates HOLD.

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/evaluation/test_prospective_gate_workflow.py tests/test_project_metadata.py -q`

Expected: FAIL on old batch wording and missing new gate identities.

- [ ] **Step 3: Update all four documents with exact Windows commands**

Document this non-secret witness sequence without a key value:

```bat
set "SCHOOL_CAPABILITY_WITNESS_KEY="
rem 独立人类见证人现在亲自在此临时终端输入真实值；agent 离开屏幕且不接收该值。
python -m tools.school_capability_prospective witness-freeze-chain --intake <单案正式intake路径> --bundle-root <单案blind-bundle路径> --staged-run <单案frozen-run路径> --out <单案witness路径> --witness-key-env SCHOOL_CAPABILITY_WITNESS_KEY --dry-run
python -m tools.school_capability_prospective witness-freeze-chain --intake <单案正式intake路径> --bundle-root <单案blind-bundle路径> --staged-run <单案frozen-run路径> --out <单案witness路径> --witness-key-env SCHOOL_CAPABILITY_WITNESS_KEY
python -m tools.school_capability_dataset witness-verify-single-case --intake <单案正式intake路径> --bundle-root <单案blind-bundle路径> --frozen-run <单案frozen-run路径> --registry <单案witness路径> --external-root <见证方仓库外保存的root> --verifier human-witness-01 --verified-at <真实UTC时间> --out <单案verification路径> --witness-key-env SCHOOL_CAPABILITY_WITNESS_KEY --dry-run
python -m tools.school_capability_dataset witness-verify-single-case --intake <单案正式intake路径> --bundle-root <单案blind-bundle路径> --frozen-run <单案frozen-run路径> --registry <单案witness路径> --external-root <见证方仓库外保存的root> --verifier human-witness-01 --verified-at <真实UTC时间> --out <单案verification路径> --witness-key-env SCHOOL_CAPABILITY_WITNESS_KEY
set "SCHOOL_CAPABILITY_WITNESS_KEY="
python -c "import os; print('SET' if os.environ.get('SCHOOL_CAPABILITY_WITNESS_KEY') else 'NOT SET')"
```

The prose must state placeholders are paths/timestamps/root only, never a key; the witness types the secret interactively without agent involvement, clears it, verifies `NOT SET`, closes the terminal, and externally anchors root.

- [ ] **Step 4: Run GREEN and documentation links**

Run: `python -m pytest tests/evaluation/test_prospective_gate_workflow.py tests/test_project_metadata.py -q && python tools/tool_registry.py --check`

Expected: PASS and tool registry exit 0.

- [ ] **Step 5: Commit**

```bat
git add META/prospective-intake-protocol-v1.md plans/upgrade-guides/post-gate-action-plan-2026-07-15.md tools/README.md handoff.md tests/evaluation/test_prospective_gate_workflow.py tests/test_project_metadata.py
git commit -m "docs: adopt immediate single case prospective workflow"
```

### Task 13: Specialized and full verification with no production entry change

**Files:**
- Verify: all files changed by Tasks 1—12
- Verify unchanged: `engine/application/pipeline_runner.py`
- Verify unchanged: `engine/claims/runner_registry.py`
- Verify unchanged: `META/six-month-platform-gate-2026-07-15.md`
- Verify unchanged: `META/six-month-platform-gate-2026-07-15.json`

**Interfaces:**
- Consumes: completed implementation.
- Produces: fresh test/tool/diff evidence; no new production artifact.

- [ ] **Step 1: Run focused workflow tests**

Run:

```bat
python -m pytest tests/evaluation/test_prospective_artifacts.py tests/evaluation/test_single_case_workflow.py tests/evaluation/test_prospective_evidence.py tests/evaluation/test_prospective_cohort.py tests/evaluation/test_prospective_gates.py tests/evaluation/test_prospective_frozen_run.py tests/evaluation/test_high_risk_review.py tests/evaluation/test_prospective_gate_workflow.py tests/test_production_entrypoints_unchanged.py -q
```

Expected: all PASS; no skipped security test.

- [ ] **Step 2: Run adjacent regressions**

Run:

```bat
python -m pytest tests/evaluation/test_dataset.py tests/evaluation/test_scoring.py tests/evaluation/test_freeze.py tests/claims/test_multi_school_freeze.py tests/decision/test_routing_holdout_artifacts.py tests/decision/test_routing_holdout_comparison.py -q
```

Expected: all PASS.

- [ ] **Step 3: Run full suite and repository checks**

Run:

```bat
python -m pytest tests -q && python tools/tool_registry.py --check && python tools/rule_status_scan.py --check && git diff --check
```

Expected: pytest has no failures/errors; tool/rule checks exit 0; diff check has no output.

- [ ] **Step 4: Mechanically verify immutable and production boundaries**

Run:

```bat
python -c "from pathlib import Path; import hashlib; paths=[Path(r'META/six-month-platform-gate-2026-07-15.md'),Path(r'META/six-month-platform-gate-2026-07-15.json')]; print({p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})" && git diff --exit-code -- engine/application/pipeline_runner.py engine/claims/runner_registry.py META/six-month-platform-gate-2026-07-15.md META/six-month-platform-gate-2026-07-15.json
```

Expected: printed digests match values recorded before Task 1; `git diff --exit-code` returns 0.

- [ ] **Step 5: Commit verification-only fixes if needed**

If verification required a test/document fix, return to the owning Task, apply that Task's named file list, rerun its RED/GREEN cycle, and use that Task's commit command. If no fix was needed, do not create an empty commit.

## Phase 4: First-Case Migration and Actual Execution

### Task 14: Prepare and execute first case through frozen run, before witness

**Files:**
- Read/verify unchanged source: `cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/input.md`
- Read: `META/prospective-go/prospective-go-recruitment-log.jsonl`
- Read: `META/prospective-go/prospective-go-b01-tasks-by-case.json`
- Create after approved dry-runs: `META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/*--future-question-registration--v001.json`
- Create after approved dry-runs: `META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/*--intake--v001.json`
- Create after approved dry-runs: `META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/*--blind-bundle--v001/`
- Create after approved dry-runs: `META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/*--frozen-run--v001.json`

**Interfaces:**
- Consumes: real first-case authorized input and one human-approved redacted future-question draft; no feedback/current-status/history content.
- Produces: first-case immutable prediction chain ending at `SIX_SOURCE_FROZEN`; no witness, verification, feedback, report, observation or label yet.

- [ ] **Step 1: Record source/baseline digests and leakage preflight**

Run:

```bat
python -m tools.preflight cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/input.md && python -c "from pathlib import Path; import hashlib; p=Path(r'cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/input.md'); print(hashlib.sha256(p.read_bytes()).hexdigest())"
```

Expected: preflight PASS; record the actual input digest in the execution log; repository leakage scanner reports 0 feedback/history/current-status markers for this input. If leakage is found, STOP this case; do not migrate it as clean evidence.

- [ ] **Step 2: Have an authorized human approve exactly one future question draft**

Create a custody-safe draft outside the blind bundle using `templates/prospective-future-question-v1.json`. For this first case the `future_task_id` must match a pre-registered assigned task, use binary positive/negative definitions, explicit verification sources, and an end time no later than three calendar months after the eventual freeze. The agent may validate the redacted draft but must not invent an observed answer or read feedback.

- [ ] **Step 3: Dry-run then publish future question and intake**

Run with the actual approved draft path and real UTC timestamp:

```bat
python -m tools.school_capability_dataset single-case-intake --input cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/input.md --tasks META/prospective-go-task-catalog-v1.json --school ziping --school ditiansui --school duan --school ren --school gao --school yang --operator human-intake-01 --tasks-by-case META/prospective-go/prospective-go-b01-tasks-by-case.json --future-question <已批准脱敏future-question草稿路径> --case-root META/prospective-go/single-cases --created-at <真实UTC时间> --dry-run
```

Expected: exactly one record, the existing full case ID, the existing four assigned tasks, six schools, one future question and no write. After human checks the dry-run, repeat without `--dry-run`; both target v001 paths must not exist beforehand.

- [ ] **Step 4: Dry-run then create the blind bundle**

Run:

```bat
python -m tools.school_capability_dataset prepare-single-case-blind --intake META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--intake--v001.json --future-question META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--future-question-registration--v001.json --tasks META/prospective-go-task-catalog-v1.json --rule-snapshot META/prospective-go-rule-snapshot-v1.json --target-dir META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--blind-bundle--v001 --dry-run
```

Expected: exact whitelist and one-case/one-question counts. After review repeat without `--dry-run`.

- [ ] **Step 5: Dry-run then publish the staged frozen run**

Run:

```bat
python -m tools.school_capability_prospective stage-single-case-frozen-run --bundle-root META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--blind-bundle--v001 --out META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--frozen-run--v001.json --dry-run
```

Expected: one case × four assigned tasks × six schools = 24 unique outputs, states only claim/abstain/unsupported, all parent hashes match, timing claims cite real `liunian_steps`. After review repeat without `--dry-run`.

- [ ] **Step 6: Verify no reveal artifact exists**

Run:

```bat
python -c "from pathlib import Path; r=Path(r'META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥'); forbidden=('feedback','immediate-retrospective','future-observation','report','labels'); hits=[p.as_posix() for p in r.rglob('*') if any(x in p.name.lower() for x in forbidden)]; print(hits); raise SystemExit(1 if hits else 0)"
```

Expected: prints `[]` and exits 0.

- [ ] **Step 7: Commit only if real-data artifact commit is separately authorized**

Do not include unrelated dirty-tree files. If authorization explicitly permits committing these non-PII artifacts:

```bat
git add META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥
git commit -m "eval: freeze first immediate prospective case"
```

Otherwise leave them uncommitted for human review; this does not change the plan document's no-commit rule.

### Task 15: Independent human witness signing and verification — FIRST HARD STOP

**Files:**
- Human-created: `META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/*--witness-freeze--v001.json`
- Human-created: `META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/*--freeze-verification--v001.json`
- External human custody: registry root record containing only root, case ID, time and witness identity reference.

**Interfaces:**
- Consumes: first-case actual intake, bundle, frozen run, witness-held real key, witness-held external root.
- Produces: VERIFIED freeze-verification artifact. Agent receives only the final verification artifact/path/status after the human has cleared and closed the terminal; agent never receives the key.

- [ ] **Step 1: Agent stops before the witness opens the temporary terminal**

The agent reports the exact three parent paths and their SHA-256 values, then relinquishes control. The independent human witness confirms they are not intake operator, runner operator, outcome custodian, reviewer A/B or adjudicator.

- [ ] **Step 2: Independent human witness personally signs in a new temporary `cmd.exe`**

The witness, not the agent, sets the real environment value privately and runs the documented `witness-freeze-chain` dry-run and formal command. The agent must not observe the screen, command history, environment, clipboard, logs or key value. The command line contains only `--witness-key-env SCHOOL_CAPABILITY_WITNESS_KEY`, never the secret.

- [ ] **Step 3: The same witness personally verifies actual parents and external root**

The witness runs `witness-verify-single-case` first with `--dry-run`, then formally, using the actual intake/bundle/frozen/registry paths and the registry root independently saved outside the repository. Expected formal artifact: `status=VERIFIED`, exactly three events, strict registered < prepared < freeze, actual parent hashes equal payload hashes, external root matches, no key field/value.

- [ ] **Step 4: Witness clears key without echoing and closes terminal**

The witness runs `set "SCHOOL_CAPABILITY_WITNESS_KEY="`, then the SET/NOT SET check documented in Task 12. Expected output: `NOT SET`. The witness closes the temporary terminal and confirms only: case ID, verification artifact path, `status=VERIFIED`, external root anchored, key cleared. They do not send the key to the agent.

- [ ] **Step 5: HUMAN HARD STOP — require explicit signed verification confirmation**

**STOP HERE.** No agent, automation, subagent or subsequent task may generate a feedback-release credential, a follow-up outline, `feedback.md`, custody request, immediate retrospective, observation, report or label until an independent human witness has personally completed Steps 1—4 and supplied explicit confirmation that the immutable verification artifact exists and validates as `VERIFIED`.

Expected checkpoint evidence:

```text
case_id=P-GO-2026-001-坤-壬戌己酉乙卯丁亥
freeze_verification_status=VERIFIED
registry_root_externally_anchored=true
witness_key_cleared=true
witness_human_signature_reference=<仓库内仅保存身份引用，不含签名秘密或PII>
```

If verification is HOLD, remain stopped. If HMAC/hash/root/role isolation fails, create only a contamination incident and mark STOP; never release feedback or re-freeze after reveal.

- [ ] **Step 6: Commit only if separately authorized after human verification**

```bat
git add META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥
git commit -m "eval: witness verify first prospective freeze"
```

Do not stage any external root file, terminal transcript, environment dump or secret.

### Task 16: Post-hard-stop feedback outline, immediate retrospective, and first-case status

**Files:**
- Create only after Task 15 signed checkpoint: `META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/*--feedback-release--v001.json`
- Create only after Task 15 signed checkpoint: custody-side follow-up outline derived from `templates/prospective-immediate-retrospective-v1.json`
- Create only after collection: `META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/*--immediate-retrospective--unbound--v001.json`
- Create after review/binding: corresponding high-risk review directory, bound retrospective and case-completion v001.
- Modify after actual evidence: `handoff.md`

**Interfaces:**
- Consumes: explicit human confirmation plus VERIFIED artifact, role/leakage audit, newly collected freeze-preexisting facts.
- Produces: immediate retrospective chain only; future question remains pending until its observation window matures.

- [ ] **Step 1: Verify the hard-stop evidence without any key**

Run:

```bat
python -m tools.school_capability_dataset verify-release-prerequisites --verification META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/P-GO-2026-001-坤-壬戌己酉乙卯丁亥--freeze-verification--v001.json --case-root META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥
```

Expected: `VERIFIED`, parent/hash/role/leakage checks PASS, target retrospective paths absent. This command does not accept a witness key and does not open feedback.

- [ ] **Step 2: Dry-run then issue feedback-release credential**

Run the implemented `issue-feedback-release` with actual verification, role declaration and zero-leakage audit, first with `--dry-run`, then formally. Expected: a create-only release artifact bound to the verification SHA-256; no feedback body is read.

- [ ] **Step 3: Generate the follow-up outline only now**

Run `release-immediate-retrospective-template` with the release credential, case ID, outcome custodian and a new output path, first dry-run then formal. The outline asks only for freeze前既往经历、freeze时已成立当前现状、发生时间/范围、来源、可核验等级和冲突状态; it contains no frozen prediction, probability, runner rationale or report.

- [ ] **Step 4: Outcome custodian collects feedback outside runner custody**

The independent custodian fills the released outline. Facts known to have occurred after freeze are excluded from immediate and reserved for future observation; facts with uncertain timing are `no_data`. The agent may receive only the redacted structured custody import approved for repository ingestion.

- [ ] **Step 5: Dry-run then create unbound immediate retrospective**

Run `collect-immediate-retrospective` with release credential and approved custody input, first `--dry-run`, then formal. Expected: `evidence_class=prediction_first_immediate_retrospective`, `fact_cutoff_at=freeze_at`, `collected_after_verification=true`, unique label identity, verification parent hash, no prediction text.

- [ ] **Step 6: Apply high-risk dual review and bind labels**

For `wealth.debt` in the first-case assigned tasks, run the updated `school_capability_review prepare → submit A/B → adjudicate if conflict → finalize` chain. Reviewer A/B and adjudicator must be independent humans and differ from all operational roles. Unresolved conflict remains HOLD. Bind low-risk and A-grade high-risk labels to the same freeze and immediate evidence class; do not create a future label.

- [ ] **Step 7: Create retrospective completion and honest gate status**

Create case completion with `retrospective_completion_status=CASE_COMPLETE_FOR_RETROSPECTIVE` only if the bound immediate label is scoreable and chain VERIFIED/non-STOP; leave `future_completion_status` pending. Recompute gate status: prediction candidate remains HOLD at 1/20; future empirical remains HOLD at 0/10; historical baseline remains the original HOLD read-only reference.

- [ ] **Step 8: Update handoff from actual artifacts and verify**

Update `handoff.md` with actual first-case paths/status, the pending future observation window, and no mixed prospective count. Run:

```bat
python -m pytest tests/evaluation/test_prospective_evidence.py tests/evaluation/test_high_risk_review.py tests/evaluation/test_prospective_gates.py -q && python tools/tool_registry.py --check && git diff --check
```

Expected: PASS/exit 0; no key/PII/prediction leakage; no future observation exists before maturity.

- [ ] **Step 9: Commit only if real-evidence commit is separately authorized**

```bat
git add META/prospective-go/single-cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥 handoff.md
git commit -m "eval: bind first immediate retrospective case"
```

Exclude custody originals, external root records, witness key material and unrelated worktree files.

## Final Self-Review Checklist

- [ ] **Spec coverage:** map sections 3—14 of the approved design to Tasks 1—16: three evidence classes and gate IDs (Tasks 6—11), immutable names/parents (Task 1), state/data flow (Tasks 2—7), release gate (Task 5/6), high risk (Task 8), 10-case aggregation (Task 9), witness environment (Task 5/12/15), STOP/recovery (Tasks 1/3/5/7/9), compatibility/docs (Task 12), first case (Tasks 14—16), and acceptance (Task 13).
- [ ] **Required item coverage:** verify explicit coverage of all 14 user-listed items: single-record intake; single-case bundle; staged frozen run; witness chain/verification/release; immediate template/evidence classification; exactly-one three-month future question/separate ledger; dual review/arbitration; 10-case parent hashes; 20/15 candidate GO; 10/8 future GO; old 30-case isolation; first-case execution/hard stop; protocol/action/tools/handoff; focused/full verification/no production change.
- [ ] **Placeholder scan:** run the command below; allowed operational placeholders are only angle-bracket path/time/root tokens in human-run commands and the literal signed checkpoint identity reference. No deferred-work marker or omitted-code marker may remain in implementation instructions.

```bat
python -c "from pathlib import Path; p=Path(r'docs/superpowers/plans/2026-07-16-single-case-immediate-freeze-feedback.md'); s=p.read_text(encoding='utf-8'); bad=['T'+'BD','T'+'ODO','implement '+'later','类似 '+'Task','适当'+'处理']; print({x:s.count(x) for x in bad}); raise SystemExit(any(x in s for x in bad))"
```

Expected: every count is 0 and exit code 0.

- [ ] **Type consistency:** mechanically compare definitions/usages for `ArtifactRef`, `GateEvidence`, `build_single_case_intake`, `prepare_single_case_blind_bundle`, `build_single_case_staged_frozen_run`, `verify_single_case_freeze_chain`, `build_feedback_release_credential`, `collect_immediate_retrospective`, `collect_future_observation`, `build_case_completion`, `build_cohort_manifest`, `evaluate_prediction_capability_candidate`, and `evaluate_future_empirical`; parameter/property names must match every later task.
- [ ] **Security review:** search plan and implementation diff for `SCHOOL_CAPABILITY_WITNESS_KEY=` followed by a non-empty value, fixture secrets outside tests, environment dumps, feedback reads before verification, and production entry modifications. The plan must never schedule an agent to set, see or receive a real key.
- [ ] **Command review:** all commands are valid Windows `cmd.exe`; no `grep`, `sed`, `awk`, `cat`, `rm`, `cp`, `mv`, Bash `$VAR`, or PowerShell-only syntax.
- [ ] **Plan-only rule:** save this plan but do not commit it. Implementation commits listed above are for the later execution session after user review.
