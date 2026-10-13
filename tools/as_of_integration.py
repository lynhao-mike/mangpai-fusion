"""G8 as-of 生产报告薄编排入口。

依赖仅由本模块单向指向既有生产 pipeline、标准报告渲染器与隔离的
``engine.asof`` 原型；不改变任何默认生产入口。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Sequence

from engine.application.pipeline_runner import run_pipeline_e2e
from engine.asof.event_candidate import (
    AnnualInteractionTrace,
    CompletionMode,
    ExtensionBoundary,
    LifeEventCandidate,
    RootLevel,
    VerificationStatus,
)
from engine.asof.natal_capacity import EvidenceRef, SourceCitation
from engine.asof.state_ledger import (
    AsOfRequest,
    EventImpactAssessment,
    EventLedgerEntry,
    ImpactLevel,
    ImpactScope,
    Persistence,
    VerifiedState,
    build_verified_state,
)
from tools.render_report import render_from_output


ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_HEADING = "## 截止状态快照"


def parse_iso_date(value: str) -> date:
    """解析规范 ``YYYY-MM-DD``；不接受宽松格式或隐式当前日期。"""
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"日期必须为规范 YYYY-MM-DD: {value!r}") from exc
    if value != parsed.isoformat():
        raise ValueError(f"日期必须为规范 YYYY-MM-DD: {value!r}")
    return parsed


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} 必须是 JSON object")
    return value


def _array(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{name} 必须是 JSON array")
    return value


def _evidence(payload: Any) -> EvidenceRef:
    data = _mapping(payload, "evidence")
    return EvidenceRef(
        source=data["source"],
        locator=data["locator"],
        excerpt=data["excerpt"],
    )


def _evidence_tuple(payload: Any, name: str) -> tuple[EvidenceRef, ...]:
    return tuple(_evidence(item) for item in _array(payload, name))


def _citation(payload: Any) -> SourceCitation:
    data = _mapping(payload, "citation")
    return SourceCitation(
        source_path=data["source_path"],
        line=data["line"],
        excerpt=data["excerpt"],
    )


def _strings(payload: Any, name: str) -> tuple[str, ...]:
    values = _array(payload, name)
    if any(not isinstance(item, str) for item in values):
        raise ValueError(f"{name} 只能包含字符串")
    return tuple(values)


def _candidate(payload: Any) -> LifeEventCandidate:
    data = _mapping(payload, "candidate")
    trace_data = _mapping(data["annual_trace"], "annual_trace")
    trace = AnnualInteractionTrace(
        year=trace_data["year"],
        liunian=trace_data["liunian"],
        dayun_ganzhi=trace_data["dayun_ganzhi"],
        relations=_evidence_tuple(trace_data["relations"], "relations"),
        activated_node_ids=_strings(trace_data["activated_node_ids"], "activated_node_ids"),
        domains=_strings(trace_data["domains"], "domains"),
        supporting_evidence=_evidence_tuple(
            trace_data["supporting_evidence"], "annual supporting_evidence"
        ),
        counter_evidence=_evidence_tuple(trace_data["counter_evidence"], "annual counter_evidence"),
        trigger_strength=trace_data["trigger_strength"],
        crossed_candidate_gate=trace_data["crossed_candidate_gate"],
    )
    return LifeEventCandidate(
        candidate_id=data["candidate_id"],
        domain=data["domain"],
        event_type=data["event_type"],
        window_start=parse_iso_date(data["window_start"]),
        window_end=parse_iso_date(data["window_end"]),
        natal_evidence=_evidence_tuple(data["natal_evidence"], "natal_evidence"),
        daiyun_evidence=_evidence_tuple(data["daiyun_evidence"], "daiyun_evidence"),
        annual_trace=trace,
        root_level=RootLevel(data["root_level"]),
        root_evidence=_evidence_tuple(data["root_evidence"], "root_evidence"),
        source_citations=tuple(
            _citation(item) for item in _array(data["source_citations"], "source_citations")
        ),
        completion_mode=CompletionMode(data["completion_mode"]),
        supporting_evidence=_evidence_tuple(data["supporting_evidence"], "supporting_evidence"),
        counter_evidence=_evidence_tuple(data["counter_evidence"], "counter_evidence"),
        alternative_hypotheses=_strings(data["alternative_hypotheses"], "alternative_hypotheses"),
        frozen_version=data["frozen_version"],
        verification_status=VerificationStatus(data["verification_status"]),
        extension_boundary=ExtensionBoundary(data["extension_boundary"]),
        is_primary_event=data["is_primary_event"],
    )


def _optional_enum(enum_type, value: Any):
    return None if value is None else enum_type(value)


def _optional_date(value: Any) -> date | None:
    return None if value is None else parse_iso_date(value)


def _assessment(payload: Any) -> EventImpactAssessment:
    data = _mapping(payload, "assessment")
    return EventImpactAssessment(
        event_id=data["event_id"],
        event_date=parse_iso_date(data["event_date"]),
        event_type=data["event_type"],
        root_level=RootLevel(data["root_level"]),
        completion_mode=CompletionMode(data["completion_mode"]),
        system_suggested_impact=ImpactLevel(data["system_suggested_impact"]),
        system_suggested_persistence=Persistence(data["system_suggested_persistence"]),
        system_suggested_scope=ImpactScope(data["system_suggested_scope"]),
        practitioner_final_impact=_optional_enum(ImpactLevel, data.get("practitioner_final_impact")),
        practitioner_final_persistence=_optional_enum(
            Persistence, data.get("practitioner_final_persistence")
        ),
        practitioner_final_scope=_optional_enum(ImpactScope, data.get("practitioner_final_scope")),
        adjustment_reason=data.get("adjustment_reason"),
        short_term_until=_optional_date(data.get("short_term_until")),
        state_value=data.get("state_value", ""),
        opened_path_ids=_strings(data.get("opened_path_ids", []), "opened_path_ids"),
        closed_path_ids=_strings(data.get("closed_path_ids", []), "closed_path_ids"),
    )


def load_ledger(path: str | Path) -> dict[str, Any]:
    """从显式 JSON 构造经过原型数据类校验的事件账本。"""
    payload = _mapping(json.loads(Path(path).read_text(encoding="utf-8")), "ledger")
    case_id = payload["case_id"]
    current_center = payload["current_center"]
    if not isinstance(case_id, str) or not case_id.strip():
        raise ValueError("ledger case_id 必须是非空字符串")
    if not isinstance(current_center, str) or not current_center.strip():
        raise ValueError("current_center 必须是非空字符串")
    entries = tuple(
        EventLedgerEntry(_candidate(item["candidate"]), _assessment(item["assessment"]))
        for item in _array(payload["entries"], "entries")
        if isinstance(item, dict)
    )
    if len(entries) != len(payload["entries"]):
        raise ValueError("每个 ledger entry 必须是 JSON object")
    return {
        "case_id": case_id,
        "daiyun_end": parse_iso_date(payload["daiyun_end"]),
        "current_center": current_center,
        "reasonable_range": _strings(payload.get("reasonable_range", []), "reasonable_range"),
        "entries": entries,
    }


def _display(values: Sequence[str]) -> str:
    return "、".join(values) if values else "无"


def append_snapshot_section(base: str, state: VerifiedState) -> str:
    """只在报告末尾追加一次事实快照；已有章节时原样返回。"""
    if SNAPSHOT_HEADING in base:
        return base
    active_states = tuple(
        f"{item.value}（来源：{item.source_event_id}）" for item in state.reality_track.active_states
    )
    path_states = tuple(
        f"{item.path_id}={item.status}（来源：{item.source_event_id}）"
        for item in state.reality_track.path_states
    )
    section = "\n".join(
        (
            SNAPSHOT_HEADING,
            "",
            f"- 截止日期：{state.as_of_date.isoformat()}",
            f"- 当前现实中心：{state.current_center}",
            f"- 合理范围：{_display(state.reasonable_range)}",
            f"- 已核验事件：{_display(state.verified_event_ids)}",
            f"- 当前有效状态：{_display(active_states)}",
            f"- 现实路径状态：{_display(path_states)}",
            f"- 决策动作：{state.decision_action.value}",
        )
    )
    return base.rstrip("\n") + "\n\n" + section + "\n"


def _validate_context(
    *,
    as_of_date: date | None,
    entries: tuple[EventLedgerEntry, ...] | None,
    daiyun_end: date | None,
    current_center: str | None,
    reasonable_range: tuple[str, ...],
    ledger_case_id: str | None,
) -> None:
    supplied = any(
        value is not None
        for value in (entries, daiyun_end, current_center, ledger_case_id)
    ) or bool(reasonable_range)
    if as_of_date is None:
        if supplied:
            raise ValueError("as-of 上下文只能与 as_of_date 一起提供")
        return
    if entries is None or daiyun_end is None or not (current_center or "").strip():
        raise ValueError("as_of_date 需要 entries、daiyun_end 与非空 current_center")
    if ledger_case_id is None or not ledger_case_id.strip():
        raise ValueError("as_of_date 需要显式 ledger case_id")


def _write_report(path: Path, content: str) -> None:
    if path.exists():
        if path.read_text(encoding="utf-8") == content:
            return
        raise FileExistsError(f"拒绝覆盖不同内容的既有报告: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".g8.tmp")
    try:
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def generate_report(
    input_md_path: str | Path,
    *,
    as_of_date: date | None = None,
    entries: tuple[EventLedgerEntry, ...] | None = None,
    daiyun_end: date | None = None,
    current_center: str | None = None,
    reasonable_range: tuple[str, ...] = (),
    ledger_case_id: str | None = None,
    cases_dir: str | Path | None = None,
    reports_dir: str | Path | None = None,
) -> Path:
    """运行既有生产流程，并可选择在报告末尾追加显式截止状态。"""
    _validate_context(
        as_of_date=as_of_date,
        entries=entries,
        daiyun_end=daiyun_end,
        current_center=current_center,
        reasonable_range=reasonable_range,
        ledger_case_id=ledger_case_id,
    )
    output, _timing = run_pipeline_e2e(
        input_md_path,
        cases_dir=cases_dir,
        do_render=False,
        error_policy="strict",
    )
    case_id = output.case_id
    if as_of_date is not None and ledger_case_id != case_id:
        raise ValueError(f"ledger case_id 与 pipeline case_id 不一致: {ledger_case_id} != {case_id}")

    report = render_from_output(
        output,
        variant="standard",
        lint_before=True,
        cases_dir=cases_dir,
        skip_findings_save=True,
    )
    if as_of_date is not None:
        state = build_verified_state(
            AsOfRequest(case_id, as_of_date),
            entries=entries or (),
            daiyun_end=daiyun_end,  # type: ignore[arg-type]
            current_center=current_center or "",
            reasonable_range=reasonable_range,
        )
        report = append_snapshot_section(report, state)

    report_root = Path(reports_dir) if reports_dir is not None else ROOT / "reports"
    report_path = report_root / f"{case_id}-content-report.md"
    _write_report(report_path, report)
    return report_path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生产统一报告，可选追加显式截止状态快照")
    parser.add_argument("input_md")
    parser.add_argument("--as-of", dest="as_of")
    parser.add_argument("--ledger")
    parser.add_argument("--cases-dir")
    parser.add_argument("--reports-dir")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    if bool(args.as_of) != bool(args.ledger):
        print("错误：--as-of 与 --ledger 必须成对提供", file=sys.stderr)
        return 2

    try:
        kwargs: dict[str, Any] = {
            "cases_dir": args.cases_dir,
            "reports_dir": args.reports_dir,
        }
        if args.as_of:
            ledger = load_ledger(args.ledger)
            kwargs.update(
                as_of_date=parse_iso_date(args.as_of),
                entries=ledger["entries"],
                daiyun_end=ledger["daiyun_end"],
                current_center=ledger["current_center"],
                reasonable_range=ledger["reasonable_range"],
                ledger_case_id=ledger["case_id"],
            )
        report_path = generate_report(args.input_md, **kwargs)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    print(report_path)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
