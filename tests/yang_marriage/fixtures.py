from dataclasses import dataclass, replace

from engine.decision.models import ChartFactLedger
from engine.features.types import ChartFeatureVector
from engine.v5.domain import V5Claim, V5Confidence, V5Evidence, V5Output


def chart(case_id: str, *, sex: str = "乾", day: str = "壬子") -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker=sex,
        four_pillars={"year": "甲午", "month": "戊寅", "day": day, "hour": "辛丑"},
        raw_source_hash=f"raw-{case_id}",
    )


def cfv(case_id: str, **changes: object) -> ChartFeatureVector:
    base = ChartFeatureVector(
        schema_version="cfv-v1",
        chart_id=case_id,
        element_counts={"木": 2, "火": 2, "土": 2, "金": 1, "水": 1},
        element_energy={"木": .2, "火": .2, "土": .2, "金": .2, "水": .2},
        dominant_element="木",
        missing_elements=(),
        element_concentration=.25,
        day_master="壬",
        day_master_element="水",
        month_branch="寅",
        month_lord="甲",
        rooted_count=1,
        supporting_count=3,
        draining_count=5,
        monthly_command_favorable=False,
        ten_god_counts={
            "正财": 1,
            "偏财": 0,
            "正官": 1,
            "七杀": 0,
            "比肩": 0,
            "劫财": 0,
            "食神": 0,
            "伤官": 0,
        },
        has_official=True,
        has_wealth=True,
        has_output=False,
        has_resource=False,
        mixed_official_kill=False,
        chong_pairs=(),
        he_pairs=(),
        xing_hai_pairs=(),
        branch_conflict_intensity=0.0,
        cold_warm_axis=0.0,
        dry_wet_axis=0.0,
        climate_extreme=False,
        has_hour_pillar=True,
        evidence_completeness="full",
    )
    return replace(base, **changes)


@dataclass(frozen=True)
class SyntheticMarriageCase:
    case_id: str
    chart: ChartFactLedger
    features: ChartFeatureVector
    expected_state: str
    expected_families: tuple[str, ...]


def synthetic_cases() -> tuple[SyntheticMarriageCase, ...]:
    male_peer = {
        "正财": 1, "偏财": 0, "正官": 0, "七杀": 0,
        "比肩": 2, "劫财": 1, "食神": 0, "伤官": 0,
    }
    male_quiet = {**male_peer, "正财": 2, "比肩": 0, "劫财": 0}
    male_absent_peer = {**male_peer, "正财": 0, "比肩": 2, "劫财": 2}
    female_output = {
        "正财": 0, "偏财": 0, "正官": 1, "七杀": 0,
        "比肩": 0, "劫财": 0, "食神": 2, "伤官": 2,
    }
    female_mixed = {**female_output, "七杀": 1, "食神": 0, "伤官": 0}
    female_absent_output = {**female_output, "正官": 0}
    anchor = "spouse_palace_event_anchor"
    context = "spouse_star_context_pressure"
    ambient = "ambient_relationship_pressure"
    peer = "spouse_star_peer_interaction"
    output = "spouse_star_output_interaction"
    configuration = "spouse_star_configuration"
    return (
        SyntheticMarriageCase("YM-SYN-M1", chart("YM-SYN-M1"),
            cfv("YM-SYN-M1", chong_pairs=(("子", "午"),), ten_god_counts=male_peer),
            "event", (anchor, context, peer)),
        SyntheticMarriageCase("YM-SYN-F1", chart("YM-SYN-F1", sex="坤"),
            cfv("YM-SYN-F1", xing_hai_pairs=(("子", "未"),), ten_god_counts=female_output),
            "event", (anchor, context, output)),
        SyntheticMarriageCase("YM-SYN-F2", chart("YM-SYN-F2", sex="坤"),
            cfv("YM-SYN-F2", chong_pairs=(("子", "午"),), mixed_official_kill=True,
                ten_god_counts=female_mixed),
            "event", (anchor, configuration)),
        SyntheticMarriageCase("YM-SYN-S1", chart("YM-SYN-S1"),
            cfv("YM-SYN-S1", ten_god_counts=male_quiet), "abstain", ()),
        SyntheticMarriageCase("YM-SYN-S2", chart("YM-SYN-S2"),
            cfv("YM-SYN-S2", chong_pairs=(("寅", "申"),),
                branch_conflict_intensity=1.0, ten_god_counts=male_quiet),
            "abstain", ()),
        SyntheticMarriageCase("YM-SYN-P1", chart("YM-SYN-P1"),
            cfv("YM-SYN-P1", chong_pairs=(("子", "午"),), ten_god_counts=male_quiet),
            "pressure", (anchor,)),
        SyntheticMarriageCase("YM-SYN-P2", chart("YM-SYN-P2"),
            cfv("YM-SYN-P2", ten_god_counts=male_peer), "pressure", (context, peer)),
        SyntheticMarriageCase("YM-SYN-P3", chart("YM-SYN-P3", sex="坤"),
            cfv("YM-SYN-P3", mixed_official_kill=True, ten_god_counts=female_mixed),
            "pressure", (configuration,)),
        SyntheticMarriageCase("YM-SYN-G1", chart("YM-SYN-G1"),
            cfv("YM-SYN-G1", has_wealth=False,
                ten_god_counts={**male_quiet, "正财": 0}), "pressure", (context,)),
        SyntheticMarriageCase("YM-SYN-G2", chart("YM-SYN-G2"),
            cfv("YM-SYN-G2", has_wealth=False, ten_god_counts=male_absent_peer),
            "pressure", (ambient, context)),
        SyntheticMarriageCase("YM-SYN-G3", chart("YM-SYN-G3", sex="坤"),
            cfv("YM-SYN-G3", has_official=False, ten_god_counts=female_absent_output),
            "pressure", (ambient, context)),
        SyntheticMarriageCase("YM-SYN-I1", chart("YM-SYN-I1", sex=""),
            cfv("YM-SYN-I1", ten_god_counts=male_quiet), "abstain", ()),
        SyntheticMarriageCase("YM-SYN-I2", chart("YM-SYN-I2", day="壬"),
            cfv("YM-SYN-I2", ten_god_counts=male_quiet), "abstain", ()),
        SyntheticMarriageCase("YM-SYN-I3", chart("YM-SYN-I3"),
            cfv("YM-SYN-I3", evidence_completeness="partial", ten_god_counts=male_quiet),
            "abstain", ()),
        SyntheticMarriageCase("YM-SYN-D1", chart("YM-SYN-D1"),
            cfv("YM-SYN-D1", chong_pairs=(("子", "午"),),
                xing_hai_pairs=(("午", "子"),), ten_god_counts=male_quiet),
            "pressure", (anchor,)),
        SyntheticMarriageCase("YM-SYN-D2", chart("YM-SYN-D2"),
            cfv("YM-SYN-D2", chong_pairs=(("子", "午"), ("子", "卯")),
                ten_god_counts=male_quiet), "pressure", (anchor,)),
        SyntheticMarriageCase("YM-SYN-D3", chart("YM-SYN-D3", sex="坤"),
            cfv("YM-SYN-D3", mixed_official_kill=True, ten_god_counts=female_mixed),
            "pressure", (configuration,)),
        SyntheticMarriageCase("YM-SYN-D4", chart("YM-SYN-D4", sex="坤"),
            cfv("YM-SYN-D4", chong_pairs=(("子", "午"), ("午", "子")),
                mixed_official_kill=True, ten_god_counts=female_mixed),
            "event", (anchor, configuration)),
        SyntheticMarriageCase("YM-SYN-X1", chart("YM-SYN-X1"),
            cfv("YM-SYN-X1", has_wealth=False, ten_god_counts=male_absent_peer),
            "pressure", (ambient, context)),
        SyntheticMarriageCase("YM-SYN-R1", chart("YM-SYN-R1", sex="坤"),
            cfv("YM-SYN-R1", chong_pairs=(("子", "午"), ("午", "子")),
                mixed_official_kill=True, ten_god_counts=female_mixed),
            "event", (anchor, configuration)),
    )


def slice_output(case_id: str, *, include_old_target: bool = True) -> V5Output:
    claims = [
        V5Claim(
            claim_id="legacy-nontarget-career",
            school="ziping",
            domain="事业",
            claim="合成非目标事业事件。",
            claim_type="event_claim",
            confidence=V5Confidence(score=.6),
            evidence=[V5Evidence("legacy-evidence", "synthetic", "合成非目标证据")],
            falsifiable="未发生则证伪。",
            metadata={"task_id": "career.role_change"},
        )
    ]
    if include_old_target:
        claims.append(V5Claim(
            claim_id="legacy-yang-marriage-target",
            school="yang_qingjuan",
            domain="婚姻",
            claim="旧目标旁路。",
            claim_type="event_claim",
            confidence=V5Confidence(score=.6),
            evidence=[V5Evidence("old-target-evidence", "synthetic", "旧目标合成证据")],
            falsifiable="未发生则证伪。",
            metadata={"task_id": "marriage.divorce_or_remarriage"},
        ))
    return V5Output(case_id=case_id, chart={}, claims=claims)
