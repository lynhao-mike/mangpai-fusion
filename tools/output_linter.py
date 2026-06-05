"""tools/output_linter.py · 兜底护栏 #2 · 输出格式 + 黑名单校验

实现 07-pipeline-flow.md § 八 的基础检查 +
06-confidence-model.md § 七/§ 十 的禁忌清单，并包含 v1.4 输出耦合与样式护栏。

支持两种输入：
  1. AnalysisOutput dataclass / dict（结构化）
  2. 一段 Markdown 文本（从 reports/*.md 中抽取断语后逐条校验）

输出 LintResult，含 errors + warnings + per-conclusion 详情。

依赖：标准库 + PyYAML（用于加载 mechanical-rules.yaml 黑名单）
能力：v1.2 基础护栏 + v1.4 W9/W10/W12/画像样式扩展
作者：Track-E
"""
from __future__ import annotations

import dataclasses
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Literal, Optional, Union

from engine.domain.confidence import (
    STAR_RANGES_PERCENT,
    expected_pct_range as _shared_expected_pct_range,
    is_star_percent_consistent,
    percent_to_star,
)
from engine.domain.social_clock import (
    INSTITUTIONAL_KEYWORDS,
    SOCIAL_CLOCK_RULES,
    SOCIAL_CLOCK_TOLERANCE,
)

try:
    import yaml  # type: ignore
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "output_linter.py 需要 PyYAML，请运行: pip install pyyaml"
    ) from e


# ============================================================
# 一、常量 / 区间表（与 06-confidence-model § 二 保持双向唯一）
# ============================================================

# ★ 区间表（左闭右闭百分比）。事实源在 engine.domain.confidence。
STAR_RANGES: dict[int, tuple[int, int]] = dict(STAR_RANGES_PERCENT)

VALID_SCHOOL_TAGS: set[str] = {"段", "杨", "任", "高", "共识", "互补", "独门", "冲突仲裁", "冲突"}

# 派别标签匹配：[...]，正文内任意字符；事后再用 VALID_SCHOOL_TAGS 过滤
SCHOOL_TAG_RE = re.compile(r"\[([^\]\n]{1,80})\]")

# ★N (XX%) 匹配，兼容三种写法（中英括号兼容、半全角数字、连写 ★）
# 1) ★3 (60%)        digit-form
# 2) ★★★ (60%)       repeat-form (1-5 stars)
STAR_PCT_RE_DIGIT = re.compile(
    r"★([1-5１-５])\s*[（(]\s*(\d{1,3})\s*%\s*[)）]"
)
STAR_PCT_RE_REPEAT = re.compile(
    r"(★{1,5})(?!\d)\s*[（(]\s*(\d{1,3})\s*%\s*[)）]"
)
STAR_PCT_RE = STAR_PCT_RE_DIGIT  # 旧名保留，外部用 parse_star_pct
STAR_ONLY_RE = re.compile(r"★([1-5])(?!\s*[（(]\s*\d)")
PCT_ONLY_RE = re.compile(r"(?<!★)\b(\d{1,3})%")

DEFAULT_RULES_YAML: Path = (
    Path(__file__).resolve().parent.parent / "engine" / "mechanical-rules.yaml"
)


# ============================================================
# 二、数据结构
# ============================================================

class Severity(str, Enum):
    ERROR = "ERROR"     # 阻塞输出
    WARNING = "WARN"    # 仅警告 / 降级
    INFO = "INFO"


@dataclass
class LintIssue:
    severity: Severity
    code: str           # "E1" / "W7" 等，对应 § 八 检查表
    message: str
    location: Optional[str] = None    # conclusion_id 或行号
    suggestion: Optional[str] = None


@dataclass
class LintResult:
    passed: bool        # 无 ERROR 即 True
    issues: list[LintIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[LintIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[LintIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    def add(
        self,
        severity: Severity,
        code: str,
        message: str,
        location: Optional[str] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        self.issues.append(LintIssue(
            severity=severity, code=code, message=message,
            location=location, suggestion=suggestion,
        ))
        if severity == Severity.ERROR:
            self.passed = False

    def format(self) -> str:  # pragma: no cover
        lines: list[str] = []
        for i in self.issues:
            head = f"[{i.severity.value} {i.code}]"
            loc = f" @ {i.location}" if i.location else ""
            lines.append(f"{head}{loc} {i.message}")
            if i.suggestion:
                lines.append(f"    → 建议: {i.suggestion}")
        if not lines:
            lines.append("[OK] linter passed (0 issue)")
        return "\n".join(lines)


# ============================================================
# 三、规则加载（mechanical-rules.yaml）
# ============================================================

@dataclass
class _RulesData:
    """从 mechanical-rules.yaml 加载的精简结构。"""
    blacklist_ids: set[str]                          # {"XF-001", ...}
    blacklist_aliases: dict[str, str]                # alias_lower → XF-id
    blacklist_blocked_outputs: dict[str, set[str]]   # XF-id → {domain1, ...}
    forbidden_hard: list[tuple[str, str]]            # [(phrase, reason), ...]
    forbidden_soft: list[tuple[str, str]]
    rule_ids: set[str]                               # {"MR-001", ...}


_RULES_CACHE: dict[str, tuple[tuple[int, int] | None, _RulesData]] = {}


def _empty_rules_data() -> _RulesData:
    return _RulesData(
        blacklist_ids=set(),
        blacklist_aliases={},
        blacklist_blocked_outputs={},
        forbidden_hard=[],
        forbidden_soft=[],
        rule_ids=set(),
    )


def _rules_signature(path: Path) -> tuple[int, int] | None:
    try:
        st = path.stat()
    except FileNotFoundError:
        return None
    return (st.st_mtime_ns, st.st_size)


def _load_rules_uncached(path: Path) -> _RulesData:
    if not path.exists():
        # 缺失 yaml = 仅做结构性 lint，黑名单功能降级
        return _empty_rules_data()

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    bl: list[dict[str, Any]] = data.get("blacklist") or []
    bl_ids: set[str] = set()
    bl_aliases: dict[str, str] = {}
    bl_blocked: dict[str, set[str]] = {}
    for b in bl:
        bid = str(b["id"])
        bl_ids.add(bid)
        bl_aliases[str(b.get("pattern", "")).strip().lower()] = bid
        for al in b.get("aliases") or []:
            bl_aliases[str(al).strip().lower()] = bid
        bl_blocked[bid] = set(b.get("blocked_in_outputs") or [])

    fp = data.get("forbidden_phrases") or {}
    hard = [(str(x["phrase"]), str(x.get("reason", ""))) for x in (fp.get("hard") or []) if isinstance(x, dict)]
    soft = [(str(x["phrase"]), str(x.get("reason", ""))) for x in (fp.get("soft") or []) if isinstance(x, dict)]

    rules = data.get("rules") or []
    rule_ids = {str(r["id"]) for r in rules if "id" in r}

    return _RulesData(
        blacklist_ids=bl_ids,
        blacklist_aliases=bl_aliases,
        blacklist_blocked_outputs=bl_blocked,
        forbidden_hard=hard,
        forbidden_soft=soft,
        rule_ids=rule_ids,
    )


def clear_rules_cache() -> None:
    """清空 mechanical-rules.yaml 解析缓存，主要供测试或热重载场景使用。"""
    _RULES_CACHE.clear()


def load_rules(yaml_path: Optional[Path] = None) -> _RulesData:
    p = Path(yaml_path) if yaml_path else DEFAULT_RULES_YAML
    key = str(p.resolve())
    sig = _rules_signature(p)
    cached = _RULES_CACHE.get(key)
    if cached is not None and cached[0] == sig:
        return cached[1]

    rules = _load_rules_uncached(p)
    _RULES_CACHE[key] = (sig, rules)
    return rules


# ============================================================
# 四、工具：★(%)/标签 正规化 + 区间一致性
# ============================================================

_STAR_FULLWIDTH_MAP = str.maketrans({
    "１": "1", "２": "2", "３": "3", "４": "4", "５": "5",
})


def parse_star_pct(text: str) -> Optional[tuple[int, int]]:
    """从字符串中抽取首个 ★N (XX%) 或 ★★★ (XX%) 组合。返回 (star, pct) 或 None。

    支持两种写法（v1.2 spec + v1.0/v2 实际报告）：
      - ``★3 (60%)``     digit-form
      - ``★★★ (60%)``    repeat-form
    """
    m = STAR_PCT_RE_DIGIT.search(text)
    if m:
        star_raw = m.group(1).translate(_STAR_FULLWIDTH_MAP)
        return int(star_raw), int(m.group(2))
    m = STAR_PCT_RE_REPEAT.search(text)
    if m:
        star = len(m.group(1))
        return star, int(m.group(2))
    return None


def is_star_pct_consistent(star: int, pct: int) -> bool:
    return is_star_percent_consistent(star, pct)


def expected_star_for_pct(pct: int) -> int:
    """给定 % 反推应该是 ★几（用于报错建议）"""
    return percent_to_star(pct)


def expected_pct_range(star: int) -> tuple[int, int]:
    return _shared_expected_pct_range(star)


# ============================================================
# 五、Conclusion 抽取（从 dict 或 markdown）
# ============================================================

@dataclass
class _Conclusion:
    """统一表示报告中一条断语，便于逐条 lint。"""
    raw_text: str                          # 原始字符串
    statement: Optional[str] = None        # 断语正文
    star: Optional[int] = None
    pct: Optional[int] = None
    school_tags: list[str] = field(default_factory=list)
    domain: Optional[str] = None
    yingqi_year: Optional[int] = None
    falsifiable: Optional[str] = None
    passed_layers: Optional[int] = None
    evidence_count: int = 0
    location: Optional[str] = None
    is_yingqi: bool = False                # 是否为应期断语


def _conclusion_from_dict(d: dict[str, Any], idx: int) -> _Conclusion:
    """把 FinalConclusion / GateResult dict 转为 _Conclusion。"""
    conf = d.get("confidence") or {}
    star = conf.get("star")
    pct = conf.get("percent")
    if isinstance(pct, float) and 0.0 <= pct <= 1.0:
        pct = int(round(pct * 100))
    elif isinstance(pct, (int, float)):
        pct = int(pct)
    else:
        pct = None
    school_tags: list[str] = []
    if "layer" in d:
        school_tags.append(str(d["layer"]))
    if "school" in d:
        school_tags.append(str(d["school"]))
    for s in (d.get("contributing_schools") or []):
        school_tags.append(str(s))
    evidence = d.get("evidence") or []
    domain = d.get("domain")
    yq = d.get("yingqi_year")
    is_yq = bool(yq) or (domain == "应期") or ("year" in d and "candidate_event" in d)
    if "year" in d and yq is None:
        yq = d.get("year")
    falsifiable = d.get("falsifiable")
    passed_layers = d.get("passed_layers")
    if passed_layers is None and conf:
        passed_layers = conf.get("passed_layers")

    statement = d.get("statement") or d.get("candidate_event") or d.get("description")

    return _Conclusion(
        raw_text=str(d),
        statement=statement,
        star=int(star) if isinstance(star, int) else None,
        pct=pct,
        school_tags=[t for t in school_tags if t],
        domain=str(domain) if domain else None,
        yingqi_year=int(yq) if isinstance(yq, int) else None,
        falsifiable=str(falsifiable) if falsifiable else None,
        passed_layers=int(passed_layers) if isinstance(passed_layers, int) else None,
        evidence_count=len(evidence),
        location=d.get("conclusion_id") or f"conclusion[{idx}]",
        is_yingqi=is_yq,
    )


# Markdown 抽取：每个含 ★ 的"行"+ 紧跟的 bullet/缩进行 视为 1 条断语 block
# 支持 ★N 与 ★★★...★ 两种写法
_BLOCK_HEAD_RE = re.compile(r"★(?:[1-5１-５]|★{0,4})\s*[（(]\s*\d")
# 行内挖出"应期: YYYY 年" 或 "应期年: YYYY"
_YQ_YEAR_RE = re.compile(r"应期[年:：]?\s*[:：]?\s*(\d{4})")
_YQ_YEAR_INLINE_RE = re.compile(r"(\d{4})\s*年")
_FALSIFIABLE_RE = re.compile(r"(证伪|falsifiable)\s*[:：]\s*(.+?)(?:[\n。；]|$)")
_PASSED_LAYERS_RE = re.compile(
    r"(?:passed_layers|三层\s*gate|应期门)\s*[=:：]\s*(\d)",
    re.IGNORECASE,
)
_EVIDENCE_TOKEN_RE = re.compile(
    r"\b(?:M[123]-[A-Z]-\d+|MR-\d+|XF-\d+|G-[A-Z0-9]+-\d+|GP-[A-Z0-9\u4e00-\u9fff_]+(?:-[A-Z0-9\u4e00-\u9fff_]+)*|ZP-PROD-[A-Z0-9-]+|DTS-PROD-[A-Z0-9-]+)\b"
)


def _extract_school_tags(text: str) -> list[str]:
    """从 [....] 区块中按分隔符拆出 token，返回所有命中 VALID_SCHOOL_TAGS 的。"""
    tags: list[str] = []
    for m in SCHOOL_TAG_RE.finditer(text):
        body = m.group(1)
        for tok in re.split(r"[+/、，·\s派一致主辅胜负4-]+", body):
            tok = tok.strip()
            if tok in VALID_SCHOOL_TAGS:
                tags.append(tok)
    return tags


def _conclusion_from_md_line(line: str, lineno: int) -> _Conclusion:
    sp = parse_star_pct(line)
    star = sp[0] if sp else None
    pct = sp[1] if sp else None
    tags = _extract_school_tags(line)
    yq = None
    m1 = _YQ_YEAR_RE.search(line)
    if m1:
        yq = int(m1.group(1))
    fals_m = _FALSIFIABLE_RE.search(line)
    fals = fals_m.group(2).strip() if fals_m else None
    pl_m = _PASSED_LAYERS_RE.search(line)
    pl = int(pl_m.group(1)) if pl_m else None
    is_yq = (yq is not None) or any(
        kw in line for kw in ("应期", "婚期", "升迁年", "流年")
    )
    if is_yq and yq is None:
        m2 = _YQ_YEAR_INLINE_RE.search(line)
        if m2:
            yq = int(m2.group(1))
    evidence_count = len(_EVIDENCE_TOKEN_RE.findall(line))
    return _Conclusion(
        raw_text=line.strip(),
        statement=line.strip(),
        star=star,
        pct=pct,
        school_tags=tags,
        domain=None,
        yingqi_year=yq,
        falsifiable=fals,
        passed_layers=pl,
        evidence_count=evidence_count,
        location=f"line:{lineno}",
        is_yingqi=is_yq,
    )


def extract_conclusions_from_md(md: str) -> list[_Conclusion]:
    """把含 ★N (XX%) 的行 + 其紧跟的 bullet/缩进行 视为一条断语 block。

    block 结束条件：
      - 遇到下一个含 ★ 的行
      - 遇到下两个连续空行
      - 遇到 markdown header (^# / ^##)
    """
    lines = md.splitlines()
    out: list[_Conclusion] = []
    i = 0
    while i < len(lines):
        if _BLOCK_HEAD_RE.search(lines[i]):
            head_lineno = i + 1
            block_lines = [lines[i]]
            j = i + 1
            blank_streak = 0
            while j < len(lines):
                ln = lines[j]
                if _BLOCK_HEAD_RE.search(ln):
                    break
                if re.match(r"^\s*$", ln):
                    blank_streak += 1
                    if blank_streak >= 2:
                        break
                    j += 1
                    continue
                blank_streak = 0
                if re.match(r"^#{1,6}\s", ln):
                    break
                # 续行：bullet (- / * / 数字.) 或 缩进或 inline continuation
                if re.match(r"^\s*([\-*•]|\d+\.|\u2014|\u2192|→|>)", ln) or ln.startswith("    ") or ln.startswith("\t"):
                    block_lines.append(ln)
                    j += 1
                    continue
                # 非 bullet 缩进 + 非空 = 散文段，归入 block 但限制 1 行
                if len(block_lines) <= 4:
                    block_lines.append(ln)
                    j += 1
                    continue
                break
            block_text = "\n".join(block_lines)
            out.append(_conclusion_from_md_line(block_text, head_lineno))
            i = j
        else:
            i += 1
    return out


# ============================================================
# 六、主接口：lint()
# ============================================================

InputType = Union[dict[str, Any], str, "AnalysisOutputProto"]


class AnalysisOutputProto:  # pragma: no cover
    """duck-type protocol：任何含 final_conclusions / gate_results 的 dataclass 都可。"""
    final_conclusions: list[Any]
    gate_results: list[Any]


def _analysis_to_dict(obj: Any) -> dict[str, Any]:
    """支持 dataclass / dict / 自定义 dataclass。"""
    if isinstance(obj, dict):
        return obj
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    # 兜底：尝试 vars()
    if hasattr(obj, "__dict__"):
        return dict(vars(obj))
    raise TypeError(f"不支持的 lint 输入类型: {type(obj).__name__}")


def lint(
    analysis_output: InputType,
    rules_yaml: Optional[Path] = None,
) -> LintResult:
    """主入口：对 dict / dataclass / markdown 文本执行 11 项 + 禁忌清单检查。"""
    rules = load_rules(rules_yaml)
    res = LintResult(passed=True)

    conclusions: list[_Conclusion]
    full_text: str

    if isinstance(analysis_output, str):
        # markdown 模式
        full_text = analysis_output
        conclusions = extract_conclusions_from_md(full_text)
        # E11 总数检查
        if len(conclusions) < 5:
            res.add(
                Severity.WARNING, "W11",
                f"断语总数 {len(conclusions)} < 5（策略 B 最少建议）",
            )
        _lint_global_text(full_text, rules, res)
        # CFL-C015-002 · 跨维度输出耦合性 gate（仅 markdown 模式适用）
        _lint_cross_domain_coupling(full_text, res)
        # CFL-C014-003 v2 · W10 学制盲区律强制前置（报告级扫描）
        _lint_social_clock(full_text, res)
        # W12 · 天干相刑 / 规则外推误用扫描（C-2026-019 复盘）
        _lint_relation_source_misuse(full_text, res)
        # 唯一标准报告 · 命主画像禁止使用框线
        _lint_portrait_box_style(full_text, res)
    else:
        d = _analysis_to_dict(analysis_output)
        full_text = ""
        conclusions = []
        for i, c in enumerate(d.get("final_conclusions") or []):
            if isinstance(c, dict):
                conclusions.append(_conclusion_from_dict(c, i))
        for i, g in enumerate(d.get("gate_results") or []):
            if isinstance(g, dict):
                co = _conclusion_from_dict(g, len(conclusions))
                co.is_yingqi = True
                conclusions.append(co)
        if len(conclusions) < 5:
            res.add(
                Severity.WARNING, "W11",
                f"conclusion 总数 {len(conclusions)} < 5（策略 B 最少建议）",
            )
        _lint_dataclass_global(d, res)

    # 逐条 lint
    for c in conclusions:
        _lint_one_conclusion(c, rules, res)

    return res


# ============================================================
# 七、单条 lint：11 项检查 + 黑名单 + 禁忌词
# ============================================================

def _lint_one_conclusion(
    c: _Conclusion,
    rules: _RulesData,
    res: LintResult,
) -> None:
    loc = c.location

    # E1：★(XX%) 区间一致
    if c.star is None or c.pct is None:
        res.add(
            Severity.ERROR, "E1",
            f"未发现 ★N (XX%) 双轨置信度",
            location=loc,
            suggestion="补 ★N (XX%)，且区间一致（参考 06-confidence § 二）",
        )
    else:
        if not is_star_pct_consistent(c.star, c.pct):
            lo, hi = expected_pct_range(c.star)
            res.add(
                Severity.ERROR, "E1",
                f"★{c.star} 与 {c.pct}% 不匹配，应在 [{lo}, {hi}]",
                location=loc,
                suggestion=f"调整为 ★{expected_star_for_pct(c.pct)} ({c.pct}%) "
                           f"或 ★{c.star} ({lo}-{hi}%)",
            )

    # E2：派别标签
    if not c.school_tags:
        res.add(
            Severity.ERROR, "E2",
            "未含派别标签 [段/杨/任/高/共识/互补/独门/冲突仲裁]",
            location=loc,
            suggestion="开头加 [共识] 或 [杨主+段辅] 类标签",
        )

    # E3：evidence 链
    if c.evidence_count == 0:
        res.add(
            Severity.ERROR, "E3",
            "缺 evidence 链（未引用任何 MR/M1/M2/M3/G/XF 编号）",
            location=loc,
            suggestion="补充 e.g. M2-Y-091, M3-R-018 等规律编号",
        )

    # E4 / E5：应期 → yingqi_year + falsifiable
    if c.is_yingqi:
        if c.yingqi_year is None:
            res.add(
                Severity.ERROR, "E4",
                "应期断语缺 yingqi_year（未给具体年份）",
                location=loc,
                suggestion="补 '应期: YYYY 年' 或 yingqi_year 字段",
            )
        if not c.falsifiable:
            res.add(
                Severity.ERROR, "E5",
                "应期断语缺 falsifiable（无证伪条件）",
                location=loc,
                suggestion="补 '证伪: 若 YYYY 年未发生 XX 则失验'",
            )

    # E6：★★★★★ 必须 passed_layers == 3
    if c.is_yingqi and c.star == 5:
        if c.passed_layers is None:
            res.add(
                Severity.WARNING, "W6",
                "★★★★★ 应期未声明 passed_layers，无法验证三层 gate",
                location=loc,
            )
        elif c.passed_layers != 3:
            res.add(
                Severity.ERROR, "E6",
                f"★★★★★ 应期但 passed_layers={c.passed_layers}（必须=3）",
                location=loc,
                suggestion="降级为 ★★★★ 或补全三层证据",
            )

    # E10：黑名单规律拦截
    text_lower = (c.statement or c.raw_text or "").lower()
    for bid in rules.blacklist_ids:
        if bid.lower() in text_lower:
            res.add(
                Severity.ERROR, "E10",
                f"引用了黑名单规律 {bid}",
                location=loc,
                suggestion=(
                    f"该规律已废弃，参考 engine/mechanical_rules.py 的 "
                    f"BLACKLIST[\"{bid}\"].replacement_rules"
                ),
            )
    for alias_lower, bid in rules.blacklist_aliases.items():
        if not alias_lower:
            continue
        if alias_lower in text_lower:
            res.add(
                Severity.ERROR, "E10",
                f"使用了黑名单规律 {bid} 的别名「{alias_lower}」",
                location=loc,
                suggestion=(
                    f"该规律已废弃，参考 engine/mechanical_rules.py 的 "
                    f"BLACKLIST[\"{bid}\"].replacement_rules"
                ),
            )

    # E7：禁忌词（hard）
    raw = c.raw_text or ""
    for ph, reason in rules.forbidden_hard:
        if ph and ph in raw:
            res.add(
                Severity.ERROR, "E7",
                f"含禁忌词「{ph}」：{reason}",
                location=loc,
            )
    # W7：软禁忌词
    for ph, reason in rules.forbidden_soft:
        if ph and ph in raw:
            res.add(
                Severity.WARNING, "W7",
                f"含被禁措辞「{ph}」: {reason}",
                location=loc,
                suggestion="改用具体年份 / 概率化（★/%）",
            )


# ============================================================
# 八、全局检查（dataclass 模式）
# ============================================================

def _lint_dataclass_global(
    d: dict[str, Any], res: LintResult
) -> None:
    """检查 upstream_hash 一致 + energy/picture 一致性等"""
    energy = d.get("energy") or {}
    picture = d.get("picture") or {}
    gates = d.get("gate_results") or []

    # E9：upstream_hash 链
    if isinstance(picture, dict):
        eh = picture.get("upstream_hash")
        # 我们不实际重算 hash（代价太大），仅检查存在
        if eh is None:
            res.add(
                Severity.ERROR, "E9",
                "PictureFindings 缺 upstream_hash（无法证明与 D1 同版本）",
            )

    # E8：energy_consistent / picture_consistent
    if isinstance(picture, dict) and picture.get("energy_consistent") is False:
        res.add(
            Severity.WARNING, "W8",
            f"PictureFindings.energy_consistent=False, "
            f"violations={picture.get('energy_violations')}",
        )
    for gi, g in enumerate(gates):
        if not isinstance(g, dict):
            continue
        if g.get("energy_consistent") is False:
            res.add(
                Severity.WARNING, "W8",
                f"GateResult[{gi}].energy_consistent=False",
            )
        if g.get("picture_consistent") is False:
            res.add(
                Severity.WARNING, "W8",
                f"GateResult[{gi}].picture_consistent=False",
            )


def _lint_global_text(
    md: str, rules: _RulesData, res: LintResult,
) -> None:
    """对 markdown 报告全文做全局禁忌词扫描（不挂在某条 conclusion）"""
    for ph, reason in rules.forbidden_hard:
        if ph and ph in md:
            res.add(Severity.ERROR, "E7", f"全文含禁忌词「{ph}」: {reason}")
    # 软词扫描已在每条 conclusion 中做；全局只补"未在 ★ 行中出现的散文段"
    # 简单计数 → 若在非 ★ 行也出现，仍报 W7
    for ph, reason in rules.forbidden_soft:
        if ph and ph in md:
            count = md.count(ph)
            res.add(
                Severity.WARNING, "W7",
                f"全文出现被禁措辞「{ph}」共 {count} 次：{reason}",
            )


# ============================================================
# 八·四、W12 · 天干相刑 / 规则外推误用扫描（C-2026-019 复盘）
# ============================================================
# 来源：C-2026-019 曾把地支寅巳作用误写成“甲木刑辛金”，
# 并把 CON-HUNYIN-003（旺神冲衰神拔根，本义为“冲”）外推成“刑伤同理”。
# 本检查只扫 markdown 报告 / 分析文档；若文本是在纠错说明中引用旧错误，
# 可通过“不能/不可/不成立/校正/不再”等否定标记免报。

_RELATION_LINT_SKIP_MARKERS: tuple[str, ...] = (
    "不能", "不可", "不成立", "不再", "校正", "错误", "原写法",
    "非天干相刑", "非“", "非\"", "非「", "不是", "不写成", "不应写成",
    "已校正", "防复发", "误用", "不作为", "不宜",
)

_GAN_WITH_ELEMENT = r"[甲乙丙丁戊己庚辛壬癸][木火土金水]?"
_ROLE_OR_GAN = (
    rf"(?:{_GAN_WITH_ELEMENT}|正官|偏官|七杀|官星|正财|偏财|财星|"
    rf"正印|偏印|印星|食神|伤官|比肩|劫财|日主|元男)"
)

_DIRECT_TG_XING_PATTERNS: tuple[re.Pattern[str], ...] = (
    # 甲木刑辛金 / 甲木刑伤辛金：必须是天干/五行直接落在“刑”两侧。
    re.compile(rf"{_GAN_WITH_ELEMENT}[^\n。；，、]{{0,8}}(?:刑|刑伤|被刑|受刑)[^\n。；，、]{{0,8}}{_GAN_WITH_ELEMENT}"),
    # 官星被甲木刑伤 / 正官被甲木刑：十神被某天干“刑伤”。
    re.compile(rf"(?:正官|偏官|七杀|官星|正财|偏财|财星|正印|偏印|印星|食神|伤官|比肩|劫财|日主|元男)[^\n。；，、]{{0,12}}被{_GAN_WITH_ELEMENT}[^\n。；，、]{{0,6}}(?:刑|刑伤)"),
)

_CON_HUNYIN_MISUSE_RE = re.compile(
    r"CON-HUNYIN-003[^\n]*(?:刑|穿|刑伤|刑动|刑制|相刑|相穿)|"
    r"(?:刑|穿|刑伤|刑动|刑制|相刑|相穿)[^\n]*CON-HUNYIN-003"
)


def _should_skip_relation_lint(line: str) -> bool:
    """纠错/否定语境中可引用旧错误，不触发 W12。"""
    return any(marker in line for marker in _RELATION_LINT_SKIP_MARKERS)


def _lint_relation_source_misuse(md: str, res: LintResult) -> None:
    """W12 · 阻断“天干相刑”和 CON-HUNYIN-003 外推到刑/穿。"""
    seen: set[tuple[str, str]] = set()

    for lineno, line in enumerate(md.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or _should_skip_relation_lint(stripped):
            continue

        for pattern in _DIRECT_TG_XING_PATTERNS:
            if pattern.search(stripped):
                key = ("direct", stripped)
                if key in seen:
                    continue
                seen.add(key)
                res.add(
                    Severity.ERROR,
                    "E12",
                    "疑似天干/十神直接相刑表述：刑/穿应先落到地支关系，不能写成“甲木刑辛金”一类天干相刑。",
                    location=f"line {lineno}: {stripped[:100]}",
                    suggestion="改为“某地支与某地支构成穿/刑动，牵动某宫/某柱象”；若仅引用旧错误，请在同句加入“原写法错误/不能/不可”等否定标记。",
                )
                break

        if _CON_HUNYIN_MISUSE_RE.search(stripped):
            key = ("con-hunyin", stripped)
            if key in seen:
                continue
            seen.add(key)
            res.add(
                Severity.ERROR,
                "E12",
                "CON-HUNYIN-003 仅支持“旺神冲衰神”类冲法判断，疑似被外推到刑/穿/刑伤。",
                location=f"line {lineno}: {stripped[:100]}",
                suggestion="删除 CON-HUNYIN-003 引用，改引地支穿/刑动来源；或明确写“CON-HUNYIN-003 不适用于本条”。",
            )


# ----------------------------------------------------------------
# CFL-C015-002 · 跨维度输出耦合性 gate
# ----------------------------------------------------------------
# 详见：engine/level-scales.md § 十一
# 触发条件：报告同时出现高置信度的 "体制内/公门/国企" 关键词
#         + 高置信度的 "中富/大富/巨富/小富" 市场财富分级
#         且无明确耦合标注（"权力层级" / "公务员薪酬" / "非体制路径下的对照值"）
# 严重等级：WARNING (W9)
# 来源：C-2026-015 反馈 / CFL-C015-002 仲裁

# 行业路径关键词（高置信暗示走体制路径）
_INSTITUTIONAL_KEYWORDS: tuple[str, ...] = INSTITUTIONAL_KEYWORDS

# 市场财富分级关键词（暗示用 5 级 15 档市场财富分级）
_MARKET_WEALTH_KEYWORDS: tuple[str, ...] = (
    "中富级",
    "中富·",
    "大富级",
    "大富·",
    "巨富级",
    "巨富·",
    "小富级",
    "小富·",
    "贫困级",
    "贫困·",
)

# 耦合标注关键词（出现任一即视为已做耦合标注，免警告）
_COUPLING_ANNOTATIONS: tuple[str, ...] = (
    "权力层级",
    "公务员薪酬",
    "非体制路径下的对照值",
    "体制路径例外条款",
    "EXC-D-LIFA-CAP-001",
    "CFL-C015-002",
    "行业路径耦合提示",
)

# 高置信信号阈值：报告中包含 ≥N% 或 ★★★★+ 的行
_HIGH_CONFIDENCE_RE = re.compile(r"★{4,5}|\((?:7[0-9]|8[0-9]|9[0-9]|100)%\)")


def _has_high_confidence_marker(text: str, keyword: str) -> bool:
    """检查 keyword 出现的行附近（同一行或上下 1 行）是否带高置信度标记。"""
    return _has_high_confidence_marker_in_lines(text.splitlines(), keyword)


def _has_high_confidence_marker_in_lines(lines: list[str], keyword: str) -> bool:
    """复用已分割行，避免跨关键词重复 split 与全量扫描。"""
    for i, line in enumerate(lines):
        if keyword not in line:
            continue
        # 检查 keyword 所在行 + 前后各 1 行
        window = "\n".join(lines[max(0, i - 1): min(len(lines), i + 2)])
        if _HIGH_CONFIDENCE_RE.search(window):
            return True
    return False


def _lint_portrait_box_style(md: str, res: LintResult) -> None:
    """v1.4 · 命主画像段禁止使用 ╔╗ 等框线字符。"""
    if "命主画像" not in md and "命 主 画 像" not in md and "portrait_block" not in md:
        return
    # W13 是 v1.4 模板样式护栏；历史 v1.0/v1.2/v1.3 存量报告可保留框线画像，
    # 避免把历史样式残留误报为理论/知识调用错误。
    if "v1.4" not in md and "portrait_block" not in md:
        return
    box_chars = {"╔", "╗", "╚", "╝", "╠", "╣", "║", "═"}
    if any(ch in md for ch in box_chars):
        res.add(
            Severity.WARNING,
            "W13",
            "命主画像段检测到框线字符（╔╗║═ 等）。v1.4 模板要求画像使用表格展示，禁止框线。",
        )



def _lint_cross_domain_coupling(
    md: str, res: LintResult,
) -> None:
    """CFL-C015-002 · 检查行业方向 / 财富层级 跨维度输出耦合一致性。

    若报告同时出现高置信"体制内"信号 + 高置信"市场财富分级"，
    且未包含任何耦合标注 → 触发 W9 cross-domain incoherence warning。

    详见 engine/level-scales.md § 十一。
    """
    institutional_candidates = [kw for kw in _INSTITUTIONAL_KEYWORDS if kw in md]
    if not institutional_candidates:
        return  # 无体制内信号 → 走默认市场财富分级，无需耦合 gate

    lines = md.splitlines()

    # 1. 检测高置信"体制内"信号
    institutional_hits = [
        kw for kw in institutional_candidates
        if _has_high_confidence_marker_in_lines(lines, kw)
    ]

    if not institutional_hits:
        return  # 无高置信体制内信号 → 无需耦合 gate

    market_wealth_candidates = [kw for kw in _MARKET_WEALTH_KEYWORDS if kw in md]
    if not market_wealth_candidates:
        return  # 无市场财富分级输出 → 已经走权力层级，符合规范

    # 2. 检测高置信"市场财富分级"输出
    market_wealth_hits = [
        kw for kw in market_wealth_candidates
        if _has_high_confidence_marker_in_lines(lines, kw)
    ]

    if not market_wealth_hits:
        return  # 无高置信市场财富分级输出 → 已经走权力层级，符合规范

    # 3. 检测耦合标注
    coupling_present = any(ann in md for ann in _COUPLING_ANNOTATIONS)

    if coupling_present:
        return  # 已做耦合标注 → 符合规范

    # 4. 触发 W9 警告
    res.add(
        Severity.WARNING, "W9",
        f"跨维度输出耦合性问题（CFL-C015-002）：报告同时输出高置信度的"
        f"体制内信号 {institutional_hits[:3]} 和市场财富分级 {market_wealth_hits[:3]}，"
        f"但未包含耦合标注。建议：1) 改用权力层级（科/处/厅/部/国）作为主输出框架；"
        f"或 2) 在财富层级标题前加注释 '以下市场财富分级仅作为非体制路径下的对照值'。"
        f"详见 engine/level-scales.md § 十一。",
    )


# ============================================================
# 八·五、CFL-C014-003 v2 · W10 学制盲区律强制前置（报告级 lint）
# ============================================================
#
# 来源：C-2026-014 v1.0/v2.0 连续犯学制盲区错误（"2026=高考"实际2024 / "2029=毕业"实际2028）。
# v1.4 已在 engine/yingqi/gate.py 落 social_clock_check（gate pipeline 路径），
# 但报告 markdown 是命理师手写，仍可能错锚 → 在 output_linter 增加 W10 报告级扫描。
#
# 检查逻辑：
#   1. 从报告头部提取出生年（"出生：YYYY-MM-DD" 或 "生年：YYYY"）
#   2. 扫描每行：若同时含 4 位年份 + 学制事件关键词 → 计算年龄
#   3. 偏差 > 容差（±1 年）→ 触发 W10 警告
#   4. 跳过元数据行（含 v1.0/v2.0/错锚/修正/已应验等关键词）

# 学制规则（与 engine/yingqi/gate._SOCIAL_CLOCK_RULES 同步）；事实源在 engine.domain.social_clock。
_LINT_SOCIAL_CLOCK_RULES: list[tuple[tuple[str, ...], tuple[int, int], str]] = list(
    SOCIAL_CLOCK_RULES
)

_LINT_SOCIAL_CLOCK_TOLERANCE: int = SOCIAL_CLOCK_TOLERANCE

# 出生年提取正则：捕获 "出生：YYYY"、"生年：YYYY"、"**出生**：YYYY-MM-DD" 等格式
# 兼容 markdown 加粗（**出生**） / 中英文冒号 / 日期 4 位前任意非数字字符
_BIRTH_YEAR_RE = re.compile(
    r"(?:出生|生年)[^0-9\n]{0,8}(\d{4})"
)

# 元数据/历史标记 → 跳过该行
_LINT_SC_SKIP_MARKERS: tuple[str, ...] = (
    "v1.0", "v2.0", "v1版", "v2版", "v2.1",
    "错锚", "修正", "已应验", "已校准",
    "✅", "原 v",
    "v2 校准", "v2.0 错", "v2.1 重锚",
    "rejected_in_cases", "校准前", "校准历史",
    "→",  # 修正表格行通常含箭头
    "前值", "旧值",
)

# 年份正则（限定 1900-2099 范围，避免误匹配）
_YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")


def _extract_birth_year_from_md(md: str) -> Optional[int]:
    """从报告 markdown 头部提取命主出生年。"""
    m = _BIRTH_YEAR_RE.search(md)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


def _should_skip_sc_lint(line: str) -> bool:
    """该行是否应跳过学制盲区扫描（元数据/历史/修正记录）。"""
    return any(marker in line for marker in _LINT_SC_SKIP_MARKERS)


def _lint_social_clock(md: str, res: LintResult) -> None:
    """W10 · 学制盲区律强制前置（报告级扫描，CFL-C014-003 v2）。

    扫描策略：
      - 仅处理含明确"年份 + 学制事件关键词"的行
      - 跳过含修正/已应验/历史 v 版本等元数据行
      - 偏差 > 容差 → 触发 W10
    """
    birth_year = _extract_birth_year_from_md(md)
    if birth_year is None:
        return  # 无出生年信息，跳过该 lint

    seen_pairs: set[tuple[int, str, int]] = set()  # 去重

    for line in md.splitlines():
        if not line.strip():
            continue
        if _should_skip_sc_lint(line):
            continue

        # 同行内匹配年份
        years = [int(m.group(1)) for m in _YEAR_RE.finditer(line)]
        if not years:
            continue

        # 同行内匹配关键词（按规则列表顺序，长关键词优先）
        for keywords, (lo, hi), label in _LINT_SOCIAL_CLOCK_RULES:
            matched_kw = next((k for k in keywords if k in line), None)
            if matched_kw is None:
                continue

            # 对每个年份逐个检查
            for year in years:
                age = year - birth_year
                if age <= 0:
                    continue
                # 严格窗口 + 容差
                if lo - _LINT_SOCIAL_CLOCK_TOLERANCE <= age <= hi + _LINT_SOCIAL_CLOCK_TOLERANCE:
                    continue
                # 偏差 > 容差 → 触发
                pair = (year, label, age)
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                res.add(
                    Severity.WARNING, "W10",
                    f"学制盲区告警 (CFL-C014-003 v2)：'{year}' + '{matched_kw}' "
                    f"→ 命主 {birth_year} 出生，{year} 应为 {age} 岁，"
                    f"但 {label} 期望窗口 [{lo},{hi}]（容差 ±{_LINT_SOCIAL_CLOCK_TOLERANCE}）",
                    location=line.strip()[:100],
                    suggestion=(
                        f"请核对：若实际是 {label}，年份应在 "
                        f"[{birth_year + lo}, {birth_year + hi}] 之间。"
                        f"若是历史校准记录或修正条目，加 'v1.0'/'已应验'/'修正' 等标记可跳过本检查。"
                    ),
                )
            break  # 一行内最多触发一种事件类型，避免 noise


# ============================================================
# 九、smoke test
# ============================================================

_SMOKE_GOOD = """\
## 报告示例

[共识 · 4 派一致] 命主从公门入仕 ★4 (82%)
- 来源：M1-D-001 / M2-Y-091 / G-XX-005 / M3-R-018
- 证伪：若 65 岁前未在公门体制内 → 失验
- 应期: 2020 年（passed_layers=3）

[共识] 财运 L2-L3 顶 ★4 (80%)
- 来源：M1-D-142, MR-002
- 证伪：若 60 岁仍年薪不到 30 万 → 失验

[杨派] 妻家有靠山 ★4 (78%)
- 来源：M2-Y-035
- 证伪：若配偶家庭普通 → 失验

[共识] 2020 母逝 + 提副科 ★5 (90%)
- 来源：M3-R-018, M1-D-200
- 应期: 2020 年（passed_layers=3）
- 证伪：若 2020 母健在且未提拔 → 失验

[互补] 长寿型 ★3 (62%)
- 来源：M1-D-308, MR-002
- 证伪：未达 80 岁 → 失验
"""

_SMOKE_BAD_RANGE = "[共识] 婚姻坎坷 ★5 (50%) 来源：M2-Y-073"
_SMOKE_BAD_BLACKLIST = "[杨派] 五凶煞=婚凶 婚姻坎坷 ★4 (75%) 来源：M2-Y-073"
_SMOKE_BAD_FORBIDDEN = "[共识] 未来某年可能必然有大事 ★3 (60%) 来源：M3-R-001"

# CFL-C015-002 smoke test：体制内信号 + 市场财富分级 同时高置信 + 无耦合标注 → W9
_SMOKE_BAD_CROSS_DOMAIN = """\
[共识 · 4 派一致] 命主走公门路径 ★5 (90%)
- 来源：M1-D-005, M2-Y-091, G-XX-005, M3-R-018
- 证伪：若 65 岁前未在体制内 → 失验

[互补] 财运一生天花板 中富级·上等（500-1000 万资产）★4 (85%)
- 来源：M1-D-173, M2-Y-035
- 证伪：若 60 岁仍年薪不到 30 万 → 失验
"""

# 同样信号但已加耦合标注 → 不应触发 W9
_SMOKE_GOOD_CROSS_DOMAIN = """\
[共识 · 4 派一致] 命主走公门路径 ★5 (90%)
- 来源：M1-D-005, M2-Y-091, G-XX-005, M3-R-018
- 证伪：若 65 岁前未在体制内 → 失验

[互补] 财运一生天花板：权力层级 正厅级 ★4 (85%)
（CFL-C015-002 输出耦合标注：以下市场财富分级仅作为非体制路径下的对照值）
中富级·上等（500-1000 万资产对照值）— 来源：M1-D-173, M2-Y-035
- 证伪：若 60 岁仍未达正厅 → 失验
"""

_SMOKE_BAD_RELATION_SOURCE = """\
[共识] 甲木刑辛金，官星被刑伤，纯官场路线不利 ★4 (84%)
- 来源：CON-HUNYIN-003（旺神冲衰神拔根·此处为刑伤同理）
"""

_SMOKE_GOOD_RELATION_SOURCE = """\
[共识·已校正] 寅巳为地支层面的穿/刑动，牵动年柱官象；不能写成“甲木刑辛金”。 ★3 (69%)
- 来源校正：CON-HUNYIN-003 只论冲，不再作为本条依据。
"""


def _smoke() -> None:
    print("---- 1. lint good markdown ----")
    r = lint(_SMOKE_GOOD)
    print(r.format())
    print()
    print("---- 2. lint bad range ----")
    r = lint(_SMOKE_BAD_RANGE)
    print(r.format())
    print()
    print("---- 3. lint blacklist ----")
    r = lint(_SMOKE_BAD_BLACKLIST)
    print(r.format())
    print()
    print("---- 4. lint forbidden phrase ----")
    r = lint(_SMOKE_BAD_FORBIDDEN)
    print(r.format())

    print()
    print("---- 5. lint cross-domain incoherence (CFL-C015-002, expect W9) ----")
    r = lint(_SMOKE_BAD_CROSS_DOMAIN)
    print(r.format())
    print()
    print("---- 6. lint cross-domain coupled OK (CFL-C015-002, no W9) ----")
    r = lint(_SMOKE_GOOD_CROSS_DOMAIN)
    print(r.format())

    print()
    print("---- 7. lint relation-source misuse (C-2026-019, expect E12) ----")
    r = lint(_SMOKE_BAD_RELATION_SOURCE)
    print(r.format())
    assert any(i.code == "E12" for i in r.errors)

    print()
    print("---- 8. lint relation-source correction note OK (C-2026-019, no E12) ----")
    r = lint(_SMOKE_GOOD_RELATION_SOURCE)
    print(r.format())
    assert not any(i.code == "E12" for i in r.errors)


if __name__ == "__main__":  # pragma: no cover
    if len(sys.argv) >= 2:
        text = Path(sys.argv[1]).read_text(encoding="utf-8")
        r = lint(text)
        print(r.format())
        sys.exit(0 if r.passed else 1)
    else:
        _smoke()
