# Case C-2026-015-甲寅乙亥丙辰辛卯 · 经验教训

**当前状态**：⚪ 命例 lessons 占位 · 待 known_facts 反馈

> 本文件分两部分：
> - § 一·**工程层 lessons**（v1.3 引擎首次跑通的工程教训，已沉淀到 PR #31）
> - § 二·**命理层 lessons** · 待 known_facts 回测后填入

---

## 一、工程 / 流水线层（已确认）

> 这一节是本案立案过程中触发的"系统级 lessons"，**与命主八字本身无关**，但与 v1.3 引擎稳定性直接相关。已通过 PR #31 沉淀。

### Lesson E1 · v1.3 schema 1.2.0 是首次端到端验证

**证据**：
- C-2026-001 / 002 / 014 全部走的 v1.0/v1.2 自由 markdown 输入；preflight 严校验路径**之前从未跑过新案**
- 本案是首例从 `input.md`（schema 1.2.0）→ `preflight.parse()` → `engine.pipeline.run_pipeline()` → `tools.render_report.render_from_output()` 的完整链路压测

**触发的 4 处 fix**（已合入 PR #31）：

| Bug | 文件 | 影响 | Fix |
|---|---|---|---|
| **Bug 1** | `engine/predicates/types.py:399` | preflight 输出的 `Canggan` dataclass 进入 `adapt_parsed` 时 `gan` 全部返回 None → `ValueError: 非法天干: None` | 加 1 对括号修运算符优先级 |
| **Bug 2** | `tools/render_report.py` `_build_picture_vm` | §B 五步法 nested for + 婚姻 picture _debug 字段 raw repr 泄漏到 client | 预渲染 `evidence_str` + 白名单 marriage_picture 字段 |
| **Bug 3** | `tools/render_report.py` `_build_conclusions_vm` | §E 互补层永远空（旧实现从 evidence 重抽，但 Evidence 缺 confidence） | 新签名接受 `final_conclusions`，pipeline.integrate 已分层结果直通 |
| **Bug 4** | `tools/output_linter.py` evidence regex | `GP-*`（高派神煞）token 不匹配 → §D/§E lint 误判 ERROR | 扩展正则到 `GP-[A-Z0-9_\u4e00-\u9fff]+` |

附加修：
- `templates/report-v1.3.md` §B 删 nested `{% for %}` + §D heading 加 `[高派]` 标签 + `MR-401` evidence
- `_bazi_str` nil-guard（兼容 `_minimal_parsed_from_energy` 路径）

### Lesson E2 · 起运年公式与晚秋出生不兼容（未修，单独 follow-up）

**证据**：
- 公式 `起运年 = birth.年 + floor(起运岁)`
- 本案：birth=1974-11-11，起运岁≈8.86，问真 APP 报"出生后 8 年 10 月 10 天起运" → 实际转大运在 1983-09 月
- 公式得 `1974 + floor(8.86) = 1982`，与 APP 1983 错 1 年（晚秋出生 + 跨年偏差）
- 当前 work-around：起运岁 round-up 到 9.0 让 floor 出 9 → 1974+9=1983 通过 preflight

**修正建议**：preflight 应改用真实起运日期（birth_date + 起运 timedelta）的年份，而非整年算术

### Lesson E3 · 沙箱环境 PyYAML 不可装

**证据**：mangpai-fusion 4 个工具（preflight / output_linter / mechanical_rules / 多个 tools）硬依赖 PyYAML，但沙箱 INTEGRATIONS_ONLY 网络 + 无 pip 镜像 → install 失败

**Work-around**：`_sandbox_shims/yaml.py` 用 `ruamel.yaml`（系统已装）实现 PyYAML 兼容 surface（`safe_load` / `safe_dump` / `YAMLError`），通过 `PYTHONPATH=_sandbox_shims:.` 注入。已 .gitignore 不入库

**根因建议**：考虑 vendoring 一个 micro-yaml.py 入仓（仅 safe_load + safe_dump），或在 README 显式说明运行环境前置条件

### Lesson E4 · cases/ 目录契约漂移

**证据**：cases-index.md § 五 规定每案必须有 `input.md / analysis.md / feedback.md / lessons.md`，但 v1.3 流水线**只生成** `input.md + findings/ + statement_index.json`，缺另外 3 个

**当前补救**：本案手工补齐 analysis.md / feedback.md / lessons.md（见本目录）

**根因建议**：
- 选项 A：`tools/render_report.py` 在 `render_from_output` 中**自动产出** analysis.md + feedback.md 模板 + lessons.md 占位
- 选项 B：更新 cases-index.md § 五，把 v1.3 的目录结构正式纳入规约（与 v1.0 并存）
- 选项 C：把"输出 analysis.md"作为 v1.3 D6 follow-up issue 单独追踪

我推荐选项 **A + B 组合**：自动化产出 + 文档同步。

---

## 二、命理 / 派别层（待 known_facts）

> 此节在命主提供 known_facts 后填入。当前是空模板。

### 候选规律（待回测验证）

> 以下为 v1.3 引擎独门发现，需 ≥ 3 案验证后才能进入"已确认"。

| 候选规律 | 派别 | 当前 ★ | 待回测项 |
|---|---|---|---|
| 「印重身弱·杀印相生·比劫制财」复合做功 = 中富中等 | 段派 | ★5 | 命主实际财富层级是否在中富区间 |
| 「正印格 + 双印透干」+ 寒丙调候不足 = 文教/管理皇粮 | 杨派 | ★5 | 命主实际是否在公门/教育/管理体系 |
| 「日柱金舆」+「红艳×2」+「童子+羊刃」 = 婚姻富贵跃升但情绪刚烈 | 高派 | ★4 | 配偶背景 + 婚姻稳定度 |
| 词馆+天乙+太极合 = 学业辅佐充足 | 高派 | ★4 | 命主实际学历层级 |
| 月柱血刃+流霞 = 一生有手术/外伤倾向 | 高派 | ★3 | 命主健康史是否含手术/事故 |
| 童子煞 = 幼年体弱多病 | 高派 | ★3 | 命主幼年健康记录 |

### 应期空段

> known_facts 全空 → D3 应期门未激活 → 无候选铁断断语

需 known_facts 补齐后重跑流水线，应期断语会按 04-gate-protocol § 七 自动生成。预期窗口：
- **2026 丙午**（当前年）：流年丙午 + 大运庚辰 → 比劫年 + 财运过渡，结构上有重要事件可能（具体是什么需 known_facts 锚定）
- **2032 壬子**：流年壬子（七杀冲日支辰）+ 大运庚辰末 → 健康/工作变动强信号
- **2033 起 辛巳大运**：财比同柱，事业/财务可能转向

---

## 三、3 案累计 lessons cross-link

| 历史 lessons | 触发案 | 在本案是否需关注 |
|---|---|---|
| 学历"词馆=985"过度乐观 | C-2026-001 + 014 连续失验 | 🟡 本案高派词馆 +10% 学业旁证已"capped"（10% 上限），相对克制 |
| 婚姻"五凶煞=婚凶"失验 | C-2026-001 | 🟡 本案高派羊刃×3 = -9% 婚耗，已纳入双刃剑评分；但仍可能高估"婚凶" |
| 应期需校验社会时钟 | C-2026-014 | 🟡 本案 51 岁，无显著学制冲突，但婚姻应期 23-30 岁的窗口与命主当前 51 岁错位 → 已在 analysis.md § 四 标注 |
| 辰戌冲夫宫 ≠ 不婚 | C-2026-002 | 🟢 本案无辰戌冲，但日支辰被时支卯穿 → 婚宫"略动"信号需校验 |

---

## 四、归档

- **状态**：⚪ 工程 lessons 已沉淀（PR #31）+ 命理 lessons 占位
- **下次更新**：known_facts 反馈到位后填 § 二
- **附属 follow-up issues**（F1-F4 工程层 · F5-F9 用户需求驱动）：
  - **F1** 起运年公式（Lesson E2）· 优先级 🟢 低
  - **F2** PyYAML vendoring（Lesson E3）· 优先级 🟢 低
  - **F3** cases/ 契约漂移 · render 自动产出 analysis/feedback/lessons（Lesson E4）· 优先级 🟢 低
  - **F4** preflight 起运岁公式重构（与 F1 联动）· 优先级 🟢 低
  - **F5** 15 层富贵分级映射（学业/事业/婚姻/财富/官命 五维）· 优先级 🔴 高
  - **F6** 流年回溯段（过去 N 年自动扫描 + 报告新增 §C′）· 优先级 🔴 高
  - **F7** 婚姻画像年龄过滤（命主超窗口时降级为参考信息）· 优先级 🟡 中
  - **F8** 命局核心结构总览段（§A 前置 §0）· 优先级 🟡 中
  - **F9** 大运全表展示（当前只显示前 4 个）· 优先级 🟡 中

> F5-F9 已在 portrait-v2.md 中以**手工综合**方式临时实现。工程化由 PR #32 跟进。
