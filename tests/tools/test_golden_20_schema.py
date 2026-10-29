"""T-170 · golden-20 盲测输入与答案的分离性 / 锚点校验（只读 JSON，不碰引擎）。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BLIND = ROOT / "META" / "golden-20-v1.json"
ANSWERS = ROOT / "META" / "golden-20-answers-v1.json"

ANSWER_FIELDS = (
    "original_analysis",
    "core_work",
    "role_direction",
    "adjudication",
    "rescue",
    "timing",
)
BLIND_KEYS = {
    "case_id",
    "school",
    "four_pillars",
    "gender",
    "dayun_start_age",
    "dayun_direction",
    "dayun",
    "source",
}


def _load(path: Path) -> dict:
    assert path.exists(), f"missing {path}"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def blind() -> dict:
    return _load(BLIND)


@pytest.fixture(scope="module")
def answers() -> dict:
    return _load(ANSWERS)


def test_case_counts_and_ids_align(blind, answers):
    assert len(blind["cases"]) == len(answers["cases"]) == 20
    assert [c["case_id"] for c in blind["cases"]] == [c["case_id"] for c in answers["cases"]]


def test_blind_input_has_no_answer_fields(blind):
    for case in blind["cases"]:
        assert set(case) <= BLIND_KEYS, case["case_id"]
        for field in ANSWER_FIELDS + ("category", "curator_notes", "source_refs"):
            assert field not in case, (case["case_id"], field)
    raw = BLIND.read_text(encoding="utf-8")
    for field in ANSWER_FIELDS:
        assert field not in raw, field


def test_answer_payload_absent_from_blind_text(blind, answers):
    raw = BLIND.read_text(encoding="utf-8")
    for case in answers["cases"]:
        for field in ANSWER_FIELDS:
            value = case[field]
            if value is None:
                continue
            for text in value if isinstance(value, list) else [value]:
                probe = text.strip().strip("。")
                if len(probe) >= 8:
                    assert probe not in raw, (case["case_id"], field)


def test_blind_fields_are_well_formed(blind):
    for case in blind["cases"]:
        assert case["gender"] in ("乾", "坤")
        assert case["dayun_direction"] in ("顺", "逆")
        assert len(case["dayun"]) == 10
        assert len(case["four_pillars"].split()) == 4
        assert case["source"]["path"].startswith("sources/")
        assert case["dayun_start_age"] is None or case["dayun_start_age"] >= 1


def test_category_coverage(answers):
    counts: dict[str, int] = {}
    for case in answers["cases"]:
        counts[case["category"]] = counts.get(case["category"], 0) + 1
    for category in ("制用", "化用", "墓用", "救应"):
        assert counts.get(category, 0) >= 3, (category, counts)


def test_every_non_null_field_has_a_verbatim_source_ref(answers):
    cache: dict[str, list[str]] = {}
    for case in answers["cases"]:
        refs = case["source_refs"]
        by_field: dict[str, list[dict]] = {}
        for ref in refs:
            assert {"path", "line", "quote"} <= set(ref), case["case_id"]
            by_field.setdefault(ref["field"], []).append(ref)
            path = ROOT / ref["path"]
            assert path.exists(), ref["path"]
            if ref["path"] not in cache:
                cache[ref["path"]] = path.read_text(encoding="utf-8").split("\n")
            lines = cache[ref["path"]]
            assert 1 <= ref["line"] <= len(lines), (case["case_id"], ref["path"], ref["line"])
            assert ref["quote"] in lines[ref["line"] - 1], (case["case_id"], ref)
        for field in ANSWER_FIELDS:
            value = case[field]
            if value is None:
                continue
            assert field in by_field, (case["case_id"], field)
            if isinstance(value, list):
                for part in value:
                    assert any(part.strip().strip("。") in r["quote"] for r in by_field[field])


def test_structural_refs_carry_a_snapshot_and_never_a_bare_edge_id(answers):
    """T-169 实测：加 --dayun-index/--liunian 后 edge_id 全量重编号；
    duan_zuogong.candidates 也不是关系边全集。故任何边号必须挂快照，
    且 candidate_id 与 edge_id 必须成对出现，缺一标 candidate_only。"""
    policy = answers["structural_policy"]
    assert "edge_id_rule" in policy and "candidate_rule" in policy
    for case in answers["cases"]:
        assert "edge_id" not in case, case["case_id"]
        snap = case["chart_snapshot"]
        assert snap["chart_id"], case["case_id"]
        assert {"dayun_index", "liunian_year"} <= set(snap), case["case_id"]
        struct = case["struct_refs"]
        assert struct["status"] in ("book_text_only", "candidate_only", "edge_confirmed")
        if struct["edge_ids"]:
            # 有边号 → 必须有快照三要素，且必须有对应 candidate
            assert snap["dayun_index"] is not None or struct["status"] == "edge_confirmed"
            assert struct["candidate_ids"], case["case_id"]
        if struct["status"] == "candidate_only":
            assert struct["candidate_ids"] and not struct["edge_ids"], case["case_id"]

