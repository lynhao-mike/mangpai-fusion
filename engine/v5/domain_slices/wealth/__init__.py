"""财富域六源切片：只接入既有可审计结构、事件与应期 runner。"""

from __future__ import annotations

from engine.v5 import ditiansui_runner, duan_runner, gao_runner, ren_runner, ziping_runner
from engine.v5.domain_slices.career import run_legacy_domain_slice
from engine.v5.domain_slices.contract import DomainAnalysisContext, SliceResult


def ziping_wealth_slice(context: DomainAnalysisContext) -> SliceResult:
    """子平仅提供原局结构背景，不据此补造具体财富事件。"""

    return run_legacy_domain_slice(
        context,
        public_school="ziping",
        tasks=("structure.overview",),
        generator=ziping_runner.generate_claims,
        domain_id="wealth",
        domain_name="财富",
    )


def ditiansui_wealth_slice(context: DomainAnalysisContext) -> SliceResult:
    """滴天髓仅提供气势结构背景，不据此补造具体财富事件。"""

    return run_legacy_domain_slice(
        context,
        public_school="ditiansui",
        tasks=("structure.overview",),
        generator=ditiansui_runner.generate_claims,
        domain_id="wealth",
        domain_name="财富",
    )


def gao_dechen_wealth_slice(context: DomainAnalysisContext) -> SliceResult:
    return run_legacy_domain_slice(
        context,
        public_school="gao_dechen",
        tasks=("wealth.debt", "wealth.major_loss_window"),
        generator=gao_runner.generate_claims,
        domain_id="wealth",
        domain_name="财富",
    )


def duan_jianye_wealth_slice(context: DomainAnalysisContext) -> SliceResult:
    return run_legacy_domain_slice(
        context,
        public_school="duan_jianye",
        tasks=("wealth.debt", "wealth.major_loss_window"),
        generator=duan_runner.generate_claims,
        domain_id="wealth",
        domain_name="财富",
    )


def ren_fuhong_wealth_slice(context: DomainAnalysisContext) -> SliceResult:
    """任付红只提供可证伪重大损失应期，不输出结构或事件命题。"""

    return run_legacy_domain_slice(
        context,
        public_school="ren_fuhong",
        tasks=("wealth.major_loss_window",),
        generator=ren_runner.generate_claims,
        domain_id="wealth",
        domain_name="财富",
    )


WEALTH_GENERATORS = {
    "ziping": ziping_wealth_slice,
    "ditiansui": ditiansui_wealth_slice,
    "gao_dechen": gao_dechen_wealth_slice,
    "duan_jianye": duan_jianye_wealth_slice,
    "ren_fuhong": ren_fuhong_wealth_slice,
}


__all__ = [
    "WEALTH_GENERATORS",
    "ditiansui_wealth_slice",
    "duan_jianye_wealth_slice",
    "gao_dechen_wealth_slice",
    "ren_fuhong_wealth_slice",
    "ziping_wealth_slice",
]
