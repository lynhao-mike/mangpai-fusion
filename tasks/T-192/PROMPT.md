# T-192 · R-tool 共同收口：归档 + 泄漏修复 + R 规格

- 状态：🔵 Ready
- 依据：A+ v1.3 kill；Opus/WB 选 R、Gemini 选 S；人类同意 R-tool + B
- 前置：main `186d2833`

## 0. 一句话

把方向产品整体归档；把 3 张旧卡原样封存；把 A+ notes §5 的案例答案清掉；写 R-tool 的
`fact-evidence-pack-v1` 规格（B：不碰 AGENTS.md §4 / report-v7-human.md）。
**不做方向、不改 engine、不跑盲测。**

## 1. 归档

- `archive/adjudication_v1/`：
  - `README.md`：A+ kill（47.5%、margin+3、cluster72.5、ambiguous1/10、quote18/20）、3 条污染、DISPOSITION KILLED；
  - 复制：`adjudication-a-plus-v1.md`、`t191-a-plus-verdict-v1.md`、`p1-anchor-60-*`（blind/answers/final v2）、T-191 三跑、T-186/T-191 评分器（只归档，不移主测试）；
  - `restricted/`：answers/标签/污染清单，标注“runner 不可读”。
- `archive/demo/`：`docs/demo/single-chart-cards-v1.md` 与 `META/single-chart-cards-v1.json` 原样复制；
  原件头部加 `STATUS: ARCHIVED_RESEARCH_ARTIFACT`（不改造内容）。
- 3 条污染：A60-046/050/020 在归档锚点标 `contaminated`；永久排除未来盲集。

## 2. 泄漏修复

- `docs/specs/adjudication-a-plus-v1-notes.md` §5：删除具体案例 ID/端点/答案，只留“A/B 有 3 条分歧，细节在 restricted 归档”；
- 受限答案移到 `archive/adjudication_v1/restricted/`；runner 只读白名单输入包；
- 新增 `tools/check_bundle_case_ids.py`：出 bundle 前扫 `A60-/PF-/P1-H/G20` 等 case_id；发现即退出 1。

## 3. R-tool 规格

- `docs/specs/fact-evidence-pack-v1.md`：
  - 范围：`engine.cli` 事实 + `query_theory` + 问题→宫位/边ID/source_ref 证据包；
  - 不输出冲/合/穿/刑方向，不输出主次裁决/断语；固定克/生/化/墓只作事实；
  - 类外零发射；3 张旧卡不进演示；
  - 第一证明点：事实审计 100% + fixed-20 类外零发射 + 分流召回预注册；
  - 保护区文件不改；R 工具不套 `report-v7-human`。

## 4. 产物

- 归档目录 + R 规格 + 泄漏修复 + bundle 扫描工具
- `tasks/T-192/BRIEF.md` + `STATUS.md`
- 不做 git 写操作；中枢提交。

## 5. 禁止

- 不做方向/断语；不改 engine/规则/答案；不碰 AGENTS/report-v7-human；不跑盲测；不复活党势。
