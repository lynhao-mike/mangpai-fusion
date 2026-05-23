# 04 · 应期三层门契约 · 04-gate-protocol

> **本文是 Track-C 的"宪法"。所有 Track-C 子模块（gate/threelayer/chufa/menshu/keys）必须遵守此文档。**
> 后续 Track 修改本契约前需 PR 通知。

最后更新：2026-05-23（W2 · Track-C 实施同步交付）
版本：v1.2.0-track-C
适用分支：`main`（v1.2-build 已合并 main，新工作直推 main）
状态：⚠️ **实施同步契约** —— 本文件由 Track-C 在交付实现的同时撰写。
W1.3 阶段并未提前交付 02/03/04/06/07/08 这 6 份契约（仅 00/09 已交付），
Track-C 因此采取"以代码为锚定，文档化既定接口"的方式补齐 04。

---

## 一、设计原则（v1.2 灵魂条款）

```
原局有 + 大运到位 + 流年引爆 = 三层齐备 → 铁口断 ★★★★★
```

任派十八道法门核心心法 §M3-R-003：
- **原局**定层次（命中可能性）
- **大运**定吉凶（窗口启闭）
- **流年**定应期（具体引爆点）

**强约束**：任何 ★★★★★ 应期断语必须 `passed_layers == 3`。
否则星级被强制降级（见 § 八 置信度公式）。

---

## 二、模块结构

```
engine/yingqi/
├── __init__.py          gate_yingqi 唯一对外入口（lazy import）
├── types.py             GateResult / LayerCheck / TriggerEvent / Door
├── keys.py              domain → 关键字映射（primary / secondary / required_dayun）
├── threelayer.py        layer1_check / layer2_check / layer3_check
├── chufa.py             6 触发引擎 + pick_primary_trigger
├── menshu.py            12 道门分类（核心 6 已实现）
└── gate.py              gate_yingqi 主入口（含上游一致性 + 置信度）
```

---

## 三、domain 关键字映射

| domain | primary 十神 | 主位字 | 备注 |
|---|---|---|---|
| 婚姻 | 男:正/偏财，女:正官/七杀 | 日支 | 男无财→食伤；女无官→财/印 |
| 事业 | 正官/七杀/正印/偏印 | — | 食伤 + 财 为 secondary |
| 财运 | 正/偏财，食神/伤官 | — | 官杀（统）为 secondary |
| 健康 | 正/偏印 + 日主 + 日支 + 禄 | 日干 + 日支 | 食神（寿星）为 secondary |
| 学业 | 正/偏印，食神/伤官 | — | 官杀 + 财 为 secondary |
| 六亲 | 按 sub_domain 分流 | 对应宫位 | 父=偏财年柱；母=正印月柱；兄弟=比劫月支；子女=男:官杀 女:食伤 时柱 |
| 其他 | 空 | — | 不强制约束 |

`get_primary_keys / get_secondary_keys / get_required_dayun_chars` 三个函数对外。

---

## 四、6 触发判定（§M3-R-031）

| ID | 触发名 | detect_* 函数 | 强度模式 |
|---|---|---|---|
| T1 | 本字到 | `detect_benzi_dao` | `0.4 + 0.2×匹配数` |
| T2 | 伏吟引动 | `detect_fuyin` | `0.7`（柱级伏吟） |
| T3 | 合冲引动 | `detect_hechong` | `0.5 + 0.15×匹配数` |
| T4 | 墓库开闭 | `detect_muku` | `0.6 + 0.15×匹配数`（仅库内含 key 才触发） |
| T5 | 藏干透出 | `detect_canggan_tou` | `0.55 + 0.15×匹配数` |
| T6 | 倒象成立 | `detect_daoxiang` | `0.95`（凶应铁律） |

`detect_all_triggers(parsed, year, primary_keys, yong_shen_chars) -> list[TriggerEvent]`

### 4.1 倒象（任派核心铁律）

倒象 = 用神受到"又生又克又合冲"矛盾作用。

Track-C 实现按"baseline vs active 增量"判定（避免对原局多重作用强的命过敏）：

| 条件 | 含义 |
|---|---|
| A | 大运/流年新增 ≥ 2 种关系类型 + 生克合三态齐 + 累计 ≥ 4 种 |
| B | 大运/流年新增类型含凶煞（冲/穿/刑/克）+ 累计 ≥ 4 种 |
| C | 大运/流年新增作用次数 ≥ 4 (兜底) |

满足任一条件 → 倒象成立 → `is_xiong=True`。

### 4.2 主触发优先级

`pick_primary_trigger(triggers, domain)` 按以下优先级返回单一主触发：

1. 倒象成立  ← 最高（凶应必报）
2. 墓库开闭
3. 合冲引动
4. 藏干透出
5. 本字到
6. 伏吟引动

同优先级按 strength 倒序。

---

## 五、12 道门分类（§M3 §16）

任派理论列 13 道门（动/格局/天地/十天/十二地/统领/墓库/夹拱/旬空/鸳鸯/寿元/伤残/牢灾）。
Track-C MVP 实现核心 6 个 + "未分类"兜底：

| 道门 | 触发条件 | 实现状态 |
|---|---|---|
| 寿元门 | health domain + 倒象 / 主位被冲 | ✅ |
| 牢灾门 | 食伤官杀两敌 + 倒象 (career/health/其他) | ✅ |
| 鸳鸯门 | 婚姻 domain + 触发涉及妻/夫宫或配偶星 | ✅ |
| 统领门 | 财官同现 + 触发涉及财/官 (career/wealth) | ✅ |
| 墓库门 | 墓库开闭触发 | ✅ |
| 动门 | 主位被引动 / ≥2 触发齐发 (兜底) | ✅ |
| 格局门 | 格局成立 → 由 Track-A energy 评估 | 🟡 留口 |
| 天地门 | 字打通天地之气 | ⏳ 后续 |
| 十天门/十二地门 | 干支专门 | ⏳ 后续 |
| 夹拱门 | 拱禄拱贵 + 大运/流年补足 | ⏳ 后续 |
| 旬空门 | 空亡引动 | ⏳ 后续（Track-D 旁证） |
| 伤残门 | 日干根坏 / 印枭重重 + 食神运 | ⏳ 后续（Track-D 旁证） |

`classify_into_12_doors(parsed, domain, triggers, energy, picture) -> Optional[Door]`

优先级（按任务说明 § 阶段 2）：寿元/牢灾 > 鸳鸯/统领 > 墓库/动门。

---

## 六、上游一致性硬约束

`gate_yingqi` 在 L1/L2/L3 后必须运行两个一致性检查：

### 6.1 check_against_energy

| 输入 | 检查 |
|---|---|
| `EnergyFindings.{domain}_capable=False` AND candidate_event 是"成立性事件"（结婚/升迁/录取等） | 返回 `(False, [reason])` |
| 否则 | `(True, ...)` |

不一致 → `passed_layers = min(passed_layers, 2)`。

### 6.2 check_against_picture（修复 G2 的关键）

| 输入 | 检查 |
|---|---|
| domain="婚姻" AND candidate_event 是结婚类 AND age ∉ best_window AND age ∉ secondary_window | `(False, [reason])` |
| domain="学业" AND is_edu AND age ∉ key_year_window | `(False, [reason])` |
| domain="事业" AND age ∉ rising_windows | `(True, ...)` （事业不强制，仅作次佳标注） |

不一致 → `passed_layers = min(passed_layers, 1)`。

**这是 G2 圣杯（C-2026-001-庚申戊寅壬子辛丑 婚期偏差 8 年）的修复机制**：
即使三层判定都过，picture 给出的婚窗 [23, 28] 之外的年份仍被强制钳到 ≤ 1 层。

---

## 七、GateResult schema（03 § 七）

```python
@dataclass
class GateResult:
    schema_version: str
    year: int
    candidate_event: str
    domain: str

    layer1: Optional[LayerCheck]    # 原局
    layer2: Optional[LayerCheck]    # 大运
    layer3: Optional[LayerCheck]    # 流年
    passed_layers: int              # 0..3

    triggers: list[TriggerEvent]
    primary_trigger: Optional[TriggerEvent]
    door: Optional[Door]

    energy_consistent: bool
    picture_consistent: bool
    consistency_reasons: list[str]

    confidence: float               # 0.0 - 1.0
    star: int                       # 1 - 5
    is_xiong: bool

    upstream_energy_hash: str
    upstream_picture_hash: str
    rule_ids: list[str]
    summary: str
```

序列化：`to_dict()` / `from_dict()` / `hash()`（16 位 MD5 截断）。

---

## 八、置信度公式（W3 应期专用）

`compute_yingqi_confidence(passed_layers, triggers, primary_trigger, is_xiong, energy_consistent, picture_consistent) -> (conf, star)`

```
conf = passed_layers × 0.25
     + primary_trigger.strength × 0.20
     + (energy_consistent ? 0.05 : 0)
     + (picture_consistent ? 0.05 : 0)
     + (is_xiong ? 0.10 : 0)

cap = 0.85 if passed_layers < 3 else 1.00
conf = min(conf, cap)

star (按 confidence.yaml):
  ≥ 0.90 → 5    ≥ 0.80 → 4    ≥ 0.65 → 3
  ≥ 0.50 → 2    < 0.50 → 1

★ 强约束（任意一条触发即降级）:
  passed_layers <  3 → star ≤ 4
  passed_layers <= 1 → star ≤ 3
  passed_layers == 0 → star ≤ 2
```

---

## 九、对外契约（其他 Track 必读）

### 9.1 Track-A 段派 D1 提供
- `EnergyFindings.{marriage,career,wealth,health,education}_capable: bool`
- `EnergyFindings.domain_yong_shen[domain]: list[str]`
- `EnergyFindings.upstream_hash: str`

Track-C 在 L1 时使用 capable 标志降级；用 yong_shen 增强 keys。

### 9.2 Track-B 杨派 D2 提供
- `PictureFindings.marriage_picture.best_window: tuple[int, int]`
- `PictureFindings.marriage_picture.secondary_window: Optional[tuple[int, int]]`
- `PictureFindings.education_picture.key_year_window: Optional[tuple[int, int]]`
- `PictureFindings.career_picture.rising_windows: list[tuple[int, int]]`
- `PictureFindings.upstream_hash: str`

Track-C 用窗口实现 picture_consistent 硬约束。

### 9.3 Track-D 高派 D4 旁证
Track-C 不直接消费 SupportFindings，但 Track-D 可用 GateResult 作为
"是否触发某神煞专项"的输入（如倒象 + 天罗地网 = 婚姻血光）。

### 9.4 Track-F 报告渲染
GateResult 有 `summary` 字段（一行人类可读总结）和完整结构化数据。
Track-F 应优先用 `rule_ids` 输出 trace_id，`summary` 作 fallback。

### 9.5 Track-G 自迭代
GateResult 的 `hash()` 提供稳定 trace_id。
反馈系统应按 `(year, domain, candidate_event, passed_layers)` 建索引，
对失验案例 rerun gate_yingqi 验证是否上下游修改改善了判定。

---

## 十、修改流程

修改本契约 = PR 到 main，title 前缀 `[CONTRACT-04]`。
若改动以下任一字段，必须通知所有运行中的 agent：
- GateResult 的 `passed_layers` 语义
- TRIGGER_TYPES 顺序
- `compute_yingqi_confidence` 公式

---

**04-gate-protocol 契约结束。下一份 02/03/05/06/07/08 由后续 Track 补齐。**
