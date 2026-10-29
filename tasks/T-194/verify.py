"""T-194 自检：只依赖标准库，退出码 0 = 通过。

检查项
1. fixed-20：20 条、克/生/化/各 5、盲卷无答案/定位字段、a/b 与答案一致、引文逐字、source_ref 区间合法。
2. fixed-20 四柱与 golden-20/holdout-20/fresh-40/anchor-60 零重叠；行区间零重叠。
3. routing：15 题、宫位/边/source_ref 计数与 counts 一致、阈值 0.80/0.60/0.60-0.79、题库存量 hash 与 prereg 一致。
"""

import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def p(rel):
    return os.path.join(ROOT, rel)


def load(rel):
    with open(p(rel), encoding="utf-8") as fh:
        return json.load(fh)


def sha(rel):
    with open(p(rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


errors = []


def check(cond, msg):
    if not cond:
        errors.append(msg)


def parse_loc(loc):
    m = re.match(r"L(\d+)-L(\d+)$", loc or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


def main():
    blind = load("META/p1-fixed-20-blind-v1.json")
    ans = load("META/p1-fixed-20-answers-v1.json")
    rq = load("META/routing-questions-v1.json")
    rp = load("META/routing-prereg-v1.json")

    # ---- fixed-20 ----
    check(len(blind["cases"]) == 20, "blind case count != 20")
    check(len(ans["cases"]) == 20, "answers case count != 20")
    check(blind["case_count"] == 20 and ans["case_count"] == 20, "case_count field != 20")

    allowed_case = {"case_id", "chart_id", "four_pillars", "gender", "layer", "target_relation"}
    allowed_tr = {"addr_a", "addr_b", "char_a", "char_b", "mechanism"}
    mech = {}
    for c in blind["cases"]:
        check(set(c) == allowed_case, "blind case keys %s" % c.get("case_id"))
        check(set(c["target_relation"]) == allowed_tr, "target_relation keys %s" % c.get("case_id"))
        mech[c["target_relation"]["mechanism"]] = mech.get(c["target_relation"]["mechanism"], 0) + 1
    check(mech == {"克": 5, "生": 5, "化": 5, "墓": 5}, "mechanism distribution %s" % mech)

    bmap = {c["case_id"]: c for c in blind["cases"]}
    amap = {c["case_id"]: c for c in ans["cases"]}
    check(set(bmap) == set(amap), "blind/answers id mismatch")

    dev_pillars = set()
    dev_intervals = {}
    for rel, nm in [("META/golden-20-v1.json", "golden-20"),
                    ("META/p1-holdout-v1.json", "holdout-20"),
                    ("META/p1-fresh-40-v1.json", "fresh-40"),
                    ("META/p1-fresh-40-routing-v1.json", "fresh-40-routing")]:
        for c in load(rel)["cases"]:
            dev_pillars.add(c["four_pillars"])
            src = c.get("source") or {}
            iv = parse_loc(src.get("locator"))
            if src.get("path") and iv:
                dev_intervals.setdefault(src["path"], []).append((iv[0], iv[1], c["case_id"], nm))
    for c in load("META/p1-anchor-60-answers-v1.json")["cases"]:
        sr = c.get("source_ref") or ""
        if ":" not in sr:
            continue
        path, loc = sr.rsplit(":", 1)
        iv = parse_loc(loc)
        if iv:
            dev_intervals.setdefault(path, []).append((iv[0], iv[1], c["case_id"], "anchor-60"))

    for cid, a in amap.items():
        b = bmap[cid]
        check(b["four_pillars"] not in dev_pillars, "%s overlaps dev four pillars" % cid)
        r = a["relation"]
        tr = b["target_relation"]
        check((r["a"], r["b"]) == (tr["char_a"], tr["char_b"]), "%s a/b mismatch" % cid)
        check(tr["mechanism"] == r["mechanism"], "%s mechanism mismatch" % cid)
        check({r["actor"], r["target"]} == {r["a"], r["b"]}, "%s actor/target not endpoints" % cid)
        check(r["actor"] != r["target"], "%s actor==target" % cid)
        path, loc = a["source_ref"].rsplit(":", 1)
        iv = parse_loc(loc)
        check(iv is not None, "%s source_ref format" % cid)
        if not iv or not os.path.exists(p(path)):
            check(False, "%s source path missing" % cid)
            continue
        lines = open(p(path), encoding="utf-8").read().splitlines()
        s, e = iv
        check(1 <= s <= e <= len(lines), "%s source range out of file" % cid)
        check(a["quote"] in lines[a["quote_line"] - 1], "%s quote not at quote_line" % cid)
        check(s <= a["quote_line"] <= e, "%s quote_line outside source_ref" % cid)
        check(r["actor"] in a["quote"] and r["target"] in a["quote"], "%s quote lacks endpoints" % cid)
        brs = [x[1] for x in b["four_pillars"].split()]
        check(brs.count(r["actor"]) == 1 and brs.count(r["target"]) == 1, "%s duplicate endpoint char" % cid)
        for (x, y, dcid, dname) in dev_intervals.get(path, []):
            check(iv[1] < x or y < iv[0], "%s interval overlaps %s/%s" % (cid, dname, dcid))

    # ---- routing ----
    check(len(rq["questions"]) == 15, "routing questions != 15")
    check(rp["thresholds"]["pass_min"] == 0.80, "pass_min != 0.80")
    check(rp["thresholds"]["kill_below"] == 0.60, "kill_below != 0.60")
    check(rp["thresholds"]["gray"] == [0.60, 0.80], "gray band mismatch")
    check(rp["inputs"]["questions_sha256"] == sha("META/routing-questions-v1.json"),
          "prereg questions hash stale")
    tot = {"palaces": 0, "edges": 0, "source_refs": 0}
    for item in rq["questions"]:
        ee = item["expected_evidence"]
        check(bool(ee["palaces"]) and bool(ee["source_refs"]), "%s empty evidence" % item["question_id"])
        tot["palaces"] += len(ee["palaces"])
        tot["edges"] += len(ee["edges"])
        tot["source_refs"] += len(ee["source_refs"])
        for sref in ee["source_refs"]:
            path, loc = sref.rsplit(":", 1)
            iv = parse_loc(loc)
            check(iv is not None and os.path.exists(p(path)), "%s bad source_ref" % item["question_id"])
            if iv and os.path.exists(p(path)):
                lines = open(p(path), encoding="utf-8").read().splitlines()
                check(1 <= iv[0] <= iv[1] <= len(lines), "%s source_ref range invalid" % item["question_id"])
    check(tot == rq["counts"]["items"], "routing counts mismatch %s vs %s" % (tot, rq["counts"]["items"]))
    routing_charts = {x["chart"]["case_id"] for x in rq["questions"]}
    check(routing_charts <= set(bmap), "routing chart not in fixed-20 blind")

    print("fixed-20 blind  sha256:", sha("META/p1-fixed-20-blind-v1.json"))
    print("fixed-20 answer sha256:", sha("META/p1-fixed-20-answers-v1.json"))
    print("routing questions sha256:", sha("META/routing-questions-v1.json"))
    print("routing prereg  sha256:", sha("META/routing-prereg-v1.json"))
    print("routing items:", tot)

    if errors:
        print("\nFAIL (%d)" % len(errors))
        for e in errors:
            print(" -", e)
        return 1
    print("\nPASS: 20/20 fixed, 15 routing questions, invariants ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
