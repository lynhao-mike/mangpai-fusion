"""V5 目标级裁决单位测试。"""

from engine.v5 import run_v5
from engine.v5.domain import V5Claim, V5Confidence, V5Evidence


def _claim(claim_id: str, stance: str, target_id: str = "career.path") -> V5Claim:
    return V5Claim(
        claim_id=claim_id,
        school="duan_jianye",
        domain="事业",
        claim="事业路径命题",
        claim_type="event_claim",
        stance=stance,  # type: ignore[arg-type]
        polarity="positive" if stance == "support" else "negative",
        confidence=V5Confidence(tier="★★★", score=0.66, note="test"),
        evidence=[V5Evidence(
            evidence_id=f"e-{claim_id}",
            source="test",
            text="chart fact",
            node_refs=["chart:root"],
            rule_ids=["RULE-TEST"],
        )],
        falsifiable="若现实路径完全相反则失验。",
        metadata={"task_id": target_id, "target_id": target_id},
    )


def test_same_target_opposition_is_unresolved_and_targets_are_separate() -> None:
    output = run_v5(
        {"case_id": "C-UNIT", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]},
        claims=[
            _claim("support", "support"),
            _claim("oppose", "oppose"),
            _claim("wealth", "support", "wealth.source"),
        ],
    )

    units = {(item.target_id, item.claim_type): item for item in output.adjudication_units}
    assert units[("career.path", "event_claim")].status == "UNRESOLVED"
    assert units[("career.path", "event_claim")].mapping_status == "NO_MAPPING"
    assert units[("career.path", "event_claim")].winner_claim_ids == ()
    assert units[("wealth.source", "event_claim")].status == "PRIMARY"


def test_v5_units_survive_output_round_trip() -> None:
    output = run_v5(
        {"case_id": "C-UNIT-ROUNDTRIP", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]},
        claims=[_claim("only", "support")],
    )
    restored = type(output).from_json(output.to_json())
    assert restored.adjudication_units == output.adjudication_units


def test_missing_target_identity_is_unsupported_instead_of_a_pseudo_target() -> None:
    output = run_v5(
        {"case_id": "C-UNIT-MISSING-TARGET", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]},
        claims=[_claim("no-target", "support", target_id="")],
    )

    unit = output.adjudication_units[0]
    assert unit.status == "UNSUPPORTED"
    assert unit.winner_claim_ids == ()
    assert "缺少显式" in unit.rationale


def test_existing_rule_topics_produce_real_target_units() -> None:
    output = run_v5(
        {"case_id": "C-UNIT-PRODUCTION", "pillars": ["庚辰", "己卯", "壬午", "丙午"]},
    )

    valid_units = [
        item for item in output.adjudication_units
        if not item.target_id.startswith("__missing_target__.")
    ]
    assert valid_units
    assert all(item.status != "UNSUPPORTED" for item in valid_units)
