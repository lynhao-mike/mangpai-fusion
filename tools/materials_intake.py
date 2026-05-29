"""tools/materials_intake.py · 教材入库前置闸门（多派别 Markdown 收件箱）

落地需求：
    新增 sources/inbox/ 作为 Markdown 教材收件箱（多派别）。把投放其中的教材
    校验 → 归档进只读语料库 sources/{school}/ → 在 theory/raw/{school}/extracted/
    生成 S1 抽取记录骨架，从而无缝接入既有的 S1-S5 理论入库管线、四派规律库
    （theory/{school}/index.yaml）与跨流派交叉核验（tools/cross_school_scan.py）。

定位（重要）：
    本工具是入库管线的"前置闸门"，**不自动臆造规律**。它只负责：
      1. 收件箱发现 + front-matter 校验（派别 / 标题 / 来源元数据）
      2. 教材归档进只读语料库 sources/{school}/（已存在则跳过，不覆盖）
      3. 生成 theory/raw/{school}/extracted/ 抽取记录骨架（含来源追溯链 + S2-S5 提示）
      4. 汇总 manifest（成功 / 跳过 / 失败）+ 审计日志
    S1 的规律抽取仍由命理师 + LLM 按 META/ingestion-protocol.md 完成。

架构契约：
    - 派别集合复用 tools/rule_lifecycle.SCHOOL_DIR_MAP / SCHOOL_TO_CN（高/段/杨/任）
    - 入库阶段 S1-S5 见 META/ingestion-protocol.md 与 META/materials-intake-protocol.md
    - 跨流派交叉核验见 tools/cross_school_scan.py + mapping/

dry-run 约定：
    本工具会写入 sources/ 与 theory/，按 tools/README.md dry-run 约定提供 --dry-run。

示例：
    python -m tools.materials_intake --dry-run
    python -m tools.materials_intake
    python -m tools.materials_intake --files sources/inbox/某教材.md
    python -m tools.materials_intake --smoke
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import pathlib
import shutil
import sys
import traceback
from dataclasses import dataclass, field
from typing import Any, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES_DIR = REPO_ROOT / "sources"
INBOX_DIR = SOURCES_DIR / "inbox"
THEORY_RAW_DIR = REPO_ROOT / "theory" / "raw"
META_DIR = REPO_ROOT / "META"
INTAKE_LOG = META_DIR / "materials-intake-log.md"

# 派别标识 → 目录名 / 中文名。优先复用单一信息源 tools/rule_lifecycle；
# 该模块依赖 PyYAML，缺失时回退到本地等价定义，保证本工具可独立运行/自检。
try:  # pragma: no cover - 取决于运行环境是否装了 PyYAML
    from tools.rule_lifecycle import SCHOOL_DIR_MAP, SCHOOL_TO_CN
except Exception:  # noqa: BLE001
    SCHOOL_DIR_MAP = {
        "段": "duan", "杨": "yang", "高": "gao", "任": "ren",
        "duan": "duan", "yang": "yang", "gao": "gao", "ren": "ren",
        # 预留流派
        "预留一": "ext1", "ext1": "ext1",
        "预留二": "ext2", "ext2": "ext2",
    }
    SCHOOL_TO_CN = {
        "duan": "段", "yang": "杨", "gao": "高", "ren": "任",
        "ext1": "预留一", "ext2": "预留二",
    }

# 派别目录 → 规律 ID 字母前缀（见 theory/SCHEMA.md 派别字母前缀表）
SCHOOL_PREFIX: dict[str, str] = {
    "gao": "G", "duan": "D", "yang": "Y", "ren": "R",
    # ── 预留流派（启用时改为真实派名/前缀）─────────────────────
    "ext1": "E", "ext2": "F",
}


# ============================================================
# 一、front-matter 解析
# ============================================================

def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    """解析 Markdown 顶部 `---` 包裹的简单 key: value front-matter。

    刻意只支持平铺 key: value（足够教材元数据），不引入 YAML 依赖。
    支持行内注释（` #` 之后部分丢弃）与首尾引号剥离。

    Returns:
        (meta, body)。无 front-matter 时 meta={}，body=原文。
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text

    end: Optional[int] = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text

    meta: dict[str, str] = {}
    for raw in lines[1:end]:
        s = raw.strip()
        if not s or s.startswith("#") or ":" not in s:
            continue
        key, _, value = s.partition(":")
        value = value.strip()
        if " #" in value:  # 丢弃行内注释
            value = value.split(" #", 1)[0].strip()
        value = value.strip().strip('"').strip("'")
        meta[key.strip()] = value

    body = "\n".join(lines[end + 1:])
    return meta, body


def _normalize_school(value: str) -> Optional[str]:
    """把 front-matter 的 school 值归一到目录名（gao/duan/yang/ren）。"""
    return SCHOOL_DIR_MAP.get(value.strip()) if value else None


# ============================================================
# 二、收件箱发现
# ============================================================

def discover_inbox(inbox_dir: pathlib.Path = INBOX_DIR) -> list[pathlib.Path]:
    """扫描 sources/inbox/ 找所有候选教材 .md（排除 README.md 与隐藏文件）。"""
    out: list[pathlib.Path] = []
    if not inbox_dir.exists():
        return out
    for child in sorted(inbox_dir.iterdir()):
        if not child.is_file() or child.suffix != ".md":
            continue
        if child.name == "README.md" or child.name.startswith("."):
            continue
        out.append(child)
    return out


# ============================================================
# 三、抽取记录骨架
# ============================================================

def _extraction_record_name(school_dir: str, chapter: str, date: str) -> str:
    cn = SCHOOL_TO_CN.get(school_dir, school_dir)
    safe_chapter = chapter.strip().replace("/", "_") or "未命名篇章"
    return f"{cn}派_{safe_chapter}_候选规律提取_{date}.md"


def _build_extraction_skeleton(
    *,
    school_dir: str,
    archived_rel: str,
    title: str,
    edition: str,
    pages: str,
    topic_hint: str,
    source_note: str,
    date: str,
) -> str:
    cn = SCHOOL_TO_CN.get(school_dir, school_dir)
    prefix = SCHOOL_PREFIX.get(school_dir, "X")
    id_topic = (topic_hint or "TOPIC").strip().upper()  # ID 中 topic 段为大写
    version_bits = [edition or "—"]
    if source_note:
        version_bits.append(source_note)
    if pages:
        version_bits.append(f"{pages} 页")
    version_line = " · ".join(version_bits)
    topic_line = topic_hint or "（待 S2 归类，取值见 theory/SCHEMA.md §二 topic 枚举）"

    return f"""# {cn}派《{title}》候选规律提取报告（骨架 · 待抽取）

> **来源文档**：`{archived_rel}`
> **原文版本**：{version_line}
> **主题预判**：{topic_line}
> **提取人**：（待填 · 命理师 / blind-bazi-analyst skill）
> **提取日期**：{date}
> **协议版本**：META/ingestion-protocol.md S1（抽取）+ META/materials-intake-protocol.md
> **审阅状态**：⏸ 待抽取 + 人审 + 案例验证

> 本文件由 `tools/materials_intake.py` 生成骨架。请按 S1 把散文规律填入下表，
> 一条规律 = 一个独立逻辑单元（不合并、不拆分歧义），保留原文锚点。

---

## 一、源文档结构概览

（待填：分课 / 分章节，列出每章核心命题。）

| # | 章节 | 核心命题 |
|---|---|---|
|   |      |          |

---

## 二、候选规律抽取（`{prefix}-{{TOPIC}}-NN` 编号）

> ID 命名规则见 theory/SCHEMA.md §四：`{{派别字母}}-{{TOPIC}}-{{序号}}`。
> 本派字母前缀 = `{prefix}`；`TOPIC` 取 theory/SCHEMA.md §二枚举的**大写**形式（如 LIFA / GEJU / HUNYIN）。

| 编号 | 候选规律内容 | 原文锚点 | 拟入模块 | 候选等级 |
|---|---|---|---|---|
| `{prefix}-{id_topic}-01` |  |  |  | 0.6 |

---

## 三、入库提示（S2–S5 + 跨流派交叉核验）

- **S2 归一**：写入 `theory/{school_dir}/*.yaml`，ID 前缀 `{prefix}-`，字段见 `theory/SCHEMA.md`。
- **S3 打分**：按 `engine/confidence.yaml` 计算 `static` 静态分；初始 `status: candidate`。
- **S4 跨派对照**：在 `mapping/{{consensus,complementary,exclusive,conflicts}}.md` 登记同向 / 冲突关系。
- **S5 入库**：git commit + 更新 `META/rule-changelog.md` 与 `META/source-trace.md`。
- **跨流派交叉核验**：积累案例反馈后运行 `python -m tools.cross_school_scan` 检测派别系统性偏差。
"""


# ============================================================
# 四、单份教材处理
# ============================================================

@dataclass
class MaterialResult:
    source_path: pathlib.Path
    school: Optional[str] = None
    title: Optional[str] = None
    archived_path: Optional[pathlib.Path] = None
    extraction_record: Optional[pathlib.Path] = None
    success: bool = False
    skipped: bool = False
    skip_reason: str = ""
    error_step: str = ""          # frontmatter / school / archive / skeleton
    error_message: str = ""
    error_traceback: str = ""
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": str(self.source_path),
            "school": self.school,
            "title": self.title,
            "archived_path": str(self.archived_path) if self.archived_path else None,
            "extraction_record": str(self.extraction_record) if self.extraction_record else None,
            "success": self.success,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
            "error_step": self.error_step,
            "error_message": self.error_message,
            "warnings": self.warnings,
        }


def _process_single(
    material_path: pathlib.Path,
    *,
    dry_run: bool,
    sources_root: pathlib.Path,
    raw_root: pathlib.Path,
    date: str,
) -> MaterialResult:
    result = MaterialResult(source_path=material_path)

    # ── Step 1: 读取 + front-matter ──────────────────────────
    try:
        text = material_path.read_text(encoding="utf-8")
        meta, _ = parse_front_matter(text)
    except Exception as exc:  # noqa: BLE001
        result.error_step = "frontmatter"
        result.error_message = str(exc)
        result.error_traceback = traceback.format_exc()
        return result

    # ── Step 2: 校验派别 ─────────────────────────────────────
    school = _normalize_school(meta.get("school", ""))
    if school is None:
        result.error_step = "school"
        result.error_message = (
            f"未知或缺失派别 school={meta.get('school', '<空>')!r}；"
            f"应为 {sorted(set(SCHOOL_DIR_MAP.values()))} 之一（或对应中文 高/段/杨/任）"
        )
        return result
    result.school = school

    # ── Step 3: 标题（缺失则回退文件名）─────────────────────
    title = meta.get("title", "").strip()
    if not title:
        title = material_path.stem
        result.warnings.append(f"front-matter 缺 title，回退用文件名 {title!r}")
    result.title = title

    # ── Step 4: 归档进 sources/{school}/ ────────────────────
    school_src_dir = sources_root / school
    dest = school_src_dir / material_path.name
    archived_rel = f"sources/{school}/{material_path.name}"
    if dest.exists():
        result.skipped = True
        result.skip_reason = f"目标已存在，不覆盖只读语料：{archived_rel}"
        return result

    if not dry_run:
        try:
            school_src_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(material_path), str(dest))
        except Exception as exc:  # noqa: BLE001
            result.error_step = "archive"
            result.error_message = str(exc)
            result.error_traceback = traceback.format_exc()
            return result
    result.archived_path = dest

    # ── Step 5: 生成抽取记录骨架 ────────────────────────────
    extracted_dir = raw_root / school / "extracted"
    record_name = _extraction_record_name(school, title, date)
    record_path = extracted_dir / record_name
    result.extraction_record = record_path

    if record_path.exists():
        result.warnings.append(f"抽取记录已存在，跳过生成：{record_name}")
        result.success = True
        return result

    if not dry_run:
        try:
            extracted_dir.mkdir(parents=True, exist_ok=True)
            skeleton = _build_extraction_skeleton(
                school_dir=school,
                archived_rel=archived_rel,
                title=title,
                edition=meta.get("edition", "").strip(),
                pages=meta.get("pages", "").strip(),
                topic_hint=meta.get("topic_hint", "").strip(),
                source_note=meta.get("source_note", "").strip(),
                date=date,
            )
            record_path.write_text(skeleton, encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            result.error_step = "skeleton"
            result.error_message = str(exc)
            result.error_traceback = traceback.format_exc()
            return result

    result.success = True
    return result


# ============================================================
# 五、批次入口
# ============================================================

@dataclass
class IntakeReport:
    started_at: str = ""
    finished_at: str = ""
    dry_run: bool = False
    materials: list[MaterialResult] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return sum(1 for m in self.materials if m.success and not m.skipped)

    @property
    def failure_count(self) -> int:
        return sum(1 for m in self.materials if not m.success and not m.skipped)

    @property
    def skip_count(self) -> int:
        return sum(1 for m in self.materials if m.skipped)

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "dry_run": self.dry_run,
            "totals": {
                "input": len(self.materials),
                "success": self.success_count,
                "failure": self.failure_count,
                "skipped": self.skip_count,
            },
            "materials": [m.to_dict() for m in self.materials],
        }


def intake(
    files: Optional[list[pathlib.Path]] = None,
    *,
    dry_run: bool = False,
    inbox_dir: pathlib.Path = INBOX_DIR,
    sources_root: pathlib.Path = SOURCES_DIR,
    raw_root: pathlib.Path = THEORY_RAW_DIR,
    write_log: bool = True,
) -> IntakeReport:
    """把收件箱教材归档 + 生成抽取记录骨架。

    Args:
        files:        显式文件列表；None → 扫 inbox_dir
        dry_run:      True 则不移文件 / 不写骨架 / 不写日志
        inbox_dir:    收件箱目录（测试可注入）
        sources_root: 语料库根（测试可注入）
        raw_root:     theory/raw 根（测试可注入）
        write_log:    是否追加 META/materials-intake-log.md

    Returns:
        IntakeReport（含每份结果 + 汇总）
    """
    started = _dt.datetime.now().isoformat(timespec="seconds")
    date = _dt.date.today().isoformat()
    inputs = files if files is not None else discover_inbox(inbox_dir)
    report = IntakeReport(started_at=started, dry_run=dry_run)

    for path in inputs:
        report.materials.append(
            _process_single(
                path,
                dry_run=dry_run,
                sources_root=sources_root,
                raw_root=raw_root,
                date=date,
            )
        )

    report.finished_at = _dt.datetime.now().isoformat(timespec="seconds")
    if write_log and not dry_run and report.materials:
        _append_intake_log(report)
    return report


# ============================================================
# 六、审计日志
# ============================================================

def _append_intake_log(report: IntakeReport) -> None:
    """每次正式 intake 追加一段 markdown 摘要到 META/materials-intake-log.md。"""
    META_DIR.mkdir(parents=True, exist_ok=True)
    if not INTAKE_LOG.exists():
        INTAKE_LOG.write_text(
            "# materials-intake-log · 教材入库历史\n\n"
            "> 由 `tools/materials_intake.py` 维护。记录教材归档与抽取记录骨架生成。\n\n",
            encoding="utf-8",
        )

    lines: list[str] = [f"\n## {report.started_at} → {report.finished_at}", ""]
    lines.append(
        f"- 输入: {len(report.materials)} 份"
        f" / 成功: {report.success_count}"
        f" / 失败: {report.failure_count}"
        f" / 跳过: {report.skip_count}"
    )
    lines.append("")
    lines.append("| 教材 | 派别 | 归档 | 抽取记录 | 结果 |")
    lines.append("|---|---|---|---|---|")
    for m in report.materials:
        if m.skipped:
            state = f"⏭️ {m.skip_reason}"
        elif m.success:
            state = "✅" + (f" ⚠️{len(m.warnings)}" if m.warnings else "")
        else:
            state = f"❌ {m.error_step}: {m.error_message[:50]}"
        archived = f"`{m.archived_path.name}`" if m.archived_path else "—"
        record = f"`{m.extraction_record.name}`" if m.extraction_record else "—"
        lines.append(
            f"| `{m.source_path.name}` | {m.school or '—'} | {archived} | {record} | {state} |"
        )

    with INTAKE_LOG.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ============================================================
# 七、自检（smoke）
# ============================================================

def _smoke() -> bool:
    """端到端自检：临时目录里跑一次 intake + 一次 dry-run，全部在 tempdir。"""
    import tempfile

    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        inbox = root / "inbox"
        sources_root = root / "sources"
        raw_root = root / "raw"
        inbox.mkdir(parents=True)

        # 用例 1：带 front-matter 的合法教材 → 应成功归档 + 生成骨架
        good = inbox / "示例理法.md"
        good.write_text(
            "---\nschool: 高\ntitle: 理法测试篇\nedition: 测试班\npages: 9\n"
            "topic_hint: lifa\n---\n\n# 正文\n月令为提纲。\n",
            encoding="utf-8",
        )
        # 用例 2：未知派别 → 应失败（不抛异常，记 error）
        bad = inbox / "未知派.md"
        bad.write_text("---\nschool: 未知\ntitle: x\n---\n正文\n", encoding="utf-8")

        report = intake(
            dry_run=False, inbox_dir=inbox, sources_root=sources_root,
            raw_root=raw_root, write_log=False,
        )

        checks: list[tuple[str, bool]] = [
            ("成功计数=1", report.success_count == 1),
            ("失败计数=1", report.failure_count == 1),
            ("归档到 sources/gao/", (sources_root / "gao" / "示例理法.md").exists()),
            ("inbox 已清出该教材", not good.exists()),
            (
                "抽取记录已生成",
                (raw_root / "gao" / "extracted" / "高派_理法测试篇_候选规律提取_"
                 f"{_dt.date.today().isoformat()}.md").exists(),
            ),
        ]

        # 用例 3：dry-run 不应写盘
        inbox2 = root / "inbox2"
        sources2 = root / "sources2"
        raw2 = root / "raw2"
        inbox2.mkdir()
        dry_md = inbox2 / "dry.md"
        dry_md.write_text("---\nschool: duan\ntitle: 干跑篇\n---\n正文\n", encoding="utf-8")
        dry_report = intake(
            dry_run=True, inbox_dir=inbox2, sources_root=sources2,
            raw_root=raw2, write_log=False,
        )
        checks.append(("dry-run 报告成功=1", dry_report.success_count == 1))
        checks.append(("dry-run 未移动文件", dry_md.exists()))
        checks.append(("dry-run 未写 sources", not (sources2 / "duan").exists()))

        for label, passed in checks:
            print(f"  [{'PASS' if passed else 'FAIL'}] {label}")
            ok = ok and passed

    print(f"\nmaterials_intake smoke: {'PASS' if ok else 'FAIL'}")
    return ok


# ============================================================
# 八、CLI
# ============================================================

def _print_human(report: IntakeReport) -> None:
    print(f"\n[materials_intake] {report.started_at} → {report.finished_at}"
          f" (dry_run={report.dry_run})")
    print(f"  输入: {len(report.materials)} 份"
          f" / ✅ {report.success_count}"
          f" / ❌ {report.failure_count}"
          f" / ⏭️ {report.skip_count}")
    print()
    for m in report.materials:
        if m.skipped:
            print(f"  ⏭️  {m.source_path.name}: {m.skip_reason}")
        elif m.success:
            extra = f" + 抽取骨架 {m.extraction_record.name}" if m.extraction_record else ""
            warn = f"  ⚠️ {'; '.join(m.warnings)}" if m.warnings else ""
            print(f"  ✅ {m.source_path.name} → sources/{m.school}/{extra}{warn}")
        else:
            print(f"  ❌ {m.source_path.name}: [{m.error_step}] {m.error_message}")
    if report.failure_count == 0 and report.success_count and not report.dry_run:
        print("\n  下一步：按 META/materials-intake-protocol.md 完成 S1 抽取 → S2-S5 入库。")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="教材入库前置闸门：扫 sources/inbox/*.md → 归档 sources/{school}/ "
                    "+ 生成 theory/raw/{school}/extracted/ 抽取骨架",
    )
    parser.add_argument("--files", nargs="*", default=None,
                        help="显式指定教材 .md 列表；不指定则扫 sources/inbox/")
    parser.add_argument("--dry-run", action="store_true",
                        help="不移文件 / 不写骨架 / 不写日志")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--smoke", action="store_true", help="跑内置自检后退出")
    args = parser.parse_args(argv)

    if args.smoke:
        return 0 if _smoke() else 1

    files = [pathlib.Path(f) for f in args.files] if args.files else None
    report = intake(files=files, dry_run=args.dry_run)

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        _print_human(report)
    return 0 if report.failure_count == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
