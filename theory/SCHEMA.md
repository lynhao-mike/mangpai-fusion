# 规律统一 Schema · v1.0

本仓库 4 派所有规律统一遵循以下 schema，写入 `theory/{school}/*.yaml`。

---

## 一、字段定义

```yaml
- id: G-LIFA-001                   # 必填 · 全局唯一 ID
                                   # 命名规则：{派别字母}-{主题}-{序号}
                                   # 派别字母：G=高 / D=段 / Y=杨 / R=任
                                   # 主题缩写见下表

  school: gao                      # 必填 · gao | duan | yang | ren

  topic: lifa                      # 必填 · 主题归类，见下表

  title: "假从杀格成立条件"         # 必填 · 简短标题（一行）

  condition: |                     # 必填 · 触发条件文字描述
    日主弱透干，地支无根
    且官杀党旺成势
    印星不透或被合化

  conclusion: |                    # 必填 · 推断结论
    可视为假从杀格
    富贵层次取决于护从神

  evidence_type:                   # 必填 · 证据类型
    - structural                   # 结构性（八字本盘判断）
    - timing                       # 应期类（大运流年触发）
    - imagery                      # 象法类（画面推断）
    - shensha                      # 神煞类
    - tuning                       # 调候改运类

  confidence:
    static: 80                     # 必填 · 0-100，静态分
                                   # 计算来源：派别支持数 + 规律本身确定性
                                   # 详见 engine/confidence.yaml
    star: 4                        # 必填 · 1-5 星
    hit_count: 0                   # 应验次数（实战累计）
    miss_count: 0                  # 失验次数（实战累计）
    hit_rate: null                 # 命中率 = hit / (hit+miss)，<3 例时为 null
    final: 80                      # 综合分 = 静态×0.4 + 动态×0.6（动态需≥3例）

  cross_school:                    # 同向支持的其他派别规律 ID 列表
    - D-GEJU-015                   # 段派类似论断
    - Y-GEJU-008                   # 杨派类似论断

  conflicts:                       # 与本规律冲突的其他规律 ID 列表
    - R-GEJU-022

  layer: complementary             # 该规律所属层级
                                   # consensus    | 共识层（4派全认可）
                                   # complementary| 互补层（2-3派同向）
                                   # exclusive    | 独门层（单派独有）

  domain_weight:                   # 适用领域（用于策略选择器）
    - geju                         # 格局
    - fugui                        # 富贵层级

  source:                          # 必填 · 可追溯来源
    file: "高派理法篇_31页.md"
    section: "第三章·假从格"
    page_in_source: 15
    extracted_in: "META/extracted/高派_理法篇_候选规律提取_2026-05-19.md"

  status: promoted                 # 必填 · 入库状态
                                   # candidate | 候选（未应验）
                                   # promoted  | 已晋级（≥3例应验）
                                   # retired   | 已退役（≥3例失验）
                                   # frozen    | 冻结（暂不使用）

  promoted_at: 2026-05-22          # 晋级日期
  last_updated: 2026-05-23

  notes: |                         # 备注（可选）
    高派与段派在此条上虽路径不同，但结论一致，互为佐证。
```

---

## 二、主题（topic）枚举

| topic 值 | 中文 | 适用范围 |
|---|---|---|
| `lifa` | 理法 | 体用得失、强弱真假、格局成立 |
| `geju` | 格局 | 格局定性、清浊高低、富贵层次 |
| `xiangfa` | 象法 | 象意推断、画面、引申断 |
| `shensha` | 神煞 | 神煞应用、贵神凶神 |
| `dayun` | 大运流年 | 运程推演、流年应期 |
| `yingqi` | 应期 | 具体事件应期推断 |
| `caiyun` | 财运事业 | 财富事业断 |
| `hunyin` | 婚姻情感 | 婚期、配偶、感情 |
| `liuqin` | 六亲画像 | 父母、兄弟、子女、配偶 |
| `jiaoyu` | 学业 | 读书、学历、文凭、考试 |
| `jiankang` | 健康灾厄 | 疾病、车祸、生死、灾厄 |
| `zhiye` | 职业 | 行业归属、工种适宜 |
| `tiaohou` | 调候改运 | 调候、改运、风水补救 |
| `mingong` | 命宫 | 命宫长生诀（高派独门） |
| `zeri` | 择日 | 择日、剖腹产择日 |

---

## 三、派别字母前缀

| 字母 | 派别 | 全称 |
|---|---|---|
| G | 高 | 高德臣盲派 |
| D | 段 | 段建业盲派 |
| Y | 杨 | 杨清娟盲派 |
| R | 任 | 任付红盲派 |
| E | 预留一 | （第 5 派预留入口 · 启用时改为真实派名，目录 `ext1`） |
| F | 预留二 | （第 6 派预留入口 · 启用时改为真实派名，目录 `ext2`） |

---

## 四、ID 命名规则

```
{派别}-{topic}-{序号}

示例：
G-LIFA-001       高派理法第1条
D-GEJU-015       段派格局第15条
Y-HUNYIN-008     杨派婚姻第8条
R-YINGQI-003     任派应期第3条
```

特殊：
- 共识规律（4 派均有，已合并到 mapping/consensus.md）使用 `CON-` 前缀，如 `CON-001`
- 互补规律组合（多派联立，存于 mapping/complementary.md）使用 `COM-` 前缀

---

## 五、入库流程

1. **抽取**：从 `sources/{school}/` 原始文档抽取候选规律
2. **填 schema**：按本 schema 写入 `theory/{school}/*.yaml`
3. **打分**：根据 `engine/confidence.yaml` 计算 `static` 静态分
4. **跨派对照**：在 mapping/ 目录登记同向/冲突关系
5. **状态标记**：默认 `status: candidate`，等待实战应验
6. **晋级**：≥3 例应验且命中率 ≥66% → `status: promoted`
7. **退役**：≥3 例失验且命中率 <33% → `status: retired`

详见 `META/ingestion-protocol.md`。
