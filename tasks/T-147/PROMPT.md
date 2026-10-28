# T-147 · 盲派成败闭环：把 `can_control` 接进断语

- 状态：🔵 Ready for Execution
- 优先级：**P0（最高）**
- 创建：2026-10-28（中枢）
- 决策依据：本卡 §1（格局判断），依据原文 `theory/raw/duan/d01-deep-read.md:106`、`:110`

## 1. 为什么做这个

实测（中枢亲跑，可复现）：

| 项 | 数字 |
|---|---|
| 已编译断语 | 12 条 |
| 用到 `can_control`（能否制住）的 | **0 条** |
| 用到岁运原子（大运流年相关）的 | **0 条** |
| `invalidators`（成败/救应）为空的 | **9 / 12** |

T-145 已经造出 `can_control` 与 4 个岁运原子，**但没有任何一条断语在用**。所以现有断语只表达了「象」（结构存在），没有表达「成败」（这个结构成不成）。

铁口箓评测（T-146）测出「不如瞎猜」，测的正是这台只走了一半的机器。

**原文依据**（`theory/raw/duan/d01-deep-read.md`）：

> 「用是什么？用是我的目的、我的追求……需要注意的是，**这个『用』与传统命理中的用神是有区别的**。」（:106）
> 「**体用之『用』≠ 子平传统『用神』。这是 M1 与 M2/M3 划清界限的核心。**」（:110）

> 「夫妻宫的宫位制去夫妻星的字为好婚姻（夫妻宫为用的情况下……）**制不住为坏婚姻**。」（`sources/duan/MinerU_markdown_21.大连段建业-面授讲义（合集）134页_2056045222002622464.md:4109`）

## 2. 要做的事

改造 **3 条**断语，从「只有象」改成「象 + 成败」两段式：

| 断语 | 类别 | 现在的问题 | 改造方向 |
|---|---|---|---|
| `M1-D-298` | 婚姻 | 冲/刑时靠 `needs_judgment` 推给 Agent | 加 `can_control(D.b, 配偶星所在地址)` 作成败判据：制得住 → 成立；制不住 → 不成立 |
| `G-SP-130` | 婚姻 | `invalidators` 有，但无力量判据 | 加 `can_control` 校验「制得住/制不住」 |
| `M2-Y-251` | 职业 | 只有「食伤旺」这个象 | 加「食伤能否制住官杀」作成败 |

### 具体规则

1. **每一条都必须保留原来的「象」**（`preconditions`），只在 `invalidators` 里加「成败」。
   - 三值语义：`象=True 且 成败=Unknown` → `needs_fact`；`象=True 且 成败=False` → `rejected`；`象=True 且 成败=True` → `candidate`。
2. **`can_control` 的参数必须给「具体地址」**，不许给模糊的角色名。地址格式见 `atoms.py`（原子表）：`Y.s/M.s/D.s/H.s/Y.b/M.b/D.b/H.b`。
3. **每条改造必须有原文锚点**（行号 + 逐字引文）。找不到原文依据的，不要改，在 BRIEF 里写 `not_found`。
4. **不许改断语的 `statement`（陈述）与 `source_ref`（出处）**。只改 `conditions_v2` 里的条件结构。

## 3. 防过拟合硬约束（最重要）

**改造断语时，禁止查看 `tiekoulu_1507_to_1428.json` 的 `correct_answer`（正确答案）字段。**

理由：如果一边看答案一边改断语，分数会假涨，而真实能力没变。这是对测试集过拟合。

具体做法：
- 改造阶段只读 `theory/`、`sources/`、`engine/`。
- 改完、跑完 `pytest`、提交后，**才允许**运行 `python -m tools.tiekoulu_eval` 看分数。
- 如果你在改造过程中需要知道某题答案，说明你在调参而不是在按原文建模，**停下来报告**。

## 4. File Scope

- `theory/claims/conditions-v2/pilot-20.yaml`（仅上述 3 条断语的 `conditions_v2`）
- 对应测试（`tests/claims/`）

**禁止**：
- 改 `tiekoulu_1507_to_1428.json`（答案集）
- 改 `engine/`（引擎与原子，T-145 已完成）
- 改其它 9 条断语
- 改 `theory/_ir/`、`sources/`（红线：原文只增不改）
- 改 `pyproject.toml`
- git commit / push / checkout / stash / reset

## 5. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m pytest -q                    # 0 failed
.venv\Scripts\python.exe -m tools.claim_condition_corpus # 看状态分布
.venv\Scripts\python.exe -m tools.tiekoulu_eval          # 重测
```

**必须自证**：

1. 三条断语改造前后的 `state` 分布对比（`candidate` / `needs_fact` / `rejected` 各多少盘）。**特别报告 `needs_fact` 是否下降**——如果加了 `can_control` 后 unknown 反而上升，说明参数给错了。
2. 三条断语各自的原文锚点（行号 + 引文），逐字可核对。
3. 铁口箓重测结果：三条断语各自的准确率、对基线的增益、p 值、样本 n。
4. `git diff -- tiekoulu_1507_to_1428.json engine/` 必须为空。

## 6. 回报格式

必须报：三条断语改造前后的状态分布对比、`needs_fact` 变化、三条的原文锚点、铁口箓重测的三组数字（准确率/增益/p 值/n）、以及一句直说——**有没有任何一条超过基线**。

如果没有，就写「三条均未超过基线」。不许美化。
