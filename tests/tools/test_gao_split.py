"""高派拆分产物专项测试

SPLIT-1 agent 的 369 条拆分规则缺专项测试。本文件验证拆分产物的
结构性约束，防止后续批次引入回归。

覆盖：
1. ID 连续无缺号、无重复（G-SP-001..369）
2. split_from 全部指向真实存在的高派原始条目
3. 每条拆分规则的 statement 是单一判断（不含 ①②③ 多单位标记）
4. domain/topic 在白名单内
5. raw_file / raw_anchor 可回读（validate 已覆盖，这里做联合检查）
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SPLIT_DIR = ROOT / "theory" / "raw" / "gao" / "promoted"
GAO_INDEX = ROOT / "theory" / "gao" / "index.yaml"

DOMAIN_WHITELIST = {
    "lifa", "xiangfa", "shensha", "caiyun", "hunyin", "dayun",
    "mingong", "jiankang", "liuqin", "jiaoyu", "zhiye", "geju",
    "yingqi", "tiaohou", "unmapped",
}
# 多单位标记：拆分后的单条不应再含这些
MULTI_UNIT = re.compile(r"[①②③④⑤⑥⑦⑧⑨⑩]")


def _yaml_block(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    m = re.search(r"```yaml\s*\n(.*?)```", text, re.DOTALL)
    if not m:
        return []
    return yaml.safe_load(m.group(1)) or []


@pytest.fixture(scope="module")
def split_rules() -> list[dict]:
    rules: list[dict] = []
    for f in sorted(SPLIT_DIR.glob("deep-extract-gao-split-*.md")):
        rules.extend(_yaml_block(f))
    return rules


@pytest.fixture(scope="module")
def gao_ids() -> set[str]:
    data = yaml.safe_load(GAO_INDEX.read_text(encoding="utf-8-sig")) or {}
    return {r["id"] for r in (data.get("rules") or []) if isinstance(r, dict)}


def test_split_files_exist() -> None:
    files = sorted(SPLIT_DIR.glob("deep-extract-gao-split-*.md"))
    assert files, "找不到任何拆分批次文件"


def test_split_rules_nonempty(split_rules) -> None:
    assert len(split_rules) >= 300, f"拆分规则仅 {len(split_rules)} 条，少于预期"


def test_ids_unique(split_rules) -> None:
    ids = [r["id"] for r in split_rules]
    dup = {i for i in ids if ids.count(i) > 1}
    assert not dup, f"重复 ID: {sorted(dup)[:10]}"


def test_ids_contiguous_from_001(split_rules) -> None:
    nums = sorted(int(r["id"].removeprefix("G-SP-")) for r in split_rules)
    assert nums[0] == 1, f"起始编号不是 1，而是 {nums[0]}"
    missing = set(range(1, max(nums) + 1)) - set(nums)
    assert not missing, f"ID 有缺号: {sorted(missing)[:15]}"


def test_all_have_split_from(split_rules) -> None:
    missing = [r["id"] for r in split_rules if not r.get("split_from")]
    assert not missing, f"缺 split_from: {missing[:10]}"


def test_split_from_points_to_real_gao_rule(split_rules, gao_ids) -> None:
    """split_from 必须能解析到高派既有条目。

    允许两种来源：index.yaml 里的原始条目，或本批拆分自身的上级
    （少数条目由一次拆分再细分）。这里只校验「能在 gao_ids 或本批内找到」。
    """
    own_ids = {r["id"] for r in split_rules}
    bad = [
        (r["id"], r["split_from"])
        for r in split_rules
        if r["split_from"] not in gao_ids and r["split_from"] not in own_ids
    ]
    assert not bad, f"split_from 悬空: {bad[:10]}"


def test_statement_is_single_unit(split_rules) -> None:
    """拆分后每条只应含一个判断，不应再有 ①②③ 多单位标记。"""
    bad = [r["id"] for r in split_rules if MULTI_UNIT.search(str(r.get("statement", "")))]
    assert not bad, f"仍含多单位标记: {bad[:10]}"


def test_domain_whitelist(split_rules) -> None:
    bad = [
        (r["id"], r.get("domain"))
        for r in split_rules
        if str(r.get("domain") or "").strip() not in DOMAIN_WHITELIST
    ]
    assert not bad, f"domain 越界: {bad[:10]}"


def test_required_fields(split_rules) -> None:
    required = ("id", "school", "classic_name", "title", "statement",
                "raw_file", "raw_anchor", "source_ref")
    bad = []
    for r in split_rules:
        miss = [k for k in required if not r.get(k)]
        if miss:
            bad.append((r.get("id"), miss))
    assert not bad, f"字段缺失: {bad[:10]}"


def test_school_is_gao(split_rules) -> None:
    bad = [r["id"] for r in split_rules if r.get("school") != "gao"]
    assert not bad, f"school 非 gao: {bad[:10]}"


def test_raw_anchor_is_line_anchor(split_rules) -> None:
    bad = [
        (r["id"], r.get("raw_anchor"))
        for r in split_rules
        if not re.fullmatch(r"line:\d+(?:-\d+)?", str(r.get("raw_anchor") or "").strip())
    ]
    assert not bad, f"raw_anchor 格式非法: {bad[:10]}"


def test_statement_length_bounded(split_rules) -> None:
    """拆分后单条 statement 应短于合并时的原文（阈值 200 与 validator 一致）。"""
    bad = [(r["id"], len(str(r.get("statement", "")))) for r in split_rules
           if len(str(r.get("statement", ""))) > 200]
    assert not bad, f"statement 超 200 字: {bad[:10]}"
