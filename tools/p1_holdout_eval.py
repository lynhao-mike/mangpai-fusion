"""tools/p1_holdout_eval.py · P1 hold-out（T-175 冻结）→ 当前引擎事实层的召回评分器（只读）。

问题：`META/p1-holdout-answers-v1.json` 里 20 条冻结的核心做功关系（谁对谁、什么关系、谁施力），
当前引擎事实层能否表达？—— 只取 `engine.api.analyze_facts` + `compact_for_agent`
（= `engine.cli all` 默认视图）的事实，评分器不排盘、不读 `sources/` 原文，
只把答案里的 `quote`/`source_ref` 当展示字段。

产物带 `artifact` 标签（`--artifact-label`，默认 `pre_fix_baseline`）：正式 P1 用 `official_p1`，
诊断用 `post_fix_candidates` / `post_fix_hua`；标签写进 JSON 的 `artifact`、MD 头与控制台标题，
防止把旧基线数字当修复后结果引用。
本工具**不改** engine / 规则 / 测试 / hold-out / answers，也**不**用 hold-out 调规则。

口径（与 dev 工具 `mangpai-fusion-rethink/tools/golden_core_edge_recall.py` 同构）
-----------------------------------------------------------------------------------
1. **端点解析**：答案的 `a`/`b` 是原书字面（单字干支、十神名或地址 `Y.s`）→ 解析成本盘地址集合；
   一对多时取全部组合，任一命中即算（`_spans`：两端落在同一条 members 里且地址不同）。
   地址来源只有 `chart.pillars[].stem/branch`（天干 `ten_god`、地支 `main_ten_god`）。
2. **边召回**：`relations.edges` 里存在一条边，`members` 同时含 a、b 的地址，且 `kind` 映射一致。
3. **候选召回**：`duan_zuogong.candidates` 里存在一条候选，`members` 同时含 a、b 的地址，
   且 `relation_kind` 映射一致（比较前去掉 `sheng(main_qi)` 这类括号后缀，同 dev 的 `_kind`）。
4. **方向召回**：答案 `actor` 非空（本 hold-out 20/20）时，匹配候选的 `actor` 必须落在 a 端地址。
   五值：ok / reversed / actor_none / no_candidate / no_edge（后两者是 dev 四值在 P1 的细分：
   有边无候选 → no_candidate；边与候选皆无 → no_edge）。`actor=null` 的答案不进方向分母。
5. **分母**：主口径 = 冻结 set 的全部 `core_work_relations`（本版 20 条）；
   敏感性 = 剔除 F28 救应（H17–H20）后的 16 条。**不与 dev 33 条比较**（见 freeze 的 `no_comparison_to_dev`）。

kind 映射表（改这张表就是改尺子，须走任务卡；答案 `kind` 是四类主功，`mechanism` 是底层机械类型）
------------------------------------------------------------------------------------------------
    mechanism  边 kind                  候选 kind               说明
    制         *（不过滤）             *（不过滤）             未指明具体关系种类 → 只要两端同现（dev: 克/制未说种类→null）
    合         wuhe / liuhe           同左                    天干五合、地支六合
    冲         chong / stem_chong     同左                    地支六冲；天干相冲为 stem_chong
    刑         xing                   同左                    三刑/自刑/子卯刑
    穿         chuan                  同左                    六穿（害）
    破         po                     同左                    六破
    克         ke                     同左 + 别名             只在同层建边：支/干→支不建克边（G3）；
                                                              推得候选 `zhi_ke`/`gan_ke_zhi` 按别名视同 `ke`（T-183，只影响「克」）
    生         sheng                  同左                    sheng(main_qi) 去掉括号后缀后同名
    化         sheng                  同左                    化=被化者→化者；引擎无「化」边，化用候选 actor=化者（T-181）
    墓         （空：引擎不建墓边）     muku                    引擎只有 relations.muku 与「墓用」候选；主口径不计 muku 为边

  未登记的值一律 `ValueError`，不静默当「不过滤」——尺子不认的答案不许悄悄抬高召回。
  候选 kind 的**通用别名**（`CAND_KIND_ALIASES`）：`zhi_ke`/`gan_ke_zhi` → `ke`，与
  `sheng(main_qi)` 剥括号同类；只归一到引擎已有的机械 kind，不是按 case 特判，也不改任何 mechanism 映射。

三处必须写进报告的口径差异
--------------------------
- **墓的方向**：dev 标注把入库方写 a、库写 b（`muku:{enter:a,ku:b}`）；本 hold-out 相反
  （a = 库 = 施力方，b = 入库方）。T-178 审计判定 **4/4 `engine_wrong`**：原文力向是库→入库方，
  引擎墓用候选应为 `members=(库,入库方)`、`actor=库`；T-179 已按此修复，命中候选时应 `ok`。
  评分器按答案 actor 比引擎 actor，逻辑不变；修复前出现 `reversed` 是引擎缺陷，不是口径对立。
- **化的方向**：T-180 审计判定 **4/4 `engine_wrong`**：化 = 被化者→化者，化者=受生端（与「生」相反），
  答案 `a/actor` 取化者。引擎无「化」kind，`化`→`sheng` 只是 kind 映射（候选召回用），**不等于 actor 等价**。
  T-181 已把 `mode=化用` 候选改为 `members=(化者,被化者)`、`actor=化者`，H09–H11 应 `ok`；
  H12（财→杀）不被化用谓词识别，仍 `reversed`（`known_gap`，不扩类、不剔分母）。
- **muku 等价口径**：dev 工具把 `relations.muku` 入库算作「边与候选都能表达」。主口径按任务卡
  §2.2 只认 `relations.edges` + `candidates`；另报 `muku_equivalent_edge_recall` 作敏感性，
  供中枢裁决，二者都在产物里，不混算。

用法
----
    python -m tools.p1_holdout_eval --holdout META/p1-holdout-v1.json --answers META/p1-holdout-answers-v1.json
    python -m tools.p1_holdout_eval ... --artifact-label official_p1   # 正式 P1；诊断用 post_fix_*
    python -m tools.p1_holdout_eval ... --json          # stdout 打完整 JSON
    python -m tools.p1_holdout_eval ... --out-json <p> --out-md <p>   # 显式写产物（已存在须 --force）

**不传 `--out-json` / `--out-md` 时只打 stdout，不写任何文件**（E-08：默认不再覆盖冻结基线
`META/p1-holdout-baseline-v1.*`）。显式传路径才写；目标已存在且未传 `--force` 时拒绝覆盖。
产物**不含时间戳**，同一引擎同一 `--artifact-label` 两次运行逐字节一致。
`--artifact-label` 默认 `pre_fix_baseline`；正式 P1 用 `official_p1`，诊断用 `post_fix_candidates` /
`post_fix_hua`。标签写进 JSON 的 `artifact`、MD 头与控制台标题。
退出码：0 = 20 条全部评到；2 = 输入不合口径（case 不匹配 / 端点未解析 / kind 未登记）或目标已存在未 --force。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.api.facade import analyze_facts, compact_for_agent

DEFAULT_HOLDOUT = ROOT / "META" / "p1-holdout-v1.json"
DEFAULT_ANSWERS = ROOT / "META" / "p1-holdout-answers-v1.json"
#: 冻结基线产物路径。只作文档/测试引用；CLI 默认**不写**（E-08），要写须显式 `--out-json/--out-md`。
DEFAULT_OUT_JSON = ROOT / "META" / "p1-holdout-baseline-v1.json"
DEFAULT_OUT_MD = ROOT / "META" / "p1-holdout-baseline-v1.md"

#: 产物标签：默认 pre-fix 基线；正式 P1 用 official_p1，post-fix 诊断用 post_fix_*。
DEFAULT_ARTIFACT_LABEL = "pre_fix_baseline"

SCHEMA_VERSION = "p1-holdout-baseline/v1"

GAN = frozenset("甲乙丙丁戊己庚辛壬癸")
ZHI = frozenset("子丑寅卯辰巳午未申酉戌亥")
ADDR_RE = re.compile(r"^[YMDH]\.[sb]$")

#: 引擎只认 乾/坤；H17/H18 原书未注明性别。freeze 决定「P1 方向召回不依赖性别」，
#: 故未注明按乾起盘，并在逐例行里记 `gender_used`，不隐去。
GENDER_FALLBACK = {"未注明": "乾"}

#: 十神→地址多解：单字十神名或其分组按 dev 标注规则宽松展开（官=正官/七杀 等）。
TEN_GOD_GROUPS: dict[str, tuple[str, ...]] = {
    "官": ("正官", "七杀"),
    "官杀": ("正官", "七杀"),
    "杀": ("七杀",),
    "财": ("正财", "偏财"),
    "印": ("正印", "偏印"),
    "枭": ("偏印",),
    "比劫": ("比肩", "劫财"),
    "食伤": ("食神", "伤官"),
    "日主": ("日主",),
}

MECHANISM_ORDER = ("制", "合", "冲", "刑", "穿", "破", "克", "生", "化", "墓")

#: 答案 mechanism（底层机械类型）→ 引擎边 kind。None = 不过滤 kind。
MECHANISM_TO_EDGE_KINDS: dict[str, frozenset[str] | None] = {
    "制": None,
    "合": frozenset({"wuhe", "liuhe"}),
    "冲": frozenset({"chong", "stem_chong"}),
    "刑": frozenset({"xing"}),
    "穿": frozenset({"chuan"}),
    "破": frozenset({"po"}),
    "克": frozenset({"ke"}),
    "生": frozenset({"sheng"}),
    "化": frozenset({"sheng"}),
    "墓": frozenset(),
}

#: 答案 mechanism → 引擎候选 relation_kind（与边同表，仅 墓 换成引擎的「墓用」muku 候选）。
MECHANISM_TO_CAND_KINDS: dict[str, frozenset[str] | None] = {
    **MECHANISM_TO_EDGE_KINDS,
    "墓": frozenset({"muku"}),
}

#: mechanism 缺失时的兜底：四类主功 kind。救应不是机械关系类型，按不过滤处理（本版 20/20 都有 mechanism）。
KIND_TO_EDGE_KINDS: dict[str, frozenset[str] | None] = {
    "制": None,
    "化": frozenset({"sheng"}),
    "墓": frozenset(),
    "救应": None,
}
KIND_TO_CAND_KINDS: dict[str, frozenset[str] | None] = {
    "制": None,
    "化": frozenset({"sheng"}),
    "墓": frozenset({"muku"}),
    "救应": None,
}

#: F28 救应子集（`META/p1-holdout-freeze-v1.json` 的 `subsets.f28_rescue_cases`）：主口径 20，敏感性 16。
F28_RESCUE_CASES = frozenset({"P1-H17", "P1-H18", "P1-H19", "P1-H20"})

DIRECTIONS = ("ok", "reversed", "actor_none", "no_candidate", "no_edge")


# ── 输入与事实 ──────────────────────────────────────────────────────────────

def _chars(text: str) -> str:
    return "".join(ch for ch in str(text) if not ch.isspace())


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _display_path(path: Path) -> str:
    """仓库内路径写相对形式，保证换 cwd 重跑仍逐字节一致。"""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def gender_for(gender: str) -> str:
    text = str(gender).strip()
    return GENDER_FALLBACK.get(text, text)


def facts_for(pillars: str, gender: str) -> dict[str, Any]:
    return compact_for_agent(analyze_facts(pillars=pillars.split(), gender=gender_for(gender)))


# ── 端点解析 ────────────────────────────────────────────────────────────────

def addr_table(facts: dict[str, Any]) -> list[dict[str, str]]:
    """每个原局地址的 字 + 十神（天干取 ten_god，地支取 main_ten_god），同 dev。"""
    rows = []
    for p in facts["chart"]["pillars"]:
        s, b = p["stem"], p["branch"]
        rows.append({"addr": s["addr"], "char": s["char"], "ten_god": s.get("ten_god", "")})
        rows.append({"addr": b["addr"], "char": b["char"], "ten_god": b.get("main_ten_god", "")})
    return rows


def resolve(spec: str, table: list[dict[str, str]]) -> set[str]:
    """端点 → 地址集合。优先级：地址 > 单字干支 > 十神（含分组展开）。

    一对多时返回全部地址（重复字、多个同十神位都会多解），由 `_spans` 取任意组合。
    """
    text = str(spec).strip()
    if ADDR_RE.match(text):
        return {text} & {r["addr"] for r in table}
    if text in GAN or text in ZHI:
        return {r["addr"] for r in table if r["char"] == text}
    gods = TEN_GOD_GROUPS.get(text, (text,))
    return {r["addr"] for r in table if r["ten_god"] in gods}


#: 推得关系的证据 kind → 引擎已有机械 kind（T-183）。与 `sheng(main_qi)` 剥括号是同一套归一：
#: 只把「支克支 / 干克支」的推得候选归到 `ke`，因此只影响 mechanism=克 的匹配，不改合/冲/穿/刑/墓。
CAND_KIND_ALIASES: dict[str, str] = {"zhi_ke": "ke", "gan_ke_zhi": "ke"}


def base_kind(raw: str) -> str:
    """候选 kind 比对口径：先剥 `sheng(main_qi)` 括号后缀，再按通用别名归到引擎机械 kind。"""
    base = str(raw).split("(")[0]
    return CAND_KIND_ALIASES.get(base, base)


def _spans(members: list[str], a: set[str], b: set[str]) -> bool:
    ms = set(members)
    return any(x in ms and y in ms and x != y for x in a for y in b)


def kind_filters(rel: dict[str, Any]) -> tuple[frozenset[str] | None, frozenset[str] | None, str]:
    """答案 → (边 kind 过滤, 候选 kind 过滤, 依据)。None = 不过滤。"""
    mechanism = rel.get("mechanism")
    if mechanism in MECHANISM_TO_EDGE_KINDS:
        return MECHANISM_TO_EDGE_KINDS[mechanism], MECHANISM_TO_CAND_KINDS[mechanism], f"mechanism:{mechanism}"
    kind = rel.get("kind")
    if kind in KIND_TO_EDGE_KINDS:
        return KIND_TO_EDGE_KINDS[kind], KIND_TO_CAND_KINDS[kind], f"kind:{kind}"
    raise ValueError(
        f"未登记的 kind/mechanism：kind={kind!r} mechanism={mechanism!r}；"
        "新值须先在 MECHANISM_TO_*_KINDS 登记（改尺子走任务卡）"
    )


def _kind_ok(kinds: frozenset[str] | None, raw: str) -> bool:
    return kinds is None or base_kind(raw) in kinds


# ── 单条关系评分 ────────────────────────────────────────────────────────────

def _direction(candidates: list[dict[str, Any]], edges: list[dict[str, Any]],
               a: set[str], b: set[str]) -> str:
    """方向：候选 actor 落在 a 端 = ok；落在 b 端 = reversed；有候选但 actor 空/不在两端 = actor_none。"""
    actors = [c.get("actor") for c in candidates]
    if any(x in a for x in actors if x):
        return "ok"
    if any(x in b for x in actors if x):
        return "reversed"
    if candidates:
        return "actor_none"
    if edges:
        return "no_candidate"
    return "no_edge"


def score_relation(rel: dict[str, Any], facts: dict[str, Any], *, case_id: str,
                   category: str = "", gender_used: str = "") -> dict[str, Any]:
    """一条 `core_work_relations[]` → 逐例行（edge_hit / candidate_hit / direction）。"""
    table = addr_table(facts)
    a_raw, b_raw = str(rel["a"]).strip(), str(rel["b"]).strip()
    a, b = resolve(a_raw, table), resolve(b_raw, table)
    edge_kinds, cand_kinds, basis = kind_filters(rel)
    row: dict[str, Any] = {
        "case_id": case_id,
        "category": category,
        "a": a_raw,
        "b": b_raw,
        "kind": rel.get("kind"),
        "mechanism": rel.get("mechanism"),
        "actor": rel.get("actor"),
        "gender_used": gender_used,
        "quote": rel.get("quote", ""),
        "source_ref": rel.get("source_ref", ""),
        "a_addrs": sorted(a),
        "b_addrs": sorted(b),
        "kind_basis": basis,
        "kind_filter": "any" if edge_kinds is None else sorted(edge_kinds),
    }
    actor_stated = bool(rel.get("actor"))
    row["actor_stated"] = actor_stated
    row["actor_consistent"] = bool(a) and resolve(str(rel["actor"]), table) <= a if actor_stated else True

    if not a or not b or (a == b and len(a) == 1):
        row.update(status="endpoint_absent", edge_hit=False, candidate_hit=False,
                   edge_ids=[], candidates=[], muku_hits=[], direction="no_edge")
        return row

    edges = [e for e in facts["relations"].get("edges", [])
             if _kind_ok(edge_kinds, e["kind"]) and _spans(e["members"], a, b)]
    candidates = [c for c in facts["duan_zuogong"].get("candidates", [])
                  if _kind_ok(cand_kinds, c["relation_kind"]) and _spans(c["members"], a, b)]

    # 墓：hold-out 记 a = 库（施力方）、b = 入库方（T-178）；muku 只作敏感性口径，不进主口径。
    muku_hits: list[str] = []
    if rel.get("mechanism") == "墓" or rel.get("kind") == "墓":
        for m in facts["relations"].get("muku") or []:
            if m["addr"] in a:
                muku_hits += [f'{c["addr"]}->{m["addr"]}' for c in m.get("candidates", [])
                              if c["addr"] in b and not c.get("excluded")]

    row.update(
        status="scored",
        edge_ids=[e["id"] for e in edges],
        candidates=[{"kind": c["relation_kind"], "members": list(c["members"]), "actor": c.get("actor")}
                    for c in candidates],
        muku_hits=muku_hits,
        edge_hit=bool(edges),
        candidate_hit=bool(candidates),
        direction=_direction(candidates, edges, a, b),
    )
    return row


# ── 汇总 ────────────────────────────────────────────────────────────────────

def pct(n: int, d: int) -> float | None:
    return None if d == 0 else round(100.0 * n / d, 1)


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """一组逐例行 → 分子/分母/百分比/方向分布 + muku 等价口径（敏感性，不与主口径混算）。"""
    scored = [r for r in rows if r["status"] == "scored"]
    directed = [r for r in scored if r["actor_stated"]]
    n_edge = sum(1 for r in scored if r["edge_hit"])
    n_cand = sum(1 for r in scored if r["candidate_hit"])
    n_dir = sum(1 for r in directed if r["direction"] == "ok")
    n_muku = sum(1 for r in scored if r["edge_hit"] or r["muku_hits"])
    breakdown: dict[str, int] = {}
    for r in directed:
        breakdown[r["direction"]] = breakdown.get(r["direction"], 0) + 1
    return {
        "scored": len(scored),
        "directed": len(directed),
        "edge_recall": f"{n_edge}/{len(scored)}",
        "edge_recall_pct": pct(n_edge, len(scored)),
        "candidate_recall": f"{n_cand}/{len(scored)}",
        "candidate_recall_pct": pct(n_cand, len(scored)),
        "directed_recall": f"{n_dir}/{len(directed)}",
        "directed_recall_pct": pct(n_dir, len(directed)),
        "direction_breakdown": dict(sorted(breakdown.items())),
        "muku_equivalent_edge_recall": f"{n_muku}/{len(scored)}",
        "muku_equivalent_edge_recall_pct": pct(n_muku, len(scored)),
    }


def _kind_map_view(mapping: dict[str, frozenset[str] | None]) -> dict[str, Any]:
    return {k: ("any" if mapping[k] is None else sorted(mapping[k])) for k in MECHANISM_ORDER}


def run(holdout_path: Path | str = DEFAULT_HOLDOUT,
        answers_path: Path | str = DEFAULT_ANSWERS,
        artifact_label: str = DEFAULT_ARTIFACT_LABEL) -> dict[str, Any]:
    """跑完一整个 hold-out，返回可 JSON 化的结果（不含时间戳，逐字节可复现）。

    `artifact_label` 写进结果的 `artifact`，用于区分 pre-fix 基线 / 正式 P1 / post-fix 诊断；
    评分逻辑与分母不随标签变化。
    """
    holdout_path, answers_path = Path(holdout_path), Path(answers_path)
    holdout = json.loads(holdout_path.read_text(encoding="utf-8"))
    answers = json.loads(answers_path.read_text(encoding="utf-8"))

    blind = {c["case_id"]: c for c in holdout["cases"]}
    if len(blind) != len(holdout["cases"]):
        raise ValueError("holdout 里 case_id 重复")
    ans_ids = [c["case_id"] for c in answers["cases"]]
    if len(set(ans_ids)) != len(ans_ids):
        raise ValueError("answers 里 case_id 重复")
    missing = sorted(set(ans_ids) - set(blind))
    if missing:
        raise ValueError(f"answers 有、holdout 无：{missing}")

    cache: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    for ans in answers["cases"]:
        case_id = ans["case_id"]
        case = blind[case_id]
        if _chars(case["four_pillars"]) != _chars(ans["four_pillars"]):
            raise ValueError(f"{case_id}: 四柱与 holdout 不一致")
        gender_used = gender_for(case.get("gender") or ans.get("gender", ""))
        if case_id not in cache:
            cache[case_id] = facts_for(case["four_pillars"], gender_used)
        for rel in ans.get("core_work_relations") or []:
            rows.append(score_relation(rel, cache[case_id], case_id=case_id,
                                       category=ans.get("category", ""), gender_used=gender_used))

    absent = sorted({r["case_id"] for r in rows if r["status"] != "scored"})
    primary = summarize(rows)
    sensitivity = summarize([r for r in rows if r["case_id"] not in F28_RESCUE_CASES])
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "task": "T-177",
        "artifact": artifact_label,
        "note": ("当前引擎的评分产物，口径标签见 `artifact`（默认 pre_fix_baseline = 修复前基线）；"
                 "三处修复落地后必须整体重跑覆盖，本表数字不得跨标签当修复后结果引用。"
                 "分母是冻结 hold-out 的关系数，不是 dev 33 条。"),
        "inputs": {
            "holdout": _display_path(holdout_path),
            "answers": _display_path(answers_path),
            "sha256": {"holdout": _sha256(holdout_path), "answers": _sha256(answers_path)},
            "cases": len(blind),
            "relations": len(rows),
        },
        "scoring": {
            "mechanism_to_edge_kinds": _kind_map_view(MECHANISM_TO_EDGE_KINDS),
            "mechanism_to_candidate_kinds": _kind_map_view(MECHANISM_TO_CAND_KINDS),
            "kind_enum_fallback": {k: ("any" if KIND_TO_EDGE_KINDS[k] is None else sorted(KIND_TO_EDGE_KINDS[k]))
                                   for k in KIND_TO_EDGE_KINDS},
            "direction_rule": ("候选 actor ∈ a 端地址 = ok；∈ b 端 = reversed；候选非空但 actor 为空或不在两端 "
                               "= actor_none；有边无候选 = no_candidate；边与候选皆无 = no_edge"),
            "muku_convention": ("engine/muku/ 与 dev 相反：本 hold-out a = 库（施力方）、b = 入库方；"
                                "muku 只进 muku_equivalent_edge_recall 敏感性，不进主口径"),
            "no_dev_comparison": True,
            "dev_33_not_used": True,
        },
        "denominator_check": {
            "relations": len(rows),
            "scored": primary["scored"],
            "endpoint_absent": absent,
            "ok": not absent,
        },
        "primary": primary,
        "sensitivity_exclude_f28_rescue": sensitivity,
        "sensitivity_denominator": len([r for r in rows if r["case_id"] not in F28_RESCUE_CASES]),
        "cases": rows,
    }
    return result


# ── Markdown ────────────────────────────────────────────────────────────────

def _pct_text(value: float | None) -> str:
    return "—" if value is None else f"{value}%"


def _row_note(row: dict[str, Any]) -> str:
    if row["status"] != "scored":
        return "端点未解析到地址（不进分母）"
    bits = ["边 " + ", ".join(row["edge_ids"]) if row["edge_hit"] else "无边"]
    if row["candidates"]:
        actors = ",".join(c["actor"] or "null" for c in row["candidates"])
        bits.append(f"候选 {len(row['candidates'])} 条 actor={actors}")
    else:
        bits.append("无候选")
    if row["muku_hits"]:
        bits.append("muku " + ",".join(row["muku_hits"]))
    return "；".join(bits)


def _ids_text(case_ids: list[str]) -> str:
    return "、".join(f"`{c}`" for c in case_ids) if case_ids else "无"


def _address_ambiguity(rows: list[dict[str, Any]]) -> list[str]:
    out = []
    for r in rows:
        parts = []
        if len(r["a_addrs"]) > 1:
            parts.append(f"a={r['a']}→{','.join(r['a_addrs'])}")
        if len(r["b_addrs"]) > 1:
            parts.append(f"b={r['b']}→{','.join(r['b_addrs'])}")
        if len(r["a_addrs"]) and len(r["b_addrs"]) and r["a"] == r["b"]:
            parts.append("a/b 同字")
        if parts:
            out.append(f"- `{r['case_id']}`：{'；'.join(parts)}")
    return out


def render_md(result: dict[str, Any]) -> str:
    primary = result["primary"]
    sens = result["sensitivity_exclude_f28_rescue"]
    rows = result["cases"]
    inputs = result["inputs"]
    ambiguous = _address_ambiguity(rows)
    reversed_muku = [r["case_id"] for r in rows if r["mechanism"] == "墓" and r["direction"] == "reversed"]
    reversed_hua = [r["case_id"] for r in rows if r["mechanism"] == "化" and r["direction"] == "reversed"]
    lines = [
        "# P1 hold-out 评分（T-177）",
        "",
        f"- artifact：`{result['artifact']}`（默认 `pre_fix_baseline` 即 pre-fix 基线；正式 P1 用 `official_p1`，"
        "诊断用 `post_fix_candidates` / `post_fix_hua`）",
        f"- 生成器：`python -m tools.p1_holdout_eval --holdout {inputs['holdout']} --answers {inputs['answers']} "
        f"--artifact-label {result['artifact']}`",
        f"- 输入 sha256：holdout `{inputs['sha256']['holdout']}`；answers `{inputs['sha256']['answers']}`"
        "（与 `META/p1-holdout-freeze-v1.json` 对照）",
        f"- 规模：{inputs['cases']} 例 / {inputs['relations']} 条 `core_work_relations`",
        "- 口径：冻结 hold-out 的全部关系；**不是** dev 33 条，不做跨集比较（freeze `no_comparison_to_dev`）",
        "- 性质：同一 `artifact` 标签内可比；三处修复落地后必须整体重跑覆盖本表，本表数字不得跨标签当修复后结果引用。",
        "",
        "## 1. 主口径（20 条）",
        "",
        "| 指标 | 分子/分母 | 百分比 |",
        "|---|---|---|",
        f"| 边召回 `edge_recall` | {primary['edge_recall']} | {_pct_text(primary['edge_recall_pct'])} |",
        f"| 候选召回 `candidate_recall` | {primary['candidate_recall']} | {_pct_text(primary['candidate_recall_pct'])} |",
        f"| 方向召回 `directed_recall` | {primary['directed_recall']} | {_pct_text(primary['directed_recall_pct'])} |",
        f"| 评到（scored） | {primary['scored']}/{inputs['relations']} | — |",
        f"| 方向分母（actor 非空） | {primary['directed']} | — |",
        "",
        "方向分布（分母 "
        f"{primary['directed']}）：" + "、".join(f"`{k}` {v}" for k, v in primary["direction_breakdown"].items()),
        "",
        "方向定义：`ok` = 匹配候选的 `actor` 落在 a 端地址；`reversed` = 落在 b 端；`actor_none` = 有候选但 "
        "`actor` 空或不在两端；`no_candidate` = 有边无候选；`no_edge` = 边与候选皆无。",
        "",
        "## 2. 敏感性：剔除 F28 救应（16 条，H17–H20）",
        "",
        "| 指标 | 分子/分母 | 百分比 |",
        "|---|---|---|",
        f"| 边召回 | {sens['edge_recall']} | {_pct_text(sens['edge_recall_pct'])} |",
        f"| 候选召回 | {sens['candidate_recall']} | {_pct_text(sens['candidate_recall_pct'])} |",
        f"| 方向召回 | {sens['directed_recall']} | {_pct_text(sens['directed_recall_pct'])} |",
        f"| 评到（scored） | {sens['scored']}/{result['sensitivity_denominator']} | — |",
        "",
        f"muku 等价边召回（dev 把 `relations.muku` 入库当成边；**仅敏感性**，不进主口径）："
        f"20 条 {primary['muku_equivalent_edge_recall']}（{_pct_text(primary['muku_equivalent_edge_recall_pct'])}）、"
        f"16 例 {sens['muku_equivalent_edge_recall']}（{_pct_text(sens['muku_equivalent_edge_recall_pct'])}）。",
        "",
        "## 3. 逐例（20 条）",
        "",
        "| case | 类 | a→b | mechanism / kind | 边 | 候选 | 方向 | 说明 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['case_id']}` | {r['category']} | {r['a']}→{r['b']} | {r['mechanism']} / {r['kind']} "
            f"| {'✓' if r['edge_hit'] else '✗'} | {'✓' if r['candidate_hit'] else '✗'} "
            f"| {r['direction']} | {_row_note(r)} |"
        )
    lines += [
        "",
        "## 4. kind 映射与口径风险",
        "",
        "映射表（`mechanism` 是底层机械类型；未登记的 kind/mechanism 一律报错，不静默当不过滤）：",
        "",
        "| mechanism | 边 kind | 候选 kind |",
        "|---|---|---|",
    ]
    for mech in MECHANISM_ORDER:
        edge = result["scoring"]["mechanism_to_edge_kinds"][mech]
        cand = result["scoring"]["mechanism_to_candidate_kinds"][mech]
        lines.append(f"| {mech} | {'不过滤' if edge == 'any' else ('无' if not edge else '/'.join(edge))} "
                     f"| {'不过滤' if cand == 'any' else ('无' if not cand else '/'.join(cand))} |")
    lines += [
        "",
        "风险与歧义（写死口径，改即改尺子）：",
        "",
        "1. **`制` 不过滤 kind**：原书只说「制」未说种类时，engine 的 chong/chuan/ke/liuhe 都可能承载；"
        "若改判为只认 `ke`，主口径边召回会下降（逐例表里 `kind_filter=any` 的行就是受这条影响的）。",
        "2. **`墓` 不是边**：engine 不建墓边，只有 `relations.muku` 与「墓用」muku 候选。主口径按任务卡 §2.2"
        " 只认 `edges`，故 墓 4 例边召回恒为 0；dev 工具的 muku 等价口径见 §2，二者不混算。",
        "3. **`墓` 方向（T-178 审计 4/4 `engine_wrong`）**：本 hold-out 的 `a` 是库（施力方）、`b` 是入库方；"
        "engine 墓用候选应为 `members=(库,入库方)`、`actor=库`，T-179 已按此修复，命中候选时应 `ok`。"
        f"修复前命中候选为 `reversed`（本版：{_ids_text(reversed_muku)}），那是引擎缺陷，不是口径对立。",
        "4. **`化` 只能借 `sheng`（T-180 审计 4/4 `engine_wrong`）**：engine 无「化」边，`化`→`sheng` 只是"
        " kind 映射，**不是 actor 等价**；化 = 被化者（生端）→ 化者（受生端），答案 `a/actor` 取化者。"
        "T-181 已把 `mode=化用` 候选修为 `(化者,被化者)`、`actor=化者`，H09–H11 应 `ok`；"
        "H12（财→杀）仍 `reversed`（`known_gap`，不扩类、不剔分母；"
        f"本版 `reversed`：{_ids_text(reversed_hua)}）。",
        "5. **方向只用候选的 actor**：`relations.edges` 无 actor 字段（G2：冲/刑/穿/破不设方向）；"
        "故边命中不等于方向可判，方向分母仍按答案 actor 非空计。",
        "6. **地址多解**：单字干支或十神在不同柱重复出现时解析成多个地址，任一组合命中即算；"
        "本版逐例多解如下（会抬高召回上限，属必要条件检验）：",
        "",
    ]
    lines += ambiguous or ["- （无）"]
    lines += [
        "",
        "7. **性别**：H17/H18 原书未注明性别，engine 只认 乾/坤，按乾起盘（`gender_used` 逐例可见）；"
        "P1 评的是原局关系，方向召回不依赖性别。",
        "",
        "## 5. 复跑",
        "",
        "```bash",
        "python -m tools.p1_holdout_eval --holdout META/p1-holdout-v1.json --answers META/p1-holdout-answers-v1.json"
        " \\",
        "    --out-json <p.json> --out-md <p.md> --artifact-label <label>   # 显式写产物；已存在须 --force",
        "python -m tools.p1_holdout_eval ... --json   # 只打 stdout，不写盘（E-08 默认）",
        "```",
        "",
        "同一引擎两次运行产物逐字节一致（无时间戳、地址集合排序、case 顺序取 answers 文件顺序）。",
        "",
    ]
    return "\n".join(lines)


# ── CLI ─────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--holdout", type=Path, default=DEFAULT_HOLDOUT)
    ap.add_argument("--answers", type=Path, default=DEFAULT_ANSWERS)
    ap.add_argument("--out-json", type=Path, default=None,
                    help="JSON 产物路径；不传则只打 stdout，不写 META 冻结基线（E-08）")
    ap.add_argument("--out-md", type=Path, default=None,
                    help="Markdown 产物路径；不传则只打 stdout，不写 META 冻结基线（E-08）")
    ap.add_argument("--force", action="store_true",
                    help="允许覆盖已存在的 --out-json/--out-md 目标（默认拒绝，E-08）")
    ap.add_argument("--artifact-label", default=DEFAULT_ARTIFACT_LABEL,
                    help="产物标签，写进 JSON 的 artifact 与控制台标题（默认 pre_fix_baseline；"
                         "正式 P1 用 official_p1，诊断用 post_fix_candidates / post_fix_hua）")
    ap.add_argument("--json", action="store_true", help="stdout 打完整 JSON（默认打一行摘要）")
    args = ap.parse_args(argv)

    existing = [p for p in (args.out_json, args.out_md) if p is not None and p.exists()]
    if existing and not args.force:
        print("[p1_holdout_eval] 目标已存在，拒绝覆盖（确认覆盖请加 --force）："
              + "；".join(str(p) for p in existing), file=sys.stderr)
        return 2

    try:
        result = run(args.holdout, args.answers, artifact_label=args.artifact_label)
    except (ValueError, OSError) as exc:
        print(f"[p1_holdout_eval] 输入不合口径：{exc}", file=sys.stderr)
        return 2

    payload = json.dumps(result, ensure_ascii=False, indent=1) + "\n"
    written: list[Path] = []
    if args.out_json is not None:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(payload, encoding="utf-8")
        written.append(args.out_json)
    if args.out_md is not None:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(render_md(result), encoding="utf-8")
        written.append(args.out_md)

    primary = result["primary"]
    if args.json:
        print(payload, end="")
    else:
        print(f"P1 hold-out {result['artifact']}（{result['inputs']['relations']} 条）："
              f"edge {primary['edge_recall']} ({_pct_text(primary['edge_recall_pct'])}) · "
              f"candidate {primary['candidate_recall']} ({_pct_text(primary['candidate_recall_pct'])}) · "
              f"directed {primary['directed_recall']} ({_pct_text(primary['directed_recall_pct'])})")
        print(f"方向分布：{primary['direction_breakdown']}")
        print("写盘：" + "；".join(str(p) for p in written) if written
              else "未写盘：未传 --out-json/--out-md（只打 stdout）")

    check = result["denominator_check"]
    if not check["ok"]:
        print(f"[p1_holdout_eval] 端点未解析：{check['endpoint_absent']}，数量未评满，退出 2", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
