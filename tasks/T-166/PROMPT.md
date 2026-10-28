# T-166 · 婚姻应期模型 v1（R1–R4，零年龄参数，只出分数）

- 状态：🔵 Ready for Execution
- 优先级：**P0（应期首测）**
- 创建：2026-10-29（中枢）
- 依据：`META/timing-feasibility-audit-v1.md`（T-165）；`docs/reviews/external-review-adjudication-v1.md`
- 前置：T-165 已完成（`8b1af43b`）

## 0. 一句话

在 382 例婚姻应期集上，用**零年龄参数**的干支规则 R1–R4 给 20–35 岁每一年打分，
**只输出分数，不计算任何准确率/命中率**。评分由独立的 T-167 评测器、由中枢一次性跑。

## 1. 预注册（卡内即协议，不得中途改）

### 1.1 总体

- 数据：`META/timing-eval-set-v1.json` 中 `usable_for_timing=true` 的 **382 例**。
- 候选人年：**20–35 岁**（含两端，16 年/例）= 6112 case-year。
- **零年龄参数**：`score_year(chart_facts, year, dayun_index)` 不接收 `birth_year`、不按年龄调权；
  出生年只用于生成候选年。

### 1.2 规则（无权重，每项 +1）

- **R1 夫妻宫引动**：流年支与 `D.b` 的边，按 kind 去重（`chong` / `he` / `xing` / `chuan`），
  每种 +1，最多 4。
- **R2 配偶星引动**：按性别取配偶星（男命财星、女命官杀），取其**地支地址**；
  每个地址若受流年 `chong` 或 `he`，+1，最多 2；取不到配偶星地址 → R2=0，并记 `no_spouse_star`。
- **R3 冲开墓库**：该流年冲开任一墓库 → +1（只认冲开；合开是已知缺口，不补，记 `muku_open_by_he_missing`）。
- **R4 三合/三会引动**：含 `D.b` 的三合/三会且 `scope` 含流年 → +1。
- **score = R1+R2+R3+R4**（整数 0–8）。

### 1.3 排序与输出

- 每例按 `(-score, sha256(case_id|year) 升序)` 排序；Top-3 由评测器取，模型不取。
- 若正分年 < 3，仍输出全部 16 年分数，并记 `positive_years`；不补齐、不猜。
- 产物 `META/timing-scores-v1.json`：
  - `protocol_id`、`frozen_at`、`git_head`、`population`、`rules`
  - `cases[]`：`case_id`、`birth_year`、`years[]`（`year`、`score`、`components{r1,r2,r3,r4}`、`edges[]`、`flags[]`）
- **不得**读 `marriage_events`、不得算命中率、不得写报告结论。

## 2. 实现约束

- 新建 `tools/timing_model_v1.py`；`python -m tools.timing_model_v1` 幂等、退出码 0。
- 建盘/取事实复用 `engine.api` / `engine.facts`（只读）；**不改 `engine/**`**。
- 流年边用 `relations.edges` 中 `scope != natal` 的边；`edge_id` 不稳定（T-165：381/382 跨年变），
  一律用 `(chart_id, dayun_index, liunian_year, edge_id)` 复合键记录，不依赖裸 id。
- 墓库：优先复用 T-165 已验证的 `chong_kai_muku` 调用；否则用 `relation_graph` 的 muku 事实 +
  流年冲边实现，并在报告中注明来源。
- 配偶星地址：复用 `engine/facts` 的十神/地址；取不到就 0 + flag，不许猜。
- 同时写 `META/eval-protocols/timing-k3-v1.yaml`（11 字段，见 `META/eval-protocol-v1.md`），
  `frozen_at` 用本卡时间，`commit` 用当前 HEAD。

## 3. 测试（新建 `tests/tools/test_timing_model_v1.py`）

1. `score_year` 签名不含 `birth_year`（inspect.signature）；
2. 同一输入两次输出逐字节一致；
3. 3 个真实年份的 `components/edges` 能回 `engine.cli` 的关系边；
4. 源码 `grep marriage_events` = 0；
5. 正分年 <3 的构造例：输出 16 年、`positive_years` 正确、不补齐。

## 4. File Scope

**允许新建**

- `tools/timing_model_v1.py`
- `META/timing-scores-v1.json`
- `META/eval-protocols/timing-k3-v1.yaml`
- `tests/tools/test_timing_model_v1.py`

**只读**

- `META/timing-eval-set-v1.json`（只读 `case_id/birth_year/birth_dt/gender`，**不读 `marriage_events`**）
- `engine/facts/**`、`engine/api/**`、`engine/predicates/**`、`engine/claims/condition_ir/atoms.py`
- `META/timing-feasibility-audit-v1.md`

**禁止**

- 改 `engine/**`、规则 YAML、T-148/T-165 产物、既有测试
- 读 `marriage_events`、算准确率/命中率、调权重/阈值
- `git commit / push / checkout / stash / reset / clean`

## 5. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m tools.timing_model_v1        # 退出码 0
.venv\Scripts\python.exe -m pytest tests/tools/test_timing_model_v1.py -q -o addopts="-ra --tb=short"
.venv\Scripts\python.exe -m pytest -q                     # 0 failed，passed >= 1303
```

中枢额外检查：

- 分数 JSON 每例 16 年、`components` 可加等于 `score`；
- `grep -E "marriage_events|命中率|accuracy" tools/timing_model_v1.py` = 0；
- 3 个年份的边可回 `engine.cli`；
- 没有改 `engine/**`、没有调权重。

## 6. 回报格式（`tasks/T-166/BRIEF.md` + `STATUS.md`）

1. **改动文件**
2. **原始输出**（382×16 覆盖、正分年分布、no_spouse/muku flag 计数）
3. **未完成与风险**（哪些年份边缺失、墓库口径）
4. **下游须知**（scores schema、protocol 路径、哪些 case 正分年<3）

## 7. 禁止

- 不许读结果标签；不许算命中率；不许为了让分数好看调权重。
- 不许改 `engine/**`；缺口只记录，不补。
