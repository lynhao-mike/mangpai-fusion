"""人工确认后将 expert × domain 反馈统计提升到 canonical runtime overlay。"""

from __future__ import annotations

import argparse
import difflib
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from tools.feedback_ingest import (
    compute_weight_update_proposal,
    get_expert_domain_stats,
)

CANONICAL_PROFILE = Path("engine/expert-weights.yaml")
_VERSION_RE = re.compile(r"^feedback-overlay-v(?P<number>[1-9][0-9]*)$")


def _load_profile(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"canonical expert weights 顶层必须是 mapping：{path}")
    if payload.get("schema_version") != "expert-weight-profile/v1":
        raise ValueError("只允许提升 expert-weight-profile/v1 canonical profile。")
    if not isinstance(payload.get("feedback_overlay"), Mapping):
        raise ValueError("canonical profile 缺少 feedback_overlay mapping。")
    return payload


def _next_version(current: str) -> str:
    if current == "no-feedback-overlay":
        return "feedback-overlay-v1"
    match = _VERSION_RE.fullmatch(current)
    if match is None:
        raise ValueError(f"无法从既有 feedback_overlay.version 严格递增：{current!r}")
    return f"feedback-overlay-v{int(match.group('number')) + 1}"


def _entry_from_stats(item: Mapping[str, Any]) -> dict[str, Any]:
    hits = float(item["hits"])
    misses = float(item["misses"])
    return {
        "expert_system": str(item["expert_system"]),
        "domain": str(item["domain"]),
        "rule_group": "parallel-domain",
        "n_eff": float(item["n_eff"]),
        "success_count": hits,
        "failure_count": misses,
        "beta_alpha": hits + 1.0,
        "beta_beta": misses + 1.0,
        "beta_mean": float(item["beta_mean"]),
        "wilson_lower_bound": float(item["wilson_lower"]),
    }


def _selected_entries(
    stats: Mapping[str, Any],
    proposal: Mapping[str, Any],
) -> list[dict[str, Any]]:
    selected = {
        (str(item.get("domain", "")), str(item.get("expert_system", "")))
        for item in proposal.get("proposals", [])
        if isinstance(item, Mapping) and item.get("requires_human_review") is True
    }
    entries = [
        _entry_from_stats(item)
        for item in stats.get("items", [])
        if isinstance(item, Mapping)
        and (str(item.get("domain", "")), str(item.get("expert_system", ""))) in selected
    ]
    return sorted(entries, key=lambda item: (item["domain"], item["expert_system"]))


def _yaml_text(payload: Mapping[str, Any]) -> str:
    return yaml.safe_dump(
        dict(payload),
        allow_unicode=True,
        sort_keys=False,
        width=1000,
    )


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(text)
        temp_path = Path(handle.name)
    try:
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def promote_expert_weight_feedback(
    *,
    profile_path: str | Path = CANONICAL_PROFILE,
    min_n_eff: int = 10,
    dry_run: bool = True,
    reviewed_by: str | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    """预览或人工确认提升；不修改基础权重，只替换 feedback_overlay。"""

    target = Path(profile_path)
    if target.name != CANONICAL_PROFILE.name or target.parent.name != CANONICAL_PROFILE.parent.name:
        raise ValueError("只允许写入 canonical engine/expert-weights.yaml；禁止 legacy 或竞争事实源。")
    if min_n_eff < 1:
        raise ValueError("min_n_eff 必须至少为 1。")
    if not dry_run and not str(reviewed_by or "").strip():
        raise ValueError("正式 promotion 必须提供非空 reviewed_by。")

    payload = _load_profile(target)
    current_overlay = dict(payload["feedback_overlay"])
    current_version = str(current_overlay.get("version") or "")
    next_version = _next_version(current_version)
    if version is not None and version != next_version:
        raise ValueError(
            f"feedback overlay version 必须严格递增为 {next_version}；拒绝复用或跳号：{version}"
        )

    stats = get_expert_domain_stats()
    proposal = compute_weight_update_proposal(min_n_eff=min_n_eff)
    entries = _selected_entries(stats, proposal)
    if not entries:
        raise ValueError("没有达到 promotion 阈值且需人工 review 的 expert/domain 统计。")

    reviewed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    overlay = {
        "version": next_version,
        "status": "human_confirmed",
        "reviewed_by": str(reviewed_by or "<required-for-write>").strip(),
        "reviewed_at": reviewed_at,
        "requires_human_review": False,
        "source_path": "engine/logs/expert_domain_feedback.jsonl",
        "proposal_schema_version": proposal.get("schema_version", ""),
        "proposal_min_n_eff": min_n_eff,
        "min_effective_sample_for_adjustment": current_overlay.get(
            "min_effective_sample_for_adjustment", 11
        ),
        "low_sample_max_delta": current_overlay.get("low_sample_max_delta", 0.02),
        "mature_sample_max_delta": current_overlay.get("mature_sample_max_delta", 0.15),
        "entries": entries,
    }
    proposed_payload = dict(payload)
    proposed_payload["updated_at"] = reviewed_at
    proposed_payload["feedback_overlay"] = overlay

    before_text = _yaml_text(payload)
    after_text = _yaml_text(proposed_payload)
    preview_diff = "\n".join(
        difflib.unified_diff(
            before_text.splitlines(),
            after_text.splitlines(),
            fromfile=str(target),
            tofile=str(target),
            lineterm="",
        )
    )
    if not dry_run:
        _atomic_write(target, after_text)

    return {
        "applied": not dry_run,
        "dry_run": dry_run,
        "profile_path": str(target),
        "current_version": current_version,
        "next_version": next_version,
        "entry_count": len(entries),
        "preview_diff": preview_diff,
        "proposal": proposal,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="预览或人工确认提升 expert/domain feedback overlay（默认 dry-run）。"
    )
    parser.add_argument("--profile-path", type=Path, default=CANONICAL_PROFILE)
    parser.add_argument("--min-n-eff", type=int, default=10)
    parser.add_argument("--apply", action="store_true", help="正式写入 canonical profile")
    parser.add_argument("--reviewed-by", help="正式写入所需的人类 reviewer 姓名")
    parser.add_argument("--version", help="可选；必须精确等于自动计算的下一 version")
    args = parser.parse_args(argv)

    try:
        result = promote_expert_weight_feedback(
            profile_path=args.profile_path,
            min_n_eff=args.min_n_eff,
            dry_run=not args.apply,
            reviewed_by=args.reviewed_by,
            version=args.version,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    print(result["preview_diff"])
    mode = "APPLIED" if result["applied"] else "DRY-RUN"
    print(
        f"{mode}: {result['current_version']} -> {result['next_version']}; "
        f"entries={result['entry_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
