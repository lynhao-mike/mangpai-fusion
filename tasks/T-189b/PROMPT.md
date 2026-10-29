# T-189b · scorer v2 增量（B1/B2、聚类、3 次、T-187 回归）

- 状态：🔵 Ready（等 T-189a 合并）
- 依据：`docs/specs/adjudication-a-plus-v1.md` §3/§4；T-189 拆分
- 前置：T-189a 已合并

## 0. 一句话

在 T-189a 核心里加：B1/B2（含四库 fallback）、margin、chart 聚类、3 次一致、T-187 回归
（必须复算 **12/40、2/20、28/40**）。不再重写三层。

## 1. 范围

- `tools/p1_assertion_eval_v2.py` 增量：
  - B1 = delta 符号（平局柱序左）；B2 = 本气克→克方、本气生→生方、本气同五行（四库）→主位端（D/H 优先，同主/同宾柱序靠后）；
  - margin = correct − max(B1,B2)；
  - chart_id 聚类 CI；3 次运行一致率；
  - T-187 回归：读 `META/p1-system-run-v1.json` + fresh-40 答案，地址/字归一，复算 edge 12/40、direction 2/20、mismatch 28/40；写在测试里，不宣称新结果。
- `tests/tools/test_p1_assertion_eval_v2.py` 增量；合成 fixture。
- 不跑 anchor-60；不改 engine/答案/阈值。

## 2. 产物

- 分支 `p1/assertion-v2b`（worktree `..\mangpai-fusion-av2b`，从 T-189a 合并后的 main 起）
- 工具 + 测试 + `tasks/T-189b/BRIEF.md`/`STATUS.md`
- `pytest tests/tools/test_p1_assertion_eval_v2.py -q` 0 failed；T-187 回归三数必须出现

## 3. 禁止

- 不重写三层；不做真实盲跑；不改阈值/分母；不 push main。
