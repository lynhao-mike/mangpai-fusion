"""从带规则 ID 的原稿提取定义；不推断或生成命理断语。"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

RULE_ID = re.compile(r"M[13]-[DR]-\d{3}(?!\d)")
HEADING = re.compile(r"^(#{1,6})\s+(.+)")


def raw_rule_bodies(theory_root: Path, school: str) -> dict[str, dict[str, Any]]:
    candidates: dict[str, tuple[int, dict[str, Any]]] = {}

    def offer(ids: list[str], body: str, path: Path, line: int, priority: int) -> None:
        body = body.strip()
        if not body:
            return
        for rule_id in ids:
            if priority > candidates.get(rule_id, (-1, {}))[0]:
                candidates[rule_id] = (priority, {
                    "conclusion": body,
                    "raw_file": path.relative_to(theory_root.parent).as_posix(),
                    "raw_anchor": f"line:{line}",
                })

    for path in sorted((theory_root / "raw" / school).rglob("*.md")):
        text = path.read_text(encoding="utf-8-sig")
        lines = text.splitlines()
        # 完整 YAML 定义优先，保留条件、结论、排除项及反证边界。
        for match in re.finditer(r"^```ya?ml\s*\n(.*?)^```", text, re.MULTILINE | re.DOTALL):
            try:
                data = yaml.safe_load(match.group(1))
            except yaml.YAMLError:
                continue
            if not isinstance(data, dict) or not RULE_ID.fullmatch(str(data.get("rule_id", ""))):
                continue
            parts = []
            for key in ("trigger", "conclusion", "exceptions", "exclusions", "falsifiable_by"):
                if data.get(key):
                    value = data[key]
                    rendered = value if isinstance(value, str) else yaml.safe_dump(value, allow_unicode=True, sort_keys=False).strip()
                    parts.append(f"{key}: {rendered}")
            id_match = re.search(r"^\s*rule_id:", match.group(1), re.MULTILINE)
            offset = match.start(1) + (id_match.start() if id_match else 0)
            offer([data["rule_id"]], "\n".join(parts), path, text.count("\n", 0, offset) + 1, 30)
        for i, line in enumerate(lines):
            heading = HEADING.match(line)
            ids = RULE_ID.findall(line)
            if heading and ids and re.match(r"M[13]-[DR]-\d{3}", heading.group(2)):
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
                    body = "；".join(f"{headers[n] if n < len(headers) else '说明'}：{cell}" for n, cell in enumerate(cells) if not RULE_ID.fullmatch(cell))
                    offer(ids, body, path, i + 1, 10)
    return {rule_id: record for rule_id, (_, record) in candidates.items()}
