"""历史问真转案大运方向迁移测试。"""
from __future__ import annotations

from pathlib import Path

from tools.fix_wenzhen_dayun_direction import migrate_case_file


INPUT = """# 保留标题

```yaml
birth:
  性别: 男
四柱:
  年柱: 乙丑
  月柱: 乙酉
  日柱: 乙亥
  时柱: 乙酉
大运:
  起运岁: 8
  起运年: 1993
  顺逆: 顺
  起运原文: 出生后8年6月22天5小时起运
  排布:
  - 序号: 1
    干支: 丙戌
    起讫: 1993-2003
    起岁: 8
    止岁: 17
  - 序号: 2
    干支: 丁亥
    起讫: 2003-2013
    起岁: 18
    止岁: 27
  - 序号: 3
    干支: 戊子
    起讫: 2013-2023
    起岁: 28
    止岁: 37
known_facts: []
```

尾注保留。
"""


def _record() -> dict:
    return {
        "case_id": "C-TEST-乾-乙丑乙酉乙亥乙酉",
        "claimed_dayun_direction": "顺",
        "computed_dayun_direction": "逆",
        "claimed_dayun_sequence": ["丙戌", "丁亥", "戊子"],
        "computed_dayun_sequence": ["甲申", "癸未", "壬午"],
        "gender": "男",
        "claimed_pillars": {"年柱": "乙丑", "月柱": "乙酉"},
    }


def test_migration_changes_only_direction_and_sequence(tmp_path: Path) -> None:
    path = tmp_path / "input.md"
    path.write_text(INPUT, encoding="utf-8")

    result = migrate_case_file(path, _record(), write=True)
    actual = path.read_text(encoding="utf-8")

    assert result["status"] == "updated"
    assert "顺逆: 逆" in actual
    assert "干支: 甲申" in actual
    assert "干支: 癸未" in actual
    assert "干支: 壬午" in actual
    assert "起运岁: 8" in actual
    assert "起运年: 1993" in actual
    assert "起讫: 1993-2003" in actual
    assert "尾注保留。" in actual


def test_migration_dry_run_does_not_write(tmp_path: Path) -> None:
    path = tmp_path / "input.md"
    path.write_text(INPUT, encoding="utf-8")

    result = migrate_case_file(path, _record(), write=False)

    assert result["status"] == "would_update"
    assert path.read_text(encoding="utf-8") == INPUT


def test_migration_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "input.md"
    path.write_text(INPUT, encoding="utf-8")

    migrate_case_file(path, _record(), write=True)
    result = migrate_case_file(path, _record(), write=True)

    assert result["status"] == "already_fixed"
