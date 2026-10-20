# T-108 · P0 构建链修复 + 门禁短路修复 + 分数归一化（同批执行）

## Review Level: 3

> 定级理由：重写 4 个 `theory/*/index.yaml`（生成产物），改动 `engine/predicates/condition_evaluator.py`
> 的核心门禁逻辑。这是**不可逆的数据重写**，且直接影响所有命盘的规则召回。
> 必须独立评审，不得自测自过。

## Context（中枢已独立复核，Worker 无需重复验证）

**基线数字（2026-10-19 22:10 实测）：**

| 派 | 总数 | 空 conclusion | 纯 § 指针 | 有 trigger | 有 score |
|---|---:|---:|---:|---:|---:|
| gao | 630 | 0 | 0 | 0 | 225 |
| duan | 428 | **290** | 0 | 0 | 290 |
| yang | 400 | 0 | **72** | 0 | **0** |
| ren | 200 | **194** | 0 | 0 | **0** |

**根因（已核实）：**

1. `tools/theory_content.py:10` 正则 `M[13]-[DR]-\d{3}` 漏掉杨派 `M2-Y`
2. 同文件第 38 行 `if not isinstance(data, dict): continue` 导致 YAML 列表块被丢弃
   （段派 `d-small-theory.md` 50 条、任派 `r05-r07-theory.md` 30 条）
3. `tools/build_indexes.py` 完全没有调用 `raw_rule_bodies`
4. `REN_SECTION_TO_TOPIC`（:340-361）章节关键词与实际标题不匹配，
   任派 144 条误标为 `lifa`
5. `build_indexes.py` 用 `os.popen("date -Iseconds")`，在 Windows 下写入非法文本
   `The system cannot accept the date entered.`

**为什么必须同批修门禁（关键）：**

`engine/predicates/condition_evaluator.py:209-211`：

```python
trigger = str(rule.get("condition") or rule.get("trigger") or "").strip()
if trigger:
    return evaluate_trigger(trigger, chart)   # ← 有 trigger 就直接返回
```

而 `evaluate_trigger` 只认 16 个英文枚举名（`always` / `has_zhi_chong` 等）。
**中文自然语言 trigger 会返回 False，并跳过后面的关键词兜底。**

实测后果（Gemini 在只读副本上验证）：
| 派 | P0 前通过数 | 仅 P0 后 |
|---|---:|---:|
| duan | 92 | **57**（降 35） |
| yang | 134 | **98**（降 36） |
| ren | 38 | 102（升 64） |

**所以 P0 单独执行是负优化。必须同批修门禁。**

## Objective

三件事一起做完，使：
1. 484 条空正文 + 72 条 § 指针恢复为真实正文
2. 415 条规则获得 trigger，且**不会因 trigger 短路导致召回退步**
3. 段派 3.0~5.0 分制归一化，排序恢复区分度

## 改动清单（4 个文件）

### 1. `tools/theory_content.py`（整文件替换）

按 Gemini 提供的完整实现，要点：
- `RULE_ID = re.compile(r"M[123]-[DRY]-\d{3}(?!\d)")`
- `_parse_yaml_rules()` 支持单字典 + 规则列表 + Markdown 混排容错
- `_format_trigger()` 把 dict 形式 trigger 规范为单行
- 第 141 行匹配用 `^[ \t]*-?[ \t]*rule_id:` 而非 `^\s*`
  （否则行号偏 1，触发 `tests/tools/test_wp7_toolchain.py:59` 断言失败）

### 2. `tools/build_indexes.py`（三段替换）

- 导入区加 `from tools.theory_content import raw_rule_bodies`
- `REN_SECTION_TO_TOPIC` 用精确短语（`"官运判定"` 而非 `"官运"`，
  避免把 §19.4 婚姻/官运/宫位操作体系误吸）
- 新增 `merge_raw_rule_bodies()` + 重写 `write_yaml()` + 重写 `main()`
- 修 `os.popen("date -Iseconds")` → `datetime.now().astimezone().isoformat(timespec="seconds")`
- `write_yaml` 探测现有文件行尾（`\r\n` vs `\n`）并沿用，
  避免 `core.autocrlf=true` 下全文件 diff

### 3. `engine/predicates/condition_evaluator.py:210`（门禁短路修复）

```python
# 改前
if trigger:
    return evaluate_trigger(trigger, chart)

# 改后
if trigger and trigger_evidence_status(trigger) == "evaluable":
    return evaluate_trigger(trigger, chart)
```

**未映射成英文枚举的自然语言 trigger，继续走下方关键词兜底。**

### 4. `engine/predicates/condition_evaluator.py:226`（分数归一化）

```python
# 改前
return min(float(rule.get("candidate_score") or 0.5), 1.0)

# 改后（>1.0 视为 5 分制，归一化到 [0,1]）
raw = float(rule.get("candidate_score") or 0.5)
return raw / 5.0 if raw > 1.0 else min(raw, 1.0)
```

## 执行顺序（严格按此顺序）

1. **先备份**到 `.p0_backup/`（6 个文件，见回滚方案）
2. 改 `tools/theory_content.py`
3. 改 `tools/build_indexes.py`
4. 改 `engine/predicates/condition_evaluator.py`（两处）
5. 跑 `python -m tools.build_indexes`
6. 跑 `python -m tools.query_theory --query "墓库" --rebuild-index`（刷新缓存）
7. 跑全部验证命令

## Completion Criteria（全部实跑并粘贴原始输出）

| # | 命令 | 期望 |
|---|---|---|
| 1 | 验证脚本（见下） | duan 空=0、yang §指针=0、ren 空=0；duan trigger=240、yang trigger=145、ren trigger=30 |
| 2 | 同脚本 | ren topics 含 `jiankang:38 / zhiye:13 / caiyun:12 / liuqin:10`，`lifa` 从 144 降到 71 |
| 3 | `python -m pytest -q` | **exit 0**，229 passed |
| 4 | `python -m pytest tests/tools -q -o addopts=""` | exit 0 |
| 5 | `python -m pytest tests/v5 -q -o addopts=""` | 与改前对比，失败数**不增加** |
| 6 | `python -m tools.rule_status_scan --check` | exit 0 |
| 7 | `git diff --stat` | 只含预期的 6 个文件（4 改 + 2 生成） |

### 验证脚本（直接用）

```bash
PYTHONIOENCODING=utf-8 python -c "
import re, yaml
from pathlib import Path
from collections import Counter
from tools.theory_content import raw_rule_bodies
SEC = re.compile(r'^§[\d.]+(?:/§[\d.]+)*\$')
for s in ('gao','duan','yang','ren'):
    rules = yaml.safe_load(Path(f'theory/{s}/index.yaml').read_text(encoding='utf-8'))['rules']
    e = sum(1 for r in rules if not str(r.get('conclusion') or '').strip())
    sec = sum(1 for r in rules if SEC.fullmatch(str(r.get('conclusion') or '').strip()))
    t = sum(1 for r in rules if str(r.get('trigger') or '').strip())
    sc = sum(1 for r in rules if r.get('candidate_score') is not None)
    print(f'{s:5s}: total={len(rules):3d} empty={e:3d} secptr={sec:2d} trigger={t:3d} score={sc:3d}')
    if s == 'ren':
        print('  topics:', dict(Counter(r.get('topic') for r in rules).most_common()))
"
```

## 回滚方案（必须执行）

```bash
python -c "
import shutil
from pathlib import Path
bak = Path('.p0_backup')
bak.mkdir(exist_ok=True)
for rel in ['tools/theory_content.py','tools/build_indexes.py',
            'engine/predicates/condition_evaluator.py',
            'theory/gao/index.yaml','theory/duan/index.yaml',
            'theory/yang/index.yaml','theory/ren/index.yaml']:
    dst = bak / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(rel, dst)
print('Backup saved to .p0_backup/')
"
```

`.p0_backup/` 要加进 `.gitignore`。

## Do NOT

- **禁止修改 `theory/ziping/index.yaml` 和 `theory/tiaohou_ditiansui/index.yaml`**
  （`build_indexes.py` 不处理它们，若出现 diff 说明改错了）
- **禁止改写已有非空 conclusion 的措辞**
  （只回填空串和纯 § 指针；已有实质结论一律保留）
- **禁止执行 `git commit` / `checkout` / `stash` / `reset` / `clean`**
- **禁止修改任何测试文件**
- **禁止扩大范围去改 `BLIND_TOPIC_DOMAINS` / 分桶配额 / ziping trigger 过滤**
  （那是 T-109，另立卡）
- 禁止在 Linux/WSL 下运行 `build_indexes.py`（会产生 `raw_file` 分隔符 diff）

## Deliverables

- 改后的 4 个文件
- 重跑生成的 4 个 `index.yaml`
- `tasks/T-108/BRIEF.md`：改前改后对比表、7 项验收原始输出、未完成与风险
- 更新 `tasks/T-108/STATUS.md`
