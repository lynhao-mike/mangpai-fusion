from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.query_theory import SCHOOLS, build_light_index, search_theory

ROOT = Path(__file__).resolve().parents[2]
THEORY_ROOT = ROOT / "theory"


@pytest.fixture(scope="module")
def cache_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("theory-index") / "light.json"


def test_injury_officer_returns_classic_and_blind_school(cache_path: Path) -> None:
    hits = search_theory("伤官见官", cache_path=cache_path)
    assert len(hits) <= 5
    assert any(hit["school"] == "ziping" and hit["classic_name"] == "《子平真诠》" for hit in hits)
    assert any(hit["school"] in {"gao", "duan", "yang", "ren"} for hit in hits)


@pytest.mark.parametrize(
    ("query", "expected_school", "classic_fragment"),
    [
        ("寅申冲", "ziping", "子平"),
        ("墓库", "gao", "高德臣"),
        ("寒木向阳", "ziping", "穷通宝鉴"),
        ("寅申冲", "tiaohou_ditiansui", "滴天髓"),
    ],
)
def test_queries_hit_relevant_sources(
    query: str, expected_school: str, classic_fragment: str, cache_path: Path
) -> None:
    hits = search_theory(query, top_k=10, per_school_cap=10, cache_path=cache_path)
    match = next(hit for hit in hits if hit["school"] == expected_school and classic_fragment in hit["classic_name"])
    assert match["id"]
    assert match["statement"]
    assert match["source_ref"]["path"]
    assert match["source_ref"]["anchor"]


def test_cache_is_light_and_contains_six_sources(cache_path: Path) -> None:
    records = build_light_index(cache_path=cache_path)
    assert {record["school"] for record in records} == set(SCHOOLS)
    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    assert payload["records"]
    assert all(len(record["statement"]) <= 200 for record in payload["records"])
    assert all(record["classic_name"] and record["id"] and record["source_ref"]["path"] for record in payload["records"])


def test_default_result_limit_and_json_shape(cache_path: Path) -> None:
    hits = search_theory("墓库", cache_path=cache_path)
    assert len(hits) <= 5
    encoded = json.dumps(hits, ensure_ascii=False, separators=(",", ":"))
    decoded = json.loads(encoded)
    assert decoded == hits
    assert all("_search" not in hit and "_search_extra" not in hit for hit in decoded)
    assert all(set(hit) == {"id", "school", "classic_name", "title", "domain", "tags", "statement", "source_ref", "score"} for hit in decoded)
