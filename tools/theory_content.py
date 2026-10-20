"""从带规则 ID 的原稿提取定义；不推断或生成命理断语。"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

# 覆盖高派 M1-D / 段派 M1-D / 杨派 M2-Y / 任派 M3-R 四类规则 ID。
# 早先的 M[13]-[DR]- 漏掉杨派 M2-Y，导致杨派 registry 条目全部取不到正文。
RULE_ID = re.compile(r"M[123]-[DRY]-\d{3}(?!\d)")
HEADING = re.compile(r"^(#{1,6})\s+(.+)")
# rule_id 键行：允许列表项符号与空白前缀。
# 必须用 ^[ \t]*-?[ \t]*rule_id: 而非 ^\s*——markdown 混排块里内容行
# 可能带 `> ` 前缀，\s* 会把这种非键行也算作键行，行号整体偏 1。
RULE_ID_LINE = re.compile(r"^[ \t]*-?[ \t]*rule_id[ \t]*:[ \t]*(\S+)[ \t]*$", re.MULTILINE)
# YAML 块内出现的 markdown 装饰行（标题 / 引用 / 表格 / 分隔线 / 反引号）。
# 注意 `-{3,}\s*$`：必须整行都是连字符才算分隔线；早期写成 `-{3,}` 会把
# YAML 列表项 `- D-06 …`（一个连字符 + 空格 + 正文）也当噪声删掉，
# 直接把段派 13 个块的 source / conclusion 列表打成空。
_MD_NOISE = re.compile(r"^\s*(?:#{1,6}\s|\||>|\*{3,}|\+\s|`|-{3,}\s*$)")
# 顶层键行（可带 `- ` 列表符）。key 列 = 缩进 + 列表符宽度，用它对齐嵌套层级。
_KEY_LINE = re.compile(r"^(?P<indent>[ \t]*)(?P<dash>-[ \t]+)?(?P<key>[A-Za-z_][\w-]*)[ \t]*:(?:[ \t]+(?P<inline>.*))?[ \t]*$")

# 组成「可追溯正文」的字段：保留条件、结论、排除项及反证边界。
_BODY_KEYS = ("trigger", "conclusion", "statement", "exceptions", "exclusions", "falsifiable_by")
# trigger 归一化时的取值顺序。
_TRIGGER_KEYS = ("condition", "when", "context", "prerequisites")


def _strip_markdown_noise(body: str) -> str:
    """剥掉 YAML 块里的 markdown 装饰行，保留纯 YAML 行。"""
    return "\n".join(line for line in body.splitlines() if not _MD_NOISE.match(line))


def _try_load(text: str) -> tuple[Any, str | None]:
    try:
        return yaml.safe_load(text), None
    except yaml.YAMLError as exc:
        return None, str(exc)


def _block_column(line: str) -> int:
    """返回键的列位（缩进 + `- ` 列表符宽度），用于判断嵌套层级。"""
    body = line.lstrip(" \t")
    if body.startswith("-"):
        return len(line) - len(body) + 1
    return len(line) - len(body)


def _drop_orphan_continuations(lines: list[str]) -> list[str]:
    """删掉「孤儿续行」：缩进键行，且其上一条顶层键已带内联标量值。

    原稿偶有把列表字段粘到标量后面的排版错误，例如
    ``calibration_rule_id: R-M1-31`` 之后紧跟 ``  topics: [...]``，
    PyYAML 报 "mapping values are not allowed here" 整块失败。
    真正属于嵌套结构的键（condition / prerequisites / topics 等）其上一条
    顶层键必然没有内联值，所以不会被误删。
    """
    kept: list[str] = []
    prev_top_had_inline = False
    for line in lines:
        match = _KEY_LINE.match(line)
        if match and _block_column(line) > 0 and prev_top_had_inline:
            prev_top_had_inline = False
            continue
        if match and _block_column(line) == 0:
            prev_top_had_inline = bool(match.group("inline"))
        kept.append(line)
    return kept


def _drop_bad_continuations(lines: list[str]) -> list[str]:
    """丢掉无法单独解析的行——未闭合引号、未转义引号、孤儿续行。

    原稿偶有这些坏行，会让 PyYAML 整块报错：
    - ``name: "有"vs"没有"二元判读``  —— 未加引号的字符串里含裸双引号；
    - ``- 若…则等同"有禄"，需补判``   —— 列表项引号没闭合；
    - ``calibration_rule_id: R-M1-31`` 之后紧跟 ``  topics: [...]``。

    逐行试解析，只丢坏行，其余原样保留。丢一行只损失该字段，
    保住同块的 trigger / conclusion / confidence_init。
    """
    kept: list[str] = []
    for line in lines:
        if line.strip():
            _, error = _try_load(line)
            if error:
                continue
        kept.append(line)
    return kept


def _looks_like_key(line: str) -> bool:
    """判断一行是否形如 ``key: value``（键名可含中日韩字符）。

    块级标量续行里偶见 ``  关键: 看偏印是否与食神争`` 这种伪键，
    ``_KEY_LINE`` 只认 ASCII 键名，匹配不到它，但它照样让 PyYAML 报
    "mapping values are not allowed here"。
    """
    stripped = line.strip()
    if not stripped or stripped.startswith(("-", "#", "|", ">", '"', "'", "[")):
        return False
    match = re.match(r"^([^\s:#][^:#]{0,40})[ \t]*:[ \t]*(.*)$", stripped)
    if not match:
        return False
    # 值里再出现冒号的多半是普通句子（如「关键：看 X 是否符合 Y：否则 Z」）
    return ":" not in match.group(2)


def _neutralize_scalar_keys(lines: list[str]) -> list[str]:
    """中和块级标量里长得像 ``key: value`` 的续行（半角冒号 → 全角）。

    原稿 ``conclusion:`` 下常直接写多行断语，其中一行形如
    ``  关键: 看偏印是否与食神争或与杀和``。PyYAML 在块级标量里遇到
    冒号会报 "mapping values are not allowed here" 整块失败。把冒号换成
    全角即可让它继续当普通文本行，不影响 trigger / conclusion 取值。
    """
    kept: list[str] = []
    for line in lines:
        if line[:1] in " \t" and line.strip() and not _KEY_LINE.match(line) and _looks_like_key(line):
            kept.append(line.replace(":", "：", 1))
            continue
        kept.append(line)
    return kept


def _parse_records(text: str) -> list[dict[str, Any]]:
    """按顶层 ``rule_id:`` 键切记录，容忍 markdown 混排与坏行。

    这是 ``yaml.safe_load`` 的兜底：段派 16 个 yaml 块里混有未转义引号、
    孤儿续行或块级标量里的伪键行，PyYAML 会整块报错。这里先按顶层
    ``rule_id:`` 行切段，再依次尝试多种修法。坏段丢掉，不影响同块其他规则。
    """
    lines = [line for line in text.splitlines() if not _MD_NOISE.match(line)]
    # 顶层 rule_id 行 = 列位为 0（允许 `- ` 列表符）的 rule_id 键。
    starts = [
        i for i, line in enumerate(lines)
        if (m := _KEY_LINE.match(line)) is not None
        and m.group("key") == "rule_id" and _block_column(line) == 0
    ]
    if not starts:
        return []
    records: list[dict[str, Any]] = []
    for start, end in zip(starts, starts[1:] + [len(lines)]):
        chunk = lines[start:end]
        attempts = [chunk]
        for repair in (_drop_orphan_continuations, _neutralize_scalar_keys,
                       _drop_bad_continuations):
            candidate = repair(chunk)
            if len(candidate) != len(chunk):
                attempts.append(candidate)
        for attempt in attempts:
            data, _ = _try_load("\n".join(attempt))
            if isinstance(data, dict):
                records.append(data)
                break
    return records


def _parse_yaml_rules(body: str) -> list[dict[str, Any]]:
    """解析一个 ```yaml 块，返回其中的规则字典列表。

    容错四档，前两档保整体，后两档逐条抢救：
    1. ``yaml.safe_load(body)`` —— 好格式块（单字典或规则列表）；
    2. 剥离 markdown 装饰行后重试 —— 块内混排 `>` 引用 / 表格 / 分隔线；
    3. 按顶层 ``rule_id:`` 切记录重试 —— 单条坏行拖垮整块的场景；
    4. 丢掉单独解析就失败的键行后重试 —— 原稿偶有
       ``name: "…"铁律`` 这种引号后紧跟正文的非法标量。

    早先的实现只认 ``isinstance(data, dict)``，段派 50 条、任派 30 条
    规则列表块被整块丢弃。
    """
    cleaned = _strip_markdown_noise(body)
    neutralized = "\n".join(_neutralize_scalar_keys(cleaned.splitlines()))
    for candidate in (body, cleaned, neutralized):
        data, _ = _try_load(candidate)
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]

    salvaged = _parse_records(neutralized)
    if salvaged:
        return salvaged

    # 丢掉单独解析就失败的顶层键行（如引号后紧跟正文的非法标量），再整体重试。
    for source in (cleaned, body):
        lines = source.splitlines()
        keep = [
            line for line in lines
            if not (_KEY_LINE.match(line) and _try_load(line)[1])
        ]
        if len(keep) != len(lines):
            data, _ = _try_load("\n".join(keep))
            if isinstance(data, dict):
                return [data]
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
    return []


def _format_trigger(value: Any) -> str:
    """把 trigger 规范为单行文本。

    原稿里 trigger 有两种写法：自然语言字符串，或
    ``trigger: {condition: ..., prerequisites: [...]}`` 的结构化字典。
    后者不归一化就直接写进 index.yaml，会变成多行 mapping 破坏生成文件。
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    if isinstance(value, dict):
        parts: list[str] = []
        for key in _TRIGGER_KEYS:
            item = value.get(key)
            if not item:
                continue
            if isinstance(item, str):
                text = re.sub(r"\s+", " ", item).strip()
            else:
                text = re.sub(r"\s+", " ", " ".join(str(x) for x in item)).strip()
            if text:
                parts.append(text if key == "condition" else f"{key}={text}")
        return " ".join(parts).strip()
    if isinstance(value, list):
        return " ".join(filter(None, (_format_trigger(item) for item in value))).strip()
    return re.sub(r"\s+", " ", str(value)).strip()


def _render_field(key: str, value: Any) -> str:
    """把单个字段渲染成单行 ``key: value``。"""
    if isinstance(value, str):
        rendered = re.sub(r"\s+", " ", value).strip()
    else:
        rendered = re.sub(r"\s+", " ", yaml.safe_dump(value, allow_unicode=True, sort_keys=False).strip())
    return f"{key}: {rendered}" if rendered else ""


def _rule_body(record: dict[str, Any]) -> tuple[str, str, float | None]:
    """渲染一条规则，返回 ``(可追溯正文, trigger 单行文本, 初始分)``。"""
    parts: list[str] = []
    trigger = ""
    for key in _BODY_KEYS:
        value = record.get(key)
        if not value:
            continue
        if key == "trigger":
            trigger = _format_trigger(value)
            if not trigger:
                continue
        rendered = _format_trigger(value) if key == "trigger" else _render_field(key, value)
        if rendered:
            parts.append(rendered)
    return "\n".join(parts), trigger, _parse_score(record.get("confidence_init"))


def _parse_score(value: Any) -> float | None:
    """把 confidence_init 解析为浮点；原稿可能是 4.5 / "4.5" / 4 等形式。"""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"-?\d+(?:\.\d+)?", str(value))
    return float(match.group(0)) if match else None


def raw_rule_bodies(theory_root: Path, school: str) -> dict[str, dict[str, Any]]:
    candidates: dict[str, tuple[int, dict[str, Any]]] = {}

    def offer(ids: list[str], body: str, path: Path, line: int, priority: int,
              trigger: str = "", confidence_init: float | None = None) -> None:
        body = body.strip()
        if not body:
            return
        for rule_id in ids:
            if priority > candidates.get(rule_id, (-1, {}))[0]:
                record: dict[str, Any] = {
                    "conclusion": body,
                    "raw_file": path.relative_to(theory_root.parent).as_posix(),
                    "raw_anchor": f"line:{line}",
                }
                # trigger 单独落字段，供 index.yaml 生成；缺失时不写空串。
                if trigger:
                    record["trigger"] = trigger
                # 原稿的 confidence_init（段派/杨派多为 3.0~5.0 分制）落成初始分。
                if confidence_init is not None:
                    record["confidence_init"] = confidence_init
                candidates[rule_id] = (priority, record)

    for path in sorted((theory_root / "raw" / school).rglob("*.md")):
        text = path.read_text(encoding="utf-8-sig")
        lines = text.splitlines()
        # 完整 YAML 定义优先，保留条件、结论、排除项及反证边界。
        for match in re.finditer(r"^```ya?ml\s*\n(.*?)^```", text, re.MULTILINE | re.DOTALL):
            body = match.group(1)
            rules = _parse_yaml_rules(body)
            if not rules:
                continue
            by_id = {str(r.get("rule_id") or "").strip(): r for r in rules}
            # 逐条定位 rule_id 行号，避免整块共用一个锚点。
            for id_match in RULE_ID_LINE.finditer(body):
                line = text.count("\n", 0, match.start(1) + id_match.start()) + 1
                rule_id = id_match.group(1).strip().strip("\"'")
                if not RULE_ID.fullmatch(rule_id):
                    continue
                record = by_id.get(rule_id)
                if record is None:
                    continue
                rendered, trigger, confidence = _rule_body(record)
                offer([rule_id], rendered, path, line, 30, trigger, confidence)
            continue
        # Markdown 标题回退：```### M1-D-001 标题``` 之后到同级标题为止。
        for i, line in enumerate(lines):
            heading = HEADING.match(line)
            ids = RULE_ID.findall(line)
            if heading and ids and re.match(r"M[123]-[DRY]-\d{3}", heading.group(2)):
                end = i + 1
                while end < len(lines):
                    next_heading = HEADING.match(lines[end])
                    if next_heading and len(next_heading.group(1)) <= len(heading.group(1)):
                        break
                    end += 1
                offer(ids, "\n".join(lines[i + 1:end]).strip().strip("-\n"), path, i + 1, 20)
            elif line.lstrip().startswith("|") and len(ids) == 1:
                # 表格回退保留列名，避免把目录中的规则名当成完整正文。
                start = i
                while start > 0 and lines[start - 1].lstrip().startswith("|"):
                    start -= 1
                headers = [x.strip() for x in lines[start].strip().strip("|").split("|")]
                cells = [x.strip() for x in line.strip().strip("|").split("|")]
                if len(cells) >= 3:
                    body = "；".join(
                        f"{headers[n] if n < len(headers) else '说明'}：{cell}"
                        for n, cell in enumerate(cells) if not RULE_ID.fullmatch(cell)
                    )
                    offer(ids, body, path, i + 1, 10)
    return {rule_id: record for rule_id, (_, record) in candidates.items()}
