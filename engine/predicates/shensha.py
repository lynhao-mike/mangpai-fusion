"""engine/predicates/shensha.py · v1.2 神煞辅助查询（5 函数）

⚠️ **本系统不计算神煞** —— 只查询 input.md 中已录入的神煞列表。
（神煞计算各派标准不一，自算引入第三套标准；见决策 A）

按 02-predicate-library.md § 4.8 实现 5 个函数。

接口约定：
    所有函数接受 input_doc: dict 形式 —— 即 ParsedInput.shensha 这种结构：
        {"年柱": ["太极贵人"], "月柱": ["驿马", "文昌", ...], ...}
    或直接接受 ParsedInput 对象（自动取 .shensha）。

作者：Track-D
"""
from __future__ import annotations

from typing import Optional, Union

from engine.predicates.types import ParsedInput, PalaceName


# ============================================================
# 内部工具：归一化输入
# ============================================================

def _normalize_input(input_doc: Union[dict, "ParsedInput"]) -> dict[str, list[str]]:
    """归一化 input：dict 直接用；ParsedInput 取 .shensha；返回 {柱名: [神煞列表]}。"""
    if hasattr(input_doc, "shensha"):
        sh = getattr(input_doc, "shensha", None) or {}
    elif isinstance(input_doc, dict):
        # 可能是直接传 shensha dict，也可能是 ParsedInput.to_dict() 形式
        if "shensha" in input_doc:
            sh = input_doc.get("shensha") or {}
        else:
            sh = input_doc  # 直接是 shensha dict
    else:
        raise TypeError(
            f"input_doc 必须是 ParsedInput 或 dict，实际 {type(input_doc).__name__}"
        )
    if not isinstance(sh, dict):
        return {}
    return {k: list(v) if isinstance(v, (list, tuple)) else [str(v)] for k, v in sh.items()}


# ============================================================
# 1. has_shensha
# ============================================================

def has_shensha(name: str, input_doc: Union[dict, "ParsedInput"]) -> bool:
    """input_doc 神煞列表中是否含 name（不分柱）。"""
    sh = _normalize_input(input_doc)
    for shenshas in sh.values():
        if name in shenshas:
            return True
    return False


# ============================================================
# 2. get_shensha_at
# ============================================================

def get_shensha_at(
    name: str, input_doc: Union[dict, "ParsedInput"]
) -> list[PalaceName]:
    """name 神煞挂在哪些柱（返回柱位列表，归一化为 X柱 形式）。"""
    sh = _normalize_input(input_doc)
    out: list[str] = []
    for palace, shenshas in sh.items():
        if name in shenshas:
            normalized = palace.replace("年支", "年柱").replace("月支", "月柱") \
                .replace("日支", "日柱").replace("时支", "时柱")
            if normalized not in out:
                out.append(normalized)
    return out  # type: ignore[return-value]


# ============================================================
# 3. is_taichi · 太极贵人
# ============================================================

def is_taichi(input_doc: Union[dict, "ParsedInput"]) -> bool:
    """太极贵人是否在原局（任一柱）。"""
    return has_shensha("太极贵人", input_doc)


# ============================================================
# 4. is_jinyu · 金舆
# ============================================================

def is_jinyu(input_doc: Union[dict, "ParsedInput"]) -> bool:
    """金舆是否在原局。

    金舆 = 富贵神煞 + 婚姻强化神煞 + 豪车象。
    """
    return has_shensha("金舆", input_doc)


# ============================================================
# 5. is_huagai · 华盖
# ============================================================

def is_huagai(input_doc: Union[dict, "ParsedInput"]) -> bool:
    """华盖是否在原局。

    华盖 = 艺术 / 宗教 / 孤高 / 文化才艺。
    """
    return has_shensha("华盖", input_doc)


# ============================================================
# 辅助：批量查询（Track-D 内部用）
# ============================================================

def get_all_shensha_names(input_doc: Union[dict, "ParsedInput"]) -> set[str]:
    """所有神煞名（去重，跨柱聚合）。"""
    sh = _normalize_input(input_doc)
    out: set[str] = set()
    for shenshas in sh.values():
        out.update(shenshas)
    return out


def has_any_shensha(
    names: list[str], input_doc: Union[dict, "ParsedInput"]
) -> list[str]:
    """names 中哪些神煞在原局出现（返回命中的子集）。"""
    all_names = get_all_shensha_names(input_doc)
    return [n for n in names if n in all_names]


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    fake_shensha = {
        "年柱": ["太极贵人"],
        "月柱": ["太极贵人", "文昌", "德秀", "天厨", "驿马", "词馆", "空亡"],
        "日柱": ["天德合", "孤鸾煞", "红艳煞", "童子煞", "将星", "九丑日", "羊刃", "空亡"],
        "时柱": ["天乙贵人", "月德合", "天医", "金舆", "天喜", "血刃", "空亡"],
    }

    assert has_shensha("金舆", fake_shensha)
    assert has_shensha("驿马", fake_shensha)
    assert not has_shensha("华盖", fake_shensha)
    assert not has_shensha("不存在的神煞", fake_shensha)

    assert get_shensha_at("金舆", fake_shensha) == ["时柱"]
    assert get_shensha_at("驿马", fake_shensha) == ["月柱"]
    assert get_shensha_at("太极贵人", fake_shensha) == ["年柱", "月柱"]
    assert get_shensha_at("华盖", fake_shensha) == []

    assert is_taichi(fake_shensha)
    assert is_jinyu(fake_shensha)
    assert not is_huagai(fake_shensha)

    # 通过 ParsedInput 调用
    from engine.predicates.types import (
        Bazi, GanZhi, _default_canggan_for, Dayun, ParsedInput,
    )
    bazi = Bazi(
        年柱=GanZhi("庚", "申"),
        月柱=GanZhi("戊", "寅"),
        日柱=GanZhi("壬", "子"),
        时柱=GanZhi("辛", "丑"),
    )
    bazi.藏干 = _default_canggan_for(bazi)
    parsed = ParsedInput(
        case_id="C-2026-001-test",
        bazi=bazi,
        dayun=Dayun(起运岁=8.5, 起运年=1988, 顺逆="顺", 排布=[]),
        shensha=fake_shensha,
    )
    assert is_jinyu(parsed)
    assert get_shensha_at("天医", parsed) == ["时柱"]

    hit = has_any_shensha(["金舆", "华盖", "驿马", "童子煞"], fake_shensha)
    assert set(hit) == {"金舆", "驿马", "童子煞"}

    all_names = get_all_shensha_names(fake_shensha)
    assert "金舆" in all_names
    assert "驿马" in all_names
    assert len(all_names) >= 15

    print("[OK] shensha smoke：5 函数 + 2 辅助全过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
