from dataclasses import asdict
from datetime import date

import pytest

from engine.asof.career_path_state import NatalCareerInclination
from engine.asof.career_relation_contract import (
    CandidateStatus,
    CareerPalace,
    CareerPillarCandidate,
    CareerRelationInference,
    LeftPillar,
    PillarPosition,
    SelectionStage,
)
from engine.asof.career_relation_graph import (
    CareerRelationGraph,
    CareerRelationGraphResult,
    HiddenStemNode,
    LeftPillarCharacterization,
    PillarNode,
    SCHEMA_VERSION,
)
from engine.asof.career_relation_reasoner import (
    adapt_reality_career_status,
    reason_dayun_career_context,
    reason_natal_career_inclination,
)
from engine.asof.daiyun_context import DaiyunStage
from engine.asof.reality_track import RealityStateEntry, RealityTrack


def _node(
    pillar: PillarPosition,
    gan: str,
    zhi: str,
    stem_shishen: str | None,
    *hidden_shishen: str,
) -> PillarNode:
    palace = (
        CareerPalace.SELF
        if pillar in {PillarPosition.DAY, PillarPosition.HOUR}
        else CareerPalace.OTHER
    )
    return PillarNode(
        pillar=pillar,
        palace=palace,
        gan=gan,
        zhi=zhi,
        stem_shishen=stem_shishen,
        hidden_stems=tuple(
            HiddenStemNode(gan="戊", canggan_type="本气", shishen=name)
            for name in hidden_shishen
        ),
    )


def _graph(*, career_shishen: tuple[str, ...], left_shishen: tuple[str, ...]) -> CareerRelationGraphResult:
    career = _node(PillarPosition.HOUR, "己", "未", career_shishen[0], *career_shishen[1:])
    left = _node(PillarPosition.DAY, "甲", "子", left_shishen[0], *left_shishen[1:])
    nodes = (
        _node(PillarPosition.YEAR, "丙", "寅", "比肩"),
        _node(PillarPosition.MONTH, "丁", "卯", "劫财"),
        left,
        career,
    )
    candidate = CareerPillarCandidate(
        pillar=PillarPosition.HOUR,
        palace=CareerPalace.SELF,
        stage=SelectionStage.SELF_OFFICER_KILLING,
        evidence_refs=("candidate:hour",),
        status=CandidateStatus.SELECTED,
    )
    inference = CareerRelationInference(
        candidates=(candidate,),
        selected_pillar=PillarPosition.HOUR,
        left_pillar=LeftPillar(PillarPosition.HOUR, PillarPosition.DAY),
        abstention_reason=None,
    )
    return CareerRelationGraphResult(
        schema_version=SCHEMA_VERSION,
        graph=CareerRelationGraph(SCHEMA_VERSION, nodes, ()),
        stage_trace=(),
        inference=inference,
        left_pillar_characterization=LeftPillarCharacterization(
            career_pillar=PillarPosition.HOUR,
            pillar=PillarPosition.DAY,
            gan=left.gan,
            zhi=left.zhi,
            stem_shishen=left.stem_shishen,
            hidden_shishen=tuple(item.shishen for item in left.hidden_stems),
        ),
        unresolved=(),
    )


def _stage(ganzhi: str, start: date = date(2020, 1, 1), end: date = date(2029, 12, 31)) -> DaiyunStage:
    return DaiyunStage(
        sequence=1,
        ganzhi=ganzhi,
        start_date=start,
        end_date=end,
        opened_paths=(),
        closed_paths=(),
        amplified_paths=(),
        suppressed_paths=(),
        repaired_paths=(),
        redirected_paths=(),
        natal_relations=(),
        domain_tendency="undetermined",
        applicability_conditions=("as_of_date_is_inside_stage",),
        counter_evidence=(),
        signal_refs=("dayun:ganzhi",),
        unresolved_signal_refs=(),
    )


@pytest.mark.parametrize(
    ("career_shishen", "left_shishen", "expected"),
    [
        (("正官",), ("正印",), (True, False)),
        (("正财",), ("伤官",), (False, True)),
        (("正官", "偏财"), ("正印", "食神"), (True, True)),
        (("正财",), ("比肩",), (False, False)),
    ],
)
def test_natal_uses_discrete_career_and_left_pillar_chains(
    career_shishen: tuple[str, ...],
    left_shishen: tuple[str, ...],
    expected: tuple[bool, bool],
) -> None:
    decision = reason_natal_career_inclination(
        _graph(career_shishen=career_shishen, left_shishen=left_shishen)
    )

    assert (
        decision.inclination.employment_inclined,
        decision.inclination.entrepreneurship_inclined,
    ) == expected
    assert not any(isinstance(value, float) for value in asdict(decision).values())
    if expected == (False, False):
        assert decision.abstain_reason == "insufficient_natal_relation_evidence"


def test_natal_does_not_treat_wealth_or_output_alone_as_entrepreneurship() -> None:
    wealth_only = reason_natal_career_inclination(
        _graph(career_shishen=("正财",), left_shishen=("正印",))
    )
    output_only = reason_natal_career_inclination(
        _graph(career_shishen=("正官",), left_shishen=("食神",))
    )

    assert wealth_only.inclination.entrepreneurship_inclined is False
    assert output_only.inclination.entrepreneurship_inclined is False


@pytest.mark.parametrize(
    ("ganzhi", "opens", "suppresses", "conflict"),
    [
        ("甲寅", True, False, False),  # 甲己合，开放已存在的官印链
        ("庚午", False, True, False),  # 午冲职业柱左邻子，抑制承接链
        ("甲午", True, True, True),  # 干合且支冲，同一路径冲突
    ],
)
def test_dayun_computes_open_suppress_and_conflict_without_scores(
    ganzhi: str, opens: bool, suppresses: bool, conflict: bool
) -> None:
    graph = _graph(career_shishen=("正官",), left_shishen=("正印",))
    natal = reason_natal_career_inclination(graph).inclination

    decision = reason_dayun_career_context(
        graph=graph,
        natal=natal,
        as_of_date=date(2025, 6, 1),
        stages=(_stage(ganzhi),),
    )

    assert decision.context is not None
    assert decision.context.opens_employment is opens
    assert decision.context.suppresses_employment is suppresses
    assert decision.has_conflict is conflict
    assert decision.abstain_reason == ("mixed_signal" if conflict else None)


@pytest.mark.parametrize(
    ("as_of_date", "stages"),
    [
        (None, (_stage("甲寅"),)),
        (date(2025, 1, 1), ()),
        (date(2035, 1, 1), (_stage("甲寅"),)),
        (
            date(2025, 1, 1),
            (
                _stage("甲寅", date(2020, 1, 1), date(2026, 1, 1)),
                _stage("乙寅", date(2025, 1, 1), date(2034, 12, 31)),
            ),
        ),
    ],
)
def test_dayun_requires_one_uniquely_locatable_explicit_interval(
    as_of_date: date | None, stages: tuple[DaiyunStage, ...]
) -> None:
    graph = _graph(career_shishen=("正官",), left_shishen=("正印",))
    natal = reason_natal_career_inclination(graph).inclination

    decision = reason_dayun_career_context(
        graph=graph,
        natal=natal,
        as_of_date=as_of_date,
        stages=stages,
    )

    assert decision.context is None
    assert decision.abstain_reason == "insufficient_dayun_information"


def test_dayun_rejects_missing_or_invalid_boundaries_without_guessing() -> None:
    class BrokenStage:
        ganzhi = "甲寅"
        start_date = None
        end_date = date(2029, 12, 31)

    graph = _graph(career_shishen=("正官",), left_shishen=("正印",))
    natal = reason_natal_career_inclination(graph).inclination

    decision = reason_dayun_career_context(
        graph=graph,
        natal=natal,
        as_of_date=date(2025, 1, 1),
        stages=(BrokenStage(),),
    )

    assert decision.context is None
    assert decision.abstain_reason == "insufficient_dayun_information"


def _track(value: str) -> RealityTrack:
    event_id = f"event:{value}"
    state = RealityStateEntry(
        state_id=f"state:{value}",
        domain="career",
        value=value,
        source_event_id=event_id,
        effective_from=date(2020, 1, 1),
        effective_until=None,
        verified=True,
    )
    return RealityTrack("C-TEST", date(2025, 1, 1), (state,), (), (event_id,))


@pytest.mark.parametrize("value", ["employed", "entrepreneurial", "mixed", "transitioning"])
def test_reality_adapter_preserves_verified_first_class_states(value: str) -> None:
    status = adapt_reality_career_status(_track(value))

    assert status.current == value
    assert status.verified_events == (f"event:{value}",)


def test_reality_is_unknown_without_verified_career_state_and_is_not_filled_by_natal() -> None:
    track = RealityTrack("C-TEST", date(2025, 1, 1), (), (), ())
    natal = NatalCareerInclination(True, True, ("natal:dual-chain",))

    status = adapt_reality_career_status(track)

    assert natal.employment_inclined and natal.entrepreneurship_inclined
    assert status.current == "unknown"
    assert status.verified_events == ()
