# 2026-07-30 对话总结报告

> 生成时间：2026-07-30  
> 覆盖范围：当日完整工作内容，含架构决策、工具交付、验证结果与下一步路线图

---

## 一、背景与目标

本次对话的核心任务是推进 mangpai-fusion 系统的**as-of 求测闭环**，解决"先盲断、后核验"的认识论缺口——系统此前只在"已知答案"的条件下生成报告，从未在"不知道答案"的条件下测试过盲断准确率。

---

## 二、主要交付成果

### 2.1 排盘引擎：lunar-python 验证与修复

**问题**：批量排盘管道被阻断，原因是 RF000449、RF000957 两案起运年龄差约8年。

**诊断过程**：
1. 语料库检索发现两套起运法（盲派粗略 vs 港台精确）和"只用十二节"规则
2. 实现 [`engine/asof/qiyun_calculator.py`](engine/asof/qiyun_calculator.py)，假设"顺逆方向数到相反方向的节"可解释差异
3. 验证失败（假设不成立）
4. **关键突破**：用户在问真APP排盘3个判别性合成案例，结果完全否定"最近节"假设，支持"顺逆方向"规则——与 lunar-python 的规则完全一致
5. **根因确认**：RF000449/RF000957 的起运数据是批量OCR转案时的抄录错误，不是 lunar-python 的问题

**修复结果**：
- [`engine/asof/birth_to_bazi.py`](engine/asof/birth_to_bazi.py)：四柱排盘验证 35/35（100%），顺逆方向 35/35（100%）
- RF000449/RF000957 两案 `input.md` 起运数据已修正（附可追溯修正记录）
- 批量排盘阻断正式解除

---

### 2.2 批量排盘管道

**工具**：[`tools/as_of_raw_feedback_paipan.py`](tools/as_of_raw_feedback_paipan.py)

**关键功能**：
- 23:00-23:59 晚子时硬性排除（默认启用，CLI 有强制放行开关）
- 按 `duplicate_key` 自动去重
- 只处理 `calendar_type=solar`
- 支持 `dry_run` 模式

**规模**：
- 992 个原始反馈 → 451 个 solar+有时辰 → 16 个 23:xx 排除 → **438 个自动排盘案例**
- 农历（359份）、阳历未注明（181份）待后续处理

---

### 2.3 截止态候选扫描与筛选

**目标**（原始设定）：找含2024年后现实截面描述的候选，用于 as-of 盲断

**流程**：
1. `scan_feedback_current_state()` 扫描：438 个案例 → 44 个启发式候选（10%命中率）
2. 人工逐案复核：44 → **26 个 CONFIRM**（18 个 REJECT 为假阳性/未来提问）
3. 为 26 个 CONFIRM 生成 [`asof-freeze-scaffold-draft.json`](cases/C-2026-RF000737-坤-辛酉癸巳辛卯戊戌/asof-freeze-scaffold-draft.json)

---

### 2.4 as-of 盲断闭环新增案例

**本日新增5案**（RF000737/302/360/356/163）：
- E1 结果：**全部 ABSTAIN**
- 原因：自动排盘案例的 feedback.md 是历史事件年表，缺少"截止当前状态+变化前后对比"结构（§9.4格式），无法进入日期事件精度分母

**当前评分池状态**（总20个闭环案例）：

| 评分单位 | 可评估 | 命中 | 命中率 |
|---|---|---|---|
| 截止日职业基本面 | ~5 | ~3 | ~60% |
| 宽阶段方向 | ~19 | ~17 | ~89% |
| 日期事件精度 | 13 | 10 | 77% |

---

### 2.5 新增工具族

| 工具 | 功能 |
|---|---|
| [`engine/asof/birth_to_bazi.py`](engine/asof/birth_to_bazi.py) | lunar-python 排盘适配器（四柱+大运）|
| [`engine/asof/qiyun_calculator.py`](engine/asof/qiyun_calculator.py) | 独立起运计算器（十二节+顺逆+两套口径）|
| [`engine/asof/annual_trace.py`](engine/asof/annual_trace.py) | L1+L2 应期门控（gate_yingqi 适配层）|
| [`tools/as_of_raw_feedback_paipan.py`](tools/as_of_raw_feedback_paipan.py) | 原始反馈批量自动排盘管道 |
| [`tools/as_of_running_stats.py`](tools/as_of_running_stats.py) | 滚动统计聚合 + 历史快照追加 |
| [`tools/as_of_candidate_prioritizer.py`](tools/as_of_candidate_prioritizer.py) | 候选案例优先级自动排序 |

---

### 2.6 验证报告

| 报告 | 内容 |
|---|---|
| [`reports/lunar-python-validation-c2026-cases-2026-07-30.md`](reports/lunar-python-validation-c2026-cases-2026-07-30.md) | C-2026 案例排盘正确性验证（96.7%匹配率，C-2026-030是唯一晚子时差异）|
| [`reports/qiyun-calculator-validation-2026-07-30.md`](reports/qiyun-calculator-validation-2026-07-30.md) | 起运计算器验证（假设不成立，原因是阻断数据本身有错）|
| [`reports/as-of-scaffold-section9-4-quality-ranking-2026-07-30.md`](reports/as-of-scaffold-section9-4-quality-ranking-2026-07-30.md) | §9.4 质量排名 |
| [`reports/as-of-new-toolchain-cohort-validation-2026-07-30.md`](reports/as-of-new-toolchain-cohort-validation-2026-07-30.md) | 新工具链队列验证 |
| [`reports/as-of-paipan-current-state-candidates-2026-07-30.md`](reports/as-of-paipan-current-state-candidates-2026-07-30.md) | 截止态候选清单（44个）|
| [`reports/as-of-paipan-candidate-review-2026-07-30.md`](reports/as-of-paipan-candidate-review-2026-07-30.md) | 人工复核报告（26个CONFIRM）|
| [`reports/as-of-running-stats-history.jsonl`](reports/as-of-running-stats-history.jsonl) | 历史统计快照时间线 |
| [`docs/as-of-blind-judgment-protocol.md`](docs/as-of-blind-judgment-protocol.md) | as-of 盲断协议操作手册 |

---

## 三、关键认识

### 3.1 as-of 盲断协议的局限性

当前协议设计强调"截止当前状态"，但：
- 原始反馈库里的 feedback.md 大多是历史事件年表，不是"截止态描述"
- 5个新案例全部 ABSTAIN 说明：**协议正确，但数据源不匹配**
- 真正能满足协议要求的案例（有2024年后现实截面+前后对比）很稀少

### 3.2 职业判断准确性：更大的机会

用户指出：**不需要截止态，只关心职业判断准确性**。

这开启了一个更大的验证机会：
- 992个原始反馈中有 **617个含职业信息**（`profile.occupation`）
- 不需要截止日，不需要年份表，直接对比系统职业判断 vs 实际职业
- 可评估样本：**617个**（是当前事件精度可评估样本 13个 的 47 倍）

**评估方式**（宽松分类）：
- 技术专业输出型（程序员/工程师/医生/律师等）
- 管理资源调配型（管理层/公务员/党政军）
- 商业财运主导型（老板/销售/个体户）
- 艺文创意服务型（教师/艺术家/服务业）
- 其他（学生/无业/退休等，暂不评估）

---

## 四、数据污染问题

**问：用617个案例评估事业/财富后，婚姻/学业领域的数据是否被污染？**

**答：不会**，因为：
- 污染只在"评估→修改规则→用同批数据验证修改后规则"这个循环里发生
- 只读取职业信息做准确率评估，不修改任何规则，其他领域数据仍然干净
- 即使根据结果修改了事业规则，也只污染"事业"维度，婚姻/学业仍干净

**建议**：现在就划出 100-150个永久holdout集（`cases/holdout/`，任何评估都不用），为将来的严格独立验证保留干净数据。

---

## 五、下一步路线图

### 优先级1：职业判断准确率批量评估（高价值，立即可做）

1. 为438个已排盘案例运行职业方向分类（4大类）
2. 与 `profile.occupation` 做宽松映射
3. 计算分类命中率，找出高错误类别
4. 可扩展到全部有职业信息的617个案例（含农历案例需排盘）

### 优先级2：holdout集切割（预防性，应立即做）

随机选150个案例存入 `cases/holdout/`，任何时候都不读取

### 优先级3：as-of 盲断协议改进（中期）

- 当前协议只适用于"有截止态描述"的案例，样本稀少
- 考虑放宽为：职业方向判断（不强求年份事件精度），可用案例大幅增加
- 或改为从2025年起新入库的案例强制要求§9.4格式

### 优先级4：农历案例排盘（中期）

- 359个农历案例可通过lunar-python农历转阳历处理
- 181个"阳历未注明"案例需要人工确认历法

---

## 六、测试状态

全部工具测试：**600 passed, 1 skipped, 1 warning**（截至2026-07-30结束时）

所有工作区根目录临时文件已清理。
