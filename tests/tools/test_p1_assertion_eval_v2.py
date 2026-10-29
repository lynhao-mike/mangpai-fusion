"""tests/tools/test_p1_assertion_eval_v2.py · T-189a · 评分器 v2 核心的合成 fixture 测试。

只测尺子，不测命理结论，**不读真实 anchor-60 / T-187 产物**：

1. 三层分录 10/40/10 全对：correct/total、precision、Wilson 95%；
2. 32/8：precision 0.8、Wilson LB ≈65.2%、correct/total 0.8；
3. 全错（全部写反）：correct=0、Wilson [0, 8.8%]；
4. dynamic 上 nj=miss：nj 与 missing 记同样的 miss，不进 correct；
5. ambiguous：缺引文 / 只给一条 / 非逐字 / 重复 / 硬给方向 / 双引文逐字；
6. 地址↔字双向归一：答案只给地址、输出给字；大小写/空白地址；交换端点判 reversed；
7. 输入契约：三层混层、layer 与 kind 不符、ambigous 缺答案引文、重复 case、未登记 case 退出 2；
8. CLI：--json 退出码 0 且两次逐字节一致；坏输入退出码 2。
"""
from __future__ import annotations

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
