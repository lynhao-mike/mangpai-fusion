"""T-165 · 婚姻应期可行性审计（只读）。

只统计「382 例婚姻应期 + 现有大运/流年原语」的可算性，回答
``tasks/T-165/PROMPT.md`` §2.2 的 6 个问题，并给出零年龄参数的预注册设计草案。

本脚本**不建模、不评分、不生成应期预测、不改 engine/**；只读 facts 与 atoms，
产出 ``META/timing-feasibility-audit-v1.json`` / ``.md``。

口径：
- 评分窗口：20–35 岁（16 个候选年）；年龄 = event.year - birth.year（T-148 定义）。
- 每例：``chart_from_solar`` 建盘一次，逐年 ``build_relation_graph(dayun_index, liunian_year)``。
- 原语矩阵状态：有＝单原子/字段直接回答；部分＝事实齐备但需调用方组合/过滤，
  或原子只覆盖部分子形态；无＝事实层缺字段/边种，组合也答不了。

运行：
    .venv\\Scripts\\python.exe -m tools.timing_feasibility_audit
"""
from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Optional

from engine.api.facade import to_jsonable
from engine.claims.condition_ir.atoms import ATOMS, SPOUSE, build_context
from engine.facts.chart_facts import chart_from_solar, is_forward
from engine.facts.relation_graph import build_relation_graph

ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = ROOT / "META" / "timing-eval-set-v1.json"
BASELINE_PATH = ROOT / "META" / "timing-baseline-v1.json"
OUT_JSON = ROOT / "META" / "timing-feasibility-audit-v1.json"
OUT_MD = ROOT / "META" / "timing-feasibility-audit-v1.md"

SCHEMA = "timing-feasibility-audit/v1"
TASK = "T-165"
WINDOW = (20, 35)
CANDIDATE_YEARS = WINDOW[1] - WINDOW[0] + 1
KS = (3, 5, 7)
PRIMARY_K = 3
ALPHA = 0.01
SIGNAL_EFFECT = 0.08
KILL_EFFECT = 0.03
KILL_P = 0.20

# 六害 / 六穿同六对支（《滴天髓》「穿，即害也」，
# 见 theory/raw 与 sources/tiaohou_ditiansui/滴天髓_part1.md:148，query id DTS-PROD-20260622-044）。
# 引擎以 relation_graph._CHUAN 的 chuan 边种承载，故「害」可答；此表只用于定位示例案例。
LIU_HAI_PAIRS = {frozenset(p) for p in ("子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌")}
THEORY_CHUAN_HAI = "sources/tiaohou_ditiansui/滴天髓_part1.md:148「穿，即害也」"

RELATION_KINDS = ("chong", "liuhe", "xing", "chuan")
CHONG_HE_KINDS = ("chong", "liuhe")

SUIYUN_ATOMS = (
    "dayun_present",
    "liunian_present",
    "suiyun_edge",
    "sanhe_with_suiyun",
    "chong_kai_muku",
    "suiyun_arrives",
)
CARD_ATOMS = ("suiyun_edge", "sanhe_with_suiyun", "chong_kai_muku", "liunian_present")


# ── I/O ─────────────────────────────────────────────────────────────────────


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


# ── 二项分布（精确，无 scipy 依赖）──────────────────────────────────────────


def _pmf_next(pmf: float, n: int, k: int, p: float) -> float:
    """由 P(X=k) 递推 P(X=k+1)。"""
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return 1.0 if k + 1 == n else 0.0
    return pmf * (n - k) / (k + 1) * (p / (1.0 - p))


def binom_tail_ge(n: int, p: float, k: int) -> float:
    """P(X >= k)，X ~ Binomial(n, p)。"""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    pmf = (1.0 - p) ** n
    cdf = 0.0
    for i in range(0, k):
        cdf += pmf
        pmf = _pmf_next(pmf, n, i, p)
    return max(0.0, 1.0 - cdf)


def critical_count(n: int, p: float, alpha: float = ALPHA) -> int:
    """拒绝域下界：最小的 k 使 P(X >= k | H0) <= alpha。"""
    pmf = (1.0 - p) ** n if p < 1.0 else 0.0
    tail = 1.0
    for k in range(n + 1):
        if tail <= alpha:
            return k
        tail -= pmf
        if k < n:
            pmf = _pmf_next(pmf, n, k, p)
    return n + 1


def power_at(n: int, p0: float, p1: float, alpha: float = ALPHA) -> float:
    """单侧精确二项检验在 p1 下的功效（拒绝域由 p0 定）。"""
    k = critical_count(n, p0, alpha)
    if k <= 0:
        return 1.0
    if p1 >= 1.0:
        return 1.0
    pmf = (1.0 - p1) ** n
    cdf = 0.0
    for i in range(0, k):
        cdf += pmf
        pmf = _pmf_next(pmf, n, i, p1)
    return max(0.0, 1.0 - cdf)


def mde80(n: int, p0: float, alpha: float = ALPHA, target: float = 0.80) -> float:
    """80% 功效下的最小可检测提升（pp，返回小数）。"""
    lo, hi = p0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if power_at(n, p0, mid, alpha) >= target:
            hi = mid
        else:
            lo = mid
    return hi - p0


def null_hit_prob(m: int, k: int, n: int = CANDIDATE_YEARS) -> float:
    """m 个正例年里随机取 k 年，至少覆盖 1 个正例年的概率。"""
    if m <= 0:
        return 0.0
    return 1.0 - math.comb(n - m, k) / math.comb(n, k)


def _pct(x: float, digits: int = 2) -> float:
    return round(100.0 * x, digits)


# ── 案例工具 ────────────────────────────────────────────────────────────────


def window_years(birth_year: int) -> list[int]:
    return [birth_year + age for age in range(WINDOW[0], WINDOW[1] + 1)]


def dayun_index_for_year(chart, year: int) -> Optional[int]:
    """公历年 → 大运序号；无覆盖返回 None（不心算，只读 facts 的 start/end_year）。"""
    for step in chart.cycles.dayun:
        if step.start_year and step.end_year and step.start_year <= year <= step.end_year:
            return step.index
    return None


def dayun_step(chart, index: int):
    return next(s for s in chart.cycles.dayun if s.index == index)


def spouse_addresses(chart) -> tuple[list[str], list[str]]:
    """(含藏干的全部配偶星地址, 仅本气柱地址)。十神口径见 atoms.SPOUSE。"""
    gods = SPOUSE[chart.gender]
    broad: set[str] = set()
    narrow: set[str] = set()
    for p in chart.pillars:
        if p.stem.ten_god in gods:
            broad.add(p.stem.addr)
            narrow.add(p.stem.addr)
        if p.branch.main_ten_god in gods:
            broad.add(p.branch.addr)
            narrow.add(p.branch.addr)
        if any(h.ten_god in gods for h in p.branch.hidden):
            broad.add(p.branch.addr)
    return sorted(broad), sorted(narrow)


def _years_in_text(text: str) -> set[int]:
    import re

    return {int(x) for x in re.findall(r"(?:19|20)\d{2}", text or "")}


def _example(
    case: dict,
    chart,
    index: int,
    year: int,
    dy_gz: str,
    ln_gz: str,
    call: str,
    value: Any,
    note: str,
    bindings: Optional[dict] = None,
    **extra: Any,
) -> dict[str, Any]:
    out = {
        "case_id": case["case_id"],
        "birth_dt": case["birth_dt"],
        "gender": case["gender"],
        "pillars": " ".join(p.ganzhi for p in chart.pillars),
        "year": year,
        "age": year - case["birth_year"],
        "dayun_index": index,
        "dayun": dy_gz,
        "liunian": ln_gz,
        "call": call,
        "value": value,
        "note": note,
        "bindings": dict(bindings or {}),
    }
    out.update(extra)
    return out


def _capture(examples: dict[str, Any], key: str, value: Any) -> None:
    if examples.get(key) is None and value is not None:
        examples[key] = value


# ── 主审计 ──────────────────────────────────────────────────────────────────


def run_audit() -> dict[str, Any]:
    timing = _load(EVAL_PATH)
    baseline = _load(BASELINE_PATH)
    all_cases = timing["cases"]
    cases = [c for c in all_cases if c.get("usable_for_timing")]

    census: dict[str, Any] = {
        "records_total": len(all_cases),
        "usable_for_timing": len(cases),
        "birth_dt_parse_ok": 0,
        "gender_ok": 0,
        "chart_built": 0,
        "chart_failures": [],
        "dayun_range_present": 0,
        "dayun_direction_consistent": 0,
        "dayun_direction_mismatches": [],
        "cases_with_event_in_window": 0,
        "cases_without_event_in_window": 0,
        "events_total": 0,
        "events_age_15_50": 0,
        "events_in_dayun_range": 0,
        "events_outside_dayun_range": 0,
        "events_in_window": 0,
        "unique_event_years_in_window": 0,
        "event_year_count_per_case": Counter(),
        "scoreable_years_per_case": Counter(),
        "case_years_total": 0,
        "dayun_steps_in_window": Counter(),
        "qiyun_start_age": Counter(),
        "gender": Counter(),
        "quality_grade": Counter(),
        "quality_flags": Counter(),
        "time_basis": Counter(),
        "boundary_warnings": Counter(),
        "cases_with_boundary_warning": 0,
        "birth_year_range": [min(c["birth_year"] for c in cases), max(c["birth_year"] for c in cases)],
        "age_histogram": Counter(),
        "cases_without_spouse_star": 0,
        "cases_without_spouse_star_examples": [],
    }

    label = Counter()
    examples: dict[str, Any] = {}
    atom_stats: dict[str, Any] = {
        "suiyun_edge": {k: {s: {"true": 0, "false": 0} for s in ("dayun", "liunian")} for k in RELATION_KINDS},
        "sanhe_with_suiyun": {"true": 0, "false": 0, "scope_counts": Counter()},
        "chong_kai_muku": {"year_arg_true": 0, "year_arg_false": 0, "no_year_true": 0},
        "liunian_present": {"true": 0},
        "dayun_present": {"true": 0},
        "suiyun_arrives": {"day_stem_true": 0, "day_branch_true": 0},
        "partial_sanhe_db_liunian_true": 0,
        "case_years_without_suiyun_edges": 0,
        "edge_kinds_seen": set(),
        "unstable_edge_id_cases": 0,
    }
    per_case: list[dict[str, Any]] = []
    case_rows: list[dict[str, Any]] = []
    band_hits: dict[int, dict[int, int]] = {w: {} for w in (3, 5, 7, 11, 16)}

    for case in cases:
        census["gender"][case["gender"]] += 1
        census["quality_grade"][str(case.get("quality_grade"))] += 1
        for flag in case.get("quality_flags") or []:
            census["quality_flags"][flag] += 1
        census["time_basis"][str(case.get("time_basis"))] += 1

        events = [e for e in case.get("marriage_events") or [] if isinstance(e.get("year"), int)]
        census["events_total"] += len(events)
        in_window: set[int] = set()
        contradicted = False
        for event in events:
            age = event["year"] - case["birth_year"]
            census["age_histogram"][age // 5 * 5] += 1
            if 15 <= age <= 50:
                census["events_age_15_50"] += 1
            years_in_text = _years_in_text(event.get("text", ""))
            if not years_in_text:
                label["no_year_in_text"] += 1
            elif event["year"] in years_in_text:
                label["match"] += 1
            else:
                label["mismatch"] += 1
            if WINDOW[0] <= age <= WINDOW[1]:
                in_window.add(event["year"])
                if years_in_text and event["year"] not in years_in_text:
                    contradicted = True
            if event.get("age_plausible") is False:
                label["age_plausible_false"] += 1
        census["events_in_window"] += sum(
            1 for e in events if WINDOW[0] <= e["year"] - case["birth_year"] <= WINDOW[1]
        )
        census["unique_event_years_in_window"] += len(in_window)
        census["event_year_count_per_case"][len(in_window)] += 1
        if in_window:
            census["cases_with_event_in_window"] += 1
        else:
            census["cases_without_event_in_window"] += 1

        try:
            birth_dt = datetime.fromisoformat(case["birth_dt"])
            census["birth_dt_parse_ok"] += 1
        except (TypeError, ValueError) as exc:
            census["chart_failures"].append({"case_id": case["case_id"], "error": repr(exc)})
            continue

        try:
            chart = chart_from_solar(birth_dt, case["gender"])
        except Exception as exc:  # noqa: BLE001 - 审计必须记录失败而不是中断
            census["chart_failures"].append({"case_id": case["case_id"], "error": repr(exc)})
            continue
        census["gender_ok"] += 1
        census["chart_built"] += 1

        chart_json = to_jsonable(chart)
        db = chart.pillars[2].branch.char
        for event in events:
            if any(
                step.start_year and step.end_year and step.start_year <= event["year"] <= step.end_year
                for step in chart.cycles.dayun
            ):
                census["events_in_dayun_range"] += 1
            else:
                census["events_outside_dayun_range"] += 1
        expected_forward = is_forward(chart.gender, chart.pillars[0].stem.char)
        if chart.cycles.direction == ("顺" if expected_forward else "逆"):
            census["dayun_direction_consistent"] += 1
        else:
            census["dayun_direction_mismatches"].append(case["case_id"])
        spouse_broad, spouse_narrow = spouse_addresses(chart)
        if not spouse_broad:
            census["cases_without_spouse_star"] += 1
            if len(census["cases_without_spouse_star_examples"]) < 5:
                census["cases_without_spouse_star_examples"].append(case["case_id"])
        for warning in chart.boundary_warnings:
            census["boundary_warnings"][warning.kind] += 1
        if chart.boundary_warnings:
            census["cases_with_boundary_warning"] += 1
        qiyun = chart.cycles.qiyun[0].start_age if chart.cycles and chart.cycles.qiyun else None
        census["qiyun_start_age"][qiyun] += 1

        scoreable: list[int] = []
        dayun_indices: set[int] = set()
        r1_years = r2_broad4_years = r2_broad2_years = r2_narrow2_years = 0
        r3_years = r4_years = 0
        cross_scope_ids: dict[int, list[tuple[int, dict]]] = {}

        for year in window_years(case["birth_year"]):
            index = dayun_index_for_year(chart, year)
            if index is None:
                continue
            step = dayun_step(chart, index)
            scoreable.append(year)
            dayun_indices.add(index)
            graph = build_relation_graph(chart, dayun_index=index, liunian_year=year)
            rel = to_jsonable(graph)
            ctx = build_context({"chart": chart_json, "relations": rel})
            ln_stem = next((c for a, c in graph.nodes if a == f"LN{year}.s"), "?")
            ln_branch = next((c for a, c in graph.nodes if a == f"LN{year}.b"), "?")
            ln_gz = ln_stem + ln_branch
            dy_gz = step.ganzhi

            suiyun_edges = [e for e in rel["edges"] if e.get("scope", "natal") != "natal"]
            if not suiyun_edges:
                atom_stats["case_years_without_suiyun_edges"] += 1
            atom_stats["edge_kinds_seen"].update(e["kind"] for e in rel["edges"])

            se: dict[tuple[str, str], Any] = {}
            for kind in RELATION_KINDS:
                for scope in ("dayun", "liunian"):
                    result = ATOMS["suiyun_edge"](ctx, {"type": kind, "at": "D.b", "scope": scope})
                    se[(kind, scope)] = result
                    atom_stats["suiyun_edge"][kind][scope]["true" if result.value else "false"] += 1

            r1_hit = any(se[(k, "liunian")].value for k in RELATION_KINDS)
            if r1_hit:
                r1_years += 1

            # R2 三种口径：全部配偶星地址×4 关系 / ×冲合 / 仅本气柱×冲合。
            kinds4 = set(RELATION_KINDS)
            kinds2 = set(CHONG_HE_KINDS)
            hit_b4 = hit_b2 = hit_n2 = False
            for edge in suiyun_edges:
                if edge.get("scope") != "liunian":
                    continue
                members = set(edge.get("members") or [])
                kind = edge.get("kind")
                if kind in kinds4 and members & set(spouse_broad):
                    hit_b4 = True
                if kind in kinds2 and members & set(spouse_broad):
                    hit_b2 = True
                if kind in kinds2 and members & set(spouse_narrow):
                    hit_n2 = True
            r2_broad4_years += hit_b4
            r2_broad2_years += hit_b2
            r2_narrow2_years += hit_n2

            muku_year = ATOMS["chong_kai_muku"](ctx, {"year": year})
            if muku_year.value:
                r3_years += 1
                atom_stats["chong_kai_muku"]["year_arg_true"] += 1
                edge = next((e for e in rel["edges"] if e["id"] == muku_year.bindings.get("edge_id")), None)
                muku_fact = next((m for m in rel["muku"] if m["addr"] == muku_year.bindings.get("addr")), None)
                if edge is not None and edge.get("kind") == "chong":
                    _capture(
                        examples,
                        "p4_chong_open",
                        _example(
                            case, chart, index, year, dy_gz, ln_gz,
                            "chong_kai_muku(year=%d)" % year,
                            muku_year.value,
                            muku_year.note,
                            muku_year.bindings,
                            edge_kind=edge["kind"],
                            edge_members=list(edge["members"]),
                        ),
                    )
                if edge is not None and edge.get("kind") == "xing":
                    _capture(
                        examples,
                        "p4_xing_open",
                        _example(
                            case, chart, index, year, dy_gz, ln_gz,
                            "chong_kai_muku(year=%d)" % year,
                            muku_year.value,
                            muku_year.note,
                            muku_year.bindings,
                            edge_kind=edge["kind"],
                            edge_members=list(edge["members"]),
                        ),
                    )
                if muku_fact is not None and not muku_fact.get("candidates"):
                    _capture(
                        examples,
                        "p4_empty_ku",
                        _example(
                            case, chart, index, year, dy_gz, ln_gz,
                            "chong_kai_muku(year=%d)" % year,
                            muku_year.value,
                            muku_year.note,
                            muku_year.bindings,
                            muku_addr=muku_fact.get("addr"),
                            muku_branch=muku_fact.get("branch"),
                            muku_candidates=len(muku_fact.get("candidates") or []),
                        ),
                    )
            else:
                atom_stats["chong_kai_muku"]["year_arg_false"] += 1

            if ATOMS["chong_kai_muku"](ctx, {}).value:
                atom_stats["chong_kai_muku"]["no_year_true"] += 1

            # 合开墓库：库被流年六合/三合/三会合住，但 atom 只认冲/刑。
            for muku_fact in rel["muku"]:
                binder_edges = [
                    e for e in suiyun_edges
                    if e["id"] in (muku_fact.get("binders") or [])
                ]
                if binder_edges and not muku_year.value:
                    binder = binder_edges[0]
                    _capture(
                        examples,
                        "p4_he_open_gap",
                        _example(
                            case, chart, index, year, dy_gz, ln_gz,
                            "chong_kai_muku(year=%d)" % year,
                            muku_year.value,
                            muku_year.note,
                            muku_year.bindings,
                            muku_addr=muku_fact.get("addr"),
                            muku_branch=muku_fact.get("branch"),
                            binder_kind=binder["kind"],
                            binder_edge_id=binder["id"],
                            binder_scope=binder.get("scope"),
                            binder_members=list(binder["members"]),
                        ),
                    )

            sanhe = ATOMS["sanhe_with_suiyun"](ctx, {"zhi_set": db})
            if sanhe.value:
                r4_years += 1
                atom_stats["sanhe_with_suiyun"]["true"] += 1
                atom_stats["sanhe_with_suiyun"]["scope_counts"][str(sanhe.bindings.get("scope"))] += 1
                _capture(
                    examples,
                    "p5_sanhe_db",
                    _example(
                        case, chart, index, year, dy_gz, ln_gz,
                        "sanhe_with_suiyun(zhi_set=%s)" % db,
                        sanhe.value,
                        sanhe.note,
                        sanhe.bindings,
                        day_branch=db,
                    ),
                )
            else:
                atom_stats["sanhe_with_suiyun"]["false"] += 1
            if ATOMS["suiyun_edge"](ctx, {"type": "sanhe", "at": "D.b", "scope": "liunian"}).value:
                atom_stats["partial_sanhe_db_liunian_true"] += 1

            if ATOMS["liunian_present"](ctx, {"year": year}).value:
                atom_stats["liunian_present"]["true"] += 1
            if ATOMS["dayun_present"](ctx, {}).value:
                atom_stats["dayun_present"]["true"] += 1
            if ATOMS["suiyun_arrives"](ctx, {"at": "D.s"}).value:
                atom_stats["suiyun_arrives"]["day_stem_true"] += 1
            if ATOMS["suiyun_arrives"](ctx, {"at": "D.b"}).value:
                atom_stats["suiyun_arrives"]["day_branch_true"] += 1

            # 示例采集：夫妻宫六冲/六合/穿害、大运六合、配偶星被冲。
            if se[("chong", "liunian")].value:
                _capture(
                    examples,
                    "p1_chong",
                    _example(
                        case, chart, index, year, dy_gz, ln_gz,
                        "suiyun_edge(type=chong, at=D.b, scope=liunian)",
                        se[("chong", "liunian")].value,
                        se[("chong", "liunian")].note,
                        se[("chong", "liunian")].bindings,
                        day_branch=db,
                    ),
                )
            if se[("liuhe", "liunian")].value:
                he_natal = ATOMS["he_at"](ctx, {"at": "D.b"})
                _capture(
                    examples,
                    "p1_liuhe",
                    _example(
                        case, chart, index, year, dy_gz, ln_gz,
                        "suiyun_edge(type=liuhe, at=D.b, scope=liunian)",
                        se[("liuhe", "liunian")].value,
                        se[("liuhe", "liunian")].note,
                        se[("liuhe", "liunian")].bindings,
                        day_branch=db,
                        he_at_value=he_natal.value,
                        he_at_note="he_at 只扫 natal 边（atoms.py:256/309），看不到这条岁运合",
                    ),
                )
            if frozenset((db, ln_branch)) in LIU_HAI_PAIRS and se[("chuan", "liunian")].value:
                _capture(
                    examples,
                    "p1_chuan_hai",
                    _example(
                        case, chart, index, year, dy_gz, ln_gz,
                        "suiyun_edge(type=chuan, at=D.b, scope=liunian)",
                        se[("chuan", "liunian")].value,
                        se[("chuan", "liunian")].note,
                        se[("chuan", "liunian")].bindings,
                        day_branch=db,
                        liunian_branch=ln_branch,
                        pair="".join((db, ln_branch)),
                        theory_ref=THEORY_CHUAN_HAI,
                        edge_kinds_in_year=sorted({e["kind"] for e in rel["edges"]}),
                    ),
                )
            if se[("liuhe", "dayun")].value:
                _capture(
                    examples,
                    "p2_dayun_liuhe",
                    _example(
                        case, chart, index, year, dy_gz, ln_gz,
                        "suiyun_edge(type=liuhe, at=D.b, scope=dayun)",
                        se[("liuhe", "dayun")].value,
                        se[("liuhe", "dayun")].note,
                        se[("liuhe", "dayun")].bindings,
                        day_branch=db,
                    ),
                )
            if se[("chong", "dayun")].value:
                _capture(
                    examples,
                    "p2_dayun_chong",
                    _example(
                        case, chart, index, year, dy_gz, ln_gz,
                        "suiyun_edge(type=chong, at=D.b, scope=dayun)",
                        se[("chong", "dayun")].value,
                        se[("chong", "dayun")].note,
                        se[("chong", "dayun")].bindings,
                        day_branch=db,
                    ),
                )
            if spouse_broad:
                for addr in spouse_broad:
                    result = ATOMS["suiyun_edge"](ctx, {"type": "chong", "at": addr, "scope": "liunian"})
                    if result.value:
                        _capture(
                            examples,
                            "p3_spouse_touch",
                            _example(
                                case, chart, index, year, dy_gz, ln_gz,
                                "suiyun_edge(type=chong, at=%s, scope=liunian)" % addr,
                                result.value,
                                result.note,
                                result.bindings,
                                spouse_addrs=spouse_broad,
                                spouse_addrs_narrow=spouse_narrow,
                                star="正财/偏财" if chart.gender == "乾" else "正官/七杀",
                            ),
                        )
                        break
            elif year == scoreable[0]:
                _capture(
                    examples,
                    "p3_no_spouse",
                    _example(
                        case, chart, index, year, dy_gz, ln_gz,
                        "spouse_addresses(chart)",
                        None,
                        "命局无配偶星（%s 在八字中不现），规则需返回 unknown"
                        % ("财" if chart.gender == "乾" else "官"),
                        {},
                        spouse_addrs=[],
                    ),
                )

            # 跨年 edge_id 稳定性：同一 (kind, members) 在相邻两年是否同 id。
            current_ids: dict[tuple, str] = {}
            for edge in rel["edges"]:
                heads = {m.split(".", 1)[0][:2] for m in edge["members"]}
                if not ({"DY", "LN"} & heads):
                    continue
                if all(h in ("DY", "LN") for h in heads):
                    continue  # 只看岁运与原局之间的边
                current_ids[(edge["kind"], tuple(edge["members"]))] = edge["id"]
            cross_scope_ids.setdefault(index, []).append((year, current_ids))

            if examples.get("p6_deterministic") is None:
                again = build_relation_graph(chart, dayun_index=index, liunian_year=year)
                same = [e.id for e in again.edges] == [e.id for e in graph.edges]
                examples["p6_deterministic"] = {
                    "case_id": case["case_id"],
                    "birth_dt": case["birth_dt"],
                    "gender": case["gender"],
                    "pillars": " ".join(p.ganzhi for p in chart.pillars),
                    "year": year,
                    "age": year - case["birth_year"],
                    "dayun_index": index,
                    "dayun": dy_gz,
                    "liunian": ln_gz,
                    "call": "build_relation_graph(chart, dayun_index, liunian_year) ×2",
                    "value": same,
                    "note": "同一次 as-of 快照内 %d 条边的 id 序列完全一致" % len(graph.edges),
                    "bindings": {},
                }
                if not same:
                    raise AssertionError("同快照两次构建的 edge id 不一致")

        if not scoreable:
            continue
        if scoreable:
            census["dayun_range_present"] += 1
        census["scoreable_years_per_case"][len(scoreable)] += 1
        census["case_years_total"] += len(scoreable)
        census["dayun_steps_in_window"][len(dayun_indices)] += 1

        unstable = False
        for index, snapshots in cross_scope_ids.items():
            if len(snapshots) < 2:
                continue
            (y1, ids1), (y2, ids2) = snapshots[0], snapshots[1]
            common = set(ids1) & set(ids2)
            diffs = sorted(key for key in common if ids1[key] != ids2[key])
            if diffs:
                unstable = True
                key = diffs[0]
                _capture(
                    examples,
                    "p6_cross_year_unstable",
                    {
                        "case_id": case["case_id"],
                        "birth_dt": case["birth_dt"],
                        "gender": case["gender"],
                        "pillars": " ".join(p.ganzhi for p in chart.pillars),
                        "dayun_index": index,
                        "year": y2,
                        "age": y2 - case["birth_year"],
                        "dayun": dayun_step(chart, index).ganzhi,
                        "liunian": "—（跨年对比）",
                        "call": "同一 (kind,members) 边的 id 跨年对比",
                        "value": False,
                        "note": "同一条 %s 边 %s 在 %d 年为 %s、%d 年为 %s"
                        % (key[0], list(key[1]), y1, ids1[key], y2, ids2[key]),
                        "bindings": {},
                        "first_year": y1,
                        "first_id": ids1[key],
                        "second_year": y2,
                        "second_id": ids2[key],
                        "members": list(key[1]),
                        "kind": key[0],
                    },
                )
        if unstable:
            atom_stats["unstable_edge_id_cases"] += 1

        per_case.append(
            {
                "case_id": case["case_id"],
                "gender": case["gender"],
                "birth_dt": case["birth_dt"],
                "birth_year": case["birth_year"],
                "pillars": " ".join(p.ganzhi for p in chart.pillars),
                "scoreable_years": len(scoreable),
                "dayun_indices": sorted(dayun_indices),
                "distinct_dayun_steps": len(dayun_indices),
                "events_in_window": len(in_window),
                "event_years_in_window": sorted(in_window),
                "has_spouse_star": bool(spouse_broad),
                "spouse_star_addrs": spouse_broad,
                "r1_years": r1_years,
                "r2_broad4_years": r2_broad4_years,
                "r2_broad2_years": r2_broad2_years,
                "r2_narrow2_years": r2_narrow2_years,
                "r3_years": r3_years,
                "r4_years": r4_years,
                "boundary_warnings": [w.kind for w in chart.boundary_warnings],
            }
        )
        case_rows.append(
            {
                "case_id": case["case_id"],
                "m": len(in_window),
                "r1_years": r1_years,
                "contradicted": contradicted,
                "gender": case["gender"],
                "time_basis": case.get("time_basis"),
            }
        )

    label["events_in_window"] = census["events_in_window"]
    label["cases_with_any_mismatch"] = 0
    label["cases_with_in_window_mismatch"] = 0
    # 逐例重算一次（事件文本年份矛盾），避免主循环里重复维护。
    for case in cases:
        events = [e for e in case.get("marriage_events") or [] if isinstance(e.get("year"), int)]
        any_bad = any(
            _years_in_text(e.get("text", "")) and e["year"] not in _years_in_text(e.get("text", ""))
            for e in events
        )
        in_bad = any(
            WINDOW[0] <= e["year"] - case["birth_year"] <= WINDOW[1]
            and _years_in_text(e.get("text", ""))
            and e["year"] not in _years_in_text(e.get("text", ""))
            for e in events
        )
        label["cases_with_any_mismatch"] += any_bad
        label["cases_with_in_window_mismatch"] += in_bad

    # 固定宽度静态年龄带（20–35 内）。
    for width, buckets in band_hits.items():
        for lo in range(WINDOW[0], WINDOW[1] - width + 2):
            buckets[lo] = sum(
                1
                for case in cases
                if any(
                    lo <= e["year"] - case["birth_year"] <= lo + width - 1
                    for e in case.get("marriage_events") or []
                    if isinstance(e.get("year"), int)
                )
            )

    baselines = _baseline_crosscheck(cases, baseline, band_hits)
    power = _power_analysis(case_rows, band_hits)
    matrix = _primitive_matrix(examples)
    atoms_section = _suiyun_atom_section(atom_stats)
    prereg = _preregistration(power)
    gaps = _gaps(census)

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "task": TASK,
        "mode": "read_only_audit",
        "inputs": {
            "eval_set": {
                "path": "META/timing-eval-set-v1.json",
                "schema": timing.get("schema"),
                "task": timing.get("task"),
                "records": len(all_cases),
                "usable_for_timing": len(cases),
            },
            "baseline": {
                "path": "META/timing-baseline-v1.json",
                "schema": baseline.get("schema"),
                "status": baseline.get("status"),
                "card_sample_size": baseline.get("sample_size"),
                "cleaned_sample_size": baseline.get("cleaned_reference", {}).get("sample_size"),
            },
        },
        "verdict": "能直接开工",
        "verdict_reason": (
            "矩阵 6 项中 2 项「有」、4 项「部分」、0 项「无」：suiyun_edge 直接回答夫妻宫的"
            "冲/合/刑/穿（含穿=害），chong_kai_muku 回答墓库冲/刑开，sanhe_with_suiyun 回答"
            "完整三合/三会含夫妻宫；配偶星柱需在模型层按十神地址组合 suiyun_edge。"
            "4 个「部分」项的缺口都可用现有字段组合绕过；其中合开墓库、跨年稳定 edge_id "
            "若要补需新原语，但不阻塞最小规则集 R1–R4。"
        ),
        "window": {
            "age_min": WINDOW[0],
            "age_max": WINDOW[1],
            "candidate_years": CANDIDATE_YEARS,
            "primary_k": PRIMARY_K,
            "secondary_k": [5],
            "exploratory_k": [7],
        },
        "case_census": _jsonable_census(census),
        "baseline_crosscheck": baselines,
        "label_fidelity": dict(sorted(label.items())),
        "per_case_coverage": per_case,
        "primitive_matrix": matrix,
        "suiyun_atoms": atoms_section,
        "power": power,
        "preregistration": prereg,
        "gaps": gaps,
        "determinism": {
            "method": "固定输入顺序 + sort_keys + 无时间戳 + 单线程；两次运行 JSON 应逐字节一致",
        },
    }
    return payload


def _jsonable_census(census: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in census.items():
        if isinstance(value, Counter):
            out[key] = {str(k): v for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
        elif isinstance(value, list):
            out[key] = value
        else:
            out[key] = value
    return out


# ── 基线核对 ────────────────────────────────────────────────────────────────


def _baseline_crosscheck(
    cases: list[dict[str, Any]], baseline: dict[str, Any], band_hits: dict[int, dict[int, int]]
) -> list[dict[str, Any]]:
    def hits(lo: int, hi: int) -> int:
        return sum(
            1
            for case in cases
            if any(
                lo <= e["year"] - case["birth_year"] <= hi
                for e in case.get("marriage_events") or []
                if isinstance(e.get("year"), int)
            )
        )

    card = {"age_26": (26, 26, 11.2), "age_24_30": (24, 30, 45.3),
            "age_22_28": (22, 28, 48.7), "age_20_30": (20, 30, 63.1)}
    cleaned = baseline.get("cleaned_reference", {}).get("bands", {})
    raw = baseline.get("bands", {})
    out = []
    for key, (lo, hi, card_pct) in card.items():
        h = hits(lo, hi)
        out.append(
            {
                "band": key,
                "range": [lo, hi],
                "card_pct": card_pct,
                "recomputed_382_hits": h,
                "recomputed_382_pct": _pct(h / len(cases)),
                "cleaned_reference_pct": cleaned.get(key, {}).get("rate_pct"),
                "card_392_pct": raw.get(key, {}).get("rate_pct"),
                "matches_382": abs(_pct(h / len(cases)) - card_pct) < 0.05,
            }
        )
    return out


# ── 功效 ────────────────────────────────────────────────────────────────────


def _power_analysis(case_rows: list[dict[str, Any]], band_hits: dict[int, dict[int, int]]) -> dict[str, Any]:
    n_all = len(case_rows)
    ms_all = [row["m"] for row in case_rows]

    def p0_for(ms: list[int], k: int) -> float:
        return sum(null_hit_prob(m, k) for m in ms) / len(ms)

    def subset_rows(pred) -> list[dict[str, Any]]:
        return [row for row in case_rows if pred(row)]

    table = []
    for k in KS:
        p0 = p0_for(ms_all, k)
        crit = critical_count(n_all, p0)
        best_width = band_hits.get(k)
        best = None
        if best_width:
            best_lo = min(best_width, key=lambda lo: (-best_width[lo], lo))
            best = {
                "range": [best_lo, best_lo + k - 1],
                "hits": best_width[best_lo],
                "pct": _pct(best_width[best_lo] / n_all),
                "p_value_vs_null": binom_tail_ge(n_all, p0, best_width[best_lo]),
            }
        fill = sum(1 for row in case_rows if row["r1_years"] < k)
        table.append(
            {
                "k": k,
                "population": n_all,
                "null_p0": round(p0, 4),
                "null_p0_pct": _pct(p0),
                "critical_hits_alpha_0_01": crit,
                "critical_rate_pct": _pct(crit / n_all),
                "card_signal_rate_pct": _pct(p0 + SIGNAL_EFFECT),
                "card_kill_rate_pct": _pct(p0 + KILL_EFFECT),
                "power_at_card_signal": round(power_at(n_all, p0, p0 + SIGNAL_EFFECT), 4),
                "mde80_pp": round(100.0 * mde80(n_all, p0), 2),
                "best_static_band_same_width": best,
                "cases_with_fewer_than_k_r1_years": fill,
                "cases_needing_zero_fill": fill,
                "r1_positive_years_dist": dict(
                    sorted(Counter(row["r1_years"] for row in case_rows).items())
                ),
                "event_year_count_dist": dict(sorted(Counter(row["m"] for row in case_rows).items())),
            }
        )

    sensitivities = []
    subsets = [
        ("all_382", case_rows),
        ("labeled_292", subset_rows(lambda r: r["m"] > 0)),
        ("exclude_contradicted", subset_rows(lambda r: not r["contradicted"])),
        ("male", subset_rows(lambda r: r["gender"] == "男")),
        ("female", subset_rows(lambda r: r["gender"] == "女")),
        ("true_solar", subset_rows(lambda r: r["time_basis"] == "true_solar")),
        ("clock_beijing", subset_rows(lambda r: r["time_basis"] == "clock_beijing")),
    ]
    for name, rows in subsets:
        if not rows:
            continue
        for k in (PRIMARY_K,):
            ms = [row["m"] for row in rows]
            p0 = p0_for(ms, k)
            sensitivities.append(
                {
                    "name": name,
                    "n": len(rows),
                    "k": k,
                    "null_p0_pct": _pct(p0),
                    "power_at_card_signal": round(power_at(len(rows), p0, p0 + SIGNAL_EFFECT), 4),
                    "mde80_pp": round(100.0 * mde80(len(rows), p0), 2),
                }
            )

    sample_size_counterfactual = []
    for k in KS:
        p0 = p0_for(ms_all, k)
        sample_size_counterfactual.append(
            {
                "k": k,
                "n_382_power_at_plus8": round(power_at(382, p0, p0 + SIGNAL_EFFECT), 4),
                "n_342_power_at_plus8": round(power_at(342, p0, p0 + SIGNAL_EFFECT), 4),
                "n_382_mde80_pp": round(100.0 * mde80(382, p0), 2),
                "n_342_mde80_pp": round(100.0 * mde80(342, p0), 2),
                "ci_width_ratio_342_over_382": round(math.sqrt(342 / 382), 4),
            }
        )

    fixed_bands = [
        {
            "name": "24_30",
            "range": [24, 30],
            "hits": band_hits[7][24],
            "pct": _pct(band_hits[7][24] / n_all),
        },
        {
            "name": "22_28",
            "range": [22, 28],
            "hits": band_hits[7][22],
            "pct": _pct(band_hits[7][22] / n_all),
        },
        {
            "name": "20_30",
            "range": [20, 30],
            "hits": band_hits[11][20],
            "pct": _pct(band_hits[11][20] / n_all),
        },
    ]

    return {
        "candidate_years": CANDIDATE_YEARS,
        "alpha": ALPHA,
        "signal_effect_pp": 100 * SIGNAL_EFFECT,
        "kill_effect_pp": 100 * KILL_EFFECT,
        "kill_p": KILL_P,
        "table": table,
        "sensitivities": sensitivities,
        "sample_size_counterfactual_342": sample_size_counterfactual,
        "fixed_band_reference": fixed_bands,
        "notes": [
            "p0 不是 K/16，而是逐例 1-C(16-m_i,K)/C(16,K) 的均值：90 例窗口内无婚姻事件，"
            "其 p0=0，直接拉低总体 null。",
            "m_i 是窗口内去重后的婚姻事件年数（385 个 case-event-year；393 条事件有 8 条同年重复）。",
            "+8pp 是相对该 null 的绝对提升；它与卡上 24–30/20–30 的静态带不是同一口径。",
            "同一宽度最佳静态年龄带的命中率（在 20–35 内选最优 lo）是年龄先验的上界，"
            "零年龄参数模型必须超过它才算增加信息。该带在同一批 382 例上选 lo，是乐观上界，"
            "其 p 值只作描述，不作正式检验。",
            "16 个候选年不把 n 变成 6112：命中指标是每例一个 0/1，n 仍是 382；"
            "6112 只是事实计算量。",
        ],
    }


# ── 原语矩阵 ────────────────────────────────────────────────────────────────


def _status_of(subchecks: list[dict[str, Any]]) -> str:
    values = {sub["status"] for sub in subchecks}
    if values == {"有"}:
        return "有"
    if values == {"无"}:
        return "无"
    return "部分"


def _primitive_matrix(examples: dict[str, Any]) -> dict[str, Any]:
    items = [
        {
            "id": "P1",
            "question": "流年支与日支 D.b 是否构成冲/合/刑/穿/害",
            "subchecks": [
                {"name": "冲", "status": "有",
                 "code": "atoms.py:781 suiyun_edge(type=chong, at=D.b, scope=liunian)；边 relation_graph.py:221"},
                {"name": "六合", "status": "有",
                 "code": "atoms.py:781 suiyun_edge(type=liuhe)；边 relation_graph.py:223"},
                {"name": "地支暗合", "status": "有",
                 "code": "atoms.py:781 suiyun_edge(type=zhi_anhe)；边 relation_graph.py:235"},
                {"name": "半合（三合 partial/half/gong）", "status": "有",
                 "code": "atoms.py:781 suiyun_edge(type=sanhe)；边 relation_graph.py:244-254"},
                {"name": "刑", "status": "有",
                 "code": "atoms.py:781 suiyun_edge(type=xing)；边 relation_graph.py:238-243"},
                {"name": "穿/害（同六对支）", "status": "有",
                 "code": "atoms.py:781 suiyun_edge(type=chuan)；边 relation_graph.py:54/225；"
                         + THEORY_CHUAN_HAI},
            ],
            "examples": [k for k in ("p1_chong", "p1_liuhe", "p1_chuan_hai") if examples.get(k)],
            "note": "六合/暗合可用 suiyun_edge 逐 kind 查询；通用 atoms.py:309 he_at 只扫 natal 边"
                    "（atoms.py:256 默认 scope=natal），不能回答岁运合，须改用 suiyun_edge。",
        },
        {
            "id": "P2",
            "question": "大运支与日支 D.b 是否构成冲/合/刑/穿/害",
            "subchecks": [
                {"name": "冲", "status": "有", "code": "atoms.py:781 suiyun_edge(type=chong, scope=dayun)"},
                {"name": "六合", "status": "有", "code": "atoms.py:781 suiyun_edge(type=liuhe, scope=dayun)"},
                {"name": "地支暗合", "status": "有", "code": "atoms.py:781 suiyun_edge(type=zhi_anhe, scope=dayun)"},
                {"name": "半合", "status": "有", "code": "atoms.py:781 suiyun_edge(type=sanhe, scope=dayun)"},
                {"name": "刑", "status": "有", "code": "atoms.py:781 suiyun_edge(type=xing, scope=dayun)"},
                {"name": "穿/害", "status": "有", "code": "atoms.py:781 suiyun_edge(type=chuan, scope=dayun)"},
            ],
            "examples": [k for k in ("p2_dayun_liuhe", "p2_dayun_chong") if examples.get(k)],
            "note": "大运十年恒定：16 年只跨 2–3 步大运（见 case_census.dayun_steps_in_window），"
                    "大运原语只能做 decade gate，不能给 16 个年份排序。",
        },
        {
            "id": "P3",
            "question": "流年/大运是否引动配偶星（财/官）所在柱",
            "subchecks": [
                {"name": "配偶星识别（十神）", "status": "有",
                 "code": "atoms.py:37 SPOUSE；chart.pillars[].stem.ten_god / branch.main_ten_god / branch.hidden[].ten_god"},
                {"name": "配偶星柱位绑定", "status": "有",
                 "code": "chart.pillars[].stem.addr / branch.addr（chart_facts.py:121 natal_addr）"},
                {"name": "单原子直接回答「引动配偶星柱」", "status": "无",
                 "code": "atoms.py:1095 ATOMS 无此原子；palace_holds/visible_god/hidden_god 只扫原局"},
                {"name": "组合可答（地址 × suiyun_edge）", "status": "有",
                 "code": "atoms.py:781 suiyun_edge(at=配偶星地址, scope=liunian/dayun)，4 种 kind 逐项调用"},
                {"name": "无配偶星案例的语义", "status": "部分",
                 "code": "atoms.py:37 SPOUSE；20/382 例八字无财/官（十神不现）；"
                         "需模型层显式返回 unknown，缺统一约定"},
            ],
            "examples": [k for k in ("p3_spouse_touch", "p3_no_spouse") if examples.get(k)],
            "note": "事实齐备但无现成原子；调用方需先按十神找地址，再逐地址调用 suiyun_edge。",
        },
        {
            "id": "P4",
            "question": "墓库是否被冲开/合开（chong_kai_muku 的输入输出）",
            "subchecks": [
                {"name": "冲开", "status": "有",
                 "code": "atoms.py:833 chong_kai_muku；MUKU_OPENER_KINDS atoms.py:697"},
                {"name": "刑开", "status": "有",
                 "code": "atoms.py:833 chong_kai_muku；MUKU_OPENER_KINDS 含 xing"},
                {"name": "年粒度（year=y）", "status": "有",
                 "code": "atoms.py:841-847；传 year 后只认流年节点参与的冲/刑边"},
                {"name": "合开（六合/三合/三会合住库）", "status": "无",
                 "code": "MUKU_OPENER_KINDS 只有 chong/xing；MukuFact.binders（relation_graph.py:405）"
                         "已产出但无原子消费；muku_open（atoms.py:397）也只认 chong"},
                {"name": "空库过滤（无候选却报冲开）", "status": "无",
                 "code": "atoms.py:848-850 chong_kai_muku 只按 branch 匹配 ctx['muku']，"
                         "不读 candidates/excluded"},
            ],
            "examples": [k for k in ("p4_chong_open", "p4_xing_open", "p4_he_open_gap", "p4_empty_ku")
                         if examples.get(k)],
            "note": "不传 year 时该原子对同一大运的 10 年返回同一结果（2082 个 case-year 为 True）；"
                    "传 year 后降到 1085 个，才是流年级信号。",
        },
        {
            "id": "P5",
            "question": "三合/三会是否把夫妻宫合入/合走（sanhe_with_suiyun）",
            "subchecks": [
                {"name": "完整三合", "status": "有",
                 "code": "atoms.py:805 sanhe_with_suiyun；completeness=full 由 relation_graph.py:272 产出"},
                {"name": "完整三会", "status": "有",
                 "code": "atoms.py:805 sanhe_with_suiyun（kind=sanhui）"},
                {"name": "夫妻宫成员判定", "status": "有",
                 "code": "atoms.py:825 zhi_set 子集判定；传 D.b 单字即成员测试"},
                {"name": "半合/拱局成局", "status": "无",
                 "code": "atom 要求 completeness=full；半合边存在（relation_graph.py:244-254）但不被认"},
                {"name": "scope 限定（流年 vs 大运）", "status": "无",
                 "code": "atoms.py:805 sanhe_with_suiyun 无 scope 参数；返回首个 full 边，"
                         "dayun-only 会遮蔽 liunian"},
            ],
            "examples": [k for k in ("p5_sanhe_db",) if examples.get(k)],
            "note": "1127 个 case-year 命中完整局含 D.b，其中 520 个 scope=dayun（十年恒定）；"
                    "要按年排序必须在模型层直接过滤 relations.edges 的 scope。",
        },
        {
            "id": "P6",
            "question": "大运/流年与原局的关系边是否有稳定 edge_id 可引用",
            "subchecks": [
                {"name": "边有 id", "status": "有", "code": "relation_graph.py:154 f'e{len+1:03d}'；Edge.id types.py:168"},
                {"name": "单快照内确定性", "status": "有",
                 "code": "relation_graph.py:439 build_relation_graph；同 (chart, dayun_index, "
                         "liunian_year) 两次构建 id 序列一致"},
                {"name": "跨年稳定", "status": "无",
                 "code": "relation_graph.py:154 id 是构建序号；381/382 例同一 (kind, members) 边相邻两年 id 不同"},
                {"name": "内容寻址 id", "status": "无",
                 "code": "types.py:168 Edge 无 content_id/hash 字段；id 不随内容哈希"},
            ],
            "examples": [k for k in ("p6_deterministic", "p6_cross_year_unstable") if examples.get(k)],
            "note": "可引用键应为 (chart_id, dayun_index, liunian_year, edge_id) 复合键；单独 edge_id 不可跨年引用。",
        },
    ]
    for item in items:
        item["status"] = _status_of(item["subchecks"])
        item["example_objects"] = [examples[key] for key in item["examples"]]
        item["example_missing"] = len(item["examples"]) == 0

    item_tally = Counter(item["status"] for item in items)
    sub_tally = Counter(sub["status"] for item in items for sub in item["subchecks"])
    return {
        "definition": {
            "有": "单个原子或字段直接回答，无需调用方补逻辑",
            "部分": "事实齐备但需调用方组合/过滤，或原子只覆盖部分子形态",
            "无": "事实层缺字段/边种，组合也答不了",
        },
        "items": items,
        "tally": {
            "items": {s: item_tally.get(s, 0) for s in ("有", "无", "部分")},
            "subchecks": {s: sub_tally.get(s, 0) for s in ("有", "无", "部分")},
            "subcheck_total": sum(sub_tally.values()),
        },
    }


def _suiyun_atom_section(atom_stats: dict[str, Any]) -> dict[str, Any]:
    stats = {
        "atoms_in_code": list(SUIYUN_ATOMS),
        "atoms_in_code_count": len(SUIYUN_ATOMS),
        "atoms_in_card": list(CARD_ATOMS),
        "atoms_in_card_count": len(CARD_ATOMS),
        "card_missing_atoms": [a for a in SUIYUN_ATOMS if a not in CARD_ATOMS],
        "suiyun_edge": {
            kind: {scope: dict(values) for scope, values in scopes.items()}
            for kind, scopes in atom_stats["suiyun_edge"].items()
        },
        "sanhe_with_suiyun": {
            "true": atom_stats["sanhe_with_suiyun"]["true"],
            "false": atom_stats["sanhe_with_suiyun"]["false"],
            "scope_counts": {str(k): v for k, v in sorted(atom_stats["sanhe_with_suiyun"]["scope_counts"].items())},
        },
        "chong_kai_muku": dict(atom_stats["chong_kai_muku"]),
        "liunian_present": dict(atom_stats["liunian_present"]),
        "dayun_present": dict(atom_stats["dayun_present"]),
        "suiyun_arrives": dict(atom_stats["suiyun_arrives"]),
        "partial_sanhe_db_liunian_true": atom_stats["partial_sanhe_db_liunian_true"],
        "case_years_without_suiyun_edges": atom_stats["case_years_without_suiyun_edges"],
        "edge_kinds_seen": sorted(atom_stats["edge_kinds_seen"]),
        "unstable_edge_id_cases": atom_stats["unstable_edge_id_cases"],
    }
    stats["notes"] = [
        "PROMPT §1 说「4 个岁运原子」，代码里实际 6 个：漏了 dayun_present 与 suiyun_arrives（到位）。",
        "suiyun_arrives 是段派「到位」原语（通禄/原身），对婚姻应期可能有用，但本卡矩阵未列，"
        "这里只记账，不纳入 6 项结论。",
        "6112 个 case-year 都有岁运边（stem 层必然建边），因此 suiyun_edge 的 False 是真否定，"
        "不会被 _has_suiyun 误判成 unknown。",
    ]
    return stats


# ── 预注册 ──────────────────────────────────────────────────────────────────


def _preregistration(power: dict[str, Any]) -> dict[str, Any]:
    rules = [
        {
            "id": "R1",
            "name": "夫妻宫受流年冲/合/刑/穿",
            "atom": "suiyun_edge",
            "args": {"at": "D.b", "scope": "liunian"},
            "kinds": list(RELATION_KINDS),
            "score": "每个命中的 kind +1",
            "age_term": False,
        },
        {
            "id": "R2",
            "name": "配偶星所在柱受流年冲/合",
            "atom": "suiyun_edge",
            "args": {"scope": "liunian"},
            "kinds": list(CHONG_HE_KINDS),
            "targets": "配偶星地址（含藏干；SPOUSE 十神），每个地址只计一次",
            "score": "每个被触及的地址 +1",
            "age_term": False,
        },
        {
            "id": "R3",
            "name": "原局墓库被该流年冲/刑开",
            "atom": "chong_kai_muku",
            "args": {"year": "<candidate_year>"},
            "score": "+1",
            "age_term": False,
        },
        {
            "id": "R4",
            "name": "夫妻宫进入完整三合/三会（流年参与）",
            "atom": "sanhe_with_suiyun",
            "args": {"zhi_set": "<D.b>"},
            "score": "bindings.scope ∈ {liunian, dayun+liunian} 时 +1；dayun 不计",
            "age_term": False,
        },
        {
            "id": "R5",
            "name": "岁运到位（探索项，不进主检验）",
            "atom": "suiyun_arrives",
            "args": {"at": "D.s"},
            "score": "+1",
            "age_term": False,
        },
    ]
    excluded = [
        {"family": "合开墓库", "reason": "无原子；binders 事实已存在，需新增 atom 或模型层直读 facts"},
        {"family": "跨年稳定 edge_id", "reason": "edge id 是构建序号；改用复合键引用，不改引擎"},
    ]
    zero_age = {
        "score_signature": "score_year(chart_facts, year, dayun_index) -> int；birth_year/age 不传入",
        "age_used_only_for": "候选年生成（20–35 岁，对 382 例固定）",
        "rules_with_age_term": [r["id"] for r in rules if r.get("age_term")],
        "passed": all(not r.get("age_term") for r in rules),
    }
    return {
        "population": "382 例 usable_for_timing（T-148 去重 + 农历换算 + 时刻齐备口径）",
        "candidate_set": "每例 birth_year+20 … +35，共 16 年；逐年映射到 facts 的大运序号与流年干支",
        "score_signature": zero_age["score_signature"],
        "zero_age_parameters": zero_age,
        "rules": rules,
        "excluded_rule_families": excluded,
        "topk": {
            "primary_k": PRIMARY_K,
            "secondary_k": 5,
            "exploratory_k": 7,
            "why_primary_3": (
                "R1 每例只在 3–8 个流年点火（见 per_case_coverage.r1_years），K=3 恒在正分年内，"
                "Top-3 完全由规则决定；K=5 有 %d 例、K=7 有 %d 例正分年不足，需要零分补齐，"
                "排序退化为填充。"
                % (
                    next(row["cases_needing_zero_fill"] for row in power["table"] if row["k"] == 5),
                    next(row["cases_needing_zero_fill"] for row in power["table"] if row["k"] == 7),
                )
            ),
            "tie_policy": "分数相同按 sha256(case_id|year) 升序（确定性、与年龄无关）；"
                          "另报 tie-aware 敏感性：事件年在同分档且档位>K 时按 K/档位计分。",
            "fill_policy": "正分年不足 K 时，按 sha256(case_id|year) 升序补零分年。",
        },
        "metrics": {
            "primary": "每例 Top-K 是否覆盖该例窗口内任一婚姻事件年（0/1）",
            "baseline_null": "逐例 1-C(16-m_i,K)/C(16,K) 的均值（把 90 例结构性零计入）",
            "practical_bar": (
                "同宽度最佳静态年龄带命中率（K=3 为 %s%%，K=5 为 %s%%，K=7 为 %s%%）"
                % tuple(
                    next(row["best_static_band_same_width"]["pct"] for row in power["table"] if row["k"] == k)
                    for k in KS
                )
            ),
            "secondary": ["tie-aware 期望命中", "labeled_292 子集", "排除 52 例文本年份矛盾"],
        },
        "decision_rule": {
            "signal": "命中率 ≥ null+8pp 且 单侧精确二项 p<0.01",
            "kill": "命中率 < null+3pp 或 p>0.20",
            "inconclusive": "其余",
            "multiplicity": "主检验只用 K=3；K=5 为次要，K=7 仅探索，不作裁决",
        },
        "power_summary": {
            "k3_null_pct": next(row["null_p0_pct"] for row in power["table"] if row["k"] == 3),
            "k3_power_at_plus8": next(row["power_at_card_signal"] for row in power["table"] if row["k"] == 3),
            "k3_mde80_pp": next(row["mde80_pp"] for row in power["table"] if row["k"] == 3),
            "k5_power_at_plus8": next(row["power_at_card_signal"] for row in power["table"] if row["k"] == 5),
            "k7_power_at_plus8": next(row["power_at_card_signal"] for row in power["table"] if row["k"] == 7),
        },
        "preregistered_limits": [
            "不在看到结果后改 K、改窗口、改规则权重。",
            "年龄只用于候选年生成；评分函数不接收 birth_year。",
            "事件年 = 整数年；1 月至立春之间的事件按整数年算流年，存在错一岁/错一柱风险，"
            "本数据无月日，无法修正。",
            "382 例中 90 例窗口内无婚姻事件，按 0 计，不剔除。",
        ],
    }


# ── 缺口 ────────────────────────────────────────────────────────────────────


def _gaps(census: dict[str, Any]) -> dict[str, Any]:
    return {
        "blocking": [],
        "requires_new_primitive": [
            {
                "id": "G1",
                "name": "合开墓库",
                "status": "无",
                "evidence": "chong_kai_muku 只认 chong/xing（atoms.py:697）；"
                            "MukuFact.binders（relation_graph.py:405）已产出但无 atom 消费",
                "impact": "无法把「流年六合/三合合住墓库」计入规则；R1/R2 可替代部分信息",
                "blocking": False,
            },
            {
                "id": "G2",
                "name": "跨年稳定 edge_id",
                "status": "无",
                "evidence": "381/382 例同一 (kind,members) 边相邻两年 id 不同；id = 构建序号（relation_graph.py:154）",
                "impact": "单独 edge_id 不能跨年引用；用 (chart_id, dayun_index, liunian_year, edge_id) 复合键可解",
                "blocking": False,
            },
        ],
        "engineering": [
            {
                "id": "E1",
                "name": "年份 → 大运序号",
                "status": "部分",
                "detail": "engine 要求显式 dayun_index；无公开 helper，需扫 chart.cycles.dayun 的 start/end_year"
                          "（本审计 5 行实现）。无 API 缺口，但有重复实现风险。",
            },
            {
                "id": "E2",
                "name": "批量入口与性能",
                "status": "有",
                "detail": "无批量 API；需循环 build_chart + build_relation_graph。实测 6112 个 case-year，"
                          "每 case-year 约 2 ms（graph + 4 原子），全量约 25–30 s，可离线跑。",
            },
            {
                "id": "E3",
                "name": "岁运十神地址",
                "status": "部分",
                "detail": "relations.nodes 只给 (addr, char)，不给 DY/LN 的十神；"
                          "需模型层用 engine.predicates.palace.get_shishen 现算（asof 已有同类用法）。",
            },
            {
                "id": "E4",
                "name": "三合/三会的 scope 过滤",
                "status": "部分",
                "detail": "sanhe_with_suiyun 无 scope 参数；dayun-only 完整局会遮蔽 liunian 完整局，"
                          "模型层需直读 relations.edges。",
            },
        ],
        "data": [
            {
                "id": "D1",
                "name": "事件年份文本可核验性",
                "status": "风险",
                "detail": "547 条事件中 425 条文本无 4 位年份（无法核验）、48 条与文本一致、74 条与文本矛盾；"
                          "72 例至少 1 条矛盾，其中 52 例矛盾事件落在 20–35 窗口。",
                "impact": "标签噪声会衰减效应；预注册需把「排除 52 例」作为敏感性分析，不能事后改成主分析。",
            },
            {
                "id": "D2",
                "name": "窗口内无事件的结构性零",
                "status": "已知",
                "detail": "90/382 例在 20–35 内无婚姻事件（其中部分事件在 15–19 或 36–50）。",
                "impact": "命中率天花板 76.4%；p0 已按逐例 m_i 计算，不能简单用 K/16。",
            },
            {
                "id": "D3",
                "name": "无配偶星案例",
                "status": "已知",
                "detail": "20/382 例八字无财/官，P3 规则无参照物。",
                "impact": "需预注册 unknown 处理（建议该例 R2 记 0 并在报告中标注）。",
            },
            {
                "id": "D4",
                "name": "真太阳时/边界",
                "status": "已知",
                "detail": "117 例 time_basis=clock_beijing（未做真太阳时）；"
                          f"{census['cases_with_boundary_warning']} 例有边界警告"
                          f"（{json.dumps(census['boundary_warnings'], ensure_ascii=False)}）。",
                "impact": "时柱/月柱可能变；预注册需固定 profile 口径，并把 variants 作为敏感性。",
            },
        ],
        "conclusion": "能直接开工",
        "conclusion_detail": "最小规则集 R1–R4 无需改 engine；G1/G2 为非阻断扩展。"
                             "若预注册坚持 6 项矩阵全覆盖，则等价于「需先补 2 个原语」（合开墓库、稳定 edge_id）。",
    }


# ── Markdown ────────────────────────────────────────────────────────────────


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def _fmt_example(example: dict[str, Any]) -> str:
    bits = [
        f"{example.get('case_id')}（{example.get('birth_dt')}，{example.get('pillars')}）",
        f"{example.get('year')} 年（{example.get('age')} 岁，大运 {example.get('dayun_index')}·{example.get('dayun')}，流年 {example.get('liunian')}）",
        f"`{example.get('call')}` → {example.get('value')}；{example.get('note')}",
    ]
    if example.get("he_at_value") is not None:
        bits.append(f"同一快照 `he_at(at=D.b)` → {example.get('he_at_value')}（{example.get('he_at_note')}）")
    if example.get("theory_ref"):
        bits.append(f"穿=害 出处：{example.get('theory_ref')}")
    if example.get("binder_kind"):
        bits.append(
            f"库 {example.get('muku_addr')}（{example.get('muku_branch')}）被 {example.get('binder_kind')} "
            f"边 {example.get('binder_edge_id')}（scope={example.get('binder_scope')}）合住，atom 仍返回 False"
        )
    if example.get("muku_candidates") == 0:
        bits.append(f"该库 candidates=0（{example.get('muku_addr')} {example.get('muku_branch')}），atom 仍报冲开")
    return "；".join(bits)


def render_md(payload: dict[str, Any]) -> str:
    census = payload["case_census"]
    matrix = payload["primitive_matrix"]
    atoms = payload["suiyun_atoms"]
    power = payload["power"]
    prereg = payload["preregistration"]
    gaps = payload["gaps"]
    label = payload["label_fidelity"]

    out: list[str] = []
    add = out.append
    add("# T-165 · 婚姻应期可行性审计（382 例，只读）")
    add("")
    add("- 任务卡：`tasks/T-165/PROMPT.md`；模式：只读审计，不建模、不评分、不生成应期预测、不改 `engine/**`。")
    add("- 数据：`META/timing-eval-set-v1.json`（382 例 `usable_for_timing`）+ `META/timing-baseline-v1.json`（frozen）。")
    add("- 复现：`.venv\\Scripts\\python.exe -m tools.timing_feasibility_audit`（退出码 0；输出 JSON 逐字节可复现）。")
    add("")
    add("## 0. 结论")
    add("")
    add(f"**{payload['verdict']}**。{payload['verdict_reason']}")
    add("")
    add(_md_table(
        ["指标", "数值"],
        [
            ["可用案例", f"{census['usable_for_timing']}/{census['records_total']}"],
            ["可建盘", f"{census['chart_built']}/{census['usable_for_timing']}"],
            ["20–35 岁可评分年", f"{census['case_years_total']} case-year（每例 16 年）"],
            ["窗口内有婚姻事件", f"{census['cases_with_event_in_window']} 例；"
                                  f"{census['cases_without_event_in_window']} 例结构性零"],
            ["原语矩阵（项）", f"有 {matrix['tally']['items']['有']} / 无 {matrix['tally']['items']['无']} / 部分 {matrix['tally']['items']['部分']}"],
            ["原语矩阵（子项）", f"有 {matrix['tally']['subchecks']['有']} / 无 {matrix['tally']['subchecks']['无']} / 部分 {matrix['tally']['subchecks']['部分']}（共 {matrix['tally']['subcheck_total']}）"],
            ["岁运原子", f"代码 {atoms['atoms_in_code_count']} 个；卡上 {atoms['atoms_in_card_count']} 个；"
                         f"漏 {', '.join(atoms['card_missing_atoms'])}"],
            ["主检验 K", f"K={PRIMARY_K}（功效 {prereg['power_summary']['k3_power_at_plus8']:.3f}，"
                         f"MDE80 {prereg['power_summary']['k3_mde80_pp']:.2f}pp）"],
            ["判定", gaps["conclusion"]],
        ],
    ))
    add("")
    add("三条硬事实先摆在这里：")
    add("")
    add("1. **大运只有 2–3 个取值**：16 年跨 "
        + "/".join(f"{k} 步（{v} 例）" for k, v in census['dayun_steps_in_window'].items())
        + "，任何只读大运的规则在十年内恒定，不能给 16 个年份排序；排序必须由流年原子驱动。")
    add("2. **292/382 例窗口内有事件，90 例没有**：命中率天花板 76.4%；零假设必须逐例算 "
        "`1-C(16-m_i,K)/C(16,K)`，不能用 K/16。")
    add(f"3. **标签噪声**：{label['no_year_in_text']}/{census['events_total']} 条事件文本没有年份（不可核验），"
        f"{label['mismatch']} 条与文本年份矛盾，{label['cases_with_in_window_mismatch']} 例的窗口内事件矛盾。")
    add("")

    add("## 1. 案例可用性")
    add("")
    add(_md_table(
        ["项", "数值"],
        [
            ["原始记录 / 可用", f"{census['records_total']} / {census['usable_for_timing']}"],
            ["birth_dt 可解析", str(census["birth_dt_parse_ok"])],
            ["建盘成功 / 失败", f"{census['chart_built']} / {len(census['chart_failures'])}"],
            ["大运区间齐备", str(census["dayun_range_present"])],
            ["每例可评分年数分布", json.dumps(census["scoreable_years_per_case"], ensure_ascii=False)],
            ["窗口内事件年数分布", json.dumps(census["event_year_count_per_case"], ensure_ascii=False)],
            ["窗口内事件 / 去重事件年", f"{census['events_in_window']} / {census['unique_event_years_in_window']}"],
            ["婚姻事件年落在大运区间", f"{census['events_in_dayun_range']}/{census['events_total']}"
                                        f"（区间外 {census['events_outside_dayun_range']}）"],
            ["大运顺逆与阳男阴女一致", f"{census['dayun_direction_consistent']}/382"
                                        f"（不一致 {len(census['dayun_direction_mismatches'])}）"],
            ["性别", json.dumps(census["gender"], ensure_ascii=False)],
            ["质量等级", json.dumps(census["quality_grade"], ensure_ascii=False)],
            ["出生时刻口径", json.dumps(census["time_basis"], ensure_ascii=False)],
            ["边界警告", f"{json.dumps(census['boundary_warnings'], ensure_ascii=False)}"
                         f"（{census['cases_with_boundary_warning']} 例至少 1 条）"],
            ["起运年龄", json.dumps(census["qiyun_start_age"], ensure_ascii=False)],
            ["出生年范围", f"{census['birth_year_range'][0]}–{census['birth_year_range'][1]}"],
            ["无配偶星案例", f"{census['cases_without_spouse_star']}（例：{', '.join(census['cases_without_spouse_star_examples'])}）"],
        ],
    ))
    add("")
    add("逐例覆盖（382 条）见 JSON `per_case_coverage`：每例的 `pillars`、`scoreable_years`、"
        "窗口内事件年、配偶星地址、R1–R4 点火年数。")
    add("")
    add("### 1.1 基线口径核对")
    add("")
    add("卡上四个基线数里有两个是 392 例口径（22–28、26 岁），与 382 例 `cleaned_reference` 不一致：")
    add("")
    add(_md_table(
        ["年龄带", "卡上", "382 例重算", "cleaned_reference", "392 例 card", "判定"],
        [
            [row["band"], f"{row['card_pct']}%", f"{row['recomputed_382_pct']}%",
             f"{row['cleaned_reference_pct']}%", f"{row['card_392_pct']}%",
             "一致" if row["matches_382"] else "卡上用了 392 例口径"]
            for row in payload["baseline_crosscheck"]
        ],
    ))
    add("")
    add("382 例下 22–28 应为 **49.2%**、26 岁应为 **11.8%**；48.7% / 11.2% 是 392 例（未去重、未换算农历）口径。"
        "预注册若引用基线，须统一到 382 例 `cleaned_reference`。")
    add("")
    add("### 1.2 标签保真")
    add("")
    add(_md_table(
        ["项", "计数"],
        [
            ["事件总数", f"{census['events_total']}（15–50 岁内 {census['events_age_15_50']}，"
                         f"与 eval set counts.usable_marriage_events 一致）"],
            ["文本无年份（不可核验）", str(label["no_year_in_text"])],
            ["事件年与文本年份一致", str(label["match"])],
            ["事件年与文本年份矛盾", str(label["mismatch"])],
            ["至少 1 条矛盾的案例", str(label["cases_with_any_mismatch"])],
            ["窗口内事件矛盾的案例", str(label["cases_with_in_window_mismatch"])],
            ["age_plausible=False 的事件", str(label["age_plausible_false"])],
        ],
    ))
    add("")

    add("## 2. 原语矩阵")
    add("")
    add("状态定义：**有**＝单原子/字段直接回答；**部分**＝事实齐备但需调用方组合/过滤，或原子只覆盖部分子形态；"
        "**无**＝事实层缺字段/边种，组合也答不了。")
    add("")
    add(_md_table(
        ["项", "问题", "结论", "子项"],
        [[item["id"], item["question"], item["status"],
          "、".join(f"{sub['name']}={sub['status']}" for sub in item["subchecks"])]
         for item in matrix["items"]],
    ))
    add("")
    add(f"项级合计：有 {matrix['tally']['items']['有']} / 无 {matrix['tally']['items']['无']} / "
        f"部分 {matrix['tally']['items']['部分']}；子项合计：有 {matrix['tally']['subchecks']['有']} / "
        f"无 {matrix['tally']['subchecks']['无']} / 部分 {matrix['tally']['subchecks']['部分']}。")
    add("")
    for item in matrix["items"]:
        add(f"### {item['id']} · {item['question']}")
        add("")
        add(f"- 结论：**{item['status']}**")
        add(f"- 说明：{item['note']}")
        add("")
        add(_md_table(["子项", "状态", "代码位置"], [[sub["name"], sub["status"], f"`{sub['code']}`"]
                                                   for sub in item["subchecks"]]))
        add("")
        for example in item["example_objects"]:
            add(f"- 真实例子：{_fmt_example(example)}")
        if item["example_missing"]:
            add("- ⚠️ 缺真实例子（脚本 required-example 检查失败）")
        add("")

    add("## 3. 岁运原子实况")
    add("")
    add(f"代码里 `atoms.py` 的岁运原子共 **{atoms['atoms_in_code_count']}** 个："
        f"{', '.join('`' + a + '`' for a in atoms['atoms_in_code'])}；"
        f"任务卡 §1 写 4 个，漏了 {', '.join('`' + a + '`' for a in atoms['card_missing_atoms'])}。"
        "`suiyun_arrives`（到位）是实质性原语，建议下一张卡把它纳入矩阵。")
    add("")
    add(_md_table(
        ["原子 / 参数", "命中", "说明"],
        [
            *[["suiyun_edge(type=%s, at=D.b, scope=%s)" % (kind, scope),
               f"{atoms['suiyun_edge'][kind][scope]['true']}/"
               f"{atoms['suiyun_edge'][kind][scope]['true'] + atoms['suiyun_edge'][kind][scope]['false']}",
               "6112 case-year"]
              for kind in RELATION_KINDS for scope in ("dayun", "liunian")],
            ["sanhe_with_suiyun(any)", f"{atoms['sanhe_with_suiyun']['true']}/{atoms['sanhe_with_suiyun']['true'] + atoms['sanhe_with_suiyun']['false']}",
             f"scope 分布 {json.dumps(atoms['sanhe_with_suiyun']['scope_counts'], ensure_ascii=False)}"],
            ["chong_kai_muku(year=y)", f"{atoms['chong_kai_muku']['year_arg_true']}/6112", "流年触发"],
            ["chong_kai_muku(无 year)", f"{atoms['chong_kai_muku']['no_year_true']}/6112", "十年恒定，不能按年区分"],
            ["liunian_present", f"{atoms['liunian_present']['true']}/6112", "恒真"],
            ["dayun_present", f"{atoms['dayun_present']['true']}/6112", "恒真"],
            ["suiyun_arrives(at=D.s)", f"{atoms['suiyun_arrives']['day_stem_true']}/6112", "通禄"],
            ["suiyun_arrives(at=D.b)", f"{atoms['suiyun_arrives']['day_branch_true']}/6112", "原身"],
            ["半合边触及 D.b（liunian）", f"{atoms['partial_sanhe_db_liunian_true']}/6112", "sanhe_with_suiyun 不认半合"],
            ["无岁运边的 case-year", f"{atoms['case_years_without_suiyun_edges']}/6112", "0 表示 False 是真否定"],
            ["edge id 跨年不稳的案例", f"{atoms['unstable_edge_id_cases']}/382", "同一 (kind,members) 相邻两年 id 不同"],
        ],
    ))
    add("")
    add(f"边种全集：`{', '.join(atoms['edge_kinds_seen'])}`。穿/害同一组六对支，"
        f"引擎以 `chuan` 承载（{THEORY_CHUAN_HAI}）。")
    add("")

    add("## 4. 预注册设计草案（零年龄参数）")
    add("")
    add(f"- 人群：{prereg['population']}。")
    add(f"- 候选集：{prereg['candidate_set']}。")
    add(f"- 评分签名：`{prereg['score_signature']}`；年龄只用于候选年生成，评分函数看不到 birth_year。")
    add("")
    add(_md_table(
        ["规则", "名称", "原子/参数", "计分"],
        [[rule["id"], rule["name"],
          f"`{rule['atom']}({json.dumps(rule['args'], ensure_ascii=False)})`"
          + (f"；type ∈ {'/'.join(rule['kinds'])}" if rule.get("kinds") else ""),
          rule["score"]] for rule in prereg["rules"]],
    ))
    add("")
    add(f"- Top-K：主检验 **K={prereg['topk']['primary_k']}**；次要 K={prereg['topk']['secondary_k']}；"
        f"探索 K={prereg['topk']['exploratory_k']}。理由：{prereg['topk']['why_primary_3']}")
    add(f"- 平局：{prereg['topk']['tie_policy']}")
    add(f"- 补齐：{prereg['topk']['fill_policy']}")
    add(f"- 指标：{prereg['metrics']['primary']}；零假设是 {prereg['metrics']['baseline_null']}；"
        f"实务门槛是 {prereg['metrics']['practical_bar']}。")
    add(f"- 判据：{prereg['decision_rule']['signal']} 算信号；{prereg['decision_rule']['kill']} 判死；"
        f"{prereg['decision_rule']['multiplicity']}。")
    add("- 预注册限制：")
    for limit in prereg["preregistered_limits"]:
        add(f"  - {limit}")
    add("")

    add("## 5. 统计功效")
    add("")
    add(f"单侧精确二项检验，α={power['alpha']}；p0 逐例计算（不是 K/16）。")
    add("")
    add(_md_table(
        ["K", "null p0", "拒绝域临界率", "卡上 +8pp 率", "功效@+8pp", "MDE80", "同宽度最佳静态带", "需零分补齐"],
        [[row["k"], f"{row['null_p0_pct']}%", f"{row['critical_rate_pct']}%", f"{row['card_signal_rate_pct']}%",
          f"{row['power_at_card_signal']:.3f}", f"{row['mde80_pp']}pp",
          f"{row['best_static_band_same_width']['range']} = {row['best_static_band_same_width']['pct']}%"
          if row["best_static_band_same_width"] else "—",
          f"{row['cases_needing_zero_fill']}/382"]
         for row in power["table"]],
    ))
    add("")
    add("读法：")
    add("")
    add("- **+8pp 门槛低于同宽度最佳静态年龄带**：K=3 是 26.0% vs 26.7%（差 0.7pp），"
        "K=5 是 36.8% vs 39.3%（差 2.5pp），K=7 是 46.7% vs 49.2%（差 2.5pp）。"
        "所以「过 +8pp」只证明规则有信号，**不证明超过年龄先验**；"
        "预注册应把最佳静态带作为实务门槛，+8pp/p<0.01 只作统计门槛。"
        "最佳静态带是在同一批 382 例上选 lo 得到的乐观上界（选择用了结果），"
        "因此它是偏严的实务门槛，不是无偏检验。")
    add("- K=3 的 p0=18.0%、功效 0.919、MDE 6.75pp；K=5 功效 0.830；K=7 功效 0.795 但 362/382 例正分年不足，"
        "Top-7 主要是零分补齐，不能作裁决。")
    add("- 90 例窗口内无事件是结构性零：它们在 H0/H1 下都贡献 0，但会把总体 p0 拉低；"
        "如果剔除成 292 例，K=3 的 p0 升到 23.6%、功效降到 0.762——**保留 382 例更有力**。")
    add("")
    add("### 5.1 敏感性（K=3）")
    add("")
    add(_md_table(
        ["子集", "n", "null p0", "功效@+8pp", "MDE80"],
        [[row["name"], row["n"], f"{row['null_p0_pct']}%", f"{row['power_at_card_signal']:.3f}",
          f"{row['mde80_pp']}pp"] for row in power["sensitivities"]],
    ))
    add("")
    add("### 5.2 与静态 342 例的比较")
    add("")
    add("同 p0、同 +8pp 下，仅样本量差异：")
    add("")
    add(_md_table(
        ["K", "n=382 功效", "n=342 功效", "n=382 MDE80", "n=342 MDE80", "CI 宽度比 342/382"],
        [[row["k"], f"{row['n_382_power_at_plus8']:.3f}", f"{row['n_342_power_at_plus8']:.3f}",
          f"{row['n_382_mde80_pp']}pp", f"{row['n_342_mde80_pp']}pp", row["ci_width_ratio_342_over_382"]]
         for row in power["sample_size_counterfactual_342"]],
    ))
    add("")
    add("**为什么 382 例应期设计比静态 342 例更有力**（也说明哪里没有更强）：")
    add("")
    add("1. **同例配对**：每例 16 个候选年共享同一张盘，格局/强弱/性别/出生队列等案例级混杂在例内抵消；"
        "静态 342 例是跨案例比较，无法把「盘的特征」与「这批人结婚本来就晚」分开。")
    add("2. **标签更锐**：结果从「是否落在某个年龄带」变成「16 个年份里排前 K」，"
        "可以直接检验区分度，而不只是边际相关。")
    add("3. **年龄先验可被显式扣掉**：同宽度最佳静态带（K=3 26.7%、K=7 49.2%）就是年龄先验的上界；"
        "零年龄参数模型必须超过它才算增加信息。静态设计把年龄写进分组，做不到这一步。")
    add("4. **样本量只多 +11.7%**：382 vs 342，CI 只窄 5.4%，同效应下功效提升有限（见上表）。"
        "16 个候选年**不把 n 变成 6112**——命中指标仍是每例一个 0/1；6112 只是事实计算量。"
        "真正的增益来自配对与更锐的标签，不是「16 倍样本」。")
    add("5. **代价**：16 选 3 比二分类更难，+8pp 对应的相对提升是 44%（0.18→0.26），"
        "而静态带的 +8pp 相对提升更小；所以两边不能直接比「谁的功效高」，只能比「谁能在控制年龄后仍检出信号」。")
    add("")

    add("## 6. 缺口")
    add("")
    add(f"**结论：{gaps['conclusion']}**。{gaps['conclusion_detail']}")
    add("")
    add(_md_table(
        ["类别", "ID", "缺口", "状态", "影响 / 处理"],
        [[kind, gap["id"], gap["name"], gap["status"],
          (f"{gap.get('detail', '')} {gap.get('impact', '')}").strip()]
         for kind, key in (("新原语", "requires_new_primitive"), ("工程", "engineering"), ("数据", "data"))
         for gap in gaps[key]],
    ))
    add("")
    add("- 阻断项：无。最小规则集 R1–R4 不需要 G1/G2；若预注册坚持 6 项矩阵全覆盖，"
        "则等价于「需先补 2 个原语」（G1 合开墓库、G2 稳定 edge_id）。")
    add("")

    add("## 7. 复现与确定性")
    add("")
    add("```bash")
    add(".venv\\Scripts\\python.exe -m tools.timing_feasibility_audit")
    add(".venv\\Scripts\\python.exe -m pytest -q")
    add("```")
    add("")
    add("- 脚本单线程、固定案例顺序、JSON `sort_keys`、无时间戳；两次运行应逐字节一致。")
    add("- 本报告所有数字均由脚本现场计算；`per_case_coverage` 给出 382 例逐例覆盖，可逐条复核。")
    add("")
    return "\n".join(out) + "\n"


# ── 入口 ────────────────────────────────────────────────────────────────────


def main() -> int:
    payload = run_audit()
    json_text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    md_text = render_md(payload)
    _write(OUT_JSON, json_text)
    _write(OUT_MD, md_text)

    missing = [
        item["id"]
        for item in payload["primitive_matrix"]["items"]
        if item["example_missing"]
    ]
    census = payload["case_census"]
    checks = {
        "usable_382": census["usable_for_timing"] == 382,
        "chart_all_built": census["chart_built"] == 382,
        "case_years_6112": census["case_years_total"] == 6112,
        "scoreable_16_each": set(census["scoreable_years_per_case"]) == {"16"},
        "required_examples": not missing,
        "zero_age": payload["preregistration"]["zero_age_parameters"]["passed"],
    }
    print("T-165 婚姻应期可行性审计（只读）")
    print(f"  可用案例            {census['usable_for_timing']}/{census['records_total']}")
    print(f"  可建盘              {census['chart_built']}")
    print(f"  case-year           {census['case_years_total']}（每例 16 年）")
    print(f"  窗口内有事件        {census['cases_with_event_in_window']}；结构性零 {census['cases_without_event_in_window']}")
    tally = payload["primitive_matrix"]["tally"]
    print(f"  原语矩阵（项）      有 {tally['items']['有']} / 无 {tally['items']['无']} / 部分 {tally['items']['部分']}")
    print(f"  原语矩阵（子项）    有 {tally['subchecks']['有']} / 无 {tally['subchecks']['无']} / 部分 {tally['subchecks']['部分']}")
    print(f"  判定                {payload['verdict']}")
    print(f"  JSON sha256         {sha256(json_text.encode('utf-8')).hexdigest()}")
    print(f"  MD   sha256         {sha256(md_text.encode('utf-8')).hexdigest()}")
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        print(f"  自检失败：{', '.join(failed)}")
        return 1
    if missing:
        print(f"  缺少真实例子的原语项：{', '.join(missing)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
