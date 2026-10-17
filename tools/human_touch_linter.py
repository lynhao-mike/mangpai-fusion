"""tools/human_touch_linter.py · WP-8 防骑墙门禁（v9 契约）

检查人话报告是否违反 docs/analysis_human_touch.md 的写作纪律。
零第三方依赖：仅使用标准库（re / sys / pathlib / argparse）。

四项检查
--------
检查 1  全局禁用词          永续层  禁「或许/可能/也许/不宜妄断/难以定论/仅供娱乐」
检查 2  正文反拆台/反骑墙    永续层  禁「不能据此直接断/不足以断/机会与调整成本并存/…」
检查 3  结构缺陷             永续层  3a 定调节 3b 三级声明 3c 第五节站队 3d 建议/流年行实断
检查 4  依据索引非空         契约层  附节须含地址/边号与规则 ID；**前置契约自检**

抗引擎变更设计
--------------
检查 1/2/3 只判断「文字怎么写」，与 engine/ 输出格式无关，属**永续层**——
engine/ 无论如何变更都照用。

检查 4 需要认识引擎的地址/边号格式，属**契约层**。契约失效时本模块
**不静默放过**：_contract_health() 失配即返回一条 [检查4] 契约失效 ERROR
并中止检查 4 的其余判定。宁可让所有报告同时报同一个错（响亮失败），
也不准假阴性放过。任何人不得为了「让某份报告通过」而删除
_contract_health() 或清空样本常量；正确做法是按
docs/analysis_human_touch.md §3.5.2 同步正则。

已知取舍（勿当 bug 修掉）
------------------------
1. 「可能」按子串匹配会一并拦截「不可能」——规范选择（用「不会/绝不」替代）。
2. 检查 1 豁免三处：《先把话说死》节、《附》依据索引节、文末引用块。
   《附》豁免的实测理由：theory/_light_index.json 共 3471 条记录，标题含
   禁用词的 2 条为 M2-Y-113「满盘泄克无生助=难以成就」与
   ZP-SAMPLE-010「四吉神失宜也可能破格」；不豁免则引用即误报。
   该节仍受检查 4 严格约束，防止用豁免区掩盖引用缺失。
3. 检查 3d 只覆盖「含 建议： 的行」与「流年表首列为年份的行」两类，
   不覆盖散文段落里的建议句——后者由 Step 6e 人工纪律约束。
4. 「不宜」不得加入检查 2 禁用表：「不宜加杠杆」等正常否定是有立场的
   结论，正是本改造要保护的对象；「不宜妄断」已由检查 1 拦截，
   虚词化的「宜重视/注意防范」由检查 3d 拦截。

CLI
---
    python -m tools.human_touch_linter <file.md> [more.md ...]
    全部通过 exit 0；任一文件有 ERROR → 逐条打印到 stderr 并 exit 1；
    无参数打印用法并 exit 2。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


# ============================================================
# 契约层常量（引擎变更时必须同步，见 docs/analysis_human_touch.md §3.5.2）
# ============================================================

ADDRESS_SCHEMA_VERSION = "addr/v1"      # 与 engine.facts 地址体系对应；引擎改格式时必须 bump

SAMPLE_ADDRESSES = ("Y.s", "M.b", "D.s", "H.b", "DY5.b", "LN2026.s")
SAMPLE_EDGE_IDS = ("e001", "e013")

ADDR_RE = re.compile(r"\b[YMDH]\.[sb]\b")
DY_RE = re.compile(r"\bDY\d+\.[sb]\b")
LN_RE = re.compile(r"\bLN\d{4}\.[sb]\b")
EDGE_RE = re.compile(r"\be\d{3}\b")
RULE_RE = re.compile(r"\b(?=[A-Z0-9-]*[A-Z])[A-Z0-9]{1,6}-[A-Z0-9]{1,6}-\d{2,}\b")
RULE_CN_RE = re.compile(r"\b[A-Z]{1,4}-[甲乙丙丁戊己庚辛壬癸]-[子丑寅卯辰巳午未申酉戌]\b")
FILELINE_RE = re.compile(r"[\w\-.]+\.md:\d+")


# ============================================================
# 永续层常量（与引擎无关，永久有效）
# ============================================================

# 检查 1：概率词堆砌
BANNED_WORDS_CHECK1 = ("或许", "可能", "也许", "不宜妄断", "难以定论", "仅供娱乐")

# 检查 2：正文反拆台 / 反骑墙
BANNED_PHRASES_CHECK2 = (
    "不能据此直接断",
    "不能据此断",
    "不能直接裁成",
    "不能只凭",
    "不等于必然",
    "不代表必然",
    "不决定吉凶",
    "不足以直接定为",
    "不足以断",
    "尚不能确认",
    "尚不认定",
    "机会与调整成本并存",
    "机会与挑战并存",
    "吉凶参半",
    "宜核验是否",
)

# 检查 3b：三级声明标记词
MARKER_BAIBAN = "板上钉钉"
MARKER_DAGAILV = "大概率"
MARKER_WUBIAN = "我不编"

# 检查 3c：裁决标记词
VERDICT_MARKERS = ("我采信", "我的最终裁决", "我的裁决", "站队")

# 检查 3d：禁用虚词（无动作）
VAGUE_WORDS_CHECK3D = ("宜重视", "注意防范", "谨慎行事", "不宜盲目", "注意风险", "宜谨慎")

# 检查 3d：动作动词白名单（30 个）
ACTION_VERBS = (
    # 核心 15
    "签约", "立字据", "锁死", "止损", "盘点", "体检", "竞聘", "考证",
    "深耕", "暂缓", "分批", "核查", "留存", "剥离", "主攻",
    # 扩充 15
    "挂靠", "转岗", "回款", "隔离", "复查", "领证", "兑现", "落袋",
    "立规矩", "砍掉", "嫁接", "报备", "续约", "退出", "申遗",
)


# ============================================================
# 行级工具
# ============================================================

_RE_H2 = re.compile(r"^##\s")
_RE_DINGDIAO = re.compile(r"^##\s*〇、一句话定调")
_RE_SHUXIANSI = re.compile(r"^##\s*先把话说死")
_RE_SEC1 = re.compile(r"^##\s*一、")
_RE_SEC5 = re.compile(r"^##\s*五、")
_RE_SEC6 = re.compile(r"^##\s*六、")
_RE_FULU = re.compile(r"^##\s*附")

_RE_BOLD = re.compile(r"\*\*[^*]*\*\*")
_RE_INLINE_MARKS = re.compile(r"[*`~]")


def _strip_bold(line: str) -> str:
    """剔除 **...** 粗体片段。"""
    return _RE_BOLD.sub("", line)


def _strip_inline_marks(text: str) -> str:
    """剔除 * ` ~ 等行内修饰符。"""
    return _RE_INLINE_MARKS.sub("", text)


def _is_heading(line: str) -> bool:
    return line.lstrip().startswith("#")


def _is_table_sep(line: str) -> bool:
    s = line.strip()
    return "|---" in s or s.replace("|", "").replace("-", "").strip() == ""


def _is_table_header(line: str) -> bool:
    s = line.strip()
    if not s.startswith("|"):
        return False
    first = s.split("|")[1] if "|" in s[1:] else ""
    return ("流年" in first) or ("年份" in first)


def _first_table_cell(line: str) -> str:
    """取表格行第一个单元格（整行以 | 开头）。"""
    parts = line.strip().split("|")
    if len(parts) >= 3:
        return parts[1]
    return ""


# ============================================================
# 节区切分
# ============================================================

def _section_bounds(lines: list[str], start_re: re.Pattern, end_res: tuple[re.Pattern, ...]) -> tuple[int, int]:
    """返回 [start_idx, end_idx) 半开区间；start_idx 为标题行，end_idx 为下一标题行（不含）。"""
    n = len(lines)
    start = None
    for i, ln in enumerate(lines):
        if start_re.search(ln):
            start = i
            break
    if start is None:
        return (-1, -1)
    end = n
    for j in range(start + 1, n):
        if any(r.search(lines[j]) for r in end_res):
            end = j
            break
    return (start, end)


def _trailing_quote_block(lines: list[str]) -> set[int]:
    """文末最后一个连续 > 行组的行号集合。"""
    idxs: set[int] = set()
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith(">"):
            idxs.add(i)
        else:
            if lines[i].strip() == "":
                continue
            break
    return idxs


# ============================================================
# 契约自检
# ============================================================

def _contract_health() -> list[str]:
    """验证正则仍能匹配样本。返回问题列表，空 = 健康。"""
    problems: list[str] = []
    for a in SAMPLE_ADDRESSES:
        if not (ADDR_RE.search(a) or DY_RE.search(a) or LN_RE.search(a)):
            problems.append(f"地址样本 {a!r} 失配")
    for e in SAMPLE_EDGE_IDS:
        if not EDGE_RE.search(e):
            problems.append(f"边号样本 {e!r} 失配")
    return problems


# ============================================================
# 主入口
# ============================================================

def lint_human_touch(text: str) -> list[str]:
    """检查人话报告，返回 ERROR 字符串列表；空列表 = 通过。

    对任意输入不得抛异常（内部 try/except 兜底）。
    """
    try:
        return _lint(text)
    except Exception as exc:  # pragma: no cover - 兜底
        return [f"[检查0] 内部异常: {type(exc).__name__}: {exc}"]


def _lint(text: str) -> list[str]:
    lines = text.splitlines()
    errors: list[str] = []

    # ---- 检查 1：全局禁用词（永续层）-----------------------------
    _check1_banned_words(lines, errors)

    # ---- 检查 2：正文反拆台 / 反骑墙（永续层）--------------------
    _check2_hedging(lines, errors)

    # ---- 检查 3：结构缺陷（永续层）-------------------------------
    _check3_structure(lines, errors)

    # ---- 检查 4：依据索引非空（契约层，含契约自检）---------------
    _check4_evidence(lines, errors)

    return errors


# ------------------------------------------------------------
# 检查 1
# ------------------------------------------------------------

def _check1_banned_words(lines: list[str], errors: list[str]) -> None:
    exempt: set[int] = set()

    # 豁免 1：《先把话说死》节
    s, e = _section_bounds(lines, _RE_SHUXIANSI, (_RE_H2,))
    if s >= 0:
        exempt.update(range(s, e))

    # 豁免 2：《附》依据索引节（客观出处索引，仍受检查 4 约束）
    s, e = _section_bounds(lines, _RE_FULU, ())
    if s >= 0:
        exempt.update(range(s, e))

    # 豁免 3：文末边界声明引用块
    exempt.update(_trailing_quote_block(lines))

    for i, line in enumerate(lines):
        if i in exempt:
            continue
        for w in BANNED_WORDS_CHECK1:
            if w in line:
                errors.append(f"[检查1] L{i + 1}: 出现禁用词「{w}」")


# ------------------------------------------------------------
# 检查 2
# ------------------------------------------------------------

def _check2_hedging(lines: list[str], errors: list[str]) -> None:
    # 作用域：`## 一、` 之后 至 `## 六、` 之前；无 `## 六、` 则延至 `## 附` 或文末
    s, _ = _section_bounds(lines, _RE_SEC1, ())
    if s < 0:
        return  # 无正文区，交给检查 3a/3c 报结构缺失

    end = len(lines)
    for j in range(s + 1, len(lines)):
        if _RE_SEC6.search(lines[j]):
            end = j
            break
        if _RE_FULU.search(lines[j]):
            end = j
            break

    for i in range(s + 1, end):
        line = lines[i]
        for p in BANNED_PHRASES_CHECK2:
            if p in line:
                errors.append(f"[检查2] L{i + 1}: 正文出现自我拆台/骑墙话术「{p}」")


# ------------------------------------------------------------
# 检查 3
# ------------------------------------------------------------

def _check3_structure(lines: list[str], errors: list[str]) -> None:
    full_text = "\n".join(lines)

    # 3a：定调节存在且非空
    s, e = _section_bounds(lines, _RE_DINGDIAO, (_RE_H2,))
    if s < 0:
        errors.append("[检查3a] 缺少「## 〇、一句话定调」节")
    else:
        body = [ln for ln in lines[s + 1:e] if ln.strip()]
        if not body:
            errors.append(f"[检查3a] L{s + 1}: 「一句话定调」节下无正文")

    # 3b：三级声明标记词
    for marker, label in (
        (MARKER_BAIBAN, "板上钉钉"),
        (MARKER_DAGAILV, "大概率"),
        (MARKER_WUBIAN, "我不编"),
    ):
        if marker not in full_text:
            errors.append(f"[检查3b] 缺少三级声明标记词「{label}」")

    # 3c：第五节必须站队（无条件）
    s, e = _section_bounds(lines, _RE_SEC5, (_RE_H2,))
    if s < 0:
        errors.append("[检查3c] 缺少「## 五、」裁决节")
    else:
        body_text = "\n".join(lines[s + 1:e])
        if not any(m in body_text for m in VERDICT_MARKERS):
            errors.append(
                f"[检查3c] L{s + 1}: 第五节未给出明确裁决（需含「我采信 / 我的最终裁决 / 我的裁决 / 站队」之一）"
            )

    # 3d：建议 / 流年行实断
    _check3d_advice(lines, errors)


def _check3d_advice(lines: list[str], errors: list[str]) -> None:
    for i, line in enumerate(lines):
        if _is_heading(line) or _is_table_sep(line) or _is_table_header(line):
            continue

        is_target = False

        # (i) 含「建议：/建议:」的行（先剔除粗体再判定）
        stripped = _strip_bold(line)
        if re.search(r"建议[:：]", stripped):
            is_target = True

        # (ii) 流年表数据行：整行以 | 开头，且首格剥离修饰符后为 4 位年份
        if not is_target and line.lstrip().startswith("|"):
            first = _strip_inline_marks(_first_table_cell(line)).strip()
            if re.match(r"^20\d\d", first):
                is_target = True

        if not is_target:
            continue

        for w in VAGUE_WORDS_CHECK3D:
            if w in line:
                errors.append(f"[检查3d] L{i + 1}: 建议行使用无动作虚词「{w}」")

        if not any(v in line for v in ACTION_VERBS):
            errors.append(
                f"[检查3d] L{i + 1}: 建议行缺少具体动作动词（须含 ACTION_VERBS 之一，如 签约/锁死/止损/盘点/核查/考证/暂缓/分批/剥离/主攻）"
            )


# ------------------------------------------------------------
# 检查 4（契约层）
# ------------------------------------------------------------

def _check4_evidence(lines: list[str], errors: list[str]) -> None:
    # 契约自检：失配则中止后续判定
    problems = _contract_health()
    if problems:
        detail = "；".join(problems)
        errors.append(
            f"[检查4] Linter 契约失效（ADDRESS_SCHEMA_VERSION={ADDRESS_SCHEMA_VERSION}）：{detail}。"
            "引擎地址/边号 schema 可能已变更，请按 docs/analysis_human_touch.md §3.5.2 "
            "同步更新本文件的样本常量与正则后再运行。"
        )
        return

    s, e = _section_bounds(lines, _RE_FULU, ())
    if s < 0:
        errors.append("[检查4] 缺少「## 附：关键依据索引」节")
        return

    body = "\n".join(lines[s + 1:e])
    if "依据索引" not in lines[s]:
        errors.append(f"[检查4] L{s + 1}: 附节标题未含「依据索引」")
        return

    has_fact = bool(
        ADDR_RE.search(body) or DY_RE.search(body) or LN_RE.search(body) or EDGE_RE.search(body)
    )
    if not has_fact:
        errors.append("[检查4] 附节内未出现任何盘面地址或边号")

    has_theory = bool(
        RULE_RE.search(body)
        or RULE_CN_RE.search(body)
        or "source_ref" in body
        or FILELINE_RE.search(body)
    )
    if not has_theory:
        errors.append("[检查4] 附节内未出现任何理论条目 ID、source_ref 或 文件名:行号 出处")


# ============================================================
# CLI
# ============================================================

def _lint_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError as exc:
        return [f"[检查0] 无法读取文件 {path}: {exc}"]
    return lint_human_touch(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.human_touch_linter",
        description="WP-8 防骑墙门禁：检查人话报告的写作纪律与依据完整性",
    )
    parser.add_argument("files", nargs="*", metavar="FILE.md", help="待检查的 Markdown 报告（可多个）")
    args = parser.parse_args(argv)

    if not args.files:
        print("usage: python -m tools.human_touch_linter <file.md> [more.md ...]", file=sys.stderr)
        return 2

    failed = False
    for f in args.files:
        errs = _lint_file(Path(f))
        if errs:
            failed = True
            for e in errs:
                print(f"{f}: {e}", file=sys.stderr)
        else:
            print(f"{f}: OK（0 ERROR）")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
