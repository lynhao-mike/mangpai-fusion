"""领域层数据结构：最终断语、冲突登记与完整分析输出。"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

from engine import FINDINGS_SCHEMA_VERSION, PIPELINE_SCHEMA_VERSION
from engine.energy.types import Confidence, EnergyFindings, Evidence, School
from engine.pangzheng.types import SupportFindings
from engine.picture.types import PictureFindings
from engine.yingqi.types import GateResult

ConclusionLayer = Literal["共识", "互补", "独门", "冲突仲裁"]


@dataclass
class FinalConclusion:
    """每条最终断语（含完整 trace_id 链）。

    evidence 字段 = trace_id 链：从 D1-D4 各层 evidence 汇聚而来，
    保证 render_report 时能 100% 溯源每一条断语的支撑规律。
    """
    conclusion_id: str                   # "CC-001"
    statement: str                       # 断语文字
    domain: str                          # 婚姻/事业/财运/学业/健康/六亲/格局/其他
    layer: ConclusionLayer               # 共识/互补/独门/冲突仲裁
    contributing_schools: list[School]    # 贡献派别
    confidence: Confidence
    evidence: list[Evidence]             # trace_id 链（核心！）
    yingqi_year: Optional[int] = None    # 应期年份（非 None 时为应期断语）
    falsifiable: str = ""                # 证伪条件

    def to_dict(self) -> dict[str, Any]:
        return {
            "conclusion_id": self.conclusion_id,
            "statement": self.statement,
            "domain": self.domain,
            "layer": self.layer,
            "contributing_schools": list(self.contributing_schools),
            "confidence": self.confidence.to_dict(),
            "evidence": [e.to_dict() for e in self.evidence],
            "yingqi_year": self.yingqi_year,
            "falsifiable": self.falsifiable,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "FinalConclusion":
        return cls(
            conclusion_id=d["conclusion_id"],
            statement=d["statement"],
            domain=d["domain"],
            layer=d["layer"],
            contributing_schools=list(d["contributing_schools"]),
            confidence=Confidence.from_dict(d["confidence"]),
            evidence=[Evidence.from_dict(x) for x in d.get("evidence", [])],
            yingqi_year=d.get("yingqi_year"),
            falsifiable=d.get("falsifiable", ""),
        )

    @property
    def trace_ids(self) -> list[str]:
        """便捷提取所有 rule_id（trace_id 链）。"""
        return [e.rule_id for e in self.evidence]

@dataclass
class Stance:
    """派别立场。"""
    school: School
    position: str
    confidence: Confidence
    rules: list[Evidence] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "school": self.school,
            "position": self.position,
            "confidence": self.confidence.to_dict(),
            "rules": [r.to_dict() for r in self.rules],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Stance":
        return cls(
            school=d["school"],
            position=d["position"],
            confidence=Confidence.from_dict(d["confidence"]),
            rules=[Evidence.from_dict(x) for x in d.get("rules", [])],
        )

@dataclass
class CrossSchoolConflict:
    """跨派冲突显式登记。"""
    conflict_id: str                     # "CFL-HUNYIN-001"
    domain: str
    description: str
    stances: list[Stance] = field(default_factory=list)
    arbitration_rule: Optional[str] = None
    winner: Optional[School] = None
    output_strategy: Literal["显示主胜方", "并列显示", "降级输出"] = "并列显示"

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "domain": self.domain,
            "description": self.description,
            "stances": [s.to_dict() for s in self.stances],
            "arbitration_rule": self.arbitration_rule,
            "winner": self.winner,
            "output_strategy": self.output_strategy,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CrossSchoolConflict":
        return cls(
            conflict_id=d["conflict_id"],
            domain=d["domain"],
            description=d["description"],
            stances=[Stance.from_dict(x) for x in d.get("stances", [])],
            arbitration_rule=d.get("arbitration_rule"),
            winner=d.get("winner"),
            output_strategy=d.get("output_strategy", "并列显示"),
        )

def _load_retrospective(d: Any) -> Optional[Any]:
    """延迟导入 + 容错的 RetrospectiveReport 反序列化。"""
    if not d:
        return None
    try:
        from engine.yingqi.retrospective import RetrospectiveReport
        return RetrospectiveReport.from_dict(d)
    except Exception:  # noqa: BLE001
        return None

@dataclass
class AnalysisOutput:
    """完整分析输出。

    包含 D1-D4 子结论 + 整合后的 final_conclusions。
    render_report / output_linter / feedback_loop 均以此为输入。
    """
    case_id: str
    analysis_date: str                   # ISO date (YYYY-MM-DD)

    # 4 派子结论（保留完整结构，下游可追溯）
    energy: EnergyFindings
    picture: PictureFindings
    gate_results: list[GateResult]
    support: SupportFindings

    # 整合后的最终结论
    final_conclusions: list[FinalConclusion] = field(default_factory=list)

    # 跨派冲突
    conflicts: list[CrossSchoolConflict] = field(default_factory=list)

    # 应期总表（按年排序，render_report 用）
    yingqi_table: list[dict[str, Any]] = field(default_factory=list)

    # 整体置信度
    overall_confidence: Optional[Confidence] = None
    layer_summary: dict[str, int] = field(default_factory=dict)

    # 元信息
    schema_version: str = FINDINGS_SCHEMA_VERSION
    pipeline_version: str = PIPELINE_SCHEMA_VERSION
    generated_at: str = ""

    # Hash 链验证结果
    hash_chain_valid: bool = True
    hash_chain_notes: list[str] = field(default_factory=list)

    # F6 · 流年回溯（不参与 hash 链；run_pipeline 注入）
    retrospective: Optional[Any] = None  # RetrospectiveReport（避免循环导入）

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "pipeline_version": self.pipeline_version,
            "generated_at": self.generated_at,
            "case_id": self.case_id,
            "analysis_date": self.analysis_date,
            "energy": self.energy.to_dict(),
            "picture": self.picture.to_dict(),
            "gate_results": [g.to_dict() for g in self.gate_results],
            "support": self.support.to_dict(),
            "final_conclusions": [c.to_dict() for c in self.final_conclusions],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "yingqi_table": list(self.yingqi_table),
            "overall_confidence": (
                self.overall_confidence.to_dict()
                if self.overall_confidence else None
            ),
            "layer_summary": dict(self.layer_summary),
            "hash_chain_valid": self.hash_chain_valid,
            "hash_chain_notes": list(self.hash_chain_notes),
            "retrospective": (
                self.retrospective.to_dict()
                if self.retrospective is not None
                and hasattr(self.retrospective, "to_dict")
                else None
            ),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AnalysisOutput":
        return cls(
            case_id=d["case_id"],
            analysis_date=d["analysis_date"],
            energy=EnergyFindings.from_dict(d["energy"]),
            picture=PictureFindings.from_dict(d["picture"]),
            gate_results=[GateResult.from_dict(g) for g in d.get("gate_results", [])],
            support=SupportFindings.from_dict(d["support"]),
            final_conclusions=[
                FinalConclusion.from_dict(c) for c in d.get("final_conclusions", [])
            ],
            conflicts=[
                CrossSchoolConflict.from_dict(c) for c in d.get("conflicts", [])
            ],
            yingqi_table=list(d.get("yingqi_table", [])),
            overall_confidence=(
                Confidence.from_dict(d["overall_confidence"])
                if d.get("overall_confidence") else None
            ),
            layer_summary=dict(d.get("layer_summary", {})),
            schema_version=d.get("schema_version", FINDINGS_SCHEMA_VERSION),
            pipeline_version=d.get("pipeline_version", PIPELINE_SCHEMA_VERSION),
            generated_at=d.get("generated_at", ""),
            hash_chain_valid=bool(d.get("hash_chain_valid", True)),
            hash_chain_notes=list(d.get("hash_chain_notes", [])),
            retrospective=_load_retrospective(d.get("retrospective")),
        )

    def to_json(self, *, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, s: str) -> "AnalysisOutput":
        return cls.from_dict(json.loads(s))

    def hash(self) -> str:
        """SHA-256[:16] of the entire output."""
        canonical = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
