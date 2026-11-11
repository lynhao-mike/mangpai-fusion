"""紫微数据集查表调度：配置加载 + Node 只读子进程 + 结果校验。

不向数据目录写入任何文件；解压走流式，不在磁盘生成 700 MB 明文。
"""
from __future__ import annotations

import json
import os
import subprocess
import tomllib
from pathlib import Path

from .case_key import CaseKey

ROOT = Path(__file__).resolve().parents[2]
READER = Path(__file__).with_name("ziwei_reader.mjs")
LOCAL_CONFIG = ROOT / "config" / "ziwei.local.toml"

DEFAULTS = {
    "dataset_dir": "",
    "project_dir": "",
    "node_bin": "node",
    "dataset_version": "v4.0-13d",
    "content_version": "ca268829f7a9",
    "release_repo": "Renhuai123/ziwei-doushu",
    "release_tag": "v4.0-13d",
    "license": "CC BY 4.0",
    "attribution": (
        "紫微斗数开源解读数据集 v4.0（674,976 张命盘 × 13 维） / "
        "https://github.com/Renhuai123/ziwei-doushu / 王多鱼AI"
    ),
}

ENV_OVERRIDES = {
    "ZIWEI_ANALYSIS_DIR": "dataset_dir",
    "ZIWEI_PROJECT_DIR": "project_dir",
    "ZIWEI_NODE_BIN": "node_bin",
}


def load_config(path: str | Path | None = None) -> dict:
    """默认 < 本机 config/ziwei.local.toml < 环境变量。"""
    cfg = dict(DEFAULTS)
    p = Path(path) if path else LOCAL_CONFIG
    if p.is_file():
        with p.open("rb") as f:
            section = tomllib.load(f).get("ziwei", {})
        cfg.update({k: v for k, v in section.items() if k in cfg})
    for env, key in ENV_OVERRIDES.items():
        if os.environ.get(env):
            cfg[key] = os.environ[env]
    return cfg


def lookup(
    case_key: CaseKey,
    dims: list[str] | tuple[str, ...] = (),
    config: dict | None = None,
    *,
    timeout: int = 180,
    prefer: str = "plain",
) -> dict:
    """返回查表器原始 payload；失败抛 LookupError。"""
    cfg = dict(config if config is not None else load_config())
    data_dir = str(cfg.get("dataset_dir", "")).strip()
    if not data_dir:
        raise LookupError(
            "未配置 dataset_dir；复制 config/ziwei.local.example.toml 为 "
            "config/ziwei.local.toml，或设置环境变量 ZIWEI_ANALYSIS_DIR"
        )

    cmd = [
        str(cfg.get("node_bin") or "node"),
        str(READER),
        data_dir,
        str(case_key.year),
        case_key.ziwei_key,
        ",".join(dims),
        prefer,
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            timeout=timeout, check=False,
        )
    except FileNotFoundError as e:
        raise LookupError(f"找不到 node 可执行文件：{e}；可设 ZIWEI_NODE_BIN") from e
    except subprocess.TimeoutExpired as e:
        raise LookupError(f"查表超时（{timeout}s）") from e

    out = (proc.stdout or "").strip()
    if not out:
        raise LookupError(f"查表器无输出；stderr={(proc.stderr or '').strip()[:300]}")
    try:
        payload = json.loads(out.splitlines()[-1])
    except json.JSONDecodeError as e:
        raise LookupError(f"查表器输出不是 JSON：{out[:300]}") from e
    if not payload.get("ok"):
        raise LookupError(str(payload.get("error", "未知查表错误")))
    return payload
