# -*- coding: utf-8 -*-
"""T-190b · B 卷交付自检（只做结构/对齐/逐字引文/哈希，不评分、不读 A 答案）。

用法：
    python tasks/T-190b/verify_b.py [--expect-hash <sha256>]

退出码 0 = 全部通过；1 = 有失败项。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BLIND = ROOT / "META/p1-anchor-60-blind-v1.json"
ANSWERS = ROOT / "META/p1-anchor-60-answers-B-v1.json"
SOURCES = ROOT / "sources/duan"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
FIXED = ("克", "生", "化", "墓")
DYNAMIC = ("冲", "合", "穿", "刑")
DIRECTIONS = ("actor→target", "mutual", "needs_judgment")

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_line(rel_locator: str) -> str | None:
    """定位符形如 sources/duan/xxx.md:L123。"""
    try:
        path_part, line_part = rel_locator.rsplit(":L", 1)
        n = int(line_part)
    except (ValueError, AttributeError):
        fail(f"非法定位符：{rel_locator!r}")
        return None
    path = ROOT / path_part
    if not path.is_file():
        fail(f"原文文件不存在：{rel_locator}")
        return None
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not (1 <= n <= len(lines)):
        fail(f"行号越界：{rel_locator}（共 {len(lines)} 行）")
        return None
    return lines[n - 1]


def check_source_ref(cid: str, ref: str, quote: str) -> None:
    text = read_line(ref)
    if text is None:
        return
    if quote not in text:
        fail(f"{cid}: quote 不在 source_ref 行内：{ref}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--expect-hash", default=None)
    args = ap.parse_args()

    if not BLIND.is_file() or not ANSWERS.is_file():
        print("FAIL：缺盲卷或答案文件", file=sys.stderr)
        return 1
    blind = load_json(BLIND)
    doc = load_json(ANSWERS)
    cases = doc.get("cases")
    if not isinstance(cases, list):
        print("FAIL：answers.cases 不是数组", file=sys.stderr)
        return 1

    if doc.get("schema_version") != "p1-adjudication-answers/v2":
        fail("schema_version 不是 p1-adjudication-answers/v2")
    if len(cases) != 60:
        fail(f"答案条数 {len(cases)} != 60")
    if doc.get("case_count") != len(cases):
        fail("case_count 与 cases 条数不符")

    blind_cases = blind.get("cases", [])
    if [c.get("case_id") for c in cases] != [c.get("case_id") for c in blind_cases]:
        fail("case_id 顺序/集合与盲卷不一致")

    counts = {"fixed": 0, "dynamic": 0, "ambiguous": 0}
    for idx, (case, bcase) in enumerate(zip(cases, blind_cases)):
        cid = case.get("case_id", f"#{idx}")
        layer = case.get("layer")
        if layer not in counts:
            fail(f"{cid}: 非法 layer {layer!r}")
            continue
        counts[layer] += 1
        if layer != bcase.get("layer"):
            fail(f"{cid}: layer 与盲卷不一致")
        if case.get("chart_id") != bcase.get("chart_id"):
            fail(f"{cid}: chart_id 与盲卷不一致")
        if case.get("four_pillars") != bcase.get("four_pillars"):
            fail(f"{cid}: 四柱与盲卷不一致")
        if not case.get("quote") or not case.get("source_ref") or not case.get("annotation"):
            fail(f"{cid}: 缺 quote/source_ref/annotation")

        for side in ("a", "b"):
            ch = case.get(f"char_{side}")
            if not isinstance(ch, str) or len(ch) != 1 or ch not in ZHI:
                fail(f"{cid}: char_{side}={ch!r} 不是单个地支字")
        kind = case.get("kind")
        if layer == "fixed" and kind not in FIXED:
            fail(f"{cid}: fixed kind={kind!r} 非法")
        if layer == "dynamic" and kind not in DYNAMIC:
            fail(f"{cid}: dynamic kind={kind!r} 非法")

        expected = case.get("expected_direction")
        if expected not in DIRECTIONS:
            fail(f"{cid}: expected_direction={expected!r} 非法")
        if layer in ("fixed", "dynamic") and expected == "needs_judgment":
            fail(f"{cid}: {layer} 不得 needs_judgment")
        if layer == "ambiguous" and expected != "needs_judgment":
            fail(f"{cid}: ambiguous 必须 needs_judgment")

        check_source_ref(cid, case["source_ref"], case["quote"])

        if layer == "ambiguous":
            texts = case.get("source_texts")
            if not isinstance(texts, dict) or len(texts) < 2:
                fail(f"{cid}: source_texts 少于 2 行")
                continue
            for locator, text in texts.items():
                line = read_line(locator)
                if line is not None and line != text:
                    fail(f"{cid}: source_texts[{locator}] 与原文整行不一致")
            quotes = case.get("conflict_quotes")
            if not isinstance(quotes, list) or len(quotes) != 2:
                fail(f"{cid}: conflict_quotes 不是 2 条")
                continue
            if quotes[0] == quotes[1]:
                fail(f"{cid}: conflict_quotes 两条相同")
            pool = list(texts.values())
            for q in quotes:
                if not isinstance(q, str) or not q.strip():
                    fail(f"{cid}: conflict_quotes 有空项")
                elif not any(q in text for text in pool):
                    fail(f"{cid}: conflict_quotes 非逐字：{q!r}")

    if counts != {"fixed": 10, "dynamic": 40, "ambiguous": 10}:
        fail(f"三层配比错误：{counts}")

    got_hash = sha256(ANSWERS)
    if args.expect_hash and args.expect_hash != got_hash:
        fail(f"答案 sha256 不匹配：{got_hash} != {args.expect_hash}")

    print(f"answers: {ANSWERS}")
    print(f"cases={len(cases)} layers={counts}")
    print(f"sha256={got_hash}")
    if errors:
        print(f"FAIL（{len(errors)} 项）")
        for e in errors[:50]:
            print(" -", e)
        return 1
    print("PASS: 对齐 / 三层 / 端点字 / 单引文 / ambiguous 双引文与整行 source_texts 全部通过；未评分。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
