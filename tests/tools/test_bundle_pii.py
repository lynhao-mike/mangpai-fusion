"""脱敏测试：确保 bundle 不含可识别到个人的信息

背景
----
某 LLM 分析者拒绝为真实个人出生盘推演命运画像，理由正当：
旧 bundle 残留「指纹：女 | 2004-02-20 10:21」+ 出生地「江苏盐城市东台」
+ 命主代号，小样本下可识别到个人。

本测试锁定脱敏契约：
- **必须剥离**：精确出生时刻、出生地、命主代号、来源路径、指纹行
- **必须保留**：性别/乾坤（排大运必需）、口径说明、四柱与全部命理内容
- **结构合法**：删字段后 YAML 仍可解析

覆盖两种 feedback 格式（格式 A 有「出生地脱敏」与时间来源字段，
格式 B 有「农历/太阳时」）。
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]

# 本地脱敏脚本已被 .gitignore 忽略、且仓库内不存在（2026-10-26 确认）。
# 过渡措施：缺失时显式 skip，让默认门禁可用并保留有脚本环境下的 PII 检查能力。
# 跟踪任务 T-114：把脱敏逻辑生产化为 tools/bundle_sanitize.py，之后删除本段。
_BUNDLE_SCRIPT = ROOT / ".workbuddy-ai" / "make_bundle_v2.py"
if not _BUNDLE_SCRIPT.exists():
    pytest.skip(
        f"本地脱敏脚本缺失：{_BUNDLE_SCRIPT}；见 T-114（生产化为 tools/bundle_sanitize.py）",
        allow_module_level=True,
    )

# make_bundle_v2 在 .workbuddy-ai 下（非包），用 spec 加载
_SPEC = importlib.util.spec_from_file_location("make_bundle_v2", _BUNDLE_SCRIPT)
_mod = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(_mod)
sanitize_input = _mod.sanitize_input


def _write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "input.md"
    p.write_text(body, encoding="utf-8")
    return p


# 格式 A：含「出生地脱敏」与时间来源/经度校正
FORMAT_A = """# Case TEST-A · 输入信息

> 问真待分析样本批量正式转案；raw_id：`RF-2026-000077`。

**立案日期**：2026-06-11  
**命主代号**：RF-2026-000077  
**采集人**：mangpai-fusion wenzhen promotion  
**指纹**：`abc123def456`（M | 1970-03-11 19:15）

---

## 一、八字盘

```yaml
schema_version: 1.2.0
case_meta:
  case_id: TEST-A
  立案日期: '2026-06-11'
  命主代号: RF-2026-000077
  source_rank: 12
  pending_samples_path: cases/raw_feedback/parsed/x.jsonl
  quality_grade: B
birth:
  性别: M
  乾坤: 乾
  公历: "1970-03-11 19:15:00"
  出生地脱敏: "厦门市"
  时间来源: birth_datetime_raw
  真太阳时字段优先: false
  经度校正: false
  经度校正说明: "本模块未做地点、经度、时区或真太阳时换算；直接采用来源字段时间。"
四柱:
  年柱: 庚戌
  月柱: 己卯
  日柱: 庚寅
  时柱: 丙戌
```
"""

# 格式 B：含农历/太阳时/出生地原始摘录
FORMAT_B = """# Case TEST-B · 输入信息

> 来源：`cases/raw_feedback/parsed/real_cases_990.jsonl` 的 `RF-2026-000421`。

**命主代号**：RF-2026-000421  
**指纹**：`35e693be0375`（女 | 2004-02-20 10:21）

```yaml
schema_version: 1.2.0
case_meta:
  case_id: TEST-B
  命主代号: RF-2026-000421
birth:
  性别: 女
  乾坤: 坤
  公历: 2004-02-20 10:21
  农历: 2004年二月初一 巳时
  出生地: 江苏盐城市
  出生地原始摘录: 江苏盐城市 东台
  真太阳时校正: true
  太阳时: 2004-02-20 10:21
四柱:
  年柱: 甲申
  月柱: 丙寅
  日柱: 己巳
  时柱: 己巳
```
"""


@pytest.mark.parametrize(("name", "body", "leaks"), [
    ("格式A", FORMAT_A, [
        "1970-03-11", "19:15", "厦门市", "RF-2026-000077",
        "abc123def456", "pending_samples_path", "raw_id",
    ]),
    ("格式B", FORMAT_B, [
        "2004-02-20", "10:21", "江苏盐城市", "东台", "RF-2026-000421",
        "35e693be0375", "二月初一", "巳时",
    ]),
])
def test_pii_removed(tmp_path: Path, name: str, body: str, leaks: list[str]) -> None:
    """必须剥离：精确时刻、出生地、命主代号、来源路径、指纹。"""
    out = sanitize_input(_write(tmp_path, body))
    found = [s for s in leaks if s in out]
    assert not found, f"{name} 未剥离: {found}"


@pytest.mark.parametrize(("name", "body"), [("格式A", FORMAT_A), ("格式B", FORMAT_B)])
def test_keeps_gender(tmp_path: Path, name: str, body: str) -> None:
    """性别/乾坤必须保留（排大运顺逆必需）。"""
    out = sanitize_input(_write(tmp_path, body))
    assert "性别:" in out, f"{name} 把性别删了"
    assert "乾坤:" in out, f"{name} 把乾坤删了"


def test_keeps_calibration_notes(tmp_path: Path) -> None:
    """格式 A 的口径说明必须保留——它影响判断前提。"""
    out = sanitize_input(_write(tmp_path, FORMAT_A))
    assert "经度校正" in out
    assert "真太阳时字段优先" in out


@pytest.mark.parametrize(("name", "body"), [("格式A", FORMAT_A), ("格式B", FORMAT_B)])
def test_keeps_pillars_and_keeps_yaml_valid(tmp_path: Path, name: str, body: str) -> None:
    """四柱必须保留，且删字段后 YAML 仍可解析。"""
    out = sanitize_input(_write(tmp_path, body))
    m = re.search(r"```yaml\s*\n(.*?)```", out, re.DOTALL)
    assert m, f"{name} yaml 块丢失"
    parsed = yaml.safe_load(m.group(1))
    assert isinstance(parsed, dict)
    assert "四柱" in parsed, f"{name} 四柱丢失"
    assert len(parsed["四柱"]) == 4


def test_marks_birth_section_desensitized(tmp_path: Path) -> None:
    """birth 段应留下脱敏说明，便于分析者知道信息是被有意移除的。"""
    out = sanitize_input(_write(tmp_path, FORMAT_B))
    assert "已脱敏" in out


def test_no_known_facts_residue(tmp_path: Path) -> None:
    """known_facts 必须整体删除（原有契约，防回归）。"""
    body = FORMAT_B.replace(
        "四柱:",
        "known_facts:\n- 年份: 2010\n  事件: 结婚\n四柱:",
    )
    out = sanitize_input(_write(tmp_path, body))
    assert "known_facts" not in out
    assert "结婚" not in out
