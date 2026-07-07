"""engine/predicates/condition_evaluator.py · 规则条件谓词求值器

用真实命盘谓词替代字符袋计数，提升规则触发精确度。

两个入口：
- evaluate_trigger(trigger, chart)  →  bool   用于有结构化 trigger 的生产规则
- score_blind_rule(rule_dict, chart) →  float  用于盲派 index.yaml 候选规则

ponytail: 不写新命理推理，只用已有 predicates/ 库做条件判断。
未知触发类型保守放行（return True），避免误杀有效规则。
"""
from __future__ import annotations

from typing import Any

# ── 干支常量 ────────────────────────────────────────────────────────────────
_TIANGAN = frozenset("甲乙丙丁戊己庚辛壬癸")
_DIZHI   = frozenset("子丑寅卯辰巳午未申酉戌亥")
_GANZHI  = _TIANGAN | _DIZHI

# 地支六冲对
_ZHI_CHONG_PAIRS: list[frozenset[str]] = [
    frozenset(("子", "午")),
    frozenset(("丑", "未")),
    frozenset(("寅", "申")),
    frozenset(("卯", "酉")),
    frozenset(("辰", "戌")),
    frozenset(("巳", "亥")),
]

# 五行字符集
_WUXING_CHARS: dict[str, frozenset[str]] = {
    "木": frozenset("甲乙寅卯"),
    "火": frozenset("丙丁巳午"),
    "土": frozenset("戊己辰戌丑未"),
    "金": frozenset("庚辛申酉"),
    "水": frozenset("壬癸亥子"),
}

# 地支三刑（寅巳申 / 丑戌未 / 子卯）
_SANXING_SETS: list[frozenset[str]] = [
    frozenset(("寅", "巳", "申")),
    frozenset(("丑", "戌", "未")),
    frozenset(("子", "卯")),
]

# 空亡查表：纳甲六十花甲每旬空亡
_KONGWANG_TABLE: dict[str, tuple[str, str]] = {
    "甲子": ("戌", "亥"), "甲戌": ("申", "酉"), "甲申": ("午", "未"),
    "甲午": ("辰", "巳"), "甲辰": ("寅", "卯"), "甲寅": ("子", "丑"),
    "甲子旬": ("戌", "亥"),
}


# ── 命盘文本提取 ─────────────────────────────────────────────────────────────

def _pillars_text(chart: dict[str, Any]) -> str:
    """提取四柱干支字符串（不含大运流年）。"""
    pillars = chart.get("pillars") or {}
    if isinstance(pillars, dict):
        return "".join(str(pillars.get(k, "")) for k in ("year", "month", "day", "hour"))
    if isinstance(pillars, list):
        return "".join(str(p) for p in pillars)
    return str(pillars)


def _full_text(chart: dict[str, Any]) -> str:
    """四柱 + 大运 + 流年。"""
    return _pillars_text(chart) + str(chart.get("current_dayun") or "") + str(chart.get("current_year") or "")


def _zhi_set(chart: dict[str, Any]) -> frozenset[str]:
    return frozenset(ch for ch in _pillars_text(chart) if ch in _DIZHI)


def _gan_set(chart: dict[str, Any]) -> frozenset[str]:
    return frozenset(ch for ch in _pillars_text(chart) if ch in _TIANGAN)


# ── 基础谓词 ─────────────────────────────────────────────────────────────────

def chart_has_zhi_chong(chart: dict[str, Any]) -> bool:
    """四柱（含大运流年）中存在任意地支六冲。"""
    text = _full_text(chart)
    present = frozenset(ch for ch in text if ch in _DIZHI)
    return any(pair <= present for pair in _ZHI_CHONG_PAIRS)


def chart_wuxing_missing(chart: dict[str, Any]) -> list[str]:
    """返回四柱中缺失的五行列表。"""
    text = _pillars_text(chart)
    return [wx for wx, chars in _WUXING_CHARS.items() if not any(ch in text for ch in chars)]


def chart_wuxing_dominant(chart: dict[str, Any]) -> tuple[str, int]:
    """返回最旺的五行及其字符数。"""
    text = _pillars_text(chart)
    counts = {wx: sum(1 for ch in text if ch in chars) for wx, chars in _WUXING_CHARS.items()}
    return max(counts.items(), key=lambda kv: kv[1])


def chart_has_sanxing(chart: dict[str, Any]) -> bool:
    """四柱含任意三刑组合（寅巳申 / 丑戌未 / 子卯）。"""
    zhi = _zhi_set(chart)
    return any(pair <= zhi for pair in _SANXING_SETS)


def chart_has_shensha(name: str, chart: dict[str, Any]) -> bool:
    """查 chart['shensha'] 中是否含指定神煞名称。"""
    shensha_raw = chart.get("shensha") or {}
    if isinstance(shensha_raw, dict):
        return any(name in v for v in shensha_raw.values() if isinstance(v, (list, str)))
    return False


def chart_has_dayun(chart: dict[str, Any]) -> bool:
    return bool(chart.get("current_dayun"))


def chart_has_liunian(chart: dict[str, Any]) -> bool:
    return bool(chart.get("current_year"))


# ── 触发器求值（生产规则 trigger 字段）───────────────────────────────────────

_TRIGGER_DISPATCH: dict[str, Any] = {}  # 延迟构建，下面 evaluate_trigger 内完成


def evaluate_trigger(trigger: str, chart: dict[str, Any]) -> bool:
    """把结构化 trigger 字段映射到真实命盘谓词。

    返回 True 表示规则在此命盘上激活。
    未知 trigger 保守放行（True），不误杀有效规则。
    """
    if trigger in ("always", "has_energy_structure", "has_tiaohou_advice"):
        return True
    if trigger == "wuxing_imbalanced":
        return bool(chart_wuxing_missing(chart))
    if trigger == "has_zhi_chong":
        return chart_has_zhi_chong(chart)
    if trigger in ("has_dayun", "has_xiaoyun"):
        return chart_has_dayun(chart)
    if trigger in ("has_liunian", "has_suiyun_interaction"):
        return chart_has_liunian(chart)
    if trigger == "has_sanhe_partial":
        # 三合半合：找是否有三合局中两字共现
        _SANHE_TRIPLES = [frozenset("申子辰"), frozenset("寅午戌"), frozenset("巳酉丑"), frozenset("亥卯未")]
        zhi = _zhi_set(chart)
        return any(len(triple & zhi) >= 2 for triple in _SANHE_TRIPLES)
    if trigger == "has_sanxing":
        return chart_has_sanxing(chart)
    if trigger == "has_kongwang":
        return chart_has_shensha("空亡", chart)
    if trigger == "has_zaisha":
        return chart_has_shensha("灾煞", chart)
    if trigger == "has_wealth_picture":
        return any(ch in _pillars_text(chart) for ch in ("财", "正财", "偏财")) or bool(
            chart.get("picture", {}).get("caifu")
        )
    if trigger == "has_official_picture":
        return bool(chart.get("picture", {}).get("guanming"))
    if trigger == "has_marriage_picture":
        return bool(chart.get("picture", {}).get("marriage_picture"))
    # ponytail: 未知 trigger 保守放行
    return True


# ── 盲派候选规则评分 ─────────────────────────────────────────────────────────

# 命盘中明文出现的冲刑关键字
_CHONG_TOKENS = ("冲", "刑", "穿", "破", "悖", "克")
# 应期相关词
_TIMING_TOKENS = ("大运", "流年", "岁运", "应期", "交运", "运程")

# 特殊干支对：如果规则明确提及某对，且命盘中两字都出现，加分
_NOTABLE_PAIRS: list[tuple[str, str]] = [
    ("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥"),  # 六冲
    ("甲", "己"), ("乙", "庚"), ("丙", "辛"), ("丁", "壬"), ("戊", "癸"),              # 天干五合
]


def score_blind_rule(rule: dict[str, Any], chart: dict[str, Any]) -> float:
    """给盲派 index.yaml 候选规则在当前命盘上打一个 0.0-1.0 的相关度分。

    算法（ponytail：不写命理，只做结构性匹配）：
    1. 基础分 = candidate_score（已有人工评估）
    2. 规则结论中明确提及的干支，在命盘中真实存在 → 加分
    3. 规则结论提及冲刑，且命盘有真实六冲 → 加分
    4. 规则涉及应期词，且有大运流年 → 加分
    5. 规则提及特定干支对（非单字），且两字同时在命盘 → 加分
    6. 五行缺失规则只在命盘确实缺五行时加分

    返回归一化分数，最高 1.0。
    """
    base = float(rule.get("candidate_score") or 0.5)

    rule_text = "".join(
        str(rule.get(k, ""))
        for k in ("topic", "topic_label", "title", "conclusion", "raw_anchor")
    )

    pillars_text = _pillars_text(chart)
    full_text    = _full_text(chart)
    present_zhi  = _zhi_set(chart)
    present_gan  = _gan_set(chart)
    present_all  = present_zhi | present_gan

    bonus = 0.0

    # 1. 单字干支命中（规则提到的干支在命盘中存在）
    rule_ganzhi = frozenset(ch for ch in rule_text if ch in _GANZHI)
    if rule_ganzhi:
        hit_ratio = len(rule_ganzhi & present_all) / len(rule_ganzhi)
        bonus += 0.15 * hit_ratio

    # 2. 显式干支对命中（两字同时存在）
    pair_hits = sum(
        1 for a, b in _NOTABLE_PAIRS
        if a in rule_text and b in rule_text and a in full_text and b in full_text
    )
    bonus += 0.08 * min(pair_hits, 2)

    # 3. 冲刑规则 + 命盘有真实六冲
    if any(tok in rule_text for tok in _CHONG_TOKENS) and chart_has_zhi_chong(chart):
        bonus += 0.10

    # 4. 应期词 + 有大运流年
    if any(tok in rule_text for tok in _TIMING_TOKENS) and (chart_has_dayun(chart) or chart_has_liunian(chart)):
        bonus += 0.06

    # 5. 五行偏枯规则：命盘确实缺五行才加分
    if any(wx in rule_text for wx in ("偏枯", "缺")) and chart_wuxing_missing(chart):
        bonus += 0.08

    # 6. 三刑规则：命盘有真实三刑才加分
    if "三刑" in rule_text and chart_has_sanxing(chart):
        bonus += 0.08

    return min(base + bonus, 1.0)


def rank_blind_rule(rule: dict[str, Any], chart: dict[str, Any]) -> tuple[float, int, str]:
    """排序键：(-score, status_rank, id)——score 高的优先。"""
    score = score_blind_rule(rule, chart)
    status = str(rule.get("status", "candidate"))
    status_rank = {"confirmed": 0, "promoted": 1, "active": 1, "candidate": 2}.get(status, 3)
    return (-score, status_rank, str(rule.get("id", "")))
