"""领域分析 CLI 参数与落盘测试。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from engine.v5.domain import V5RunSnapshot
from engine.v5.domain_metadata_integrity import seal_capability_metadata
from tools.domain_analysis_cli import main


def test_non_interactive_missing_required_arguments_fails_without_reading_stdin(monkeypatch, capsys) -> None:
    monkeypatch.setattr("builtins.input", lambda prompt="": (_ for _ in ()).throw(AssertionError("must not read stdin")))

    code = main(["analyze", "--non-interactive"])

    assert code == 2
    assert "缺少必填参数" in capsys.readouterr().err


def test_non_interactive_rejects_output_file_path(tmp_path: Path, capsys) -> None:
    output_file = tmp_path / "not-a-directory"
    output_file.write_text("occupied", encoding="utf-8")

    code = main([
        "analyze", "--gender", "乾", "--birth", "1990-01-01 12:00",
        "--as-of-date", "2026-07-31", "--domains", "career", "--out", str(output_file),
        "--non-interactive",
    ])

    assert code == 1
    assert "输出路径不是目录" in capsys.readouterr().err



def test_non_interactive_analyze_writes_snapshot_and_report(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "out"

    code = main(
        [
            "analyze",
            "--gender", "乾",
            "--birth", "1990-01-01 12:00",
            "--as-of-date", "2026-07-31",
            "--domains", "career", "wealth", "marriage",
            "--out", str(output_dir),
            "--non-interactive",
        ]
    )

    assert code == 0
    files = sorted(output_dir.iterdir())
    assert {path.suffix for path in files} == {".json", ".md"}
    payload = json.loads(next(path for path in files if path.suffix == ".json").read_text(encoding="utf-8"))
    assert payload["metadata"]["production_ready"] is False
    report = next(path for path in files if path.suffix == ".md").read_text(encoding="utf-8")
    assert "六源三领域切片已接入" in report
    assert "六源逐命题工作台" in report
    assert payload["run_id"] not in report
    assert "run snapshot" in capsys.readouterr().out


def _explicit_analyze_args(output_dir: Path, case_id: str) -> list[str]:
    return [
        "analyze", "--gender", "乾", "--birth", "1979-02-09 04:09",
        "--as-of-date", "2026-08-01", "--domains", "career", "wealth", "marriage",
        "--case-id", case_id, "--out", str(output_dir), "--non-interactive",
    ]


def test_non_interactive_analyze_honors_explicit_create_only_case_identity(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    case_id = "DA-乾-己未丙寅丁未壬寅-197902090409-v2"

    assert main(_explicit_analyze_args(output_dir, case_id)) == 0

    snapshot_path = output_dir / f"{case_id}.run.json"
    snapshot = V5RunSnapshot.from_json(snapshot_path.read_text(encoding="utf-8"))
    assert snapshot.case_id == case_id
    assert snapshot.canonical_input["case_id"] == case_id
    assert snapshot.artifact_bindings["report_path"] == f"{case_id}-content-report.md"
    assert snapshot.metadata["domain_evaluation_claims"]
    assert all(item["source_claim_hash"] for item in snapshot.metadata["domain_evaluation_claims"])


def test_repeated_analyze_is_create_only_and_preserves_both_artifacts(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "out"
    case_id = "DA-create-only-repeat"
    args = _explicit_analyze_args(output_dir, case_id)

    assert main(args) == 0
    paths = [output_dir / f"{case_id}.run.json", output_dir / f"{case_id}-content-report.md"]
    before = {path: (path.read_bytes(), hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths}

    assert main(args) != 0
    assert "create-only" in capsys.readouterr().err
    assert {path: (path.read_bytes(), hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths} == before


@pytest.mark.parametrize("existing_kind", ["run", "report"])
def test_analyze_fails_closed_when_only_one_target_exists(
    tmp_path: Path, capsys, existing_kind: str
) -> None:
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    case_id = f"DA-one-existing-{existing_kind}"
    run_path = output_dir / f"{case_id}.run.json"
    report_path = output_dir / f"{case_id}-content-report.md"
    existing = run_path if existing_kind == "run" else report_path
    missing = report_path if existing_kind == "run" else run_path
    existing.write_bytes(b"pre-existing-bytes")
    before = existing.read_bytes()

    assert main(_explicit_analyze_args(output_dir, case_id)) != 0
    assert "create-only" in capsys.readouterr().err
    assert existing.read_bytes() == before
    assert not missing.exists()


@pytest.mark.parametrize("target_kind", ["run", "report"])
def test_analyze_rejects_symlink_or_non_regular_target(
    tmp_path: Path, capsys, target_kind: str
) -> None:
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    case_id = f"DA-unsafe-{target_kind}"
    target = output_dir / (f"{case_id}.run.json" if target_kind == "run" else f"{case_id}-content-report.md")
    target.mkdir()

    assert main(_explicit_analyze_args(output_dir, case_id)) != 0
    assert "create-only" in capsys.readouterr().err
    assert target.is_dir()
    assert len(list(output_dir.iterdir())) == 1


def test_analyze_rejects_symlink_target_without_writing_peer(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    case_id = "DA-unsafe-symlink"
    report_path = output_dir / f"{case_id}-content-report.md"
    try:
        report_path.symlink_to(output_dir / "missing-report.md")
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable on this Windows host: {exc}")

    assert main(_explicit_analyze_args(output_dir, case_id)) != 0
    assert "symlink" in capsys.readouterr().err
    assert report_path.is_symlink()
    assert not (output_dir / f"{case_id}.run.json").exists()


def test_analyze_race_loser_cleans_only_its_report_and_preserves_new_run_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    output_dir = tmp_path / "out"
    case_id = "DA-create-only-race"
    run_path = output_dir / f"{case_id}.run.json"
    report_path = output_dir / f"{case_id}-content-report.md"
    race_bytes = b"race-winner-run"
    from tools import domain_analysis_cli

    real_create_text = domain_analysis_cli._create_text

    def create_with_run_race(path: Path, content: str):
        if path == run_path:
            run_path.write_bytes(race_bytes)
            raise FileExistsError(f"create-only 目标已存在：{path}")
        return real_create_text(path, content)

    monkeypatch.setattr(domain_analysis_cli, "_create_text", create_with_run_race)

    assert main(_explicit_analyze_args(output_dir, case_id)) != 0
    assert "create-only" in capsys.readouterr().err
    assert run_path.read_bytes() == race_bytes
    assert not report_path.exists()


def test_audit_accepts_untampered_snapshot(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "out"
    assert main([
        "analyze", "--gender", "乾", "--birth", "1990-01-01 12:00",
        "--as-of-date", "2026-07-31", "--domains", "career", "--out", str(output_dir),
        "--non-interactive",
    ]) == 0
    snapshot_path = next(output_dir.glob("*.json"))
    report_path = next(output_dir.glob("*.md"))
    snapshot = V5RunSnapshot.from_json(snapshot_path.read_text(encoding="utf-8"))

    assert snapshot.artifact_bindings["report_path"] == report_path.name
    assert snapshot.artifact_bindings["report_sha256"] == hashlib.sha256(report_path.read_bytes()).hexdigest()
    assert main(["audit", str(snapshot_path)]) == 0
    assert "审计通过" in capsys.readouterr().out


@pytest.mark.parametrize("target", ["domain_evaluation_claims", "domain_evaluation_exclusions"])
def test_audit_rejects_shape_valid_evaluation_metadata_tampering_after_resealing(
    tmp_path: Path, capsys, target: str
) -> None:
    output_dir = tmp_path / "out"
    case_id = f"DA-audit-reprojection-{target}"
    assert main(_explicit_analyze_args(output_dir, case_id)) == 0
    snapshot_path = output_dir / f"{case_id}.run.json"
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    changed = [dict(item) for item in payload["metadata"][target]]
    if target == "domain_evaluation_claims":
        changed[0]["task_id"] = "career.forged_target"
    else:
        changed[0]["reason"] = "abstain" if changed[0]["reason"] != "abstain" else "missing_task_id"
    metadata = {**payload["metadata"], target: changed}
    metadata.pop("capability_integrity")
    snapshot = V5RunSnapshot.from_dict({**payload, "metadata": seal_capability_metadata(metadata)})
    resealed = V5RunSnapshot.from_dict({**snapshot.to_dict(), "output_hash": snapshot.to_output().hash()})
    snapshot_path.write_text(resealed.to_json(), encoding="utf-8")

    assert main(["audit", str(snapshot_path)]) == 1
    assert "evaluation" in capsys.readouterr().err


def test_audit_rejects_tampered_report(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "out"
    assert main([
        "analyze", "--gender", "乾", "--birth", "1990-01-01 12:00",
        "--as-of-date", "2026-07-31", "--domains", "career", "--out", str(output_dir),
        "--non-interactive",
    ]) == 0
    snapshot_path = next(output_dir.glob("*.json"))
    report_path = next(output_dir.glob("*.md"))
    report_path.write_text(report_path.read_text(encoding="utf-8") + "\n篡改", encoding="utf-8")

    assert main(["audit", str(snapshot_path)]) == 1
    assert "报告绑定" in capsys.readouterr().err


def test_audit_rejects_snapshot_output_tampering_even_when_report_is_untouched(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "out"
    assert main([
        "analyze", "--gender", "乾", "--birth", "1990-01-01 12:00",
        "--as-of-date", "2026-07-31", "--domains", "career", "--out", str(output_dir),
        "--non-interactive",
    ]) == 0
    snapshot_path = next(output_dir.glob("*.json"))
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    payload["claims"][0]["claim"] = "被篡改的命题"
    snapshot_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    assert main(["audit", str(snapshot_path)]) == 1
    assert "output hash 不匹配" in capsys.readouterr().err


def test_audit_rejects_invalid_slice_coverage_even_when_output_hash_matches(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "out"
    assert main([
        "analyze", "--gender", "乾", "--birth", "1990-01-01 12:00",
        "--as-of-date", "2026-07-31", "--domains", "career", "--out", str(output_dir),
        "--non-interactive",
    ]) == 0
    snapshot_path = next(output_dir.glob("*.json"))
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    payload["metadata"]["slice_coverage"][0]["school"] = "fake_school"
    snapshot_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    assert main(["audit", str(snapshot_path)]) == 1
    assert "槽位" in capsys.readouterr().err


def test_interactive_mode_retries_invalid_input_then_writes_outputs(tmp_path: Path, monkeypatch, capsys) -> None:
    output_dir = tmp_path / "interactive"
    answers = iter([
        "男", "1990-01-01 12:00", "2026-07-31", "", str(output_dir),
        "乾", "1990-01-01 12:00", "2026-07-31", "career", str(output_dir), "y",
    ])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    assert main([]) == 0
    assert len(list(output_dir.iterdir())) == 2
    assert "输入错误" in capsys.readouterr().out


def test_interactive_mode_can_cancel_without_writing(tmp_path: Path, monkeypatch, capsys) -> None:
    output_dir = tmp_path / "cancelled"
    answers = iter(["乾", "1990-01-01 12:00", "2026-07-31", "career", str(output_dir), "n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    assert main([]) == 1
    assert not output_dir.exists()
    assert "已取消" in capsys.readouterr().out
