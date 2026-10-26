"""tools/education_label_sheet.py · 生成学历人工标注表（T-122）。

只读 cases/<case>/feedback.md（命主自述 / 核验材料），不读 analysis.md、findings 等 AI 产物，
避免用模型自己的推断去当标签。表格里所有 `|` 都会被替换，防止破坏 Markdown 表格。

用法：python -m tools.education_label_sheet
输出：META/education-label-sheet-v1.md
"""
from __future__ import annotations

import pathlib
import re

import yaml

from engine.api import analyze_facts, to_jsonable
from engine.claims.condition_ir import build_context, compile_claim, evaluate_claim

ROOT = pathlib.Path(__file__).resolve().parents[1]
PILOT = ROOT / "theory" / "claims" / "conditions-v2" / "pilot-20.yaml"
OUT = ROOT / "META" / "education-label-sheet-v1.md"
CLAIM_ID = "G-SP-165"
CASE_RE = re.compile(r"^(C-\d{4}-[A-Za-z0-9]+)-(乾|坤)-((?:[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]){4})$")

# 真正能判档位的表述（不含「读书好」这类形容词）
GRADE_WORDS = ("小学", "初中", "高中", "中专", "技校", "职高", "大专", "专科", "本科", "硕士",
               "研究生", "博士", "大学", "辍学", "学历", "自考", "专升本", "考研")
# 具体事实动词：出现才算「说清了学历」
FACT_WORDS = ("毕业", "在读", "考上", "读完", "读到", "就读", "辍学", "退学", "录取", "学历",
              "本科", "大专", "专科", "中专", "技校", "研究生", "硕士", "博士", "大学")
# AI 推断信号：出现即丢弃，避免拿模型的结论当标签
AI_SIGNALS = ("报告结论", "原判", "待精确确认", "REVISE", "推断", "大概率", "待核验", "原分析",
              "预测", "待补", "核验", "问题", "清单", "？", "?",
              "信息不足", "提前启动", "反馈：[", "待确认", "未提供")


def clean(text: str, limit: int = 160) -> str:
    text = re.sub(r"\s+", " ", text.replace("|", "｜").replace("\n", " ")).strip()
    return text[:limit]


def excerpts(feedback: pathlib.Path) -> list[str]:
    if not feedback.exists():
        return []
    text = feedback.read_text(encoding="utf-8", errors="ignore")
    out: list[str] = []
    for line in text.splitlines():
        if not any(w in line for w in GRADE_WORDS):
            continue
        if line.strip().startswith("#"):          # 标题行不算证据
            continue
        if any(s in line for s in AI_SIGNALS):    # 只要自述，不要 AI 推断
            continue
        for seg in re.split(r"(?<=[。；！？])", line):
            seg = seg.strip(" ｜|\t")
            if not any(w in seg for w in GRADE_WORDS):
                continue
            if not any(w in seg for w in FACT_WORDS):
                continue
            if any(s in seg for s in AI_SIGNALS):
                continue
            # 去掉表格里的空单元格与序号
            seg = re.sub(r"(｜\s*)+", "｜", seg)
            if len(seg) < 6:
                continue
            out.append(clean(seg))
    # 去重、保序
    seen, uniq = set(), []
    for s in out:
        if s and s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq[:2]


def main() -> None:
    claim = next(c for c in yaml.safe_load(PILOT.read_text(encoding="utf-8"))["claims"]
                 if c["id"] == CLAIM_ID)
    assert compile_claim(claim)["status"] == "compiled", "该断语当前不是 compiled"
    rows, hit, no_text = [], 0, []
    for p in sorted((ROOT / "cases").iterdir()):
        m = CASE_RE.match(p.name)
        if not m:
            continue
        pillars = [m.group(3)[i:i + 2] for i in range(0, 8, 2)]
        try:
            ctx = build_context(to_jsonable(analyze_facts(pillars=pillars, gender=m.group(2))))
        except Exception:  # noqa: BLE001
            continue
        if evaluate_claim(claim, ctx)["state"] != "candidate":
            continue
        hit += 1
        ex = excerpts(p / "feedback.md")
        if ex:
            rows.append((p.name, " ／ ".join(ex)))
        else:
            no_text.append(p.name)

    lines = [
        "# 学历标注表 v1（T-122）",
        "",
        f"断语：**「印星空亡 → 学业难成」**（`{CLAIM_ID}`，高德臣·神煞篇）",
        f"命中盘 {hit} 张，其中 **{len(rows)} 张的 feedback.md 里有学历相关自述**，另外 {len(no_text)} 张没有，未列入下表。",
        "",
        "## 为什么填这张表",
        "",
        "这是第一次拿真实案例检验一条断语。没有真实学历结局，就只能统计「命中多少张盘」，",
        "不能回答「命中的人是不是真的学历低」。填完才能算：命中组 vs 未命中组的学历差异。",
        "",
        "## 怎么填（只看命主自己说的话）",
        "",
        "1. 打开最后一列给的原文，判断这个人的**最高已取得学历**；",
        "2. 在「档位」列写一个字母：**A** 小学及以下 / **B** 初高中·技校·中专 / **C** 大专·本科 / **D** 研究生及以上；",
        "3. 原文没提学历、或只写「读书好」「学习一般」→ 写 `?`，不要猜。",
        "",
        "> 只采信 feedback.md 里命主自述或核验材料；**不要**参考 analysis.md 里 AI 的「学历判定」，那会变成自己验证自己。",
        "",
        "| # | 案例 | 命主原话（feedback.md 摘录） | 档位 |",
        "|---:|---|---|:---:|",
    ]
    for i, (case, ex) in enumerate(rows, 1):
        lines.append(f"| {i} | `{case}` | {ex} |  |")
    if no_text:
        lines += ["", f"## 未列入的 {len(no_text)} 张（feedback.md 无学历表述）", ""]
        lines += [f"- `{c}`" for c in no_text]
    lines += ["", "> 自动生成：`python -m tools.education_label_sheet`。若某行摘录对不上原文，以 `cases/<案例>/feedback.md` 为准。", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"hit={hit} labelled_rows={len(rows)} no_text={len(no_text)} -> {OUT}")


if __name__ == "__main__":
    main()
