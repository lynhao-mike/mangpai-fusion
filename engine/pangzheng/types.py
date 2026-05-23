"""engine/pangzheng/types.py · v1.2 D4 高派 SupportFindings 数据结构

严格按 03-findings-schema.md § 八 实现。

复用上游已实现的共用类型：
    Confidence / Evidence / School / Magnitude  ← 来自 engine.energy.types

Track-D 自定义：
    ShenshaSupport / HealthFinding / CiguanXuetang / SupportFindings

含 to_dict / from_dict / to_json / from_json + hash 方法。

作者：Track-D
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

# 复用 Track-A/B/C 已实现的共用类型
from engine.energy.types import (  # noqa: F401
    Confidence,
    Evidence,
    Magnitude,
    School,
)
from engine.predicates.types import PalaceName


# ============================================================
# 一、字面量类型
# ============================================================

# 旁证 boost 所属的领域 key（与 03 § 八 一致）
SupportDomain = Literal["marriage", "career", "wealth", "health", "education", "general"]


# ============================================================
# 二、ShenshaSupport · 单个神煞的旁证
# ============================================================

@dataclass
class ShenshaSupport:
    """单个神煞对某领域结论的补强。"""
    name: str                            # 神煞名（如 "金舆" / "驿马"）
    palaces: list[PalaceName] = field(default_factory=list)  # 挂在哪些柱
    contribution: str = ""               # 对哪条结论补强（人类可读）
    boost: float = 0.0                   # 对置信度的提升 0.0-0.2
    tags: list[str] = field(default_factory=list)  # 取象标签（"奔波/调动" 等）

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "palaces": list(self.palaces),
            "contribution": self.contribution,
            "boost": self.boost,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ShenshaSupport":
        return cls(
            name=d["name"],
            palaces=list(d.get("palaces", [])),
            contribution=d.get("contribution", ""),
            boost=float(d.get("boost", 0.0)),
            tags=list(d.get("tags", [])),
        )


# ============================================================
# 三、HealthFinding · 健康专项
# ============================================================

@dataclass
class HealthFinding:
    """单条健康/灾厄判定（高派强项 GP-CH-08~11）。"""
    organ: str                            # 器官 / 系统（"肝胆" / "下肢" / "寿元" 等）
    risk_level: Magnitude                 # 风险等级
    risk_years: list[int] = field(default_factory=list)  # 高风险年份
    rationale: str = ""                   # 一句话说明
    evidence: list[Evidence] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "organ": self.organ,
            "risk_level": self.risk_level.to_dict(),
            "risk_years": list(self.risk_years),
            "rationale": self.rationale,
            "evidence": [e.to_dict() for e in self.evidence],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "HealthFinding":
        return cls(
            organ=d["organ"],
            risk_level=Magnitude.from_dict(d["risk_level"]),
            risk_years=list(d.get("risk_years", [])),
            rationale=d.get("rationale", ""),
            evidence=[Evidence.from_dict(x) for x in d.get("evidence", [])],
        )


# ============================================================
# 四、CiguanXuetang · 词馆学堂（学历）
# ============================================================

@dataclass
class CiguanXuetang:
    """词馆 / 学堂 / 文昌 旁证（高派学历专门 GP-XL）。"""
    has_ciguan: bool = False              # 是否有词馆
    has_xuetang: bool = False             # 是否有学堂
    has_wenchang: bool = False            # 是否有文昌
    has_taiyi: bool = False               # 是否有天乙贵人（学业辅佐）
    contribution: str = ""                # 对学历层级的补强说明
    boost: float = 0.0                    # 对学业 confidence 的提升 0.0-0.10

    def to_dict(self) -> dict[str, Any]:
        return {
            "has_ciguan": self.has_ciguan,
            "has_xuetang": self.has_xuetang,
            "has_wenchang": self.has_wenchang,
            "has_taiyi": self.has_taiyi,
            "contribution": self.contribution,
            "boost": self.boost,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CiguanXuetang":
        return cls(
            has_ciguan=bool(d.get("has_ciguan", False)),
            has_xuetang=bool(d.get("has_xuetang", False)),
            has_wenchang=bool(d.get("has_wenchang", False)),
            has_taiyi=bool(d.get("has_taiyi", False)),
            contribution=d.get("contribution", ""),
            boost=float(d.get("boost", 0.0)),
        )


# ============================================================
# 五、SupportFindings 主体
# ============================================================

@dataclass
class SupportFindings:
    """D4 高派输出 · 旁证补强（横向）。

    特殊性（03 § 八）：D4 的 boost 只能**增强**已有 D1/D2/D3 结论，
    不能**新提**结论。这是"旁证"二字的本意。
    """

    # ========== 神煞旁证（按领域分组）==========
    shensha_supports: dict[str, list[ShenshaSupport]] = field(default_factory=dict)

    # ========== 健康灾厄专项 ==========
    health_findings: list[HealthFinding] = field(default_factory=list)

    # ========== 词馆学堂（学历）==========
    ciguan_xuetang: Optional[CiguanXuetang] = None

    # ========== 命宫长生诀择日（特殊场景）==========
    mingong_zhairi: Optional[dict] = None

    # ========== 元信息 ==========
    confidence: Optional[Confidence] = None
    evidence: list[Evidence] = field(default_factory=list)
    school: str = "高"
    schema_version: str = "1.2.0"
    case_id: str = ""

    # ========== 上游 hash（追溯）==========
    upstream_energy_hash: str = ""
    upstream_picture_hash: str = ""
    upstream_gate_hash: str = ""

    # ========== 调试 ==========
    debug_info: dict[str, Any] = field(default_factory=dict)

    # ============================================================
    # 序列化
    # ============================================================

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "school": self.school,
            "case_id": self.case_id,
            "shensha_supports": {
                k: [s.to_dict() for s in v]
                for k, v in self.shensha_supports.items()
            },
            "health_findings": [h.to_dict() for h in self.health_findings],
            "ciguan_xuetang": (
                self.ciguan_xuetang.to_dict() if self.ciguan_xuetang else None
            ),
            "mingong_zhairi": dict(self.mingong_zhairi) if self.mingong_zhairi else None,
            "confidence": self.confidence.to_dict() if self.confidence else None,
            "evidence": [e.to_dict() for e in self.evidence],
            "upstream_energy_hash": self.upstream_energy_hash,
            "upstream_picture_hash": self.upstream_picture_hash,
            "upstream_gate_hash": self.upstream_gate_hash,
            "debug_info": dict(self.debug_info),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SupportFindings":
        return cls(
            shensha_supports={
                k: [ShenshaSupport.from_dict(x) for x in v]
                for k, v in (d.get("shensha_supports") or {}).items()
            },
            health_findings=[
                HealthFinding.from_dict(x) for x in (d.get("health_findings") or [])
            ],
            ciguan_xuetang=(
                CiguanXuetang.from_dict(d["ciguan_xuetang"])
                if d.get("ciguan_xuetang") else None
            ),
            mingong_zhairi=(dict(d["mingong_zhairi"]) if d.get("mingong_zhairi") else None),
            confidence=(
                Confidence.from_dict(d["confidence"]) if d.get("confidence") else None
            ),
            evidence=[Evidence.from_dict(x) for x in (d.get("evidence") or [])],
            school=d.get("school", "高"),
            schema_version=d.get("schema_version", "1.2.0"),
            case_id=str(d.get("case_id", "")),
            upstream_energy_hash=str(d.get("upstream_energy_hash", "")),
            upstream_picture_hash=str(d.get("upstream_picture_hash", "")),
            upstream_gate_hash=str(d.get("upstream_gate_hash", "")),
            debug_info=dict(d.get("debug_info", {})),
        )

    def to_json(self, *, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, s: str) -> "SupportFindings":
        return cls.from_dict(json.loads(s))

    def hash(self) -> str:
        """SHA-256 hash 前 16 位。"""
        canonical = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

    # ============================================================
    # 便捷查询
    # ============================================================

    def total_boost_for(self, domain: str) -> float:
        """该 domain 的总 boost（求和，但 cap 在 0.20 防止过冲）。"""
        supports = self.shensha_supports.get(domain, [])
        total = sum(s.boost for s in supports)
        # 词馆学堂额外加成（仅对 education）
        if domain in ("education", "学业") and self.ciguan_xuetang:
            total += self.ciguan_xuetang.boost
        # cap
        return min(total, 0.20)

    def all_shensha_names(self) -> list[str]:
        """所有出现过的神煞名（去重）。"""
        names: set[str] = set()
        for supports in self.shensha_supports.values():
            for s in supports:
                names.add(s.name)
        return sorted(names)


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    """构造一个最小 SupportFindings 并 round-trip。"""
    s_marriage = ShenshaSupport(
        name="金舆",
        palaces=["时柱"],
        contribution="金舆在时柱 → 配偶贵气，婚姻富贵跃升信号",
        boost=0.05,
        tags=["豪车", "配偶贵气"],
    )
    s_career = ShenshaSupport(
        name="驿马",
        palaces=["月柱"],
        contribution="驿马在月柱 → 事业奔波/调动信号",
        boost=0.04,
        tags=["奔波", "调动", "外出"],
    )

    h = HealthFinding(
        organ="寿元",
        risk_level=Magnitude(ordinal="弱", score=0.3),
        risk_years=[2026, 2030],
        rationale="日支子被多重穿合，寿元星受损但有印护",
        evidence=[
            Evidence(rule_id="GP-CH-11", school="高",
                     description="寿元星受伤=短寿信号", weight=0.6),
        ],
    )

    cx = CiguanXuetang(
        has_ciguan=True,
        has_taiyi=True,
        contribution="词馆+天乙×2 → 学业辅佐力量加强",
        boost=0.06,
    )

    support = SupportFindings(
        shensha_supports={
            "marriage": [s_marriage],
            "career": [s_career],
        },
        health_findings=[h],
        ciguan_xuetang=cx,
        confidence=Confidence(
            star=4, percent=0.78, posterior=0.78,
            variance=0.05, sample_n=2,
        ),
        evidence=[
            Evidence(rule_id="GP-BD-01", school="高",
                     description="金舆在时柱补强婚姻", weight=0.5),
        ],
        case_id="C-2026-001-test",
        upstream_energy_hash="abc1234567890abc",
        upstream_picture_hash="def4567890abcdef",
        upstream_gate_hash="123abcdef4567890",
    )

    s = support.to_json()
    support2 = SupportFindings.from_json(s)
    assert support.to_dict() == support2.to_dict()
    assert support.hash() == support2.hash()

    # 便捷查询
    assert abs(support.total_boost_for("marriage") - 0.05) < 1e-9
    assert abs(support.total_boost_for("career") - 0.04) < 1e-9
    # 学业有词馆 boost
    assert abs(support.total_boost_for("education") - 0.06) < 1e-9
    # 不存在的 domain → 0
    assert support.total_boost_for("xxx") == 0.0

    names = support.all_shensha_names()
    assert "金舆" in names and "驿马" in names

    print(f"[OK] SupportFindings round-trip · hash={support.hash()}")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
