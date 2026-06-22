"""tools.v5_prediction_feedback · v5 prediction-first 账本反馈回写工具。

prediction-first 闭环：先预测（V5Prediction），再等待反馈，再校准。
本工具负责把命主反馈标注写回到 v5.json 的 prediction_ledger 条目中。

不依赖旧 statement_index / statement_records 系统。
不改旧 feedback_ingest.py。

公开 API
--------
list_predictions(case_id)
    列出当前案例 prediction ledger，用于查看待反馈条目。

apply_prediction_feedback(case_id, prediction_id, verdict, *, note="")
    把反馈标注写回 prediction ledger JSON。

verdict 合法值：
    hit      命中
    miss     失验
    partial  半命中（事件发生但时间或程度偏差较大）
    skipped  跳过（命主不知道 / 不适用）

CLI：
    python -m tools.v5_prediction_feedback list C-2026-001-乾-庚申戊寅壬子辛丑
    python -m tools.v5_prediction_feedback apply C-2026-001-乾-庚申戊寅壬子辛丑 v5pred-xxxx hit
    python -m tools.v5_prediction_feedback apply C-2026-001-乾-庚申戊寅壬子辛丑 v5pred-xxxx miss --note "时间窗未命中"
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = REPO_ROOT / "reports"

V5FeedbackVerdict = Literal["hit", "miss", "partial", "skipped"]
VALID_VERDICTS: set[str] = {"hit", "miss", "partial", "skipped"}

_VERDICT_LABELS: dict[str, str] = {
    "hit": "命中",
    "miss": "失验",
    "partial": "半命中",
    "skipped": "跳过",
    "pending": "待反馈",
}


@dataclass
class PredictionSummary:
    prediction_id: str
    domain: str
    event_label: str
    time_window: str
    trigger_conditions: list[str]
    probability_range: list[float]
    confidence_tier: str
    falsifier: str
    feedback_state: str

    def display(self) -> str:
        label = _VERDICT_LABELS.get(self.feedback_state, self.feedback_state)
        prob = f"{int(self.probability_range[0]*100)}%–{int(self.probability_range[1]*100)}%"
        lines = [
            f"  ID:     {self.prediction_id}",
            f"  领域:   {self.domain}",
            f"  应事:   {self.event_label}",
            f"  时间窗: {self.time_window}",
            f"  概率:   {prob} ({self.confidence_tier})",
            f"  证伪:   {self.falsifier}",
            f"  状态:   {label}",
        ]
        return "\n".join(lines)


def _find_v5_json(case_id: str) -> Path | None:
    """优先从 reports/ 目录查找 v5 JSON；返回 None 表示未找到。"""

    pattern = f"*{case_id}*-v6-preprod-content-report.v5.json"
    matches = list(REPORTS_DIR.glob(pattern))
    if matches:
        return max(matches, key=lambda p: p.stat().st_mtime)
    pattern2 = f"*{case_id}*.v5.json"
    matches2 = list(REPORTS_DIR.glob(pattern2))
    if matches2:
        return max(matches2, key=lambda p: p.stat().st_mtime)
    return None


def list_predictions(case_id: str, *, v5_json_path: str | Path | None = None) -> list[PredictionSummary]:
    """列出当前 case 的 prediction ledger 条目。

    v5_json_path 可选：显式指定 JSON 路径；不传则从 reports/ 自动查找。
    """

    v5_path = Path(v5_json_path) if v5_json_path is not None else _find_v5_json(case_id)
    if v5_path is None:
        return []
    raw = json.loads(v5_path.read_text(encoding="utf-8"))
    predictions = raw.get("prediction_ledger", {}).get("predictions", [])
    result: list[PredictionSummary] = []
    for item in predictions:
        tw = item.get("time_window", {})
        time_label = tw.get("label", str(tw)) if isinstance(tw, dict) else str(tw)
        result.append(
            PredictionSummary(
                prediction_id=str(item.get("prediction_id", "")),
                domain=str(item.get("domain", "")),
                event_label=str(item.get("event_label", "")),
                time_window=time_label,
                trigger_conditions=list(item.get("trigger_conditions", [])),
                probability_range=[float(x) for x in item.get("probability_range", [0.0, 0.0])],
                confidence_tier=str(item.get("confidence", {}).get("tier", "")),
                falsifier=str(item.get("falsifier", "")),
                feedback_state=str(item.get("feedback_state", "pending")),
            )
        )
    return result


def apply_prediction_feedback(
    case_id: str,
    prediction_id: str,
    verdict: V5FeedbackVerdict,
    *,
    note: str = "",
    dry_run: bool = False,
    v5_json_path: str | Path | None = None,
) -> bool:
    """把反馈标注写回 v5 JSON 的 prediction_ledger 条目。

    v5_json_path 可选：显式指定 JSON 路径；不传则从 reports/ 自动查找。
    返回 True 表示成功更新，False 表示未找到对应 prediction_id。
    """

    if verdict not in VALID_VERDICTS:
        raise ValueError(f"verdict 必须是 {sorted(VALID_VERDICTS)} 之一，实际为 {verdict!r}。")

    if v5_json_path is not None:
        v5_path = Path(v5_json_path)
    else:
        v5_path = _find_v5_json(case_id)
    if v5_path is None:
        raise FileNotFoundError(f"未找到 case {case_id!r} 的 v5 JSON；请先运行 render_report_v6 生成报告。")

    raw = json.loads(v5_path.read_text(encoding="utf-8"))
    predictions = raw.get("prediction_ledger", {}).get("predictions", [])
    updated = False
    for item in predictions:
        if item.get("prediction_id") == prediction_id:
            old_state = item.get("feedback_state", "pending")
            item["feedback_state"] = verdict
            if note:
                item["calibration_note"] = f"{item.get('calibration_note', '')} | 反馈备注: {note}".strip(" |")
            updated = True
            if not dry_run:
                print(f"[OK] {prediction_id}: {old_state} → {verdict} ({_VERDICT_LABELS.get(verdict, verdict)})")
            else:
                print(f"[DRY-RUN] {prediction_id}: {old_state} → {verdict}")
            break

    if not updated:
        return False

    if not dry_run:
        v5_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] 已写回 {v5_path.name}")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="v5 prediction-first 账本反馈回写")
    subparsers = parser.add_subparsers(dest="cmd")

    sub_list = subparsers.add_parser("list", help="列出当前 case 的 prediction 账本")
    sub_list.add_argument("case_id", help="案例 ID")

    sub_apply = subparsers.add_parser("apply", help="写入一条预测反馈")
    sub_apply.add_argument("case_id", help="案例 ID")
    sub_apply.add_argument("prediction_id", help="预测 ID（v5pred-xxxxx）")
    sub_apply.add_argument("verdict", choices=sorted(VALID_VERDICTS), help="反馈标注")
    sub_apply.add_argument("--note", "-n", default="", help="反馈备注")
    sub_apply.add_argument("--dry-run", action="store_true", help="只模拟，不写盘")

    args = parser.parse_args(argv)
    if args.cmd is None:
        parser.print_help()
        return 1

    if args.cmd == "list":
        predictions = list_predictions(args.case_id)
        if not predictions:
            print(f"[WARN] 未找到 case {args.case_id!r} 的 v5 JSON 或 prediction 账本为空。")
            return 0
        pending = [p for p in predictions if p.feedback_state == "pending"]
        done = [p for p in predictions if p.feedback_state != "pending"]
        print(f"=== v5 预测账本：{args.case_id} ===\n")
        if pending:
            print(f"待反馈 ({len(pending)} 条):")
            for p in pending:
                print(p.display())
                print()
        if done:
            print(f"已反馈 ({len(done)} 条):")
            for p in done:
                print(p.display())
                print()
        return 0

    if args.cmd == "apply":
        try:
            ok = apply_prediction_feedback(
                args.case_id,
                args.prediction_id,
                args.verdict,
                note=args.note,
                dry_run=args.dry_run,
            )
        except (FileNotFoundError, ValueError) as exc:
            print(f"[ERROR] {exc}")
            return 1
        if not ok:
            print(f"[ERROR] 未找到 prediction_id={args.prediction_id!r}；请用 list 命令确认正确 ID。")
            return 1
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
