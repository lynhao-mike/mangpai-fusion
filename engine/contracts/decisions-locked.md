# v1.2 重构决策面板（已锁定）

> **本文是 v1.2 重构 W2/W3/W4 阶段所有 agent 的"红线手册"**。
> 决策一旦锁定即写入此文档；后续修改需 PR + 整合 agent 批准（流程见 00 § 十）。

最后更新：2026-05-23 · 由 Track-D 整理（基于 Track-C/D 实战 + 用户最终拍板）
适用范围：v1.2 重构期间（W2 - W6 发布）

---

## 总览：13 项决策（A - M）状态

| 决策 | 主题 | 选项 | **锁定值** | 锁定时间 | 锁定人 |
|---|---|---|---|---|---|
| **A** | 排盘外部化 | (1)自算/(2)外部/(3)自算干支大运+外部神煞 | **(3)** | W1.1 | User |
| **B** | DSL 形态 | (1)纯 YAML / (2)YAML+Python 谓词库 / (3)嵌入 DSL | **纯 Python** | W2 末（Track-C/D 实战后调整）| User |
| **C** | 做功能量量化 | (1)纯序数 / (2)浮点+序数 / (3)纯数值 | **(2)** | W1.1 | User |
| **D** | 引擎 vs AI | (1)只 JSON / (2)死板 MD / (3)骨架+AI 润色 | **(3)** | W1.1（Track-F 落地时确认）| User |
| **E** | 置信度更新 | (1)简单计数 / (2)Beta 分布 / (3)时间衰减 | **(1)→(2)** 切换条件：≥30 反馈 | W2 末 | User |
| **F** | 升降级阈值 | (1)全自动 / (2)升自动+降人工 / (3)全人工 | **(2)** 默认（按 05 契约）| W1.3 | User |
| **G** | 失验规律处理 | (1)立刻降 / (2)累计 3 次降 / (3)仅记录 | **(2)** 默认（按 05 契约）| W1.3 | User |
| **H** | 协作交付 | (1)PR 子分支 / (2)直推主干 / (3)各分支整合合并 | **PR-based（v1.2 重构期间）** / 重构后恢复直推 main | W2 末 | User |
| **I** | 发布门槛 | (1)3 案回放 / (2)+2 新案 / (3)严格优于 v1.0 | **(3)** | W1.1 | User |
| **J** | 预测封存 | (1)人工封存 / (2)引擎自动抽取 | **(2)** | W1.1（按 07 契约）| User |
| **K** | 跨派扫描 | (含频率) | **每 10 案扫描一次** | W1.1 | User |
| **L** | 案例命名 | (含干支后缀)  | **加干支后缀**（C-2026-001-庚申戊寅壬子辛丑）| W1.1 | User |
| **M** | 优先级保底 | (含降级链) | **E > A > C > G > 其他** | W1.1 | User |

---

## 决策 B 详细说明（W2 末关键调整）

> **背景**：W1 设计时推荐 (2) "YAML 结构 + Python 谓词函数库"。
> Track-C / Track-D 实战后，发现纯 Python 体验远好于 YAML+Python 混合，于 W2 末改为纯 Python。

### 红线规则

| 项 | 允许 | 禁止 |
|---|---|---|
| **判定逻辑** | `.py` 函数 + dataclass + Python list | YAML 表达分支 / 嵌套 if-else / 优先级排序 |
| **规律 metadata** | YAML（rule_id / source / domain / 适用范围 / 描述文本）| 把判定逻辑硬编码到 metadata |
| **配置参数** | YAML（confidence.yaml / domain-weights.yaml / level-scales.yaml 等阈值表）| 把"如果 A 则 B 否则 C"逻辑放进 YAML |

### 反例（不允许）

```yaml
# ❌ YAML 不应表达判定逻辑
- rule_id: M3-R-031.6
  trigger:
    type: 倒象
    condition:
      if:
        and:
          - has_real_sheng: true
          - has_real_ke: true
          - has_he: true
          - delta_types_count: ">= 2"
        then: is_xiong = true
```

### 正例（允许）

```yaml
# ✓ YAML 仅描述 metadata
- rule_id: M3-R-031.6
  school: 任
  source: m3-mechanics §17 第 6 条
  domain: [婚姻, 事业, 财运, 健康, 学业, 六亲]
  description: 倒象成立 = 必凶铁律
  base_strength: 0.85
  type_bonus: 0.05
```

```python
# ✓ Python 实现判定逻辑（engine/yingqi/chufa.py）
def detect_daoxiang(parsed, year, yong_shen_chars):
    """倒象判定：增量法 (baseline vs active)。"""
    # ...纯 Python 逻辑...
```

### 证据：实战教训

Track-C 实施过程中（v1.2-track-C 分支）：
- 6 触发引擎的判定逻辑 (chufa.py 681 行) 用 Python dataclass + 函数表达，**清晰且 IDE 类型检查覆盖**
- 12 道门优先级排序 (menshu.py 713 行) 用 `_DoorMatch.priority` int + sorted() 表达，**50 行 vs YAML 200 行嵌套结构**
- 倒象判定 (chufa.py 增量法) 涉及 baseline vs active 集合差，YAML 表达不出来

---

## 决策 E 详细说明（置信度切换路径）

### 当前阶段（W2-W4）：线性加权

```python
# engine/yingqi/gate.py · compute_yingqi_confidence()
posterior = primary_strength + trigger_bonus + type_bonus
# - primary_strength: 06 § 4.1 触发类型基础强度
# - trigger_bonus: 多触发奖励 min(0.10, (n-1)*0.04)
# - type_bonus: 06 § 4.1 触发类型加成
```

### 切换条件

当 `cases/` 目录下"feedback hit/miss 总样本量 ≥ 30 条"时，由 Track-G 自迭代触发切换。

### 切换后（W5+）：Beta 分布

```python
# 计算 Beta(α=hits+1, β=misses+1) 后验
posterior = (hits + 1) / (hits + misses + 2)  # 期望值
variance = posterior * (1 - posterior) / (hits + misses + 3)  # Beta 方差
```

切换后保留 `posterior_to_star()` 映射不变（06 § 二）。

---

## 决策 H 详细说明（协作分支策略）

### v1.2 重构期间（W2 - W6）

```
main                       ← v1.0 服务旧报告（不冻结）
 └── v1.2-build            ← 长生整合分支
      ├── v1.2-track-A     ← Track-A agent 工作（PR #8 已合）
      ├── v1.2-track-B     ← Track-B agent 工作（PR #11 已合）
      ├── v1.2-track-C     ← Track-C agent 工作（PR #13 已合）
      ├── v1.2-track-D     ← Track-D agent 工作（PR #14 待合）
      ├── v1.2-track-G     ← Track-G agent 工作（PR #9 已合）
      ├── v1.2-track-H     ← Track-H agent 工作（PR #10 已合）
      ├── v1.2-track-F     ← Track-F agent 工作（W3 启动）
      └── v1.2-w3-integration ← W3 集成日（整合 agent 接入 G1~G4 regression）

每个 track 分支完成 → PR 到 v1.2-build → 整合 agent review + merge
v1.2 全部 Track 完成后 → v1.2-build 一次性合并到 main → 发布 v1.2
```

### v1.2 发布后

恢复用户原偏好"直推 main 不开新分支"。本决策仅 v1.2 重构期间临时生效。

---

## 决策 I 发布门槛（量化指标）

详见 `tests/regression/test_v1_2_vs_v1_0.py` 实现：

| 编号 | 指标 | v1.0 基线 | v1.2 限值 | 实施 |
|---|---|---|---|---|
| **G1** | 三案核心铁断命中数 | 5 | ≥ 6 | Track-H 框架已写，待 W3 接入 D1+D2+D3+D4 pipeline |
| **G2** | C-2026-001 婚期误差 | 8 年 | ≤ 3 年 | Track-C 已实现，G2 圣杯本地端到端 0 年（PASS） |
| **G3** | C-2026-002 婚姻失验数 | 4 | ≤ 1 | 待 W3 接入 |
| **G4** | C-2026-014 学历过判档数 | +1 | = 0 | 待 W3 接入 D2+D4 pipeline |
| **G5** | trace_id 覆盖率 | 0% | 100% | 待 W3 集成日 + Track-F |
| **G6** | ★★★★★ 三层 gate 通过率 | 0% | 100% | Track-C 已强制约束（passed_layers=3 才允许 ★5）|

---

## 修改本文流程

修改任何决策项 = PR 标题前缀 `[DECISION]` + 必须列出影响的 Track + 整合 agent 批准。
如影响 ≥ 3 个 Track 或导致代码重写，必须暂停在做的 agent 工作 1 工作日。

---

## 历史版本

| 版本 | 时间 | 修改 |
|---|---|---|
| v1.0 | 2026-05-23 W2 末 | Track-D 整理首版（13 项决策全部锁定）|
