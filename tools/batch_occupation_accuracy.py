"""批量评估：职业方向4大类分类命中率。

支持两种数据集：
  RF 系列：438 个已排盘 as-of 候选案例（cases/C-2026-RF*），真值来自
           real_cases_990.jsonl 的 profile.occupation 自由文本（标签噪声高）。
  P 系列：cases/shuru-input.md + cases/fankui-feedback.md 的 76 个人工整理案例，
           真值来自 fankui-feedback.md 的"职业"字段；该字段覆盖率极低，只能
           在达到最低有效样本门槛后用于统计对照。

报告同时呈现覆盖率、描述性命中率和样本充分性；样本不足时不作根因判决。

用户定义的4大类（reports/session-summary-2026-07-30.md § 3.2）：
    tech        技术专业输出型（程序员/工程师/医生/律师等）
    manage      管理资源调配型（管理层/公务员/党政军）
    business    商业财运主导型（老板/销售/个体户）
    art         艺文创意服务型（教师/艺术家/服务业）

不修改任何规则、不写回 cases/，纯只读评估。
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from engine.predicates.ganzhi import get_canggan
from engine.predicates.palace import get_shishen

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "cases" / "raw_feedback" / "parsed" / "real_cases_990.jsonl"
DEFAULT_CASES_ROOT = ROOT / "cases"
DEFAULT_SHURU = ROOT / "cases" / "shuru-input.md"
DEFAULT_FANKUI = ROOT / "cases" / "fankui-feedback.md"

CATEGORY_LABELS = {
    "tech": "技术专业输出型",
    "manage": "管理资源调配型",
    "business": "商业财运主导型",
    "art": "艺文创意服务型",
}

# ---------------------------------------------------------------------------
# 1. 真实职业标签：从 profile.occupation 自由文本映射到4大类
# ---------------------------------------------------------------------------

# 关键词按优先级排列；命中即归类，不做加权评分（与用户"宽松分类"表述一致）。
_TRUTH_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("manage", (
        "公务员", "事业单位", "体制内", "国企", "央企", "党政", "机关", "编制",
        "领导", "主管", "经理", "总监", "总裁", "厂长", "干部", "军人", "警察",
        "公安", "法官", "检察", "处长", "科长", "局长", "部长", "行长", "院长",
        "leader", "管理岗", "中层", "高管",
    )),
    ("tech", (
        "程序员", "工程师", "医生", "律师", "会计", "技术员", "研发", "码农",
        "软件", "开发", "架构师", "设计师", "护士", "药剂师", "技师", "施工",
        "机械", "电工", "数据", "分析师", "计算机", "computer science", "it ",
        "建筑师", "测绘",
    )),
    ("business", (
        "老板", "个体户", "自由职业", "自主创业", "创业", "销售", "业务员",
        "经商", "生意", "开店", "私企", "私营", "个体", "商人", "股票", "投资",
        "淘宝", "电商", "微商", "自由", "自营", "包工头",
    )),
    ("art", (
        "教师", "老师", "艺术家", "美术", "音乐", "舞蹈", "服务业", "服务员",
        "厨师", "美容", "美发", "导游", "主播", "演员", "文员", "客服", "餐饮",
        "教育", "培训", "作家", "编辑", "记者", "设计（美术）",
    )),
)

_NOISE_PATTERNS = (
    "婚姻", "健康", "学业", "感情", "分手", "父母", "家庭", "子女", "收入",
    "财运", "性格", "从格", "用神",
)

_MIN_LABEL_LEN = 2
_MAX_LABEL_LEN = 40  # 超过此长度的自由文本多为提问语境而非纯职业标签
_MIN_COMPARISON_SAMPLES = 20
_MISSING_OCCUPATION_VALUES = {"来源未提供", "未提供", "未知", "不详"}


def truth_category(raw_occupation: str) -> str | None:
    """把 profile.occupation 原始文本映射为4大类之一，不可分类返回 None。

    保留判定思路：
    - 空文本 / 明显与职业无关（婚姻/健康/学业话题误落入该字段）→ None
    - 过长文本（多为提问描述而非职业标签，噪声混入信号）→ 仍按关键词试分类，
      但要求命中优先级最高类别的关键词，否则 None
    """
    text = (raw_occupation or "").strip()
    if not text or len(text) < _MIN_LABEL_LEN:
        return None

    # 否定短语不能作为类别证据，例如“会计人员（非财务管理岗位）”中的“管理岗”。
    classification_text = re.sub(r"非[^，；。）（()]{0,12}管理岗位", "", text)
    lowered = classification_text.lower()

    # 若文本主体是纯噪声话题（婚姻/健康...）且不含任何职业关键词，直接判空
    has_any_keyword = any(
        kw in classification_text or kw.lower() in lowered
        for _, keywords in _TRUTH_KEYWORDS
        for kw in keywords
    )
    if not has_any_keyword:
        return None

    for category, keywords in _TRUTH_KEYWORDS:
        for kw in keywords:
            if kw in classification_text or kw.lower() in lowered:
                return category
    return None


# ---------------------------------------------------------------------------
# 2. 预测：从四柱十神结构预测职业方向4大类
# ---------------------------------------------------------------------------

_TEN_GODS = ("比肩", "劫财", "食神", "伤官", "正财", "偏财", "正官", "七杀", "正印", "偏印")

_PILLAR_RE = re.compile(
    r"年柱:\s*[\"']?([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])[\"']?\s*"
    r"\n\s*月柱:\s*[\"']?([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])[\"']?\s*"
    r"\n\s*日柱:\s*[\"']?([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])[\"']?\s*"
    r"\n\s*时柱:\s*[\"']?([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])[\"']?",
)


def parse_pillars_from_input_md(text: str) -> tuple[str, str, str, str] | None:
    match = _PILLAR_RE.search(text)
    if not match:
        return None
    return (match.group(1), match.group(2), match.group(3), match.group(4))


def ten_god_counts(pillars: tuple[str, str, str, str]) -> dict[str, int]:
    day_master = pillars[2][0]
    gans = [p[0] for p in pillars]
    zhis = [p[1] for p in pillars]
    counts = Counter({name: 0 for name in _TEN_GODS})
    for gan in gans:
        counts[get_shishen(gan, day_master)] += 1
    for zhi in zhis:
        for hidden in get_canggan(zhi):
            counts[get_shishen(hidden.gan, day_master)] += 1
    return dict(counts)


def predict_category(counts: dict[str, int]) -> str:
    """十神计数 → 职业方向4大类预测。

    规则（对齐用户4大类定义）：
        manage:   正官 + 正印 占优（官印相生 = 体制/管理路径）
        tech:     食神 + 伤官 占优，且官杀不占优（专业技术输出路径）
        business: 正财 + 偏财 + 比肩 + 劫财 占优（财星/比劫 = 经商路径）
        art:      印星占优但官杀弱、食伤弱（偏印/正印为主的教育文教服务路径）

    采用"取最大总分类别"的方式（而非门限硬编码），四类各自的加权分：
        manage_score   = 正官*1.5 + 七杀*1.0 + 正印*0.5
        tech_score     = 食神*1.0 + 伤官*1.2 + 正印*0.3
        business_score = 正财*1.2 + 偏财*1.5 + 比肩*0.6 + 劫财*0.6
        art_score      = 正印*1.0 + 偏印*1.2 + 食神*0.3
    """
    manage_score = counts.get("正官", 0) * 1.5 + counts.get("七杀", 0) * 1.0 + counts.get("正印", 0) * 0.5
    tech_score = counts.get("食神", 0) * 1.0 + counts.get("伤官", 0) * 1.2 + counts.get("正印", 0) * 0.3
    business_score = (
        counts.get("正财", 0) * 1.2 + counts.get("偏财", 0) * 1.5
        + counts.get("比肩", 0) * 0.6 + counts.get("劫财", 0) * 0.6
    )
    art_score = counts.get("正印", 0) * 1.0 + counts.get("偏印", 0) * 1.2 + counts.get("食神", 0) * 0.3

    scores = {
        "manage": manage_score,
        "tech": tech_score,
        "business": business_score,
        "art": art_score,
    }
    return max(scores, key=lambda k: (scores[k], -list(scores).index(k)))


# ---------------------------------------------------------------------------
# 3. 数据装配
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class EvalRow:
    case_id: str
    raw_id: str
    pillars: tuple[str, str, str, str]
    occupation_raw: str
    truth: str | None
    predicted: str


def load_raw_records(source: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        raw_id = str(rec.get("raw_id", ""))
        if raw_id:
            records[raw_id] = rec
    return records


_CASE_DIR_RE = re.compile(r"^C-2026-RF(\d{6})-([乾坤])-([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]{8}|.+)$")

# 天干地支字符集，用于正则验证
_GAN = "甲乙丙丁戊己庚辛壬癸"
_ZHI = "子丑寅卯辰巳午未申酉戌亥"
_GANZHI_RE = re.compile(rf"[{_GAN}][{_ZHI}]")


def resolve_raw_id(case_dir_name: str) -> str | None:
    match = re.match(r"^C-2026-RF(\d{6})-", case_dir_name)
    if not match:
        return None
    return f"RF-2026-{match.group(1)}"


# ---------------------------------------------------------------------------
# P 系列解析：shuru-input.md + fankui-feedback.md
# ---------------------------------------------------------------------------

_P_SECTION_RE = re.compile(
    r"^##\s+(P-2026-\d{3})\s*·\s*([乾坤])\s*·\s*([^\n]+)",
    re.MULTILINE,
)
_SIZHU_LINE_RE = re.compile(
    rf"四柱[：:]\s*(([{_GAN}][{_ZHI}]\s*){{4}})"
)
_OCCUPATION_LINE_RE = re.compile(r"职业[：:]\s*(.+)")


def _parse_pillars_from_sizhu_line(line: str) -> tuple[str, str, str, str] | None:
    """从"四柱：甲子 乙丑 丙寅 丁卯"行提取四柱。"""
    ganzhi_tokens = _GANZHI_RE.findall(line)
    if len(ganzhi_tokens) >= 4:
        return tuple(ganzhi_tokens[:4])  # type: ignore[return-value]
    return None


def _split_p_sections(text: str) -> dict[str, str]:
    """把 md 文件按 ## P-2026-NNN 标题拆成 {case_id: section_text}。"""
    sections: dict[str, str] = {}
    matches = list(_P_SECTION_RE.finditer(text))
    for idx, m in enumerate(matches):
        case_id = m.group(1)
        start = m.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        sections[case_id] = text[start:end]
    return sections


def collect_p_series_rows(
    shuru_path: Path,
    fankui_path: Path,
) -> tuple[list[EvalRow], list[str]]:
    """从 shuru-input.md 取四柱，从 fankui-feedback.md 取职业字段，组装 EvalRow。"""
    shuru_text = shuru_path.read_text(encoding="utf-8")
    fankui_text = fankui_path.read_text(encoding="utf-8")

    shuru_sections = _split_p_sections(shuru_text)
    fankui_sections = _split_p_sections(fankui_text)

    rows: list[EvalRow] = []
    skipped: list[str] = []

    for case_id, shuru_sec in sorted(shuru_sections.items()):
        # 四柱
        sizhu_m = _SIZHU_LINE_RE.search(shuru_sec)
        if sizhu_m is None:
            skipped.append(f"{case_id}: 无法找到四柱行")
            continue
        pillars = _parse_pillars_from_sizhu_line(sizhu_m.group(0))
        if pillars is None:
            skipped.append(f"{case_id}: 四柱解析失败 ({sizhu_m.group(0)!r})")
            continue

        # 职业真值来自 fankui
        fankui_sec = fankui_sections.get(case_id, "")
        occ_m = _OCCUPATION_LINE_RE.search(fankui_sec)
        occupation_raw = occ_m.group(1).strip() if occ_m else ""
        truth = truth_category(occupation_raw) if occupation_raw else None

        counts = ten_god_counts(pillars)
        predicted = predict_category(counts)
        rows.append(EvalRow(
            case_id=case_id,
            raw_id=case_id,
            pillars=pillars,
            occupation_raw=occupation_raw,
            truth=truth,
            predicted=predicted,
        ))

    return rows, skipped


def collect_eval_rows(cases_root: Path, raw_records: dict[str, dict[str, Any]]) -> tuple[list[EvalRow], list[str]]:
    rows: list[EvalRow] = []
    skipped: list[str] = []
    for case_dir in sorted(cases_root.glob("C-2026-RF*-*")):
        if not case_dir.is_dir():
            continue
        input_path = case_dir / "input.md"
        if not input_path.exists():
            skipped.append(f"{case_dir.name}: 无 input.md")
            continue
        raw_id = resolve_raw_id(case_dir.name)
        if raw_id is None or raw_id not in raw_records:
            skipped.append(f"{case_dir.name}: 无法反查 raw_id={raw_id}")
            continue
        text = input_path.read_text(encoding="utf-8")
        pillars = parse_pillars_from_input_md(text)
        if pillars is None:
            skipped.append(f"{case_dir.name}: 无法解析四柱")
            continue
        occupation_raw = str((raw_records[raw_id].get("profile") or {}).get("occupation", "") or "").strip()
        truth = truth_category(occupation_raw)
        counts = ten_god_counts(pillars)
        predicted = predict_category(counts)
        rows.append(
            EvalRow(
                case_id=case_dir.name,
                raw_id=raw_id,
                pillars=pillars,
                occupation_raw=occupation_raw,
                truth=truth,
                predicted=predicted,
            )
        )
    return rows, skipped


# ---------------------------------------------------------------------------
# 4. 统计与报告
# ---------------------------------------------------------------------------

def _section_stats(rows: list[EvalRow], skipped: list[str], title: str) -> list[str]:
    """为一组 rows 输出统计表格（可复用给 RF 和 P 两组）。"""
    total_cases = len(rows) + len({s.split(":")[0] for s in skipped})
    labeled = [r for r in rows if r.truth is not None]
    unlabeled = [r for r in rows if r.truth is None]

    confusion: dict[str, Counter] = defaultdict(Counter)
    for r in labeled:
        confusion[r.truth][r.predicted] += 1

    correct = sum(1 for r in labeled if r.truth == r.predicted)
    overall_rate = correct / len(labeled) if labeled else 0.0

    lines: list[str] = []
    lines.append(f"## {title}\n")
    lines.append(f"- 案例数：{total_cases}")
    lines.append(f"- 成功解析四柱：{len(rows)}")
    lines.append(f"- 解析失败跳过：{len(skipped)}")
    lines.append(f"- 有效真值样本（occupation 可映射4大类）：{len(labeled)}")
    lines.append(f"- 无法映射（噪声/未提供）：{len(unlabeled)}")
    lines.append(f"- **有效标签率：{len(labeled)/total_cases:.1%}**")
    lines.append("")
    lines.append(f"### 总体命中率：{correct}/{len(labeled)} = **{overall_rate:.1%}**\n")

    lines.append("### 混淆矩阵（行=真实，列=预测）\n")
    header = ["真实\\预测"] + [CATEGORY_LABELS[c] for c in CATEGORY_LABELS]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "---|" * len(header))
    for truth_cat in CATEGORY_LABELS:
        row_counts = confusion.get(truth_cat, Counter())
        row_total = sum(row_counts.values())
        cells = [str(row_counts.get(pred_cat, 0)) for pred_cat in CATEGORY_LABELS]
        lines.append(f"| {CATEGORY_LABELS[truth_cat]}（n={row_total}） | " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("### 按真实类别的命中率\n")
    lines.append("| 类别 | 样本数 | 命中 | 命中率 |")
    lines.append("|---|---|---|---|")
    for truth_cat in CATEGORY_LABELS:
        row_counts = confusion.get(truth_cat, Counter())
        n = sum(row_counts.values())
        hit = row_counts.get(truth_cat, 0)
        rate = hit / n if n else 0.0
        lines.append(f"| {CATEGORY_LABELS[truth_cat]} | {n} | {hit} | {rate:.1%} |")
    lines.append("")

    lines.append("### 预测分布（模型塌陷检查）\n")
    pred_counter = Counter(r.predicted for r in labeled)
    lines.append("| 预测类别 | 次数 | 占比 |")
    lines.append("|---|---|---|")
    for cat in CATEGORY_LABELS:
        n = pred_counter.get(cat, 0)
        rate = n / len(labeled) if labeled else 0.0
        lines.append(f"| {CATEGORY_LABELS[cat]} | {n} | {rate:.1%} |")
    lines.append("")

    lines.append("### 误判样本（前10条）\n")
    lines.append("| case_id | 真实 | 预测 | occupation原文（截断） |")
    lines.append("|---|---|---|---|")
    mismatches = [r for r in labeled if r.truth != r.predicted]
    for r in mismatches[:10]:
        snippet = r.occupation_raw.replace("|", "\\|").replace("\n", " ")[:60]
        lines.append(f"| {r.case_id} | {CATEGORY_LABELS[r.truth]} | {CATEGORY_LABELS[r.predicted]} | {snippet} |")
    lines.append("")

    if skipped:
        lines.append(f"### 跳过明细（前10条，共{len(skipped)}条）\n")
        for s in skipped[:10]:
            lines.append(f"- {s}")
        lines.append("")

    return lines


def build_report(
    rf_rows: list[EvalRow],
    rf_skipped: list[str],
    p_rows: list[EvalRow],
    p_skipped: list[str],
) -> str:
    rf_labeled = [r for r in rf_rows if r.truth is not None]
    p_labeled = [r for r in p_rows if r.truth is not None]
    rf_correct = sum(1 for r in rf_labeled if r.truth == r.predicted)
    p_correct = sum(1 for r in p_labeled if r.truth == r.predicted)
    rf_rate = rf_correct / len(rf_labeled) if rf_labeled else 0.0
    p_rate = p_correct / len(p_labeled) if p_labeled else 0.0

    lines: list[str] = []
    lines.append("# 职业方向4大类分类命中率批量评估（RF系列 vs P系列对比）\n")
    lines.append("> 目的：评估两组数据的职业真值覆盖率与描述性命中率。")
    lines.append("> 只有两组均达到最低有效样本门槛，才比较命中率并判断标签噪声或模型能力。\n")

    # 摘要对比表
    lines.append("## 摘要对比\n")
    lines.append("| 指标 | RF 系列（自动排盘，自由文本标签） | P 系列（人工整理，叙事反馈） |")
    lines.append("|---|---|---|")
    lines.append(f"| 案例总数 | {len(rf_rows) + len(rf_skipped)} | {len(p_rows) + len(p_skipped)} |")
    lines.append(f"| 有效真值样本 | {len(rf_labeled)} | {len(p_labeled)} |")
    lines.append(f"| 有效标签率 | {len(rf_labeled)/(len(rf_rows)+len(rf_skipped)):.1%} | {len(p_labeled)/(len(p_rows)+len(p_skipped)):.1%} |")
    lines.append(f"| 总体命中率 | **{rf_rate:.1%}** | **{p_rate:.1%}** |")
    lines.append("")

    # 根因判断：小样本命中率波动极大，不能拿来做数据集间归因。
    gap = p_rate - rf_rate
    if len(rf_labeled) < _MIN_COMPARISON_SAMPLES or len(p_labeled) < _MIN_COMPARISON_SAMPLES:
        verdict = (
            f"**样本不足，不作统计归因。** 最低门槛为每组 {_MIN_COMPARISON_SAMPLES} 个有效真值；"
            f"当前 RF={len(rf_labeled)}、P={len(p_labeled)}。P 系列的 {p_correct}/{len(p_labeled)} "
            "仅是描述性结果，不能证明标签噪声或模型能力是主因。"
        )
    elif abs(gap) < 0.05:
        verdict = f"两组命中率差异 < 5%（{gap:+.1%}），模型能力弱于标签质量差异的解释力。"
    elif gap > 0:
        verdict = f"P 系列命中率比 RF 系列高 {gap:.1%}，标签噪声可能是重要根因，但仍需结合绝对命中率判断模型能力。"
    else:
        verdict = f"P 系列命中率比 RF 系列低 {-gap:.1%}，需复核标签映射与数据分布差异。"

    lines.append(f"### 根因判断\n\n{verdict}\n")

    lines += _section_stats(rf_rows, rf_skipped, "RF 系列详情（real_cases_990.jsonl，自动排盘，自由文本标签）")
    lines += _section_stats(p_rows, p_skipped, "P 系列详情（shuru-input.md + fankui-feedback.md，人工整理案例）")

    # P 系列所有实际职业描述均列出，避免只看两条关键词可映射样本。
    p_described = [
        row for row in p_rows
        if row.occupation_raw
        and row.occupation_raw.strip() not in _MISSING_OCCUPATION_VALUES
    ]
    lines.append("## P 系列职业描述定性核对\n")
    lines.append(f"共 {len(p_described)} 条实际职业描述；其中只有 {len(p_labeled)} 条可由当前关键词表映射到4类。")
    lines.append("本表用于逐案审计，不参与样本不足条件下的统计归因。\n")
    lines.append("| case_id | 四柱 | 职业原文 | 关键词真值 | 临时模型预测 | 命中 |")
    lines.append("|---|---|---|---|---|---|")
    for row in p_described:
        truth_label = CATEGORY_LABELS[row.truth] if row.truth is not None else "不可映射"
        hit = "是" if row.truth is not None and row.truth == row.predicted else ("否" if row.truth is not None else "不适用")
        occupation = row.occupation_raw.replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {row.case_id} | {' '.join(row.pillars)} | {occupation} | "
            f"{truth_label} | {CATEGORY_LABELS[row.predicted]} | {hit} |"
        )
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--cases-root", type=Path, default=DEFAULT_CASES_ROOT)
    parser.add_argument("--shuru", type=Path, default=DEFAULT_SHURU)
    parser.add_argument("--fankui", type=Path, default=DEFAULT_FANKUI)
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "occupation-4class-accuracy-2026-07-30.md")
    args = parser.parse_args()

    raw_records = load_raw_records(args.source)
    rf_rows, rf_skipped = collect_eval_rows(args.cases_root, raw_records)
    p_rows, p_skipped = collect_p_series_rows(args.shuru, args.fankui)
    report = build_report(rf_rows, rf_skipped, p_rows, p_skipped)
    args.out.write_text(report, encoding="utf-8")
    print(f"报告已写入 {args.out}")
    print(f"RF系列：{len(rf_rows)}案例，{sum(1 for r in rf_rows if r.truth is not None)}个有效真值")
    print(f"P系列：{len(p_rows)}案例，{sum(1 for r in p_rows if r.truth is not None)}个有效真值")


if __name__ == "__main__":
    main()
