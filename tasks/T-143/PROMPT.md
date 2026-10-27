# T-143 · 断语层：修 M1-D-298 编译 + 补 invalidators + 挂 needs_judgment

- 状态：🔵 Ready for Execution
- 优先级：P1
- 创建：2026-10-27（中枢）
- 决策依据：ADR-007 D10 / D11 / D12
- **前置：T-142 已完成**（需要 `needs_judgment` 原子、修好的 `he_at`）

## 1. 背景

中枢拿段派原文标杆盘 `坤造 癸丑 癸亥 辛亥 癸巳` 实跑，结果 `M1-D-298` 返回 `rejected`，**系统对这张盘零输出**。
而段建业原文对此盘的判断是**婚姻好**（「伤官亥冲巳，夫宫为喜，冲去夫星忌神」）。

原因两条：
1. `frame_atom: {atom: tiyong, args: {role: 用, at: D.b}}` —— 把「夫妻宫有用」错误编译成「日支本气必须是财官（用）」。而此盘日支亥是**伤官（双属）**，按段派体用表食伤可体可用，它照样「有用」。
2. `he_at` 定义过宽（由 T-142 修）。

## 2. 要做的事

### ① 修 `M1-D-298` 的 `frame_atom`

「夫妻宫有用」不等于「日支本气是财官」。请**先查原文**（`sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md` 第 48 行起的整段，含紧接着的好婚姻标杆例）确定段派怎么判「夫妻宫有用」，再决定编译形式。

可能的形式：日支参与做功候选（`zuogong` 命中 D.b）、或日支体用为「用/双属」、或其他。**选中哪个必须给原文依据。**

### ② 给 `M1-D-298` 的 `he_at` 传限定参数

按 T-142 修好的语义，只拦六合/暗合他星，不拦半三合、拱局、自合。是否排除配偶星本星相合，查原文后定。

### ③ 补 `invalidators`（成败）—— 这是本卡最重要的部分

现状：`pilot-20.yaml` 20 条断语的 `invalidators` **20/20 全为空**。等于全部只有「象」没有「成败」。

**本卡只要求补 3–5 条高价值断语的 `invalidators`，不要贪多。** 优先 `M1-D-298`、`M1-D-299`、`M2-Y-395`。

每补一条必须：
- 有**原文逐字锚点**（行号 + 引文），不许自己编；
- 写清「什么情况下这条断语**不成立**」（救应、反条件、忌神被制等）；
- 找不到原文依据的，**不要补**，在 BRIEF 里列为 `not_found`。

### ④ 给 partial 断语挂 `needs_judgment`

`pilot-20.yaml` 里 `compile_state: partial` 的 4 条（`M1-D-009`、`M1-D-013`、`M1-D-242`、`M3-R-166`），现在把不会算的条件塞在 `unmapped_prose` 里。

**要求**：把这些未量化条件用 `needs_judgment(reason=...)` 显式挂进 `preconditions.all`，然后**才**把 `compile_state` 从 partial 改为 compiled（如果其余部分确实完整）。

判定标准：挂上 `needs_judgment` 后，该断语在 481 盘上的求值必须出现 `needs_fact` 状态，而不是恒真/恒假。

### ⑤ 修正 `M3-R-166` 的状态

它当前 `partial`，真实阻塞是 `requires_pair: [M2-Y-017]` 而后者 `needs_human`。T-142 补了 `lu_at` 之后，`M2-Y-017` 是否可编译？**你来判断并给依据**，不要擅自改 `M2-Y-017` 的 `compile_state`——那是中枢的判断，写进 BRIEF 供中枢裁决。

## 3. File Scope

- `theory/claims/conditions-v2/pilot-20.yaml`
- 对应测试（若有断言断语内容的）

**禁止**：改 `engine/` 下任何文件；改 `theory/_ir/`、`sources/`（红线：原文只增不改）；改 `pyproject.toml`；git 破坏性操作。

## 4. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m tools.claim_condition_corpus
.venv\Scripts\python.exe -m tools.claim_condition_report
```

**必须自证**：
1. `M1-D-298` 在 481 盘上的命中数从 **6** 升到 **≥30**（这是 ADR-007 的证明点 A）。
2. `坤造 癸丑 癸亥 辛亥 癸巳` 这张盘上，`M1-D-298` 不再是 `rejected`（应为 `candidate` 或 `needs_fact`），并说明是哪一种、为什么。
3. 试点 **未知率** 从 `0.0` 变为正值，`未知显性率` 保持 `1.0`（unknown 必须带原因）。
4. 新补的 `invalidators` 每条都有原文锚点，且锚点行号可在原文里核对到。

## 5. 回报格式

改了哪几条断语、`frame_atom` 的新形式与原文依据、`invalidators` 补了哪几条及各自锚点、`needs_judgment` 挂了哪些、三条验收命令的实际数字（含 M1-D-298 命中数、未知率）、以及你认为需要中枢裁决的项。
