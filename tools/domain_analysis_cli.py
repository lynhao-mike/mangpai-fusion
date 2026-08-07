"""六源三领域分析引擎的中文交互与非交互 CLI。"""

from __future__ import annotations

import argparse
import hashlib
import os
import stat
import sys
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from typing import Sequence

from engine.v5.domain import V5RunSnapshot, V5_SCHOOLS
from engine.v5.domain_analysis_report import render_domain_analysis_report
from engine.v5.domain_metadata_integrity import (
    validate_capability_metadata,
    validate_domain_evaluation_metadata,
)
from engine.v5.domain_slices.contract import DOMAIN_IDS, DomainAnalysisRequest
from engine.v5.domain_slices.orchestrator import run_domain_analysis
from tools.output_linter import lint_report_text


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="六源事业、财富、婚姻分析引擎")
    subparsers = parser.add_subparsers(dest="command")
    analyze = subparsers.add_parser("analyze", help="生成 run snapshot 与 Markdown 报告")
    analyze.add_argument("--gender", choices=("乾", "坤"))
    analyze.add_argument("--birth")
    analyze.add_argument("--as-of-date")
    analyze.add_argument("--domains", nargs="+", choices=DOMAIN_IDS)
    analyze.add_argument("--case-id")
    analyze.add_argument("--out")
    analyze.add_argument("--non-interactive", action="store_true")
    audit = subparsers.add_parser("audit", help="只读审计既有 run snapshot")
    audit.add_argument("snapshot")
    return parser


def _parse_request(
    gender: str,
    birth: str,
    as_of: str,
    domains: Sequence[str],
    output_dir: str,
    case_id: str = "",
) -> DomainAnalysisRequest:
    return DomainAnalysisRequest(
        gender=gender,
        birth_datetime=datetime.strptime(birth, "%Y-%m-%d %H:%M"),
        as_of_date=date.fromisoformat(as_of),
        domains=tuple(domains),
        output_dir=output_dir,
        case_id=case_id,
    )


def _interactive_request() -> DomainAnalysisRequest | None:
    print("六源三领域命理分析向导")
    while True:
        try:
            gender = input("性别（乾/坤）：").strip()
            birth = input("已校正公历出生时间（YYYY-MM-DD HH:MM）：").strip()
            as_of = input(f"分析截止日（YYYY-MM-DD，默认 {date.today().isoformat()}）：").strip() or date.today().isoformat()
            raw_domains = input("领域（career wealth marriage，默认全部）：").strip()
            domains = raw_domains.split() if raw_domains else list(DOMAIN_IDS)
            output_dir = input("输出目录（默认 reports/domain-analysis）：").strip() or "reports/domain-analysis"
            request = _parse_request(gender, birth, as_of, domains, output_dir)
            summary = f"{request.gender}造，出生 {request.birth_datetime:%Y-%m-%d %H:%M}，截止 {request.as_of_date}"
            if input(f"排盘请求：{summary}。确认生成？（y/N）：").strip().lower() != "y":
                return None
            return request
        except (ValueError, TypeError) as exc:
            print(f"输入错误：{exc}，请重新输入。")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reject_symlink_chain(path: Path) -> None:
    current = path.absolute()
    while True:
        if current.is_symlink():
            raise ValueError(f"create-only 路径含 symlink：{current}")
        parent = current.parent
        if parent == current:
            return
        current = parent


def _prepare_create_only_targets(output_dir: Path, targets: Sequence[Path]) -> None:
    _reject_symlink_chain(output_dir)
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError("输出路径不是目录")
    output_dir.mkdir(parents=True, exist_ok=True)
    _reject_symlink_chain(output_dir)
    if not output_dir.is_dir():
        raise ValueError("输出路径不是目录")
    for target in targets:
        _reject_symlink_chain(target)
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"create-only 目标已存在：{target}")


def _create_text(path: Path, content: str) -> os.stat_result:
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
            return os.fstat(handle.fileno())
    except FileExistsError as exc:
        raise FileExistsError(f"create-only 目标已存在：{path}") from exc


def _remove_owned_file(path: Path, identity: os.stat_result) -> None:
    try:
        current = path.stat(follow_symlinks=False)
    except OSError:
        return
    if (
        stat.S_ISREG(current.st_mode)
        and current.st_dev == identity.st_dev
        and current.st_ino == identity.st_ino
    ):
        path.unlink(missing_ok=True)


def _write_outputs(request: DomainAnalysisRequest) -> tuple[Path, Path]:
    snapshot = run_domain_analysis(request)
    report = render_domain_analysis_report(snapshot)
    issues = lint_report_text(report)
    if issues:
        raise ValueError(f"report lint failed: {issues}")
    output_dir = Path(request.output_dir)
    stem = snapshot.case_id
    snapshot_path = output_dir / f"{stem}.run.json"
    report_path = output_dir / f"{stem}-content-report.md"
    _prepare_create_only_targets(output_dir, (report_path, snapshot_path))

    report_identity = _create_text(report_path, report)
    try:
        snapshot = replace(
            snapshot,
            artifact_bindings={
                **snapshot.artifact_bindings,
                "report_path": report_path.name,
                "report_sha256": _sha256(report_path),
            },
        )
        _create_text(snapshot_path, snapshot.to_json())
    except BaseException:
        _remove_owned_file(report_path, report_identity)
        raise
    return snapshot_path, report_path



def _coverage_is_valid(coverage: object) -> bool:
    if not isinstance(coverage, list):
        return False
    expected = {(school, domain) for school in V5_SCHOOLS for domain in DOMAIN_IDS}
    actual: set[tuple[str, str]] = set()
    for item in coverage:
        if not isinstance(item, dict):
            return False
        school = item.get("school")
        domain = item.get("domain")
        status = item.get("status")
        audit = item.get("audit")
        if status not in {"implemented", "abstain", "unsupported"} or not isinstance(audit, dict):
            return False
        actual.add((school, domain))
    return len(coverage) == len(expected) and actual == expected



def _audit(path: str) -> int:
    snapshot_path = Path(path)
    snapshot = V5RunSnapshot.from_json(snapshot_path.read_text(encoding="utf-8"))
    if not snapshot.output_hash_matches():
        print("审计失败：快照 output hash 不匹配。", file=sys.stderr)
        return 1
    if not _coverage_is_valid(snapshot.metadata.get("slice_coverage")):
        print("审计失败：十八槽位身份或状态不完整。", file=sys.stderr)
        return 1
    validate_capability_metadata(snapshot.metadata)
    try:
        validate_domain_evaluation_metadata(snapshot.claims, snapshot.metadata)
    except ValueError as exc:
        raise ValueError(f"domain evaluation runtime claims 重投影校验失败：{exc}") from exc
    if any(not claim.evidence for claim in snapshot.claims):
        print("审计失败：存在缺少证据的命题。", file=sys.stderr)
        return 1
    report_name = snapshot.artifact_bindings.get("report_path", "")
    expected_report_hash = snapshot.artifact_bindings.get("report_sha256", "")
    if not report_name or Path(report_name).name != report_name or not expected_report_hash:
        print("审计失败：报告绑定缺失或路径不安全。", file=sys.stderr)
        return 1
    report_path = snapshot_path.parent / report_name
    if not report_path.is_file() or _sha256(report_path) != expected_report_hash:
        print("审计失败：报告绑定 hash 不匹配。", file=sys.stderr)
        return 1
    print(f"审计通过：{snapshot.run_id}")
    return 0

def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    if args.command == "audit":
        try:
            return _audit(args.snapshot)
        except (OSError, ValueError, KeyError) as exc:
            print(f"审计失败：{exc}", file=sys.stderr)
            return 1

    if args.command is None:
        request = _interactive_request()
        if request is None:
            print("已取消，未生成文件。")
            return 1
    elif args.non_interactive:
        missing = [name for name in ("gender", "birth", "as_of_date", "domains", "out") if not getattr(args, name)]
        if missing:
            print("缺少必填参数：" + ", ".join(missing), file=sys.stderr)
            return 2
        try:
            request = _parse_request(args.gender, args.birth, args.as_of_date, args.domains, args.out, args.case_id or "")
        except ValueError as exc:
            print(f"参数错误：{exc}", file=sys.stderr)
            return 2
    else:
        print("analyze 参数模式必须显式使用 --non-interactive；无参数可进入交互向导。", file=sys.stderr)
        return 2

    try:
        snapshot_path, report_path = _write_outputs(request)
    except (OSError, ValueError) as exc:
        print(f"生成失败：{exc}", file=sys.stderr)
        return 1
    print(f"run snapshot：{snapshot_path}")
    print(f"Markdown 报告：{report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
