"""tests/tools/test_timing_eval_v1.py · T-167 评测器测试

只用手工 fixture：不读 META/timing-scores-v1.json、不读真实评测集事件。
覆盖：
- 4 例手算（全中 / 全不中 / e=0 / 多事件年）：p_case、observed/expected、精确 Poisson-binomial p；
- 同 K 静态基线枚举（20–22 … 33–35）与并列取 lo 小；
- 敏感性剔除逻辑（T-168 矛盾名单 / clock_beijing / 边界警告 / 性别）；
- 确定性（两次运行逐字节一致、无时间戳/随机数）；
- 输入缺字段/覆盖不符 → 退出码 2。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools import timing_eval_v1 as te

BIRTH_YEAR = 2000
AGES = tuple(range(20, 36))
YEARS = tuple(BIRTH_YEAR + age for age in AGES)


# ── fixture 构造 ────────────────────────────────────────────────────────────


def eval_case(case_id: str, *, events=(), gender: str = "男", time_basis: str = "true_solar") -> dict:
    return {
        "case_id": case_id,
        "gender": gender,
        "birth_datetime_raw": "fixture",
        "birth_dt": "2000-01-01 00:00:00",
        "birth_year": BIRTH_YEAR,
        "birth_has_time": True,
        "time_basis": time_basis,
        "birth_source": "fixture",
        "calendar_type_raw": "solar",
        "marriage_events": [
            {
                "year": year,
                "age": year - BIRTH_YEAR,
                "age_plausible": True,
                "polarity": "unknown",
                "text": "fixture",
            }
            for year in events
        ],
        "usable_for_timing": True,
        "quality_grade": "B",
        "quality_flags": [],
        "duplicate_key": "fixture",
    }


def scores_case(case_id: str, score_by_year: dict[int, int] | None = None) -> dict:
    mapping = score_by_year or {}
    return {
        "case_id": case_id,
        "birth_year": BIRTH_YEAR,
        "years": [
            {
                "year": year,
                "score": mapping.get(year, 0),
                "components": {"r1": 0, "r2": 0, "r3": 0, "r4": 0},
                "edges": [],
                "flags": [],
            }
            for year in YEARS
        ],
    }


def eval_payload(cases) -> dict:
    return {"schema": "timing-eval-set/v1", "cases": list(cases)}


def scores_payload(cases) -> dict:
    return {
        "protocol_id": "fixture-k3",
        "frozen_at": "fixture",
        "git_head": "fixture",
        "population": {"usable_for_timing": len(cases)},
        "cases": list(cases),
    }


def write_json(path: Path, payload) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


# 4 例手算 fixture：全中 / 全不中 / e=0 / 多事件年。
def four_case_fixture():
    cases = [
        eval_case("A", events=[2020]),  # 全中：e=1，Top-3 含 2020
        eval_case("B", events=[2021]),  # 全不中：e=1，2021 被压到 Top-3 之外
        eval_case("C", events=[2019, 2036]),  # e=0：事件年全在窗口外
        eval_case("D", events=[2022, 2023, 2024, 2025]),  # 多事件年：e=4，Top-3 含 2024
    ]
    scores = [
        scores_case("A", {2020: 5}),
        scores_case("B", {year: (0 if year == 2021 else 1) for year in YEARS}),
        scores_case("C", {}),
        scores_case("D", {2024: 3}),
    ]
    return cases, scores


# ── 4 例手算 ────────────────────────────────────────────────────────────────


def test_four_case_hand_computed_values():
    cases, scores = four_case_fixture()
    report = te.build_report(
        eval_payload=eval_payload(cases),
        scores_payload=scores_payload(scores),
        eval_path="fixture/eval.json",
        scores_path="fixture/scores.json",
        contradicted=None,
        audit=None,
    )

    main = report["populations"][0]
    assert main["n"] == 4
    assert main["observed"] == 2
    # p_case: 3/16 + 3/16 + 0 + 17/28 = 55/56
    assert main["expected"] == pytest.approx(55 / 56, rel=1e-15)
    assert main["gates"]["observed_rate"] == pytest.approx(0.5)
    assert main["gates"]["expected_rate"] == pytest.approx(55 / 56 / 4)
    # 精确 Poisson-binomial：P(X>=2) = 1 - (1859 + 3731)/7168 = 1578/7168
    assert main["p_value"] == pytest.approx(1578 / 7168, rel=1e-12)
    # 差值 25.4pp 但 p=0.2201 > 0.20 → 按卡判死
    assert main["gates"]["diff_pp"] == pytest.approx(100 * 0.5 - 100 * (55 / 56 / 4))
    assert main["gates"]["verdict"] == "dead"

    ledger = {row["case_id"]: row for row in report["cases"]}
    assert ledger["A"]["e"] == 1 and ledger["A"]["hit"] is True
    assert ledger["A"]["p_case"] == pytest.approx(3 / 16, rel=1e-15)
    assert ledger["B"]["e"] == 1 and ledger["B"]["hit"] is False
    assert ledger["B"]["p_case"] == pytest.approx(3 / 16, rel=1e-15)
    assert ledger["C"]["e"] == 0 and ledger["C"]["hit"] is False
    assert ledger["C"]["p_case"] == 0.0
    assert ledger["D"]["e"] == 4 and ledger["D"]["hit"] is True
    assert ledger["D"]["p_case"] == pytest.approx(17 / 28, rel=1e-15)
    assert 2020 in ledger["A"]["top3"]
    assert 2021 not in ledger["B"]["top3"]
    assert 2024 in ledger["D"]["top3"]
    assert ledger["C"]["event_years"] == []
    assert report["e_distribution"] == {"0": 1, "1": 2, "4": 1}


def test_p_case_formula_values():
    assert te.p_case_for(0) == 0.0
    assert te.p_case_for(1) == pytest.approx(3 / 16)
    assert te.p_case_for(2) == pytest.approx(1 - 364 / 560)
    assert te.p_case_for(3) == pytest.approx(1 - 286 / 560)
    assert te.p_case_for(4) == pytest.approx(17 / 28)
    assert te.p_case_for(13) == pytest.approx(559 / 560)
    # 16-e < K 时任何 K 年都必含事件年
    assert te.p_case_for(14) == 1.0
    assert te.p_case_for(16) == 1.0


def test_poisson_binomial_exact_and_edges():
    probs = [3 / 16, 3 / 16, 0.0, 17 / 28]
    assert te.poisson_binomial_tail(probs, 0) == 1.0
    assert te.poisson_binomial_tail(probs, 2) == pytest.approx(1578 / 7168, rel=1e-13)
    # P(3 个非零全中) = 3/16 * 3/16 * 17/28 = 153/7168
    assert te.poisson_binomial_tail(probs, 3) == pytest.approx(153 / 7168, rel=1e-13)
    assert te.poisson_binomial_tail(probs, 4) == 0.0
    # 四个 0.5：P(X>=2) = 1 - 5/16 = 11/16
    assert te.poisson_binomial_tail([0.5] * 4, 2) == pytest.approx(11 / 16, rel=1e-15)


def test_wilson_lower_bound():
    low_zero, _ = te.wilson_interval(0, 382)
    assert low_zero == 0.0
    low_all, _ = te.wilson_interval(382, 382)
    assert low_all == pytest.approx(0.990044, abs=1e-5)
    low_102, high_102 = te.wilson_interval(102, 382)
    assert low_102 == pytest.approx(0.22513, abs=1e-4)
    assert low_102 < 102 / 382 < high_102
    assert te.wilson_interval(110, 382)[0] > low_102


# ── 排序 ────────────────────────────────────────────────────────────────────


def test_rank_top_uses_score_then_sha256():
    mapping = {year: 0 for year in reversed(YEARS)}
    top = te.rank_top("X", mapping)
    expected = sorted(
        YEARS, key=lambda year: hashlib.sha256(f"X|{year}".encode("utf-8")).hexdigest()
    )[:3]
    assert [year for year, _ in top] == expected
    # score 优先于 sha256
    assert te.rank_top("X", {2020: 2, 2021: 1})[0] == (2020, 2)


# ── 同 K 静态基线 ───────────────────────────────────────────────────────────


def test_static_baseline_enumerates_all_windows():
    cases = [
        {"birth_year": BIRTH_YEAR, "event_years": [2020]},
        {"birth_year": BIRTH_YEAR, "event_years": [2021]},
        {"birth_year": BIRTH_YEAR, "event_years": [2030]},
        {"birth_year": BIRTH_YEAR, "event_years": []},
    ]
    baseline = te.static_baseline(cases)
    assert [row["lo"] for row in baseline["table"]] == list(range(20, 34))
    assert all(row["hi"] == row["lo"] + 2 for row in baseline["table"])
    assert baseline["best"]["lo"] == 20
    assert baseline["best"]["hits"] == 2
    assert baseline["best"]["rate_pct"] == 50.0
    assert baseline["best"]["rate"] == max(row["rate"] for row in baseline["table"])


def test_static_baseline_tie_break_lowest_lo():
    cases = [{"birth_year": BIRTH_YEAR, "event_years": [2020, 2021]}]
    baseline = te.static_baseline(cases)
    assert baseline["table"][0]["hits"] == 1 and baseline["table"][1]["hits"] == 1
    assert baseline["best"]["lo"] == 20


def test_report_static_baseline_is_not_seven_year_band():
    cases, scores = four_case_fixture()
    report = te.build_report(
        eval_payload=eval_payload(cases),
        scores_payload=scores_payload(scores),
        eval_path="fixture/eval.json",
        scores_path="fixture/scores.json",
        contradicted=None,
        audit=None,
    )
    block = report["static_baseline"]
    assert block["k"] == 3
    assert len(block["table"]) == 14
    assert block["best"]["hits"] == max(row["hits"] for row in block["table"])
    assert block["best"]["rate"] == max(row["rate"] for row in block["table"])
    assert block["best"]["lo"] == 20 and block["best"]["rate_pct"] == 75.0
    assert "45.3%" in block["seven_year_band_note"]
    assert block["reference_t165_pct"] == 26.7


# ── 判定阈值 ────────────────────────────────────────────────────────────────


def test_classify_thresholds():
    signal_above = te.classify(
        n=382, observed=120, expected=68.84, p_value=1e-6, wilson_low=0.27, baseline_rate=0.267
    )
    assert signal_above["signal"] is True
    assert signal_above["practical_gate"] is True
    assert signal_above["verdict"] == "signal_above_static_baseline"

    signal_below = te.classify(
        n=382, observed=120, expected=68.84, p_value=1e-6, wilson_low=0.26, baseline_rate=0.267
    )
    assert signal_below["verdict"] == "signal_below_static_baseline"

    # 恰好 +8.0pp 且 p<0.01 → 信号
    boundary_signal = te.classify(
        n=100, observed=28, expected=20.0, p_value=0.0099, wilson_low=0.19, baseline_rate=0.1
    )
    assert boundary_signal["diff_pp"] == 8.0
    assert boundary_signal["signal"] is True

    # p 恰为 0.01 不算 < 0.01
    just_over = te.classify(
        n=100, observed=28, expected=20.0, p_value=0.01, wilson_low=0.19, baseline_rate=0.1
    )
    assert just_over["signal"] is False
    assert just_over["kill"] is False
    assert just_over["verdict"] == "inconclusive"

    # 差值 7.0pp → 不够信号，也不到判死
    seven_pp = te.classify(
        n=100, observed=27, expected=20.0, p_value=0.005, wilson_low=0.19, baseline_rate=0.1
    )
    assert seven_pp["signal"] is False
    assert seven_pp["verdict"] == "inconclusive"

    # 差值 < +3pp → 判死
    dead_diff = te.classify(
        n=100, observed=22, expected=20.0, p_value=0.9, wilson_low=0.12, baseline_rate=0.1
    )
    assert dead_diff["kill"] is True
    assert dead_diff["verdict"] == "dead"

    # 差值 3.0pp 但 p 0.2001 > 0.20 → 判死
    dead_p = te.classify(
        n=100, observed=23, expected=20.0, p_value=0.2001, wilson_low=0.16, baseline_rate=0.1
    )
    assert dead_p["kill"] is True
    assert dead_p["verdict"] == "dead"

    # p 恰为 0.20 不算 > 0.20
    at_kill_p = te.classify(
        n=100, observed=23, expected=20.0, p_value=0.20, wilson_low=0.16, baseline_rate=0.1
    )
    assert at_kill_p["kill"] is False
    assert at_kill_p["verdict"] == "inconclusive"


# ── 敏感性 ──────────────────────────────────────────────────────────────────


def sensitivity_fixture():
    cases = [
        eval_case("s1", events=[2020], gender="男", time_basis="true_solar"),
        eval_case("s2", events=[2021], gender="女", time_basis="clock_beijing"),
        eval_case("s3", events=[2022], gender="男", time_basis="true_solar"),
        eval_case("s4", events=[], gender="女", time_basis="true_solar"),
        eval_case("s5", events=[2023, 2024], gender="男", time_basis="clock_beijing"),
        eval_case("s6", events=[2025], gender="男", time_basis="true_solar"),
    ]
    scores = [
        scores_case("s1", {2020: 5}),
        scores_case("s2", {year: (0 if year == 2021 else 1) for year in YEARS}),
        scores_case("s3", {2022: 5}),
        scores_case("s4", {}),
        scores_case("s5", {2023: 5}),
        scores_case("s6", {2025: 5}),
    ]
    audit = {
        "per_case_coverage": [
            {"case_id": "s1", "boundary_warnings": []},
            {"case_id": "s2", "boundary_warnings": []},
            {"case_id": "s3", "boundary_warnings": ["late_zi"]},
            {"case_id": "s4", "boundary_warnings": []},
            {"case_id": "s5", "boundary_warnings": []},
            {"case_id": "s6", "boundary_warnings": []},
        ]
    }
    contradicted = {
        "schema": "timing-event-year-audit/v1",
        "sensitivity": {"sensitivity_exclude": ["s6"]},
    }
    return cases, scores, audit, contradicted


def test_sensitivity_subsets():
    cases, scores, audit, contradicted = sensitivity_fixture()
    report = te.build_report(
        eval_payload=eval_payload(cases),
        scores_payload=scores_payload(scores),
        eval_path="fixture/eval.json",
        scores_path="fixture/scores.json",
        contradicted=("fixture/contradicted.json", contradicted),
        audit=("fixture/audit.json", audit),
    )
    populations = {row["name"]: row for row in report["populations"]}
    assert [row["name"] for row in report["populations"]] == [
        "all",
        "labeled",
        "exclude_contradicted",
        "exclude_clock_beijing",
        "exclude_boundary_warnings",
        "male",
        "female",
    ]

    assert populations["all"]["n"] == 6
    assert populations["all"]["observed"] == 4
    assert populations["labeled"]["n"] == 5
    assert populations["labeled"]["observed"] == 4
    assert populations["labeled"]["e_zero_cases"] == 0

    assert populations["exclude_contradicted"]["n"] == 5
    assert populations["exclude_contradicted"]["observed"] == 3
    assert populations["exclude_contradicted"]["excluded"] == 1
    assert populations["exclude_contradicted"]["excluded_unknown_case_ids"] == []
    assert "s6" not in populations["exclude_contradicted"]["case_ids"]

    assert populations["exclude_clock_beijing"]["n"] == 4
    assert populations["exclude_clock_beijing"]["excluded"] == 2
    # 剩下 s1/s3/s4/s6：s1、s3、s6 命中
    assert populations["exclude_clock_beijing"]["observed"] == 3

    assert populations["exclude_boundary_warnings"]["n"] == 5
    assert populations["exclude_boundary_warnings"]["excluded"] == 1
    assert "s3" not in populations["exclude_boundary_warnings"]["case_ids"]

    assert populations["male"]["n"] == 4
    assert populations["male"]["observed"] == 4
    assert populations["female"]["n"] == 2
    assert populations["female"]["observed"] == 0


def test_sensitivity_unavailable_without_sidecars():
    cases, scores, _, _ = sensitivity_fixture()
    report = te.build_report(
        eval_payload=eval_payload(cases),
        scores_payload=scores_payload(scores),
        eval_path="fixture/eval.json",
        scores_path="fixture/scores.json",
        contradicted=None,
        audit=None,
    )
    populations = {row["name"]: row for row in report["populations"]}
    assert populations["exclude_contradicted"]["status"] == "unavailable"
    assert populations["exclude_boundary_warnings"]["status"] == "unavailable"
    assert report["inputs"]["contradicted"] is None
    assert report["inputs"]["feasibility_audit"] is None


def test_contradicted_loader_accepts_documented_shapes():
    assert te.load_contradicted(["c", "c", "a"]) == ["a", "c"]
    assert te.load_contradicted({"sensitivity_exclude": ["a"]}) == ["a"]
    assert te.load_contradicted({"sensitivity": {"sensitivity_exclude": ["b"]}}) == ["b"]
    assert te.load_contradicted([{"case_id": "d"}]) == ["d"]
    with pytest.raises(te.InputError):
        te.load_contradicted({"sensitivity": {}})


def test_contradicted_list_accepts_plain_ids_and_ignores_unknown():
    cases, scores, audit, _ = sensitivity_fixture()
    report = te.build_report(
        eval_payload=eval_payload(cases),
        scores_payload=scores_payload(scores),
        eval_path="fixture/eval.json",
        scores_path="fixture/scores.json",
        contradicted=("fixture/contradicted.json", ["s2", "not-a-real-case"]),
        audit=("fixture/audit.json", audit),
    )
    populations = {row["name"]: row for row in report["populations"]}
    assert populations["exclude_contradicted"]["n"] == 5
    assert populations["exclude_contradicted"]["excluded_unknown_case_ids"] == ["not-a-real-case"]
    assert "s2" not in populations["exclude_contradicted"]["case_ids"]


# ── CLI / 确定性 / 退出码 ───────────────────────────────────────────────────


def _cli_fixture(tmp_path: Path) -> tuple[Path, Path]:
    cases, scores = four_case_fixture()
    eval_path = write_json(tmp_path / "eval.json", eval_payload(cases))
    scores_path = write_json(tmp_path / "scores.json", scores_payload(scores))
    return eval_path, scores_path


def test_cli_writes_report_and_is_deterministic(tmp_path, capsys):
    eval_path, scores_path = _cli_fixture(tmp_path)
    out = tmp_path / "report"
    argv = ["--scores", str(scores_path), "--eval-set", str(eval_path), "--out", str(out)]

    assert te.main(argv) == 0
    json_first = (tmp_path / "report.json").read_bytes()
    md_first = (tmp_path / "report.md").read_bytes()
    assert json_first and md_first

    assert te.main(argv) == 0
    assert (tmp_path / "report.json").read_bytes() == json_first
    assert (tmp_path / "report.md").read_bytes() == md_first

    payload = json.loads(json_first.decode("utf-8"))
    assert payload["schema"] == "timing-k3-report/v1"
    assert "generated_at" not in payload
    assert payload["determinism"]["random"] is False
    assert payload["determinism"]["timestamp"] is False
    assert payload["cases"][0]["case_id"] == "A"
    md_text = md_first.decode("utf-8")
    assert "同 K 静态基线" in md_text
    assert "45.3%" in md_text
    capsys.readouterr()


def test_cli_json_flag_prints_pure_report(tmp_path, capsys):
    eval_path, scores_path = _cli_fixture(tmp_path)
    argv = [
        "--scores", str(scores_path),
        "--eval-set", str(eval_path),
        "--out", str(tmp_path / "report"),
        "--json",
    ]
    assert te.main(argv) == 0
    stdout = capsys.readouterr().out
    payload = json.loads(stdout)
    assert payload["schema"] == "timing-k3-report/v1"


def test_module_has_no_random_or_timestamp():
    source = Path(te.__file__).read_text(encoding="utf-8")
    assert "import random" not in source
    assert "time.time" not in source
    assert "generated_at" not in source


def test_cli_missing_scores_file_exits_2(tmp_path, capsys):
    eval_path, _ = _cli_fixture(tmp_path)
    assert te.main(["--scores", str(tmp_path / "nope.json"), "--eval-set", str(eval_path)]) == 2
    capsys.readouterr()


def test_cli_scores_missing_cases_exits_2(tmp_path, capsys):
    eval_path, _ = _cli_fixture(tmp_path)
    bad = write_json(tmp_path / "bad.json", {"protocol_id": "x"})
    assert te.main(["--scores", str(bad), "--eval-set", str(eval_path)]) == 2
    capsys.readouterr()


def test_cli_missing_case_exits_2(tmp_path, capsys):
    cases, scores = four_case_fixture()
    eval_path = write_json(tmp_path / "eval.json", eval_payload(cases))
    scores_path = write_json(tmp_path / "scores.json", scores_payload(scores[:-1]))
    assert te.main(["--scores", str(scores_path), "--eval-set", str(eval_path)]) == 2
    capsys.readouterr()


def test_cli_extra_case_exits_2(tmp_path, capsys):
    cases, scores = four_case_fixture()
    eval_path = write_json(tmp_path / "eval.json", eval_payload(cases))
    scores_path = write_json(tmp_path / "scores.json", scores_payload(scores + [scores_case("Z")]))
    assert te.main(["--scores", str(scores_path), "--eval-set", str(eval_path)]) == 2
    capsys.readouterr()


def test_cli_incomplete_years_exits_2(tmp_path, capsys):
    cases, scores = four_case_fixture()
    eval_path = write_json(tmp_path / "eval.json", eval_payload(cases))
    truncated = json.loads(json.dumps(scores_payload(scores)))
    truncated["cases"][0]["years"] = truncated["cases"][0]["years"][:-1]
    scores_path = write_json(tmp_path / "scores.json", truncated)
    assert te.main(["--scores", str(scores_path), "--eval-set", str(eval_path)]) == 2
    capsys.readouterr()


def test_cli_birth_year_mismatch_exits_2(tmp_path, capsys):
    cases, scores = four_case_fixture()
    eval_path = write_json(tmp_path / "eval.json", eval_payload(cases))
    payload = json.loads(json.dumps(scores_payload(scores)))
    payload["cases"][0]["birth_year"] = BIRTH_YEAR + 1
    scores_path = write_json(tmp_path / "scores.json", payload)
    assert te.main(["--scores", str(scores_path), "--eval-set", str(eval_path)]) == 2
    capsys.readouterr()


def test_cli_years_outside_window_exits_2(tmp_path, capsys):
    cases, scores = four_case_fixture()
    eval_path = write_json(tmp_path / "eval.json", eval_payload(cases))
    payload = json.loads(json.dumps(scores_payload(scores)))
    payload["cases"][0]["years"][0]["year"] = BIRTH_YEAR + 19  # 19 岁不在候选窗
    scores_path = write_json(tmp_path / "scores.json", payload)
    assert te.main(["--scores", str(scores_path), "--eval-set", str(eval_path)]) == 2
    capsys.readouterr()


def test_cli_eval_set_without_cases_exits_2(tmp_path, capsys):
    _, scores = four_case_fixture()
    eval_path = write_json(tmp_path / "eval.json", {"schema": "timing-eval-set/v1"})
    scores_path = write_json(tmp_path / "scores.json", scores_payload(scores))
    assert te.main(["--scores", str(scores_path), "--eval-set", str(eval_path)]) == 2
    capsys.readouterr()


def test_cli_explicit_missing_audit_exits_2(tmp_path, capsys):
    eval_path, scores_path = _cli_fixture(tmp_path)
    argv = [
        "--scores", str(scores_path),
        "--eval-set", str(eval_path),
        "--audit", str(tmp_path / "missing-audit.json"),
    ]
    assert te.main(argv) == 2
    capsys.readouterr()
