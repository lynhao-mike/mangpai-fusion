# restricted · 受限答案归档（runner 不可读）

> 本目录含 anchor-60 的答案、评分标签与污染清单。**任何 runner/Agent 都不得读取、打包或引用。**
>
> 目录来源：`tasks/T-192/PROMPT.md` §1–§2；A+ v1.3 方向产品已 **KILLED**。

## 内容

| 文件 | 说明 |
|---|---|
| `p1-anchor-60-answers-final-v2.json` | 实际评分所用 final v2 答案（A + B 修正；schema `p1-adjudication-answers/v2`） |
| `p1-anchor-60-answers-B-v1.json` | annotator B 的独立答案（A/B 复核留证） |
| `p1-anchor-60-answers-v1.json` | annotator A 的初版答案（历史留证） |
| `labels-v1.json` | 从 final v2 提取的评分标签（case_id/layer/kind/端点/actor/target/expected_direction） |
| `contamination-list-v1.json` | A60-020 / A60-046 / A60-050：`contaminated`，永久排除 |

所有文件 sha256 见上级 `MANIFEST.sha256`。

## 规则

1. 不得进入任何 runner/Agent 输入包；不得在报告、演示、规格中复述方向/端点/引文答案。
2. 需要复核时，由中枢或**未读过答案**的审计者单独开盒；开盒记录写 `tasks/T-192/STATUS.md`。
3. 出包前必须跑 `python -m tools.check_bundle_case_ids <bundle>` 且退出 0；本目录本身不得被打包。
4. 污染条目永久排除：不因阈值、复测或新口径而解禁。
