from __future__ import annotations

from engine.picture.wealth_15tier import _make_band, compute_wealth_15tier


class FakeEnergy:
    wealth_ceiling = "巨富级·上"
    layer_count = 4


class FakeGuanming:
    rank = 2
    type = "化官生印"


class FakeCaifu:
    rank = 1
    type = "官杀库"


class FakePicture:
    caifu = FakeCaifu()
    guanming = FakeGuanming()
    evidence = []


def _assert_ordered(band) -> None:
    assert 1 <= band.low <= band.mid <= band.high <= 15


def test_make_band_normalizes_reversed_bounds() -> None:
    band = _make_band(13, 13, 12, "reversed bounds")

    assert band.low == 12
    assert band.mid == 13
    assert band.high == 13


def test_wealth_15tier_extreme_structural_case_stays_ordered_and_conservative() -> None:
    result = compute_wealth_15tier(FakeEnergy(), FakePicture())

    for band in [result.xueye, result.shiye, result.hunyin, result.caifu, result.guanming]:
        assert band is not None
        _assert_ordered(band)

    assert result.shiye.high <= 12
    assert result.shiye.mid <= result.shiye.high
    assert result.xueye.high <= 8
    assert result.hunyin.high <= 9
    assert result.caifu.high <= 12
