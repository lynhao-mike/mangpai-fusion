"""tests/tools/test_verify_baseline.py · T-162

覆盖「测出 0 分」与「根本没跑起来」的区分：
1. pytest 正常跑（有 passed 汇总）→ pytest_ran=True、passed=1246；
2. 空输出 rc=1 → 计数为 None、--save 退出 2 且不写文件；
3. 有 failed → passed/failed 解析正确、--save 因 rc!=0 退出 2 且不写文件；
4. 已有基线 + 本次未跑 → --compare 退出 2，不报「通过数下降」；
5. 正常 --save 后 --compare 退出 0。

全部用 monkeypatch 替换 run()，不真的跑 pytest。
"""
from __future__ import annotations

import json
import sys

import pytest

from tools import verify_baseline as mod

PYTEST_OK = (0, "1246 passed, 1 skipped in 90.12s")
AUDIT_OK = (0, "案例 481；有问题 0；问题种类 0；口径说明 0")
RELATIONS_OK = (0, "关系图全量校验 · cases/\n案例总数: 481\n\n结论: 全部通过")
ZUOGONG_OK = (0, "盘数 481；有宫制星候选 477 (99.2%)；actor=D.b 346 (71.9%)")


def make_run(pytest_result, *, audit=AUDIT_OK, relations=RELATIONS_OK, zuogong=ZUOGONG_OK):
    """伪造 run()：只认四种命令，其余命令直接失败，避免悄悄跑真实工具。"""
    calls: list[list[str]] = []

    def fake_run(args):
        calls.append(list(args))
        if args[:2] == ["-m", "pytest"]:
            return pytest_result
        if "tools.engine_audit" in args:
            return audit
        if "tools.relations_audit" in args:
            return relations
        if "tools.zuogong_probe" in args:
            return zuogong
        raise AssertionError(f"未预期的命令: {args!r}")

    fake_run.calls = calls
    return fake_run


def baseline_payload(**overrides):
    data = {
        "pytest_passed": 1246,
        "pytest_failed": 0,
        "pytest_rc": 0,
        "audit_errors": 0,
        "audit_rc": 0,
        "relations_ok": True,
        "relations_rc": 0,
        "zuogong_charts": 477,
        "zuogong_day_branch": 346,
        "zuogong_rc": 0,
        "quick": False,
    }
    data.update(overrides)
    return data


def invoke(monkeypatch, tmp_path, argv, fake_run):
    """把模块的 run()/基线路径/sys.argv 换掉后调用 main()。"""
    baseline = tmp_path / "baseline-v1.json"
    monkeypatch.setattr(mod, "run", fake_run)
    monkeypatch.setattr(mod, "BASELINE", baseline)
    monkeypatch.setattr(sys, "argv", ["verify_baseline", *argv])
    return mod.main(), baseline


def test_measure_success(monkeypatch):
    monkeypatch.setattr(mod, "run", make_run(PYTEST_OK))
    m = mod.measure(False)

    assert m["pytest_ran"] is True
    assert m["pytest_parse_ok"] is True
    assert m["pytest_passed"] == 1246
    assert m["pytest_failed"] == 0
    assert m["pytest_rc"] == 0
    assert m["audit_ran"] is True
    assert m["relations_ran"] is True
    assert m["zuogong_ran"] is True
    assert m["zuogong_charts"] == 477
    assert m["zuogong_day_branch"] == 346


def test_measure_empty_output_is_null_not_zero(monkeypatch):
    monkeypatch.setattr(mod, "run", make_run((1, "")))
    m = mod.measure(False)

    assert m["pytest_ran"] is False
    assert m["pytest_parse_ok"] is False
    assert m["pytest_passed"] is None
    assert m["pytest_failed"] is None
    assert m["pytest_rc"] == 1


def test_save_refuses_when_pytest_not_ran(monkeypatch, tmp_path, capsys):
    fake = make_run((1, ""))
    code, baseline = invoke(monkeypatch, tmp_path, ["--save"], fake)

    assert code == 2
    assert not baseline.exists()
    out = capsys.readouterr().out
    assert "拒绝写入基线" in out
    assert "pytest 未跑起来" in out


def test_failed_run_parses_counts_and_blocks_save(monkeypatch, tmp_path, capsys):
    fake = make_run((1, "3 failed, 10 passed in 5.00s"))
    monkeypatch.setattr(mod, "run", fake)
    m = mod.measure(False)

    assert m["pytest_ran"] is True
    assert m["pytest_parse_ok"] is True
    assert m["pytest_passed"] == 10
    assert m["pytest_failed"] == 3

    code, baseline = invoke(monkeypatch, tmp_path, ["--save"], fake)
    assert code == 2
    assert not baseline.exists()
    out = capsys.readouterr().out
    assert "拒绝写入基线" in out
    assert "pytest 退出码 1" in out


def test_compare_refuses_when_pytest_not_ran(monkeypatch, tmp_path, capsys):
    baseline = tmp_path / "baseline-v1.json"
    baseline.write_text(json.dumps(baseline_payload()), encoding="utf-8")

    code, _ = invoke(monkeypatch, tmp_path, ["--compare"], make_run((1, "")))

    assert code == 2
    out = capsys.readouterr().out
    assert "pytest 未跑起来，不能与基线比较" in out
    assert "通过数" not in out


def test_compare_refuses_null_baseline_field(monkeypatch, tmp_path, capsys):
    baseline = tmp_path / "baseline-v1.json"
    baseline.write_text(json.dumps(baseline_payload(pytest_passed=None)), encoding="utf-8")

    code, _ = invoke(monkeypatch, tmp_path, ["--compare"], make_run(PYTEST_OK))

    assert code == 2
    out = capsys.readouterr().out
    assert "无法比较" in out
    assert "pytest_passed" in out


def test_save_then_compare_ok(monkeypatch, tmp_path, capsys):
    code, baseline = invoke(monkeypatch, tmp_path, ["--save"], make_run(PYTEST_OK))
    assert code == 0
    assert baseline.exists()

    saved = json.loads(baseline.read_text(encoding="utf-8"))
    assert saved["pytest_ran"] is True
    assert saved["pytest_parse_ok"] is True
    assert saved["pytest_passed"] == 1246
    assert saved["pytest_failed"] == 0
    assert saved["audit_ran"] is True
    assert saved["relations_ran"] is True
    assert saved["zuogong_ran"] is True
    assert saved["quick"] is False

    code, _ = invoke(monkeypatch, tmp_path, ["--compare"], make_run(PYTEST_OK))
    assert code == 0
    out = capsys.readouterr().out
    assert "基线未退步" in out


def test_regressions_rejects_null_side():
    old = baseline_payload()
    new = baseline_payload(pytest_passed=None)

    with pytest.raises(mod.BaselineError):
        mod.regressions(old, new)
