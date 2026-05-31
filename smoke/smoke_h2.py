#!/usr/bin/env python3
"""H2 · 唯一标准报告 stdlib smoke（无 pytest/PyYAML）

核心：025 标准章节存在、无反馈空槽、无双版标记、上下文只保留 ★4+ 主线。
"""
import sys, types, re

fake_yaml = types.ModuleType("yaml")
fake_yaml.safe_load = lambda s: {}
fake_yaml.safe_dump = lambda d, **kw: ""
fake_yaml.load = lambda s, Loader=None: {}
fake_yaml.YAMLError = Exception
class _Loader: pass
fake_yaml.SafeLoader = _Loader
sys.modules["yaml"] = fake_yaml

sys.path.insert(0, ".")

PASS = []
FAIL = []

def check(name, cond, msg=""):
    if cond:
        PASS.append(name)
        print(f"  PASS  {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL  {name}  {msg}")

print("=== H2 唯一标准报告 ===")

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
    evidence=[_Ev("M1-D-001","段","财官印齐主公职"), _Ev("M2-Y-068","杨","婚姻晚")]
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
    anyin_results=[]
    wealth_15tier=None
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
    排布=[_DayunStep("甲戌",1989,1998),_DayunStep("乙亥",1999,2008),_DayunStep("丙子",2009,2018),_DayunStep("丁丑",2019,2028)]
class _Pillar:
    def __init__(self, gan, zhi): self.gan=gan; self.zhi=zhi
    def __str__(self): return self.gan+self.zhi
class _Bazi:
    年柱=_Pillar("甲","申"); 月柱=_Pillar("乙","酉"); 日柱=_Pillar("丙","申"); 时柱=_Pillar("乙","未")
class MockParsed:
    case_id="C-2026-099-甲申乙酉丙申乙未"
    bazi=_Bazi(); dayun=_Dayun(); birth={"公历":"1981-09-15","性别":"男"}

from tools.render_report import render

ctx = {}
out = render(
    energy=MockEnergy(), picture=MockPicture(),
    gates=[MockGate(2027,"结婚","婚姻",passed=3,star=5,pct=92), MockGate(2025,"弱应期","财运",passed=2,star=3,pct=60)],
    parsed=MockParsed(), support=None, template_name="legacy-ignored.md", variant="legacy-ignored",
    _skip_lint=True, _capture_ctx_to=ctx,
)

required = ["## 0. 基本盘面", "## 一、命局核心结论", "## 三、五维定位", "## 九、总评", "## 归档信息"]
check("T1_025章节齐全", all(h in out for h in required))
check("T2_无反馈空槽", re.search(r"\[S-[\w-]+\]\s*\[\s*\]", out) is None)
check("T3_无双版标记", all(x not in out for x in ["MASTER 版", "CLIENT 版", "master/client"]))
check("T4_variant收敛standard", ctx.get("variant") == "standard" and ctx.get("is_client") is True and ctx.get("is_master") is False)
low_items = [item for key in ("zuogong_paths","consensus_conclusions","complementary_conclusions","gate_results","iron_gates") for item in ctx.get(key, []) if item.get("star",0) <= 3]
check("T5_只保留高星主线", not low_items, f"low_items={low_items[:2]}")

print(f"\nH2: {len(PASS)}/5 PASS  {'OK' if not FAIL else 'FAIL: '+str(FAIL)}")
sys.exit(0 if not FAIL else 1)
