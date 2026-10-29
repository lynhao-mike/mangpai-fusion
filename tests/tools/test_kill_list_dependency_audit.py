"""T-171 Kill List 依赖审计脚本的确定性 / 不变量测试。

只做静态图 + 分类，不跑 481 盘运行期探针（那是 `--check` / META 产物的活）。
"""
from __future__ import annotations

import json

import pytest

from tools.kill_list_dependency_audit import (
    CLASSES,
    CLASS_REFERENCED,
    CLASS_RULER,
    CLASS_SAFE,
    ENTRYPOINTS,
    ROOT,
    build_report,
    render_markdown,
    ruler_roots,
)


@pytest.fixture(scope="module")
def report() -> dict:
    return build_report(probe_runtime=False)


def test_entrypoints_all_exist() -> None:
    assert len(ENTRYPOINTS) == 6
    for _entry_id, path, _desc in ENTRYPOINTS:
        assert (ROOT / path).is_file(), path


def test_every_kill_list_item_is_classified(report: dict) -> None:
    paths = [item["path"] for item in report["items"]]
    assert len(paths) == len(set(paths))
    assert len(paths) > 300
    for item in report["items"]:
        assert item["class"] in CLASSES, item["path"]
        assert item["recommendation"], item["path"]


def test_safe_items_have_no_external_importer(report: dict) -> None:
    """「安全归档」必须有证据：Kill List 外零引用（否则就是「看起来没人用」）。"""
    for item in report["items"]:
        if item["class"] != CLASS_SAFE:
            continue
        external = [row for row in item["imported_by"] if not row["in_kill_list"]]
        assert external == [], f"{item['path']} 有外部引用却判成安全归档"


def test_hard_entry_dependencies_are_never_archivable_now(report: dict) -> None:
    for item in report["items"]:
        if item["in_hard_entry_closure"]:
            assert item["class"] in (CLASS_REFERENCED, CLASS_RULER), item["path"]
            assert item["batch"] != 1, item["path"]


def test_batch_invariants(report: dict) -> None:
    """批号必须满足「先 importer 后 imported」，脚本自检同样应为空。"""
    assert report["summary"]["invariants"]["ok"] is True
    assert report["summary"]["invariants"]["violation_count"] == 0
    by_path = {item["path"]: item for item in report["items"]}
    for item in report["items"]:
        if item["batch"] is None:
            continue
        for row in item["kill_list_imported_by"]:
            source = by_path.get(row["from"])
            if source is None or source["path"] == item["path"]:
                continue
            assert source["batch"] is not None, f"{item['path']} 的 importer 被保留"
            assert source["batch"] <= item["batch"], f"{item['path']} 的 importer 在更晚批"


def test_no_runtime_evidence_without_probes(report: dict) -> None:
    assert report["runtime_probes"] == []
    for item in report["items"]:
        assert item["runtime_loaded"] == {} or not any(item["runtime_loaded"].values())
        assert item["breaks_481_0"] is False


def test_fact_rulers_are_the_fact_layer() -> None:
    rulers = ruler_roots()
    assert "tests/facts" in rulers
    assert "tests/api" in rulers
    assert "tests/predicates" in rulers


def test_report_is_deterministic(report: dict) -> None:
    again = build_report(probe_runtime=False)
    if again["summary"]["py_files_scanned"] != report["summary"]["py_files_scanned"]:
        pytest.skip("工作树在两次构建之间被并发任务改动，跳过确定性比对")
    first = json.dumps(report, ensure_ascii=False, sort_keys=False)
    second = json.dumps(again, ensure_ascii=False, sort_keys=False)
    assert first == second


def test_markdown_renders(report: dict) -> None:
    text = render_markdown(report, "0" * 64, "kill-list-dependency-audit-v1.json")
    assert text.startswith("# Kill List 依赖审计 v1")
    assert "## 3. 「一动就破 481/0」的模块" in text
    assert "## 4. 分批归档顺序" in text
