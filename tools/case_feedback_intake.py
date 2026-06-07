"""tools/case_feedback_intake.py · 真实案例反馈语料抽取工具

用途：
    处理大批量真实命例反馈 Markdown，例如：
      - cases/实战案例反馈990个案例_part1.md
      - cases/实战案例反馈990个案例_part2.md
      - cases/实战案例反馈990个案例_part3.md
      - cases/raw_feedback/source/*.md

定位：
    本工具只做 S0-S3 初步抽取：发现原文、拆分候选、抽取字段、脱敏标记、质量分级、去重摘要。
    它不会创建正式 cases/C-...，不会写 cases-index.md，不会运行 pipeline，不会生成 report，也不会修改 theory/。

输出：
    cases/raw_feedback/parsed/real_cases_990.jsonl
    cases/raw_feedback/parsed/real_cases_990-summary.json

示例：
    python -m tools.case_feedback_intake --dry-run
    python -m tools.case_feedback_intake
    python -m tools.case_feedback_intake --files cases/实战案例反馈990个案例_part1.md
    python -m tools.case_feedback_intake --smoke
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import pathlib
import re
import shutil
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CASES_DIR = REPO_ROOT / "cases"
RAW_FEEDBACK_DIR = CASES_DIR / "raw_feedback"
SOURCE_DIR = RAW_FEEDBACK_DIR / "source"
PARSED_DIR = RAW_FEEDBACK_DIR / "parsed"
DEFAULT_JSONL = PARSED_DIR / "real_cases_990.jsonl"
DEFAULT_SUMMARY = PARSED_DIR / "real_cases_990-summary.json"
DEFAULT_GLOB = "实战案例反馈990个案例_part*.md"
PROTOCOL_PATH = REPO_ROOT / "META" / "case-feedback-intake-protocol.md"

GENDER_RE = re.compile(r"(?<![\u4e00-\u9fff])(男生|女生|男|女|乾|坤)(?![\u4e00-\u9fff])")
CALENDAR_RE = re.compile(r"公\s*\(?阳\)?\s*历|农\s*\(?阴\)?\s*历|阳历|阴历|农历|公历")
ISO_DATE_RE = re.compile(r"(?P<year>19\d{2}|20\d{2})[-/.年]\s*(?P<month>\d{1,2})[-/.月]\s*(?P<day>\d{1,2})")
CN_DATE_RE = re.compile(r"(?P<year>19\d{2}|20\d{2})\s*年\s*(?P<month>\d{1,2})\s*月\s*(?P<day>\d{1,2})\s*[日号]?")
TIME_RE = re.compile(r"(?P<hour>\d{1,2})\s*(?:[:：点时])\s*(?P<minute>\d{1,2})?\s*(?:分)?")
TRUE_SOLAR_RE = re.compile(r"真太阳时[^:：，。\n]*[:：]?\s*(?P<value>\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}[:：]\d{1,2}(?::\d{1,2})?)")
BAZI_RE = re.compile(r"(?P<bazi>[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s*[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s*[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]\s*[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])")
EVENT_RE = re.compile(r"(?P<year>19\d{2}|20\d{2})\s*年?\s*[:：,，、]?\s*(?P<payload>.{0,120}?)(?=(?:19\d{2}|20\d{2})\s*年?\s*[:：,，、]|$)")
QUESTION_SPLIT_RE = re.compile(r"(?:问题|提问|想问|请问|咨询)\s*[:：]")
PLACE_RE = re.compile(
    r"(?P<place>[\u4e00-\u9fff]{2,12}(?:省|自治区|特别行政区|市|地区|盟|州|县|区|旗)(?:\s*[\u4e00-\u9fff]{1,12}(?:市|县|区|旗|镇|乡|街道|人))?)"
)
EXPLICIT_PLACE_RE = re.compile(
    r"(?:出生地|出生于|出生在|出生城市|出生|于)\s*[:：,，]?\s*"
    r"(?P<place>[\u4e00-\u9fff]{2,18}(?:省|自治区|特别行政区|市|地区|盟|州|县|区|旗|香港|澳门|台湾|北京|上海|天津|重庆|马来西亚|新加坡)(?:\s*[\u4e00-\u9fff]{1,12}(?:市|县|区|旗|镇|乡|街道|人))?)"
)
PHONE_RE = re.compile(r"(?:(?:\+?86[-\s]?)?1[3-9]\d{9})")
WECHAT_RE = re.compile(r"(?:微信|vx|VX|v信)\s*[:： ]\s*[A-Za-z0-9_\-*]{4,}")
MASK_RE = re.compile(r"\*{2,}|█+|X{2,}|x{2,}|\?{3,}")

DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "occupation": ("职业", "工作", "事业", "行业", "上班", "央企", "国企", "公务员", "老师", "医生", "程序员", "银行", "销售", "主播"),
    "income": ("收入", "年收入", "工资", "存款", "财运", "身价", "房", "车", "负债", "贷款", "发财", "赚钱", "破财"),
    "family": ("出身", "家庭", "父", "母", "兄", "弟", "姐", "妹", "爷爷", "奶奶", "父母", "家境"),
    "health": ("健康", "身体", "病", "手术", "抑郁", "癌", "住院", "受伤", "骨折", "疾病", "失眠", "焦虑", "体检"),
    "marriage": ("婚姻", "结婚", "离婚", "恋爱", "对象", "女友", "男友", "配偶", "老公", "老婆", "正缘", "感情"),
    "children": ("子女", "孩子", "儿子", "女儿", "生子", "生小孩", "怀孕", "流产"),
    "personality": ("性格", "内向", "外向", "急躁", "慢性子", "社恐", "人缘", "朋友", "领导", "孤独"),
}

SENSITIVE_KEYWORDS: tuple[str, ...] = (
    "自杀", "轻生", "抑郁", "精神", "癌", "牢", "坐过牢", "诈骗", "被骗", "负债", "家暴", "流产", "ICU", "病危", "校园霸凌", "暴力", "灰色", "叔叔通告", "欠债",
)


@dataclass
class RawCandidate:
    source_file: str
    source_path: pathlib.Path
    line_start: int
    line_end: int
    text: str


@dataclass
class IntakeRecord:
    raw_id: str
    source_file: str
    line_start: int
    line_end: int
    gender: str = ""
    qian_kun: str = ""
    calendar_type: str = "unknown"
    birth_datetime_raw: str = ""
    true_solar_time_raw: str = ""
    birth_place_raw: str = ""
    birth_place_sanitized: str = ""
    bazi_raw: str = ""
    events: list[dict[str, Any]] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    profile: dict[str, str] = field(default_factory=dict)
    quality_grade: str = "D"
    quality_flags: list[str] = field(default_factory=list)
    privacy_flags: list[str] = field(default_factory=list)
    duplicate_key: str = ""
    raw_text_hash: str = ""
    raw_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_id": self.raw_id,
            "source_file": self.source_file,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "gender": self.gender,
            "qian_kun": self.qian_kun,
            "calendar_type": self.calendar_type,
            "birth_datetime_raw": self.birth_datetime_raw,
            "true_solar_time_raw": self.true_solar_time_raw,
            "birth_place_raw": self.birth_place_raw,
            "birth_place_sanitized": self.birth_place_sanitized,
            "bazi_raw": self.bazi_raw,
            "events": self.events,
            "questions": self.questions,
            "profile": self.profile,
            "quality_grade": self.quality_grade,
            "quality_flags": self.quality_flags,
            "privacy_flags": self.privacy_flags,
            "duplicate_key": self.duplicate_key,
            "raw_text_hash": self.raw_text_hash,
            "raw_text": self.raw_text,
        }


@dataclass
class IntakeResult:
    dry_run: bool
    source_files: list[str]
    records: list[IntakeRecord]
    output_jsonl: pathlib.Path = DEFAULT_JSONL
    output_summary: pathlib.Path = DEFAULT_SUMMARY
    copied_sources: list[str] = field(default_factory=list)
    duplicate_keys: dict[str, int] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        quality: dict[str, int] = {}
        privacy: dict[str, int] = {}
        flags: dict[str, int] = {}
        for record in self.records:
            quality[record.quality_grade] = quality.get(record.quality_grade, 0) + 1
            for flag in record.privacy_flags:
                privacy[flag] = privacy.get(flag, 0) + 1
            for flag in record.quality_flags:
                flags[flag] = flags.get(flag, 0) + 1
        return {
            "schema_version": "case-feedback-intake/v0.1",
            "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
            "dry_run": self.dry_run,
            "protocol": str(PROTOCOL_PATH.relative_to(REPO_ROOT)).replace("\\", "/"),
            "source_files": self.source_files,
            "source_file_count": len(self.source_files),
            "record_count": len(self.records),
            "quality_distribution": quality,
            "privacy_flag_distribution": privacy,
            "quality_flag_distribution": flags,
            "duplicate_key_count": sum(1 for count in self.duplicate_keys.values() if count > 1),
            "duplicate_record_count": sum(count for count in self.duplicate_keys.values() if count > 1),
            "copied_sources": self.copied_sources,
            "output_jsonl": str(self.output_jsonl.relative_to(REPO_ROOT)).replace("\\", "/"),
            "output_summary": str(self.output_summary.relative_to(REPO_ROOT)).replace("\\", "/"),
        }


def discover_sources(files: Optional[list[str]] = None) -> list[pathlib.Path]:
    """发现真实案例反馈原文。"""
    if files:
        return sorted({_resolve_path(p) for p in files})

    root_sources = sorted(CASES_DIR.glob(DEFAULT_GLOB))
    source_sources = sorted(p for p in SOURCE_DIR.glob("*.md") if not p.name.startswith(".")) if SOURCE_DIR.exists() else []

    # 同名文件同时存在于 cases/ 根目录与 raw_feedback/source/ 时，只处理根目录版本。
    # raw_feedback/source/ 是只读归档副本，避免第二次运行把同一批语料重复计数。
    root_names = {p.name for p in root_sources}
    out: list[pathlib.Path] = list(root_sources)
    out.extend(p for p in source_sources if p.name not in root_names)

    seen: set[pathlib.Path] = set()
    deduped: list[pathlib.Path] = []
    for path in out:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(path)
    return deduped


def _resolve_path(value: str) -> pathlib.Path:
    path = pathlib.Path(value)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def copy_sources_to_raw(paths: Iterable[pathlib.Path], *, dry_run: bool) -> list[str]:
    """把 cases 根目录中的原文复制到 raw_feedback/source/；不覆盖。"""
    copied: list[str] = []
    for path in paths:
        if not path.exists() or path.parent.resolve() == SOURCE_DIR.resolve():
            continue
        target = SOURCE_DIR / path.name
        rel_target = str(target.relative_to(REPO_ROOT)).replace("\\", "/")
        if target.exists():
            continue
        copied.append(rel_target)
        if not dry_run:
            SOURCE_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    return copied


def split_candidates(path: pathlib.Path) -> list[RawCandidate]:
    """按行读取，并对粘连行做保守拆分。"""
    text = path.read_text(encoding="utf-8", errors="replace")
    candidates: list[RawCandidate] = []
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        for segment in _split_line_segments(line):
            if _looks_like_case(segment):
                candidates.append(
                    RawCandidate(
                        source_file=path.name,
                        source_path=path,
                        line_start=lineno,
                        line_end=lineno,
                        text=segment.strip(),
                    )
                )
    return candidates


def _looks_like_case(text: str) -> bool:
    if len(text) < 18:
        return False
    score = 0
    if GENDER_RE.search(text):
        score += 1
    if CALENDAR_RE.search(text) or ISO_DATE_RE.search(text) or CN_DATE_RE.search(text):
        score += 1
    if "经历" in text or "年表" in text or "其他信息" in text or "问题" in text or "问" in text:
        score += 1
    if BAZI_RE.search(text):
        score += 1
    return score >= 2


def _split_line_segments(line: str) -> list[str]:
    """对同一行多案例粘连做启发式拆分。"""
    starts = _case_start_positions(line)
    if len(starts) <= 1:
        return [line]
    segments: list[str] = []
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(line)
        segment = line[start:end].strip(" ，。；;\t")
        if segment:
            segments.append(segment)
    return segments or [line]


def _case_start_positions(line: str) -> list[int]:
    positions = {0}
    pattern = re.compile(
        r"(?:(?<=。)|(?<=！)|(?<=？)|(?<=\s))"
        r"(?=(?:男生|女生|男|女|乾|坤)[,，、。\s]*(?:公\s*\(?阳\)?\s*历|农\s*\(?阴\)?\s*历|阳历|阴历|农历|公历|\d{4}))"
    )
    for match in pattern.finditer(line):
        positions.add(match.start())
    return sorted(positions)


def parse_candidate(candidate: RawCandidate, index: int) -> IntakeRecord:
    text = _normalize_space(candidate.text)
    record = IntakeRecord(
        raw_id=f"RF-2026-{index:06d}",
        source_file=candidate.source_file,
        line_start=candidate.line_start,
        line_end=candidate.line_end,
        raw_text=text,
        raw_text_hash=_sha1(text),
    )
    record.gender, record.qian_kun = _extract_gender(text)
    record.calendar_type = _extract_calendar_type(text)
    record.birth_datetime_raw = _extract_birth_datetime(text)
    record.true_solar_time_raw = _extract_true_solar_time(text)
    record.birth_place_raw = _extract_birth_place(text)
    record.birth_place_sanitized = _sanitize_place(record.birth_place_raw)
    record.bazi_raw = _extract_bazi(text)
    record.events = _extract_events(text)
    record.questions = _extract_questions(text)
    record.profile = _extract_profile(text)
    record.privacy_flags = _privacy_flags(text)
    record.quality_grade, record.quality_flags = _quality_grade(record)
    record.duplicate_key = _duplicate_key(record)
    return record


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()


def _extract_gender(text: str) -> tuple[str, str]:
    match = GENDER_RE.search(text)
    if not match:
        return "", ""
    value = match.group(1)
    if value in {"男", "男生", "乾"}:
        return "男", "乾"
    return "女", "坤"


def _extract_calendar_type(text: str) -> str:
    prefix = text[:80]
    if re.search(r"农\s*\(?阴\)?\s*历|阴历|农历", prefix):
        return "lunar"
    if re.search(r"公\s*\(?阳\)?\s*历|阳历|公历", prefix):
        return "solar"
    if ISO_DATE_RE.search(prefix) or CN_DATE_RE.search(prefix):
        return "solar_unspecified"
    return "unknown"


def _extract_birth_datetime(text: str) -> str:
    date_match = ISO_DATE_RE.search(text[:180]) or CN_DATE_RE.search(text[:180])
    if not date_match:
        return ""
    start = date_match.start()
    window = text[start:start + 80]
    time_match = TIME_RE.search(window)
    if time_match:
        return window[:time_match.end()].strip(" ，。,")
    return date_match.group(0).strip()


def _extract_true_solar_time(text: str) -> str:
    match = TRUE_SOLAR_RE.search(text[:240])
    return match.group("value").replace("：", ":") if match else ""


def _extract_birth_place(text: str) -> str:
    head = text[:260]
    explicit = [_clean_place(m.group("place")) for m in EXPLICIT_PLACE_RE.finditer(head)]
    if explicit:
        return explicit[-1]

    places = [_clean_place(m.group("place")) for m in PLACE_RE.finditer(head)]
    filtered = [
        p for p in places
        if p and not any(bad in p for bad in ("阳历", "阴历", "公历", "农历", "上市", "年月", "月份"))
    ]
    return filtered[-1] if filtered else ""


def _clean_place(place: str) -> str:
    place = re.sub(r"^[分于在]+", "", place.strip(" ，。；;:："))
    place = re.sub(r"人$", "", place)
    return place.strip()


def _sanitize_place(place: str) -> str:
    if not place:
        return ""
    place = _clean_place(place)
    match = re.search(r"(.+?(?:省|自治区|特别行政区|市|地区|盟|州|香港|澳门|台湾|北京|上海|天津|重庆))", place)
    if match:
        return match.group(1).strip()
    return place[:8]


def _extract_bazi(text: str) -> str:
    match = BAZI_RE.search(text[:260])
    if not match:
        return ""
    return re.sub(r"\s+", "", match.group("bazi"))


def _extract_events(text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    body = text
    if "年表经历" in text:
        body = text.split("年表经历", 1)[1]
    for match in EVENT_RE.finditer(body):
        year = int(match.group("year"))
        payload = match.group("payload").strip(" ，。；;:")
        if not payload or len(payload) < 2:
            continue
        events.append({
            "year": year,
            "polarity": _event_polarity(payload),
            "domains": _event_domains(payload),
            "text": payload[:160],
        })
        if len(events) >= 40:
            break
    return events


def _event_polarity(text: str) -> str:
    if "吉" in text and "凶" not in text:
        return "positive"
    if "凶" in text and "吉" not in text:
        return "negative"
    return "unknown"


def _event_domains(text: str) -> list[str]:
    out: list[str] = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(k in text for k in keywords):
            out.append(domain)
    return out


def _extract_questions(text: str) -> list[str]:
    questions: list[str] = []
    parts = QUESTION_SPLIT_RE.split(text, maxsplit=1)
    if len(parts) == 2:
        tail = parts[1]
    else:
        return questions
    for part in re.split(r"[？?]|(?:\s+\d+[、.．])", tail):
        s = part.strip(" ，。；;:：")
        if 4 <= len(s) <= 120:
            questions.append(s)
        if len(questions) >= 12:
            break
    return questions


def _extract_profile(text: str) -> dict[str, str]:
    profile = {key: "" for key in DOMAIN_KEYWORDS}
    chunks = re.split(r"(?=职业|身价|年收入|收入|出身|健康情况|健康|婚姻情况|婚姻|子女情况|子女|性格特点|性格)", text)
    for key, keywords in DOMAIN_KEYWORDS.items():
        for chunk in chunks:
            if any(k in chunk[:20] for k in keywords):
                profile[key] = chunk[:180].strip(" ，。；;")
                break
    return profile


def _privacy_flags(text: str) -> list[str]:
    flags: list[str] = []
    if PHONE_RE.search(text):
        flags.append("phone")
    if WECHAT_RE.search(text):
        flags.append("wechat")
    if MASK_RE.search(text):
        flags.append("masked_or_redacted")
    if any(k in text for k in SENSITIVE_KEYWORDS):
        flags.append("sensitive_life_event")
    if len(_extract_birth_place(text)) >= 8:
        flags.append("detailed_place")
    return sorted(set(flags))


def _quality_grade(record: IntakeRecord) -> tuple[str, list[str]]:
    flags: list[str] = []
    if not record.gender:
        flags.append("missing_gender")
    if not record.birth_datetime_raw and not record.bazi_raw:
        flags.append("missing_birth_datetime_or_bazi")
    if record.calendar_type == "unknown":
        flags.append("unknown_calendar")
    if not record.birth_place_raw and not record.true_solar_time_raw:
        flags.append("missing_birth_place_or_true_solar_time")
    if len(record.raw_text) > 1800:
        flags.append("very_long_possible_concatenation")
    if len(record.raw_text) < 45:
        flags.append("too_short")
    if _has_abnormal_date(record.birth_datetime_raw):
        flags.append("abnormal_birth_date")
    if not record.events:
        flags.append("missing_events")
    if not record.questions:
        flags.append("missing_questions")

    fatal = {"missing_birth_datetime_or_bazi", "abnormal_birth_date", "too_short"}
    if any(f in fatal for f in flags):
        return "D", flags
    if len(flags) >= 4 or "very_long_possible_concatenation" in flags:
        return "C", flags
    if flags:
        return "B", flags
    return "A", flags


def _has_abnormal_date(value: str) -> bool:
    if not value:
        return False
    match = ISO_DATE_RE.search(value) or CN_DATE_RE.search(value)
    if not match:
        return False
    year = int(match.group("year"))
    month = int(match.group("month"))
    day = int(match.group("day"))
    if year < 1900 or year > 2026:
        return True
    if month < 1 or month > 12:
        return True
    if day < 1 or day > 31:
        return True
    return False


def _duplicate_key(record: IntakeRecord) -> str:
    bits = [record.gender, record.calendar_type, record.birth_datetime_raw, record.true_solar_time_raw, record.bazi_raw]
    base = "|".join(bits).strip("|")
    if not base:
        base = record.raw_text[:120]
    return _sha1(base)


def intake(files: Optional[list[str]] = None, *, dry_run: bool = False) -> IntakeResult:
    sources = discover_sources(files)
    copied = copy_sources_to_raw(sources, dry_run=dry_run)
    candidates: list[RawCandidate] = []
    for path in sources:
        if not path.exists():
            continue
        candidates.extend(split_candidates(path))

    records = [parse_candidate(candidate, idx) for idx, candidate in enumerate(candidates, start=1)]
    duplicate_keys: dict[str, int] = {}
    for record in records:
        duplicate_keys[record.duplicate_key] = duplicate_keys.get(record.duplicate_key, 0) + 1
        if duplicate_keys[record.duplicate_key] > 1 and "possible_duplicate" not in record.quality_flags:
            record.quality_flags.append("possible_duplicate")
            if record.quality_grade == "A":
                record.quality_grade = "B"

    result = IntakeResult(
        dry_run=dry_run,
        source_files=[str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in sources],
        records=records,
        copied_sources=copied,
        duplicate_keys=duplicate_keys,
    )
    if not dry_run:
        _write_outputs(result)
    return result


def _write_outputs(result: IntakeResult) -> None:
    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    with result.output_jsonl.open("w", encoding="utf-8") as fh:
        for record in result.records:
            fh.write(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
    result.output_summary.write_text(
        json.dumps(result.summary(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _print_human(result: IntakeResult) -> None:
    summary = result.summary()
    print("case-feedback-intake")
    print(f"  dry_run: {summary['dry_run']}")
    print(f"  sources: {summary['source_file_count']}")
    for src in summary["source_files"]:
        print(f"    - {src}")
    print(f"  records: {summary['record_count']}")
    print(f"  quality: {summary['quality_distribution']}")
    print(f"  privacy_flags: {summary['privacy_flag_distribution']}")
    print(f"  quality_flags: {summary['quality_flag_distribution']}")
    print(f"  duplicate_keys: {summary['duplicate_key_count']}")
    if result.copied_sources:
        print("  copied_sources:")
        for path in result.copied_sources:
            print(f"    - {path}")
    if not result.dry_run:
        print(f"  wrote: {summary['output_jsonl']}")
        print(f"  wrote: {summary['output_summary']}")


def _smoke() -> int:
    sample = "女 公(阳)历:1999 年 7 月 13 日 14:00 分, 广州市 荔湾区人。真太阳时时间: 1999-07-13 13:36:00 年表经历：2018 年: 吉,高考发挥好。2024 年: 凶,健康检查异常。其他信息: 职业：写作 健康情况: 体弱 婚姻情况: 未婚 子女情况: 无 性格特点: 慢性子 问题：未来事业如何？"
    candidate = RawCandidate("smoke.md", pathlib.Path("smoke.md"), 1, 1, sample)
    record = parse_candidate(candidate, 1)
    assert record.gender == "女"
    assert record.qian_kun == "坤"
    assert record.calendar_type == "solar"
    assert record.birth_datetime_raw
    assert record.true_solar_time_raw
    assert record.events
    assert record.questions
    assert record.quality_grade in {"A", "B"}
    print("smoke passed")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="真实案例反馈语料抽取工具")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写入 parsed/，不复制 source/")
    parser.add_argument("--files", nargs="*", help="指定要处理的 Markdown 文件路径")
    parser.add_argument("--smoke", action="store_true", help="运行内置 smoke test")
    args = parser.parse_args(argv)

    if args.smoke:
        return _smoke()

    result = intake(args.files, dry_run=args.dry_run)
    _print_human(result)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
