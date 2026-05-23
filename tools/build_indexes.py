#!/usr/bin/env python3
"""
build_indexes.py · 从 theory/raw/ 抽取 4 派全部 914 条规律 → theory/{school}/index.yaml

输入：
  theory/raw/gao/extracted/*.md          (高派 261 条，含 anchor + score)
  theory/raw/duan/promoted/m1-*.md       (段派 290 条，分布在 m1-patterns/practice/timing)
  theory/raw/yang/promoted/m2-rules-registry.md  (杨派 163 条 registry)
  theory/raw/ren/promoted/m3-rules-registry.md   (任派 200 条 registry)

每条索引项包含：
  id, school, topic, title, conclusion(if available),
  status, layer, raw_source, raw_anchor, candidate_score, raw_file
"""
import os
import re
import sys
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "theory" / "raw"


# ============================================================
# 高派 抽取（已有 23-30 条/文件 的结构化表格）
# ============================================================
GAO_PREFIX_TO_TOPIC = {
    "LF": "lifa",          # 理法
    "XF": "xiangfa",       # 象法
    "SS": "shensha",       # 神煞
    "BD": "shensha",       # 神煞应用宝典
    "CY": "caiyun",        # 财运
    "CS": "caiyun",        # 财运事业断法
    "DY": "dayun",         # 大运流年
    "CH": "hunyin",        # 车祸婚姻（先归婚姻为主，灾厄交叉）
    "MG": "mingong",       # 命宫长生诀择日
}

GAO_FILE_TO_SOURCE = {
    "高派_理法篇_候选规律提取_2026-05-19.md": "2018弟子班_理法篇_31页.md",
    "高派_象法篇_候选规律提取_2026-05-19.md": "2018弟子班_象法篇_83页.md",
    "高派_神煞篇_候选规律提取_2026-05-19.md": "2018弟子班_神煞篇_34页.md",
    "高派_神煞应用宝典_候选规律提取_2026-05-19.md": "盲派神煞应用宝典.md",
    "高派_财运篇_候选规律提取_2026-05-19.md": "2018弟子班_财运篇_43页.md",
    "高派_财运事业断法_候选规律提取_2026-05-19.md": "财运事业断法弟子提高班_105页.md",
    "高派_大运流年篇_候选规律提取_2026-05-19.md": "2018弟子班_大运流年篇_55页.md",
    "高派_车祸婚姻篇_候选规律提取_2026-05-19.md": "2018弟子班_车祸婚姻篇_85页.md",
    "高派_命宫长生诀择日篇_候选规律提取_2026-05-19.md": "2018弟子班_命宫长生诀择日篇_78页.md",
}


def extract_gao():
    rules = []
    for f in sorted((RAW / "gao" / "extracted").glob("*.md")):
        content = f.read_text(encoding="utf-8")
        source = GAO_FILE_TO_SOURCE.get(f.name, f.name)
        pattern = re.compile(
            r"\|\s*\*\*GP-([A-Z]+)-(\d+)\*\*\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*([\d.]+)\s*\|"
        )
        for m in pattern.finditer(content):
            prefix, num, rule_text, anchor, _module, score = m.groups()
            topic = GAO_PREFIX_TO_TOPIC.get(prefix, "other")
            rule_text = re.sub(r"\s+", " ", rule_text).strip()
            # 标题 = 第一个 ：/—— 之前的部分
            title_match = re.match(r"[^：:——]+(?:[：:]|——)", rule_text)
            if title_match:
                title = title_match.group(0).rstrip("：:——").strip()
                if len(title) > 60:
                    title = title[:60] + "…"
                conclusion = rule_text[len(title_match.group(0)):].strip()
            else:
                title = rule_text[:50] + ("…" if len(rule_text) > 50 else "")
                conclusion = rule_text
            # 移除 ⭐ 装饰
            title = re.sub(r"^[⭐\s]+", "", title)
            title = re.sub(r"\*\*", "", title)
            new_id = f"G-{prefix}-{int(num):03d}"
            rules.append({
                "id": new_id,
                "legacy_id": f"GP-{prefix}-{num}",
                "school": "gao",
                "topic": topic,
                "title": title,
                "conclusion": conclusion[:400],
                "status": "candidate",
                "layer": "unmapped",
                "raw_source": source,
                "raw_anchor": anchor.strip(),
                "candidate_score": float(score),
                "raw_file": f"theory/raw/gao/extracted/{f.name}",
            })
    return rules


# ============================================================
# 段派 抽取
# ============================================================
DUAN_TOPIC_BY_SECTION = {
    # m1-patterns.md 章节 → topic
    "17.1": ("lifa", "宾主"),
    "17.2": ("lifa", "体用"),
    "17.3": ("lifa", "做功"),
    "17.4": ("lifa", "贼神捕神"),
    "17.5": ("lifa", "势与党"),
    "17.6": ("lifa", "制法"),
    "17.7": ("geju", "反局体系"),
    "17.8": ("lifa", "判读层"),
    "17.9": ("xiangfa", "象法体系"),
    "18.1": ("geju", "正格12格局"),
    "18.2": ("geju", "变格"),
    "18.3": ("geju", "签字+案例"),
    "18.4": ("xiangfa", "暗合"),
    "18.5": ("geju", "实战签字"),
    "18.6": ("geju", "过河拆桥"),
}


def extract_duan():
    rules = {}
    files = sorted((RAW / "duan" / "promoted").glob("m1-*.md"))
    
    # 阶段 1：从 m1-patterns.md 抽取（带章节归类）
    for f in files:
        content = f.read_text(encoding="utf-8")
        # 跟踪当前章节
        current_section = None
        current_section_topic = None
        current_section_label = None
        
        for line in content.splitlines():
            # 匹配章节头：### 17.1 宾主（M1-D-001..004, 111）
            sec_match = re.match(r"^###\s+(\d+\.\d+)\s+([^（(]+)", line)
            if sec_match:
                current_section = sec_match.group(1)
                meta = DUAN_TOPIC_BY_SECTION.get(current_section)
                if meta:
                    current_section_topic, current_section_label = meta
                else:
                    current_section_topic = "unmapped"
                    current_section_label = sec_match.group(2).strip()
            
            # 匹配规律行：| M1-D-001 | 宾主第 1 层 — ... | 4.0 |
            rule_match = re.match(
                r"^\|\s*(M1-D-\d+)\s*\|\s*([^|]+?)\s*\|\s*([\d.]+)?\s*\|", line
            )
            if rule_match:
                rule_id = rule_match.group(1)
                title = rule_match.group(2).strip()
                priority = rule_match.group(3)
                if rule_id in rules:
                    continue
                # 清洗 title
                title = re.sub(r"\*\*", "", title).strip()
                rules[rule_id] = {
                    "id": rule_id,
                    "school": "duan",
                    "topic": current_section_topic or "unmapped",
                    "topic_label": current_section_label or "",
                    "title": title[:120],
                    "conclusion": "",
                    "status": "promoted",
                    "layer": "unmapped",
                    "raw_source": "段派 m1 模块",
                    "raw_anchor": f"§{current_section} {current_section_label}" if current_section else "",
                    "candidate_score": float(priority) if priority else None,
                    "raw_file": str(f.relative_to(ROOT)),
                }
    
    # 阶段 2：补全 raw/duan/d*-theory.md 中可能新增的规律
    for f in sorted((RAW / "duan").glob("d*-theory.md")):
        content = f.read_text(encoding="utf-8")
        # 匹配 §17.X 之类章节头与规律块
        for m in re.finditer(r"^\|\s*(M1-D-\d+)\s*\|\s*([^|]+?)\s*\|", content, re.MULTILINE):
            rule_id = m.group(1)
            title = m.group(2).strip()
            if rule_id in rules:
                continue
            rules[rule_id] = {
                "id": rule_id,
                "school": "duan",
                "topic": "unmapped",
                "topic_label": "",
                "title": title[:120],
                "conclusion": "",
                "status": "candidate",
                "layer": "unmapped",
                "raw_source": "段派 deep-read",
                "raw_anchor": "",
                "candidate_score": None,
                "raw_file": str(f.relative_to(ROOT)),
            }
    
    # 阶段 3：兜底——确保 001..290 全部存在
    for i in range(1, 291):
        rid = f"M1-D-{i:03d}"
        if rid not in rules:
            rules[rid] = {
                "id": rid,
                "school": "duan",
                "topic": "unmapped",
                "topic_label": "",
                "title": "(待补)",
                "conclusion": "",
                "status": "pending_normalization",
                "layer": "unmapped",
                "raw_source": "(see m1-patterns.md / d-theory.md)",
                "raw_anchor": "",
                "candidate_score": None,
                "raw_file": "",
            }
    
    return sorted(rules.values(), key=lambda x: int(re.search(r"\d+", x["id"]).group()))


# ============================================================
# 杨派 抽取（m2-rules-registry.md 最完整）
# ============================================================
def extract_yang():
    rules = {}
    f = RAW / "yang" / "promoted" / "m2-rules-registry.md"
    content = f.read_text(encoding="utf-8")
    
    # 跟踪章节获取 topic
    current_section_label = ""
    current_topic = "unmapped"
    
    section_topic_map = {
        "入口规则": "lifa",
        "基础篇": "lifa",
        "结构基础": "lifa",
        "天干五合": "lifa",
        "十神深化": "lifa",
        "结婚应期": "hunyin",
        "婚姻深化": "hunyin",
        "学历判定": "jiaoyu",
        "调候改运": "tiaohou",
        "三刑": "shensha",
        "六穿医学": "jiankang",
        "财富级别": "caiyun",
        "禄体系": "lifa",
        "十神场合": "lifa",
        "官命深化": "caiyun",
        "实战步骤": "lifa",
        "比劫分层": "lifa",
        "象法": "xiangfa",
        "应期": "yingqi",
        "六亲": "liuqin",
        "灾": "jiankang",
        "格局": "geju",
        "禄": "lifa",
        "做功": "lifa",
        "调候": "tiaohou",
        "暗合": "xiangfa",
        "桃花": "hunyin",
        "五合": "lifa",
        "穿": "jiankang",
    }
    
    for line in content.splitlines():
        # 匹配章节
        sec_match = re.match(r"^###?\s*(?:§\d+\.?\d*)?\s*[·]?\s*([^（(]+)", line)
        if sec_match and "M2-Y" in line:
            label = sec_match.group(1).strip()
            current_section_label = label
            current_topic = "unmapped"
            for key, topic in section_topic_map.items():
                if key in label:
                    current_topic = topic
                    break
        
        # 匹配规律：| M2-Y-001 | 法无定法唯变是法 | 八字无固定公式... |
        rule_match = re.match(
            r"^\|\s*(M2-Y-\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line
        )
        if rule_match:
            rule_id = rule_match.group(1)
            title = rule_match.group(2).strip()
            conclusion = rule_match.group(3).strip()
            if rule_id in rules or title.startswith("---"):
                continue
            rules[rule_id] = {
                "id": rule_id,
                "school": "yang",
                "topic": current_topic,
                "topic_label": current_section_label,
                "title": title[:80],
                "conclusion": conclusion[:300],
                "status": "promoted",
                "layer": "unmapped",
                "raw_source": "杨派 m2-rules-registry",
                "raw_anchor": current_section_label,
                "candidate_score": None,
                "raw_file": str(f.relative_to(ROOT)),
            }
    
    # 兜底 001..163
    for i in range(1, 164):
        rid = f"M2-Y-{i:03d}"
        if rid not in rules:
            rules[rid] = {
                "id": rid,
                "school": "yang",
                "topic": "unmapped",
                "topic_label": "",
                "title": "(待补)",
                "conclusion": "",
                "status": "pending_normalization",
                "layer": "unmapped",
                "raw_source": "(see m2-rules-registry.md)",
                "raw_anchor": "",
                "candidate_score": None,
                "raw_file": "",
            }
    
    return sorted(rules.values(), key=lambda x: int(re.search(r"\d+", x["id"]).group()))


# ============================================================
# 任派 抽取（m3-rules-registry.md 200 条 8 大主题）
# ============================================================
REN_SECTION_TO_TOPIC = {
    "十八道法门": "lifa",
    "初/中/高级班": "lifa",
    "断命例题": "yingqi",
    "财运篇": "caiyun",
    "官运篇": "caiyun",
    "命例集": "yingqi",
    "课堂讲义": "lifa",
    "实战": "yingqi",
    "六合": "hunyin",
    "六冲": "yingqi",
    "六穿": "jiankang",
    "六害": "jiankang",
    "三合": "yingqi",
    "三刑": "shensha",
    "神煞": "shensha",
    "婚姻": "hunyin",
    "应期": "yingqi",
    "格局": "geju",
    "象法": "xiangfa",
    "调候": "tiaohou",
}


def extract_ren():
    rules = {}
    f = RAW / "ren" / "promoted" / "m3-rules-registry.md"
    content = f.read_text(encoding="utf-8")
    
    current_section_label = ""
    current_topic = "lifa"
    
    for line in content.splitlines():
        # 章节标题
        sec_match = re.match(r"^###?\s*(?:§\d+\.?\d*)?\s*[·]?\s*(.+)", line)
        if sec_match and "(M3-R" in line:
            label = sec_match.group(1).strip()
            current_section_label = label
            current_topic = "lifa"
            for key, topic in REN_SECTION_TO_TOPIC.items():
                if key in label:
                    current_topic = topic
                    break
        
        # 规律行：| M3-R-001 | 八字本质 | §6/§7 |
        rule_match = re.match(
            r"^\|\s*(M3-R-\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line
        )
        if rule_match:
            rule_id = rule_match.group(1)
            title = rule_match.group(2).strip()
            anchor = rule_match.group(3).strip()
            if rule_id in rules or title.startswith("---"):
                continue
            rules[rule_id] = {
                "id": rule_id,
                "school": "ren",
                "topic": current_topic,
                "topic_label": current_section_label,
                "title": title[:80],
                "conclusion": "",
                "status": "promoted",
                "layer": "unmapped",
                "raw_source": "任派 m3-rules-registry",
                "raw_anchor": f"{current_section_label} · {anchor}",
                "candidate_score": None,
                "raw_file": str(f.relative_to(ROOT)),
            }
    
    # 兜底 001..200
    for i in range(1, 201):
        rid = f"M3-R-{i:03d}"
        if rid not in rules:
            rules[rid] = {
                "id": rid,
                "school": "ren",
                "topic": "unmapped",
                "topic_label": "",
                "title": "(待补)",
                "conclusion": "",
                "status": "pending_normalization",
                "layer": "unmapped",
                "raw_source": "(see m3-rules-registry.md)",
                "raw_anchor": "",
                "candidate_score": None,
                "raw_file": "",
            }
    
    return sorted(rules.values(), key=lambda x: int(re.search(r"\d+", x["id"]).group()))


# ============================================================
# YAML 写出
# ============================================================
def yaml_escape(s):
    if s is None:
        return ""
    s = str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    return s


def write_yaml(rules, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = os.popen("date -Iseconds").read().strip()
    
    # 统计
    topic_counts = Counter(r.get("topic", "unmapped") for r in rules)
    status_counts = Counter(r.get("status", "candidate") for r in rules)
    
    with output_path.open("w", encoding="utf-8") as fp:
        fp.write("# Auto-generated by tools/build_indexes.py · DO NOT EDIT BY HAND\n")
        fp.write(f"# Total rules: {len(rules)}\n")
        fp.write(f"# Generated at: {timestamp}\n")
        fp.write("# Topic distribution:\n")
        for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1]):
            fp.write(f"#   {topic}: {count}\n")
        fp.write("# Status distribution:\n")
        for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
            fp.write(f"#   {status}: {count}\n")
        fp.write("\n")
        fp.write("rules:\n")
        for r in rules:
            fp.write(f"  - id: {r['id']}\n")
            if r.get("legacy_id"):
                fp.write(f"    legacy_id: {r['legacy_id']}\n")
            fp.write(f"    school: {r['school']}\n")
            fp.write(f"    topic: {r['topic']}\n")
            if r.get("topic_label"):
                fp.write(f'    topic_label: "{yaml_escape(r["topic_label"])}"\n')
            fp.write(f'    title: "{yaml_escape(r["title"])}"\n')
            if r.get("conclusion"):
                fp.write(f'    conclusion: "{yaml_escape(r["conclusion"])}"\n')
            fp.write(f"    status: {r['status']}\n")
            fp.write(f"    layer: {r['layer']}\n")
            if r.get("raw_source"):
                fp.write(f'    raw_source: "{yaml_escape(r["raw_source"])}"\n')
            if r.get("raw_anchor"):
                fp.write(f'    raw_anchor: "{yaml_escape(r["raw_anchor"])}"\n')
            if r.get("raw_file"):
                fp.write(f'    raw_file: "{yaml_escape(r["raw_file"])}"\n')
            if r.get("candidate_score") is not None:
                fp.write(f"    candidate_score: {r['candidate_score']}\n")


def main():
    summary = {}
    for school, extractor in [
        ("gao", extract_gao),
        ("duan", extract_duan),
        ("yang", extract_yang),
        ("ren", extract_ren),
    ]:
        rules = extractor()
        write_yaml(rules, ROOT / "theory" / school / "index.yaml")
        topic_counts = Counter(r["topic"] for r in rules)
        status_counts = Counter(r["status"] for r in rules)
        summary[school] = {
            "total": len(rules),
            "topics": dict(topic_counts),
            "status": dict(status_counts),
        }
        print(f"{school}: {len(rules)} 条")
        print(f"  topics: {dict(topic_counts)}")
        print(f"  status: {dict(status_counts)}")
    
    print(f"\n总计: {sum(s['total'] for s in summary.values())} 条规律已索引")
    return summary


if __name__ == "__main__":
    main()
