"""紫微旁证查表 CLI（与 engine.cli 同参）。

    python -m tools.ziwei_lookup --birth "2001-12-31 06:00" --gender 坤 --json
    python -m tools.ziwei_lookup --birth "2001-12-31 06:00" --gender 坤 --dim career,wealth --json

输出 evidence-envelope/v1。紫微侧只作结论层旁证，
不得用作 engine.cli 事实或 query_theory 理论依据。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridges.ziwei import build_case_key, build_envelope, load_config, lookup  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="紫微 v4.0 解读数据集只读查表（同参旁证）")
    ap.add_argument("--birth", required=True, help='与 engine.cli 同款，如 "2001-12-31 06:00"')
    ap.add_argument("--gender", required=True, help="坤 / 乾 / female / male")
    ap.add_argument("--dim", default="", help="逗号分隔维度；留空只给元数据与字数，不输出正文")
    ap.add_argument("--json", action="store_true", help="输出 evidence-envelope/v1 JSON")
    ap.add_argument("--raw", action="store_true", help="输出查表器原始 payload（调试用）")
    ap.add_argument("--config", default=None, help="指定 toml 配置路径")
    ap.add_argument("--tz-policy", default="no_correction", help="默认 no_correction，与数据集口径一致")
    args = ap.parse_args(argv)

    try:
        ck = build_case_key(args.birth, args.gender, tz_policy=args.tz_policy)
        cfg = load_config(args.config)
        dims = [d.strip() for d in args.dim.split(",") if d.strip()]
        payload = lookup(ck, dims, cfg)
    except (ValueError, LookupError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if args.raw:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.json:
        print(json.dumps(build_envelope(ck, payload, config=cfg), ensure_ascii=False, indent=2))
        return 0

    rec, loc = payload["record"], payload["locator"]
    print(f"case_key  : {ck.ziwei_key}  ({ck.branch}时 / {ck.gender_ziwei})")
    print(f"八字同参  : {ck.birth_iso} {ck.gender}")
    print(f"locator   : {loc['shard']}  offset={loc['offset']}  length={loc['length']}")
    print(f"命宫主星  : {rec['ms'] or '（空宫）'}   13 维合计 {payload['text_chars_total']} 字")
    print("维度字数  : " + ", ".join(f"{k}={v}" for k, v in rec["t"].items()))
    if dims:
        for d in dims:
            print(f"\n--- {d} ---\n{rec['c'][d]}")
    else:
        print("\n（未指定 --dim，未输出正文；用 --dim career,wealth 取结论文本）")
    print("\nalignment_warnings: " + ", ".join(ck.alignment_warnings))
    print("边界：紫微为结论层旁证，不作 engine.cli 事实 / query_theory 理论依据")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
