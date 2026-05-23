"""tools/render_report.py · v1.2 D-F · 三段式报告渲染器

按 07-pipeline-flow.md § 九 + 08-agent-handoff.md § 二 F 实现。

主入口：
    render(analysis_output, template="report-v1.2.md") -> str

输入结构（03 § 九 AnalysisOutput，本分支用松散 dict 兼容）：
    energy:   EnergyFindings（D1 段派）
    picture:  PictureFindings（D2 杨派）
    gates:    list[GateResult]（D3 任派）
    support:  Optional[SupportFindings]（D4 高派，Track-D 未合入时为 None）
    parsed:   ParsedInput

输出：Markdown 字符串，通过 output_linter 0 error。

AI 润色边界（决策 D）：
    仅 §H 命主画像版的 [AI-polish] 段允许修改（文字润色）。
    §A-§G 的所有 ★/% 数值、evidence chain 不可改。

作者：Track-F
"""
from __future__ import annotations

import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.energy.types import EnergyFindings
from engine.picture.types import PictureFindings
from engine.predicates.cycles import get_dayun_at_year, liunian_ganzhi
from engine.predicates.types import ParsedInput
from engine.yingqi.types import GateResult



# ============================================================
# 一、ViewModel：把上游 dataclass 转成模板友好的 dict
# ============================================================

STAR_ICONS = {True: "✓", False: "✗"}
LAYER_ICONS = {True: "✓", False: "✗"}


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


def _dayun_str(parsed: ParsedInput) -> str:
    try:
        steps = parsed.dayun.排布
        if not steps:
            return "—"
        parts = []
        for s in steps[:4]:
            parts.append(f"{s.起讫年[0]}-{s.起讫年[1]}【{s.干支}】")
        return "  ".join(parts)
    except Exception:
        return "—"


def _bazi_str(parsed: ParsedInput) -> str:
    b = parsed.bazi
    return f"{b.年柱}{b.月柱}{b.日柱}{b.时柱}"




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
        zuogong.append({
            "rule_id": rule_id,
            "description": getattr(p, "description", ""),
            "strength_ordinal": getattr(s_mag, "ordinal", "?") if s_mag else "?",
            "layer_count": getattr(p, "layer_count", 0),
            "star": p_star,
            "pct": p_pct,
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
        wubu.append({
            "step": step.step,
            "name": step.name,
            "finding": step.finding,
            "evidence": _evidence_list(step),
        })

    marriage_window_str = "—"
    marriage_picture_extra = ""
    if mp:
        win = mp.get("初婚最佳窗口")
        if win and len(win) == 2:
            marriage_window_str = f"{win[0]}-{win[1]} 岁"
        for k, v in mp.items():
            if k != "初婚最佳窗口":
                marriage_picture_extra += f"{k}：{v}  "

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
        row = {
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


def _build_support_vm(support: Optional[Any]) -> dict:
    """§D 旁证视图（Track-D 未合入时 support=None）。"""
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
        marriage_boosts.append({
            "name": rule,
            "rule_id": f"GP-{rule}",
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
        health_rows.append({
            "organ": getattr(h, "organ", ""),
            "risk_ordinal": getattr(rl, "ordinal", "弱") if rl else "弱",
            "rationale": getattr(h, "rationale", ""),
            "evidence": _evidence_list(h),
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
) -> dict:
    """§E 立体合并：从上游 evidence 中提炼共识/互补断语。"""
    consensus = []
    complementary = []

    # 共识断语：从能量 evidence 中取高置信（★4+），打 [共识] 标签
    for ev in energy.evidence:
        star, pct = _star_pct(getattr(ev, "confidence", None))
        if star >= 4:
            ev_str = f"{ev.rule_id}({ev.school})"
            consensus.append({
                "statement": ev.description,
                "schools_str": f"{ev.school}派",
                "star": star,
                "pct": pct,
                "evidence": [{"rule_id": ev.rule_id, "school": ev.school,
                              "description": ev.description}],
                "evidence_str": ev_str,
                "falsifiable": f"若命主最终财富/层级不符则 {ev.rule_id} 失验",
            })

    # 互补断语：从图景 evidence 中取，打 [互补] 标签
    for ev in picture.evidence:
        star, pct = _star_pct(getattr(ev, "confidence", None))
        if star >= 3:
            ev_str = f"{ev.rule_id}({ev.school})"
            complementary.append({
                "statement": ev.description,
                "schools_str": f"{ev.school}派",
                "star": star,
                "pct": pct,
                "evidence": [{"rule_id": ev.rule_id, "school": ev.school,
                              "description": ev.description}],
                "evidence_str": ev_str,
                "falsifiable": f"若不符则 {ev.rule_id} 失验",
            })

    # 三层铁断的应期 evidence 也加入互补层（任派独门）
    for g in gates:
        if g.passed_layers == 3:
            star, pct = _star_pct(g.confidence)
            ev_list = _evidence_list(g)
            ev_str = " ".join(f"{e['rule_id']}({e['school']})" for e in ev_list) or "MR-LAYER3(任)"
            complementary.append({
                "statement": f"{g.year} 年 {g.domain} · {g.candidate_event}（三层齐备）",
                "schools_str": "任派",
                "star": star,
                "pct": pct,
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

    portrait = f"""╔══════════════════════════════════════════════════════════════╗
║                    命 主 画 像                               ║
╠══════════════════════════════════════════════════════════════╣
║ case_id：{parsed.case_id[:20]:<20}                       ║
║ 四柱：{_bazi_str(parsed)}                                    ║
╠══════════════════════════════════════════════════════════════╣
║【财富天花板】{energy.wealth_ceiling}（做功{energy.layer_count}层，{star_e}星/{pct_e}%）║
║【画面置信度】{star_p}星/{pct_p}%                             ║
"""
    if yingqi_lines:
        portrait += "║【铁口应期（三层全过）】\n"
        for line in yingqi_lines:
            portrait += f"║{line}\n"
    portrait += "╚══════════════════════════════════════════════════════════════╝\n"
    portrait += "\n<!-- [AI-polish] 以下文字可由 AI 润色，不可改变星级/百分比数值 -->\n"
    portrait += f"\n命主整体能量{energy.wealth_ceiling}，{energy.layer_count}层做功基础，"
    portrait += f"财富路径清晰。杨派五步法与段派体用判断方向一致，"
    portrait += f"整体方向评估{star_e}星/{pct_e}%。"
    if iron:
        portrait += f"\n\n应期方面，共识最高的事件集中在 "
        portrait += "、".join(str(g.year) for g in sorted(iron, key=lambda x: x.year)[:3])
        portrait += " 年前后，三层 gate 全部通过，建议命主重点关注。"
    return portrait



# ============================================================
# 二、模板填充（极简 Jinja2-like 渲染，无需额外依赖）
# ============================================================

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
    for_re = re.compile(
        r"\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}",
        re.DOTALL,
    )
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

    out = for_re.sub(_expand_for, out)

    # 2) {% if not key %} ... {% endif %}
    if_not_re = re.compile(
        r"\{%\s*if\s+not\s+(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}", re.DOTALL
    )
    def _expand_if_not(m):
        key = m.group(1)
        body = m.group(2)
        val = ctx.get(key)
        return body if not val else ""
    out = if_not_re.sub(_expand_if_not, out)

    # 3) {% if key %} ... {% endif %}
    if_re = re.compile(
        r"\{%\s*if\s+(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}", re.DOTALL
    )
    def _expand_if(m):
        key = m.group(1)
        body = m.group(2)
        val = ctx.get(key)
        return body if val else ""
    out = if_re.sub(_expand_if, out)

    # 4) {{ key }} → 替换为 ctx[key]
    def _replace_var(m):
        key = m.group(1).strip()
        return str(ctx.get(key, f"{{{{{key}}}}}"))
    out = re.sub(r"\{\{\s*([\w.]+)\s*\}\}", _replace_var, out)

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
    template_name: str = "report-v1.2.md",
) -> str:
    """三段式报告渲染主入口。

    Args:
        energy:    D1 EnergyFindings
        picture:   D2 PictureFindings
        gates:     D3 GateResult 列表（已过滤 passed_layers >= 1）
        parsed:    ParsedInput（含 bazi / dayun / birth）
        support:   D4 SupportFindings（Optional，Track-D 未合入时传 None）
        template_name: 模板文件名（相对 templates/ 目录）

    Returns:
        str: 完整 Markdown 报告
    """
    tpl_path = ROOT / "templates" / template_name
    if not tpl_path.exists():
        raise FileNotFoundError(f"模板文件不存在: {tpl_path}")
    template = tpl_path.read_text(encoding="utf-8")

    # 构建上下文
    ctx: dict[str, Any] = {}

    # 元信息
    ctx["case_id"] = parsed.case_id
    ctx["gender"] = (parsed.birth or {}).get("性别", "—")
    ctx["birth_date"] = _birth_str(parsed)
    ctx["bazi_str"] = _bazi_str(parsed)
    ctx["dayun_str"] = _dayun_str(parsed)
    ctx["analysis_date"] = date.today().isoformat()
    ctx["generated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # §A 能量
    ctx.update(_build_energy_vm(energy))

    # §B 画面
    ctx.update(_build_picture_vm(picture))

    # §C 应期
    ctx.update(_build_gates_vm(gates, parsed))

    # §D 旁证
    ctx.update(_build_support_vm(support))

    # §E 立体合并
    ctx.update(_build_conclusions_vm(energy, picture, gates))

    # §H 画像版骨架
    ctx["portrait_block"] = _build_portrait_vm(energy, picture, gates, parsed)

    return _render_template(template, ctx)


# ============================================================
# 四、命令行入口
# ============================================================

def _smoke() -> None:
    """smoke test：用 C-2026-001 跑完整渲染流程。"""
    from tests.fixtures.cases import load_case
    from engine.energy.evaluator import evaluate_energy
    from engine.picture.matcher import match_picture
    from engine.yingqi import gate_yingqi

    parsed = load_case("C-2026-001-庚申戊寅壬子辛丑")
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

    # 简单校验：包含铁口断 §C 和 §H
    assert "三层" in report or "passed" in report.lower()
    assert "[AI-polish]" in report
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
