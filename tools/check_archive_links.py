"""Check report/case markdown archive links.

This validator checks two things:
1. Every markdown link that targets reports/ or cases/ resolves to an existing file.
2. Cases with multiple reports have each report linking every sibling report.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
CASES_DIR = ROOT / "cases"
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)")
CASE_ID_RE = re.compile(r"(C-\d{4}-\d{3})-")


def target_exists(md_path: Path, target: str) -> bool:
    if target.startswith(("http://", "https://", "mailto:")):
        return True
    return (md_path.parent / target).resolve().exists()


def _iter_markdown_files() -> list[Path]:
    md_files = list(REPORTS_DIR.glob("*.md"))
    md_files.extend(p for p in CASES_DIR.glob("C-*/*.md") if p.is_file())
    return sorted(md_files)


def _read_texts(paths: list[Path]) -> dict[Path, str]:
    texts: dict[Path, str] = {}
    for path in paths:
        try:
            texts[path] = path.read_text(encoding="utf-8")
        except OSError:
            texts[path] = ""
    return texts


def check_links(texts: dict[Path, str] | None = None) -> list[str]:
    errors: list[str] = []
    if texts is None:
        texts = _read_texts(_iter_markdown_files())
    for md_path, text in texts.items():
        for line_no, line in enumerate(text.splitlines(), 1):
            for match in LINK_RE.finditer(line):
                target = match.group(1)
                if ("reports/" in target or "cases/" in target or target.endswith((".md", ".json"))) and not target_exists(md_path, target):
                    errors.append(f"{md_path.relative_to(ROOT).as_posix()}:{line_no}: missing target {target}")
    return errors


def check_sibling_reports(texts: dict[Path, str] | None = None) -> list[str]:
    errors: list[str] = []
    report_paths = sorted(REPORTS_DIR.glob("C-*.md"))
    if texts is None:
        texts = _read_texts(report_paths)
    by_case: dict[str, list[Path]] = {}
    for report in report_paths:
        match = CASE_ID_RE.search(report.name)
        if match:
            by_case.setdefault(match.group(1), []).append(report)
    for reports in by_case.values():
        if len(reports) < 2:
            continue
        sibling_names_by_report = {
            report: {sibling.name for sibling in reports if sibling != report}
            for report in reports
        }
        for report, sibling_names in sibling_names_by_report.items():
            text = texts.get(report, "")
            missing = [name for name in sibling_names if name not in text]
            for sibling_name in missing:
                errors.append(
                    f"{report.relative_to(ROOT).as_posix()}: missing sibling report link {sibling_name}"
                )
    return errors


def main() -> None:
    texts = _read_texts(_iter_markdown_files())
    errors = check_links(texts) + check_sibling_reports(texts)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print("archive links ok")


if __name__ == "__main__":
    main()
