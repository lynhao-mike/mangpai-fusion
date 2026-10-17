"""tools/blind_ledger.py · 盲测封存与反馈对账（L1：封存 + 对账）

设计原则（避免重蹈 L0~L9 过度设计覆辙）
--------------------------------------
本工具只做三件事，没有状态机、没有阶段流转、没有门禁：

1. **封存（seal）**：对分析报告的文本与解析出的 claims 做 sha256，写不可变快照。
2. **对账（reveal）**：录入真实反馈后，逐条给 claim 记 verdict。
3. **统计（stats）**：纯函数式汇总，不存新状态。

双模式
------
- `consult`（普通咨询）：已知事实可用，**永久不标盲测**，只做归档。
- `blind`（严格盲测）：未读反馈前完成分析并封存；封存后才允许 reveal。

铁律
----
- 封存后的 rounds 内容**不可修改**；更正只能新增 round 或新增 outcome 版本。
- 本工具**永不修改规则库**；只输出统计与待审标记。
- claims **不手填**，从 v7 报告文末《附：关键依据索引与可核验断语表》机械解析。

CLI
---
    python -m tools.blind_ledger seal --case C-2026-001-乾-... --report <file.md> --mode blind
    python -m tools.blind_ledger reveal --case <case_id> --round 1 --feedback <file.md>
    python -m tools.blind_ledger adjudicate --case <case_id> --round 1 --claim 1 --verdict hit --evidence "..."
    python -m tools.blind_ledger stats [--rule M1-D-045] [--matter career]
    python -m tools.blind_ledger show --case <case_id>

存储
----
`META/blind_ledger/<case_id>.json`，单文件单案例，无跨案例状态。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LEDGER_DIR = ROOT / "META" / "blind_ledger"
SCHEMA_VERSION = "blind-ledger/v1"

# 《附》表格列：序号 | 报告章节 | 核心断语摘要 | 等级 | 盘面地址与边号 | 理论条目 ID 与出处
_FULU_HEADER = re.compile(r"^\|\s*序号\s*\|\s*报告章节")
_ADDR_RE = re.compile(r"\b(?:[YMDH]|DY\d+|LN\d{4})\.[sb]\b")
_EDGE_RE = re.compile(r"\be\d{3}\b")
# 规则 ID 两段式（学院-编号）与三段式（学院-子类-编号）。
# 关键：第一段必须允许字母+数字（M1/M2/M3/G/ZP/DTS/QT），否则 M1-D-045 匹配不到。
# 负向前瞻排除纯数字（如 1986-07-31、2026-07-15）。
_RULE_RE = re.compile(
    r"\b(?=[A-Z0-9-]*[A-Z])[A-Z0-9]{1,8}-[A-Z0-9]{1,8}-(?:[A-Z0-9]{1,8}-)?\d{2,}\b"
)
_RULE_CN_RE = re.compile(r"\b[A-Z]{1,4}-[甲乙丙丁戊己庚辛壬癸]-[子丑寅卯辰巳午未申酉戌]\b")

VERDICTS = ("hit", "miss", "partial", "unverifiable")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── 从 v7 报告解析 claims ───────────────────────────────────────────────────

def _split_row(line: str) -> list[str]:
    parts = line.strip().strip("|").split("|")
    return [p.strip() for p in parts]


def parse_claims(report_text: str) -> list[dict[str, Any]]:
    """从 v7 报告文末《附：关键依据索引与可核验断语表》机械解析断语。

    解析失败（找不到表格）时返回空列表——调用方必须显式处理，
    不允许静默产出一份"零 claim"的封存。
    """
    lines = report_text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if _FULU_HEADER.search(ln):
            start = i
            break
    if start is None:
        return []

    # 跳过分隔行
    body_start = start + 1
    while body_start < len(lines) and set(
        lines[body_start].strip().replace("|", "").replace("-", "")
    ) <= {""}:
        body_start += 1

    claims: list[dict[str, Any]] = []
    for ln in lines[body_start:]:
        if not ln.strip().startswith("|"):
            break
        cells = _split_row(ln)
        if len(cells) < 6:
            continue
        seq_raw, section, assertion, grade, addrs_raw, rules_raw = cells[:6]
        if not re.match(r"^\d+$", seq_raw):
            continue
        addrs = _ADDR_RE.findall(addrs_raw) + _EDGE_RE.findall(addrs_raw)
        rules = _RULE_RE.findall(rules_raw) + _RULE_CN_RE.findall(rules_raw)
        claims.append({
            "claim_id": f"seq:{seq_raw}",
            "seq": int(seq_raw),
            "section": section,
            "assertion": assertion,
            "grade": grade,
            "addrs": sorted(set(addrs)),
            "edges": sorted(set(_EDGE_RE.findall(addrs_raw))),
            "rule_ids": sorted(set(rules)),
        })
    return claims


# ── 存储 ────────────────────────────────────────────────────────────────────

def _ledger_path(case_id: str) -> Path:
    safe = re.sub(r"[^\w\-.一-龥]", "_", case_id)
    return LEDGER_DIR / f"{safe}.json"


def load_ledger(case_id: str) -> dict[str, Any]:
    p = _ledger_path(case_id)
    if not p.exists():
        return {
            "schema_version": SCHEMA_VERSION,
            "case_id": case_id,
            "mode": None,
            "rounds": [],
            "reveal": None,
            "created_at": _now(),
        }
    return json.loads(p.read_text(encoding="utf-8-sig"))


def save_ledger(case_id: str, data: dict[str, Any]) -> Path:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    p = _ledger_path(case_id)
    data["updated_at"] = _now()
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


# ── seal ────────────────────────────────────────────────────────────────────

def cmd_seal(case_id: str, report: Path, mode: str, round_no: int | None,
             sources: list[str] | None = None) -> int:
    if mode not in ("blind", "consult"):
        print(f"ERROR: mode 必须是 blind 或 consult，得到 {mode!r}", file=sys.stderr)
        return 2
    if not report.exists():
        print(f"ERROR: 报告文件不存在: {report}", file=sys.stderr)
        return 2

    text = report.read_text(encoding="utf-8-sig", errors="replace")
    claims = parse_claims(text)
    if not claims:
        print(
            "ERROR: 未能从报告解析出任何 claim。v7 报告必须含文末"
            "《附：关键依据索引与可核验断语表》。拒绝产出零 claim 封存。",
            file=sys.stderr,
        )
        return 2

    # 盲测模式必须声明依赖来源。这不是形式主义：工具无法验证"封存前真的
    # 没读过反馈"，只能把声明写进不可变快照，供事后审计。若声明里出现
    # feedback / 反馈 / 事件年表 / analysis.md 等字样，说明封存前很可能
    # 已接触反馈，此时按 blind 封存会污染准确率基线——拒绝并要求人工确认。
    declared = sources or []
    if mode == "blind":
        suspicious = [
            s for s in declared
            if re.search(r"feedback|反馈|事件年表|analysis\.md|known_facts", s, re.I)
        ]
        if suspicious:
            print(
                "ERROR: blind 封存的依赖来源中出现了疑似反馈材料：\n  "
                + "\n  ".join(suspicious)
                + "\n封存前若已读反馈，本报告不是盲测产物，按 blind 封存会污染准确率基线。",
                file=sys.stderr,
            )
            print(
                "  若确认未读反馈内容、仅参考了其文件结构，请用 --sources 明确写出"
                "实际参考的材料；否则请改用 --mode consult。",
                file=sys.stderr,
            )
            return 2

    data = load_ledger(case_id)
    if data["mode"] and data["mode"] != mode:
        print(f"ERROR: 该案例 mode 已固定为 {data['mode']}，不能改为 {mode}", file=sys.stderr)
        return 2
    data["mode"] = mode

    seq = round_no or (len(data["rounds"]) + 1)
    for r in data["rounds"]:
        if r["seq"] == seq:
            print(f"ERROR: round {seq} 已封存，不可覆盖。请用新 round 号。", file=sys.stderr)
            return 2

    data["rounds"].append({
        "seq": seq,
        "sealed_at": _now(),
        "report_file": str(report),
        "report_sha256": _sha256(text),
        "claims_sha256": _sha256(json.dumps(claims, ensure_ascii=False, sort_keys=True)),
        "claims": claims,
        "declared_sources": declared,
    })
    data["rounds"].sort(key=lambda r: r["seq"])
    p = save_ledger(case_id, data)
    print(f"OK: {case_id} round {seq} 已封存（mode={mode}，{len(claims)} claims）")
    print(f"    report_sha256 = {data['rounds'][-1]['report_sha256']}")
    print(f"    ledger = {p}")
    return 0


# ── reveal ──────────────────────────────────────────────────────────────────

def cmd_reveal(case_id: str, feedback: Path) -> int:
    data = load_ledger(case_id)
    if not data["rounds"]:
        print("ERROR: 该案例尚未封存任何 round", file=sys.stderr)
        return 2
    if data["mode"] != "blind":
        print(f"ERROR: mode={data['mode']} 不是 blind，不需要 reveal 流程", file=sys.stderr)
        return 2
    if not feedback.exists():
        print(f"ERROR: 反馈文件不存在: {feedback}", file=sys.stderr)
        return 2

    if data.get("reveal"):
        print("ERROR: 已 reveal，不可重复揭示（防止反复读反馈改结论）", file=sys.stderr)
        return 2

    text = feedback.read_text(encoding="utf-8-sig", errors="replace")
    data["reveal"] = {
        "revealed_at": _now(),
        "feedback_file": str(feedback),
        "feedback_sha256": _sha256(text),
        "outcomes": [],
    }
    p = save_ledger(case_id, data)
    print(f"OK: {case_id} 已揭示反馈，现在可以 adjudicate 逐条对账")
    print(f"    待对账 claim 数：{sum(len(r['claims']) for r in data['rounds'])}")
    print(f"    ledger = {p}")
    return 0


# ── adjudicate ──────────────────────────────────────────────────────────────

def cmd_adjudicate(
    case_id: str, round_no: int, claim_id: str, verdict: str,
    evidence: str, rule_id: str | None,
) -> int:
    if verdict not in VERDICTS:
        print(f"ERROR: verdict 必须是 {VERDICTS} 之一", file=sys.stderr)
        return 2
    data = load_ledger(case_id)
    if not data.get("reveal"):
        print("ERROR: 尚未 reveal，不能对账", file=sys.stderr)
        return 2

    target_round = next((r for r in data["rounds"] if r["seq"] == round_no), None)
    if target_round is None:
        print(f"ERROR: round {round_no} 不存在", file=sys.stderr)
        return 2
    claim = next((c for c in target_round["claims"] if c["claim_id"] == claim_id), None)
    if claim is None:
        print(f"ERROR: round {round_no} 无 claim {claim_id}", file=sys.stderr)
        return 2

    outcomes = data["reveal"]["outcomes"]
    existing = next(
        (o for o in outcomes if o["round_seq"] == round_no and o["claim_id"] == claim_id), None
    )
    if existing:
        print(f"ERROR: {claim_id} 已对账为 {existing['verdict']}；如需更正请用 --amend", file=sys.stderr)
        return 2

    outcomes.append({
        "round_seq": round_no,
        "claim_id": claim_id,
        "verdict": verdict,
        "evidence": evidence,
        "rule_id": rule_id or (claim["rule_ids"][0] if claim["rule_ids"] else None),
        "adjudicated_at": _now(),
        "version": 1,
    })
    p = save_ledger(case_id, data)
    print(f"OK: {case_id} r{round_no} {claim_id} → {verdict}")
    print(f"    ledger = {p}")
    return 0


# ── stats ───────────────────────────────────────────────────────────────────

def _iter_outcomes() -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    if not LEDGER_DIR.exists():
        return
    for p in sorted(LEDGER_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        if not data.get("reveal"):
            continue
        rounds = {r["seq"]: r for r in data.get("rounds", [])}
        for o in data["reveal"]["outcomes"]:
            rnd = rounds.get(o["round_seq"])
            if rnd is None:
                continue
            claim = next((c for c in rnd["claims"] if c["claim_id"] == o["claim_id"]), None)
            if claim is None:
                continue
            yield data["case_id"], claim, o


def cmd_stats(rule_filter: str | None, matter_filter: str | None) -> int:
    case_total = 0
    case_hit = 0
    rule_stats: dict[str, dict[str, int]] = {}

    for case_id, claim, outcome in _iter_outcomes():
        if matter_filter and matter_filter not in (claim.get("section") or ""):
            continue
        case_total += 1
        if outcome["verdict"] == "hit":
            case_hit += 1
        rid = outcome.get("rule_id")
        if rid and (not rule_filter or rid == rule_filter):
            s = rule_stats.setdefault(rid, {
                "n_hit": 0, "n_miss": 0, "n_partial": 0, "n_unverifiable": 0
            })
            key = {"hit": "n_hit", "miss": "n_miss",
                   "partial": "n_partial", "unverifiable": "n_unverifiable"}[outcome["verdict"]]
            s[key] += 1

    print(f"=== 案例级准确率（以封存 round 的 claim 为单位） ===")
    print(f"  已对账 claim 数：{case_total}")
    print(f"  hit：{case_hit}  miss：{case_total - case_hit}")
    if case_total:
        print(f"  准确率：{case_hit / case_total * 100:.1f}%")

    print()
    print(f"=== 规则级命中率 ===")
    if not rule_stats:
        print("  （无数据）")
    for rid in sorted(rule_stats):
        s = rule_stats[rid]
        n = sum(s.values())
        print(f"  {rid:32s} n={n:4d}  hit={s['n_hit']:4d}  "
              f"miss={s['n_miss']:4d}  partial={s['n_partial']:3d}  "
              f"unver={s['n_unverifiable']:3d}  命中率={s['n_hit']/n*100:.1f}%")

    print()
    print("  说明：本工具只做统计，永不修改规则库。规则修改须命理师确认。")
    return 0


# ── show ────────────────────────────────────────────────────────────────────

def cmd_show(case_id: str) -> int:
    p = _ledger_path(case_id)
    if not p.exists():
        print(f"ERROR: 无该案例 ledger: {p}", file=sys.stderr)
        return 2
    print(p.read_text(encoding="utf-8-sig"))
    return 0


# ── CLI ─────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.blind_ledger",
        description="盲测封存与反馈对账（L1）",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_seal = sub.add_parser("seal", help="封存一轮分析与 claims")
    p_seal.add_argument("--case", required=True)
    p_seal.add_argument("--report", type=Path, required=True)
    p_seal.add_argument("--mode", required=True, choices=["blind", "consult"])
    p_seal.add_argument("--round", type=int, default=None)
    p_seal.add_argument(
        "--sources", nargs="*", default=[],
        help="本 round 实际参考过的材料路径（blind 模式必填；出现 feedback/analysis.md "
             "等字样会被拒绝，防止把非盲产物封成盲测）",
    )

    p_reveal = sub.add_parser("reveal", help="揭示真实反馈（blind 模式）")
    p_reveal.add_argument("--case", required=True)
    p_reveal.add_argument("--feedback", type=Path, required=True)

    p_adj = sub.add_parser("adjudicate", help="逐条对账")
    p_adj.add_argument("--case", required=True)
    p_adj.add_argument("--round", type=int, required=True)
    p_adj.add_argument("--claim", required=True)
    p_adj.add_argument("--verdict", required=True, choices=list(VERDICTS))
    p_adj.add_argument("--evidence", required=True)
    p_adj.add_argument("--rule", default=None)

    p_stats = sub.add_parser("stats", help="统计准确率与规则命中率")
    p_stats.add_argument("--rule", default=None)
    p_stats.add_argument("--matter", default=None)

    p_show = sub.add_parser("show", help="查看某案例 ledger")
    p_show.add_argument("--case", required=True)

    args = parser.parse_args(argv)

    if args.cmd == "seal":
        return cmd_seal(args.case, args.report, args.mode, args.round, args.sources)
    if args.cmd == "reveal":
        return cmd_reveal(args.case, args.feedback)
    if args.cmd == "adjudicate":
        return cmd_adjudicate(
            args.case, args.round, args.claim, args.verdict, args.evidence, args.rule
        )
    if args.cmd == "stats":
        return cmd_stats(args.rule, args.matter)
    if args.cmd == "show":
        return cmd_show(args.case)
    return 2


if __name__ == "__main__":
    sys.exit(main())
