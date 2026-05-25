"""H6 · 完整闭环跑通

落地：plans/architecture-v1.3.md § 六 H6
要求：给 10 案 + 全反馈 → 自动产出 iteration-report-001.md

策略：
    本测试不依赖完整 engine pipeline（沙箱无 PyYAML），只验证
    "10 案完成反馈 → _bump_state 触发 → run_iteration 被调 → 报告产出"
    这条调度链端到端不崩。

    完整 engine 流水线由 H5（v1.2 G1-G6 不退化）通过 CI 单独验证。
"""
from __future__ import annotations

import json
import pathlib

import pytest


pytestmark = pytest.mark.v1_3_acceptance


def test_h6_ten_cases_trigger_iteration_report(tmp_path, monkeypatch):
    """10 案完成反馈 → iteration_seq=1 + 报告产出。"""
    import tools.feedback_ingest as fi
    import tools.iteration_report as ir
    from tools.feedback_ingest import IngestResult, IterationState

    # 1. 隔离 META 目录
    meta = tmp_path / "META"
    meta.mkdir()
    monkeypatch.setattr(fi, "META_DIR", meta)
    monkeypatch.setattr(fi, "ITERATION_STATE_FILE", meta / "iteration-state.json")

    # 2. mock run_iteration → 验证被调 + 写假报告
    invoked: dict = {}
    fake_report = meta / "iteration-report-001.md"

    class _FakeIR:
        report_path = fake_report

    def fake_run(*, seq, dry_run):
        invoked["seq"] = seq
        invoked["dry_run"] = dry_run
        # 真实场景下 run_iteration 自己写报告；这里我们 mock 一下
        fake_report.write_text(
            f"# Iteration Report #{seq:03d}\n\nmocked", encoding="utf-8"
        )
        return _FakeIR()

    monkeypatch.setattr(ir, "run_iteration", fake_run)

    # 3. 喂 10 案
    for i in range(1, 11):
        cid = f"C-H6-{i:03d}"
        result = IngestResult(case_id=cid, feedback_count=3, rule_count=2)
        fi._bump_state(result, cid)
        if i < 10:
            assert not result.iteration_triggered, f"第 {i} 案不应触发"
            assert invoked == {}, "未到 10 案前 run_iteration 不应被调"

    # 第 10 案验收
    assert result.iteration_triggered, "第 10 案应触发 iteration_seq +1"
    assert invoked["seq"] == 1, f"应触发 seq=1，实得 {invoked.get('seq')}"
    assert invoked["dry_run"] is False
    assert result.iteration_report_path == str(fake_report)
    assert fake_report.exists()
    assert "Iteration Report #001" in fake_report.read_text(encoding="utf-8")

    # 4. iteration-state.json 状态正确
    state_data = json.loads(
        (meta / "iteration-state.json").read_text(encoding="utf-8")
    )
    assert state_data["feedback_completed_count"] == 10
    assert state_data["iteration_seq"] == 1
    assert state_data["last_iteration_at_count"] == 10
    assert len(state_data["completed_case_ids"]) == 10


def test_h6_iteration_report_failure_does_not_block(tmp_path, monkeypatch):
    """iteration_report 抛错时 ingest 不阻塞 — warn-only 设计。"""
    import tools.feedback_ingest as fi
    import tools.iteration_report as ir
    from tools.feedback_ingest import IngestResult
    from tools.feedback_loop import IterationDiff

    meta = tmp_path / "META"
    meta.mkdir()
    monkeypatch.setattr(fi, "META_DIR", meta)
    monkeypatch.setattr(fi, "ITERATION_STATE_FILE", meta / "iteration-state.json")

    def boom(**kwargs):
        raise RuntimeError("boundary_miner 挂了")

    monkeypatch.setattr(ir, "run_iteration", boom)

    last_result = None
    for i in range(1, 11):
        cid = f"C-H6F-{i:03d}"
        r = IngestResult(case_id=cid, feedback_count=1, rule_count=1)
        r.iteration_diff = IterationDiff(case_id=cid, ts="", case_count=0)
        fi._bump_state(r, cid)
        last_result = r

    assert last_result is not None
    assert last_result.iteration_triggered, "第 10 案应触发"
    assert last_result.iteration_report_path is None, "调度失败 → 路径应为 None"

    notes = " ".join(last_result.iteration_diff.notes)
    assert "warn-only" in notes, f"应在 notes 标 warn-only：{last_result.iteration_diff.notes}"
    assert "boundary_miner 挂了" in notes


def test_h6_20_cases_trigger_seq_2(tmp_path, monkeypatch):
    """20 案 → 触发两次（seq=1, 2），第 11~20 案累积无误。"""
    import tools.feedback_ingest as fi
    import tools.iteration_report as ir
    from tools.feedback_ingest import IngestResult

    meta = tmp_path / "META"
    meta.mkdir()
    monkeypatch.setattr(fi, "META_DIR", meta)
    monkeypatch.setattr(fi, "ITERATION_STATE_FILE", meta / "iteration-state.json")

    triggered_at: list[tuple[int, int]] = []

    class _FakeIR:
        report_path = None

    def fake_run(*, seq, dry_run):
        return _FakeIR()

    monkeypatch.setattr(ir, "run_iteration", fake_run)

    for i in range(1, 21):
        cid = f"C-H6X-{i:03d}"
        r = IngestResult(case_id=cid, feedback_count=1, rule_count=1)
        fi._bump_state(r, cid)
        if r.iteration_triggered:
            triggered_at.append((i, r.iteration_seq))

    assert triggered_at == [(10, 1), (20, 2)], (
        f"应在第 10、20 案触发 seq=1, 2；实际 {triggered_at}"
    )


def test_h6_duplicate_case_does_not_double_count(tmp_path, monkeypatch):
    """同一案重复 ingest 不重复计数（避免误触发迭代）。"""
    import tools.feedback_ingest as fi
    from tools.feedback_ingest import IngestResult

    meta = tmp_path / "META"
    meta.mkdir()
    monkeypatch.setattr(fi, "META_DIR", meta)
    monkeypatch.setattr(fi, "ITERATION_STATE_FILE", meta / "iteration-state.json")

    cid = "C-H6-DUP"
    for _ in range(5):
        r = IngestResult(case_id=cid, feedback_count=1, rule_count=1)
        fi._bump_state(r, cid)

    # 5 次重复 ingest 同一案 → feedback_completed_count 仍为 1
    assert r.feedback_completed_count == 1
    assert not r.iteration_triggered
