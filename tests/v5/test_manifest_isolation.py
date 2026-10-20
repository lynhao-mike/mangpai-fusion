"""T-106 回归：`manifest_root` 隔离 manifest 写入，不污染仓库 cases/。

历史 bug：`render_v6_preprod_case` 无条件把运行登记写回 `input.md` 的父目录，
于是任何用真实仓库 case 渲染的测试都会改写 `cases/<case_id>/manifest.json`
（追加 run_id、改写 active_run_id、把 artifact_paths 指向 pytest 临时目录）。
本测试把该行为固化：显式传 `manifest_root` 后，仓库 manifest 字节不变，
登记落在目标目录且仍记录 case 的真实位置。
"""

from __future__ import annotations

from pathlib import Path

from engine.v5.domain import V5CaseManifest
from engine.v5.preprod import render_v6_preprod_case

ROOT = Path(__file__).resolve().parents[2]
CASE_ID = "C-2026-035-乾-戊辰癸亥甲戌庚午"
CASE_DIR = ROOT / "cases" / CASE_ID
CASE_INPUT = CASE_DIR / "input.md"
REPO_MANIFEST = CASE_DIR / "manifest.json"


def test_render_with_manifest_root_leaves_repo_manifest_untouched(tmp_path: Path) -> None:
    assert REPO_MANIFEST.exists(), "前置条件：仓库内该 case 的 manifest 应存在"
    before = REPO_MANIFEST.read_bytes()

    render_v6_preprod_case(
        CASE_INPUT,
        reports_dir=tmp_path / "reports",
        workspace_root=ROOT,
        manifest_root=tmp_path / "manifests",
    )

    assert REPO_MANIFEST.read_bytes() == before, "渲染不应改写仓库内 manifest.json"

    isolated_manifest_path = tmp_path / "manifests" / CASE_ID / "manifest.json"
    assert isolated_manifest_path.exists(), "manifest 应写到 manifest_root/<case_id>/manifest.json"
    manifest = V5CaseManifest.from_json(isolated_manifest_path.read_text(encoding="utf-8"))
    assert manifest.case_id == CASE_ID
    assert len(manifest.run_ids) == 1
    assert manifest.active_run_id == manifest.run_ids[0]
    assert manifest.case_path == f"cases/{CASE_ID}", "case_path 仍应记录 case 的真实位置"
    # artifact_paths 应指向本次调用的报告目录（tmp），而不是仓库内路径
    assert manifest.artifact_paths["report"].startswith((tmp_path / "reports").as_posix())
    assert manifest.artifact_paths["input"] == f"cases/{CASE_ID}/input.md"


def test_manifest_root_default_keeps_writing_to_case_dir(tmp_path: Path) -> None:
    """默认 None 时必须逐字节保持旧行为：写回 input.md 所在目录。"""

    import shutil

    case_dir = tmp_path / CASE_ID
    shutil.copytree(CASE_DIR, case_dir, ignore=shutil.ignore_patterns("manifest.json"))
    copied_manifest = case_dir / "manifest.json"
    assert not copied_manifest.exists()

    render_v6_preprod_case(
        case_dir / "input.md",
        reports_dir=tmp_path / "reports",
        workspace_root=ROOT,
    )

    assert copied_manifest.exists(), "未传 manifest_root 时 manifest 应写回 case 目录"
    manifest = V5CaseManifest.from_json(copied_manifest.read_text(encoding="utf-8"))
    assert manifest.case_id == CASE_ID
