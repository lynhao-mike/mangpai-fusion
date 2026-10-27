# T-140 · 修通事实出口：facade 保留 tiyong / binzhu / distance / actor

- 状态：🔵 Ready for Execution
- 优先级：**P0（最高，阻塞一切断语求值）**
- 创建：2026-10-27（中枢）
- 决策依据：[`docs/adr/ADR-007-refactor-direction-adjudication.md`](../../docs/adr/ADR-007-refactor-direction-adjudication.md) D5

## 1. 为什么这是第一件事

`engine/claims/condition_ir/atoms.py:495` 的 `zuogong` 原子这样算 target：

```python
ty = tuple(c.get("tiyong") or ())
target = next((m for m, t in zip(members, ty) if t == "用"), members[-1] if members else None)
```

但 `engine/api/facade.py:93` 的 keep 白名单里**没有 `tiyong`**，所以 `c.get("tiyong")` 永远是空元组 → `zip()` 永远为空 → **target 永远回退到 `members[-1]`**。

含义：段派做功断语里「谁制谁」的 target 判定**当前是静默错的**。不修这个，后面所有断语都建在沙子上。

另有第二处：`facade.py:66-68` 的 `_compact()` 会把值为 `None` 的键整个丢弃，所以 `actor` 不是「值为 null」，而是**键不存在**，下游 `cand["actor"]` 会 `KeyError`。

## 2. 要做的事

1. **扩 keep 白名单**：
   ```python
   keep = ("mode", "relation_kind", "edge_id", "members", "ten_gods",
           "tiyong", "actor", "binzhu", "distance")
   ```
2. **让 `actor` 恒保留键**：值为 `None` 时输出 `"actor": null`，不允许被 `_compact()` 删掉。
   - 注意：`_compact()`（`:45-73`）对**整个 payload** 递归执行，第 66-68 行 `if compact in (None, [], {}): continue` 会删掉任何空值键。
   - 你必须自己追一遍调用链（`_compact_zuogong` 的输出之后还会不会再过 `_compact`），选一个**最小且正确**的改法（例如给 `_compact` 加 `keep_null_keys` 参数）。不要用哨兵字符串糊弄。
3. **确认正交性**：`tiyong`（体/用/双属）、`binzhu`（主/宾层级）、`distance`（柱序距离）、`actor`（生克发出方）全部由位置与五行生克决定，**不含吉凶结论**，符合 ADR-001「引擎只发事实」。若你发现其中任何一个含有判断成分，**停下来报告**，不要放出去。

## 3. File Scope

- `engine/api/facade.py`（唯一允许改的实现文件）
- 对应测试（`tests/api/` 下）

**禁止**：改 `engine/facts/` 下任何文件（另有任务在改）；改 `theory/_ir/`、`sources/`；改 `pyproject.toml`；git 破坏性操作。

## 4. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m pytest -q              # 0 failed，passed 不少于 220
.venv\Scripts\python.exe -m tools.verify_baseline  # 四项不降
```

### ⚠️ 4.0 追加约束（2026-10-27 中枢补，因为实测撞了红线）

`tests/api/test_engine_reset_regression.py::test_cli_all_json_under_15kb` 要求 `engine.cli all` 的输出 **< 15000 字节**。这是真实的产品约束：Agent 每次调工具都不该吃掉 15KB 上下文。

实测（盘 `庚申 戊寅 壬子 辛丑`，16 条做功候选）：

| 字段 | 出现 | 约占字节 |
|---|---|---|
| `binzhu` | 16 条 | **3370** |
| `tiyong` | 16 条 | 453 |
| `distance` | 16 条 | 256 |
| `actor` | 16 条 | 268 |
| 合计 payload | — | **20196**（超限） |

**裁决：不发字段不是选项，但 `binzhu` 必须换紧凑表示。**

原因：`binzhu` 由 `(addr, layer)` 唯一决定，同一地址在不同候选里重复了 16 次，每次还带 `sides` + `direction` 四个层级，是纯冗余。而 `engine/facts/chart_facts.py:125 binzhu_side(addr, layer)` 是纯函数，调用方可自行还原。

**要求**：
- `tiyong` / `distance` / `actor` 照常发（体积可接受）。
- `binzhu` 改为**紧凑形式**，二选一：
  - (a) 只发 `binzhu` 的**方向摘要**，如 `"binzhu": {"1": "同在宾位", "2": "正向"}`；或
  - (b) 候选里不发 `binzhu`，改在 payload **顶层**发一张 `binzhu_map`（每个地址一层，全局去重）。
- 选哪种由你判断，**判据是：`binzhu` 原子（`atoms.py:517`）仍能拿到它需要的信息**。若原子只需 `direction`，就只发 `direction`。

**硬要求**：改完后 `pytest -q` 必须 0 failed，`test_cli_all_json_under_15kb` 必须通过。**不许为了过这条测试去删改那个断言**（放宽 15000 是改判据让红变绿）。

若你认为 15KB 这条限制本身不合理（例如事实层确实需要更多字节），**停下报告理由**，由中枢决定是调限额还是调表示法。不要自己动手改限额。

**必须自证的三条**（把命令与原始输出贴进 BRIEF）：

1. 对 `癸丑 癸亥 辛亥 癸巳`（坤）跑 `engine.cli all`，`duan_zuogong.candidates` 里**至少一条**同时含 `tiyong` 与 `actor` 键，且 `actor` 明确是 `null` 或具体地址。
2. 同盘，`zuogong` 原子（`atom: zuogong`）的 target 判定不再恒等于 `members[-1]`：至少构造一个用例，使 target 不等于最后一个成员。
3. `binzhu` / `distance` 出现在候选里。

## 5. 回报格式

改了哪几行、`_compact` 的改法、actor 为 null 时最终 JSON 长什么样（贴真实片段）、target 判定修复前后的对比、两条验收命令的数字与退出码。
