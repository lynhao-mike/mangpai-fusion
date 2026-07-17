# Cross-School Slicing and Ren Career Timing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish separate catalog/executable-slice metrics and build a staged, deterministic Ren-school career-role-change timing slice that emits L5 timing only when auditable sui-yun triggers exist.

**Architecture:** Keep the production path unchanged. Add one read-only metrics tool, one Ren-specific immutable discriminator, one strict Ren timing rule registry, and one staged adapter/freeze projection; validate each boundary with synthetic tests before any historical evaluation. Do not create a generic runtime framework until this second school slice proves which interfaces are actually shared.

**Tech Stack:** Python 3.11+, stdlib `dataclasses`/`enum`/`hashlib`/`json`, PyYAML already used by the repository, pytest, existing `ChartFactLedger`, `ChartFeatureVector`, `EventHypothesis`, `TimingProbability`, `BlindSchoolOutput`, and `freeze_outputs()` contracts.

## Global Constraints

- Approved design source: `docs/superpowers/specs/2026-07-17-cross-school-theory-slicing-and-ren-timing-design.md`.
- Work from an isolated worktree at execution time; re-run `git fetch --prune origin` and record start-state equality without hardcoding HEAD in long-lived docs.
- Do not modify `engine/claims/domain.py`, `engine/decision/models.py`, `engine/decision/l5_timing.py`, `engine/claims/runner_registry.py`, `engine/application/pipeline_runner.py`, `theory/production/claim-rules-v1.yaml`, report renderers, or public report schemas.
- Do not modify `engine/decision/yang_marriage.py`, `engine/decision/yang_marriage_slice.py`, `tests/yang_marriage/`, or any file currently owned by the Yang agent.
- Do not modify shared state or guard files until Task 8; `META/project-state.json`, `tests/test_project_metadata.py`, and `tests/test_production_entrypoints_unchanged.py` have one final integration owner.
- The default runner registry, production pipeline, production YAML, public schemas, and report entrypoints must remain unchanged through G0-G5.
- Ren timing consumes an already-qualified `career.role_change` event; it must not create or re-qualify the event.
- Only local publication state `emit` may enter the L5 adapter. `hold`, `abstain`, and `unsupported` must fail closed.
- No valid Ren trigger means zero staged L5 objects; never call the generic default-window builder as fallback.
- Synthetic tests and deterministic freeze proof are gates; they do not establish accuracy improvement or production GO.
- Use TDD for every behavior change and commit after every independently reviewable task.

---

## File Responsibility Map

| Path | Action | Single responsibility |
|---|---|---|
| `tools/theory_slice_status.py` | Create | Report `catalog_count` and manifest-backed `executable_slice_count` without changing rule lifecycle state. |
| `theory/executable-slices-v1.yaml` | Create | Registry of slices that satisfy the approved minimum artifact contract; initial records describe existing audited slices, and the Ren record is added only after G0-G5. |
| `tests/tools/test_theory_slice_status.py` | Create | Validate metric separation, manifest strictness, deterministic ordering, and CLI JSON output. |
| `theory/production/ren-career-timing-rules-v1.yaml` | Create | Ren career timing atoms, priorities, source locators, and confidence policy; staged-only. |
| `engine/decision/ren_timing_rules.py` | Create | Strict loader and immutable rule DTO for the Ren timing YAML. |
| `engine/decision/ren_career_timing.py` | Create | Extract atoms, reduce evidence families, evaluate gates, and return immutable local results. |
| `engine/decision/ren_career_timing_slice.py` | Create | Emit-only L5 adapter, staged assembly, evidence resolution, and blind-output projection for freezing. |
| `tests/ren_timing/conftest.py` | Create | Synthetic charts, qualified events, and canonical fixtures only; no historical data. |
| `tests/ren_timing/test_rule_registry.py` | Create | Rule schema/source/operator rejection and deterministic load tests. |
| `tests/ren_timing/test_discriminator.py` | Create | Atom, deduplication, state-machine, gate, ordering, and first-falsifier tests. |
| `tests/ren_timing/test_adapter.py` | Create | Emit-only adapter, valid timing window, evidence resolution, and invalid-state failures. |
| `tests/ren_timing/test_staged_slice.py` | Create | Staged assembly, freeze determinism, trace wiring, and production isolation tests. |
| `tests/test_production_entrypoints_unchanged.py` | Modify in Task 8 only | Add immutable hashes for the untouched production rule file and report entrypoint signatures if not already covered. |
| `META/project-state.json` | Modify in Task 8 only | Record staged capability after all gates pass; do not claim production activation. |
| `tests/test_project_metadata.py` | Modify in Task 8 only | Validate the exact staged state key and value. |
| `tools/README.md` | Modify in Task 8 only | Document the read-only metrics command and explicitly mark Ren slice as staged-only. |

---

### Task 1: Freeze Baseline and Synthetic Fixture Contract

**Files:**
- Create: `tests/ren_timing/conftest.py`
- Create: `tests/ren_timing/test_staged_slice.py`

**Interfaces:**
- Consumes: `ChartFactLedger`, `EventHypothesis`, `build_chart_feature_vector()`.
- Produces: pytest fixtures `career_event`, `trigger_chart`, `no_trigger_chart`, `partial_chart`, and a baseline isolation test used by all later tasks.

- [ ] **Step 1: Write the synthetic fixture module**

```python
from __future__ import annotations

import pytest

from engine.decision.models import ChartFactLedger, EventHypothesis
from engine.features import build_chart_feature_vector


@pytest.fixture
def career_event() -> EventHypothesis:
    return EventHypothesis(
        event_id="evt-career-role-change-001",
        source_verdict_ids=["sv-career-001"],
        domain="事业",
        event_type="career.role_change",
        subject="命主",
        concrete_event="职业角色或岗位发生显著变化",
        landing_path="上游事件资格已通过；任派只负责应期",
        confidence=0.72,
    )


@pytest.fixture
def trigger_chart() -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker="乾",
        four_pillars={"year": "庚申", "month": "戊寅", "day": "壬子", "hour": "辛丑"},
        dayun_steps=[{"ganzhi": "甲午", "start_year": 2024, "end_year": 2033}],
        liunian_steps=[
            {"year": 2026, "ganzhi": "丙午", "dayun": "甲午"},
            {"year": 2028, "ganzhi": "戊申", "dayun": "甲午"},
        ],
    )


@pytest.fixture
def no_trigger_chart() -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker="乾",
        four_pillars={"year": "甲子", "month": "丁卯", "day": "庚午", "hour": "己酉"},
        dayun_steps=[{"ganzhi": "丙辰", "start_year": 2024, "end_year": 2033}],
        liunian_steps=[{"year": 2027, "ganzhi": "丁巳", "dayun": "丙辰"}],
    )


@pytest.fixture
def partial_chart() -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker="乾",
        four_pillars={"year": "庚申", "month": "戊寅", "day": "壬子", "hour": "辛丑"},
        dayun_steps=[],
        liunian_steps=[],
        missing_fields=["dayun", "liunian"],
    )


@pytest.fixture
def trigger_features(trigger_chart: ChartFactLedger):
    return build_chart_feature_vector(trigger_chart)
```

- [ ] **Step 2: Write the production-baseline test before slice code exists**

```python
from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

from engine.application.pipeline_runner import run_pipeline
from engine.claims.runner_registry import DEFAULT_RUNNER_REGISTRY


def _sha256(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_ren_staged_work_starts_from_unchanged_production_boundaries() -> None:
    registrations = sorted(
        (school, task, fn.__module__ + "." + fn.__name__)
        for (school, task), fn in DEFAULT_RUNNER_REGISTRY._runners.items()
    )
    assert hashlib.sha256(json.dumps(registrations, separators=(",", ":")).encode()).hexdigest() == (
        "88779529d0d470d80558b2005a79089950adfc4deaf3d96e7b7d20bd78c0b16d"
    )
    assert "ren_career_timing" not in str(inspect.signature(run_pipeline))
    assert _sha256("theory/production/claim-rules-v1.yaml") == (
        "6396883d8db0b8d24c6c15435c130c6f9ae045c8c6d1fe8d2a84748c5b0bebef"
    )
```

- [ ] **Step 3: Run fixture collection and baseline guard**

Run: `pytest tests/ren_timing/test_staged_slice.py --collect-only -q && pytest tests/ren_timing/test_staged_slice.py -q`

Expected: collection succeeds and the baseline guard passes.

- [ ] **Step 4: Commit**

```bat
git add tests/ren_timing/conftest.py tests/ren_timing/test_staged_slice.py
git commit -m "test: freeze ren timing staged baseline"
```

---

### Task 2: Separate Catalog and Executable-Slice Metrics

**Files:**
- Create: `theory/executable-slices-v1.yaml`
- Create: `tools/theory_slice_status.py`
- Create: `tests/tools/test_theory_slice_status.py`

**Interfaces:**
- Produces: `scan_theory_slices(root: Path) -> dict[str, object]` and CLI `python -m tools.theory_slice_status --format json`.
- Manifest schema: `schema_version`, `slices`; each slice has `slice_id`, `school_id`, `task_id`, `target_layer`, `status`, and `artifacts`.

- [ ] **Step 1: Write failing manifest and scanner tests**

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.theory_slice_status import load_executable_manifest, scan_theory_slices


def test_metrics_keep_catalog_and_executable_counts_separate(tmp_path: Path) -> None:
    (tmp_path / "theory" / "ren").mkdir(parents=True)
    (tmp_path / "theory" / "ren" / "index.yaml").write_text(
        "rules:\n  - id: R1\n  - id: R2\n", encoding="utf-8"
    )
    (tmp_path / "theory" / "executable-slices-v1.yaml").write_text(
        "schema_version: executable-slices/v1\nslices:\n"
        "  - slice_id: REN-CAREER-TIMING-V1\n"
        "    school_id: ren\n    task_id: career.role_change\n"
        "    target_layer: L5\n    status: staged_verified\n"
        "    artifacts: [engine/decision/ren_career_timing.py]\n",
        encoding="utf-8",
    )
    result = scan_theory_slices(tmp_path)
    assert result["schools"]["ren"] == {"catalog_count": 2, "executable_slice_count": 1}


def test_manifest_rejects_unknown_keys(tmp_path: Path) -> None:
    path = tmp_path / "manifest.yaml"
    path.write_text(
        "schema_version: executable-slices/v1\nslices:\n"
        "  - slice_id: X\n    school_id: ren\n    task_id: x\n"
        "    target_layer: L5\n    status: staged_verified\n    artifacts: []\n    extra: bad\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown slice keys"):
        load_executable_manifest(path)
```

- [ ] **Step 2: Run tests and verify import failure**

Run: `pytest tests/tools/test_theory_slice_status.py -q`

Expected: FAIL because `tools.theory_slice_status` does not exist.

- [ ] **Step 3: Create the initial executable-slice manifest**

```yaml
schema_version: executable-slices/v1
slices:
  - slice_id: DUAN-CAREER-ROLE-CHANGE-V1
    school_id: duan
    task_id: career.role_change
    target_layer: L2
    status: existing_audited
    artifacts:
      - engine/v5/duan_runner.py
      - theory/production/claim-rules-v1.yaml
  - slice_id: GAO-HEALTH-SYSTEM-RISK-V1
    school_id: gao
    task_id: health.system_risk
    target_layer: L2
    status: existing_audited
    artifacts:
      - engine/v5/gao_runner.py
      - theory/production/claim-rules-v1.yaml
  - slice_id: YANG-MARRIAGE-DIVORCE-RISK-V1
    school_id: yang
    task_id: marriage.divorce_or_remarriage
    target_layer: L2
    status: existing_audited
    artifacts:
      - engine/v5/yang_runner.py
      - theory/production/claim-rules-v1.yaml
```

- [ ] **Step 4: Implement the strict read-only scanner**

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

_REQUIRED = {"slice_id", "school_id", "task_id", "target_layer", "status", "artifacts"}
_ALLOWED_STATUS = {"existing_audited", "staged_verified", "production_active"}
_SCHOOLS = ("gao", "duan", "yang", "ren", "ziping", "tiaohou_ditiansui")


def load_executable_manifest(path: Path) -> list[dict[str, Any]]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "slices"}:
        raise ValueError("manifest requires exactly schema_version and slices")
    if raw["schema_version"] != "executable-slices/v1" or not isinstance(raw["slices"], list):
        raise ValueError("invalid executable-slices manifest")
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for item in raw["slices"]:
        if not isinstance(item, dict):
            raise ValueError("slice record must be mapping")
        unknown = set(item) - _REQUIRED
        if unknown:
            raise ValueError(f"unknown slice keys: {sorted(unknown)}")
        if set(item) != _REQUIRED:
            raise ValueError("slice record missing required keys")
        if item["slice_id"] in seen:
            raise ValueError(f"duplicate slice_id: {item['slice_id']}")
        if item["status"] not in _ALLOWED_STATUS or not isinstance(item["artifacts"], list):
            raise ValueError("invalid slice status or artifacts")
        seen.add(item["slice_id"])
        rows.append(dict(item))
    return sorted(rows, key=lambda row: row["slice_id"])


def _catalog_count(path: Path) -> int:
    if not path.exists():
        return 0
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return len(raw)
    if isinstance(raw, dict):
        for key in ("rules", "entries", "items"):
            if isinstance(raw.get(key), list):
                return len(raw[key])
    return 0


def scan_theory_slices(root: Path) -> dict[str, object]:
    manifest = load_executable_manifest(root / "theory" / "executable-slices-v1.yaml")
    schools: dict[str, dict[str, int]] = {}
    for school in _SCHOOLS:
        catalog = _catalog_count(root / "theory" / school / "index.yaml")
        executable = sum(1 for row in manifest if row["school_id"] == school)
        schools[school] = {"catalog_count": catalog, "executable_slice_count": executable}
    return {"schema_version": "theory-slice-status/v1", "schools": schools, "slices": manifest}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=("json",), default="json")
    args = parser.parse_args()
    print(json.dumps(scan_theory_slices(Path.cwd()), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run unit and real-repository scanner checks**

Run: `pytest tests/tools/test_theory_slice_status.py -q && python -m tools.theory_slice_status --format json > _theory_slice_status.json && python -c "import json; d=json.load(open('_theory_slice_status.json',encoding='utf-8')); assert 'ren' in d['schools']; print(d['schools']['ren'])"`

Expected: tests PASS; the command prints separate Ren catalog and executable counts without modifying theory files.

- [ ] **Step 6: Remove the temporary output and commit**

```bat
del _theory_slice_status.json
git add theory/executable-slices-v1.yaml tools/theory_slice_status.py tests/tools/test_theory_slice_status.py
git commit -m "feat: separate theory catalog and executable slice metrics"
```

---

### Task 3: Strict Ren Timing Rule Registry

**Files:**
- Create: `theory/production/ren-career-timing-rules-v1.yaml`
- Create: `engine/decision/ren_timing_rules.py`
- Create: `tests/ren_timing/test_rule_registry.py`

**Interfaces:**
- Produces: immutable `RenTimingRule` and `load_ren_timing_rules(path: Path | None = None) -> tuple[RenTimingRule, ...]`.
- Supported relations: `冲`, `刑`, `穿`, `合`, `伏吟`; lower integer priority wins.

- [ ] **Step 1: Write failing loader tests**

```python
from pathlib import Path

import pytest

from engine.decision.ren_timing_rules import load_ren_timing_rules


def test_default_registry_is_deterministic_and_source_backed() -> None:
    first = load_ren_timing_rules()
    second = load_ren_timing_rules()
    assert first == second
    assert [item.relation for item in first] == ["冲", "刑", "穿", "伏吟", "合"]
    assert all(Path(item.source_path).is_file() for item in first)


def test_registry_rejects_unknown_relation(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        "schema_version: ren-career-timing-rules/v1\nrules:\n"
        "  - rule_id: BAD\n    relation: 破\n    priority: 1\n"
        "    source_path: theory/ren/index.yaml\n    source_anchor: M4-R-001\n"
        "    confidence: 0.6\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unsupported relation"):
        load_ren_timing_rules(path)
```

- [ ] **Step 2: Run tests and verify import failure**

Run: `pytest tests/ren_timing/test_rule_registry.py -q`

Expected: FAIL because the loader does not exist.

- [ ] **Step 3: Create the staged rule registry**

```yaml
schema_version: ren-career-timing-rules/v1
rules:
  - rule_id: REN-CAREER-TIMING-CHONG-V1
    relation: 冲
    priority: 10
    source_path: theory/ren/index.yaml
    source_anchor: M4-R-031
    confidence: 0.72
  - rule_id: REN-CAREER-TIMING-XING-V1
    relation: 刑
    priority: 20
    source_path: theory/ren/index.yaml
    source_anchor: M4-R-031
    confidence: 0.68
  - rule_id: REN-CAREER-TIMING-CHUAN-V1
    relation: 穿
    priority: 30
    source_path: theory/ren/index.yaml
    source_anchor: M4-R-031
    confidence: 0.66
  - rule_id: REN-CAREER-TIMING-FUYIN-V1
    relation: 伏吟
    priority: 40
    source_path: theory/ren/index.yaml
    source_anchor: M4-R-031
    confidence: 0.64
  - rule_id: REN-CAREER-TIMING-HE-V1
    relation: 合
    priority: 50
    source_path: theory/ren/index.yaml
    source_anchor: M4-R-031
    confidence: 0.62
```

- [ ] **Step 4: Implement the immutable strict loader**

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

_ALLOWED_RELATIONS = ("冲", "刑", "穿", "伏吟", "合")
_DEFAULT = Path("theory/production/ren-career-timing-rules-v1.yaml")


@dataclass(frozen=True)
class RenTimingRule:
    rule_id: str
    relation: str
    priority: int
    source_path: str
    source_anchor: str
    confidence: float


def load_ren_timing_rules(path: Path | None = None) -> tuple[RenTimingRule, ...]:
    source = path or _DEFAULT
    raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "rules"}:
        raise ValueError("ren timing registry requires schema_version and rules")
    if raw["schema_version"] != "ren-career-timing-rules/v1" or not isinstance(raw["rules"], list):
        raise ValueError("invalid ren timing registry")
    required = {"rule_id", "relation", "priority", "source_path", "source_anchor", "confidence"}
    seen_ids: set[str] = set()
    seen_relations: set[str] = set()
    rules: list[RenTimingRule] = []
    for item in raw["rules"]:
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError("invalid ren timing rule fields")
        relation = str(item["relation"])
        if relation not in _ALLOWED_RELATIONS:
            raise ValueError(f"unsupported relation: {relation}")
        if item["rule_id"] in seen_ids or relation in seen_relations:
            raise ValueError("duplicate ren timing rule identity")
        confidence = float(item["confidence"])
        if not 0.0 <= confidence <= 1.0 or type(item["priority"]) is not int:
            raise ValueError("invalid priority or confidence")
        if path is None and not Path(item["source_path"]).is_file():
            raise ValueError(f"missing source path: {item['source_path']}")
        seen_ids.add(item["rule_id"])
        seen_relations.add(relation)
        rules.append(RenTimingRule(confidence=confidence, **{k: item[k] for k in required - {"confidence"}}))
    return tuple(sorted(rules, key=lambda rule: (rule.priority, rule.rule_id)))
```

- [ ] **Step 5: Run tests and commit**

Run: `pytest tests/ren_timing/test_rule_registry.py -q`

Expected: all tests PASS.

```bat
git add theory/production/ren-career-timing-rules-v1.yaml engine/decision/ren_timing_rules.py tests/ren_timing/test_rule_registry.py
git commit -m "feat: add strict ren career timing rule registry"
```

---

### Task 4: Immutable Trigger Atoms and Evidence-Family Reduction

**Files:**
- Create: `engine/decision/ren_career_timing.py`
- Create: `tests/ren_timing/test_discriminator.py`

**Interfaces:**
- Produces: `TriggerAtom`, `EvidenceFamily`, `RenTimingResult`, `RenTimingState`, `PublicationState`, and `discriminate_ren_career_timing(chart, features, event, *, task_id="career.role_change")`.
- This task implements extraction/reduction only; adapter behavior comes in Task 5.

- [ ] **Step 1: Write failing atom and deduplication tests**

```python
from dataclasses import replace

from engine.decision.ren_career_timing import discriminate_ren_career_timing


def test_relation_atoms_are_family_deduplicated(trigger_chart, trigger_features, career_event) -> None:
    result = discriminate_ren_career_timing(trigger_chart, trigger_features, career_event)
    keys = [family.family_key for family in result.evidence_families]
    assert len(keys) == len(set(keys))
    assert all(atom.year >= 1900 for family in result.evidence_families for atom in family.atoms)


def test_input_order_does_not_change_result(trigger_chart, trigger_features, career_event) -> None:
    reversed_chart = replace(trigger_chart, liunian_steps=list(reversed(trigger_chart.liunian_steps)))
    reversed_features = replace(trigger_features, chart_id=trigger_features.chart_id)
    assert discriminate_ren_career_timing(trigger_chart, trigger_features, career_event).to_dict() == (
        discriminate_ren_career_timing(reversed_chart, reversed_features, career_event).to_dict()
    )
```

- [ ] **Step 2: Run tests and verify failure**

Run: `pytest tests/ren_timing/test_discriminator.py -q`

Expected: FAIL because `engine.decision.ren_career_timing` does not exist.

- [ ] **Step 3: Implement immutable DTOs and relation extraction**

```python
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any

from engine.decision.models import ChartFactLedger, EventHypothesis
from engine.decision.ren_timing_rules import RenTimingRule, load_ren_timing_rules
from engine.features import ChartFeatureVector
from engine.predicates.relations import zhi_chong, zhi_chuan, zhi_liuhe, zhi_xing


class RenTimingState(str, Enum):
    TIMING_READY = "timing-ready"
    INSUFFICIENT_TRIGGER = "insufficient-trigger"
    ABSTAIN = "abstain"
    UNSUPPORTED = "unsupported"


class PublicationState(str, Enum):
    EMIT = "emit"
    HOLD = "hold"
    ABSTAIN = "abstain"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class TriggerAtom:
    atom_id: str
    relation: str
    year: int
    liunian_ref: str
    target_ref: str
    target_kind: str
    left_branch: str
    right_branch: str
    rule_id: str
    source_ref: str
    priority: int
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class EvidenceFamily:
    family_key: str
    atoms: tuple[TriggerAtom, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"family_key": self.family_key, "atoms": [atom.to_dict() for atom in self.atoms]}


@dataclass(frozen=True)
class RenTimingResult:
    task_id: str
    event_id: str
    local_state: RenTimingState
    publication_state: PublicationState
    evidence_families: tuple[EvidenceFamily, ...] = ()
    selected_family_key: str = ""
    input_blockers: tuple[str, ...] = ()
    failed_gates: tuple[str, ...] = ()
    routing_blockers: tuple[str, ...] = ()
    diagnostic_reasons: tuple[str, ...] = ()
    remediation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "event_id": self.event_id,
            "local_state": self.local_state.value,
            "publication_state": self.publication_state.value,
            "evidence_families": [item.to_dict() for item in self.evidence_families],
            "selected_family_key": self.selected_family_key,
            "input_blockers": list(self.input_blockers),
            "failed_gates": list(self.failed_gates),
            "routing_blockers": list(self.routing_blockers),
            "diagnostic_reasons": list(self.diagnostic_reasons),
            "remediation": self.remediation,
        }


def _relation(left: str, right: str) -> str | None:
    if zhi_chong(left, right):
        return "冲"
    if zhi_xing(left, right) is not None:
        return "刑"
    if zhi_chuan(left, right):
        return "穿"
    if left == right:
        return "伏吟"
    if zhi_liuhe(left, right) is not None or frozenset((left, right)) == frozenset(("午", "未")):
        return "合"
    return None


def _atom_id(*parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return "ren-atom-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def _extract_atoms(chart: ChartFactLedger, rules: tuple[RenTimingRule, ...]) -> tuple[TriggerAtom, ...]:
    by_relation = {rule.relation: rule for rule in rules}
    atoms: dict[str, TriggerAtom] = {}
    for index, step in enumerate(chart.liunian_steps):
        year = step.get("year", step.get("年份"))
        ganzhi = str(step.get("ganzhi") or step.get("干支") or "")
        if type(year) is not int or len(ganzhi) < 2:
            continue
        left = ganzhi[1]
        targets = [("pillar", f"four_pillars.{name}", str(value)) for name, value in chart.four_pillars.items()]
        dayun = str(step.get("dayun") or step.get("大运") or "")
        if dayun:
            targets.append(("dayun", f"liunian_steps.{index}.dayun", dayun))
        for target_kind, target_ref, target in targets:
            if len(target) < 2:
                continue
            right = target[1]
            relation = _relation(left, right)
            rule = by_relation.get(relation or "")
            if rule is None:
                continue
            family_key = f"{year}:{relation}:{''.join(sorted((left, right)))}:{target_kind}"
            atom = TriggerAtom(
                atom_id=_atom_id(family_key, rule.rule_id), relation=relation, year=year,
                liunian_ref=f"liunian_steps.{index}", target_ref=target_ref,
                target_kind=target_kind, left_branch=left, right_branch=right,
                rule_id=rule.rule_id, source_ref=f"{rule.source_path}#{rule.source_anchor}",
                priority=rule.priority, confidence=rule.confidence,
            )
            atoms[atom.atom_id] = atom
    return tuple(sorted(atoms.values(), key=lambda a: (a.year, a.priority, a.atom_id)))


def _reduce_families(atoms: tuple[TriggerAtom, ...]) -> tuple[EvidenceFamily, ...]:
    grouped: dict[str, list[TriggerAtom]] = {}
    for atom in atoms:
        key = f"{atom.year}:{atom.relation}:{''.join(sorted((atom.left_branch, atom.right_branch)))}:{atom.target_kind}"
        grouped.setdefault(key, []).append(atom)
    return tuple(
        EvidenceFamily(key, tuple(sorted(grouped[key], key=lambda atom: atom.atom_id)))
        for key in sorted(grouped)
    )
```

- [ ] **Step 4: Add a minimal discriminator that returns extracted families**

```python
def discriminate_ren_career_timing(
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    event: EventHypothesis | None,
    *,
    task_id: str = "career.role_change",
) -> RenTimingResult:
    if task_id != "career.role_change":
        return RenTimingResult(task_id, event.event_id if event else "", RenTimingState.UNSUPPORTED, PublicationState.UNSUPPORTED)
    if event is None or event.event_type != "career.role_change" or not event.event_id:
        return RenTimingResult(
            task_id, event.event_id if event else "", RenTimingState.ABSTAIN, PublicationState.ABSTAIN,
            routing_blockers=("qualified_career_event_required",),
            remediation="提供已通过事件资格且可追踪的 career.role_change 事件。",
        )
    blockers = []
    if len(chart.four_pillars) != 4:
        blockers.append("complete_four_pillars_required")
    if not chart.dayun_steps:
        blockers.append("dayun_required")
    if not chart.liunian_steps:
        blockers.append("liunian_required")
    if blockers:
        return RenTimingResult(
            task_id, event.event_id, RenTimingState.ABSTAIN, PublicationState.ABSTAIN,
            input_blockers=tuple(blockers), remediation="补齐合法四柱、大运与候选流年事实。",
        )
    families = _reduce_families(_extract_atoms(chart, load_ren_timing_rules()))
    return RenTimingResult(
        task_id, event.event_id, RenTimingState.INSUFFICIENT_TRIGGER, PublicationState.HOLD,
        evidence_families=families, failed_gates=("timing_gate_not_evaluated",),
    )
```

- [ ] **Step 5: Run atom tests and commit**

Run: `pytest tests/ren_timing/test_discriminator.py -q`

Expected: atom/dedup/order tests PASS.

```bat
git add engine/decision/ren_career_timing.py tests/ren_timing/test_discriminator.py
git commit -m "feat: extract and deduplicate ren timing atoms"
```

---

### Task 5: Named Timing Gate and First Falsifier

**Files:**
- Modify: `engine/decision/ren_career_timing.py`
- Modify: `tests/ren_timing/test_discriminator.py`

**Interfaces:**
- Changes `discriminate_ren_career_timing()` from extraction-only hold to final local state.
- Named gate: `qualified_event AND complete_suiyun_context AND at_least_one_relation_family`.
- Selection order: lowest rule priority, then earliest year, then stable family key.

- [ ] **Step 1: Add failing state-machine tests**

```python
def test_valid_trigger_emits_one_selected_family(trigger_chart, trigger_features, career_event) -> None:
    result = discriminate_ren_career_timing(trigger_chart, trigger_features, career_event)
    assert result.local_state.value == "timing-ready"
    assert result.publication_state.value == "emit"
    assert result.selected_family_key
    assert result.failed_gates == ()


def test_first_falsifier_has_no_l5_eligible_result(no_trigger_chart, career_event) -> None:
    features = build_chart_feature_vector(no_trigger_chart)
    result = discriminate_ren_career_timing(no_trigger_chart, features, career_event)
    assert result.publication_state.value != "emit"
    assert result.selected_family_key == ""
    assert "relation_trigger_required" in result.failed_gates


def test_missing_context_abstains(partial_chart, career_event) -> None:
    features = build_chart_feature_vector(partial_chart)
    result = discriminate_ren_career_timing(partial_chart, features, career_event)
    assert result.local_state.value == "abstain"
    assert set(result.input_blockers) == {"dayun_required", "liunian_required"}
```

- [ ] **Step 2: Run focused tests and verify failure**

Run: `pytest tests/ren_timing/test_discriminator.py -q`

Expected: valid trigger and first-falsifier assertions FAIL against the extraction-only state.

- [ ] **Step 3: Replace the final return with named-gate evaluation**

```python
    families = _reduce_families(_extract_atoms(chart, load_ren_timing_rules()))
    if not families:
        return RenTimingResult(
            task_id, event.event_id, RenTimingState.ABSTAIN, PublicationState.ABSTAIN,
            failed_gates=("relation_trigger_required",),
            diagnostic_reasons=("候选岁运未形成任派冲、刑、穿、合或伏吟触发。",),
            remediation="补充后续候选流年；不得用默认大运窗口替代真实触发。",
        )
    selected = min(
        families,
        key=lambda family: (
            min(atom.priority for atom in family.atoms),
            min(atom.year for atom in family.atoms),
            family.family_key,
        ),
    )
    return RenTimingResult(
        task_id, event.event_id, RenTimingState.TIMING_READY, PublicationState.EMIT,
        evidence_families=families, selected_family_key=selected.family_key,
        diagnostic_reasons=("qualified_event", "complete_suiyun_context", "relation_trigger_present"),
    )
```

- [ ] **Step 4: Add a hold test for incomplete candidate evidence**

```python
def test_related_but_unusable_year_is_hold(trigger_chart, trigger_features, career_event) -> None:
    incomplete = replace(trigger_chart, liunian_steps=[{"ganzhi": "丙午", "dayun": "甲午"}])
    result = discriminate_ren_career_timing(incomplete, trigger_features, career_event)
    assert result.local_state.value == "insufficient-trigger"
    assert result.publication_state.value == "hold"
    assert result.selected_family_key == ""
```

Implement this case before the no-family abstain branch by detecting relation-bearing steps with a missing integer year and returning `INSUFFICIENT_TRIGGER/HOLD` with failed gate `trigger_year_required`.

- [ ] **Step 5: Run full discriminator tests and commit**

Run: `pytest tests/ren_timing/test_discriminator.py -q`

Expected: all tests PASS.

```bat
git add engine/decision/ren_career_timing.py tests/ren_timing/test_discriminator.py
git commit -m "feat: gate ren career timing publication"
```

---

### Task 6: Emit-Only L5 Adapter and Resolvable Evidence

**Files:**
- Create: `engine/decision/ren_career_timing_slice.py`
- Create: `tests/ren_timing/test_adapter.py`

**Interfaces:**
- Produces: `to_ren_timing_probability(case_id, result) -> TimingProbability`.
- Does not call `build_timing_probabilities()`.

- [ ] **Step 1: Write failing adapter tests**

```python
import pytest

from engine.decision.ren_career_timing import discriminate_ren_career_timing
from engine.decision.ren_career_timing_slice import to_ren_timing_probability


def test_emit_result_builds_real_annual_window(trigger_chart, trigger_features, career_event) -> None:
    result = discriminate_ren_career_timing(trigger_chart, trigger_features, career_event)
    timing = to_ren_timing_probability("C-REN-TIMING-001", result)
    assert timing.event_id == career_event.event_id
    assert timing.time_window["label"] == "annual"
    assert timing.time_window["start_year"] == timing.time_window["end_year"]
    assert "MVP 默认时间窗" not in str(timing.to_dict())
    assert all("#" in ref or ref.startswith(("four_pillars.", "liunian_steps.")) for ref in timing.trigger_conditions)


@pytest.mark.parametrize("fixture_name", ["no_trigger_chart", "partial_chart"])
def test_non_emit_result_fails_closed(request, fixture_name, career_event) -> None:
    chart = request.getfixturevalue(fixture_name)
    result = discriminate_ren_career_timing(chart, build_chart_feature_vector(chart), career_event)
    with pytest.raises(ValueError, match="emit publication state required"):
        to_ren_timing_probability("C-REN-TIMING-001", result)
```

- [ ] **Step 2: Run tests and verify import failure**

Run: `pytest tests/ren_timing/test_adapter.py -q`

Expected: FAIL because the staged adapter does not exist.

- [ ] **Step 3: Implement stable emit-only adapter**

```python
from __future__ import annotations

import hashlib

from engine.decision.models import TimingProbability
from engine.decision.ren_career_timing import PublicationState, RenTimingResult


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:20]}"


def to_ren_timing_probability(case_id: str, result: RenTimingResult) -> TimingProbability:
    if result.publication_state is not PublicationState.EMIT:
        raise ValueError("emit publication state required for Ren L5 adapter")
    selected = next(
        (family for family in result.evidence_families if family.family_key == result.selected_family_key),
        None,
    )
    if selected is None or not selected.atoms:
        raise ValueError("selected evidence family is required")
    atom = min(selected.atoms, key=lambda item: (item.priority, item.year, item.atom_id))
    if atom.year < 1900 or atom.year > 2100:
        raise ValueError("Ren timing year outside supported staged range")
    refs = sorted({atom.liunian_ref, atom.target_ref, atom.source_ref})
    return TimingProbability(
        prediction_id=_stable_id("ren-timing", case_id, result.event_id, atom.year, atom.rule_id),
        event_id=result.event_id,
        time_window={"start_year": atom.year, "end_year": atom.year, "label": "annual"},
        trigger_conditions=refs,
        probability_range=(max(0.0, atom.confidence - 0.1), min(1.0, atom.confidence + 0.1)),
        confidence=atom.confidence,
        falsifier=f"若 {atom.year} 年未发生可核验的显著职业角色或岗位变化，则该任派应期命题证伪。",
    )
```

- [ ] **Step 4: Run adapter and discriminator suites**

Run: `pytest tests/ren_timing/test_adapter.py tests/ren_timing/test_discriminator.py -q`

Expected: all tests PASS and no output contains `MVP 默认时间窗`.

- [ ] **Step 5: Commit**

```bat
git add engine/decision/ren_career_timing_slice.py tests/ren_timing/test_adapter.py
git commit -m "feat: adapt emitted ren trigger to staged L5 timing"
```

---

### Task 7: Staged Assembly and Deterministic Freeze Projection

**Files:**
- Modify: `engine/decision/ren_career_timing_slice.py`
- Modify: `tests/ren_timing/test_staged_slice.py`

**Interfaces:**
- Produces: `build_ren_career_timing_slice(case_id, chart, features, event, *, task_id="career.role_change") -> tuple[RenTimingResult, tuple[TimingProbability, ...]]`.
- Produces: `to_blind_output(case_id, result, timings) -> BlindSchoolOutput` for existing `freeze_outputs()`.

- [ ] **Step 1: Write failing staged assembly tests**

```python
from dataclasses import replace

from engine.decision.ren_career_timing_slice import build_ren_career_timing_slice, to_blind_output
from engine.evaluation.freeze import canonical_json, freeze_outputs, verify_frozen_run


def test_first_falsifier_produces_zero_l5(no_trigger_chart, career_event) -> None:
    result, timings = build_ren_career_timing_slice(
        "C-REN-NO-TRIGGER", no_trigger_chart, build_chart_feature_vector(no_trigger_chart), career_event
    )
    assert result.publication_state.value != "emit"
    assert timings == ()


def test_staged_freeze_is_byte_stable(trigger_chart, trigger_features, career_event) -> None:
    result, timings = build_ren_career_timing_slice(
        "C-REN-TIMING-001", trigger_chart, trigger_features, career_event
    )
    output = to_blind_output("C-REN-TIMING-001", result, timings)
    first = freeze_outputs([output], "prospective-go-task-catalog/v1", "ren-career-timing-rules/v1")
    second = freeze_outputs([output], "prospective-go-task-catalog/v1", "ren-career-timing-rules/v1")
    verify_frozen_run(first)
    assert canonical_json(first.to_dict()) == canonical_json(second.to_dict())
```

- [ ] **Step 2: Run tests and verify missing assembly functions**

Run: `pytest tests/ren_timing/test_staged_slice.py -q`

Expected: FAIL because staged assembly functions are absent.

- [ ] **Step 3: Implement staged assembly**

```python
from engine.decision.models import ChartFactLedger, EventHypothesis
from engine.evaluation.models import BlindPrediction, BlindSchoolOutput
from engine.features import ChartFeatureVector


def build_ren_career_timing_slice(
    case_id: str,
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    event: EventHypothesis | None,
    *,
    task_id: str = "career.role_change",
) -> tuple[RenTimingResult, tuple[TimingProbability, ...]]:
    result = discriminate_ren_career_timing(chart, features, event, task_id=task_id)
    if result.publication_state is not PublicationState.EMIT:
        return result, ()
    return result, (to_ren_timing_probability(case_id, result),)


def to_blind_output(
    case_id: str,
    result: RenTimingResult,
    timings: tuple[TimingProbability, ...],
) -> BlindSchoolOutput:
    state = "claim" if timings else ("unsupported" if result.publication_state is PublicationState.UNSUPPORTED else "abstain")
    predictions = [
        BlindPrediction(
            prediction_id=item.prediction_id,
            event_label="career.role_change",
            probability=item.confidence,
            time_window=dict(item.time_window),
            evidence_refs=[ref for ref in item.trigger_conditions if "#" in ref],
            fact_refs=[ref for ref in item.trigger_conditions if "#" not in ref],
            falsifier=item.falsifier,
        )
        for item in timings
    ]
    reasons = (*result.input_blockers, *result.failed_gates, *result.routing_blockers)
    rationale = (
        "任派真实岁运触发形成职业角色变化应期窗口。"
        if predictions
        else "; ".join(reasons) or "任派切片未形成可发布应期。"
    )
    return BlindSchoolOutput(
        case_id=case_id,
        task_id=result.task_id,
        school_id="ren",
        state=state,
        rationale=rationale,
        predictions=predictions,
        counter_evidence=list(result.failed_gates),
    )
```

This mapping uses the existing immutable constructors exactly: `BlindPrediction(prediction_id, event_label, probability, time_window, evidence_refs, falsifier, fact_refs)` and `BlindSchoolOutput(case_id, school_id, task_id, state, rationale, predictions, counter_evidence)`. Do not modify those shared models.

- [ ] **Step 4: Add ordering permutation and duplicate-event tests**

```python
def test_liunian_permutation_keeps_frozen_output(trigger_chart, trigger_features, career_event) -> None:
    reversed_chart = replace(trigger_chart, liunian_steps=list(reversed(trigger_chart.liunian_steps)))
    left = build_ren_career_timing_slice("C-REN-PERMUTE", trigger_chart, trigger_features, career_event)
    right = build_ren_career_timing_slice("C-REN-PERMUTE", reversed_chart, trigger_features, career_event)
    assert left[0].to_dict() == right[0].to_dict()
    assert [item.to_dict() for item in left[1]] == [item.to_dict() for item in right[1]]
```

- [ ] **Step 5: Run staged, adapter, discriminator, and freeze tests**

Run: `pytest tests/ren_timing tests/evaluation/test_prospective_frozen_run.py -q`

Expected: all tests PASS; first falsifier has zero L5; frozen output verifies.

- [ ] **Step 6: Commit**

```bat
git add engine/decision/ren_career_timing_slice.py tests/ren_timing/test_staged_slice.py
git commit -m "feat: freeze staged ren career timing slice"
```

---

### Task 8: Final Integration Ownership, Status, and Shared Guards

**Files:**
- Modify: `theory/executable-slices-v1.yaml`
- Modify: `tests/test_production_entrypoints_unchanged.py`
- Modify: `META/project-state.json`
- Modify: `tests/test_project_metadata.py`
- Modify: `tools/README.md`

**Interfaces:**
- Adds manifest record `REN-CAREER-ROLE-CHANGE-TIMING-V1` with status `staged_verified` only after Tasks 1-7 pass.
- Adds project-state key `ren_career_role_change_timing_slice: staged_verified_production_unchanged`.

- [ ] **Step 1: Fetch and verify no Yang-owned path changed in this branch**

Run:

```bat
git fetch --prune origin
git diff --name-only origin/main...HEAD -- engine/decision/yang_marriage.py engine/decision/yang_marriage_slice.py tests/yang_marriage
```

Expected: no output. If output exists, stop and resolve ownership rather than merging automatically.

- [ ] **Step 2: Add the staged manifest record**

```yaml
  - slice_id: REN-CAREER-ROLE-CHANGE-TIMING-V1
    school_id: ren
    task_id: career.role_change
    target_layer: L5
    status: staged_verified
    artifacts:
      - theory/production/ren-career-timing-rules-v1.yaml
      - engine/decision/ren_timing_rules.py
      - engine/decision/ren_career_timing.py
      - engine/decision/ren_career_timing_slice.py
      - tests/ren_timing/test_staged_slice.py
```

- [ ] **Step 3: Write failing metadata and production-isolation assertions**

Add to `tests/test_project_metadata.py`:

```python
def test_ren_career_timing_slice_is_staged_not_production() -> None:
    state = json.loads(Path("META/project-state.json").read_text(encoding="utf-8"))
    assert state["intelligence_platform_status"]["ren_career_role_change_timing_slice"] == (
        "staged_verified_production_unchanged"
    )
```

Add to `tests/test_production_entrypoints_unchanged.py`:

```python
def test_ren_staged_slice_does_not_modify_production_claim_rules() -> None:
    assert _sha256(Path("theory/production/claim-rules-v1.yaml")) == (
        "6396883d8db0b8d24c6c15435c130c6f9ae045c8c6d1fe8d2a84748c5b0bebef"
    )
```

The literal is the verified `origin/main` production-rule artifact digest at design time. If upstream intentionally changes that production artifact before execution, stop for integration review instead of silently refreshing the guard.

- [ ] **Step 4: Run tests and verify metadata failure**

Run: `pytest tests/test_project_metadata.py tests/test_production_entrypoints_unchanged.py -q`

Expected: metadata test FAILS because the staged state key is absent; production hashes pass after inserting the literal digest.

- [ ] **Step 5: Add the exact staged state**

Insert into `META/project-state.json` under `intelligence_platform_status`:

```json
"ren_career_role_change_timing_slice": "staged_verified_production_unchanged"
```

Do not add `production_active`, `GO`, accuracy, or default-registry claims.

- [ ] **Step 6: Document the read-only metric and staged boundary**

Add this row to the active tools table in `tools/README.md`:

```markdown
| `theory_slice_status.py` | 分账扫描理论目录条目与可执行切片清单 | 只读输出 `catalog_count` / `executable_slice_count`；不更新规则生命周期、生产 registry 或权重 |
```

Add a short boundary paragraph:

```markdown
任派职业角色变化应期切片当前仅为 staged 专用入口：它消费已成立的职业变化事件，使用真实岁运触发生成可证伪 L5 窗口；未注册到默认 runner registry，也不替换正式 pipeline 或报告入口。
```

- [ ] **Step 7: Run all focused and shared gates**

Run:

```bat
pytest tests/ren_timing tests/tools/test_theory_slice_status.py tests/test_project_metadata.py tests/test_production_entrypoints_unchanged.py tests/claims/test_multi_school_freeze.py -q
python -m tools.theory_slice_status --format json
python tools/tool_registry.py --check
python tools/rule_status_scan.py --check
git diff --check
```

Expected: every command exits 0; the scanner reports Ren `executable_slice_count` increased by exactly one; default registry digest remains unchanged.

- [ ] **Step 8: Commit shared integration changes**

```bat
git add theory/executable-slices-v1.yaml tests/test_production_entrypoints_unchanged.py META/project-state.json tests/test_project_metadata.py tools/README.md
git commit -m "docs: register staged ren career timing slice"
```

---

### Task 9: G0-G5 Evidence Pack and Final Verification

**Files:**
- Create: `reports/ren-career-timing-slice-g0-g5-verification.md`

**Interfaces:**
- Produces a human-readable staged evidence pack; it must not claim G6 or production GO.

- [ ] **Step 1: Run the complete verification suite and capture exact results**

Run:

```bat
pytest tests/ren_timing tests/tools/test_theory_slice_status.py tests/test_project_metadata.py tests/test_production_entrypoints_unchanged.py tests/claims/test_multi_school_freeze.py tests/claims/test_school_strength_runners.py -q
pytest tests/ -q
python -m tools.theory_slice_status --format json
git status --short --branch
git diff origin/main...HEAD --name-only
```

Expected: focused and full suites exit 0. If the full suite has unrelated pre-existing failures, record exact failing node IDs and demonstrate that focused gates pass; do not write “all tests pass.”

- [ ] **Step 2: Write the evidence pack with actual command output values**

```markdown
# 任派职业变化应期切片 G0-G5 验证

## 结论

状态：staged_verified_production_unchanged。该结论只证明规格、判别、适配、冻结与生产隔离门通过，不代表 G6、准确率提升或生产 GO。

## G0 规格门

- 任务：career.role_change 的应期，不重新判断事件资格。
- 首个证伪点：事件成立但无有效岁运触发时，L5 数量为 0。

## G1-G4 行为门

- 原子触发：冲、刑、穿、合、伏吟及大运上下文。
- 同源家族去重与输入顺序确定性：通过。
- 非 emit 适配 fail-closed：通过。
- 真实年度窗口与可解析证据：通过。

## G5 冻结与隔离门

- 冻结 hash 验证：通过。
- 默认 runner registry：未变化。
- 正式 pipeline 签名：未变化。
- production claim rules：未变化。
- 报告入口与公共 schema：未变化。
- 杨派专属写区：未变化。

## 测试证据

记录实际通过数、失败数、耗时和完整命令。不得填写推测数字。

## G6 状态

未进入。需要独立冻结样本上的误报、漏报、校准与适用性后验，并需另行审批。
```

Replace only the “记录实际通过数” sentence with the exact observed results. Do not add mutable HEAD or current rule counts.

- [ ] **Step 3: Check the evidence pack for forbidden claims**

Run:

```bat
python -c "from pathlib import Path; s=Path('reports/ren-career-timing-slice-g0-g5-verification.md').read_text(encoding='utf-8'); forbidden=('生产 GO','准确率提升已证实','production_active'); assert not any(x in s for x in forbidden); assert '未进入' in s and 'staged_verified_production_unchanged' in s"
git diff --check
```

Expected: exit 0.

- [ ] **Step 4: Commit evidence pack**

```bat
git add reports/ren-career-timing-slice-g0-g5-verification.md
git commit -m "test: document ren timing slice g0-g5 evidence"
```

- [ ] **Step 5: Final repository verification**

Run:

```bat
git status --short --branch
git log -8 --oneline
```

Expected: clean worktree; commits appear in task order. Push or merge only after confirming the Yang agent has not claimed overlapping shared files.

---

## Execution Order and Review Gates

1. Tasks 1-2 may run independently if they use separate worktrees; Task 2 owns only metrics files.
2. Tasks 3-7 are sequential because each consumes the preceding Ren interface.
3. Task 8 is single-owner integration and must wait for the Yang agent's current branch status.
4. Task 9 runs only after G0-G5 focused gates pass.
5. Stop immediately on any default registry, production YAML, public schema, report entrypoint, or Yang-path diff.

## Production Promotion Explicitly Deferred

This plan ends at `staged_verified_production_unchanged`. A later G6 plan must define independent frozen samples, labels, TP/FP/FN metrics, calibration limits, high-risk review requirements, rollback, and one explicit choice among dedicated-only, staged-parallel, or production replacement. No task in this plan may make that choice implicitly.
