# T-105 · 语料质量普查：量化 3699 条规则的有效性

## Review Level: 1

> 定级理由：纯只读勘察 + 产出报告，不修改任何代码、测试、配置或语料。
> 唯一的写操作是新建 `tasks/T-105/REPORT.md`。属于机械型任务。

## Context（中枢只读勘察已确证，Worker 无需重复勘察）

**语料家底（2026-10-19 实测）：**

| 流派 | 规则数 | 原始语料 | 密度（条/K） |
|---|---|---|---|
| 滴天髓/调候 | 1108 | 828K | 1.34 |
| 子平真诠 | 933 | 704K | 1.33 |
| 高德臣（盲派） | 630 | 1.1M | 0.57 |
| 段建业（盲派） | 428 | 4.6M | 0.09 |
| 杨清娟（盲派） | 400 | 4.6M | 0.09 |
| 任付红（盲派） | 200 | 1.4M | 0.14 |
| **合计** | **3699** | **13.2M** | — |

**已知的问题（来自 r10 回归勘察，已核实）：**

1. **盲派三派（gao/duan/yang）的规则一条都没有 `condition` 或 `trigger` 字段**，
   导致 `blind_rule_gate`（`engine/predicates/condition_evaluator.py:208`）只能走关键词兜底：
   提到「冲」→ 查命盘有无地支冲；提到「墓/库」→ 查有无辰戌丑未。
   后果：只要命盘含辰戌丑未，所有提「墓库」的规则全部被选中。

2. **`BLIND_TOPIC_DOMAINS`（`engine/v5/runner.py:52`）覆盖不全：**
   - `liuqin`（六亲）**不在映射表里**，也不在兜底关键词里 → 只能靠正文猜
   - `shensha`（神煞）被映射成 **「健康」** —— 这个映射在语义上存疑
   - 报告发现 `jiaoyu`/`geju`/`tihou`/`liuqin`/`yingqi`/`unmapped` 六个 topic 未映射

3. **域分布极不均衡**（以高派为例）：
   `shensha 131 / caiyun 115 / mingong 85 / hunyin 75 / dayun 71 /
    xiangfa 56 / lifa 46 / zhiye 20 / jiankang 16 / liuqin 15`
   —— 事业只有 20 条，六亲只有 15 条。

## Objective

量化回答三个问题，为「语料该不该继续扩充、扩充哪里」提供决策依据：

**Q1. 可精确求值的规则有多少？**
逐派统计有 `condition` / `trigger` 字段的规则条数与占比。

**Q2. 能正确归域的规则有多少？**
逐派统计：
- `topic` 在 `BLIND_TOPIC_DOMAINS` 中的（精确映射）
- `topic` 不在表中但能靠正文关键词兜底成功的（模糊映射）
- 两者都不行的（无法归域 = 纯噪音）

**Q3. 抽取质量如何？**
抽样检查（每派 ≥20 条随机样本）：
- `conclusion` 是否为空 / 过短（<10 字）/ 是否为纯标题复述
- `raw_anchor` 是否存在且能定位到原文
- 是否存在明显重复（title 或 conclusion 高度相似）

## File Scope

**只读**（禁止修改）：
- `theory/*/index.yaml`（6 个文件）
- `engine/v5/runner.py`（只看 `BLIND_TOPIC_DOMAINS` 与 `_blind_rule_domain`）
- `engine/predicates/condition_evaluator.py`（只看 `blind_rule_gate` / `score_blind_rule`）

**唯一可写**：
- `tasks/T-105/REPORT.md`

## Steps

### Step 0: Preflight

- [ ] 确认 6 个 index.yaml 可读，规则数与上表一致
- [ ] 读 `BLIND_TOPIC_DOMAINS` 与 `_blind_rule_domain` 全文，理解映射逻辑

### Step 1: 写普查脚本（临时，不入库）

- [ ] 用 Python 解析 6 个 index.yaml（注意：文件头有 `#` 注释，且 gao 的
      `Generated at:` 行有异常文本 `The system cannot accept the date entered.`，
      解析时要容忍）
- [ ] 统计 Q1、Q2 的硬指标
- [ ] 脚本可放 `tasks/T-105/` 下，或直接用 `python -c`，不入库即可

### Step 2: 抽样人工核查 Q3

- [ ] 每派随机抽 ≥20 条，人工看 conclusion 质量
- [ ] 记录典型问题（举实例，不要只给百分比）

### Step 3: 产出报告

- [ ] 写 `tasks/T-105/REPORT.md`

## Completion Criteria（可执行命令 + 期望退出码）

| # | 命令 | 期望 |
|---|---|---|
| 1 | `python -c "..."` 普查脚本 | **exit 0**，输出 6 派 × 3 类统计 |
| 2 | `git status --porcelain` | 只有 `tasks/T-105/`，**无其他改动** |
| 3 | `git diff --stat` | **空**（未修改任何已跟踪文件） |
| 4 | `tasks/T-105/REPORT.md` 存在 | 含 Q1/Q2/Q3 三节，每节有具体数字与实例 |

## REPORT.md 必须包含

```markdown
## Q1 可精确求值的规则
| 流派 | 总条数 | 有 condition/trigger | 占比 |

## Q2 归域正确性
| 流派 | 精确映射 | 模糊兜底 | 无法归域 | 主要问题 topic |

## Q3 抽取质量抽样
| 流派 | 样本数 | 空/过短 conclusion | 重复 | raw_anchor 缺失 |
（每类问题附 2-3 个真实实例）

## 结论：扩充建议
- 哪些派/哪些域最该补
- 哪些派现有规则质量不足以支撑扩充（先修质量再加量）
- 对 BLIND_TOPIC_DOMAINS 的具体修改建议
```

## Do NOT

- **禁止修改任何 `theory/*/index.yaml`**——它们是 `tools/build_indexes.py` 生成的产物
- **禁止修改 `engine/` 下任何文件**
- **禁止修改任何测试**
- **禁止执行 `git commit` / `checkout` / `stash` / `reset` / `clean`**
- **禁止运行 `tools/build_indexes.py`**（会重写 index.yaml）
- 禁止读取 File Scope 之外的文件
- **禁止下结论说「应该扩充到 N 条」**——只给数据与判断依据，扩充规模由中枢决策

## Deliverables

- `tasks/T-105/REPORT.md`：三节统计 + 实例 + 扩充建议
- 更新 `tasks/T-105/STATUS.md`
