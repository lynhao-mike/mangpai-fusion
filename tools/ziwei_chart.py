"""L1 结构化盘面 CLI：在紫微体系内核验宫位、星曜与四化断言。

    python -m tools.ziwei_chart --birth "2001-12-31 06:00" --gender 坤
    python -m tools.ziwei_chart --birth "2001-12-31 06:00" --gender 坤 --json > l1.json
    python -m tools.ziwei_chart --birth "2001-12-31 06:00" --gender 坤 --claims my_claims.json --json

输出 evidence-envelope/v1（level=L1）。L1 只回答「紫微盘面长什么样、外部文本的盘面
陈述对不对」；结论层对账请用 tools.ziwei_lookup + tools.cross_check。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridges.ziwei import (  # noqa: E402
    build_case_key, build_l1_envelope, load_config,
)
from bridges.ziwei.chart_l1 import (  # noqa: E402
    DEFAULT_CLAIMS, evaluate_assertions, generate_chart,
)


def _load_claims(path: str | None) -> list[dict]:
    if not path:
        return DEFAULT_CLAIMS
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not all(isinstance(x, dict) and "check" in x for x in data):
        raise ValueError("--claims 需要 JSON 数组，每项含 id/text/check")
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="紫微 L1 结构化盘面核验（同参旁证）")
    ap.add_argument("--birth", required=True, help='与 engine.cli 同款，如 "2001-12-31 06:00"')
    ap.add_argument("--gender", required=True, help="坤 / 乾 / female / male")
    ap.add_argument("--claims", default=None, help="自定义断言 JSON 数组（缺省用内置 14 条）")
    ap.add_argument("--json", action="store_true", help="输出 L1 evidence-envelope/v1 JSON")
    ap.add_argument("--full", action="store_true", help="信封内附完整 ZiweiChart（默认只给摘要与 sha256）")
    ap.add_argument("--out", default=None, help="写文件而非 stdout")
    ap.add_argument("--config", default=None, help="指定 toml 配置路径")
    ap.add_argument("--tz-policy", default="no_correction")
    args = ap.parse_args(argv)

    try:
        ck = build_case_key(args.birth, args.gender, tz_policy=args.tz_policy)
        cfg = load_config(args.config)
        claims = _load_claims(args.claims)
        payload = generate_chart(ck, cfg)
        assertions = evaluate_assertions(payload["chart"], claims)
        env = build_l1_envelope(
            ck, payload["chart"], assertions,
            config=cfg, generator=payload.get("generator"),
            include_full_chart=args.full,
        )
    except (ValueError, LookupError, OSError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if args.json or args.out:
        text = json.dumps(env, ensure_ascii=False, indent=2)
    else:
        s = env["chart_summary"]
        loc = env["locator"]
        lines = [
            f"case_key   : {ck.ziwei_key}  ({ck.branch}时 / {ck.gender_ziwei})",
            f"命宫       : {s['ming_gong']['branch_name']}宫·{s['ming_gong']['name']}  "
            f"主星={','.join(s['ming_gong']['major']) or '（空宫）'}",
            f"对宫       : {s['opposite']['name']} 主星={','.join(s['opposite']['major']) or '（无）'}",
            f"身宫       : {s['shen_gong']['name']}   五行局={s['wuxing_ju']}   {s['yin_yang_gender']}",
            f"chart_sha256: {loc['chart_sha256']}",
            "",
            "盘面断言核验：",
        ]
        for a in env["assertions"]:
            mark = "成立" if a["matched"] is True else ("不成立" if a["matched"] is False else "无法判定")
            lines.append(f"  [{mark}] {a['text']}")
            lines.append(f"          {a['evidence']}")
        c = env["assertion_counts"]
        lines += [
            "",
            f"合计：成立 {c['matched']} / 不成立 {c['mismatched']} / 无法判定 {c['undetermined']}",
            "",
            "边界：L1 是紫微体系内的盘面核验，对本仓库仍是旁证；"
            "不作 engine.cli 事实、不作 query_theory 理论出处。",
        ]
        text = "\n".join(lines) + "\n"

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"written: {args.out}")
    else:
        print(text, end="" if text.endswith("\n") else "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
