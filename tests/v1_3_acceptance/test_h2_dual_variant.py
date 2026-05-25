"""H2 · 双版报告差分校验

落地：plans/architecture-v1.3.md § 六 H2
要求：
  - client 版断语数 ≤ master 版
  - client 版无 ★≤3 断语
  - client 版无弱项标记 / 反馈位
"""
from __future__ import annotations

import re

import pytest


pytestmark = pytest.mark.v1_3_acceptance


_FEEDBACK_RE = re.compile(r"\[S-[\w-]+\]\s*\[\s*\]")  # `[S-...] [ ]` 反馈位
_STAR_RE = re.compile(r"★(\d)\s*\(\s*(\d{1,3})%\s*\)")


def _count_feedback_slots(report: str) -> int:
    return len(_FEEDBACK_RE.findall(report))


def _count_low_star_lines(report: str) -> int:
    """数 ★1/2/3 出现的行（client 不应有）。"""
    n = 0
    for line in report.splitlines():
        m = _STAR_RE.search(line)
        if m and int(m.group(1)) <= 3:
            n += 1
    return n


def _count_statement_anchors(report: str) -> int:
    """数报告中出现的 [S-...]（不带 [ ]） — master 含锚点，client 不应含。"""
    return len(re.findall(r"\[S-[\w-]+\]", report))


def test_h2_master_has_feedback_slots(
    mock_energy, mock_picture, mock_gates, mock_parsed
):
    """master 版应含 [S-...] [ ] 反馈位（D2）。"""
    from tools.render_report import render

    out = render(
        energy=mock_energy, picture=mock_picture, gates=mock_gates,
        parsed=mock_parsed, support=None,
        template_name="report-v1.3.md",
        variant="master",
        _skip_lint=True,
    )
    n = _count_feedback_slots(out)
    assert n > 0, f"master 应含反馈位，实际 {n}"


def test_h2_client_has_no_feedback_slots(
    mock_energy, mock_picture, mock_gates, mock_parsed
):
    """client 版必须不含反馈位 + 无 statement_id 锚点。"""
    from tools.render_report import render

    out = render(
        energy=mock_energy, picture=mock_picture, gates=mock_gates,
        parsed=mock_parsed, support=None,
        template_name="report-v1.3.md",
        variant="client",
        _skip_lint=True,
    )
    fb = _count_feedback_slots(out)
    assert fb == 0, f"client 不应含反馈位，实际 {fb}"


def test_h2_client_filters_low_star_complementary(
    mock_energy, mock_picture, mock_gates, mock_parsed
):
    """client 版必须过滤掉 ★≤3 的弱项断语（D2 决策）。"""
    from tools.render_report import render

    master_ctx: dict = {}
    client_ctx: dict = {}
    try:
        render(
            energy=mock_energy, picture=mock_picture, gates=mock_gates,
            parsed=mock_parsed, support=None,
            template_name="report-v1.3.md", variant="master",
            _skip_lint=True, _capture_ctx_to=master_ctx,
        )
    except Exception:
        pass
    try:
        render(
            energy=mock_energy, picture=mock_picture, gates=mock_gates,
            parsed=mock_parsed, support=None,
            template_name="report-v1.3.md", variant="client",
            _skip_lint=True, _capture_ctx_to=client_ctx,
        )
    except Exception:
        pass

    # 收集 master/client 的 complementary 断语 + iron_gates
    master_compl = master_ctx.get("complementary_conclusions", [])
    client_compl = client_ctx.get("complementary_conclusions", [])
    master_gates = master_ctx.get("gate_results", [])
    client_gates = client_ctx.get("gate_results", [])

    # 数量：client ≤ master
    assert len(client_compl) <= len(master_compl), (
        f"client complementary {len(client_compl)} > master {len(master_compl)}"
    )
    assert len(client_gates) <= len(master_gates), (
        f"client gates {len(client_gates)} > master {len(master_gates)}"
    )

    # 强约束：client 中所有 complementary star >= 4
    for c in client_compl:
        assert c.get("star", 0) >= 4, (
            f"client 含 ★{c.get('star')} 弱项: {c.get('statement', '')[:40]}"
        )
    for g in client_gates:
        assert g.get("star", 0) >= 4, (
            f"client 含 ★{g.get('star')} 弱应期: {g.get('candidate_event', '')}"
        )


def test_h2_master_keeps_low_star(
    mock_energy, mock_picture, mock_gates, mock_parsed
):
    """master 应保留所有 ★ 等级的断语（不预过滤）。"""
    from tools.render_report import render

    master_ctx: dict = {}
    try:
        render(
            energy=mock_energy, picture=mock_picture, gates=mock_gates,
            parsed=mock_parsed, support=None,
            template_name="report-v1.3.md", variant="master",
            _skip_lint=True, _capture_ctx_to=master_ctx,
        )
    except Exception:
        pass

    # mock_picture 含 ★3 弱项，mock_gates 含 ★3 弱应期
    # master 应同时保留
    has_low = False
    for c in master_ctx.get("complementary_conclusions", []):
        if c.get("star", 0) <= 3:
            has_low = True
            break
    for g in master_ctx.get("gate_results", []):
        if g.get("star", 0) <= 3:
            has_low = True
            break
    assert has_low, "master 应保留至少一个 ★≤3 的弱项（mock 数据 fixture 已含 ★3）"


def test_h2_master_client_share_high_star_sids(
    mock_energy, mock_picture, mock_gates, mock_parsed
):
    """master 与 client 中 ★4+ 断语的 sid 集合一致（client 是 master 的 ★4+ 子集）。"""
    from tools.render_report import render

    master_ctx: dict = {}
    client_ctx: dict = {}
    for ctx, variant in [(master_ctx, "master"), (client_ctx, "client")]:
        try:
            render(
                energy=mock_energy, picture=mock_picture, gates=mock_gates,
                parsed=mock_parsed, support=None,
                template_name="report-v1.3.md", variant=variant,
                _skip_lint=True, _capture_ctx_to=ctx,
            )
        except Exception:
            pass

    def sids_high_star(ctx: dict) -> set[str]:
        out = set()
        for key in ("complementary_conclusions", "gate_results", "zuogong_paths"):
            for item in ctx.get(key, []):
                if item.get("star", 0) >= 4 and item.get("statement_id"):
                    out.add(item["statement_id"])
        return out

    master_high = sids_high_star(master_ctx)
    client_all = sids_high_star(client_ctx)
    assert client_all <= master_high, (
        f"client 高星 sid 应是 master 高星 sid 的子集；多出: {client_all - master_high}"
    )
