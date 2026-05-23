"""tests/regression/test_e_guardrails.py · 整合 Track-E E-001~E-008

把 ``tests/track_e_smoke/test_e_negatives.py`` 的 8 项负向测试以 pytest
fixture 方式重新封装。Track-E 的原始文件用纯 stdlib + ``_Reporter`` 累加
方式实现，签名 ``test_E0XX(rep, tmp)`` 不符合 pytest 测试函数约定。

策略：
    - **不修改** ``tests/track_e_smoke/`` 目录（08 § 二 H 列只读）
    - 直接 ``from tests.track_e_smoke.test_e_negatives import ...`` 复用底层函数
    - 每个 pytest 测试函数：构造一个临时 _Reporter + tmpdir，调用底层函数，
      把 _Reporter 末尾结果转换为 assert
    - tests/conftest.py 用 ``collect_ignore_glob`` 跳过 Track-E 原文件，
      避免 pytest 把签名不兼容的函数当成测试收集

验收（08 § 六）：8 条铁律的负向测试全过。

作者：Track-H · v1.2.0
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Callable

import pytest

# Track-E 原模块（pytest 已用 collect_ignore_glob 跳过其内置 test_* 函数收集）
from tests.track_e_smoke.test_e_negatives import (
    _Reporter,
    test_E001_missing_schema_version as _e001,
    test_E002_invalid_pillar as _e002,
    test_E003_star_pct_range as _e003,
    test_E004_yingqi_no_year as _e004,
    test_E005_blacklisted_rule as _e005,
    test_E006_three_layer_mismatch as _e006,
    test_E007_forbidden_phrase as _e007,
    test_E008_duplicate_fingerprint as _e008,
)

pytestmark = pytest.mark.regression


def _run_e_test(
    fn: Callable[..., None],
    needs_tmp: bool = False,
) -> None:
    """运行 Track-E 底层测试函数，把 _Reporter 结果转为 assert。

    每个底层函数往 ``rep`` 里 add 一条记录（PASS/FAIL/SKIP）。
    本封装提取唯一一条记录，FAIL → pytest fail with same msg。
    """
    rep = _Reporter()
    if needs_tmp:
        with tempfile.TemporaryDirectory() as td:
            fn(rep, Path(td))
    else:
        fn(rep)

    assert len(rep.results) == 1, (
        f"底层测试 {fn.__name__} 应仅记录 1 条结果，实有 {len(rep.results)}"
    )
    tid, status, msg = rep.results[0]
    if status == "FAIL":
        pytest.fail(f"[{tid}] {msg}")
    elif status == "SKIP":
        pytest.skip(f"[{tid}] {msg}")
    # status == "PASS" → 测试通过


# ============================================================
# E-001 ~ E-008
# ============================================================

def test_E001_missing_schema_version() -> None:
    """E-001 缺 schema_version → preflight FAIL"""
    _run_e_test(_e001, needs_tmp=True)


def test_E002_invalid_pillar() -> None:
    """E-002 四柱含非法字 '甲丑' → preflight FAIL"""
    _run_e_test(_e002, needs_tmp=True)


def test_E003_star_percent_out_of_range() -> None:
    """E-003 ★5 (50%) 区间不符 → linter FAIL"""
    _run_e_test(_e003, needs_tmp=False)


def test_E004_yingqi_missing_year() -> None:
    """E-004 应期断语无 yingqi_year → linter FAIL"""
    _run_e_test(_e004, needs_tmp=False)


def test_E005_blacklisted_rule_referenced() -> None:
    """E-005 引用 blacklisted 规律 → linter FAIL"""
    _run_e_test(_e005, needs_tmp=False)


def test_E006_three_layer_mismatch() -> None:
    """E-006 ★★★★★ + passed_layers=2 → three_layer_check FAIL"""
    _run_e_test(_e006, needs_tmp=False)


def test_E007_forbidden_phrase_warning() -> None:
    """E-007 含 '未来某年' → linter WARNING（W7）"""
    _run_e_test(_e007, needs_tmp=False)


def test_E008_duplicate_fingerprint() -> None:
    """E-008 指纹重复 → preflight FAIL"""
    _run_e_test(_e008, needs_tmp=True)
