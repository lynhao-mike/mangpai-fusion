from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

_INITIAL_REVIEW_N_EFF = 5.0


def _number(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def render_capability_report(
    manifest_summary: Mapping[str, int],
    experiment_summary: Mapping[str, Any],
    posteriors: Sequence[Mapping[str, Any] | object],
) -> str:
    """Render a cautious baseline view; it never promotes production expertise."""
    posterior_rows = [item if isinstance(item, Mapping) else item.to_dict() for item in posteriors]
    all_below_threshold = all(float(item.get("n_eff", 0.0)) < _INITIAL_REVIEW_N_EFF for item in posterior_rows)
    recommendation = "HOLD" if all_below_threshold else "GO（仅进入人工复核，不进入生产校准）"
    manifest_lines = [f"- {name}: {count}" for name, count in sorted(manifest_summary.items())] or ["- 无案例记录"]
    experiment_lines: list[str] = []
    for group, summary in sorted(experiment_summary.items()):
        if isinstance(summary, Mapping):
            rendered = ", ".join(f"{key}={_number(value)}" for key, value in sorted(summary.items()))
        else:
            rendered = _number(summary)
        experiment_lines.append(f"- {group}: {rendered}")
    if not experiment_lines:
        experiment_lines.append("- 尚无可发布的实验结果")
    posterior_lines = [
        "- {school}/{task}: posterior={mean}, N_eff={n_eff}, evidence={grade}".format(
            school=item.get("school_id", "unknown"),
            task=item.get("task_id", "unknown"),
            mean=_number(item.get("posterior_mean", "n/a")),
            n_eff=_number(item.get("n_eff", 0.0)),
            grade=item.get("evidence_grade", "unknown"),
        )
        for item in posterior_rows
    ] or ["- 尚无条件化后验"]
    return "\n".join([
        "# 学派能力暂定能力基线",
        "",
        "## 1. 评估范围与证据等级",
        "本报告区分弱先验、历史盲评证据与未来前瞻证据；当前结果仅是可复核基线。",
        "",
        "## 2. 案例可用性与污染盘点",
        *manifest_lines,
        "",
        "## 3. 任务覆盖与三态输出",
        "输出状态为 claim / abstain / unsupported；缺失输出不得视为错误预测。",
        "",
        "## 4. 五维能力基线",
        "按覆盖、区分度、准确度、校准与增量收益观察，不合成为生产权重。",
        "",
        "## 5. 四组增量实验",
        *experiment_lines,
        "",
        "## 6. 条件化能力后验",
        *posterior_lines,
        "",
        "## 7. 校准与高风险误差",
        "高风险误报需单独审查；低样本校准值不得外推。",
        "",
        "## 8. 样本与证据限制",
        "历史报告、已知反馈与规则开发材料可能造成标签泄漏；污染案例不得作为盲评证据。",
        "初始样本不能证明稳定专长，结论必须由独立前瞻样本证伪或复现。",
        "",
        "## 9. GO / HOLD / STOP 建议",
        f"**{recommendation}**",
        "所有条件后验 N_eff 均低于初始复核门槛时默认 HOLD。" if all_below_threshold else "存在达到门槛的条件后验，仍须人工复核。",
        "",
    ])
