"""engine/pangzheng/support.py · Track-D 主入口模块名 alias

Track-H tests/regression/test_v1_2_vs_v1_0.py 中的 _engine_d_available() 探测
``engine.pangzheng.support`` 模块来判断 Track-D 是否就绪。

为了让该探测能正确感知 Track-D 已落地，本文件 re-export support_with_shensha。

实际实现见 ``engine/pangzheng/pangzheng.py``。
"""
from engine.pangzheng.pangzheng import support_with_shensha  # noqa: F401
from engine.pangzheng.types import SupportFindings  # noqa: F401

__all__ = ["support_with_shensha", "SupportFindings"]
