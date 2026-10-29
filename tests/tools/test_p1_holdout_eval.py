"""tests/tools/test_p1_holdout_eval.py · T-177（T-182 同步 artifact 标签与墓/化契约）· P1 评分器合成 fixture 测试。

只测尺子，不测命理结论，也**不**读真实答案做断言（`META/p1-holdout-answers-v1.json` 只由中枢跑）：

1. 端点解析：地址 / 单字干支 / 十神 / 分组 / 一对多；
2. kind 映射：制=不过滤、化=sheng、墓=无边 + muku 候选、未登记值报错；
3. 逐例五值：全中、全不中、actor 反、无候选、无方向（actor_none）、多地址、端点不在盘；
   墓用 `(库,入库方)/actor=库` → ok；化用 `(化者,被化者)/actor=化者` → ok；H12 财→杀 `known_gap` → reversed；
4. 汇总：分母、百分比、方向分布、actor 为空不进方向分母、muku 等价口径；
5. 端到端：20/16 子集切分、两次运行逐字节一致、case 不匹配报错、CLI 退出码、
   `--artifact-label` 默认/自定义写入 JSON 与控制台标题；
6. 引擎冒烟：真实 `facts_for` 只断言不变量（不锁边数，免得修复后误红）。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import p1_holdout_eval as mod

# ── 合成 fixture（手写 engine 事实视图，不经引擎）────────────────────────────

PILLARS = [
    ("甲", "比肩", "子", "正印"),
    ("丙", "食神", "午", "伤官"),
    ("甲", "比肩", "寅", "比肩"),
    ("壬", "偏印", "戌", "偏财"),
]

#: T-180 H09 盘（癸巳 乙卯 己巳 己巳）：答案 a=巳（化者/受生端）、b=卯（被化者/生端）。
HUA09_PILLARS = [
    ("癸", "正财", "巳", "正印"),
    ("乙", "七杀", "卯", "七杀"),
    ("己", "日主", "巳", "正印"),
    ("己", "比肩", "巳", "正印"),
]

#: T-180 H12 盘（乙巳 乙酉 戊子 甲寅）：答案 a=寅（化者/受生端）、b=子（被化者/生端），财→杀。
HUA12_PILLARS = [
    ("乙", "正官", "巳", "偏印"),
    ("乙", "正官", "酉", "伤官"),
    ("戊", "日主", "子", "正财"),
    ("甲", "七杀", "寅", "七杀"),
]


def make_facts(pillars=PILLARS, edges=(), candidates=(), muku=()):
    rows = []
    for i, (stem, stem_god, branch, branch_god) in enumerate(pillars):
        head = "YMDH"[i]
        rows.append({
            "stem": {"addr": f"{head}.s", "char": stem, "ten_god": stem_god},
            "branch": {"addr": f"{head}.b", "char": branch, "main_ten_god": branch_god},
        })
    return {
        "chart": {"pillars": rows},
        "relations": {"edges": [dict(e) for e in edges], "muku": [dict(m) for m in muku]},
        "duan_zuogong": {"candidates": [dict(c) for c in candidates]},
    }


def edge(edge_id: str, kind: str, *members: str) -> dict:
    return {"id": edge_id, "kind": kind, "members": list(members)}


def cand(kind: str, *members: str, actor="__absent__", mode: str | None = None) -> dict:
    out = {"relation_kind": kind, "members": list(members)}
    if actor != "__absent__":
        out["actor"] = actor
    if mode is not None:
        out["mode"] = mode
    return out


FACTS = make_facts(
    edges=[edge("e001", "ke", "Y.s", "M.s"), edge("e002", "chong", "Y.b", "M.b")],
    candidates=[cand("ke", "Y.s", "M.s", actor="Y.s"), cand("chong", "Y.b", "M.b", actor=None)],
)


def rel(a: str, b: str, kind: str = "制", mechanism: str = "克", actor: str | None = None) -> dict:
    return {"a": a, "b": b, "kind": kind, "mechanism": mechanism,
            "actor": a if actor is None else actor,
            "quote": "合成 fixture，不是原书引文", "source_ref": "sources/duan/x.md:L1"}


# ── 1. 端点解析 ────────────────────────────────────────────────────────────

def test_resolve_addr_char_ten_god_and_group():
    table = mod.addr_table(FACTS)
    assert mod.resolve("Y.s", table) == {"Y.s"}
    assert mod.resolve("甲", table) == {"Y.s", "D.s"}        # 一字多址
    assert mod.resolve("丙", table) == {"M.s"}
    assert mod.resolve("正印", table) == {"Y.b"}             # 十神名
    assert mod.resolve("印", table) == {"H.s", "Y.b"}        # 分组展开：正印 + 偏印
    assert mod.resolve("比劫", table) == {"D.b", "D.s", "Y.s"}   # 比肩+劫财，含地支本气
    assert mod.resolve("亥", table) == set()                 # 不在盘
    assert mod.resolve("Z.z", table) == set()                # 非法地址形态落到十神分支 → 空


def test_addr_table_pairs_stem_and_branch():
    table = mod.addr_table(FACTS)
    assert len(table) == 8
    assert {"addr": "Y.b", "char": "子", "ten_god": "正印"} in table


# ── 2. kind 映射 ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("rel_in, edge_kinds, cand_kinds", [
    ({"kind": "制", "mechanism": "制"}, None, None),
    ({"kind": "制", "mechanism": "合"}, frozenset({"wuhe", "liuhe"}), frozenset({"wuhe", "liuhe"})),
    ({"kind": "化", "mechanism": "化"}, frozenset({"sheng"}), frozenset({"sheng"})),
    ({"kind": "墓", "mechanism": "墓"}, frozenset(), frozenset({"muku"})),
    ({"kind": "救应", "mechanism": "穿"}, frozenset({"chuan"}), frozenset({"chuan"})),
])
def test_kind_filters(rel_in, edge_kinds, cand_kinds):
    got_edge, got_cand, basis = mod.kind_filters(rel_in)
    assert got_edge == edge_kinds and got_cand == cand_kinds
    assert basis == f"mechanism:{rel_in['mechanism']}"


def test_kind_filters_falls_back_to_kind():
    assert mod.kind_filters({"kind": "墓", "mechanism": None}) == (
        frozenset(), frozenset({"muku"}), "kind:墓")


def test_kind_filters_rejects_unregistered_value():
    with pytest.raises(ValueError):
        mod.kind_filters({"kind": "破", "mechanism": "合体"})


def test_base_kind_strips_parenthetical_suffix():
    assert mod.base_kind("sheng(main_qi)") == "sheng"
    assert mod.base_kind("muku") == "muku"


# ── 3. 逐例五值 ────────────────────────────────────────────────────────────

def test_all_hit_direction_ok():
    row = mod.score_relation(rel("甲", "丙"), FACTS, case_id="T-01", category="制")
    assert row["status"] == "scored"
    assert row["a_addrs"] == ["D.s", "Y.s"]                  # 一对多解析
    assert row["edge_hit"] is True and row["candidate_hit"] is True
    assert row["direction"] == "ok"
    assert row["actor_stated"] is True and row["actor_consistent"] is True


def test_all_miss_is_no_edge():
    row = mod.score_relation(rel("子", "寅", mechanism="冲"), FACTS, case_id="T-02")
    assert (row["edge_hit"], row["candidate_hit"], row["direction"]) == (False, False, "no_edge")


def test_kind_mismatch_is_miss():
    # 盘上有 chong[子,午]，按「穿」评不应命中
    row = mod.score_relation(rel("子", "午", mechanism="穿"), FACTS, case_id="T-03")
    assert (row["edge_hit"], row["candidate_hit"], row["direction"]) == (False, False, "no_edge")


def test_reversed_when_actor_on_b_end():
    facts = make_facts(candidates=[cand("ke", "Y.s", "M.s", actor="M.s")])
    row = mod.score_relation(rel("甲", "丙"), facts, case_id="T-04")
    assert row["candidate_hit"] is True and row["direction"] == "reversed"


def test_actor_none_when_candidate_has_no_actor():
    row = mod.score_relation(rel("子", "午", mechanism="冲"), FACTS, case_id="T-05")
    assert row["candidate_hit"] is True and row["direction"] == "actor_none"


def test_no_candidate_when_only_edge_matches():
    facts = make_facts(edges=[edge("e009", "chong", "Y.b", "M.b")], candidates=[])
    row = mod.score_relation(rel("子", "午", mechanism="冲"), facts, case_id="T-06")
    assert (row["edge_hit"], row["candidate_hit"], row["direction"]) == (True, False, "no_candidate")


def test_multi_address_any_combination_hits():
    facts = make_facts(edges=[edge("e010", "ke", "D.s", "M.s")],
                       candidates=[cand("ke", "D.s", "M.s", actor="D.s")])
    row = mod.score_relation(rel("甲", "丙"), facts, case_id="T-07")
    assert row["a_addrs"] == ["D.s", "Y.s"]
    assert row["edge_hit"] is True and row["direction"] == "ok"


def test_endpoint_absent_is_not_scored():
    row = mod.score_relation(rel("亥", "丙"), FACTS, case_id="T-08")
    assert row["status"] == "endpoint_absent"
    assert (row["edge_hit"], row["candidate_hit"]) == (False, False)
    assert mod.summarize([row])["scored"] == 0


def test_muku_candidate_and_excluded_filter():
    # T-178/T-179：墓用候选 members=(库,入库方)、actor=库；答案 a=库 → ok
    facts = make_facts(
        edges=[edge("e011", "chong", "Y.b", "M.b")],
        candidates=[cand("muku", "Y.b", "M.b", actor="Y.b", mode="墓用")],
        muku=[{"addr": "Y.b", "candidates": [{"addr": "M.b", "excluded": False},
                                             {"addr": "H.b", "excluded": True}]}],
    )
    row = mod.score_relation(rel("子", "午", kind="墓", mechanism="墓"), facts, case_id="T-09")
    assert row["edge_hit"] is False                 # 墓 的边映射为空：盘上有 chong 也不算
    assert row["candidate_hit"] is True
    assert row["muku_hits"] == ["M.b->Y.b"]         # excluded 的 H.b 不计
    assert row["direction"] == "ok"                 # 墓用候选的 actor 是库（a 端）


def test_muku_hits_only_for_mu_relations():
    facts = make_facts(muku=[{"addr": "Y.b", "candidates": [{"addr": "M.b", "excluded": False}]}])
    row = mod.score_relation(rel("子", "午", mechanism="冲"), facts, case_id="T-10")
    assert row["muku_hits"] == []


def test_candidate_kind_suffix_is_stripped():
    # T-180/T-181：化用候选 members=(化者,被化者)、actor=化者；答案 a=化者 → ok
    facts = make_facts(candidates=[cand("sheng(main_qi)", "Y.b", "M.b", actor="Y.b", mode="化用")])
    row = mod.score_relation(rel("子", "午", kind="化", mechanism="化"), facts, case_id="T-11")
    assert row["candidate_hit"] is True and row["direction"] == "ok"


def test_hua_candidate_actor_is_hua_zhe_t180():
    """T-180/T-181 化用：a=化者（受生端）、b=被化者（生端），候选 (化者,被化者)、actor=化者 → ok。

    H09（癸巳 乙卯 己巳 己巳）：巳火印化卯木杀，卯生巳，化者=巳；三条化用候选 actor 均落 a 端。
    """
    facts = make_facts(
        pillars=HUA09_PILLARS,
        candidates=[cand("sheng(main_qi)", "Y.b", "M.b", actor="Y.b", mode="化用"),
                    cand("sheng(main_qi)", "D.b", "M.b", actor="D.b", mode="化用"),
                    cand("sheng(main_qi)", "H.b", "M.b", actor="H.b", mode="化用")],
    )
    row = mod.score_relation(rel("巳", "卯", kind="化", mechanism="化"), facts, case_id="P1-H09")
    assert row["a_addrs"] == ["D.b", "H.b", "Y.b"]
    assert row["b_addrs"] == ["M.b"]
    assert row["candidate_hit"] is True
    assert row["candidates"] == [
        {"kind": "sheng(main_qi)", "members": ["Y.b", "M.b"], "actor": "Y.b"},
        {"kind": "sheng(main_qi)", "members": ["D.b", "M.b"], "actor": "D.b"},
        {"kind": "sheng(main_qi)", "members": ["H.b", "M.b"], "actor": "H.b"},
    ]
    assert row["direction"] == "ok"


def test_h12_cai_sha_hua_known_gap_t180():
    """H12 财→杀是 known_gap：引擎只有 mode=生泄用，(子,寅) actor=子（被化者）→ 仍 reversed。

    按 T-180 §6.3 / T-181：不扩类、不改标签、不剔分母；修复化用 actor 碰不到本条。
    """
    facts = make_facts(
        pillars=HUA12_PILLARS,
        candidates=[cand("sheng(main_qi)", "D.b", "H.b", actor="D.b", mode="生泄用")],
    )
    row = mod.score_relation(rel("寅", "子", kind="化", mechanism="化"), facts, case_id="P1-H12")
    assert (row["a_addrs"], row["b_addrs"]) == (["H.b"], ["D.b"])
    assert row["candidate_hit"] is True
    assert row["direction"] == "reversed"            # known_gap：不是 ok，也不从分母剔除
    assert row["actor_consistent"] is True


def test_actor_not_equal_a_is_flagged():
    row = mod.score_relation(rel("甲", "丙", actor="丙"), FACTS, case_id="T-12")
    assert row["actor_consistent"] is False


# ── 4. 汇总 ────────────────────────────────────────────────────────────────

def scored_row(case_id: str, *, edge_hit: bool = False, candidate_hit: bool = False,
               direction: str = "no_edge", actor_stated: bool = True, muku_hits=()) -> dict:
    return {"case_id": case_id, "status": "scored", "actor_stated": actor_stated,
            "edge_hit": edge_hit, "candidate_hit": candidate_hit,
            "muku_hits": list(muku_hits), "direction": direction}


def test_summarize_counts_and_pct():
    rows = [
        scored_row(f"P1-H{i:02d}", edge_hit=i < 8, candidate_hit=i < 14,
                   direction="ok" if i == 0 else ("reversed" if i < 8 else "no_edge"))
        for i in range(20)
    ]
    s = mod.summarize(rows)
    assert (s["edge_recall"], s["edge_recall_pct"]) == ("8/20", 40.0)
    assert (s["candidate_recall"], s["candidate_recall_pct"]) == ("14/20", 70.0)
    assert (s["directed_recall"], s["directed_recall_pct"]) == ("1/20", 5.0)
    assert s["direction_breakdown"] == {"no_edge": 12, "ok": 1, "reversed": 7}


def test_summarize_actor_null_leaves_direction_denominator():
    s = mod.summarize([scored_row("P1-H01", actor_stated=False, direction="actor_none"),
                       scored_row("P1-H02", direction="ok")])
    assert s["directed"] == 1 and s["directed_recall"] == "1/1"
    assert s["direction_breakdown"] == {"ok": 1}


def test_summarize_zero_denominator_is_none():
    s = mod.summarize([scored_row("X", actor_stated=False)])
    assert s["directed_recall"] == "0/0" and s["directed_recall_pct"] is None


def test_summarize_ignores_endpoint_absent_rows():
    rows = [scored_row("P1-H01"), {"case_id": "P1-H02", "status": "endpoint_absent"}]
    s = mod.summarize(rows)
    assert s["scored"] == 1 and s["edge_recall"] == "0/1"


def test_summarize_muku_equivalent_counts_muku_only_rows():
    s = mod.summarize([scored_row("P1-H01", muku_hits=["M.b->Y.b"])])
    assert s["edge_recall"] == "0/1"
    assert (s["muku_equivalent_edge_recall"], s["muku_equivalent_edge_recall_pct"]) == ("1/1", 100.0)


# ── 5. 端到端（monkeypatch facts_for，不跑引擎）─────────────────────────────

def _case(case_id: str, category: str = "制", *, four="甲子 丙寅 甲午 甲子",
          gender="乾", a="甲", b="丙", kind="制", mechanism="克") -> dict:
    return {"case_id": case_id, "four_pillars": four, "gender": gender, "category": category,
            "rel": {"a": a, "b": b, "kind": kind, "mechanism": mechanism, "actor": a,
                    "quote": "合成 fixture", "source_ref": "sources/duan/x.md:L1"}}


def _write(tmp_path: Path, cases: list[dict]) -> tuple[Path, Path]:
    holdout = {
        "schema_version": "p1-holdout-blind-input/v1",
        "case_count": len(cases),
        "cases": [{"case_id": c["case_id"], "four_pillars": c["four_pillars"],
                   "gender": c["gender"], "source": {"path": "sources/duan/x.md", "locator": "L1"}}
                  for c in cases],
    }
    answers = {
        "schema_version": "p1-holdout-answers/v1",
        "case_count": len(cases),
        "cases": [{"case_id": c["case_id"], "four_pillars": c["four_pillars"],
                   "gender": c["gender"], "category": c["category"],
                   "core_work_relations": [dict(c["rel"])]} for c in cases],
    }
    holdout_path = tmp_path / "holdout.json"
    answers_path = tmp_path / "answers.json"
    holdout_path.write_text(json.dumps(holdout, ensure_ascii=False, indent=1), encoding="utf-8")
    answers_path.write_text(json.dumps(answers, ensure_ascii=False, indent=1), encoding="utf-8")
    return holdout_path, answers_path


def test_run_splits_primary_and_f28_subsets(monkeypatch, tmp_path):
    cases = [_case(f"P1-H{i:02d}", "救应" if i >= 17 else "制") for i in range(1, 21)]
    holdout_path, answers_path = _write(tmp_path, cases)
    monkeypatch.setattr(mod, "facts_for", lambda pillars, gender: FACTS)

    result = mod.run(holdout_path, answers_path)
    assert result["artifact"] == "pre_fix_baseline"
    assert result["inputs"]["relations"] == 20
    assert result["denominator_check"] == {"relations": 20, "scored": 20,
                                          "endpoint_absent": [], "ok": True}
    assert result["primary"]["edge_recall"] == "20/20"
    assert result["primary"]["candidate_recall"] == "20/20"
    assert result["primary"]["directed_recall"] == "20/20"
    assert result["sensitivity_denominator"] == 16
    assert result["sensitivity_exclude_f28_rescue"]["scored"] == 16
    assert result["sensitivity_exclude_f28_rescue"]["edge_recall"] == "16/16"
    assert [r["case_id"] for r in result["cases"]] == [c["case_id"] for c in cases]
    assert result["scoring"]["no_dev_comparison"] is True


def test_run_is_deterministic(monkeypatch, tmp_path):
    holdout_path, answers_path = _write(tmp_path, [_case("P1-H01"), _case("P1-H02", "墓", mechanism="墓")])
    monkeypatch.setattr(mod, "facts_for", lambda pillars, gender: FACTS)
    first = json.dumps(mod.run(holdout_path, answers_path), ensure_ascii=False, indent=1)
    second = json.dumps(mod.run(holdout_path, answers_path), ensure_ascii=False, indent=1)
    assert first == second


def test_run_records_input_hashes(tmp_path, monkeypatch):
    holdout_path, answers_path = _write(tmp_path, [_case("P1-H01")])
    monkeypatch.setattr(mod, "facts_for", lambda pillars, gender: FACTS)
    result = mod.run(holdout_path, answers_path)
    assert result["inputs"]["sha256"]["holdout"] == mod._sha256(holdout_path)
    assert result["inputs"]["sha256"]["answers"] == mod._sha256(answers_path)


def test_run_artifact_label_default_and_override(monkeypatch, tmp_path):
    holdout_path, answers_path = _write(tmp_path, [_case("P1-H01")])
    monkeypatch.setattr(mod, "facts_for", lambda pillars, gender: FACTS)
    assert mod.run(holdout_path, answers_path)["artifact"] == "pre_fix_baseline"
    assert mod.run(holdout_path, answers_path, artifact_label="official_p1")["artifact"] == "official_p1"


def test_run_rejects_pillar_mismatch(monkeypatch, tmp_path):
    holdout_path, answers_path = _write(tmp_path, [_case("P1-H01")])
    monkeypatch.setattr(mod, "facts_for", lambda pillars, gender: FACTS)
    data = json.loads(answers_path.read_text(encoding="utf-8"))
    data["cases"][0]["four_pillars"] = "乙丑 戊寅 乙卯 丙子"
    answers_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="四柱"):
        mod.run(holdout_path, answers_path)


def test_run_rejects_case_missing_in_holdout(monkeypatch, tmp_path):
    holdout_path, answers_path = _write(tmp_path, [_case("P1-H01"), _case("P1-H02")])
    monkeypatch.setattr(mod, "facts_for", lambda pillars, gender: FACTS)
    data = json.loads(holdout_path.read_text(encoding="utf-8"))
    data["cases"] = data["cases"][:1]
    holdout_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="answers 有、holdout 无"):
        mod.run(holdout_path, answers_path)


def test_run_rejects_duplicate_case_ids(monkeypatch, tmp_path):
    holdout_path, answers_path = _write(tmp_path, [_case("P1-H01"), _case("P1-H01")])
    monkeypatch.setattr(mod, "facts_for", lambda pillars, gender: FACTS)
    with pytest.raises(ValueError, match="重复"):
        mod.run(holdout_path, answers_path)


# ── 6. CLI 与产物 ──────────────────────────────────────────────────────────

def test_cli_writes_byte_identical_artifacts(monkeypatch, tmp_path):
    holdout_path, answers_path = _write(tmp_path, [_case("P1-H01"), _case("P1-H02")])
    monkeypatch.setattr(mod, "facts_for", lambda pillars, gender: FACTS)
    outs = []
    for name in ("a", "b"):
        out_json = tmp_path / f"{name}.json"
        out_md = tmp_path / f"{name}.md"
        rc = mod.main(["--holdout", str(holdout_path), "--answers", str(answers_path),
                       "--out-json", str(out_json), "--out-md", str(out_md)])
        assert rc == 0
        outs.append((out_json.read_bytes(), out_md.read_bytes()))

    assert outs[0][0] == outs[1][0], "两次运行 JSON 必须逐字节一致"
    assert outs[0][1] == outs[1][1], "两次运行 MD 必须逐字节一致"

    payload = json.loads(outs[0][0].decode("utf-8"))
    assert payload["denominator_check"]["ok"] is True
    assert "generated_at" not in json.dumps(payload, ensure_ascii=False)
    text = outs[0][1].decode("utf-8")
    assert "| 边召回 `edge_recall` | 2/2 | 100.0% |" in text
    assert "pre-fix 基线" in text


@pytest.mark.parametrize("label", [None, "official_p1", "post_fix_hua"])
def test_cli_artifact_label_in_json_and_console_title(monkeypatch, tmp_path, capsys, label):
    holdout_path, answers_path = _write(tmp_path, [_case("P1-H01")])
    monkeypatch.setattr(mod, "facts_for", lambda pillars, gender: FACTS)
    out_json, out_md = tmp_path / "o.json", tmp_path / "o.md"
    argv = ["--holdout", str(holdout_path), "--answers", str(answers_path),
            "--out-json", str(out_json), "--out-md", str(out_md)]
    if label is not None:
        argv += ["--artifact-label", label]

    assert mod.main(argv) == 0
    expected = label or "pre_fix_baseline"       # 默认 pre_fix_baseline
    assert json.loads(out_json.read_text(encoding="utf-8"))["artifact"] == expected
    title = capsys.readouterr().out.splitlines()[0]
    assert title.startswith("P1 hold-out ") and expected in title
    assert f"- artifact：`{expected}`" in out_md.read_text(encoding="utf-8")


def test_cli_json_flag_prints_payload(monkeypatch, tmp_path, capsys):
    holdout_path, answers_path = _write(tmp_path, [_case("P1-H01")])
    monkeypatch.setattr(mod, "facts_for", lambda pillars, gender: FACTS)
    rc = mod.main(["--holdout", str(holdout_path), "--answers", str(answers_path),
                   "--out-json", str(tmp_path / "o.json"), "--out-md", str(tmp_path / "o.md"),
                   "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["primary"]["scored"] == 1
    assert payload["primary"]["edge_recall"] == "1/1"


def test_cli_exit_2_when_endpoint_absent(monkeypatch, tmp_path):
    holdout_path, answers_path = _write(tmp_path, [
        {"case_id": "P1-H01", "four_pillars": "甲子 丙寅 甲午 甲子", "gender": "乾", "category": "制",
         "rel": {"a": "亥", "b": "丙", "kind": "制", "mechanism": "克", "actor": "亥",
                 "quote": "合成 fixture", "source_ref": "sources/duan/x.md:L1"}},
    ])
    monkeypatch.setattr(mod, "facts_for", lambda pillars, gender: FACTS)
    rc = mod.main(["--holdout", str(holdout_path), "--answers", str(answers_path),
                   "--out-json", str(tmp_path / "o.json"), "--out-md", str(tmp_path / "o.md")])
    assert rc == 2


def test_cli_exit_2_on_unreadable_input(tmp_path, capsys):
    rc = mod.main(["--holdout", str(tmp_path / "nope.json"),
                   "--answers", str(tmp_path / "nope2.json"),
                   "--out-json", str(tmp_path / "o.json"), "--out-md", str(tmp_path / "o.md")])
    assert rc == 2
    assert "输入不合口径" in capsys.readouterr().err


# ── 7. 引擎冒烟（只断言不变量）─────────────────────────────────────────────

def test_real_engine_facts_smoke():
    facts = mod.facts_for("甲子 丙寅 甲午 甲子", "乾")
    assert len(facts["chart"]["pillars"]) == 4
    assert isinstance(facts["relations"].get("edges"), list)
    assert isinstance(facts["duan_zuogong"].get("candidates"), list)

    row = mod.score_relation(rel("子", "午", mechanism="冲"), facts, case_id="SMOKE")
    assert row["status"] == "scored"
    assert set(row["a_addrs"]) == {"Y.b", "H.b"}      # 子 在原局两处
    assert row["b_addrs"] == ["D.b"]
    assert row["direction"] in mod.DIRECTIONS


def test_gender_fallback_only_for_unstated():
    assert mod.gender_for("未注明") == "乾"
    assert mod.gender_for("坤") == "坤"
    # 引擎只认 乾/坤；未注明必须能起盘
    facts = mod.facts_for("甲子 丙寅 甲午 甲子", "未注明")
    assert len(facts["chart"]["pillars"]) == 4
