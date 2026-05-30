"""应用层整合服务：把 D1-D4 findings 合成为 AnalysisOutput。"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional

from engine.domain.analysis import AnalysisOutput, FinalConclusion
from engine.energy.types import Confidence, EnergyFindings, Evidence
from engine.pangzheng.types import SupportFindings
from engine.picture.types import PictureFindings
from engine.predicates.types import ParsedInput
from engine.yingqi.types import GateResult

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

def _infer_industry_path(picture: PictureFindings) -> dict[str, Any]:
    """v1.4 V5：从行业指针推断体制路径概率。

    这是最小可运行实现，用于把 CFL-C015-002 的输出耦合 gate 从文档/lint
    推进到结构化 findings。后续可替换为更精细的 D2 行业路径模型。
    """
    explicit = getattr(picture, "industry_path", None) or {}
    if explicit:
        return dict(explicit)

    pointers = [str(x) for x in getattr(picture, "industry_pointers", []) or []]
    text = " ".join(pointers)
    institutional_keywords = [
        "公门", "国企", "体制", "事业单位", "选调", "公务员",
        "党政", "行政", "机关", "编制", "官印", "公检法",
    ]
    hits = [kw for kw in institutional_keywords if kw in text]
    if len(hits) >= 2:
        p = 0.85
    elif len(hits) == 1:
        p = 0.72
    elif pointers:
        p = 0.20
    else:
        p = 0.0

    if p > 0.7:
        primary = "institutional"
    elif p >= 0.3:
        primary = "dual"
    elif pointers:
        primary = "market"
    else:
        primary = "unknown"

    return {
        "P_institutional": p,
        "primary_path": primary,
        "signals": hits,
        "source": "engine.pipeline._infer_industry_path",
    }

def _infer_wealth_framework(industry_path: dict[str, Any]) -> str:
    """v1.4 V6：按 P(体制内) 切换财富输出框架。"""
    p = float(industry_path.get("P_institutional", 0.0) or 0.0)
    if p > 0.7:
        return "power_hierarchy"
    if p >= 0.3:
        return "dual"
    return "market_wealth"

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

    # 5. v1.4 V5/V6：行业路径与财富框架耦合
    industry_path = _infer_industry_path(picture)
    wealth_framework = _infer_wealth_framework(industry_path)
    picture.industry_path = industry_path
    picture.wealth_level = {
        **getattr(picture, "wealth_level", {}),
        "framework": wealth_framework,
    }
    if industry_path.get("primary_path") in {"institutional", "dual"}:
        p_inst = float(industry_path.get("P_institutional", 0.0) or 0.0)
        conclusions.append(FinalConclusion(
            conclusion_id="CC-D2-003",
            statement=(
                "行业路径耦合："
                f"P(体制内)={p_inst:.2f}，财富域采用 {wealth_framework} 框架"
            ),
            domain="财运",
            layer="互补",
            contributing_schools=["杨", "段"],
            confidence=picture.confidence or Confidence(
                star=3, percent=0.70, posterior=0.70, variance=0.05, sample_n=1
            ),
            evidence=list(picture.evidence[:3]),
            falsifiable="若命主实际长期走纯市场/民营路径，则该耦合框架需降级为 market_wealth",
        ))

    # 6. 计算 layer_summary
    layer_summary: dict[str, int] = {"共识": 0, "互补": 0, "独门": 0, "冲突仲裁": 0}
    for c in conclusions:
        layer_summary[c.layer] = layer_summary.get(c.layer, 0) + 1

    # 7. 计算 overall_confidence
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

    # 8. 应期总表
    yingqi_table = _build_yingqi_table(gate_results)

    # 9. 生成时间戳
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
        conflicts=[],  # 结构化冲突由人工/报告层登记；自动语义仲裁另走独立模型
        yingqi_table=yingqi_table,
        overall_confidence=overall,
        layer_summary=layer_summary,
        schema_version="1.4.0",
        pipeline_version="1.4.0",
        generated_at=generated_at,
        hash_chain_valid=valid,
        hash_chain_notes=hash_notes,
    )
