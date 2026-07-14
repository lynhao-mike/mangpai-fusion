"""Batch helpers for prospective school-capability case intake.

This module treats a case summary file as prediction-time input only. It keeps
chart facts and strips source/feedback/report references so later labels must be
provided in a separate reveal step.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence
import re

from engine.claims.orchestrator import generate_blind_outputs
from engine.evaluation.capability import build_capability_posteriors
from engine.evaluation.freeze import freeze_outputs, verify_frozen_run
from engine.evaluation.models import BlindTask, FrozenBlindRun, RevealedLabel
from engine.evaluation.scoring import score_output


_STEMS = "甲乙丙丁戊己庚辛壬癸"
_BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
_PILLAR_RE = f"[{_STEMS}][{_BRANCHES}]"


@dataclass(frozen=True)
class ProspectiveCase:
    case_id: str
    sex_marker: str
    four_pillars: tuple[str, str, str, str]
    solar_datetime: str
    dayun_sequence: tuple[str, ...]
    isolated_input: str


@dataclass(frozen=True)
class BatchParseResult:
    cases: tuple[ProspectiveCase, ...]
    duplicates: list[dict[str, str]]


def _section_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("## P-") and current:
            blocks.append("\n".join(current).strip())
            current = [line]
        elif line.strip() == "---" and current:
            blocks.append("\n".join(current).strip())
            current = []
        elif line.startswith("## P-") or current:
            current.append(line)
    if current:
        blocks.append("\n".join(current).strip())
    return [block for block in blocks if block.startswith("## P-")]


def _extract_one(pattern: str, text: str, name: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        raise ValueError(f"missing {name}")
    return match.group(1).strip()


def _parse_dayun_sequence(block: str) -> tuple[str, ...]:
    line_match = re.search(r"^- 大运[：:]\s*(.+)$", block, re.MULTILINE)
    if not line_match:
        return ()
    tail = line_match.group(1)
    raw = re.split(r"[；;]", tail)[-1]
    return tuple(re.findall(_PILLAR_RE, raw))


def _isolated_input(case_id: str, sex_marker: str, pillars: tuple[str, str, str, str], solar: str, dayun: tuple[str, ...]) -> str:
    lines = [
        f"# {case_id}",
        f"性别：{sex_marker}",
        f"四柱：{' '.join(pillars)}",
        f"公历生日：{solar}",
    ]
    if dayun:
        lines.append("大运：" + " → ".join(dayun))
    return "\n".join(lines) + "\n"


def _parse_case_blocks(path: Path) -> list[ProspectiveCase]:
    text = Path(path).read_text(encoding="utf-8")
    cases: list[ProspectiveCase] = []
    for block in _section_blocks(text):
        header_match = re.search(
            r"^##\s+(P-\d{4}-\d{3})\s+·\s+([乾坤])\s+·\s+((?:" + _PILLAR_RE + r"){4})",
            block,
            re.MULTILINE,
        )
        if header_match is None:
            raise ValueError("invalid case header")
        base_id, sex_marker, compact_pillars = header_match.groups()
        pillar_line = _extract_one(r"^- 四柱[：:]\s*((?:" + _PILLAR_RE + r"\s*){4})", block, "four pillars")
        pillars = tuple(re.findall(_PILLAR_RE, pillar_line))
        if len(pillars) != 4 or "".join(pillars) != compact_pillars:
            raise ValueError(f"pillar mismatch: {base_id}")
        solar = _extract_one(r"^- 公历生日[：:]\s*([^\r\n（(]+)", block, "solar birthday")
        dayun = _parse_dayun_sequence(block)
        case_id = f"{base_id}-{sex_marker}-{''.join(pillars)}"
        cases.append(ProspectiveCase(
            case_id=case_id,
            sex_marker=sex_marker,
            four_pillars=pillars,  # type: ignore[arg-type]
            solar_datetime=solar,
            dayun_sequence=dayun,
            isolated_input=_isolated_input(case_id, sex_marker, pillars, solar, dayun),  # type: ignore[arg-type]
        ))
    return cases


def _completeness(case: ProspectiveCase) -> tuple[int, int]:
    solar_known = int(not case.solar_datetime.startswith(("来源未", "约")))
    return solar_known, len(case.dayun_sequence)


def parse_case_summary_with_audit(path: Path) -> BatchParseResult:
    selected: dict[tuple[str, tuple[str, str, str, str]], ProspectiveCase] = {}
    duplicates: list[dict[str, str]] = []
    for case in _parse_case_blocks(path):
        subject = case.sex_marker, case.four_pillars
        previous = selected.get(subject)
        if previous is None:
            selected[subject] = case
            continue
        kept, discarded = (
            (case, previous)
            if _completeness(case) > _completeness(previous)
            else (previous, case)
        )
        selected[subject] = kept
        duplicates.append({
            "discarded_case_id": discarded.case_id,
            "kept_case_id": kept.case_id,
            "reason": "duplicate_subject_less_complete",
        })
    cases = tuple(sorted(selected.values(), key=lambda item: item.case_id))
    return BatchParseResult(cases=cases, duplicates=duplicates)


def parse_case_summary(path: Path) -> list[ProspectiveCase]:
    cases = _parse_case_blocks(path)
    seen_subjects: set[tuple[str, tuple[str, str, str, str]]] = set()
    for case in cases:
        subject = case.sex_marker, case.four_pillars
        if subject in seen_subjects:
            raise ValueError(f"duplicate subject: {case.case_id.split('-乾-')[0].split('-坤-')[0]}")
        seen_subjects.add(subject)
    return cases


def _chart_mapping(case: ProspectiveCase) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "sex_marker": case.sex_marker,
        "solar_datetime": case.solar_datetime,
        "four_pillars": list(case.four_pillars),
        "dayun_steps": [{"ganzhi": ganzhi} for ganzhi in case.dayun_sequence],
        "liunian_steps": [],
    }


def build_historical_blind_artifacts(
    source: Path,
    tasks: Sequence[BlindTask],
    *,
    schools: Sequence[str],
    task_catalog_version: str,
    rule_snapshot_id: str,
    frozen_at: str,
) -> dict[str, Any]:
    """Build a label-isolated historical blind batch from chart facts only."""
    audit = parse_case_summary_with_audit(source)
    outputs = [
        output
        for case in audit.cases
        for output in generate_blind_outputs(
            _chart_mapping(case),
            tasks,
            case_id=case.case_id,
            schools=schools,
        )
    ]
    frozen = freeze_outputs(
        outputs,
        task_catalog_version,
        rule_snapshot_id,
        frozen_at=frozen_at,
    )
    return {
        "schema_version": "school-capability-historical-batch/v1",
        "classification": "historical_blind_candidate",
        "cases": [
            {
                "case_id": case.case_id,
                "sex_marker": case.sex_marker,
                "four_pillars": list(case.four_pillars),
                "solar_datetime": case.solar_datetime,
                "dayun_sequence": list(case.dayun_sequence),
            }
            for case in audit.cases
        ],
        "duplicate_audit": audit.duplicates,
        "frozen_run": frozen.to_dict(),
    }


_EDUCATION_LABELS = (
    ("博士", "postgraduate"),
    ("硕士", "postgraduate"),
    ("研究生", "postgraduate"),
    ("本科", "tertiary"),
    ("大学毕业", "tertiary"),
    ("大专", "tertiary"),
    ("二本", "tertiary"),
    ("专科", "tertiary"),
    ("高中", "secondary"),
    ("初中", "secondary"),
    ("小学", "basic"),
)
_CAREER_CHANGE = ("入职", "离职", "辞职", "失业", "跳槽", "转岗", "调动", "升职", "裁员", "创业", "参加工作", "开始做工", "考上公务员", "考上事业单位")
_MARRIAGE_CHANGE = ("结婚", "离婚", "复婚", "再婚", "分居", "同居", "分手", "恋爱", "婚变")
_EMPLOYMENT = ("上班", "打工", "国企", "公职", "公务员", "事业单位", "行政机关", "职员", "参加工作")
_ENTREPRENEURSHIP = ("创业", "经商", "做生意", "自营", "合伙")


def _feedback_sections(text: str) -> list[tuple[str, int, list[str]]]:
    lines = text.splitlines()
    starts = [index for index, line in enumerate(lines) if re.match(r"^## P-\d{4}-\d{3}\b", line)]
    sections: list[tuple[str, int, list[str]]] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        base_id = re.match(r"^## (P-\d{4}-\d{3})\b", lines[start]).group(1)  # type: ignore[union-attr]
        sections.append((base_id, start + 1, lines[start:end]))
    return sections


def _label_record(
    case_id: str,
    task_id: str,
    label: object,
    line_number: int,
    confidence: str,
    reviewer: str,
) -> dict[str, Any]:
    observed_at = "2026-07-14"
    if isinstance(label, dict) and type(label.get("year")) is int:
        observed_at = f"{label['year']}-01-01"
    return {
        "case_id": case_id,
        "task_id": task_id,
        "label": label,
        "source": f"cases/fankui-feedback.md:{line_number}",
        "observed_at": observed_at,
        "confidence_grade": confidence,
        "quantifiable": True,
        "conflict_state": "none",
        "reviewer": reviewer,
    }


def _first_exact_year_event(lines: list[str], keywords: tuple[str, ...], start_line: int) -> tuple[int, int] | None:
    for offset, line in enumerate(lines):
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2 or re.fullmatch(r"\d{4}", cells[0]) is None:
            continue
        event_text = " ".join(cells[1:])
        if "可能" in event_text or "待核" in event_text:
            continue
        if any(keyword in event_text for keyword in keywords):
            return int(cells[0]), start_line + offset
    return None


def parse_feedback_labels(
    path: Path,
    eligible_case_ids: set[str],
    *,
    reviewer: str,
) -> list[dict[str, Any]]:
    """Extract conservative, non-high-risk labels after prediction freeze."""
    if not reviewer or reviewer.lower().startswith(("automated", "agent", "ai-")):
        raise ValueError("reviewer must identify a human reviewer")
    by_base = {case_id[:10]: case_id for case_id in eligible_case_ids}
    text = Path(path).read_text(encoding="utf-8")
    labels: list[dict[str, Any]] = []
    for base_id, start_line, lines in _feedback_sections(text):
        case_id = by_base.get(base_id)
        if case_id is None:
            continue
        section = "\n".join(lines)
        confidence = "C" if "二级来源" in section else "B"
        seen_tasks: set[str] = set()

        for token, value in _EDUCATION_LABELS:
            match = next((index for index, line in enumerate(lines) if token in line and ("学历" in line or "大学" in line or "大专" in line or "研究生" in line)), None)
            if match is not None:
                labels.append(_label_record(case_id, "education.attainment_band", value, start_line + match, confidence, reviewer))
                seen_tasks.add("education.attainment_band")
                break

        has_employment = any(token in section for token in _EMPLOYMENT)
        has_entrepreneurship = any(token in section for token in _ENTREPRENEURSHIP)
        if has_employment or has_entrepreneurship:
            value = "mixed" if has_employment and has_entrepreneurship else "entrepreneurship" if has_entrepreneurship else "employment"
            line_index = next(index for index, line in enumerate(lines) if any(token in line for token in (*_EMPLOYMENT, *_ENTREPRENEURSHIP)))
            labels.append(_label_record(case_id, "career.path_type", value, start_line + line_index, confidence, reviewer))
            seen_tasks.add("career.path_type")

        career = _first_exact_year_event(lines, _CAREER_CHANGE, start_line)
        if career is not None:
            year, line_number = career
            labels.append(_label_record(case_id, "career.change_window", {"occurred": True, "year": year}, line_number, confidence, reviewer))
            labels.append(_label_record(case_id, "career.role_change", "occurred", line_number, confidence, reviewer))
            seen_tasks.update(("career.change_window", "career.role_change"))

        marriage = _first_exact_year_event(lines, _MARRIAGE_CHANGE, start_line)
        if marriage is not None:
            year, line_number = marriage
            labels.append(_label_record(case_id, "marriage.event_window", {"occurred": True, "year": year}, line_number, confidence, reviewer))
            seen_tasks.add("marriage.event_window")

        late_line = next((index for index, line in enumerate(lines) if "晚婚" in line and "不" not in line), None)
        if late_line is not None:
            labels.append(_label_record(case_id, "marriage.late_marriage", "occurred", start_line + late_line, confidence, reviewer))
            seen_tasks.add("marriage.late_marriage")

    identities = [(item["case_id"], item["task_id"]) for item in labels]
    if len(identities) != len(set(identities)):
        raise ValueError("feedback extraction produced duplicate label identity")
    return sorted(labels, key=lambda item: (item["case_id"], item["task_id"]))


def score_historical_batch(
    artifact: dict[str, Any],
    tasks: Sequence[BlindTask],
    *,
    labels: list[dict[str, Any]],
    reviewer: str,
    evaluated_at: str,
) -> dict[str, Any]:
    """Score an already-frozen historical batch without changing its identity."""
    if artifact.get("classification") != "historical_blind_candidate":
        raise ValueError("artifact must be a historical blind candidate batch")
    run = FrozenBlindRun.from_dict(artifact["frozen_run"])
    verify_frozen_run(run)
    task_map = {task.task_id: task for task in tasks}
    if len(task_map) != len(tasks):
        raise ValueError("duplicate task_id")
    label_objects = [RevealedLabel.from_dict(item) for item in labels]
    label_map = {(item.case_id, item.task_id): item for item in label_objects}
    if len(label_map) != len(label_objects):
        raise ValueError("duplicate label identity")

    cases = {item["case_id"]: item for item in artifact["cases"]}
    score_objects = []
    for output in run.outputs:
        task = task_map.get(output.task_id)
        if task is None:
            raise ValueError(f"unknown task: {output.task_id}")
        score = score_output(output, task, label_map.get((output.case_id, output.task_id)))
        evidence_band = "complete" if cases[output.case_id]["dayun_sequence"] and not str(cases[output.case_id]["solar_datetime"]).startswith(("来源未", "约")) else "partial"
        score_objects.append(score.__class__(
            **{
                **score.to_dict(),
                "chart_prototype_id": "prototype-provisional",
                "time_horizon": task.allowed_time_horizons[0],
                "evidence_completeness_band": evidence_band,
            }
        ))

    probability_scores = [
        score for score in score_objects
        if task_map[score.task_id].scoring_method == "binary_probability"
    ]
    probability_map: dict[tuple[str, str, str], float] = {}
    eligible: dict[tuple[str, str, str, str, str, str], set[str]] = {}
    for score in probability_scores:
        identity = (
            score.school_id, score.task_id, score.chart_prototype_id,
            score.claim_type, score.time_horizon, score.evidence_completeness_band,
        )
        eligible.setdefault(identity, set()).add(score.case_id)
        output = next(
            item for item in run.outputs
            if (item.case_id, item.task_id, item.school_id) == (score.case_id, score.task_id, score.school_id)
        )
        if output.state == "claim" and output.predictions:
            probability_map[(score.case_id, score.task_id, score.school_id)] = output.predictions[0].probability

    posteriors = build_capability_posteriors(
        probability_scores,
        "B",
        evaluated_at,
        claim_probabilities=probability_map,
        eligible_case_ids=eligible,
    ) if probability_scores else []
    hold_reasons: list[str] = []
    if not probability_map:
        hold_reasons.append("no probability claims")
    if len({item["case_id"] for item in labels}) < 30:
        hold_reasons.append("fewer than 30 labelled cases")
    return {
        "schema_version": "school-capability-historical-scores/v1",
        "freeze_hash": run.freeze_hash,
        "reviewed_by": reviewer,
        "evaluated_at": evaluated_at,
        "scored_output_count": len(score_objects),
        "label_count": len(labels),
        "labelled_case_count": len({item["case_id"] for item in labels}),
        "scores": [score.to_dict() for score in score_objects],
        "posteriors": [posterior.to_dict() for posterior in posteriors],
        "status": "HOLD" if hold_reasons else "GO",
        "hold_reasons": hold_reasons,
    }


def build_historical_reviewed_manifest(
    artifact: dict[str, Any],
    tasks: Sequence[BlindTask],
    *,
    labels: list[dict[str, Any]],
    reviewer: str,
    generated_at: str,
) -> dict[str, Any]:
    task_map = {task.task_id: task for task in tasks}
    labelled_cases = {item["case_id"] for item in labels}
    outputs_by_case: dict[str, list[dict[str, Any]]] = {item["case_id"]: [] for item in artifact["cases"]}
    for output in artifact["frozen_run"]["outputs"]:
        outputs_by_case[output["case_id"]].append(output)
    records = []
    for case in artifact["cases"]:
        case_id = case["case_id"]
        eligible = case_id in labelled_cases
        routes = []
        if eligible:
            for output in outputs_by_case[case_id]:
                task = task_map[output["task_id"]]
                routes.append({
                    "school_id": output["school_id"],
                    "task_id": output["task_id"],
                    "chart_prototype_id": "prototype-provisional",
                    "claim_type": task.claim_type,
                    "time_horizon": task.allowed_time_horizons[0],
                    "evidence_completeness_band": "complete" if case["dayun_sequence"] and not str(case["solar_datetime"]).startswith(("来源未", "约")) else "partial",
                })
        records.append({
            "case_id": case_id,
            "has_input": True,
            "has_feedback": eligible,
            "has_statement_index": False,
            "has_existing_report": False,
            "feedback_quantifiable": eligible,
            "contamination_flags": [],
            "eligibility": "historical_blind_candidate" if eligible else "development_only",
            "evidence_notes": ["feedback revealed after current-run freeze"] if eligible else ["no conservative task label extracted"],
            "eligible_routes": routes,
        })
    return {
        "schema_version": "school-capability-case-manifest/v1",
        "generated_at": generated_at,
        "reviewed_by": reviewer,
        "expected_schools": sorted({output["school_id"] for output in artifact["frozen_run"]["outputs"]}),
        "records": records,
    }


def render_historical_baseline(manifest: dict[str, Any], scores: dict[str, Any]) -> str:
    eligible_count = sum(row["eligibility"] == "historical_blind_candidate" for row in manifest["records"])
    development_count = sum(row["eligibility"] == "development_only" for row in manifest["records"])
    state_counts = {name: sum(row["state"] == name for row in scores["scores"]) for name in ("claim", "abstain", "unsupported")}
    n_eff_values = [float(row.get("n_eff", 0.0)) for row in scores["posteriors"]]
    max_n_eff = max(n_eff_values, default=0.0)
    return "\n".join([
        "# 学派能力历史隔离基线（2026-07-14）",
        "",
        "## 判定",
        f"**{scores['status']}**",
        "",
        "## 数据与冻结",
        f"- 冻结案例：{len(manifest['records'])}",
        f"- 可评分历史隔离案例：{eligible_count}",
        f"- 未抽取到保守标签案例：{development_count}",
        f"- 结构化标签：{scores['label_count']}",
        f"- 冻结输出：{scores['scored_output_count']}",
        "- 冻结完整性：已验证",
        "",
        "## 三态能力覆盖",
        f"- 产生命题：{state_counts['claim']}",
        f"- 克制不判：{state_counts['abstain']}",
        f"- 当前不支持：{state_counts['unsupported']}",
        "",
        "## 六维能力后验",
        f"- 条件切片：{len(scores['posteriors'])}",
        f"- 最大有效样本量：{max_n_eff:.1f}",
        "- 当前没有可概率评分命题；数组非空仅代表覆盖切片存在，不代表形成能力证据。",
        "",
        "## HOLD 原因",
        *[f"- {reason}" for reason in scores["hold_reasons"]],
        "",
        "## 失败分类",
        "- 任务覆盖缺失：多数流派与任务组合当前不支持。",
        "- 输入证据不足：事件时间任务缺逐年流年事实，正确克制不判。",
        "- 概率能力为空：无二元概率命题可形成有效样本量。",
        "- 数据属性限制：本批为历史隔离盲测，不是前瞻新案。",
        "",
        "## 结论",
        "本批满足真实反馈标签数量与冻结隔离要求，但不满足非空概率能力后验门槛。不得用于生产调权或宣称系统已具备稳定预测能力。",
        "",
    ])
