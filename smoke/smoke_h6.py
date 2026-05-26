#!/usr/bin/env python3
"""H6 · 完整闭环 stdlib smoke（无 pytest/PyYAML）

模拟 10 案 → _bump_state → iteration_report 触发链
"""
import sys, types, json, pathlib, tempfile, os

# ── 桩 yaml ───────────────────────────────────────────────
fake_yaml = types.ModuleType("yaml")
fake_yaml.safe_load = lambda s: {}
fake_yaml.safe_dump = lambda d, **kw: ""
fake_yaml.load = lambda s, Loader=None: {}
fake_yaml.YAMLError = Exception
class _Loader: pass
fake_yaml.SafeLoader = _Loader
sys.modules["yaml"] = fake_yaml

sys.path.insert(0, "/projects/sandbox/mangpai-fusion")

PASS = []
FAIL = []

def check(name, cond, msg=""):
    if cond:
        PASS.append(name)
        print(f"  PASS  {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL  {name}  {msg}")

print("=== H6 完整闭环 ===")

import tools.feedback_ingest as fi
import tools.iteration_report as ir
from tools.feedback_ingest import IngestResult, IterationState
from tools.feedback_loop import IterationDiff

# ── T1: 10 案触发 iteration_report ─────────────────────
with tempfile.TemporaryDirectory() as td:
    meta = pathlib.Path(td) / "META"
    meta.mkdir()

    # 打补丁隔离
    orig_meta = fi.META_DIR
    orig_state = fi.ITERATION_STATE_FILE
    fi.META_DIR = meta
    fi.ITERATION_STATE_FILE = meta / "iteration-state.json"

    invoked = {}
    fake_report = meta / "iteration-report-001.md"

    class _FakeIR:
        report_path = fake_report

    def fake_run(*, seq, dry_run):
        invoked["seq"] = seq
        invoked["dry_run"] = dry_run
        fake_report.write_text(f"# Iteration Report #{seq:03d}\n\nmocked", encoding="utf-8")
        return _FakeIR()

    orig_run = ir.run_iteration
    ir.run_iteration = fake_run

    last_result = None
    for i in range(1, 11):
        cid = f"C-H6-{i:03d}"
        result = IngestResult(case_id=cid, feedback_count=3, rule_count=2)
        fi._bump_state(result, cid)
        if i < 10:
            if result.iteration_triggered:
                FAIL.append(f"T1_第{i}案不应触发")
                print(f"  FAIL  第{i}案不应触发")
        last_result = result

    check("T1_第10案触发", last_result.iteration_triggered)
    check("T1_触发seq=1", invoked.get("seq") == 1, f"seq={invoked.get('seq')}")
    check("T1_dry_run=False", invoked.get("dry_run") is False)
    check("T1_报告路径有值", last_result.iteration_report_path is not None,
          f"path={last_result.iteration_report_path}")
    check("T1_报告文件存在", fake_report.exists())
    check("T1_报告内容正确", "Iteration Report #001" in fake_report.read_text(encoding="utf-8"))

    # 检查 state json
    state_data = json.loads((meta / "iteration-state.json").read_text(encoding="utf-8"))
    check("T1_state_completed=10", state_data["feedback_completed_count"] == 10,
          f"got={state_data['feedback_completed_count']}")
    check("T1_state_seq=1", state_data["iteration_seq"] == 1)
    check("T1_state_10cids", len(state_data["completed_case_ids"]) == 10)

    # 还原
    fi.META_DIR = orig_meta
    fi.ITERATION_STATE_FILE = orig_state
    ir.run_iteration = orig_run

# ── T2: 异常 warn-only ───────────────────────────────
with tempfile.TemporaryDirectory() as td:
    meta = pathlib.Path(td) / "META"
    meta.mkdir()
    fi.META_DIR = meta
    fi.ITERATION_STATE_FILE = meta / "iteration-state.json"

    def boom(**kwargs): raise RuntimeError("boundary_miner 挂了")
    orig_run = ir.run_iteration
    ir.run_iteration = boom

    last_result = None
    for i in range(1, 11):
        cid = f"C-H6F-{i:03d}"
        r = IngestResult(case_id=cid, feedback_count=1, rule_count=1)
        r.iteration_diff = IterationDiff(case_id=cid, ts="", case_count=0)
        fi._bump_state(r, cid)
        last_result = r

    check("T2_第10案触发", last_result.iteration_triggered)
    check("T2_报告路径为None", last_result.iteration_report_path is None,
          f"path={last_result.iteration_report_path}")
    notes = " ".join(last_result.iteration_diff.notes if last_result.iteration_diff else [])
    check("T2_notes含warn-only", "warn-only" in notes, f"notes={notes[:200]}")
    check("T2_notes含异常消息", "boundary_miner 挂了" in notes)

    fi.META_DIR = orig_meta
    fi.ITERATION_STATE_FILE = orig_state
    ir.run_iteration = orig_run

# ── T3: 20 案触发两次 seq=1,2 ────────────────────────
with tempfile.TemporaryDirectory() as td:
    meta = pathlib.Path(td) / "META"
    meta.mkdir()
    fi.META_DIR = meta
    fi.ITERATION_STATE_FILE = meta / "iteration-state.json"

    triggered_at = []
    class _FakeIR2:
        report_path = None
    def fake_run2(*, seq, dry_run): return _FakeIR2()
    orig_run = ir.run_iteration
    ir.run_iteration = fake_run2

    for i in range(1, 21):
        cid = f"C-H6X-{i:03d}"
        r = IngestResult(case_id=cid, feedback_count=1, rule_count=1)
        fi._bump_state(r, cid)
        if r.iteration_triggered:
            triggered_at.append((i, r.iteration_seq))

    check("T3_20案触发两次", triggered_at == [(10,1),(20,2)],
          f"triggered_at={triggered_at}")

    fi.META_DIR = orig_meta
    fi.ITERATION_STATE_FILE = orig_state
    ir.run_iteration = orig_run

# ── T4: 重复案不重复计数 ──────────────────────────────
with tempfile.TemporaryDirectory() as td:
    meta = pathlib.Path(td) / "META"
    meta.mkdir()
    fi.META_DIR = meta
    fi.ITERATION_STATE_FILE = meta / "iteration-state.json"

    cid = "C-H6-DUP"
    for _ in range(5):
        r = IngestResult(case_id=cid, feedback_count=1, rule_count=1)
        fi._bump_state(r, cid)

    check("T4_重复计数=1", r.feedback_completed_count == 1,
          f"count={r.feedback_completed_count}")
    check("T4_重复不触发", not r.iteration_triggered)

    fi.META_DIR = orig_meta
    fi.ITERATION_STATE_FILE = orig_state

print(f"\nH6: {len(PASS)}/{len(PASS)+len(FAIL)} PASS  {'OK' if not FAIL else 'FAIL: '+str(FAIL)}")
sys.exit(0 if not FAIL else 1)
