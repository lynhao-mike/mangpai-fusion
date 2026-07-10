from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from engine.decision import v5_adapter
from engine.decision.l1_school_router import route_schools
from engine.decision.l4_events import build_event_hypotheses
from engine.decision.models import ChartFactLedger, ContextFactLedger
from engine.decision.r10_ziping_career import apply_ziping_career_slice
from engine.v5.runner import run_v5

BASELINE_PATH = Path("tests/r10/fixtures/r6_ziping_career_baseline.json")
TARGET_DOMAINS = {"总体", "事业"}
CHART = {
    "case_id": "C-R10-ZIPING",
    "pillars": {"year": "庚申", "month": "戊寅", "day": "壬子", "hour": "辛丑"},
    "current_dayun": "壬午",
    "current_year": "丙午（2026 年）",
}


def load_r6_baseline() -> dict[str, object]:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def test_r6_baseline_is_frozen_and_nonempty() -> None:
    baseline = load_r6_baseline()
    assert baseline["case_id"] == "C-2026-035-乾-戊辰癸亥甲戌庚午"
    assert int(baseline["career_claim_count"]) == 270
    assert int(baseline["career_school_count"]) == 5
    assert int(baseline["career_evidence_count"]) == 270
    assert int(baseline["career_fifteen_layer_count"]) == 15
    assert baseline["required_text_sentinels"] == ["事业", "依据", "置信度", "应期"]


def test_r6_frozen_gate_rejects_degraded_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    degraded_path = tmp_path / "r6_ziping_career_baseline.json"
    degraded_path.write_text(
        json.dumps(
            {
                "case_id": "C-2026-035-乾-戊辰癸亥甲戌庚午",
                "career_claim_count": 1,
                "career_school_count": 1,
                "career_evidence_count": 1,
                "career_fifteen_layer_count": 15,
                "required_text_sentinels": ["x"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(sys.modules[__name__], "BASELINE_PATH", degraded_path)

    with pytest.raises(AssertionError):
        test_r6_baseline_is_frozen_and_nonempty()


def test_ziping_career_slice_never_sends_target_claims_to_adapter() -> None:
    output = run_v5(CHART, case_id="C-R10-ZIPING")
    ledger = ChartFactLedger(
        four_pillars=CHART["pillars"],
        dayun_steps=[{"ganzhi": "壬午"}],
    )
    applicability = route_schools(
        ledger,
        ContextFactLedger(analysis_focus_text="事业"),
    )

    with (
        patch("engine.decision.v5_adapter._claims", wraps=v5_adapter._claims) as legacy_claims,
        patch(
            "engine.decision.v5_adapter._verdicts",
            side_effect=AssertionError("slice must call L3 directly"),
        ),
        patch(
            "engine.decision.v5_adapter._events",
            side_effect=AssertionError("slice must call L4 directly"),
        ),
    ):
        claims, verdicts, events = apply_ziping_career_slice(output, applicability)

    legacy_claims.assert_called_once()
    legacy_output = legacy_claims.call_args.args[0]
    assert not any(
        claim.school == "ziping" and claim.domain in TARGET_DOMAINS
        for claim in legacy_output.claims
    )

    role = next(item.role for item in applicability if item.school == "ziping")
    native_ids = {
        claim.claim_id
        for claim in output.claims
        if claim.school == "ziping" and claim.domain in TARGET_DOMAINS
    }
    native_l2 = [claim for claim in claims if claim.claim_id in native_ids]
    assert native_l2
    assert {claim.claim_id for claim in native_l2} == native_ids
    assert {claim.role_granted_by_l1 for claim in native_l2} == {role}

    non_target_ids = {
        claim.claim_id
        for claim in output.claims
        if not (claim.school == "ziping" and claim.domain in TARGET_DOMAINS)
        and claim.claim_id
        and claim.school
        and claim.domain
        and next(
            (item.role for item in applicability if item.school == claim.school),
            "co_lead",
        )
        != "abstain"
    }
    assert non_target_ids <= {claim.claim_id for claim in claims}
    assert {verdict.claim_id for verdict in verdicts} == {
        claim.claim_id for claim in claims
    }

    eligible_event_claim_ids = {
        claim.claim_id
        for claim in claims
        if claim.claim_type in {"event", "event_claim"}
        and claim.role_granted_by_l1 != "evidence_only"
        and next(
            verdict.verdict
            for verdict in verdicts
            if verdict.claim_id == claim.claim_id
        )
        in {"pass", "weaken"}
    }
    event_claim_ids = {
        verdict.claim_id
        for event in events
        for verdict in verdicts
        if verdict.verdict_id in event.source_verdict_ids
    }
    assert event_claim_ids <= eligible_event_claim_ids
    assert events == build_event_hypotheses(output.case_id, verdicts, claims)
    assert {claim.domain for claim in claims} >= {
        claim.domain
        for claim in output.claims
        if claim.claim_id in non_target_ids
    }
