# T-135 · 「禄」提升为事实层 + `lu` 原子（解锁 M2-Y-017 / M3-R-166）

> ## ⛔ 2026-10-27 中枢裁定：**前提不成立，本任务撤销**
>
> 本卡称「禄表只在 `engine/energy/tiyong.py:43`，事实层没有」。**该判断错误。**
>
> 实测：`engine/facts/chart_facts.py:67` 已定义 `_LU = {"甲":"寅","乙":"卯","丙":"巳","丁":"午","戊":"巳","己":"午","庚":"申","辛":"酉","壬":"亥","癸":"子"}`，`:69` 另有 `_YANG_REN`，`:221-223` 已用于「坐禄 / 坐羊刃」判定；宾主也已实现于 `:125 binzhu_side()` 与 `structure_check.py:395-406 _binzhu()`。
>
> 所以「禄」与「宾主」**早就在事实层**，缺的只是「没透出给 `condition_ir` 的上下文」和「没有对应的原子」——那是 10 行级别的接线工作，不是「提升为事实层」的工程。
>
> 真正需要的是：
> 1. 在 `atoms.py` 增加 `lu_at(ctx, args)`（读 `_LU`，查日干或指定天干的禄支落在哪个地支地址）；
> 2. 按 ADR-007 的 D5，让 `facade.py` 保留 `binzhu` 字段，并在 `atoms.py:517` 的 `binzhu` 原子中读取实现，消除空壳。
>
> 这两项已并入 ADR-007 的 Step 1 执行清单，**不再单独立卡**。
>
> 本卡保留仅作追溯，**不得据本卡修改 `engine/facts/`**。


- 状态：🔵 Ready for Execution
- 优先级：P2（成本低、解锁两条断语，但不阻塞主线）
- 创建：2026-10-27（中枢）
- 由来：T-132（A4 墓库扩十神）前提证伪后，从其真实阻塞点拆出

## 1. 为什么需要这个

`M2-Y-017`（杨派·健康·「人生三宝印食禄，全坏则贫贱多灾」）当前是 `needs_human`，卡住的原因只有一条：**缺「禄」原子**。

它连带卡住 `M3-R-166`：后者 `requires_pair: [M2-Y-017]`，配对命题不裁决，`evaluate_claim` 只会落 `evidence_only`，永远不可能成为 `candidate`。所以那条断语的 `fire=0` 与墓库扫描无关，与「禄」缺失有关。

现状实测（中枢已核）：

- 禄位表已存在，但**在遗留链**：`engine/energy/tiyong.py:43` `_GAN_LU_TABLE` + `:50 get_lu()`，注释标注原文锚点 M1-D-067 / D-150（段派「禄」= 临官位）。
- **断语求值器读不到**：`engine/claims/condition_ir/atoms.py::build_context` 构造的上下文里没有禄字段（已确认无匹配）。
- `engine/facts/chart_facts.py:222/225` 只有「坐禄 / 坐长生」这类柱位标记，不提供「日主之禄在哪个支」。

## 2. 要做的事

1. **搬到事实层**：在 `engine/facts/` 产出「日主之禄位」这一确定性事实，随 `analyze_facts` 返回。禄位表**直接沿用** `engine/energy/tiyong.py:43` 的 `_GAN_LU_TABLE`，不要另造一张表，也不要改它的取值。
2. **加原子**：在 `engine/claims/condition_ir/atoms.py` 新增 `lu` 原子，语义为「日主之禄是否成立 / 禄是否在原局」，参数与 `SIGNATURES` 一并登记。
   - **注意**：`atoms.py:684` 有 `assert len(ATOMS) == 42`。**不允许为了加原子而直接把这个断言改成 43** —— 那是改断言让测试变绿。正确做法是同步修改契约 `engine/contracts/23-claim-condition-protocol-v1.md` 的原子表，把「42」更新为真实数目并写明新增理由，再改断言，并在提交信息里说明「契约新增原子的依据」。
3. **不要改 `M2-Y-017` 的 compile_state**。你只负责把原子补齐；把 `needs_human` 改成 `compiled` 是中枢的判断，需要重新核对 `unmapped_prose` 里「三宝是否被坏也需逐一判定」是否还有分支没建模。**你改了就是替中枢拍板，禁止。**

## 3. File Scope

- `engine/facts/`（新增禄位事实；由你定位具体落点并写进 STATUS.md）
- `engine/claims/condition_ir/atoms.py`（新增 `lu` 原子 + SIGNATURES + ATOMS）
- `engine/contracts/23-claim-condition-protocol-v1.md`（原子表数目与说明）
- 对应测试（`tests/facts/`、`tests/claims/` 就近）

**禁止**：改 `theory/_ir/`、`sources/`、`theory/claims/**`、`pyproject.toml`；git 破坏性操作。

## 4. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m pytest -q                 # 0 failed，passed 不少于 220
.venv\Scripts\python.exe -m tools.verify_baseline     # 四项不降
```

外加两条必须自证：

1. 对至少 3 个日主不同的盘，`lu` 原子的取值与 `engine.energy.tiyong.get_lu()` 一致（写命令与输出）。
2. 新增原子后，`M2-Y-017` 的 `preconditions` 若用人手构造的条件求值，能在至少 1 张真实盘上给出 True，并给出是哪张盘、哪个地址绑定。

## 5. 回报格式

禄位事实落在哪个模块/字段、`lu` 原子的签名与语义、契约原子表从 42 改成几、`assert` 是否为配合契约而改（并说明依据）、以及验收两条命令的实际数字与退出码。
