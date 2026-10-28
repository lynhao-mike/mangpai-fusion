# T-149 · 修三处缺陷：`can_control` 克关系门、力量相当语义、基线刷新

- 状态：🔵 Ready for Execution
- 优先级：**P0（阻塞一切后续判断）**
- 创建：2026-10-28（中枢）
- 依据：`docs/reviews/verdict-chatgpt6.md` + 中枢逐条复现（`docs/handoff-hub-v1.md` §10）

## 1. 三处缺陷（都已实测证实）

### 缺陷一：`can_control` 是「关系盲」的（最严重）

**实测**：盘 `丁卯 癸卯 丁卯 癸卯`（日主丁火），调用 `can_control({"actor":"Y.b","target":"Y.s"})`：

```
返回 True，note 写「制得住（MinerU_22…）」
```

但 `Y.b` 是**卯（木）**，`Y.s` 是**丁（火）**——**木生火，木不克火**。

它只比较了双方「旺项/衰项」计数，**从未检查五行相克关系**。

规模（36 期铁口箓盘，1578 个异五行有序对）：真 169 / 假 169 / **未知 1240（78.6%）**；169 个「真」里 **135 个（79.9%）是非克对**。

### 缺陷二：「力量相当」返回未知，违背原文

原文（`sources/duan/MinerU_markdown_22.盲派初级命理学_2056045493286002688.md:1812`）：
> 「戌辰力量相当，**互相制不了**。」

「制不了」是**确定的否定结论**，不是「不知道」。现行实现返回 `None`（未知），把原文唯一给出的裁决点丢掉了。

### 缺陷三：`META/baseline-v1.json` 已过期

文件里存的是 `pytest_passed: 220`、`zuogong_day_branch: 350`；实际是 **1040 / 346**。

于是 `verify_baseline --compare` 一直在和一个月前的基线比——**「重构前后用同一把尺子」这条红线实际没守住**。

## 2. 要做的事

### 2.1 给 `can_control` 加「克关系门」

在进入旺衰比较之前，先判五行关系：

- 定义克序（**必须用项目已有的五行表，不要另造**）：木克土、土克水、水克火、火克金、金克木。
- **actor 不克 target → 直接返回 `False`**，note 写「不构成制：{actor五行}不克{target五行}」。
  - 这属于「确定的否定」，不是未知。
- 同五行 → 仍返回未知（「同五行不构成对抗」），保持不变。
- 只有「确实克」时才进入原来的旺衰比较。

**要求**：克序表如有现成实现就复用；没有就新建一个常量，并在注释里写明依据（五行相克为命理常识，非本文推断）。

### 2.2 「力量相当」改为 `False`

- 双方旺衰接近（现判 unknown 的那一档）→ 返回 **`False`**，note 写「力量相当，制不了（原文：互相制不了）」。
- **未知只保留三种情况**：地址解析失败、事实缺失、同五行不构成对抗。

### 2.3 刷新基线

```bash
.venv\Scripts\python.exe -m tools.verify_baseline --save
```

写入当前真实数字，并确认文件里的 `pytest_passed`、`zuogong_day_branch` 与实际一致。

## 3. 硬约束

- **不许为让测试变绿而删改断言。** 现有测试若断言「力量相当返回 None」，那是对的旧判据，**要改就说明为什么旧判据错了**（引原文「互相制不了」），并在提交信息里写明。
- 不许改 `theory/_ir/`、`sources/`（红线）。
- 不许改 `theory/claims/**`（本卡只修原子与基线）。
- 不许 git commit / push / checkout / stash / reset。

## 4. File Scope

- `engine/claims/condition_ir/atoms.py`（仅 `can_control` 及其辅助）
- `tests/claims/test_condition_ir_atoms.py`（对应测试）
- `META/baseline-v1.json`（由 `--save` 生成）

## 5. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m tools.verify_baseline
```

**必须自证四条**：

1. **非克对必须返回假**：盘 `丁卯 癸卯 丁卯 癸卯`，`can_control(卯木 → 丁火)` 返回 **False**，note 说明「不构成制」。
2. **真克对仍正确**：标杆盘 A `癸丑 癸亥 辛亥 癸巳`，`can_control(D.b 亥水 → H.b 巳火)` 返回 **True**（水克火，且水得令、多）。
3. **力量相当返回假**：标杆盘 B `壬子 乙巳 庚子 壬午`，`can_control(D.b 子水 → M.b 巳火)` 返回 **False**，note 含「力量相当」。
4. 基线文件里的 `pytest_passed` 与实际 `pytest -q` 输出一致。

**外加**：重新统计 36 期铁口箓盘上 `can_control` 的三值分布，报告改前（真 169 / 假 169 / 未知 1240）改后各多少。

## 6. 回报格式

报四组数：非克对返回假的验证、标杆盘 A/B 的改后结果、三值分布改前改后对比、基线文件新旧数字对比。

加一句结论：**改后 `can_control` 是否忠实于「只有克才构成制」这条？**
