"""T-164 地址级证据盘点工具测试（确定性，不落盘）。

覆盖：
1. 12 条婚姻信号全部落到三态（有地址 / 只有聚合 / 缺失），且「有地址」为 0；
2. 地址串里的 members 都是合法盘面地址（Y/M/D/H + .s/.b）；
3. actor=None 的制用候选只出现在冲/刑/穿/天干冲上（代码只对 ke 设 actor）；
4. 两次构建逐字节一致（无时间戳）；
5. `engine.cli relations` 回放与 API 边表一致（1 例，防地址串与 CLI 脱钩）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import address_level_evidence_audit as audit  # noqa: E402

ADDR_HEADS = {"Y", "M", "D", "H"}


@pytest.fixture(scope="module")
def payload() -> dict:
    return audit.build_payload(limit=3, check_cli=False)


def test_population_invariants(payload: dict) -> None:
    pop = payload["population"]
    assert pop["cases_total"] == audit.EXPECTED_CASES
    assert pop["usable_for_timing"] == 3  # --limit 3
    assert pop["labeled_negative_positive"] <= 3


def test_every_signal_classified(payload: dict) -> None:
    signals = payload["signal_map"]
    assert len(signals) == 12
    allowed = {audit.ADDRESSED, audit.AGGREGATE, audit.MISSING}
    for signal in signals:
        assert signal["classification"] in allowed, signal["id"]
        assert signal["code_loc"]
        assert signal["gaps"]
    counts = payload["classification_counts"]
    assert counts["有地址"] == 0
    assert counts["只有聚合"] + counts["缺失"] == 12
    assert counts["缺失"] == 1


def test_examples_use_real_addresses(payload: dict) -> None:
    examples = payload["examples"]
    assert len(examples) == 3
    for example in examples:
        assert example["day_branch_address"].startswith("D.b=")
        assert example["cli_command"].startswith("python -m engine.cli relations")
        for edge in example["edge_evidence"]:
            for member in edge["members"]:
                head, layer = member.split(".")
                assert head in ADDR_HEADS
                assert layer in ("s", "b")


def test_actor_none_only_on_undirected_kinds() -> None:
    payload = audit.build_payload(limit=12, check_cli=False)
    kinds = set(payload["actor_none"]["zhiyong_actor_none_by_relation_kind"])
    assert kinds <= {"chong", "xing", "chuan", "stem_chong"}
    assert payload["actor_none"]["zhiyong_actor_none_total"] > 0


def test_payload_is_deterministic() -> None:
    first = json.dumps(audit.build_payload(limit=3, check_cli=False), ensure_ascii=False, sort_keys=True)
    second = json.dumps(audit.build_payload(limit=3, check_cli=False), ensure_ascii=False, sort_keys=True)
    assert first == second


def test_cli_parity_on_one_case() -> None:
    payload = audit.build_payload(limit=1, check_cli=True)
    assert payload["cli_parity"]["checked"] is True
    assert payload["cli_parity"]["mismatches"] == []
    assert payload["examples"][0]["cli_check"]["mismatches"] == []
