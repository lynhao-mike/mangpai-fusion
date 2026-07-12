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
        "GO / HOLD / STOP 建议",
    ):
        assert heading in text
