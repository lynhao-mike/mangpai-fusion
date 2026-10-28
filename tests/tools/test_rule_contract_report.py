"""T-163 · ``rule_contract_report`` 的 ``--out-prefix`` 路径参数测试。

覆盖：
1. 指定 tmp 前缀 → 只写 ``<prefix>.json`` / ``<prefix>.md``，退出码 0；
2. 默认调用（无参数）仍是 ``META/rule-contract-dryrun-v1`` 前缀（monkeypatch 到 tmp 跑，
   不污染仓库）；
3. 前缀目录不存在 → 退出码 2，且不创建目录、不写文件；
4. 只写成功一个文件 → 退出码 2；
5. 两次真实运行逐字节一致（JSON 与 MD）。

统计逻辑、规则读取、表格输出不在本文件断言范围内；真实运行只比对文件落点与字节。
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tools import rule_contract_report as mod


def _minimal_payload() -> dict:
    """够 ``_render_markdown`` 渲染的最小 payload，供不跑 382 例的路径测试用。"""
    return {
        "schema": "rule-contract-dryrun/v1",
        "task": "T-152",
        "corpus": {
            "path": "META/timing-eval-set-v1.json",
            "filter": "usable_for_timing=true",
            "n_cases": 0,
            "n_built": 0,
            "n_build_failed": 0,
            "build_failures": [],
        },
        "matched_equals_triggered": True,
        "rules": [],
        "totals": {
            "n_evaluated": 0,
            "n_triggered": 0,
            "n_counter": 0,
            "n_suppressed_if_flipped": 0,
        },
    }


def _stub_evaluation(monkeypatch: pytest.MonkeyPatch) -> None:
    """把建盘/统计换成空结果，只测路径与写出行为。"""
    monkeypatch.setattr(mod, "_evaluate_corpus", lambda cases, rules: ({}, []))
    monkeypatch.setattr(
        mod,
        "_build_payload",
        lambda registry_rules, stats, cases, failures: _minimal_payload(),
    )


@pytest.fixture(scope="module")
def real_run(tmp_path_factory: pytest.TempPathFactory) -> tuple[int, Path]:
    prefix = tmp_path_factory.mktemp("t163") / "dryrun-real"
    return mod.main(["--out-prefix", str(prefix)]), prefix


def test_out_prefix_writes_both_files(real_run: tuple[int, Path]) -> None:
    rc, prefix = real_run
    json_path = Path(f"{prefix}.json")
    md_path = Path(f"{prefix}.md")
    assert rc == 0
    assert json_path.is_file() and md_path.is_file()
    assert json_path.stat().st_size > 0 and md_path.stat().st_size > 0
    assert {path.name for path in prefix.parent.iterdir()} == {json_path.name, md_path.name}


def test_two_runs_are_byte_identical(
    real_run: tuple[int, Path], tmp_path_factory: pytest.TempPathFactory
) -> None:
    rc_first, first = real_run
    second = tmp_path_factory.mktemp("t163") / "dryrun-real-2"
    rc_second = mod.main(["--out-prefix", str(second)])
    assert rc_first == rc_second == 0
    for suffix in (".json", ".md"):
        assert Path(f"{first}{suffix}").read_bytes() == Path(f"{second}{suffix}").read_bytes()


def test_default_prefix_is_still_v1() -> None:
    assert mod.DEFAULT_OUT_PREFIX == "META/rule-contract-dryrun-v1"
    assert mod._build_arg_parser().parse_args([]).out_prefix == mod.DEFAULT_OUT_PREFIX
    default_prefix = mod._resolve_out_prefix(mod.DEFAULT_OUT_PREFIX)
    assert default_prefix == mod.ROOT / "META" / "rule-contract-dryrun-v1"
    assert mod._output_paths(default_prefix) == (
        mod.ROOT / "META" / "rule-contract-dryrun-v1.json",
        mod.ROOT / "META" / "rule-contract-dryrun-v1.md",
    )


def test_default_call_writes_v1_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _stub_evaluation(monkeypatch)
    monkeypatch.setattr(mod, "DEFAULT_OUT_PREFIX", str(tmp_path / "rule-contract-dryrun-v1"))

    assert mod.main([]) == 0

    json_path = tmp_path / "rule-contract-dryrun-v1.json"
    md_path = tmp_path / "rule-contract-dryrun-v1.md"
    assert json_path.is_file() and md_path.is_file()
    stdout = capsys.readouterr().out
    assert f"已写出：{json_path}" in stdout
    assert f"已写出：{md_path}" in stdout


def test_missing_directory_exits_2_without_writing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    prefix = tmp_path / "missing" / "dryrun"

    assert mod.main(["--out-prefix", str(prefix)]) == 2

    assert not (tmp_path / "missing").exists()
    assert "输出目录不存在" in capsys.readouterr().err


def test_only_one_file_written_exits_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _stub_evaluation(monkeypatch)
    prefix = tmp_path / "dryrun"
    (tmp_path / "dryrun.md").mkdir()  # 让 .md 必然写失败，只剩 .json

    assert mod.main(["--out-prefix", str(prefix)]) == 2

    assert (tmp_path / "dryrun.json").is_file()
    assert (tmp_path / "dryrun.md").is_dir()
    assert "写出失败" in capsys.readouterr().err
