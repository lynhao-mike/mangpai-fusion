# T-189a STATUS

- 状态：✅ **已验收 / 已合并**（2026-10-29 17:30，中枢）
- 执行者：子代理（评分器 Agent）
- 任务卡：`tasks/T-189a/PROMPT.md`
- 分支：`p1/assertion-v2a`（worktree `..\mangpai-fusion-av2a`）
- 代码提交：`654b11e5`（rebased 到 `457c3cdc`；`46c00c3a` 仍是祖先）
- 验收：中枢亲自跑；只做核心
- 简报：`tasks/T-189a/BRIEF.md`

## Execution Log

| 时间 | 动作 |
|---|---|
| 17:15 | T-189 房间耗尽、无产物；拆 T-189a/189b，先派 a |
| 17:16 | 读卡 + 规格 §3/§4 + T-186 BRIEF + 旧测试的 schema 片段（未读 713 行旧工具）；建 worktree，分支从 `46c00c3a` 起 |
| 17:19 | 写 `tools/p1_assertion_eval_v2.py`（610 行）：三层分录、地址/字归一、nj=miss、conflict_quotes[2] 逐字行内、correct/precision/delivered/Wilson、by_kind、契约护栏 |
| 17:21 | 写 `tests/tools/test_p1_assertion_eval_v2.py`（493 行，19 函数 / 24 用例）；首轮 19 failed（`case_id` 未透传）→ 3 failed（delivered 口径、fixture 缺 book）→ **24 passed** |
| 17:24 | 全仓 `pytest -q`：**1513 passed, 1 skipped**（T-114 既有 skip），exit 0；合成 fixture A–E 用 CLI 跑完（`%TEMP%\t189a-smoke\`，非真实盘） |
| 17:25 | rebase 到 `457c3cdc`（让卡与 STATUS 在位，避免 add/add 冲突）；提交 `654b11e5`；写 BRIEF/STATUS |
| 17:30 | 中枢合并 `p1/assertion-v2a`；主仓 verify_baseline **1520/1、481/0、relations 全过**；15KB 14,653；24 个 v2 用例全过。注：子代理分支 1513 是 T-188 合并前（1496）基数；主仓 1520=1496+24。T-189b 补 B1/B2/聚类/3次/T-187 回归 |

## Blockers

**无硬阻塞。** 待中枢/T-189b 拍板的契约项（详见 `BRIEF.md` §3.2）：

1. v2 schema 是本卡自定（真实 anchor-60 字段若不同，先改卡再改码）；
2. 层与 kind 强绑定（`破` 只能进 ambiguous；dynamic 出现破边会退出 2）；
3. 地址须能落到单个地支字（天干/柱级编码要先映射）；
4. 引文只校验答案自带 `source_texts` 行，不读 `sources/` 真文件；
5. 不出 pass/kill（阈值判定、B1/B2、cluster、3-run、T-187 回归全部留给 T-189b）。
