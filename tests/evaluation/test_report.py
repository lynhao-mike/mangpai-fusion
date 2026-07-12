from engine.evaluation.models import CapabilityPosterior
from engine.evaluation.report import render_capability_report


def test_report_refuses_to_publish_permanent_expertise_language() -> None:
    text = render_capability_report(
        manifest_summary={"blind_candidate": 3, "development_only": 2},
        experiment_summary={"all_schools": {"utility": 0.61}},
        posteriors=[],
    )

    assert "暂定能力基线" in text
    assert "永久专长" not in text
    assert "样本与证据限制" in text
    assert "标签泄漏" in text
    assert "HOLD" in text
    for heading in (
        "评估范围与证据等级",
        "案例可用性与污染盘点",
        "任务覆盖与三态输出",
        "五维能力基线",
        "四组增量实验",
        "条件化能力后验",
        "校准与高风险误差",
        "评估门禁建议",
    ):
        assert heading in text


def test_report_five_dimension_section_displays_every_posterior_metric() -> None:
    posterior = CapabilityPosterior(
        school_id="ziping", task_id="education.credentials", chart_prototype_id="strong",
        claim_type="event", time_horizon="lifetime", evidence_completeness_band="complete",
        coverage_rate=0.75, discrimination_score=0.2, accuracy_score=0.8,
        calibration_error=0.1, posterior_mean=0.7, credible_interval=(0.4, 0.9),
        n_eff=6.0, evidence_grade="A", last_evaluated_at="2026-07-12T00:00:00Z",
        incremental_gain=0.15,
    )
    text = render_capability_report({}, {}, [posterior])
    for value in ("coverage=0.750", "discrimination=0.200", "accuracy=0.800",
                  "calibration=0.100", "incremental_gain=0.150", "interval=[0.400, 0.900]",
                  "N_eff=6.000", "evidence=A"):
        assert value in text
    assert text.count("## ") == 9
