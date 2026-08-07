"""财富与婚姻域切片的能力边界、公开 ID 与默认注册测试。"""

from __future__ import annotations

from datetime import date, datetime

from engine.v5.domain_slices import build_domain_registry
from engine.v5.domain_slices.career import _task
from engine.v5.domain_slices.contract import DomainAnalysisContext, DomainAnalysisRequest
from engine.v5.domain_slices.orchestrator import run_domain_analysis


def _context() -> DomainAnalysisContext:
    return DomainAnalysisContext(
        request=DomainAnalysisRequest(
            gender="乾",
            birth_datetime=datetime(1990, 1, 1, 12, 0),
            as_of_date=date(2024, 1, 1),
            domains=("wealth", "marriage"),
            output_dir="reports/domain-analysis",
        ),
        case_id="DA-WEALTH-MARRIAGE-TEST",
        pillars=("癸未", "甲寅", "壬戌", "丙午"),
        dayun=(
            {"ganzhi": "丙辰", "start_year": 2018},
            {"ganzhi": "丁巳", "start_year": 2028},
        ),
        current_dayun={"ganzhi": "丙辰", "start_year": 2018, "end_year": 2027},
        future_years=((2024, "甲辰"), (2025, "乙巳"), (2026, "丙午")),
        calculator="test-calculator",
    )


def test_full_registry_declares_real_wealth_and_marriage_capabilities() -> None:
    registry = build_domain_registry()

    assert len(registry) == 18
    assert registry.resolve("yang_qingjuan", "wealth").status == "unsupported"
    for school in ("ziping", "ditiansui", "gao_dechen", "duan_jianye", "ren_fuhong"):
        assert registry.resolve(school, "wealth").status == "implemented"
    for school in (
        "ziping",
        "ditiansui",
        "gao_dechen",
        "duan_jianye",
        "yang_qingjuan",
        "ren_fuhong",
    ):
        assert registry.resolve(school, "marriage").status == "implemented"


def test_wealth_and_marriage_slices_never_leak_legacy_school_ids() -> None:
    registry = build_domain_registry()
    context = _context()

    results = [
        registry.resolve(school, domain).generator(context)
        for school in (
            "ziping",
            "ditiansui",
            "gao_dechen",
            "duan_jianye",
            "yang_qingjuan",
            "ren_fuhong",
        )
        for domain in ("wealth", "marriage")
        if registry.resolve(school, domain).status == "implemented"
    ]
    serialized = str([result.to_dict() for result in results])

    assert "'school': 'gao'" not in serialized
    assert "'school': 'duan'" not in serialized
    assert "'school': 'yang'" not in serialized
    assert "'school': 'ren'" not in serialized
    assert all(
        claim.domain in {"财富", "婚姻"}
        for result in results
        for claim in result.claims
    )


def test_ren_wealth_and_marriage_slices_are_timing_only() -> None:
    registry = build_domain_registry()
    context = _context()

    for domain in ("wealth", "marriage"):
        result = registry.resolve("ren_fuhong", domain).generator(context)
        assert all(claim.claim_type == "timing_claim" for claim in result.claims)
        assert all(claim.timing_hints for claim in result.claims)


def test_yang_marriage_is_implemented_but_wealth_is_not_fabricated() -> None:
    registry = build_domain_registry()
    context = _context()

    marriage = registry.resolve("yang_qingjuan", "marriage").generator(context)
    assert marriage.status in {"implemented", "abstain"}
    assert all(claim.school == "yang_qingjuan" for claim in marriage.claims)
    assert registry.resolve("yang_qingjuan", "wealth").generator is None


def test_default_orchestrator_uses_full_domain_registry_without_opt_in() -> None:
    snapshot = run_domain_analysis(_context().request)
    coverage = {
        (item["school"], item["domain"]): item["status"]
        for item in snapshot.metadata["slice_coverage"]
    }

    # 能力注册为 implemented 不保证具体命盘命中；运行时可克制 abstain。
    assert coverage[("gao_dechen", "wealth")] in {"implemented", "abstain"}
    assert coverage[("yang_qingjuan", "wealth")] == "unsupported"
    assert coverage[("yang_qingjuan", "marriage")] in {"implemented", "abstain"}
    assert coverage[("ren_fuhong", "marriage")] in {"implemented", "abstain"}
    assert snapshot.engine_version == "domain-analysis-p3-three-domains"


def test_selected_domains_do_not_cross_contaminate_claims() -> None:
    snapshot = run_domain_analysis(_context().request)

    output = snapshot.to_output()
    assert {claim.domain for claim in output.claims} <= {"财富", "婚姻"}
    assert all(claim.domain != "事业" for claim in output.claims)


def test_structure_background_slices_do_not_fabricate_wealth_or_marriage_events() -> None:
    registry = build_domain_registry()
    context = _context()

    for school in ("ziping", "ditiansui"):
        wealth = registry.resolve(school, "wealth").generator(context)
        assert all(claim.claim_type == "structure_claim" for claim in wealth.claims)
    marriage = registry.resolve("ditiansui", "marriage").generator(context)
    assert all(claim.claim_type == "structure_claim" for claim in marriage.claims)


def test_high_risk_domain_tasks_are_marked_before_runner_execution() -> None:
    for task_id, domain_name in (
        ("wealth.debt", "财富"),
        ("wealth.major_loss_window", "财富"),
        ("marriage.divorce_or_remarriage", "婚姻"),
    ):
        task = _task(task_id, domain_name=domain_name)
        assert task.high_risk is True
        assert task.domain == domain_name

    assert _task("marriage.event_window", domain_name="婚姻").high_risk is False
