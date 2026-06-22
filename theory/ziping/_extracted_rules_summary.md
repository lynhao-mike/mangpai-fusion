# 子平类八字分析规则全量抽取报告

## 一、规则库概览

- **规则总数**: 933 条
- **状态**: 全部 active（可被生产规则加载器读取）
- **来源**: [`sources/ziping/`](../../sources/ziping/) 原始 md 文档
- **输出**: [`theory/ziping/index.yaml`](index.yaml)
- **提取时间**: 2026-06-22
- **去重口径**: 规范化文本指纹去重；同义近义保留原典来源差异，后续由 merge map 合并。

## 二、来源分布

| 项目 | 数量 |
|---|---:|
| sources/ziping/《三命通会》.md | 727 |
| sources/ziping/穷通宝鉴-明-余春台_part1.md | 79 |
| sources/ziping/穷通宝鉴-明-余春台_part2.md | 66 |
| sources/ziping/《子平真诠》.md | 61 |

## 三、领域覆盖

| 项目 | 数量 |
|---|---:|
| 事业 | 820 |
| 婚姻 | 684 |
| 财富 | 653 |
| 健康 | 636 |
| 性格 | 456 |
| 家庭 | 230 |
| 学业 | 193 |
| 迁移 | 84 |
| 总体 | 19 |

## 四、主题归类

| 项目 | 数量 |
|---|---:|
| yongshen_pattern | 377 |
| wealth_structure | 247 |
| official_career | 127 |
| relations_combo | 79 |
| tiaohou_wuxing | 45 |
| marriage_family | 20 |
| health_body | 14 |
| food_injury | 13 |
| seal_resource | 4 |
| luck_timing | 3 |
| ziping_general | 2 |
| liunian_timing | 1 |
| shensha_tianluo | 1 |

## 五、触发器分布

| 项目 | 数量 |
|---|---:|
| always | 455 |
| has_wealth_picture | 247 |
| has_official_picture | 127 |
| has_zhi_chong | 79 |
| has_marriage_picture | 20 |
| has_dayun | 3 |
| has_liunian | 1 |
| has_tianluodiwang | 1 |

## 六、生产化说明

- 每条规则包含 `id/status/expert_system/title/topic/domains/axis_refs/claim/conditions/output/source/review/layer/confidence`。
- `source.path` 与 `source.line` 保留原文追溯点。
- 原文绝对化断语统一降级为结构证据，不作为机械铁断。
- 初始置信度沿用子平生产规则默认 0.72 / ★★★★ / sample_n=1，等待反馈校准。
