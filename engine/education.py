"""可工程化学业分析模块。

ponytail: 单文件纯函数模块；先切断“能力直接推出学历”的错链，后续命中率证明需要再接更细模型。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from engine.domain.social_clock import build_education_timeline

SchoolSystem = Literal["ziping", "tiaohou_ditiansui", "blind"]
SignalKind = Literal["ability", "environment", "exam_pressure", "degree_direct", "interference"]
Polarity = Literal["positive", "negative", "mixed"]
EducationMode = Literal["prediction", "calibration"]

METHODOLOGY: dict[SchoolSystem, dict[str, str]] = {
    "ziping": {
        "how": "十神结构：印星看学习承载，食伤看理解表达，官杀看考试制度压力，财星看分心干扰。",
        "say": "印旺身强，多主读书顺利；官印相生，多主高学历；财多坏印，贪玩误学。",
        "boundary": "只能推学习能力/考试适配，不得跳过高考、录取、学校、毕业直接给学历。",
    },
    "tiaohou_ditiansui": {
        "how": "气势调候：看清浊、通关、寒暖燥湿是否支持文明学习环境。",
        "say": "木火通明，多主文章显达；水木清华，聪明好学；清则灵，浊则滞。",
        "boundary": "偏学习环境和认知状态，不直接断学校层级或学历兑现。",
    },
    "blind": {
        "how": "象法旁证：文昌、学堂、词馆、天乙、印星等给学业象。",
        "say": "文昌入命，多主读书有成；天乙临身，学业有人扶持；印旺文昌，此命有学历候选。",
        "boundary": "可作直断候选，但必须降为待反馈，不能绕过考试/学校/毕业锚点。",
    },
}

ANCHOR_KEYS = ("gaokao", "admission", "school", "major", "graduation", "highest_degree")


@dataclass(frozen=True)
class EducationSignal:
    school: SchoolSystem
    kind: SignalKind
    statement: str
    strength: float = 0.5
    polarity: Polarity = "positive"


@dataclass(frozen=True)
class EducationProfile:
    timeline: list[dict[str, Any]]
    ability_score: float
    environment_score: float
    exam_pressure_score: float
    interference_score: float
    degree_verdict: str
    institution_verdict: str
    usable_for_final_degree: bool
    mode: EducationMode
    probability_range: tuple[int, int] | None = None
    calibration_notes: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    methodology: dict[SchoolSystem, dict[str, str]] = field(default_factory=lambda: METHODOLOGY)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timeline": self.timeline,
            "ability_score": self.ability_score,
            "environment_score": self.environment_score,
            "exam_pressure_score": self.exam_pressure_score,
            "interference_score": self.interference_score,
            "degree_verdict": self.degree_verdict,
            "institution_verdict": self.institution_verdict,
            "usable_for_final_degree": self.usable_for_final_degree,
            "mode": self.mode,
            "probability_range": self.probability_range,
            "calibration_notes": list(self.calibration_notes),
            "risks": list(self.risks),
            "methodology": self.methodology,
        }


def analyze_education(
    *,
    birth_year: int,
    signals: list[EducationSignal | dict[str, Any]],
    anchors: dict[str, Any] | None = None,
) -> EducationProfile:
    """双模式学业分析：无反馈=概率预测；有反馈=结构解释与校准。"""
    normalized = [_as_signal(item) for item in signals]
    anchors = anchors or {}
    anchor_count = sum(bool(anchors.get(key)) for key in ANCHOR_KEYS)

    ability = _score(normalized, "ability")
    environment = _score(normalized, "environment")
    exam_pressure = _score(normalized, "exam_pressure")
    interference = _score(normalized, "interference")
    direct_degree = [item for item in normalized if item.kind == "degree_direct"]

    risks: list[str] = []
    if direct_degree and anchor_count < 3:
        risks.append("盲派直断学历信号存在，但缺少高考/录取/学校/毕业锚点，已降级为待反馈候选。")
    if anchor_count < 3:
        risks.append("现实锚点不足：禁止由学习能力直接推出学历或学校层级。")
    if interference >= 0.6:
        risks.append("财星/干扰信号较强：学习能力可能不等于学历兑现。")

    usable = anchor_count >= 3
    mode: EducationMode = "calibration" if usable else "prediction"
    if usable:
        degree = _anchored_degree(anchors)
        institution = _anchored_institution(anchors)
        probability = None
        calibration_notes = _calibration_notes(anchors, ability, environment, exam_pressure, interference)
    else:
        probability = _probability_range(ability, environment, exam_pressure, interference, bool(direct_degree))
        degree = f"概率预测候选：学历兑现概率约 {probability[0]}%–{probability[1]}%，需反馈校准，不能确定学历层级"
        institution = "概率预测候选：学校层级缺录取批次、学校名称或毕业记录，暂不输出"
        calibration_notes = []

    return EducationProfile(
        timeline=build_education_timeline(birth_year),
        ability_score=ability,
        environment_score=environment,
        exam_pressure_score=exam_pressure,
        interference_score=interference,
        degree_verdict=degree,
        institution_verdict=institution,
        usable_for_final_degree=usable,
        mode=mode,
        probability_range=probability,
        calibration_notes=calibration_notes,
        risks=risks,
    )


def _as_signal(item: EducationSignal | dict[str, Any]) -> EducationSignal:
    if isinstance(item, EducationSignal):
        return item
    return EducationSignal(
        school=item.get("school", "blind"),
        kind=item.get("kind", "ability"),
        statement=str(item.get("statement", "")),
        strength=float(item.get("strength", 0.5)),
        polarity=item.get("polarity", "positive"),
    )


def _score(signals: list[EducationSignal], kind: SignalKind) -> float:
    values = [s.strength * (-1 if s.polarity == "negative" else 1) for s in signals if s.kind == kind]
    if not values:
        return 0.0
    return round(max(0.0, min(1.0, sum(values) / len(values))), 3)


def _probability_range(
    ability: float,
    environment: float,
    exam_pressure: float,
    interference: float,
    has_direct_degree_signal: bool,
) -> tuple[int, int]:
    score = 0.35 + ability * 0.25 + environment * 0.15 + exam_pressure * 0.10 - interference * 0.10
    if has_direct_degree_signal:
        score += 0.05
    mid = max(35, min(85, int(round(score * 100))))
    return max(30, mid - 8), min(90, mid + 8)


def _calibration_notes(
    anchors: dict[str, Any],
    ability: float,
    environment: float,
    exam_pressure: float,
    interference: float,
) -> list[str]:
    notes = ["已进入反馈校准模式：现实学历优先于理论信号。"]
    if anchors.get("highest_degree"):
        notes.append(f"最高学历反馈：{anchors['highest_degree']}。")
    if anchors.get("school") or anchors.get("admission"):
        notes.append(f"学校/录取反馈：{_anchored_institution(anchors)}。")
    if ability >= 0.6 and not anchors.get("graduation"):
        notes.append("学习能力信号不弱，但缺毕业年份，学历兑现仍需补证。")
    if interference >= 0.6:
        notes.append("干扰信号较强：若现实学历低于能力信号，优先解释为兑现受阻。")
    if environment < 0.45:
        notes.append("学习环境分偏低：若现实阶段波动，优先从调候/环境压力解释。")
    return notes


def _anchored_degree(anchors: dict[str, Any]) -> str:
    return str(anchors.get("highest_degree") or "学历已具备部分锚点，仍需最高学历反馈校准")


def _anchored_institution(anchors: dict[str, Any]) -> str:
    school = anchors.get("school") or "学校待补"
    admission = anchors.get("admission") or "录取批次待补"
    return f"{school}；{admission}"
