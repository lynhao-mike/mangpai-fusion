from __future__ import annotations

from pathlib import Path

from engine.pipeline import run_pipeline
from engine.predicates.types import adapt_parsed
from tools.preflight import parse
from tools.render_report import render_from_output

RAW_SUFFIXES = ["RF000771", "RF000551", "RF000894", "RF000684"]


def main() -> int:
    reports: list[str] = []
    cases_dir = Path("cases")
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    for suffix in RAW_SUFFIXES:
        matches = sorted(cases_dir.glob(f"C-2026-{suffix}-*/input.md"))
        if len(matches) != 1:
            raise RuntimeError(f"expected exactly one input for {suffix}, got {len(matches)}: {matches}")
        input_path = matches[0]
        parsed = parse(input_path)
        adapted = adapt_parsed(parsed)
        analysis_output = run_pipeline(adapted)
        report_md = render_from_output(analysis_output, variant="standard", lint_before=True)
        report_path = reports_dir / f"{parsed.case_id}-analyst-report.md"
        report_path.write_text(report_md, encoding="utf-8")
        reports.append(report_path.as_posix())

    print("\n".join(reports))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
