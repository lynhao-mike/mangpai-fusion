"""as-of 盲断闭环 · 冻结契约预检门（偏离A/B/D修复工具）。

背景：审计报告 reports/as-of-post-2026-07-18-alignment-audit.md §3.1、§3.2、
§3.4 确认三个高严重度偏离在每次冻结时都可能重现：

偏离A：职业中心描述用"或"连接过多互斥选项（如"技术方法、分析判断或复杂问题
解决之一"），覆盖面近乎全部知识工作，无法被证伪。

偏离B：事件候选窗口为 2～3 年加多选事件类型，精确应期不可核验；审计报告记录
R4 修复为单年、R5 仍为单年、fresh cohort 又退回 2～3 年，说明没有检测就会退化。

偏离D：completion_mode=ACTIVATE_EXISTING 且缺乏显性财官证据时，未冻结"能力
存在但现实兑现不稳"的同方向备选，把结构潜能直接等同于现实完成度。

本模块提供四条预检函数，覆盖上述偏离及理论证据协议；每条函数对应一个冻结产物
中的具体字段或字段组合。前三条是启发式检测，命中表示"存在需要人工复核的信号"，
不是自动拒绝冻结；理论证据检查是硬门控，字段缺失、为空或仅含占位文本时不得冻结。

理论证据的 locator 可达性校验是**报警项，不是阻断项**：它只读地确认 locator 指向的
理论库文件存在且行号在范围内，结论写进 ``TheoryEvidenceFinding.locator_findings``
并计入 ``ContractGateResult.any_issue_found`` 与 summary，但**不进入
``blocking_reasons``、不翻转 ``passes_gate``**。之所以默认不阻断，是因为 2026-10-19
的存量体检（T-110）发现 43 个已冻结 ``asof-blind-freeze.json`` 中已有 5 个 locator 失效
（详见 tasks/T-110/BRIEF.md）；存量清零前改阻断会让全部旧冻结包无法过门禁。存量修好后
可把 ``LOCATOR_REACHABILITY_BLOCKS_FREEZE`` 改 True 转为阻断。

除 locator 可达性校验外本模块不读写任何文件：该校验只以只读方式统计被引用理论库
文件的行数，不写入、不移动、不删除任何文件，也不修改任何 engine.asof 对象；它不是
as-of 两阶段协议的组成部分，只是协议写入前的独立自查步骤。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from tools.as_of_root_level_gate import RootLevelGateFinding, check_root_level_justification

__all__ = (
    "OR_COUNT_WARN_THRESHOLD",
    "MAX_WINDOW_MONTHS",
    "LOCATOR_REACHABILITY_BLOCKS_FREEZE",
    "LocatorReachabilityFinding",
    "CenterStatementFinding",
    "EventWindowFinding",
    "CompletionRealizationFinding",
    "TheoryEvidenceFinding",
    "ContractGateResult",
    "check_center_statement_breadth",
    "check_event_window",
    "check_completion_realization_guard",
    "check_theory_evidence",
    "check_locator_reachability",
    "run_contract_gate",
)

OR_COUNT_WARN_THRESHOLD = 3
MAX_WINDOW_MONTHS = 14.0

# locator 可达性校验默认只报警、不阻断冻结（见模块 docstring「存量体检」段）。
# 存量失效 locator 清零后，可把这里改 True 升级为硬门控。
LOCATOR_REACHABILITY_BLOCKS_FREEZE = False

# 冻结包中的 theory locator 形如 "path:start-end" 或 "path:line"，
# 多个引用可以用 ";" 串在一起。路径段不允许含 ":"，行号必须是十进制正整数。
_LOCATOR_TARGET_RE = re.compile(r"^(?P<path>[^:]+):(?P<start>\d+)(?:-(?P<end>\d+))?$")
_LOCATOR_SEPARATOR = ";"
_DAYS_PER_MONTH = 365.2425 / 12
_PLACEHOLDER_THEORY_EVIDENCE: frozenset[str] = frozenset(
    {
        "todo",
        "tbd",
        "n/a",
        "na",
        "无",
        "暂无",
        "待补充",
        "待填写",
        "待检索",
        "占位",
        "placeholder",
    }
)
_INCOMPLETE_REALIZATION_SIGNALS: tuple[str, ...] = (
    "间断",
    "不稳",
    "项目制",
    "自由接单",
    "频繁转岗",
    "待业",
    "转型",
    "收入不稳",
    "兑现不稳",
    "无法形成稳定",
    "尚未稳定",
    "过渡期",
)


@dataclass(frozen=True, slots=True)
class CenterStatementFinding:
    """职业中心描述宽泛性检查结果。"""

    or_count: int
    likely_too_broad: bool
    note: str


@dataclass(frozen=True, slots=True)
class EventWindowFinding:
    """单个事件候选的窗口跨度与描述宽度检查结果。"""

    candidate_id: str
    window_days: int
    window_months: float
    exceeds_limit: bool
    or_count_in_event: int
    note: str


@dataclass(frozen=True, slots=True)
class CompletionRealizationFinding:
    """现实兑现不完整备选的覆盖检查结果。"""

    has_activate_existing_center: bool
    has_incomplete_realization_alt: bool
    missing_realization_guard: bool
    note: str


@dataclass(frozen=True, slots=True)
class LocatorReachabilityFinding:
    """单个 locator（或其分号分隔的单个目标）的可达性检查结果。

    ``target`` 是去掉行号部分的仓库相对路径；``start``/``end`` 是请求的行号区间
    （``path`` 缺行号时表示无法解析，两者均为 0）。``reachable`` 为 False 时
    ``reason`` 说明是文件缺失、行号越界还是格式无法解析。
    """

    target: str
    start: int
    end: int
    reachable: bool
    reason: str


@dataclass(frozen=True, slots=True)
class TheoryEvidenceFinding:
    """理论库检索证据硬门控结果。"""

    evidence_count: int
    placeholder_only: bool
    blocks_freeze: bool
    note: str
    locator_findings: tuple[LocatorReachabilityFinding, ...] = ()
    locator_blocks_freeze: bool = False


@dataclass(frozen=True, slots=True)
class ContractGateResult:
    """冻结核心字段的四项提醒与一项硬门控汇总。"""

    center_statement_finding: CenterStatementFinding
    event_window_findings: tuple[EventWindowFinding, ...]
    completion_finding: CompletionRealizationFinding
    theory_evidence_finding: TheoryEvidenceFinding
    root_level_finding: RootLevelGateFinding | None
    locator_findings: tuple[LocatorReachabilityFinding, ...]
    locator_blocks_freeze: bool
    any_issue_found: bool
    passes_gate: bool
    blocking_reasons: tuple[str, ...]
    summary: str


def _count_disjunctions(text: str) -> int:
    """统计显式“或”及由末尾“或”统摄的顿号枚举分支。"""

    explicit_or_count = text.count("或")
    implied_or_count = text.count("、") if explicit_or_count else 0
    return explicit_or_count + implied_or_count


def check_center_statement_breadth(statement: str) -> CenterStatementFinding:
    """检查职业中心描述是否因过多“或”连接词而覆盖面过宽。

    ``or_count`` 包含显式“或”，以及在文本已有“或”时由它统摄的顿号枚举分支；
    例如“A、B、C或D”按三个析取连接计数。达到提醒阈值时，冻结者应检查这些
    分支是否真正互斥、是否各有独立命盘结构依据。这是启发式信号，不是自动拒绝。
    """

    or_count = _count_disjunctions(statement)
    likely_too_broad = or_count >= OR_COUNT_WARN_THRESHOLD
    if likely_too_broad:
        note = (
            f"职业中心描述含 {or_count} 个‘或’，达到宽泛性提醒阈值；请人工复核各分支"
            "是否互斥且分别有结构依据。本信号不是自动拒绝依据。"
        )
    else:
        note = (
            f"职业中心描述含 {or_count} 个‘或’，未达到宽泛性提醒阈值；本启发式检查"
            "不保证描述本身足够具体或可证伪。"
        )
    return CenterStatementFinding(or_count, likely_too_broad, note)


def check_event_window(
    candidate_id: str,
    window_start: str,
    window_end: str,
    center_event: str,
) -> EventWindowFinding:
    """检查单个事件候选的窗口跨度是否超过单年容差限制。

    超过14个月（约1年+2个月容差）时标记 ``exceeds_limit=True``；窗口天数按首尾
    日期差计算，月数按平均公历月 ``365.2425 / 12`` 天折算。事件描述中的“或”
    另行计数，供人工判断事件类型是否同样过宽。
    """

    start = date.fromisoformat(window_start)
    end = date.fromisoformat(window_end)
    if end < start:
        raise ValueError("window_end must not precede window_start")

    window_days = (end - start).days
    window_months = window_days / _DAYS_PER_MONTH
    exceeds_limit = window_months > MAX_WINDOW_MONTHS
    or_count = _count_disjunctions(center_event)

    if exceeds_limit:
        note = (
            f"候选 {candidate_id} 的窗口为 {window_days} 天（约 {window_months:.2f} 个月），"
            f"客观超过 {MAX_WINDOW_MONTHS:.1f} 个月限制；应考虑收窄到单年窗口。"
        )
    else:
        note = (
            f"候选 {candidate_id} 的窗口为 {window_days} 天（约 {window_months:.2f} 个月），"
            f"未超过 {MAX_WINDOW_MONTHS:.1f} 个月限制；仍应人工检查事件描述是否过宽。"
        )

    return EventWindowFinding(
        candidate_id=candidate_id,
        window_days=window_days,
        window_months=window_months,
        exceeds_limit=exceeds_limit,
        or_count_in_event=or_count,
        note=note,
    )


def check_completion_realization_guard(
    center_completion_mode: str,
    alternative_statements: tuple[str, ...],
) -> CompletionRealizationFinding:
    """检查中心为 ``ACTIVATE_EXISTING`` 时是否有现实兑现不稳的保护备选。

    ``missing_realization_guard=True`` 表示中心声称“激活既有结构”，但没有任何
    备选覆盖“能力存在但实际兑现不稳/间断/项目化”的同方向情况。这是偏离D的
    直接信号，但仍需人工结合显性财官证据复核，不由本函数自动拒绝冻结。
    """

    has_activate_existing = center_completion_mode == "ACTIVATE_EXISTING"
    has_incomplete_alt = any(
        signal in statement
        for statement in alternative_statements
        for signal in _INCOMPLETE_REALIZATION_SIGNALS
    )
    missing_guard = has_activate_existing and not has_incomplete_alt

    if missing_guard:
        note = (
            "中心使用 ACTIVATE_EXISTING，但备选未覆盖能力存在而现实兑现不稳、间断或"
            "项目化的同方向情况；需人工补充或确认现实完成度证据。"
        )
    elif has_activate_existing:
        note = "中心使用 ACTIVATE_EXISTING，且已有备选覆盖现实兑现不完整信号。"
    else:
        note = "中心未使用 ACTIVATE_EXISTING，本条现实兑现保护检查不触发。"

    return CompletionRealizationFinding(
        has_activate_existing_center=has_activate_existing,
        has_incomplete_realization_alt=has_incomplete_alt,
        missing_realization_guard=missing_guard,
        note=note,
    )


def _evidence_texts(value: object) -> tuple[str, ...]:
    """提取字符串或结构化证据中的非空文本叶节点。"""

    if isinstance(value, str):
        text = value.strip()
        return (text,) if text else ()
    if isinstance(value, dict):
        return tuple(text for child in value.values() for text in _evidence_texts(child))
    if isinstance(value, (tuple, list)):
        return tuple(text for child in value for text in _evidence_texts(child))
    return ()


def _repo_root() -> Path:
    """定位仓库根目录（本模块所在 tools/ 的上一级）。"""

    return Path(__file__).resolve().parent.parent


def _count_lines(path: Path) -> int:
    """只读统计文件行数；统计失败时返回 -1 交由上层记为不可达。"""

    try:
        with path.open("rb") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return -1


def check_locator_reachability(
    locator: str,
    repo_root: Path | None = None,
) -> tuple[LocatorReachabilityFinding, ...]:
    """校验一个 theory locator 指向的理论库文件是否存在、行号是否越界。

    locator 形如 ``path:start-end`` 或 ``path:line``，允许用 ``;`` 串起多个引用。
    路径按仓库相对路径解析（``repo_root`` 缺省时取本模块上两级）。只读，不写入、
    不创建、不删除任何文件；无法解析的目标以 ``reachable=False`` 返回而不抛异常。
    """

    base = (repo_root or _repo_root()).resolve()
    findings: list[LocatorReachabilityFinding] = []
    for raw in locator.split(_LOCATOR_SEPARATOR):
        target_text = raw.strip()
        if not target_text:
            continue
        match = _LOCATOR_TARGET_RE.match(target_text)
        if match is None:
            findings.append(
                LocatorReachabilityFinding(
                    target=target_text,
                    start=0,
                    end=0,
                    reachable=False,
                    reason="locator 格式无法解析；期望 path:start-end 或 path:line",
                )
            )
            continue

        relative = match.group("path").strip()
        start = int(match.group("start"))
        end = int(match.group("end") or match.group("start"))
        if start < 1 or end < start:
            findings.append(
                LocatorReachabilityFinding(
                    target=relative,
                    start=start,
                    end=end,
                    reachable=False,
                    reason=f"行号区间非法（{start}-{end}）；期望 start>=1 且 end>=start",
                )
            )
            continue

        candidate = base / relative.replace("\\", "/")
        if not candidate.is_file():
            findings.append(
                LocatorReachabilityFinding(
                    target=relative,
                    start=start,
                    end=end,
                    reachable=False,
                    reason=f"文件不存在：{relative}",
                )
            )
            continue

        total = _count_lines(candidate)
        if total < 0:
            findings.append(
                LocatorReachabilityFinding(
                    target=relative,
                    start=start,
                    end=end,
                    reachable=False,
                    reason=f"文件无法读取：{relative}",
                )
            )
            continue
        if end > total:
            findings.append(
                LocatorReachabilityFinding(
                    target=relative,
                    start=start,
                    end=end,
                    reachable=False,
                    reason=f"行号越界：{relative} 共 {total} 行，locator 请求 {start}-{end}",
                )
            )
            continue

        findings.append(
            LocatorReachabilityFinding(
                target=relative,
                start=start,
                end=end,
                reachable=True,
                reason=f"{relative} 共 {total} 行，请求 {start}-{end} 在范围内",
            )
        )
    return tuple(findings)


def _theory_locators(theory_evidence: tuple[object, ...] | None) -> tuple[str, ...]:
    """从结构化 theory_evidence 中按条目顺序取出全部字符串 locator。"""

    locators: list[str] = []
    for entry in theory_evidence or ():
        if isinstance(entry, dict):
            value = entry.get("locator")
            if isinstance(value, str) and value.strip():
                locators.append(value)
    return tuple(locators)


def check_theory_evidence(theory_evidence: tuple[object, ...] | None) -> TheoryEvidenceFinding:
    """要求理论证据非空且不能只由占位文本构成，并检查 locator 可达性。

    经实际检索后形成的“已检索关键词X/Y，无命中”是有效审计记录，不属于占位符；
    ``TODO``、``待补充``、``暂无`` 等不能证明检索发生，因而阻断冻结。既有冻结包
    使用的结构化引用对象也受同一规则检查。

    locator 可达性是叠加约束而非替代：结构化条目中的 ``locator`` 会被只读校验，
    结果写入 ``locator_findings``。它默认只报警不阻断（``locator_blocks_freeze``），
    只有 ``LOCATOR_REACHABILITY_BLOCKS_FREEZE=True`` 时才与占位文本一样阻断冻结；
    原有三个分支（缺失 / 占位 / 通过）的 ``blocks_freeze`` 语义保持不变。
    """

    entries = tuple(theory_evidence or ())
    texts = tuple(text for entry in entries for text in _evidence_texts(entry))
    locator_findings = tuple(
        finding
        for locator in _theory_locators(entries)
        for finding in check_locator_reachability(locator)
    )
    unreachable = tuple(finding for finding in locator_findings if not finding.reachable)
    locator_blocks_freeze = bool(unreachable) and LOCATOR_REACHABILITY_BLOCKS_FREEZE
    locator_note = (
        ""
        if not locator_findings
        else (
            f"另发现 {len(unreachable)}/{len(locator_findings)} 个 theory locator 不可达"
            "（文件缺失或行号越界），审计溯源已断，请人工复核。"
            if unreachable
            else f"{len(locator_findings)} 个 theory locator 均可达。"
        )
    )

    def _note(base: str) -> str:
        return base if not locator_note else f"{base}{locator_note}"

    if not entries or not texts:
        return TheoryEvidenceFinding(
            evidence_count=0,
            placeholder_only=False,
            blocks_freeze=True,
            note=_note(
                "缺少 theory_evidence：字段缺失或完全为空；必须写入真实检索命中或带关键词的无命中记录。"
            ),
            locator_findings=locator_findings,
            locator_blocks_freeze=locator_blocks_freeze,
        )

    placeholder_only = all(text.casefold() in _PLACEHOLDER_THEORY_EVIDENCE for text in texts)
    if placeholder_only:
        return TheoryEvidenceFinding(
            evidence_count=len(entries),
            placeholder_only=True,
            blocks_freeze=True,
            note=_note("theory_evidence 仅含占位文本；必须写入真实检索命中或带关键词的无命中记录。"),
            locator_findings=locator_findings,
            locator_blocks_freeze=locator_blocks_freeze,
        )

    return TheoryEvidenceFinding(
        evidence_count=len(entries),
        placeholder_only=False,
        blocks_freeze=locator_blocks_freeze,
        note=_note(
            "theory_evidence 非空且不是占位文本，理论证据硬门控通过。"
            if not locator_blocks_freeze
            else "theory_evidence 非空且不是占位文本，但 locator 不可达且本门禁已配置为阻断模式。"
        ),
        locator_findings=locator_findings,
        locator_blocks_freeze=locator_blocks_freeze,
    )


def run_contract_gate(
    center_statement: str,
    center_completion_mode: str,
    alternative_statements: tuple[str, ...],
    event_candidates: tuple[tuple[str, str, str, str], ...],
    theory_evidence: tuple[object, ...] | None = None,
    root_level: str | None = None,
    root_level_justification: str | None = None,
) -> ContractGateResult:
    """对即将写入冻结包的核心字段做四条提醒检查与一条硬门控。"""

    center_finding = check_center_statement_breadth(center_statement)
    event_findings = tuple(check_event_window(*candidate) for candidate in event_candidates)
    completion_finding = check_completion_realization_guard(
        center_completion_mode,
        alternative_statements,
    )
    theory_finding = check_theory_evidence(theory_evidence)
    root_level_finding = (
        check_root_level_justification(root_level_justification)
        if root_level == "STRONG_ROOT" and root_level_justification
        else None
    )
    root_level_issue = root_level_finding is not None and root_level_finding.likely_shortcut
    # locator 不可达是报警项：计入 any_issue_found 与 summary 让审计能看见，
    # 但默认不进入 blocking_reasons（见 LOCATOR_REACHABILITY_BLOCKS_FREEZE）。
    locator_alarm = any(not finding.reachable for finding in theory_finding.locator_findings)
    advisory_issue = (
        center_finding.likely_too_broad
        or any(finding.exceeds_limit for finding in event_findings)
        or completion_finding.missing_realization_guard
        or root_level_issue
    )
    blocking_reasons = (theory_finding.note,) if theory_finding.blocks_freeze else ()
    any_issue = advisory_issue or locator_alarm or bool(blocking_reasons)
    if blocking_reasons:
        summary = f"冻结契约硬门控未通过：{theory_finding.note}"
    elif locator_alarm:
        summary = "理论证据硬门控通过，但发现 locator 可达性报警：" + "; ".join(
            f"{finding.target}:{finding.start}-{finding.end} {finding.reason}"
            for finding in theory_finding.locator_findings
            if not finding.reachable
        )
    elif root_level_issue:
        summary = f"理论证据硬门控通过；发现 root_level 预检提醒：{root_level_finding.note}"
    elif advisory_issue:
        summary = "理论证据硬门控通过；发现冻结契约预检提醒，请人工复核命中项。"
    else:
        summary = "理论证据硬门控及四项冻结契约预检均通过；本结果不保证冻结内容必然正确。"
    return ContractGateResult(
        center_statement_finding=center_finding,
        event_window_findings=event_findings,
        completion_finding=completion_finding,
        theory_evidence_finding=theory_finding,
        root_level_finding=root_level_finding,
        locator_findings=theory_finding.locator_findings,
        locator_blocks_freeze=theory_finding.locator_blocks_freeze,
        any_issue_found=any_issue,
        passes_gate=not blocking_reasons,
        blocking_reasons=blocking_reasons,
        summary=summary,
    )
