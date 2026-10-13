# as-of 盲态截断探针 · 表格内嵌真实履历注释检测合同

> 最终状态：PASS / COMPLETE - EVIDENCE-BOUNDED FREEZE。
>
> VERIFY 真实证据：
> - python -m pytest tests/tools/test_as_of_blind_judgment_probe.py -v 到 8 passed in 0.11s，退出码 0。
> - python -c 导入检查 truncate_blind_section、detect_table_embedded_annotation、KNOWN_FACTS_HEADING_PATTERN、KNOWN_FACTS_YAML_KEY_PATTERN 到 IMPORT_OK，退出码 0。
> - python -m pytest tests/tools/ -q 到 14 passed in 13.64s，退出码 0，既有 test_theory_slice_status.py 无回归。
>
> 直接证明：新函数能检测合成夹具复现的候选10污染结构模式（表格行加年龄区间加中文括号注释）；对无括号、无年龄区间、英文括号内容的表格行均正确不命中；truncate_blind_section 的三种既有边界行为经回归测试确认未被改动。
>
> 禁止推断：不得推断该检测覆盖所有可能的嵌入式泄露模式（已知局限：无括号自由文本注释、非中文字符括号内容均不命中）；不得推断本次修改已应用于任何既有已冻结批次报告的历史候选筛选结果；不得推断本地测试通过等同 Git/GitHub 同步。
>
> LOCAL ONLY / NOT PUSHED。
> 触发场景：自主发现长任务候选 E（用户指定顺序"先 B 后 E"）。
> 根因证据：[`reports/as-of-life-state-blind-judgment-batch-report.md`](../reports/as-of-life-state-blind-judgment-batch-report.md) §2.2/§2.3 记录的候选 `C-2026-010-坤-甲子丁卯癸卯庚申` 真实污染事件——大运表格行内嵌括号真实履历注释（如"32-42 | 癸亥 | 比/劫（深圳外贸）"），发生在既有截断边界*之前*，[`truncate_blind_section()`](../tools/as_of_blind_judgment_probe.py:52) 无法检测。

## 1. 唯一目标

在 [`tools/as_of_blind_judgment_probe.py`](../tools/as_of_blind_judgment_probe.py) 中新增一个独立函数 `detect_table_embedded_annotation()`，用于检测"Markdown 表格行 + 年龄区间/当前标记 + 中文括号注释"结构模式（不依赖具体词汇），供受控会话在阶段一读取截断视图前先行扫描。**不修改、不扩展 `truncate_blind_section()` 的函数签名或返回值**。

## 2. 权威输入与只读依赖

1. 上游批次报告 [`reports/as-of-life-state-blind-judgment-batch-report.md`](../reports/as-of-life-state-blind-judgment-batch-report.md) §2.2（污染证据，只读，不修改）。
2. 既有 `truncate_blind_section()` 实现（只读参考，不修改）。
3. 本次会话已在多个临时脚本中实测验证过的正则模式：`ROW_PATTERN = r"^\|.*\|.*\|"`、`AGE_PATTERN = r"[0-9]+[-\u2013][0-9]+|当前"`、`BRACKET_PATTERN = r"[（(][\u4e00-\u9fff]{2,}[）)]"`（作为实现参考，非强制照搬）。

## 3. 写集白名单

只允许新增/修改：

1. `tools/as_of_blind_judgment_probe.py`（新增函数 `detect_table_embedded_annotation()`，追加到 `__all__`；不修改 `truncate_blind_section()` 的签名、返回值或既有行为；可更新模块 docstring 说明新函数）。
2. `tests/tools/test_as_of_blind_judgment_probe.py`（新建测试文件，验证新函数）。

**禁止修改**：`truncate_blind_section()` 现有函数体的截断逻辑与返回值结构；`engine/asof/` 任何文件；任何既有测试；任何案例文件；两份既有 as-of 批次报告正文。

## 4. 测试夹具设计（不重新读取案例原文）

测试夹具使用**合成文本**（非真实案例内容），模拟候选10已被记录在报告中的污染模式结构（表格行+年龄区间+括号注释），不重新打开候选10的 `input.md` 或任何其他候选文件。这样测试证据来自本轮已如实记录的污染描述，不构成对候选10本身的二次读取。

## 5. Gate 执行顺序

- ADMISSION：已完成，`PASS`。
- 格局判断：已完成，`PASS`。
- CONTRACT：本文件；完成后逻辑新鲜独立自审。
- IMPLEMENT：新增函数 + 新增测试。
- STATIC_REVIEW：核对签名未变、写集合规、新函数不导入 `engine.asof`。
- VERIFY：运行新测试，记录真实命令输出（退出码、通过数）；同时重跑一次候选10污染模式的合成夹具确认能检测。
- EVIDENCE_REVIEW：逻辑新鲜独立核对测试真实通过、无破坏性变更。
- FREEZE：产出裁决，更新 `handoff.md` 或撰写简短交接。

## 6. STOP 条件

- 若发现修复需要改变 `truncate_blind_section()` 签名才能完成，视为超出本合同范围，停止并如实报告（不得静默扩大范围）；
- 需要执行任何 Git/GitHub 操作。

## 7. 已知的方法论局限

新函数只覆盖"表格行+年龄区间+括号注释"这一种已观测模式；不保证覆盖未来可能出现的其他嵌入式泄露模式（如无括号的自由文本注释）。检测为正则模式匹配，存在假阴性可能（如括号内容为纯数字或英文字母不含中文字符时不会命中）。

## 8. 最终裁决的两种可能取值

- `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`（新函数通过真实测试验证，能检测已记录的污染模式）；
- `BLOCKED — <具体原因>`（若发现需要修改既有签名或存在其他阻塞）。

## 9. 逻辑新鲜独立自审

- 目标明确（新增独立函数，不改既有签名）：**PASS**。
- 写集范围小且不涉及生产/引擎代码：**PASS**。
- 测试夹具设计避免二次读取候选案例：**PASS**。
- Gate 顺序完整：**PASS**。

**本合同自审结论：`PASS`，进入 IMPLEMENT。**

`LOCAL ONLY / NOT PUSHED`
