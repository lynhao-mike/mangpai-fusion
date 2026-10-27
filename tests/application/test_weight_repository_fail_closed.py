"""权重加载 Fail-Closed 回归（ADR-007 D7 / T-144）。

背景：`engine/infrastructure/weight_repository.py` 曾用两层 `except Exception` 静默回落到
硬编码 `_DEFAULT_SCHOOL_WEIGHTS`。实测危害——配置路径一旦失效，权重从
`{ziping:0.5, tiaohou:0.25, blind:0.25}` 悄悄变成 `{0.42, 0.32, 0.26}`。
权重决定「哪一派的话更算数」，静默回落等于裁决配比在无人知情下变成出厂值，
而且报告上看不出任何异常。

本测试把三条契约钉死：
1. 文件缺失 / YAML 损坏 / domain 不存在 → 抛错，不返回默认值；
2. `_DEFAULT_SCHOOL_WEIGHTS` 常量名仍保留（`tests/test_production_entrypoints_unchanged.py` 有相等断言）；
3. 两个加载函数体内不得再出现捕获 `Exception` 的 `except` 分支。
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
import yaml

import engine.infrastructure.weight_repository as weight_repository
from engine.infrastructure.weight_repository import (
    _DEFAULT_SCHOOL_WEIGHTS,
    load_expert_weights,
    load_school_weights,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "engine" / "infrastructure" / "weight_repository.py"

CANONICAL_BUSINESS_WEIGHTS = {
    "ziping": 0.50,
    "tiaohou_ditiansui": 0.25,
    "blind": 0.25,
}


def test_canonical_config_is_read_verbatim() -> None:
    assert load_school_weights("事业") == pytest.approx(CANONICAL_BUSINESS_WEIGHTS)


def test_default_constant_survives_for_baseline_assertions() -> None:
    assert _DEFAULT_SCHOOL_WEIGHTS == {
        "ziping": 0.42,
        "tiaohou_ditiansui": 0.32,
        "blind": 0.26,
    }


def test_missing_config_file_raises_instead_of_falling_back(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_school_weights("事业", workspace_root=tmp_path, source_path="nope.yaml")


def test_broken_yaml_raises_instead_of_falling_back(tmp_path: Path) -> None:
    (tmp_path / "broken.yaml").write_text("weights: [unclosed\n  :::", encoding="utf-8")
    with pytest.raises(yaml.YAMLError):
        load_school_weights("事业", workspace_root=tmp_path, source_path="broken.yaml")


def test_unknown_domain_raises_instead_of_using_defaults() -> None:
    with pytest.raises(ValueError, match="未定义权重 domain"):
        load_school_weights("不存在的域")


def test_incomplete_profile_raises_instead_of_filling_from_defaults(
    tmp_path: Path,
) -> None:
    """domain 缺一个流派时也必须抛错——不能拿 `_DEFAULT_SCHOOL_WEIGHTS` 补齐。"""

    payload = yaml.safe_load(
        (REPO_ROOT / "engine" / "expert-weights.yaml").read_text(encoding="utf-8")
    )
    del payload["weights"]["事业"]["blind"]
    (tmp_path / "partial.yaml").write_text(
        yaml.dump(payload, allow_unicode=True), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="缺少专家权重"):
        load_school_weights("事业", workspace_root=tmp_path, source_path="partial.yaml")


def test_raw_loader_raises_on_missing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(weight_repository, "_WEIGHTS_PATH", tmp_path / "absent.yaml")
    with pytest.raises(FileNotFoundError):
        load_expert_weights()


def _exception_handlers(function_name: str) -> list[ast.ExceptHandler]:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"), filename=str(MODULE_PATH))
    definition = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == function_name
    )
    return [
        node
        for node in ast.walk(definition)
        if isinstance(node, ast.ExceptHandler)
    ]


@pytest.mark.parametrize("function_name", ["load_expert_weights", "load_school_weights"])
def test_no_silent_exception_swallowing_in_loaders(function_name: str) -> None:
    """静态守卫：两个加载函数体内不得再出现 `except Exception` / 裸 `except`。"""

    offenders = []
    for handler in _exception_handlers(function_name):
        if handler.type is None:
            offenders.append("bare except")
            continue
        candidates = (
            handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
        )
        for candidate in candidates:
            name = getattr(candidate, "id", None) or getattr(candidate, "attr", None)
            if name in {"Exception", "BaseException"}:
                offenders.append(f"except {name}")

    assert not offenders, f"{function_name} 仍在静默吞异常：{offenders}"


def test_default_constant_is_not_used_as_runtime_fallback() -> None:
    """`_DEFAULT_SCHOOL_WEIGHTS` 只允许出现在常量定义里，不得在任何函数体内被引用。"""

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"), filename=str(MODULE_PATH))
    uses_in_functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        for inner in ast.walk(node)
        if isinstance(inner, ast.Name) and inner.id == "_DEFAULT_SCHOOL_WEIGHTS"
    ]
    assert not uses_in_functions, "函数体内仍在引用 _DEFAULT_SCHOOL_WEIGHTS，等于留了回落后门"
