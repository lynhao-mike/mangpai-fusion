from __future__ import annotations

import ast
import hashlib
import inspect
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import date, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable

import pytest

from engine.asof.session_contract import (
    BLIND_INPUT_SCHEMA_VERSION,
    SESSION_SCHEMA_VERSION,
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
    TWELVE_GROWTH_PHASES,
    BlindChartInput,
    ChartGender,
    ChartSource,
    ConsultationState,
    DaiyunInput,
    FourPillarsInput,
    PillarInput,
    PillarName,
    SessionContractError,
    SessionEnvelope,
    SessionIdentity,
    blind_chart_input_from_mapping,
    blind_input_to_canonical_bytes,
    compute_blind_input_sha256,
    create_initial_envelope,
    transition_session,
    verify_envelope_hash,
)


EXPECTED_CANONICAL_BYTES = (
    '{"chart_source":"wenzhen_structured_v1","daiyun":[{"branch":"卯","end_date":"2010-01-01","sequence":1,"start_date":"2000-01-01","stem":"己"},{"branch":"辰","end_date":"2020-01-01","sequence":2,"start_date":"2010-01-01","stem":"庚"}],"gender":"乾","pillars":{"day":{"branch":"子","changsheng":"帝旺","hidden_stems":["癸"],"stem":"壬"},"hour":{"branch":"丑","changsheng":"衰","hidden_stems":["己","癸","辛"],"stem":"辛"},"month":{"branch":"寅","changsheng":"病","hidden_stems":["甲","丙","戊"],"stem":"戊"},"year":{"branch":"申","changsheng":"长生","hidden_stems":["庚","壬","戊"],"stem":"庚"}},"schema_version":"asof-blind-input/v1"}'
).encode("utf-8")
EXPECTED_DIGEST = "f1970e3295423eb1eeda6bc94a4d098a225b98b549be1a88073875c6871cf606"


def _valid_mapping() -> dict[str, Any]:
    return {
        "schema_version": "asof-blind-input/v1",
        "chart_source": "wenzhen_structured_v1",
        "gender": "乾",
        "pillars": {
            "year": {"stem": "庚", "branch": "申", "hidden_stems": ["庚", "壬", "戊"], "changsheng": "长生"},
            "month": {"stem": "戊", "branch": "寅", "hidden_stems": ["甲", "丙", "戊"], "changsheng": "病"},
            "day": {"stem": "壬", "branch": "子", "hidden_stems": ["癸"], "changsheng": "帝旺"},
            "hour": {"stem": "辛", "branch": "丑", "hidden_stems": ["己", "癸", "辛"], "changsheng": "衰"},
        },
        "daiyun": [
            {"sequence": 1, "stem": "己", "branch": "卯", "start_date": "2000-01-01", "end_date": "2010-01-01"},
            {"sequence": 2, "stem": "庚", "branch": "辰", "start_date": "2010-01-01", "end_date": "2020-01-01"},
        ],
    }


def _identity(**changes: Any) -> SessionIdentity:
    values = {
        "schema_version": SESSION_SCHEMA_VERSION,
        "case_id": "C-2026-001-乾-庚申戊寅壬子辛丑",
        "as_of_date": date(2020, 1, 1),
        "session_id": "S-20260727T120000Z-0123abcd",
    }
    values.update(changes)
    return SessionIdentity(**values)


def _pillar(**changes: Any) -> PillarInput:
    values = {"stem": "庚", "branch": "申", "hidden_stems": ("庚", "壬", "戊"), "changsheng": "长生"}
    values.update(changes)
    return PillarInput(**values)


def _daiyun(**changes: Any) -> DaiyunInput:
    values = {"sequence": 1, "stem": "己", "branch": "卯", "start_date": date(2000, 1, 1), "end_date": date(2010, 1, 1)}
    values.update(changes)
    return DaiyunInput(**values)


def _assert_error(code: str, operation: Callable[[], Any]) -> None:
    with pytest.raises(SessionContractError) as caught:
        operation()
    assert caught.value.code == code


def _unknown_top(payload: dict[str, Any]) -> None:
    payload["leak"] = "secret"


def _unknown_pillars(payload: dict[str, Any]) -> None:
    payload["pillars"]["leak"] = {}


def _unknown_year(payload: dict[str, Any]) -> None:
    payload["pillars"]["year"]["leak"] = "secret"


def _unknown_daiyun(payload: dict[str, Any]) -> None:
    payload["daiyun"][0]["leak"] = "secret"


def _non_string_key(payload: dict[str, Any]) -> None:
    payload["pillars"]["year"][1] = "secret"


UNKNOWN_MUTATIONS = (_unknown_top, _unknown_pillars, _unknown_year, _unknown_daiyun, _non_string_key)


STATE_VALUES = tuple(ConsultationState)
FORWARD_EDGES = tuple(zip(STATE_VALUES, STATE_VALUES[1:]))
INVALID_EDGES = tuple((left, right) for left in STATE_VALUES for right in STATE_VALUES if (left, right) not in FORWARD_EDGES)


PROTECTED_BASELINE = {
    "engine/application/pipeline_runner.py": "b60c3e768b42f77fd108ad04cbc3e3cbc81018533309e67ffd942a5d80358dd4",
    "engine/claims/runner_registry.py": "42289b1c91a41d87c78a1d1e034e25749d816137156190f4cf66dc6c86de1431",
    "engine/expert-weights.yaml": "d8c8a90df1fe625a952ecc67ee6925812e28dbfe7200f4dbfc9f091d2e0fabae",
    "engine/application/weight_profile_service.py": "4b58c81c27fcccb194944ca5262c32b8e406f1975bbdd7220578c985a9d0db02",
    "engine/evaluation/prospective_gates.py": "25b5956f466e2174d848e5ac6106daa7e18b4124fff4dc09d59d97c8347c8920",
    "tools/as_of_integration.py": "d25da17093e2bed21ca6b8901dc0843897312da3417b9e390e756a5b796af02e",
    "tools/production_as_of_cli.py": "7f68331a7c824682942bcac4604999fbb3db6d64a05428a2c70a90790cb74d44",
    "tools/preflight.py": "5bfd78bf916d8d2c02f28ac69923f870b434f7efa8a36b550a9c17e759dc82b2",
    "tools/feedback_ingest.py": "82f30900d29b3b65c8fb0649d9a5b8e8fb38614b319e093af0fb77efb2ccb59a",
    "tools/promote_expert_weight_feedback.py": "94d43e78f25dffd17ce5bffd48f533a67166de97a51a7707f13890a9328ce012",
    "tools/rule_status_scan.py": "018ea259340df4bd9c71182d99c5e97c4bb157db301ecde8d26a1fa573359c4d",
    "META/iteration-state.json": "4a59b75250620f7772e01f045e3afecbd79272a10fa5d79ba3fbbc39a0b44a61",
    "theory/production/claim-rules-v1.yaml": "6396883d8db0b8d24c6c15435c130c6f9ae045c8c6d1fe8d2a84748c5b0bebef",
    "engine/asof/__init__.py": "e823e161de220edd62978ef6fb445d2fd39f4f064408002ae1d38fb3ed09ed3a",
}


def test_valid_mapping_builds_closed_immutable_model() -> None:
    assert issubclass(ConsultationState, str)
    assert issubclass(ChartSource, str)
    assert issubclass(ChartGender, str)
    assert issubclass(PillarName, str)
    assert tuple(member.name for member in ConsultationState) == (
        "STRICT_BLIND_INPUT",
        "BLIND_DRAFTED",
        "FROZEN",
        "VERIFICATION_OPEN",
        "ADJUDICATED",
        "STATE_BUILT",
        "PROJECTED",
        "ARCHIVED",
    )
    assert tuple(member.value for member in ConsultationState) == tuple(member.name for member in ConsultationState)
    model = blind_chart_input_from_mapping(_valid_mapping())
    assert is_dataclass(model) and type(model) is BlindChartInput
    assert model.schema_version == BLIND_INPUT_SCHEMA_VERSION
    assert model.chart_source is ChartSource.WENZHEN_STRUCTURED_V1
    assert model.gender is ChartGender.QIAN
    assert type(model.pillars) is FourPillarsInput
    assert model.pillars.year.stem in HEAVENLY_STEMS
    assert model.pillars.year.branch in EARTHLY_BRANCHES
    assert model.pillars.year.changsheng in TWELVE_GROWTH_PHASES
    assert PillarName.YEAR.value == "year"
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        model.gender = ChartGender.KUN


def test_canonical_bytes_and_sha256_match_literal_oracle() -> None:
    model = blind_chart_input_from_mapping(_valid_mapping())
    assert len(EXPECTED_CANONICAL_BYTES) == 661
    assert hashlib.sha256(EXPECTED_CANONICAL_BYTES).hexdigest() == EXPECTED_DIGEST
    assert blind_input_to_canonical_bytes(model) == EXPECTED_CANONICAL_BYTES
    assert compute_blind_input_sha256(model) == EXPECTED_DIGEST


@pytest.mark.parametrize("mutate", UNKNOWN_MUTATIONS)
def test_recursive_allowlist_rejects_unknown_keys(mutate: Callable[[dict[str, Any]], None]) -> None:
    payload = _valid_mapping()
    mutate(payload)
    _assert_error("UNKNOWN_FIELD", lambda: blind_chart_input_from_mapping(payload))


@pytest.mark.parametrize(
    ("operation", "code"),
    (
        (lambda: blind_chart_input_from_mapping({**_valid_mapping(), "known_facts": []}), "UNKNOWN_FIELD"),
        (lambda: blind_chart_input_from_mapping({**_valid_mapping(), "questions": []}), "UNKNOWN_FIELD"),
        (lambda: blind_chart_input_from_mapping({**_valid_mapping(), "chart_source": "resume:CEO"}), "INVALID_VALUE"),
        (lambda: blind_chart_input_from_mapping({**_valid_mapping(), "gender": "男"}), "INVALID_VALUE"),
        (lambda: _identity(case_id="C-2026-001-乾-庚申戊寅壬子辛丑\n"), "INVALID_VALUE"),
        (lambda: _identity(session_id="S-20260727T120000Z-0123abcd\n"), "INVALID_VALUE"),
        (lambda: blind_chart_input_from_mapping({**_valid_mapping(), "daiyun": [{**_valid_mapping()["daiyun"][0], "sequence": True}, _valid_mapping()["daiyun"][1]]}), "INVALID_TYPE"),
        (lambda: blind_chart_input_from_mapping({**_valid_mapping(), "pillars": {**_valid_mapping()["pillars"], "year": {**_valid_mapping()["pillars"]["year"], "hidden_stems": ("庚", "壬", "戊")}}}), "INVALID_TYPE"),
    ),
)
def test_gateway_rejects_leakage_values_identifiers_and_scalar_types(operation: Callable[[], Any], code: str) -> None:
    _assert_error(code, operation)
    sequence_before_date = _valid_mapping()
    sequence_before_date["daiyun"][0]["sequence"] = True
    sequence_before_date["daiyun"][0]["start_date"] = object()
    _assert_error("INVALID_TYPE", lambda: blind_chart_input_from_mapping(sequence_before_date))
    stem_before_date = _valid_mapping()
    stem_before_date["daiyun"][0]["stem"] = "not-a-stem"
    stem_before_date["daiyun"][0]["end_date"] = object()
    _assert_error("INVALID_VALUE", lambda: blind_chart_input_from_mapping(stem_before_date))
    pillar_stem_before_hidden = _valid_mapping()
    pillar_stem_before_hidden["pillars"]["year"]["stem"] = "not-a-stem"
    pillar_stem_before_hidden["pillars"]["year"]["hidden_stems"] = object()
    _assert_error("INVALID_VALUE", lambda: blind_chart_input_from_mapping(pillar_stem_before_hidden))
    pillar_branch_before_hidden = _valid_mapping()
    pillar_branch_before_hidden["pillars"]["year"]["branch"] = "not-a-branch"
    pillar_branch_before_hidden["pillars"]["year"]["hidden_stems"] = object()
    _assert_error("INVALID_VALUE", lambda: blind_chart_input_from_mapping(pillar_branch_before_hidden))


@pytest.mark.parametrize(
    ("operation", "code"),
    (
        (lambda: _pillar(hidden_stems=["庚", "壬", "戊"]), "INVALID_TYPE"),
        (lambda: _pillar(hidden_stems=("甲", "甲")), "INVALID_VALUE"),
        (lambda: _daiyun(sequence=True), "INVALID_TYPE"),
        (lambda: _daiyun(start_date=datetime(2000, 1, 1)), "INVALID_TYPE"),
        (lambda: _daiyun(end_date=date(2000, 1, 1)), "INVALID_VALUE"),
        (lambda: replace(blind_chart_input_from_mapping(_valid_mapping()), daiyun=()), "INVALID_VALUE"),
        (lambda: replace(blind_chart_input_from_mapping(_valid_mapping()), daiyun=(_daiyun(), _daiyun(sequence=3, stem="庚", branch="辰", start_date=date(2010, 1, 1), end_date=date(2020, 1, 1)))), "INVALID_VALUE"),
        (lambda: replace(blind_chart_input_from_mapping(_valid_mapping()), daiyun=(_daiyun(end_date=date(2009, 12, 31)), _daiyun(sequence=2, stem="庚", branch="辰", start_date=date(2010, 1, 1), end_date=date(2020, 1, 1)))), "INVALID_VALUE"),
    ),
)
def test_nested_models_reject_invalid_values_and_cross_field_invariants(operation: Callable[[], Any], code: str) -> None:
    _assert_error(code, operation)
    _assert_error(
        "INVALID_VALUE",
        lambda: PillarInput("not-a-stem", "not-a-branch", ("甲",), "not-a-phase"),
    )
    _assert_error(
        "SCHEMA_MISMATCH",
        lambda: BlindChartInput(
            "wrong-schema",
            ChartSource.WENZHEN_STRUCTURED_V1,
            ChartGender.QIAN,
            blind_chart_input_from_mapping(_valid_mapping()).pillars,
            blind_chart_input_from_mapping(_valid_mapping()).daiyun,
        ),
    )


def test_initial_factory_uses_explicit_identity_and_computed_hash() -> None:
    chart = blind_chart_input_from_mapping(_valid_mapping())
    identity = _identity()
    envelope = create_initial_envelope(identity, chart)
    assert envelope.identity == identity
    assert envelope.blind_input_sha256 == compute_blind_input_sha256(chart)
    assert envelope.state is ConsultationState.STRICT_BLIND_INPUT
    assert "state" not in inspect.signature(create_initial_envelope).parameters
    bad_identity = _identity(case_id="C-2026-001-坤-庚申戊寅壬子辛丑")
    _assert_error("INVALID_VALUE", lambda: create_initial_envelope(bad_identity, chart))


@pytest.mark.parametrize("matches", (True, False))
def test_envelope_hash_validation_is_fail_closed(matches: bool) -> None:
    chart = blind_chart_input_from_mapping(_valid_mapping())
    envelope = create_initial_envelope(_identity(), chart)
    candidate = envelope if matches else replace(envelope, blind_input_sha256="0" * 64)
    if matches:
        assert verify_envelope_hash(candidate, chart) is None
    else:
        _assert_error("HASH_MISMATCH", lambda: verify_envelope_hash(candidate, chart))


@pytest.mark.parametrize(("source", "target"), FORWARD_EDGES)
def test_all_and_only_forward_adjacent_transitions_succeed(source: ConsultationState, target: ConsultationState) -> None:
    envelope = replace(create_initial_envelope(_identity(), blind_chart_input_from_mapping(_valid_mapping())), state=source)
    transitioned = transition_session(envelope, target)
    assert transitioned.state is target
    assert envelope.state is source


@pytest.mark.parametrize(("source", "target"), INVALID_EDGES)
def test_non_adjacent_same_backward_and_archived_transitions_fail(source: ConsultationState, target: ConsultationState) -> None:
    envelope = replace(create_initial_envelope(_identity(), blind_chart_input_from_mapping(_valid_mapping())), state=source)
    _assert_error("INVALID_TRANSITION", lambda: transition_session(envelope, target))


def test_models_and_transition_are_immutable_and_deterministic() -> None:
    chart = blind_chart_input_from_mapping(_valid_mapping())
    identity = _identity()
    envelope = create_initial_envelope(identity, chart)
    models = (
        chart.pillars.year,
        chart.pillars,
        chart.daiyun[0],
        chart,
        identity,
        envelope,
    )
    for model in models:
        field_name = next(iter(model.__dataclass_fields__))
        with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
            setattr(model, field_name, getattr(model, field_name))
    first_target = STATE_VALUES[1]
    left = transition_session(envelope, first_target)
    right = transition_session(envelope, first_target)
    assert left == right and left is not right
    assert envelope.state is ConsultationState.STRICT_BLIND_INPUT
    assert blind_input_to_canonical_bytes(chart) == blind_input_to_canonical_bytes(chart)


def test_session_contract_has_no_tools_pipeline_runner_registry_reports_or_io_imports() -> None:
    tree = ast.parse(Path("engine/asof/session_contract.py").read_text(encoding="utf-8"))
    forbidden_prefixes = ("tools", "engine.application", "engine.claims", "engine.reports")
    forbidden_top_level = {"pathlib", "io", "os", "random", "uuid", "time"}
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    assert not [name for name in imports if name.startswith(forbidden_prefixes) or name.split(".")[0] in forbidden_top_level]
    forbidden_calls = {"open", "exec", "eval", "compile", "__import__"}
    assert not [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in forbidden_calls]


def test_protected_workspace_bytes_match_contract_baseline() -> None:
    actual = {path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in PROTECTED_BASELINE}
    assert actual == PROTECTED_BASELINE
