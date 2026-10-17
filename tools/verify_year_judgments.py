"""tools/verify_year_judgments.py · 年份判断作答的自检工具（给盲断 agent 用）

盲断 agent 每完成一例的 year_judgments.json，可自行运行本工具校验，
不必等我人工检查。校验项：

V1 年份完整性：作答年份集合 == probe.md 列出的年份集合
V2 极性合法：polarity ∈ {吉, 凶, 平}
V3 事项域合法：matters ⊆ {career,wealth,marriage,health,education,family}
V4 依据非空且含盘面引用：basis 含 `e\\d{3}` 或地址模式（如 M.b / D.s / Y.s）
V5 无骑墙词：不得出现 可能/或许/也许/大概/参半/难以

用法
----
    python -m tools.verify_year_judgments                    # 全部案例
    python -m tools.verify_year_judgments --case <case_id>   # 单例
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROBES = ROOT / ".workbuddy-ai" / "year-probes"

VALID_POLARITY = {"吉", "凶", "平"}
VALID_MATTERS = {"career", "wealth", "marriage", "health", "education", "family"}
HEDGE_WORDS = ["可能", "或许", "也许", "大概", "参半", "难以", "不确定", "说不准"]
EDGE_RE = re.compile(r"\be\d{3}\b")
ADDR_RE = re.compile(r"\b(?:Y|M|D|H)\.(?:s|b)\b|\bDY\d+\.(?:s|b)\b|\bLN\d+\.(?:s|b)\b")


def probe_years(case: str) -> set[int]:
    p = PROBES / case / "probe.md"
    if not p.exists():
        return set()
    text = p.read_text(encoding="utf-8")
    m = re.search(r"需要判断的年份共\s*\d+\s*个：(.+)", text)
    if not m:
        return set()
    return {int(y) for y in re.findall(r"\d{4}", m.group(1))}


def verify_case(case: str) -> tuple[bool, list[str]]:
    issues: list[str] = []
    p = PROBES / case / "year_judgments.json"
    if not p.exists():
        return False, ["year_judgments.json 不存在"]

    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        return False, [f"JSON 解析失败: {exc}"]

    expected = probe_years(case)
    if not expected:
        issues.append("无法从 probe.md 解析年份清单")

    rows = data.get("year_judgments") or []
    got = set()
    for i, j in enumerate(rows):
        y = j.get("year")
        if not isinstance(y, int):
            issues.append(f"第 {i+1} 条 year 非整数: {y!r}")
            continue
        got.add(y)
        pol = j.get("polarity")
        if pol not in VALID_POLARITY:
            issues.append(f"{y}: polarity「{pol}」不合法（须为 吉/凶/平）")
        matters = j.get("matters")
        if not isinstance(matters, list):
            issues.append(f"{y}: matters 非数组")
        else:
            bad = set(matters) - VALID_MATTERS
            if bad:
                issues.append(f"{y}: matters 含非法值 {bad}")
            if pol == "平" and matters:
                issues.append(f"{y}: 判「平」但 matters 非空 {matters}")
        basis = str(j.get("basis") or "")
        if not basis.strip():
            issues.append(f"{y}: basis 为空")
        elif not (EDGE_RE.search(basis) or ADDR_RE.search(basis)):
            issues.append(f"{y}: basis 未引用边号或地址: {basis[:40]}")
        for w in HEDGE_WORDS:
            if w in basis:
                issues.append(f"{y}: basis 含骑墙词「{w}」")

    missing = expected - got
    extra = got - expected
    if missing:
        issues.append(f"缺失年份: {sorted(missing)}")
    if extra:
        issues.append(f"多余年份: {sorted(extra)}")

    return not issues, issues


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="年份判断作答自检")
    ap.add_argument("--case")
    args = ap.parse_args(argv)

    cases = [args.case] if args.case else sorted(
        p.name for p in PROBES.iterdir() if p.is_dir()
    )
    all_ok = True
    for case in cases:
        ok, issues = verify_case(case)
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_ok = False
        print(f"[{status}] {case}")
        for i in issues:
            print(f"       - {i}")
    print()
    print("全部通过" if all_ok else "存在问题，请修正后重跑")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
