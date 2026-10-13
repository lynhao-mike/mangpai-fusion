# 职业路径冻结竞争产品分流契约 v1

> 状态：active / offline-only  
> 实现：[`tools/career_path_product_routing.py`](../../tools/career_path_product_routing.py:1)  
> 上游协议：[`14-career-path-evaluation-protocol-v1.md`](14-career-path-evaluation-protocol-v1.md:1)、[`17-career-relation-expert-annotation-v1.md`](17-career-relation-expert-annotation-v1.md:1)、[`18-career-path-prospective-cohort-v1.md`](18-career-path-prospective-cohort-v1.md:1)

## 一、目的与边界

本契约把一次冻结竞争评分的不可变证据链转换为产品用途分类。工具只读既有制品，不运行模型、不揭示标签、不执行评分、不创建 score receipt、不修改生产路由。

无论输出何种分类，`production_switch_permitted` 永远为 `false`。生产默认切换必须经过本流程之外的独立、显式人工授权；`shadow_candidate` 不是生产授权。

## 二、失败关闭状态机

状态只有以下四种：

1. `blocked_not_ready`：cohort、模型资格、有效新模型预注册、标签或必需指标任一尚不可评价；缺失结构层阈值时也进入此状态。
2. `shadow_candidate`：终态 promotion 门槛完整且全部通过，只允许 shadow 使用。
3. `structural_evidence_assistant`：终态门槛失败，但新预注册在标签揭示前显式冻结了结构指标阈值、最低分母及证据要求，且评分制品全部满足；只允许结构证据辅助用途。
4. `rejected`：完整性、哈希、唯一性、泄漏门禁失败，或终态层与可评价结构层均失败。

不得从缺失字段、空分母、未声明阈值或非布尔门禁结果猜测通过。

## 三、模型身份和预注册

`career-path-relation-model-v1` 已由处置文件冻结为 `invalidated_requires_new_model_id`。它可以作为历史基线保留，但永远不能进入 `shadow_candidate` 或 `structural_evidence_assistant`。

正式候选必须同时满足：

- 使用不同于旧 v1 的新 `model_id`；
- disposition 的 `model_id` 与预注册唯一 candidate 完全一致；
- `formal_scoring_status=eligible`；
- `holdout_scoring_permitted=true`；
- `promotion_eligible=true`；
- 新预注册在标签揭示前冻结，且与 freeze、score、receipt 绑定。

## 四、一次评分证据链

产品分流必须同时校验：

- `preregistration_id` 与预注册文件 SHA-256；
- cohort SHA-256；
- predictions 文件 SHA-256；
- labels 文件 SHA-256；
- freeze 文件 SHA-256；
- candidate `model_id`；
- disposition 文件 SHA-256；
- score canonical SHA-256 与 receipt；
- freeze、score、receipt 三者均声明 `one_score_only=true`；
- score 明示 cohort ready、labels valid、no leakage 三项均为真。

任一绑定缺失或不一致均为 `rejected`，不能降级为 shadow 或助手。

## 五、结构助手预注册 schema 门禁

既有 [`career-path-holdout-preregistration-v1.json`](../../META/as-of-evaluation/career-path-holdout-preregistration-v1.json:1) 只列出结构指标名称，没有冻结职业柱一致率、trace 完整率等结构层晋级阈值、最低分母或证据要求。因此既有预注册的结构助手结论固定为 `not_evaluable`，不得事后补阈值并声称预注册成立。

未来新模型预注册若希望允许结构助手分类，必须在标签揭示前显式包含：

```json
{
  "structural_assistant_gate": {
    "metrics": {
      "metric_name": {
        "minimum": 0.0,
        "minimum_denominator": 1
      }
    },
    "required_evidence": ["explicit_evidence_kind"]
  }
}
```

阈值数值由未来预注册依据独立设计确定，本契约不凭空规定。

## 六、当前仓库状态

只读命令：

```bat
python -m tools.career_path_product_routing status
```

当前必须返回非零退出码并至少包含：

- `state=blocked_not_ready`；
- `unseen_holdout_not_registered`；
- `invalidated_model_id`；
- `production_switch_permitted=false`。

事实依据是当前 unseen holdout 为 `not_ready / case_count=0`，且 model-v1 disposition 为 `invalidated`。不得运行真实 score、创建 receipt 或制造竞争成绩来改变该状态。
