# 理论入库协议 · v1.0

> 4 派理论从原始文档 → 结构化 YAML 入库的标准化流程。  
> 任何理论修改、新增、退役都必须遵循此协议。

---

## 一、五阶段管线

```
S1 抽取(Extract) → S2 归一(Normalize) → S3 打分(Score) → S4 跨派对照(Map) → S5 入库(Commit)
```

### S1 · Extract（抽取）

- 来源：`sources/{gao|duan|yang|ren}/*.md`
- 产出：`META/extracted/{派别}_{篇章}_候选规律提取_{日期}.md`
- 要求：
  - 保留原文引用（章节 + 页码）
  - 提取触发条件 + 推断结论
  - 一条规律 = 一个独立逻辑单元（不合并、不拆分歧义）

### S2 · Normalize（归一）

- 把 S1 的散文记录转写为 SCHEMA 格式
- 产出：`theory/{school}/*.yaml`（按 topic 分文件）
- 要求：
  - ID 唯一：`{派别}-{topic}-{序号}`
  - 字段全填（必填字段不可为空）
  - condition / conclusion 必须可独立读懂

### S3 · Score（打分）

- 静态分计算（详见 `engine/confidence.yaml`）：
  - 派别支持基线分（共识层 80 / 互补层 65 / 独门层 50）
  - 规律本身确定性加分（范围 -15 ~ +15）
  - 来源权威性加分（书籍/讲义/口诀 不同）
- 初始 hit_count / miss_count = 0
- 初始 status = `candidate`

### S4 · Map（跨派对照）

- 对每条新规律，在已入库规律中查找：
  - **同向**：结论相同或互相加强 → 写入 `cross_school` 字段 + `mapping/complementary.md`
  - **冲突**：结论相反 → 写入 `conflicts` 字段 + `mapping/conflicts.md`
- 4 派全部支持 → 升入 `mapping/consensus.md`
- 单派独有 → 写入 `mapping/exclusive.md`

### S5 · Commit（入库）

- 每次入库 = 一次 git commit
- commit message 格式：`theory({school}): add {N} {topic} rules from {source}`
- 同步更新 `META/rule-changelog.md`
- 同步更新 `META/source-trace.md`

---

## 二、晋级与退役

| 触发 | 当前 status | 新 status |
|---|---|---|
| 实战应验 ≥ 3 例，命中率 ≥ 66% | candidate | promoted |
| 实战失验 ≥ 3 例，命中率 < 33% | candidate / promoted | retired |
| 派别一致性证据补强（新增 cross_school） | candidate | candidate（仅 static 加分） |
| 严重冲突暴露 | promoted | candidate（降回观察） |
| 用户人工审定为不适用 | * | frozen |

晋级/退役**必须更新**：
- 该规律的 yaml 文件
- `META/rule-changelog.md`
- 关联的 `mapping/` 文件

---

## 三、来源追溯链

每条规律的 source 字段必须给出：
- `file`：原始文件名（位于 sources/）
- `section`：章节标题
- `page_in_source`：原文页码（如有）
- `extracted_in`：在 META/extracted/ 中的抽取记录文件

任何看到结论但找不到源头的规律 = **可疑数据**，标记 `status: frozen` 并人工复核。

---

## 四、工具支持

| 阶段 | 当前入口 | 自动化程度 |
|---|---|---|
| S1 抽取 | 人工 + LLM 协助 | 半自动 |
| S2 归一 | 历史 `tools/normalize_extracted.py` 当前不存在；按人工 review + `theory/*/index.yaml` 入库 | 半自动 |
| S3 打分 | 历史 `tools/score_initial.py` 当前不存在；按 `engine/confidence.yaml` 与人工 review | 半自动 |
| S4 对照 | 历史 `tools/cross_map.py` 当前不存在；当前跨派偏差运行时入口为 `tools/cross_school_scan.py` | 半自动 |
| S5 入库 | git + 手动 review | 半自动 |
| 反馈摄入 / 晋级退役 | `tools/feedback_ingest.py`（结构化入口）→ `tools/feedback_loop.py`（生命周期核心） | 自动（基于反馈） |

历史缺失工具不得作为当前可执行入口；当前工具状态以 `tools/README.md` 与 `tools/tool_registry.py` 为准。工具尚未实现的，先人工执行流程并记录于 `META/rule-changelog.md`。
