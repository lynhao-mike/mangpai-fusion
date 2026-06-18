from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
IR_PATH = ROOT / "theory/_ir/ziping_rule_ir.yaml"
REPORT_PATH = ROOT / "theory/_ir/ziping_alignment_report.yaml"
BATCH12_SCRIPT = ROOT / "tools/tmp_append_ziping_source_rules_batch12.py"
SOURCE_SANMING = "sources/ziping/《三命通会》.md"

NEW_RULES = [
    {
        "rule_id": "ZP-SRC-20260617-148",
        "theory_id": "ziping",
        "statement": "六阴朝阳以六辛日逢戊子时为格，子宫只宜一位，喜戊合癸、子为辛生地并运行西方；忌午冲、丑绊、丙巳填实及南方火地破格。",
        "structure_type": ["pattern", "ten_gods", "use_god", "avoid_god"],
        "element_vector": {"wood": 0, "fire": -1, "earth": 1, "metal": 1, "water": 1},
        "domain": ["career", "fate", "wealth", "family"],
        "status": "active",
        "source_path": SOURCE_SANMING,
        "source_excerpt": "六辛日，时逢戊子，嫌午位，运喜西方...柱中只宜子字一位，多则不中，怕午冲丑绊，则阴不能朝阳，丙巳填实...南方死绝则忌。",
        "source_line": 95,
    },
    {
        "rule_id": "ZP-SRC-20260617-149",
        "theory_id": "ziping",
        "statement": "六乙鼠贵以乙日独遇子时、遥合申中庚官为贵，子多聚贵尤妙；喜月通木局、水印相助，忌午冲、丑绊、申庚酉辛官煞显露及金火伤贵。",
        "structure_type": ["pattern", "ten_gods", "use_god", "avoid_god"],
        "element_vector": {"wood": 1, "fire": -1, "earth": 0, "metal": -1, "water": 1},
        "domain": ["career", "fate", "wealth"],
        "status": "active",
        "source_path": SOURCE_SANMING,
        "source_excerpt": "阴木独遇子时，为六乙鼠贵之地...若子字多，谓之聚贵，尤妙。年月中有午冲丑绊，则子不能遥禄，申庚为官露，酉辛为煞露...此格要月通木局...忌见金火。",
        "source_line": 96,
    },
    {
        "rule_id": "ZP-SRC-20260617-150",
        "theory_id": "ziping",
        "statement": "日禄归时以日主禄归时位且无官星为青云得路，喜日干坐旺、印绶生、月透财元、伤食与二德，主大富贵；忌刑冲破害、空亡死绝、劫财分禄、倒食作合及官煞克制。",
        "structure_type": ["pattern", "ten_gods", "use_god", "avoid_god"],
        "element_vector": {"wood": 0, "fire": 0, "earth": 0, "metal": 0, "water": 0},
        "domain": ["career", "wealth", "fate", "health"],
        "status": "active",
        "source_path": SOURCE_SANMING,
        "source_excerpt": "日禄归时没官星，号青云得路...日主之禄归于时位，喜日干坐旺、印绶生、月透财元、伤食、天月二德，主大富贵。忌刑冲破害、空亡死绝、及劫财分禄、倒食作合、官煞克制。",
        "source_line": 97,
    },
    {
        "rule_id": "ZP-SRC-20260617-151",
        "theory_id": "ziping",
        "statement": "日禄归时须辨财官另格与归禄互换：月有官星或天干透财官则作财官论，时支归禄而年月时亦见禄为聚福归禄，日时或年时互换禄多主贵享福。",
        "structure_type": ["pattern", "ten_gods", "use_god"],
        "element_vector": {"wood": 0, "fire": 0, "earth": 0, "metal": 0, "water": 0},
        "domain": ["career", "wealth", "fate"],
        "status": "active",
        "source_path": SOURCE_SANMING,
        "source_excerpt": "若月有官星或天干透财官，只作财官论；若时支归禄，年月时支亦有禄，谓之聚福归禄...若日禄归时，时禄归日，谓之互换禄；若年禄归时，时禄归年...俱主大贵享福。",
        "source_line": 97,
    },
    {
        "rule_id": "ZP-SRC-20260617-152",
        "theory_id": "ziping",
        "statement": "归禄得财而获福，无财归禄亦贫；日禄归时四柱岁运皆不喜官星与刑害，相冲克破则福因受损，身旺财食印旺运可发。",
        "structure_type": ["pattern", "ten_gods", "use_god", "avoid_god"],
        "element_vector": {"wood": 0, "fire": 0, "earth": 0, "metal": 0, "water": 0},
        "domain": ["career", "wealth", "fate"],
        "status": "active",
        "source_path": SOURCE_SANMING,
        "source_excerpt": "《元理赋》云：归禄得财而获福，无财归禄亦须贫。又云：日禄归时，四柱岁运皆不喜官星，有刑害，其福减半...若遇相冲灾必至，忽遭克破福无因。",
        "source_line": 97,
    },
    {
        "rule_id": "ZP-SRC-20260617-153",
        "theory_id": "ziping",
        "statement": "拱禄拱贵以日时同干夹拱禄位或官贵为格，须贵禄与月令通气，喜身旺、贵禄旺地及印绶食伤财运；忌刑冲破害、羊刃七煞伤日时。",
        "structure_type": ["pattern", "ten_gods", "use_god", "avoid_god"],
        "element_vector": {"wood": 0, "fire": 0, "earth": 0, "metal": 0, "water": 0},
        "domain": ["career", "wealth", "fate"],
        "status": "active",
        "source_path": SOURCE_SANMING,
        "source_excerpt": "拱禄拱贵，填实则凶。拱，向也，夹也...凡拱格，须日时同干，贵禄与月令通气，运行身旺及贵禄旺地，方大好，印绶、伤官、食神、财运，亦吉。忌刑冲破害，羊刃七煞，伤了日时。",
        "source_line": 98,
    },
    {
        "rule_id": "ZP-SRC-20260617-154",
        "theory_id": "ziping",
        "statement": "拱禄拱贵大忌填实与空亡，虚则能容、完则能盛，填实者多虚名虚利；提纲有用则以月令为重，月令无神方取虚拱之奇。",
        "structure_type": ["pattern", "ten_gods", "avoid_god"],
        "element_vector": {"wood": 0, "fire": 0, "earth": 0, "metal": 0, "water": 0},
        "domain": ["career", "fate", "wealth"],
        "status": "active",
        "source_path": SOURCE_SANMING,
        "source_excerpt": "大忌填实、空亡，譬如器皿空则能容，实则无用，所以只宜虚拱；完则能盛，破则无用，所以怕见空亡...拱禄拱贵格中稀，也须月令看支提，提纲有用提纲重，月令无神用此奇。",
        "source_line": 98,
    },
    {
        "rule_id": "ZP-SRC-20260617-155",
        "theory_id": "ziping",
        "statement": "冲禄以柱中无本禄而由同支多冲冲出对宫禄位为格，如庚寅多寅冲申、甲申多申冲寅；大忌伤日干之神与禄位填实，填实则不贵。",
        "structure_type": ["pattern", "ten_gods", "use_god", "avoid_god"],
        "element_vector": {"wood": 0, "fire": 0, "earth": 0, "metal": 0, "water": 0},
        "domain": ["career", "fate"],
        "status": "active",
        "source_path": SOURCE_SANMING,
        "source_excerpt": "冲禄此格如庚禄申，柱中无申，得庚寅日，年月时再有寅字，并冲申为庚之禄。甲禄在寅，柱中无寅，却得甲申日，年月时再有申字，并冲寅为甲之禄。大忌丙伤庚、庚伤甲，填实禄位则不贵。",
        "source_line": 99,
    },
    {
        "rule_id": "ZP-SRC-20260617-156",
        "theory_id": "ziping",
        "statement": "六壬趋艮以六壬日见甲寅时合出亥中壬禄为暗禄，明禄不如暗禄；喜寅多、身旺、食神生财生官，忌亥填实、冲刑克破、官煞损身与申庚伤甲。",
        "structure_type": ["pattern", "ten_gods", "use_god", "avoid_god"],
        "element_vector": {"wood": 1, "fire": 0, "earth": 0, "metal": -1, "water": 1},
        "domain": ["career", "wealth", "fate"],
        "status": "active",
        "source_path": SOURCE_SANMING,
        "source_excerpt": "六壬趋艮此格乃六壬日见甲寅时，合出亥中壬禄，即暗禄格。经云：明禄不如暗禄是也。忌亥字填实，怕冲刑克破...见寅字多者大富，以寅中甲木食神生丙火长生之财，财旺生官...忌官煞损身，申庚伤甲。",
        "source_line": 100,
    },
    {
        "rule_id": "ZP-SRC-20260617-157",
        "theory_id": "ziping",
        "statement": "六甲趋乾以六甲日见亥为格，亥为甲木长生并能合出寅中本禄；喜透印绶、生印助身，忌寅填实、巳刑冲，身弱逢金局太多岁运重见则生灾。",
        "structure_type": ["pattern", "ten_gods", "use_god", "avoid_god"],
        "element_vector": {"wood": 1, "fire": 0, "earth": 0, "metal": -1, "water": 1},
        "domain": ["career", "fate", "health", "personality"],
        "status": "active",
        "source_path": SOURCE_SANMING,
        "source_excerpt": "六甲趋乾此格乃六甲日见亥。亥，天门之位...甲木赖之长生。又亥能合出寅中本禄...忌寅字填实，巳字刑冲。又曰：甲见亥时，亥有壬禄为印，喜见辛金生印...若身弱遇巳酉丑局，金神太多，岁运重见，生灾。",
        "source_line": 101,
    },
    {
        "rule_id": "ZP-SRC-20260617-158",
        "theory_id": "ziping",
        "statement": "财官双美又称禄马同乡，以日支自坐正财正官、禄马兼全为贵，壬午、癸巳尤纯；柱中再有财官相得且无克夺，可取三台八座之贵。",
        "structure_type": ["pattern", "ten_gods", "use_god"],
        "element_vector": {"wood": 0, "fire": 1, "earth": 1, "metal": 0, "water": 1},
        "domain": ["career", "wealth", "fate"],
        "status": "active",
        "source_path": SOURCE_SANMING,
        "source_excerpt": "六壬生临午位，号曰禄马同乡，癸日坐向巳宫，乃是财官双美...人命禄马财官，难得兼全，况自坐支下，所以为贵...禄马同乡无克夺，财官同处最为荣，三台八座真奇贵。",
        "source_line": 102,
    },
    {
        "rule_id": "ZP-SRC-20260617-159",
        "theory_id": "ziping",
        "statement": "财官双美仍须随日主与月令取喜忌，秋生金旺可远害，寅卯旺则秀而不实，冬生水旺可贵；大贵命可合二三格局取之，不可以格多即作杂论。",
        "structure_type": ["pattern", "ten_gods", "use_god", "avoid_god"],
        "element_vector": {"wood": -1, "fire": 1, "earth": 1, "metal": 0, "water": 1},
        "domain": ["career", "wealth", "fate"],
        "status": "active",
        "source_path": SOURCE_SANMING,
        "source_excerpt": "喜秋生金旺永生木死，不能克土，故为远害。若见寅卯旺则秀而不实，冬生玄武当权，贵为王侯...大凡大贵命合三二格局取之，左右逢源，不可以格多为杂。",
        "source_line": 102,
    },
    {
        "rule_id": "ZP-SRC-20260617-160",
        "theory_id": "ziping",
        "statement": "日贵为日坐天乙贵人，贵气聚于日，得财食印相助与三六合、宅墓合、贵人财旺运则发福；忌刑冲破害、空亡、煞刃、魁罡加会，日夜还须分得体。",
        "structure_type": ["pattern", "ten_gods", "use_god", "avoid_god"],
        "element_vector": {"wood": 0, "fire": 0, "earth": 0, "metal": 0, "water": 0},
        "domain": ["career", "fate", "wealth", "personality"],
        "status": "active",
        "source_path": SOURCE_SANMING,
        "source_excerpt": "日贵者，自坐天乙是也...贵气聚于日，更有财食印相助，贵气为福。喜三六合宅墓合，行贵人财旺运，发福。大忌刑冲破害空亡...更见魁罡，定主贫夭。日贵须分昼夜。",
        "source_line": 103,
    },
    {
        "rule_id": "ZP-SRC-20260617-161",
        "theory_id": "ziping",
        "statement": "日德以五阳干特定日柱为格，合格者性慈稳厚、逢凶有救，运临身旺则奇；日德只宜一位并喜财官，重叠则不宜见财官及刑冲破害、空亡、魁罡。",
        "structure_type": ["pattern", "ten_gods", "use_god", "avoid_god"],
        "element_vector": {"wood": 0, "fire": 0, "earth": 0, "metal": 0, "water": 0},
        "domain": ["fate", "career", "personality", "health"],
        "status": "active",
        "source_path": SOURCE_SANMING,
        "source_excerpt": "日德此格止有五日：甲寅、丙辰、戊辰、庚辰、壬戌...若合日德，主为人性格慈善...逢凶有救，遇难有解...运临身旺，大是奇绝...此格只一位，喜财官，日德重叠，不宜见财官，及刑冲破害，空亡、魁罡会合加临。",
        "source_line": 104,
    },
    {
        "rule_id": "ZP-SRC-20260617-162",
        "theory_id": "ziping",
        "statement": "魁罡以庚辰、壬辰、戊戌、庚戌四日为格，重叠有情且行身旺运可发权贵，性聪明果断；一见财官或带刑煞冲克则祸重，但月令财官印绶得位时须斟酌提纲取用。",
        "structure_type": ["pattern", "ten_gods", "use_god", "avoid_god"],
        "element_vector": {"wood": 0, "fire": 0, "earth": 1, "metal": 1, "water": 1},
        "domain": ["career", "fate", "personality", "health"],
        "status": "active",
        "source_path": SOURCE_SANMING,
        "source_excerpt": "魁罡此格有四日：庚辰、壬辰、戊戌、庚戌...魁罡聚众，发福非常...运行身旺，发福百端，一见财官，祸患立至，或带刑煞尤甚...若月令见财官印绶，日主一位，即以财官印食取用。",
        "source_line": 105,
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
        "batch_id": "source_text_batch_013",
        "source_files": [SOURCE_SANMING],
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
        "batch_id": "source_text_batch_013",
        "source_files": [SOURCE_SANMING],
        "added_rule_ids": [rule["rule_id"] for rule in NEW_RULES],
    }
)

if BATCH12_SCRIPT.exists():
    BATCH12_SCRIPT.unlink()

dump_yaml(IR_PATH, ir)
dump_yaml(REPORT_PATH, report)

all_ids = [rule["rule_id"] for rule in all_rules]
assert len(all_rules) == 219, len(all_rules)
assert len(set(all_ids)) == len(all_ids)
assert all(rule.get("theory_id") == "ziping" for rule in all_rules)
assert "conflict_edges" not in ir
assert ir["enhancement"]["source_text_extraction"]["boundary"]["cross_school_fusion"] is False
assert ir["enhancement"]["source_text_extraction"]["boundary"]["conflict_edges_generated"] is False
assert ir["enhancement"]["source_text_extraction"]["boundary"]["rule_graph_updated"] is False
assert ir["enhancement"]["source_text_extraction"]["boundary"]["family_clustering"] is False
assert report["rule_count"] == 219
assert report_meta["added_rule_count"] == 162
print(f"BATCH13 OK added={len(NEW_RULES)} rule_count={len(all_rules)} coverage={coverage(all_rules)}")
print("boundary ok: ziping only; no conflict_edges; no cross-school fusion; batch12 temp cleaned")
