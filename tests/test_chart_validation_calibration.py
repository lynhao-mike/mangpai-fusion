"""仓库现有案例排盘校准工具测试。"""
from __future__ import annotations

from pathlib import Path

from tools.chart_validation_calibrate import audit_case_file, audit_repository_cases


CASE_YAML = """```yaml
schema_version: "1.2.0"
case_meta:
  case_id: "{case_id}"
  来源: "问真八字 APP 排盘"
birth:
  性别: "M"
  公历: "1980-02-09 02:00"
  来源: "问真八字 APP 排盘"
四柱:
  年柱: "庚申"
  月柱: "{month_pillar}"
  日柱: "壬子"
  时柱: "辛丑"
大运:
  起运岁: 8
  顺逆: "顺"
  排布:
    - {{干支: "己卯"}}
    - {{干支: "庚辰"}}
    - {{干支: "辛巳"}}
```
"""


def _write_case(root: Path, case_id: str, month_pillar: str = "戊寅") -> Path:
    case_dir = root / case_id
    case_dir.mkdir(parents=True)
    path = case_dir / "input.md"
    path.write_text(
        CASE_YAML.format(case_id=case_id, month_pillar=month_pillar),
        encoding="utf-8",
    )
    return path


def test_audit_case_forces_recalculation_even_for_wenzhen(tmp_path: Path) -> None:
    path = _write_case(tmp_path, "C-TEST-001-乾-庚申戊寅壬子辛丑")

    record = audit_case_file(path)

    assert record["eligible"] is True
    assert record["trusted_source"] is True
    assert record["validation_skipped"] is False
    assert record["status"] == "pass"
    assert record["pillar_checks"] == {
        "年柱": True,
        "月柱": True,
        "日柱": True,
        "时柱": True,
    }
    assert record["dayun_direction_ok"] is True
    assert record["dayun_sequence_ok"] is True
    assert record["qiyun_age_ok"] is True


def test_audit_case_reports_wrong_wenzhen_chart_instead_of_bypassing(tmp_path: Path) -> None:
    path = _write_case(
        tmp_path,
        "C-TEST-002-乾-庚申丁丑壬子辛丑",
        month_pillar="丁丑",
    )

    record = audit_case_file(path)

    assert record["status"] == "fail"
    assert record["pillar_checks"]["月柱"] is False
    assert record["corrected_pillars"]["月柱"] == "戊寅"


def test_repository_summary_counts_eligible_pass_and_fail(tmp_path: Path) -> None:
    _write_case(tmp_path, "C-TEST-001-乾-庚申戊寅壬子辛丑")
    _write_case(
        tmp_path,
        "C-TEST-002-乾-庚申丁丑壬子辛丑",
        month_pillar="丁丑",
    )

    result = audit_repository_cases(tmp_path)

    assert result["summary"]["eligible"] == 2
    assert result["summary"]["passed"] == 1
    assert result["summary"]["failed"] == 1
    assert result["summary"]["qiyun_age_failures"] == 0


def test_existing_repository_has_at_least_30_full_pass_cases() -> None:
    """以仓库现有案例实际重算，至少 30 案必须四柱/大运/起运全通过。"""
    result = audit_repository_cases(Path("cases"))
    summary = result["summary"]

    assert summary["eligible"] >= 30
    assert summary["trusted_source_eligible"] >= 30
    assert summary["passed"] >= 30
    assert all(
        record.get("validation_skipped") is False
        for record in result["records"]
        if record["eligible"]
    )
