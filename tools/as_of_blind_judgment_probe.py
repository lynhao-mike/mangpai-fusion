"""as-of 真实盲断闭环 · 阶段一盲态输入截断探针（历史/手动 side path）。

本脚本不注册为默认工具，不切换任何生产入口，也不导入 ``engine.asof``。

修复背景：as-of 盲断闭环第一轮执行把"整份 input.md 含命主已知信息小节"误判为
"污染"，过早触发 STOP、产出 BLOCKED 结论。审计发现该小节是仓库 input.md 模板的
标准组成部分（见 templates/input-from-wenzhen.md 第57行起），不是异常污染。真正
应该做的是把阶段一盲态输入粒度从"整份文件"降级为"排盘小节截断"。本脚本的
``truncate_blind_section()`` 就是这个修复点：把 input.md 截断到已知信息类边界
标记（Markdown 标题或 YAML 顶层键）之前，只保留四柱/藏干/十神/大运等排盘事实。

第二次修复背景：批次验证（见 reports/as-of-life-state-blind-judgment-batch-report.md
§2.2）实测发现，截断边界*之前*的排盘表格本身也可能被旧格式教学案例库（Mang.pai
案例库编号 001-037 段）嵌入真实履历括号注释（例如大运表格行"32-42 | 癸亥 | 比/劫
（深圳外贸）"），这类注释不含任何职业/婚育关键词，纯词表检测无法覆盖。
``detect_table_embedded_annotation()`` 是这个修复点：检测"Markdown 表格行 + 年龄
区间或'当前'标记 + 中文括号注释"这一结构模式本身，不依赖具体词汇。

本脚本的实际公开面有三项：

1. ``truncate_blind_section()``：阶段一盲态输入截断函数，返回
   ``(截断后文本, 截断行号, 边界类型)``。**其函数签名与返回值结构自首次实现后
   保持不变**，本次新增检测函数不改动此函数的任何既有行为。
2. ``detect_table_embedded_annotation()``：独立、可选调用的表格内嵌真实履历
   注释检测函数，返回匹配到该模式的行号列表（不含具体注释内容片段）。调用方
   应在读取截断后视图*之前*（或与读取同一批次内先行）调用本函数作为补充安全
   检查；命中不代表一定是真实污染，只代表存在"表格行+年龄区间+中文括号"这一
   结构模式，需要人工在读取截断视图时额外留意。
3. ``_main()`` CLI：把截断后的纯排盘文本写 stdout、把边界诊断写 stderr，供受控
   会话在阶段一只读取截断结果而不接触原始全文。

冻结盲断与揭示核验的编排**不在本脚本内**：它们由受控会话按当轮合同直接调用
``engine.asof`` 的公共 API（``build_natal_capacity_graph()``、
``adapt_daiyun_segment()``、``evaluate_event_candidate()``、
``freeze_career_draft()``、``run_career_session()``）完成，逐案例落盘产物。
这样每轮的原局判读都必须由该轮会话自己承担，不会被本脚本固化成可复用的
"标准答案"编排。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

__all__ = (
    "KNOWN_FACTS_HEADING_PATTERN",
    "KNOWN_FACTS_YAML_KEY_PATTERN",
    "TABLE_ROW_PATTERN",
    "AGE_RANGE_OR_CURRENT_PATTERN",
    "CHINESE_BRACKET_ANNOTATION_PATTERN",
    "truncate_blind_section",
    "detect_table_embedded_annotation",
)

# 仓库内 input.md 至少存在两种格式变体，均已在本任务实测中确认：
# 1. Markdown 表格模板（见 templates/input-from-wenzhen.md 第57行起）把
#    "命主已知信息" 固定为一个二级标题小节，格式满足 `^##\s+.*已知信息`
#    （可能带序号、v2.0/known_facts 等后缀）。
# 2. 结构化 YAML 代码块模板（schema_version 1.2.0 系列）用顶层 YAML 键
#    `known_facts:` 引入同一类信息，不带 Markdown 标题。若只检测标题格式，
#    这类文件会被误判为"无已知信息"，导致截断函数原样返回全文——这是本探针
#    第一版实测暴露的真实缺口（案例 C-2026-015 触发），现已修复为同时检测
#    两种边界标记。
KNOWN_FACTS_HEADING_PATTERN = re.compile(r"^##\s+.*已知信息")
KNOWN_FACTS_YAML_KEY_PATTERN = re.compile(r"^known_facts\s*:\s*$")


# 候选10（C-2026-010）真实污染事件实测确认的结构模式：Markdown 表格行内，
# 年龄区间（如"32-42"）或"当前"标记之后，紧跟一段中文括号注释（如"（深圳外贸）"）。
# 三个子模式独立组合判定，不依赖任何职业/婚育词表，因此能覆盖词表检测的盲区。
TABLE_ROW_PATTERN = re.compile(r"^\|.*\|.*\|")
AGE_RANGE_OR_CURRENT_PATTERN = re.compile(r"[0-9]+[-\u2013][0-9]+|当前")
CHINESE_BRACKET_ANNOTATION_PATTERN = re.compile(r"[（(][\u4e00-\u9fff]{2,}[）)]")


def detect_table_embedded_annotation(text: str) -> tuple[int, ...]:
    """检测文本中"表格行 + 年龄区间/当前标记 + 中文括号注释"结构模式的行号。

    返回命中该结构模式的 1 基行号元组（可能为空）。本函数只检测结构，不判断
    括号内容是否真的构成污染；命中即视为需要人工在读取该行时额外留意，不能
    仅凭本函数返回空元组就认定该文本绝对安全（本函数不覆盖所有可能的嵌入式
    泄露形态，例如无括号的自由文本注释）。
    """

    hits: list[int] = []
    for index, line in enumerate(text.splitlines()):
        stripped = line.strip()
        if (
            TABLE_ROW_PATTERN.match(stripped)
            and AGE_RANGE_OR_CURRENT_PATTERN.search(stripped)
            and CHINESE_BRACKET_ANNOTATION_PATTERN.search(stripped)
        ):
            hits.append(index + 1)
    return tuple(hits)


def truncate_blind_section(text: str) -> tuple[str, int | None, str | None]:
    """把 input.md 全文截断到第一个已知信息类边界标记之前。

    返回 ``(截断后文本, 截断发生的行号或 None, 边界类型或 None)``。截断行号
    从 1 开始计数，对应原文件中被截掉的边界标记所在行；边界类型是
    ``"heading"``（Markdown 二级标题）或 ``"yaml_key"``（顶层 YAML 键）。
    若全文没有匹配到任一边界标记，返回原文全文、``None``、``None``——调用方
    必须把这种情况视为"无法确认该文件是否纯排盘"，而不是默认视为安全。
    """

    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        stripped = line.strip()
        if KNOWN_FACTS_HEADING_PATTERN.match(stripped):
            return "".join(lines[:index]), index + 1, "heading"
        if KNOWN_FACTS_YAML_KEY_PATTERN.match(stripped):
            return "".join(lines[:index]), index + 1, "yaml_key"
    return text, None, None


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="打印案例 input.md 截断到命主已知信息小节之前的纯排盘文本",
    )
    parser.add_argument("input_path", help="案例 input.md 的路径")
    args = parser.parse_args(argv)

    path = Path(args.input_path)
    text = path.read_text(encoding="utf-8")
    truncated, cut_line, boundary_type = truncate_blind_section(text)
    sys.stdout.write(truncated)
    if cut_line is not None:
        sys.stderr.write(f"[truncated at line {cut_line}: {boundary_type} boundary removed]\n")
    else:
        sys.stderr.write("[UNCONFIRMED: no known-facts boundary marker found; full file returned]\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
