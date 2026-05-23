# predictions/ · 封存预测

存放**尚未到应期、待验证**的预测。

每份预测一个文件：`PRED-YYYY-NNN-{topic}.md`

封存策略：
- 预测时间锁定（不可事后修改）
- 应期到达时打开 → 命主反馈 → 移入对应 case 的 feedback.md → 校准引擎更新规律命中率

工具：`tools/seal_prediction.py`（M7 阶段迁移自 gufamangpai）
