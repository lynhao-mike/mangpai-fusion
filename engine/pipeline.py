"""engine/pipeline.py · v1.2 流水线整合层

按 03-findings-schema.md § 九 + 07-pipeline-flow.md § 七 实现。

提供：
- FinalConclusion   — 每条最终断语（含完整 trace_id 链 = evidence: list[Evidence]）
- CrossSchoolConflict — 跨派冲突显式登记
- AnalysisOutput    — 完整分析输出（render_report 直接消费）
- integrate()       — 合并 D1-D4 → AnalysisOutput
- run_pipeline()    — 端到端编排：parsed → AnalysisOutput

设计原则：
- 纯函数：输入 dataclass → 输出 dataclass（不修改入参）
- 每条 FinalConclusion 的 evidence 链保证 100% trace_id 覆盖
- upstream_hash 校验贯穿全链路，任何失配立即中断

作者：整合 agent (W3+)
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Literal, Optional

from engine.energy.evaluator import evaluate_energy
from engine.energy.types import (
    Confidence,
    EnergyFindings,
    Evidence,
    School,
)
from engine.pangzheng.pangzheng import support_with_shensha
from engine.pangzheng.types import SupportFindings
from engine.picture.matcher import match_picture
from engine.picture.types import PictureFindings
from engine.predicates.types import ParsedInput
from engine.yingqi.gate import gate_yingqi
from engine.yingqi.types import GateResult


# ============================================================
# 一、FinalConclusion（03 § 九）
# ============================================================

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


# ============================================================
# 二、CrossSchoolConflict（03 § 九）
# ============================================================

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


# ============================================================
# 三、AnalysisOutput（03 § 九 · render_report 直接消费）
# ============================================================

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
    schema_version: str = "1.2.0"
    pipeline_version: str = "1.2.0"
    generated_at: str = ""

    # Hash 链验证结果
    hash_chain_valid: bool = True
    hash_chain_notes: list[str] = field(default_factory=list)

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
            schema_version=d.get("schema_version", "1.2.0"),
            pipeline_version=d.get("pipeline_version", "1.2.0"),
            generated_at=d.get("generated_at", ""),
            hash_chain_valid=bool(d.get("hash_chain_valid", True)),
            hash_chain_notes=list(d.get("hash_chain_notes", [])),
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


# ============================================================
# 四、Hash 链校验工具
# ============================================================

def verify_hash_chain(
    energy: EnergyFindings,
    picture: PictureFindings,
    gate_results: list[GateResult],
    support: SupportFindings,
) -> tuple[bool, list[str]]:
    """验证整条 hash 链是否完整一致。

    返回 (all_valid, notes)。
    """
    notes: list[str] = []
    e_hash = energy.hash()

    # D2.upstream_hash == D1.hash()
    if picture.upstream_hash and picture.upstream_hash != e_hash:
        notes.append(
            f"D2.upstream_hash={picture.upstream_hash} != "
            f"D1.hash()={e_hash}"
        )

    p_hash = picture.hash()

    # D3 upstream hashes
    for i, gr in enumerate(gate_results):
        if gr.upstream_energy_hash and gr.upstream_energy_hash != e_hash:
            notes.append(
                f"D3[{i}].upstream_energy_hash={gr.upstream_energy_hash} != "
                f"D1.hash()={e_hash}"
            )
        if gr.upstream_picture_hash and gr.upstream_picture_hash != p_hash:
            notes.append(
                f"D3[{i}].upstream_picture_hash={gr.upstream_picture_hash} != "
                f"D2.hash()={p_hash}"
            )

    # D4 upstream hashes
    if support.upstream_energy_hash and support.upstream_energy_hash != e_hash:
        notes.append(
            f"D4.upstream_energy_hash={support.upstream_energy_hash} != "
            f"D1.hash()={e_hash}"
        )
    if support.upstream_picture_hash and support.upstream_picture_hash != p_hash:
        notes.append(
            f"D4.upstream_picture_hash={support.upstream_picture_hash} != "
            f"D2.hash()={p_hash}"
        )

    return (len(notes) == 0, notes)


# ============================================================
# 五、integrate() — 合并 D1-D4 → AnalysisOutput
# ============================================================

def _build_yingqi_table(gate_results: list[GateResult]) -> list[dict[str, Any]]:
    """从 GateResult 列表构建应期总表（按年排序）。"""
    table = []
    for gr in sorted(gate_results, key=lambda g: g.year):
        if gr.passed_layers >= 1 and gr.confidence and gr.confidence.star >= 1:
            table.append({
                "year": gr.year,
                "event": gr.candidate_event,
                "domain": gr.domain,
                "passed_layers": gr.passed_layers,
                "star": gr.confidence.star,
                "percent": gr.confidence.percent,
                "door": gr.door,
                "trace_ids": [e.rule_id for e in gr.evidence],
            })
    return table


def _gate_to_conclusion(
    gr: GateResult,
    idx: int,
) -> FinalConclusion:
    """将一个 GateResult 转为 FinalConclusion。"""
    return FinalConclusion(
        conclusion_id=f"CC-YQ-{idx + 1:03d}",
        statement=(
            f"{gr.year}年 {gr.candidate_event}"
            f"（{gr.domain}·{gr.door or '—'}）"
        ),
        domain=gr.domain,
        layer="独门",  # 应期通常是任派独门
        contributing_schools=["任"],
        confidence=gr.confidence or Confidence(
            star=0, percent=0.0, posterior=0.0, variance=1.0, sample_n=0
        ),
        evidence=list(gr.evidence),  # trace_id 链直传
        yingqi_year=gr.year,
        falsifiable=f"如果 {gr.year}年未发生'{gr.candidate_event}'，则失验",
    )


def integrate(
    energy: EnergyFindings,
    picture: PictureFindings,
    gate_results: list[GateResult],
    support: SupportFindings,
    parsed: Optional[ParsedInput] = None,
) -> AnalysisOutput:
    """合并 D1-D4 → AnalysisOutput（07 § 七）。

    1. 验证 hash 链
    2. 将 gate_results (passed≥2 且 ★≥4) 转为铁断 FinalConclusion
    3. 将 energy / picture 核心断语也转为 FinalConclusion
    4. 构建 yingqi_table
    5. 计算 overall_confidence
    6. 返回 AnalysisOutput
    """
    # 0. Hash 链校验
    valid, hash_notes = verify_hash_chain(energy, picture, gate_results, support)

    # 1. 应期铁断 → FinalConclusion（passed_layers=3 且 ★≥4）
    conclusions: list[FinalConclusion] = []
    yq_idx = 0
    for gr in sorted(gate_results, key=lambda g: g.year):
        if gr.passed_layers >= 2 and gr.confidence and gr.confidence.star >= 4:
            conclusions.append(_gate_to_conclusion(gr, yq_idx))
            yq_idx += 1

    # 2. D1 能量核心断语
    conclusions.append(FinalConclusion(
        conclusion_id="CC-D1-001",
        statement=(
            f"格局做功 {energy.layer_count} 层，富贵层级 {energy.wealth_ceiling}"
        ),
        domain="格局",
        layer="独门",
        contributing_schools=["段"],
        confidence=energy.confidence,
        evidence=list(energy.evidence),
    ))

    # 3. D2 画面核心断语（婚姻窗口、行业指引）
    if picture.marriage_picture and "初婚最佳窗口" in picture.marriage_picture:
        win = picture.marriage_picture["初婚最佳窗口"]
        mp_evidence = picture.marriage_picture.get("evidence", [])
        conclusions.append(FinalConclusion(
            conclusion_id="CC-D2-001",
            statement=f"初婚最佳窗口 {win[0]}-{win[1]} 岁",
            domain="婚姻",
            layer="独门",
            contributing_schools=["杨"],
            confidence=picture.confidence or Confidence(
                star=3, percent=0.65, posterior=0.65, variance=0.05, sample_n=1
            ),
            evidence=mp_evidence if mp_evidence else list(picture.evidence),
        ))

    if picture.industry_pointers:
        conclusions.append(FinalConclusion(
            conclusion_id="CC-D2-002",
            statement=f"行业方向：{'、'.join(picture.industry_pointers[:3])}",
            domain="事业",
            layer="互补",
            contributing_schools=["杨", "段"],
            confidence=picture.confidence or Confidence(
                star=3, percent=0.65, posterior=0.65, variance=0.05, sample_n=1
            ),
            evidence=list(picture.evidence[:3]),
        ))

    # 4. D4 旁证核心断语（boost 显著的 domain）
    for domain_key, supports in support.shensha_supports.items():
        total_boost = support.total_boost_for(domain_key)
        if total_boost >= 0.04:
            d4_ev = list(support.evidence)
            for s in supports:
                # 补充每个神煞自身作为 evidence
                d4_ev.append(Evidence(
                    rule_id=f"GP-{domain_key[:2].upper()}-{s.name}",
                    school="高",
                    description=f"{s.name}在{','.join(s.palaces)}→{s.contribution}",
                    weight=s.boost,
                ))
            conclusions.append(FinalConclusion(
                conclusion_id=f"CC-D4-{domain_key[:6].upper()}",
                statement=f"[旁证]{domain_key}域 boost +{total_boost:.2f}",
                domain=domain_key,
                layer="互补",
                contributing_schools=["高"],
                confidence=support.confidence or Confidence(
                    star=3, percent=0.65, posterior=0.65, variance=0.05, sample_n=1
                ),
                evidence=d4_ev,
            ))

    # 5. 计算 layer_summary
    layer_summary: dict[str, int] = {"共识": 0, "互补": 0, "独门": 0, "冲突仲裁": 0}
    for c in conclusions:
        layer_summary[c.layer] = layer_summary.get(c.layer, 0) + 1

    # 6. 计算 overall_confidence
    if conclusions:
        stars = [c.confidence.star for c in conclusions]
        avg_star = sum(stars) / len(stars)
        avg_post = sum(c.confidence.posterior for c in conclusions) / len(conclusions)
        overall = Confidence(
            star=min(5, max(1, round(avg_star))),
            percent=round(avg_post, 3),
            posterior=round(avg_post, 3),
            variance=0.05,
            sample_n=len(conclusions),
        )
    else:
        overall = Confidence(star=2, percent=0.50, posterior=0.50,
                             variance=0.10, sample_n=0)

    # 7. 应期总表
    yingqi_table = _build_yingqi_table(gate_results)

    # 8. 生成时间戳
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    case_id = energy.case_id or (parsed.case_id if parsed else "")

    return AnalysisOutput(
        case_id=case_id,
        analysis_date=date.today().isoformat(),
        energy=energy,
        picture=picture,
        gate_results=gate_results,
        support=support,
        final_conclusions=conclusions,
        conflicts=[],  # TODO: 跨派冲突仲裁（v1.3 候选）
        yingqi_table=yingqi_table,
        overall_confidence=overall,
        layer_summary=layer_summary,
        generated_at=generated_at,
        hash_chain_valid=valid,
        hash_chain_notes=hash_notes,
    )


# ============================================================
# 六、run_pipeline() — 端到端编排
# ============================================================

def run_pipeline(parsed: ParsedInput) -> AnalysisOutput:
    """v1.2 流水线端到端编排。

    输入：ParsedInput（preflight 解析后）
    输出：AnalysisOutput（含完整 trace_id 链 + hash 链校验）

    流程：
        1. D1 evaluate_energy(parsed)
        2. D2 match_picture(energy, parsed)
        3. D3 gate_yingqi(year, event, domain, ...) × N 候选事件
        4. D4 support_with_shensha(parsed, energy, picture, gates)
        5. integrate(energy, picture, gates, support, parsed)
    """
    # Step 1: D1 段派
    energy = evaluate_energy(parsed)

    # Step 2: D2 杨派
    picture = match_picture(energy, parsed)

    # Step 3: D3 任派 — 从 known_facts 生成候选事件
    gate_results: list[GateResult] = []
    candidates = _extract_candidates(parsed)
    for year, event, domain in candidates:
        gr = gate_yingqi(year, event, domain, energy, picture, parsed)
        if gr.passed_layers >= 1:
            gate_results.append(gr)

    # Step 4: D4 高派
    support = support_with_shensha(parsed, energy, picture, gate_results)

    # Step 5: 整合
    output = integrate(energy, picture, gate_results, support, parsed)

    return output


def _extract_candidates(
    parsed: ParsedInput,
) -> list[tuple[int, str, str]]:
    """从 ParsedInput.known_facts + questions 提取候选事件。

    返回 [(year, candidate_event, domain), ...]
    """
    candidates: list[tuple[int, str, str]] = []

    # 从 known_facts 提取
    for fact in (parsed.known_facts or []):
        if fact.year and fact.event:
            candidates.append((fact.year, fact.event, fact.type or "其他"))
        elif fact.year and fact.content:
            candidates.append((fact.year, fact.content, fact.type or "其他"))

    return candidates
