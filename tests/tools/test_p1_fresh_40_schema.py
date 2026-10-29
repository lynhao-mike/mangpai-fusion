"""T-185 · P1 新鲜 40 条盲集（`p1-fresh-40` v1）的 schema、分离、非 dev 与冻结校验。

本测试只校验「尺子本身」可机械判定的部分：
1. 盲测输入不含任何答案字段（relation/kind/mechanism/actor/mutual/quote）；
2. 40 条 / ≥25 盘 / 每盘 ≤2 条，盲测与答案逐条对齐；
3. 与两套 dev（`META/golden-20-v1.json`、`META/p1-holdout-v1.json`）不重盘、不重 source 行区间；
4. 每条 `quote` 能在 `source_ref` 指向的行内逐字检索，端点 a/b 在四柱内，`actor == a`（`mutual` 例外）；
5. 八类 mechanism 全覆盖；`mutual` 只出现在「刑」；
6. 两份 JSON 的 sha256 与 `META/p1-fresh-40-v1.md` 里冻结的值一致（冻结后不得再改）。

它不判断命理结论是否正确——那是中枢抽查与 P1 评分的事。
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BLIND_PATH = ROOT / "META" / "p1-fresh-40-v1.json"
ANSWERS_PATH = ROOT / "META" / "p1-fresh-40-answers-v1.json"
ROUTING_BLIND_PATH = ROOT / "META" / "p1-fresh-40-routing-blind-v1.json"
ROUTING_ANSWERS_PATH = ROOT / "META" / "p1-fresh-40-routing-v1.json"
MANIFEST_PATH = ROOT / "META" / "p1-fresh-40-v1.md"
DEV_PATHS = (ROOT / "META" / "golden-20-v1.json", ROOT / "META" / "p1-holdout-v1.json")

GAN = set("甲乙丙丁戊己庚辛壬癸")
ZHI = set("子丑寅卯辰巳午未申酉戌亥")
GENDERS = {"乾", "坤", "未注明"}
MECHANISMS = {"冲", "合", "穿", "刑", "克", "生", "化", "墓", "制"}
REQUIRED_MECHANISMS = {"冲", "合", "穿", "刑", "克", "生", "化", "墓"}
KINDS = {"制", "化", "墓", "救应", "冲", "合", "穿", "刑", "克", "生"}
RELATION_KEYS = {"a", "b", "kind", "mechanism", "actor", "mutual"}
BLIND_CASE_KEYS = {"case_id", "chart_id", "four_pillars", "gender", "source"}
ANSWER_CASE_KEYS = {
    "case_id", "chart_id", "four_pillars", "gender", "relation", "quote", "source_ref", "annotation",
}
FORBIDDEN_IN_BLIND = {
    "relation", "kind", "mechanism", "actor", "mutual", "quote", "core_work_relations",
    "category", "source_ref", "annotation", "rescued",
}
LOCATOR_RE = re.compile(r"L(\d+)(?:-L(\d+))?")
SOURCE_REF_RE = re.compile(r"^(sources/duan/.+\.md):L(\d+)$")
ROUTING_TYPES = {"穿制", "合绊", "保护", "制净", "Δ=0"}
ROUTING_CASE_KEYS = {
    "case_id", "chart_id", "four_pillars", "gender", "relation", "quote", "source_ref",
    "routing_type", "expected_direction", "annotation",
}
ROUTING_RELATION_KEYS = {"a", "b", "kind", "mechanism"}
ROUTING_FORBIDDEN = {"expected_direction", "routing_type", "actor", "quote", "relation"}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _chars(text: str) -> str:
    return "".join(str(text).split())


def _pillars(text: str) -> list[str]:
    parts = str(text).split()
    assert len(parts) == 4, f"四柱不是 4 柱: {text!r}"
    return parts


def _ranges(locator: str) -> list[tuple[int, int]]:
    return [
        (int(m.group(1)), int(m.group(2) or m.group(1)))
        for m in LOCATOR_RE.finditer(str(locator))
    ]


@pytest.fixture(scope="module")
def blind() -> dict:
    return _load(BLIND_PATH)


@pytest.fixture(scope="module")
def answers() -> dict:
    return _load(ANSWERS_PATH)


@pytest.fixture(scope="module")
def devs() -> list[dict]:
    return [_load(p) for p in DEV_PATHS]


@pytest.fixture(scope="module")
def routing_blind() -> dict:
    return _load(ROUTING_BLIND_PATH)


@pytest.fixture(scope="module")
def routing_answers() -> dict:
    return _load(ROUTING_ANSWERS_PATH)


def test_blind_input_has_no_answer_fields(blind: dict) -> None:
    assert blind["case_count"] == len(blind["cases"])

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                yield key
                yield from walk(value)
        elif isinstance(node, list):
            for item in node:
                yield from walk(item)

    leaked = set(walk(blind)) & FORBIDDEN_IN_BLIND
    assert not leaked, f"盲测输入出现答案字段: {sorted(leaked)}"
    for case in blind["cases"]:
        assert set(case) == BLIND_CASE_KEYS, f"{case['case_id']}: 盲测字段多余/缺失"
        assert set(case["source"]) == {"path", "locator"}


def test_scale_charts_and_per_chart_cap(blind: dict, answers: dict) -> None:
    assert len(blind["cases"]) == len(answers["cases"]) == 40
    assert answers["case_count"] == 40
    assert blind["chart_count"] == answers["chart_count"]

    per_chart: dict[str, int] = {}
    chart_keys: dict[str, str] = {}
    for case in blind["cases"]:
        per_chart[case["chart_id"]] = per_chart.get(case["chart_id"], 0) + 1
        key = _chars(case["four_pillars"])
        assert chart_keys.setdefault(case["chart_id"], key) == key, (
            f"{case['chart_id']}: 同一 chart_id 出现不同四柱"
        )
    assert len(per_chart) >= 25, f"不同盘不足 25: {len(per_chart)}"
    assert max(per_chart.values()) <= 2, f"存在每盘 >2 条: {per_chart}"
    assert len(set(chart_keys.values())) == len(per_chart), "不同 chart_id 却同四柱"


def test_blind_and_answers_aligned(blind: dict, answers: dict) -> None:
    blind_by_id = {c["case_id"]: c for c in blind["cases"]}
    ans_by_id = {c["case_id"]: c for c in answers["cases"]}
    assert len(blind_by_id) == len(blind["cases"]), "盲测 case_id 重复"
    assert len(ans_by_id) == len(answers["cases"]), "答案 case_id 重复"
    assert set(blind_by_id) == set(ans_by_id)

    for case_id, bcase in blind_by_id.items():
        acase = ans_by_id[case_id]
        assert set(acase) == ANSWER_CASE_KEYS, f"{case_id}: 答案字段多余/缺失"
        assert acase["four_pillars"] == bcase["four_pillars"]
        assert acase["gender"] == bcase["gender"]
        assert acase["chart_id"] == bcase["chart_id"]
        assert bcase["source"]["path"].startswith("sources/duan/")
        ranges = _ranges(bcase["source"]["locator"])
        assert ranges, f"{case_id}: 非法 locator"

        path, line_no = acase["source_ref"].rsplit(":L", 1)
        assert path == bcase["source"]["path"], f"{case_id}: source_ref 与盲测 source 不一致"
        assert any(start <= int(line_no) <= end for start, end in ranges), (
            f"{case_id}: source_ref L{line_no} 不在盲测 locator 区间内"
        )


def test_not_dev_and_not_same_source_lines(blind: dict, devs: list[dict]) -> None:
    dev_pillars = {_chars(c["four_pillars"]) for dev in devs for c in dev["cases"]}
    dev_ranges: dict[str, list[tuple[int, int]]] = {}
    for dev in devs:
        for case in dev["cases"]:
            dev_ranges.setdefault(case["source"]["path"], []).extend(_ranges(case["source"]["locator"]))

    for case in blind["cases"]:
        key = _chars(case["four_pillars"])
        assert key not in dev_pillars, f"{case['case_id']} 与 dev 同盘"
        for start, end in _ranges(case["source"]["locator"]):
            for dstart, dend in dev_ranges.get(case["source"]["path"], []):
                assert end < dstart or start > dend, (
                    f"{case['case_id']} source 行与 dev 重叠: L{start}-L{end} vs L{dstart}-L{dend}"
                )


def test_four_pillars_and_gender(blind: dict) -> None:
    for case in blind["cases"]:
        for pillar in _pillars(case["four_pillars"]):
            assert len(pillar) == 2, f"{case['case_id']}: 非两字干支 {pillar!r}"
            assert pillar[0] in GAN, f"{case['case_id']}: 非法天干 {pillar!r}"
            assert pillar[1] in ZHI, f"{case['case_id']}: 非法地支 {pillar!r}"
        assert case["gender"] in GENDERS, f"{case['case_id']}: 非法性别 {case['gender']!r}"


def test_relation_shape_quote_and_actor(answers: dict) -> None:
    for case in answers["cases"]:
        rel = case["relation"]
        assert set(rel) <= RELATION_KEYS, f"{case['case_id']}: relation 字段越界 {sorted(rel)}"
        assert {"a", "b", "kind", "mechanism", "actor"} <= set(rel), f"{case['case_id']}: relation 缺字段"

        assert rel["mechanism"] in MECHANISMS, f"{case['case_id']}: 非法 mechanism"
        assert rel["kind"] in KINDS, f"{case['case_id']}: 非法 kind"
        assert rel["a"] != rel["b"], f"{case['case_id']}: a == b"

        chart = _chars(case["four_pillars"])
        assert rel["a"] in chart, f"{case['case_id']}: a={rel['a']} 不在四柱内"
        assert rel["b"] in chart, f"{case['case_id']}: b={rel['b']} 不在四柱内"

        if rel.get("mutual"):
            assert rel["mechanism"] == "刑", f"{case['case_id']}: mutual 只用于刑的两败"
            assert rel.get("actor") in (None, ""), f"{case['case_id']}: mutual 不得硬填 actor"
        else:
            assert rel.get("actor"), f"{case['case_id']}: 非 mutual 必须给 actor"
            assert rel["actor"] == rel["a"], f"{case['case_id']}: actor 必须等于 a"

        assert case["quote"].strip(), f"{case['case_id']}: 空 quote"
        m = SOURCE_REF_RE.match(case["source_ref"])
        assert m, f"{case['case_id']}: 非法 source_ref {case['source_ref']!r}"
        path, line_no = m.group(1), int(m.group(2))
        lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
        assert 1 <= line_no <= len(lines), f"{case['case_id']}: source_ref 行号越界"
        assert case["quote"] in lines[line_no - 1], (
            f"{case['case_id']}: quote 不是 L{line_no} 的逐字片段"
        )


def test_mechanism_coverage_and_counts(answers: dict) -> None:
    actual: dict[str, int] = {}
    for case in answers["cases"]:
        mech = case["relation"]["mechanism"]
        actual[mech] = actual.get(mech, 0) + 1

    assert REQUIRED_MECHANISMS <= set(actual), (
        f"mechanism 未覆盖: {sorted(REQUIRED_MECHANISMS - set(actual))}"
    )
    for mech, count in answers["mechanism_counts"].items():
        assert actual.get(mech, 0) == count, f"{mech} 计数与 mechanism_counts 不一致"
    assert sum(answers["mechanism_counts"].values()) == 40
    assert sum(answers["kind_counts"].values()) == 40
    assert sum(answers["gender_counts"].values()) == 40


def test_blind_does_not_contain_answers(blind: dict, answers: dict) -> None:
    blob = json.dumps(blind, ensure_ascii=False)
    for case in answers["cases"]:
        assert case["quote"] not in blob, f"{case['case_id']}: 盲测输入含答案 quote"


def test_frozen_sha256_matches_manifest() -> None:
    manifest = MANIFEST_PATH.read_text(encoding="utf-8")
    for path in (BLIND_PATH, ANSWERS_PATH, ROUTING_BLIND_PATH, ROUTING_ANSWERS_PATH):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest in manifest, f"{path.name}: sha256 未写入 META/p1-fresh-40-v1.md（冻结失效）"


def test_routing_blind_has_no_answer_fields(routing_blind: dict) -> None:
    assert routing_blind["case_count"] == len(routing_blind["cases"]) == 5

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                yield key
                yield from walk(value)
        elif isinstance(node, list):
            for item in node:
                yield from walk(item)

    leaked = set(walk(routing_blind)) & ROUTING_FORBIDDEN
    assert not leaked, f"路由盲测输入出现答案字段: {sorted(leaked)}"
    for case in routing_blind["cases"]:
        assert set(case) == BLIND_CASE_KEYS
        assert set(case["source"]) == {"path", "locator"}


def test_routing_answers_needs_judgment_and_types(routing_blind: dict, routing_answers: dict) -> None:
    blind_by_id = {c["case_id"]: c for c in routing_blind["cases"]}
    ans_by_id = {c["case_id"]: c for c in routing_answers["cases"]}
    assert len(blind_by_id) == len(routing_blind["cases"]) == 5, "路由盲测 case_id 重复或数量不对"
    assert set(blind_by_id) == set(ans_by_id), "路由盲测/答案 case_id 不对齐"

    types: dict[str, int] = {}
    for case_id, acase in ans_by_id.items():
        bcase = blind_by_id[case_id]
        assert set(acase) == ROUTING_CASE_KEYS, f"{case_id}: 路由答案字段多余/缺失"
        assert set(acase["relation"]) == ROUTING_RELATION_KEYS, f"{case_id}: 路由 relation 不得含 actor"
        assert acase["expected_direction"] == "needs_judgment", f"{case_id}: 必须是 needs_judgment"
        assert acase["routing_type"] in ROUTING_TYPES, f"{case_id}: 非法 routing_type"
        assert acase["four_pillars"] == bcase["four_pillars"]
        assert acase["gender"] == bcase["gender"]
        assert acase["chart_id"] == bcase["chart_id"]
        types[acase["routing_type"]] = types.get(acase["routing_type"], 0) + 1

    assert set(types) == ROUTING_TYPES, f"路由类型未覆盖: {sorted(ROUTING_TYPES - set(types))}"
    assert types == routing_answers["routing_types"], "routing_types 计数与 cases 不一致"


def test_routing_not_dev_not_main_and_quotes(
    routing_blind: dict, routing_answers: dict, blind: dict, devs: list[dict],
) -> None:
    main_pillars = {_chars(c["four_pillars"]) for c in blind["cases"]}
    dev_pillars = {_chars(c["four_pillars"]) for dev in devs for c in dev["cases"]}
    dev_ranges: dict[str, list[tuple[int, int]]] = {}
    for dev in devs:
        for case in dev["cases"]:
            dev_ranges.setdefault(case["source"]["path"], []).extend(_ranges(case["source"]["locator"]))

    seen: set[str] = set()
    for case in routing_answers["cases"]:
        key = _chars(case["four_pillars"])
        assert key not in main_pillars, f"{case['case_id']}: 与主集 40 条同盘"
        assert key not in dev_pillars, f"{case['case_id']}: 与 dev 同盘"
        assert key not in seen, f"{case['case_id']}: 路由集内重盘"
        seen.add(key)

        for pillar in _pillars(case["four_pillars"]):
            assert len(pillar) == 2 and pillar[0] in GAN and pillar[1] in ZHI
        for ch in (case["relation"]["a"], case["relation"]["b"]):
            assert ch in key, f"{case['case_id']}: 端点 {ch} 不在四柱内"

        m = SOURCE_REF_RE.match(case["source_ref"])
        assert m, f"{case['case_id']}: 非法 source_ref"
        path, line_no = m.group(1), int(m.group(2))
        lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
        assert case["quote"] in lines[line_no - 1], f"{case['case_id']}: quote 不是逐字片段"

        bcase = next(c for c in routing_blind["cases"] if c["case_id"] == case["case_id"])
        assert path == bcase["source"]["path"]
        ranges = _ranges(bcase["source"]["locator"])
        assert any(start <= line_no <= end for start, end in ranges)
        for start, end in ranges:
            for dstart, dend in dev_ranges.get(path, []):
                assert end < dstart or start > dend, f"{case['case_id']}: source 行与 dev 重叠"


def test_routing_blind_does_not_contain_answers(routing_blind: dict, routing_answers: dict) -> None:
    blob = json.dumps(routing_blind, ensure_ascii=False)
    for case in routing_answers["cases"]:
        assert case["quote"] not in blob, f"{case['case_id']}: 路由盲测输入含答案 quote"
        assert case["routing_type"] not in blob, f"{case['case_id']}: 路由盲测输入含 routing_type"

