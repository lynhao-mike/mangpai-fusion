from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from tools.query_theory import build_light_index, search_theory

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def records(tmp_path_factory):
    return build_light_index(cache_path=tmp_path_factory.mktemp("wp7") / "index.json")


@pytest.mark.parametrize(("school", "prefix", "count"), [("duan", "M1-D-", 290), ("ren", "M3-R-", 200)])
def test_all_rules_have_traceable_bodies(records, school, prefix, count):
    rules = {r["id"]: r for r in records if r["school"] == school}
    assert set(rules) == {f"{prefix}{i:03}" for i in range(1, count + 1)}
    for rule_id, record in rules.items():
        assert record["content_status"] == "full", rule_id
        assert record["conclusion"] and record["conclusion"] != record["title"], rule_id
        assert record["statement"]
        path = ROOT / record["raw_file"]
        line = int(record["raw_anchor"].removeprefix("line:"))
        assert rule_id in path.read_text(encoding="utf-8-sig").splitlines()[line - 1]


@pytest.mark.parametrize("query", ["壬水 寅月 调候", "壬日 正月", "壬水寅月"])
def test_stem_month_context_prefers_exact_excerpt(query, tmp_path):
    hits = search_theory(query, schools=("ziping",), per_school_cap=10, cache_path=tmp_path / "index.json")
    assert hits[0]["id"] in {"QT-壬-寅", "ZP-PROD-20260622-909"}
    assert "正月壬水" in hits[0]["statement"]
    assert all(not re.match(r"(?:正月|二月|三春)甲木", hit["title"]) for hit in hits)


def test_title_only_is_explicit_and_source_excerpt_resolves(tmp_path):
    import yaml

    theory = tmp_path / "theory"
    (theory / "duan").mkdir(parents=True)
    (theory / "ziping").mkdir()
    source = tmp_path / "sources" / "test.md"
    source.parent.mkdir()
    source.write_text("# 原书\n\n可定位的经典正文。\n", encoding="utf-8")
    (theory / "duan" / "index.yaml").write_text(yaml.safe_dump({"rules": [{"id": "M1-D-001", "title": "只有标题"}]}, allow_unicode=True), encoding="utf-8")
    (theory / "ziping" / "index.yaml").write_text(yaml.safe_dump({"rules": [{"id": "Z-1", "title": "经典", "source": {"path": "sources/test.md", "excerpt": "可定位的经典正文。"}}]}, allow_unicode=True), encoding="utf-8")
    records = build_light_index(theory_root=theory)
    missing = next(r for r in records if r["id"] == "M1-D-001")
    assert missing["content_status"] == "title_only"
    assert missing["statement"]
    classic = next(r for r in records if r["id"] == "Z-1")
    assert classic["source_ref"]["anchor"] == "line:3"
    source.write_text("# 原书\n\n\n可定位的经典正文。\n", encoding="utf-8")
    assert next(r for r in build_light_index(theory_root=theory) if r["id"] == "Z-1")["source_ref"]["anchor"] == "line:4"


def test_wrong_stem_penalty_survives_matching_month(tmp_path):
    import yaml

    theory = tmp_path / "theory"
    (theory / "ziping").mkdir(parents=True)
    rules = [{"id": "wrong", "title": "正月甲木", "conclusion": "调候须核对日主"},
             {"id": "right", "title": "正月壬水", "conclusion": "调候须核对日主"}]
    (theory / "ziping" / "index.yaml").write_text(yaml.safe_dump({"rules": rules}, allow_unicode=True), encoding="utf-8")
    hits = search_theory("壬水 正月 调候", theory_root=theory, per_school_cap=10)
    assert hits[0]["id"] == "right"
    assert next(h["score"] for h in hits if h["id"] == "wrong") < hits[0]["score"] * 0.05


@pytest.mark.parametrize("module,args,success", [
    ("tools.query_theory", ["--query", "夫妻宫", "--schools", "ren", "--json"], True),
    ("engine.cli", ["chart", "--pillars", "庚申 戊寅 壬子 辛丑"], True),
    ("engine.cli", ["chart", "--pillars", "错误"], False),
    ("tools.query_theory", ["--不存在"], False),
])
def test_cli_overrides_legacy_stdio_encoding(module, args, success):
    env = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONUTF8="0")
    result = subprocess.run([sys.executable, "-m", module, *args], cwd=ROOT, env=env, capture_output=True)
    assert (result.returncode == 0) == success
    text = (result.stdout if success else result.stderr).decode("utf-8")
    assert "UnicodeEncodeError" not in text
    if success:
        json.loads(text)


def test_pillars_all_explains_unavailable_calendar_facts():
    from engine.cli import _parser, _run

    payload = _run("all", _parser().parse_args(["all", "--pillars", "庚申 戊寅 壬子 辛丑"]))
    notes = payload["input_limitations"]
    assert notes["mode"] == "pillars"
    assert {"qiyun", "dayun_calendar", "siling"} <= set(notes["unavailable"])
    assert all(notes["unavailable"].values())
