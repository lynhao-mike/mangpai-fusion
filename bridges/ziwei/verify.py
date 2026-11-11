"""阶段 1–4 黄金样本验收（只依赖标准库 + 本机 node；L1 另需紫微项目已装 tsx）。

    python bridges/ziwei/verify.py              # 无数据 / 无紫微项目时跳过对应断言
    python bridges/ziwei/verify.py --require-data
    python bridges/ziwei/verify.py --require-l1

退出码 0 = 全部通过，1 = 有失败项。对应 AGENTS.md §5「以退出码表达验收结果」。
不修改测试或断言使其通过。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridges.ziwei import (  # noqa: E402
    ENVELOPE_VERSION, NOT_USABLE_AS, build_case_key, build_envelope, build_l1_envelope,
    chart_fingerprint, evaluate_assertions, generate_chart, load_config, lookup,
)
from tools.cross_check import build_report, render_markdown  # noqa: E402
from tools.ziwei_appendix import render_appendix  # noqa: E402
from tools.ziwei_fetch import load_manifest, sha256_file  # noqa: E402

BIRTH = "2001-12-31 06:00"
GENDER = "坤"
GOLD_KEY = "2001-12-31-3-female"
GOLD_OFFSET = 710394103
GOLD_LENGTH = 84563
GOLD_CHART_ID = "cf-281c0165ae85687dafe7"
READER = ROOT / "bridges" / "ziwei" / "ziwei_reader.mjs"

_failures: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    mark = "PASS" if cond else "FAIL"
    print(f"[{mark}] {name}" + (f" :: {detail}" if detail else ""))
    if not cond:
        _failures.append(name)


def _run(cmd: list[str], *, timeout: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=str(ROOT), capture_output=True, text=True,
        encoding="utf-8", timeout=timeout, check=False,
    )


def main() -> int:
    ck = build_case_key(BIRTH, GENDER)
    check("case_key 映射", ck.ziwei_key == GOLD_KEY and ck.hour_index == 3 and ck.branch == "卯",
          f"{ck.ziwei_key} / {ck.branch}时")
    check("口径警告恒在", "bazi_jieqi_vs_ziwei_solar_date" in ck.alignment_warnings)
    late = build_case_key("2001-12-31 23:30", GENDER)
    check("晚子时不静默换算", late.ziwei_key.startswith("2001-12-31-0-")
          and "late_zi_hour_date_policy_unverified" in late.alignment_warnings,
          late.ziwei_key)

    cfg = load_config()
    data_dir = Path(str(cfg.get("dataset_dir", "")).strip()) if cfg.get("dataset_dir") else None
    project_dir = Path(str(cfg.get("project_dir", "")).strip()) if cfg.get("project_dir") else None
    has_data = bool(
        data_dir
        and (data_dir / "year-2001.idx.json").is_file()
        and ((data_dir / "year-2001.jsonl").is_file() or (data_dir / "year-2001.jsonl.zst").is_file())
    )
    has_l1 = bool(
        project_dir
        and (project_dir / "lib" / "ziwei" / "algorithm.ts").is_file()
        and (project_dir / "node_modules" / "tsx").is_dir()
    )
    facts: dict | None = None
    l2_env: dict | None = None

    if "--require-data" in sys.argv and not has_data:
        check("要求数据存在", False, "缺 year-2001 分片；运行 tools.ziwei_fetch --year 2001 --download")
    if "--require-l1" in sys.argv and not has_l1:
        check("要求 L1 环境", False, "缺紫微项目或 tsx；L1 需 npm install 后的 ziwei-doushu")

    # ---------------- 阶段 1–2 ----------------
    if not has_data:
        print("[SKIP] 阶段 1–2 数据断言（本机无 year-2001 分片）")
    else:
        payload = lookup(ck, ["career", "wealth"], cfg)
        l2_env = build_envelope(ck, payload, config=cfg)
        loc = l2_env["locator"]
        check("分片定位", loc["offset"] == GOLD_OFFSET and loc["length"] == GOLD_LENGTH,
              f"offset={loc['offset']} length={loc['length']}")
        check("命宫空宫", l2_env["ziwei_dataset_fields"]["minggong_main_star_ms"] is None)
        check("13 维齐备", len(l2_env["dimensions_available"]) == 13,
              ",".join(l2_env["dimensions_available"]))
        check("career 字数", l2_env["dimension_chars"].get("career") == 2271,
              str(l2_env["dimension_chars"].get("career")))
        check("仅取请求维度正文", sorted(c["dim"] for c in l2_env["claims"]) == ["career", "wealth"])
        check("信封契约", l2_env["envelope"] == ENVELOPE_VERSION
              and set(NOT_USABLE_AS).issubset(l2_env["not_usable_as"])
              and l2_env["source_kind"] == "interpretation_text"
              and l2_env["verifiable_by"].startswith("ziwei-doushu"))
        check("许可署名", "王多鱼AI" in l2_env["dataset"]["attribution"]
              and l2_env["dataset"]["license"] == "CC BY 4.0")

        proc = _run([sys.executable, "-m", "engine.cli", "chart", "--birth", BIRTH,
                     "--gender", GENDER, "--json"])
        try:
            facts = json.loads((proc.stdout or "").strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            facts = {}
        check("engine 同参 chart_id", facts.get("chart_id") == GOLD_CHART_ID,
              str(facts.get("chart_id")))
        check("engine 输入对齐",
              str(facts.get("input", {}).get("solar_datetime", "")).startswith("2001-12-31 06:00")
              and facts.get("input", {}).get("true_solar_corrected") is None)

        rep = build_report(facts, l2_env)
        check("三态对账骨架", len(rep["rows"]) == 13
              and rep["counts"]["unverifiable"] == 13
              and set(NOT_USABLE_AS).issubset(rep["ziwei"]["not_usable_as"]))
        md = render_markdown(rep)
        check("对账表含三态与边界", "收敛 / 分歧 / 不核验" in md
              and "不构成八字引擎事实" in md)

        try:
            streamed = lookup(ck, ["career"], cfg, prefer="zst")
        except LookupError as e:
            check("流式解压路径一致", False, str(e))
        else:
            check("流式解压路径一致",
                  streamed["locator"]["offset"] == GOLD_OFFSET
                  and streamed["locator"]["shard"].endswith(".zst")
                  and streamed["record"]["c"]["career"] == payload["record"]["c"]["career"],
                  streamed["locator"]["shard"])

        verdicts = {
            "career": {"status": "converged", "reason": "两套都指向大机构制度岗，方向收敛"},
            "wealth": {"status": "divergent", "reason": "紫微判中年置产，八字判 2033 后留存，站队引擎事实"},
        }
        rep2 = build_report(
            facts, l2_env,
            claims=[{"topic": "career", "text": "去有职称序列的平台",
                     "source_ref": "ZP-PROD-20260622-034", "address": "H.s"}],
            verdicts=verdicts,
        )
        check("三态可落定", rep2["counts"]["converged"] == 1
              and rep2["counts"]["divergent"] == 1
              and rep2["counts"]["unverifiable"] == 11)
        career_row = next(r for r in rep2["rows"] if r["topic"] == "career")
        check("八字侧结论带出处", career_row["bazi_source_ref"] == "ZP-PROD-20260622-034")
        try:
            build_report(facts, l2_env, verdicts={"career": {"status": "converged", "reason": "各有道理"}})
            check("骑墙措辞被拒", False, "未抛 ValueError")
        except ValueError:
            check("骑墙措辞被拒", True)

    # ---------------- 阶段 3：L1 与附录 ----------------
    l1_env: dict | None = None
    if not has_l1:
        print("[SKIP] 阶段 3 L1 断言（缺紫微项目 tsx 环境）")
    else:
        try:
            res = generate_chart(ck, cfg)
        except LookupError as e:
            check("L1 排盘", False, str(e))
        else:
            chart = res["chart"]
            fp1 = chart_fingerprint(chart)["sha256"]
            check("L1 排盘与指纹", len(chart.get("palaces", [])) == 12 and len(fp1) == 64, fp1[:16])
            assertions = evaluate_assertions(chart)
            check("L1 盘面断言 14 条全成立",
                  len(assertions) == 14 and all(a["matched"] is True for a in assertions),
                  f"成立 {sum(1 for a in assertions if a['matched'] is True)}/{len(assertions)}")
            check("L1 命宫空宫且落酉",
                  chart.get("mingGongBranch") == 9
                  and not any(s.get("type") == "major"
                              for p in chart["palaces"] if p.get("isMingGong")
                              for s in p.get("stars", [])))
            l1_env = build_l1_envelope(ck, chart, assertions, config=cfg, generator=res.get("generator"))
            check("L1 信封契约", l1_env["level"] == "L1"
                  and l1_env["source_kind"] == "chart_fact"
                  and l1_env["dataset"] is None
                  and set(NOT_USABLE_AS).issubset(l1_env["not_usable_as"])
                  and l1_env["locator"]["chart_sha256"] == fp1)
            try:
                fp2 = chart_fingerprint(generate_chart(ck, cfg)["chart"])["sha256"]
                check("L1 指纹可复现", fp1 == fp2, fp2[:16])
            except LookupError as e:
                check("L1 指纹可复现", False, str(e))
            try:
                build_report(facts or {}, l1_env)
                check("对账拒绝 L1 信封", False, "未抛 ValueError")
            except ValueError:
                check("对账拒绝 L1 信封", True)
            proc = _run([sys.executable, "-m", "tools.ziwei_chart", "--birth", BIRTH,
                         "--gender", GENDER, "--json"])
            try:
                # ziwei_chart 输出 indent=2 的多行 JSON，不能按「最后一行」解析
                cli_env = json.loads((proc.stdout or "").strip())
            except (json.JSONDecodeError, IndexError):
                cli_env = {}
            check("L1 CLI 端到端", proc.returncode == 0 and cli_env.get("level") == "L1"
                  and cli_env.get("assertion_counts", {}).get("matched") == 14)

    # 附录：L1 / L2 / cross 三份都给齐时验完整形态，缺件时验降级形态
    cross = None
    if l2_env is not None and facts is not None:
        cross = build_report(facts, l2_env, verdicts={
            "career": {"status": "converged", "reason": "两套都指向大机构制度岗，方向收敛"},
            "wealth": {"status": "divergent", "reason": "置产年份两套不同，站队引擎 2033 甲辰运"},
        })
    if l1_env is not None or l2_env is not None or cross is not None:
        try:
            md = render_appendix(l1_env, l2_env, cross)
            expected_sha = (l1_env or {}).get("locator", {}).get("chart_sha256", "")[:12]
            check("附录边界与定位",
                  "不是主报告" in md and "engine_fact" in md and "theory_source_ref" in md
                  and (not expected_sha or expected_sha in md)
                  and "## 四、三级置信与依据索引" in md)
            if l1_env is not None:
                check("附录 L1 断言表带定位", md.count("成立 |") >= 14 and "盘面核验" in md)
            if cross is not None:
                check("附录 L2 对账带 locator", "收敛 1" in md and "offset" in md)
        except (ValueError, KeyError, TypeError) as e:
            check("附录边界与定位", False, str(e))

        try:
            bad = json.loads(json.dumps(cross)) if cross else {
                "report": "cross-check/v1", "rows": [
                    {"topic": "career", "status": "converged", "verdict_reason": "各有道理"}
                ], "counts": {}, "alignment_warnings": [], "case_key": {},
            }
            if cross:
                bad["rows"][0]["verdict_reason"] = "各有道理"
            render_appendix(l1_env, l2_env, bad)
            check("附录拒绝骑墙", False, "未抛 ValueError")
        except ValueError:
            check("附录拒绝骑墙", True)

    # ---------------- 阶段 4：清单与懒加载 ----------------
    try:
        man = load_manifest()
        shards = man["shards"]
        check("清单结构", man["manifest"] == "ziwei-dataset-manifest/v1"
              and len(shards) == 77
              and man["years"] == {"start": 1950, "end": 2026, "count": 77}
              and man["checksum"] == "sha256")
        check("清单体积适合入库", (ROOT / "config" / "dataset-manifest.json").stat().st_size < 100_000,
              f"{(ROOT / 'config' / 'dataset-manifest.json').stat().st_size} bytes")
        entry = next(s for s in shards if s["year"] == 2001)
        check("清单 2001 条目", entry["bytes"] == 2054526 and len(entry["sha256"] or "") == 64
              and entry["index_keys"] is not None,
              f"bytes={entry['bytes']} keys={entry['index_keys']}")
        if has_data:
            check("清单哈希与本机一致",
                  sha256_file(data_dir / "year-2001.jsonl.zst") == entry["sha256"])
        ign = subprocess.run(
            ["git", "check-ignore", "-q", "config/dataset-manifest.json"],
            cwd=str(ROOT), capture_output=True, check=False,
        )
        check("清单可入库（未被忽略）", ign.returncode != 0)
    except (OSError, ValueError, KeyError, StopIteration) as e:
        check("清单结构", False, str(e))

    proc = _run([sys.executable, "-m", "tools.ziwei_fetch", "--year", "2001", "--verify-only"])
    check("懒加载 verify-only", proc.returncode == 0 and "ALL OK" in (proc.stdout or ""),
          (proc.stdout or "").strip().splitlines()[-1] if proc.stdout else "")
    dry = _run([sys.executable, "-m", "tools.ziwei_fetch", "--year", "2001"])
    check("懒加载 dry-run 不联网", dry.returncode == 0 and "dry-run" in (dry.stdout or ""))

    # 流式建索引：合成小样本，明文 / zst 两条路径都要给出同样的 [offset, length]
    td = Path(tempfile.mkdtemp(prefix="ziwei-verify-"))
    try:
        f = td / "year-9999.jsonl"
        line1 = '{"k":"1999-01-01-3-female","c":{"career":"x"}}'
        line2 = '{"k":"1999-01-01-4-male","c":{"career":"y"}}'
        # 显式 LF：Windows 默认会把 \n 写成 \r\n，索引按磁盘字节计长会多 1
        with f.open("w", encoding="utf-8", newline="") as fh:
            fh.write(line1 + "\n" + line2 + "\n")
        expected = {"1999-01-01-3-female": [0, len(line1.encode())],
                    "1999-01-01-4-male": [len(line1.encode()) + 1, len(line2.encode())]}
        p1 = _run(["node", str(READER), str(td), "9999", "--build-index"])
        idx1 = json.loads((p1.stdout or "").strip().splitlines()[-1]).get("index")
        js = (
            "const fs=require('fs'),z=require('zlib');const p=" + json.dumps(str(f)) + ";"
            "fs.writeFileSync(p+'.zst',z.zstdCompressSync(fs.readFileSync(p)));fs.unlinkSync(p);"
        )
        pack = _run(["node", "-e", js])
        p2 = _run(["node", str(READER), str(td), "9999", "--build-index"])
        idx2 = json.loads((p2.stdout or "").strip().splitlines()[-1]).get("index")
        check("流式建索引两条路径一致",
              pack.returncode == 0 and p1.returncode == 0 and p2.returncode == 0
              and idx1 == expected and idx2 == expected,
              f"rc=({pack.returncode},{p1.returncode},{p2.returncode}) "
              f"plain={json.dumps(idx1, ensure_ascii=False)} "
              f"zst={json.dumps(idx2, ensure_ascii=False)} "
              f"expected={json.dumps(expected, ensure_ascii=False)} "
              f"pack_err={(pack.stderr or '')[:120]}")
    except (OSError, json.JSONDecodeError, IndexError) as e:
        check("流式建索引两条路径一致", False, str(e))
    finally:
        shutil.rmtree(td, ignore_errors=True)

    if _failures:
        print(f"\nFAILED: {len(_failures)} 项 -> {', '.join(_failures)}")
        return 1
    print("\nALL PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
