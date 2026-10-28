"""tools/m2y395_real_score.py · T-155：并入「婚姻质量」标签并计分（342 / 敏感性两套）。

职责分工（``tasks/T-155/PROMPT.md`` §2.1–§2.2）：
  - ``tools/m2y395_real_direction.py`` 只出方向，不读标签；
  - 本文件按 ``case_id`` 并入 ``META/marriage-quality-labels-v1.json``，产出
    ``META/m2y395-v2-scored.json``，并用 ``META/eval-protocols/m2y395-v2.yaml`` 跑
    ``engine.claims.metrics.score``（与 ``python -m tools.claim_metric`` 同一实现）。

预注册口径（卡内 §1，不得改）：
  - 样本 = label ∈ {negative, positive} 的 342 例；40 例 unknown 不折入分母；
  - answer_letter：negative → ``N``，positive → ``P``；
  - self_controls → 预测 ``P``；other_controls → 预测 ``N``；no_ke / ambiguous → 弃权；
  - 基线 = 同一 scored 集上的 baseline_single；判据 = Wilson 95% 区间 + 硬门槛 n_scored ≥ 50；
  - 敏感性 = 剔除 T-153 §9 列名的 7 例已知误判后重算；两套结论翻转 → 「标签不足以裁决」。

用法：``.venv\\Scripts\\python.exe -m tools.m2y395_real_score``
退出码：0 = 两套都出分并写出产物；1 = 结构性问题（标签缺失 / 无可计分例 / 预注册缺字段）。
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from collections import Counter
from typing import Any

import yaml

from engine.claims.metrics import MetricError, score

ROOT = pathlib.Path(__file__).resolve().parents[1]
CASES = ROOT / "META" / "m2y395-v2-cases.json"
LABELS = ROOT / "META" / "marriage-quality-labels-v1.json"
PROTOCOL = ROOT / "META" / "eval-protocols" / "m2y395-v2.yaml"
OUT = ROOT / "META" / "m2y395-v2-scored.json"
REPORT = ROOT / "META" / "m2y395-v2-report.md"

CLAIM_ID = "M2-Y-395"
LABEL_TO_LETTER = {"negative": "N", "positive": "P"}
SCORED_LABELS = tuple(LABEL_TO_LETTER)
MIN_SCORED = 50

# tasks/T-153/PROMPT.md §9：7 例已知误判（名单即预注册，不许增删）。
SENSITIVITY_EXCLUDE = (
    "RF-2026-000495",  # 否定语境「一直没结婚」
    "RF-2026-000560",  # 否定语境「且未结婚」
    "RF-2026-000544",  # 第三人称「父母离婚」
    "RF-2026-000528",  # 第三人称「再婚对象 / 后奶奶」
    "RF-2026-000845",  # 第三人称「父母离异」
    "RF-2026-000947",  # 繁体「離婚」
    "RF-2026-000355",  # 繁体「離過婚」
)


# ── 加载与并入 ──────────────────────────────────────────────────────────

def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_protocol() -> dict[str, Any]:
    return yaml.safe_load(PROTOCOL.read_text(encoding="utf-8"))


def merge_scores(direction_cases: list[dict[str, Any]],
                 label_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按 case_id 并入标签；只留 label ∈ {negative, positive} 的 342 例。"""
    labels = {
        str(c["case_id"]): c
        for c in label_cases
        if c.get("usable_for_timing") is True and c.get("label") in SCORED_LABELS
    }
    merged: list[dict[str, Any]] = []
    for case in direction_cases:
        case_id = str(case["case_id"])
        labelled = labels.get(case_id)
        if labelled is None:  # 40 例 unknown 不折入分母
            continue
        label = str(labelled["label"])
        merged.append({
            "case_id": case_id,
            "claim_id": CLAIM_ID,
            "branch": case["direction"],
            "triggered": bool(case["triggered"]),
            "outcome": "unknown",
            "prediction_letters": list(case["prediction_letters"]),
            "answer_letter": LABEL_TO_LETTER[label],
            "label": label,
            "pillars": case.get("pillars"),
            "day_branch": case.get("day_branch"),
            "edges": case.get("edges") or [],
            "n_chong_edges": case.get("n_chong_edges", 0),
        })
    merged.sort(key=lambda c: c["case_id"])
    return merged


# ── 判定 ────────────────────────────────────────────────────────────────

def judge(result: dict[str, Any]) -> tuple[str, str]:
    """卡内 §1.4：硬门槛优先，其次 Wilson 区间对 baseline_single。"""
    n = result["n_scored"]
    base = result["baseline_single"]["accuracy"]
    low, high = result["wilson_ci_95"]
    if n < MIN_SCORED:
        return "样本不足", f"n_scored={n} < {MIN_SCORED}（硬门槛，不看区间）"
    if high < base:
        return "否证", f"Wilson 上界 {high:.4f} < 基线 {base:.4f}"
    if low > base:
        return "有信号", f"Wilson 下界 {low:.4f} > 基线 {base:.4f}"
    return "样本不足", f"Wilson [{low:.4f}, {high:.4f}] 跨基线 {base:.4f}"


def summarise(cases: list[dict[str, Any]], result: dict[str, Any]) -> dict[str, Any]:
    triggered = [c for c in cases if c["triggered"] is True]
    dir_counts = Counter(c["branch"] for c in triggered)
    scored_dirs = Counter(c["branch"] for c in triggered if c["prediction_letters"])
    return {
        "n_total": result["n_total"],
        "n_triggered": len(triggered),
        "n_scored": result["n_scored"],
        "n_correct": result["n_correct"],
        "n_abstain": result["n_abstain"],
        "n_not_triggered": result["n_not_triggered"],
        "n_self": dir_counts.get("self_controls", 0),
        "n_other": dir_counts.get("other_controls", 0),
        "n_no_ke": dir_counts.get("no_ke", 0),
        "n_ambiguous": dir_counts.get("ambiguous", 0),
        "n_self_scored": scored_dirs.get("self_controls", 0),
        "n_other_scored": scored_dirs.get("other_controls", 0),
        "accuracy": result["accuracy"],
        "baseline_single": result["baseline_single"],
        "baseline_same_k": result["baseline_same_k"],
        "wilson_ci_95": result["wilson_ci_95"],
        "by_branch": result["by_branch"],
        "input_sha256": result["input_sha256"],
    }


# ── 输出层 ──────────────────────────────────────────────────────────────

def print_block(title: str, s: dict[str, Any]) -> None:
    print("-" * 74)
    print(f"{title}")
    print("-" * 74)
    print(f"  n_total={s['n_total']}  n_triggered={s['n_triggered']}  "
          f"n_scored={s['n_scored']}  n_correct={s['n_correct']}")
    print(f"  n_abstain={s['n_abstain']}（no_ke={s['n_no_ke']} / ambiguous={s['n_ambiguous']}）  "
          f"n_not_triggered={s['n_not_triggered']}")
    print(f"  方向人数  : self={s['n_self']}  other={s['n_other']}  no_ke={s['n_no_ke']}  "
          f"ambiguous={s['n_ambiguous']}")
    print(f"  计入 scored: self={s['n_self_scored']}  other={s['n_other_scored']}")
    print(f"  accuracy={s['accuracy']:.4f}  "
          f"baseline_single({s['baseline_single']['letter']})="
          f"{s['baseline_single']['accuracy']:.4f}  "
          f"baseline_same_k={s['baseline_same_k']['accuracy']:.4f}（乐观参考）")
    print(f"  wilson_ci_95=[{s['wilson_ci_95'][0]:.4f}, {s['wilson_ci_95'][1]:.4f}]")
    for branch, row in s["by_branch"].items():
        acc = "n/a" if row["accuracy"] is None else f"{row['accuracy']:.4f}"
        print(f"  by_branch {branch}: {row['correct']}/{row['n']} = {acc}")


def _one_line(text: Any) -> str:
    """把 YAML 折叠块压成一行（折叠换行会在中文标点两侧留下空格）。"""
    flat = re.sub(r"\s+", " ", str(text)).strip()
    flat = re.sub(r"\s+(?=[，。；：、）」])", "", flat)
    return re.sub(r"(?<=[，。；：、（「])\s+", "", flat)


def build_report(payload: dict[str, Any], protocol: dict[str, Any]) -> str:
    full, sens = payload["full"], payload["sensitivity"]
    lines: list[str] = []
    add = lines.append

    add("# M2-Y-395 v2 · 「夫妻宫被冲，谁制谁」换「婚姻质量」标签重测报告")
    add("")
    add(f"- 协议：`{protocol['protocol_id']}`（claim `{protocol['claim_id']}`，"
        f"冻结 `{protocol['frozen_at']}`，commit `{protocol['commit']}`）")
    add(f"- 任务：T-155；生成：`python -m tools.m2y395_real_score`（确定性，无运行时间戳）")
    add("- 回答的唯一问题：T-151 的否证，是**标签错**还是**假设错**。")
    add("")
    add("## 1. 预注册（卡内 §1，跑分前冻结）")
    add("")
    add(f"- **触发器**：{_one_line(protocol['trigger_definition'])}")
    add(f"- **方向**：{_one_line(protocol['direction_rule'])}")
    add("- **预测**：`self_controls` → `P`（婚姻不差）；`other_controls` → `N`（负面婚姻事件）；"
        "`no_ke` / `ambiguous` → 弃权（`prediction_letters: []`）；无冲 → 未触发。")
    add("- **标签映射**：`negative` → `N`，`positive` → `P`；`unknown` 40 例不折入分母。")
    add(f"- **基线**：{_one_line(protocol['baseline'])}")
    add(f"- **判据**：{_one_line(protocol['decision_rule'])}")
    add("")
    add("## 2. 数据与触发")
    add("")
    add(f"- 方向源：`META/timing-eval-set-v1.json` 中 `usable_for_timing=true` 的 "
        f"**{payload['pipeline']['n_usable']}** 例，全部建盘成功"
        f"（失败 {payload['pipeline']['n_build_failed']}）。")
    add(f"- 日支有冲（按人计）：**{payload['pipeline']['n_triggered']} / "
        f"{payload['pipeline']['n_built']} = {payload['pipeline']['trigger_rate']:.2%}**。")
    add(f"- 方向分布：self_controls {payload['pipeline']['n_self']}、"
        f"other_controls {payload['pipeline']['n_other']}、no_ke {payload['pipeline']['n_no_ke']}、"
        f"ambiguous {payload['pipeline']['n_ambiguous']}、no_chong "
        f"{payload['pipeline']['n_no_chong']}。")
    add(f"- 标签分母：342（negative {payload['pipeline']['n_negative']} / "
        f"positive {payload['pipeline']['n_positive']}），40 例 unknown 不计。")
    add("")
    add("## 3. 342 例全集")
    add("")
    add("| 指标 | 值 |")
    add("|---|---|")
    for key, label in (
        ("n_total", "n_total"), ("n_triggered", "n_triggered"), ("n_scored", "n_scored"),
        ("n_correct", "n_correct"), ("n_abstain", "n_abstain"),
        ("n_not_triggered", "n_not_triggered"), ("n_self", "n_self（触发人数）"),
        ("n_other", "n_other（触发人数）"), ("n_no_ke", "n_no_ke（弃权）"),
        ("n_ambiguous", "n_ambiguous（弃权）"),
        ("accuracy", "accuracy"), ("baseline_single", "baseline_single"),
        ("baseline_same_k", "baseline_same_k（乐观参考）"), ("wilson_ci_95", "wilson_ci_95"),
    ):
        add(f"| {label} | {_fmt(full[key])} |")
    add("")
    add("| branch | correct / n | accuracy |")
    add("|---|---|---|")
    for branch, row in full["by_branch"].items():
        acc = "n/a" if row["accuracy"] is None else f"{row['accuracy']:.4f}"
        add(f"| {branch} | {row['correct']} / {row['n']} | {acc} |")
    add("")
    add("## 4. 敏感性集（剔除 T-153 §9 的 7 例已知误判）")
    add("")
    add(f"- 剔除名单 7 例，**在本集内命中 {payload['sensitivity_hits']} 例** → "
        f"n_total = **{sens['n_total']}**。")
    add(f"- 口径差异（如实记录）：卡内 §1.1 写「7 例 → 335」，该算式假定 7 例都在 342 内；"
        f"其中 `RF-2026-000947` 的标签是 `unknown`（neutral），本就不在 342 分母里，"
        f"因此按名单剔除后是 **{sens['n_total']}** 例，不是 335。不得为凑 335 另挑一例。")
    add(f"- 命中名单的 {payload['sensitivity_hits']} 例中，触发 "
        f"**{payload['sensitivity_hits_triggered']}** 例：sensitivity 的 scored 集与 342 全集"
        f"完全一致（{sens['n_scored']} 例）。故这套敏感性只能证明「判定不依赖这 "
        f"{payload['sensitivity_hits']} 例」；它对 scored 集内的标签噪声不构成检验。")
    add("")
    add("| 指标 | 342 全集 | 敏感性集 |")
    add("|---|---:|---:|")
    for key in ("n_total", "n_triggered", "n_scored", "n_correct", "n_abstain",
                "n_self", "n_other", "n_no_ke", "n_ambiguous"):
        add(f"| {key} | {full[key]} | {sens[key]} |")
    add(f"| accuracy | {full['accuracy']:.4f} | {sens['accuracy']:.4f} |")
    add(f"| baseline_single | {full['baseline_single']['accuracy']:.4f} "
        f"({full['baseline_single']['letter']}) | {sens['baseline_single']['accuracy']:.4f} "
        f"({sens['baseline_single']['letter']}) |")
    add(f"| wilson_ci_95 | [{full['wilson_ci_95'][0]:.4f}, {full['wilson_ci_95'][1]:.4f}] | "
        f"[{sens['wilson_ci_95'][0]:.4f}, {sens['wilson_ci_95'][1]:.4f}] |")
    add("")
    add("## 5. 判定（四选一：否证 / 有信号 / 样本不足 / 标签不足以裁决）")
    add("")
    add(f"- 342 全集：**{payload['verdict_full']}** —— {payload['reason_full']}")
    add(f"- 敏感性集：**{payload['verdict_sens']}** —— {payload['reason_sens']}")
    add(f"- **最终判定：{payload['verdict']}** —— {payload['verdict_reason']}")
    add("")
    self_row = full["by_branch"].get("self_controls") or {"correct": 0, "n": 0}
    other_row = full["by_branch"].get("other_controls") or {"correct": 0, "n": 0}
    add("补充观察（**不改变上面的判定**，仅记录点估计方向）：")
    add("")
    add(f"- 整体 accuracy {full['accuracy']:.4f} **低于**同集基线 "
        f"{full['baseline_single']['letter']} 的 {full['baseline_single']['accuracy']:.4f}；"
        f"self_controls 分支 {self_row['correct']}/{self_row['n']}，"
        f"other_controls 分支 {other_row['correct']}/{other_row['n']}。")
    add("- 也就是说，没有任何「方向有信号」的迹象；但预注册的「否证」要求 Wilson **上界** "
        f"({full['wilson_ci_95'][1]:.4f}) 低于基线，实际未满足，故不得升级为「否证」，"
        "只能按硬门槛判「样本不足」。")
    add("")
    add("## 6. 风险与边界")
    add("")
    add(f"1. **样本量**：scored 集只有 {full['n_scored']} 例（硬门槛 50）。Wilson 区间 "
        f"[{full['wilson_ci_95'][0]:.4f}, {full['wilson_ci_95'][1]:.4f}] 宽到跨过基线，"
        f"任何方向的结论都不成立；本报告只能写「样本不足」，不能写成「有效/无效」。")
    add(f"2. **触发率低**：按人计只有 {payload['pipeline']['trigger_rate']:.2%} 的人日支有冲，"
        f"342 集内触发 {full['n_triggered']} 人，其中 {full['n_no_ke']} 人 no_ke 弃权"
        f"、{full['n_ambiguous']} 人 ambiguous；方向规则能裁决的面很窄。")
    add("3. **标签噪声**：T-153 为关键词/极性标签，已知 7 例误判保留未改；敏感性集的作用是"
        "证明结论不依赖这 7 例，不是把噪声洗掉（且名单内命中的 6 例均未触发，scored 集不变）。")
    add("4. **计数单位变更**：T-151 以冲边为一例，本报告以人一例。两者不可直接比 accuracy，"
        "只能比「方向本身是否被否证」这一判断。")
    add("5. **不追认答案**：方向只由 `KE_MAP` 与本气五行决定，未读标签、未按标签挑案例、"
        "未为结论改规则。")
    add("")
    add("## 7. 复跑")
    add("")
    add("```bash")
    add(".venv\\Scripts\\python.exe -m tools.m2y395_real_direction")
    add(".venv\\Scripts\\python.exe -m tools.m2y395_real_score")
    add(".venv\\Scripts\\python.exe -m tools.claim_metric "
        "--protocol META/eval-protocols/m2y395-v2.yaml --cases META/m2y395-v2-scored.json")
    add("```")
    add("")
    add(f"- 输入指纹（342 全集，`score()` 的 input_sha256）：`{full['input_sha256']}`")
    add(f"- 输入指纹（敏感性集）：`{sens['input_sha256']}`")
    add("")
    return "\n".join(lines)


def _fmt(value: Any) -> str:
    if isinstance(value, dict):
        if "letter" in value:
            return f"{value.get('letter')} / {value.get('accuracy'):.4f}"
        return f"{value.get('accuracy'):.4f}"
    if isinstance(value, list):
        return "[" + ", ".join(f"{v:.4f}" for v in value) + "]"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


# ── 主流程 ──────────────────────────────────────────────────────────────

def main() -> int:
    for path in (CASES, LABELS, PROTOCOL):
        if not path.exists():
            print(f"[FATAL] 缺少输入：{path}", file=sys.stderr)
            return 1
    direction_payload = load_json(CASES)
    label_payload = load_json(LABELS)
    protocol = load_protocol()

    cases = merge_scores(direction_payload["cases"], label_payload["cases"])
    if not cases:
        print("[FATAL] 并入标签后没有任何可计分案例", file=sys.stderr)
        return 1
    label_counts = Counter(c["label"] for c in cases)
    if set(label_counts) - set(SCORED_LABELS):
        print(f"[FATAL] 出现预注册外标签：{sorted(set(label_counts) - set(SCORED_LABELS))}",
              file=sys.stderr)
        return 1

    sensitivity = [c for c in cases if c["case_id"] not in set(SENSITIVITY_EXCLUDE)]
    excluded = [c for c in cases if c["case_id"] in set(SENSITIVITY_EXCLUDE)]
    hits = len(excluded)

    try:
        result_full = score([dict(c) for c in cases], protocol)
        result_sens = score([dict(c) for c in sensitivity], protocol)
    except MetricError as exc:
        print(f"[FATAL] 计分拒绝：{exc}", file=sys.stderr)
        return 1

    full = summarise(cases, result_full)
    sens = summarise(sensitivity, result_sens)
    verdict_full, reason_full = judge(result_full)
    verdict_sens, reason_sens = judge(result_sens)
    if verdict_full != verdict_sens:
        verdict, reason = "标签不足以裁决", (
            f"342 全集判「{verdict_full}」，敏感性集判「{verdict_sens}」，两套结论翻转")
    else:
        verdict, reason = verdict_full, f"两套一致：{reason_full}"

    scored_payload = {
        "meta": {
            "protocol_id": protocol["protocol_id"],
            "claim_id": CLAIM_ID,
            "task": "T-155",
            "generated_by": "python -m tools.m2y395_real_score",
            "label_source": "META/marriage-quality-labels-v1.json",
            "direction_source": "META/m2y395-v2-cases.json",
            "n_cases": len(cases),
            "n_unknown_excluded": 40,
            "label_counts": dict(sorted(label_counts.items())),
            "answer_letter_rule": "negative→N, positive→P",
            "case_unit": "一个人（case）一例",
            "sensitivity_exclude": list(SENSITIVITY_EXCLUDE),
            "sensitivity_hits": hits,
        },
        "cases": cases,
    }
    OUT.write_text(json.dumps(scored_payload, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")

    payload = {
        "full": full,
        "sensitivity": sens,
        "sensitivity_hits": hits,
        "sensitivity_hits_triggered": sum(1 for c in excluded if c["triggered"]),
        "verdict_full": verdict_full,
        "reason_full": reason_full,
        "verdict_sens": verdict_sens,
        "reason_sens": reason_sens,
        "verdict": verdict,
        "verdict_reason": reason,
        "pipeline": {
            "n_usable": direction_payload["meta"]["n_usable_cases"],
            "n_built": direction_payload["meta"]["n_built"],
            "n_build_failed": direction_payload["meta"]["n_build_failed"],
            "n_triggered": direction_payload["meta"]["n_triggered"],
            "trigger_rate": direction_payload["meta"]["trigger_rate"],
            "n_self": direction_payload["meta"]["direction_counts"]["self_controls"],
            "n_other": direction_payload["meta"]["direction_counts"]["other_controls"],
            "n_no_ke": direction_payload["meta"]["direction_counts"]["no_ke"],
            "n_ambiguous": direction_payload["meta"]["direction_counts"]["ambiguous"],
            "n_no_chong": direction_payload["meta"]["direction_counts"]["no_chong"],
            "n_negative": label_counts.get("negative", 0),
            "n_positive": label_counts.get("positive", 0),
        },
    }

    print("=" * 74)
    print("T-155 · M2-Y-395 v2 换标签重测")
    print("=" * 74)
    print_block("【1】342 例全集（label ∈ negative/positive）", full)
    print_block(f"【2】敏感性集（342 − 名单命中 {hits} 例 = {sens['n_total']}；卡内写 335）", sens)
    print("-" * 74)
    print(f"342 全集判定  : {verdict_full}（{reason_full}）")
    print(f"敏感性集判定  : {verdict_sens}（{reason_sens}）")
    print(f"最终判定      : {verdict}")
    print("-" * 74)
    print(f"产物          : {OUT.relative_to(ROOT)}")
    REPORT.write_text(build_report(payload, protocol), encoding="utf-8")
    print(f"报告          : {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
