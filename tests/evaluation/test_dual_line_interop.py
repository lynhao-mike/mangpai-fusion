from __future__ import annotations

from importlib.util import find_spec
from types import SimpleNamespace

import pytest


CASE_ID = "SYNTHETIC-INTEROP-001"


def test_controlled_dual_line_interop_module_is_available() -> None:
    """Phase 3 exposes an evaluation-only entry, separate from production runners."""
    assert find_spec("engine.evaluation.dual_line_interop") is not None


def test_direction_mismatch_is_preserved_as_human_adjudication_blocker() -> None:
    from engine.evaluation.dual_line_interop import (
        FieldDifference,
        build_diff_report,
    )

    report = build_diff_report(
        case_id=CASE_ID,
        input_sha256="a" * 64,
        differences=[
            FieldDifference(
                statement_key="career:claim-1",
                field_path="direction",
                compatibility_value="positive",
                v5_value="negative",
            )
        ],
    )

    difference = report.differences[0]
    assert difference.classification == "human_adjudication_blocker"
    assert difference.compatibility_value == "positive"
    assert difference.v5_value == "negative"
    assert report.adjudication_blockers == [difference]


def test_blind_compatibility_input_drops_known_facts_and_sensitive_metadata() -> None:
    from engine.evaluation.dual_line_interop import blind_compatibility_input

    original = SimpleNamespace(
        case_id=CASE_ID,
        bazi={"年柱": "甲子", "月柱": "乙丑", "日柱": "丙寅", "时柱": "丁卯"},
        known_facts=[{"event": "synthetic revealed result"}],
        questions=["synthetic future question"],
        birth={"性别": "女", "公历": "2000-01-01 12:00"},
        case_meta={
            "来源": "问真",
            "排盘验证状态": "validated",
            "feedback": "synthetic revealed outcome",
        },
    )

    blind = blind_compatibility_input(original)

    assert blind is not original
    assert blind.known_facts == []
    assert blind.questions == []
    assert blind.case_meta == {"来源": "问真", "排盘验证状态": "validated"}
    assert original.known_facts == [{"event": "synthetic revealed result"}]
    assert original.questions == ["synthetic future question"]
    assert original.case_meta["feedback"] == "synthetic revealed outcome"


def test_input_hash_is_stable_and_includes_explicit_blind_chart_fields() -> None:
    from engine.evaluation.dual_line_interop import blind_input_sha256

    left = {"case_id": CASE_ID, "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]}
    right = {"pillars": ["甲子", "乙丑", "丙寅", "丁卯"], "case_id": CASE_ID}

    assert blind_input_sha256(left) == blind_input_sha256(right)
    assert blind_input_sha256(left) != blind_input_sha256(
        {**left, "pillars": ["甲子", "乙丑", "丙寅", "戊辰"]}
    )


def test_sample_admission_accepts_only_exact_v004_bundle_root(tmp_path) -> None:
    from engine.evaluation.dual_line_interop import admit_v004_bundle

    admitted = tmp_path / "P-GO-2026-001--blind-bundle--v004"
    admitted.mkdir()
    assert admit_v004_bundle(admitted, expected_case_id="P-GO-2026-001") == admitted

    with pytest.raises(ValueError, match="v004"):
        admit_v004_bundle(tmp_path / "P-GO-2026-001--blind-bundle--v003", expected_case_id="P-GO-2026-001")


def test_sample_admission_requires_the_approved_case_identifier(tmp_path) -> None:
    from engine.evaluation.dual_line_interop import admit_v004_bundle

    disguised = tmp_path / "RF000417--blind-bundle--v004"
    disguised.mkdir()
    with pytest.raises(ValueError, match="case"):
        admit_v004_bundle(disguised, expected_case_id="P-GO-2026-001")


def test_dual_line_runner_rejects_unapproved_case_before_execution(tmp_path) -> None:
    from engine.evaluation.dual_line_interop import run_dual_line

    with pytest.raises(ValueError, match="allowlist"):
        run_dual_line(
            case_id="SYNTHETIC-NOT-ADMITTED",
            parsed_input=object(),
            chart={},
            approved_case_ids=frozenset({"P-GO-2026-001"}),
            workspace_root=tmp_path,
        )


def test_dual_line_runner_executes_blind_copies_and_binds_v5_decision_trace(
    monkeypatch, tmp_path
) -> None:
    from engine.evaluation import dual_line_interop as interop
    from engine.predicates.types import Bazi, Dayun, GanZhi, ParsedInput
    from engine.v5.domain import V5Output

    parsed = ParsedInput(
        case_id=CASE_ID,
        bazi=Bazi(
            年柱=GanZhi.parse("甲子"),
            月柱=GanZhi.parse("乙丑"),
            日柱=GanZhi.parse("丙寅"),
            时柱=GanZhi.parse("丁卯"),
        ),
        dayun=Dayun(起运岁=0.0, 起运年=2000, 顺逆="顺"),
        known_facts=[SimpleNamespace(type="career", year=2020, event="synthetic")],
        questions=["synthetic future question"],
        case_meta={"feedback": "synthetic outcome", "来源": "synthetic"},
    )
    compatibility_calls = []
    v5_calls = []

    def run_compatibility(blind, *, cases_dir, write_findings):
        compatibility_calls.append((blind, cases_dir, write_findings))
        return SimpleNamespace(case_id=CASE_ID, final_conclusions=[])

    def run_v5(chart, *, case_id, workspace_root):
        v5_calls.append(dict(chart))
        return V5Output(case_id=case_id, chart=dict(chart))

    monkeypatch.setattr("engine.application.pipeline_runner.run_pipeline", run_compatibility)
    monkeypatch.setattr("engine.v5.runner.run_v5", run_v5)

    chart = {
        "case_id": CASE_ID,
        "pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"},
        "known_facts": [{"event": "synthetic revealed outcome"}],
        "questions": ["synthetic future question"],
        "feedback": "synthetic revealed outcome",
    }
    result = interop.run_dual_line(
        case_id=CASE_ID,
        parsed_input=parsed,
        chart=chart,
        approved_case_ids=frozenset({CASE_ID}),
        workspace_root=tmp_path,
    )

    assert result.case_id == CASE_ID
    blind_chart = {"case_id": CASE_ID, "pillars": chart["pillars"]}
    assert result.input_sha256 == interop.blind_input_sha256(blind_chart)
    assert v5_calls == [blind_chart]
    assert len(compatibility_calls) == 1
    blind, cases_dir, write_findings = compatibility_calls[0]
    assert blind is not parsed
    assert blind.known_facts == []
    assert blind.questions == []
    assert "feedback" not in blind.case_meta
    assert cases_dir == tmp_path / "cases"
    assert write_findings is False
    assert parsed.known_facts and parsed.questions and "feedback" in parsed.case_meta
    assert result.v5_snapshot.case_id == CASE_ID
    assert result.decision_run.run_id == result.v5_snapshot.run_id
    assert result.trace_issues == []
    assert result.diff_report.case_id == CASE_ID
    assert result.diff_report.input_sha256 == result.input_sha256
    assert result.diff_report.differences == []


@pytest.mark.parametrize(
    ("decision_case_id", "decision_run_id"),
    [("OTHER-CASE", "unbound"), (CASE_ID, "unbound")],
)
def test_dual_line_runner_rejects_unbound_decision_run_identity(
    monkeypatch, tmp_path, decision_case_id, decision_run_id
) -> None:
    from engine.evaluation import dual_line_interop as interop
    from engine.predicates.types import Bazi, Dayun, GanZhi, ParsedInput
    from engine.v5.domain import V5Output

    parsed = ParsedInput(
        case_id=CASE_ID,
        bazi=Bazi(
            年柱=GanZhi.parse("甲子"),
            月柱=GanZhi.parse("乙丑"),
            日柱=GanZhi.parse("丙寅"),
            时柱=GanZhi.parse("丁卯"),
        ),
        dayun=Dayun(起运岁=0.0, 起运年=2000, 顺逆="顺"),
        case_meta={"来源": "synthetic"},
    )
    monkeypatch.setattr(
        "engine.application.pipeline_runner.run_pipeline",
        lambda *_args, **_kwargs: SimpleNamespace(case_id=CASE_ID, final_conclusions=[]),
    )
    monkeypatch.setattr(
        "engine.v5.runner.run_v5",
        lambda _chart, *, case_id, workspace_root: V5Output(
            case_id=case_id,
            chart={
                "case_id": case_id,
                "pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "戊辰"},
            },
        ),
    )

    monkeypatch.setattr(
        "engine.decision.v5_adapter.decision_run_from_snapshot",
        lambda _snapshot: SimpleNamespace(
            run_id=decision_run_id,
            case_id=decision_case_id,
            validate_trace=lambda: [],
        ),
    )
    with pytest.raises(ValueError, match="case_id|run_id|trace"):
        interop.run_dual_line(
            case_id=CASE_ID,
            parsed_input=parsed,
            chart={"case_id": CASE_ID, "pillars": {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"}},
            approved_case_ids=frozenset({CASE_ID}),
            workspace_root=tmp_path,
        )


def test_dual_line_diff_matches_only_shared_rule_identity_and_preserves_raw_values() -> None:
    from engine.evaluation.dual_line_interop import compare_dual_line_outputs

    compatibility = SimpleNamespace(
        final_conclusions=[
            SimpleNamespace(
                conclusion_id="legacy-1",
                statement="兼容线断语",
                domain="事业",
                evidence=[SimpleNamespace(rule_id="RULE-SYNTH-001")],
            )
        ]
    )
    v5 = SimpleNamespace(
        claims=[
            SimpleNamespace(
                claim_id="v5-1",
                claim="V5 原始命题",
                domain="career",
                evidence=[SimpleNamespace(rule_ids=["RULE-SYNTH-001"])],
            )
        ]
    )

    report = compare_dual_line_outputs(
        case_id=CASE_ID,
        input_sha256="b" * 64,
        compatibility_output=compatibility,
        v5_output=v5,
    )

    assert [(item.field_path, item.compatibility_value, item.v5_value) for item in report.differences] == [
        ("statement", "兼容线断语", "V5 原始命题"),
        ("domain", "事业", "career"),
    ]
    assert all(item.classification == "human_adjudication_blocker" for item in report.adjudication_blockers)


def test_dual_line_diff_does_not_similarity_merge_unmatched_claims() -> None:
    from engine.evaluation.dual_line_interop import compare_dual_line_outputs

    compatibility = SimpleNamespace(
        final_conclusions=[
            SimpleNamespace(statement="相似描述", domain="事业", evidence=[])
        ]
    )
    v5 = SimpleNamespace(
        claims=[SimpleNamespace(claim="相似描述", domain="career", evidence=[])]
    )

    report = compare_dual_line_outputs(
        case_id=CASE_ID,
        input_sha256="c" * 64,
        compatibility_output=compatibility,
        v5_output=v5,
    )

    assert len(report.differences) == 2
    assert {item.classification for item in report.differences} == {"human_adjudication_blocker"}
    assert {item.compatibility_value is None for item in report.differences} == {False, True}


def test_dual_line_diff_leaves_ambiguous_shared_rule_matches_unpaired() -> None:
    from engine.evaluation.dual_line_interop import compare_dual_line_outputs

    compatibility = SimpleNamespace(
        final_conclusions=[
            SimpleNamespace(
                conclusion_id="legacy-1",
                statement="兼容断语",
                evidence=[SimpleNamespace(rule_id="RULE-SYNTH-SHARED")],
            )
        ]
    )
    v5 = SimpleNamespace(
        claims=[
            SimpleNamespace(claim_id="v5-1", claim="V5 断语一", evidence=[SimpleNamespace(rule_ids=["RULE-SYNTH-SHARED"])]),
            SimpleNamespace(claim_id="v5-2", claim="V5 断语二", evidence=[SimpleNamespace(rule_ids=["RULE-SYNTH-SHARED"])]),
        ]
    )

    report = compare_dual_line_outputs(
        case_id=CASE_ID,
        input_sha256="d" * 64,
        compatibility_output=compatibility,
        v5_output=v5,
    )

    assert len(report.differences) == 3
    assert sum(item.compatibility_value is None for item in report.differences) == 2
    assert sum(item.v5_value is None for item in report.differences) == 1


def test_diff_report_archive_is_json_and_create_only(tmp_path) -> None:
    import json

    from engine.evaluation.dual_line_interop import (
        FieldDifference,
        archive_diff_report,
        build_diff_report,
    )

    report = build_diff_report(
        case_id=CASE_ID,
        input_sha256="e" * 64,
        differences=[FieldDifference("rule:R-SYNTH", "statement", "原文甲", "原文乙")],
    )
    destination = tmp_path / "diff-report.json"

    archive_diff_report(report, destination)

    archived = json.loads(destination.read_text(encoding="utf-8"))
    assert archived["case_id"] == CASE_ID
    assert archived["input_sha256"] == "e" * 64
    assert archived["differences"][0]["compatibility_value"] == "原文甲"
    assert archived["adjudication_blockers"] == archived["differences"]
    with pytest.raises(FileExistsError):
        archive_diff_report(report, destination)


def test_decision_trace_failure_fails_closed_without_partial_report() -> None:
    from engine.evaluation.dual_line_interop import validate_dual_line_trace

    malformed = SimpleNamespace(validate_trace=lambda: ["missing event source"])
    with pytest.raises(ValueError, match="trace"):
        validate_dual_line_trace(malformed)


def test_decision_trace_requires_decision_run_validator() -> None:
    from engine.evaluation.dual_line_interop import validate_dual_line_trace

    with pytest.raises(ValueError, match="DecisionRun"):
        validate_dual_line_trace(SimpleNamespace())


def test_statement_record_v2_mapping_requires_explicit_learning_identity() -> None:
    from engine.evaluation.dual_line_interop import statement_records_v2_for_conclusions

    conclusion = SimpleNamespace(
        statement="Synthetic only",
        domain="事业",
        contributing_schools=["duan"],
        trace_ids=["R-SYNTH-001"],
        confidence=SimpleNamespace(star=3, percentage=0.6),
    )
    output = SimpleNamespace(final_conclusions=[conclusion])

    with pytest.raises(ValueError, match="rule_direction|matter_category|section"):
        statement_records_v2_for_conclusions(output, case_id=CASE_ID, run_id="run-synthetic")


def test_statement_record_v2_mapping_keeps_explicit_learning_identity() -> None:
    from engine.evaluation.dual_line_interop import statement_records_v2_for_conclusions

    conclusion = SimpleNamespace(
        conclusion_id="CC-SYNTH-001",
        statement="Synthetic career statement",
        domain="事业",
        layer="独门",
        contributing_schools=["duan"],
        trace_ids=["RULE-SYNTH-CAREER"],
        confidence=SimpleNamespace(star=3, percent=0.6),
        matter_category="career",
        rule_direction="positive",
        section="synthetic-career",
        evidence=[SimpleNamespace(rule_id="RULE-SYNTH-CAREER", school="duan")],
    )
    output = SimpleNamespace(final_conclusions=[conclusion])

    records = statement_records_v2_for_conclusions(output, case_id=CASE_ID, run_id="run-synthetic")

    assert records["schema_version"] == "statement_record.v2"
    assert records["run_id"] == "run-synthetic"
    assert records["records"][0]["matter_category"] == "career"
    assert records["records"][0]["rule_direction"] == "positive"
    assert records["records"][0]["section"] == "synthetic-career"
