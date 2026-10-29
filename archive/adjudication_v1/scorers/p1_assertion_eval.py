"""tools/p1_assertion_eval.py · P1′ 系统级断言评分器（T-186；只读、只评方向）。

问题：`META/p1-fresh-40-answers-v1.json`（40 条原书明确方向断言）+ 5 条 routing 例
（预注册 `expected_direction=needs_judgment`）这一卷，系统的**方向判定**能判对多少？
本工具只做「比对 + 记账」：不排盘、不读 `sources/`、不跑 engine、不改答案、不调阈值。
**真实 fresh-40 由中枢在 T-183/T-185 完成后一次性执行**；本工具的测试只用合成 fixture。

输入
----
1. `--answers`：`p1-fresh-40-answers/v1`。每条 `cases[]` 至少有 `case_id` 与
   `relation{a, b, kind, mechanism, actor, mutual?}`；`actor` = 施力端（T-185 口径 `actor == a`），
   `mutual: true` 表示两端互毁（刑的两败例，无单一施力端）。
2. `--routing`：5 条 routing 例，每条至少有 `case_id`、`a`、`b`、`expected_direction=needs_judgment`。
   **routing 例单列**：只进 `total` 与 routing 小表，不进 `precision` 分母。
3. `--system-output`：系统输出 JSON，`cases[]` 每条
   `{case_id, a, b, kind, direction∈{actor→target, mutual, needs_judgment}, edge_id, source_ref}`。

方向语义（写死，改即改尺子）
--------------------------
- `a` = 系统自报的**施力端**（与 prereg §4.2 的 `palace.actor` 同义），`b` = 另一端；
  `direction="actor→target"` 意为「我的 `a` 端施力于 `b` 端」；`mutual` 意为两端互毁。
- 因此「写反」= 系统把两端写反（系统 `a` 等于答案 target），记 `wrong / reversed`；
  两端不是答案那一对 → `wrong / endpoint_mismatch`（系统答的不是这条断言，不得算对）。
- 答案 `mutual: true` 而系统给 `actor→target`（或反之）→ `wrong`，理由分别记
  `mutual_expected_directed_observed` / `directed_expected_mutual_observed`。
- `kind` 只随行输出、不参与判分（本卷判的是方向；kind 映射另见 `p1_holdout_eval`）。

六个记账桶（每条断言恰好落一个；routing 例不进 precision）
----------------------------------------------------------
    correct             main，方向与答案同向（或 mutual ↔ mutual）
    wrong               main，确实给了方向但不同向（写反 / 端点不同 / mutual 与单向互串）
    abstain_expected    routing（预注册 needs_judgment），系统也 abstain —— 正解是分流
    abstain_unexpected  main，系统却 `needs_judgment` —— 该判方向却不判（abstain 不记 ok/wrong）
    missing             系统输出里没有该 `case_id`
    routing_claims      routing 例上系统仍硬给方向 —— **不进 precision 分母**，单独记账

恒等式（工具内部断言，测试复核）：

    total == correct + wrong + abstain_expected + abstain_unexpected + missing + routing_claims

一等指标（任务卡 §2，逐条照抄，不改分子分母）
--------------------------------------------
    total                = main 例数 + routing 例数（本卷 40 + 5）
    precision            = correct / (correct + wrong)          # 不含 needs_judgment
    coverage             = (correct + wrong) / total            # 分母含 routing（卡面 §2.4 字面口径）
    needs_judgment_rate  = 系统实际 needs_judgment 数 / total
    confident_error      = wrong / (correct + wrong)
    Wilson 95% CI        = precision、coverage 各一（标准 Wilson score interval，z=1.959963984540054）

注意（写出来免得被当成 bug）：coverage 分母按卡面字面取 `total`=45，所以 routing 5 条即使全部
正确 abstain 也不进 `correct + wrong`；满分运行 coverage = 40/45 = 88.9%。若中枢本意是 40 分母，
须在任务卡改口径 —— 本工具**不擅自改分母**。

判定（只读预注册阈值，代码里不许调）
----------------------------------
    pass   = correct ≥ 32/40 且 precision Wilson 下界 > 50% 且 coverage ≥ 75%
             且 confident_error ≤ 10% 且 dev-20 否决/不变量全过（`--dev20-veto passed`）
    kill   = correct < 24
    灰区   = 24 ≤ correct ≤ 31（只发事实层）
    other  = correct ≥ 32 但次级门槛未满足 → `fail_secondary_gate`（不算 pass，也不算 kill）
    claim  = needs_judgment_rate > 50% 只准宣称「分流引擎」（`routing_engine_only`），否则「方向引擎」

分母不是 40/5（例如合成 fixture）时，不给 pass/kill，一律 `not_evaluated` ——
防止把 fixture 上的数字当真实结果引用。

用法
----
    python -m tools.p1_assertion_eval --answers META/p1-fresh-40-answers-v1.json \\
        --routing META/p1-fresh-40-routing-v1.json --system-output <run.json>
    python -m tools.p1_assertion_eval ... --json          # stdout 打完整 JSON
    python -m tools.p1_assertion_eval ... --dev20-veto passed   # 中枢已核 dev-20 后才可判 pass

退出码：0 = 评完（即使判定是 kill）；2 = 输入不合口径（缺文件 / schema 错 / case 对不上）。
产物不含时间戳，同一输入两次运行逐字节一致。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_ANSWERS = ROOT / "META" / "p1-fresh-40-answers-v1.json"
DEFAULT_ROUTING = ROOT / "META" / "p1-fresh-40-routing-v1.json"

SCHEMA_VERSION = "p1-assertion-eval/v1"
TASK = "T-186"

DIRECTED = "actor→target"
MUTUAL = "mutual"
NEEDS_JUDGMENT = "needs_judgment"
DIRECTIONS = (DIRECTED, MUTUAL, NEEDS_JUDGMENT)

MAIN_SET = "main"
ROUTING_SET = "routing"

BUCKETS = ("correct", "wrong", "abstain_expected", "abstain_unexpected", "missing", "routing_claims")

#: 分类型小表的顺序（任务卡 §2.8）；表外 mechanism 追加在后面，不丢行。
MECHANISM_ORDER = ("克", "生", "化", "墓", "冲", "合", "穿", "刑")

#: 标准 Wilson score interval 的 95% 双侧 z。
Z_95 = 1.959963984540054

#: 预注册阈值（只读）。来源：`tasks/T-186/PROMPT.md` §3（goal v5，2026-10-29 预注册）。
#: 改这里 = 改尺子；`tests/tools/test_p1_assertion_eval.py` 有逐值钉死。
PREREG_THRESHOLDS: dict[str, Any] = {
    "source": "tasks/T-186/PROMPT.md §3（goal v5 预注册；本工具只读，不调）",
    "main_cases": 40,
    "routing_cases": 5,
    "pass_correct_min": 32,
    "pass_precision_wilson_lower_strictly_greater": 0.50,
    "pass_coverage_min": 0.75,
    "pass_confident_error_max": 0.10,
    "kill_correct_below": 24,
    "gray_zone_inclusive": [24, 31],
    "needs_judgment_rate_routing_only_above": 0.50,
    "requires_dev20_veto": True,
}


# ── 小工具 ──────────────────────────────────────────────────────────────────

def _norm(value: Any) -> str:
    """端点字规范化：去空白（OCR 引文里常有空格，端点本身是单字）；None → 空串。"""
    if value is None:
        return ""
    return "".join(str(value).split())


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _display_path(path: Path) -> str:
    """仓库内路径写相对形式，换 cwd 重跑仍逐字节一致。"""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _ratio(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else numerator / denominator


def _percent(value: float | None) -> float | None:
    return None if value is None else round(100.0 * value, 2)


def wilson_interval(successes: int, n: int, z: float = Z_95) -> tuple[float, float] | None:
    """标准 Wilson score interval（未做连续性校正）。n == 0 返回 None。"""
    if n <= 0:
        return None
    p = successes / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denom
    margin = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / denom
    return max(0.0, centre - margin), min(1.0, centre + margin)


def _ci_payload(interval: tuple[float, float] | None) -> dict[str, Any] | None:
    if interval is None:
        return None
    lower, upper = interval
    return {
        "lower": lower,
        "upper": upper,
        "lower_percent": _percent(lower),
        "upper_percent": _percent(upper),
    }


def _rate_payload(numerator: int, denominator: int) -> dict[str, Any]:
    value = _ratio(numerator, denominator)
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": value,
        "percent": _percent(value),
    }


# ── 输入 ────────────────────────────────────────────────────────────────────

def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"{label} 文件不存在：{path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{label} 顶层不是 JSON 对象：{path}")
    return data


def load_answers(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """答案 → 逐条期望。每条期望记录 set / case_id / a / b / actor / target / mechanism / kind。"""
    data = _load_json_object(path, "answers")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"answers 缺 cases[] 或为空：{path}")
    if "case_count" in data and data["case_count"] != len(cases):
        raise ValueError(f"answers.case_count={data['case_count']} 与 cases 数 {len(cases)} 不一致")

    expectations: list[dict[str, Any]] = []
    seen: set[str] = set()
    for case in cases:
        case_id = str(case.get("case_id") or "").strip()
        if not case_id:
            raise ValueError("answers 有 case 缺 case_id")
        if case_id in seen:
            raise ValueError(f"answers case_id 重复：{case_id}")
        seen.add(case_id)

        relation = case.get("relation")
        if not isinstance(relation, dict):
            raise ValueError(f"{case_id}: answers 缺 relation 对象")
        a, b = _norm(relation.get("a")), _norm(relation.get("b"))
        if not a or not b:
            raise ValueError(f"{case_id}: relation.a / relation.b 为空")
        mutual = relation.get("mutual") is True
        actor = _norm(relation["actor"]) if relation.get("actor") else ""
        if mutual:
            # mutual 优先：答案说两端互毁时，即使误填 actor 也不按单向评分。
            expected, expected_actor, expected_target = MUTUAL, "", ""
        elif actor:
            if actor not in (a, b):
                raise ValueError(f"{case_id}: relation.actor={actor!r} 不在 a/b={a!r},{b!r} 之内")
            expected_target = b if actor == a else a
            expected, expected_actor = DIRECTED, actor
        else:
            raise ValueError(f"{case_id}: relation 既无 actor 也无 mutual=true，无法定期望方向")

        expectations.append({
            "set": MAIN_SET,
            "case_id": case_id,
            "a": a,
            "b": b,
            "actor": expected_actor,
            "target": expected_target,
            "expected_direction": expected,
            "mechanism": str(relation.get("mechanism") or ""),
            "kind": str(relation.get("kind") or ""),
            "source_ref": str(case.get("source_ref") or ""),
        })

    return expectations, {"path": _display_path(path), "sha256": _sha256(path), "cases": len(cases)}


def load_routing(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """routing 例 → 逐条期望。`expected_direction` 必须是 `needs_judgment`（本卷口径，不认别的值）。"""
    data = _load_json_object(path, "routing")
    cases = data.get("cases")
    if not isinstance(cases, list):
        raise ValueError(f"routing 缺 cases[]：{path}")
    if "case_count" in data and data["case_count"] != len(cases):
        raise ValueError(f"routing.case_count={data['case_count']} 与 cases 数 {len(cases)} 不一致")

    routing: list[dict[str, Any]] = []
    seen: set[str] = set()
    for case in cases:
        case_id = str(case.get("case_id") or "").strip()
        if not case_id:
            raise ValueError("routing 有 case 缺 case_id")
        if case_id in seen:
            raise ValueError(f"routing case_id 重复：{case_id}")
        seen.add(case_id)
        expected = str(case.get("expected_direction") or "").strip()
        if expected != NEEDS_JUDGMENT:
            raise ValueError(
                f"{case_id}: routing 例的 expected_direction 必须是 {NEEDS_JUDGMENT}，"
                f"实际 {expected!r}（本卷 routing 只装预注册 needs_judgment 的例）"
            )
        routing.append({
            "set": ROUTING_SET,
            "case_id": case_id,
            "a": _norm(case.get("a")),
            "b": _norm(case.get("b")),
            "actor": "",
            "target": "",
            "expected_direction": NEEDS_JUDGMENT,
            "mechanism": str(case.get("mechanism") or ""),
            "kind": str(case.get("kind") or ""),
            "source_ref": str(case.get("source_ref") or ""),
        })

    return routing, {"path": _display_path(path), "sha256": _sha256(path), "cases": len(cases)}


def load_observations(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """系统输出 → {case_id: observation}。方向枚举未登记 / case_id 重复一律报错，不静默兜底。"""
    data = _load_json_object(path, "system_output")
    cases = data.get("cases")
    if not isinstance(cases, list):
        raise ValueError(f"system_output 缺 cases[]：{path}")
    if "case_count" in data and data["case_count"] != len(cases):
        raise ValueError(f"system_output.case_count={data['case_count']} 与 cases 数 {len(cases)} 不一致")

    observations: dict[str, dict[str, Any]] = {}
    for case in cases:
        case_id = str(case.get("case_id") or "").strip()
        if not case_id:
            raise ValueError("system_output 有 case 缺 case_id")
        if case_id in observations:
            raise ValueError(f"system_output case_id 重复：{case_id}（一条断言一条输出，不合并）")
        direction = str(case.get("direction") or "").strip()
        if direction not in DIRECTIONS:
            raise ValueError(
                f"{case_id}: system_output.direction={direction!r} 未登记；"
                f"只认 {', '.join(DIRECTIONS)}"
            )
        observations[case_id] = {
            "case_id": case_id,
            "a": _norm(case.get("a")),
            "b": _norm(case.get("b")),
            "kind": str(case.get("kind") or ""),
            "direction": direction,
            "edge_id": case.get("edge_id"),
            "source_ref": str(case.get("source_ref") or ""),
        }

    return observations, {"path": _display_path(path), "sha256": _sha256(path), "cases": len(cases)}


# ── 单条评分 ────────────────────────────────────────────────────────────────

def _same_endpoint_pair(expectation: dict[str, Any], observation: dict[str, Any]) -> bool:
    return sorted([observation["a"], observation["b"]]) == sorted([expectation["a"], expectation["b"]])


def _row_base(expectation: dict[str, Any], observation: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "set": expectation["set"],
        "case_id": expectation["case_id"],
        "mechanism": expectation["mechanism"],
        "kind": expectation["kind"],
        "expected_direction": expectation["expected_direction"],
        "expected_actor": expectation["actor"] or None,
        "expected_a": expectation["a"],
        "expected_b": expectation["b"],
        "observed_direction": None if observation is None else observation["direction"],
        "observed_a": None if observation is None else observation["a"],
        "observed_b": None if observation is None else observation["b"],
        "observed_kind": None if observation is None else observation["kind"],
        "observed_edge_id": None if observation is None else observation["edge_id"],
        "endpoint_match": None if observation is None else _same_endpoint_pair(expectation, observation),
        "status": None,
        "reason": None,
        "source_ref": expectation["source_ref"],
    }


def score_main_case(expectation: dict[str, Any], observation: dict[str, Any] | None) -> dict[str, Any]:
    """main（40 条明确方向断言）→ 六桶之一。abstain 不记 ok/wrong。"""
    row = _row_base(expectation, observation)
    if observation is None:
        row.update(status="missing", reason="not_in_system_output")
        return row

    direction = observation["direction"]
    if direction == NEEDS_JUDGMENT:
        row.update(status="abstain_unexpected", reason="abstained_where_direction_expected")
        return row

    if not row["endpoint_match"]:
        row.update(status="wrong", reason="endpoint_mismatch")
        return row

    if expectation["expected_direction"] == MUTUAL:
        if direction == MUTUAL:
            row.update(status="correct", reason="mutual")
        else:
            row.update(status="wrong", reason="mutual_expected_directed_observed")
        return row

    if direction == MUTUAL:
        row.update(status="wrong", reason="directed_expected_mutual_observed")
        return row

    if observation["a"] == expectation["actor"] and observation["b"] == expectation["target"]:
        row.update(status="correct", reason="same_orientation")
    else:
        row.update(status="wrong", reason="reversed")
    return row


def score_routing_case(expectation: dict[str, Any], observation: dict[str, Any] | None) -> dict[str, Any]:
    """routing（预注册 needs_judgment）→ abstain_expected / routing_claims / missing。"""
    row = _row_base(expectation, observation)
    if observation is None:
        row.update(status="missing", reason="not_in_system_output")
    elif observation["direction"] == NEEDS_JUDGMENT:
        row.update(status="abstain_expected", reason="abstained_as_preregistered")
    else:
        row.update(status="routing_claims", reason="routing_expected_needs_judgment")
    return row


# ── 汇总 ────────────────────────────────────────────────────────────────────

def _count_buckets(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {bucket: 0 for bucket in BUCKETS}
    for row in rows:
        counts[row["status"]] += 1
    return counts


def _mechanism_rows(rows: list[dict[str, Any]]) -> list[str]:
    present = {row["mechanism"] for row in rows if row["mechanism"]}
    ordered = [m for m in MECHANISM_ORDER if m in present]
    ordered += sorted(present - set(MECHANISM_ORDER))
    return ordered


def by_kind_table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """分类型小表（main 只）：每类 total / correct / wrong / abstain_unexpected / missing / precision。"""
    table: list[dict[str, Any]] = []
    for mechanism in _mechanism_rows(rows):
        subset = [row for row in rows if row["mechanism"] == mechanism]
        counts = _count_buckets(subset)
        table.append({
            "mechanism": mechanism,
            "total": len(subset),
            "correct": counts["correct"],
            "wrong": counts["wrong"],
            "abstain_unexpected": counts["abstain_unexpected"],
            "missing": counts["missing"],
            "precision": _rate_payload(counts["correct"], counts["correct"] + counts["wrong"]),
        })
    return table


def routing_table(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """routing 小表：只记分流是否正确，不进 precision。"""
    counts = _count_buckets(rows)
    by_mechanism = []
    for mechanism in _mechanism_rows(rows):
        subset = [row for row in rows if row["mechanism"] == mechanism]
        sub = _count_buckets(subset)
        by_mechanism.append({
            "mechanism": mechanism,
            "total": len(subset),
            "abstain_expected": sub["abstain_expected"],
            "routing_claims": sub["routing_claims"],
            "missing": sub["missing"],
        })
    return {
        "total": len(rows),
        "abstain_expected": counts["abstain_expected"],
        "routing_claims": counts["routing_claims"],
        "missing": counts["missing"],
        "abstain_expected_rate": _rate_payload(counts["abstain_expected"], len(rows)),
        "by_mechanism": by_mechanism,
    }


def compute_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """一等指标（任务卡 §2 的定义，逐条照抄）。"""
    counts = _count_buckets(rows)
    total = len(rows)
    decided = counts["correct"] + counts["wrong"]

    precision_value = _ratio(counts["correct"], decided)
    coverage_value = _ratio(decided, total)
    needs_judgment = sum(1 for row in rows if row["observed_direction"] == NEEDS_JUDGMENT)
    confident_error_value = _ratio(counts["wrong"], decided)
    precision_ci = wilson_interval(counts["correct"], decided)
    coverage_ci = wilson_interval(decided, total)

    return {
        "total": total,
        "correct": counts["correct"],
        "wrong": counts["wrong"],
        "abstain_expected": counts["abstain_expected"],
        "abstain_unexpected": counts["abstain_unexpected"],
        "missing": counts["missing"],
        "routing_claims": counts["routing_claims"],
        "precision": {
            **_rate_payload(counts["correct"], decided),
            "wilson95": _ci_payload(precision_ci),
        },
        "coverage": {
            **_rate_payload(decided, total),
            "wilson95": _ci_payload(coverage_ci),
        },
        "needs_judgment_rate": _rate_payload(needs_judgment, total),
        "confident_error": _rate_payload(counts["wrong"], decided),
    }


def build_verdict(metrics: dict[str, Any], *, main_total: int, routing_total: int,
                  dev20_veto: str) -> dict[str, Any]:
    """按预注册阈值判 pass / kill / 灰区 / 次级门槛未过 / not_evaluated；阈值只读。"""
    thresholds = PREREG_THRESHOLDS
    prereg_denominators_met = (
        main_total == thresholds["main_cases"] and routing_total == thresholds["routing_cases"]
    )

    correct = metrics["correct"]
    precision_lower = metrics["precision"]["wilson95"]["lower"] if metrics["precision"]["wilson95"] else None
    coverage_value = metrics["coverage"]["value"]
    confident_error_value = metrics["confident_error"]["value"]

    gates = {
        "correct_at_least_32": correct >= thresholds["pass_correct_min"],
        "precision_wilson_lower_gt_50": (
            precision_lower is not None
            and precision_lower > thresholds["pass_precision_wilson_lower_strictly_greater"]
        ),
        "coverage_at_least_75": (
            coverage_value is not None and coverage_value >= thresholds["pass_coverage_min"]
        ),
        "confident_error_at_most_10": (
            confident_error_value is not None
            and confident_error_value <= thresholds["pass_confident_error_max"]
        ),
        "dev20_veto_passed": dev20_veto == "passed",
    }

    needs_judgment_rate = metrics["needs_judgment_rate"]["value"]
    routing_only = needs_judgment_rate is not None and (
        needs_judgment_rate > thresholds["needs_judgment_rate_routing_only_above"]
    )

    if not prereg_denominators_met:
        verdict = "not_evaluated"
        reasons = [
            f"预注册分母未满足：main {main_total}/{thresholds['main_cases']}、"
            f"routing {routing_total}/{thresholds['routing_cases']}；合成 fixture 不得判 pass/kill"
        ]
    elif correct < thresholds["kill_correct_below"]:
        verdict = "kill"
        reasons = [f"correct={correct} < {thresholds['kill_correct_below']}（卡 §3：kill）"]
    elif thresholds["gray_zone_inclusive"][0] <= correct <= thresholds["gray_zone_inclusive"][1]:
        verdict = "gray_zone"
        reasons = [f"correct={correct} 落在灰区 24–31：只发事实层（卡 §3）"]
    else:
        failed = [name for name, ok in gates.items() if not ok]
        if failed:
            verdict = "fail_secondary_gate"
            reasons = [f"correct≥32 但次级门槛未满足：{', '.join(failed)}"]
            if dev20_veto == "unknown":
                reasons.append("dev-20 否决/不变量未由中枢核验（--dev20-veto passed 才能判 pass）")
        else:
            verdict = "pass"
            reasons = ["全部门槛满足（correct≥32、Wilson 下界>50%、coverage≥75%、confident_error≤10%、dev-20 通过）"]

    return {
        "verdict": verdict,
        "reasons": reasons,
        "prereg_denominators_met": prereg_denominators_met,
        "main_total": main_total,
        "routing_total": routing_total,
        "gates": gates,
        "dev20_veto": dev20_veto,
        "claim": "routing_engine_only" if routing_only else "direction_engine",
        "claim_note": (
            "needs_judgment_rate > 50%：只准宣称「分流引擎」，不准宣称「方向引擎」（卡 §3）"
            if routing_only else
            "needs_judgment_rate ≤ 50%：不触发分流引擎限制（仍受 verdict 约束）"
        ),
        "notes": [
            "routing 例不进 precision，也不在卡 §3 的 pass 门槛内：routing_claims 只单列"
            "（卡 §4「routing 例单列，不混入 precision 分母」）。要把分流正确率设成门槛，须改卡。",
            "coverage 分母按卡 §2.4 字面取 total（main + routing）：routing 的正确 abstain 不进"
            " correct + wrong，故满分运行 coverage = 40/45 ≈ 88.9%。",
            "confident_error = wrong / (correct + wrong)，与 precision 同一分母；它衡量「判错占已判」的"
            "比例，不衡量「该判不判」。",
        ],
    }


def _check_accounting(metrics: dict[str, Any]) -> None:
    total = metrics["total"]
    bucket_sum = sum(metrics[bucket] for bucket in BUCKETS)
    if total != bucket_sum:
        raise ValueError(f"内部记账不平：total={total} != 六桶之和 {bucket_sum}")


# ── 入口 ────────────────────────────────────────────────────────────────────

def run(answers_path: Path | str = DEFAULT_ANSWERS,
        routing_path: Path | str = DEFAULT_ROUTING,
        system_output_path: Path | str | None = None,
        *,
        dev20_veto: str = "unknown") -> dict[str, Any]:
    """评完整卷，返回可 JSON 化的结果（不含时间戳，逐字节可复现）。"""
    if system_output_path is None:
        raise ValueError("必须给 --system-output（系统输出 JSON）")
    if dev20_veto not in ("passed", "failed", "unknown"):
        raise ValueError(f"dev20_veto 只认 passed/failed/unknown，实际 {dev20_veto!r}")

    answers_path, routing_path = Path(answers_path), Path(routing_path)
    system_output_path = Path(system_output_path)

    expectations, answers_input = load_answers(answers_path)
    routing_cases, routing_input = load_routing(routing_path)
    observations, output_input = load_observations(system_output_path)

    known = {exp["case_id"] for exp in expectations} | {rt["case_id"] for rt in routing_cases}
    overlap = {exp["case_id"] for exp in expectations} & {rt["case_id"] for rt in routing_cases}
    if overlap:
        raise ValueError(f"routing 与 answers 的 case_id 重叠：{sorted(overlap)}")
    extra = sorted(set(observations) - known)
    if extra:
        raise ValueError(f"system_output 有、answers/routing 无的 case_id：{extra}（输入对不上，不得静默丢）")

    rows = [score_main_case(exp, observations.get(exp["case_id"])) for exp in expectations]
    rows += [score_routing_case(rt, observations.get(rt["case_id"])) for rt in routing_cases]

    metrics = compute_metrics(rows)
    _check_accounting(metrics)
    verdict = build_verdict(metrics, main_total=len(expectations),
                            routing_total=len(routing_cases), dev20_veto=dev20_veto)

    return {
        "schema_version": SCHEMA_VERSION,
        "task": TASK,
        "note": ("系统级断言评分器：只比对方向，不排盘、不读 sources、不跑 engine。"
                 "routing 例单列、不进 precision 分母；abstain 不记 ok/wrong；missing 单列。"
                 "真实 fresh-40 由中枢执行，本工具不产生真实结果。"),
        "inputs": {
            "answers": answers_input,
            "routing": routing_input,
            "system_output": output_input,
        },
        "prereg_thresholds": PREREG_THRESHOLDS,
        "denominators": {
            "total": len(rows),
            "main": len(expectations),
            "routing": len(routing_cases),
            "preregistered_main": PREREG_THRESHOLDS["main_cases"],
            "preregistered_routing": PREREG_THRESHOLDS["routing_cases"],
            "coverage_denominator": len(rows),
            "precision_denominator_rule": "correct + wrong（不含 routing / abstain / missing）",
        },
        "metrics": metrics,
        "by_kind": by_kind_table([row for row in rows if row["set"] == MAIN_SET]),
        "routing": routing_table([row for row in rows if row["set"] == ROUTING_SET]),
        "verdict": verdict,
        "cases": rows,
    }


def _pct_text(value: float | None) -> str:
    return "—" if value is None else f"{100.0 * value:.1f}%"


def _ci_text(payload: dict[str, Any] | None) -> str:
    if payload is None:
        return "—"
    return f"[{100.0 * payload['lower']:.1f}%, {100.0 * payload['upper']:.1f}%]"


def render_summary(result: dict[str, Any]) -> str:
    """一行一人话摘要（完整数据用 `--json`）。"""
    metrics = result["metrics"]
    verdict = result["verdict"]
    denominators = result["denominators"]
    parts = [
        f"[P1′ 断言评分 {result['task']}] total={metrics['total']}"
        f"（main {denominators['main']} + routing {denominators['routing']}）",
        f"  buckets: correct={metrics['correct']} wrong={metrics['wrong']}"
        f" abstain_expected={metrics['abstain_expected']} abstain_unexpected={metrics['abstain_unexpected']}"
        f" missing={metrics['missing']} routing_claims={metrics['routing_claims']}",
        f"  precision {metrics['precision']['numerator']}/{metrics['precision']['denominator']}"
        f" = {_pct_text(metrics['precision']['value'])}  Wilson95 {_ci_text(metrics['precision']['wilson95'])}",
        f"  coverage  {metrics['coverage']['numerator']}/{metrics['coverage']['denominator']}"
        f" = {_pct_text(metrics['coverage']['value'])}  Wilson95 {_ci_text(metrics['coverage']['wilson95'])}",
        f"  needs_judgment_rate {metrics['needs_judgment_rate']['numerator']}"
        f"/{metrics['needs_judgment_rate']['denominator']} = {_pct_text(metrics['needs_judgment_rate']['value'])}"
        f"  confident_error = {_pct_text(metrics['confident_error']['value'])}",
        f"  verdict: {verdict['verdict']}（{'; '.join(verdict['reasons'])}）；claim: {verdict['claim']}",
    ]
    kinds = [f"{row['mechanism']} {row['correct']}/{row['correct'] + row['wrong']}" for row in result["by_kind"]]
    if kinds:
        parts.append("  分类型 precision：" + " | ".join(kinds))
    parts.append(
        f"  routing: abstain_expected={result['routing']['abstain_expected']} "
        f"routing_claims={result['routing']['routing_claims']} missing={result['routing']['missing']}"
    )
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--answers", type=Path, default=DEFAULT_ANSWERS)
    ap.add_argument("--routing", type=Path, default=DEFAULT_ROUTING)
    ap.add_argument("--system-output", type=Path, required=True)
    ap.add_argument("--dev20-veto", choices=("passed", "failed", "unknown"), default="unknown",
                    help="dev-20 否决/不变量是否全过（pass 判定必须 passed；默认 unknown 不判 pass）")
    ap.add_argument("--json", action="store_true", help="stdout 打完整 JSON（默认打人话摘要）")
    args = ap.parse_args(argv)

    try:
        result = run(args.answers, args.routing, args.system_output, dev20_veto=args.dev20_veto)
    except (ValueError, OSError) as exc:
        print(f"[p1_assertion_eval] 输入不合口径：{exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    else:
        print(render_summary(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
