"""基础设施层：文件系统、归档与外部边界适配。"""

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
from engine.infrastructure.findings_repository import _save_findings, save_findings

__all__ = [
    "_save_findings",
    "save_findings",
    "MATCH",
    "MATCH_CRLF_RECORDED",
    "MATCH_EOL_NORMALIZED",
    "MISMATCH",
    "compare_digest",
    "digest_diagnostics",
    "digest_matches",
    "sha256_file",
    "sha256_file_crlf",
    "sha256_file_lf",
]
