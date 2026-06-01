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


def check_links() -> list[str]:
    errors: list[str] = []
    md_files = list(REPORTS_DIR.glob("*.md"))
    md_files.extend(p for p in CASES_DIR.glob("C-*/*.md") if p.is_file())
    for md_path in sorted(md_files):
        text = md_path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), 1):
            for match in LINK_RE.finditer(line):
                target = match.group(1)
                if ("reports/" in target or "cases/" in target or target.endswith((".md", ".json"))) and not target_exists(md_path, target):
                    errors.append(f"{md_path.relative_to(ROOT).as_posix()}:{line_no}: missing target {target}")
    return errors


def check_sibling_reports() -> list[str]:
    errors: list[str] = []
    by_case: dict[str, list[Path]] = {}
    for report in REPORTS_DIR.glob("C-*.md"):
        match = CASE_ID_RE.search(report.name)
        if match:
            by_case.setdefault(match.group(1), []).append(report)
    for reports in by_case.values():
        if len(reports) < 2:
            continue
        for report in reports:
            text = report.read_text(encoding="utf-8")
            for sibling in reports:
                if sibling != report and sibling.name not in text:
                    errors.append(
                        f"{report.relative_to(ROOT).as_posix()}: missing sibling report link {sibling.name}"
                    )
    return errors


def main() -> None:
    errors = check_links() + check_sibling_reports()
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print("archive links ok")


if __name__ == "__main__":
    main()
