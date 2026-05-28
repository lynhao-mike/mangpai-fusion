# Findings Schema 契约 · 03-findings-schema

> **本文规定 D1/D2/D3/D4 引擎之间的数据交换格式。**
> 4 个 Findings 是 v1.2 的"血液"——所有引擎只产/消费这些结构。

最后更新：2026-05-23（W1.2）
版本：v1.2.0
依赖：流水线设计（`00-OVERVIEW § 二`）

---

## 一、设计原则

1. **JSON Schema 表达**：用 Python `dataclass` + `pydantic` 模型实现，可序列化为 JSON
2. **强类型**：所有字段含类型；Optional 必显式
3. **向后兼容**：新版增字段必须给 default，不删字段（用 deprecated 标记）
4. **可追溯**：每条 finding 必含 `source_rules: list[RuleId]`（trace_id 链）
5. **引擎只读上游**：D2 只读 D1 输出，不写；D3 只读 D1+D2，不写

---

## 二、4 个 Findings 的关系图

```
ParsedInput          ← preflight 解析后的内部结构
    │
    ▼
┌──────────────┐
│ EnergyFindings│  ← D1 段派输出（能量级别）
│  (level)     │
└─────┬────────┘
      │
      ▼
┌──────────────┐
│PictureFindings│  ← D2 杨派输出（细节画面），必引用 EnergyFindings
│  (details)   │
└─────┬────────┘
      │
      ▼
┌──────────────┐
│ GateResults  │  ← D3 任派输出（应期），必引用 D1+D2
│  (timing)    │
└─────┬────────┘
      │
      ▼
┌──────────────┐
│SupportFindings│ ← D4 高派输出（旁证），横向补强
│  (auxiliary) │
└─────┬────────┘
      │
      ▼
AnalysisOutput     ← 整体输出，由 render_report 消费
```


---

## 三、共用基础类型

```python
from dataclasses import dataclass, field
from typing import Literal, Optional
from datetime import date

# 双轨置信度
@dataclass
class Confidence:
    star: Literal[1,2,3,4,5]            # ★ 1-5 星
    percent: float                       # 0.0-1.0 百分比
    posterior: float                     # Beta 后验值
    variance: float                      # Beta 方差（用于 -1★ 触发）
    sample_n: int                        # 该规律累计样本数

# 规律来源
RuleId = str  # e.g. "M1-D-142", "M2-Y-035", "MR-001", "XF-001"
School = Literal["段","杨","高","任"]

@dataclass
class Evidence:
    rule_id: RuleId
    school: School
    description: str                     # 一句话简述该规律的判断
    weight: float                        # 该规律对结论的贡献权重 0-1

# 5 级序数 + 浮点（决策 C）
OrdinalLevel = Literal["无","弱","中","强","极强"]

@dataclass
class Magnitude:
    ordinal: OrdinalLevel
    score: float                         # 0.0-1.0 浮点（内部计算）

# 派别立场（用于跨派冲突时显式记录）
@dataclass
class Stance:
    school: School
    position: str                        # 该派的判断
    confidence: Confidence
    rules: list[Evidence]
```


---

## 四、ParsedInput（preflight 输出，引擎统一消费）

```python
from engine.predicates.types import Bazi, Dayun

@dataclass
class KnownFact:
    type: Literal["婚姻","学历","职业","财运","六亲","健康","子女","灾厄","牢狱","出国","其他"]
    year: Optional[int] = None
    event: Optional[str] = None          # 时间型用
    content: Optional[str] = None        # 状态型用

@dataclass
class ParsedInput:
    schema_version: str                  # "1.2.0"
    case_id: str                         # "C-2026-001-庚申戊寅壬子辛丑"
    case_meta: dict
    birth: dict                          # {性别, 公历, 农历, 出生地, 真太阳时校正}
    bazi: Bazi
    dayun: Dayun
    shensha: dict[str, list[str]]        # {年柱: ["驿马"], 月柱: [...], ...}
    twelve_changsheng: dict[str, str]    # {日干: "壬", 年支: "长生", ...}
    known_facts: list[KnownFact]
    questions: list[str]
    fingerprint: str                     # MD5[:12]
    preflight_warnings: list[str]
```

---

## 五、EnergyFindings（D1 段派 · 能量级别）

```python
ZuogongType = Literal["制","化","生泄","合","墓","复合"]
TiyongRole = Literal["体","用","印","比劫","食伤","财","官杀"]

@dataclass
class ZuogongPath:
    """单条做功路径（如：用神→化神→印星）"""
    type: ZuogongType
    chain: list[Gan|Zhi]                 # 涉及的字
    description: str                     # 一句话描述
    strength: Magnitude                  # 这条路径的能量级别
    layer_count: int                     # 层数 1-4

@dataclass
class TiyongStructure:
    body: list[tuple[Gan|Zhi, TiyongRole]]   # 体（工具）
    purpose: list[tuple[Gan|Zhi, TiyongRole]]# 用（目的）
    rationale: str                       # 段派 M1 体用判别理由

@dataclass
class ShiDang:
    """势 + 党"""
    shi: dict[Wuxing, float]             # 5 行势力比例
    dang: list[tuple[Wuxing, str]]       # 党的形态（12 种之一）
    description: str

@dataclass
class ZeishenBushen:
    """贼神 + 捕神"""
    zei_shen: list[Gan|Zhi]              # 贼神
    bu_shen: list[Gan|Zhi]               # 捕神
    triggered_by_dayun: list[int]        # 哪些大运步会引爆
```


```python
@dataclass
class EnergyFindings:
    """D1 段派输出 · 能量级别"""

    # 主结论
    energy_level: Magnitude              # 整体能量级别（5 级）
    layer_count: int                     # 做功总层数 1-4（段派核心）

    # 分项
    zuogong_paths: list[ZuogongPath]     # 所有做功路径
    tiyong: TiyongStructure              # 体用结构
    shidang: ShiDang                     # 势 + 党
    zeishen: ZeishenBushen               # 贼神捕神

    # 富贵层级（与 layer_count 关联）
    wealth_ceiling: Literal[
        "巨富级·上","巨富级·中","巨富级·下",
        "大富级·上","大富级·中","大富级·下",
        "中富级·上","中富级·中","中富级·下",
        "小富级·上","小富级·中","小富级·下",
        "贫困级·上","贫困级·中","贫困级·下"]

    # 段派独门
    has_guoheqiaoqiao: bool              # 过河拆桥结构
    muxing_qufa: Literal["禄","食伤","比劫","印"]  # 母星取法

    # 元信息
    confidence: Confidence
    evidence: list[Evidence]             # 支撑规律列表
    school: School = "段"
    schema_version: str = "1.2.0"
```

**EnergyFindings 的下游约束**：D2/D3 输出不允许违背 `wealth_ceiling`。例如 D2 不能输出"中富级"画面而 D1 给的是"小富级"。

---

## 六、PictureFindings（D2 杨派 · 细节画面）

```python
@dataclass
class WubuStep:
    """五步算命法的每步结果"""
    step: int                            # 1-5
    name: str                            # "家里找财官" 等
    finding: str                         # 该步的判断结果
    evidence: list[Evidence]

@dataclass
class WuheRelation:
    """天干五合"""
    pair: tuple[Gan, Gan]
    化神: Wuxing
    state: Literal["化成","合绊","搅局"]
    palaces: tuple[PalaceName, PalaceName]
    应事: Optional[str]                  # 杨派"应事表"映射
```


```python
@dataclass
class AnyinResult:
    """十神暗引（5 公式之一）"""
    formula: Literal["1旺不受伤","2受制为用","3得令通根","4印护身","5官印相生"]
    triggered_shishen: Shishen           # 暗引出来的十神
    real_meaning: str                    # 真实背景含义

@dataclass
class CaifuRanking:
    """财富 7 等排序结果"""
    rank: Literal[1,2,3,4,5,6,7]         # 1=官杀库 / 2=食伤库 / ... / 7=纯财
    type: Literal["官杀库","食伤库","旺杀","财库","旺官","食伤当财","纯财"]
    rationale: str

@dataclass
class GuanmingQufa:
    """官命 9 种取法"""
    rank: Literal[1,2,3,4,5,6,7,8,9]     # 1=化杀生枭最大 / ... / 9=制印得权最小
    type: str
    rationale: str

@dataclass
class PictureFindings:
    """D2 杨派输出 · 细节画面"""

    # 五步法结果（必须 5 步全跑）
    wubu_steps: list[WubuStep]

    # 五合
    wuhe_relations: list[WuheRelation]

    # 暗引
    anyin_results: list[AnyinResult]

    # 财富 / 官命
    caifu: Optional[CaifuRanking]
    guanming: Optional[GuanmingQufa]

    # 活死五行（行业定位）
    huosi_wuxing: dict[Wuxing, Literal["活","死","活木","死木","活金","寒金","活水","死水"]]
    industry_pointers: list[str]         # 推荐的行业方向

    # 婚姻画像（杨派强项）
    marriage_picture: Optional[dict] = None  # {初婚年龄, 配偶画像, 婚姻稳定度...}

    # 调候改运（6 维：颜色/方位/数字/文化/食物/贵人）
    tiaohou_advice: Optional[dict] = None

    # 上游约束验证
    energy_consistent: bool              # 是否与 D1 EnergyFindings 一致
    energy_violations: list[str]         # 若不一致，列出违背项

    # 元信息
    confidence: Confidence
    evidence: list[Evidence]
    school: School = "杨"
    schema_version: str = "1.2.0"
    upstream_hash: str                   # EnergyFindings 的 hash，确保版本一致
```

**PictureFindings 的下游约束**：D3 应期判定时，必须以 `marriage_picture.初婚年龄` 等为先验约束。


---

## 七、GateResult（D3 任派 · 应期三层门）

> 这是 v1.2 最关键的结构。**应期判定的硬约束在这里实现。**

```python
TriggerType = Literal[
    "本字到",      # 流年地支 = 原局某关键字
    "伏吟",        # 流年与原局某柱完全相同
    "合冲引动",    # 流年与原局合冲（六合/三合/六冲）
    "墓库开闭",    # 辰戌丑未的开闭
    "藏干透出",    # 流年透出原局某藏干
    "倒象成立"     # 又制又生又合又冲（任派"倒象=必凶"）
]

GateLayer = Literal["L1_原局有","L2_大运到位","L3_流年引爆"]

@dataclass
class LayerCheck:
    layer: GateLayer
    passed: bool
    evidence_chars: list[str] = field(default_factory=list)
    rationale: str = ""
    used_transition: bool = False        # L2 是否仅靠过渡期相邻大运通过
    used_secondary_keys: bool = False    # L1 是否退到 secondary 关键字通过

@dataclass
class TriggerEvent:
    type: TriggerType
    description: str
    target_chars: list[str] = field(default_factory=list)
    is_xiong: bool = False

@dataclass
class GateResult:
    """单个候选事件的应期判定"""

    year: int
    candidate_event: str                 # "结婚" / "升迁" / "母亡" 等
    domain: Literal["婚姻","事业","财运","健康","学业","六亲","其他"]

    # 三层 gate 检查结果
    layer1: LayerCheck                   # L1 原局有
    layer2: LayerCheck                   # L2 大运到位
    layer3: LayerCheck                   # L3 流年引爆
    passed_layers: int                   # 0-3，全过=3

    # 6 触发引擎结果
    triggers: list[TriggerEvent] = field(default_factory=list)
    primary_trigger: Optional[TriggerEvent] = None

    # 12 道门归属（任派 §16）
    door: Optional[Literal[
        "动门","格局门","天地门","统领门","墓库门","夹拱门",
        "旬空门","鸳鸯门","寿元门","伤残门","牢灾门"]] = None

    # v1.4 V4：一个应期触发可保留多个事件类型候选，避免体制内财源/升迁等单解误伤
    event_type_hypotheses: list[str] = field(default_factory=list)

    # 最终置信度（已应用三层惩罚）
    confidence: Optional[Confidence] = None

    # 上游约束
    energy_consistent: bool = True
    picture_consistent: bool = True       # 不违背 D2 marriage_picture 等
    consistency_notes: list[str] = field(default_factory=list)

    # 元信息
    evidence: list[Evidence] = field(default_factory=list)
    school: str = "任"
    schema_version: str = "1.2.0"
    case_id: str = ""
    upstream_energy_hash: str = ""
    upstream_picture_hash: str = ""
    debug_info: dict[str, Any] = field(default_factory=dict)
```

**三层惩罚规则**（v1.2 硬约束）：
```
passed_layers == 3 → confidence.star 可达 ★★★★★
passed_layers == 2 → confidence.star 最多 ★★★★
passed_layers == 1 → confidence.star 最多 ★★★
passed_layers == 0 → 不输出此候选事件
```


---

## 八、SupportFindings（D4 高派 · 旁证补强）

```python
@dataclass
class ShenshaSupport:
    """单个神煞的旁证"""
    name: str                            # 神煞名（如"金舆"）
    palaces: list[PalaceName] = field(default_factory=list)  # 挂在哪
    contribution: str = ""               # 对哪条结论补强
    boost: float = 0.0                   # 对置信度的提升 0.0-0.2
    tags: list[str] = field(default_factory=list)

@dataclass
class HealthFinding:
    """健康专项（高派强项）"""
    organ: str                           # 器官/系统
    risk_level: Magnitude
    risk_years: list[int]                # 高风险年份
    rationale: str
    evidence: list[Evidence]

@dataclass
class CiguanXuetang:
    """词馆学堂（高派学历专用）"""
    has_ciguan: bool = False
    has_xuetang: bool = False
    has_wenchang: bool = False
    has_taiyi: bool = False
    contribution: str = ""
    boost: float = 0.0

@dataclass
class SupportFindings:
    """D4 高派输出 · 旁证补强"""

    # 神煞旁证（按对哪条上游结论补强分组）
    shensha_supports: dict[str, list[ShenshaSupport]] = field(default_factory=dict)
    # key 形如 "marriage" "career" "wealth" "health" "education" "general"

    # 健康灾厄专项
    health_findings: list[HealthFinding] = field(default_factory=list)

    # 词馆学堂（学历）
    ciguan_xuetang: Optional[CiguanXuetang] = None

    # 命宫长生诀择日（特殊场景）
    mingong_zhairi: Optional[dict] = None

    # 元信息
    confidence: Optional[Confidence] = None
    evidence: list[Evidence] = field(default_factory=list)
    school: str = "高"
    schema_version: str = "1.2.0"
    case_id: str = ""
    upstream_energy_hash: str = ""
    upstream_picture_hash: str = ""
    upstream_gate_hash: str = ""
    debug_info: dict[str, Any] = field(default_factory=dict)
```

**SupportFindings 的特殊性**：D4 的 boost 只能**增强**已有 D1/D2/D3 结论，不能**新提**结论。这是"旁证"二字的本意。

---

## 九、AnalysisOutput（最终整体输出）

```python
@dataclass
class CrossSchoolConflict:
    """跨派冲突显式登记"""
    conflict_id: str                     # "CFL-HUNYIN-001"
    domain: str
    description: str
    stances: list[Stance]                # 各派立场
    arbitration_rule: Optional[RuleId]   # 仲裁依据
    winner: School                       # 仲裁胜方
    output_strategy: Literal["显示主胜方","并列显示","降级输出"]

@dataclass
class FinalConclusion:
    """每条最终断语"""
    conclusion_id: str                   # "CC-001"
    statement: str                       # 断语文字
    domain: str                          # 婚姻/事业/...
    layer: Literal["共识","互补","独门","冲突仲裁"]
    contributing_schools: list[School]
    confidence: Confidence
    evidence: list[Evidence]             # trace_id 链
    yingqi_year: Optional[int]           # 应期年份
    falsifiable: str                     # 证伪条件
```


```python
@dataclass
class AnalysisOutput:
    """完整分析输出（render_report 直接消费）"""

    case_id: str
    analysis_date: date

    # 4 派子结论
    energy: EnergyFindings
    picture: PictureFindings
    gate_results: list[GateResult]
    support: SupportFindings

    # 整合后的最终结论
    final_conclusions: list[FinalConclusion]

    # 跨派冲突
    conflicts: list[CrossSchoolConflict]

    # 应期总表
    yingqi_table: list[dict]             # render_report 用

    # 整体置信度
    overall_confidence: Confidence
    layer_summary: dict[str, int]        # {共识: 7, 互补: 4, 独门: 3, 冲突: 2}

    # 元信息
    schema_version: str = "1.2.0"
    pipeline_version: str = "1.2.0"
    generated_at: str                    # ISO timestamp
```

---

## 十、Hash 校验（防止上下游版本错乱）

每个 Findings 落盘时同时记录其 hash：
```python
def findings_hash(findings) -> str:
    """SHA-256(canonical_json(findings))[:16]"""
```

下游引擎在使用上游 Findings 时**必须**校验 `upstream_hash`：
- D2.upstream_hash != hash(D1.energy) → 引擎拒绝运行
- D3.upstream_energy_hash / upstream_picture_hash 同理

这样保证：D2 改了上游 D1，D3 必须重跑。

---

## 十一、JSON 序列化

所有 Findings 必须可双向 JSON 序列化（用 `pydantic` 或 `dataclasses-json`）：

```python
# 序列化
energy_json = energy.to_json()
energy_findings_dict = energy.to_dict()

# 反序列化
energy_back = EnergyFindings.from_json(energy_json)
```

落盘位置：
```
cases/C-XXX/findings/
├── energy.json
├── picture.json
├── gate_results.json
├── support.json
└── analysis_output.json   ← 整合后，render_report 输入
```


---

## 十二、单元测试要求

每个 Findings 类必须有：
1. **Round-trip 测试**：`from_json(to_json(x)) == x`
2. **空值测试**：所有 Optional 字段为 None 时仍可序列化
3. **下游约束测试**：D2 检测 EnergyFindings 不一致时正确报错
4. **Hash 一致性测试**：同样输入产生同 hash

---

## 十三、版本演进

| 版本 | 变更 |
|---|---|
| 1.2.0 | 初版 4 个 Findings + AnalysisOutput |

修改 Findings schema 必须：
1. PR 标记 `[FINDINGS]`
2. 写迁移函数 `migrate_v1_X_to_vY_Z()`
3. 影响的 agent（A/B/C/D/F）全部 review
4. 整合 agent 批准

---

## 附录：D1→D2→D3 数据流示例

```python
# Step 1: preflight 解析
parsed: ParsedInput = preflight.parse("cases/C-2026-001-庚申戊寅壬子辛丑/input.md")

# Step 2: D1 段派
energy: EnergyFindings = energy_evaluator.evaluate(parsed.bazi, parsed.dayun)
# energy.layer_count = 2
# energy.wealth_ceiling = "中富级·上"
# energy.confidence = Confidence(★4, 82%, ...)

# Step 3: D2 杨派（消费 D1）
picture: PictureFindings = picture_matcher.match(energy, parsed)
# picture.upstream_hash = findings_hash(energy)
# picture.energy_consistent = True
# 内部 5 步法全跑，一致性校验通过

# Step 4: D3 任派（消费 D1+D2）
gate_results: list[GateResult] = []
for year in range(2026, 2050):
    result = yingqi_gate.gate(year, candidate_event, energy, picture, parsed)
    if result.passed_layers >= 1:  # 至少 1 层通过才输出
        gate_results.append(result)

# Step 5: D4 高派（横向旁证）
support: SupportFindings = support_with_shensha(parsed, energy, picture, gate_results)

# Step 6: 整合
output: AnalysisOutput = integrate(energy, picture, gate_results, support, parsed)

# Step 7: 渲染（新案默认 master/client 双版；v1.2 模板仅保留向下兼容）
master_md, client_md = render_report.render_both(output)
```

---

**契约结束。W1.2 三份契约（01/02/03）全部交付。**
**W1.3 待写：04 应期门接口 + 05 规律生命周期 + 06 置信度模型。**
