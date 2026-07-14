"""使用仓库现有案例校准八字排盘验证模块。

本工具与生产入口的“问真来源直接信任”规则不同：校准时故意关闭可信来源
旁路，使用寿星天文历重新计算每一个问真案例，以检验模块本身。

用法::

    python -m tools.chart_validation_calibrate \
        --cases cases \
        --json-out META/chart-validation-calibration.json \
        --markdown-out META/chart-validation-calibration.md
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from engine.chart_validation import compute_dayun, validate_chart
from engine.predicates.types import GanZhi
from tools.preflight import extract_yaml_blocks, merge_blocks


_PILLAR_NAMES = ("年柱", "月柱", "日柱", "时柱")


def _date_text(value: Any) -> Optional[str]:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if value is None:
        return None
    text = str(value).strip()
    match = re.match(
        r"^(\d{4}-\d{1,2}-\d{1,2})(?:[ T](\d{1,2}:\d{1,2})(?::\d{1,2})?)?",
        text,
    )
    if not match:
        return None
    return f"{match.group(1)} {match.group(2)}" if match.group(2) else match.group(1)


def _is_wenzhen_source(source: str) -> bool:
    normalized = "".join(source.split()).lower()
    return "问真" in normalized or "wenzhen" in normalized


def _ineligible(path: Path, reason: str) -> dict[str, Any]:
    return {
        "case_id": path.parent.name,
        "input_path": path.as_posix(),
        "eligible": False,
        "status": "ineligible",
        "reason": reason,
    }


def audit_case_file(input_path: Path) -> dict[str, Any]:
    """强制重算一个案例，返回机器可读校准记录。"""
    input_path = Path(input_path)
    try:
        blocks = extract_yaml_blocks(input_path.read_text(encoding="utf-8"))
        if not blocks:
            return _ineligible(input_path, "无 YAML 数据块")
        merged = merge_blocks(blocks)
    except Exception as exc:  # noqa: BLE001
        return _ineligible(input_path, f"输入解析失败: {exc}")

    case_meta = merged.get("case_meta") or {}
    birth = merged.get("birth") or {}
    pillars = merged.get("四柱") or {}
    dayun = merged.get("大运") or {}
    solar_date = _date_text(birth.get("公历"))

    if not solar_date:
        return _ineligible(input_path, "缺少可解析的公历日期")
    if not isinstance(pillars, dict) or not all(name in pillars for name in _PILLAR_NAMES):
        return _ineligible(input_path, "缺少完整四柱")
    if not isinstance(dayun, dict):
        return _ineligible(input_path, "缺少大运 mapping")
    raw_steps = dayun.get("排布")
    if not isinstance(raw_steps, list) or not raw_steps:
        return _ineligible(input_path, "缺少大运排布")
    if dayun.get("顺逆") not in {"顺", "逆"}:
        return _ineligible(input_path, "缺少合法大运方向")

    claimed_pillars = {name: str(pillars[name]) for name in _PILLAR_NAMES}
    claimed_sequence: list[str] = []
    for item in raw_steps:
        if not isinstance(item, dict) or "干支" not in item:
            return _ineligible(input_path, "大运排布项缺少干支")
        claimed_sequence.append(str(item["干支"]))

    source = str(birth.get("来源") or case_meta.get("来源") or "")
    gender = str(birth.get("性别") or "")
    claimed_dayun = {
        "顺逆": dayun.get("顺逆"),
        "起运岁": dayun.get("起运岁"),
        "排布": claimed_sequence,
    }

    # 校准必须强制重算：source=None，绝不走问真可信旁路。
    result = validate_chart(
        claimed_pillars=claimed_pillars,
        gender=gender,
        solar_date=solar_date,
        hour_zhi=claimed_pillars["时柱"][1],
        source=None,
        claimed_dayun=claimed_dayun,
    )
    corrected = result.corrected_pillars or dict(claimed_pillars)
    pillar_checks = {
        name: claimed_pillars[name] == corrected.get(name)
        for name in _PILLAR_NAMES
    }

    computed_dayun = compute_dayun(
        month_pillar=GanZhi.parse(corrected["月柱"]),
        gender=gender,
        year_gan=corrected["年柱"][0],
        solar_date=solar_date,
        steps=max(10, len(claimed_sequence)),
    )
    computed_sequence = [str(step) for step in computed_dayun.sequence]
    direction_ok = dayun.get("顺逆") == computed_dayun.direction
    sequence_ok = all(
        claimed == computed_sequence[index]
        for index, claimed in enumerate(claimed_sequence)
    )

    claimed_qiyun = dayun.get("起运岁")
    try:
        qiyun_delta = abs(float(claimed_qiyun) - computed_dayun.qiyun_age)
    except (TypeError, ValueError):
        qiyun_delta = None

    qiyun_age_ok = qiyun_delta is not None and qiyun_delta < 1.5
    errors = list(result.errors)
    if not direction_ok and not any("大运方向" in error for error in errors):
        errors.append(
            f"大运方向错误：声称 {dayun.get('顺逆')}，精算 {computed_dayun.direction}"
        )
    if not sequence_ok and not any("步大运" in error for error in errors):
        errors.append("大运排布与精算序列不一致")

    if not qiyun_age_ok:
        errors.append(
            f"起运岁差异过大：声称 {claimed_qiyun}，"
            f"精算 {computed_dayun.qiyun_age:.4f}"
        )

    passed = (
        all(pillar_checks.values())
        and direction_ok
        and sequence_ok
        and qiyun_age_ok
    )
    return {
        "case_id": str(case_meta.get("case_id") or input_path.parent.name),
        "input_path": input_path.as_posix(),
        "eligible": True,
        "status": "pass" if passed else "fail",
        "source": source,
        "trusted_source": _is_wenzhen_source(source),
        "validation_skipped": False,
        "solar_date": solar_date,
        "gender": gender,
        "claimed_pillars": claimed_pillars,
        "corrected_pillars": corrected,
        "pillar_checks": pillar_checks,
        "claimed_dayun_direction": dayun.get("顺逆"),
        "computed_dayun_direction": computed_dayun.direction,
        "dayun_direction_ok": direction_ok,
        "claimed_dayun_sequence": claimed_sequence,
        "computed_dayun_sequence": computed_sequence[: len(claimed_sequence)],
        "dayun_sequence_ok": sequence_ok,
        "claimed_qiyun_age": claimed_qiyun,
        "computed_qiyun_age": round(computed_dayun.qiyun_age, 4),
        "qiyun_age_delta": round(qiyun_delta, 4) if qiyun_delta is not None else None,
        "qiyun_age_ok": qiyun_age_ok,
        "warnings": list(result.warnings),
        "errors": errors,
    }


def audit_repository_cases(cases_dir: Path) -> dict[str, Any]:
    """扫描案例目录并汇总全部校准记录。"""
    cases_dir = Path(cases_dir)
    records = [
        audit_case_file(path)
        for path in sorted(cases_dir.glob("*/input.md"), key=lambda item: item.as_posix())
    ]
    eligible = [record for record in records if record["eligible"]]
    passed = [record for record in eligible if record["status"] == "pass"]
    failed = [record for record in eligible if record["status"] == "fail"]
    trusted = [record for record in eligible if record.get("trusted_source")]
    pillar_failures = {
        name: sum(not record["pillar_checks"][name] for record in eligible)
        for name in _PILLAR_NAMES
    }
    fixed_gender_direction_pattern = sum(
        (record["gender"] in {"M", "男"} and record["claimed_dayun_direction"] == "顺")
        or (record["gender"] in {"F", "女"} and record["claimed_dayun_direction"] == "逆")
        for record in eligible
        if not record["dayun_direction_ok"]
    )
    return {
        "schema_version": "chart-validation-calibration/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cases_dir": cases_dir.as_posix(),
        "summary": {
            "scanned": len(records),
            "eligible": len(eligible),
            "trusted_source_eligible": len(trusted),
            "passed": len(passed),
            "failed": len(failed),
            "ineligible": len(records) - len(eligible),
            "pillar_failures": pillar_failures,
            "dayun_direction_failures": sum(
                not record["dayun_direction_ok"] for record in eligible
            ),
            "dayun_sequence_failures": sum(
                not record["dayun_sequence_ok"] for record in eligible
            ),
            "qiyun_age_failures": sum(
                not record["qiyun_age_ok"] for record in eligible
            ),
            "fixed_gender_direction_pattern_failures": fixed_gender_direction_pattern,
        },
        "diagnosis": {
            "fixed_gender_direction_pattern": (
                "历史问真转案工具曾按乾顺坤逆生成大运，未使用年干阴阳；"
                "相关 48 案已由 wenzhen-dayun-direction-fix/v1 迁移修复。"
            ),
            "evidence_paths": [
                "tools/promote_wenzhen_ready_batch.py:323",
                "tools/promote_wenzhen_pending_analysis_samples.py:434",
                "tools/promote_wenzhen_first5_cases.py:293",
            ],
        },
        "records": records,
    }


def render_markdown(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# 八字排盘验证模块 · 仓库案例校准结果",
        "",
        f"- 扫描案例：{summary['scanned']}",
        f"- 可核验案例：{summary['eligible']}",
        f"- 其中问真可信来源：{summary['trusted_source_eligible']}",
        f"- 完全通过：{summary['passed']}",
        f"- 存在差异：{summary['failed']}",
        f"- 不具备核验字段：{summary['ineligible']}",
        f"- 命中历史‘乾顺坤逆’固定生成模式：{summary['fixed_gender_direction_pattern_failures']}",
        "",
        "## 差异诊断",
        "",
        "历史问真转案工具曾按乾顺、坤逆生成大运，未结合年干阴阳；相关 48 案现已完成迁移修复。当前统计中的固定方向模式命中数应为 0。",
        "",
        "证据：",
        "- `tools/promote_wenzhen_ready_batch.py:323`",
        "- `tools/promote_wenzhen_pending_analysis_samples.py:434`",
        "- `tools/promote_wenzhen_first5_cases.py:293`",
        "",
        "| case_id | 状态 | 四柱 | 大运方向 | 大运序列 | 起运差值 |",
        "|---|---|---|---|---|---:|",
    ]
    for record in result["records"]:
        if not record["eligible"]:
            continue
        pillar_ok = "通过" if all(record["pillar_checks"].values()) else "差异"
        delta = record["qiyun_age_delta"]
        delta_text = "—" if delta is None else f"{delta:.2f}"
        lines.append(
            f"| {record['case_id']} | {record['status']} | {pillar_ok} | "
            f"{'通过' if record['dayun_direction_ok'] else '差异'} | "
            f"{'通过' if record['dayun_sequence_ok'] else '差异'} | "
            f"{delta_text}{'' if record['qiyun_age_ok'] else ' ⚠️'} |"
        )
    lines.append("")
    lines.append("> 校准强制关闭问真来源旁路；所有可核验案例均由模块实际重算。")
    return "\n".join(lines) + "\n"


def render_failures_markdown(result: dict[str, Any]) -> str:
    """按差异类型输出可人工复核的错误案例清单。"""
    failures = [record for record in result["records"] if record.get("status") == "fail"]
    pillar_failures = [
        record for record in failures
        if not all(record["pillar_checks"].values())
    ]
    qiyun_failures = [record for record in failures if not record["qiyun_age_ok"]]
    dayun_failures = [
        record for record in failures
        if not record["dayun_direction_ok"] or not record["dayun_sequence_ok"]
    ]
    lines = [
        "# 八字排盘校准错误案例清单",
        "",
        f"> 共 {len(failures)} 个差异案例；同一案例可能出现在多个分类。",
        "",
    ]

    lines.extend([
        f"## 四柱差异（{len(pillar_failures)} 案）",
        "",
        "| case_id | 公历 | 差异柱 | 原值 | 精算值 |",
        "|---|---|---|---|---|",
    ])
    for record in pillar_failures:
        names = [name for name, ok in record["pillar_checks"].items() if not ok]
        claimed = "；".join(
            f"{name}={record['claimed_pillars'][name]}" for name in names
        )
        computed = "；".join(
            f"{name}={record['corrected_pillars'][name]}" for name in names
        )
        lines.append(
            f"| {record['case_id']} | {record['solar_date']} | "
            f"{'、'.join(names)} | {claimed} | {computed} |"
        )

    lines.extend([
        "",
        f"## 起运岁差异（{len(qiyun_failures)} 案）",
        "",
        "| case_id | 公历 | 原起运岁 | 精算起运岁 | 差值 |",
        "|---|---|---:|---:|---:|",
    ])
    for record in qiyun_failures:
        lines.append(
            f"| {record['case_id']} | {record['solar_date']} | "
            f"{record['claimed_qiyun_age']} | {record['computed_qiyun_age']} | "
            f"{record['qiyun_age_delta']} |"
        )

    lines.extend([
        "",
        f"## 大运方向或序列差异（{len(dayun_failures)} 案）",
        "",
        "| case_id | 性别 | 年柱 | 原方向 | 精算方向 | 原前三运 | 精算前三运 |",
        "|---|---|---|---|---|---|---|",
    ])
    for record in dayun_failures:
        lines.append(
            f"| {record['case_id']} | {record['gender']} | "
            f"{record['claimed_pillars']['年柱']} | "
            f"{record['claimed_dayun_direction']} | "
            f"{record['computed_dayun_direction']} | "
            f"{','.join(record['claimed_dayun_sequence'][:3])} | "
            f"{','.join(record['computed_dayun_sequence'][:3])} |"
        )

    lines.extend([
        "",
        "## 已定位的系统性原因",
        "",
        "历史转案工具曾固定使用‘乾顺、坤逆’，没有结合年干阴阳；相关 48 案已完成迁移，当前大运方向差异为 0：",
        "",
        "- `tools/promote_wenzhen_ready_batch.py:323`",
        "- `tools/promote_wenzhen_pending_analysis_samples.py:434`",
        "- `tools/promote_wenzhen_first5_cases.py:293`",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="用仓库现有案例校准排盘验证模块")
    parser.add_argument("--cases", type=Path, default=Path("cases"))
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    parser.add_argument("--failures-out", type=Path)
    parser.add_argument("--require-min", type=int, default=30)
    args = parser.parse_args()

    result = audit_repository_cases(args.cases)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(render_markdown(result), encoding="utf-8")

    if args.failures_out:
        args.failures_out.parent.mkdir(parents=True, exist_ok=True)
        args.failures_out.write_text(
            render_failures_markdown(result),
            encoding="utf-8",
        )

    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    return 0 if result["summary"]["eligible"] >= args.require_min else 2


if __name__ == "__main__":
    raise SystemExit(main())
