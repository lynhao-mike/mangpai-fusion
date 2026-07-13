"""Conservative adapter from v5 output to blind-evaluation outputs.

Precise task claims require an explicit task binding. Until such bindings exist,
a covered runner abstains and a missing runner reports unsupported.
"""
from __future__ import annotations

from collections.abc import Sequence

from engine.evaluation.models import BlindSchoolOutput, BlindTask
from engine.v5.domain import V5Output

_SUPPORTED_RUNNERS = {"ziping", "ditiansui", "gao_dechen", "duan_jianye", "yang_qingjuan"}


def adapt_v5_to_blind_outputs(
    output: V5Output,
    tasks: Sequence[BlindTask],
    *,
    schools: Sequence[str],
) -> list[BlindSchoolOutput]:
    """Return one honest state for every school/task pair.

    Domain similarity is intentionally insufficient for a claim: the current v5
    output has no versioned task-specific event binding, so supported runners
    abstain rather than leaking broad claims into precise evaluation tasks.
    """
    rows = []
    for school in sorted(set(schools)):
        state = "abstain" if school in _SUPPORTED_RUNNERS else "unsupported"
        rationale = (
            "runner exists but no explicit task-specific event binding is available"
            if state == "abstain"
            else "no independent runner is available for this school"
        )
        for task in sorted(tasks, key=lambda item: item.task_id):
            rows.append(BlindSchoolOutput(
                case_id=output.case_id,
                school_id=school,
                task_id=task.task_id,
                state=state,
                rationale=rationale,
            ))
    return rows
