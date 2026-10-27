# T-131 · STATUS

- 状态：✅ Done（只读盘点完成，未修任何代码）
- 优先级：P1
- 执行：子代理，2026-10-27
- 产物：`META/upper-layer-faults-v1.md`（唯一新建文件）

## 结论摘要

| 指标 | 值 |
|---|---|
| 清单条数（故障项） | **19** |
| P0 | **9** |
| P1 | **10** |
| 反证记录（纠正任务卡假设，非故障） | 1（A-07） |
| `except Exception`（engine+tools+tests） | **110**（engine 46 / tools 54 / tests 10） |
| 其中静默吞错 | **20**（SILENT_PASS 7 + SILENT_CONTINUE 5 + RETURN_NONE 8） |
| 「只断言不抛异常」测试 | **20**（NO_VERIFY 14 + ONLY_NOT_NONE 6）；门禁内仅 2 |
| `tiyong` 为 `None` 是否复现 | ❌ 否证（实际是完整 8 字字典） |
| `binzhu` 为 `None` 是否复现 | ❌ 否证（实际是被整键删除，不是 `None`） |
| 冲/刑/穿 `actor` 为 `None` 是否复现 | ✅ 是，且更严重：键不存在（`KeyError` 风险） |

## 最该先修的三条

1. **B-01 · 两套体用表冲突（P0）** —— `engine/energy/tiyong.py:140-141`（食伤→体）vs `engine/facts/structure_check.py:91-94`（食神/伤官→双属）。同一张盘两种答案，且 `_crosses()` 会因此改变做功候选集合本身。ADR-006 的 import 闸门管不到（`engine/energy` 不是 `engine.v5`）。**理由：这是唯一会让 Agent 拿到自相矛盾事实的故障，比缺字段更危险。**
2. **A-01 + A-02/03/04 · 候选字段静默删键（P0，4 条）** —— `facade.py:93-94` 的 keep 白名单删掉 `tiyong`/`binzhu`/`distance`；`facade.py:94` 删掉 `None` 的 `actor`；`structure_check.py:476` 让冲/刑/穿 `actor` 恒 `None`。**理由：段派「谁做谁」「宾主方位」「层距」全部无事实支撑，而 `binzhu.direction` 无法从 `members` 反推。修法必须两处同改，否则「无 actor」仍不可见。**
3. **C-03 · 权重静默回默认值（P0）** —— `weight_repository.py:24,45`。YAML 读失败即静默返回 `{ziping:0.42, tiaohou_ditiansui:0.32, blind:0.26}`。**理由：四派权重直接决定「谁的话更算数」，静默回落意味着裁决配比可能已在无人知情下变成出厂默认，而报告上看不出异常。**

## Blockers

无。本任务只读，无阻塞。

## 并发干扰记录（非本任务失败）

盘点期间其他子代理实时写文件，**未造成任何 pytest 失败**：

- `tools/case_time_basis_audit.py` 于 **2026-10-27 10:01:09** 新建（本任务 09:56 开始时不存在），使 `except Exception` 计数 110 → 111。多出的 1 处为 `tools/case_time_basis_audit.py:378` 的 `except Exception: pass`，属并发新增，**未计入本清单评级**。
- 同期其他改动：`theory/claims/conditions-v2/pilot-20.yaml`(M)、`META/claim-condition-pilot-v1.json`(M)、`META/case-time-basis-v1.json`(新)、`theory/claims/drafts/`(新)、`docs/adr/ADR-006-v5-retirement-strategy.md`(新)、`tasks/T-128/PROMPT.md`(M)、`tasks/T-130/`~`tasks/T-135/`(新)。
- 本报告所有数字**钉在 110 快照**；复现时若看到 111 属正常。
- 本任务未改任何 `.py`，`git status` 可自证。

## 验收

```powershell
.venv\Scripts\python.exe -m pytest -q
# 220 passed, 1 skipped in 11.90s   （改动前 11.63s 同为 220 passed, 1 skipped）

git status --porcelain
# 与本任务相关的新增只有：?? META/upper-layer-faults-v1.md
```

## Execution Log

| 时间 | 动作 | 结果 |
|---|---|---|
| 2026-10-27 09:54 | 读 `PROMPT.md`，跑 `git status` 基线 | 通过 |
| 2026-10-27 09:56 | 扫 `except Exception`（engine/tools/tests） | 110 处，分类完成 |
| 2026-10-27 09:58 | `engine.cli all` 实跑 `庚申 戊寅 壬子 辛丑`，查 `tiyong`/`binzhu`/`actor` | `tiyong` 正常（否证）；`actor` 键缺失（复现） |
| 2026-10-27 10:00 | 换盘 `甲子 辛未 丙寅 戊戌` 复现穿边 `actor` | 复现成功 |
| 2026-10-27 10:01 | 检测到并发新增 `tools/case_time_basis_audit.py` | 记录，钉住 110 快照 |
| 2026-10-27 10:03 | 对比 `engine/energy` 与 `engine/facts` 体用表 | B-01 冲突确认 |
| 2026-10-27 10:06 | AST 扫全 `tests/` 弱断言 | 20 处（剔除 3 处 fixture 误计） |
| 2026-10-27 10:10 | 逐条构造 C 组静默吞错复现 | 6 组全部实跑成功 |
| 2026-10-27 10:14 | 写 `META/upper-layer-faults-v1.md` | 19 条 + 1 反证 |
| 2026-10-27 10:18 | 复验 `pytest -q` 与 `git status` | `220 passed, 1 skipped`，无 `.py` 改动 |
