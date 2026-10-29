# T-190b BRIEF · annotator B

- 任务卡：`tasks/T-190b/PROMPT.md`
- 执行者：子代理 AQ（annotator B）
- 日期：2026-10-29
- 状态：✅ 已交付（60/60；待中枢开盒比较 A/B）

## 1. 改动文件

| 文件 | 状态 | 说明 |
|---|---|---|
| `META/p1-anchor-60-answers-B-v1.json` | 新增 | 60 条 B 答案；`schema_version=p1-adjudication-answers/v2`；sha256 `bb4a36bd930c4e2f51d2bcd17993881afa5e6f42fd6e013c6743c11f6ad25af1` |
| `META/p1-anchor-60-B-v1.md` | 新增 | 60 条清单 / 对齐 / engine 预检 / ambiguous 双引文 / 8 条性别 / disputed / hash |
| `tasks/T-190b/verify_b.py` | 新增 | 仅标准库的交付自检（结构、三层、端点字、逐字引文、source_texts、hash；不评分） |
| `tasks/T-190b/BRIEF.md` | 新增 | 本文件 |
| `tasks/T-190b/STATUS.md` | 更新 | 状态、交付物、自检结果、Execution Log |

未改动：盲卷、A 答案、`sources/`、`engine/`、`tests/`、评分器；未做 git 写操作。

## 2. 原始输出

```text
# engine.cli 预检（54 次调用：53 盘 + A60-005/A60-045 同柱不同性别各一次）
charts 54 bad 0
60/60 端点 addr→char 与盲卷一致

# 引文逐字回查（60 条，回查 sources/duan 原行）
checked 60 bad 0

# 交付自检（非评分器）
$ python tasks/T-190b/verify_b.py --expect-hash bb4a36bd930c4e2f51d2bcd17993881afa5e6f42fd6e013c6743c11f6ad25af1
cases=60 layers={'fixed': 10, 'dynamic': 40, 'ambiguous': 10}
sha256=bb4a36bd930c4e2f51d2bcd17993881afa5e6f42fd6e013c6743c11f6ad25af1
PASS
```

- 输入 hash：blind `9c730d35ae1a1d8881ec55522ac114ee3d83bbbbd54802e7c87d55fca7217bc3`；A+ 规格 `2a9ad12cc08ee816fd1fa2fe1b7b4947d2db9e3d7eb31bd736b1872f38d64803`。
- 56 条 directed（fixed 10 + dynamic 39）按 `char_a=actor / char_b=target` 输出；1 条 dynamic mutual（A60-047）。
- ambiguous 10 条全部 `needs_judgment` + `conflict_quotes[2]` + `source_texts[2]`（逐字整行）。

## 3. 未完成与风险

- **未做 A/B 一致性比较**：按卡由中枢开盒比较；B 全程未读 A 答案，无法预判一致率。
- **未跑评分器/runner**：本卷不含任何 pass/kill 判定。
- **disputed 1 条**：`A60-042`（癸卯 壬戌 壬寅 乙巳，卯/戌）。盲卷标 `刑`，但原文/engine 均为卯戌 **六合**、卯制戌，B 改标 `kind=合`、方向 `卯→戌`，并标 `disputed=true`。不改盲卷。
- **主观取舍点**（中枢复核优先看）：
  - `A60-023` 午未合：原文只说「午未相合」，B 取原文主语「午」为 actor；若按合为互绊应记 mutual。
  - `A60-045` 寅巳：段派「寅穿巳为主、刑为附带」，B 保留盲卷 `刑`、方向寅→巳，仅注记口径差异。
  - `A60-047` 子卯：段派内部有「子卯为破非刑」异说；B 取《命理瑰宝》「子卯刑，卯与子两伤」标 mutual。
  - ambiguous 10 条均按真歧义处理，不替原文选边。
- **8 条盲卷「未注明」性别**：均据原书/同盘互证补定（7 乾、1 坤），逐条依据见 MD §7；若中枢要求严格保留「未注明」可按表回退，不影响方向。
- **文本风险**：`sources/duan/` 为 OCR 文本，存在空格与「巳/己」混排；引文均对现有行逐字回查，保留原空格。

## 4. 下游须知

1. 读 `META/p1-anchor-60-answers-B-v1.json`：端点只用 `char_a/char_b`，**不写全局 `addr_a/addr_b`**（避免跨盘同名宫位地址在 scorer 地址簿归一冲突）；盲卷地址保留在 `blind_addr_a/blind_addr_b`。
2. 方向编码：directed 条 `char_a` 恒为 actor、`char_b` 恒为 target；`expected_direction="actor→target"`。mutual 条 `expected_direction="mutual"`、`relation.mutual=true`。ambiguous 条 `expected_direction="needs_judgment"`、`relation.actor/target=null`。
3. `kind` 用中文（克/生/化/墓、冲/合/穿/刑）；`blind_mechanism` 保留盲卷原机制，便于核对 `A60-042` 的改标。
4. ambiguous 的 `source_texts` 是「定位符→整行原文」，`conflict_quotes` 为行内逐字片段；比较时直接用 JSON，不要只读 MD 的截断引文。
5. 自检命令：`python tasks/T-190b/verify_b.py --expect-hash bb4a36bd930c4e2f51d2bcd17993881afa5e6f42fd6e013c6743c11f6ad25af1`（退出码 0；只验交付结构，不评分）。
6. 本卷未读 A 答案；若中枢比较后要求复标，请先确认是否需要保留 8 条已补性别与 `A60-042` 的 `合` 改标。
