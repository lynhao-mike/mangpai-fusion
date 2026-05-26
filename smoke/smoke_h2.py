#!/usr/bin/env python3
"""H2 · 双版报告差分 stdlib smoke（无 pytest/PyYAML）

核心：client 版 0 反馈位 / master 版 >0 反馈位 / client ★≤3 被过滤
"""
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

PASS = []
FAIL = []

def check(name, cond, msg=""):
    if cond:
        PASS.append(name)
        print(f"  PASS  {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL  {name}  {msg}")

print("=== H2 双版报告差分 ===")

# ── Mock fixtures (复刻 conftest.py) ─────────────────────

class _Conf:
    def __init__(self, star, pct): self.star=star; self.percent=pct

class _Ev:
    def __init__(self, rule_id, school, description=""):
        self.rule_id=rule_id; self.school=school; self.description=description

class _Mag:
    def __init__(self, ordinal, score): self.ordinal=ordinal; self.score=score

class _Tiyong:
    body=[]; purpose=[]; rationale="mock体用"

class _Zuogong:
    def __init__(self, desc, rule_ids, star=4, pct=80):
        self.description=desc
        self.evidence=[_Ev(r,"段") for r in rule_ids]
        self.confidence=_Conf(star, pct)
        self.strength=_Mag("强",0.8)
        self.layer_count=3

class MockEnergy:
    case_id="C-2026-099-甲申乙酉丙申乙未"
    layer_count=4; wealth_ceiling="L4"
    energy_level=_Mag("中上",0.75)
    confidence=_Conf(4,80)
    zuogong_paths=[_Zuogong("财官印齐",["M1-D-001"],star=4,pct=80),
                   _Zuogong("食伤生财",["M1-D-007"],star=5,pct=88)]
    tiyong=_Tiyong()
    evidence=[_Ev("M1-D-001","段","财官印齐主公职"),
              _Ev("M2-Y-068","杨","婚姻晚")]
    def hash(self): return "mockenergy01"

class _Caifu:
    type="印格"; rank=4
class _Guanming:
    type="正官格"; rank=4
class _WubuStep:
    def __init__(self,step,name,finding):
        self.step=step; self.name=name; self.finding=finding; self.evidence=[]

class MockPicture:
    case_id="C-2026-099"
    confidence=_Conf(4,82)
    caifu=_Caifu(); guanming=_Guanming()
    industry_pointers=["公职","文化"]
    marriage_picture={"初婚最佳窗口":[28,32]}
    wubu_steps=[_WubuStep(1,"看格","印格成立"),_WubuStep(2,"看气","气清")]
    evidence=[_Ev("M2-Y-068","杨","婚姻晚"),_Ev("M2-Y-099","杨","弱项-应过滤")]
    anyin_results=[]  # 补齐 _build_section_zero_vm 依赖
    wealth_15tier=None  # 补齐 _build_15tier_vm
    def hash(self): return "mockpicture01"

class _Layer:
    def __init__(self,passed): self.passed=passed
class _Trigger:
    def __init__(self,t,d): self.type=t; self.description=d

class MockGate:
    def __init__(self,year,event,domain,passed=3,star=5,pct=90,rule_ids=None):
        self.year=year; self.candidate_event=event; self.domain=domain
        self.passed_layers=passed
        self.layer1=_Layer(passed>=1); self.layer2=_Layer(passed>=2); self.layer3=_Layer(passed>=3)
        self.confidence=_Conf(star,pct)
        self.primary_trigger=_Trigger("合化","卯戌合化火")
        self.door="正门"; self.is_xiong=False
        self.evidence=[_Ev(r,"任") for r in (rule_ids or ["MR-LAYER3"])]

class _DayunStep:
    def __init__(self,gz,s,e): self.干支=gz; self.起讫年=(s,e)
class _Dayun:
    排布=[_DayunStep("甲戌",1989,1998),_DayunStep("乙亥",1999,2008),
          _DayunStep("丙子",2009,2018),_DayunStep("丁丑",2019,2028)]
class _Pillar:
    def __init__(self, gan, zhi): self.gan=gan; self.zhi=zhi
    def __str__(self): return self.gan+self.zhi

class _Bazi:
    年柱=_Pillar("甲","申"); 月柱=_Pillar("乙","酉"); 日柱=_Pillar("丙","申"); 时柱=_Pillar("乙","未")

class MockParsed:
    case_id="C-2026-099-甲申乙酉丙申乙未"
    bazi=_Bazi(); dayun=_Dayun()
    birth={"公历":"1981-09-15","性别":"男"}

energy = MockEnergy()
picture = MockPicture()
gates = [
    MockGate(2027,"结婚","婚姻",passed=3,star=5,pct=92,rule_ids=["MR-LAYER3"]),
    MockGate(2030,"升迁","事业",passed=3,star=4,pct=85,rule_ids=["M3-R-031"]),
    MockGate(2025,"弱应期","财运",passed=2,star=3,pct=60,rule_ids=["MR-LAYER3"]),
]
parsed = MockParsed()

# ── 渲染 ────────────────────────────────────────────────
from tools.render_report import render

_FB_RE = re.compile(r"\[S-[\w-]+-[a-f0-9]{6}\]\s*\[\s*\]")

master_ctx = {}
client_ctx = {}
master_out = ""
client_out = ""

try:
    master_out = render(
        energy=energy, picture=picture, gates=gates, parsed=parsed, support=None,
        template_name="report-v1.3.md", variant="master",
        _skip_lint=True, _capture_ctx_to=master_ctx,
    )
except Exception as e:
    print(f"  [warn] master render: {e}")

try:
    client_out = render(
        energy=energy, picture=picture, gates=gates, parsed=parsed, support=None,
        template_name="report-v1.3.md", variant="client",
        _skip_lint=True, _capture_ctx_to=client_ctx,
    )
except Exception as e:
    print(f"  [warn] client render: {e}")

master_fb = len(_FB_RE.findall(master_out))
client_fb = len(_FB_RE.findall(client_out))

# T1: master 有反馈位
check("T1_master有反馈位", master_fb > 0, f"master_fb={master_fb}")

# T2: client 无反馈位（核心 H2 断言）
check("T2_client无反馈位", client_fb == 0,
      f"client_fb={client_fb}，泄漏了反馈位！渲染结果片段：\n"
      + "\n".join(l for l in client_out.splitlines() if "[S-" in l)[:300])

# T3: client complementary ★ >= 4
client_compl = client_ctx.get("complementary_conclusions", [])
master_compl = master_ctx.get("complementary_conclusions", [])
low_star_client = [c for c in client_compl if c.get("star",0) <= 3]
check("T3_client过滤弱项", len(low_star_client) == 0,
      f"client 含 ★≤3 断语: {[c.get('statement','')[:30] for c in low_star_client]}")

# T4: client gates ★ >= 4
client_gates = client_ctx.get("gate_results", [])
master_gates = master_ctx.get("gate_results", [])
low_gates_client = [g for g in client_gates if g.get("star",0) <= 3]
check("T4_client过滤弱应期", len(low_gates_client) == 0,
      f"client 含 ★≤3 应期: {[g.get('candidate_event','') for g in low_gates_client]}")

# T5: master 保留 ★≤3
has_low = any(c.get("star",0) <= 3 for c in master_compl) or \
          any(g.get("star",0) <= 3 for g in master_gates)
check("T5_master保留弱项", has_low,
      f"master compl stars={[c.get('star') for c in master_compl]}, "
      f"gate stars={[g.get('star') for g in master_gates]}")

# T6: client complementary ≤ master complementary
check("T6_client断语数≤master", len(client_compl) <= len(master_compl),
      f"client={len(client_compl)} > master={len(master_compl)}")

print(f"\nH2: {len(PASS)}/6 PASS  {'OK' if not FAIL else 'FAIL: '+str(FAIL)}")
sys.exit(0 if not FAIL else 1)
