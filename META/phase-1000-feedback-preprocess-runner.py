import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path('.')
CASES_ROOT = ROOT / 'cases'
OUT_DIR = ROOT / 'META' / 'phase-1000-feedback-preprocess'
NORMALIZED_DIR = OUT_DIR / 'normalized-feedback'
FALLBACK_REASON = "ModuleNotFoundError('No module named tools')"

EMOJI_RE = re.compile('[✅❌🟡❓⚠️⏳🔴🟢🟠⭐★]')
BRACKET_RE = re.compile(r'\[\s*(y|n|\?|skip|pending|hit|miss|partial|unknown|命中|未命中|部分命中|待反馈)?\s*\]', re.I)
STMT_BRACKET_RE = re.compile(r'\[?(S[-A-Za-z0-9_]+)\]?\s*\[\s*(y|n|\?|skip|pending|hit|miss|partial|unknown|命中|未命中|部分命中|待反馈)?\s*\]', re.I)
MD_TABLE_SEP = re.compile(r'^\s*\|?\s*:?-{2,}:?')


def norm_verdict(raw: str | None, text: str = '') -> tuple[str, str, str]:
    s = (raw or '').strip().lower()
    t = text or ''
    if s in ('partial', '部分命中', '部分') or '🟡' in t or '部分' in t:
        pr = '部分命中'
        if any(w in t for w in ('时间', '年份', '差1年', '偏后', '偏前', '应期')):
            pr = '时间错'
        elif any(w in t for w in ('强度', '层级', '高估', '低估', '升星', '降权')):
            pr = '强度错'
        elif any(w in t for w in ('多断语', '复合', '拆分')):
            pr = '多断语'
        elif any(w in t for w in ('领域', 'domain', '方向')):
            pr = '领域错'
        return 'pending', pr, ''
    if s in ('y', 'hit', 'strong_hit', 'risk_hit', '命中', '应验') or '✅' in t or '应验' in t or ('命中' in t and '未命中' not in t):
        return 'y', '', ''
    if s in ('n', 'miss', '未命中', '失验') or '❌' in t or '失验' in t or '否认' in t:
        return 'n', '', ''
    if s in ('skip', '跳过') or 'skip' in t.lower() or '风险提示' in t:
        return 'skip', '', ''
    if s in ('?', 'pending', 'unknown', '待反馈', '') or '[ ]' in t or '⏳' in t or '未反馈' in t or '待验' in t or '未到' in t:
        unknown_reason = '未反馈'
        if '[ ]' in t or '空' in t:
            unknown_reason = '空字段'
        return 'pending', '', unknown_reason
    return 'pending', '', '其他'


def load_index(case_dir: Path) -> tuple[dict[str, dict], bool]:
    path = case_dir / 'statement_index.json'
    if not path.exists():
        return {}, False
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}, True
    statements = data.get('statements', []) if isinstance(data, dict) else []
    out: dict[str, dict] = {}
    if isinstance(statements, list):
        for item in statements:
            if isinstance(item, dict) and item.get('statement_id'):
                out[item['statement_id']] = item
    return out, True


def infer_rule_type(statement_id: str, stmt: dict) -> str:
    domain = str(stmt.get('domain', '')) if isinstance(stmt, dict) else ''
    summary = str(stmt.get('summary', '')) if isinstance(stmt, dict) else ''
    sid = statement_id.lower()
    if 'yq' in sid or '应期' in domain or re.search(r'20\d{2}|19\d{2}', summary):
        return 'TIMING'
    if any(k in domain for k in ('健康', '婚', '事业', '财', '学', '家庭')):
        return 'EVENT'
    if statement_id.startswith('UNMAPPED-'):
        return 'UNMAPPED'
    return 'GENERAL_PRINCIPLE'


def extract_signals(feedback_text: str, case_id: str) -> list[tuple[str, str, str, str, str, str]]:
    signals: list[tuple[str, str, str, str, str, str]] = []
    for match in STMT_BRACKET_RE.finditer(feedback_text):
        sid = match.group(1)
        raw = match.group(2) or ''
        line_start = feedback_text.rfind('\n', 0, match.start()) + 1
        line_end = feedback_text.find('\n', match.end())
        if line_end == -1:
            line_end = len(feedback_text)
        line = feedback_text[line_start:line_end].strip()
        verdict, partial_reason, unknown_reason = norm_verdict(raw, line)
        signals.append((sid, verdict, partial_reason, unknown_reason, line, 'annotation'))

    for line in feedback_text.splitlines():
        if not line.strip().startswith('|') or MD_TABLE_SEP.match(line):
            continue
        cells = [cell.strip().strip('`') for cell in line.strip().strip('|').split('|')]
        sid = None
        for cell in cells[:2]:
            mm = re.search(r'(S[-A-Za-z0-9_]+)', cell)
            if mm:
                sid = mm.group(1)
                break
        if not sid:
            continue
        if any(sid == existing[0] and line.strip() == existing[4] for existing in signals):
            continue
        verdict_cell = ''
        for cell in cells:
            if BRACKET_RE.search(cell) or any(token in cell for token in ('✅', '❌', '🟡', '⏳', 'pending', 'hit', 'miss', '待反馈', '未反馈', '应验', '失验', '部分')):
                verdict_cell = cell
        verdict, partial_reason, unknown_reason = norm_verdict(verdict_cell, line)
        signals.append((sid, verdict, partial_reason, unknown_reason, line.strip(), 'table'))

    if not signals and feedback_text.strip():
        for line_no, line in enumerate(feedback_text.splitlines(), 1):
            if any(token in line for token in ('[y]', '[n]', '[?]', '[skip]', '✅', '❌', '🟡', '⏳', 'pending', 'unknown', 'hit', 'miss')):
                sid = f'UNMAPPED-{case_id}-{line_no:04d}'
                verdict, partial_reason, unknown_reason = norm_verdict('', line)
                signals.append((sid, verdict, partial_reason, unknown_reason, line.strip(), 'unmapped_line'))
    return signals


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)

    case_dirs = sorted([p for p in CASES_ROOT.iterdir() if p.is_dir() and p.name.startswith('C-2026-')])
    paired = [p for p in case_dirs if (p / 'input.md').exists()]
    phase_cases = paired[:100]

    rows: list[dict[str, str]] = []
    case_summary: list[dict] = []

    for case_dir in phase_cases:
        case_id = case_dir.name
        feedback_path = case_dir / 'feedback.md'
        input_exists = (case_dir / 'input.md').exists()
        feedback_exists = feedback_path.exists()
        statement_index, statement_index_exists = load_index(case_dir)
        feedback_text = feedback_path.read_text(encoding='utf-8', errors='ignore') if feedback_exists else ''

        # P4-2 已判定 Phase 候选 fallback 原因为 tools import path；本轮只做标记，不修复入口。
        fallback = True
        signals = extract_signals(feedback_text, case_id)

        normalized_lines = [
            '| statement_id | verdict | partial_reason | unknown_reason | evidence_note | reviewer |',
            '|---|---|---|---|---|---|',
        ]

        for sid, verdict, partial_reason, unknown_reason, note, source in signals:
            stmt = statement_index.get(sid, {})
            rule_ids = []
            if isinstance(stmt, dict):
                raw_rule_ids = stmt.get('rule_ids') or stmt.get('rules') or []
                if isinstance(raw_rule_ids, str):
                    rule_ids = [raw_rule_ids]
                elif isinstance(raw_rule_ids, list):
                    rule_ids = [str(x) for x in raw_rule_ids]
            if not rule_ids:
                rule_ids = ['UNMAPPED']

            learnable = verdict in ('y', 'n') and sid in statement_index and rule_ids != ['UNMAPPED']
            if learnable:
                rule_type = infer_rule_type(sid, stmt)
                lane = 'timing' if rule_type == 'TIMING' else 'event'
            elif partial_reason:
                lane = {
                    '时间错': 'timing',
                    '强度错': 'strength',
                    '领域错': 'domain',
                    '多断语': 'non_learning',
                    '部分命中': 'event',
                }.get(partial_reason, 'non_learning')
            else:
                lane = 'non_learning'

            domain = stmt.get('domain', 'UNMAPPED') if isinstance(stmt, dict) else 'UNMAPPED'
            rule_type = infer_rule_type(sid, stmt) if isinstance(stmt, dict) else 'UNMAPPED'
            for rule_id in rule_ids:
                rows.append({
                    'case_id': case_id,
                    'rule_id': rule_id,
                    'statement_id': sid,
                    'feedback_verdict': verdict,
                    'partial_reason': partial_reason,
                    'unknown_reason': unknown_reason,
                    'learnable': str(bool(learnable)).lower(),
                    'learning_lane': lane,
                    'source': source,
                    'domain': domain,
                    'school': 'UNMAPPED',
                    'family': 'UNMAPPED',
                    'rule_type': rule_type,
                    'needs_mapping_repair': str(rule_id == 'UNMAPPED' or sid not in statement_index).lower(),
                    'case_feedback_missing': str(not feedback_exists).lower(),
                    'case_fallback': str(fallback).lower(),
                    'fallback_reason': FALLBACK_REASON,
                })

            clean_note = EMOJI_RE.sub('', note or '').replace('|', '/').replace('\n', ' ')
            normalized_lines.append(f'| `{sid}` | `{verdict}` | {partial_reason} | {unknown_reason} | {clean_note} | preprocess |')

        (NORMALIZED_DIR / f'{case_id}-feedback.normalized.md').write_text('\n'.join(normalized_lines) + '\n', encoding='utf-8')

        case_summary.append({
            'case_id': case_id,
            'input_exists': input_exists,
            'feedback_exists': feedback_exists,
            'statement_index_exists': statement_index_exists,
            'statement_count': len(statement_index),
            'feedback_signal_count': len(signals),
            'has_y_n': any(signal[1] in ('y', 'n') for signal in signals),
            'fallback_flag': fallback,
            'fallback_reason': FALLBACK_REASON,
            'needs_repair': (not feedback_exists or fallback or len(signals) == 0 or not statement_index_exists),
        })

    csv_path = OUT_DIR / 'rule_statement_verdict_map.csv'
    fields = [
        'case_id', 'rule_id', 'statement_id', 'feedback_verdict', 'partial_reason', 'unknown_reason',
        'learnable', 'learning_lane', 'source', 'domain', 'school', 'family', 'rule_type',
        'needs_mapping_repair', 'case_feedback_missing', 'case_fallback', 'fallback_reason',
    ]
    with csv_path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    json_path = OUT_DIR / 'rule_statement_verdict_map.json'
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')

    case_path = OUT_DIR / 'case_feedback_preprocess_audit.json'
    case_path.write_text(json.dumps(case_summary, ensure_ascii=False, indent=2), encoding='utf-8')

    verdict_counts = Counter(row['feedback_verdict'] for row in rows)
    school_stats = Counter(row['school'] for row in rows)
    family_stats = Counter(row['family'] for row in rows)
    rule_type_stats = Counter(row['rule_type'] for row in rows)
    case_counts = Counter()
    for item in case_summary:
        case_counts['total_cases'] += 1
        case_counts['paired_input_feedback'] += 1 if item['input_exists'] and item['feedback_exists'] else 0
        case_counts['missing_feedback'] += 1 if not item['feedback_exists'] else 0
        case_counts['missing_statement_index'] += 1 if not item['statement_index_exists'] else 0
        case_counts['zero_feedback_signal'] += 1 if item['feedback_signal_count'] == 0 else 0
        case_counts['cases_with_any_feedback_signal'] += 1 if item['feedback_signal_count'] > 0 else 0
        case_counts['cases_with_y_n'] += 1 if item['has_y_n'] else 0
        case_counts['fallback_cases'] += 1 if item['fallback_flag'] else 0

    learnable_rows = sum(1 for row in rows if row['learnable'] == 'true')
    repair_rows = sum(1 for row in rows if row['needs_mapping_repair'] == 'true')
    needs_repair_cases = sum(1 for item in case_summary if item['needs_repair'])

    summary_path = ROOT / 'META' / 'phase-1000-feedback-preprocess-summary.md'
    md: list[str] = []
    md.append('# Phase-1000 Feedback Sample Pre-Processing Summary')
    md.append('')
    md.append('> 范围：正式 `cases/C-2026-*` 目录中具备 `input.md` 的前 100 个 Phase-1000 候选；只生成标准化副本与映射表，不改写原始 `cases/*`、`theory/*`、`engine/*`、`tests/*`、`META/project-state.json`。')
    md.append('')
    md.append('## 1. 输出产物')
    md.append('')
    md.append(f'- 映射 CSV：`{csv_path.as_posix()}`')
    md.append(f'- 映射 JSON：`{json_path.as_posix()}`')
    md.append(f'- case 审计 JSON：`{case_path.as_posix()}`')
    md.append(f'- 标准化 feedback 副本目录：`{NORMALIZED_DIR.as_posix()}/`')
    md.append('')
    md.append('## 2. 案例覆盖率')
    md.append('')
    md.append('| metric | value |')
    md.append('|---|---:|')
    for key in ['total_cases', 'paired_input_feedback', 'missing_feedback', 'missing_statement_index', 'cases_with_any_feedback_signal', 'zero_feedback_signal', 'cases_with_y_n', 'fallback_cases']:
        md.append(f'| `{key}` | {case_counts[key]} |')
    md.append(f'| `feedback_signal_rows` | {len(rows)} |')
    md.append(f'| `learnable_rows` | {learnable_rows} |')
    md.append(f'| `mapping_repair_rows` | {repair_rows} |')
    md.append('')
    md.append('## 3. verdict 标准化状态')
    md.append('')
    md.append('| verdict | rows |')
    md.append('|---|---:|')
    for verdict in ['y', 'n', 'skip', 'pending']:
        md.append(f'| `{verdict}` | {verdict_counts[verdict]} |')
    md.append('')
    md.append('说明：旧 `[?]`、空 `[ ]`、`unknown`、`待反馈`、`⏳ pending` 统一映射为 `pending`；`partial` / `🟡` 不保留为顶层 verdict，按 P4-2 写入 `partial_reason` 并默认不进入可学习样本。')
    md.append('')
    md.append('## 4. 缺失 / fallback 案例统计')
    md.append('')
    md.append('| category | count | action |')
    md.append('|---|---:|---|')
    md.append(f'| feedback 缺失 | {case_counts["missing_feedback"]} | 待补 `feedback.md` |')
    md.append(f'| 零反馈信号 | {case_counts["zero_feedback_signal"]} | 待按 v1.3 表补充 `statement_id/verdict` |')
    md.append(f'| statement_index 缺失 | {case_counts["missing_statement_index"]} | 待回填 `statement_index.json` |')
    md.append(f'| fallback 标记 | {case_counts["fallback_cases"]} | 待修复：`{FALLBACK_REASON}` |')
    md.append('')
    md.append('## 5. 覆盖不足统计')
    md.append('')
    md.append('### 5.1 School')
    md.append('')
    md.append('| school | rows | note |')
    md.append('|---|---:|---|')
    for key, value in school_stats.most_common():
        md.append(f'| `{key}` | {value} | 当前 `statement_index.json` 多数未携带 school 字段，需后续回填 |')
    md.append('')
    md.append('### 5.2 Family')
    md.append('')
    md.append('| family | rows | note |')
    md.append('|---|---:|---|')
    for key, value in family_stats.most_common():
        md.append(f'| `{key}` | {value} | 当前 `statement_index.json` 多数未携带 family 字段，暂不可做 family posterior |')
    md.append('')
    md.append('### 5.3 Rule Type')
    md.append('')
    md.append('| rule_type | rows |')
    md.append('|---|---:|')
    for key, value in rule_type_stats.most_common():
        md.append(f'| `{key}` | {value} |')
    md.append('')
    md.append('### 5.4 案例数')
    md.append('')
    md.append('| bucket | case_count |')
    md.append('|---|---:|')
    md.append(f'| 有任一反馈信号 | {case_counts["cases_with_any_feedback_signal"]} |')
    md.append(f'| 有明确 y/n | {case_counts["cases_with_y_n"]} |')
    md.append(f'| 待补或待修复 | {needs_repair_cases} |')
    md.append('')
    md.append('## 6. 结论')
    md.append('')
    md.append('本轮完成了 Phase-1000 候选反馈字段的标准化预处理与 `rule_id -> statement_id -> verdict` 映射输出。当前最大阻塞仍是 fallback 环境标记与 rule 映射不足：大量断语缺少可学习 `rule_id`，因此本批输出只能作为动态置信度引擎读取前的清洗副本与修复队列，不能直接解冻规则 posterior 自动更新。')
    summary_path.write_text('\n'.join(md) + '\n', encoding='utf-8')

    print(json.dumps({
        'cases': len(phase_cases),
        'rows': len(rows),
        'learnable_rows': learnable_rows,
        'summary': summary_path.as_posix(),
        'csv': csv_path.as_posix(),
        'json': json_path.as_posix(),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
