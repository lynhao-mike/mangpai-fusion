"""engine.yingqi · Track-C 任派 D3 应期三层门引擎

v1.2 灵魂条款：原局有 + 大运到位 + 流年引爆 三层齐备才下铁口断。

主入口（所有子模块写完后启用）：
    from engine.yingqi import gate_yingqi
"""

# 避免循环：先 lazy 暴露 types，gate 在底部补
from .types import GateResult, LayerCheck, TriggerEvent, Door

__all__ = [
    "GateResult",
    "LayerCheck",
    "TriggerEvent",
    "Door",
    "gate_yingqi",
]


def __getattr__(name):
    """延迟加载 gate_yingqi 以避免子模块未就绪时 import 失败。"""
    if name == "gate_yingqi":
        from .gate import gate_yingqi as _g
        return _g
    raise AttributeError(name)
