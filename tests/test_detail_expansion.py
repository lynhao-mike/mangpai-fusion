from __future__ import annotations

from engine.detail_expansion import build_detail_expansions


class _Confidence:
    def __init__(self, percent: int, sample_n: int = 0) -> None:
        self.percent = percent
        self.sample_n = sample_n


class _Evidence:
    def __init__(self, rule_id: str, school: str = "段") -> None:
        self.rule_id = rule_id
        self.school = school
        self.description = rule_id


class _Energy:
    def __init__(self, *, rich: bool, percent: int = 50, sample_n: int = 0) -> None:
        self.confidence = _Confidence(percent, sample_n)
        self.wealth_ceiling = "L4" if rich else None
        self.layer_count = 4 if rich else 0
        self.evidence = [_Evidence(f"D-{i}") for i in range(3 if rich else 0)]


class _Picture:
    def __init__(self, *, rich: bool, percent: int = 50, sample_n: int = 0) -> None:
        self.confidence = _Confidence(percent, sample_n)
        self.caifu = object() if rich else None
        self.guanming = object() if rich else None
        self.marriage_picture = {"window": [28, 32]} if rich else None
        self.industry_pointers = ["规则平台"] if rich else []
        self.evidence = [_Evidence(f"Y-{i}", "杨") for i in range(3 if rich else 0)]


class _Gate:
    def __init__(self, domain: str, *, passed_layers: int = 3, percent: int = 50, sample_n: int = 0) -> None:
        self.domain = domain
        self.passed_layers = passed_layers
        self.confidence = _Confidence(percent, sample_n)


class _Support:
    def __init__(self, *, rich: bool) -> None:
        self.confidence = _Confidence(50)
        self.shensha_supports = {
            "career": [object(), object()] if rich else [],
            "marriage": [object(), object()] if rich else [],
            "health": [object(), object()] if rich else [],
            "education": [object(), object()] if rich else [],
        }
        self.health_findings = [object(), object()] if rich else []
        self.ciguan_xuetang = object() if rich else None


def test_high_evidence_low_confidence_allows_theory_detail() -> None:
    expansions = build_detail_expansions(
        energy=_Energy(rich=True, percent=50),
        picture=_Picture(rich=True, percent=50),
        gates=[_Gate("事业", passed_layers=3, percent=50)],
        support=_Support(rich=True),
        final_conclusions=[],
        known_facts=None,
    )

    career = expansions["career"]

    assert career.evidence_score.value >= 0.75
    assert career.confidence_score.value <= 0.55
    assert career.allow_theory_detail is True
    assert career.inference_type == "理论推断"
    assert "不等同于已被案例验证" in career.uncertainty
    assert "L2 层级预测" in career.detail_items


def test_low_evidence_keeps_coarse_detail_only() -> None:
    expansions = build_detail_expansions(
        energy=_Energy(rich=False),
        picture=_Picture(rich=False),
        gates=[],
        support=_Support(rich=False),
        final_conclusions=[],
        known_facts=None,
    )

    education = expansions["education"]

    assert education.evidence_score.value < 0.75
    assert education.allow_theory_detail is False
    assert education.level == 0
    assert education.detail_items == ["L0 粗粒度结论"]


def test_high_sample_confidence_is_validation_not_inflated_theory_consensus() -> None:
    expansions = build_detail_expansions(
        energy=_Energy(rich=True, percent=85, sample_n=10),
        picture=_Picture(rich=True, percent=85, sample_n=10),
        gates=[_Gate("婚姻", passed_layers=3, percent=85, sample_n=10)],
        support=_Support(rich=True),
        final_conclusions=[],
        known_facts=["已验证事实", "反馈一致"],
    )

    marriage = expansions["marriage"]

    assert marriage.evidence_score.value >= 0.75
    assert marriage.confidence_score.value > 0.55
    assert marriage.allow_theory_detail is True
    assert marriage.inference_type == "验证推断"
