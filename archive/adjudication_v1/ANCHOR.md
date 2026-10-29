# anchor-60 final v2 · 归档锚点

> 任务：T-192；归档日期：2026-10-29。
> 状态：A+ v1.3 方向产品 **KILLED**；本锚点只作历史留证，不再用于新盲跑。
> 本文件只列 case_id / layer / chart_id / 归档状态，不含方向、端点答案或引文。

## 冻结与归档

- blind final v2 sha256：`cc88d10ea15ac68c72bcb82ac1ba982ab177e169e678897bfd6f2010aadb7292`（与 T-190 冻结值一致）
- answers final v2 归档 sha256：`754caa14f4fcffb36385bebf636eef150ae8f6c967fa539463f42ddde6c189d2`
- answers 冻结记录 sha256：`4c6ee69a3a303de5d335af1e4fa20f84f5bf0bf7c9b9f5c9706d0de78902cd53`（见 `anchor/p1-anchor-60-final-v2.md`；与归档副本不一致，原因见 README §5）
- 归档副本：`anchor/p1-anchor-60-blind-final-v2.json`、`anchor/p1-anchor-60-final-v2.md`；答案在 `restricted/p1-anchor-60-answers-final-v2.json`。

## 使用状态

- 全部 60 条已在 T-191 被三份 run 使用，不再构成新的盲集。
- 其中 3 条标 `contaminated`：T-192 前 notes §5 曾公开写明方向，**永久排除**未来盲集/演示/评分。
- 污染详情只在 `restricted/contamination-list-v1.json`；本文件不复述方向。

## 逐条锚点

| case_id | layer | chart_id | 归档状态 |
|---|---|---|---|
| A60-001 | fixed | A60-CH01 | used |
| A60-002 | fixed | A60-CH02 | used |
| A60-003 | fixed | A60-CH03 | used |
| A60-004 | fixed | A60-CH04 | used |
| A60-005 | fixed | A60-CH05 | used |
| A60-006 | fixed | A60-CH06 | used |
| A60-007 | fixed | A60-CH07 | used |
| A60-008 | fixed | A60-CH08 | used |
| A60-009 | fixed | A60-CH09 | used |
| A60-010 | fixed | A60-CH10 | used |
| A60-011 | dynamic | A60-CH11 | used |
| A60-012 | dynamic | A60-CH12 | used |
| A60-013 | dynamic | A60-CH13 | used |
| A60-014 | dynamic | A60-CH14 | used |
| A60-015 | dynamic | A60-CH15 | used |
| A60-016 | dynamic | A60-CH16 | used |
| A60-017 | dynamic | A60-CH08 | used |
| A60-018 | dynamic | A60-CH17 | used |
| A60-019 | dynamic | A60-CH18 | used |
| A60-020 | dynamic | A60-CH19 | contaminated |
| A60-021 | dynamic | A60-CH04 | used |
| A60-022 | dynamic | A60-CH20 | used |
| A60-023 | dynamic | A60-CH21 | used |
| A60-024 | dynamic | A60-CH22 | used |
| A60-025 | dynamic | A60-CH23 | used |
| A60-026 | dynamic | A60-CH24 | used |
| A60-027 | dynamic | A60-CH25 | used |
| A60-028 | dynamic | A60-CH26 | used |
| A60-029 | dynamic | A60-CH06 | used |
| A60-030 | dynamic | A60-CH27 | used |
| A60-031 | dynamic | A60-CH28 | used |
| A60-032 | dynamic | A60-CH29 | used |
| A60-033 | dynamic | A60-CH30 | used |
| A60-034 | dynamic | A60-CH31 | used |
| A60-035 | dynamic | A60-CH32 | used |
| A60-036 | dynamic | A60-CH33 | used |
| A60-037 | dynamic | A60-CH34 | used |
| A60-038 | dynamic | A60-CH35 | used |
| A60-039 | dynamic | A60-CH36 | used |
| A60-040 | dynamic | A60-CH37 | used |
| A60-041 | dynamic | A60-CH38 | used |
| A60-042 | dynamic | A60-CH39 | used |
| A60-043 | dynamic | A60-CH40 | used |
| A60-044 | dynamic | A60-CH41 | used |
| A60-045 | dynamic | A60-CH05 | used |
| A60-046 | dynamic | A60-CH42 | contaminated |
| A60-047 | dynamic | A60-CH43 | used |
| A60-048 | dynamic | A60-CH44 | used |
| A60-049 | dynamic | A60-CH45 | used |
| A60-050 | dynamic | A60-CH46 | contaminated |
| A60-051 | ambiguous | A60-CH47 | used |
| A60-052 | ambiguous | A60-CH48 | used |
| A60-053 | ambiguous | A60-CH49 | used |
| A60-054 | ambiguous | A60-CH21 | used |
| A60-055 | ambiguous | A60-CH50 | used |
| A60-056 | ambiguous | A60-CH51 | used |
| A60-057 | ambiguous | A60-CH52 | used |
| A60-058 | ambiguous | A60-CH32 | used |
| A60-059 | ambiguous | A60-CH53 | used |
| A60-060 | ambiguous | A60-CH18 | used |

## 统计

- 总数：60；fixed 10；dynamic 40；ambiguous 10
- contaminated：3；其余 used（已用，非干净盲集）。
