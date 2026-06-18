import yaml
from pathlib import Path
from collections import Counter

root = Path('theory/ziping')
source_path = root / 'index.yaml'
out_dir = root / '_cleaned'
out_dir.mkdir(parents=True, exist_ok=True)
data = yaml.safe_load(source_path.read_text(encoding='utf-8'))
rules = data.get('rules', [])
by_id = {r['id']: r for r in rules}

cluster_specs = [
    ('ZP-CLEAN-CLUSTER-001', ['ZP-PROD-20260605-001', 'ZP-PROD-20260605-005'], '子平判断应先定位用神，并围绕用神是否成立、受护或受破来评估格局成败、整体吉凶与事业财富层次。', 'yongshen_global_success_failure', 'claim语义等价：均以用神为全局裁断核心，结论均指向格局成败与整体吉凶。'),
    ('ZP-CLEAN-CLUSTER-002', ['ZP-PROD-20260605-003', 'ZP-PROD-20260606-002'], '子平取用与成格先后应优先依据月令提纲，并结合透干、藏干、旺相休囚与通月气情况判断。', 'yueling_tigang_priority', 'claim语义等价：月令、提纲均作为旺衰取用与先后次序的核心依据。'),
    ('ZP-CLEAN-CLUSTER-003', ['ZP-PROD-20260605-004', 'ZP-PROD-20260606-004'], '普通格局须先判日主强弱，再按日主承载力、十神状态、通月气与制化关系决定取用方向，不可只按十神名义定吉凶。', 'shenqiang_shenruo_shishen_quyong', '十神结构一致但表达不同：均要求以身强身弱和制化状态决定取用。'),
    ('ZP-CLEAN-CLUSTER-004', ['ZP-PROD-20260605-007', 'ZP-PROD-20260605-013'], '格局或官格判断须看清纯与混杂：结构纯一、财印相生和护卫顺畅者层级较高，伤官七杀或异神混杂且无制化者层次下降。', 'geju_chunza_zhengguan_purity', '格局判断重复表达：一条为格局纯杂总则，一条为正官格清纯的条件化展开。'),
    ('ZP-CLEAN-CLUSTER-005', ['ZP-PROD-20260605-008', 'ZP-PROD-20260605-015'], '格局层级应综合用神有情、纯杂、相神、护卫与救应判断；用神顺接且护卫周全者层级提高，单点证据不足时不宜定高低。', 'geju_level_youqing_composite', '条件不同但结论相同：均指向格局高低不能单看用神存在，而要看有情、护卫、纯杂与救应。'),
    ('ZP-CLEAN-CLUSTER-006', ['ZP-PROD-20260605-014', 'ZP-PROD-20260606-010'], '从格、化格、从势、专旺及飞天禄马、壬骑龙背、魁罡、合化等特殊格须先验真成、得令与未破，再决定是否另按特殊取用和贵气判断。', 'special_geju_authenticity', '条件不同但结论相同：均强调特殊格不能机械套普通扶抑或见名即贵，必须先辨真伪破成。'),
    ('ZP-CLEAN-CLUSTER-007', ['ZP-PROD-20260605-016', 'ZP-PROD-20260606-011'], '原局成败须与大运流年分层处理，运岁可放大、修复或逆转用神、相神、忌神、库与合冲刑害所对应的成败状态。', 'yunshi_geju_transformation', 'claim语义等价：均表达静态格局不能替代动态运岁判断，成败可随运岁转化。'),
    ('ZP-CLEAN-CLUSTER-008', ['ZP-PROD-20260605-002', 'ZP-PROD-20260605-017'], '财星、官星的多少只提供结构信息，财富和事业判断仍须回到身财承载、取用、制化、生护与成格条件。', 'wealth_official_quantity_quyong', '条件不同但结论相同：均反对只看财官数量，要求回到承载、取用、制化和成格。'),
    ('ZP-CLEAN-CLUSTER-009', ['ZP-PROD-20260606-030', 'ZP-PROD-20260606-032'], '金局用火须分阶段：金未成器时喜适度火炼成形，金已成器后再遇强火则需提示过度锻炼、压力变形或伤损风险。', 'jinhuo_chengqi_stage', 'conditional_variation：一条说明金需火炼成器，一条限定成器后不欲再火，合并为阶段性规则。'),
    ('ZP-CLEAN-CLUSTER-010', ['ZP-PROD-20260618-019', 'ZP-PROD-20260618-020', 'ZP-PROD-20260618-021'], '六亲、配偶与子息判断须看对应星位或宫位所坐之地及生助冲克；坐生旺库、禄马、贵人、官印且受生者助力提高，坐空亡、刑克煞、羊刃、死绝、冲败者风险提高。', 'liuqin_spouse_children_star_location', '十神结构一致但对象不同：父母兄弟、妻妾、子息均使用星位坐地旺衰贵煞与生助冲克结构。'),
    ('ZP-CLEAN-CLUSTER-011', ['ZP-PROD-20260618-014', 'ZP-PROD-20260618-015'], '七煞与时上偏官须校验数量、清透、身旺身弱与制伏轻重；一位清透且制伏得宜可成权用，重见或制伏失衡则劳碌受限，制太过者喜煞旺运恢复权用。', 'qisha_zhifu_shishang_pianguan', 'partial_overlap：时上偏官规则内含七煞制伏太过喜煞旺运，与七煞制伏轻重规则重复。'),
]
clustered = {rid for _, ids, _, _, _ in cluster_specs for rid in ids}

def avg(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else 0.0

def star_from_percent(p):
    if p >= 0.85: return 5
    if p >= 0.65: return 4
    if p >= 0.45: return 3
    if p >= 0.25: return 2
    return 1

def confidence_for(rule_ids):
    items = [by_id[i] for i in rule_ids]
    n = len(items)
    base = avg([(r.get('confidence') or {}).get('percent') for r in items])
    posterior_base = avg([(r.get('confidence') or {}).get('posterior') for r in items])
    variance_base = avg([(r.get('confidence') or {}).get('variance') for r in items])
    penalty = 0.0 if n == 1 else min(0.05 * (n - 1), 0.25)
    adjusted = round(base * (1 - penalty), 4)
    posterior = round(posterior_base * (1 - penalty), 4)
    return {'base': round(base, 4), 'posterior_base': round(posterior_base, 4), 'variance': round(variance_base + (0.02 * (n - 1)), 4), 'redundancy_penalty': round(penalty, 4), 'percent': adjusted, 'posterior': posterior, 'star': star_from_percent(adjusted), 'cluster_size': n}

def domains_for(rule_ids):
    seen = []
    for rid in rule_ids:
        for d in by_id[rid].get('domains', []) or []:
            if d not in seen:
                seen.append(d)
    return seen

def structure_type_for(rule):
    topic = str(rule.get('topic') or '')
    if any(k in topic for k in ['yongshen', 'yueling', 'shenqiang', 'quyong']): return 'quyong_framework'
    if any(k in topic for k in ['geju', 'guan', 'qisha', 'guansha', 'shangguan']): return 'geju_shishen_structure'
    if any(k in topic for k in ['dayun', 'yun', 'liunian', 'sui', 'yingqi', 'xiaoyun']): return 'timing_trigger_structure'
    if any(k in topic for k in ['he_', 'chong', 'xing', 'hai', 'sanhe', 'sanxing', 'kongwang']): return 'interaction_trigger_structure'
    if any(k in topic for k in ['wuxing', 'mu_', 'huo', 'tu', 'jin', 'shui', 'jia', 'yi', 'bing', 'ding', 'wu', 'ji', 'geng', 'xin', 'ren', 'gui']): return 'wuxing_seasonal_structure'
    if any(k in topic for k in ['liuqin', 'qiqie', 'zixi', 'nvming', 'guchen', 'guasu']): return 'kinship_family_structure'
    if any(k in topic for k in ['zaisha', 'goujiao', 'tianluodiwang', 'shie']): return 'shensha_risk_structure'
    return 'atomic_rule_structure'

clean_rules = []
merge_clusters = []
merge_map = {'source_file': 'theory/ziping/index.yaml', 'cluster_id_to_rule_ids': {}, 'merge_clusters': []}
for idx, (cluster_id, rids, statement, structure_type, reason) in enumerate(cluster_specs, 1):
    clean_id = f'ZP-CLEAN-20260618-{idx:03d}'
    clean_rules.append({'rule_id': clean_id, 'original_rule_ids': rids, 'statement': statement, 'domains': domains_for(rids), 'structure_type': structure_type, 'confidence_adjusted': confidence_for(rids)})
    cluster = {'cluster_id': cluster_id, 'merged_rule': {'rule_id': clean_id, 'statement': statement, 'source_rules': rids}, 'preservation': {'original_rule_ids': rids, 'source_excerpts': [{'rule_id': rid, 'path': (by_id[rid].get('source') or {}).get('path'), 'excerpt': (by_id[rid].get('source') or {}).get('excerpt')} for rid in rids]}, 'merge_reason': reason}
    merge_clusters.append(cluster)
    merge_map['cluster_id_to_rule_ids'][cluster_id] = rids
    merge_map['merge_clusters'].append(cluster)

next_idx = len(cluster_specs) + 1
for r in rules:
    if r['id'] in clustered:
        continue
    clean_rules.append({'rule_id': f'ZP-CLEAN-20260618-{next_idx:03d}', 'original_rule_ids': [r['id']], 'statement': (r.get('output') or {}).get('statement') or r.get('claim') or r.get('title'), 'domains': r.get('domains') or [], 'structure_type': structure_type_for(r), 'confidence_adjusted': confidence_for([r['id']])})
    next_idx += 1

conflict_tags = [
    {'rule_a': 'ZP-PROD-20260605-004', 'rule_b': 'ZP-PROD-20260605-014', 'type': 'conditional_variation'},
    {'rule_a': 'ZP-PROD-20260605-009', 'rule_b': 'ZP-PROD-20260605-004', 'type': 'conditional_variation'},
    {'rule_a': 'ZP-PROD-20260606-030', 'rule_b': 'ZP-PROD-20260606-032', 'type': 'conditional_variation'},
    {'rule_a': 'ZP-PROD-20260605-011', 'rule_b': 'ZP-PROD-20260605-012', 'type': 'conditional_variation'},
    {'rule_a': 'ZP-PROD-20260605-006', 'rule_b': 'ZP-PROD-20260605-005', 'type': 'conditional_variation'},
    {'rule_a': 'ZP-PROD-20260606-037', 'rule_b': 'ZP-PROD-20260606-038', 'type': 'partial_overlap'},
    {'rule_a': 'ZP-PROD-20260605-013', 'rule_b': 'ZP-PROD-20260618-016', 'type': 'partial_overlap'},
    {'rule_a': 'ZP-PROD-20260618-007', 'rule_b': 'ZP-PROD-20260606-003', 'type': 'partial_overlap'},
]
before = len(rules)
after = len(clean_rules)
merged_domains = Counter()
for _, rids, _, _, _ in cluster_specs:
    for d in domains_for(rids):
        merged_domains[d] += 1
report_doc = {'total_rules_before': before, 'total_clusters_found': len(cluster_specs), 'redundancy_ratio': round((before - after) / before, 4), 'merged_rules_count': after, 'conflict_density': round(len(conflict_tags) / before, 4), 'high_redundancy_domains': [d for d, n in merged_domains.most_common() if n >= 3], 'merge_clusters': merge_clusters, 'conflict_tags': conflict_tags}
cleaned_doc = {'schema_version': 'ziping-cleaned-rules-2026-06-18', 'source_file': 'theory/ziping/index.yaml', 'expert_system': 'ziping', 'clean_rules': clean_rules}
merge_map['total_clusters_found'] = len(cluster_specs)
for path, doc in [(out_dir / 'index_cleaned.yaml', cleaned_doc), (root / '_cleaning_report.yaml', report_doc), (root / '_merge_map.yaml', merge_map)]:
    path.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=120), encoding='utf-8')
print({'before': before, 'after': after, 'clusters': len(cluster_specs), 'redundancy_ratio': round((before - after) / before, 4), 'conflicts': len(conflict_tags)})
