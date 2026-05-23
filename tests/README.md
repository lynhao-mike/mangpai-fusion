# tests · mangpai-fusion v1.2 测试架构

> Track-H 维护。建立时间：W2（2026-05-23）。

本目录是 v1.2 的**统一测试基础设施**。把 Track-A/E/G 已实现的 smoke
统合，叠加 Track-H 的 14 案 fixture + 6 项发布门槛断言（决策 I）。

---

## 一、目录结构

```
tests/
├── README.md                         ← 本文件
├── conftest.py                       ← pytest 全局配置 + 共用 fixture
├── __init__.py
│
├── fixtures/                         ← Track-H 提供的夹具
│   ├── __init__.py
│   ├── cases.py                      ← 14 案 fixture 加载器（含短形式自动补全）
│   ├── feedback_ground_truth.yaml    ← 3 真实失验案例 ground truth
│   └── v1_0_baseline.yaml            ← v1.0 实绩基线（v1.2 必须超过）
│
├── regression/                       ← Track-H 整合的回归测试（pytest 友好）
│   ├── __init__.py
│   ├── test_a_energy.py              ← 整合 Track-A A-001~A-005
│   ├── test_e_guardrails.py          ← 整合 Track-E E-001~E-008
│   ├── test_g_iteration.py           ← 整合 Track-G G-001
│   └── test_v1_2_vs_v1_0.py          ← v1.2 严格优于 v1.0 的 6 项断言
│
├── regression_baseline.yaml          ← 6 项量化指标定义（决策 I）
│
├── track_a_smoke/                    ← Track-A 原版 smoke（**只读**，不修改）
│   ├── __init__.py
│   ├── _fixtures.py
│   └── test_a_layer_count.py
│
├── track_e_smoke/                    ← Track-E 原版 smoke（**只读**，不修改）
│   ├── __init__.py
│   └── test_e_negatives.py           ← 用 stdlib + main() 自跑；pytest 不收集
│
└── track_g_smoke/                    ← Track-G 原版 smoke（**只读**，不修改）
    ├── __init__.py
    └── test_g_replay.py              ← 已是 unittest.TestCase，pytest 直接收集
```

---

## 二、运行

### 2.1 一键全量回归

```bash
pip install -r requirements-dev.txt
pytest tests/
```

### 2.2 仅跑整合回归

```bash
pytest tests/regression/ -v
```

### 2.3 仅跑 v1.2 发布门槛断言

```bash
pytest tests/regression/test_v1_2_vs_v1_0.py -v -m v1_2_gate
```

### 2.4 按 marker 过滤

```bash
# 仅跑各 track smoke
pytest -m smoke

# 跳过等待 B/C/D 引擎的测试
pytest tests/ -m "not (needs_engine_b or needs_engine_c or needs_engine_d)"
```

### 2.5 直接运行 Track-E 自跑（pytest 之外）

Track-E 用纯 stdlib 写，pytest 收集会卡住。可单独跑：

```bash
python tests/track_e_smoke/test_e_negatives.py
```

而 pytest 体系下走 `tests/regression/test_e_guardrails.py` 的封装。

---

## 三、Fixture 用法速查

```python
from tests.fixtures.cases import (
    load_case,            # 加载 case → ParsedInput
    list_real_cases,      # 10 个完整 case_id
    list_validated_cases, # 3 个有 feedback.md 的真实失验案例
    parse_case_metadata,  # 出生年/性别/起运岁
    has_feedback,         # 是否有 feedback.md
)

# 完整形式
parsed = load_case("C-2026-001-庚申戊寅壬子辛丑")

# 短形式（自动补全）
parsed = load_case("C-2026-001")

# 参数化
@pytest.mark.parametrize(
    "case_input",
    ["C-2026-001", "C-2026-002", "C-2026-014"],
    indirect=True,
)
def test_xxx(case_input):  # case_input 是 fixture 注入的 ParsedInput
    assert case_input.bazi.day_master in "甲乙丙丁戊己庚辛壬癸"
```

`conftest.py` 提供的全局 fixture：

| Fixture | 类型 | 说明 |
|---|---|---|
| `repo_root` | `Path` | 仓库根目录 |
| `fixtures_dir` | `Path` | `tests/fixtures/` |
| `all_real_case_ids` | `list[str]` | 10 个完整 case_id |
| `validated_case_ids` | `list[str]` | 3 个真实失验案例 |
| `case_input` | `ParsedInput` | 单案 fixture（支持 indirect 参数化）|
| `feedback_truth` | `dict` | `feedback_ground_truth.yaml` 解析 |
| `v1_0_baseline` | `dict` | `v1_0_baseline.yaml` 解析 |
| `regression_baseline` | `dict` | `regression_baseline.yaml` 解析 |

---

## 四、v1.2 发布门槛（决策 I 6 项）

`tests/regression_baseline.yaml` 定义了 6 项必须严格优于 v1.0 的指标：

| ID | 指标 | v1.0 | v1.2 必须 | 阻塞 |
|---|---|---|---|---|
| G1 | 三案核心断语命中率 | 5 | ≥ v1.0 + 1 | B + C |
| G2 | C-001 婚期误差 | 8 年 | ≤ 3 年 | B + C |
| G3 | C-002 婚姻定性失验数 | 4 | ≤ 1 | B + C |
| G4 | C-014 学历过判档数 | 1 | = 0 | B + D |
| G5 | trace_id 覆盖率 | 0% | = 100% | （已可跑） |
| G6 | ★★★★★ 三层 gate 通过率 | 0% | = 100% | （已可跑） |

通过条件：**6 项中 ≥ 5 项达成**。

---

## 五、各阶段预期通过率

| 阶段 | 描述 | PASS | SKIP | XFAIL | 说明 |
|---|---|---|---|---|---|
| **W2 当前** | A/E/G 落地 + Track-H 搭架子 | 41 | 4 (G1-G4) | 2 (A-003 严格) | 现状 |
| **W3 集成日** | B/C/D 落地 | ~50+ | 0-2 | 2 | G1-G4 解锁 |
| **W4 收尾** | F 报告 + integration | ~55+ | 0 | 0-2 | 全绿 |
| **v1.2 发布** | 决策 I 通过 | 全绿 | 0 | 0 | 6/6 门槛达成 |

---

## 六、各 Track 测试清单

### Track-A · 段派 D1 能量引擎（08 § 六）

| 测试 | 输入 | 期望 | 状态 |
|---|---|---|---|
| A-001 | C-2026-001 | layer=2, 中富/大富 | ✅ PASS |
| A-002 | C-2026-002 | layer=1, 中富 | ✅ PASS |
| A-003 严格 | C-2026-014 | layer=1 | 🟡 XFAIL（已知，留 TODO）|
| A-003 宽松 | C-2026-014 | layer ∈ [1,4] | ✅ PASS |
| A-004 | C-2026-011 | layer ≥ 2 | ✅ PASS |
| A-005 | C-2026-012 | layer ≥ 2 | ✅ PASS |
| 契约：必填字段 | × 3 案 | 字段非空 + 类型对 | ✅ PASS |
| 契约：JSON round-trip | C-2026-002 | 序列化一致 + hash 稳定 | ✅ PASS |
| 契约：母星非印 | × 5 案 | muxing_qufa ≠ 印 | ✅ PASS |

### Track-E · 兜底护栏（08 § 六）

| 测试 | 输入 | 期望 | 状态 |
|---|---|---|---|
| E-001 | 缺 schema_version | preflight FAIL | ✅ PASS |
| E-002 | 四柱含 "甲丑" | preflight FAIL | ✅ PASS |
| E-003 | ★5 (50%) | linter FAIL | ✅ PASS |
| E-004 | 应期断语无 yingqi_year | linter FAIL | ✅ PASS |
| E-005 | 引用 blacklisted | linter FAIL | ✅ PASS |
| E-006 | ★★★★★ + passed_layers=2 | three_layer FAIL | ✅ PASS |
| E-007 | 含 "未来某年" | linter WARNING | ✅ PASS |
| E-008 | 指纹重复 | preflight FAIL | ✅ PASS |

### Track-G · 自迭代（08 § 六）

| 测试 | 输入 | 期望 | 状态 |
|---|---|---|---|
| G-001-a 幂等 | C-2026-001 dry_run | 两次结果一致 | ✅ PASS |
| G-001-b miss | C-2026-001 | M2-Y-068 verdict=miss | ✅ PASS |
| G-001-c +1 | C-2026-001 | misses 加 1 | ✅ PASS |
| G-001-d 冻结 | calibration.yaml | freeze=False | ✅ PASS |
| G-001 完整回放 | C-2026-001 | 落盘 + 回滚一致 | ✅ PASS |

### v1.2 vs v1.0（决策 I）

| 测试 | 状态 |
|---|---|
| G1 三案核心命中率 | ⏳ SKIP（等 B+C） |
| G2 C-001 婚期误差 | ⏳ SKIP（等 B+C） |
| G3 C-002 婚姻失验数 | ⏳ SKIP（等 B+C） |
| G4 C-014 学历过判 | ⏳ SKIP（等 B+D） |
| G5 trace_id 覆盖 | ✅ PASS |
| G6 三层 gate 通过 | ✅ PASS |
| 门槛规则未篡改 | ✅ PASS |

---

## 七、维护规约（Track-H 自律）

1. **可写区**仅限：`tests/`（含子目录）+ `pyproject.toml`/`pytest.ini` +
   `requirements-dev.txt`（08 § 二 H 列）
2. **只读区**：`engine/contracts/`、`engine/`、`tools/`、`cases/`、
   `reports/`、`predictions/`、`theory/`、`tests/track_X_smoke/`
3. **新增 fixture**：先看 ``cases.py`` 是否已注册；未注册则按 ``_CASE_DATA``
   补充（不要在测试文件里 hardcode 大运排布）
4. **新增 v1_0 数据**：必须从 ``cases/cases-index.md`` 或 ``feedback.md``
   引用（不要臆造）
5. **新增 G* 门槛**：必须改 ``regression_baseline.yaml`` + 对应测试函数

---

## 八、已知 TODO（W3+ 解锁）

- [ ] G1 三案核心命中率 — 等 Track-B/C 引擎接入
- [ ] G2 C-001 婚期误差（圣杯测试）— 等 Track-B/C 引擎接入
- [ ] G3 C-002 婚姻失验数 — 等 Track-B/C
- [ ] G4 C-014 学历过判档数 — 等 Track-B/D
- [ ] A-003 严格版 — 启发式 over-counts，等"杀印链吸收"语义判定
- [ ] 14 旧案 input.md → v1.2 strict YAML 迁移；目前用 ``_CASE_DATA``
      硬编码大运表
- [ ] G5/G6 接入真正 ``AnalysisOutput`` mock（W4 集成日 F agent 落地后）

---

## 九、版本

| 版本 | 日期 | 内容 |
|---|---|---|
| 0.1.0 | 2026-05-23 | Track-H 首发：fixture + baseline + 6 项门槛框架（W2）|

---

最后更新：2026-05-23 W2 · Track-H · v1.2.0
