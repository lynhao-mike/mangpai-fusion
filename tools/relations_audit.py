"""tools/relations_audit.py · 关系图边完整性/多余性体检（独立表驱动；--limit N 调试）。"""
from __future__ import annotations
import argparse, pathlib, re, sys
from collections import defaultdict
from engine.api import analyze_facts
ROOT = pathlib.Path(__file__).resolve().parents[1]
CASE_RE = re.compile(r"^(C-\d{4}-[A-Za-z0-9]+)-(乾|坤)-((?:[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]){4})$")
STEM_POS = ("Y.s", "M.s", "D.s", "H.s")
BRANCH_POS = ("Y.b", "M.b", "D.b", "H.b")

# 六冲、六合、六穿（害）
CHONG = {frozenset(p) for p in "子午 丑未 寅申 卯酉 辰戌 巳亥".split()}
LIUHE = {frozenset(p) for p in "子丑 寅亥 卯戌 辰酉 巳申 午未".split()}
CHUAN = {frozenset(p) for p in "子未 丑午 寅巳 卯辰 申亥 酉戌".split()}
# 天干五合、天干相冲
WUHE = {frozenset(p) for p in "甲己 乙庚 丙辛 丁壬 戊癸".split()}
STEM_CHONG = {frozenset(p) for p in "甲庚 乙辛 丙壬 丁癸".split()}
# 刑：子卯；寅巳申三刑；丑戌未三刑；辰午酉亥自刑
XING = {frozenset(p) for p in "子卯 寅巳 巳申 寅申 丑戌 戌未 丑未".split()}
ZIXING = set("辰午酉亥")
# 三合、三会（只统计存在率，不判错）
SANHE = [set(t) for t in "申子辰 亥卯未 寅午戌 巳酉丑".split()]
SANHUI = [set(t) for t in "寅卯辰 巳午未 申酉戌 亥子丑".split()]
FAKE_TABLES = {
    "chong": ("branch", CHONG), "liuhe": ("branch", LIUHE), "chuan": ("branch", CHUAN),
    "wuhe": ("stem", WUHE), "stem_chong": ("stem", STEM_CHONG),
}
KIND_ORDER = ("chong", "liuhe", "chuan", "xing", "wuhe", "stem_chong")

def _edges(edges: list[dict], kind: str, addrs: tuple[str, ...]) -> list[dict]:
    """某 kind 下成员恰好为给定地址的边。"""
    want = frozenset(addrs)
    return [e for e in edges if e.get("kind") == kind and frozenset(e.get("members") or ()) == want]
def audit_one(name: str, pillars: str, gender: str) -> tuple[list, list, list, dict]:
    """审计一盘：返回 (缺边, 假边, 重复边, 三合三会计数)。"""
    missing, fake, extra = [], [], []
    stats = {"sanhe": [0, 0], "sanhui": [0, 0]}  # [有边数, 应有两字组合数]
    ps = [pillars[i:i + 2] for i in range(0, 8, 2)]
    stems, branches = [p[0] for p in ps], [p[1] for p in ps]
    facts = analyze_facts(pillars=ps, gender=gender)
    edges = [e for e in facts["relations"]["edges"] if e.get("scope") == "natal"]
    chart_chars = dict(zip(STEM_POS, stems)) | dict(zip(BRANCH_POS, branches))

    def require(kind: str, addrs: tuple[str, ...], exact: bool = False) -> None:
        n = len(_edges(edges, kind, addrs))
        if n == 0:
            missing.append((kind, name, "/".join(addrs)))
        elif exact and n > 1:
            extra.append((kind, name, f"{'/'.join(addrs)} x{n}"))

    for i in range(4):
        for j in range(i + 1, 4):
            spair = frozenset((stems[i], stems[j]))
            if spair in WUHE:
                require("wuhe", (STEM_POS[i], STEM_POS[j]))
            if spair in STEM_CHONG:
                require("stem_chong", (STEM_POS[i], STEM_POS[j]))
            bpair = frozenset((branches[i], branches[j]))
            baddrs = (BRANCH_POS[i], BRANCH_POS[j])
            if branches[i] == branches[j]:
                if branches[i] in ZIXING:
                    require("xing", baddrs)
            else:
                if bpair in CHONG:
                    require("chong", baddrs, exact=True)
                if bpair in LIUHE:
                    require("liuhe", baddrs)
                if bpair in CHUAN:
                    require("chuan", baddrs)
                if bpair in XING:
                    require("xing", baddrs)
                for kind, groups in (("sanhe", SANHE), ("sanhui", SANHUI)):
                    if any(bpair <= grp for grp in groups):
                        stats[kind][1] += 1
                        if _edges(edges, kind, baddrs):
                            stats[kind][0] += 1

    for e in edges:
        spec = FAKE_TABLES.get(e.get("kind"))
        if spec is None:
            continue
        layer, table = spec
        chars = e.get("chars") or []
        members = e.get("members") or ()
        if (e.get("layer") != layer or len(chars) != 2 or len(members) != 2
                or frozenset(chars) not in table
                or any(chart_chars.get(m) != c for m, c in zip(members, chars))):
            fake.append((e.get("kind"), name, f"{e.get('id')} {e.get('chars')}"))
    return missing, fake, extra, stats
def _report(title: str, rows: list[tuple[str, str, str]]) -> int:
    """按 kind 分组打印，各给最多 3 个案例名示例；返回问题总数。"""
    print(f"\n{title}:")
    if not rows:
        print("  无")
        return 0
    grouped = defaultdict(list)
    for kind, name, detail in rows:
        grouped[kind].append((name, detail))
    for kind in KIND_ORDER:
        items = grouped.get(kind)
        if items:
            names = list(dict.fromkeys(n for n, _ in items))
            print(f"  {kind}: {len(items)} 处 / {len(names)} 案例")
            print(f"    示例: {'、'.join(names[:3])}")
    return len(rows)

def main() -> int:
    ap = argparse.ArgumentParser(description="关系图全量校验")
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 个案例（调试用）")
    args = ap.parse_args()
    cases = []
    for p in sorted((ROOT / "cases").iterdir()):
        m = CASE_RE.match(p.name)
        if m and p.is_dir():
            cases.append((p.name, m.group(3), m.group(2)))
    if args.limit:
        cases = cases[:args.limit]

    missing, fake, extra, errors = [], [], [], []
    totals = {"sanhe": [0, 0], "sanhui": [0, 0]}
    for name, pillars, gender in cases:
        try:
            miss, fk, ex, stats = audit_one(name, pillars, gender)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
            continue
        missing.extend(miss); fake.extend(fk); extra.extend(ex)
        for kind in totals:
            totals[kind][0] += stats[kind][0]
            totals[kind][1] += stats[kind][1]

    print("关系图全量校验 · cases/")
    print(f"案例总数: {len(cases)}")
    n_missing = _report("缺边统计（按 kind）", missing)
    n_fake = _report("假边统计（按 kind）", fake)
    n_extra = _report("重复边统计（按 kind）", extra)
    print("\n三合/三会存在率（两字同现，仅统计）:")
    for kind, label in (("sanhe", "三合"), ("sanhui", "三会")):
        hit, total = totals[kind]
        print(f"  {label}: {hit}/{total} = {f'{hit / total * 100:.2f}%' if total else 'N/A'}")
    if errors:
        print(f"\n运行异常: {len(errors)} 例")
        for row in errors[:3]:
            print(f"  {row}")
    print(f"\n结论: {'全部通过' if not (n_missing or n_fake or n_extra or errors) else '存在问题'}")
    return 1 if (n_missing or n_fake or n_extra or errors) else 0

if __name__ == "__main__":
    sys.exit(main())
