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
    HE_KINDS,
    binzhu,
    chong_at,
    edge,
    group_complete,
    he_at,
    lu_at,
    needs_judgment,
)
from engine.claims.condition_ir.ir import _label
from engine.facts.chart_facts import _LU, binzhu_side

NATAL = ["庚申", "戊寅", "壬子", "辛丑"]      # D.b=子：有六合(子丑)、半三合、半三会
HALF_ONLY = ["壬申", "癸卯", "丁未", "壬寅"]  # D.b=未：只有 sanhe half_mu，无六合/暗合
ANHE_ONLY = ["甲子", "丁卯", "癸卯", "庚申"]  # D.b=卯：只有 zhi_anhe
ZIHE_ONLY = ["甲子", "丙子", "丙戌", "戊子"]  # D.b=戌：只有 ganzhi_zihe（日柱自合）
FULL_SANHE = ["甲寅", "庚午", "甲戌", "丙子"]  # 寅午戌完整三合，D.b=戌


def _ctx(pillars=NATAL, gender="乾", liunian_year=None):
    facts = to_jsonable(analyze_facts(
        pillars=list(pillars), gender=gender, liunian_year=liunian_year))
    return build_context(facts)


@pytest.fixture(scope="module")
def ctx_natal():
    return _ctx()


@pytest.fixture(scope="module")
def ctx_liunian():
    return _ctx(liunian_year=2026)


# ---------------------------------------------------------------- 契约记账

def test_registry_has_44_atoms_and_new_signatures():
    assert len(ATOMS) == 44
    assert set(ATOMS) == set(SIGNATURES)
    assert SIGNATURES["lu_at"] == ((), ("gan", "at"))
    assert SIGNATURES["needs_judgment"] == (("reason",), ())
    assert "scope" in SIGNATURES["edge"][1]
    assert "exclude_god" in SIGNATURES["he_at"][1]


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
