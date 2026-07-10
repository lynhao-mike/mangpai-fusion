from __future__ import annotations

from engine.decision.models import SchoolClaim
from engine.decision.v5_adapter import _extract_geju_profile, _verdicts


def test_school_claim_carries_metadata():
    c = SchoolClaim(
        claim_id="c1", school="ziping", role_granted_by_l1="lead",
        domain="事业", claim_type="structure", statement="正印格",
        metadata={"geju_type": "正格", "favor_shishen": ["食神"]},
    )
    assert c.metadata["geju_type"] == "正格"
    assert c.to_dict()["metadata"]["geju_type"] == "正格"


def test_school_claim_metadata_defaults_empty():
    c = SchoolClaim(
        claim_id="c1", school="ziping", role_granted_by_l1="lead",
        domain="事业", claim_type="structure", statement="x",
    )
    assert c.metadata == {}


def test_extract_geju_profile_reads_favor_avoid():
    claims = [
        SchoolClaim(claim_id="c1", school="ziping", role_granted_by_l1="lead",
                    domain="事业", claim_type="structure", statement="格局大类裁决：正格",
                    metadata={"geju_type": "正格",
                              "favor_shishen": ["食神", "伤官"],
                              "avoid_shishen": ["正印", "比肩"]}),
        SchoolClaim(claim_id="c2", school="duan_jianye", role_granted_by_l1="lead",
                    domain="事业", claim_type="event", statement="做功"),
    ]
    profile = _extract_geju_profile(claims)
    assert profile is not None
    assert profile["geju_type"] == "正格"
    assert "食神" in profile["favor"]
    assert "正印" in profile["avoid"]


def test_extract_geju_profile_none_when_absent():
    claims = [
        SchoolClaim(claim_id="c1", school="duan_jianye", role_granted_by_l1="lead",
                    domain="事业", claim_type="event", statement="做功"),
    ]
    assert _extract_geju_profile(claims) is None


def test_verdicts_weaken_claim_against_geju_avoid():
    claims = [
        SchoolClaim(claim_id="g", school="ziping", role_granted_by_l1="lead",
                    domain="事业", claim_type="structure_claim", statement="格局大类裁决：正格",
                    confidence=0.65,
                    metadata={"geju_type": "正格", "favor_shishen": ["食神"], "avoid_shishen": ["正印"]}),
        SchoolClaim(claim_id="bad", school="ziping", role_granted_by_l1="lead",
                    domain="事业", claim_type="structure_claim", statement="正印当权主贵", confidence=0.45),
    ]
    verdicts = {v.claim_id: v for v in _verdicts("C-T", claims)}
    assert verdicts["bad"].verdict in {"weaken", "reject"}


def test_verdicts_zero_regression_without_geju_profile():
    claims = [
        SchoolClaim(claim_id="s", school="ziping", role_granted_by_l1="lead",
                    domain="事业", claim_type="structure_claim", statement="日主得令", confidence=0.6),
    ]
    verdicts = {v.claim_id: v for v in _verdicts("C-T", claims)}
    assert verdicts["s"].verdict == "pass"


def test_verdicts_favor_claim_stays_pass():
    claims = [
        SchoolClaim(claim_id="g", school="ziping", role_granted_by_l1="lead",
                    domain="事业", claim_type="structure_claim", statement="格局大类裁决：正格",
                    confidence=0.65,
                    metadata={"geju_type": "正格", "favor_shishen": ["食神"], "avoid_shishen": ["正印"]}),
        SchoolClaim(claim_id="good", school="ziping", role_granted_by_l1="lead",
                    domain="事业", claim_type="structure_claim", statement="食神吐秀主聪明", confidence=0.6),
    ]
    verdicts = {v.claim_id: v for v in _verdicts("C-T", claims)}
    assert verdicts["good"].verdict == "pass"
