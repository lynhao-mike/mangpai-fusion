"""T-154 · 首条产品断语正确性分数（婚姻两条规则）。

对 ``DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1`` 与
``YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1`` 在 T-153 的 342 例婚姻质量标签上
做第一次真实正确性计分。

口径（预注册见 ``META/eval-protocols/product-marriage-{duan,yang}-v1.yaml``）：

* 样本：``META/timing-eval-set-v1.json`` 中 ``usable_for_timing=true``，且
  ``META/marriage-quality-labels-v1.json`` 的 ``label`` ∈ {negative, positive} → 342 例；
  40 例 unknown 不折入。敏感性：剔除 T-153 §9 的 7 例已知误判中落在 342 的 6 例
  → 336 例（947 的 label 是 unknown，不在 342；卡面原写 335，PROMPT §7.1 已更正）。
* 触发：**只用** ``evaluate_rule(...).triggered``；不用 ``outcome`` 筛样本或计分。
* 预测：triggered=True → ``N``；triggered=False → 弃权（不进 claim_metric 分母）。
* 判定（PROMPT §7.2）：两比例检验，比较 ``P(negative | triggered)`` 与
  ``P(negative | not triggered)``；差值用 Newcombe 95% CI，p 值用标准库实现的
  Fisher 精确检验双侧。判定词只有「有区分力 / 反向 / 无差异 / 样本不足」。
* ``claim_metric`` 的 accuracy / baseline_single 仍照报，但**只作描述**：
  对「恒预测 N + 弃权」的单标签规则，accuracy 恒等于触发集负率、且等于
  baseline_single（N 为多数类时），「超过基线」分支在数学上不可达。
* ``outcome=fail`` 的 triggered 例只报描述性 n / accuracy，不参与判定。

建盘 / 特征 / runner 上下文逐字复用 ``tools/rule_contract_report.py``（只读 import，
不改该文件），保证与 T-152 干跑同一口径。

用法::

    python -m tools.product_claim_eval

两次运行产物逐字节一致（无时间戳、case 按 case_id 排序）。
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

import yaml

from engine.claims.metrics import score
from engine.claims.rule_loader import (
    ExecutableClaimRule,
    evaluate_rule,
    load_claim_rule_registry,
)
from engine.features import build_chart_feature_vector
from tools.rule_contract_report import (
    _build_ledger,
    _describe_conditions,
    _duan_active_path_count,
    _selections,
)

ROOT = Path(__file__).resolve().parents[1]
TIMING_PATH = ROOT / "META" / "timing-eval-set-v1.json"
LABEL_PATH = ROOT / "META" / "marriage-quality-labels-v1.json"
SCORE_PATH = ROOT / "META" / "product-marriage-score-v1.json"
REPORT_PATH = ROOT / "META" / "product-marriage-report-v1.md"
PROTOCOL_DIR = ROOT / "META" / "eval-protocols"

SCHEMA = "product-marriage-score/v1"
TASK_ID = "T-154"
LABEL_LETTERS = {"negative": "N", "positive": "P"}
WILSON_Z_95 = 1.959963984540054
MIN_GROUP_N = 30
VERDICT_WORDS = ("有区分力", "反向", "无差异 / 样本不足", "样本不足")

RULES: tuple[dict[str, Any], ...] = (
    {
        "key": "duan",
        "rule_id": "DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1",
        "protocol_id": "product-marriage-duan-v1",
        "protocol_path": PROTOCOL_DIR / "product-marriage-duan-v1.yaml",
    },
    {
        "key": "yang",
        "rule_id": "YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1",
        "protocol_id": "product-marriage-yang-v1",
        "protocol_path": PROTOCOL_DIR / "product-marriage-yang-v1.yaml",
    },
)

# T-153 §9：7 例已知误判（2 否定语境 + 3 第三人称 + 2 繁体）。
# RF-2026-000947 的 label 是 unknown，不在 342；因此实际只能剔除 6 例 → 336。
SENSITIVITY_CASE_IDS: tuple[str, ...] = (
    "RF-2026-000495",
    "RF-2026-000560",
    "RF-2026-000544",
    "RF-2026-000528",
    "RF-2026-000845",
    "RF-2026-000947",
    "RF-2026-000355",
)
EXPECTED_FULL_N = 342
EXPECTED_SENSITIVITY_N = 336
DECLARED_SENSITIVITY_N = 335
EXPECTED_LABEL_COUNTS = {"negative": 186, "positive": 156}

SENSITIVITY_NOTE = (
    "卡面声明 335、实际 336、差 1 例因 RF-2026-000947 的 label 是 unknown、不在 342；"
    "从 342 剔除能落进去的 6 例 = 336。不许为凑 335 另挑 1 例。"
)


# ---------------------------------------------------------------------------
# 数据加载
# ---------------------------------------------------------------------------

def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_sample() -> tuple[list[dict[str, Any]], list[Mapping[str, Any]], Mapping[str, Any]]:
    timing = _load_json(TIMING_PATH)
    labels = _load_json(LABEL_PATH)
    label_by_id = {str(case["case_id"]): case for case in labels["cases"]}
    usable = [case for case in timing["cases"] if case.get("usable_for_timing") is True]

    sample: list[dict[str, Any]] = []
    for case in sorted(usable, key=lambda item: str(item["case_id"])):
        case_id = str(case["case_id"])
        label_case = label_by_id.get(case_id)
        if label_case is None:
            raise RuntimeError(f"标签文件缺 case：{case_id}")
        if label_case.get("usable_for_timing") is not True:
            raise RuntimeError(f"标签/评测集 usable_for_timing 不一致：{case_id}")
        label = str(label_case["label"])
        if label not in LABEL_LETTERS:
            continue
        sample.append(
            {
                "case_id": case_id,
                "birth_dt": case["birth_dt"],
                "gender": case["gender"],
                "label": label,
            }
        )

    counts = Counter(item["label"] for item in sample)
    if len(sample) != EXPECTED_FULL_N or dict(counts) != EXPECTED_LABEL_COUNTS:
        raise RuntimeError(
            f"冻结样本不符：n={len(sample)} counts={dict(counts)}"
            f"（期望 {EXPECTED_FULL_N} / {EXPECTED_LABEL_COUNTS}）"
        )
    if len(usable) != 382:
        raise RuntimeError(f"usable_for_timing 应为 382，实为 {len(usable)}")
    return sample, usable, labels


# ---------------------------------------------------------------------------
# 逐例求值（只取 triggered，outcome 仅记录）
# ---------------------------------------------------------------------------

def _new_row(case: dict[str, Any], triggered: bool | None, outcome: str) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "triggered": triggered,
        "outcome": outcome,
        "label": case["label"],
    }


def _evaluate(
    sample: list[dict[str, Any]], rules_by_id: Mapping[str, ExecutableClaimRule]
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, str]]]:
    rows: dict[str, list[dict[str, Any]]] = {rule["rule_id"]: [] for rule in RULES}
    failures: list[dict[str, str]] = []
    for case in sample:
        try:
            ledger = _build_ledger(case)
            features = build_chart_feature_vector(ledger)
        except Exception as exc:  # noqa: BLE001 - 建盘失败必须逐例列原因，不许静默
            failures.append(
                {
                    "case_id": case["case_id"],
                    "stage": "build",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            for rule_id in rows:
                rows[rule_id].append(_new_row(case, None, "unknown"))
            continue

        try:
            active_path_count: int | None = _duan_active_path_count(ledger)
        except (KeyError, TypeError, ValueError) as exc:
            # 与 duan_runner.generate_claims 的兜底一致：段派结构失败只影响段派规则。
            failures.append(
                {
                    "case_id": case["case_id"],
                    "stage": "duan_structure",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            active_path_count = None

        sex = "male" if str(case["gender"]) == "男" else "female"
        selections = {
            selection.rule_id: selection
            for selection in _selections(ledger, features, sex, active_path_count)
        }
        for rule_id in rows:
            selection = selections.get(rule_id)
            if selection is None:
                rows[rule_id].append(_new_row(case, None, "unknown"))
                continue
            result = evaluate_rule(rules_by_id[rule_id], selection.context)
            rows[rule_id].append(_new_row(case, bool(result.triggered), result.outcome))
    return rows, failures


# ---------------------------------------------------------------------------
# 计分：claim_metric（仅描述）+ 两比例检验（判定）
# ---------------------------------------------------------------------------

def _metric_cases(rows: list[dict[str, Any]], rule_id: str) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for row in rows:
        triggered = row["triggered"]
        if triggered is True:
            branch = "triggered"
        elif triggered is False:
            branch = "untriggered"
        else:
            branch = "not_evaluated"
        cases.append(
            {
                "case_id": row["case_id"],
                "claim_id": rule_id,
                "branch": branch,
                "triggered": triggered,
                "outcome": row["outcome"] if triggered is not None else "unknown",
                "prediction_letters": ["N"] if triggered is True else [],
                "answer_letter": LABEL_LETTERS[row["label"]],
            }
        )
    return cases


def _wilson_bounds(count: int, n: int) -> tuple[float, float]:
    """Wilson score 区间（不取整；Newcombe 组合区间需要原始精度）。"""
    p = count / n
    z2 = WILSON_Z_95 * WILSON_Z_95
    denominator = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denominator
    margin = WILSON_Z_95 * math.sqrt(p * (1.0 - p) / n + z2 / (4.0 * n * n)) / denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def _newcombe_ci(x1: int, n1: int, x2: int, n2: int) -> tuple[float, float]:
    """两独立比例差 p1 − p2 的 Newcombe（1998）method 10 混合 score 区间。"""
    p1, p2 = x1 / n1, x2 / n2
    l1, u1 = _wilson_bounds(x1, n1)
    l2, u2 = _wilson_bounds(x2, n2)
    diff = p1 - p2
    lower = diff - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    upper = diff + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return max(-1.0, lower), min(1.0, upper)


def _fisher_exact_two_sided(a: int, b: int, c: int, d: int) -> float:
    """2x2 Fisher 精确检验双侧 p（概率排序法；整数分子比较，避免浮点容差）。

    表：[[a, b], [c, d]] = [[触发组负, 触发组正], [未触发组负, 未触发组正]]。
    置列联表边际固定，a 的零分布为超几何；双侧 p = 所有不比观测表更可能的表的概率和。
    """
    n1 = a + b
    n2 = c + d
    m1 = a + c
    n = n1 + n2
    if n == 0 or n1 == 0 or n2 == 0 or m1 == 0 or m1 == n:
        return 1.0
    low = max(0, n1 + m1 - n)
    high = min(n1, m1)
    numerators = [
        math.comb(m1, x) * math.comb(n - m1, n1 - x) for x in range(low, high + 1)
    ]
    observed = math.comb(m1, a) * math.comb(n - m1, n1 - a)
    total = sum(value for value in numerators if value <= observed)
    return total / math.comb(n, n1)


def _two_proportion_verdict(n1: int, n2: int, lower: float, upper: float) -> str:
    if n1 < MIN_GROUP_N or n2 < MIN_GROUP_N:
        return "样本不足"
    if lower > 0:
        return "有区分力"
    if upper < 0:
        return "反向"
    return "无差异 / 样本不足"


def _two_proportion(
    triggered_rows: list[dict[str, Any]], untriggered_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    n1, n2 = len(triggered_rows), len(untriggered_rows)
    x1 = sum(1 for row in triggered_rows if row["label"] == "negative")
    x2 = sum(1 for row in untriggered_rows if row["label"] == "negative")
    result: dict[str, Any] = {
        "definition": (
            "P(negative | triggered) vs P(negative | not triggered)；"
            "diff = p_triggered - p_not_triggered"
        ),
        "triggered": {
            "n": n1,
            "n_negative": x1,
            "negative_rate": round(x1 / n1, 4) if n1 else None,
        },
        "not_triggered": {
            "n": n2,
            "n_negative": x2,
            "negative_rate": round(x2 / n2, 4) if n2 else None,
        },
        "diff_pp": None,
        "newcombe_ci95_pp": None,
        "newcombe_ci95": None,
        "fisher_exact_p_two_sided": None,
        "verdict": "样本不足",
    }
    if n1 == 0 or n2 == 0:
        return result

    diff = x1 / n1 - x2 / n2
    lower, upper = _newcombe_ci(x1, n1, x2, n2)
    result.update(
        {
            "diff_pp": round(diff * 100.0, 2),
            "newcombe_ci95_pp": [round(lower * 100.0, 2), round(upper * 100.0, 2)],
            "newcombe_ci95": [round(lower, 6), round(upper, 6)],
            "fisher_exact_p_two_sided": _fisher_exact_two_sided(
                x1, n1 - x1, x2, n2 - x2
            ),
            "verdict": _two_proportion_verdict(n1, n2, lower, upper),
        }
    )
    return result


def _summarize(
    rows: list[dict[str, Any]],
    rule_id: str,
    protocol: Mapping[str, Any],
    sample_name: str,
    excluded_ids: frozenset[str],
) -> dict[str, Any]:
    selected = [row for row in rows if row["case_id"] not in excluded_ids]
    metric = score(_metric_cases(selected, rule_id), dict(protocol))
    triggered_rows = [row for row in selected if row["triggered"] is True]
    untriggered_rows = [row for row in selected if row["triggered"] is False]
    n_triggered = len(triggered_rows)
    n_not_evaluated = sum(1 for row in selected if row["triggered"] is None)
    if metric["n_scored"] != n_triggered:
        raise RuntimeError(
            f"{rule_id}/{sample_name}: n_scored={metric['n_scored']} 与 n_triggered={n_triggered} 不一致"
        )

    fail_rows = [
        row for row in selected if row["triggered"] is True and row["outcome"] == "fail"
    ]
    fail_correct = sum(1 for row in fail_rows if row["label"] == "negative")
    two_proportion = _two_proportion(triggered_rows, untriggered_rows)

    return {
        "sample": sample_name,
        "n_total": metric["n_total"],
        "n_triggered": n_triggered,
        "n_scored": metric["n_scored"],
        "n_correct": metric["n_correct"],
        "n_untriggered": len(untriggered_rows),
        "n_not_triggered": metric["n_not_triggered"],
        "n_not_evaluated": n_not_evaluated,
        "n_abstain": metric["n_abstain"],
        "n_missing_answer": metric["n_missing_answer"],
        "trigger_rate": round(n_triggered / metric["n_total"], 4),
        "accuracy": metric["accuracy"],
        "baseline": {
            "letter": metric["baseline_single"]["letter"],
            "hits": metric["baseline_single"]["hits"],
            "accuracy": metric["baseline_single"]["accuracy"],
            "definition": "baseline_single on the same scored set",
            "used_for_decision": False,
        },
        "baseline_same_k": metric["baseline_same_k"],
        "wilson_ci_95": metric["wilson_ci_95"],
        "accuracy_used_for_decision": False,
        "descriptive_metric_note": (
            "claim_metric 的 accuracy / baseline_single / Wilson 只作描述，不作判定："
            "triggered=True 恒预测 N、triggered=False 弃权，scored 集 = 触发集，"
            "accuracy 恒等于触发集负率；N 为多数类时 baseline_single 也是同一负率，"
            "accuracy 恒等于 baseline，「超过基线」分支在数学上不可达（PROMPT §7.2）。"
        ),
        "two_proportion": two_proportion,
        "verdict": two_proportion["verdict"],
        "fail_outcome_subset": {
            "note": "triggered=True 且 outcome=fail；仅描述，不参与判定；仍按 N 计入 claim_metric。",
            "n": len(fail_rows),
            "n_correct": fail_correct,
            "accuracy": round(fail_correct / len(fail_rows), 4) if fail_rows else None,
            "wilson_ci_95": (
                [round(value, 4) for value in _wilson_bounds(fail_correct, len(fail_rows))]
                if fail_rows
                else None
            ),
        },
        "cases": [
            {
                "case_id": row["case_id"],
                "triggered": row["triggered"],
                "outcome": row["outcome"],
                "label": row["label"],
                "prediction_letter": "N" if row["triggered"] is True else None,
            }
            for row in selected
        ],
    }


def _load_protocols() -> dict[str, Mapping[str, Any]]:
    protocols: dict[str, Mapping[str, Any]] = {}
    for rule in RULES:
        path: Path = rule["protocol_path"]
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(document, Mapping):
            raise RuntimeError(f"协议不是映射：{_rel(path)}")
        if document.get("claim_id") != rule["rule_id"]:
            raise RuntimeError(f"协议 claim_id 不匹配：{_rel(path)}")
        if document.get("protocol_id") != rule["protocol_id"]:
            raise RuntimeError(f"协议 protocol_id 不匹配：{_rel(path)}")
        protocols[rule["rule_id"]] = document
    return protocols


# ---------------------------------------------------------------------------
# 产物
# ---------------------------------------------------------------------------

def _build_payload(
    sample: list[dict[str, Any]],
    usable: list[Mapping[str, Any]],
    labels: Mapping[str, Any],
    rows: Mapping[str, list[dict[str, Any]]],
    failures: list[dict[str, str]],
    protocols: Mapping[str, Mapping[str, Any]],
    rules_by_id: Mapping[str, ExecutableClaimRule],
) -> dict[str, Any]:
    present_ids = {item["case_id"] for item in sample}
    excluded_ids = tuple(case_id for case_id in SENSITIVITY_CASE_IDS if case_id in present_ids)
    absent_ids = tuple(case_id for case_id in SENSITIVITY_CASE_IDS if case_id not in present_ids)
    sensitivity_n = EXPECTED_FULL_N - len(excluded_ids)
    if sensitivity_n != EXPECTED_SENSITIVITY_N:
        raise RuntimeError(f"敏感性集应为 {EXPECTED_SENSITIVITY_N}，实为 {sensitivity_n}")

    rule_payloads: list[dict[str, Any]] = []
    for rule in RULES:
        rule_id = rule["rule_id"]
        executable = rules_by_id[rule_id]
        rule_payloads.append(
            {
                "key": rule["key"],
                "rule_id": rule_id,
                "school_id": executable.school_id,
                "task_scope": list(executable.task_scope),
                "protocol_id": rule["protocol_id"],
                "protocol_path": _rel(rule["protocol_path"]),
                "protocol_sha256": _sha256(rule["protocol_path"]),
                "conditions": _describe_conditions(executable.conditions),
                "exclusions": _describe_conditions(executable.exclusions),
                "counter_conditions": _describe_conditions(executable.counter_conditions),
                "full_342": _summarize(
                    rows[rule_id], rule_id, protocols[rule_id], "full_342", frozenset()
                ),
                "sensitivity_336": _summarize(
                    rows[rule_id],
                    rule_id,
                    protocols[rule_id],
                    "sensitivity_336",
                    frozenset(excluded_ids),
                ),
            }
        )

    return {
        "schema": SCHEMA,
        "task": TASK_ID,
        "frozen_at": protocols[RULES[0]["rule_id"]]["frozen_at"],
        "amended_at": protocols[RULES[0]["rule_id"]]["amended_at"],
        "semantics": {
            "trigger": "evaluate_rule(...).triggered is true；只用 triggered",
            "prediction": "triggered=True → N；triggered=False → 弃权（prediction_letters=[]）",
            "outcome": "只作 outcome=fail 子集的描述，不参与触发、计分、筛样（T-152 §9）",
            "decision": (
                "两比例检验：P(negative|triggered) vs P(negative|not triggered)；"
                "差值用 Newcombe 95% CI，p 值用 Fisher 精确检验双侧"
            ),
            "verdict_words": list(VERDICT_WORDS),
            "accuracy_baseline": "claim_metric 的 accuracy / baseline_single 只作描述，不作判定",
        },
        "corpus": {
            "timing_eval_set": {
                "path": _rel(TIMING_PATH),
                "sha256": _sha256(TIMING_PATH),
                "n_usable_for_timing": len(usable),
            },
            "labels": {
                "path": _rel(LABEL_PATH),
                "sha256": _sha256(LABEL_PATH),
                "n_cases": len(labels["cases"]),
            },
            "n_labeled": len(sample),
            "label_counts": dict(sorted(Counter(item["label"] for item in sample).items())),
            "n_unknown_excluded": len(usable) - len(sample),
            "sensitivity_n": sensitivity_n,
            "sensitivity_declared_n": DECLARED_SENSITIVITY_N,
            "sensitivity_excluded_case_ids": list(excluded_ids),
            "sensitivity_absent_case_ids": list(absent_ids),
            "sensitivity_note": SENSITIVITY_NOTE,
        },
        "protocols": {
            rule["protocol_id"]: {
                "path": _rel(rule["protocol_path"]),
                "sha256": _sha256(rule["protocol_path"]),
            }
            for rule in RULES
        },
        "rules": rule_payloads,
        "build_failures": failures,
        "determinism": "无时间戳；case 按 case_id 排序；同一输入两次运行逐字节一致。",
    }


def _fmt_rate(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.4f}"


def _fmt_p(value: float | None) -> str:
    if value is None:
        return "n/a"
    if value < 0.0001:
        return f"{value:.2e}"
    return f"{value:.4f}"


def _decision_row(rule: Mapping[str, Any], summary: Mapping[str, Any]) -> str:
    two = summary["two_proportion"]
    triggered = two["triggered"]
    untriggered = two["not_triggered"]
    ci = two["newcombe_ci95_pp"]
    ci_text = "n/a" if ci is None else f"[{ci[0]:.2f}, {ci[1]:.2f}]"
    diff_text = "n/a" if two["diff_pp"] is None else f"{two['diff_pp']:+.2f}"
    return (
        f"| `{rule['rule_id']}` | {triggered['n']} / {triggered['n_negative']} | "
        f"{triggered['negative_rate']:.4f} | {untriggered['n']} / {untriggered['n_negative']} | "
        f"{untriggered['negative_rate']:.4f} | {diff_text} | {ci_text} | "
        f"{_fmt_p(two['fisher_exact_p_two_sided'])} | **{two['verdict']}** |"
    )


def _descriptive_row(rule: Mapping[str, Any], summary: Mapping[str, Any]) -> str:
    baseline = summary["baseline"]
    ci = summary["wilson_ci_95"]
    return (
        f"| `{rule['rule_id']}` | {summary['sample']} | {summary['n_triggered']} | "
        f"{summary['n_scored']} | {summary['accuracy']:.4f} | "
        f"{baseline['accuracy']:.4f}（{baseline['letter']} {baseline['hits']}/{summary['n_scored']}） | "
        f"[{ci[0]:.4f}, {ci[1]:.4f}] |"
    )


def _render_report(payload: Mapping[str, Any]) -> str:
    corpus = payload["corpus"]
    rules = payload["rules"]
    lines = [
        "# T-154 · 首条产品断语正确性分数（婚姻两条规则）",
        "",
        f"- 任务：`{TASK_ID}`（`tasks/T-154/PROMPT.md`，含 §7 Amendments）",
        "- 性质：**探索性首测**；本报告只给预注册判定词，不作规则成立/不成立的终局裁决。",
        f"- 数据：`{corpus['timing_eval_set']['path']}`（`usable_for_timing=true`，"
        f"{corpus['timing_eval_set']['n_usable_for_timing']} 例）+ "
        f"`{corpus['labels']['path']}`（`label ∈ {{negative, positive}}`，"
        f"{corpus['n_labeled']} 例；unknown {corpus['n_unknown_excluded']} 例不折入）。",
        "- 触发：`evaluate_rule(...).triggered`。**只用 triggered**；`outcome` 不参与触发、"
        "计分与筛样（T-152 §9）。",
        "- 预测：triggered=True → `N`；triggered=False → 弃权（不进 `claim_metric` 分母）。",
        "- 判定（PROMPT §7.2）：两比例检验，比较 `P(negative | triggered)` 与 "
        "`P(negative | not triggered)`；差值（百分点）用 **Newcombe 95% CI**，"
        "p 值用 **Fisher 精确检验双侧**。",
        "- 判定词：任一组 n < 30 → 样本不足；CI 下界 > 0 → 有区分力；CI 上界 < 0 → 反向；"
        "其余 → 无差异 / 样本不足。",
        "- `claim_metric` 的 `accuracy / baseline_single` 仍照报，但**只作描述，不作判定**"
        "（退化证明见 §7）。",
        "",
        "## 1. 样本与分母",
        "",
        "| 项 | 数 |",
        "|---|---:|",
        f"| `usable_for_timing=true` | {corpus['timing_eval_set']['n_usable_for_timing']} |",
        f"| `label ∈ {{negative, positive}}`（主样本） | {corpus['n_labeled']} |",
        f"| negative / positive | {corpus['label_counts']['negative']} / {corpus['label_counts']['positive']} |",
        f"| unknown（排除，不折入） | {corpus['n_unknown_excluded']} |",
        f"| 敏感性集 | {corpus['sensitivity_n']}（卡面原写 {corpus['sensitivity_declared_n']}） |",
        "",
        "## 2. 主结果：两比例检验（342 例）",
        "",
        "| 规则 | 触发组 n / 负 | 触发组负率 | 未触发组 n / 负 | 未触发组负率 | 差值（百分点） | Newcombe 95% CI（pp） | Fisher 双侧 p | 判定 |",
        "|---|---:|---:|---:|---:|---:|---|---:|---|",
    ]
    lines += [_decision_row(rule, rule["full_342"]) for rule in rules]
    lines += [
        "",
        "差值 = 触发组负率 − 未触发组负率；正号表示触发组负面婚姻事件更多。",
        "",
        "## 3. 敏感性（实际 336 例）",
        "",
        f"> {corpus['sensitivity_note']}",
        "",
        f"- 剔除的 case_id（{len(corpus['sensitivity_excluded_case_ids'])} 例）："
        + "、".join(f"`{case_id}`" for case_id in corpus["sensitivity_excluded_case_ids"]),
        f"- 卡面名单中不在 342 的 case_id："
        + "、".join(f"`{case_id}`" for case_id in corpus["sensitivity_absent_case_ids"]),
        "",
        "| 规则 | 触发组 n / 负 | 触发组负率 | 未触发组 n / 负 | 未触发组负率 | 差值（百分点） | Newcombe 95% CI（pp） | Fisher 双侧 p | 判定 |",
        "|---|---:|---:|---:|---:|---:|---|---:|---|",
    ]
    lines += [_decision_row(rule, rule["sensitivity_336"]) for rule in rules]
    flipped = [
        rule["rule_id"]
        for rule in rules
        if rule["full_342"]["verdict"] != rule["sensitivity_336"]["verdict"]
    ]
    lines += [
        "",
        "两套判定是否翻转："
        + (f"**翻转**（{', '.join(flipped)}）→ 按卡面判「标签受限」。" if flipped else "未翻转。"),
        "",
        "## 4. `claim_metric` 描述（**不判定**）",
        "",
        "| 规则 | 样本 | n_triggered | n_scored | accuracy | baseline_single | Wilson 95% |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for rule in rules:
        lines.append(_descriptive_row(rule, rule["full_342"]))
        lines.append(_descriptive_row(rule, rule["sensitivity_336"]))
    lines += [
        "",
        "Worker 在改判据前已看到的两个数保留在此：段派 **55.07%（76/138）**、"
        "杨派 **52.45%（107/204）**。它们等于各自 scored 集的负率，也等于 "
        "`baseline_single`（N 为多数类），因此不能用于「超过基线」判定。",
        "",
        "## 5. 反条件描述（`outcome=fail`；仅描述，不判定）",
        "",
        "这些例已 `triggered=True`，仍按 `N` 计入 `claim_metric`；本表只回答"
        "「若反条件可用会怎样」，不改变任何判定词。",
        "",
        "| 规则 | 样本 | n | n_correct | accuracy | Wilson 95% |",
        "|---|---|---:|---:|---:|---|",
    ]
    for rule in rules:
        for summary in (rule["full_342"], rule["sensitivity_336"]):
            subset = summary["fail_outcome_subset"]
            ci = subset["wilson_ci_95"]
            accuracy_text = (
                "n/a" if subset["accuracy"] is None else f"{subset['accuracy']:.4f}"
            )
            ci_text = "n/a" if ci is None else f"[{ci[0]:.4f}, {ci[1]:.4f}]"
            lines.append(
                f"| `{rule['rule_id']}` | {summary['sample']} | {subset['n']} | "
                f"{subset['n_correct']} | {accuracy_text} | {ci_text} |"
            )
    lines += [
        "",
        "## 6. 已知标签噪声",
        "",
        "T-153 §9 保留的 7 例已知误判：",
        "",
        "| case_id | 类型 | label | 在 342 |",
        "|---|---|---|---|",
        "| `RF-2026-000495` | 否定语境「未结婚」 | positive | 是 |",
        "| `RF-2026-000560` | 否定语境「未结婚」 | positive | 是 |",
        "| `RF-2026-000544` | 第三人称「父母离婚」 | negative | 是 |",
        "| `RF-2026-000528` | 第三人称 | negative | 是 |",
        "| `RF-2026-000845` | 第三人称 | negative | 是 |",
        "| `RF-2026-000947` | 繁体「離婚」 | unknown | **否**（不在 342） |",
        "| `RF-2026-000355` | 繁体「離婚」 | positive | 是 |",
        "",
        "上游已知噪声（T-153 §9）：`RF-2026-000066` 的 positive 实为恋爱；"
        "`RF-2026-000704` 的 negative 实为抑郁文本。模型误差不得全算给断语。",
        "",
        "## 7. 判据退化与改判说明（PROMPT §7.2）",
        "",
        "- 规则是「triggered=True 恒预测 N，否则弃权」，所以 `claim_metric` 的 scored 集 = "
        "触发集，`accuracy` = 触发集负率。",
        "- 当 N 是 scored 集多数类时，`baseline_single` 也是同一个负率 → "
        "`accuracy` 恒等于 `baseline`；「超过基线」分支在数学上不可达。",
        "- 这是尺子对单标签规则退化，不是断语好坏。因此主判定改为两比例检验；"
        "`accuracy / baseline_single / Wilson` 只作描述。",
        "- 改判据的依据是上述恒等式，且在计算未触发组之前登记（PROMPT §7.3）；"
        "不是看到结果后改判据。",
        "",
        "## 8. 逐规则口径与触发",
        "",
    ]
    for rule in rules:
        full = rule["full_342"]
        lines += [
            f"### `{rule['rule_id']}`",
            "",
            f"- 流派 / 任务：{rule['school_id']} / {', '.join(rule['task_scope'])}",
            f"- 正条件：{'；'.join(rule['conditions'])}",
            f"- 排除条件：{'；'.join(rule['exclusions']) or '（无）'}",
            f"- 反条件：{'；'.join(rule['counter_conditions']) or '（无）'}",
            f"- 342：n_evaluated={full['n_total'] - full['n_not_evaluated']}，"
            f"n_triggered={full['n_triggered']}，n_scored={full['n_scored']}，"
            f"n_untriggered={full['n_untriggered']}，n_not_evaluated={full['n_not_evaluated']}，"
            f"n_abstain={full['n_abstain']}，n_missing_answer={full['n_missing_answer']}，"
            f"trigger_rate={full['trigger_rate']:.4f}",
            f"- 336：n_triggered={rule['sensitivity_336']['n_triggered']}，"
            f"n_untriggered={rule['sensitivity_336']['n_untriggered']}，"
            f"verdict={rule['sensitivity_336']['verdict']}",
            "",
        ]
    lines += [
        "### 口径观察（杨派规则，未改规则）",
        "",
        "- 生产上下文（`engine/v5/yang_runner.py:94`）把 `sex` 传为 `male` / `female` 字符串；"
        "规则里的 `sex truthy` 条件与 `sex falsy` 排除对两个非空字符串同真同假，"
        "因此该规则实际未按性别门控（`theory/production/claim-rules-v1.yaml:240-245`）。"
        "本卡沿用 deployed 口径、不改规则，仅记录供后续规则卡裁决。",
        "",
    ]
    lines += [
        "## 9. 复现",
        "",
        "```text",
        ".venv\\Scripts\\python.exe -m tools.product_claim_eval",
        ".venv\\Scripts\\python.exe -m pytest -q",
        "```",
        "",
        f"- 逐例明细：`{_rel(SCORE_PATH)}`（`full_342.cases` 342 行、"
        f"`sensitivity_336.cases` 336 行，均含 case_id / triggered / outcome / label / prediction_letter）。",
        f"- 预注册：`{_rel(RULES[0]['protocol_path'])}`、"
        f"`{_rel(RULES[1]['protocol_path'])}`。",
        f"- 建盘失败 / 段派结构失败：{len(payload['build_failures'])} 例。",
        "- 无时间戳；case 按 case_id 排序；同一输入两次运行逐字节一致。",
        "",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def _print_decision_table(title: str, rules: list[Mapping[str, Any]], key: str) -> None:
    print(title)
    print(
        "rule | trig_n | trig_neg | trig_rate | not_n | not_neg | not_rate | "
        "diff_pp | newcombe_ci_pp | fisher_p | verdict"
    )
    for rule in rules:
        two = rule[key]["two_proportion"]
        triggered = two["triggered"]
        untriggered = two["not_triggered"]
        ci = two["newcombe_ci95_pp"]
        print(
            f"{rule['rule_id']} | {triggered['n']} | {triggered['n_negative']} | "
            f"{triggered['negative_rate']:.4f} | {untriggered['n']} | "
            f"{untriggered['n_negative']} | {untriggered['negative_rate']:.4f} | "
            f"{two['diff_pp']:+.2f} | "
            f"{'n/a' if ci is None else f'[{ci[0]:.2f}, {ci[1]:.2f}]'} | "
            f"{_fmt_p(two['fisher_exact_p_two_sided'])} | {two['verdict']}"
        )


def _print_descriptive_table(title: str, rules: list[Mapping[str, Any]], key: str) -> None:
    print(title)
    print(
        "rule | n_triggered | n_scored | accuracy | baseline | wilson | "
        "（claim_metric 仅描述，不判定）"
    )
    for rule in rules:
        summary = rule[key]
        ci = summary["wilson_ci_95"]
        print(
            f"{rule['rule_id']} | {summary['n_triggered']} | {summary['n_scored']} | "
            f"{summary['accuracy']:.4f} | {summary['baseline']['accuracy']:.4f} | "
            f"[{ci[0]:.4f}, {ci[1]:.4f}]"
        )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    sample, usable, labels = _load_sample()
    registry = load_claim_rule_registry()
    rules_by_id = {rule.rule_id: rule for rule in registry.rules}
    for rule in RULES:
        if rule["rule_id"] not in rules_by_id:
            raise RuntimeError(f"规则文件缺规则：{rule['rule_id']}")
    protocols = _load_protocols()

    rows, failures = _evaluate(sample, rules_by_id)
    payload = _build_payload(sample, usable, labels, rows, failures, protocols, rules_by_id)

    SCORE_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    REPORT_PATH.write_text(_render_report(payload), encoding="utf-8")

    corpus = payload["corpus"]
    print(
        f"{TASK_ID} 产品断语正确性分数。样本 {len(sample)} 例"
        f"（382 usable − {len(usable) - len(sample)} unknown）；"
        f"敏感性 {corpus['sensitivity_n']} 例"
        f"（卡面原写 {DECLARED_SENSITIVITY_N}；947 为 unknown 不在 342）。"
    )
    if failures:
        print(f"警告：建盘/段派结构失败 {len(failures)} 例，详见 JSON。")
    print()
    _print_decision_table(
        f"[342] 判定：两比例检验（{corpus['n_labeled']} 例）", payload["rules"], "full_342"
    )
    print()
    _print_decision_table(
        f"[{corpus['sensitivity_n']}] 判定：两比例检验（敏感性）",
        payload["rules"],
        "sensitivity_336",
    )
    print()
    _print_descriptive_table(
        "[342] claim_metric（仅描述，不判定）", payload["rules"], "full_342"
    )
    print()
    _print_descriptive_table(
        f"[{corpus['sensitivity_n']}] claim_metric（仅描述，不判定）",
        payload["rules"],
        "sensitivity_336",
    )
    print()
    for rule in payload["rules"]:
        subset = rule["full_342"]["fail_outcome_subset"]
        print(
            f"描述（不判定） outcome=fail 子集：{rule['rule_id']} "
            f"n={subset['n']} accuracy={_fmt_rate(subset['accuracy'])}"
        )
    print()
    print(f"已写出：{_rel(SCORE_PATH)}")
    print(f"已写出：{_rel(REPORT_PATH)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
