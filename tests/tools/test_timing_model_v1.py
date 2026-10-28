"""T-166 模型检查：零年龄签名、确定性、边可回 engine.cli、标签隔离、低正分年不补齐。"""
from __future__ import annotations

import inspect
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest
import yaml

import tools.timing_model_v1 as model
from engine.facts.chart_facts import chart_from_solar

ROOT = Path(__file__).resolve().parents[2]
SCORES_PATH = ROOT / "META" / "timing-scores-v1.json"
EVAL_PATH = ROOT / "META" / "timing-eval-set-v1.json"
PROTOCOL_PATH = ROOT / "META" / "eval-protocols" / "timing-k3-v1.yaml"
MODEL_SOURCE = ROOT / "tools" / "timing_model_v1.py"

PROTOCOL_FIELDS = {
    "protocol_id",
    "claim_id",
    "frozen_at",
    "commit",
    "trigger_definition",
    "direction_rule",
    "label_map",
    "prediction_rule",
    "scored_set_rule",
    "baseline",
    "decision_rule",
}


@pytest.fixture(scope="module")
def scores() -> dict:
    return json.loads(SCORES_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def eval_cases() -> dict[str, dict]:
    data = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    return {case["case_id"]: case for case in data["cases"] if case.get("usable_for_timing")}


def _cli_relations(birth_dt: str, gender: str, dayun_index: int, year: int) -> dict:
    proc = subprocess.run(
        [
            sys.executable, "-m", "engine.cli", "relations",
            "--birth", birth_dt, "--gender", gender,
            "--dayun-index", str(dayun_index), "--liunian", str(year), "--json",
        ],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


# ── 1. 零年龄参数 ───────────────────────────────────────────────────────────


def test_score_year_takes_no_age_parameter() -> None:
    params = list(inspect.signature(model.score_year).parameters)
    assert params == ["chart_facts", "year", "dayun_index"]
    assert not any("birth" in name or "age" in name for name in params)
    assert model.CASE_FIELDS == ("case_id", "birth_dt", "gender", "birth_year")


# ── 2. 同输入两次输出逐字节一致 ─────────────────────────────────────────────


def test_two_runs_are_byte_identical() -> None:
    cases = model.load_eval_cases()[:3]
    first = model.render_json(model.build_payload(cases, head="test-head"))
    second = model.render_json(model.build_payload(cases, head="test-head"))
    assert first == second
    # 规范形式：sort_keys + indent=2 + 末尾换行
    assert first == json.dumps(
        json.loads(first), ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"


def test_scores_json_is_canonical(scores: dict) -> None:
    text = SCORES_PATH.read_text(encoding="utf-8")
    assert text == model.render_json(scores)


# ── 3. 三个真实年份的边可回 engine.cli ──────────────────────────────────────


def test_three_real_years_trace_back_to_engine_cli(scores: dict, eval_cases: dict[str, dict]) -> None:
    wanted = ["R2", "R3", "R4"]
    picks: list[tuple[dict, dict]] = []
    seen: set[str] = set()
    for case in scores["cases"]:
        for year in case["years"]:
            rules = {edge["rule"] for edge in year["edges"]}
            for rule in wanted:
                if rule in rules and rule not in seen:
                    picks.append((case, year))
                    seen.add(rule)
            if len(picks) == len(wanted):
                break
        if len(picks) == len(wanted):
            break
    assert len(picks) == 3, "产物里缺少 R2/R3/R4 的可追溯示例"

    for case, year in picks:
        source = eval_cases[case["case_id"]]
        assert year["year"] - source["birth_year"] >= model.AGE_MIN
        assert year["year"] - source["birth_year"] <= model.AGE_MAX
        dayun_index = year["edges"][0]["dayun_index"]
        chart = chart_from_solar(datetime.fromisoformat(source["birth_dt"]), source["gender"])
        assert model.score_year(chart, year["year"], dayun_index) == year["score"]
        rel = _cli_relations(source["birth_dt"], source["gender"], dayun_index, year["year"])
        by_id = {edge["id"]: edge for edge in rel["edges"]}
        for recorded in year["edges"]:
            edge = by_id[recorded["edge_id"]]
            assert recorded["chart_id"] == rel["chart_id"]
            assert recorded["dayun_index"] == dayun_index
            assert recorded["liunian_year"] == year["year"]
            assert recorded["kind"] == edge["kind"]
            assert recorded["scope"] == edge["scope"]
            assert recorded["members"] == list(edge["members"])
            assert recorded["at"] in recorded["members"]
            assert recorded["edge_key"] == (
                f"{recorded['chart_id']}|{recorded['dayun_index']}|"
                f"{recorded['liunian_year']}|{recorded['edge_id']}"
            )


# ── 4. 不读结果标签 ─────────────────────────────────────────────────────────


def test_source_never_reads_result_labels() -> None:
    text = MODEL_SOURCE.read_text(encoding="utf-8")
    forbidden = ("marriage" + "_" + "events", "acc" + "uracy", "命中" + "率")
    for token in forbidden:
        assert token not in text


# ── 5. 正分年 <3 的构造例：16 年、positive_years 正确、不补齐 ────────────────


def test_low_positive_years_are_not_padded(monkeypatch: pytest.MonkeyPatch) -> None:
    case = model.load_eval_cases()[0]
    target = case["birth_year"] + 25

    def fake_score(chart, year: int, dayun_index: int) -> dict:
        hit = 1 if year == target else 0
        return {
            "year": year,
            "score": hit,
            "components": {"r1": hit, "r2": 0, "r3": 0, "r4": 0},
            "edges": [],
            "flags": [],
        }

    payload = model.build_payload([case], score_fn=fake_score, head="test-head")
    record = payload["cases"][0]
    assert len(record["years"]) == 16
    assert [item["year"] for item in record["years"]] == model.candidate_years(
        case["birth_year"]
    )
    assert record["positive_years"] == 1
    assert [item["year"] for item in record["years"] if item["score"] > 0] == [target]
    assert sum(item["score"] for item in record["years"]) == 1
    # 不补齐：没有额外年份、没有把零分年改成正分
    assert all(item["year"] != target or item["score"] == 1 for item in record["years"])


# ── 6. 产物覆盖与内部可加 ───────────────────────────────────────────────────


def test_scores_cover_382_cases_16_years(scores: dict) -> None:
    assert scores["schema"] == "timing-scores/v1"
    assert scores["task"] == "T-166"
    assert scores["protocol_id"] == "timing-k3-v1"
    assert scores["frozen_at"] == model.FROZEN_AT
    assert re.fullmatch(r"[0-9a-f]{40}|unknown", scores["git_head"])
    population = scores["population"]
    assert population["cases"] == 382
    assert population["years_per_case"] == 16
    assert population["case_years"] == 6112
    assert population["years_per_case_counts"] == {"16": 382}
    assert len(scores["cases"]) == 382
    assert len({case["case_id"] for case in scores["cases"]}) == 382

    allowed_flags = {"no_spouse_star", "muku_open_by_he_missing", "no_dayun_context"}
    for case in scores["cases"]:
        assert len(case["years"]) == 16
        assert [item["year"] for item in case["years"]] == model.candidate_years(
            case["birth_year"]
        )
        assert case["positive_years"] == sum(1 for item in case["years"] if item["score"] > 0)
        for item in case["years"]:
            comp = item["components"]
            assert set(comp) == {"r1", "r2", "r3", "r4"}
            assert item["score"] == sum(comp.values())
            assert 0 <= item["score"] <= model.MAX_SCORE
            assert 0 <= comp["r1"] <= model.R1_CAP
            assert 0 <= comp["r2"] <= model.R2_CAP
            assert 0 <= comp["r3"] <= model.R3_CAP
            assert 0 <= comp["r4"] <= model.R4_CAP
            counts = {"R1": 0, "R2": 0, "R3": 0, "R4": 0}
            for edge in item["edges"]:
                counts[edge["rule"]] += 1
            assert counts == {"R1": comp["r1"], "R2": comp["r2"], "R3": comp["r3"], "R4": comp["r4"]}
            assert set(item["flags"]) <= allowed_flags
            assert "age" not in item and "age" not in case


# ── 7. 协议 11 字段 ─────────────────────────────────────────────────────────


def test_protocol_preregisters_eleven_fields() -> None:
    data = yaml.safe_load(PROTOCOL_PATH.read_text(encoding="utf-8"))
    assert set(data) == PROTOCOL_FIELDS
    assert data["protocol_id"] == "timing-k3-v1"
    assert data["frozen_at"] == model.FROZEN_AT
    assert re.fullmatch(r"[0-9a-f]{40}", str(data["commit"]))
    assert set(data["label_map"]) == {"event_year", "no_event_year"}
    assert "top3" in data["prediction_rule"]
    assert "K=3" in data["decision_rule"]
    assert "8pp" in data["decision_rule"] and "p < 0.01" in data["decision_rule"]
    assert "26.7%" in data["baseline"]
