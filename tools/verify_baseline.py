"""重构基线尺子：一条命令跑出四项基线指标，供重构前后对比。

依据 docs/adr/ADR-004-hub-commander-authority.md 红线三：
重构前后必须用同一把尺子，任一指标下降须写明原因。

用法：
    python -m tools.verify_baseline                 # 跑基线并打印
    python -m tools.verify_baseline --save          # 跑完写入 META/baseline-v1.json
    python -m tools.verify_baseline --compare       # 与已存基线对比，任一下降退出码 1
    python -m tools.verify_baseline --quick         # 只跑 20 盘（调试用，不作验收）

四项指标：
    pytest            通过数（下降即退步）
    engine_audit      481 盘底层事实错误数（上升即退步）
    relations_audit   关系图校验是否全通过（由通转过即退步）
    zuogong_probe     宫制星候选覆盖盘数（下降即退步）

注意：本工具不自己实现任何校验逻辑，只解析既有校验器的输出与退出码。
校验器本身才是判据来源，避免「验证自己」。
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
BASELINE = ROOT / "META" / "baseline-v1.json"


def run(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run([PY, *args], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def measure(quick: bool) -> dict:
    out: dict = {}

    rc, text = run(["-m", "pytest", "-q"])
    m = re.search(r"(\d+) passed", text)
    out["pytest_passed"] = int(m.group(1)) if m else 0
    m = re.search(r"(\d+) failed", text)
    out["pytest_failed"] = int(m.group(1)) if m else 0
    out["pytest_rc"] = rc

    limit = ["--limit", "20"] if quick else []
    rc, text = run(["-X", "utf8", "-m", "tools.engine_audit", *limit])
    m = re.search(r"有问题 (\d+)", text)
    out["audit_errors"] = int(m.group(1)) if m else -1
    out["audit_rc"] = rc

    rc, text = run(["-X", "utf8", "-m", "tools.relations_audit", *limit])
    out["relations_ok"] = rc == 0
    out["relations_rc"] = rc

    rc, text = run(["-X", "utf8", "-m", "tools.zuogong_probe", *limit])
    m = re.search(r"有宫制星候选 (\d+)", text)
    out["zuogong_charts"] = int(m.group(1)) if m else -1
    m = re.search(r"actor=D\.b (\d+)", text)
    out["zuogong_day_branch"] = int(m.group(1)) if m else -1
    out["zuogong_rc"] = rc
    return out


def regressions(old: dict, new: dict) -> list[str]:
    """指标下降清单。"""
    bad: list[str] = []
    if new["pytest_failed"] > old["pytest_failed"]:
        bad.append(f"pytest 失败数 {old['pytest_failed']} → {new['pytest_failed']}")
    if new["pytest_passed"] < old["pytest_passed"]:
        bad.append(f"pytest 通过数 {old['pytest_passed']} → {new['pytest_passed']}")
    if new["audit_errors"] > old["audit_errors"]:
        bad.append(f"底层体检错误数 {old['audit_errors']} → {new['audit_errors']}")
    if old["relations_ok"] and not new["relations_ok"]:
        bad.append("关系图校验由通过变为失败")
    if new["zuogong_charts"] < old["zuogong_charts"]:
        bad.append(f"宫制星覆盖盘数 {old['zuogong_charts']} → {new['zuogong_charts']}")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    new = measure(args.quick)
    print(json.dumps(new, ensure_ascii=False, indent=2))

    if args.save:
        new["quick"] = args.quick
        BASELINE.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\n已写入 {BASELINE.relative_to(ROOT)}")

    if args.compare:
        if not BASELINE.exists():
            print("\n没有已存基线，先跑一次 --save")
            return 2
        old = json.loads(BASELINE.read_text(encoding="utf-8"))
        if bool(old.get("quick")) != args.quick:
            print("\n注意：基线与本次的 quick 口径不同，盘数类指标不可直接比较")
        bad = regressions(old, new)
        if bad:
            print("\n【指标下降】")
            for line in bad:
                print("  -", line)
            return 1
        print("\n【基线未退步】")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
