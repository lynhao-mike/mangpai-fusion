# 来源追溯账本 · v1.0

> 记录本仓库每份语料/规律的来源，保证 100% 可追溯。

最后更新：2026-05-23

---

## 一、4 派原始语料（sources/）

### 高派（gao）· 来源仓库 lynhao-mike/Mang.pai

| 文件 | 大小 | 说明 |
|---|---|---|
| `2018弟子班_理法篇_31页.md` | 31p | 理法基础（强弱真假/格局/体用） |
| `2018弟子班_象法篇_83页.md` | 83p | 象法详解（象意/画面/引申） |
| `2018弟子班_神煞篇_34页.md` | 34p | 神煞基础 |
| `盲派神煞应用宝典.md` | - | 神煞应用宝典（高派独门武器） |
| `2018弟子班_财运篇_43页.md` | 43p | 财运（基础） |
| `财运事业断法弟子提高班_105页.md` | 105p | 财运事业进阶 |
| `2018弟子班_车祸婚姻篇_85页.md` | 85p | 车祸 + 婚姻 |
| `2018弟子班_车祸篇_9页.md` | 9p | 车祸专题 |
| `2018弟子班_大运流年篇_55页.md` | 55p | 大运流年三层互动 |
| `2018弟子班_命宫长生诀择日篇_78页.md` | 78p | 命宫 + 择日（高派独门） |
| `README.md` | - | 知识库索引 |

**合计**：10 份理论文档 + 1 README ≈ 596 页

### 段派（duan）· 来源仓库 lynhao-mike/gufamangpai

44 份 MinerU 转译的 markdown 文档，覆盖：
- 段建业盲派命理断语集
- 八字断句集 1-10 集
- 盲派批命案例集 263 例 74 页
- 乾坤之论 / 案例析
- 各类专题讲座

### 杨派（yang）· 来源仓库 lynhao-mike/gufamangpai

26 份 MinerU 转译文档，覆盖：
- 杨清娟命理基础电子书 261 页
- 教学体系命例集细解 245 页
- 配套学员笔记
- 基础篇 / 内部资料篇 等讲座

### 任派（ren）· 来源仓库 lynhao-mike/gufamangpai

30 份 MinerU 转译文档，覆盖：
- 任付红民间实用八字财运/官运/初级/高级
- 断命例题解
- 18 道法门系列等

---

## 二、已结构化理论（theory/raw/）

### 高派（gao）

#### `theory/raw/gao/extracted/` · 候选规律抽取
9 份文件，来自 Mang.pai/.kiro/skills/META/extracted/。
每份对应一个原始篇章，提取候选规律列表（已含触发条件 + 推断结论）：

| 文件 | 对应原文 |
|---|---|
| 高派_理法篇_候选规律提取_2026-05-19.md | 2018弟子班_理法篇 |
| 高派_象法篇_候选规律提取_2026-05-19.md | 2018弟子班_象法篇 |
| 高派_神煞篇_候选规律提取_2026-05-19.md | 2018弟子班_神煞篇 |
| 高派_神煞应用宝典_候选规律提取_2026-05-19.md | 盲派神煞应用宝典 |
| 高派_财运篇_候选规律提取_2026-05-19.md | 2018弟子班_财运篇 |
| 高派_财运事业断法_候选规律提取_2026-05-19.md | 财运事业断法弟子提高班 |
| 高派_车祸婚姻篇_候选规律提取_2026-05-19.md | 2018弟子班_车祸婚姻篇 |
| 高派_大运流年篇_候选规律提取_2026-05-19.md | 2018弟子班_大运流年篇 |
| 高派_命宫长生诀择日篇_候选规律提取_2026-05-19.md | 2018弟子班_命宫长生诀择日篇 |

**合计**：约 261 条候选规律（已晋级 249 条）

#### `theory/raw/gao/promoted/` · 已晋级模块
9 份模块文件，来自 Mang.pai/.kiro/skills/modules/：
- module-a-paipan.md（排盘）
- module-b-geju.md（格局）
- module-c-yunqi.md（运气）
- module-c2-zaihou.md（灾厄）
- module-c3-yingqi.md（应期）
- module-d-hehun.md（合婚）
- module-e-zeri.md（择日）
- appendix-quxiang.md（取象）
- appendix-zhiye.md（职业）

### 段派（duan）

#### `theory/raw/duan/` · 段派理论提取
11 份理论文件（来自 gufamangpai/.kiro/skills/protocol/theory/）：
- d-small-theory.md（小法门）
- d01-deep-read.md（D01 深读）
- d02 / d03 / d05 / d06-d09 / d10 / d15-d18 / d19-d24 / d25-d29

涵盖段建业 D01-D29 全部 法门（约 290 条规律）

#### `theory/raw/duan/promoted/` · 段派模块
5 份模块文件（来自 gufamangpai/.kiro/skills/modules/m1/）：
- m1-foundation.md / m1-patterns.md / m1-practice.md / m1-timing.md / index.md

### 杨派（yang）

#### `theory/raw/yang/` · 杨派理论提取
7 份理论文件（来自 gufamangpai/.kiro/skills/protocol/theory/）：
- y01-y05 / y06-y08 / y09-y13 / y14-y21 / y22-y25 / y26-y29

涵盖杨清娟 Y01-Y29 全部法门（约 163 条规律）

#### `theory/raw/yang/promoted/` · 杨派模块
8 份模块文件（来自 gufamangpai/.kiro/skills/modules/m2/）：
- m2-disaster / m2-five-steps / m2-imagery / m2-marriage / m2-rules-registry / m2-shishen / m2-tuning / index

### 任派（ren）

#### `theory/raw/ren/` · 任派理论提取
8 份理论文件（来自 gufamangpai/.kiro/skills/protocol/theory/）：
- r01-r04 / r05-r07 / r09-r14 / r15-r20 / r21-r26 / r29-r30 + m3-ren-integration

涵盖任付红 R01-R30 全部法门 + 18 道法门整合（约 200 条规律）

#### `theory/raw/ren/promoted/` · 任派模块
5 份模块文件（来自 gufamangpai/.kiro/skills/modules/m3/）：
- m3-foundation / m3-mechanics / m3-rules-registry / m3-tools / index

---

## 三、参考资料（不直接采用）

### `theory/raw/_legacy-shared-rules/`
gufamangpai 已经做过的跨派共识工作（4 份），可参考：
- confirmed-rules.md
- consensus-candidates.md
- production-ready-rules.md
- promotion-pipeline.md

⚠️ 注意：这些只覆盖段+杨+任三派，**不含高派**，需要在 M4 阶段重新做四派共识工程。

### `theory/raw/_legacy-protocol-ref/`
gufamangpai 已有的引擎/协议文件（参考）：
- engine-dimensions.yaml（三维引擎，将扩展为五维）
- evidence-aggregator.yaml（证据聚合器）
- strategy-selector.yaml（策略选择器）
- school-arbitration.md（14 条 CF 仲裁）
- output-adapter.yaml（输出适配器）
- level-scales.md（富贵层级 L0-L5）
- cross-validation.md（跨派校验）
- sources-manifest.md（来源清单）

⚠️ 这些是**三派架构**，本仓库要重写为**四派架构**，但可借鉴。

---

## 四、规律量级总览

| 派别 | 候选规律量 | 已晋级量 | 来源覆盖 |
|---|---|---|---|
| 高德臣 | ~261 | ~249 | 10 份原典 |
| 段建业 | ~290 | ~290 | 44 份原典 |
| 杨清娟 | ~163 | ~163 | 26 份原典 |
| 任付红 | ~200 | ~200 | 30 份原典 |
| **合计** | **~914** | **~902** | **110 份原典** |

---

## 五、每条规律必须可回溯

任何 `theory/{school}/*.yaml` 中的规律必须能通过 source 字段追溯到：
1. `sources/{school}/` 中的某份原典
2. （如有）`theory/raw/{school}/extracted/` 或 `promoted/` 中的提取记录

无法回溯的规律 → 标记为 `status: frozen` 等待人工核查。

---

## 六、变更日志

- **2026-05-23**：初始化，4 派语料全量迁入完成
