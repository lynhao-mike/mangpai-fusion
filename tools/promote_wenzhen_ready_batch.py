"""Promote Wenzhen READY staging candidates to formal case directories.

This helper reads the reviewed staging manifest and writes the four required formal
case files for a selected batch. It is intended for human-approved small batches
after promotion preflight has passed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
from typing import Any

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
STAGING_JSONL = REPO_ROOT / "cases" / "raw_feedback" / "parsed" / "wenzhen_repan_top30_staging_manifest.jsonl"
PROMOTION_PREFLIGHT_SUMMARY = (
    REPO_ROOT / "cases" / "raw_feedback" / "parsed" / "wenzhen_repan_top30_promotion_preflight-summary.json"
)
TODAY = "2026-06-08"

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
JIAZI: list[str] = []
for i in range(60):
    g = GAN[i % 10]
    z = ZHI[i % 12]
    if (GAN.index(g) % 2) == (ZHI.index(z) % 2):
        JIAZI.append(g + z)

BRANCH_HIDDEN_STEMS: dict[str, list[tuple[str, str, float]]] = {
    "子": [("癸", "主气", 1.0)],
    "丑": [("己", "主气", 1.0), ("癸", "中气", 0.3), ("辛", "余气", 0.2)],
    "寅": [("甲", "主气", 1.0), ("丙", "中气", 0.3), ("戊", "余气", 0.2)],
    "卯": [("乙", "主气", 1.0)],
    "辰": [("戊", "主气", 1.0), ("乙", "中气", 0.3), ("癸", "余气", 0.2)],
    "巳": [("丙", "主气", 1.0), ("庚", "中气", 0.3), ("戊", "余气", 0.2)],
    "午": [("丁", "主气", 1.0), ("己", "中气", 0.3)],
    "未": [("己", "主气", 1.0), ("丁", "中气", 0.3), ("乙", "余气", 0.2)],
    "申": [("庚", "主气", 1.0), ("壬", "中气", 0.3), ("戊", "余气", 0.2)],
    "酉": [("辛", "主气", 1.0)],
    "戌": [("戊", "主气", 1.0), ("辛", "中气", 0.3), ("丁", "余气", 0.2)],
    "亥": [("壬", "主气", 1.0), ("甲", "中气", 0.3)],
}

TYPE_MAP = {
    "occupation": "职业",
    "income": "财运",
    "health": "健康",
    "family": "六亲",
    "marriage": "婚姻",
    "education": "学历",
    "children": "子女",
    "other": "其他",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Promote selected Wenzhen READY staging candidates.")
    parser.add_argument("--start-rank", type=int, required=True, help="First staging rank to promote, 1-based.")
    parser.add_argument("--count", type=int, default=5, help="Number of candidates to promote.")
    parser.add_argument("--batch-label", default="问真 staging 小批量正式转案", help="Human-readable batch label.")
    parser.add_argument("--dry-run", action="store_true", help="Preview selected cases without writing files.")
    args = parser.parse_args(argv)

    rows = _load_staging()
    selected = [row for row in rows if int(row["rank"]) >= args.start_rank][: args.count]
    if len(selected) != args.count:
        raise ValueError(f"selected {len(selected)} rows, expected {args.count}")

    promoted: list[dict[str, Any]] = []
    for staging in selected:
        if staging.get("promotion_blocking_flags"):
            raise ValueError(f"candidate has blocking flags: {staging['raw_id']}")
        draft = _load_draft(REPO_ROOT / staging["draft_path"])
        item = _item_from_staging(staging)
        case_dir = REPO_ROOT / item["case_dir"]
        promoted.append({"case_id": item["case_id"], "raw_id": item["raw_id"], "case_dir": item["case_dir"]})
        if args.dry_run:
            continue
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "input.md").write_text(_render_input(item, staging, draft, args.batch_label), encoding="utf-8")
        (case_dir / "analysis.md").write_text(_render_analysis(item, staging, args.batch_label), encoding="utf-8")
        (case_dir / "feedback.md").write_text(_render_feedback(item, draft, args.batch_label), encoding="utf-8")
        (case_dir / "statement_index.json").write_text(
            json.dumps(_statement_index(item, draft), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(json.dumps({"dry_run": args.dry_run, "promoted": promoted, "count": len(promoted)}, ensure_ascii=False, indent=2))
    return 0


def _load_staging() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in STAGING_JSONL.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rows.append(row)
    return sorted(rows, key=lambda item: int(item["rank"]))


def _load_draft(path: pathlib.Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"```ya?ml\s*\n(?P<body>.*?)\n```", text, re.S | re.I)
    if not match:
        raise ValueError(f"draft lacks yaml block: {path}")
    data = yaml.safe_load(match.group("body"))
    if not isinstance(data, dict):
        raise ValueError(f"draft yaml is not mapping: {path}")
    data["_raw_excerpt"] = text.split("## 原始反馈摘录", 1)[-1].strip()
    return data


def _item_from_staging(staging: dict[str, Any]) -> dict[str, Any]:
    case_id = staging["suggested_case_id"]
    return {
        "case_id": case_id,
        "raw_id": staging["raw_id"],
        "case_dir": f"cases/{case_id}",
        "draft_path": staging["draft_path"],
        "source_index_path": staging["source_index_path"],
    }


def _render_input(item: dict[str, Any], staging: dict[str, Any], draft: dict[str, Any], batch_label: str) -> str:
    bazi = staging["bazi"]
    pillars = [bazi[i : i + 2] for i in range(0, 8, 2)]
    birth = staging["birth"]
    dayun = _build_dayun(staging, pillars[1])
    payload = {
        "schema_version": "1.2.0",
        "case_meta": {
            "case_id": item["case_id"],
            "立案日期": TODAY,
            "命主代号": item["raw_id"],
            "策略": "B",
            "来源": batch_label,
            "原始反馈ID": item["raw_id"],
            "source_index_path": item["source_index_path"],
            "draft_path": item["draft_path"],
            "staging_manifest_path": "cases/raw_feedback/parsed/wenzhen_repan_top30_staging_manifest.jsonl",
            "promotion_preflight_summary": "cases/raw_feedback/parsed/wenzhen_repan_top30_promotion_preflight-summary.json",
        },
        "birth": {
            "性别": birth["性别"],
            "乾坤": birth["乾坤"],
            "公历": birth["公历"],
            "农历": staging.get("base", {}).get("Lunar", birth.get("农历", "待补")),
            "出生地": birth["出生地脱敏"],
            "出生地原始摘录": birth.get("出生地", ""),
            "真太阳时校正": _as_bool(birth.get("真太阳时校正")),
            "太阳时": birth.get("太阳时", staging.get("base", {}).get("Sun", "")),
        },
        "四柱": {"年柱": pillars[0], "月柱": pillars[1], "日柱": pillars[2], "时柱": pillars[3]},
        "藏干": _hidden_stems_for_pillars(pillars),
        "大运": dayun,
        "神煞": _shensha(staging),
        "十二长生": _changsheng(staging, pillars),
        "known_facts": _known_facts(draft),
        "提问": draft.get("提问") or ["用于理论验证：依据真实反馈事件回测命局结构、应期与功能域规则。"],
    }
    fingerprint = hashlib.md5(f"{payload['birth']['性别']}|{payload['birth']['公历']}".encode("utf-8")).hexdigest()[:12]
    return (
        f"# Case {item['case_id']} · 输入信息\n\n"
        f"> {batch_label}；raw_id：`{item['raw_id']}`。\n\n"
        f"**立案日期**：{TODAY}  \n"
        f"**命主代号**：{item['raw_id']}  \n"
        f"**采集人**：mangpai-fusion wenzhen promotion  \n"
        f"**指纹**：`{fingerprint}`（{payload['birth']['性别']} | {payload['birth']['公历']}）\n\n"
        "---\n\n"
        "## 一、八字盘\n\n"
        "```yaml\n"
        f"{yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)}"
        "```\n\n"
        "## 二、来源追踪\n\n"
        f"- raw_id：`{item['raw_id']}`\n"
        f"- 来源草稿：`{item['draft_path']}`\n"
        f"- 来源索引：`{item['source_index_path']}`\n"
        "- staging manifest：`cases/raw_feedback/parsed/wenzhen_repan_top30_staging_manifest.jsonl`\n"
        "- promotion preflight summary：`cases/raw_feedback/parsed/wenzhen_repan_top30_promotion_preflight-summary.json`\n\n"
        "## 三、分析重点\n\n"
        "- 策略 B：围绕真实反馈年表做命局结构、功能域与应期回测。\n\n"
        "## 四、隐私设置\n\n"
        "- [x] 默认（脱敏归档，可 push 到 GitHub）\n"
        "- [ ] 隐私（不 push，仅本地）\n"
    )


def _render_analysis(item: dict[str, Any], staging: dict[str, Any], batch_label: str) -> str:
    return (
        f"# Case {item['case_id']} · 分析记录\n\n"
        "## 一、转案说明\n\n"
        f"- 转案日期：{TODAY}\n"
        f"- 转案批次：{batch_label}\n"
        f"- raw_id：`{item['raw_id']}`\n"
        f"- 来源草稿：`{item['draft_path']}`\n"
        f"- 来源索引：`{item['source_index_path']}`\n"
        "- staging manifest：`cases/raw_feedback/parsed/wenzhen_repan_top30_staging_manifest.jsonl`\n"
        "- promotion preflight summary：`cases/raw_feedback/parsed/wenzhen_repan_top30_promotion_preflight-summary.json`\n\n"
        "## 二、当前状态\n\n"
        "本文件为正式 case 初始化分析记录；尚未生成命理师报告。\n\n"
        "## 三、待分析重点\n\n"
        "- 命局结构与问真四柱核对。\n"
        "- 已知事实年表与大运、流年应期回测。\n"
        "- 多流派功能域结论与后续 statement_index 绑定。\n"
    )


def _render_feedback(item: dict[str, Any], draft: dict[str, Any], batch_label: str) -> str:
    lines = [
        f"# Case {item['case_id']} · 命主反馈",
        "",
        f"> {batch_label}；本文件先迁移原 known_facts，后续报告断语反馈再补 `[S-...] [y/n/?/skip]`。",
        "",
        f"**反馈日期**：{TODAY}  ",
        "**采集方式**：问真真实反馈样本迁移  ",
        "**关联报告**：待生成  ",
        f"**关联索引**：cases/{item['case_id']}/statement_index.json  ",
        "",
        "---",
        "",
        "## 一、来源追踪",
        "",
        f"- raw_id：`{item['raw_id']}`",
        f"- 来源草稿：`{item['draft_path']}`",
        f"- 来源索引：`{item['source_index_path']}`",
        "- staging manifest：`cases/raw_feedback/parsed/wenzhen_repan_top30_staging_manifest.jsonl`",
        "- promotion preflight summary：`cases/raw_feedback/parsed/wenzhen_repan_top30_promotion_preflight-summary.json`",
        "",
        "## 二、已知事实年表",
        "",
        "| 年份 | 类型 | 事实摘录 |",
        "|---:|---|---|",
    ]
    for fact in _known_facts(draft):
        lines.append(f"| {fact.get('年份', '')} | {fact.get('类型', '')} | {str(fact.get('事件', '')).replace('|', '/')} |")
    lines.extend([
        "",
        "## 三、断语反馈占位",
        "",
        "> 待正式分析报告生成后，将报告中的 `反馈：[S-...] [ ]` 复制到此处并标注。",
        "",
    ])
    return "\n".join(lines)


def _statement_index(item: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
    statements = []
    for idx, fact in enumerate(_known_facts(draft), start=1):
        digest = hashlib.md5(f"{item['case_id']}|{idx}|{fact.get('年份')}|{fact.get('事件')}".encode("utf-8")).hexdigest()[:6]
        statements.append(
            {
                "statement_id": f"S-{item['raw_id'].replace('RF-2026-', 'RF')}-{digest}",
                "domain": _fact_domain(str(fact.get("类型", "其他"))),
                "summary": f"{fact.get('年份', '')}：{fact.get('事件', '')}",
                "status": "observed_fact",
                "section": "known_facts_migrated",
                "rule_ids": [],
                "schools": [],
                "source_raw_id": item["raw_id"],
            }
        )
    return {"case_id": item["case_id"], "generated_at": TODAY, "statements": statements}


def _known_facts(draft: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for row in draft.get("known_facts") or []:
        typ = TYPE_MAP.get(str(row.get("type", "other")), "其他")
        out.append({"年份": int(row["year"]), "类型": typ, "事件": str(row.get("desc", ""))})
    return out


def _fact_domain(typ: str) -> str:
    return {"职业": "事业", "财运": "财运", "健康": "健康", "六亲": "家庭", "婚姻": "婚姻", "学历": "学业"}.get(typ, "其他")


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"true", "1", "yes", "y"}


def _hidden_stems_for_pillars(pillars: list[str]) -> dict[str, list[dict[str, Any]]]:
    keys = ["年支", "月支", "日支", "时支"]
    return {
        key: [{"干": gan, "类型": typ, "力量": li} for gan, typ, li in BRANCH_HIDDEN_STEMS[pillar[1]]]
        for key, pillar in zip(keys, pillars)
    }


def _changsheng(staging: dict[str, Any], pillars: list[str]) -> dict[str, str]:
    keys = {"Y": "年支", "M": "月支", "D": "日支", "H": "时支"}
    out = {"日干": pillars[2][0]}
    for src, target in keys.items():
        parts = str(staging["pillars"][src]).split(",")
        out[target] = parts[4] if len(parts) > 4 else "长生"
    return out


def _shensha(staging: dict[str, Any]) -> dict[str, list[str]]:
    keys = {"Y": "年柱", "M": "月柱", "D": "日柱", "H": "时柱"}
    out: dict[str, list[str]] = {}
    for src, target in keys.items():
        parts = str(staging["pillars"][src]).split(",")
        out[target] = [] if len(parts) < 8 or parts[7] == "_" else parts[7].split("/")
    return out


def _build_dayun(staging: dict[str, Any], month_pillar: str) -> dict[str, Any]:
    birth_year = int(str(staging["birth"]["公历"])[:4])
    match = re.search(r"出生后(\d+)年", str(staging.get("start", "")))
    qiyun_sui = int(match.group(1)) if match else 5
    qiyun_sui = max(1, min(11, qiyun_sui))
    qiyun_year = birth_year + qiyun_sui
    shun_ni = "顺" if staging["qian_kun"] == "乾" else "逆"
    start_idx = JIAZI.index(month_pillar)
    steps = []
    for i in range(8):
        idx = (start_idx + (i + 1 if shun_ni == "顺" else -(i + 1))) % 60
        start_year = qiyun_year + i * 10
        start_age = qiyun_sui + i * 10
        steps.append(
            {
                "序号": i + 1,
                "干支": JIAZI[idx],
                "起讫": f"{start_year}-{start_year + 10}",
                "起岁": start_age,
                "止岁": start_age + 9,
            }
        )
    return {"起运岁": qiyun_sui, "起运年": qiyun_year, "顺逆": shun_ni, "排布": steps}


if __name__ == "__main__":
    raise SystemExit(main())
