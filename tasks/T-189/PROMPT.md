# T-189 · scorer v2（三层 + 地址/字 + B1/B2 + 聚类）

- 状态：🔵 Ready
- 依据：`docs/specs/adjudication-a-plus-v1.md` §3/§4；Gemini v5/WB v4/Opus v6
- 前置：main `fd4188aa`

## 0. 一句话

写独立的 `tools/p1_assertion_eval_v2.py`：fixed 10 / dynamic 40 / ambiguous 10 三层独立记账；
地址/字双向对齐；decidable 上 nj=miss；ambiguous 校验 conflict_quotes[2]；B1/B2 含四库 fallback；
chart 聚类 CI；3 次一致；先用 T-187 fixture 复算 12/40、2/20、28/40。

## 1. 输入

- `--fixed`、`--dynamic`、`--ambiguous`：三层答案（可合并为一个 JSON 的 layers）
- `--system-output`：三层断言；每条 `case_id, addr_a, addr_b, char_a, char_b, mechanism, direction, actor_addr, target_addr, mutual, conflict_quotes?`
- `--t187-run` + `--t187-answers`：回归 fixture（可选；用于复算）
- 地址/字：`Y.s/Y.b/M.s/M.b/D.s/D.b/H.s/H.b` ↔ 四柱字符；双向精确对齐。

## 2. 指标 / 阈值（只读 A+ v1.3，不自定义）

- fixed 10/10；dynamic correct/40；ambiguous pass 7/10；nj=miss；conflict_quotes 逐字行内；
- B1 = delta 符号（平局柱序左）；B2 = 本气克→克方；本气生→生方；本气同五行（四库）→主位端（D/H 优先，同主/同宾柱序靠后）；
  margin = correct − max(B1,B2)；pass ≥32/40 + Wilson>65% + cluster≥78% + margin≥+8；
- 28–31 灰；≤27 kill；复测≤31 kill；nj≥5 kill；引文≥3 kill；3 次<90% kill；
- T-187 回归必须复算：edge 12/40、direction 2/20、edge mismatch 28/40；不能复算=scorer 没修好，停。

## 3. 产物

- `tools/p1_assertion_eval_v2.py`
- `tests/tools/test_p1_assertion_eval_v2.py`（合成 fixture + T-187 回归）
- 分支 `p1/assertion-v2`（worktree `..\mangpai-fusion-av2`，从 `fd4188aa` 起）
- `tasks/T-189/BRIEF.md`/`STATUS.md`

## 4. 禁止

- 不跑真实 anchor-60；不改 engine/规则/答案；不调阈值/分母；不把 fixed 混进 dynamic；不 push main。
