"""tools/three_layer_check.py · 兜底护栏 #3 · 应期三层 gate 强一致

校验 GateResult 的 ★ 等级与 passed_layers 是否一致：

    ★★★★★ 必须 passed_layers == 3
    ★★★★   必须 passed_layers >= 2
    ★★★     必须 passed_layers >= 1
    ★★       passed_layers 可为 0-3（已是惩罚级别，不强校）
    ★         passed_layers 可为 0-3

参考契约：
  - 04-gate-protocol.md § 七 confidence_ceiling_by_passed_layers
  - 06-confidence-model.md § 四 应期 GateResult 的置信度
  - 03-findings-schema.md § 七 GateResult 的三层惩罚规则

依赖：标准库
版本：v1.2.0
作者：Track-E
"""
from __future__ import annotations

import dataclasses
import sys
from dataclasses import dataclass
from typing import Any, Optional, Union


@dataclass
class CheckIssue:
    """三层校验失败时的报错条目"""
    star: int
    passed_layers: int
    expected_min: int
    detail: str


# ★ → 必需的最低 passed_layers
STAR_MIN_PASSED: dict[int, int] = {
    1: 0,
    2: 0,
    3: 1,
    4: 2,
    5: 3,
}


def _get(obj: Any, attr: str, default: Any = None) -> Any:
    """支持 dataclass / dict / 属性访问"""
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)


def _extract_star_and_layers(
    gate_result: Any,
) -> tuple[Optional[int], Optional[int]]:
    """从 GateResult-like 对象提取 (star, passed_layers)。

    支持：
      - dataclass GateResult（带 confidence.star + passed_layers 字段）
      - dict 形如 {confidence: {star: 5}, passed_layers: 3}
      - dict 形如 {star: 5, passed_layers: 3}（扁平，便于测试）
    """
    pl = _get(gate_result, "passed_layers")
    star = _get(gate_result, "star")
    if star is None:
        conf = _get(gate_result, "confidence")
        if conf is not None:
            star = _get(conf, "star")
    if star is not None:
        try:
            star = int(star)
        except (TypeError, ValueError):
            star = None
    if pl is not None:
        try:
            pl = int(pl)
        except (TypeError, ValueError):
            pl = None
    return star, pl


def check_yingqi(gate_result: Any) -> tuple[bool, str]:
    """主接口：校验单个 GateResult 的 ★/passed_layers 一致。

    :param gate_result: dataclass / dict / 自定义对象
    :return: (ok, message)
        - ok=True  : 校验通过，message='OK: ★X with passed_layers=Y'
        - ok=False : 校验失败，message='★X 与 passed_layers={N} 不匹配'
    """
    star, pl = _extract_star_and_layers(gate_result)
    if star is None:
        return False, "缺 confidence.star（无法判定 ★ 等级）"
    if pl is None:
        return False, "缺 passed_layers 字段"
    if star < 1 or star > 5:
        return False, f"★{star} 非法（必须 1-5）"
    if pl < 0 or pl > 3:
        return False, f"passed_layers={pl} 非法（必须 0-3）"

    expected_min = STAR_MIN_PASSED.get(star, 0)
    # ★★★★★ 还要求 ==3，不允许过头
    if star == 5 and pl != 3:
        return False, (
            f"★5 与 passed_layers={pl} 不匹配（必须严格 = 3）"
        )
    if pl < expected_min:
        return False, (
            f"★{star} 与 passed_layers={pl} 不匹配（最少需 {expected_min}）"
        )
    return True, f"OK: ★{star} with passed_layers={pl}"


def check_all(
    gate_results: list[Any],
) -> tuple[bool, list[CheckIssue]]:
    """批量校验：返回 (all_ok, [失败项])"""
    issues: list[CheckIssue] = []
    for i, gr in enumerate(gate_results):
        ok, msg = check_yingqi(gr)
        if ok:
            continue
        star, pl = _extract_star_and_layers(gr)
        issues.append(CheckIssue(
            star=star or 0,
            passed_layers=pl or 0,
            expected_min=STAR_MIN_PASSED.get(star or 0, 0),
            detail=msg,
        ))
    return len(issues) == 0, issues


# ============================================================
# smoke test
# ============================================================

def _smoke() -> None:
    fixtures: list[tuple[str, dict[str, Any], bool]] = [
        ("★5+pass3 OK",   {"star": 5, "passed_layers": 3}, True),
        ("★5+pass2 FAIL", {"star": 5, "passed_layers": 2}, False),
        ("★4+pass2 OK",   {"star": 4, "passed_layers": 2}, True),
        ("★4+pass1 FAIL", {"star": 4, "passed_layers": 1}, False),
        ("★3+pass1 OK",   {"star": 3, "passed_layers": 1}, True),
        ("★3+pass0 FAIL", {"star": 3, "passed_layers": 0}, False),
        ("★2+pass0 OK",   {"star": 2, "passed_layers": 0}, True),
        ("★1+pass0 OK",   {"star": 1, "passed_layers": 0}, True),
        ("nested confidence",
         {"confidence": {"star": 5}, "passed_layers": 3}, True),
        ("missing star",  {"passed_layers": 3}, False),
        ("missing pl",    {"star": 5}, False),
        ("bad star",      {"star": 6, "passed_layers": 3}, False),
        ("bad pl",        {"star": 4, "passed_layers": 5}, False),
        ("★5+pass3+over", {"star": 5, "passed_layers": 3}, True),
    ]
    fail = 0
    for name, payload, expect_ok in fixtures:
        ok, msg = check_yingqi(payload)
        mark = "✓" if ok == expect_ok else "✗"
        if ok != expect_ok:
            fail += 1
        print(f"{mark} {name:25s}: ok={ok}  msg={msg}")
    print(f"\nfail={fail}/{len(fixtures)}")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":  # pragma: no cover
    _smoke()
