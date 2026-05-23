"""engine/picture/types.py · v1.2 D2 杨派 · PictureFindings 数据结构

严格按 03-findings-schema.md § 六 实现 PictureFindings + 子结构。
含 to_dict / from_dict / to_json / from_json + hash 方法
（参考 Track-A engine/energy/types.py 的实现风格）。

作者：Track-B
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

# 复用 Track-A 已实现的共用类型（避免重复定义）
from engine.energy.types import (  # noqa: F401
    Confidence,
    Evidence,
    Magnitude,
    OrdinalLevel,
    School,
)
from engine.predicates.types import (
    Bazi,
    Gan,
    GanZhi,
    Shishen,
    Wuxing,
    Zhi,
)


# ============================================================
# 一、五步算命法（M2-Y-119）
# ============================================================

WubuStepName = Literal[
    "家里找财官",       # Step 1
    "出处",             # Step 2
    "取法",             # Step 3
    "皇粮民营",         # Step 4
    "天地一气",         # Step 5
]


@dataclass
class WubuStep:
    """五步算命法的单步结果。"""
    step: int                            # 1-5
    name: WubuStepName
    finding: str                         # 该步的核心判断结果
    evidence: list[Evidence] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "name": self.name,
            "finding": self.finding,
            "evidence": [e.to_dict() for e in self.evidence],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "WubuStep":
        return cls(
            step=int(d["step"]),
            name=d["name"],
            finding=d["finding"],
            evidence=[Evidence.from_dict(x) for x in d.get("evidence", [])],
        )


# ============================================================
# 二、天干五合（M2-Y-024..028）
# ============================================================

WuheState = Literal["化成", "合绊", "搅局"]
PalaceShortName = Literal["年柱", "月柱", "日柱", "时柱"]


@dataclass
class WuheRelation:
    """天干五合关系。"""
    pair: tuple[str, str]                # (gan_a, gan_b)
    化神: Wuxing
    state: WuheState
    palaces: tuple[str, str]             # 两干所在柱
    应事: Optional[str] = None           # 应事表映射（M2-Y-027）
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "pair": list(self.pair),
            "化神": self.化神,
            "state": self.state,
            "palaces": list(self.palaces),
            "应事": self.应事,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "WuheRelation":
        return cls(
            pair=(d["pair"][0], d["pair"][1]),
            化神=d["化神"],
            state=d["state"],
            palaces=(d["palaces"][0], d["palaces"][1]),
            应事=d.get("应事"),
            rationale=d.get("rationale", ""),
        )


# ============================================================
# 三、十神暗引（M2-Y-029）
# ============================================================

AnyinFormula = Literal[
    "1旺不受伤",     # 食伤旺不受伤 → 暗引比劫
    "2受制为用",     # 食伤制杀 / 比劫去财
    "3得令通根",     # 印生比劫
    "4印护身",       # 印化杀
    "5官印相生",     # 杀印一体
]


@dataclass
class AnyinResult:
    """十神暗引（5 公式之一）。"""
    formula: AnyinFormula
    triggered_shishen: str               # 暗引出来的十神（Shishen）
    real_meaning: str                    # 真实背景含义（如"印护身=家有靠山"）
    evidence: list[Evidence] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "formula": self.formula,
            "triggered_shishen": self.triggered_shishen,
            "real_meaning": self.real_meaning,
            "evidence": [e.to_dict() for e in self.evidence],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "AnyinResult":
        return cls(
            formula=d["formula"],
            triggered_shishen=d["triggered_shishen"],
            real_meaning=d["real_meaning"],
            evidence=[Evidence.from_dict(x) for x in d.get("evidence", [])],
        )


# ============================================================
# 四、财富 7 等（M2-Y-035）
# ============================================================

CaifuType = Literal[
    "官杀库", "食伤库", "旺杀", "财库", "旺官", "食伤当财", "纯财",
]


@dataclass
class CaifuRanking:
    """财富 7 等排序结果。"""
    rank: int                            # 1-7（1=官杀库，7=纯财）
    type: CaifuType
    rationale: str                       # 一句话说明
    evidence: list[Evidence] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "type": self.type,
            "rationale": self.rationale,
            "evidence": [e.to_dict() for e in self.evidence],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CaifuRanking":
        return cls(
            rank=int(d["rank"]),
            type=d["type"],
            rationale=d["rationale"],
            evidence=[Evidence.from_dict(x) for x in d.get("evidence", [])],
        )


# ============================================================
# 五、官命 9 取（M2-Y-042）
# ============================================================

GuanmingType = Literal[
    "化杀生枭",       # 1 最大
    "化官生印",       # 2
    "合完整官",       # 3
    "财生官+合官",     # 4
    "食神制杀",       # 5
    "比劫生食伤制杀",  # 6
    "劫财制财",        # 7
    "伤官伤尽",        # 8
    "制印得权",        # 9 最小
]


@dataclass
class GuanmingQufa:
    """官命 9 种取法层次。"""
    rank: int                            # 1-9（1=最大，9=最小）
    type: GuanmingType
    rationale: str
    evidence: list[Evidence] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "type": self.type,
            "rationale": self.rationale,
            "evidence": [e.to_dict() for e in self.evidence],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "GuanmingQufa":
        return cls(
            rank=int(d["rank"]),
            type=d["type"],
            rationale=d["rationale"],
            evidence=[Evidence.from_dict(x) for x in d.get("evidence", [])],
        )


# ============================================================
# 六、PictureFindings 主体
# ============================================================

# 行业方向（杨派活死五行 → 行业映射）
IndustryHint = str  # "公门/国企" / "服务/公共" / "技术/制造" / ...

HuosiState = Literal[
    "活", "死", "活木", "死木", "活金", "寒金", "活水", "死水",
]


@dataclass
class PictureFindings:
    """D2 杨派输出 · 细节画面。

    严格按 03-findings-schema.md § 六 + Track-B handoff 要求实现。
    """

    # ========== 五步法（必跑 5 步）==========
    wubu_steps: list[WubuStep] = field(default_factory=list)

    # ========== 天干五合 ==========
    wuhe_relations: list[WuheRelation] = field(default_factory=list)

    # ========== 十神暗引 ==========
    anyin_results: list[AnyinResult] = field(default_factory=list)

    # ========== 财富 / 官命 ==========
    caifu: Optional[CaifuRanking] = None
    guanming: Optional[GuanmingQufa] = None

    # ========== 活死五行 + 行业定位 ==========
    huosi_wuxing: dict[str, str] = field(default_factory=dict)
    industry_pointers: list[IndustryHint] = field(default_factory=list)

    # ========== 婚姻画像（杨派强项 · 修复 G2 关键）==========
    # 子字段（dict 形式，避免过度结构化）：
    #   "初婚最佳窗口": tuple[int, int]   # (lo, hi) 年龄
    #   "配偶画像": str                   # 描述配偶背景特征
    #   "婚姻稳定度": str                 # 稳定 / 中等 / 易动
    #   "早婚信号": Literal["强","中","弱"]
    #   "晚婚信号": Literal["强","中","弱"]
    #   "evidence": list[Evidence]
    marriage_picture: Optional[dict] = None

    # ========== 调候改运（6 维）==========
    # 子字段：
    #   "颜色": list[str] / "方位": str / "数字": list[int]
    #   "文化": str / "食物": list[str] / "贵人": str
    tiaohou_advice: Optional[dict] = None

    # ========== 上游约束验证 ==========
    energy_consistent: bool = True
    energy_violations: list[str] = field(default_factory=list)

    # ========== 元信息 ==========
    confidence: Optional[Confidence] = None
    evidence: list[Evidence] = field(default_factory=list)
    school: str = "杨"
    schema_version: str = "1.2.0"
    upstream_hash: str = ""              # EnergyFindings 的 hash
    case_id: str = ""

    debug_info: dict[str, Any] = field(default_factory=dict)

    # ============================================================
    # 序列化
    # ============================================================

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "school": self.school,
            "case_id": self.case_id,
            "upstream_hash": self.upstream_hash,
            "wubu_steps": [s.to_dict() for s in self.wubu_steps],
            "wuhe_relations": [r.to_dict() for r in self.wuhe_relations],
            "anyin_results": [a.to_dict() for a in self.anyin_results],
            "caifu": self.caifu.to_dict() if self.caifu else None,
            "guanming": self.guanming.to_dict() if self.guanming else None,
            "huosi_wuxing": dict(self.huosi_wuxing),
            "industry_pointers": list(self.industry_pointers),
            "marriage_picture": _marriage_to_dict(self.marriage_picture),
            "tiaohou_advice": dict(self.tiaohou_advice) if self.tiaohou_advice else None,
            "energy_consistent": self.energy_consistent,
            "energy_violations": list(self.energy_violations),
            "confidence": self.confidence.to_dict() if self.confidence else None,
            "evidence": [e.to_dict() for e in self.evidence],
            "debug_info": dict(self.debug_info),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "PictureFindings":
        return cls(
            wubu_steps=[WubuStep.from_dict(x) for x in d.get("wubu_steps", [])],
            wuhe_relations=[WuheRelation.from_dict(x) for x in d.get("wuhe_relations", [])],
            anyin_results=[AnyinResult.from_dict(x) for x in d.get("anyin_results", [])],
            caifu=CaifuRanking.from_dict(d["caifu"]) if d.get("caifu") else None,
            guanming=GuanmingQufa.from_dict(d["guanming"]) if d.get("guanming") else None,
            huosi_wuxing=dict(d.get("huosi_wuxing", {})),
            industry_pointers=list(d.get("industry_pointers", [])),
            marriage_picture=_marriage_from_dict(d.get("marriage_picture")),
            tiaohou_advice=dict(d["tiaohou_advice"]) if d.get("tiaohou_advice") else None,
            energy_consistent=bool(d.get("energy_consistent", True)),
            energy_violations=list(d.get("energy_violations", [])),
            confidence=Confidence.from_dict(d["confidence"]) if d.get("confidence") else None,
            evidence=[Evidence.from_dict(x) for x in d.get("evidence", [])],
            school=d.get("school", "杨"),
            schema_version=d.get("schema_version", "1.2.0"),
            upstream_hash=str(d.get("upstream_hash", "")),
            case_id=str(d.get("case_id", "")),
            debug_info=dict(d.get("debug_info", {})),
        )

    def to_json(self, *, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, s: str) -> "PictureFindings":
        return cls.from_dict(json.loads(s))

    def hash(self) -> str:
        """SHA-256 hash 前 16 位（用于 D3 upstream_picture_hash 校验）。"""
        canonical = json.dumps(
            self.to_dict(), ensure_ascii=False, sort_keys=True
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


# ============================================================
# 内部：marriage_picture / tiaohou_advice 序列化辅助
# ============================================================

def _marriage_to_dict(m: Optional[dict]) -> Optional[dict]:
    """marriage_picture → dict（处理 tuple/Evidence）。"""
    if m is None:
        return None
    out: dict[str, Any] = {}
    for k, v in m.items():
        if k == "初婚最佳窗口" and isinstance(v, (tuple, list)) and len(v) == 2:
            out[k] = [int(v[0]), int(v[1])]
        elif k == "evidence":
            out[k] = [
                e.to_dict() if isinstance(e, Evidence) else e
                for e in (v or [])
            ]
        else:
            out[k] = v
    return out


def _marriage_from_dict(d: Optional[dict]) -> Optional[dict]:
    """dict → marriage_picture（恢复 tuple/Evidence）。"""
    if d is None:
        return None
    out: dict[str, Any] = {}
    for k, v in d.items():
        if k == "初婚最佳窗口" and isinstance(v, (list, tuple)) and len(v) == 2:
            out[k] = (int(v[0]), int(v[1]))
        elif k == "evidence":
            out[k] = [
                Evidence.from_dict(e) if isinstance(e, dict) else e
                for e in (v or [])
            ]
        else:
            out[k] = v
    return out


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    """构造一个最小 PictureFindings 并 round-trip。"""
    f = PictureFindings(
        wubu_steps=[
            WubuStep(step=1, name="家里找财官", finding="日时家里有偏财（寅藏丙）",
                     evidence=[Evidence(rule_id="M2-Y-119", school="杨",
                                        description="第1步家里找财官", weight=0.7)]),
            WubuStep(step=2, name="出处", finding="月支寅出偏财", evidence=[]),
            WubuStep(step=3, name="取法", finding="用印取财官（白领）", evidence=[]),
            WubuStep(step=4, name="皇粮民营", finding="天干透印=吃皇粮候选", evidence=[]),
            WubuStep(step=5, name="天地一气", finding="天干印+地支水印 = 天地一气", evidence=[]),
        ],
        wuhe_relations=[],
        anyin_results=[],
        caifu=CaifuRanking(rank=4, type="财库", rationale="辰水库藏癸+丑藏己"),
        guanming=GuanmingQufa(rank=4, type="财生官+合官", rationale="戊七杀+财生官"),
        huosi_wuxing={"水": "活水", "木": "活木"},
        industry_pointers=["公门/国企"],
        marriage_picture={
            "初婚最佳窗口": (22, 28),
            "配偶画像": "贴身偏财（寅藏丙）= 性情温和、家境中等",
            "婚姻稳定度": "中等",
            "早婚信号": "强",
            "晚婚信号": "弱",
            "evidence": [
                Evidence(rule_id="M2-Y-141", school="杨",
                         description="结婚应期完整版", weight=0.8),
            ],
        },
        tiaohou_advice={"颜色": ["蓝", "绿"], "方位": "南"},
        energy_consistent=True,
        confidence=Confidence(star=4, percent=0.78, posterior=0.78,
                              variance=0.04, sample_n=3),
        evidence=[Evidence(rule_id="M2-Y-119", school="杨",
                           description="五步法落地", weight=0.7)],
        case_id="C-2026-001-test",
        upstream_hash="abc1234567890abc",
    )
    s = f.to_json()
    f2 = PictureFindings.from_json(s)
    assert f.to_dict() == f2.to_dict()
    h = f.hash()
    assert len(h) == 16
    # 关键：marriage_picture.初婚最佳窗口 round-trip 后仍是 tuple
    assert f2.marriage_picture is not None
    win = f2.marriage_picture["初婚最佳窗口"]
    assert isinstance(win, tuple) and win == (22, 28)
    print(f"[OK] PictureFindings round-trip pass · hash={h}")
    print(f"     marriage_picture.初婚最佳窗口 = {win}")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
