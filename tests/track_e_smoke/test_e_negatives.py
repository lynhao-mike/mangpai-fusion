"""tests/track_e_smoke/test_e_negatives.py

Track-E 8 条负向自测（E-001 ~ E-008）。
对应 08-agent-handoff.md § 六 Agent E 回归测试表。

| 编号 | 输入                    | 期望              |
|------|-------------------------|-------------------|
| E-001| 缺 schema_version       | preflight FAIL    |
| E-002| 四柱含非法字 "甲丑"     | preflight FAIL    |
| E-003| ★5 (50%) 区间不符       | linter FAIL       |
| E-004| 应期断语无 yingqi_year  | linter FAIL       |
| E-005| 引用 blacklisted 规律   | linter FAIL       |
| E-006| ★★★★★ + passed_layers=2| three_layer FAIL  |
| E-007| 含 "未来某年"           | linter WARNING    |
| E-008| 指纹重复                | preflight FAIL    |

不依赖 pytest，纯 stdlib，便于 `python tests/track_e_smoke/test_e_negatives.py` 直接跑。
"""
from __future__ import annotations

import sys
import tempfile
import textwrap
import traceback
from pathlib import Path

# 让本文件无论被 pytest 或 直接 python 调用，都能找到 tools/
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.preflight import (  # noqa: E402
    PreflightError, parse,
)
from tools.output_linter import (  # noqa: E402
    Severity, lint,
)
from tools.three_layer_check import (  # noqa: E402
    check_yingqi,
)


# ============================================================
# 通用测试结果累计
# ============================================================

class _Reporter:
    def __init__(self) -> None:
        self.results: list[tuple[str, str, str]] = []  # (id, status, msg)

    def add(self, tid: str, ok: bool, msg: str) -> None:
        self.results.append((tid, "PASS" if ok else "FAIL", msg))

    def add_skip(self, tid: str, msg: str) -> None:
        self.results.append((tid, "SKIP", msg))

    def summary(self) -> int:
        passes = sum(1 for _, s, _ in self.results if s == "PASS")
        fails = sum(1 for _, s, _ in self.results if s == "FAIL")
        skips = sum(1 for _, s, _ in self.results if s == "SKIP")
        print()
        print("=" * 70)
        for tid, status, msg in self.results:
            icon = {"PASS": "✓", "FAIL": "✗", "SKIP": "—"}[status]
            print(f"{icon} {tid}  [{status}]  {msg}")
        print("=" * 70)
        print(f"PASS={passes}  FAIL={fails}  SKIP={skips}  TOTAL={len(self.results)}")
        return 0 if fails == 0 else 1


# ============================================================
# 工具：写一份"基本合规"的 input.md（其余 case 在此基础上突变）
# ============================================================

_BASE_INPUT_TMPL = textwrap.dedent("""\
    # {case_id} · 输入信息

    ```yaml
    {schema_block}
    case_meta:
      case_id: {case_id}
      立案日期: 2099-01-01
      命主代号: 测试命主
      策略: B
    birth:
      性别: M
      公历: "{gongli}"
      出生地: 北京市
      真太阳时校正: true

    四柱:
      年柱: {nz}
      月柱: {yz}
      日柱: {dz}
      时柱: {sz}
    ```

    ```yaml
    藏干:
      年支:
        - {{干: 癸, 类型: 主气, 力量: 1.0}}
      月支:
        - {{干: 戊, 类型: 主气, 力量: 1.0}}
      日支:
        - {{干: 乙, 类型: 主气, 力量: 1.0}}
      时支:
        - {{干: 戊, 类型: 主气, 力量: 1.0}}

    大运:
      起运岁: 5
      起运年: 2029
      顺逆: 顺
      排布:
        - {{序号: 1, 干支: 乙亥, 起讫: "2029-2039", 起岁: 5,  止岁: 14}}
        - {{序号: 2, 干支: 丙子, 起讫: "2039-2049", 起岁: 15, 止岁: 24}}
        - {{序号: 3, 干支: 丁丑, 起讫: "2049-2059", 起岁: 25, 止岁: 34}}
        - {{序号: 4, 干支: 戊寅, 起讫: "2059-2069", 起岁: 35, 止岁: 44}}
        - {{序号: 5, 干支: 己卯, 起讫: "2069-2079", 起岁: 45, 止岁: 54}}
        - {{序号: 6, 干支: 庚辰, 起讫: "2079-2089", 起岁: 55, 止岁: 64}}
        - {{序号: 7, 干支: 辛巳, 起讫: "2089-2099", 起岁: 65, 止岁: 74}}
        - {{序号: 8, 干支: 壬午, 起讫: "2099-2109", 起岁: 75, 止岁: 84}}

    神煞:
      年柱: []
      月柱: []
      日柱: []
      时柱: []

    十二长生:
      日干: {dgan}
      年支: 临官
      月支: 衰
      日支: 长生
      时支: 衰

    known_facts: []

    提问: []
    ```
""")


def write_case(
    tmp: Path,
    case_id: str = "C-2099-001-甲子甲戌癸卯壬戌",
    nz: str = "甲子",
    yz: str = "甲戌",
    dz: str = "癸卯",
    sz: str = "壬戌",
    dgan: str = "癸",
    gongli: str = "2024-01-01 00:00",
    schema_block: str = "schema_version: 1.2.0",
    extra_nzhi_override: str | None = None,
) -> Path:
    case_dir = tmp / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    body = _BASE_INPUT_TMPL.format(
        case_id=case_id, nz=nz, yz=yz, dz=dz, sz=sz,
        dgan=dgan, gongli=gongli, schema_block=schema_block,
    )
    if extra_nzhi_override is not None:
        body = body.replace(f"年柱: {nz}", extra_nzhi_override)
    (case_dir / "input.md").write_text(body, encoding="utf-8")
    return case_dir / "input.md"


# ============================================================
# 8 条负向测试
# ============================================================

def test_E001_missing_schema_version(rep: _Reporter, tmp: Path) -> None:
    """E-001 缺 schema_version → preflight FAIL"""
    inp = write_case(tmp / "e001", schema_block="# (no schema_version)")
    try:
        parse(inp)
        rep.add("E-001", False, "应当抛 PreflightError，实际放过")
    except PreflightError as e:
        ok = e.step == 1 and "schema_version" in e.field_path
        rep.add("E-001", ok, f"step={e.step} field={e.field_path} detail={e.detail}")
    except Exception as e:  # pragma: no cover
        rep.add("E-001", False, f"非预期异常 {type(e).__name__}: {e}")


def test_E002_invalid_pillar(rep: _Reporter, tmp: Path) -> None:
    """E-002 四柱含非法字 '甲丑' → preflight FAIL（甲为阳干、丑为阴支不配 60 甲子）"""
    # 用 case_id 为合法（保证前面几步过），仅四柱.年柱 改为 甲丑（非法）
    case_id = "C-2099-002-甲子甲戌癸卯壬戌"
    inp = write_case(tmp / "e002", case_id=case_id, nz="甲子")
    text = inp.read_text(encoding="utf-8")
    text = text.replace("年柱: 甲子", "年柱: 甲丑")
    inp.write_text(text, encoding="utf-8")
    try:
        parse(inp)
        rep.add("E-002", False, "应当抛 PreflightError，实际放过")
    except PreflightError as e:
        ok = e.step in (4, 6) and ("年柱" in e.field_path or "甲丑" in e.detail or "甲子" in e.detail)
        rep.add("E-002", ok, f"step={e.step} field={e.field_path} detail={e.detail}")
    except Exception as e:  # pragma: no cover
        rep.add("E-002", False, f"非预期异常 {type(e).__name__}: {e}")


def test_E003_star_pct_range(rep: _Reporter) -> None:
    """E-003 ★5 (50%) → linter FAIL（区间不符）"""
    md = "[共识] 测试断语 ★5 (50%) 来源：MR-001"
    r = lint(md)
    fails = [i for i in r.errors if i.code == "E1"]
    rep.add("E-003", len(fails) >= 1,
            f"errors={[i.code for i in r.errors]}")


def test_E004_yingqi_no_year(rep: _Reporter) -> None:
    """E-004 应期断语无 yingqi_year → linter FAIL"""
    # 故意构造为应期断语（domain=应期 / candidate_event=结婚）而无 yingqi_year
    payload = {
        "final_conclusions": [
            {
                "conclusion_id": "CC-001",
                "statement": "命主婚期应期",
                "domain": "应期",
                "candidate_event": "结婚",
                "confidence": {"star": 5, "percent": 0.90, "passed_layers": 3},
                "evidence": [{"rule_id": "MR-005"}],
                "falsifiable": "若实际未结婚则失验",
                # 故意缺 yingqi_year + year
            }
        ],
        "gate_results": [],
    }
    r = lint(payload)
    fails = [i for i in r.errors if i.code == "E4"]
    rep.add("E-004", len(fails) >= 1,
            f"errors={[i.code for i in r.errors]}")


def test_E005_blacklisted_rule(rep: _Reporter) -> None:
    """E-005 引用 blacklisted 规律 → linter FAIL"""
    md = (
        "[杨派] 命主因 XF-002 五凶煞集齐 → 婚姻坎坷必离 ★4 (75%) "
        "来源：M2-Y-073, XF-002"
    )
    r = lint(md)
    fails = [i for i in r.errors if i.code == "E10"]
    rep.add("E-005", len(fails) >= 1,
            f"errors={[i.code for i in r.errors]} matched={[i.message for i in fails]}")


def test_E006_three_layer_mismatch(rep: _Reporter) -> None:
    """E-006 ★★★★★ 但 passed_layers=2 → three_layer_check FAIL"""
    gr = {"star": 5, "passed_layers": 2}
    ok, msg = check_yingqi(gr)
    rep.add("E-006", (not ok) and "5" in msg and "2" in msg,
            f"ok={ok} msg={msg}")


def test_E007_forbidden_phrase(rep: _Reporter) -> None:
    """E-007 含'未来某年' → linter WARNING（不阻塞，但有 W7）"""
    md = "[共识] 命主未来某年有大事 ★3 (60%) 来源：MR-001 应期: 2030 年"
    r = lint(md)
    warns = [i for i in r.warnings if i.code == "W7"]
    has_match = any("未来某年" in i.message for i in warns)
    rep.add("E-007", has_match,
            f"warnings={[i.code for i in r.warnings]} match={has_match}")


def test_E008_duplicate_fingerprint(rep: _Reporter, tmp: Path) -> None:
    """E-008 指纹重复 → preflight FAIL"""
    # 构造 cases-index.md 含已注册指纹
    case_id = "C-2099-003-甲子甲戌癸卯壬戌"
    case_dir = tmp / "e008"
    case_dir.mkdir()
    inp = write_case(case_dir, case_id=case_id, gongli="2024-01-01 00:00")
    # 把同 fingerprint 的另一 case_id 写入 cases-index.md
    from tools.preflight import compute_fingerprint
    fp = compute_fingerprint({"性别": "M", "公历": "2024-01-01 00:00"})
    cases_index = case_dir / "cases-index.md"
    cases_index.write_text(
        f"# 案例索引\n\n## 二、八字指纹防重\n\n```\n"
        f"{fp}  · C-2099-999-某某某某  · 男  · 2024-01-01 00:00 · 甲子甲戌癸卯壬戌\n```\n",
        encoding="utf-8",
    )
    try:
        parse(inp, cases_index_path=cases_index)
        rep.add("E-008", False, "应当抛 PreflightError，实际放过")
    except PreflightError as e:
        ok = e.step == 5 and "fingerprint" in e.field_path
        rep.add("E-008", ok, f"step={e.step} field={e.field_path}")
    except Exception as e:  # pragma: no cover
        rep.add("E-008", False, f"非预期异常 {type(e).__name__}: {e}")


# ============================================================
# 主入口
# ============================================================

def main() -> int:
    rep = _Reporter()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for fn, args in [
            (test_E001_missing_schema_version, (rep, tmp)),
            (test_E002_invalid_pillar,         (rep, tmp)),
            (test_E003_star_pct_range,         (rep,)),
            (test_E004_yingqi_no_year,         (rep,)),
            (test_E005_blacklisted_rule,       (rep,)),
            (test_E006_three_layer_mismatch,   (rep,)),
            (test_E007_forbidden_phrase,       (rep,)),
            (test_E008_duplicate_fingerprint,  (rep, tmp)),
        ]:
            try:
                fn(*args)
            except Exception as e:  # pragma: no cover
                tid = fn.__name__.split("_")[1]
                rep.add(tid, False,
                        f"测试自身崩溃: {type(e).__name__}: {e}\n"
                        f"{traceback.format_exc()}")
    return rep.summary()


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
