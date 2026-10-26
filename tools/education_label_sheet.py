"""tools/education_label_sheet.py · 生成学历人工标注表（T-122）。

只做一件事：把「印星空亡」命中的真实案例里、与学历有关的原文句子摘出来，
排成一张可填的表（A/B/C/D 四档留空），供人工判读。

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
EDU = ("学历", "本科", "大专", "高中", "中专", "技校", "硕士", "研究生", "大学", "读书", "辍学", "小学", "初中")


def sentences(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or not any(w in line for w in EDU):
            continue
        for s in re.split(r"(?<=[。；！？])", line):
            s = s.strip()
            if s and any(w in s for w in EDU):
                out.append(s[:120])
    return out


def main() -> None:
    claim = next(c for c in yaml.safe_load(PILOT.read_text(encoding="utf-8"))["claims"]
                 if c["id"] == CLAIM_ID)
    assert compile_claim(claim)["status"] == "compiled", "该断语当前不是 compiled"
    rows, hit_total = [], 0
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
        hit_total += 1
        text = "\n".join(f.read_text(encoding="utf-8", errors="ignore") for f in p.rglob("*.md"))
        ss = sentences(text)
        if not ss:
            continue
        rows.append((p.name, " / ".join(ss[:3])))

    lines = [
        "# 学历人工标注表 v1（T-122）",
        "",
        f"- 断语：`{CLAIM_ID}` 印星空亡 → 学业难成",
        f"- 命中盘：{hit_total} 张；其中有学历相关文字的 {len(rows)} 张",
        "- 档位：A 小学及以下 / B 初高中·技校·中专 / C 大专·本科 / D 研究生及以上",
        "- 口径：以**最高已取得学历**为准；「读书好/聪明」不算；「中专后自考本科」记 C；「初中辍学」记 B。",
        "- 填法：在最后一列写 A/B/C/D；判不了的写 `?` 并在备注写原因。",
        "",
        "| # | 案例 | 相关原文（自动摘录，可能不完整） | 档位 |",
        "|---:|---|---|---|",
    ]
    for i, (case, excerpt) in enumerate(rows, 1):
        lines.append(f"| {i} | `{case}` | {excerpt} |  |")
    lines += ["", "> 自动生成：`python -m tools.education_label_sheet`。摘录仅供定位，判读请打开案例原文。", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"hit={hit_total} rows={len(rows)} -> {OUT}")


if __name__ == "__main__":
    main()
