# T-189a · scorer v2 核心（三层 + 地址/字 + nj=miss + 引文 + Wilson）

- 状态：🔵 Ready
- 依据：`docs/specs/adjudication-a-plus-v1.md` §3/§4；T-189 拆分
- 前置：main `46c00c3a`；T-189 房间耗尽、无产物

## 0. 一句话

只写 **核心评分器**：三层分录、地址/字对齐、dynamic 上 nj=miss、ambiguous 的 conflict_quotes[2]、Wilson。
**不做 B1/B2、chart 聚类、3 次一致、T-187 回归**；这些留给 T-189b。

## 1. 范围

- 新 `tools/p1_assertion_eval_v2.py`：
  - 读 fixed 10 / dynamic 40 / ambiguous 10（JSON 三层；`layer` 字段）；
  - `addr_a/addr_b` 与 `char_a/char_b` 双向归一；
  - dynamic：correct / wrong / nj（nj=miss）；ambiguous：expected nj + conflict_quotes[2] 逐字行内；
  - `correct/total`、`precision`、`delivered`、Wilson 95% CI；分类型小表。
- 新 `tests/tools/test_p1_assertion_eval_v2.py`：合成 fixture（全对/32-8/全错/nj/ambiguous 缺引文/地址字对齐）；
- **不读/不跑真实 anchor-60**；不读 T-187 产物（T-189b 再做回归）。

## 2. 产物

- 分支 `p1/assertion-v2a`（worktree `..\mangpai-fusion-av2a`，从 `46c00c3a` 起）
- 上述 2 文件 + `tasks/T-189a/BRIEF.md`/`STATUS.md`
- `pytest tests/tools/test_p1_assertion_eval_v2.py -q` 0 failed

## 3. 禁止

- 不做 B1/B2/cluster/3-run/T-187 回归；不改 engine/答案/阈值；
- 不把 fixed 混进 dynamic；不跑真实数据；不 push main。
