# EXTRACT-1 进度报告 · 杨派+段派（2026-10-17）

## 本日完成
- 新增 **223 条**（M2-Y-164..386），全部入 `theory/_light_index.json`（3471 → 3694，既有条目零改动）
- 5 个批次产物：`deep-extract-yang-b01.md`（41，gold standard）～`b05.md`（42）

## 领域分布（223 条合计）
| domain | 条数 |  | domain | 条数 |
|---|---|---|---|---|
| lifa | 122 |  | caiyun | 21 |
| jiankang | 18 |  | hunyin | 8 |
| liuqin | 15 |  | zhiye | 10 |
| geju | 9 |  | jiaoyu | 7 |
| xiangfa | 9 |  | shensha | 5 |
| yingqi | 4 |  | tiaohou | 1 |
| dayun | 1 |  |  |  |

content_status：full 222 / title_only 1（M2-Y-199 财星暗引食伤，原稿未展开）。

## 覆盖的任务重点
- ✅ 十神暗引五公式（b01 M2-Y-193..199，含细分金阴阳两路）
- ✅ 六穿医学断（b01 M2-Y-181..192 六组+总则）
- ✅ 开库体系（b02：入墓/开库定义/力量/吉凶/归属，20 条）
- ✅ 羊刃/华盖/空亡三态立场/禄五忌/枭印夺食（b02/b03/b04）
- ✅ 算命步骤（b05：原稿第七章 8 步——任务书「五步法」在 yang 源 0 命中，按实际文本提取）
- ✅ 甲辰活木（b04 M2-Y-341，任务书「活木死木」的系统 treatment 不在 yang 源，散见案例）

## 质量记录
- 追加前机械校验 223/223 通过（锚点存在 + verify_fragment ±5 行命中 + statement ≤200 字 + ID 无碰撞）
- 随机 10 条人工回读忠于原文
- 回归测试 19 项全过
- 无 anchor_confidence: low 条目（全部锚点均为 Read 工具亲验行号）

## 未解决（需人类/主 agent 裁决）
1. `tools/extraction_validator.py` 尚未提供，协议阶段三校验无法执行，本批以自建等价校验替代
2. 持久化通道：新记录目前仅存活于 `_light_index.json` 缓存；任一 index.yaml/sources 的 mtime 变化或运行 `tools/build_indexes.py` 会触发缓存重建并冲掉新条目。持久化需要写 `theory/raw/yang/` 扩权或手改 `theory/yang/index.yaml`

## 下一步
- b06：2017 五班 + 2018 六班转录的夫妻宫/应期/职业专题（目标 +177 条至 400）
- 杨派达标后切换段派深水区（16 格局细则/贼神捕神/过河拆桥等）


## 段派追加（同日 · 主 agent 指令后）

- 新增 **112 条**（M1-D-291..402）：`theory/raw/duan/promoted/deep-extract-duan-b01.md`（40：婚姻专辑+过河拆桥）、`b02`（40：体用/墓穿/宾主作用）、`b03`（32：象法篇干支类象+职业推断）。段派 290+112=402。
- 杨派修正：M2-Y-223 verify_fragment 补空格（theory/yang 与 raw 两副本）；b02-b05 我处副本以真源稿（完整 schema）覆盖；新增 b06 14 条（M2-Y-387..400，婚姻应期）→ 杨派 163+237=400。
- 验收：`extraction_validator` 全量 586 条 PASS/0 SUSPECT/0 FORGE；`pytest tests/tools/test_query_theory.py` 7 项过；检索实测新条目居首。
- 任务重点覆盖：16 格局细则之过河拆桥（7 例+反例）、贼神捕神做功体系定义源、反局要件（原局/大运）、连体带象借象之同象定义、干支类象职业推断（十干+十二支全表+20 职业例）、应期（死墓绝/引动冲去/巳运冲余财）。
- 已知坑：校验器 V2 精确子串（NBSP、跨行拼接均会 SUSPECT）；行号归属需 grep 复核。
