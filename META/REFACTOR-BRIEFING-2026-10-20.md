# 项目重构 Briefing · 给 Opus（指挥官）

> 本文件自包含。Opus 读它即可开始，无需再问 Claude 要上下文。
> 最后更新：2026-10-20 14:20（Claude 整理，用户审议中）

---

## 零、这个项目的真正目标（第一性原则）

### 0.1 用户原话

> **「我的目的是能将真实八字分析准确」**

### 0.2 这个目标在仓库里已有量化指标

仓库里有两个**衡量完全不同维度**的指标，必须分清：

#### 指标 A：盲断年份吉凶准确率（判断质量）

来源 `META/blind-baseline-v1-2026-10-18.md`（2026-10-18 实测）：

| 口径 | 计算 | 数值 | 说明 |
|---|---|---|---|
| **严格** | 77 / 170 | **45.3%** | partial 视为未命中 |
| 半分 | (77+17) / 170 | 55.3% | partial 记 0.5 |
| 宽松 | 77 / 136 | 56.6% | partial 排除出分母（会高估能力） |

样本：18 例 / 232 判断点，记录年 170，对照年 62，独立样本 17。

错误构成：59 incorrect + 34 partial，方向翻转 59 次——
**过吉 37 > 过凶 22**（与第 1 批结论相反）。

**仓库自己推荐引用严格口径 45.3%**，理由是它回答「问这个年是吉是凶，答对了吗」；
宽松口径把「答平」排除，会高估能力。

#### 指标 B：职业路径分类 balanced_accuracy（有硬门槛）

来源 `tools/career_path_promotion_gate.py`：

```python
PROMOTION_REQUIREMENTS = {
    "min_balanced_accuracy": 0.60,                 # 绝对门槛
    "beats_frozen_baseline_balanced_acc": 0.425,   # 相对门槛
}
```

当前实测（`tests/test_career_path_promotion_gate.py:78`）：
`balanced_accuracy == 0.3625`，`eligible is False`。

**两个门槛都没过**：`0.3625 < 0.425 < 0.60`。

#### 两个指标的区别

| | 指标 A（盲断准确率） | 指标 B（balanced_accuracy） |
|---|---|---|
| 衡量什么 | 流年吉凶判断对不对 | 二分类（就业/创业）分得准不准 |
| 样本 | 18 例 / 170 记录年 | p-series 案例集 |
| 有硬门槛吗 | **没有**，只有历史基线 | **有**：0.425 / 0.60 |
| 失败方式 | 方向翻转（过吉/过凶） | 少数类被忽略（recall 失衡） |
| 对应代码 | `tools/blind_year_score.py` | `tools/career_path_promotion_gate.py` |

### 0.3 为什么优先级以指标 B 为准

**指标 B 有硬门槛，指标 A 没有。**

具体说：
- 指标 B 的 `eligible is False` 是一个**二值裁决**——达不到 0.425 就不许推广，
  这是一个可以被 CI 化的门禁。
- 指标 A 的 45.3% 是**参考基线**，没有「低于 X 就不许用」的规则。

而且 `balanced_accuracy` 的计算方式（`sum(recalls.values()) / 2`）意味着：
**它对少数类召回敏感**。如果模型把所有案例都判成"就业"，accuracy 可能很高，
但 balanced_accuracy 会暴露这个问题。

**这正好对应指标 A 发现的「过吉 37 > 过凶 22」**——系统性地偏向一类答案。

**所以两个指标其实在说同一件事的不同侧面**：
> 系统倾向于给出"安全但错误"的答案。

### 0.4 所以重构的成功标准是

```
指标 B（有硬门槛，优先级最高）：
  balanced_accuracy: 0.3625 → > 0.425（先过相对门槛）→ > 0.60（再过绝对门槛）
  eligible: False → True

指标 A（参考基线，持续监控）：
  严格口径: 45.3% → 显著提升
  方向偏差: 过吉 37 / 过凶 22 → 趋于平衡
```

**不是**「代码更干净」「测试更多」「规则更多」。

### 0.5 AGENTS.md 铁律（不可违反）

```
1. 确定性盘面事实只从 python -m engine.cli 获取
   —— 禁止心算排盘、禁止编造干支关系/长生/空亡/神煞/起运
2. 经典与流派理论通过 python -m tools.query_theory 检索
3. 综合推理、证据权衡与最终裁决由 Agent 完成
   —— 工具列出的事实或候选不等于自动成立的命理结论
```

**推论**：系统价值 = **证据链可追溯**。
任何「假阳性」或「静默失败」都比「没有功能」更糟——因为它会让 Agent 基于假证据下结论。

---

## 一、当前技术债的量化图景

### 1.1 已完成（2026-10-20，不要重复劳动）

| 项 | 实测结果 |
|---|---|
| P0 构建链 | `theory/{gao,duan,yang,ren}/index.yaml` 重建完成：484 条空正文 + 72 条 § 指针 + 414 条 trigger + 175 条初始分全部恢复 |
| `blind_rule_gate` | 已修：只有 `evaluable` 才短路；关键词兜底只扫 topic/title/conclusion（不扫 condition/trigger，避免 35 条否定词反向召回） |
| `score_blind_rule` | 已修：`raw>1.0` 除以 5.0（段派 3.0~5.0 分制归一化） |
| `_picture_rank_within` | 已修：用 `rank` 门槛代替 `bool()`，防 204 条 `*_picture` 恒真 |
| manifest 污染 | 已修（T-106）：12 个 tracked manifest 零污染 + 隔离回归测试 |
| locator 校验 | 已加报警模式（T-110）：59 个 locator 体检，失效 5 个 |
| 仓库瘦身 | 14.22 MiB 移出 git 跟踪 |

**索引现状**：

```
派    总数  空  §指针  trigger  score
gao   630   0    0      0      225
duan   428   0    0    239      290
yang   400   0    0    145      145
ren   200   0    0     30       30
```

**当前测试基线**：

```
python -m pytest -q                          → 229 passed
python -m pytest tests/tools -q -o addopts="" → 294 passed
python -m pytest tests/v5 -q -o addopts=""   → 130 passed
python -m pytest tests/r10 -q -o addopts=""  → 4 failed, 60 passed
```

### 1.2 规则库真实状态（实测）

```
总规则 3699 条，分两套 schema：

A 类（盲派候选，1658 条）：gao 630 / duan 428 / yang 400 / ren 200
  · 一条 condition/trigger 都没有（P0 后部分恢复：duan 239 + yang 145 + ren 30 = 414）
  · 剩余 1244 条仍无 trigger
  · blind_rule_gate 只能关键词兜底：1139 条恒 False，519 条只看 2 个布尔量
  · 6 张真实命盘只产生 3 种通过集合（理论上限 2^3=8）

B 类（生产规则，2041 条）：ziping 933 / tiaohou_ditiansui 1108
  · 100% 有 trigger、100% 有行号锚点、0 空正文
  · 但 ziping 有 455 条 trigger 是 always（恒真无门禁）
  · 多域泛标：ziping 平均 4.05 个域，630 条（67.5%）标了 4 个以上
```

**密度对比**（说明语料不是瓶颈）：

| 流派 | 规则数 | 原始语料 | 密度(条/K) |
|---|---|---|---|
| 滴天髓 | 1108 | 828K | 1.34 |
| 子平真诠 | 933 | 704K | 1.33 |
| 高德臣(盲派) | 630 | 1.1M | 0.57 |
| 段建业(盲派) | 428 | 4.6M | 0.09 |
| 杨清娟(盲派) | 400 | 4.6M | 0.09 |
| 任付红(盲派) | 200 | 1.4M | 0.14 |

---

## 二、六个断点（核心问题，每个都有实测证据）

### 断点 1：四柱解析断

**现象**：16 个早期案例（C-2026-002..020）解析出**全空四柱**。

**根因**：`engine/v5/preprod.py:24` 的 `PILLAR_RE` 要求表格带粗体 `| **年柱** |`。
而那些案例是 `| 年柱 | 壬（偏财） | 戌 |`，且**没有独立主星列**——
正则会把「壬（偏财）」当主星跳过，把「戌」抓成天干、把藏干「戊比肩」抓成地支。

**影响**：输入就是假的，后面全错。

**⚠️ 这是二手结论（Gemini 勘察），Opus 需亲自复核。**

---

### 断点 2：事实计算断（含假谓词陷阱）

**现象**：v5 的 chart 只有 `pillars`，**没有 `energy`/`shensha`/`picture`**。

**后果**：
- 39 条「做功」规则恒 False（`chart.get("energy")` 为空）
- 所有神煞 trigger 恒 False
- 6 个 `has_*_picture` 类象 trigger 恒 False

**假谓词陷阱**（Claude 已实测确认）：

| 函数 | 返回值 | `bool()` |
|---|---|---|
| `compute_caifu` | `CaifuRanking` dataclass | **恒 True** |
| `compute_guanming` | rank=1/2，非空 | **恒 True** |
| `build_marriage_picture` | 非空 dict | **恒 True** |

原代码：
```python
if trigger == "has_wealth_picture":
    return ... or bool(chart.get("picture", {}).get("caifu"))
```

**致命链条**：

| 阶段 | 204 条 `*_picture` 规则 |
|---|---|
| 现在 | 无 picture 字段 → `bool({})` → **全死** |
| 挂上 picture 后 | dataclass 非空 → **全活，不看命盘** |

Claude 已加 `_picture_rank_within(chart, key, max_rank)` 修复。

---

### 断点 3：规则召回断

**现象**：`engine/v5/runner.py:198` 的 `build_ziping_production_claims`
**无 trigger 过滤、无 limit**，267 条子平规则全量灌入每个命盘。

**267 条 quantifiable 的 trigger 分布**（实测）：

```
has_wealth_picture:  102 (38.2%)
has_official_picture: 86 (32.2%)
has_zhi_chong:        61 (22.8%)
has_marriage_picture: 16 (6.0%)
has_dayun / liunian:   2
```

**关键约束**：在断点 2 修好之前**单独**加 `evaluate_trigger` 过滤 = **断流**。
因为 204 条 `*_picture` 会因 chart 无 picture 而全 False，无冲命盘只剩 2 条。

**所以断点 2 和 3 必须连贯修。**

---

### 断点 4：域归类断

**现象 A（盲派）**：`BLIND_TOPIC_DOMAINS` 把方法论和时间维度当事件域。

```
事业域 563 条
├─ lifa（理法）448 条   ← 「月令为提纲」「盲派三大支柱体系」
├─ dayun（大运）75 条   ← 时间维度
└─ zhiye（真实事业）40 条 = 7.1%
```

**现象 B（子平）**：`theory/ziping/index.yaml` 933 条里
**820 条（87.9%）的 `domains[0]` 是「事业」**。

**后果**：拿操作手册论证职业吉凶；报告里 87.9% 的证据堆在一个域。

---

### 断点 5：置信度断

**现象**：`engine/v5/runner.py:929` 的 `_evidence_confidence` 传硬编码 `{"pillars": {}}`。

**后果**：`_route_weight` 对空四柱永远返回 0.35（四柱残缺惩罚值），
所有仲裁星级锁死 ★★。

**⚠️ 二手结论（Gemini），Opus 需复核**：它还说 `blended * weight` 有第二层算术缺陷——
ziping 的 `confidence.score` 最高 0.74，weight 0.55，乘积 0.396，
**永远够不到 ★★★ 的 0.50 门槛**。

---

### 断点 6：视图渲染断

**现象**：`engine/v5/report_view.py:288-296, 333-360` 里，
「命局做功与人生主线」四行核心结论**全部是写死的字符串常量**：

```
体结构资源: "由五派结构裁判汇总，MVP 阶段待细化。"
用现实目标: "由事件裁判与预测账本汇总，MVP 阶段待细化。"
做功路径: "五派 runner 接入后输出自力、平台、配偶、贵人、经营等路径。"
```

22 个细分指标里 **16 个硬编码 "待反馈..."**；
15 层判断摘要里 12 行是套话。

**只有「事业」域接了 L7 裁决**，其余 4 个域只截取 `event_result.conclusion` 前 80 字。

**后果**：**修通前 5 个断点，报告里仍有一半表格写着「待细化」。**

**⚠️ 二手结论（Gemini），Opus 需复核。**

---

## 三、四阶段重构方案

```
阶段 0（已完成）：P0 构建链
    ↓
阶段 1：打通 v5 事实底座（断点 1 + 2 + 5）
    · 修 16 个空四柱案例（兼容 4 种异构格式）
    · chart 挂载 energy / picture / shensha（复用 engine/facts/shensha.py 的 find_shensha）
    · _evidence_confidence 传真实 chart
    · 约 55 行代码
    ↓
阶段 2：修 B 类召回（断点 3 + 4 的 B 类部分）
    · build_ziping_production_claims 加 evaluate_trigger 过滤 + 每域 Top-K limit
    · 废除 domains[0] 截断
    · 同步更新 tests/v5/test_v5_contracts.py:220,226 和 r6_ziping_career_baseline.json
    · 约 35 行代码
    ↓
阶段 3：修 A 类域映射（断点 4 的 A 类部分）
    · BLIND_TOPIC_DOMAINS：lifa/dayun 从「事业」剥离到「总体」
    · _estimate_marriage_timing 去掉「甲寅日男命」硬编码，改为动态十神
    · 约 30 行代码
    ↓
阶段 4（排后面）：断点 6 视图渲染 + index-new 收编 + 仓库瘦身
```

---

## 四、硬约束（Opus 必须遵守）

1. **断点 2 和 3 必须连贯修**：
   单独修 3 会断流（204 条 `*_picture` 因无 picture 字段全 False）；
   单独修 2 会让 204 条恒真灌入。

2. **tests/ 是保护区**：
   可以改 baseline **数据**（如 `r6_ziping_career_baseline.json` 的预期召回数），
   但**禁止**改断言逻辑、禁止 skip/xfail/吞异常。

3. **每轮必须跑的回归**：
   ```
   python -m pytest -q                          → 229 passed
   python -m pytest tests/r10 -q -o addopts=""  → 失败数不增加（当前 4）
   python -m pytest tests/v5 -q -o addopts=""   → 130 passed
   ```

4. **禁止重构 6 套引擎**：
   asof/f09/governance/evaluation 冻结不动。
   以 `engine/facts/` 为唯一确定性事实源，v5 只做轻量消费。
   （理由：上百个契约测试绑死了各引擎的 dataclass，动刀会陷入无休止修测试泥潭）

5. **不要扩充语料**：
   瓶颈 100% 在「精确过滤与分域路由」，不在规则数量。

6. **北极星指标优先**：
   任何改动如果不能让「严格口径准确率 45.3%」或「balanced_accuracy 0.3625」有提升路径，
   就是低优先级。

---

## 五、其他已知问题（排后面）

| 问题 | 状态 |
|---|---|
| `theory/ziping/index-new.yaml` 236 条游离 | 127 唯一 ID，109 重复废稿，`quantifiable` 全缺，94 条 `has_wealth_picture` 占位符污染。**必须在断点 3 修好后才能收编** |
| `cases/` 1896 个可重算 JSON | `all.json` 446 个 12.69M + `facts_summary.json` 1.34M + `statement_index.json` 0.91M，可从 `input.md` 重新生成 |
| `META/` 巨型快照 | 三个文件 5.3M，都是某次评估的时间点快照 |
| `.gitignore` 忽略了被引用的源文件 | `theory/_ir/unified_rule_ir.yaml` 被 1 个冻结 case 引用，但已被 gitignore 且文件不存在 |
| `tests/evaluation` 320 个失败 | 8 个文件依赖已删除的 `.omo/drafts/` 草稿 |
| `tests/asof` 2 个红灯 | 模块越界导入 + 受保护文件哈希基线漂移 |

---

## 六、协作方式与 Review 流程（用户已授权 Opus 全权）

### 6.1 三角色分工

| 角色 | 承担者 | 职责 |
|---|---|---|
| **指挥官** | Opus | 读实时代码、定方案、直接改代码、**布置 Review 任务** |
| **执行者** | Opus（或按需分派的 agent） | 按方案改代码 |
| **Reviewer** | **独立 agent（用户指定）** | 只读审查，跑回归，写验收报告 |
| **桥梁** | 用户 | 在 Opus 和 Reviewer 之间传递，拍板架构决策 |

**关键设计**：Review 由**独立 agent** 执行，不由 Opus 自己审，也不由改代码的人审。

### 6.2 为什么 Review 必须独立

今天（2026-10-20）Claude 独自执行时错了 5 次，其中 4 次是被 Gemini（另一条链路的审查者）抓出来的：

| # | Claude 的错 | 谁抓到的 |
|---|---|---|
| 1 | 转述「中神是违规」 | Gemini |
| 2 | 说 index-new 是 41 条（实际 236） | Gemini |
| 3 | 说 519 条可求值（实际 480） | Gemini |
| 4 | 说 236 条质量高（实际 127 唯一 ID） | Gemini |
| 5 | 报告 T-108「成功」时没查 score | Gemini |

**共同模式：单边判断 + 把一个数字当成一个结论。**

所以：**改代码的人不能当自己的 Reviewer。**

### 6.3 Review 流程（Opus 必须遵守）

```
┌─────────────────────────────────────────────────────┐
│ 步骤 1：Opus 定方案并实施                             │
│   · 每轮改动 ≤ 80 行核心代码                          │
│   · 产出「实施说明」：改了哪些文件、为什么、预期影响      │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ 步骤 2：Opus 布置 Review 任务（写成一份任务书）         │
│   必须包含：                                          │
│   · 本轮改动的文件清单 + diff 或代码块                 │
│   · 本轮针对哪些断点、预期解决什么                      │
│   · Opus 自己的验证输出（命令 + 完整输出）              │
│   · 明确要求 Reviewer 独立跑回归，不信 Opus 的汇报      │
│   · Review 重点：Opus 自己标注「不确定的地方」           │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ 步骤 3：用户把任务书转给 Reviewer agent                │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ 步骤 4：Reviewer 独立执行（只读 + 跑命令）              │
│   · 亲自跑：pytest -q / tests/r10 / tests/v5          │
│   · 逐行审查改动，不依赖 Opus 的说明                   │
│   · 输出结论：PASSED / REWORK / ESCALATE              │
└─────────────────────────────────────────────────────┘
                      ↓
        PASSED → 进入下一轮
        REWORK → Opus 按 findings 修，重新布置 Review
        ESCALATE → 用户拍板
```

### 6.4 Reviewer 必须跑的回归（每轮）

```bash
python -m pytest -q                          → 期望 229 passed
python -m pytest tests/tools -q -o addopts="" → 期望 294 passed
python -m pytest tests/v5 -q -o addopts=""   → 期望 130 passed
python -m pytest tests/r10 -q -o addopts=""  → 期望 4 failed, 60 passed（失败数不增加）
```

**铁律**：Reviewer 只以自己跑出的退出码和 diff 为准，
**不信 Opus 的自我汇报，不信改代码的人的任何文字结论**。

### 6.5 Review 任务书模板（Opus 每轮直接套用）

```markdown
# Review 任务 · 第 <N> 轮 · <标题>

## 1. 本轮改动
- 文件清单：<path:line>
- 改动内容：<代码块或 diff>

## 2. 针对的断点
<断点编号 + 预期效果>

## 3. Opus 自己的验证输出
<命令 + 完整原始输出>

## 4. 请 Reviewer 独立执行

### 4.1 跑回归（必须自己跑，贴原始输出）
- python -m pytest -q
- python -m pytest tests/r10 -q -o addopts=""
- python -m pytest tests/v5 -q -o addopts=""

### 4.2 逐行审查
- 改动是否落在声明的范围内？越界即判 REWORK
- 是否修改了 tests/ 的断言逻辑？（只允许改 baseline 数据）
- 是否引入假阳性？（如 bool() 判空、恒真 trigger、硬编码兜底）

### 4.3 反向验证
- 本轮声称解决的问题，真的解决了吗？给出你自己的测量方法
- 有没有引入新的静默失败？

## 5. 输出要求
第一行只写：PASSED / REWORK / ESCALATE
然后给依据。不要复述 Opus 的说明。
```

### 6.6 铁律汇总

1. **改代码的人不当自己的 Reviewer**
2. **Reviewer 只信自己跑出的退出码和 diff**
3. **每轮改动 ≤ 80 行核心代码**
4. **tests/ 保护区：可改 baseline 数据，不可改断言逻辑**
5. **禁止重构 6 套引擎**（asof/f09/governance/evaluation 冻结）
6. **不要扩充语料**（瓶颈在过滤与路由，不在数量）

---

## 七、Claude 今天错过的 5 次（Opus 请重点审查这些方向）

1. 转述「r10 第 3 条是人话冒出中神」——实际中神在语料里，真因是高派缺席
2. 说 `index-new.yaml` 是 41 条——实际 236 条（`yaml.safe_load` 撞 3 个重复 `rules:` 键）
3. 说 519 条盲派规则可求值——实际只 480 条（39 条做功因 chart 无 energy 恒 False）
4. 说 236 条质量高该优先并入——实际 127 唯一 ID、`quantifiable` 全缺、94 条 trigger 占位符
5. 报告 T-108「成功」时没查 score——实际 yang/ren 的 `candidate_score` 仍是 0

**共同模式：把一个数字当成一个结论，没验证完整性。**

---

## 八、待定的战略抉择（比六个断点更上位，Opus 请裁决）

> 以下问题 Claude 无法独自决定，因为它们决定「修什么」甚至「要不要修」。
> 用户会 review Opus 的结论。

### 抉择 1：`engine/v5/` 这条「引擎自治」路线还要不要保留？

**背景**：仓库有两条报告产出路线。

#### 路线 1：CLI + Agent（用户称为 B 选项）

```
engine.cli 出确定性事实 → tools.query_theory 检索理论 → Agent（大模型）综合推理 → 人话报告
```

**样板产物**：`reports/1980-02-09-乾-庚申戊寅壬子辛丑-human-report.md`

实测质量（Claude 已读全文）：
- 带证据地址：`e001` 戊生庚、`e005` 戊生辛、`M1-D-045`、`G-XF-014`
- 明确分层：「板上钉钉」/「大概率主断」/「我不编的」
- 主动声明信息边界：「命主未提供婚姻史/职业/学历，所有应期均为前瞻，未做回测」

**这是用户第一性原则的正面样板。**

#### 路线 2：v5 引擎自治（用户称为 A 选项）

```
engine/v5/preprod.py 解析输入 → runner.py 跑规则 → report_view.py 直接吐报告
```

**问题**：`engine/v5/report_view.py` 有 **22 处硬编码桩文本**（Claude 实测）：

```
体结构资源: "由五派结构裁判汇总，MVP 阶段待细化。"
用现实目标: "由事件裁判与预测账本汇总，MVP 阶段待细化。"
做功路径: "五派 runner 接入后输出自力、平台、配偶、贵人、经营等路径。"
学校层级判断: "待反馈细分学校层级"
单位层级判断: "待反馈单位性质与层级"
资产层级判断: "待反馈资产与负债"
...
```

22 个细分指标里 16 个是「待反馈」；15 层判断摘要里 12 行是套话。
**只有「事业」域接了 L7 裁决**，其余 4 个域只截取 `event_result.conclusion` 前 80 字。

**用户的倾向**：「既然 B 选项已经能解决问题，A 选项的 v5 就没有必要了吧」

#### 但砍掉 v5 的代价（Claude 实测，需要 Opus 评估）

**依赖 v5 的生产工具（8 个）**：

```
tools/domain_analysis_cli.py
tools/domain_capability_status.py
tools/domain_feedback.py
tools/domain_prospective_cohort.py
tools/feedback_ingest.py
tools/p_series_career_blind_harness.py
tools/render_report.py
tools/render_report_v6.py
```

**依赖 v5 的测试**：

```
tests/v5/                    130 passed
tests/r10/                    60 passed, 4 failed
tests/evaluation/            538 passed（虽被 ignore）
tests/f09/                  1183 passed
tests/asof/                  609 passed
```

**关键疑点（Claude 尚未验证）**：
- 盲断评分链（`tools/blind_year_score.py` 等 9 个工具）是否依赖 v5？
  Claude grep 未发现直接依赖，但 `tools/p_series_career_blind_harness.py`
  在依赖 v5 的列表里，而 balanced_accuracy 0.3625 正是 p-series 的指标。
  **如果砍掉 v5，指标 B 的度量链路是否断？**

**请 Opus 回答**：
1. v5 是「必须保留的度量基础设施」还是「可以被 CLI+Agent 取代的报告生成器」？
2. 如果砍掉，`balanced_accuracy` 这条度量链怎么接？
3. 如果保留，22 处桩文本是修还是接受（作为"待人工补充"的显式标记）？

---

### 抉择 2：两个北极星指标是否都必要？

**背景**（详见 0.2~0.4 节）：
- 指标 A（盲断准确率 45.3%）无硬门槛，是参考基线
- 指标 B（balanced_accuracy 0.3625）有硬门槛 0.425/0.60，可 CI 化

**用户的疑问**：「这两个问题是关于什么的？是否有存在的必要性？」

**Claude 的回答**（供 Opus 参考）：
- 它们是唯一能证明「引擎 + Agent = 准确预测」的证据
- 没有它们，无法区分「重构后变准了」和「只是代码变干净了」
- 但**如果 v5 被砍，指标 B 的载体可能消失**

**请 Opus 回答**：
1. 指标 A 和 B 是否覆盖了「预测准确」的两个正交维度？
2. 有没有第三个更直接的指标（比如端到端报告的人工评审通过率）？
3. 如果只能保留一个，保留哪个？

---

### 抉择 3：六个断点还值不值得修？

**背景**：如果抉择 1 的结论是「砍掉 v5」，那六个断点里的大部分失去意义：

| 断点 | 是否只在 v5 内 |
|---|---|
| 1 四柱解析断 | **只在 v5**（`engine/v5/preprod.py`） |
| 2 事实计算断 | **只在 v5**（v5 的 chart 缺 energy/shensha/picture） |
| 3 规则召回断 | **只在 v5**（`runner.py:198`） |
| 4 域归类断 | **跨两边**（BLIND_TOPIC_DOMAINS 在 v5，但域定义影响 Agent 读法） |
| 5 置信度断 | **只在 v5**（`runner.py:929`） |
| 6 视图渲染断 | **只在 v5**（`report_view.py` 桩文本） |

**如果砍掉 v5，只剩断点 4 可能还对 Agent 有价值。**

**请 Opus 回答**：
1. 砍掉 v5 后，Agent 走 CLI 路线时，`engine.cli` 的输出够不够丰富？
   （Claude 实测：`engine.cli all --json` 返回 chart/relations/strength/structures 四层，
   但 `energy`/`picture`/`shensha` 是否在其中？**未验证**）
2. 如果 CLI 输出不够，该扩展 CLI 而不是修 v5？
3. 六个断点应该全部取消、部分保留、还是全部保留？

---

### 抉择 4：`engine/facts/` 是不是唯一事实源？

**背景**：Gemini 建议「以 engine/facts/ 为唯一事实源，v5 只做轻量消费」。
但如果 v5 被砍，这个建议是否升级为「engine/facts/ 是唯一引擎，其他全部冻结」？

**已实测的事实**：
- `engine/facts/` 在 `pyproject.toml` 的 testpaths 内（229 测试保护）
- `engine/v5/preprod.py` 和 `runner.py` 对 `engine.facts` **零引用**
- `engine/energy/` + `engine/picture/` 有纯函数实现（`evaluate_energy` / `match_picture`），
  段派做功、杨派画面、任派应期、高派神煞四套确定性计算器
- 但这四套由 `engine/application/pipeline_runner.py` 编排，**不在 v5 主链上**

**请 Opus 回答**：
1. 如果 v5 被砍，`engine/energy/` + `engine/picture/` 应该由谁调用？
   CLI 直接暴露？还是 Agent 自己算？
2. 四派确定性计算器（D1 做功 / D2 画面 / D3 应期 / D4 神煞）是引擎职责还是 Agent 职责？

---

## 九、Opus 请回答的完整问题清单

合并第八节（技术）和新增的四个战略抉择：

### A. 战略层（决定方向）

1. **v5 砍不砍？**（抉择 1）
   - 砍：给出 `balanced_accuracy` 度量链的接法
   - 不砍：给出 22 处桩文本的处理方案
2. **两个北极星指标保留几个？**（抉择 2）
3. **六个断点该取消、部分保留、还是全修？**（抉择 3）
4. **`engine/facts/` 是否升级为唯一引擎？**（抉择 4）
   - 如果是，`energy`/`picture`/`shensha` 该由 CLI 暴露还是 Agent 计算？

### B. 技术层（决定实现）

5. **复核 6 个断点**：哪些确认、哪些推翻？断点 1/5/6 是二手结论。
6. **如果 v5 保留**，四阶段顺序对不对？
7. **如果 v5 砍掉**，Agent 走 CLI 路线缺什么？CLI 该扩展哪些输出？
8. **我可能错在哪**：Claude 已错 5 次（见第七节），请重点审查方向判断。

### C. 输出格式

先回答 A（战略），再回答 B（技术）。
**如果 A 的答案是「砍掉 v5」，B 的大部分可能不需要回答**——这会大幅减少工作量。

