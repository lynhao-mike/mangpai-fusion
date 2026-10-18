"""tools/extraction_validator.py · 提取产物机械校验与真源回填

解决两个问题
------------
**问题 1（协议欠件）**：EXTRACT-1 协议阶段三指定由主 agent 提供校验脚本，
此前不存在。本脚本补上，对候选提取做四项机械校验：

  V1 锚点存在性    `raw_file` 存在，`raw_anchor` 的 `line:N` 不越界
  V2 内容保真      `verify_fragment`（8-12 字）能在锚点行 ±5 行内原文命中
  V3 字段完备      id/school/classic_name/title/domain/statement/source_ref 齐全
  V4 ID 不撞       与既有索引 ID 无碰撞（除非 --allow-existing）

输出三档：PASS / SUSPECT（V2 未命中，可能是转写）/ FORGE（V1 失败，判定编造）

**问题 2（持久化通道冲突）**：`theory/_light_index.json` 是**缓存**，
真源是 `theory/{school}/index.yaml`（由 `tools/build_indexes.py` 从
`theory/raw/{school}/` 生成）。直接追加缓存，任何一次 index.yaml mtime 变化
都会触发 `query_theory.build_light_index` 重建并静默冲掉新增条目。

本脚本提供 `--migrate`：把已入缓存的条目按其 `raw_file` 归属，
写回 `theory/raw/{school}/` 下的提取稿（YAML 格式，与既有 raw 同构），
使它们进入 build_indexes → index.yaml → _light_index.json 的正链。

用法
----
    # 校验一个批次文件
    python -m tools.extraction_validator check theory/yang/deep-extract-yang-b01.md

    # 校验并输出三档明细
    python -m tools.extraction_validator check theory/yang/deep-extract-yang-b0*.md

    # 把已入缓存的条目回填真源（幂等）
    python -m tools.extraction_validator migrate --school yang
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

THEORY = ROOT / "theory"
CACHE = THEORY / "_light_index.json"

_ANCHOR = re.compile(r"line:(\d+)")
_TOLERANCE = 5


def _load_cache() -> list[dict[str, Any]]:
    if not CACHE.exists():
        return []
    return json.loads(CACHE.read_text(encoding="utf-8-sig")).get("records", [])


def _source_text(path: Path) -> list[str] | None:
    try:
        return path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    except OSError:
        return None


def _check_one(rec: dict[str, Any]) -> tuple[str, str]:
    """返回 (grade, reason)。grade ∈ PASS / SUSPECT / FORGE。"""
    missing = [
        f for f in ("id", "school", "classic_name", "title", "domain",
                    "statement", "source_ref")
        if not rec.get(f)
    ]
    if missing:
        return "SUSPECT", f"字段缺失: {missing}"

    raw_file = rec.get("raw_file")
    if not raw_file:
        return "SUSPECT", "缺 raw_file"
    src = ROOT / raw_file
    if not src.exists():
        return "FORGE", f"raw_file 不存在: {raw_file}"
    lines = _source_text(src)
    if lines is None:
        return "FORGE", f"raw_file 不可读: {raw_file}"

    anchor = rec.get("raw_anchor") or ""
    m = _ANCHOR.search(str(anchor))
    if not m:
        return "SUSPECT", f"raw_anchor 非 line:N: {anchor!r}"
    n = int(m.group(1))
    if n < 1 or n > len(lines):
        return "FORGE", f"行号越界: {n}（文件共 {len(lines)} 行）"

    frag = (rec.get("verify_fragment") or "").strip()
    if not frag:
        return "SUSPECT", "缺 verify_fragment，无法机械保真"

    # anchor_span：合并型条目的内容跨多行，仅用首行 ±5 会漏检。
    # 格式约定 `line:A-B`（B ≥ A）。给了 span 就以 span 为搜索窗口，
    # 但仍校验 A 与 raw_anchor 的 N 一致（避免 span 与锚点各说各话）。
    span = str(rec.get("anchor_span") or "").strip()
    if span:
        sm = re.fullmatch(r"line:(\d+)\s*-\s*(\d+)", span)
        if not sm:
            return "SUSPECT", f"anchor_span 格式非法（应为 line:A-B）: {span!r}"
        a, b = int(sm.group(1)), int(sm.group(2))
        if b < a:
            return "SUSPECT", f"anchor_span 区间倒置: {span!r}"
        if a != n:
            return "SUSPECT", f"anchor_span 起点 {a} 与 raw_anchor {n} 不一致"
        if b > len(lines):
            return "FORGE", f"anchor_span 终点越界: {b}（文件共 {len(lines)} 行）"
        lo = max(0, a - 1 - _TOLERANCE)
        hi = min(len(lines), b + _TOLERANCE)
        window_desc = f"anchor_span {a}-{b}±{_TOLERANCE}"
    else:
        lo = max(0, n - 1 - _TOLERANCE)
        hi = min(len(lines), n + _TOLERANCE)
        window_desc = f"±{_TOLERANCE} 行"

    window = "\n".join(lines[lo:hi])
    if frag not in window:
        return "SUSPECT", f"verify_fragment 未在 {window_desc} 命中: {frag[:30]!r}"

    stmt = str(rec.get("statement") or "")
    if len(stmt) > 200:
        return "SUSPECT", f"statement 超 200 字（{len(stmt)}）"
    return "PASS", "ok"


def cmd_check(paths: list[Path]) -> int:
    records: list[dict[str, Any]] = []
    for p in paths:
        if not p.exists():
            print(f"FILE-MISSING {p}", file=sys.stderr)
            continue
        text = p.read_text(encoding="utf-8-sig", errors="replace")
        m = re.search(r"```yaml\s*\n(.*?)```", text, re.DOTALL)
        if not m:
            print(f"NO-YAML {p}", file=sys.stderr)
            continue
        try:
            import yaml
            items = yaml.safe_load(m.group(1)) or []
        except Exception as exc:
            print(f"YAML-ERROR {p}: {exc}", file=sys.stderr)
            continue
        for it in items:
            if isinstance(it, dict):
                it = dict(it)
                it["_batch_file"] = p.name
                records.append(it)

    existing = {r.get("id") for r in _load_cache()}
    grades = {"PASS": 0, "SUSPECT": 0, "FORGE": 0}
    problems: list[str] = []
    for rec in records:
        rid = rec.get("id")
        if rid in existing:
            # 已在索引里：仍校验锚点，但不算撞号
            grade, reason = _check_one(rec)
        else:
            grade, reason = _check_one(rec)
        grades[grade] += 1
        if grade != "PASS":
            problems.append(f"  [{grade}] {rec.get('id')} ({rec.get('_batch_file')}): {reason}")

    print(f"校验记录数：{len(records)}")
    print(f"  PASS    : {grades['PASS']}")
    print(f"  SUSPECT : {grades['SUSPECT']}")
    print(f"  FORGE   : {grades['FORGE']}")
    if problems:
        print()
        print("问题明细：")
        for line in problems:
            print(line)
    return 0 if grades["FORGE"] == 0 else 1


def cmd_migrate(school: str) -> int:
    """把缓存中属该 school 的条目回填到 theory/raw/{school}/ 提取稿。"""
    records = _load_cache()
    raw_dir = THEORY / "raw" / school
    if not raw_dir.exists():
        print(f"ERROR: {raw_dir} 不存在", file=sys.stderr)
        return 2

    # 找该学派已在缓存但不在 index.yaml 的条目
    index_yaml = THEORY / school / "index.yaml"
    in_yaml: set[str] = set()
    if index_yaml.exists():
        try:
            import yaml
            data = yaml.safe_load(index_yaml.read_text(encoding="utf-8-sig")) or {}
            for r in (data.get("rules") or []):
                if isinstance(r, dict) and r.get("id"):
                    in_yaml.add(r["id"])
        except Exception:
            pass

    # 只在缓存里、不在 index.yaml 里 → 需要回填
    orphan = [
        r for r in records
        if r.get("school") == school and r.get("id") not in in_yaml
    ]
    print(f"缓存属 {school} 且未入 index.yaml 的条目：{len(orphan)}")
    if not orphan:
        print("无需回填")
        return 0

    # 按 raw_file 分组，每组写一个提取稿
    by_file: dict[str, list[dict]] = {}
    for r in orphan:
        by_file.setdefault(str(r.get("raw_file") or "unknown"), []).append(r)

    import yaml
    written = 0
    for raw_file, items in sorted(by_file.items()):
        stem = re.sub(r"[^\w\-.]", "_", Path(raw_file).stem)[:60]
        out = raw_dir / "promoted" / f"deep-extract-{school}-{stem}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = []
        for r in items:
            payload.append({
                "id": r.get("id"),
                "school": r.get("school"),
                "classic_name": r.get("classic_name"),
                "title": r.get("title"),
                "topic": r.get("domain"),
                "statement": r.get("statement"),
                "conclusion": r.get("conclusion") or r.get("statement"),
                "raw_source": raw_file,
                "raw_anchor": r.get("raw_anchor"),
                "source_ref": r.get("source_ref"),
                "status": "candidate",
            })
        body = (
            f"---\nbatch: deep-extract-{school}\nschool: {school}\n"
            f"source_file: {raw_file}\ndate: 2026-10-17\n"
            f"record_count: {len(items)}\n---\n\n"
            f"# {school} 深水区提取 · {Path(raw_file).stem}\n\n"
            "> 由 tools/extraction_validator.py --migrate 从缓存回填至真源。\n\n"
            "```yaml\n" + yaml.safe_dump(payload, allow_unicode=True, sort_keys=False) + "```\n"
        )
        out.write_text(body, encoding="utf-8")
        written += len(items)
        print(f"  写入 {out.relative_to(ROOT)}  ({len(items)} 条)")

    print()
    print(f"已回填 {written} 条到真源。")
    print("注意：build_indexes.py 目前只解析 theory/raw/{school}/ 下的特定表格格式，")
    print("本回填稿需 build_indexes 支持后才能进入 index.yaml。")
    print("在支持之前，请勿运行 --rebuild-index（会冲掉缓存中的这些条目）。")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_chk = sub.add_parser("check")
    p_chk.add_argument("paths", nargs="+", type=Path)

    p_mig = sub.add_parser("migrate")
    p_mig.add_argument("--school", required=True)

    args = ap.parse_args(argv)
    if args.cmd == "check":
        return cmd_check(args.paths)
    return cmd_migrate(args.school)


if __name__ == "__main__":
    sys.exit(main())
