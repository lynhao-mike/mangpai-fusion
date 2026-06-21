# 11 · Outcome Taxonomy v1 契约

> 目标：为 mangpai-fusion 建立独立、可训练、可量化、可回归校准的 outcome taxonomy。报告模板、反馈采集、五派推理、仲裁输出都只能引用本契约与机器可读定义，不得在展示层自行发明训练标签。

---

## 1. 定位

Outcome taxonomy 是现实结果标签本体，不是命理规则库，也不是报告模板。

它回答的是：

```text
一级领域 → 二级指标 → 三级等级 → 四级描述 → 五级案例映射
```

- 一级领域：可反馈、可回测的现实事项域。
- 二级指标：领域下可拆分、可观察、可标注的结果维度。
- 三级等级：统一使用 `L0`-`L14` 十五级等级轴。
- 四级描述：每一级的可读说明、边界与相邻等级差异。
- 五级案例映射：把真实反馈、现实标签、报告展示值映射回等级轴。

---

## 2. 事实源

| 类型 | 事实源 |
|---|---|
| taxonomy 契约语义 | 本文件 |
| 机器可读 taxonomy | `mapping/outcome-taxonomy-v1.yaml` |
| 案例级 outcome 映射 | `cases/*/findings/v5/outcome-taxonomy.json` |
| 报告展示 | `templates/report-v5.md` 引用 taxonomy 后渲染 |
| 反馈回灌 | `feedback.md` 与反馈工具引用 taxonomy 字段 |

约束：

1. 报告模板不得定义训练标签，只能引用 taxonomy。
2. “985、发财、婚姻好、寿命长”等现实说法只能作为展示描述或案例映射，不是核心训练标签。
3. 五派推理输出不得直接裁决现实标签；必须输出对 taxonomy 指标等级的证据、概率槽与不确定区间。
4. 仲裁器只输出 taxonomy level、置信度、候选范围与证伪条件。
5. 健康领域禁止预测具体死亡年龄，只允许输出风险等级、风险类型、健康管理窗口与长寿倾向。

---

## 3. 一级领域

| Domain | 中文 | 是否概率化 | 反馈要求 |
|---|---|---:|---|
| `education` | 学业 | 是 | 学历层次、学校层次、成绩水平、专业/方向类型 |
| `career` | 事业 | 是 | 职业层级、单位层级、权力层级、成就层级 |
| `wealth` | 财富 | 是 | 年收入、资产等级、财富稳定性 |
| `marriage` | 婚姻 | 是 | 感情状态、婚姻质量、配偶层次、家庭结构 |
| `health` | 健康 | 是 | 体质、疾病风险、心理健康、寿元风险/长寿倾向 |

性格、格局、气势、用忌等结构性判断不进入 outcome taxonomy 主标签；它们只能作为证据或解释变量。

---

## 4. 统一 L0-L14 等级轴

`L0`-`L14` 是相对等级轴，不直接等于某个社会称谓。每个领域和指标必须在机器可读 taxonomy 中给出自己的等级描述与现实映射。

| Level | 通用含义 | 使用边界 |
|---|---|---|
| `L0` | 极低 / 缺失 / 严重受损 | 现实反馈长期缺位或明显低于常模 |
| `L1` | 很低 | 有基础功能但持续受阻 |
| `L2` | 低 | 能维持最低现实承载，发展受限 |
| `L3` | 偏低 | 低于平均，靠外部条件补偿 |
| `L4` | 略低 | 有可用基础，但稳定性或质量不足 |
| `L5` | 普通下沿 | 接近普通水平，仍有明显短板 |
| `L6` | 普通 | 常规现实承载，成败取决于阶段运势与选择 |
| `L7` | 普通上沿 | 略优于平均，可见阶段性优势 |
| `L8` | 良好 | 具备稳定优势或较好兑现能力 |
| `L9` | 较高 | 在同环境中有明显竞争力 |
| `L10` | 高 | 可进入优质平台、较强成就或较高质量区间 |
| `L11` | 很高 | 稳定高阶兑现，具备稀缺性 |
| `L12` | 顶层候选 | 接近头部，但需反馈确认边界 |
| `L13` | 头部 | 明显头部现实结果，具备强反馈支撑 |
| `L14` | 极顶层 | 极少数顶层结果，必须有强反馈与多源证据 |

---

## 5. 二级指标

### 5.1 `education`

必备指标：

- `degree_level`：学历层次；报告展示为“学历层次”。候选枚举包括文盲、小学、初中、中专、普高、高职高专、大专、民办本科、普通本科、一本、省重点、211、985、C9、清北、硕士、博士、海外顶尖。
- `institution_level`：学校层次；与学历层次分开标注。候选枚举包括普通、省重点、国家重点、双一流、211、985、C9、清北、海外前五十、海外前十。
- `academic_performance`：成绩水平；候选枚举包括差、中下、普通、中上、优秀、尖子生、竞赛级。
- `field_type`：专业/方向类型；只作分类，不使用 L0-L14。

辅助指标 `learning_ability`、`exam_ability`、`academic_achievement` 可作为证据来源，但报告主表必须优先展示以上四项。

### 5.2 `career`

必备指标：

- `occupation_level`：职业层级；候选枚举包括无业、普通工人、技术员、技工、职员、基层管理、中层管理、高层管理、小创业者、中型创业者、大型创业者、本地名人、行业领袖、全国级、世界级。
- `organization_level`：单位层级；候选枚举包括小民企、中民企、上市公司、国企、央企、政府、事业单位、头部公司、世界五百强。
- `authority_level`：权力层级；尤其适合官杀体系，候选枚举包括无、组长、部门经理、主任、局级、厅级、省级、部级。
- `achievement_level`：成就层级；用于标注项目、业绩、奖项、作品、行业影响和社会可见度。

辅助指标 `management_level`、`social_influence` 可作为证据来源，但报告主表必须优先展示以上四项。

### 5.3 `wealth`

必备指标：

- `income_level`：年收入；候选枚举包括五万以下、五到十万、十到二十万、二十到五十万、五十到一百万、一百万到三百万、三百万到一千万、一千万到三千万、三千万以上。
- `asset_level`：资产等级；候选枚举包括负资产、零到五十万、五十到二百万、二百万到五百万、五百万到一千万、一千万到五千万、五千万到一亿、一亿到十亿、十亿以上。
- `wealth_stability`：财富性质/稳定性；候选枚举包括不稳定、波动、稳定、稳定增长、爆发式增长、周期性。

辅助指标 `wealth_level`、`wealth_source` 可作为证据来源，但报告主表必须优先展示以上三项。

### 5.4 `marriage`

必备指标：

- `relationship_status`：感情状态；候选枚举包括单身、多段关系、晚婚、早婚、离异、再婚、终身单身。
- `marriage_quality`：婚姻质量；候选枚举包括差、不稳定、普通、和谐、优秀。
- `spouse_quality`：配偶层次；必须拆分展示为配偶教育、配偶事业、配偶财富、配偶外貌、配偶气质。
- `family_structure`：家庭结构；标注子女、居住、重组、异地、同居、分居、双方家庭牵连等现实结构。

配偶外貌候选枚举包括普通、有吸引力、漂亮/英俊、出众；配偶教育、事业、财富应分别映射学业、事业、财富的中文等级体系。

### 5.5 `health`

必备指标：

- `physical_condition`：体质；候选枚举包括弱、普通、强、运动型。
- `major_disease_risk`：疾病风险；候选类型包括心血管、消化、呼吸、内分泌、肝、肾、神经、癌症、意外。
- `mental_health`：心理健康；标注压力、睡眠、情绪、心理韧性和诊疗反馈。
- `longevity_risk`：寿元风险/长寿倾向；只表达低风险、普通、高风险、长寿倾向，不得预测死亡年龄。

辅助指标 `chronic_risk`、`accident_risk` 可作为疾病风险或证据来源，但报告主表必须优先展示以上四项。

---

## 6. 五派概率槽

每个可反馈指标允许五派给出独立概率槽：

```yaml
school_probabilities:
  ziping: 0.00-1.00
  ditiansui: 0.00-1.00
  gao_dechen: 0.00-1.00
  duan_jianye: 0.00-1.00
  yang_qingjuan: 0.00-1.00
```

约束：

- 概率槽表达某流派对该等级或候选等级的支持度，不等于最终概率。
- 五派缺证据时必须允许 `null`，不得硬填。
- 仲裁输出必须保留 `winning_schools`、`dissenting_schools` 或等价结构，但报告展示不得暴露内部 ID。

---

## 7. 仲裁输出

每个领域与指标的最终输出必须包含：

```yaml
domain: education
indicator: degree_level
level: L8
level_range: [L7, L9]
label: 普通本科至较好本科候选
confidence:
  star: ★★★
  percent: 66
uncertainty: 0.22
school_probabilities:
  ziping: 0.68
  ditiansui: 0.62
  gao_dechen: 0.58
  duan_jianye: 0.55
  yang_qingjuan: null
evidence:
  - 食伤透出，学习转化能力不弱
feedback_fields:
  - highest_degree
  - school_level
falsifier: 若反馈为初中及以下且无后续证照，则下修到 L3-L5。
```

---

## 8. 报告展示约束

1. 报告正文必须使用中文可读字段名，不得显示 `degree_level`、`occupation_level` 等机器字段名。
2. 机器字段只允许出现在契约、映射、结构化 findings、statement index 或内部调试文件中。
3. 报告主表必须按学业、事业、财富、婚姻、健康五大领域独立展示二级指标，不得退回单一粗粒度十五层总表。
4. 健康章不得预测具体死亡年龄；“寿元”只能展示为风险等级、健康管理窗口或长寿倾向。

---

## 9. 案例映射

案例级映射文件必须引用 schema：

```json
{
  "schema_version": "outcome-taxonomy-v1",
  "taxonomy_path": "mapping/outcome-taxonomy-v1.yaml",
  "case_id": "C-YYYY-NNN-乾-干支",
  "domains": {}
}
```

每个 domain 至少包含：

- `domain_level`
- `level_range`
- `label`
- `confidence`
- `indicators`
- `school_probabilities`
- `evidence`
- `feedback_fields`
- `falsifier`

---

## 10. 反馈闭环

反馈摄入时必须把现实反馈拆解为：

1. 原始反馈值：用户原话或证据材料。
2. 归一化反馈字段：如 `highest_degree`、`annual_income_band`。
3. taxonomy 映射：映射到 domain / indicator / level。
4. 命中判定：`hit` / `miss` / `partial` / `unknown`。
5. 校准信号：用于流派权重、规则置信度、等级边界和候选范围更新。

禁止把“判断准/不准”作为唯一反馈标签；必须落到具体 domain 与 indicator。

---

## 10. 报告展示规则

报告可以展示：

- 领域等级与候选范围。
- 二级指标等级和现实描述。
- 置信度、应期、证据链。
- 反馈入口与待确认字段。

报告不得展示：

- 训练样本内部编号。
- statement index。
- claim / prediction / evidence 内部 ID。
- taxonomy 的机器字段全集。
- 未经解释的裸概率矩阵。

---

## 11. 迁移原则

旧模板中的现实枚举按以下原则迁移：

- `project_985`、`c9`、`tsinghua_peking` 等改为 `education.institution_level` 的高阶案例映射，不是核心等级。
- `<5w`、`100w_300w` 等收入区间改为 `wealth.income_level` 的案例映射，不是领域总等级。
- `harmonious`、`excellent` 等婚姻描述改为 `marriage.marriage_quality` 的展示标签，并挂载 L 级。
- `longevity_tendency` 改为 `health.longevity_risk` 的低风险 / 长寿倾向描述，不输出寿元年龄。
