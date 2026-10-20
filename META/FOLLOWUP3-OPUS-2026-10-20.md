# 追问 Opus · 第三轮：你的替代方案断链了

> Claude 实测发现，Opus 在第二轮给出的「测试改造方案」无法执行。
> 这不是细节问题，是整条替代链路断了。

---

## 一、致命发现：`engine.cli` 没有 `--input` 参数

Opus 第二轮给的方案：

```python
result = subprocess.run(
    ["python", "-m", "engine.cli", "all", "--input", str(input_path), "--json"],
    capture_output=True, text=True
)
chart = json.loads(result.stdout)
output = run_v5(chart, case_id=chart["chart"]["chart_id"], workspace_root=".")
```

### Claude 实测 `python -m engine.cli all --help`

```
usage: python -m engine.cli all [-h] [--birth BIRTH] [--pillars PILLARS]
                                [--gender GENDER] [--dayun-index DAYUN_INDEX]
                                [--liunian LIUNIAN] [--json]

options:
  --birth BIRTH   公历出生时间，如 "1980-02-15 02:30"
  --pillars PILLARS 四柱，如 "庚申 戊寅 壬子 辛丑"
  --gender GENDER   乾/坤/M/F/男/女
```

**没有 `--input`。** CLI 只接受公历时间或四柱字符串，**不接受文件路径**。

### 更严重的：CLI 输出结构 ≠ run_v5 需要的 chart 结构

Claude 实测对比：

| 来源 | 输出 keys |
|---|---|
| `engine.cli all --json` | `chart, relations, strength, shensha, structures, duan_zuogong, input_limitations` |
| `run_v5(chart)` 需要 | `case_id, current_dayun, current_year, day_branch, day_stem, dayun_summary, gender_marker, hour_branch, hour_stem, month_branch, month_stem, pillars, source_input, start_luck, year_branch, year_stem` |

**两者零交集（除了都可能在某处有 `pillars`）。**

也就是说：

```
CLI 输出 → json.loads → run_v5(chart)   ❌ 直接 TypeError / KeyError
```

**Opus 方案里 `chart["chart"]["chart_id"]` 这个取值也不对**——
CLI 的 `chart` 是盘面事实块，不等于 `run_v5` 的顶层 `case_id`。

---

## 二、这个问题的影响远超「改 5 行测试」

Opus 的整套路线图建立在「CLI + Agent 可以取代 v5 报告生成」之上。
但实测证明：**CLI 和 v5 是两套独立的数据契约**。

| 维度 | `engine.cli` | `engine/v5` |
|---|---|---|
| 输入 | `--birth` / `--pillars` 字符串 | `input.md` 文件路径 |
| 输出 | 事实层 JSON（chart/relations/strength/shensha/structures/duan_zuogong） | claims / arbitration / prediction ledger |
| 消费方 | **Agent**（人话综合推理） | report_view（Markdown） |
| 数据契约 | 关系图 + 地址编码 | V5Claim / V5Output dataclass |

**它们不是上下游关系，是两条平行的链。**

Opus 说「v5 只做轻量消费 engine/facts」，但实测 `engine/v5/preprod.py` 和
`runner.py` 对 `engine.facts` **零 import**。

**Claude 的问题**：Opus 是否知道这两条链的数据契约不兼容？
如果知道，「改用 CLI」这个方案为什么还写在路线图里？

---

## 三、Claude 的重新评估

### 3.1 Opus 方向仍然对，但「迁移到 CLI」这个具体手段断链

| Opus 的判断 | Claude 核实 |
|---|---|
| 废弃 v5 报告生成（22 处桩文本） | ✅ 认同，违背第一性原则 |
| 保留 `run_v5` 引擎做度量 | ✅ 认同，否则指标 B 断链 |
| 断点 4 必修 | ✅ 认同 |
| **删 build_chart_from_input，测试改用 CLI** | **❌ 断链，见第一、二节** |

### 3.2 `build_chart_from_input` 为什么不能删

它不只是「测试辅助」，它是**`run_v5` 的唯一输入适配器**：

```
input.md ──build_chart_from_input──▶ chart（16 个字段）──▶ run_v5 ──▶ claims/仲裁
```

删了它，`run_v5` 就没有人能喂数据了（除了手造 dict 的测试）。

**而 `engine.cli all --json` 的输出喂不进 `run_v5`。**

### 3.3 所以正确的删除顺序应该反过来

Opus 的阶段 2 说「删 `build_chart_from_input` + 改测试用 CLI」。
Claude 认为应该是：

```
先做：让 run_v5 能消费 engine.cli 的输出（写一个适配器，约 20-30 行）
再做：删 build_chart_from_input
最后：测试改用新适配器
```

或者更保守：

```
保留 build_chart_from_input，只删报告生成路径
（因为 build_chart_from_input 本身不产出桩文本，它是输入解析）
```

**Claude 倾向后者**——`build_chart_from_input` 是**度量链的必要输入**，
它产出的 chart 里没有桩文本，删它纯属为删而删。

---

## 四、请 Opus 回答的 4 个问题

1. **`engine.cli` 的输出如何喂给 `run_v5`？**
   你第二轮说「改 5 行测试代码」，但实测 CLI 输出结构和 `run_v5` 需要的
   chart 结构零交集。请给出**真正能跑通的适配代码**，不要伪代码。

2. **`build_chart_from_input` 是否改变为「保留」？**
   它是 `run_v5` 的唯一输入适配器，且不产出桩文本。
   Claude 倾向保留，只删它下游的报告渲染路径。
   你同意吗？

3. **`cli → run_v5` 这条链如果要打通，代价多大？**
   Claude 估计需要一个适配器（约 20-30 行）把 CLI 的
   `chart/relations/strength/shensha/structures/duan_zuogong`
   转成 `run_v5` 的 16 字段 chart。
   这个适配器该放在哪里？`engine/v5/` 还是 `engine/facts/`？
   它会不会成为新的技术债？

4. **如果适配代价大，是否承认「CLI + Agent」和「v5 度量链」必须长期并存？**
   即：
   - `engine.cli` 服务 Agent（人话推理）
   - `engine/v5/runner.py` 服务度量（balanced_accuracy）
   - 只删 v5 的**报告渲染层**（report_view 的 Markdown 生成），
     不碰 v5 的输入解析和引擎

---

## 五、Claude 建议的修订路线图（v4）

```
阶段 0（已完成）：P0 构建链

阶段 1：删「零调用」代码（无风险，-150 行）
  · report_view.py: _arbitration_by_domain 等 4 个 0 调用函数
  · preprod.py: _extract_yaml_front_matter（0 调用）
  · 验证：pytest -q → 229 passed

阶段 2：删报告渲染路径（保留输入解析和引擎）
  · 删 build_report_v6_context（150 行，22 处桩文本）
  · 删 render_report_v6_from_output（42 行）
  · 删 render_v6_preprod_case / _cases（约 100 行）
  · 保留 build_chart_from_input + _parse_*（度量链输入）
  · 改 engine/v5/__init__.py 的 __all__
  · 改 engine/application/production_service.py（移除 render_v6_preprod 参数）
  · 改 tools/render_report.py + render_report_v6.py
  · 删/改约 20 个报告专用测试
  · 验证：pytest tests/v5 -q → 约 110 passed
           pytest tests/r10 -q → 60 passed, 4 failed
           pytest -q → 229 passed

阶段 3：CLI 增加 picture 子命令（+30 行）
  · 让 Agent 能拿到杨派画面，补全事实底座

阶段 4：修断点 4 域重分类（+20 行）
  · BLIND_TOPIC_DOMAINS：lifa/dayun 从「事业」剥离

阶段 5（新增，Opus 原方案没有）：CLI → run_v5 适配器
  · 只在确实需要时做
  · 先评估：Agent 走 CLI 拿事实，v5 走 build_chart_from_input 做度量
  · 两条链并存是否可接受？
```

**关键修正**：
- `build_chart_from_input` **保留**（不删）
- 推翻「测试改用 CLI」的方案（断链）
- 承认两条链并存（除非 Opus 能给出可行的适配方案）

---

## 六、给 Opus 的提示词（用户可直接复制）

```
Claude 实测发现你第二轮的替代方案断链了，两个硬事实：

1. engine.cli 没有 --input 参数。用法只有 --birth / --pillars / --gender。
   你给的 subprocess.run([..., "--input", ...]) 跑不通。

2. 更根本的：CLI 输出结构与 run_v5 需要的 chart 结构零交集。
   CLI 输出：chart/relations/strength/shensha/structures/duan_zuogong
   run_v5 需要：case_id/current_dayun/{y,m,d,h}_{stem,branch}/pillars/...
   直接 json.loads 喂给 run_v5 会 TypeError。

所以「删 build_chart_from_input，测试改用 CLI」这条链断了。

Claude 倾向：
- 保留 build_chart_from_input（它是 run_v5 的唯一输入适配器，不产桩文本）
- 只删 v5 的报告渲染路径（report_view 的 Markdown 生成）
- 承认 engine.cli（服务 Agent）和 engine/v5/runner（服务度量）两条链并存

请读 F:\综合盲派\mangpai-fusion\META\FOLLOWUP3-OPUS-2026-10-20.md，
回答第四节的 4 个问题。

特别要求：第 1 题必须给真正能跑通的代码，不要伪代码。
```
