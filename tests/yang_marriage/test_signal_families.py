import pytest

from engine.decision.yang_marriage import (
    _canonical_pair,
    extract_yang_marriage_signals,
    reduce_yang_marriage_families,
)
from tests.yang_marriage.fixtures import cfv, chart


def family_keys(signals) -> tuple[str, ...]:
    return tuple(item.family_key for item in reduce_yang_marriage_families(signals))


def test_pair_order_and_cross_collection_duplicates_are_canonicalized_once() -> None:
    signals = extract_yang_marriage_signals(
        "YM-SYN-D1",
        chart("YM-SYN-D1", day="壬寅"),
        cfv(
            "YM-SYN-D1",
            chong_pairs=(("寅", "申"),),
            xing_hai_pairs=(("申", "寅"),),
        ),
    )

    assert signals.canonical_palace_pairs == (("寅", "申"),)


@pytest.mark.parametrize(
    "pair",
    (("子", "子"), ("子", "甲"), ("甲", "午"), ("子",)),
)
def test_canonical_pair_rejects_self_non_branch_and_non_binary_pairs(
    pair: tuple[str, ...],
) -> None:
    with pytest.raises(ValueError, match="invalid relationship pair"):
        _canonical_pair(pair)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("sex", "day", "completeness", "reason"),
    [
        ("", "壬子", "full", "missing_or_unknown_sex"),
        ("未知", "壬子", "full", "missing_or_unknown_sex"),
        ("乾", "壬", "full", "missing_or_invalid_day_pillar"),
        ("坤", "壬子", "partial", "incomplete_evidence"),
        ("乾", "壬子", "no_hour", "incomplete_evidence"),
    ],
)
def test_missing_unknown_or_incomplete_input_is_explicitly_blocked(
    sex: str,
    day: str,
    completeness: str,
    reason: str,
) -> None:
    signals = extract_yang_marriage_signals(
        "YM-SYN-I",
        chart("YM-SYN-I", sex=sex, day=day),
        cfv("YM-SYN-I", evidence_completeness=completeness),
    )

    assert reason in signals.blocking_reason_codes


@pytest.mark.parametrize(
    ("chong_pairs", "xing_hai_pairs"),
    [
        ((("子", "午"),), (("子", "子"),)),
        ((("子", "丑"),), ()),
        ((), (("子", "午"),)),
    ],
)
def test_invalid_relationship_pair_blocks_and_discards_all_palace_pairs(
    chong_pairs: tuple[tuple[str, str], ...],
    xing_hai_pairs: tuple[tuple[str, str], ...],
) -> None:
    signals = extract_yang_marriage_signals(
        "YM-SYN-I4",
        chart("YM-SYN-I4"),
        cfv(
            "YM-SYN-I4",
            chong_pairs=chong_pairs,
            xing_hai_pairs=xing_hai_pairs,
        ),
    )

    assert signals.canonical_palace_pairs == ()
    assert signals.blocking_reason_codes == ("invalid_relationship_pair",)


def test_non_day_branch_conflict_does_not_create_palace_anchor() -> None:
    signals = extract_yang_marriage_signals(
        "YM-SYN-S2",
        chart("YM-SYN-S2"),
        cfv(
            "YM-SYN-S2",
            chong_pairs=(("寅", "申"),),
            branch_conflict_intensity=1.0,
        ),
    )

    assert signals.canonical_palace_pairs == ()
    assert "spouse_palace_event_anchor" not in family_keys(signals)


@pytest.mark.parametrize(
    ("sex", "counts", "has_wealth", "has_official", "basis", "count", "present"),
    [
        (
            "乾",
            {"正财": 1, "偏财": 2, "正官": 4, "七杀": 3},
            True,
            True,
            "male_wealth",
            3,
            True,
        ),
        (
            "坤",
            {"正财": 4, "偏财": 3, "正官": 1, "七杀": 2},
            True,
            True,
            "female_official",
            3,
            True,
        ),
        (
            "",
            {"正财": 4, "偏财": 3, "正官": 1, "七杀": 2},
            True,
            True,
            "unknown",
            0,
            False,
        ),
    ],
)
def test_spouse_star_basis_is_sex_specific(
    sex: str,
    counts: dict[str, int],
    has_wealth: bool,
    has_official: bool,
    basis: str,
    count: int,
    present: bool,
) -> None:
    signals = extract_yang_marriage_signals(
        "YM-SYN-STAR",
        chart("YM-SYN-STAR", sex=sex),
        cfv(
            "YM-SYN-STAR",
            ten_god_counts=counts,
            has_wealth=has_wealth,
            has_official=has_official,
        ),
    )

    assert (signals.sex_basis, signals.spouse_star_count, signals.spouse_star_present) == (
        basis,
        count,
        present,
    )


def test_reducer_emits_each_named_family_at_most_once_and_compound_only_enhances_anchor() -> None:
    signals = extract_yang_marriage_signals(
        "YM-SYN-FAMILIES",
        chart("YM-SYN-FAMILIES", sex="坤"),
        cfv(
            "YM-SYN-FAMILIES",
            chong_pairs=(("子", "午"),),
            xing_hai_pairs=(("子", "卯"),),
            ten_god_counts={
                "正财": 0,
                "偏财": 0,
                "正官": 1,
                "七杀": 1,
                "比肩": 0,
                "劫财": 0,
                "食神": 2,
                "伤官": 2,
            },
            has_official=True,
            mixed_official_kill=True,
        ),
    )
    families = reduce_yang_marriage_families(signals)

    assert tuple(item.family_key for item in families) == (
        "spouse_palace_event_anchor",
        "spouse_star_configuration",
        "spouse_star_output_interaction",
    )
    anchor = next(item for item in families if item.family_key == "spouse_palace_event_anchor")
    assert anchor.canonical_pairs == (("午", "子"), ("卯", "子"))


def test_male_wealth_peer_context_is_interaction_not_ambient_pressure() -> None:
    signals = extract_yang_marriage_signals(
        "YM-SYN-MALE",
        chart("YM-SYN-MALE", sex="乾"),
        cfv(
            "YM-SYN-MALE",
            ten_god_counts={
                "正财": 1,
                "偏财": 0,
                "正官": 0,
                "七杀": 0,
                "比肩": 2,
                "劫财": 1,
                "食神": 0,
                "伤官": 0,
            },
            has_wealth=True,
            has_official=False,
        ),
    )

    assert family_keys(signals) == (
        "spouse_star_context_pressure",
        "spouse_star_peer_interaction",
    )


def test_missing_spouse_star_with_heavy_global_structures_reduces_to_pressure_families() -> None:
    signals = extract_yang_marriage_signals(
        "YM-SYN-PRESSURE",
        chart("YM-SYN-PRESSURE", sex="乾"),
        cfv(
            "YM-SYN-PRESSURE",
            ten_god_counts={
                "正财": 0,
                "偏财": 0,
                "正官": 0,
                "七杀": 0,
                "比肩": 2,
                "劫财": 2,
                "食神": 2,
                "伤官": 2,
            },
            has_wealth=False,
            has_official=False,
        ),
    )

    assert family_keys(signals) == (
        "ambient_relationship_pressure",
        "spouse_star_context_pressure",
    )
