from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "sources" / "tiaohou_ditiansui"
OUTPUT_YAML = ROOT / "theory" / "tiaohou_ditiansui" / "index.yaml"
OUTPUT_JSON = ROOT / "theory" / "tiaohou_ditiansui" / "_extracted_rules.json"
SUMMARY_MD = ROOT / "theory" / "tiaohou_ditiansui" / "_extracted_rules_summary.md"

SOURCE_FILES = sorted(path for path in SOURCE_DIR.glob("*.md") if path.name != "README.md")

NOISE_PATTERNS = [
    re.compile(r"^[\s\u3000\t]*$"),
    re.compile(r"^滴天髓目录$"),
    re.compile(r"^通神论六亲论$"),
    re.compile(r"^(通神论|六亲论)$"),
    re.compile(r"^[一二三四五六七八九十百]+、?.{0,10}$"),
    re.compile(r"^[甲乙丙丁戊己庚辛壬癸]{1,4}$"),
    re.compile(r"^[子丑寅卯辰巳午未申酉戌亥]{1,4}$"),
    re.compile(r"^[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥、，\s\u3000]+$"),
]

TRIGGER_BY_TOPIC = {
    "tiyong_source": "always",
    "qi_momentum": "always",
    "zhonghe_pianku": "always",
    "cold_warm_dry_wet": "has_tiaohou_advice",
    "source_flow": "has_energy_structure",
    "passage": "has_energy_structure",
    "stem_branch_relation": "has_zhi_chong",
    "chong_he": "has_zhi_chong",
    "luck_timing": "has_dayun",
    "liunian_timing": "has_liunian",
    "career_official": "has_official_picture",
    "wealth_structure": "has_wealth_picture",
    "marriage_family": "has_marriage_picture",
    "health_body": "wuxing_imbalanced",
}

DOMAIN_KEYWORDS = [
    ("事业", ["官", "贵", "科甲", "功名", "名利", "职", "仕", "权", "用神", "格局", "清", "浊", "真神"]),
    ("财富", ["财", "富", "发财", "经营", "家业", "产业", "利", "妻财", "财官"]),
    ("婚姻", ["妻", "夫", "子", "女命", "夫妻", "子女", "父母", "兄弟", "六亲", "孤", "刑妻", "克子"]),
    ("健康", ["病", "疾", "夭", "寿", "灾", "伤", "死", "寒", "燥", "湿", "枯", "偏枯", "中和"]),
    ("性格", ["性", "情", "仁", "义", "礼", "智", "信", "奸", "慈", "刚", "柔", "顺", "悖"]),
    ("学业", ["书", "文章", "科甲", "读书", "翰苑", "文", "儒", "才学"]),
    ("家庭", ["祖", "父", "母", "兄弟", "六亲", "子女", "妻子", "骨肉"]),
    ("迁移", ["运转", "出外", "离乡", "奔波", "迁", "远"]),
]

TOPIC_KEYWORDS = [
    ("cold_warm_dry_wet", ["寒", "暖", "燥", "湿", "调候", "丙火", "癸水", "丁火", "壬水"]),
    ("zhonghe_pianku", ["中和", "偏枯", "缺陷", "平正", "五行之全"]),
    ("source_flow", ["源流", "流通", "生化", "顺其", "逆其", "气势", "旺极", "从其"]),
    ("passage", ["通关", "关", "相战", "制化", "有情", "无情"]),
    ("stem_branch_relation", ["天干", "地支", "干支", "三元", "人元", "月令"]),
    ("chong_he", ["冲", "合", "会", "刑", "穿", "害", "暗冲", "暗会"]),
    ("luck_timing", ["大运", "行运", "运转", "运走", "岁运", "运至"]),
    ("liunian_timing", ["流年", "太岁", "岁君"]),
    ("career_official", ["官杀", "官", "杀", "煞", "功名", "科甲", "权"]),
    ("wealth_structure", ["财", "富", "妻财", "发财"]),
    ("marriage_family", ["夫妻", "子女", "父母", "兄弟", "六亲", "妻", "夫", "子"]),
    ("health_body", ["疾病", "病", "疾", "夭", "寿", "伤", "灾"]),
    ("qi_momentum", ["进退", "衰旺", "旺相", "休囚", "气", "清气", "浊气", "真神", "假神"]),
    ("tiyong_source", ["体用", "用神", "喜神", "忌神", "精神", "月令"]),
]

USABLE_KEYWORDS = [
    "喜", "忌", "宜", "不宜", "主", "吉", "凶", "贵", "富", "贫", "夭", "寿", "病", "灾", "用", "取", "怕", "发",
    "中和", "偏枯", "顺", "逆", "流通", "用神", "喜神", "忌神", "官", "财", "印", "食", "伤", "杀", "煞",
    "寒", "暖", "燥", "湿", "冲", "合", "刑", "会", "运", "岁", "妻", "子", "父", "母", "兄弟",
]


def normalize_text(text: str) -> str:
    text = re.sub(r"[`*_#>\[\]（）()，。；：、\s\u3000\t\r\n]+", "", text)
    text = re.sub(r"[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]{8,}", "", text)
    return text[:240]


def is_noise(text: str) -> bool:
    stripped = text.strip()
    if stripped.startswith(("时日月年", "新增", "若思按")):
        return True
    return any(pattern.match(stripped) for pattern in NOISE_PATTERNS)


def is_case_line(text: str) -> bool:
    stripped = text.strip()
    stems = len(re.findall(r"[甲乙丙丁戊己庚辛壬癸]", stripped))
    branches = len(re.findall(r"[子丑寅卯辰巳午未申酉戌亥]", stripped))
    return len(stripped) <= 28 and stems + branches >= 6


def split_units(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    units: list[dict[str, Any]] = []
    current_heading = ""
    buffer: list[str] = []
    start_line = 1

    def flush(end_line: int) -> None:
        nonlocal buffer, start_line
        text = "".join(item.strip() for item in buffer).strip()
        if text and not is_noise(text):
            units.append({"heading": current_heading, "text": text, "line": start_line, "end_line": end_line})
        buffer = []

    heading_re = re.compile(r"^(?:[一二三四五六七八九十百]+[、\s　]+)?[^，。；：]{2,24}$")
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            flush(idx - 1)
            start_line = idx + 1
            continue
        if stripped.startswith("#"):
            flush(idx - 1)
            current_heading = re.sub(r"^#+\s*", "", stripped)
            start_line = idx + 1
            continue
        if is_case_line(stripped):
            flush(idx - 1)
            start_line = idx + 1
            continue
        if heading_re.match(stripped) and any(key in stripped for key in ["道", "理气", "配合", "天干", "地支", "寒暖", "燥湿", "源流", "通关", "官杀", "伤官", "清气", "浊气", "真神", "假神", "夫妻", "子女", "父母", "兄弟", "疾病", "岁运", "体用", "月令", "衰旺", "中和"]):
            flush(idx - 1)
            current_heading = stripped.strip("　 ")
            start_line = idx + 1
            continue
        buffer.append(stripped)
    flush(len(lines))
    return units


def split_long_text(text: str) -> list[str]:
    if len(text) <= 380:
        return [text]
    parts = [part.strip() for part in re.split(r"(?<=[。！？；])", text) if part.strip()]
    chunks: list[str] = []
    current = ""
    for part in parts:
        if len(current) + len(part) <= 360:
            current += part
        else:
            if current:
                chunks.append(current)
            current = part
    if current:
        chunks.append(current)
    return chunks


def classify_topic(text: str, heading: str) -> str:
    haystack = heading + text
    for topic, keywords in TOPIC_KEYWORDS:
        if any(keyword in haystack for keyword in keywords):
            return topic
    return "ditiansui_general"


def classify_domains(text: str, heading: str) -> list[str]:
    haystack = heading + text
    domains = [domain for domain, keywords in DOMAIN_KEYWORDS if any(keyword in haystack for keyword in keywords)]
    if not domains:
        domains = ["总体"]
    return domains[:6]


def title_from(heading: str, text: str) -> str:
    heading = heading.strip("# ○：: 　")
    if heading and len(heading) <= 32:
        return heading
    title = re.split(r"[。；，,]", text.strip())[0]
    return title[:28] or "滴天髓原典规则"


def build_statement(text: str) -> str:
    statement = re.sub(r"\s+", "", text)[:180]
    if not statement.endswith(("。", "！", "？")):
        statement += "。"
    return f"滴天髓规则参与：{statement}"


def build_claim(text: str) -> str:
    claim = re.sub(r"\s+", "", text)[:160]
    if not claim.endswith(("。", "！", "？")):
        claim += "。"
    return claim


def classify_rule_type(topic: str, trigger: str, domains: list[str]) -> tuple[str, bool, str]:
    if topic in {"luck_timing", "liunian_timing"} or trigger in {"has_dayun", "has_liunian"}:
        return "TIMING", trigger != "always" and len(domains) <= 4, "独门"
    if topic in {"cold_warm_dry_wet", "source_flow", "passage", "stem_branch_relation", "chong_he", "career_official", "zhonghe_pianku", "qi_momentum", "tiyong_source", "wealth_structure", "health_body"}:
        quantifiable = trigger != "always" and len(domains) <= 4
        return "STRUCTURE", quantifiable, "共识" if quantifiable else "互补"
    if topic == "marriage_family":
        quantifiable = trigger != "always" and len(domains) <= 4
        return "EVENT", quantifiable, "互补"
    return "GENERAL_PRINCIPLE", False, "互补"


def build_rule(idx: int, path: Path, unit: dict[str, Any], text: str) -> dict[str, Any]:
    topic = classify_topic(text, unit["heading"])
    domains = classify_domains(text, unit["heading"])
    trigger = TRIGGER_BY_TOPIC.get(topic, "always")
    rule_type, quantifiable, layer = classify_rule_type(topic, trigger, domains)
    line = int(unit["line"])
    digest = hashlib.sha1(f"{path.as_posix()}:{line}:{text}".encode("utf-8")).hexdigest()[:8].upper()
    return {
        "id": f"DTS-PROD-20260622-{idx:03d}",
        "status": "active",
        "expert_system": "tiaohou_ditiansui",
        "title": title_from(unit["heading"], text),
        "topic": topic,
        "domains": domains,
        "axis_refs": ["AXIS-02", "AXIS-03", "AXIS-04"],
        "claim": build_claim(text),
        "rule_type": rule_type,
        "quantifiable": quantifiable,
        "layer": layer,
        "conditions": {
            "trigger": trigger,
            "required": ["已完成四柱排盘", "可识别五行旺衰、寒暖燥湿、气势顺逆与用神喜忌"],
            "optional": ["结合月令、源流、通关、岁运与案例反馈复核"],
            "exclusions": ["原文为单一古籍断语，未满足气势与喜忌条件时不得机械铁断"],
        },
        "output": {
            "statement": build_statement(text),
            "falsifiable": "若案例反馈显示该气势、调候或顺逆判断长期不能提升对应领域命中率，则本规则需降权、合并或转入反证清单。",
        },
        "confidence": {"star": 4, "percent": 0.72, "posterior": 0.72, "variance": 0.06, "sample_n": 1},
        "source": {"path": path.relative_to(ROOT).as_posix(), "excerpt": text[:420], "line": line},
        "review": {"notes": f"2026-06-22 全量原文抽取；source={path.stem}；heading={unit['heading']}；digest={digest}。"},
    }


def extract_rules() -> list[dict[str, Any]]:
    seen: set[str] = set()
    candidates: list[tuple[Path, dict[str, Any], str]] = []
    for path in SOURCE_FILES:
        for unit in split_units(path):
            heading = unit["heading"].strip()
            if heading in {"滴天髓目录", "通神论", "六亲论"}:
                continue
            for text in split_long_text(unit["text"]):
                if len(text) < 18 or is_noise(text) or is_case_line(text):
                    continue
                if not any(keyword in text for keyword in USABLE_KEYWORDS):
                    continue
                norm = normalize_text(text)
                if len(norm) < 14 or norm in seen:
                    continue
                seen.add(norm)
                candidates.append((path, unit, text))
    return [build_rule(idx, path, unit, text) for idx, (path, unit, text) in enumerate(candidates, start=1)]


def write_summary(rules: list[dict[str, Any]]) -> None:
    domain_counts = Counter(domain for rule in rules for domain in rule["domains"])
    topic_counts = Counter(rule["topic"] for rule in rules)
    source_counts = Counter(rule["source"]["path"] for rule in rules)
    trigger_counts = Counter(rule["conditions"]["trigger"] for rule in rules)

    def table(counter: Counter[str]) -> str:
        lines = ["| 项目 | 数量 |", "|---|---:|"]
        for key, value in counter.most_common():
            lines.append(f"| {key} | {value} |")
        return "\n".join(lines)

    SUMMARY_MD.write_text(
        "# 滴天髓类八字分析规则全量抽取报告\n\n"
        "## 一、规则库概览\n\n"
        f"- **规则总数**: {len(rules)} 条\n"
        "- **状态**: 全部 active（可被生产规则加载器读取）\n"
        "- **来源**: [`sources/tiaohou_ditiansui/`](../../sources/tiaohou_ditiansui/) 原始 md 文档\n"
        "- **输出**: [`theory/tiaohou_ditiansui/index.yaml`](index.yaml)\n"
        "- **提取时间**: 2026-06-22\n"
        "- **去重口径**: 规范化文本指纹去重；同义近义保留原典来源差异，后续由 merge map 合并。\n\n"
        "## 二、来源分布\n\n"
        f"{table(source_counts)}\n\n"
        "## 三、领域覆盖\n\n"
        f"{table(domain_counts)}\n\n"
        "## 四、主题归类\n\n"
        f"{table(topic_counts)}\n\n"
        "## 五、触发器分布\n\n"
        f"{table(trigger_counts)}\n\n"
        "## 六、生产化说明\n\n"
        "- 每条规则包含 `id/status/expert_system/title/topic/domains/axis_refs/claim/conditions/output/source/review/layer/confidence`。\n"
        "- `source.path` 与 `source.line` 保留原文追溯点。\n"
        "- 原文绝对化断语统一降级为气势/调候结构证据，不作为机械铁断。\n"
        "- 初始置信度沿用生产规则默认 0.72 / ★★★★ / sample_n=1，等待反馈校准。\n",
        encoding="utf-8",
    )


def main() -> None:
    rules = extract_rules()
    payload = {
        "schema_version": "production-rules-2026-06-22-full-source-extraction",
        "status": "active",
        "source_scope": "production_rules",
        "expert_system": "tiaohou_ditiansui",
        "notes": "由 sources/tiaohou_ditiansui 原始 md 全量抽取、去重归类生成；用于滴天髓/调候生产规则加载。",
        "rules": rules,
    }
    OUTPUT_YAML.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")
    OUTPUT_JSON.write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")
    write_summary(rules)
    print(f"extracted_rules={len(rules)}")


if __name__ == "__main__":
    main()
