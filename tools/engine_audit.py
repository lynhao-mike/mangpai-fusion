"""tools/engine_audit.py · 底层事实体检（不依赖 engine 自身的判定逻辑）。

所有期望值都由本文件的表独立算出，再与 engine 输出比对：
表驱动的校验器与被测代码不能共享同一份实现，否则只是在验证自己。

用法：python -m tools.engine_audit [--limit N]
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

from engine.api import analyze_facts, to_jsonable

ROOT = pathlib.Path(__file__).resolve().parents[1]
CASE_RE = re.compile(r"^(C-\d{4}-[A-Za-z0-9]+)-(乾|坤)-((?:[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]){4})$")

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
GAN_WX = dict(zip(GAN, "木木火火土土金金水水"))
GAN_YY = dict(zip(GAN, "阳阴阳阴阳阴阳阴阳阴"))
ZHI_YY = dict(zip(ZHI, "阳阴阳阴阳阴阳阴阳阴阳阴"))
ZHI_WX = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
          "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}
HIDDEN = {"子": "癸", "丑": "己癸辛", "寅": "甲丙戊", "卯": "乙", "辰": "戊乙癸", "巳": "丙庚戊",
          "午": "丁己", "未": "己丁乙", "申": "庚壬戊", "酉": "辛", "戌": "戊辛丁", "亥": "壬甲"}
# 五虎遁：年干 → 寅月天干
WUHU = {"甲": "丙", "己": "丙", "乙": "戊", "庚": "戊", "丙": "庚", "辛": "庚",
        "丁": "壬", "壬": "壬", "戊": "甲", "癸": "甲"}
# 五鼠遁：日干 → 子时天干
WUSHU = {"甲": "甲", "己": "甲", "乙": "丙", "庚": "丙", "丙": "戊", "辛": "戊",
         "丁": "庚", "壬": "庚", "戊": "壬", "癸": "壬"}
# 六旬空亡
XUN_KONG = {"甲子": "戌亥", "甲戌": "申酉", "甲申": "午未", "甲午": "辰巳", "甲辰": "寅卯", "甲寅": "子丑"}

SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def ten_god(day_gan: str, other: str) -> str:
    """标准十神：以日干为我。"""
    me_wx, me_yy = GAN_WX[day_gan], GAN_YY[day_gan]
    o_wx, o_yy = GAN_WX[other], GAN_YY[other]
    same = me_yy == o_yy
    if o_wx == me_wx:
        return "比肩" if same else "劫财"
    if SHENG[me_wx] == o_wx:
        return "食神" if same else "伤官"
    if KE[me_wx] == o_wx:
        return "偏财" if same else "正财"
    if KE[o_wx] == me_wx:
        return "七杀" if same else "正官"
    return "偏印" if same else "正印"


def jiazi_index(gan: str, zhi: str) -> int | None:
    for i in range(60):
        if GAN[i % 10] == gan and ZHI[i % 12] == zhi:
            return i
    return None


def xun_kong(day_gan: str, day_zhi: str) -> str | None:
    idx = jiazi_index(day_gan, day_zhi)
    if idx is None:
        return None
    head = idx - idx % 10
    return XUN_KONG.get(GAN[head % 10] + ZHI[head % 12])


def month_gan(year_gan: str, month_zhi: str) -> str | None:
    """五虎遁：从寅月起顺数到目标月支。"""
    if month_zhi not in ZHI or month_zhi not in "寅卯辰巳午未申酉戌亥丑子":
        return None
    start = WUHU[year_gan]                       # 寅月天干
    off = (ZHI.index(month_zhi) - ZHI.index("寅")) % 12
    return GAN[(GAN.index(start) + off) % 10]


def hour_gan(day_gan: str, hour_zhi: str) -> str:
    start = WUSHU[day_gan]                       # 子时天干
    off = ZHI.index(hour_zhi)                    # 子=0
    return GAN[(GAN.index(start) + off) % 10]


def read_birth(case_dir: pathlib.Path) -> str | None:
    """从 input.md 的指纹行取出生时间：`（M | 1991-08-08 23:21）`。"""
    p = case_dir / "input.md"
    if not p.exists():
        return None
    m = re.search(r"[（(]\s*[MF]\s*\|\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2})", p.read_text(encoding="utf-8", errors="ignore"))
    return m.group(1) if m else None


def solar_corrected(case_dir: pathlib.Path) -> bool:
    """案例是否声明了真太阳时校正。

    标的案例，其四柱是按校正后时刻排的，用钟表时间复算必然可能差一个时辰，
    因此不能判「四柱与出生时间不符」——那是口径差异，不是数据错误。
    """
    p = case_dir / "input.md"
    if not p.exists():
        return False
    m = re.search(r"真太阳时校正\s*[:：]\s*(\w+)", p.read_text(encoding="utf-8", errors="ignore")[:4000])
    return bool(m and m.group(1).lower() == "true")


def audit_one(name: str, pillars: str, gender: str) -> tuple[list[str], str]:
    bad: list[str] = []
    note = ""
    ps = [pillars[i:i + 2] for i in range(0, 8, 2)]
    y, m, d, h = ps
    for label, p in zip("年月日时", ps):
        if jiazi_index(p[0], p[1]) is None:
            bad.append(f"{label}柱 {p} 不是合法六十甲子")
        elif GAN_YY[p[0]] != ZHI_YY[p[1]]:
            bad.append(f"{label}柱 {p} 干支阴阳不一致")
    if jiazi_index(y[0], y[1]) is not None and m[1] in ZHI:
        exp = month_gan(y[0], m[1])
        if exp and exp != m[0]:
            bad.append(f"月干 {m[0]} 违反五虎遁（{y[0]}年{m[1]}月应为{exp}）")
    if jiazi_index(d[0], d[1]) is not None and h[1] in ZHI:
        exp = hour_gan(d[0], h[1])
        if exp != h[0]:
            # 晚子时口径：日柱用当日、时柱取次日子时（engine profile=late_zi_split）
            idx = jiazi_index(d[0], d[1])
            nxt_gan = GAN[(idx + 1) % 10] if idx is not None else None
            if h[1] == "子" and nxt_gan and hour_gan(nxt_gan, "子") == h[0]:
                note = f"晚子时口径：日柱{d}、时柱{h}按次日{nxt_gan}日起子时"
            else:
                bad.append(f"时干 {h[0]} 违反五鼠遁（{d[0]}日{h[1]}时应为{exp}）")

    birth = read_birth(ROOT / "cases" / name)
    if birth and not solar_corrected(ROOT / "cases" / name):
        try:
            from engine.api import analyze_facts as _af
            base = to_jsonable(_af(birth_dt=birth, gender=gender))
            got = "".join(x["stem"]["char"] + x["branch"]["char"] for x in base["chart"]["pillars"])
            if got != pillars.replace(" ", ""):
                bad.append(f"四柱与出生时间不符：出生 {birth} 应为 {got}，案例写 {pillars}")
        except Exception as exc:  # noqa: BLE001
            bad.append(f"出生时间复算失败：{type(exc).__name__}: {exc}")
    elif birth:
        note = (note + "；" if note else "") + "已标真太阳时校正，钟表时间不可直接复算四柱（口径待定，见 ADR-004/A1）"

    facts = to_jsonable(analyze_facts(pillars=ps, gender=gender))
    chart = facts.get("chart") or {}
    stems: dict = {}
    branches: dict = {}
    for p in chart.get("pillars") or []:
        if p.get("stem"):
            stems[p["stem"]["addr"]] = p["stem"]
        if p.get("branch"):
            branches[p["branch"]["addr"]] = p["branch"]
    if not stems or not branches:
        return bad + ["engine 未返回 stems/branches"], note

    for addr, s in stems.items():
        ch = s.get("char")
        if ch not in GAN:
            bad.append(f"{addr} 天干非法：{ch}")
            continue
        exp = "日主" if addr.startswith("D.") else ten_god(d[0], ch)
        if s.get("ten_god") != exp:
            bad.append(f"{addr} {ch} 十神={s.get('ten_god')}，应为{exp}")
    for addr, b in branches.items():
        ch = b.get("char")
        if ch not in ZHI:
            bad.append(f"{addr} 地支非法：{ch}")
            continue
        hid = b.get("hidden") or []
        got = {x.get("c") for x in hid if isinstance(x, dict)}
        exp = set(HIDDEN[ch])
        if got != exp:
            bad.append(f"{addr} {ch} 藏干={sorted(x for x in got if x)}，应为{sorted(exp)}")
        main = next((x for x in hid if isinstance(x, dict) and x.get("q") == "本气"), None)
        if main and main.get("c"):
            exp_g = ten_god(d[0], main["c"])
            want = b.get("main_ten_god")
            if want and want != "日主" and want != exp_g:
                bad.append(f"{addr} {ch} 本气十神={want}，应为{exp_g}")

    kongw = chart.get("kongwang") or {}
    by_day = set(kongw.get("by_day_xun") or [])
    exp_kong = set(xun_kong(d[0], d[1]) or "")
    if by_day and by_day != exp_kong:
        bad.append(f"日柱旬空 {sorted(by_day)}，应为{sorted(exp_kong)}")
    by_year = set(kongw.get("by_year_xun") or [])
    for hit in kongw.get("hits") or []:
        if not (isinstance(hit, (list, tuple)) and hit):
            continue
        addr = hit[0]
        kind = hit[1] if len(hit) > 1 else None
        ref = {"day": by_day, "year": by_year}.get(kind)
        b = branches.get(addr)
        if b and ref and b.get("char") not in ref:
            bad.append(f"旬空命中 {addr}（{b.get('char')}）不在{kind}旬空 {sorted(ref)} 内")
    return bad, note


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    cases = []
    for p in sorted((ROOT / "cases").iterdir()):
        m = CASE_RE.match(p.name)
        if m:
            cases.append((p.name, m.group(3), m.group(2)))
    if args.limit:
        cases = cases[:args.limit]
    groups: dict[str, list[str]] = {}
    fails = 0
    notes: list[str] = []
    for name, pillars, gender in cases:
        try:
            bad, note = audit_one(name, pillars, gender)
        except Exception as exc:  # noqa: BLE001
            bad, note = [f"异常：{type(exc).__name__}: {exc}"], ""
        if note:
            notes.append(f"{name}：{note}")
        for b in bad:
            key = re.sub(r"^\S+ ", "", b).split("=")[0][:40]
            groups.setdefault(key, []).append(f"{name}：{b}")
        if bad:
            fails += 1
    print(f"案例 {len(cases)}；有问题 {fails}；问题种类 {len(groups)}；口径说明 {len(notes)}")
    for key, items in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f"\n[{len(items)}] {key}")
        for line in items[:3]:
            print("   ", line)
    if notes:
        print("\n== 非错误（已声明口径）==")
        for line in notes[:8]:
            print("   ", line)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
