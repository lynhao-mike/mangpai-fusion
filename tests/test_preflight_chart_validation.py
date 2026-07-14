"""tests/test_preflight_chart_validation.py · preflight 排盘验证硬门测试

验证 tools/preflight.parse() 在加载 case 时:
- 问真八字来源的排盘 → 标记为 skipped_trusted_wenzhen 直接放行
- 其他来源的错误排盘 → 抛 PreflightError 阻断分析
- 其他来源的正确排盘 → 标记为 validated 放行

作者：排盘验证模块
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.preflight import PreflightError, parse


# ============================================================
# 可信样本的最小 v1.2 yaml case 模板（1980-02-09 02:00, 男, 庚申戊寅壬子辛丑）
# ============================================================

_CORRECT_CASE_WITH_WENZHEN_SOURCE = """
```yaml
schema_version: "1.2.0"
case_meta:
  case_id: "C-2099-777-乾-庚申戊寅壬子辛丑"
  立案日期: "2026-05-23"
  命主代号: "TEST-WZ"
  策略: "B"
birth:
  性别: "M"
  公历: "1980-02-09 02:00"
  出生地: "未提供"
  真太阳时校正: true
  来源: "问真八字 APP 排盘"
四柱:
  年柱: "庚申"
  月柱: "戊寅"
  日柱: "壬子"
  时柱: "辛丑"
藏干:
  年支:
    - {干: "庚", 类型: "主气", 力量: 1.0}
    - {干: "壬", 类型: "中气", 力量: 0.3}
    - {干: "戊", 类型: "余气", 力量: 0.2}
  月支:
    - {干: "甲", 类型: "主气", 力量: 1.0}
    - {干: "丙", 类型: "中气", 力量: 0.3}
    - {干: "戊", 类型: "余气", 力量: 0.2}
  日支:
    - {干: "癸", 类型: "主气", 力量: 1.0}
  时支:
    - {干: "己", 类型: "主气", 力量: 1.0}
    - {干: "癸", 类型: "中气", 力量: 0.3}
    - {干: "辛", 类型: "余气", 力量: 0.2}
大运:
  起运岁: 8
  起运年: 1988
  顺逆: "顺"
  排布:
    - {序号: 1, 干支: "己卯", 起讫: "1988-1998", 起岁: 8, 止岁: 17}
    - {序号: 2, 干支: "庚辰", 起讫: "1998-2008", 起岁: 18, 止岁: 27}
    - {序号: 3, 干支: "辛巳", 起讫: "2008-2018", 起岁: 28, 止岁: 37}
    - {序号: 4, 干支: "壬午", 起讫: "2018-2028", 起岁: 38, 止岁: 47}
    - {序号: 5, 干支: "癸未", 起讫: "2028-2038", 起岁: 48, 止岁: 57}
    - {序号: 6, 干支: "甲申", 起讫: "2038-2048", 起岁: 58, 止岁: 67}
    - {序号: 7, 干支: "乙酉", 起讫: "2048-2058", 起岁: 68, 止岁: 77}
    - {序号: 8, 干支: "丙戌", 起讫: "2058-2068", 起岁: 78, 止岁: 87}
神煞:
  年柱: []
  月柱: []
  日柱: []
  时柱: []
  整体: []
十二长生:
  日干: "壬"
  年支: "长生"
  月支: "病"
  日支: "帝旺"
  时支: "衰"
known_facts: []
提问: []
```
"""


def _write_case(tmp: Path, case_id: str, body: str) -> Path:
    """把 yaml body 写入 cases/CASE_ID/input.md 结构。"""
    case_dir = tmp / "cases" / case_id
    case_dir.mkdir(parents=True)
    path = case_dir / "input.md"
    path.write_text(f"# case\n\n{body}", encoding="utf-8")
    return path


def test_preflight_bypasses_wenzhen_source(tmp_path: Path) -> None:
    """来源为问真八字时,排盘验证跳过,parsed.case_meta 标记 skipped_trusted_wenzhen。"""
    case_id = "C-2099-777-乾-庚申戊寅壬子辛丑"
    body = _CORRECT_CASE_WITH_WENZHEN_SOURCE.replace(
        "TEST-WZ", "命主 WZ 测试"
    )
    path = _write_case(tmp_path, case_id, body)

    parsed = parse(path)

    assert parsed.case_meta.get("排盘验证状态") == "skipped_trusted_wenzhen"


def test_preflight_validates_correct_non_wenzhen(tmp_path: Path) -> None:
    """非问真来源但排盘正确时,标记为 validated。"""
    case_id = "C-2099-778-乾-庚申戊寅壬子辛丑"
    body = _CORRECT_CASE_WITH_WENZHEN_SOURCE.replace(
        'case_id: "C-2099-777-乾-庚申戊寅壬子辛丑"',
        f'case_id: "{case_id}"',
    ).replace(
        '来源: "问真八字 APP 排盘"',
        '来源: "用户手工整理"',
    )
    path = _write_case(tmp_path, case_id, body)

    parsed = parse(path)

    assert parsed.case_meta.get("排盘验证状态") == "validated"


def test_preflight_blocks_wrong_month_pillar(tmp_path: Path) -> None:
    """非问真来源 + 月柱错误,应抛 PreflightError,携带正确的修正四柱。"""
    case_id = "C-2099-779-乾-庚申丁丑壬子辛丑"
    body = _CORRECT_CASE_WITH_WENZHEN_SOURCE.replace(
        'case_id: "C-2099-777-乾-庚申戊寅壬子辛丑"',
        f'case_id: "{case_id}"',
    ).replace(
        '来源: "问真八字 APP 排盘"',
        '来源: "用户手工整理"',
    ).replace(
        '月柱: "戊寅"', '月柱: "丁丑"',
    )
    # case_id 已改成含错误月柱,但四柱字段也要跟着改否则 step 6 会先炸
    # 上面已同步

    path = _write_case(tmp_path, case_id, body)

    with pytest.raises(PreflightError) as exc:
        parse(path)
    assert "排盘验证" in exc.value.field_path
    assert "月柱" in exc.value.detail
    assert "戊寅" in exc.value.detail  # 修正四柱含正确月柱
