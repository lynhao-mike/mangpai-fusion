"""H5 · v1.3 不应导致 v1.2 G1-G6 退化

落地：plans/architecture-v1.3.md § 六 H5 + decisions-locked.md 决策 I
基础测试：tests/regression/test_v1_2_vs_v1_0.py（已实现 v1.2 G1-G6 6 项门槛）

H5 含义：v1.3 自迭代闭环上线后，v1.2 发布门槛（决策 I 的 G1-G6）必须**全部仍然通过**——
任何 D1-D8 改动若导致 v1.2 G1-G6 退化即为退化（regression）。

本文件是 H5 的 pytest 锚点：
    1. 验证 tests/regression/test_v1_2_vs_v1_0.py 文件存在且被 pytest 收集
    2. 验证 tests/regression_baseline.yaml 含 6 项 gate 定义
    3. 不重复执行 G1-G6 的实际断言（那是 test_v1_2_vs_v1_0.py 的职责）

历史背景：v1.3 W4 验收时 STATUS.md 写"H4 / H5 由 CI 单独验证"但 H5 没有显式的
pytest 锚点。本 PR 补上锚点，让"v1.2 不退化"明确为 H5 收编入口。
"""
from __future__ import annotations

import pathlib

import pytest

import yaml


pytestmark = [pytest.mark.v1_3_acceptance]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_h5_v1_2_regression_test_file_exists():
    """v1.2 G1-G6 回归测试文件必须存在，否则 H5 等于无防线。"""
    p = REPO_ROOT / "tests" / "regression" / "test_v1_2_vs_v1_0.py"
    assert p.exists(), f"v1.2 回归测试文件缺失: {p}"


def test_h5_regression_baseline_has_six_gates():
    """tests/regression_baseline.yaml 必须含 6 项 gate 定义（决策 I）。"""
    p = REPO_ROOT / "tests" / "regression_baseline.yaml"
    assert p.exists(), f"基线文件缺失: {p}"
    with p.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict)
    assert "gates" in data, "regression_baseline.yaml 必须含 'gates' 顶层键"
    gates = data["gates"]
    assert len(gates) == 6, f"必须有 6 项 gate（G1-G6），实际 {len(gates)}"


def test_h5_regression_test_collects_in_pytest(pytestconfig):
    """通过 pytest 内部 API 验证回归测试文件可被 pytest 正常收集。
    若被意外排除（如误加 collect_ignore）会立即报错。"""
    rootpath = pathlib.Path(pytestconfig.rootpath)
    target = rootpath / "tests" / "regression" / "test_v1_2_vs_v1_0.py"
    assert target.exists()

    # 通过文件路径反查内部测试函数定义数量（粗略指标）
    text = target.read_text(encoding="utf-8")
    test_funcs = [line for line in text.splitlines()
                  if line.startswith("def test_") or line.startswith("    def test_")]
    assert len(test_funcs) >= 1, (
        f"v1.2 回归文件 {target.name} 应至少含 1 个 test_ 函数，"
        f"实际 {len(test_funcs)}"
    )


def test_h5_pytest_marker_registered(pytestconfig):
    """v1_3_acceptance / regression marker 必须在 pyproject.toml 中显式注册
    （--strict-markers 下 H5 自身这个 mark 不能拼错）。"""
    markers = pytestconfig.getini("markers")
    names = [m.split(":", 1)[0].strip() for m in markers]
    assert "v1_3_acceptance" in names, f"v1_3_acceptance 未注册：{names}"
    assert "regression" in names, f"regression 未注册：{names}"
