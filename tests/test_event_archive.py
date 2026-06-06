from __future__ import annotations

from pathlib import Path

import tools.event_archive as event_archive


def test_archive_interaction_appends_case_event(tmp_path, monkeypatch) -> None:
    repo = tmp_path
    case_id = "C-2099-001-乾-甲子甲戌癸卯壬戌"
    case_dir = repo / "cases" / case_id
    case_dir.mkdir(parents=True)
    monkeypatch.setattr(event_archive, "REPO_ROOT", repo)
    monkeypatch.setattr(event_archive, "CASES_DIR", repo / "cases")
    monkeypatch.setattr(event_archive, "META_DIR", repo / "META")
    monkeypatch.setattr(event_archive, "REPORTS_DIR", repo / "reports")

    record = event_archive.archive_interaction(
        case_id="C-2099-001",
        event_type="财运专项",
        question="2026-2027 是否适合投资黄金交易？",
        analysis="2026-2027 为压力与换运窗口，非主财路。",
        result="不宜杠杆短线，仅可小仓位配置。",
        created_at="2099-01-02T03:04:05Z",
    )

    path = repo / "reports" / f"{case_id}-events.md"
    text = path.read_text(encoding="utf-8")
    assert record.target_path == path
    assert record.case_id == case_id
    assert "# events" in text
    assert f"{case_id}-analyst-report.md" in text
    assert f"../cases/{case_id}/events.md" in text
    assert not (case_dir / "events.md").exists()
    assert "财运专项" in text
    assert "2026-2027 是否适合投资黄金交易" in text
    assert "不宜杠杆短线" in text


def test_archive_interaction_writes_meta_when_case_absent(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(event_archive, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(event_archive, "CASES_DIR", tmp_path / "cases")
    monkeypatch.setattr(event_archive, "META_DIR", tmp_path / "META")
    monkeypatch.setattr(event_archive, "REPORTS_DIR", tmp_path / "reports")

    record = event_archive.archive_interaction(
        event_type="架构评审",
        question="识别结构问题",
        analysis="需要集中归档临时交互。",
        result="写入 META 专项记录。",
        created_at="2099-01-02T03:04:05Z",
    )

    path = tmp_path / "META" / "session-events.md"
    text = path.read_text(encoding="utf-8")
    assert record.target_path == path
    assert record.case_id is None
    assert "session-events" in text
    assert "架构评审" in text


def test_archive_interaction_dry_run_does_not_write(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(event_archive, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(event_archive, "CASES_DIR", tmp_path / "cases")
    monkeypatch.setattr(event_archive, "META_DIR", tmp_path / "META")
    monkeypatch.setattr(event_archive, "REPORTS_DIR", tmp_path / "reports")

    record = event_archive.archive_interaction(
        event_type="预演",
        question="q",
        analysis="a",
        result="r",
        created_at="2099-01-02T03:04:05Z",
        dry_run=True,
    )

    assert record.record_id.startswith("EVT-20990102-")
    assert not (tmp_path / "META" / "session-events.md").exists()
