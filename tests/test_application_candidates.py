from __future__ import annotations

from typing import cast
from types import SimpleNamespace

from engine.application.candidates import _extract_candidates
from engine.predicates.types import KnownFact, ParsedInput


def test_extract_candidates_normalizes_known_fact_types_to_gate_domains() -> None:
    parsed = SimpleNamespace(
        known_facts=[
            KnownFact(type="职业", year=2020, event="升副科", content=""),
            KnownFact(type="学历", year=2024, event="高考考上一本", content=""),
            KnownFact(type="子女", year=2006, event="生子", content=""),
            KnownFact(type="父母", year=2020, event="母亲去世", content=""),
            KnownFact(type="婚姻", year=2005, event="结婚", content=""),
        ]
    )

    assert _extract_candidates(cast(ParsedInput, parsed)) == [
        (2020, "升副科", "事业"),
        (2024, "高考考上一本", "学业"),
        (2006, "生子", "六亲"),
        (2020, "母亲去世", "六亲"),
        (2005, "结婚", "婚姻"),
    ]
