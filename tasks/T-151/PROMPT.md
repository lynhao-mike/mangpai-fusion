# T-151 · M2-Y-395 窄口重建与指纹核对（尺子校准，不证新结论）

- 状态：🔵 Ready for Execution
- 优先级：**P0（与 T-150 并行）**
- 创建：2026-10-28（中枢）
- 依据：`docs/reviews/verdict-chatgpt6.md` §4.2、§5；`docs/reviews/direction-decisions-v1.md` §3.1④
- 前置：无。本卡**不依赖** T-150；只产出题单与计数，正式评分由中枢用 T-150 的尺子跑。

## 0. 一句话

从题库**确定性重建**「夫妻宫被冲，谁制谁」那 78 道题，核对 34 / 25 / 19 三个分支数与各分支答案分布。**对不上只报差异，不许改筛选去凑数字。**

## 1. 本卡即预注册（Worker 不得改）

### 1.1 数据源

- `tiekoulu_1507_to_1428.json`（仓库根目录，284 期，2392 题）。
- 题：题干含「日主婚姻状况」的单选题，共 **283 道**（每期 1 道）。
- 答案字段是 `correct_answer`，选项字段是 `options`（A–E）。

### 1.2 触发器

原局存在 `chong` 边，且边成员含日支 `D.b`。只看原局，不看岁运。

### 1.3 方向规则（确定性，无旺衰阈值）

对每个与 `D.b` 相冲的支 `other`，比较**本气五行**：

- `KE_MAP[wx(D.b)] == wx(other)` → `self_controls`（我制对方）
- `KE_MAP[wx(other)] == wx(D.b)` → `other_controls`（对方制我）
- 其余（含同五行，如辰戌、丑未）→ `no_ke`（无克，弃权）

多个冲并存时：因为六冲是一对一，同一 `D.b` 的所有冲边应指向同一支/同一五行；若出现不同方向，记 `ambiguous` 并单独计数（预期 0）。

### 1.4 预测映射（预注册）

- `self_controls` → `["B"]`
- `other_controls` → `["C", "E"]`
- `no_ke` / `ambiguous` → `[]`（弃权，不进分母，但要报数）

### 1.5 预期指纹（必须逐格对上）

| 分支 | n | 答案分布 | 命中 |
|---|---:|---|---:|
| `self_controls` | 34 | A=9, B=19, C=5, D=1 | B：19/34 |
| `other_controls` | 25 | A=8, B=13, C=2, D=1, E=1 | C/E：3/25 |
| `no_ke` | 19 | A=1, B=9, C=6, D=2, E=1 | 弃权 |
| **合计** | **78** |  | **22/59 = 37.3%** |

同一 59 题 scored 集上：最多数字母 B = 32/59 = **54.2%**；Wilson 95% 置信区间 [26.1%, 50.0%]。

### 1.6 如果对不上

先分类，再报告，**不许改 §1.2–§1.4 的规则**：

1. 建盘差异（解析失败、晚子时、农历口径）
2. 冲边定义差异（是否含天干冲、合冲、岁运）
3. 多冲/歧义
4. 题面解析差异（题干匹配到不同题）
5. 其他

只有**证明实现写错**（例如 `KE_MAP` 方向反了、地址取错）才允许修实现，且必须在 BRIEF 逐条写「错在哪、依据是什么」。

## 2. 要做的事

### 2.1 建盘与方向（不读答案）

新建 `tools/m2y395_direction.py`：

- 复用 `tools/tiekoulu_eval.py` 的解析/建盘路径。**只读 import，不许改该文件**；若需要的函数不可 import，把最小逻辑复制到新脚本并注明来源行号。
- 解析失败必须逐期列入 `parse_failures`，按原因分类（格式/缺时刻/农历转换/其他）。
- **本模块不得出现 `correct_answer` 字样，不得读答案**（中枢会 grep 检查）。
- 产出 `META/m2y395-cases-v1.json`：

```json
{"meta": {"protocol_id": "m2y395-v1", "n_periods": 284, "n_parse_failed": 0,
          "ke_map_source": "engine/predicates/types.py", "definition": "见 FORMAT"},
 "cases": [
   {"case_id": "tiekoulu-1507", "period": "第1507期", "pillars": "壬午 壬子 庚午 丙子",
    "day_branch": "午", "chong": [{"edge_id": "e012", "other": "子", "other_wx": "水",
    "direction": "other_controls"}], "direction": "other_controls",
    "prediction_letters": ["C", "E"]}
 ]}
```

`pillars` 允许留空，但 `day_branch`、`chong[].edge_id`、`direction` 必须非空（无法判定时写 `no_ke` 并说明）。

### 2.2 并入答案并计数

新建 `tools/m2y395_score.py`：

- 按 `case_id`（期号）从题库并入 `answer_letter` 与 `options`。
- 产出 `META/m2y395-scored-v1.json`：在 cases 基础上加 `answer_letter`、`correct`、`branch`。
- 打印指纹表：分支 n、A–E 分布、命中数、22/59、B 基线 32/59。
- **不做最终裁决**（「克向即制」死没死由中枢判）。

### 2.3 报告

`META/m2y395-report-v1.md`：数据源、触发器、方向规则、指纹表、差异分类（如有）、3 例人工抽查记录。结论只写「复现 / 未复现」，**不写「制有效/无效」**。

## 3. File Scope

**允许新建**

- `tools/m2y395_direction.py`
- `tools/m2y395_score.py`
- `META/m2y395-cases-v1.json`
- `META/m2y395-scored-v1.json`
- `META/m2y395-report-v1.md`

**只读**

- `tiekoulu_1507_to_1428.json`
- `engine/facts/**`、`engine/predicates/types.py`
- `tools/tiekoulu_eval.py`

**禁止**

- 修改 `tools/tiekoulu_eval.py`、`engine/**`、`theory/**`、`sources/**`、既有测试
- 期号白名单、按答案筛选、按答案调规则
- `git commit / push / checkout / stash / reset / clean`

## 4. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m tools.m2y395_direction   # 退出码 0；两次输出一致
.venv\Scripts\python.exe -m tools.m2y395_score       # 退出码 0；打印 78 / 34 / 25 / 19
.venv\Scripts\python.exe -m pytest -q                # 0 failed，passed >= 1043
```

中枢额外检查：

- 逐格比对 §1.5 指纹表；对不上时，差异分类是否成立。
- `grep correct_answer tools/m2y395_direction.py` → 必须零命中。
- 抽查 3 例：日支、冲边 ID、五行克向手工核对。
- 读脚本：无硬编码期号列表、无按答案筛选的痕迹。

## 5. 回报格式（`tasks/T-151/BRIEF.md` + `STATUS.md`）

1. **改动文件**
2. **原始输出**（两条命令 + 指纹表）
3. **未完成与风险**（差异分类；解析失败逐类计数）
4. **下游须知**（cases 文件字段、哪些期无法判定）

## 6. 发现卡有问题时

写 Blockers，不扩范围。若 §1.5 的预期数字本身来自二手、与数据冲突，**先报冲突**，由中枢裁决，不许自作主张改预注册。

## 7. Amendments（中枢裁决，2026-10-28 22:05）

1. **§1.5 的计数单位补正**：卡面写的「78 道题」实为 **78 条 `(D.b, other)` 冲边**；
   70 期日支有冲，7 期多冲；59 例 scored 只来自 **53 个独立期**。
   预注册的计数单位是冲边（指纹只有按边计数才可能相加为 78），**期级 20/53 只作敏感性对照，不作主口径**。
2. 中枢已独立复算边级与期级两套数字、抽查 3 例、用 T-150 计分器跑正式分；
   结果见 `docs/reviews/m2y395-verdict-v1.md`。**裁决：方向 alone 被否证。**
3. 本条只登记单位与裁决，不改 §1.2–§1.4 的任何规则、不改筛选。
