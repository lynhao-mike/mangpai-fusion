"""tools/extract_predictions.py · v1.2 Track-G 应期自动抽取

落地契约：
    engine/contracts/00-OVERVIEW.md 决策 J（引擎自动从报告 ★★★★+ 应期抽取）
    engine/contracts/07-pipeline-flow.md § 十一（archive + predict 步骤）
    engine/contracts/09-naming-convention.md § 二·3（predictions 文件名规范）

职责：
    扫描 reports/C-*-report.md（或 cases/C-*/findings/analysis_output.json）
    把 ★★★★+ 的应期断语抽出来 → predictions/PRED-YYYY-NNN-CXXXXXXX-{干支}-{event}.md

文件名格式（09 § 二·3）：
    predictions/PRED-YYYY-NNN-CXXXXXXX-{干支}-{event}.md
    其中：
        YYYY = 应期年（不是 case 年）
        NNN  = 当年序号（001 起）
        CXXXXXXX = case_id 简化（去 dash）
        干支 = 4 柱 8 字
        event = future / verification / 具体事件名（拼音/英文，避免特殊符号）

frontmatter 必须含：
    yingqi_year, falsifiable, case_id, statement, confidence_star, confidence_percent
    schools, domain, status=pending

注意：
    - 优先消费 cases/C-XXX/findings/analysis_output.json（Track-F 落盘的结构化输出）
    - 当结构化文件不存在时，对 reports/C-*-report.md 做启发式抽取（fallback）
    - 已存在的 predictions 文件不覆盖（按文件名指纹判重）

作者：Track-G
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import pathlib
import re
from dataclasses import dataclass
from typing import Any, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PREDICTIONS_DIR = REPO_ROOT / "predictions"
REPORTS_DIR = REPO_ROOT / "reports"
CASES_DIR = REPO_ROOT / "cases"


# ============================================================
# 一、数据结构
# ============================================================

@dataclass
class PredictionDraft:
    case_id: str
    case_ganzhi: str       # "庚申戊寅壬子辛丑"
    yingqi_year: int
    statement: str
    confidence_star: int
    confidence_percent: int
    schools: list[str]
    domain: Optional[str]
    falsifiable: str
    source: str            # "report" / "analysis_output"
    raw_line: str = ""

    def fingerprint(self) -> str:
        h = hashlib.md5()
        h.update(
            f"{self.case_id}|{self.yingqi_year}|{self.statement}".encode("utf-8")
        )
        return h.hexdigest()[:8]

    def event_slug(self) -> str:
        """事件名 slug，进文件名。

        简单策略：取断语前 12 个非标点中文字符；若全英文则保留前 24 字符。
        """
        text = self.statement
        # 去 markdown / 标点
        text = re.sub(r"[★*_`#\[\](){}|/\\,.:;!?'\"\s—\-]+", "", text)
        if not text:
            text = self.domain or "future"
        if len(text) > 12:
            text = text[:12]
        return text


# ============================================================
# 二、case_id 工具
# ============================================================

CASE_ID_RE = re.compile(r"^C-(\d{4})-(\d{3})-([\u4e00-\u9fff]{8})$")


def parse_case_id(case_id: str) -> tuple[str, str]:
    """C-2026-001-庚申戊寅壬子辛丑 → ("C2026001", "庚申戊寅壬子辛丑")"""
    m = CASE_ID_RE.match(case_id)
    if not m:
        # 接受不带干支的 fallback
        plain = case_id.replace("-", "")
        return plain, ""
    yyyy, nnn, ganzhi = m.groups()
    return f"C{yyyy}{nnn}", ganzhi


def list_case_dirs() -> list[pathlib.Path]:
    if not CASES_DIR.exists():
        return []
    out = []
    for p in CASES_DIR.iterdir():
        if p.is_dir() and CASE_ID_RE.match(p.name):
            out.append(p)
    return sorted(out)


# ============================================================
# 三、抽取：analysis_output.json（Track-F 结构化）
# ============================================================

def extract_from_analysis_output(case_dir: pathlib.Path) -> list[PredictionDraft]:
    """从 cases/C-XXX/findings/analysis_output.json 抽取 ★★★★+ 应期。

    若该文件不存在 → 返回 []（让 caller 走 fallback）。
    """
    out: list[PredictionDraft] = []
    findings_dir = case_dir / "findings"
    aout = findings_dir / "analysis_output.json"
    if not aout.exists():
        return out

    try:
        data: dict[str, Any] = json.loads(aout.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return out

    case_id = data.get("case_id", case_dir.name)
    plain, ganzhi = parse_case_id(case_id)

    # 优先看 final_conclusions（含 yingqi_year）
    for c in data.get("final_conclusions", []) or []:
        conf = c.get("confidence") or {}
        if int(conf.get("star", 0)) < 4:
            continue
        if c.get("yingqi_year") is None:
            continue
        out.append(PredictionDraft(
            case_id=case_id,
            case_ganzhi=ganzhi,
            yingqi_year=int(c["yingqi_year"]),
            statement=str(c.get("statement", "")),
            confidence_star=int(conf.get("star", 0)),
            confidence_percent=int(round(float(conf.get("percent", 0)) * 100)),
            schools=list(c.get("contributing_schools", [])),
            domain=c.get("domain"),
            falsifiable=str(c.get("falsifiable", "")),
            source="analysis_output",
        ))

    # 次级：直接 gate_results 里 ★★★★+
    for g in data.get("gate_results", []) or []:
        conf = g.get("confidence") or {}
        if int(conf.get("star", 0)) < 4:
            continue
        out.append(PredictionDraft(
            case_id=case_id,
            case_ganzhi=ganzhi,
            yingqi_year=int(g["year"]),
            statement=f"{g.get('candidate_event','')}（{g.get('domain','')}）",
            confidence_star=int(conf.get("star", 0)),
            confidence_percent=int(round(float(conf.get("percent", 0)) * 100)),
            schools=["任"],
            domain=g.get("domain"),
            falsifiable=f"若 {g['year']} 年内未发生 {g.get('candidate_event','')} → 失验",
            source="analysis_output",
        ))
    return out


# ============================================================
# 四、抽取：report.md 启发式（fallback）
# ============================================================

# 匹配 ★★★★ (XX%) 或 ★★★★★ (XX%) 的可信度
_CONFIDENCE_RE = re.compile(r"★(?P<stars>★{3,4})\s*\((?P<pct>\d{1,3})%\)")
# 4 位年（19xx / 20xx / 21xx）
_YEAR_RE = re.compile(r"\b(19|20|21)\d{2}\b")


def extract_from_report_md(case_dir: pathlib.Path) -> list[PredictionDraft]:
    """从 reports/C-XXX-{干支}-report.md 启发式抽取。

    扫每一行，若同时含有 ★★★★+ 与 4 位年份 → 视为应期断语。
    """
    out: list[PredictionDraft] = []
    case_id = case_dir.name
    plain, ganzhi = parse_case_id(case_id)

    # 报告路径
    report_candidates = [
        REPORTS_DIR / f"{case_id}-report.md",
        REPORTS_DIR / f"{plain}-report.md",
    ]
    report_path: Optional[pathlib.Path] = None
    for p in report_candidates:
        if p.exists():
            report_path = p
            break
    # 兜底：报告可能用旧 v1.0 文件名
    if report_path is None:
        prefix = case_id.split("-", 3)[:3]
        prefix_plain = "-".join(prefix)
        for p in REPORTS_DIR.glob(f"{prefix_plain}*-report.md"):
            report_path = p
            break
    if report_path is None:
        return out

    # 读 analysis.md 也作为补充（v1.0 报告 + analysis 都可能含应期表）
    sources = [report_path]
    analysis = case_dir / "analysis.md"
    if analysis.exists():
        sources.append(analysis)

    seen: set[str] = set()
    for src in sources:
        text = src.read_text(encoding="utf-8")
        for line in text.splitlines():
            mc = _CONFIDENCE_RE.search(line)
            if not mc:
                continue
            star_count = len(mc.group("stars")) + 1  # group 不含第一颗 ★
            # _CONFIDENCE_RE 设计为后续 3-4 颗 ★，加上初始一颗 = 4 或 5
            if star_count < 4:
                continue
            try:
                pct = int(mc.group("pct"))
            except ValueError:
                continue

            year_match = _YEAR_RE.search(line)
            if not year_match:
                continue
            year = int(year_match.group())
            # 略过过去太久（> 100 年前）的离群值
            now = _dt.date.today().year
            if year < now - 100 or year > now + 100:
                continue

            # 建 statement = 整行去 markdown 修饰
            stmt = re.sub(r"[\|*`>]+", " ", line).strip()
            stmt = re.sub(r"\s{2,}", " ", stmt)
            if len(stmt) > 200:
                stmt = stmt[:200] + "..."

            # 从行内抽 schools / domain
            schools = [s for s in ("段", "杨", "高", "任") if s in line]
            domain = None
            for kw, dom in (
                ("婚姻", "婚姻"), ("婚", "婚姻"), ("夫", "婚姻"), ("妻", "婚姻"),
                ("学历", "学业"), ("学业", "学业"), ("高考", "学业"),
                ("财", "财运"), ("收入", "财运"),
                ("健康", "健康"), ("外伤", "健康"),
                ("事业", "事业"), ("职业", "事业"), ("升迁", "事业"),
                ("六亲", "六亲"), ("母", "六亲"), ("父", "六亲"),
            ):
                if kw in line:
                    domain = dom
                    break

            falsifiable = f"若 {year} 年内未发生 {domain or '所述事件'} → 失验"

            draft = PredictionDraft(
                case_id=case_id,
                case_ganzhi=ganzhi,
                yingqi_year=year,
                statement=stmt,
                confidence_star=star_count,
                confidence_percent=pct,
                schools=schools,
                domain=domain,
                falsifiable=falsifiable,
                source="report",
                raw_line=line.strip(),
            )
            fp = draft.fingerprint()
            if fp in seen:
                continue
            seen.add(fp)
            out.append(draft)
    return out


# ============================================================
# 五、序列号分配（每年 NNN）
# ============================================================

_FILENAME_RE = re.compile(
    r"^PRED-(?P<year>\d{4})-(?P<seq>\d{3})-"
)


def _next_seq_for_year(year: int) -> int:
    """扫 predictions/ 目录里同年最大序号 + 1。"""
    if not PREDICTIONS_DIR.exists():
        return 1
    max_seq = 0
    for p in PREDICTIONS_DIR.iterdir():
        m = _FILENAME_RE.match(p.name)
        if m and int(m.group("year")) == year:
            max_seq = max(max_seq, int(m.group("seq")))
    return max_seq + 1


# ============================================================
# 六、写盘
# ============================================================

def _draft_to_markdown(d: PredictionDraft, *, seq: int) -> str:
    """生成 PRED-*.md 内容（带 frontmatter）。"""
    today = _dt.date.today().isoformat()
    fm: dict[str, Any] = {
        "schema_version": "1.2.0",
        "case_id": d.case_id,
        "case_ganzhi": d.case_ganzhi,
        "yingqi_year": d.yingqi_year,
        "domain": d.domain or "未分类",
        "schools": d.schools,
        "confidence": {
            "star": d.confidence_star,
            "percent": d.confidence_percent,
        },
        "falsifiable": d.falsifiable,
        "status": "pending",
        "extracted_at": today,
        "extracted_from": d.source,
        "fingerprint": d.fingerprint(),
        "seq": seq,
    }

    body: list[str] = []
    body.append("---")
    import yaml as _yaml
    body.append(_yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).rstrip())
    body.append("---")
    body.append("")
    body.append(f"# PRED · {d.yingqi_year} · {d.domain or '应期'}")
    body.append("")
    body.append(f"> 由 `tools/extract_predictions.py` 自动从 {d.source} 抽取。")
    body.append(f"> case: `{d.case_id}`")
    body.append("")
    body.append("## 断语")
    body.append("")
    body.append(d.statement)
    body.append("")
    body.append("## 置信度")
    body.append("")
    body.append(f"- ★ `{d.confidence_star}` / 5")
    body.append(f"- percent `{d.confidence_percent}%`")
    body.append(f"- 派别签名: {' + '.join(d.schools) if d.schools else '(未识别)'}")
    body.append("")
    body.append("## 证伪条件")
    body.append("")
    body.append(d.falsifiable)
    body.append("")
    body.append("## 状态")
    body.append("")
    body.append("- 当前: `pending`")
    body.append(f"- 应期年: {d.yingqi_year}")
    body.append("")
    body.append("---")
    body.append("")
    body.append("> 命主反馈到位后由 `tools/feedback_loop.ingest_feedback()`")
    body.append("> 标记 verified / falsified 并回填 hits/misses。")
    if d.raw_line:
        body.append("")
        body.append("```")
        body.append(d.raw_line)
        body.append("```")
    return "\n".join(body) + "\n"


def write_prediction(d: PredictionDraft) -> Optional[pathlib.Path]:
    """写一个 PRED 文件；若已存在同指纹则跳过返回 None。"""
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    plain, _ganzhi = parse_case_id(d.case_id)
    fp = d.fingerprint()
    # 判重：扫现有同 case + 同应期年 + 同指纹
    for existing in PREDICTIONS_DIR.glob(f"PRED-*-{plain}-*.md"):
        text = existing.read_text(encoding="utf-8", errors="ignore")
        if fp in text:
            return None
    seq = _next_seq_for_year(d.yingqi_year)
    event = d.event_slug()
    fname = (
        f"PRED-{d.yingqi_year}-{seq:03d}-{plain}-{d.case_ganzhi}-{event}.md"
    )
    path = PREDICTIONS_DIR / fname
    path.write_text(_draft_to_markdown(d, seq=seq), encoding="utf-8")
    return path


# ============================================================
# 七、入口
# ============================================================

def extract_for_case(case_id: str) -> list[pathlib.Path]:
    """对单个 case 抽取并落盘。返回新写入的文件列表。"""
    case_dir = REPO_ROOT / "cases" / case_id
    if not case_dir.exists():
        # 模糊
        for p in CASES_DIR.iterdir():
            if p.name.startswith(case_id):
                case_dir = p
                break
    if not case_dir.exists():
        raise FileNotFoundError(f"case 目录不存在: {case_id}")

    drafts = extract_from_analysis_output(case_dir)
    if not drafts:
        drafts = extract_from_report_md(case_dir)

    written: list[pathlib.Path] = []
    for d in drafts:
        p = write_prediction(d)
        if p:
            written.append(p)
    return written


def extract_all() -> dict[str, list[pathlib.Path]]:
    """对 cases/ 下全部 case 抽取。"""
    out: dict[str, list[pathlib.Path]] = {}
    for cd in list_case_dirs():
        try:
            out[cd.name] = extract_for_case(cd.name)
        except FileNotFoundError:
            continue
    return out


# ============================================================
# smoke / CLI
# ============================================================

def _smoke() -> None:
    drafts = extract_from_report_md(CASES_DIR / "C-2026-001-庚申戊寅壬子辛丑")
    print(f"[draft count] C-2026-001: {len(drafts)}")
    for d in drafts[:5]:
        print(
            f"  - {d.yingqi_year} ★{d.confidence_star} ({d.confidence_percent}%) "
            f"[{d.domain}] {d.schools}: {d.statement[:60]}..."
        )
    print(f"\n=== extract_predictions.smoke 完成 ===")


if __name__ == "__main__":  # pragma: no cover
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "all":
            res = extract_all()
            for cid, paths in res.items():
                print(f"{cid}: {len(paths)} prediction(s) written")
        else:
            res = extract_for_case(sys.argv[1])
            for p in res:
                print(p)
    else:
        _smoke()
