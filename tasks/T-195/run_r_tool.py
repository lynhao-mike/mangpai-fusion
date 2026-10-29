#!/usr/bin/env python
"""T-195 · R-tool runner: fixed-20 固定类事实 + routing 证据包（无方向/无断语）。

只读（白名单）：
  - META/p1-fixed-20-blind-v1.json            （盲卷：case/chart/四柱/性别/target_relation）
  - META/routing-questions-v1.json            （仅 runner_visible_fields：question_id/domain/question/chart）
  - docs/specs/fact-evidence-pack-v1.md       （R 规格）
  - docs/specs/actor-rules-v1.md              （engine 固定规则的 actor 口径）
  - python -m engine.cli                      （盘面事实唯一来源）
  - python -m tools.query_theory              （理论检索）
  - sources/                                  （原文逐字核对）
禁止：p1-fixed-20-answers*、p1-fixed-20-B*、routing-prereg 的 expected_evidence、
      anchor/fresh/holdout/golden answers、p1-system-run*；不跑评分器；不写 git。

产出：META/r-tool-run-v1.json

用法：
  .venv\\Scripts\\python.exe tasks\\T-195\\run_r_tool.py [--out META/r-tool-run-v1.json]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from engine.facts.chart_facts import wuxing_relation  # noqa: E402
from engine.predicates.types import ZHI_TO_WUXING  # noqa: E402

PY = sys.executable
NOW = _dt.datetime.now(_dt.timezone(_dt.timedelta(hours=8))).isoformat(timespec="seconds")

BLIND = REPO / "META" / "p1-fixed-20-blind-v1.json"
QUESTIONS = REPO / "META" / "routing-questions-v1.json"

FOUR = ("克", "生", "化", "墓")
PILLAR_ORDER = {"Y": 0, "M": 1, "D": 2, "H": 3}
RUNNER_VISIBLE = ("question_id", "domain", "question", "chart")

# ── 类级原文锚点（actor-rules-v1 §3 正例）────────────────────────────────────
CLASS_ANCHOR = {
    "克": ("sources/duan/MinerU_markdown_22.盲派初级命理学_2056045493286002688.md", "官杀来克身"),
    "生": ("sources/duan/MinerU_markdown_墓__穿_2056043829099421696.md", "庚金生坐下子水"),
    "化": ("sources/duan/MinerU_markdown_23.盲派中级命理学_2056045463376420864.md", "甲寅七杀被旺火所化"),
    "墓": ("sources/duan/MinerU_markdown_22.盲派初级命理学_2056045493286002688.md", "未墓寅"),
}

# ── 领域 → 原文段落登记表（M-10..M-13）────────────────────────────────────────
DOMAIN_DOC = {
    "婚姻": {
        "query": "配偶宫 配偶星",
        "album": "sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md",
        "ranges": [(15, 17), (37, 44)],
        "applicability": ["配偶宫/配偶星定义", "配偶宫与配偶星的相关性类型"],
    },
    "事业": {
        "query": "官命 官杀 印星",
        "album": "sources/duan/MinerU_markdown_23.盲派中级命理学_2056045463376420864.md",
        "ranges": [(2819, 2827), (2829, 2831)],
        "applicability": ["官命核心：官杀与印星", "官职类型组合"],
    },
    "健康": {
        "query": "疾病 日支 身体",
        "album": "sources/duan/MinerU_markdown_疾病_2056043976378220544.md",
        "ranges": [(3, 11)],
        "applicability": ["疾病总则：宫位与干支象法"],
    },
    "财运": {
        "query": "求财 财星",
        "album": "sources/duan/MinerU_markdown_求财_2056043780500029440.md",
        "ranges": [(3, 5)],
        "extras": [("sources/duan/MinerU_markdown_命格组合_2056043853946478592.md", 3, 7,
                    "主位/宾位与财官组合")],
        "applicability": ["求财取象"],
    },
}

PALACE_BASIS = {
    "M-01": ("sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md", 15, 17, "配偶宫为日主坐支"),
    "M-02": ("sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md", 17, 17, "配偶星：男命财星、女命官杀"),
    "M-03": ("sources/duan/MinerU_markdown_23.盲派中级命理学_2056045463376420864.md", 2819, 2827, "月令为事业与格局之根"),
    "M-04": (None, 0, 0, "日干为本人（engine chart.day_master）"),
    "M-05": ("sources/duan/MinerU_markdown_疾病_2056043976378220544.md", 3, 11, "日支为身体宫"),
    "M-06": ("sources/duan/MinerU_markdown_疾病_2056043976378220544.md", 5, 7, "月令定阴阳寒燥"),
    "M-07": ("sources/duan/MinerU_markdown_求财_2056043780500029440.md", 3, 5, "财星取象"),
    "M-08": ("sources/duan/MinerU_markdown_命格组合_2056043853946478592.md", 3, 7, "主位取财之身"),
}

NON_CLAIMS = [
    "不判冲/合/穿/刑/破的方向（一律 direction=undetermined、actor=null、target=null）",
    "不判吉凶、成败、应期、事件、概率、置信度",
    "不判主次/体用胜负",
    "不把固定克/生/化/墓写成结论（is_conclusion 恒 false）",
    "不判救应、不判岁运引动、不判党势",
]


# ── 基础设施 ────────────────────────────────────────────────────────────────
def run(cmd: list[str]) -> tuple[int, bytes, bytes]:
    p = subprocess.run(cmd, cwd=str(REPO), capture_output=True)
    return p.returncode, p.stdout, p.stderr


def engine_all(pillars: str, gender: str) -> tuple[dict, dict]:
    """返回 (engine JSON, input_meta)；性别非 乾/坤 时回退 乾 并记录。"""
    meta = {"gender_input": gender, "gender_used": gender, "fallback": None}
    code, out, err = run([PY, "-m", "engine.cli", "all", "--pillars", pillars,
                          "--gender", gender, "--json"])
    if code != 0:
        if "性别" not in err.decode("utf-8", "replace"):
            raise RuntimeError(f"engine.cli failed: {err.decode('utf-8', 'replace')[:300]}")
        meta["gender_used"] = "乾"
        meta["fallback"] = ("盲卷性别为「未注明」，engine 仅接受 乾/坤；此处按 乾 排盘。"
                            "固定类事实与十神判定不依赖性别，routing 未用到该盘。")
        code, out, err = run([PY, "-m", "engine.cli", "all", "--pillars", pillars,
                              "--gender", "乾", "--json"])
        if code != 0:
            raise RuntimeError(f"engine.cli failed: {err.decode('utf-8', 'replace')[:300]}")
    return json.loads(out.decode("utf-8-sig")), meta


_FILE_CACHE: dict[str, list[str]] = {}


def read_lines(rel_path: str) -> list[str]:
    if rel_path not in _FILE_CACHE:
        with open(REPO / rel_path, encoding="utf-8") as fh:
            _FILE_CACHE[rel_path] = fh.read().splitlines()
    return _FILE_CACHE[rel_path]


def line_text(rel_path: str, lineno: int) -> str:
    lines = read_lines(rel_path)
    if not 1 <= lineno <= len(lines):
        raise IndexError(f"{rel_path}:L{lineno} out of range")
    return lines[lineno - 1]


def _strip_marks(raw: str) -> str:
    """只剥行首/行尾 markdown 标记，结果仍是原行的连续子串。"""
    text = raw.strip()
    changed = True
    while changed:
        changed = False
        for mark in ("**", "#", "- ", "> "):
            if text.startswith(mark):
                text = text[len(mark):].strip()
                changed = True
        if text.endswith("**") and len(text) > 2:
            text = text[:-2].strip()
            changed = True
    return text


def _truncate(text: str, max_len: int = 72) -> str:
    if len(text) <= max_len:
        return text
    cut = text[:max_len]
    for sep in ("。", "；", "，", " "):
        idx = cut.rfind(sep)
        if idx >= 24:
            return text[: idx + 1].strip()
    return cut.strip()


def verbatim_quote(rel_path: str, start: int, end: int, min_len: int = 16) -> str:
    """在行区间内取第一条实句，返回原文的连续子串（逐字）。"""
    for n in range(start, end + 1):
        text = _strip_marks(line_text(rel_path, n))
        if len(text) >= min_len:
            return _truncate(text)
    raise ValueError(f"{rel_path}:{start}-{end} 无可引用实句")


def verify_quote(rel_path: str, start: int, end: int, quote: str) -> bool:
    if not quote:
        return False
    return any(quote in line_text(rel_path, n) for n in range(start, end + 1))


def addr_span(start: int, end: int) -> str:
    return f"L{start}" if start == end else f"L{start}-L{end}"


def class_anchor(cls: str) -> dict:
    path, phrase = CLASS_ANCHOR[cls]
    for n, text in enumerate(read_lines(path), 1):
        if phrase in text:
            i = text.index(phrase)
            quote = text[i: i + len(phrase) + 30].strip()
            assert quote in text
            return {"source_ref": f"{path}:L{n}", "quote": quote,
                    "role": "class_rule_anchor", "quote_verified": True}
    raise RuntimeError(f"{cls} 类锚点未找到：{path} / {phrase}")


# ── fixed-20 ────────────────────────────────────────────────────────────────
def pick_candidate(cands: list[dict], pair: set[str], cls: str) -> dict | None:
    if cls == "克":
        for kind in ("zhi_ke", "ke", "canggan_ke", "gan_ke_zhi"):
            for c in cands:
                if set(c["members"]) == pair and c["mode"] == "制用" and c["relation_kind"] == kind:
                    return c
    elif cls == "生":
        for mode in ("生泄用", "sheng"):
            for c in cands:
                if set(c["members"]) == pair and c["mode"] == mode:
                    return c
    elif cls == "化":
        for c in cands:
            if set(c["members"]) == pair and c["mode"] == "化用":
                return c
    elif cls == "墓":
        for c in cands:
            if set(c["members"]) == pair and c["mode"] == "墓用":
                return c
    return None


def element_direction(chars: dict[str, str], a: str, b: str, cls: str):
    """按 engine 五行表推得施力方；化者=受生端（actor-rules-v1 §4.8）。"""
    wa, wb = ZHI_TO_WUXING[chars[a]], ZHI_TO_WUXING[chars[b]]
    rel = wuxing_relation(wa, wb)
    if cls == "生":
        if rel == "生":
            return a, b, f"engine 五行表：{wa}生{wb}（生者→被生者）"
        if rel == "被生":
            return b, a, f"engine 五行表：{wb}生{wa}（生者→被生者）"
    if cls == "化":
        if rel == "生":
            return b, a, f"engine 五行表：{wa}生{wb}；化者=受生端（actor-rules-v1 §4.8）"
        if rel == "被生":
            return a, b, f"engine 五行表：{wb}生{wa}；化者=受生端（actor-rules-v1 §4.8）"
    if cls == "克":
        if rel == "克":
            return a, b, f"engine 五行表：{wa}克{wb}"
        if rel == "被克":
            return b, a, f"engine 五行表：{wb}克{wa}"
    return None


def build_fixed_facts(case: dict, eng: dict, inmeta: dict) -> dict:
    tr = case["target_relation"]
    cls = tr["mechanism"]
    pair = {tr["addr_a"], tr["addr_b"]}
    a_addr, b_addr = sorted(pair, key=lambda x: PILLAR_ORDER[x[0]])

    chars: dict[str, str] = {}
    for p in eng["chart"]["pillars"]:
        chars[p["stem"]["addr"]] = p["stem"]["char"]
        chars[p["branch"]["addr"]] = p["branch"]["char"]

    cands = eng["duan_zuogong"]["candidates"]
    cand = pick_candidate(cands, pair, cls)

    fact = {
        "case_id": case["case_id"],
        "chart_id": case["chart_id"],
        "four_pillars": case["four_pillars"],
        "target_relation": {"addr_a": tr["addr_a"], "addr_b": tr["addr_b"],
                            "char_a": tr["char_a"], "char_b": tr["char_b"], "mechanism": cls},
        "class": cls,
        "is_conclusion": False,
        "basis": "engine_fixed_rule",
        "gender_input": inmeta["gender_input"],
        "gender_used": inmeta["gender_used"],
        "class_source_ref": class_anchor(cls),
    }

    if cand is not None:
        actor, target = cand["members"][0], cand["members"][1]
        fact.update({
            "actor": actor, "actor_char": chars[actor],
            "target": target, "target_char": chars[target],
            "edge_id": cand.get("edge_id"),
            "engine_path": f"duan_zuogong.candidates[{cands.index(cand)}]",
            "engine_rule": f"{cand['mode']}/{cand['relation_kind']}",
            "matched_by": "engine_candidate",
            "rule_ref": {
                "克": "engine/facts/structure_check.py:473-482 (_derived_zhi_ke)；docs/specs/actor-rules-v1.md:L120-L127",
                "生": "engine/facts/structure_check.py:415-430 (_derived_sheng)；docs/specs/actor-rules-v1.md:L129-L137",
                "化": "docs/specs/actor-rules-v1.md:L138-L148（化用：官杀→印，化者=受生端）",
                "墓": "docs/specs/actor-rules-v1.md:L150-L166（墓用：库→入库方）",
            }[cls],
        })
    else:
        flags = []
        derived = None
        if cls in ("生", "化", "克"):
            derived = element_direction(chars, a_addr, b_addr, cls)
        if derived is None:
            for c in cands:
                if set(c["members"]) == pair and c["actor"]:
                    derived = (c["members"][0], c["members"][1],
                               f"engine 同端点对候选 {c['mode']}/{c['relation_kind']} 的力向")
                    flags.append("class_rule_unavailable_engine_pair_fallback")
                    fact["basis"] = "engine_pair_direction_with_target_class"
                    break
        if derived is None:
            raise RuntimeError(f"{case['case_id']}: 无法由 engine 固定规则定位施力方")
        actor, target, note = derived
        fact.update({
            "actor": actor, "actor_char": chars[actor],
            "target": target, "target_char": chars[target],
            "edge_id": None,
            "engine_path": "derived",
            "engine_rule": "engine 五行表 + actor-rules-v1",
            "matched_by": "engine_element_rule" if "五行表" in note else "engine_pair_fallback",
            "rule_ref": "docs/specs/actor-rules-v1.md:L129-L148；engine/predicates/types.py ZHI_TO_WUXING",
            "derivation": note,
            "class_rule_mismatch": True,
            "flags": flags or ["engine 未对该端点对发出目标类候选，按 engine 五行表推得"],
        })
        if not flags:
            fact["basis"] = "engine_fixed_rule_derived"

    fact["endpoints_within_target_relation"] = {fact["actor"], fact["target"]} == pair
    fact["direction_validity"] = "within_target_relation_endpoints"
    fact["source_ref"] = fact["class_source_ref"]["source_ref"]
    return fact


# ── routing ─────────────────────────────────────────────────────────────────
def ten_god_index(eng: dict) -> dict[str, str]:
    out = {}
    for p in eng["chart"]["pillars"]:
        out[p["stem"]["addr"]] = p["stem"]["ten_god"]
        out[p["branch"]["addr"]] = p["branch"]["main_ten_god"]
    return out


def palaces_for(domain: str, eng: dict) -> list[dict]:
    index = ten_god_index(eng)
    seats: list[dict] = []

    def add(addr: str, rule: str, role: str) -> None:
        for seat in seats:  # 同址合并，避免同一宫位重复计数
            if seat["addr"] == addr:
                if role not in seat["role"]:
                    seat["role"] += "；" + role
                if rule not in seat["mapping_rules"]:
                    seat["mapping_rules"].append(rule)
                return
        path, s, e, basis = PALACE_BASIS[rule]
        item = {"addr": addr, "role": role, "ten_god": index.get(addr),
                "mapping_rule": rule, "mapping_rules": [rule], "mapping_basis": basis}
        if path:
            item["basis_source_ref"] = f"{path}:{addr_span(s, e)}"
        seats.append(item)

    if domain == "婚姻":
        add("D.b", "M-01", "配偶宫（夫妻宫）")
        stars = ("正财", "偏财") if eng["chart"]["gender"] == "乾" else ("正官", "七杀")
        label = "配偶星：财星（男命）" if eng["chart"]["gender"] == "乾" else "配偶星：官杀（女命）"
        for addr in [a for a, g in index.items() if g in stars]:
            add(addr, "M-02", label + ("（透干）" if addr.endswith(".s") else ""))
    elif domain == "事业":
        add("M.b", "M-03", "月令/事业宫")
        add("D.s", "M-04", "日主")
    elif domain == "健康":
        add("D.b", "M-05", "日支/身体宫")
        add("D.s", "M-04", "日主")
        add("M.b", "M-06", "月令/气候")
    elif domain == "财运":
        for addr in [a for a, g in index.items() if g in ("正财", "偏财")]:
            add(addr, "M-07", "财星" + ("（透干）" if addr.endswith(".s") else ""))
        add("D.b", "M-08", "主位/取财之身")
    return seats


def edges_for(palaces: list[dict], eng: dict) -> list[dict]:
    branch_keys = {p["addr"] for p in palaces if p["addr"].endswith(".b")}
    out = []
    for e in eng["relations"]["edges"]:
        members = e["members"]
        if not all(m.endswith(".b") for m in members):
            continue
        if not branch_keys & set(members):
            continue
        out.append({
            "edge_id": e["id"], "kind": e["kind"], "members": members,
            "chars": e.get("chars"),
            "scope": "natal", "group": e.get("group"), "completeness": e.get("completeness"),
            "direction": "undetermined", "actor": None, "target": None,
        })
    return out


def query_theory_hits(domain: str) -> list[dict]:
    q = DOMAIN_DOC[domain]["query"]
    code, out, err = run([PY, "-m", "tools.query_theory", "--query", q, "--schools", "duan",
                          "--top-k", "8", "--per-school-cap", "0", "--json"])
    if code != 0:
        return []
    try:
        hits = json.loads(out.decode("utf-8-sig"))
    except json.JSONDecodeError:
        return []
    return [{"entry_id": h.get("id"), "source_ref": (h.get("source_ref") or {}).get("path"),
             "anchor": (h.get("source_ref") or {}).get("anchor"), "score": h.get("score"),
             "title": h.get("title")} for h in hits]


def theory_for(domain: str, eng: dict, hits: list[dict]) -> list[dict]:
    doc = DOMAIN_DOC[domain]
    album = doc["album"]
    items: list[dict] = []

    def entry_id_for(path: str, s: int, e: int) -> str | None:
        for h in hits:
            if h.get("source_ref") != path or not h.get("anchor"):
                continue
            try:
                n = int(str(h["anchor"]).split(":")[-1].split("-")[0])
            except ValueError:
                continue
            if s <= n <= e:
                return h["entry_id"]
        return None

    def push(path: str, s: int, e: int, applicability: str, basis: str) -> None:
        quote = verbatim_quote(path, s, e)
        items.append({
            "entry_id": entry_id_for(path, s, e),
            "source_ref": f"{path}:{addr_span(s, e)}",
            "quote": quote,
            "applicability": applicability,
            "quote_verified": verify_quote(path, s, e, quote),
            "basis": basis,
        })

    for (s, e), applicability in zip(doc["ranges"], doc["applicability"]):
        push(album, s, e, applicability, "domain_album_passage")

    if domain == "健康":
        d_b = next(p for p in eng["chart"]["pillars"] if p["branch"]["addr"] == "D.b")["branch"]["char"]
        for n, text in enumerate(read_lines(album), 1):
            if text.strip().startswith(d_b + "："):
                quote = text.strip()
                items.append({
                    "entry_id": None,
                    "source_ref": f"{album}:L{n}",
                    "quote": quote,
                    "applicability": f"日支{d_b}的身体象（branch_to_organ_line）",
                    "quote_verified": quote in text,
                    "basis": "branch_to_organ_line",
                })
                break

    for path, s, e, applicability in doc.get("extras", []):
        push(path, s, e, applicability, "domain_album_passage")
    return items


def build_pack(q: dict, eng: dict) -> dict:
    palaces = palaces_for(q["domain"], eng)
    edges = edges_for(palaces, eng)
    hits = query_theory_hits(q["domain"])
    theory = theory_for(q["domain"], eng, hits)

    gaps = ["G2" if edges else None, "G3", "G4", "G5", "suiyun_ten_god"]
    gaps = [g for g in gaps if g]
    if eng["relations"].get("muku"):
        gaps.append("muku_open_close")
    if q["domain"] == "婚姻" and not any("M-02" in p["mapping_rules"] for p in palaces):
        gaps.append("no_spouse_star")
    if any(p["branch"]["char"] == "子" and p["branch"]["addr"] == "H.b" for p in eng["chart"]["pillars"]):
        gaps.append("boundary_zi_shi")

    facts = {
        "pillars": [
            {"palace": p["palace"], "ganzhi": p["ganzhi"],
             "stem": {"addr": p["stem"]["addr"], "char": p["stem"]["char"], "ten_god": p["stem"]["ten_god"]},
             "branch": {"addr": p["branch"]["addr"], "char": p["branch"]["char"],
                        "main_ten_god": p["branch"]["main_ten_god"],
                        "hidden": p["branch"]["hidden"]}}
            for p in eng["chart"]["pillars"]
        ],
        "day_master": eng["chart"]["day_master"],
        "ten_gods": [{"addr": p["stem"]["addr"], "char": p["stem"]["char"], "ten_god": p["stem"]["ten_god"]}
                     for p in eng["chart"]["pillars"]]
                    + [{"addr": p["branch"]["addr"], "char": p["branch"]["char"],
                        "ten_god": p["branch"]["main_ten_god"]} for p in eng["chart"]["pillars"]],
        "hidden_stems": [{"addr": p["branch"]["addr"], "char": p["branch"]["char"],
                          "hidden": p["branch"]["hidden"]} for p in eng["chart"]["pillars"]],
        "kong_wang": eng["chart"]["kongwang"],
        "tiyong": eng["duan_zuogong"]["tiyong"],
        "muku": [{"addr": m["addr"], "branch": m["branch"], "ku_of": m["ku_of"]}
                 for m in (eng["relations"].get("muku") or [])],
    }

    evidence = ([{"type": "palace", "ref": p["addr"], "mapping_rule": p["mapping_rule"]} for p in palaces]
                + [{"type": "edge", "ref": e["edge_id"]} for e in edges]
                + [{"type": "source", "ref": t["source_ref"]} for t in theory])

    return {
        "question_id": q["question_id"],
        "question": q["question"],
        "domain": q["domain"],
        "prereg_id": q["question_id"],
        "chart_id": q["chart"]["chart_id"],
        "case_id": q["chart"]["case_id"],
        "snapshot": {"chart_id": q["chart"]["chart_id"], "dayun_index": None, "liunian_year": None},
        "facts": facts,
        "palaces": palaces,
        "edges": edges,
        "theory": theory,
        "retrieval": {"engine": "tools.query_theory", "query": DOMAIN_DOC[q["domain"]]["query"],
                      "hits": hits},
        "evidence_items": evidence,
        "gaps": gaps,
        "non_claims": NON_CLAIMS,
        "provenance": {
            "engine_cmd": (f'python -m engine.cli all --pillars "{q["chart"]["four_pillars"]}" '
                           f'--gender {eng["chart"]["gender"]} --json'),
            "theory_cmd": (f'python -m tools.query_theory --query "{DOMAIN_DOC[q["domain"]]["query"]}" '
                           f'--schools duan --top-k 8 --per-school-cap 0 --json'),
            "pack_version": "v1",
        },
    }


# ── 主流程 ──────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="META/r-tool-run-v1.json")
    args = ap.parse_args()

    blind = json.loads(BLIND.read_text(encoding="utf-8"))
    prompts = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    questions = [{k: q[k] for k in RUNNER_VISIBLE} for q in prompts["questions"]]

    cache: dict[str, tuple[dict, dict]] = {}
    for c in blind["cases"]:
        cache[c["four_pillars"]] = engine_all(c["four_pillars"], c["gender"])

    fixed = [build_fixed_facts(c, cache[c["four_pillars"]][0], cache[c["four_pillars"]][1])
             for c in blind["cases"]]
    packs = [build_pack(q, cache[q["chart"]["four_pillars"]][0]) for q in questions]

    # 结构门禁自检（不评分，只做断言）
    assert {f["class"] for f in fixed} <= set(FOUR)
    assert len(fixed) == len(blind["cases"]) == 20
    assert all(f["endpoints_within_target_relation"] for f in fixed)
    assert all(t["quote_verified"] for p in packs for t in p["theory"]), "quote 未逐字命中"
    assert all(e["direction"] == "undetermined" and e["actor"] is None and e["target"] is None
               for p in packs for e in p["edges"])
    assert all(f["class_source_ref"]["quote_verified"] for f in fixed)
    covered = sum(1 for f in fixed if f["class"] == f["target_relation"]["mechanism"])

    breakdown: dict[str, int] = {}
    for f in fixed:
        breakdown[f["matched_by"]] = breakdown.get(f["matched_by"], 0) + 1

    out = {
        "schema": "r-tool-run/v1",
        "task": "T-195",
        "generated_at": NOW,
        "spec": "docs/specs/fact-evidence-pack-v1.md",
        "runner": {
            "script": "tasks/T-195/run_r_tool.py",
            "python": str(PY),
            "input_digest": {
                "META/p1-fixed-20-blind-v1.json": hashlib.sha256(BLIND.read_bytes()).hexdigest()[:16],
                "META/routing-questions-v1.json": hashlib.sha256(QUESTIONS.read_bytes()).hexdigest()[:16],
            },
        },
        "isolation": {
            "read_whitelist": [
                "tasks/T-195/PROMPT.md",
                "docs/specs/fact-evidence-pack-v1.md",
                "docs/specs/actor-rules-v1.md",
                "META/p1-fixed-20-blind-v1.json",
                "META/routing-questions-v1.json",
                "engine.cli", "tools.query_theory", "sources/",
                "engine/facts/structure_check.py（固定规则实现）",
                "engine/facts/chart_facts.py、engine/predicates/types.py（五行表）",
            ],
            "read_forbidden": False,
            "read_answers": False,
            "restricted_field_exposure": {
                "occurred": True,
                "file": "META/routing-questions-v1.json",
                "field": "questions[].expected_evidence",
                "declared_as": "access.restricted_fields（文件自称 runner 视图，实际未脱敏）",
                "scope": "routing 15 题；fixed-20 与答案文件未涉及",
                "consequence": "routing 证据包非盲跑，blind_valid=false，不可作为盲测入账",
            },
            "notes": [
                "未读 META/p1-fixed-20-answers-v1.json、p1-fixed-20-answers-B-v1.json、p1-fixed-20-B-v1.md",
                "未读 META/routing-prereg-v1.json、anchor/fresh/holdout/golden answers、p1-system-run*",
                "未跑评分器、未自评",
                "未做 git 写；未改 engine/答案/阈值/测试",
                "routing 证据包由本脚本按固定规则生成，可由干净会话重跑复现",
            ],
        },
        "fixed20": {
            "schema": "fact-evidence-pack/v1 · fixed slice",
            "case_count": len(fixed),
            "covered": covered,
            "coverage": f"{covered}/{len(fixed)}",
            "out_of_class_emissions": 0,
            "emission_policy": ("每条仅发射 target_relation 目标类（克/生/化/墓）一条方向事实；"
                                "不发射冲/合/穿/刑/破/党势/岁运方向"),
            "coverage_note": (
                "覆盖 20/20 由构造保证：target_relation.mechanism 已在盲卷内给出，runner 负责定位该类事实。"
                "信息量在 class_source_breakdown：engine 候选类直接命中 17/20；其余 3 条 engine 未发出目标类候选，"
                "按 engine 五行表/同端点对力向推得（逐条 class_rule_mismatch + flags）。"
                "G3：engine 不建支-支克边，故克类多为 inferred 候选（edge_id=null）。"
            ),
            "class_source_breakdown": breakdown,
            "class_rule_mismatch_cases": [f["case_id"] for f in fixed if f.get("class_rule_mismatch")],
            "facts": fixed,
        },
        "routing": {
            "schema": "fact-evidence-pack/v1",
            "question_count": len(packs),
            "blind_valid": False,
            "blind_invalid_reason": (
                "runner 按任务卡读 META/routing-questions-v1.json（标注为 runner 视图）时，"
                "文件内 expected_evidence 字段（access.restricted_fields）随整文件读取进入上下文，"
                "routing 已非盲跑。fixed-20 未受影响（未读任何答案文件）。"
                "需中枢提供脱敏 runner 视图（仅 runner_visible_fields）后在干净会话重跑本脚本，方可入账。"
            ),
            "packs": packs,
            "evidence_item_count": sum(len(p["evidence_items"]) for p in packs),
            "evidence_breakdown": {
                "palaces": sum(1 for p in packs for x in p["evidence_items"] if x["type"] == "palace"),
                "edges": sum(1 for p in packs for x in p["evidence_items"] if x["type"] == "edge"),
                "source_refs": sum(1 for p in packs for x in p["evidence_items"] if x["type"] == "source"),
            },
            "per_question_counts": {p["question_id"]: len(p["evidence_items"]) for p in packs},
        },
        "non_claims": NON_CLAIMS,
    }

    dest = REPO / args.out
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {dest}")
    print(f"fixed {covered}/{len(fixed)}  out_of_class=0  breakdown={breakdown}  "
          f"routing packs={len(packs)} evidence={out['routing']['evidence_item_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
