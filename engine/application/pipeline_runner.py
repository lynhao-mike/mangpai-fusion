"""应用层流水线用例：编排 D1-D4 引擎、渲染与自迭代边界。"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal, Optional, Union

from engine.application.candidates import _extract_candidates
from engine.application.dual_engine_adapter import analyze_dual_engine
from engine.application.fusion_engine_v2 import build_final_prediction
from engine.application.integration import integrate
from engine.application.ports import PipelineAdapters
from engine.application.prediction_layer import build_prediction_output
from engine.application.prediction_signals import (
    extract_dtt_signal,
    extract_mp_signal,
    extract_ziping_signal,
)
from engine.application.timing import PIPELINE_THRESHOLD_SECONDS, PipelineTiming
from engine.domain.analysis import AnalysisOutput
from engine.energy.evaluator import evaluate_energy
from engine.infrastructure.findings_repository import _save_findings
from engine.pangzheng.pangzheng import support_with_shensha
from engine.picture.matcher import match_picture
from engine.predicates.types import ParsedInput
from engine.yingqi.gate import gate_yingqi
from engine.yingqi.types import GateResult

logger = logging.getLogger(__name__)

def run_pipeline(
    parsed: ParsedInput,
    *,
    cases_dir: Optional[Union[str, Path]] = None,
    write_findings: bool = True,
    timing: Optional[PipelineTiming] = None,
    threshold_seconds: float = PIPELINE_THRESHOLD_SECONDS,
) -> AnalysisOutput:
    """v1.2 流水线编排：parsed → AnalysisOutput（W1-W4 + integrate）。

    输入：ParsedInput（preflight 解析后）
    输出：AnalysisOutput（含完整 trace_id 链 + hash 链校验 + ``timing`` 属性）

    流程（每步前后均含耗时埋点）：
        Step 2 [energy]    evaluate_energy(parsed)
        Step 3 [picture]   match_picture(energy, parsed)
        Step 4 [yingqi]    gate_yingqi(...) × N 候选事件
        Step 5 [pangzheng] support_with_shensha(parsed, energy, picture, gates)
        Step 6 [integrate] integrate(...)

    （Step 1 preflight / Step 7 render / Step 8 self_iter 由 ``run_pipeline_e2e``
    负责，本函数仅负责中间 5 步。如外层 ``timing`` 注入则共享同一个计时器。）

    Args:
        parsed:            ParsedInput（preflight 已通过）。
        cases_dir:         cases/ 根目录（None=仓库根 cases/）。
        write_findings:    是否落盘 D1-D4 + analysis_output.json + timing.json。
                           外层 e2e 会在所有 8 步完成后统一落盘，因此 e2e 调用本
                           函数时传 ``False``。
        timing:            外层注入的 PipelineTiming；为 None 时本函数自建一个。
        threshold_seconds: 耗时护栏阈值（秒），仅在自建 timing 时生效。

    Returns:
        AnalysisOutput；附带 ``output.timing`` 引用本次运行的 PipelineTiming。
    """
    own_timing = timing is None
    if timing is None:
        timing = PipelineTiming(threshold_seconds=threshold_seconds)

    # Step 2: D1 段派
    with timing.step("energy"):
        energy = evaluate_energy(parsed)

    # Step 3: D2 杨派
    with timing.step("picture"):
        picture = match_picture(energy, parsed)

    # Step 4: D3 任派 — 从 known_facts 生成候选事件
    with timing.step("yingqi"):
        gate_results: list[GateResult] = []
        candidates = _extract_candidates(parsed)
        for year, event, domain in candidates:
            gr = gate_yingqi(year, event, domain, energy, picture, parsed)
            if gr.passed_layers >= 1:
                gate_results.append(gr)

    # Step 5: D4 高派
    with timing.step("pangzheng"):
        support = support_with_shensha(parsed, energy, picture, gate_results)

    # Step 6: 整合
    with timing.step("integrate"):
        output = integrate(energy, picture, gate_results, support, parsed)

    # v1.6 · 双引擎适配层（理论派 + 盲派 + 融合层）—— 不参与 D1-D4 hash 链
    try:
        theory_findings, blind_findings, fusion_findings = analyze_dual_engine(
            parsed=parsed,
            energy=energy,
            picture=picture,
            gate_results=gate_results,
            support=support,
        )
        output.theory_findings = theory_findings
        output.blind_findings = blind_findings
        output.fusion_findings = fusion_findings
        output.parallel_analysis = fusion_findings.parallel_analysis
    except Exception as e:  # noqa: BLE001
        logger.warning("dual engine adapter 失败：%s", e)
        output.theory_findings = None
        output.blind_findings = None
        output.fusion_findings = None

    # v4.2 预测层（增强版）：独立隔离，失败不影响三派 findings
    try:
        with timing.step("prediction"):
            ziping_sig = extract_ziping_signal(energy, output.theory_findings)
            dtt_sig = extract_dtt_signal(picture)
            mp_sig = extract_mp_signal(gate_results)
            final_pred = build_final_prediction(ziping_sig, dtt_sig, mp_sig)
            # v4.2 增强：传递 parsed_input 用于大运信息提取和概率校准
            prediction = build_prediction_output(
                final_pred,
                output.fusion_findings,
                gate_results,
                use_calibration=True,   # 启用概率校准
                parsed_input=parsed,     # 传递 parsed_input 给增强时间窗推理
            )
        output.prediction = prediction
    except Exception as _pe:  # noqa: BLE001
        logger.warning("v4.2 prediction layer（增强版）失败：%s", _pe)
        output.prediction = None

    # F6 · 流年回溯（截止当前年份）—— 不参与 hash 链，独立挂载到 output
    try:
        from datetime import datetime as _dt
        from engine.yingqi.retrospective import scan_retrospective
        retrospective = scan_retrospective(parsed, current_year=_dt.now().year)
        object.__setattr__(output, "retrospective", retrospective)
    except Exception as e:  # noqa: BLE001
        logger.warning("retrospective scan 失败：%s", e)
        object.__setattr__(output, "retrospective", None)

    # 把 render 所需的原始 ParsedInput 挂到 output 上。
    # AnalysisOutput 的声明字段专注于 D1-D4 findings，不序列化完整输入；但
    # render_from_output() 需要 bazi/dayun/birth 等上下文渲染报告头与画像表。
    # 使用动态属性维持现有 JSON schema 不变，同时避免退化到占位 ParsedInput。
    object.__setattr__(output, "_parsed", parsed)

    # 把 timing 引用挂到 output 上（dataclass 非 frozen → 可动态附加）。
    # 注意：to_dict/to_json 仅序列化声明字段，timing 不会泄漏进 JSON 制品。
    object.__setattr__(output, "timing", timing)

    # 落盘 findings + timing.json（e2e 模式下 write_findings=False，由 e2e 兜底）
    if write_findings:
        try:
            findings_dir = _save_findings(output, cases_dir=cases_dir)
            timing.write_to(findings_dir, case_id=output.case_id)
        except Exception as e:  # noqa: BLE001 — 落盘失败不阻断业务
            logger.warning("findings 落盘失败：%s", e)

    # 仅当本函数自建 timing（独立调用）时立即触发护栏；外层 e2e 注入时由 e2e
    # 在 8 步全部完成后统一调用 check_threshold()，避免重复警告 & 中间态误报。
    if own_timing:
        timing.check_threshold()

    return output

def run_pipeline_e2e(
    input_md_path: Union[str, Path],
    *,
    cases_dir: Optional[Union[str, Path]] = None,
    cases_index_path: Optional[Union[str, Path]] = None,
    do_render: bool = False,
    do_self_iter: bool = False,
    template_name: str = "report-v1.3.md",
    report_variant: str = "standard",
    threshold_seconds: float = PIPELINE_THRESHOLD_SECONDS,
    adapters: Optional[PipelineAdapters] = None,
    error_policy: Literal["tolerant", "strict"] = "tolerant",
) -> tuple[AnalysisOutput, PipelineTiming]:
    """端到端 8 步编排（v1.2.1 性能监控版）。

    8 个步骤每步前后均含 ``time.perf_counter()`` 埋点，最终落盘
    ``cases/C-XXX/findings/timing.json``。总耗时超过 ``threshold_seconds``
    时输出醒目警告（[PERF WARN]），但**不阻断** findings/报告落盘。

    Steps:
        1. preflight   — PreflightPort.parse(input_md_path) → ParsedInput
        2. energy      — D1 段派
        3. picture     — D2 杨派
        4. yingqi      — D3 任派
        5. pangzheng   — D4 高派
        6. integrate   — D1-D4 → AnalysisOutput
        7. render      — ReportRenderPort.render（do_render=True 时）
        8. self_iter   — FeedbackIngestPort.ingest（do_self_iter=True 时）

    Args:
        input_md_path:     cases/C-XXX/input.md 路径。
        cases_dir:         cases/ 根目录（None=仓库根 cases/）。
        cases_index_path:  cases-index.md 路径，传给 preflight 做指纹防重。
        do_render:         是否调用 render_report 渲染 Markdown 报告。
        do_self_iter:      是否调用 feedback_loop 自迭代。
        template_name:     兼容参数；渲染统一收敛到 report-v1.3.md 标准模板。
        report_variant:    兼容参数；e2e/生产统一收敛到 standard。
        threshold_seconds: 端到端总耗时阈值（默认 60s）。
        error_policy:      ``"tolerant"``（默认）：render/self_iter/findings 失败仅
                           记录警告，不阻断返回；``"strict"``：上述步骤任一失败直接
                           抛出异常，供生产服务捕获并将 job 标记为 failed。

    Returns:
        ``(AnalysisOutput, PipelineTiming)``。

    Note:
        tolerant 模式下 Step 7/8/findings 任一异常时仅记录耗时 + 日志，不会让
        上游业务失败——这与 contracts/07-pipeline-flow § 十二 错误处理表保持一致。
        strict 模式由 ProductionAnalysisService 使用，确保交付完整性。
    """
    timing = PipelineTiming(threshold_seconds=threshold_seconds)

    # Step 1: preflight
    parsed: Optional[ParsedInput] = None
    adapters = adapters or _load_default_adapters()
    if adapters.preflight is None:
        raise ValueError("run_pipeline_e2e requires a PreflightPort adapter")
    with timing.step("preflight"):
        parsed = adapters.preflight.parse(
            Path(input_md_path),
            Path(cases_index_path) if cases_index_path else None,
        )

    # Steps 2-6: energy / picture / yingqi / pangzheng / integrate
    # write_findings=False —— 我们在 8 步全部完成后统一落盘
    output = run_pipeline(
        parsed,
        cases_dir=cases_dir,
        write_findings=False,
        timing=timing,
        threshold_seconds=threshold_seconds,
    )

    # Step 7: render（可选）
    if do_render:
        with timing.step("render"):
            try:
                if adapters.renderer is None:
                    raise ValueError("do_render=True requires a ReportRenderPort adapter")
                report_md = adapters.renderer.render(
                    output,
                    template_name=template_name,
                    variant=report_variant,
                    cases_dir=cases_dir,
                    skip_findings_save=True,
                )
                # 不写入 to_dict 的字段，仅作返回时附带；真正的落盘由 render_report 内部完成
                object.__setattr__(output, "report_md", report_md)
            except Exception as e:  # noqa: BLE001
                if error_policy == "strict":
                    raise
                logger.warning("render 步骤失败（不阻断）：%s", e)

    # Step 8: 自迭代（可选）
    if do_self_iter:
        with timing.step("self_iter"):
            try:
                if adapters.feedback is None:
                    raise ValueError("do_self_iter=True requires a FeedbackIngestPort adapter")
                adapters.feedback.ingest(output.case_id)
            except Exception as e:  # noqa: BLE001
                if error_policy == "strict":
                    raise
                logger.warning("self_iter 步骤失败（不阻断）：%s", e)

    # 统一落盘 findings + timing.json（即便 render/self_iter 失败也照常落）
    try:
        findings_dir = _save_findings(output, cases_dir=cases_dir)
        timing.write_to(findings_dir, case_id=output.case_id)
    except Exception as e:  # noqa: BLE001
        if error_policy == "strict":
            raise
        logger.warning("findings 落盘失败：%s", e)

    # 护栏断言：超 60s 仅警告、不阻断
    timing.check_threshold()

    return output, timing


def _load_default_adapters() -> PipelineAdapters:
    """延迟加载 infrastructure 默认适配器，保留旧调用方的 e2e 行为。"""
    from engine.infrastructure.adapters import default_pipeline_adapters

    return default_pipeline_adapters()
