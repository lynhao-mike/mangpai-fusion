#!/usr/bin/env python3
"""H3 · feedback_ingest 解析正确率 ≥ 99% stdlib smoke"""
import sys, types
from pathlib import Path

# ── 桩 yaml ───────────────────────────────────────────────
fake_yaml = types.ModuleType("yaml")
fake_yaml.safe_load = lambda s: {}
fake_yaml.safe_dump = lambda d, **kw: ""
fake_yaml.load = lambda s, Loader=None: {}
fake_yaml.YAMLError = Exception
class _Loader: pass
fake_yaml.SafeLoader = _Loader
sys.modules["yaml"] = fake_yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PASS = []
FAIL = []

def check(name, cond, msg=""):
    if cond:
        PASS.append(name)
        print(f"  PASS  {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL  {name}  {msg}")

print("=== H3 feedback_ingest 解析正确率 ===")

from tools.feedback_ingest import (
    parse_statement_feedback,
    ANNOTATION_TO_VERDICT,
    StatementFeedback,
    fanout_to_rules,
)

# ── T1: 100 条样本 ≥ 99% 正确率 ───────────────────────
def _gen_100():
    sids = []
    for i in range(100):
        nnn = f"{(i+1)%1000:03d}"
        suffix = f"{(i*31337 + 0xa1b2c3)%0xffffff:06x}"
        sids.append(f"S-{nnn}-{suffix}")
    annotations = ["y","n","?","skip"]
    verdicts = {"y":"hit","n":"miss","?":"no_data","skip":"no_data"}
    formats = [
        "反馈：[{sid}] [{ann}]",
        "[{sid}] [{ann}]",
        "  反馈：[{sid}]  [{ann}]  ",
        "**反馈**：[{sid}] [{ann}]",
        "| 表格 | [{sid}] [{ann}] |",
    ]
    samples = []
    for i in range(100):
        ann = annotations[i%4]
        fmt = formats[i%len(formats)]
        line = fmt.format(sid=sids[i], ann=ann)
        samples.append((line, sids[i], verdicts[ann]))
    return samples

samples = _gen_100()
text = "\n".join(line for line,_,_ in samples)
parsed = parse_statement_feedback(text)
parsed_map = {f.statement_id: f for f in parsed}

correct = 0
errors = []
for line, expected_sid, expected_verdict in samples:
    if expected_sid not in parsed_map:
        errors.append(f"未解析: {line[:80]}  期望 sid={expected_sid}")
        continue
    got = parsed_map[expected_sid].verdict
    if got == expected_verdict:
        correct += 1
    else:
        errors.append(f"verdict错: 期望={expected_verdict} 实得={got}  行={line[:60]}")

accuracy = correct / 100
check("T1_100样本正确率≥99%", accuracy >= 0.99,
      f"accuracy={accuracy:.1%}\n  首5错误: {errors[:5]}")

# ── T2: ?/skip → no_data ──────────────────────────────
check("T2_问号映射no_data", ANNOTATION_TO_VERDICT["?"] == "no_data")
check("T2_skip映射no_data", ANNOTATION_TO_VERDICT["skip"] == "no_data")

fb_txt = "反馈：[S-001-aaaaaa] [?]\n反馈：[S-001-bbbbbb] [skip]"
r2 = parse_statement_feedback(fb_txt)
check("T2_?skip实际解析", all(p.verdict == "no_data" for p in r2),
      f"verdicts={[p.verdict for p in r2]}")

# ── T3: 同 sid 取最后 ─────────────────────────────────
dup_txt = "反馈：[S-001-deadbe] [y]\n改主意：\n反馈：[S-001-deadbe] [n]"
r3 = parse_statement_feedback(dup_txt)
check("T3_重复sid取最后", len(r3) == 1 and r3[0].verdict == "miss",
      f"count={len(r3)} verdict={r3[0].verdict if r3 else 'N/A'}")

# ── T4: 空文档 → 0 条 ────────────────────────────────
check("T4_空文档0条", parse_statement_feedback("") == [])
check("T4_纯文字0条", parse_statement_feedback("# 命主反馈\n纯文字无标注") == [])

# ── T5: fanout 决断力优先 miss > hit（兼容 list schema 扩展 rule_ids） ─────────────────
si = {
    "case_id": "C-2026-001-乾-甲子乙丑丙寅丁卯",
    "generated_at": "2026-05-30",
    "statements": [
        {"statement_id":"S-001-aaaaaa","domain":"婚姻","summary":"婚姻晚","status":"pending",
         "rule_ids":["M1-D-001","M2-Y-068"]},
        {"statement_id":"S-001-bbbbbb","domain":"事业","summary":"公职","status":"pending",
         "rule_ids":["M1-D-001"]},
    ],
}
fbs = [StatementFeedback("S-001-aaaaaa","y","hit"),
       StatementFeedback("S-001-bbbbbb","n","miss")]
rule_vd, unknown = fanout_to_rules(fbs, si)
check("T5_miss优先于hit", rule_vd.get("M1-D-001",("?",))[0] == "miss",
      f"M1-D-001 verdict={rule_vd.get('M1-D-001','?')}")
check("T5_M2-Y-068是hit", rule_vd.get("M2-Y-068",("?",))[0] == "hit",
      f"M2-Y-068 verdict={rule_vd.get('M2-Y-068','?')}")
check("T5_unknown=0", unknown == [], f"unknown={unknown}")

si_standard = {
    "case_id": "C-2026-025-坤-辛未乙未甲辰乙亥",
    "generated_at": "2026-05-30",
    "statements": [{"statement_id":"S-025-d1a001","domain":"事业/财富","summary":"财厚劫透","status":"pending"}],
}
rule_vd2, unknown2 = fanout_to_rules([StatementFeedback("S-025-d1a001","y","hit")], si_standard)
check("T6_标准无rule_ids不判unknown", rule_vd2 == {} and unknown2 == [], f"rule_vd={rule_vd2} unknown={unknown2}")

print(f"\nH3: {len(PASS)}/11 PASS  {'OK' if not FAIL else 'FAIL: '+str(FAIL)}")
sys.exit(0 if not FAIL else 1)
