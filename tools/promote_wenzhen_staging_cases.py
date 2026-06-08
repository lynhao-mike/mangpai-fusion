"""Promote Wenzhen staging records into formal case directories.

This tool is intentionally conservative:
- --dry-run prints the exact files that would be created.
- It only promotes records with empty promotion_blocking_flags.
- It never touches theory weights or feedback calibration files.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
STAGING_JSONL = REPO_ROOT / "cases/raw_feedback/parsed/wenzhen_repan_top30_staging_manifest.jsonl"
FIRST5_PLAN = REPO_ROOT / "cases/raw_feedback/parsed/wenzhen_repan_first5_promotion_plan.json"
CASES_ROOT = REPO_ROOT / "cases"

GANZHI = [
    "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉",
    "甲戌", "乙亥", "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未",
    "甲申", "乙酉", "丙戌", "丁亥", "戊子", "己丑", "庚寅", "辛卯", "壬辰", "癸巳",
    "甲午", "乙未", "丙申", "丁酉", "戊戌", "己亥", "庚子", "辛丑", "壬寅", "癸卯",
    "甲辰", "乙巳", "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥", "壬子", "癸丑",
    "甲寅", "乙卯", "丙辰", "丁巳", "戊午", "己未", "庚申", "辛酉", "壬戌", "癸亥",
]
YANG_GAN = {"甲", "丙", "戊", "庚", "壬"}
BRANCH_HIDDEN = {
    "子": [("癸", "主气", 1.0)],
    "丑": [("己", "主气", 0.6), ("癸", "中气", 0.3), ("辛", "余气", 0.1)],
    "寅": [("甲", "主气", 0.6), ("丙", "中气", 0.3), ("戊", "余气", 0.1)],
    "卯": [("乙", "主气", 1.0)],
    "辰": [("戊", "主气", 0.6), ("乙", "中气", 0.3), ("癸", "余气", 0.1)],
    "巳": [("丙", "主气", 0.6), ("庚", "中气", 0.3), ("戊", "余气", 0.1)],
    "午": [("丁", "主气", 0.7), ("己", "中气", 0.3)],
    "未": [("己", "主气", 0.6), ("丁", "中气", 0.3), ("乙", "余气", 0.1)],
    "申": [("庚", "主气", 0.6), ("壬", "中气", 0.3), ("戊", "余气", 0.1)],
    "酉": [("辛", "主气", 1.0)],
    "戌": [("戊", "主气", 0.6), ("辛", "中气", 0.3), ("丁", "余气", 0.1)],
    "亥": [("壬", "主气", 0.7), ("甲", "中气", 0.3)],
}
FACT_TYPE_MAP = {
    "other": "其他",
    "occupation": "职业",
    "health": "健康",
    "income": "财运",
    "family": "六亲",
    "marriage": "婚姻",
    "education": "学历",
}
PILLAR_KEYS = [("Y", "年柱", "年支"), ("M", "月柱", "月支"), ("D", "日柱", "日支"), ("H", "时柱", "时支")]


@dataclass
class PromotionCase:
    raw_id: str
    case_id: str
    case_dir: Path
    input_path: Path
    analysis_path: Path
    feedback_path: Path
    statement_index_path: Path
    report_path: Path


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def load_first5_ids() -> list[str]:
    data = json.loads(FIRST5_PLAN.read_text(encoding="utf-8"))
    return [item["raw_id"] for item in data["plans"]]


def parse_draft_yaml(draft_path: Path) -> dict[str, Any]:
    text = draft_path.read_text(encoding="utf-8")
    match = re.search(r"```ya?ml\s*\n(?P<body>.*?)\n```", text, re.S | re.I)
    if not match:
        return {}
    return yaml.safe_load(match.group("body")) or {}


def split_pillar(raw: str) -> dict[str, Any]:
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) < 8:
        raise ValueError(f"pillar summary has too few fields: {raw}")
    return {
        "gan": parts[1],
        "zhi": parts[2],
        "changsheng": parts[4],
        "void": parts[5],
        "nayin": parts[6],
        "shensha": [] if parts[7] == "_" else [x for x in parts[7].split("/") if x and x != "_"],
    }


def build_pillars(record: dict[str, Any]) -> dict[str, str]:
    out = {}
    for source_key, pillar_key, _branch_key in PILLAR_KEYS:
        parsed = split_pillar(record["pillars"][source_key])
        out[pillar_key] = parsed["gan"] + parsed["zhi"]
    return out


def build_canggan(pillars: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    out = {}
    for _source_key, pillar_key, branch_key in PILLAR_KEYS:
        branch = pillars[pillar_key][1]
        out[branch_key] = [
            {"干": gan, "类型": kind, "力量": strength}
            for gan, kind, strength in BRANCH_HIDDEN[branch]
        ]
    return out


def build_shensha(record: dict[str, Any]) -> dict[str, list[str]]:
    out = {}
    for source_key, pillar_key, _branch_key in PILLAR_KEYS:
        out[pillar_key] = split_pillar(record["pillars"][source_key])["shensha"]
    return out


def build_changsheng(record: dict[str, Any], pillars: dict[str, str]) -> dict[str, str]:
    out = {"日干": pillars["日柱"][0]}
    for source_key, _pillar_key, branch_key in PILLAR_KEYS:
        out[branch_key] = split_pillar(record["pillars"][source_key])["changsheng"]
    return out


def dayun_direction(record: dict[str, Any], pillars: dict[str, str]) -> str:
    year_gan = pillars["年柱"][0]
    qian_kun = record["qian_kun"]
    yang_year = year_gan in YANG_GAN
    return "顺" if (qian_kun == "乾" and yang_year) or (qian_kun == "坤" and not yang_year) else "逆"


def next_ganzhi(gz: str, direction: str, step: int) -> str:
    idx = GANZHI.index(gz)
    delta = step if direction == "顺" else -step
    return GANZHI[(idx + delta) % len(GANZHI)]


def parse_qiyun_sui(start_text: str) -> int:
    match = re.search(r"出生后(\d+)年", start_text)
    if not match:
        return 1
    value = int(match.group(1))
    return max(1, min(11, value))


def build_dayun(record: dict[str, Any], pillars: dict[str, str]) -> dict[str, Any]:
    birth_year = int(str(record["birth"]["公历"])[:4])
    qiyun_sui = parse_qiyun_sui(record.get("start") or record.get("base", {}).get("Start", ""))
    qiyun_year = birth_year + int(qiyun_sui)
    direction = dayun_direction(record, pillars)
    month_gz = pillars["月柱"]
    steps = []
    for idx in range(10):
        start_year = qiyun_year + idx * 10
        start_age = qiyun_sui + idx * 10
        steps.append({
            "序号": idx + 1,
            "干支": next_ganzhi(month_gz, direction, idx + 1),
            "起讫": f"{start_year}-{start_year + 10}",
            "起岁": start_age,
            "止岁": start_age + 9,
        })
    return {
        "起运描述": record.get("start") or record.get("base", {}).get("Start", ""),
        "起运岁": qiyun_sui,
        "起运年": qiyun_year,
        "顺逆": direction,
        "排布": steps,
    }


def normalize_birth(record: dict[str, Any]) -> dict[str, Any]:
    birth = dict(record["birth"])
    birth["真太阳时校正"] = str(birth.get("真太阳时校正", "true")).lower() == "true"
    birth["公历"] = str(birth.get("公历", "")).replace("：", ":").replace(" 分", "")
    birth["太阳时"] = str(birth.get("太阳时", "")).replace("：", ":").replace(" 分", "")
    birth["出生地"] = birth.get("出生地脱敏") or birth.get("出生地") or "已脱敏"
    return birth


def normalize_known_facts(draft: dict[str, Any]) -> list[dict[str, Any]]:
    facts = []
    for item in draft.get("known_facts") or []:
        raw_type = str(item.get("type", "other"))
        facts.append({
            "年份": item.get("year"),
            "类型": FACT_TYPE_MAP.get(raw_type, "其他"),
            "事件": item.get("desc") or item.get("event") or item.get("content") or "",
            "内容": item.get("content") or item.get("desc") or item.get("event") or "",
        })
    return facts


def render_yaml_block(data: dict[str, Any]) -> str:
    return "```yaml\n" + yaml.safe_dump(data, allow_unicode=True, sort_keys=False).strip() + "\n```"


def build_case(record: dict[str, Any]) -> tuple[PromotionCase, dict[str, str]]:
    case_id = record["suggested_case_id"]
    case_dir = CASES_ROOT / case_id
    report_path = REPO_ROOT / "reports" / f"{case_id}-analyst-report.md"
    target = PromotionCase(
        raw_id=record["raw_id"],
        case_id=case_id,
        case_dir=case_dir,
        input_path=case_dir / "input.md",
        analysis_path=case_dir / "analysis.md",
        feedback_path=case_dir / "feedback.md",
        statement_index_path=case_dir / "statement_index.json",
        report_path=report_path,
    )
    draft = parse_draft_yaml(REPO_ROOT / record["draft_path"])
    pillars = build_pillars(record)
    input_sections = [
        f"# {case_id} · 输入信息",
        "",
        render_yaml_block({
            "schema_version": "1.2.0",
            "case_meta": {
                "case_id": case_id,
                "立案日期": "2026-06-08",
                "命主代号": record["raw_id"],
                "策略": "B",
                "来源": "真实反馈990案例 + 问真八字 APP 补盘",
                "原始反馈ID": record["raw_id"],
                "转案状态": "formal_promoted_from_wenzhen_staging",
            },
        }),
        "",
        render_yaml_block({"birth": normalize_birth(record)}),
        "",
        render_yaml_block({"四柱": pillars}),
        "",
        render_yaml_block({"藏干": build_canggan(pillars)}),
        "",
        render_yaml_block({"大运": build_dayun(record, pillars)}),
        "",
        render_yaml_block({"神煞": build_shensha(record)}),
        "",
        render_yaml_block({"十二长生": build_changsheng(record, pillars)}),
        "",
        render_yaml_block({
            "三宫元": {
                "胎元": record.get("base", {}).get("Tai", "待复核"),
                "命宫": record.get("base", {}).get("Ming", "待复核"),
                "身宫": record.get("base", {}).get("Shen", "待复核"),
                "司令": record.get("base", {}).get("Siling", "待复核"),
                "空亡": record.get("void", record.get("base", {}).get("Void", "待复核")),
            }
        }),
        "",
        render_yaml_block({"known_facts": normalize_known_facts(draft)}),
        "",
        render_yaml_block({"提问": ["用于理论验证：依据真实反馈事件回测命局结构、应期与功能域规则。"]}),
        "",
        "## 转案追踪",
        "",
        f"- 原始反馈 ID：{record['raw_id']}",
        f"- 来源草稿：{record['draft_path']}",
        f"- 来源索引：{record['source_index_path']}",
        f"- 关联命理师报告：[{target.report_path.name}](../../reports/{target.report_path.name})",
        "- 注意：大运排布由问真起运描述与月柱顺逆机械展开，后续可人工复核。",
        "",
    ]
    feedback = [
        f"# {case_id} · 断语级反馈",
        "",
        f"- 原始反馈 ID：{record['raw_id']}",
        f"- 来源草稿：{record['draft_path']}",
        "- ingest 入口：`python tools/feedback_ingest.py {}`".format(case_id),
        "- 标注约定：仅对正式报告中的 `[S-...]` 使用 `[y]` / `[n]` / `[?]` / `[skip]`。",
        "",
        "## 已知事实年表",
        "",
    ]
    for fact in normalize_known_facts(draft):
        feedback.append(f"- {fact.get('年份', '未知')} · {fact['类型']} · {fact['事件']}")
    feedback.extend(["", "## 断语标注区", "", "<!-- 生成报告后在此按 [S-...] 补充标注。 -->", ""])
    analysis = [
        f"# {case_id} · 分析归档",
        "",
        "## 转案说明",
        "",
        f"- 原始反馈 ID：{record['raw_id']}",
        f"- 问真四柱：{record['bazi']}",
        f"- 关联输入：[{target.input_path.name}](input.md)",
        f"- 关联反馈：[{target.feedback_path.name}](feedback.md)",
        f"- 关联报告：[{target.report_path.name}](../../reports/{target.report_path.name})",
        "",
        "## Pipeline 分析",
        "",
        "待运行正式 pipeline 后回填。",
        "",
    ]
    statement_index = {
        "schema_version": "statement-index/formal-wenzhen-v0.1",
        "case_id": case_id,
        "source": {
            "raw_id": record["raw_id"],
            "draft_path": record["draft_path"],
            "staging_manifest": _rel(STAGING_JSONL),
        },
        "status": "initialized_pending_pipeline",
        "statements": [],
        "archive_links": {
            "input": _rel(target.input_path),
            "analysis": _rel(target.analysis_path),
            "feedback": _rel(target.feedback_path),
            "analyst_report": _rel(target.report_path),
        },
    }
    files = {
        _rel(target.input_path): "\n".join(input_sections),
        _rel(target.analysis_path): "\n".join(analysis),
        _rel(target.feedback_path): "\n".join(feedback),
        _rel(target.statement_index_path): json.dumps(statement_index, ensure_ascii=False, indent=2) + "\n",
    }
    return target, files


def select_records(batch: str) -> list[dict[str, Any]]:
    records = load_jsonl(STAGING_JSONL)
    if batch == "first5":
        wanted = set(load_first5_ids())
        return [record for record in records if record["raw_id"] in wanted]
    if batch == "ready26":
        return [record for record in records if not record.get("promotion_blocking_flags")]
    raise ValueError(batch)


def promote(batch: str, *, dry_run: bool) -> dict[str, Any]:
    records = select_records(batch)
    cases = []
    for record in records:
        if record.get("promotion_blocking_flags"):
            continue
        target, files = build_case(record)
        cases.append({
            "raw_id": target.raw_id,
            "case_id": target.case_id,
            "case_dir": _rel(target.case_dir),
            "files": list(files.keys()),
            "report": _rel(target.report_path),
            "exists": target.case_dir.exists(),
        })
        if not dry_run:
            if target.case_dir.exists():
                raise FileExistsError(f"target case dir already exists: {_rel(target.case_dir)}")
            target.case_dir.mkdir(parents=True, exist_ok=False)
            for rel_path, content in files.items():
                path = REPO_ROOT / rel_path
                path.write_text(content, encoding="utf-8")
    return {
        "schema_version": "wenzhen-formal-promotion/v0.1",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "dry_run": dry_run,
        "batch": batch,
        "case_count": len(cases),
        "cases": cases,
        "policy": "No theory weight files are modified.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", choices=("first5", "ready26"), default="first5")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(promote(args.batch, dry_run=args.dry_run), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
