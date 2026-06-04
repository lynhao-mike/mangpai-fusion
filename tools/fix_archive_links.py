"""Normalize clickable archive links between case files and reports.

This maintenance helper focuses on human-facing markdown archive references:
- reports/*.md association sections should link back to cases/ and sibling reports.
- cases/C-*/ markdown files should link to related reports and local case files.

It is intentionally conservative: it only rewrites plain archive paths in markdown prose,
and skips fenced code blocks and already-linked markdown destinations.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
CASES_DIR = ROOT / "cases"

PATH_RE = re.compile(
    r"(?<!\]\()(?<![\w./-])"
    r"((?:reports/[^\s`，。；;）)]+\.md)|"
    r"(?:cases/C-[^\s`，。；;）)]+/(?:(?:input|analysis|feedback|future-events|events|lessons)\.md|statement_index\.json))|"
    r"(?:cases/C-[^\s`，。；;）)]+/))"
)


def is_inside_markdown_link(line: str, start: int) -> bool:
    """Return True if the match is already inside a markdown link destination."""
    before = line[:start]
    # Already handled direct `](` by regex, but keep a broader same-line guard.
    last_open = before.rfind("](")
    last_close = before.rfind(")")
    return last_open > last_close


def is_inside_inline_code(line: str, start: int) -> bool:
    return line[:start].count("`") % 2 == 1


def link_target(md_path: Path, raw_path: str) -> str:
    """Build a markdown target without depending on Windows ANSI path decoding.

    The repository contains Chinese filenames. In cmd.exe sessions Python may see
    those filenames through the active ANSI code page, so existence/resolve based
    path math can fall back incorrectly. Archive references are all rooted at
    either reports/ or cases/, therefore deterministic textual rewriting is safer.
    """
    rel = md_path.relative_to(ROOT).as_posix()
    if rel.startswith("reports/"):
        if raw_path.startswith("cases/"):
            return "../" + raw_path
        if raw_path.startswith("reports/"):
            return raw_path.removeprefix("reports/")
        return raw_path
    if rel.startswith("cases/C-"):
        case_dir = rel.rsplit("/", 1)[0]
        if raw_path.startswith("reports/"):
            return "../../" + raw_path
        if raw_path.startswith(case_dir + "/"):
            return raw_path.removeprefix(case_dir + "/")
        if raw_path.startswith("cases/"):
            return "../" + raw_path.removeprefix("cases/")
        return raw_path
    return raw_path


def link_label(raw_path: str) -> str:
    if raw_path.endswith("/"):
        return raw_path.rstrip("/").split("/")[-1] + "/"
    return raw_path.split("/")[-1]


def rewrite_line(md_path: Path, line: str) -> str:
    def repl(match: re.Match[str]) -> str:
        raw = match.group(1)
        if is_inside_markdown_link(line, match.start(1)) or is_inside_inline_code(line, match.start(1)):
            return raw
        return f"[{link_label(raw)}]({link_target(md_path, raw)})"

    return PATH_RE.sub(repl, line)


LINK_DEST_RE = re.compile(r"\]\((cases/[^)]+|reports/[^)]+)\)")
CASE_ID_RE = re.compile(r"(C-\d{4}-\d{3})-")


def fix_existing_destinations(md_path: Path, line: str) -> str:
    def repl(match: re.Match[str]) -> str:
        return f"]({link_target(md_path, match.group(1))})"

    return LINK_DEST_RE.sub(repl, line)


def rewrite_text(md_path: Path, text: str) -> tuple[bool, str]:
    lines = text.splitlines(keepends=True)
    changed = False
    in_fence = False
    out: list[str] = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        new_line = fix_existing_destinations(md_path, rewrite_line(md_path, line))
        if new_line != line:
            changed = True
        out.append(new_line)
    return changed, "".join(out)


def rewrite_file(md_path: Path) -> bool:
    text = md_path.read_text(encoding="utf-8")
    changed, new_text = rewrite_text(md_path, text)
    if changed:
        md_path.write_text(new_text, encoding="utf-8")
    return changed


def ensure_report_cross_links(report_path: Path, sibling_reports: list[Path], text: str | None = None) -> bool:
    if text is None:
        text = report_path.read_text(encoding="utf-8")
    additions: list[str] = []
    for sibling in sibling_reports:
        if sibling == report_path:
            continue
        sibling_name = sibling.name
        if sibling_name not in text:
            label = "关联报告" if "-report" in sibling_name else "关联文件"
            target = sibling.relative_to(report_path.parent).as_posix()
            additions.append(f"- {label}：[{sibling_name}]({target})")
    if not additions:
        return False
    if not text.endswith("\n"):
        text += "\n"
    text += "\n" + "\n".join(additions) + "\n"
    report_path.write_text(text, encoding="utf-8")
    return True


def case_key(report_path: Path) -> str | None:
    match = CASE_ID_RE.match(report_path.name)
    return match.group(1) if match else None


def main() -> None:
    changed: list[str] = []
    changed_set: set[str] = set()

    report_files = sorted(REPORTS_DIR.glob("*.md"))
    case_md_files = sorted(p for p in CASES_DIR.glob("C-*/*.md") if p.is_file())
    md_files = [*report_files, *case_md_files]
    report_text_cache: dict[Path, str] = {}

    for md_path in md_files:
        try:
            text = md_path.read_text(encoding="utf-8")
        except OSError:
            continue
        changed_file, new_text = rewrite_text(md_path, text)
        if changed_file:
            md_path.write_text(new_text, encoding="utf-8")
            text = new_text
            rel = md_path.relative_to(ROOT).as_posix()
            if rel not in changed_set:
                changed.append(rel)
                changed_set.add(rel)
        if md_path in report_files:
            # 复用本轮已读取/重写后的报告文本，避免 sibling cross-link 阶段重复 I/O。
            report_text_cache[md_path] = text

    reports_by_case: dict[str, list[Path]] = {}
    for report in report_files:
        key = case_key(report)
        if key:
            reports_by_case.setdefault(key, []).append(report)

    for siblings in reports_by_case.values():
        if len(siblings) < 2:
            continue
        siblings = sorted(siblings)
        for report in siblings:
            if ensure_report_cross_links(report, siblings, report_text_cache.get(report)):
                rel = report.relative_to(ROOT).as_posix()
                if rel not in changed_set:
                    changed.append(rel)
                    changed_set.add(rel)

    for rel in changed:
        print(rel)


if __name__ == "__main__":
    main()
