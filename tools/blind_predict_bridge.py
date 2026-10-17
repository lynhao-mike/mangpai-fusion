"""tools/blind_predict_bridge.py · 盲断预测 → dual_core_blind 封存 桥接层

为什么需要这个桥
----------------
`engine/evaluation/dual_core_blind.py` 已有完整的封存与规则统计实现，且测试
14 passed。但它要求调用方提供**已经结构化好的 rounds 与 verification_records**：

- `rounds`：每条必须精确含 `case_id/round_index/matter_category/time_scope/
  direction/conclusion/rationale/applied_rules` 八个字段（多一个少一个都报错）
- `verification_records`：结构同 rounds，但**必填非空**（"required at first reveal"）
- `matter_category` 是**单值**参数，一次 seal 只覆盖一个事项

而盲断 agent 的产出是 `predictions.json`（每条预测带 matter_category/time_scope/
direction/event_definition/rule_independent），且**不读 feedback**。

本桥负责三件事：
1. **rounds 构造**：把 predictions.json 按 matter_category 分组，每组生成一条
   round；`conclusion` 取 prediction 文本，`rationale` 取 event_definition +
   prediction_id，`applied_rules` 取 rule_independent。
2. **verification_records 构造**：由**读过反馈的核验者**（本工具的调用方）
   从 feedback.md 提取事件年表，与预测的 time_scope 比对，产出结构同 rounds 的
   核验记录。这一步**只能由知道反馈的人执行**——桥本身不猜。
3. **独立封存**：每个 (案例, 事项) 调一次 `seal_blind_run`，落在
   `META/blind_seals/<case>/<matter>.json`。

信息隔离边界
------------
本工具**不读取 blind-bundle 内的任何文件**，只读：
- `blind-bundle/<case>/predictions.json`（盲断者产出，不含反馈）
- `cases/<case>/feedback.md`（核验者专用，**桥的调用方必须确认自己不是盲断者**）

CLI
---
    # 预览：某案例某事项的 rounds / verification_records
    python -m tools.blind_predict_bridge inspect \
        --case C-2026-RF000441-乾-... --matter career

    # 封存（需先有 predictions.json）
    python -m tools.blind_predict_bridge seal \
        --case C-2026-RF000441-乾-... --matter career \
        --revealed-at 2026-10-18T00:00:00Z
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.evaluation.dual_core_blind import (  # noqa: E402
    compute_rule_review_statistics,
    seal_blind_run,
)

BUNDLE = ROOT / ".workbuddy-ai" / "blind-bundle"
SEALS_ROOT = ROOT / "META" / "blind_seals"
MATTERS = ("career", "wealth", "marriage", "health", "education", "family")

# 事件年表行：| 2013 | 结婚 | marriage |
_EVENT_ROW = re.compile(r"^\|\s*(\d{4})\s*\|\s*(.+?)\s*\|\s*([^|]*)\|")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_seal_path(case_id: str, matter: str) -> Path:
    """dual_core_blind 强制：<admitted_root>/.dual-core-blind-seals/<sha256(case_id)>.json

    注意：它的 canonical path **不含 matter 维度**——一个案例只有一个封存文件。
    因此本桥对同一案例的多个 matter 采用「同一次 seal 调用、rounds 覆盖全部事项」，
    而不是每 matter 一个文件。matter 参数保留用于日志与幂等判断。
    """
    case_digest = hashlib.sha256(case_id.encode("utf-8")).hexdigest()
    return SEALS_ROOT / ".dual-core-blind-seals" / f"{case_digest}.json"


# ── 读盲断产出 ──────────────────────────────────────────────────────────────

def load_predictions(case_id: str) -> dict[str, Any]:
    p = BUNDLE / case_id / "predictions.json"
    if not p.exists():
        raise FileNotFoundError(f"盲断产出不存在: {p}")
    return json.loads(p.read_text(encoding="utf-8-sig"))


def build_rounds(case_id: str, matter: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    """把 predictions.json 里属某事项的预测转成一条 round。"""
    preds = [
        p for p in payload.get("predictions", [])
        if p.get("matter_category") == matter
    ]
    if not preds:
        return []

    conclusions = "；".join(
        f"[{p['prediction_id']}] {p['prediction']}" for p in preds
    )
    rationale = "；".join(
        f"[{p['prediction_id']}] 事件定义: {p['event_definition']}"
        f"（时段 {p['time_scope']}，方向 {p['direction']}）"
        for p in preds
    )
    # dual_core_blind._validate_round:78-86 禁止同一 round 内同一 rule_id
    # 出现冲突方向。盲断 agent 可能把同一条规则同时用于正反两面的不同预测
    # （实测 RF000243 婚姻事项的 MP-05 即如此）。语义上该规则并未单向成立，
    # 故合并为 mixed——这也使 compute_rule_review_statistics 的
    # direction_opposed 判定为 False，不会被错误计入"被推翻"。
    seen_dirs: dict[str, set[str]] = {}
    for p in preds:
        for r in p.get("rule_independent", []):
            seen_dirs.setdefault(r["rule_id"], set()).add(r["rule_direction"])

    applied_rules = []
    emitted: set[str] = set()
    conflicts: list[str] = []
    for p in preds:
        for r in p.get("rule_independent", []):
            rid = r["rule_id"]
            if rid in emitted:
                continue
            emitted.add(rid)
            dirs = seen_dirs[rid]
            if len(dirs) > 1:
                conflicts.append(f"{rid}{sorted(dirs)}")
                direction = "mixed"
            else:
                direction = next(iter(dirs))
            applied_rules.append({
                "rule_id": rid,
                "school": _school_of(rid),
                "rule_direction": direction,
                "rule_statement": r["rule_statement"],
            })
    if conflicts:
        print(
            f"  NOTE {case_id}/{matter}: 同一规则被双向引用，已合并为 mixed："
            f"{', '.join(conflicts)}",
            file=sys.stderr,
        )

    return [{
        "case_id": case_id,
        "round_index": 1,
        "matter_category": matter,
        "time_scope": _merge_scope([p["time_scope"] for p in preds]),
        "direction": _merge_direction([p["direction"] for p in preds]),
        "conclusion": conclusions,
        "rationale": rationale,
        "applied_rules": applied_rules,
    }]


# 盲断 agent 自建规则命名空间 → 学派归属。
# 盲测铁律禁止检索理论语料，故 agent 不引用 theory registry ID；
# 但它自建的规则族（MP/ZP/TH/GW/DY）对应明确的流派渊源，这里显式映射，
# 避免 dual_core_blind 收到 "unknown" 导致学派维度统计失真。
ANALYST_NAMESPACE_SCHOOL = {
    "MP": "mangpai_fusion",   # 四派融合自主规则
    "ZP": "ziping",
    "TH": "tiaohou_ditiansui",
    "GW": "gao",
    "DY": "duan",
    "YR": "yang",
    "RN": "ren",
}


def _school_of(rule_id: str) -> str:
    prefix = rule_id.split("-", 1)[0].upper()
    if prefix in ANALYST_NAMESPACE_SCHOOL:
        return ANALYST_NAMESPACE_SCHOOL[prefix]
    return {
        "M1": "duan", "M2": "yang", "M3": "ren", "G": "gao",
        "ZP": "ziping", "DTS": "ditiansui", "QT": "ziping",
    }.get(prefix, "unknown")


def _merge_scope(scopes: list[str]) -> str:
    years: list[int] = []
    for s in scopes:
        years.extend(int(y) for y in re.findall(r"\d{4}", s))
    if not years:
        return scopes[0] if scopes else "unknown"
    return f"{min(years)}-{max(years)}"


def _merge_direction(directions: list[str]) -> str:
    uniq = {d for d in directions if d in ("positive", "negative", "mixed")}
    if len(uniq) == 1:
        return uniq.pop()
    return "mixed"


# ── 核验记录（只由知道反馈的人生成）────────────────────────────────────────

def load_feedback_events(case_id: str) -> list[dict[str, Any]]:
    """从 cases/<case>/feedback.md 提取事件年表。"""
    p = ROOT / "cases" / case_id / "feedback.md"
    if not p.exists():
        return []
    events = []
    for line in p.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        m = _EVENT_ROW.match(line.strip())
        if not m:
            continue
        year, text, domains = m.groups()
        events.append({
            "year": int(year),
            "text": text.strip(),
            "domains": [d.strip() for d in domains.split(",") if d.strip()],
        })
    return events


_MATTER_KEYWORDS = {
    "career": ["工作", "事业", "职业", "升", "岗", "跳", "创业", "单位", "公司", "职", "调动"],
    "wealth": ["财", "钱", "收入", "赚", "破财", "负债", "投资", "生意", "款"],
    "marriage": ["婚", "恋", "妻", "夫", "对象", "感情", "离婚", "结婚", "分手", "同居"],
    "health": ["病", "医", "手术", "健康", "伤", "住院", "癌", "体检", "痛"],
    "education": ["学", "考", "大学", "毕业", "学历", "升学", "录取"],
    "family": ["父", "母", "子", "女", "兄", "弟", "姐", "妹", "家人", "亲", "产"],
}


def build_verification_records(
    case_id: str, matter: str, rounds: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """构造 verification_records。

    口径（blind-scoring/v1）：把 feedback 中落在 round.time_scope 内、
    且事项相关的事件写成一条核验记录。**没有匹配事件 ≠ 事件未发生**——
    此种情况记 direction 为 mixed 并在 rationale 明说"反馈未提供",
    由 compute_rule_review_statistics 的调用方决定是否计入分母。
    """
    if not rounds:
        return []
    rnd = rounds[0]
    scope_years = [int(y) for y in re.findall(r"\d{4}", rnd["time_scope"])]
    lo, hi = (min(scope_years), max(scope_years)) if scope_years else (0, 9999)
    kws = _MATTER_KEYWORDS.get(matter, [])

    matched = [
        e for e in events
        if lo <= e["year"] <= hi
        and (any(k in e["text"] for k in kws)
             or any(k in " ".join(e["domains"]) for k in kws))
    ]

    if matched:
        conclusion = "；".join(f"{e['year']}: {e['text']}" for e in matched)
        rationale = (
            f"反馈在时段 {rnd['time_scope']} 内提供 {len(matched)} 条{matter}相关事件；"
            "逐条核对见 evidence。"
        )
        direction = "mixed"
    else:
        conclusion = f"反馈未在 {rnd['time_scope']} 内提供{matter}相关事件"
        rationale = (
            "按 blind-scoring/v1：反馈未提及 ≠ 事件未发生。"
            "本记录不进正确率分母（undetermined）。"
        )
        direction = "mixed"

    return [{
        "case_id": case_id,
        "round_index": rnd["round_index"] + 1,
        "matter_category": matter,
        "time_scope": rnd["time_scope"],
        "direction": direction,
        "conclusion": conclusion,
        "rationale": rationale,
        "applied_rules": [],
    }]


# ── inspect / seal ─────────────────────────────────────────────────────────

def cmd_inspect(case_id: str, matter: str) -> int:
    payload = load_predictions(case_id)
    rounds = build_rounds(case_id, matter, payload)
    if not rounds:
        print(f"{case_id} / {matter}: 无预测")
        return 0
    events = load_feedback_events(case_id)
    ver = build_verification_records(case_id, matter, rounds, events)

    print(f"=== {case_id} / {matter} ===")
    print(f"盲断预测条数（该事项）：{len([p for p in payload.get('predictions', []) if p.get('matter_category') == matter])}")
    print(f"feedback 事件总数：{len(events)}")
    print()
    print("--- rounds（将封存）---")
    print(json.dumps(rounds, ensure_ascii=False, indent=2))
    print()
    print("--- verification_records（核验者生成）---")
    print(json.dumps(ver, ensure_ascii=False, indent=2))
    print()
    print("--- 规则统计预览（未核验时 reversal 为空）---")
    try:
        stats = compute_rule_review_statistics(rounds=rounds, independent_rule_outcomes=[])
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    except (ValueError, TypeError) as exc:
        print(f"  （统计暂不可用：{exc}）")
    return 0


def cmd_seal(case_id: str, revealed_at: str) -> int:
    """按事项逐次封存。

    `dual_core_blind` 有两条互相咬合的硬约束：
      1. `_validate_round` 要求每条 round 的 matter_category 与 seal 的
         matter_category **完全一致** → 一次 seal 只能覆盖一个事项；
      2. canonical path 是 `<root>/.dual-core-blind-seals/<sha256(case_id)>.json`，
         **不含 matter 维度**。

    解法：把 `"{case_id}#{matter}"` 作为传给 seal_blind_run 的 case_id。
    这样 path 由该复合 ID 唯一决定（不冲突），round 的 matter 也与 seal 一致。
    复合 ID 记入 payload 的 case_id 字段，事后可还原原始案例。
    """
    payload = load_predictions(case_id)
    ok = skip = 0
    sealed_any = False

    for matter in MATTERS:
        rounds = build_rounds(case_id, matter, payload)
        if not rounds:
            continue
        sealed_any = True

        seal_case_id = f"{case_id}#{matter}"
        out = _canonical_seal_path(seal_case_id, matter)
        if out.exists():
            skip += 1
            print(f"SKIP {case_id}/{matter}: 封存已存在")
            continue

        # rounds 与 verification 的 case_id 都必须与 seal 的复合 ID 一致
        # （dual_core_blind._validate_round 逐条比对）
        for rnd in rounds:
            rnd["case_id"] = seal_case_id
        events = load_feedback_events(case_id)
        ver = build_verification_records(case_id, matter, rounds, events)
        for v in ver:
            v["case_id"] = seal_case_id

        try:
            ref = seal_blind_run(
                case_id=seal_case_id,
                matter_category=matter,
                rounds=rounds,
                verification_records=ver,
                expected_round_count=len(rounds),
                revealed_at=revealed_at,
                output_path=out,
                admitted_root=SEALS_ROOT,
            )
        except (ValueError, TypeError) as exc:
            print(f"ERROR {case_id}/{matter}: {exc}", file=sys.stderr)
            return 1

        n_rules = len(rounds[0]["applied_rules"])
        ok += 1
        print(f"OK {case_id}/{matter}  rules={n_rules}  seal={Path(ref.artifact_path).name}")

    if not sealed_any:
        print(f"SKIP {case_id}: 无任何事项的预测")
        return 0
    print(f"  → {case_id}: sealed={ok} skipped={skip}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ins = sub.add_parser("inspect")
    p_ins.add_argument("--case", required=True)
    p_ins.add_argument("--matter", required=True, choices=list(MATTERS))

    p_seal = sub.add_parser("seal", help="封存该案例全部事项（一次调用）")
    p_seal.add_argument("--case", required=True)
    p_seal.add_argument("--revealed-at", required=True)

    args = parser.parse_args(argv)
    if args.cmd == "inspect":
        return cmd_inspect(args.case, args.matter)
    if args.cmd == "seal":
        return cmd_seal(args.case, args.revealed_at)
    return 2


if __name__ == "__main__":
    sys.exit(main())
