"""T-164 · 盘面地址级证据盘点（婚姻域，只读）。

只回答一个问题：现有事实层里，哪些东西能写出「某宫某神通过冲/合/刑/穿/制/化
作用于某宫某神」这样的地址串；两条婚姻规则消费的信号，各自落在这条线的哪一侧。

**本模块不改任何产品代码、不建盘、不评分、不生成断语。** 它只调用
``engine.api.analyze_facts``（与 ``python -m engine.cli all`` 同一入口）读事实，
并逐条比对 ``engine.cli relations`` 的关系边，确认地址串可回放。

产物（确定性：无运行时间戳，重复运行逐字节一致）：

* ``META/address-level-evidence-audit-v1.json``  机器可读（计数 / 词表 / 信号映射 / 3 例地址串 / 缺口）
* ``META/address-level-evidence-audit-v1.md``    人读报告

口径（任务卡 §2 预注册，本模块不改判据）：

* 分类三态 —— **有地址**：规则消费的字段本身携带盘面地址（``Y.s``…``H.b`` 或 ``e0xx``）；
  **只有聚合**：规则消费的是计数/布尔/字对/强度，底层可能有带地址的事实但产品路径已丢掉；
  **缺失**：所需原语在事实层不存在，或该字段根本不是盘面证据。
* 例子选取 —— 382 例可用盘按「地址可写性覆盖度」（7 项：D.b 有边、D.b 有冲、D.b 有刑/穿、
  D.b 有合、配偶星有克边、有伤官制官候选、有比劫夺财候选）降序，同分按 ``case_id`` 升序，
  取前 3 例。选的是**最能说明地址串写法**的盘，不是随机样本；总体覆盖率另在 §4 报。
* 两次运行一致 —— 不写时间戳、不写绝对路径；输入文件以 sha256 记录。

用法::

    python -m tools.address_level_evidence_audit [--limit N] [--no-cli-check]

退出码：0 通过；2 输入不可读或 schema 不符；3 计数不变量不复现（411/382/342）；
4 地址串与 ``engine.cli relations`` 的关系边对不上；5 产物写入失败。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Sequence

from engine.api.facade import analyze_facts
from engine.decision.models import ChartFactLedger
from engine.energy.tiyong import evaluate_tiyong
from engine.energy.zuogong import evaluate_zuogong
from engine.features.chart_feature_vector import build_chart_feature_vector
from engine.facts.chart_facts import wuxing_relation
from engine.predicates.types import Bazi, GanZhi, ZHI_TO_WUXING, _default_canggan_for

ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = ROOT / "META" / "timing-eval-set-v1.json"
LABELS_PATH = ROOT / "META" / "marriage-quality-labels-v1.json"
JSON_PATH = ROOT / "META" / "address-level-evidence-audit-v1.json"
MD_PATH = ROOT / "META" / "address-level-evidence-audit-v1.md"

SCHEMA = "address-level-evidence-audit/v1"
TASK = "T-164"
SCRIPT = "tools/address_level_evidence_audit.py"

# 计数不变量（任务卡 §2.3 冻结分母）。不复现即视为数据源变更，拒绝覆盖产物。
EXPECTED_CASES = 411
EXPECTED_USABLE = 382
EXPECTED_LABELED = 342

# 分类三态（任务卡硬约束 2：每个婚姻信号必须落到一个桶，不许「大概可以」）。
ADDRESSED = "有地址"
AGGREGATE = "只有聚合"
MISSING = "缺失"

SPOUSE_STAR = {"乾": ("正财", "偏财"), "坤": ("正官", "七杀")}
OFFICIAL = ("正官", "七杀")
PEER = ("比肩", "劫财")
OUTPUT = ("食神", "伤官")
WEALTH = ("正财", "偏财")

DUAN_RULE = "DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1"
YANG_RULE = "YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1"

# 冲/刑/穿 = 婚姻相关「破坏类」边；再加破/合/会 = 广义对偶边。
DAMAGE_KINDS = ("chong", "xing", "chuan")
DUI_OU_KINDS = ("chong", "xing", "chuan", "po", "liuhe", "zhi_anhe", "sanhe", "sanhui", "ganzhi_zihe")

EDGE_LABEL = {
    "chong": "冲", "xing": "刑", "chuan": "穿", "po": "破",
    "liuhe": "六合", "zhi_anhe": "暗合", "sanhe": "三合", "sanhui": "三会",
    "ganzhi_zihe": "自合", "ke": "克", "sheng": "生", "wuhe": "五合", "stem_chong": "天干冲",
}

# 缺口指向的代码位置（本次审计逐行核对过，供中枢复核）。
LOC_CFV = "engine/features/chart_feature_vector.py:133-157（_branch_relations）"
LOC_YANG = "engine/v5/yang_runner.py:39-92（_palace_disruption / signals）"
LOC_DUAN = "engine/v5/duan_runner.py:251-258（_marriage_divorce_or_remarriage）"
LOC_ACTOR = "engine/facts/structure_check.py:475-478（actor = members[0] if kind == 'ke' else None）"
LOC_EDGE_MEMBERS = "engine/facts/types.py:167-174（Edge.members 仅 sheng/ke 有序）"
LOC_BRANCH_EDGES = "engine/facts/relation_graph.py:210-258（_branch_pair_edges）"
LOC_CANGGAN_KE = "engine/facts/structure_check.py:433-448（_derived_canggan_ke）"
LOC_HIDDEN = "engine/facts/types.py:69-74（HiddenStem 只有 char/qi/ten_god）"
LOC_TEN_GOD_AT = "engine/claims/condition_ir/atoms.py:354-357（_ten_god_at 只取 main_ten_god）"
LOC_ZUOGONG_PATH = "engine/energy/types.py:100-107（ZuogongPath.chain: list[str]）"
LOC_STRUCT_STATUS = "engine/facts/structure_check.py:30,332-352（仅子平八格有 met/unmet/needs_judgment）"
LOC_ATOM_RESCUE = "engine/claims/condition_ir/atoms.py:666-690（structure_rescue 只读八格）"

SIGNAL_ORDER = (
    "D1_DAY_BRANCH_DISRUPTED",
    "D2_MIXED_OFFICIAL_KILL",
    "D3_CHONG_AND_XINGHAI",
    "D4_ACTIVE_PATH_COUNT",
    "Y1_SPOUSE_PALACE_DISRUPTED",
    "Y2_SPOUSE_STAR_WEAK",
    "Y3_PEER_COMPETITION",
    "Y4_OUTPUT_SPOUSE_CONFLICT",
    "Y5_FEMALE_MIXED_OFFICIAL",
    "Y6_COMPOUND_PALACE_PAIRS",
    "Y7_INDEPENDENT_SIGNAL_COUNT",
    "Y8_SPOUSE_STAR_BASIS",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ── 单盘行 ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Row:
    case_id: str
    gender_cn: str
    gender: str
    birth_dt: str
    time_basis: str
    pillars: tuple[str, ...]
    day_master: str
    day_branch: str
    labeled: bool
    label: str
    features: dict[str, Any]
    edges: tuple[dict[str, Any], ...]
    chars: dict[str, str]
    gods: dict[str, tuple[str, ...]]
    spouse_star: tuple[dict[str, Any], ...]
    zhiyong: tuple[dict[str, Any], ...]
    duan_paths: tuple[dict[str, Any], ...]
    signals: dict[str, bool]
    structures_count: int
    shensha_count: int
    muku_count: int

    def day_branch_edges(self, kinds: Sequence[str] = DUI_OU_KINDS) -> tuple[dict[str, Any], ...]:
        want = set(kinds)
        return tuple(e for e in self.edges if "D.b" in e["members"] and e["kind"] in want)

    def spouse_addrs(self) -> tuple[str, ...]:
        return tuple(item["addr"] for item in self.spouse_star)


def _edge_dict(e: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": e["id"],
        "kind": e["kind"],
        "members": tuple(e["members"]),
        "chars": tuple(e.get("chars") or ()),
        "group": e.get("group"),
        "completeness": e.get("completeness"),
        "scope": e.get("scope", "natal"),
    }


def _bazi(pillars: Sequence[str]) -> Bazi:
    gz = [GanZhi.parse(p) for p in pillars]
    bazi = Bazi(年柱=gz[0], 月柱=gz[1], 日柱=gz[2], 时柱=gz[3])
    bazi.藏干 = _default_canggan_for(bazi)
    return bazi


def _yang_signals(features: Any, gender: str, day_branch: str) -> dict[str, bool]:
    """逐行复刻 engine/v5/yang_runner.py:39-91（不导入 runner，避免规则注册表副作用）。"""
    chong_pairs = {frozenset(p) for p in features.chong_pairs if day_branch in p}
    xing_hai_pairs = {frozenset(p) for p in features.xing_hai_pairs if day_branch in p}
    palace_pair_count = len(chong_pairs | xing_hai_pairs)
    palace_disrupted = bool(chong_pairs or xing_hai_pairs)

    spouse_count = sum(int(features.ten_god_counts.get(g, 0)) for g in SPOUSE_STAR[gender])
    spouse_present = (
        (features.has_wealth if gender == "乾" else features.has_official) and spouse_count > 0
    )
    peer_competition = sum(int(features.ten_god_counts.get(g, 0)) for g in PEER) >= 3
    output_heavy = sum(int(features.ten_god_counts.get(g, 0)) for g in OUTPUT) >= 4
    spouse_weak = not spouse_present or spouse_count <= 1

    return {
        "Y1_SPOUSE_PALACE_DISRUPTED": palace_disrupted,
        "Y2_SPOUSE_STAR_WEAK": spouse_weak,
        "Y3_PEER_COMPETITION": peer_competition,
        "Y4_OUTPUT_SPOUSE_CONFLICT": output_heavy and spouse_present,
        "Y5_FEMALE_MIXED_OFFICIAL": gender == "坤" and bool(features.mixed_official_kill),
        "Y6_COMPOUND_PALACE_PAIRS": (
            palace_pair_count >= 2 and bool(chong_pairs) and bool(xing_hai_pairs)
        ),
    }


def _duan_signals(features: Any, day_branch: str, active_path_count: int) -> dict[str, bool]:
    """逐行复刻 engine/v5/duan_runner.py:251-258。"""
    day_branch_disrupted = any(
        day_branch in pair for pair in (*features.chong_pairs, *features.xing_hai_pairs)
    )
    return {
        "D1_DAY_BRANCH_DISRUPTED": day_branch_disrupted,
        "D2_MIXED_OFFICIAL_KILL": bool(features.mixed_official_kill),
        "D3_CHONG_AND_XINGHAI": bool(features.chong_pairs) and bool(features.xing_hai_pairs),
        "D4_ACTIVE_PATH_COUNT": active_path_count >= 1,
    }


def analyse_case(case: dict[str, Any], label: Optional[str]) -> Row:
    gender = "乾" if case["gender"] == "男" else "坤"
    facts = analyze_facts(birth_dt=case["birth_dt"], gender=gender)
    chart = facts["chart"]
    edges = tuple(_edge_dict(e) for e in (facts["relations"].get("edges") or ()))
    pillars = tuple(p["ganzhi"] for p in chart["pillars"])
    day_branch = chart["pillars"][2]["branch"]["char"]

    chars: dict[str, str] = {}
    gods: dict[str, list[str]] = {}
    spouse_star: list[dict[str, Any]] = []
    for p in chart["pillars"]:
        stem = p["stem"]
        chars[stem["addr"]] = stem["char"]
        gods.setdefault(stem["ten_god"], []).append(stem["addr"])
        if stem["ten_god"] in SPOUSE_STAR[gender] and stem["addr"] != "D.s":
            spouse_star.append({
                "addr": stem["addr"], "char": stem["char"], "god": stem["ten_god"],
                "layer": "透干", "qi": "",
            })
        branch = p["branch"]
        chars[branch["addr"]] = branch["char"]
        gods.setdefault(branch["main_ten_god"], []).append(branch["addr"])
        if branch["main_ten_god"] in SPOUSE_STAR[gender]:
            spouse_star.append({
                "addr": branch["addr"], "char": branch["char"],
                "god": branch["main_ten_god"], "layer": "本气", "qi": "本气",
            })
        for h in branch["hidden"]:
            chars[f"{branch['addr']}⊕{h['c']}"] = h["c"]
            gods.setdefault(h["g"], []).append(f"{branch['addr']}⊕{h['c']}")
            if h["g"] in SPOUSE_STAR[gender]:
                spouse_star.append({
                    "addr": f"{branch['addr']}⊕{h['c']}", "char": h["c"], "god": h["g"],
                    "layer": f"藏-{h['q']}", "qi": h["q"],
                })
    gods_t = {k: tuple(dict.fromkeys(v)) for k, v in gods.items()}

    zhiyong = tuple(
        {
            "mode": c["mode"],
            "relation_kind": c["relation_kind"],
            "edge_id": c.get("edge_id"),
            "members": tuple(c["members"]),
            "ten_gods": tuple(c["ten_gods"]),
            "tiyong": tuple(c["tiyong"]),
            "actor": c.get("actor"),
        }
        for c in ((facts.get("duan_zuogong") or {}).get("candidates") or ())
    )

    bazi = _bazi(pillars)
    tiyong = evaluate_tiyong(bazi)
    paths = tuple(
        {"type": p.type, "chain": tuple(p.chain), "layer_count": int(p.layer_count)}
        for p in evaluate_zuogong(bazi, tiyong)
    )
    active_paths = sum(1 for p in paths if p["layer_count"] >= 1)

    ledger = ChartFactLedger(
        sex_marker=case["gender"],
        four_pillars={"year": pillars[0], "month": pillars[1], "day": pillars[2], "hour": pillars[3]},
    )
    features = build_chart_feature_vector(ledger)

    signals = {
        **_duan_signals(features, day_branch, active_paths),
        **_yang_signals(features, gender, day_branch),
    }

    return Row(
        case_id=case["case_id"],
        gender_cn=case["gender"],
        gender=gender,
        birth_dt=case["birth_dt"],
        time_basis=case.get("time_basis", ""),
        pillars=pillars,
        day_master=chart["day_master"],
        day_branch=day_branch,
        labeled=label is not None,
        label=label or "",
        features={
            "chong_pairs": tuple(features.chong_pairs),
            "xing_hai_pairs": tuple(features.xing_hai_pairs),
            "he_pairs": tuple(features.he_pairs),
            "ten_god_counts": dict(features.ten_god_counts),
            "has_wealth": bool(features.has_wealth),
            "has_official": bool(features.has_official),
            "has_output": bool(features.has_output),
            "mixed_official_kill": bool(features.mixed_official_kill),
            "branch_conflict_intensity": round(float(features.branch_conflict_intensity), 4),
            "evidence_completeness": features.evidence_completeness,
        },
        edges=edges,
        chars=chars,
        gods=gods_t,
        spouse_star=tuple(spouse_star),
        zhiyong=zhiyong,
        duan_paths=paths,
        signals=signals,
        structures_count=len(facts.get("structures") or ()),
        shensha_count=len((facts.get("shensha") or {}).get("hits") or ()),
        muku_count=len(facts["relations"].get("muku") or ()),
    )


# ── 每个信号的地址重建（分类独立于重建：分类看规则消费什么，重建看今天能写什么）──


def _dui_ou(row: Row, kinds: Sequence[str]) -> list[str]:
    out: list[str] = []
    for e in row.day_branch_edges(kinds):
        for other, ch in zip(e["members"], e["chars"]):
            if other == "D.b":
                continue
            out.append(
                f"D.b={row.day_branch} ←{EDGE_LABEL.get(e['kind'], e['kind'])}— {other}={ch}（edge {e['id']}）"
            )
    return out


def _god_strings(row: Row, wanted: Iterable[str]) -> list[str]:
    out: list[str] = []
    for g in wanted:
        for a in row.gods.get(g, ()):
            out.append(f"{a} {row.chars.get(a, '')} {g}".replace("  ", " "))
    return out


def cov_D1(row: Row) -> list[str]:
    return _dui_ou(row, DAMAGE_KINDS)


def cov_D2(row: Row) -> list[str]:
    have = [g for g in OFFICIAL if row.gods.get(g)]
    return _god_strings(row, have) if len(have) == 2 else []


def cov_D3(row: Row) -> list[str]:
    chong = [e for e in row.edges if e["kind"] == "chong"]
    other = [e for e in row.edges if e["kind"] in ("xing", "chuan")]
    if not chong or not other:
        return []
    return [f"chong {chong[0]['id']}", f"{other[0]['kind']} {other[0]['id']}"]


def cov_D4(row: Row) -> list[str]:
    """active_path_count 的路径只有字；地址不可回填（见缺口 G3）。"""
    return []


def cov_Y1(row: Row) -> list[str]:
    return _dui_ou(row, ("chong", "xing", "chuan"))


def cov_Y2(row: Row) -> list[str]:
    return [
        f"{item['addr']} {item['char']} {item['god']}（{item['layer']}）"
        for item in row.spouse_star
    ]


def cov_Y3(row: Row) -> list[str]:
    addrs = _god_strings(row, PEER)
    return addrs if len(addrs) >= 3 else []


def cov_Y4(row: Row) -> list[str]:
    if not row.gods.get("食神") and not row.gods.get("伤官"):
        return []
    return _god_strings(row, (*OUTPUT, *SPOUSE_STAR[row.gender]))


def cov_Y5(row: Row) -> list[str]:
    return cov_D2(row) if row.gender == "坤" else []


def cov_Y6(row: Row) -> list[str]:
    return cov_D3(row)


def cov_none(row: Row) -> list[str]:
    return []


COVERAGE: dict[str, Callable[[Row], list[str]]] = {
    "D1_DAY_BRANCH_DISRUPTED": cov_D1,
    "D2_MIXED_OFFICIAL_KILL": cov_D2,
    "D3_CHONG_AND_XINGHAI": cov_D3,
    "D4_ACTIVE_PATH_COUNT": cov_D4,
    "Y1_SPOUSE_PALACE_DISRUPTED": cov_Y1,
    "Y2_SPOUSE_STAR_WEAK": cov_Y2,
    "Y3_PEER_COMPETITION": cov_Y3,
    "Y4_OUTPUT_SPOUSE_CONFLICT": cov_Y4,
    "Y5_FEMALE_MIXED_OFFICIAL": cov_Y5,
    "Y6_COMPOUND_PALACE_PAIRS": cov_Y6,
    "Y7_INDEPENDENT_SIGNAL_COUNT": cov_none,
    "Y8_SPOUSE_STAR_BASIS": cov_none,
}


def signal_table() -> list[dict[str, Any]]:
    """任务卡 §2.2 的信号映射表；classification 是审计判断，coverage 由 --limit 实测另算。"""
    return [
        {
            "id": "D1_DAY_BRANCH_DISRUPTED",
            "zh": "日支受扰（冲/刑/害）",
            "rule_id": DUAN_RULE,
            "code_loc": LOC_DUAN,
            "consumes": "features.chong_pairs / features.xing_hai_pairs（字对，无地址、无边 ID）",
            "classification": AGGREGATE,
            "direction": "部分",
            "direction_note": "能写「D.b ↔ X.b 冲/刑/穿」对偶；主客方向不可写（Edge.members 只对 sheng/ke 有序，冲刑穿候选 actor=None）",
            "upstream_object": "relations.edges（chong/xing/chuan，带 id/members/chars）",
            "reconstruct": "D.b 的 chong/xing/chuan 边（cov_D1）",
            "gaps": ["G1", "G2"],
        },
        {
            "id": "D2_MIXED_OFFICIAL_KILL",
            "zh": "官杀混杂（十神计数）",
            "rule_id": DUAN_RULE,
            "code_loc": LOC_DUAN,
            "consumes": "features.mixed_official_kill = bool(ten_god_counts['正官'] and ten_god_counts['七杀'])",
            "classification": AGGREGATE,
            "direction": "否",
            "direction_note": "只能指认官、杀各自的地址；「混杂」是计数事实，没有谁作用于谁",
            "upstream_object": "chart.pillars[].stem.ten_god / branch.main_ten_god / branch.hidden[].ten_god",
            "reconstruct": "正官/七杀逐字地址（藏干为 addr⊕char 复合串，见 G4）",
            "gaps": ["G3", "G4"],
        },
        {
            "id": "D3_CHONG_AND_XINGHAI",
            "zh": "冲与刑害并见（布尔复合）",
            "rule_id": DUAN_RULE,
            "code_loc": LOC_DUAN,
            "consumes": "bool(features.chong_pairs) and bool(features.xing_hai_pairs)",
            "classification": AGGREGATE,
            "direction": "否",
            "direction_note": "两个布尔求交，不落到具体边；同一字对可同时计入冲与刑（如丑未）",
            "upstream_object": "relations.edges（chong ∪ xing/chuan）",
            "reconstruct": "取首条 chong 边与首条 xing/chuan 边作代表（cov_D3）",
            "gaps": ["G1"],
        },
        {
            "id": "D4_ACTIVE_PATH_COUNT",
            "zh": "段派做功路径数（active_path_count）",
            "rule_id": DUAN_RULE,
            "code_loc": "engine/v5/duan_runner.py:58-69,293-296（_duan_structure）",
            "consumes": "len([p for p in evaluate_zuogong(...) if p.layer_count >= 1])",
            "classification": AGGREGATE,
            "direction": "否",
            "direction_note": "ZuogongPath.chain 只有字（['辛','乙']），柱位只出现在 description 中文文本里，不能当证据引用",
            "upstream_object": "engine.energy.types.ZuogongPath（chain: list[str]；description: 自然语言）",
            "reconstruct": "无地址可回填（cov_D4 恒空）；description 里的「时支未」只能人读",
            "gaps": ["G3"],
        },
        {
            "id": "Y1_SPOUSE_PALACE_DISRUPTED",
            "zh": "夫妻宫被冲/刑/害",
            "rule_id": YANG_RULE,
            "code_loc": LOC_YANG,
            "consumes": "features.chong_pairs / features.xing_hai_pairs 中 day_branch 参与的对",
            "classification": AGGREGATE,
            "direction": "部分",
            "direction_note": "与 D1 同源：对偶可写，主客不可写",
            "upstream_object": "relations.edges（chong/xing/chuan）",
            "reconstruct": "D.b 的 chong/xing/chuan 边（cov_Y1）",
            "gaps": ["G1", "G2"],
        },
        {
            "id": "Y2_SPOUSE_STAR_WEAK",
            "zh": "配偶星弱（数量阈值）",
            "rule_id": YANG_RULE,
            "code_loc": LOC_YANG,
            "consumes": "ten_god_counts[正财/偏财 或 正官/七杀] 与 has_wealth/has_official",
            "classification": AGGREGATE,
            "direction": "否",
            "direction_note": "计数把透干、本气、中气、余气同等计数；配偶星位置与受制关系都不进入判定",
            "upstream_object": "chart.pillars[].stem.ten_god / branch.main_ten_god / branch.hidden[].ten_god",
            "reconstruct": "配偶星逐字地址（cov_Y2）；藏干只能写 addr⊕char（G4）",
            "gaps": ["G4"],
        },
        {
            "id": "Y3_PEER_COMPETITION",
            "zh": "比劫竞争（比劫计数 ≥3）",
            "rule_id": YANG_RULE,
            "code_loc": LOC_YANG,
            "consumes": "ten_god_counts[比肩]+ten_god_counts[劫财] >= 3",
            "classification": AGGREGATE,
            "direction": "部分",
            "direction_note": "「比劫夺财」只有走 ke 边（干→干）或 canggan_ke（支→干）才有方向；支→支无克边（G3）",
            "upstream_object": "chart 十神 + relations.edges(ke) + duan_zuogong.candidates(canggan_ke)",
            "reconstruct": "比劫地址 ≥3（cov_Y3）；夺财方向需再查 ke/canggan_ke",
            "gaps": ["G1", "G3"],
        },
        {
            "id": "Y4_OUTPUT_SPOUSE_CONFLICT",
            "zh": "食伤重与配偶星并存",
            "rule_id": YANG_RULE,
            "code_loc": LOC_YANG,
            "consumes": "食伤计数 >= 4 且 spouse_present",
            "classification": AGGREGATE,
            "direction": "部分",
            "direction_note": "「伤官制官」仅当双方都在天干（ke）或支→干（canggan_ke）时可得方向；支上伤官制官不可写",
            "upstream_object": "chart 十神 + relations.edges(ke) + duan_zuogong.candidates",
            "reconstruct": "食伤地址 + 配偶星地址（cov_Y4）；制需另查 actor 非空候选",
            "gaps": ["G1", "G3"],
        },
        {
            "id": "Y5_FEMALE_MIXED_OFFICIAL",
            "zh": "女命官杀混杂",
            "rule_id": YANG_RULE,
            "code_loc": LOC_YANG,
            "consumes": "sex == female and features.mixed_official_kill",
            "classification": AGGREGATE,
            "direction": "否",
            "direction_note": "同 D2，另加性别门槛",
            "upstream_object": "chart 十神",
            "reconstruct": "正官/七杀逐字地址（cov_Y5）",
            "gaps": ["G3", "G4"],
        },
        {
            "id": "Y6_COMPOUND_PALACE_PAIRS",
            "zh": "夫妻宫冲刑复合（≥2 个不同字对）",
            "rule_id": YANG_RULE,
            "code_loc": LOC_YANG,
            "consumes": "palace_pair_count >= 2 and palace_chong and palace_xing_hai",
            "classification": AGGREGATE,
            "direction": "否",
            "direction_note": "字对集合的基数，不指向具体边",
            "upstream_object": "relations.edges（chong/xing/chuan 的 id 集合）",
            "reconstruct": "D.b 上不同边的 id 计数（cov_Y6 = cov_D3）",
            "gaps": ["G1"],
        },
        {
            "id": "Y7_INDEPENDENT_SIGNAL_COUNT",
            "zh": "独立信号数（规则唯一主条件）",
            "rule_id": YANG_RULE,
            "code_loc": LOC_YANG,
            "consumes": "sum(int(v) for v in signals.values())",
            "classification": AGGREGATE,
            "direction": "否",
            "direction_note": "布尔求和；它是「聚合的聚合」，本身不可能带地址",
            "upstream_object": None,
            "reconstruct": "无（cov_none）",
            "gaps": ["G1"],
        },
        {
            "id": "Y8_SPOUSE_STAR_BASIS",
            "zh": "配偶星取用口径（wealth / official）",
            "rule_id": YANG_RULE,
            "code_loc": "engine/v5/yang_runner.py:67-74",
            "consumes": "spouse_star_basis = 'wealth' if male else 'official'",
            "classification": MISSING,
            "direction": "否",
            "direction_note": "不是盘面证据，是性别→配偶星的取用口径；事实层没有「为何取财/取官」的地址级判据（如财透干/官透干、宫星同宫）",
            "upstream_object": None,
            "reconstruct": "无地址；只能按性别字符串回推（cov_none）",
            "gaps": ["G1"],
        },
    ]


# ── 缺口清单（≤5 条，每条指向具体代码位置）────────────────────────────────


def gaps() -> list[dict[str, Any]]:
    return [
        {
            "id": "G1",
            "title": "规则输入侧没接地址层：婚姻信号与关系图是两套独立的关系判定",
            "code_loc": [LOC_CFV, LOC_YANG, LOC_DUAN],
            "evidence": (
                "chart_feature_vector._branch_relations 用 engine/predicates/relations.py 的 "
                "zhi_chong/zhi_xing/zhi_chuan 另判一次，只存 (字,字) 对；yang_runner/duan_runner "
                "只消费这些字对与 counts，从不读 relations.edges。因此边 ID、地址、柱序全部丢失。"
            ),
            "impact": "两条婚姻规则无法引用任何 e0xx 或 Y/M/D/H 地址；地址串只能被新规则重算，不能从规则输入取。",
            "priority": "P0（改造既有规则的前置；新规则可直接读 edges 绕过）",
            "primitive": False,
        },
        {
            "id": "G2",
            "title": "冲/刑/穿/破边无方向，制用候选 actor=None",
            "code_loc": [LOC_ACTOR, LOC_EDGE_MEMBERS],
            "evidence": (
                "build_duan_zuogong_candidates 对制用只给 ke 设 actor，其余 kind 一律 None；"
                "Edge.members 的 from→to 语义只在 sheng/ke 上成立。实测见 actor_none 段。"
            ),
            "impact": "「夫妻宫被穿」与「宫穿星」不可区分；写出的是对偶，不是「谁作用于谁」。",
            "priority": "P0",
            "primitive": True,
        },
        {
            "id": "G3",
            "title": "地支之间不建克边；宫制星只推「支→干」，做功路径只存字",
            "code_loc": [LOC_BRANCH_EDGES, LOC_CANGGAN_KE, LOC_ZUOGONG_PATH],
            "evidence": (
                "_branch_pair_edges 只建冲/合/穿/破/刑/三合/三会/暗合，没有支克支；"
                "_derived_canggan_ke 只产出 (branch, stem) 对；ZuogongPath.chain 是 list[str]。"
            ),
            "impact": "比劫夺财、伤官制官当双方都在地支时无 edge/actor；做功路径无法回地址。",
            "priority": "P1",
            "primitive": True,
        },
        {
            "id": "G4",
            "title": "藏干没有独立地址，宫制星丢了 «via» 字",
            "code_loc": [LOC_HIDDEN, LOC_TEN_GOD_AT, "engine/api/facade.py:99-107（_compact_zuogong 丢掉 notes）"],
            "evidence": (
                "HiddenStem 只有 char/qi/ten_god，地址只能写成 addr⊕char 复合串；"
                "atoms._ten_god_at 对地支只取 main_ten_god；canggan_ke 候选的 notes（「丑藏辛克乙」）"
                "在 Agent 视图被裁掉，下游只知 D.b 克 H.s，不知经哪个藏干。"
            ),
            "impact": "「财藏月支中气被制」不能作为 edge 端点；藏干层的宫星作用只能人读。",
            "priority": "P1",
            "primitive": True,
        },
        {
            "id": "G5",
            "title": "婚姻域没有救应/反制事实，三态里的 countered_resolved 无地址承载",
            "code_loc": [LOC_STRUCT_STATUS, LOC_ATOM_RESCUE],
            "evidence": (
                "事实层的 met/unmet/needs_judgment 只覆盖子平八格（structures_mvp.yaml）；"
                "婚姻域没有 counter-edge、没有 rescue 原语，condition_ir 的 structure_rescue "
                "只读八格且产品零调用。"
            ),
            "impact": "复审要求的「有忌象但得救应」无法作为独立断语带地址输出，只能压成不触发。",
            "priority": "P2",
            "primitive": True,
        },
    ]


# ── 汇总 ────────────────────────────────────────────────────────────────────


def _count(rows: Sequence[Row], pred: Callable[[Row], bool]) -> int:
    return sum(1 for r in rows if pred(r))


def _has_any_day_branch_edge(row: Row) -> bool:
    return bool(row.day_branch_edges())


def _has_damage(row: Row) -> bool:
    return bool(row.day_branch_edges(DAMAGE_KINDS))


def _god_of_addr(row: Row, addr: str) -> str:
    for god, addrs in row.gods.items():
        if addr in addrs:
            return god
    return ""


def _has_directed_spouse_control(row: Row) -> bool:
    """配偶星被「别人」制：排除日主本人（我克财/官是正常取用，不是被制）。"""
    spouse = set(row.spouse_addrs())
    for e in row.edges:
        if e["kind"] == "ke" and e["members"][1] in spouse and _god_of_addr(row, e["members"][0]) != "日主":
            return True
    for c in row.zhiyong:
        if (
            c["actor"] and c["mode"] == "制用" and c["members"][1] in spouse
            and c["ten_gods"][0] != "日主"
        ):
            return True
    return False


def _has_directed_zhiyong(row: Row) -> bool:
    return any(c["actor"] and c["mode"] == "制用" for c in row.zhiyong)


def coverage_block(rows: Sequence[Row]) -> dict[str, Any]:
    n = len(rows)
    kinds = Counter()
    for row in rows:
        kinds.update(e["kind"] for e in row.day_branch_edges())
    signal_true = {sid: _count(rows, lambda r, s=sid: r.signals.get(s, False)) for sid in SIGNAL_ORDER}
    with_addr = {sid: _count(rows, lambda r, s=sid: bool(COVERAGE[s](r))) for sid in SIGNAL_ORDER}
    return {
        "cases": n,
        "day_branch_edge_cases": _count(rows, _has_any_day_branch_edge),
        "day_branch_damage_cases": _count(rows, _has_damage),
        "day_branch_edge_kind_counts": {k: v for k, v in sorted(kinds.items())},
        "spouse_star_cases": _count(rows, lambda r: bool(r.spouse_star)),
        "spouse_star_stem_cases": _count(rows, lambda r: any(i["layer"] == "透干" for i in r.spouse_star)),
        "spouse_star_main_cases": _count(rows, lambda r: any(i["layer"] == "本气" for i in r.spouse_star)),
        "spouse_star_hidden_only_cases": _count(
            rows, lambda r: bool(r.spouse_star) and all(i["layer"].startswith("藏") for i in r.spouse_star)
        ),
        "spouse_star_absent_cases": _count(rows, lambda r: not r.spouse_star),
        "zhiyong_cases": _count(rows, lambda r: bool(r.zhiyong)),
        "zhiyong_day_branch_cases": _count(
            rows, lambda r: any("D.b" in c["members"] for c in r.zhiyong)
        ),
        "zhiyong_directed_cases": _count(rows, _has_directed_zhiyong),
        "spouse_star_controlled_cases": _count(rows, _has_directed_spouse_control),
        "address_rule_input_cases": _count(
            rows, lambda r: _has_any_day_branch_edge(r) and bool(r.spouse_star)
        ),
        "address_rule_damage_cases": _count(
            rows, lambda r: _has_damage(r) and bool(r.spouse_star)
        ),
        "signal_true_cases": signal_true,
        "signal_with_address_cases": with_addr,
        "signal_true_without_address_cases": {
            sid: signal_true[sid] - _count(
                rows, lambda r, s=sid: r.signals.get(s, False) and bool(COVERAGE[s](r))
            )
            for sid in SIGNAL_ORDER
        },
    }


def actor_none_block(rows: Sequence[Row]) -> dict[str, Any]:
    total = 0
    by_mode = Counter()
    all_none = 0
    none_by_mode = Counter()
    zhiyong = 0
    zhiyong_by_kind = Counter()
    zhiyong_none_by_kind = Counter()
    cases_any = 0
    cases_none = 0
    none_on_day_branch = 0
    none_on_spouse = 0
    cases_none_damage = 0
    for row in rows:
        spouse = set(row.spouse_addrs())
        for c in row.zhiyong:
            total += 1
            by_mode[c["mode"]] += 1
            if c["actor"] is None:
                all_none += 1
                none_by_mode[c["mode"]] += 1
            if c["mode"] != "制用":
                continue
            zhiyong += 1
            zhiyong_by_kind[c["relation_kind"]] += 1
            if c["actor"] is not None:
                continue
            zhiyong_none_by_kind[c["relation_kind"]] += 1
            if "D.b" in c["members"]:
                none_on_day_branch += 1
            if spouse & set(c["members"]):
                none_on_spouse += 1
        if any(c["mode"] == "制用" for c in row.zhiyong):
            cases_any += 1
        if any(c["mode"] == "制用" and c["actor"] is None for c in row.zhiyong):
            cases_none += 1
        if any(
            c["mode"] == "制用" and c["actor"] is None
            and c["relation_kind"] in ("chong", "xing", "chuan", "stem_chong")
            for c in row.zhiyong
        ):
            cases_none_damage += 1
    return {
        "cases": len(rows),
        "candidates_total": total,
        "candidates_by_mode": dict(sorted(by_mode.items())),
        "candidates_actor_none_total": all_none,
        "candidates_actor_none_by_mode": dict(sorted(none_by_mode.items())),
        "zhiyong_total": zhiyong,
        "zhiyong_by_relation_kind": dict(sorted(zhiyong_by_kind.items())),
        "zhiyong_actor_none_total": sum(zhiyong_none_by_kind.values()),
        "zhiyong_actor_none_by_relation_kind": dict(sorted(zhiyong_none_by_kind.items())),
        "zhiyong_actor_none_damage_total": sum(
            n for k, n in zhiyong_none_by_kind.items() if k in ("chong", "xing", "chuan", "stem_chong")
        ),
        "cases_with_zhiyong": cases_any,
        "cases_with_zhiyong_actor_none": cases_none,
        "cases_with_zhiyong_actor_none_damage": cases_none_damage,
        "zhiyong_actor_none_on_day_branch": none_on_day_branch,
        "zhiyong_actor_none_on_spouse_star": none_on_spouse,
    }


def branch_ke_block(rows: Sequence[Row]) -> dict[str, Any]:
    """地支克地支在事实层没有边：统计有多少克对、多少盘受影响。"""
    pairs = 0
    cases = 0
    both_kinds = 0
    for row in rows:
        addrs = [a for a in ("Y.b", "M.b", "D.b", "H.b") if a in row.chars]
        hit = 0
        for i, a in enumerate(addrs):
            for b in addrs[i + 1:]:
                rel = wuxing_relation(ZHI_TO_WUXING[row.chars[a]], ZHI_TO_WUXING[row.chars[b]])
                if rel == "克" or rel == "被克":
                    pairs += 1
                    hit += 1
        if hit:
            cases += 1
        if any(e["kind"] == "ke" and all(m.endswith(".b") for m in e["members"]) for e in row.edges):
            both_kinds += 1
    return {
        "cases": len(rows),
        "branch_ke_pairs": pairs,
        "cases_with_branch_ke_pair": cases,
        "branch_ke_edges_in_fact_layer": both_kinds,
    }


def drift_block(rows: Sequence[Row]) -> dict[str, Any]:
    """cfv 的二字字对表 vs relations.edges 的二字边：两套判定是否一致。

    三字齐全的 xing 边（寅巳申 / 丑戌未）在 cfv 里没有对应形态，单列计数，不算漂移。
    """
    diff_chong = 0
    diff_xing = 0
    multi_member = 0
    samples: list[dict[str, Any]] = []
    for row in rows:
        cfv_chong = {frozenset(p) for p in row.features["chong_pairs"]}
        edge_chong = {
            frozenset(e["chars"]) for e in row.edges
            if e["kind"] == "chong" and len(e["chars"]) == 2
        }
        cfv_xing = {frozenset(p) for p in row.features["xing_hai_pairs"]}
        edge_xing = {
            frozenset(e["chars"]) for e in row.edges
            if e["kind"] in ("xing", "chuan") and len(e["chars"]) == 2
        }
        multi_member += sum(1 for e in row.edges if e["kind"] in ("xing", "chong") and len(e["chars"]) > 2)
        if cfv_chong != edge_chong:
            diff_chong += 1
            if len(samples) < 5:
                samples.append({
                    "case_id": row.case_id,
                    "axis": "chong",
                    "only_feature_vector": sorted("".join(sorted(p)) for p in cfv_chong - edge_chong),
                    "only_edges": sorted("".join(sorted(p)) for p in edge_chong - cfv_chong),
                })
        if cfv_xing != edge_xing:
            diff_xing += 1
            if len(samples) < 5:
                samples.append({
                    "case_id": row.case_id,
                    "axis": "xing_hai",
                    "only_feature_vector": sorted("".join(sorted(p)) for p in cfv_xing - edge_xing),
                    "only_edges": sorted("".join(sorted(p)) for p in edge_xing - cfv_xing),
                })
    return {
        "cases": len(rows),
        "chong_pair_mismatch_cases": diff_chong,
        "xing_hai_pair_mismatch_cases": diff_xing,
        "multi_member_group_edges": multi_member,
        "samples": samples,
    }


# ── 3 例地址串 ──────────────────────────────────────────────────────────────


def _score(row: Row) -> int:
    kinds = {e["kind"] for e in row.day_branch_edges()}
    spouse = set(row.spouse_addrs())
    ke_to_spouse = any(e["kind"] == "ke" and e["members"][1] in spouse for e in row.edges)
    shishang_zhi_guan = any(
        c["actor"] and c["mode"] == "制用" and c["ten_gods"][0] in OUTPUT and c["ten_gods"][1] in OFFICIAL
        for c in row.zhiyong
    )
    bijie_duo_cai = any(
        c["actor"] and c["mode"] == "制用" and c["ten_gods"][0] in PEER and c["ten_gods"][1] in WEALTH
        for c in row.zhiyong
    )
    return sum([
        bool(kinds),
        "chong" in kinds,
        bool(kinds & {"xing", "chuan"}),
        "liuhe" in kinds,
        ke_to_spouse,
        shishang_zhi_guan,
        bijie_duo_cai,
    ])


def _addr_label(row: Row, addr: str) -> str:
    """藏干地址本身已含字（M.b⊕辛），不再重复打印。"""
    if "⊕" in addr:
        return addr
    return f"{addr}={row.chars.get(addr, '')}"


def _candidate_string(row: Row, c: dict[str, Any]) -> str:
    a, t = c["members"]
    ag, tg = c["ten_gods"]
    anchor = "→克→" if c["relation_kind"] != "sheng" else "→生→"
    if c["edge_id"]:
        return (
            f"{_addr_label(row, a)} {ag} {anchor} {_addr_label(row, t)} {tg}"
            f"（edge {c['edge_id']}，zuogong {c['mode']}）"
        )
    if c["relation_kind"] == "canggan_ke":
        return (
            f"{_addr_label(row, a)}（藏干）{ag} {anchor} {_addr_label(row, t)} {tg}"
            f"（zuogong 制用 canggan_ke，actor={c['actor']}；藏干字未随候选输出，见 G4）"
        )
    return (
        f"{_addr_label(row, a)} {ag} {anchor} {_addr_label(row, t)} {tg}"
        f"（zuogong {c['mode']} {c['relation_kind']}，推得关系无 edge）"
    )


def _pair_direction(row: Row, a: str, b: str) -> str:
    rel = wuxing_relation(ZHI_TO_WUXING[row.chars[a]], ZHI_TO_WUXING[row.chars[b]])
    if rel == "克":
        return f"{a}={row.chars[a]} 克 {b}={row.chars[b]}"
    return f"{b}={row.chars[b]} 克 {a}={row.chars[a]}"


def example_payload(row: Row) -> dict[str, Any]:
    spouse = set(row.spouse_addrs())
    dui_ou = _dui_ou(row, DUI_OU_KINDS)
    # 「配偶星被制」排除日主本人克财/克官：我克财是正常取财，不是被外力制。
    spouse_controls = [
        c for c in row.zhiyong
        if c["actor"] and c["mode"] == "制用" and c["members"][1] in spouse
        and c["ten_gods"][0] != "日主"
    ]
    patterned = [
        c for c in row.zhiyong
        if c["actor"] and c["mode"] == "制用" and (
            (c["ten_gods"][0] in OUTPUT and c["ten_gods"][1] in OFFICIAL)
            or (c["ten_gods"][0] in PEER and c["ten_gods"][1] in WEALTH)
        )
    ]
    none_on_day = [
        c for c in row.zhiyong
        if c["actor"] is None and "D.b" in c["members"] and c["mode"] == "制用"
    ]
    edge_evidence = [
        {
            "id": e["id"], "kind": e["kind"], "members": list(e["members"]),
            "chars": list(e["chars"]), "group": e["group"], "completeness": e["completeness"],
        }
        for e in row.edges
        if e["id"] in {
            *(e2["id"] for e2 in row.day_branch_edges()),
            *(c["edge_id"] for c in (*spouse_controls, *patterned, *none_on_day) if c["edge_id"]),
        }
    ]
    unexpressible: list[str] = []
    for sid in SIGNAL_ORDER:
        if row.signals.get(sid) and not COVERAGE[sid](row):
            unexpressible.append(f"{sid} 在本例为真，但事实层取不到地址")
    if none_on_day:
        unexpressible.append(f"D.b 的冲/刑/穿制用候选 {len(none_on_day)} 个 actor=None：写不出「谁作用于谁」")
    branch_ke = [
        (a, b) for i, a in enumerate(("Y.b", "M.b", "D.b", "H.b"))
        for b in ("Y.b", "M.b", "D.b", "H.b")[i + 1:]
        if a in row.chars and b in row.chars
        and wuxing_relation(ZHI_TO_WUXING[row.chars[a]], ZHI_TO_WUXING[row.chars[b]]) in ("克", "被克")
    ]
    if branch_ke:
        unexpressible.append(
            "地支克地支无 edge：" + "、".join(_pair_direction(row, a, b) for a, b in branch_ke)
        )
    return {
        "case_id": row.case_id,
        "gender": row.gender,
        "birth_datetime": row.birth_dt,
        "time_basis": row.time_basis,
        "label": row.label or "unknown（不进 342 分母）",
        "pillars": list(row.pillars),
        "day_master": row.day_master,
        "day_branch": row.day_branch,
        "day_branch_address": f"D.b={row.day_branch}（日支 / 夫妻宫）",
        "day_branch_dui_ou": dui_ou,
        "spouse_star_basis": "财（乾）" if row.gender == "乾" else "官杀（坤）",
        "spouse_star": [
            f"{_addr_label(row, i['addr'])} {i['god']}（{i['layer']}）" for i in row.spouse_star
        ],
        "spouse_star_controlled": [_candidate_string(row, c) for c in spouse_controls],
        "directed_control_examples": [_candidate_string(row, c) for c in patterned],
        "zhiyong_actor_none": [
            f"制用 {c['relation_kind']} {list(c['members'])}（{list(c['ten_gods'])}，"
            f"edge {c['edge_id'] or '推得'}，actor=None）"
            for c in none_on_day
        ],
        "unexpressible": unexpressible,
        "edge_evidence": edge_evidence,
        "cli_command": (
            f'python -m engine.cli relations --birth "{row.birth_dt}" --gender {row.gender} --json'
        ),
    }


def cli_edges(row: Row) -> list[tuple[str, str, tuple[str, ...]]]:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    proc = subprocess.run(
        [sys.executable, "-m", "engine.cli", "relations", "--birth", row.birth_dt,
         "--gender", row.gender, "--json"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", env=env, check=True,
    )
    payload = json.loads(proc.stdout)
    return [(e["id"], e["kind"], tuple(e["members"])) for e in payload["edges"]]


def verify_cli(rows: Sequence[Row]) -> dict[str, Any]:
    checked = 0
    mismatches: list[dict[str, Any]] = []
    for row in rows:
        try:
            external = cli_edges(row)
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            return {"checked": False, "reason": f"engine.cli 不可调用：{type(exc).__name__}", "mismatches": []}
        internal = [(e["id"], e["kind"], e["members"]) for e in row.edges]
        checked += 1
        if external != internal:
            mismatches.append({
                "case_id": row.case_id,
                "only_cli": [x for x in external if x not in internal][:5],
                "only_api": [x for x in internal if x not in external][:5],
            })
    return {"checked": True, "cases": checked, "mismatches": mismatches}


# ── 词表 ────────────────────────────────────────────────────────────────────


def address_vocabulary(rows: Sequence[Row]) -> list[dict[str, Any]]:
    probe = rows[0]
    sample_edge = next((e for e in probe.edges if "D.b" in e["members"]), probe.edges[0])
    return [
        {
            "field": "chart.pillars[].stem.addr / branch.addr",
            "path": "chart.pillars[0..3].stem.addr | branch.addr",
            "example": f"{probe.pillars[0][0]}@{'Y.s'} / {probe.pillars[0][1]}@Y.b",
            "address_level": True,
            "coverage": "每盘 8 个（4 干 + 4 支）",
            "note": "唯一物理地址；DY{n}.* 与 LN{year}.* 由 --dayun-index / --liunian 追加",
        },
        {
            "field": "chart.pillars[].palace",
            "path": "chart.pillars[0..3].palace",
            "example": "year / month / day / hour",
            "address_level": True,
            "coverage": "每盘 4 个",
            "note": "英文宫位名，与 Y/M/D/H 一一对应；中文「年/月/日/时」只在文档里",
        },
        {
            "field": "chart.pillars[].stem.ten_god",
            "path": "chart.pillars[i].stem.ten_god",
            "example": f"{probe.pillars[0][0]}@Y.s = 七杀",
            "address_level": True,
            "coverage": f"{len(rows)}/{len(rows)} 盘有 4 个天干十神",
            "note": "日干固定为「日主」",
        },
        {
            "field": "chart.pillars[].branch.main_ten_god",
            "path": "chart.pillars[i].branch.main_ten_god",
            "example": f"{probe.pillars[2][1]}@D.b = 偏印",
            "address_level": True,
            "coverage": f"{len(rows)}/{len(rows)} 盘有 4 个地支本气十神",
            "note": "只取本气；中气/余气见 hidden",
        },
        {
            "field": "chart.pillars[].branch.hidden[]",
            "path": "chart.pillars[i].branch.hidden[j] = {char, qi, ten_god}",
            "example": "D.b 藏 己(本气,偏印)/癸(中气,食神)/辛(余气,比肩)",
            "address_level": False,
            "coverage": "每盘 8–12 个藏干，全部无独立地址",
            "note": "只能写 addr⊕char 复合串；见缺口 G4",
        },
        {
            "field": "relations.edges[]",
            "path": "relations.edges[j] = {id, kind, members, chars, scope, distance, between, group, completeness, attrs}",
            "example": f"{sample_edge['id']} {sample_edge['kind']} {list(sample_edge['members'])}",
            "address_level": True,
            "coverage": f"{len(rows)}/{len(rows)} 盘有边；每盘 {min(len(r.edges) for r in rows)}–{max(len(r.edges) for r in rows)} 条",
            "note": "members 是地址；chars 是字；只有 sheng/ke 的 members 有序（from→to）",
        },
        {
            "field": "relations.pair_index",
            "path": "relations.pair_index['M.b|D.b'] = ['e012', ...]",
            "example": "M.b|D.b → [e012, e013]",
            "address_level": True,
            "coverage": "仅 `engine.cli relations` 返回；analyze_facts / `all` 裁掉",
            "note": "地址对 → 边 ID 的索引，可直接拿地址查边",
        },
        {
            "field": "relations.muku[]",
            "path": "relations.muku[j] = {addr, branch, ku_of, candidates[], openers[], chuan_po[], binders[]}",
            "example": f"D.b=丑 的 openers={['e015', 'e016']}",
            "address_level": True,
            "coverage": f"{sum(1 for r in rows if r.muku_count)}/{len(rows)} 盘有墓库事实",
            "note": "开闭只给边 ID，不给开/闭结论；候选里的 damaged_by_edges 同样是地址级",
        },
        {
            "field": "duan_zuogong.candidates[].actor / members（structure_check 制用候选）",
            "path": "duan_zuogong.candidates[k] = {mode, relation_kind, edge_id, members, ten_gods, actor}",
            "example": "制用 canggan_ke members=['D.b','H.s'] actor='D.b'",
            "address_level": True,
            "coverage": f"{sum(1 for r in rows if r.zhiyong)}/{len(rows)} 盘有候选；actor 只在 ke/sheng/canggan_ke/muku 上非空",
            "note": "冲/刑/穿/破/合用候选 actor=None（缺口 G2）",
        },
        {
            "field": "duan_zuogong.tiyong",
            "path": "duan_zuogong.tiyong = {addr: 体|用|双属}",
            "example": "{'D.s': '体', 'D.b': '体', 'M.s': '双属'}",
            "address_level": True,
            "coverage": f"{len(rows)}/{len(rows)} 盘 8 个地址",
            "note": "体用分类是地址属性，不是结论",
        },
        {
            "field": "structures[].items[].evidence",
            "path": "structures[i].items[j].evidence = ['e001', 'D.b', ...]",
            "example": "breaker met evidence=['e001']",
            "address_level": True,
            "coverage": f"{sum(1 for r in rows if r.structures_count)}/{len(rows)} 盘有命中项",
            "note": "只覆盖子平八格；婚姻域没有对应结构（缺口 G5）",
        },
        {
            "field": "strength.day_master.roots[]",
            "path": "strength.day_master.roots[j] = {addr, hidden_char, qi, changsheng, distance}",
            "example": "roots[0] addr=D.b hidden_char=辛 qi=余气",
            "address_level": True,
            "coverage": "每盘若干通根项",
            "note": "藏干用 addr + hidden_char 两个字段拼，不是独立地址",
        },
        {
            "field": "shensha.hits[]",
            "path": "shensha.hits[j] = {name, anchor_addr, target_addr, source_ref}",
            "example": "桃花 anchor_addr=Y.b target_addr=M.b",
            "address_level": True,
            "coverage": f"{sum(1 for r in rows if r.shensha_count)}/{len(rows)} 盘有命中",
            "note": "明确区分锚点与目标，是现成的关系型地址词汇，但婚姻两规则不读",
        },
        {
            "field": "chart.kongwang.hits[]",
            "path": "chart.kongwang.hits[j] = [addr, 'day'|'year']",
            "example": "['D.b', 'day']",
            "address_level": True,
            "coverage": "每盘 0–8 项",
            "note": "空亡按旬取，地址级；婚姻规则不读",
        },
        {
            "field": "condition_ir.atoms.SIGNATURES",
            "path": "engine/claims/condition_ir/atoms.py:1124-1171（46 原子地址签名）",
            "example": "chong_at: 必需 ('at',)；he_at: ('at',) + ('with_god','exclude_god')",
            "address_level": True,
            "coverage": "46/46 原子有地址签名；engine/ 内产品零调用",
            "note": "现成的地址级谓词层，未接任何产品规则（本卡不改、不启用）",
        },
    ]


# ── 汇装 ────────────────────────────────────────────────────────────────────


def load_population() -> tuple[list[dict[str, Any]], dict[str, str]]:
    eval_set = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
    labels = json.loads(LABELS_PATH.read_text(encoding="utf-8"))
    label_by_id = {
        c["case_id"]: c["label"] for c in labels["cases"]
        if c.get("usable_for_timing") and c.get("label") in ("negative", "positive")
    }
    cases = eval_set["cases"]
    if len(cases) != EXPECTED_CASES:
        raise SystemExit(f"案例数 {len(cases)} ≠ {EXPECTED_CASES}（数据源已变，拒绝覆盖产物）")
    usable = [c for c in cases if c["usable_for_timing"]]
    if len(usable) != EXPECTED_USABLE:
        raise SystemExit(f"可用盘 {len(usable)} ≠ {EXPECTED_USABLE}")
    if len(label_by_id) != EXPECTED_LABELED:
        raise SystemExit(f"标签盘 {len(label_by_id)} ≠ {EXPECTED_LABELED}")
    return usable, label_by_id


def build_payload(limit: int = 0, check_cli: bool = True) -> dict[str, Any]:
    usable, label_by_id = load_population()
    if limit:
        usable = usable[:limit]
    rows = tuple(analyse_case(case, label_by_id.get(case["case_id"])) for case in usable)
    labeled = tuple(r for r in rows if r.labeled)

    scored = sorted(rows, key=lambda r: (-_score(r), r.case_id))
    examples = [example_payload(r) for r in scored[:3]]
    cli_result = verify_cli([r for r in rows if r.case_id in {e["case_id"] for e in examples}]) if check_cli else {
        "checked": False, "reason": "--no-cli-check", "mismatches": [],
    }
    by_id = {e["case_id"]: e for e in examples}
    for case_id in by_id:
        by_id[case_id]["cli_check"] = {
            "checked": bool(cli_result.get("checked")),
            "mismatches": [
                m for m in cli_result.get("mismatches", []) if m["case_id"] == case_id
            ],
        }

    signal_rows = signal_table()
    cov_all = coverage_block(rows)
    cov_labeled = coverage_block(labeled)
    rule_level = {"Y7_INDEPENDENT_SIGNAL_COUNT", "Y8_SPOUSE_STAR_BASIS"}
    for item in signal_rows:
        sid = item["id"]
        item["coverage"] = {
            "cases": len(rows),
            "signal_true": None if sid in rule_level else cov_all["signal_true_cases"][sid],
            "address_reconstructable": cov_all["signal_with_address_cases"][sid],
            "signal_true_without_address": (
                None if sid in rule_level else cov_all["signal_true_without_address_cases"][sid]
            ),
            "labeled_342": {
                "cases": len(labeled),
                "signal_true": None if sid in rule_level else cov_labeled["signal_true_cases"][sid],
                "address_reconstructable": cov_labeled["signal_with_address_cases"][sid],
                "signal_true_without_address": (
                    None if sid in rule_level
                    else cov_labeled["signal_true_without_address_cases"][sid]
                ),
            },
        }

    classification = Counter(item["classification"] for item in signal_rows)
    actor_none = actor_none_block(rows)
    payload = {
        "schema": SCHEMA,
        "task": TASK,
        "script": SCRIPT,
        "inputs": {
            "timing_eval_set": {"path": "META/timing-eval-set-v1.json", "sha256": _sha256(EVAL_PATH)},
            "marriage_quality_labels": {"path": "META/marriage-quality-labels-v1.json", "sha256": _sha256(LABELS_PATH)},
        },
        "method": {
            "address_level_rule": (
                "有地址=规则消费的字段本身就是 addr 或 edge id；只有聚合=消费计数/布尔/字对/强度，"
                "底层虽有地址但产品路径已丢弃；缺失=所需原语不存在或该字段不是盘面证据。"
            ),
            "signal_replication": (
                "信号真值按 engine/v5/yang_runner.py:39-91 与 duan_runner.py:251-258 逐行复刻；"
                "未导入 runner，避免规则注册表副作用。特征向量用 build_chart_feature_vector 原样构建。"
            ),
            "example_selection": (
                "382 例按 7 项地址可写性覆盖度降序、同分按 case_id 升序取前 3；"
                "是最大可写性样本，不是随机样本，总体覆盖率见 coverage。"
            ),
            "read_only": True,
        },
        "population": {
            "cases_total": EXPECTED_CASES,
            "usable_for_timing": len(rows),
            "labeled_negative_positive": len(labeled),
            "gender": dict(sorted(Counter(r.gender for r in rows).items())),
            "time_basis": dict(sorted(Counter(r.time_basis for r in rows).items())),
            "note": "342 = usable 382 中 negative(186)+positive(156)；unknown 40 不进分母（T-153 口径）",
        },
        "classification_counts": {
            "有地址": classification.get(ADDRESSED, 0),
            "只有聚合": classification.get(AGGREGATE, 0),
            "缺失": classification.get(MISSING, 0),
            "total_signals": len(signal_rows),
        },
        "address_vocabulary": address_vocabulary(rows),
        "signal_map": signal_rows,
        "coverage": {
            "usable_382": cov_all,
            "labeled_342": cov_labeled,
            "branch_ke": branch_ke_block(rows),
            "drift": drift_block(rows),
        },
        "actor_none": actor_none,
        "examples": examples,
        "cli_parity": cli_result,
        "gaps": gaps(),
        "primitive_check": primitive_check(),
        "verdict": verdict_block(cov_all, actor_none),
    }
    return payload


def primitive_check() -> list[dict[str, Any]]:
    """任务卡 §2.3 点名的三类候选原语，逐条核：已有 / 半有 / 不在本卡。"""
    return [
        {
            "name": "十神在支上的地址",
            "status": "已有",
            "where": "chart.pillars[].branch.main_ten_god（+ hidden[].ten_god）",
            "note": "本气十神可直引到 Y.b…H.b；中气/余气只能写 addr⊕char（G4），但地址本身存在。",
        },
        {
            "name": "墓库开闭",
            "status": "半有",
            "where": "relations.muku[].openers / binders / chuan_po / candidates[].damaged_by_edges",
            "note": "开闭相关的边 ID 有，开/闭结论没有（relation_graph 刻意不判）；「库被冲开」只能写边，不能写结论。",
        },
        {
            "name": "大运 / 流年引动",
            "status": "不在本卡",
            "where": "engine.cli --dayun-index / --liunian → DY{n}.s/b、LN{year}.s/b",
            "note": "地址形态已存在（scope=dayun/liunian 的边），但应期建模归 T-165，本卡不深挖。",
        },
    ]


def verdict_block(cov: dict[str, Any], actor_none: dict[str, Any]) -> dict[str, Any]:
    n = cov["cases"]
    return {
        "answer": "不够",
        "scope": (
            "针对「某宫某神通过冲/合/刑/穿/制/化作用于某宫某神 + 救应三态」的完整语义："
            f"12 个婚姻信号里 0 个有地址、11 个只有聚合、1 个缺失；规则输入侧拿不到任何 e0xx 或 Y/M/D/H。"
        ),
        "writable_today": {
            "scope": "只读 relations.edges + chart 十神 + duan_zuogong.actor，可写「D.b 对偶边 + 配偶星地址 + 干/支→干制化」两态规则",
            "cases_with_day_branch_edge_and_spouse_star": cov["address_rule_input_cases"],
            "cases_with_day_branch_damage_and_spouse_star": cov["address_rule_damage_cases"],
            "of": n,
            "cases_with_directed_spouse_control": cov["spouse_star_controlled_cases"],
            "directed_spouse_control_note": "只算「日主以外」的神克配偶星；日主克财/官是正常取用，已排除",
            "blocked_sentences": [
                "地支之间的克（比劫夺财 / 伤官制官双方都在支上）——无 edge（G3）",
                "冲/刑/穿的主客方向——actor=None（G2）",
                "有忌象得救应（countered_resolved）——无救应原语（G5）",
            ],
        },
        "primitives_needed": [
            {"priority": "P0", "gap": "G2", "name": "冲/刑/穿/破边方向绑定（actor/target）",
             "why": f"{actor_none['zhiyong_actor_none_total']}/{actor_none['zhiyong_total']} 个制用候选 actor=None"},
            {"priority": "P0", "gap": "G5", "name": "婚姻域救应/反制事实（counter-edge / rescue）",
             "why": "三态输出里 countered_resolved 目前无地址承载"},
            {"priority": "P1", "gap": "G3", "name": "地支克边 + 藏干地址（G4 一并）",
             "why": "支上制/夺与藏干端点当前不可写"},
        ],
        "wiring_prerequisite": {
            "gap": "G1",
            "note": "既有两条规则要变地址级，必须先在 cfv 输入侧接 relations.edges；新规则可直接读 edges 绕过。",
        },
    }


# ── Markdown ────────────────────────────────────────────────────────────────


def _md_cell(value: Any) -> str:
    if isinstance(value, dict):
        value = " / ".join(f"{k} {v}" for k, v in value.items())
    text = str(value).replace("|", "\\|").replace("\n", "<br>")
    return text


def _md_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    out = ["| " + " | ".join(_md_cell(h) for h in headers) + " |", "|" + "---|" * len(headers)]
    for row in rows:
        out.append("| " + " | ".join(_md_cell(c) for c in row) + " |")
    return "\n".join(out)


def render_markdown(payload: dict[str, Any]) -> str:
    cov = payload["coverage"]["usable_382"]
    cov_l = payload["coverage"]["labeled_342"]
    cls = payload["classification_counts"]
    lines: list[str] = []
    add = lines.append

    add("# T-164 · 盘面地址级证据盘点（婚姻域，只读）")
    add("")
    add("> 产物：`META/address-level-evidence-audit-v1.json` / `.md`；工具：`tools/address_level_evidence_audit.py`。")
    add("> 本卡只盘点，不改 `engine/**`、规则 YAML、`condition_ir`、既有测试；不建盘、不评分。")
    add("")
    add("## 0. 一句话")
    add("")
    add(
        f"**{payload['verdict']['answer']}**——{payload['verdict']['scope']}"
    )
    add("")
    add("## 1. 数据与口径")
    add("")
    pop = payload["population"]
    add(_md_table(
        ["项", "值"],
        [
            ["候选案例", pop["cases_total"]],
            ["可用盘（usable_for_timing）", pop["usable_for_timing"]],
            ["婚姻质量标签盘（negative+positive）", pop["labeled_negative_positive"]],
            ["性别", pop["gender"]],
            ["时间基准", pop["time_basis"]],
        ],
    ))
    add("")
    add(
        "口径：`engine.cli` 把 `birth_dt` 当已校正的本地时间，引擎不做真太阳时换算；"
        f"`time_basis=true_solar` 的 {pop['time_basis'].get('true_solar', 0)} 例按记录原值喂入，"
        f"`clock_beijing` 的 {pop['time_basis'].get('clock_beijing', 0)} 例按钟表时间喂入，"
        "两者都不再二次校正。地址串只在这一口径下成立。"
    )
    add("")
    add("## 2. 分类结果（每条婚姻信号必须落一个桶）")
    add("")
    add(f"- **有地址**：{cls['有地址']} 条")
    add(f"- **只有聚合**：{cls['只有聚合']} 条")
    add(f"- **缺失**：{cls['缺失']} 条")
    add("")
    add(_md_table(
        ["信号", "规则", "分类", "方向", "规则消费的字段", "地址重建", "缺口"],
        [
            [
                f"`{s['id']}`\n{s['zh']}",
                s["rule_id"],
                f"**{s['classification']}**",
                s["direction"],
                s["consumes"],
                f"{s['coverage']['address_reconstructable']}/{s['coverage']['cases']} 例可写\n"
                f"（真值 {s['coverage']['signal_true'] if s['coverage']['signal_true'] is not None else '—（规则级字段）'} 例，"
                f"真值但无地址 {s['coverage']['signal_true_without_address'] if s['coverage']['signal_true_without_address'] is not None else '—'} 例）",
                ",".join(s["gaps"]),
            ]
            for s in payload["signal_map"]
        ],
    ))
    add("")
    add(
        "「可写」= 用现成事实层能把该信号写成至少一条地址串的盘数（不要求信号为真）；"
        "「真值」= 按产品代码复刻的信号真值为真的盘数；「真值但无地址」= 信号真、却拼不出地址串的盘。"
    )
    add("")
    add("## 3. 地址词汇表（当前 API 可直接引用的字段）")
    add("")
    add(_md_table(
        ["字段", "地址级", "示例", "覆盖", "说明"],
        [
            [f"`{v['field']}`", "是" if v["address_level"] else "**否**", v["example"], v["coverage"], v["note"]]
            for v in payload["address_vocabulary"]
        ],
    ))
    add("")
    add("## 4. 三例真实盘地址串")
    add("")
    for ex in payload["examples"]:
        add(f"### {ex['case_id']} · {ex['gender']} · {ex['birth_datetime']}（{ex['time_basis']}；标签 {ex['label']}）")
        add("")
        add(f"- 四柱：`{' '.join(ex['pillars'])}`；日主 {ex['day_master']}；{ex['day_branch_address']}")
        add(f"- 复现：`{ex['cli_command']}`")
        add("")
        add("**日支（夫妻宫）的对偶边**")
        add("")
        for s in ex["day_branch_dui_ou"] or ["（本例 D.b 无关系边）"]:
            add(f"- `{s}`")
        add("")
        add(f"**配偶星地址**（{ex['spouse_star_basis']}）")
        add("")
        for s in ex["spouse_star"] or ["（本例取不到配偶星地址）"]:
            add(f"- `{s}`")
        add("")
        add("**配偶星被制**")
        add("")
        for s in ex["spouse_star_controlled"] or ["（本例无 actor 非空的制用候选指向配偶星）"]:
            add(f"- `{s}`")
        add("")
        add("**伤官制官 / 比劫夺财**")
        add("")
        for s in ex["directed_control_examples"] or ["（本例无对应候选）"]:
            add(f"- `{s}`")
        add("")
        add("**写不出来的（本例）**")
        add("")
        for s in ex["unexpressible"] or ["（无）"]:
            add(f"- {s}")
        add("")
        add("**回 `engine.cli` 对边**")
        add("")
        add(_md_table(
            ["edge", "kind", "members", "chars", "group/completeness"],
            [
                [e["id"], e["kind"], ",".join(e["members"]), "".join(e["chars"]),
                 f"{e['group'] or '-'} / {e['completeness'] or '-'}"]
                for e in ex["edge_evidence"]
            ],
        ))
        check = ex.get("cli_check") or {}
        add("")
        add(f"`engine.cli relations` 逐项比对：checked={check.get('checked')}，mismatches={len(check.get('mismatches') or [])}")
        add("")
    add("## 5. 量化缺口")
    add("")
    add("### 5.1 每盘可取得的地址级证据")
    add("")
    add(_md_table(
        ["指标", "382 例", "342 例"],
        [
            ["D.b 至少一条关系边", cov["day_branch_edge_cases"], cov_l["day_branch_edge_cases"]],
            ["D.b 有冲/刑/穿", cov["day_branch_damage_cases"], cov_l["day_branch_damage_cases"]],
            ["取得到配偶星地址", cov["spouse_star_cases"], cov_l["spouse_star_cases"]],
            ["配偶星透干", cov["spouse_star_stem_cases"], cov_l["spouse_star_stem_cases"]],
            ["配偶星仅藏支（无透干无本气）", cov["spouse_star_hidden_only_cases"], cov_l["spouse_star_hidden_only_cases"]],
            ["取不到任何配偶星地址", cov["spouse_star_absent_cases"], cov_l["spouse_star_absent_cases"]],
            ["有段派做功候选", cov["zhiyong_cases"], cov_l["zhiyong_cases"]],
            ["有 actor 非空的制用候选", cov["zhiyong_directed_cases"], cov_l["zhiyong_directed_cases"]],
            ["有「日主以外克配偶星」的地址", cov["spouse_star_controlled_cases"], cov_l["spouse_star_controlled_cases"]],
            ["D.b 有边且取得到配偶星地址", cov["address_rule_input_cases"], cov_l["address_rule_input_cases"]],
            ["D.b 有冲/刑/穿且取得到配偶星地址（限定版最窄口径）", cov["address_rule_damage_cases"], cov_l["address_rule_damage_cases"]],
        ],
    ))
    add("")
    add(
        "比劫口径注意：`chart_feature_vector._ten_god_features` 对全部天干调 `get_shishen`，"
        f"日干因此被计成「比肩」；Y3（比劫≥3）真值 {cov['signal_true_cases']['Y3_PEER_COMPETITION']} 例，"
        f"但能写出 ≥3 个比劫地址的只有 {cov['signal_with_address_cases']['Y3_PEER_COMPETITION']} 例，"
        f"差 {cov['signal_true_without_address_cases']['Y3_PEER_COMPETITION']} 例正是「日干凑数」造成的聚合/地址分歧。"
    )
    add("")
    add("### 5.2 制用候选的 actor=None")
    add("")
    an = payload["actor_none"]
    add(_md_table(
        ["项", "值"],
        [
            ["候选总数（全 mode）", an["candidates_total"]],
            ["按 mode", an["candidates_by_mode"]],
            ["制用候选总数", an["zhiyong_total"]],
            ["制用候选 actor=None", an["zhiyong_actor_none_total"]],
            ["其中冲/刑/穿/天干冲", an["zhiyong_actor_none_damage_total"]],
            ["按 relation_kind", an["zhiyong_actor_none_by_relation_kind"]],
            ["落在 D.b 上", an["zhiyong_actor_none_on_day_branch"]],
            ["落在配偶星地址上", an["zhiyong_actor_none_on_spouse_star"]],
            ["有制用候选的盘", an["cases_with_zhiyong"]],
            ["有 actor=None 制用候选的盘", an["cases_with_zhiyong_actor_none"]],
            ["有 actor=None 冲/刑/穿制用候选的盘", an["cases_with_zhiyong_actor_none_damage"]],
        ],
    ))
    add("")
    add(
        "T-149 记录的 301/56 出自它的临时探针（36 期 / 1578 对）口径；本卡按 382 例应期集重算，"
        "分母不同，结论同向：**凡是冲/刑/穿，actor 一律为空**（代码只对 `ke` 设 actor）。"
    )
    add("")
    add("### 5.3 地支克地支：事实层没有边")
    add("")
    bk = payload["coverage"]["branch_ke"]
    add(_md_table(
        ["项", "值"],
        [
            ["地支五克对（原局）总数", bk["branch_ke_pairs"]],
            ["受影响盘数", f"{bk['cases_with_branch_ke_pair']}/{bk['cases']}"],
            ["事实层「支→支克」边数", bk["branch_ke_edges_in_fact_layer"]],
        ],
    ))
    add("")
    add("### 5.4 两套关系判定的字对一致性（cfv 字对 vs relations.edges 二字边）")
    add("")
    dr = payload["coverage"]["drift"]
    add(_md_table(
        ["轴", "不一致盘数"],
        [["冲", dr["chong_pair_mismatch_cases"]], ["刑/穿", dr["xing_hai_pair_mismatch_cases"]]],
    ))
    add("")
    add(
        f"三字齐全的刑边（寅巳申 / 丑戌未，cfv 不建三字组）共 {dr['multi_member_group_edges']} 条，"
        "单列、不算漂移。字对层面 0 差异说明：问题不在两套表算得不一样，而在规则只拿了字对、丢了地址。"
    )
    add("")
    add("### 5.5 候选原语核查（任务卡 §2.3 点名的三类）")
    add("")
    add(_md_table(
        ["原语", "状态", "在哪", "说明"],
        [[p["name"], p["status"], f"`{p['where']}`", p["note"]] for p in payload["primitive_check"]],
    ))
    add("")
    add("## 6. 缺口清单（≤5 条）")
    add("")
    add(_md_table(
        ["ID", "缺口", "代码位置", "优先级", "是否缺原语"],
        [
            [g["id"], g["title"], "<br>".join(f"`{c}`" for c in g["code_loc"]), g["priority"],
             "是" if g["primitive"] else "接线"]
            for g in payload["gaps"]
        ],
    ))
    add("")
    add("## 7. 结论")
    add("")
    add(f"**{payload['verdict']['answer']}**：{payload['verdict']['scope']}")
    add("")
    vt = payload["verdict"]["writable_today"]
    add(f"今天就能写的**限定版**：{vt['scope']}。"
        f"可写盘数 {vt['cases_with_day_branch_edge_and_spouse_star']}/{vt['of']}；"
        f"收窄到「D.b 有冲/刑/穿」为 {vt['cases_with_day_branch_damage_and_spouse_star']}/{vt['of']}。"
        f"其中能被「日主以外的神」克的配偶星：{vt['cases_with_directed_spouse_control']} 例"
        f"（{vt['directed_spouse_control_note']}）。")
    add("")
    add("仍写不出来的句子：")
    for s in vt["blocked_sentences"]:
        add(f"- {s}")
    add("")
    add("要补的原语（按优先级）：")
    for p in payload["verdict"]["primitives_needed"]:
        add(f"- **{p['priority']}** {p['gap']} {p['name']}——{p['why']}")
    add("")
    add(f"接线前置：{payload['verdict']['wiring_prerequisite']['note']}")
    add("")
    add("## 8. 复现")
    add("")
    add("```bash")
    add(".venv\\Scripts\\python.exe -m tools.address_level_evidence_audit")
    add(".venv\\Scripts\\python.exe -m pytest -q")
    add("```")
    add("")
    add("产物不含运行时间戳，两次运行逐字节一致；输入以 sha256 记录。")
    add("")
    return "\n".join(lines)


# ── 入口 ────────────────────────────────────────────────────────────────────


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="T-164 盘面地址级证据盘点（只读）")
    parser.add_argument("--limit", type=int, default=0, help="只跑前 N 例（调试用；产物随之缩小）")
    parser.add_argument("--no-cli-check", action="store_true", help="跳过 engine.cli 关系边回放")
    parser.add_argument("--check", action="store_true", help="只校验产物可生成，不落盘")
    args = parser.parse_args(argv)

    try:
        payload = build_payload(limit=args.limit, check_cli=not args.no_cli_check)
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 3
    except (OSError, json.JSONDecodeError) as exc:
        print(f"输入不可读：{exc}", file=sys.stderr)
        return 2

    body = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    report = render_markdown(payload)

    if not args.check:
        try:
            _write(JSON_PATH, body)
            _write(MD_PATH, report)
        except OSError as exc:
            print(f"产物写入失败：{exc}", file=sys.stderr)
            return 5

    mismatches = payload["cli_parity"].get("mismatches") or []
    cls = payload["classification_counts"]
    cov = payload["coverage"]["usable_382"]
    print(
        f"案件 {payload['population']['usable_for_timing']}（标签 {payload['population']['labeled_negative_positive']}）"
        f"；分类 有地址 {cls['有地址']} / 只有聚合 {cls['只有聚合']} / 缺失 {cls['缺失']}"
    )
    print(
        f"D.b 有边 {cov['day_branch_edge_cases']}；配偶星地址 {cov['spouse_star_cases']}；"
        f"限定版可写 {cov['address_rule_input_cases']}；actor=None "
        f"{payload['actor_none']['zhiyong_actor_none_total']}/{payload['actor_none']['zhiyong_total']}"
    )
    if payload["cli_parity"].get("checked"):
        print(f"engine.cli 关系边回放：{payload['cli_parity']['cases']} 例，mismatches={len(mismatches)}")
    if mismatches:
        print(json.dumps(mismatches, ensure_ascii=False), file=sys.stderr)
        return 4
    if not args.check:
        print(f"已写入 {JSON_PATH.relative_to(ROOT)} / {MD_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
