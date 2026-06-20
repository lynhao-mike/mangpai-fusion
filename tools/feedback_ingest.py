"""tools/feedback_ingest.py · v1.3 D5 结构化反馈摄入

落地契约：
    plans/architecture-v1.3.md § 四 D5（过后反馈工作流）
    plans/architecture-v1.3.md § 四 D8（每 10 反馈案触发自迭代）

工作流（命理师视角）：
    1. 命理师把 master 报告（含 `[S-...] [ ]` 反馈位）另存为
       cases/C-XXXX/feedback.md
    2. 把每条 `[ ]` 填为：
         [y]    应验
         [n]    失验
         [?]    命主当场不知道（入库不计数，等待延迟反馈兑现）
         [skip] 解释时未讲到 / 不适用
    3. 运行：python3 -m tools.feedback_ingest C-XXXX
    4. 系统反查 cases/C-XXXX/statement_index.json 找规律 ID，
       把 statement-level verdict fanout 到 rule-level，
       调 feedback_loop._apply_rule_verdicts 重算置信度
    5. 完成反馈案数 +1；若达到 10 的整数倍 → 输出迭代提示

公开 API
--------
ingest(case_id, *, cfg=None, dry_run=False) -> IngestResult
    主入口；解析 → statement_records fanout → 应用 → 计数 → 落盘审计

parse_statement_feedback(text) -> list[StatementFeedback]
    纯函数：从填好的 feedback.md 文本里抽出 [(sid, verdict), ...]

fanout_to_rules(statement_feedbacks, statement_records)
    → dict[rule_id, (Verdict, VerdictContext)]
    按决断力优先级（miss > hit > abstain > skip/no_data）合并

build_learning_samples(statement_feedbacks, statement_records)
    → list[dict]，仅输出已映射且 verdict 非 pending/no_data 的学习样本。

注意：本工具优先消费 v1.4+ 结构化路径（statement_records.json + 标注式 feedback.md）。
若 statement_records.json 不存在或 feedback.md 中无 `[S-...]` 标注，
回退给 feedback_loop.ingest_feedback 走 v1.0 启发式路径。legacy
statement_index.json / statement_rule_map.json 不再作为 Dynamic Confidence fanout 来源。

作者：Track-G v1.3
"""
from __future__ import annotations

import argparse
import datetime as _dt
import difflib
import json
import math
import pathlib
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

from engine.application.dynamic_weight_logs import (
    append_jsonl,
    ensure_log_files,
    read_jsonl,
)
from engine.application.feedback_parser import (
    ANNOTATION_TO_VERDICT,
    FEEDBACK_RE,
    StatementFeedback,
    parse_statement_feedback,
)
from engine.application.timing import PipelineTiming
from engine.application.minimal_learning_loop import (
    FeedbackNormalizationError,
    normalize_feedback_entries,
    run_learning_update,
)
from tools.feedback_loop import (
    IterationDiff,
    Verdict,
    VerdictContext,
    _apply_rule_verdicts,
    append_iteration_log,
    find_case_dir,
    total_case_count,
    write_snapshot,
)
from tools.rule_lifecycle import LifecycleConfig

# ============================================================
# 一、路径常量
# ============================================================

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
META_DIR = REPO_ROOT / "META"
ITERATION_STATE_FILE = META_DIR / "iteration-state.json"
ENGINE_LOG_DIR = REPO_ROOT / "engine" / "logs"
WEIGHT_CHANGES_LOG = ENGINE_LOG_DIR / "weight-changes.jsonl"
EXPERT_DOMAIN_FEEDBACK_LOG = ENGINE_LOG_DIR / "expert_domain_feedback.jsonl"
ADJUDICATION_ACCURACY_LOG = ENGINE_LOG_DIR / "adjudication_accuracy.jsonl"
DOMAIN_WEIGHT_PRIOR_PROFILE = REPO_ROOT / "theory" / "raw" / "yaml" / "domain_weight_profile_2026-06-05.yaml"
DEFAULT_EXPERT_SYSTEMS = ("blind", "ziping", "tiaohou_ditiansui")


# ============================================================
# 二、解析器
# ============================================================

# 反馈标注正则、标注映射、StatementFeedback 与 parse_statement_feedback
# 下沉在 engine.application.feedback_parser，避免 application 层反向依赖 tools。


@dataclass
class BridgeMappingStats:
    """Dynamic Confidence bridge 的只读映射统计。"""

    total_rows: int = 0
    mapped_rows: int = 0
    learnable_rows: int = 0
    unmapped_rows: int = 0
    pending_rows: int = 0
    needs_mapping_repair_rows: int = 0

    def to_dict(self) -> dict[str, Any]:
        total = self.total_rows or 1
        return {
            "total_rows": self.total_rows,
            "mapped_rows": self.mapped_rows,
            "learnable_rows": self.learnable_rows,
            "unmapped_rows": self.unmapped_rows,
            "pending_rows": self.pending_rows,
            "needs_mapping_repair_rows": self.needs_mapping_repair_rows,
            "recoverable_percent": round(self.learnable_rows / total * 100, 2),
            "mapped_percent": round(self.mapped_rows / total * 100, 2),
            "unmapped_percent": round(self.unmapped_rows / total * 100, 2),
            "pending_percent": round(self.pending_rows / total * 100, 2),
            "readiness": "READY_FOR_BRIDGE" if self.learnable_rows > 0 else "BLOCKED",
        }


@dataclass
class IngestResult:
    """ingest() 的返回值。"""
    case_id: str
    feedback_count: int                       # 解析到的 statement 反馈条数
    rule_count: int                           # fanout 后涉及的不重复规律数
    skipped_unknown_sid: list[str] = field(default_factory=list)
    skipped_no_index: bool = False             # 走了启发式 fallback
    iteration_diff: Optional[IterationDiff] = None
    feedback_completed_count: int = 0          # 本次写入后的总完成反馈案数
    iteration_seq: int = 0                     # 当前迭代序号（每 10 完成案 +1）
    iteration_triggered: bool = False          # 本次是否达到 10 案整数倍
    iteration_report_path: Optional[str] = None  # v1.3 D8：自动触发的迭代报告路径
    learning_sample_count: int = 0             # Dynamic Confidence 可学习样本数
    bridge_mapping_stats: Optional[BridgeMappingStats] = None
    phase_a_learning_summary: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "feedback_count": self.feedback_count,
            "rule_count": self.rule_count,
            "skipped_unknown_sid": self.skipped_unknown_sid,
            "skipped_no_index": self.skipped_no_index,
            "feedback_completed_count": self.feedback_completed_count,
            "iteration_seq": self.iteration_seq,
            "iteration_triggered": self.iteration_triggered,
            "iteration_report_path": self.iteration_report_path,
            "learning_sample_count": self.learning_sample_count,
            "bridge_mapping_stats": self.bridge_mapping_stats.to_dict() if self.bridge_mapping_stats else None,
            "phase_a_learning_summary": self.phase_a_learning_summary,
            "iteration_diff": self.iteration_diff.to_dict() if self.iteration_diff else None,
        }


# ============================================================
# 三、Statement → Rule fanout
# ============================================================

# 决断力优先级：miss 最强 → no_data 最弱
_PRIORITY: dict[Verdict, int] = {
    "miss": 0,
    "hit": 1,
    "abstain": 2,
    "no_data": 3,
}


def _merge_statement_rule_map(
    statement_index: dict[str, Any],
    rule_map: Mapping[str, Any],
) -> dict[str, Any]:
    """把旁路 statement_rule_map.json 合并进 statement_index。

    设计目标：保持 C-2026-025 标准 list schema 的
    ``statement_id/domain/summary/status`` 稳定字段不变；需要规则级校准时，
    允许 case 目录额外提供 ``statement_rule_map.json`` 作为可选追溯层。
    支持两种写法：
      - {"S-001-aaaaaa": ["M1-D-001"]}
      - {"statements": {"S-001-aaaaaa": {"rule_ids": [...]}}}
    """
    if not rule_map:
        return statement_index

    raw_map = rule_map.get("statements", rule_map) if isinstance(rule_map, Mapping) else {}
    if not isinstance(raw_map, Mapping):
        return statement_index

    merged = dict(statement_index)
    raw_statements = merged.get("statements", {})
    if isinstance(raw_statements, list):
        statement_list: list[Any] = []
        for item in raw_statements:
            if not isinstance(item, dict):
                statement_list.append(item)
                continue
            sid = item.get("statement_id")
            mapped = raw_map.get(sid) if sid else None
            if mapped:
                updated = dict(item)
                if isinstance(mapped, Mapping):
                    updated["rule_ids"] = list(mapped.get("rule_ids", []) or [])
                    if mapped.get("section") and not updated.get("section"):
                        updated["section"] = mapped.get("section")
                    if mapped.get("year") and not updated.get("year"):
                        updated["year"] = mapped.get("year")
                elif isinstance(mapped, list):
                    updated["rule_ids"] = list(mapped)
                else:
                    updated["rule_ids"] = [str(mapped)]
                statement_list.append(updated)
            else:
                statement_list.append(item)
        merged["statements"] = statement_list
        return merged

    if isinstance(raw_statements, dict):
        statement_map: dict[Any, Any] = {k: dict(v) if isinstance(v, dict) else v for k, v in raw_statements.items()}
        for sid, mapped in raw_map.items():
            if sid not in statement_map or not isinstance(statement_map[sid], dict):
                continue
            if isinstance(mapped, Mapping):
                statement_map[sid]["rule_ids"] = list(mapped.get("rule_ids", []) or [])
                statement_map[sid].setdefault("section", mapped.get("section", ""))
                if mapped.get("year"):
                    statement_map[sid].setdefault("year", mapped.get("year"))
            elif isinstance(mapped, list):
                statement_map[sid]["rule_ids"] = list(mapped)
            else:
                statement_map[sid]["rule_ids"] = [str(mapped)]
        merged["statements"] = statement_map
    return merged


def _record_map(statement_records: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """把 statement_records.json envelope 规范化为 statement_id -> record。"""

    raw_records = statement_records.get("records", []) if isinstance(statement_records, Mapping) else []
    if isinstance(raw_records, Mapping):
        raw_records = list(raw_records.values())
    records: dict[str, dict[str, Any]] = {}
    if not isinstance(raw_records, list):
        return records
    for item in raw_records:
        if not isinstance(item, dict):
            continue
        sid = str(item.get("statement_id") or "").strip()
        if sid:
            records[sid] = dict(item)
    return records


def _record_is_mapped(record: Mapping[str, Any] | None) -> bool:
    if not record:
        return False
    required = ("statement_id", "rule_id", "family_id", "school", "canon", "rule_type")
    for field in required:
        value = str(record.get(field) or "").strip()
        if not value or value.upper().startswith("UNMAPPED"):
            return False
    return True


def build_learning_samples(
    feedbacks: list[StatementFeedback],
    statement_records: Mapping[str, Any],
) -> tuple[list[dict[str, str]], list[dict[str, Any]], BridgeMappingStats]:
    """构建 Dynamic Confidence 可学习样本，但不写权重、不更新置信度。

    输出只包含七字段：statement_id, rule_id, family_id, school, canon,
    rule_type, verdict。无法 join 到 statement_records 或 metadata 不完整的反馈行
    标记为 needs_mapping_repair=true，并排除出学习样本。
    """

    records = _record_map(statement_records)
    samples: list[dict[str, str]] = []
    mapped_rows: list[dict[str, Any]] = []
    stats = BridgeMappingStats(total_rows=len(feedbacks))
    for fb in feedbacks:
        record = records.get(fb.statement_id)
        mapped = _record_is_mapped(record)
        pending = fb.verdict == "no_data"
        row = {
            "statement_id": fb.statement_id,
            "verdict": fb.verdict,
            "annotation": fb.annotation,
            "needs_mapping_repair": not mapped,
            "repair_reason": "" if mapped else "statement_id_not_found_or_incomplete_statement_record",
        }
        if record:
            row.update({
                "rule_id": str(record.get("rule_id") or ""),
                "family_id": str(record.get("family_id") or ""),
                "school": str(record.get("school") or ""),
                "canon": str(record.get("canon") or ""),
                "rule_type": str(record.get("rule_type") or ""),
            })
        else:
            row.update({
                "rule_id": "UNMAPPED",
                "family_id": "UNMAPPED",
                "school": "UNMAPPED",
                "canon": "UNMAPPED",
                "rule_type": "UNMAPPED",
            })
        mapped_rows.append(row)
        if pending:
            stats.pending_rows += 1
        if mapped:
            stats.mapped_rows += 1
        else:
            stats.unmapped_rows += 1
            stats.needs_mapping_repair_rows += 1
        if mapped and not pending:
            sample = {
                "statement_id": fb.statement_id,
                "rule_id": row["rule_id"],
                "family_id": row["family_id"],
                "school": row["school"],
                "canon": row["canon"],
                "rule_type": row["rule_type"],
                "verdict": fb.verdict,
            }
            samples.append(sample)
            stats.learnable_rows += 1
    return samples, mapped_rows, stats


def fanout_to_rules(
    feedbacks: list[StatementFeedback],
    statement_records: Mapping[str, Any],
) -> tuple[dict[str, tuple[Verdict, VerdictContext]], list[str]]:
    """把 statement-level verdict 通过 statement_records / legacy statement_index fanout 到 rule-level。"""

    records = _record_map(statement_records)
    legacy_statements = _statement_map(dict(statement_records)) if isinstance(statement_records, Mapping) else {}
    rule_verdicts: dict[str, tuple[Verdict, VerdictContext]] = {}
    unknown_sids: list[str] = []

    for fb in feedbacks:
        info = records.get(fb.statement_id)
        legacy_info = legacy_statements.get(fb.statement_id)
        if _record_is_mapped(info):
            rule_ids = [str(info.get("rule_id") or "").strip()]
            context_source = info or {}
        elif legacy_info is not None:
            rule_ids = [str(rid).strip() for rid in (legacy_info.get("rule_ids", []) or []) if str(rid).strip()]
            context_source = legacy_info
            if not rule_ids:
                continue
        else:
            unknown_sids.append(fb.statement_id)
            continue

        for rid in rule_ids:
            existing = rule_verdicts.get(rid)
            if existing is None or _PRIORITY[fb.verdict] < _PRIORITY[existing[0]]:
                prev_sids = existing[1].statement_ids if existing else []
                vctx = VerdictContext(
                    section=str(context_source.get("section") or ""),
                    year=context_source.get("year"),
                    domain=str(context_source.get("domain") or ""),
                    role=str(context_source.get("role") or "unknown"),
                    statement_ids=sorted(set(prev_sids + [fb.statement_id])),
                )
                rule_verdicts[rid] = (fb.verdict, vctx)
            else:
                ev, vctx = existing
                vctx.statement_ids = sorted(set(vctx.statement_ids + [fb.statement_id]))

    return rule_verdicts, unknown_sids


def fanout_to_parallel_feedback(
    feedbacks: list[StatementFeedback],
    statement_index: dict[str, Any],
    *,
    case_id: str,
    dry_run: bool = False,
) -> dict[str, int]:
    """把 statement 反馈旁路登记到 reading / adjudication 级 JSONL。"""

    statements = _statement_map(statement_index)
    expert_rows: list[dict[str, Any]] = []
    adjudication_rows: list[dict[str, Any]] = []
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for feedback in feedbacks:
        if feedback.verdict not in {"hit", "miss"}:
            continue
        info = statements.get(feedback.statement_id)
        if not info:
            continue
        domain = str(info.get("domain", ""))
        expert_systems = [str(x) for x in info.get("expert_systems", []) or []]
        reading_ids = [str(x) for x in info.get("reading_ids", []) or []]
        if not expert_systems and info.get("expert_system"):
            expert_systems = [str(info.get("expert_system"))]
        for reading_id in reading_ids:
            expert = _expert_for_reading(reading_id, expert_systems)
            expert_rows.append({
                "ts": now,
                "event_type": "expert_domain_feedback",
                "case_id": case_id,
                "statement_id": feedback.statement_id,
                "reading_id": reading_id,
                "domain": domain,
                "expert_system": expert,
                "verdict": feedback.verdict,
                "annotation": feedback.annotation,
            })
        adjudication_id = str(info.get("adjudication_id", ""))
        if adjudication_id:
            adjudication_rows.append({
                "ts": now,
                "event_type": "adjudication_accuracy",
                "case_id": case_id,
                "statement_id": feedback.statement_id,
                "adjudication_id": adjudication_id,
                "domain": domain,
                "claim": info.get("claim", info.get("summary", "")),
                "decision": info.get("decision", info.get("stance", "")),
                "supporting_experts": list(info.get("supporting_experts", []) or []),
                "dissenting_experts": list(info.get("dissenting_experts", []) or []),
                "abstained_experts": list(info.get("abstained_experts", []) or []),
                "consensus_layer": info.get("consensus_layer", info.get("layer", "")),
                "verdict": feedback.verdict,
                "minority_vindicated": feedback.verdict == "miss",
            })
    if not dry_run:
        ensure_log_files((WEIGHT_CHANGES_LOG, EXPERT_DOMAIN_FEEDBACK_LOG, ADJUDICATION_ACCURACY_LOG))
        _append_jsonl(EXPERT_DOMAIN_FEEDBACK_LOG, expert_rows, event_type="expert_domain_feedback")
        _append_jsonl(ADJUDICATION_ACCURACY_LOG, adjudication_rows, event_type="adjudication_accuracy")
    return {"expert_feedback_rows": len(expert_rows), "adjudication_feedback_rows": len(adjudication_rows)}


def get_expert_domain_stats(domain: str | None = None, expert: str | None = None) -> dict[str, Any]:
    """聚合 expert × domain 的 hit/miss、Beta 均值与 Wilson 下界。"""

    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    for row in _read_jsonl(EXPERT_DOMAIN_FEEDBACK_LOG):
        row_domain = str(row.get("domain", ""))
        row_expert = str(row.get("expert_system", ""))
        if domain is not None and row_domain != domain:
            continue
        if expert is not None and row_expert != expert:
            continue
        if row.get("verdict") not in {"hit", "miss"}:
            continue
        bucket = buckets.setdefault(
            (row_domain, row_expert),
            {"domain": row_domain, "expert_system": row_expert, "hits": 0, "misses": 0},
        )
        if row.get("verdict") == "hit":
            bucket["hits"] += 1
        else:
            bucket["misses"] += 1
    stats = [_finalize_expert_stats(bucket) for bucket in buckets.values()]
    return {"items": stats}


def compute_weight_update_proposal(min_n_eff: int = 10) -> dict[str, Any]:
    """基于反馈历史计算动态权重调整提案；不自动写入任何 YAML。"""

    stats = get_expert_domain_stats()["items"]
    proposals: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for item in stats:
        n_eff = float(item["n_eff"])
        diagnostic = {
            "domain": item["domain"],
            "expert_system": item["expert_system"],
            "n_eff": n_eff,
            "beta_mean": item["beta_mean"],
            "wilson_lower": item["wilson_lower"],
            "adjustment_allowed": False,
            "reason": "样本不足，不调整" if n_eff < min_n_eff else "样本达到阈值，可进入人工 review",
        }
        if n_eff < min_n_eff:
            diagnostics.append(diagnostic)
            continue
        lower_bound = 0.70 if n_eff >= 10 else 0.90
        upper_bound = 1.30 if n_eff >= 10 else 1.10
        multiplier = min(upper_bound, max(lower_bound, float(item["beta_mean"]) / 0.5))
        proposal = {
            "domain": item["domain"],
            "expert_system": item["expert_system"],
            "n_eff": n_eff,
            "beta_mean": item["beta_mean"],
            "wilson_lower": item["wilson_lower"],
            "proposed_feedback_multiplier": round(multiplier, 6),
            "requires_human_review": True,
            "source": "expert_domain_feedback_stats",
        }
        proposals.append(proposal)
        diagnostics.append({**diagnostic, "adjustment_allowed": True, "proposed_feedback_multiplier": proposal["proposed_feedback_multiplier"]})
    return {
        "schema_version": "expert-domain-weight-proposal/v0.2",
        "min_n_eff": min_n_eff,
        "proposal_count": len(proposals),
        "proposals": proposals,
        "diagnostics": diagnostics,
        "note": "仅为动态权重调整提案；未经 apply_weight_update_proposal(confirm=True) 不会写入任何权重文件。",
    }


def apply_weight_update_proposal(
    proposal: Mapping[str, Any],
    *,
    base_profile: Mapping[str, Any] | None = None,
    confirm: bool = False,
    output_path: str | pathlib.Path | None = None,
) -> dict[str, Any]:
    """显式确认后把 proposal 应用为新 overlay；默认只返回 preview diff。"""

    base = dict(base_profile or _load_weight_prior_profile())
    base_weights = base.get("weights", {})
    if not isinstance(base_weights, Mapping):
        raise ValueError("base profile 缺少 weights mapping。")
    proposed_weights = _apply_proposal_to_weights(base_weights, proposal.get("proposals", []))
    overlay = {
        "schema_version": "expert-domain-feedback-overlay/v0.1",
        "status": "human_confirmed" if confirm else "preview_only",
        "base_profile_id": base.get("profile_id", ""),
        "base_profile_version": base.get("profile_version", ""),
        "source": "tools.feedback_ingest.apply_weight_update_proposal",
        "requires_human_review": not confirm,
        "weights": proposed_weights,
    }
    preview_diff = _weight_preview_diff(base_weights, proposed_weights)
    result = {
        "applied": bool(confirm and output_path),
        "confirmed": confirm,
        "output_path": str(output_path) if output_path else None,
        "preview_diff": preview_diff,
        "overlay": overlay,
    }
    if not confirm:
        return result
    if output_path is None:
        raise ValueError("confirm=True 时必须提供 output_path，且不得覆盖 prior profile。")
    target = pathlib.Path(output_path)
    if target.resolve() == DOMAIN_WEIGHT_PRIOR_PROFILE.resolve():
        raise ValueError("禁止覆盖 review_draft prior profile；请写入新的 overlay 文件。")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(overlay, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {**result, "applied": True}


def _load_weight_prior_profile() -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("读取 prior profile 需要 PyYAML。") from exc
    raw = yaml.safe_load(DOMAIN_WEIGHT_PRIOR_PROFILE.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"领域权重 prior profile 顶层必须是 mapping：{DOMAIN_WEIGHT_PRIOR_PROFILE}")
    return raw


def _apply_proposal_to_weights(
    base_weights: Mapping[str, Any],
    proposals: Any,
) -> dict[str, dict[str, float]]:
    multipliers: dict[tuple[str, str], float] = {}
    for item in proposals if isinstance(proposals, list) else []:
        if not isinstance(item, Mapping):
            continue
        if item.get("requires_human_review") is not True:
            continue
        domain = str(item.get("domain", ""))
        expert = str(item.get("expert_system", ""))
        if domain and expert:
            multipliers[(domain, expert)] = float(item.get("proposed_feedback_multiplier", 1.0))

    proposed: dict[str, dict[str, float]] = {}
    for domain, domain_weights in base_weights.items():
        if not isinstance(domain_weights, Mapping):
            continue
        adjusted = {
            expert: float(domain_weights.get(expert, 0.0)) * multipliers.get((str(domain), expert), 1.0)
            for expert in DEFAULT_EXPERT_SYSTEMS
        }
        proposed[str(domain)] = _normalize_domain_weights(adjusted)
    return proposed


def _normalize_domain_weights(weights: Mapping[str, float]) -> dict[str, float]:
    total = sum(float(weights.get(expert, 0.0)) for expert in DEFAULT_EXPERT_SYSTEMS)
    if total <= 0:
        return {expert: round(1 / len(DEFAULT_EXPERT_SYSTEMS), 6) for expert in DEFAULT_EXPERT_SYSTEMS}
    normalized = {expert: float(weights.get(expert, 0.0)) / total for expert in DEFAULT_EXPERT_SYSTEMS}
    rounded = {expert: round(value, 6) for expert, value in normalized.items()}
    drift = round(1.0 - sum(rounded.values()), 6)
    if drift:
        rounded[DEFAULT_EXPERT_SYSTEMS[0]] = round(rounded[DEFAULT_EXPERT_SYSTEMS[0]] + drift, 6)
    return rounded


def _weight_preview_diff(
    base_weights: Mapping[str, Any],
    proposed_weights: Mapping[str, Any],
) -> str:
    before = json.dumps(base_weights, ensure_ascii=False, indent=2, sort_keys=True).splitlines()
    after = json.dumps(proposed_weights, ensure_ascii=False, indent=2, sort_keys=True).splitlines()
    return "\n".join(difflib.unified_diff(before, after, fromfile="prior_weights", tofile="feedback_overlay", lineterm=""))


def _statement_map(statement_index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = statement_index.get("statements", {})
    if isinstance(raw, list):
        return {
            str(item.get("statement_id")): item
            for item in raw
            if isinstance(item, dict) and item.get("statement_id")
        }
    if isinstance(raw, dict):
        return {str(key): value for key, value in raw.items() if isinstance(value, dict)}
    return {}


def _expert_for_reading(reading_id: str, fallback_experts: list[str]) -> str:
    upper = reading_id.upper()
    if "ZIPING" in upper or "子平" in reading_id:
        return "ziping"
    if "DITIANSUI" in upper or "TIAOHOU" in upper or "滴天髓" in reading_id:
        return "tiaohou_ditiansui"
    if "BLIND" in upper or "盲派" in reading_id:
        return "blind"
    if len(fallback_experts) == 1:
        return fallback_experts[0]
    return ""


def _append_jsonl(path: pathlib.Path, rows: list[dict[str, Any]], *, event_type: str | None = None) -> None:
    append_jsonl(path, rows, event_type=event_type)


def _read_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    return read_jsonl(path)


def _finalize_expert_stats(bucket: dict[str, Any]) -> dict[str, Any]:
    hits = int(bucket["hits"])
    misses = int(bucket["misses"])
    n_eff = hits + misses
    beta_mean = (hits + 1) / (n_eff + 2) if n_eff >= 0 else 0.5
    return {
        "domain": bucket["domain"],
        "expert_system": bucket["expert_system"],
        "hits": hits,
        "misses": misses,
        "n_eff": float(n_eff),
        "beta_mean": round(beta_mean, 6),
        "wilson_lower": round(_wilson_lower(hits, n_eff), 6),
        "sample_warning": n_eff < 5,
    }


def _wilson_lower(hits: int, total: int, z: float = 1.96) -> float:
    if total <= 0:
        return 0.0
    phat = hits / total
    denominator = 1 + z * z / total
    centre = phat + z * z / (2 * total)
    margin = z * math.sqrt((phat * (1 - phat) + z * z / (4 * total)) / total)
    return max(0.0, (centre - margin) / denominator)


# ============================================================
# 四、迭代计数器（D8 每 10 反馈案触发）
# ============================================================

@dataclass
class IterationState:
    feedback_completed_count: int = 0
    last_iteration_at_count: int = 0
    iteration_seq: int = 0
    completed_case_ids: list[str] = field(default_factory=list)

    @classmethod
    def load(cls) -> "IterationState":
        if ITERATION_STATE_FILE.exists():
            try:
                payload = json.loads(ITERATION_STATE_FILE.read_text(encoding="utf-8"))
                return cls(
                    feedback_completed_count=payload.get("feedback_completed_count", 0),
                    last_iteration_at_count=payload.get("last_iteration_at_count", 0),
                    iteration_seq=payload.get("iteration_seq", 0),
                    completed_case_ids=payload.get("completed_case_ids", []),
                )
            except (json.JSONDecodeError, ValueError):
                pass
        return cls()

    def save(self) -> None:
        META_DIR.mkdir(parents=True, exist_ok=True)
        ITERATION_STATE_FILE.write_text(
            json.dumps(
                {
                    "feedback_completed_count": self.feedback_completed_count,
                    "last_iteration_at_count": self.last_iteration_at_count,
                    "iteration_seq": self.iteration_seq,
                    "completed_case_ids": self.completed_case_ids,
                    "_updated_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


# ============================================================
# 五、主入口 ingest()
# ============================================================

def ingest(
    case_id: str,
    *,
    cfg: Optional[LifecycleConfig] = None,
    today: Optional[str] = None,
    dry_run: bool = False,
) -> IngestResult:
    """v1.4 bridge 主入口：解析 feedback.md → statement_records fanout → 应用 → 计数。

    Steps:
        1. 找 case 目录
        2. 读 statement_records.json（Dynamic Confidence 学习事实源）
        3. 解析 feedback.md 中的 `[S-...] [y/n/?/skip]` 标注
        4. 生成只读 learning samples，并标记无法映射的 row
        5. fanout 到 rule_verdicts
        6. 调 feedback_loop._apply_rule_verdicts 应用现有规则级更新
        7. 写 iteration-log + snapshot
        8. 更新 META/iteration-state.json 计数器
        9. 检查 % 10 == 0 → iteration_triggered=True

    Args:
        case_id:  完整 case_id 或前缀（如 ``C-2026-001``）
        cfg:      LifecycleConfig；默认从 engine/calibration.yaml 加载
        today:    ISO 日期串（测试用）
        dry_run:  True 则不写规律 yaml / 不写 iteration-log / 不写 state

    Raises:
        FileNotFoundError: case 目录或 feedback.md 不存在
        RuntimeError:      没有可解析的反馈（既无标注又无启发式可走）
    """
    cfg = cfg or LifecycleConfig.from_yaml()
    today = today or _dt.date.today().isoformat()
    timing = PipelineTiming()
    timing_run_id = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    case_dir = find_case_dir(case_id)
    full_case_id = case_dir.name

    feedback_path = case_dir / "feedback.md"
    if not feedback_path.exists():
        raise FileNotFoundError(f"feedback.md 不存在: {feedback_path}")

    # 1. 解析 statement-level 标注
    with timing.step("parse_feedback"):
        feedback_text = feedback_path.read_text(encoding="utf-8")
        feedbacks = parse_statement_feedback(feedback_text)

    # 2. 读 statement_records。legacy statement_index / statement_rule_map 不再作为 bridge fanout 来源。
    records_path = case_dir / "statement_records.json"
    statement_records: dict[str, Any] = {}
    skipped_no_index = False
    with timing.step("load_statement_records"):
        if records_path.exists():
            try:
                statement_records = json.loads(records_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, ValueError):
                statement_records = {}

    # 3. 决策路径选择
    if not feedbacks or not _record_map(statement_records):
        # 退回 v1.0 启发式路径（feedback_loop.ingest_feedback）
        from tools.feedback_loop import ingest_feedback as _legacy_ingest
        with timing.step("apply_rules"):
            diff = _legacy_ingest(full_case_id, cfg=cfg, today=today, dry_run=dry_run)
        skipped_no_index = True
        # 仍然把这个案纳入完成反馈计数（哪怕走了启发式）
        result = IngestResult(
            case_id=full_case_id,
            feedback_count=len(feedbacks),
            rule_count=len(diff.rule_updates),
            skipped_unknown_sid=[],
            skipped_no_index=True,
            iteration_diff=diff,
            bridge_mapping_stats=BridgeMappingStats(
                total_rows=len(feedbacks),
                unmapped_rows=len(feedbacks),
                needs_mapping_repair_rows=len(feedbacks),
            ),
        )
        if not dry_run:
            with timing.step("bump_state"):
                _bump_state(result, full_case_id, timing=timing)
            _write_ingest_timing(timing, timing_run_id, result, dry_run=dry_run)
        return result

    # 4. 生成 bridge learning samples、执行 Phase-A 最小学习更新，再执行现有规则级 fanout。
    with timing.step("bridge_learning_samples"):
        learning_samples, mapped_rows, bridge_stats = build_learning_samples(feedbacks, statement_records)
        normalized_feedback = normalize_feedback_entries(
            feedbacks,
            case_id=full_case_id,
            source_text=feedback_text,
        )
    with timing.step("phase_a_learning_update"):
        phase_a_learning_summary = run_learning_update(
            statement_records,
            normalized_feedback,
            case_dir=case_dir,
            dry_run=dry_run,
        )
    with timing.step("fanout"):
        rule_verdicts, unknown_sids = fanout_to_rules(feedbacks, statement_records)
        parallel_feedback_counts = {"expert_feedback_rows": 0, "adjudication_feedback_rows": 0}

    # 5. 应用现有规则级更新（不写 log，本函数末尾统一写）。
    with timing.step("apply_rules"):
        diff = _apply_rule_verdicts(
            full_case_id, rule_verdicts, cfg=cfg, today=today, dry_run=dry_run
        )

    diff.notes.append(
        "Phase-A Minimal Learning Loop："
        f"learnable={len(learning_samples)}，mapped={bridge_stats.mapped_rows}，"
        f"unmapped={bridge_stats.unmapped_rows}，pending={bridge_stats.pending_rows}，"
        f"confidence_updates={phase_a_learning_summary['updated_count']}。"
    )
    if not rule_verdicts:
        diff.notes.append(
            "statement-level 反馈已登记，但未找到完整 statement_records 映射；"
            "needs_mapping_repair=true 的 row 不纳入学习样本"
        )
    if parallel_feedback_counts["expert_feedback_rows"] or parallel_feedback_counts["adjudication_feedback_rows"]:
        diff.notes.append(
            "parallel-domain 反馈已登记："
            f"reading={parallel_feedback_counts['expert_feedback_rows']}，"
            f"adjudication={parallel_feedback_counts['adjudication_feedback_rows']}"
        )

    # 6. 落 log + snapshot
    if unknown_sids:
        diff.notes.append(
            f"忽略 {len(unknown_sids)} 个 statement_id（feedback 与 statement_records 不匹配，"
            f"可能需重跑 render）：{','.join(unknown_sids[:3])}"
        )
    if not dry_run:
        with timing.step("write_audit"):
            append_iteration_log(diff)
            write_snapshot(diff)

    # 7. 计数器
    result = IngestResult(
        case_id=full_case_id,
        feedback_count=len(feedbacks),
        rule_count=len(rule_verdicts),
        skipped_unknown_sid=unknown_sids,
        iteration_diff=diff,
        learning_sample_count=len(learning_samples),
        bridge_mapping_stats=bridge_stats,
        phase_a_learning_summary=phase_a_learning_summary,
    )
    if not dry_run:
        with timing.step("bump_state"):
            _bump_state(result, full_case_id, timing=timing)
        _write_ingest_timing(timing, timing_run_id, result, dry_run=dry_run)

    return result


def _bump_state(
    result: IngestResult,
    case_id: str,
    *,
    timing: Optional[PipelineTiming] = None,
) -> None:
    """把当前案件计入完成反馈，并检测是否到 10 案触发点。"""
    state = IterationState.load()
    completed_case_id_set = set(state.completed_case_ids)
    if case_id in completed_case_id_set:
        # 同一案重复 ingest 不重复计数
        result.feedback_completed_count = state.feedback_completed_count
        result.iteration_seq = state.iteration_seq
        return
    state.feedback_completed_count += 1
    state.completed_case_ids.append(case_id)

    # 每 10 案触发一次（D8 锁定）
    if state.feedback_completed_count - state.last_iteration_at_count >= 10:
        state.iteration_seq += 1
        state.last_iteration_at_count = state.feedback_completed_count
        result.iteration_triggered = True
        result.iteration_seq = state.iteration_seq
    else:
        result.iteration_seq = state.iteration_seq

    result.feedback_completed_count = state.feedback_completed_count
    state.save()

    # v1.3 D8：完成反馈案达 10 整数倍 → 自动触发迭代调度
    # 失败不阻塞 ingest 主流程（warn-only），命理师仍能继续摄入下一案
    if result.iteration_triggered:
        try:
            from tools.iteration_report import run_iteration
            if timing is None:
                ir = run_iteration(seq=result.iteration_seq, dry_run=False)
            else:
                with timing.step("iteration_report"):
                    ir = run_iteration(seq=result.iteration_seq, dry_run=False)
            if ir.report_path:
                result.iteration_report_path = str(ir.report_path)
        except Exception as exc:  # noqa: BLE001
            # 把异常打到 iteration_diff.notes（如果存在），不抛
            if result.iteration_diff is not None:
                result.iteration_diff.notes.append(
                    f"[D8 warn-only] iteration_report 触发失败：{exc!r}"
                )


def _write_ingest_timing(
    timing: PipelineTiming,
    run_id: str,
    result: IngestResult,
    *,
    dry_run: bool,
) -> None:
    """将 feedback ingest 耗时写入 META/timings/，不阻断主流程。"""
    try:
        timing.write_meta_timing(
            META_DIR,
            timing_type="feedback_ingest",
            run_id=f"{run_id}-{result.case_id}",
            case_id=result.case_id,
            extra={
                "feedback_count": result.feedback_count,
                "rule_count": result.rule_count,
                "skipped_unknown_sid_count": len(result.skipped_unknown_sid),
                "skipped_no_index": result.skipped_no_index,
                "learning_sample_count": result.learning_sample_count,
                "bridge_mapping_stats": result.bridge_mapping_stats.to_dict() if result.bridge_mapping_stats else None,
                "phase_a_learning_summary": result.phase_a_learning_summary,
                "iteration_triggered": result.iteration_triggered,
                "iteration_seq": result.iteration_seq,
                "dry_run": dry_run,
            },
        )
    except OSError:
        pass


# ============================================================
# 六、CLI
# ============================================================

def _safe_print(text: str = "") -> None:
    """跨平台安全打印，避免 Windows cmd 的 GBK 编码被 emoji 阻断。"""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(
            sys.stdout.encoding or "utf-8", errors="replace"
        ))


def _print_human(result: IngestResult) -> None:
    _safe_print(f"\n[feedback_ingest] case_id={result.case_id}")
    _safe_print(f"  解析到 statement 反馈: {result.feedback_count} 条")
    _safe_print(f"  fanout 后涉及规律: {result.rule_count} 条")
    _safe_print(f"  Dynamic Confidence 可学习样本: {result.learning_sample_count} 条")
    if result.phase_a_learning_summary:
        _safe_print(
            "  Phase-A 学习更新: "
            f"updates={result.phase_a_learning_summary.get('updated_count', 0)} / "
            f"observable_changes={len(result.phase_a_learning_summary.get('observable_confidence_changes', []))}"
        )
    if result.bridge_mapping_stats:
        stats = result.bridge_mapping_stats.to_dict()
        _safe_print(
            "  bridge 映射统计: "
            f"recoverable={stats['recoverable_percent']}% / "
            f"unmapped={stats['unmapped_percent']}% / pending={stats['pending_percent']}% / "
            f"{stats['readiness']}"
        )
    if result.skipped_no_index:
        _safe_print("  [WARN] statement_records.json 缺失或为空 → 已退回 v1.0 启发式路径")
    if result.skipped_unknown_sid:
        _safe_print(f"  [WARN] 忽略未知 sid: {len(result.skipped_unknown_sid)} 条 (前 3: "
                    f"{','.join(result.skipped_unknown_sid[:3])})")
    if result.iteration_diff:
        d = result.iteration_diff
        _safe_print(f"  规律更新: {len(d.rule_updates)} 条 / "
                    f"状态变更: {len(d.status_changes)} 条 / "
                    f"跨派扫描: {'是' if d.cross_school_triggered else '否'}")
    _safe_print(f"  累计完成反馈案: {result.feedback_completed_count}")
    _safe_print(f"  当前迭代序号 (iteration_seq): {result.iteration_seq:03d}")
    if result.iteration_triggered:
        _safe_print("\n  ** 已达 10 案整数倍 → iteration_report 已自动触发 **")
        if result.iteration_report_path:
            _safe_print(f"     报告: {result.iteration_report_path}")
        else:
            _safe_print("     [WARN] 报告写入失败，详见 iteration_diff.notes")
            _safe_print(f"     预期路径: META/iteration-report-{result.iteration_seq:03d}.md")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="结构化反馈摄入：解析 feedback.md → statement_records bridge fanout → 应用规律级更新"
    )
    parser.add_argument("case_id", nargs="?", help="案例 ID 或前缀（如 C-2026-001）")
    parser.add_argument("--dry-run", action="store_true", help="不落盘 yaml / log / state")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出结果")
    parser.add_argument("--expert-domain-stats", action="store_true", help="只读输出专家×功能域反馈统计")
    parser.add_argument("--weight-proposal", action="store_true", help="只读输出动态权重调整 proposal，不写文件")
    parser.add_argument("--min-n-eff", type=int, default=10, help="生成权重 proposal 的最小有效样本数")
    args = parser.parse_args(argv)

    if args.expert_domain_stats:
        print(json.dumps(get_expert_domain_stats(), ensure_ascii=False, indent=2))
        return 0
    if args.weight_proposal:
        print(json.dumps(compute_weight_update_proposal(min_n_eff=args.min_n_eff), ensure_ascii=False, indent=2))
        return 0
    if not args.case_id:
        parser.error("除 --expert-domain-stats / --weight-proposal 外必须提供 case_id")

    try:
        result = ingest(args.case_id, dry_run=args.dry_run)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_human(result)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
