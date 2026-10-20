"""engine/predicates/condition_evaluator.py · 规则条件谓词求值器

用真实命盘谓词替代字符袋计数，提升规则触发精确度。

两个入口：
- evaluate_trigger(trigger, chart)  →  bool   用于有结构化 trigger 的生产规则
- trigger_evidence_status(trigger)  →  str    区分真实命中与证据不足
- score_blind_rule(rule_dict, chart) →  float  用于盲派 index.yaml 候选规则

ponytail: 不写新命理推理，只用已有 predicates/ 库做条件判断。
未知 trigger 返回 False，并标记 insufficient_evidence；不得因无法判断而放行。
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


def trigger_evidence_status(trigger: str) -> str:
    """返回 trigger 的证据状态，不把未知条件伪装成已满足。"""
    known = {
        "always",
        "has_energy_structure",
        "has_tiaohou_advice",
        "wuxing_imbalanced",
        "has_zhi_chong",
        "has_dayun",
        "has_xiaoyun",
        "has_liunian",
        "has_suiyun_interaction",
        "has_sanhe_partial",
        "has_sanxing",
        "has_kongwang",
        "has_zaisha",
        "has_wealth_picture",
        "has_official_picture",
        "has_marriage_picture",
    }
    return "evaluable" if trigger in known else "insufficient_evidence"


def evaluate_trigger(trigger: str, chart: dict[str, Any]) -> bool:
    """把结构化 trigger 字段映射到真实命盘谓词。

    返回 True 表示已知 trigger 在此命盘上激活。
    未知 trigger 返回 False，状态由 trigger_evidence_status 标为 insufficient_evidence。
    """
    if trigger_evidence_status(trigger) == "insufficient_evidence":
        return False
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
        return any(ch in _pillars_text(chart) for ch in ("财", "正财", "偏财")) or _picture_rank_within(
            chart, "caifu", 5
        )
    if trigger == "has_official_picture":
        return _picture_rank_within(chart, "guanming", 6)
    if trigger == "has_marriage_picture":
        return _picture_rank_within(chart, "marriage_picture", 6)
    return False


def _picture_rank_within(chart: dict[str, Any], key: str, max_rank: int) -> bool:
    """类象谓词：只在实质命中有该象时为 True。

    compute_caifu / compute_guanming / build_marriage_picture 对任何命盘都返回
    非空对象（最差也是 {"rank": 7, "type": "普通"}），直接 bool() 会恒真。
    以 rank 门槛判定：rank 数值越小越强，max_rank 即「有实质该象」的下限。
    """
    picture = chart.get("picture") or {}
    node = picture.get(key) if isinstance(picture, dict) else None
    if node is None:
        return False
    if isinstance(node, bool):
        return node
    if isinstance(node, (list, tuple, set)):
        return bool(node)
    if isinstance(node, dict):
        rank = node.get("rank")
        if rank is None:
            # 没有 rank 字段的类象（如 industry_pointers）退回到「有实质内容」。
            return bool(node)
        try:
            return int(rank) <= max_rank
        except (TypeError, ValueError):
            return False
    return bool(node)


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


def blind_rule_gate(rule: dict[str, Any], chart: dict[str, Any]) -> bool:
    """有显式条件必须求值通过；纯文本不得凭干支撞字成为有效证据。

    只有能映射到已知枚举的 trigger 才短路求值；中文自然语言 trigger
    （来自原稿回填）无法求值时退回正文关键词兜底，避免整条规则恒 False。

    注意：关键词兜底只扫 topic/title/conclusion，**不扫 condition/trigger**。
    原稿 trigger 里大量是否定前置条件（"官杀同柱不冲刑"、"五行独旺无克泄"）
    或元话术（"位置与生克关系已确定"），拼进来会让规则反向误召回。
    """
    trigger = str(rule.get("condition") or rule.get("trigger") or "").strip()
    if trigger and trigger_evidence_status(trigger) == "evaluable":
        return evaluate_trigger(trigger, chart)
    text = "".join(str(rule.get(k, "")) for k in ("topic", "topic_label", "title", "conclusion"))
    if any(tok in text for tok in _CHONG_TOKENS):
        return chart_has_zhi_chong(chart)
    if "墓" in text or "库" in text:
        return bool(_zhi_set(chart) & frozenset("辰戌丑未"))
    if "做功" in text:
        return bool(chart.get("energy", {}).get("layer_count"))
    return False


def score_blind_rule(rule: dict[str, Any], chart: dict[str, Any]) -> float:
    """只给通过结构门禁的规则打分；字符重合不再加分。

    candidate_score 存在两套量纲：高派/杨派为 0~1，段派为 3.0~5.0 分制。
    超过 1.0 的按 5 分制归一化，否则 min(..., 1.0) 会把段派分数全部削平成 1.0，
    排序退化为按 id 字典序（2026-10-19 实测）。
    """
    if not blind_rule_gate(rule, chart):
        return 0.0
    raw = float(rule.get("candidate_score") or 0.5)
    if raw > 1.0:
        return min(raw / 5.0, 1.0)
    return min(raw, 1.0)


def rank_blind_rule(rule: dict[str, Any], chart: dict[str, Any]) -> tuple[float, int, str]:
    """排序键：(-score, status_rank, id)——score 高的优先。"""
    score = score_blind_rule(rule, chart)
    status = str(rule.get("status", "candidate"))
    status_rank = {"confirmed": 0, "promoted": 0, "active": 0, "candidate": 1}.get(status, 2)
    return (-score, status_rank, str(rule.get("id", "")))
