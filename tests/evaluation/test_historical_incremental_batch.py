from __future__ import annotations

import json
from pathlib import Path

from tools.school_capability_incremental import HIGH_RISK_TASK_IDS, derive_incremental
from tools.school_capability_task8 import APPROVED_TASK_IDS


def _baseline(path: Path) -> Path:
    case_id = "P-2026-001-乾-甲子乙丑丙寅丁卯"
    path.write_text(json.dumps({
        "schema_version": "six-month-capability-baseline/v1",
        "classification": "historical_blind_candidate",
        "freeze_hash": "a" * 64,
        "case_count": 1,
        "scores": [{"case_id": case_id}],
    }, ensure_ascii=False), encoding="utf-8")
    return path


def test_derive_incremental_excludes_frozen_subject_and_strips_revealed_text(tmp_path: Path) -> None:
    source = tmp_path / "input.md"
    source.write_text(
        """## P-2026-010 · 乾 · 甲子乙丑丙寅丁卯
- 公历生日：2000-01-01 01:00
- 四柱：甲子 乙丑 丙寅 丁卯
- 来源：https://example.invalid/report
---
## P-2026-011 · 坤 · 戊辰己巳庚午辛未
- 公历生日：2001-02-03 04:00
- 四柱：戊辰 己巳 庚午 辛未
- 大运：3岁起运；壬申→癸酉
- 来源：https://example.invalid/feedback
""",
        encoding="utf-8",
    )

    audit, isolated = derive_incremental(source, _baseline(tmp_path / "baseline.json"))

    assert audit["parent_case_count"] == 1
    assert audit["current_deduplicated_case_count"] == 2
    assert audit["incremental_case_ids"] == ["P-2026-011-坤-戊辰己巳庚午辛未"]
    assert "来源" not in isolated
    assert "feedback" not in isolated.lower()
    assert "report" not in isolated.lower()


def test_approved_incremental_tasks_exclude_non_catalog_education_and_identify_all_high_risk() -> None:
    assert "education.attainment_band" not in APPROVED_TASK_IDS
    assert HIGH_RISK_TASK_IDS == {
        "marriage.divorce_or_remarriage",
        "wealth.debt",
        "health.system_risk",
        "health.event_window",
        "wealth.major_loss_window",
    }
