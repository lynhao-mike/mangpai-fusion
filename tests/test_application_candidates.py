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
    def test_extract_candidates_keeps_all_fact_types_inside_gate_domain_contract() -> None:
    parsed = SimpleNamespace(
        known_facts=[
            KnownFact(type="灾厄", year=2018, event="重病", content=""),
            KnownFact(type="牢狱", year=2019, event="诉讼", content=""),
            KnownFact(type="出国", year=2021, event="出国定居", content=""),
            KnownFact(type="未注册类型", year=2022, event="其他事实", content=""),
        ]
    )

    assert _extract_candidates(cast(ParsedInput, parsed)) == [
        (2018, "重病", "健康"),
        (2019, "诉讼", "其他"),
        (2021, "出国定居", "其他"),
        (2022, "其他事实", "其他"),
    ]
