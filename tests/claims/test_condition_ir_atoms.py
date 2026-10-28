"""T-142 · 条件原子层回归（契约 23 §4，ADR-007 D3 / D5 / D12）。

覆盖六件事：
1. 原局原子隔离岁运边（默认只扫 scope == "natal"）；`edge` 可用 `scope` 查岁运边。
2. `he_at` 收窄：只认六合 / 地支暗合，排除三合三会的半局与拱局、完整局、日柱自合。
3. `binzhu` 读事实（做功候选 binzhu 读数 / 事实层纯位置函数），不再恒返回 unknown。
4. 新增 `lu_at`：某天干的禄支是否落在指定/任一地支，禄表与 `chart_facts._LU` 一致。
5. 新增 `needs_judgment`：恒 unknown，使 `True AND Unknown = Unknown`、`False AND Unknown = False`。
6. `_label` 支持 all / any / not 组合节点，不再输出 `?()`。
"""
from __future__ import annotations

import pytest

from engine.api import analyze_facts, to_jsonable
from engine.claims.condition_ir import ATOMS, SIGNATURES, build_context, evaluate, evaluate_claim
from engine.claims.condition_ir.atoms import (
    DUO_MIN,
    GUA_MAX,
    HE_KINDS,
    STRONG_MIN,
    YUANSHEN,
    binzhu,
    can_control,
    chong_at,
    chong_kai_muku,
    dayun_present,
    edge,
    group_complete,
    he_at,
    liunian_present,
    lu_at,
    needs_judgment,
    sanhe_with_suiyun,
    suiyun_arrives,
    suiyun_edge,
)
from engine.claims.condition_ir.ir import _label
from engine.facts.chart_facts import _LU, binzhu_side

NATAL = ["庚申", "戊寅", "壬子", "辛丑"]      # D.b=子：有六合(子丑)、半三合、半三会
HALF_ONLY = ["壬申", "癸卯", "丁未", "壬寅"]  # D.b=未：只有 sanhe half_mu，无六合/暗合
ANHE_ONLY = ["甲子", "丁卯", "癸卯", "庚申"]  # D.b=卯：只有 zhi_anhe
ZIHE_ONLY = ["甲子", "丙子", "丙戌", "戊子"]  # D.b=戌：只有 ganzhi_zihe（日柱自合）
FULL_SANHE = ["甲寅", "庚午", "甲戌", "丙子"]  # 寅午戌完整三合，D.b=戌


def _ctx(pillars=NATAL, gender="乾", liunian_year=None, dayun_index=None):
    facts = to_jsonable(analyze_facts(
        pillars=list(pillars), gender=gender,
        liunian_year=liunian_year, dayun_index=dayun_index))
    return build_context(facts)


@pytest.fixture(scope="module")
def ctx_natal():
    return _ctx()


@pytest.fixture(scope="module")
def ctx_liunian():
    return _ctx(liunian_year=2026)


# ---------------------------------------------------------------- 契约记账

def test_registry_has_46_atoms_and_new_signatures():
    assert len(ATOMS) == 46
    assert set(ATOMS) == set(SIGNATURES)
    assert SIGNATURES["lu_at"] == ((), ("gan", "at"))
    assert SIGNATURES["needs_judgment"] == (("reason",), ())
    assert "scope" in SIGNATURES["edge"][1]
    assert "exclude_god" in SIGNATURES["he_at"][1]
    # v1.2（T-145）
    assert SIGNATURES["suiyun_edge"] == (("type", "at"), ("scope",))
    assert SIGNATURES["sanhe_with_suiyun"] == ((), ("zhi_set",))
    assert SIGNATURES["chong_kai_muku"] == ((), ("zhi", "year"))
    assert SIGNATURES["suiyun_arrives"] == (("at",), ("via",))
    assert SIGNATURES["can_control"] == (("actor", "target"), ())


# ---------------------------------------------------------------- ① 岁运隔离

def test_natal_atoms_ignore_suiyun_edges(ctx_natal, ctx_liunian):
    # 2026 = 丙午，午冲子：岁运层确有 chong(D.b, LN2026.b)
    assert chong_at(ctx_natal, {"at": "D.b"}).value is False
    assert chong_at(ctx_liunian, {"at": "D.b"}).value is False  # 原局结论不变
    found = edge(ctx_liunian, {"type": "chong", "scope": "liunian"})
    assert found.value is True
    assert found.bindings["edge_id"].startswith("e")
    assert edge(ctx_liunian, {"type": "chong"}).bindings["edge_id"] != found.bindings["edge_id"]


def test_suiyun_scope_edges_are_invisible_to_default_queries(ctx_natal, ctx_liunian):
    scopes = {e.get("scope", "natal") for e in ctx_liunian["edges"]}
    assert {"natal", "liunian"} <= scopes
    assert len(ctx_liunian["edges"]) > len(ctx_natal["edges"])
    # group_complete 只认原局完整局；2026 与 M.b 只是半三合
    assert group_complete(ctx_liunian, {"type": "sanhe"}).value is False


# ---------------------------------------------------------------- ② he_at

def test_he_at_kinds_are_only_liuhe_and_anhe():
    assert HE_KINDS == ("liuhe", "zhi_anhe")


def test_he_at_hits_liuhe_and_ignores_half_groups_on_same_branch(ctx_natal):
    # D.b=子 同时挂着 sanhe:half_sheng 与 sanhui:partial，只认六合 子丑
    result = he_at(ctx_natal, {"at": "D.b"})
    assert result.value is True
    kinds = {e["kind"] for e in ctx_natal["edges"] if e["id"] == result.bindings["edge_id"]}
    assert kinds == {"liuhe"}


def test_he_at_rejects_half_sanhe_only():
    ctx = _ctx(HALF_ONLY)
    assert {e.get("completeness") for e in ctx["edges"]
            if e["kind"] == "sanhe" and "D.b" in (e.get("members") or [])} == {"half_mu"}
    assert he_at(ctx, {"at": "D.b"}).value is False


def test_he_at_hits_zhi_anhe():
    ctx = _ctx(ANHE_ONLY)
    result = he_at(ctx, {"at": "D.b"})
    assert result.value is True
    kinds = {e["kind"] for e in ctx["edges"] if e["id"] == result.bindings["edge_id"]}
    assert kinds == {"zhi_anhe"}


def test_he_at_rejects_ganzhi_zihe():
    ctx = _ctx(ZIHE_ONLY)
    assert "ganzhi_zihe" in {e["kind"] for e in ctx["edges"] if "D.b" in (e.get("members") or [])}
    assert he_at(ctx, {"at": "D.b"}).value is False


def test_he_at_rejects_full_sanhe_pending_adjudication():
    # 完整三合（寅午戌）是否算「被合」原文无据，暂排除；group_complete 仍能看到完整局
    ctx = _ctx(FULL_SANHE)
    assert he_at(ctx, {"at": "D.b"}).value is False
    assert group_complete(ctx, {"type": "sanhe"}).value is True


def test_he_at_with_god_and_exclude_god(ctx_natal):
    # D.b=子 与 H.b=丑 六合，丑的本气十神为官杀 → with_god 命中；排除同名十神则落空
    hit = he_at(ctx_natal, {"at": "D.b", "with_god": "官杀"})
    assert hit.value is True and hit.bindings["other"] == "H.b"
    assert he_at(ctx_natal, {"at": "D.b", "exclude_god": "官杀"}).value is False


# ---------------------------------------------------------------- ③ binzhu

def test_binzhu_reads_fact_layers(ctx_natal):
    assert binzhu(ctx_natal, {"layer": 1, "at": "D.s"}).value is True
    assert binzhu(ctx_natal, {"layer": 1, "at": "D.s", "side": "宾"}).value is False
    assert binzhu(ctx_natal, {"layer": 3, "at": "H.b", "side": "主"}).value is True
    assert binzhu(ctx_natal, {"layer": 2, "at": "Y.s", "side": "宾"}).value is True


def test_binzhu_agrees_with_fact_layer_function(ctx_natal):
    for addr in ("Y.s", "M.s", "D.s", "H.s", "Y.b", "M.b", "D.b", "H.b"):
        for layer in (1, 2, 3):
            want = binzhu_side(addr, layer)  # type: ignore[arg-type]
            got = binzhu(ctx_natal, {"layer": layer, "at": addr})
            assert got.value is True, (addr, layer)
            assert got.note.startswith(f"{addr} 第{layer}层为{want}")


def test_binzhu_layer4_needs_suiyun_nodes(ctx_natal, ctx_liunian):
    assert binzhu(ctx_natal, {"layer": 4, "side": "宾"}).value is False
    assert binzhu(ctx_liunian, {"layer": 4, "at": "LN2026.s", "side": "宾"}).value is True
    assert binzhu(ctx_liunian, {"layer": 4, "at": "D.s", "side": "主"}).value is True


def test_binzhu_never_silently_unknown(ctx_natal):
    # 旧实现恒返回 unknown；现在只对非法参数返回 unknown
    assert binzhu(ctx_natal, {"layer": 9}).value is None
    assert binzhu(ctx_natal, {"layer": 1, "side": "客"}).value is None
    assert binzhu(ctx_natal, {"layer": 1, "at": "D.s"}).value is True


# ---------------------------------------------------------------- ④ lu_at

@pytest.mark.parametrize("gan,pillars,expect_at", [
    ("甲", ["甲寅", "丙寅", "甲子", "乙丑"], "Y.b"),   # 甲禄寅
    ("甲", ["庚申", "戊寅", "壬子", "辛丑"], "M.b"),   # 甲禄寅，落在他人月支也算
    ("壬", ["癸丑", "癸亥", "辛巳", "丙申"], "M.b"),   # 壬禄亥
    ("癸", ["甲子", "丙子", "丙戌", "戊子"], "Y.b"),   # 癸禄子
])
def test_lu_at_locates_lu_branch(gan, pillars, expect_at):
    ctx = _ctx(pillars)
    result = lu_at(ctx, {"gan": gan})
    assert result.value is True
    assert result.bindings["addr"] == expect_at
    assert result.bindings["zhi"] == _LU[gan]
    assert ctx["branches"][expect_at]["char"] == _LU[gan]


@pytest.mark.parametrize("gan", list(_LU))
def test_lu_at_consistent_with_fact_table_for_all_stems(gan):
    ctx = _ctx()
    want = [a for a, b in ctx["branches"].items() if b.get("char") == _LU[gan]]
    result = lu_at(ctx, {"gan": gan})
    assert result.value is bool(want)
    if want:
        assert result.bindings["zhi"] == _LU[gan]
        assert result.bindings["addr"] in want


def test_lu_at_defaults_to_day_master_and_respects_at():
    ctx = _ctx()  # 壬子日 → 壬禄亥，盘中无亥
    assert lu_at(ctx, {}).value is False
    ctx_jia = _ctx(["甲寅", "丙寅", "甲子", "乙丑"])  # 甲子日 → 甲禄寅，年支月支都是寅
    assert lu_at(ctx_jia, {}).value is True
    assert lu_at(ctx_jia, {}).bindings["addr"] == "Y.b"
    assert lu_at(ctx_jia, {"at": "M.b"}).value is True
    assert lu_at(ctx_jia, {"at": "D.b"}).value is False  # 子不是甲的禄


def test_lu_at_unknown_inputs(ctx_natal):
    assert lu_at(ctx_natal, {"gan": "甲", "at": "D.s"}).value is None  # 禄只看地支
    assert lu_at(ctx_natal, {"gan": "?"}).value is None


# ---------------------------------------------------------------- ⑤ needs_judgment

def test_needs_judgment_is_always_unknown(ctx_natal):
    assert needs_judgment(ctx_natal, {"reason": "行运是否走财运"}).value is None
    assert needs_judgment(ctx_natal, {}).value is None  # 缺 reason 也是 unknown，但附说明


def _claim(preconditions, framework="standalone"):
    return {
        "id": "T142-JUDGE-01",
        "school": "duan",
        "domain": "财富",
        "statement": "测试用断语",
        "source_ref": {"path": "sources/duan/x.md", "line": 1},
        "falsifier": "若前置为真但结论不成立",
        "conditions_v2": {
            "preconditions": preconditions,
            "invalidators": {"any": []},
            "framework_dependency": framework,
        },
    }


TRUE_ATOM = {"atom": "day_master", "args": {"gan": "壬"}}
FALSE_ATOM = {"atom": "day_master", "args": {"gan": "甲"}}
JUDGE = {"atom": "needs_judgment", "args": {"reason": "未量化：行运是否走财运"}}


def test_true_and_unknown_is_unknown(ctx_natal):
    out = evaluate({"all": [TRUE_ATOM, JUDGE]}, ctx_natal)
    assert out.value is None
    claim = evaluate_claim(_claim({"all": [TRUE_ATOM, JUDGE]}), ctx_natal)
    assert claim["state"] == "needs_fact"
    assert any("行运是否走财运" in u for u in claim["unknown_facts"])


def test_false_and_unknown_is_false(ctx_natal):
    # 未知在前、假在后，以及假在前、未知在后，都必须判假（不折叠未知，但假优先）
    for order in ([JUDGE, FALSE_ATOM], [FALSE_ATOM, JUDGE]):
        out = evaluate({"all": order}, ctx_natal)
        assert out.value is False
        claim = evaluate_claim(_claim({"all": order}), ctx_natal)
        assert claim["state"] == "rejected"


# ---------------------------------------------------------------- ⑥ _label

def test_label_renders_composition_nodes():
    assert _label({"not": {"atom": "kongwang", "args": {"at": "D.b"}}}) == "not(kongwang(at=D.b))"
    assert _label({"any": [
        {"atom": "edge", "args": {"type": "chong", "between": ["Y.b", "D.b"]}},
        {"not": {"atom": "kongwang", "args": {"at": "D.b"}}},
    ]}) == "any[edge(type=chong, between=['Y.b', 'D.b']), not(kongwang(at=D.b))]"
    assert _label({"all": [{"any": [{"atom": "day_master", "args": {"gan": "壬"}}]}]}) == \
        "all[any[day_master(gan=壬)]]"


def test_failure_labels_are_traceable(ctx_natal):
    node = {"all": [{"atom": "day_master", "args": {"gan": "甲"}}]}
    out = evaluate(node, ctx_natal)
    assert out.value is False
    assert "day_master(gan=甲)" in out.failed
    assert "?()" not in "".join(out.failed)

    neg = {"not": {"atom": "day_master", "args": {"gan": "甲"}}}
    unknown_node = {"all": [TRUE_ATOM, neg, {"atom": "needs_judgment", "args": {"reason": "缺岁运"}}]}
    out2 = evaluate(unknown_node, ctx_natal)
    assert out2.value is None
    assert any("needs_judgment" in label for label in out2.unknowns)
    assert all("?()" not in label for label in out2.unknowns)


# ---------------------------------------------------------------- ⑦ 岁运 4 原子（T-145 / ADR-007 D3）

# 标杆盘 A（段派「伤官亥冲巳，冲去夫星忌神，婚姻好」）
PLATE_A = ["癸丑", "癸亥", "辛亥", "癸巳"]
# 标杆盘 B（原文对照组：「水火力量相当，制不住夫星」）
PLATE_B = ["壬子", "乙巳", "庚子", "壬午"]


@pytest.fixture(scope="module")
def ctx_a_natal():
    return _ctx(PLATE_A, gender="坤")


@pytest.fixture(scope="module")
def ctx_a_suiyun():
    # 坤造逆排：dayun_index=1 = 甲子；2027 = 丁未。
    # 未指定 dayun_index 时事实层不建 DY 节点，因此不会有任何大运边。
    return _ctx(PLATE_A, gender="坤", liunian_year=2027, dayun_index=1)


def test_suiyun_atoms_unknown_without_context(ctx_a_natal):
    """未提供岁运 → unknown + 「未提供大运/流年上下文」，使 state = needs_fact。"""
    for fn, args in (
        (suiyun_edge, {"type": "liuhe", "at": "Y.b"}),
        (sanhe_with_suiyun, {}),
        (chong_kai_muku, {}),
        (suiyun_arrives, {"at": "Y.s"}),
    ):
        result = fn(ctx_a_natal, args)
        assert result.value is None, fn.__name__
        assert "未提供大运/流年上下文" in result.note, fn.__name__


def test_presence_atoms_are_false_not_unknown(ctx_a_natal, ctx_a_suiyun):
    """探测存在性：未提供是客观事实，给 false 而不是 unknown（第四值禁止）。"""
    assert dayun_present(ctx_a_natal, {}).value is True     # 有出生数据即可排大运
    assert liunian_present(ctx_a_natal, {}).value is False  # 未指定年份
    assert liunian_present(ctx_a_suiyun, {"year": 2027}).value is True
    assert liunian_present(ctx_a_suiyun, {"year": 2030}).value is False


def test_suiyun_edge_hits_liunian_and_binds_edge_id(ctx_a_suiyun):
    """2027 丁未：未冲丑 → liunian 层的 chong(Y.b, LN2027.b)。"""
    result = suiyun_edge(ctx_a_suiyun, {"type": "chong", "at": "Y.b"})
    assert result.value is True
    assert result.bindings["edge_id"].startswith("e")
    assert result.bindings["scope"] == "liunian"
    edge_ids = {e["id"]: e for e in ctx_a_suiyun["edges"]}
    assert edge_ids[result.bindings["edge_id"]]["kind"] == "chong"
    assert "LN2027.b" in edge_ids[result.bindings["edge_id"]]["members"]


def test_suiyun_edge_only_scans_non_natal_edges(ctx_a_suiyun):
    """原局 e011 chong(M.b,D.b) 存在，但 suiyun_edge 不得命中 natal 边。"""
    natal = [e for e in ctx_a_suiyun["edges"]
             if e.get("kind") == "chong" and e.get("scope") == "natal"]
    assert natal, "该盘应存在原局冲边，否则本测试无意义"
    for e in natal:
        for addr in e["members"]:
            got = suiyun_edge(ctx_a_suiyun, {"type": "chong", "at": addr})
            assert got.value is False or got.bindings["edge_id"] != e["id"]


def test_suiyun_edge_scope_filter(ctx_a_suiyun):
    assert suiyun_edge(ctx_a_suiyun, {"type": "liuhe", "at": "Y.b"}).bindings["scope"] == "dayun"
    assert suiyun_edge(ctx_a_suiyun, {"type": "chong", "at": "Y.b", "scope": "dayun"}).value is False
    assert suiyun_edge(ctx_a_suiyun, {"type": "chong", "at": "Y.b", "scope": "liunian"}).value is True
    assert suiyun_edge(ctx_a_suiyun, {"type": "chong", "at": "Y.b", "scope": "??"}).value is None


def test_sanhe_with_suiyun_requires_full_group(ctx_a_suiyun):
    """亥子丑：甲子运与月支亥、年支丑成完整三会（completeness=full）。"""
    result = sanhe_with_suiyun(ctx_a_suiyun, {})
    assert result.value is True
    assert result.bindings["edge_id"].startswith("e")
    full = [e for e in ctx_a_suiyun["edges"]
            if e.get("completeness") == "full" and e.get("scope") != "natal"]
    assert result.bindings["edge_id"] in {e["id"] for e in full}
    assert sanhe_with_suiyun(ctx_a_suiyun, {"zhi_set": "亥子丑"}).value is True
    assert sanhe_with_suiyun(ctx_a_suiyun, {"zhi_set": "巳午未"}).value is False


def test_chong_kai_muku_hits_suiyun_opener(ctx_a_suiyun):
    """原局丑库（Y.b）被 2027 未冲 + 丑未刑触及。"""
    result = chong_kai_muku(ctx_a_suiyun, {})
    assert result.value is True
    assert result.bindings["addr"] == "Y.b"
    opener = next(e for e in ctx_a_suiyun["edges"] if e["id"] == result.bindings["edge_id"])
    assert opener["kind"] in ("chong", "xing")
    assert opener["scope"] in ("dayun", "liunian")
    assert chong_kai_muku(ctx_a_suiyun, {"zhi": "丑"}).value is True
    assert chong_kai_muku(ctx_a_suiyun, {"zhi": "辰"}).value is False   # 盘无辰库
    assert chong_kai_muku(ctx_a_suiyun, {"year": 2027}).value is True
    assert chong_kai_muku(ctx_a_suiyun, {"year": 2030}).value is None  # 未提供该年上下文


def test_suiyun_arrives_tonglu(ctx_a_suiyun):
    """M1-D-042 通禄：原局天干癸的禄为子，甲子运地支正是子。"""
    result = suiyun_arrives(ctx_a_suiyun, {"at": "Y.s"})
    assert result.value is True
    assert result.bindings["addr"] == "Y.s"
    assert result.bindings["sui_addr"].endswith(".b")
    assert result.bindings["sui_addr"].startswith("DY")
    assert suiyun_arrives(ctx_a_suiyun, {"at": "癸"}).bindings["addr"] == "Y.s"


def test_suiyun_arrives_yuanshen_and_muku_exclusion(ctx_a_suiyun):
    """M1-D-042 现原身：巳的原身为丙戊，甲子运 / 丁未年均未见 → false。

    辰戌丑未无原身（M1-D-058 falsifiable_by）→ 丑判 false 并在 note 说明，不补造土支原身。
    """
    assert YUANSHEN["巳"] == ("丙", "戊")
    assert YUANSHEN["午"] == ("丁", "己")
    assert set(YUANSHEN) == set("寅卯巳午申酉亥子")
    assert suiyun_arrives(ctx_a_suiyun, {"at": "H.b"}).value is False
    assert "丙" in suiyun_arrives(ctx_a_suiyun, {"at": "H.b"}).note
    muku = suiyun_arrives(ctx_a_suiyun, {"at": "Y.b"})
    assert muku.value is False and "无原身" in muku.note


def test_suiyun_arrives_via_must_match_layer(ctx_a_suiyun):
    assert suiyun_arrives(ctx_a_suiyun, {"at": "Y.s", "via": "原身"}).value is None
    assert suiyun_arrives(ctx_a_suiyun, {"at": "H.b", "via": "通禄"}).value is None
    assert suiyun_arrives(ctx_a_suiyun, {"at": "Y.s", "via": "??"}).value is None
    assert suiyun_arrives(ctx_a_suiyun, {"at": "不存在"}).value is None


def test_natal_atoms_still_isolated_after_t145(ctx_a_suiyun):
    """T-142 成果回归：原局原子仍看不见岁运边。"""
    assert chong_at(ctx_a_suiyun, {"at": "Y.b"}).value is False       # 只有岁运冲丑
    assert group_complete(ctx_a_suiyun, {"type": "sanhui"}).value is False  # 完整三会只在岁运层
    natal_hui = [e for e in ctx_a_suiyun["edges"] if e.get("kind") == "sanhui"]
    # 默认 scope 命中的只能是原局边（本盘有丑亥半会），不得是完整局
    hit = edge(ctx_a_suiyun, {"type": "sanhui"})
    assert hit.value is True
    got = next(e for e in natal_hui if e["id"] == hit.bindings["edge_id"])
    assert got.get("scope", "natal") == "natal" and got.get("completeness") != "full"
    assert edge(ctx_a_suiyun, {"type": "sanhui", "scope": "dayun"}).value is True


# ---------------------------------------------------------------- ⑧ can_control（T-145 / ADR-007 D4）

def test_plate_a_controls(ctx_a_natal):
    """标杆盘 A：伤官亥冲巳，水旺得令，巳火失令孤立受克 → 制得住。"""
    result = can_control(ctx_a_natal, {"actor": "亥", "target": "巳"})
    assert result.value is True
    assert result.bindings["actor_addr"] in ("M.b", "D.b")
    assert result.bindings["target_addr"] == "H.b"
    assert "得令" in result.note and "受克" in result.note


def test_plate_a_reverse_direction_is_false(ctx_a_natal):
    """方向不可混淆：反向（火制水）必须为 false，与正判互为镜像。"""
    result = can_control(ctx_a_natal, {"actor": "巳", "target": "亥"})
    assert result.value is False
    # T-149 起先过克关系门：火不克水，note 说明「不构成制」，不再进入旺衰比较。
    assert "不构成制：火不克水" in result.note


# T-149 缺陷一（关系盲）：旧实现只比旺项/衰项计数，从不检查五行相克，对非克对也给自信的 True。
# 实测盘「丁卯 癸卯 丁卯 癸卯」上 卯(木)→丁(火) 曾返回 True（木生火，不制火）。
PLATE_NONKE = ["丁卯", "癸卯", "丁卯", "癸卯"]   # Y.b=卯木、Y.s=丁火、M.s=癸水


@pytest.mark.parametrize("actor,target,a_wx,t_wx", [
    ("Y.b", "Y.s", "木", "火"),   # 木生火，不克（旧实现判 True）
    ("M.s", "Y.b", "水", "木"),   # 水生木，不克
    ("Y.s", "M.s", "火", "水"),   # 反向相克：水克火，火不克水（旧实现判 unknown）
])
def test_can_control_requires_ke_relation(actor, target, a_wx, t_wx):
    """T-149：只有 actor 五行克 target 五行才构成制；不克是确定的否定（False），不是未知。"""
    result = can_control(_ctx(PLATE_NONKE), {"actor": actor, "target": target})
    assert result.value is False
    assert f"不构成制：{a_wx}不克{t_wx}" in result.note


def test_plate_b_strength_parity_is_false():
    """标杆盘 B：水火力量相当（水多以多旺、火以得令旺）→ 制不了，返回 False。

    T-149 修正旧判据：旧断言要求 unknown，与原文不符。原文
    MinerU_22:1812「戌辰力量相当，互相制不了」、:1824「谁也制不了谁」都是
    **确定的否定结论**，不是「不知道」；unknown 只留给地址解析失败 / 事实缺失 /
    同五行不构成对抗（docs/reviews/verdict-chatgpt6.md §1.2 与 §4.3）。
    """
    ctx_b = _ctx(PLATE_B)
    for actor, target in (("子", "巳"), ("子", "午"), ("Y.b", "M.b")):
        result = can_control(ctx_b, {"actor": actor, "target": target})
        assert result.value is False, (actor, target, result.note)
        assert "力量相当" in result.note
        assert "制不了" in result.note
    # 不允许「A 判未知而 B 判真」的错向
    assert can_control(_ctx(PLATE_A), {"actor": "亥", "target": "巳"}).value is not None


def test_can_control_note_carries_both_sides_detail():
    """判不住（含力量相当）的 note 也必须把双方根气与党势讲清楚（供 Agent 追问）。"""
    note = can_control(_ctx(PLATE_B), {"actor": "子", "target": "巳"}).note
    for token in ("制者", "被制", "旺项", "衰项", "水", "火"):
        assert token in note


def test_can_control_thresholds_are_engineering_values():
    """阈值是工程取值，必须集中可查、且不是原文数值——改动须同步 BRIEF。"""
    assert (DUO_MIN, GUA_MAX, STRONG_MIN) == (3, 1, 2)


def test_can_control_rejects_degenerate_input(ctx_a_natal):
    """unknown 只保留三种：地址解析失败、事实缺失、同五行不构成对抗。"""
    assert can_control(ctx_a_natal, {"actor": "?", "target": "巳"}).value is None   # 地址解析失败
    assert can_control(ctx_a_natal, {"actor": "亥", "target": "不存在"}).value is None
    assert can_control(ctx_a_natal, {"actor": "亥", "target": "亥"}).value is None  # 同五行不成对抗
    # 事实缺失（缺 strength.climate.wuxing_layered）→ unknown，不能降级成 False
    broken = dict(ctx_a_natal)
    broken["strength"] = {"climate": {}}
    assert can_control(broken, {"actor": "亥", "target": "巳"}).value is None
