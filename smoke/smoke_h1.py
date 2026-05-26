#!/usr/bin/env python3
"""H1 · statement_id 稳定性 stdlib smoke（无 pytest/PyYAML）"""
import sys, types, re

# ── 桩 yaml ───────────────────────────────────────────────
fake_yaml = types.ModuleType("yaml")
fake_yaml.safe_load = lambda s: {}
fake_yaml.safe_dump = lambda d, **kw: ""
fake_yaml.load = lambda s, Loader=None: {}
fake_yaml.YAMLError = Exception
class _Loader: pass
fake_yaml.SafeLoader = _Loader
sys.modules["yaml"] = fake_yaml

sys.path.insert(0, "/projects/sandbox/mangpai-fusion")

from tools.render_report import _compute_statement_id

PASS = []
FAIL = []

def check(name, cond, msg=""):
    if cond:
        PASS.append(name)
        print(f"  PASS  {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL  {name}  {msg}")

print("=== H1 statement_id 稳定性 ===")

# T1: 5 次重跑 sid 集合一致
def _sid():
    return _compute_statement_id("C-2026-001-X", ["M1-D-001", "M2-Y-068"])
base = _sid()
all_same = all(_sid() == base for _ in range(4))
check("T1_5次重跑一致", all_same)

# T2: 格式 S-NNN-xxxxxx
sid = _compute_statement_id("C-2026-099-甲申", ["M1-D-001"])
pat = re.compile(r"^S-\w{1,8}-[a-f0-9]{6}$")
check("T2_格式正确", bool(pat.match(sid)), f"got={sid}")

# T3: 20 个不同 case → 20 个不同 sid
sids_20 = {_compute_statement_id(f"C-2026-{i:03d}-X", ["M1-D-001", "M2-Y-068"]) for i in range(20)}
check("T3_不同case不碰撞", len(sids_20) == 20, f"unique={len(sids_20)}")

# T4: 排序无关
a = _compute_statement_id("C-2026-001-X", ["A", "B", "C"])
b = _compute_statement_id("C-2026-001-X", ["C", "A", "B"])
c = _compute_statement_id("C-2026-001-X", ["B", "C", "A", "A"])
check("T4_排序去重不影响sid", a == b == c, f"a={a} b={b} c={c}")

# T5: 集合变化 → sid 变
s1 = _compute_statement_id("C-2026-001-X", ["A", "B"])
s2 = _compute_statement_id("C-2026-001-X", ["A", "B", "C"])
s3 = _compute_statement_id("C-2026-001-X", ["A"])
check("T5_集合变化sid变", s1 != s2 and s2 != s3 and s1 != s3)

print(f"\nH1: {len(PASS)}/5 PASS  {'OK' if not FAIL else 'FAIL: '+str(FAIL)}")
sys.exit(0 if not FAIL else 1)
