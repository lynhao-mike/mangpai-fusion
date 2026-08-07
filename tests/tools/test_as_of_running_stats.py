import json
from pathlib import Path

from tools.as_of_running_stats import append_stats_snapshot, compute_running_stats


def test_compute_running_stats_scans_existing_verdicts() -> None:
    stats = compute_running_stats(Path("cases"))

    assert stats.case_count >= 4
    assert stats.event_center_hits >= 1
    assert stats.career_evaluable <= stats.case_count


def test_append_stats_snapshot_appends_parseable_json_lines(tmp_path: Path) -> None:
    stats = compute_running_stats(Path("cases"))
    history_path = tmp_path / "history.jsonl"

    append_stats_snapshot(stats, history_path)
    append_stats_snapshot(stats, history_path)

    lines = history_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    snapshots = [json.loads(line) for line in lines]
    assert all(snapshot["case_count"] == stats.case_count for snapshot in snapshots)
    assert all("as_of" in snapshot for snapshot in snapshots)
