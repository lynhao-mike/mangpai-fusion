"""tools/render_report.py · 标准报告渲染器（产品 v1.3.0 / pipeline schema v1.4.0）

按 07-pipeline-flow.md § 九 + 08-agent-handoff.md § 二 F 实现。

公开 API
--------
render(energy, picture, gates, parsed, support, template_name)
    低级入口：直接传 D1-D4 dataclass。
    内置双护栏：先对 Markdown 文本运行 output_linter，遇到 ERROR 立即
    抛出 RenderGuardrailError，阻断报告落盘（07 § 八 要求）。

render_from_output(analysis_output, *, template_name, lint_before, cases_dir)
    高级入口：接受 engine.pipeline.AnalysisOutput，自动完成
    ① findings JSON 落盘 → ② 渲染模板 → ③ 双护栏 lint 校验。

RenderGuardrailError
    output_linter 返回 ERROR 时抛出，携带完整 LintResult。

save_findings(output, cases_dir)
    将 D1-D4 JSON 写入 cases/C-XXX/findings/。

AI 润色边界（决策 D · 永久锁定）
    仅 §H 命主画像版的 [AI-polish] 段允许修改（文字润色）。
    §A-§G 的所有 ★/% 数值、evidence chain、证伪条件不可改。

作者：Track-F
"""
from __future__ import annotations

import json
import re
import sys
import warnings
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional, Union

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.detail_expansion import DETAIL_DOMAINS, build_detail_expansions
from engine.domain.ids import compute_statement_id
from engine.energy.types import EnergyFindings
from engine.statement_runtime import write_statement_records
from engine.picture.types import PictureFindings
from engine.predicates.cycles import get_dayun_at_year, liunian_ganzhi
from engine.predicates.types import ParsedInput
from engine.yingqi.types import GateResult


_TEMPLATE_CACHE: dict[Path, tuple[tuple[int, int], str]] = {}
_FOR_BLOCK_RE = re.compile(
    r"\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}",
    re.DOTALL,
)
_IF_NOT_INNER_RE = re.compile(
    r"\{%\s*if\s+not\s+(\w+)\s*%\}((?:(?!\{%\s*if\b).)*?)\{%\s*endif\s*%\}",
    re.DOTALL,
)
_IF_INNER_RE = re.compile(
    r"\{%\s*if\s+(\w+)\s*%\}((?:(?!\{%\s*if\b).)*?)\{%\s*endif\s*%\}",
    re.DOTALL,
)
_VAR_RE = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")


def _write_text_if_changed(path: Path, text: str, *, encoding: str = "utf-8") -> bool:
    """仅在内容变化时写盘，减少批量重复渲染的无效 I/O。"""
    if path.exists():
        try:
            if path.read_text(encoding=encoding) == text:
                return False
        except OSError:
            pass
    path.write_text(text, encoding=encoding)
    return True


# ============================================================
# 0. 双护栏异常 + 工具函数
# ============================================================

class RenderGuardrailError(RuntimeError):
    """output_linter 在渲染后报告中发现 ERROR 级别问题时抛出。

    按 07-pipeline-flow.md § 八/§ 十二：output_linter 拒绝时，
    流水线中断，不落盘报告；findings JSON 保留以便 debug。

    Attributes:
        lint_result: 完整的 LintResult 对象，含所有 errors / warnings。
        report:      渲染后但未通过 lint 的 Markdown 文本（仅供 debug）。
    """
    def __init__(self, lint_result: Any, report: str) -> None:
        errors = getattr(lint_result, "errors", [])
        msg = (
            f"output_linter 拒绝报告：{len(errors)} 个 ERROR\n"
            + "\n".join(
                f"  [{e.code}] {getattr(e, 'location', '?')}: {e.message}"
                for e in errors[:10]
            )
        )
        super().__init__(msg)
        self.lint_result = lint_result
        self.report = report


def save_findings(
    output: Any,
    cases_dir: Optional[Union[str, Path]] = None,
) -> Path:
    """将 D1-D4 Findings JSON 写入 cases/C-XXX/findings/。

    兼容保留工具层公开 API；实际落盘逻辑统一委托给
    engine.infrastructure.findings_repository，避免工具层与基础设施层
    各维护一份 JSON 序列化/文件写入实现。
    """
    from engine.infrastructure.findings_repository import save_findings as _save_findings

    return _save_findings(output, cases_dir=cases_dir)

def render_from_output(
    analysis_output: Any,
    *,
    template_name: Optional[str] = None,
    variant: str = "standard",
    lint_before: bool = True,
    cases_dir: Optional[Union[str, Path]] = None,
    skip_findings_save: bool = False,
    report_schema: Literal["v5", "v6"] = "v6",
) -> str:
    """高级渲染入口：接受 AnalysisOutput，完成全链路。

    流程（按当前默认命理师报告标准）：
        1. 将 D1-D4 JSON 落盘到 cases/C-XXX/findings/
        2. 调用 render() 生成命理师报告 Markdown
        3. 落盘 cases/C-XXX/statement_index.json（statements 列表）
        4. 调用 output_linter.lint()；如有 ERROR 则抛 RenderGuardrailError

    Args:
        analysis_output: engine.pipeline.AnalysisOutput 实例。
        template_name:   兼容参数；None 默认收敛到 report-v6.md；report-v5.md 作为兼容 alias。
        variant:         兼容参数；历史 master/client/v1.2/v1.4 均收敛到 standard。
        lint_before:     是否启用双护栏 lint（默认 True；测试时可关闭）。
        cases_dir:       cases/ 目录路径（None = 仓库根 cases/）。
        report_schema:   展示层 schema；默认 v6，v5 仅保留旧系统兼容。

    Returns:
        通过 lint 的 Markdown 报告字符串。

    Raises:
        RenderGuardrailError: lint 返回任何 ERROR 时。
    """
    # Step 1: 落盘 findings JSON。e2e 可跳过，避免重复写盘。
    if not skip_findings_save:
        try:
            save_findings(analysis_output, cases_dir)
        except Exception as exc:
            # 落盘失败不阻断渲染，但必须显式暴露，否则后续 D5 反馈会丢失溯源材料。
            warnings.warn(
                f"save_findings failed for {getattr(analysis_output, 'case_id', 'UNKNOWN')}: {exc}",
                RuntimeWarning,
                stacklevel=2,
            )

    # Step 2: 拆包 AnalysisOutput 字段
    energy = getattr(analysis_output, "energy")
    picture = getattr(analysis_output, "picture")
    gates = getattr(analysis_output, "gate_results", [])
    support = getattr(analysis_output, "support", None)
    final_conclusions = getattr(analysis_output, "final_conclusions", None) or []
    retrospective = getattr(analysis_output, "retrospective", None)
    parallel_analysis = getattr(analysis_output, "parallel_analysis", None)
    parsed = getattr(analysis_output, "_parsed", None)

    # 如果 AnalysisOutput 没有 _parsed（它不存储 ParsedInput），
    # 尝试从 energy.case_id 重建一个最小 ParsedInput
    if parsed is None:
        parsed = _minimal_parsed_from_energy(energy)

    # Step 3: 渲染（捕获 ctx 用于落盘 statement_index）
    captured_ctx: dict = {}
    report = render(
        energy=energy,
        picture=picture,
        gates=gates,
        parsed=parsed,
        support=support,
        final_conclusions=final_conclusions,
        retrospective=retrospective,
        parallel_analysis=parallel_analysis,
        template_name=template_name,
        variant=variant,
        _skip_lint=not lint_before,
        _capture_ctx_to=captured_ctx,
        report_schema=report_schema,
    )

    # Step 4: 按 C-2026-025 标准落盘 statement_index.json，并同步生成 statement_records.json。
    case_id = (
        getattr(analysis_output, "case_id", None)
        or getattr(getattr(analysis_output, "energy", None), "case_id", None)
        or "UNKNOWN"
    )
    try:
        cases_root = Path(cases_dir) if cases_dir else ROOT / "cases"
        idx_dir = cases_root / case_id
        idx_dir.mkdir(parents=True, exist_ok=True)
        write_statement_records(captured_ctx, case_id, idx_dir)
        idx = _build_statement_index(captured_ctx, case_id)
        idx_text = json.dumps(idx, ensure_ascii=False, indent=2)
        _write_text_if_changed(idx_dir / "statement_index.json", idx_text)
    except Exception as exc:
        # statement runtime/index 落盘失败不阻断报告交付，但必须显式暴露（否则 D5 反馈会静默降级）。
        warnings.warn(
            f"statement runtime artifact write failed for {case_id}: {exc}",
            RuntimeWarning,
            stacklevel=2,
        )

    return report


def _minimal_parsed_from_energy(energy: EnergyFindings) -> ParsedInput:
    """从 EnergyFindings 重建最小 ParsedInput（仅 render 所需字段）。"""
    from engine.predicates.types import Dayun
    # EnergyFindings 不存储 ParsedInput，但 render 只需 case_id / bazi / dayun / birth
    # 这些信息在 energy 的 debug_info 中没有，所以我们构造一个最小占位
    # (render 的 birth_year fallback 逻辑会用到 dayun.起运年 - dayun.起运岁)
    stub = ParsedInput.__new__(ParsedInput)
    object.__setattr__(stub, "case_id", energy.case_id or "UNKNOWN")
    object.__setattr__(stub, "bazi", None)
    object.__setattr__(stub, "dayun", None)
    object.__setattr__(stub, "birth", {})
    object.__setattr__(stub, "shensha", {})
    object.__setattr__(stub, "known_facts", [])
    object.__setattr__(stub, "questions", [])
    object.__setattr__(stub, "fingerprint", "")
    object.__setattr__(stub, "preflight_warnings", [])
    object.__setattr__(stub, "schema_version", "1.2.0")
    object.__setattr__(stub, "case_meta", {})
    object.__setattr__(stub, "twelve_changsheng", {})
    return stub



# ============================================================
# 一、ViewModel：把上游 dataclass 转成模板友好的 dict
# ============================================================

STAR_ICONS = {True: "✓", False: "✗"}
LAYER_ICONS = {True: "✓", False: "✗"}


# ============================================================
# 1.5 statement_id 计算（v1.3 D1）
# ============================================================

def _compute_statement_id(case_id: str, rule_ids: list[str]) -> str:
    """v1.3 D1：稳定的断语 ID。

    兼容旧私有函数名；事实源在 engine.domain.ids.compute_statement_id。
    应期类断语应在 rule_ids 中追加 ``"YEAR-{year}"`` 标记，避免不同年份
    相同 evidence 集合产生 ID 碰撞。
    """
    return compute_statement_id(case_id, rule_ids)


def _star_pct(conf) -> tuple[int, int]:
    """从 Confidence 取 (star, pct%)；兜底返回 (0, 0)。"""
    if conf is None:
        return 0, 0
    star = getattr(conf, "star", 0) or 0
    pct = getattr(conf, "percent", 0) or 0
    if isinstance(pct, float) and pct <= 1.0:
        pct = int(round(pct * 100))
    return int(star), int(pct)


def _evidence_list(obj) -> list[dict]:
    """从 dataclass 或 dict 的 evidence 字段提取 [{rule_id, school, description}, ...]。"""
    ev = getattr(obj, "evidence", None) or []
    out = []
    for e in ev:
        if hasattr(e, "rule_id"):
            out.append({"rule_id": e.rule_id, "school": e.school,
                        "description": getattr(e, "description", "")})
        elif isinstance(e, dict):
            out.append({"rule_id": e.get("rule_id", "?"),
                        "school": e.get("school", "?"),
                        "description": e.get("description", "")})
    return out


def _birth_str(parsed: ParsedInput) -> str:
    birth = parsed.birth or {}
    return str(birth.get("公历", birth.get("农历", "—")))


def _qian_kun_from(parsed: ParsedInput) -> str:
    """从 case_id 或性别字段推导命式（乾/坤）。"""
    case_id = str(getattr(parsed, "case_id", "") or "") if parsed else ""
    m = re.match(r"^C-\d{4}-\d{3}-([乾坤])-", case_id)
    if m:
        return m.group(1)

    gender = str(((getattr(parsed, "birth", None) or {}).get("性别", "")) if parsed else "")
    return {
        "M": "乾",
        "男": "乾",
        "乾": "乾",
        "F": "坤",
        "女": "坤",
        "坤": "坤",
    }.get(gender, "—")


def _dayun_year_range(step: Any) -> Optional[tuple[int, int]]:
    """兼容本地 ParsedInput.起讫年 与 preflight ParsedInput.起讫。"""
    years = getattr(step, "起讫年", None)
    if years is not None:
        try:
            return int(years[0]), int(years[1])
        except Exception:
            pass

    text = getattr(step, "起讫", None)
    if isinstance(text, str):
        m = re.match(r"^\s*(\d{4})\s*[-—~～]\s*(\d{4})\s*$", text)
        if m:
            return int(m.group(1)), int(m.group(2))
    return None


def _dayun_str(parsed: ParsedInput) -> str:
    try:
        steps = parsed.dayun.排布
        if not steps:
            return "—"
        parts = []
        for s in steps[:4]:
            year_range = _dayun_year_range(s)
            year_text = (
                f"{year_range[0]}-{year_range[1]}"
                if year_range is not None
                else str(getattr(s, "起讫", "—"))
            )
            parts.append(f"{year_text}【{s.干支}】")
        return "  ".join(parts)
    except Exception:
        return "—"


def _bazi_str(parsed: ParsedInput) -> str:
    if parsed is None:
        return "—"
    b = getattr(parsed, "bazi", None)
    if b is None:
        return "—"

    def _pillar(name: str) -> str:
        val = getattr(b, name, None)
        if val is None and isinstance(b, dict):
            val = b.get(name)
        return str(val or "")

    pillars = [_pillar(name) for name in ("年柱", "月柱", "日柱", "时柱")]
    return "".join(pillars) if all(pillars) else "—"


def _dayun_full_table(parsed: ParsedInput) -> list[dict]:
    """F9 · 全 9 步大运表（含当前标记）。

    行：[{seq, ganzhi, age_range, year_range, is_current}]
    """
    out: list[dict] = []
    try:
        steps = parsed.dayun.排布
        if not steps:
            return out
        # 当前年龄
        try:
            birth_year = int((parsed.birth or {}).get("公历", "1980-01-01").split("-")[0])
        except Exception:
            birth_year = 1980
        from datetime import datetime as _dt
        current_year = _dt.now().year
        current_age = current_year - birth_year
        for s in steps:
            year_range = _dayun_year_range(s)
            year_text = (
                f"{year_range[0]}-{year_range[1] - 1}"
                if year_range is not None
                else str(getattr(s, "起讫", "—"))
            )
            is_current = (s.起岁 <= current_age <= s.止岁)
            out.append({
                "seq": s.序号,
                "ganzhi": str(s.干支),
                "age_range": f"{s.起岁}-{s.止岁}",
                "year_range": year_text,
                "is_current": is_current,
                "marker": "← 当前" if is_current else "",
            })
    except Exception:
        pass
    return out


def _pillar_parts(pillar: Any) -> tuple[str, str]:
    """Return (gan, zhi) for both GanZhi-like objects and legacy string pillars."""
    gan = getattr(pillar, "gan", None)
    zhi = getattr(pillar, "zhi", None)
    if gan is not None and zhi is not None:
        return str(gan), str(zhi)

    text = str(pillar or "")
    if len(text) >= 2:
        return text[0], text[1]
    if len(text) == 1:
        return text, "—"
    return "—", "—"


def _known_facts_to_display(known_facts: Any) -> tuple[list[str], str]:
    """Build report-facing known facts text without exposing internal indexes."""
    if not known_facts:
        items = ["暂无已知反馈事实；本报告按命盘结构与可回测断语输出，后续需通过反馈校准。"]
        return items, items[0]
    out: list[str] = []
    for fact in known_facts:
        year = getattr(fact, "year", None)
        event = getattr(fact, "event", None)
        content = getattr(fact, "content", None)
        if isinstance(fact, dict):
            year = fact.get("year", year)
            event = fact.get("event", event)
            content = fact.get("content", content)
        parts = [str(x) for x in (year, event, content) if x not in (None, "")]
        if parts:
            out.append(" / ".join(parts))
    if not out:
        out = ["暂无已知反馈事实；本报告按命盘结构与可回测断语输出，后续需通过反馈校准。"]
    return out, "<br>".join(out)


def _build_section_zero_vm(
    energy: EnergyFindings,
    picture: PictureFindings,
    parsed: ParsedInput,
) -> dict:
    """F8 · §0 命局核心结构总览。"""
    b = getattr(parsed, "bazi", None) if parsed else None
    if not b:
        return {"section_zero": False}

    def _get_pillar(name: str) -> Any:
        if isinstance(b, dict):
            return b.get(name, "")
        return getattr(b, name, "")

    year_raw = _get_pillar("年柱")
    month_raw = _get_pillar("月柱")
    day_raw = _get_pillar("日柱")
    hour_raw = _get_pillar("时柱")
    year_gan, year_zhi = _pillar_parts(year_raw)
    month_gan, month_zhi = _pillar_parts(month_raw)
    day_gan, day_zhi = _pillar_parts(day_raw)
    hour_gan, hour_zhi = _pillar_parts(hour_raw)

    # 4 柱 + 干十神 + 主气 + 长生
    pillars = [
        {"name": "年", "gan": year_gan, "zhi": year_zhi},
        {"name": "月", "gan": month_gan, "zhi": month_zhi},
        {"name": "日", "gan": day_gan, "zhi": day_zhi, "is_master": True},
        {"name": "时", "gan": hour_gan, "zhi": hour_zhi},
    ]

    def _format_canggan_item(item: Any) -> str:
        if isinstance(item, dict):
            gan = item.get("干", "")
            item_type = item.get("类型", "")
        else:
            gan = getattr(item, "干", "")
            item_type = getattr(item, "类型", "")
        return f"{gan}({item_type})" if item_type else str(gan or item)

    canggan_raw = getattr(parsed, "canggan", {}) or {}
    canggan_by_branch = {}
    for key in ("年支", "月支", "日支", "时支"):
        raw_items = canggan_raw.get(key, []) if isinstance(canggan_raw, dict) else getattr(canggan_raw, key, []) or []
        canggan_by_branch[key] = [_format_canggan_item(item) for item in raw_items]
    changsheng_by_branch = getattr(parsed, "twelve_changsheng", {}) or {}
    shensha_by_pillar = getattr(parsed, "shensha", {}) or {}

    # 体用结构
    ty = energy.tiyong if energy and energy.tiyong else None
    body_str = "、".join(f"{x.char}({x.role})" for x in ty.body) if ty and ty.body else "—"
    purpose_str = "、".join(f"{x.char}({x.role})" for x in ty.purpose) if ty and ty.purpose else "—"
    # 暗引 brief
    anyin_brief = ""
    anyin_results = getattr(picture, "anyin_results", None) or []
    if anyin_results:
        items = [f"{a.formula}({a.real_meaning})" for a in anyin_results[:3]]
        anyin_brief = "、".join(items)
    # 神煞 brief（来自 parsed.shensha）
    shensha_brief = ""
    if parsed and getattr(parsed, "shensha", None):
        s = parsed.shensha or {}
        items = []
        for k in ("年柱", "月柱", "日柱", "时柱"):
            v = s.get(k) or []
            if v:
                items.append(f"{k}: {'·'.join(v[:5])}")
        shensha_brief = "  ｜  ".join(items[:4])
    return {
        "section_zero": True,
        "sz_pillars": pillars,
        "year_pillar": f"{year_gan}{year_zhi}",
        "month_pillar": f"{month_gan}{month_zhi}",
        "day_pillar": f"{day_gan}{day_zhi}",
        "hour_pillar": f"{hour_gan}{hour_zhi}",
        "year_gan": year_gan,
        "year_zhi": year_zhi,
        "month_gan": month_gan,
        "month_zhi": month_zhi,
        "day_gan": day_gan,
        "day_zhi": day_zhi,
        "hour_gan": hour_gan,
        "hour_zhi": hour_zhi,
        "sz_day_master": day_gan,
        "sz_yueling": month_zhi,
        "sz_body_str": body_str,
        "sz_purpose_str": purpose_str,
        "sz_layer_count": getattr(energy, "layer_count", 0),
        "sz_wealth_ceiling": getattr(energy, "wealth_ceiling", "—"),
        "sz_anyin_brief": anyin_brief or "—",
        "sz_shensha_brief": shensha_brief or "—",
        "canggan_by_branch": canggan_by_branch,
        "changsheng_by_branch": changsheng_by_branch,
        "shensha_by_pillar": shensha_by_pillar,
    }


def _build_15tier_vm(picture: PictureFindings) -> dict:
    """F5 · §B.6 15 层五维定位。"""
    w = getattr(picture, "wealth_15tier", None) if picture else None
    if not w:
        return {"has_15tier": False}
    domains = []
    for key, label in [
        ("xueye", "学业"), ("shiye", "事业"), ("hunyin", "婚姻"),
        ("caifu", "财富"), ("guanming", "官命"),
    ]:
        band = getattr(w, key, None)
        if band is None:
            continue
        domains.append({
            "key": key,
            "domain_label": label,
            "low": band.low,
            "mid": band.mid,
            "high": band.high,
            "label": band.label,
            "society": band.society,
            "income_cny": band.income_cny,
            "rationale": band.rationale,
        })
    return {
        "has_15tier": True,
        "tier_domains": domains,
        "tier_disclaimer": w.tier_disclaimer,
    }


def _build_v2_15tier_display_defaults(ctx: dict[str, Any]) -> dict[str, str]:
    """Build V2 report-facing 15-tier fields without exposing internal statement IDs.

    The current renderer historically exposes five-dimensional ``tier_domains`` from
    ``picture.wealth_15tier``. V2 needs six report domains. Until the full six-domain
    expert model is wired into runtime objects, provide conservative display defaults
    so the template never leaks raw placeholders; richer case-specific values may be
    supplied by future context builders and should override these defaults.
    """
    by_label = {str(d.get("domain_label", "")): d for d in ctx.get("tier_domains", []) if isinstance(d, dict)}

    def _boundary_explain(boundary: str) -> str:
        if "-" in boundary and not boundary.startswith("待"):
            low, high = boundary.split("-", 1)
            return f"下限 {low} 表示反馈不足、执行走偏或资源不接时的保守落点；上限 {high} 表示大运承接、教育/平台/规则配合良好时的可冲层次"
        return "下限与上限均待现实反馈、三派裁判和应期回测后确定"

    def _from_band(label: str, fallback_layer: str, fallback_meaning: str) -> tuple[str, str, str, str]:
        band = by_label.get(label)
        if not band:
            return fallback_layer, fallback_meaning, "待反馈校准", "命局结构、三派逐域裁判、现实反馈"
        low = band.get("low", "?")
        mid = band.get("mid", "?")
        high = band.get("high", "?")
        text_label = band.get("label", fallback_meaning)
        layer = f"L{mid}｜{text_label}"
        meaning = str(band.get("society") or fallback_meaning)
        boundary = f"L{low}-L{high}"
        evidence = str(band.get("rationale") or "命局结构、三派逐域裁判、现实反馈")
        return layer, meaning, boundary, evidence

    specs = {
        "education": _from_band("学业", "待补｜学业层级待三派裁判补齐", "升学、证照、学习稳定度待反馈校准"),
        "career": _from_band("事业", "待补｜事业层级待三派裁判补齐", "职业平台、岗位责任、专业资质待反馈校准"),
        "wealth": _from_band("财富", "待补｜财富层级待三派裁判补齐", "收入、资产沉淀、风险隔离待反馈校准"),
        "marriage": _from_band("婚姻", "待补｜婚姻层级待三派裁判补齐", "关系稳定度、边界和应期待反馈校准"),
        "health": _from_band("健康", "待补｜健康风险待三派裁判补齐", "体检、作息、压力和疾病反馈待校准"),
        "personality": _from_band("性格", "待补｜性格层级待三派裁判补齐", "行为风格、抗压和执行力待反馈校准"),
    }
    expansions = ctx.get("detail_expansions") or {}
    out: dict[str, str] = {}
    for key, (layer, meaning, boundary, evidence) in specs.items():
        expansion = expansions.get(key)
        evidence_score = float(getattr(getattr(expansion, "evidence_score", None), "value", 0.0) or 0.0)
        confidence_score = float(getattr(getattr(expansion, "confidence_score", None), "value", 0.0) or 0.0)
        inference_type = str(getattr(expansion, "inference_type", "待反馈校准") if expansion else "待反馈校准")
        uncertainty = str(getattr(expansion, "uncertainty", "需通过现实反馈校准") if expansion else "需通过现实反馈校准")
        sources = "、".join(getattr(expansion, "theory_sources", []) or ["命局结构", "生产规则"])
        detail_level = str(getattr(expansion, "level_label", "L0 粗粒度结论") if expansion else "L0 粗粒度结论")
        detail_items = "、".join(getattr(expansion, "detail_items", []) or ["L0 粗粒度结论"])
        confidence_text = (
            f"证据强度 {evidence_score:.2f}；反馈置信 {confidence_score:.2f}；"
            f"{inference_type}；{uncertainty}"
        )
        process = (
            f"细分层级：{detail_level}（{detail_items}）；理论来源：{sources}；"
            f"{inference_type}口径，不把理论共识计作案例验证"
        )
        out[f"{key}_15tier_layer"] = layer
        out[f"{key}_15tier_meaning"] = meaning
        out[f"{key}_15tier_boundary"] = boundary
        out[f"{key}_15tier_evidence"] = f"{evidence}；理论来源：{sources}"
        out[f"{key}_15tier_confidence"] = confidence_text
        out[f"{key}_15tier_timing"] = "随大运与流年反馈复盘"
        out[f"{key}_15tier_boundary_explain"] = _boundary_explain(str(boundary))
        out[f"{key}_domain_process"] = process

    outcome_defaults = {
        "education_degree_result": "学历层次待结合最高学历反馈校准",
        "education_degree_range": "小学至海外顶尖按反馈映射",
        "education_institution_result": "学校层次待结合毕业院校与录取类型校准",
        "education_institution_range": "普通、省重点、国家重点、双一流、211、985、C9、清北、海外前五十、海外前十",
        "education_performance_result": "成绩水平待结合考试成绩、排名与竞赛反馈校准",
        "education_performance_range": "差、中下、普通、中上、优秀、尖子生、竞赛级",
        "education_field_result": "专业或方向类型待结合现实专业与职业路径校准",
        "education_field_range": "人文、财经、工程、技术、医学、法律、教育、艺术、商业、公职服务或其他",
        "career_occupation_result": "职业层级待结合岗位、头衔、经营规模校准",
        "career_occupation_range": "无业、普通工人、技术员、技工、职员、基层管理、中层管理、高层管理、小创业者、中型创业者、大型创业者、本地名人、行业领袖、全国级、世界级",
        "career_organization_result": "单位层级待结合组织性质、平台规模校准",
        "career_organization_range": "小民企、中民企、上市公司、国企、央企、政府、事业单位、头部公司、世界五百强",
        "career_authority_result": "权力层级待结合正式任命、管理半径和资源调度校准",
        "career_authority_range": "无、组长、部门经理、主任、局级、厅级、省级、部级",
        "career_achievement_result": "成就层级待结合项目、业绩、奖项与行业影响校准",
        "career_achievement_range": "普通成果、稳定业绩、区域成果、行业成果、全国级成果、世界级成果",
        "wealth_income_result": "年收入待结合真实收入区间校准",
        "wealth_income_range": "五万以下、五到十万、十到二十万、二十到五十万、五十到一百万、一百万到三百万、三百万到一千万、一千万到三千万、三千万以上",
        "wealth_asset_result": "资产等级待结合净资产、房产、投资与负债校准",
        "wealth_asset_range": "负资产、零到五十万、五十到二百万、二百万到五百万、五百万到一千万、一千万到五千万、五千万到一亿、一亿到十亿、十亿以上",
        "wealth_stability_result": "财富稳定性待结合现金流、负债与收入波动校准",
        "wealth_stability_range": "不稳定、波动、稳定、稳定增长、爆发式增长、周期性",
        "marriage_relationship_result": "感情状态待结合恋爱、结婚、离异、再婚反馈校准",
        "marriage_relationship_range": "单身、多段关系、晚婚、早婚、离异、再婚、终身单身",
        "marriage_quality_result": "婚姻质量待结合满意度、冲突频率与支持度校准",
        "marriage_quality_range": "差、不稳定、普通、和谐、优秀",
        "marriage_spouse_education_result": "配偶教育层次待反馈校准",
        "marriage_spouse_career_result": "配偶事业层次待反馈校准",
        "marriage_spouse_wealth_result": "配偶财富层次待反馈校准",
        "marriage_spouse_appearance_result": "配偶外貌气质待反馈校准",
        "marriage_spouse_appearance_range": "普通、有吸引力、漂亮或英俊、出众",
        "marriage_spouse_temperament_result": "配偶性情气质待反馈校准",
        "marriage_family_result": "家庭结构待结合子女、居住、再婚与双方家庭牵连校准",
        "marriage_family_range": "核心家庭、大家庭、重组家庭、异地、同居稳定、分居、有子女、无子女或其他",
        "health_physical_result": "体质待结合体检、病史与运动水平校准",
        "health_physical_range": "弱、普通、强、运动型",
        "health_disease_result": "疾病风险待结合体检与家族史校准",
        "health_disease_range": "心血管、消化、呼吸、内分泌、肝、肾、神经、癌症、意外",
        "health_mental_result": "心理健康待结合压力、睡眠、情绪与诊疗反馈校准",
        "health_mental_range": "压力明显、普通可调节、韧性较强、稳定性强",
        "health_longevity_result": "寿元风险只表达风险等级或长寿倾向，不预测具体死亡年龄",
        "health_longevity_range": "低风险、普通、高风险、长寿倾向",
    }
    for key, value in outcome_defaults.items():
        out.setdefault(key, value)
    return out


def _vertical_cell(items: Any, *, empty: str = "—", separator: str = "<br>") -> str:
    """Render report table cells as vertical Markdown-safe text."""
    if items is None:
        return empty
    if isinstance(items, str):
        raw_items = re.split(r"[、,，/／\s]+", items)
    else:
        try:
            raw_items = list(items)
        except TypeError:
            raw_items = [items]
    cleaned = [str(item).strip() for item in raw_items if str(item).strip() and str(item).strip() not in {"—", "-", "无"}]
    return separator.join(cleaned) if cleaned else empty


def _confidence_cell(state: Any, star: Any = None, *, empty: str = "待反馈校准") -> str:
    """Render confidence as centered two-line table text, e.g. 中<br>（★★★☆☆）."""
    state_text = str(state or "").strip()
    star_text = str(star or "").strip()
    if not state_text:
        return empty
    compact = re.search(r"(?P<state>[高中低]{1,2})(?:置信)?[（(](?P<star>[★☆]{5})[）)]", state_text)
    if compact:
        return f"{compact.group('state')}<br>（{compact.group('star')}）"
    if star_text:
        short_state = state_text.replace("置信", "")
        return f"{short_state}<br>（{star_text}）"
    return state_text


def _nowrap_cell(value: Any) -> str:
    """Keep compact table cells such as time windows on one visual line."""
    return str(value or "").strip().replace(" ", "&nbsp;")


def normalize_v6_probability_band(
    raw: tuple[int, int] | tuple[float, float] | None,
    *,
    consensus_count: int = 0,
    is_primary: bool = True,
) -> str:
    """Normalize v6.2 probability bands with 55% baseline, primary range and prior boost."""
    if raw is None:
        low, high = (65, 85) if is_primary else (55, 70)
    else:
        low, high = raw
        if isinstance(low, float) and low <= 1:
            low = int(round(low * 100))
        if isinstance(high, float) and high <= 1:
            high = int(round(high * 100))
        low, high = int(low), int(high)
    low = max(low, 55)
    high = max(high, low)
    if is_primary:
        low = max(low, 65)
        high = max(high, 85)
    if consensus_count >= 5:
        low = min(100, low + 8)
        high = min(100, high + 10)
    return f"{low}%–{high}%"


def build_v6_display_context(
    ctx: dict[str, Any],
    gates: Optional[list[Any]] = None,
    parallel_analysis: Optional[Any] = None,
    support: Optional[Any] = None,
) -> dict[str, str]:
    """Build v7.7 report-facing display fields while keeping legacy pipeline inputs stable."""
    domain_defaults = {
        "education": (normalize_v6_probability_band((55, 68), is_primary=False), "中置信", "★★★☆☆"),
        "career": (normalize_v6_probability_band((65, 75), consensus_count=5), "中高置信", "★★★★☆"),
        "wealth": (normalize_v6_probability_band((65, 78)), "中置信", "★★★★☆"),
        "marriage": (normalize_v6_probability_band((65, 75)), "中置信", "★★★☆☆"),
        "health": (normalize_v6_probability_band((55, 70), is_primary=False), "中置信", "★★★☆☆"),
    }
    out: dict[str, str] = {}
    for key, (probability, confidence_state, star) in domain_defaults.items():
        out[f"{key}_probability_range"] = probability
        out[f"{key}_confidence_state"] = confidence_state
        out[f"{key}_star_display"] = star

    out.update({
        "probability_event_1_domain": "事业变化",
        "probability_event_1_window": "2025–2027",
        "probability_event_1_range": normalize_v6_probability_band((65, 78), consensus_count=5),
        "probability_event_1_confidence_state": "中高置信",
        "probability_event_1_star": "★★★★☆",
        "probability_event_1_explanation": "五派一致支持事业跃迁，已按结构先验上调，未低于百分之五十五基础线",
        "probability_event_2_domain": "财富变化",
        "probability_event_2_window": "2025–2027",
        "probability_event_2_range": normalize_v6_probability_band((65, 75)),
        "probability_event_2_confidence_state": "中置信",
        "probability_event_2_star": "★★★★☆",
        "probability_event_2_explanation": "财库与食伤生财结构成立，按主候选区间展示并保留反馈校准",
        "probability_event_3_domain": "婚姻变化",
        "probability_event_3_window": "2026–2027",
        "probability_event_3_range": normalize_v6_probability_band((65, 72)),
        "probability_event_3_confidence_state": "中置信",
        "probability_event_3_star": "★★★☆☆",
        "probability_event_3_explanation": "夫妻宫受冲合影响，按主候选概率区间展示关系压力窗口",
    })
    dayun_items = []
    for row in ctx.get("dayun_full_table", []) or []:
        if isinstance(row, dict):
            is_current = bool(row.get("marker"))
            dayun_items.append({
                "干支": f"**{row.get('ganzhi', '待引擎补全')}**" if is_current else row.get("ganzhi", "待引擎补全"),
                "年龄范围": f"**{_nowrap_cell(row.get('age_range', '待引擎补全'))}**" if is_current else _nowrap_cell(row.get("age_range", "待引擎补全")),
                "年份范围": f"**{_nowrap_cell(row.get('year_range', '待引擎补全'))}**" if is_current else _nowrap_cell(row.get("year_range", "待引擎补全")),
                "标记": f"**{row.get('marker', '')}**" if is_current else row.get("marker", ""),
            })

    shensha_by_pillar = ctx.get("shensha_by_pillar") or {}
    canggan_by_branch = ctx.get("canggan_by_branch") or {}
    changsheng_by_branch = ctx.get("changsheng_by_branch") or {}

    def _pillar_shensha(name: str) -> str:
        if isinstance(shensha_by_pillar, dict):
            return _vertical_cell(shensha_by_pillar.get(name))
        return "—"

    def _pillar_canggan(name: str) -> str:
        if isinstance(canggan_by_branch, dict):
            return _vertical_cell(canggan_by_branch.get(name))
        return "—"

    def _pillar_changsheng(name: str) -> str:
        if isinstance(changsheng_by_branch, dict):
            return _vertical_cell(changsheng_by_branch.get(name))
        return "—"

    out.update({
        "案例编号": ctx.get("case_id", "待引擎补全"),
        "命式": ctx.get("qian_kun", "待引擎补全"),
        "当前大运": ctx.get("current_luck", ctx.get("dayun_str", "待引擎补全")),
        "起运时间": ctx.get("luck_start", "待引擎补全"),
        "时间标准": "公历（YYYY–YYYY年）+ 年龄（XX–XX岁）",
        "分析状态": ctx.get("case_status", "正式分析 / 待反馈校准"),
        "报告路径": f"reports/{ctx.get('report_filename', '待引擎补全')}",
        "案例目录": f"cases/{ctx.get('case_dir', ctx.get('case_id', '待引擎补全'))}/",
        "反馈入口": f"cases/{ctx.get('case_dir', ctx.get('case_id', '待引擎补全'))}/feedback.md",
        "年干": ctx.get("year_gan", "待引擎补全"),
        "月干": ctx.get("month_gan", "待引擎补全"),
        "日干": ctx.get("day_gan", "待引擎补全"),
        "时干": ctx.get("hour_gan", "待引擎补全"),
        "年支": ctx.get("year_zhi", "待引擎补全"),
        "月支": ctx.get("month_zhi", "待引擎补全"),
        "日支": ctx.get("day_zhi", "待引擎补全"),
        "时支": ctx.get("hour_zhi", "待引擎补全"),
        "年柱十神主轴": ctx.get("year_tengod_axis", "待反馈校准"),
        "月柱十神主轴": ctx.get("month_tengod_axis", "待反馈校准"),
        "日柱十神主轴": ctx.get("day_tengod_axis", "日主"),
        "时柱十神主轴": ctx.get("hour_tengod_axis", "待反馈校准"),
        "年柱藏干": _pillar_canggan("年支"),
        "月柱藏干": _pillar_canggan("月支"),
        "日柱藏干": _pillar_canggan("日支"),
        "时柱藏干": _pillar_canggan("时支"),
        "年柱长生": _pillar_changsheng("年支"),
        "月柱长生": _pillar_changsheng("月支"),
        "日柱长生": _pillar_changsheng("日支"),
        "时柱长生": _pillar_changsheng("时支"),
        "年柱神煞": _pillar_shensha("年柱"),
        "月柱神煞": _pillar_shensha("月柱"),
        "日柱神煞": _pillar_shensha("日柱"),
        "时柱神煞": _pillar_shensha("时柱"),
        "大运列表": dayun_items,
        "大运速览": ctx.get("dayun_str", "待引擎补全"),
        "体结构资源": ctx.get("sz_body_str", "待引擎补全"),
        "用现实目标": ctx.get("sz_purpose_str", "待引擎补全"),
        "做功路径": ctx.get("tiyong_summary", "待引擎补全"),
        "人生主线": "以结构资源承接现实目标，通过做功路径进入事业、财富、婚姻、健康的可反馈校准。",
        "性格判断": ctx.get("personality_15tier_meaning", "待引擎补全"),
        "性格证据链": ctx.get("personality_15tier_evidence", "待引擎补全"),
        "性格置信度": _confidence_cell(ctx.get("personality_confidence_state", "中"), ctx.get("personality_star_display", "★★★☆☆")),
        "性格应期": ctx.get("personality_15tier_timing", "长期结构"),
        "学历层次判断": ctx.get("education_degree_result", "待引擎补全"),
        "学校层级判断": ctx.get("education_institution_result", "待引擎补全"),
        "学业表现判断": ctx.get("education_performance_result", "待引擎补全"),
        "学科倾向判断": ctx.get("education_field_result", "待引擎补全"),
        "学业证据链": ctx.get("education_15tier_evidence", ctx.get("education_domain_process", "待引擎补全")),
        "学业置信度": _confidence_cell(ctx.get("education_confidence_state", "中"), ctx.get("education_star_display", "★★★☆☆")),
        "学业应期": ctx.get("education_15tier_timing", "待反馈校准"),
        "职业层级判断": ctx.get("career_occupation_result", "待引擎补全"),
        "单位层级判断": ctx.get("career_organization_result", "待引擎补全"),
        "权力层级判断": ctx.get("career_authority_result", "待引擎补全"),
        "成就等级判断": ctx.get("career_achievement_result", "待引擎补全"),
        "事业证据链": ctx.get("career_15tier_evidence", ctx.get("career_domain_process", "待引擎补全")),
        "事业置信度": _confidence_cell(ctx.get("career_confidence_state", "中高"), ctx.get("career_star_display", "★★★★☆")),
        "事业应期": ctx.get("career_15tier_timing", "待反馈校准"),
        "收入层级判断": ctx.get("wealth_income_result", "待引擎补全"),
        "资产层级判断": ctx.get("wealth_asset_result", "待引擎补全"),
        "财富状态判断": ctx.get("wealth_stability_result", "待引擎补全"),
        "财富证据链": ctx.get("wealth_15tier_evidence", ctx.get("wealth_domain_process", "待引擎补全")),
        "财富置信度": _confidence_cell(ctx.get("wealth_confidence_state", "中"), ctx.get("wealth_star_display", "★★★★☆")),
        "财富应期": ctx.get("wealth_15tier_timing", "待反馈校准"),
        "感情状态判断": ctx.get("marriage_relationship_result", "待引擎补全"),
        "婚姻质量判断": ctx.get("marriage_quality_result", "待引擎补全"),
        "配偶学历判断": ctx.get("marriage_spouse_education_result", "待引擎补全"),
        "配偶事业判断": ctx.get("marriage_spouse_career_result", "待引擎补全"),
        "配偶财富判断": ctx.get("marriage_spouse_wealth_result", "待引擎补全"),
        "配偶外貌判断": ctx.get("marriage_spouse_appearance_result", "待引擎补全"),
        "配偶气质判断": ctx.get("marriage_spouse_temperament_result", "待引擎补全"),
        "婚姻证据链": ctx.get("marriage_15tier_evidence", ctx.get("marriage_domain_process", "待引擎补全")),
        "婚姻置信度": _confidence_cell(ctx.get("marriage_confidence_state", "中"), ctx.get("marriage_star_display", "★★★☆☆")),
        "婚姻应期": ctx.get("marriage_15tier_timing", "待反馈校准"),
        "体质判断": ctx.get("health_physical_result", "待引擎补全"),
        "疾病风险判断": ctx.get("health_disease_result", "待引擎补全"),
        "健康状态判断": ctx.get("health_mental_result", "待引擎补全"),
        "寿元倾向判断": ctx.get("health_longevity_result", "不预测具体死亡年龄，仅做风险等级与长寿倾向提示"),
        "健康证据链": ctx.get("health_15tier_evidence", ctx.get("health_domain_process", "待引擎补全")),
        "健康置信度": _confidence_cell(ctx.get("health_confidence_state", "中"), ctx.get("health_star_display", "★★★☆☆")),
        "健康应期": ctx.get("health_15tier_timing", "待反馈校准"),
        "概率事件一领域": ctx.get("probability_event_1_domain", "事业"),
        "概率事件一应事": ctx.get("probability_event_1_explanation", "待反馈校准"),
        "概率事件一窗口": _nowrap_cell(ctx.get("probability_event_1_window", "待反馈校准")),
        "概率事件一数值": ctx.get("probability_event_1_range", "待反馈校准"),
        "概率事件一置信状态": _confidence_cell(ctx.get("probability_event_1_confidence_state", "中高"), ctx.get("probability_event_1_star", "★★★★☆")),
        "概率事件一星级": ctx.get("probability_event_1_star", "待反馈校准"),
        "概率事件二领域": ctx.get("probability_event_2_domain", "财富"),
        "概率事件二应事": ctx.get("probability_event_2_explanation", "待反馈校准"),
        "概率事件二窗口": _nowrap_cell(ctx.get("probability_event_2_window", "待反馈校准")),
        "概率事件二数值": ctx.get("probability_event_2_range", "待反馈校准"),
        "概率事件二置信状态": _confidence_cell(ctx.get("probability_event_2_confidence_state", "中"), ctx.get("probability_event_2_star", "★★★★☆")),
        "概率事件二星级": ctx.get("probability_event_2_star", "待反馈校准"),
        "概率事件三领域": ctx.get("probability_event_3_domain", "婚姻"),
        "概率事件三应事": ctx.get("probability_event_3_explanation", "待反馈校准"),
        "概率事件三窗口": _nowrap_cell(ctx.get("probability_event_3_window", "待反馈校准")),
        "概率事件三数值": ctx.get("probability_event_3_range", "待反馈校准"),
        "概率事件三置信状态": _confidence_cell(ctx.get("probability_event_3_confidence_state", "中"), ctx.get("probability_event_3_star", "★★★☆☆")),
        "概率事件三星级": ctx.get("probability_event_3_star", "待反馈校准"),
        "已发生反馈一优先级": "高",
        "已发生反馈一领域": ctx.get("probability_event_1_domain", "事业"),
        "已发生反馈一窗口": _nowrap_cell(ctx.get("probability_event_1_window", "待反馈校准")),
        "已发生反馈一应事": ctx.get("probability_event_1_explanation", "待反馈校准"),
        "已发生反馈一要点": "职位、平台、职责、行业或工作模式是否明显变化",
        "已发生反馈二优先级": "中",
        "已发生反馈二领域": ctx.get("probability_event_2_domain", "财富"),
        "已发生反馈二窗口": _nowrap_cell(ctx.get("probability_event_2_window", "待反馈校准")),
        "已发生反馈二应事": ctx.get("probability_event_2_explanation", "待反馈校准"),
        "已发生反馈二要点": "收入结构、资产配置、现金流或负债是否变化",
        "已发生反馈三优先级": "中",
        "已发生反馈三领域": ctx.get("probability_event_3_domain", "婚姻"),
        "已发生反馈三窗口": _nowrap_cell(ctx.get("probability_event_3_window", "待反馈校准")),
        "已发生反馈三应事": ctx.get("probability_event_3_explanation", "待反馈校准"),
        "已发生反馈三要点": "恋爱、婚姻、分合、家庭结构或关系压力是否出现",
        "预测反馈一优先级": "高",
        "预测反馈一领域": ctx.get("probability_event_1_domain", "事业"),
        "预测反馈一窗口": _nowrap_cell(ctx.get("probability_event_1_window", "待反馈校准")),
        "预测反馈一应事": ctx.get("probability_event_1_explanation", "待反馈校准"),
        "预测反馈一要点": "职位、平台、职责、行业或工作模式是否明显变化",
        "预测反馈二优先级": "中",
        "预测反馈二领域": ctx.get("probability_event_2_domain", "财富"),
        "预测反馈二窗口": _nowrap_cell(ctx.get("probability_event_2_window", "待反馈校准")),
        "预测反馈二应事": ctx.get("probability_event_2_explanation", "待反馈校准"),
        "预测反馈二要点": "收入结构、资产配置、现金流或负债是否变化",
        "预测反馈三优先级": "中",
        "预测反馈三领域": ctx.get("probability_event_3_domain", "婚姻"),
        "预测反馈三窗口": _nowrap_cell(ctx.get("probability_event_3_window", "待反馈校准")),
        "预测反馈三应事": ctx.get("probability_event_3_explanation", "待反馈校准"),
        "预测反馈三要点": "恋爱、婚姻、分合、家庭结构或关系压力是否出现",
        "健康反馈窗口": ctx.get("health_feedback_window", "当前大运数字区间及未来三年"),
        "报告结构版本": "v7.7",
        "展示策略": "全中文字段、稳定枚举、五大模块同级结构、反馈可回写、禁止英文编码字段展示",
    })
    return out


def _build_v6_probability_display_defaults(ctx: dict[str, Any]) -> dict[str, str]:
    """Backward-compatible alias for v6 display fields."""
    return build_v6_display_context(ctx)


def _detail_policy_allows(item: dict[str, Any], expansions: dict[str, Any]) -> bool:
    """Allow low-confidence visible details only when evidence is explicitly sufficient."""
    if item.get("star", 0) >= 4:
        return True
    domain = str(item.get("domain", ""))
    for key, expansion in expansions.items():
        label = getattr(expansion, "label", "")
        if key in domain or (label and label in domain):
            return bool(getattr(expansion, "allow_theory_detail", False))
    return False


def _annotate_theory_detail(item: dict[str, Any], expansions: dict[str, Any]) -> dict[str, Any]:
    domain = str(item.get("domain", ""))
    expansion = None
    for key, candidate in expansions.items():
        label = getattr(candidate, "label", "")
        if key in domain or (label and label in domain):
            expansion = candidate
            break
    if not expansion or item.get("star", 0) >= 4:
        return item
    evidence_score = getattr(getattr(expansion, "evidence_score", None), "value", 0.0)
    confidence_score = getattr(getattr(expansion, "confidence_score", None), "value", 0.0)
    item = dict(item)
    marker = (
        f"理论推断｜证据强度 {evidence_score:.2f} / "
        f"反馈置信 {confidence_score:.2f}｜{getattr(expansion, 'uncertainty', '')}"
    )
    item["statement"] = f"{item.get('statement', '')}（{marker}）"
    return item


def _build_retrospective_vm(retrospective: Optional[Any]) -> dict:
    """F6 · §C.0 流年回溯。

    输出按大运分段；每段含 flow_years 列表（每年 1 行）+ 预渲染的 markdown 表格。
    （模板引擎不支持嵌套 {% for %}，故每段直接给 `flow_years_md` 字符串。）
    """
    if retrospective is None:
        return {"has_retrospective": False}
    segments_vm = []
    for seg in getattr(retrospective, "segments", []) or []:
        rows = []
        for f in seg.flow_years:
            rel_str = "; ".join(f.relations[:3]) if f.relations else ""
            domains_str = "/".join(f.domains[:3]) if f.domains else "—"
            # MD 表格行（| 之间用空格围绕）
            rows.append(
                f"| {f.year} | {f.liunian} | {f.age} | {f.strength} | "
                f"{f.main_energy} | {domains_str} | {rel_str} |"
            )
        flow_md = "\n".join(rows) if rows else "| — | — | — | — | — | — | — |"
        segments_vm.append({
            "seq": seg.seq,
            "ganzhi": seg.ganzhi,
            "age_range": f"{seg.age_range[0]}-{seg.age_range[1]}",
            "year_range": f"{seg.year_range[0]}-{seg.year_range[1] - 1}",
            "feature": seg.feature,
            "typical_domains_str": "/".join(seg.typical_domains[:3]) if seg.typical_domains else "—",
            "flow_years_md": flow_md,
        })
    return {
        "has_retrospective": True,
        "retro_current_age": getattr(retrospective, "current_age", 0),
        "retro_current_year": getattr(retrospective, "current_year", 0),
        "retro_current_dayun": getattr(retrospective, "current_dayun", "—"),
        "retro_segments": segments_vm,
        "retro_note": getattr(retrospective, "note", ""),
    }




def _build_energy_vm(energy: EnergyFindings) -> dict:
    """§A 能量视图。"""
    star, pct = _star_pct(energy.confidence)
    energy_mag = energy.energy_level
    energy_ordinal = getattr(energy_mag, "ordinal", "—")
    energy_score = getattr(energy_mag, "score", 0.0)

    zuogong = []
    for p in energy.zuogong_paths:
        p_star, p_pct = _star_pct(getattr(p, "confidence", None))
        # fallback：路径没有单独 confidence 时，用整体能量 confidence
        if p_star == 0:
            p_star, p_pct = star, pct
        s_mag = getattr(p, "strength", None)
        ev_list = _evidence_list(p)
        rule_id = ev_list[0]["rule_id"] if ev_list else "M1-D-001"
        rule_ids = [e["rule_id"] for e in ev_list] or [rule_id]
        sid = _compute_statement_id(energy.case_id, rule_ids)
        zuogong.append({
            "statement_id": sid,
            "rule_id": rule_id,
            "description": getattr(p, "description", ""),
            "strength_ordinal": getattr(s_mag, "ordinal", "?") if s_mag else "?",
            "layer_count": getattr(p, "layer_count", 0),
            "star": p_star,
            "pct": p_pct,
            "evidence": ev_list,
            "evidence_str": " ".join(f"{e['rule_id']}({e['school']})" for e in ev_list) or rule_id,
            "falsifiable": f"若命主最终财富层级低于{energy.wealth_ceiling}则该路径失验",
        })

    ty = energy.tiyong
    body_str = "、".join(f"{x.char}({x.role})" for x in ty.body) if ty.body else "—"
    purpose_str = "、".join(f"{x.char}({x.role})" for x in ty.purpose) if ty.purpose else "—"
    tiyong_summary = f"体：{body_str} → 用：{purpose_str}（{getattr(ty, 'rationale', '')}）"

    return {
        "layer_count": energy.layer_count,
        "wealth_ceiling": energy.wealth_ceiling,
        "energy_ordinal": energy_ordinal,
        "energy_score_pct": int(energy_score * 100),
        "energy_star": star,
        "energy_pct": pct,
        "zuogong_paths": zuogong,
        "tiyong_summary": tiyong_summary,
        "energy_hash": energy.hash(),
    }


def _build_picture_vm(picture: PictureFindings) -> dict:
    """§B 画面视图。"""
    star, pct = _star_pct(picture.confidence)

    caifu = picture.caifu
    guanming = picture.guanming
    mp = picture.marriage_picture

    wubu = []
    for step in picture.wubu_steps:
        ev_list = _evidence_list(step)
        wubu.append({
            "step": step.step,
            "name": step.name,
            "finding": step.finding,
            "evidence": ev_list,
            # v1.3 D3: 预渲染避免模板嵌套 {% for %} 在外层非贪婪正则下被拦截
            "evidence_str": " ".join(
                f"{e['rule_id']}({e['school']})" for e in ev_list
            ) or "—",
        })

    marriage_window_str = "—"
    marriage_picture_extra = ""
    marriage_age_warning = ""
    if mp:
        win = mp.get("初婚最佳窗口")
        if win and len(win) == 2:
            marriage_window_str = f"{win[0]}-{win[1]} 岁"
        # F7: age status
        age_status = mp.get("age_status") or {}
        if age_status.get("downgrade") and age_status.get("warning"):
            marriage_age_warning = age_status["warning"]
        elif age_status.get("warning"):
            # 非降级也展示提示（如"在窗口"）
            marriage_age_warning = age_status["warning"]
        # v1.3 D3: 白名单展示，避免泄漏内部 _debug / Evidence(...) 等结构化数据。
        # 仅展示稳态、可读的画像字段；其余仅在 master 内部审阅时通过 evidence
        # 列表暴露，client 报告完全屏蔽。
        _PICTURE_WHITELIST = (
            "配偶画像", "婚姻稳定度", "早婚信号", "晚婚信号",
            "二婚信号", "婚后家境", "桃花强度",
        )
        for k in _PICTURE_WHITELIST:
            if k in mp and mp[k]:
                marriage_picture_extra += f"{k}：{mp[k]}  "

    return {
        "caifu_type": caifu.type if caifu else "—",
        "caifu_rank": caifu.rank if caifu else "—",
        "guanming_type": guanming.type if guanming else "—",
        "guanming_rank": guanming.rank if guanming else "—",
        "industry_pointers_str": "、".join(picture.industry_pointers) or "—",
        "picture_star": star,
        "picture_pct": pct,
        "wubu_steps": wubu,
        "marriage_picture": bool(mp),
        "marriage_window_str": marriage_window_str,
        "marriage_picture_extra": marriage_picture_extra.strip(),
        "marriage_age_warning": marriage_age_warning,
        "picture_hash": picture.hash(),
    }



def _build_gates_vm(gates: list[GateResult], parsed: ParsedInput) -> dict:
    """§C 应期视图。"""
    birth_year = int((parsed.birth or {}).get("公历", "1980").split("-")[0])

    gate_rows = []
    iron_gates = []
    has_xiong = False
    xiong_years = []

    for g in sorted(gates, key=lambda x: (-x.passed_layers, x.year)):
        ln = liunian_ganzhi(g.year)
        liunian_str = f"{ln.gan}{ln.zhi}"
        try:
            dy_step = get_dayun_at_year(parsed.dayun, birth_year, g.year)
            dayun_str = f"{dy_step.干支}"
        except Exception:
            dayun_str = "—"

        star, pct = _star_pct(g.confidence)
        layers_icon = f"{'✓' if g.layer1 and g.layer1.passed else '✗'}L1·{'✓' if g.layer2 and g.layer2.passed else '✗'}L2·{'✓' if g.layer3 and g.layer3.passed else '✗'}L3"
        pt = g.primary_trigger
        pt_type = pt.type if pt else "—"
        pt_desc = (pt.description[:40] if pt else "")

        ev_list = _evidence_list(g)
        ev_str = " ".join(f"{e['rule_id']}({e['school']})" for e in ev_list) or "MR-LAYER3(任)"
        rule_ids = [e["rule_id"] for e in ev_list] or ["MR-LAYER3"]
        # 应期断语 statement_id 必须把 year 也纳入 hash，否则不同年份相同 evidence 会撞 ID
        sid = _compute_statement_id(
            getattr(parsed, "case_id", "") or "",
            rule_ids + [f"YEAR-{g.year}"],
        )
        row = {
            "statement_id": sid,
            "year": g.year,
            "liunian": liunian_str,
            "dayun_str": dayun_str,
            "candidate_event": g.candidate_event,
            "domain": g.domain,
            "layers_icon": layers_icon,
            "door": g.door or "—",
            "door_str": g.door or "未分类",
            "star": star,
            "pct": pct,
            "primary_trigger_type": pt_type,
            "primary_trigger_desc": pt_desc,
            "evidence": ev_list,
            "evidence_str": ev_str,
            "passed_layers": g.passed_layers,
            "is_xiong": g.is_xiong,
            "l1_icon": "✓" if g.layer1 and g.layer1.passed else "✗",
            "l2_icon": "✓" if g.layer2 and g.layer2.passed else "✗",
            "l3_icon": "✓" if g.layer3 and g.layer3.passed else "✗",
        }
        gate_rows.append(row)
        if g.passed_layers == 3:
            iron_gates.append(row)
        if g.is_xiong:
            has_xiong = True
            xiong_years.append(g.year)

    return {
        "gate_results": gate_rows,
        "iron_gates": iron_gates,
        "has_xiong_gate": has_xiong,
        "xiong_years_str": "、".join(str(y) for y in sorted(set(xiong_years))),
    }


def _build_support_vm(support: Optional[Any], case_id: str = "") -> dict:
    """§D 旁证视图（Track-D 未合入时 support=None）。

    v1.3 D1：每条 boost / health 项挂 statement_id。
    """
    if support is None:
        return {"support": False}

    star, pct = _star_pct(getattr(support, "confidence", None))
    sh = getattr(support, "shensha_supports", {}) or {}
    marriage_boosts = []
    for s in sh.get("marriage", []):
        rule = getattr(s, "name", s.get("name", "?") if isinstance(s, dict) else "?")
        boost = getattr(s, "boost", 0)
        palaces = getattr(s, "palaces", [])
        contrib = getattr(s, "contribution", "")
        rule_id = f"GP-{rule}"
        sid = _compute_statement_id(case_id, [rule_id])
        marriage_boosts.append({
            "statement_id": sid,
            "name": rule,
            "rule_id": rule_id,
            "evidence": [{"rule_id": rule_id, "school": "高", "description": contrib}],
            "palaces_str": "、".join(palaces),
            "contribution": contrib,
            "boost_pct": int(boost * 100),
        })

    cx = getattr(support, "ciguan_xuetang", None)
    edu_summary = ""
    edu_boost = 0
    if cx:
        parts = []
        if getattr(cx, "has_ciguan", False):
            parts.append("词馆")
        if getattr(cx, "has_xuetang", False):
            parts.append("学堂")
        if getattr(cx, "has_wenchang", False):
            parts.append("文昌")
        if getattr(cx, "has_taiyi", False):
            parts.append("天乙贵人")
        edu_summary = "+".join(parts) + f"：{getattr(cx, 'contribution', '')}"
        edu_boost = int(getattr(cx, "boost", 0) * 100)

    hf = getattr(support, "health_findings", []) or []
    health_rows = []
    for h in hf:
        rl = getattr(h, "risk_level", None)
        ev_list = _evidence_list(h)
        rule_ids = [e["rule_id"] for e in ev_list] or [f"GH-{getattr(h, 'organ', 'X')}"]
        sid = _compute_statement_id(case_id, rule_ids)
        health_rows.append({
            "statement_id": sid,
            "organ": getattr(h, "organ", ""),
            "risk_ordinal": getattr(rl, "ordinal", "弱") if rl else "弱",
            "rationale": getattr(h, "rationale", ""),
            "evidence": ev_list,
            # 给 health 行用，画像/应期等看 evidence 即可；这里 evidence_str 方便模板
            "evidence_str": " ".join(f"{e['rule_id']}({e['school']})" for e in ev_list) or rule_ids[0],
        })

    return {
        "support": True,
        "support_star": star,
        "support_pct": pct,
        "support_marriage_boosts": marriage_boosts,
        "support_edu": bool(cx and edu_boost > 0),
        "support_edu_summary": edu_summary,
        "support_edu_boost_pct": edu_boost,
        "support_health": health_rows,
    }



def _build_conclusions_vm(
    energy: EnergyFindings,
    picture: PictureFindings,
    gates: list[GateResult],
    final_conclusions: Optional[list] = None,
) -> dict:
    """§E 立体合并：构建共识/互补层断语视图。

    v1.3 D3：优先消费 ``final_conclusions``（来自 ``AnalysisOutput.final_conclusions``，
    其 ``layer`` 字段已由 pipeline.integrate 按 04 § 五分层）。当上游未注入
    final_conclusions 时回退到旧路径——从 evidence 中按星级粗略抽取。

    v1.3 D1：每条断语挂 statement_id（基于 case_id + 支撑 rule_ids 集合）。
    """
    case_id = energy.case_id or ""
    consensus = []
    complementary = []

    if final_conclusions:
        # 走新路径：直接使用 pipeline.integrate 已分层的 FinalConclusion
        for fc in final_conclusions:
            layer = getattr(fc, "layer", None) or (
                fc.get("layer") if isinstance(fc, dict) else None
            )
            if layer not in ("共识", "互补"):
                continue
            star, pct = _star_pct(getattr(fc, "confidence", None))
            schools = getattr(fc, "contributing_schools", None) or (
                fc.get("contributing_schools") if isinstance(fc, dict) else []
            ) or []
            statement = getattr(fc, "statement", None) or (
                fc.get("statement") if isinstance(fc, dict) else ""
            )
            ev_list = _evidence_list(fc)
            ev_str = " ".join(
                f"{e['rule_id']}({e['school']})" for e in ev_list
            ) or "—"
            rule_ids = [e["rule_id"] for e in ev_list] or [
                getattr(fc, "conclusion_id", None)
                or (fc.get("conclusion_id") if isinstance(fc, dict) else "MR-LAYER")
            ]
            sid = _compute_statement_id(case_id, rule_ids)
            falsifiable = getattr(fc, "falsifiable", None) or (
                fc.get("falsifiable") if isinstance(fc, dict) else None
            ) or f"若不符则 {rule_ids[0]} 失验"
            entry = {
                "statement_id": sid,
                "statement": statement,
                "schools_str": "/".join(f"{s}派" for s in schools) if schools else "—",
                "star": star,
                "pct": pct,
                "evidence": ev_list,
                "evidence_str": ev_str,
                "falsifiable": falsifiable,
            }
            if layer == "共识":
                consensus.append(entry)
            else:
                complementary.append(entry)
    else:
        # 回退路径：从 evidence 中按星级粗略抽取（保留向下兼容）
        for ev in energy.evidence:
            star, pct = _star_pct(getattr(ev, "confidence", None))
            if star >= 4:
                ev_str = f"{ev.rule_id}({ev.school})"
                sid = _compute_statement_id(case_id, [ev.rule_id])
                consensus.append({
                    "statement_id": sid,
                    "statement": ev.description,
                    "schools_str": f"{ev.school}派",
                    "star": star,
                    "pct": pct,
                    "evidence": [{"rule_id": ev.rule_id, "school": ev.school,
                                  "description": ev.description}],
                    "evidence_str": ev_str,
                    "falsifiable": f"若命主最终财富/层级不符则 {ev.rule_id} 失验",
                })
        for ev in picture.evidence:
            star, pct = _star_pct(getattr(ev, "confidence", None))
            if star >= 3:
                ev_str = f"{ev.rule_id}({ev.school})"
                sid = _compute_statement_id(case_id, [ev.rule_id])
                complementary.append({
                    "statement_id": sid,
                    "statement": ev.description,
                    "schools_str": f"{ev.school}派",
                    "star": star,
                    "pct": pct,
                    "evidence": [{"rule_id": ev.rule_id, "school": ev.school,
                                  "description": ev.description}],
                    "evidence_str": ev_str,
                    "falsifiable": f"若不符则 {ev.rule_id} 失验",
                })
        for g in gates:
            if g.passed_layers == 3:
                star, pct = _star_pct(g.confidence)
                ev_list = _evidence_list(g)
                ev_str = " ".join(f"{e['rule_id']}({e['school']})" for e in ev_list) or "MR-LAYER3(任)"
                rule_ids = [e["rule_id"] for e in ev_list] or ["MR-LAYER3"]
                sid = _compute_statement_id(case_id, rule_ids + [f"YEAR-{g.year}"])
                complementary.append({
                    "statement_id": sid,
                    "statement": f"{g.year} 年 {g.domain} · {g.candidate_event}（三层齐备）",
                    "schools_str": "任派",
                    "star": star,
                    "pct": pct,
                    "year": g.year,
                    "domain": g.domain,
                    "evidence": ev_list,
                    "evidence_str": ev_str,
                    "falsifiable": f"若 {g.year} 年上述事件未发生 → 失验",
                })

    return {
        "consensus_conclusions": consensus,
        "complementary_conclusions": complementary,
    }


def _build_portrait_vm(
    energy: EnergyFindings,
    picture: PictureFindings,
    gates: list[GateResult],
    parsed: ParsedInput,
) -> str:
    """§H 命主画像版骨架文字（AI 润色前的铁断骨架）。
    注意：画像版不使用 ★N (XX%) 格式，避免 output_linter 误检测。
    """
    star_e, pct_e = _star_pct(energy.confidence)
    star_p, pct_p = _star_pct(picture.confidence)

    iron = [g for g in gates if g.passed_layers == 3]
    yingqi_lines = []
    for g in sorted(iron, key=lambda x: x.year)[:5]:
        s, p = _star_pct(g.confidence)
        yingqi_lines.append(f"  · {g.year}：{g.domain} · {g.candidate_event}（{s}星/{p}%）")

    portrait = (
        "| 项目 | 内容 |\n"
        "|---|---|\n"
        f"| case_id | {parsed.case_id} |\n"
        f"| 四柱 | {_bazi_str(parsed)} |\n"
        f"| 财富天花板 | {energy.wealth_ceiling}（做功{energy.layer_count}层，{star_e}星/{pct_e}%） |\n"
        f"| 画面置信度 | {star_p}星/{pct_p}% |\n"
    )
    if yingqi_lines:
        portrait += "| 铁口应期（三层全过） | " + "<br>".join(yingqi_lines) + " |\n"
    portrait += "\n<!-- [AI-polish] 以下文字可由 AI 润色，不可改变星级/百分比数值 -->\n"
    portrait += f"\n命主整体能量{energy.wealth_ceiling}，{energy.layer_count}层做功基础，"
    portrait += f"财富路径清晰。杨派五步法与段派体用判断方向一致，"
    portrait += f"整体方向评估{star_e}星/{pct_e}%。"
    if iron:
        portrait += f"\n\n应期方面，共识最高的事件集中在 "
        portrait += "、".join(str(g.year) for g in sorted(iron, key=lambda x: x.year)[:3])
        portrait += " 年前后，三层 gate 全部通过，建议命主重点关注。"
    return portrait



def _join_trace_values(values: list[Any], *, empty: str = "source_missing") -> str:
    """把真实 trace 字段转成 Markdown 单元格展示；缺源时显式标注。"""

    cleaned = [str(value) for value in values if str(value).strip()]
    return ",".join(cleaned) if cleaned else empty



def _build_parallel_analysis_vm(parallel_analysis: Optional[Any], case_id: str) -> dict:
    """v1.5 · 多专家功能域裁判视图。"""
    if parallel_analysis is None:
        return {
            "parallel_domain_conclusions": [],
            "parallel_domain_readings": [],
            "parallel_domain_sections": [],
            "parallel_domain_consistency_notes": [],
        }

    domain_rows: list[dict[str, Any]] = []
    reading_rows: list[dict[str, Any]] = []
    domain_sections: list[dict[str, Any]] = []
    consistency_rows: list[dict[str, Any]] = []
    for note in getattr(parallel_analysis, "consistency_notes", []) or []:
        if not isinstance(note, dict):
            continue
        note_id = str(note.get("note_id", ""))
        domains = [str(x) for x in note.get("domains", [])]
        related_adjudication_ids = [str(x) for x in note.get("related_adjudication_ids", [])]
        consistency_rows.append({
            "statement_id": _compute_statement_id(case_id, [note_id or "CDC"]),
            "note_id": note_id,
            "domain": "/".join(domains) or "跨域一致性",
            "domains": domains,
            "severity": str(note.get("severity", "warning")),
            "statement": str(note.get("message", "")),
            "arbitration_note": str(note.get("arbitration_note", "")),
            "related_adjudication_ids": related_adjudication_ids,
            "source": str(note.get("source", "engine.application.cross_domain_consistency")),
        })
    for analysis in getattr(parallel_analysis, "domain_analyses", []) or []:
        consensus = getattr(analysis, "consensus", None)
        adjudication = getattr(analysis, "adjudication_result", None)
        if consensus is None or adjudication is None:
            continue
        evidence_items = getattr(consensus, "evidence_items", []) or []
        refs = [str(getattr(item, "ref", "")) for item in evidence_items if getattr(item, "ref", "")]
        statement_id = _compute_statement_id(
            case_id,
            refs or [getattr(consensus, "conclusion_id", "PDC")],
        )
        conf = getattr(consensus, "confidence", None)
        conflicts = getattr(analysis, "conflicts", []) or []
        conflict_explanations = [str(getattr(conflict, "arbitration_reason", "")) for conflict in conflicts]
        supporting_experts = list(getattr(adjudication, "winning_experts", []) or [])
        dissenting_experts = list(getattr(adjudication, "dissenting_experts", []) or [])
        abstained_experts = list(getattr(adjudication, "abstained_experts", []) or [])
        expert_systems = [str(getattr(r, "expert_system", "")) for r in getattr(analysis, "readings", []) or []]
        reading_ids = [str(getattr(r, "reading_id", "")) for r in getattr(analysis, "readings", []) or []]
        consensus_layer = getattr(consensus, "layer", "")
        feedback_state = getattr(adjudication, "feedback_state", getattr(consensus, "feedback_state", ""))
        domain_rows.append({
            "statement_id": statement_id,
            "domain": getattr(consensus, "domain", getattr(analysis, "domain", "综合")),
            "headline": getattr(consensus, "headline", ""),
            "statement": getattr(consensus, "final_statement", ""),
            "layer": consensus_layer,
            "decision": getattr(adjudication, "decision", ""),
            "support_score": getattr(adjudication, "support_score", 0.0),
            "oppose_score": getattr(adjudication, "oppose_score", 0.0),
            "star": int(getattr(conf, "star", 0) or 0),
            "pct": int(getattr(conf, "percent", 0) or 0),
            "experts_str": "/".join(getattr(consensus, "contributing_experts", []) or []) or "—",
            "dissenting_str": "/".join(getattr(consensus, "dissenting_experts", []) or []) or "—",
            "expert_systems": expert_systems,
            "expert_systems_str": _join_trace_values(expert_systems),
            "consensus_layer": consensus_layer,
            "supporting_experts": supporting_experts,
            "supporting_experts_str": _join_trace_values(supporting_experts),
            "dissenting_experts": dissenting_experts,
            "dissenting_experts_str": _join_trace_values(dissenting_experts, empty="none"),
            "abstained_experts": abstained_experts,
            "abstained_experts_str": _join_trace_values(abstained_experts, empty="none"),
            "feedback_state": feedback_state or "source_missing",
            "conflict_explanations": conflict_explanations,
            "conflict_summary": "；".join(conflict_explanations) or "无专家强冲突。",
            "evidence": [
                {
                    "rule_id": str(getattr(item, "ref", "")),
                    "school": "多专家裁判",
                    "description": str(getattr(item, "summary", "")),
                }
                for item in evidence_items
            ],
            "evidence_str": " ".join(refs) or "—",
            "falsifiable": getattr(consensus, "falsifiable", ""),
            "reading_ids": reading_ids,
            "reading_ids_str": _join_trace_values(reading_ids),
            "adjudication_id": getattr(adjudication, "adjudication_id", "") or "source_missing",
        })
        readings_by_expert: dict[str, list[dict[str, Any]]] = {
            "blind": [],
            "ziping": [],
            "tiaohou_ditiansui": [],
        }
        for reading in getattr(analysis, "readings", []) or []:
            row = _parallel_reading_row(reading, case_id)
            reading_rows.append(row)
            expert_system = str(row.get("expert_system", ""))
            if expert_system in readings_by_expert:
                readings_by_expert[expert_system].append(row)
        domain_sections.append({
            "domain": getattr(analysis, "domain", getattr(consensus, "domain", "综合")),
            "headline": getattr(consensus, "headline", ""),
            "decision": getattr(adjudication, "decision", ""),
            "layer": getattr(consensus, "layer", ""),
            "star": int(getattr(conf, "star", 0) or 0),
            "pct": int(getattr(conf, "percent", 0) or 0),
            "statement": getattr(consensus, "final_statement", ""),
            "adjudication_id": getattr(adjudication, "adjudication_id", ""),
            "expert_systems_str": "/".join(expert_systems) or "—",
            "feedback_state": getattr(adjudication, "feedback_state", getattr(consensus, "feedback_state", "")),
            "conflict_summary": "；".join(conflict_explanations) or "无专家强冲突。",
            "blind_block": _merge_parallel_expert_rows(readings_by_expert["blind"], "盲派专家组"),
            "ziping_block": _merge_parallel_expert_rows(readings_by_expert["ziping"], "子平格局派"),
            "ditiansui_block": _merge_parallel_expert_rows(readings_by_expert["tiaohou_ditiansui"], "滴天髓调候派"),
        })
    return {
        "parallel_domain_conclusions": domain_rows,
        "parallel_domain_readings": reading_rows,
        "parallel_domain_sections": domain_sections,
        "parallel_domain_consistency_notes": consistency_rows,
    }


def _parallel_reading_row(reading: Any, case_id: str) -> dict[str, Any]:
    """把单条 ExpertReading 转为报告与 statement_index 共用行。"""

    r_conf = getattr(reading, "confidence", None)
    evidence = getattr(reading, "evidence_items", []) or []
    evidence_refs = [str(getattr(item, "ref", "")) for item in evidence if getattr(item, "ref", "")]
    evidence_summaries = [str(getattr(item, "summary", "")) for item in evidence if getattr(item, "summary", "")]
    return {
        "statement_id": _compute_statement_id(
            case_id,
            evidence_refs or [str(getattr(reading, "reading_id", "PDR"))],
        ),
        "reading_id": getattr(reading, "reading_id", ""),
        "domain": getattr(reading, "domain", ""),
        "expert_system": getattr(reading, "expert_system", ""),
        "expert_name": getattr(reading, "expert_name", ""),
        "stance": getattr(reading, "stance", ""),
        "statement": getattr(reading, "claim", ""),
        "claim": getattr(reading, "claim", ""),
        "star": int(getattr(r_conf, "star", 0) or 0),
        "pct": int(getattr(r_conf, "percent", 0) or 0),
        "evidence": [
            {
                "rule_id": str(getattr(item, "ref", "")),
                "school": str(getattr(reading, "expert_name", getattr(reading, "expert_system", ""))),
                "description": str(getattr(item, "summary", "")),
            }
            for item in evidence
        ],
        "evidence_str": " ".join(evidence_refs) or "—",
        "evidence_summary": "；".join(evidence_summaries[:3]) or "—",
        "axis_refs_str": "、".join(getattr(reading, "axis_refs", []) or []) or "—",
        "scope_limit": getattr(reading, "scope_limit", "") or "—",
        "falsifiable": getattr(reading, "falsifiable", "") or "—",
        "source_engine": getattr(reading, "source_engine", "") or "—",
        "notes": getattr(reading, "notes", "") or "—",
    }


def _merge_parallel_expert_rows(rows: list[dict[str, Any]], fallback_name: str) -> str:
    """把同一功能域下同一专家体系的多条 reading 合并为模板可直接渲染的块。"""

    if not rows:
        return (
            f"**{fallback_name}**：未生成读数。\n"
            "- 立场：abstain；置信：★0/0%。\n"
            "- 取法过程与断语：该域暂无已接线生产读数。\n"
            "- 证据：—。\n"
            "- 边界：规则未接线或触发条件不足。\n"
            "- 证伪：后续接线并回测后再建立可证伪断语。"
        )
    lines: list[str] = []
    title = str(rows[0].get("expert_name") or fallback_name)
    lines.append(f"**{title}**：")
    for idx, row in enumerate(rows, start=1):
        lines.append(
            f"{idx}. 立场：{row.get('stance', '—')}；置信：★{row.get('star', 0)}/{row.get('pct', 0)}%。"
        )
        lines.append(f"   - 取法过程与断语：{row.get('claim', '—')}")
        lines.append(f"   - 证据：{row.get('evidence_str', '—')}：{row.get('evidence_summary', '—')}")
        lines.append(f"   - 分析轴：{row.get('axis_refs_str', '—')}")
        lines.append(f"   - 边界：{row.get('scope_limit', '—')}")
        lines.append(f"   - 证伪：{row.get('falsifiable', '—')}")
    return "\n".join(lines)


def _build_statement_index(ctx: dict, case_id: str) -> dict:
    """构建 C-2026-025 标准断语索引：statements 列表。

    除命主反馈所需字段外，同步写入 rule_ids / schools / section 等追溯元数据，
    让 feedback_ingest 可直接 fanout 到规则与流派统计；旧的不带 rule_ids 的 list
    schema 仍由反馈摄入侧兼容。
    """
    SECTIONS = {
        "zuogong_paths": "energy",
        "production_rule_conclusions": "production_rules",
        "consensus_conclusions": "consensus",
        "complementary_conclusions": "complementary",
        "iron_gates": "yingqi",
        "support_marriage_boosts": "support_marriage",
        "support_health": "support_health",
        "parallel_domain_conclusions": "parallel_domain_adjudication",
        "parallel_domain_readings": "parallel_domain_reading",
        "parallel_domain_consistency_notes": "parallel_domain_consistency",
    }
    statements: list[dict[str, Any]] = []
    seen: set[str] = set()
    for key, section in SECTIONS.items():
        for item in ctx.get(key, []) or []:
            sid = item.get("statement_id")
            if not sid:
                continue
            stmt = (
                item.get("statement")
                or item.get("description")
                or item.get("candidate_event")
                or item.get("name")
                or ""
            )
            if sid in seen:
                continue
            seen.add(sid)
            domain = item.get("domain") or section
            year = item.get("year")
            if year and str(year) not in str(domain):
                domain = "应期" if section == "yingqi" else domain
            ev_list = item.get("evidence") or []
            rule_ids = sorted({str(e.get("rule_id", "")).strip() for e in ev_list if isinstance(e, dict) and e.get("rule_id")})
            schools = sorted({str(e.get("school", "")).strip() for e in ev_list if isinstance(e, dict) and e.get("school")})
            if not rule_ids and item.get("rule_id"):
                rule_ids = [str(item.get("rule_id"))]
            row = {
                "statement_id": sid,
                "domain": str(domain or "综合"),
                "summary": str(stmt).strip()[:120],
                "status": "pending",
                "section": section,
                "rule_ids": rule_ids,
                "schools": schools,
            }
            if section == "parallel_domain_adjudication":
                conflict_explanations = list(item.get("conflict_explanations", [])) or [
                    str(item.get("conflict_summary", "无专家强冲突。"))
                ]
                row.update({
                    "reading_ids": list(item.get("reading_ids", [])),
                    "adjudication_id": item.get("adjudication_id", ""),
                    "expert_systems": list(item.get("expert_systems", [])),
                    "consensus_layer": item.get("consensus_layer", item.get("layer", "")),
                    "supporting_experts": list(item.get("supporting_experts", [])),
                    "dissenting_experts": list(item.get("dissenting_experts", [])),
                    "abstained_experts": list(item.get("abstained_experts", [])),
                    "conflict_explanations": conflict_explanations,
                    "feedback_state": item.get("feedback_state", ""),
                    "vote_id": item.get("adjudication_id", ""),
                    "stance": item.get("decision", ""),
                })
            elif section == "parallel_domain_reading":
                row.update({
                    "reading_id": item.get("reading_id", ""),
                    "expert_system": item.get("expert_system", ""),
                    "expert_name": item.get("expert_name", ""),
                    "stance": item.get("stance", ""),
                    "source_engine": item.get("source_engine", ""),
                    "axis_refs": [
                        x for x in str(item.get("axis_refs_str", "")).split("、") if x and x != "—"
                    ],
                })
            elif section == "parallel_domain_consistency":
                row.update({
                    "note_id": item.get("note_id", ""),
                    "domains": list(item.get("domains", [])),
                    "severity": item.get("severity", ""),
                    "arbitration_note": item.get("arbitration_note", ""),
                    "related_adjudication_ids": list(item.get("related_adjudication_ids", [])),
                    "source": item.get("source", ""),
                })
            statements.append(row)
    return {
        "case_id": case_id,
        "generated_at": date.today().isoformat(),
        "statements": statements,
    }


# ============================================================
# 二、模板填充（极简 Jinja2-like 渲染，无需额外依赖）
# ============================================================


def _read_template_cached(tpl_path: Path) -> str:
    st = tpl_path.stat()
    sig = (st.st_mtime_ns, st.st_size)
    cached = _TEMPLATE_CACHE.get(tpl_path)
    if cached is not None and cached[0] == sig:
        return cached[1]
    template = tpl_path.read_text(encoding="utf-8")
    _TEMPLATE_CACHE[tpl_path] = (sig, template)
    return template


def _normalize_report_probability_terms(text: Any) -> str:
    """Normalize linter-sensitive probability wording for report display only."""
    return (
        str(text)
        .replace("不必然", "不直接")
        .replace("必然", "一定")
        .replace("绝对", "单点")
        .replace("可能", "或会")
    )


def _normalize_report_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Return a display-only copy with probability wording normalized."""
    normalized = dict(entry)
    for key in ("statement", "evidence_str", "falsifiable"):
        if key in normalized:
            normalized[key] = _normalize_report_probability_terms(normalized[key])
    return normalized


def _render_template(template: str, ctx: dict) -> str:
    """极简模板渲染：
    - {{ key }}  → str(ctx[key])（缺失则输出“待引擎补全”）
    - {% if key %}...{% endif %}  → 按 ctx[key] truthy 控制
    - {% if not key %}...{% endif %}
    - {% for item in key %}...{% endfor %}  → 循环展开 list
    - {{ item.field }}  → 在循环体内可访问 item 的属性/字段
    """
    out = template

    # 1) {% for item in list_key %} ... {% endfor %}
    def _expand_for(m):
        item_name = m.group(1)
        list_key = m.group(2)
        body = m.group(3)
        items = ctx.get(list_key, [])
        if not isinstance(items, list):
            return ""

        item_field_re = re.compile(
            r"\{\{\s*" + re.escape(item_name) + r"\.(\w+)\s*\}\}"
        )
        nested_for_re = re.compile(
            r"\{%\s*for\s+(\w+)\s+in\s+" + re.escape(item_name) +
            r"\.(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}",
            re.DOTALL,
        )

        nested_item_field_re_cache: dict[str, re.Pattern[str]] = {}

        parts = []
        for item in items:
            b = body
            # 展开 {{ item.field }} 和嵌套 {% for ev in item.evidence %}。
            if isinstance(item, dict):
                b = item_field_re.sub(
                    lambda mm, i=item: str(i.get(mm.group(1), "")),
                    b,
                )

                def _expand_nested(mm, item=item):
                    n_item_name = mm.group(1)
                    n_field = mm.group(2)
                    n_body = mm.group(3)
                    n_list = item.get(n_field, []) if isinstance(item, dict) else []
                    n_item_field_re = nested_item_field_re_cache.get(n_item_name)
                    if n_item_field_re is None:
                        n_item_field_re = re.compile(
                            r"\{\{\s*" + re.escape(n_item_name) + r"\.(\w+)\s*\}\}"
                        )
                        nested_item_field_re_cache[n_item_name] = n_item_field_re
                    np_parts = []
                    for ni in (n_list or []):
                        nb = n_body
                        if isinstance(ni, dict):
                            nb = n_item_field_re.sub(
                                lambda mmm, ni=ni: str(ni.get(mmm.group(1), "")),
                                nb,
                            )
                        np_parts.append(nb)
                    return "".join(np_parts)
                b = nested_for_re.sub(_expand_nested, b)
            parts.append(b)
        return "".join(parts)

    out = _FOR_BLOCK_RE.sub(_expand_for, out)

    # 2)+3) {% if not key %} / {% if key %}（嵌套支持）
    # 关键：body 中加负前瞻 (?:(?!\{%\s*if\b).)*?，确保 body 不含嵌套 {% if %}，
    # 这样每次匹配的 {% endif %} 一定配对最内层；外层 while 循环逐层向外展开，
    # 直到无变化为止。修复了原非贪婪 (.*?) 在嵌套场景下外层 endif 错配为内层
    # endif，导致 client 模式泄漏反馈位的 bug。
    def _expand_if_not(m):
        key = m.group(1)
        body = m.group(2)
        val = ctx.get(key)
        return body if not val else ""
    def _expand_if(m):
        key = m.group(1)
        body = m.group(2)
        val = ctx.get(key)
        return body if val else ""
    # 防御性上限：模板嵌套深度不应超过 32 层；超过即视为模板异常并退出循环。
    for _ in range(32):
        prev = out
        out = _IF_NOT_INNER_RE.sub(_expand_if_not, out)
        out = _IF_INNER_RE.sub(_expand_if, out)
        if out == prev:
            break

    # 4) {{ key }} → 替换为 ctx[key]；正式报告不允许裸占位符泄漏。
    def _replace_var(m):
        key = m.group(1).strip()
        return str(ctx.get(key, "待引擎补全"))
    out = _VAR_RE.sub(_replace_var, out)

    return out



# ============================================================
# 三、主入口 render()
# ============================================================

def render(
    energy: EnergyFindings,
    picture: PictureFindings,
    gates: list[GateResult],
    parsed: ParsedInput,
    support: Optional[Any] = None,
    final_conclusions: Optional[list] = None,
    retrospective: Optional[Any] = None,
    parallel_analysis: Optional[Any] = None,
    template_name: Optional[str] = None,
    variant: str = "standard",
    *,
    _skip_lint: bool = False,
    _capture_ctx_to: Optional[dict] = None,
    report_schema: Literal["v5", "v6"] = "v6",
) -> str:
    """唯一标准报告渲染主入口。

    输出固定为当前命理师报告标准：产品 v1.3.0、pipeline/schema v1.4.0。
    历史 variant 与 template_name 参数仅保留兼容，不再默认产生用户/客户/命主可读报告。

    每条可回测断语仍在 ViewModel 中保留 ``statement_id``，用于生成标准
    ``statement_index.json`` 的 statements 列表。

    双护栏机制（07 § 八 + § 九）：
        生成 Markdown 后立即调用 output_linter.lint()。
        如有任何 ERROR 级别问题，抛出 RenderGuardrailError 并阻断落盘。
        仅 WARNING 级别问题通过（符合 07 § 十二 错误处理要求）。

    Args:
        energy:        D1 EnergyFindings
        picture:       D2 PictureFindings
        gates:         D3 GateResult 列表（已过滤 passed_layers >= 1）
        parsed:        ParsedInput（含 bazi / dayun / birth）
        support:       D4 SupportFindings（Optional，Track-D 未合入时传 None）
        template_name: 兼容参数；None 默认使用 templates/report-v6.md；report-v5.md 保留 alias。
        variant:       兼容参数；输出始终收敛为 standard。
        _skip_lint:    内部标志，跳过 lint（仅供测试 / render_from_output 内部协调用）
        _capture_ctx_to: 内部协调用：若传入 dict，则把构建好的 ctx 复制进去
                       （供 render_from_output 落盘 statement_index.json 使用）。

    Returns:
        str: 通过 output_linter 的完整 Markdown 报告。

    Raises:
        RenderGuardrailError: output_linter 返回 ERROR 时。
        FileNotFoundError:    模板文件不存在时。
    """
    # 唯一标准模板：当前默认作为 v6 命理师报告结构基线。
    # template_name / variant 仅保留为兼容旧调用的入参，不再默认生成用户报告。
    if template_name in (None, "", "report-v5.md"):
        template_name = "report-v6.md" if report_schema == "v6" else "report-v5.md"
    variant = "standard"
    tpl_path = ROOT / "templates" / template_name
    if not tpl_path.exists():
        raise FileNotFoundError(f"模板文件不存在: {tpl_path}")
    template = _read_template_cached(tpl_path)

    # 构建上下文
    ctx: dict[str, Any] = {}

    # 元信息
    ctx["case_id"] = getattr(parsed, "case_id", "UNKNOWN") if parsed else "UNKNOWN"
    ctx["gender"] = ((getattr(parsed, "birth", None) or {}).get("性别", "—")) if parsed else "—"
    ctx["qian_kun"] = _qian_kun_from(parsed) if parsed else "—"
    ctx["birth_date"] = _birth_str(parsed) if parsed else "—"
    ctx["bazi_str"] = _bazi_str(parsed) if (parsed and getattr(parsed, "bazi", None)) else "—"
    ctx["dayun_str"] = _dayun_str(parsed) if (parsed and getattr(parsed, "dayun", None)) else "—"
    ctx["analysis_date"] = date.today().isoformat()
    ctx["generated_date"] = ctx["analysis_date"]
    ctx["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ctx["case_status"] = "正式归档 / 待反馈校准"
    product_version_path = ROOT / "VERSION"
    ctx["product_version"] = product_version_path.read_text(encoding="utf-8").strip() if product_version_path.exists() else "unknown"
    case_id_parts = str(ctx["case_id"]).split("-", 3)
    ctx["case_dir"] = str(ctx["case_id"])
    ctx["pillars_compact"] = _bazi_str(parsed) if parsed else "—"
    ctx["report_filename"] = f"{ctx['case_id']}-content-report.md"
    ctx["solar_birth"] = ((getattr(parsed, "birth", None) or {}).get("公历", "—")) if parsed else "—"
    ctx["lunar_birth"] = ((getattr(parsed, "birth", None) or {}).get("农历", "—")) if parsed else "—"
    ctx["source_note"] = ((getattr(parsed, "birth", None) or {}).get("来源", "问真八字 APP 排盘")) if parsed else "问真八字 APP 排盘"
    if len(case_id_parts) == 4 and case_id_parts[3]:
        ctx["case_dir"] = str(ctx["case_id"])
    known_facts, known_facts_br = _known_facts_to_display(getattr(parsed, "known_facts", None) if parsed else None)
    ctx["known_facts"] = known_facts
    ctx["known_facts_br"] = known_facts_br
    # 历史 master/client/v1.2/v1.4 已作废；默认产物为命理师内容报告（统一版）。
    ctx["variant"] = variant
    ctx["is_master"] = True
    ctx["is_client"] = False
    ctx["is_v1_4"] = False

    # §A 能量
    ctx.update(_build_energy_vm(energy))

    # §B 画面
    ctx.update(_build_picture_vm(picture))

    # §C 应期
    ctx.update(_build_gates_vm(gates, parsed) if parsed else {"gate_results": [], "iron_gates": [], "has_xiong_gate": False, "xiong_years_str": ""})

    # §D 旁证
    ctx.update(_build_support_vm(support, case_id=ctx["case_id"]))

    # §E 立体合并
    ctx.update(_build_conclusions_vm(energy, picture, gates, final_conclusions))

    # §H 画像版骨架
    ctx["portrait_block"] = _build_portrait_vm(energy, picture, gates, parsed) if parsed else ""

    # F8 · §0 命局核心结构总览
    ctx.update(_build_section_zero_vm(energy, picture, parsed))

    # F5 · §B.6 15 层五维定位 + 证据强度 / 反馈置信双指标
    ctx.update(_build_15tier_vm(picture))
    detail_expansions = build_detail_expansions(
        energy=energy,
        picture=picture,
        gates=gates,
        support=support,
        final_conclusions=final_conclusions,
        known_facts=getattr(parsed, "known_facts", None) if parsed else None,
    )
    ctx["detail_expansions"] = detail_expansions
    ctx["detail_expansion_rows"] = [
        {
            "domain": expansion.domain,
            "label": expansion.label,
            "level_label": expansion.level_label,
            "evidence_score_value": f"{expansion.evidence_score.value:.2f}",
            "confidence_score_value": f"{expansion.confidence_score.value:.2f}",
            "inference_type": expansion.inference_type,
            "theory_sources": "、".join(expansion.theory_sources),
            "uncertainty": expansion.uncertainty,
        }
        for expansion in (detail_expansions[key] for key in DETAIL_DOMAINS)
    ]
    ctx.update(_build_v2_15tier_display_defaults(ctx))
    ctx.update(build_v6_display_context(ctx, gates, parallel_analysis, support))

    # F9 · 大运全表
    ctx["dayun_full_table"] = _dayun_full_table(parsed) if parsed else []

    # F6 · §C.0 流年回溯
    ctx.update(_build_retrospective_vm(retrospective))

    # v1.5 · 多专家功能域裁判
    ctx.update(_build_parallel_analysis_vm(parallel_analysis, case_id=ctx["case_id"]))

    # 命理师内容报告（统一版）：高置信主线直出；低置信但高证据项以“理论推断”透明保留。
    ctx["zuogong_paths"] = [p for p in ctx.get("zuogong_paths", []) if _detail_policy_allows(p, detail_expansions)]
    ctx["consensus_conclusions"] = [
        _normalize_report_entry(_annotate_theory_detail(c, detail_expansions))
        for c in ctx.get("consensus_conclusions", [])
        if _detail_policy_allows(c, detail_expansions)
    ]
    ctx["complementary_conclusions"] = [
        _normalize_report_entry(_annotate_theory_detail(c, detail_expansions))
        for c in ctx.get("complementary_conclusions", [])
        if _detail_policy_allows(c, detail_expansions)
    ]
    ctx["production_rule_conclusions"] = [
        c for c in ctx.get("complementary_conclusions", [])
        if any(tag in c.get("schools_str", "") for tag in ("子平", "滴天髓"))
    ]
    production_ids = {c.get("statement_id") for c in ctx["production_rule_conclusions"]}
    ctx["complementary_conclusions"] = [
        c for c in ctx.get("complementary_conclusions", [])
        if c.get("statement_id") not in production_ids
    ]
    ctx["gate_results"] = [
        _normalize_report_entry(_annotate_theory_detail(g, detail_expansions))
        for g in ctx.get("gate_results", [])
        if _detail_policy_allows(g, detail_expansions)
    ]
    ctx["iron_gates"] = [
        _normalize_report_entry(_annotate_theory_detail(g, detail_expansions))
        for g in ctx.get("iron_gates", [])
        if _detail_policy_allows(g, detail_expansions)
    ]
    ctx["support_health"] = [h for h in ctx.get("support_health", []) if h.get("risk_ordinal") in ("强", "中")]
    ctx["parallel_domain_conclusions"] = [
        c for c in ctx.get("parallel_domain_conclusions", []) if c.get("star", 0) >= 1
    ]

    # 把构建好的 ctx 暴露给调用方（供 render_from_output 落盘 statement_index.json）
    if _capture_ctx_to is not None:
        _capture_ctx_to.clear()
        _capture_ctx_to.update(ctx)

    report = _render_template(template, ctx)

    # ── 双护栏：output_linter 出口校验 ────────────────────────────
    # 07 § 八：output_linter 是兜底护栏 #2，不可绕过（_skip_lint 仅内部协调用）
    if not _skip_lint:
        from tools.output_linter import lint  # 延迟导入，避免循环
        lint_result = lint(report)
        if not lint_result.passed:
            raise RenderGuardrailError(lint_result, report)
    # ──────────────────────────────────────────────────────────────

    return report


# ============================================================
# 四、命令行入口
# ============================================================

def _smoke() -> None:
    """smoke test：用 C-2026-001 跑完整渲染流程。"""
    from tests.fixtures.cases import load_case
    from engine.energy.evaluator import evaluate_energy
    from engine.picture.matcher import match_picture
    from engine.yingqi import gate_yingqi

    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    energy = evaluate_energy(parsed)
    picture = match_picture(energy, parsed)

    # 扫描几个候选年份
    gates = []
    for year, event, domain in [
        (2005, "结婚", "婚姻"),
        (2020, "母亲去世", "六亲"),
        (2020, "升副科", "事业"),
        (2013, "结婚", "婚姻"),
    ]:
        g = gate_yingqi(year, event, domain, energy, picture, parsed)
        if g.passed_layers >= 1:
            gates.append(g)

    report = render(energy, picture, gates, parsed)
    print(report[:2000])
    print(f"\n...(共 {len(report)} 字)")

    # 简单校验：包含 v6 增强版标准结构
    assert report.startswith("# 📁 归档信息（可点击导航）")
    assert "# 📊 受限概率提示（校准增强版）" in report
    assert "# 📌 待反馈关键流年与事件（重点校准区）" in report
    assert "★" in report
    assert parsed.case_id in report

    # output_linter 校验
    from tools.output_linter import lint
    result = lint(report)
    errors = result.errors
    print(f"\noutput_linter: passed={result.passed} errors={len(errors)} warnings={len(result.warnings)}")
    for e in errors:
        print(f"  [ERROR {e.code}] {e.message}")

    print("\n[OK] render_report smoke 通过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
