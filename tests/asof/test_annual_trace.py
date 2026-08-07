from engine.asof.annual_trace import (
    adapt_flow_year_energy,
    build_annual_traces,
    build_annual_traces_with_gate,
    probe_layer_gate_compatibility,
)
from engine.asof.event_candidate import AnnualInteractionTrace
from engine.yingqi.retrospective import FlowYearEnergy
from tests.fixtures.cases import load_case


def _flow_year(*, relations: list[str], strength: str = "▲") -> FlowYearEnergy:
    return FlowYearEnergy(
        year=2020,
        age=40,
        liunian="庚子",
        dayun="壬午",
        relations=relations,
        main_energy="工作变动 / 压力",
        strength=strength,  # type: ignore[arg-type]
        domains=["事业", "健康"],
    )


def test_build_annual_traces_from_real_fixture() -> None:
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")

    traces = build_annual_traces(parsed, current_year=2026)

    assert traces
    assert all(isinstance(trace, AnnualInteractionTrace) for trace in traces)
    assert all(trace.year > 0 and trace.liunian and trace.dayun_ganzhi for trace in traces)


def test_asof_trace_is_not_retrospective_flow_year_container() -> None:
    assert AnnualInteractionTrace is not FlowYearEnergy
    assert not issubclass(AnnualInteractionTrace, FlowYearEnergy)


def test_explicit_crossed_gate_requires_and_preserves作用_chain() -> None:
    trace = adapt_flow_year_energy(
        _flow_year(relations=["流年支冲日支子"]),
        natal_nodes=(("natal.day.branch", "日支", "子"),),
        crossed_candidate_gate=True,
    )

    assert trace.crossed_candidate_gate is True
    assert trace.relations
    assert trace.activated_node_ids == ("natal.day.branch",)


def test_empty_relations_are_low_strength_and_below_gate() -> None:
    trace = adapt_flow_year_energy(
        _flow_year(relations=[], strength="▲"),
        natal_nodes=(("natal.day.branch", "日支", "子"),),
        crossed_candidate_gate=True,
    )


    assert trace.relations == ()
    assert trace.activated_node_ids == ()
    assert trace.trigger_strength == "low"
    assert trace.crossed_candidate_gate is False


def test_probe_reports_layer_gate_is_not_callable_with_only_bazi_and_dayun() -> None:
    compatibility = probe_layer_gate_compatibility()

    assert compatibility["layer1_required_parameters"] == ("domain", "parsed")
    assert compatibility["layer2_required_parameters"] == (
        "year",
        "domain",
        "energy",
        "parsed",
    )
    assert compatibility["requires_candidate_event"] is False
    assert compatibility["compatible_with_bazi_dayun_only"] is False
    assert compatibility["missing_inputs"] == ("domain", "parsed", "year")


def test_activated_nodes_use_exact_relation_tokens_not_bare_character_matches() -> None:
    trace = adapt_flow_year_energy(
        _flow_year(relations=["流年支冲日支子", "流年伏吟月支(寅)"]),
        natal_nodes=(
            ("natal.year.branch", "年支", "子"),
            ("natal.month.branch", "月支", "寅"),
            ("natal.day.branch", "日支", "子"),
        ),
    )

    assert trace.activated_node_ids == (
        "natal.month.branch",
        "natal.day.branch",
    )


def test_build_with_gate_returns_annual_traces_for_real_case() -> None:
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")

    traces = build_annual_traces_with_gate(parsed, "事业", current_year=2026)

    assert isinstance(traces, tuple)
    assert traces
    assert all(isinstance(trace, AnnualInteractionTrace) for trace in traces)
    assert any(trace.trigger_strength == "high" for trace in traces)


def test_build_with_gate_has_crossed_gate_when_l1_l2_pass() -> None:
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")

    traces = build_annual_traces_with_gate(parsed, "事业", current_year=2026)
    crossed_traces = tuple(trace for trace in traces if trace.crossed_candidate_gate)

    for trace in crossed_traces:
        assert trace.relations
        assert trace.activated_node_ids
