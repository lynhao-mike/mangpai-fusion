"""engine/pipeline.py · v1.2 流水线整合层

按 03-findings-schema.md § 九 + 07-pipeline-flow.md § 七 实现。

提供：
- FinalConclusion   — 每条最终断语（含完整 trace_id 链 = evidence: list[Evidence]）
- CrossSchoolConflict — 跨派冲突显式登记
- AnalysisOutput    — 完整分析输出（render_report 直接消费）
- integrate()       — 合并 D1-D4 → AnalysisOutput
- run_pipeline()    — W1-W4 + integrate 编排：parsed → AnalysisOutput
- run_pipeline_e2e()— 端到端 8 步编排（preflight → 渲染 → 自迭代），含耗时埋点
- PipelineTiming    — 轻量级耗时记录器（仅依赖 stdlib time）

设计原则：
- 纯函数：输入 dataclass → 输出 dataclass（不修改入参）
- 每条 FinalConclusion 的 evidence 链保证 100% trace_id 覆盖
- upstream_hash 校验贯穿全链路，任何失配立即中断
- 性能监控埋点仅依赖 stdlib (time / logging / warnings)，不引入第三方
  监控框架；端到端 60s 阈值仅做"软护栏"——超阈值发出醒目警告，不阻断主业务落盘

作者：整合 agent (W3+) · v1.2.1 性能监控（DevOps）
"""
from __future__ import annotations

import hashlib
import json
import logging
import sys
import time
import warnings
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Literal, Optional, Union

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
# 〇、性能监控 · PipelineTiming（v1.2.1 DevOps 埋点）
# ============================================================
#
# 设计目标（与 07-pipeline-flow.md § 十三 性能约束对齐）：
#   - 端到端 < 60s（不含 AI polish）
#   - 仅依赖 stdlib：time.perf_counter / logging / warnings
#   - 单一 JSON 制品 cases/C-XXX/findings/timing.json
#   - 超阈值仅发"醒目警告"，不阻断 findings 落盘（软护栏）
#
# 8 个核心步骤命名（与 07-pipeline-flow 各 § 一致）：
#   preflight → energy(W1) → picture(W2) → yingqi(W3)
#   → pangzheng(W4) → integrate → render → self_iter

logger = logging.getLogger(__name__)

#: 端到端总耗时阈值（秒）。超过即触发护栏警告。
PIPELINE_THRESHOLD_SECONDS: float = 60.0

#: 8 个核心步骤的规范名称（顺序即流水线执行顺序）。
PIPELINE_STEP_NAMES: tuple[str, ...] = (
    "preflight",   # 兜底护栏 #1：input.md → ParsedInput
    "energy",      # W1 D1 段派
    "picture",     # W2 D2 杨派
    "yingqi",      # W3 D3 任派
    "pangzheng",   # W4 D4 高派
    "integrate",   # D1-D4 → AnalysisOutput
    "render",      # tools/render_report.render_from_output
    "self_iter",   # tools/feedback_loop.ingest_feedback（自迭代）
)


@dataclass
class StepTiming:
    """单步耗时记录。"""
    name: str
    seconds: float
    started_at: str  # ISO 8601 UTC，含微秒

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "seconds": self.seconds,
            "started_at": self.started_at,
        }


class PipelineTiming:
    """轻量级流水线耗时记录器（仅依赖 stdlib time）。

    用法 1（被 run_pipeline 内部使用）::

        timing = PipelineTiming()
        with timing.step("energy"):
            energy = evaluate_energy(parsed)
        ...
        timing.write_to(findings_dir, case_id=case_id)
        timing.check_threshold()  # 超 60s 时打印 [PERF WARN]

    用法 2（外层 e2e 注入复用，避免双重计时器）::

        timing = PipelineTiming()
        with timing.step("preflight"):
            parsed = preflight.parse(path)
        run_pipeline(parsed, timing=timing, write_findings=False)
        # 所有 8 步累加在同一个 timing 上
    """

    def __init__(self, threshold_seconds: float = PIPELINE_THRESHOLD_SECONDS) -> None:
        self.threshold_seconds: float = float(threshold_seconds)
        self.records: list[StepTiming] = []
        self._created_at: float = time.perf_counter()

    @contextmanager
    def step(self, name: str) -> Iterator["PipelineTiming"]:
        """精准计时一个步骤；异常也会落账（finally 块）。"""
        started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        t0 = time.perf_counter()
        try:
            yield self
        finally:
            dt = time.perf_counter() - t0
            self.records.append(StepTiming(
                name=name,
                seconds=round(dt, 4),
                started_at=started_at,
            ))

    @property
    def total_seconds(self) -> float:
        """所有已记录步骤的耗时之和（秒）。"""
        return round(sum(r.seconds for r in self.records), 4)

    @property
    def exceeded_threshold(self) -> bool:
        return self.total_seconds > self.threshold_seconds

    def steps_map(self) -> dict[str, float]:
        """按步骤名汇总（同名重复出现时累加，例如 yingqi 多次循环计时）。"""
        out: dict[str, float] = {}
        for r in self.records:
            out[r.name] = round(out.get(r.name, 0.0) + r.seconds, 4)
        return out

    def to_dict(self, *, case_id: str = "") -> dict[str, Any]:
        return {
            "case_id": case_id,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "pipeline_version": "1.2.1",
            "threshold_seconds": self.threshold_seconds,
            "total_seconds": self.total_seconds,
            "exceeded_threshold": self.exceeded_threshold,
            "step_names": list(PIPELINE_STEP_NAMES),
            "steps": self.steps_map(),
            "step_details": [r.to_dict() for r in self.records],
        }

    def write_to(
        self,
        findings_dir: Union[str, Path],
        *,
        case_id: str = "",
    ) -> Path:
        """落盘 timing.json 到 findings/ 目录。"""
        findings_dir = Path(findings_dir)
        findings_dir.mkdir(parents=True, exist_ok=True)
        path = findings_dir / "timing.json"
        path.write_text(
            json.dumps(self.to_dict(case_id=case_id), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def check_threshold(self) -> Optional[str]:
        """护栏断言：若总耗时超过阈值，发出醒目警告。

        - 终端：在 stderr 上用 "!!!" 边框打印（命令行肉眼可见）
        - 日志：``logger.warning(...)``
        - Python warning：``warnings.warn(..., RuntimeWarning)``
          （便于 pytest / capsys / -W error 捕获）

        **不抛异常、不阻断主业务**——这是软护栏，仅作可见性提醒。

        Returns:
            超阈值时返回警告文本；未超返回 None。
        """
        if not self.exceeded_threshold:
            return None
        per_step = ", ".join(
            f"{r.name}={r.seconds:.2f}s" for r in self.records
        ) or "<no steps recorded>"
        msg = (
            f"Pipeline total {self.total_seconds:.2f}s exceeded threshold "
            f"{self.threshold_seconds:.2f}s. Per-step: {per_step}"
        )
        bar = "!" * 70
        print(f"\n{bar}", file=sys.stderr)
        print(f"[PERF WARN] {msg}", file=sys.stderr)
        print(f"{bar}\n", file=sys.stderr)
        logger.warning("[PERF WARN] %s", msg)
        warnings.warn(msg, RuntimeWarning, stacklevel=2)
        return msg


# ============================================================
# 〇·下、轻量级 findings 落盘工具
# ============================================================

def _save_findings(
    output: "AnalysisOutput",
    *,
    cases_dir: Optional[Union[str, Path]] = None,
) -> Path:
    """把 D1-D4 + AnalysisOutput 落盘到 cases/C-XXX/findings/。

    与 ``tools/render_report.save_findings`` 等价的轻量副本——独立放在 engine
    层，避免 engine→tools 的分层倒置（pipeline.py 不允许 import tools.*）。

    写入文件：
        - energy.json
        - picture.json
        - gate_results.json
        - support.json
        - analysis_output.json

    Returns:
        findings/ 目录路径。
    """
    if cases_dir is None:
        cases_dir = Path(__file__).resolve().parent.parent / "cases"
    cases_root = Path(cases_dir)

    case_id = (output.case_id or "UNKNOWN").strip() or "UNKNOWN"
    findings_dir = cases_root / case_id / "findings"
    findings_dir.mkdir(parents=True, exist_ok=True)

    def _dump(obj: Any) -> str:
        if obj is None:
            return "null"
        if hasattr(obj, "to_json"):
            return obj.to_json(indent=2)
        if hasattr(obj, "to_dict"):
            return json.dumps(obj.to_dict(), ensure_ascii=False, indent=2)
        if isinstance(obj, list):
            return json.dumps(
                [(x.to_dict() if hasattr(x, "to_dict") else x) for x in obj],
                ensure_ascii=False,
                indent=2,
            )
        return json.dumps(obj, ensure_ascii=False, indent=2)

    (findings_dir / "energy.json").write_text(
        _dump(output.energy), encoding="utf-8")
    (findings_dir / "picture.json").write_text(
        _dump(output.picture), encoding="utf-8")
    (findings_dir / "gate_results.json").write_text(
        _dump(output.gate_results), encoding="utf-8")
    (findings_dir / "support.json").write_text(
        _dump(output.support), encoding="utf-8")
    (findings_dir / "analysis_output.json").write_text(
        _dump(output), encoding="utf-8")

    return findings_dir


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
    schema_version: str = "1.2.0"
    pipeline_version: str = "1.2.0"
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
            schema_version=d.get("schema_version", "1.2.0"),
            pipeline_version=d.get("pipeline_version", "1.2.0"),
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
# 六、run_pipeline() — W1-W4 + integrate 编排
# ============================================================

def run_pipeline(
    parsed: ParsedInput,
    *,
    cases_dir: Optional[Union[str, Path]] = None,
    write_findings: bool = True,
    timing: Optional[PipelineTiming] = None,
    threshold_seconds: float = PIPELINE_THRESHOLD_SECONDS,
) -> AnalysisOutput:
    """v1.2 流水线编排：parsed → AnalysisOutput（W1-W4 + integrate）。

    输入：ParsedInput（preflight 解析后）
    输出：AnalysisOutput（含完整 trace_id 链 + hash 链校验 + ``timing`` 属性）

    流程（每步前后均含耗时埋点）：
        Step 2 [energy]    evaluate_energy(parsed)
        Step 3 [picture]   match_picture(energy, parsed)
        Step 4 [yingqi]    gate_yingqi(...) × N 候选事件
        Step 5 [pangzheng] support_with_shensha(parsed, energy, picture, gates)
        Step 6 [integrate] integrate(...)

    （Step 1 preflight / Step 7 render / Step 8 self_iter 由 ``run_pipeline_e2e``
    负责，本函数仅负责中间 5 步。如外层 ``timing`` 注入则共享同一个计时器。）

    Args:
        parsed:            ParsedInput（preflight 已通过）。
        cases_dir:         cases/ 根目录（None=仓库根 cases/）。
        write_findings:    是否落盘 D1-D4 + analysis_output.json + timing.json。
                           外层 e2e 会在所有 8 步完成后统一落盘，因此 e2e 调用本
                           函数时传 ``False``。
        timing:            外层注入的 PipelineTiming；为 None 时本函数自建一个。
        threshold_seconds: 耗时护栏阈值（秒），仅在自建 timing 时生效。

    Returns:
        AnalysisOutput；附带 ``output.timing`` 引用本次运行的 PipelineTiming。
    """
    own_timing = timing is None
    if timing is None:
        timing = PipelineTiming(threshold_seconds=threshold_seconds)

    # Step 2: D1 段派
    with timing.step("energy"):
        energy = evaluate_energy(parsed)

    # Step 3: D2 杨派
    with timing.step("picture"):
        picture = match_picture(energy, parsed)

    # Step 4: D3 任派 — 从 known_facts 生成候选事件
    with timing.step("yingqi"):
        gate_results: list[GateResult] = []
        candidates = _extract_candidates(parsed)
        for year, event, domain in candidates:
            gr = gate_yingqi(year, event, domain, energy, picture, parsed)
            if gr.passed_layers >= 1:
                gate_results.append(gr)

    # Step 5: D4 高派
    with timing.step("pangzheng"):
        support = support_with_shensha(parsed, energy, picture, gate_results)

    # Step 6: 整合
    with timing.step("integrate"):
        output = integrate(energy, picture, gate_results, support, parsed)

    # F6 · 流年回溯（截止当前年份）—— 不参与 hash 链，独立挂载到 output
    try:
        from datetime import datetime as _dt
        from engine.yingqi.retrospective import scan_retrospective
        retrospective = scan_retrospective(parsed, current_year=_dt.now().year)
        object.__setattr__(output, "retrospective", retrospective)
    except Exception as e:  # noqa: BLE001
        logger.warning("retrospective scan 失败：%s", e)
        object.__setattr__(output, "retrospective", None)

    # 把 timing 引用挂到 output 上（dataclass 非 frozen → 可动态附加）。
    # 注意：to_dict/to_json 仅序列化声明字段，timing 不会泄漏进 JSON 制品。
    object.__setattr__(output, "timing", timing)

    # 落盘 findings + timing.json（e2e 模式下 write_findings=False，由 e2e 兜底）
    if write_findings:
        try:
            findings_dir = _save_findings(output, cases_dir=cases_dir)
            timing.write_to(findings_dir, case_id=output.case_id)
        except Exception as e:  # noqa: BLE001 — 落盘失败不阻断业务
            logger.warning("findings 落盘失败：%s", e)

    # 仅当本函数自建 timing（独立调用）时立即触发护栏；外层 e2e 注入时由 e2e
    # 在 8 步全部完成后统一调用 check_threshold()，避免重复警告 & 中间态误报。
    if own_timing:
        timing.check_threshold()

    return output


# ============================================================
# 七、run_pipeline_e2e() — 端到端 8 步编排（preflight → 自迭代）
# ============================================================

def run_pipeline_e2e(
    input_md_path: Union[str, Path],
    *,
    cases_dir: Optional[Union[str, Path]] = None,
    cases_index_path: Optional[Union[str, Path]] = None,
    do_render: bool = False,
    do_self_iter: bool = False,
    template_name: str = "report-v1.3.md",
    threshold_seconds: float = PIPELINE_THRESHOLD_SECONDS,
) -> tuple[AnalysisOutput, PipelineTiming]:
    """端到端 8 步编排（v1.2.1 性能监控版）。

    8 个步骤每步前后均含 ``time.perf_counter()`` 埋点，最终落盘
    ``cases/C-XXX/findings/timing.json``。总耗时超过 ``threshold_seconds``
    时输出醒目警告（[PERF WARN]），但**不阻断** findings/报告落盘。

    Steps:
        1. preflight   — tools/preflight.parse(input_md_path) → ParsedInput
        2. energy      — D1 段派
        3. picture     — D2 杨派
        4. yingqi      — D3 任派
        5. pangzheng   — D4 高派
        6. integrate   — D1-D4 → AnalysisOutput
        7. render      — tools/render_report.render_from_output（do_render=True 时）
        8. self_iter   — tools/feedback_loop.ingest_feedback（do_self_iter=True 时）

    Args:
        input_md_path:     cases/C-XXX/input.md 路径。
        cases_dir:         cases/ 根目录（None=仓库根 cases/）。
        cases_index_path:  cases-index.md 路径，传给 preflight 做指纹防重。
        do_render:         是否调用 render_report 渲染 Markdown 报告。
        do_self_iter:      是否调用 feedback_loop 自迭代。
        template_name:     渲染模板（默认 report-v1.3.md；report-v1.2.md 仅向下兼容）。
        threshold_seconds: 端到端总耗时阈值（默认 60s）。

    Returns:
        ``(AnalysisOutput, PipelineTiming)``。

    Note:
        Step 1/7/8 任一异常时仅记录耗时 + 日志，不会让上游业务失败——
        这与 contracts/07-pipeline-flow § 十二 错误处理表保持一致。
    """
    timing = PipelineTiming(threshold_seconds=threshold_seconds)

    # Step 1: preflight
    parsed: Optional[ParsedInput] = None
    with timing.step("preflight"):
        # 延迟导入：避免 engine 启动时强依赖 tools/PyYAML
        from tools.preflight import parse as preflight_parse
        from engine.predicates.types import adapt_parsed
        parsed_raw = preflight_parse(
            Path(input_md_path),
            Path(cases_index_path) if cases_index_path else None,
        )
        parsed = adapt_parsed(parsed_raw)

    # Steps 2-6: energy / picture / yingqi / pangzheng / integrate
    # write_findings=False —— 我们在 8 步全部完成后统一落盘
    output = run_pipeline(
        parsed,
        cases_dir=cases_dir,
        write_findings=False,
        timing=timing,
        threshold_seconds=threshold_seconds,
    )

    # Step 7: render（可选）
    if do_render:
        with timing.step("render"):
            try:
                from tools.render_report import render_from_output
                report_md = render_from_output(
                    output,
                    template_name=template_name,
                    cases_dir=cases_dir,
                )
                # 不写入 to_dict 的字段，仅作返回时附带；真正的落盘由 render_report 内部完成
                object.__setattr__(output, "report_md", report_md)
            except Exception as e:  # noqa: BLE001
                logger.warning("render 步骤失败（不阻断）：%s", e)

    # Step 8: 自迭代（可选）
    if do_self_iter:
        with timing.step("self_iter"):
            try:
                from tools.feedback_loop import ingest_feedback
                ingest_feedback(output.case_id)
            except Exception as e:  # noqa: BLE001
                logger.warning("self_iter 步骤失败（不阻断）：%s", e)

    # 统一落盘 findings + timing.json（即便 render/self_iter 失败也照常落）
    try:
        findings_dir = _save_findings(output, cases_dir=cases_dir)
        timing.write_to(findings_dir, case_id=output.case_id)
    except Exception as e:  # noqa: BLE001
        logger.warning("findings 落盘失败：%s", e)

    # 护栏断言：超 60s 仅警告、不阻断
    timing.check_threshold()

    return output, timing


def _extract_candidates(
    parsed: ParsedInput,
) -> list[tuple[int, str, str]]:
    """从 ParsedInput.known_facts + questions 提取候选事件。

    返回 [(year, candidate_event, domain), ...]

    domain 映射表（preflight type → engine domain）：
        职业 → 事业
        学历 → 学业
        其余 保持不变
    """
    # preflight type → engine domain 映射
    _TYPE_TO_DOMAIN: dict[str, str] = {
        "职业": "事业",
        "学历": "学业",
    }

    candidates: list[tuple[int, str, str]] = []

    # 从 known_facts 提取
    for fact in (parsed.known_facts or []):
        raw_type = fact.type or "其他"
        domain = _TYPE_TO_DOMAIN.get(raw_type, raw_type)
        if fact.year and fact.event:
            candidates.append((fact.year, fact.event, domain))
        elif fact.year and fact.content:
            candidates.append((fact.year, fact.content, domain))

    return candidates
