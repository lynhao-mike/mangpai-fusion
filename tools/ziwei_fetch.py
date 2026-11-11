"""阶段 4：紫微数据集清单与按年懒加载。

    python -m tools.ziwei_fetch --year 2001                 # 只打印计划（默认 dry-run，不联网不写盘）
    python -m tools.ziwei_fetch --year 2001 --verify-only   # 校验本机分片 sha256
    python -m tools.ziwei_fetch --year 2001 --download      # 显式下载缺失分片并按需建索引
    python -m tools.ziwei_fetch --rebuild-manifest          # 从本机数据重算 config/dataset-manifest.json

设计要点：
- 仓库只留 config/dataset-manifest.json（77 年 × URL / 字节数 / sha256），5.7 GB 数据留本地；
- 已存在且校验和匹配的分片一律跳过，绝不覆盖本机数据；
- 缺 idx 时用 Node 22 流式解压 zst 直接产出索引 JSON，不生成 700 MB 明文；
- 下载走 GitHub Release + 两个镜像回退，写入临时文件、校验通过后才原子替换。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import urllib.request
from urllib.parse import urlparse
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridges.ziwei import load_config  # noqa: E402

MANIFEST_PATH = ROOT / "config" / "dataset-manifest.json"
READER = ROOT / "bridges" / "ziwei" / "ziwei_reader.mjs"
MANIFEST_VERSION = "ziwei-dataset-manifest/v1"
YEAR_START, YEAR_END = 1950, 2026
MIRRORS = ("{}", "https://ghproxy.net/{}", "https://gh-proxy.com/{}")
RELEASE_URL = (
    "https://github.com/{repo}/releases/download/{tag}/year-{year}.jsonl.zst"
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _index_keys(path: Path) -> int | None:
    try:
        with path.open("r", encoding="utf-8") as f:
            return len(json.load(f))
    except (OSError, json.JSONDecodeError):
        return None


def build_manifest(data_dir: Path, cfg: dict) -> dict:
    """从本机分片重算清单。缺某一年时该条标 missing，不猜测哈希。"""
    shards = []
    for year in range(YEAR_START, YEAR_END + 1):
        zst = data_dir / f"year-{year}.jsonl.zst"
        idx = data_dir / f"year-{year}.idx.json"
        item = {"year": year, "shard": zst.name, "index": idx.name}
        item["bytes"] = zst.stat().st_size if zst.is_file() else None
        item["sha256"] = sha256_file(zst) if zst.is_file() else None
        item["index_bytes"] = idx.stat().st_size if idx.is_file() else None
        item["index_sha256"] = sha256_file(idx) if idx.is_file() else None
        item["index_keys"] = _index_keys(idx) if idx.is_file() else None
        shards.append(item)
    return {
        "manifest": MANIFEST_VERSION,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "dataset": {
            "version": cfg.get("dataset_version"),
            "content_version": cfg.get("content_version"),
            "release_repo": cfg.get("release_repo"),
            "release_tag": cfg.get("release_tag"),
            "license": cfg.get("license"),
            "attribution": cfg.get("attribution"),
            "license_note": "解读中引用的倪海厦《天纪》原话不在 CC BY 4.0 授权内，不入库",
        },
        "release_url_template": RELEASE_URL,
        "mirrors": list(MIRRORS),
        "checksum": "sha256",
        "index_policy": {
            "generated_locally": True,
            "builder": "bridges/ziwei/ziwei_reader.mjs --build-index",
            "note": "Release 只提供 .jsonl.zst；idx 由流式解压逐行扫描生成，不落 700 MB 明文",
        },
        "years": {"start": YEAR_START, "end": YEAR_END, "count": len(shards)},
        "total_bytes": sum(s["bytes"] or 0 for s in shards),
        "shards": shards,
    }


def load_manifest(path: Path | None = None) -> dict:
    p = path or MANIFEST_PATH
    if not p.is_file():
        raise FileNotFoundError(
            f"缺清单 {p}；运行 python -m tools.ziwei_fetch --rebuild-manifest"
        )
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if data.get("manifest") != MANIFEST_VERSION:
        raise ValueError(f"不是 {MANIFEST_VERSION}：{data.get('manifest')!r}")
    return data


def _shard_map(manifest: dict) -> dict[int, dict]:
    return {s["year"]: s for s in manifest.get("shards", [])}


def plan_year(year: int, data_dir: Path, entry: dict) -> dict:
    zst = data_dir / entry["shard"]
    idx = data_dir / entry["index"]
    zst_ok = zst.is_file() and (
        not entry.get("sha256") or sha256_file(zst) == entry["sha256"]
    )
    idx_ok = idx.is_file()
    actions = []
    if not zst.is_file():
        actions.append("download_shard")
    elif not zst_ok:
        actions.append("sha256_mismatch")
    if not idx_ok:
        actions.append("build_index")
    return {
        "year": year,
        "shard": entry["shard"],
        "shard_present": zst.is_file(),
        "shard_bytes": zst.stat().st_size if zst.is_file() else None,
        "shard_sha256_ok": bool(zst_ok),
        "index_present": idx_ok,
        "actions": actions,
    }


def download_shard(year: int, data_dir: Path, entry: dict, cfg: dict, *, timeout: int = 60) -> str:
    url = RELEASE_URL.format(
        repo=cfg.get("release_repo"), tag=cfg.get("release_tag"), year=year,
    )
    dest = data_dir / entry["shard"]
    tmp = dest.with_suffix(dest.suffix + ".part")
    last_err: Exception | None = None
    for wrap in MIRRORS:
        target = wrap.format(url)
        try:
            req = urllib.request.Request(target, headers={"User-Agent": "mangpai-fusion/ziwei-fetch"})
            with urllib.request.urlopen(req, timeout=timeout) as resp, tmp.open("wb") as f:
                while True:
                    buf = resp.read(1024 * 1024)
                    if not buf:
                        break
                    f.write(buf)
            got = tmp.stat().st_size
            digest = sha256_file(tmp)
            if entry.get("bytes") and got != entry["bytes"]:
                raise ValueError(f"字节数不符：期望 {entry['bytes']}，实得 {got}")
            if entry.get("sha256") and digest != entry["sha256"]:
                raise ValueError(f"sha256 不符：期望 {entry['sha256']}，实得 {digest}")
            tmp.replace(dest)
            return f"downloaded {got} bytes ← {urlparse(target).netloc}"
        except Exception as e:  # noqa: BLE001 — 镜像逐个回退，最后统一报错
            last_err = e
            tmp.unlink(missing_ok=True)
            print(f"  镜像失败 {urlparse(target).netloc}：{e}", file=sys.stderr)
    raise RuntimeError(f"所有下载源均失败（{year}）：{last_err}")


def build_index(year: int, data_dir: Path, cfg: dict, *, timeout: int = 300) -> int:
    cmd = [str(cfg.get("node_bin") or "node"), str(READER), str(data_dir), str(year), "--build-index"]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8",
        timeout=timeout, check=False,
    )
    out = (proc.stdout or "").strip()
    if not out:
        raise RuntimeError(f"建索引无输出：{(proc.stderr or '').strip()[:300]}")
    payload = json.loads(out.splitlines()[-1])
    if not payload.get("ok"):
        raise RuntimeError(str(payload.get("error", "建索引失败")))
    dest = data_dir / f"year-{year}.idx.json"
    dest.write_text(json.dumps(payload["index"], ensure_ascii=False), encoding="utf-8")
    return int(payload.get("count", 0))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="紫微数据集按年懒加载与清单校验")
    ap.add_argument("--year", nargs="*", type=int, default=None, help="年份，可多个；缺省 2001")
    ap.add_argument("--all", action="store_true", help="全部 1950–2026")
    ap.add_argument("--download", action="store_true", help="显式联网下载缺失分片（默认只打印计划）")
    ap.add_argument("--verify-only", action="store_true", help="只校验本机分片 sha256")
    ap.add_argument("--rebuild-manifest", action="store_true", help="从本机数据重算 config/dataset-manifest.json")
    ap.add_argument("--no-index", action="store_true", help="不自动补建缺失 idx")
    ap.add_argument("--config", default=None, help="指定 toml 配置路径")
    ap.add_argument("--timeout", type=int, default=60, help="单次下载超时秒数")
    args = ap.parse_args(argv)

    try:
        cfg = load_config(args.config)
        data_dir = Path(str(cfg.get("dataset_dir", "")).strip())
        if not str(data_dir) or str(data_dir) == ".":
            raise ValueError("未配置 dataset_dir；复制 config/ziwei.local.example.toml 并填写本机路径")

        if args.rebuild_manifest:
            manifest = build_manifest(data_dir, cfg)
            MANIFEST_PATH.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
            )
            present = sum(1 for s in manifest["shards"] if s["sha256"])
            print(f"written: {MANIFEST_PATH}")
            print(f"年份 {manifest['years']['count']} / 本机有分片 {present} / "
                  f"压缩总量 {manifest['total_bytes'] / 1024 ** 2:.1f} MB")
            return 0

        manifest = load_manifest()
        smap = _shard_map(manifest)
        years = (list(range(YEAR_START, YEAR_END + 1)) if args.all
                 else (args.year or [2001]))
        unknown = [y for y in years if y not in smap]
        if unknown:
            raise ValueError(f"清单中没有这些年份：{unknown}")

        plans = [plan_year(y, data_dir, smap[y]) for y in years]
        failed = False
        for p in plans:
            flag = "OK" if p["shard_sha256_ok"] and p["index_present"] else "NEED"
            print(f"[{flag}] {p['year']} {p['shard']} "
                  f"bytes={p['shard_bytes']} sha256={'ok' if p['shard_sha256_ok'] else 'missing/bad'} "
                  f"idx={'yes' if p['index_present'] else 'no'} actions={','.join(p['actions']) or 'none'}")
            if args.verify_only:
                if not p["shard_sha256_ok"]:
                    failed = True
                continue
            if not args.download:
                continue
            if "sha256_mismatch" in p["actions"]:
                print("  已存在分片但校验和不符，拒绝覆盖；若要重下请先手动移除该文件")
                failed = True
                continue
            if "download_shard" in p["actions"]:
                print(f"  {download_shard(p['year'], data_dir, smap[p['year']], cfg, timeout=args.timeout)}")
            if "build_index" in p["actions"] and not args.no_index:
                n = build_index(p["year"], data_dir, cfg)
                print(f"  built index: {n} keys → year-{p['year']}.idx.json")

        if not args.download and not args.verify_only:
            print("\n（dry-run：未联网、未写盘。加 --download 才会下载缺失分片并补建索引）")
        if args.verify_only:
            print("\n校验：" + ("FAILED（有分片缺失或哈希不符）" if failed else "ALL OK"))
        return 1 if failed else 0
    except (ValueError, OSError, RuntimeError, json.JSONDecodeError, KeyError, subprocess.TimeoutExpired) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
