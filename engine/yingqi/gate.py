"""engine/yingqi/gate.py · v1.2 D3 任派 · gate_yingqi 主入口

按 04-gate-protocol.md § 六 实现。

主流程：
    1. 三层判定（L1 / L2 / L3）→ passed_layers
    2. 上游一致性校验（check_against_energy / check_against_picture）
    3. picture_consistent=False → 强制 passed_layers = min(passed_layers, 1)
        ← 修复 G2（C-2026-001 婚期偏差 8 年）的核心机制
    4. 12 道门分类
    5. 计算 confidence（按 06 § 四 应期专用公式）
    6. 收集 evidence + 返回 GateResult

API（与 04 契约一致）：
    gate_yingqi(year, candidate_event, domain, energy, picture, parsed) -> GateResult

作者：Track-C
"""
from __future__ import annotations

from typing import Optional

from engine.energy.types import (
    Confidence,
    EnergyFindings,
    Evidence,
)
from engine.picture.types import PictureFindings
from engine.predicates.cycles import liunian_ganzhi
from engine.predicates.types import ParsedInput

from engine.yingqi.keys import infer_sub_domain
from engine.yingqi.menshu import classify_into_12_doors
from engine.yingqi.threelayer import (
    layer1_check,
    layer2_check,
    layer3_check,
)
from engine.yingqi.types import (
    GateResult,
    LayerCheck,
    PASSED_LAYERS_TO_STAR_CEILING,
    TriggerEvent,
)


# ============================================================
# 一、上游一致性校验
# ============================================================

# 成立性事件关键词（这些事件 = 需要 capable=True）
_SUCCESS_KEYWORDS: tuple[str, ...] = (
    "结婚", "成婚", "嫁", "娶", "领证",
    "升迁", "升职", "提拔", "晋升", "升正", "升副",
    "考上", "录取", "高考考上", "考研", "得财",
    "怀孕", "生子", "生女", "得子", "得女",
    "上学", "入学",
)

# 凶应事件关键词（不要求 capable）
_XIONG_KEYWORDS: tuple[str, ...] = (
    "去世", "亡", "逝", "死", "病", "灾",
    "离婚", "分手", "破财", "失业", "降职",
    "牢狱", "车祸", "重病",
)


def _is_success_event(candidate_event: str) -> bool:
    cev = candidate_event or ""
    return any(k in cev for k in _SUCCESS_KEYWORDS)


def _is_xiong_event(candidate_event: str) -> bool:
    cev = candidate_event or ""
    return any(k in cev for k in _XIONG_KEYWORDS)


def check_against_energy(
    candidate_event: str,
    domain: str,
    energy: Optional[EnergyFindings],
) -> tuple[bool, list[str]]:
    """检查 candidate_event 是否与 energy 一致。

    判定原则：
        - 凶应事件（去世/破财/失业等）→ 总是一致（不要求 capable）
        - 成立性事件 → 看 wealth_ceiling / caifu / guanming 等是否支持
        - 简化版：仅在明显矛盾时返回 False（如 财运 + 暴富 + wealth_ceiling=贫困）
    """
    if energy is None:
        return True, ["energy=None，跳过 energy 一致性检查"]

    if _is_xiong_event(candidate_event):
        return True, [f"凶应事件 '{candidate_event}'：energy 不构成约束"]

    if not _is_success_event(candidate_event):
        return True, ["非典型成立性事件，跳过 energy 一致性检查"]

    notes: list[str] = []
    wc = energy.wealth_ceiling

    # 财运 / 事业：财库严重不匹配（贫困级 + 升迁=fail）
    if domain in ("财运", "事业"):
        if wc.startswith("贫困级"):
            return False, [
                f"成立性事件 '{candidate_event}' 但 D1 wealth_ceiling={wc} → 不一致"
            ]
        notes.append(f"D1 wealth_ceiling={wc}（足以支撑成立性事件）")

    # 婚姻：D2 marriage_picture 主导（picture_consistent 严校），energy 仅作弱约束
    if domain == "婚姻":
        notes.append("婚姻 domain：能量层不强约束，由 picture 主导")

    return True, notes


def _compute_age_at_year(parsed: ParsedInput, year: int) -> int:
    """从 parsed.birth 提取出生年并计算 age = year - birth_year。

    优先顺序：``birth["公历"]`` (e.g. "1980-01-01") → ``birth["公历年"]`` →
    ``dayun.起运年 - 起运岁`` 推算（兜底）。
    """
    birth_year_str = str((parsed.birth or {}).get("公历", "0"))
    try:
        # birth["公历"] 形如 "1980-01-01"
        birth_year = int(birth_year_str.split("-")[0]) if "-" in birth_year_str \
            else int((parsed.birth or {}).get("公历年") or 0)
    except (ValueError, AttributeError):
        birth_year = int((parsed.birth or {}).get("公历年") or 0)
    if birth_year == 0:
        # 用大运推：起运年 - 起运岁 = 出生年
        birth_year = parsed.dayun.起运年 - int(parsed.dayun.起运岁)
    return year - birth_year


# ============================================================
# 一·五、social_clock_check (CFL-C014-003 v2 学制盲区律强制前置)
# ============================================================
#
# 来源：C-2026-014（李砚儒儿子）连续 2 次校准均犯学制盲区错误：
#   - v1.0 报告判 "2026 丙午=高考"（实际 2024）
#   - v2.0 校准重锚 "2029 己酉=大学毕业"（实际 2028）
# 在 v2.0 § D 仲裁中明确承诺 social_clock_check 强制前置，但
# 实际未落代码 → v2.1 再次发现错误。本函数补上这个工程债务。
#
# 设计原则：
#   1. 仅匹配明确含"成立性事件"关键词的 candidate_event
#   2. 出生年 + 关键词 → 期望年龄窗口 [lo, hi]
#   3. 严格窗口内 → consistent=True
#   4. 容差带（±1 年）→ True 但标 ⚠️ warn-only
#   5. 偏差 > 1 年 → consistent=False，gate_yingqi 钳 passed_layers ≤ 1
#
# 关键词列表按"长关键词优先"排序，避免"毕业"误匹配掉"本科毕业"。

# 事件关键词 → (lo, hi, label) 年龄窗口
_SOCIAL_CLOCK_RULES: list[tuple[tuple[str, ...], tuple[int, int], str]] = [
    # ===== 学业系列（按长度降序避免被泛词吃掉）=====
    (("研究生毕业", "硕士毕业"), (24, 29), "研究生毕业"),
    (("博士毕业", "PhD毕业", "PhD 毕业"), (27, 35), "博士毕业"),
    (("研究生入学", "硕士入学", "读研"), (21, 26), "研究生入学"),
    (("博士入学",), (24, 32), "博士入学"),
    (("本科毕业", "大学毕业"), (21, 24), "本科毕业（4 年制）"),
    (("高考",), (17, 19), "高考"),
    (("考研",), (21, 25), "考研"),
    (("入学", "上学", "录取"), (17, 23), "升学/入学"),
    # ===== 婚姻系列（picture 已有强约束，本函数作为二次保险）=====
    (("初婚", "成家"), (20, 40), "初婚"),
    (("结婚", "成婚", "嫁", "娶", "领证"), (20, 50), "结婚（含再婚）"),
    # ===== 工作系列 =====
    (("入职", "第一份工作", "首份工作"), (21, 28), "首次入职"),
    (("升迁", "升职", "提拔", "晋升"), (25, 65), "升职"),
    (("退休",), (55, 70), "退休"),
    # ===== 生育系列 =====
    (("生子", "生女", "怀孕", "得子", "得女"), (20, 45), "生育"),
]

# 偏差容忍度（单位：年）。命主年龄换算可能因农历/虚岁出现 ±1 年误差。
_SOCIAL_CLOCK_TOLERANCE: int = 1


def check_social_clock(
    candidate_event: str,
    year: int,
    parsed: ParsedInput,
) -> tuple[bool, list[str]]:
    """v1.4 CFL-C014-003 v2：学制盲区律强制前置检查。

    Args:
        candidate_event: 候选事件描述（"结婚" / "高考" / "大学毕业" 等）
        year:            公历年份
        parsed:          ParsedInput（含 birth / dayun）

    Returns:
        (consistent, notes) — consistent=False 时 gate_yingqi 应钳 passed_layers ≤ 1
    """
    if not candidate_event:
        return True, ["candidate_event 为空，跳过 social_clock 检查"]

    # 关键词匹配（按规则列表顺序，长关键词优先）
    matched = None
    for keywords, (lo, hi), label in _SOCIAL_CLOCK_RULES:
        if any(k in candidate_event for k in keywords):
            matched = (lo, hi, label)
            break

    if matched is None:
        return True, [
            f"事件 '{candidate_event}' 非典型成立性事件，跳过 social_clock 检查"
        ]

    lo, hi, label = matched
    age = _compute_age_at_year(parsed, year)

    if age <= 0:
        return True, [
            f"年龄 {age} 不合法（year={year} 早于出生年）→ 跳过 social_clock 检查"
        ]

    # 严格窗口
    if lo <= age <= hi:
        return True, [f"年龄 {age} ∈ {label} 期望窗口 [{lo},{hi}]"]

    # 容差带（±_SOCIAL_CLOCK_TOLERANCE 年）→ warn-only 通过
    if lo - _SOCIAL_CLOCK_TOLERANCE <= age <= hi + _SOCIAL_CLOCK_TOLERANCE:
        return True, [
            f"⚠️ 年龄 {age} 在 {label} 期望窗口 [{lo},{hi}] 边缘 "
            f"(容差 ±{_SOCIAL_CLOCK_TOLERANCE} 年内)，warn-only 通过"
        ]

    # 严重偏差 → 不一致
    return False, [
        f"年龄 {age} ∉ {label} 期望窗口 [{lo},{hi}] "
        f"(容差 ±{_SOCIAL_CLOCK_TOLERANCE} 年也不含) → social_clock_consistent=False, "
        f"passed_layers 应钳到 ≤ 1（CFL-C014-003 学制盲区律 v2）"
    ]


def check_against_picture(
    candidate_event: str,
    domain: str,
    picture: Optional[PictureFindings],
    year: int,
    parsed: ParsedInput,
) -> tuple[bool, list[str]]:
    """检查 candidate_event 是否在 picture 给出的窗口内。

    本函数是修复 G2 的关键。
    - 婚姻：必须落入 marriage_picture['初婚最佳窗口']（含次佳）
    - 学业：落入 education_picture（picture types 中无字段，宽松处理）
    - 事业：rising_windows（不强约束）
    """
    if picture is None:
        return True, ["picture=None，跳过 picture 一致性检查"]

    notes: list[str] = []

    # 计算年龄（沿用 _compute_age_at_year 工具函数）
    age = _compute_age_at_year(parsed, year)

    # ============ 婚姻 ============
    if domain == "婚姻":
        marry_keywords = ("结婚", "成婚", "嫁", "娶", "领证", "成家", "初婚")
        is_marry = any(k in candidate_event for k in marry_keywords)
        if not is_marry:
            return True, [f"事件 '{candidate_event}' 非结婚类，跳过婚姻 picture 检查"]

        mp = picture.marriage_picture
        if not mp or "初婚最佳窗口" not in mp:
            return True, ["picture.marriage_picture 缺失，跳过婚姻 picture 检查"]

        win = mp["初婚最佳窗口"]
        if not (isinstance(win, (tuple, list)) and len(win) == 2):
            return True, [f"marriage_picture['初婚最佳窗口']={win} 格式不识别"]

        lo, hi = int(win[0]), int(win[1])
        # 严格窗口
        if lo <= age <= hi:
            return True, [f"年龄 {age} ∈ 初婚最佳窗口 [{lo},{hi}]"]

        # 次佳窗口（picture types 暂无单独字段，给 ±2 年宽容带）
        secondary_lo, secondary_hi = lo - 2, hi + 2
        if secondary_lo <= age <= secondary_hi:
            return True, [
                f"年龄 {age} ∈ 次佳窗口 [{secondary_lo},{secondary_hi}]（最佳 [{lo},{hi}] ±2）"
            ]

        return False, [
            f"年龄 {age} ∉ 初婚最佳窗口 [{lo},{hi}]"
            f"（次佳 [{secondary_lo},{secondary_hi}] 也不含）"
            f" → picture_consistent=False"
        ]

    # ============ 学业 ============
    if domain == "学业":
        edu_keywords = ("高考", "考上", "上学", "录取", "考研", "毕业")
        is_edu = any(k in candidate_event for k in edu_keywords)
        if not is_edu:
            return True, [f"事件 '{candidate_event}' 非学业类"]
        # picture types 当前无 education_picture.key_year_window 字段
        # → 用普世判定：18 岁前后为高考窗口
        if 16 <= age <= 20:
            return True, [f"年龄 {age} 在普世高考窗口 [16,20]"]
        if 21 <= age <= 30:
            return True, [f"年龄 {age} 在考研/在读窗口 [21,30]"]
        return True, [f"年龄 {age} 偏离普世学业窗口（不强约束）"]

    # ============ 事业 ============
    if domain == "事业":
        # PictureFindings 当前实现无 career_picture.rising_windows
        # （仅 industry_pointers），事业 picture 不强约束
        return True, ["事业 domain：picture 无强约束（参考 industry_pointers）"]

    # ============ 其他 domain ============
    return True, [f"domain={domain} 无 picture 强约束"]


# ============================================================
# 二、应期专用置信度（按 06 § 四）
# ============================================================

# 06 § 4.1 触发类型基础强度
_TRIGGER_BASE_STRENGTH: dict[str, float] = {
    "本字到": 0.65,
    "伏吟": 0.78,
    "合冲引动": 0.62,
    "墓库开闭": 0.60,
    "藏干透出": 0.58,
    "倒象成立": 0.85,
}

# 06 § 4.1 触发类型加成
_TRIGGER_TYPE_BONUS: dict[str, float] = {
    "倒象成立": 0.05,
    "伏吟": 0.03,
}


def _trigger_strength(t: TriggerEvent) -> float:
    """单条触发的基础强度（06 § 4.1）。"""
    return _TRIGGER_BASE_STRENGTH.get(t.type, 0.50)


def _trigger_type_bonus(t: TriggerEvent) -> float:
    """触发类型加成（仅算第一次出现的，避免重复加）。"""
    return _TRIGGER_TYPE_BONUS.get(t.type, 0.0)


def _posterior_to_star(p: float) -> int:
    """06 § 二 五星映射。"""
    if p < 0.40:
        return 1
    if p < 0.55:
        return 2
    if p < 0.70:
        return 3
    if p < 0.85:
        return 4
    return 5


def compute_yingqi_confidence(
    passed_layers: int,
    triggers: list[TriggerEvent],
    primary_trigger: Optional[TriggerEvent],
    l2_via_transition: bool,
    upstream_consistent: bool,
) -> Confidence:
    """应期 Confidence 计算（06 § 四完整公式）。

    返回 Confidence 五元组（star / percent / posterior / variance / sample_n）。
    """
    # 1. gate 上限
    gate_ceiling = PASSED_LAYERS_TO_STAR_CEILING.get(passed_layers, 0)
    if gate_ceiling == 0:
        # passed=0 → 不输出此候选
        return Confidence(
            star=0, percent=0.0, posterior=0.0, variance=1.0, sample_n=0
        )

    # 2. 主触发强度
    n_triggers = len(triggers)
    primary_strength = (
        _trigger_strength(primary_trigger) if primary_trigger
        else 0.50  # 兜底
    )

    # 多触发奖励（最多 +0.10）
    trigger_bonus = min(0.10, max(0, n_triggers - 1) * 0.04)

    # 触发类型加成（每种类型只加一次，避免重复触发的同类型多次加分）
    seen_types: set[str] = set()
    type_bonus = 0.0
    for t in triggers:
        if t.type in seen_types:
            continue
        seen_types.add(t.type)
        type_bonus += _trigger_type_bonus(t)

    posterior = primary_strength + trigger_bonus + type_bonus

    # 3. 过渡期惩罚
    if l2_via_transition:
        posterior -= 0.08
        gate_ceiling = max(1, gate_ceiling - 1)

    # 4. 上游不一致 → 强降级
    if not upstream_consistent:
        posterior -= 0.20
        gate_ceiling = min(gate_ceiling, 2)

    # 5. clamp + 映射 ★
    posterior = max(0.0, min(0.95, posterior))
    star = _posterior_to_star(posterior)
    star = min(star, gate_ceiling)

    # passed=1 时强制 ★ ≤ 3 (PASSED_LAYERS_TO_STAR_CEILING)
    # passed=0 时强制 ★ = 0
    # 已通过 gate_ceiling 限制

    return Confidence(
        star=star,
        percent=round(posterior, 3),
        posterior=round(posterior, 3),
        variance=0.05,  # gate 路径无 variance 概念，固定低值
        sample_n=n_triggers,
    )


# ============================================================
# 三、Evidence 收集
# ============================================================

def _collect_evidence(
    domain: str,
    l1: LayerCheck, l2: LayerCheck, l3: LayerCheck,
    triggers: list[TriggerEvent],
    primary_trigger: Optional[TriggerEvent],
) -> list[Evidence]:
    """从三层 + 触发 + 道门收集 evidence 链。"""
    out: list[Evidence] = []

    # 三层基础 evidence（每层 1 条）
    if l1.passed:
        out.append(Evidence(
            rule_id="MR-LAYER1",
            school="任",
            description=f"L1 原局有 → {l1.rationale[:60]}",
            weight=0.70,
        ))
    if l2.passed:
        ru = "MR-LAYER2-TRANS" if l2.used_transition else "MR-LAYER2"
        out.append(Evidence(
            rule_id=ru,
            school="任",
            description=f"L2 大运到位 → {l2.rationale[:60]}",
            weight=0.65 if l2.used_transition else 0.75,
        ))
    if l3.passed:
        out.append(Evidence(
            rule_id="MR-LAYER3",
            school="任",
            description=f"L3 流年引爆 → {l3.rationale[:60]}",
            weight=0.78,
        ))

    # 主触发
    if primary_trigger is not None:
        rule_map = {
            "本字到": "M3-R-031.1",
            "伏吟": "M3-R-031.2",
            "合冲引动": "M3-R-031.3",
            "墓库开闭": "M3-R-031.4",
            "藏干透出": "M3-R-031.5",
            "倒象成立": "M3-R-031.6",
        }
        out.append(Evidence(
            rule_id=rule_map.get(primary_trigger.type, "M3-R-031"),
            school="任",
            description=(
                f"主触发 [{primary_trigger.type}]: "
                f"{primary_trigger.description[:60]}"
            ),
            weight=_trigger_strength(primary_trigger),
        ))

    # 倒象成立 → 凶应铁律
    daoxiang = next((t for t in triggers if t.type == "倒象成立"), None)
    if daoxiang is not None and daoxiang is not primary_trigger:
        out.append(Evidence(
            rule_id="MR-006",
            school="任",
            description=f"倒象铁律：{daoxiang.description[:60]}",
            weight=0.85,
        ))

    return out


# ============================================================
# 三·五、v1.4 V4：体制内案例的事件类型多解（CFL-C015-003）
# ============================================================

# 体制内路径关键词（与 output_linter._INSTITUTIONAL_KEYWORDS 保持一致核心子集）
_INSTITUTIONAL_HINTS: tuple[str, ...] = (
    "公门", "国企", "体制", "事业单位", "选调", "公务员",
    "党政", "行政", "省厅", "正厅", "副厅", "正处", "副处",
    "厅局", "省部",
)


def _infer_event_type_hypotheses(
    domain: str,
    candidate_event: str,
    picture: PictureFindings,
) -> list[str]:
    """v1.4 V4：根据行业路径推断事件类型候选。

    触发条件（CFL-C015-003 规约）：
        - domain ∈ {"财运", "事业"}
        - picture.industry_pointers 含体制路径关键词
        - 当前 candidate_event 暗示"财源/置业"类（避免对已经是"升迁"的事件重复注入）

    返回：
        - 满足触发条件 → ["职级升迁", "财源/置业"]
        - 否则 → [] （表示采用 candidate_event 单解）

    设计原则：保守注入，仅在强信号下输出多候选；其他案例保持向后兼容。
    """
    if domain not in ("财运", "事业"):
        return []

    pointers = list(picture.industry_pointers or [])
    pointers_str = "".join(pointers)
    if not any(kw in pointers_str for kw in _INSTITUTIONAL_HINTS):
        return []

    # 已经是"升迁/升职"类事件 → 不需要注入（事件类型已明确）
    if any(k in candidate_event for k in ("升迁", "升职", "提拔", "晋升")):
        return []

    # 财星/财源类事件 → 注入双解（职级 / 财源）
    if any(k in candidate_event for k in ("财", "置业", "财源", "财星", "求财")):
        return ["职级升迁", "财源/置业"]

    # 事业域的笼统事件 → 同样注入
    if domain == "事业":
        return ["职级升迁", "财源/置业"]

    return []


# ============================================================
# 四、主入口
# ============================================================

def gate_yingqi(
    year: int,
    candidate_event: str,
    domain: str,
    energy: EnergyFindings,
    picture: PictureFindings,
    parsed: ParsedInput,
) -> GateResult:
    """应期三层门主入口（04 § 二）。

    Args:
        year:           公历年份
        candidate_event: 候选事件描述（"结婚" / "升迁" / "母亲去世" 等）
        domain:         "婚姻" / "事业" / "财运" / "健康" / "学业" / "六亲" / "其他"
        energy:         上游 D1 EnergyFindings
        picture:        上游 D2 PictureFindings
        parsed:         ParsedInput（含 bazi / dayun / birth / shensha）

    Returns:
        GateResult: 含 passed_layers / triggers / door / confidence 等。
    """
    # 0. 推断 sub_domain（六亲细分）
    sub_domain = (
        infer_sub_domain(candidate_event) if domain == "六亲" else None
    )

    # 1. 三层判定
    l1 = layer1_check(domain, parsed, energy, sub_domain=sub_domain)
    l2 = layer2_check(year, domain, energy, parsed, sub_domain=sub_domain)
    l3, triggers, primary_trigger = layer3_check(
        year, domain, energy, picture, parsed, sub_domain=sub_domain
    )

    raw_passed = sum([1 if x.passed else 0 for x in (l1, l2, l3)])

    # 2. 上游一致性
    e_ok, e_notes = check_against_energy(candidate_event, domain, energy)
    p_ok, p_notes = check_against_picture(
        candidate_event, domain, picture, year, parsed
    )
    # v1.4 CFL-C014-003 v2：学制盲区律强制前置（与 picture 同级钳制）
    s_ok, s_notes = check_social_clock(candidate_event, year, parsed)

    consistency_notes: list[str] = []
    consistency_notes.extend([f"[energy] {n}" for n in e_notes])
    consistency_notes.extend([f"[picture] {n}" for n in p_notes])
    consistency_notes.extend([f"[social_clock] {n}" for n in s_notes])

    # 3. picture 不一致 → 强制 passed_layers ≤ 1（修复 G2 关键！）
    final_passed = raw_passed
    if not p_ok:
        final_passed = min(final_passed, 1)
        consistency_notes.insert(
            0,
            f"[硬约束] picture_consistent=False → "
            f"passed_layers 从 {raw_passed} 钳到 {final_passed}",
        )

    # 3·五. v1.4 CFL-C014-003：social_clock 不一致 → 同样钳到 ≤ 1（修复 C-014 学制盲区）
    if not s_ok:
        prev = final_passed
        final_passed = min(final_passed, 1)
        consistency_notes.insert(
            0,
            f"[硬约束] social_clock_consistent=False → "
            f"passed_layers 从 {prev} 钳到 {final_passed} (CFL-C014-003 v2)",
        )

    # energy 不一致 → 钳到 ≤ 2
    if not e_ok:
        final_passed = min(final_passed, 2)
        consistency_notes.insert(
            0,
            f"[硬约束] energy_consistent=False → passed_layers 钳到 ≤ 2",
        )

    # 4. 12 道门
    door = classify_into_12_doors(
        triggers, domain, energy, picture, parsed, year=year
    )

    # 5. 置信度
    upstream_ok = e_ok and p_ok and s_ok
    confidence = compute_yingqi_confidence(
        passed_layers=final_passed,
        triggers=triggers,
        primary_trigger=primary_trigger,
        l2_via_transition=l2.used_transition,
        upstream_consistent=upstream_ok,
    )

    # 6. Evidence
    evidence = _collect_evidence(domain, l1, l2, l3, triggers, primary_trigger)

    # 7. 上游 hash
    e_hash = energy.hash() if energy is not None else ""
    p_hash = picture.hash() if picture is not None else ""

    # 8. 调试信息
    ln = liunian_ganzhi(year)
    debug = {
        "raw_passed_layers": raw_passed,
        "final_passed_layers": final_passed,
        "liunian": str(ln),
        "primary_trigger_type": primary_trigger.type if primary_trigger else None,
        "primary_trigger_strength": (
            _trigger_strength(primary_trigger) if primary_trigger else 0.0
        ),
        "n_triggers": len(triggers),
        "is_xiong": any(t.is_xiong for t in triggers),
        "sub_domain": sub_domain,
        "l2_via_transition": l2.used_transition,
    }

    return GateResult(
        year=year,
        candidate_event=candidate_event,
        domain=domain,
        layer1=l1, layer2=l2, layer3=l3,
        passed_layers=final_passed,
        triggers=triggers,
        primary_trigger=primary_trigger,
        door=door,
        event_type_hypotheses=_infer_event_type_hypotheses(
            domain, candidate_event, picture,
        ),
        confidence=confidence,
        energy_consistent=e_ok,
        picture_consistent=p_ok,
        consistency_notes=consistency_notes,
        evidence=evidence,
        case_id=parsed.case_id,
        upstream_energy_hash=e_hash,
        upstream_picture_hash=p_hash,
        debug_info=debug,
    )


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    from tests.fixtures.cases import load_case
    from engine.energy.evaluator import evaluate_energy
    from engine.picture.matcher import match_picture

    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    energy = evaluate_energy(parsed)
    picture = match_picture(energy, parsed)

    print("\n" + "=" * 78)
    print("           G2 圣杯 · C-2026-001 婚期 2005 vs 2013（v1.2 关键修复）")
    print("=" * 78)
    print(f"  v1.0 报告判婚期 = 2013（差 8 年）")
    print(f"  实际婚年       = 2005（25 岁，feedback.md ground truth）")
    print(f"  picture.marriage_picture['初婚最佳窗口'] = "
          f"{picture.marriage_picture['初婚最佳窗口']}")
    print()

    # 2005 婚姻
    r2005 = gate_yingqi(2005, "结婚", "婚姻", energy, picture, parsed)
    print(f"\n[2005 结婚]")
    print(f"  L1: {'✓' if r2005.layer1.passed else '✗'} | {r2005.layer1.rationale}")
    print(f"  L2: {'✓' if r2005.layer2.passed else '✗'} | {r2005.layer2.rationale[:80]}")
    print(f"  L3: {'✓' if r2005.layer3.passed else '✗'} | {r2005.layer3.rationale[:80]}")
    print(f"  raw_passed = {r2005.debug_info['raw_passed_layers']}, "
          f"final_passed = {r2005.passed_layers}")
    print(f"  triggers ({len(r2005.triggers)}): "
          f"{[t.type for t in r2005.triggers]}")
    print(f"  primary = {r2005.primary_trigger.type if r2005.primary_trigger else None}")
    print(f"  door = {r2005.door}")
    print(f"  energy_ok={r2005.energy_consistent}, picture_ok={r2005.picture_consistent}")
    print(f"  Confidence: ★{r2005.confidence.star} ({r2005.confidence.percent:.0%})")

    # 2013 婚姻
    r2013 = gate_yingqi(2013, "结婚", "婚姻", energy, picture, parsed)
    print(f"\n[2013 结婚（v1.0 错婚期）]")
    print(f"  raw_passed = {r2013.debug_info['raw_passed_layers']}, "
          f"final_passed = {r2013.passed_layers}")
    print(f"  picture_ok = {r2013.picture_consistent}")
    print(f"  consistency_notes: {r2013.consistency_notes[:3]}")
    print(f"  Confidence: ★{r2013.confidence.star} ({r2013.confidence.percent:.0%})")

    print()
    print("=" * 78)
    print(f"G2 圣杯结果: {'PASS ✓' if r2005.passed_layers == 3 and r2005.confidence.star >= 4 and r2013.passed_layers <= 1 else 'FAIL ✗'}")
    print(f"  · 2005: passed=3 / 5 ★ ?  → {r2005.passed_layers}/3 ★{r2005.confidence.star}")
    print(f"  · 2013: passed≤1 / ★≤3 ? → {r2013.passed_layers}/3 ★{r2013.confidence.star}")
    print("=" * 78)

    assert r2005.passed_layers == 3, f"2005 应 3 层全过，实 {r2005.passed_layers}"
    assert r2005.confidence.star >= 4, f"2005 应 ★≥4，实 {r2005.confidence.star}"
    assert r2013.passed_layers <= 1, f"2013 应 ≤1 层，实 {r2013.passed_layers}"
    assert r2013.confidence.star <= 3, f"2013 应 ★≤3，实 {r2013.confidence.star}"

    # 序列化测试
    s = r2005.to_json()
    r_back = GateResult.from_json(s)
    assert r_back.passed_layers == 3
    print(f"\n[OK] gate_yingqi smoke + G2 圣杯 + JSON round-trip")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
