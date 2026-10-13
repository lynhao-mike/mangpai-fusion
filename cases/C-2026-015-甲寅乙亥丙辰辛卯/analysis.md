# Case C-2026-015-甲寅乙亥丙辰辛卯 · 分析过程

**立案日期**：2026-05-25
**策略**：B · 全面画像（known_facts 全 unknown · 首次入库待回测）
**分析师**：mangpai-fusion **v1.3 引擎自动产出** + 人工 §H 润色
**指纹**：`4ffe3325d69d`
**关联 PR**：[#31](https://github.com/lynhao-mike/mangpai-fusion/pull/31)（含 4 处 ENGINE-FIX）

---

## 零、契约说明（v1.3 与旧 v1.0 的差异）

> 本案是 v1.3 strict-schema 流水线**首例端到端通跑**的案例。与 001/002/014 案的人工 `analysis.md` 写法不同，v1.3 的"分析过程"以**结构化 JSON + 模板渲染报告**为权威源。本文件是面向人类读者的**导航摘要**，不重复 JSON 内容。

| v1.0 旧规约 | v1.3 等价物 | 本案路径 |
|---|---|---|
| `analysis.md` 派别仲裁 | `findings/analysis_output.json`（含 `final_conclusions[].layer/contributing_schools`） | [findings/analysis_output.json](findings/analysis_output.json) |
| `analysis.md` 4 派各自定性 | `findings/{energy,picture,gate_results,support}.json` | [findings/](findings/) |
| `analysis.md` 双轨置信度断语 | `reports/...-master.md` §A-§G（铁断段，禁止 AI 修改） | [reports/...-master.md](../../reports/C-2026-015-甲寅乙亥丙辰辛卯-report-master.md) |
| `analysis.md` 应期一览 | `findings/gate_results.json` + 报告 §C | （本案为空，详见 § 四） |
| 反查锚点 | `statement_index.json`（v1.3 D1 新增） | [statement_index.json](statement_index.json) |

---

## 一、流水线运行摘要

| 维度 | 数值 | 落档 |
|---|---|---|
| `hash_chain_valid` | True | analysis_output.json |
| 总耗时 | < 1 s（本机沙箱） | timing.json |
| `layer_summary` | 共识 0 / 互补 5 / 独门 2 / 冲突仲裁 0 | analysis_output.json |
| `overall_confidence` | **★4 (85.1%)** | analysis_output.json |
| `gate_results` 数 | **0** | gate_results.json（空数组） |
| `final_conclusions` 数 | 7 | analysis_output.json |
| 双护栏 lint（master） | 0 ERROR · 通过 | reports/ |
| 双护栏 lint（client） | 0 ERROR · 通过 | reports/ |

---

## 二、四派各自定性（机器落定，未走人工仲裁）

### D1 段派 · 能量层（★5 / 95%）

- **格局类型**：月令亥水透壬七杀藏，乙木正印透月干 → **正印格 + 杀印相生**
- **做功层数**：2 层
- **财富天花板**：**中富级·中**
- **体用结构**：体 = 丙(日主) + 甲乙(印) + 寅(印) + 辰(食伤) + 卯(印)；用 = 辛(财) + 亥(官杀)
- **做功路径**（10 条全部继承整体置信 ★5）：
  1. 日支辰 ↔ 时支卯 之**穿** → 作用于辰中食伤
  2. 月支亥(官杀) → 生 → 年柱甲(印) → 印化杀
  3. 日柱丙(比劫) 克 时柱辛(财) → 比劫制财
  4. 日支辰(食伤) → 生 → 时柱辛(财) → 食伤生财
  5. 时柱辛(财) → 生 → 月支亥(官杀) → 财生官
  6. 年支寅 ↔ 月支亥 之**六合** → 作用于亥中官杀
  7. 日柱丙 合 时柱辛 化水（=官杀） → 合绊
  8. 年支寅 ↔ 月支亥 之**破**（弱）
  9. 日支辰 库藏 癸（财官，未冲刑→关库）
  10. 复合做功 = 制+化+合+生泄 多种叠加（M1-D-014）

> 详见 [findings/energy.json](findings/energy.json) · `zuogong_paths`

### D2 杨派 · 画面层（★5 / 90%）

| 五步 | 结论 | evidence |
|---|---|---|
| 1 家里找财官 | 时辛(财) + 日支癸(官) 自家拿，弱制即得 | M2-Y-019 / M2-Y-119 |
| 2 出处 | 从坐下出 = 完全是我自己的 | M2-Y-119 / M2-Y-162 |
| 3 取法 | 段派母星=比劫 → 杨派对应"低（劳动者）"；D1=2 层 → 自食其力扎实 | M2-Y-021 |
| 4 皇粮民营 | 天干透甲乙双印 → 吃皇粮候选（文教/管理） | M2-Y-120 |
| 5 天地一气 | 天干印+财 / 地支印+官杀+食伤，仅"印"重叠 → 部分一致 | M2-Y-121 |

- **财富等级**：旺官（第 5 等）
- **官命取法**：**化杀生枭**（第 1 取）— 这是杨派对"杀印相生"的命名
- **行业方向**：公门/国企、文教/管理、教育/医疗/文化（活木+水）、矿产/珠宝/金融（活金有火）、流通/贸易/运输（活水）
- **婚姻画面**：
  - 初婚最佳窗口 **23-30 岁**
  - 配偶画像：时柱藏辛正财，配偶相识较晚或跨年龄，性情果断利落
  - 婚姻稳定度：中等
  - 早婚信号：中 / 晚婚信号：中（混合）
  - 早期大运激活：丙子大运 9-18 岁与婚宫辰 + 寅形成三合化水（注：与命主实际年龄 51 岁不匹配，纯结构信号）

> 详见 [findings/picture.json](findings/picture.json)

### D3 任派 · 应期层（**未运行**）

- `gate_results: []` 空
- **原因**：known_facts 全 unknown → 无回测真值锚 → 引擎按 04-gate-protocol § 七 **主动跳过应期扫描**，避免在无 G2/G3/G4 红线下输出 ★≥4 误判
- 这是**正确行为**而非缺陷。补 known_facts 后引擎会自动激活三层 gate

> 详见 [findings/gate_results.json](findings/gate_results.json)（空数组）

### D4 高派 · 旁证层（★4 / 80%）

| 项 | 内容 | boost | evidence |
|---|---|---|---|
| 婚姻 · 金舆（日柱） | 配偶有车有产 / 婚姻富贵跃升 | **+5%** | GP-金舆 |
| 婚姻 · 红艳煞 ×2（年/时） | 异性缘旺（双刃剑：旺则桃花 / 凶则烂桃花） | +2%×2 | GP-红艳煞 |
| 婚姻 · 童子煞（日时） | 早期波折 / 二婚信号（负向） | **-3%** | GP-童子煞 |
| 婚姻 · 羊刃 ×3（月/月/日） | 命主刚烈，对婚姻有耗（负向） | -3%×3 | GP-羊刃 |
| 学业 · 词馆+天乙×1+太极 | 累计 +12% capped to **+10%** | +10% | GP-CG-词馆 / GP-TY-天乙 |
| 健康 · 血刃/流霞（月柱） | 一生有手术/外伤倾向（弱风险） | warn | GP-CH-09 |
| 健康 · 童子煞 | 幼年体弱多病（弱风险） | warn | GP-BD-12 |

> 详见 [findings/support.json](findings/support.json)

---

## 三、立体合并（共识/互补/独门）

机器分层结果（pipeline.integrate 落定）：

- **共识层**：**0 条** — 无四派全一致的高置信断语
  - 原因：D2 杨派与 D4 高派各有独门发现，但缺 D3 应期锚点，达不到"4 派一致"门槛
- **互补层**：**5 条**（已在 reports/...master.md §E.5.2 完整落档）
  1. [杨/段] 行业方向（公门+文教+教育+矿产+流通） ★5 (90%)
  2. [高] career 域 boost +0.20 ★4 (80%)
  3. [高] general 域 boost +0.20 ★4 (80%)
  4. [高] health 域 boost +0.20 ★4 (80%)
  5. [高] wealth 域 boost +0.04 ★4 (80%)
- **独门层**：**2 条**
  1. [段派 独门] 格局做功 2 层，富贵层级中富·中 ★5
  2. [杨派 独门] 婚姻最佳窗口 23-30 岁 ★5
- **冲突仲裁**：0 条（4 派无矛盾断语）

> 详见 [findings/analysis_output.json](findings/analysis_output.json) · `final_conclusions[]`

---

## 四、本案的特殊性（文档化）

1. **首例 v1.3 strict-schema 端到端跑通**：触发了 4 处 ENGINE-FIX（PR #31），首次验证从 input.md → preflight → pipeline → render 的完整链路
2. **known_facts 全 unknown 模式**：用于压力测试引擎的"无真值降级"行为，验证 D3 应期门正确封闭、置信度正确封顶 ★4
3. **婚姻画像存在结构-时间不匹配**：D2 输出 23-30 岁初婚窗口 + 大运 1（丙子，9-18 岁）激活婚宫，但命主实际 51 岁。这种 mismatch 在补 known_facts 后引擎会自动反相检测；目前是**结构信号**而非应期断言

---

## 五、分析交付清单

| 文件 | 路径 | 用途 |
|---|---|---|
| 输入 | [input.md](input.md) | schema 1.2.0 |
| D1-D4 落档 | [findings/](findings/) | 6 个 JSON |
| 反查索引 | [statement_index.json](statement_index.json) | D5 反馈 fanout |
| 命理师版报告 | [reports/...master.md](../../reports/C-2026-015-甲寅乙亥丙辰辛卯-report-master.md) | 含 [S-...] 反馈位 |
| 命主可读版 | [reports/...client.md](../../reports/C-2026-015-甲寅乙亥丙辰辛卯-report-client.md) | ★≤3 已过滤 |
| 反馈采集 | [feedback.md](feedback.md) | 模板（待填） |
| 教训 | [lessons.md](lessons.md) | 工程 lessons + 命理 lessons 占位 |

---

## 六、下一步

- 等命主补 known_facts（婚 / 子 / 学 / 职 / 健 / 父母 / 重大事件 ≥ 3 件）
- 等到后：① 重跑 v1.3 流水线 → D3 应期门激活 → 整体置信度可上探 ★5；② 由 master 阅读 reports/...master.md 后填 feedback.md（每条 [S-...] [ ] → [y]/[n]/[?]/[skip]）；③ 自动触发 feedback_loop 重算
- 当前状态：引擎跑通 · 待回测
