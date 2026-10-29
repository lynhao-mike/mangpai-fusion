"""T-192 verification: archive, redaction, R spec, and bundle scanner.

Standard library only. Run from the repo root:

    .venv\\Scripts\\python.exe tasks\\T-192\\verify.py

Exit 0 = all checks pass. Exit 1 = at least one check failed.
The scanner is exercised only with synthetic fixtures; no real bundle is scanned.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "archive" / "adjudication_v1"
DEMO_ARCH = ROOT / "archive" / "demo"

CASE_ID_RE = re.compile(r"(?:A60|PF|G20)-[0-9A-Za-z]+|P1-H[0-9A-Za-z]+")
CONTAMINATED = {"A60-020", "A60-046", "A60-050"}

# Archived final-v2 answers snapshot (worktree shape used by scorer v2).
FINAL_ANSWERS_SHA256 = "754caa14f4fcffb36385bebf636eef150ae8f6c967fa539463f42ddde6c189d2"

# Pre-status hashes of the two T-176 demo artifacts (archived verbatim).
DEMO_MD_SHA256 = "6695e45058eaf3b06f4063cf3a9b067df11ccce2776e42cf3018078ecd8761e7"
DEMO_JSON_SHA256 = "a644b900fd8adc53662a64f90e85fbaa53e26663a96e2dae4e21106556798e65"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_required_files() -> None:
    required = [
        ARCH / "README.md",
        ARCH / "ANCHOR.md",
        ARCH / "MANIFEST.sha256",
        ARCH / "adjudication-a-plus-v1.md",
        ARCH / "t191-a-plus-verdict-v1.md",
        ARCH / "anchor" / "p1-anchor-60-blind-final-v2.json",
        ARCH / "anchor" / "p1-anchor-60-final-v2.md",
        ARCH / "t191-runs" / "p1-system-run-r1.json",
        ARCH / "t191-runs" / "p1-system-run-r2.json",
        ARCH / "t191-runs" / "p1-system-run-r3.json",
        ARCH / "scorers" / "p1_assertion_eval.py",
        ARCH / "scorers" / "p1_assertion_eval_v2.py",
        ARCH / "restricted" / "README.md",
        ARCH / "restricted" / "p1-anchor-60-answers-v1.json",
        ARCH / "restricted" / "p1-anchor-60-answers-B-v1.json",
        ARCH / "restricted" / "p1-anchor-60-answers-final-v2.json",
        ARCH / "restricted" / "labels-v1.json",
        ARCH / "restricted" / "contamination-list-v1.json",
        DEMO_ARCH / "README.md",
        DEMO_ARCH / "single-chart-cards-v1.md",
        DEMO_ARCH / "single-chart-cards-v1.json",
        ROOT / "docs" / "specs" / "fact-evidence-pack-v1.md",
        ROOT / "tools" / "check_bundle_case_ids.py",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    assert not missing, f"missing files: {missing}"


def check_manifest() -> None:
    manifest = ARCH / "MANIFEST.sha256"
    entries: dict[str, str] = {}
    for line in read(manifest).splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        entries[rel.strip()] = digest.strip()
    actual = {
        path.relative_to(ARCH).as_posix(): path
        for path in ARCH.rglob("*")
        if path.is_file() and path.name != "MANIFEST.sha256"
    }
    assert set(entries) == set(actual), (
        f"manifest mismatch: only_in_manifest={sorted(set(entries) - set(actual))} "
        f"only_on_disk={sorted(set(actual) - set(entries))}"
    )
    for rel, path in actual.items():
        assert sha256(path) == entries[rel], f"hash mismatch: {rel}"


def check_copies() -> None:
    pairs = [
        (ARCH / "adjudication-a-plus-v1.md", ROOT / "docs" / "specs" / "adjudication-a-plus-v1.md"),
        (ARCH / "t191-a-plus-verdict-v1.md", ROOT / "docs" / "reviews" / "t191-a-plus-verdict-v1.md"),
        (ARCH / "anchor" / "p1-anchor-60-blind-final-v2.json", ROOT / "META" / "p1-anchor-60-blind-final-v2.json"),
        (ARCH / "anchor" / "p1-anchor-60-final-v2.md", ROOT / "META" / "p1-anchor-60-final-v2.md"),
        (ARCH / "t191-runs" / "p1-system-run-r1.json", ROOT / "META" / "p1-system-run-r1.json"),
        (ARCH / "t191-runs" / "p1-system-run-r2.json", ROOT / "META" / "p1-system-run-r2.json"),
        (ARCH / "t191-runs" / "p1-system-run-r3.json", ROOT / "META" / "p1-system-run-r3.json"),
        (ARCH / "scorers" / "p1_assertion_eval.py", ROOT / "tools" / "p1_assertion_eval.py"),
        (ARCH / "scorers" / "p1_assertion_eval_v2.py", ROOT / "tools" / "p1_assertion_eval_v2.py"),
        (ARCH / "restricted" / "p1-anchor-60-answers-v1.json", ROOT / "META" / "p1-anchor-60-answers-v1.json"),
        (ARCH / "restricted" / "p1-anchor-60-answers-B-v1.json", ROOT / "META" / "p1-anchor-60-answers-B-v1.json"),
    ]
    for archived, source in pairs:
        assert archived.read_bytes() == source.read_bytes(), f"copy drift: {archived} != {source}"
    # final-v2 answers were already dirty when T-192 started; freeze the archived
    # snapshot by hash instead of tracking a file another task may still rewrite.
    assert (
        sha256(ARCH / "restricted" / "p1-anchor-60-answers-final-v2.json")
        == FINAL_ANSWERS_SHA256
    ), "archived final-v2 answers snapshot changed"


def check_demo() -> None:
    assert sha256(DEMO_ARCH / "single-chart-cards-v1.md") == DEMO_MD_SHA256
    assert sha256(DEMO_ARCH / "single-chart-cards-v1.json") == DEMO_JSON_SHA256
    md = read(ROOT / "docs" / "demo" / "single-chart-cards-v1.md")
    assert "STATUS: ARCHIVED_RESEARCH_ARTIFACT" in "\n".join(md.splitlines()[:8])
    doc = json.loads(read(ROOT / "META" / "single-chart-cards-v1.json"))
    assert doc.get("STATUS") == "ARCHIVED_RESEARCH_ARTIFACT"
    assert len(doc.get("cards", [])) == 3
    assert not CASE_ID_RE.search(json.dumps(doc)), "demo json must not contain case ids"


def check_disposition() -> None:
    for path in (
        ROOT / "docs" / "specs" / "adjudication-a-plus-v1.md",
        ARCH / "adjudication-a-plus-v1.md",
    ):
        assert "DISPOSITION: KILLED" in read(path), f"missing DISPOSITION: KILLED in {path}"


def check_notes_redaction() -> None:
    path = ROOT / "docs" / "specs" / "adjudication-a-plus-v1-notes.md"
    text = read(path)
    assert not CASE_ID_RE.search(text), "notes still contain a case id"
    section = text[text.index("## 5.") :]
    assert "restricted" in section
    assert "3 条分歧" in section
    for token in ("A60-", "未戌", "丑戌", "辰戌", "→", "mutual"):
        assert token not in section, f"notes §5 still exposes {token!r}"


def check_anchor_and_contamination() -> None:
    anchor = read(ARCH / "ANCHOR.md")
    rows = [line for line in anchor.splitlines() if line.startswith("| A60-")]
    assert len(rows) == 60, f"anchor rows={len(rows)}"
    marked = [line for line in rows if line.rstrip().endswith("| contaminated |")]
    assert len(marked) == 3, f"contaminated rows={len(marked)}"
    for case_id in CONTAMINATED:
        assert any(line.startswith(f"| {case_id} |") for line in marked), case_id
    doc = json.loads(read(ARCH / "restricted" / "contamination-list-v1.json"))
    cases = {item["case_id"]: item for item in doc["cases"]}
    assert set(cases) == CONTAMINATED
    assert doc["status"] == "contaminated" and doc["permanent_exclusion"] is True
    for item in cases.values():
        assert item["status"] == "contaminated"
        assert item["permanent_exclusion"] is True
    labels = json.loads(read(ARCH / "restricted" / "labels-v1.json"))
    assert labels["case_count"] == 60 and len(labels["labels"]) == 60


def check_restricted_boundary() -> None:
    public_answers = [
        path
        for path in ARCH.rglob("*")
        if path.is_file()
        and "restricted" not in path.parts
        and path.name.startswith("p1-anchor-60-answers")
    ]
    assert not public_answers, f"answers outside restricted: {public_answers}"
    readme = read(ARCH / "restricted" / "README.md")
    assert "runner 不可读" in readme
    assert "contaminated" in readme


def check_archive_readme() -> None:
    readme = read(ARCH / "README.md")
    for token in ("DISPOSITION: KILLED", "47.5%", "+3", "72.5%", "1/10", "18/20", "A60-020", "A60-046", "A60-050"):
        assert token in readme, f"archive README missing {token!r}"


def check_r_spec() -> None:
    text = read(ROOT / "docs" / "specs" / "fact-evidence-pack-v1.md")
    for token in (
        "类外零发射",
        "第一证明点",
        "事实审计 100%",
        "fixed-20",
        "分流召回预注册",
        "restricted",
        "report-v7-human",
        "保护区",
        "不输出冲/合/穿/刑方向",
        "3 张旧卡不进演示",
        "out_of_class_emissions",
    ):
        assert token in text, f"R spec missing {token!r}"


def _run_tool(target: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "tools.check_bundle_case_ids", str(target)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )


def check_bundle_scanner() -> None:
    tool = ROOT / "tools" / "check_bundle_case_ids.py"
    assert tool.is_file(), "scanner missing"
    with tempfile.TemporaryDirectory(prefix="t192_scan_") as tmp:
        base = Path(tmp)
        (base / "clean").mkdir()
        (base / "clean" / "readme.md").write_text(
            "A60 combat, PFAS, G20 summit, P1-H only\n", encoding="utf-8"
        )
        (base / "dirty_a60").mkdir()
        (base / "dirty_a60" / "notes.md").write_text("case A60-001 leaked\n", encoding="utf-8")
        (base / "dirty_chart").mkdir()
        (base / "dirty_chart" / "c.json").write_text('{"chart_id":"A60-CH01"}\n', encoding="utf-8")
        (base / "dirty_p1h").mkdir()
        (base / "dirty_p1h" / "x.json").write_text('{"case_id":"P1-H01"}\n', encoding="utf-8")

        clean_zip = base / "clean.zip"
        with zipfile.ZipFile(clean_zip, "w") as archive:
            archive.writestr("readme.txt", "nothing here")
        dirty_zip = base / "dirty.zip"
        with zipfile.ZipFile(dirty_zip, "w") as archive:
            archive.writestr("data.json", '{"case_id":"PF-007"}')
            archive.writestr("G20-003.json", "{}")

        cases = [
            (base / "clean", 0),
            (clean_zip, 0),
            (base / "dirty_a60", 1),
            (base / "dirty_chart", 1),
            (base / "dirty_p1h", 1),
            (dirty_zip, 1),
            (base / "missing", 2),
        ]
        for target, expected in cases:
            result = _run_tool(target)
            assert result.returncode == expected, (
                f"scanner {target.name}: exit={result.returncode}, expected {expected}; "
                f"stdout={result.stdout!r} stderr={result.stderr!r}"
            )
        hit = _run_tool(dirty_zip)
        assert "CASE_ID_FOUND" in hit.stdout and "FAIL" in hit.stdout
        clean = _run_tool(clean_zip)
        assert "OK:" in clean.stdout


def check_notes_and_brief() -> None:
    assert (ROOT / "tasks" / "T-192" / "BRIEF.md").is_file(), "BRIEF.md missing"
    status = read(ROOT / "tasks" / "T-192" / "STATUS.md")
    assert "T-192" in status
    assert "Execution Log" in status


CHECKS = [
    ("required_files", check_required_files),
    ("archive_manifest", check_manifest),
    ("archive_copies", check_copies),
    ("demo_archive", check_demo),
    ("disposition_killed", check_disposition),
    ("notes_section5_redaction", check_notes_redaction),
    ("anchor_contamination", check_anchor_and_contamination),
    ("restricted_boundary", check_restricted_boundary),
    ("archive_readme", check_archive_readme),
    ("r_spec", check_r_spec),
    ("bundle_scanner_synthetic", check_bundle_scanner),
    ("task_docs", check_notes_and_brief),
]


def main() -> int:
    failures: list[tuple[str, str]] = []
    for name, check in CHECKS:
        try:
            check()
        except AssertionError as exc:
            failures.append((name, str(exc)))
            print(f"FAIL {name}: {exc}")
        except Exception as exc:  # noqa: BLE001 - verification reports all errors
            failures.append((name, f"{type(exc).__name__}: {exc}"))
            print(f"ERROR {name}: {type(exc).__name__}: {exc}")
        else:
            print(f"PASS {name}")
    if failures:
        print(f"\nFAILED: {len(failures)}/{len(CHECKS)} check(s)")
        return 1
    print(f"\nPASS: {len(CHECKS)}/{len(CHECKS)} checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
