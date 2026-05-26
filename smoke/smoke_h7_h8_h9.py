#!/usr/bin/env python3
"""v1.4 H7+H8+H9 smoke

H7 · quantifiable=False 不计分
H8 · domain_restriction 跳过域不匹配
H9 · event_type_hypotheses round-trip + 注入逻辑

沙箱约束：用 ruamel.yaml 做 PyYAML shim（参考 smoke/run_ingest_c015.py）
"""
import sys, types, io, json
from ruamel.yaml import YAML as _YAML

# ── PyYAML shim via ruamel.yaml ─────────────────────────
_ry = _YAML()
_ry.preserve_quotes = True
fake_yaml = types.ModuleType("yaml")

def _safe_load(stream):
    if isinstance(stream, (str, bytes)):
        stream = io.StringIO(stream) if isinstance(stream, str) else io.BytesIO(stream)
    result = _ry.load(stream)
    def _conv(o):
        if o is None: return o
        if isinstance(o, dict): return {k: _conv(v) for k, v in o.items()}
        if isinstance(o, list): return [_conv(v) for v in o]
        return o
    return _conv(result)

def _safe_dump(data, stream=None, **kw):
    buf = io.StringIO()
    _r = _YAML(); _r.default_flow_style = False; _r.allow_unicode = True; _r.width = 4096
    _r.dump(data, buf)
    text = buf.getvalue()
    if stream:
        stream.write(text); return None
    return text

fake_yaml.safe_load = _safe_load
fake_yaml.safe_dump = _safe_dump
fake_yaml.load = lambda s, Loader=None: _safe_load(s)
fake_yaml.dump = lambda d, stream=None, **kw: _safe_dump(d, stream=stream)
fake_yaml.YAMLError = Exception
class _L: pass
fake_yaml.SafeLoader = _L
fake_yaml.FullLoader = _L
fake_yaml.Dumper = _L
sys.modules["yaml"] = fake_yaml

sys.path.insert(0, "/projects/sandbox/mangpai-fusion")

PASS = []
FAIL = []

def check(name, cond, msg=""):
    if cond:
        PASS.append(name)
        print(f"  PASS  {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL  {name}  {msg}")


# ============================================================
# H7 · quantifiable=False 不计分
# ============================================================
print("=== H7 quantifiable=False 不计分 ===")

import tools.rule_lifecycle as rl
import tools.feedback_loop as fl
from tools.feedback_loop import _apply_rule_verdicts, VerdictContext
from tools.rule_lifecycle import LifecycleConfig

cfg = LifecycleConfig.from_yaml()

# 1) M3-R-003 已在 yaml 中写入 quantifiable=false → load 出来字段对
r3 = rl.load_rule("M3-R-003")
check("T1_M3-R-003_yaml_quantifiable=False", r3.quantifiable is False,
      f"got={r3.quantifiable}")

# 2) M3-R-031 已写入 domain_restriction=["应期"]
r31 = rl.load_rule("M3-R-031")
check("T1_M3-R-031_yaml_domain_restriction", r31.domain_restriction == ["应期"],
      f"got={r31.domain_restriction}")

# 3) 其他规律保持默认值
r5 = rl.load_rule("M3-R-005")
check("T1_M3-R-005_默认quantifiable=True", r5.quantifiable is True)
check("T1_M3-R-005_默认domain_restriction空", r5.domain_restriction == [])

# 4) ingest 跳过逻辑：M3-R-003 verdict miss → 跳过整条
verdicts_h7 = {"M3-R-003": ("miss", VerdictContext(section="任派心法", domain="婚姻"))}
diff_h7 = _apply_rule_verdicts("H7-TEST", verdicts_h7, cfg=cfg, today="2026-05-26", dry_run=True)
check("T2_M3-R-003跳过_无rule_update", len(diff_h7.rule_updates) == 0,
      f"got={len(diff_h7.rule_updates)}")
check("T2_M3-R-003跳过_有V1_note",
      any("v1.4-V1" in n for n in diff_h7.notes),
      f"notes={diff_h7.notes}")

# 5) M3-R-003 状态 hits/misses 不变（dry_run + 跳过双重保险）
r3_check = rl.load_rule("M3-R-003")
check("T2_M3-R-003_hits_未变", r3_check.hits == r3.hits, f"{r3.hits}→{r3_check.hits}")
check("T2_M3-R-003_misses_未变", r3_check.misses == r3.misses, f"{r3.misses}→{r3_check.misses}")


# ============================================================
# H8 · domain_restriction 跳过域不匹配
# ============================================================
print("\n=== H8 domain_restriction 跳过 ===")

# 6) M3-R-031 在"婚姻"域 → 跳过
verdicts_h8a = {"M3-R-031": ("miss", VerdictContext(section="任派应期", domain="婚姻"))}
diff_h8a = _apply_rule_verdicts("H8-TEST-A", verdicts_h8a, cfg=cfg, today="2026-05-26", dry_run=True)
check("T3_婚姻域跳过_无rule_update", len(diff_h8a.rule_updates) == 0,
      f"got={len(diff_h8a.rule_updates)}")
check("T3_婚姻域跳过_有V2_note",
      any("v1.4-V2" in n for n in diff_h8a.notes),
      f"notes={diff_h8a.notes}")

# 7) M3-R-031 在"应期"域 → 正常计 hit
verdicts_h8b = {"M3-R-031": ("hit", VerdictContext(section="任派应期", domain="应期"))}
diff_h8b = _apply_rule_verdicts("H8-TEST-B", verdicts_h8b, cfg=cfg, today="2026-05-26", dry_run=True)
check("T4_应期域计hit", len(diff_h8b.rule_updates) == 1,
      f"got={len(diff_h8b.rule_updates)}")
if diff_h8b.rule_updates:
    u = diff_h8b.rule_updates[0]
    check("T4_应期域verdict=hit", u.verdict == "hit", f"got={u.verdict}")
    check("T4_应期域hits增加", u.hits_after == u.hits_before + 1,
          f"{u.hits_before}→{u.hits_after}")

# 8) M3-R-031 在空域 → 兜底不强制（计 hit）
verdicts_h8c = {"M3-R-031": ("hit", VerdictContext(section="", domain=""))}
diff_h8c = _apply_rule_verdicts("H8-TEST-C", verdicts_h8c, cfg=cfg, today="2026-05-26", dry_run=True)
check("T5_空域兜底不强制", len(diff_h8c.rule_updates) == 1,
      f"got={len(diff_h8c.rule_updates)}")


# ============================================================
# H9 · event_type_hypotheses round-trip + 注入逻辑
# ============================================================
print("\n=== H9 event_type_hypotheses ===")

from engine.yingqi.types import GateResult, LayerCheck, TriggerEvent
from engine.energy.types import Confidence
from engine.yingqi.gate import _infer_event_type_hypotheses
from engine.picture.types import PictureFindings

# 9) 默认空 list（向后兼容）
gr_default = GateResult(
    year=2010, candidate_event="财源", domain="财运",
    layer1=LayerCheck(layer="L1_原局有", passed=True),
    layer2=LayerCheck(layer="L2_大运到位", passed=True),
    layer3=LayerCheck(layer="L3_流年引爆", passed=True),
    passed_layers=3,
)
check("T6_默认event_type_hypotheses空", gr_default.event_type_hypotheses == [],
      f"got={gr_default.event_type_hypotheses}")

# 10) round-trip 一致
gr_filled = GateResult(
    year=2010, candidate_event="财源", domain="财运",
    layer1=LayerCheck(layer="L1_原局有", passed=True),
    layer2=LayerCheck(layer="L2_大运到位", passed=True),
    layer3=LayerCheck(layer="L3_流年引爆", passed=True),
    passed_layers=3,
    event_type_hypotheses=["职级升迁", "财源/置业"],
)
gr_back = GateResult.from_json(gr_filled.to_json())
check("T7_round_trip_一致",
      gr_back.event_type_hypotheses == ["职级升迁", "财源/置业"],
      f"got={gr_back.event_type_hypotheses}")
check("T7_to_dict_一致", gr_filled.to_dict() == gr_back.to_dict())
check("T7_hash_一致", gr_filled.hash() == gr_back.hash())

# 11) 旧 JSON（无字段）反序列化 → 默认空
old_json = {
    "year": 2005, "candidate_event": "结婚", "domain": "婚姻",
    "layer1": {"layer": "L1_原局有", "passed": True, "evidence_chars": [], "rationale": ""},
    "layer2": {"layer": "L2_大运到位", "passed": True, "evidence_chars": [], "rationale": ""},
    "layer3": {"layer": "L3_流年引爆", "passed": True, "evidence_chars": [], "rationale": ""},
    "passed_layers": 3, "triggers": [], "primary_trigger": None, "door": None,
    "confidence": None,
    # 故意省略 event_type_hypotheses
}
gr_legacy = GateResult.from_json(json.dumps(old_json))
check("T8_legacy_json_默认空", gr_legacy.event_type_hypotheses == [],
      f"got={gr_legacy.event_type_hypotheses}")

# 12) _infer_event_type_hypotheses 注入逻辑
def make_picture(pointers):
    return PictureFindings(industry_pointers=pointers)

# 12.1 体制内 + 财源事件 → 注入
r1 = _infer_event_type_hypotheses("财运", "财源/置业", make_picture(["公门"]))
check("T9_体制内财源_注入双解", r1 == ["职级升迁", "财源/置业"], f"got={r1}")

# 12.2 体制内 + 已是升迁 → 不注入
r2 = _infer_event_type_hypotheses("事业", "升迁副处", make_picture(["公门"]))
check("T9_已是升迁_不注入", r2 == [], f"got={r2}")

# 12.3 非体制 → 不注入
r3 = _infer_event_type_hypotheses("财运", "财源/置业",
                                   make_picture(["技术/制造"]))
check("T9_非体制_不注入", r3 == [], f"got={r3}")

# 12.4 婚姻域 → 不注入
r4 = _infer_event_type_hypotheses("婚姻", "结婚", make_picture(["公门"]))
check("T9_婚姻域_不注入", r4 == [], f"got={r4}")

# 12.5 空 industry_pointers → 不注入
r5 = _infer_event_type_hypotheses("财运", "财源", make_picture([]))
check("T9_空pointers_不注入", r5 == [], f"got={r5}")

# 12.6 事业单位 + 财动 → 注入
r6 = _infer_event_type_hypotheses("财运", "财动婚动", make_picture(["事业单位"]))
check("T9_事业单位财动_注入", r6 == ["职级升迁", "财源/置业"], f"got={r6}")


# ============================================================
print(f"\nv1.4 H7+H8+H9: {len(PASS)}/{len(PASS)+len(FAIL)} PASS  "
      f"{'OK' if not FAIL else 'FAIL: '+str(FAIL)}")
sys.exit(0 if not FAIL else 1)
