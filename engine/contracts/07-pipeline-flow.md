# 流水线数据流契约 · 07-pipeline-flow

> **本文精确定义 v1.2 W1-W4 的 3+1 维流水线。**
> 每一步的输入/输出/前置条件/后置断言，8 个 agent 按此文件编码。

最后更新：2026-05-23（W1.4）
版本：v1.2.0

---

## 一、流水线总览（与 00-OVERVIEW § 二 对应）

```
ParsedInput → [preflight] → W1(D1) → W2(D2) → W3(D3) → W4(D4)
              → [output_linter] → [render_report] → [AI polish] → [archive+predict]
```

每步都是**纯函数**：输入确定 → 输出确定。无全局可变状态。

---

## 二、Step 0 · preflight（兜底护栏 #1）

| 项 | 值 |
|---|---|
| 入口 | `tools/preflight.py parse(input_md_path)` |
| 输入 | `cases/C-XXX/input.md`（原始 Markdown + YAML 块） |
| 输出 | `ParsedInput` 对象（03-findings-schema § 四） |
| 前置 | input.md 文件存在，schema_version=1.2.0 |
| 后置 | 11 步校验全过（01-input-schema § 四），否则 raise PreflightError |
| 副作用 | 无（不写文件） |
| 失败行为 | 拒绝进入流水线，打印 `[FAIL] ...` |

---

## 三、Step W1 · D1 能量评估（段派）

| 项 | 值 |
|---|---|
| 入口 | `engine/energy/evaluator.py evaluate_energy(parsed)` |
| 输入 | `ParsedInput` |
| 输出 | `EnergyFindings`（03 § 五） |
| 前置 | ParsedInput 校验通过 |
| 后置 | `energy.layer_count ∈ [0,4]`；`energy.wealth_ceiling` 合法枚举；`energy.evidence` 非空 |
| 内部子步骤 | ① 体用判别 → ② 做功路径扫描 → ③ 势党计算 → ④ 贼神捕神 → ⑤ 富贵层级折算 |
| 落盘 | `cases/C-XXX/findings/energy.json` |

### W1 内部 DAG

```
parsed.bazi + parsed.dayun
    │
    ├── tiyong.py: 判定体(印/比/禄)用(财/官) → TiyongStructure
    │
    ├── zuogong.py: 扫描 6 种做功路径 → list[ZuogongPath]
    │       依赖 tiyong 输出
    │
    ├── shidang.py: 5 行势力比 + 12 种党形态 → ShiDang
    │       依赖 parsed.bazi
    │
    └── zeishen.py: 强体+弱用+大运到位 → ZeishenBushen
            依赖 tiyong + shidang + parsed.dayun

    汇总 → evaluator.py 组装 EnergyFindings
```

---

## 四、Step W2 · D2 画面合拍（杨派）

| 项 | 值 |
|---|---|
| 入口 | `engine/picture/matcher.py match_picture(energy, parsed)` |
| 输入 | `EnergyFindings` + `ParsedInput` |
| 输出 | `PictureFindings`（03 § 六） |
| 前置 | `energy` 非 None；`upstream_hash` = `findings_hash(energy)` |
| 后置 | `picture.energy_consistent == True`（否则写 violations 但仍继续）；`picture.wubu_steps` 长度=5 |
| 约束 | D2 画面不得违背 D1 的 `wealth_ceiling`（如 D1=小富 → D2 不能输出"千万级收入画面"） |
| 落盘 | `cases/C-XXX/findings/picture.json` |

### W2 内部 DAG

```
energy.tiyong + energy.wealth_ceiling + parsed
    │
    ├── wubu.py: 五步法 → list[WubuStep]
    │       步骤：家里找财官→出处→取法→皇粮民营→天地一气
    │
    ├── wuhe.py: 天干五合扫描 → list[WuheRelation]
    │
    ├── anyin.py: 十神暗引 5 公式 → list[AnyinResult]
    │
    └── caifu.py: 财富 7 等 + 官命 9 取 → CaifuRanking / GuanmingQufa
            依赖 energy.layer_count 作为上界约束

    汇总 → matcher.py 组装 PictureFindings + energy_consistent 校验
```

---

## 五、Step W3 · D3 应期三层门（任派）

| 项 | 值 |
|---|---|
| 入口 | `engine/yingqi/gate.py gate_yingqi(year, event, domain, energy, picture, parsed)` |
| 输入 | `EnergyFindings` + `PictureFindings` + `ParsedInput` + 候选年份列表 |
| 输出 | `list[GateResult]`（03 § 七） |
| 前置 | `upstream_energy_hash` + `upstream_picture_hash` 校验通过 |
| 后置 | 每个 GateResult.passed_layers ∈ [1,3]（=0 的被丢弃不输出） |
| 候选年产生 | 扫描 `birth_year + 10` ~ `birth_year + 80`（或 known_facts 中的事件年 ± 3 年窗口） |
| 落盘 | `cases/C-XXX/findings/gate_results.json` |

### W3 调用模式

```python
# 不是逐年盲扫，而是"候选事件驱动"
candidates = generate_candidate_events(energy, picture, parsed)
# candidates 形如: [("结婚", "婚姻", [2003,2004,2005,...]), ("升迁", "事业", [...]), ...]

gate_results = []
for event_name, domain, year_list in candidates:
    for year in year_list:
        result = gate_yingqi(year, event_name, domain, energy, picture, parsed)
        if result.passed_layers >= 1:
            gate_results.append(result)

# 按 passed_layers 降序 + year 升序排序
gate_results.sort(key=lambda r: (-r.passed_layers, r.year))
```

---

## 六、Step W4 · D4 旁证补强（高派）

| 项 | 值 |
|---|---|
| 入口 | `engine/pangzheng/support.py support_with_shensha(parsed, energy, picture, gate_results)` |
| 输入 | `ParsedInput` + 上游三个 Findings |
| 输出 | `SupportFindings`（03 § 八） |
| 前置 | parsed.shensha 非空（若为空则 D4 输出空结构，不阻塞流水线） |
| 后置 | D4 不新提结论（`shensha_supports` 的 key 必须对应已有 D1/D2/D3 的某条结论） |
| 落盘 | `cases/C-XXX/findings/support.json` |

### D4 boost 上限

| 神煞类别 | 单个 boost 上限 | 累计 boost 上限 |
|---|---|---|
| 天乙/金舆/将星等贵人系 | 0.05 | 0.15 |
| 词馆/学堂/文昌等学术系 | 0.03 | 0.10 |
| 华盖/太极等玄学系 | 0.02 | 0.05 |
| 白虎/羊刃/灾煞等凶煞系 | 0.04 | 0.12 |

---

## 七、Step 整合 · AnalysisOutput 生成

```python
# 在 W4 完成后
output = integrate(energy, picture, gate_results, support, parsed)
# integrate() 做：
#   1. 合并 4 个 Findings → final_conclusions（含跨派冲突仲裁）
#   2. 按 共识/互补/独门/冲突 分层
#   3. 填充 yingqi_table（按时间排序）
#   4. 计算 overall_confidence
#   5. 落盘 cases/C-XXX/findings/analysis_output.json
```

---

## 八、Step output_linter（兜底护栏 #2）

| 项 | 值 |
|---|---|
| 入口 | `tools/output_linter.py lint(analysis_output)` |
| 输入 | `AnalysisOutput` |
| 输出 | `LintResult`（pass / fail + 错误列表） |
| 检查项（11 项） | 详见下表 |

| # | 检查 | 失败行为 |
|---|---|---|
| 1 | 每条 conclusion 含 `★N (X%)`，区间一致 | 拒绝 |
| 2 | 每条 conclusion 含 `[派别标签]` | 拒绝 |
| 3 | 每条 conclusion 含 `evidence` 链（≥1 条） | 拒绝 |
| 4 | 应期断语含 `yingqi_year`（非 None） | 拒绝 |
| 5 | 应期断语含 `falsifiable`（非空） | 拒绝 |
| 6 | ★★★★★ 断语的 gate passed_layers == 3 | 拒绝 |
| 7 | 无"未来某年/可能/一定/肯定"等被禁措辞 | 降级标记 |
| 8 | `energy_consistent` + `picture_consistent` 全 True | 警告 |
| 9 | 所有 `upstream_hash` 一致 | 拒绝 |
| 10 | 无 blacklisted 规律被引用 | 拒绝 |
| 11 | conclusion 总数 ≥ 5（策略 B 最少断语数） | 警告 |

---

## 九、Step render_report

| 项 | 值 |
|---|---|
| 入口 | `tools/render_report.py render(analysis_output, template="report-v1.2.md")` |
| 输入 | `AnalysisOutput` (lint 通过后) |
| 输出 | Markdown 报告骨架（铁断不可改） |
| 落盘 | `reports/C-XXX-{干支}-report.md` |

骨架结构（三段式）：
```
§A 能量级别（D1·段派）
§B 画面细节（D2·杨派）
§C 时间应期（D3·任派）
§D 旁证补强（D4·高派）
§E 立体合并
§F 应期总表
§G 风险提示
§H 命主画像版 [AI-polish 允许段]
```

---

## 十、Step AI polish（限定段）

| 项 | 值 |
|---|---|
| 输入 | render_report 输出的骨架 Markdown |
| 允许改动区域 | **仅** `§H 命主画像版` 内标 `[AI-polish]` 的段落 |
| 禁止改动区域 | §A-§G 的所有铁断文字 + ★ + % + evidence |
| 输出 | 最终报告（AI 润色后） |
| 标记 | 被 AI 改写的段落开头标 `<!-- [AI-polish] -->` |

---

## 十一、Step archive + predict

```python
# tools/extract_predictions.py（自动从 ★★★★+ 应期抽取）
for gate_r in analysis_output.gate_results:
    if gate_r.confidence.star >= 4:
        create_prediction_file(gate_r, case_id)
        # → predictions/PRED-YYYY-NNN-CXXXXXXX-{干支}-{event}.md
```

同时执行归档：
- `cases/C-XXX/` 全部文件落盘完毕
- `cases-index.md` 自动追加一行
- 触发 `feedback_loop.py`（如果 known_facts 中有事实，立即回测）

---

## 十二、错误处理 & 中断恢复

| 错误发生位置 | 行为 |
|---|---|
| preflight 失败 | 整个流水线不启动，返回错误信息 |
| W1 内部异常 | 写 `cases/C-XXX/findings/energy_error.json`，流水线中断 |
| W2 upstream_hash 不匹配 | 拒绝运行 W2，要求重跑 W1 |
| W3 无任何 passed_layers≥1 的候选 | 输出空 gate_results，报告 §C 标注"无铁口应期" |
| output_linter 拒绝 | 流水线中断，不落盘报告；findings 保留以便 debug |
| render 正常但 AI polish 超时 | 输出骨架版报告（无 §H 润色段），标注"[骨架版]" |

---

## 十三、性能约束

| 步骤 | 目标时间 | 备注 |
|---|---|---|
| preflight | < 2s | 纯解析 |
| W1 | < 5s | 无外部 IO |
| W2 | < 5s | 无外部 IO |
| W3 | < 10s | 扫描 ~50 年 × ~5 事件 = 250 次 gate |
| W4 | < 3s | 查表 |
| integrate | < 2s | 纯聚合 |
| output_linter | < 1s | 纯校验 |
| render | < 2s | 模板填充 |
| AI polish | < 30s | AI 生成 |
| archive+predict | < 3s | 文件 IO |
| **端到端** | **< 60s** | 不含 AI polish 约 30s |

---

**契约结束。下一份请阅读 `08-agent-handoff.md`（W1.4 第 2 份，也是最后一份）。**
