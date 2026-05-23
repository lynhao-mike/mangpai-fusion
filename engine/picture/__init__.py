"""engine/picture · v1.2 D2 杨派画面合拍引擎

杨清娟派"画面合拍器"——把 D1（段派）给的"能量级别"具象化为
"什么人/什么事"的画面。

入口：``match_picture(energy, parsed) → PictureFindings``

子模块：
    types       - PictureFindings + 子结构 + JSON 序列化
    matcher     - match_picture 主入口（编排 + 上游约束校验）
    wubu        - 五步算命法
    wuhe        - 天干五合（化成 / 合绊 / 搅局）
    anyin       - 十神暗引 5 公式
    caifu       - 财富 7 等 + 官命 9 取
    marriage    - 婚姻画像 + 初婚最佳窗口（修复 G2 关键）
    tiaohou     - 调候改运 6 维

作者：Track-B
"""
from engine.picture.types import (  # noqa: F401
    AnyinResult,
    CaifuRanking,
    GuanmingQufa,
    PictureFindings,
    WubuStep,
    WuheRelation,
)


def __getattr__(name: str):
    """Lazy import for ``match_picture`` to avoid circular import during W2 dev."""
    if name == "match_picture":
        from engine.picture.matcher import match_picture as _match_picture
        return _match_picture
    raise AttributeError(f"module 'engine.picture' has no attribute {name!r}")


__all__ = [
    "match_picture",
    "PictureFindings",
    "WubuStep",
    "WuheRelation",
    "AnyinResult",
    "CaifuRanking",
    "GuanmingQufa",
]
