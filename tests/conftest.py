"""tests/conftest.py · v1.2 pytest 全局配置 + 共用 fixture

- 注入 sys.path（确保 import engine/tools/tests.fixtures 都正确）
- 注册全局 fixture：``case_input``、``feedback_truth``、``v1_0_baseline``、
  ``regression_baseline``
- 通过 ``collect_ignore`` 跳过 Track-E 的纯 stdlib 测试文件（它们用 ``main()``
  方式自跑，签名 ``test_E0XX(rep, tmp)`` 与 pytest fixture 机制不兼容；
  我们用 ``tests/regression/test_e_guardrails.py`` 重新封装）。

作者：Track-H · v1.2.0
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

# ============================================================
# sys.path 调整：repo 根目录注入
# ============================================================
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ============================================================
# Track-E 测试自跑（pytest 不收）
# ============================================================
# Track-E 的 tests/track_e_smoke/test_e_negatives.py 用纯 stdlib 写
# （签名 test_E0XX(rep: _Reporter, tmp: Path) 不符合 pytest 测试函数约定），
# 设计上是 ``python tests/track_e_smoke/test_e_negatives.py`` 直接跑。
#
# 在 pytest 体系下让它们走 tests/regression/test_e_guardrails.py 的封装。
collect_ignore_glob = [
    "track_e_smoke/test_*.py",
]


# ============================================================
# pytest 全局 marker 注册（重复 pyproject.toml，更安全）
# ============================================================
def pytest_configure(config: pytest.Config) -> None:
    """注册自定义 marker，避免 ``--strict-markers`` 误判。"""
    for line in [
        "regression: 整合回归测试（Track-H 维护）",
        "smoke: 各 track 自带 smoke",
        "v1_2_gate: v1.2 发布门槛断言（决策 I）",
        "needs_engine_b: 需要 Track-B（杨派 D2）实现",
        "needs_engine_c: 需要 Track-C（任派 D3）实现",
        "needs_engine_d: 需要 Track-D（高派 D4）实现",
    ]:
        config.addinivalue_line("markers", line)


# ============================================================
# 共用路径
# ============================================================

@pytest.fixture(scope="session")
def repo_root() -> Path:
    """仓库根目录。"""
    return ROOT


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """tests/fixtures/ 目录。"""
    return ROOT / "tests" / "fixtures"


# ============================================================
# 14 案 fixture
# ============================================================

@pytest.fixture(scope="session")
def all_real_case_ids() -> list[str]:
    """10 个完整 case_id（cases-index 真实案例）。"""
    from tests.fixtures.cases import list_real_cases
    return list_real_cases()


@pytest.fixture(scope="session")
def validated_case_ids() -> list[str]:
    """3 个有 feedback.md 的真实失验案例。"""
    from tests.fixtures.cases import list_validated_cases
    return list_validated_cases()


@pytest.fixture
def case_input(request: pytest.FixtureRequest):
    """参数化加载 case → ParsedInput。

    用法 1：``request.param`` 是 case_id 字符串（建议 indirect=True）
        @pytest.mark.parametrize("case_input", [
            "C-2026-001", "C-2026-002"
        ], indirect=True)
        def test_xxx(case_input):
            assert case_input.bazi.day_master == "壬"

    用法 2：在测试函数中显式指定，则 ``request.param`` 缺省返回首案。
    """
    from tests.fixtures.cases import load_case
    case_id = getattr(request, "param", None)
    if case_id is None:
        case_id = "C-2026-001"
    return load_case(case_id)


# ============================================================
# YAML 数据 fixture
# ============================================================

@pytest.fixture(scope="session")
def feedback_truth(fixtures_dir: Path) -> dict:
    """``tests/fixtures/feedback_ground_truth.yaml`` 解析为 dict。"""
    p = fixtures_dir / "feedback_ground_truth.yaml"
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict), f"feedback_ground_truth.yaml 顶层非 dict"
    return data


@pytest.fixture(scope="session")
def v1_0_baseline(fixtures_dir: Path) -> dict:
    """``tests/fixtures/v1_0_baseline.yaml`` 解析为 dict。"""
    p = fixtures_dir / "v1_0_baseline.yaml"
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict)
    return data


@pytest.fixture(scope="session")
def regression_baseline(repo_root: Path) -> dict:
    """``tests/regression_baseline.yaml`` 解析为 dict（6 项门槛定义）。"""
    p = repo_root / "tests" / "regression_baseline.yaml"
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict)
    assert "gates" in data and len(data["gates"]) == 6, "必须有 6 项 gate"
    return data
