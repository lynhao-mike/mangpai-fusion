"""anchor_span 支持测试 · 覆盖合并型条目的多行锚点

背景
----
语义复核发现：合并型条目的内容跨多行（如 M1-D-387 锚 284 但内容含 290-301），
仅用 raw_anchor ±5 搜索 verify_fragment 会漏检。约定 `anchor_span: line:A-B`
把搜索窗口扩展到整个 span。

本测试覆盖：
1. 合法 span（A == raw_anchor，B ≥ A，fragment 在 span 内）→ PASS
2. span 起点与 raw_anchor 不一致 → SUSPECT
3. span 终点越界 → FORGE
4. span 格式非法 → SUSPECT
5. span 区间倒置 → SUSPECT
6. 无 span 时保持原行为（±5 行）
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.extraction_validator import _check_one  # noqa: E402


@pytest.fixture()
def source_file(tmp_path: Path, monkeypatch) -> Path:
    """在 tmp 下造一个 40 行原稿，并把 ROOT 指过去。"""
    src = tmp_path / "sources" / "demo.md"
    src.parent.mkdir(parents=True)
    lines = [f"第{i}行填充内容" for i in range(1, 41)]
    lines[9] = "第十行：真正的规则原文在这里"      # line:10
    lines[28] = "第二十九行：合并型条目的第二段原文"  # line:29
    src.write_text("\n".join(lines) + "\n", encoding="utf-8")

    import tools.extraction_validator as mod
    monkeypatch.setattr(mod, "ROOT", tmp_path)
    return Path("sources/demo.md")


def _rec(**kw) -> dict:
    base = {
        "id": "T-001",
        "school": "yang",
        "classic_name": "测试",
        "title": "测试规则",
        "domain": "lifa",
        "statement": "测试正文",
        "raw_file": "sources/demo.md",
        "raw_anchor": "line:10",
        "source_ref": {"path": "sources/demo.md", "anchor": "line:10"},
        "verify_fragment": "真正的规则原文在这里",
    }
    base.update(kw)
    return base


def test_no_span_keeps_tolerance_behavior(source_file) -> None:
    grade, reason = _check_one(_rec())
    assert grade == "PASS", reason


def test_span_covers_multi_line_content(source_file) -> None:
    """fragment 在 line:29，锚点在 line:10 —— 无 span 会漏，有 span 命中。"""
    rec = _rec(
        verify_fragment="合并型条目的第二段原文",
        anchor_span="line:10-29",
    )
    grade, reason = _check_one(rec)
    assert grade == "PASS", reason


def test_span_start_mismatch_is_suspect(source_file) -> None:
    rec = _rec(anchor_span="line:5-29")
    grade, reason = _check_one(rec)
    assert grade == "SUSPECT"
    assert "不一致" in reason


def test_span_end_out_of_range_is_forge(source_file) -> None:
    rec = _rec(anchor_span="line:10-999")
    grade, reason = _check_one(rec)
    assert grade == "FORGE"
    assert "越界" in reason


def test_span_bad_format_is_suspect(source_file) -> None:
    rec = _rec(anchor_span="lines 10 to 29")
    grade, reason = _check_one(rec)
    assert grade == "SUSPECT"
    assert "格式非法" in reason


def test_span_reversed_is_suspect(source_file) -> None:
    rec = _rec(anchor_span="line:29-10")
    grade, reason = _check_one(rec)
    assert grade == "SUSPECT"
    assert "倒置" in reason


def test_span_still_fails_when_fragment_absent(source_file) -> None:
    rec = _rec(
        verify_fragment="这句话原稿里根本没有",
        anchor_span="line:10-29",
    )
    grade, _ = _check_one(rec)
    assert grade == "SUSPECT"
