# T-131 · BRIEF（上层故障只读盘点 · A2 前置）

- 执行：子代理，2026-10-27
- 结论文件：`META/upper-layer-faults-v1.md`（19 条故障 + 1 条反证，P0 9 / P1 10）

## 1. 改动文件

| 文件 | 动作 |
|---|---|
| `META/upper-layer-faults-v1.md` | **新建**（唯一产物，35940 字节） |
| `tasks/T-131/BRIEF.md` | 新建（本文件） |
| `tasks/T-131/STATUS.md` | 新建 |

**未改任何 `.py`，未改任何测试，未新增测试。** 未执行 `git commit` / `push` / `checkout` / `stash` / `reset`。

只读基线（改动前后各跑一次，均为）：

```powershell
.venv\Scripts\python.exe -m pytest -q
# 220 passed, 1 skipped in 11.63s   /   220 passed, 1 skipped in 11.90s
```

`git status --porcelain` 中与本任务相关的只有 `?? META/upper-layer-faults-v1.md`（以及 `tasks/T-131/` 本身，任务目录未跟踪）。

## 2. 原始输出

### 2.1 三类 `None` 的实跑复现结论

| 字段 | 任务卡假设 | 实跑结果 | 是否复现成功 |
|---|---|---|---|
| `tiyong` | 序列化成 `None` | **否证**。`duan_zuogong.tiyong` 返回完整 8 字字典 `{"Y.s":"体",...,"H.b":"用"}`；`tiyong_view` 无缺陷 | ❌ 假设不成立（反证 A-07） |
| `binzhu` | 序列化成 `None` | **否证**。`binzhu` 从不出现 `null`，而是被 `facade.py:93-94` 的 keep 白名单**整键删除** | ❌ 假设不成立（真故障记为 A-01） |
| 冲/刑/穿边 `actor` | 为 `None` | **✅ 复现成功**。且比描述更严重：`actor` 键**根本不存在**（`'actor' in c` → `False`），调用方 `cand["actor"]` 会 `KeyError` | ✅ A-02（冲）/ A-03（刑）/ A-04（穿） |

`actor` 复现原始输出：

```
# 冲、刑（庚申 戊寅 壬子 辛丑）
化用 sheng True M.s
制用 ke True M.s
制用 chong False None      ← 键不存在
制用 xing False None       ← 键不存在

# 穿（甲子 辛未 丙寅 戊戌）
制用 chuan False None      ← 键不存在
制用 xing False None
```

### 2.2 `except Exception` 计数

```
engine/: 46 处（26 文件）
tools/ : 54 处（28 文件）
tests/ : 10 处（ 4 文件）
合计   : 110 处
```

按 catch 体分类：`SILENT_PASS` 7 / `SILENT_CONTINUE` 5 / `RETURN_NONE` 8 / `LOGGED` 10 / `RERAISE` 9 / `OTHER` 71。
**静默吞错合计 20 处。**

### 2.3 「只断言不抛异常」的测试

AST 扫描全 `tests/`：`ONLY_NOT_NONE` 6 处 + `NO_VERIFY` 17 处（其中 3 处是 `@pytest.fixture` 误计，剔除后 **14** 处）→ **真值 20 处**。
其中落在 `pyproject.toml` `testpaths` 门禁内的只有 **2 处**（`tests/facts/test_chart_facts.py:212`、`tests/facts/test_strength_facts.py:189`）。

### 2.4 P0 九条（摘）

```
A-01 facade.py:93-94           候选 tiyong/binzhu/distance 被整键删除
A-02 structure_check.py:476    冲边 actor=None 且删键
A-03 structure_check.py:476    刑边 actor=None
A-04 structure_check.py:476    穿边 actor=None
B-01 energy/tiyong.py:140-141  vs facts/structure_check.py:91-94  两套体用表冲突
C-01 全局                      110 处 except Exception，20 处静默
C-02 domain/analysis.py:143..  5 个反序列化器失败即 return None
C-03 weight_repository.py:24,45 权重读失败静默回默认值
D-01 tests/track_e_smoke:170-268 8 用例只 rep.add 不断言 + pytest 下 8 ERROR
```

## 3. 未完成与风险

1. **并发干扰（已确认，非本任务失败）。** 盘点期间其他子代理实时写文件：
   - `tools/case_time_basis_audit.py` 于 **10:01:09** 新建（本任务 09:56 开始时不存在），使 `except Exception` 从 110 变 111（多出的即 `case_time_basis_audit.py:378` 的 `except Exception: pass`）。
   - 同期被改/新增：`theory/claims/conditions-v2/pilot-20.yaml`(M)、`META/claim-condition-pilot-v1.json`(M)、`META/case-time-basis-v1.json`(新)、`theory/claims/drafts/`(新)、`docs/adr/ADR-006-v5-retirement-strategy.md`(新)、`tasks/T-128/PROMPT.md`(M)、`tasks/T-130/`~`tasks/T-135/`(新)。
   - 本报告数字**钉在 110 快照**，复现时看到 111 属正常。
   - **本任务未因此产生任何 pytest 失败**（两次跑均 `220 passed, 1 skipped`），无需标注「疑似并发改动干扰」导致的红。
2. **C-05 未构造出真实失败盘面。** `get_dayun_at_year` 对合法输入不抛，只验证了「`except Exception: pass` 构造存在」。评级保守取 P1。
3. **A-06（破边不产生候选）未定性。** 只证明「`po` 边排盘有、做功候选无」这个事实，未判断是漏实现还是有意排除。**中枢定性前不要直接补 `"po"` 进 `_ZHI_KINDS`。**
4. **B-01 裁决方向未定。** 只证明两套体用表冲突，未判断哪套权威。`energy/tiyong.py` 的 docstring 引用 M1-D-005..008 等条目（有出处），`structure_check.py` 的 `双属` 更像候选层的工程折中。**需理论侧裁决，不要按「哪边改得少」来选。**
5. **未逐条判断被 `addopts --ignore` 排除目录的断言强度。** `tests/f09`、`tests/asof`、`tests/evaluation` 等只按 AST 扫了「有无断言」，没判断「断言够不够」。A2 若要全覆盖，这是下一轮口子。
6. **未统计下游消费方。** 没 grep「哪些断语模板/规则实际读 `cand['actor']`」。若下游全是 `.get('actor')`，A-02 危害是「方向缺失」；若有硬取键，则是运行时 `KeyError`。两种严重度不同。

## 4. 下游须知

1. **别按任务卡原话修 `tiyong`。** `tiyong_view`（`facade.py:165`）是对的，A-07 已否证「序列化成 None」。要改的是 `facade.py:93-94` 的 keep 白名单 + `facade.py:67` 的「删 None」。
2. **A-02/A-03/A-04 必须两处同改。** 只改 `structure_check.py:476` 让冲/刑/穿有 actor 不够——`facade.py:94` 仍会删 `None` 键。建议把 `actor` 从「可删键」改为「恒输出，无方向时输出 `null`」，让 `null` 承载「算了但没有」的语义。
3. **B-01 优先级高于全部 A 组。** A 组是「字段看不见」，B-01 是「字段看见了但两个数不一样」。后者让 Agent 拿到自相矛盾的事实，比缺字段更危险。建议 A2 第一件事是裁决 `engine/energy` 与 `engine/facts` 谁是体用 SSOT。
4. **ADR-006 的闸门不覆盖 B-01。** `tools/v5_boundary_check.py` 只拦 `import engine.v5`；`engine/energy` 是独立包，两边都算「现行侧」。若决定让 `engine/energy` 退役，闸门规则需扩展；若决定它是权威，则 `structure_check.py` 的 `_TIYONG` 要改成调用它。**不要两边都留。**
5. **D-01 修的时候注意：** 那 8 条在 pytest 下是 ERROR（`fixture 'rep' not found`），说明 `tests/track_e_smoke` 从来没进过 `testpaths` 门禁。修法是加 `assert` 或加 `rep` fixture，**不要**只把它们移进 `testpaths`——那等于给门禁加 8 条永绿测试。
6. **本任务验收口径：** `pytest -q` 仍 `220 passed, 1 skipped`；`git status` 中与本任务相关的新增只有 `META/upper-layer-faults-v1.md`。
