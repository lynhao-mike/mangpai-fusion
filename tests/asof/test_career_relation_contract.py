from dataclasses import FrozenInstanceError

import pytest

from engine.asof.career_relation_contract import (
    AbstentionReason,
    CandidateStatus,
    CareerPalace,
    CareerPillarCandidate,
    CareerRelation,
    CareerRelationInference,
    LeftPillar,
    PillarPosition,
    RejectionReason,
    RelationType,
    SelectionStage,
    infer_career_pillar,
    left_neighbor,
)


def _candidate(
    pillar: PillarPosition,
    stage: SelectionStage,
    *,
    relations: tuple[CareerRelation, ...] = (),
    evidence_refs: tuple[str, ...] = ("theory:Z.3",),
) -> CareerPillarCandidate:
    palace = (
        CareerPalace.SELF
        if pillar in (PillarPosition.DAY, PillarPosition.HOUR)
        else CareerPalace.OTHER
    )
    return CareerPillarCandidate(
        pillar=pillar,
        palace=palace,
        stage=stage,
        relations=relations,
        evidence_refs=evidence_refs,
    )


def _hour_link(pillar: PillarPosition) -> CareerRelation:
    return CareerRelation(
        source=pillar,
        target=PillarPosition.HOUR,
        relation_type=RelationType.COMBINATION,
        evidence_refs=("chart:relation-1",),
    )


def test_contracts_are_frozen_and_use_slots() -> None:
    relation = _hour_link(PillarPosition.MONTH)
    candidate = _candidate(
        PillarPosition.MONTH,
        SelectionStage.OTHER_OFFICER_KILLING_LINKED_TO_HOUR,
        relations=(relation,),
    )

    with pytest.raises(FrozenInstanceError):
        candidate.pillar = PillarPosition.YEAR  # type: ignore[misc]
    assert not hasattr(relation, "__dict__")
    assert not hasattr(candidate, "__dict__")


def test_invalid_relation_rejects_same_endpoint_and_non_neighbor_adjacency() -> None:
    with pytest.raises(ValueError, match="different pillars"):
        CareerRelation(
            source=PillarPosition.DAY,
            target=PillarPosition.DAY,
            relation_type=RelationType.ROOTED,
            evidence_refs=("chart:root",),
        )

    with pytest.raises(ValueError, match="neighboring pillars"):
        CareerRelation(
            source=PillarPosition.YEAR,
            target=PillarPosition.DAY,
            relation_type=RelationType.ADJACENT,
            evidence_refs=("chart:not-adjacent",),
        )


def test_five_step_priority_selects_earliest_stage_without_scoring() -> None:
    step_three = _candidate(
        PillarPosition.MONTH,
        SelectionStage.OTHER_OFFICER_KILLING_LINKED_TO_HOUR,
        relations=(_hour_link(PillarPosition.MONTH),),
    )
    step_two = _candidate(
        PillarPosition.DAY,
        SelectionStage.SELF_OFFICER_KILLING_TOMB,
    )
    step_one = _candidate(
        PillarPosition.HOUR,
        SelectionStage.SELF_OFFICER_KILLING,
    )

    result = infer_career_pillar((step_three, step_two, step_one))

    assert result.selected_pillar is PillarPosition.HOUR
    assert result.left_pillar == LeftPillar(
        career_pillar=PillarPosition.HOUR,
        pillar=PillarPosition.DAY,
    )
    assert result.abstention_reason is None
    statuses = {candidate.pillar: candidate.status for candidate in result.candidates}
    assert statuses[PillarPosition.HOUR] is CandidateStatus.SELECTED
    assert statuses[PillarPosition.DAY] is CandidateStatus.REJECTED
    assert statuses[PillarPosition.MONTH] is CandidateStatus.REJECTED


def test_other_palace_candidate_without_hour_link_is_rejected() -> None:
    candidate = _candidate(
        PillarPosition.MONTH,
        SelectionStage.OTHER_OFFICER_KILLING_LINKED_TO_HOUR,
    )

    result = infer_career_pillar((candidate,))

    assert result.selected_pillar is None
    assert result.abstention_reason is AbstentionReason.NO_ELIGIBLE_CANDIDATE
    assert result.candidates[0].rejection_reason is RejectionReason.MISSING_HOUR_LINK


def test_no_candidate_abstains_explicitly() -> None:
    result = infer_career_pillar(())

    assert result.candidates == ()
    assert result.selected_pillar is None
    assert result.left_pillar is None
    assert result.abstention_reason is AbstentionReason.NO_CANDIDATE


def test_multiple_top_priority_candidates_remain_explicit_conflict() -> None:
    result = infer_career_pillar(
        (
            _candidate(
                PillarPosition.DAY,
                SelectionStage.SELF_OFFICER_KILLING,
                evidence_refs=("chart:day-officer",),
            ),
            _candidate(
                PillarPosition.HOUR,
                SelectionStage.SELF_OFFICER_KILLING,
                evidence_refs=("chart:hour-officer",),
            ),
        )
    )

    assert result.selected_pillar is None
    assert result.left_pillar is None
    assert result.abstention_reason is AbstentionReason.MULTIPLE_TOP_PRIORITY_CANDIDATES
    assert {candidate.status for candidate in result.candidates} == {
        CandidateStatus.CONFLICT
    }


def test_left_pillar_boundary_is_explicit_for_year_and_hour() -> None:
    assert left_neighbor(PillarPosition.YEAR) is None
    assert left_neighbor(PillarPosition.MONTH) is PillarPosition.YEAR
    assert left_neighbor(PillarPosition.DAY) is PillarPosition.MONTH
    assert left_neighbor(PillarPosition.HOUR) is PillarPosition.DAY

    year_result = infer_career_pillar(
        (
            _candidate(
                PillarPosition.YEAR,
                SelectionStage.WEALTH_OR_WEALTH_TOMB,
            ),
        )
    )
    assert year_result.left_pillar == LeftPillar(PillarPosition.YEAR, None)

    with pytest.raises(ValueError, match="left pillar for hour must be day"):
        LeftPillar(PillarPosition.HOUR, None)


def test_canonical_serialization_is_stable_across_input_order() -> None:
    relation_a = CareerRelation(
        source=PillarPosition.MONTH,
        target=PillarPosition.HOUR,
        relation_type=RelationType.HIDDEN_REVEALED,
        evidence_refs=("z-ref", "a-ref"),
    )
    relation_b = CareerRelation(
        source=PillarPosition.MONTH,
        target=PillarPosition.DAY,
        relation_type=RelationType.CLASH,
        evidence_refs=("b-ref",),
    )
    first = _candidate(
        PillarPosition.MONTH,
        SelectionStage.OTHER_OFFICER_KILLING_LINKED_TO_HOUR,
        relations=(relation_a, relation_b),
        evidence_refs=("z-candidate", "a-candidate"),
    )
    second = _candidate(
        PillarPosition.YEAR,
        SelectionStage.WEALTH_OR_WEALTH_TOMB,
        evidence_refs=("year-candidate",),
    )

    result_a = infer_career_pillar((second, first))
    result_b = infer_career_pillar(
        (
            second,
            _candidate(
                PillarPosition.MONTH,
                SelectionStage.OTHER_OFFICER_KILLING_LINKED_TO_HOUR,
                relations=(relation_b, relation_a),
                evidence_refs=("a-candidate", "z-candidate"),
            ),
        )
    )

    assert result_a.to_canonical_json() == result_b.to_canonical_json()
    assert '"schema_version":"career-relation-inference/v1"' in (
        result_a.to_canonical_json()
    )


def test_inference_requires_proposed_inputs() -> None:
    selected = CareerPillarCandidate(
        pillar=PillarPosition.HOUR,
        palace=CareerPalace.SELF,
        stage=SelectionStage.SELF_OFFICER_KILLING,
        evidence_refs=("chart:hour",),
        status=CandidateStatus.SELECTED,
    )

    with pytest.raises(ValueError, match="proposed status"):
        infer_career_pillar((selected,))


def test_selected_inference_requires_explicit_left_pillar() -> None:
    with pytest.raises(ValueError, match="explicit left_pillar"):
        CareerRelationInference(
            candidates=(),
            selected_pillar=PillarPosition.HOUR,
            left_pillar=None,
            abstention_reason=None,
        )
