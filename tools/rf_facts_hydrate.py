"""tools/rf_facts_hydrate.py · 为 RF 案例批量落盘 engine.cli 引擎事实

背景
----
`META/project-state.json` 的 `domain_prospective real_cohort = not_ready`，
根因不是数据不够，而是 446 个 RF 案例**从未被引擎跑过**——它们只有
`input.md` + `feedback.md`，没有 chart/relations/strength/structures 事实。

本工具读取每个案例的 `input.md`（yaml 块），按口径调用 `engine.cli`：

- 有 `公历` 字段  → `engine.cli all --birth "<公历>" --gender <乾/坤> --json`
- 无 `公历` 字段  → `engine.cli all --pillars "<四柱>" --gender <乾/坤> --json`
                   （pillar-only 口径，会返回 input_limitations）

产出
----
每个案例目录下 `facts/`：
- `all.json`           全量事实（chart + relations + strength + shensha +
                        structures + duan_zuogong + input_limitations）
- `facts_summary.json` 机器可读摘要（chart_id / 四柱 / 日主 / 起运 /
                        大运序列 / 边数 / 关键口径），供 blind_ledger 与
                        后续评测直接消费，不必反复解析大 JSON

设计取舍
--------
1. **幂等**：已存在 `facts/all.json` 的案例默认跳过，`--force` 才重跑。
2. **不猜**：`input.md` 缺性别或四柱不全 → 记为 skipped，不补造。
3. **单案例失败不中断批次**：错误记入 `facts/error.txt`，继续下一个。
4. **子进程隔离**：每个案例起一次 `engine.cli` 子进程，避免引擎内部状态
   跨案例残留（引擎本身无状态，但子进程隔离是最稳的边界）。

CLI
---
    python -m tools.rf_facts_hydrate --dry-run
    python -m tools.rf_facts_hydrate --limit 50
    python -m tools.rf_facts_hydrate --force          # 重跑已有
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_CASES_ROOT = ROOT / "cases"
_YAML_BLOCK = re.compile(r"```yaml\s*\n(.*?)```", re.DOTALL)


# ── input.md 解析 ───────────────────────────────────────────────────────────

def _yaml_scalar(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def parse_input(path: Path) -> dict[str, Any]:
    """从 input.md 抽出 birth/四柱/大运。解析失败抛 ValueError。"""
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    m = _YAML_BLOCK.search(text)
    if not m:
        raise ValueError("input.md 无 yaml 块")
    block = m.group(1)

    def field(name: str) -> str:
        fm = re.search(rf"^\s*{re.escape(name)}:\s*(.+)$", block, re.M)
        return _yaml_scalar(fm.group(1)) if fm else ""

    qian_kun = field("乾坤")
    gender = field("性别")
    solar = field("公历")
    pillars = [field(f"{p}柱") for p in ("年", "月", "日", "时")]

    if not qian_kun:
        raise ValueError(f"缺乾坤（性别字段={gender!r}）")
    if not all(pillars):
        raise ValueError(f"四柱不全: {pillars}")

    dayun = []
    dm = re.search(r"排布:\s*\n((?:\s+-\s+干支:.*\n(?:\s+起始年:.*\n)?)+)", block)
    if dm:
        for gz, yr in re.findall(r'干支:\s*"([^"]+)"\s*\n\s*起始年:\s*(\d+)', dm.group(1)):
            dayun.append({"ganzhi": gz, "start_year": int(yr)})

    return {
        "case_id": field("case_id") or path.parent.name,
        "qian_kun": qian_kun,
        "gender": gender,
        "solar": solar,
        "pillars": pillars,
        "dayun_declared": dayun,
        "strategy": field("策略"),
    }


# ── engine.cli 调用 ─────────────────────────────────────────────────────────

def run_engine_cli(parsed: dict[str, Any], timeout: int = 120) -> dict[str, Any]:
    if parsed["solar"]:
        cmd = [
            sys.executable, "-m", "engine.cli", "all",
            "--birth", parsed["solar"], "--gender", parsed["qian_kun"], "--json",
        ]
    else:
        cmd = [
            sys.executable, "-m", "engine.cli", "all",
            "--pillars", " ".join(parsed["pillars"]),
            "--gender", parsed["qian_kun"], "--json",
        ]
    proc = subprocess.run(
        cmd, cwd=ROOT, capture_output=True, encoding="utf-8", timeout=timeout
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"engine.cli 退出码 {proc.returncode}: {(proc.stderr or '')[:400]}"
        )
    return json.loads(proc.stdout)


# ── 摘要 ────────────────────────────────────────────────────────────────────

def build_summary(parsed: dict[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    chart = facts.get("chart", {})
    cycles = chart.get("cycles") or {}
    relations = facts.get("relations", {})
    strength = facts.get("strength", {})
    limitations = facts.get("input_limitations") or {}

    qiyun = cycles.get("qiyun") or []
    precise = next((q for q in qiyun if q.get("method") == "precise"), None)

    return {
        "schema_version": "rf-facts-summary/v1",
        "case_id": parsed["case_id"],
        "chart_id": chart.get("chart_id"),
        "mode": "birth" if parsed["solar"] else "pillars",
        "pillars": [p["ganzhi"] for p in chart.get("pillars", [])],
        "day_master": chart.get("day_master"),
        "gender": chart.get("gender"),
        "profile": chart.get("profile"),
        "qiyun_precise": precise,
        "dayun": [
            {"index": d.get("index"), "ganzhi": d.get("ganzhi"),
             "start_year": d.get("start_year"), "end_year": d.get("end_year")}
            for d in (cycles.get("dayun") or [])
        ],
        "dayun_declared_in_input": parsed["dayun_declared"],
        "edge_count": len(relations.get("edges") or []),
        "muku_addrs": [m.get("addr") for m in (relations.get("muku") or [])],
        "kongwang": chart.get("kongwang"),
        "siling": (strength.get("day_master") or {}).get("siling"),
        "tiaohou_listed_stems": (strength.get("climate") or {}).get(
            "tiaohou_lookup", {}
        ).get("listed_stems"),
        "structure_ids": [s.get("structure_id") for s in (facts.get("structures") or [])],
        "shensha_names": [h.get("name") for h in (facts.get("shensha") or {}).get("hits", [])],
        "input_limitations": limitations,
        "boundary_warnings": chart.get("boundary_warnings"),
    }


# ── 主流程 ──────────────────────────────────────────────────────────────────

def iter_case_dirs(cases_root: Path) -> list[Path]:
    return sorted(
        p for p in cases_root.glob("C-2026-RF*-*")
        if p.is_dir() and (p / "input.md").exists()
    )


def hydrate_case(case_dir: Path, *, force: bool = False, timeout: int = 120) -> dict[str, Any]:
    facts_dir = case_dir / "facts"
    all_json = facts_dir / "all.json"
    if all_json.exists() and not force:
        return {"case": case_dir.name, "status": "skipped_exists"}

    try:
        parsed = parse_input(case_dir / "input.md")
    except (ValueError, OSError) as exc:
        return {"case": case_dir.name, "status": "skipped_parse", "error": str(exc)}

    try:
        facts = run_engine_cli(parsed, timeout=timeout)
    except (subprocess.TimeoutExpired, RuntimeError, json.JSONDecodeError) as exc:
        # 公历口径失败（常见于残缺时间串，如 "1990-02-06 11?5"）→
        # 回退四柱口径。命主自报四柱仍可用，代价是无人元司令与起运年份，
        # 由 input_limitations 如实标注，不猜、不补。
        if parsed["solar"]:
            fallback = dict(parsed, solar="")
            try:
                facts = run_engine_cli(fallback, timeout=timeout)
                summary = build_summary(fallback, facts)
                summary["fallback_from_birth"] = parsed["solar"]
                summary["fallback_reason"] = str(exc)[:200]
                facts_dir.mkdir(parents=True, exist_ok=True)
                all_json.write_text(
                    json.dumps(facts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
                (facts_dir / "facts_summary.json").write_text(
                    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
                err = facts_dir / "error.txt"
                if err.exists():
                    err.unlink()
                return {
                    "case": case_dir.name,
                    "status": "ok",
                    "mode": "pillars(fallback)",
                    "chart_id": summary["chart_id"],
                    "pillars": summary["pillars"],
                    "day_master": summary["day_master"],
                    "edge_count": summary["edge_count"],
                    "input_limitations": sorted(
                        (summary["input_limitations"] or {}).get("unavailable", {}).keys()
                    ),
                }
            except (subprocess.TimeoutExpired, RuntimeError, json.JSONDecodeError) as exc2:
                exc = exc2
        if not force:
            facts_dir.mkdir(parents=True, exist_ok=True)
            (facts_dir / "error.txt").write_text(str(exc) + "\n", encoding="utf-8")
        return {"case": case_dir.name, "status": "error", "error": str(exc)}

    summary = build_summary(parsed, facts)
    facts_dir.mkdir(parents=True, exist_ok=True)
    all_json.write_text(
        json.dumps(facts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (facts_dir / "facts_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    err = facts_dir / "error.txt"
    if err.exists():
        err.unlink()

    return {
        "case": case_dir.name,
        "status": "ok",
        "mode": summary["mode"],
        "chart_id": summary["chart_id"],
        "pillars": summary["pillars"],
        "day_master": summary["day_master"],
        "edge_count": summary["edge_count"],
        "input_limitations": sorted((summary["input_limitations"] or {}).get("unavailable", {}).keys()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases-root", type=Path, default=DEFAULT_CASES_ROOT)
    parser.add_argument("--limit", type=int, default=0, help="0 = 全部")
    parser.add_argument("--force", action="store_true", help="重跑已有 facts")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    dirs = iter_case_dirs(args.cases_root)
    if args.limit:
        dirs = dirs[: args.limit]

    if args.dry_run:
        done = sum(
            1 for d in dirs if (d / "facts" / "all.json").exists()
        )
        print(f"案例目录：{len(dirs)}  已有 facts：{done}  待跑：{len(dirs) - done}")
        return 0

    ok = skipped = err = 0
    for i, case_dir in enumerate(dirs, 1):
        r = hydrate_case(case_dir, force=args.force, timeout=args.timeout)
        st = r["status"]
        if st == "ok":
            ok += 1
            lim = r.get("input_limitations") or []
            lim_tag = f" [pillar-only: {','.join(lim)}]" if lim else ""
            print(f"[{i}/{len(dirs)}] OK   {r['case']}  {r['mode']}  "
                  f"{''.join(r['pillars'])}  edges={r['edge_count']}{lim_tag}")
        elif st == "skipped_exists":
            skipped += 1
        else:
            err += 1
            print(f"[{i}/{len(dirs)}] {st.upper()}  {r['case']}  {r.get('error', '')[:120]}",
                  file=sys.stderr)

    print()
    print(f"完成：ok={ok}  skipped={skipped}  error={err}  共={len(dirs)}")
    return 0 if err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
