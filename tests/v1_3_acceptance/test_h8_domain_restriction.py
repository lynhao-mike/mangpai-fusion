"""H8 · domain_restriction 域感知分账

落地：plans/architecture-v1.4.md § 六 H8（v1.4 W1 决策 V2）
契约：engine/contracts/05-rule-lifecycle.md § 6.1 V2 跳过策略

要求：
    1. domain_restriction 非空 + 当前 domain ∉ list → 写入 role=misapplied，
       但不污染顶层 hits/misses/recent_5 与生命周期状态
    2. domain ∈ domain_restriction → 正常计 hit/miss，并同步写入 domain/role 分账
    3. domain 为空（无法判定）→ 不强制（仍计分），由上层决断力合并兜底
    4. 默认 domain_restriction=[] → 所有域都计分（向后兼容）
    5. freeze_auto_demotion=True → 继续记录样本，但冻结自动降级与漂移降级
"""
from __future__ import annotations

import pytest


pytestmark = [pytest.mark.v1_3_acceptance, pytest.mark.v1_4_acceptance]


def _make_fake_rule(rid, *, domain_restriction=None,
                    hits=0, misses=0, status="confirmed"):
    from tools.rule_lifecycle import Rule
    return Rule(
        id=rid, school="任", topic="lifa", status=status,
        hits=hits, misses=misses,
        domain_restriction=list(domain_restriction or []),
    )


@pytest.fixture
def patched_loader(monkeypatch):
    from tools.rule_lifecycle import RuleNotFoundError
    store: dict = {}

    def fake_load(rid):
        if rid not in store:
            raise RuleNotFoundError(rid)
        return store[rid]

    monkeypatch.setattr("tools.feedback_loop.load_rule", fake_load)
    monkeypatch.setattr("tools.feedback_loop.save_rule", lambda r: store.update({r.id: r}))
    return store


def test_h8_domain_mismatch_goes_to_misapplied_bucket(patched_loader):
    """V2 主断言：应期规则在婚姻域 ingest → 只记 misapplied 分账，不污染顶层。"""
    from tools.feedback_loop import _apply_rule_verdicts, VerdictContext
    from tools.rule_lifecycle import LifecycleConfig

    fake = _make_fake_rule("M3-R-031-FAKE", domain_restriction=["应期"],
                            hits=5, misses=3)
    patched_loader["M3-R-031-FAKE"] = fake

    diff = _apply_rule_verdicts(
        "C-H8-A",
        {"M3-R-031-FAKE": ("miss", VerdictContext(section="婚姻段", domain="婚姻"))},
        cfg=LifecycleConfig(), today="2026-05-26", dry_run=True,
    )
    assert len(diff.rule_updates) == 1
    u = diff.rule_updates[0]
    assert u.hits_before == 5 and u.hits_after == 5
    assert u.misses_before == 3 and u.misses_after == 3
    assert "role=misapplied" in u.note
    assert any("[domain-role] 错域记录" in n for n in diff.notes), \
        f"notes 未含错域记录标记：{diff.notes}"
    assert fake.hits == 5
    assert fake.misses == 3
    bucket = fake.domain_role_stats["婚姻"]["misapplied"]
    assert bucket.hits == 0
    assert bucket.misses == 1
    assert bucket.n == 1


def test_h8_domain_match_counts_hit(patched_loader):
    """domain ∈ domain_restriction → 正常计 hit。"""
    from tools.feedback_loop import _apply_rule_verdicts, VerdictContext
    from tools.rule_lifecycle import LifecycleConfig

    fake = _make_fake_rule("M3-R-031-FAKE2", domain_restriction=["应期"],
                            hits=5, misses=3)
    patched_loader["M3-R-031-FAKE2"] = fake

    diff = _apply_rule_verdicts(
        "C-H8-B",
        {"M3-R-031-FAKE2": ("hit", VerdictContext(section="应期段", domain="应期"))},
        cfg=LifecycleConfig(), today="2026-05-26", dry_run=True,
    )
    assert len(diff.rule_updates) == 1
    u = diff.rule_updates[0]
    assert u.verdict == "hit"
    assert u.hits_after == 6
    assert u.misses_after == 3


def test_h8_domain_empty_does_not_force(patched_loader):
    """domain 为空字符串 → 不强制（仍计分），由上层兜底。"""
    from tools.feedback_loop import _apply_rule_verdicts, VerdictContext
    from tools.rule_lifecycle import LifecycleConfig

    fake = _make_fake_rule("M3-R-031-FAKE3", domain_restriction=["应期"],
                            hits=5, misses=3)
    patched_loader["M3-R-031-FAKE3"] = fake

    diff = _apply_rule_verdicts(
        "C-H8-C",
        {"M3-R-031-FAKE3": ("hit", VerdictContext(section="", domain=""))},
        cfg=LifecycleConfig(), today="2026-05-26", dry_run=True,
    )
    # domain 为空时不应被 V2 跳过
    assert len(diff.rule_updates) == 1, \
        f"空 domain 应走兜底计分，但被跳过了：{diff.notes}"


def test_h8_default_empty_restriction_allows_all_domains(patched_loader):
    """默认 domain_restriction=[] → 所有域都计分（向后兼容）。"""
    from tools.feedback_loop import _apply_rule_verdicts, VerdictContext
    from tools.rule_lifecycle import LifecycleConfig

    fake = _make_fake_rule("UNRESTRICTED", domain_restriction=[])
    patched_loader["UNRESTRICTED"] = fake

    for domain in ("婚姻", "财运", "学业", "健康"):
        diff = _apply_rule_verdicts(
            f"C-H8-D-{domain}",
            {"UNRESTRICTED": ("hit", VerdictContext(domain=domain))},
            cfg=LifecycleConfig(), today="2026-05-26", dry_run=True,
        )
        assert len(diff.rule_updates) == 1, \
            f"无 restriction 在 {domain} 域应正常计分"


def test_h8_multi_domain_restriction(patched_loader):
    """domain_restriction=[应期, 财运] → 列表内任一匹配即计分。"""
    from tools.feedback_loop import _apply_rule_verdicts, VerdictContext
    from tools.rule_lifecycle import LifecycleConfig

    fake = _make_fake_rule("MULTI-DOMAIN", domain_restriction=["应期", "财运"])
    patched_loader["MULTI-DOMAIN"] = fake

    # 应期 → 计分
    diff = _apply_rule_verdicts(
        "C-H8-E", {"MULTI-DOMAIN": ("hit", VerdictContext(domain="应期"))},
        cfg=LifecycleConfig(), today="2026-05-26", dry_run=True,
    )
    assert len(diff.rule_updates) == 1

    # 财运 → 计分
    diff = _apply_rule_verdicts(
        "C-H8-F", {"MULTI-DOMAIN": ("miss", VerdictContext(domain="财运"))},
        cfg=LifecycleConfig(), today="2026-05-26", dry_run=True,
    )
    assert len(diff.rule_updates) == 1

    # 婚姻 → 错域分账，不污染顶层
    top_hits_before = fake.hits
    top_misses_before = fake.misses
    diff = _apply_rule_verdicts(
        "C-H8-G", {"MULTI-DOMAIN": ("hit", VerdictContext(domain="婚姻"))},
        cfg=LifecycleConfig(), today="2026-05-26", dry_run=True,
    )
    assert len(diff.rule_updates) == 1
    assert fake.hits == top_hits_before
    assert fake.misses == top_misses_before
    assert fake.domain_role_stats["婚姻"]["misapplied"].hits == 1
    assert any("[domain-role] 错域记录" in n for n in diff.notes)


def test_h8_v1_takes_precedence_over_v2(patched_loader):
    """同时设 quantifiable=False + domain_restriction → V1 先生效（更早跳过）。"""
    from tools.rule_lifecycle import Rule, LifecycleConfig
    from tools.feedback_loop import _apply_rule_verdicts, VerdictContext

    fake = Rule(id="BOTH-FLAGS", school="任", topic="lifa",
                status="confirmed", hits=2, misses=2,
                quantifiable=False,
                domain_restriction=["应期"])
    patched_loader["BOTH-FLAGS"] = fake

    diff = _apply_rule_verdicts(
        "C-H8-H",
        # domain="应期" 本应通过 V2，但 V1 先生效
        {"BOTH-FLAGS": ("hit", VerdictContext(domain="应期"))},
        cfg=LifecycleConfig(), today="2026-05-26", dry_run=True,
    )
    assert diff.rule_updates == []
    # notes 应该带 V1 标记（V1 先 continue），不是 V2
    v1_notes = [n for n in diff.notes if "[v1.4-V1]" in n]
    v2_notes = [n for n in diff.notes if "[v1.4-V2]" in n]
    assert v1_notes and not v2_notes, \
        f"V1 应先于 V2 生效。V1={v1_notes}, V2={v2_notes}"


def test_h8_freeze_auto_demotion_records_without_status_downshift(patched_loader):
    """freeze_auto_demotion=True：顶层样本仍记录，但自动降级被冻结。"""
    from tools.feedback_loop import _apply_rule_verdicts, VerdictContext
    from tools.rule_lifecycle import LifecycleConfig

    fake = _make_fake_rule("FREEZE-DEMOTE", domain_restriction=["应期"],
                            hits=10, misses=2, status="confirmed")
    fake.misses_at_confirmed = 0
    patched_loader["FREEZE-DEMOTE"] = fake

    diff = _apply_rule_verdicts(
        "C-H8-I",
        {"FREEZE-DEMOTE": ("miss", VerdictContext(section="应期段", domain="应期", role="trigger"))},
        cfg=LifecycleConfig(confirmed_demote_misses=3, freeze_auto_demotion=True),
        today="2026-05-26",
        dry_run=True,
    )

    assert len(diff.rule_updates) == 1
    assert fake.misses == 3
    assert fake.status == "confirmed"
    assert diff.status_changes == []
    assert fake.domain_role_stats["应期"]["trigger"].misses == 1
    assert any("freeze_auto_demotion=true" in n for n in diff.notes)
