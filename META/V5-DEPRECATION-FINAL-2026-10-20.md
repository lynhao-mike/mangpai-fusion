# v5 报告生成废弃 · 终稿（待 Gemini 审核）

> 本文档是 Opus v5 终稿 + Claude 四轮核实的合并结论。
> 所有删除候选都经过外部调用验证（`grep -rnE "\b<name>\b"`，排除自身文件）。
> 生成时间：2026-10-20 15:55

---

## 一、战略结论（Opus 提出，Claude 认同）

### 1.1 核心判断

**废弃 `engine/v5` 的报告渲染层，保留引擎和输入解析。**

理由：
1. `report_view.py` 有 **22 处硬编码桩文本**（「MVP 阶段待细化」「待反馈细分学校层级」），
   违背第一性原则（证据链可追溯）
2. `engine.cli` + Agent 路线已有正面样板
   （`reports/1980-02-09-乾-庚申戊寅壬子辛丑-human-report.md`，
   带 `e001`/`e005` 边号、`M1-D-045`/`G-XF-014` 规则 ID、
   明确分层「板上钉钉/大概率主断/我不编的」）
3. **两条链必须并存，不应强行融合**（详见 1.3）

### 1.2 两条链的职责分工（实测确认）

| 维度 | `engine.cli` | `engine/v5/runner` |
|---|---|---|
| 服务对象 | **Agent**（人话综合推理） | **度量链**（balanced_accuracy） |
| 输入 | `--birth` / `--pillars` 字符串 | `input.md` 文件路径 |
| 输出 | `chart/relations/strength/shensha/structures/duan_zuogong` | `V5Claim/V5Output` dataclass |
| 无状态性 | 纯函数，不读文件 | 需读 `input.md` + 规则索引 |
| 测试 | `pytest -q` 229 passed | `tests/v5` + `tests/r10` |
| 对 `engine.facts` 的引用 | **本身就是 facts** | **零 import** |

### 1.3 为什么必须并存（Claude 实测，Opus 认同）

**`engine.cli all --json` 的输出无法喂给 `run_v5`**：

```
CLI 输出 keys:   chart, relations, strength, shensha, structures, duan_zuogong
run_v5 需要:     case_id, current_dayun, current_year, {y,m,d,h}_{stem,branch},
                 dayun_summary, gender_marker, pillars, source_input, start_luck
```

**零交集。** 且 CLI 没有 `--input` 参数（只有 `--birth`/`--pillars`/`--gender`），
不提供 `current_dayun`/`start_luck`/`dayun_summary`。

强行融合需 50-80 行适配器 + 重复 40 行解析逻辑 + 破坏 CLI 无状态定位。**代价 > 收益。**

---

## 二、待删清单（全部经过外部调用验证）

### 2.1 第一层：零调用，可直接删（无风险）

| 函数 | 文件 | 外部调用 | 判定 |
|---|---|---|---|
| `_arbitration_by_domain` | `report_view.py:81` | **0** | 删 |
| `_claims_by_domain_school` | `report_view.py:88` | **0** | 删 |
| `_l7_school_evidence_for_domain` | `report_view.py:170` | **0** | 删 |
| `_l7_conflict_for_domain` | `report_view.py:193` | **0** | 删 |
| `_first_prediction` | `report_view.py:101` | **0** | 删 |
| `_prediction_window` | `report_view.py:108` | **0** | 删 |
| `_prediction_trigger` | `report_view.py:114` | **0** | 删 |
| `_prediction_probability` | `report_view.py:120` | **0** | 删 |
| `_prediction_confidence_state` | `report_view.py:127` | **0** | 删 |
| `_prediction_star` | `report_view.py:137` | **0** | 删 |
| `_prediction_falsifier` | `report_view.py:143` | **0** | 删 |
| `_prediction_feedback` | `report_view.py:149` | **0** | 删 |
| `_extract_yaml_front_matter` | `preprod.py:109` | **0** | 删 |
| `_report_relative_path` | `preprod.py:198` | **0** | 删 |

**Claude 的修正**：Opus 原来说 `_prediction_feedback` 有 28 处调用、`_prediction_probability` 有 2 处，
那是**子串误匹配**（匹配到 `log_prediction_feedback` / `collect_prediction_feedbacks` /
`parse_prediction_feedback` 等）。用 `\b` 边界精确匹配后为 **0**。
（Claude 差点又犯「把数字当结论」的错，特此记录）

**预期删除**：约 150 行

### 2.2 第二层：有测试调用，无生产调用（删函数 + 删/改测试）

| 函数 | 文件 | 调用方 |
|---|---|---|
| `_l7_conclusion_for_domain` | `report_view.py:211` | `tests/v5/test_report_reads_l7.py`（8 测试） |
| `build_comparison_summary` | `report_view.py:562` | `tests/v5/test_report_view.py`（5 测试） |
| `build_report_context_from_frozen_run` | `report_view.py:477` | `tests/v5/test_report_view.py` |

**预期删除**：约 230 行 + 删约 13 个测试

### 2.3 第三层：有生产调用，需先处理依赖

| 函数 | 文件 | 调用方 | 处理方式 |
|---|---|---|---|
| `build_report_v6_context` | `report_view.py:253` | `engine/v5/__init__.py`（export）、`tools/render_report.py`、`tests/r10`、`tests/test_archive_links.py`、`tests/v5/test_report_reads_l7.py` | **待 Opus 回答矛盾 3** |
| `render_report_v6_from_output` | `report_view.py:404` | `engine/v5/__init__.py`（export）、`tools/render_report.py` | 同上传 |
| `render_v6_preprod_case` | `preprod.py:215` | `engine/application/production_service.py:165`（默认 `render_v6_preprod=False`）、`tools/render_report_v6.py`、`tests/r10`、`tests/v5/test_manifest_isolation.py`、`tests/v5/test_report_reads_l7.py` | **待 Opus 回答矛盾 2/3** |
| `render_v6_preprod_cases` | `preprod.py:323` | `tools/render_report_v6.py` | 同上传 |

### 2.4 明确保留（Opus 第三轮已修正，Claude 认同）

| 函数 | 文件 | 保留理由 |
|---|---|---|
| `build_chart_from_input` | `preprod.py:120` | **`run_v5` 的唯一输入适配器**，CLI 无法替代 |
| `_parse_*` 系列（8 个） | `preprod.py:29-106` | `build_chart_from_input` 的依赖 |
| `_display_path` | `preprod.py:191` | **`build_chart_from_input` 第 256 行调用它** |

**Claude 的修正**：Opus 在 v5 终稿里把 `_display_path` 列入「报告专用」删除，
但它被 `build_chart_from_input` 调用（第 256 行 `chart["source_input"] = _display_path(...)`）。
保留 `build_chart_from_input` 就必须保留 `_display_path`。

---

## 三、三个未决矛盾（需 Opus 回答后才可执行第二、三层）

### 矛盾 1：`tools/render_report.py` 是独立渲染器，不是薄包装

Opus v5 终稿写「render_report.py 改用 CLI + Agent（约 20 行）」。
Claude 实测：它自己实现 Jinja for/if/变量替换（`_FOR_BLOCK_RE`/`_IF_INNER_RE`/`_VAR_RE`），
还依赖 `engine.yingqi`、`engine.statement_runtime`、`engine.picture`、`engine.predicates.cycles`。

**这是 400+ 行的模板渲染器，不是调用 report_view 的包装。**

**选项**：A 直接删除 / B 重写为 CLI / C 保留并因此不能删它依赖的 report_view 函数

### 矛盾 2：`render_v6_preprod` 进了 cache key

```python
def _compute_cache_key(input_sha256, render, template_name, render_v6_preprod=False) -> str
```

移除它会：
- 变更 HTTP API 契约（`tools/production_api.py` 的 schema）
- 使所有已缓存条目失效
- 删除 `summary["v6_preprod_rendered"]` 输出字段

**选项**：A 直接删参数 / B 保留参数但 no-op（更安全的降级）

### 矛盾 3：`tests/r10` 依赖要删的报告函数

`tests/r10/test_r10_ziping_career_acceptance.py` 同时调用
`render_v6_preprod_case` 和 `build_report_v6_context`。

Opus v5 终稿声称「`pytest tests/r10` → 60 passed, 4 failed（不变）」，
**这在删除这两个函数后不可能成立**。

**选项**：A 保留最小可用子集供度量测试 / B 改写度量测试断言结构化数据（需用户授权）

---

## 四、建议的执行顺序（Claude 提出，待 Opus 确认）

```
1. 第二层之「断点 4 域重分类」（+20 行）  ← Opus 认定的唯一必修，且 Agent 走 CLI 时直接用到
2. 第一层零调用删除（-150 行）            ← 零风险，随时可做
3. CLI picture 子命令（+30 行）           ← 补全事实底座，独立
4. 第二、三层报告渲染删除（-460 行）       ← 等 3 个矛盾有答案
```

**理由**：断点 4 影响 `tools/query_theory.py` 的域检索，是 Agent 直接消费的；
删代码只是清洁工作，优先级应低于「让 Agent 拿到更准的证据」。

---

## 五、断点 4 的具体内容（Opus 认定唯一必修）

### 5.1 问题

`BLIND_TOPIC_DOMAINS`（`engine/v5/runner.py:52-69`）把方法论和时间维度映射成事件域：

```
事业域 563 条（A 类实测）
├─ lifa（理法）448 条   ← 「月令为提纲」「盲派三大支柱体系」
├─ dayun（大运）75 条   ← 时间维度
└─ zhiye（真实事业）40 条 = 7.1%
```

### 5.2 修复方向

| topic | 现状 | 改为 | 理由 |
|---|---|---|---|
| `lifa` | 事业 | **总体** | 论命总纲/方法论，不是事件 |
| `dayun` | 事业 | **总体** | 时间维度，跨域通用 |
| `shensha` | 健康 | **删除映射**（落兜底） | 150 条中 83 条（55.3%）语义不符 |
| `liuqin` | 无映射 | **总体** | 34 条六亲规则，避免落入命主健康/财富账本 |
| `geju` | 无映射 | **总体** | 117 条格局规则 |
| `jiaoyu` | 无映射 | **学业** | 12 条，当前被「财」字抓去财富 |

### 5.3 Gemini 曾指出的风险（需复核）

`_blind_rule_domain`（`runner.py:434-445`）用 `if key.lower() in haystack` **子串匹配**，
不是精确匹配。改映射表时需同步改为精确匹配，否则会出现新的截胡。

---

## 六、请 Gemini 审核的 6 个点

1. **战略判断**：废弃 v5 报告渲染层、保留引擎和输入解析、两条链并存——这个判断对吗？
2. **删除清单**：第一层 14 个函数 + 第二层 3 个函数，有无遗漏或误删？
   （特别是 `_display_path` 的保留判断）
3. **三个矛盾**：`render_report.py` / `render_v6_preprod` cache key / `tests/r10` 依赖，
   Gemini 倾向哪个选项？
4. **执行顺序**：断点 4 优先于删代码，对吗？
5. **断点 4 的修复方向**：lifa/dayun→总体、shensha 删映射、liuqin/geju→总体、jiaoyu→学业
6. **有无更高杠杆的切入口**：我们漏掉了什么？

---

## 七、给 Gemini 的提示词（用户可直接复制）

```
请审核 F:\综合盲派\mangpai-fusion\META\V5-DEPRECATION-FINAL-2026-10-20.md。

背景：Opus 作为指挥官提出「废弃 engine/v5 报告渲染层」，
Claude 作为执行/Reviewer 进行了四轮核实，修正了多处范围误判。
这是合并后的终稿，尚未执行任何删除。

重点审核第六节的 6 个点，特别是：
- 删除清单有无遗漏或误删（第一层 14 个函数都经过外部调用验证）
- 三个未决矛盾你倾向哪个选项
- 执行顺序（断点4优先于删代码）是否合理
- 有无更高杠杆的切入口

文档里所有数字都有实测依据，凡 Claude 修正过 Opus 的地方都标注了「Claude 的修正」。
```
