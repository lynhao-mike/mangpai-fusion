"""文件摘要工具：行尾无关的 sha256 比对。

动机（见 `.workbuddy-ai/kb/lead-findings.md` KB-001）
-----------------------------------
仓库 `core.autocrlf=true` 且无 `.gitattributes`，Windows 检出会把文本文件的
LF 转成 CRLF。若某处「先记录文件 sha256、日后再比对」，记录与比对之间行尾
可能翻转，导致**内容完全一致却判为漂移**。历史后果：p-series 冻结门禁因此
fail-closed、metrics 被置空、测试 KeyError，且错误定性为「数据完整性已破」。

本模块提供的判定语义
-------------------
`compare_digest(path, recorded)` 返回四态之一，**不再是一个裸 bool**：

    raw            原始字节即匹配（文件行尾未变）
    eol_normalized 仅 CRLF→LF 归一化后匹配（假漂移：记录 LF、工作区 CRLF）
    crlf_recorded  仅 LF→CRLF 归一化后匹配（假漂移：记录 CRLF、工作区 LF）
    mismatch       三者皆不中（真漂移，需人工处置）

两个方向的归一化都要试：`engine/asof/*.py`、`cases/shuru-input.md` 属于
「记录 CRLF、工作区 LF」的反向情形，只试一个方向会漏。

设计约束
--------
* 只依赖标准库，`engine.infrastructure` 层可被 `tools/` 安全导入。
* 不修改任何文件；纯读。
* `sha256_file` 保持「原始字节」语义，供确实需要字节级摘要的场景使用
  （如归档、内容寻址），**不要**用它做跨平台冻结比对。
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Union

PathLike = Union[str, Path]

MATCH = "match"
MATCH_EOL_NORMALIZED = "match_eol_normalized"
MATCH_CRLF_RECORDED = "match_crlf_recorded"
MISMATCH = "mismatch"


def _read(path: PathLike) -> bytes:
    return Path(path).read_bytes()


def sha256_file(path: PathLike) -> str:
    """原始字节 sha256。字节级摘要，**跨平台冻结比对请用 compare_digest**。"""
    return hashlib.sha256(_read(path)).hexdigest()


def sha256_file_lf(path: PathLike) -> str:
    """CRLF→LF 归一化后的 sha256。"""
    return hashlib.sha256(_read(path).replace(b"\r\n", b"\n")).hexdigest()


def sha256_file_crlf(path: PathLike) -> str:
    """LF→CRLF 归一化后的 sha256。"""
    normalized = _read(path).replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    return hashlib.sha256(normalized).hexdigest()


def compare_digest(path: PathLike, recorded: object) -> str:
    """判定记录摘要与工作区文件的关系，返回 MATCH / MATCH_EOL_NORMALIZED /
    MATCH_CRLF_RECORDED / MISMATCH。

    ``recorded`` 非 64 位十六进制字符串时直接判 MISMATCH——调用方不应把
    「记录缺失」静默当作「匹配」。
    """
    if not isinstance(recorded, str) or len(recorded) != 64:
        return MISMATCH
    if sha256_file(path) == recorded:
        return MATCH
    if sha256_file_lf(path) == recorded:
        return MATCH_EOL_NORMALIZED
    if sha256_file_crlf(path) == recorded:
        return MATCH_CRLF_RECORDED
    return MISMATCH


def digest_matches(path: PathLike, recorded: object) -> bool:
    """行尾无关地判定是否一致。真漂移返回 False。"""
    return compare_digest(path, recorded) != MISMATCH


def digest_diagnostics(path: PathLike, recorded: object) -> dict[str, str]:
    """返回可审计的判定详情，供门禁写进 diagnostics。

    含判定态、记录值与三种归一化实测值，便于人工一眼看出漂移性质，
    而不是只拿到一个 false。
    """
    kind = compare_digest(path, recorded)
    return {
        "digest_verdict": kind,
        "recorded_sha256": recorded if isinstance(recorded, str) else "",
        "actual_sha256": sha256_file(path),
        "actual_sha256_lf": sha256_file_lf(path),
        "actual_sha256_crlf": sha256_file_crlf(path),
    }
