"""tests/v1_3_acceptance/conftest.py · v1.3 验收测试共用 fixture。

构造一组 mock 数据：EnergyFindings / PictureFindings / GateResult，
让 H1-H6 测试不依赖完整 engine 流水线即可跑。
"""
from __future__ import annotations

from typing import Any

import pytest


# ============================================================
# Mock dataclass：足够 render_report.py 用
# ============================================================

class _MockConfidence:
    def __init__(self, star: int, percent: int):
        self.star = star
        self.percent = percent


class _MockEvidence:
    def __init__(self, rule_id: str, school: str, description: str = ""):
        self.rule_id = rule_id
        self.school = school
        self.description = description


class _MockMagnitude:
    def __init__(self, ordinal: str, score: float):
        self.ordinal = ordinal
        self.score = score


class _MockTiyong:
    def __init__(self):
        self.body = []
        self.purpose = []
        self.rationale = "mock 体用"


class _MockZuogong:
    def __init__(self, description: str, rule_ids: list[str], star: int = 4, pct: int = 80):
        self.description = description
        self.evidence = [_MockEvidence(rid, "段") for rid in rule_ids]
        self.confidence = _MockConfidence(star, pct)
        self.strength = _MockMagnitude("强", 0.8)
        self.layer_count = 3


class MockEnergy:
    """Mock EnergyFindings — 满足 _build_energy_vm 调用即可。"""
    def __init__(self, case_id: str = "C-2026-099-甲申乙酉丙申乙未"):
        self.case_id = case_id
        self.layer_count = 4
        self.wealth_ceiling = "L4"
        self.energy_level = _MockMagnitude("中上", 0.75)
        self.confidence = _MockConfidence(4, 80)
        self.zuogong_paths = [
            _MockZuogong("财官印齐", ["M1-D-001"], star=4, pct=80),
            _MockZuogong("食伤生财", ["M1-D-007"], star=5, pct=88),
        ]
        self.tiyong = _MockTiyong()
        self.evidence = [
            _MockEvidence("M1-D-001", "段", "财官印齐主公职"),
            _MockEvidence("M2-Y-068", "杨", "婚姻晚而有波折"),
        ]

    def hash(self) -> str:
        return "mockenergy01"


class _MockCaifu:
    def __init__(self):
        self.type = "印格"
        self.rank = 4


class _MockGuanming:
    def __init__(self):
        self.type = "正官格"
        self.rank = 4


class _MockWubuStep:
    def __init__(self, step: int, name: str, finding: str):
        self.step = step
        self.name = name
        self.finding = finding
        self.evidence = []


class MockPicture:
    """Mock PictureFindings — 满足 _build_picture_vm。"""
    def __init__(self):
        self.case_id = "C-2026-099"
        self.confidence = _MockConfidence(4, 82)
        self.caifu = _MockCaifu()
        self.guanming = _MockGuanming()
        self.industry_pointers = ["公职", "文化"]
        self.marriage_picture = {"初婚最佳窗口": [28, 32]}
        self.wubu_steps = [
            _MockWubuStep(1, "看格", "印格成立"),
            _MockWubuStep(2, "看气", "气清"),
        ]
        self.evidence = [
            _MockEvidence("M2-Y-068", "杨", "婚姻晚而有波折"),
            _MockEvidence("M2-Y-099", "杨", "弱项断语-应过滤"),
        ]

    def hash(self) -> str:
        return "mockpicture01"


class _MockLayer:
    def __init__(self, passed: bool):
        self.passed = passed


class _MockTrigger:
    def __init__(self, type_: str, description: str):
        self.type = type_
        self.description = description


class MockGate:
    """Mock GateResult — 满足 _build_gates_vm。"""
    def __init__(self, year: int, candidate_event: str, domain: str,
                 *, passed: int = 3, star: int = 5, pct: int = 90,
                 evidence_chain: list[str] | None = None):
        self.year = year
        self.candidate_event = candidate_event
        self.domain = domain
        self.passed_layers = passed
        self.layer1 = _MockLayer(passed >= 1)
        self.layer2 = _MockLayer(passed >= 2)
        self.layer3 = _MockLayer(passed >= 3)
        self.confidence = _MockConfidence(star, pct)
        self.primary_trigger = _MockTrigger("合化", "卯戌合化火")
        self.door = "正门"
        self.is_xiong = False
        self.evidence = [
            _MockEvidence(rid, "任") for rid in (evidence_chain or ["MR-LAYER3"])
        ]


class _MockBazi:
    年柱 = "甲申"
    月柱 = "乙酉"
    日柱 = "丙申"
    时柱 = "乙未"


class _MockDayunStep:
    def __init__(self, ganzhi: str, start: int, end: int):
        self.干支 = ganzhi
        self.起讫年 = (start, end)


class _MockDayun:
    def __init__(self):
        self.排布 = [
            _MockDayunStep("甲戌", 1989, 1998),
            _MockDayunStep("乙亥", 1999, 2008),
            _MockDayunStep("丙子", 2009, 2018),
            _MockDayunStep("丁丑", 2019, 2028),
        ]


class MockParsed:
    """Mock ParsedInput — 满足 render() 内部所有引用。"""
    def __init__(self, case_id: str = "C-2026-099-甲申乙酉丙申乙未"):
        self.case_id = case_id
        self.bazi = _MockBazi()
        self.dayun = _MockDayun()
        self.birth = {"公历": "1981-09-15", "性别": "男"}


@pytest.fixture
def mock_energy() -> MockEnergy:
    return MockEnergy()


@pytest.fixture
def mock_picture() -> MockPicture:
    return MockPicture()


@pytest.fixture
def mock_gates() -> list[MockGate]:
    return [
        MockGate(2027, "结婚", "婚姻", passed=3, star=5, pct=92,
                 evidence_chain=["MR-LAYER3"]),
        MockGate(2030, "升迁", "事业", passed=3, star=4, pct=85,
                 evidence_chain=["M3-R-031"]),
        MockGate(2025, "弱应期", "财运", passed=2, star=3, pct=60,
                 evidence_chain=["MR-LAYER3"]),
    ]


@pytest.fixture
def mock_parsed() -> MockParsed:
    return MockParsed()
