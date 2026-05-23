"""engine.yingqi.types · Track-C 应期门数据结构

按契约 03-findings-schema § 七 GateResult 建模（契约文档尚未交付，
本文件即作为该节的"实现即契约"参考实现）。

核心结构：
- LayerCheck     单层（L1/L2/L3）的判定结果
- TriggerEvent   6 触发之一的判定结果
- Door           12 道门之一的归属
- GateResult     gate_yingqi() 的总输出
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional
import hashlib
import json


# ============================================================
# 一、单层判定结果
# ============================================================


@dataclass
class LayerCheck:
    """L1 / L2 / L3 单层判定。"""

    layer: int                         # 1 / 2 / 3
    passed: bool                       # 是否通过
    score: float = 0.0                 # 0.0 - 1.0 强度
    reasons: list[str] = field(default_factory=list)  # 通过 / 不通过的具体证据
    keys_matched: list[str] = field(default_factory=list)  # 命中的关键字

    def to_dict(self) -> dict:
        return {
            "layer": self.layer,
            "passed": self.passed,
            "score": self.score,
            "reasons": list(self.reasons),
            "keys_matched": list(self.keys_matched),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LayerCheck":
        return cls(**d)


# ============================================================
# 二、6 触发事件
# ============================================================

# 6 触发名（按 m3-mechanics §17）
TRIGGER_TYPES = (
    "本字到",       # 命中字到大运/流年出现
    "伏吟引动",     # 流年伏吟原局某柱
    "合冲引动",     # 命中有合流年逢冲；命中有冲流年逢合；或流年单独触发
    "墓库开闭",     # 财官入墓逢冲刑开库即应
    "藏干透出",     # 藏干通过大运/流年透到天干
    "倒象成立",     # 大运/流年使原局形成倒象（必凶）
)


@dataclass
class TriggerEvent:
    """单个触发事件。"""

    trigger_type: str                  # TRIGGER_TYPES 之一
    triggered: bool                    # 是否触发
    strength: float = 0.0              # 0.0 - 1.0
    target_chars: list[str] = field(default_factory=list)  # 被触发的原局字
    explanation: str = ""              # 人类可读说明
    is_xiong: bool = False             # 是否凶应（倒象铁律）

    def to_dict(self) -> dict:
        return {
            "trigger_type": self.trigger_type,
            "triggered": self.triggered,
            "strength": self.strength,
            "target_chars": list(self.target_chars),
            "explanation": self.explanation,
            "is_xiong": self.is_xiong,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TriggerEvent":
        return cls(**d)


# ============================================================
# 三、12 道门归属
# ============================================================

# 任派十二道门（按 m3-mechanics §16；含动门 / 格局门 / 天地门 / 十天门 / 十二地门 /
# 统领门 / 墓库门 / 夹拱门 / 旬空门 / 鸳鸯门 / 寿元门 / 伤残门 / 牢灾门）
DOOR_TYPES = (
    "动门",
    "格局门",
    "天地门",
    "统领门",
    "墓库门",
    "夹拱门",
    "旬空门",
    "鸳鸯门",
    "寿元门",
    "伤残门",
    "牢灾门",
    "未分类",
)

# Track-C MVP 实现的核心门（fallback 中的 6 个 + 通用兜底）
CORE_DOORS_IMPL = ("动门", "统领门", "墓库门", "鸳鸯门", "寿元门", "牢灾门")


@dataclass
class Door:
    """12 道门归属。"""

    door_type: str                     # DOOR_TYPES 之一
    matched: bool = False
    confidence: float = 0.0
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "door_type": self.door_type,
            "matched": self.matched,
            "confidence": self.confidence,
            "explanation": self.explanation,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Door":
        return cls(**d)


# ============================================================
# 四、GateResult 主输出
# ============================================================


@dataclass
class GateResult:
    """gate_yingqi() 的总输出。

    核心字段：
      - passed_layers ∈ {0, 1, 2, 3}：3 = 铁断 ★★★★★
      - confidence ∈ [0, 1]
      - star ∈ {1..5}
      - is_xiong：是否倒象铁律凶应
    """

    # ----- 基础元数据 -----
    schema_version: str = "0.1"
    year: int = 0
    candidate_event: str = ""           # 例 "结婚" / "升迁" / "高考"
    domain: str = ""                    # 例 "婚姻" / "事业" / "学业"

    # ----- 三层判定 -----
    layer1: Optional[LayerCheck] = None  # 原局
    layer2: Optional[LayerCheck] = None  # 大运
    layer3: Optional[LayerCheck] = None  # 流年
    passed_layers: int = 0              # 通过层数 0-3

    # ----- 6 触发 -----
    triggers: list[TriggerEvent] = field(default_factory=list)
    primary_trigger: Optional[TriggerEvent] = None

    # ----- 12 道门 -----
    door: Optional[Door] = None

    # ----- 上游一致性约束 -----
    energy_consistent: bool = True
    picture_consistent: bool = True
    consistency_reasons: list[str] = field(default_factory=list)

    # ----- 输出 -----
    confidence: float = 0.0             # 0.0 - 1.0
    star: int = 1                       # 1 - 5
    is_xiong: bool = False              # 倒象 → True

    # ----- 追溯 -----
    upstream_energy_hash: str = ""
    upstream_picture_hash: str = ""
    rule_ids: list[str] = field(default_factory=list)

    # ----- 人类可读摘要 -----
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "year": self.year,
            "candidate_event": self.candidate_event,
            "domain": self.domain,
            "layer1": self.layer1.to_dict() if self.layer1 else None,
            "layer2": self.layer2.to_dict() if self.layer2 else None,
            "layer3": self.layer3.to_dict() if self.layer3 else None,
            "passed_layers": self.passed_layers,
            "triggers": [t.to_dict() for t in self.triggers],
            "primary_trigger": self.primary_trigger.to_dict() if self.primary_trigger else None,
            "door": self.door.to_dict() if self.door else None,
            "energy_consistent": self.energy_consistent,
            "picture_consistent": self.picture_consistent,
            "consistency_reasons": list(self.consistency_reasons),
            "confidence": self.confidence,
            "star": self.star,
            "is_xiong": self.is_xiong,
            "upstream_energy_hash": self.upstream_energy_hash,
            "upstream_picture_hash": self.upstream_picture_hash,
            "rule_ids": list(self.rule_ids),
            "summary": self.summary,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GateResult":
        copy = dict(d)
        copy["layer1"] = LayerCheck.from_dict(d["layer1"]) if d.get("layer1") else None
        copy["layer2"] = LayerCheck.from_dict(d["layer2"]) if d.get("layer2") else None
        copy["layer3"] = LayerCheck.from_dict(d["layer3"]) if d.get("layer3") else None
        copy["triggers"] = [TriggerEvent.from_dict(t) for t in d.get("triggers", [])]
        copy["primary_trigger"] = (
            TriggerEvent.from_dict(d["primary_trigger"])
            if d.get("primary_trigger")
            else None
        )
        copy["door"] = Door.from_dict(d["door"]) if d.get("door") else None
        return cls(**copy)

    def hash(self) -> str:
        """稳定哈希（用于自迭代闭环 trace_id 索引）。"""
        s = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
        return hashlib.md5(s.encode("utf-8")).hexdigest()[:16]


# ============================================================
# smoke
# ============================================================


def _smoke() -> None:
    l1 = LayerCheck(layer=1, passed=True, score=0.9, reasons=["原局有财"], keys_matched=["丙"])
    l2 = LayerCheck(layer=2, passed=True, score=0.8, reasons=["大运辰合子"], keys_matched=["辰"])
    l3 = LayerCheck(layer=3, passed=True, score=0.85, reasons=["乙酉合大运"], keys_matched=["乙", "酉"])
    t = TriggerEvent(trigger_type="合冲引动", triggered=True, strength=0.9,
                     target_chars=["子"], explanation="辰酉合 + 乙庚合")
    d = Door(door_type="鸳鸯门", matched=True, confidence=0.85, explanation="妻宫合身")

    gr = GateResult(
        year=2005, candidate_event="结婚", domain="婚姻",
        layer1=l1, layer2=l2, layer3=l3, passed_layers=3,
        triggers=[t], primary_trigger=t, door=d,
        energy_consistent=True, picture_consistent=True,
        confidence=0.92, star=5,
    )
    dd = gr.to_dict()
    gr2 = GateResult.from_dict(dd)
    assert gr2.passed_layers == 3
    assert gr2.layer3 is not None and gr2.layer3.passed is True
    assert gr2.primary_trigger is not None and gr2.primary_trigger.trigger_type == "合冲引动"
    h = gr.hash()
    assert isinstance(h, str) and len(h) == 16

    print("yingqi.types smoke OK")


if __name__ == "__main__":
    _smoke()
