from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "sources" / "ziping"
OUTPUT_YAML = ROOT / "theory" / "ziping" / "index.yaml"
OUTPUT_JSON = ROOT / "theory" / "ziping" / "_extracted_rules.json"
SUMMARY_MD = ROOT / "theory" / "ziping" / "_extracted_rules_summary.md"

SOURCE_FILES = [
    SOURCE_DIR / "《子平真诠》.md",
    SOURCE_DIR / "《三命通会》.md",
    SOURCE_DIR / "穷通宝鉴-明-余春台_part1.md",
    SOURCE_DIR / "穷通宝鉴-明-余春台_part2.md",
]

SKIP_PREFIXES = ("时日月年",)
NOISE_PATTERNS = [
    re.compile(r"^[\s\u3000\t]*$"),
    re.compile(r"^卷[一二三四五六七八九十]+$"),
    re.compile(r"^[甲乙丙丁戊己庚辛壬癸]{1,4}$"),
    re.compile(r"^[子丑寅卯辰巳午未申酉戌亥]{1,4}$"),
]

TRIGGER_BY_TOPIC = {
    "luck_timing": "has_dayun",
    "liunian_timing": "has_liunian",
    "marriage_family": "has_marriage_picture",
    "wealth_structure": "has_wealth_picture",
    "official_career": "has_official_picture",
    "relations_combo": "has_zhi_chong",
    "shensha_kongwang": "has_kongwang",
    "shensha_sanxing": "has_sanxing",
    "shensha_guchen": "has_guchen_guasu",
    "shensha_tianluo": "has_tianluodiwang",
    "shensha_zaisha": "has_zaisha",
    "shensha_goujiao": "has_goujiao",
}

DOMAIN_KEYWORDS = [
    ("事业", ["官", "贵", "科甲", "功名", "职", "仕", "禄", "权", "武", "文", "名利", "显达", "富贵"]),
    ("财富", ["财", "富", "妻财", "财帛", "产业", "田园", "发财", "禄马", "库"]),
    ("婚姻", ["妻", "夫", "婚", "孤寡", "子", "女命", "男命", "配偶", "淫", "桃花", "咸池"]),
    ("健康", ["病", "疾", "夭", "寿", "残", "灾", "死", "血", "伤", "目", "耳", "脾", "肺", "肝", "肾"]),
    ("性格", ["性", "情", "仁", "义", "礼", "智", "信", "聪明", "刚", "柔", "奸", "慈", "厚", "好"]),
    ("学业", ["学", "文章", "科甲", "登科", "儒", "翰", "文星", "学堂", "词馆"]),
    ("家庭", ["祖", "父", "母", "兄弟", "六亲", "子息", "子女", "骨肉"]),
    ("迁移", ["驿马", "迁", "远", "奔", "离乡", "迁改"]),
]

TOPIC_KEYWORDS = [
    ("yongshen_pattern", ["用神", "相神", "格局", "成格", "破格", "救应", "格"]),
    ("wealth_structure", ["财", "妻财", "偏财", "正财", "财库"]),
    ("official_career", ["正官", "偏官", "七煞", "官煞", "官星", "杀", "禄"]),
    ("food_injury", ["食神", "伤官", "倒食", "枭"]),
    ("seal_resource", ["印绶", "正印", "偏印"]),
    ("relations_combo", ["合", "冲", "刑", "害", "会", "破"]),
    ("luck_timing", ["大运", "行运", "运喜", "运至", "岁运", "小运"]),
    ("liunian_timing", ["太岁", "流年", "岁君", "岁伤", "日犯"]),
    ("marriage_family", ["妻", "夫", "子女", "六亲", "父母", "兄弟"]),
    ("health_body", ["疾病", "五脏", "病", "疾", "夭", "寿", "残"]),
    ("shensha_kongwang", ["空亡", "天中"]),
    ("shensha_sanxing", ["三刑", "自刑"]),
    ("shensha_guchen", ["孤辰", "寡宿", "孤寡"]),
    ("shensha_tianluo", ["天罗", "地网", "罗网"]),
    ("shensha_zaisha", ["灾煞"]),
    ("shensha_goujiao", ["勾绞"]),
    ("tiaohou_wuxing", ["春", "夏", "秋", "冬", "寒", "暖", "燥", "湿", "丙", "癸", "丁", "庚", "壬", "甲"]),
]

USABLE_KEYWORDS = [
    "喜", "忌", "主", "贵", "富", "贫", "夭", "寿", "吉", "凶", "格", "用", "取", "怕", "宜", "不宜", "断", "发", "灾",
    "科甲", "官", "财", "印", "食", "伤", "煞", "杀", "妻", "夫", "子", "病", "运", "岁", "冲", "合", "刑", "害",
]


def normalize_text(text: str) -> str:
    text = re.sub(r"[`*_#>\[\]（）()，。；：、\s\u3000\t\r\n]+", "", text)
    return text[:220]


def is_noise(text: str) -> bool:
    stripped = text.strip()
    if stripped.startswith(SKIP_PREFIXES):
        return True
    return any(pattern.match(stripped) for pattern in NOISE_PATTERNS)


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

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            flush(idx - 1)
            current_heading = re.sub(r"^#+\s*", "", stripped)
            start_line = idx + 1
            continue
        if stripped.startswith("○"):
            flush(idx - 1)
            parts = re.split(r"(?<=[。！？])", stripped, maxsplit=1)
            current_heading = parts[0][:40]
            remainder = stripped[len(parts[0]):].strip() if parts else ""
            start_line = idx
            if remainder:
                buffer.append(remainder)
            continue
        if re.match(r"^(三春|三夏|三秋|三冬|春月|夏月|秋月|冬月|正月|二月|三月|四月|五月|六月|七月|八月|九月|十月|十一月|十二月|论[木火土金水]|[甲乙丙丁戊己庚辛壬癸].*月)", stripped) and len(stripped) <= 40:
            flush(idx - 1)
            current_heading = stripped.rstrip("：:")
            start_line = idx + 1
            continue
        if not stripped:
            flush(idx - 1)
            start_line = idx + 1
            continue
        buffer.append(stripped)
    flush(len(lines))
    return units


def split_long_text(text: str) -> list[str]:
    if len(text) <= 360:
        return [text]
    parts = [part.strip() for part in re.split(r"(?<=[。！？；])", text) if part.strip()]
    chunks: list[str] = []
    current = ""
    for part in parts:
        if len(current) + len(part) <= 340:
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
    return "ziping_general"


def classify_domains(text: str, heading: str) -> list[str]:
    haystack = heading + text
    domains = [domain for domain, keywords in DOMAIN_KEYWORDS if any(keyword in haystack for keyword in keywords)]
    if not domains:
        domains = ["总体"]
    return domains[:6]


def title_from(heading: str, text: str) -> str:
    heading = heading.strip("# ○：: ")
    if heading and len(heading) <= 32:
        return heading
    title = re.split(r"[。；，,]", text.strip())[0]
    return title[:28] or "子平原典规则"


def source_title(path: Path) -> str:
    return path.stem


def build_statement(text: str) -> str:
    statement = re.sub(r"\s+", "", text)
    statement = statement[:180]
    if not statement.endswith(("。", "！", "？")):
        statement += "。"
    return f"子平规则参与：{statement}"


def build_claim(text: str) -> str:
    claim = re.sub(r"\s+", "", text)
    return claim[:160] + ("。" if not claim.endswith(("。", "！", "？")) else "")


def classify_rule_type(topic: str, trigger: str, domains: list[str]) -> tuple[str, bool, str]:
    if topic in {"luck_timing", "liunian_timing"} or trigger in {"has_dayun", "has_liunian"}:
        return "TIMING", trigger != "always" and len(domains) <= 4, "独门"
    if topic in {"yongshen_pattern", "wealth_structure", "official_career", "relations_combo", "tiaohou_wuxing", "food_injury", "seal_resource", "health_body"}:
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
        "id": f"ZP-PROD-20260622-{idx:03d}",
        "status": "active",
        "expert_system": "ziping",
        "title": title_from(unit["heading"], text),
        "topic": topic,
        "domains": domains,
        "axis_refs": ["AXIS-01", "AXIS-04"],
        "claim": build_claim(text),
        "conditions": {
            "trigger": trigger,
            "required": ["已完成四柱排盘", "可识别日主、月令、干支关系与基础十神"],
            "optional": ["结合旺衰、格局、调候、岁运与反馈证据复核"],
            "exclusions": ["原文为单一古籍断语，未满足结构条件时不得机械铁断"],
        },
        "output": {
            "statement": build_statement(text),
            "falsifiable": "若案例反馈显示该结构条件长期不能提升对应领域判断命中率，则本规则需降权、合并或转入反证清单。",
        },
        "source": {
            "path": path.relative_to(ROOT).as_posix(),
            "excerpt": text[:420],
            "line": line,
        },
        "review": {
            "notes": f"2026-06-22 全量原文抽取；source={source_title(path)}；heading={unit['heading']}；digest={digest}。"
        },
        "rule_type": rule_type,
        "quantifiable": quantifiable,
        "layer": layer,
        "confidence": {"star": 4, "percent": 0.72, "posterior": 0.72, "variance": 0.06, "sample_n": 1},
    }


def extract_rules() -> list[dict[str, Any]]:
    seen: set[str] = set()
    candidates: list[tuple[Path, dict[str, Any], str]] = []
    for path in SOURCE_FILES:
        for unit in split_units(path):
            for text in split_long_text(unit["text"]):
                if len(text) < 18:
                    continue
                if unit["heading"].strip() in {"序"}:
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
        "# 子平类八字分析规则全量抽取报告\n\n"
        "## 一、规则库概览\n\n"
        f"- **规则总数**: {len(rules)} 条\n"
        "- **状态**: 全部 active（可被生产规则加载器读取）\n"
        "- **来源**: [`sources/ziping/`](../../sources/ziping/) 原始 md 文档\n"
        "- **输出**: [`theory/ziping/index.yaml`](index.yaml)\n"
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
        "- 原文绝对化断语统一降级为结构证据，不作为机械铁断。\n"
        "- 初始置信度沿用子平生产规则默认 0.72 / ★★★★ / sample_n=1，等待反馈校准。\n",
        encoding="utf-8",
    )


def main() -> None:
    rules = extract_rules()
    payload = {
        "schema_version": "production-rules-2026-06-22-full-source-extraction",
        "status": "active",
        "source_scope": "production_rules",
        "expert_system": "ziping",
        "notes": "由 sources/ziping 原始 md 全量抽取、去重归类生成；用于 v5 子平结构法度命题与默认生产规则加载。",
        "rules": rules,
    }
    OUTPUT_YAML.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")
    OUTPUT_JSON.write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")
    write_summary(rules)
    print(f"extracted_rules={len(rules)}")


if __name__ == "__main__":
    main()
