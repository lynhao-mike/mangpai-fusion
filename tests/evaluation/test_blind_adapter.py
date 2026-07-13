from engine.evaluation.blind_adapter import adapt_v5_to_blind_outputs
from engine.evaluation.models import BlindTask
from engine.v5.domain import V5Output


def _task(task_id: str = "career.change_window") -> BlindTask:
    return BlindTask(
        task_id=task_id,
        domain="事业",
        claim_type="event_timing",
        scoring_method="time_window",
        quantifiable=True,
        high_risk=False,
        allowed_time_horizons=["annual"],
        required_input_fields=["four_pillars"],
        label_schema={"type": "object", "required": ["occurred", "year"]},
        evaluation_note="fixture",
    )


def test_adapter_does_not_promote_wide_domain_predictions_to_precise_task() -> None:
    output = V5Output(case_id="C-BLIND-001")

    rows = adapt_v5_to_blind_outputs(output, [_task()], schools=["ziping", "ren_fuhong"])

    assert [(row.school_id, row.state) for row in rows] == [
        ("ren_fuhong", "unsupported"),
        ("ziping", "abstain"),
    ]
    assert all(not row.predictions for row in rows)
    assert all(row.task_id == "career.change_window" for row in rows)


def test_adapter_is_deterministic_and_covers_every_school_task_pair() -> None:
    output = V5Output(case_id="C-BLIND-001")
    tasks = [_task("career.change_window"), _task("health.event_window")]

    first = adapt_v5_to_blind_outputs(output, tasks, schools=["ziping", "ditiansui"])
    second = adapt_v5_to_blind_outputs(output, tasks, schools=["ziping", "ditiansui"])

    assert [row.to_dict() for row in first] == [row.to_dict() for row in second]
    assert len(first) == 4
