from dataclasses import FrozenInstanceError
import json

import pytest

from engine.decision.yang_marriage import (
    FamilyKey,
    SexBasis,
    YangMarriageDiscrimination,
    YangMarriageFamilyEvidence,
    YangMarriageRawSignals,
    YangMarriageState,
)


def family(key: FamilyKey) -> YangMarriageFamilyEvidence:
    return YangMarriageFamilyEvidence(
        family_key=key,
        matched=True,
        fact_refs=("four_pillars.day",),
        feature_refs=("chong_pairs",),
        canonical_pairs=(("午", "子"),) if key == "spouse_palace_event_anchor" else (),
        reason_codes=(f"matched_{key}",),
        detail="合成审计证据",
    )


def discrimination(
    *,
    state: YangMarriageState,
    families: tuple[YangMarriageFamilyEvidence, ...],
    event_anchor_passed: bool,
    independent_spouse_interaction_passed: bool,
    blocking_reason_codes: tuple[str, ...],
    sex_basis: SexBasis = "male_wealth",
    spouse_palace_branch: str = "子",
) -> YangMarriageDiscrimination:
    return YangMarriageDiscrimination(
        schema_version="yang-marriage-discrimination/v1",
        case_id=f"YM-SYN-{state.upper()}",
        state=state,
        sex_basis=sex_basis,
        spouse_palace_branch=spouse_palace_branch,
        families=families,
        event_anchor_passed=event_anchor_passed,
        independent_spouse_interaction_passed=independent_spouse_interaction_passed,
        blocking_reason_codes=blocking_reason_codes,
        falsifier="合成证伪口径。",
        source_rule_refs=("theory/yang/index.yaml#M2-Y-068",),
    )


def test_event_requires_named_a_and_b_gates_and_is_frozen() -> None:
    result = discrimination(
        state="event",
        families=(
            family("spouse_palace_event_anchor"),
            family("spouse_star_peer_interaction"),
        ),
        event_anchor_passed=True,
        independent_spouse_interaction_passed=True,
        blocking_reason_codes=(),
    )

    assert result.to_dict()["state"] == "event"
    assert "probability" not in result.to_dict()
    with pytest.raises(FrozenInstanceError):
        result.state = "pressure"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("state", "families", "anchor", "interaction", "blockers", "message"),
    [
        (
            "event",
            (family("spouse_palace_event_anchor"),),
            True,
            False,
            (),
            "event requires named A and B families",
        ),
        (
            "event",
            (family("spouse_star_peer_interaction"),),
            True,
            True,
            (),
            "event requires named A and B families",
        ),
        (
            "event",
            (
                family("spouse_palace_event_anchor"),
                family("spouse_star_peer_interaction"),
            ),
            True,
            True,
            ("incomplete_evidence",),
            "event requires named A and B families",
        ),
        (
            "pressure",
            (),
            False,
            False,
            ("insufficient_yang_marriage_signal",),
            "pressure requires evidence",
        ),
        (
            "pressure",
            (
                family("spouse_palace_event_anchor"),
                family("spouse_star_peer_interaction"),
            ),
            True,
            True,
            ("unexpected_blocker",),
            "pressure requires evidence",
        ),
        (
            "pressure",
            (family("spouse_palace_event_anchor"),),
            True,
            False,
            (),
            "pressure requires evidence",
        ),
        (
            "abstain",
            (),
            False,
            False,
            (),
            "abstain requires blocking reasons",
        ),
        (
            "abstain",
            (family("spouse_palace_event_anchor"),),
            True,
            False,
            ("incomplete_evidence",),
            "abstain cannot pass event gates",
        ),
        (
            "abstain",
            (
                family("spouse_palace_event_anchor"),
                family("spouse_star_peer_interaction"),
            ),
            False,
            False,
            ("incomplete_evidence",),
            "abstain cannot carry a complete event family payload",
        ),
    ],
)
def test_inconsistent_state_combinations_are_rejected(
    state: YangMarriageState,
    families: tuple[YangMarriageFamilyEvidence, ...],
    anchor: bool,
    interaction: bool,
    blockers: tuple[str, ...],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        discrimination(
            state=state,
            families=families,
            event_anchor_passed=anchor,
            independent_spouse_interaction_passed=interaction,
            blocking_reason_codes=blockers,
        )


def test_duplicate_family_is_rejected() -> None:
    anchor = family("spouse_palace_event_anchor")
    with pytest.raises(ValueError, match="duplicate family_key"):
        discrimination(
            state="pressure",
            families=(anchor, anchor),
            event_anchor_passed=True,
            independent_spouse_interaction_passed=False,
            blocking_reason_codes=("missing_independent_spouse_interaction",),
        )


def test_family_evidence_is_validated_deduplicated_and_sorted() -> None:
    evidence = YangMarriageFamilyEvidence(
        family_key="spouse_palace_event_anchor",
        matched=True,
        fact_refs=("z", "a", "z"),
        feature_refs=("xing_hai_pairs", "chong_pairs", "chong_pairs"),
        canonical_pairs=(("午", "子"), ("丑", "未"), ("午", "子")),
        reason_codes=("z", "a", "z"),
        detail="合成审计证据",
    )

    assert evidence.fact_refs == ("a", "z")
    assert evidence.feature_refs == ("chong_pairs", "xing_hai_pairs")
    assert evidence.canonical_pairs == (("丑", "未"), ("午", "子"))
    assert evidence.reason_codes == ("a", "z")
    with pytest.raises(ValueError, match="matched family requires"):
        YangMarriageFamilyEvidence(
            "ambient_relationship_pressure", False, (), (), (), (), "",
        )


def test_discrimination_sorting_and_serialization_are_deterministic() -> None:
    first = YangMarriageDiscrimination(
        schema_version="yang-marriage-discrimination/v1",
        case_id="YM-SYN-DETERMINISTIC",
        state="event",
        sex_basis="male_wealth",
        spouse_palace_branch="子",
        families=(
            family("spouse_star_peer_interaction"),
            family("spouse_palace_event_anchor"),
        ),
        event_anchor_passed=True,
        independent_spouse_interaction_passed=True,
        blocking_reason_codes=(),
        falsifier="合成证伪口径。",
        source_rule_refs=("z", "a", "z"),
    )
    second = YangMarriageDiscrimination(
        schema_version="yang-marriage-discrimination/v1",
        case_id="YM-SYN-DETERMINISTIC",
        state="event",
        sex_basis="male_wealth",
        spouse_palace_branch="子",
        families=(
            family("spouse_palace_event_anchor"),
            family("spouse_star_peer_interaction"),
        ),
        event_anchor_passed=True,
        independent_spouse_interaction_passed=True,
        blocking_reason_codes=(),
        falsifier="合成证伪口径。",
        source_rule_refs=("a", "z"),
    )
    expected = {
        "schema_version": "yang-marriage-discrimination/v1",
        "case_id": "YM-SYN-DETERMINISTIC",
        "state": "event",
        "sex_basis": "male_wealth",
        "spouse_palace_branch": "子",
        "families": [
            family("spouse_palace_event_anchor").to_dict(),
            family("spouse_star_peer_interaction").to_dict(),
        ],
        "event_anchor_passed": True,
        "independent_spouse_interaction_passed": True,
        "blocking_reason_codes": [],
        "falsifier": "合成证伪口径。",
        "source_rule_refs": ["a", "z"],
    }

    assert first.to_dict() == second.to_dict() == expected
    assert json.dumps(first.to_dict(), ensure_ascii=False, sort_keys=True) == json.dumps(
        expected, ensure_ascii=False, sort_keys=True
    )


@pytest.mark.parametrize("field", ("schema_version", "case_id", "falsifier"))
def test_discrimination_requires_identity_and_falsifier(field: str) -> None:
    values = {
        "schema_version": "yang-marriage-discrimination/v1",
        "case_id": "YM-SYN-REQUIRED",
        "falsifier": "合成证伪口径。",
    }
    values[field] = " "
    with pytest.raises(ValueError, match="identity and falsifier are required"):
        YangMarriageDiscrimination(
            schema_version=values["schema_version"],
            case_id=values["case_id"],
            state="abstain",
            sex_basis="unknown",
            spouse_palace_branch="",
            families=(),
            event_anchor_passed=False,
            independent_spouse_interaction_passed=False,
            blocking_reason_codes=("missing_input",),
            falsifier=values["falsifier"],
            source_rule_refs=(),
        )


def test_literal_fields_and_boolean_fields_are_runtime_validated() -> None:
    with pytest.raises(ValueError, match="invalid family_key"):
        family("not_a_family")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="invalid state"):
        discrimination(
            state="not_a_state",  # type: ignore[arg-type]
            families=(),
            event_anchor_passed=False,
            independent_spouse_interaction_passed=False,
            blocking_reason_codes=("invalid_state",),
        )
    with pytest.raises(ValueError, match="invalid sex_basis"):
        YangMarriageRawSignals(
            "YM-SYN-SEX", "other", "", (), False, 0,  # type: ignore[arg-type]
            False, False, False, ("missing_input",),
        )
    with pytest.raises(ValueError, match="boolean fields must be boolean"):
        YangMarriageRawSignals(
            "YM-SYN-BOOL", "unknown", "", (), 1, 0,  # type: ignore[arg-type]
            False, False, False, ("missing_input",),
        )


def test_event_requires_known_sex_nonempty_spouse_palace_and_consistent_gates() -> None:
    event_families = (
        family("spouse_palace_event_anchor"),
        family("spouse_star_peer_interaction"),
    )
    invalid_inputs: tuple[tuple[SexBasis, str, bool, bool, str], ...] = (
        ("unknown", "子", True, True, "interaction family is incompatible with sex_basis"),
        ("male_wealth", " ", True, True, "invalid spouse_palace_branch"),
        ("male_wealth", "子", False, True, "event requires named A and B families"),
        ("male_wealth", "子", True, False, "event requires named A and B families"),
    )
    for sex_basis, spouse_palace_branch, anchor, interaction, message in invalid_inputs:
        with pytest.raises(ValueError, match=message):
            YangMarriageDiscrimination(
                "yang-marriage-discrimination/v1", "YM-SYN-EVENT-INVARIANT", "event",
                sex_basis, spouse_palace_branch, event_families, anchor, interaction, (),
                "合成证伪口径。", (),
            )


@pytest.mark.parametrize(
    ("sex_basis", "interaction_family"),
    [
        ("male_wealth", "spouse_star_output_interaction"),
        ("male_wealth", "spouse_star_configuration"),
        ("female_official", "spouse_star_peer_interaction"),
    ],
)
def test_sex_basis_rejects_incompatible_event_interaction_families(
    sex_basis: SexBasis,
    interaction_family: FamilyKey,
) -> None:
    with pytest.raises(ValueError, match="interaction family is incompatible with sex_basis"):
        YangMarriageDiscrimination(
            "yang-marriage-discrimination/v1", "YM-SYN-SEX-FAMILY", "event",
            sex_basis, "子",
            (family("spouse_palace_event_anchor"), family(interaction_family)),
            True, True, (), "合成证伪口径。", (),
        )


@pytest.mark.parametrize("spouse_palace_branch", ("甲", "invalid"))
def test_nonempty_spouse_palace_branch_must_be_a_valid_earthly_branch(
    spouse_palace_branch: str,
) -> None:
    with pytest.raises(ValueError, match="invalid spouse_palace_branch"):
        YangMarriageDiscrimination(
            "yang-marriage-discrimination/v1", "YM-SYN-BRANCH", "abstain",
            "unknown", spouse_palace_branch, (), False, False,
            ("missing_or_unknown_sex",), "合成证伪口径。", (),
        )
    with pytest.raises(ValueError, match="invalid spouse_palace_branch"):
        YangMarriageRawSignals(
            "YM-SYN-BRANCH", "unknown", spouse_palace_branch, (), False, 0,
            False, False, False, ("missing_or_unknown_sex",),
        )


@pytest.mark.parametrize(
    "hard_blocker",
    (
        "missing_or_unknown_sex",
        "incomplete_evidence",
        "missing_or_invalid_day_pillar",
        "invalid_relationship_pair",
    ),
)
def test_pressure_rejects_specified_hard_blockers(hard_blocker: str) -> None:
    with pytest.raises(ValueError, match="hard blocker requires abstain"):
        discrimination(
            state="pressure",
            families=(family("spouse_palace_event_anchor"),),
            event_anchor_passed=True,
            independent_spouse_interaction_passed=False,
            blocking_reason_codes=(hard_blocker, "missing_independent_spouse_interaction"),
        )


@pytest.mark.parametrize(
    ("sex_basis", "spouse_palace_branch"),
    (("unknown", "子"), ("male_wealth", "")),
)
def test_pressure_requires_known_sex_and_nonempty_spouse_palace(
    sex_basis: SexBasis,
    spouse_palace_branch: str,
) -> None:
    with pytest.raises(ValueError, match="pressure requires known sex and spouse palace"):
        discrimination(
            state="pressure",
            families=(family("spouse_palace_event_anchor"),),
            event_anchor_passed=True,
            independent_spouse_interaction_passed=False,
            blocking_reason_codes=("missing_independent_spouse_interaction",),
            sex_basis=sex_basis,
            spouse_palace_branch=spouse_palace_branch,
        )


def test_pressure_gate_booleans_must_match_family_payload() -> None:
    with pytest.raises(ValueError, match="gate fields must match family payload"):
        discrimination(
            state="pressure",
            families=(family("spouse_palace_event_anchor"),),
            event_anchor_passed=False,
            independent_spouse_interaction_passed=False,
            blocking_reason_codes=("missing_independent_spouse_interaction",),
        )
    with pytest.raises(ValueError, match="gate fields must match family payload"):
        discrimination(
            state="pressure",
            families=(family("spouse_star_peer_interaction"),),
            event_anchor_passed=False,
            independent_spouse_interaction_passed=False,
            blocking_reason_codes=("missing_event_anchor",),
        )


def test_abstain_with_family_and_only_non_hard_reason_is_rejected() -> None:
    with pytest.raises(ValueError, match="abstain with families requires a hard blocker"):
        discrimination(
            state="abstain",
            families=(family("spouse_palace_event_anchor"),),
            event_anchor_passed=False,
            independent_spouse_interaction_passed=False,
            blocking_reason_codes=("missing_independent_spouse_interaction",),
        )


def test_abstain_may_retain_incomplete_diagnostic_families() -> None:
    result = discrimination(
        state="abstain",
        families=(
            family("spouse_palace_event_anchor"),
            family("ambient_relationship_pressure"),
        ),
        event_anchor_passed=False,
        independent_spouse_interaction_passed=False,
        blocking_reason_codes=("incomplete_evidence",),
    )

    assert tuple(item.family_key for item in result.families) == (
        "ambient_relationship_pressure",
        "spouse_palace_event_anchor",
    )


def test_hard_blocked_abstain_may_retain_sex_incompatible_audit_family() -> None:
    result = discrimination(
        state="abstain",
        families=(family("spouse_star_output_interaction"),),
        event_anchor_passed=False,
        independent_spouse_interaction_passed=False,
        blocking_reason_codes=("incomplete_evidence",),
        sex_basis="male_wealth",
    )

    assert tuple(item.family_key for item in result.families) == (
        "spouse_star_output_interaction",
    )


def test_raw_signals_are_frozen_stable_and_reject_negative_counts() -> None:
    signals = YangMarriageRawSignals(
        case_id="YM-SYN-RAW",
        sex_basis="male_wealth",
        spouse_palace_branch="子",
        canonical_palace_pairs=(("午", "子"), ("丑", "未"), ("午", "子")),
        spouse_star_present=True,
        spouse_star_count=1,
        peer_heavy=False,
        output_heavy=False,
        mixed_official_kill=False,
        blocking_reason_codes=("z", "a", "z"),
    )

    assert signals.canonical_palace_pairs == (("丑", "未"), ("午", "子"))
    assert signals.blocking_reason_codes == ("a", "z")
    assert signals.to_dict()["canonical_palace_pairs"] == [["丑", "未"], ["午", "子"]]
    with pytest.raises(FrozenInstanceError):
        signals.spouse_star_count = 2  # type: ignore[misc]
    with pytest.raises(ValueError, match="spouse_star_count must be non-negative"):
        YangMarriageRawSignals(
            "YM-SYN-NEG", "unknown", "", (), False, -1,
            False, False, False, ("missing_input",),
        )
