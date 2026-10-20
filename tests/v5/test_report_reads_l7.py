from __future__ import annotations

import json
import pathlib

from engine.v5.report_view import _l7_conclusion_for_domain


def _decisions():
    return [
        {"decision_id": "d-career", "domain": "事业"},
        {"decision_id": "d-wealth", "domain": "财富"},
    ]


def _report_items():
    return [
        {"report_item_id": "r1", "decision_id": "d-career", "display_text": "事业：分层链裁决结论。"},
        {"report_item_id": "r2", "decision_id": "d-wealth", "display_text": "财富：分层链裁决结论。"},
    ]


def test_returns_display_text_for_matching_domain():
    text = _l7_conclusion_for_domain("事业", _report_items(), _decisions())
    assert text == "事业：分层链裁决结论。"


def test_returns_none_when_domain_absent():
    text = _l7_conclusion_for_domain("健康", _report_items(), _decisions())
    assert text is None


def test_returns_none_when_report_items_empty():
    assert _l7_conclusion_for_domain("事业", [], _decisions()) is None


def test_context_career_uses_l7_when_provided():
    from engine.v5 import run_v5
    from engine.v5.report_view import build_report_v6_context

    output = run_v5({"case_id": "C-TEST-R6", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})
    template_text = "{{ 事业裁决结论 }}|{{ 财富裁决结论 }}"

    report_items = [{"report_item_id": "r1", "decision_id": "d-c", "display_text": "事业：来自L7的裁决。"}]
    decisions = [{"decision_id": "d-c", "domain": "事业"}]

    ctx = build_report_v6_context(
        output,
        template_text=template_text,
        report_items=report_items,
        arbitration_decisions=decisions,
    )

    assert ctx["事业裁决结论"] == "事业：来自L7的裁决。"


def test_context_default_unchanged_without_report_items():
    from engine.v5 import run_v5
    from engine.v5.report_view import build_report_v6_context

    output = run_v5({"case_id": "C-TEST-R6-DEF", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})
    template_text = "{{ 事业裁决结论 }}"

    with_none = build_report_v6_context(output, template_text=template_text)
    explicit_none = build_report_v6_context(output, template_text=template_text, report_items=None)

    assert with_none["事业裁决结论"] == explicit_none["事业裁决结论"]
    assert with_none["事业裁决结论"]


def test_preprod_career_report_matches_l7(tmp_path):
    from engine.v5.preprod import render_v6_preprod_case

    input_path = "cases/C-2026-035-乾-戊辰癸亥甲戌庚午/input.md"
    report_path, _ = render_v6_preprod_case(
        input_path, reports_dir=tmp_path, workspace_root=".", manifest_root=tmp_path
    )
    report_text = pathlib.Path(report_path).read_text(encoding="utf-8")
    decision_json = pathlib.Path(str(report_path).replace(".md", ".decision-run.json"))
    d = json.loads(decision_json.read_text(encoding="utf-8"))
    dom_by_dec = {x["decision_id"]: x["domain"] for x in d["arbitration_decisions"]}
    career_text = next(
        (ri["display_text"] for ri in d["report_items"] if dom_by_dec.get(ri["decision_id"]) == "事业"),
        None,
    )
    assert career_text, "事业域应有 L7 report_item"
    assert career_text in report_text


def test_report_items_display_text_carries_school_evidence():
    from engine.decision.v5_adapter import _report_items
    from engine.decision.models import ArbitrationDecision, SchoolClaim

    decisions = [
        ArbitrationDecision(
            decision_id="d-career", domain="事业", competing_event_ids=["e1"],
            result="winner", winner_ids=["e1"], reason="事业裁决",
        )
    ]
    claims = [
        SchoolClaim(claim_id="c1", school="ziping", role_granted_by_l1="lead", domain="事业", claim_type="structure", statement="正印格用食伤", confidence=0.8),
        SchoolClaim(claim_id="c2", school="duan_jianye", role_granted_by_l1="lead", domain="事业", claim_type="event", statement="做功制用明显", confidence=0.7),
    ]

    items = _report_items("C-T", decisions, [], claims)
    text = items[0].display_text

    assert "事业" in text
    assert "参与流派" in text
    assert "依据：" in text
    assert "正印格用食伤" in text or "做功制用明显" in text
    assert "c1" not in text and "d-career" not in text
    assert items[0].evidence_summary == "本域共 2 条流派命题参与结构裁决。"


def test_context_all_domains_use_l7_when_provided():
    from engine.v5 import run_v5
    from engine.v5.report_view import build_report_v6_context

    output = run_v5({"case_id": "C-TEST-R7", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})
    template_text = "{{ 事业裁决结论 }}|{{ 健康裁决结论 }}|{{ 财富裁决结论 }}"
    report_items = [
        {"report_item_id": "r1", "decision_id": "d-c", "display_text": "事业：L7事业。"},
        {"report_item_id": "r2", "decision_id": "d-h", "display_text": "健康：L7健康。"},
        {"report_item_id": "r3", "decision_id": "d-w", "display_text": "财富：L7财富。"},
    ]
    decisions = [
        {"decision_id": "d-c", "domain": "事业"},
        {"decision_id": "d-h", "domain": "健康"},
        {"decision_id": "d-w", "domain": "财富"},
    ]

    ctx = build_report_v6_context(output, template_text=template_text, report_items=report_items, arbitration_decisions=decisions)

    assert ctx["事业裁决结论"] == "事业：L7事业。"
    assert ctx["健康裁决结论"] == "健康：L7健康。"
    assert ctx["财富裁决结论"] == "财富：L7财富。"
