"""as-of 盲断闭环 · theory/ 结构化规律库关键词检索（冻结前语料证据门）。

背景（根因诊断，见 reports/as-of-life-state-blind-judgment-root-cause-report.md
及后续 First Proof Point 复核）：`theory/{gao,duan,yang,ren,ziping,tiaohou_ditiansui}/
index.yaml` 四派及子平/滴天髓结构化规律库已经存在，但对 `engine/asof/` 全部模块
做 import 扫描零命中——as-of 引擎从未从这个库检索过任何规则，判定者只能凭记忆
临时手写 `root_evidence`/`source_citations`。

First Proof Point 复核证实库覆盖是足够的，只是没有被查：

- RF000164（正财+食神三见，判 STRONG_ROOT+ACTIVATE_EXISTING，事后 MISS）：
  `theory/ziping/index.yaml` 命中"我生者为食神……食神生财、制杀，喜身旺有根，
  忌枭神夺食"（源自《子平真诠》）——判定时完全没有检查原局是否有偏印夺食，
  而这条原文本可以直接作为该案 root_evidence 的检索来源。
- RF000149（正官潜藏，判 STRONG_ROOT+REPAIR_DEFECT，事后 MISS）：
  `theory/yang/index.yaml` 命中"正者要化偏者要制"铁律："正官用印化=贵……
  颠倒则半途而废"——判定时完全没有检查原局是否有印星去化正官。

本模块提供最小可行的关键词检索：加载全部 `theory/{school}/index.yaml`（跳过
`_ir/`、`raw/`、`prediction_models/`、`production/` 等非规律索引目录），
对每条规律的可搜索文本（兼容 `title+conclusion` 与 `claim+output.statement`
两种既有 schema 变体）做关键词匹配，返回可直接引用的 `TheoryHit`（含
school、rule_id、可读文本、来源定位）。

本模块只做只读检索，不修改任何 `theory/` 文件、不改变任何 `engine.asof`
契约、不自动把检索结果写入任何冻结记录——由判定者在冻结前手动调用、审阅、
决定是否采纳为 `root_evidence`/`source_citations` 的来源，这是刻意保留的
人工判断步骤，不是自动化管线。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

__all__ = (
    "THEORY_ROOT",
    "SEARCHABLE_SCHOOLS",
    "TheoryHit",
    "load_school_rules",
    "search_theory",
)

THEORY_ROOT = Path("theory")

# 只检索四派+子平+调候滴天髓的规律库本身；不检索 _ir/（派生索引）、raw/（未结构化
# 候选提取记录）、prediction_models/、production/、executable-slices-v1.yaml
# 等非规律条目文件，避免把同一条规律的多个派生副本重复返回。
SEARCHABLE_SCHOOLS = ("gao", "duan", "yang", "ren", "ziping", "tiaohou_ditiansui")


@dataclass(frozen=True, slots=True)
class TheoryHit:
    """单条命中规律；供判定者审阅后决定是否采纳为证据来源。"""

    school: str
    rule_id: str
    searchable_text: str
    source_file: str

    def as_citation_line(self) -> str:
        """生成可直接粘贴进冻结记录 root_evidence/source_citations 的一行文本。"""

        return f"[{self.school}:{self.rule_id}] {self.searchable_text} (来源: {self.source_file})"


def _extract_searchable_text(rule: dict) -> str:
    """兼容两种既有 schema 变体，拼接出该条规律的可搜索文本。

    变体一（gao/duan/yang/ren）：``title`` + ``conclusion``。
    变体二（ziping/tiaohou_ditiansui）：``claim`` + ``output.statement``。
    两个变体都可能同时缺失部分字段；缺失的部分跳过，不因缺字段报错，因为
    这是只读检索工具，遇到不完整条目应尽量返回可用文本而不是拒绝整条规律。
    """

    parts: list[str] = []
    for key in ("title", "conclusion", "claim"):
        value = rule.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    output = rule.get("output")
    if isinstance(output, dict):
        statement = output.get("statement")
        if isinstance(statement, str) and statement.strip():
            parts.append(statement.strip())
    return " ".join(parts)


def load_school_rules(school: str, *, theory_root: Path = THEORY_ROOT) -> tuple[dict, ...]:
    """加载单个派别 ``index.yaml`` 的全部规律条目（原始 dict，未做字段校验）。

    找不到文件或文件为空返回空元组，不视为错误——不是每个派别在每次调用时
    都必然有 index.yaml（例如仓库演化中可能新增/重命名派别目录）。
    """

    index_path = theory_root / school / "index.yaml"
    if not index_path.is_file():
        return ()
    with index_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        return ()
    rules = data.get("rules")
    if not isinstance(rules, list):
        return ()
    return tuple(rule for rule in rules if isinstance(rule, dict))


def search_theory(
    keywords: tuple[str, ...],
    *,
    schools: tuple[str, ...] = SEARCHABLE_SCHOOLS,
    theory_root: Path = THEORY_ROOT,
) -> tuple[TheoryHit, ...]:
    """按关键词（AND 语义：全部关键词都必须出现）检索 theory/ 规律库。

    这是刻意简单的子串匹配，不做分词、不做同义词扩展、不做相关性排序——
    命中结果的数量和质量取决于调用方选择的关键词是否贴合候选事件的十神
    结构与领域。调用方应把候选事件涉及的十神名称（如"正官""食神"）与
    关键动作词（如"印化""夺食"）作为关键词，而不是宽泛的领域名称。
    """

    if not keywords:
        raise ValueError("at least one keyword is required")
    if any(not keyword.strip() for keyword in keywords):
        raise ValueError("keywords must not be empty strings")

    hits: list[TheoryHit] = []
    for school in schools:
        index_path = theory_root / school / "index.yaml"
        for rule in load_school_rules(school, theory_root=theory_root):
            text = _extract_searchable_text(rule)
            if not text:
                continue
            if all(keyword in text for keyword in keywords):
                rule_id = rule.get("id")
                hits.append(
                    TheoryHit(
                        school=school,
                        rule_id=str(rule_id) if rule_id is not None else "UNKNOWN_ID",
                        searchable_text=text,
                        source_file=str(index_path),
                    )
                )
    return tuple(hits)
