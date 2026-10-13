"""婚姻域六源切片：只接入既有可审计事件与应期 runner。"""

from __future__ import annotations

from engine.v5 import ditiansui_runner, duan_runner, gao_runner, ren_runner, yang_runner, ziping_runner
from engine.v5.domain_slices.career import run_legacy_domain_slice
from engine.v5.domain_slices.contract import DomainAnalysisContext, SliceResult


def ziping_marriage_slice(context: DomainAnalysisContext) -> SliceResult:
    return run_legacy_domain_slice(
        context,
        public_school="ziping",
        tasks=("marriage.late_marriage",),
        generator=ziping_runner.generate_claims,
        domain_id="marriage",
        domain_name="婚姻",
    )


def ditiansui_marriage_slice(context: DomainAnalysisContext) -> SliceResult:
    """滴天髓仅提供气势结构背景，不据此补造具体婚姻事件。"""

    return run_legacy_domain_slice(
        context,
        public_school="ditiansui",
        tasks=("structure.overview",),
        generator=ditiansui_runner.generate_claims,
        domain_id="marriage",
        domain_name="婚姻",
    )


def gao_dechen_marriage_slice(context: DomainAnalysisContext) -> SliceResult:
    return run_legacy_domain_slice(
        context,
        public_school="gao_dechen",
        tasks=("marriage.event_window",),
        generator=gao_runner.generate_claims,
        domain_id="marriage",
        domain_name="婚姻",
    )


def duan_jianye_marriage_slice(context: DomainAnalysisContext) -> SliceResult:
    return run_legacy_domain_slice(
        context,
        public_school="duan_jianye",
        tasks=("marriage.divorce_or_remarriage", "marriage.event_window"),
        generator=duan_runner.generate_claims,
        domain_id="marriage",
        domain_name="婚姻",
    )


def yang_qingjuan_marriage_slice(context: DomainAnalysisContext) -> SliceResult:
    return run_legacy_domain_slice(
        context,
        public_school="yang_qingjuan",
        tasks=("marriage.divorce_or_remarriage",),
        generator=yang_runner.generate_claims,
        domain_id="marriage",
        domain_name="婚姻",
    )


def ren_fuhong_marriage_slice(context: DomainAnalysisContext) -> SliceResult:
    """任付红只提供可证伪婚姻应期，不输出结构或事件命题。"""

    return run_legacy_domain_slice(
        context,
        public_school="ren_fuhong",
        tasks=("marriage.event_window",),
        generator=ren_runner.generate_claims,
        domain_id="marriage",
        domain_name="婚姻",
    )


MARRIAGE_GENERATORS = {
    "ziping": ziping_marriage_slice,
    "ditiansui": ditiansui_marriage_slice,
    "gao_dechen": gao_dechen_marriage_slice,
    "duan_jianye": duan_jianye_marriage_slice,
    "yang_qingjuan": yang_qingjuan_marriage_slice,
    "ren_fuhong": ren_fuhong_marriage_slice,
}


__all__ = [
    "MARRIAGE_GENERATORS",
    "ditiansui_marriage_slice",
    "duan_jianye_marriage_slice",
    "gao_dechen_marriage_slice",
    "ren_fuhong_marriage_slice",
    "yang_qingjuan_marriage_slice",
    "ziping_marriage_slice",
]
