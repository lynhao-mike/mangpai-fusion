"""六源理论语料的轻量缓存检索器。"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

THEORY_ROOT = Path(__file__).resolve().parents[1] / "theory"
_INDEX_VERSION = 2
SCHOOLS = ("gao", "duan", "yang", "ren", "ziping", "tiaohou_ditiansui")
SCHOOL_NAMES = {
    "gao": "高德臣盲派",
    "duan": "段建业盲派",
    "yang": "杨清娟盲派",
    "ren": "任付红盲派",
    "ziping": "子平",
    "tiaohou_ditiansui": "滴天髓调候派",
}


def _text(value: Any) -> str:
    if isinstance(value, str):
        return " ".join(value.split())
    if isinstance(value, (list, tuple)):
        return " ".join(filter(None, (_text(item) for item in value)))
    return ""


def _short(value: str, limit: int = 200) -> str:
    value = " ".join(value.split())
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def _classic_name(school: str, source_path: str) -> str:
    name = Path(source_path.replace("\\", "/")).name
    if school == "ziping":
        for title in ("子平真诠", "穷通宝鉴", "三命通会", "千里命稿"):
            if title in name:
                return f"《{title}》"
        return "《子平典籍》"
    if school == "tiaohou_ditiansui":
        return "《滴天髓阐微》" if "阐微" in name else "《滴天髓》"
    return SCHOOL_NAMES[school]


def _infer_classic(school: str, rule: dict[str, Any], source_path: str) -> str:
    if school != "ziping":
        return _classic_name(school, source_path)
    for value in (source_path, _text(rule.get("title")), _text(rule.get("claim")), _text(rule.get("output", {}).get("statement") if isinstance(rule.get("output"), dict) else "")):
        for title in ("子平真诠", "穷通宝鉴", "三命通会", "千里命稿"):
            if title in value:
                return f"《{title}》"
    return "《子平典籍》"


def _source_ref(rule: dict[str, Any], index_path: Path, theory_root: Path) -> dict[str, str]:
    source = rule.get("source")
    source = source if isinstance(source, dict) else {}
    path = _text(source.get("path")) or _text(rule.get("raw_file"))
    anchor = _text(source.get("line"))
    if anchor:
        anchor = f"line:{anchor}"
    else:
        anchor = _text(rule.get("raw_anchor")) or _text(source.get("heading"))
    if not path:
        path = index_path.relative_to(theory_root).as_posix()
    return {"path": path.replace("\\", "/"), "anchor": anchor or "rule"}


def _domains(rule: dict[str, Any]) -> str:
    value = rule.get("domains") or rule.get("domain") or rule.get("topic_label") or rule.get("topic")
    return _text(value)


def _tags(rule: dict[str, Any]) -> list[str]:
    value = rule.get("tags") or rule.get("keywords") or rule.get("relations") or []
    if isinstance(value, dict):
        value = list(value.values())
    tags = _text(value).split()
    for key in ("topic_label", "topic"):
        item = _text(rule.get(key))
        if item and item not in tags:
            tags.append(item)
    return tags


def _rule_record(rule: dict[str, Any], school: str, index_path: Path, theory_root: Path) -> dict[str, Any] | None:
    output = rule.get("output")
    output = output if isinstance(output, dict) else {}
    source = rule.get("source")
    source = source if isinstance(source, dict) else {}
    statement = _text(output.get("statement")) or _text(rule.get("conclusion")) or _text(rule.get("claim"))
    title = _text(rule.get("title")) or _text(rule.get("topic_label"))
    if not title and not statement:
        return None
    ref = _source_ref(rule, index_path, theory_root)
    return {
        "id": _text(rule.get("id")) or "UNKNOWN_ID",
        "school": school,
        "classic_name": _infer_classic(school, rule, ref["path"]),
        "title": title,
        "domain": _domains(rule),
        "tags": _tags(rule),
        "statement": _short(statement),
        "source_ref": ref,
        "_search_extra": _text(source.get("excerpt")),
    }


_CANDIDATE_HEADING = re.compile(r"^#{2,3}\s+([A-Za-z0-9][A-Za-z0-9_-]*)\s*[·|｜]\s*(.+?)\s*$")
_CANDIDATE_FIELD = re.compile(r"^\s*[-*]\s*(原文摘录|理论归纳|触发条件|输出方向|拟入模块|适用域)\s*[：:]\s*(.*)$")


def _candidate_records(path: Path, theory_root: Path, school: str) -> list[dict[str, Any]]:
    content = path.read_text(encoding="utf-8-sig")
    source_match = re.search(r"^\s*>?\s*来源[：:]\s*`?([^`\r\n]+)", content, re.MULTILINE)
    source_name = source_match.group(1).strip() if source_match else path.name
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    fields: dict[str, str] = {}

    def finish() -> None:
        if current is None:
            return
        statement = fields.get("理论归纳") or fields.get("原文摘录") or current["title"]
        search_extra = _short(" ".join(fields.get(key, "") for key in ("原文摘录", "触发条件", "输出方向")), 400)
        tags = [fields[key] for key in ("适用域", "拟入模块") if fields.get(key)]
        records.append({
            "id": current["id"],
            "school": school,
            "classic_name": _classic_name(school, source_name),
            "title": current["title"],
            "domain": fields.get("适用域") or fields.get("拟入模块", ""),
            "tags": tags,
            "statement": _short(statement),
            "source_ref": {
                "path": path.relative_to(theory_root.parent).as_posix(),
                "anchor": current["id"],
            },
            "_search_extra": search_extra,
        })

    for line in content.splitlines():
        heading = _CANDIDATE_HEADING.match(line)
        if heading:
            finish()
            current = {"id": heading.group(1), "title": heading.group(2).strip()}
            fields = {}
            continue
        field = _CANDIDATE_FIELD.match(line)
        if current is not None and field:
            fields[field.group(1)] = field.group(2).strip().strip("`")
    finish()
    return records


def _source_files(theory_root: Path) -> list[Path]:
    files = [theory_root / school / "index.yaml" for school in SCHOOLS]
    for school in ("ziping", "tiaohou_ditiansui"):
        files.extend((theory_root / "raw" / school / "extracted").glob("*.md"))
    return sorted(path for path in files if path.is_file())


def _signature(files: list[Path], theory_root: Path) -> list[list[Any]]:
    return [[path.relative_to(theory_root).as_posix(), path.stat().st_size, path.stat().st_mtime_ns] for path in files]


def build_light_index(
    *, theory_root: Path = THEORY_ROOT, cache_path: Path | None = None, rebuild: bool = False
) -> list[dict[str, Any]]:
    """读取缓存；源索引或提取稿变化时重建一次。"""
    theory_root = Path(theory_root)
    cache_path = Path(cache_path) if cache_path else theory_root / "_light_index.json"
    files = [path for path in _source_files(theory_root) if path.is_file()]
    signature = _signature(files, theory_root)
    if not rebuild and cache_path.is_file():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if cached.get("version") == _INDEX_VERSION and cached.get("signature") == signature and isinstance(cached.get("records"), list):
                return cached["records"]
        except (OSError, json.JSONDecodeError, AttributeError):
            pass

    records: list[dict[str, Any]] = []
    for school in SCHOOLS:
        index_path = theory_root / school / "index.yaml"
        if index_path.is_file():
            data = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
            rules = data.get("rules", []) if isinstance(data, dict) else []
            if isinstance(rules, list):
                records.extend(
                    record for rule in rules if isinstance(rule, dict)
                    if (record := _rule_record(rule, school, index_path, theory_root)) is not None
                )
    for school in ("ziping", "tiaohou_ditiansui"):
        for path in sorted((theory_root / "raw" / school / "extracted").glob("*.md")):
            records.extend(_candidate_records(path, theory_root, school))

    for record in records:
        extra = record.pop("_search_extra", "")
        record["_search"] = " ".join((record["title"], " ".join(record["tags"]), record["domain"], record["statement"], extra)).lower()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps({"version": _INDEX_VERSION, "signature": signature, "records": records}, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    return records


def _terms(query: str) -> list[str]:
    return [term.strip().lower() for term in re.split(r"[,，、;；\s]+", query) if term.strip()]


def search_theory(
    query: str,
    *,
    schools: tuple[str, ...] = SCHOOLS,
    domain: str | None = None,
    top_k: int = 5,
    per_school_cap: int | None = 2,
    theory_root: Path = THEORY_ROOT,
    cache_path: Path | None = None,
    rebuild: bool = False,
) -> list[dict[str, Any]]:
    if not query.strip():
        raise ValueError("query must not be empty")
    if not 1 <= top_k <= 10:
        raise ValueError("top_k must be between 1 and 10")
    terms = _terms(query)
    selected = {"tiaohou_ditiansui" if school == "ditiansui" else school for school in schools}
    results: list[tuple[float, dict[str, Any]]] = []
    for record in build_light_index(theory_root=theory_root, cache_path=cache_path, rebuild=rebuild):
        if record["school"] not in selected:
            continue
        if domain and domain.casefold() not in record["domain"].casefold() and domain.casefold() not in " ".join(record["tags"]).casefold():
            continue
        title = record["title"].lower()
        tags = " ".join(record["tags"]).lower()
        body = record.get("_search", record["statement"].lower())
        score = 0.0
        for term in terms:
            if term in title:
                score += 12
            if term in tags:
                score += 8
            if term in record["domain"].lower():
                score += 4
            if term in body:
                score += 2
        query_chars = ""
        if len(terms) == 1 and re.fullmatch(r"[\u3400-\u9fff]{3,}", terms[0]):
            query_chars = terms[0]
            bigrams = [query_chars[index:index + 2] for index in range(len(query_chars) - 1)]
            fields = (title, tags, record["domain"].lower(), body)
            for field, weight in zip(fields, (12, 8, 4, 2)):
                matched = sum(bigram in field for bigram in bigrams)
                if matched:
                    score += weight * matched / len(bigrams)
        if score:
            results.append((score, record))
    results.sort(key=lambda item: (-item[0], item[1]["school"], item[1]["id"]))

    hits: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    classic_counts: dict[tuple[str, str], int] = {}
    while results and len(hits) < top_k:
        eligible = [
            (score - classic_counts.get((record["school"], record["classic_name"]), 0) * 10, index, score, record)
            for index, (score, record) in enumerate(results)
            if not per_school_cap or counts.get(record["school"], 0) < per_school_cap
        ]
        if not eligible:
            break
        _, index, score, record = max(eligible, key=lambda item: (item[0], -item[1]))
        results.pop(index)
        school = record["school"]
        counts[school] = counts.get(school, 0) + 1
        classic = (school, record["classic_name"])
        classic_counts[classic] = classic_counts.get(classic, 0) + 1
        hit = {key: record[key] for key in ("id", "school", "classic_name", "title", "domain", "tags", "statement", "source_ref")}
        hit["score"] = score
        hits.append(hit)
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="检索六源理论规则与古籍候选条目")
    parser.add_argument("--query", required=True, help="关键词；多个词可用空格或逗号分隔")
    parser.add_argument("--schools", nargs="+", default=list(SCHOOLS), choices=(*SCHOOLS, "ditiansui"))
    parser.add_argument("--domain")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--per-school-cap", type=int, default=2, help="每个来源最多命中数；0 表示不限")
    parser.add_argument("--json", action="store_true", dest="as_json", help="输出精简 JSON")
    parser.add_argument("--rebuild-index", action="store_true", help="忽略缓存并重建")
    args = parser.parse_args(argv)
    try:
        hits = search_theory(
            args.query, schools=tuple(args.schools), domain=args.domain, top_k=args.top_k,
            per_school_cap=args.per_school_cap or None, rebuild=args.rebuild_index,
        )
    except ValueError as exc:
        parser.error(str(exc))
    if args.as_json:
        print(json.dumps(hits, ensure_ascii=False, separators=(",", ":")))
    else:
        for hit in hits:
            print(f"[{hit['school']}·{hit['classic_name']}] {hit['title']} — {hit['statement']} ({hit['source_ref']['path']}#{hit['source_ref']['anchor']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
