"""engine/energy/types.py · v1.2 D1 段派 · EnergyFindings 数据结构

严格按 03-findings-schema.md § 五 实现 EnergyFindings + 子结构。
含 to_dict / from_dict / to_json / from_json 序列化方法。

作者：Track-A
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Any, Literal, Optional, Union

from engine.predicates.types import (
    Bazi,
    Gan,
    GanZhi,
    Wuxing,
    Zhi,
)


# ============================================================
# 一、共用基础类型（节选自 03 § 三）
# ============================================================

OrdinalLevel = Literal["无", "弱", "中", "强", "极强"]
School = Literal["段", "杨", "高", "任"]


@dataclass
class Magnitude:
    ordinal: OrdinalLevel
    score: float  # 0.0-1.0

    def to_dict(self) -> dict[str, Any]:
        return {"ordinal": self.ordinal, "score": self.score}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Magnitude":
        return cls(ordinal=d["ordinal"], score=float(d["score"]))


@dataclass
class Confidence:
    star: int                # 1-5
    percent: float           # 0.0-1.0
    posterior: float         # Beta 后验值
    variance: float          # Beta 方差
    sample_n: int            # 累计样本

    def to_dict(self) -> dict[str, Any]:
        return {
            "star": self.star,
            "percent": self.percent,
            "posterior": self.posterior,
            "variance": self.variance,
            "sample_n": self.sample_n,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Confidence":
        return cls(
            star=int(d["star"]),
            percent=float(d["percent"]),
            posterior=float(d["posterior"]),
            variance=float(d["variance"]),
            sample_n=int(d["sample_n"]),
        )


@dataclass
class Evidence:
    rule_id: str
    school: School
    description: str
    weight: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "school": self.school,
            "description": self.description,
            "weight": self.weight,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Evidence":
        return cls(
            rule_id=d["rule_id"],
            school=d["school"],
            description=d["description"],
            weight=float(d["weight"]),
        )


# ============================================================
# 二、做功路径 ZuogongPath
# ============================================================

ZuogongType = Literal["制", "化", "生泄", "合", "墓", "复合"]
TiyongRole = Literal["体", "用", "印", "比劫", "食伤", "财", "官杀", "禄"]


@dataclass
class ZuogongPath:
    """单条做功路径。"""
    type: ZuogongType
    chain: list[str]         # 涉及的字（gan / zhi 字符串）
    description: str
    strength: Magnitude
    layer_count: int         # 该路径对总层数的贡献（0/1）

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "chain": list(self.chain),
            "description": self.description,
            "strength": self.strength.to_dict(),
            "layer_count": self.layer_count,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ZuogongPath":
        return cls(
            type=d["type"],
            chain=list(d["chain"]),
            description=d["description"],
            strength=Magnitude.from_dict(d["strength"]),
            layer_count=int(d["layer_count"]),
        )


# ============================================================
# 三、体用结构 TiyongStructure
# ============================================================

@dataclass
class TiyongItem:
    """体用项（字 + 角色 + 出现位置）。"""
    char: str                # 干 / 支
    role: TiyongRole
    location: str            # "年柱-天干" 等

    def to_dict(self) -> dict[str, Any]:
        return {"char": self.char, "role": self.role, "location": self.location}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TiyongItem":
        return cls(char=d["char"], role=d["role"], location=d["location"])


@dataclass
class TiyongStructure:
    body: list[TiyongItem]       # 体（工具）
    purpose: list[TiyongItem]    # 用（目的）
    rationale: str               # 段派 M1 体用判别理由

    def to_dict(self) -> dict[str, Any]:
        return {
            "body": [b.to_dict() for b in self.body],
            "purpose": [p.to_dict() for p in self.purpose],
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TiyongStructure":
        return cls(
            body=[TiyongItem.from_dict(x) for x in d["body"]],
            purpose=[TiyongItem.from_dict(x) for x in d["purpose"]],
            rationale=d["rationale"],
        )


# ============================================================
# 四、势 + 党 ShiDang
# ============================================================

@dataclass
class ShiDang:
    shi: dict[str, float]                   # 5 行势力比例（key: Wuxing）
    dang: list[tuple[str, str]]             # 党的形态：[(五行/概念, 描述)]
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "shi": dict(self.shi),
            "dang": [list(x) for x in self.dang],
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ShiDang":
        return cls(
            shi={k: float(v) for k, v in d["shi"].items()},
            dang=[(x[0], x[1]) for x in d["dang"]],
            description=d["description"],
        )


# ============================================================
# 五、贼神捕神 ZeishenBushen
# ============================================================

@dataclass
class ZeishenBushen:
    zei_shen: list[str]                     # 贼神
    bu_shen: list[str]                      # 捕神
    triggered_by_dayun: list[int]           # 大运步序号（1-based）
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "zei_shen": list(self.zei_shen),
            "bu_shen": list(self.bu_shen),
            "triggered_by_dayun": list(self.triggered_by_dayun),
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ZeishenBushen":
        return cls(
            zei_shen=list(d.get("zei_shen", [])),
            bu_shen=list(d.get("bu_shen", [])),
            triggered_by_dayun=list(d.get("triggered_by_dayun", [])),
            rationale=d.get("rationale", ""),
        )


# ============================================================
# 六、富贵层级（5 级 × 3 档 = 15 档）
# ============================================================

WealthCeiling = Literal[
    "巨富级·上", "巨富级·中", "巨富级·下",
    "大富级·上", "大富级·中", "大富级·下",
    "中富级·上", "中富级·中", "中富级·下",
    "小富级·上", "小富级·中", "小富级·下",
    "贫困级·上", "贫困级·中", "贫困级·下",
]

MuxingQufa = Literal["禄", "食伤", "比劫", "印"]


# ============================================================
# 七、EnergyFindings 主体
# ============================================================

@dataclass
class EnergyFindings:
    """D1 段派输出 · 能量级别。"""

    # 主结论
    energy_level: Magnitude              # 整体能量级别（5 级）
    layer_count: int                     # 做功总层数 1-4

    # 分项
    zuogong_paths: list[ZuogongPath]
    tiyong: TiyongStructure
    shidang: ShiDang
    zeishen: ZeishenBushen

    # 富贵层级
    wealth_ceiling: WealthCeiling

    # 段派独门
    has_guoheqiaoqiao: bool              # 过河拆桥结构
    muxing_qufa: MuxingQufa              # 母星取法（默认 禄，区别于杨派取印）

    # 元信息
    confidence: Confidence
    evidence: list[Evidence]
    school: School = "段"
    schema_version: str = "1.2.0"
    case_id: str = ""

    # 上游 / 调试
    debug_info: dict[str, Any] = field(default_factory=dict)

    # ---- 序列化 ---------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "school": self.school,
            "case_id": self.case_id,
            "energy_level": self.energy_level.to_dict(),
            "layer_count": self.layer_count,
            "zuogong_paths": [p.to_dict() for p in self.zuogong_paths],
            "tiyong": self.tiyong.to_dict(),
            "shidang": self.shidang.to_dict(),
            "zeishen": self.zeishen.to_dict(),
            "wealth_ceiling": self.wealth_ceiling,
            "has_guoheqiaoqiao": self.has_guoheqiaoqiao,
            "muxing_qufa": self.muxing_qufa,
            "confidence": self.confidence.to_dict(),
            "evidence": [e.to_dict() for e in self.evidence],
            "debug_info": dict(self.debug_info),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EnergyFindings":
        return cls(
            energy_level=Magnitude.from_dict(d["energy_level"]),
            layer_count=int(d["layer_count"]),
            zuogong_paths=[ZuogongPath.from_dict(x) for x in d["zuogong_paths"]],
            tiyong=TiyongStructure.from_dict(d["tiyong"]),
            shidang=ShiDang.from_dict(d["shidang"]),
            zeishen=ZeishenBushen.from_dict(d["zeishen"]),
            wealth_ceiling=d["wealth_ceiling"],
            has_guoheqiaoqiao=bool(d["has_guoheqiaoqiao"]),
            muxing_qufa=d["muxing_qufa"],
            confidence=Confidence.from_dict(d["confidence"]),
            evidence=[Evidence.from_dict(x) for x in d["evidence"]],
            school=d.get("school", "段"),
            schema_version=d.get("schema_version", "1.2.0"),
            case_id=d.get("case_id", ""),
            debug_info=dict(d.get("debug_info", {})),
        )

    def to_json(self, *, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, s: str) -> "EnergyFindings":
        return cls.from_dict(json.loads(s))

    def hash(self) -> str:
        """SHA-256 hash 前 16 位（用于上下游 upstream_hash 校验）。"""
        canonical = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    """构造一个最小 EnergyFindings 并 round-trip。"""
    f = EnergyFindings(
        energy_level=Magnitude(ordinal="中", score=0.55),
        layer_count=2,
        zuogong_paths=[
            ZuogongPath(
                type="制", chain=["申", "寅"], description="寅申冲制月令杀根",
                strength=Magnitude(ordinal="中", score=0.6), layer_count=1,
            )
        ],
        tiyong=TiyongStructure(body=[], purpose=[], rationale="测试"),
        shidang=ShiDang(shi={"水": 0.3, "金": 0.3, "土": 0.2, "木": 0.15, "火": 0.05},
                        dang=[("水金", "印生比劫党")], description="测试"),
        zeishen=ZeishenBushen(zei_shen=[], bu_shen=[], triggered_by_dayun=[]),
        wealth_ceiling="中富级·上",
        has_guoheqiaoqiao=False,
        muxing_qufa="禄",
        confidence=Confidence(star=3, percent=0.65, posterior=0.65, variance=0.04, sample_n=2),
        evidence=[Evidence(rule_id="M1-D-009", school="段",
                           description="制用结构是做功 1 之首", weight=0.4)],
        case_id="C-2026-001-test",
    )
    s = f.to_json()
    f2 = EnergyFindings.from_json(s)
    assert f.to_dict() == f2.to_dict()
    h = f.hash()
    assert len(h) == 16
    print(f"[OK] EnergyFindings round-trip pass · hash={h}")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
