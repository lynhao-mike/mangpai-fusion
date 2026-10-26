"""engine/claims/condition_ir · 断语条件 IR（契约 23）。

本包只负责「把一条断语的条件编译成可求值的树，并在某张盘上求值」。
它**不**定义 L2 命题对象（那是 `engine.claims.domain.Claim`），也不产出结论：

- `atoms`：42 个带盘面地址的原子谓词，只读 engine.facts。
- `ir`：三值逻辑求值（真/假/未知）、地址变量绑定、断语状态机、编译校验。

一条断语编译通过后，按 `rule_id` 挂到 `Claim.evidence[].rule_id`，由 L2 层引用。
"""
from engine.claims.condition_ir.atoms import ATOMS, SIGNATURES, AtomResult, build_context
from engine.claims.condition_ir.ir import (
    Outcome,
    compile_claim,
    evaluate,
    evaluate_claim,
    validate_claim,
)

__all__ = [
    "ATOMS",
    "SIGNATURES",
    "AtomResult",
    "build_context",
    "Outcome",
    "evaluate",
    "evaluate_claim",
    "compile_claim",
    "validate_claim",
]
