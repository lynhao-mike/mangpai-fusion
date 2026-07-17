# 子平职业路径“官杀路径受扰资格门”实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立一个仅供 staged 验证的子平 `career.role_change` L2→L3 纵切，使 production 粗 trigger 在官杀—食伤结构必要门不成立时无法进入 L3 pass。

**Architecture:** 使用独立、严格的子平职业规则映射 YAML，将 `ZP-PROD-20260622-011/012` 稳定映射到 `ZIPING-CAREER-OFFICIAL-PATH-DISRUPTION-V1`；纯判别器只消费 `ChartFactLedger`、`ChartFeatureVector` 与显式格局 profile，生成局部结构态和统一发布态；专用 staged assembler 仅把 `supported/emit` 转成一个无时间窗 L2 `SchoolClaim` 和一个 L3 `StructuralVerdict(pass)`，随后生成确定性冻结制品并停止。

**Tech Stack:** Python 3、不可变 `dataclass`、`Enum`、PyYAML、pytest、现有 `ChartFactLedger` / `ChartFeatureVector` / `SchoolClaim` / `StructuralVerdict` / `canonical_json()` / `compute_freeze_hash()`。

## Global Constraints

- 单任务固定为 `career.role_change`，单结论固定为“官杀职业路径受扰结构是否具备发布资格”。
- target layer 固定为 staged L3；禁止构造 `EventHypothesis` 或 `TimingProbability`。
- 禁止读取大运、流年、任派/杨派输出、feedback、labels、reports、known facts 和默认时间窗。
- 默认 runner registry、正式 pipeline、`theory/production/claim-rules-v1.yaml`、公共 schema、报告入口保持字节或签名不变。
- 既有任派与杨派专属实现、测试和规则路径零改动。
- 所有实现任务遵循 RED→最小 GREEN→focused tests→独立提交→复核。
- 同一十神事实的派生布尔、摘要和强度只计一个证据家族；地支冲突不能替代官杀锚点或食伤干扰门。
- 只有 `supported → emit` 可进入 L2/L3 adapter；`weakened/contradicted → hold`，输入不足为 `abstain`，未知任务为 `unsupported`。
- G0-G5 通过后只登记 `staged_verified_production_unchanged`，不得宣称准确率提升或生产晋级。
- 开始每项任务前执行 `git status --short --branch` 与 `git rev-list --left-right --count HEAD...origin/main`；出现非本计划改动时停止，不覆盖并行 agent。

---

## 文件结构锁定

| 路径 | 操作 | 单一职责 |
|---|---|---|
| `theory/production/ziping-career-structure-rules-v1.yaml` | 新建 | production IDs 到 task rule ID 的严格映射、门、反条件、来源和文案 |
| `engine/decision/ziping_career_rules.py` | 新建 | 只读加载、严格校验、不可变映射与 digest |
| `engine/decision/ziping_career_structure.py` | 新建 | 事实提取、家族归并、具名门、局部态与发布态判别 |
| `engine/decision/ziping_career_structure_slice.py` | 新建 | emit-only L2 adapter、专用 L3 adapter、staged assembler 与冻结制品 |
| `tests/ziping_career/conftest.py` | 新建 | 完整/首证伪/反条件/不完整命盘与 CFV fixtures |
| `tests/ziping_career/test_rule_mapping.py` | 新建 | G0 严格映射和身份稳定性 |
| `tests/ziping_career/test_discriminator.py` | 新建 | G1 positive/negative/exclusion/boundary/state tests |
| `tests/ziping_career/test_staged_slice.py` | 新建 | G2-G4 adapter、L3、冻结、截断与首证伪测试 |
| `tests/ziping_career/test_production_isolation.py` | 新建 | G5 默认入口、production artifact、任派/杨派路径隔离 |
| `theory/executable-slices-v1.yaml` | 最终集成时修改 | G0-G5 通过后登记一个 staged_verified 子平切片 |
| `META/project-state.json` | 最终集成时修改 | 登记 `staged_verified_production_unchanged`，不改生产开关 |
| `tests/test_project_metadata.py` | 最终集成时修改 | 冻结机器状态登记值 |
| `tests/tools/test_theory_slice_status.py` | 最终集成时修改 | 冻结子平 catalog / executable 分账结果 |
| `reports/ziping-career-structure-slice-g0-g5-verification.md` | 最终集成时新建 | 记录门禁证据、测试命令与生产隔离结论 |

---

### Task 1: 严格规则映射与 production 来源身份

**Files:**
- Create: `theory/production/ziping-career-structure-rules-v1.yaml`
- Create: `engine/decision/ziping_career_rules.py`
- Create: `tests/ziping_career/__init__.py`
- Create: `tests/ziping_career/test_rule_mapping.py`

**Interfaces:**
- Consumes: `theory/ziping/index.yaml` 中 `ZP-PROD-20260622-011` 与 `ZP-PROD-20260622-012`。
- Produces: `ZipingCareerRuleMapping`、`SourceAnchor`、`RuleCondition`、`load_ziping_career_rule_mapping(path=DEFAULT_RULE_PATH) -> ZipingCareerRuleMapping`、`mapping_digest(mapping) -> str`。

- [ ] **Step 1: 重新核验 Git 与并行写区**

Run:

```bat
git fetch --prune origin && git status --short --branch && git rev-list --left-right --count HEAD...origin/main && git diff --name-only -- engine/decision/yang_marriage.py engine/decision/yang_marriage_claims.py tests/yang_marriage engine/decision/ren_career_timing.py engine/decision/ren_career_timing_slice.py engine/decision/ren_timing_rules.py tests/ren_timing
```

Expected: 只有已批准规格提交造成的 ahead；工作区无输出；杨派/任派路径无 diff。若不满足，停止任务并审计差异。

- [ ] **Step 2: 写严格映射 RED 测试**

创建 `tests/ziping_career/__init__.py` 为空文件。创建 `tests/ziping_career/test_rule_mapping.py`，至少包含以下完整测试骨架：

```python
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
import yaml

from engine.decision.ziping_career_rules import (
    DEFAULT_RULE_PATH,
    MappingSchemaError,
    load_ziping_career_rule_mapping,
    mapping_digest,
)


def test_mapping_binds_exact_production_ids_to_one_task_rule() -> None:
    mapping = load_ziping_career_rule_mapping()
    assert mapping.schema_version == "ziping-career-structure-rules/v1"
    assert mapping.school_id == "ziping"
    assert mapping.task_id == "career.role_change"
    assert mapping.domain == "事业"
    assert mapping.target_layer == "L3"
    assert mapping.task_rule_id == "ZIPING-CAREER-OFFICIAL-PATH-DISRUPTION-V1"
    assert tuple(item.production_rule_id for item in mapping.source_anchors) == (
        "ZP-PROD-20260622-011",
        "ZP-PROD-20260622-012",
    )
    assert mapping.required_gates == (
        "complete_fact_closure",
        "official_path_anchor",
        "output_interference_present",
        "structure_qualification",
    )


def test_source_anchors_resolve_to_exact_production_entries() -> None:
    document = yaml.safe_load(Path("theory/ziping/index.yaml").read_text(encoding="utf-8"))
    indexed = {item["id"]: item for item in document["rules"]}
    mapping = load_ziping_career_rule_mapping()
    for anchor in mapping.source_anchors:
        source = indexed[anchor.production_rule_id]
        assert source["source"]["path"] == anchor.path
        assert int(source["source"]["line"]) == anchor.line
        assert anchor.excerpt in source["source"]["excerpt"]


def test_mapping_is_immutable_and_digest_is_order_stable(tmp_path: Path) -> None:
    original = load_ziping_career_rule_mapping()
    raw = yaml.safe_load(DEFAULT_RULE_PATH.read_text(encoding="utf-8"))
    raw["source_anchors"] = list(reversed(raw["source_anchors"]))
    path = tmp_path / "mapping.yaml"
    path.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")
    reordered = load_ziping_career_rule_mapping(path)
    assert mapping_digest(original) == mapping_digest(reordered)
    with pytest.raises(FrozenInstanceError):
        original.task_rule_id = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda doc: doc.update(extra=True), "unknown top-level"),
        (lambda doc: doc.update(schema_version="wrong"), "schema_version"),
        (lambda doc: doc.update(task_id="career.change_window"), "task_id"),
        (lambda doc: doc["source_anchors"].clear(), "source_anchors"),
        (lambda doc: doc["conditions"][0].update(op="python_eval"), "operator"),
    ],
)
def test_invalid_mapping_fails_closed(tmp_path: Path, mutation, message: str) -> None:
    raw = yaml.safe_load(DEFAULT_RULE_PATH.read_text(encoding="utf-8"))
    mutation(raw)
    path = tmp_path / "invalid.yaml"
    path.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=False), encoding="utf-8")
    with pytest.raises(MappingSchemaError, match=message):
        load_ziping_career_rule_mapping(path)
```

- [ ] **Step 3: 运行 RED 测试**

Run:

```bat
pytest tests/ziping_career/test_rule_mapping.py -q
```

Expected: collection ERROR，明确指出 `engine.decision.ziping_career_rules` 不存在。

- [ ] **Step 4: 新建映射 YAML**

创建 `theory/production/ziping-career-structure-rules-v1.yaml`，内容固定为：

```yaml
schema_version: ziping-career-structure-rules/v1
school_id: ziping
task_id: career.role_change
domain: 事业
target_layer: L3
task_rule_id: ZIPING-CAREER-OFFICIAL-PATH-DISRUPTION-V1
claim_type: structure_claim
required_facts:
  - evidence_completeness
  - ten_god_counts.正官
  - ten_god_counts.七杀
  - ten_god_counts.食神
  - ten_god_counts.伤官
  - ten_god_counts.正财
  - ten_god_counts.偏财
  - ten_god_counts.正印
  - ten_god_counts.偏印
  - mixed_official_kill
  - geju_profile.geju_type
  - geju_profile.favor_shishen
  - geju_profile.avoid_shishen
required_gates:
  - complete_fact_closure
  - official_path_anchor
  - output_interference_present
  - structure_qualification
conditions:
  - {fact: official_count, op: gte, value: 1}
  - {fact: output_count, op: gte, value: 1}
exclusions:
  - {fact: evidence_completeness, op: ne, value: full}
counter_conditions:
  - {fact: wealth_count, op: gte, value: 1}
  - {fact: resource_count, op: gte, value: 1}
conclusion_template: 子平原局官杀职业路径存在食伤介入，且结构必要门成立，支持职业角色或职责路径具有变化倾向；本结论不判断事件必然发生与具体年份。
confidence_basis: 官杀路径锚点、食伤介入与格局方向共同成立；财印护官与格局反向证据会阻止发布。
falsifier: 若按同一事实口径复核不存在官杀锚点或食伤介入，或可核验职业历程长期无角色与职责变化，则本结构命题证伪或降权。
source_anchors:
  - production_rule_id: ZP-PROD-20260622-011
    path: sources/ziping/《子平真诠》.md
    line: 60
    excerpt: 官格见财印相生为纯，混杂伤官七杀则杂。
    supports: 支持区分官格的财印保护结构与伤官、七杀混杂结构。
  - production_rule_id: ZP-PROD-20260622-012
    path: sources/ziping/《子平真诠》.md
    line: 64
    excerpt: 同是官格，财生官、印护官为上格，伤官破官、七杀混官为下格。
    supports: 支持把财印护官作为反条件，并把伤官破官作为结构干扰。
lifecycle_state: staged
base_confidence: 0.60
```

- [ ] **Step 5: 实现最小严格 loader**

创建 `engine/decision/ziping_career_rules.py`。实现必须包含：

```python
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from engine.evaluation.freeze import canonical_json

SCHEMA_VERSION = "ziping-career-structure-rules/v1"
TASK_RULE_ID = "ZIPING-CAREER-OFFICIAL-PATH-DISRUPTION-V1"
DEFAULT_RULE_PATH = Path(__file__).resolve().parents[2] / "theory" / "production" / "ziping-career-structure-rules-v1.yaml"
_ALLOWED_OPERATORS = {"eq", "ne", "gte", "lte", "in", "not_in", "truthy", "falsy"}
_EXPECTED_SOURCE_IDS = ("ZP-PROD-20260622-011", "ZP-PROD-20260622-012")

class MappingSchemaError(ValueError):
    pass

@dataclass(frozen=True)
class RuleCondition:
    fact: str
    op: str
    value: object

@dataclass(frozen=True)
class SourceAnchor:
    production_rule_id: str
    path: str
    line: int
    excerpt: str
    supports: str

@dataclass(frozen=True)
class ZipingCareerRuleMapping:
    schema_version: str
    school_id: str
    task_id: str
    domain: str
    target_layer: str
    task_rule_id: str
    claim_type: str
    required_facts: tuple[str, ...]
    required_gates: tuple[str, ...]
    conditions: tuple[RuleCondition, ...]
    exclusions: tuple[RuleCondition, ...]
    counter_conditions: tuple[RuleCondition, ...]
    conclusion_template: str
    confidence_basis: str
    falsifier: str
    source_anchors: tuple[SourceAnchor, ...]
    lifecycle_state: str
    base_confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "school_id": self.school_id,
            "task_id": self.task_id,
            "domain": self.domain,
            "target_layer": self.target_layer,
            "task_rule_id": self.task_rule_id,
            "claim_type": self.claim_type,
            "required_facts": list(self.required_facts),
            "required_gates": list(self.required_gates),
            "conditions": [item.__dict__ for item in self.conditions],
            "exclusions": [item.__dict__ for item in self.exclusions],
            "counter_conditions": [item.__dict__ for item in self.counter_conditions],
            "conclusion_template": self.conclusion_template,
            "confidence_basis": self.confidence_basis,
            "falsifier": self.falsifier,
            "source_anchors": [item.__dict__ for item in self.source_anchors],
            "lifecycle_state": self.lifecycle_state,
            "base_confidence": self.base_confidence,
        }

def mapping_digest(mapping: ZipingCareerRuleMapping) -> str:
    data = mapping.to_dict()
    data["source_anchors"] = sorted(data["source_anchors"], key=lambda item: item["production_rule_id"])
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()
```

`load_ziping_career_rule_mapping()` 须进一步严格检查：顶层字段集合完全相等；固定 schema/school/task/domain/layer/task rule/claim type/lifecycle；条件 operator 白名单；两个 source ID 集合完全相等；source 文件存在且 excerpt 可在对应 production entry 中解析；`base_confidence` 在 0..1；最终按 production rule ID 排序构造 tuple。

- [ ] **Step 6: 运行 GREEN 测试并复核 diff**

Run:

```bat
pytest tests/ziping_career/test_rule_mapping.py -q && git diff --check && git diff --stat
```

Expected: 全部 PASS；仅 Task 1 四个新文件发生变化。

- [ ] **Step 7: 独立提交 Task 1**

```bat
git add theory/production/ziping-career-structure-rules-v1.yaml engine/decision/ziping_career_rules.py tests/ziping_career/__init__.py tests/ziping_career/test_rule_mapping.py && git commit -m "feat: map ziping career structure rule identities"
```

- [ ] **Step 8: 提交后复核**

Run:

```bat
git show --stat --oneline HEAD && git status --short
```

Expected: 提交只含 Task 1 文件；工作区干净。

---

### Task 2: 事实家族与局部四态纯判别器

**Files:**
- Create: `engine/decision/ziping_career_structure.py`
- Create: `tests/ziping_career/conftest.py`
- Create: `tests/ziping_career/test_discriminator.py`

**Interfaces:**
- Consumes: `ZipingCareerRuleMapping`、`ChartFactLedger`、`ChartFeatureVector`、`geju_profile: Mapping[str, object]`。
- Produces: `LocalStructureState`、`PublicationState`、`CareerStructureFacts`、`CareerEvidenceFamily`、`ZipingCareerDiscrimination`、`discriminate_ziping_career_structure(chart, features, geju_profile, *, task_id="career.role_change", mapping=None) -> ZipingCareerDiscrimination`。

- [ ] **Step 1: 写 fixtures 与 RED 状态测试**

`tests/ziping_career/conftest.py` 使用一个完整 `ChartFactLedger`，再用 `dataclasses.replace(build_chart_feature_vector(chart), ...)` 精确构造以下 fixtures：

```python
@pytest.fixture
def supported_features(base_features):
    return replace(
        base_features,
        ten_god_counts={"正官": 1, "七杀": 0, "食神": 0, "伤官": 1, "正财": 0, "偏财": 0, "正印": 0, "偏印": 0},
        has_official=True,
        has_output=True,
        has_wealth=False,
        has_resource=False,
        mixed_official_kill=False,
        evidence_completeness="full",
    )

@pytest.fixture
def coarse_trigger_without_output_features(supported_features):
    return replace(
        supported_features,
        ten_god_counts={"正官": 1, "七杀": 0, "食神": 0, "伤官": 0, "正财": 0, "偏财": 0, "正印": 0, "偏印": 0},
        has_output=False,
    )

@pytest.fixture
def protected_features(supported_features):
    return replace(
        supported_features,
        ten_god_counts={"正官": 1, "七杀": 0, "食神": 0, "伤官": 1, "正财": 1, "偏财": 0, "正印": 1, "偏印": 0},
        has_wealth=True,
        has_resource=True,
    )
```

`tests/ziping_career/test_discriminator.py` 至少包含：

```python
from dataclasses import FrozenInstanceError, replace

import pytest

from engine.decision.ziping_career_structure import (
    LocalStructureState,
    PublicationState,
    discriminate_ziping_career_structure,
)


def test_supported_requires_named_official_output_and_structure_gates(chart, supported_features) -> None:
    result = discriminate_ziping_career_structure(
        chart, supported_features, {"geju_type": "正格", "favor_shishen": [], "avoid_shishen": []}
    )
    assert result.local_state is LocalStructureState.SUPPORTED
    assert result.publication_state is PublicationState.EMIT
    assert result.gates == {
        "complete_fact_closure": True,
        "official_path_anchor": True,
        "output_interference_present": True,
        "structure_qualification": True,
    }
    assert {item.family_key for item in result.families if item.matched} >= {
        "official_path_anchor", "output_interference", "geju_direction"
    }


def test_first_falsifier_coarse_official_trigger_without_output_is_hold(
    chart, coarse_trigger_without_output_features
) -> None:
    result = discriminate_ziping_career_structure(
        chart,
        coarse_trigger_without_output_features,
        {"geju_type": "正格", "favor_shishen": [], "avoid_shishen": []},
    )
    assert result.coarse_trigger_observed is True
    assert result.gates["official_path_anchor"] is True
    assert result.gates["output_interference_present"] is False
    assert result.local_state is LocalStructureState.WEAKENED
    assert result.publication_state is PublicationState.HOLD


def test_financial_and_seal_protection_can_contradict_disruption(chart, protected_features) -> None:
    result = discriminate_ziping_career_structure(
        chart,
        protected_features,
        {"geju_type": "正格", "favor_shishen": ["正官", "正印"], "avoid_shishen": ["伤官"]},
    )
    assert result.local_state is LocalStructureState.CONTRADICTED
    assert result.publication_state is PublicationState.HOLD
    assert "official_path_protection" in result.matched_counter_families


def test_branch_conflict_cannot_replace_official_or_output_gates(chart, supported_features) -> None:
    features = replace(
        supported_features,
        ten_god_counts={key: 0 for key in supported_features.ten_god_counts},
        has_official=False,
        has_output=False,
        branch_conflict_intensity=1.0,
    )
    result = discriminate_ziping_career_structure(
        chart, features, {"geju_type": "正格", "favor_shishen": [], "avoid_shishen": []}
    )
    assert result.publication_state is not PublicationState.EMIT
    assert result.gates["official_path_anchor"] is False
    assert result.gates["output_interference_present"] is False


def test_partial_input_abstains(chart, supported_features) -> None:
    result = discriminate_ziping_career_structure(
        chart,
        replace(supported_features, evidence_completeness="partial"),
        {"geju_type": "正格", "favor_shishen": [], "avoid_shishen": []},
    )
    assert result.local_state is LocalStructureState.ABSTAIN
    assert result.publication_state is PublicationState.ABSTAIN
    assert "complete_fact_closure" in result.failed_gates


def test_unknown_task_is_unsupported(chart, supported_features) -> None:
    result = discriminate_ziping_career_structure(
        chart,
        supported_features,
        {"geju_type": "正格", "favor_shishen": [], "avoid_shishen": []},
        task_id="career.change_window",
    )
    assert result.publication_state is PublicationState.UNSUPPORTED


def test_discrimination_and_nested_families_are_immutable(chart, supported_features) -> None:
    result = discriminate_ziping_career_structure(
        chart, supported_features, {"geju_type": "正格", "favor_shishen": [], "avoid_shishen": []}
    )
    with pytest.raises(FrozenInstanceError):
        result.local_state = LocalStructureState.ABSTAIN  # type: ignore[misc]
```

- [ ] **Step 2: 运行 RED 测试**

Run:

```bat
pytest tests/ziping_career/test_discriminator.py -q
```

Expected: collection ERROR，指出 `engine.decision.ziping_career_structure` 不存在。

- [ ] **Step 3: 实现不可变领域类型与信号提取**

创建 `engine/decision/ziping_career_structure.py`，固定公开类型：

```python
class LocalStructureState(str, Enum):
    SUPPORTED = "supported"
    WEAKENED = "weakened"
    CONTRADICTED = "contradicted"
    ABSTAIN = "abstain"

class PublicationState(str, Enum):
    EMIT = "emit"
    HOLD = "hold"
    ABSTAIN = "abstain"
    UNSUPPORTED = "unsupported"

@dataclass(frozen=True)
class CareerEvidenceFamily:
    family_key: str
    matched: bool
    fact_refs: tuple[str, ...]
    feature_refs: tuple[str, ...]
    production_rule_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    detail: str

@dataclass(frozen=True)
class ZipingCareerDiscrimination:
    task_id: str
    task_rule_id: str
    mapping_digest: str
    local_state: LocalStructureState
    publication_state: PublicationState
    coarse_trigger_observed: bool
    gates: Mapping[str, bool]
    families: tuple[CareerEvidenceFamily, ...]
    failed_gates: tuple[str, ...]
    matched_counter_families: tuple[str, ...]
    exclusions: tuple[str, ...]
    diagnostic_reasons: tuple[str, ...]
    remediation: str
```

`coarse_trigger_observed` 只能定义为 `official_count > 0` 的诊断哨兵，不能参与 `structure_qualification`；代码注释明确它模拟 production `has_official_picture/always` 类粗入口的“相关触发已存在”事实，而不是必要门替代物。

- [ ] **Step 4: 实现最小状态机**

判别顺序固定为：

```python
if task_id != mapping.task_id:
    return unsupported_result
if features.evidence_completeness != "full" or not geju_profile.get("geju_type"):
    return abstain_result

official_count = count("正官", "七杀")
output_count = count("食神", "伤官")
wealth_count = count("正财", "偏财")
resource_count = count("正印", "偏印")
direct_hurting_official = count("伤官") > 0 and count("正官") > 0
output_official_coexistence = official_count > 0 and output_count > 0

gates = {
    "complete_fact_closure": True,
    "official_path_anchor": official_count > 0,
    "output_interference_present": output_count > 0,
    "structure_qualification": direct_hurting_official or output_official_coexistence,
}

if not gates["official_path_anchor"] or not gates["output_interference_present"]:
    state, publication = WEAKENED, HOLD
elif protective_and_geju_counter_is_explicit:
    state, publication = CONTRADICTED, HOLD
elif all(gates.values()):
    state, publication = SUPPORTED, EMIT
else:
    state, publication = WEAKENED, HOLD
```

`protective_and_geju_counter_is_explicit` 首版固定为：`wealth_count >= 1 and resource_count >= 1 and (favor 含正官/正印 or avoid 含食神/伤官)`；禁止引入权重系统或可调阈值框架。

- [ ] **Step 5: 运行 GREEN 与边界测试**

Run:

```bat
pytest tests/ziping_career/test_discriminator.py tests/ziping_career/test_rule_mapping.py -q
```

Expected: 全部 PASS。

- [ ] **Step 6: 静态隔离复核**

在测试中使用 AST 检查 `engine/decision/ziping_career_structure.py` 不导入包含 `feedback`、`labels`、`reports`、`ren_career_timing`、`l5_timing`、`pipeline` 的模块。运行：

```bat
pytest tests/ziping_career/test_discriminator.py -q && git diff --check
```

Expected: PASS。

- [ ] **Step 7: 独立提交 Task 2**

```bat
git add engine/decision/ziping_career_structure.py tests/ziping_career/conftest.py tests/ziping_career/test_discriminator.py && git commit -m "feat: discriminate ziping career path structure"
```

- [ ] **Step 8: 提交后复核**

```bat
git show --stat --oneline HEAD && git status --short
```

Expected: 只含 Task 2 三个文件；工作区干净。

---

### Task 3: emit-only L2 与专用 L3 adapter

**Files:**
- Create: `engine/decision/ziping_career_structure_slice.py`
- Create: `tests/ziping_career/test_staged_slice.py`

**Interfaces:**
- Consumes: `ZipingCareerDiscrimination`、`SchoolRole`。
- Produces: `to_ziping_career_school_claim(result, role, chart_signature) -> SchoolClaim`、`to_ziping_career_structural_verdict(case_id, result, claim) -> StructuralVerdict`、`build_ziping_career_structure_slice(...) -> ZipingCareerSliceRun`。

- [ ] **Step 1: 写 emit-only 和首证伪 RED 测试**

`tests/ziping_career/test_staged_slice.py` 先加入：

```python
from dataclasses import replace

import pytest

from engine.decision.ziping_career_structure import PublicationState, discriminate_ziping_career_structure
from engine.decision.ziping_career_structure_slice import (
    build_ziping_career_structure_slice,
    to_ziping_career_school_claim,
    to_ziping_career_structural_verdict,
)


def test_emit_builds_one_structure_claim_and_one_l3_pass(chart, supported_features) -> None:
    run = build_ziping_career_structure_slice(
        "C-ZIPING-CAREER-001",
        chart,
        supported_features,
        {"geju_type": "正格", "favor_shishen": [], "avoid_shishen": []},
        role="lead",
    )
    assert run.result.publication_state is PublicationState.EMIT
    assert len(run.claims) == 1
    assert len(run.verdicts) == 1
    assert run.claims[0].claim_type == "structure_claim"
    assert run.verdicts[0].verdict == "pass"
    assert "time_window" not in run.claims[0].metadata
    assert run.events == ()
    assert run.timings == ()


def test_first_falsifier_produces_zero_l2_and_zero_l3(
    chart, coarse_trigger_without_output_features
) -> None:
    run = build_ziping_career_structure_slice(
        "C-ZIPING-CAREER-FALSIFIER",
        chart,
        coarse_trigger_without_output_features,
        {"geju_type": "正格", "favor_shishen": [], "avoid_shishen": []},
        role="lead",
    )
    assert run.result.coarse_trigger_observed is True
    assert run.result.publication_state is PublicationState.HOLD
    assert run.claims == ()
    assert run.verdicts == ()
    assert run.events == ()
    assert run.timings == ()


@pytest.mark.parametrize("fixture_name", ["coarse_trigger_without_output_features", "protected_features"])
def test_non_emit_fails_closed_in_l2_adapter(request, chart, fixture_name: str) -> None:
    features = request.getfixturevalue(fixture_name)
    result = discriminate_ziping_career_structure(
        chart, features, {"geju_type": "正格", "favor_shishen": ["正官", "正印"], "avoid_shishen": ["伤官"]}
    )
    with pytest.raises(ValueError, match="emit publication state required"):
        to_ziping_career_school_claim(result, "lead", features.chart_id)


def test_l3_rejects_wrong_rule_identity_or_missing_family(chart, supported_features) -> None:
    result = discriminate_ziping_career_structure(
        chart, supported_features, {"geju_type": "正格", "favor_shishen": [], "avoid_shishen": []}
    )
    claim = to_ziping_career_school_claim(result, "lead", supported_features.chart_id)
    with pytest.raises(ValueError, match="task rule identity"):
        to_ziping_career_structural_verdict(
            "C-ZIPING-CAREER-001",
            result,
            replace(claim, metadata={**claim.metadata, "task_rule_id": "WRONG"}),
        )
```

- [ ] **Step 2: 运行 RED 测试**

Run:

```bat
pytest tests/ziping_career/test_staged_slice.py -q
```

Expected: collection ERROR，指出 `ziping_career_structure_slice` 不存在。

- [ ] **Step 3: 实现 L2 adapter**

固定行为：

```python
def to_ziping_career_school_claim(
    result: ZipingCareerDiscrimination,
    role: SchoolRole,
    chart_signature: str,
) -> SchoolClaim:
    if result.publication_state is not PublicationState.EMIT:
        raise ValueError("emit publication state required for Ziping career L2 adapter")
    if role == "abstain":
        raise ValueError("non-abstain L1 role required")
    matched = tuple(item for item in result.families if item.matched)
    required = {"official_path_anchor", "output_interference", "geju_direction"}
    if not required <= {item.family_key for item in matched}:
        raise ValueError("required evidence families are missing")
    evidence_refs = sorted({
        *(f"family:{item.family_key}" for item in matched),
        *(f"fact:{ref}" for item in matched for ref in item.fact_refs),
        *(f"feature:{ref}" for item in matched for ref in item.feature_refs),
        *(f"rule:{ref}" for item in matched for ref in item.production_rule_refs),
    })
    return SchoolClaim(
        claim_id=_stable_id("ziping-career-claim", "ziping", result.task_id, chart_signature, result.task_rule_id),
        school="ziping",
        role_granted_by_l1=role,
        domain="事业",
        claim_type="structure_claim",
        statement=MAPPING.conclusion_template,
        evidence_refs=evidence_refs,
        confidence=MAPPING.base_confidence,
        falsifier=MAPPING.falsifier,
        dependencies=[f"mapping:{result.mapping_digest}"],
        metadata={
            "task_id": result.task_id,
            "task_rule_id": result.task_rule_id,
            "publication_state": result.publication_state.value,
            "local_state": result.local_state.value,
            "mapping_digest": result.mapping_digest,
            "family_keys": sorted(item.family_key for item in matched),
        },
    )
```

不要导入或调用 `engine.v5.ziping_runner._role_change_claim()`；新切片拥有独立 task rule 身份。

- [ ] **Step 4: 实现专用 L3 adapter 与 staged run**

新增不可变 `ZipingCareerSliceRun`，字段固定为：

```python
@dataclass(frozen=True)
class ZipingCareerSliceRun:
    case_id: str
    result: ZipingCareerDiscrimination
    claims: tuple[SchoolClaim, ...]
    verdicts: tuple[StructuralVerdict, ...]
    events: tuple[object, ...] = ()
    timings: tuple[object, ...] = ()
```

`to_ziping_career_structural_verdict()` 必须检查：emit、task rule ID、mapping digest、required family keys、claim type、school、domain、metadata 中不存在 `time_window`。通过后返回唯一 `pass`：

```python
StructuralVerdict(
    verdict_id=_stable_id("ziping-career-l3", case_id, claim.claim_id, result.mapping_digest),
    claim_id=claim.claim_id,
    verdict="pass",
    structural_reason="官杀路径锚点、食伤介入与任务专属结构资格门均通过。",
    blocking_factors=[],
    required_support=[],
    confidence=min(0.7, claim.confidence),
)
```

`build_ziping_career_structure_slice()` 对非 emit 返回零 claims/verdicts；对 emit 构造恰好一个 claim 和 verdict；不得调用 L4/L5。

- [ ] **Step 5: 运行 GREEN 测试**

Run:

```bat
pytest tests/ziping_career/test_staged_slice.py tests/ziping_career/test_discriminator.py tests/ziping_career/test_rule_mapping.py -q
```

Expected: 全部 PASS。

- [ ] **Step 6: 增加重复身份与 role 边界测试**

加入测试：`role="abstain"` 不生成 Claim；篡改 `mapping_digest`、删除 required family、重复 evidence ref 都不能绕过 L3；supported 输入重跑得到相同 Claim/Verdict ID。运行 focused suite，预期 PASS。

- [ ] **Step 7: 独立提交 Task 3**

```bat
git add engine/decision/ziping_career_structure_slice.py tests/ziping_career/test_staged_slice.py && git commit -m "feat: stage ziping career l2 l3 slice"
```

- [ ] **Step 8: 提交后复核**

```bat
git show --stat --oneline HEAD && git status --short
```

Expected: 只含 Task 3 两个文件；工作区干净。

---

### Task 4: 确定性冻结与 L3 截断证明

**Files:**
- Modify: `engine/decision/ziping_career_structure_slice.py`
- Modify: `tests/ziping_career/test_staged_slice.py`

**Interfaces:**
- Consumes: `ZipingCareerSliceRun`。
- Produces: `FrozenZipingCareerSlice`、`freeze_ziping_career_slice(run) -> FrozenZipingCareerSlice`、`verify_frozen_ziping_career_slice(frozen) -> None`。

- [ ] **Step 1: 写冻结 RED 测试**

加入：

```python
from engine.decision.ziping_career_structure_slice import (
    freeze_ziping_career_slice,
    verify_frozen_ziping_career_slice,
)
from engine.evaluation.freeze import canonical_json


def test_supported_slice_freezes_byte_stably(chart, supported_features) -> None:
    kwargs = {
        "case_id": "C-ZIPING-FREEZE",
        "chart": chart,
        "features": supported_features,
        "geju_profile": {"geju_type": "正格", "favor_shishen": [], "avoid_shishen": []},
        "role": "lead",
    }
    first = freeze_ziping_career_slice(build_ziping_career_structure_slice(**kwargs))
    second = freeze_ziping_career_slice(build_ziping_career_structure_slice(**kwargs))
    verify_frozen_ziping_career_slice(first)
    verify_frozen_ziping_career_slice(second)
    assert first.freeze_hash == second.freeze_hash
    assert canonical_json(first.to_dict()).encode("utf-8") == canonical_json(second.to_dict()).encode("utf-8")
    assert first.events == ()
    assert first.timings == ()


def test_feature_and_profile_order_permutation_keeps_freeze_hash(chart, supported_features) -> None:
    left = build_ziping_career_structure_slice(
        "C-ZIPING-PERMUTE", chart, supported_features,
        {"geju_type": "正格", "favor_shishen": ["正官", "正印"], "avoid_shishen": []}, role="lead"
    )
    reordered = replace(
        supported_features,
        ten_god_counts=dict(reversed(list(supported_features.ten_god_counts.items()))),
    )
    right = build_ziping_career_structure_slice(
        "C-ZIPING-PERMUTE", chart, reordered,
        {"avoid_shishen": [], "favor_shishen": ["正印", "正官"], "geju_type": "正格"}, role="lead"
    )
    assert freeze_ziping_career_slice(left).freeze_hash == freeze_ziping_career_slice(right).freeze_hash


def test_first_falsifier_freezes_zero_l2_l3_and_zero_timing(
    chart, coarse_trigger_without_output_features
) -> None:
    frozen = freeze_ziping_career_slice(build_ziping_career_structure_slice(
        "C-ZIPING-FALSIFIER-FROZEN", chart, coarse_trigger_without_output_features,
        {"geju_type": "正格", "favor_shishen": [], "avoid_shishen": []}, role="lead"
    ))
    assert frozen.claims == ()
    assert frozen.verdicts == ()
    assert frozen.events == ()
    assert frozen.timings == ()
```

- [ ] **Step 2: 运行 RED 测试**

Run:

```bat
pytest tests/ziping_career/test_staged_slice.py -q
```

Expected: FAIL，指出冻结类型或函数未定义。

- [ ] **Step 3: 实现规范化冻结类型**

`FrozenZipingCareerSlice` 必须包含：schema version、case ID、task ID、task rule ID、mapping digest、local/publication state、families、gates、claims、verdicts、events、timings、freeze hash。`to_dict()` 对 mapping、families、refs、claims 和 verdicts 做稳定排序。

使用现有：

```python
from engine.evaluation.freeze import canonical_json, compute_freeze_hash
```

冻结算法：

```python
def freeze_ziping_career_slice(run: ZipingCareerSliceRun) -> FrozenZipingCareerSlice:
    provisional = FrozenZipingCareerSlice.from_run(run, freeze_hash="")
    payload = provisional.to_dict()
    payload.pop("freeze_hash")
    return replace(provisional, freeze_hash=compute_freeze_hash(payload))

def verify_frozen_ziping_career_slice(frozen: FrozenZipingCareerSlice) -> None:
    payload = frozen.to_dict()
    claimed = payload.pop("freeze_hash")
    if compute_freeze_hash(payload) != claimed:
        raise ValueError("freeze hash mismatch")
```

- [ ] **Step 4: 添加静态 L3 截断测试**

AST 检查 `engine/decision/ziping_career_structure_slice.py` 不导入 `l4_events`、`l5_timing`、`ren_career_timing`、`render_report`；检查源码中不出现 `TimeWindow(`、`TimingProbability(`、`build_timing_probabilities(`。

- [ ] **Step 5: 运行 GREEN 与全子平专项**

```bat
pytest tests/ziping_career -q
```

Expected: 全部 PASS。

- [ ] **Step 6: 独立提交 Task 4**

```bat
git add engine/decision/ziping_career_structure_slice.py tests/ziping_career/test_staged_slice.py && git commit -m "test: freeze ziping career staged slice"
```

- [ ] **Step 7: 提交后复核**

```bat
git show --stat --oneline HEAD && git status --short
```

Expected: 只含 Task 4 两个文件；工作区干净。

---

### Task 5: G5 生产隔离与既有路径回归

**Files:**
- Create: `tests/ziping_career/test_production_isolation.py`

**Interfaces:**
- Consumes: staged 文件与现有生产护栏常量。
- Produces: 默认入口、production artifact、公共 schema、任派/杨派路径零变化的自动证据。

- [ ] **Step 1: 写生产隔离测试**

创建 `tests/ziping_career/test_production_isolation.py`：

```python
from __future__ import annotations

import ast
import hashlib
import inspect
import json
from pathlib import Path

from engine.application.pipeline_runner import run_pipeline
from engine.claims.runner_registry import DEFAULT_RUNNER_REGISTRY
from engine.decision.models import SchoolClaim, StructuralVerdict

PIPELINE_SIGNATURE = (
    "(parsed: 'ParsedInput', *, cases_dir: 'Optional[Union[str, Path]]' = None, "
    "write_findings: 'bool' = True, timing: 'Optional[PipelineTiming]' = None, "
    "threshold_seconds: 'float' = 60.0) -> 'AnalysisOutput'"
)
DEFAULT_REGISTRY_SHA256 = "88779529d0d470d80558b2005a79089950adfc4deaf3d96e7b7d20bd78c0b16d"
PRODUCTION_CLAIM_RULES_SHA256 = "6396883d8db0b8d24c6c15435c130c6f9ae045c8c6d1fe8d2a84748c5b0bebef"


def _sha256(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_default_registry_pipeline_and_production_claim_rules_are_unchanged() -> None:
    registrations = sorted(
        (school, task, generator.__module__ + "." + generator.__name__)
        for (school, task), generator in DEFAULT_RUNNER_REGISTRY._runners.items()
    )
    digest = hashlib.sha256(json.dumps(registrations, separators=(",", ":")).encode()).hexdigest()
    assert digest == DEFAULT_REGISTRY_SHA256
    assert str(inspect.signature(run_pipeline)) == PIPELINE_SIGNATURE
    assert _sha256("theory/production/claim-rules-v1.yaml") == PRODUCTION_CLAIM_RULES_SHA256


def test_public_schema_has_not_been_extended_for_slice() -> None:
    assert tuple(SchoolClaim.__dataclass_fields__) == (
        "claim_id", "school", "role_granted_by_l1", "domain", "claim_type",
        "statement", "evidence_refs", "confidence", "falsifier", "dependencies", "metadata",
    )
    assert tuple(StructuralVerdict.__dataclass_fields__) == (
        "verdict_id", "claim_id", "verdict", "structural_reason",
        "blocking_factors", "required_support", "confidence",
    )


def test_staged_modules_do_not_import_default_registry_pipeline_reports_or_timing() -> None:
    forbidden = ("runner_registry", "pipeline_runner", "render_report", "l5_timing", "ren_career_timing")
    for relative in (
        "engine/decision/ziping_career_rules.py",
        "engine/decision/ziping_career_structure.py",
        "engine/decision/ziping_career_structure_slice.py",
    ):
        tree = ast.parse(Path(relative).read_text(encoding="utf-8"))
        imported = [
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        ]
        assert not any(token in module for token in forbidden for module in imported), relative
```

- [ ] **Step 2: 运行生产隔离与 focused regression**

```bat
pytest tests/ziping_career tests/test_production_entrypoints_unchanged.py tests/ren_timing tests/yang_marriage tests/claims/test_multi_school_freeze.py tests/claims/test_executable_claim_rules.py tests/r10/test_r10_ziping_career_l2.py tests/r10/test_r10_ziping_career_layers.py -q
```

Expected: 全部 PASS；允许既有、与本切片无关的 warning，但不允许 failure。

- [ ] **Step 3: 核验未触碰并行写区与生产文件**

```bat
git diff --name-only origin/main...HEAD -- engine/decision/yang_marriage.py engine/decision/yang_marriage_claims.py tests/yang_marriage engine/decision/ren_career_timing.py engine/decision/ren_career_timing_slice.py engine/decision/ren_timing_rules.py theory/production/ren-career-timing-rules-v1.yaml tests/ren_timing theory/production/claim-rules-v1.yaml engine/claims/runner_registry.py engine/application/pipeline_runner.py engine/decision/models.py
```

Expected: 无输出。若出现输出，G5 失败，不提交。

- [ ] **Step 4: 独立提交 Task 5**

```bat
git add tests/ziping_career/test_production_isolation.py && git commit -m "test: guard ziping career production isolation"
```

- [ ] **Step 5: 提交后复核**

```bat
git show --stat --oneline HEAD && git status --short
```

Expected: 只含 Task 5 测试文件；工作区干净。

---

### Task 6: G0-G5 登记、验证报告与最终复核

**Files:**
- Modify: `theory/executable-slices-v1.yaml`
- Modify: `META/project-state.json`
- Modify: `tests/test_project_metadata.py`
- Modify: `tests/tools/test_theory_slice_status.py`
- Create: `reports/ziping-career-structure-slice-g0-g5-verification.md`

**Interfaces:**
- Consumes: Task 1-5 的已提交实现与测试证据。
- Produces: `executable_slice_count(ziping)=1`、机器状态 `staged_verified_production_unchanged`、G0-G5 证据包；不产生生产开关。

- [ ] **Step 1: 先运行完整 focused gate，保存真实结果**

```bat
pytest tests/ziping_career tests/tools/test_theory_slice_status.py tests/test_project_metadata.py tests/test_production_entrypoints_unchanged.py tests/ren_timing tests/yang_marriage tests/claims/test_multi_school_freeze.py tests/claims/test_executable_claim_rules.py tests/r10/test_r10_ziping_career_l2.py tests/r10/test_r10_ziping_career_layers.py -q
```

Expected: 0 failed。记录真实 passed/skipped/warnings/耗时，禁止预填数字。

- [ ] **Step 2: 写登记 RED 测试**

在 `tests/test_project_metadata.py` 增加：

```python
def test_ziping_career_structure_slice_is_staged_verified_without_production_change() -> None:
    state = json.loads(Path("META/project-state.json").read_text(encoding="utf-8"))
    assert state["intelligence_platform_status"]["ziping_career_official_path_disruption_slice"] == (
        "staged_verified_production_unchanged"
    )
```

在 `tests/tools/test_theory_slice_status.py` 的真实仓库扫描测试中断言：

```python
status = scan_theory_slices(Path("."))
assert status["schools"]["ziping"] == {
    "catalog_count": 933,
    "executable_slice_count": 1,
}
```

运行：

```bat
pytest tests/test_project_metadata.py tests/tools/test_theory_slice_status.py -q
```

Expected: FAIL；状态键不存在，子平 executable slice 仍为 0。

- [ ] **Step 3: 最小登记 executable slice**

向 `theory/executable-slices-v1.yaml` 添加：

```yaml
  - slice_id: ZIPING-CAREER-OFFICIAL-PATH-DISRUPTION-V1
    school_id: ziping
    task_id: career.role_change
    target_layer: L3
    status: staged_verified
    artifacts:
      - theory/production/ziping-career-structure-rules-v1.yaml
      - engine/decision/ziping_career_rules.py
      - engine/decision/ziping_career_structure.py
      - engine/decision/ziping_career_structure_slice.py
      - tests/ziping_career/test_staged_slice.py
```

只新增这一条，不重排或改写既有任派、杨派、段派、高派条目。

- [ ] **Step 4: 最小登记机器状态**

在 `META/project-state.json` 的 `intelligence_platform_status` 增加：

```json
"ziping_career_official_path_disruption_slice": "staged_verified_production_unchanged"
```

不修改产品版本、current phase、生产开关或任派状态。

- [ ] **Step 5: 运行 GREEN 登记测试**

```bat
pytest tests/test_project_metadata.py tests/tools/test_theory_slice_status.py -q && python tools/theory_slice_status.py --format json
```

Expected: PASS；输出显示子平 `catalog_count=933`、`executable_slice_count=1`。

- [ ] **Step 6: 创建真实 G0-G5 验证报告**

创建 `reports/ziping-career-structure-slice-g0-g5-verification.md`，必须包含：

```markdown
# 子平职业路径结构切片 G0-G5 验证

## 结论
状态：`staged_verified_production_unchanged`。

该结论只证明来源映射、纯判别、L2/L3 适配、冻结确定性和生产隔离通过；不代表准确率提升、生产晋级或可用于正式报告。

## G0
- production IDs：`ZP-PROD-20260622-011/012`
- task rule ID：`ZIPING-CAREER-OFFICIAL-PATH-DISRUPTION-V1`
- `catalog_count=933`、production entries=933、`executable_slice_count=1`

## G1
- 记录 supported/weakened/contradicted/abstain 与 emit/hold/abstain/unsupported 覆盖。
- 首个证伪点：粗官杀 trigger 存在、食伤必要门失败时不发布。

## G2-G4
- 仅 emit 生成一个无时间窗 L2 structure Claim。
- 仅合格 Claim 生成一个 L3 pass。
- 首证伪点 L2=0、L3=0、events=0、timings=0。
- 重跑与输入顺序置换后冻结 hash 一致。

## G5
- 默认 registry digest 未变化。
- pipeline 签名未变化。
- production claim-rules SHA-256 未变化。
- 公共 schema、报告入口、杨派与任派路径未变化。

## 测试证据
- 写入 Step 1 的真实命令与真实结果；不得写未完整运行的 full-suite 成功声明。

## G6
未进入。需要独立冻结样本后验和另行审批。
```

所有文件引用使用仓库相对路径；不要硬编码 Git HEAD。

- [ ] **Step 7: 最终 G0-G5 focused suite**

```bat
pytest tests/ziping_career tests/tools/test_theory_slice_status.py tests/test_project_metadata.py tests/test_production_entrypoints_unchanged.py tests/ren_timing tests/yang_marriage tests/claims/test_multi_school_freeze.py tests/claims/test_executable_claim_rules.py tests/r10/test_r10_ziping_career_l2.py tests/r10/test_r10_ziping_career_layers.py -q
```

Expected: 0 failed。若结果与报告数字不一致，先修报告再继续。

- [ ] **Step 8: 工具、规则与 diff 护栏**

```bat
python tools/tool_registry.py --check && python tools/rule_status_scan.py --check && git diff --check && git diff --name-only -- theory/production/claim-rules-v1.yaml engine/claims/runner_registry.py engine/application/pipeline_runner.py engine/decision/models.py engine/decision/yang_marriage.py engine/decision/yang_marriage_claims.py tests/yang_marriage engine/decision/ren_career_timing.py engine/decision/ren_career_timing_slice.py engine/decision/ren_timing_rules.py tests/ren_timing
```

Expected: 两个工具检查通过；`git diff --check` 通过；受保护路径无输出。

- [ ] **Step 9: 独立提交 Task 6**

```bat
git add theory/executable-slices-v1.yaml META/project-state.json tests/test_project_metadata.py tests/tools/test_theory_slice_status.py reports/ziping-career-structure-slice-g0-g5-verification.md && git commit -m "docs: register staged ziping career structure slice"
```

- [ ] **Step 10: 最终 Git 一致性复核**

```bat
git fetch --prune origin && git status --short --branch && git rev-list --left-right --count HEAD...origin/main && git log -7 --oneline --decorate
```

Expected: 工作区干净；本分支只领先本计划的规格与独立任务提交。若 origin/main 前进，先审计新提交与本计划写区交集，不自动 rebase、merge 或覆盖。

---

## 最终验收清单

- [ ] Task 1-6 每项都有独立 RED、GREEN、提交与提交后复核证据。
- [ ] production IDs 与 task rule ID 映射稳定、严格、不可变、来源可解析。
- [ ] 首个证伪点明确观察到粗官杀 trigger，但食伤必要门失败。
- [ ] 首个证伪点 L2 Claim=0、L3 pass=0、EventHypothesis=0、TimingProbability=0。
- [ ] supported/emit 恰好生成一个无时间窗 L2 structure Claim 与一个专用 L3 pass。
- [ ] contradicted 保留局部反证并发布为 hold，不生成 oppose Claim。
- [ ] 冻结重跑和顺序置换字节稳定。
- [ ] 默认 registry、正式 pipeline、production claim-rules、公共 schema、报告入口、任派与杨派路径零变化。
- [ ] `theory_slice_status` 显示子平 `catalog_count=933`、`executable_slice_count=1`。
- [ ] 最终状态仅为 `staged_verified_production_unchanged`，未进入 G6。
