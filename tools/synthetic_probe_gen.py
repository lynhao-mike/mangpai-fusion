"""生成合成盘盲测批次：无真实个人对应，供拒答真实案例的分析者使用

设计动机
--------
某分析者（LLM）拒绝为真实个人出生盘推演敏感命运画像，即使已脱敏。
这是正当立场：四柱 + 性别 + 精确出生时刻在小样本下可识别到个人。

解决方式：构造合成四柱（非任何真实个人的出生时刻），
保留命理结构的多样性（五行分布、格局类型、刑冲合会、库的多少），
但不指向任何真实人。

与真实案例盲测的区别
--------------------
1. **没有真值**：合成盘没有对应的人生，无法判「对错」
2. **能测什么**：只能测**内部一致性**——同一盘两次判断是否一致、
   不同分析者之间是否一致、是否违反五道前置关、是否滥用「平」
3. **不能测什么**：准确率

因此本批次的价值是「方法论一致性检验」，不是「能力评测」。
这与跨模型一致性（inter-rater reliability）的目标一致，
而准确率仍需真实案例（由接受该任务的分析者完成）。

CLI
---
    python -m tools.synthetic_probe_gen --count 8 --out .workbuddy-ai/synthetic-batch1.json
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / ".workbuddy-ai" / "synthetic-probes"

# 天干地支（用于构造合法四柱）
STEMS = list("甲乙丙丁戊己庚辛壬癸")
BRANCHES = list("子丑寅卯辰巳午未申酉戌亥")

# 六十甲子合法性：天干序号与地支序号同奇偶
_GAN_IDX = {g: i for i, g in enumerate(STEMS)}
_ZHI_IDX = {z: i for i, z in enumerate(BRANCHES)}

# 五鼠遁：日干 → 子时天干序号
_WUSHU = {
    "甲": 0, "己": 0, "乙": 2, "庚": 2, "丙": 4, "辛": 4,
    "丁": 6, "壬": 6, "戊": 8, "癸": 8,
}

# 五虎遁：年干 → 寅月天干序号
_WUHU = {
    "甲": 2, "己": 2, "乙": 4, "庚": 4, "丙": 6, "辛": 6,
    "丁": 8, "壬": 8, "戊": 0, "癸": 0,
}

# 传统年柱起点用立春，这里简化为「年干支」由调用方给出合法组合
YEAR_PILLARS = [
    "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未",
    "壬申", "癸酉", "甲戌", "乙亥", "丙子", "丁丑", "戊寅", "己卯",
    "庚辰", "辛巳", "壬午", "癸未", "甲申", "乙酉", "丙戌", "丁亥",
]


def _valid_ganzhi(g: str, z: str) -> bool:
    return (_GAN_IDX[g] - _ZHI_IDX[z]) % 2 == 0


def month_pillars_for(year_stem: str) -> list[str]:
    """五虎遁：年干 → 12 个月的月柱（寅月起始）。"""
    start = _WUHU[year_stem]
    out = []
    for i in range(12):
        branch = BRANCHES[(2 + i) % 12]          # 寅月起
        stem = STEMS[(start + i) % 10]
        if _valid_ganzhi(stem, branch):
            out.append(stem + branch)
    return out


def hour_pillars_for(day_stem: str) -> list[str]:
    """五鼠遁：日干 → 12 个时辰的时柱。"""
    start = _WUSHU[day_stem]
    out = []
    for i in range(12):
        stem = STEMS[(start + i) % 10]
        branch = BRANCHES[i]
        if _valid_ganzhi(stem, branch):
            out.append(stem + branch)
    return out


def make_chart(rng: random.Random) -> list[str]:
    """构造一组合法四柱：年柱取自合法六十甲子，月柱按五虎遁，日柱任意合法，时柱按五鼠遁。"""
    year = rng.choice(YEAR_PILLARS)
    months = month_pillars_for(year[0])
    month = rng.choice(months)
    # 日柱：任取天干 + 合法地支
    while True:
        dg = rng.choice(STEMS)
        dz = rng.choice(BRANCHES)
        if _valid_ganzhi(dg, dz):
            day = dg + dz
            break
    hours = hour_pillars_for(day[0])
    hour = rng.choice(hours)
    return [year, month, day, hour]


def _birth_year_from_pillar(year_pillar: str, today_year: int = 2026) -> int:
    """由年柱反推一个合法的合成出生年份（最近一轮六十甲子内的年份）。"""
    gan, zhi = year_pillar[0], year_pillar[1]
    gi, zi = STEMS.index(gan), BRANCHES.index(zhi)
    # 从 today_year 逐年回退，找干支匹配的年份
    for y in range(today_year, today_year - 61, -1):
        if STEMS[(y - 4) % 10] == gan and BRANCHES[(y - 4) % 12] == zhi:
            return y
    return today_year - 30


def _compute_dayun(pillars: list[str], gender: str, birth_year: int) -> dict:
    """计算大运表与起运年。

    引擎 `--pillars` 模式能给出**大运干支序列与顺逆**（由年干阴阳 + 性别决定），
    但没有出生时刻 → 算不出精确交节时差 → `qiyun` 与 `start_year` 为 None。

    对合成盘而言，精确起运岁并非判断所必需（它只影响前后 1-2 年的边界）。
    因此这里：
    1. 用引擎 `--pillars` 取大运干支序列（这是精确的）；
    2. 按合成规则给定起运岁 = 3（题面明示为「合成假设」）；
    3. 由此推每年份的起讫年。

    题面会明确写出「起运 3 岁为合成假设」，避免分析者以为这是真实排盘结果。
    """
    import json as _json
    import subprocess as _sp

    r = _sp.run(
        [sys.executable, "-m", "engine.cli", "chart",
         "--pillars", " ".join(pillars), "--gender", gender, "--json"],
        cwd=ROOT, capture_output=True, encoding="utf-8",
    )
    if r.returncode != 0:
        return {"dayun": [], "qiyun": None, "qiyun_year": None,
                "error": (r.stderr or "")[:200]}
    try:
        d = _json.loads(r.stdout)
    except _json.JSONDecodeError:
        return {"dayun": [], "qiyun": None, "qiyun_year": None, "error": "输出非 JSON"}

    chart = d.get("chart", d)
    cycles = chart.get("cycles") or {}
    raw_dayun = cycles.get("dayun") or []
    direction = cycles.get("direction")

    SYNTH_QIYUN_AGE = 3          # 合成假设，题面明示
    qiyun_year = birth_year + SYNTH_QIYUN_AGE - 1

    dayun = []
    for i, dy in enumerate(raw_dayun):
        start = qiyun_year + i * 10
        dayun.append({
            "index": dy.get("index", i + 1),
            "ganzhi": dy.get("ganzhi"),
            "start_year": start,
            "end_year": start + 9,
            "start_age": SYNTH_QIYUN_AGE + i * 10,
        })

    return {
        "dayun": dayun,
        "qiyun": SYNTH_QIYUN_AGE,
        "qiyun_year": qiyun_year,
        "direction": direction,
        "synthetic_qiyun": True,     # 标记：起运岁是合成假设
        "error": None,
    }


def build_probe(pillars: list[str], rng: random.Random) -> dict:
    """合成盘：补全性别、出生年份、大运表，使题面信息自足。"""
    gender = rng.choice(["乾", "坤"])
    birth_year = _birth_year_from_pillar(pillars[0])
    dy = _compute_dayun(pillars, gender, birth_year)

    n = rng.randint(8, 12)
    # 待判年份限定在起运后、且不超过出生后 60 年，保证每年都能落进某步大运
    lo = (dy.get("qiyun_year") or (birth_year + 3)) + 1
    hi = min(birth_year + 60, 2030)
    pool = list(range(lo, hi + 1))
    if len(pool) < n:
        pool = list(range(birth_year + 1, birth_year + 61))
    years = sorted(rng.sample(pool, min(n, len(pool))))

    return {
        "case_id": "SYN-" + "".join(pillars),
        "pillars": pillars,
        "gender": gender,
        "birth_year": birth_year,
        "probe_years": years,
        "dayun": dy.get("dayun") or [],
        "qiyun": dy.get("qiyun"),
        "qiyun_year": dy.get("qiyun_year"),
        "dayun_error": dy.get("error"),
        "synthetic": True,
    }


def render_exam(item: dict) -> str:
    years = item["probe_years"]
    gender_cn = "男（乾造）" if item.get("gender") == "乾" else "女（坤造）"
    dayun = item.get("dayun") or []

    if dayun:
        rows = []
        by = item.get("birth_year") or 0
        for d in dayun:
            sy = d.get("start_year")
            start_age = d.get("start_age")
            if start_age is None and isinstance(sy, int) and by:
                start_age = sy - by + 1
            rows.append(
                f"| {d.get('index', '')} | {d.get('ganzhi', '')} | "
                f"{sy if sy is not None else '—'}–{d.get('end_year') if d.get('end_year') is not None else '—'} "
                f"| {start_age if start_age is not None else '—'} |"
            )
        dayun_rows = "\n".join(rows)
    else:
        dayun_rows = "| — | （引擎未能推算，请按常规规则自推） | — | — |"

    return f"""# 合成盘盲测题 · {item['case_id']}

> **这是一副合成盘**：四柱由程序构造，不对应任何真实个人的出生时刻。
> 因此没有「真实发生的事」可以对照——你不能判对错，我们也不判对错。
>
> 本批次测的是**判断过程的一致性与纪律性**：
> - 同样的盘，两次判断是否一致
> - 是否严格执行五道前置关
> - 是否滥用「平」来回避

## 一、盘面（信息已完整，无需推测）

- 四柱：{' '.join(item['pillars'])}
- 性别：{gender_cn}（决定大运顺逆）
- 合成出生年份：{item.get('birth_year')} 年
- 起运：{item.get('qiyun') or 3} 岁起运（{item.get('qiyun_year') or '—'} 年交运）
  **此起运岁为合成假设**（合成盘无精确出生时刻，引擎算不出真实交节时差），
  但大运干支序列由引擎精确推算。
- 待判断年份共 {len(years)} 个：{'、'.join(str(y) for y in years)}

### 大运表（干支由引擎推算，年份按 3 岁起运合成推算）

| 序 | 大运 | 起讫年 | 起始虚岁 |
|---|---|---|---|
{dayun_rows}

（说明：以上大运干支由引擎按年干阴阳 + 性别定顺逆精确推算；
  起讫年份按「3 岁起运、10 年一步」的合成假设推算。
  这是合成盘，不对应任何真实个人。）

## 二、作答要求（每年四项）

1. **领域** `matters`：该年谁被引动、应事落在哪个领域
2. **运级基调** `dayun_tone`：一句话定大运对该年的基调，流年只做应期修正
3. **吉凶** `polarity`：`吉` / `凶` / `平` 三选一
4. **依据** `basis`：必须用「地址ID＋干支＋关系名」
   （如 `H.b午×LN.b子 冲`、`M.b寅 三合火局 full`），**禁用 e### 边号**

## 三、五道前置关（缺一不得下断）

1. **领域判定**：这一年究竟「动」在什么事上？
2. **运级定位**：大运对这个年的基调是什么？（禁止跳过大运）
3. **成度三问**：合局是 full/half/gong？中神现否？成局之物为我所用还是攻体？
4. **倾向规则条件复述**：引「必凶」/「必吉」类规则时，复述全部前提并对盘
5. **漏边反向扫描**：断凶查救应（合绊/通关/合解冲）；断吉查用神是否被合克化

## 四、判「平」的条件

答平前必须双侧正查：给出「若判吉最强证据」+「若判凶最强证据」+
说明为何都不足。**仅「没看到实质损伤」不构成答平理由。**

## 五、输出格式

```json
{{
  "case_id": "{item['case_id']}",
  "year_judgments": [
    {{
      "year": {years[0]},
      "matters": ["career"],
      "dayun_tone": "某运某干支，基调偏吉/偏凶",
      "polarity": "吉",
      "basis": "M.b寅 三合火局 full；H.b午 填实"
    }}
  ]
}}
```

## 六、完成后

输出到 `.workbuddy-ai/synthetic-probes/<case_id>/year_judgments.json`。

**重复判断一次**（同一盘，隔开时间后重做），输出到
`year_judgments.round2.json`。这一步用于测你自己的内部一致率，
不是重复劳动——若两轮差异很大，说明该盘判断不稳定。
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="合成盘盲测生成器")
    ap.add_argument("--count", type=int, default=8)
    ap.add_argument("--seed", type=int, default=20261019)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)

    rng = random.Random(args.seed)
    seen: set[str] = set()
    items = []
    while len(items) < args.count:
        pillars = make_chart(rng)
        key = "".join(pillars)
        if key in seen:
            continue
        seen.add(key)
        items.append(build_probe(pillars, rng))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for it in items:
        d = OUT_DIR / it["case_id"]
        d.mkdir(exist_ok=True)
        (d / "exam.md").write_text(render_exam(it), encoding="utf-8")

    out = args.out or (ROOT / ".workbuddy-ai" / "synthetic-batch1.json")
    out.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"生成 {len(items)} 副合成盘 -> {OUT_DIR}")
    for it in items:
        print(f"  {it['case_id']:20s} {' '.join(it['pillars'])}  {len(it['probe_years'])} 年")
    print(f"\n清单已写入 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
