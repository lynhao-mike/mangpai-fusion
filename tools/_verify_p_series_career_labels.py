import json
import re
from collections import Counter
from pathlib import Path

SOURCE_PATH = Path("cases/fankui-feedback.md")
LABELS_PATH = Path("cases/p-series-career-path-labels.jsonl")
REPORT_PATH = Path("reports/p-series-career-path-labeling-summary.md")

source_text = SOURCE_PATH.read_text(encoding="utf-8")
report_text = REPORT_PATH.read_text(encoding="utf-8")
rows = [
    json.loads(line)
    for line in LABELS_PATH.read_text(encoding="utf-8").splitlines()
    if line.strip()
]

expected_ids = [f"P-2026-{number:03d}" for number in range(1, 77)]
actual_ids = [row["case_id"] for row in rows]
required_fields = {
    "case_id",
    "label",
    "confidence",
    "evidence_quote",
    "rationale",
    "review_status",
    "source",
}
allowed_labels = {"employment", "entrepreneurship", "mixed", "unknown"}
allowed_confidence = {"high", "medium", "low"}

assert len(rows) == 76, f"expected 76 rows, got {len(rows)}"
assert len(actual_ids) == len(set(actual_ids)), "case_id values are not unique"
assert set(actual_ids) == set(expected_ids), "case_id coverage mismatch"
assert actual_ids == expected_ids, "case_id rows are not in P-2026-001..076 order"

for row in rows:
    assert set(row) == required_fields, f"field mismatch: {row['case_id']}"
    assert row["label"] in allowed_labels, f"invalid label: {row['case_id']}"
    assert row["confidence"] in allowed_confidence, f"invalid confidence: {row['case_id']}"
    assert row["review_status"] == "manual_reviewed", f"invalid review_status: {row['case_id']}"
    assert row["source"] == "cases/fankui-feedback.md", f"invalid source: {row['case_id']}"
    assert isinstance(row["evidence_quote"], str), f"non-string evidence: {row['case_id']}"
    assert row["rationale"].strip(), f"empty rationale: {row['case_id']}"

headings = list(re.finditer(r"^## (P-2026-\d{3})\b.*$", source_text, flags=re.MULTILINE))
sections = {}
for index, match in enumerate(headings):
    end = headings[index + 1].start() if index + 1 < len(headings) else len(source_text)
    sections[match.group(1)] = source_text[match.start():end]

assert set(sections) == set(expected_ids), "source sections do not cover expected IDs"
for row in rows:
    quote = row["evidence_quote"]
    if quote:
        assert quote in sections[row["case_id"]], f"quote not found in section: {row['case_id']} -> {quote}"

label_counts = Counter(row["label"] for row in rows)
confidence_counts = Counter(row["confidence"] for row in rows)
expected_label_counts = {
    "employment": 32,
    "entrepreneurship": 5,
    "mixed": 3,
    "unknown": 36,
}
expected_confidence_counts = {"high": 57, "medium": 15, "low": 4}
assert dict(label_counts) == expected_label_counts, f"label counts mismatch: {dict(label_counts)}"
assert dict(confidence_counts) == expected_confidence_counts, f"confidence counts mismatch: {dict(confidence_counts)}"

non_unknown = sum(row["label"] != "unknown" for row in rows)
assert non_unknown == 40
assert f"| 非 unknown 有效案例 | {non_unknown} |" in report_text
assert "| 非 unknown 有效率 | 52.63% |" in report_text
for label, count in expected_label_counts.items():
    assert f"| {label} | {count} |" in report_text
for confidence, count in expected_confidence_counts.items():
    assert f"| {confidence} | {count} |" in report_text

for row in rows:
    assert report_text.count(f"| {row['case_id']} |") >= 1, f"missing audit row: {row['case_id']}"

print("PASS: 76 rows exactly")
print("PASS: case_id unique, ordered, and complete P-2026-001..076")
print("PASS: fields and enum values valid")
print("PASS: every non-empty evidence_quote is verbatim in its own source section")
print(f"PASS: label counts {dict(label_counts)}")
print(f"PASS: confidence counts {dict(confidence_counts)}")
print("PASS: summary metrics and all 76 audit rows present")
