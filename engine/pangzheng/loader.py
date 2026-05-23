"""engine/pangzheng/loader.py · 从 cases/*/input.md 加载神煞数据

旁路：tests/fixtures/cases.py 不读取 input.md 中的神煞列表（只构造 bazi+dayun），
本模块补这个缺口，供 Track-D 测试使用。

input.md 中的神煞表格形如：
    | 柱别 | ... | 神煞 |
    | 年柱 | ... | 太极贵人 |
    | 月柱 | ... | 太极贵人、文昌、德秀、天厨、驿马、词馆、空亡 |
    ...

作者：Track-D
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


# 仓库根目录
_ROOT = Path(__file__).resolve().parents[2]
_CASES_DIR = _ROOT / "cases"


def _find_case_dir(case_id: str) -> Optional[Path]:
    """根据 case_id（短或全形式）找到 cases/ 下的目录。"""
    # 全形式直接试
    p = _CASES_DIR / case_id
    if p.exists():
        return p
    # 短形式：扫描 cases/ 找前缀
    if _CASES_DIR.exists():
        matches = sorted(
            d for d in _CASES_DIR.iterdir()
            if d.is_dir() and d.name.startswith(case_id)
        )
        if matches:
            return matches[0]
    return None


def _parse_markdown_table(text: str) -> dict[str, list[str]]:
    """解析 markdown table 格式（C-001 等老格式）。

    形如 | **年柱** | ... | 太极贵人 |
    """
    out: dict[str, list[str]] = {}
    pillar_re = re.compile(r"\|[^|]*\*\*?(年柱|月柱|日柱|时柱)\*\*?[^|]*\|")
    for line in text.splitlines():
        m = pillar_re.search(line)
        if not m:
            continue
        pillar_name = m.group(1)
        cells = [c.strip() for c in line.split("|") if c.strip()]
        if len(cells) < 2:
            continue
        shensha_str = cells[-1]
        if not shensha_str or shensha_str in ("—", "-", "无", "无神煞"):
            out[pillar_name] = []
            continue
        # 用 顿号/逗号/斜杠/空格 分隔
        parts = re.split(r"[、,，/／\s]+", shensha_str)
        out[pillar_name] = [p.strip() for p in parts if p.strip()]
    return out


def _parse_fixed_width(text: str) -> dict[str, list[str]]:
    """解析 fixed-width 纯文本格式（C-014 等新格式）。

    形如 "年柱   丙      戌      伤官      丁辛戊         德秀贵人 / 天罗地网 / 流霞"
    """
    out: dict[str, list[str]] = {}
    # 行首是 "年柱/月柱/日柱/时柱" + 多个空格 + ... 然后最后一个字段是神煞
    pillar_line_re = re.compile(
        r"^(年柱|月柱|日柱|时柱)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.+?)\s*$"
    )
    for line in text.splitlines():
        m = pillar_line_re.match(line.strip())
        if not m:
            continue
        pillar_name = m.group(1)
        shensha_str = m.group(6).strip()
        if not shensha_str or shensha_str in ("—", "-", "无", "无神煞"):
            out[pillar_name] = []
            continue
        parts = re.split(r"[、,，/／\s]+", shensha_str)
        out[pillar_name] = [p.strip() for p in parts if p.strip()]
    return out


def load_shensha_from_input_md(case_id: str) -> dict[str, list[str]]:
    """从 cases/{case_id}/input.md 解析神煞表格。

    支持两种格式（自动尝试）：
      1. Markdown table（C-001 等）：| **年柱** | ... | 太极贵人 |
      2. Fixed-width 纯文本（C-014 等）：年柱   丙      戌      ...   德秀贵人 / 天罗地网

    返回 {年柱: [...], 月柱: [...], 日柱: [...], 时柱: [...]}。
    若文件不存在或解析失败 → 返回空 dict（不抛错）。
    """
    case_dir = _find_case_dir(case_id)
    if case_dir is None:
        return {}
    input_md = case_dir / "input.md"
    if not input_md.exists():
        return {}

    try:
        text = input_md.read_text(encoding="utf-8")
    except OSError:
        return {}

    # 优先 markdown table
    out = _parse_markdown_table(text)
    if out and any(out.values()):
        return out

    # fallback fixed-width
    out = _parse_fixed_width(text)
    return out


def attach_shensha(parsed) -> None:
    """给一个 ParsedInput 注入 shensha 字段（in-place）。"""
    if parsed is None:
        return
    case_id = getattr(parsed, "case_id", "")
    if not case_id:
        return
    if getattr(parsed, "shensha", None):
        # 已有数据，不覆盖
        return
    sh = load_shensha_from_input_md(case_id)
    if sh:
        parsed.shensha = sh


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    # C-2026-001（应有完整神煞表）
    sh = load_shensha_from_input_md("C-2026-001-庚申戊寅壬子辛丑")
    assert "年柱" in sh, f"应解析到年柱: {sh}"
    assert "月柱" in sh
    assert "日柱" in sh
    assert "时柱" in sh
    # C-001 时柱有金舆
    assert "金舆" in sh.get("时柱", []), f"时柱应含金舆：{sh.get('时柱')}"
    # C-001 月柱有驿马
    assert "驿马" in sh.get("月柱", []), f"月柱应含驿马：{sh.get('月柱')}"
    print(f"[OK] C-001 shensha:")
    for k, v in sh.items():
        print(f"  {k}: {v}")

    # 短形式
    sh2 = load_shensha_from_input_md("C-2026-001")
    assert sh == sh2, "短形式应与全形式结果相同"

    # C-2026-014（学业案）
    sh14 = load_shensha_from_input_md("C-2026-014-丙戌庚子乙亥辛巳")
    print(f"\n[OK] C-014 shensha:")
    for k, v in sh14.items():
        print(f"  {k}: {v}")

    # 不存在的 case → 空
    bad = load_shensha_from_input_md("C-9999-999")
    assert bad == {}

    print("\n[OK] loader smoke 全过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
