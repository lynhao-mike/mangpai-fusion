"""as-of 剩余候选优先级排序测试。"""
from pathlib import Path

from tools.as_of_candidate_prioritizer import rank_remaining_candidates


def test_rank_remaining_candidates_excludes_frozen_cases() -> None:
    ranked = rank_remaining_candidates(Path("cases"))
    frozen_case_fragments = (
        "RF000861",
        "RF000441",
        "RF000149",
        "RF000417",
        "RF000464",
        "RF000763",
        "RF000343",
        "RF000897",
    )

    assert ranked
    assert all(
        fragment not in candidate.case_id
        for candidate in ranked
        for fragment in frozen_case_fragments
    )


def test_rank_remaining_candidates_sorts_by_descending_priority() -> None:
    ranked = rank_remaining_candidates(Path("cases"))

    assert [candidate.priority_score for candidate in ranked] == sorted(
        (candidate.priority_score for candidate in ranked),
        reverse=True,
    )
