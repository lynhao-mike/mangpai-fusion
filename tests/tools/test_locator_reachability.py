"""tests/tools/test_locator_reachability.py —— T-110.locator 可达性校验回归测试。

背景：``tools/as_of_contract_gate.py`` 的 ``check_theory_evidence`` 原先只校验
「非空 + 非占位文本」，从不验证 ``theory_evidence[].locator`` 指向的文件是否存在、
行号是否越界。后果是删掉被冻结包引用的理论库文件后 pytest 依然全绿，审计溯源静默断掉。

这些测试锁定三条契约：

1. 可达的 locator 被确认可达（真实读取仓库内 theory/ 文件）；
2. 文件缺失 / 行号越界 / 格式非法被报为 ``reachable=False`` 且给出原因；
3. **默认只报警、不阻断**：存量失效清零前不可把旧冻结包判为不过门禁
   （``passes_gate`` 保持 True、``blocking_reasons`` 保持为空、``any_issue_found`` 为 True）。

内部实现（``_count_lines`` 的行数口径、``;`` 多目标拆分）也在本文件内锁定，以防
有人无意中把「可达」放宽成「字符串非空」。
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.as_of_contract_gate import (
    LOCATOR_REACHABILITY_BLOCKS_FREEZE,
    LocatorReachabilityFinding,
    check_locator_reachability,
    check_theory_evidence,
    run_contract_gate,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

# 真实存在于仓库内的理论库索引文件（tests/tools/test_locator_reachability.py 的上两级）。
REAL_YAML = REPO_ROOT / "theory" / "yang" / "index.yaml"
REAL_TOTAL_LINES = sum(1 for _ in REAL_YAML.open("rb"))


def _structured(locator: str | None) -> tuple[dict, ...]:
    """构造与冻结包 asof-blind-freeze.json 同构的 theory_evidence 条目。"""

    entry = {
        "school": "ziping",
        "rule_id": "ZP-PROD-TEST-001",
        "status": "active",
        "summary": "食神生财，喜身旺有根。",
        "application": "职业取向锚定。",
    }
    if locator is not None:
        entry["locator"] = locator
    return (entry,)


def _advice_kwargs(theory_evidence: tuple[object, ...]) -> dict:
    """其余冻结契约字段取无提醒取值，隔离出 locator 的影响。"""

    return dict(
        center_statement="数据分析或流程质量管理",
        center_completion_mode="COMPLETE_LATENT",
        alternative_statements=(),
        event_candidates=(("EVENT-OK", "2024-01-01", "2024-12-31", "岗位调整"),),
        theory_evidence=theory_evidence,
    )


# --------------------------------------------------------------------------
# 1. 可达 locator 被确认可达
# --------------------------------------------------------------------------


def test_reachable_locator_inside_real_yaml_is_reported_reachable() -> None:
    findings = check_locator_reachability(f"theory/yang/index.yaml:1-10")
    assert len(findings) == 1
    finding = findings[0]
    assert isinstance(finding, LocatorReachabilityFinding)
    assert finding.reachable is True
    assert finding.target == "theory/yang/index.yaml"
    assert finding.start == 1
    assert finding.end == 10
    assert "在范围内" in finding.reason


def test_reachable_locator_single_line_without_range_is_reported_reachable() -> None:
    findings = check_locator_reachability("theory/yang/index.yaml:10")
    assert len(findings) == 1
    assert findings[0].reachable is True
    assert findings[0].start == 10
    assert findings[0].end == 10


def test_boundary_locator_at_last_line_is_reachable() -> None:
    findings = check_locator_reachability(f"theory/yang/index.yaml:{REAL_TOTAL_LINES}")
    assert findings[0].reachable is True


def test_semicolon_separated_locator_returns_one_finding_per_target() -> None:
    findings = check_locator_reachability(
        "theory/yang/index.yaml:1-5; theory/yang/index.yaml:6-10"
    )
    assert len(findings) == 2
    assert all(finding.reachable is True for finding in findings)


# --------------------------------------------------------------------------
# 2. 失效 locator 被逐条报出（文件缺失 / 行号越界 / 格式非法）
# --------------------------------------------------------------------------


def test_missing_file_locator_is_reported_unreachable() -> None:
    findings = check_locator_reachability("theory/ziping/does-not-exist.yaml:1-10")
    assert len(findings) == 1
    assert findings[0].reachable is False
    assert "文件不存在" in findings[0].reason


def test_out_of_range_locator_is_reported_unreachable() -> None:
    beyond = REAL_TOTAL_LINES + 1
    findings = check_locator_reachability(f"theory/yang/index.yaml:1-{beyond}")
    assert findings[0].reachable is False
    assert "行号越界" in findings[0].reason
    assert str(REAL_TOTAL_LINES) in findings[0].reason


def test_locator_without_line_number_is_reported_unreachable() -> None:
    findings = check_locator_reachability("theory/yang/index.yaml")
    assert findings[0].reachable is False
    assert "无法解析" in findings[0].reason


def test_inverted_line_range_is_reported_unreachable() -> None:
    findings = check_locator_reachability("theory/yang/index.yaml:10-1")
    assert findings[0].reachable is False


def test_zero_line_number_is_reported_unreachable() -> None:
    findings = check_locator_reachability("theory/yang/index.yaml:0-5")
    assert findings[0].reachable is False


def test_unreachable_target_is_reported_but_does_not_raise() -> None:
    # 该断言覆盖 T-110 实测到的 3 类真实失效形态：
    #   a) 文件缺失     b) 仅路径无行号     c) 多目标串中混入无行号引用
    findings = check_locator_reachability(
        "theory/yang/index.yaml:1-10; theory/ziping/does-not-exist.yaml:1-10"
    )
    assert findings
    assert any(finding.reachable is False for finding in findings)
    # 混入的可达目标仍被单独报告为可达，不被整体判死。
    assert any(finding.reachable is True for finding in findings)


# --------------------------------------------------------------------------
# 3. 报警优先、不阻断（存量清零前的默认契约）
# --------------------------------------------------------------------------


def test_locator_failure_is_advisory_only_and_never_blocks_freeze() -> None:
    result = run_contract_gate(
        **_advice_kwargs(_structured("theory/ziping/does-not-exist.yaml:1-10"))
    )
    assert result.theory_evidence_finding.locator_findings
    assert all(
        finding.reachable is False
        for finding in result.theory_evidence_finding.locator_findings
    )
    assert result.any_issue_found is True
    assert result.locator_blocks_freeze is False
    # 关键：报警不阻断。
    assert result.passes_gate is True
    assert result.blocking_reasons == ()


def test_reachable_locator_does_not_raise_advisory_issue() -> None:
    result = run_contract_gate(**_advice_kwargs(_structured("theory/yang/index.yaml:1-10")))
    assert result.any_issue_found is False
    assert result.passes_gate is True
    assert result.locator_findings[0].reachable is True


def test_locator_failure_keeps_note_visible_for_audit() -> None:
    result = run_contract_gate(
        **_advice_kwargs(_structured("theory/ziping/does-not-exist.yaml:1-10"))
    )
    note = result.theory_evidence_finding.note
    assert "locator" in note
    assert "1/" in note


def test_plain_string_evidence_without_locator_still_passes() -> None:
    # 无 locator 的纯文本证据（含「无命中」审计记录）行为不变：不得因缺 locator 而报警。
    result = run_contract_gate(**_advice_kwargs(("已检索关键词正官/印化，无命中",)))
    assert result.any_issue_found is False
    assert result.passes_gate is True
    assert result.theory_evidence_finding.locator_findings == ()


def test_structured_entry_without_locator_key_does_not_warn() -> None:
    finding = check_theory_evidence(
        ({"school": "yang", "rule_id": "M2-Y-003", "summary": "正官用印化"},)
    )
    assert finding.blocks_freeze is False
    assert finding.evidence_count == 1
    assert finding.locator_findings == ()


def test_locator_check_default_is_advisory_mode() -> None:
    assert LOCATOR_REACHABILITY_BLOCKS_FREEZE is False


def test_placeholder_gate_is_not_disturbed_by_locator_mode() -> None:
    # 占位文本分支的 blocks_freeze 语义必须保持阻断，与 locator 配置无关。
    # 注意条目内所有文本叶子都必须是占位符才会触发占位分支（与既有口径一致）。
    finding = check_theory_evidence(({"summary": "TODO", "application": "待补充"},))
    assert finding.placeholder_only is True
    assert finding.blocks_freeze is True


def test_placeholder_entry_with_reachable_locator_still_blocks() -> None:
    # 占位分支 + 可达 locator：仍阻断（说明阻断来自占位文本，不是来自 locator）。
    finding = check_theory_evidence(
        ({"summary": "TODO", "locator": "theory/yang/index.yaml:1-1"},)
    )
    assert finding.placeholder_only is False  # 该条目只有 summary 是占位叶子
    assert finding.blocks_freeze is False
    assert finding.locator_findings[0].reachable is True


def test_missing_evidence_still_blocks_when_locator_also_broken() -> None:
    result = run_contract_gate(
        center_statement="数据分析",
        center_completion_mode="COMPLETE_LATENT",
        alternative_statements=(),
        event_candidates=(("EVENT-OK", "2024-01-01", "2024-12-31", "岗位调整"),),
    )
    assert result.passes_gate is False
    assert "缺少 theory_evidence" in result.blocking_reasons[0]


def test_locator_findings_survive_existing_documented_fields() -> None:
    # TheoryEvidenceFinding 的既有四个字段必须仍可读取且语义不变。
    finding = check_theory_evidence(_structured("theory/yang/index.yaml:1-10"))
    assert finding.evidence_count == 1
    assert finding.placeholder_only is False
    assert finding.blocks_freeze is False
    assert isinstance(finding.note, str) and finding.note


def test_check_locator_reachability_needs_no_arguments_for_repo_root() -> None:
    # 显式传入 repo_root 与缺省推导必须一致（防止根目录解析漂移）。
    explicit = check_locator_reachability("theory/yang/index.yaml:1-10", repo_root=REPO_ROOT)
    implicit = check_locator_reachability("theory/yang/index.yaml:1-10")
    assert explicit == implicit


def test_locator_targets_are_not_written_to_disk(tmp_path: Path) -> None:
    # 只读性回归：传一个不存在的仓库根，校验不得顺带创建该目录或文件。
    fake_root = tmp_path / "fake-repo"
    findings = check_locator_reachability("theory/yang/index.yaml:1-10", repo_root=fake_root)
    assert findings[0].reachable is False
    assert "文件不存在" in findings[0].reason
    assert not (fake_root / "theory").exists()
    assert list(tmp_path.iterdir()) == [] or all(
        not path.name.endswith(".yaml") for path in tmp_path.rglob("*")
    )


if __name__ == "__main__":  # pragma: no cover - 允许直接运行做冒烟
    raise SystemExit(pytest.main([__file__, "-q"]))
