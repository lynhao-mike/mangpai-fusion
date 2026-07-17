from dataclasses import replace

from engine.decision.models import ChartFactLedger
from engine.features.types import ChartFeatureVector


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
