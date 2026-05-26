#!/usr/bin/env python3
"""在无 PyYAML 沙箱中运行 feedback_ingest C-2026-015

利用已安装的 ruamel.yaml 构建兼容 PyYAML API 的 shim。
"""
import sys, types, pathlib, json, io

# ── 用 ruamel.yaml 构建 PyYAML 兼容 shim ──────────────────
from ruamel.yaml import YAML as _YAML

_ry = _YAML()
_ry.preserve_quotes = True

fake_yaml = types.ModuleType("yaml")

def _safe_load(stream):
    if isinstance(stream, (str, bytes)):
        stream = io.StringIO(stream) if isinstance(stream, str) else io.BytesIO(stream)
    result = _ry.load(stream)
    return _convert(result)

def _convert(obj):
    """Convert ruamel ordereddict/CommentedSeq to plain dict/list."""
    if obj is None:
        return obj
    if isinstance(obj, dict):
        return {k: _convert(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert(v) for v in obj]
    return obj

def _safe_dump(data, stream=None, **kw):
    buf = io.StringIO()
    _ry_dump = _YAML()
    _ry_dump.default_flow_style = False
    _ry_dump.dump(data, buf)
    text = buf.getvalue()
    if stream:
        stream.write(text)
        return None
    return text

def _load(stream, Loader=None):
    return _safe_load(stream)

def _dump(data, stream=None, **kw):
    return _safe_dump(data, stream=stream)

fake_yaml.safe_load = _safe_load
fake_yaml.safe_dump = _safe_dump
fake_yaml.load = _load
fake_yaml.dump = _dump
fake_yaml.YAMLError = Exception

class _SafeLoader: pass
class _FullLoader: pass
class _Dumper: pass

fake_yaml.SafeLoader = _SafeLoader
fake_yaml.FullLoader = _FullLoader
fake_yaml.Dumper = _Dumper
sys.modules["yaml"] = fake_yaml

# ── 设置路径 ─────────────────────────────────────────────
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

# ── 执行 ingest ──────────────────────────────────────────
from tools.feedback_ingest import ingest

case_id = "C-2026-015-甲寅乙亥丙辰辛卯"
dry_run = "--dry-run" in sys.argv

print(f"[run_ingest_c015] case_id={case_id}  dry_run={dry_run}")
print("=" * 60)

try:
    result = ingest(case_id, dry_run=dry_run)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    print("=" * 60)
    print(f"✅ 完成：feedback_count={result.feedback_count}, rule_count={result.rule_count}")
    print(f"   走启发式路径: {result.skipped_no_index}")
    print(f"   累计完成反馈案: {result.feedback_completed_count}")
    print(f"   迭代序号: {result.iteration_seq}")
    print(f"   本次触发迭代: {result.iteration_triggered}")
    if result.iteration_report_path:
        print(f"   迭代报告: {result.iteration_report_path}")
except Exception as exc:
    print(f"❌ 错误: {exc!r}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
