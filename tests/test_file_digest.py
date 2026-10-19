"""engine.infrastructure.file_digest 的契约测试。

覆盖：四态判定、两个方向的行尾归一化、非字符串/长度不符的记录值、
以及诊断字典的完整性。背景见 `.workbuddy-ai/kb/lead-findings.md` KB-001。
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from engine.infrastructure.file_digest import (
    MATCH,
    MATCH_CRLF_RECORDED,
    MATCH_EOL_NORMALIZED,
    MISMATCH,
    compare_digest,
    digest_diagnostics,
    digest_matches,
    sha256_file,
    sha256_file_crlf,
    sha256_file_lf,
)


def _write(path: Path, text: str, *, crlf: bool = False) -> bytes:
    payload = text.encode("utf-8")
    if crlf:
        payload = payload.replace(b"\n", b"\r\n")
    path.write_bytes(payload)
    return payload


def test_raw_match(tmp_path: Path) -> None:
    path = tmp_path / "a.json"
    raw = _write(path, '{"a": 1}\n{"b": 2}\n')
    recorded = hashlib.sha256(raw).hexdigest()

    assert compare_digest(path, recorded) == MATCH
    assert digest_matches(path, recorded) is True
    assert sha256_file(path) == recorded


def test_eol_normalized_match_recorded_lf_worktree_crlf(tmp_path: Path) -> None:
    """记录 LF、工作区 CRLF → 最常见的 Windows 假漂移形态。"""
    path = tmp_path / "b.json"
    lf = _write(path, '{"a": 1}\n{"b": 2}\n')
    recorded_lf = hashlib.sha256(lf).hexdigest()
    _write(path, '{"a": 1}\n{"b": 2}\n', crlf=True)

    assert compare_digest(path, recorded_lf) == MATCH_EOL_NORMALIZED
    assert digest_matches(path, recorded_lf) is True


def test_crlf_recorded_match_recorded_crlf_worktree_lf(tmp_path: Path) -> None:
    """记录 CRLF、工作区 LF → 反向假漂移。

    `engine/asof/*.py`、`cases/shuru-input.md` 属于此类；只归一化一个方向会漏。
    """
    path = tmp_path / "c.py"
    crlf = _write(path, "x = 1\ny = 2\n", crlf=True)
    recorded_crlf = hashlib.sha256(crlf).hexdigest()
    _write(path, "x = 1\ny = 2\n")

    assert compare_digest(path, recorded_crlf) == MATCH_CRLF_RECORDED
    assert digest_matches(path, recorded_crlf) is True


def test_real_content_change_is_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "d.json"
    original = _write(path, '{"a": 1}\n')
    recorded = hashlib.sha256(original).hexdigest()
    _write(path, '{"a": 2}\n')

    assert compare_digest(path, recorded) == MISMATCH
    assert digest_matches(path, recorded) is False


@pytest.mark.parametrize("recorded", [None, "", "abc", "0" * 63, "0" * 65, 123, b"0" * 64])
def test_non_digest_recorded_value_is_mismatch(tmp_path: Path, recorded: object) -> None:
    """记录缺失或格式不符必须判 mismatch，绝不能静默放行。"""
    path = tmp_path / "e.json"
    _write(path, '{"a": 1}\n')

    assert compare_digest(path, recorded) == MISMATCH
    assert digest_matches(path, recorded) is False


def test_lone_cr_is_not_treated_as_line_ending(tmp_path: Path) -> None:
    """孤立 CR（非 CRLF）不应被归一化抹掉——那是内容差异。"""
    path = tmp_path / "f.txt"
    payload = b"a\rb\n"
    path.write_bytes(payload)
    recorded = hashlib.sha256(b"ab\n").hexdigest()

    # 孤立 CR 不属于行尾，归一化不动它 → 仍判 mismatch
    assert compare_digest(path, recorded) == MISMATCH


def test_normalized_helpers_are_idempotent(tmp_path: Path) -> None:
    """对已是 LF 的文件，归一化后应与原始字节一致。"""
    path = tmp_path / "g.txt"
    lf = _write(path, "a\nb\n")

    assert sha256_file_lf(path) == hashlib.sha256(lf).hexdigest()
    assert sha256_file(path) == sha256_file_lf(path)


def test_diagnostics_contains_all_four_measured_values(tmp_path: Path) -> None:
    path = tmp_path / "h.json"
    raw = _write(path, '{"a": 1}\n')
    recorded = hashlib.sha256(raw).hexdigest()

    diag = digest_diagnostics(path, recorded)
    assert set(diag) == {
        "digest_verdict",
        "recorded_sha256",
        "actual_sha256",
        "actual_sha256_lf",
        "actual_sha256_crlf",
    }
    assert diag["digest_verdict"] == MATCH
    assert diag["recorded_sha256"] == recorded
    assert diag["actual_sha256"] == recorded


def test_diagnostics_on_mismatch_still_reports_all_variants(tmp_path: Path) -> None:
    """真漂移时诊断必须给出三种实测值，便于人工一眼判别漂移性质。"""
    path = tmp_path / "i.json"
    _write(path, '{"a": 1}\n')

    diag = digest_diagnostics(path, "0" * 64)
    assert diag["digest_verdict"] == MISMATCH
    assert diag["recorded_sha256"] == "0" * 64
    assert diag["actual_sha256"] != "0" * 64
    assert diag["actual_sha256_lf"] != "0" * 64
    assert diag["actual_sha256_crlf"] != "0" * 64


def test_accepts_str_path_as_well_as_path_object(tmp_path: Path) -> None:
    path = tmp_path / "j.json"
    raw = _write(path, '{"a": 1}\n')
    recorded = hashlib.sha256(raw).hexdigest()

    assert compare_digest(str(path), recorded) == MATCH
    assert sha256_file(str(path)) == recorded
