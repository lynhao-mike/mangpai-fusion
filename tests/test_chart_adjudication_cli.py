from __future__ import annotations

from dataclasses import replace

import pytest

from engine.claims.orchestrator import generate_chart_adjudication
from engine.claims.runner_registry import RunnerRegistry
from engine.decision.models import ChartFactLedger
from tools.chart_adjudication import (
    ChartAdjudicationInputError,
    _assert_chart_only,
    render_chart_adjudication,
    structure_task,
)
from tests.claims.test_chart_adjudication import _claim


def test_chart_only_renderer_exposes_structure_conclusion_and_boundary() -> None:
    task = structure_task()
    claim = _claim("primary", task)
    result = generate_chart_adjudication(
        ChartFactLedger(four_pillars={"year": "甲子", "month": "丙寅", "day": "戊辰", "hour": "庚午"}),
        task,
        case_id="synthetic-chart-cli",
        schools=["synthetic"],
        registry=RunnerRegistry({("synthetic", task.task_id): lambda *args: [claim]}),
    )
    text = render_chart_adjudication(result)
    assert "Synthetic structure claim primary" in text
    assert "现实映射：未进入现实 outcome 测量层" in text


def test_chart_only_input_rejects_reality_fields_recursively() -> None:
    with pytest.raises(ChartAdjudicationInputError):
        _assert_chart_only({"pillars": {"year": "甲子"}, "nested": {"known_facts": []}})
