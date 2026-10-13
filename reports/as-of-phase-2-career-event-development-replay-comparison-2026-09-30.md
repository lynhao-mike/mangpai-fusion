# Phase 2 事业角色变化 development replay 双模型比较

## 证据边界
- 数据分类：`development_replay_only`。
- `promotion_eligible = false`。
- `unseen_holdout_evidence = none`。
- `predict-freeze` 进程只读取 chart-only blind cohort；标签保存在独立 artifact，并由后续 `reveal-score` 进程读取。
- 本结果只比较已暴露历史 cohort 上的旧 Ren `Timing → Event` 与共享 `Structure → Event → Timing`；不得表述为正式准确率提升。

## 指标
| 指标 | legacy Ren | shared | shared - legacy |
|---|---:|---:|---:|
| `predicted_case_count` | 8 | 2 | -6.0 |
| `abstain_count` | 2 | 8 | 6.0 |
| `coverage` | 0.8 | 0.2 | -0.6 |
| `timing_hit_rate` | 0.777778 | 0.222222 | -0.555556 |
| `event_type_hit_rate` | 0.777778 | 0.222222 | -0.555556 |
| `domain_hit_rate` | 0.777778 | 0.222222 | -0.555556 |
| `direction_hit_rate` | 0.111111 | 0.111111 | 0.0 |
| `magnitude_hit_rate` | 0.555556 | 0.222222 | -0.333334 |
| `false_positive_count` | 1 | 0 | -1.0 |
| `false_positive_rate` | 1.0 | 0.0 | -1.0 |
| `false_negative_count` | 2 | 7 | 5.0 |
| `false_negative_rate` | 0.222222 | 0.777778 | 0.555556 |

## 解释
- 结构门降低覆盖并抑制 timing-only 事件声明，但在当前 cohort 上增加了假阴性。
- 方向维度仍受共享结构规则 `neutral` 输出限制；当前对比用于暴露瓶颈，不用于 Calibration。
- blind cohort digest：`db649c962498da8ea7c5cef4b6295bc843b5b3f15de6710b96c2ae3c2f918ad3`。
- labels digest：`f2da11b673cfc40e8682bc6ca92c5482e40c0c686b4f3009004bd15c683d8d7c`。
- freeze bundle hash：`a615b8135facbc4195d6ecbe370c82115864cc1a974258bb09c479c2ae8b6f67`。
- score bundle hash：`cff9cf15f87e3d65addb58243dff2cfbf838ba30da7ee00655a2f27b69e9c3b5`。
- comparison hash：`33416188dcd29544e567dc2665cde19f92fdae5d7f716006eea74c2290437d88`。
