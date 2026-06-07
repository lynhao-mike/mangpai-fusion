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

from engine.domain.ids import compute_statement_id
from engine.energy.types import EnergyFindings
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

    按 07-pipeline-flow.md § 三/§ 四/§ 五/§ 六 落盘约定：
        cases/C-XXX/findings/energy.json
        cases/C-XXX/findings/picture.json
        cases/C-XXX/findings/gate_results.json
        cases/C-XXX/findings/support.json
        cases/C-XXX/findings/analysis_output.json  (如 output 是 AnalysisOutput)

    Args:
        output: AnalysisOutput 或含 energy/picture/gate_results/support 字段的对象。
        cases_dir: cases/ 目录路径（默认为仓库根 cases/）。

    Returns:
        findings 目录的 Path。
    """
    cases_root = Path(cases_dir) if cases_dir else ROOT / "cases"

    # 取 case_id
    case_id: str = (
        getattr(output, "case_id", None)
        or (getattr(output, "energy", None) and getattr(output.energy, "case_id", ""))
        or "UNKNOWN"
    )

    findings_dir = cases_root / case_id / "findings"
    findings_dir.mkdir(parents=True, exist_ok=True)

    def _write(name: str, obj: Any) -> None:
        if obj is None:
            return
        if hasattr(obj, "to_json"):
            text = obj.to_json(indent=2)
        elif hasattr(obj, "to_dict"):
            text = json.dumps(obj.to_dict(), ensure_ascii=False, indent=2)
        elif isinstance(obj, list):
            text = json.dumps(
                [
                    (x.to_dict() if hasattr(x, "to_dict") else x)
                    for x in obj
                ],
                ensure_ascii=False,
                indent=2,
            )
        else:
            text = json.dumps(obj, ensure_ascii=False, indent=2)
        (findings_dir / name).write_text(text, encoding="utf-8")

    energy = getattr(output, "energy", None)
    picture = getattr(output, "picture", None)
    gates = getattr(output, "gate_results", None)
    support = getattr(output, "support", None)

    _write("energy.json", energy)
    _write("picture.json", picture)
    _write("gate_results.json", gates)
    _write("support.json", support)

    # analysis_output.json — only if the object itself has to_dict (i.e. AnalysisOutput)
    if hasattr(output, "to_dict") and energy is not None:
        _write("analysis_output.json", output)

    return findings_dir


def render_from_output(
    analysis_output: Any,
    *,
    template_name: Optional[str] = None,
    variant: str = "standard",
    lint_before: bool = True,
    cases_dir: Optional[Union[str, Path]] = None,
    skip_findings_save: bool = False,
) -> str:
    """高级渲染入口：接受 AnalysisOutput，完成全链路。

    流程（按当前默认命理师报告标准）：
        1. 将 D1-D4 JSON 落盘到 cases/C-XXX/findings/
        2. 调用 render() 生成命理师报告 Markdown
        3. 落盘 cases/C-XXX/statement_index.json（statements 列表）
        4. 调用 output_linter.lint()；如有 ERROR 则抛 RenderGuardrailError

    Args:
        analysis_output: engine.pipeline.AnalysisOutput 实例。
        template_name:   兼容参数；None 或任意历史模板名均收敛到 report-v1.3.md。
        variant:         兼容参数；历史 master/client/v1.2/v1.4 均收敛到 standard。
        lint_before:     是否启用双护栏 lint（默认 True；测试时可关闭）。
        cases_dir:       cases/ 目录路径（None = 仓库根 cases/）。

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
    )

    # Step 4: 按 C-2026-025 标准落盘 statement_index.json
    case_id = (
        getattr(analysis_output, "case_id", None)
        or getattr(getattr(analysis_output, "energy", None), "case_id", None)
        or "UNKNOWN"
    )
    try:
        cases_root = Path(cases_dir) if cases_dir else ROOT / "cases"
        idx_dir = cases_root / case_id
        idx_dir.mkdir(parents=True, exist_ok=True)
        idx = _build_statement_index(captured_ctx, case_id)
        (idx_dir / "statement_index.json").write_text(
            json.dumps(idx, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as exc:
        # statement_index 落盘失败不阻断报告交付，但必须显式暴露（否则 D5 反馈会静默降级）。
        warnings.warn(
            f"statement_index write failed for {case_id}: {exc}",
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

    year_gan, year_zhi = _pillar_parts(_get_pillar("年柱"))
    month_gan, month_zhi = _pillar_parts(_get_pillar("月柱"))
    day_gan, day_zhi = _pillar_parts(_get_pillar("日柱"))
    hour_gan, hour_zhi = _pillar_parts(_get_pillar("时柱"))

    # 4 柱 + 干十神 + 主气 + 长生
    pillars = [
        {"name": "年", "gan": year_gan, "zhi": year_zhi},
        {"name": "月", "gan": month_gan, "zhi": month_zhi},
        {"name": "日", "gan": day_gan, "zhi": day_zhi, "is_master": True},
        {"name": "时", "gan": hour_gan, "zhi": hour_zhi},
    ]
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
        "sz_day_master": day_gan,
        "sz_yueling": month_zhi,
        "sz_body_str": body_str,
        "sz_purpose_str": purpose_str,
        "sz_layer_count": getattr(energy, "layer_count", 0),
        "sz_wealth_ceiling": getattr(energy, "wealth_ceiling", "—"),
        "sz_anyin_brief": anyin_brief or "—",
        "sz_shensha_brief": shensha_brief or "—",
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



def _build_parallel_analysis_vm(parallel_analysis: Optional[Any], case_id: str) -> dict:
    """v1.5 · 多专家功能域裁判视图。"""
    if parallel_analysis is None:
        return {
            "parallel_domain_conclusions": [],
            "parallel_domain_readings": [],
            "parallel_domain_sections": [],
        }

    domain_rows: list[dict[str, Any]] = []
    reading_rows: list[dict[str, Any]] = []
    domain_sections: list[dict[str, Any]] = []
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
        domain_rows.append({
            "statement_id": statement_id,
            "domain": getattr(consensus, "domain", getattr(analysis, "domain", "综合")),
            "headline": getattr(consensus, "headline", ""),
            "statement": getattr(consensus, "final_statement", ""),
            "layer": getattr(consensus, "layer", ""),
            "decision": getattr(adjudication, "decision", ""),
            "support_score": getattr(adjudication, "support_score", 0.0),
            "oppose_score": getattr(adjudication, "oppose_score", 0.0),
            "star": int(getattr(conf, "star", 0) or 0),
            "pct": int(getattr(conf, "percent", 0) or 0),
            "experts_str": "/".join(getattr(consensus, "contributing_experts", []) or []) or "—",
            "dissenting_str": "/".join(getattr(consensus, "dissenting_experts", []) or []) or "—",
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
            "reading_ids": [str(getattr(r, "reading_id", "")) for r in getattr(analysis, "readings", []) or []],
            "adjudication_id": getattr(adjudication, "adjudication_id", ""),
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
            "blind_block": _merge_parallel_expert_rows(readings_by_expert["blind"], "盲派专家组"),
            "ziping_block": _merge_parallel_expert_rows(readings_by_expert["ziping"], "子平格局派"),
            "ditiansui_block": _merge_parallel_expert_rows(readings_by_expert["tiaohou_ditiansui"], "滴天髓调候派"),
        })
    return {
        "parallel_domain_conclusions": domain_rows,
        "parallel_domain_readings": reading_rows,
        "parallel_domain_sections": domain_sections,
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
                row.update({
                    "reading_ids": list(item.get("reading_ids", [])),
                    "adjudication_id": item.get("adjudication_id", ""),
                    "expert_systems": [
                        x for x in str(item.get("experts_str", "")).split("/") if x and x != "—"
                    ],
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


def _render_template(template: str, ctx: dict) -> str:
    """极简模板渲染：
    - {{ key }}  → str(ctx[key])（缺失则保留占位符）
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
        parts = []
        for item in items:
            b = body
            # 展开 {{ item.field }} 和 {{ item }}
            if isinstance(item, dict):
                # {{ item.field }} → item["field"]
                b = re.sub(
                    r"\{\{\s*" + re.escape(item_name) + r"\.(\w+)\s*\}\}",
                    lambda mm, i=item: str(i.get(mm.group(1), "")),
                    b,
                )
                # 嵌套 {% for ev in item.evidence %} 展开
                nested_for_re = re.compile(
                    r"\{%\s*for\s+(\w+)\s+in\s+" + re.escape(item_name) +
                    r"\.(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}",
                    re.DOTALL,
                )
                def _expand_nested(mm, item=item):
                    n_item_name = mm.group(1)
                    n_field = mm.group(2)
                    n_body = mm.group(3)
                    n_list = item.get(n_field, []) if isinstance(item, dict) else []
                    np_parts = []
                    for ni in (n_list or []):
                        nb = n_body
                        if isinstance(ni, dict):
                            nb = re.sub(
                                r"\{\{\s*" + re.escape(n_item_name) + r"\.(\w+)\s*\}\}",
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

    # 4) {{ key }} → 替换为 ctx[key]
    def _replace_var(m):
        key = m.group(1).strip()
        return str(ctx.get(key, f"{{{{{key}}}}}"))
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
        template_name: 兼容参数；输出始终使用 templates/report-v1.3.md。
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
    # 唯一标准模板：当前默认作为命理师报告结构基线。
    # template_name / variant 仅保留为兼容旧调用的入参，不再默认生成用户报告。
    template_name = "report-v1.3.md"
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
    ctx["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # 历史 master/client/v1.2/v1.4 已作废；默认产物为 analyst 内部报告。
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

    # F5 · §B.6 15 层五维定位
    ctx.update(_build_15tier_vm(picture))

    # F9 · 大运全表
    ctx["dayun_full_table"] = _dayun_full_table(parsed) if parsed else []

    # F6 · §C.0 流年回溯
    ctx.update(_build_retrospective_vm(retrospective))

    # v1.5 · 多专家功能域裁判
    ctx.update(_build_parallel_analysis_vm(parallel_analysis, case_id=ctx["case_id"]))

    # 命理师报告：保留可回测主线与低置信旁路结论，便于后续反馈校准。
    ctx["zuogong_paths"] = [p for p in ctx.get("zuogong_paths", []) if p.get("star", 0) >= 4]
    ctx["consensus_conclusions"] = [c for c in ctx.get("consensus_conclusions", []) if c.get("star", 0) >= 4]
    ctx["complementary_conclusions"] = [c for c in ctx.get("complementary_conclusions", []) if c.get("star", 0) >= 4]
    ctx["production_rule_conclusions"] = [
        c for c in ctx.get("complementary_conclusions", [])
        if any(tag in c.get("schools_str", "") for tag in ("子平", "滴天髓"))
    ]
    production_ids = {c.get("statement_id") for c in ctx["production_rule_conclusions"]}
    ctx["complementary_conclusions"] = [
        c for c in ctx.get("complementary_conclusions", [])
        if c.get("statement_id") not in production_ids
    ]
    ctx["gate_results"] = [g for g in ctx.get("gate_results", []) if g.get("star", 0) >= 4]
    ctx["iron_gates"] = [g for g in ctx.get("iron_gates", []) if g.get("star", 0) >= 4]
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

    # 简单校验：包含 C-2026-025 标准结构
    assert "## 0. 基本盘面" in report
    assert "## 归档信息" in report
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
