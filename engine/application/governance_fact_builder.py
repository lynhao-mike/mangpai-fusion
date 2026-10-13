from __future__ import annotations

from dataclasses import dataclass
from typing import Never

from engine.decision.models import ChartFactLedger, RawWenzhenPayload
from engine.features.chart_feature_vector import build_chart_feature_vector
from engine.features.types import ChartFeatureVector
from engine.governance import (
    CanonicalValue,
    DigestRef,
    FactLevel,
    FactSnapshot,
    FactSpec,
    GovernanceFact,
    SnapshotSpec,
    TemporalLayer,
    TemporalScope,
    build_fact_snapshot,
    build_governance_fact,
)


_SNAPSHOT_SCHEMA = "governance.fact-snapshot.v1"
_FEATURE_CALCULATOR_ID = "engine.features.chart_feature_vector"


@dataclass(frozen=True, slots=True)
class FactBuilderError(Exception):
    issue_code: str
    field_path: str
    diagnostic: str


def _fail(issue_code: str, field_path: str, diagnostic: str) -> Never:
    raise FactBuilderError(issue_code, field_path, diagnostic)


def _valid_year(value: int | None) -> bool:
    return type(value) is int and 1 <= value <= 9999


@dataclass(frozen=True, slots=True)
class _L0Projection:
    fact_kind: str
    temporal_scope: TemporalScope
    source_positions: tuple[str, ...]
    input_refs: tuple[str, ...]
    payload: CanonicalValue

    def build(self, version: str) -> GovernanceFact:
        return build_governance_fact(
            FactSpec(
                fact_kind=self.fact_kind,
                fact_level=FactLevel.CANONICAL_OBSERVATION,
                temporal_scope=self.temporal_scope,
                source_positions=self.source_positions,
                input_refs=self.input_refs,
                calculator_id="governance.fact-builder",
                calculator_version=version,
            ),
            self.payload,
        )


def _natal_facts(chart: ChartFactLedger, version: str) -> tuple[GovernanceFact, ...]:
    pillars = {
        key: chart.four_pillars[key]
        for key in ("year", "month", "day", "hour")
        if type(chart.four_pillars.get(key)) is str and chart.four_pillars[key].strip()
    }
    facts: list[GovernanceFact] = []
    if pillars:
        facts.append(
            _L0Projection(
                "chart.four_pillars",
                TemporalScope(TemporalLayer.NATAL),
                tuple(f"four_pillars.{key}" for key in pillars),
                ("input.chart_ledger.four_pillars",),
                pillars,
            ).build(version)
        )
    if chart.sex_marker.strip():
        facts.append(
            _L0Projection(
                "chart.sex_marker",
                TemporalScope(TemporalLayer.NATAL),
                ("sex_marker",),
                ("input.chart_ledger.sex_marker",),
                {"sex_marker": chart.sex_marker},
            ).build(version)
        )
    return tuple(facts)


def _validated_dayun_steps(chart: ChartFactLedger) -> tuple[tuple[str, int, int], ...]:
    steps: list[tuple[str, int, int]] = []
    for step in chart.dayun_steps:
        ganzhi = step.get("ganzhi")
        start_year = step.get("start_year")
        end_year = step.get("end_year")
        if (
            type(ganzhi) is not str
            or not ganzhi.strip()
            or not _valid_year(start_year)
            or not _valid_year(end_year)
            or start_year > end_year
        ):
            _fail(
                "FACT_BUILDER.DAYUN_STEP_INVALID",
                "chart.dayun_steps",
                "every declared dayun step requires a nonempty ganzhi and valid range",
            )
        steps.append((ganzhi, start_year, end_year))
    ordered = tuple(sorted(steps, key=lambda item: (item[1], item[2], item[0])))
    if any(
        current[1] <= previous[2] for previous, current in zip(ordered, ordered[1:])
    ):
        _fail(
            "FACT_BUILDER.DAYUN_OVERLAP",
            "chart.dayun_steps",
            "declared dayun ranges must not overlap",
        )
    return ordered


def _dayun_facts(chart: ChartFactLedger, version: str) -> tuple[GovernanceFact, ...]:
    facts: list[GovernanceFact] = []
    for ganzhi, start_year, end_year in _validated_dayun_steps(chart):
        facts.append(
            _L0Projection(
                "chart.dayun",
                TemporalScope(TemporalLayer.DAYUN, start_year, end_year),
                (f"dayun.{start_year}-{end_year}",),
                ("input.chart_ledger.dayun_steps",),
                {"end_year": end_year, "ganzhi": ganzhi, "start_year": start_year},
            ).build(version)
        )
    return tuple(facts)


def _liunian_fact(
    chart: ChartFactLedger, target_year: int | None, version: str
) -> GovernanceFact | None:
    if target_year is None:
        return None
    if not _valid_year(target_year):
        _fail(
            "FACT_BUILDER.TARGET_YEAR",
            "target_year",
            "target_year must be an integer from 1 through 9999",
        )
    dayun_ranges = _validated_dayun_steps(chart)
    if not dayun_ranges:
        _fail(
            "FACT_BUILDER.DAYUN_CONTEXT_REQUIRED",
            "chart.dayun_steps",
            "liunian requires a valid declared dayun range",
        )
    if not any(start <= target_year <= end for _, start, end in dayun_ranges):
        _fail(
            "FACT_BUILDER.TARGET_YEAR_OUTSIDE_DAYUN",
            "target_year",
            "target_year must be inside a declared dayun range",
        )
    matches = tuple(
        ganzhi
        for step in chart.liunian_steps
        if step.get("year") == target_year
        and type(step.get("year")) is int
        and type(ganzhi := step.get("ganzhi")) is str
        and ganzhi.strip()
    )
    if not matches:
        return None
    if len(matches) != 1:
        issue_code = (
            "FACT_BUILDER.LIUNIAN_DUPLICATE"
            if len(set(matches)) == 1
            else "FACT_BUILDER.LIUNIAN_CONFLICT"
        )
        _fail(
            issue_code,
            "chart.liunian_steps",
            "liunian target year must have exactly one declared ganzhi",
        )
    ganzhi = matches[0]
    return _L0Projection(
        "chart.liunian",
        TemporalScope(TemporalLayer.LIUNIAN, target_year=target_year),
        (f"liunian.{target_year}",),
        ("input.chart_ledger.liunian_steps",),
        {"ganzhi": ganzhi, "year": target_year},
    ).build(version)


def _feature_fact(
    chart: ChartFactLedger, feature_vector: ChartFeatureVector | None
) -> GovernanceFact | None:
    if feature_vector is None:
        return None
    try:
        expected_chart_id = build_chart_feature_vector(
            chart, schema_version=feature_vector.schema_version
        ).chart_id
    except ValueError as error:
        raise FactBuilderError(
            "FACT_BUILDER.FEATURE_VECTOR_UNBINDABLE",
            "feature_vector.chart_id",
            "feature vector cannot be bound to the current chart",
        ) from error
    if feature_vector.chart_id != expected_chart_id:
        _fail(
            "FACT_BUILDER.FEATURE_VECTOR_CHART_ID",
            "feature_vector.chart_id",
            "feature vector chart_id must bind to the current chart",
        )
    return build_governance_fact(
        FactSpec(
            fact_kind="chart.feature_vector.day_master_signals",
            fact_level=FactLevel.CANDIDATE_DERIVED,
            temporal_scope=TemporalScope(TemporalLayer.NATAL),
            source_positions=("feature_vector.day_master_signals",),
            input_refs=("input.chart_ledger.four_pillars",),
            calculator_id=_FEATURE_CALCULATOR_ID,
            calculator_version=feature_vector.schema_version,
        ),
        {
            "draining_count": feature_vector.draining_count,
            "monthly_command_favorable": feature_vector.monthly_command_favorable,
            "rooted_count": feature_vector.rooted_count,
            "supporting_count": feature_vector.supporting_count,
        },
    )


def build_governance_fact_snapshot(
    case_id: str,
    raw_payload: RawWenzhenPayload,
    chart: ChartFactLedger,
    *,
    target_year: int | None = None,
    calculator_version: str,
    feature_vector: ChartFeatureVector | None = None,
) -> FactSnapshot:
    if chart.raw_source_hash != raw_payload.raw_hash:
        _fail(
            "FACT_BUILDER.RAW_SOURCE_HASH",
            "chart.raw_source_hash",
            "chart.raw_source_hash must match raw_payload.raw_hash",
        )
    facts = [
        *_natal_facts(chart, calculator_version),
        *_dayun_facts(chart, calculator_version),
    ]
    liunian = _liunian_fact(chart, target_year, calculator_version)
    if liunian is not None:
        facts.append(liunian)
    feature = _feature_fact(chart, feature_vector)
    if feature is not None:
        facts.append(feature)
    return build_fact_snapshot(
        SnapshotSpec(
            schema_version=_SNAPSHOT_SCHEMA,
            case_id=case_id,
            input_digest=DigestRef.from_material(
                ("raw_wenzhen", raw_payload.raw_hash, raw_payload.parser_version)
            ),
        ),
        tuple(facts),
    )
