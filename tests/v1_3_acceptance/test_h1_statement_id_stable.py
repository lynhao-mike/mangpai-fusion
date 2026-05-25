"""H1 · statement_id 稳定性

落地：plans/architecture-v1.3.md § 六 H1
要求：同一 input 重跑 5 次，statement_id 集合完全一致
"""
from __future__ import annotations

import pytest


pytestmark = pytest.mark.v1_3_acceptance


def _collect_sids_from_ctx(ctx: dict) -> set[str]:
    """从 render() 捕获到的 ctx 中收集所有 statement_id。"""
    sids: set[str] = set()
    for key in (
        "zuogong_paths",
        "consensus_conclusions",
        "complementary_conclusions",
        "iron_gates",
        "support_marriage_boosts",
        "support_health",
    ):
        for item in ctx.get(key, []) or []:
            sid = item.get("statement_id")
            if sid:
                sids.add(sid)
    return sids


def test_h1_statement_id_stable_across_5_runs(
    mock_energy, mock_picture, mock_gates, mock_parsed
):
    """同一 input 跑 5 次，statement_id 集合一致。"""
    from tools.render_report import render

    sid_sets: list[set[str]] = []
    for _ in range(5):
        ctx_capture: dict = {}
        try:
            render(
                energy=mock_energy,
                picture=mock_picture,
                gates=mock_gates,
                parsed=mock_parsed,
                support=None,
                template_name="report-v1.3.md",
                variant="master",
                _skip_lint=True,
                _capture_ctx_to=ctx_capture,
            )
        except Exception:
            # 模板渲染失败不影响 sid 计算（ctx 已捕获）
            pass
        sid_sets.append(_collect_sids_from_ctx(ctx_capture))

    # 5 次集合必须全等
    base = sid_sets[0]
    assert base, "至少应捕获到 1 个 statement_id"
    for i, s in enumerate(sid_sets[1:], start=2):
        assert s == base, (
            f"第 {i} 次重跑 statement_id 集合不一致：\n"
            f"  base={sorted(base)}\n"
            f"  run{i}={sorted(s)}\n"
            f"  diff_added={sorted(s - base)}\n"
            f"  diff_lost={sorted(base - s)}"
        )


def test_h1_sid_format_S_NNN_xxxxxx(
    mock_energy, mock_picture, mock_gates, mock_parsed
):
    """所有 sid 必须形如 ``S-NNN-xxxxxx``（D1 决策格式）。"""
    import re
    from tools.render_report import render

    ctx_capture: dict = {}
    try:
        render(
            energy=mock_energy,
            picture=mock_picture,
            gates=mock_gates,
            parsed=mock_parsed,
            support=None,
            template_name="report-v1.3.md",
            variant="master",
            _skip_lint=True,
            _capture_ctx_to=ctx_capture,
        )
    except Exception:
        pass

    sids = _collect_sids_from_ctx(ctx_capture)
    pattern = re.compile(r"^S-\w{1,8}-[a-f0-9]{6}$")
    for sid in sids:
        assert pattern.match(sid), f"sid 格式不符: {sid}"


def test_h1_sid_collision_free_across_cases(
    mock_picture, mock_gates
):
    """不同 case_id × 同一 rule_ids → 不同 sid（D1 强约束）。"""
    from tools.render_report import _compute_statement_id

    sids = {
        _compute_statement_id(f"C-2026-{i:03d}-X", ["M1-D-001", "M2-Y-068"])
        for i in range(20)
    }
    assert len(sids) == 20, f"20 个不同 case 应生成 20 个不同 sid，实际 {len(sids)}"


def test_h1_sid_stable_under_rule_id_reordering():
    """同一 rule_ids 集合无论排序，sid 一致（D1 决策：sorted hash）。"""
    from tools.render_report import _compute_statement_id

    sid_a = _compute_statement_id("C-2026-001-X", ["A", "B", "C"])
    sid_b = _compute_statement_id("C-2026-001-X", ["C", "A", "B"])
    sid_c = _compute_statement_id("C-2026-001-X", ["B", "C", "A", "A"])  # 含重复
    assert sid_a == sid_b == sid_c, (
        f"排序/去重应不影响 sid: {sid_a}, {sid_b}, {sid_c}"
    )


def test_h1_sid_changes_when_rule_set_changes():
    """rule_ids 集合变化（增减）→ sid 必须变。"""
    from tools.render_report import _compute_statement_id

    sid_1 = _compute_statement_id("C-2026-001-X", ["A", "B"])
    sid_2 = _compute_statement_id("C-2026-001-X", ["A", "B", "C"])
    sid_3 = _compute_statement_id("C-2026-001-X", ["A"])
    assert sid_1 != sid_2 and sid_2 != sid_3 and sid_1 != sid_3, (
        f"集合不同应有不同 sid: {sid_1}, {sid_2}, {sid_3}"
    )
