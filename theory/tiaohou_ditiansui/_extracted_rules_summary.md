# 滴天髓类八字分析规则全量抽取报告

## 一、规则库概览

- **规则总数**: 1108 条
- **状态**: 全部 active（可被生产规则加载器读取）
- **来源**: [`sources/tiaohou_ditiansui/`](../../sources/tiaohou_ditiansui/) 原始 md 文档
- **输出**: [`theory/tiaohou_ditiansui/index.yaml`](index.yaml)
- **提取时间**: 2026-06-22
- **去重口径**: 规范化文本指纹去重；同义近义保留原典来源差异，后续由 merge map 合并。

## 二、来源分布

| 项目 | 数量 |
|---|---:|
| sources/tiaohou_ditiansui/滴天髓_part2.md | 256 |
| sources/tiaohou_ditiansui/滴天髓_part1.md | 254 |
| sources/tiaohou_ditiansui/滴天髓_part3.md | 233 |
| sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md | 61 |
| sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part7.md | 59 |
| sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md | 52 |
| sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md | 49 |
| sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md | 45 |
| sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md | 41 |
| sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md | 33 |
| sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md | 25 |

## 三、领域覆盖

| 项目 | 数量 |
|---|---:|
| 事业 | 808 |
| 健康 | 782 |
| 婚姻 | 700 |
| 财富 | 650 |
| 性格 | 478 |
| 家庭 | 289 |
| 学业 | 269 |
| 迁移 | 88 |
| 总体 | 12 |

## 四、主题归类

| 项目 | 数量 |
|---|---:|
| cold_warm_dry_wet | 655 |
| source_flow | 101 |
| stem_branch_relation | 100 |
| passage | 64 |
| chong_he | 64 |
| career_official | 39 |
| zhonghe_pianku | 31 |
| luck_timing | 28 |
| wealth_structure | 7 |
| qi_momentum | 6 |
| marriage_family | 6 |
| health_body | 3 |
| ditiansui_general | 3 |
| liunian_timing | 1 |

## 五、触发器分布

| 项目 | 数量 |
|---|---:|
| has_tiaohou_advice | 655 |
| has_energy_structure | 165 |
| has_zhi_chong | 164 |
| always | 40 |
| has_official_picture | 39 |
| has_dayun | 28 |
| has_wealth_picture | 7 |
| has_marriage_picture | 6 |
| wuxing_imbalanced | 3 |
| has_liunian | 1 |

## 六、生产化说明

- 每条规则包含 `id/status/expert_system/title/topic/domains/axis_refs/claim/conditions/output/source/review/layer/confidence`。
- `source.path` 与 `source.line` 保留原文追溯点。
- 原文绝对化断语统一降级为气势/调候结构证据，不作为机械铁断。
- 初始置信度沿用生产规则默认 0.72 / ★★★★ / sample_n=1，等待反馈校准。
