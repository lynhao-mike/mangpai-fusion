from __future__ import annotations

from engine.decision.l3_structure import build_structural_verdicts
from engine.decision.models import SchoolClaim


def _claim(claim_id: str, statement: str, metadata: dict | None = None) -> SchoolClaim:
    return SchoolClaim(
        claim_id=claim_id,
        school="ziping",
        role_granted_by_l1="lead",
        domain="事业",
        claim_type="structure_claim",
        statement=statement,
        confidence=0.6,
        metadata=metadata or {},
    )


def test_l3_consumes_geju_direction_from_l2_without_recomputing_it() -> None:
    claims = [
        _claim(
            "profile",
            "格局大类裁决：正格",
            {
                "geju_type": "正格",
                "favor_shishen": ["食神"],
                "avoid_shishen": ["正印"],
            },
        ),
        _claim("bad", "正印当权主事业上升"),
    ]

    verdicts = {
        item.claim_id: item
        for item in build_structural_verdicts("C-R10", claims)
    }

    assert verdicts["bad"].verdict == "weaken"
    assert "正印" in verdicts["bad"].structural_reason
    assert "正格" in verdicts["bad"].structural_reason


def test_l3_without_l2_geju_metadata_does_not_invent_favor_or_avoid() -> None:
    claim = _claim("plain", "正印当权主事业上升", {})

    verdict = build_structural_verdicts("C-R10", [claim])[0]

    assert verdict.verdict == "pass"
    assert "忌神" not in verdict.structural_reason
    assert "用神" not in verdict.structural_reason
