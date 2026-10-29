"""Fail a bundle hand-off when reserved case ids are present.

Scans a directory or a zip archive (entry names and file contents) for
identifiers carrying the reserved prefixes ``A60-``, ``PF-``, ``P1-H`` or
``G20`` (for example ``A60-001``, ``A60-CH01``, ``PF-007``, ``P1-H01``,
``G20-003``). A hit means the bundle still links back to a blind/adjudication
case and must not be handed to a runner.

Exit codes:
    0  clean
    1  at least one reserved case id found
    2  usage or IO error (missing target, unreadable archive, oversized file)

This is a pre-hand-off leak gate, not a sanitizer: it never rewrites files.
Nested archives inside a scanned directory are not expanded; zip members are
read directly, so a nested zip is only found if its raw bytes contain an id.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import zipfile
from pathlib import Path

CASE_ID_RE = re.compile(
    rb"(?<![0-9A-Za-z])(?:A60|PF|G20)-[0-9A-Za-z]+"
    rb"|(?<![0-9A-Za-z])P1-H[0-9A-Za-z]+",
    re.IGNORECASE,
)
CHUNK_SIZE = 1 << 20
OVERLAP = 64
MAX_FILE_BYTES = 64 * 1024 * 1024


class ScanError(RuntimeError):
    """The target could not be scanned reliably (fail closed)."""


def _ids_in_text(text: str) -> set[str]:
    encoded = text.encode("utf-8", "surrogateescape")
    return {
        match.group(0).decode("ascii", "replace")
        for match in CASE_ID_RE.finditer(encoded)
    }


def _ids_in_stream(stream) -> set[str]:
    found: set[str] = set()
    tail = b""
    while True:
        chunk = stream.read(CHUNK_SIZE)
        if not chunk:
            break
        buffer = tail + chunk
        for match in CASE_ID_RE.finditer(buffer):
            found.add(match.group(0).decode("ascii", "replace"))
        tail = buffer[-OVERLAP:]
    return found


def _check_size(label: str, size: int) -> None:
    if size > MAX_FILE_BYTES:
        raise ScanError(
            f"{label}: {size} bytes exceeds the {MAX_FILE_BYTES}-byte scan cap; "
            "split the bundle or inspect it manually"
        )


def _scan_directory(root: Path, findings: list[tuple[str, str]]) -> int:
    scanned = 0
    root_ids = _ids_in_text(root.name)
    for case_id in sorted(root_ids):
        findings.append(("(directory name)", case_id))
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames.sort()
        filenames.sort()
        for name in filenames:
            path = Path(dirpath) / name
            if path.is_symlink() or not path.is_file():
                continue
            scanned += 1
            label = path.relative_to(root).as_posix()
            ids = _ids_in_text(label)
            _check_size(label, path.stat().st_size)
            try:
                with path.open("rb") as stream:
                    ids |= _ids_in_stream(stream)
            except OSError as exc:
                raise ScanError(f"{label}: {exc}") from exc
            for case_id in sorted(ids):
                findings.append((label, case_id))
    return scanned


def _scan_zip(path: Path, findings: list[tuple[str, str]]) -> int:
    scanned = 0
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise ScanError(f"{path}: cannot open zip: {exc}") from exc
    with archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            scanned += 1
            label = f"{path}!{info.filename}"
            ids = _ids_in_text(info.filename)
            _check_size(label, info.file_size)
            try:
                with archive.open(info) as stream:
                    ids |= _ids_in_stream(stream)
            except (OSError, RuntimeError, NotImplementedError, zipfile.BadZipFile) as exc:
                raise ScanError(f"{label}: {exc}") from exc
            for case_id in sorted(ids):
                findings.append((label, case_id))
    return scanned


def scan_targets(targets: list[Path]) -> tuple[list[tuple[str, str]], int]:
    findings: list[tuple[str, str]] = []
    scanned = 0
    for target in targets:
        if not target.exists():
            raise ScanError(f"{target}: target does not exist")
        if target.is_dir():
            scanned += _scan_directory(target, findings)
        elif zipfile.is_zipfile(target):
            scanned += _scan_zip(target, findings)
        else:
            raise ScanError(f"{target}: not a directory or zip archive")
    return findings, scanned


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Exit 1 if a bundle contains reserved A60-/PF-/P1-H/G20 case ids."
    )
    parser.add_argument("targets", nargs="+", type=Path, help="zip archive or directory to scan")
    args = parser.parse_args(argv)
    try:
        findings, scanned = scan_targets(args.targets)
    except ScanError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if findings:
        for label, case_id in findings:
            print(f"CASE_ID_FOUND {case_id} in {label}")
        print(f"FAIL: {len(findings)} reserved case id hit(s) in {scanned} scanned file(s)")
        return 1
    print(f"OK: {scanned} file(s) scanned; no A60-/PF-/P1-H/G20 case ids")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
