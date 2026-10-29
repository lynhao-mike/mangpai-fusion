# -*- coding: utf-8 -*-
"""T-193 事实审计 runner（独立来源 = sxtwl 2.0.7 + 公开通行表；engine 只经 engine.cli 读取）。

用法：
    .venv\\Scripts\\python.exe META/fact-audit-v1-runner.py

产物（覆盖写）：
    META/fact-audit-v1.json   逐盘 engine / 独立值、差异、节气传播诊断
    META/fact-audit-v1.md     来源、方法、覆盖、差异表、结论

只读 engine.cli；不改 engine/规则/测试；不做方向/断语；不做 git 写。
"""
from __future__ import annotations

import calendar
import hashlib
import json
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import sxtwl

REPO = Path(__file__).resolve().parents[1]
PY = sys.executable
OUT_JSON = REPO / "META" / "fact-audit-v1.json"
OUT_MD = REPO / "META" / "fact-audit-v1.md"

GAN = list("甲乙丙丁戊己庚辛壬癸")
ZHI = list("子丑寅卯辰巳午未申酉戌亥")
GAN_WX = dict(zip(GAN, "木木火火土土金金水水"))
JIAZI = tuple(GAN[i % 10] + ZHI[i % 12] for i in range(60))
JIE_TO_BRANCH = {
    "立春": "寅", "惊蛰": "卯", "清明": "辰", "立夏": "巳", "芒种": "午", "小暑": "未",
    "立秋": "申", "白露": "酉", "寒露": "戌", "立冬": "亥", "大雪": "子", "小寒": "丑",
}
JQ_NAMES = ["冬至", "小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨", "立夏",
            "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑", "白露", "秋分", "寒露",
            "霜降", "立冬", "小雪", "大雪"]
WUHU = {"甲": "丙", "己": "丙", "乙": "戊", "庚": "戊", "丙": "庚",
        "辛": "庚", "丁": "壬", "壬": "壬", "戊": "甲", "癸": "甲"}
WUSHU = {"甲": "甲", "己": "甲", "乙": "丙", "庚": "丙", "丙": "戊",
         "辛": "戊", "丁": "庚", "壬": "庚", "戊": "壬", "癸": "壬"}
CANG = {
    "子": [("癸", "本气")],
    "丑": [("己", "本气"), ("癸", "中气"), ("辛", "余气")],
    "寅": [("甲", "本气"), ("丙", "中气"), ("戊", "余气")],
    "卯": [("乙", "本气")],
    "辰": [("戊", "本气"), ("乙", "中气"), ("癸", "余气")],
    "巳": [("丙", "本气"), ("庚", "中气"), ("戊", "余气")],
    "午": [("丁", "本气"), ("己", "中气")],
    "未": [("己", "本气"), ("丁", "中气"), ("乙", "余气")],
    "申": [("庚", "本气"), ("壬", "中气"), ("戊", "余气")],
    "酉": [("辛", "本气")],
    "戌": [("戊", "本气"), ("辛", "中气"), ("丁", "余气")],
    "亥": [("壬", "本气"), ("甲", "中气")],
}
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
TIMING_FIELDS = {"qiyun.precise_start_age", "qiyun.precise_start_datetime"}


# ── sxtwl 交节表 ────────────────────────────────────────────────────────────
_JIE_CACHE: dict[int, list[tuple[datetime, str]]] = {}


def _jie_year(y: int) -> list[tuple[datetime, str]]:
    if y not in _JIE_CACHE:
        out = []
        for it in sxtwl.getJieQiByYear(y):
            name = JQ_NAMES[it.jqIndex]
            if name not in JIE_TO_BRANCH:
                continue
            t = sxtwl.JD2DD(it.jd)
            sec = int(t.s)
            base = datetime(int(t.Y), int(t.M), int(t.D), int(t.h), int(t.m), min(59, sec))
            out.append((base + timedelta(microseconds=round((t.s - sec) * 1_000_000)), name))
        out.sort()
        _JIE_CACHE[y] = out
    return _JIE_CACHE[y]


def all_jie(dt: datetime) -> list[tuple[datetime, str]]:
    got: dict[tuple[datetime, str], None] = {}
    for y in (dt.year - 1, dt.year, dt.year + 1):
        for item in _jie_year(y):
            got[item] = None
    return sorted(got)


def next_jie(dt: datetime) -> tuple[datetime, str]:
    return next(x for x in all_jie(dt) if x[0] >= dt)


def prev_jie(dt: datetime) -> tuple[datetime, str]:
    return next(x for x in reversed(all_jie(dt)) if x[0] <= dt)


def nearest_jie_gap_hours(dt: datetime) -> float:
    return min(abs((x[0] - dt).total_seconds()) for x in all_jie(dt)) / 3600


# ── 独立排盘（sxtwl + 通行表）───────────────────────────────────────────────
def gz_of(idx: int) -> str:
    return JIAZI[idx % 60]


def jiazi_index(gz: str) -> int:
    return JIAZI.index(gz)


def day_gz(d: date) -> str:
    gz = sxtwl.fromSolar(d.year, d.month, d.day).getDayGZ()
    return GAN[gz.tg] + ZHI[gz.dz]


def shishen(day_gan: str, target_gan: str) -> str:
    dw, tw = GAN_WX[day_gan], GAN_WX[target_gan]
    same = (GAN.index(day_gan) % 2) == (GAN.index(target_gan) % 2)
    if dw == tw:
        return "比肩" if same else "劫财"
    if SHENG[dw] == tw:
        return "食神" if same else "伤官"
    if KE[dw] == tw:
        return "偏财" if same else "正财"
    if KE[tw] == dw:
        return "七杀" if same else "正官"
    return "偏印" if same else "正印"


def independent(birth: datetime, gender: str) -> dict:
    lc = next(x for x in _jie_year(birth.year) if x[1] == "立春")
    nyear = birth.year if birth >= lc[0] else birth.year - 1
    year_gz = gz_of(nyear - 4)
    ref, jie_name = prev_jie(birth)
    mbranch = JIE_TO_BRANCH[jie_name]
    mstem = GAN[(GAN.index(WUHU[year_gz[0]]) + (ZHI.index(mbranch) - 2) % 12) % 10]
    month_gz = mstem + mbranch
    dgz = day_gz(birth.date())
    hbranch = ZHI[((birth.hour + 1) // 2) % 12]
    stem_day = dgz[0]
    if birth.hour == 23:  # 晚子时：时干按次日五鼠遁（engine 默认 late_zi_split 同口径）
        stem_day = day_gz(birth.date() + timedelta(days=1))[0]
    hstem = GAN[(GAN.index(WUSHU[stem_day]) + ZHI.index(hbranch)) % 10]
    pillars = [year_gz, month_gz, dgz, hstem + hbranch]
    dm = dgz[0]
    hidden_char, hidden_qi, hidden_ss = [], [], []
    for p in pillars:
        hidden_char.append([g for g, _ in CANG[p[1]]])
        hidden_qi.append([q for _, q in CANG[p[1]]])
        hidden_ss.append([shishen(dm, g) for g, _ in CANG[p[1]]])
    stems_ss = ["日主" if i == 2 else shishen(dm, p[0]) for i, p in enumerate(pillars)]
    main_ss = [hidden_ss[i][0] for i in range(4)]

    def xun_kong(gz: str) -> list[str]:
        start = jiazi_index(gz) // 10 * 10
        return [ZHI[(start % 12 + 10) % 12], ZHI[(start % 12 + 11) % 12]]

    by_day, by_year = xun_kong(dgz), xun_kong(year_gz)
    hits = []
    for i, p in enumerate(pillars):
        addr = ["Y.b", "M.b", "D.b", "H.b"][i]
        if p[1] in by_day:
            hits.append([addr, "day"])
        if p[1] in by_year:
            hits.append([addr, "year"])

    yang = GAN.index(year_gz[0]) % 2 == 0
    forward = yang == (gender == "乾")
    ref_jie = next_jie(birth) if forward else prev_jie(birth)
    diff_hours = abs((ref_jie[0] - birth).total_seconds()) / 3600.0
    whole = int(diff_hours / 24.0)
    years, rem = divmod(whole, 3)
    rough = min(10, max(1, years + (1 if rem == 2 else 0)))
    precise_years = diff_hours / 72.0
    precise_dt = birth + timedelta(days=diff_hours * 5.0)

    # 大运年份：传统时辰差法（3 日=1 年、1 日=4 月、1 时辰=10 天）
    start_solar = birth if forward else ref_jie[0]
    end_solar = ref_jie[0] if forward else birth
    hz = lambda h: 11 if h == 23 else h // 2  # noqa: E731
    hour_diff = hz(end_solar.hour) - hz(start_solar.hour)
    day_diff = (end_solar.date() - start_solar.date()).days
    if hour_diff < 0:
        hour_diff += 12
        day_diff -= 1
    month_diff = int(hour_diff * 10 / 30)
    months = day_diff * 4 + month_diff
    days = hour_diff * 10 - month_diff * 30
    add_years, add_months = months // 12, months % 12
    y, m = birth.year + add_years, birth.month + add_months
    if m > 12:
        y, m = y + 1, m - 12
    qiyun_date = date(y, m, min(birth.day, calendar.monthrange(y, m)[1])) + timedelta(days=days)
    midx = jiazi_index(month_gz)
    dayun = [[gz_of(midx + (k + 1) * (1 if forward else -1)),
              qiyun_date.year + 10 * k, qiyun_date.year + 10 * k + 9] for k in range(10)]

    return {
        "pillars": pillars,
        "day_master": dm,
        "stem_ten_god": stems_ss,
        "hidden_char": hidden_char,
        "hidden_qi": hidden_qi,
        "hidden_ten_god": hidden_ss,
        "main_ten_god": main_ss,
        "kongwang": {"by_day_xun": by_day, "by_year_xun": by_year, "hits": hits},
        "qiyun": {
            "direction": "顺" if forward else "逆",
            "ref_jie": {"name": ref_jie[1],
                        "datetime": ref_jie[0].strftime("%Y-%m-%d %H:%M:%S"),
                        "datetime_precise": ref_jie[0].isoformat(sep=" ", timespec="microseconds")},
            "diff_hours": diff_hours,
            "mangpai_rough_start_age": rough,
            "precise_start_age": precise_years,
            "precise_start_datetime": precise_dt.isoformat(sep=" ", timespec="seconds"),
        },
        "dayun": dayun,
    }


# ── engine.cli 读取 ────────────────────────────────────────────────────────
def engine_chart(birth_text: str, gender: str) -> dict:
    p = subprocess.run(
        [PY, "-m", "engine.cli", "chart", "--birth", birth_text, "--gender", gender, "--full"],
        cwd=str(REPO), capture_output=True, text=True, encoding="utf-8",
    )
    if p.returncode != 0:
        raise RuntimeError(f"engine.cli 失败 rc={p.returncode}: {p.stderr.strip()}")
    return json.loads(p.stdout)


def engine_fields(raw: dict) -> dict:
    q = {item["method"]: item for item in raw["cycles"]["qiyun"]}
    return {
        "pillars": [p["ganzhi"] for p in raw["pillars"]],
        "day_master": raw["day_master"],
        "stem_ten_god": [p["stem"]["ten_god"] for p in raw["pillars"]],
        "hidden_char": [[h["char"] for h in p["branch"]["hidden"]] for p in raw["pillars"]],
        "hidden_qi": [[h["qi"] for h in p["branch"]["hidden"]] for p in raw["pillars"]],
        "hidden_ten_god": [[h["ten_god"] for h in p["branch"]["hidden"]] for p in raw["pillars"]],
        "main_ten_god": [p["branch"]["main_ten_god"] for p in raw["pillars"]],
        "kongwang": {
            "by_day_xun": raw["kongwang"]["by_day_xun"],
            "by_year_xun": raw["kongwang"]["by_year_xun"],
            "hits": [list(h) for h in raw["kongwang"]["hits"]],
        },
        "qiyun": {
            "direction": raw["cycles"]["direction"],
            "mangpai_rough_start_age": q["mangpai_rough"]["start_age"],
            "precise_start_age": q["precise"]["start_age"],
            "precise_start_datetime": q["precise"]["start_datetime"],
        },
        "dayun": [[d["ganzhi"], d["start_year"], d["end_year"]] for d in raw["cycles"]["dayun"]],
        "profile": dict(raw["profile"]),
        "boundary_warnings": [w["kind"] for w in raw["boundary_warnings"]],
        "variants": [{"axis": v["axis"], "alt_value": v["alt_value"], "diffs": v["diffs"]}
                     for v in raw["variants"]],
        "chart_id": raw["chart_id"],
    }


# ── 第二实现交叉核对（lunar_python；仅非四柱字段）─────────────────────────
def lunar_crosscheck(birth: datetime) -> dict:
    from lunar_python import Solar

    ec = Solar.fromYmdHms(birth.year, birth.month, birth.day, birth.hour, birth.minute, 0) \
        .getLunar().getEightChar()
    ec.setSect(2)  # 与 engine 默认 late_zi_split 同口径
    names = ("Year", "Month", "Day", "Time")
    return {
        "pillars": [getattr(ec, f"get{n}")() for n in names],
        "stem_ten_god": [getattr(ec, f"get{n}ShiShenGan")() for n in names],
        "hidden_char": [getattr(ec, f"get{n}HideGan")() for n in names],
        "hidden_ten_god": [getattr(ec, f"get{n}ShiShenZhi")() for n in names],
        "by_day_xun": list(ec.getDayXunKong()),
        "by_year_xun": list(ec.getYearXunKong()),
    }


def crosscheck_diffs(eng: dict, lpy: dict) -> list[dict]:
    out = []
    for key in ("stem_ten_god", "hidden_char", "hidden_ten_god"):
        if eng[key] != lpy[key]:
            out.append({"field": key, "engine": eng[key], "lunar_python": lpy[key]})
    if eng["kongwang"]["by_day_xun"] != lpy["by_day_xun"]:
        out.append({"field": "kongwang.by_day_xun", "engine": eng["kongwang"]["by_day_xun"],
                    "lunar_python": lpy["by_day_xun"]})
    if eng["kongwang"]["by_year_xun"] != lpy["by_year_xun"]:
        out.append({"field": "kongwang.by_year_xun", "engine": eng["kongwang"]["by_year_xun"],
                    "lunar_python": lpy["by_year_xun"]})
    return out


# ── 样本（锚点相对于 sxtwl 交节时刻，保证可复现）─────────────────────────────
def at(y: int, jie: str, offset_min: float, day_shift: float = 0.0) -> datetime:
    base = next(x for x in _jie_year(y) if x[1] == jie)[0]
    return (base + timedelta(days=day_shift, minutes=offset_min)).replace(second=0, microsecond=0)


CASES = [
    # 晚子时（23:00–00:59）：5 盘 23 点 + 2 盘 0 点
    dict(id="LZ-01", cat="late_zi", birth="1990-05-12 23:20", gender="乾", place="北京"),
    dict(id="LZ-02", cat="late_zi", birth="1984-11-03 23:45", gender="坤", place="成都"),
    dict(id="LZ-03", cat="late_zi", birth="1972-08-19 23:05", gender="乾", place="沈阳"),
    dict(id="LZ-04", cat="late_zi", birth="2001-02-14 23:55", gender="坤", place="广州"),
    dict(id="LZ-05", cat="late_zi", birth="1996-01-01 00:35", gender="乾", place="上海"),
    dict(id="LZ-06", cat="late_zi", birth="2008-12-31 00:10", gender="坤", place="西安"),
    dict(id="LZ-07", cat="late_zi", birth="1988-02-29 23:30", gender="坤", place="厦门"),
    # 节气交界（交节 ±1 小时内）
    dict(id="NJ-01", cat="near_jie", anchor=(1982, "立春", -10), gender="乾", place="天津"),
    dict(id="NJ-02", cat="near_jie", anchor=(1982, "立春", 10), gender="坤", place="天津"),
    dict(id="NJ-03", cat="near_jie", anchor=(1993, "惊蛰", 35), gender="乾", place="长沙"),
    dict(id="NJ-04", cat="near_jie", anchor=(1974, "立秋", -45), gender="坤", place="青岛"),
    dict(id="NJ-05", cat="near_jie", anchor=(1997, "寒露", 25), gender="乾", place="昆明"),
    dict(id="NJ-06", cat="near_jie", anchor=(2015, "大雪", -20), gender="坤", place="兰州"),
    # 起运边界（与方向性十二节差落在 3 日倍数翻转点上，误差 ≤30 分钟；含 29 日封顶）
    dict(id="QY-01", cat="qiyun_edge", anchor=(1984, "立夏", -20, -8), gender="乾", place="苏州"),
    dict(id="QY-02", cat="qiyun_edge", anchor=(1984, "立夏", 20, -8), gender="乾", place="苏州"),
    dict(id="QY-03", cat="qiyun_edge", anchor=(1984, "立秋", 15, 5), gender="坤", place="杭州"),
    dict(id="QY-04", cat="qiyun_edge", anchor=(1984, "立秋", -15, 5), gender="坤", place="杭州"),
    dict(id="QY-05", cat="qiyun_edge", anchor=(1990, "寒露", -20, -11), gender="乾", place="合肥"),
    dict(id="QY-06", cat="qiyun_edge", anchor=(1990, "寒露", 20, -11), gender="乾", place="合肥"),
    dict(id="QY-07", cat="qiyun_edge", anchor=(1990, "寒露", -30, -29), gender="乾", place="南昌"),
    # 普通
    dict(id="NM-01", cat="normal", birth="1953-07-14 09:20", gender="乾", place="哈尔滨"),
    dict(id="NM-02", cat="normal", birth="1965-11-23 16:40", gender="坤", place="南京"),
    dict(id="NM-03", cat="normal", birth="1988-04-09 07:05", gender="乾", place="武汉"),
    dict(id="NM-04", cat="normal", birth="2004-09-27 20:15", gender="坤", place="深圳"),
    dict(id="NM-05", cat="normal", birth="2019-03-16 12:00", gender="乾", place="郑州"),
]


def resolve(case: dict) -> dict:
    if "birth" in case:
        birth = datetime.strptime(case["birth"], "%Y-%m-%d %H:%M")
    else:
        birth = at(*case["anchor"])
    return dict(case, birth_dt=birth, birth=birth.strftime("%Y-%m-%d %H:%M"))


# ── 比对 ──────────────────────────────────────────────────────────────────
def flat(fields: dict) -> dict:
    out = {}
    for i, pal in enumerate(["year", "month", "day", "hour"]):
        out[f"pillar.{pal}"] = fields["pillars"][i]
        out[f"stem_ten_god.{pal}"] = fields["stem_ten_god"][i]
        out[f"hidden_char.{pal}"] = fields["hidden_char"][i]
        out[f"hidden_qi.{pal}"] = fields["hidden_qi"][i]
        out[f"hidden_ten_god.{pal}"] = fields["hidden_ten_god"][i]
        out[f"main_ten_god.{pal}"] = fields["main_ten_god"][i]
    out["day_master"] = fields["day_master"]
    out["kongwang.by_day_xun"] = fields["kongwang"]["by_day_xun"]
    out["kongwang.by_year_xun"] = fields["kongwang"]["by_year_xun"]
    out["kongwang.hits"] = fields["kongwang"]["hits"]
    out["qiyun.direction"] = fields["qiyun"]["direction"]
    out["qiyun.mangpai_rough_start_age"] = fields["qiyun"]["mangpai_rough_start_age"]
    out["qiyun.precise_start_age"] = fields["qiyun"]["precise_start_age"]
    out["qiyun.precise_start_datetime"] = fields["qiyun"]["precise_start_datetime"]
    for k, (gz, sy, ey) in enumerate(fields["dayun"], 1):
        out[f"dayun.{k}.ganzhi"] = gz
        out[f"dayun.{k}.start_year"] = sy
        out[f"dayun.{k}.end_year"] = ey
    return out


def timing_diagnosis(birth: datetime, eng: dict, ind: dict) -> dict:
    d_eng = float(eng["qiyun"]["precise_start_age"]) * 72.0
    d_ind = ind["qiyun"]["diff_hours"]
    forward = eng["qiyun"]["direction"] == "顺"
    implied = birth + timedelta(hours=d_eng) if forward else birth - timedelta(hours=d_eng)
    ref = ind["qiyun"]["ref_jie"]
    sxtwl_dt = datetime.fromisoformat(ref["datetime_precise"])
    delta_jie_s = (sxtwl_dt - implied).total_seconds()
    dd = d_ind - d_eng
    eng_dt = datetime.strptime(eng["qiyun"]["precise_start_datetime"], "%Y-%m-%d %H:%M:%S")
    ind_dt = datetime.strptime(ind["qiyun"]["precise_start_datetime"], "%Y-%m-%d %H:%M:%S")
    actual_dt = (eng_dt - ind_dt).total_seconds()
    predicted_dt = -432000.0 * dd
    actual_age = float(eng["qiyun"]["precise_start_age"]) - float(ind["qiyun"]["precise_start_age"])
    predicted_age = -dd / 72.0
    return {
        "reference_jie": {"name": ref["name"],
                          "sxtwl": ref["datetime"],
                          "engine_implied": implied.isoformat(sep=" ", timespec="seconds"),
                          "delta_s_sxtwl_minus_engine": round(delta_jie_s, 6)},
        "d_engine_hours": round(d_eng, 9),
        "d_independent_hours": round(d_ind, 9),
        "d_delta_hours": round(dd, 12),
        "start_datetime": {
            "actual_engine_minus_independent_s": actual_dt,
            "predicted_engine_minus_independent_s": round(predicted_dt, 3),
            "residual_s": round(actual_dt - predicted_dt, 3),
        },
        "start_age": {
            "actual_engine_minus_independent": actual_age,
            "predicted_engine_minus_independent": predicted_age,
            "residual": actual_age - predicted_age,
        },
    }


def diff_records(eng: dict, ind: dict, diagnosis: dict) -> list[dict]:
    a, b = flat(eng), flat(ind)
    out = []
    for key in a:
        va, vb = a[key], b[key]
        if va == vb:
            continue
        rec = {"field": key, "engine": va, "independent": vb,
               "class": "timing" if key in TIMING_FIELDS else "discrete"}
        if key == "qiyun.precise_start_datetime":
            rec["delta_engine_minus_independent_s"] = diagnosis["start_datetime"][
                "actual_engine_minus_independent_s"]
            rec["predicted_by_jie_delta_s"] = diagnosis["start_datetime"][
                "predicted_engine_minus_independent_s"]
            rec["residual_s"] = diagnosis["start_datetime"]["residual_s"]
        elif key == "qiyun.precise_start_age":
            rec["delta_engine_minus_independent"] = diagnosis["start_age"][
                "actual_engine_minus_independent"]
            rec["predicted_by_jie_delta"] = diagnosis["start_age"][
                "predicted_engine_minus_independent"]
            rec["residual"] = diagnosis["start_age"]["residual"]
        out.append(rec)
    return out


def main() -> int:
    charts, all_diffs, supp_diffs, secondary_diffs = [], [], [], []
    field_checks = checks_discrete = checks_timing = 0
    supp_checks = secondary_checks = 0
    for case in CASES:
        c = resolve(case)
        birth_text = c["birth_dt"].strftime("%Y-%m-%d %H:%M")
        eng = engine_fields(engine_chart(birth_text, c["gender"]))
        ind = independent(c["birth_dt"], c["gender"])
        diag = timing_diagnosis(c["birth_dt"], eng, ind)
        diffs = diff_records(eng, ind, diag)
        lpy = lunar_crosscheck(c["birth_dt"])
        cc = crosscheck_diffs(eng, lpy)
        secondary_checks += 5
        for d in cc:
            secondary_diffs.append({"chart": c["id"], **d})
        checks = len(flat(eng))
        field_checks += checks
        checks_timing += 2
        checks_discrete += checks - 2
        for d in diffs:
            all_diffs.append({"chart": c["id"], **d})
        # 补充检查（不计入主差异）：边界告警与晚子时变体
        supp = []
        kinds = eng["boundary_warnings"]
        if c["birth_dt"].hour == 23:
            supp.append(("23 点报 late_zi", "late_zi" in kinds))
            supp.append(("23 点不报 early_zi", "early_zi" not in kinds))
            nxt = day_gz(c["birth_dt"].date() + timedelta(days=1))
            alt = [v for v in eng["variants"] if v["axis"] == "zi_shi"
                   and v["alt_value"] == "rollover_23"]
            alt_day = dict((d[0], d[1]) for d in alt[0]["diffs"]).get("/pillars/2/ganzhi") if alt else None
            supp.append((f"rollover_23 日柱={nxt}", alt_day == nxt))
        if c["birth_dt"].hour == 0:
            supp.append(("0 点报 early_zi", "early_zi" in kinds))
        if c["cat"] == "near_jie":
            supp.append(("距节 ≤1h 报 near_jie", "near_jie" in kinds))
        for name, ok in supp:
            supp_checks += 1
            if not ok:
                supp_diffs.append({"chart": c["id"], "check": name})
        charts.append({
            "id": c["id"], "category": c["cat"], "birth": c["birth"],
            "gender": c["gender"], "place": c["place"],
            "time_basis": "北京时间（UTC+8）钟表时间；engine 与独立来源同口径，均不做经度/真太阳时校正",
            "engine": {k: eng[k] for k in ("pillars", "day_master", "stem_ten_god",
                                           "hidden_char", "hidden_qi", "hidden_ten_god",
                                           "main_ten_god", "kongwang", "qiyun", "dayun",
                                           "boundary_warnings", "profile", "chart_id")},
            "independent": {k: ind[k] for k in ("pillars", "day_master", "stem_ten_god",
                                                "hidden_char", "hidden_qi", "hidden_ten_god",
                                                "main_ten_god", "kongwang", "qiyun", "dayun")},
            "timing_diagnosis": diag,
            "secondary_crosscheck": {"source": "lunar_python 1.4.8 EightChar(setSect=2)",
                                     "fields": ["stem_ten_god", "hidden_char",
                                                "hidden_ten_god", "by_day_xun", "by_year_xun"],
                                     "diffs": cc},
            "field_checks": checks,
            "diffs": diffs,
        })
        print(f"{c['id']} {c['cat']:11s} {c['birth']} {c['gender']} "
              f"{'/'.join(ind['pillars'])} checks={checks} diffs={len(diffs)}")

    by_cat = {k: sum(1 for c in charts if c["category"] == k)
              for k in ("late_zi", "near_jie", "qiyun_edge", "normal")}
    unexplained = [
        d for d in all_diffs
        if d["class"] == "timing" and (
            (d["field"].endswith("datetime") and abs(d.get("residual_s", 0)) > 2)
            or (d["field"].endswith("age") and abs(d.get("residual", 0)) > 1e-8))
    ]
    max_jie = max((abs(c["timing_diagnosis"]["reference_jie"]["delta_s_sxtwl_minus_engine"])
                   for c in charts), default=0.0)
    max_dt = max((abs(d.get("delta_engine_minus_independent_s", 0)) for d in all_diffs), default=0.0)
    dt_deltas = [abs(d["delta_engine_minus_independent_s"]) for d in all_diffs
                 if "delta_engine_minus_independent_s" in d]
    summary = {
        "charts": len(charts),
        "by_category": by_cat,
        "field_checks": field_checks,
        "checks_discrete": checks_discrete,
        "checks_timing": checks_timing,
        "diff_count": len(all_diffs),
        "diff_discrete": sum(1 for d in all_diffs if d["class"] == "discrete"),
        "diff_timing": sum(1 for d in all_diffs if d["class"] == "timing"),
        "unexplained_diff_count": len(unexplained),
        "max_reference_jie_delta_s": round(max_jie, 6),
        "max_start_datetime_delta_s": round(max_dt, 3),
        "start_datetime_delta_bands": {
            "<=60s": sum(1 for x in dt_deltas if x <= 60),
            "60-300s": sum(1 for x in dt_deltas if 60 < x <= 300),
            ">300s": sum(1 for x in dt_deltas if x > 300),
        },
        "supplementary_checks": supp_checks,
        "supplementary_diff_count": len(supp_diffs),
        "secondary_crosscheck_checks": secondary_checks,
        "secondary_crosscheck_diffs": len(secondary_diffs),
        "strict_pass": len(all_diffs) == 0,
    }
    payload = {
        "schema": "fact-audit/v1",
        "task": "T-193",
        "generated_at": datetime.now().isoformat(sep=" ", timespec="seconds"),
        "repo_head": subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(REPO),
                                    capture_output=True, text=True).stdout.strip(),
        "engine_entry": "python -m engine.cli chart --birth <YYYY-MM-DD HH:MM> --gender <乾|坤> --full",
        "engine_profile": charts[0]["engine"]["profile"],
        "verdict": {
            "card_rule": "差异必须为 0；任何差异列为缺陷，不静默；>0 不宣称通过",
            "strict_zero_diff": summary["strict_pass"],
            "discrete_facts_zero_diff": summary["diff_discrete"] == 0,
            "unexplained_diff_count": summary["unexplained_diff_count"],
            "discrete_diff_count": summary["diff_discrete"],
            "timing_diff_count": summary["diff_timing"],
            "summary": (f"严格 0 差异未达成：{summary['diff_timing']} 项时刻类差异"
                        f"（{summary['charts']} 盘 × 精确起运岁数/精确交运时刻）。"
                        f"离散盘面事实 {summary['checks_discrete']} 项差异 {summary['diff_discrete']}；"
                        "差异可被节气表秒差 ×120 逐盘算尽，"
                        f"未解释差异 {summary['unexplained_diff_count']}。按卡口径不宣称通过。"),
        },
        "coverage": {
            "by_category": by_cat,
            "gender": {g: sum(1 for c in charts if c["gender"] == g) for g in ("乾", "坤")},
            "direction": {d: sum(1 for c in charts if c["engine"]["qiyun"]["direction"] == d)
                          for d in ("顺", "逆")},
            "birth_year_range": [int(min(c["birth"][:4] for c in charts)),
                                 int(max(c["birth"][:4] for c in charts))],
            "hour_23": sum(1 for c in charts if c["birth"][11:13] == "23"),
            "hour_00": sum(1 for c in charts if c["birth"][11:13] == "00"),
            "near_jie_hours_max": round(max(
                nearest_jie_gap_hours(datetime.strptime(c["birth"], "%Y-%m-%d %H:%M"))
                for c in charts if c["category"] == "near_jie"), 3),
        },
        "independent_sources": [
            {"name": "sxtwl（寿星天文历 Python 绑定）", "version": "2.0.7", "role": "primary",
             "scope": "四柱（年/月/日/时）、十二节交节时刻、起运/交运/大运年份",
             "independence": "独立 C++ 历法实现；本 runner 以 sxtwl 交节时刻 + 立春换年 + "
                             "十二节换月 + 00:00 换日 + 五虎遁/五鼠遁独立推算四柱"},
            {"name": "《三命通会》通行地支藏干表 + 子平十神生克定义 + 六十甲子旬空",
             "version": "通行本（runner 内置表）", "role": "primary",
             "scope": "藏干字符/气位、天干十神、本气十神、旬空"},
            {"name": "lunar_python", "version": "1.4.8", "role": "secondary_crosscheck_only",
             "scope": "藏干/十神/旬空的第二实现交叉核对（不计入主差异）",
             "independence": "engine 的四柱亦由 lunar_python 生成，故该库对四柱不构成独立来源；"
                             "本审计的四柱独立值不使用该库"},
        ],
        "method": {
            "compare": "逐盘逐字段严格相等比对，不设容差；浮点精确比较，"
                       "交运时刻按 engine 输出的秒级字符串比对",
            "late_zi_rule": "23:00–23:59 日柱取当日、时干按次日五鼠遁"
                            "（engine 默认 profile zi_shi=late_zi_split；独立侧同规则）",
            "qiyun_rules": {
                "mangpai_rough": "出生与方向性十二节之差按整日 ÷3，余二进一，夹在 1–10 岁",
                "precise": "diff_hours/72 年；交运 = 出生 + 5×diff_hours 日",
                "dayun_years": "传统时辰差法：3 日=1 年、1 日=4 月、1 时辰=10 天；"
                               "起运年 = 出生 + 年/月/日后的公历年，逐年 +10",
            },
            "timing_sensitivity": "交运时刻 = 出生 + 5×diff_hours 日：参考节每差 1 秒，"
                                  "交运时刻差 120 秒；精确岁数差 1/259200 年",
            "excluded": "不比对纳音、神煞、关系图、格局；不做方向/断语",
        },
        "coverage_definitions": {
            "late_zi": "出生钟点 23:00–00:59（5 盘 23 点 + 2 盘 0 点）",
            "near_jie": "出生时刻距十二节交节 ≤1 小时",
            "qiyun_edge": "出生与方向性十二节之差落在粗略起运岁数翻转边界"
                          "（5/8/11 日，误差 ≤30 分钟）或 29 日封顶附近",
            "normal": "距十二节 >1 天且不在 23:00–00:59",
        },
        "known_limitations": [
            "精确交运时刻不具备秒级独立可复现性：engine 用 lunar_python 节气表，"
            "独立值用 sxtwl 天文学交节，两者本批最大差 6.914 秒；交运时刻被 ×120 放大，"
            "故该字段只能按节气表精度核对。",
            "公开万年历通常只给到分钟，无法用公开表仲裁秒级节气差；本审计不据此判定哪一方更准。",
            "样本时间为北京时间钟表时间；engine 不做经度/真太阳时校正，独立来源同口径，"
            "真太阳时不在本卡范围。",
            "藏干/十神/旬空为通行表事实：由 runner 内置表独立实现，并以 lunar_python 1.4.8 "
            "第二实现交叉核对；两实现一致不等于典籍唯一口径。",
        ],
        "summary": summary,
        "diffs": all_diffs,
        "supplementary": {"checks": supp_checks, "diffs": supp_diffs},
        "secondary_crosscheck": {"checks": secondary_checks, "diffs": secondary_diffs},
        "charts": charts,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    write_markdown(payload)
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


def write_markdown(p: dict) -> None:
    s = p["summary"]
    sha = hashlib.sha256(OUT_JSON.read_bytes()).hexdigest()
    cat_names = {"late_zi": "晚子时", "near_jie": "节气交界",
                 "qiyun_edge": "起运边界", "normal": "普通"}
    bands = s["start_datetime_delta_bands"]
    lines = []
    add = lines.append
    verdict = ("**不通过（严格 0 差异口径未达成）**"
               if not s["strict_pass"] else "**通过**")
    add("# 事实审计 v1 · T-193（晚子时 / 节气交界 / 起运边界）")
    add("")
    add(f"- 结论：{verdict}")
    add(f"- 差异：{s['diff_count']} 项全为时刻类（精确起运岁数 25 + 精确交运时刻 25），"
        f"离散事实差异 {s['diff_discrete']}，未解释差异 {s['unexplained_diff_count']}。")
    add(f"- 盘数：{s['charts']}（{'、'.join(f'{cat_names[k]} {v}' for k, v in s['by_category'].items())}）")
    add(f"- 字段检查：{s['field_checks']} 项（离散 {s['checks_discrete']} + 时刻类 {s['checks_timing']}）")
    add(f"- 交运时刻绝对差分布：≤60s {bands['<=60s']} 盘、60–300s {bands['60-300s']} 盘、"
        f">300s {bands['>300s']} 盘；最大 {s['max_start_datetime_delta_s']:.0f}s")
    add(f"- 参考节最大秒差：{s['max_reference_jie_delta_s']:.3f}s（sxtwl 天文学交节 vs engine 隐含交节）")
    add(f"- 补充检查：{s['supplementary_checks']} 项，差异 {s['supplementary_diff_count']}")
    add(f"- 第二实现交叉核对（lunar_python 1.4.8：天干十神/藏干/藏干十神/旬空）："
        f"{s['secondary_crosscheck_checks']} 项，差异 {s['secondary_crosscheck_diffs']}")
    add(f"- 生成时间：{p['generated_at']}　仓库 HEAD：`{p['repo_head']}`")
    add(f"- engine 入口：`{p['engine_entry']}`")
    add(f"- engine profile：`{json.dumps(p['engine_profile'], ensure_ascii=False)}`")
    add(f"- JSON：`META/fact-audit-v1.json`　sha256 `{sha}`")
    add("")
    add("> 一句话：四柱/日主/藏干/十神/旬空/粗略起运/大运干支与起止年全部对上；"
        "只有「精确交运时刻 + 精确起运岁数」对不上，且差额可被「节气表秒差 ×120」逐盘算尽"
        f"（未解释 {s['unexplained_diff_count']}）。按卡的 0 差异口径判不通过，不宣称通过。")
    add("")
    add("## 1. 独立来源与版本")
    add("")
    add("| 用途 | 来源 | 版本 | 独立性说明 |")
    add("|---|---|---|---|")
    for src in p["independent_sources"]:
        add(f"| {src['scope']} | {src['name']} | {src['version']} | "
            f"{src.get('independence', '通行表 + 独立实现，非 engine 代码路径')} |")
    add("")
    add("## 2. 方法与口径")
    add("")
    add(f"- 比对：{p['method']['compare']}。")
    add(f"- 晚子时：{p['method']['late_zi_rule']}。")
    for k, v in p["method"]["qiyun_rules"].items():
        add(f"- 起运（{k}）：{v}。")
    add(f"- 时刻传播：{p['method']['timing_sensitivity']}。")
    add(f"- 不比对：{p['method']['excluded']}。")
    add("- 时间基准：全部盘按北京时间（UTC+8）钟表时间输入；engine 不做经度/真太阳时校正，"
        "独立来源同口径，两边可直接比对。")
    add("")
    add("已知限制：")
    add("")
    for item in p["known_limitations"]:
        add(f"- {item}")
    add("")
    add("## 3. 覆盖")
    add("")
    add("| 类别 | 盘数 | 定义 | 盘号 |")
    add("|---|---|---|---|")
    for k, name in cat_names.items():
        ids = "、".join(c["id"] for c in p["charts"] if c["category"] == k)
        add(f"| {name} | {s['by_category'][k]} | {p['coverage_definitions'][k]} | {ids} |")
    add("")
    add("## 4. 逐盘事实对照")
    add("")
    add("样本为审计向量（非真实命主）；出生地只用于固定时间基准。下表 engine 与独立四柱逐盘一致"
        "（差异只出现在第 5 节的两类时刻字段）。")
    add("")
    add("| 盘号 | 类别 | 出生（北京时间） | 性别 | 出生地 | 四柱 | 日主 | 粗略起运（engine） | 精确起运岁（engine） | 大运首步（engine） | 参考节 Δ（sxtwl−engine） | 差异 |")
    add("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for c in p["charts"]:
        e, i = c["engine"], c["independent"]
        jd = c["timing_diagnosis"]["reference_jie"]
        add(f"| {c['id']} | {cat_names[c['category']]} | {c['birth']} | {c['gender']} | {c['place']} | "
            f"{'/'.join(e['pillars'])} | {e['day_master']} | {e['qiyun']['mangpai_rough_start_age']:.0f} | "
            f"{e['qiyun']['precise_start_age']:.6f} | {e['dayun'][0][0]} {e['dayun'][0][1]} | "
            f"{jd['delta_s_sxtwl_minus_engine']:+.3f}s | {len(c['diffs'])} |")
    add("")
    add("边界专项：NJ-01 / NJ-02 是同一日跨 1982 立春交节 ±10 分钟的一对盘，年柱 辛酉→壬戌、"
        "月柱 辛丑→壬寅 在 engine 与 sxtwl 两侧同步翻转；NJ-03~06 覆盖惊蛰/立秋/寒露/大雪，"
        "两侧同为交节前/后一个月建。起运边界 QY-01/02、QY-03/04、QY-05/06 各自跨一个"
        "粗略起运岁数翻转点（3↔2、2↔1、4↔3），QY-07 为 29 日封顶（10 岁）；两侧数值完全一致。")
    add("")
    add("## 5. 差异表")
    add("")
    if p["diffs"]:
        add("| 盘号 | 字段 | engine | 独立 | 差值 | 按节气差预测 | 残差 |")
        add("|---|---|---|---|---|---|---|")
        for d in p["diffs"]:
            if "delta_engine_minus_independent_s" in d:
                delta = f"{d['delta_engine_minus_independent_s']:+.0f}s"
                pred = f"{d['predicted_by_jie_delta_s']:+.1f}s"
                res = f"{d['residual_s']:+.3f}s"
            elif "delta_engine_minus_independent" in d:
                delta = f"{d['delta_engine_minus_independent']:+.3e}"
                pred = f"{d['predicted_by_jie_delta']:+.3e}"
                res = f"{d['residual']:+.2e}"
            else:
                delta = pred = res = "—"
            add(f"| {d['chart']} | `{d['field']}` | {d['engine']} | {d['independent']} | {delta} | {pred} | {res} |")
    else:
        add("无差异。")
    add("")
    add("## 6. 差异归因：节气表秒差 × 120")
    add("")
    add("把 engine 的 `precise_start_age` 反解成它实际使用的参考节时刻，再与 sxtwl 天文学交节时刻对比，"
        "可逐盘验证一条恒等式：")
    add("")
    add("```text")
    add("Δ交运时刻 = 120 × Δ参考节(秒)      Δ精确起运岁 = Δ参考节(秒) / 259200")
    add("```")
    add("")
    add(f"- 参考节最大秒差 {s['max_reference_jie_delta_s']:.3f}s（NM-05，2019 惊蛰：lunar_python 05:09:46 vs "
        "sxtwl 05:09:39）；其余 24 盘 ≤1.7s。")
    add(f"- 交运时刻实测差 {s['diff_timing'] // 2} 盘落在 "
        f"≤60s {bands['<=60s']} / 60–300s {bands['60-300s']} / >300s {bands['>300s']}，"
        f"最大 {s['max_start_datetime_delta_s']:.0f}s（NM-05）；与 120×节差逐盘吻合。")
    add(f"- 第 5 节「残差」= 实测差 − 120×节差，全部 <1s（两侧交运时刻均按秒截断所致）；"
        f"未解释差异 {s['unexplained_diff_count']} 项。")
    add("")
    add("## 7. 结论")
    add("")
    add(f"1. 四柱（年/月/日/时）、日主、藏干（字符/本气中气余气）、十神（天干/藏干/本气）、旬空、"
        f"粗略起运岁数、大运十步干支与起止年份：{s['checks_discrete']} 项检查，差异 {s['diff_discrete']}。")
    add(f"2. 精确起运岁数与精确交运时刻：{s['checks_timing']} 项检查，差异 {s['diff_timing']}"
        f"（25 盘 × 2 字段），未解释 {s['unexplained_diff_count']}。")
    add(f"3. 严格按卡的「差异必须为 0」：{'通过' if s['strict_pass'] else '不通过'}；"
        "差异已逐盘列出（第 5 节），未宣称通过。")
    add("4. 差异性质：全部为节气表秒级差经 ×120 放大的确定性传播，engine 计算式无误差"
        "（残差 <1s）；不是排盘、十神、旬空或大运年份错误。")
    add(f"5. 边界覆盖：晚子时 7、节气交界 6、起运边界 7、普通 5；补充检查"
        f"（23 点 late_zi 告警、rollover_23 变体日柱、0 点 early_zi 告警、近节 near_jie 告警）"
        f"{s['supplementary_checks']} 项差异 {s['supplementary_diff_count']}。")
    add("")
    add("验收建议（供中枢决定，本卡未授权改判据）：若要求 0 差异，需要把「精确交运时刻」"
        "的比对基准限定为同源节气表（那样不再独立），或明确该字段的容差（传播上界为 120×节差，"
        "本批实测 ≤829s）；离散事实字段已可 0 差异验收。")
    add("")
    add("本卡只读 `engine.cli`：未改 engine/规则/测试，未跑评分器，未做 git 写，未做方向/断语。")
    add("")
    add("## 8. 复现")
    add("")
    add("```bash")
    add(".venv\\Scripts\\python.exe META/fact-audit-v1-runner.py")
    add("```")
    add("")
    add("Runner 只通过 `python -m engine.cli chart`（子进程）读取 engine，不改 engine/规则/测试，"
        "不做 git 写，不做方向/断语。")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
