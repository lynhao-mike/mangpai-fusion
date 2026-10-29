# T-188 · 自刑候选过滤（A+ v1.3 Step 1）

- 状态：🔵 Ready
- 依据：`docs/specs/adjudication-a-plus-v1.md` §2；Gemini v5/WB v4/Opus v6
- 前置：main `fd4188aa`

## 0. 一句话

`RelationGraph.edges` 里的自刑边（酉酉/亥亥/午午/辰辰）保留为事实边，但在
`build_duan_zuogong_candidates` 中**逐条 logged 剔除**，不再冒充做功候选。不做其他规则。

## 1. 改动

- `engine/facts/structure_check.py`：
  - 在候选循环里，若 `e.kind == "xing"` 且两端地支字符相同（或 `e.completeness == "zixing"`），跳过 `emit`；
  - 保留该边在 `RelationGraph.edges`；不删、不改边 ID；
  - 记录被剔除的 edge_id（logger.debug 或候选 notes；不得静默）；
  - 不碰 party/方向/其他 kind。
- 测试：
  - 酉酉/亥亥/午午/辰辰 不出现在 `duan_zuogong.candidates`；
  - 同一盘 `RelationGraph.edges` 仍有这些边；
  - 非自刑的 xing（如 丑戌刑、未戌刑）仍保留候选（mutual 候选由后续 Agent 决定）。

## 2. 验证

- `pytest -q` 0 failed；1489+新增；
- `engine_audit` 481/0；relations 全过；15KB 测试盘 <15,000B；
- dev-20 只作否决：显式 `--out-json META/p1-dev20-selfx-veto.json --artifact-label dev20_selfx_veto` 一次，确认无回退；
- 不跑 anchor-60/fresh-40；不碰 party/党势。

## 3. 产物

- 分支 `p1/selfxing`（worktree `..\mangpai-fusion-selfx`，从 `fd4188aa` 起）
- `structure_check.py` + 测试 + `tasks/T-188/BRIEF.md`/`STATUS.md`

## 4. 禁止

- 不删 RelationGraph 边；不改非自刑 xing；不做党势/方向；不改 fresh-40/dev-20；不 push main。
