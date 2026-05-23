# tools/ · 自动化工具

| 工具 | 用途 | 状态 |
|---|---|---|
| `calibrate.py` | 命主反馈 → 命中率重算 → 规律升降级 | M7 待实现（迁移自 gufamangpai） |
| `seal_prediction.py` | 预测封存 + 应期到达解封 | M7 待实现（迁移自 gufamangpai） |
| `verify_evidence.py` | 报告中证据链一致性校验 | M7 待实现 |
| `normalize_extracted.py` | theory/raw/ → theory/{school}/*.yaml | M2/M3 待实现 |
| `score_initial.py` | 静态分初始化打分 | M5 待实现 |
| `cross_map.py` | 跨派语义相似度匹配 | M4 待实现 |

所有工具支持 dry-run 模式，避免误操作。
