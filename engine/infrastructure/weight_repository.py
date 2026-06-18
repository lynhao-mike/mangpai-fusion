"""engine/infrastructure/weight_repository.py · v4.2 流派权重 YAML 仓库

唯一负责 expert-weights.yaml 的读写，其他层不得直接操作该文件。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_WEIGHTS_PATH = Path(__file__).parent.parent / "expert-weights.yaml"

_DEFAULT_SCHOOL_WEIGHTS: dict[str, float] = {
    "ziping": 0.42,
    "tiaohou_ditiansui": 0.32,
    "blind": 0.26,
}


def load_expert_weights() -> dict[str, Any]:
    try:
        return yaml.safe_load(_WEIGHTS_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def save_expert_weights(data: dict[str, Any]) -> None:
    _WEIGHTS_PATH.write_text(
        yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


def load_school_weights(domain: str = "事业") -> dict[str, float]:
    """读取指定领域的流派权重，缺失时 fallback 到默认值。"""
    try:
        data = load_expert_weights()
        w = data.get("weights", {}).get(domain, {})
        return {
            "ziping": float(w.get("ziping", _DEFAULT_SCHOOL_WEIGHTS["ziping"])),
            "tiaohou_ditiansui": float(w.get("tiaohou_ditiansui", _DEFAULT_SCHOOL_WEIGHTS["tiaohou_ditiansui"])),
            "blind": float(w.get("blind", _DEFAULT_SCHOOL_WEIGHTS["blind"])),
        }
    except Exception:
        return dict(_DEFAULT_SCHOOL_WEIGHTS)
