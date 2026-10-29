"""tools/timing_eval_v1.py · 婚姻应期评测器 v1（T-167）

只消费「分数 JSON（T-166 产物）」与「评测集事件年份」，算 Top-K 命中、逐例零假设、
精确 Poisson-binomial p、同 K 静态基线、Wilson 下界与预注册判定；不读模型源码、
不改模型/规则/阈值。

口径（tasks/T-167/PROMPT.md §1，卡内固定）：
- 候选年：20–35 岁共 16 年；主检验 K=3。
- 事件年 E：婚姻事件年份落在 20–35 的去重年份；e=|E|；Top-3 中任一年 ∈ E 即命中。
- 逐例零假设：模型选定的 3 年固定，把 e 个事件年随机放进 16 年，
  p_case = 1 - C(16-e,3)/C(16,3)；e=0 → 0（结构性零）。
- 聚合：observed=Σhit，expected=Σp_case，精确 Poisson-binomial 单侧 p（标准库 DP）。
- 同 K 静态基线：枚举 3 个连续年龄窗口（20–22 … 33–35），取命中率最高者（并列取 lo 小）。
  7 年窗口 24–30 的 45.3% 只作参考，不作 Top-3 基线。
- 判定：信号 = 差值 ≥ +8pp 且 p < 0.01；实用门 = Wilson 95% 下界 > 同 K 静态基线；
  判死 = 差值 < +3pp 或 p > 0.20；其余为中间态，不宣布有效。

用法：
    python -m tools.timing_eval_v1 --scores META/timing-scores-v1.json \
        --eval-set META/timing-eval-set-v1.json [--json]

退出码：0 已生成报告；2 输入缺失/字段不符（不抛堆栈）。
确定性：排序键 sha256(case_id|year)；无随机数、无时间戳；同输入两次运行逐字节一致。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from statistics import NormalDist
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_PREFIX = ROOT / "META" / "timing-k3-report-v1"
AUDIT_FILENAME = "timing-feasibility-audit-v1.json"
CONTRADICTED_FILENAME = "timing-event-year-audit-v1.json"

SCHEMA = "timing-k3-report/v1"
TASK = "T-167"
AGE_MIN, AGE_MAX = 20, 35
CANDIDATE_YEARS = AGE_MAX - AGE_MIN + 1  # 16
K = 3
ALPHA = 0.01
SIGNAL_PP = 8.0
KILL_PP = 3.0
KILL_P = 0.20
REFERENCE_STATIC_PCT = 26.7  # T-165 复算值，仅供对账，不参与判定
Z_95 = NormalDist().inv_cdf(0.975)


class InputError(ValueError):
    """输入文件或字段不符合协议；CLI 以退出码 2 结束。"""


# ── I/O ─────────────────────────────────────────────────────────────────────


def _load_json(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise InputError(f"文件不存在：{path}") from exc
    except OSError as exc:
        raise InputError(f"无法读取文件：{path}（{exc}）") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise InputError(f"JSON 解析失败：{path}（第 {exc.lineno} 行）") from exc


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


# ── 输入解析与校验 ──────────────────────────────────────────────────────────


def parse_eval_set(payload: Any) -> list[dict[str, Any]]:
    """取 usable_for_timing=true 的案例，并算好窗口内去重事件年。"""
    if not isinstance(payload, dict):
        raise InputError("评测集顶层必须是 JSON 对象")
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list):
        raise InputError("评测集缺少 cases 列表")

    cases: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_cases:
        if not isinstance(raw, dict):
            raise InputError("评测集 cases[] 必须是 JSON 对象")
        if raw.get("usable_for_timing") is not True:
            continue
        case_id = raw.get("case_id")
        birth_year = raw.get("birth_year")
        if not isinstance(case_id, str) or not case_id:
            raise InputError("评测集存在缺 case_id 的可用案例")
        if case_id in seen:
            raise InputError(f"评测集 case_id 重复：{case_id}")
        if not _is_int(birth_year):
            raise InputError(f"评测集 {case_id} 的 birth_year 不是整数")
        seen.add(case_id)

        years: set[int] = set()
        for event in raw.get("marriage_events") or []:
            if not isinstance(event, dict):
                continue
            year = event.get("year")
            if _is_int(year) and AGE_MIN <= year - birth_year <= AGE_MAX:
                years.add(year)
        cases.append(
            {
                "case_id": case_id,
                "birth_year": birth_year,
                "gender": str(raw.get("gender") or ""),
                "time_basis": str(raw.get("time_basis") or ""),
                "event_years": sorted(years),
                "event_year_set": frozenset(years),
            }
        )

    if not cases:
        raise InputError("评测集没有 usable_for_timing=true 的案例")
    return sorted(cases, key=lambda case: case["case_id"])


def parse_scores(
    payload: Any,
) -> tuple[dict[str, dict[int, int]], dict[str, int], dict[str, Any]]:
    """分数文件 → ({case_id: {year: score}}, {case_id: birth_year}, 元信息)。"""
    if not isinstance(payload, dict):
        raise InputError("分数文件顶层必须是 JSON 对象")
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise InputError("分数文件缺少非空 cases 列表")

    scores: dict[str, dict[int, int]] = {}
    birth_years: dict[str, int] = {}
    for raw in raw_cases:
        if not isinstance(raw, dict):
            raise InputError("分数文件 cases[] 必须是 JSON 对象")
        case_id = raw.get("case_id")
        years = raw.get("years")
        if not isinstance(case_id, str) or not case_id:
            raise InputError("分数文件存在缺 case_id 的案例")
        if case_id in scores:
            raise InputError(f"分数文件 case_id 重复：{case_id}")
        if not isinstance(years, list) or not years:
            raise InputError(f"分数文件 {case_id} 缺少 years 列表")
        if "birth_year" in raw:
            if not _is_int(raw.get("birth_year")):
                raise InputError(f"分数文件 {case_id} 的 birth_year 不是整数")
            birth_years[case_id] = raw["birth_year"]
        mapping: dict[int, int] = {}
        for item in years:
            if not isinstance(item, dict):
                raise InputError(f"分数文件 {case_id}.years[] 必须是 JSON 对象")
            year = item.get("year")
            score = item.get("score")
            if not _is_int(year):
                raise InputError(f"分数文件 {case_id} 存在非整数 year")
            if not _is_int(score):
                raise InputError(f"分数文件 {case_id}/{year} 的 score 不是整数")
            if year in mapping:
                raise InputError(f"分数文件 {case_id} 年份重复：{year}")
            mapping[year] = score
        scores[case_id] = mapping

    meta = {key: payload.get(key) for key in ("protocol_id", "frozen_at", "git_head", "population")}
    return scores, birth_years, meta


def validate_coverage(
    eval_cases: Sequence[dict[str, Any]],
    scores: dict[str, dict[int, int]],
    birth_years: dict[str, int] | None = None,
) -> None:
    """分数必须与评测集一一对应，且每例覆盖 20–35 岁共 16 个候选年。"""
    expected_ids = {case["case_id"] for case in eval_cases}
    missing = sorted(expected_ids - set(scores))
    extra = sorted(set(scores) - expected_ids)
    if missing or extra:
        raise InputError(
            "分数案例集与评测集不一致："
            f"缺 {len(missing)} 例 {missing[:3]}，多 {len(extra)} 例 {extra[:3]}"
        )
    for case in eval_cases:
        case_id = case["case_id"]
        if birth_years and case_id in birth_years and birth_years[case_id] != case["birth_year"]:
            raise InputError(
                f"{case_id} 出生年不一致：分数 {birth_years[case_id]} vs 评测集 {case['birth_year']}"
            )
        want = {case["birth_year"] + age for age in range(AGE_MIN, AGE_MAX + 1)}
        got = set(scores[case_id])
        if want != got:
            missing_years = sorted(want - got)
            extra_years = sorted(got - want)
            raise InputError(
                f"{case_id} 候选年覆盖不符（必须恰为 20–35 岁 16 年）："
                f"缺 {missing_years[:4]}，多 {extra_years[:4]}"
            )


def load_contradicted(payload: Any) -> list[str]:
    """T-168 矛盾名单。

    兼容三种形状：顶层 case_id 列表；``{"sensitivity_exclude": [...]}``；
    ``{"sensitivity": {"sensitivity_exclude": [...]}}``（T-168 v1 实际产物）。
    """
    if isinstance(payload, list):
        raw = payload
    elif isinstance(payload, dict):
        raw = payload.get("sensitivity_exclude")
        if raw is None and isinstance(payload.get("sensitivity"), dict):
            raw = payload["sensitivity"].get("sensitivity_exclude")
    else:
        raise InputError("矛盾名单必须是 case_id 列表，或含 sensitivity_exclude 的对象")
    if not isinstance(raw, list):
        raise InputError("矛盾名单缺少 sensitivity_exclude 列表（顶层或 sensitivity 内）")

    case_ids: list[str] = []
    for item in raw:
        if isinstance(item, str) and item:
            case_ids.append(item)
        elif isinstance(item, dict) and isinstance(item.get("case_id"), str):
            case_ids.append(item["case_id"])
        else:
            raise InputError("矛盾名单元素必须是 case_id 字符串或含 case_id 的对象")
    return sorted(set(case_ids))


def load_boundary_cases(payload: Any) -> set[str]:
    """T-165 审计 per_case_coverage → 有边界警告的 case_id。"""
    if not isinstance(payload, dict):
        raise InputError("审计文件顶层必须是 JSON 对象")
    coverage = payload.get("per_case_coverage")
    if not isinstance(coverage, list):
        raise InputError("审计文件缺少 per_case_coverage 列表")
    flagged: set[str] = set()
    for row in coverage:
        if not isinstance(row, dict):
            raise InputError("审计文件 per_case_coverage[] 必须是 JSON 对象")
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise InputError("审计文件 per_case_coverage[] 缺 case_id")
        if row.get("boundary_warnings"):
            flagged.add(case_id)
    return flagged


# ── 统计核心 ────────────────────────────────────────────────────────────────


def sha_rank(case_id: str, year: int) -> str:
    """并列时唯一确定的排序键（卡上口径：sha256(case_id|year) 升序）。"""
    return hashlib.sha256(f"{case_id}|{year}".encode("utf-8")).hexdigest()


def rank_top(case_id: str, year_scores: dict[int, int], k: int = K) -> list[tuple[int, int]]:
    """按 (-score, sha256(case_id|year) 升序) 取 Top-K。"""
    ordered = sorted(year_scores.items(), key=lambda item: (-item[1], sha_rank(case_id, item[0])))
    return ordered[:k]


def p_case_for(e: int, k: int = K, candidate_years: int = CANDIDATE_YEARS) -> float:
    """事件置换零假设：p_case = 1 - C(n-e,k)/C(n,k)；e=0 → 0。"""
    if e <= 0:
        return 0.0
    if candidate_years - e < k:
        return 1.0
    return 1.0 - math.comb(candidate_years - e, k) / math.comb(candidate_years, k)


def poisson_binomial_tail(probabilities: Iterable[float], observed: int) -> float:
    """P(X >= observed)，X ~ Σ Bernoulli(p_i) 独立；标准库 DP 精确卷积。"""
    probs = list(probabilities)
    if observed <= 0:
        return 1.0
    if observed > len(probs):
        return 0.0
    pmf = [1.0]
    for p in probs:
        q = 1.0 - p
        nxt = [0.0] * (len(pmf) + 1)
        for index, value in enumerate(pmf):
            nxt[index] += value * q
            nxt[index + 1] += value * p
        pmf = nxt
    tail = math.fsum(pmf[observed:])
    return min(1.0, max(0.0, tail))


def wilson_interval(hits: int, n: int, z: float = Z_95) -> tuple[float, float]:
    """二项比例的 Wilson 区间（95%）。"""
    if n <= 0:
        return 0.0, 1.0
    p = hits / n
    denominator = 1.0 + z * z / n
    centre = p + z * z / (2.0 * n)
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
    low = (centre - half) / denominator
    high = (centre + half) / denominator
    # 端点解析为 0 / 1，避免浮点残差（hits=0 时下界必为 0，hits=n 时上界必为 1）。
    if hits == 0:
        low = 0.0
    if hits == n:
        high = 1.0
    return min(1.0, max(0.0, low)), min(1.0, max(0.0, high))


def static_baseline(cases: Sequence[dict[str, Any]], width: int = K) -> dict[str, Any]:
    """枚举宽 K 的连续年龄窗口（20–22 … 33–35），命中=该例任一事件年落在窗口内。"""
    n = len(cases)
    table: list[dict[str, Any]] = []
    for lo in range(AGE_MIN, AGE_MAX - width + 2):
        hi = lo + width - 1
        hits = sum(
            1
            for case in cases
            if any(lo <= year - case["birth_year"] <= hi for year in case["event_years"])
        )
        table.append(
            {
                "lo": lo,
                "hi": hi,
                "hits": hits,
                "rate": hits / n if n else 0.0,
                "rate_pct": round(100.0 * hits / n, 2) if n else 0.0,
            }
        )
    best = min(table, key=lambda row: (-row["hits"], row["lo"]))
    return {
        "k": width,
        "n": n,
        "best": dict(best),
        "table": table,
    }


def classify(
    *,
    n: int,
    observed: int,
    expected: float,
    p_value: float,
    wilson_low: float,
    baseline_rate: float,
) -> dict[str, Any]:
    """预注册判定；阈值是模块常量，不看结果动态调整。"""
    observed_rate = observed / n if n else 0.0
    expected_rate = expected / n if n else 0.0
    # 用「百分比之差」直接算，避免 100*(a-b) 在 8pp/3pp 边界上的浮点毛刺。
    diff_pp = 100.0 * observed / n - 100.0 * expected / n if n else 0.0
    signal_pp_ok = diff_pp >= SIGNAL_PP
    signal_p_ok = p_value < ALPHA
    signal = signal_pp_ok and signal_p_ok
    practical = wilson_low > baseline_rate
    kill = diff_pp < KILL_PP or p_value > KILL_P
    if signal and practical:
        verdict = "signal_above_static_baseline"
    elif signal:
        verdict = "signal_below_static_baseline"
    elif kill:
        verdict = "dead"
    else:
        verdict = "inconclusive"
    return {
        "observed_rate": observed_rate,
        "expected_rate": expected_rate,
        "diff_pp": diff_pp,
        "signal_effect_ok": signal_pp_ok,
        "signal_p_ok": signal_p_ok,
        "signal": signal,
        "practical_gate": practical,
        "kill": kill,
        "verdict": verdict,
    }


def evaluate_population(
    name: str,
    description: str,
    cases: Sequence[dict[str, Any]],
    tops: dict[str, list[tuple[int, int]]],
    *,
    is_main: bool = False,
) -> dict[str, Any]:
    """一个口径的 observed/expected/精确 p/Wilson/同 K 静态基线/判定。"""
    if not cases:
        return {
            "name": name,
            "description": description,
            "is_main": is_main,
            "status": "empty",
            "n": 0,
        }

    hits: list[int] = []
    p_values: list[float] = []
    for case in cases:
        top_years = {year for year, _ in tops[case["case_id"]]}
        hits.append(1 if top_years & case["event_year_set"] else 0)
        p_values.append(p_case_for(len(case["event_years"])))

    n = len(cases)
    observed = sum(hits)
    expected = math.fsum(p_values)
    p_value = poisson_binomial_tail(p_values, observed)
    wilson_low, wilson_high = wilson_interval(observed, n)
    baseline = static_baseline(cases)
    gates = classify(
        n=n,
        observed=observed,
        expected=expected,
        p_value=p_value,
        wilson_low=wilson_low,
        baseline_rate=baseline["best"]["rate"],
    )

    return {
        "name": name,
        "description": description,
        "is_main": is_main,
        "status": "ok",
        "n": n,
        "e_zero_cases": sum(1 for case in cases if not case["event_years"]),
        "observed": observed,
        "expected": expected,
        "p_value": p_value,
        "wilson_low": wilson_low,
        "wilson_high": wilson_high,
        "static_baseline": {
            "window": [baseline["best"]["lo"], baseline["best"]["hi"]],
            "hits": baseline["best"]["hits"],
            "rate": baseline["best"]["rate"],
            "rate_pct": baseline["best"]["rate_pct"],
        },
        "gates": gates,
        "case_ids_sha256": _case_ids_digest(cases),
        "case_ids": [case["case_id"] for case in cases],
    }


def _case_ids_digest(cases: Sequence[dict[str, Any]]) -> str:
    joined = "\n".join(sorted(case["case_id"] for case in cases))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


# ── 报告组装 ────────────────────────────────────────────────────────────────


def build_report(
    *,
    eval_payload: Any,
    scores_payload: Any,
    eval_path: str,
    scores_path: str,
    contradicted: tuple[str, Any] | None,
    audit: tuple[str, Any] | None,
) -> dict[str, Any]:
    eval_cases = parse_eval_set(eval_payload)
    scores, birth_years, scores_meta = parse_scores(scores_payload)
    validate_coverage(eval_cases, scores, birth_years)

    tops = {case["case_id"]: rank_top(case["case_id"], scores[case["case_id"]]) for case in eval_cases}
    by_id = {case["case_id"]: case for case in eval_cases}

    contradicted_ids: list[str] | None = None
    if contradicted is not None:
        contradicted_ids = load_contradicted(contradicted[1])
    boundary_ids: set[str] | None = None
    if audit is not None:
        boundary_ids = load_boundary_cases(audit[1])

    populations: list[dict[str, Any]] = [
        evaluate_population("all", "全部可用案例（主口径）", eval_cases, tops, is_main=True),
        evaluate_population(
            "labeled",
            "剔除结构性零（e=0）",
            [case for case in eval_cases if case["event_years"]],
            tops,
        ),
    ]

    if contradicted_ids is None:
        populations.append(
            {
                "name": "exclude_contradicted",
                "description": "剔除 T-168 年份矛盾例",
                "status": "unavailable",
                "reason": "未提供 T-168 审计名单（--contradicted 或 META/timing-event-year-audit-v1.json）",
            }
        )
    else:
        drop = set(contradicted_ids)
        missing = sorted(drop - set(by_id))
        populations.append(
            evaluate_population(
                "exclude_contradicted",
                "剔除 T-168 年份矛盾例",
                [case for case in eval_cases if case["case_id"] not in drop],
                tops,
            )
        )
        populations[-1]["excluded"] = len(drop & set(by_id))
        populations[-1]["excluded_unknown_case_ids"] = missing

    populations.append(
        evaluate_population(
            "exclude_clock_beijing",
            "剔除 time_basis=clock_beijing",
            [case for case in eval_cases if case["time_basis"] != "clock_beijing"],
            tops,
        )
    )

    if boundary_ids is None:
        populations.append(
            {
                "name": "exclude_boundary_warnings",
                "description": "剔除有边界警告的案例",
                "status": "unavailable",
                "reason": "未提供 T-165 审计（--audit 或 META/timing-feasibility-audit-v1.json）",
            }
        )
    else:
        drop = boundary_ids & set(by_id)
        populations.append(
            evaluate_population(
                "exclude_boundary_warnings",
                "剔除有边界警告的案例",
                [case for case in eval_cases if case["case_id"] not in drop],
                tops,
            )
        )
        populations[-1]["excluded"] = len(drop)

    populations.append(
        evaluate_population(
            "male",
            "性别=男",
            [case for case in eval_cases if case["gender"] == "男"],
            tops,
        )
    )
    populations.append(
        evaluate_population(
            "female",
            "性别=女",
            [case for case in eval_cases if case["gender"] == "女"],
            tops,
        )
    )

    for population in populations[1:]:
        if population.get("status") == "ok" and population["name"].startswith("exclude_"):
            population.setdefault("excluded", len(eval_cases) - population["n"])

    main = populations[0]
    static_all = static_baseline(eval_cases)

    inputs: dict[str, Any] = {
        "eval_set": {
            "path": eval_path,
            "usable_cases": len(eval_cases),
        },
        "scores": {
            "path": scores_path,
            "cases": len(scores),
            "protocol_id": scores_meta.get("protocol_id"),
            "frozen_at": scores_meta.get("frozen_at"),
            "git_head": scores_meta.get("git_head"),
            "population": scores_meta.get("population"),
        },
        "contradicted": (
            None
            if contradicted is None
            else {"path": contradicted[0], "listed": len(contradicted_ids or [])}
        ),
        "feasibility_audit": (
            None
            if audit is None
            else {"path": audit[0], "boundary_cases": len(boundary_ids or set())}
        ),
    }

    ledger: list[dict[str, Any]] = []
    for case in eval_cases:
        top = tops[case["case_id"]]
        top_years = [year for year, _ in top]
        ledger.append(
            {
                "case_id": case["case_id"],
                "birth_year": case["birth_year"],
                "e": len(case["event_years"]),
                "event_years": case["event_years"],
                "top3": top_years,
                "top3_scores": [score for _, score in top],
                "hit": bool(set(top_years) & case["event_year_set"]),
                "p_case": p_case_for(len(case["event_years"])),
            }
        )

    e_distribution: dict[str, int] = {}
    for case in eval_cases:
        key = str(len(case["event_years"]))
        e_distribution[key] = e_distribution.get(key, 0) + 1

    return {
        "schema": SCHEMA,
        "task": TASK,
        "protocol": {
            "population": "usable_for_timing=true",
            "candidate_years": {"min_age": AGE_MIN, "max_age": AGE_MAX, "count": CANDIDATE_YEARS},
            "primary_k": K,
            "hit_rule": "Top-K 中任一年 ∈ E",
            "null": "事件置换：p_case = 1 - C(16-e,3)/C(16,3)，e=0 → 0",
            "aggregate": "精确 Poisson-binomial 单侧 p（标准库 DP 卷积）",
            "alpha": ALPHA,
            "signal_pp": SIGNAL_PP,
            "kill_pp": KILL_PP,
            "kill_p": KILL_P,
            "tie_break": "sha256(case_id|year) 升序",
            "static_baseline": "同 K=3 连续年龄窗口 20–22 … 33–35，取命中率最高（并列取 lo 小）",
        },
        "inputs": inputs,
        "verdict": main.get("gates", {"verdict": "empty"}),
        "static_baseline": {
            "k": static_all["k"],
            "n": static_all["n"],
            "best": static_all["best"],
            "reference_t165_pct": REFERENCE_STATIC_PCT,
            "matches_reference": abs(static_all["best"]["rate_pct"] - REFERENCE_STATIC_PCT) <= 0.05,
            "seven_year_band_note": "24–30 岁 7 年窗口的 45.3% 只作参考，不作 Top-3 基线",
            "table": static_all["table"],
        },
        "populations": populations,
        "e_distribution": e_distribution,
        "cases": ledger,
        "determinism": {
            "tie_break": "sha256(case_id|year) 升序",
            "random": False,
            "timestamp": False,
            "case_order": "case_id 升序",
        },
    }


# ── Markdown 渲染 ───────────────────────────────────────────────────────────

_VERDICT_CN = {
    "signal_above_static_baseline": "信号成立且过同 K 静态基线（有增量信息）",
    "signal_below_static_baseline": "统计信号成立但未过同 K 静态基线（不宣布有效）",
    "dead": "判死（差值 < +3pp 或 p > 0.20）",
    "inconclusive": "中间态 / 样本不足（不宣布有效）",
    "empty": "空集（无案例）",
}


def _pct_text(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def _sidecar_text(info: dict[str, Any] | None, count_key: str) -> str:
    if not info:
        return "未提供"
    return f"`{info['path']}`，{info[count_key]} 例"


def render_md(report: dict[str, Any]) -> str:
    main = report["populations"][0]
    verdict_value = report["verdict"].get("verdict", "empty")
    best = report["static_baseline"]["best"]
    lines: list[str] = []
    add = lines.append

    add("# 婚姻应期评测报告 v1（K=3） · T-167")
    add("")
    add("> 本报告由 `python -m tools.timing_eval_v1` 生成：只读分数与事件年份，"
        "无随机数、无时间戳；同一输入两次运行逐字节一致。")
    add("> 真实评分由中枢一次性执行；评测器不含任何「看结果调阈值」的分支。")
    add("")

    add("## 0. 输入")
    add("")
    add("| 项 | 值 |")
    add("|---|---|")
    add(f"| 评测集 | `{report['inputs']['eval_set']['path']}` |")
    add(f"| 可用案例 | {report['inputs']['eval_set']['usable_cases']} |")
    add(f"| 分数文件 | `{report['inputs']['scores']['path']}` |")
    add(f"| 分数案例 | {report['inputs']['scores']['cases']} |")
    add(f"| protocol_id | {report['inputs']['scores']['protocol_id']} |")
    add(f"| 冻结时间 | {report['inputs']['scores']['frozen_at']} |")
    add(f"| git_head | {report['inputs']['scores']['git_head']} |")
    contradicted = report["inputs"]["contradicted"]
    add(f"| T-168 矛盾名单 | {_sidecar_text(contradicted, 'listed')} |")
    audit = report["inputs"]["feasibility_audit"]
    add(f"| T-165 边界警告 | {_sidecar_text(audit, 'boundary_cases')} |")
    add("")

    add("## 1. 判定（主口径 all）")
    add("")
    add("| 指标 | 值 |")
    add("|---|---|")
    if main.get("status") == "ok":
        gates = main["gates"]
        add(f"| 样本 n | {main['n']} |")
        add(f"| observed | {main['observed']} |")
        add(f"| expected（Σp_case） | {main['expected']:.4f} |")
        add(f"| observed 命中率 | {_pct_text(gates['observed_rate'])} |")
        add(f"| expected 命中率 | {_pct_text(gates['expected_rate'])} |")
        add(f"| 差值 | {gates['diff_pp']:+.2f}pp |")
        add(f"| 精确单侧 p | {main['p_value']:.6g} |")
        add(f"| Wilson 95% 下界 | {_pct_text(main['wilson_low'])} |")
        add(f"| 同 K 静态基线 | {main['static_baseline']['rate_pct']:.2f}%"
            f"（{main['static_baseline']['window'][0]}–{main['static_baseline']['window'][1]} 岁） |")
    add(f"| **判定** | **{_VERDICT_CN.get(verdict_value, verdict_value)}** |")
    add("")

    add("## 2. 全部口径与敏感性（K=3，预注册）")
    add("")
    add("| 口径 | n | e=0 | observed | expected | obs% | exp% | 差值 | 精确 p | Wilson 下界 | 静态基线% | 判定 |")
    add("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for population in report["populations"]:
        if population.get("status") != "ok":
            add(f"| {population['name']} | - | - | - | - | - | - | - | - | - | - | "
                f"{population.get('status')}：{population.get('reason', '')} |")
            continue
        gates = population["gates"]
        add(
            f"| {population['name']} | {population['n']} | {population['e_zero_cases']} | "
            f"{population['observed']} | {population['expected']:.2f} | "
            f"{100.0 * gates['observed_rate']:.2f}% | {100.0 * gates['expected_rate']:.2f}% | "
            f"{gates['diff_pp']:+.2f}pp | {population['p_value']:.6g} | "
            f"{100.0 * population['wilson_low']:.2f}% | {population['static_baseline']['rate_pct']:.2f}% | "
            f"{_VERDICT_CN.get(gates['verdict'], gates['verdict'])} |"
        )
    add("")
    add("敏感性口径的静态基线按该子集自身重算（同一枚举规则）；正式判定只看主口径 all。")
    add("")

    add(f"## 3. 同 K 静态基线枚举（宽 {report['static_baseline']['k']}，20–22 … 33–35）")
    add("")
    add("| 窗口 | 命中 | 命中率 |")
    add("|---|---|---|")
    for row in report["static_baseline"]["table"]:
        add(f"| {row['lo']}–{row['hi']} 岁 | {row['hits']}/{report['static_baseline']['n']} | {row['rate_pct']:.2f}% |")
    add("")
    add(f"最佳窗口：**{best['lo']}–{best['hi']} 岁，{best['hits']}/{report['static_baseline']['n']} = "
        f"{best['rate_pct']:.2f}%**（T-165 参考值 {REFERENCE_STATIC_PCT}%）。")
    add(f"注：{report['static_baseline']['seven_year_band_note']}。")
    add("")

    add("## 4. 口径与公式")
    add("")
    add(f"- 候选年：{AGE_MIN}–{AGE_MAX} 岁共 {CANDIDATE_YEARS} 年；主检验 K={K}。")
    add("- 事件年 E：婚姻事件年份落在窗口内的去重年份；Top-3 中任一年 ∈ E 即命中。")
    add("- 逐例零假设（事件置换）：`p_case = 1 - C(16-e,3)/C(16,3)`；e=0 → 0（结构性零）。")
    add("- 聚合：`observed=Σhit`，`expected=Σp_case`，精确 Poisson-binomial 单侧 p（DP 卷积）。")
    add("- Wilson 95% 下界基于 observed 命中率；实用门要求其严格大于同 K 静态基线。")
    add(f"- 判定：差值 ≥ +{SIGNAL_PP:g}pp 且 p < {ALPHA} 为信号；差值 < +{KILL_PP:g}pp 或 p > {KILL_P} 判死；"
        "其余为中间态。")
    add("- 并列：按 `sha256(case_id|year)` 升序取年，跨平台确定。")
    add("")

    add("## 5. 结构与风险")
    add("")
    e_dist = report["e_distribution"]
    add(f"- 窗口内事件年数分布：{json.dumps(e_dist, ensure_ascii=False, sort_keys=True)}。")
    add("- e=0 为结构性零：H0/H1 下都不命中，p_case=0，按预注册保留在主口径，另报 labeled 子集。")
    add("- e<3 无特殊处理：公式对 e=1、2 自然给出 3/16、35%；e≥14 时 p_case=1（16-e<3）。")
    add("- Poisson-binomial 用浮点 DP（逐例独立伯努利，p≤0.49），尾概率用 `math.fsum` 求和，无双精度溢出风险。")
    add("- 分数文件必须恰好覆盖每例 20–35 岁 16 年；缺年/多年/缺例一律退出码 2，不做补齐或剔除。")
    add("")

    return "\n".join(lines)


# ── CLI ─────────────────────────────────────────────────────────────────────


def _resolve_sidecar(explicit: Path | None, eval_path: Path, filename: str) -> Path | None:
    if explicit is not None:
        return explicit
    candidate = eval_path.parent / filename
    return candidate if candidate.exists() else None


def _emit(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", "replace") + b"\n")
        sys.stdout.flush()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.timing_eval_v1",
        description="婚姻应期评测器 v1（K=3，只读分数与事件年份）",
    )
    parser.add_argument("--scores", required=True, type=Path, help="分数 JSON（T-166 产物）")
    parser.add_argument("--eval-set", required=True, type=Path, help="评测集 JSON（只读事件年份）")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_PREFIX, help="报告输出前缀（生成 .json/.md）")
    parser.add_argument("--contradicted", type=Path, default=None, help="T-168 矛盾名单 JSON")
    parser.add_argument("--audit", type=Path, default=None, help="T-165 可行性审计 JSON（取边界警告）")
    parser.add_argument("--json", action="store_true", help="把完整报告 JSON 打到 stdout")
    args = parser.parse_args(argv)

    try:
        eval_payload = _load_json(args.eval_set)
        scores_payload = _load_json(args.scores)
        contradicted_path = _resolve_sidecar(args.contradicted, args.eval_set, CONTRADICTED_FILENAME)
        audit_path = _resolve_sidecar(args.audit, args.eval_set, AUDIT_FILENAME)
        contradicted = (
            (str(contradicted_path), _load_json(contradicted_path)) if contradicted_path else None
        )
        audit = (str(audit_path), _load_json(audit_path)) if audit_path else None
        report = build_report(
            eval_payload=eval_payload,
            scores_payload=scores_payload,
            eval_path=str(args.eval_set),
            scores_path=str(args.scores),
            contradicted=contradicted,
            audit=audit,
        )
    except InputError as exc:
        print(f"[timing_eval_v1] 输入错误：{exc}", file=sys.stderr)
        return 2

    json_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    md_text = render_md(report)
    json_path = args.out.with_suffix(".json")
    md_path = args.out.with_suffix(".md")
    _write_text(json_path, json_text)
    _write_text(md_path, md_text)

    if args.json:
        _emit(json_text)
    else:
        main_row = report["populations"][0]
        if main_row.get("status") == "ok":
            gates = main_row["gates"]
            _emit(
                f"[timing_eval_v1] n={main_row['n']} observed={main_row['observed']} "
                f"expected={main_row['expected']:.2f} "
                f"diff={gates['diff_pp']:+.2f}pp p={main_row['p_value']:.6g} "
                f"wilson_low={_pct_text(main_row['wilson_low'])} "
                f"baseline={main_row['static_baseline']['rate_pct']:.2f}% "
                f"verdict={gates['verdict']}"
            )
        _emit(f"[timing_eval_v1] written {json_path}")
        _emit(f"[timing_eval_v1] written {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
