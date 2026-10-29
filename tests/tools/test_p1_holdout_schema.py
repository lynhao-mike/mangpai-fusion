"""T-175 · P1 hold-out 盲测输入/答案的 schema、分离与出处校验。

本测试只校验「尺子本身」可机械判定的部分：
1. 盲测输入不含答案字段；
2. 盲测/答案 case_id 与四柱一一对应，20 例且四类各 ≥3；
3. 与 dev（`META/golden-20-v1.json`）不重盘、不重 source 行；
4. 每例至少一条 `core_work_relations`，`actor == a`，`quote` 能在 `source_ref` 行内逐字检索；
5. 四柱为合法干支。

它不判断命理结论是否正确——那是中枢抽查与 P1 评分的事。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BLIND_PATH = ROOT / "META" / "p1-holdout-v1.json"
ANSWERS_PATH = ROOT / "META" / "p1-holdout-answers-v1.json"
DEV_PATH = ROOT / "META" / "golden-20-v1.json"

GAN = set("甲乙丙丁戊己庚辛壬癸")
ZHI = set("子丑寅卯辰巳午未申酉戌亥")
KINDS = {"制", "化", "墓", "救应"}
MECHANISMS = {"制", "合", "冲", "穿", "克", "刑", "墓", "化", "生"}
GENDERS = {"乾", "坤", "未注明"}
BLIND_CASE_KEYS = {"case_id", "four_pillars", "gender", "source"}
ANSWER_KEYS = {"a", "b", "kind", "mechanism", "actor", "quote", "source_ref"}
LOCATOR_RE = re.compile(r"L(\d+)(?:-L(\d+))?")
SOURCE_REF_RE = re.compile(r"^(sources/duan/.+\.md):L(\d+)$")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _pillars(text: str) -> list[str]:
    parts = text.split()
    assert len(parts) == 4, f"四柱不是 4 柱: {text!r}"
    return parts


def _chars(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())


def _ranges(locator: str) -> list[tuple[int, int]]:
    out = []
    for m in LOCATOR_RE.finditer(locator):
        start = int(m.group(1))
        end = int(m.group(2) or start)
        out.append((start, end))
    return out


@pytest.fixture(scope="module")
def blind() -> dict:
    return _load(BLIND_PATH)


@pytest.fixture(scope="module")
def answers() -> dict:
    return _load(ANSWERS_PATH)


@pytest.fixture(scope="module")
def dev() -> dict:
    return _load(DEV_PATH)


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

    keys = set(walk(blind))
    assert not (keys & {"core_work_relations", "actor", "quote", "kind", "mechanism", "rescued"}), (
        f"盲测输入出现答案字段: {sorted(keys & {'core_work_relations', 'actor', 'quote', 'kind', 'mechanism', 'rescued'})}"
    )
    for case in blind["cases"]:
        assert set(case) == BLIND_CASE_KEYS
        assert set(case["source"]) == {"path", "locator"}


def test_case_count_and_four_category_floor(blind: dict, answers: dict) -> None:
    assert len(blind["cases"]) >= 15, "hold-out 不足，P1 不可裁决"
    assert len(blind["cases"]) == len(answers["cases"]) == 20
    assert answers["case_count"] == 20

    actual = {kind: 0 for kind in KINDS}
    for case in answers["cases"]:
        assert case["category"] in KINDS
        actual[case["category"]] += 1
    assert actual == answers["category_counts"]
    for kind, count in actual.items():
        assert count >= 3, f"{kind} 类不足 3 例: {count}"


def test_blind_and_answers_aligned(blind: dict, answers: dict) -> None:
    blind_by_id = {c["case_id"]: c for c in blind["cases"]}
    ans_by_id = {c["case_id"]: c for c in answers["cases"]}
    assert len(blind_by_id) == len(blind["cases"]), "盲测 case_id 重复"
    assert len(ans_by_id) == len(answers["cases"]), "答案 case_id 重复"
    assert set(blind_by_id) == set(ans_by_id)
    for case_id, bcase in blind_by_id.items():
        acase = ans_by_id[case_id]
        assert acase["four_pillars"] == bcase["four_pillars"]
        assert acase["gender"] == bcase["gender"]
        assert acase["school"] == "duan"
        assert bcase["source"]["path"].startswith("sources/duan/")
        ranges = _ranges(bcase["source"]["locator"])
        assert ranges, f"{case_id}: 非法 locator"
        for rel in acase["core_work_relations"]:
            ref_path, ref_line = rel["source_ref"].rsplit(":L", 1)
            assert ref_path == bcase["source"]["path"], f"{case_id}: source_ref 与盲测 source 不一致"
            assert any(start <= int(ref_line) <= end for start, end in ranges), (
                f"{case_id}: source_ref L{ref_line} 不在盲测 locator 区间内"
            )


def test_not_dev_and_not_same_source_lines(blind: dict, dev: dict) -> None:
    dev_pillars = {_chars(c["four_pillars"]) for c in dev["cases"]}
    seen = set()
    for case in blind["cases"]:
        key = _chars(case["four_pillars"])
        assert key not in dev_pillars, f"{case['case_id']} 与 dev 同盘"
        assert key not in seen, f"{case['case_id']} 与 hold-out 内部同盘"
        seen.add(key)

    # 同一本 dev 书里，hold-out 的 chart/quote 行区间必须与 dev locator 不重叠。
    dev_ranges: dict[str, list[tuple[int, int]]] = {}
    for case in dev["cases"]:
        src = case["source"]
        dev_ranges.setdefault(src["path"], []).extend(_ranges(src["locator"]))
    for case in blind["cases"]:
        src = case["source"]
        mine = _ranges(src["locator"])
        for start, end in mine:
            for dstart, dend in dev_ranges.get(src["path"], []):
                assert end < dstart or start > dend, (
                    f"{case['case_id']} source 行与 dev 重叠: L{start}-L{end} vs L{dstart}-L{dend}"
                )


def test_four_pillars_and_gender(blind: dict, answers: dict) -> None:
    for case in blind["cases"]:
        for pillar in _pillars(case["four_pillars"]):
            assert len(pillar) == 2, f"{case['case_id']}: 非两字干支 {pillar!r}"
            assert pillar[0] in GAN, f"{case['case_id']}: 非法天干 {pillar!r}"
            assert pillar[1] in ZHI, f"{case['case_id']}: 非法地支 {pillar!r}"
        assert case["gender"] in GENDERS, f"{case['case_id']}: 非法性别 {case['gender']!r}"

    for case in answers["cases"]:
        basis = case["gender_basis"]
        assert basis in {"source_label", "not_stated", "inferred_from_occupation"}
        if basis == "not_stated":
            assert case["gender"] == "未注明"
        else:
            assert case["gender"] in {"乾", "坤"}


def test_each_relation_has_quoted_actor(answers: dict) -> None:
    for case in answers["cases"]:
        rels = case["core_work_relations"]
        assert rels, f"{case['case_id']}: 无 core_work_relations"
        for rel in rels:
            assert set(rel) >= ANSWER_KEYS
            assert rel["kind"] in KINDS
            assert rel["mechanism"] in MECHANISMS
            assert rel["actor"] == rel["a"], f"{case['case_id']}: actor 必须等于 a"
            assert rel["a"] != rel["b"]
            assert rel["quote"].strip()

            m = SOURCE_REF_RE.match(rel["source_ref"])
            assert m, f"{case['case_id']}: 非法 source_ref {rel['source_ref']!r}"
            path, line_no = m.group(1), int(m.group(2))
            lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
            assert 1 <= line_no <= len(lines), f"{case['case_id']}: source_ref 行号越界"
            assert rel["quote"] in lines[line_no - 1], (
                f"{case['case_id']}: quote 不是 L{line_no} 的逐字片段"
            )

            assert rel["a"] in case["four_pillars"] or rel["a"] in rel["quote"]
            assert rel["b"] in case["four_pillars"] or rel["b"] in rel["quote"]
            if rel["kind"] == "救应":
                assert rel.get("rescued")
        assert any(rel["kind"] == case["category"] for rel in rels), (
            f"{case['case_id']}: 没有任何关系落在声明的 {case['category']} 类"
        )


def test_blind_does_not_contain_answers(blind: dict, answers: dict) -> None:
    blob = json.dumps(blind, ensure_ascii=False)
    for case in answers["cases"]:
        for rel in case["core_work_relations"]:
            assert rel["quote"] not in blob, f"{case['case_id']}: 盲测输入含答案 quote"
