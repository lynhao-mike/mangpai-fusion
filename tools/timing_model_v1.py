"""T-166 · 婚姻应期模型 v1（R1–R4，零年龄参数，只出分数）。

按 ``tasks/T-166/PROMPT.md`` §1.2，对 382 例 ``usable_for_timing`` 案例的
20–35 岁（16 年/例）逐年打分：

- R1 夫妻宫引动：流年支与 ``D.b`` 的 chong/liuhe/xing/chuan 边，按 kind 去重，每种 +1，上限 4。
- R2 配偶星引动：配偶星（男财/女官杀）的地支地址受流年 chong/liuhe，每个地址 +1，上限 2；
  取不到地址 → R2=0 并记 ``no_spouse_star``。
- R3 冲开墓库：该流年冲开任一原局墓库 → +1（复用 T-165 已验证的 ``chong_kai_muku(year=…)``）。
- R4 三合/三会引动：含 ``D.b`` 的完整三合/三会且 scope 含流年 → +1。

红线（与任务卡一致）：

- ``score_year(chart_facts, year, dayun_index)`` 不接收 birth_year/age；
  出生年只在装配层用于生成候选年。
- 只从评测集读 ``case_id / birth_dt / gender / birth_year / usable_for_timing`` 五个字段，
  不读任何结果标签，不计算任何评测指标（评测器见 T-167）。
- 只读 engine 事实层，不改 ``engine/**``、不改规则、不调权重或阈值。

运行::

    .venv\\Scripts\\python.exe -m tools.timing_model_v1

产出 ``META/timing-scores-v1.json``（sort_keys + indent=2 + UTF-8 + LF，两次运行逐字节一致）。
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

from engine.api.facade import to_jsonable
from engine.claims.condition_ir.atoms import ATOMS, SPOUSE, build_context
from engine.facts.chart_facts import chart_from_solar
from engine.facts.relation_graph import build_relation_graph
from engine.facts.types import ChartFacts

ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = ROOT / "META" / "timing-eval-set-v1.json"
OUT_PATH = ROOT / "META" / "timing-scores-v1.json"

SCHEMA = "timing-scores/v1"
TASK = "T-166"
PROTOCOL_ID = "timing-k3-v1"
# 冻结时间 = 建卡提交（2a0adc6）时间；与 META/eval-protocols/timing-k3-v1.yaml 一致。
FROZEN_AT = "2026-10-29T07:44:53+08:00"

AGE_MIN, AGE_MAX = 20, 35
CANDIDATE_YEARS = AGE_MAX - AGE_MIN + 1  # 16

# R1/R2 的「he」指六合 liuhe（T-165 审计 RELATION_KINDS 同口径）；不含暗合、三合半局。
R1_KINDS = ("chong", "liuhe", "xing", "chuan")
R2_KINDS = ("chong", "liuhe")
R1_CAP, R2_CAP, R3_CAP, R4_CAP = 4, 2, 1, 1
MAX_SCORE = R1_CAP + R2_CAP + R3_CAP + R4_CAP  # 8

# 评测集只允许读的字段：写入白名单，装配层不再碰其它键。
CASE_FIELDS = ("case_id", "birth_dt", "gender", "birth_year")


# ── 事实装配 ────────────────────────────────────────────────────────────────


def git_head() -> str:
    """读当前 HEAD（不调 git 子进程；工作树/普通仓库都可读）。"""
    git = ROOT / ".git"
    if git.is_dir():
        head = (git / "HEAD").read_text(encoding="ascii").strip()
        if head.startswith("ref: "):
            ref = head[len("ref: "):].strip()
            ref_path = git / ref
            return ref_path.read_text(encoding="ascii").strip() if ref_path.is_file() else "unknown"
        return head
    if git.is_file():  # worktree: ".git" 指向真实 gitdir
        text = git.read_text(encoding="ascii").strip()
        if text.startswith("gitdir:"):
            real = Path(text.split(":", 1)[1].strip())
            real = real if real.is_absolute() else (ROOT / real).resolve()
            head = (real / "HEAD").read_text(encoding="ascii").strip()
            if head.startswith("ref: "):
                ref_path = real / head[len("ref: "):].strip()
                return ref_path.read_text(encoding="ascii").strip() if ref_path.is_file() else "unknown"
            return head
    return "unknown"


def candidate_years(birth_year: int) -> list[int]:
    """候选年 = 出生年 + 20 … +35（年龄只在此处出现，不进评分函数）。"""
    return [birth_year + age for age in range(AGE_MIN, AGE_MAX + 1)]


def dayun_index_for_year(chart: ChartFacts, year: int) -> Optional[int]:
    """公历年 → 大运序号；只读 facts 的 start/end_year，不心算起运。"""
    cycles = chart.cycles
    if cycles is None:
        return None
    for step in cycles.dayun:
        if step.start_year and step.end_year and step.start_year <= year <= step.end_year:
            return step.index
    return None


def spouse_branch_addresses(chart: ChartFacts) -> list[str]:
    """配偶星的地支地址（本气或藏干见配偶星），按原局柱序排序。

    只取地支地址：任务卡 R2 明确「取其地支地址」；天干透出的配偶星不在此列。
    取不到返回空列表 → R2=0 并记 ``no_spouse_star``。
    """
    gods = SPOUSE[chart.gender]
    addrs: list[str] = []
    for pillar in chart.pillars:
        hidden = pillar.branch.hidden
        if pillar.branch.main_ten_god in gods or any(h.ten_god in gods for h in hidden):
            addrs.append(pillar.branch.addr)
    return addrs


# ── 规则 ────────────────────────────────────────────────────────────────────


def _r1_hits(edges, year: int) -> dict[str, Any]:
    """夫妻宫引动：流年支与 D.b 的直边，按 kind 去重（每种取图内首条边）。"""
    needle = f"LN{year}.b"
    hits: dict[str, Any] = {}
    for edge in edges:
        if edge.kind not in R1_KINDS or edge.scope != "liunian":
            continue
        if "D.b" not in edge.members or needle not in edge.members:
            continue
        hits.setdefault(edge.kind, edge)
    return hits


def _r2_hits(edges, year: int, spouse_addrs: list[str]) -> list[tuple[str, Any]]:
    """配偶星引动：每个配偶星地支地址受流年 chong/liuhe，各 +1（按地址顺序，最多 2）。"""
    needle = f"LN{year}.b"
    hits: list[tuple[str, Any]] = []
    for addr in spouse_addrs:
        for edge in edges:
            if edge.kind not in R2_KINDS or edge.scope != "liunian":
                continue
            if addr in edge.members and needle in edge.members:
                hits.append((addr, edge))
                break
        if len(hits) >= R2_CAP:
            break
    return hits


def _r3_hit(ctx: dict[str, Any], edges, year: int) -> tuple[int, Any, Optional[str]]:
    """冲开墓库：复用 T-165 已验证的 ``chong_kai_muku(year=…)``（含引擎既有刑开口径）。"""
    result = ATOMS["chong_kai_muku"](ctx, {"year": year})
    if result.value is not True:
        return 0, None, None
    edge = next((e for e in edges if e.id == result.bindings.get("edge_id")), None)
    return 1, edge, result.bindings.get("addr")


def _r4_hit(edges) -> Any:
    """三合/三会引动：含 D.b 的完整局，且 scope 含流年（dayun-only 不计）。"""
    for edge in edges:
        if edge.kind not in ("sanhe", "sanhui") or edge.completeness != "full":
            continue
        if "D.b" not in edge.members:
            continue
        if edge.scope in ("liunian", "dayun+liunian"):
            return edge
    return None


def _muku_bound_by_liunian(edges, year: int, muku_addrs: Iterable[str]) -> bool:
    """该流年是否以六合/完整三合/完整三会合住原局墓库（合开缺口的事实侧记录）。"""
    needle = f"LN{year}.b"
    addrs = set(muku_addrs)
    for edge in edges:
        if edge.scope not in ("liunian", "dayun+liunian") or needle not in edge.members:
            continue
        if edge.kind == "liuhe" or (
            edge.kind in ("sanhe", "sanhui") and edge.completeness == "full"
        ):
            if addrs & set(edge.members):
                return True
    return False


def _edge_record(
    rule: str,
    chart_id: str,
    year: int,
    dayun_index: int,
    edge,
    at: str,
) -> dict[str, Any]:
    """一条计分边的记录：复合键 (chart_id, dayun_index, liunian_year, edge_id) 全字段落盘。"""
    return {
        "rule": rule,
        "edge_key": f"{chart_id}|{dayun_index}|{year}|{edge.id}",
        "chart_id": chart_id,
        "dayun_index": dayun_index,
        "liunian_year": year,
        "edge_id": edge.id,
        "kind": edge.kind,
        "scope": edge.scope,
        "members": list(edge.members),
        "at": at,
    }


def evaluate_year(chart_facts: ChartFacts, year: int, dayun_index: int) -> dict[str, Any]:
    """算一年：返回 ``year/score/components/edges/flags``（artifact 的 years[] 元素）。

    不接收 birth_year/age；唯一时间输入是候选公历年与显式大运序号。
    """
    graph = build_relation_graph(chart_facts, dayun_index=dayun_index, liunian_year=year)
    ctx = build_context({
        "chart": to_jsonable(chart_facts),
        "relations": to_jsonable(graph),
    })
    edges = graph.edges
    chart_id = chart_facts.chart_id
    spouse_addrs = spouse_branch_addresses(chart_facts)

    r1_hits = _r1_hits(edges, year)
    r2_hits = _r2_hits(edges, year, spouse_addrs)
    r3, r3_edge, muku_addr = _r3_hit(ctx, edges, year)
    r4_edge = _r4_hit(edges)

    r1 = min(len(r1_hits), R1_CAP)
    r2 = min(len(r2_hits), R2_CAP)
    r4 = 1 if r4_edge is not None else 0

    edges_out: list[dict[str, Any]] = []
    for kind in R1_KINDS:
        edge = r1_hits.get(kind)
        if edge is not None:
            edges_out.append(_edge_record("R1", chart_id, year, dayun_index, edge, "D.b"))
    for addr, edge in r2_hits:
        edges_out.append(_edge_record("R2", chart_id, year, dayun_index, edge, addr))
    if r3_edge is not None:
        edges_out.append(_edge_record("R3", chart_id, year, dayun_index, r3_edge, muku_addr or ""))
    if r4_edge is not None:
        edges_out.append(_edge_record("R4", chart_id, year, dayun_index, r4_edge, "D.b"))

    flags: list[str] = []
    if not spouse_addrs:
        flags.append("no_spouse_star")
    if r3 == 0 and _muku_bound_by_liunian(
        edges, year, (m.addr for m in graph.muku)
    ):
        flags.append("muku_open_by_he_missing")

    return {
        "year": year,
        "score": r1 + r2 + r3 + r4,
        "components": {"r1": r1, "r2": r2, "r3": r3, "r4": r4},
        "edges": edges_out,
        "flags": sorted(flags),
    }


def score_year(chart_facts: ChartFacts, year: int, dayun_index: int) -> int:
    """任务卡评分签名：只看盘面事实与候选年，不接收 birth_year/age。

    实现委托 :func:`evaluate_year`，保证分数与 artifact 的 components/edges 同源。
    """
    return int(evaluate_year(chart_facts, year, dayun_index)["score"])


# ── 案例装配 ────────────────────────────────────────────────────────────────


def build_case_record(
    case: dict[str, Any],
    score_fn: Callable[[ChartFacts, int, int], dict[str, Any]] = evaluate_year,
) -> dict[str, Any]:
    """一例：建盘一次，逐候选年评分；正分年不足 3 也照常输出 16 年，不补齐。"""
    chart = chart_from_solar(datetime.fromisoformat(case["birth_dt"]), case["gender"])
    years: list[dict[str, Any]] = []
    for year in candidate_years(case["birth_year"]):
        index = dayun_index_for_year(chart, year)
        if index is None:
            years.append({
                "year": year,
                "score": 0,
                "components": {"r1": 0, "r2": 0, "r3": 0, "r4": 0},
                "edges": [],
                "flags": ["no_dayun_context"],
            })
            continue
        years.append(score_fn(chart, year, index))
    return {
        "case_id": case["case_id"],
        "birth_year": case["birth_year"],
        "positive_years": sum(1 for item in years if item["score"] > 0),
        "years": years,
    }


def _population(cases: list[dict[str, Any]], records: list[dict[str, Any]]) -> dict[str, Any]:
    genders = Counter(str(case["gender"]) for case in cases)
    per_case_years = Counter(len(record["years"]) for record in records)
    return {
        "source": "META/timing-eval-set-v1.json",
        "filter": {"field": "usable_for_timing", "value": True},
        "cases": len(cases),
        "gender_counts": {key: genders[key] for key in sorted(genders)},
        "candidate_age_min": AGE_MIN,
        "candidate_age_max": AGE_MAX,
        "years_per_case": CANDIDATE_YEARS,
        "case_years": sum(len(record["years"]) for record in records),
        "years_per_case_counts": {str(k): per_case_years[k] for k in sorted(per_case_years)},
        "candidate_year_rule": "birth_year+20 … birth_year+35；出生年只用于生成候选年，评分函数不接收",
    }


def _rules() -> dict[str, Any]:
    return {
        "R1": {
            "name": "夫妻宫引动",
            "target": "D.b",
            "scope": "liunian",
            "edge_kinds": list(R1_KINDS),
            "dedupe": "kind",
            "per_hit": 1,
            "cap": R1_CAP,
        },
        "R2": {
            "name": "配偶星引动",
            "target": "配偶星地支地址（男命财星 / 女命官杀；本气或藏干见星）",
            "scope": "liunian",
            "edge_kinds": list(R2_KINDS),
            "per_addr": 1,
            "cap": R2_CAP,
            "missing": "取不到地支地址 → R2=0，记 no_spouse_star（不猜，不借天干地址）",
        },
        "R3": {
            "name": "冲开墓库",
            "source": "engine.claims.condition_ir.atoms.chong_kai_muku(year=…)（T-165 已验证调用）",
            "kinds": ["chong", "xing"],
            "per_hit": 1,
            "cap": R3_CAP,
            "gap": "合开墓库无原语，不补；R3=0 且流年六合/完整三合/三会合住墓库时记 muku_open_by_he_missing",
        },
        "R4": {
            "name": "三合/三会引动",
            "target": "D.b",
            "scope": ["liunian", "dayun+liunian"],
            "kinds": ["sanhe", "sanhui"],
            "completeness": "full",
            "per_hit": 1,
            "cap": R4_CAP,
        },
        "score": "R1+R2+R3+R4，无权重，整数 0–8",
        "zero_age_parameters": True,
        "score_signature": "score_year(chart_facts, year, dayun_index) -> int",
        "tie_break": "(-score, sha256(case_id|year) 升序)；Top-3 由评测器取，模型不取",
        "gaps_not_filled": ["muku_open_by_he_missing", "no_spouse_star"],
    }


def build_payload(
    cases: Iterable[dict[str, Any]],
    *,
    score_fn: Callable[[ChartFacts, int, int], dict[str, Any]] = evaluate_year,
    frozen_at: str = FROZEN_AT,
    head: Optional[str] = None,
) -> dict[str, Any]:
    """装配完整 artifact；``cases`` 只含 CASE_FIELDS 白名单字段。"""
    case_list = list(cases)
    records = [build_case_record(case, score_fn) for case in case_list]
    return {
        "schema": SCHEMA,
        "task": TASK,
        "protocol_id": PROTOCOL_ID,
        "frozen_at": frozen_at,
        "git_head": git_head() if head is None else head,
        "population": _population(case_list, records),
        "rules": _rules(),
        "cases": records,
    }


def load_eval_cases(path: Path = EVAL_PATH) -> list[dict[str, Any]]:
    """只取白名单字段；事件标签不进入本模型。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    cases: list[dict[str, Any]] = []
    for raw in data["cases"]:
        if raw.get("usable_for_timing") is not True:
            continue
        case = {field: raw.get(field) for field in CASE_FIELDS}
        missing = [field for field, value in case.items() if value in (None, "")]
        if missing:
            raise ValueError(f"{raw.get('case_id')} 缺字段 {missing}")
        cases.append(case)
    return cases


def render_json(payload: dict[str, Any]) -> str:
    """规范 JSON：sort_keys + indent=2 + UTF-8 + 末尾换行（两次运行逐字节一致）。"""
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_scores(payload: dict[str, Any], path: Path = OUT_PATH) -> str:
    text = render_json(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def summarize(payload: dict[str, Any]) -> dict[str, Any]:
    """运行期摘要（只统计本模型自己的输出，不读任何标签）。"""
    score_hist = Counter()
    positive_hist = Counter()
    flags = Counter()
    rule_hits = Counter()
    for case in payload["cases"]:
        positive_hist[case["positive_years"]] += 1
        for year in case["years"]:
            score_hist[year["score"]] += 1
            flags.update(year["flags"])
            rule_hits.update(edge["rule"] for edge in year["edges"])
    return {
        "cases": len(payload["cases"]),
        "case_years": sum(len(case["years"]) for case in payload["cases"]),
        "years_per_case": dict(sorted(Counter(
            len(case["years"]) for case in payload["cases"]
        ).items())),
        "positive_years_per_case": {str(k): positive_hist[k] for k in sorted(positive_hist)},
        "score_histogram": {str(k): score_hist[k] for k in sorted(score_hist)},
        "flags": {k: flags[k] for k in sorted(flags)},
        "rule_edges": {k: rule_hits[k] for k in sorted(rule_hits)},
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    cases = load_eval_cases()
    payload = build_payload(cases)
    digest = write_scores(payload)
    summary = summarize(payload)
    print(json.dumps({"summary": summary, "sha256": digest}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
