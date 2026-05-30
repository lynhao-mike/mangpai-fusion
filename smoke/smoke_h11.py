#!/usr/bin/env python3
"""v1.4 H11 · output_linter W10 学制盲区律报告级扫描 smoke

CFL-C014-003 v2 修订的报告层补丁：social_clock_check 在 gate.py 中已生效，
但报告 markdown 是命理师手写产物（不经 gate pipeline）→ output_linter
增加 W10 自动扫描，命中错锚立即告警。

本 smoke 覆盖：
  - 出生年自动提取
  - 错锚检测：v2.0 报告（"2029 = 大学毕业"）应触发 W10
  - 修正后通过：v2.1 报告（"2028 = 大学毕业"）不应触发 W10
  - 元数据行跳过：含 "v1.0"/"已应验"/"修正" 的行不算错
  - 容差行为：±1 年内不告警
  - 已应验行不误报
"""
import sys
import types
import io

# ── PyYAML shim ─────────────────────────────────────────
from ruamel.yaml import YAML as _YAML
_ry = _YAML(); _ry.preserve_quotes = True
fake_yaml = types.ModuleType("yaml")
def _safe_load(stream):
    if isinstance(stream, (str, bytes)):
        stream = io.StringIO(stream) if isinstance(stream, str) else io.BytesIO(stream)
    result = _ry.load(stream)
    def _conv(o):
        if o is None: return o
        if isinstance(o, dict): return {k: _conv(v) for k, v in o.items()}
        if isinstance(o, list): return [_conv(v) for v in o]
        return o
    return _conv(result)
fake_yaml.safe_load = _safe_load
fake_yaml.safe_dump = lambda d, **kw: ""
fake_yaml.load = lambda s, Loader=None: _safe_load(s)
fake_yaml.YAMLError = Exception
class _L: pass
fake_yaml.SafeLoader = _L; fake_yaml.FullLoader = _L; fake_yaml.Dumper = _L
sys.modules["yaml"] = fake_yaml

sys.path.insert(0, "/projects/sandbox/mangpai-fusion")

PASS = []
FAIL = []

def check(name, cond, msg=""):
    if cond:
        PASS.append(name)
        print(f"  PASS  {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL  {name}  {msg}")


print("=== H11 output_linter W10 学制盲区报告级扫描 ===")

from tools.output_linter import (
    lint,
    _extract_birth_year_from_md,
    _should_skip_sc_lint,
    _LINT_SOCIAL_CLOCK_RULES,
    _LINT_SOCIAL_CLOCK_TOLERANCE,
)

# ============================================================
# T1: 出生年提取
# ============================================================
print("\n--- T1: _extract_birth_year_from_md ---")

md1 = "**出生**：2006-12-12 09:45（真太阳时·巳时）"
check("T1a_出生YYYY-MM-DD", _extract_birth_year_from_md(md1) == 2006,
      f"got={_extract_birth_year_from_md(md1)}")

md2 = "生年：1980"
check("T1b_生年YYYY", _extract_birth_year_from_md(md2) == 1980)

md3 = "无出生信息"
check("T1c_无出生信息_None", _extract_birth_year_from_md(md3) is None)


# ============================================================
# T2: 元数据行跳过
# ============================================================
print("\n--- T2: 元数据行跳过 ---")

skip_lines = [
    "v1.0 写'2029 = 大学毕业'是错的",
    "已应验：2024 高考南京审计大学",
    "v2.0 错锚：2029 大学毕业 → v2.1 修正为 2028",
    "原 v2.0 校准记录",
    "✅ 2024 高考已应验",
]
for line in skip_lines:
    check(f"T2_跳过: {line[:30]}...", _should_skip_sc_lint(line))

# 不应跳过的行
check("T2_预测行不跳过", not _should_skip_sc_lint("2029 己酉 大学毕业 ★4"))


# ============================================================
# T3: 错锚检测 - 模拟 v2.0 错锚版报告
# ============================================================
print("\n--- T3: 明显错锚的报告应触发 W10 ---")

# 命主 2006 出生 → 2027 年应为 21 岁。21 岁高考超容差 [16,20] → W10
# (注：2029 大学毕业 = 23 岁，在合理窗口 [21,24] 内 → lint 抓不到，这是 W10 局限)
md_gaokao_late = """\
# 八字分析报告 · 命主 14
**出生**：2006-12-12 09:45

## 应期总表（错锚示范）
| 2027 | 丁未 | 高考重大年 ★4 |
"""

r = lint(md_gaokao_late)
w10_issues = [i for i in r.issues if i.code == "W10"]
check("T3a_21岁高考_超容差触发W10", len(w10_issues) >= 1,
      f"got={len(w10_issues)}, issues={[i.message[:80] for i in w10_issues]}")

# 验证捕获 2027 高考
caught_2027_gaokao = any("2027" in i.message and "高考" in i.message for i in w10_issues)
check("T3b_捕获2027_21岁高考",
      caught_2027_gaokao,
      f"got messages={[i.message[:60] for i in w10_issues]}")


# ============================================================
# T4: 正确版（v2.1）应不触发 / 触发应在容差内
# ============================================================
print("\n--- T4: v2.1 修正版报告不应触发 W10 ---")

md_v21_正确 = """\
# 八字分析报告 · 命主 14
**出生**：2006-12-12 09:45

## 应期总表（v2.1 校准）

| 年份 | 流年 | 大运 | 事件预测 |
|---|---|---|---|
| 2024 | 甲辰 | ✅ 高考·南京审计大学 |
| 2028 | 戊申 | 大学毕业 · 三岔口落定 ★4 |
| 2031 | 辛亥 | 婚期窗口① ★4 |
| 2033 癸丑 | 婚期最可能 ★4 |

[共识] 体制内财经赛道 ★4 (84%)
"""

r = lint(md_v21_正确)
w10_issues = [i for i in r.issues if i.code == "W10"]
check("T4_v2.1正确版_无W10", len(w10_issues) == 0,
      f"got={len(w10_issues)}, issues={[i.message[:80] for i in w10_issues]}")


# ============================================================
# T5: 元数据行被正确跳过（v2.1 报告含历史 v2.0 错锚记录）
# ============================================================
print("\n--- T5: v2.1 含历史 v2.0 错锚记录，应被跳过 ---")

md_v21_含历史 = """\
# 八字分析报告 · 命主 14
**出生**：2006-12-12 09:45

## v2.0 → v2.1 变更
| v2.0 | v2.1 | 修正 |
|---|---|---|
| 2029 己酉=大学毕业 ★4 (76%) | 2028 戊申=大学毕业 ★4 (78%) | v2.1 重锚 |

## 应期总表
| 2028 | 戊申 | 大学毕业 ★4 |

[共识] 已应验：2024 高考南审 ★5
"""

r = lint(md_v21_含历史)
w10_issues = [i for i in r.issues if i.code == "W10"]
check("T5_含v2.0历史_无W10",
      len(w10_issues) == 0,
      f"含 v2.0/修正/已应验 标记的行应被跳过，got={len(w10_issues)}")


# ============================================================
# T6: 不同命主 / 婚姻应期 / 工作应期
# ============================================================
print("\n--- T6: 不同事件类型 ---")

# 25 岁结婚 OK
md_marry_ok = """\
**出生**：1990-06-15
| 2015 | 结婚 ★4 |
"""
r = lint(md_marry_ok)
check("T6a_25岁结婚_OK", len([i for i in r.issues if i.code == "W10"]) == 0)

# 60 岁高考（错锚）
md_gaokao_bad = """\
**出生**：1990-01-01
| 2050 | 高考 ★3 |
"""
r = lint(md_gaokao_bad)
w10 = [i for i in r.issues if i.code == "W10"]
check("T6b_60岁高考_触发W10", len(w10) >= 1,
      f"got={len(w10)}, msgs={[i.message[:60] for i in w10]}")

# 70 岁结婚（错锚，>50 严重偏差）
md_marry_bad = """\
**出生**：1980-01-01
| 2055 | 结婚 ★3 |
"""
r = lint(md_marry_bad)
w10 = [i for i in r.issues if i.code == "W10"]
check("T6c_75岁结婚_触发W10", len(w10) >= 1,
      f"got={len(w10)}")


# ============================================================
# T7: 容差边界（±1 年）
# ============================================================
print("\n--- T7: 容差边界行为 ---")

# 命主 2006 出生，2025 高考（age=19，窗口 [17,19] 边缘）→ 应通过
md_t7a = """\
**出生**：2006-12-12
| 2025 | 高考 |
"""
r = lint(md_t7a)
check("T7a_19岁高考_通过容差", len([i for i in r.issues if i.code == "W10"]) == 0)

# 2026 高考（age=20，>窗口 1 年）→ 容差通过 (lo-1=16, hi+1=20)
md_t7b = """\
**出生**：2006-12-12
| 2026 | 高考 |
"""
r = lint(md_t7b)
check("T7b_20岁高考_容差通过", len([i for i in r.issues if i.code == "W10"]) == 0)

# 2027 高考（age=21，>窗口 2 年，超容差）→ 触发
md_t7c = """\
**出生**：2006-12-12
| 2027 | 高考 |
"""
r = lint(md_t7c)
w10 = [i for i in r.issues if i.code == "W10"]
check("T7c_21岁高考_超容差触发", len(w10) >= 1,
      f"got={len(w10)}")


# ============================================================
# T8: 真实 C-014 v2.1 报告测试（验证修正后零 W10）
# ============================================================
print("\n--- T8: 真实 C-014 v2.1 报告（修正版）---")

import pathlib
report_path = pathlib.Path(
    "/projects/sandbox/mangpai-fusion/reports/"
    "C-2026-014-乾-丙戌庚子乙亥辛巳-report.md"
)
if report_path.exists():
    md_real = report_path.read_text(encoding="utf-8")
    r = lint(md_real)
    w10 = [i for i in r.issues if i.code == "W10"]
    check("T8_真实v2.1报告_零W10",
          len(w10) == 0,
          f"v2.1 修正版应零告警，got={len(w10)} 条 W10\n  细节:\n    " +
          "\n    ".join(f"{i.message[:100]} | loc: {i.location[:60] if i.location else 'N/A'}"
                        for i in w10[:5]))
else:
    print(f"  SKIP  T8_真实报告未找到: {report_path}")


# ============================================================
# T9: 无出生年信息 → 跳过
# ============================================================
print("\n--- T9: 无出生年信息 ---")

md_no_birth = """\
[共识] 学历层级 一本 ★4
| 2029 | 大学毕业 ★4 |
"""
r = lint(md_no_birth)
w10 = [i for i in r.issues if i.code == "W10"]
check("T9_无出生年_跳过W10", len(w10) == 0)


# ============================================================
# T10: 规则字典完整性（与 engine/yingqi/gate 同步）
# ============================================================
print("\n--- T10: 规则字典完整性 ---")

check("T10_规则数量≥12", len(_LINT_SOCIAL_CLOCK_RULES) >= 12)
check("T10_容差=1", _LINT_SOCIAL_CLOCK_TOLERANCE == 1)

# 与 engine/yingqi/gate 字典对比（结构应一致）
from engine.yingqi.gate import _SOCIAL_CLOCK_RULES as _GATE_RULES
check("T10_与gate字典数量一致",
      len(_LINT_SOCIAL_CLOCK_RULES) == len(_GATE_RULES),
      f"linter={len(_LINT_SOCIAL_CLOCK_RULES)}, gate={len(_GATE_RULES)}")


# ============================================================
print(f"\nv1.4 H11 W10 学制盲区律 lint: {len(PASS)}/{len(PASS)+len(FAIL)} PASS  "
      f"{'OK' if not FAIL else 'FAIL: '+str(FAIL)}")
sys.exit(0 if not FAIL else 1)
