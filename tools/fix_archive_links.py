"""Safely migrate historical Markdown archive links.

The migration is deterministic and conservative:
- normalize repository-root destinations in reports and known nested v6 links;
- replace legacy report names only when exactly one same-full-identity content report exists;
- preserve and report unresolved legacy references instead of inventing files;
- add bidirectional sibling links only for the same full case identity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
CASES_DIR = ROOT / "cases"

FULL_CASE_ID_PATTERN = r"C-\d{4}-(?:\d{3}|RF\d+)-(?:乾|坤)-[^\-/\s)]+"
FULL_CASE_ID_RE = re.compile(rf"({FULL_CASE_ID_PATTERN})")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)#]+)(#[^)]*)?\)")
NESTED_GENERATED_LINK_RE = re.compile(
    r"\[([^\]]+)\]\(\[\1\]\(([^)]+)\)\)"
)
LEGACY_REPORT_NAME_RE = re.compile(
    rf"^(?P<identity>{FULL_CASE_ID_PATTERN})-(?P<suffix>"
    r"report(?:-master|-v2)?|analyst-report|career-marriage-report|"
    r"future-choice-report|future-events-report)\.md$"
)
CANONICAL_REPORT_RE = re.compile(
    rf"^(?P<identity>{FULL_CASE_ID_PATTERN})(?:-v6-preprod)?-content-report\.md$"
)


@dataclass(frozen=True)
class UnresolvedLink:
    source: str
    line: int
    target: str
    reason: str


@dataclass(frozen=True)
class MigrationResult:
    changed: list[str]
    unresolved: list[UnresolvedLink]


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _identity(path_or_name: str) -> str | None:
    match = FULL_CASE_ID_RE.search(path_or_name)
    return match.group(1) if match else None


def _canonical_reports(reports_dir: Path) -> dict[str, list[Path]]:
    by_identity: dict[str, list[Path]] = {}
    for path in sorted(reports_dir.glob("C-*.md")):
        match = CANONICAL_REPORT_RE.match(path.name)
        if match:
            by_identity.setdefault(match.group("identity"), []).append(path)
    return by_identity


def _target_for(md_path: Path, repository_target: str, root: Path) -> str:
    """Return a POSIX link from ``md_path`` to a repository-relative target."""
    target = root / repository_target.rstrip("/")
    try:
        return target.relative_to(md_path.parent).as_posix()
    except ValueError:
        # pathlib.relative_to does not calculate paths containing ``..``.
        import os

        return Path(os.path.relpath(target, md_path.parent)).as_posix()


def _normalize_root_target(md_path: Path, target: str, root: Path) -> str:
    if target.startswith("reports/"):
        return _target_for(md_path, target, root)
    if target.startswith("cases/"):
        return _target_for(md_path, target, root)
    return target


def _legacy_replacement(
    md_path: Path,
    target: str,
    canonical: dict[str, list[Path]],
    root: Path,
) -> tuple[str, str | None]:
    name = Path(target).name
    match = LEGACY_REPORT_NAME_RE.match(name)
    if not match:
        return target, None
    if (md_path.parent / target).resolve().is_file():
        return target, None

    identity = match.group("identity")
    candidates = canonical.get(identity, [])
    if len(candidates) == 1:
        return _target_for(md_path, f"reports/{candidates[0].name}", root), None
    if not candidates:
        return target, "no canonical report for full case identity"
    return target, "multiple canonical reports for full case identity"


def _rewrite_text(
    md_path: Path,
    text: str,
    canonical: dict[str, list[Path]],
    root: Path,
) -> tuple[str, list[UnresolvedLink]]:
    unresolved: list[UnresolvedLink] = []
    out: list[str] = []
    in_fence = False

    for line_no, line in enumerate(text.splitlines(keepends=True), 1):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue

        # Historical v6 output duplicated a complete link as both outer label and target.
        line = NESTED_GENERATED_LINK_RE.sub(lambda m: f"[{m.group(1)}]({m.group(2)})", line)

        def replace_link(match: re.Match[str]) -> str:
            label, target, anchor = match.group(1), match.group(2), match.group(3) or ""
            replacement, reason = _legacy_replacement(md_path, target, canonical, root)
            if reason is not None:
                unresolved.append(
                    UnresolvedLink(_relative(md_path, root), line_no, target, reason)
                )
                return match.group(0)
            replacement = _normalize_root_target(md_path, replacement, root)
            return f"[{label}]({replacement}{anchor})"

        out.append(MARKDOWN_LINK_RE.sub(replace_link, line))

    return "".join(out), unresolved


def _append_sibling_links(report: Path, siblings: list[Path], text: str) -> str:
    additions = [
        f"- 关联报告：[{sibling.name}]({sibling.name})"
        for sibling in siblings
        if sibling != report and sibling.name not in text
    ]
    if not additions:
        return text
    return text.rstrip("\n") + "\n\n" + "\n".join(additions) + "\n"


def migrate_archive(root: Path = ROOT) -> MigrationResult:
    """Migrate archive Markdown under ``root`` and return an auditable result."""
    reports_dir = root / "reports"
    cases_dir = root / "cases"
    report_files = sorted(reports_dir.glob("*.md"))
    case_files = sorted(path for path in cases_dir.glob("C-*/*.md") if path.is_file())
    canonical = _canonical_reports(reports_dir)
    changed: set[str] = set()
    unresolved: list[UnresolvedLink] = []
    texts: dict[Path, str] = {}

    for md_path in [*report_files, *case_files]:
        try:
            original = md_path.read_text(encoding="utf-8")
        except OSError:
            continue
        migrated, file_unresolved = _rewrite_text(md_path, original, canonical, root)
        unresolved.extend(file_unresolved)
        texts[md_path] = migrated
        if migrated != original:
            md_path.write_text(migrated, encoding="utf-8")
            changed.add(_relative(md_path, root))

    readme = reports_dir / "README.md"
    template = root / "templates" / "report-v6.md"
    if readme in texts and template.exists():
        current = texts[readme]
        migrated = current.replace("../templates/report-v1.3.md", "../templates/report-v6.md")
        if migrated != current:
            readme.write_text(migrated, encoding="utf-8")
            texts[readme] = migrated
            changed.add(_relative(readme, root))

    siblings_by_identity: dict[str, list[Path]] = {}
    for report in report_files:
        identity = _identity(report.name)
        if identity:
            siblings_by_identity.setdefault(identity, []).append(report)

    for siblings in siblings_by_identity.values():
        if len(siblings) < 2:
            continue
        siblings = sorted(siblings)
        for report in siblings:
            original = texts.get(report, report.read_text(encoding="utf-8"))
            migrated = _append_sibling_links(report, siblings, original)
            if migrated != original:
                report.write_text(migrated, encoding="utf-8")
                texts[report] = migrated
                changed.add(_relative(report, root))

    return MigrationResult(sorted(changed), sorted(unresolved, key=lambda item: (item.source, item.line, item.target)))


def main() -> None:
    result = migrate_archive()
    for path in result.changed:
        print(f"changed: {path}")
    for item in result.unresolved:
        print(
            f"unresolved: {item.source}:{item.line}: {item.target}"
            f" ({item.reason})"
        )
    print(f"summary: changed={len(result.changed)} unresolved={len(result.unresolved)}")


if __name__ == "__main__":
    main()
