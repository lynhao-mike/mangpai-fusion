from __future__ import annotations

import pytest


def test_school_domain_stat_exposes_small_sample_confidence_metrics() -> None:
    from tools.cross_school_scan import SchoolDomainStat

    stat = SchoolDomainStat(school="段", domain="财运", hits=1, misses=0)
    cell = stat.to_report_cell()

    assert cell["hits"] == 1
    assert cell["misses"] == 0
    assert cell["n"] == 1
    assert cell["hit_rate"] == 1.0
    assert cell["beta_mean"] == pytest.approx(2 / 3)
    assert cell["ci_low"] is not None
    assert cell["ci_high"] is not None
    assert 0 <= cell["ci_low"] <= cell["ci_high"] <= 1


def test_school_domain_stat_empty_interval_is_none() -> None:
    from tools.cross_school_scan import SchoolDomainStat

    stat = SchoolDomainStat(school="任", domain="应期")

    assert stat.hit_rate is None
    assert stat.beta_mean is None
    assert stat.wilson_interval() == (None, None)
