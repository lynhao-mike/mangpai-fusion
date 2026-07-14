from __future__ import annotations

from engine.decision.routing_holdout_artifacts import (
    audit_competitive_coverage,
    build_deterministic_case_split,
    rewrite_score_prototypes,
)


def test_case_split_is_deterministic_disjoint_and_groups_duplicate_subjects() -> None:
    cases = [
        {"case_id": "P-001-乾-甲子乙丑丙寅丁卯", "sex_marker": "乾", "four_pillars": ["甲子", "乙丑", "丙寅", "丁卯"]},
        {"case_id": "P-ALIAS-乾-甲子乙丑丙寅丁卯", "sex_marker": "乾", "four_pillars": ["甲子", "乙丑", "丙寅", "丁卯"]},
        {"case_id": "P-002-坤-戊辰己巳庚午辛未", "sex_marker": "坤", "four_pillars": ["戊辰", "己巳", "庚午", "辛未"]},
        {"case_id": "P-003-乾-壬申癸酉甲戌乙亥", "sex_marker": "乾", "four_pillars": ["壬申", "癸酉", "甲戌", "乙亥"]},
    ]

    first = build_deterministic_case_split(cases, holdout_fraction=0.34, salt="l1-v1")
    second = build_deterministic_case_split(list(reversed(cases)), holdout_fraction=0.34, salt="l1-v1")

    assert first == second
    assert set(first.training_case_ids).isdisjoint(first.holdout_case_ids)
    assert set(first.training_case_ids) | set(first.holdout_case_ids) == {row["case_id"] for row in cases}
    assert ("P-001-乾-甲子乙丑丙寅丁卯" in first.holdout_case_ids) == ("P-ALIAS-乾-甲子乙丑丙寅丁卯" in first.holdout_case_ids)


def test_rewrite_score_prototypes_uses_cfv_mapping_and_preserves_other_fields() -> None:
    cases = [{
        "case_id": "P-001-乾-甲子乙丑丙寅丁卯",
        "sex_marker": "乾",
        "four_pillars": ["甲子", "乙丑", "丙寅", "丁卯"],
        "solar_datetime": "2000-01-01 01:00",
        "dayun_sequence": ["戊辰"],
    }]
    scores = [{
        "case_id": cases[0]["case_id"], "school_id": "ziping", "task_id": "career.role_change",
        "claim_type": "binary_event", "state": "claim", "abstained": False, "knowledge_coverage": True,
        "chart_prototype_id": "prototype-provisional", "time_horizon": "ten_year",
        "evidence_completeness_band": "complete", "probability_score": 0.8, "timing_score": None,
        "ordinal_score": None, "portrait_agreement": None, "utility": 0.6, "observed_positive": True,
    }]

    rewritten = rewrite_score_prototypes(scores, cases)

    assert rewritten[0]["chart_prototype_id"].startswith("prototype-")
    assert rewritten[0]["chart_prototype_id"] != "prototype-provisional"
    assert rewritten[0]["utility"] == 0.6


def test_competitive_coverage_requires_two_scorable_schools_per_case_task() -> None:
    rows = [
        {"case_id": "C-1", "task_id": "career.role_change", "school_id": "ziping", "utility": 0.7},
        {"case_id": "C-1", "task_id": "career.role_change", "school_id": "ren", "utility": None},
        {"case_id": "C-2", "task_id": "career.role_change", "school_id": "ziping", "utility": 0.6},
        {"case_id": "C-2", "task_id": "career.role_change", "school_id": "ren", "utility": 0.5},
    ]

    audit = audit_competitive_coverage(rows, holdout_case_ids={"C-1", "C-2"}, minimum_competitive_cases=2)

    assert audit.competitive_case_task_count == 1
    assert audit.status == "HOLD"
    assert "C-2|career.role_change" in audit.competitive_identities


def test_competitive_coverage_goes_ready_only_after_minimum_is_met() -> None:
    rows = [
        {"case_id": case_id, "task_id": "career.role_change", "school_id": school, "utility": utility}
        for case_id in ("C-1", "C-2")
        for school, utility in (("ziping", 0.7), ("ren", 0.5))
    ]

    audit = audit_competitive_coverage(rows, holdout_case_ids={"C-1", "C-2"}, minimum_competitive_cases=2)

    assert audit.status == "READY"
    assert audit.competitive_case_task_count == 2
