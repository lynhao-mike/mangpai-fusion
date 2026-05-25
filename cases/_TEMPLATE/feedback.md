# Case C-YYYY-NNN · 命主反馈

> v1.3 D5 工作流：**报告即反馈表**。命理师把 master 报告另存为本文件后，
> 把每条 `反馈：[S-...] [ ]` 中的 `[ ]` 填为：
>
> | 标注 | 含义 | 计数 |
> |---|---|---|
> | `[y]`    | 应验 | 计 hit |
> | `[n]`    | 失验 | 计 miss |
> | `[?]`    | 命主当场不知道 | 入库不计数（等延迟反馈兑现） |
> | `[skip]` | 解释时未讲到 / 不适用 | 入库不计数 |

**反馈日期**：YYYY-MM-DD  
**采集方式**：[面对面 / 电话 / 微信 / 视频]  
**关联报告**：reports/C-YYYY-NNN-master.md  
**关联索引**：cases/C-YYYY-NNN/statement_index.json  

---

## 一、推荐工作流（v1.3）

```bash
# Step 1: 命理师把 master 报告另存为 feedback.md
cp reports/C-YYYY-NNN-master.md cases/C-YYYY-NNN/feedback.md

# Step 2: 编辑 feedback.md，把每条 `[ ]` 填为 [y]/[n]/[?]/[skip]
# 不必填全所有断语，只填解释时讲到的那些

# Step 3: 一键摄入
python3 -m tools.feedback_ingest C-YYYY-NNN

# 系统会自动：
#   ① 解析 [S-...] [y/n/?/skip] 标注
#   ② 反查 statement_index.json 找规律 ID
#   ③ fanout 到 rule-level verdicts（决断力优先：miss > hit > abstain > no_data）
#   ④ 调 _apply_rule_verdicts 重算置信度 + 升降级
#   ⑤ 写 META/iteration-log.md + META/calibration/*.snapshot.yaml
#   ⑥ bump META/iteration-state.json（每 10 完成反馈案 → 触发迭代报告）
```

---

## 二、断语反馈（从 master 报告填入）

> 把 master 报告里所有 `反馈：[S-...] [ ]` 行直接复制到这里并填值。
> feedback_ingest 只看 `[S-xxx-xxxxxx] [y/n/?/skip]` 这种正则匹配，
> 其他文字（章节标题、断语正文）保留不影响解析。

### 2.1 §A 能量层级

反馈：[S-NNN-xxxxxx] [ ]
反馈：[S-NNN-xxxxxx] [ ]

### 2.2 §C 应期铁口断

反馈：[S-NNN-xxxxxx] [ ]

### 2.3 §D 旁证（婚姻 / 健康）

反馈：[S-NNN-xxxxxx] [ ]

### 2.4 §E 共识 / 互补断语

反馈：[S-NNN-xxxxxx] [ ]
反馈：[S-NNN-xxxxxx] [ ]

---

## 三、命主新增信息（用于回填 input.md）

> 在与命主对话中获得的额外信息，可能影响后续分析。

- [新信息 1]：例 "命主提到 2015 年有过创业失败"
- [新信息 2]：例 "命主父亲八字是甲午年生"

这些信息可手动回填到 `cases/C-YYYY-NNN/input.md`。

---

## 四、命理师内部备忘（不入库）

> 仅供本案后续 review 时参考；feedback_ingest 不会解析此段。

- 整体准确率：[X/Y 条断语应验]
- 主要应验：
- 主要失误：
- 沟通体感：

---

## 五、向下兼容（v1.0 启发式路径）

如果本案早期已用 v1.0 表格式反馈（含 ✅/❌/🟡 等标记），且
`cases/C-YYYY-NNN/statement_index.json` 不存在，那么 `feedback_ingest`
会**自动退回**到 v1.0 启发式路径（`feedback_loop.parse_feedback_md` +
`parse_analysis_md`），无需手动转换。

> 详见 `tools/feedback_ingest.py` 的 fallback 分支。

---

## 模板版本

v1.3 · D5 结构化反馈 · 替代 v1.0 自由表格
