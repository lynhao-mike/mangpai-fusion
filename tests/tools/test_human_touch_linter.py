"""tests/tools/test_human_touch_linter.py · WP-8 防骑墙门禁测试（v9 契约）

覆盖：
- 正例 ×2：内嵌最小合法 v7 样例 + T6 成品报告文件（存在才跑，否则 skip）
- 反例 ×12：在正例 1 基础上注入各类违规
- 契约测试 ×1：Linter 正则必须匹配当前 engine.cli 真实输出（抗引擎变更哨兵）

tests/tools/ 需在 pyproject.toml 的 testpaths 中显式注册，否则裸跑 pytest 不收集。
"""
from __future__ import annotations

import json as _json
import re
import subprocess as _sp
import sys as _sys
from pathlib import Path

import pytest

from tools import human_touch_linter as mod
from tools.human_touch_linter import lint_human_touch

ROOT = Path(__file__).resolve().parents[2]


# ============================================================
# 正例 1：最小合法 v7 样例
# ============================================================

VALID_SAMPLE = """# 八字命理分析报告 · 1980-02-09 02:00 · 乾造

> 四柱：`庚申 戊寅 壬子 辛丑` ｜ chart_id：`cf-3d87627d6c7762569b6c` ｜ profile：`zi_shi=late_zi_split; yin_changsheng=yin_reverse; tu_jigong=duan_split_earth`
> 盘面 schema：`relation-graph/v1` ｜ 地址契约：`addr/v1`

## 〇、一句话定调

你是靠专业资质和制度牌照吃饭的人，压力越大越能换成职权；短板是钱不进门，得靠你把本事递出去。

## 先把话说死：哪些是钉死的，哪些是我看的，哪些我不编

- **板上钉钉（盘面硬事实）**：庚申 戊寅 壬子 辛丑，日主壬，坐子帝旺；寅月戊土用事；庚辛双印生身；丑为金库，庚申入墓；子丑合化土。
- **大概率主断（多派收敛，我直接站队）**：事业走平台依附路线，靠资质和资历换权；2027 是结构松动年，2028 换挡。
- **我不编的（信息边界）**：未核验真太阳时；不判精确到月的事件，不猜具体数字。

## 一、命局画像：你是哪种人、靠什么吃饭

壬水日主，庚辛双印透干有根，天生是"靠知识和制度吃饭"的底色。寅月七杀当令，压力常伴，但印星把压力化成资历。

### 核心结构翻译

1. **杀印相生** —— 扛责换权：压力越大约能转化成职权与资历，适合在大平台里逐级爬（依据：`e001`/`e005`、`M1-D-045`）
2. **寅申冲（驿马逢冲）** —— 你坐不住冷板凳，跨城/跨部门调动、赛道切换是常态（依据：`e007`/`e008`）

## 二、事业与财运：怎么干最顺、钱从哪来

- **核心饭碗与赛道定位（大概率）**：进大平台或体制依附型单位，靠专业资质、制度牌照吃饭；不适合单打独斗做纯销售。
- **求财模式与漏财坑点**：财星不透，钱不会自己找上门，得靠你把作品和服务递出去；最大的破耗点是比劫分财与寅申冲带来的经营反复。
- **阶段/大运节奏**：2008–2017 辛巳运扎根；2018–2027 壬午运是爬坡与婚姻宫受冲的十年；2028–2037 癸未运换挡，丑未冲开金库。

## 三、婚姻感情

- **关系模式与配偶画像（大概率）**：妻宫子水被午冲、被丑合，感情是"既想稳住又总被搅动"的体质；配偶偏沉稳务实。
- **关键应期与相处建议**：2026 是震荡确认年，2027 谈实质，2028 定名分。建议：2027 年内和对方坐下来核查一次彼此的经济安排与既有承诺，把口头预期落成书面共识。

## 四、流年实战指南（2026–2028）

| 流年 | 岁运引动核心 | 一句话主断（动在何事、吉凶倾向） | 落地行动建议（动词+对象+场景+时限） | 盘面依据 |
|---|---|---|---|---|
| 2026 丙午 | 运岁双午冲子，午午自刑 | 婚、财、健三头同时晃，以守成为主 | 盘点手头现金，锁死三个月生活费；不做任何杠杆决定 | `e027`/`e028`/`e031` |
| 2027 丁未 | 丁壬合、子未穿、丑未冲开库 | 结构松动年，关系与资源同时松口 | 和配偶谈一次经济安排，核查既有合同；推进关系实质化 | `e012`/`e026`/`e028` |
| 2028 戊申 | 跨入癸未运，戊癸合、寅申冲再现 | 换挡年，岗位或赛道必然动一次 | 立字据锁定新合作条款；投简历前先剥离非核心业务 | `e008`/`e022`/`e028` |

## 五、各派怎么看、我为什么这么裁

- **各派共识（直接当定论用）**：杀印相生成格；印重身旺；财弱需靠输出换。
- **流派分歧点**：段派重做功路径（印化杀），杨派重财官受损打折扣。
- **我的最终裁决（明确站队）**：**我采信段派做功路线为主、杨派承载论为辅**。理由是：庚辛双印贴身有根、化杀路径完整，而财官确实弱且受冲，上限与落地要分开看。

## 六、几句实在话（收尾叮嘱）

1. **命局最大的底牌**：资质与资历，这是别人拿不走的东西。
2. **最需要避开的坑**：2026 年任何形式的杠杆与裸辞。
3. **近期最关键的节点**：2027 年内把关系和合同都落到纸面。

## 附：关键依据索引与可核验断语表

| 序号 | 报告章节 | 核心断语摘要 | 等级 | 盘面地址与边号 | 理论条目 ID 与出处 |
|---|---|---|---|---|---|
| 1 | 一 | 杀印相生，扛责换权 | 板上钉钉 | `M.s`/`Y.s`/`e001` | `M1-D-045`（d-small-theory.md:821） |
| 2 | 二 | 财弱，靠输出换 | 大概率 | `Y.b`/`M.b`/`e007` | `QT-壬-寅`（穷通宝鉴_part2.md:396） |
| 3 | 四 | 2027 丑未冲开库 | 大概率 | `H.b`/`e028` | `M3-R-042`（r01-r04-theory.md:224） |

> 边界声明：本报告为基于传统命理典籍与确定性盘面事实的趋势性推演，供复盘与决策参考。
"""


# ============================================================
# 正例 2：T6 成品报告文件
# ============================================================

POSITIVE_FILES = [
    ROOT / "reports" / "1980-02-09-乾-庚申戊寅壬子辛丑-human-report.md",
    ROOT / "reports" / "1980-02-09-四柱-庚申戊寅壬子辛丑-human-report.md",
    ROOT / "reports" / "1984-11-05-乾-甲子甲戌癸卯壬戌-人情味分析.md",
]


def test_valid_sample_passes() -> None:
    assert lint_human_touch(VALID_SAMPLE) == []


@pytest.mark.parametrize("path", POSITIVE_FILES, ids=lambda p: p.name)
def test_positive_files_pass(path: Path) -> None:
    if not path.exists():
        pytest.skip(f"文件不存在：{path.name}")
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    assert lint_human_touch(text) == []


# ============================================================
# 反例（在正例 1 基础上注入）
# ============================================================

def test_neg1_body_hedging_bu_ju() -> None:
    text = VALID_SAMPLE.replace(
        "## 二、事业与财运：怎么干最顺、钱从哪来",
        "## 二、事业与财运：怎么干最顺、钱从哪来\n\n但不能据此直接断升迁，前景有待观察。",
    )
    errs = lint_human_touch(text)
    assert errs
    assert any("检查2" in e for e in errs)


def test_neg2_body_hedging_buzu_duan() -> None:
    """v9 新增变体：不足以断"""
    text = VALID_SAMPLE.replace(
        "## 二、事业与财运：怎么干最顺、钱从哪来",
        "## 二、事业与财运：怎么干最顺、钱从哪来\n\n综合来看，不足以断现金收入会大增。",
    )
    errs = lint_human_touch(text)
    assert errs
    assert any("检查2" in e for e in errs)


def test_neg3_banned_word_in_dingdiao() -> None:
    text = VALID_SAMPLE.replace(
        "## 〇、一句话定调\n\n",
        "## 〇、一句话定调\n\n或许明年运程会有转机，但不宜妄断。\n\n",
    )
    errs = lint_human_touch(text)
    assert errs
    assert any("检查1" in e for e in errs)


def test_neg4_missing_wubian_marker() -> None:
    text = VALID_SAMPLE.replace("我不编", "信息边界")
    errs = lint_human_touch(text)
    assert errs
    assert any("检查3b" in e for e in errs)


def test_neg5_no_verdict_in_sec5() -> None:
    text = VALID_SAMPLE.replace(
        "- **我的最终裁决（明确站队）**：**我采信段派做功路线为主、杨派承载论为辅**。理由是：",
        "- **本节结论**：两派各有道理。",
    )
    errs = lint_human_touch(text)
    assert errs
    assert any("检查3c" in e for e in errs)


def test_neg6_vague_advice() -> None:
    text = VALID_SAMPLE.replace(
        "| 2026 丙午 | 运岁双午冲子，午午自刑 | 婚、财、健三头同时晃，以守成为主 | 盘点手头现金，锁死三个月生活费；不做任何杠杆决定 |",
        "| 2026 丙午 | 运岁双午冲子，午午自刑 | 婚、财、健三头同时晃，以守成为主 | 建议：宜重视书面约定，注意防范风险 |",
    )
    errs = lint_human_touch(text)
    assert errs
    assert any("检查3d" in e for e in errs)


def test_neg7_missing_fulu_section() -> None:
    text = VALID_SAMPLE.split("## 附：关键依据索引与可核验断语表")[0]
    errs = lint_human_touch(text)
    assert errs
    assert any("检查4" in e for e in errs)


def test_neg8_jihui_yu_chengben() -> None:
    text = VALID_SAMPLE.replace(
        "## 二、事业与财运：怎么干最顺、钱从哪来",
        "## 二、事业与财运：怎么干最顺、钱从哪来\n\n2027 年机会与调整成本并存。",
    )
    errs = lint_human_touch(text)
    assert errs
    assert any("检查2" in e for e in errs)


def test_neg9_fulu_without_evidence() -> None:
    text = VALID_SAMPLE.replace(
        "| 1 | 一 | 杀印相生，扛责换权 | 板上钉钉 | `M.s`/`Y.s`/`e001` | `M1-D-045`（d-small-theory.md:821） |",
        "| 1 | 一 | 杀印相生，扛责换权 | 板上钉钉 | 见上文 | 见上文 |",
    ).replace(
        "| 2 | 二 | 财弱，靠输出换 | 大概率 | `Y.b`/`M.b`/`e007` | `QT-壬-寅`（穷通宝鉴_part2.md:396） |",
        "| 2 | 二 | 财弱，靠输出换 | 大概率 | 见上文 | 见上文 |",
    ).replace(
        "| 3 | 四 | 2027 丑未冲开库 | 大概率 | `H.b`/`e028` | `M3-R-042`（r01-r04-theory.md:224） |",
        "| 3 | 四 | 2027 丑未冲开库 | 大概率 | 见上文 | 见上文 |",
    )
    errs = lint_human_touch(text)
    assert errs
    assert any("检查4" in e for e in errs)


def test_neg10_missing_sec5() -> None:
    head, _, tail = VALID_SAMPLE.partition("## 五、各派怎么看、我为什么这么裁")
    tail = tail.partition("## 六、几句实在话（收尾叮嘱）")[2]
    text = head + "## 六、几句实在话（收尾叮嘱）" + tail
    errs = lint_human_touch(text)
    assert errs
    assert any("检查3c" in e for e in errs)


def test_neg11_contract_breakdown(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mod, "SAMPLE_ADDRESSES", ("Y.s",))
    monkeypatch.setattr(mod, "ADDR_RE", re.compile(r"ZZZ"))
    errs = lint_human_touch(VALID_SAMPLE)
    assert errs
    assert any("契约失效" in e for e in errs)


def test_neg12_bold_year_cell_still_checked() -> None:
    """v9：流年表首格加粗不得逃过 3d 检查。"""
    text = VALID_SAMPLE.replace(
        "| 2026 丙午 | 运岁双午冲子，午午自刑 | 婚、财、健三头同时晃，以守成为主 | 盘点手头现金，锁死三个月生活费；不做任何杠杆决定 |",
        "| **2026 丙午** | 运岁双午冲子，午午自刑 | 婚、财、健三头同时晃，以守成为主 | 宜重视沟通，注意防范风险 |",
    )
    errs = lint_human_touch(text)
    assert errs
    assert any("检查3d" in e for e in errs)


# ============================================================
# 契约测试（抗引擎变更哨兵）
# ============================================================

def test_linter_contract_matches_live_engine() -> None:
    """契约哨兵：Linter 正则必须匹配当前引擎真实输出。

    引擎若变更地址格式或边号编号规则，本测试失败 → 强制同步 Linter。
    缺 PyYAML 等引擎依赖、或探针执行失败时 skip（不阻断门禁）。
    """
    if not (ROOT / "engine" / "cli.py").exists():
        pytest.skip("engine/cli.py 不存在")

    try:
        import yaml  # noqa: F401
    except ImportError:
        pytest.skip("缺 PyYAML，跳过引擎契约测试")

    # 带 --dayun-index/--liunian，一次运行覆盖原局(Y.s/M.b)、大运(DY4.*)、
    # 流年(LN2026.*) 三类地址与边号(e001)正则。
    cmd = [
        _sys.executable, "-m", "engine.cli", "relations",
        "--pillars", "庚申 戊寅 壬子 辛丑", "--gender", "乾",
        "--dayun-index", "4", "--liunian", "2026", "--json",
    ]
    try:
        proc = _sp.run(cmd, cwd=ROOT, capture_output=True, encoding="utf-8", timeout=180)
    except Exception as exc:
        pytest.skip(f"engine.cli 探针执行失败: {exc}")
    if proc.returncode != 0:
        pytest.skip(f"engine.cli 探针退出码 {proc.returncode}")

    data = _json.loads(proc.stdout)

    # 地址来源：优先 edges[].members（必然存在且直接对应边引用）；
    # members 元素一律 str，非字符串元素过滤掉，避免 re.search 抛 TypeError。
    addrs = sorted({
        m for e in data.get("edges", [])
        for m in e.get("members", ())
        if isinstance(m, str)
    })
    # 兜底：若 edges 未提供地址，退回 nodes（兼容两种输出形态）
    if not addrs and "nodes" in data:
        addrs = [n[0] for n in data["nodes"] if isinstance(n, (list, tuple)) and n]

    edge_ids = [
        e["id"] for e in data.get("edges", [])
        if isinstance(e, dict) and isinstance(e.get("id"), str)
    ]

    assert addrs, "engine.cli relations 未返回任何边成员地址"
    assert all(
        mod.ADDR_RE.search(a) or mod.DY_RE.search(a) or mod.LN_RE.search(a)
        for a in addrs
    ), (
        f"契约失效：引擎地址 {addrs} 存在不被 Linter 正则匹配的项。"
        f"请按 docs/analysis_human_touch.md §3.5.2 同步 "
        f"ADDRESS_SCHEMA_VERSION={mod.ADDRESS_SCHEMA_VERSION!r}、SAMPLE_ADDRESSES 与正则。"
    )
    assert edge_ids and all(mod.EDGE_RE.search(e) for e in edge_ids), (
        f"契约失效：边号 {edge_ids} 中有不被 EDGE_RE 匹配的项。"
    )
