"""engine.picture.types · PictureFindings 数据结构（Track-B 上游存根）

⚠️ Track-B（杨派 D2）尚未交付，本类型为 Track-C 必需的最小集。

完整版应按契约 03-findings-schema 定义（尚未写）。
关键字段是 marriage_picture.best_window —— 修复 G2 婚期偏差 8 年的核心信号源。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MarriagePicture:
    """婚姻画面：杨派 D2 输出的婚姻最佳窗口与画像。"""

    # 初婚最佳窗口（虚岁 / 周岁，含两端）
    best_window: tuple[int, int] = (22, 32)
    # 次佳窗口（如有）
    secondary_window: Optional[tuple[int, int]] = None
    # 婚姻状态预测：'稳定' / '波折' / '不婚'
    expected_status: str = "未知"
    # 配偶画像关键词
    spouse_keywords: list[str] = field(default_factory=list)
    # 信心度（0-1，杨派 D2 画面合拍命中率）
    confidence: float = 0.6

    def to_dict(self) -> dict:
        return {
            "best_window": list(self.best_window),
            "secondary_window": list(self.secondary_window) if self.secondary_window else None,
            "expected_status": self.expected_status,
            "spouse_keywords": list(self.spouse_keywords),
            "confidence": self.confidence,
        }


@dataclass
class CareerPicture:
    """事业画面：杨派 D2 输出的事业关键窗口。"""

    # 事业关键节点窗口（虚岁/周岁）
    rising_windows: list[tuple[int, int]] = field(default_factory=list)
    # 事业类别画像
    domain_keywords: list[str] = field(default_factory=list)
    confidence: float = 0.6


@dataclass
class EducationPicture:
    """学业画面：杨派 D2 输出的学历层级 + 高考关键年份。"""

    expected_level: str = "高级·中等"   # 参 level-scales.md
    key_year_window: Optional[tuple[int, int]] = None  # 高考前后周岁窗口
    confidence: float = 0.6


@dataclass
class PictureFindings:
    """杨派 D2 画面合拍输出（Track-C 消费）。"""

    schema_version: str = "0.1-stub"
    bazi_str: str = ""

    marriage_picture: MarriagePicture = field(default_factory=MarriagePicture)
    career_picture: CareerPicture = field(default_factory=CareerPicture)
    education_picture: EducationPicture = field(default_factory=EducationPicture)

    upstream_hash: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "bazi_str": self.bazi_str,
            "marriage_picture": self.marriage_picture.to_dict(),
            "career_picture": {
                "rising_windows": [list(w) for w in self.career_picture.rising_windows],
                "domain_keywords": list(self.career_picture.domain_keywords),
                "confidence": self.career_picture.confidence,
            },
            "education_picture": {
                "expected_level": self.education_picture.expected_level,
                "key_year_window": (
                    list(self.education_picture.key_year_window)
                    if self.education_picture.key_year_window
                    else None
                ),
                "confidence": self.education_picture.confidence,
            },
            "upstream_hash": self.upstream_hash,
        }


def _smoke() -> None:
    mp = MarriagePicture(best_window=(23, 27), expected_status="稳定")
    pf = PictureFindings(bazi_str="庚申戊寅壬子辛丑", marriage_picture=mp)
    d = pf.to_dict()
    assert d["marriage_picture"]["best_window"] == [23, 27]
    assert d["marriage_picture"]["expected_status"] == "稳定"
    print("picture.types smoke OK")


if __name__ == "__main__":
    _smoke()
