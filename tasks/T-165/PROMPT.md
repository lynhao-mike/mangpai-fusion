# T-165 · 婚姻应期可行性审计（382 例，只读）

- 状态：🔵 Ready for Execution
- 优先级：**P0（外部复审接受后的第一步；只读，不建模）**
- 创建：2026-10-29（中枢）
- 依据：`docs/reviews/external-review-adjudication-v1.md` §1–§6；T-148 应期集
- 前置：T-148 已完成（`482d777b`）

## 0. 一句话

判断「382 例婚姻应期 + 现有大运/流年原语」能否支撑一个**零年龄参数**的 Top-K 年份预测模型；
列出缺口与预注册设计。**只读审计：不建模、不评分、不建盘。**

## 1. 已知事实（不要重复验证）

- `META/timing-eval-set-v1.json`：382 例 `usable_for_timing`，有 `birth_dt`、性别、婚姻事件年份；
  基线：24–30 岁 45.3%、20–30 岁 63.1%、22–28 岁 48.7%、26 岁 11.2%。
- `condition_ir` 有 4 个岁运原子：`suiyun_edge`、`sanhe_with_suiyun`、`chong_kai_muku`、`liunian_present`；
  能消费 `scope != natal` 的边（T-145）。
- 产品路径不走 `condition_ir`；本卡不要求把它接进产品，只盘点能力。

## 2. 审计内容（只读）

### 2.1 案例可用性

- 382 例里：`birth_dt` 可解析多少、有性别多少、能建盘多少、婚姻事件年份落在可计算大运/流年区间多少；
- 每例可评分的年份范围（建议 20–35 岁）有多少个；是否每例都有至少一个婚姻事件年份在范围内。

### 2.2 原语盘点

逐项回答：现有代码能否在**某一具体流年**上回答以下问题，并给出函数/字段位置与一个真实例子：

1. 流年支与日支 `D.b` 是否构成冲/合/刑/穿/害；
2. 大运支与日支 `D.b` 是否构成冲/合/刑/穿/害；
3. 流年/大运是否引动配偶星（财/官）所在柱；
4. 墓库是否被冲开/合开（`chong_kai_muku` 的输入输出）；
5. 三合/三会是否把夫妻宫合入/合走（`sanhe_with_suiyun`）；
6. 大运/流年与原局的关系边是否有稳定 `edge_id` 可引用。

明确写「有 / 无 / 部分」，不许用「大概」。

### 2.3 评价设计（提案，不执行）

- 每例在 20–35 岁打分，取 Top-K（K=3/5/7）；
- 与「同宽度年龄窗口」基线比：24–30 岁 45.3%、20–30 岁 63.1%；
- 零年龄参数：规则只看干支关系，不按年龄调权；
- 预注册判据：命中率高出对应基线 ≥ +8pp 且 p<0.01 算有信号；< +3pp 或 p>0.20 判死；
- 说明 382 例下的统计功效，以及为什么这个设计比静态 342 例更有力。

### 2.4 缺口

- 缺哪些事实（如大运/流年十神地址、墓库开闭、配偶星柱位绑定）；
- 缺哪些工程（如批量计算 382 例 × 16 年 × 4 原语的性能/入口）；
- 给出「能直接开工 / 需先补 1–2 个原语 / 不可行」的明确结论。

## 3. 产物

- `META/timing-feasibility-audit-v1.json`：计数、原语矩阵、每例覆盖、缺口
- `META/timing-feasibility-audit-v1.md`：人读报告 + 预注册设计草案
- 可选 `tests/tools/test_timing_feasibility_audit.py`（确定性）

**禁止**建模、评分、生成应期预测、建盘写入；只读。

## 4. File Scope

**允许新建**

- `tools/timing_feasibility_audit.py`
- `META/timing-feasibility-audit-v1.json`
- `META/timing-feasibility-audit-v1.md`
- `tests/tools/test_timing_feasibility_audit.py`（可选）

**只读**

- `META/timing-eval-set-v1.json`、`META/timing-baseline-v1.json`
- `engine/facts/**`、`engine/api/**`、`engine/asof/**`、`engine/energy/**`、`engine/claims/condition_ir/atoms.py`
- `theory/production/claim-rules-v1.yaml`

**禁止**

- 改 `engine/**`、T-148 产物、规则、`condition_ir`、既有测试
- 建模/评分/写预测
- `git commit / push / checkout / stash / reset / clean`

## 5. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m tools.timing_feasibility_audit        # 退出码 0
.venv\Scripts\python.exe -m pytest -q                              # 0 failed，passed >= 1246
```

中枢额外检查：

- 382 例覆盖数可加；
- 原语矩阵每项都有代码位置与一个真实例子；
- 预注册设计里没有年龄参数；
- 缺口结论明确，不许「差不多可以」。

## 6. 回报格式（`tasks/T-165/BRIEF.md` + `STATUS.md`）

1. **改动文件**
2. **原始输出**（覆盖数 + 原语矩阵 + 缺口）
3. **未完成与风险**（性能、边界、大运顺逆）
4. **下游须知**（能否直接开工、先补什么、预注册草案）

## 7. 禁止

- 不许写模型/评分代码。
- 不许把「4 个岁运原子存在」当成「应期可算」；必须逐项给例子。

## 7. 中枢裁决（2026-10-29 01:30）

1. **岁运原子实际 6 个**（卡 §1 写 4）：另有 `dayun_present`、`suiyun_arrives`；后者是段派「到位」，建议下一张卡纳入。
2. **382 例基线更正**：22–28 岁 **49.2%**、26 岁 **11.8%**（卡上 48.7% / 11.2% 是 392 例口径）；
   24–30 45.3%、20–30 63.1% 不变。
3. **同 K 基线陷阱（必须先解决）**：Top-K 预测必须与**同 K 静态年龄带**比
   （K=3 **26.7%**、K=5 **39.27%**、K=7 **49.21%**），不能拿 7 年窗口的 45.3% 当基线。
   若模型的 +8pp 仍低于同 K 门槛，**不算有信号**。
4. **结论接受**：能直接开工（R1–R4 不改 `engine/**`）；K=3 主检验，功效 0.919、MDE 6.75pp；
   合开墓库、跨年稳定 `edge_id` 为非阻断缺口；16 个候选年不把 n 变成 6112。
5. 本卡只读，未建模、未评分；建模另立卡，需人类签字。
