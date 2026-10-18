# -*- coding: utf-8 -*-
"""盲测工具链回归测试。

只测 tools/ 下五个盲测工具的行为，不修改被测工具。
被测模块用模块级常量（CASES/PROBES/OUT）定位目录，测试用 monkeypatch
把它们指到 tmp_path 下的临时目录，不依赖真实 cases/。
"""
from __future__ import annotations

import importlib
import json
import random
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[2] / "tools"
if str(TOOLS.parent) not in sys.path:
    sys.path.insert(0, str(TOOLS.parent))

bp = importlib.import_module("tools.blind_year_probe")
bs = importlib.import_module("tools.blind_year_score")
bcp = importlib.import_module("tools.blind_candidate_pick")
vj = importlib.import_module("tools.verify_year_judgments")
beg = importlib.import_module("tools.blind_exam_generator")


# ────────────────────────── 工具函数 ──────────────────────────

def _make_case(cases_root: Path, case: str, feedback_rows: list[tuple[int, str, str]],
               birth: str | None = "1980-02-15") -> Path:
    d = cases_root / case
    d.mkdir(parents=True, exist_ok=True)
    if birth is not None:
        (d / "input.md").write_text(f'公历: "{birth} 02:30"\n', encoding="utf-8")
    if feedback_rows is not None:
        lines = ["| 年份 | 已知事实 | 功能域 |", "|---|---|---|"]
        for y, text, dom in feedback_rows:
            lines.append(f"| {y} | {text} | {dom} |")
        (d / "feedback.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return d


def _mk_facts(case_dir: Path, mode="birth", boundary=False, fallback=False) -> None:
    d = case_dir / "facts"
    d.mkdir(parents=True, exist_ok=True)
    (d / "facts_summary.json").write_text(json.dumps({
        "mode": mode,
        "boundary_warnings": ["x"] if boundary else [],
        "fallback_from_birth": fallback,
    }, ensure_ascii=False), encoding="utf-8")


def _feedback(n: int, start=2000) -> list[tuple[int, str, str]]:
    """生成 n 条中性事件行（关键词互不触发吉凶计票）。"""
    out = []
    for i in range(n):
        out.append((start + i, f"甲辰年事{i}件", "其他"))
    return out


@pytest.fixture()
def probe_env(tmp_path, monkeypatch):
    """blind_year_probe / verify_year_judgments 的临时目录环境。"""
    cases = tmp_path / "cases"
    probes = tmp_path / "year-probes"
    out = tmp_path / "probe-out"
    cases.mkdir(); probes.mkdir()
    monkeypatch.setattr(bp, "CASES", cases)
    monkeypatch.setattr(bp, "OUT", out)
    monkeypatch.setattr(vj, "PROBES", probes)
    monkeypatch.setattr(bs, "CASES", cases)
    monkeypatch.setattr(bs, "PROBES", probes)
    monkeypatch.setattr(bcp, "CASES", cases)
    monkeypatch.setattr(bcp, "PROBES", probes)
    monkeypatch.setattr(beg, "CASES", cases)
    monkeypatch.setattr(beg, "OUT", tmp_path / "exams")
    return {"cases": cases, "probes": probes, "out": out, "tmp": tmp_path}


# ─────────────────── blind_year_probe._detect_columns ───────────────────

def test_detect_columns_format_a_text_1_domain_2():
    # 格式 A: 年份|已知事实|功能域 → 文本=1, 域=2
    assert bp._detect_columns("| 年份 | 已知事实 | 功能域 |") == (1, 2)


def test_detect_columns_format_b_swapped():
    # 格式 B: 年份|类型|事实摘录 → 域=1, 文本=2
    assert bp._detect_columns("| 年份 | 类型 | 事实摘录 |") == (2, 1)


def test_detect_columns_unrecognized_defaults_to_a():
    # 无法识别时按 A 处理
    assert bp._detect_columns("| 年份 | 甲 | 乙 |") == (1, 2)


# ─────────────────────── blind_year_probe.classify ───────────────────────

def test_classify_prefix_xun_beats_keywords():
    # 前缀「凶,」优先于正文关键词计票（正文全是吉词也不能翻盘）
    assert bp.classify("凶,升职加薪结婚顺利得奖") == "negative"


def test_classify_prefix_ji_beats_keywords():
    assert bp.classify("吉,破财欠债离职离婚") == "positive"


def test_classify_keyword_vote_negative():
    assert bp.classify("这年破财又欠债") == "negative"


def test_classify_keyword_vote_positive():
    assert bp.classify("这年结婚买房顺利") == "positive"


def test_classify_no_signal_returns_mixed():
    assert bp.classify("甲辰年有些变动") == "mixed"


# ────────────────────── blind_year_probe.load_events ──────────────────────

def test_load_events_parses_rows_and_sorts_by_year(probe_env):
    _make_case(probe_env["cases"], "C1", [(2015, "吉,升职", "career"), (2001, "凶,破财", "wealth")])
    evs = bp.load_events("C1")
    assert [e["year"] for e in evs] == [2001, 2015]
    assert evs[0]["polarity"] == "negative"
    assert evs[1]["domains"] == ["career"]


def test_load_events_missing_feedback_returns_empty(probe_env):
    assert bp.load_events("NOPE") == []


def test_load_events_format_b_takes_fact_column(probe_env):
    d = probe_env["cases"] / "C2"
    d.mkdir(parents=True)
    (d / "feedback.md").write_text(
        "| 年份 | 类型 | 事实摘录 |\n|---|---|---|\n"
        "| 2010 | 其他 | 吉,生子 |\n",
        encoding="utf-8")
    evs = bp.load_events("C2")
    # 文本列=2，不应取到「其他」这种类型标签
    assert evs[0]["text"] == "吉,生子"
    assert evs[0]["polarity"] == "positive"


# ───────────── blind_exam_generator.pick_exam_years（在 beg 中） ─────────────

def test_pick_exam_years_quiet_years_exclude_recorded_years():
    events = [{"year": 2000 + i, "text": "甲年事件"} for i in range(6)]  # 2000-2005
    rng = random.Random(1)
    res = beg.pick_exam_years(events, rng)
    # quiet 必须落在事件跨度内且不与记录年重叠
    recorded = {e["year"] for e in events}
    for y in res["quiet"]:
        assert y not in recorded
        assert 2000 <= y <= 2003  # safe_hi = 2005-2


def test_pick_exam_years_empty_events_returns_empty():
    assert beg.pick_exam_years([], random.Random(1)) == {}


# ─────────────────── blind_year_score.canon_polarity ───────────────────

@pytest.mark.parametrize("raw,expected", [
    ("吉", "positive"), ("凶", "negative"), ("平", "neutral"),
    ("positive", "positive"), ("negative", "negative"), ("neutral", "neutral"),
    ("不利", "negative"), ("有利", "positive"), ("无大事", "neutral"),
])
def test_canon_polarity_accepts_chinese_and_english(raw, expected):
    assert bs.canon_polarity(raw) == expected


def test_canon_polarity_unknown_string():
    assert bs.canon_polarity("???") == "unknown"


# ────────────── blind_year_score._same_person_groups（临时目录） ──────────────

def test_same_person_groups_same_birthdate_grouped(tmp_path, probe_env):
    cases = probe_env["cases"]
    for name in ("CA", "CB", "CC"):
        (probe_env["probes"] / name).mkdir(parents=True, exist_ok=True)
    _make_case(cases, "CA", _feedback(3), birth="1980-02-15")
    _make_case(cases, "CB", _feedback(3), birth="1980-02-15")
    _make_case(cases, "CC", _feedback(3), birth="1990-01-01")
    groups = bs._same_person_groups(probe_env["probes"])
    assert set(groups.keys()) == {"1980-02-15"}
    assert sorted(groups["1980-02-15"]) == ["CA", "CB"]


def test_same_person_groups_singletons_not_returned(tmp_path, probe_env):
    cases = probe_env["cases"]
    (probe_env["probes"] / "CA").mkdir(parents=True, exist_ok=True)
    _make_case(cases, "CA", _feedback(3), birth="1980-02-15")
    assert bs._same_person_groups(probe_env["probes"]) == {}


# ─────────────────── blind_year_score.score_case 对照年 ───────────────────

def test_score_case_control_year_undetermined_not_in_denominator(probe_env):
    case = "C1"
    _make_case(probe_env["cases"], case, [(2000, "凶,破财", "wealth")])
    probe_dir = probe_env["probes"] / case
    probe_dir.mkdir(parents=True)
    # probe_years 含一个记录年 2000 和一个对照年 2001
    (probe_dir / "answer_key.json").write_text(json.dumps({
        "case_id": case,
        "probe_years": [2000, 2001],
        "truth": {
            "2000": {"polarity": "negative", "matters": [], "events": ["凶,破财"], "recorded": True},
            "2001": {"polarity": "undetermined", "matters": [], "events": [], "recorded": False},
        },
    }, ensure_ascii=False), encoding="utf-8")
    (probe_dir / "year_judgments.json").write_text(json.dumps({
        "year_judgments": [
            {"year": 2000, "polarity": "凶", "matters": [], "basis": "e001 子午冲"},
            {"year": 2001, "polarity": "凶", "matters": [], "basis": "e002 寅申冲"},
        ],
    }, ensure_ascii=False), encoding="utf-8")
    r = bs.score_case(case)
    # 记录年判对；对照年判凶只记误报，不进 incorrect 分母
    assert r["correct"] == 1
    assert r["incorrect"] == 0
    assert r["control_false_positive"] == 1
    assert r["control_years"] == 1


# ─────────────────── blind_candidate_pick.tier_of ───────────────────

@pytest.mark.parametrize("n,expected", [
    (7, "high"), (10, "high"), (6, "mid"), (4, "mid"), (3, "low"),
    (2, "insufficient"), (0, "insufficient"),
])
def test_tier_of_boundaries(n, expected):
    assert bcp.tier_of(n) == expected


# ─────────────────── blind_candidate_pick.pick ───────────────────

def _rows(spec: dict[str, int]) -> list[dict]:
    out = []
    for tier, n in spec.items():
        for i in range(n):
            out.append({"case": f"{tier}-{i}", "events_tier": tier, "n_events": 3})
    return out


def test_pick_balanced_quota_across_tiers():
    rows = _rows({"high": 5, "mid": 5, "low": 5})
    chosen = bcp.pick(rows, 9, seed=1)
    tiers = [c["events_tier"] for c in chosen]
    assert tiers.count("high") == 3
    assert tiers.count("mid") == 3
    assert tiers.count("low") == 3


def test_pick_backfills_when_tier_short():
    # high 只有 1 例，count=6 → high 1 例，剩余由其他层回填
    rows = _rows({"high": 1, "mid": 5, "low": 5})
    chosen = bcp.pick(rows, 6, seed=2)
    assert len(chosen) == 6
    assert len({c["case"] for c in chosen}) == 6  # 无重复


def test_pick_seed_deterministic():
    rows = _rows({"high": 5, "mid": 5, "low": 5})
    a = [c["case"] for c in bcp.pick(rows, 6, seed=42)]
    b = [c["case"] for c in bcp.pick(rows, 6, seed=42)]
    assert a == b


# ─────────────── blind_candidate_pick.collect_candidates（临时目录） ───────────────

def test_collect_candidates_excludes_already_done(probe_env):
    d = _make_case(probe_env["cases"], "C-2026-RF-A-1", _feedback(5))
    _mk_facts(d)
    probe_dir = probe_env["probes"] / d.name
    probe_dir.mkdir(parents=True)
    (probe_dir / "year_judgments.json").write_text("{}", encoding="utf-8")
    rows, exc = bcp.collect_candidates()
    assert rows == []
    assert exc.get("already_done") == 1


def test_collect_candidates_excludes_non_birth_mode(probe_env):
    d = _make_case(probe_env["cases"], "C-2026-RF-B-1", _feedback(5))
    _mk_facts(d, mode="pillar")
    rows, exc = bcp.collect_candidates()
    assert rows == []
    assert exc.get("not_birth_mode") == 1


def test_collect_candidates_excludes_boundary_warning(probe_env):
    d = _make_case(probe_env["cases"], "C-2026-RF-C-1", _feedback(5))
    _mk_facts(d, boundary=True)
    rows, exc = bcp.collect_candidates()
    assert rows == []
    assert exc.get("boundary_warning") == 1


def test_collect_candidates_excludes_fallback(probe_env):
    d = _make_case(probe_env["cases"], "C-2026-RF-D-1", _feedback(5))
    _mk_facts(d, fallback=True)
    rows, exc = bcp.collect_candidates()
    assert rows == []
    assert exc.get("fallback_birth") == 1


def test_collect_candidates_excludes_insufficient_events(probe_env):
    d = _make_case(probe_env["cases"], "C-2026-RF-E-1", _feedback(2))
    _mk_facts(d)
    rows, exc = bcp.collect_candidates()
    assert rows == []
    assert exc.get("events_lt_3") == 1


def test_collect_candidates_dedups_same_birth_date(probe_env):
    cases = probe_env["cases"]
    d1 = _make_case(cases, "C-2026-RF-F-1", _feedback(5), birth="1980-02-15")
    d2 = _make_case(cases, "C-2026-RF-F-2", _feedback(4), birth="1980-02-15")
    _mk_facts(d1); _mk_facts(d2)
    rows, exc = bcp.collect_candidates()
    # 排序在前者保留，后者按同人去重排除
    assert [r["case"] for r in rows] == ["C-2026-RF-F-1"]
    assert exc.get("same_person_dup") == 1


def test_collect_candidates_accepts_valid_case(probe_env):
    d = _make_case(probe_env["cases"], "C-2026-RF-G-1", _feedback(5), birth="1985-06-01")
    _mk_facts(d)
    rows, exc = bcp.collect_candidates()
    assert len(rows) == 1
    assert rows[0]["events_tier"] == "mid"
    assert rows[0]["birth_date"] == "1985-06-01"
    assert exc == {} or not any(v for v in exc.values())


# ─────────────────── verify_year_judgments.verify_case ───────────────────

def _write_probe(probe_env, case, years):
    probe_dir = probe_env["probes"] / case
    probe_dir.mkdir(parents=True, exist_ok=True)
    body = "\n".join([
        "# 题面", "",
        f"- 需要判断的年份共 {len(years)} 个：{'、'.join(str(y) for y in years)}", "",
    ])
    (probe_dir / "probe.md").write_text(body, encoding="utf-8")


def _write_answer(probe_env, case, judgments):
    probe_dir = probe_env["probes"] / case
    (probe_dir / "year_judgments.json").write_text(
        json.dumps({"year_judgments": judgments}, ensure_ascii=False), encoding="utf-8")


def test_verify_passes_fully_valid_answer(probe_env):
    _write_probe(probe_env, "C1", [2000, 2001])
    _write_answer(probe_env, "C1", [
        {"year": 2000, "polarity": "吉", "matters": ["career"], "basis": "e005 寅午半合火局成"},
        {"year": 2001, "polarity": "平", "matters": [], "basis": "M.b 月支伏吟"},
    ])
    ok, issues = vj.verify_case("C1")
    assert ok, issues


def test_verify_fails_on_missing_year(probe_env):
    _write_probe(probe_env, "C1", [2000, 2001])
    _write_answer(probe_env, "C1", [
        {"year": 2000, "polarity": "吉", "matters": ["career"], "basis": "e005 寅午合"},
    ])
    ok, issues = vj.verify_case("C1")
    assert not ok
    assert any("缺失年份" in i for i in issues)


def test_verify_fails_on_extra_year(probe_env):
    _write_probe(probe_env, "C1", [2000])
    _write_answer(probe_env, "C1", [
        {"year": 2000, "polarity": "吉", "matters": ["career"], "basis": "e005 寅午合"},
        {"year": 2010, "polarity": "吉", "matters": ["career"], "basis": "e006 卯酉冲"},
    ])
    ok, issues = vj.verify_case("C1")
    assert not ok
    assert any("多余年份" in i for i in issues)


def test_verify_fails_on_illegal_polarity(probe_env):
    _write_probe(probe_env, "C1", [2000])
    _write_answer(probe_env, "C1", [
        {"year": 2000, "polarity": "中", "matters": ["career"], "basis": "e005 寅午合"},
    ])
    ok, issues = vj.verify_case("C1")
    assert not ok
    assert any("polarity" in i for i in issues)


def test_verify_fails_on_basis_without_reference(probe_env):
    _write_probe(probe_env, "C1", [2000])
    _write_answer(probe_env, "C1", [
        {"year": 2000, "polarity": "吉", "matters": ["career"], "basis": "这年运势很好"},
    ])
    ok, issues = vj.verify_case("C1")
    assert not ok
    assert any("未引用边号" in i for i in issues)


def test_verify_fails_on_hedge_word_in_basis(probe_env):
    _write_probe(probe_env, "C1", [2000])
    _write_answer(probe_env, "C1", [
        {"year": 2000, "polarity": "吉", "matters": ["career"], "basis": "e005 可能寅午合火"},
    ])
    ok, issues = vj.verify_case("C1")
    assert not ok
    assert any("骑墙词" in i for i in issues)


# ─────────────────── blind_exam_generator 种子确定性 ───────────────────

def test_exam_generator_same_case_id_same_output(probe_env):
    _make_case(probe_env["cases"], "C1", [
        (2000, "凶,离职", "career"),
        (2001, "吉,升学读大学", "education"),
        (2002, "甲年事件", "其他"),
        (2003, "吉,结婚生子", "marriage"),
        (2004, "凶,破财", "wealth"),
    ])
    assert beg.generate("C1")
    exam1 = (beg.OUT / "C1" / "exam.md").read_text(encoding="utf-8")
    key1 = (beg.OUT / "C1" / "answer_key.json").read_text(encoding="utf-8")
    # 覆盖重生成
    assert beg.generate("C1")
    exam2 = (beg.OUT / "C1" / "exam.md").read_text(encoding="utf-8")
    key2 = (beg.OUT / "C1" / "answer_key.json").read_text(encoding="utf-8")
    assert exam1 == exam2
    assert key1 == key2
