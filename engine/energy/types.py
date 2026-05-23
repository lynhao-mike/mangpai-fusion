"""engine.energy.types · EnergyFindings 数据结构（Track-A 上游存根）

⚠️ Track-A（段派 D1）尚未交付，本类型为 Track-C 必需的最小集。

完整版应按契约 03-findings-schema 定义（尚未写）。
本最小集保证 Track-C 的 gate_yingqi() 能消费上游能量信息，
且 Track-A 完整版可平滑替换（仅新增字段，不破坏现有字段）。

字段语义：
- 各 *_capable 表示原局是否具备该领域的"做功基础"
- 用神_chars / 忌神_chars 是十神类（财/官/印/食伤/比劫）映射到具体字
- energy_level 表示整体能量层级（0=平庸 5=国之栋梁），暂用粗粒度
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EnergyFindings:
    """段派 D1 能量评估结果（Track-A 上游存根 / Track-C 消费）。"""

    # ----- 基础元数据 -----
    bazi_str: str = ""               # 例 "庚申戊寅壬子辛丑"
    schema_version: str = "0.1-stub"

    # ----- 能力概览（Track-C 用来做 L1 / picture 一致性快查）-----
    # 默认 True：在 Track-A 未交付时不阻塞 gate
    marriage_capable: bool = True   # 婚姻可成（有财 / 有妻宫 / 不绝灭）
    career_capable: bool = True     # 事业可成
    wealth_capable: bool = True     # 财运可成
    health_capable: bool = True     # 健康基础在
    education_capable: bool = True  # 学业可成

    # ----- 富贵层级（粗粒度 0-5，对应段派 L0-L5）-----
    energy_level: int = 2           # 默认中等

    # ----- 用神 / 忌神 -----
    # 十神类（财/官/印/食伤/比劫）→ 具体字列表
    yong_shen_chars: list[str] = field(default_factory=list)  # 用神字
    ji_shen_chars: list[str] = field(default_factory=list)    # 忌神字

    # 关键字标签：哪些是支撑某领域的"用神"
    # domain → list of chars （供 keys.py 复合参考）
    domain_yong_shen: dict[str, list[str]] = field(default_factory=dict)
    domain_ji_shen: dict[str, list[str]] = field(default_factory=dict)

    # ----- 可选：体用 / 做功结构 / 神党（Track-A 完整版才填）-----
    ti_strength: Optional[str] = None   # '强' / '中' / '弱'
    yong_strength: Optional[str] = None
    zuogong_count: int = 0              # 做功层数

    # ----- 哈希 / 追溯 -----
    upstream_hash: str = ""

    # ============================================================
    # 序列化
    # ============================================================
    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "bazi_str": self.bazi_str,
            "marriage_capable": self.marriage_capable,
            "career_capable": self.career_capable,
            "wealth_capable": self.wealth_capable,
            "health_capable": self.health_capable,
            "education_capable": self.education_capable,
            "energy_level": self.energy_level,
            "yong_shen_chars": list(self.yong_shen_chars),
            "ji_shen_chars": list(self.ji_shen_chars),
            "domain_yong_shen": {k: list(v) for k, v in self.domain_yong_shen.items()},
            "domain_ji_shen": {k: list(v) for k, v in self.domain_ji_shen.items()},
            "ti_strength": self.ti_strength,
            "yong_strength": self.yong_strength,
            "zuogong_count": self.zuogong_count,
            "upstream_hash": self.upstream_hash,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EnergyFindings":
        return cls(**d)


def _smoke() -> None:
    e = EnergyFindings(
        bazi_str="庚申戊寅壬子辛丑",
        marriage_capable=True,
        domain_yong_shen={"婚姻": ["丙", "丁"]},
    )
    d = e.to_dict()
    e2 = EnergyFindings.from_dict(d)
    assert e2.bazi_str == e.bazi_str
    assert e2.domain_yong_shen["婚姻"] == ["丙", "丁"]
    print("energy.types smoke OK")


if __name__ == "__main__":
    _smoke()
