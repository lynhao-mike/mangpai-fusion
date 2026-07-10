from __future__ import annotations

from engine.decision.l1_school_router import _apply_learned_prior, _downgrade_role


def test_downgrade_role_moves_one_step() -> None:
    assert _downgrade_role("lead") == "co_lead"
    assert _downgrade_role("co_lead") == "evidence_only"
    assert _downgrade_role("evidence_only") == "abstain"
    assert _downgrade_role("abstain") == "abstain"


def test_apply_prior_none_is_noop() -> None:
    role, score, reasons = _apply_learned_prior("ziping", "lead", 0.75, None)
    assert (role, score, reasons) == ("lead", 0.75, [])


def test_apply_prior_low_hit_downgrades() -> None:
    role, score, reasons = _apply_learned_prior("ziping", "lead", 0.75, {"ziping": (0.1, 10)})
    assert role == "co_lead"
    assert score < 0.75
    assert reasons


def test_apply_prior_insufficient_sample_is_noop() -> None:
    role, score, reasons = _apply_learned_prior("ziping", "lead", 0.75, {"ziping": (0.1, 3)})
    assert (role, score, reasons) == ("lead", 0.75, [])


def test_apply_prior_high_hit_is_noop() -> None:
    role, score, reasons = _apply_learned_prior("ziping", "lead", 0.75, {"ziping": (0.9, 10)})
    assert (role, score, reasons) == ("lead", 0.75, [])


def test_apply_prior_other_school_untouched() -> None:
    role, score, reasons = _apply_learned_prior("duan_jianye", "co_lead", 0.6, {"ziping": (0.1, 10)})
    assert (role, score, reasons) == ("co_lead", 0.6, [])


def test_route_schools_default_unchanged_by_prior_param() -> None:
    from engine.decision.l1_school_router import route_schools
    from engine.decision.models import ChartFactLedger, ContextFactLedger

    chart = ChartFactLedger(four_pillars={"year": "甲子", "month": "丁丑", "day": "庚辰", "hour": "癸未"})
    ctx = ContextFactLedger()

    without = {i.school: (i.role, i.applicability_score) for i in route_schools(chart, ctx)}
    with_none = {i.school: (i.role, i.applicability_score) for i in route_schools(chart, ctx, learned_prior=None)}

    assert without == with_none


def test_route_schools_downgrades_low_hit_school() -> None:
    from engine.decision.l1_school_router import route_schools
    from engine.decision.models import ChartFactLedger, ContextFactLedger

    chart = ChartFactLedger(four_pillars={"year": "甲子", "month": "丁丑", "day": "庚辰", "hour": "癸未"})
    ctx = ContextFactLedger()

    base = {i.school: i for i in route_schools(chart, ctx)}
    learned = {i.school: i for i in route_schools(chart, ctx, learned_prior={"ziping": (0.1, 10)})}

    assert base["ziping"].role == "lead"
    assert learned["ziping"].role == "co_lead"
    assert learned["ziping"].applicability_score < base["ziping"].applicability_score
    assert any("学习先验" in r for r in learned["ziping"].reasons)
    for school in base:
        if school != "ziping":
            assert (learned[school].role, learned[school].applicability_score) == (
                base[school].role,
                base[school].applicability_score,
            )
