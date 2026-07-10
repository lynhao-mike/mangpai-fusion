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
        input_path, reports_dir=tmp_path, workspace_root="."
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
