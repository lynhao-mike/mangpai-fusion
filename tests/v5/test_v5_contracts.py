"""v5 五派命题图契约测试。"""

from __future__ import annotations

from engine.v5 import run_v5
from engine.v5.domain import (
    V5Claim,
    V5Confidence,
    V5Evidence,
    V5Output,
    V5_SCHOOLS,
)


def _sample_claim(**kwargs) -> V5Claim:
    defaults = dict(
        claim_id="v5cl-sample",
        school="ziping",
        domain="事业",
        claim="原局结构支持事业责任上升，但需岁运触发。",
        claim_type="structure_claim",
        stance="support",
        polarity="positive",
        confidence=V5Confidence(tier="★★★", score=0.66, note="测试命题"),
        evidence=[
            V5Evidence(
                evidence_id="v5ev-sample",
                source="unit-test",
                text="月令与十神结构提供事业判断依据。",
                node_refs=["chart:root"],
                rule_ids=["TEST-RULE-001"],
            )
        ],
        timing_hints=[{"type": "dayun", "label": "测试大运"}],
        probabilistic=True,
        falsifiable="若反馈显示对应阶段无事业责任变化，则命题需降权。",
    )
    defaults.update(kwargs)
    return V5Claim(**defaults)


def test_v5_five_school_constants():
    assert V5_SCHOOLS == (
        "ziping",
        "ditiansui",
        "gao_dechen",
        "duan_jianye",
        "yang_qingjuan",
    )


def test_v5_claim_round_trip():
    claim = _sample_claim()
    restored = V5Claim.from_dict(claim.to_dict())
    assert restored == claim
    assert restored.role == "structure_law"


def test_v5_output_round_trip():
    output = run_v5(
        {"case_id": "C-TEST-V5", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]},
        claims=[
            _sample_claim(),
            _sample_claim(
                claim_id="v5cl-duan",
                school="duan_jianye",
                claim_type="event_claim",
                claim="事业事件需看宫位与十神落点。",
            ),
        ],
    )
    restored = V5Output.from_json(output.to_json())
    assert restored == output
    assert restored.hash() == output.hash()


def test_run_v5_default_loads_production_rules_and_mvp_school_runners():
    output = run_v5({"case_id": "C-TEST-ZIPING", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})

    ziping_claims = [claim for claim in output.claims if claim.school == "ziping"]
    ditiansui_claims = [claim for claim in output.claims if claim.school == "ditiansui"]
    blind_rule_claims = [claim for claim in output.claims if claim.metadata.get("runner_state") == "school_rule"]
    stub_claims = [claim for claim in output.claims if claim.metadata.get("runner_state") == "stub"]

    assert len(ziping_claims) == 267
    assert 1 <= len(ditiansui_claims) <= 12
    assert {claim.school for claim in output.claims} == set(V5_SCHOOLS)
    assert all(claim.stance == "support" for claim in ziping_claims)
    assert all(claim.metadata.get("runner_state") == "production_rule" for claim in ziping_claims)
    assert all(claim.metadata.get("source_scope") == "production_rules" for claim in ziping_claims)
    assert all(claim.metadata.get("runner_state") == "production_rule" for claim in ditiansui_claims)
    assert all(claim.metadata.get("selection") == "v6_preprod_limited" for claim in ditiansui_claims)
    assert not any(claim.metadata.get("rule_id", "").startswith("ZP-CAND-") for claim in ziping_claims)
    assert {claim.school for claim in blind_rule_claims} >= {"gao_dechen", "duan_jianye", "yang_qingjuan"}
    assert all(claim.metadata.get("selection") == "v6_preprod_blind_limited" for claim in blind_rule_claims)
    assert stub_claims == []
    assert len(output.prediction_ledger.predictions) >= 5
    assert len(output.learning_signals) == len(output.claims) + len(output.prediction_ledger.predictions)


def test_run_v5_probability_whitelist_creates_ledger_entry():
    output = run_v5(
        {"case_id": "C-TEST-PROB", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]},
        claims=[_sample_claim(domain="事业", probabilistic=True)],
    )
    assert len(output.prediction_ledger.predictions) == 5
    prediction = output.prediction_ledger.predictions[0]
    assert prediction.domain == "事业"
    assert prediction.probability_range == (0.35, 0.55)
    assert {item.domain for item in output.prediction_ledger.predictions} >= {"事业", "财富", "婚姻", "健康", "学业"}


def test_run_v5_rejects_non_whitelist_probability_domain():
    output = run_v5(
        {"case_id": "C-TEST-CHARACTER", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]},
        claims=[_sample_claim(domain="性格", probabilistic=True)],
    )
    assert {item.domain for item in output.prediction_ledger.predictions} == {"事业", "财富", "婚姻", "健康", "学业"}
    assert all(item.domain != "性格" for item in output.prediction_ledger.predictions)
    probability_stage = [item for item in output.arbitration_results if item.stage == "probability_timing"][0]
    assert probability_stage.probabilistic_allowed is False
