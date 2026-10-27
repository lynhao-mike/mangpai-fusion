"""engine/infrastructure/weight_repository.py · v4.2 流派权重 YAML 仓库

唯一负责 expert-weights.yaml 的**原始读写**（读原始 mapping 供学习回路回写、写回）。
**经过校验的 runtime 读取统一收口到** `engine/application/weight_profile_service.py`。

Fail-Closed 约定（ADR-007 D7）：文件缺失、YAML 损坏、请求的 domain 不存在，一律直接抛错。
本模块不再保留任何静默回落到 `_DEFAULT_SCHOOL_WEIGHTS` 的分支——权重决定「哪一派的话更算数」，
静默回落会让裁决配比在无人知情下变成出厂值，且报告上看不出任何异常。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

from engine.application.weight_profile_service import load_expert_weight_profile_payload

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WEIGHTS_PATH = Path(__file__).parent.parent / "expert-weights.yaml"
_WEIGHTS_SOURCE = "engine/expert-weights.yaml"

#: 出厂默认权重 **仅作历史基线常量**（`tests/test_production_entrypoints_unchanged.py` 有相等断言）。
#: 运行时任何路径都不得用它兜底；读到它的唯一合法方式是被测试直接引用。
_DEFAULT_SCHOOL_WEIGHTS: dict[str, float] = {
    "ziping": 0.42,
    "tiaohou_ditiansui": 0.32,
    "blind": 0.26,
}


def load_expert_weights() -> dict[str, Any]:
    """读取 expert-weights.yaml 的原始 mapping。

    Fail-Closed：文件缺失抛 `FileNotFoundError`，YAML 损坏抛 `yaml.YAMLError`，
    顶层不是 mapping 抛 `ValueError`。不返回空 dict。
    """
    raw = yaml.safe_load(_WEIGHTS_PATH.read_text(encoding="utf-8"))
    if raw is None:
        raise ValueError(f"expert-weights.yaml 为空文件：{_WEIGHTS_PATH}")
    if not isinstance(raw, Mapping):
        raise ValueError(f"expert-weights.yaml 顶层必须是 mapping：{_WEIGHTS_PATH}")
    return dict(raw)


def save_expert_weights(data: dict[str, Any]) -> None:
    _WEIGHTS_PATH.write_text(
        yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


def load_school_weights(
    domain: str = "事业",
    *,
    workspace_root: str | Path = _REPO_ROOT,
    source_path: str = _WEIGHTS_SOURCE,
) -> dict[str, float]:
    """读取指定领域的流派权重。

    Fail-Closed：不提供任何默认值兜底。文件缺失 / YAML 损坏 / schema 不合规由
    `weight_profile_service.load_expert_weight_profile_payload` 抛错；
    请求的 domain 未定义则抛 `ValueError`。

    `workspace_root` / `source_path` 仅用于显式指定配置来源（缺省即仓库内 canonical 源），
    不改变 fail-closed 语义。
    """
    payload = load_expert_weight_profile_payload(
        workspace_root=workspace_root,
        source_path=source_path,
    )
    if domain not in payload.weights:
        raise ValueError(
            f"expert-weights.yaml 未定义权重 domain={domain!r}；已知 domain：{sorted(payload.weights)}"
        )
    return {expert: float(value) for expert, value in payload.weights[domain].items()}
