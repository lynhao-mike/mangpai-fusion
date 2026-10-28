"""T-165 审计产物的确定性/完整性检查（不重跑 6112 个 case-year）。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.timing_feasibility_audit import (
    KS,
    WINDOW,
    binom_tail_ge,
    null_hit_prob,
    render_md,
)

ROOT = Path(__file__).resolve().parents[2]
JSON_PATH = ROOT / "META" / "timing-feasibility-audit-v1.json"
MD_PATH = ROOT / "META" / "timing-feasibility-audit-v1.md"


@pytest.fixture(scope="module")
def payload() -> dict:
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def eval_cases() -> dict[str, dict]:
    data = json.loads((ROOT / "META" / "timing-eval-set-v1.json").read_text(encoding="utf-8"))
    return {case["case_id"]: case for case in data["cases"]}


def test_payload_shape_and_counts(payload: dict) -> None:
    assert payload["schema"] == "timing-feasibility-audit/v1"
    assert payload["task"] == "T-165"
    assert payload["mode"] == "read_only_audit"
    census = payload["case_census"]
    assert census["usable_for_timing"] == 382
    assert census["chart_built"] == 382
    assert census["case_years_total"] == 6112
    assert census["scoreable_years_per_case"] == {"16": 382}
    assert len(payload["per_case_coverage"]) == 382
    assert census["events_total"] == 547
    assert census["events_age_15_50"] == 534
    assert census["events_in_dayun_range"] + census["events_outside_dayun_range"] == census["events_total"]
    assert census["dayun_direction_consistent"] == 382
    assert census["dayun_direction_mismatches"] == []
    assert census["cases_with_event_in_window"] + census["cases_without_event_in_window"] == 382


def test_primitive_matrix_complete(payload: dict) -> None:
    matrix = payload["primitive_matrix"]
    items = matrix["items"]
    assert len(items) == 6
    assert {item["id"] for item in items} == {"P1", "P2", "P3", "P4", "P5", "P6"}
    for item in items:
        assert item["status"] in {"有", "无", "部分"}
        assert item["subchecks"], item["id"]
        assert item["example_objects"], item["id"]
        for sub in item["subchecks"]:
            assert sub["status"] in {"有", "无", "部分"}
            assert ".py:" in sub["code"], (item["id"], sub["name"])
        expected = (
            "有"
            if {sub["status"] for sub in item["subchecks"]} == {"有"}
            else "无"
            if {sub["status"] for sub in item["subchecks"]} == {"无"}
            else "部分"
        )
        assert item["status"] == expected, item["id"]
    tally = matrix["tally"]
    assert sum(tally["items"].values()) == 6
    assert tally["subcheck_total"] == sum(tally["subchecks"].values())
    assert tally["items"] == {"有": 2, "无": 0, "部分": 4}
    assert tally["subchecks"] == {"有": 23, "无": 7, "部分": 1}


def test_examples_are_real_cases(payload: dict, eval_cases: dict[str, dict]) -> None:
    for item in payload["primitive_matrix"]["items"]:
        for example in item["example_objects"]:
            case = eval_cases[example["case_id"]]
            assert example["birth_dt"] == case["birth_dt"]
            assert example["gender"] == case["gender"]
            assert WINDOW[0] <= example["age"] <= WINDOW[1]
            assert isinstance(example["year"], int)
            assert "call" in example and example["call"]
            # 例子必须真的落在 20–35 岁窗口内。
            assert example["year"] - case["birth_year"] == example["age"]


def test_preregistration_has_no_age_parameter(payload: dict) -> None:
    prereg = payload["preregistration"]
    assert prereg["zero_age_parameters"]["passed"] is True
    assert prereg["zero_age_parameters"]["rules_with_age_term"] == []
    assert prereg["topk"]["primary_k"] == 3
    assert prereg["topk"]["secondary_k"] == 5
    assert prereg["topk"]["exploratory_k"] == 7
    assert prereg["rules"]
    for rule in prereg["rules"]:
        assert rule["age_term"] is False
        assert "age" not in rule["args"]
    assert "birth_year" not in prereg["score_signature"].split("->")[0]
    assert "birth_year/age 不传入" in prereg["score_signature"]
    assert "8pp" in prereg["decision_rule"]["signal"]
    assert "p<0.01" in prereg["decision_rule"]["signal"]
    assert payload["window"]["age_min"] == 20
    assert payload["window"]["age_max"] == 35
    assert payload["window"]["candidate_years"] == 16


def test_power_table_and_gap_verdict(payload: dict) -> None:
    table = {row["k"]: row for row in payload["power"]["table"]}
    assert set(table) == set(KS)
    assert table[3]["null_p0_pct"] < table[5]["null_p0_pct"] < table[7]["null_p0_pct"]
    assert table[3]["power_at_card_signal"] > 0.80
    assert table[3]["mde80_pp"] < 8.0
    assert table[3]["cases_needing_zero_fill"] == 0
    assert table[5]["cases_needing_zero_fill"] == 124
    assert table[7]["cases_needing_zero_fill"] == 362
    for row in table.values():
        assert row["critical_rate_pct"] < row["card_signal_rate_pct"]
        best = row["best_static_band_same_width"]
        assert best["pct"] > row["null_p0_pct"]
        assert best["range"][1] - best["range"][0] + 1 == row["k"]
    assert payload["gaps"]["blocking"] == []
    assert payload["gaps"]["conclusion"] == "能直接开工"
    assert payload["verdict"] == "能直接开工"


def test_pure_statistics_helpers() -> None:
    assert null_hit_prob(0, 3) == 0.0
    assert null_hit_prob(1, 3) == pytest.approx(3 / 16)
    assert null_hit_prob(16, 7) == 1.0
    assert binom_tail_ge(10, 0.5, 10) == pytest.approx(1 / 1024)
    assert binom_tail_ge(10, 0.5, 0) == 1.0


def test_json_is_canonical(payload: dict) -> None:
    text = JSON_PATH.read_text(encoding="utf-8")
    assert text == json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def test_markdown_matches_payload(payload: dict) -> None:
    text = MD_PATH.read_text(encoding="utf-8")
    assert text == render_md(payload)
    for heading in ("## 2. 原语矩阵", "## 4. 预注册设计草案", "## 5. 统计功效", "## 6. 缺口"):
        assert heading in text
    assert "零年龄参数" in text
    assert "穿，即害也" in text
