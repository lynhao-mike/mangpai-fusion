"""tests/tools/test_p1_assertion_eval_v2.py · T-189a 核心 + T-189b 增量测试。

T-189a（合成 fixture，非真实盘）：三层 10/40/10、32/8、全错、nj=miss、
ambiguous 引文 5 变体、地址/字归一、输入契约、CLI 确定性。

T-189b 增量：

1. B1 = T-184 delta 符号（V1a/V1b 向量、delta 正负、平局柱序左、同类端弃权）；
2. B2 = 本气克/生/同五行四库主位端（D/H 优先、同主同宾柱序靠后），四库不弃权；
3. margin = dynamic.correct − max(B1,B2)，弃权按不中计；
4. chart_id 聚类：macro、全对盘率、固定 seed bootstrap（误差集中时全对盘率下降）；
5. 3 次运行方向一致率（定向比端点取向，缺 case 记不一致）；
6. T-187 回归：读 `META/p1-system-run-v1.json` + `META/p1-fresh-40-answers-v1.json`，
   复算 edge **12/40**、direction **2/20**、edge mismatch **28/40**（不宣称新结果）；
7. ambiguous 只读 source loader：缺 `source_texts` 时按 `source_ref(s)` 从 `sources/` 取行，
   引文口径不变；越界/缺行退出 2。
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools import p1_assertion_eval_v2 as mod

# ── 合成 fixture（手写，非任何真实盘）────────────────────────────────────────

PAIRS = [
    ("巳", "亥"), ("丑", "未"), ("子", "午"), ("卯", "酉"),
    ("辰", "戌"), ("寅", "申"), ("亥", "卯"), ("酉", "戌"),
]
FIXED_KINDS = ["克", "生", "化", "墓"]
DYNAMIC_KINDS = ["冲", "合", "穿", "刑"]

ADDRESS_BOOK: dict[str, str] = {}
CHAR_TO_ADDR: dict[str, str] = {}
for _index, (_left, _right) in enumerate(PAIRS):
    ADDRESS_BOOK[f"D{_index + 1}"] = _left
    ADDRESS_BOOK[f"H{_index + 1}"] = _right
    CHAR_TO_ADDR.setdefault(_left, f"D{_index + 1}")
    CHAR_TO_ADDR.setdefault(_right, f"H{_index + 1}")

AMB_LOC1 = "sources/duan/fixture-ambiguous.md:L1"
AMB_LOC2 = "sources/duan/fixture-ambiguous.md:L2"
AMB_TEXTS = {
    AMB_LOC1: "未戌相刑，土旺而藏干不发，功在开库。",
    AMB_LOC2: "未戌相刑，金水入库而用神反失，功不可成。",
}
Q_FOR = "土旺而藏干不发"
Q_AGAINST = "金水入库而用神反失"


# ── fixture 生成 ────────────────────────────────────────────────────────────

def fixed_cases() -> list[dict]:
    """fixed 10：答案只给地址（考地址→字归一），系统用字回报。"""
    return [
        {
            "case_id": f"FX-{i + 1:02d}", "layer": "fixed",
            "kind": FIXED_KINDS[i % 4], "mechanism": FIXED_KINDS[i % 4],
            "addr_a": f"D{i % 8 + 1}", "addr_b": f"H{i % 8 + 1}",
            "expected_direction": mod.DIRECTED,
        }
        for i in range(10)
    ]


def dynamic_cases() -> list[dict]:
    return [
        {
            "case_id": f"DY-{i + 1:02d}", "layer": "dynamic",
            "kind": DYNAMIC_KINDS[i % 4], "mechanism": DYNAMIC_KINDS[i % 4],
            "char_a": PAIRS[i % 8][0], "char_b": PAIRS[i % 8][1],
            "expected_direction": mod.DIRECTED,
        }
        for i in range(40)
    ]


def ambiguous_cases() -> list[dict]:
    return [
        {
            "case_id": f"AM-{i + 1:02d}", "layer": "ambiguous",
            "kind": "刑" if i % 2 == 0 else "墓", "mechanism": "刑" if i % 2 == 0 else "墓",
            "char_a": PAIRS[i % 8][0], "char_b": PAIRS[i % 8][1],
            "expected_direction": mod.NEEDS_JUDGMENT,
            "source_ref": AMB_LOC1, "source_texts": dict(AMB_TEXTS),
            "conflict_quotes": [Q_FOR, Q_AGAINST],
        }
        for i in range(10)
    ]


def answers_doc(cases: list[dict], *, book: dict | None = None) -> dict:
    doc = {"schema_version": mod.SCHEMA_ANSWERS, "case_count": len(cases), "cases": cases}
    if book is not None:
        doc["address_book"] = book
    return doc


def output_doc(cases: list[dict]) -> dict:
    return {"schema_version": mod.SCHEMA_OUTPUT, "case_count": len(cases), "cases": cases}


def obs(case_id: str, a: str, b: str, direction: str, **extra) -> dict:
    return {"case_id": case_id, "a": a, "b": b, "direction": direction, **extra}


def correct_outputs() -> list[dict]:
    rows = []
    for case in fixed_cases():
        # 答案只给地址，系统给字（地址→字）
        rows.append(obs(case["case_id"], ADDRESS_BOOK[case["addr_a"]],
                        ADDRESS_BOOK[case["addr_b"]], mod.DIRECTED))
    for case in dynamic_cases():
        # 系统 a 用字、b 用地址（字↔地址混用）
        rows.append(obs(case["case_id"], f" {case['char_a']} ",
                        CHAR_TO_ADDR[case["char_b"]], mod.DIRECTED))
    for case in ambiguous_cases():
        rows.append(obs(case["case_id"], case["char_a"], case["char_b"],
                        mod.NEEDS_JUDGMENT, conflict_quotes=[Q_FOR, Q_AGAINST]))
    return rows


def full_docs() -> tuple[dict, dict]:
    cases = fixed_cases() + dynamic_cases() + ambiguous_cases()
    return answers_doc(cases, book=ADDRESS_BOOK), output_doc(correct_outputs())


def write_docs(tmp_path: Path, answers: dict, output: dict) -> tuple[Path, Path]:
    ap = tmp_path / "answers.json"
    sp = tmp_path / "output.json"
    ap.write_text(json.dumps(answers, ensure_ascii=False), encoding="utf-8")
    sp.write_text(json.dumps(output, ensure_ascii=False), encoding="utf-8")
    return ap, sp


def evaluate(tmp_path: Path, answers: dict, output: dict) -> dict:
    ap, sp = write_docs(tmp_path, answers, output)
    return mod.run(ap, sp)


def row_of(result: dict, case_id: str) -> dict:
    for row in result["cases"]:
        if row["case_id"] == case_id:
            return row
    raise AssertionError(f"缺少 case {case_id}")


def assert_accounting(result: dict) -> None:
    for layer in mod.LAYERS:
        summary = result["layers"][layer]
        parts = (summary["correct"] + summary["wrong"] + summary["missing"]
                 + summary.get("nj", 0) + summary.get("quote_fail", 0))
        assert parts == summary["total"]


# ── 1. 全对 ────────────────────────────────────────────────────────────────

def test_all_correct_three_layers(tmp_path: Path) -> None:
    answers, output = full_docs()
    result = evaluate(tmp_path, answers, output)

    counts = result["counts"]
    assert (counts["fixed"], counts["dynamic"], counts["ambiguous"], counts["total"]) == (10, 40, 10, 60)
    assert counts["denominators_met"] is True and counts["total_met"] is True

    layers = result["layers"]
    assert layers["fixed"]["correct"] == 10 and layers["fixed"]["all_correct"] is True
    assert layers["dynamic"]["correct"] == 40
    assert layers["ambiguous"]["correct"] == 10
    for layer in mod.LAYERS:
        assert layers[layer]["precision"]["value"] == 1.0
        assert layers[layer]["wrong"] == 0 and layers[layer]["missing"] == 0
    assert layers["dynamic"]["nj"] == 0 and layers["dynamic"]["miss"] == 0
    assert layers["fixed"]["delivered"] == 10  # 答案地址→字归一后系统全对
    assert layers["ambiguous"]["quotes_checked"] == 20
    assert layers["ambiguous"]["quote_violations"] == 0
    assert_accounting(result)


def test_wilson_on_perfect_40(tmp_path: Path) -> None:
    answers = answers_doc(dynamic_cases())
    output = output_doc([
        obs(c["case_id"], c["char_a"], c["char_b"], mod.DIRECTED) for c in dynamic_cases()
    ])
    result = evaluate(tmp_path, answers, output)
    wilson = result["layers"]["dynamic"]["precision"]["wilson95"]
    assert wilson["lower"] == pytest.approx(0.9124, abs=1e-3)
    assert wilson["upper"] == pytest.approx(1.0, abs=1e-3)


# ── 2. 32/8 ────────────────────────────────────────────────────────────────

def test_32_of_40_precision_and_wilson(tmp_path: Path) -> None:
    answers, _ = full_docs()
    rows = []
    for index, case in enumerate(dynamic_cases()):
        direction = mod.DIRECTED
        a, b = case["char_a"], case["char_b"]
        if index >= 32:  # 后 8 条写反
            a, b = b, a
        rows.append(obs(case["case_id"], a, b, direction))
    for case in fixed_cases():
        rows.append(obs(case["case_id"], ADDRESS_BOOK[case["addr_a"]],
                        ADDRESS_BOOK[case["addr_b"]], mod.DIRECTED))
    for case in ambiguous_cases():
        rows.append(obs(case["case_id"], case["char_a"], case["char_b"],
                        mod.NEEDS_JUDGMENT, conflict_quotes=[Q_FOR, Q_AGAINST]))
    result = evaluate(tmp_path, answers, output_doc(rows))

    dynamic = result["layers"]["dynamic"]
    assert (dynamic["correct"], dynamic["wrong"]) == (32, 8)
    assert dynamic["precision"]["numerator"] == 32
    assert dynamic["precision"]["denominator"] == 40
    assert dynamic["precision"]["value"] == pytest.approx(0.8)
    assert dynamic["correct_over_total"]["value"] == pytest.approx(0.8)
    assert dynamic["precision"]["percent"] == 80.0
    assert dynamic["precision"]["wilson95"]["lower"] == pytest.approx(0.6524, abs=1e-3)
    assert dynamic["precision"]["wilson95"]["upper"] == pytest.approx(0.895, abs=1e-3)
    assert row_of(result, "DY-40")["status"] == "wrong"
    assert row_of(result, "DY-40")["reason"] == "reversed"
    assert_accounting(result)


# ── 3. 全错 ────────────────────────────────────────────────────────────────

def test_all_wrong_reversed(tmp_path: Path) -> None:
    answers, _ = full_docs()
    rows = []
    for case in fixed_cases():
        rows.append(obs(case["case_id"], ADDRESS_BOOK[case["addr_b"]],
                        ADDRESS_BOOK[case["addr_a"]], mod.DIRECTED))
    for case in dynamic_cases():
        rows.append(obs(case["case_id"], case["char_b"], case["char_a"], mod.DIRECTED))
    for case in ambiguous_cases():
        rows.append(obs(case["case_id"], case["char_b"], case["char_a"], mod.DIRECTED))
    result = evaluate(tmp_path, answers, output_doc(rows))

    dynamic = result["layers"]["dynamic"]
    assert (dynamic["correct"], dynamic["wrong"]) == (0, 40)
    assert dynamic["precision"]["value"] == 0.0
    assert dynamic["precision"]["wilson95"]["lower"] == 0.0
    assert dynamic["precision"]["wilson95"]["upper"] == pytest.approx(0.0876, abs=1e-3)
    assert result["layers"]["fixed"]["correct"] == 0
    assert row_of(result, "DY-01")["reason"] == "reversed"
    assert row_of(result, "AM-01")["status"] == "wrong"
    assert_accounting(result)


# ── 4. dynamic 上 nj=miss ──────────────────────────────────────────────────

def test_dynamic_nj_is_miss(tmp_path: Path) -> None:
    answers = answers_doc(dynamic_cases())
    base = [obs(c["case_id"], c["char_a"], c["char_b"], mod.DIRECTED)
            for c in dynamic_cases()]
    rows = base[:30] + [
        obs(dynamic_cases()[i]["case_id"], *reversed(PAIRS[i % 8]), mod.DIRECTED)
        for i in range(30, 35)
    ] + [
        obs(dynamic_cases()[i]["case_id"], dynamic_cases()[i]["char_a"],
            dynamic_cases()[i]["char_b"], mod.NEEDS_JUDGMENT)
        for i in range(35, 40)
    ]
    with_nj = evaluate(tmp_path, answers, output_doc(rows))
    dynamic = with_nj["layers"]["dynamic"]
    assert (dynamic["correct"], dynamic["wrong"], dynamic["nj"], dynamic["missing"]) == (30, 5, 5, 0)
    assert dynamic["miss"] == 5
    assert dynamic["delivered"] == 35
    assert dynamic["precision"]["value"] == pytest.approx(30 / 35)
    assert row_of(with_nj, "DY-36")["status"] == "nj"
    assert row_of(with_nj, "DY-36")["reason"] == "needs_judgment"

    # 同一批 5 条直接不输出 → 读数与 nj 一致（nj=miss）
    missing_rows = [row for row in rows if row["case_id"] not in
                    {f"DY-{i + 1:02d}" for i in range(35, 40)}]
    with_missing = evaluate(tmp_path, answers, output_doc(missing_rows))
    for key in ("correct", "wrong", "delivered", "miss"):
        assert with_missing["layers"]["dynamic"][key] == dynamic[key]
    assert with_missing["layers"]["dynamic"]["missing"] == 5
    assert_accounting(with_nj)
    assert_accounting(with_missing)


def test_fixed_nj_fails_ten_of_ten_and_stays_in_fixed(tmp_path: Path) -> None:
    answers = answers_doc(fixed_cases() + dynamic_cases(), book=ADDRESS_BOOK)
    rows = [obs(c["case_id"], ADDRESS_BOOK[c["addr_a"]], ADDRESS_BOOK[c["addr_b"]],
                mod.NEEDS_JUDGMENT) for c in fixed_cases()[:1]]
    rows += [obs(c["case_id"], ADDRESS_BOOK[c["addr_a"]], ADDRESS_BOOK[c["addr_b"]],
                 mod.DIRECTED) for c in fixed_cases()[1:]]
    rows += [obs(c["case_id"], c["char_a"], c["char_b"], mod.DIRECTED)
             for c in dynamic_cases()]
    result = evaluate(tmp_path, answers, output_doc(rows))

    fixed = result["layers"]["fixed"]
    assert (fixed["correct"], fixed["nj"], fixed["all_correct"]) == (9, 1, False)
    assert fixed["miss"] == 1
    assert result["layers"]["dynamic"]["correct"] == 40
    assert fixed["total"] == 10 and result["layers"]["dynamic"]["total"] == 40
    assert_accounting(result)


# ── 5. ambiguous：引文 ─────────────────────────────────────────────────────

def _ambiguous_outputs() -> list[dict]:
    cases = ambiguous_cases()
    rows = []
    rows.append(obs(cases[0]["case_id"], cases[0]["char_a"], cases[0]["char_b"],
                    mod.NEEDS_JUDGMENT))  # 缺引文
    rows.append(obs(cases[1]["case_id"], cases[1]["char_a"], cases[1]["char_b"],
                    mod.NEEDS_JUDGMENT, conflict_quotes=[Q_FOR]))  # 只给一条
    rows.append(obs(cases[2]["case_id"], cases[2]["char_a"], cases[2]["char_b"],
                    mod.NEEDS_JUDGMENT, conflict_quotes=["未戌相刑无库可开", Q_AGAINST]))  # 非逐字
    rows.append(obs(cases[3]["case_id"], cases[3]["char_a"], cases[3]["char_b"],
                    mod.NEEDS_JUDGMENT, conflict_quotes=[Q_FOR, Q_FOR]))  # 重复
    rows.append(obs(cases[4]["case_id"], cases[4]["char_a"], cases[4]["char_b"],
                    mod.DIRECTED, conflict_quotes=[Q_FOR, Q_AGAINST]))  # 硬给方向
    for case in cases[5:]:
        rows.append(obs(case["case_id"], case["char_a"], case["char_b"],
                        mod.NEEDS_JUDGMENT, conflict_quotes=[Q_FOR, Q_AGAINST]))
    return rows


def test_ambiguous_quote_failures(tmp_path: Path) -> None:
    answers = answers_doc(ambiguous_cases())
    result = evaluate(tmp_path, answers, output_doc(_ambiguous_outputs()))
    layer = result["layers"]["ambiguous"]

    assert (layer["correct"], layer["wrong"], layer["quote_fail"], layer["missing"]) == (5, 1, 4, 0)
    assert layer["delivered"] == 10
    assert layer["precision"]["value"] == pytest.approx(0.5)
    assert layer["both_quotes"]["value"] == pytest.approx(0.5)
    assert row_of(result, "AM-01")["reason"] == "conflict_quotes_not_2"
    assert row_of(result, "AM-02")["status"] == "quote_fail"
    assert row_of(result, "AM-03")["reason"] == "quote_not_verbatim"
    assert [q["found"] for q in row_of(result, "AM-03")["quotes"]] == [False, True]
    assert row_of(result, "AM-04")["reason"] == "conflict_quotes_duplicate"
    assert row_of(result, "AM-05")["status"] == "wrong"
    assert row_of(result, "AM-05")["reason"] == "directed_claim_on_ambiguous"
    assert row_of(result, "AM-06")["reason"] == "needs_judgment_with_quotes"
    assert layer["quote_violations"] == 1
    assert_accounting(result)


def test_ambiguous_quote_object_with_locator(tmp_path: Path) -> None:
    answers = answers_doc(ambiguous_cases()[:2])
    good = [
        obs("AM-01", *PAIRS[0], mod.NEEDS_JUDGMENT, conflict_quotes=[
            {"quote": Q_FOR, "source_ref": AMB_LOC1},
            {"quote": Q_AGAINST, "source_ref": AMB_LOC2}]),
        # 第二条引文错标到 L1（L1 里没有）→ 逐字行内不成立
        obs("AM-02", *PAIRS[1], mod.NEEDS_JUDGMENT, conflict_quotes=[
            {"quote": Q_FOR, "source_ref": AMB_LOC1},
            {"quote": Q_AGAINST, "source_ref": AMB_LOC1}]),
    ]
    result = evaluate(tmp_path, answers, output_doc(good))

    assert row_of(result, "AM-01")["status"] == "correct"
    assert row_of(result, "AM-02")["status"] == "quote_fail"
    assert [q["found"] for q in row_of(result, "AM-02")["quotes"]] == [True, False]
    assert result["layers"]["ambiguous"]["quotes_checked"] == 4
    assert result["layers"]["ambiguous"]["quotes_verbatim"] == 3


# ── 6. 地址/字双向归一 ─────────────────────────────────────────────────────

def mini_answer(**overrides) -> dict:
    case = {
        "case_id": "DY-01", "layer": "dynamic", "kind": "冲", "mechanism": "冲",
        "addr_a": "D1", "char_a": "巳", "addr_b": "H3", "char_b": "亥",
        "expected_direction": mod.DIRECTED,
    }
    case.update(overrides)
    return case


@pytest.mark.parametrize("a,b,direction,status", [
    ("巳", "亥", mod.DIRECTED, "correct"),       # 全字
    ("D1", "H3", mod.DIRECTED, "correct"),       # 全地址
    ("d1", " h3 ", mod.DIRECTED, "correct"),     # 地址大小写/空白归一
    ("D1", "亥", mod.DIRECTED, "correct"),       # 地址 + 字混用
    ("H3", "D1", mod.DIRECTED, "wrong"),         # 交换 → reversed
    ("子", "午", mod.DIRECTED, "wrong"),         # 另一端 → endpoint_mismatch
])
def test_address_char_normalization(tmp_path: Path, a, b, direction, status) -> None:
    answers = answers_doc([mini_answer()], book={"D1": "巳", "H3": "亥"})
    result = evaluate(tmp_path, answers, output_doc([obs("DY-01", a, b, direction)]))
    row = row_of(result, "DY-01")
    assert row["status"] == status
    if (a, b) == ("H3", "D1"):
        assert row["reason"] == "reversed"
    if (a, b) == ("子", "午"):
        assert row["reason"] == "endpoint_mismatch"


def test_answer_addr_only_resolved_by_book(tmp_path: Path) -> None:
    case = mini_answer()
    case.pop("char_a")
    case.pop("char_b")
    answers = answers_doc([case], book={"D1": "巳", "H3": "亥"})
    result = evaluate(tmp_path, answers,
                      output_doc([obs("DY-01", "巳", "H3", mod.DIRECTED)]))
    row = row_of(result, "DY-01")
    assert (row["status"], row["reason"]) == ("correct", "directed_match")


def test_mutual_expected_accepts_either_order(tmp_path: Path) -> None:
    answers = answers_doc([mini_answer(expected_direction=mod.MUTUAL)])
    ok = evaluate(tmp_path, answers, output_doc([obs("DY-01", "H3", "D1", mod.MUTUAL)]))
    assert row_of(ok, "DY-01")["status"] == "correct"
    directed = evaluate(tmp_path, answers,
                        output_doc([obs("DY-01", "巳", "亥", mod.DIRECTED)]))
    assert row_of(directed, "DY-01")["reason"] == "expected_mutual_observed_directed"


# ── 7. 输入契约 ────────────────────────────────────────────────────────────

def test_layer_kind_mixing_rejected(tmp_path: Path) -> None:
    answers = answers_doc([mini_answer(kind="克")])  # dynamic 层放 fixed 的克
    with pytest.raises(mod.InputError, match="dynamic 层 kind"):
        evaluate(tmp_path, answers, output_doc([]))


def test_nj_answer_on_dynamic_rejected(tmp_path: Path) -> None:
    answers = answers_doc([mini_answer(expected_direction=mod.NEEDS_JUDGMENT)])
    with pytest.raises(mod.InputError, match="可判层"):
        evaluate(tmp_path, answers, output_doc([]))


def test_ambiguous_answer_needs_two_quotes(tmp_path: Path) -> None:
    case = ambiguous_cases()[0]
    case["conflict_quotes"] = [Q_FOR]
    with pytest.raises(mod.InputError, match="conflict_quotes\\[2\\]"):
        evaluate(tmp_path, answers_doc([case]), output_doc([]))


def test_duplicate_and_unknown_case_ids(tmp_path: Path) -> None:
    dup = answers_doc([mini_answer(), mini_answer()])
    with pytest.raises(mod.InputError, match="重复 case_id"):
        evaluate(tmp_path, dup, output_doc([]))
    unknown = output_doc([obs("DY-99", "巳", "亥", mod.DIRECTED)])
    with pytest.raises(mod.InputError, match="未登记 case_id"):
        evaluate(tmp_path, answers_doc([mini_answer()]), unknown)


def test_bad_direction_and_bad_endpoint(tmp_path: Path) -> None:
    answers = answers_doc([mini_answer()], book={"D1": "巳", "H3": "亥"})
    with pytest.raises(mod.InputError, match="direction"):
        evaluate(tmp_path, answers, output_doc([obs("DY-01", "巳", "亥", "forward")]))
    with pytest.raises(mod.InputError, match="端点"):
        evaluate(tmp_path, answers, output_doc([obs("DY-01", "D9", "亥", mod.DIRECTED)]))


def test_case_count_mismatch(tmp_path: Path) -> None:
    answers = answers_doc([mini_answer()])
    answers["case_count"] = 3
    with pytest.raises(mod.InputError, match="case_count"):
        evaluate(tmp_path, answers, output_doc([]))


# ── 8. CLI ─────────────────────────────────────────────────────────────────

def test_cli_json_repeatable_and_exit_codes(tmp_path: Path, capsys) -> None:
    answers, output = full_docs()
    ap, sp = write_docs(tmp_path, answers, output)

    code = mod.main(["--answers", str(ap), "--system-output", str(sp), "--json"])
    first = capsys.readouterr().out
    code2 = mod.main(["--answers", str(ap), "--system-output", str(sp), "--json"])
    second = capsys.readouterr().out
    assert (code, code2) == (0, 0)
    assert first == second
    parsed = json.loads(first)
    assert parsed["schema_version"] == mod.SCHEMA_SCORE
    assert parsed["layers"]["dynamic"]["correct"] == 40

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"cases": [mini_answer(kind="克")]}, ensure_ascii=False),
                   encoding="utf-8")
    code3 = mod.main(["--answers", str(bad), "--system-output", str(sp)])
    captured = capsys.readouterr()
    assert code3 == 2
    assert "输入不合口径" in captured.err

    missing = mod.main(["--answers", str(tmp_path / "nope.json"), "--system-output", str(sp)])
    assert missing == 2
    capsys.readouterr()


def test_console_output_mentions_three_layers(tmp_path: Path, capsys) -> None:
    answers, output = full_docs()
    ap, sp = write_docs(tmp_path, answers, output)
    assert mod.main(["--answers", str(ap), "--system-output", str(sp)]) == 0
    text = capsys.readouterr().out
    assert "fixed" in text and "dynamic" in text and "ambiguous" in text
    assert "nj=miss" in text


# ════════════════════════════════════════════════════════════════════════════
# T-189b · B1 / B2 / margin / chart 聚类 / 3 次一致 / T-187 回归 / source loader
# ════════════════════════════════════════════════════════════════════════════

META_DIR = Path(__file__).resolve().parents[2] / "META"
T187_RUN = META_DIR / "p1-system-run-v1.json"
T187_ANSWERS = META_DIR / "p1-fresh-40-answers-v1.json"


def single_dynamic(char_a: str, char_b: str, *, pillar_a: str | None = None,
                   pillar_b: str | None = None, delta: int | None = None,
                   four_pillars: str | None = None,
                   expected: str = mod.DIRECTED) -> dict:
    """单条 dynamic 合成 case，直接看 b1/b2 读数（不写文件）。"""
    case: dict = {
        "case_id": "T-1", "layer": "dynamic", "kind": "刑", "mechanism": "刑",
        "char_a": char_a, "char_b": char_b, "expected_direction": expected,
    }
    if pillar_a is not None:
        case["pillar_a"] = pillar_a
    if pillar_b is not None:
        case["pillar_b"] = pillar_b
    if delta is not None:
        case["party_delta"] = delta
    if four_pillars is not None:
        case["four_pillars"] = four_pillars
    return mod.evaluate({"cases": [case]}, {"cases": []})["cases"][0]


def baseline_case(index: int, delta: int) -> dict:
    """午@M.b → 子@D.b；B2=子→午（克方 b），B1 由 delta 定。"""
    return {
        "case_id": f"BL-{index + 1:02d}", "chart_id": f"CH-{index // 2:02d}",
        "layer": "dynamic", "kind": "冲", "mechanism": "冲",
        "addr_a": "M.b", "char_a": "午", "addr_b": "D.b", "char_b": "子",
        "expected_direction": mod.DIRECTED, "party_delta": delta,
    }


def baseline_docs(*, correct: int = 32, b1_hits: int = 12) -> tuple[dict, dict]:
    cases = [baseline_case(i, 1 if i < b1_hits else -1) for i in range(40)]
    answers = {
        "schema_version": mod.SCHEMA_ANSWERS,
        "address_book": {"M.b": "午", "D.b": "子"},
        "cases": cases,
    }
    rows = []
    for i in range(40):
        a, b = ("M.b", "D.b") if i < correct else ("D.b", "M.b")
        rows.append({"case_id": f"BL-{i + 1:02d}", "a": a, "b": b,
                     "direction": mod.DIRECTED})
    return answers, output_doc(rows)


def clone_output(output: dict, flips: list[int] | None = None,
                 drop: int | None = None) -> dict:
    rows = copy.deepcopy(output["cases"])
    for index in flips or []:
        rows[index]["a"], rows[index]["b"] = rows[index]["b"], rows[index]["a"]
    if drop is not None:
        rows = [row for index, row in enumerate(rows) if index != drop]
    return {"schema_version": mod.SCHEMA_OUTPUT, "cases": rows}


# ── 1. T-184 delta（B1 的输入） ─────────────────────────────────────────────

def test_t184_delta_v1_vectors() -> None:
    # docs/specs/party-direction-v1.md §2.8 的 V1a/V1b：只验计数口径，非真实盘。
    assert mod.compute_party_delta("甲子 戊午 辛辰 壬戌") == -1
    assert mod.compute_party_delta("甲子 戊午 庚辰 壬戌") == 0


def test_t184_delta_rejects_bad_pillars() -> None:
    with pytest.raises(mod.InputError, match="四柱"):
        mod.compute_party_delta("甲子 戊午 辛辰")
    with pytest.raises(mod.InputError, match="天干\\+地支"):
        mod.compute_party_delta("甲子 戊午 辛 壬戌")


def test_t184_delta_matches_t187_receipts() -> None:
    """独立实现对齐：T-187 运行人现算的 party.delta 逐条复现（不是新结果）。"""
    run = json.loads(T187_RUN.read_text(encoding="utf-8"))
    answers = json.loads(T187_ANSWERS.read_text(encoding="utf-8"))
    four = {case["case_id"]: case["four_pillars"] for case in answers["cases"]}
    checked = 0
    for case in run["cases"]:
        if "party" not in case:
            continue
        checked += 1
        assert mod.compute_party_delta(four[case["case_id"]]) == case["party"]["delta"], case["case_id"]
    assert checked == 17


# ── 2. B1 = delta 符号（平局柱序左） ────────────────────────────────────────

@pytest.mark.parametrize("delta,actor", [(1, "b"), (-1, "a")])
def test_b1_delta_sign(delta: int, actor: str) -> None:
    row = single_dynamic("子", "午", pillar_a="Y", pillar_b="M", delta=delta)
    assert row["b1"]["delta"] == delta
    assert row["b1"]["basis"] == "party_delta"
    assert row["b1"]["actor"] == actor
    assert row["b1"]["predicted"] == ("b→a" if actor == "b" else "a→b")


@pytest.mark.parametrize("pillar_a,pillar_b,actor", [("Y", "D", "a"), ("D", "Y", "b")])
def test_b1_tie_uses_left_pillar(pillar_a: str, pillar_b: str, actor: str) -> None:
    row = single_dynamic("子", "午", pillar_a=pillar_a, pillar_b=pillar_b, delta=0)
    assert row["b1"]["basis"] == "delta_zero_pillar_left"
    assert row["b1"]["actor"] == actor


def test_b1_same_party_abstains_but_b2_covers() -> None:
    # 未戌同为燥土（F）：delta 符号无法在同类端之间定向 → B1 弃权，不编方向。
    row = single_dynamic("未", "戌", pillar_a="M", pillar_b="D", delta=5)
    assert row["b1"]["basis"] == "delta_party_ambiguous"
    assert row["b1"]["actor"] is None and row["b1"]["predicted"] is None
    # 四库 fallback 由 B2 兜住（D 为主位 → actor=b）。
    assert row["b2"]["predicted"] == "b→a"
    assert row["b2"]["basis"] == "same_element_main_position"


def test_b1_from_four_pillars_and_conflict_guard() -> None:
    row = single_dynamic("子", "午", pillar_a="Y", pillar_b="M",
                         four_pillars="甲子 戊午 辛辰 壬戌")
    assert row["b1"]["delta"] == -1
    assert row["b1"]["basis"] == "party_delta" and row["b1"]["actor"] == "a"

    case = {
        "case_id": "T-1", "layer": "dynamic", "kind": "刑", "mechanism": "刑",
        "char_a": "子", "char_b": "午", "pillar_a": "Y", "pillar_b": "M",
        "expected_direction": mod.DIRECTED, "party_delta": 0,
        "four_pillars": "甲子 戊午 辛辰 壬戌",
    }
    with pytest.raises(mod.InputError, match="不一致"):
        mod.evaluate({"cases": [case]}, {"cases": []})


def test_b1_without_delta_is_not_invented() -> None:
    row = single_dynamic("子", "午", pillar_a="Y", pillar_b="M")
    assert row["b1"]["basis"] == "no_delta"
    assert row["b1"]["actor"] is None


# ── 3. B2 = 本气克/生/同五行四库主位端 ─────────────────────────────────────

@pytest.mark.parametrize("char_a,char_b,basis,actor", [
    ("子", "午", "ke", "a"),      # 水克火 → 子
    ("午", "子", "ke", "b"),      # 水克火 → 子
    ("卯", "酉", "ke", "b"),      # 金克木 → 酉
    ("酉", "卯", "ke", "a"),
    ("寅", "亥", "sheng", "b"),   # 水生木 → 亥
    ("亥", "寅", "sheng", "a"),
    ("巳", "丑", "sheng", "a"),   # 火生土 → 巳
    ("丑", "巳", "sheng", "b"),
])
def test_b2_ke_and_sheng(char_a: str, char_b: str, basis: str, actor: str) -> None:
    row = single_dynamic(char_a, char_b, pillar_a="Y", pillar_b="M")
    assert row["b2"]["basis"] == basis
    assert row["b2"]["actor"] == actor
    assert row["b2"]["predicted"] == ("a→b" if actor == "a" else "b→a")


@pytest.mark.parametrize("char_a,char_b,pillar_a,pillar_b,actor,basis", [
    ("辰", "戌", "Y", "M", "b", "same_element_later_pillar"),   # 同宾 → 柱序后 M(b)
    ("丑", "未", "Y", "H", "b", "same_element_main_position"),  # H 主位优先
    ("丑", "戌", "D", "H", "b", "same_element_later_pillar"),   # 同主 → 柱序后 H(b)
    ("未", "戌", "M", "D", "b", "same_element_main_position"),  # D 主位优先
    ("辰", "戌", "D", "Y", "a", "same_element_main_position"),  # D 主位优先
    ("未", "戌", "D", "H", "b", "same_element_later_pillar"),   # 同主 → 柱序后 H(b)
])
def test_b2_four_muku_main_position(char_a: str, char_b: str, pillar_a: str, pillar_b: str,
                                    actor: str, basis: str) -> None:
    row = single_dynamic(char_a, char_b, pillar_a=pillar_a, pillar_b=pillar_b)
    assert row["b2"]["basis"] == basis
    assert row["b2"]["actor"] == actor
    assert row["b2"]["predicted"] is not None


@pytest.mark.parametrize("char_a,char_b", [("辰", "戌"), ("丑", "未"), ("丑", "戌"), ("未", "戌")])
def test_b2_four_muku_never_abstains(char_a: str, char_b: str) -> None:
    # A+ §4：四库题 B2 不得弃权 0；不同柱位都要给出方向。
    for pillar_a, pillar_b in [("Y", "M"), ("M", "D"), ("D", "H"), ("Y", "H")]:
        row = single_dynamic(char_a, char_b, pillar_a=pillar_a, pillar_b=pillar_b)
        assert row["b2"]["actor"] is not None
        assert row["b2"]["predicted"] is not None


# ── 4. margin = correct − max(B1,B2) ───────────────────────────────────────

def test_margin_dynamic_minus_best_baseline(tmp_path: Path) -> None:
    answers, output = baseline_docs(correct=32, b1_hits=12)
    result = evaluate(tmp_path, answers, output)
    baselines = result["baselines"]

    assert result["layers"]["dynamic"]["correct"] == 32
    assert baselines["total"] == 40 and baselines["correct"] == 32
    assert baselines["b1"]["correct"] == 12 and baselines["b1"]["available"] == 40
    assert baselines["b2"]["correct"] == 0      # 答案写反了本气克向 → B2 全不中
    assert baselines["best"] == "b1" and baselines["best_correct"] == 12
    assert baselines["margin"] == 20
    assert baselines["margin"] == baselines["correct"] - baselines["best_correct"]
    assert baselines["margin_comparable"] is True


def test_margin_marks_incomparable_without_delta(tmp_path: Path) -> None:
    answers, output = baseline_docs()
    answers["cases"][0].pop("party_delta")
    baselines = evaluate(tmp_path, answers, output)["baselines"]
    assert baselines["b1"]["available"] == 39 and baselines["b1"]["abstain"] == 1
    assert baselines["b1"]["data_missing"] == 1
    assert baselines["margin_comparable"] is False
    assert baselines["b1"]["correct"] == 11


def test_margin_comparable_when_b1_legitimately_abstains() -> None:
    # 未戌同类端：B1 合法弃权（不是缺数据），B2 覆盖；margin 仍可比。
    case = {
        "case_id": "T-1", "layer": "dynamic", "kind": "刑", "mechanism": "刑",
        "char_a": "未", "char_b": "戌", "pillar_a": "M", "pillar_b": "D",
        "expected_direction": mod.DIRECTED, "party_delta": 5,
    }
    baselines = mod.evaluate({"cases": [case]}, {"cases": []})["baselines"]
    assert baselines["b1"]["abstain"] == 1 and baselines["b1"]["data_missing"] == 0
    assert baselines["b2"]["available"] == 1
    assert baselines["margin_comparable"] is True


# ── 5. chart_id 聚类 ───────────────────────────────────────────────────────

def test_chart_cluster_macro_all_correct_and_bootstrap(tmp_path: Path) -> None:
    answers, output = baseline_docs(correct=32)
    cluster = evaluate(tmp_path, answers, output)["chart_cluster"]
    assert cluster["charts"] == 20 and cluster["cases"] == 40
    assert cluster["case_weighted_accuracy"]["value"] == pytest.approx(0.8)
    assert cluster["chart_macro_accuracy"] == pytest.approx(0.8)
    assert cluster["all_correct_charts"] == 16
    assert cluster["all_correct_chart_rate"]["denominator"] == 20
    assert cluster["bootstrap95"]["lower"] == pytest.approx(0.6)
    assert cluster["bootstrap95"]["upper"] == pytest.approx(0.95)
    assert cluster["bootstrap"]["iterations"] == 2000
    assert cluster["chart_sizes"] == {"2": 20}


def test_chart_cluster_bootstrap_is_deterministic(tmp_path: Path) -> None:
    answers, output = baseline_docs()
    first = evaluate(tmp_path, answers, output)["chart_cluster"]
    second = evaluate(tmp_path, answers, output)["chart_cluster"]
    assert first == second


def test_chart_cluster_penalizes_concentrated_errors(tmp_path: Path) -> None:
    # 同样 32/40：误差集中在 4 个盘 vs 分散在 8 个盘，全对盘率不同（聚类要看见相关性）。
    answers, output = baseline_docs(correct=40)
    spread = clone_output(output, flips=list(range(0, 16, 2)))
    cluster = evaluate(tmp_path, answers, spread)["chart_cluster"]
    assert cluster["cases"] == 40 and cluster["correct"] == 32
    assert cluster["chart_macro_accuracy"] == pytest.approx(0.8)
    assert cluster["all_correct_charts"] == 12
    assert cluster["all_correct_chart_rate"]["value"] == pytest.approx(0.6)


def test_pillar_addresses_are_per_chart() -> None:
    # 真实 anchor 的 Y.b/M.b 在不同盘指向不同的字；不得因全局地址表冲突而拒绝。
    cases = [
        {"case_id": "A-1", "chart_id": "CH-A", "layer": "dynamic", "kind": "冲",
         "mechanism": "冲", "addr_a": "M.b", "char_a": "午", "addr_b": "D.b",
         "char_b": "子", "expected_direction": mod.DIRECTED, "party_delta": 1},
        {"case_id": "B-1", "chart_id": "CH-B", "layer": "dynamic", "kind": "冲",
         "mechanism": "冲", "addr_a": "M.b", "char_a": "子", "addr_b": "D.b",
         "char_b": "午", "expected_direction": mod.DIRECTED, "party_delta": -1},
    ]
    output = output_doc([
        obs("A-1", "M.b", "D.b", mod.DIRECTED),
        obs("B-1", "M.b", "D.b", mod.DIRECTED),
    ])
    result = mod.evaluate({"cases": cases}, output)
    assert [row["status"] for row in result["cases"]] == ["correct", "correct"]
    assert result["chart_cluster"]["charts"] == 2


# ── 6. 3 次方向一致率 ──────────────────────────────────────────────────────

def test_three_run_direction_consistency(tmp_path: Path) -> None:
    answers, output = baseline_docs()
    run3 = clone_output(output, flips=[0, 1, 2, 3])  # 第 3 次再翻 4 条定向
    result = mod.evaluate_runs(answers, [output, output, run3])
    consistency = result["consistency"]
    assert consistency["runs"] == 3 and consistency["three_runs"] is True
    assert consistency["dynamic"]["cases"] == 40
    assert consistency["dynamic"]["consistent"] == 36
    assert consistency["dynamic"]["rate"]["value"] == pytest.approx(0.9)
    assert consistency["all"]["consistent"] == 36


def test_consistency_missing_case_is_inconsistent() -> None:
    answers, output = baseline_docs()
    missing = clone_output(output, drop=5)
    consistency = mod.evaluate_runs(
        answers, [output, missing, output]
    )["consistency"]
    assert consistency["dynamic"]["consistent"] == 39


def test_consistency_single_run_not_applicable() -> None:
    answers, output = baseline_docs()
    consistency = mod.evaluate_runs(answers, [output])["consistency"]
    assert consistency["three_runs"] is False
    assert consistency["dynamic"]["rate"] is None


# ── 7. T-187 回归（只读冻结产物，复算三数，不宣称新结果） ──────────────────

def test_t187_regression_three_numbers() -> None:
    run = json.loads(T187_RUN.read_text(encoding="utf-8"))
    answers = json.loads(T187_ANSWERS.read_text(encoding="utf-8"))
    regression = mod.t187_regression(run, answers)
    assert regression["cases"] == 40
    assert regression["edge_match"] == 12          # 12/40
    assert regression["edge_mismatch"] == 28       # 28/40
    assert regression["edge_match_rate"]["value"] == pytest.approx(0.3)
    assert regression["direction_delivered"] == 20
    assert regression["direction_correct"] == 2    # 2/20
    assert regression["direction_rate"]["value"] == pytest.approx(0.1)
    assert len(regression["edge_match_case_ids"]) == 12


def test_t187_regression_does_not_double_count_routing() -> None:
    run = json.loads(T187_RUN.read_text(encoding="utf-8"))
    answers = json.loads(T187_ANSWERS.read_text(encoding="utf-8"))
    regression = mod.t187_regression(run, answers)
    assert regression["cases"] == len(answers["cases"]) == 40
    assert not set(regression["edge_match_case_ids"]) - {
        case["case_id"] for case in answers["cases"]
    }


def test_t187_regression_recomputes_instead_of_hardcoding() -> None:
    run = json.loads(T187_RUN.read_text(encoding="utf-8"))
    answers = json.loads(T187_ANSWERS.read_text(encoding="utf-8"))
    baseline = mod.t187_regression(run, answers)
    mutated = copy.deepcopy(run)
    target = next(case for case in mutated["cases"] if case["case_id"] == "PF-002")
    target["a"], target["b"] = target["b"], target["a"]  # 边仍对（无序），定向翻反
    after = mod.t187_regression(mutated, answers)
    assert after["edge_match"] == baseline["edge_match"]
    assert after["direction_correct"] == baseline["direction_correct"] - 1


# ── 8. ambiguous 只读 source loader（不改引文口径） ────────────────────────

def _source_root(tmp_path: Path) -> Path:
    root = tmp_path / "sources"
    (root / "duan").mkdir(parents=True)
    (root / "duan" / "fixture-ambiguous.md").write_text(
        AMB_TEXTS[AMB_LOC1] + "\n" + AMB_TEXTS[AMB_LOC2], encoding="utf-8"
    )
    return root


def _loader_docs() -> tuple[dict, dict]:
    case = dict(ambiguous_cases()[0])
    case.pop("source_texts")
    case["source_refs"] = [AMB_LOC1, AMB_LOC2]
    output = output_doc([
        obs(case["case_id"], case["char_a"], case["char_b"], mod.NEEDS_JUDGMENT,
            conflict_quotes=[Q_FOR, Q_AGAINST]),
    ])
    return {"cases": [case]}, output


def test_source_loader_fills_missing_source_texts(tmp_path: Path) -> None:
    answers, output = _loader_docs()
    loader = mod.SourceLoader(_source_root(tmp_path))
    result = mod.evaluate(answers, output, source_loader=loader)
    assert result["layers"]["ambiguous"]["correct"] == 1
    assert result["layers"]["ambiguous"]["quotes_verbatim"] == 2


def test_source_loader_is_required_when_source_texts_missing() -> None:
    answers, output = _loader_docs()
    with pytest.raises(mod.InputError, match="source_texts"):
        mod.evaluate(answers, output)


def test_source_loader_keeps_quote_semantics(tmp_path: Path) -> None:
    answers, output = _loader_docs()
    output["cases"][0]["conflict_quotes"] = ["未戌相刑无库可开", Q_AGAINST]
    result = mod.evaluate(answers, output,
                          source_loader=mod.SourceLoader(_source_root(tmp_path)))
    ambiguous = result["layers"]["ambiguous"]
    assert ambiguous["correct"] == 0 and ambiguous["quote_fail"] == 1
    assert result["cases"][0]["reason"] == "quote_not_verbatim"


def test_source_texts_take_precedence_over_loader() -> None:
    def boom(_locator: str) -> str:
        raise AssertionError("有 source_texts 时不得调用 loader")

    case = ambiguous_cases()[0]  # 自带 source_texts
    output = output_doc([
        obs(case["case_id"], case["char_a"], case["char_b"], mod.NEEDS_JUDGMENT,
            conflict_quotes=[Q_FOR, Q_AGAINST]),
    ])
    result = mod.evaluate({"cases": [case]}, output, source_loader=boom)
    assert result["layers"]["ambiguous"]["correct"] == 1


def test_source_loader_rejects_escape_and_missing(tmp_path: Path) -> None:
    loader = mod.SourceLoader(_source_root(tmp_path))
    with pytest.raises(mod.InputError, match="越出"):
        loader("sources/../escape.md:L1")
    with pytest.raises(mod.InputError, match="行号"):
        loader("sources/duan/fixture-ambiguous.md:L9")
    with pytest.raises(mod.InputError, match="不存在"):
        loader("sources/duan/nope.md:L1")
    with pytest.raises(mod.InputError, match="形式"):
        loader("sources/duan/fixture-ambiguous.md")


def test_cli_source_loader_flag(tmp_path: Path, capsys) -> None:
    answers, output = _loader_docs()
    ap, sp = write_docs(tmp_path, answers, output)
    root = _source_root(tmp_path)
    code = mod.main(["--answers", str(ap), "--system-output", str(sp),
                     "--source-loader", "--source-root", str(root), "--json"])
    assert code == 0
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["layers"]["ambiguous"]["correct"] == 1


# ── 9. CLI：多次运行 + T-187 回归 + 控制台 ─────────────────────────────────

def test_cli_three_runs_and_t187_flags(tmp_path: Path, capsys) -> None:
    answers, output = baseline_docs()
    ap, sp = write_docs(tmp_path, answers, output)
    code = mod.main(["--answers", str(ap), "--system-output", str(sp),
                     "--system-output", str(sp), "--system-output", str(sp), "--json"])
    assert code == 0
    parsed = json.loads(capsys.readouterr().out)
    assert parsed["consistency"]["three_runs"] is True
    assert parsed["consistency"]["dynamic"]["consistent"] == 40

    code2 = mod.main(["--answers", str(ap), "--system-output", str(sp),
                      "--t187-run", str(T187_RUN), "--t187-answers", str(T187_ANSWERS),
                      "--json"])
    assert code2 == 0
    parsed2 = json.loads(capsys.readouterr().out)
    regression = parsed2["t187_regression"]
    assert (regression["edge_match"], regression["direction_correct"],
            regression["edge_mismatch"]) == (12, 2, 28)


def test_console_output_mentions_baselines_cluster_and_consistency(
        tmp_path: Path, capsys) -> None:
    answers, output = baseline_docs()
    ap, sp = write_docs(tmp_path, answers, output)
    assert mod.main(["--answers", str(ap), "--system-output", str(sp)]) == 0
    text = capsys.readouterr().out
    assert "基线" in text and "B1" in text and "margin" in text and "+20" in text
    assert "chart 聚类" in text and "bootstrap95" in text
    assert "3 次方向一致" in text
