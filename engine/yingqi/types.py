"""engine/yingqi/types.py · v1.2 D3 任派 · GateResult 数据结构

严格按 03-findings-schema.md § 七 实现 GateResult + LayerCheck + TriggerEvent。

复用上游已实现的共用类型：
    Confidence / Evidence / School  ← 来自 engine.energy.types

Track-C 自定义：
    LayerCheck / TriggerEvent / GateResult

含 to_dict / from_dict / to_json / from_json + hash 方法
（参考 Track-A engine/energy/types.py 与 Track-B engine/picture/types.py）。

作者：Track-C
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Literal, Optional, Union

# 复用 Track-A/B 已实现的共用类型
from engine import FINDINGS_SCHEMA_VERSION
from engine.energy.types import (  # noqa: F401
    Confidence,
    Evidence,
    School,
)
from engine.predicates.types import (
    Gan,
    GanZhi,
    PalaceName,
    Zhi,
)


# ============================================================
# 一、字面量类型（与 03-findings-schema § 七 严格一致）
# ============================================================

# 6 触发类型（任派 §17）
TriggerType = Literal[
    "本字到",       # 流年地支 = 原局某关键字
    "伏吟",         # 流年与原局某柱完全相同
    "合冲引动",     # 流年与原局合冲（六合/三合/六冲）
    "墓库开闭",     # 辰戌丑未的开闭
    "藏干透出",     # 流年透出原局某藏干
    "倒象成立",     # 又制又生又合又冲（任派"倒象=必凶"）
]

# 三层 gate 名（layer 字段）
GateLayer = Literal["L1_原局有", "L2_大运到位", "L3_流年引爆"]

# 12 道门（任派 §16）
DoorType = Literal[
    "动门", "格局门", "天地门", "统领门", "墓库门", "夹拱门",
    "旬空门", "鸳鸯门", "寿元门", "伤残门", "牢灾门",
]

# Domain（与 04-gate § 二 一致）
Domain = Literal["婚姻", "事业", "财运", "健康", "学业", "六亲", "其他"]

# 触发优先级（04 § 5.2 高 → 低）
TRIGGER_PRIORITY: dict[str, int] = {
    "倒象成立": 1,   # 凶性优先（最高）
    "伏吟": 2,
    "本字到": 3,    # 与"合冲引动"等价
    "合冲引动": 3,
    "墓库开闭": 4,
    "藏干透出": 5,
}

# ★ 上限（04 § 七）
PASSED_LAYERS_TO_STAR_CEILING: dict[int, int] = {0: 0, 1: 3, 2: 4, 3: 5}


# ============================================================
# 二、LayerCheck（单层 gate 检查结果）
# ============================================================

@dataclass
class LayerCheck:
    """L1 / L2 / L3 单层检查结果。"""
    layer: GateLayer
    passed: bool
    evidence_chars: list[str] = field(default_factory=list)  # gan / zhi 字符
    rationale: str = ""

    # Track-C 内部追加：变体标记（不进契约必填，但供下游 confidence 计算）
    used_transition: bool = False  # L2 是否仅靠过渡期相邻大运通过
    used_secondary_keys: bool = False  # L1 是否退到 secondary 关键字通过

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer,
            "passed": self.passed,
            "evidence_chars": list(self.evidence_chars),
            "rationale": self.rationale,
            "used_transition": self.used_transition,
            "used_secondary_keys": self.used_secondary_keys,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "LayerCheck":
        return cls(
            layer=d["layer"],
            passed=bool(d["passed"]),
            evidence_chars=list(d.get("evidence_chars", [])),
            rationale=d.get("rationale", ""),
            used_transition=bool(d.get("used_transition", False)),
            used_secondary_keys=bool(d.get("used_secondary_keys", False)),
        )


# ============================================================
# 三、TriggerEvent（6 触发之一）
# ============================================================

@dataclass
class TriggerEvent:
    """单个触发事件。"""
    type: TriggerType
    description: str
    target_chars: list[str] = field(default_factory=list)  # 涉及的字
    is_xiong: bool = False  # 倒象成立 → True

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "description": self.description,
            "target_chars": list(self.target_chars),
            "is_xiong": self.is_xiong,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TriggerEvent":
        return cls(
            type=d["type"],
            description=d["description"],
            target_chars=list(d.get("target_chars", [])),
            is_xiong=bool(d.get("is_xiong", False)),
        )


# ============================================================
# 四、GateResult 主体
# ============================================================

@dataclass
class GateResult:
    """单个候选事件的应期判定结果。

    三层 gate + 6 触发 + 12 道门 + 上游一致性 → 最终 confidence。
    """

    # ========== 候选事件描述 ==========
    year: int
    candidate_event: str                 # "结婚" / "升迁" / "母亡" 等
    domain: Domain

    # ========== 三层 gate ==========
    layer1: LayerCheck                   # L1 原局有
    layer2: LayerCheck                   # L2 大运到位
    layer3: LayerCheck                   # L3 流年引爆
    passed_layers: int                   # 0-3，全过=3

    # ========== 6 触发引擎结果 ==========
    triggers: list[TriggerEvent] = field(default_factory=list)
    primary_trigger: Optional[TriggerEvent] = None

    # ========== 12 道门归属 ==========
    door: Optional[DoorType] = None

    # ========== v1.4 V4：事件类型候选列表（CFL-C015-003） ==========
    # 当应期触发器是"财星显象"且命主走体制路径时，应输出多个候选事件类型
    # 例如：["职级升迁", "财源/置业"] 而不是单一的"财源/置业"。
    # 默认为空列表 → 表示采用 candidate_event 单解（向后兼容）。
    event_type_hypotheses: list[str] = field(default_factory=list)

    # ========== 最终置信度 ==========
    confidence: Optional[Confidence] = None

    # ========== 上游约束 ==========
    energy_consistent: bool = True
    picture_consistent: bool = True
    consistency_notes: list[str] = field(default_factory=list)

    # ========== 元信息 ==========
    evidence: list[Evidence] = field(default_factory=list)
    school: str = "任"
    schema_version: str = FINDINGS_SCHEMA_VERSION
    case_id: str = ""

    # ========== 上游 hash（追溯）==========
    upstream_energy_hash: str = ""
    upstream_picture_hash: str = ""

    debug_info: dict[str, Any] = field(default_factory=dict)

    # ============================================================
    # 序列化
    # ============================================================

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "school": self.school,
            "case_id": self.case_id,
            "year": self.year,
            "candidate_event": self.candidate_event,
            "domain": self.domain,
            "layer1": self.layer1.to_dict(),
            "layer2": self.layer2.to_dict(),
            "layer3": self.layer3.to_dict(),
            "passed_layers": self.passed_layers,
            "triggers": [t.to_dict() for t in self.triggers],
            "primary_trigger": (
                self.primary_trigger.to_dict() if self.primary_trigger else None
            ),
            "door": self.door,
            "event_type_hypotheses": list(self.event_type_hypotheses),
            "confidence": self.confidence.to_dict() if self.confidence else None,
            "energy_consistent": self.energy_consistent,
            "picture_consistent": self.picture_consistent,
            "consistency_notes": list(self.consistency_notes),
            "evidence": [e.to_dict() for e in self.evidence],
            "upstream_energy_hash": self.upstream_energy_hash,
            "upstream_picture_hash": self.upstream_picture_hash,
            "debug_info": dict(self.debug_info),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "GateResult":
        return cls(
            year=int(d["year"]),
            candidate_event=d["candidate_event"],
            domain=d["domain"],
            layer1=LayerCheck.from_dict(d["layer1"]),
            layer2=LayerCheck.from_dict(d["layer2"]),
            layer3=LayerCheck.from_dict(d["layer3"]),
            passed_layers=int(d["passed_layers"]),
            triggers=[TriggerEvent.from_dict(t) for t in d.get("triggers", [])],
            primary_trigger=(
                TriggerEvent.from_dict(d["primary_trigger"])
                if d.get("primary_trigger") else None
            ),
            door=d.get("door"),
            event_type_hypotheses=list(d.get("event_type_hypotheses", []) or []),
            confidence=Confidence.from_dict(d["confidence"]) if d.get("confidence") else None,
            energy_consistent=bool(d.get("energy_consistent", True)),
            picture_consistent=bool(d.get("picture_consistent", True)),
            consistency_notes=list(d.get("consistency_notes", [])),
            evidence=[Evidence.from_dict(x) for x in d.get("evidence", [])],
            school=d.get("school", "任"),
            schema_version=d.get("schema_version", FINDINGS_SCHEMA_VERSION),
            case_id=str(d.get("case_id", "")),
            upstream_energy_hash=str(d.get("upstream_energy_hash", "")),
            upstream_picture_hash=str(d.get("upstream_picture_hash", "")),
            debug_info=dict(d.get("debug_info", {})),
        )

    def to_json(self, *, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, s: str) -> "GateResult":
        return cls.from_dict(json.loads(s))

    def hash(self) -> str:
        """SHA-256 hash 前 16 位（用于 trace_id 或下游消费追溯）。"""
        canonical = json.dumps(
            self.to_dict(), ensure_ascii=False, sort_keys=True
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

    # ============================================================
    # 便捷查询
    # ============================================================

    @property
    def is_xiong(self) -> bool:
        """是否凶应（任一触发 is_xiong=True 即为凶）。"""
        return any(t.is_xiong for t in self.triggers)

    @property
    def star(self) -> int:
        """便捷取 ★ 等级（0 表示不输出）。"""
        return self.confidence.star if self.confidence else 0


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    """构造一个最小 GateResult 并 round-trip。"""
    l1 = LayerCheck(
        layer="L1_原局有",
        passed=True,
        evidence_chars=["丙", "子"],
        rationale="原局月支寅藏丙偏财 + 日支子婚宫",
    )
    l2 = LayerCheck(
        layer="L2_大运到位",
        passed=True,
        evidence_chars=["辰"],
        rationale="大运庚辰，辰与日支子半合（化水激活婚宫）",
    )
    l3 = LayerCheck(
        layer="L3_流年引爆",
        passed=True,
        evidence_chars=["乙", "酉"],
        rationale="流年乙酉：乙合年干庚 + 酉合大运辰",
    )

    triggers = [
        TriggerEvent(
            type="合冲引动",
            description="2005 乙酉与年干庚合 + 酉合大运辰",
            target_chars=["庚", "辰"],
            is_xiong=False,
        ),
    ]

    gr = GateResult(
        year=2005,
        candidate_event="结婚",
        domain="婚姻",
        layer1=l1, layer2=l2, layer3=l3,
        passed_layers=3,
        triggers=triggers,
        primary_trigger=triggers[0],
        door="鸳鸯门",
        confidence=Confidence(
            star=5, percent=0.88, posterior=0.88,
            variance=0.04, sample_n=3,
        ),
        energy_consistent=True,
        picture_consistent=True,
        consistency_notes=["picture.marriage_picture[初婚最佳窗口]=22-28 含 25 岁"],
        evidence=[
            Evidence(rule_id="M3-R-018", school="任",
                     description="三层叠加：原局有+大运到+流年引", weight=0.85),
        ],
        case_id="C-2026-001-test",
        upstream_energy_hash="abc1234567890abc",
        upstream_picture_hash="def4567890abcdef",
    )

    s = gr.to_json()
    gr2 = GateResult.from_json(s)
    assert gr.to_dict() == gr2.to_dict()
    assert gr.hash() == gr2.hash()
    assert gr.star == 5
    assert gr.is_xiong is False
    assert gr2.passed_layers == 3
    print(f"[OK] GateResult round-trip · hash={gr.hash()}")
    print(f"     {gr.year}年 {gr.domain} · {gr.candidate_event} → "
          f"passed={gr.passed_layers}/3 ★{gr.star} ({gr.confidence.percent:.0%})")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
