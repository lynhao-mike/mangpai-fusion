# T-141 · 体用 SSOT：修 `_crosses` 排除「双属 × 双属」

- 状态：🔵 Ready for Execution
- 优先级：**P0**
- 创建：2026-10-27（中枢）
- 决策依据：ADR-007 D1

## 1. 背景与原文依据

仓库里有两套体用表，给出不同答案：

- `engine/energy/tiyong.py:139-141`：食伤 → **归体**（硬编码）
- `engine/facts/structure_check.py:94`：食神/伤官 → **双属**

**裁决：以 `engine/facts/structure_check.py` 为唯一事实源**，因为原文支持它：

> 「我们把日主、印星、禄神、比劫当体，财星、官杀星当用，**食神与伤官既可以是体，也可以是用**……如一定区分它们，则**食神更近于体，伤官则接近于用**。」
> —— `sources/duan/MinerU_markdown_35.盲派命理开山之作_2056045397672648704.md:1311-1313`

> 「伤官与食神星为**中性之物**，食神略偏于体，伤官略偏于用，在命中既可被制，也可制它。」
> —— 同书 `:1319`

`energy/tiyong.py` 无条件归体是错的：若食伤恒为体，段派核心的「枭印夺食」「印制食伤」会因两边都是体而被过滤掉。

## 2. 要做的事（只有一处代码改动）

`engine/facts/structure_check.py:381` 现在：

```python
def _crosses(a: TiYong, b: TiYong) -> bool:
    return {a, b} != {"体"} and {a, b} != {"用"}
```

问题：`{"双属","双属"}` 会返回 **True**，即「食伤与食伤之间也算体用相交做功」。这与同文件 `_ti_yong_ends`（`:385-388`）已经写好的 `if a == "双属" and b == "双属": return None` **自相矛盾**。

改为：

```python
def _crosses(a: TiYong, b: TiYong) -> bool:
    return {a, b} not in ({"体"}, {"用"}, {"双属"})
```

**只改这一处。** 不要动 `_TIYONG` 表本身，不要动 `energy/tiyong.py`（那属于 v5 链，另案处理）。

## 3. File Scope

- `engine/facts/structure_check.py`（仅 `_crosses` 函数）
- 对应测试（`tests/facts/` 下）

**禁止**：改 `engine/energy/`、`engine/api/facade.py`（另有任务）、`theory/_ir/`、`sources/`、`pyproject.toml`；git 破坏性操作。

## 4. 验收（中枢亲自跑）

```bash
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m tools.verify_baseline
```

**重点 watch**：`zuogong_probe` 的 `zuogong_charts` 现在是 **477**。这个改动会减少「双属×双属」的候选，**可能让该数字下降**。

- 若下降，**不要改测试、不要调判据去维持 477**。在 BRIEF 里写清楚：下降多少、下降的是哪些候选、下降是否**符合原文**（食伤内部互见不算做功）。
- 中枢会判断「这个下降是修复还是回归」。你只负责如实报告，不许自己找平。

**必须自证**：改前改后各跑一次 481 盘，给出「双属×双属」候选的具体数量变化，并抽 3 例说明原来误判、现在正确。

## 5. 回报格式

改了几行、481 盘上 5 类做功候选各模式的数量变化（改前 vs 改后）、`zuogong_charts` 变化、3 个抽样例证、两条验收命令的数字与退出码。
