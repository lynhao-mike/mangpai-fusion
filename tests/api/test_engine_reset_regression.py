"""引擎重设回归：旧引擎 6 大失真场景不得再出现。"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

from engine.api import analyze_facts, build_chart
from engine.facts.relation_graph import muku_at
from engine.facts.types import ChartFacts, RelationGraph
from engine.predicates.cycles import (
    CycleOutOfRange,
    PreQiyun,
    ganzhi_at,
    get_dayun_at_age,
    get_dayun_at_year,
)
from engine.predicates.types import Dayun, DayunStep, GanZhi

ROOT = Path(__file__).resolve().parents[2]


def _items(structure: dict) -> dict:
    return {item["id"]: item for item in structure["items"]}


def _dayun() -> Dayun:
    steps = [
        DayunStep(
            序号=i + 1,
            干支=GanZhi.parse(gz),
            起岁=8 + 10 * i,
            止岁=17 + 10 * i,
            起讫年=(1988 + 10 * i, 1998 + 10 * i),
        )
        for i, gz in enumerate(["己卯", "庚辰", "辛巳"])
    ]
    return Dayun(起运岁=8.5, 起运年=1988, 顺逆="顺", 排布=steps)


# ── 1. 排盘边界与流年立春切分 ───────────────────────────────────────────────

def test_late_zi_boundary_and_alt_chart_id():
    chart = build_chart(birth_dt="2024-01-10 23:30", gender="乾")
    assert isinstance(chart, ChartFacts)
    assert any(w.kind == "late_zi" for w in chart.boundary_warnings)
    variants = [v for v in chart.variants if v.axis == "zi_shi"]
    assert len(variants) == 1
    assert variants[0].alt_chart_id and variants[0].alt_chart_id != chart.chart_id


def test_ganzhi_at_splits_liunian_on_lichun():
    assert [str(x) for x in ganzhi_at(datetime(2024, 2, 4, 16, 0))] == ["癸卯", "乙丑"]
    assert [str(x) for x in ganzhi_at(datetime(2024, 2, 4, 17, 0))] == ["甲辰", "丙寅"]


def test_get_dayun_at_age_raises_pre_qiyun_and_out_of_range():
    dy = _dayun()
    with pytest.raises(PreQiyun):
        get_dayun_at_age(dy, 5)
    with pytest.raises(CycleOutOfRange):
        get_dayun_at_age(dy, 60)
    with pytest.raises(CycleOutOfRange):
        get_dayun_at_year(dy, 1980, 2030)


# ── 2. 人元司令与根气无二次打折 ─────────────────────────────────────────────

def test_siling_and_tou_same_wuxing_are_integers_without_discount():
    solar = analyze_facts(birth_dt="2024-10-11 12:00", gender="乾")
    siling = solar["strength"]["day_master"]["siling"]
    assert siling["commanding_stem"] == "辛"
    assert siling["source_ref"].endswith("《三命通会》.md:14")

    payload = analyze_facts(pillars=["甲子", "丙寅", "丙寅", "庚寅"], gender="乾")
    strength = payload["strength"]
    assert strength["day_master"]["tou_same_wuxing"] == ["M.s"]
    assert strength["stems"]["M.s"]["tou_same_wuxing"] == ["D.s"]
    for facts in [strength["day_master"], *strength["stems"].values()]:
        assert facts["addr"] not in facts.get("tou_same_wuxing", [])
    for layered in [*strength["camp_counts"].values(), *strength["climate"]["wuxing_layered"].values()]:
        for key in ("stems", "main_qi", "mid_qi", "residual_qi"):
            assert isinstance(layered[key], int)
            assert layered[key] != pytest.approx(0.09)


# ── 3. 墓库精准开闭与任派五细则 ─────────────────────────────────────────────

def test_muku_openers_only_when_ku_itself_is_chong_or_xing():
    from engine.facts import build_relation_graph, chart_from_pillars

    # 丑未相冲，但未冲到辰墓本身 → 辰.openers 为空
    g: RelationGraph = build_relation_graph(chart_from_pillars(["甲辰", "乙亥", "丁丑", "丁未"], "乾"))
    chen = muku_at(g, "Y.b")
    assert chen.openers == ()
    for addr in ("D.b", "H.b"):
        cand = next(c for c in chen.candidates if c.addr == addr)
        assert cand.excluded and any("不论入墓" == h.effect for h in cand.rule_hits)

    # 只有冲到墓支本身才进 openers
    g2 = build_relation_graph(chart_from_pillars(["壬子", "壬子", "壬辰", "庚戌"], "乾"))
    chong = next(e for e in g2.edges if e.kind == "chong" and set(e.members) == {"D.b", "H.b"})
    assert chong.id in muku_at(g2, "D.b").openers
    assert chong.id in muku_at(g2, "H.b").openers

    # 丑未辰齐见：因丑未冲，丑未不入辰墓
    g3 = build_relation_graph(chart_from_pillars(["戊辰", "己未", "己丑", "丁卯"], "乾"))
    chen3 = muku_at(g3, "Y.b")
    for addr in ("M.b", "D.b"):
        cand = next(c for c in chen3.candidates if c.addr == addr)
        assert cand.excluded
        assert any("丑未冲" in h.rule for h in cand.rule_hits)


# ── 4. 子平取格与救应要件核对 ───────────────────────────────────────────────

def test_zhengguan_requirement_breaker_rescuer_met():
    payload = analyze_facts(pillars=["丁卯", "己酉", "甲子", "壬申"], gender="乾")
    zg = next(s for s in payload["structures"] if s["structure_id"] == "ziping_zhengguan")
    items = _items(zg)
    assert items["req_month_guan"]["kind"] == "requirement" and items["req_month_guan"]["status"] == "met"
    assert items["brk_shangguan_jian_guan"]["kind"] == "breaker" and items["brk_shangguan_jian_guan"]["status"] == "met"
    assert items["rsc_he_qu_shang"]["kind"] == "rescuer" and items["rsc_he_qu_shang"]["status"] == "met"


# ── 5. 段派做功候选与干支自合 ───────────────────────────────────────────────

def test_duan_zuogong_hua_yong_and_ganzhi_zihe_without_fugui_score():
    payload = analyze_facts(pillars=["壬子", "壬寅", "庚辰", "辛巳"], gender="乾")
    cands = payload["duan_zuogong"]["candidates"]
    hua = next(c for c in cands if c["mode"] == "化用" and c["members"] == ["H.b", "D.b"])
    assert hua["ten_gods"] == ["七杀", "偏印"] and hua["actor"] == "H.b"

    he = next(c for c in cands if c["mode"] == "合用" and c["relation_kind"] == "ganzhi_zihe")
    assert he["members"] == ["H.s", "H.b"]
    graph = payload["relations"]
    edge = next(e for e in graph["edges"] if e["id"] == he["edge_id"])
    assert edge["attrs"]["branch_controls_stem"] is True

    blob = json.dumps(payload["duan_zuogong"], ensure_ascii=False)
    for banned in ("富贵", "fugui", "score", "档次"):
        assert banned not in blob


# ── 6. CLI 端到端契约 ───────────────────────────────────────────────────────

def test_cli_all_json_under_15kb():
    proc = subprocess.run(
        [
            sys.executable, "-m", "engine.cli", "all",
            "--pillars", "庚申 戊寅 壬子 辛丑",
            "--gender", "乾",
            "--json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert {"chart", "relations", "strength", "shensha", "structures", "duan_zuogong"} <= set(payload)
    assert payload["shensha"]
    th = payload["strength"]["climate"]["tiaohou_lookup"]
    assert th["listed_stems"] and th["source_ref"]
    assert len(proc.stdout.encode("utf-8")) < 15_000


def test_cli_shensha_subcommand_returns_hits():
    proc = subprocess.run(
        [
            sys.executable, "-m", "engine.cli", "shensha",
            "--pillars", "庚申 戊寅 壬子 辛丑",
            "--gender", "乾",
            "--json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    hits = payload["hits"] if isinstance(payload, dict) else payload
    assert hits
    names = {hit["name"] for hit in hits}
    assert {"驿马", "金舆", "文昌", "太极贵人"} <= names
    assert all(hit.get("anchor_addr") and hit.get("target_addr") and hit.get("source_ref") for hit in hits)
