"""回归测试：冻结记录的 sha256 与工作区文件的行尾差异必须是「假漂移」。

背景见 `.workbuddy-ai/kb/lead-findings.md` KB-001：
core.autocrlf=true + 无 .gitattributes → Windows 检出 CRLF，
冻结记录的 sha256 多在 LF 下计算 → 内容一致但 hash 不匹配。

本测试**只读**仓库现有冻结记录，不做任何修复。目的是：
一旦有人把某处的 hash 比对改回「原始字节」而不做行尾归一化，这里立刻红。

范围说明：只扫 `META/as-of-evaluation/**.json`。
这些记录的 `*_sha256` 字段语义是「目标文件的字节 hash」（有配对的 `*_path`）。
另一类 `artifact_sha256`（META/prospective-go/ 下）语义是「文档自身的 canonical
JSON hash」，与文件行尾无关，不在本测试范围——混入会产生假失败。
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCAN_ROOT = ROOT / "META" / "as-of-evaluation"
SHA_RE = re.compile(r"\b[0-9a-f]{64}\b")


def _lf_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _crlf_sha256(path: Path) -> str:
    normalized = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return hashlib.sha256(normalized).hexdigest()


def _raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _eol_class(path: Path, recorded: str) -> str:
    """判定记录值与工作区文件的关系。

    返回四类之一：
      raw            : 原始字节即匹配
      eol_normalized : 仅行尾归一化后匹配（假漂移）
      crlf_recorded  : 记录的是 CRLF 版 hash，工作区是 LF（反向假漂移）
      mismatch       : 三者都不匹配（真漂移，需人工处置）
    """
    if _raw_sha256(path) == recorded:
        return "raw"
    if _lf_sha256(path) == recorded:
        return "eol_normalized"
    if _crlf_sha256(path) == recorded:
        return "crlf_recorded"
    return "mismatch"


def _collect_file_hash_records() -> list[tuple[str, str, str, str]]:
    """收集 (record_file, field, target_path, recorded_sha) 四元组。

    只收**文件字节 hash 语义**的记录，判定条件全部满足：
      1. 字段名以 `_sha256` 结尾
      2. 同层存在 `<前缀>_path` 字段且值为字符串
      3. 该 path 指向真实存在的文件
    不收 `*_digest` / `*_hash` 字段——它们是内容摘要（canonical JSON 或指标聚合），
    与文件行尾无关，混入会产生假失败。
    """
    records: list[tuple[str, str, str, str]] = []
    for json_path in sorted(SCAN_ROOT.rglob("*.json")):
        try:
            doc = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(doc, dict):
            continue
        for key, value in doc.items():
            if not key.endswith("_sha256"):
                continue
            if not (isinstance(value, str) and SHA_RE.fullmatch(value)):
                continue
            target = doc.get(key[: -len("_sha256")] + "_path")
            if not (isinstance(target, str) and target):
                continue
            if not (ROOT / target).is_file():
                continue
            records.append(
                (json_path.relative_to(ROOT).as_posix(), key, target, value)
            )
    return records


RECORDS = _collect_file_hash_records()


def test_freeze_records_were_discovered() -> None:
    """护栏：若扫描逻辑失效（路径改坏/字段改名），不要让下面测试静默全绿。"""
    assert len(RECORDS) >= 10, "只扫到 %d 条记录，扫描逻辑可能已失效" % len(RECORDS)


@pytest.mark.parametrize(
    ("record_file", "field", "target", "recorded"),
    RECORDS,
    ids=[f"{r[0].split('/')[-1]}::{r[1]}->{r[2].split('/')[-1]}" for r in RECORDS],
)
def test_recorded_hash_matches_after_eol_normalization(
    record_file: str, field: str, target: str, recorded: str
) -> None:
    """记录的 sha256 必须与工作区文件在「行尾无关」的意义上一致。

    三种可接受形态：
      raw            —— 原始字节即匹配（文件行尾未变）
      eol_normalized —— 仅 CRLF→LF 归一化后匹配（假漂移）
      crlf_recorded  —— 记录的是 CRLF 版 hash（反向假漂移）
    仅 mismatch（三者皆不中）才算真漂移 → 失败，需人工处置。
    """
    path = ROOT / target
    assert path.exists(), f"target missing: {record_file}::{field} -> {target}"
    kind = _eol_class(path, recorded)
    assert kind != "mismatch", (
        f"真漂移（内容变更，非行尾）：{record_file}::{field} -> {target}\n"
        f"  recorded={recorded}\n"
        f"  actual_raw={_raw_sha256(path)}\n"
        f"  actual_lf={_lf_sha256(path)}\n"
        f"  actual_crlf={_crlf_sha256(path)}"
    )


def test_eol_only_drift_is_actually_present() -> None:
    """反向护栏：必须确实存在「原始字节不等、归一化后相等」的记录。

    若这条失败，说明仓库里已无行尾差异（例如 .gitattributes 生效或全库转 LF），
    此时 KB-001 的场景消失，本测试文件应连同 KB-001 一起重新评估，
    而不是留一个永远绿但无意义的断言。
    """
    eol_only = [
        (record_file, target)
        for record_file, _field, target, recorded in RECORDS
        if (ROOT / target).exists()
        and _raw_sha256(ROOT / target) != recorded
        and _lf_sha256(ROOT / target) == recorded
    ]
    assert eol_only, "未发现任何行尾假漂移记录；KB-001 场景可能已消失，需重新评估"


def test_known_eol_drift_files_are_content_identical() -> None:
    """具名护栏：KB-001 记录的 p-series 假漂移文件必须内容一致。"""
    pairs = [
        (
            "META/as-of-evaluation/p-series-career-path-classifier-freeze-v1.json",
            "predictions_sha256",
            "predictions/p-series-career-path-classifier-v1.jsonl",
        ),
        (
            "META/as-of-evaluation/p-series-career-path-classifier-freeze-v1.json",
            "manifest_sha256",
            "META/as-of-evaluation/p-series-career-cohort-v1.json",
        ),
        (
            "META/as-of-evaluation/p-series-career-path-classifier-freeze-v2.json",
            "predictions_sha256",
            "predictions/p-series-career-path-classifier-v2.jsonl",
        ),
        (
            "META/as-of-evaluation/p-series-career-path-classifier-freeze-v3.json",
            "predictions_sha256",
            "predictions/p-series-career-path-classifier-v3.jsonl",
        ),
    ]
    checked = 0
    for record_file, field, target in pairs:
        doc = json.loads((ROOT / record_file).read_text(encoding="utf-8"))
        recorded = doc.get(field)
        target_path = ROOT / target
        if not isinstance(recorded, str) or not target_path.exists():
            continue
        assert _lf_sha256(target_path) == recorded, (
            f"{target} 与冻结记录内容不一致（真漂移，需人工处理）"
        )
        checked += 1
    assert checked >= 1, "没有任何一对可校验，测试形同虚设"


def test_gate_distinguishes_eol_drift_from_content_drift() -> None:
    """门禁必须能区分行尾差异与内容差异，且 fail-closed 语义保留。"""
    from tools.career_path_promotion_gate import _hash_verdict

    sample = ROOT / "engine" / "archive.py"
    assert sample.exists()
    raw = _raw_sha256(sample)
    lf = _lf_sha256(sample)

    # 1) 记录的是原始字节 hash → 直接匹配
    passed, reason = _hash_verdict(sample, raw)
    assert passed is True and reason == "match"

    # 2) 记录的是 LF hash，工作区是 CRLF → 归一化后匹配
    passed, reason = _hash_verdict(sample, lf)
    assert passed is True and reason == "match_eol_normalized"

    # 3) 记录的是错值 → 必须拦下
    passed, reason = _hash_verdict(sample, "0" * 64)
    assert passed is False and reason == "content_mismatch"

    # 4) 记录缺失/非字符串 → 必须拦下（不能静默放行）
    passed, reason = _hash_verdict(sample, None)
    assert passed is False
    passed, reason = _hash_verdict(sample, "")
    assert passed is False
