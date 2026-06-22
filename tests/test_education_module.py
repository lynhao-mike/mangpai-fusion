from __future__ import annotations

from engine.education import EducationSignal, analyze_education


def test_education_without_anchors_never_outputs_final_degree() -> None:
    profile = analyze_education(
        birth_year=1984,
        signals=[
            EducationSignal("ziping", "ability", "印旺身强，多主读书顺利", 0.8),
            EducationSignal("blind", "degree_direct", "文昌入命，多主读书有成", 0.8),
        ],
        anchors={},
    )

    assert profile.timeline[3]["stage"] == "大学阶段"
    assert profile.timeline[3]["year_range"] == (2002, 2006)
    assert profile.usable_for_final_degree is False
    assert "待反馈候选" in profile.degree_verdict
    assert any("禁止" in risk for risk in profile.risks)


def test_education_with_anchors_can_output_degree_candidate() -> None:
    profile = analyze_education(
        birth_year=1984,
        signals=[
            {"school": "ziping", "kind": "ability", "statement": "官印相生", "strength": 0.7},
            {"school": "tiaohou_ditiansui", "kind": "environment", "statement": "水木清华", "strength": 0.7},
        ],
        anchors={
            "gaokao": "已提供",
            "admission": "本科批",
            "school": "某本科院校",
            "graduation": "2008",
            "highest_degree": "本科",
        },
    )

    assert profile.usable_for_final_degree is True
    assert profile.degree_verdict == "本科"
    assert "某本科院校" in profile.institution_verdict
