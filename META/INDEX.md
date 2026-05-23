# META · 自迭代元数据层

> 本目录是 mangpai-fusion 系统的"自我反思"与"自我升级"层。  
> 每次案例 + 反馈都会在这里留下痕迹，让系统不断进化。

---

## 文件组织

```
META/
├── INDEX.md                       本文件
├── ingestion-protocol.md          理论入库 5 阶段管线
├── calibration-methodology.md     双轨置信度校准方法论
├── source-trace.md                4 派来源追溯账本
├── rule-changelog.md              所有规律变更日志
├── arbitration-log.md             仲裁裁决记录（每案）
└── extracted/                     原始抽取过程档案
    └── (按需迁入 Mang.pai/.kiro/skills/META/extracted/ 的内容)
```

---

## 5 大职能

### 1. 理论入库（ingestion）
- 来源：`sources/{school}/`
- 流程：S1 抽取 → S2 归一 → S3 打分 → S4 跨派对照 → S5 入库
- 协议：`ingestion-protocol.md`

### 2. 置信度校准（calibration）
- 输入：案例反馈（应验/失验）
- 流程：hit_count/miss_count → dynamic_score → final_score → star → status_transition
- 工具：`tools/calibrate.py`
- 方法论：`calibration-methodology.md`

### 3. 来源追溯（source trace）
- 每条规律必须可追溯到 `sources/{school}/` 中的原始文档
- 账本：`source-trace.md`

### 4. 变更登记（changelog）
- 所有规律的新增/晋级/退役/冻结操作必须登记
- 文件：`rule-changelog.md`

### 5. 仲裁记录（arbitration log）
- 每次派别冲突仲裁的记录
- 用于回溯仲裁正确性，调整 CF 规则
- 文件：`arbitration-log.md`（M7 创建）

---

## META 与其他目录的关系

```
              ┌─────────────────────────┐
              │  sources/{school}/      │
              │  原始语料               │
              └────────────┬────────────┘
                           │ S1 抽取
                           ▼
              ┌─────────────────────────┐
              │  theory/raw/{school}/   │
              │  半结构化抽取记录       │
              └────────────┬────────────┘
                           │ S2 归一
                           ▼
              ┌─────────────────────────┐
              │  theory/{school}/       │
              │  *.yaml 索引            │ ← 由 META/ingestion-protocol.md 管控
              └────────────┬────────────┘
                           │ S3-S4 打分 + 对照
                           ▼
              ┌─────────────────────────┐
              │  mapping/*.md           │
              │  共识/互补/独门/冲突    │ ← 由 META/source-trace.md 维护
              └────────────┬────────────┘
                           │ S5 入库 → 实战使用
                           ▼
              ┌─────────────────────────┐
              │  cases/C-YYYY-NNN/      │
              │  实战案例 + 反馈        │
              └────────────┬────────────┘
                           │ 反馈采集
                           ▼
              ┌─────────────────────────┐
              │  tools/calibrate.py     │
              │  自动重算 hit_rate      │ ← 由 META/calibration-methodology.md 实现
              └────────────┬────────────┘
                           │ 写入
                           ▼
                ┌──────────────────────────┐
                │  META/rule-changelog.md  │
                └──────────────────────────┘
                           │
                           │ 升降级 → 反向更新
                           ▼
              ┌─────────────────────────┐
              │  theory/{school}/       │
              │  mapping/*.md           │ ← 形成闭环
              └─────────────────────────┘
```

---

## META 维护规则

1. **不可手动篡改 hit_count**：只能通过 `tools/calibrate.py` 触发
2. **每次校准必登记 rule-changelog**
3. **来源追溯必须 100% 完整**：无法追溯的规律 → frozen
4. **仲裁错误必须显式记录**：用于改进 CF 规则
5. **M7 阶段后**：每月自动生成 `META/monthly-report.md`（健康度报告）
