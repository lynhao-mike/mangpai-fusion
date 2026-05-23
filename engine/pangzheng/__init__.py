"""engine/pangzheng · v1.2 D4 高派旁证引擎

主入口：
    from engine.pangzheng import support_with_shensha

    support = support_with_shensha(parsed, energy=..., picture=..., gates=...)
    if support.total_boost_for("marriage") >= 0.04:
        # 婚姻有旁证补强
        ...

模块结构（08 § 二 Track-D 可写区）：
    types          - SupportFindings / ShenshaSupport / HealthFinding / CiguanXuetang
    shensha_lib    - 神煞 → domain → boost 速查表（GP-BD/GP-CH/GP-XL 系）
    loader         - 从 cases/*/input.md 解析神煞表（兼容 markdown table + fixed-width）
    pangzheng      - support_with_shensha 主入口

对外 API（按 03 § 八 + 08 § 二 D 一致）：
    support_with_shensha(parsed, energy, picture, gates) -> SupportFindings

特殊性（03 § 八）：
    "D4 的 boost 只能**增强**已有 D1/D2/D3 结论，不能**新提**结论。"

作者：Track-D
"""
from engine.pangzheng.types import (  # noqa: F401
    CiguanXuetang,
    HealthFinding,
    ShenshaSupport,
    SupportDomain,
    SupportFindings,
)

from engine.pangzheng.shensha_lib import (  # noqa: F401
    EDUCATION_SHENSHA,
    SHENSHA_RULES,
    evaluate_ciguan_xuetang,
    get_all_rule_names,
    get_rule,
)

from engine.pangzheng.loader import (  # noqa: F401
    attach_shensha,
    load_shensha_from_input_md,
)

from engine.pangzheng.pangzheng import (  # noqa: F401
    support_with_shensha,
)


__all__ = [
    # 类型
    "SupportFindings", "ShenshaSupport", "HealthFinding", "CiguanXuetang",
    "SupportDomain",
    # 速查库
    "SHENSHA_RULES", "EDUCATION_SHENSHA",
    "get_rule", "get_all_rule_names", "evaluate_ciguan_xuetang",
    # 加载器
    "load_shensha_from_input_md", "attach_shensha",
    # 主入口
    "support_with_shensha",
]
