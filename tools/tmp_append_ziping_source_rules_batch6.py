from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
IR_PATH = ROOT / "theory/_ir/ziping_rule_ir.yaml"
REPORT_PATH = ROOT / "theory/_ir/ziping_alignment_report.yaml"
BATCH5_SCRIPT = ROOT / "tools/tmp_append_ziping_source_rules_batch5.py"
SOURCE_P2 = "sources/ziping/穷通宝鉴-明-余春台_part2.md"

NEW_RULES = [
    {
        "rule_id": "ZP-SRC-20260617-058",
        "theory_id": "ziping",
        "statement": "庚金生于九月，戊土司令而有土厚埋金之患，宜先用甲木疏土、后用壬水淘洗，忌己土浊壬；甲壬俱备则格局清贵，二者俱无则下格。",
        "structure_type": ["use_god", "avoid_god", "pattern"],
        "element_vector": {"wood": 1, "fire": 0, "earth": -1, "metal": 1, "water": 1},
        "domain": ["career", "fate"],
        "status": "active",
        "source_path": SOURCE_P2,
        "source_excerpt": "九月庚金，戊土司令，最怕土厚埋金，宜先用甲疏，後用壬洗，则金自出矣，忌见己土浊壬。",
        "source_line": 172,
    },
    {
        "rule_id": "ZP-SRC-20260617-059",
        "theory_id": "ziping",
        "statement": "庚金生于十月，水冷金寒，须丁火炼金、丙火温暖；若金水混杂而全无丙丁，或金局无火，则格局偏寒而难成。",
        "structure_type": ["use_god", "avoid_god", "pattern"],
        "element_vector": {"wood": 1, "fire": 1, "earth": 0, "metal": 1, "water": -1},
        "domain": ["career", "fate", "health"],
        "status": "active",
        "source_path": SOURCE_P2,
        "source_excerpt": "十月庚金，水冷性寒，非丁莫造，非丙不暖。",
        "source_line": 187,
    },
    {
        "rule_id": "ZP-SRC-20260617-060",
        "theory_id": "ziping",
        "statement": "庚金生于十一月，天气严寒，仍以丁火、甲木为先，丙火照暖为次；若一派金水而不入火土之乡，多主孤贫浪荡。",
        "structure_type": ["use_god", "avoid_god", "pattern"],
        "element_vector": {"wood": 1, "fire": 1, "earth": 0, "metal": 1, "water": -1},
        "domain": ["career", "fate", "health"],
        "status": "active",
        "source_path": SOURCE_P2,
        "source_excerpt": "十一月庚金，天气严寒，仍取丁甲，次取丙火照暖。",
        "source_line": 200,
    },
    {
        "rule_id": "ZP-SRC-20260617-061",
        "theory_id": "ziping",
        "statement": "庚金生于十二月，寒湿太重，先取丙火解冻，次取丁火炼金，甲木亦不可少；丙丁甲得用则寒金可成器。",
        "structure_type": ["use_god", "pattern"],
        "element_vector": {"wood": 1, "fire": 1, "earth": 0, "metal": 1, "water": -1},
        "domain": ["career", "fate"],
        "status": "active",
        "source_path": SOURCE_P2,
        "source_excerpt": "十二月庚金，寒气太重，且多湿泥，愈寒愈冻，先取丙火解冻，次取丁火炼金，甲亦不可少。",
        "source_line": 215,
    },
    {
        "rule_id": "ZP-SRC-20260617-062",
        "theory_id": "ziping",
        "statement": "辛金生于正月，寒未尽而甲木司权，先取己土为身本，再赖壬水发金，庚金佐制甲木；己壬庚配合则富贵较全。",
        "structure_type": ["use_god", "avoid_god", "pattern"],
        "element_vector": {"wood": -1, "fire": 1, "earth": 1, "metal": 1, "water": 1},
        "domain": ["career", "wealth", "fate"],
        "status": "active",
        "source_path": SOURCE_P2,
        "source_excerpt": "故正月辛金，先己後壬，己为君，庚为佐，如用丙火须参看。",
        "source_line": 232,
    },
    {
        "rule_id": "ZP-SRC-20260617-063",
        "theory_id": "ziping",
        "statement": "辛金生于二月，阳和木旺，以壬水为尊，戊己土为病，须甲木制伏土浊；壬甲得配则金不埋、水不浊。",
        "structure_type": ["use_god", "avoid_god", "pattern"],
        "element_vector": {"wood": 1, "fire": 0, "earth": -1, "metal": 1, "water": 1},
        "domain": ["career", "wealth", "fate"],
        "status": "active",
        "source_path": SOURCE_P2,
        "source_excerpt": "二月辛金，阳和之际，壬水为尊，见戊己为病，得甲制伏，则辛金不致埋没，壬水不致混浊。",
        "source_line": 241,
    },
    {
        "rule_id": "ZP-SRC-20260617-064",
        "theory_id": "ziping",
        "statement": "辛金生于三月，戊土司令而母旺子相，先用壬水淘洗，后用甲木疏土；壬甲俱无则平常，土厚无甲则易成埋金。",
        "structure_type": ["use_god", "avoid_god", "pattern"],
        "element_vector": {"wood": 1, "fire": -1, "earth": -1, "metal": 1, "water": 1},
        "domain": ["career", "fate"],
        "status": "active",
        "source_path": SOURCE_P2,
        "source_excerpt": "三月辛金，戊土司令，辛承正气，母旺子相，先壬後甲。",
        "source_line": 265,
    },
    {
        "rule_id": "ZP-SRC-20260617-065",
        "theory_id": "ziping",
        "statement": "辛金生于四月，忌丙火燥烈，喜壬水洗淘；壬癸甲俱无又不成格者为下品，火旺无水时可取土泄火。",
        "structure_type": ["use_god", "avoid_god", "pattern"],
        "element_vector": {"wood": 1, "fire": -1, "earth": 1, "metal": 1, "water": 1},
        "domain": ["career", "fate", "health"],
        "status": "active",
        "source_path": SOURCE_P2,
        "source_excerpt": "四月辛金，时道首夏，忌丙火之燥烈，喜壬水之洗淘。",
        "source_line": 271,
    },
    {
        "rule_id": "ZP-SRC-20260617-066",
        "theory_id": "ziping",
        "statement": "辛金生于五月，丁火司权而辛金失令，不宜煅炼，须壬水与己土并用，癸水可辅但力弱；火局无壬则难救。",
        "structure_type": ["use_god", "avoid_god", "pattern"],
        "element_vector": {"wood": 0, "fire": -1, "earth": 1, "metal": 1, "water": 1},
        "domain": ["career", "wealth", "fate", "health"],
        "status": "active",
        "source_path": SOURCE_P2,
        "source_excerpt": "五月辛金，丁火司权，辛金失令，阴柔之极，不宜煆炼，须己壬兼用。",
        "source_line": 282,
    },
    {
        "rule_id": "ZP-SRC-20260617-067",
        "theory_id": "ziping",
        "statement": "辛金生于六月，己土当权而土多掩金，先用壬水，取庚金为佐，忌戊土出干；若得甲木制戊方吉。",
        "structure_type": ["use_god", "avoid_god", "pattern"],
        "element_vector": {"wood": 1, "fire": 0, "earth": -1, "metal": 1, "water": 1},
        "domain": ["career", "fate"],
        "status": "active",
        "source_path": SOURCE_P2,
        "source_excerpt": "六月辛金，己土当权，辅助太多，恐掩金光，先用壬水，取庚佐之。",
        "source_line": 293,
    },
    {
        "rule_id": "ZP-SRC-20260617-068",
        "theory_id": "ziping",
        "statement": "辛金生于七月，庚金司令而金旺，壬水为尊以泄金流通，甲木与戊土酌用，癸水不可作为主用。",
        "structure_type": ["use_god", "pattern"],
        "element_vector": {"wood": 1, "fire": 0, "earth": 1, "metal": 1, "water": 1},
        "domain": ["career", "fate"],
        "status": "active",
        "source_path": SOURCE_P2,
        "source_excerpt": "七月辛金，壬不在多，故书曰，水浅金多，号曰体全之象，壬水为尊，甲戊酌用可也，癸水不可为用。",
        "source_line": 308,
    },
    {
        "rule_id": "ZP-SRC-20260617-069",
        "theory_id": "ziping",
        "statement": "辛金生于八月，金旺至极，专用壬水淘洗流通，戊己土生扶太过为病，有土则喜甲木制土，无戊则不宜用甲。",
        "structure_type": ["use_god", "avoid_god", "pattern"],
        "element_vector": {"wood": 1, "fire": 0, "earth": -1, "metal": 1, "water": 1},
        "domain": ["career", "wealth", "fate"],
        "status": "active",
        "source_path": SOURCE_P2,
        "source_excerpt": "八月辛金，当权得令，旺之极矣，专用壬水淘洗，故云金见水以流通。",
        "source_line": 316,
    },
    {
        "rule_id": "ZP-SRC-20260617-070",
        "theory_id": "ziping",
        "statement": "辛金生于九月，成土司令而土重，先壬后甲，以壬泄旺金、甲疏厚土；火土为病，水木为药。",
        "structure_type": ["use_god", "avoid_god", "pattern"],
        "element_vector": {"wood": 1, "fire": -1, "earth": -1, "metal": 1, "water": 1},
        "domain": ["career", "fate"],
        "status": "active",
        "source_path": SOURCE_P2,
        "source_excerpt": "九月辛金，成土司令，母旺子相，须甲疏土，壬泄旺金，先壬後甲。",
        "source_line": 338,
    },
    {
        "rule_id": "ZP-SRC-20260617-071",
        "theory_id": "ziping",
        "statement": "水命总论以源流、堤防与寒暖为纲：水赖金生而流远，泛滥赖土堤防，水火均则既济，水土混则浊源；四时忌火多、土重、金死、木旺失衡。",
        "structure_type": ["use_god", "avoid_god", "pattern"],
        "element_vector": {"wood": -1, "fire": -1, "earth": 1, "metal": 1, "water": 1},
        "domain": ["fate", "health", "career"],
        "status": "active",
        "source_path": SOURCE_P2,
        "source_excerpt": "水不绝源，仗金生而流远，水流泛滥，赖土克以堤防，水火均，则合既济之美，水土混，则有浊源之凶。",
        "source_line": 385,
    },
]


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def dump_yaml(path: Path, data) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")


def coverage(rules):
    keys = ["pattern", "ten_gods", "use_god", "avoid_god"]
    total = len(rules)
    return {
        key: round(sum(1 for rule in rules if key in rule.get("structure_type", [])) / total * 100, 2)
        for key in keys
        if any(key in rule.get("structure_type", []) for rule in rules)
    }


ir = load_yaml(IR_PATH)
report = load_yaml(REPORT_PATH)
existing_ids = {rule["rule_id"] for rule in ir["rules"]}
for rule in NEW_RULES:
    if rule["rule_id"] in existing_ids:
        raise SystemExit(f"duplicate rule_id: {rule['rule_id']}")

ir["rules"].extend(NEW_RULES)
source_meta = ir.setdefault("enhancement", {}).setdefault("source_text_extraction", {})
source_meta["added_rule_count"] = source_meta.get("added_rule_count", 0) + len(NEW_RULES)
source_meta.setdefault("added_rule_ids", []).extend(rule["rule_id"] for rule in NEW_RULES)
source_meta.setdefault("batches", []).append(
    {
        "batch_id": "source_text_batch_006",
        "source_files": [SOURCE_P2],
        "added_rule_ids": [rule["rule_id"] for rule in NEW_RULES],
    }
)

all_rules = ir["rules"]
report["rule_count"] = len(all_rules)
report["structure_coverage"] = {key: value for key, value in coverage(all_rules).items() if key != "avoid_god"}
report_meta = report.setdefault("source_text_extraction", {})
report_meta["added_rule_count"] = source_meta["added_rule_count"]
report_meta.setdefault("added_rule_ids", []).extend(rule["rule_id"] for rule in NEW_RULES)
report_meta.setdefault("batches", []).append(
    {
        "batch_id": "source_text_batch_006",
        "source_files": [SOURCE_P2],
        "added_rule_ids": [rule["rule_id"] for rule in NEW_RULES],
    }
)

if BATCH5_SCRIPT.exists():
    BATCH5_SCRIPT.unlink()

dump_yaml(IR_PATH, ir)
dump_yaml(REPORT_PATH, report)

all_ids = [rule["rule_id"] for rule in all_rules]
assert len(all_rules) == 128, len(all_rules)
assert len(set(all_ids)) == len(all_ids)
assert all(rule.get("theory_id") == "ziping" for rule in all_rules)
assert "conflict_edges" not in ir
assert ir["enhancement"]["source_text_extraction"]["boundary"]["cross_school_fusion"] is False
assert ir["enhancement"]["source_text_extraction"]["boundary"]["conflict_edges_generated"] is False
assert ir["enhancement"]["source_text_extraction"]["boundary"]["rule_graph_updated"] is False
assert ir["enhancement"]["source_text_extraction"]["boundary"]["family_clustering"] is False
assert report["rule_count"] == 128
assert report_meta["added_rule_count"] == 71
print(f"BATCH6 OK added={len(NEW_RULES)} rule_count={len(all_rules)} coverage={coverage(all_rules)}")
print("boundary ok: ziping only; no conflict_edges; no cross-school fusion; batch5 temp cleaned")
