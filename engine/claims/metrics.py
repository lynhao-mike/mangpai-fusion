"""engine/claims/metrics.py · 断语度量契约 v1（T-150；契约 23 §五.1）。

本模块只做**计分**：输入「预注册协议 + 逐例结果」，输出可复现的分数与基线。
纯函数、无 I/O、无全局状态、不读时钟——同一输入两次调用必须逐字节一致。

口径（写死，跑分中不得改）：

- **scored 集** = `triggered is True` 且 `prediction_letters` 非空，**且**有 `answer_letter`。
  三个排除项各自单列、不静默丢弃：
  `n_not_triggered`（triggered 不是 True）/ `n_abstain`（触发了但预测为空）/
  `n_missing_answer`（触发了且有预测，但没有答案可判分）。
  四者构成 `n_total` 的一个划分。缺答案若计入分母，等于把数据缺陷算成断语错误。
- `correct` = `answer_letter ∈ prediction_letters`。
- `accuracy = n_correct / n_scored`；**`n_scored == 0` 必须抛 `MetricError`**（0/0 不许静默出分）。
- `baseline_single`：scored 集上出现最多的**单个字母**的命中率（并列按字母序）。这是判定基线。
- `baseline_same_k`：每例按预测字母数 `k`，取 scored 集上频率最高的 `k` 个字母（并列按字母序）
  作为常量预测的命中率。**只是乐观参考，不参与判定**（防止「多猜几个字母」占便宜）。
- `wilson_ci_95`：`accuracy` 的 Wilson 95% 区间，保留 4 位小数。
- 未知（`outcome == "unknown"`）在任何情况下都不许折叠成成功或失败：它只影响描述，不改分母。

fail-closed：预注册缺字段、label 未定义、`case_id` 重复、`triggered=False + outcome=fail`
这类违约组合、scored 集为空，一律抛 `MetricError`，由 CLI 以退出码 2 拒绝出分。
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any, Mapping, Optional, Sequence

# 预注册必填字段（一个都不能少；缺任一项即拒绝运行）。
PROTOCOL_FIELDS: tuple[str, ...] = (
    "protocol_id", "claim_id", "frozen_at", "commit",
    "trigger_definition", "direction_rule",
    "label_map", "prediction_rule",
    "scored_set_rule", "baseline", "decision_rule",
)

OUTCOMES: tuple[str, ...] = ("success", "fail", "unknown")
WILSON_Z_95 = 1.959963984540054


class MetricError(ValueError):
    """输入或预注册不合格。调用方必须 fail-closed（CLI 退出码 2），不得静默出分。"""


def _round4(value: float) -> float:
    return round(float(value), 4)


def _letters(value: Any, field: str) -> tuple[str, ...]:
    """字母集：必须是列表/元组（裸字符串含义不明，拒绝）；去空白、大写、去重后排序。"""
    if not isinstance(value, (list, tuple)):
        raise MetricError(f"{field}: 必须是字母列表（不要写裸字符串）")
    letters: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise MetricError(f"{field}: 非法字母 {item!r}")
        letters.append(item.strip().upper())
    return tuple(sorted(set(letters)))


def validate_protocol(protocol: Optional[Mapping[str, Any]]) -> dict[str, Any]:
    """校验预注册并返回规范化副本（不改调用方对象）。缺字段一律抛 `MetricError`。"""
    if not isinstance(protocol, Mapping):
        raise MetricError("protocol 必须是映射（YAML / JSON 对象）")
    missing = [name for name in PROTOCOL_FIELDS if protocol.get(name) in (None, "", [], {})]
    if missing:
        raise MetricError("预注册缺字段：" + ", ".join(missing))

    raw_labels = protocol["label_map"]
    if not isinstance(raw_labels, Mapping) or not raw_labels:
        raise MetricError("label_map 必须是非空映射（标签 -> 字母列表）")
    label_map: dict[str, tuple[str, ...]] = {}
    for label, letters in raw_labels.items():
        if not isinstance(label, str) or not label.strip():
            raise MetricError(f"label_map: 非法标签 {label!r}")
        norm = _letters(letters, f"label_map[{label}]")
        if not norm:
            raise MetricError(f"label_map[{label}]: 字母集为空")
        label_map[label.strip()] = norm

    raw_rule = protocol["prediction_rule"]
    if not isinstance(raw_rule, Mapping) or not raw_rule:
        raise MetricError("prediction_rule 必须是非空映射（分支 -> 标签）")
    prediction_rule: dict[str, str] = {}
    for branch, label in raw_rule.items():
        if not isinstance(branch, str) or not branch.strip():
            raise MetricError(f"prediction_rule: 非法分支 {branch!r}")
        if not isinstance(label, str) or label.strip() not in label_map:
            raise MetricError(
                f"prediction_rule[{branch}]: 标签 {label!r} 不在 label_map 里")
        prediction_rule[branch.strip()] = label.strip()

    return {
        "protocol_id": str(protocol["protocol_id"]),
        "claim_id": str(protocol["claim_id"]),
        "label_map": label_map,
        "prediction_rule": prediction_rule,
    }


def _normalize_cases(cases: Any, protocol: Mapping[str, Any]) -> list[dict[str, Any]]:
    """逐例校验 + 落实「分支 -> 标签 -> 字母集」的预注册方向，最后按 case_id 排序。"""
    if not isinstance(cases, Sequence) or isinstance(cases, (str, bytes)):
        raise MetricError("cases 必须是列表")
    label_map: Mapping[str, tuple[str, ...]] = protocol["label_map"]
    prediction_rule: Mapping[str, str] = protocol["prediction_rule"]

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, Mapping):
            raise MetricError(f"cases[{index}] 不是对象")
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise MetricError(f"cases[{index}] 缺 case_id")
        case_id = case_id.strip()
        if case_id in seen:
            raise MetricError(f"case_id 重复：{case_id}")
        seen.add(case_id)

        branch = case.get("branch")
        if not isinstance(branch, str) or not branch.strip():
            raise MetricError(f"{case_id}: 缺 branch")
        branch = branch.strip()

        triggered = case.get("triggered")
        if "triggered" not in case:
            raise MetricError(f"{case_id}: 缺 triggered 字段（`unknown` 要显式写 null）")
        if triggered is not True and triggered is not False and triggered is not None:
            raise MetricError(f"{case_id}: triggered 只允许 true / false / null")

        outcome = case.get("outcome", "unknown")
        if outcome not in OUTCOMES:
            raise MetricError(f"{case_id}: outcome 只允许 {'/'.join(OUTCOMES)}")
        if triggered is not True and outcome != "unknown":
            # 契约 23 §五.1 硬规则：结构未触发/未知时不许有成败结论。
            raise MetricError(
                f"{case_id}: triggered={triggered!r} 时 outcome 必须为 'unknown'，收到 {outcome!r}")

        raw_pred = case.get("prediction_letters")
        if raw_pred is None:
            label = prediction_rule.get(branch)
            if label is None:
                raise MetricError(
                    f"{case_id}: 缺 prediction_letters，且 branch {branch!r} 不在 prediction_rule 中")
            letters = label_map[label]
        else:
            letters = _letters(raw_pred, f"{case_id}.prediction_letters")

        answer = case.get("answer_letter")
        if answer is not None and not isinstance(answer, str):
            raise MetricError(f"{case_id}: answer_letter 只允许字符串或 null")
        answer = (answer or "").strip().upper() or None

        normalized.append({
            "case_id": case_id,
            "claim_id": case.get("claim_id"),
            "branch": branch,
            "triggered": triggered,
            "outcome": outcome,
            "prediction_letters": letters,
            "answer_letter": answer,
        })

    normalized.sort(key=lambda case: case["case_id"])
    return normalized


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _input_sha256(cases: Sequence[Mapping[str, Any]]) -> str:
    payload = [{
        "case_id": case["case_id"],
        "claim_id": case["claim_id"],
        "branch": case["branch"],
        "triggered": case["triggered"],
        "outcome": case["outcome"],
        "prediction_letters": list(case["prediction_letters"]),
        "answer_letter": case["answer_letter"],
    } for case in cases]
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def wilson_ci_95(correct: int, total: int) -> list[float]:
    """Wilson 95% 置信区间（保留 4 位小数）。`total == 0` 抛错——0/0 无区间可言。"""
    if total <= 0:
        raise MetricError("Wilson 区间需要 total > 0")
    if not 0 <= correct <= total:
        raise MetricError(f"correct={correct} 不在 [0, {total}] 内")
    p = correct / total
    z2 = WILSON_Z_95 ** 2
    denominator = 1.0 + z2 / total
    center = (p + z2 / (2.0 * total)) / denominator
    margin = WILSON_Z_95 * ((p * (1.0 - p) / total + z2 / (4.0 * total * total)) ** 0.5) / denominator
    return [_round4(max(0.0, center - margin)), _round4(min(1.0, center + margin))]


def score(cases: list[dict], protocol: dict) -> dict:
    """按预注册口径计分。返回确定性字典；`n_scored == 0` 抛 `MetricError`。"""
    proto = validate_protocol(protocol)
    normalized = _normalize_cases(cases, proto)

    n_not_triggered = 0
    n_abstain = 0
    n_missing_answer = 0
    scored: list[dict[str, Any]] = []
    for case in normalized:
        if case["triggered"] is not True:
            n_not_triggered += 1
            continue
        if not case["prediction_letters"]:
            n_abstain += 1
            continue
        if case["answer_letter"] is None:
            n_missing_answer += 1
            continue
        scored.append(case)

    n_scored = len(scored)
    if n_scored == 0:
        raise MetricError(
            "scored 集为空（triggered=true 且预测非空且有答案的样本为 0），拒绝 0/0 出分")

    n_correct = sum(1 for case in scored if case["answer_letter"] in case["prediction_letters"])

    # 判定基线：scored 集上出现最多的单个字母；并列按字母序，保证确定性。
    answer_dist = Counter(case["answer_letter"] for case in scored)
    ranked = sorted(answer_dist.items(), key=lambda item: (-item[1], item[0]))
    single_letter, single_hits = ranked[0]
    letter_order = [letter for letter, _ in ranked]

    # 乐观参考：每例按自己的 k，取全局频率最高的 k 个字母当常量预测。
    same_k_hits = 0
    by_k: dict[int, dict[str, Any]] = {}
    for case in scored:
        k = len(case["prediction_letters"])
        top_k = letter_order[:k]
        hit = case["answer_letter"] in top_k
        same_k_hits += int(hit)
        row = by_k.setdefault(k, {"letters": list(top_k), "hits": 0, "n": 0})
        row["n"] += 1
        row["hits"] += int(hit)

    by_branch: dict[str, dict[str, Any]] = {}
    for branch in sorted({case["branch"] for case in normalized}):
        branch_scored = [case for case in scored if case["branch"] == branch]
        branch_correct = sum(
            1 for case in branch_scored if case["answer_letter"] in case["prediction_letters"])
        by_branch[branch] = {
            "n": len(branch_scored),
            "correct": branch_correct,
            "accuracy": (_round4(branch_correct / len(branch_scored))
                         if branch_scored else None),
        }

    return {
        "protocol_id": proto["protocol_id"],
        "claim_id": proto["claim_id"],
        "n_total": len(normalized),
        "n_scored": n_scored,
        "n_correct": n_correct,
        "n_abstain": n_abstain,
        "n_not_triggered": n_not_triggered,
        "n_missing_answer": n_missing_answer,
        "accuracy": _round4(n_correct / n_scored),
        "baseline_single": {
            "letter": single_letter,
            "hits": single_hits,
            "accuracy": _round4(single_hits / n_scored),
        },
        "baseline_same_k": {
            "hits": same_k_hits,
            "accuracy": _round4(same_k_hits / n_scored),
            "by_k": {
                str(k): {
                    "letters": row["letters"],
                    "hits": row["hits"],
                    "n": row["n"],
                    "accuracy": _round4(row["hits"] / row["n"]),
                }
                for k, row in sorted(by_k.items())
            },
        },
        "wilson_ci_95": wilson_ci_95(n_correct, n_scored),
        "by_branch": by_branch,
        "input_sha256": _input_sha256(normalized),
    }


__all__ = [
    "MetricError",
    "OUTCOMES",
    "PROTOCOL_FIELDS",
    "score",
    "validate_protocol",
    "wilson_ci_95",
]
