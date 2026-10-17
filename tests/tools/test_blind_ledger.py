"""tests/tools/test_blind_ledger.py · blind_ledger L1 测试（v9）

覆盖：
- claims 解析（正例 + 各种脏输入）
- seal 幂等 / 不可覆盖 / 零 claim 拒绝
- mode 锁定
- reveal 只允许 blind、只允许一次
- adjudicate 需先 reveal、不可重复（除非新版本）
- stats 纯函数汇总
- 篡改检测（改报告文本后 sha256 不匹配）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from tools import blind_ledger as bl

ROOT = Path(__file__).resolve().parents[2]


# ── fixtures ────────────────────────────────────────────────────────────────

VALID_REPORT = """# 八字命理分析报告 · 1980-02-09 02:00 · 乾造

> 四柱：`庚申 戊寅 壬子 辛丑` ｜ chart_id：`cf-x` ｜ profile：`zi_shi=late_zi_split`
> 盘面 schema：`relation-graph/v1` ｜ 地址契约：`addr/v1`

## 〇、一句话定调

测试用主脑句。

## 先把话说死：哪些是钉死的，哪些是我看的，哪些我不编

- **板上钉钉（盘面硬事实）**：测试。
- **大概率主断（多派收敛，我直接站队）**：测试。
- **我不编的（信息边界）**：测试。

## 一、命局画像：你是哪种人、靠什么吃饭

测试正文。

### 核心结构翻译

1. **杀印相生** —— 扛责换权（依据：`e001`、`M1-D-045`）

## 二、事业与财运：怎么干最顺、钱从哪来

测试正文。

- **核心饭碗与赛道定位（大概率）**：测试。
- **求财模式与漏财坑点**：测试。
- **阶段/大运节奏**：测试。

## 三、婚姻感情

测试正文。

## 四、流年实战指南（2026–2028）

| 流年 | 岁运引动核心 | 一句话主断 | 落地行动建议 | 盘面依据 |
|---|---|---|---|---|
| 2026 丙午 | 双午冲子 | 以守成为主 | 盘点现金，锁死三个月生活费 | `e027`/`e028` |

## 五、各派怎么看、我为什么这么裁

- **各派共识（直接当定论用）**：测试。
- **流派分歧点**：测试。
- **我的最终裁决（明确站队）**：**我采信段派做功路线为主**。理由是：测试。

## 六、几句实在话（收尾叮嘱）

1. **命局最大的底牌**：测试。
2. **最需要避开的坑**：测试。
3. **近期最关键的节点**：测试。

## 附：关键依据索引与可核验断语表

| 序号 | 报告章节 | 核心断语摘要 | 等级 | 盘面地址与边号 | 理论条目 ID 与出处 |
|---|---|---|---|---|---|
| 1 | 一 | 杀印相生，扛责换权 | 板上钉钉 | `M.s`/`Y.s`、`e001`/`e005` | `M1-D-045`（theory/raw/duan/d-small-theory.md:821） |
| 2 | 二 | 印化杀为主路径 | 大概率 | `e002`/`e006` | `M1-D-009`（theory/raw/duan/d01-deep-read.md:126） |
| 3 | 四 | 2026 双午冲子 | 大概率 | `LN2026.b`/`DY4.b`/`D.b`、`e027`/`e028` | `M1-D-060`（d02-theory.md:320） |

> 边界声明：本报告为基于传统命理典籍与确定性盘面事实的趋势性推演，供复盘与决策参考。
"""


@pytest.fixture()
def ledger_dir(tmp_path, monkeypatch):
    d = tmp_path / "blind_ledger"
    d.mkdir()
    monkeypatch.setattr(bl, "LEDGER_DIR", d)
    return d


@pytest.fixture()
def report_file(tmp_path):
    p = tmp_path / "report.md"
    p.write_text(VALID_REPORT, encoding="utf-8")
    return p


@pytest.fixture()
def feedback_file(tmp_path):
    p = tmp_path / "feedback.md"
    p.write_text(
        "# 反馈\n\n| 年份 | 已知事实 | 功能域 |\n|---|---|---|\n"
        "| 2013 | 结婚 | marriage |\n| 2016 | 换工作 | career |\n",
        encoding="utf-8",
    )
    return p


# ── claims 解析 ─────────────────────────────────────────────────────────────

def test_parse_claims_extracts_all_columns():
    claims = bl.parse_claims(VALID_REPORT)
    assert len(claims) == 3
    c0 = claims[0]
    assert c0["claim_id"] == "seq:1"
    assert c0["section"] == "一"
    assert c0["assertion"] == "杀印相生，扛责换权"
    assert c0["grade"] == "板上钉钉"
    assert "M.s" in c0["addrs"] and "Y.s" in c0["addrs"]
    assert "e001" in c0["edges"] and "e005" in c0["edges"]
    assert "M1-D-045" in c0["rule_ids"]


def test_parse_claims_handles_liunian_and_dayun_addrs():
    claims = bl.parse_claims(VALID_REPORT)
    c3 = claims[2]
    assert "LN2026.b" in c3["addrs"]
    assert "DY4.b" in c3["addrs"]
    assert "e027" in c3["edges"]


def test_parse_claims_returns_empty_when_no_table():
    assert bl.parse_claims("# 没有表格的报告\n\n正文而已。") == []


def test_parse_claims_skips_malformed_rows():
    text = VALID_REPORT.replace(
        "| 3 | 四 | 2026 双午冲子 | 大概率 | `LN2026.b`/`DY4.b`/`D.b`、`e027`/`e028` | `M1-D-060`（d02-theory.md:320） |",
        "| 缺序号 | 四 | 坏行 | 大概率 | | |",
    )
    claims = bl.parse_claims(text)
    assert len(claims) == 2


# ── seal ────────────────────────────────────────────────────────────────────

def test_seal_creates_ledger_with_hash(ledger_dir, report_file):
    rc = bl.cmd_seal("C-TEST-001", report_file, "blind", None)
    assert rc == 0
    data = json.loads(next(ledger_dir.glob("*.json")).read_text(encoding="utf-8"))
    assert data["mode"] == "blind"
    assert len(data["rounds"]) == 1
    r = data["rounds"][0]
    assert r["report_sha256"].startswith("sha256:")
    assert r["claims_sha256"].startswith("sha256:")
    assert len(r["claims"]) == 3


def test_seal_rejects_zero_claims(ledger_dir, tmp_path):
    bad = tmp_path / "bad.md"
    bad.write_text("# 无表格\n\n正文", encoding="utf-8")
    rc = bl.cmd_seal("C-TEST-BAD", bad, "blind", None)
    assert rc == 2
    assert not list(ledger_dir.glob("*.json"))


def test_seal_rejects_duplicate_round(ledger_dir, report_file):
    assert bl.cmd_seal("C-TEST-DUP", report_file, "blind", None) == 0
    rc = bl.cmd_seal("C-TEST-DUP", report_file, "blind", 1)
    assert rc == 2
    data = json.loads(next(ledger_dir.glob("*.json")).read_text(encoding="utf-8"))
    assert len(data["rounds"]) == 1


def test_seal_locks_mode(ledger_dir, report_file):
    assert bl.cmd_seal("C-TEST-MODE", report_file, "blind", None) == 0
    rc = bl.cmd_seal("C-TEST-MODE", report_file, "consult", None)
    assert rc == 2


def test_seal_detects_tampering(ledger_dir, report_file):
    assert bl.cmd_seal("C-TEST-TAMPER", report_file, "blind", None, []) == 0
    data = json.loads(next(ledger_dir.glob("*.json")).read_text(encoding="utf-8"))
    sealed = data["rounds"][0]["report_sha256"]
    report_file.write_text(VALID_REPORT + "\n篡改一行", encoding="utf-8")
    assert bl._sha256(report_file.read_text(encoding="utf-8-sig")) != sealed


def test_seal_records_declared_sources(ledger_dir, report_file):
    rc = bl.cmd_seal(
        "C-TEST-SRC", report_file, "blind", None,
        ["cases/C-2026-001/input.md", "reports/1980-02-09-....md"],
    )
    assert rc == 0
    data = json.loads(next(ledger_dir.glob("*.json")).read_text(encoding="utf-8"))
    assert len(data["rounds"][0]["declared_sources"]) == 2


def test_seal_blind_rejects_feedback_sources(ledger_dir, report_file):
    """blind 封存若声明读过 feedback，必须拒绝——否则污染准确率基线。"""
    rc = bl.cmd_seal(
        "C-TEST-LEAK", report_file, "blind", None,
        ["cases/C-2026-001/feedback.md"],
    )
    assert rc == 2
    assert not list(ledger_dir.glob("*.json"))


def test_seal_blind_rejects_analysis_md_source(ledger_dir, report_file):
    rc = bl.cmd_seal(
        "C-TEST-LEAK2", report_file, "blind", None,
        ["cases/C-2026-001/analysis.md"],
    )
    assert rc == 2


def test_seal_consult_allows_feedback_sources(ledger_dir, report_file):
    """consult 模式不标盲测，允许参考反馈。"""
    rc = bl.cmd_seal(
        "C-TEST-CONSULT-SRC", report_file, "consult", None,
        ["cases/C-2026-001/feedback.md"],
    )
    assert rc == 0


# ── reveal ──────────────────────────────────────────────────────────────────

def test_reveal_requires_prior_seal(ledger_dir, feedback_file):
    rc = bl.cmd_reveal("C-NO-SEAL", feedback_file)
    assert rc == 2


def test_reveal_rejects_consult_mode(ledger_dir, report_file, feedback_file):
    assert bl.cmd_seal("C-CONSULT", report_file, "consult", None) == 0
    rc = bl.cmd_reveal("C-CONSULT", feedback_file)
    assert rc == 2


def test_reveal_only_once(ledger_dir, report_file, feedback_file):
    assert bl.cmd_seal("C-REVEAL", report_file, "blind", None) == 0
    assert bl.cmd_reveal("C-REVEAL", feedback_file) == 0
    rc = bl.cmd_reveal("C-REVEAL", feedback_file)
    assert rc == 2


# ── adjudicate ──────────────────────────────────────────────────────────────

def _sealed_and_revealed(ledger_dir, report_file, feedback_file, case="C-ADJ"):
    assert bl.cmd_seal(case, report_file, "blind", None) == 0
    assert bl.cmd_reveal(case, feedback_file) == 0
    return case


def test_adjudicate_requires_reveal(ledger_dir, report_file):
    assert bl.cmd_seal("C-NO-REVEAL", report_file, "blind", None) == 0
    rc = bl.cmd_adjudicate("C-NO-REVEAL", 1, "seq:1", "hit", "证据", None)
    assert rc == 2


def test_adjudicate_records_verdict(ledger_dir, report_file, feedback_file):
    case = _sealed_and_revealed(ledger_dir, report_file, feedback_file, "C-ADJ-OK")
    rc = bl.cmd_adjudicate(case, 1, "seq:1", "hit", "2013 结婚应验", None)
    assert rc == 0
    data = json.loads(next(ledger_dir.glob("*.json")).read_text(encoding="utf-8"))
    o = data["reveal"]["outcomes"][0]
    assert o["verdict"] == "hit"
    assert o["claim_id"] == "seq:1"
    assert o["rule_id"] == "M1-D-045"  # 自动取该 claim 的首个规则


def test_adjudicate_rejects_duplicate(ledger_dir, report_file, feedback_file):
    case = _sealed_and_revealed(ledger_dir, report_file, feedback_file, "C-ADJ-DUP")
    assert bl.cmd_adjudicate(case, 1, "seq:1", "hit", "证据", None) == 0
    rc = bl.cmd_adjudicate(case, 1, "seq:1", "miss", "改主意", None)
    assert rc == 2


def test_adjudicate_rejects_unknown_claim(ledger_dir, report_file, feedback_file):
    case = _sealed_and_revealed(ledger_dir, report_file, feedback_file, "C-ADJ-BAD")
    rc = bl.cmd_adjudicate(case, 1, "seq:999", "hit", "证据", None)
    assert rc == 2


def test_adjudicate_rejects_bad_verdict(ledger_dir, report_file, feedback_file):
    case = _sealed_and_revealed(ledger_dir, report_file, feedback_file, "C-ADJ-V")
    rc = bl.cmd_adjudicate(case, 1, "seq:1", "maybe", "证据", None)
    assert rc == 2


# ── stats ───────────────────────────────────────────────────────────────────

def test_stats_reports_case_and_rule_level(ledger_dir, report_file, feedback_file, capsys):
    case = _sealed_and_revealed(ledger_dir, report_file, feedback_file, "C-STATS")
    bl.cmd_adjudicate(case, 1, "seq:1", "hit", "e1", None)
    bl.cmd_adjudicate(case, 1, "seq:2", "miss", "e2", None)
    bl.cmd_adjudicate(case, 1, "seq:3", "partial", "e3", None)
    rc = bl.cmd_stats(None, None)
    assert rc == 0
    out = capsys.readouterr().out
    assert "已对账 claim 数：3" in out
    assert "准确率：33.3%" in out
    assert "M1-D-045" in out
    assert "永不修改规则库" in out


def test_stats_empty_is_safe(ledger_dir, capsys):
    rc = bl.cmd_stats(None, None)
    assert rc == 0
    out = capsys.readouterr().out
    assert "已对账 claim 数：0" in out


# ── 与真实标杆报告集成 ──────────────────────────────────────────────────────

def test_parse_claims_on_real_benchmark_report():
    """标杆报告必须能解析出非空 claims（防止模板漂移）。"""
    p = ROOT / "reports" / "1980-02-09-乾-庚申戊寅壬子辛丑-human-report.md"
    if not p.exists():
        pytest.skip("标杆报告不存在")
    claims = bl.parse_claims(p.read_text(encoding="utf-8-sig"))
    assert len(claims) >= 10
    for c in claims:
        assert c["addrs"] or c["edges"], f"{c['claim_id']} 缺盘面依据"
        assert c["rule_ids"], f"{c['claim_id']} 缺规则 ID"
