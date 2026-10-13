"""as-of 盲断闭环 · root_level 双证据门启发式校验（事后复核用）。

背景（根因诊断，见 reports/as-of-life-state-blind-judgment-root-cause-report.md）：
对已核验案例 RF000149、RF000164 的复核发现，两案的 ``STRONG_ROOT`` 判定理由
（冻结产物 ``frozen_prediction.confidence_qualitative`` 字段）都只引用了十二长生
根气强弱描述（例如"日支临官、时支帝旺，根气结构性极强"），而没有按
plans/as-of-life-state-reasoning-design-2026-07-18.md 第285行起规定的"双证据门"
说明：

1. 命盘结构证据：原局是否已有与候选事件对应的领域、对象、作用方向和承载节点；
2. 原始语料证据：是否存在可定位原文，支持该结构与该事件功能之间的映射。

日主根气强弱只回答"日主本身承载力强不强"，不回答"这个人在候选事件所属领域
（例如管理岗、商业技术复合岗）是否有对应结构"——这是两个不同的证据维度，把
前者当成后者的替代品，是一种可复现的判定捷径，不是随机噪声。

本模块只做启发式文本校验，不改变 ``engine.asof`` 任何契约、不拦截生产流程、
不具备强制力：它服务于人工在冻结前自查，或在事后复核报告中标注"该冻结记录的
root_level 判定理由是否只依赖根气强弱描述"。命中本检测不代表该判定必然错误，
只代表该判定理由的书面表述缺少双证据门要求的领域/对象定位说明，需要人工补充
确认。本模块不读取、不使用任何案例的 feedback.md。
"""
from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = (
    "ROOT_QI_ONLY_PATTERN",
    "DOMAIN_LOCATION_PATTERN",
    "SOURCE_CITATION_PATTERN",
    "RootLevelGateFinding",
    "check_root_level_justification",
)

# 十二长生根气强弱描述：命中这类词但缺少下面两类定位描述时，说明判定理由
# 可能只停留在"日主本身强弱"层面，没有触及候选事件所属领域的结构定位。
ROOT_QI_ONLY_PATTERN = re.compile(
    r"(临官|帝旺|长生|冠带|根气结构性(极强|很强|偏强))"
)

# 命盘结构证据的最小信号：判定理由中是否出现了对"候选事件所属领域/对象"的
# 具体定位描述（十神、宫位、既有路径等），而不仅仅是根气强弱形容。
DOMAIN_LOCATION_PATTERN = re.compile(
    r"(正官|七杀|正财|偏财|食神|伤官|印|比劫)[^。]{0,20}(潜藏|透出|透干|承载|对应|路径|结构)"
)

# 原始语料证据的最小信号：判定理由中是否引用了可定位原文（书名/篇名/条目）。
SOURCE_CITATION_PATTERN = re.compile(r"(参见|见|引自)[^。]{0,40}")


@dataclass(frozen=True, slots=True)
class RootLevelGateFinding:
    """单条 root_level 判定理由文本的双证据门自查结果。"""

    root_qi_only_hit: bool
    domain_location_hit: bool
    source_citation_hit: bool
    likely_shortcut: bool
    note: str


def check_root_level_justification(justification_text: str) -> RootLevelGateFinding:
    """对单条判定理由文本做双证据门启发式自查。

    ``likely_shortcut=True`` 表示：理由文本命中了十二长生根气强弱描述，但没有
    同时命中"候选事件所属领域/对象定位"信号。这是需要人工补充确认的信号，
    不是自动拒绝依据。命中原始语料引用信号不是必需条件（不强制要求），因为
    冻结产物的 ``confidence_qualitative`` 字段本身是简短摘要，完整语料引用
    通常保存在 ``root_evidence`` / ``source_citations`` 字段而不在这段摘要里；
    但若既缺少领域定位、又缺少语料引用，问题更严重，应在 note 中如实注明。
    """

    if not justification_text.strip():
        raise ValueError("justification text must not be empty")

    root_qi_only = bool(ROOT_QI_ONLY_PATTERN.search(justification_text))
    domain_location = bool(DOMAIN_LOCATION_PATTERN.search(justification_text))
    source_citation = bool(SOURCE_CITATION_PATTERN.search(justification_text))

    likely_shortcut = root_qi_only and not domain_location

    if likely_shortcut and not source_citation:
        note = (
            "命中根气强弱描述，未命中领域/对象定位信号，也未命中语料引用信号："
            "判定理由可能只停留在日主本身强弱层面，未说明候选事件所属领域的"
            "命盘结构证据，需要人工补充双证据门说明后才能确认 root_level。"
        )
    elif likely_shortcut:
        note = (
            "命中根气强弱描述，未命中领域/对象定位信号（但命中语料引用信号）："
            "仍建议人工确认判定理由是否明确说明了候选事件所属领域的命盘结构，"
            "而不仅是引用原文却未落实到具体领域对应关系。"
        )
    else:
        note = "未发现根气强弱替代领域定位的捷径信号；本检测不保证判定本身正确。"

    return RootLevelGateFinding(
        root_qi_only_hit=root_qi_only,
        domain_location_hit=domain_location,
        source_citation_hit=source_citation,
        likely_shortcut=likely_shortcut,
        note=note,
    )
