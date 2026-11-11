"""报告层「独立旁证附录」生成器（不改 v7 主报告模板、不改 Linter 契约）。

    python -m tools.ziwei_appendix --l1 l1.json --l2 l2.json --cross report.json --out 旁证附录.md

三份输入都可选，但至少要给一份：
  --l1    tools.ziwei_chart --json（L1 结构化盘面 + 断言核验）
  --l2    tools.ziwei_lookup --json（L2 解读文本信封）
  --cross tools.cross_check --json（三态对账报告）

附录是**独立文件**，不合并进主报告；每条结论都带 locator，且显式声明
「非 engine.cli 事实 / 非 query_theory 理论出处」。v7 主报告照旧跑 human_touch_linter。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridges.ziwei.envelope import ENVELOPE_VERSION, NOT_USABLE_AS  # noqa: E402
from tools.cross_check import BANNED  # noqa: E402


def _load(path: str | None, label: str) -> dict | None:
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{label} 需要 JSON 对象")
    return data


def _envelope_ok(env: dict, level: str) -> None:
    if env.get("envelope") != ENVELOPE_VERSION:
        raise ValueError(f"不是 {ENVELOPE_VERSION} 信封：{env.get('envelope')!r}")
    if env.get("level") != level:
        raise ValueError(f"期望 level={level}，实得 {env.get('level')!r}")
    missing = set(NOT_USABLE_AS) - set(env.get("not_usable_as", []))
    if missing:
        raise ValueError(f"信封缺 not_usable_as 约束：{sorted(missing)}")


def _l1_locator(env: dict) -> str:
    loc = env.get("locator", {})
    sha = str(loc.get("chart_sha256", ""))
    return f"`{loc.get('generator', 'algorithm.ts')}` / `{sha[:12]}`"


def _l2_locator(env: dict) -> str:
    loc = env.get("locator", {}) or {}
    return f"`{loc.get('shard', '?')}` offset `{loc.get('offset', '?')}`"


def _cell(value, limit: int = 150) -> str:
    if not value:
        return "—"
    s = str(value).replace("\n", " ").replace("|", "\\|").strip()
    return s if len(s) <= limit else s[:limit] + "…"


def render_appendix(l1: dict | None, l2: dict | None, cross: dict | None) -> str:
    if not any((l1, l2, cross)):
        raise ValueError("至少要给 --l1 / --l2 / --cross 之一")
    if l1:
        _envelope_ok(l1, "L1")
    if l2:
        _envelope_ok(l2, "L2")
    if cross and cross.get("report") != "cross-check/v1":
        raise ValueError("--cross 需要 tools.cross_check --json 的 cross-check/v1 报告")
    if cross:
        for r in cross.get("rows", []):
            reason = str(r.get("verdict_reason", ""))
            if any(w in reason for w in BANNED):
                raise ValueError(f"对账维度 {r.get('topic')} 的裁决理由含骑墙措辞：{reason}")

    ck = (l1 or l2 or cross or {}).get("case_key", {})
    lines = [
        "# 外部体系旁证附录 · evidence-envelope/v1",
        "",
        "> **本文件是独立旁证附录，不是主报告。** 主报告仍按 v7 人话模板与 `human_touch_linter` 产出；"
        "本附录不并入主报告、不参与其门禁。",
        "> 边界：紫微侧 **不构成 `engine.cli` 盘面事实**，**不作 `tools.query_theory` 理论出处**；"
        "两套体系的分歧由 Agent 站队，结论以八字引擎事实与理论条目为准。",
        "> 依据可复核：L1 由紫微项目排盘引擎生成，L2 由本机数据集分片定点读取；"
        "每一行都带 locator，凡 locator 缺失的断言不下结论。",
        "",
        f"- 同参主键：`{ck.get('ziwei_key', '—')}`（`{ck.get('birth_iso', '—')}` / {ck.get('gender', '—')}）",
        f"- 口径策略：八字 `{ck.get('calendar_policy', {}).get('bazi', 'jieqi')}` / "
        f"紫微 `{ck.get('calendar_policy', {}).get('ziwei', 'solar_date')}`；"
        f"真太阳时 `{ck.get('tz_policy', 'no_correction')}`",
        "- 禁用标签：`engine_fact`、`theory_source_ref`",
        "",
    ]

    # ---- 一、L1 ----
    lines += ["## 一、L1 盘面核验（紫微体系内）", ""]
    if not l1:
        lines += ["（未提供 L1 信封；本轮不对紫微宫位、星曜、四化做任何断言。）", ""]
    else:
        c = l1.get("assertion_counts", {})
        lines += [
            f"来源：`{l1.get('verified_within', 'ziwei-doushu engine')}`；"
            f"定位：{_l1_locator(l1)}；完整盘面 JSON `{l1['locator'].get('chart_json_bytes', '?')}` 字节。",
            "",
            f"**核验结果：成立 {c.get('matched', 0)} / 不成立 {c.get('mismatched', 0)} / "
            f"无法判定 {c.get('undetermined', 0)}。** 下表只回答「外部文本的盘面陈述对不对」，不推吉凶。",
            "",
            "| 盘面陈述 | 核验 | 证据（宫位 / 星曜 / 四化） | 定位 |",
            "|---|---|---|---|",
        ]
        for a in l1.get("assertions", []):
            mark = "成立" if a.get("matched") is True else ("不成立" if a.get("matched") is False else "无法判定")
            lines.append(
                f"| {_cell(a.get('text'), 80)} | {mark} | {_cell(a.get('evidence'), 170)} | "
                f"{_l1_locator(l1)} |"
            )
        s = l1.get("chart_summary", {})
        mg, opp = s.get("ming_gong") or {}, s.get("opposite") or {}
        lines += [
            "",
            f"盘面摘要：命宫 {mg.get('branch_name', '?')}宫（主星 "
            f"{','.join(mg.get('major', [])) or '空宫'}），对宫 {opp.get('name', '?')} "
            f"主星 {','.join(opp.get('major', [])) or '无'}；五行局 {s.get('wuxing_ju', '?')}；"
            f"{s.get('yin_yang_gender', '?')}。",
            "",
        ]

    # ---- 二、L2 ----
    lines += ["## 二、L2 结论层对账", ""]
    if not l2 and not cross:
        lines += ["（未提供 L2 信封或对账报告；本轮不引用紫微解读文本。）", ""]
    else:
        loc = _l2_locator(l2) if l2 else "（见对账报告 locator）"
        if l2:
            ds = l2.get("dataset") or {}
            lines += [
                f"来源：`{l2.get('source_kind')}` / 内容版本 `{ds.get('content_version')}`；"
                f"定位：{loc}；13 维字数合计 `{l2.get('text_chars_total', '?')}`。",
                "",
                "**附录不复制 3 万字原文**（含非商用引文，只留本地 `cases/_private/`）；"
                "下表只列结论摘要与定位。",
                "",
            ]
        if cross:
            cnt = cross.get("counts", {})
            lines += [
                f"三态统计：**收敛 {cnt.get('converged', 0)} / 分歧 {cnt.get('divergent', 0)} / "
                f"不核验 {cnt.get('unverifiable', 0)}**。",
                "",
                "| 维度 | 八字侧结论（带 source_ref） | 紫微侧结论（摘要） | 状态 | 裁决理由 | 定位 |",
                "|---|---|---|---|---|---|",
            ]
            decided = [r for r in cross.get("rows", []) if r.get("status") != "unverifiable"]
            for r in decided:
                bazi = r.get("bazi_claim") or "（未填）"
                if r.get("bazi_source_ref"):
                    bazi += f"（`{r['bazi_source_ref']}`）"
                lines.append(
                    f"| {r.get('topic')} | {_cell(bazi, 110)} | {_cell(r.get('ziwei_claim'), 110)} | "
                    f"`{r.get('status')}` | {_cell(r.get('verdict_reason'), 170)} | {loc} |"
                )
            if not decided:
                lines.append("| — | — | — | `unverifiable` | 待 Agent 裁决 | — |")
            lines += [
                "",
                "未取正文或未裁决的维度一律记为 `unverifiable`，不写进结论。",
                "",
            ]

    # ---- 三、口径警告 ----
    warns: list[str] = []
    for env in (l1, l2):
        for w in (env or {}).get("alignment_warnings", []):
            if w not in warns:
                warns.append(w)
    for w in (cross or {}).get("alignment_warnings", []):
        if w not in warns:
            warns.append(w)
    lines += ["## 三、口径警告（不静默对齐）", ""]
    lines += [f"- `{w}`" for w in warns] or ["- （无）"]
    lines += [
        "",
        "L1 实时排盘与 L2 v4.0 文本可能不一致：数据集按「现代修正 v2」亮度生成，"
        "紫微引擎默认已改《斗数全书》；本附录只用 L2 做结论层对账，不拿 L2 反推盘面。",
        "",
    ]

    # ---- 四、置信与依据 ----
    lines += [
        "## 四、三级置信与依据索引",
        "",
        "- **板上钉钉**：L1 中标「成立」的盘面字段（可在紫微引擎复算）、L2 的 locator 与内容版本、"
        "对账报告里带 `source_ref` 的八字侧结论。",
        "- **大概率（Agent 裁决）**：标注 `converged` / `divergent` 的裁决理由；分歧项须站队，"
        "本附录拒绝「各有道理」一类骑墙措辞。",
        "- **不核验**：紫微盘面对八字吉凶的因果解释、事件精确月份、薪资数字、岗位百分比、方位吉凶；"
        "引擎无字段，不编。",
        "",
        "| 依据 | 命令 / 文件 |",
        "|---|---|",
        "| 八字事实 | `python -m engine.cli chart --birth ... --gender ... --json` |",
        "| L1 盘面 | `python -m tools.ziwei_chart --birth ... --gender ... --json` |",
        "| L2 文本 | `python -m tools.ziwei_lookup --birth ... --gender ... --dim ... --json` |",
        "| 三态对账 | `python -m tools.cross_check --bazi ... --ziwei ... --json` |",
        "| 契约设计 | `docs/ziwei-corroboration-bridge.md` |",
        "| 验收 | `python bridges/ziwei/verify.py` |",
    ]
    for env in (l1, l2):
        if env:
            lines.append(f"| 信封 | `{env.get('envelope')}` / level `{env.get('level')}` / "
                         f"source_kind `{env.get('source_kind')}` |")
    lines += [
        "",
        "数据来源（CC BY 4.0，需署名）：紫微斗数开源解读数据集 v4.0（674,976 张命盘 × 13 维），"
        "https://github.com/Renhuai123/ziwei-doushu ，作者 王多鱼AI。"
        "解读中引用的倪海厦《天纪》原话不在该授权范围内（CC BY-NC-SA 4.0、非商用），原文不入库。",
        "",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="生成独立的紫微旁证附录 Markdown")
    ap.add_argument("--l1", default=None, help="tools.ziwei_chart --json 的 L1 信封")
    ap.add_argument("--l2", default=None, help="tools.ziwei_lookup --json 的 L2 信封")
    ap.add_argument("--cross", default=None, help="tools.cross_check --json 的对账报告")
    ap.add_argument("--out", default=None, help="输出 Markdown 文件；缺省打印到 stdout")
    args = ap.parse_args(argv)

    try:
        text = render_appendix(
            _load(args.l1, "--l1"),
            _load(args.l2, "--l2"),
            _load(args.cross, "--cross"),
        )
    except (ValueError, OSError, json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"written: {args.out}")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
