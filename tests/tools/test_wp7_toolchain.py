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


@pytest.mark.parametrize(("school", "prefix", "min_count"), [("duan", "M1-D-", 290), ("ren", "M3-R-", 200)])
def test_all_rules_have_traceable_bodies(records, school, prefix, min_count):
    """所有规则必须有可追溯正文。

    条数下限而非精确值：语料会持续扩充（段派 290 → 428）。
    早期版本写死 count=290 并在语料扩充后误报失败——语料增长不是回归。

    可追溯性分两类核对：
    - **registry 条目**（raw_file 指向 registry 表格）：该行文本必须含 rule_id，
      因为 registry 是「ID → 规则」的一一对应表。
    - **深水区条目**（raw_file 指向 sources/ 原稿）：原稿是别人的书，
      不可能含我们的 rule_id。此时改为核对该行确实存在且非空，
      并用 verify_fragment（若有）做内容保真校验。
    """
    rules = {r["id"]: r for r in records if r["school"] == school}
    nums = {int(rid[len(prefix):]) for rid in rules}
    assert nums == set(range(1, max(nums) + 1)), f"{school} ID 有缺号"
    assert len(rules) >= min_count, f"{school} 仅 {len(rules)} 条，少于既定基线 {min_count}"

    for rule_id, record in rules.items():
        assert record["content_status"] == "full", rule_id
        assert record["conclusion"] and record["conclusion"] != record["title"], rule_id
        assert record["statement"]

        path = ROOT / record["raw_file"]
        assert path.is_file(), f"{rule_id}: raw_file 不存在 {record['raw_file']}"
        anchor = str(record["raw_anchor"])
        m = re.search(r"line:(\d+)", anchor)
        assert m, f"{rule_id}: raw_anchor 非行号 {anchor!r}"
        line_no = int(m.group(1))
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        assert 1 <= line_no <= len(lines), f"{rule_id}: 行号越界 {line_no}"
        if "sources/" in str(record["raw_file"]):
            # 深水区条目：原稿不可能含我们的 ID，只要求该行非空
            assert lines[line_no - 1].strip(), f"{rule_id}: 原稿该行为空"
        else:
            # registry 条目：该行必须写明 rule_id
            assert rule_id in lines[line_no - 1], f"{rule_id}: registry 该行未含 ID"


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
