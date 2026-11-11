"""L1 结构化盘面：调紫微项目排盘引擎，并在紫微体系内核验盘面断言。

与 L2（v4.0 解读文本）严格分离：
- L1 是紫微体系内的 chart_fact，用来核对「命宫是否空宫、四化落宫」这类断言；
- 对本仓库而言它仍是**旁证**，信封保留 not_usable_as，绝不冒充 engine.cli 事实或理论 source_ref。

Python 侧零新增依赖；Node 侧复用紫微项目已装的 tsx / iztro（cwd 设为紫微项目根）。
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from .case_key import BRANCHES, CaseKey
from .lookup import load_config

ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).with_name("ziwei_chart_l1.mts")

# 声明式断言：核验外部紫微文本里的盘面陈述，不做命理推断、不推断吉凶。
# 传入自定义 --claims 时用同样 schema 覆盖。
DEFAULT_CLAIMS: list[dict] = [
    {"id": "ming_gong_you", "text": "命宫在酉位",
     "check": {"type": "ming_branch", "equals": 9}},
    {"id": "ming_gong_empty", "text": "命宫无主星（空宫）",
     "check": {"type": "palace_empty", "scope": "ming", "expect": True}},
    {"id": "lucun_shou_ming", "text": "禄存守命",
     "check": {"type": "palace_stars", "scope": "ming", "names": ["禄存"]}},
    {"id": "yangtuo_jia_ming", "text": "擎羊陀罗夹命",
     "check": {"type": "clip", "names": ["擎羊", "陀罗"]}},
    {"id": "duigong_ziwei_tanlang", "text": "对宫紫微贪狼同坐（借星来源）",
     "check": {"type": "palace_major", "scope": "opposite", "equals": ["紫微", "贪狼"]}},
    {"id": "qianyi_ziwei_tanlang", "text": "迁移宫紫微贪狼",
     "check": {"type": "palace", "scope": "迁移", "major_equals": ["紫微", "贪狼"]}},
    {"id": "shengong_qianyi", "text": "身宫落迁移",
     "check": {"type": "shen_palace", "equals": "迁移"}},
    {"id": "guanlu_tianfu_lingxing", "text": "官禄宫天府、同坐铃星",
     "check": {"type": "palace", "scope": "官禄", "major_equals": ["天府"], "names": ["铃星"]}},
    {"id": "caibo_tianxiang", "text": "财帛宫天相",
     "check": {"type": "palace", "scope": "财帛", "major_equals": ["天相"]}},
    {"id": "tiankui_puyi", "text": "天魁在仆役",
     "check": {"type": "palace", "scope": "仆役", "names": ["天魁"]}},
    {"id": "sihua_jumen_lu", "text": "巨门化禄在疾厄",
     "check": {"type": "palace_sihua", "scope": "疾厄", "pairs": [["巨门", "禄"]]}},
    {"id": "sihua_taiyang_quan", "text": "太阳化权在田宅",
     "check": {"type": "palace_sihua", "scope": "田宅", "pairs": [["太阳", "权"]]}},
    {"id": "sihua_wenchang_wenqu_fuqi", "text": "文昌化忌与文曲化科同落夫妻",
     "check": {"type": "palace_sihua", "scope": "夫妻",
               "pairs": [["文昌", "忌"], ["文曲", "科"]]}},
    {"id": "daxian_26_35", "text": "26–35 岁大限走亥宫福德，武曲破军加天马天虚",
     "check": {"type": "daxian", "start_age": 26, "end_age": 35,
               "palace": "福德", "branch": 11, "stars": ["武曲", "破军", "天马", "天虚"]}},
]


def generate_chart(case_key: CaseKey, config: dict | None = None, *, timeout: int = 120) -> dict:
    """调用紫微项目 generateChart，返回 {ok, chart, generator}。失败抛 LookupError。"""
    cfg = dict(config if config is not None else load_config())
    project_dir = str(cfg.get("project_dir", "")).strip()
    if not project_dir:
        raise LookupError(
            "未配置 project_dir；在 config/ziwei.local.toml 填紫微项目路径，"
            "或设置 ZIWEI_PROJECT_DIR（L1 需要该项目已 npm install）"
        )
    if not Path(project_dir, "lib", "ziwei", "algorithm.ts").is_file():
        raise LookupError(f"project_dir 下找不到 lib/ziwei/algorithm.ts：{project_dir}")

    cmd = [
        str(cfg.get("node_bin") or "node"),
        "--import", "tsx",
        str(RUNNER),
        project_dir,
        str(case_key.year),
        str(int(case_key.birth_iso[5:7])),
        str(int(case_key.birth_iso[8:10])),
        str(case_key.hour_index),
        case_key.gender_ziwei,
    ]
    try:
        proc = subprocess.run(
            cmd, cwd=project_dir, capture_output=True, text=True,
            encoding="utf-8", timeout=timeout, check=False,
        )
    except FileNotFoundError as e:
        raise LookupError(f"找不到 node：{e}；可设 ZIWEI_NODE_BIN") from e
    except subprocess.TimeoutExpired as e:
        raise LookupError(f"L1 排盘超时（{timeout}s）") from e

    out = (proc.stdout or "").strip()
    if not out:
        raise LookupError(
            f"L1 排盘无输出；stderr={(proc.stderr or '').strip()[:400]}；"
            "确认紫微项目已 npm install（需要 tsx / iztro / lunar-javascript）"
        )
    try:
        payload = json.loads(out.splitlines()[-1])
    except json.JSONDecodeError as e:
        raise LookupError(f"L1 排盘输出不是 JSON：{out[:300]}") from e
    if not payload.get("ok"):
        raise LookupError(str(payload.get("error", "未知 L1 排盘错误")))
    if not isinstance(payload.get("chart"), dict):
        raise LookupError("L1 排盘结果缺 chart 对象")
    return payload


def chart_fingerprint(chart: dict) -> dict:
    """稳定序列化后的指纹，供附录 locator 与复现比对。"""
    blob = json.dumps(chart, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob)}


def _stars(palace: dict) -> list[str]:
    return [str(s.get("name", "")) for s in palace.get("stars", []) if isinstance(s, dict)]


def _major(palace: dict) -> list[str]:
    return [str(s.get("name", "")) for s in palace.get("stars", [])
            if isinstance(s, dict) and s.get("type") == "major"]


def _sihua(palace: dict) -> list[list[str]]:
    return [[str(s.get("name", "")), str(s.get("siHua", ""))]
            for s in palace.get("stars", [])
            if isinstance(s, dict) and s.get("siHua")]


def _label(palace: dict) -> str:
    return f"{BRANCHES[palace['branch']]}宫·{palace.get('name', '?')}"


def _palace(chart: dict, scope: str) -> dict | None:
    palaces = chart.get("palaces", [])
    if scope == "ming":
        return next((p for p in palaces if p.get("isMingGong")), None)
    if scope == "shen":
        return next((p for p in palaces if p.get("isShenGong")), None)
    if scope == "opposite":
        ming = _palace(chart, "ming")
        if not ming:
            return None
        target = (ming["branch"] + 6) % 12
        return next((p for p in palaces if p.get("branch") == target), None)
    return next((p for p in palaces if p.get("name") == scope), None)


def _evaluate_one(chart: dict, check: dict) -> tuple[bool | None, str]:
    """返回 (matched, evidence)。None = 字段缺失，无法判定。"""
    kind = check.get("type")
    if kind == "ming_branch":
        ming = _palace(chart, "ming")
        if not ming:
            return None, "缺命宫字段"
        b = ming.get("branch")
        return b == check.get("equals"), f"命宫地支索引 {b}（{BRANCHES[b]}），期望 {check.get('equals')}"

    if kind == "palace_empty":
        p = _palace(chart, str(check.get("scope")))
        if not p:
            return None, f"找不到宫位 {check.get('scope')}"
        empty = not _major(p)
        return empty == bool(check.get("expect", True)), (
            f"{_label(p)} 主星={','.join(_major(p)) or '（无）'}；"
            f"全星={','.join(_stars(p)) or '（无）'}"
        )

    if kind in ("palace_stars", "palace_major", "palace", "palace_sihua"):
        p = _palace(chart, str(check.get("scope")))
        if not p:
            return None, f"找不到宫位 {check.get('scope')}"
        major, stars, hua = _major(p), _stars(p), _sihua(p)
        results: list[bool] = []
        bits = [f"{_label(p)} 主星={','.join(major) or '（无）'}"]
        if "major_equals" in check:
            results.append(sorted(major) == sorted(check["major_equals"]))
            bits.append(f"期望主星={','.join(check['major_equals'])}")
        if "names" in check:
            missing = [n for n in check["names"] if n not in stars]
            results.append(not missing)
            bits.append(f"需含={','.join(check['names'])}；缺={','.join(missing) or '无'}")
        if kind == "palace_major":
            expected = check.get("equals", [])
            results.append(sorted(major) == sorted(expected))
            bits.append(f"期望主星={','.join(expected)}")
        if "pairs" in check:
            missing = [f"{a}:{b}" for a, b in check["pairs"] if [a, b] not in hua]
            results.append(not missing)
            bits.append(f"四化={','.join(f'{a}:{b}' for a, b in hua) or '（无）'}；缺={','.join(missing) or '无'}")
        return (all(results) if results else None), "；".join(bits)

    if kind == "clip":
        ming = _palace(chart, "ming")
        if not ming:
            return None, "缺命宫字段"
        palaces = chart.get("palaces", [])
        prev = next((p for p in palaces if p.get("branch") == (ming["branch"] + 11) % 12), None)
        nxt = next((p for p in palaces if p.get("branch") == (ming["branch"] + 1) % 12), None)
        if not prev or not nxt:
            return None, "缺命宫相邻宫"
        expected = set(check.get("names", []))
        found = set(_stars(prev)) | set(_stars(nxt))
        return expected.issubset(found), (
            f"{_label(prev)} 含 {','.join(n for n in expected if n in _stars(prev)) or '—'}；"
            f"{_label(nxt)} 含 {','.join(n for n in expected if n in _stars(nxt)) or '—'}"
        )

    if kind == "shen_palace":
        p = _palace(chart, "shen")
        if not p:
            return None, "缺身宫字段"
        return p.get("name") == check.get("equals"), (
            f"身宫 {_label(p)}，期望 {check.get('equals')}"
        )

    if kind == "daxian":
        hit = next((d for d in chart.get("daXians", [])
                    if d.get("startAge") == check.get("start_age")
                    and d.get("endAge") == check.get("end_age")), None)
        if not hit:
            return None, f"找不到 {check.get('start_age')}–{check.get('end_age')} 大限"
        branch_ok = hit.get("palaceBranch") == check.get("branch") if "branch" in check else True
        name_ok = hit.get("palaceName") == check.get("palace") if "palace" in check else True
        p = next((x for x in chart.get("palaces", []) if x.get("branch") == hit.get("palaceBranch")), None)
        stars = _stars(p) if p else []
        missing = [s for s in check.get("stars", []) if s not in stars]
        return (branch_ok and name_ok and not missing), (
            f"{check.get('start_age')}–{check.get('end_age')} → "
            f"{BRANCHES[hit.get('palaceBranch', 0)]}宫·{hit.get('palaceName')}；"
            f"该宫星曜={','.join(stars) or '（无）'}；缺={','.join(missing) or '无'}"
        )

    return None, f"未知断言类型 {kind!r}"


def evaluate_assertions(chart: dict, claims: list[dict] | None = None) -> list[dict]:
    claims = DEFAULT_CLAIMS if claims is None else claims
    rows = []
    for c in claims:
        matched, evidence = _evaluate_one(chart, c.get("check", {}))
        rows.append({
            "id": c.get("id"),
            "text": c.get("text"),
            "check": c.get("check"),
            "matched": matched,
            "evidence": evidence,
        })
    return rows


def summarize_chart(chart: dict) -> dict:
    """信封里的精简盘面摘要；完整 chart 由 --full 单独取。"""
    ming, shen, opp = _palace(chart, "ming"), _palace(chart, "shen"), _palace(chart, "opposite")
    palaces = chart.get("palaces", [])
    return {
        "ming_gong": {"branch": ming.get("branch"), "branch_name": BRANCHES[ming["branch"]],
                      "name": ming.get("name"), "major": _major(ming), "stars": _stars(ming)} if ming else None,
        "shen_gong": {"branch": shen.get("branch"), "name": shen.get("name")} if shen else None,
        "opposite": {"branch": opp.get("branch"), "name": opp.get("name"),
                     "major": _major(opp)} if opp else None,
        "wuxing_ju": chart.get("wuxingJuName"),
        "ziwei_pos": chart.get("ziweiPos"),
        "yin_yang_gender": chart.get("yinYangGender"),
        "ming_zhu": chart.get("mingZhu"),
        "shen_zhu": chart.get("shenZhu"),
        "sihua_by_palace": [
            {"palace": p.get("name"), "branch": BRANCHES[p["branch"]], "pairs": _sihua(p)}
            for p in palaces if _sihua(p)
        ],
        "sanfang_sizheng": [
            {"palace": p.get("name"), "branch": BRANCHES[p["branch"]], "major": _major(p)}
            for p in palaces if p.get("name") in ("命宫", "财帛", "官禄", "迁移")
        ],
        "da_xian_count": len(chart.get("daXians", [])),
    }
