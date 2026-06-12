# -*- coding: utf-8 -*-
"""P6-A1 New Case Feedback Traceability Audit (read-only)."""
import json, os, re, sys
from pathlib import Path

CASES = [
    "C-2026-001-乾-庚申戊寅壬子辛丑",
    "C-2026-002-坤-壬戌庚戌戊辰丙辰",
    "C-2026-007-乾-乙丑庚辰己丑庚午",
    "C-2026-008-坤-壬申癸卯丁未壬寅",
    "C-2026-009-乾-庚辰乙酉丙申乙未",
    "C-2026-010-坤-甲子丁卯癸卯庚申",
    "C-2026-011-乾-乙丑乙酉丁丑癸卯",
    "C-2026-012-坤-壬戌癸丑丙申壬辰",
    "C-2026-013-坤-壬申甲辰丙辰己丑",
    "C-2026-014-乾-丙戌庚子乙亥辛巳",
    "C-2026-015-乾-甲寅乙亥丙辰辛卯",
    "C-2026-018-坤-乙丑戊寅乙酉乙酉",
    "C-2026-025-坤-辛未乙未甲辰乙亥",
    "C-2026-026-坤-癸未甲寅壬戌丙午",
    "C-2026-RF000345-乾-癸酉乙丑乙卯乙酉",
    "C-2026-RF000441-乾-癸亥己未己未庚午",
    "C-2026-RF000864-乾-己巳丙子乙卯甲申",
    "C-2026-RF000243-坤-己卯己巳戊午丁巳",
    "C-2026-RF000524-坤-己巳丙寅戊戌丁巳",
    "C-2026-032-乾-癸酉乙卯戊戌甲寅",
]

ROOT = Path("cases")
SID_PATTERN = re.compile(r"\[S-[A-Za-z0-9_\-]+\]")


def safe_read(p):
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def main():
    rows = []
    summary = {
        "total": 0,
        "sr_exists": 0,
        "sr_with_records": 0,
        "sr_total_records": 0,
        "md_with_sid": 0,
        "report_with_sid": 0,
        "fb_with_sid": 0,
        "fb_sid_total": 0,
        "report_sid_total": 0,
        "md_sid_total": 0,
    }
    for c in CASES:
        d = ROOT / c
        sr = d / "statement_records.json"
        fb = d / "feedback.md"
        al = d / "analysis.md"

        sr_exists = sr.exists()
        sr_records_n = 0
        sr_ids = []
        if sr_exists:
            try:
                data = json.loads(sr.read_text(encoding="utf-8", errors="ignore"))
                rs = data.get("records", [])
                sr_records_n = len(rs)
                sr_ids = [r.get("statement_id", "") for r in rs]
            except Exception:
                pass

        # collect all md files
        md_files = sorted([f for f in d.iterdir() if f.is_file() and f.suffix == ".md"])
        all_md = ""
        report_md = ""
        for f in md_files:
            t = safe_read(f)
            all_md += "\n=== " + f.name + " ===\n" + t
            # main report candidates (NOT analysis, NOT feedback, NOT input, NOT lessons, NOT portrait, NOT career, NOT events, NOT blind-report kind)
            if f.name in ("input.md", "feedback.md", "lessons.md", "analysis.md",
                          "career-projection.md", "portrait-v2.md", "events.md"):
                continue
            report_md += "\n=== " + f.name + " ===\n" + t
        if not report_md:
            # fallback: use analysis.md as best-effort main report
            report_md = safe_read(al)

        fb_text = safe_read(fb)
        al_text = safe_read(al)

        sids_all = sorted(set(SID_PATTERN.findall(all_md)))
        sids_report = sorted(set(SID_PATTERN.findall(report_md)))
        sids_fb = sorted(set(SID_PATTERN.findall(fb_text)))
        sids_al = sorted(set(SID_PATTERN.findall(al_text)))

        summary["total"] += 1
        if sr_exists:
            summary["sr_exists"] += 1
        if sr_records_n > 0:
            summary["sr_with_records"] += 1
        summary["sr_total_records"] += sr_records_n
        if sids_all:
            summary["md_with_sid"] += 1
        if sids_report:
            summary["report_with_sid"] += 1
        if sids_fb:
            summary["fb_with_sid"] += 1
        summary["fb_sid_total"] += len(sids_fb)
        summary["report_sid_total"] += len(sids_report)
        summary["md_sid_total"] += len(sids_all)

        rows.append({
            "case": c,
            "sr_exists": sr_exists,
            "sr_records": sr_records_n,
            "sr_sample_ids": sr_ids[:5],
            "report_sids": sids_report,
            "fb_sids": sids_fb,
            "all_md_sids": sids_all,
            "md_files": [f.name for f in md_files],
        })

    out_dir = Path("META")
    out_dir.mkdir(exist_ok=True)
    out = out_dir / "new-case-feedback-traceability.json"
    out.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")

    # also print to stdout for visibility
    print("=== P6-A1 SUMMARY ===")
    for k, v in summary.items():
        print("  %s: %s" % (k, v))
    print("=== PER-CASE ===")
    for r in rows:
        print("[%s] sr=%s recs=%s | report_sids=%d %s | fb_sids=%d %s" % (
            r["case"], r["sr_exists"], r["sr_records"],
            len(r["report_sids"]), r["report_sids"][:3],
            len(r["fb_sids"]), r["fb_sids"][:3],
        ))


if __name__ == "__main__":
    main()
