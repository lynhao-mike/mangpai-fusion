"""tools/claim_metric.py · 断语度量器 CLI（T-150；契约 23 §五.1）。

用法：
    python -m tools.claim_metric --protocol <file> --cases <file> [--json]
    python -m tools.claim_metric --self-check

退出码：
    0 = 正常出分（或 self-check 全部手算断言通过）
    1 = self-check 断言失败（实现与手算值不符）
    2 = fail-closed：文件缺失 / 预注册缺字段 / 违约组合 / scored 集为空

本工具**只计分**：不改断语、不改阈值、不改题；口径由预注册文件冻结。
格式说明见 `META/eval-protocol-v1.md`。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

import yaml

from engine.claims.metrics import MetricError, score


# ─────────────────────────────────────────────────────────────── 加载层

def load_document(path: str | pathlib.Path) -> Any:
    """读 YAML / JSON（JSON 是 YAML 子集，统一走 yaml.safe_load）。"""
    target = pathlib.Path(path)
    if not target.exists():
        raise MetricError(f"文件不存在：{target}")
    if not target.is_file():
        raise MetricError(f"不是文件：{target}")
    text = target.read_text(encoding="utf-8")
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise MetricError(f"无法解析 {target}：{exc}") from exc


def load_cases(path: str | pathlib.Path) -> list[dict]:
    """cases 文件要么是列表，要么是 {"cases": [...]}。"""
    doc = load_document(path)
    if isinstance(doc, dict) and "cases" in doc:
        doc = doc["cases"]
    if not isinstance(doc, list):
        raise MetricError(f"cases 文件必须是列表或 {{\"cases\": [...]}}：{path}")
    return doc


# ─────────────────────────────────────────────────────────────── 输出层

def print_human(result: dict) -> None:
    single = result["baseline_single"]
    same_k = result["baseline_same_k"]
    ci = result["wilson_ci_95"]
    print(f"[claim_metric] protocol={result['protocol_id']} claim={result['claim_id']}")
    print(f"  n_total={result['n_total']}  n_scored={result['n_scored']}  "
          f"n_correct={result['n_correct']}  n_abstain={result['n_abstain']}  "
          f"n_not_triggered={result['n_not_triggered']}  "
          f"n_missing_answer={result['n_missing_answer']}")
    print(f"  accuracy={result['accuracy']:.4f}  "
          f"baseline_single({single['letter']})={single['accuracy']:.4f}  "
          f"baseline_same_k={same_k['accuracy']:.4f}（乐观上界，只作参考）  "
          f"wilson_ci_95=[{ci[0]:.4f}, {ci[1]:.4f}]")
    for branch, row in result["by_branch"].items():
        acc = "n/a" if row["accuracy"] is None else f"{row['accuracy']:.4f}"
        print(f"  by_branch {branch}: {row['correct']}/{row['n']} = {acc}")
    print(f"  input_sha256={result['input_sha256']}")


# ─────────────────────────────────────────────────────────────── self-check

SELF_CHECK_PROTOCOL: dict[str, Any] = {
    "protocol_id": "self-check-v1",
    "claim_id": "SELF-CHECK-01",
    "frozen_at": "2026-10-28T00:00:00+08:00",
    "commit": "self-check",
    "trigger_definition": "triggered=true = 前置条件与框架前置全部成立（结构存在）",
    "direction_rule": "分支 -> 标签 -> 字母集，方向在预注册时冻结，跑分时不得改",
    "label_map": {"wide": ["A", "B"], "single": ["A"]},
    "prediction_rule": {"self_controls": "wide", "attacked": "single"},
    "scored_set_rule": "triggered is true 且 prediction_letters 非空且有答案；缺答案单列不入分母",
    "baseline": "baseline_single 参与判定；baseline_same_k 仅作乐观参考",
    "decision_rule": "accuracy 须严格高于 baseline_single，且 Wilson 下界高于基线才算『超过』",
}

# 覆盖：单字母预测 / 多字母预测 / 弃权 / 未触发 / 缺答案 / 预注册派生字母集。
SELF_CHECK_CASES: list[dict[str, Any]] = [
    {"case_id": "c01", "claim_id": "SELF-CHECK-01", "branch": "self_controls",
     "triggered": True, "outcome": "success", "prediction_letters": ["B"], "answer_letter": "B"},
    {"case_id": "c02", "claim_id": "SELF-CHECK-01", "branch": "self_controls",
     "triggered": True, "outcome": "fail", "prediction_letters": ["A", "B"], "answer_letter": "B"},
    {"case_id": "c03", "claim_id": "SELF-CHECK-01", "branch": "attacked",
     "triggered": True, "outcome": "unknown", "prediction_letters": [], "answer_letter": "A"},
    {"case_id": "c04", "claim_id": "SELF-CHECK-01", "branch": "attacked",
     "triggered": False, "outcome": "unknown", "prediction_letters": ["A"], "answer_letter": "A"},
    {"case_id": "c05", "claim_id": "SELF-CHECK-01", "branch": "attacked",
     "triggered": True, "outcome": "success", "prediction_letters": ["A"], "answer_letter": None},
    {"case_id": "c06", "claim_id": "SELF-CHECK-01", "branch": "attacked",
     "triggered": True, "outcome": "success", "prediction_letters": ["A"], "answer_letter": "C"},
    {"case_id": "c07", "claim_id": "SELF-CHECK-01", "branch": "self_controls",
     "triggered": True, "outcome": "success", "answer_letter": "A"},  # 无 prediction_letters，走预注册派生
]

# 手算值（不是跑完再抄的）：scored = c01/c02/c06/c07 四例，正确 B/B/C/A 中的 3 例。
SELF_CHECK_EXPECTED: dict[str, Any] = {
    "n_total": 7,
    "n_scored": 4,
    "n_correct": 3,
    "n_abstain": 1,          # c03：触发但预测为空
    "n_not_triggered": 1,    # c04：triggered=false，答案 A 不进分母
    "n_missing_answer": 1,   # c05：触发且有预测，但无答案
    "accuracy": 0.75,
    "baseline_single": {"letter": "B", "hits": 2, "accuracy": 0.5},
    "baseline_same_k": {"hits": 3, "accuracy": 0.75},
    "wilson_ci_95": [0.3006, 0.9544],
}


def _check(name: str, actual: Any, expected: Any, problems: list[str]) -> None:
    ok = actual == expected
    print(f"  [{'PASS' if ok else 'FAIL'}] {name} = {actual!r}"
          + ("" if ok else f"  （手算期望 {expected!r}）"))
    if not ok:
        problems.append(name)


def self_check() -> int:
    print("=" * 78)
    print("claim_metric self-check · 内置玩具集手算断言")
    print("=" * 78)
    problems: list[str] = []
    result = score(SELF_CHECK_CASES, SELF_CHECK_PROTOCOL)

    for key in ("n_total", "n_scored", "n_correct", "n_abstain",
                "n_not_triggered", "n_missing_answer", "accuracy"):
        _check(key, result[key], SELF_CHECK_EXPECTED[key], problems)
    _check("baseline_single", result["baseline_single"],
           SELF_CHECK_EXPECTED["baseline_single"], problems)
    _check("baseline_same_k.hits", result["baseline_same_k"]["hits"],
           SELF_CHECK_EXPECTED["baseline_same_k"]["hits"], problems)
    _check("baseline_same_k.accuracy", result["baseline_same_k"]["accuracy"],
           SELF_CHECK_EXPECTED["baseline_same_k"]["accuracy"], problems)
    _check("wilson_ci_95", result["wilson_ci_95"], SELF_CHECK_EXPECTED["wilson_ci_95"], problems)
    _check("by_branch.self_controls", result["by_branch"]["self_controls"],
           {"n": 3, "correct": 3, "accuracy": 1.0}, problems)
    _check("by_branch.attacked", result["by_branch"]["attacked"],
           {"n": 1, "correct": 0, "accuracy": 0.0}, problems)

    # 确定性：同一输入两次运行必须逐字节一致。
    again = score(SELF_CHECK_CASES, SELF_CHECK_PROTOCOL)
    _check("determinism(byte-identical)",
           json.dumps(again, ensure_ascii=False, sort_keys=True),
           json.dumps(result, ensure_ascii=False, sort_keys=True), problems)

    # 0 分母：全部弃权 / 未触发时必须报错，不许 0/0 静默出分。
    empty_cases = [c for c in SELF_CHECK_CASES if c["case_id"] in ("c03", "c04")]
    try:
        score(empty_cases, SELF_CHECK_PROTOCOL)
    except MetricError as exc:
        _check("n_scored==0 raises MetricError", "MetricError", "MetricError", problems)
        print(f"         └ {exc}")
    else:
        _check("n_scored==0 raises MetricError", "no error", "MetricError", problems)

    # 违约组合：triggered=False + outcome=fail 必须拒绝。
    try:
        score([{"case_id": "bad", "branch": "attacked", "triggered": False,
                "outcome": "fail", "prediction_letters": ["A"], "answer_letter": "A"}],
              SELF_CHECK_PROTOCOL)
    except MetricError as exc:
        _check("triggered=False + outcome=fail rejected", "MetricError", "MetricError", problems)
        print(f"         └ {exc}")
    else:
        _check("triggered=False + outcome=fail rejected", "no error", "MetricError", problems)

    # 预注册缺字段必须拒绝。
    broken = dict(SELF_CHECK_PROTOCOL)
    broken.pop("decision_rule")
    try:
        score(SELF_CHECK_CASES, broken)
    except MetricError as exc:
        _check("missing protocol field rejected", "MetricError", "MetricError", problems)
        print(f"         └ {exc}")
    else:
        _check("missing protocol field rejected", "no error", "MetricError", problems)

    print("-" * 78)
    if problems:
        print(f"self-check FAILED：{len(problems)} 项不符 —— {', '.join(problems)}")
        return 1
    print("self-check PASSED：全部手算断言一致")
    return 0


# ─────────────────────────────────────────────────────────────── 入口

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.claim_metric",
        description="按预注册协议给断语评测计分（fail-closed：缺预注册即退出码 2）")
    parser.add_argument("--protocol", help="预注册协议文件（YAML / JSON）")
    parser.add_argument("--cases", help="逐例结果文件（列表或 {\"cases\": [...]}）")
    parser.add_argument("--json", action="store_true", help="只输出机器可读 JSON")
    parser.add_argument("--self-check", action="store_true", help="跑内置玩具集手算断言")
    args = parser.parse_args(argv)

    if args.self_check:
        return self_check()
    if not args.protocol or not args.cases:
        print("[claim_metric] 必须同时提供 --protocol 与 --cases（或使用 --self-check）",
              file=sys.stderr)
        return 2

    try:
        protocol = load_document(args.protocol)
        cases = load_cases(args.cases)
        result = score(cases, protocol)
    except MetricError as exc:
        print(f"[claim_metric] 拒绝出分：{exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_human(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
