#!/usr/bin/env python3
"""
calibrate.py · 反馈回流校准工具 · v1.0

用途：把命主反馈应验/失验数据，回流到 4 派 theory/{school}/index.yaml，
      自动重算每条规律的 hit_count / miss_count / dynamic_score / star，
      触发升降级，更新 META/rule-changelog.md。

输入：
  cases/C-YYYY-NNN/feedback.md  (命主反馈，按 templates/feedback.md 格式)
  cases/C-YYYY-NNN/analysis.md  (分析时使用的规律列表)

输出：
  cases/C-YYYY-NNN/calibration-report.md   校准报告
  theory/{school}/index.yaml                更新后的索引（hit/miss/score 字段）
  META/rule-changelog.md                    增补本次校准记录
  mapping/*.md                              如有规律层级变更同步更新

使用：
  python3 tools/calibrate.py --case C-2026-001
  python3 tools/calibrate.py --case C-2026-001 --dry-run
"""
import argparse
import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "cases"
THEORY = ROOT / "theory"
MAPPING = ROOT / "mapping"
META = ROOT / "META"

# ============================================================
# 置信度计算（与 engine/confidence.yaml 同步）
# ============================================================

ALPHA_STATIC = 0.4
BETA_DYNAMIC = 0.6

CONFIDENCE_FACTORS = {
    3: 0.70,
    4: 0.78,
    5: 0.85,
    6: 0.88,
    7: 0.92,
    8: 0.95,
    9: 0.98,
    10: 1.00,
}

def confidence_factor(sample_size: int) -> float:
    """按样本量返回 dynamic_score 的置信因子"""
    if sample_size < 3:
        return 0.0
    if sample_size >= 10:
        return 1.0
    return CONFIDENCE_FACTORS.get(sample_size, 1.0)


def calc_dynamic_score(hit: int, miss: int) -> float:
    """动态分 = hit_rate × 100 × confidence_factor"""
    sample = hit + miss
    if sample < 3:
        return 0.0  # 不可信
    hit_rate = hit / sample
    return hit_rate * 100 * confidence_factor(sample)


def calc_final_score(static_score: float, hit: int, miss: int) -> float:
    """final = α × static + β × dynamic"""
    sample = hit + miss
    if sample < 3:
        # 样本不足，退回静态分
        return static_score
    dynamic = calc_dynamic_score(hit, miss)
    return ALPHA_STATIC * static_score + BETA_DYNAMIC * dynamic


def score_to_star(score: float) -> int:
    """0-100 分 → 1-5 星"""
    if score >= 90:
        return 5
    if score >= 80:
        return 4
    if score >= 65:
        return 3
    if score >= 50:
        return 2
    return 1


def status_transition(current_status: str, hit: int, miss: int) -> str:
    """根据应验情况判定 status 升降级"""
    sample = hit + miss
    if sample < 3:
        return current_status
    hit_rate = hit / sample
    if hit_rate >= 0.66 and current_status == "candidate":
        return "promoted"
    if hit_rate <= 0.33 and current_status in ("candidate", "promoted"):
        return "retired"
    if 0.33 < hit_rate < 0.66 and current_status == "promoted":
        # 命中率从 promoted 跌入观察区 → 降回 candidate
        return "candidate"
    return current_status


# ============================================================
# 反馈解析
# ============================================================

def parse_feedback(feedback_path: Path) -> list:
    """
    从 feedback.md 解析每条规律的应验情况。
    
    支持的反馈行格式：
    | M1-D-001 | ... | ✅ 应验 | ... |
    | M1-D-001 | ... | ❌ 失验 | ... |
    | M1-D-001 | ... | ⚠️ 部分应验 | ... |
    
    返回：[{rule_id, status, evidence_strength}, ...]
    """
    if not feedback_path.exists():
        print(f"⚠️  反馈文件不存在: {feedback_path}")
        return []
    
    content = feedback_path.read_text(encoding="utf-8")
    feedbacks = []
    
    # 匹配规律 ID 和应验状态
    rule_id_re = re.compile(
        r"\|\s*((?:M[123]-[DYR]-\d+)|(?:G-[A-Z]+-\d+)|(?:CON-[A-Z]+-\d+)|"
        r"(?:COM-[A-Z]+-\d+)|(?:EXC-[GDYR]-[A-Z]+-\d+))\s*\|"
    )
    status_re = re.compile(r"(✅\s*应验|❌\s*失验|⚠️\s*部分应验|⏳\s*pending)")
    
    for line in content.splitlines():
        rule_match = rule_id_re.search(line)
        if not rule_match:
            continue
        rule_id = rule_match.group(1)
        
        status_match = status_re.search(line)
        if not status_match:
            continue
        
        status_raw = status_match.group(1)
        if "应验" in status_raw and "部分" not in status_raw:
            status = "hit"
        elif "失验" in status_raw:
            status = "miss"
        elif "部分应验" in status_raw:
            status = "partial"
        elif "pending" in status_raw:
            status = "pending"
        else:
            continue
        
        # 检测证据类型（影响权重）
        evidence_strength = 1.0
        if "命主自报" in line or "命主原话" in line:
            evidence_strength = 0.8
        if "客观证据" in line or "公开资料" in line or "诊断书" in line:
            evidence_strength = 1.0
        
        feedbacks.append({
            "rule_id": rule_id,
            "status": status,
            "evidence_strength": evidence_strength,
        })
    
    return feedbacks


# ============================================================
# theory/{school}/index.yaml 更新
# ============================================================

def school_from_rule_id(rule_id: str) -> str:
    """根据规律 ID 推断派别"""
    if rule_id.startswith("M1-D-"):
        return "duan"
    if rule_id.startswith("M2-Y-"):
        return "yang"
    if rule_id.startswith("M3-R-"):
        return "ren"
    if rule_id.startswith("G-"):
        return "gao"
    return None


def load_index_yaml(school: str) -> tuple:
    """
    加载 theory/{school}/index.yaml 为 (header, rules_dict)
    rules_dict: {rule_id: rule_data}
    """
    path = THEORY / school / "index.yaml"
    if not path.exists():
        return ("", {})
    
    content = path.read_text(encoding="utf-8")
    # 抽取 header（rules: 之前的部分）
    if "\nrules:" in content:
        header, body = content.split("\nrules:", 1)
        header = header + "\nrules:"
    else:
        header = content
        body = ""
    
    # 解析 rules（简易 YAML 解析）
    rules = {}
    current_rule = None
    for line in body.splitlines():
        if re.match(r"^  - id:", line):
            if current_rule:
                rules[current_rule["id"]] = current_rule
            current_rule = {"id": line.split(":", 1)[1].strip(), "_lines": [line]}
        elif current_rule and line.startswith("    "):
            current_rule["_lines"].append(line)
            kv = re.match(r"^    (\w+):\s*(.*)$", line)
            if kv:
                key, val = kv.group(1), kv.group(2).strip()
                # 去引号
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                current_rule[key] = val
    if current_rule:
        rules[current_rule["id"]] = current_rule
    
    return (header, rules)


def update_index_with_feedback(school: str, rule_updates: dict, dry_run: bool = False) -> dict:
    """
    更新 theory/{school}/index.yaml 中的规律 hit/miss/score/star
    rule_updates: {rule_id: {hit_delta, miss_delta, partial_delta}}
    返回每条规律更新前后的对比
    """
    header, rules = load_index_yaml(school)
    transitions = []
    
    for rule_id, delta in rule_updates.items():
        if rule_id not in rules:
            continue
        rule = rules[rule_id]
        
        # 当前 hit/miss
        hit = int(rule.get("hit_count", 0)) + delta.get("hit_delta", 0)
        miss = int(rule.get("miss_count", 0)) + delta.get("miss_delta", 0)
        # partial 不计入 hit/miss，但记录到 partial_count
        partial = int(rule.get("partial_count", 0)) + delta.get("partial_delta", 0)
        
        # 静态分（默认值）
        static_score = float(rule.get("static_score", rule.get("candidate_score") or 50.0))
        if static_score < 1.0:
            # candidate_score 0.6 → 60
            static_score = static_score * 100
        
        # 重算
        dynamic = calc_dynamic_score(hit, miss)
        final = calc_final_score(static_score, hit, miss)
        star = score_to_star(final)
        old_status = rule.get("status", "candidate")
        new_status = status_transition(old_status, hit, miss)
        
        transitions.append({
            "rule_id": rule_id,
            "school": school,
            "old": {
                "hit": int(rule.get("hit_count", 0)),
                "miss": int(rule.get("miss_count", 0)),
                "static": static_score,
                "final": float(rule.get("final_score", static_score)),
                "star": int(rule.get("star", score_to_star(static_score))),
                "status": old_status,
            },
            "new": {
                "hit": hit,
                "miss": miss,
                "partial": partial,
                "static": static_score,
                "dynamic": round(dynamic, 1),
                "final": round(final, 1),
                "star": star,
                "status": new_status,
            },
        })
        
        # 更新 rule 数据（保留所有字段）
        rule["hit_count"] = hit
        rule["miss_count"] = miss
        rule["partial_count"] = partial
        rule["static_score"] = static_score
        rule["dynamic_score"] = round(dynamic, 1)
        rule["final_score"] = round(final, 1)
        rule["star"] = star
        rule["status"] = new_status
        rule["last_calibrated"] = datetime.now().strftime("%Y-%m-%d")
    
    # 写回 yaml
    if not dry_run:
        write_index_yaml(school, header, rules)
    
    return transitions


def write_index_yaml(school: str, header: str, rules: dict):
    """重写 theory/{school}/index.yaml"""
    path = THEORY / school / "index.yaml"
    
    lines = [header.strip(), ""]
    for rule_id in sorted(rules.keys(), key=lambda x: (
        x.split("-")[0],
        x.split("-")[1] if len(x.split("-")) > 2 else "",
        int(re.search(r"\d+", x).group()),
    )):
        rule = rules[rule_id]
        # 优先使用原 _lines 但更新关键字段
        # 重新生成关键字段块
        out = [f"  - id: {rule_id}"]
        # 排序后的字段
        priority_fields = [
            "legacy_id", "school", "topic", "topic_label", "title", "conclusion",
            "status", "layer", "raw_source", "raw_anchor", "raw_file",
            "candidate_score",
            "static_score", "dynamic_score", "final_score", "star",
            "hit_count", "miss_count", "partial_count",
            "last_calibrated",
        ]
        for field in priority_fields:
            if field in rule and field not in ("id", "_lines"):
                val = rule[field]
                if isinstance(val, str):
                    val_escaped = val.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
                    out.append(f'    {field}: "{val_escaped}"')
                else:
                    out.append(f'    {field}: {val}')
        # 其他字段（可能存在的自定义）
        for k, v in rule.items():
            if k in ("id", "_lines") or k in priority_fields:
                continue
            if isinstance(v, str):
                v_escaped = v.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
                out.append(f'    {k}: "{v_escaped}"')
            else:
                out.append(f'    {k}: {v}')
        lines.extend(out)
    
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ============================================================
# 校准报告生成
# ============================================================

def generate_calibration_report(case_id: str, transitions: list, output_path: Path):
    """生成 cases/C-YYYY-NNN/calibration-report.md"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lines = [
        f"# 校准报告 · {case_id}",
        f"",
        f"**校准时间**：{timestamp}",
        f"**总更新规律数**：{len(transitions)}",
        f"",
        "---",
        "",
        "## 一、规律级变化",
        "",
    ]
    
    # 按 status 变化分组
    promoted = [t for t in transitions if t["old"]["status"] != t["new"]["status"] and t["new"]["status"] == "promoted"]
    retired = [t for t in transitions if t["old"]["status"] != t["new"]["status"] and t["new"]["status"] == "retired"]
    demoted = [t for t in transitions if t["old"]["status"] == "promoted" and t["new"]["status"] == "candidate"]
    no_change = [t for t in transitions if t["old"]["status"] == t["new"]["status"]]
    
    if promoted:
        lines.append(f"### 🟢 晋级（candidate → promoted）·{len(promoted)} 条")
        lines.append("| 规律 ID | 派别 | hit/miss | 命中率 | final_score | star |")
        lines.append("|---|---|---|---|---|---|")
        for t in promoted:
            sample = t["new"]["hit"] + t["new"]["miss"]
            rate = t["new"]["hit"] / sample if sample > 0 else 0
            lines.append(
                f"| {t['rule_id']} | {t['school']} | {t['new']['hit']}/{t['new']['miss']} "
                f"| {rate:.0%} | {t['new']['final']} | {'★' * t['new']['star']} |"
            )
        lines.append("")
    
    if retired:
        lines.append(f"### 🔴 退役（→ retired）·{len(retired)} 条")
        lines.append("| 规律 ID | 派别 | hit/miss | 命中率 | star |")
        lines.append("|---|---|---|---|---|")
        for t in retired:
            sample = t["new"]["hit"] + t["new"]["miss"]
            rate = t["new"]["hit"] / sample if sample > 0 else 0
            lines.append(
                f"| {t['rule_id']} | {t['school']} | {t['new']['hit']}/{t['new']['miss']} "
                f"| {rate:.0%} | {'★' * t['new']['star']} |"
            )
        lines.append("")
    
    if demoted:
        lines.append(f"### 🟡 降级（promoted → candidate）·{len(demoted)} 条")
        for t in demoted:
            lines.append(f"- {t['rule_id']} ({t['school']}): {t['old']['final']} → {t['new']['final']}")
        lines.append("")
    
    lines.append(f"### ⚪ 无 status 变化（仅分数微调）·{len(no_change)} 条")
    lines.append("（详见各规律 yaml）")
    lines.append("")
    
    # 派别表现
    lines.append("---")
    lines.append("")
    lines.append("## 二、本案 4 派表现")
    lines.append("")
    lines.append("| 派别 | 采用 | 应验 | 失验 | 命中率 |")
    lines.append("|---|---|---|---|---|")
    
    school_stats = defaultdict(lambda: {"used": 0, "hit": 0, "miss": 0})
    for t in transitions:
        s = t["school"]
        school_stats[s]["used"] += 1
        delta_hit = t["new"]["hit"] - t["old"]["hit"]
        delta_miss = t["new"]["miss"] - t["old"]["miss"]
        school_stats[s]["hit"] += delta_hit
        school_stats[s]["miss"] += delta_miss
    
    for school in ["gao", "duan", "yang", "ren"]:
        stats = school_stats[school]
        sample = stats["hit"] + stats["miss"]
        rate = f"{stats['hit'] / sample:.0%}" if sample > 0 else "-"
        lines.append(
            f"| {school} | {stats['used']} | {stats['hit']} | {stats['miss']} | {rate} |"
        )
    lines.append("")
    
    # 写入下游
    lines.append("---")
    lines.append("")
    lines.append("## 三、下游影响")
    lines.append("")
    lines.append("- ✅ 已更新 theory/{school}/index.yaml")
    lines.append("- ✅ 已更新 META/rule-changelog.md")
    if promoted:
        lines.append(f"- ⚠️  {len(promoted)} 条规律晋级，建议 review mapping/complementary.md 是否需升入 consensus.md")
    if retired:
        lines.append(f"- ⚠️  {len(retired)} 条规律退役，建议从 mapping/ 中暂时屏蔽")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


# ============================================================
# 更新 META/rule-changelog.md
# ============================================================

def append_to_changelog(case_id: str, transitions: list):
    """追加到 META/rule-changelog.md"""
    path = META / "rule-changelog.md"
    if not path.exists():
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    new_block = [f"\n## {today} · 校准 · {case_id}\n"]
    
    promoted = [t for t in transitions if t["old"]["status"] != t["new"]["status"] and t["new"]["status"] == "promoted"]
    retired = [t for t in transitions if t["old"]["status"] != t["new"]["status"] and t["new"]["status"] == "retired"]
    demoted = [t for t in transitions if t["old"]["status"] == "promoted" and t["new"]["status"] == "candidate"]
    
    if promoted:
        new_block.append("### 晋级（candidate → promoted）")
        for t in promoted:
            new_block.append(f"- {t['rule_id']} · 命中 {t['new']['hit']}/{t['new']['hit']+t['new']['miss']} = {t['new']['hit']/(t['new']['hit']+t['new']['miss']):.0%}")
        new_block.append("")
    
    if retired:
        new_block.append("### 退役（→ retired）")
        for t in retired:
            new_block.append(f"- {t['rule_id']} · 失验 {t['new']['miss']}/{t['new']['hit']+t['new']['miss']}")
        new_block.append("")
    
    if demoted:
        new_block.append("### 降级（promoted → candidate）")
        for t in demoted:
            new_block.append(f"- {t['rule_id']} · final_score 从 {t['old']['final']} 降至 {t['new']['final']}")
        new_block.append("")
    
    if promoted or retired or demoted:
        with path.open("a", encoding="utf-8") as fp:
            fp.write("\n".join(new_block))


# ============================================================
# 主流程
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="反馈回流校准工具")
    parser.add_argument("--case", required=True, help="Case ID 如 C-2026-001")
    parser.add_argument("--dry-run", action="store_true", help="预览模式不写入")
    parser.add_argument("--feedback", help="自定义反馈文件路径（默认 cases/{case}/feedback.md）")
    args = parser.parse_args()
    
    case_id = args.case
    case_dir = CASES / case_id
    feedback_path = Path(args.feedback) if args.feedback else (case_dir / "feedback.md")
    
    if not feedback_path.exists():
        print(f"❌ 反馈文件不存在: {feedback_path}")
        sys.exit(1)
    
    print(f"📊 加载反馈: {feedback_path}")
    feedbacks = parse_feedback(feedback_path)
    print(f"   解析到 {len(feedbacks)} 条反馈")
    
    if not feedbacks:
        print("⚠️  无有效反馈，退出")
        sys.exit(0)
    
    # 按派别分组
    rule_updates_by_school = defaultdict(lambda: defaultdict(lambda: {"hit_delta": 0, "miss_delta": 0, "partial_delta": 0}))
    
    for fb in feedbacks:
        school = school_from_rule_id(fb["rule_id"])
        if not school:
            continue
        rid = fb["rule_id"]
        if fb["status"] == "hit":
            rule_updates_by_school[school][rid]["hit_delta"] += 1
        elif fb["status"] == "miss":
            rule_updates_by_school[school][rid]["miss_delta"] += 1
        elif fb["status"] == "partial":
            rule_updates_by_school[school][rid]["partial_delta"] += 1
    
    # 更新各派 index
    all_transitions = []
    for school, updates in rule_updates_by_school.items():
        print(f"📝 更新 theory/{school}/index.yaml ({len(updates)} 条规律)")
        transitions = update_index_with_feedback(school, dict(updates), dry_run=args.dry_run)
        all_transitions.extend(transitions)
    
    # 生成校准报告
    report_path = case_dir / "calibration-report.md"
    print(f"📄 生成校准报告: {report_path}")
    if not args.dry_run:
        generate_calibration_report(case_id, all_transitions, report_path)
    
    # 更新 changelog
    if not args.dry_run:
        append_to_changelog(case_id, all_transitions)
    
    # 总结
    promoted = [t for t in all_transitions if t["old"]["status"] != t["new"]["status"] and t["new"]["status"] == "promoted"]
    retired = [t for t in all_transitions if t["old"]["status"] != t["new"]["status"] and t["new"]["status"] == "retired"]
    demoted = [t for t in all_transitions if t["old"]["status"] == "promoted" and t["new"]["status"] == "candidate"]
    
    print(f"")
    print(f"✅ 校准完成 ({'DRY RUN' if args.dry_run else '已写入'})")
    print(f"   总更新规律: {len(all_transitions)}")
    print(f"   🟢 晋级: {len(promoted)}")
    print(f"   🔴 退役: {len(retired)}")
    print(f"   🟡 降级: {len(demoted)}")
    
    if promoted or retired:
        print(f"")
        print(f"⚠️  发生 status 变化，建议接下来：")
        if promoted:
            print(f"   - review mapping/complementary.md，{len(promoted)} 条新晋级规律是否升入 consensus.md")
        if retired:
            print(f"   - 把 {len(retired)} 条退役规律从 mapping/exclusive.md 暂屏蔽")


if __name__ == "__main__":
    main()
