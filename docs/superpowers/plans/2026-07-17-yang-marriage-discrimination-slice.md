# Yang Marriage Discrimination Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按已批准的[设计规格](../specs/2026-07-17-yang-marriage-discrimination-slice-design.md)，在不改变生产规则、公共契约或默认入口的前提下，建立杨派婚姻原局 `pressure / event / abstain` 局部判别切片，并机械证明只有同时满足夫妻宫事件锚与独立配偶结构交互的 `event` 能进入 L2-L6。

**Architecture:** 新增一个只消费现有 `ChartFactLedger` 与 `ChartFeatureVector` 的纯函数模块，将输入规范化为原始信号、按六个固定结构家族去重，再通过具名 A+B 必要门生成不可变局部 DTO。新增专用切片 assembler，复用 `apply_ziping_career_slice()` 的目标先剥离、非目标走旧桥、合并后拒绝重复、直接调用 L3-L6 的模式，并返回现有 `DecisionRun` 而不是定义第三套 run 模型；`pressure` 与 `abstain` 只保留在局部审计结果中。

**Tech Stack:** Python 3、stdlib `dataclasses` / `hashlib` / `json` / `pathlib` / `typing`、现有 `engine.decision` L1-L6 与 `ChartFeatureVector`、pytest、Windows 10 `cmd.exe`。

## Global Constraints

- 第一阶段只实现杨派婚姻原局 `pressure / event / abstain` 三态；硬阻断优先 `abstain`，A+B 同时通过才为 `event`，否则有 matched family 为 `pressure`，无信号为 `abstain`。
- 门 A 固定为日支参与且 canonical 去重后的冲或刑/害；全局冲突强度、非日支 pair、合与暗合均不得成为事件锚。
- 门 B 固定为与门 A 不同的 `spouse_star_peer_interaction`、`spouse_star_output_interaction` 或 `spouse_star_configuration`；配偶星弱/缺失和无配偶星上下文的全局比劫/食伤只能形成 pressure。
- 同一家族最多贡献一次；pair 先转为合法地支组成的 canonical 无序二元 tuple，再稳定排序；同源别名、多个 pair 与 `branch_conflict_intensity` 不得膨胀资格数。
- 只有 `event` 可转换为现有 `SchoolClaim` 并进入 L3-L6；`pressure` / `abstain` 的目标对象在 L2、L3、L4、L5、L6 必须全部为零；event adapter 收到非 event 必须抛出 `ValueError`。
- `theory/production/claim-rules-v1.yaml` 保持字节不变；不得修改或 staged 标记 `YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1`。
- 不修改公共 `Claim`、`SchoolClaim`、`BlindSchoolOutput` schema，不新增公共 pressure task，不修改 L7、模板、报告、默认 `run_pipeline()`、`DEFAULT_RUNNER_REGISTRY`、概率公式、覆盖矩阵、feedback 或学习链。
- 专用切片只由测试显式调用；不修改 `engine/v5/yang_runner.py`，旧 production candidate 与切片结果冲突时只在测试中观察，不回写生产路径。
- 新合成夹具是唯一机械门禁；不得引用 `cases/`、`reports/`、历史 `feedback.md`、prospective frozen run 或 `tests/r10/fixtures/r6_ziping_career_baseline.json`，不得据历史结果调整家族、阈值或 expected state。
- `event` 只表达非必然的原局事件资格；statement 禁止出现“必离”“100%”“多婚命”。验收结论只能写“杨派婚姻判别切片在合成矩阵上满足三态、去重、必要门与层级隔离规格”，不得宣称准确率提升、GO、可切生产或可替换规则。
- 当前 Python 3.14 环境缺少 `sxtwl`；不得创建 fake module、不得 monkeypatch `sys.modules` 冒充依赖。纯函数与切片测试直接构造 `ChartFactLedger` / `ChartFeatureVector`，不得调用 `build_chart_feature_vector()`；全量回归必须在能安装 `requirements-dev.txt` 中 `sxtwl==2.0.7` 的受支持 Python 环境执行。
- 当前工作树已有大量未提交清理变更。实施前必须使用 `superpowers:using-git-worktrees` 创建隔离 worktree 与专用分支；所有命令和逐任务提交只在该 worktree 执行，当前工作树不得参与实施或提交。
- 所有命令使用 Windows 10 `cmd.exe` 语法；Python 测试统一使用 `python -m pytest`，命令连接使用 `&&`，不得使用 Unix shell 命令。
- 本计划文件不提交；实施中的每个 Task 在 RED→GREEN 与任务级 diff 审查后单独提交。最终任务只验证并更新必要机器事实源，不提交本计划。

---

## File Responsibility Map

| File | Action | Single responsibility |
|---|---|---|
| `engine/decision/yang_marriage.py` | Create | 定义局部不可变 DTO、原始信号提取、canonical pair 校验、结构家族归并和 A+B 三态纯判别；不构造公共 claim。 |
| `engine/decision/yang_marriage_slice.py` | Create | 将唯一 `event` 适配为 `SchoolClaim`，剥离旧目标、保留非目标、拒绝重复 ID，并用现有 L3-L6 builder 装配现有 `DecisionRun`。 |
| `tests/yang_marriage/__init__.py` | Create | 标记专用合成测试包；不暴露生产 API。 |
| `tests/yang_marriage/fixtures.py` | Create | 直接构造不依赖 `sxtwl` 的合成 chart/CFV、矩阵 case 与非目标 `V5Output` 测试数据。 |
| `tests/yang_marriage/test_domain_model.py` | Create | 验证局部 DTO 冻结性、合法状态组合、唯一家族、稳定序列化与 event adapter fail-closed 前置契约。 |
| `tests/yang_marriage/test_signal_families.py` | Create | 验证性别/partial 阻断、夫妻宫 pair canonical 化、六个家族提取、同源去重和具名 A+B 门。 |
| `tests/yang_marriage/test_synthetic_matrix.py` | Create | 对 M1/F1/F2、S1/S2、P1-P3、G1-G3、I1-I3、D1-D4、首个证伪点逐项断言三态与家族。 |
| `tests/yang_marriage/test_slice_layers.py` | Create | 验证 event 唯一进入 L2-L6、pressure/abstain 全层隔离、完整 trace、重复 claim fail-fast、确定性和非目标逐字段零回归。 |
| `tests/yang_marriage/test_static_isolation.py` | Create | 静态扫描禁止历史/报告/学习依赖、禁止计数阈值旁路，并锁定公共 schema、生产 YAML、默认 registry、pipeline、L7/模板边界。 |
| [`META/project-state.json`](../../../META/project-state.json) | Modify | 在全部机械门禁通过后仅记录该专用切片的事实状态为合成规格通过且 production/default/report 仍未切换。 |
| [`tests/test_project_metadata.py`](../../../tests/test_project_metadata.py) | Modify | 验证新增项目状态键使用保守状态值且不宣称 GO、准确率或生产替换。 |

## Execution Precondition: Isolated worktree and supported environments

在执行 Task 1 前完成，不产生功能提交：

1. 在当前仓库只读取分支与 worktree 状态，不清理、不 stash、不提交现有工作树：

```bat
git status --short && git branch --show-current && git worktree list
```

Expected: 可看到当前工作树的既有未提交清理变更；不得执行 `git add`、`git commit`、`git reset` 或 `git stash`。

2. 按 `superpowers:using-git-worktrees` 选择仓库外 sibling 目录并创建专用分支；以下命令中的目录与分支名固定使用本计划值：

```bat
git worktree add ..\mangpai-fusion-yang-marriage -b feat/yang-marriage-discrimination-slice HEAD
```

Expected: 新建 `..\mangpai-fusion-yang-marriage`，分支为 `feat/yang-marriage-discrimination-slice`；原工作树状态不变。后续所有命令的 working directory 必须是该目录。

3. 在隔离 worktree 建立两级验证前提：当前 Python 3.14 仅跑不导入 `sxtwl` 的专用纯函数测试；另用能成功安装依赖的受支持 Python 环境跑全量测试。不得 fake module：

```bat
python --version && python -c "import sys; print(sys.executable)" && python -m pytest --version
```

Expected: 当前解释器信息可审计；若为 Python 3.14 且 `sxtwl` 不可安装，只执行 `tests/yang_marriage/` 与不触发该依赖的静态门禁。

受支持环境的最终前提命令：

```bat
py -0p && py -3.12 -m venv .venv312 && .venv312\Scripts\python -m pip install -r requirements-dev.txt && .venv312\Scripts\python -c "import sxtwl; print(sxtwl.__file__)"
```

Expected: 若本机已安装可用 Python 3.12，则依赖安装成功并打印真实 site-packages 中的 `sxtwl` 路径；若该解释器不存在，最终全量验证保持未满足并不得宣称完成，但纯函数门禁仍可运行。

## Phase 1: Local discrimination contract

### Task 1: Immutable local domain model and invariant enforcement

**Files:**
- Create: `engine/decision/yang_marriage.py`
- Create: `tests/yang_marriage/__init__.py`
- Create: `tests/yang_marriage/test_domain_model.py`

**Interfaces:**
- Consumes: only stdlib values in this task.
- Produces: `YangMarriageState = Literal["pressure", "event", "abstain"]`; `SexBasis`; `FamilyKey`; `CanonicalPair`; frozen `YangMarriageRawSignals`, `YangMarriageFamilyEvidence`, `YangMarriageDiscrimination`; deterministic `to_dict()` methods.
- Invariants: one family key at most once; `event` iff A+B and no blockers; `pressure` has matched family and not both gates; `abstain` never carries an event payload; no probability, time window, L7 text or public claim state fields.

- [ ] **Step 1: Write the failing invariant tests**

```python
from dataclasses import FrozenInstanceError
import pytest

from engine.decision.yang_marriage import (
    YangMarriageDiscrimination,
    YangMarriageFamilyEvidence,
)


def family(key: str) -> YangMarriageFamilyEvidence:
    return YangMarriageFamilyEvidence(
        family_key=key,
        matched=True,
        fact_refs=("four_pillars.day",),
        feature_refs=("chong_pairs",),
        canonical_pairs=(("午", "子"),) if key == "spouse_palace_event_anchor" else (),
        reason_codes=(f"matched_{key}",),
        detail="合成审计证据",
    )


def test_event_requires_named_a_and_b_gates_and_is_frozen() -> None:
    result = YangMarriageDiscrimination(
        schema_version="yang-marriage-discrimination/v1",
        case_id="YM-SYN-M1",
        state="event",
        sex_basis="male_wealth",
        spouse_palace_branch="子",
        families=(family("spouse_palace_event_anchor"), family("spouse_star_peer_interaction")),
        event_anchor_passed=True,
        independent_spouse_interaction_passed=True,
        blocking_reason_codes=(),
        falsifier="婚姻史无离婚或再婚则证伪。",
        source_rule_refs=("theory/yang/index.yaml#M2-Y-068",),
    )
    assert result.to_dict()["state"] == "event"
    assert "probability" not in result.to_dict()
    with pytest.raises(FrozenInstanceError):
        result.state = "pressure"  # type: ignore[misc]


def test_duplicate_family_and_inconsistent_event_are_rejected() -> None:
    anchor = family("spouse_palace_event_anchor")
    with pytest.raises(ValueError, match="duplicate family_key"):
        YangMarriageDiscrimination(
            "yang-marriage-discrimination/v1", "YM-SYN-DUP", "pressure",
            "male_wealth", "子", (anchor, anchor), True, False,
            ("missing_independent_spouse_interaction",),
            "存在压力不等于事件。", (),
        )
    with pytest.raises(ValueError, match="event requires both named gates"):
        YangMarriageDiscrimination(
            "yang-marriage-discrimination/v1", "YM-SYN-BAD", "event",
            "male_wealth", "子", (anchor,), True, False, (),
            "婚姻史无离婚或再婚则证伪。", (),
        )
```

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/yang_marriage/test_domain_model.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'engine.decision.yang_marriage'`.

- [ ] **Step 3: Implement the frozen DTOs and exact invariant checks**

```python
from dataclasses import dataclass
from typing import Any, Literal

YangMarriageState = Literal["pressure", "event", "abstain"]
SexBasis = Literal["male_wealth", "female_official", "unknown"]
FamilyKey = Literal[
    "spouse_palace_event_anchor",
    "spouse_star_peer_interaction",
    "spouse_star_output_interaction",
    "spouse_star_configuration",
    "spouse_star_context_pressure",
    "ambient_relationship_pressure",
]
CanonicalPair = tuple[str, str]


@dataclass(frozen=True)
class YangMarriageFamilyEvidence:
    family_key: FamilyKey
    matched: bool
    fact_refs: tuple[str, ...]
    feature_refs: tuple[str, ...]
    canonical_pairs: tuple[CanonicalPair, ...]
    reason_codes: tuple[str, ...]
    detail: str

    def __post_init__(self) -> None:
        if not self.matched or not self.reason_codes or not self.detail.strip():
            raise ValueError("matched family requires reason_codes and detail")
        object.__setattr__(self, "fact_refs", tuple(sorted(set(self.fact_refs))))
        object.__setattr__(self, "feature_refs", tuple(sorted(set(self.feature_refs))))
        object.__setattr__(self, "canonical_pairs", tuple(sorted(set(self.canonical_pairs))))
        object.__setattr__(self, "reason_codes", tuple(sorted(set(self.reason_codes))))

    def to_dict(self) -> dict[str, Any]:
        return {
            "family_key": self.family_key,
            "matched": self.matched,
            "fact_refs": list(self.fact_refs),
            "feature_refs": list(self.feature_refs),
            "canonical_pairs": [list(pair) for pair in self.canonical_pairs],
            "reason_codes": list(self.reason_codes),
            "detail": self.detail,
        }


@dataclass(frozen=True)
class YangMarriageDiscrimination:
    schema_version: str
    case_id: str
    state: YangMarriageState
    sex_basis: SexBasis
    spouse_palace_branch: str
    families: tuple[YangMarriageFamilyEvidence, ...]
    event_anchor_passed: bool
    independent_spouse_interaction_passed: bool
    blocking_reason_codes: tuple[str, ...]
    falsifier: str
    source_rule_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        keys = [item.family_key for item in self.families]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate family_key")
        if self.state == "event" and (
            not self.event_anchor_passed
            or not self.independent_spouse_interaction_passed
            or self.blocking_reason_codes
        ):
            raise ValueError("event requires both named gates and no blockers")
        if self.state == "pressure" and (
            not self.families
            or (self.event_anchor_passed and self.independent_spouse_interaction_passed)
            or not self.blocking_reason_codes
        ):
            raise ValueError("pressure requires evidence, a failed gate, and blockers")
        if self.state == "abstain" and not self.blocking_reason_codes:
            raise ValueError("abstain requires blocking reasons")
        if not self.case_id.strip() or not self.schema_version.strip() or not self.falsifier.strip():
            raise ValueError("identity and falsifier are required")
        object.__setattr__(self, "families", tuple(sorted(self.families, key=lambda item: item.family_key)))
        object.__setattr__(self, "blocking_reason_codes", tuple(sorted(set(self.blocking_reason_codes))))
        object.__setattr__(self, "source_rule_refs", tuple(sorted(set(self.source_rule_refs))))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "state": self.state,
            "sex_basis": self.sex_basis,
            "spouse_palace_branch": self.spouse_palace_branch,
            "families": [item.to_dict() for item in self.families],
            "event_anchor_passed": self.event_anchor_passed,
            "independent_spouse_interaction_passed": self.independent_spouse_interaction_passed,
            "blocking_reason_codes": list(self.blocking_reason_codes),
            "falsifier": self.falsifier,
            "source_rule_refs": list(self.source_rule_refs),
        }
```

Also define frozen `YangMarriageRawSignals` in this file with explicit fields used by Task 2: `case_id: str`, `sex_basis: SexBasis`, `spouse_palace_branch: str`, `canonical_palace_pairs: tuple[CanonicalPair, ...]`, `spouse_star_present: bool`, `spouse_star_count: int`, `peer_heavy: bool`, `output_heavy: bool`, `mixed_official_kill: bool`, `blocking_reason_codes: tuple[str, ...]`. Its `__post_init__()` must stabilize tuples and reject negative counts; it must not infer state.

- [ ] **Step 4: Run GREEN**

Run: `python -m pytest tests/yang_marriage/test_domain_model.py -q`

Expected: PASS; invalid state/gate combinations and duplicate families raise exact `ValueError`, and DTO mutation raises `FrozenInstanceError`.

- [ ] **Step 5: Review isolated diff and commit**

```bat
git status --short && git diff --check && git diff -- engine/decision/yang_marriage.py tests/yang_marriage/__init__.py tests/yang_marriage/test_domain_model.py && git add engine/decision/yang_marriage.py tests/yang_marriage/__init__.py tests/yang_marriage/test_domain_model.py && git diff --cached --name-only && git commit -m "feat: add yang marriage discrimination domain model"
```

Expected: staged names are exactly the three files listed above; commit succeeds without including the plan or existing cleanup changes.

### Task 2: Raw signal extraction and canonical pair validation

**Files:**
- Modify: `engine/decision/yang_marriage.py`
- Create: `tests/yang_marriage/fixtures.py`
- Create: `tests/yang_marriage/test_signal_families.py`

**Interfaces:**
- Consumes: `extract_yang_marriage_signals(case_id: str, chart: ChartFactLedger, features: ChartFeatureVector) -> YangMarriageRawSignals`.
- Produces: `_canonical_pair(pair: tuple[str, str]) -> CanonicalPair`; stable day-branch anchor pairs; sex-specific spouse-star context; explicit blocker codes `missing_or_unknown_sex`, `incomplete_evidence`, `missing_or_invalid_day_pillar`, `invalid_relationship_pair`.
- Does not consume: `build_chart_feature_vector()`, `sxtwl`, `he_pairs`, timing fields, reports, feedback or production YAML.

- [ ] **Step 1: Add direct-construction fixtures and failing extraction tests**

```python
# tests/yang_marriage/fixtures.py
from dataclasses import replace
from engine.decision.models import ChartFactLedger
from engine.features.types import ChartFeatureVector


def chart(case_id: str, *, sex: str = "乾", day: str = "壬子") -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker=sex,
        four_pillars={"year": "甲午", "month": "戊寅", "day": day, "hour": "辛丑"},
        raw_source_hash=f"raw-{case_id}",
    )


def cfv(case_id: str, **changes: object) -> ChartFeatureVector:
    base = ChartFeatureVector(
        schema_version="cfv-v1", chart_id=case_id,
        element_counts={"木": 2, "火": 2, "土": 2, "金": 1, "水": 1},
        element_energy={"木": .2, "火": .2, "土": .2, "金": .2, "水": .2},
        dominant_element="木", missing_elements=(), element_concentration=.25,
        day_master="壬", day_master_element="水", month_branch="寅", month_lord="甲",
        rooted_count=1, supporting_count=3, draining_count=5, monthly_command_favorable=False,
        ten_god_counts={"正财": 1, "偏财": 0, "正官": 1, "七杀": 0,
                        "比肩": 0, "劫财": 0, "食神": 0, "伤官": 0},
        has_official=True, has_wealth=True, has_output=False, has_resource=False,
        mixed_official_kill=False, chong_pairs=(), he_pairs=(), xing_hai_pairs=(),
        branch_conflict_intensity=0.0, cold_warm_axis=0.0, dry_wet_axis=0.0,
        climate_extreme=False, has_hour_pillar=True, evidence_completeness="full",
    )
    return replace(base, **changes)
```

```python
# tests/yang_marriage/test_signal_families.py
import pytest
from engine.decision.yang_marriage import extract_yang_marriage_signals
from tests.yang_marriage.fixtures import cfv, chart


def test_pair_order_and_cross_collection_duplicates_are_canonicalized_once() -> None:
    signals = extract_yang_marriage_signals(
        "YM-SYN-D1", chart("YM-SYN-D1"),
        cfv("YM-SYN-D1", chong_pairs=(("子", "午"),), xing_hai_pairs=(("午", "子"),)),
    )
    assert signals.canonical_palace_pairs == (("午", "子"),)


@pytest.mark.parametrize(
    ("sex", "day", "completeness", "reason"),
    [("", "壬子", "full", "missing_or_unknown_sex"),
     ("乾", "壬", "full", "missing_or_invalid_day_pillar"),
     ("坤", "壬子", "partial", "incomplete_evidence"),
     ("乾", "壬子", "no_hour", "incomplete_evidence")],
)
def test_missing_or_partial_input_is_explicitly_blocked(
    sex: str, day: str, completeness: str, reason: str,
) -> None:
    signals = extract_yang_marriage_signals(
        "YM-SYN-I", chart("YM-SYN-I", sex=sex, day=day),
        cfv("YM-SYN-I", evidence_completeness=completeness),
    )
    assert reason in signals.blocking_reason_codes


def test_non_day_branch_conflict_does_not_create_palace_anchor() -> None:
    signals = extract_yang_marriage_signals(
        "YM-SYN-S2", chart("YM-SYN-S2"),
        cfv("YM-SYN-S2", chong_pairs=(("寅", "申"),), branch_conflict_intensity=1.0),
    )
    assert signals.canonical_palace_pairs == ()
```

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/yang_marriage/test_signal_families.py -q`

Expected: FAIL with `ImportError` because `extract_yang_marriage_signals` is not defined.

- [ ] **Step 3: Implement minimal pure extraction**

```python
_BRANCHES = frozenset("子丑寅卯辰巳午未申酉戌亥")
_MALE = frozenset({"乾", "男", "男命", "乾造", "M", "male"})
_FEMALE = frozenset({"坤", "女", "女命", "坤造", "F", "female"})


def _canonical_pair(pair: tuple[str, str]) -> CanonicalPair:
    if len(pair) != 2 or pair[0] not in _BRANCHES or pair[1] not in _BRANCHES or pair[0] == pair[1]:
        raise ValueError("invalid relationship pair")
    return tuple(sorted(pair))  # type: ignore[return-value]


def extract_yang_marriage_signals(
    case_id: str,
    chart: ChartFactLedger,
    features: ChartFeatureVector,
) -> YangMarriageRawSignals:
    blockers: set[str] = set()
    marker = chart.sex_marker.strip()
    sex_basis: SexBasis = (
        "male_wealth" if marker in _MALE
        else "female_official" if marker in _FEMALE
        else "unknown"
    )
    if sex_basis == "unknown":
        blockers.add("missing_or_unknown_sex")
    if features.evidence_completeness != "full":
        blockers.add("incomplete_evidence")
    day = str(chart.four_pillars.get("day", chart.four_pillars.get("日柱", ""))).strip()
    day_branch = day[1] if len(day) == 2 and day[1] in _BRANCHES else ""
    if not day_branch:
        blockers.add("missing_or_invalid_day_pillar")
    palace_pairs: set[CanonicalPair] = set()
    try:
        for pair in features.chong_pairs + features.xing_hai_pairs:
            canonical = _canonical_pair(pair)
            if day_branch and day_branch in canonical:
                palace_pairs.add(canonical)
    except ValueError:
        blockers.add("invalid_relationship_pair")
        palace_pairs.clear()
    wealth_count = sum(int(features.ten_god_counts.get(name, 0)) for name in ("正财", "偏财"))
    official_count = sum(int(features.ten_god_counts.get(name, 0)) for name in ("正官", "七杀"))
    spouse_count = wealth_count if sex_basis == "male_wealth" else official_count if sex_basis == "female_official" else 0
    spouse_present = (
        features.has_wealth and spouse_count > 0 if sex_basis == "male_wealth"
        else features.has_official and spouse_count > 0 if sex_basis == "female_official"
        else False
    )
    return YangMarriageRawSignals(
        case_id=case_id,
        sex_basis=sex_basis,
        spouse_palace_branch=day_branch,
        canonical_palace_pairs=tuple(sorted(palace_pairs)),
        spouse_star_present=spouse_present,
        spouse_star_count=spouse_count,
        peer_heavy=sum(int(features.ten_god_counts.get(name, 0)) for name in ("比肩", "劫财")) >= 3,
        output_heavy=sum(int(features.ten_god_counts.get(name, 0)) for name in ("食神", "伤官")) >= 4,
        mixed_official_kill=sex_basis == "female_official" and features.mixed_official_kill,
        blocking_reason_codes=tuple(sorted(blockers)),
    )
```

Keep threshold values only as raw-signal compatibility facts inherited from the existing runner; do not sum them and do not use them as an event threshold. Invalid pair input must retain `invalid_relationship_pair` and later force `abstain`.

- [ ] **Step 4: Run GREEN without importing `sxtwl`**

Run: `python -m pytest tests/yang_marriage/test_domain_model.py tests/yang_marriage/test_signal_families.py -q`

Expected: PASS under Python 3.14 even when `python -c "import sxtwl"` fails, because tests import `engine.features.types` and directly instantiate CFV.

- [ ] **Step 5: Review isolated diff and commit**

```bat
git status --short && git diff --check && git add engine/decision/yang_marriage.py tests/yang_marriage/fixtures.py tests/yang_marriage/test_signal_families.py && git diff --cached --name-only && git commit -m "feat: extract yang marriage structural signals"
```

Expected: staged names exactly match this task; commit succeeds.

### Task 3: Structure-family reducer and named A+B discriminator

**Files:**
- Modify: `engine/decision/yang_marriage.py`
- Modify: `tests/yang_marriage/test_signal_families.py`

**Interfaces:**
- Consumes: `reduce_yang_marriage_families(signals: YangMarriageRawSignals) -> tuple[YangMarriageFamilyEvidence, ...]`.
- Produces: `discriminate_yang_marriage(case_id: str, chart: ChartFactLedger, features: ChartFeatureVector) -> YangMarriageDiscrimination`.
- Family order is stable by key; event-interaction keys are a fixed set; state uses named boolean conjunction, never family count or `independent_signal_count`.

- [ ] **Step 1: Write failing family and gate tests**

```python
from engine.decision.yang_marriage import discriminate_yang_marriage


def keys(result) -> tuple[str, ...]:
    return tuple(item.family_key for item in result.families)


def test_male_event_requires_palace_anchor_and_wealth_peer_interaction() -> None:
    result = discriminate_yang_marriage(
        "YM-SYN-M1", chart("YM-SYN-M1", sex="乾"),
        cfv("YM-SYN-M1", chong_pairs=(("子", "午"),),
            ten_god_counts={"正财": 1, "偏财": 0, "正官": 0, "七杀": 0,
                            "比肩": 2, "劫财": 1, "食神": 0, "伤官": 0}),
    )
    assert result.state == "event"
    assert keys(result) == ("spouse_palace_event_anchor", "spouse_star_peer_interaction")
    assert result.event_anchor_passed and result.independent_spouse_interaction_passed


def test_two_non_palace_signals_are_pressure_not_event() -> None:
    result = discriminate_yang_marriage(
        "YM-SYN-FALSIFIER", chart("YM-SYN-FALSIFIER", sex="乾"),
        cfv("YM-SYN-FALSIFIER", has_wealth=False,
            ten_god_counts={"正财": 0, "偏财": 0, "正官": 0, "七杀": 0,
                            "比肩": 2, "劫财": 2, "食神": 0, "伤官": 0}),
    )
    assert result.state == "pressure"
    assert result.event_anchor_passed is False
    assert "spouse_star_context_pressure" in keys(result)
    assert "ambient_relationship_pressure" in keys(result)


def test_palace_pair_multiplicity_never_creates_second_family() -> None:
    result = discriminate_yang_marriage(
        "YM-SYN-D2", chart("YM-SYN-D2"),
        cfv("YM-SYN-D2", chong_pairs=(("子", "午"), ("子", "卯"))),
    )
    assert result.state == "pressure"
    assert keys(result).count("spouse_palace_event_anchor") == 1
    assert len(result.families[0].canonical_pairs) == 2
```

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/yang_marriage/test_signal_families.py -q`

Expected: FAIL with `ImportError` because reducer/discriminator functions do not exist.

- [ ] **Step 3: Implement exact six-family reduction and state precedence**

```python
_EVENT_INTERACTIONS = frozenset({
    "spouse_star_peer_interaction",
    "spouse_star_output_interaction",
    "spouse_star_configuration",
})


def reduce_yang_marriage_families(
    signals: YangMarriageRawSignals,
) -> tuple[YangMarriageFamilyEvidence, ...]:
    families: dict[FamilyKey, YangMarriageFamilyEvidence] = {}

    def add(key: FamilyKey, *, facts: tuple[str, ...], features: tuple[str, ...],
            pairs: tuple[CanonicalPair, ...] = (), reason: str, detail: str) -> None:
        families[key] = YangMarriageFamilyEvidence(
            key, True, facts, features, pairs, (reason,), detail,
        )

    if signals.canonical_palace_pairs:
        add("spouse_palace_event_anchor", facts=("four_pillars.day",),
            features=("chong_pairs", "xing_hai_pairs"), pairs=signals.canonical_palace_pairs,
            reason="day_branch_disrupted", detail="日支参与去重后的冲或刑害。")
    if signals.sex_basis == "male_wealth" and signals.spouse_star_present and signals.peer_heavy:
        add("spouse_star_peer_interaction", facts=("sex_marker",),
            features=("has_wealth", "ten_god_counts.正财", "ten_god_counts.偏财",
                      "ten_god_counts.比肩", "ten_god_counts.劫财"),
            reason="male_wealth_peer_interaction", detail="男命财星上下文与比劫结构显式交互。")
    if signals.sex_basis == "female_official" and signals.spouse_star_present and signals.output_heavy:
        add("spouse_star_output_interaction", facts=("sex_marker",),
            features=("has_official", "ten_god_counts.正官", "ten_god_counts.七杀",
                      "ten_god_counts.食神", "ten_god_counts.伤官"),
            reason="female_official_output_interaction", detail="女命官杀上下文与食伤结构显式交互。")
    if signals.sex_basis == "female_official" and signals.mixed_official_kill:
        add("spouse_star_configuration", facts=("sex_marker",),
            features=("mixed_official_kill", "ten_god_counts.正官", "ten_god_counts.七杀"),
            reason="female_mixed_official_configuration", detail="女命正官七杀复合配置按一个家族归并。")
    if signals.sex_basis != "unknown" and (not signals.spouse_star_present or signals.spouse_star_count <= 1):
        add("spouse_star_context_pressure", facts=("sex_marker",),
            features=("has_wealth", "has_official", "ten_god_counts.正财", "ten_god_counts.偏财",
                      "ten_god_counts.正官", "ten_god_counts.七杀"),
            reason="spouse_star_weak_or_missing", detail="配偶星弱或缺失只支持关系压力。")
    ambient = ((signals.sex_basis != "male_wealth" or not signals.spouse_star_present) and signals.peer_heavy) or (
        (signals.sex_basis != "female_official" or not signals.spouse_star_present) and signals.output_heavy
    )
    if ambient:
        add("ambient_relationship_pressure", facts=("sex_marker",),
            features=("ten_god_counts.比肩", "ten_god_counts.劫财", "ten_god_counts.食神", "ten_god_counts.伤官"),
            reason="ambient_pressure_without_spouse_interaction", detail="全局压力缺少性别对应配偶星交互上下文。")
    return tuple(sorted(families.values(), key=lambda item: item.family_key))


def discriminate_yang_marriage(
    case_id: str,
    chart: ChartFactLedger,
    features: ChartFeatureVector,
) -> YangMarriageDiscrimination:
    signals = extract_yang_marriage_signals(case_id, chart, features)
    families = reduce_yang_marriage_families(signals)
    anchor = any(item.family_key == "spouse_palace_event_anchor" for item in families)
    interaction = any(item.family_key in _EVENT_INTERACTIONS for item in families)
    blockers = list(signals.blocking_reason_codes)
    if blockers:
        state: YangMarriageState = "abstain"
        falsifier = "补齐并校验输入后重算。"
    elif anchor and interaction:
        state = "event"
        falsifier = "若婚姻史中没有离婚或再婚记录，则命题证伪。"
    elif families:
        state = "pressure"
        if not anchor:
            blockers.append("missing_spouse_palace_event_anchor")
        if not interaction:
            blockers.append("missing_independent_spouse_interaction")
        falsifier = "存在关系压力不等于离婚或再婚事件成立。"
    else:
        state = "abstain"
        blockers.append("insufficient_yang_marriage_signal")
        falsifier = "当前无足够杨派婚姻信号；补充可验证结构后重算。"
    return YangMarriageDiscrimination(
        "yang-marriage-discrimination/v1", case_id, state, signals.sex_basis,
        signals.spouse_palace_branch, families, anchor, interaction,
        tuple(sorted(set(blockers))), falsifier,
        ("theory/yang/index.yaml#M2-Y-068", "theory/yang/index.yaml#M2-Y-088"),
    )
```

For a hard blocker, preserve extracted families only for audit but force `abstain`; the adapter in Task 5 must never consume them. Add tests proving female output interaction requires actual official context and mixed-official aliases produce one configuration family.

- [ ] **Step 4: Run GREEN**

Run: `python -m pytest tests/yang_marriage/test_domain_model.py tests/yang_marriage/test_signal_families.py -q`

Expected: PASS; the first falsifier is `pressure`, multiple palace pairs remain one family, and no assertion uses a family-count threshold.

- [ ] **Step 5: Review isolated diff and commit**

```bat
git status --short && git diff --check && git add engine/decision/yang_marriage.py tests/yang_marriage/test_signal_families.py && git diff --cached --name-only && git commit -m "feat: discriminate yang marriage by named structure gates"
```

Expected: only the two task files are staged; commit succeeds.

## Phase 2: Synthetic mechanical gate

### Task 4: Complete synthetic fixture matrix and deterministic discrimination gate

**Files:**
- Modify: `tests/yang_marriage/fixtures.py`
- Create: `tests/yang_marriage/test_synthetic_matrix.py`

**Interfaces:**
- Consumes: `SyntheticMarriageCase(case_id, chart, features, expected_state, expected_families)` and `synthetic_cases() -> tuple[SyntheticMarriageCase, ...]` from fixtures.
- Produces: all required M1/F1/F2, S1/S2, P1-P3, G1-G3, I1-I3, D1-D4, X1 first-falsifier and R1 discrimination assertions; no file-backed historical data.

- [ ] **Step 1: Define the full matrix and failing parametrized gate**

```python
# append to tests/yang_marriage/fixtures.py
from dataclasses import dataclass

@dataclass(frozen=True)
class SyntheticMarriageCase:
    case_id: str
    chart: ChartFactLedger
    features: ChartFeatureVector
    expected_state: str
    expected_families: tuple[str, ...]


def synthetic_cases() -> tuple[SyntheticMarriageCase, ...]:
    male_peer = {"正财": 1, "偏财": 0, "正官": 0, "七杀": 0,
                 "比肩": 2, "劫财": 1, "食神": 0, "伤官": 0}
    female_output = {"正财": 0, "偏财": 0, "正官": 1, "七杀": 0,
                     "比肩": 0, "劫财": 0, "食神": 2, "伤官": 2}
    return (
        SyntheticMarriageCase("YM-SYN-M1", chart("YM-SYN-M1", sex="乾"),
            cfv("YM-SYN-M1", chong_pairs=(("子", "午"),), ten_god_counts=male_peer),
            "event", ("spouse_palace_event_anchor", "spouse_star_peer_interaction")),
        SyntheticMarriageCase("YM-SYN-F1", chart("YM-SYN-F1", sex="坤"),
            cfv("YM-SYN-F1", xing_hai_pairs=(("子", "未"),), ten_god_counts=female_output),
            "event", ("spouse_palace_event_anchor", "spouse_star_output_interaction")),
        SyntheticMarriageCase("YM-SYN-F2", chart("YM-SYN-F2", sex="坤"),
            cfv("YM-SYN-F2", chong_pairs=(("子", "午"),), mixed_official_kill=True,
                ten_god_counts={**female_output, "食神": 0, "伤官": 0, "七杀": 1}),
            "event", ("spouse_palace_event_anchor", "spouse_star_configuration")),
        SyntheticMarriageCase("YM-SYN-S1", chart("YM-SYN-S1"), cfv("YM-SYN-S1",
            ten_god_counts={**male_peer, "比肩": 0, "劫财": 0, "正财": 2}),
            "abstain", ()),
        SyntheticMarriageCase("YM-SYN-S2", chart("YM-SYN-S2"),
            cfv("YM-SYN-S2", chong_pairs=(("寅", "申"),), branch_conflict_intensity=1.0,
                ten_god_counts={**male_peer, "比肩": 0, "劫财": 0, "正财": 2}),
            "abstain", ()),
        SyntheticMarriageCase("YM-SYN-P1", chart("YM-SYN-P1"),
            cfv("YM-SYN-P1", chong_pairs=(("子", "午"),),
                ten_god_counts={**male_peer, "比肩": 0, "劫财": 0, "正财": 2}),
            "pressure", ("spouse_palace_event_anchor",)),
        SyntheticMarriageCase("YM-SYN-P2", chart("YM-SYN-P2"), cfv("YM-SYN-P2", ten_god_counts=male_peer),
            "pressure", ("spouse_star_peer_interaction",)),
        SyntheticMarriageCase("YM-SYN-P3", chart("YM-SYN-P3", sex="坤"),
            cfv("YM-SYN-P3", mixed_official_kill=True,
                ten_god_counts={**female_output, "食神": 0, "伤官": 0, "七杀": 1}),
            "pressure", ("spouse_star_configuration",)),
    )
```

Continue the same function with explicit entries:

- G1: `has_wealth=False`, wealth counts zero, no anchor → exactly `spouse_star_context_pressure`, `pressure`.
- G2: male, wealth absent, peer count 3, no anchor → `ambient_relationship_pressure` plus context pressure, `pressure`; no peer-interaction family.
- G3: female, official absent, output count 4, no anchor → ambient plus context pressure, `pressure`; no output-interaction family.
- I1: `sex=""` → `abstain`, blocker `missing_or_unknown_sex`.
- I2: `day="壬"` → `abstain`, blocker `missing_or_invalid_day_pillar`.
- I3: `evidence_completeness="partial"` → `abstain`, blocker `incomplete_evidence`.
- D1: same day pair in chong and xing/hai, no B → one anchor family and one canonical pair, `pressure`.
- D2: two different day pairs, no B → one anchor family and two canonical pairs, `pressure`.
- D3: female mixed flag plus official counts, no anchor → one configuration family, `pressure`.
- D4: A plus female mixed/config aliases → exactly A plus one configuration family, `event`.
- X1: male, wealth absent/weak plus peer-heavy, no day-branch pair → exactly context pressure plus ambient pressure, `pressure`; this is the separately named first falsifier even though it intentionally shares the same structural pattern as G2.

```python
# tests/yang_marriage/test_synthetic_matrix.py
import json
import pytest
from engine.decision.yang_marriage import discriminate_yang_marriage
from tests.yang_marriage.fixtures import synthetic_cases


@pytest.mark.parametrize("sample", synthetic_cases(), ids=lambda item: item.case_id)
def test_synthetic_matrix_has_exact_state_and_unique_families(sample) -> None:
    result = discriminate_yang_marriage(sample.case_id, sample.chart, sample.features)
    keys = tuple(item.family_key for item in result.families)
    assert result.state == sample.expected_state
    assert keys == sample.expected_families
    assert len(keys) == len(set(keys))
    assert result.state == "event" is (
        result.event_anchor_passed and result.independent_spouse_interaction_passed
        and not result.blocking_reason_codes
    )


def test_r1_is_deterministic_under_repeat_and_pair_order_permutation() -> None:
    sample = next(item for item in synthetic_cases() if item.case_id == "YM-SYN-D4")
    first = discriminate_yang_marriage(sample.case_id, sample.chart, sample.features)
    reversed_features = replace(
        sample.features,
        chong_pairs=tuple(tuple(reversed(pair)) for pair in reversed(sample.features.chong_pairs)),
        xing_hai_pairs=tuple(tuple(reversed(pair)) for pair in reversed(sample.features.xing_hai_pairs)),
    )
    second = discriminate_yang_marriage(sample.case_id, sample.chart, reversed_features)
    assert json.dumps(first.to_dict(), ensure_ascii=False, sort_keys=True) == json.dumps(
        second.to_dict(), ensure_ascii=False, sort_keys=True
    )
```

- [ ] **Step 2: Run RED for the complete matrix**

Run: `python -m pytest tests/yang_marriage/test_synthetic_matrix.py -q`

Expected: FAIL until every named fixture, exact expected family tuple, blocker assertion, D1-D4 cardinality assertion and missing `replace` import are present.

- [ ] **Step 3: Complete fixture-specific assertions without weakening production code**

Add one explicit test per I1-I3 and D1-D4 using `next(item for item in synthetic_cases() if item.case_id == ...)`; assert exact blocker, canonical pair count, forbidden B family and state. Do not adjust extraction thresholds based on any historical case and do not add a generic `signal_count` field.

- [ ] **Step 4: Run GREEN and matrix cardinality gate**

Run: `python -m pytest tests/yang_marriage/test_synthetic_matrix.py -q && python -c "from tests.yang_marriage.fixtures import synthetic_cases; ids=[x.case_id for x in synthetic_cases()]; assert len(ids)==20 and len(ids)==len(set(ids)); print('20 synthetic cases: PASS')"`

Expected: pytest PASS and exact output `20 synthetic cases: PASS`.

- [ ] **Step 5: Review isolated diff and commit**

```bat
git status --short && git diff --check && git add tests/yang_marriage/fixtures.py tests/yang_marriage/test_synthetic_matrix.py && git diff --cached --name-only && git commit -m "test: gate yang marriage discrimination with synthetic matrix"
```

Expected: only the synthetic fixture and matrix test are committed.

## Phase 3: Dedicated L2-L6 slice

### Task 5: Event-only adapter, target stripping, and duplicate claim rejection

**Files:**
- Create: `engine/decision/yang_marriage_slice.py`
- Modify: `tests/yang_marriage/test_domain_model.py`
- Create: `tests/yang_marriage/test_slice_layers.py`

**Interfaces:**
- Consumes: `to_yang_marriage_school_claim(result: YangMarriageDiscrimination, role: SchoolRole) -> SchoolClaim`; `apply_yang_marriage_slice(output: V5Output, chart: ChartFactLedger, features: ChartFeatureVector, applicability: list[SchoolApplicability]) -> tuple[YangMarriageDiscrimination, list[SchoolClaim], list[StructuralVerdict], list[EventHypothesis], list[TimingProbability], list[ArbitrationDecision]]`.
- Produces: exactly one target `SchoolClaim` for event; `_is_yang_marriage_target()` matching `school="yang_qingjuan"`, `domain="婚姻"`, `metadata["task_id"]="marriage.divorce_or_remarriage"`; `_reject_duplicate_claim_ids()` with fail-fast behavior.
- Reuses: `v5_adapter._claims`, existing L3-L6 builders and existing confidence `0.60`; does not call L7 or define a run DTO.

- [ ] **Step 1: Write failing adapter and duplicate tests**

```python
from engine.decision.models import SchoolApplicability
from engine.decision.yang_marriage import discriminate_yang_marriage
from engine.decision.yang_marriage_slice import (
    _reject_duplicate_claim_ids,
    to_yang_marriage_school_claim,
)
from tests.yang_marriage.fixtures import synthetic_cases


def test_adapter_accepts_only_event_and_uses_both_gate_evidence() -> None:
    event = next(item for item in synthetic_cases() if item.case_id == "YM-SYN-M1")
    result = discriminate_yang_marriage(event.case_id, event.chart, event.features)
    claim = to_yang_marriage_school_claim(result, "lead")
    assert claim.school == "yang_qingjuan"
    assert claim.domain == "婚姻"
    assert claim.claim_type == "event_claim"
    assert claim.confidence == 0.60
    assert len(claim.evidence_refs) >= 2
    assert claim.metadata["task_id"] == "marriage.divorce_or_remarriage"
    assert not any(text in claim.statement for text in ("必离", "100%", "多婚命"))


def test_adapter_rejects_pressure_and_duplicate_ids_fail_fast() -> None:
    pressure = next(item for item in synthetic_cases() if item.case_id == "YM-SYN-P1")
    result = discriminate_yang_marriage(pressure.case_id, pressure.chart, pressure.features)
    with pytest.raises(ValueError, match="event only"):
        to_yang_marriage_school_claim(result, "lead")
    event = next(item for item in synthetic_cases() if item.case_id == "YM-SYN-M1")
    claim = to_yang_marriage_school_claim(
        discriminate_yang_marriage(event.case_id, event.chart, event.features), "lead"
    )
    with pytest.raises(ValueError, match="duplicate L2 claim_id"):
        _reject_duplicate_claim_ids([claim, claim])
```

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/yang_marriage/test_domain_model.py tests/yang_marriage/test_slice_layers.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'engine.decision.yang_marriage_slice'`.

- [ ] **Step 3: Implement event adapter and slice assembly**

```python
_TARGET_TASK = "marriage.divorce_or_remarriage"
_TARGET_SCHOOL = "yang_qingjuan"


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]}"


def _is_yang_marriage_target(claim: object) -> bool:
    metadata = getattr(claim, "metadata", {}) or {}
    return (
        getattr(claim, "school", None) == _TARGET_SCHOOL
        and getattr(claim, "domain", None) == "婚姻"
        and metadata.get("task_id") == _TARGET_TASK
    )


def _reject_duplicate_claim_ids(claims: list[SchoolClaim]) -> None:
    seen: set[str] = set()
    for claim in claims:
        if claim.claim_id in seen:
            raise ValueError(f"duplicate L2 claim_id: {claim.claim_id}")
        seen.add(claim.claim_id)


def to_yang_marriage_school_claim(
    result: YangMarriageDiscrimination,
    role: SchoolRole,
) -> SchoolClaim:
    if result.state != "event":
        raise ValueError("yang marriage adapter accepts event only")
    event_families = [item for item in result.families if item.family_key in {
        "spouse_palace_event_anchor", "spouse_star_peer_interaction",
        "spouse_star_output_interaction", "spouse_star_configuration",
    }]
    evidence_refs = [
        _stable_id("yme", result.case_id, family.family_key,
                   ",".join(family.reason_codes), ",".join(map(str, family.canonical_pairs)))
        for family in event_families
    ]
    return SchoolClaim(
        claim_id=_stable_id("ymc", result.case_id, _TARGET_TASK),
        school=_TARGET_SCHOOL,
        role_granted_by_l1=role,
        domain="婚姻",
        claim_type="event_claim",
        statement="杨派原局夫妻宫事件锚与独立配偶结构交互同向，存在离婚或再婚事件风险，但不作必然判断。",
        evidence_refs=evidence_refs,
        confidence=0.60,
        falsifier=result.falsifier,
        dependencies=[result.schema_version],
        metadata={"task_id": _TARGET_TASK, "source_scope": "yang_marriage_discrimination_slice",
                  "family_keys": [item.family_key for item in event_families]},
    )
```

Implement `apply_yang_marriage_slice()` exactly in this order:

```python
result = discriminate_yang_marriage(output.case_id or features.chart_id, chart, features)
yang_roles = [item for item in applicability if item.school == _TARGET_SCHOOL]
if len(yang_roles) > 1:
    raise ValueError("duplicate yang_qingjuan applicability")
legacy_output = replace(output, claims=[c for c in output.claims if not _is_yang_marriage_target(c)])
legacy_l2 = v5_adapter._claims(legacy_output, applicability)
role = yang_roles[0].role if yang_roles else "abstain"
native_l2 = [] if result.state != "event" or role == "abstain" else [to_yang_marriage_school_claim(result, role)]
claims = legacy_l2 + native_l2
_reject_duplicate_claim_ids(claims)
case_id = output.case_id or features.chart_id
verdicts = build_structural_verdicts(case_id, claims)
events = build_event_hypotheses(case_id, verdicts, claims)
timings = build_timing_probabilities(case_id, events)
decisions = build_arbitration_decisions(case_id, events, applicability)
return result, claims, verdicts, events, timings, decisions
```

Do not call `route_schools()` inside this function; it consumes the passed applicability exactly once. Do not modify `v5_adapter`, `l2_v5_claims`, L3-L6 or production runner files.

- [ ] **Step 4: Run GREEN**

Run: `python -m pytest tests/yang_marriage/test_domain_model.py tests/yang_marriage/test_slice_layers.py -q`

Expected: PASS; event adapter emits one conservative target claim with evidence from A and B, pressure is rejected, and duplicate IDs raise before L3.

- [ ] **Step 5: Review isolated diff and commit**

```bat
git status --short && git diff --check && git add engine/decision/yang_marriage_slice.py tests/yang_marriage/test_domain_model.py tests/yang_marriage/test_slice_layers.py && git diff --cached --name-only && git commit -m "feat: add event-only yang marriage decision slice"
```

Expected: exactly three files staged and committed.

### Task 6: Existing DecisionRun assembly and L2-L6 semantic isolation

**Files:**
- Modify: `engine/decision/yang_marriage_slice.py`
- Modify: `tests/yang_marriage/fixtures.py`
- Modify: `tests/yang_marriage/test_slice_layers.py`

**Interfaces:**
- Consumes: `build_yang_marriage_slice_decision_run(output: V5Output, chart: ChartFactLedger, features: ChartFeatureVector, raw_text: str = "") -> tuple[YangMarriageDiscrimination, DecisionRun]`.
- Produces: existing `DecisionRun` with L0/L1/L2-L6 populated, L7-L9 empty; `validate_trace() == []`; target-object filter helpers in tests; byte-for-byte dict equality for non-target legacy objects.
- Does not produce: report items, feedback signals, calibration actions, a new run dataclass, rendered files or persisted audit DTO.

- [ ] **Step 1: Add synthetic V5 output builder and failing end-to-end tests**

```python
# append to tests/yang_marriage/fixtures.py
from engine.v5.domain import V5Claim, V5Confidence, V5Evidence, V5Output


def slice_output(case_id: str, *, include_old_target: bool = True) -> V5Output:
    claims = [
        V5Claim(
            claim_id="legacy-nontarget-career", school="ziping", domain="事业",
            claim="合成非目标事业事件。", claim_type="event_claim",
            confidence=V5Confidence(score=.6),
            evidence=[V5Evidence("legacy-evidence", "synthetic", "合成非目标证据")],
            falsifiable="未发生则证伪。", metadata={"task_id": "career.role_change"},
        )
    ]
    if include_old_target:
        claims.append(V5Claim(
            claim_id="legacy-yang-marriage-target", school="yang_qingjuan", domain="婚姻",
            claim="旧目标旁路。", claim_type="event_claim",
            confidence=V5Confidence(score=.6),
            evidence=[V5Evidence("old-target-evidence", "synthetic", "旧目标合成证据")],
            falsifiable="未发生则证伪。",
            metadata={"task_id": "marriage.divorce_or_remarriage"},
        ))
    return V5Output(case_id=case_id, chart={}, claims=claims)
```

Use the actual required defaults from `V5Output` if its constructor requires additional fields; construct only existing model types and no fake module.

```python
from engine.decision.yang_marriage_slice import build_yang_marriage_slice_decision_run


def target_counts(run) -> tuple[int, int, int, int, int]:
    claim_ids = {c.claim_id for c in run.school_claims if c.metadata.get("task_id") == "marriage.divorce_or_remarriage"}
    verdict_ids = {v.verdict_id for v in run.structural_verdicts if v.claim_id in claim_ids}
    event_ids = {e.event_id for e in run.event_hypotheses if set(e.source_verdict_ids) & verdict_ids}
    return (
        len(claim_ids), len(verdict_ids), len(event_ids),
        sum(t.event_id in event_ids for t in run.timing_probabilities),
        sum(bool(set(d.competing_event_ids) & event_ids) for d in run.arbitration_decisions),
    )


@pytest.mark.parametrize("case_id", ["YM-SYN-M1", "YM-SYN-F1", "YM-SYN-F2"])
def test_event_has_exact_complete_l2_l6_trace(case_id: str) -> None:
    sample = next(item for item in synthetic_cases() if item.case_id == case_id)
    result, run = build_yang_marriage_slice_decision_run(
        slice_output(case_id), sample.chart, sample.features
    )
    assert result.state == "event"
    assert target_counts(run) == (1, 1, 1, 1, 1)
    assert run.validate_trace() == []
    assert run.report_items == []
    assert run.feedback_signals == [] and run.calibration_actions == []


@pytest.mark.parametrize("sample", [x for x in synthetic_cases() if x.expected_state != "event"], ids=lambda x: x.case_id)
def test_pressure_and_abstain_have_zero_target_objects_in_every_layer(sample) -> None:
    result, run = build_yang_marriage_slice_decision_run(
        slice_output(sample.case_id), sample.chart, sample.features
    )
    assert result.state in {"pressure", "abstain"}
    assert target_counts(run) == (0, 0, 0, 0, 0)
    assert all(c.claim_id != "legacy-yang-marriage-target" for c in run.school_claims)
```

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/yang_marriage/test_slice_layers.py -q`

Expected: FAIL because `build_yang_marriage_slice_decision_run` does not exist and/or fixture construction lacks exact `V5Output` defaults.

- [ ] **Step 3: Build the existing DecisionRun without L7-L9**

```python
def build_yang_marriage_slice_decision_run(
    output: V5Output,
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    raw_text: str = "",
) -> tuple[YangMarriageDiscrimination, DecisionRun]:
    raw = raw_text or f"{output.schema_version}|{output.case_id}|yang-marriage-synthetic-slice"
    raw_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    bound_chart = replace(chart, raw_source_hash=raw_hash)
    payload = RawWenzhenPayload(
        raw_text=raw, raw_hash=raw_hash,
        parser_version="decision-yang-marriage-slice-v1",
    )
    context = ContextFactLedger(preserved_text_blocks=["yang_marriage_discrimination_slice"])
    applicability = route_schools(bound_chart, context)
    result, claims, verdicts, events, timings, decisions = apply_yang_marriage_slice(
        output, bound_chart, features, applicability
    )
    run = DecisionRun(
        run_id=_stable_id("drun", output.case_id or features.chart_id, raw_hash),
        case_id=output.case_id or features.chart_id,
        raw_payload=payload,
        chart_ledger=bound_chart,
        context_ledger=context,
        school_applicability=applicability,
        school_claims=claims,
        structural_verdicts=verdicts,
        event_hypotheses=events,
        timing_probabilities=timings,
        arbitration_decisions=decisions,
        report_items=[], feedback_signals=[], feedback_attributions=[], calibration_actions=[],
    )
    return result, run
```

This reuses the existing `DecisionRun`; do not add `YangMarriageRun`, `SliceRun`, a persisted audit projection or a second orchestrator model.

Add tests that:

1. run D4 twice and with pair order reversed, then compare `result.to_dict()` and target L2-L6 `to_dict()` JSON with `sort_keys=True`;
2. compare a run with and without old target and prove the old target never survives;
3. compare the non-target claim/verdict/event/timing/decision dicts from direct legacy builders against the slice result, excluding only objects transitively sourced from the stripped target;
4. inject a duplicate non-target claim ID and assert fail-fast before L3;
5. assert pressure statement text is absent from all public layers because no pressure claim exists.

- [ ] **Step 4: Run GREEN for all semantic gates**

Run: `python -m pytest tests/yang_marriage/test_slice_layers.py tests/yang_marriage/test_synthetic_matrix.py -q`

Expected: PASS; M1/F1/F2 each show `(1, 1, 1, 1, 1)`, every non-event fixture shows `(0, 0, 0, 0, 0)`, `validate_trace()` is empty, non-target dicts are equal, and serialization is deterministic.

- [ ] **Step 5: Review isolated diff and commit**

```bat
git status --short && git diff --check && git add engine/decision/yang_marriage_slice.py tests/yang_marriage/fixtures.py tests/yang_marriage/test_slice_layers.py && git diff --cached --name-only && git commit -m "test: prove yang marriage l2 l6 semantic isolation"
```

Expected: only the three task files are committed.

## Phase 4: Isolation and non-target regression locks

### Task 7: Static isolation, public contract, and production byte locks

**Files:**
- Create: `tests/yang_marriage/test_static_isolation.py`
- Modify: `tests/test_production_entrypoints_unchanged.py`

**Interfaces:**
- Consumes: source AST/text, `dataclasses.fields`, and production YAML bytes read from the isolated branch merge-base through `git show`.
- Produces: mechanical guards for forbidden imports/paths, forbidden count condition, unchanged public field sets, unchanged production YAML bytes, unchanged default registry/pipeline, and no L7/report branch.

- [ ] **Step 1: Write failing static and byte guards**

```python
import ast
import hashlib
import inspect
import subprocess
from dataclasses import fields
from pathlib import Path

from engine.claims.domain import Claim
from engine.decision.models import ReportViewItem, SchoolClaim
from engine.evaluation.models import BlindSchoolOutput
import engine.decision.yang_marriage as discriminator
import engine.decision.yang_marriage_slice as slice_module

PUBLIC_FIELDS = {
    Claim: ("claim_id", "school_id", "task_id", "claim_type", "stance", "statement", "evidence", "falsifier", "time_window", "confidence_basis", "applicability_snapshot", "domain", "polarity", "magnitude", "confidence", "high_risk", "target_id"),
    SchoolClaim: ("claim_id", "school", "role_granted_by_l1", "domain", "claim_type", "statement", "evidence_refs", "confidence", "falsifier", "dependencies", "metadata"),
    BlindSchoolOutput: ("case_id", "school_id", "task_id", "state", "rationale", "predictions", "counter_evidence"),
}


def test_public_contract_fields_and_production_rule_bytes_are_unchanged() -> None:
    for model, expected in PUBLIC_FIELDS.items():
        assert tuple(item.name for item in fields(model)) == expected
    path = "theory/production/claim-rules-v1.yaml"
    baseline_ref = subprocess.check_output(
        ["git", "merge-base", "HEAD", "main"], text=True
    ).strip()
    baseline = subprocess.check_output(["git", "show", f"{baseline_ref}:{path}"])
    current = Path(path).read_bytes()
    assert hashlib.sha256(current).digest() == hashlib.sha256(baseline).digest()
    assert current == baseline


def test_slice_has_no_history_report_learning_or_count_threshold_dependency() -> None:
    paths = [Path(discriminator.__file__), Path(slice_module.__file__)]
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    forbidden = ("cases/", "reports/", "feedback", "frozen", "r6_ziping_career_baseline",
                 "render_report", "ReportViewItem", "independent_signal_count")
    assert not {token for token in forbidden if token in text}
    assert ">= 2" not in inspect.getsource(discriminator.discriminate_yang_marriage)


def test_slice_imports_do_not_reach_l7_l9_or_production_runner() -> None:
    imported = set()
    for path in (Path(discriminator.__file__), Path(slice_module.__file__)):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported |= {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    forbidden_prefixes = ("engine.decision.l7", "engine.decision.l8", "engine.decision.l9",
                          "engine.application", "engine.v5.yang_runner", "tools")
    assert not {name for name in imported if name.startswith(forbidden_prefixes)}
```

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/yang_marriage/test_static_isolation.py tests/test_production_entrypoints_unchanged.py -q`

Expected: FAIL because the new static isolation module and merge-base byte comparison have not yet been added; existing pipeline and registry guards still pass.

- [ ] **Step 3: Complete merge-base byte comparison and source-scope guards**

Keep the exact byte comparison shown in Step 1: it reads the isolated branch merge-base version through `git show` and compares both full bytes and SHA-256 digest to the worktree file. This avoids embedding a drifting digest while still failing on any byte change.

In `test_static_isolation.py`, scan only `tests/yang_marriage/fixtures.py`, `test_synthetic_matrix.py`, and `test_slice_layers.py` for forbidden path tokens `cases/`, `reports/`, `feedback.md`, `META/prospective-go`, `r6_ziping_career_baseline`; scan `engine/application/pipeline_runner.py`, `engine/claims/runner_registry.py`, `engine/decision/l7_report_view.py`, `tools/render_report.py`, and `templates/` references to assert none import `yang_marriage_slice`. Use `Path.rglob("*")` only for text files and decode with UTF-8.

- [ ] **Step 4: Run GREEN and default-boundary regression**

Run: `python -m pytest tests/yang_marriage/test_static_isolation.py tests/test_production_entrypoints_unchanged.py -q`

Expected: PASS; YAML digest, public fields, pipeline signature, default registry digest, report/L7 exclusion and synthetic-only dependency guards all hold.

- [ ] **Step 5: Review isolated diff and commit**

```bat
git status --short && git diff --check && git diff -- theory/production/claim-rules-v1.yaml && git add tests/yang_marriage/test_static_isolation.py tests/test_production_entrypoints_unchanged.py && git diff --cached --name-only && git commit -m "test: lock yang marriage slice production isolation"
```

Expected: `git diff -- theory/production/claim-rules-v1.yaml` prints nothing; only two test files are staged and committed.

### Task 8: Necessary project-state fact, final supported-environment verification, and no-commit handoff

**Files:**
- Modify: `META/project-state.json`
- Modify: `tests/test_project_metadata.py`
- Verify only, do not modify: `theory/production/claim-rules-v1.yaml`
- Verify only, do not modify: `engine/application/pipeline_runner.py`
- Verify only, do not modify: `engine/claims/runner_registry.py`
- Verify only, do not modify: `engine/decision/models.py`
- Verify only, do not modify: `engine/claims/domain.py`
- Verify only, do not modify: `engine/evaluation/models.py`

**Interfaces:**
- Consumes: all task-level tests and current machine state.
- Produces: `META/project-state.json["intelligence_platform_status"]["yang_marriage_discrimination_slice"] = "synthetic_spec_passed_dedicated_only"`; a metadata test rejecting broader status claims; final verification evidence.
- Does not produce: accuracy metric, GO decision, production switch, report status, coverage matrix change, feedback/learning state or commit of the plan file.

- [ ] **Step 1: Write the failing conservative-state test**

```python
import json
from pathlib import Path


def test_yang_marriage_slice_status_is_dedicated_synthetic_only() -> None:
    state = json.loads(Path("META/project-state.json").read_text(encoding="utf-8"))
    value = state["intelligence_platform_status"]["yang_marriage_discrimination_slice"]
    assert value == "synthetic_spec_passed_dedicated_only"
    forbidden = ("accuracy", "go", "production", "default", "promoted")
    assert not any(token in value.lower() for token in forbidden)
```

- [ ] **Step 2: Run RED**

Run: `python -m pytest tests/test_project_metadata.py::test_yang_marriage_slice_status_is_dedicated_synthetic_only -q`

Expected: FAIL with `KeyError: 'yang_marriage_discrimination_slice'`.

- [ ] **Step 3: Update only the necessary machine fact**

Add exactly one key under the existing `intelligence_platform_status` object in `META/project-state.json`:

```json
"yang_marriage_discrimination_slice": "synthetic_spec_passed_dedicated_only"
```

Keep `last_updated` at `2026-07-17`; do not edit `README.md`, `STATUS.md`, `handoff.md`, `tools/README.md`, contracts, templates, reports or historical changelog because the default/production/report state has not changed.

- [ ] **Step 4: Run task GREEN and commit only the machine fact**

Run: `python -m pytest tests/test_project_metadata.py -q`

Expected: PASS with the new conservative status and all existing metadata invariants.

```bat
git status --short && git diff --check && git add META/project-state.json tests/test_project_metadata.py && git diff --cached --name-only && git commit -m "docs: record dedicated yang marriage slice proof"
```

Expected: only the two listed files are committed; the plan remains untracked/unstaged in the implementation worktree if copied there.

- [ ] **Step 5: Run the dedicated Python 3.14-compatible gate**

Run: `python -m pytest tests/yang_marriage tests/test_production_entrypoints_unchanged.py tests/test_project_metadata.py -q`

Expected: PASS without importing `sxtwl`; all synthetic, L2-L6, static isolation and status tests pass.

- [ ] **Step 6: Run the full suite in the supported environment**

Run: `.venv312\Scripts\python -m pytest tests -q`

Expected: PASS in the Python environment where `.venv312\Scripts\python -c "import sxtwl"` previously succeeded. If Python 3.12 or real `sxtwl` is unavailable, record full-suite verification as BLOCKED by environment and do not substitute a fake module or claim full completion.

- [ ] **Step 7: Verify exact scope, forbidden changes, and clean staged state**

```bat
git diff --check HEAD && git status --short && git diff --name-only HEAD && git diff -- theory/production/claim-rules-v1.yaml engine/application/pipeline_runner.py engine/claims/runner_registry.py engine/decision/models.py engine/claims/domain.py engine/evaluation/models.py && git log --oneline --decorate -8
```

Expected: forbidden-file diff is empty; changed files from the branch are limited to the File Responsibility Map; no staged files remain; commits are one per Task and contain no dirty-worktree cleanup.

- [ ] **Step 8: Verify no unresolved markers, type/name consistency, and Markdown links**

Run: `python -c "from pathlib import Path; p=Path('docs/superpowers/plans/2026-07-17-yang-marriage-discrimination-slice.md'); t=p.read_text(encoding='utf-8'); banned=('T'+'BD','TO'+'DO','implement '+'later','fill in '+'details','Similar to '+'Task','类似 '+'Task'); hits=[x for x in banned if x in t]; assert not hits, hits; print('unresolved-marker scan: PASS')"`

Expected: `unresolved-marker scan: PASS`; no committed implementation file may contain unresolved implementation markers.

Run: `python -m compileall -q engine/decision/yang_marriage.py engine/decision/yang_marriage_slice.py tests/yang_marriage && python -c "from engine.decision.yang_marriage import discriminate_yang_marriage, reduce_yang_marriage_families, extract_yang_marriage_signals, YangMarriageDiscrimination; from engine.decision.yang_marriage_slice import apply_yang_marriage_slice, build_yang_marriage_slice_decision_run, to_yang_marriage_school_claim; print('type/name import consistency: PASS')"`

Expected: `type/name import consistency: PASS`.

Run: `python -c "import re; from pathlib import Path; p=Path('docs/superpowers/plans/2026-07-17-yang-marriage-discrimination-slice.md').resolve(); t=p.read_text(encoding='utf-8'); links=re.findall(r'\[[^\]]+\]\(([^)]+)\)', t); bad=[]; [bad.append(x) for x in links if not x.startswith(('http://','https://','#')) and not (p.parent / x.split('#',1)[0]).resolve().exists()]; assert not bad, bad; print(f'markdown relative links: PASS ({len(links)})')"`

Expected: `markdown relative links: PASS (3)`; links point to the approved spec and the two existing files modified by the plan. Files to be created remain exact code-span paths until implementation creates them, avoiding knowingly broken links.

- [ ] **Step 9: Do not create another commit**

Do not commit after final verification. Preserve command output for review and report only:

- plan path;
- eight implementation tasks;
- dedicated-gate result;
- supported full-suite result or explicit environment BLOCKED;
- production YAML/default/public-schema zero-diff result;
- wording exactly limited to synthetic specification compliance.

## Self-Review Checklist

### Spec coverage

- [ ] 三态、优先级、blocker、不可变 DTO：Task 1 and Task 3.
- [ ] 性别/partial/no-hour/非法日柱/非法 pair 保守 abstain：Task 2 and Task 4.
- [ ] 六个固定家族、canonical pair、同源与别名去重：Task 2-4.
- [ ] 具名门 A + 门 B，禁止总信号数替代：Task 3, Task 4, Task 7.
- [ ] M1/F1/F2、S1/S2、P1-P3、G1-G3、I1-I3、D1-D4、R1：Task 4.
- [ ] 首个证伪点“无锚双非宫位信号”：Task 3 and Task 4.
- [ ] event-only SchoolClaim、pressure/abstain fail-closed：Task 5.
- [ ] R10 式目标剥离、非目标旧桥、合并去重、直接 L3-L6：Task 5 and Task 6.
- [ ] 不新增第三套 run 模型、沿用 DecisionRun、L7-L9 为空：Task 6.
- [ ] event 每层一个、完整 trace；非 event 每层零：Task 6.
- [ ] 决定性、重复 claim fail-fast、非目标逐字段零回归：Task 5 and Task 6.
- [ ] 合成夹具唯一门禁、历史/反馈/frozen 路径静态隔离：Task 4 and Task 7.
- [ ] production YAML 字节不变、公共 schema/默认 registry/pipeline/L7/report 不变：Task 7.
- [ ] 概率不重算，adapter 沿用现有 `0.60`，DTO 无概率：Task 1 and Task 5.
- [ ] Python 3.14 缺 `sxtwl` 时纯函数可测，受支持环境全量验证且禁止 fake module：Execution Precondition and Task 8.
- [ ] 脏工作树隔离 worktree、逐任务独立提交、不混提交：Execution Precondition and every Task commit step.
- [ ] 必要事实源只更新 `META/project-state.json`，不宣称准确率/GO/生产资格：Task 8.

### Unresolved-marker scan

- [ ] 运行 Task 8 的机械扫描并确认没有未决实施标记或角括号替换标记。
- [ ] Task 7 必须通过 merge-base 原始字节与 SHA-256 双比较，不使用漂移的手写摘要。

### Type consistency

- [ ] `YangMarriageState`, `SexBasis`, `FamilyKey`, `CanonicalPair` names are identical across Tasks 1-8.
- [ ] `extract_yang_marriage_signals()` returns `YangMarriageRawSignals`; `reduce_yang_marriage_families()` consumes it; `discriminate_yang_marriage()` returns `YangMarriageDiscrimination`.
- [ ] `to_yang_marriage_school_claim()` accepts only `YangMarriageDiscrimination` plus `SchoolRole` and returns existing `SchoolClaim`.
- [ ] `apply_yang_marriage_slice()` six layer-list return types match `build_yang_marriage_slice_decision_run()` consumption.
- [ ] `build_yang_marriage_slice_decision_run()` returns `tuple[YangMarriageDiscrimination, DecisionRun]`; no alternate run type appears.
- [ ] School identifier is consistently `yang_qingjuan` at V5/Decision layers; task identifier is consistently `marriage.divorce_or_remarriage`; domain is consistently `婚姻`.

## Permitted completion statement

`杨派婚姻判别切片在合成矩阵上满足三态、去重、必要门与层级隔离规格。production YAML、公共 schema、默认入口、L7、模板、报告、概率、覆盖矩阵及 feedback/学习链保持不变。`
