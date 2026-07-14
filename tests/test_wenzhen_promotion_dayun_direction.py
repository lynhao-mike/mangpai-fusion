"""问真转案工具大运方向回归测试。"""
from __future__ import annotations

import pytest

from tools.promote_wenzhen_first5_cases import _build_dayun as build_first5_dayun
from tools.promote_wenzhen_pending_analysis_samples import (
    _build_dayun as build_pending_dayun,
)
from tools.promote_wenzhen_ready_batch import _build_dayun as build_ready_dayun


@pytest.mark.parametrize("builder", [build_ready_dayun, build_first5_dayun])
def test_staging_builders_use_yin_year_male_reverse(builder):
    staging = {
        "birth": {"公历": "1985-10-03 17:20"},
        "qian_kun": "乾",
        "start": "出生后8年6月22天5小时起运",
        "pillars": {"Y": "乙,丑"},
    }

    result = builder(staging, "乙酉")

    assert result["顺逆"] == "逆"
    assert [step["干支"] for step in result["排布"][:3]] == ["甲申", "癸未", "壬午"]


@pytest.mark.parametrize("builder", [build_ready_dayun, build_first5_dayun])
def test_staging_builders_use_yin_year_female_forward(builder):
    staging = {
        "birth": {"公历": "1985-10-03 17:20"},
        "qian_kun": "坤",
        "start": "出生后8年6月22天5小时起运",
        "pillars": {"Y": "乙,丑"},
    }

    result = builder(staging, "乙酉")

    assert result["顺逆"] == "顺"
    assert [step["干支"] for step in result["排布"][:3]] == ["丙戌", "丁亥", "戊子"]


def test_pending_builder_uses_yin_year_male_reverse():
    sample = {
        "base": {"Solar": "1985-10-03 17:20"},
        "bazi": "乙丑乙酉乙亥乙酉",
        "qian_kun": "乾",
        "start": "出生后8年6月22天5小时起运",
    }

    result = build_pending_dayun(sample, "乙酉")

    assert result["顺逆"] == "逆"
    assert [step["干支"] for step in result["排布"][:3]] == ["甲申", "癸未", "壬午"]


def test_pending_builder_uses_yin_year_female_forward():
    sample = {
        "base": {"Solar": "1985-10-03 17:20"},
        "bazi": "乙丑乙酉乙亥乙酉",
        "qian_kun": "坤",
        "start": "出生后8年6月22天5小时起运",
    }

    result = build_pending_dayun(sample, "乙酉")

    assert result["顺逆"] == "顺"
    assert [step["干支"] for step in result["排布"][:3]] == ["丙戌", "丁亥", "戊子"]
